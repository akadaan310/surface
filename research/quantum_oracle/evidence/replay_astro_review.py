"""Recompute the independently selected 1000-point local-TAN challenge."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from research.quantum_oracle import astro

receipt_path = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).with_name("astro-independent-review.json")
receipt = json.loads(receipt_path.read_text())
for source, expected in receipt["source_sha256"].items():
    if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != expected:
        raise ValueError("review source changed")
image = astro.FITSImage(astro.FIXTURE.read_bytes())
if image.sha256 != receipt["raw_data_sha256"]:
    raise ValueError("review data changed")
rng = np.random.default_rng(receipt["seed"])
points = rng.uniform([0, 0], [890, 892], size=(receipt["points"], 2))
actual = astro.local_tan_wcs(image, points)
reference = WCS(fits.Header({key: image.header[key] for key in astro.TAN_KEYS}))
forward = float(abs(actual - reference.wcs_pix2world(points, 0)).max())
inverse = float(abs(reference.wcs_world2pix(actual, 0) - points).max())
if forward >= receipt["forward_tolerance_degrees"] or inverse >= receipt["inverse_tolerance_pixels"]:
    raise ValueError("independent local TAN challenge failed")
print(json.dumps({"status": "PASS", "forward_error_degrees": forward,
                  "inverse_error_pixels": inverse, "points": receipt["points"]}))
