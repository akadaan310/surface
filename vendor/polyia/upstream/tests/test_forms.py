"""Independent small orbit expectations and adversarial structured-form checks."""
import copy
import hashlib
import importlib.util
import itertools
import json
from math import factorial, gcd
from pathlib import Path
import unittest

try:
    from polyia.forms import run_forms
except ImportError:
    def run_forms(parameters):
        return {'status': 'REFUSED', 'result': {'reason': 'NOT_IMPLEMENTED'}}

VERSION = 'polyia.forms/0.1'
SOURCE = {'source': 'test:declared-fixture', 'anchor': 'literal definitions', 'sha256': '0' * 64}


def request(operation, **values):
    return {'version': VERSION, 'operation': operation, **values}


def alphabet(kind='lettered', symbols=('a', 'b', 'c'), group=None):
    values = {
        'lettered': lambda i, s: s,
        'numeric': lambda i, s: str(i),
        'geometric': lambda i, s: {'shape': 'segment', 'vertices': [['0', '0'], [str(i+1), '0']], 'ports': ['start', 'end']},
        'retial': lambda i, s: {'vertices': ['u', 'v'], 'edges': [['u', 'v']], 'directed': False},
        'phonetic': lambda i, s: {'notation': 'ipa', 'transcription': ('p', 'b', 'm')[i % 3]},
    }
    return {'version': 'polyia.alphabet/0.1', 'entity_id': 'test:' + kind,
            'kind': kind, 'interpretation': 'Explicit test data; no domain law inferred.',
            'sources': [SOURCE], 'letters': [
                {'id': s, 'sort': kind, 'value': values[kind](i, s),
                 'coordinates': [str(i), '1/2'], 'sources': [SOURCE]}
                for i, s in enumerate(symbols)],
            'group': {'elements': group or [{'id': 'e', 'images': list(symbols)}]}}


def cyclic_alphabet():
    return alphabet(group=[{'id': 'e', 'images': ['a', 'b', 'c']},
                           {'id': 'r', 'images': ['b', 'c', 'a']},
                           {'id': 'r2', 'images': ['c', 'a', 'b']}])


class FormsTests(unittest.TestCase):
    def passed(self, operation, **values):
        report = run_forms(request(operation, **values))
        self.assertEqual(report['status'], 'PASS', report)
        self.assertIs(report['llm_inference'], False)
        self.assertEqual(report['evidence_class'], 'EXACTLY_CHECKED')
        self.assertTrue(report['checks'])
        self.assertTrue(all(check['passed'] for check in report['checks']))
        return report['result']

    def refused(self, operation, reason, **values):
        report = run_forms(request(operation, **values))
        expected = reason if reason in ('RESOURCE_LIMIT', 'UNSUPPORTED') else 'REFUSED'
        self.assertEqual(report['status'], expected, report)
        self.assertEqual(report['result']['reason'], reason, report)
        return report

    def word(self, a, index, labels, **extra):
        return {'version': 'polyia.word/0.1', 'entity_id': 'word:fixture',
                'alphabet_cid': self.passed('alphabet', alphabet=a)['content_cid'],
                'index': index, 'labels': labels, **extra}

    def canonical(self, a, w, relation, **extra):
        return self.passed('canonicalize', alphabet=a, word=w, relation=relation, **extra)['equivalence_cid']

    def test_all_six_kinds_have_computed_product_letters_coordinates_and_group(self):
        for kind in ('lettered', 'geometric', 'numeric', 'retial', 'phonetic'):
            with self.subTest(kind=kind):
                result = self.passed('alphabet', alphabet=alphabet(kind))
                self.assertEqual(result['letter_count'], 3)
                self.assertEqual(result['group']['order'], 1)
        a, b = alphabet(symbols=('a', 'b')), alphabet('numeric', ('0', '1'))
        result = self.passed('product', components=[a, b], entity_id='test:product',
                             interpretation='Ordered pair of explicit component letters.', sources=[SOURCE])
        product = result['alphabet']
        self.assertEqual(product['kind'], 'product')
        validated = self.passed('alphabet', alphabet=product)
        self.assertEqual(validated['letter_count'], 4)
        self.assertEqual([l['value'] for l in validated['resolved_letters']],
                         [['a', '0'], ['a', '1'], ['b', '0'], ['b', '1']])
        self.assertEqual(validated['resolved_letters'][3]['coordinates'], ['1', '1/2', '1', '1/2'])

    def test_group_table_is_composition_not_supplied_metadata(self):
        result = self.passed('alphabet', alphabet=cyclic_alphabet())
        self.assertEqual(result['group']['identity'], 'e')
        self.assertEqual(result['group']['inverse'], {'e': 'e', 'r': 'r2', 'r2': 'r'})
        self.assertEqual(result['group']['multiplication'],
                         [['e', 'r', 'r2'], ['r', 'r2', 'e'], ['r2', 'e', 'r']])

    def test_invalid_permutations_identity_closure_duplicates_and_types(self):
        cases = [([{'id': 'e', 'images': ['a', 'a', 'c']}], 'GROUP'),
                 ([{'id': 'r', 'images': ['b', 'c', 'a']}], 'GROUP'),
                 ([{'id': 'e', 'images': ['a', 'b', 'c']}, {'id': 'r', 'images': ['b', 'c', 'a']}], 'GROUP'),
                 ([{'id': 'e', 'images': ['a', 'b', 'c']}, {'id': 'same', 'images': ['a', 'b', 'c']}], 'GROUP')]
        for group, reason in cases:
            self.refused('alphabet', reason, alphabet=alphabet(group=group))
        a = cyclic_alphabet(); a['letters'][0]['sort'] = 'different-sort'
        self.refused('alphabet', 'TYPE', alphabet=a)

    def test_noncommutative_group_actions_obey_ordered_composition(self):
        permutations = list(itertools.permutations('abc'))
        a = alphabet(group=[{'id': str(i), 'images': list(p)} for i, p in enumerate(permutations)])
        table = self.passed('alphabet', alphabet=a)['group']['multiplication']
        w = self.word(a, {'kind': 'tuple', 'length': 3}, {'0': 'a', '1': 'b', '2': 'c'})
        for g in range(6):
            for h in range(6):
                first = self.passed('act', alphabet=a, word=w, element=str(h))['word']
                left = self.passed('act', alphabet=a, word=first, element=str(g))['word']
                right = self.passed('act', alphabet=a, word=w, element=table[g][h])['word']
                self.assertEqual(left, right)
                # Independent source-position action convention: (g h)(x) = g(h(x)).
                self.assertEqual(left['labels']['0'], permutations[g]['abc'.index(permutations[h][0])])
        self.assertNotEqual(table[1][2], table[2][1])

    def test_product_action_is_componentwise_and_product_bound_checked_before_expansion(self):
        a = alphabet(symbols=('a', 'b'), group=[{'id': 'e', 'images': ['a', 'b']}, {'id': 's', 'images': ['b', 'a']}])
        product = self.passed('product', components=[a, a], entity_id='product:pair',
                             interpretation='Two bits.', sources=[SOURCE])['alphabet']
        result = self.passed('alphabet', alphabet=product)
        self.assertEqual(result['group']['order'], 4)
        letters = result['resolved_letters']
        w = self.word(product, {'kind': 'point'}, {'*': letters[0]['id']})
        acted = self.passed('act', alphabet=product, word=w, element='["s","e"]')['word']
        self.assertEqual(acted['labels']['*'], letters[2]['id'])
        large = alphabet(symbols=tuple(str(i) for i in range(12)))
        self.refused('product', 'RESOURCE_LIMIT', components=[large, large], entity_id='too-large',
                     interpretation='Bounded Cartesian product.', sources=[SOURCE])

    def test_effective_naturals_membership_evaluation_and_words_without_enumeration(self):
        a = {'version': 'polyia.alphabet/0.1', 'entity_id': 'N', 'kind': 'numeric',
             'interpretation': 'Nonnegative mathematical integers, queried individually.', 'sources': [SOURCE],
             'generator': {'name': 'naturals', 'start': 0, 'coordinates': 'value'},
             'group': {'elements': [{'id': 'e', 'rule': 'identity'}]}}
        result = self.passed('alphabet', alphabet=a)
        self.assertIsNone(result['letter_count'])
        self.assertEqual(result['cardinality'], 'countably-infinite-definition')
        self.assertTrue(self.passed('member', alphabet=a, candidate=10**60)['member'])
        self.assertFalse(self.passed('member', alphabet=a, candidate=-1)['member'])
        letter = self.passed('generate', alphabet=a, index=10**60)['letter']
        self.assertEqual(letter['value'], str(10**60))
        self.assertEqual(letter['coordinates'], [str(10**60)])
        w = self.word(a, {'kind': 'sequence', 'length': 2}, {'0': '0', '1': str(10**60)})
        self.assertEqual(self.passed('act', alphabet=a, word=w, element='e')['word'], w)
        self.refused('generate', 'DOMAIN', alphabet=a, index=-1)
        self.refused('member', 'TYPE', alphabet=a, candidate=True)
        self.refused('generate', 'RESOURCE_LIMIT', alphabet=a, index=1 << 257)
        a['generator']['name'] = '__import__("os")'
        self.refused('alphabet', 'UNSUPPORTED', alphabet=a)

    def test_each_index_kind_and_rank_round_trips_exact_labeled_structure(self):
        a = alphabet()
        examples = [({'kind': 'point'}, {'*': 'a'}),
                    ({'kind': 'sequence', 'length': 0}, {}),
                    ({'kind': 'tuple', 'length': 2}, {'0': 'b', '1': 'a'}),
                    ({'kind': 'multiset', 'size': 3}, {'0': 'b', '1': 'a', '2': 'b'}),
                    ({'kind': 'cyclic', 'length': 3}, {'0': 'a', '1': 'b', '2': 'c'}),
                    ({'kind': 'rooted_tree', 'vertices': ['root', 'leaf'], 'root': 'root', 'edges': [['root', 'leaf']]}, {'root': 'a', 'leaf': 'b'}),
                    ({'kind': 'graph', 'vertices': ['v', 'u'], 'directed': True, 'edges': [['u', 'v']]}, {'v': 'a', 'u': 'b'})]
        for rank in range(4):
            origin, shape = [-1] * rank, [2] * rank
            coords = list(itertools.product(*(range(-1, 1) for _ in range(rank))))
            examples.append(({'kind': 'box', 'origin': origin, 'shape': shape},
                             {json.dumps(list(c), separators=(',', ':')): 'abc'[i % 3] for i, c in enumerate(coords)}))
        for index, labels in examples:
            with self.subTest(index=index):
                w = self.word(a, index, labels)
                encoded = self.passed('serialize', alphabet=a, word=w)['text']
                decoded = self.passed('deserialize', alphabet=a, text=encoded)['word']
                self.assertEqual(decoded, w)
                self.assertEqual(json.loads(encoded), w)
                relation = {'multiset': 'multiset', 'cyclic': 'cyclic_rotations',
                            'rooted_tree': 'rooted_unordered_tree', 'graph': 'graph_isomorphism'}.get(index['kind'], 'ordered')
                self.assertEqual(self.canonical(a, w, relation), self.canonical(a, decoded, relation))

    def test_tuple_multiset_and_cyclic_relations_are_distinct(self):
        a = alphabet()
        for kind, relation, equivalent in [('tuple', 'ordered', False), ('multiset', 'multiset', True),
                                           ('cyclic', 'cyclic_rotations', False), ('cyclic', 'dihedral', True)]:
            index = {'kind': kind, ('size' if kind == 'multiset' else 'length'): 3}
            w = self.word(a, index, dict(zip(map(str, range(3)), 'abc')))
            reverse = copy.deepcopy(w); reverse['labels'] = dict(zip(map(str, range(3)), 'acb'))
            self.assertEqual(self.canonical(a, w, relation) == self.canonical(a, reverse, relation), equivalent)
        w = self.word(a, {'kind': 'cyclic', 'length': 3}, dict(zip(map(str, range(3)), 'bca')))
        result = self.passed('canonicalize', alphabet=a, word=w, relation='cyclic_rotations')
        self.assertEqual(result['canonical']['form']['labels'], ['a', 'b', 'c'])
        self.assertEqual(result['index_candidates_checked'], 3)
        self.refused('canonicalize', 'RELATION', alphabet=a, word=w, relation='multiset')

    def test_alphabet_orbit_is_explicit_and_does_not_claim_domain_semantics(self):
        a = cyclic_alphabet()
        w = self.word(a, {'kind': 'tuple', 'length': 2}, {'0': 'b', '1': 'c'})
        acted = self.passed('act', alphabet=a, word=w, element='r')['word']
        self.assertNotEqual(self.canonical(a, w, 'ordered'), self.canonical(a, acted, 'ordered'))
        self.assertEqual(self.canonical(a, w, 'ordered', alphabet_symmetry=True),
                         self.canonical(a, acted, 'ordered', alphabet_symmetry=True))
        result = self.passed('canonicalize', alphabet=a, word=w, relation='ordered', alphabet_symmetry=True)
        self.assertEqual(result['canonical']['form']['labels'], ['a', 'b'])
        self.assertEqual(result['preserved_relation'], 'declared-structural-orbit-only')

    def test_rooted_tree_canonicalizes_child_order_names_but_preserves_root_and_labels(self):
        a = alphabet()
        w = self.word(a, {'kind': 'rooted_tree', 'vertices': ['r', 'x', 'y'], 'root': 'r', 'edges': [['r', 'x'], ['r', 'y']]}, {'r': 'a', 'x': 'b', 'y': 'c'})
        renamed = self.word(a, {'kind': 'rooted_tree', 'vertices': ['2', '1', '0'], 'root': '0', 'edges': [['0', '2'], ['0', '1']]}, {'0': 'a', '1': 'c', '2': 'b'})
        self.assertEqual(self.canonical(a, w, 'rooted_unordered_tree'), self.canonical(a, renamed, 'rooted_unordered_tree'))
        changed = copy.deepcopy(renamed); changed['labels']['0'] = 'b'
        self.assertNotEqual(self.canonical(a, w, 'rooted_unordered_tree'), self.canonical(a, changed, 'rooted_unordered_tree'))

    def test_exact_graph_canonicalization_distinguishes_same_degree_nonisomorphic_graphs(self):
        a = alphabet(); vertices = list('abcdef')
        cycle = [[vertices[i], vertices[(i + 1) % 6]] for i in range(6)]
        triangles = [['a', 'b'], ['b', 'c'], ['c', 'a'], ['d', 'e'], ['e', 'f'], ['f', 'd']]
        w = self.word(a, {'kind': 'graph', 'vertices': vertices, 'directed': False, 'edges': cycle}, dict.fromkeys(vertices, 'a'))
        other = copy.deepcopy(w); other['index']['edges'] = triangles
        first = self.passed('canonicalize', alphabet=a, word=w, relation='graph_isomorphism')
        second = self.passed('canonicalize', alphabet=a, word=other, relation='graph_isomorphism')
        self.assertNotEqual(first['equivalence_cid'], second['equivalence_cid'])
        self.assertEqual(first['index_candidates_checked'], 720)
        rename = dict(zip(vertices, list('zuvwxy')))
        new = copy.deepcopy(w)
        new['index']['vertices'] = list(reversed(list(rename.values())))
        new['index']['edges'] = [[rename[v], rename[u]] for u, v in reversed(cycle)]
        new['labels'] = {rename[k]: v for k, v in w['labels'].items()}
        self.assertEqual(first['equivalence_cid'], self.canonical(a, new, 'graph_isomorphism'))

    def test_directed_incidence_and_loop_are_preserved(self):
        a = alphabet()
        w = self.word(a, {'kind': 'graph', 'vertices': ['x', 'y'], 'directed': True, 'edges': [['x', 'y']]}, {'x': 'a', 'y': 'b'})
        reverse = copy.deepcopy(w); reverse['index']['edges'] = [['y', 'x']]
        loop = copy.deepcopy(w); loop['index']['edges'] = [['x', 'x']]
        self.assertNotEqual(self.canonical(a, w, 'graph_isomorphism'), self.canonical(a, reverse, 'graph_isomorphism'))
        self.assertNotEqual(self.canonical(a, w, 'graph_isomorphism'), self.canonical(a, loop, 'graph_isomorphism'))

    def test_layout_changes_view_identity_only_never_incidence_or_content(self):
        a = alphabet()
        w = self.word(a, {'kind': 'graph', 'vertices': ['x', 'y'], 'directed': False, 'edges': [['x', 'y']]}, {'x': 'a', 'y': 'b'})
        snapshot = copy.deepcopy(w)
        before = self.passed('word', alphabet=a, word=w)
        laid_out = self.passed('layout', alphabet=a, word=w, coordinates={'x': ['0', '1/3'], 'y': ['5', '2']})
        self.assertEqual(w, snapshot)
        self.assertEqual(laid_out['word']['index'], w['index'])
        self.assertEqual(laid_out['content_cid'], before['content_cid'])
        self.assertNotEqual(laid_out['representation_cid'], before['representation_cid'])
        self.assertEqual(self.canonical(a, w, 'graph_isomorphism'), self.canonical(a, laid_out['word'], 'graph_isomorphism'))
        bad = copy.deepcopy(laid_out['word']); bad['view']['edges'] = []
        self.refused('word', 'SCHEMA', alphabet=a, word=bad)
        changed = copy.deepcopy(w); changed['index']['edges'] = []
        self.assertNotEqual(self.passed('word', alphabet=a, word=changed)['content_cid'], before['content_cid'])
        changed = copy.deepcopy(w); changed['entity_id'] = 'word:other'
        self.assertEqual(self.passed('word', alphabet=a, word=changed)['content_cid'], before['content_cid'])

    def test_type_and_coordinate_guards_do_not_coerce_numbers_or_infer_chemistry(self):
        for bad in (True, 0.5, float('nan'), '1/0', '2/4'):
            a = alphabet(); a['letters'][0]['coordinates'][0] = bad
            self.refused('alphabet', 'RATIONAL' if type(bad) is str else 'TYPE', alphabet=a)
        a = alphabet('numeric'); a['letters'][0]['value'] = True
        self.refused('alphabet', 'TYPE', alphabet=a)
        a = alphabet(); a['interpretation'] = ''
        self.refused('alphabet', 'SCHEMA', alphabet=a)
        self.refused('chemical_valence', 'UNSUPPORTED', alphabet=alphabet())

    def test_word_rejects_wrong_alphabet_unknown_letters_missing_and_extra_cells(self):
        a = alphabet(); w = self.word(a, {'kind': 'tuple', 'length': 2}, {'0': 'a', '1': 'b'})
        for modify, reason in [(lambda x: x.update(alphabet_cid='0'*64), 'ALPHABET_BINDING'),
                               (lambda x: x['labels'].update({'1': 'z'}), 'UNKNOWN_LETTER'),
                               (lambda x: x['labels'].pop('1'), 'INDEX'),
                               (lambda x: x['labels'].update({'2': 'a'}), 'INDEX')]:
            bad = copy.deepcopy(w); modify(bad)
            self.refused('word', reason, alphabet=a, word=bad)

    def test_index_structure_rejects_invalid_tree_graph_and_box(self):
        a = alphabet()
        cases = [({'kind': 'rooted_tree', 'vertices': ['a', 'b'], 'root': 'a', 'edges': [['a', 'b'], ['b', 'a']]}, {'a': 'a', 'b': 'b'}),
                 ({'kind': 'graph', 'vertices': ['a', 'b'], 'directed': False, 'edges': [['a', 'b'], ['b', 'a']]}, {'a': 'a', 'b': 'b'}),
                 ({'kind': 'graph', 'vertices': ['a'], 'directed': True, 'edges': [['a', 'missing']]}, {'a': 'a'}),
                 ({'kind': 'box', 'origin': [0], 'shape': [True]}, {'[0]': 'a'})]
        for index, labels in cases:
            self.refused('word', 'INDEX', alphabet=a, word=self.word(a, index, labels))
        w = self.word(a, {'kind': 'box', 'origin': [0]*4, 'shape': [1]*4}, {'[0,0,0,0]': 'a'})
        self.refused('word', 'UNSUPPORTED', alphabet=a, word=w)

    def test_explicit_search_depth_cell_group_and_output_budgets(self):
        a = alphabet(); vertices = list(map(str, range(9)))
        w = self.word(a, {'kind': 'graph', 'vertices': vertices, 'directed': False, 'edges': []}, dict.fromkeys(vertices, 'a'))
        self.refused('canonicalize', 'RESOURCE_LIMIT', alphabet=a, word=w, relation='graph_isomorphism')
        w['index']['vertices'] = vertices[:6]; w['labels'] = dict.fromkeys(vertices[:6], 'a')
        report = self.refused('canonicalize', 'RESOURCE_LIMIT', alphabet=a, word=w, relation='graph_isomorphism', budgets={'work': 100})
        self.assertNotIn('equivalence_cid', report['result'])
        self.refused('alphabet', 'RESOURCE_LIMIT', alphabet=cyclic_alphabet(), budgets={'work': 5})
        self.refused('word', 'RESOURCE_LIMIT', alphabet=a, word=w, budgets={'cells': 2})
        self.refused('alphabet', 'RESOURCE_LIMIT', alphabet=a, budgets={'output_bytes': 100})
        path = self.word(a, {'kind': 'rooted_tree', 'vertices': vertices, 'root': '0', 'edges': [[str(i), str(i+1)] for i in range(8)]}, dict.fromkeys(vertices, 'a'))
        self.refused('word', 'RESOURCE_LIMIT', alphabet=a, word=path, budgets={'depth': 4})

    def test_malformed_envelopes_untrusted_deserialization_and_no_input_mutation(self):
        a = alphabet(); original = copy.deepcopy(a)
        result = self.passed('alphabet', alphabet=a); result['alphabet']['letters'][0]['value'] = 'changed'
        self.assertEqual(a, original)
        self.refused('alphabet', 'SCHEMA', alphabet=a, arbitrary=True)
        report = run_forms({'version': 'wrong', 'operation': 'alphabet', 'alphabet': a})
        self.assertEqual(report['result']['reason'], 'VERSION')
        self.refused('deserialize', 'SERIALIZATION', alphabet=a, text='{"version":1,"version":2}')
        self.refused('deserialize', 'SERIALIZATION', alphabet=a, text='{"value":NaN}')
        self.refused('deserialize', 'SERIALIZATION', alphabet=a, text='__import__("os").system("true")')
        self.refused('act', 'GROUP', alphabet=a, word=self.word(a, {'kind': 'point'}, {'*': 'a'}), element='missing')
        a['letters'][0]['sources'] = []
        self.refused('alphabet', 'SOURCE', alphabet=a)

    def test_source_pins_are_actual_bytes_and_scope_is_not_full_acceptance(self):
        report = run_forms(request('alphabet', alphabet=alphabet()))
        self.assertEqual(report['status'], 'PASS', report)
        root = Path(__file__).resolve().parents[1]
        for source in report['sources']:
            self.assertEqual(hashlib.sha256((root / source['path']).read_bytes()).hexdigest(), source['sha256'])
            self.assertTrue(source['anchor'])
        self.assertIs(report['mission_acceptance'], False)
        self.assertTrue(any('chemistry' in text.lower() for text in report['limitations']))

    def test_binary_necklace_and_bracelet_counts_against_independent_burnside_formula(self):
        a = alphabet(symbols=('a', 'b'))
        for n in range(3, 8):
            rotations, bracelets = set(), set()
            for values in itertools.product('ab', repeat=n):
                w = self.word(a, {'kind': 'cyclic', 'length': n}, dict(zip(map(str, range(n)), values)))
                rotations.add(self.canonical(a, w, 'cyclic_rotations'))
                bracelets.add(self.canonical(a, w, 'dihedral'))
            rotation_fixed_sum = sum(2**gcd(n, shift) for shift in range(n))
            reflection_fixed_sum = n * 2**((n+1)//2) if n % 2 else n//2 * (2**(n//2) + 2**(n//2+1))
            self.assertEqual(len(rotations), rotation_fixed_sum // n)
            self.assertEqual(len(bracelets), (rotation_fixed_sum + reflection_fixed_sum) // (2*n))

    def test_small_graph_orbit_counts_against_independent_edge_cycle_burnside(self):
        a = alphabet(symbols=('a',))
        for n in range(5):
            vertices = list(map(str, range(n)))
            pairs = list(itertools.combinations(vertices, 2))
            classes = set()
            for edge_bits in itertools.product((False, True), repeat=len(pairs)):
                edges = [list(pair) for pair, include in zip(pairs, edge_bits) if include]
                w = self.word(a, {'kind': 'graph', 'vertices': vertices, 'directed': False, 'edges': edges}, dict.fromkeys(vertices, 'a'))
                classes.add(self.canonical(a, w, 'graph_isomorphism'))
            fixed_sum = 0
            for image in itertools.permutations(vertices):
                rename = dict(zip(vertices, image))
                unseen = set(pairs); cycles = 0
                while unseen:
                    pair = next(iter(unseen)); cycles += 1
                    while pair in unseen:
                        unseen.remove(pair)
                        pair = tuple(sorted((rename[pair[0]], rename[pair[1]])))
                fixed_sum += 2**cycles
            self.assertEqual(len(classes), fixed_sum // factorial(n))
            self.assertEqual(len(classes), [1, 1, 2, 4, 11][n])

    def test_malformed_leaf_mutations_and_recursive_python_values_return_reports(self):
        a = cyclic_alphabet()
        w = self.word(a, {'kind': 'graph', 'vertices': ['x', 'y'], 'directed': True, 'edges': [['x', 'y']]}, {'x': 'a', 'y': 'b'})
        base = request('canonicalize', alphabet=a, word=w, relation='graph_isomorphism')

        def leaf_paths(value, prefix=()):
            if isinstance(value, dict):
                return [path for key, child in value.items() for path in leaf_paths(child, prefix + (key,))]
            if isinstance(value, list):
                return [path for i, child in enumerate(value) for path in leaf_paths(child, prefix + (i,))]
            return [prefix]
        for path in leaf_paths(base):
            for replacement in (None, True, {}, [], 0.5, '', 0, 1 << 257):
                mutated = copy.deepcopy(base); parent = mutated
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = replacement
                report = run_forms(mutated)
                self.assertIn(report['status'], ('PASS', 'REFUSED', 'RESOURCE_LIMIT', 'UNSUPPORTED'))
        recursive = []; recursive.append(recursive)
        report = run_forms(request('alphabet', alphabet=recursive))
        self.assertEqual(report['status'], 'RESOURCE_LIMIT')

    def test_documented_examples_execute_actual_kernel_and_match_literal_expectations(self):
        path = Path(__file__).resolve().parents[1] / 'examples/forms/demo.py'
        self.assertTrue(path.exists(), 'The executable examples must exist')
        spec = importlib.util.spec_from_file_location('forms_demo', path)
        demo = importlib.util.module_from_spec(spec); spec.loader.exec_module(demo)
        result = demo.run_examples()
        self.assertTrue(all(result['checks'].values()))
        self.assertEqual(len(result['checks']), 9)
        self.assertEqual(len(result['calls']), 14)
        self.assertFalse(result['mission_acceptance'])

    def test_successful_serialization_remains_readable_when_json_escaping_expands_envelope(self):
        a = alphabet(symbols=('a',))
        vertices = [str(i) + '\\'*120 for i in range(30)]
        edges = [[u, v] for u in vertices for v in vertices][:260]
        w = self.word(a, {'kind': 'graph', 'vertices': vertices, 'edges': edges, 'directed': True}, dict.fromkeys(vertices, 'a'))
        text = self.passed('serialize', alphabet=a, word=w)['text']
        self.assertGreater(len(json.dumps(request('deserialize', alphabet=a, text=text)).encode()), 262144)
        restored = self.passed('deserialize', alphabet=a, text=text)['word']
        self.assertEqual(restored, w)
        self.refused('deserialize', 'RESOURCE_LIMIT', alphabet=a, text=' ' * 262145)


if __name__ == '__main__':
    unittest.main()
