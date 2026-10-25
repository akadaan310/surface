#!/usr/bin/env python3
"""Build Surface's native headless executable and optionally run all current tests.

No package installer, browser, rendering framework or network access is used.
--render additionally produces a bounded portrait PPM and actual host timing JSON.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'
OBJECTS=BUILD/'native-objects'
TESTS=BUILD/'tests'

def run(command,timeout=120):
    command=[str(x) for x in command]
    print('RUN '+shlex.join(command),flush=True)
    started=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    if result.stdout:print(result.stdout,end='',flush=True)
    if result.stderr:print(result.stderr,end='',file=sys.stderr,flush=True)
    entry={'command':command,'returncode':result.returncode,'seconds':time.monotonic()-started,
           'stdout':result.stdout,'stderr':result.stderr}
    if result.returncode:raise RuntimeError(json.dumps(entry))
    return entry

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test',action='store_true',help='Build/run every tests/test_*.cpp, then Python tests')
    parser.add_argument('--render',action='store_true',help='Render a 720x1280 native demonstration of 60 frames')
    parser.add_argument('--compiler',default=os.environ.get('CXX','c++'))
    options=parser.parse_args()
    compiler=shlex.split(options.compiler)
    if not compiler:raise ValueError('compiler command is empty')
    for directory in (OBJECTS,TESTS,ROOT/'evidence'):directory.mkdir(parents=True,exist_ok=True)
    (ROOT/'evidence/headless-build-attempt.json').write_text(json.dumps({
        'schema':'SURFACE-NATIVE-BUILD-ATTEMPT/1','status':'running','requestedTests':options.test,
        'requestedRender':options.render},indent=2)+'\n')
    flags=['-std=c++20','-O3','-pthread','-Wall','-Wextra','-Wpedantic','-Iinclude']
    signature=json.dumps([compiler,flags])
    signature_path=OBJECTS/'flags.json'
    flags_changed=not signature_path.exists() or signature_path.read_text()!=signature
    dependencies=list((ROOT/'include').rglob('*.hpp'))+list((ROOT/'src').glob('*.inc'))
    header_time=max((p.stat().st_mtime_ns for p in dependencies),default=0)
    commands=[];objects=[]
    for source in sorted((ROOT/'src').glob('*.cpp')):
        if source.name=='main.cpp':continue
        output=OBJECTS/(source.stem+'.o');objects.append(output)
        if flags_changed or not output.exists() or max(source.stat().st_mtime_ns,header_time)>output.stat().st_mtime_ns:
            commands.append(run([*compiler,*flags,'-c',source,'-o',output]))
    signature_path.write_text(signature)
    commands.append(run([*compiler,*flags,ROOT/'src/main.cpp',*objects,'-o',BUILD/'surface']))
    test_results=[]
    if options.test:
        for source in sorted((ROOT/'tests').glob('test_*.cpp')):
            output=TESTS/source.stem
            commands.append(run([*compiler,*flags,source,*objects,'-o',output]))
            test_results.append(run([output],timeout=60))
        if list((ROOT/'tests').glob('test_*.py')):
            test_results.append(run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],timeout=60))
    if options.render:
        commands.append(run([BUILD/'surface','--demo','--frames','60','--width','720','--height','1280',
            '--output','build/previews/coupled.ppm','--report','evidence/headless-coupled.json'],timeout=120))
    compiler_version=subprocess.run([*compiler,'--version'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()[0]
    receipt={'schema':'SURFACE-NATIVE-BUILD/1','compiler':compiler_version,'platform':platform.platform(),
        'executable':'build/surface','flags':flags,'testSuitesRun':len(test_results),
        'allRequestedChecksPassed':True,'commands':commands,'tests':test_results,
        'scope':'Native host build/tests. Timing reports are not Android device performance.'}
    (ROOT/'evidence/headless-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (ROOT/'evidence/headless-build-attempt.json').write_text(json.dumps({
        'schema':'SURFACE-NATIVE-BUILD-ATTEMPT/1','status':'succeeded','testSuitesRun':len(test_results),
        'receipt':'evidence/headless-build.json'},indent=2)+'\n')
    print(json.dumps({'executable':'build/surface','testSuitesRun':len(test_results),'passed':True}),flush=True)

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as error:
        try:
            (ROOT/'evidence').mkdir(parents=True,exist_ok=True)
            (ROOT/'evidence/headless-build-attempt.json').write_text(json.dumps({
                'schema':'SURFACE-NATIVE-BUILD-ATTEMPT/1','status':'failed','error':str(error),
                'lastSuccessfulReceipt':'evidence/headless-build.json'},indent=2)+'\n')
        except OSError:pass
        print('Native build failed: '+str(error),file=sys.stderr);raise SystemExit(1)
