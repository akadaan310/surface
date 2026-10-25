"""Real photographic FITS fixture, independent readers and malformed controls."""
import io
import math
from pathlib import Path
import struct
import unittest

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

try:
    from research.quantum_oracle import astro as a
except ImportError:
    a = None

DATA = Path(__file__).resolve().parents[1] / "data/HorseHead.fits"


def replace_card(raw, key, value):
    prefix = key.ljust(8).encode() + b"= "
    offset = raw.index(prefix)
    replacement = f"{key:<8}= {value:>20}".ljust(80).encode()
    return raw[:offset] + replacement + raw[offset + 80:]


class AstronomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = DATA.read_bytes()

    def setUp(self):
        self.assertIsNotNone(a, "bounded FITS adapter is missing")

    def test_real_plate_reader_agrees_on_every_integer_pixel(self):
        image = a.FITSImage(self.raw)
        self.assertEqual(image.shape, (893, 891))
        self.assertEqual(image.data_offset, 14400)
        with fits.open(io.BytesIO(self.raw), memmap=False, do_not_scale_image_data=True) as hdus:
            np.testing.assert_array_equal(image.pixels, hdus[0].data)
            self.assertEqual(image.header["INSTRUME"], "Photographic Plate")
            self.assertEqual(image.header["ORIGIN"], "STScI/MAST")
        self.assertEqual((int(image.pixels.min()), int(image.pixels.max())), (3759, 22918))

    def test_raw_offsets_use_x_fast_big_endian_signed_words(self):
        image = a.FITSImage(self.raw)
        for x, y in ((0, 0), (1, 0), (0, 1), (445, 446), (890, 892)):
            expected_offset = 14400 + 2 * (y * 891 + x)
            witness = image.pixel_witness(x, y)
            expected = struct.unpack_from(">h", self.raw, expected_offset)[0]
            self.assertEqual(witness["offset"], expected_offset)
            self.assertEqual(witness["value"], expected)
            self.assertEqual(witness["hex"], self.raw[expected_offset:expected_offset + 2].hex())
        for xy in ((-1, 0), (891, 0), (0, 893), (True, 0), (1.0, 0)):
            with self.assertRaises(ValueError):
                image.pixel_witness(*xy)

    def test_original_bytes_and_opaque_extension_survive(self):
        image = a.FITSImage(self.raw)
        self.assertEqual(image.raw, self.raw)
        self.assertEqual(image.extension_offset, 1607040)
        self.assertEqual(len(image.raw[image.extension_offset:]), 43200)
        self.assertTrue(image.raw[image.extension_offset:].startswith(b"XTENSION"))
        with self.assertRaises(TypeError):
            image.header["NAXIS1"] = 1000000
        with self.assertRaises(ValueError):
            image.pixels.setflags(write=True)

    def test_bad_shape_encoding_truncation_and_scaling_fail_closed(self):
        for raw in (self.raw[:-1], self.raw[:15000],
                    replace_card(self.raw, "NAXIS1", "99999999999999999"),
                    replace_card(self.raw, "BITPIX", "-32"),
                    replace_card(self.raw, "NAXIS", "3"),
                    replace_card(self.raw, "SIMPLE", "F")):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                a.FITSImage(raw)
        with self.assertRaises((TypeError, ValueError)):
            a.FITSImage(bytearray(self.raw))
        with self.assertRaises(ValueError):
            a.FITSImage(b" " * (4 * 1024 * 1024 + 1))

    def test_duplicate_critical_header_and_nonfinite_wcs_reject(self):
        duplicate = self.raw[:400] + self.raw[240:320] + self.raw[480:]
        with self.assertRaises(ValueError):
            a.FITSImage(duplicate)
        with self.assertRaises(ValueError):
            a.FITSImage(replace_card(self.raw, "CRVAL1", "NaN"))
        end = self.raw.index(b"END " + b" " * 76)
        corrupt = self.raw[:end] + b" " * 80 + self.raw[end + 80:]
        with self.assertRaises(ValueError):
            a.FITSImage(corrupt)

    def test_local_tan_projection_matches_independent_astropy_model(self):
        image = a.FITSImage(self.raw)
        points = np.array([[445, 446], [0, 0], [890, 892], [223.5, 333.25]])
        got = a.local_tan_wcs(image, points)
        # Explicit selection prevents WCSLIB replacing local TAN by full DSS.
        header = fits.Header()
        for key in ("WCSAXES", "CTYPE1", "CTYPE2", "CUNIT1", "CUNIT2", "CRPIX1", "CRPIX2",
                    "CRVAL1", "CRVAL2", "CD1_1", "CD1_2", "CD2_1", "CD2_2", "RADESYS"):
            header[key] = image.header[key]
        reference = WCS(header).wcs_pix2world(points, 0)
        np.testing.assert_allclose(got, reference, rtol=0, atol=1e-11)
        np.testing.assert_allclose(got[0], [85.274970, -2.458265], rtol=0, atol=1e-12)

    def test_unsupported_projection_units_and_coordinate_domain_reject(self):
        for keyword, value in (("CTYPE1", "'RA---SIN'"), ("CUNIT1", "'rad'"),
                               ("RADESYS", "'FK5'"), ("CD1_1", "0"), ("CRVAL2", "100")):
            changed = replace_card(self.raw, keyword, value)
            if keyword == "CD1_1":
                changed = replace_card(changed, "CD1_2", "0")
            with self.subTest(keyword=keyword), self.assertRaises(ValueError):
                a.local_tan_wcs(a.FITSImage(changed), [[445, 446]])
        image = a.FITSImage(self.raw)
        for points in ([[math.nan, 0]], [[891, 0]], [[0, -1]], [[1, 2, 3]], [[False, 0]], [[0, 0]] * 1025):
            with self.subTest(points=len(points)), self.assertRaises((TypeError, ValueError)):
                a.local_tan_wcs(image, points)

    def test_fixture_report_separates_decoding_astrometry_and_calibration(self):
        report = a.fixture_report()
        self.assertEqual(report["pixel_comparison"]["checked"], 795663)
        self.assertEqual(report["pixel_comparison"]["mismatches"], 0)
        self.assertLess(report["local_tan_comparison"]["max_error_degrees"], 1e-11)
        self.assertGreater(report["full_dss_vs_local_tan"]["max_difference_degrees"], 1e-5)
        self.assertEqual(report["calibration"]["status"], "UNKNOWN")
        self.assertEqual(report["uncertainty"]["status"], "UNKNOWN")
        self.assertEqual(report["full_g3"], "UNKNOWN")
        self.assertFalse(report["flux_claimed"])


if __name__ == "__main__":
    unittest.main()
