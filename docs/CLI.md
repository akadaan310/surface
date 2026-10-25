# Native host runner and repeatable previews

`build/surface` is a native C++20 headless executable. It calls the same `Session`, `Physics`, original CPU `Renderer`, acoustic reference and Gaia catalogue APIs used by the native project. It produces actual rendered pixels and numerical receipts. It does not embed a browser, WebView, JavaScript runtime or external rendering engine.

Run commands below from the project root. The host runner is a reproducibility and image-export tool; the Android NativeActivity is the touch-driven application.

## Build and verify

```sh
python3 tools/build_native.py
python3 tools/build_native.py --test
```

The driver needs Python's standard library and a C++20 compiler. It defaults to `c++`; `--compiler clang++` or the `CXX` environment variable selects another compiler. It compiles common source modules once with `-O3 -std=c++20 -pthread`, links `build/surface`, and uses the same object files when building tests. Headers and embedded `.inc` changes invalidate the cached objects. It never sets `NDEBUG`, so assertion-based native tests stay active.

`--test` discovers every `tests/test_*.cpp`, builds and executes each, then runs the Python test suite. Compilation subprocesses have 120-second deadlines and test processes have 60-second deadlines. The successful result and captured command outputs are saved in `evidence/headless-build.json`; `evidence/headless-build-attempt.json` tracks the latest attempt separately so a later failure cannot be mistaken for the previous successful build. The completed verification ran nine native test executables, including the gesture-travel regression test, and all fourteen Python supervisor tests.

`python3 tools/build_native.py --render` also produces a 60-frame, 720×1280 deterministic coupled-field PPM at `build/previews/coupled.ppm`, with measurements in `evidence/headless-coupled.json`. It does not require Pillow. Pillow was used only to convert the delivered PPM previews into PNG files, without editing their pixels.

## Draw a repeatable physical-ink example

```sh
build/surface --demo --frames 60 --width 720 --height 1280 \
  --mode 0 --output build/previews/coupled.ppm \
  --save build/previews/demo.surface \
  --audio build/previews/modal.wav \
  --report evidence/headless-coupled.json
```

The default field grid is 128×160, with a fixed deterministic seed. Each frame advances the session by 1/60 second and renders it. `--demo` deposits material along a deterministic smooth curved path using the same `Session::paint` entry point as native input and wakes nearby renderer tracers. Frame count determines the sampling of this demonstration curve. No random external asset or generated illustration is substituted for a solver result.

The renderer keeps its declared observation transforms: streamline integration, radiant color, exposure and trail persistence. The image is an observation of the reduced model, not a photograph or complete physical simulation. Model assumptions are documented in `docs/PHYSICS.md`.

## Observations

| `--mode` | Observation | Report name |
|---:|---|---|
| 0 | Coupled field and material | `coupled` |
| 1 | Magnetic | `magnetic` |
| 2 | Acoustic pressure | `wave` |
| 3 | Thermal | `heat` |
| 4 | Electric | `electric` |
| 5 | Optical | `light` |
| 6 | Observed catalogue directions | `cosmos` |

For the real catalogue projection:

```sh
build/surface --mode 6 --frames 30 --width 720 --height 1280 \
  --output build/previews/cosmos.ppm \
  --report evidence/headless-cosmos.json
```

Mode 6 loads `data/gaia.bin` through its bounded native decoder, projects real source directions through `atlas::projectStars`, and calls `Renderer::renderSky`. `--atlas path/gaia.bin` changes the local asset path. The shipped binary contains 10,000 actual Gaia DR3 sources, with no inferred stellar distances. `--demo` gently changes camera yaw in this mode. The underlying physical field is not stepped during a sky observation.

`projectedStars` in the receipt counts directions on the front hemisphere. Some projections may lie outside the viewport and be clipped by the renderer. The default orthographic view visibly shows a bounded hemisphere; it is not an all-sky image or complete universe. Coordinate conventions, precision, missing values, source hashes and Gaia's CC BY-NC 3.0 IGO terms are in `docs/ATLAS.md`.

## Portable state

```sh
build/surface --load build/previews/demo.surface --frames 1 \
  --width 360 --height 640 --output build/previews/resumed.ppm \
  --report evidence/headless-resumed.json
```

The writer uses `Session::exportFile` when the session API provides it, so the current executable emits the `SURFEXP1` portable envelope. A compile-time fallback to `Session::serialize` supports older compatible session implementations. Loading calls `Session::restore`, which owns schema, digest, finite-value and state admission. Inputs and exported files are capped at 10 MiB. The CLI writes a temporary export before renaming it to the requested path; durable two-slot application checkpoints are handled separately by `CheckpointStore`.

An explicitly supplied `--mode` changes the loaded observation; otherwise the saved observation is retained. The loaded pause flag is also retained. Requested image dimensions affect the raster output, not the restored field dimensions. Renderer tracers are initialized for the new rendering process; portable state preserves the modeled session and view rather than reproducing every accumulated display pixel.

The checked example saved 60 input events at simulation time 1 second, loaded in a fresh process and advanced to 1.01666666667 seconds with input sequence 60 intact. A modified export payload was rejected with `export SHA256 mismatch`. The portable example is 329,819 bytes. These observations are recorded in `evidence/headless-resumed.json` and `evidence/headless-cli-qa.json`.

## Audio reference

`--audio path.wav` writes a three-second, mono, 48 kHz, 16-bit PCM response from the native rectangular-room modal acoustic reference. Demonstration touch positions seed the modal response; without a demonstration, a declared fixed strike is used. This optional file is a decaying response after the accumulated strikes, not a synchronized recording of every frame in the demonstration. Its amplitude mapping is an explicit numerical observation transform, not calibrated speaker output. The actual file header was checked: 144,000 samples, one channel, two bytes per sample.

## Bounds and failures

Each raster dimension is 16–4096 pixels, with at most 4,194,304 pixels total. Frames are 1–10,000. Modes are 0–6. Invalid numbers, unknown arguments, duplicate output paths, oversized imports and malformed sessions return exit code 2 and print the reason to standard error. These failures occur without substituting an apparently successful image.

The CLI uses synchronous stepping for deterministic repeatability. It does not run the asynchronous `EngineService` for its frame loop; the service's FIFO ordering, acknowledged barriers and checkpoint behavior are exercised by `test_engine` in the same native build. Process supervision is a separate component, covered by the fourteen fault-injection tests.

## Measured host results

These are observed measurements from the available native host, **not Android-device frame rates**. They include the first-frame renderer warmup. Frame duration includes input injection, solver advancement and rendering; in cosmos mode it includes projection and sky rendering. Output file I/O is excluded from frame duration and included in total wall time.

| Actual run | Frames | Mean frame ms | Median ms | 95th percentile ms | Total wall ms |
|---|---:|---:|---:|---:|---:|
| Coupled ink, 720×1280, deterministic drawing | 60 | 49.878 | 49.111 | 57.852 | 3033.456 |
| Gaia projection, 720×1280, fixed camera | 30 | 7.885 | 6.630 | 10.565 | 270.244 |

These runs perform different work and should not be treated as interchangeable performance results. Host scheduling affects timings. Reports preserve the actual measured values and dimensions. Device installation, touch input, audio routing and sustained Android performance require their own execution evidence.

`build/previews/coupled.png` and `build/previews/cosmos.png` were visually inspected. The coupled image shows the computed red/cyan field streamlines with the deposited curved stroke; the cosmos image shows the real catalogue projection. Neither contains visible controls, labels, titles or other interface chrome.
