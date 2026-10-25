#!/usr/bin/env python3
"""Trusted installed checker for an untrusted generator package directory.

Run this file from a separately trusted installation, never from the candidate
being authenticated. Candidate verifier code is checked as data and never run.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile

MAX_FILE=2097152
# Installation-owned execution admission, independent of candidate claims or
# the externally supplied custody digest. Historical releases carry their own
# trusted checker; there is deliberately no command-line override for this pin.
TRUSTED_RUNTIMES={
    'polyia.generators/0.1':'7ed24c06988e7323607871e1c5cb27c4b6cb6d397fed4817ebec66a79b303bef',
}


def _read(path, limit):
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode): raise ValueError('Only regular package files may be read.')
        if info.st_size>limit: raise ValueError('Package file exceeds its byte limit.')
        parts=[];size=0
        while size<=limit:
            part=os.read(fd,min(65536,limit+1-size))
            if not part: break
            parts.append(part);size+=len(part)
        if size>limit: raise ValueError('Package file exceeds its byte limit.')
        return b''.join(parts)
    finally: os.close(fd)


def verify_package(package, manifest_sha256):
    if type(manifest_sha256) is not str or re.fullmatch('[0-9a-f]{64}',manifest_sha256) is None:
        raise ValueError('An external SHA-256 manifest identity is required.')
    root=Path(package).resolve()
    if not root.is_dir(): raise ValueError('Package must be a directory.')
    data=_read(root/'MANIFEST.json',1048576)
    if hashlib.sha256(data).hexdigest()!=manifest_sha256:
        raise ValueError('Manifest digest does not match the external expected identity.')
    manifest=json.loads(data)
    if (type(manifest) is not dict or manifest.get('schema')!='polyia.generator-release/0.1'
            or type(manifest.get('files')) is not list or not 1<=len(manifest['files'])<=64
            or manifest.get('fixture_status')!='PASS' or manifest.get('full_mission_acceptance') is not False):
        raise ValueError('Unsupported package manifest.')
    captured={}
    for row in manifest['files']:
        if type(row) is not dict or set(row)!={'path','sha256','bytes'} or type(row['path']) is not str:
            raise ValueError('Malformed manifest file record.')
        path=PurePosixPath(row['path'])
        if (path.is_absolute() or '..' in path.parts or not path.parts or str(path)!=row['path']
                or row['path'] in captured or row['path']=='MANIFEST.json'):
            raise ValueError('Unsafe or duplicate manifest path.')
        if type(row['bytes']) is not int or not 0<=row['bytes']<=MAX_FILE:
            raise ValueError('Unsupported captured file size.')
        target=root/path
        if not target.resolve().is_relative_to(root): raise ValueError('Package path escapes its root.')
        content=_read(target,MAX_FILE)
        if len(content)!=row['bytes'] or hashlib.sha256(content).hexdigest()!=row['sha256']:
            raise ValueError('Captured file differs: '+row['path'])
        captured[row['path']]=content
    # Bounded census uses scandir directly so an unexpected directory cannot
    # cause an unbounded materialized recursive listing.
    actual=set();pending=[root];entries=0
    while pending:
        with os.scandir(pending.pop()) as directory:
            for entry in directory:
                entries+=1
                if entries>256 or entry.is_symlink(): raise ValueError('Unexpected package entry.')
                if entry.is_dir(follow_symlinks=False): pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False): actual.add(str(Path(entry.path).relative_to(root)))
                else: raise ValueError('Only regular package files are supported.')
    if actual!=set(captured)|{'MANIFEST.json'}: raise ValueError('Package file census changed.')
    if not {'runtime.py','model.json','run.json','expected.json','verify.py'}<=captured.keys():
        raise ValueError('Package lacks its executable contract or fixture.')
    if hashlib.sha256(captured['runtime.py']).hexdigest()!=manifest['runtime_sha256']:
        raise ValueError('Runtime identity does not match its manifest.')
    model=json.loads(captured['model.json'])
    if model['cid']!=manifest['model_cid']: raise ValueError('Model identity does not match its manifest.')
    if TRUSTED_RUNTIMES.get(model['dependencies']['runtime'])!=manifest['runtime_sha256']:
        raise ValueError('Runtime is not registered by this trusted checker; manifest custody is not execution authority.')
    for source in model['source_lock']:
        if source['path'] not in captured or hashlib.sha256(captured[source['path']]).hexdigest()!=source['sha256']:
            raise ValueError('Documentary source lock does not match captured bytes.')
    # Execute only the authenticated bytes copied into a private directory. A
    # later edit of the candidate runtime/run.json cannot win a check/use race.
    with tempfile.TemporaryDirectory(prefix='polyia-generator-verified-') as temporary:
        runtime=Path(temporary)/'runtime.py';runtime.write_bytes(captured['runtime.py'])
        completed=subprocess.run([sys.executable,'-I','-B',str(runtime),'run'],
            input=captured['run.json'],capture_output=True,timeout=15,cwd=temporary)
    if (completed.returncode!=0 or len(completed.stdout)>MAX_FILE
            or json.dumps(json.loads(completed.stdout),sort_keys=True,separators=(',',':'),allow_nan=False)
            !=json.dumps(json.loads(captured['expected.json']),sort_keys=True,separators=(',',':'),allow_nan=False)):
        raise ValueError('Independent execution differs from the captured fixture.')
    return {'status':'PASS','model_cid':manifest['model_cid'],'files':len(captured),
            'runtime_sha256':manifest['runtime_sha256'],
            'runtime_admission':'installation-owned exact source SHA-256',
            'scope':'external manifest custody, registered runtime and independent fixture execution; no full mission acceptance'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(verify_package(args.package,args.manifest_sha256),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError,RecursionError,subprocess.TimeoutExpired) as error:
        print(json.dumps({'status':'FAIL','detail':str(error)}));return 2


if __name__=='__main__':raise SystemExit(main())
