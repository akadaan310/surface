# Native Surface Implementation Plan

> **For agentic workers:** Execute bounded independent components; root integrates and publishes. The user authorized direct implementation.

**Goal:** Usable native full-screen Surface with an original renderer and recoverable scientific state.

**Architecture:** Dependency-free C++20 computational and pixel engine; thin Android NativeActivity adapter; independent Python development supervisor; versioned native binary records.

**Tech Stack:** C++20, Android NDK, ANativeWindow, AAudio, standard Linux C++ toolchain, Python stdlib, APK packaging tools.

**Spec:** `docs/superpowers/specs/2026-10-25-native-surface.md`

## Constraints
- No web runtime or third-party rendering engine in Surface.
- Never overwrite original archive bytes or infer scientific passes from screenshots.
- Fixed budgets, checked array dimensions, exact source IDs, explicit units and domain limits.
- No persistent visible UI. System navigation remains usable.

## Review focus
- Malformed checkpoint size/dimension/NaN and stale generation publication.
- App pause/rotation/window recreation without discarded state or runaway catchup.
- Out-of-range touch and astronomy projection at poles/seams.
- Cross-target little-endian serialization, exact IDs and numerical differences.
- Missing Android runtime evidence is reported rather than silently inferred from a successful build.

## Tasks
1. Preserve inventory, all supplied hashes, current source checkpoint, site identity and historical UNKNOWN evidence. Record native override.
2. Port physical kernels and source-labeled spectral operators; tests against independent analytical fixtures. Agent physics owns include/surface/physics.hpp and src/physics.cpp.
3. Port catalogue and PHANTOM adapters, exact-ID/endian/quantum/pulse tests. Agent atlas owns atlas/phantom modules and data receipts.
4. Implement host supervision and native checkpoint store with fault tests. Agent recovery owns tools/supervise.py and checkpoint module.
5. Implement original rasterizer, native app state and headless driver. Root owns renderer/runtime/headless and integration tests.
6. Implement Android platform adapter, native touch and immersive lifecycle, audio; download pinned official toolchain, cross-compile ARM64 and package/sign APK. Root owns Android scripts and adapter.
7. Run integrated tests, checkpoint replay, native rendering QA, measured benchmark and independent review. Preserve actual commands/results and unresolved scientific gates.
8. Commit/push source, package release and publish native download endpoint using preserved Site identity. Return binary/source/recovery links with exact verification boundaries.
