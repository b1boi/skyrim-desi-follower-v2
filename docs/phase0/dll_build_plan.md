# Phase 0: GitHub Actions Build Plan for SKSE Plugins

**Target DLLs**: `SKSE_HTTP.dll` & `MantellaSubtitles.dll`  
**Target Runtime**: Skyrim Special Edition / Anniversary Edition `1.7.104.0` (SKSE64 `2.3.1`, Address Library v13)  
**Execution Environment**: GitHub Actions (`windows-latest` runner)  
**Forks**:  
- `https://github.com/b1boi/SKSE_HTTP_sarkaar` (MIT License)  
- `https://github.com/b1boi/Mantella-Subtitles-Plugin-sarkaar` (MIT License)  
**Status**: **DRAFT ONLY (DO NOT RUN)** — Activate only if testing confirms the original upstream v0.14 DLLs fail to load under SKSE 2.3.1.

---

## 1. Context & Motivation

If `skse64.log` reports that the prebuilt `SKSE_HTTP.dll` (v0.1.0-beta9) or `MantellaSubtitles.dll` shipped in Mantella-Spell v0.14 fails to load because the plugin header is locked to older runtimes ($\le 1.6.1170$), a clean source rebuild is required.

Both plugins are open-source MIT C++ projects built on **`CommonLibSSE-NG`**. Compiling them on Linux via Clang/xwin cross-compilation is notoriously fragile due to MSVC precompiled header (`PCH.h`) differences and ATL/MFC dependencies. Using a GitHub Actions `windows-latest` runner provides a clean, isolated MSVC environment with all Windows SDK headers and Address Library v13 bindings out of the box in under 10 minutes.

---

## 2. Fork Repositories & Dependency Pinning

| Component | Fork Repository URL | License | Upstream Base | Target Scope |
| :--- | :--- | :---: | :--- | :--- |
| **`SKSE_HTTP`** | [`https://github.com/b1boi/SKSE_HTTP_sarkaar`](https://github.com/b1boi/SKSE_HTTP_sarkaar) | MIT | `Leidtier/SKSE_HTTP` | SE+AE multi-runtime HTTP client |
| **`MantellaSubtitles`** | [`https://github.com/b1boi/Mantella-Subtitles-Plugin-sarkaar`](https://github.com/b1boi/Mantella-Subtitles-Plugin-sarkaar) | MIT | `swwu/Mantella-Subtitles-Plugin-NG` | SE+AE HUD subtitle display |
| **`CommonLibSSE-NG`** | [`https://github.com/alandtse/CommonLibSSE-NG`](https://github.com/alandtse/CommonLibSSE-NG) | GPL-3.0+ | Branch `ng` (tracks modern AE point updates) | Address Library dynamic resolution |
| **Address Library** | Database version 13 | Meh321 | Nexus Mods #32444 ("All in One 1.7.104.0") | Runtime address resolution |

---

## 3. Workflow Specifications (`.github/workflows/build.yml`)

The production build workflow is maintained at [`.github/workflows/build.yml`](.github/workflows/build.yml). It adheres to strict reproducibility and security rules:

1. **Trigger**: `workflow_dispatch` only (manual trigger; never triggers automatically on push).
2. **Zero Secrets**: Requires no API keys, tokens, or repository secrets.
3. **Commit SHA Pinning**: All GitHub Actions are pinned to full 40-character commit SHAs:
   - `actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332` (v4.1.7)
   - `ilammy/msvc-dev-cmd@cdc98472f2329188e8d893c5d648b2512f4fa9b4` (v1.13.0)
   - `actions/upload-artifact@0b2256b8c012f0828dc542b3febcab082c67f72b` (v4.3.4)
4. **CommonLibSSE-NG Inspection Step**: Outputs the exact `git rev-parse HEAD` and `git log -1` to the CI console for verifiable build provenance.
5. **Multi-Target Configuration**: Configures `-DENABLE_SKYRIM_SE=ON -DENABLE_SKYRIM_AE=ON -DENABLE_SKYRIM_VR=OFF` (VR target disabled).
6. **Artifact & Hash Packaging**: Calculates SHA-256 checksums on Windows and uploads the compiled DLLs along with their `.sha256` files as workflow artifacts.
