"""Constructive, bounded regular-language and polynomial exercise generators.

Cards, compiled semantic packages, execution receipts and prose views are distinct
objects. No user Python, network, subprocess or model inference is executed.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
from itertools import product
import json
import re

VERSION = 'polyia.generators/0.1'
CARD = 'polyia.generator-card/0.1'
PACKAGE = 'polyia.generator-package/0.1'
LIMITS = {'input_nodes': 200000, 'input_depth': 32, 'string_bytes': 2097152,
          'ast_nodes': 64, 'ast_depth': 12, 'word_length': 32, 'nfa_states': 512,
          'dfa_states': 128, 'queue': 8192, 'work_units': 200000,
          'candidates': 256, 'rational_bits': 256, 'output_bytes': 2097152}
SOURCES = (
    ('sources/originals/UCG_CODEX_CONSTITUTIONAL_COMMISSION.md',
     '0cf03197777e19330ce36cf478bec9a5c4cad5459fd142c37eb4ae0e82bd6d7e', '040,123-132,135,152'),
    ('sources/recovered/CODEX_CONSTITUTION.md',
     'cfe0b88f9c701e139372d783db1d9568da272f6433f9e513d6475fe7985a2630', 'C-020,021,030,051,053,064,069,070,076'),
    ('sources/originals/RELATIONAL_GENERATIVITY_FOUNDATION_V0_1.md',
     '359a3d584a06c3fd3cb30ebd43c9a3d7781ecc7e33ba6846823bf3758d7c528f', '3,5,8'),
    ('sources/expanded/POLYIA_FOUNDATION_V0_1/POLYIA_FOUNDATION_V0_1/docs/TECHNICAL_TREATISE.md',
     'bed750d816b54029a59ff933361cc5ad15709de14b59b595735d6e95439a2e01', '1,3-7,10'),
    ('sources/repos/computationalgrammartheory/CGT_SDK_SPEC.md',
     '4ed9074c9d1713f4aba14da0f21de08bfea192fdba57bcefcf8219886e87ca9f', '2.1,2.2,2.3,4,5'),
    ('docs/SCIENTIFIC_FOUNDATIONS.md',
     '78dff0f8c6637449d043e3816d2d4f6cfc5a42a2d4aad6dd662f2d6b5e9cd8f0', 'SF-06,07,08'),
    ('GOD_SEED.md',
     '4f179f83ff2279e1bf3e471ac8edc80456b9fdff29548332bf5b649a3c724f38', 'PIA-097..PIA-108'),
    ('docs/FORMAL_VOCABULARY.md',
     '45455b3d908b5ca978a510902337c08363478db378aa52b0825c91a5deb5ce24', 'FV-01..FV-09'),
    ('sources/expanded/POLYIA_FOUNDATION_V0_1/POLYIA_FOUNDATION_V0_1/docs/STATE_MACHINE.md',
     '48c38a2a24128513fc45c091ba1c26c61feb4cd48a3062f876bb560c6d05fa5e', 'state graph and representation boundary'),
    ('sources/expanded/POLYIA_FOUNDATION_V0_1/POLYIA_FOUNDATION_V0_1/docs/CONCIERGE_CONTRACT.md',
     '0400c89054a4fa88cbb40f8312d38f9548f6373f666746874d7005e30b31692b', 'intent coverage, source custody and refusal'),
    ('sources/expanded/TRE_TREE_FOUNDATIONS_RESEARCH_PACKET_V01/TRE_TREE_FOUNDATIONS_V01/docs/01_MACHINE_COMPILER.md',
     '8955e70c7d48bb47588f863382df6c3a046a2301d4701ef84d4fe4bc29d5a14b', 'typed machine construction and verification'),
)
LIMITATIONS = (
    'Two finite registered families; no arbitrary program synthesis or open-domain language understanding.',
    'Finite exact checks establish stated objects, not full D-GENERATORS or inherited benchmark acceptance.',
    'Source pins are references; pure operations do not read or authenticate source files.',
    'Python and its standard library are trusted; this is a fixed interpreter, not an OS sandbox.',
    'No stochastic component, learned parameters, neural model, network or external tool is used.',
    'Work and state metrics are counted operations, not wall-clock latency or measured energy.',
    'Regular packages use a declared finite-machine IR; they do not complete the general native compiler backend.',
)
NAME = re.compile(r'[A-Za-z][A-Za-z0-9_.-]{0,63}\Z')
RATIONAL = re.compile(r'-?[0-9]+(?:/[1-9][0-9]*)?\Z')


class Refusal(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(detail)


def _need(condition, code, detail):
    if not condition:
        raise Refusal(code, detail)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _cid(kind, value):
    return hashlib.sha256((kind + '\0' + _json(value)).encode('utf-8')).hexdigest()


def _copy(value):
    return json.loads(_json(value))


def _guard(value):
    count, size, stack = 0, 0, [(value, 0)]
    while stack:
        item, depth = stack.pop(); count += 1
        _need(count <= LIMITS['input_nodes'] and depth <= LIMITS['input_depth'], 'RESOURCE_LIMIT', 'Input nesting or item bound exceeded.')
        if type(item) is dict:
            _need(len(item) <= 4096 and all(type(k) is str for k in item), 'SCHEMA', 'Objects require bounded string keys.')
            stack.extend((x, depth+1) for pair in item.items() for x in pair)
        elif type(item) is list:
            _need(len(item) <= 8192, 'RESOURCE_LIMIT', 'Input array bound exceeded.')
            stack.extend((x, depth+1) for x in item)
        elif type(item) is str:
            try: size += len(item.encode('utf-8'))
            except UnicodeError: raise Refusal('INVALID_UNICODE', 'Unicode scalar values are required.') from None
            _need(size <= LIMITS['string_bytes'], 'RESOURCE_LIMIT', 'Input string byte bound exceeded.')
        elif type(item) is int:
            _need(item.bit_length() <= 256, 'RESOURCE_LIMIT', 'Input integer bound exceeded.')
        else:
            _need(item is None or type(item) is bool, 'SCHEMA', 'Only discrete JSON values are admitted.')


def _keys(value, required, optional=()):
    _need(type(value) is dict and set(required) <= value.keys() <= set(required)|set(optional), 'SCHEMA', 'Missing or unknown fields.')


def _integer(value, low, high, label):
    _need(type(value) is int and low <= value <= high, 'RESOURCE_LIMIT', label + ' is outside its integer bound.')
    return value


def _number(value):
    _need(type(value) in (int, str, Fraction), 'TYPE', 'Coefficients require exact integers or rational strings.')
    if type(value) is str:
        _need(len(value) <= 128 and RATIONAL.fullmatch(value) is not None, 'RATIONAL', 'Malformed exact rational.')
    try: number = Fraction(value)
    except (ValueError, ZeroDivisionError): raise Refusal('RATIONAL', 'Malformed exact rational.') from None
    _need(max(number.numerator.bit_length(), number.denominator.bit_length()) <= LIMITS['rational_bits'], 'RESOURCE_LIMIT', 'Rational bit bound exceeded.')
    return number


def _trim(value):
    value = list(value) or [Fraction(0)]
    while len(value) > 1 and not value[-1]: value.pop()
    return value


def _poly(value):
    _need(type(value) is list and 1 <= len(value) <= 17, 'TYPE', 'A polynomial needs 1..17 ascending coefficients.')
    return _trim([_number(x) for x in value])


def _serial(value):
    return [str(_number(x)) for x in value]


def _add(a, b):
    return _trim([_number((a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0)) for i in range(max(len(a), len(b)))])


def _multiply(a, b):
    result = [Fraction(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b): result[i+j] = _number(result[i+j]+x*y)
    return _trim(result)


def _derivative(a):
    return _trim([_number(i*a[i]) for i in range(1, len(a))])


def _division_reference(a, b):
    """Independent descending coefficient elimination, not the generating law."""
    remainder = list(a); q = [Fraction(0)]*max(1, len(a)-len(b)+1)
    for position in range(len(a)-len(b), -1, -1):
        factor = _number(remainder[position+len(b)-1]/b[-1]); q[position] = factor
        for j in range(len(b)): remainder[position+j] = _number(remainder[position+j]-factor*b[j])
    return _trim(q), _trim(remainder)


def _grammar(node, alphabet, depth=0, counter=None):
    counter = [0] if counter is None else counter; counter[0] += 1
    _need(depth <= LIMITS['ast_depth'] and counter[0] <= LIMITS['ast_nodes'], 'RESOURCE_LIMIT', 'Grammar tree bound exceeded.')
    _need(type(node) is dict and type(node.get('op')) is str, 'GRAMMAR', 'Typed grammar node required.')
    op = node['op']
    if op == 'token':
        _keys(node, ('op', 'token')); _need(node['token'] in alphabet, 'UNKNOWN_TOKEN', 'Token is outside the alphabet.')
        return 1
    if op == 'empty':
        _keys(node, ('op',)); return 0
    if op in ('sequence', 'choice'):
        _keys(node, ('op', 'parts')); parts = node['parts']
        _need(type(parts) is list and 1 <= len(parts) <= 8, 'GRAMMAR', 'Composition needs 1..8 typed parts.')
        lengths = [_grammar(p, alphabet, depth+1, counter) for p in parts]
        length = sum(lengths) if op == 'sequence' else max(lengths)
    elif op == 'repeat':
        _keys(node, ('op', 'body', 'min', 'max'))
        low = _integer(node['min'], 0, 4, 'repeat min'); high = _integer(node['max'], low, 4, 'repeat max')
        length = high*_grammar(node['body'], alphabet, depth+1, counter)
    else: raise Refusal('UNSUPPORTED_GRAMMAR', 'Grammar operation is not registered.')
    _need(length <= LIMITS['word_length'], 'RESOURCE_LIMIT', 'Grammar word-length bound exceeded.')
    return length


def _nfa(grammar):
    edges = []
    def state():
        _need(len(edges) < LIMITS['nfa_states'], 'RESOURCE_LIMIT', 'NFA state bound exceeded.')
        edges.append([]); return len(edges)-1
    def build(node):
        start, end = state(), state(); op = node['op']
        if op in ('token', 'empty'): edges[start].append([node.get('token'), end])
        elif op == 'choice':
            for part in node['parts']:
                a, b = build(part); edges[start].append([None,a]); edges[b].append([None,end])
        else:
            previous = start
            parts = node['parts'] if op == 'sequence' else [node['body']]*node['max']
            if op == 'repeat' and node['min'] == 0: edges[start].append([None,end])
            for i, part in enumerate(parts):
                a, b = build(part); edges[previous].append([None,a]); previous = b
                if op == 'repeat' and i+1 >= node['min']: edges[b].append([None,end])
            edges[previous].append([None,end])
        return start, end
    start, end = build(grammar)
    return edges, start, end


def _dfa(grammar, alphabet):
    edges, first, last = _nfa(grammar); work = 0
    def closure(nodes):
        nonlocal work
        seen, pending = set(nodes), list(nodes)
        while pending:
            for token, target in edges[pending.pop()]:
                work += 1; _need(work <= LIMITS['work_units'], 'RESOURCE_LIMIT', 'Compilation work exhausted.')
                if token is None and target not in seen: seen.add(target); pending.append(target)
        return tuple(sorted(seen))
    start = closure([first]); states = [start]; positions = {start:0}; transitions = []; accepted = []
    for current in states:
        accepted.append(last in current); row = []
        for token in alphabet:
            target = closure([dest for node in current for symbol,dest in edges[node] if symbol == token])
            if target not in positions:
                _need(len(states) < LIMITS['dfa_states'], 'RESOURCE_LIMIT', 'Reachable DFA state bound exceeded.')
                positions[target] = len(states); states.append(target)
            row.append(positions[target]); work += 1
        transitions.append(row)
    return {'schema':'polyia.dfa/0.1','input_type':'Token[]','output_type':'Bool',
            'alphabet':list(alphabet),'start':0,'accepting':accepted,'transitions':transitions}, work, len(edges)


def _minimize(machine):
    rows, accepting = machine['transitions'], machine['accepting']; groups = [int(v) for v in accepting]; rounds = 0
    while True:
        signatures = [(accepting[i], tuple(groups[j] for j in row)) for i,row in enumerate(rows)]
        ids = {}; new = []
        for signature in signatures:
            if signature not in ids: ids[signature] = len(ids)
            new.append(ids[signature])
        rounds += 1
        if all((groups[i] == groups[j]) == (new[i] == new[j]) for i in range(len(rows)) for j in range(len(rows))):
            groups = new; break
        groups = new
    representatives = [groups.index(i) for i in range(max(groups)+1)]
    reduced = dict(machine, start=groups[machine['start']], accepting=[accepting[i] for i in representatives],
                   transitions=[[groups[j] for j in rows[i]] for i in representatives])
    pending = [(machine['start'], reduced['start'])]; seen = set(); counterexample = None
    while pending:
        a,b = pending.pop()
        if (a,b) in seen: continue
        seen.add((a,b))
        if machine['accepting'][a] != reduced['accepting'][b]: counterexample = [a,b]; break
        pending.extend(zip(machine['transitions'][a], reduced['transitions'][b]))
    _need(counterexample is None, 'VERIFICATION_FAILED', 'Minimized machine changes accepted language.')
    return reduced, {'metric':'reachable DFA state count','baseline_states':len(rows),'candidate_states':len(representatives),
                     'improvement':len(rows)-len(representatives),'required_improvement':1,
                     'admitted_as_improvement':len(rows)>len(representatives),'equivalent':True,
                     'product_pairs_checked':len(seen),'refinement_rounds':rounds,
                     'scope':'exact product equivalence of these finite total DFAs; no latency claim'}


def _ast_accepts(grammar, word, meter=None):
    """Independent source interpreter: sets of consumed suffix positions."""
    work = [0]; memo = {}
    def ends(node, start):
        work[0] += 1; _need(work[0] <= LIMITS['work_units'], 'RESOURCE_LIMIT', 'Reference interpretation work exhausted.')
        if meter is not None: meter.charge(1)
        key = (id(node),start)
        if key not in memo: memo[key] = calculate(node,start)
        return memo[key]
    def calculate(node,start):
        op = node['op']
        if op == 'empty': return {start}
        if op == 'token': return {start+1} if start < len(word) and word[start] == node['token'] else set()
        if op == 'choice': return set().union(*(ends(p,start) for p in node['parts']))
        positions = {start}
        if op == 'sequence':
            for child in node['parts']: positions = set().union(*(ends(child,p) for p in positions))
            return positions
        accepted = {start} if node['min'] == 0 else set()
        for i in range(node['max']):
            positions = set().union(*(ends(node['body'],p) for p in positions))
            if i+1 >= node['min']: accepted.update(positions)
        return accepted
    return len(word) in ends(grammar,0)


def _compile(card):
    _guard(card)
    common = {'schema','id','version','family','bounds','seed'}
    _need(type(card) is dict and type(card.get('family')) is str, 'SCHEMA', 'Typed generator card required.')
    family = card['family']
    if family == 'regular': _keys(card, common|{'alphabet','grammar'})
    elif family == 'polynomial-division': _keys(card, common|{'coefficient_choices','divisor','quotient_degree'})
    else: raise Refusal('UNSUPPORTED_FAMILY', 'Only regular and polynomial-division families are registered.')
    _need(card['schema'] == CARD and type(card['id']) is str and NAME.fullmatch(card['id']) is not None
          and type(card['version']) is str and len(card['version']) <= 64 and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',card['version']) is not None,
          'SCHEMA', 'A supported schema and explicit bounded id/version are required.')
    _need(type(card['seed']) is int and card['seed'] == 0, 'RANDOMNESS_UNSUPPORTED', 'This deterministic enumeration profile requires seed zero; no sampling is performed.')
    _keys(card['bounds'], ('work_units','max_candidates'))
    _integer(card['bounds']['work_units'],1,LIMITS['work_units'],'work_units')
    _integer(card['bounds']['max_candidates'],1,LIMITS['candidates'],'max_candidates')
    if family == 'regular':
        alphabet = card['alphabet']
        _need(type(alphabet) is list and 1 <= len(alphabet) <= 8 and all(type(t) is str and 1 <= len(t.encode()) <= 64 for t in alphabet)
              and len(set(alphabet)) == len(alphabet), 'ALPHABET', 'Require 1..8 distinct bounded token identities.')
        max_length = _grammar(card['grammar'], alphabet)
        baseline, work, nfa_size = _dfa(card['grammar'],alphabet); program, optimization = _minimize(baseline)
        construction = {'nfa_states':nfa_size,'subset_work_units':work,'maximum_word_length':max_length}
        output = 'Token[]'; primitive = ['epsilon','token','choice','sequence','bounded-repeat','DFA-transition']
    else:
        divisor = _poly(card['divisor']); _need(divisor != [0] and len(divisor) <= 5, 'DIVISOR', 'Require a nonzero divisor of degree at most four.')
        choices = card['coefficient_choices']; _need(type(choices) is list and 1 <= len(choices) <= 8, 'CHOICES', 'Require 1..8 exact coefficient choices.')
        choices = [_number(x) for x in choices]
        _need(len(set(choices)) == len(choices) and any(choices), 'CHOICES', 'Normalized coefficient choices must be distinct and include a nonzero value.')
        degree = _integer(card['quotient_degree'],0,4,'quotient_degree')
        program = {'schema':'polyia.polynomial-constructor/0.1','input_type':'FiniteCoefficientChoice[]','output_type':'DivisionExercise',
                   'opcodes':['CHOOSE_QUOTIENT','CHOOSE_REMAINDER','CONVOLVE','ADD_REMAINDER','CHECK_DIVISION','CHECK_DERIVATIVES'],
                   'coefficient_choices':_serial(choices),'divisor':_serial(divisor),'quotient_degree':degree}
        optimization = {'metric':'none','admitted_as_improvement':False,'scope':'No polynomial optimization is claimed.'}
        construction = {'finite_derivation_count':len(choices)**(degree+max(0,len(divisor)-1))*sum(bool(c) for c in choices)}
        output = 'DivisionExercise'; primitive = ['exact-rational','polynomial-convolution','addition','Euclidean-division','formal-derivative']
    model = {'schema':PACKAGE,'entity':{'id':card['id'],'version':card['version']},'family':family,'spec':_copy(card),
             'input_type':'GeneratorRequest','output_type':output,'program':program,'construction':construction,'optimization':optimization,
             'state_map':{'states':['INPUT','GENERATE','CONSTRAIN','VERIFY','REPRESENT','COMPLETE','STOPPED','REFUSED'],
                          'tool_calls':[],'effects':[]},
             'randomness':{'algorithm':'none','seed':0,'distribution':'deterministic enumeration; no probability model'},
             'dependencies':{'runtime':VERSION,'standard_library':['fractions','hashlib','itertools','json','re'],'primitives':primitive},
             'source_lock':[{'path':p,'sha256':h,'anchors':a} for p,h,a in SOURCES],
             'learned_parameters':None,'effects':[]}
    model['cid'] = _cid('polyia-generator-package',model)
    return model


def compile_model(card):
    try:
        return {'ok':True,'model':_compile(card)}
    except Refusal as error:
        return {'ok':False,'error':{'code':error.code,'detail':str(error)}}


def _verified_model(model):
    _guard(model)
    _need(type(model) is dict and 'spec' in model, 'PACKAGE', 'A compiled package is required.')
    expected = _compile(model['spec'])
    _need(_json(model) == _json(expected), 'PACKAGE_INTEGRITY', 'Package differs from its reproducible compilation.')
    return expected


def _accepts(machine, word):
    state = machine['start']; path = [state]
    for token in word:
        state = machine['transitions'][state][machine['alphabet'].index(token)]; path.append(state)
    return machine['accepting'][state], path


def _seal_content(kind, value, witness, derivation):
    content = {'schema':'polyia.generated-content/0.1','kind':kind,'value':value,
               'witness':witness,'derivation':derivation,
               'source_lock':[{'path':p,'sha256':h,'anchors':a} for p,h,a in SOURCES]}
    content['id'] = _cid('polyia-generated-content',content)
    return content


class _Meter:
    def __init__(self, limit): self.limit, self.used = limit, 0
    def charge(self, amount):
        _need(self.used + amount <= self.limit, 'RESOURCE_LIMIT', 'Execution operation-credit bound exhausted.')
        self.used += amount


def _regular_content(model, word, meter=None):
    if meter is not None: meter.charge(1+len(word))
    accepted, path = _accepts(model['program'], word)
    reference = _ast_accepts(model['spec']['grammar'], word, meter)
    _need(accepted and reference, 'VERIFICATION_FAILED', 'Generated word failed independent recognition.')
    return _seal_content('regular-word',list(word),
                         {'compiled_accepts':accepted,'reference_accepts':reference},
                         {'grammar':_copy(model['spec']['grammar']),'alphabet':list(model['program']['alphabet']),
                          'machine_path':path,'model_cid':model['cid'],'spec':_copy(model['spec'])})


def _derivative_product_reference(a, b, quotient=False):
    """Coefficient formula independent of composing derivative/multiply helpers."""
    result = [Fraction(0)]*max(1,len(a)+len(b)-2)
    for i in range(len(a)):
        for j in range(len(b)):
            if i+j:
                result[i+j-1] = _number(result[i+j-1] + (i-j if quotient else i+j)*a[i]*b[j])
    return _trim(result)


def _polynomial_content(a, b, q, r):
    aq, ar = _division_reference(a,b)
    product_derivative = _add(_multiply(_derivative(a),b),_multiply(a,_derivative(b)))
    quotient_numerator = _add(_multiply(_derivative(a),b),[-x for x in _multiply(a,_derivative(b))])
    division_matches = aq == q and ar == r and (r == [0] or len(r) < len(b))
    derivatives_match = (product_derivative == _derivative_product_reference(a,b)
                         and quotient_numerator == _derivative_product_reference(a,b,True))
    _need(division_matches and derivatives_match, 'VERIFICATION_FAILED', 'Constructed polynomial failed independent coefficient checks.')
    value = {'dividend':_serial(a),'divisor':_serial(b),'quotient':_serial(q),'remainder':_serial(r),
             'product_derivative':_serial(product_derivative),'quotient_derivative_numerator':_serial(quotient_numerator),
             'quotient_derivative_denominator':_serial(_multiply(b,b)),
             'domain':{'requirement':'b(x) != 0','excluded_by_polynomial':_serial(b)}}
    return _seal_content('polynomial-division',value,
                         {'division_matches':division_matches,'derivative_numerators_match':derivatives_match,
                          'checker':'descending coefficient elimination and direct double-sum coefficient identities'},
                         {'rule':'a=b*q+r','choices':{'quotient':_serial(q),'remainder':_serial(r)}})


def _evaluate(poly, x):
    value = Fraction(0)
    for coefficient in reversed(poly): value = _number(value*x+coefficient)
    return value


def _frontier(model, meter):
    """Yield (candidate or None, elementary cost), never materialize a language."""
    if model['family'] == 'regular':
        machine = model['program']; queue = [([],machine['start'])]; position = 0
        maximum = model['construction']['maximum_word_length']
        while position < len(queue):
            word,state = queue[position]; position += 1
            meter.charge(1)
            candidate = _regular_content(model,word,meter) if machine['accepting'][state] else None
            yield candidate, 1+len(word)
            if len(word) < maximum:
                _need(len(queue)-position+len(machine['alphabet']) <= LIMITS['queue'], 'RESOURCE_LIMIT', 'Frontier queue bound exhausted.')
                queue.extend((word+[token],machine['transitions'][state][i]) for i,token in enumerate(machine['alphabet']))
            if position >= 1024:
                queue = queue[position:]; position = 0
    else:
        choices = [_number(v) for v in model['program']['coefficient_choices']]
        b = _poly(model['program']['divisor']); degree = model['program']['quotient_degree']
        for coefficients in product(choices,repeat=degree+1):
            if not coefficients[-1]:
                meter.charge(1)
                yield None, 1
                continue
            q = list(coefficients)
            for remainder in product(choices,repeat=len(b)-1):
                r = _trim(remainder); length = len(b)+len(q)-1
                meter.charge(8*length*len(b)+8*(length+len(b)+len(q)+len(r))+len(b)**2)
                a = _add(_multiply(b,q),r)
                candidate = _polynomial_content(a,b,q,r)
                # Fixed algebra kernel invocation count; detailed CPU/energy cost is not claimed.
                yield candidate, 1+len(b)*len(q)+len(a)*len(b)*2


def _trace_entry(trace, state, event, data):
    entry = {'index':len(trace),'previous':trace[-1]['digest'] if trace else '0'*64,
             'state':state,'event':event,'data':data}
    entry['digest'] = _cid('polyia-generator-trace',entry); trace.append(entry)


def _report(model, request, status, result, trace, checks):
    _trace_entry(trace,'COMPLETE' if status == 'PASS' else 'STOPPED' if status == 'RESOURCE_LIMIT' else 'REFUSED',
                 'finish',{'status':status,'result_cid':_cid('polyia-generator-result',result)})
    report = {'schema':'polyia.generator-report/0.1','status':status,'engine':VERSION,
              'model_cid':model['cid'],'request':_copy(request),'result':result,'trace':trace,
              'checks':checks,'llm_inference':False,'evidence_class':'bounded-constructive-generator',
              'limitations':list(LIMITATIONS)}
    _need(len(_json(report).encode()) <= LIMITS['output_bytes'], 'RESOURCE_LIMIT', 'Report output byte bound exhausted.')
    return report


def _request(model, request):
    _guard(request); _need(type(request) is dict, 'SCHEMA', 'A typed request is required.')
    operation = request.get('operation'); optional = {'search_budget','paused'}
    if operation == 'generate': _keys(request, ('operation',),optional)
    elif operation == 'recognize':
        _keys(request, ('operation','word'),optional)
        _need(model['family'] == 'regular', 'TYPE', 'Recognition requires the regular family.')
        word = request['word']
        _need(type(word) is list and len(word) <= LIMITS['word_length'] and all(type(x) is str and x in model['program']['alphabet'] for x in word),
              'UNKNOWN_TOKEN', 'A bounded word over the declared alphabet is required.')
    elif operation == 'inverse':
        _need(model['family'] == 'polynomial-division', 'TYPE', 'This inverse profile requires polynomial-division.')
        if 'target' in request:
            _keys(request, ('operation','target'),optional); _poly(request['target'])
        else:
            _keys(request, ('operation','value_at','target_value'),optional)
            _number(request['value_at']); _number(request['target_value'])
    else: raise Refusal('UNSUPPORTED_OPERATION', 'Only generate, recognize and the declared polynomial inverse are registered.')
    if 'paused' in request: _need(type(request['paused']) is bool,'TYPE','paused requires a Boolean.')
    _need(not request.get('paused',False),'PAUSED','Caller requested a paused frontier; no candidates executed.')
    return _integer(request.get('search_budget',model['spec']['bounds']['work_units']),1,
                    model['spec']['bounds']['work_units'],'search_budget')


def _run(model, request):
    model = _verified_model(model); budget = _request(model,request); operation = request['operation']
    trace = []; _trace_entry(trace,'INPUT','admit',{'model_cid':model['cid'],'request_cid':_cid('polyia-generator-request',request)})
    if operation == 'recognize':
        meter = _Meter(budget); meter.charge(len(request['word'])+1)
        accepted,path = _accepts(model['program'],request['word']); reference = _ast_accepts(model['spec']['grammar'],request['word'],meter)
        _need(accepted == reference, 'VERIFICATION_FAILED', 'DFA and source interpretation disagree.')
        result = {'accepted':accepted,'reference_accepted':reference,'machine_path':path,'complete':True,
                  'work_units':len(path),'operation_credits':meter.used,'operation_credit_limit':meter.limit,
                  'work_unit_definition':'DFA start/token visits; operation credits additionally count reference AST visits'}
        _trace_entry(trace,'VERIFY','recognize',{'accepted':accepted,'word':_copy(request['word'])})
        return _report(model,request,'PASS',result,trace,[{'name':'independent source recognition','passed':True}])
    _trace_entry(trace,'GENERATE','begin_frontier',{'family':model['family'],'search_budget':budget,'tool_calls':[]})
    counts = {'generated':0,'duplicate':0,'refused':0,'tested':0,'admitted':0,'frontier_visits':0}
    candidates = []; seen = set(); work = 0; complete = True; stop = None
    meter = _Meter(model['spec']['bounds']['work_units'])
    if model['family'] == 'regular':
        domain_visits = sum(len(model['program']['alphabet'])**i for i in range(model['construction']['maximum_word_length']+1))
    else:
        program = model['program']; n = len(program['coefficient_choices']); degree = program['quotient_degree']
        zeros = sum(_number(x) == 0 for x in program['coefficient_choices'])
        domain_visits = model['construction']['finite_derivation_count'] + zeros*n**degree
    frontier = _frontier(model,meter)
    while counts['frontier_visits'] < domain_visits:
        if counts['frontier_visits'] >= budget:
            complete = False; stop = 'SEARCH_BUDGET'; break
        if counts['admitted'] >= model['spec']['bounds']['max_candidates']:
            complete = False; stop = 'CANDIDATE_LIMIT'; break
        try:
            candidate,cost = next(frontier)
        except Refusal as error:
            if error.code != 'RESOURCE_LIMIT': raise
            complete = False; stop = 'OPERATION_OR_REPRESENTATION_BOUND'; break
        counts['frontier_visits'] += 1; work += cost
        if candidate is None:
            counts['refused'] += 1; continue
        counts['generated'] += 1; counts['tested'] += 1
        if candidate['id'] in seen: counts['duplicate'] += 1; continue
        seen.add(candidate['id'])
        matches = True
        if operation == 'inverse':
            a = _poly(candidate['value']['dividend'])
            matches = a == _poly(request['target']) if 'target' in request else _evaluate(a,_number(request['value_at'])) == _number(request['target_value'])
        if not matches: counts['refused'] += 1; continue
        candidates.append(candidate); counts['admitted'] += 1
        binding = {'content_id':candidate['id'],'frontier_visit':counts['frontier_visits']}
        _trace_entry(trace,'GENERATE','construct_candidate',binding.copy())
        _trace_entry(trace,'CONSTRAIN','constraints_passed',binding.copy())
        _trace_entry(trace,'VERIFY','admit_candidate',binding.copy())
    result = {'candidates':candidates,'counts':counts,'complete':complete,'stop_reason':stop,'work_units':work,
              'operation_credits':meter.used,'operation_credit_limit':meter.limit,
              'domain_frontier_visits':domain_visits,
              'budget_unit':'bounded constructor/checker invocation or visited regular-word prefix',
              'cost_unit':'state/token visits for regular; fixed rational-operation estimate for polynomial; excludes compiler and JSON transport',
              'operation_credit_definition':'one regular prefix, DFA token/start or memoized AST visit; polynomial conservative reservation 8*len(a)*len(b)+8*(len(a)+len(b)+len(q)+len(r))+len(b)^2' }
    if operation == 'inverse':
        result.update(matching_count=len(candidates),classification=(
            'UNRESOLVED_SEARCH_BUDGET' if not complete else 'NO_PREIMAGE_IN_DECLARED_DOMAIN' if not candidates
            else 'UNIQUE_IN_DECLARED_DOMAIN' if len(candidates) == 1 else 'MULTIPLE_IN_DECLARED_DOMAIN'))
    return _report(model,request,'PASS' if complete else 'RESOURCE_LIMIT',result,trace,
                   [{'name':'each admitted candidate independently checked','passed':True},
                    {'name':'declared finite domain exhausted','passed':complete}])


def run_model(model, request):
    """Execute only a reproducibly compiled registered package and typed request."""
    try:
        return _run(model,request)
    except Refusal as error:
        return {'schema':'polyia.generator-report/0.1','status':'RESOURCE_LIMIT' if error.code == 'RESOURCE_LIMIT' else 'REFUSED',
                'engine':VERSION,'result':{'reason':error.code,'detail':str(error),'complete':False},
                'checks':[],'trace':[],'llm_inference':False,'evidence_class':'bounded-constructive-generator',
                'limitations':list(LIMITATIONS)}


def replay_trace(report):
    """Validate captured hash-chain and result bindings; never rerun a generator.

    This detects corruption, not a malicious author who fabricates a whole receipt.
    Authentic capture requires the ledger's immutable run/code/source bindings.
    """
    try:
        _guard(report)
        _keys(report, ('schema','status','engine','model_cid','request','result','trace','checks','llm_inference','evidence_class','limitations'))
        _need(report['schema'] == 'polyia.generator-report/0.1' and report['engine'] == VERSION and report['llm_inference'] is False,
              'TRACE','Unsupported report identity.')
        trace = report['trace']; _need(type(trace) is list and 2 <= len(trace) <= 3*LIMITS['candidates']+3,'TRACE','Bounded complete receipt required.')
        previous = '0'*64
        for i,entry in enumerate(trace):
            _keys(entry,('index','previous','state','event','data','digest'))
            payload = {k:v for k,v in entry.items() if k != 'digest'}
            _need(type(entry['index']) is int and entry['index'] == i and entry['previous'] == previous
                  and entry['digest'] == _cid('polyia-generator-trace',payload),'TRACE','Trace chain mismatch.')
            previous = entry['digest']
        _need(trace[0]['state'] == 'INPUT' and trace[0]['event'] == 'admit'
              and trace[0]['data'] == {'model_cid':report['model_cid'],'request_cid':_cid('polyia-generator-request',report['request'])},'TRACE','Input binding mismatch.')
        expected_state = 'COMPLETE' if report['status'] == 'PASS' else 'STOPPED' if report['status'] == 'RESOURCE_LIMIT' else 'REFUSED'
        _need(trace[-1]['state'] == expected_state and trace[-1]['event'] == 'finish'
              and trace[-1]['data'] == {'status':report['status'],'result_cid':_cid('polyia-generator-result',report['result'])},'TRACE','Result binding mismatch.')
        if report['request']['operation'] in ('generate','inverse'):
            contents = report['result']['candidates']; counts = report['result']['counts']
            _need(trace[1]['state'] == 'GENERATE' and trace[1]['event'] == 'begin_frontier'
                  and trace[1]['data']['tool_calls'] == [],'TRACE','Frontier admission mismatch.')
            phases = trace[2:-1]
            _need(len(contents) == counts['admitted'] and len(phases) == 3*len(contents),'TRACE','Candidate count mismatch.')
            for index,content in enumerate(contents):
                group = phases[index*3:index*3+3]
                _need([(e['state'],e['event']) for e in group] == [('GENERATE','construct_candidate'),('CONSTRAIN','constraints_passed'),('VERIFY','admit_candidate')]
                      and group[0]['data'] == group[1]['data'] == group[2]['data']
                      and group[0]['data']['content_id'] == content['id'],'TRACE','Candidate phase binding mismatch.')
            for content in contents:
                _need(content['id'] == _cid('polyia-generated-content',{k:v for k,v in content.items() if k != 'id'}),'TRACE','Content identity mismatch.')
        else:
            _need(len(trace) == 3 and trace[1]['event'] == 'recognize' and trace[1]['state'] == 'VERIFY'
                  and trace[1]['data'] == {'accepted':report['result']['accepted'],'word':report['request']['word']},'TRACE','Recognition binding mismatch.')
        return {'ok':True,'entries':len(trace),'result_cid':trace[-1]['data']['result_cid'],
                'scope':'captured trace integrity only; no execution or provenance authentication'}
    except (Refusal,KeyError,TypeError) as error:
        return {'ok':False,'error':{'code':'TRACE','detail':str(error)}}


def _checked_content(content):
    _guard(content)
    _keys(content,('schema','kind','value','witness','derivation','source_lock','id'))
    _need(content['schema'] == 'polyia.generated-content/0.1' and content['id'] == _cid('polyia-generated-content',{k:v for k,v in content.items() if k != 'id'}),
          'CONTENT_INTEGRITY','Content identity mismatch.')
    if content['kind'] == 'polynomial-division':
        value = content['value']; _need(type(value) is dict,'TYPE','Polynomial content required.')
        _need(all(k in value for k in ('dividend','divisor','quotient','remainder')),'TYPE','Missing polynomial fields.')
        a,b,q,r = [_poly(value[k]) for k in ('dividend','divisor','quotient','remainder')]
        _need(b != [0],'DIVISOR','Nonzero polynomial required.')
        expected = _polynomial_content(a,b,q,r)
        _need(_json(content) == _json(expected),'CONTENT_INTEGRITY','Content differs from independently checked reconstruction.')
    elif content['kind'] == 'regular-word':
        d = content['derivation']; _keys(d,('grammar','alphabet','machine_path','model_cid','spec'))
        model = _compile(d['spec']); _need(model['family'] == 'regular','TYPE','A regular source model is required.')
        word = content['value']
        _need(type(word) is list and len(word) <= LIMITS['word_length'] and all(type(x) is str and x in model['program']['alphabet'] for x in word),'TYPE','Bounded token word required.')
        _need(_json(content) == _json(_regular_content(model,word)),'CONTENT_INTEGRITY','Content differs from independently checked source reconstruction.')
    else: raise Refusal('UNSUPPORTED_CONTENT','No renderer for this content type.')
    return content


def render_explanation(content, options):
    """Fixed style variants render only independently checked semantic facts."""
    try:
        _guard(options); _keys(options,('style',)); _need(options['style'] in ('concise','tutorial'),'STYLE','Unsupported rendering style.')
        content = _checked_content(content); value = content['value']; tutorial = options['style'] == 'tutorial'
        if content['kind'] == 'polynomial-division':
            relations = {'division':'a=b*q+r','a':value['dividend'],'b':value['divisor'],'q':value['quotient'],'r':value['remainder'],
                         'product_derivative':value['product_derivative'],'quotient_derivative_numerator':value['quotient_derivative_numerator'],
                         'quotient_derivative_denominator':value['quotient_derivative_denominator'],'domain':value['domain']}
            text = ('Coefficients are exact rationals in ascending powers. ' if tutorial else '')
            text += 'Division: a = b*q + r; a='+str(value['dividend'])+', b='+str(value['divisor'])+', q='+str(value['quotient'])+', r='+str(value['remainder'])+'. '
            if tutorial: text += 'First use fraction arithmetic; then eliminate descending coefficients for division. The product rule is (a*b)\' = a\'*b+a*b\'. '
            text += 'Product derivative coefficients: '+str(value['product_derivative'])+'. Quotient derivative: '+str(value['quotient_derivative_numerator'])+' / '+str(value['quotient_derivative_denominator'])+'. Domain: b(x) != 0.'
        else:
            relations = {'word':value,'grammar':content['derivation']['grammar'],'accepted':True}
            text = ('Follow the typed grammar from input through sequence, choice and bounded repetition. ' if tutorial else '')
            text += 'Accepted token sequence: '+_json(value)+'. The source interpreter accepts this sequence.'
        view = {'schema':'polyia.generator-view/0.1','content_id':content['id'],'style':options['style'],'relations':relations,'text':text,
                'source_lock':_copy(content['source_lock']),
                'state_trace':[{'state':'INPUT','content_id':content['id']},{'state':'VERIFY','independent_check':True},
                               {'state':'REPRESENT','style':options['style'],'tool_calls':[]}]} 
        view['view_id'] = _cid('polyia-generator-view',view)
        return {'ok':True,'view':view}
    except Refusal as error:
        return {'ok':False,'error':{'code':error.code,'detail':str(error)}}


def build_curriculum(content):
    """Construct a prerequisite graph whose worked facts are exact operations."""
    try:
        content = _checked_content(content)
        _need(content['kind'] == 'polynomial-division','UNSUPPORTED_CONTENT','This curriculum requires a division exercise.')
        value = content['value']; b,q,r = [_poly(value[k]) for k in ('divisor','quotient','remainder')]
        fraction_result = _number(b[0]*q[0]+r[0])
        steps = [
            {'id':'fractions','requires':[],'operation':'multiply then add exact rationals',
             'operands':[str(b[0]),str(q[0]),str(r[0])],'result':str(fraction_result),
             'claim':'constant coefficient b[0]*q[0]+r[0] equals a[0]'},
            {'id':'division','requires':['fractions'],'operation':'descending coefficient elimination',
             'dividend':value['dividend'],'divisor':value['divisor'],
             'quotient':value['quotient'],'remainder':value['remainder']},
            {'id':'product-derivative','requires':['division'],'operation':'(a*b)\' = a\'*b+a*b\'',
             'result':value['product_derivative']},
            {'id':'quotient-derivative','requires':['division','product-derivative'],
             'operation':'(a/b)\' = (a\'*b-a*b\')/(b*b)',
             'numerator':value['quotient_derivative_numerator'],'denominator':value['quotient_derivative_denominator'],
             'domain':value['domain']},
        ]
        for step in steps: step.update(source_refs=[0,1,5],evidence_class='exact-rational-coefficient-check')
        curriculum = {'schema':'polyia.curriculum/0.1','content_id':content['id'],'steps':steps,
                      'source_lock':_copy(content['source_lock']),
                      'assumptions':['Q[x], ascending exact rational coefficients','r=0 or degree(r)<degree(b)','quotient differentiation requires b(x) != 0'],
                      'scope':'four exact worked steps, not a complete pedagogy or learner assessment'}
        curriculum['id'] = _cid('polyia-generator-curriculum',curriculum)
        return {'ok':True,'curriculum':curriculum}
    except Refusal as error:
        return {'ok':False,'error':{'code':error.code,'detail':str(error)}}


def export_native(content):
    """Emit source for the existing fixed .polyia polynomial VM profile."""
    try:
        content = _checked_content(content)
        _need(content['kind'] == 'polynomial-division','UNSUPPORTED_CONTENT','Only polynomial content has a native backend here.')
        value = content['value']
        source = '(commission\n  (profile "polyia.native/0.1")\n  (budget 128)\n'
        source += '  (let a Polynomial (poly '+' '.join(value['dividend'])+'))\n'
        source += '  (let b Polynomial (poly '+' '.join(value['divisor'])+'))\n'
        source += '  (let d Division (divmod a b))\n'
        source += '  (emit quotient (quotient d))\n  (emit remainder (remainder d))\n'
        source += '  (emit product_derivative (derivative (pmul a b)))\n'
        source += '  (emit quotient_numerator (padd (pmul (derivative a) b) (pmul (poly -1) (pmul a (derivative b)))))\n)\n'
        return {'ok':True,'content_id':content['id'],'source':source,
                'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                'requires':'polyia.native/0.1; separately compile and execute this emitted source'}
    except Refusal as error:
        return {'ok':False,'error':{'code':error.code,'detail':str(error)}}


def _parse_json(raw):
    def reject_constant(value): raise Refusal('JSON','Nonfinite JSON constants are forbidden.')
    def unique_object(pairs):
        result = {}
        for key,value in pairs:
            _need(key not in result,'JSON','Duplicate JSON object fields are forbidden.')
            result[key] = value
        return result
    return json.loads(raw,parse_constant=reject_constant,object_pairs_hook=unique_object)


def _main():
    import sys
    try:
        _need(len(sys.argv) == 2 and sys.argv[1] in ('compile','run','view','replay'),'OPERATION','Use compile, run, view or replay with a JSON document on stdin.')
        raw = sys.stdin.buffer.read(LIMITS['output_bytes']+1)
        _need(len(raw) <= LIMITS['output_bytes'],'RESOURCE_LIMIT','Input transport byte bound exceeded.')
        value = _parse_json(raw.decode('utf-8'))
        operation = sys.argv[1]
        if operation == 'compile': result = compile_model(value)
        elif operation == 'replay': result = replay_trace(value)
        elif operation == 'run':
            _keys(value,('model','request')); result = run_model(value['model'],value['request'])
        else:
            _keys(value,('content','options')); result = render_explanation(value['content'],value['options'])
    except (Refusal,UnicodeError,ValueError,RecursionError) as error:
        result = {'ok':False,'error':{'code':'INPUT','detail':str(error)}}
    sys.stdout.write(_json(result)+'\n')
    return 0 if result.get('ok',result.get('status') == 'PASS') else 2


if __name__ == '__main__':
    raise SystemExit(_main())
