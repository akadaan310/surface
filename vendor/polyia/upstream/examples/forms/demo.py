"""Reproducible literal constructions; emits JSON, never writes ledger state."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from polyia.forms import VERSION, run_forms  # noqa: E402


def run_examples():
    source = {'source': 'examples/forms/demo.py', 'anchor': 'run_examples literal constructions',
              'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    calls = []

    def run(operation, **values):
        parameters = {'version': VERSION, 'operation': operation, **values}
        report = run_forms(parameters)
        if report['status'] != 'PASS':
            raise AssertionError(report)
        calls.append({'parameters': parameters, 'report': report})
        return report['result']

    def finite(kind, records, interpretation, elements=None):
        letters = [{'id': name, 'sort': sort, 'value': value, 'coordinates': coords, 'sources': [source]}
                   for name, sort, value, coords in records]
        return {'version': 'polyia.alphabet/0.1', 'kind': kind, 'entity_id': 'example:' + kind,
                'interpretation': interpretation, 'sources': [source], 'letters': letters,
                'group': {'elements': elements or [{'id': 'e', 'images': [r[0] for r in records]}]}}

    alphabets = {
        'lettered': finite('lettered', [('H', 'ElementToken', 'H', ['1', '1']),
                                        ('He', 'ElementToken', 'He', ['1', '18'])],
                           'Two transcribed periodic-table positions. This is a supplied layout, not a chemical law.'),
        'geometric': finite('geometric', [
            (name, 'Point', {'shape': 'point', 'vertices': [coords], 'ports': [name]}, coords)
            for name, coords in [('E', ['1', '0']), ('N', ['0', '1']), ('W', ['-1', '0']), ('S', ['0', '-1'])]],
            'Four rational points with declared cyclic letter permutations. No general isometry checker.',
            [{'id': 'r'+str(k), 'images': list('ENWS'[k:]+'ENWS'[:k])} for k in range(4)]),
        'numeric': finite('numeric', [('0', 'Bit', '0', ['0']), ('1', 'Bit', '1', ['1'])],
                          'Exact bit values; identity and complement are explicitly declared.',
                          [{'id': 'e', 'images': ['0', '1']}, {'id': 'flip', 'images': ['1', '0']}]),
        'retial': finite('retial', [('edge', 'GraphMotif', {'vertices': ['u', 'v'], 'edges': [['u', 'v']], 'directed': False}, ['0'])],
                         'An explicit graph motif used as a letter; no chemical interpretation.'),
        'phonetic': finite('phonetic', [('p', 'Segment', {'notation': 'ipa', 'transcription': 'p'}, ['0']),
                                       ('b', 'Segment', {'notation': 'ipa', 'transcription': 'b'}, ['1'])],
                           'Supplied IPA transcription tokens. No acoustic or universal phonological model.'),
    }
    summaries = {name: run('alphabet', alphabet=value) for name, value in alphabets.items()}
    product = run('product', components=[alphabets['phonetic'], alphabets['numeric']],
                  entity_id='example:phonetic-bit', interpretation='Ordered phonetic token × exact bit.', sources=[source])
    alphabets['product'] = product['alphabet']; summaries['product'] = product
    naturals = {'version': 'polyia.alphabet/0.1', 'kind': 'numeric', 'entity_id': 'example:N',
                'interpretation': 'The effective nonnegative integer definition, queried individually.',
                'sources': [source], 'generator': {'name': 'naturals', 'start': 0, 'coordinates': 'value'},
                'group': {'elements': [{'id': 'e', 'rule': 'identity'}]}}
    natural_value = run('generate', alphabet=naturals, index=10**30)['letter']['value']
    negative_member = run('member', alphabet=naturals, candidate=-3)['member']

    def word(name, index, labels):
        return {'version': 'polyia.word/0.1', 'entity_id': 'example:word',
                'alphabet_cid': summaries[name]['content_cid'], 'index': index, 'labels': labels}

    binary = alphabets['numeric']
    cyclic = word('numeric', {'kind': 'cyclic', 'length': 4}, {'0': '1', '1': '0', '2': '0', '3': '1'})
    canonical = run('canonicalize', alphabet=binary, word=cyclic, relation='dihedral')['canonical']['form']['labels']
    flipped = run('act', alphabet=binary, word=cyclic, element='flip')['word']['labels']
    graph = word('lettered', {'kind': 'graph', 'vertices': ['atom-one', 'atom-two'],
                             'edges': [['atom-one', 'atom-two']], 'directed': False},
                 {'atom-one': 'H', 'atom-two': 'He'})
    # This is only a graph of supplied tokens. No molecule admission is performed.
    initial = run('word', alphabet=alphabets['lettered'], word=graph)
    layout = run('layout', alphabet=alphabets['lettered'], word=graph,
                 coordinates={'atom-one': ['1/3', '2'], 'atom-two': ['-3', '0']})
    serialized = run('serialize', alphabet=alphabets['lettered'], word=layout['word'])['text']
    recovered = run('deserialize', alphabet=alphabets['lettered'], text=serialized)['word']
    checks = {
        'all_six_kinds': sorted(alphabets) == ['geometric', 'lettered', 'numeric', 'phonetic', 'product', 'retial'],
        'product_four_ordered_pairs': product['letter_count'] == 4,
        'natural_exact_value': natural_value == '1000000000000000000000000000000',
        'negative_not_natural': negative_member is False,
        'dihedral_known_minimum': canonical == ['0', '0', '1', '1'],
        'pointwise_complement': flipped == {'0': '0', '1': '1', '2': '1', '3': '0'},
        'view_preserves_content': initial['content_cid'] == layout['content_cid'],
        'view_preserves_incidence': graph['index'] == layout['word']['index'],
        'complete_labeled_roundtrip': recovered == layout['word'],
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    return {'schema': 'polyia.forms-example-evidence/0.1', 'status': 'PASS',
            'kernel_sha256': hashlib.sha256((ROOT / 'polyia/forms.py').read_bytes()).hexdigest(),
            'source': source, 'checks': checks, 'calls': calls,
            'scope': 'Executed construction examples with literal expected outputs, not blind external evidence or chemical validation.',
            'mission_acceptance': False, 'llm_inference': False}


if __name__ == '__main__':
    print(json.dumps(run_examples(), ensure_ascii=False, sort_keys=True, indent=2))
