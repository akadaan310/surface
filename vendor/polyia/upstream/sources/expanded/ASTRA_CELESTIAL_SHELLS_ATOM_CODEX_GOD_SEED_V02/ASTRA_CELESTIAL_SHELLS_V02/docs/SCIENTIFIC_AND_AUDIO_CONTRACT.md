# Scientific, sound, and graphical contracts — ASTRA 0.2

## Provenance

- Celestial sample: `examples/hipparcos_sample.json`, 20 catalog sky directions, derived from the existing university bright Hipparcos sample (source: d3-celestial; BSD-3-Clause attribution in original project).
- Celestial shell radii, perspective center, synthetic stars, multi-shell galactic visualization, non-Earth destinations: **artistic constructs**.
- Planet markers and ISS: **illustrative**, not orbital ephemerides.
- Audio: locally generated original musical layers based on C-major seven-tone note set; not sound recorded from space or a physically reconstructed spectral emission.
- Samples: `audio_assets/celestial-drift.wav` and `portal-chime.wav`, algorithmically generated original stereo PCM under project authorship. Not sampled from any third-party soundtrack.

## Geometry

ICRS unit vector from right ascension and declination (`ra`,`dec` in degrees): `V=(cos(dec)sin(ra), sin(dec), cos(dec)cos(ra))`. Euler yaw and pitch produce a camera-space direction; finite perspective projection uses `x'=x f/(d-z)` and `y'=y f/(d-z)`, with near-plane validation. This is a visualization transform, not an orbital solver. Multi-shell radii are arbitrary user-interface scales.

The displayed graph edges are derived nearest-neighbor geometry; they do not claim to reproduce astronomical constellations. Scientific stars have HIP IDs and apparent magnitudes. Synthetic starlight must remain identifiable as art.

## Audio

- Web Audio context starts after click; browsers may block sound until a user gesture.
- Seven diatonic frequencies, all tied to independently modulated oscillator phases; lowpass filters, stereo panners, a conservative master gain and a compressor on the final channel.
- Master gain is a controllable **software** volume. No attempt is made to set system-level volume.
- Chimes are gesture-driven and time-bounded. The soundtrack is not calibrated to auditory threshold, loudness standard, target ear SPL, or individual headphone sensitivity. Default input amplitude is deliberately low and should remain configurable.
- Any mapping from temperature, chemical spectral emission or orbital frequency into audible Hz is a **sonification mapping**, not sound carried through interplanetary vacuum. Define and test that mapping before claiming it is scientific.
- Vibrate is a best-effort, user-interaction-triggered feature, absent in unsupported browsers. No real eye position or gaze inference is claimed.

## Real-data roadmap

ESA Gaia DR3 includes roughly 1.8 billion sources; this v0.2 bundle includes only 20 Hipparcos bright-star directions, not Gaia itself. Gaia has uncertainties and parallaxes and needs distance estimation. JPL Horizons can return observer-based directions or state vectors with timestamps and reference centers. Do not label future Mars viewpoint correct without the observer transform. NASA media content can have special usage/endorsement constraints; do not ship downloaded media without an asset-level license review.

## Tests and blockers

Python: 23 inherited ATOM tests pass. Node JS: 14 assertions pass. Browser injected-content plus real HTTP bridge: 16 interaction checks pass on desktop and mobile emulation; no pageerrors. WebGL2 was **unavailable in the test environment**, so no GPU pixels were tested. Localhost navigation in headless Chromium returned `ERR_BLOCKED_BY_ADMINISTRATOR`; screenshots are real Chromium renderings using exact source injected into about:blank, with UI API requests bridged to a real local ATOM HTTP backend. Audio graph initialization and seven voices were verified through browser runtime introspection, not subjective listening or loopback recording. Frame pacing on a physical phone and true stereo localization listening are NOT_RUN.
