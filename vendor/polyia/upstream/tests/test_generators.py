"""Real constructive outputs, adverse inputs, and independent semantic witnesses."""
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
path = ROOT/'polyia/generators.py'
if path.exists():
    spec = importlib.util.spec_from_file_location('generators_under_test', path)
    generators = importlib.util.module_from_spec(spec); spec.loader.exec_module(generators)
else:
    class Missing:
        def compile_model(self, value): return {'ok':False,'error':{'code':'NOT_IMPLEMENTED'}}
        def run_model(self, *args): return {'status':'REFUSED','result':{'reason':'NOT_IMPLEMENTED'}}
        def replay_trace(self,*args): return {'ok':False}
        def render_explanation(self,*args): return {'ok':False}
    generators = Missing()


def regular(grammar=None):
    return {'schema':'polyia.generator-card/0.1','id':'message-language','version':'1.0.0',
            'family':'regular','alphabet':['PING','ACK'],'seed':0,
            'grammar':grammar or {'op':'sequence','parts':[{'op':'token','token':'PING'},
                        {'op':'repeat','body':{'op':'token','token':'ACK'},'min':1,'max':2}]},
            'bounds':{'work_units':10000,'max_candidates':64}}


def polynomial():
    return {'schema':'polyia.generator-card/0.1','id':'polynomial-exercises','version':'1.0.0',
            'family':'polynomial-division','coefficient_choices':['-1','0','1'],
            'divisor':['-1','1'],'quotient_degree':1,'seed':0,
            'bounds':{'work_units':10000,'max_candidates':64}}


class GeneratorTests(unittest.TestCase):
    def compile(self, card):
        result=generators.compile_model(card)
        self.assertTrue(result['ok'],result)
        return result['model']

    def execute(self, model, request, status='PASS'):
        report=generators.run_model(model,request)
        self.assertEqual(report['status'],status,report)
        self.assertFalse(report['llm_inference'])
        return report

    def test_constructs_unlisted_regular_words_and_replays_derivations(self):
        card=regular(); before=copy.deepcopy(card); model=self.compile(card)
        report=self.execute(model,{'operation':'generate'})
        self.assertEqual([x['value'] for x in report['result']['candidates']], [['PING','ACK'],['PING','ACK','ACK']])
        self.assertEqual(report['result']['counts']['admitted'],2)
        self.assertTrue(report['result']['complete'])
        self.assertTrue(all(x['witness']['reference_accepts'] for x in report['result']['candidates']))
        self.assertTrue(generators.replay_trace(report)['ok'])
        self.assertEqual(card,before)
        self.assertEqual(generators.run_model(model,{'operation':'generate'}),report)
        changed=copy.deepcopy(report);changed['trace'][1]['event']='fabricated'
        self.assertFalse(generators.replay_trace(changed)['ok'])

    def test_dfa_and_ast_agree_on_all_small_words_including_negative_cases(self):
        model=self.compile(regular())
        for length in range(5):
            for word in itertools.product(['PING','ACK'],repeat=length):
                report=self.execute(model,{'operation':'recognize','word':list(word)})
                expected=list(word) in [['PING','ACK'],['PING','ACK','ACK']]
                self.assertEqual(report['result']['accepted'],expected)
                self.assertEqual(report['result']['reference_accepted'],expected)
        report=generators.run_model(model,{'operation':'recognize','word':['EXEC']})
        self.assertEqual(report['status'],'REFUSED')

    def test_minimization_reports_measured_reduction_and_product_equivalence(self):
        grammar={'op':'choice','parts':[{'op':'sequence','parts':[{'op':'token','token':'PING'},{'op':'token','token':'ACK'}]},
                                      {'op':'sequence','parts':[{'op':'token','token':'ACK'},{'op':'token','token':'ACK'}]}]}
        model=self.compile(regular(grammar))
        optimization=model['optimization']
        self.assertTrue(optimization['equivalent'])
        self.assertGreater(optimization['baseline_states'],optimization['candidate_states'])
        self.assertGreater(optimization['product_pairs_checked'],0)
        self.assertEqual(optimization['metric'],'reachable DFA state count')

    def test_polynomial_generator_constructs_and_independently_checks_new_problems(self):
        model=self.compile(polynomial());report=self.execute(model,{'operation':'generate'})
        candidates=report['result']['candidates']
        self.assertEqual(len(candidates),18) # 3 constant choices * 2 nonzero leading choices * 3 remainders.
        first=candidates[0]['value']
        self.assertEqual(first['divisor'],['-1','1'])
        self.assertEqual(first['quotient'],['-1','-1'])
        self.assertEqual(first['remainder'],['-1'])
        self.assertEqual(first['dividend'],['0','0','-1'])
        self.assertTrue(all(c['witness']['division_matches'] and c['witness']['derivative_numerators_match'] for c in candidates))
        self.assertEqual(len({c['id'] for c in candidates}),18)
        self.assertTrue(generators.replay_trace(report)['ok'])

    def test_inverse_distinguishes_unique_multiple_empty_and_unresolved(self):
        model=self.compile(polynomial())
        unique=self.execute(model,{'operation':'inverse','target':['0','0','-1']})
        self.assertEqual(unique['result']['classification'],'UNIQUE_IN_DECLARED_DOMAIN')
        empty=self.execute(model,{'operation':'inverse','target':['10']})
        self.assertEqual(empty['result']['classification'],'NO_PREIMAGE_IN_DECLARED_DOMAIN')
        multiple=self.execute(model,{'operation':'inverse','value_at':'0','target_value':'0'})
        self.assertGreater(multiple['result']['matching_count'],1)
        self.assertEqual(multiple['result']['classification'],'MULTIPLE_IN_DECLARED_DOMAIN')
        short=self.execute(model,{'operation':'inverse','target':['10'],'search_budget':1},'RESOURCE_LIMIT')
        self.assertEqual(short['result']['classification'],'UNRESOLVED_SEARCH_BUDGET')
        self.assertFalse(short['result']['complete'])

    def test_view_choices_preserve_certified_content_and_reject_added_claims(self):
        model=self.compile(polynomial());report=self.execute(model,{'operation':'generate'})
        content=report['result']['candidates'][0]
        concise=generators.render_explanation(content,{'style':'concise'})
        tutorial=generators.render_explanation(content,{'style':'tutorial'})
        self.assertTrue(concise['ok']);self.assertTrue(tutorial['ok'])
        self.assertNotEqual(concise['view']['text'],tutorial['view']['text'])
        self.assertEqual(concise['view']['content_id'],tutorial['view']['content_id'])
        self.assertEqual(concise['view']['relations'],tutorial['view']['relations'])
        self.assertIn('b(x) != 0',tutorial['view']['text'])
        self.assertFalse(generators.render_explanation(content,{'style':'tutorial','claim':'valid at excluded roots'})['ok'])
        tampered=copy.deepcopy(content);tampered['value']['dividend']=['999']
        self.assertFalse(generators.render_explanation(tampered,{'style':'concise'})['ok'])

    def test_forged_package_unknown_effects_and_resource_exhaustion_refuse(self):
        for mutation in [{'effects':['network']},{'family':'neural'},{'seed':True}]:
            card=regular();card.update(mutation)
            self.assertFalse(generators.compile_model(card)['ok'])
        card=regular();card['grammar']={'op':'execute','source':'__import__("os")'}
        self.assertFalse(generators.compile_model(card)['ok'])
        model=self.compile(regular());bad=copy.deepcopy(model);bad['program']['accepting']=[]
        self.assertEqual(generators.run_model(bad,{'operation':'generate'})['status'],'REFUSED')
        short=self.execute(model,{'operation':'generate','search_budget':1},'RESOURCE_LIMIT')
        self.assertFalse(short['result']['complete'])
        paused=self.execute(model,{'operation':'generate','paused':True},'REFUSED')
        self.assertEqual(paused['result']['reason'],'PAUSED')

    def test_packages_execute_in_clean_interpreter_with_only_the_fixed_runtime(self):
        for card,request,want in [(regular(),{'operation':'recognize','word':['PING','ACK']},True),
                                  (polynomial(),{'operation':'generate'},None)]:
            model=self.compile(card)
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);(root/'generators.py').write_bytes(path.read_bytes())
                wire={'model':model,'request':request}
                result=subprocess.run([sys.executable,'-I','-B',str(root/'generators.py'),'run'],input=json.dumps(wire),capture_output=True,text=True,cwd=root,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)
                report=json.loads(result.stdout);self.assertEqual(report['status'],'PASS',report)
                if want is not None:self.assertEqual(report['result']['accepted'],want)
                else:self.assertEqual(len(report['result']['candidates']),18)

    def test_budget_does_not_construct_the_first_excluded_candidate(self):
        card=polynomial();card.update(divisor=['2'],quotient_degree=0,coefficient_choices=['1',str(2**256-1)])
        report=self.execute(self.compile(card),{'operation':'generate','search_budget':1},'RESOURCE_LIMIT')
        self.assertEqual(report['result'].get('candidates',[{}])[0].get('value',{}).get('dividend'),['2'])
        self.assertEqual(report['result']['counts']['frontier_visits'],1)

    def test_large_valid_receipt_remains_replayable(self):
        card=polynomial();card.update(divisor=['1','0','0','1'],quotient_degree=4,coefficient_choices=['-1','1'])
        card['bounds']={'work_units':200000,'max_candidates':256}
        report=self.execute(self.compile(card),{'operation':'generate'})
        self.assertEqual(len(report['result']['candidates']),256)
        self.assertTrue(generators.replay_trace(report)['ok'])

    def test_curriculum_and_native_emission_share_exact_verified_content(self):
        model=self.compile(polynomial());content=self.execute(model,{'operation':'generate'})['result']['candidates'][0]
        plan=getattr(generators,'build_curriculum',lambda _: {'ok':False})(content)
        self.assertTrue(plan['ok'],plan)
        self.assertEqual([s['id'] for s in plan['curriculum']['steps']],['fractions','division','product-derivative','quotient-derivative'])
        self.assertEqual(plan['curriculum']['steps'][0]['result'],'0')
        exported=getattr(generators,'export_native',lambda _: {'ok':False})(content)
        self.assertTrue(exported['ok'],exported)
        from polyia import native
        compiled=native.compile_program(exported['source']);self.assertTrue(compiled['ok'],compiled)
        execution=native.execute_program(compiled['program']);self.assertTrue(execution['ok'],execution)
        self.assertEqual(execution['outputs']['quotient']['value'],['-1','-1'])
        self.assertEqual(execution['outputs']['remainder']['value'],['-1'])
        self.assertEqual(execution['outputs']['product_derivative']['value'],['0','2','-3'])
        self.assertEqual(execution['outputs']['quotient_numerator']['value'],['0','2','-1'])

    def test_rehashed_forged_regular_witness_cannot_be_rendered(self):
        model=self.compile(regular());content=self.execute(model,{'operation':'generate'})['result']['candidates'][0]
        for field,value in [('machine_path',[999]),('alphabet',5),('model_cid','0'*64)]:
            forged=copy.deepcopy(content);forged['derivation'][field]=value
            payload={k:v for k,v in forged.items() if k!='id'}
            forged['id']=hashlib.sha256(('polyia-generated-content\0'+json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'))).encode()).hexdigest()
            try: result=generators.render_explanation(forged,{'style':'concise'})
            except Exception as error:self.fail('Malformed captured content must return a structured refusal: '+repr(error))
            self.assertFalse(result['ok'],(field,result))

    def test_operation_credits_bound_expensive_but_valid_frontier(self):
        card=regular({'op':'repeat','body':{'op':'choice','parts':[{'op':'token','token':'PING'},{'op':'token','token':'ACK'}]},'min':0,'max':4})
        card['bounds']={'work_units':20,'max_candidates':64}
        report=self.execute(self.compile(card),{'operation':'generate'},'RESOURCE_LIMIT')
        self.assertLessEqual(report['result']['operation_credits'],20)
        self.assertFalse(report['result']['complete'])
        self.assertTrue(generators.replay_trace(report)['ok'])

    def test_state_map_carries_generation_constraints_checks_and_representation(self):
        report=self.execute(self.compile(regular()),{'operation':'generate'})
        states={row['state'] for row in report['trace']}
        self.assertTrue({'INPUT','GENERATE','CONSTRAIN','VERIFY','COMPLETE'} <= states,states)
        view=generators.render_explanation(report['result']['candidates'][0],{'style':'tutorial'})['view']
        self.assertEqual(view['state_trace'][-1]['state'],'REPRESENT')
        self.assertEqual(view['state_trace'][-1]['style'],'tutorial')
        self.assertTrue(view['source_lock'])

    def test_one_thousand_distinct_inputs_reproduce_with_negative_controls(self):
        model=self.compile(regular());words=[]
        for length in range(10): words.extend(itertools.product(['PING','ACK'],repeat=length))
        for word in words[:1000]:
            request={'operation':'recognize','word':list(word)}
            first=self.execute(model,request);second=self.execute(model,request)
            self.assertEqual(first,second)
            self.assertEqual(first['result']['accepted'],word in [('PING','ACK'),('PING','ACK','ACK')])

    def test_nonimproving_minimization_is_not_admitted_as_improvement(self):
        model=self.compile(regular({'op':'empty'}))
        self.assertEqual(model['optimization']['improvement'],0)
        self.assertFalse(model['optimization']['admitted_as_improvement'])
        report=self.execute(model,{'operation':'generate'})
        self.assertEqual([c['value'] for c in report['result']['candidates']],[[]])

    def test_cli_rejects_duplicate_json_fields(self):
        wire=json.dumps(regular()).replace('"seed": 0','"seed": 1, "seed": 0')
        process=subprocess.run([sys.executable,'-I','-B',str(path),'compile'],input=wire,capture_output=True,text=True,timeout=10)
        self.assertNotEqual(process.returncode,0)
        self.assertFalse(json.loads(process.stdout)['ok'])

    def test_recognition_budget_includes_independent_grammar_check(self):
        card=regular({'op':'choice','parts':[{'op':'token','token':'PING'} for _ in range(8)]})
        card['bounds']['work_units']=2
        self.execute(self.compile(card),{'operation':'recognize','word':['PING']},'RESOURCE_LIMIT')


if __name__=='__main__':unittest.main()
