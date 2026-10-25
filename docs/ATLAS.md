# Observed astronomical catalogue

The native catalogue contains **10,000 actual Gaia DR3 sources**, retrieved from the public ESA Gaia Archive on 25 October 2026. It is a bounded bright-source selection, not a complete star catalogue, sky survey, or model of the entire universe. `data/gaia.bin` loads locally and requires no network service.

The source query is preserved exactly in `data/gaia-provenance.json`:

```sql
SELECT TOP 10000 source_id,ref_epoch,ra,dec,parallax,parallax_error,
       phot_g_mean_mag,bp_rp
FROM gaiadr3.gaia_source
WHERE phot_g_mean_mag < 7.5
ORDER BY phot_g_mean_mag ASC
```

The delivered selection spans Gaia G magnitudes 1.731607 to 6.330654. The query selects rows in Gaia DR3; it does not guarantee that every physically brighter star is in Gaia. The source is the [ESA TAP endpoint](https://gea.esac.esa.int/tap-server/tap/sync), following ESA's [programmatic access documentation](https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access).

## Identity and reproducibility

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Original response, `data/gaia-dr3-bright-source.csv` | 1,129,055 | `fda4d14d08e4e44c38193ac67e385ae3cbf4503e33c19736ddfc027a1ff9d96f` |
| Runtime catalogue, `data/gaia.bin` | 560,072 | `f8105fda8968e6f18fb3b6982c688f908fc62826c415c65c492b906b68d804bd` |

Rebuild the native table from the preserved source with `python3 data/import-atlas.py`. The script makes no network request and fails if the expected count, source IDs, coordinates or finite numeric values are invalid. Source IDs remain integers throughout; they are never converted to IEEE-754 floating point. Display them with `std::to_string(star.id)`.

Right ascension and declination are ICRS coordinates in degrees at **Julian epoch J2016.0**. The Gaia archive describes the epoch as a Julian year in TCB. Source parallax and its standard error are in milliarcseconds. See the primary [Gaia DR3 data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html) and [release description](https://www.cosmos.esa.int/web/gaia/dr3).

Coordinates are held in binary64. G magnitude and BP−RP are held in binary32, matching the source column precision; the original decimal text remains in the preserved CSV. Parallax and its standard error are binary64. All 10,000 selected sources have BP−RP. **310 sources lack a parallax and its error**. Missing values use finite zero storage with the corresponding presence flag unset. Zero storage is not a measured zero. Negative measured parallaxes are retained.

No stellar distance is inferred. In particular, this build does not replace missing or uncertain parallax with an invented radius, apply an unqualified inverse-parallax conversion, or label a projected direction cosine as parsecs. Any future distance estimate needs a separately declared statistical method and uncertainties.

## Native API and camera

`include/surface/atlas.hpp` exposes `loadCatalogue(span<const uint8_t>)`, `equatorialToCartesian(raDeg, decDeg, distance)` and `projectStars(stars, yaw, pitch, zoom, width, height, maxMagnitude)`.

The Cartesian basis is:

\[
(x,y,z)=r(\cos\delta\cos\alpha,\cos\delta\sin\alpha,\sin\delta).
\]

Positive X points to RA 0°, Dec 0°; positive Y to RA 90°, Dec 0°; positive Z to the north celestial pole. Caller-supplied `distance` supplies the length unit. The display uses a unit sphere because these records have no adopted physical distance.

Camera yaw and pitch are radians. Zero yaw/pitch faces RA 0°, Dec 0°. The projection is orthographic, north upward and increasing RA to the right, with circle radius `min(width,height) * 0.5 * zoom`. Only the facing hemisphere is returned. `ProjectedStar.depth` is a camera direction cosine in [0,1]. The renderer may clip pixels outside the viewport. Halos, hue mapping, size and brightness compression are display transforms, not calibrated spectra or measured stellar sizes.

The loader accepts at most 20,000 records and validates exact file length, version, reserved fields, CRC32, IDs, duplicates, finite measurements, coordinate ranges and missing-value flags. The packaged table contains exactly 10,000. Payload CRC32 detects accidental runtime corruption; the full-file SHA-256 in the receipt identifies the distributed asset. These checks do not authenticate an author.

## Binary layout, version 1

Every integer and floating-point word is little endian. Reading uses explicit byte assembly and `std::bit_cast`, never reinterpretation of a packed native structure, so host padding and alignment cannot alter the format.

| Header byte offset | Storage | Meaning |
|---:|---|---|
| 0 | 8 bytes | ASCII `SGAIA001` |
| 8 | u32 | Schema version, 1 |
| 12 | u32 | Header byte count, 72 |
| 16 | u32 | Record byte count, 56 |
| 20 | u32 | Source count, 10,000 |
| 24 | f64 | Julian epoch, 2016.0 |
| 32 | 32 bytes | SHA-256 of original CSV |
| 64 | u32 | CRC32 of all record bytes |
| 68 | u32 | Reserved zero |

| Record byte offset | Storage | Meaning |
|---:|---|---|
| 0 | u64 | Gaia DR3 source ID |
| 8 | f64 | RA, degrees |
| 16 | f64 | Declination, degrees |
| 24 | f32 | G magnitude |
| 28 | f32 | BP−RP color index, or flagged absent |
| 32 | f64 | Parallax, mas, or flagged absent |
| 40 | f64 | Parallax standard error, mas, or flagged absent |
| 48 | u32 | Presence flags: 1 color, 2 parallax, 4 error |
| 52 | u32 | Reserved zero |

## Scope and checks

`tests/test_atlas.cpp` checks independent cardinal-direction fixtures; center/north/east/back camera positions; 90° camera rotation; the exact first Gaia source ID and source coordinates; the pinned 10,000-source count; absent parallax; corrupted/truncated bytes; and invalid coordinates/camera bounds.

This build does not propagate proper motion from J2016.0, account for an observer's location, apply aberration or extinction corrections, infer temperature from BP−RP, render a 3D distance survey, ingest billions of records, reproduce FITS/WCS measurements, or perform pulsar timing. The complete original science-commission gates remain separate from this bounded native catalogue test.

## Attribution and terms

Data credit: **ESA/Gaia/DPAC**. This work uses ESA Gaia mission data processed by the Gaia Data Processing and Analysis Consortium. DPAC funding comes from national institutions participating in the Gaia Multilateral Agreement. See ESA's [credits](https://www.cosmos.esa.int/web/gaia-users/credits) and the [Gaia DR3 overview paper](https://doi.org/10.1051/0004-6361/202243940).

ESA's [Gaia data license page](https://www.cosmos.esa.int/web/gaia-users/license), checked on 25 October 2026, specifies [CC BY-NC 3.0 IGO](https://creativecommons.org/licenses/by-nc/3.0/igo/). The dataset retains those terms. The code's licensing does not override the data's noncommercial-use condition. This build does not claim a commercial-use permission.
