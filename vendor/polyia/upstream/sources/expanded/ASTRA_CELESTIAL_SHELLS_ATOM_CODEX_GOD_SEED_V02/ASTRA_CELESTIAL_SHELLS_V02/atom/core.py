"""ATOM v0.1: zero-dependency, deterministic stepwise orchestrator.
The hash chain is an integrity check, not signature-backed immutability.
An ATOM is a typed transition specification; an atom instance is a machine.
"""
from __future__ import annotations
import copy, hashlib, json, os, re, tempfile
from pathlib import Path
from typing import Any

PHASES = ('OBSERVE', 'PROPOSE', 'ADMIT', 'EXECUTE', 'VERIFY', 'CHECKPOINT', 'HOLD')
OPS = ('journey', 'render', 'focus', 'science', 'economy', 'evidence')
TEMPLATES = {
    'journey': {'mission': 'Plan a physically qualified universal traversal', 'default': {'destination':'Mars','from':'Earth'}},
    'render': {'mission':'Compose layered visual plates', 'default': {'plates':['stars','plasma','hud'],'depth':[0.12,0.45,0.91]}},
    'focus': {'mission':'Infer pointer-based visual interest, not actual gaze', 'default': {'mode':'pointer-proxy','x':0.50,'y':0.50}},
    'science': {'mission':'Validate model provenance and units', 'default': {'model':'H_balmer_3_to_2','wavelength_nm':656.28,'kind':'modeled'}},
    'economy': {'mission':'Account simulated nonredeemable game credits', 'default': {'grant':5,'reason':'verified-tour-demo'}},
    'evidence': {'mission':'Verify a registered evidence digest', 'default': {'artifact':'fixture','content':'prototype evidence'}},
}
GUARD = {'nominal':0,'limited_gpu':1,'bad_data':2}
PAYOFFS = { # utilities are scenario preferences, not empirically learned equilibria
    'EXPLORE': {'nominal':7,'limited_gpu':3,'bad_data':-3},
    'OPTIMIZE': {'nominal':5,'limited_gpu':7,'bad_data':2},
    'VERIFY': {'nominal':4,'limited_gpu':5,'bad_data':8},
    'HOLD': {'nominal':1,'limited_gpu':1,'bad_data':1},
}


def canon(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf8')
def sha(value:bytes)->str: return hashlib.sha256(value).hexdigest()
def digest(value:Any)->str: return sha(canon(value))
def atomic_json(path:Path, value:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_bytes(canon(value)+b'\n')
    os.replace(tmp,path)

class AtomError(Exception): pass

class Universe:
    def __init__(self,root:Path):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.state_path=self.root/'state.json';self.events=self.root/'events.jsonl';self.checkpoints=self.root/'checkpoints';self.checkpoints.mkdir(exist_ok=True);self.objects=self.root/'objects';self.objects.mkdir(exist_ok=True)
        if not self.state_path.exists():
            initial={'protocol':'ATOM/0.1','tick':0,'phase':'OBSERVE','head':'0'*64,'atoms':{},'active':None,'pending':None,'results':[], 'credits':0,'last_checkpoint':None,'committed':[], 'max_credits':1000}
            atomic_json(self.state_path,initial)
            self.events.write_text('')
    def state(self): return json.loads(self.state_path.read_text('utf8'))
    def _commit(self,state,event):
        event=copy.deepcopy(event);event.update({'version':state['tick']+1,'prev':state['head']})
        event['hash']=digest({k:v for k,v in event.items() if k!='hash'})
        with self.events.open('a',encoding='utf8') as f: f.write(json.dumps(event,sort_keys=True,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
        state['tick']+=1;state['head']=event['hash'];atomic_json(self.state_path,state)
        return event
    def register(self,name,kind):
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,47}',name):raise AtomError('Invalid atom identifier')
        if kind not in TEMPLATES:raise AtomError('Unregistered atom kind')
        s=self.state()
        if s['phase']!='OBSERVE':raise AtomError('Register only while observing')
        if name in s['atoms']:raise AtomError('Atom already exists')
        s['atoms'][name]={'kind':kind,'state':'READY','runs':0,'last_result':None}
        self._commit(s,{'verb':'REGISTER','atom':name,'kind':kind});return s
    def source_archive(self):
        """Preserve selected local source bytes at checkpoints. Changed working files are okay later;
        prior snapshots are content-addressed and checked independently. No symlinks followed.
        """
        project=self.root.parent
        selected=['atom/core.py','atom/cli.py','atom/server.py','web/index.html','web/app.js','web/style.css','web/atom-bus.js','web/sky.js','web/star-gpu.js','web/audio.js','audio_assets/celestial-drift.wav','audio_assets/portal-chime.wav']
        artifacts={}
        for rel in selected:
            p=project/rel
            if p.is_symlink() or not p.is_file():continue
            data=p.read_bytes();key=sha(data)
            target=self.objects/key
            if target.exists() and sha(target.read_bytes())!=key:raise AtomError('Object digest collision')
            if not target.exists():
                target.write_bytes(data)
            artifacts[rel]={'sha256':key,'bytes':len(data)}
        return artifacts
    def candidates(self):
        return [{'action':a,'worst_case_utility':min(p.values()),'nominal':p['nominal']} for a,p in PAYOFFS.items()]
    def choose(self):return sorted(self.candidates(),key=lambda o:(-o['worst_case_utility'],-o['nominal'],o['action']))[0]
    def advance(self,atom=None,params=None):
        s=self.state();ph=s['phase'];params=params or {}
        if not isinstance(params,dict):raise AtomError('params must be an object')
        if ph=='OBSERVE':
            if atom not in s['atoms']:raise AtomError('Unknown atom')
            s['active']=atom;s['pending']={'params':params,'decision':None,'evaluation':None,'output':None};s['phase']='PROPOSE'
            ev={'verb':'SELECT','atom':atom}
        elif ph=='PROPOSE':
            s['pending']['decision']=self.choose()
            s['phase']='ADMIT';ev={'verb':'PROPOSE','policy':'maximin','decision':s['pending']['decision']}
        elif ph=='ADMIT':
            kind=s['atoms'][s['active']]['kind'];p=s['pending']['params'];self._check(kind,p,s)
            s['phase']='EXECUTE';ev={'verb':'ADMIT','kind':kind,'schema':'ATOM/0.1'}
        elif ph=='EXECUTE':
            kind=s['atoms'][s['active']]['kind'];value=self._evaluate(kind,s['pending']['params'],s)
            s['pending']['output']=value;s['phase']='VERIFY';ev={'verb':'EXECUTE','output_digest':digest(value)}
        elif ph=='VERIFY':
            kind=s['atoms'][s['active']]['kind'];out=s['pending']['output'];p=s['pending']['params']
            self._verify_output(kind,p,out)
            s['pending']['evaluation']={'verdict':'PASS','kind':kind,'output_hash':digest(out)}
            s['phase']='CHECKPOINT';ev={'verb':'VERIFY','verdict':'PASS','output_hash':digest(out)}
        elif ph=='CHECKPOINT':
            active=s['active'];kind=s['atoms'][active]['kind'];out=s['pending']['output'];evaluation=s['pending']['evaluation']
            s['atoms'][active]['runs']+=1;s['atoms'][active]['last_result']=out
            if kind=='economy':s['credits']+=out['credited']
            s['results'].append({'atom':active,'kind':kind,'output':out,'witness':evaluation})
            s['phase']='HOLD'
            # Checkpoint contains the exact state BEFORE the receipt transaction but with the forward phase attached.
            checkpoint={'checkpoint_version':s['tick']+1,'parent':s['last_checkpoint'],'tree':copy.deepcopy(s),'source_archive':self.source_archive()}
            cp_hash=digest(checkpoint);cp_file=self.checkpoints/(cp_hash+'.json')
            if cp_file.exists() and cp_file.read_bytes()!=canon(checkpoint)+b'\n':raise AtomError('Checkpoint collision')
            atomic_json(cp_file,checkpoint)
            s['last_checkpoint']=cp_hash;s['committed'].append(cp_hash)
            ev={'verb':'CHECKPOINT','checkpoint':cp_hash,'atom':active,'status':'LOCKED'}
        elif ph=='HOLD':
            s['phase']='OBSERVE';s['active']=None;s['pending']=None;ev={'verb':'RESUME','after':s['last_checkpoint']}
        else:raise AtomError('Invalid phase')
        self._commit(s,ev);return {'phase':s['phase'],'event':ev,'tick':s['tick'],'checkpoint':s['last_checkpoint']}
    def _check(self,kind,p,s):
        if kind=='journey':
            if set(p)-{'destination','from'}:raise AtomError('Unsupported journey parameters')
            if p.get('destination','Mars') not in ('Earth','Moon','Mars','Jupiter','Saturn','Neptune') or p.get('from','Earth') not in ('Earth','Moon','Mars','Jupiter','Saturn','Neptune'):raise AtomError('Unknown modeled station')
        elif kind=='render':
            if set(p)-{'plates','depth'}:raise AtomError('Unsupported render parameters')
            plates=p.get('plates',TEMPLATES[kind]['default']['plates']);depth=p.get('depth',TEMPLATES[kind]['default']['depth'])
            if not isinstance(plates,list) or len(plates)!=len(depth) or len(plates)>7 or len(set(plates))!=len(plates) or any(t not in ('stars','plasma','hud','orbits','spectrum','focus') for t in plates):raise AtomError('Invalid plates')
            if any(type(z) not in (float,int) or not 0<=z<=1 for z in depth):raise AtomError('Invalid depths')
        elif kind=='focus':
            if set(p)-{'mode','x','y'}:raise AtomError('Invalid focus parameters')
            if p.get('mode','pointer-proxy')!='pointer-proxy':raise AtomError('Actual eye tracking unavailable')
            if any(type(p.get(k,.5)) not in (float,int) or not 0<=p.get(k,.5)<=1 for k in ('x','y')):raise AtomError('Coordinates must be normalized')
        elif kind=='science':
            if set(p)-{'model','wavelength_nm','kind'}:raise AtomError('Invalid scientific parameters')
            if p.get('kind','modeled')!='modeled' or p.get('model','H_balmer_3_to_2')!='H_balmer_3_to_2':raise AtomError('Unsupported measurement, use modeled')
            if abs(p.get('wavelength_nm',656.28)-656.28)>1.:raise AtomError('Value outside model tolerance')
        elif kind=='economy':
            if set(p)-{'grant','reason'}:raise AtomError('Invalid economy parameters')
            if type(p.get('grant',5)) is not int or not 0<=p.get('grant',5)<=10 or s['credits']+p.get('grant',5)>s['max_credits']:raise AtomError('Simulated ledger limit')
            if not isinstance(p.get('reason','verified-tour-demo'),str) or len(p.get('reason','verified-tour-demo'))>120:raise AtomError('Bad credit reason')
        elif kind=='evidence':
            if set(p)-{'artifact','content'}:raise AtomError('Invalid evidence parameters')
            if not isinstance(p.get('content','prototype evidence'),str) or len(p.get('content','prototype evidence')) > 10000 or not isinstance(p.get('artifact','fixture'),str) or len(p.get('artifact','fixture'))>120:raise AtomError('Evidence fields must be bounded strings')
    def _evaluate(self,kind,p,s):
        a={**TEMPLATES[kind]['default'],**p}
        if kind=='journey':return {'from':a['from'],'to':a['destination'],'mode':'simulated-shift','physical_ephemeris':'NOT_VERIFIED'}
        if kind=='render':return {'plates':[{'name':n,'z':z} for n,z in sorted(zip(a['plates'],a['depth']),key=lambda v:v[1])],'renderer':'canvas2d-plate-compositor'}
        if kind=='focus':return {'x':a['x'],'y':a['y'],'source':'pointer-proxy','is_eye_tracking':False}
        if kind=='science':return {'model':a['model'],'wavelength_nm':a['wavelength_nm'],'source':'analytical-model','measured':False}
        if kind=='economy':return {'credited':a['grant'],'reason':a['reason'],'currency':'PLAY_CREDIT_ONLY','redeemable':False}
        if kind=='evidence':return {'artifact':a['artifact'],'sha256':sha(a['content'].encode('utf8')),'source':'caller-provided'}
        raise AtomError('Unknown executor')
    def _verify_output(self,kind,p,out):
        expected=self._evaluate(kind,p,None)
        if out!=expected:raise AtomError('Output tampered')
    def verify(self):
        s=self.state();prev='0'*64;count=0
        for line in self.events.read_text('utf8').splitlines():
            ev=json.loads(line);provided=ev.pop('hash');expected=digest(ev)
            if ev['prev']!=prev or provided!=expected or ev['version']!=count+1:raise AtomError('Receipt chain invalid')
            prev=provided;count+=1
        if count!=s['tick'] or prev!=s['head']:raise AtomError('State and journal disagree')
        parent=None
        for cp_hash in s['committed']:
            path=self.checkpoints/(cp_hash+'.json')
            if not path.exists():raise AtomError('Missing checkpoint')
            cp=json.loads(path.read_text('utf8'))
            if digest(cp)!=cp_hash or cp['parent']!=parent:raise AtomError('Checkpoint integrity or ancestry failed')
            for name,item in cp.get('source_archive',{}).items():
                obj=self.objects/item['sha256']
                if not obj.is_file() or sha(obj.read_bytes())!=item['sha256']:raise AtomError('Archived artifact corrupted: '+name)
            parent=cp_hash
        if s['last_checkpoint']!=parent:raise AtomError('Checkpoint HEAD mismatch')
        return {'verified':True,'events':count,'checkpoints':len(s['committed']),'head':prev,'phase':s['phase']}
    def protocol(self):
        return {'protocol':'ATOM/0.1','phases':list(PHASES),'templates':TEMPLATES,'operators':['register','advance','status','verify','report'],'admission':'declared schema only','receipt':'SHA256 linked events','decision':'deterministic maximin policy','llm_required':False,'sandbox':'no subprocess or shell execution'}
    def report(self):
        s=self.state();return {'protocol':'ATOM-HANDOFF/0.1','state_digest':digest(s),'tick':s['tick'],'phase':s['phase'],'active':s['active'],'checkpoint_head':s['last_checkpoint'],'recent':s['results'][-5:],'verification':self.verify(),'next_action':'advance' if s['phase']!='OBSERVE' else 'register-or-select','limits':['hashes not signatures','no LLM integration','no real eye tracking','play credits have no monetary value']}
