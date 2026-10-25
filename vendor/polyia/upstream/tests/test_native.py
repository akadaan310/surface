"""Behavioral acceptance for the bounded compiler, with hand-derived answers."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'polyia' / 'native.py'
from polyia.native import compile_program, execute_program


def source(body):
    return '(commission (profile "polyia.native/0.1") ' + body + ')'


class NativeTests(unittest.TestCase):
    def compile(self, text):
        result = compile_program(text)
        self.assertTrue(result['ok'], result)
        return result['program']

    def run_source(self, text):
        result = execute_program(self.compile(text))
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['verification']['agreement'])
        return result['outputs']

    def refusal(self, text, code):
        result = compile_program(text)
        if result['ok']:
            result = execute_program(result['program'])
        self.assertFalse(result['ok'], result)
        self.assertEqual(result['error']['code'], code, result)
        return result

    def test_exact_rational_polynomial_and_text_composition(self):
        result = self.run_source(source('''
          (let p Polynomial (pmul (poly -1 1) (poly 1 1)))
          (emit polynomial p)
          (emit slope (evaluate (derivative p) 3/2))
          (emit exact (add 1/3 1/6))
          (emit wording (replace (concat "المعادلة: " "x*x - 1") "x*x" "x²"))
        '''))
        self.assertEqual(result, {
          'polynomial': {'type': 'Polynomial', 'value': ['-1', '0', '1']},
          'slope': {'type': 'Rational', 'value': '3'},
          'exact': {'type': 'Rational', 'value': '1/2'},
          'wording': {'type': 'Text', 'value': 'المعادلة: x² - 1'}})

    def test_reference_comparison_on_hand_derived_family(self):
        for n in range(-12, 13):
            result = self.run_source(source(f'(emit y (evaluate (derivative (poly 2 -3 1)) {n}))'))
            self.assertEqual(result['y']['value'], str(2*n-3))

    def test_type_error_carries_utf8_source_span(self):
        text = source('(let s Text "سلام")\n(emit y (add s 1))')
        result = self.refusal(text, 'TYPE_ERROR')
        span = result['error']['span']
        self.assertEqual(text.encode()[span['byte_start']:span['byte_end']].decode(), '(add s 1)')
        self.assertEqual(span['line'], 2)

    def test_unknown_operations_types_effects_and_names_refuse(self):
        cases = [
          ('(emit x (shell "id"))', 'UNKNOWN_OPERATION'),
          ('(emit x (network "https://example.org"))', 'UNKNOWN_OPERATION'),
          ('(let x Float 2)', 'UNKNOWN_TYPE'),
          ('(effect network)', 'UNKNOWN_STATEMENT'),
          ('(emit x missing)', 'UNBOUND_NAME'),
          ('(let x Rational 1)(let x Rational 2)(emit y x)', 'DUPLICATE_NAME'),
          ('(emit x 1)(emit x 2)', 'DUPLICATE_OUTPUT'),
          ('(emit x (add 1))', 'ARITY'),
          ('(emit x (poly "a"))', 'TYPE_ERROR'),
        ]
        for body, code in cases:
            with self.subTest(body=body): self.refusal(source(body), code)

    def test_syntax_profile_and_malformed_numbers_refuse(self):
        for text, code in [
          ('(commission (emit x 1))', 'PROFILE'),
          (source('(emit x 1/0)'), 'ZERO_DENOMINATOR'),
          (source('(emit x 1/2/3)'), 'LEXICAL'),
          (source('(emit x "bad\\t")'), 'LEXICAL'),
          (source('(emit x 1)') + ' trailing', 'SYNTAX'),
          (source('(emit x "\ud800")'), 'INVALID_UNICODE'),
          (source(''), 'NO_OUTPUT'),
          (source('(emit x (poly))'), 'ARITY'),
        ]:
            with self.subTest(code=code): self.refusal(text, code)

    def test_resource_refusals_bound_source_depth_numbers_and_growth(self):
        cases = [
          (source('(emit x "' + 'a'*70000 + '")'), 'SOURCE_BUDGET'),
          (source('(emit x ' + '(add 1 '*70 + '1' + ')'*70 + ')'), 'DEPTH_BUDGET'),
          (source('(emit x ' + '9'*200 + ')'), 'ARITHMETIC_BUDGET'),
          (source('(budget 1)(emit x (add 1 2))'), 'INSTRUCTION_BUDGET'),
          (source('(emit x (poly ' + ' '.join(['1']*66) + '))'), 'POLYNOMIAL_BUDGET'),
          (source('(let x Text "' + 'a'*1000 + '")(emit y (replace x "a" x))'), 'TEXT_BUDGET'),
          (source('(emit y (replace "x" "" "a"))'), 'EMPTY_PATTERN'),
        ]
        for text, code in cases:
            with self.subTest(code=code): self.refusal(text, code)

    def test_serialization_determinism_and_package_tampering(self):
        text = source('(emit y (sub 7/3 1/3))')
        program = self.compile(text)
        self.assertEqual(program, self.compile(text))
        self.assertEqual(execute_program(json.loads(json.dumps(program)))['outputs']['y']['value'], '2')
        for field in ['instructions', 'ast', 'effects', 'source_sha256']:
            altered = copy.deepcopy(program)
            altered[field] = ['network'] if field == 'effects' else [] if field != 'source_sha256' else '0'*64
            result = execute_program(altered)
            self.assertFalse(result['ok'], result)
            self.assertEqual(result['error']['code'], 'PACKAGE_MISMATCH')
        self.assertEqual(execute_program({'version': 'bogus'})['error']['code'], 'PACKAGE_FORMAT')

    def test_polynomial_division_keeps_exact_quotient_and_remainder(self):
        result = self.run_source(source('''
          (let d Division (divmod (poly 1 0 1) (poly 1 2)))
          (emit q (quotient d)) (emit r (remainder d)) (emit division d)
        '''))
        self.assertEqual(result['q']['value'], ['-1/4', '1/2'])
        self.assertEqual(result['r']['value'], ['5/4'])
        self.assertEqual(result['division']['value'], {
            'quotient': ['-1/4', '1/2'], 'remainder': ['5/4']})
        result = self.run_source(source('(emit q (quotient (divmod (poly -1 0 1) (poly -1 1))))'))
        self.assertEqual(result['q']['value'], ['1', '1'])
        self.refusal(source('(emit q (divmod (poly 1) (poly 0)))'), 'ZERO_POLYNOMIAL')
        self.refusal(source('(emit q (quotient (poly 1)))'), 'TYPE_ERROR')

    def test_declared_statement_and_total_work_bounds_are_enforced(self):
        self.refusal(source(' '.join(f'(emit x{i} 1)' for i in range(129))), 'STATEMENT_BUDGET')
        body = '(let x Text "' + 'a'*10000 + '")'
        body += ''.join(f'(let y{i} Text (replace x "a" "b"))' for i in range(25))
        self.refusal(source(body + '(emit result y24)'), 'WORK_BUDGET')
        body = '(let x Text "' + 'a'*10000 + '")'
        body += ''.join(f'(emit y{i} x)' for i in range(7))
        self.refusal(source(body), 'OUTPUT_BUDGET')

    def test_malformed_package_values_never_escape_structured_refusal(self):
        for extra in [True, 1.5, None, object()]:
            program = self.compile(source('(emit x 1)'))
            program['extra'] = extra
            result = execute_program(program)
            self.assertFalse(result['ok'])
            self.assertEqual(result['error']['code'], 'PACKAGE_FORMAT')
        program = self.compile(source('(emit x 1)'))
        program['\ud800'] = 'bad key'
        self.assertEqual(execute_program(program)['error']['code'], 'PACKAGE_FORMAT')
        program = self.compile(source('(emit x 1)'))
        program['cycle'] = program
        self.assertEqual(execute_program(program)['error']['code'], 'PACKAGE_FORMAT')

    def test_no_empty_or_noncanonical_polynomial_and_escaped_strings(self):
        result = self.run_source(source('; comment\n(emit p (padd (poly 1 0 0) (poly -1))) (emit s "a\\n\\\"\\\\")'))
        self.assertEqual(result['p']['value'], ['0'])
        self.assertEqual(result['s']['value'], 'a\n"\\')

    def test_clean_runtime_invocation_without_repository_imports(self):
        program = self.compile(source('(emit p (pmul (poly 1 1) (poly 1 -1)))'))
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp) / 'native.py'
            runtime.write_bytes(MODULE_PATH.read_bytes())
            package = Path(temp) / 'example.json'
            package.write_text(json.dumps(program))
            run = subprocess.run([sys.executable, '-I', '-B', str(runtime), 'run', str(package)],
                                 cwd=temp, capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            result = json.loads(run.stdout)
            self.assertEqual(result['outputs']['p']['value'], ['1', '0', '-1'])
            self.assertTrue(result['verification']['agreement'])

    def test_cli_compile_then_run_and_refusal_exit_status(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'hello.polyia'
            path.write_text(source('(emit text (concat "hello" " world"))'))
            run = subprocess.run([sys.executable, '-B', str(MODULE_PATH), 'compile', str(path)],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertTrue(json.loads(run.stdout)['ok'])
            path.write_text(source('(emit x (exec "touch /tmp/forbidden"))'))
            run = subprocess.run([sys.executable, '-B', str(MODULE_PATH), 'compile', str(path)],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)['error']['code'], 'UNKNOWN_OPERATION')

if __name__ == '__main__': unittest.main()
