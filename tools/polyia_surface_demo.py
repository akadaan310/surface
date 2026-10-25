#!/usr/bin/env python3
"""Verify and exercise the pinned, finite PolyIA import without a service or model.

The optional University example requires Node 24+. The default path needs only
Python's standard library. This example does not modify Surface or PolyIA state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/polyia'
IMPORT_MANIFEST_SHA256 = '6eebb37ec30fceae018fcd158e39fecb2f3c47cacae6a732891f3fdb99ebaf01'


def verify_imports(vendor_root: Path = VENDOR) -> dict:
    """Check installed source custody against this adapter's pinned manifest."""
    root = Path(vendor_root).resolve()
    manifest_path = root / 'IMPORT_MANIFEST.json'
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError('Import custody requires a regular manifest file.')
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != IMPORT_MANIFEST_SHA256:
        raise ValueError('Import custody manifest differs from the pinned adapter identity.')
    manifest = json.loads(raw)
    expected = set()
    total = 0
    for row in manifest['files']:
        path = PurePosixPath(row['path'])
        target = root / path
        if path.is_absolute() or '..' in path.parts or str(path) in expected:
            raise ValueError('Import custody contains an unsafe or duplicate path.')
        if (target.is_symlink() or not target.is_file()
                or not target.resolve().is_relative_to(root)):
            raise ValueError('Import custody requires a contained regular file: ' + str(path))
        data = target.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if (len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']
                or blob != row['git_blob_sha1']):
            raise ValueError('Import custody mismatch: ' + str(path))
        expected.add(str(path))
        total += len(data)
    actual = {str(path.relative_to(root))
              for prefix in ('upstream', 'substrate-university')
              for path in (root / prefix).rglob('*') if path.is_file()
              and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.pyo')}
    if expected != actual:
        raise ValueError('Import custody file census differs from the pinned selection.')
    return {'status': 'PASS', 'files': len(expected), 'bytes': total,
            'manifest_sha256': IMPORT_MANIFEST_SHA256,
            'upstreams': manifest['upstreams'],
            'scope': 'Exact Git blob and SHA-256 custody; not a license grant or scientific proof.'}


def _module(root: Path, name: str):
    if name not in ('generators', 'native', 'forms', 'astra'):
        raise ValueError('Only the fixed imported kernels are available.')
    spec = importlib.util.spec_from_file_location('surface_import_' + name,
                                                 root / 'upstream/polyia' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pass(report: dict) -> dict:
    if report.get('status', 'PASS' if report.get('ok') else 'REFUSED') != 'PASS':
        raise ValueError('Bounded imported operation failed: ' + json.dumps(report, sort_keys=True))
    return report


def build_demo(vendor_root: Path = VENDOR) -> dict:
    """Return a deterministic JSON-shaped receipt from four real pure kernels."""
    root = Path(vendor_root).resolve()
    custody = verify_imports(root)
    generators, native, forms, astra = [_module(root, name)
                                       for name in ('generators', 'native', 'forms', 'astra')]

    def generate(name):
        card = json.loads((root / 'upstream/examples/generators' / name).read_text())
        model = _pass(generators.compile_model(card))['model']
        return model, _pass(generators.run_model(model, {'operation': 'generate'}))

    protocol_model, protocol = generate('protocol.card.json')
    negative = _pass(generators.run_model(protocol_model, {'operation': 'recognize', 'word': ['ACK']}))
    tampered = copy.deepcopy(protocol)
    tampered['trace'][1]['event'] = 'fabricated'
    polynomial_model, polynomial = generate('rational-division.card.json')
    first = polynomial['result']['candidates'][0]
    limited = generators.run_model(polynomial_model,
                                   {'operation': 'inverse', 'target': ['10'], 'search_budget': 1})
    exported = _pass(generators.export_native(first))
    compiled = _pass(native.compile_program(exported['source']))
    executed = _pass(native.execute_program(compiled['program']))
    curriculum = _pass(generators.build_curriculum(first))['curriculum']
    concise = _pass(generators.render_explanation(first, {'style': 'concise'}))['view']
    tutorial = _pass(generators.render_explanation(first, {'style': 'tutorial'}))['view']

    source = {'source': 'tools/polyia_surface_demo.py', 'anchor': 'build_demo authored bit fixture',
              'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    alphabet = {'version': 'polyia.alphabet/0.1', 'entity_id': 'surface:bits', 'kind': 'numeric',
                'interpretation': 'Exact bit tokens; no physical denotation is inferred.',
                'sources': [source],
                'letters': [{'id': value, 'sort': 'Bit', 'value': value,
                             'coordinates': [value], 'sources': [source]} for value in ('0', '1')],
                'group': {'elements': [{'id': 'e', 'images': ['0', '1']},
                                       {'id': 'flip', 'images': ['1', '0']}]}}

    def form(operation, **values):
        return _pass(forms.run_forms({'version': forms.VERSION, 'operation': operation,
                                      'alphabet': alphabet, **values}))['result']

    word = {'version': 'polyia.word/0.1', 'entity_id': 'surface:word',
            'alphabet_cid': form('alphabet')['content_cid'],
            'index': {'kind': 'sequence', 'length': 2}, 'labels': {'0': '0', '1': '1'}}
    before = form('word', word=word)
    after = form('layout', word=word, coordinates={'0': ['-1', '2'], '1': ['3', '4']})
    text = form('serialize', word=after['word'])['text']
    restored = form('deserialize', text=text)['word']

    def atom(operation, **values):
        return astra.run_adapter({'adapter_version': astra.ADAPTER_VERSION,
                                  'source_version': astra.SOURCE_VERSION,
                                  'protocol': astra.PROTOCOL, 'operation': operation, **values})

    state = _pass(atom('atom.initialize'))
    phases = [state['state']['phase']]
    for index in range(5):
        state = _pass(atom('atom.advance', state=state['state'],
                           expected_state_digest=state['report']['state_digest'],
                           input={'artifact': 'Surface bounded import', 'content': 'abc'} if index == 0 else {}))
        phases.append(state['state']['phase'])
    checkpoint = atom('atom.advance', state=state['state'],
                      expected_state_digest=state['report']['state_digest'], input={})

    result = {
        'schema': 'surface.polyia-demo/1', 'status': 'PASS', 'custody': custody,
        'protocol': {'model_cid': protocol_model['cid'],
                     'words': [item['value'] for item in protocol['result']['candidates']],
                     'negative_member': negative['result']['accepted'],
                     'replay': generators.replay_trace(protocol),
                     'tampered_replay': generators.replay_trace(tampered),
                     'trace': protocol['trace']},
        'polynomial': {'model_cid': polynomial_model['cid'], 'candidate_count': len(polynomial['result']['candidates']),
                       'first_content_id': first['id'], 'first': first['value'],
                       'limited_inverse': {'status': limited['status'],
                                           'classification': limited['result']['classification'],
                                           'complete': limited['result']['complete']},
                       'curriculum': curriculum,
                       'style_preserves_relations': concise['relations'] == tutorial['relations'],
                       'style_preserves_content_id': concise['content_id'] == tutorial['content_id']},
        'native': {'source': exported['source'], 'outputs': executed['outputs'],
                   'verification': executed['verification']},
        'forms': {'before_content_cid': before['content_cid'], 'after_content_cid': after['content_cid'],
                  'before_representation_cid': before['representation_cid'],
                  'after_representation_cid': after['representation_cid'],
                  'roundtrip_equal': restored == after['word']},
        'astra': {'phases': phases, 'events': state['state']['events'],
                  'event_persistence': state['event_persistence'],
                  'verification': state['report']['verification'],
                  'checkpoint_attempt': checkpoint['error']['code']},
        'full_mission_acceptance': False, 'llm_inference': False,
        'scope': 'Local finite computations and source custody; no live service, durable ledger, native renderer binding or Android execution.',
        'limitations': ['PolyIA remains NOT_COMMISSIONED; the source handoff reports 2/192 accepted mission obligations.',
                        'Owner-paused upstream research is not resumed by this example.',
                        'Trace replay detects corruption; an unsigned self-consistent receipt is not authenticated provenance.',
                        'Differential VM checking shares Python and Fraction; it is not a formal proof.',
                        'Infinity is IX; VII and VIII remain open research charters.',
                        'No model-free open-domain interpretation or open-ended discovery is claimed.'],
    }
    checks = {
        'two_protocol_words': result['protocol']['words'] == [['PING', 'ACK'], ['PING', 'ACK', 'ACK']],
        'negative_membership': result['protocol']['negative_member'] is False,
        'trace_intact': result['protocol']['replay']['ok'] is True,
        'trace_tamper_refused': result['protocol']['tampered_replay']['ok'] is False,
        'eighteen_exact_exercises': result['polynomial']['candidate_count'] == 18,
        'limited_search_unresolved': result['polynomial']['limited_inverse'] == {
            'status': 'RESOURCE_LIMIT', 'classification': 'UNRESOLVED_SEARCH_BUDGET', 'complete': False},
        'native_differential_agreement': executed['verification']['agreement'] is True,
        'same_content_after_layout': before['content_cid'] == after['content_cid'],
        'different_representation_after_layout': before['representation_cid'] != after['representation_cid'],
        'roundtrip': restored == after['word'],
        'style_preserves_content': result['polynomial']['style_preserves_relations'] and result['polynomial']['style_preserves_content_id'],
        'no_fabricated_checkpoint': result['astra']['checkpoint_attempt'] == 'PERSISTENCE_REQUIRED',
    }
    if not all(checks.values()):
        raise ValueError('Bounded Surface import checks failed: ' + json.dumps(checks, sort_keys=True))
    result['checks'] = checks
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write the same JSON receipt to this path.')
    parser.add_argument('--with-university', action='store_true', help='Also run the fixed University fixture in Node 24+.')
    args = parser.parse_args()
    try:
        result = build_demo()
        if args.with_university:
            node = shutil.which('node')
            if not node:
                raise ValueError('University execution requires Node 24 or later; it was not run.')
            run = subprocess.run([node, '--no-warnings', str(VENDOR / 'university_demo.mjs')],
                                 capture_output=True, text=True, timeout=15)
            if run.returncode:
                raise ValueError('University fixture failed: ' + run.stderr.strip())
            result['university'] = json.loads(run.stdout)
        raw = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(raw, encoding='utf-8')
        print(raw, end='')
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'status': 'REFUSED', 'detail': str(error), 'full_mission_acceptance': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
