"""CERN observed-data custody plus explicitly synthetic kinematic controls."""
import gzip
import hashlib
import importlib.util
import math
from pathlib import Path
import sys
import tempfile
import time
import unittest
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FIRST = (b"165617,74601703,G,9.6987,-9.5104,0.3662,1.8633,9.5175,0.1945,3.1031,-1,"
         b"G,9.7633,7.3277,-1.1524,6.3473,7.4178,0.7756,-0.1560,1,17.4922\n")


class ColliderTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "research/quantum_oracle/collider.py"
        self.assertTrue(path.is_file(), "bounded observed collider adapter is missing")
        spec = importlib.util.spec_from_file_location("collider_contract", path)
        self.c = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.c
        spec.loader.exec_module(self.c)

    def fixture(self, line=FIRST):
        return self.c.HEADER + b"\n" + line

    def test_exact_source_offsets_and_large_integer_identifiers(self):
        source = self.fixture(FIRST.replace(b"74601703", b"9007199254740993"))
        event = next(self.c.iter_events(source))
        self.assertEqual(event.run, 165617)
        self.assertEqual(event.event, 9007199254740993)
        self.assertEqual(event.row_index, 0)
        self.assertEqual(source[event.byte_start:event.byte_end], source[len(self.c.HEADER)+1:])
        self.assertEqual(event.source_sha256, hashlib.sha256(source).hexdigest())
        lo, hi = event.field_spans[3]
        self.assertEqual(source[lo:hi], b"9.6987")
        self.assertEqual(event.muon1.momentum.rounding[0], .00005)
        self.assertEqual(event.muon1.charge, -1)
        self.assertEqual(event.published_mass, 17.4922)

    def test_synthetic_back_to_back_invariant_and_scalar_vector_agreement(self):
        p = self.c.FourMomentum(5, 4, 0, 0)
        q = self.c.FourMomentum(5, -4, 0, 0)
        self.assertEqual(p.mass(), 3)
        self.assertEqual((p+q).mass(), 10)
        raw = np.array([[[5., 4, 0, 0], [5, -4, 0, 0]],
                        [[5., 0, 3, 0], [5, 0, -3, 0]]])
        np.testing.assert_array_equal(self.c.vectorized_pair_mass_squared(raw), [100, 100])

    def test_synthetic_lorentz_boost_preserves_mass_and_has_declared_direction(self):
        p = self.c.FourMomentum(5, 4, 0, 0)
        rest = p.boost((.8, 0, 0))
        self.assertAlmostEqual(rest.energy, 3, places=13)
        self.assertAlmostEqual(rest.px, 0, places=13)
        self.assertAlmostEqual(rest.mass_squared(), 9, places=13)
        back = rest.boost((-.8, 0, 0))
        np.testing.assert_allclose(back.components, p.components, atol=2e-14)
        for beta in [(1, 0, 0), (0, 0, math.nan), (0, 0), (True, 0, 0)]:
            with self.subTest(beta=beta), self.assertRaises(self.c.ColliderError):
                p.boost(beta)

    def test_negative_spacelike_nonfinite_and_units_reject_explicitly(self):
        for args in [(-1, 0, 0, 0), (math.inf, 0, 0, 0), (5, 4j, 0, 0), (True, 0, 0, 0)]:
            with self.subTest(args=args), self.assertRaises(self.c.ColliderError):
                self.c.FourMomentum(*args)
        with self.assertRaises(self.c.ColliderError):
            self.c.FourMomentum(5, 4, 0, 0, unit="MeV")
        p = self.c.FourMomentum(1, 2, 0, 0)
        self.assertEqual(p.mass_squared(), -3)
        with self.assertRaisesRegex(self.c.ColliderError, "SPACELIKE"):
            p.mass()
        with self.assertRaises(self.c.ColliderError):
            self.c.vectorized_pair_mass_squared(np.ones((1, 2, 4), dtype=complex))

    def test_signed_integer_minimum_cannot_wrap_past_component_bound(self):
        for dtype in (np.int32, np.int64):
            data = np.zeros((1, 2, 4), dtype=dtype)
            data[0, 0, 1] = np.iinfo(dtype).min
            with self.subTest(dtype=dtype), self.assertRaises(self.c.ColliderError):
                self.c.vectorized_pair_mass_squared(data)

    def test_rounding_interval_derived_from_each_original_token(self):
        self.assertEqual(self.c.decimal_half_step("1.2300"), .00005)
        self.assertEqual(self.c.decimal_half_step("123.4"), .05)
        self.assertEqual(self.c.decimal_half_step("1.23e2"), .5)
        event = next(self.c.iter_events(self.fixture()))
        report = self.c.compare_mass(event)
        self.assertTrue(report["rounding_intervals_overlap"])
        self.assertLess(report["mass_interval_GeV"][0], event.published_mass)
        self.assertGreater(report["mass_interval_GeV"][1], event.published_mass)
        false = next(self.c.iter_events(self.fixture(FIRST.replace(b"17.4922", b"18.4922"))))
        self.assertFalse(self.c.compare_mass(false)["rounding_intervals_overlap"])

    def test_pair_negative_central_mass_is_retained_without_zero_clipping(self):
        source = self.fixture(b"1,2,G,1.0000,1.0001,0.0000,0.0000,1.0001,0.0000,0.0000,-1,"
                              b"G,1.0000,1.0001,0.0000,0.0000,1.0001,0.0000,0.0000,1,0.0000\n")
        event = next(self.c.iter_events(source))
        result = self.c.compare_mass(event)
        self.assertLess(result["mass_squared_GeV2"], 0)
        self.assertIsNone(result["central_mass_GeV"])
        self.assertEqual(result["central_mass_status"], "SPACELIKE_PRINTED_INPUT")

    def test_format_limits_finite_and_integer_grammar_rejection(self):
        lines = [FIRST.replace(b"165617", b"165617.0"), FIRST.replace(b"9.6987", b"nan"),
                 FIRST.replace(b"9.6987", b"-9.6987"), FIRST.replace(b"17.4922", b"-1.0000"),
                 FIRST.replace(b",G,", b",X,", 1), FIRST.replace(b",-1,G,", b",0,G,"),
                 FIRST.rstrip(b"\n") + b",0\n", b"\n", FIRST.replace(b"9.6987", b"\"9.6987\"")]
        for line in lines:
            with self.subTest(line=line[:50]), self.assertRaises(self.c.ColliderError):
                list(self.c.iter_events(self.fixture(line)))
        with self.assertRaises(self.c.ColliderError):
            list(self.c.iter_events(b"bad header\n"+FIRST))
        with self.assertRaises(self.c.ColliderError):
            list(self.c.iter_events(self.fixture(), limits=self.c.Limits(max_bytes=32)))
        with self.assertRaises(self.c.ColliderError):
            list(self.c.iter_events(self.fixture(FIRST+FIRST), limits=self.c.Limits(max_events=1)))
        with self.assertRaises(self.c.ColliderError):
            list(self.c.iter_events(self.fixture(b"0"*1025+b"\n")))
        with self.assertRaises(self.c.ColliderError):
            self.c.Limits(max_events=100001)
        budget = self.c.Budget(.001)
        time.sleep(.005)
        with self.assertRaisesRegex(self.c.ColliderError, "TIME_LIMIT"):
            list(self.c.iter_events(self.fixture(), budget=budget))

    def test_source_reconstruction_handles_crlf_and_preserves_duplicate_ids(self):
        source = self.fixture(FIRST+FIRST).replace(b"\n", b"\r\n")
        rows = list(self.c.iter_events(source))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].event, rows[1].event)
        self.assertNotEqual(rows[0].row_index, rows[1].row_index)
        self.assertEqual(source[rows[1].byte_start:rows[1].byte_end], FIRST.replace(b"\n", b"\r\n"))

    def test_gzip_bomb_and_source_tampering_reject(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"bad.csv.gz"
            path.write_bytes(gzip.compress(b"a"*2048))
            with self.assertRaises(self.c.ColliderError):
                self.c.read_source(path, limits=self.c.Limits(max_bytes=1024))
        with self.assertRaisesRegex(self.c.ColliderError, "SOURCE_IDENTITY"):
            self.c.verify_published_source(self.fixture())

    def test_complete_observed_file_and_published_identity_are_preserved(self):
        path = ROOT / "research/quantum_oracle/data/cern-5201-Dimuon_DoubleMu.csv.gz"
        self.assertTrue(path.is_file(), "authentic CERN fixture is absent; do not substitute synthetic data")
        raw = self.c.read_source(path)
        identity = self.c.verify_published_source(raw)
        self.assertEqual(len(raw), 13935840)
        self.assertEqual(f"{zlib.adler32(raw)&0xffffffff:08x}", "5b87a72a")
        self.assertEqual(identity["sha256"], "58caa45c580f8bcf4b457281c8525a56de0e0b8eb0e0b29e86a9b655a8e64d35")
        report = self.c.analyze(raw)
        self.assertEqual(report["event_rows"], 100000)
        self.assertEqual(report["source_coverage"]["first_byte"], len(self.c.HEADER)+1)
        self.assertEqual(report["source_coverage"]["last_byte"], len(raw))
        self.assertEqual(report["mass_comparison"]["outside_rounding_intervals"], 1381)
        self.assertEqual(report["individual_muons"]["spacelike_beyond_rounding"], 949)
        self.assertEqual(report["mass_comparison"]["negative_central_mass_squared"], 1)
        self.assertEqual(report["independent_reader"]["status"], "ACCEPT")
        self.assertFalse(report["full_G4_acceptance"])
        self.assertEqual(len(report["counterexamples"]), 1381)
        self.assertTrue(report["source_sha256"])

    def test_deterministic_archive_reconstructs_exact_bytes(self):
        data = self.fixture()
        one = self.c.deterministic_gzip(data)
        self.assertEqual(one, self.c.deterministic_gzip(data))
        self.assertEqual(gzip.decompress(one), data)
        self.assertEqual(one[4:8], bytes(4))
        for seconds in (0, 61, math.nan):
            with self.subTest(seconds=seconds), self.assertRaises(self.c.ColliderError):
                self.c.download_published(max_seconds=seconds)

    def test_analysis_and_optional_limits_reject_malformed_types(self):
        for call in [lambda: list(self.c.iter_events(self.fixture(), limits=False)),
                     lambda: list(self.c.iter_events(self.fixture(), budget=False)),
                     lambda: self.c.analyze(self.fixture(), limits="large", require_published=False),
                     lambda: self.c.analyze(self.fixture(), require_published="yes"),
                     lambda: self.c.analyze("csv", require_published=False),
                     lambda: list(self.c.iter_events(self.c.HEADER+b"\r\r\n"+FIRST))]:
            with self.subTest(call=call), self.assertRaises(self.c.ColliderError):
                call()

    def test_counterexample_budget_rejects_without_silent_truncation(self):
        false = FIRST.replace(b"17.4922", b"18.4922")
        with self.assertRaisesRegex(self.c.ColliderError, "counterexample"):
            self.c.analyze(self.fixture(false+false), require_published=False,
                           limits=self.c.Limits(max_counterexamples=1))

    def test_unverified_fixture_is_not_labelled_cern_observation(self):
        report = self.c.analyze(self.fixture(), require_published=False)
        self.assertEqual(report["evidence_class"], "unverified user-supplied controlled input")
        self.assertIsNone(report["source_url"])
        self.assertFalse(report["published_source_verified"])
        self.assertFalse(report["full_G4_acceptance"])

    def test_empty_event_table_has_explicit_format_error(self):
        with self.assertRaisesRegex(self.c.ColliderError, "FORMAT.*no event rows"):
            self.c.analyze(self.c.HEADER+b"\n", require_published=False)


if __name__ == "__main__":
    unittest.main()
