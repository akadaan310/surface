#!/usr/bin/env python3
"""Verify the release's exact source bytes and, in Git, its tracked path census.

Use --write-manifest only when deliberately preparing a new reviewed release.
The manifest is anchored by the published Git commit; it is not a signature.
"""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import subprocess

NAME='MANIFEST_SHA256.json'
SCHEMA='surface.repository-manifest.v1'
MAX_FILE=64*1024*1024

def tracked(root):
    p=subprocess.run(['git','-C',str(root),'ls-files','-s','-z'],capture_output=True,timeout=30)
    if p.returncode:return None
    out={}
    for line in p.stdout.split(b'\0'):
        if not line:continue
        meta,path=line.decode('utf8').split('\t',1);mode,blob,stage=meta.split()
        if stage!='0' or mode not in ('100644','100755'):raise ValueError('unmerged or non-regular tracked path '+path)
        if path!=NAME:out[path]=mode
    return out

def capture(root,name):
    p=PurePosixPath(name)
    if not name or p.is_absolute() or '\\' in name or ':' in name or any(x in ('','.','..','.git') for x in name.split('/')):raise ValueError('unsafe source path')
    path=root.joinpath(*p.parts)
    for part in [path,*path.parents]:
        if part==root:break
        if part.is_symlink():raise ValueError('linked source path '+name)
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):raise ValueError('missing/escaped source '+name)
    if path.stat().st_size>MAX_FILE:raise ValueError('file budget exceeded '+name)
    data=path.read_bytes()
    return {'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}

def prepare(root):
    paths=tracked(root)
    if not paths:raise ValueError('a nonempty staged Git census is required to prepare a release')
    rows=[]
    for name,mode in sorted(paths.items()):
        if Path(name).suffix.lower() in ('.keystore','.jks','.pk8','.pem','.key'):raise ValueError('private signing/key container refused: '+name)
        rows.append({**capture(root,name),'git_mode':mode})
    doc={'schema':SCHEMA,'repository':'https://github.com/akadaan310/surface','scope':'Every tracked source path except this manifest; generated execution directories are excluded by Git','files':rows}
    (root/NAME).write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n')
    return verify(root)

def verify(root):
    path=root/NAME
    if path.is_symlink() or not path.is_file() or path.stat().st_size>8*1024*1024:raise ValueError('missing/invalid manifest')
    raw=path.read_bytes();doc=json.loads(raw)
    if doc['schema']!=SCHEMA or not 0<len(doc['files'])<=10000:raise ValueError('manifest schema/count')
    names=set();total=0
    for row in doc['files']:
        if row['path']==NAME or row['path'] in names:raise ValueError('duplicate/self-referential manifest entry')
        names.add(row['path']);actual=capture(root,row['path'])
        if any(actual[k]!=row[k] for k in actual):raise ValueError('source identity mismatch '+row['path'])
        total+=actual['bytes']
    paths=tracked(root)
    if paths is not None:
        if set(paths)!=names:raise ValueError('tracked source census differs from manifest')
        if any(paths[r['path']]!=r['git_mode'] for r in doc['files']):raise ValueError('Git mode mismatch')
    return {'status':'PASS','files':len(names),'bytes':total,'manifest_sha256':hashlib.sha256(raw).hexdigest(),'git_census':'exact' if paths is not None else 'not available; verified listed files','tolerance':'zero file length, SHA-256, Git blob or mode mismatches'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--write-manifest',action='store_true');a=p.parse_args()
    try:report=prepare(a.root.resolve()) if a.write_manifest else verify(a.root.resolve())
    except (ValueError,OSError,KeyError,subprocess.TimeoutExpired) as e:p.exit(1,'repository verification refused: '+str(e)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
