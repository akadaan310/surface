"""Bounded photographic FITS decoding and an explicitly selected local TAN map.

Raw signed integer decoding uses the FITS byte contract, independently checked
against Astropy. The local TAN approximation is not the full DSS plate model.
"""
from dataclasses import dataclass
import hashlib
import io
import math
import numbers
from pathlib import Path
import re
import struct
from types import MappingProxyType
import warnings

import numpy as np

MAX_BYTES = 4 * 1024 * 1024
MAX_PIXELS = 1_000_000
MAX_CARDS = 360
MAX_WCS_POINTS = 1024
FIXTURE = Path(__file__).with_name("data") / "HorseHead.fits"
FIXTURE_SHA256 = "c4bcc0bccbadf1488e4e361c0d8f04255dc344ff401fd4827139b3354eafe863"
TAN_KEYS = ("WCSAXES", "CTYPE1", "CTYPE2", "CUNIT1", "CUNIT2", "CRPIX1", "CRPIX2",
            "CRVAL1", "CRVAL2", "CD1_1", "CD1_2", "CD2_1", "CD2_2", "RADESYS")


def _number(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise ValueError("finite real number required")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("number outside binary64 range") from exc
    if not math.isfinite(result):
        raise ValueError("nonfinite number")
    return result


def _card_value(text):
    text = text.lstrip()
    if text.startswith("'"):
        result = ""
        i = 1
        while i < len(text):
            if text[i] == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    result += "'"
                    i += 2
                    continue
                remainder = text[i + 1:].lstrip()
                if remainder and not remainder.startswith("/"):
                    raise ValueError("invalid FITS string suffix")
                return result.rstrip()
            result += text[i]
            i += 1
        raise ValueError("unterminated FITS string")
    token = text.split("/", 1)[0].strip()
    if token in ("T", "F"):
        return token == "T"
    if re.fullmatch(r"[+-]?\d+", token):
        return int(token)
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[ED][+-]?\d+)?", token):
        value = float(token.replace("D", "E"))
        if math.isfinite(value):
            return value
    raise ValueError("unsupported or nonfinite FITS card value")


@dataclass(frozen=True, init=False)
class FITSImage:
    raw: bytes
    header: object
    card_offsets: object
    shape: tuple
    data_offset: int
    extension_offset: int
    sha256: str

    def __init__(self, raw):
        if type(raw) is not bytes:
            raise TypeError("immutable bytes required")
        if not 2880 <= len(raw) <= MAX_BYTES or len(raw) % 2880:
            raise ValueError("bounded complete FITS blocks required")
        header, offsets = {}, {}
        end = None
        for offset in range(0, min(len(raw), MAX_CARDS * 80), 80):
            try:
                card = raw[offset:offset + 80].decode("ascii")
            except UnicodeDecodeError as exc:
                raise ValueError("non-ASCII FITS header") from exc
            if any(ord(c) < 32 or ord(c) > 126 for c in card):
                raise ValueError("nonprintable FITS header")
            key = card[:8].strip()
            if key == "END":
                if card[8:].strip():
                    raise ValueError("malformed END card")
                end = offset + 80
                break
            if key in ("COMMENT", "HISTORY", ""):
                continue
            if not re.fullmatch(r"[A-Z0-9_-]{1,8}", key) or card[8:10] != "= ":
                raise ValueError("unsupported FITS keyword card")
            if key in header:
                raise ValueError("duplicate valued FITS keyword")
            header[key] = _card_value(card[10:])
            offsets[key] = offset
        if end is None:
            raise ValueError("END missing within header budget")
        data_offset = ((end + 2879) // 2880) * 2880
        if raw[end:data_offset] != b" " * (data_offset - end):
            raise ValueError("nonblank header padding")
        if list(header)[:5] != ["SIMPLE", "BITPIX", "NAXIS", "NAXIS1", "NAXIS2"]:
            raise ValueError("unsupported primary header order")
        if header["SIMPLE"] is not True or type(header["BITPIX"]) is not int or header["BITPIX"] != 16:
            raise ValueError("only SIMPLE signed int16 primary images are admitted")
        if type(header["NAXIS"]) is not int or header["NAXIS"] != 2:
            raise ValueError("exactly two axes required")
        width, height = header["NAXIS1"], header["NAXIS2"]
        if (type(width) is not int or type(height) is not int or
                not 1 <= width <= MAX_PIXELS or not 1 <= height <= MAX_PIXELS or width * height > MAX_PIXELS):
            raise ValueError("image dimension budget exceeded")
        if (_number(header.get("BSCALE", 1)) != 1 or _number(header.get("BZERO", 0)) != 0 or
                "BLANK" in header or header.get("GROUPS", False) is not False):
            raise ValueError("scaling, blank-mask and random-group semantics are not admitted")
        data_end = data_offset + width * height * 2
        extension_offset = ((data_end + 2879) // 2880) * 2880
        if len(raw) < extension_offset or any(raw[data_end:extension_offset]):
            raise ValueError("truncated primary data or nonzero data padding")
        if len(raw) > extension_offset and header.get("EXTEND") is not True:
            raise ValueError("undeclared trailing extension")
        for key, value in {"raw": raw, "header": MappingProxyType(header),
                           "card_offsets": MappingProxyType(offsets), "shape": (height, width),
                           "data_offset": data_offset, "extension_offset": extension_offset,
                           "sha256": hashlib.sha256(raw).hexdigest()}.items():
            object.__setattr__(self, key, value)

    @property
    def pixels(self):
        return np.frombuffer(self.raw, dtype=">i2", count=math.prod(self.shape), offset=self.data_offset).reshape(self.shape)

    def pixel_witness(self, x, y):
        if type(x) is not int or type(y) is not int or not 0 <= x < self.shape[1] or not 0 <= y < self.shape[0]:
            raise ValueError("bounded zero-based integer x/y pixel required")
        offset = self.data_offset + 2 * (y * self.shape[1] + x)
        return {"source_sha256": self.sha256, "offset": offset, "bytes": 2,
                "dtype": ">i2", "x": x, "y": y, "hex": self.raw[offset:offset + 2].hex(),
                "value": struct.unpack_from(">h", self.raw, offset)[0]}


def local_tan_wcs(image, points):
    """Zero-based pixel centers -> ICRS RA/Dec degrees, selected local TAN only.

    All source DSS coefficients remain retained, but are deliberately not used
    by this named approximation. No claim of calibrated full-DSS accuracy.
    """
    if not isinstance(image, FITSImage):
        raise TypeError("FITSImage required")
    h = image.header
    if any(key not in h for key in TAN_KEYS):
        raise ValueError("complete explicit local TAN metadata required")
    if (type(h["WCSAXES"]) is not int or h["WCSAXES"] != 2 or h["CTYPE1"] != "RA---TAN" or
            h["CTYPE2"] != "DEC--TAN" or h["CUNIT1"] != "deg" or h["CUNIT2"] != "deg" or h["RADESYS"] != "ICRS" or
            h.get("LONPOLE", 180) != 180):
        raise ValueError("unsupported local projection, units, frame or pole convention")
    crpix = [_number(h["CRPIX1"]), _number(h["CRPIX2"])]
    ra0, dec0 = _number(h["CRVAL1"]), _number(h["CRVAL2"])
    cd = np.array([[_number(h["CD1_1"]), _number(h["CD1_2"])],
                   [_number(h["CD2_1"]), _number(h["CD2_2"])]])
    if (not 0 <= ra0 < 360 or not -90 < dec0 < 90 or max(map(abs, crpix)) > 1e6 or
            np.max(abs(cd)) > 1 or not np.isfinite(np.linalg.cond(cd)) or np.linalg.cond(cd) > 1e12):
        raise ValueError("local WCS numeric range or invertibility")
    if not isinstance(points, (list, tuple, np.ndarray)) or not 1 <= len(points) <= MAX_WCS_POINTS:
        raise ValueError("bounded coordinate point list required")
    coordinates = []
    for point in points:
        if not isinstance(point, (list, tuple, np.ndarray)) or len(point) != 2:
            raise ValueError("XY coordinates required")
        x, y = map(_number, point)
        if not 0 <= x <= image.shape[1] - 1 or not 0 <= y <= image.shape[0] - 1:
            raise ValueError("coordinate outside observed image")
        coordinates.append((x, y))
    plane = np.radians((np.asarray(coordinates) + 1 - crpix) @ cd.T)
    alpha, delta = math.radians(ra0), math.radians(dec0)
    xi, eta = plane.T
    denominator = math.cos(delta) - eta * math.sin(delta)
    ra = (alpha + np.arctan2(xi, denominator)) % (2 * math.pi)
    dec = np.arctan2(math.sin(delta) + eta * math.cos(delta), np.hypot(denominator, xi))
    return np.degrees(np.column_stack((ra, dec)))


def fixture_report():
    """Execute independent comparisons on the pinned real image, entirely offline."""
    import astropy
    from astropy.io import fits
    from astropy.wcs import WCS
    if FIXTURE.is_symlink() or not FIXTURE.is_file() or FIXTURE.stat().st_size > MAX_BYTES:
        raise ValueError("missing or unsafe fixture")
    image = FITSImage(FIXTURE.read_bytes())
    if image.sha256 != FIXTURE_SHA256:
        raise ValueError("fixture source identity differs")
    with fits.open(io.BytesIO(image.raw), memmap=False, do_not_scale_image_data=True) as hdus:
        reference = hdus[0].data
        mismatch = int(np.count_nonzero(image.pixels != reference))
        points = np.array([[445, 446], [0, 0], [890, 892], [223.5, 333.25]])
        local_header = fits.Header({key: image.header[key] for key in TAN_KEYS})
        ours = local_tan_wcs(image, points)
        local = WCS(local_header).wcs_pix2world(points, 0)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            full = WCS(hdus[0].header).wcs_pix2world(points, 0)
        differences = np.abs(ours - local)
        full_difference = np.abs(ours - full)
        if mismatch or float(differences.max()) > 1e-11:
            raise ValueError("independent FITS or local TAN comparison failed")
        return {"schema": "quantum-oracle.fits-observation/1", "source_sha256": image.sha256,
                "source_bytes": len(image.raw), "astropy_version": astropy.__version__,
                "input_kind": "real digitized photographic plate", "shape_yx": list(image.shape),
                "data_offset": image.data_offset, "data_bytes": math.prod(image.shape) * 2,
                "pixel_comparison": {"status": "ACCEPT", "checked": math.prod(image.shape), "mismatches": mismatch,
                                     "method": "independent raw big-endian int16 view versus Astropy FITS reader", "tolerance": 0,
                                     "scope": "integer decoding of this source primary image only"},
                "pixel_witnesses": [image.pixel_witness(x, y) for x, y in ((0, 0), (1, 0), (0, 1), (445, 446), (890, 892))],
                "statistics": {"minimum": int(image.pixels.min()), "maximum": int(image.pixels.max()),
                               "mean": float(image.pixels.mean()), "unit": "uncalibrated photographic digitization values"},
                "local_tan_comparison": {"status": "ACCEPT", "points_xy_zero_based": points.tolist(),
                    "coordinates_ra_dec_degrees": ours.tolist(), "max_error_degrees": float(differences.max()),
                    "tolerance_degrees": 1e-11, "selected_keywords": list(TAN_KEYS),
                    "scope": "header local TAN approximation; independent inverse-gnomonic formula versus Astropy/WCSLIB"},
                "full_dss_vs_local_tan": {"max_difference_degrees": float(full_difference.max()),
                    "component_differences_degrees": full_difference.tolist(), "warnings": [str(w.message) for w in caught],
                    "full_dss_independent_validation": "UNKNOWN", "reason": "DSS plate model differs from local approximation"},
                "opaque_extensions": {"offset": image.extension_offset, "bytes": len(image.raw) - image.extension_offset,
                    "sha256": hashlib.sha256(image.raw[image.extension_offset:]).hexdigest(),
                    "interpretation": "er.mask table retained byte-exact; not treated as a pixel uncertainty array"},
                "observation": {key: image.header.get(key) for key in ("ORIGIN", "SURVEY", "PLATEID", "INSTRUME", "DATE-OBS", "EXPOSURE", "COPYRGHT")},
                "time_scale": "UNKNOWN; DATE-OBS retained without invented time-scale/barycentric conversion",
                "calibration": {"status": "UNKNOWN", "reason": "No density-to-intensity/flux response or calibrated PSF supplied"},
                "uncertainty": {"status": "UNKNOWN", "reason": "No validated per-pixel uncertainty/covariance model supplied"},
                "flux_claimed": False, "full_g3": "UNKNOWN", "source_reconstruction": "image.raw retains every original byte"}
