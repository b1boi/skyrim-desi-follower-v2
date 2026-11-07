# Phase 0: GitHub Actions Build Plan for SKSE Plugins

**Target DLLs**: `SKSE_HTTP.dll` & `MantellaSubtitles.dll`  
**Target Runtime**: Skyrim Special Edition / Anniversary Edition `1.7.104.0` (Address Library v13)  
**Execution Environment**: GitHub Actions (`windows-latest` runner)  
**Status**: **DRAFT ONLY (DO NOT RUN)** — Activate only if testing confirms the original upstream v0.14 DLLs fail to load under SKSE 2.3.1.

---

## 1. Context & Motivation

If `skse64.log` reports that the prebuilt `SKSE_HTTP.dll` (v0.1.0-beta9) or `MantellaSubtitles.dll` shipped in Mantella-Spell v0.14 fails to load because the plugin header is locked to older runtimes ($\le 1.6.1170$), a clean source rebuild is required.

Both plugins are open-source MIT C++ projects built on **`CommonLibSSE-NG`**. Compiling them on Linux via Clang/xwin cross-compilation is notoriously fragile due to MSVC precompiled header (`PCH.h`) differences and ATL/MFC dependencies. Using a GitHub Actions `windows-latest` runner provides a clean, isolated MSVC environment with all Windows SDK headers and Address Library v13 bindings out of the box in under 10 minutes.

---

## 2. Upstream Repositories & Dependency Pinning

| Component | Repository URL | License | Recommended Branch / Commit | Role |
| :--- | :--- | :---: | :--- | :--- |
| **`SKSE_HTTP`** | [`https://github.com/Leidtier/SKSE_HTTP`](https://github.com/Leidtier/SKSE_HTTP) | MIT | `master` (or tag `v0.1.0-beta9`) | Native HTTP client & dictionary container |
| **`MantellaSubtitles`** | [`https://github.com/swwu/Mantella-Subtitles-Plugin-NG`](https://github.com/swwu/Mantella-Subtitles-Plugin-NG) | MIT | `main` | HUD subtitle rendering |
| **`CommonLibSSE-NG`** | [`https://github.com/CharmedBaryon/CommonLibSSE-NG`](https://github.com/CharmedBaryon/CommonLibSSE-NG) | MIT | `master` (commit `d31a5c6` or newer) | Skyrim SE/AE reverse engineering library supporting Address Library v13 |
| **Address Library** | Database version 13 | Meh321 | Header offset table for `1.7.104.0` | Runtime address resolution |

---

## 3. Toolchain & Build Requirements

- **Runner**: `windows-latest` (Windows Server 2022)
- **Compiler**: Microsoft Visual C++ 2022 (`v143` toolchain, MSVC $\ge 19.38$)
- **Windows SDK**: `10.0.22621.0` or newer
- **C++ Standard**: C++20 (`/std:c++20`)
- **CMake**: 3.25+ (pre-installed on runner)
- **Build System**: Ninja or MSBuild
- **Package Manager**: `vcpkg` (for `cpr` and `libcurl` in `SKSE_HTTP`)

---

## 4. Draft GitHub Actions Workflow

Below is the complete standalone GitHub Actions workflow file. To activate, save this file to `.github/workflows/build_skse_plugins.yml` and trigger via `workflow_dispatch`:

```yaml
name: Build SKSE Plugins for Skyrim 1.7.104

on:
  workflow_dispatch:
    inputs:
      commonlib_ref:
        description: 'CommonLibSSE-NG ref/branch'
        required: true
        default: 'master'

jobs:
  build-skse-http:
    name: Build SKSE_HTTP.dll
    runs-on: windows-latest

    steps:
      - name: Checkout SKSE_HTTP
        uses: actions/checkout@v4
        with:
          repository: 'Leidtier/SKSE_HTTP'
          submodules: 'recursive'
          path: 'SKSE_HTTP'

      - name: Set up MSVC Developer Command Prompt
        uses: ilammy/msvc-dev-cmd@v1
        with:
          arch: 'x64'

      - name: Setup Ninja
        uses: ashley-tauro/ninja-build-action@v1.0.0

      - name: Update CommonLibSSE-NG submodule
        shell: pwsh
        run: |
          cd SKSE_HTTP/extern/CommonLibSSE-NG
          git checkout ${{ github.event.inputs.commonlib_ref }}
          git pull origin ${{ github.event.inputs.commonlib_ref }}

      - name: Configure CMake
        shell: pwsh
        run: |
          cmake -B SKSE_HTTP/build `
                -S SKSE_HTTP `
                -G "Visual Studio 17 2022" `
                -A x64 `
                -DCMAKE_BUILD_TYPE=Release `
                -DENABLE_SKYRIM_AE=ON `
                -DENABLE_SKYRIM_SE=ON

      - name: Build SKSE_HTTP
        shell: pwsh
        run: |
          cmake --build SKSE_HTTP/build --config Release --target SKSE_HTTP

      - name: Upload SKSE_HTTP Artifact
        uses: actions/upload-artifact@v4
        with:
          name: SKSE_HTTP_1.7.104
          path: SKSE_HTTP/build/Release/SKSE_HTTP.dll

  build-mantella-subtitles:
    name: Build MantellaSubtitles.dll
    runs-on: windows-latest

    steps:
      - name: Checkout Mantella-Subtitles-Plugin-NG
        uses: actions/checkout@v4
        with:
          repository: 'swwu/Mantella-Subtitles-Plugin-NG'
          submodules: 'recursive'
          path: 'MantellaSubtitles'

      - name: Set up MSVC Developer Command Prompt
        uses: ilammy/msvc-dev-cmd@v1
        with:
          arch: 'x64'

      - name: Update CommonLibSSE-NG submodule
        shell: pwsh
        run: |
          cd MantellaSubtitles/extern/CommonLibSSE-NG
          git checkout ${{ github.event.inputs.commonlib_ref }}
          git pull origin ${{ github.event.inputs.commonlib_ref }}

      - name: Configure CMake
        shell: pwsh
        run: |
          cmake -B MantellaSubtitles/build `
                -S MantellaSubtitles `
                -G "Visual Studio 17 2022" `
                -A x64 `
                -DCMAKE_BUILD_TYPE=Release

      - name: Build MantellaSubtitles
        shell: pwsh
        run: |
          cmake --build MantellaSubtitles/build --config Release

      - name: Upload MantellaSubtitles Artifact
        uses: actions/upload-artifact@v4
        with:
          name: MantellaSubtitles_1.7.104
          path: MantellaSubtitles/build/Release/MantellaSubtitles.dll
```

---

## 5. Artifact Verification & In-Game Deployment Procedure

Once GitHub Actions finishes building:

1. **Download Artifacts**: Download `SKSE_HTTP_1.7.104.zip` and `MantellaSubtitles_1.7.104.zip` from the GitHub Actions run summary.
2. **Compute Hashes**:
   ```bash
   sha256sum SKSE_HTTP.dll MantellaSubtitles.dll
   ```
   Record hashes in `docs/phase0/dll_evidence.md`.
3. **Deploy to Skyrim Data Directory**:
   Copy the newly compiled DLLs into:
   ```bash
   <Skyrim Special Edition>/Data/SKSE/Plugins/
   ```
   (replacing the older v0.14 versions).
4. **Inspect `skse64.log`**:
   Launch Skyrim via SKSE64 under Proton and confirm both plugins load with status `loaded successfully`.
