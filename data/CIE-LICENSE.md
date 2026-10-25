# CIE 1931 observer data attribution and license

CIE 2019, *Colour-matching functions of CIE 1931 standard colorimetric observer*, International Commission on Illumination (CIE), Vienna, Austria.

- DOI: https://doi.org/10.25039/CIE.DS.xvudnb9b
- Publisher landing page: https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer
- Data download: https://files.cie.co.at/Publications-datasets/CIE_xyz_1931_2deg.csv
- Metadata: https://files.cie.co.at/Publications-datasets/CIE_xyz_1931_2deg.csv_metadata.json
- License as stated in the supplied publisher metadata: **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.
- License terms: https://creativecommons.org/licenses/by-sa/4.0/
- Legal code: https://creativecommons.org/licenses/by-sa/4.0/legalcode

The supplied CSV and JSON are retained without changes. Source CSV SHA-256 is `fa663e3535a7e0763a745993a1f0a192eb0275ac46ad2d1befd7626841e713c1`, which matches the publisher's checksum. It contains 471 rows over 360–830 nm, inclusive, in 1 nm steps.

`src/cie1931.inc` is an adaptation of this dataset, distributed under CC BY-SA 4.0. The modification is a mechanical reformat into C++ double-precision numeric initializers; the wavelength column becomes an implicit 360+index coordinate. This attribution and license applies to the source data and its reformatted table, and is not a claim that CIE endorses Surface.

The program uses the metadata's linear interpolation and zero extrapolation. Its subsequent XYZ-to-RGB matrix, clipping, normalization and display transforms are separately documented observation choices.
