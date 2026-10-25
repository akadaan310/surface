"""Headless reuse contracts: actual outputs, refusals, custody and view isolation."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / 'tools/polyia_surface_demo.py'
VENDOR = ROOT / 'vendor/polyia'
NODE = shutil.which('node')
try:
    NODE24 = bool(NODE) and int(subprocess.check_output(
        [NODE, '--version'], text=True, timeout=5).strip().lstrip('v').split('.')[0]) >= 24
except (OSError, ValueError, subprocess.SubprocessError):
    NODE24 = False


class PolyiaIntegrationTests(unittest.TestCase):
    def adapter(self):
        self.assertTrue(ADAPTER.is_file(), 'The headless Surface adapter is not implemented.')
        spec = importlib.util.spec_from_file_location('surface_polyia_demo', ADAPTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_real_generators_and_native_vm_agree_with_literal_results(self):
        result = self.adapter().build_demo()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['protocol']['words'], [['PING', 'ACK'], ['PING', 'ACK', 'ACK']])
        self.assertFalse(result['protocol']['negative_member'])
        self.assertEqual(result['polynomial']['candidate_count'], 18)
        first = result['polynomial']['first']
        self.assertEqual(first['dividend'], ['0', '0', '-1/2'])
        self.assertEqual(first['divisor'], ['-1', '1'])
        self.assertEqual(first['quotient'], ['-1/2', '-1/2'])
        self.assertEqual(first['remainder'], ['-1/2'])
        self.assertEqual(result['native']['outputs']['product_derivative']['value'], ['0', '1', '-3/2'])
        self.assertEqual(result['native']['outputs']['quotient_numerator']['value'], ['0', '1', '-1/2'])
        self.assertEqual(first['domain']['requirement'], 'b(x) != 0')

    def test_replay_detects_tampering_and_budget_does_not_claim_impossibility(self):
        result = self.adapter().build_demo()
        self.assertTrue(result['protocol']['replay']['ok'])
        self.assertFalse(result['protocol']['tampered_replay']['ok'])
        self.assertEqual(result['polynomial']['limited_inverse']['status'], 'RESOURCE_LIMIT')
        self.assertEqual(result['polynomial']['limited_inverse']['classification'], 'UNRESOLVED_SEARCH_BUDGET')
        self.assertFalse(result['polynomial']['limited_inverse']['complete'])
        self.assertFalse(result['full_mission_acceptance'])
        self.assertFalse(result['llm_inference'])

    def test_view_changes_preserve_semantics_and_atom_checkpoint_needs_a_ledger(self):
        result = self.adapter().build_demo()
        self.assertEqual(result['forms']['before_content_cid'], result['forms']['after_content_cid'])
        self.assertNotEqual(result['forms']['before_representation_cid'], result['forms']['after_representation_cid'])
        self.assertTrue(result['forms']['roundtrip_equal'])
        self.assertEqual(result['astra']['phases'], ['OBSERVE', 'PROPOSE', 'ADMIT', 'EXECUTE', 'VERIFY', 'CHECKPOINT'])
        self.assertEqual(result['astra']['checkpoint_attempt'], 'PERSISTENCE_REQUIRED')
        self.assertEqual(result['astra']['event_persistence'], 'NOT_COMMITTED_BY_KERNEL')

    def test_changed_vendored_runtime_refuses_before_it_can_execute(self):
        module = self.adapter()
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'polyia'
            shutil.copytree(VENDOR, candidate)
            executable = candidate / 'upstream/polyia/generators.py'
            executable.write_bytes(executable.read_bytes() + b'\nraise RuntimeError("untrusted execution")\n')
            with self.assertRaisesRegex(ValueError, 'custody'):
                module.build_demo(vendor_root=candidate)

    def test_demo_is_deterministic_and_runs_from_an_independent_working_directory(self):
        module = self.adapter()
        self.assertEqual(module.build_demo(), module.build_demo())
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'receipt.json'
            completed = subprocess.run(
                [sys.executable, '-I', '-B', str(ADAPTER), '--output', str(output)],
                cwd=temporary, capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json.loads(output.read_text()), json.loads(completed.stdout))
            self.assertEqual(json.loads(completed.stdout)['status'], 'PASS')

    @unittest.skipUnless(NODE24, 'Node 24+ is unavailable; University execution is NOT_RUN.')
    def test_university_uses_real_exact_matrices_world_rules_and_topic_registry(self):
        driver = VENDOR / 'university_demo.mjs'
        self.assertTrue(driver.is_file(), 'The headless University adapter is not implemented.')
        completed = subprocess.run(
            [NODE, '--no-warnings', str(driver)],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result['matrix'], [['0', '-2', '1'], ['2', '0', '0'], ['0', '0', '1']])
        self.assertEqual(result['rule90_rows'], ['000010000', '000101000', '001000100', '010101010'])
        self.assertTrue(result['non_quarter_turn_refused'])
        self.assertTrue(result['uncommitted_refused'])
        self.assertTrue(result['cycle_refused'])
        self.assertEqual(result['preimage_kinds'], ['empty', 'affine'])
        self.assertEqual(result['registry']['topic_count'], 62)
        self.assertEqual(result['registry']['labels'], {'established': 42, 'house': 18, 'application': 2})
        self.assertEqual(result['registry']['topics_by_division'], {'foundations': 10, 'relational': 10,
                         'languages': 10, 'geometry': 12, 'acoustic': 10, 'worlds': 10})
        self.assertFalse(result['browser_required'])
        self.assertFalse(result['full_university_acceptance'])


if __name__ == '__main__':
    unittest.main()
