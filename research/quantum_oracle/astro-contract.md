# Bounded real FITS observation adapter, version 1

`astro.py` decodes the preserved Horsehead image from the Astropy data server and compares every primary-image value with the independent Astropy FITS reader. It also implements the image header's explicitly selected local TAN coordinate approximation and compares it with an independently constructed Astropy/WCSLIB model of the same approximation. This is a real observational-data path with bounded acceptance; full Oracle G3 remains UNKNOWN because calibrated photometry, validated uncertainty/PSF and complete observational analysis are absent.

## Source and rights

The exact 1,650,240-byte `data/HorseHead.fits` has SHA-256 `c4bcc0bccbadf1488e4e361c0d8f04255dc344ff401fd4827139b3354eafe863`. Both the STScI Astropy mirror and the Astropy GitHub data mirror returned identical bytes. Acquisition time, response headers, download bounds and the retained source identity are in `data/HorseHead.download.json`; scientific provenance and usage terms are in `data/HorseHead.provenance.json`.

The source is a scanned photographic plate, as documented by the [Astropy tutorial](https://learn.astropy.org/tutorials/FITS-images.html). The retained header identifies STScI/MAST, SERC-ER plate A0JP, UK Schmidt, photographic emulsion IIIaF, filter OG590 and observation date `1990-12-22T13:49:00`. It records `EXPOSURE=65.0` with an exposure-minutes comment. The values are photographic digitization data. A density-to-intensity response is needed before deriving physical brightness; see the [MAST DSS description](https://archive.stsci.edu/missions-and-data/dss--gsc/dss-information). No photon counts, flux, magnitude, calibrated noise, or uncertainty is inferred from the integer values.

The FITS header's copyright attribution is `AAO/ROE`. The [MAST data-use policy](https://archive.stsci.edu/publishing/data-use) permits research, teaching and other nonprofit use of the copyrighted DSS collections with requested acknowledgment; commercial use requires written permission. This fixture is retained for the commissioned scientific research. It is not declared public domain or relicensed as software. The STScI Digitized Sky Surveys and original UK Schmidt/AAO/ROE plate sources are acknowledged; see `data/README.md`.

## Exact byte interpretation

The reader admits immutable `bytes`, at most 4 MiB, with complete 2,880-byte FITS blocks. Its supported primary subset is `SIMPLE=T`, `BITPIX=16`, `NAXIS=2`, positive dimensions with at most one million pixels, unscaled signed integers and no `BLANK` or random-group interpretation. Unsupported scaling, dimensionality or encoding fails explicitly. Header scan is bounded to 360 cards of 80 bytes; it requires a valid END, blank header padding, mandatory keyword order, finite scalar fields and no duplicate valued keywords. Repeated commentary/history cards remain in the original bytes. Quoted strings preserve embedded slashes and escaped single quotes.

These structures follow the [FITS standard](https://fits.gsfc.nasa.gov/fits_standard.html). The complete original source stays in `image.raw`. Headers are immutable mappings and numeric arrays have an immutable bytes owner. The image has shape `(y,x)=(893,891)`, primary data offset 14,400 and 1,591,326 data bytes. For zero-based integer pixel `(x,y)`:

```text
offset = 14400 + 2*(891*y + x)
value = signed big-endian int16(raw[offset:offset+2])
```

The comparison checks all 795,663 values, with zero-tolerance integer equality. Independent `struct.unpack_from('>h', ...)` witnesses retain selected raw offsets/bytes, including asymmetric first-row/first-column controls. Statistics describe digitization values, with no calibrated physical unit. Five selected pixel witnesses plus the complete raw payload make reconstruction inspectable.

The second HDU starts at byte 1,607,040 and occupies 43,200 bytes. Its `er.mask` ASCII table is retained and hashed as opaque extension data. This adapter does not interpret the table as pixel-quality flags or covariance. Extension decoding remains outside the supported primary-image subset.

## Explicit local TAN coordinate map

The original header has both DSS plate coefficients and a WCS labelled as a local approximation. Astropy/WCSLIB processing of the full header chooses a DSS model whose coordinates differ from the local TAN/CD map. Silently comparing different models would give misleading validation.

`local_tan_wcs` therefore names its approximation and consumes only the listed `TAN_KEYS`: two `RA---TAN`/`DEC--TAN` axes, degrees, ICRS, CRPIX/CRVAL and the 2×2 CD matrix. It assumes the conventional 180° native longitude pole and rejects a conflicting declaration. Coordinates are explicitly zero-based pixel centers inside the observed rectangle. At most 1,024 points are admitted; invalid shapes, nonfinite values, Boolean coordinates, unsupported frames/projections/units and singular or ill-conditioned CD matrices reject.

The intermediate plane is `CD @ ([x,y]+1-CRPIX)` in degrees. For its radian values `(xi,eta)` and reference `(alpha0,delta0)`:

```text
d = cos(delta0) - eta*sin(delta0)
alpha = alpha0 + atan2(xi,d)       # reduced to [0,2*pi)
delta = atan2(sin(delta0)+eta*cos(delta0), hypot(d,xi))
```

Four center/corner/fractional points are compared to Astropy/WCSLIB built from exactly the selected TAN keywords, with absolute tolerance `1e-11` degrees. The reference pixel `(445,446)` gives `(85.274970,-2.458265)` degrees. The receipt separately compares the selected map to Astropy's full original-header DSS solution and retains the observed disagreement; this is an approximation difference, not a calibration uncertainty estimate. Independent validation of the full DSS solution remains UNKNOWN. No WCS conversion is presented as proof of the plate's physical positional accuracy.

`DATE-OBS` is retained literally. The source does not supply an admitted time-scale contract here; the adapter does not invent UTC, TDB, barycentric timing or an exposure midpoint. Astropy's automatic DATE-OBS-to-MJD header-fix warning is preserved in the comparison receipt as library behavior, not promoted to a verified observational timing conversion.

## Controls, replay and remaining gates

The test suite was first observed failing because the adapter was absent. It then checks the real image against an independent reader, raw offsets, immutable state, all source-byte preservation, malformed/truncated/oversized headers, duplicate keywords, unsupported encodings, nonfinite values and projection constraints. No test downloads data or sends provider/hardware requests.

```sh
.venv/bin/python -B -m unittest discover -s research/quantum_oracle/tests -p test_astro.py -v
.venv/bin/python -B -c 'import json; from research.quantum_oracle.astro import fixture_report; print(json.dumps(fixture_report(), indent=2))'
```

`fixture_report()` checks the fixture digest before emitting results. Its ACCEPT values apply only to exact decoding of this primary image and numerical agreement for this explicitly selected local coordinate map. The source's original headers/extensions remain intact. The full G3 gate, photometric response, calibrated detector/PSF model, per-pixel uncertainty and covariance, full plate-model validation, physical time-scale analysis, spectra/light-curve pathways and broader observational inference remain open. Passing this fixture does not close G7 or the full V2/V3 release.
