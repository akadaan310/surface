#!/usr/bin/env python3
"""Create a separate initiative branch/worktree from an explicit immutable base.

This pins a base; it does not certify that base's scientific claims. Inspect its
manifest and acceptance receipt before using it as the latest verified baseline.
No network, force checkout, reset, deletion, commit or push is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def git(repo,*args):
    p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,timeout=30)
    if p.returncode: raise ValueError(p.stderr.strip() or 'git operation failed')
    return p.stdout.strip()


def unlinked(path):
    path=Path(path).absolute()
    for component in (path,*path.parents):
        if component.is_symlink(): raise ValueError('linked path component: '+str(component))
    return path


def inside(worktree,path):
    root=unlinked(worktree).resolve()
    path=unlinked(path)
    if not path.resolve().is_relative_to(root): raise ValueError('initiative path escapes worktree')
    return path

def create(slug,repo,base,path):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,47}',slug): raise ValueError('initiative name must be <=48 lower-case letters, digits or hyphens')
    repo=Path(git(repo,'rev-parse','--show-toplevel')).resolve()
    if git(repo,'status','--porcelain'): raise ValueError('preserve and commit/stash current work before creating an initiative')
    commit=git(repo,'rev-parse','--verify',base+'^{commit}')
    path=unlinked(path)
    if path.exists(): raise ValueError('destination already exists')
    if path.resolve().is_relative_to(repo): raise ValueError('worktree must live outside source checkout')
    branch='initiative/'+slug
    exists=subprocess.run(['git','-C',str(repo),'show-ref','--verify','--quiet','refs/heads/'+branch],timeout=10)
    if exists.returncode == 0: raise ValueError('initiative branch already exists; inspect it instead of overwriting')
    if exists.returncode != 1: raise ValueError('could not inspect branch identity')
    path.parent.mkdir(parents=True,exist_ok=True)
    unlinked(path)
    git(repo,'worktree','add','-b',branch,str(path),commit)
    try:
        directory=inside(path,path/'initiatives'/slug)
        record=inside(path,directory/'INITIATIVE.json')
        prompt=inside(path,directory/'SELF_PROMPT.md')
        manifest=inside(path,path/'MANIFEST_SHA256.json')
        if record.exists(): raise ValueError('base already contains this initiative')
        if prompt.exists() and not prompt.is_file(): raise ValueError('existing initiative prompt is not a regular file')
        directory.mkdir(parents=True,exist_ok=True)
        state={'schema':'surface.initiative.v1','id':slug,'branch':branch,'base_ref_at_creation':base,'base_commit':commit,
               'base_tree':git(path,'rev-parse','HEAD^{tree}'),
               'base_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest() if manifest.is_file() else None,
               'status':'SCOPED_NOT_ACCEPTED','validation':'Base pinned; read and rerun its acceptance gates before implementation',
               'dependencies':[],'budgets':{'task_seconds':300,'semantic_seconds':120,'classified_retries':1},
               'acceptance':{'implementation':None,'command':None,'observed_result':None,'tolerance':None,'evidence':[],'status':'NOT_STARTED'},
               'recovery':'Preserve source, stage outputs by epoch, never renew a deadline through heartbeat, reconcile before rerun.'}
        with inside(path,record).open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(state,indent=2)+'\n')
        if not prompt.exists():
            with inside(path,prompt).open('x',encoding='utf-8') as stream:
                stream.write(f'# Resume {slug}\n\nRead AGENTS.md, SUM.md, the base manifest and this initiative record. Base `{commit}` is immutable.\n\nBefore writes, inspect current revision, jobs and checkpoints. Define a bounded task and acceptance witness. Preserve all originals and UNKNOWN/BLOCKED obligations. Run the mathematical atlas review. Do not treat successful compilation as scientific acceptance.\n')
    except (ValueError,OSError) as error:
        raise ValueError(str(error)+'; worktree preserved for inspection at '+str(path)) from error
    return {'worktree':str(path),'branch':branch,'base_commit':commit,'record':str(record),'next':'Review scope and evidence, then commit the initiative record on its branch.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('slug');p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--base',required=True,help='verified commit or ref; resolved and pinned before worktree creation')
    p.add_argument('--path',type=Path)
    a=p.parse_args();path=a.path or a.repo.absolute().parent/'surface-worktrees'/a.slug
    try: result=create(a.slug,a.repo,a.base,path)
    except (ValueError,OSError,subprocess.TimeoutExpired) as e:p.exit(1,'initiative creation refused: '+str(e)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
