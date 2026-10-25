#!/usr/bin/env python3
"""Build an independently runnable generator release with exact source custody.

This explicit packaging tool reads/writes files. The generator handler remains
pure. Existing output directories are refused before any write.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from polyia import generators


def _bytes(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def build_package(card, destination):
    output=Path(destination)
    if output.exists() or output.is_symlink(): raise ValueError('Output already exists; no files were changed.')
    compiled=generators.compile_model(card)
    if not compiled['ok']: raise ValueError('Model refused: '+json.dumps(compiled['error']))
    model=compiled['model'];request={'operation':'generate'}
    expected=generators.run_model(model,request)
    if expected['status']!='PASS': raise ValueError('Default fixture must exhaust its bounded domain: '+str(expected['result'].get('stop_reason')))
    runtime=(ROOT/'polyia/generators.py').read_bytes()
    payload={'runtime.py':runtime,'card.json':_bytes(card),'model.json':_bytes(model),
             'run.json':_bytes({'model':model,'request':request}),'expected.json':_bytes(expected),
             'verify.py':(ROOT/'tools/verify_generator_package.py').read_bytes()}
    for source in model['source_lock']:
        path=ROOT/source['path']
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT): raise ValueError('Source escapes repository.')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=source['sha256']: raise ValueError('Pinned source changed: '+source['path'])
        payload[source['path']]=data
    content=expected['result']['candidates']
    if content and model['family']=='polynomial-division':
        first=content[0]
        payload['example.polyia']=generators.export_native(first)['source'].encode()
        payload['curriculum.json']=_bytes(generators.build_curriculum(first)['curriculum'])
        payload['explanation.json']=_bytes(generators.render_explanation(first,{'style':'tutorial'})['view'])
    payload['README.md']=(
        '# Portable generator package\n\n'
        'Requires Python 3.12 or newer and only its standard library. Run from any directory:\n\n'
        '    python3 -I -B runtime.py run < run.json\n\n'
        'For custody and independent execution, use a separately trusted installed checker, outside this candidate:\n\n'
        '    python3 -I -B /trusted/PolyIA/tools/verify_generator_package.py --package /path/to/this/package --manifest-sha256 <receipt digest>\n\n'
        'Do not execute candidate verify.py to establish trust: candidate verifier code is itself untrusted. '
        'The included copy is data for custody and a convenience only after its own bytes are independently authenticated.\n\n'
        'Keep that receipt separately: a digest stored only beside mutable files does not authenticate them. '
        'The external digest authenticates custody, not arbitrary-code execution. The trusted installed checker also requires '
        'the runtime to match its installation-owned exact source SHA-256; candidate manifests cannot register code. '
        'Use the separately trusted checker from the corresponding historical release for an older runtime. '
        'The checker reads only regular files without following symlinks or blocking on FIFOs, then executes a private copy of the fixed runtime. It uses a 15 second '
        'process timeout for this fixture. The pure runtime itself uses finite operation and representation bounds.\n\n'
        'The model, runtime source, exact documentary sources, constraints, expected fixture and verifier are included. '
        'Model content identity and immutable entity version are separate from prose view identity. '
        'Source custody is exact; documentary grounding is not full inherited acceptance. '
        'This package contains one of two bounded generator families and makes no neural, stochastic, '
        'open-domain, chemistry, historical-language, or complete mission claim.\n'
    ).encode()
    if any(len(data)>2097152 for data in payload.values()): raise ValueError('Package file exceeds its byte bound.')
    manifest={'schema':'polyia.generator-release/0.1','model_cid':model['cid'],
              'entity':model['entity'],'runtime_sha256':hashlib.sha256(runtime).hexdigest(),
              'fixture_status':expected['status'],'full_mission_acceptance':False,
              'files':[{'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for path,data in sorted(payload.items())]}
    manifest_data=_bytes(manifest)
    output.mkdir(parents=False,exist_ok=False)
    for name,data in sorted(payload.items()):
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
    with (output/'MANIFEST.json').open('xb') as stream:stream.write(manifest_data)
    return {'status':'PASS','model_cid':model['cid'],'output':str(output),
            'manifest_sha256':hashlib.sha256(manifest_data).hexdigest(),
            'runtime_sha256':manifest['runtime_sha256'],'files':len(manifest['files']),
            'scope':'source-locked portable package; full D-GENERATORS acceptance remains open'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--card',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.card.stat().st_size>65536: raise ValueError('Card exceeds 64 KiB.')
        card=generators._parse_json(args.card.read_text(encoding='utf-8'))
        print(json.dumps(build_package(card,args.output),sort_keys=True));return 0
    except (OSError,ValueError,RecursionError) as error:
        print(json.dumps({'status':'REFUSED','detail':str(error)}));return 2


if __name__=='__main__':raise SystemExit(main())
