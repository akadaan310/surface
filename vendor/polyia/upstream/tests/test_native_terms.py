"""Typed term inverse/normalizer behavior, distinct from source-byte recovery."""
import copy
import unittest

from polyia import native


class NativeTermTests(unittest.TestCase):
    def call(self, name, *args):
        function = getattr(native, name, None)
        self.assertTrue(callable(function), name + ' must be a public bounded term operation')
        return function(*args)

    def term(self, source, bindings=None):
        result = self.call('parse_term', source, bindings)
        self.assertTrue(result['ok'], result)
        return result['term']

    def test_parse_print_inverse_keeps_types_and_explicit_free_variable_context(self):
        bindings = {'x': 'Rational'}
        original = ' ; authored surface\n(add x (mul 06/08 -0/4)) '
        parsed = self.call('parse_term', original, bindings)
        self.assertTrue(parsed['ok'], parsed)
        self.assertEqual(parsed['source'], original)
        self.assertEqual(parsed['version'], 'polyia.term/0.1')
        printed = self.call('print_term', parsed['term'], bindings)
        self.assertTrue(printed['ok'], printed)
        self.assertEqual(printed['source'], '(add x (mul 3/4 0))')
        self.assertEqual(self.term(printed['source'], bindings), parsed['term'])
        self.assertFalse(self.call('parse_term', 'x')['ok'])

    def test_unicode_and_supported_escapes_print_without_normalizing_text(self):
        source = '"أ é é \\" \\\\ \\n"'
        term = self.term(source)
        printed = self.call('print_term', term)
        self.assertTrue(printed['ok'], printed)
        self.assertEqual(self.term(printed['source']), term)
        self.assertEqual(term['value'], 'أ é é " \\ \n')

    def test_normalization_performs_real_partial_rewrites_and_is_idempotent(self):
        term = self.term('(add (mul 3/4 4/3) (sub 7 2))')
        original = copy.deepcopy(term)
        result = self.call('normalize_term', term)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['term'], {'kind': 'literal', 'type': 'Rational', 'value': '6'})
        self.assertEqual(result['rewrites'], 3)
        self.assertEqual(term, original)
        again = self.call('normalize_term', result['term'])
        self.assertEqual(again['term'], result['term'])
        self.assertEqual(again['rewrites'], 0)

    def test_polynomial_and_text_normal_forms_preserve_declared_observable(self):
        for source, expected in [('(poly 3 (sub 1 1) 0)', '(poly 3)'),
                                 ('(poly 0 0 0)', '(poly 0)'),
                                 ('(concat "a\\n" "ب")', '"a\\nب"')]:
            with self.subTest(source=source):
                normalized = self.call('normalize_term', self.term(source))
                self.assertTrue(normalized['ok'], normalized)
                self.assertEqual(self.call('print_term', normalized['term'])['source'], expected)

    def test_partial_operations_and_free_variables_are_not_erased(self):
        for source, bindings in [('(add x 0)', {'x': 'Rational'}),
                                  ('(quotient (divmod (poly 1) (poly 0)))', {}),
                                  ('(replace "a" "" "b")', {})]:
            with self.subTest(source=source):
                term = self.term(source, bindings)
                result = self.call('normalize_term', term, bindings)
                self.assertTrue(result['ok'], result)
                self.assertEqual(result['term'], term)

    def test_types_unknown_functions_bad_context_and_trailing_terms_refuse(self):
        for source, bindings in [('(add "x" 1)', {}), ('(sin 1)', {}),
                                  ('(exec "id")', {}), ('x', {'x': 'Float'}),
                                  ('1 2', {}), ('x', {'bad name': 'Rational'}),
                                  ('1/0', {}), ('"\ud800"', {})]:
            with self.subTest(source=repr(source)):
                result = self.call('parse_term', source, bindings)
                self.assertFalse(result['ok'], result)
                self.assertIn('code', result['error'])

    def test_untrusted_terms_cycles_wrong_types_and_extra_fields_refuse(self):
        valid = self.term('(add 1 2)')
        cases = [None, True, [], {'kind': 'literal', 'type': 'Rational', 'value': '2/4'}]
        wrong = copy.deepcopy(valid); wrong['type'] = 'Text'; cases.append(wrong)
        extra = copy.deepcopy(valid); extra['effects'] = ['network']; cases.append(extra)
        cyclic = copy.deepcopy(valid); cyclic['arguments'][0] = cyclic; cases.append(cyclic)
        bad_string = {'kind': 'literal', 'type': 'Text', 'value': '\ud800'}; cases.append(bad_string)
        for term in cases:
            for operation in ['print_term', 'normalize_term']:
                with self.subTest(operation=operation, term_type=type(term).__name__):
                    result = self.call(operation, term)
                    self.assertFalse(result['ok'], result)

    def test_depth_text_and_arithmetic_growth_are_bounded(self):
        for text in ['(add 1 ' * 70 + '1' + ')' * 70, '"' + 'a' * 20000 + '"']:
            self.assertFalse(self.call('parse_term', text)['ok'])
        large = str(2**400)
        result = self.call('normalize_term', self.term('(mul ' + large + ' ' + large + ')'))
        self.assertFalse(result['ok'], result)
        self.assertEqual(result['error']['code'], 'ARITHMETIC_BUDGET')


if __name__ == '__main__':
    unittest.main()
