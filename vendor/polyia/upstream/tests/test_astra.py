"""Astra adapter checks use hand-derived geometry and a published SHA-256 vector."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest

try:
    from polyia.astra import run_adapter
except ImportError:
    def run_adapter(parameters):
        return {'ok': False, 'status': 'REFUSED', 'error': {'code': 'NOT_IMPLEMENTED'}}


def request(operation, **fields):
    return {'adapter_version': 'POLYIA-ASTRA/0.1', 'source_version': 'ASTRA/0.2',
            'protocol': 'ATOM-HANDOFF/0.1', 'operation': operation, **fields}


def point(ra=0, dec=0, **fields):
    return {'id': 'direction-1', 'ra_deg': ra, 'dec_deg': dec,
            'provenance': {'kind': 'synthetic', 'source_id': 'authored:test'}, **fields}


def scene(points=None, **view):
    return request('geometry.project', input={
        'observer': 'ICRS-direction-only', 'points': points or [point()],
        'view': {'width': 800, 'height': 500, 'distance': 4,
                 'yaw_rad': 0, 'pitch_rad': 0, **view}})


class AstraTests(unittest.TestCase):
    def run_ok(self, value):
        result = run_adapter(value)
        self.assertTrue(result['ok'], result)
        return result

    def refused(self, value, code):
        before = copy.deepcopy(value)
        result = run_adapter(value)
        self.assertFalse(result['ok'], result)
        self.assertEqual(result['status'], 'REFUSED')
        self.assertEqual(result['error']['code'], code, result)
        self.assertEqual(value, before)
        return result

    def initialized(self):
        return self.run_ok(request('atom.initialize'))

    def advance(self, result, parameters=None):
        return self.run_ok(request('atom.advance', state=result['state'],
            expected_state_digest=result['report']['state_digest'], input=parameters or {}))

    def test_cardinal_vectors_match_the_inherited_axis_convention(self):
        for ra, dec, expected in [(0, 0, [0, 0, 1]), (90, 0, [1, 0, 0]),
                (180, 0, [0, 0, -1]), (270, 0, [-1, 0, 0]),
                (0, 90, [0, 1, 0]), (0, -90, [0, -1, 0])]:
            with self.subTest(ra=ra, dec=dec):
                p = self.run_ok(scene([point(ra, dec)]))['projection']['points'][0]
                for got, want in zip(p['unit_vector'], expected):
                    self.assertAlmostEqual(got, want, places=12)

    def test_norm_and_radius_are_distinct_from_semantic_coordinates(self):
        p = self.run_ok(scene([point(45, 30, radius=2)]))['projection']['points'][0]
        self.assertAlmostEqual(math.hypot(*p['unit_vector']), 1, places=12)
        self.assertAlmostEqual(math.hypot(*p['camera_vector']), 2, places=12)
        self.assertAlmostEqual(p['unit_vector'][0], math.sqrt(6)/4, places=12)
        self.assertAlmostEqual(p['unit_vector'][1], .5, places=12)

    def test_known_perspective_and_yaw_pitch_signs(self):
        p = self.run_ok(scene([point(90)]))['projection']['points'][0]
        self.assertAlmostEqual(p['screen']['x'], 578.75, places=10)
        self.assertAlmostEqual(p['screen']['y'], 255, places=10)
        for view, expected in [({'yaw_rad': math.pi/2}, [-1, 0, 0]),
                               ({'pitch_rad': math.pi/2}, [0, -1, 0])]:
            p = self.run_ok(scene(**view))['projection']['points'][0]
            for got, want in zip(p['camera_vector'], expected):
                self.assertAlmostEqual(got, want, places=12)
        p = self.run_ok(scene([point(0, 90)]))['projection']['points'][0]
        self.assertAlmostEqual(p['screen']['y'], 76.25, places=10)

    def test_near_plane_clips_without_division_or_false_failure(self):
        for distance in [1, 1.399, .5]:
            p = self.run_ok(scene(distance=distance))['projection']['points'][0]
            self.assertTrue(p['clipped'])
            self.assertIsNone(p['screen'])
        # radius=.1, distance=.5 has an exactly represented subtraction of .4.
        p = self.run_ok(scene([point(radius=.1)], distance=.5))['projection']['points'][0]
        self.assertFalse(p['clipped'])

    def test_camera_and_display_radius_leave_semantic_digest_unchanged(self):
        original = scene()
        before = copy.deepcopy(original)
        a = self.run_ok(original)
        b = self.run_ok(scene([point(radius=2)], yaw_rad=.3, selected='direction-1'))
        self.assertEqual(a['semantic_digest'], b['semantic_digest'])
        self.assertNotEqual(a['projection'], b['projection'])
        self.assertEqual(a['semantic_objects'], b['semantic_objects'])
        self.assertEqual(original, before)
        bad = scene()
        bad['input']['view']['semantic_relation'] = 'same-as'
        self.refused(bad, 'SCHEMA')

    def test_provenance_stays_caller_asserted_and_no_observer_transform_is_invented(self):
        values = [point(), point(90, id='HIP 32349', provenance={
            'kind': 'catalog', 'source_id': 'hipparcos:32349'})]
        result = self.run_ok(scene(values))
        self.assertEqual([p['provenance']['kind'] for p in result['semantic_objects']],
                         ['synthetic', 'catalog'])
        self.assertEqual(result['provenance_verification'], 'CALLER_ASSERTED_NOT_CATALOG_VERIFIED')
        bad = scene(); bad['input']['observer'] = 'Mars'
        self.refused(bad, 'UNSUPPORTED_OBSERVER')

    def test_nonfinite_extreme_and_missing_context_refuse(self):
        for value in [float('nan'), float('inf'), -float('inf'), 10**1000, True, '90']:
            with self.subTest(value=str(value)[:20]):
                result = run_adapter(scene([point(value)]))
                self.assertFalse(result['ok'], result)
                self.assertEqual(result['status'], 'REFUSED')
        for field, value in [('ra_deg', -1), ('ra_deg', 360), ('dec_deg', 91),
                             ('radius', 0), ('radius', 1e308)]:
            self.refused(scene([point(**{field: value})]), 'DOMAIN')
        for field in ['observer', 'view']:
            bad = scene(); del bad['input'][field]
            self.refused(bad, 'SCHEMA')
        self.refused(scene(width=0), 'DOMAIN')
        self.refused(scene(yaw_rad=1e100), 'DOMAIN')

    def test_versions_unknown_operations_and_unbounded_values_refuse(self):
        for key in ['adapter_version', 'source_version', 'protocol']:
            bad = scene(); bad[key] = 'unknown'
            self.refused(bad, 'VERSION')
        self.refused(request('shell', input={'command': 'id'}), 'UNKNOWN_OPERATION')
        self.refused(scene([point(id=str(i)) for i in range(257)]), 'RESOURCE_LIMIT')
        bad = scene(); bad['input']['points'][0]['provenance']['kind'] = 'proved'
        self.refused(bad, 'PROVENANCE')
        self.refused(scene([point(), point()]), 'DUPLICATE_ID')
        bad = scene(); bad['input']['points'][0]['id'] = '\ud800'
        self.refused(bad, 'INVALID_UNICODE')

    def test_atom_evidence_advances_one_phase_with_published_hash_vector(self):
        result = self.initialized()
        for index, phase in enumerate(['PROPOSE', 'ADMIT', 'EXECUTE', 'VERIFY', 'CHECKPOINT'], 1):
            result = self.advance(result, {'artifact': 'known-vector', 'content': 'abc'} if index == 1 else None)
            self.assertEqual(result['report']['phase'], phase)
            self.assertEqual(result['report']['tick'], index)
            self.assertEqual(len(result['state']['events']), index)
        self.assertEqual(result['state']['pending']['output'], {
            'artifact': 'known-vector',
            'sha256': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
            'source': 'caller-provided'})
        self.assertEqual(result['report']['verification']['evidence_class'], 'HANDLER_SELF_CONSISTENCY')
        self.assertEqual(result['report']['verification']['verdict'], 'PASS')
        self.assertIsNone(result['report']['checkpoint_head'])
        self.assertFalse(result['report']['verification']['independent'])

    def test_atom_report_does_not_advance_and_has_all_handoff_fields(self):
        result = self.advance(self.initialized(), {'artifact': 'text', 'content': 'hello'})
        before = copy.deepcopy(result['state'])
        inspect = self.run_ok(request('atom.report', state=result['state']))
        self.assertEqual(inspect['state'], before)
        self.assertEqual(inspect['report']['state_digest'], result['report']['state_digest'])
        self.assertTrue({'protocol', 'state_digest', 'tick', 'phase', 'active',
            'checkpoint_head', 'recent', 'verification', 'next_action', 'limits'} <= inspect['report'].keys())

    def test_atom_stale_guard_bad_phase_and_mutated_output_refuse_without_advancement(self):
        result = self.initialized()
        bad = request('atom.advance', state=result['state'], expected_state_digest='0'*64, input={})
        rejected = self.refused(bad, 'STALE_STATE')
        self.assertEqual(rejected['state'], result['state'])
        bad = request('atom.report', state=copy.deepcopy(result['state']))
        bad['state']['phase'] = 'TELEPORT'
        self.refused(bad, 'PHASE')
        for _ in range(4):
            result = self.advance(result)
        bad = request('atom.report', state=copy.deepcopy(result['state']))
        bad['state']['pending']['output']['sha256'] = '0'*64
        self.refused(bad, 'STATE_INTEGRITY')

    def test_atom_guard_refuses_at_admit_and_does_not_execute_strings(self):
        result = self.advance(self.initialized(), {'artifact': 'literal', 'content': '__import__("os").system("id")'})
        result = self.advance(result)
        result = self.advance(result)
        self.assertEqual(result['report']['phase'], 'EXECUTE')
        bad = self.advance(self.initialized(), {'shell': 'id'})
        bad = self.advance(bad)
        rejected = self.refused(request('atom.advance', state=bad['state'],
            expected_state_digest=bad['report']['state_digest'], input={}), 'SCHEMA')
        self.assertEqual(rejected['state']['phase'], 'ADMIT')
        for fields in [{'content': 'x'*10001}, {'artifact': 'x'*121}, {'content': 5}]:
            candidate = self.advance(self.initialized(), fields)
            candidate = self.advance(candidate)
            self.refused(request('atom.advance', state=candidate['state'],
                expected_state_digest=candidate['report']['state_digest'], input={}), 'GUARD')

    def test_checkpoint_requires_real_storage_and_no_batch_resume_is_implied(self):
        result = self.initialized()
        for _ in range(5): result = self.advance(result)
        rejected = self.refused(request('atom.advance', state=result['state'],
            expected_state_digest=result['report']['state_digest'], input={}), 'PERSISTENCE_REQUIRED')
        self.assertEqual(rejected['state'], result['state'])
        self.assertIsNone(rejected['report']['checkpoint_head'])
        bad = request('atom.advance', state=result['state'],
            expected_state_digest=result['report']['state_digest'], input={}, steps=7)
        self.refused(bad, 'SCHEMA')

    def test_source_pins_resolve_actual_bytes_and_results_are_json_finite(self):
        result = self.run_ok(scene())
        root = Path(__file__).resolve().parents[1]
        for source in result['identity']['sources']:
            self.assertEqual(hashlib.sha256((root / source['path']).read_bytes()).hexdigest(), source['sha256'])
            self.assertTrue(source['anchor'])
        self.assertFalse(result['llm_required'])
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_source_evidence_handler_agreement_is_differential_not_independent_proof(self):
        root = Path(__file__).resolve().parents[1]
        original = root / ('sources/expanded/ASTRA_CELESTIAL_SHELLS_ATOM_CODEX_GOD_SEED_V02/'
                           'ASTRA_CELESTIAL_SHELLS_V02/atom/core.py')
        spec = importlib.util.spec_from_file_location('retained_astra_core', original)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for fields in [{}, {'content': ''}, {'artifact': 'unicode', 'content': 'سلام 🌌'}]:
            result = self.initialized()
            for index in range(4): result = self.advance(result, fields if index == 0 else None)
            # Call only the inspected pure handler; never instantiate its disk-backed Universe.
            expected = module.Universe._evaluate(None, 'evidence', fields, None)
            self.assertEqual(result['state']['pending']['output'], expected)

    def test_forged_event_or_phase_cannot_skip_admission(self):
        result = self.initialized()
        for _ in range(4): result = self.advance(result)
        for field, replacement in [('phase', 'CHECKPOINT'), ('tick', 5), ('active', 'shell')]:
            altered = copy.deepcopy(result['state']); altered[field] = replacement
            self.refused(request('atom.report', state=altered), 'STATE_INTEGRITY')
        altered = copy.deepcopy(result['state'])
        altered['events'][2]['verb'] = 'EXECUTE'
        self.refused(request('atom.report', state=altered), 'STATE_INTEGRITY')
        altered = copy.deepcopy(result['state']); altered['protocol'] = 'ATOM/0.2'
        self.refused(request('atom.report', state=altered), 'VERSION')

    def test_state_reconstruction_rejects_json_scalar_type_changes(self):
        result = self.advance(self.advance(self.initialized()))
        altered = copy.deepcopy(result['state'])
        altered['events'][0]['tick'] = True
        self.refused(request('atom.report', state=altered), 'STATE_INTEGRITY')
        altered = copy.deepcopy(result['state'])
        altered['pending']['decision']['nominal'] = 4.0
        self.refused(request('atom.report', state=altered), 'STATE_INTEGRITY')

    def test_nested_json_bounds_and_selection_context_are_enforced(self):
        nested = {}
        for _ in range(20): nested = {'child': nested}
        self.refused(request('atom.advance', state=nested, expected_state_digest='0'*64, input={}), 'RESOURCE_LIMIT')
        self.refused(scene(selected='missing'), 'DOMAIN')
        self.refused(request('atom.initialize', input={}), 'SCHEMA')
        self.refused(scene([point(provenance={'kind': 'catalog'})]), 'SCHEMA')
        empty = scene(); empty['input']['points'] = []
        self.assertEqual(self.run_ok(empty)['semantic_objects'], [])

    def test_atom_input_cannot_change_after_select_and_return_values_are_isolated(self):
        result = self.advance(self.initialized(), {'content': 'abc'})
        rejected = self.refused(request('atom.advance', state=result['state'],
            expected_state_digest=result['report']['state_digest'], input={'content': 'different'}), 'SCHEMA')
        self.assertEqual(rejected['state'], result['state'])
        snapshot = copy.deepcopy(result['state'])
        inspected = self.run_ok(request('atom.report', state=result['state']))
        inspected['state']['pending']['params']['content'] = 'mutated'
        self.assertEqual(result['state'], snapshot)
        again = self.run_ok(request('atom.report', state=result['state']))
        self.assertEqual(again['state']['pending']['params']['content'], 'abc')


if __name__ == '__main__':
    unittest.main()
