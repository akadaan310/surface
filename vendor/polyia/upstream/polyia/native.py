"""Versioned pure .polyia compiler and bounded stack VM; no external effects.

This is a finite compiler increment, not the complete D-COMPILER contract.
The AST reference evaluator is separately implemented, but shares Fraction and
front-end validation: agreement is differential evidence, not a formal proof.
"""
from fractions import Fraction
import hashlib
import json
import re

VERSION = 'polyia.native/0.1'
LIMITS = {'source_bytes': 65536, 'tokens': 4096, 'depth': 48,
          'statements': 128, 'instructions': 2048, 'rational_bits': 512,
          'polynomial_degree': 64, 'text_bytes': 16384,
          'output_bytes': 65536, 'work_units': 200000}
SIGNATURES = {
    'add': (['Rational', 'Rational'], 'Rational'),
    'sub': (['Rational', 'Rational'], 'Rational'),
    'mul': (['Rational', 'Rational'], 'Rational'),
    'padd': (['Polynomial', 'Polynomial'], 'Polynomial'),
    'pmul': (['Polynomial', 'Polynomial'], 'Polynomial'),
    'divmod': (['Polynomial', 'Polynomial'], 'Division'),
    'quotient': (['Division'], 'Polynomial'),
    'remainder': (['Division'], 'Polynomial'),
    'derivative': (['Polynomial'], 'Polynomial'),
    'evaluate': (['Polynomial', 'Rational'], 'Rational'),
    'concat': (['Text', 'Text'], 'Text'),
    'replace': (['Text', 'Text', 'Text'], 'Text'),
}
SOURCES = [
    {'source_id': 'SRC-POLYIA96', 'path': 'sources/recovered/CODEX_CONSTITUTION.md',
     'anchors': ['C-017', 'C-018', 'C-019', 'C-021', 'C-022', 'C-023', 'C-057', 'C-058', 'C-064'],
     'sha256': 'cfe0b88f9c701e139372d783db1d9568da272f6433f9e513d6475fe7985a2630'},
    {'source_id': 'SRC-UCG156', 'path': 'sources/originals/UCG_CODEX_CONSTITUTIONAL_COMMISSION.md',
     'anchors': ['084', '124', '132'],
     'sha256': '0cf03197777e19330ce36cf478bec9a5c4cad5459fd142c37eb4ae0e82bd6d7e'},
]
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_.-]*\Z', re.ASCII)
NUMBER = re.compile(r'-?[0-9]+(?:/[0-9]+)?\Z', re.ASCII)


class Refusal(Exception):
    def __init__(self, code, message, span=None):
        self.error = {'code': code, 'message': message}
        if span is not None:
            self.error['span'] = span
        super().__init__(message)


def _refuse(code, message, span=None):
    raise Refusal(code, message, span)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _digest(value):
    return hashlib.sha256(('polyia-native-package\0' + _canonical(value)).encode()).hexdigest()


def _rational(value, span=None):
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > LIMITS['rational_bits']:
        _refuse('ARITHMETIC_BUDGET', 'Exact rational exceeds its bit bound.', span)
    return value


def _poly(values, span=None):
    result = list(values)
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    if len(result) > LIMITS['polynomial_degree'] + 1:
        _refuse('POLYNOMIAL_BUDGET', 'Polynomial degree exceeds the supported bound.', span)
    return [_rational(v, span) for v in result]


def _text(value, span=None):
    if len(value.encode()) > LIMITS['text_bytes']:
        _refuse('TEXT_BUDGET', 'Text exceeds its UTF-8 byte bound.', span)
    return value


def _lex(source):
    # Prefix positions ensure precise UTF-8 offsets without quadratic rescans.
    positions, byte, line, column = [], 0, 1, 1
    for char in source:
        positions.append((byte, line, column))
        byte += len(char.encode())
        if char == '\n': line, column = line + 1, 1
        else: column += 1
    positions.append((byte, line, column))

    def span(start, end):
        return {'start': start, 'end': end, 'byte_start': positions[start][0],
                'byte_end': positions[end][0], 'line': positions[start][1],
                'column': positions[start][2]}

    tokens, index = [], 0
    while index < len(source):
        char = source[index]
        if char in ' \t\r\n': index += 1; continue
        if char == ';':
            end = source.find('\n', index)
            index = len(source) if end < 0 else end
            continue
        start = index
        if char in '()':
            index += 1
            kind, value = char, char
        elif char == '"':
            index += 1
            value = ''
            while index < len(source) and source[index] != '"':
                current = source[index]
                if current == '\\':
                    index += 1
                    if index >= len(source) or source[index] not in '\\"n':
                        _refuse('LEXICAL', 'Only quote, slash and newline escapes are supported.', span(start, index))
                    current = {'\\': '\\', '"': '"', 'n': '\n'}[source[index]]
                elif ord(current) < 32:
                    _refuse('LEXICAL', 'Control characters in strings must use supported escapes.', span(start, index+1))
                value += current
                index += 1
            if index == len(source):
                _refuse('LEXICAL', 'Unterminated string.', span(start, index))
            index += 1
            kind = 'string'
            _text(value, span(start, index))
        else:
            while index < len(source) and source[index] not in '() \t\r\n;"':
                index += 1
            value = source[start:index]
            if NUMBER.fullmatch(value): kind = 'number'
            elif NAME.fullmatch(value): kind = 'name'
            else: _refuse('LEXICAL', 'Unsupported token.', span(start, index))
        tokens.append({'kind': kind, 'value': value, 'span': span(start, index)})
        if len(tokens) > LIMITS['tokens']:
            _refuse('TOKEN_BUDGET', 'Too many source tokens.', span(start, index))
    return tokens


def _parse(tokens):
    index = 0

    def item(depth):
        nonlocal index
        if depth > LIMITS['depth']:
            _refuse('DEPTH_BUDGET', 'Expression nesting exceeds the supported bound.')
        if index >= len(tokens): _refuse('SYNTAX', 'Expected source form.')
        token = tokens[index]
        index += 1
        if token['kind'] == ')': _refuse('SYNTAX', 'Unexpected closing parenthesis.', token['span'])
        if token['kind'] != '(': return token
        children = []
        while index < len(tokens) and tokens[index]['kind'] != ')':
            children.append(item(depth+1))
        if index == len(tokens): _refuse('SYNTAX', 'Unclosed source form.', token['span'])
        end = tokens[index]['span']
        index += 1
        span = dict(token['span'], end=end['end'], byte_end=end['byte_end'])
        return {'kind': 'form', 'children': children, 'span': span}

    root = item(0)
    if index != len(tokens): _refuse('SYNTAX', 'Only one commission is allowed.', tokens[index]['span'])
    return root


def _head(node):
    if node['kind'] != 'form' or not node['children'] or node['children'][0]['kind'] != 'name':
        _refuse('SYNTAX', 'Expected a named parenthesized form.', node['span'])
    return node['children'][0]['value'], node['children'][1:]


def _name(node):
    if node['kind'] != 'name': _refuse('SYNTAX', 'Expected an identifier.', node['span'])
    return node['value']


def _literal(node):
    raw = node['value']
    # Decimal length is checked before integer construction.
    if any(len(part.lstrip('-')) > 155 for part in raw.split('/')):
        _refuse('ARITHMETIC_BUDGET', 'Rational literal exceeds its digit bound.', node['span'])
    if '/' in raw and int(raw.split('/')[1]) == 0:
        _refuse('ZERO_DENOMINATOR', 'A rational denominator must be nonzero.', node['span'])
    return str(_rational(Fraction(raw), node['span']))


def _typed_expression(node, symbols):
    span = node['span']
    if node['kind'] == 'number':
        out = {'kind': 'literal', 'type': 'Rational', 'value': _literal(node), 'span': span}
    elif node['kind'] == 'string':
        out = {'kind': 'literal', 'type': 'Text', 'value': node['value'], 'span': span}
    elif node['kind'] == 'name':
        if node['value'] not in symbols: _refuse('UNBOUND_NAME', 'Name has no earlier binding.', span)
        out = {'kind': 'reference', 'type': symbols[node['value']], 'name': node['value'], 'span': span}
    else:
        operation, values = _head(node)
        if operation == 'poly':
            if not values: _refuse('ARITY', 'A polynomial requires at least one coefficient.', span)
            if len(values) > LIMITS['polynomial_degree']+1:
                _refuse('POLYNOMIAL_BUDGET', 'Too many polynomial coefficients.', span)
            expected, result_type = ['Rational'] * len(values), 'Polynomial'
        elif operation in SIGNATURES:
            expected, result_type = SIGNATURES[operation]
        else: _refuse('UNKNOWN_OPERATION', 'Operation is not admitted by this pure profile.', span)
        if len(values) != len(expected): _refuse('ARITY', 'Incorrect number of operation arguments.', span)
        children = [_typed_expression(value, symbols) for value in values]
        if [child['type'] for child in children] != expected:
            _refuse('TYPE_ERROR', 'Argument types do not match the operation signature.', span)
        out = {'kind': 'call', 'operation': operation, 'type': result_type, 'arguments': children, 'span': span}
    return out


def _compile(source):
    if type(source) is not str: _refuse('SOURCE_TYPE', 'Source must be a string.')
    try: raw = source.encode('utf-8')
    except UnicodeEncodeError: _refuse('INVALID_UNICODE', 'Source must contain Unicode scalar values.')
    if len(raw) > LIMITS['source_bytes']: _refuse('SOURCE_BUDGET', 'Source exceeds its UTF-8 byte bound.')
    root = _parse(_lex(source))
    name, statements = _head(root)
    if name != 'commission': _refuse('SYNTAX', 'The root form must be commission.', root['span'])
    if not statements: _refuse('PROFILE', 'An explicit language profile is required.', root['span'])
    profile, args = _head(statements[0])
    if profile != 'profile' or len(args) != 1 or args[0]['kind'] != 'string' or args[0]['value'] != VERSION:
        _refuse('PROFILE', 'Expected the supported explicit native profile.', statements[0]['span'])
    if len(statements) > LIMITS['statements'] + 2:
        _refuse('STATEMENT_BUDGET', 'Too many statements.', root['span'])
    symbols, outputs, ast, instructions = {}, {}, [], []
    budget, budget_seen, body_seen = LIMITS['instructions'], False, False

    def lower(node):
        common = {'type': node['type'], 'span': node['span'], 'effects': []}
        if node['kind'] == 'literal': instructions.append(dict(common, op='CONST', value=node['value']))
        elif node['kind'] == 'reference': instructions.append(dict(common, op='LOAD', name=node['name']))
        else:
            for child in node['arguments']: lower(child)
            instructions.append(dict(common, op='CALL', operation=node['operation'], arity=len(node['arguments'])))

    for statement in statements[1:]:
        kind, args = _head(statement)
        span = statement['span']
        if kind == 'budget':
            if budget_seen or body_seen or len(args) != 1 or args[0]['kind'] != 'number' or '/' in args[0]['value']:
                _refuse('BUDGET_DECLARATION', 'One integer budget is allowed before executable statements.', span)
            if len(args[0]['value']) > 5: _refuse('INSTRUCTION_BUDGET', 'Invalid instruction budget.', span)
            budget = int(args[0]['value'])
            if not 1 <= budget <= LIMITS['instructions']:
                _refuse('INSTRUCTION_BUDGET', 'Budget must be within the runtime ceiling.', span)
            budget_seen = True
            continue
        body_seen = True
        if kind not in ('let', 'emit'): _refuse('UNKNOWN_STATEMENT', 'Statement is not admitted.', span)
        if len(args) != (3 if kind == 'let' else 2): _refuse('ARITY', 'Incorrect statement arity.', span)
        identifier = _name(args[0])
        if kind == 'let':
            if identifier in symbols: _refuse('DUPLICATE_NAME', 'Bindings cannot be redefined.', span)
            declared = _name(args[1])
            if declared not in ('Rational', 'Polynomial', 'Text', 'Division'): _refuse('UNKNOWN_TYPE', 'Unsupported type.', args[1]['span'])
        elif identifier in outputs: _refuse('DUPLICATE_OUTPUT', 'Output names must be unique.', span)
        value = _typed_expression(args[-1], symbols)
        if kind == 'let' and declared != value['type']: _refuse('TYPE_ERROR', 'Declared type does not match expression.', span)
        ast.append({'kind': kind, 'name': identifier, 'type': value['type'], 'expression': value, 'span': span})
        if len(ast) > LIMITS['statements']:
            _refuse('STATEMENT_BUDGET', 'Too many executable statements.', span)
        lower(value)
        instructions.append({'op': 'STORE' if kind == 'let' else 'EMIT', 'name': identifier,
                             'type': value['type'], 'span': span, 'effects': []})
        if kind == 'let': symbols[identifier] = value['type']
        else: outputs[identifier] = value['type']
    if not outputs: _refuse('NO_OUTPUT', 'A commission must emit at least one value.', root['span'])
    if len(instructions) > budget: _refuse('INSTRUCTION_BUDGET', 'Lowering exceeds the declared instruction budget.', root['span'])
    program = {'version': VERSION, 'format': 'polyia.typed-stack/0.1', 'source': source,
               'source_sha256': hashlib.sha256(raw).hexdigest(), 'source_refs': SOURCES,
               'ast': ast, 'instructions': instructions, 'effects': [], 'inputs': {}, 'outputs': outputs,
               'context': {'polynomial_ring': 'Q[x]', 'text_semantics': 'exact Unicode scalar sequence'},
               'assumptions': ['no external effects', 'acyclic immutable bindings', 'bounded exact arithmetic'],
               'dependencies': ['Python standard library: fractions, hashlib, json, re'],
               'limits': dict(LIMITS, instructions=budget),
               'cost': {'bytecode_instructions': len(instructions), 'arithmetic_work': 'charged at execution'},
               'proof_obligations': ['typed lowering', 'bounded execution', 'VM/reference observable agreement'],
               'scope': 'bounded compiler increment; full D-COMPILER acceptance remains open'}
    # Do not expose references to mutable module-level policy objects.
    program = json.loads(_canonical(program))
    program['package_sha256'] = _digest(program)
    return program


def compile_program(source: str) -> dict:
    """Compile native source; return {ok, program} or a structured refusal."""
    try: return {'ok': True, 'program': _compile(source)}
    except Refusal as exc: return {'ok': False, 'error': exc.error}


class Meter:
    def __init__(self): self.work = 0
    def charge(self, units, span):
        self.work += units
        if self.work > LIMITS['work_units']: _refuse('WORK_BUDGET', 'Execution work budget exhausted.', span)


def _vm_call(operation, args, meter, span):
    meter.charge(1, span)
    if operation in ('add', 'sub', 'mul'):
        a, b = args
        return _rational(a+b if operation == 'add' else a-b if operation == 'sub' else a*b, span)
    if operation == 'poly': return _poly(args, span)
    if operation == 'padd':
        a, b = args
        meter.charge(max(len(a), len(b)), span)
        return _poly([(a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0)
                      for i in range(max(len(a), len(b)))], span)
    if operation == 'pmul':
        a, b = args
        if len(a)+len(b)-2 > LIMITS['polynomial_degree']:
            _refuse('POLYNOMIAL_BUDGET', 'Product degree exceeds its bound.', span)
        meter.charge(len(a)*len(b), span)
        result = [Fraction(0)] * (len(a)+len(b)-1)
        for i, left in enumerate(a):
            for j, right in enumerate(b):
                result[i+j] = _rational(result[i+j] + _rational(left*right, span), span)
        return _poly(result, span)
    if operation == 'derivative':
        meter.charge(len(args[0]), span)
        return _poly([i*value for i, value in enumerate(args[0]) if i] or [Fraction(0)], span)
    if operation == 'divmod':
        dividend, divisor = args
        if divisor == [0]: _refuse('ZERO_POLYNOMIAL', 'Polynomial divisor must be nonzero.', span)
        remainder = list(dividend)
        quotient = [Fraction(0)] * max(1, len(dividend)-len(divisor)+1)
        while remainder != [0] and len(remainder) >= len(divisor):
            shift = len(remainder)-len(divisor)
            factor = _rational(remainder[-1]/divisor[-1], span)
            quotient[shift] = factor
            meter.charge(len(divisor), span)
            for i, coefficient in enumerate(divisor):
                remainder[i+shift] = _rational(remainder[i+shift]-_rational(factor*coefficient, span), span)
            remainder = _poly(remainder, span)
        return {'quotient': _poly(quotient, span), 'remainder': remainder}
    if operation in ('quotient', 'remainder'): return args[0][operation]
    if operation == 'evaluate':
        coefficients, x = args
        meter.charge(len(coefficients), span)
        result = Fraction(0)
        for coefficient in reversed(coefficients):
            result = _rational(_rational(result*x, span)+coefficient, span)
        return result
    if operation == 'concat':
        meter.charge(len(args[0])+len(args[1]), span)
        if len(args[0].encode())+len(args[1].encode()) > LIMITS['text_bytes']:
            _refuse('TEXT_BUDGET', 'Concatenation exceeds text byte bound.', span)
        return args[0]+args[1]
    if operation == 'replace':
        text, old, new = args
        if not old: _refuse('EMPTY_PATTERN', 'Replacement pattern must be nonempty.', span)
        meter.charge(len(text)+len(old)+len(new), span)
        count = text.count(old)
        size = len(text.encode()) + count*(len(new.encode())-len(old.encode()))
        if size > LIMITS['text_bytes']: _refuse('TEXT_BUDGET', 'Replacement exceeds text byte bound.', span)
        return text.replace(old, new)
    _refuse('UNKNOWN_OPERATION', 'Bytecode operation is not registered.', span)


def _encode_value(kind, value):
    if kind == 'Division':
        return {'type': kind, 'value': {name: [str(v) for v in coefficients]
                                     for name, coefficients in value.items()}}
    return {'type': kind, 'value': [str(v) for v in value] if kind == 'Polynomial'
            else str(value) if kind == 'Rational' else value}


def _vm(program):
    stack, bindings, outputs, meter = [], {}, {}, Meter()
    for instruction in program['instructions']:
        op, span = instruction['op'], instruction['span']
        meter.charge(1, span)
        if op == 'CONST':
            stack.append(Fraction(instruction['value']) if instruction['type'] == 'Rational' else instruction['value'])
        elif op == 'LOAD': stack.append(bindings[instruction['name']])
        elif op == 'CALL':
            count = instruction['arity']
            args = stack[-count:]
            del stack[-count:]
            stack.append(_vm_call(instruction['operation'], args, meter, span))
        elif op == 'STORE': bindings[instruction['name']] = stack.pop()
        elif op == 'EMIT':
            outputs[instruction['name']] = _encode_value(instruction['type'], stack.pop())
            if len(_canonical(outputs).encode()) > LIMITS['output_bytes']:
                _refuse('OUTPUT_BUDGET', 'Combined outputs exceed their byte bound.', span)
        else: _refuse('UNKNOWN_OPCODE', 'Bytecode instruction is not registered.', span)
    return outputs, meter.work


def _reference(program):
    """Independent AST traversal/operation implementation (shared rational type).

Polynomial product uses coefficient diagonals, evaluation uses explicit powers,
text replacement uses split/join. This does not invoke the VM operation handler.
The admitted AST is already bounded, and this evaluator runs only after the VM
has completed within limits, so all inputs have passed those resource guards.
"""
    bindings, outputs = {}, {}

    def normalize(coefficients):
        while len(coefficients) > 1 and coefficients[-1] == 0: coefficients.pop()
        return coefficients

    def evaluate(node):
        if node['kind'] == 'literal':
            return Fraction(node['value']) if node['type'] == 'Rational' else node['value']
        if node['kind'] == 'reference': return bindings[node['name']]
        args = [evaluate(child) for child in node['arguments']]
        op = node['operation']
        if op == 'add': return args[0]+args[1]
        if op == 'sub': return args[0]-args[1]
        if op == 'mul': return args[0]*args[1]
        if op == 'poly': return normalize(args)
        if op == 'padd':
            left, right = list(args[0]), list(args[1])
            size = max(len(left), len(right))
            left += [Fraction(0)]*(size-len(left)); right += [Fraction(0)]*(size-len(right))
            return normalize([a+b for a, b in zip(left, right)])
        if op == 'pmul':
            left, right = args
            return normalize([sum((left[i]*right[k-i] for i in range(len(left)) if 0 <= k-i < len(right)), Fraction(0))
                              for k in range(len(left)+len(right)-1)])
        if op == 'derivative':
            coefficients = args[0]
            return normalize([coefficients[n]*n for n in range(1, len(coefficients))] or [Fraction(0)])
        if op == 'divmod':
            dividend, divisor = args
            size = max(0, len(dividend)-len(divisor)+1)
            quotient = [Fraction(0)]*size
            # Solve the upper triangular coefficient equations directly from
            # the original dividend, rather than mutating a remainder as VM does.
            for k in reversed(range(size)):
                degree = k+len(divisor)-1
                known = sum((quotient[j]*divisor[degree-j]
                             for j in range(k+1, size) if 0 <= degree-j < len(divisor)), Fraction(0))
                quotient[k] = (dividend[degree]-known)/divisor[-1]
            remainder = [coefficient-sum((quotient[j]*divisor[degree-j]
                         for j in range(size) if 0 <= degree-j < len(divisor)), Fraction(0))
                         for degree, coefficient in enumerate(dividend)]
            return {'quotient': normalize(quotient or [Fraction(0)]), 'remainder': normalize(remainder)}
        if op in ('quotient', 'remainder'): return args[0][op]
        if op == 'evaluate':
            coefficients, x = args
            return sum((coefficient*(x**exponent) for exponent, coefficient in enumerate(coefficients)), Fraction(0))
        if op == 'concat': return ''.join(args)
        if op == 'replace': return args[2].join(args[0].split(args[1]))
        _refuse('REFERENCE_OPERATION', 'Reference evaluator has no operation rule.', node['span'])

    for statement in program['ast']:
        value = evaluate(statement['expression'])
        if statement['kind'] == 'let': bindings[statement['name']] = value
        else: outputs[statement['name']] = _encode_value(statement['type'], value)
    return outputs


def _validate_package_shape(program):
    if type(program) is not dict or type(program.get('source')) is not str:
        _refuse('PACKAGE_FORMAT', 'Expected a compiled package containing native source.')
    # Bound untrusted serialized metadata before recursion/canonicalization.
    pending, visited, size = [(program, 0)], 0, 0
    while pending:
        value, depth = pending.pop()
        visited += 1
        if visited > 200000 or depth > 160: _refuse('PACKAGE_FORMAT', 'Package structure exceeds limits.')
        if type(value) is dict:
            if len(value) > 200000: _refuse('PACKAGE_FORMAT', 'Package has too many fields.')
            for key, child in value.items():
                if type(key) is not str: _refuse('PACKAGE_FORMAT', 'Package keys must be strings.')
                try: size += len(key.encode())
                except UnicodeEncodeError: _refuse('PACKAGE_FORMAT', 'Package key contains invalid Unicode.')
                pending.append((child, depth+1))
        elif type(value) is list:
            if len(value) > 200000: _refuse('PACKAGE_FORMAT', 'Package has too many elements.')
            pending.extend((child, depth+1) for child in value)
        elif type(value) is str:
            try: size += len(value.encode())
            except UnicodeEncodeError: _refuse('PACKAGE_FORMAT', 'Package contains invalid Unicode.')
        elif type(value) is int:
            if value.bit_length() > 64: _refuse('PACKAGE_FORMAT', 'Package integer exceeds its bound.')
        else: _refuse('PACKAGE_FORMAT', 'Package contains an unsupported value type.')
        if size > 4000000: _refuse('PACKAGE_FORMAT', 'Package exceeds its byte budget.')


def execute_program(program: dict) -> dict:
    """Validate source-to-package identity, execute bytecode, compare reference."""
    try:
        _validate_package_shape(program)
        expected = _compile(program['source'])
        if _canonical(program) != _canonical(expected):
            _refuse('PACKAGE_MISMATCH', 'Package differs from trusted lowering of its retained source.')
        outputs, work = _vm(expected)
        witness = _reference(expected)
        if outputs != witness: _refuse('VERIFICATION_FAILED', 'Bytecode and AST evaluator disagree.')
        return {'ok': True, 'version': VERSION, 'package_sha256': expected['package_sha256'],
                'source_sha256': expected['source_sha256'], 'outputs': outputs,
                'cost': {'instructions': len(expected['instructions']), 'vm_work_units': work},
                'effects': [], 'verification': {'agreement': True, 'method': 'bytecode versus separate AST evaluator',
                'evidence_class': 'differential-check', 'shared_dependencies': ['lexer/parser/typechecker', 'fractions.Fraction'],
                'limitation': 'finite supported profile; agreement is not proof or full mission acceptance'}}
    except Refusal as exc: return {'ok': False, 'error': exc.error}



# Public expression operations extend the API without altering program packages.
TERM_VERSION = 'polyia.term/0.1'
_TERM_TYPES = ('Rational', 'Polynomial', 'Division', 'Text')


def _term_bindings(bindings):
    if bindings is None:
        return {}
    if type(bindings) is not dict or len(bindings) > 32:
        _refuse('TERM_CONTEXT', 'Term context must contain at most 32 typed free variables.')
    for name, kind in bindings.items():
        if (type(name) is not str or len(name) > 128 or not NAME.fullmatch(name)
                or type(kind) is not str or kind not in _TERM_TYPES):
            _refuse('TERM_CONTEXT', 'Free variables require bounded native names and supported types.')
    return dict(bindings)


def _term_without_spans(node):
    return {key: [_term_without_spans(child) for child in value] if key == 'arguments' else value
            for key, value in node.items() if key != 'span'}


def _parse_term(source, bindings):
    if type(source) is not str:
        _refuse('SOURCE_TYPE', 'Term source must be a string.')
    if len(source) > LIMITS['source_bytes']:
        _refuse('SOURCE_BUDGET', 'Term source exceeds its character budget.')
    try:
        data = source.encode('utf-8')
    except UnicodeEncodeError:
        _refuse('INVALID_UNICODE', 'Term source must contain Unicode scalar values.')
    if len(data) > LIMITS['source_bytes']:
        _refuse('SOURCE_BUDGET', 'Term source exceeds its byte budget.')
    return _term_without_spans(_typed_expression(_parse(_lex(source)), bindings))


def parse_term(source: str, bindings=None) -> dict:
    """Parse one typed expression; retain raw source separately from its term."""
    try:
        context = _term_bindings(bindings)
        term = _parse_term(source, context)
        return {'ok': True, 'version': TERM_VERSION, 'source': source,
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                'bindings': context, 'term': term}
    except Refusal as exc:
        return {'ok': False, 'error': exc.error}


def _term_text(term, bindings):
    count = 0
    source_bytes = 0

    def charge(text):
        nonlocal source_bytes
        source_bytes += len(text.encode('utf-8'))
        if source_bytes > LIMITS['source_bytes']:
            _refuse('SOURCE_BUDGET', 'Printed term exceeds its byte budget.')
        return text

    def render(node, depth):
        nonlocal count
        count += 1
        if count > LIMITS['tokens'] or depth > LIMITS['depth']:
            _refuse('TERM_BUDGET', 'Term node or nesting budget exceeded.')
        if type(node) is not dict or len(node) > 4:
            _refuse('TERM_FORMAT', 'A typed term node must be an object.')
        kind = node.get('kind')
        if kind == 'literal':
            if set(node) != {'kind', 'type', 'value'} or type(node['value']) is not str:
                _refuse('TERM_FORMAT', 'Invalid literal node.')
            value = node['value']
            if len(value) > LIMITS['text_bytes']:
                _refuse('TERM_BUDGET', 'Literal term value exceeds its character bound.')
            if node['type'] == 'Rational':
                if not NUMBER.fullmatch(value):
                    _refuse('TERM_FORMAT', 'Invalid rational literal.')
                if _literal({'value': value, 'span': None}) != value:
                    _refuse('TERM_FORMAT', 'Rational term literals must already be canonical.')
                return charge(value)
            if node['type'] == 'Text':
                try:
                    _text(value)
                except UnicodeEncodeError:
                    _refuse('INVALID_UNICODE', 'Term text must contain Unicode scalar values.')
                if any(ord(char) < 32 and char != '\n' for char in value):
                    _refuse('TERM_FORMAT', 'Text contains controls unavailable in native syntax.')
                return charge('"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"')
            _refuse('TERM_FORMAT', 'Only Rational and Text use literal nodes.')
        if kind == 'reference':
            if set(node) != {'kind', 'type', 'name'} or type(node['name']) is not str:
                _refuse('TERM_FORMAT', 'Invalid reference node.')
            name = node['name']
            if name not in bindings or node['type'] != bindings[name]:
                _refuse('TERM_CONTEXT', 'Reference does not match its explicit free-variable context.')
            return charge(name)
        if kind == 'call':
            if set(node) != {'kind', 'type', 'operation', 'arguments'}:
                _refuse('TERM_FORMAT', 'Invalid call node.')
            operation, arguments = node['operation'], node['arguments']
            if type(operation) is not str or operation not in (*SIGNATURES, 'poly'):
                _refuse('UNKNOWN_OPERATION', 'Term operation is not registered.')
            if type(arguments) is not list or len(arguments) > LIMITS['polynomial_degree'] + 1:
                _refuse('TERM_FORMAT', 'Invalid argument list.')
            charge('(' + operation + ' ' * len(arguments) + ')')
            return '(' + operation + ''.join(' ' + render(child, depth+1) for child in arguments) + ')'
        _refuse('TERM_FORMAT', 'Unknown term node kind.')

    text = render(term, 0)
    # The same frontend validates all signatures and return types. Exact node
    # equality also refuses booleans, foreign fields and noncanonical literals.
    reparsed = _parse_term(text, bindings)
    if reparsed != term:
        _refuse('TERM_FORMAT', 'Term differs from the canonical typed parse of its printed form.')
    return text, reparsed


def print_term(term: dict, bindings=None) -> dict:
    """Print an admitted canonical term; source trivia is intentionally absent."""
    try:
        context = _term_bindings(bindings)
        text, _ = _term_text(term, context)
        return {'ok': True, 'version': TERM_VERSION, 'source': text, 'bindings': context}
    except Refusal as exc:
        return {'ok': False, 'error': exc.error}


def normalize_term(term: dict, bindings=None) -> dict:
    """Bottom-up partial normalization; no cancellation of undefined operations.

Rules fold constant exact rational add/sub/mul, concatenate constant text, and
trim trailing literal polynomial zeros. Every rewrite removes AST nodes; each
rule's output is irreducible at its node. This is no general algebraic solver.
"""
    try:
        context = _term_bindings(bindings)
        _, admitted = _term_text(term, context)
        rewrites = 0

        def normalize(node):
            nonlocal rewrites
            if node['kind'] != 'call':
                return dict(node)
            args = [normalize(child) for child in node['arguments']]
            operation = node['operation']
            if operation in ('add', 'sub', 'mul') and all(arg['kind'] == 'literal' for arg in args):
                a, b = (Fraction(arg['value']) for arg in args)
                value = _rational(a+b if operation == 'add' else a-b if operation == 'sub' else a*b)
                rewrites += 1
                return {'kind': 'literal', 'type': 'Rational', 'value': str(value)}
            if operation == 'concat' and all(arg['kind'] == 'literal' for arg in args):
                value = _text(args[0]['value'] + args[1]['value'])
                rewrites += 1
                return {'kind': 'literal', 'type': 'Text', 'value': value}
            if operation == 'poly':
                while len(args) > 1 and args[-1] == {'kind': 'literal', 'type': 'Rational', 'value': '0'}:
                    args.pop()
                    rewrites += 1
            return dict(node, arguments=args)

        normalized = normalize(admitted)
        return {'ok': True, 'version': TERM_VERSION, 'term': normalized,
                'bindings': context, 'rewrites': rewrites,
                'scope': 'constant rational arithmetic, constant text concatenation, literal polynomial zero tails',
                'effects': []}
    except Refusal as exc:
        return {'ok': False, 'error': exc.error}


def main():
    """File access is confined to the explicit operator CLI, outside the VM."""
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['compile', 'run'])
    parser.add_argument('path', help='.polyia source or serialized compiled package')
    args = parser.parse_args()
    try:
        with open(args.path, 'rb') as handle: data = handle.read(4000001)
        if len(data) > 4000000: _refuse('PACKAGE_FORMAT', 'Input file exceeds its bound.')
        text = data.decode('utf-8')
        if args.command == 'compile': result = compile_program(text)
        else:
            def pairs(items):
                obj = {}
                for key, value in items:
                    if key in obj: _refuse('PACKAGE_FORMAT', 'Duplicate JSON package key.')
                    obj[key] = value
                return obj
            package = json.loads(text, object_pairs_hook=pairs)
            result = execute_program(package)
    except Refusal as exc: result = {'ok': False, 'error': exc.error}
    except (OSError, UnicodeError, ValueError, RecursionError):
        result = {'ok': False, 'error': {'code': 'INPUT_FORMAT', 'message': 'Cannot read a valid bounded input file.'}}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
