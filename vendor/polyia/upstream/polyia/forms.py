"""Exact, bounded typed alphabets and finite labeled index structures.

This module is pure: no file/network/model access and no evaluator strings.
Structural orbit equivalence is explicitly separate from domain denotation.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
from itertools import permutations, product
import json
from math import factorial, prod
import re

VERSION = 'polyia.forms/0.1'
ALPHABET = 'polyia.alphabet/0.1'
WORD = 'polyia.word/0.1'
PINS = (
    ('GOD_SEED.md', '4f179f83ff2279e1bf3e471ac8edc80456b9fdff29548332bf5b649a3c724f38', 'PIA-050, PIA-051'),
    ('docs/SCIENTIFIC_FOUNDATIONS.md', '78dff0f8c6637449d043e3816d2d4f6cfc5a42a2d4aad6dd662f2d6b5e9cd8f0', 'SF-01, SF-02'),
    ('docs/FORMAL_VOCABULARY.md', '45455b3d908b5ca978a510902337c08363478db378aa52b0825c91a5deb5ce24', 'FV-01 through FV-09; especially FV-03, FV-04, FV-05'),
    ('sources/originals/PLICASTRATUM.md', '3a11ee1c6998d740cd556847ae8b64115bdac17c21e78efa85c5701e2606fcdd', '§§2.1–2.2, 4 D1–D3, 6.3, 7; complete source read'),
    ('sources/originals/UCG_CODEX_CONSTITUTIONAL_COMMISSION.md', '0cf03197777e19330ce36cf478bec9a5c4cad5459fd142c37eb4ae0e82bd6d7e', '§013 Alphabet kinds; §014 Words of any rank'),
    ('sources/originals/UCG_FOUNDATIONS.md', '699d8e6bbb286b41512f746bd27fb353d506d7a7f7128e80dd41a27479043d1d', '§§0–1, 3.1–3.3, 5; complete source read'),
)
LIMITATIONS = (
    'Established finite permutation/group algorithms implement a chosen versioned representation; no general semantic preservation is asserted.',
    'Only the named structural equivalence is checked. Alphabet permutations preserve declared sorts, not inferred geometry, sound, physics or chemistry.',
    'A supplied periodic-table layout is data, not an aufbau, valence or molecular generative law. UCG-055/062/066/102 remain open.',
    'Graph words are simple directed or undirected vertex-labeled graphs with optional loops; no multiedges, edge labels, hyperedges or general graph grammar.',
    'Graph canonicalization exhausts vertex permutations within the declared budget; larger cases return RESOURCE_LIMIT without an equivalence digest.',
    'Tree canonicalization is for rooted unordered labeled trees; boxes have rank 0 through 3 and ordered coordinates. No implicit lattice isometry is applied.',
    'Naturals supplies an effective definition and individual bounded queries, never a finite enumeration of infinity. Generated products are unsupported.',
    'Serialization restores JSON values and complete labeled structure, not original whitespace or original JSON bytes. Quotients are not reversible encodings.',
    'Source references supplied with letters are custody declarations, not independently authenticated facts. Embedded implementation source pins are not read at runtime.',
    'No chemical domain validation, acoustic synthesis, native compiler integration, store/API registration or full mission acceptance is supplied.',
)
CAPS = {'work': 1_000_000, 'cells': 256, 'depth': 64, 'output_bytes': 524_288}
OPERATIONS = {
    'alphabet': (('alphabet',), ()),
    'product': (('components', 'entity_id', 'interpretation', 'sources'), ()),
    'member': (('alphabet', 'candidate'), ()),
    'generate': (('alphabet', 'index'), ()),
    'word': (('alphabet', 'word'), ()),
    'serialize': (('alphabet', 'word'), ()),
    'deserialize': (('alphabet', 'text'), ()),
    'act': (('alphabet', 'word', 'element'), ()),
    'layout': (('alphabet', 'word', 'coordinates'), ()),
    'canonicalize': (('alphabet', 'word', 'relation'), ('alphabet_symmetry',)),
}


class Refusal(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(detail)


def need(condition, code, detail):
    if not condition:
        raise Refusal(code, detail)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def cid(value):
    return hashlib.sha256(encoded(value).encode('utf-8')).hexdigest()


def obj(value, required, optional=()):
    need(type(value) is dict and set(required) <= value.keys()
         and value.keys() <= set(required) | set(optional), 'SCHEMA', 'Missing or unknown object fields')


def string(value, maximum=128, code='SCHEMA'):
    need(type(value) is str and 0 < len(value) <= maximum, code, 'Expected a nonempty bounded string')
    return value


def integer(value, code='TYPE'):
    need(type(value) is int, code, 'Expected an integer, without boolean coercion')
    need(value.bit_length() <= 256, 'RESOURCE_LIMIT', 'Integer exceeds 256-bit query bound')
    return value


def json_guard(value, serialized_envelope=False):
    """Bound hostile Python/JSON inputs before hashing, copying or descent."""
    nodes = 0
    bytes_seen = 0

    def visit(item, depth):
        nonlocal nodes, bytes_seen
        nodes += 1
        need(nodes <= 30000 and depth <= 32, 'RESOURCE_LIMIT', 'JSON node/depth budget exceeded')
        if type(item) is str:
            need(len(item) <= 262144, 'RESOURCE_LIMIT', 'String size budget exceeded')
            try:
                bytes_seen += len(item.encode('utf-8'))
            except UnicodeEncodeError:
                raise Refusal('SCHEMA', 'Unicode scalar values required') from None
            need(bytes_seen <= 262144, 'RESOURCE_LIMIT', 'Input string byte budget exceeded')
        elif type(item) is int:
            integer(item)
        elif type(item) in (dict, list):
            need(len(item) <= 4096, 'RESOURCE_LIMIT', 'JSON collection budget exceeded')
            if type(item) is dict:
                for key, child in item.items():
                    need(type(key) is str, 'SCHEMA', 'JSON object keys must be strings')
                    visit(key, depth+1); visit(child, depth+1)
            else:
                for child in item:
                    visit(child, depth+1)
        else:
            need(item is None or type(item) is bool, 'TYPE', 'Only discrete JSON input is admitted; floats are not exact rationals')
    visit(value, 0)
    # A serialized JSON word is itself a JSON string. Escaping that string may
    # double its encoded size while leaving the bounded logical input intact.
    encoded_cap = 524288 if serialized_envelope and type(value) is dict and value.get('operation') == 'deserialize' else 262144
    need(len(encoded(value).encode('utf-8')) <= encoded_cap, 'RESOURCE_LIMIT', 'Encoded input exceeds its bounded envelope size')


class Budget:
    def __init__(self, caps, work=0):
        self.caps = caps
        self.work = work

    def charge(self, amount):
        need(self.work + amount <= self.caps['work'], 'RESOURCE_LIMIT',
             f'Exact computation needs additional {amount} work units; {self.caps["work"]-self.work} remain')
        self.work += amount


def budget_for(value):
    need(type(value) is dict and value.keys() <= CAPS.keys(), 'SCHEMA', 'Unknown budget field')
    limits = dict(CAPS)
    for key, amount in value.items():
        need(type(amount) is int and 1 <= amount <= CAPS[key], 'SCHEMA', 'Budgets may only lower positive hard caps')
        limits[key] = amount
    return Budget(limits)


def rational(value):
    need(type(value) is str, 'TYPE', 'Exact rational must be a canonical string')
    need(len(value) <= 160, 'RESOURCE_LIMIT', 'Rational text exceeds budget')
    need(re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?', value) is not None,
         'RATIONAL', 'Expected canonical integer or reduced p/q, q positive')
    parts = value.split('/')
    numerator, denominator = int(parts[0]), int(parts[1]) if len(parts) == 2 else 1
    integer(numerator); integer(denominator)
    need(str(Fraction(numerator, denominator)) == value, 'RATIONAL', 'Rational must be reduced with canonical sign')
    return value


def coordinates(value, maximum=16):
    need(type(value) is list and 1 <= len(value) <= maximum, 'SCHEMA', 'Coordinate vector requires a bounded positive dimension')
    for component in value:
        rational(component)


def source_refs(value):
    need(type(value) is list and 1 <= len(value) <= 16, 'SOURCE', 'Nonempty bounded source references required')
    for source in value:
        obj(source, ('source', 'anchor', 'sha256'))
        string(source['source'], 512, 'SOURCE'); string(source['anchor'], 1024, 'SOURCE')
        need(type(source['sha256']) is str and re.fullmatch('[0-9a-f]{64}', source['sha256']),
             'SOURCE', 'Source digest must be lowercase SHA-256')


def vertex_graph(index, budget, tree=False):
    obj(index, ('kind', 'vertices', 'edges', 'root') if tree else ('kind', 'vertices', 'edges', 'directed'))
    vertices = index['vertices']
    need(type(vertices) is list, 'INDEX', 'Vertices must be an explicit list')
    need(len(vertices) <= budget.caps['cells'], 'RESOURCE_LIMIT', 'Vertex budget exceeded')
    for v in vertices:
        string(v, 128, 'INDEX')
    need(len(set(vertices)) == len(vertices), 'INDEX', 'Duplicate vertex identities')
    edges = index['edges']
    need(type(edges) is list and len(edges) <= 4096, 'INDEX', 'Edges must be a bounded list')
    if not tree:
        need(type(index['directed']) is bool, 'INDEX', 'Directed flag must be boolean')
    directed = tree or index['directed']
    seen, children, indegree = set(), {v: [] for v in vertices}, dict.fromkeys(vertices, 0)
    for edge in edges:
        need(type(edge) is list and len(edge) == 2 and all(type(v) is str and v in children for v in edge),
             'INDEX', 'Edge endpoints must name existing vertices')
        u, v = edge
        key = tuple(edge) if directed else tuple(sorted(edge))
        need(key not in seen, 'INDEX', 'Parallel/duplicate edges are outside simple graph profile')
        seen.add(key); children[u].append(v); indegree[v] += 1
    budget.charge(len(vertices) + len(edges))
    if tree:
        root = index['root']
        need(type(root) is str and root in children and indegree[root] == 0
             and all(indegree[v] == 1 for v in vertices if v != root), 'INDEX', 'Rooted tree requires one parent per non-root')
        reached, pending = set(), [(root, 1)]
        while pending:
            v, depth = pending.pop()
            need(depth <= budget.caps['depth'], 'RESOURCE_LIMIT', 'Tree depth budget exceeded')
            need(v not in reached, 'INDEX', 'Tree contains a cycle')
            reached.add(v)
            pending.extend((child, depth+1) for child in children[v])
        need(reached == set(vertices), 'INDEX', 'Tree must be connected and acyclic')
    return vertices


def letter_value(kind, value, budget):
    if kind == 'lettered':
        string(value, 1024)
    elif kind == 'numeric':
        rational(value)
    elif kind == 'phonetic':
        obj(value, ('notation', 'transcription'))
        need(value['notation'] in ('ipa', 'opaque'), 'UNSUPPORTED', 'Phonetic notation must be declared ipa or opaque')
        string(value['transcription'], 1024)
    elif kind == 'geometric':
        obj(value, ('shape', 'vertices', 'ports'))
        need(value['shape'] in ('point', 'segment', 'polygon'), 'UNSUPPORTED', 'Unsupported geometric shape')
        vertices = value['vertices']
        need(type(vertices) is list and 1 <= len(vertices) <= 64, 'SCHEMA', 'Bounded shape vertices required')
        expected = {'point': 1, 'segment': 2}.get(value['shape'])
        need(len(vertices) == expected if expected else len(vertices) >= 3, 'SCHEMA', 'Shape vertex count mismatch')
        for vertex in vertices:
            coordinates(vertex, 3)
        need(len({len(v) for v in vertices}) == 1 and len({tuple(v) for v in vertices}) == len(vertices),
             'SCHEMA', 'Shape vertices must have common dimension and distinct positions')
        ports = value['ports']
        need(type(ports) is list and len(ports) <= len(vertices), 'SCHEMA', 'Ports identify vertices in listed order')
        for port in ports:
            string(port)
        need(len(set(ports)) == len(ports), 'SCHEMA', 'Duplicate shape ports')
    elif kind == 'retial':
        obj(value, ('vertices', 'edges', 'directed'))
        vertex_graph({'kind': 'graph', **value}, budget)


def finite_group(value, letters, budget):
    obj(value, ('elements',))
    elements = value['elements']
    need(type(elements) is list and 1 <= len(elements) <= 64, 'RESOURCE_LIMIT', 'Finite group requires 1..64 explicitly enumerated elements')
    symbols = [letter['id'] for letter in letters]
    positions = {s: i for i, s in enumerate(symbols)}
    names, actions = [], []
    for element in elements:
        obj(element, ('id', 'images')); names.append(string(element['id'], 512, 'GROUP'))
        images = element['images']
        need(type(images) is list and len(images) == len(symbols)
             and all(type(s) is str for s in images) and set(images) == set(symbols), 'GROUP', 'Each action must permute every letter exactly once')
        action = tuple(positions[s] for s in images)
        need(all(letters[i]['sort'] == letters[j]['sort'] for i, j in enumerate(action)), 'TYPE', 'Alphabet actions must preserve declared sorts')
        actions.append(action)
    need(len(set(names)) == len(names) and len(set(actions)) == len(actions), 'GROUP', 'Group ids and permutation actions must be unique')
    identity = tuple(range(len(symbols)))
    need(identity in actions, 'GROUP', 'Permutation group lacks the identity')
    lookup = {action: i for i, action in enumerate(actions)}
    budget.charge(len(actions)**2 * max(1, len(symbols)))
    table, inverses = [], {}
    for i, g in enumerate(actions):
        row = []
        for j, h in enumerate(actions):
            composite = tuple(g[h[k]] for k in range(len(symbols)))
            need(composite in lookup, 'GROUP', 'Listed permutations are not closed under composition')
            row.append(names[lookup[composite]])
            if composite == identity:
                inverses[names[i]] = names[j]
        table.append(row)
    need(len(inverses) == len(names), 'GROUP', 'Every group element must have an inverse')
    return names, actions, {'order': len(names), 'elements': names, 'identity': names[lookup[identity]],
                            'inverse': inverses, 'multiplication': table,
                            'convention': 'row g, column h means g after h: (gh)(x)=g(h(x))'}


class ResolvedAlphabet:
    def __init__(self, raw, content_cid, letters, names, actions, group, generator=False):
        self.raw = raw
        self.content_cid = content_cid
        self.letters = letters
        self.names = names
        self.actions = actions
        self.group = group
        self.generator = generator

    def summary(self):
        return {'alphabet': copy.deepcopy(self.raw), 'content_cid': self.content_cid,
                'entity_id': self.raw['entity_id'], 'letter_count': None if self.generator else len(self.letters),
                'cardinality': 'countably-infinite-definition' if self.generator else 'finite',
                'resolved_letters': copy.deepcopy(self.letters), 'group': copy.deepcopy(self.group)}

    def has(self, symbol):
        if self.generator:
            if type(symbol) is not str or re.fullmatch(r'0|[1-9][0-9]*', symbol) is None:
                return False
            need(len(symbol) <= 78, 'RESOURCE_LIMIT', 'Generated letter identity exceeds integer budget')
            integer(int(symbol))
            return True
        return symbol in {letter['id'] for letter in self.letters}

    def generated(self, index):
        integer(index)
        need(index >= 0, 'DOMAIN', 'Natural index must be nonnegative')
        return {'id': str(index), 'sort': 'Natural', 'value': str(index),
                'coordinates': [str(index)], 'sources': copy.deepcopy(self.raw['sources'])}


def resolve_alphabet(raw, budget, depth=0):
    need(depth <= 4, 'RESOURCE_LIMIT', 'Product alphabet nesting exceeds four levels')
    base = ('version', 'entity_id', 'kind', 'interpretation', 'sources')
    need(type(raw) is dict, 'SCHEMA', 'Alphabet must be an object')
    kind = raw.get('kind')
    need(type(kind) is str and kind in ('lettered', 'numeric', 'geometric', 'retial', 'phonetic', 'product'), 'UNSUPPORTED', 'Unknown alphabet kind')
    fields = ('components',) if kind == 'product' else (('generator', 'group') if 'generator' in raw else ('letters', 'group'))
    obj(raw, base + fields)
    need(raw['version'] == ALPHABET, 'VERSION', 'Unsupported alphabet version')
    string(raw['entity_id']); string(raw['interpretation'], 4096); source_refs(raw['sources'])
    content_cid = cid({k: v for k, v in raw.items() if k != 'entity_id'})
    if kind == 'product':
        components = raw['components']
        need(type(components) is list and len(components) == 2, 'SCHEMA', 'Product alphabet requires exactly two components; nested products are explicit')
        left, right = [resolve_alphabet(c, budget, depth+1) for c in components]
        need(not left.generator and not right.generator, 'UNSUPPORTED', 'Only finite alphabet products are implemented')
        need(len(left.letters)*len(right.letters) <= 128 and len(left.names)*len(right.names) <= 64,
             'RESOURCE_LIMIT', 'Product letter/group size exceeds finite bounds')
        pairs = list(product(range(len(left.letters)), range(len(right.letters))))
        ids = {pair: encoded([left.letters[pair[0]]['id'], right.letters[pair[1]]['id']]) for pair in pairs}
        letters = []
        for i, j in pairs:
            a, b = left.letters[i], right.letters[j]
            sources = {encoded(s): s for s in a['sources'] + b['sources']}
            coords = a['coordinates'] + b['coordinates']; coordinates(coords)
            letters.append({'id': ids[i, j], 'sort': encoded([a['sort'], b['sort']]),
                            'value': [a['id'], b['id']], 'coordinates': coords,
                            'sources': [copy.deepcopy(sources[key]) for key in sorted(sources)]})
        elements = [{'id': encoded([left.names[g], right.names[h]]),
                     'images': [ids[left.actions[g][i], right.actions[h][j]] for i, j in pairs]}
                    for g, h in product(range(len(left.names)), range(len(right.names)))]
        names, actions, group = finite_group({'elements': elements}, letters, budget)
    elif 'generator' in raw:
        need(kind == 'numeric', 'UNSUPPORTED', 'Effective generators currently support numeric Naturals only')
        generator = raw['generator']; obj(generator, ('name', 'start', 'coordinates'))
        need(generator['name'] == 'naturals', 'UNSUPPORTED', 'No evaluator strings or unknown generators')
        need(type(generator['start']) is int and generator['start'] == 0 and generator['coordinates'] == 'value',
             'SCHEMA', 'Naturals starts at zero with the exact value coordinate')
        obj(raw['group'], ('elements',)); elements = raw['group']['elements']
        need(type(elements) is list and len(elements) == 1, 'GROUP', 'Naturals supports only the explicit identity action')
        obj(elements[0], ('id', 'rule')); name = string(elements[0]['id'], 512, 'GROUP')
        need(elements[0]['rule'] == 'identity', 'GROUP', 'Unknown infinite-alphabet action')
        budget.charge(1)
        group = {'order': 1, 'elements': [name], 'identity': name, 'inverse': {name: name},
                 'multiplication': [[name]], 'convention': 'identity function on every natural; no domain enumeration'}
        return ResolvedAlphabet(raw, content_cid, [], [name], [()], group, True)
    else:
        letters = raw['letters']
        need(type(letters) is list and 1 <= len(letters) <= 128, 'RESOURCE_LIMIT', 'Finite alphabet requires 1..128 explicit letters')
        for letter in letters:
            obj(letter, ('id', 'sort', 'value', 'coordinates', 'sources'))
            string(letter['id']); string(letter['sort']); source_refs(letter['sources']); coordinates(letter['coordinates'])
            letter_value(kind, letter['value'], budget)
        need(len({l['id'] for l in letters}) == len(letters), 'SCHEMA', 'Letter identities must be unique')
        need(len({len(l['coordinates']) for l in letters}) == 1, 'SCHEMA', 'Alphabet coordinates must have a common dimension')
        names, actions, group = finite_group(raw['group'], letters, budget)
    return ResolvedAlphabet(raw, content_cid, letters, names, actions, group)


def index_keys(index, budget):
    need(type(index) is dict and type(index.get('kind')) is str, 'INDEX', 'An explicit index kind is required')
    kind = index['kind']
    if kind == 'point':
        obj(index, ('kind',)); keys = ['*']
    elif kind in ('sequence', 'tuple', 'cyclic', 'multiset'):
        field = 'size' if kind == 'multiset' else 'length'
        obj(index, ('kind', field)); count = integer(index[field], 'INDEX')
        need(count >= 0, 'INDEX', 'Index size cannot be negative')
        need(count <= budget.caps['cells'], 'RESOURCE_LIMIT', 'Word cell budget exceeded')
        keys = list(map(str, range(count)))
    elif kind == 'box':
        obj(index, ('kind', 'origin', 'shape'))
        origin, shape = index['origin'], index['shape']
        need(type(origin) is list and type(shape) is list and len(origin) == len(shape), 'INDEX', 'Box origin and shape must have equal rank')
        need(len(shape) <= 3, 'UNSUPPORTED', 'Only box ranks 0..3 are implemented')
        for start, size in zip(origin, shape):
            integer(start, 'INDEX'); integer(size, 'INDEX')
            need(size >= 0, 'INDEX', 'Box extent cannot be negative')
            need(size <= budget.caps['cells'], 'RESOURCE_LIMIT', 'Box axis extent exceeds budget')
            integer(start+size, 'INDEX')
        need(prod(shape) <= budget.caps['cells'], 'RESOURCE_LIMIT', 'Box cell budget exceeded')
        keys = [encoded(list(c)) for c in product(*(range(start, start+size) for start, size in zip(origin, shape)))]
    elif kind in ('graph', 'rooted_tree'):
        keys = vertex_graph(index, budget, tree=kind == 'rooted_tree')
    else:
        raise Refusal('UNSUPPORTED', 'Unsupported finite index structure')
    budget.charge(len(keys))
    return keys


def view_coordinates(value, keys):
    need(type(value) is dict and set(value) == set(keys), 'INDEX', 'View must locate every existing cell and cannot add incidence')
    for vector in value.values():
        coordinates(vector, 3)
    need(len({len(vector) for vector in value.values()}) <= 1, 'SCHEMA', 'View coordinates must have a common dimension')


def validate_word(word, alphabet, budget):
    obj(word, ('version', 'entity_id', 'alphabet_cid', 'index', 'labels'), ('view',))
    need(word['version'] == WORD, 'VERSION', 'Unsupported word version')
    string(word['entity_id'])
    need(word['alphabet_cid'] == alphabet.content_cid, 'ALPHABET_BINDING', 'Word must bind the exact alphabet content digest')
    keys = index_keys(word['index'], budget)
    labels = word['labels']
    need(type(labels) is dict and set(labels) == set(keys), 'INDEX', 'Word labels must cover exactly the index cells')
    for label in labels.values():
        need(type(label) is str and alphabet.has(label), 'UNKNOWN_LETTER', 'Label is not admitted by this alphabet')
    if 'view' in word:
        obj(word['view'], ('coordinates',)); view_coordinates(word['view']['coordinates'], keys)
    return keys


def word_summary(word):
    content = {key: word[key] for key in ('version', 'alphabet_cid', 'index', 'labels')}
    return {'word': copy.deepcopy(word), 'entity_id': word['entity_id'], 'content_cid': cid(content),
            'representation_cid': cid(word), 'view_cid': cid(word['view']) if 'view' in word else None}


def act(word, alphabet, element):
    need(type(element) is str and element in alphabet.names, 'GROUP', 'Unknown alphabet group element')
    result = copy.deepcopy(word)
    if not alphabet.generator:
        action = alphabet.actions[alphabet.names.index(element)]
        renaming = {letter['id']: alphabet.letters[action[i]]['id'] for i, letter in enumerate(alphabet.letters)}
        result['labels'] = {key: renaming[label] for key, label in word['labels'].items()}
    return result


RELATIONS = {'identity': None, 'ordered': ('point', 'sequence', 'tuple', 'box'),
             'multiset': ('multiset',), 'cyclic_rotations': ('cyclic',), 'dihedral': ('cyclic',),
             'rooted_unordered_tree': ('rooted_tree',), 'graph_isomorphism': ('graph',)}


def canonical_index(word, keys, relation, budget):
    index, labels = word['index'], word['labels']
    kind = index['kind']
    values = [labels[key] for key in keys]
    if relation == 'identity':
        budget.charge(len(keys))
        return {'index': copy.deepcopy(index), 'labels': copy.deepcopy(labels)}, 1
    if relation == 'ordered':
        budget.charge(len(keys))
        return {'index': copy.deepcopy(index), 'labels': values}, 1
    if relation == 'multiset':
        budget.charge(max(1, len(keys))**2)
        return {'index': {'kind': kind, 'size': len(keys)}, 'labels': sorted(values)}, 1
    if relation in ('cyclic_rotations', 'dihedral'):
        n = len(values)
        budget.charge(max(1, n)**2 * (2 if relation == 'dihedral' else 1))
        candidates = [values[i:] + values[:i] for i in range(n)] or [[]]
        if relation == 'dihedral':
            reverse = list(reversed(values))
            candidates.extend(reverse[i:] + reverse[:i] for i in range(n))
        return {'index': {'kind': kind, 'length': n}, 'labels': min(candidates)}, len(candidates)
    if relation == 'rooted_unordered_tree':
        children = {key: [] for key in keys}
        for parent, child in index['edges']:
            children[parent].append(child)
        budget.charge(max(1, len(keys))**2)

        def code(vertex):
            branches = [code(child) for child in children[vertex]]
            branches.sort(key=encoded)
            return [labels[vertex], branches]
        return {'index': {'kind': kind}, 'root': code(index['root'])}, 1
    # All vertex renamings are actually exhausted. Degree sequences are insufficient.
    n = len(keys)
    need(n <= 8, 'RESOURCE_LIMIT', 'Exact graph canonicalization supports at most eight vertices')
    count = factorial(n)
    budget.charge(count * max(1, n + len(index['edges'])))
    best, best_text = None, None
    for order in permutations(keys):
        numbering = {vertex: i for i, vertex in enumerate(order)}
        edges = [[numbering[u], numbering[v]] for u, v in index['edges']]
        if not index['directed']:
            edges = [sorted(edge) for edge in edges]
        edges.sort()
        candidate = {'index': {'kind': 'graph', 'size': n, 'directed': index['directed'], 'edges': edges},
                     'labels': [labels[v] for v in order]}
        text = encoded(candidate)
        if best_text is None or text < best_text:
            best, best_text = candidate, text
    return best, count


def strict_loads(text):
    need(type(text) is str, 'SERIALIZATION', 'Serialized word must be JSON text')

    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'SERIALIZATION', 'Duplicate JSON object key')
            result[key] = value
        return result

    def constant(value):
        raise Refusal('SERIALIZATION', 'Nonfinite JSON constants are not admitted')
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError) as exc:
        if isinstance(exc, Refusal):
            raise
        raise Refusal('SERIALIZATION', 'Invalid or excessively deep serialized JSON') from None
    json_guard(value)
    return value


def run_forms(parameters):
    """Return deterministic PASS/REFUSED/UNSUPPORTED/RESOURCE_LIMIT reports.

    No report authorizes an effect or certifies broader mission acceptance.
    All returned objects are detached from caller-owned mutable inputs.
    """
    checks, budget = [], Budget(dict(CAPS))
    result, status = {}, 'PASS'
    try:
        json_guard(parameters, serialized_envelope=True)
        need(type(parameters) is dict and parameters.get('version') == VERSION, 'VERSION', 'Unsupported forms envelope version')
        operation = parameters.get('operation')
        need(type(operation) is str and operation in OPERATIONS, 'UNSUPPORTED', 'Unknown structured-forms operation')
        required, optional = OPERATIONS[operation]
        obj(parameters, {'version', 'operation'} | set(required), {'budgets'} | set(optional))
        budget = budget_for(parameters.get('budgets', {}))
        if operation == 'product':
            raw = {'version': ALPHABET, 'kind': 'product', **{key: parameters[key] for key in required}}
        else:
            raw = parameters['alphabet']
        alphabet = resolve_alphabet(raw, budget)
        checks.append({'name': 'typed-alphabet-and-declared-group', 'passed': True,
                       'scope': 'validated exact permutations or built-in natural identity; supplied sources are references'})
        if operation in ('alphabet', 'product'):
            result = alphabet.summary()
        elif operation in ('member', 'generate'):
            need(alphabet.generator, 'UNSUPPORTED', 'Individual effective-generator operations require a Naturals alphabet')
            if operation == 'member':
                candidate = integer(parameters['candidate'])
                result = {'member': candidate >= 0, 'domain': 'Naturals-including-zero', 'enumerated': False}
            else:
                result = {'letter': alphabet.generated(parameters['index']), 'enumerated': False}
            checks.append({'name': 'bounded-natural-query', 'passed': True})
        else:
            word = strict_loads(parameters['text']) if operation == 'deserialize' else parameters['word']
            keys = validate_word(word, alphabet, budget)
            checks.append({'name': 'complete-labeling-and-index-structure', 'passed': True})
            if operation in ('word', 'deserialize', 'serialize'):
                result = word_summary(word)
                if operation == 'serialize':
                    result['text'] = encoded(word)
            elif operation == 'act':
                budget.charge(len(keys))
                transformed = act(word, alphabet, parameters['element'])
                result = word_summary(transformed)
                result['preserved_relation'] = 'same-index-with-sort-preserving-pointwise-letter-action'
                checks.append({'name': 'declared-letter-permutation', 'passed': True})
            elif operation == 'layout':
                view_coordinates(parameters['coordinates'], keys)
                transformed = copy.deepcopy(word)
                transformed['view'] = {'coordinates': copy.deepcopy(parameters['coordinates'])}
                result = word_summary(transformed)
                need(result['content_cid'] == word_summary(word)['content_cid'], 'INTERNAL', 'View changed labeled content')
                checks.append({'name': 'layout-preserves-index-and-labels', 'passed': True})
            else:
                relation = parameters['relation']
                need(type(relation) is str and relation in RELATIONS, 'RELATION', 'Unknown equivalence relation')
                need(RELATIONS[relation] is None or word['index']['kind'] in RELATIONS[relation], 'RELATION', 'Relation does not apply to this index kind')
                symmetry = parameters.get('alphabet_symmetry', False)
                need(type(symmetry) is bool, 'TYPE', 'Alphabet symmetry must be an explicit boolean')
                elements = alphabet.names if symmetry else [alphabet.group['identity']]
                best, best_key, selected, orbit = None, None, None, None
                for element in elements:
                    transformed = act(word, alphabet, element)
                    form, count = canonical_index(transformed, keys, relation, budget)
                    key = encoded(form)
                    if best_key is None or key < best_key:
                        best, best_key, selected, orbit = form, key, element, count
                canonical = {'version': 'polyia.form-quotient/0.1', 'alphabet_cid': alphabet.content_cid,
                             'relation': relation, 'alphabet_symmetry': symmetry, 'form': best}
                result = {'canonical': canonical, 'equivalence_cid': cid(canonical),
                          'alphabet_element': selected, 'alphabet_elements_checked': len(elements),
                          'index_candidates_checked': orbit,
                          'candidate_count_meaning': 'candidate transformations checked per alphabet element, not number of distinct orbit images; tree/multiset use direct canonical algorithms',
                          'preserved_relation': 'declared-structural-orbit-only'}
                checks.append({'name': 'complete-bounded-canonicalization', 'passed': True})
        need(len(encoded(result).encode('utf-8')) <= budget.caps['output_bytes'], 'RESOURCE_LIMIT', 'Result output byte budget exceeded')
    except Refusal as exc:
        status = exc.code if exc.code in ('RESOURCE_LIMIT', 'UNSUPPORTED') else 'REFUSED'
        result = {'reason': exc.code, 'detail': str(exc), 'complete': False}
        checks.append({'name': 'requested-operation-completed', 'passed': False})
    return {'version': VERSION, 'status': status, 'evidence_class': 'EXACTLY_CHECKED' if status == 'PASS' else 'NO_RESULT',
            'result': result, 'checks': checks, 'work_used': budget.work, 'budgets': dict(budget.caps),
            'sources': [{'path': path, 'sha256': digest, 'anchor': anchor} for path, digest, anchor in PINS],
            'limitations': list(LIMITATIONS), 'mission_acceptance': False, 'llm_inference': False, 'effects': []}
