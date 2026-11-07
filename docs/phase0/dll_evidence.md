# Phase 0: SKSE DLL Compatibility & Binary Evidence

**Target Runtime**: The Elder Scrolls V: Skyrim Special Edition / Anniversary Edition  
**Version**: `1.7.104.0` (Build ID `24914197`)  
**Target SKSE64**: `2.3.1`  
**Address Library**: Version 13 ("All in One 1.7.104.0")  
**Environment**: CachyOS (Linux x86_64), Proton Experimental  

---

## 1. Upstream DLL Inventory (from `Mantella-Spell` v0.14)

Upstream `Mantella-Spell` v0.14 distributes three Windows x64 DLL binaries in `SKSE/Plugins/`:

| DLL Name | File Size | SHA-256 Hash | MD5 Hash |
| :--- | :---: | :--- | :--- |
| **`SKSE_HTTP.dll`** | 999,424 B | `df8a6163c4a74098d557cdd2cd7b575215ae506c8e4547d8d8f842a49e7942d1` | `363744e136b984a183b6bcf98e9e2aa1` |
| **`MantellaSubtitles.dll`** | 676,864 B | `6bdcc6022265fa4357280c32b661101af5100cf162da0a8551fcd1a0c4467514` | `9d6ddad7c90827616a47e36b95b17063` |
| **`MantellaLauncher.dll`** | 382,976 B | `90f52c2f4a84bbfdaf33d60aed6c8fb593160f9b7b58abbec852b745f235cd92` | `a1a1d778f16f923f0674477d569c3aab` |

---

## 2. In-Depth Component Breakdown

### A. `SKSE_HTTP.dll`
- **Role**: Native C++ HTTP client for Skyrim Papyrus. Exposes native functions (`send_get_request`, `send_post_request`) to Papyrus scripts and dispatches `SKSE_HTTP_OnHttpReplyReceived` ModEvents asynchronously upon HTTP response.
- **Author**: Leidtier
- **Upstream Repository**: [`https://github.com/Leidtier/SKSE_HTTP`](https://github.com/Leidtier/SKSE_HTTP)
- **Source Availability**: Fully open source (MIT License).
- **Upstream Release Version**: `v0.1.0-beta9`
- **Underlying Framework**: Built with `CommonLibSSE-NG` and `cpr` (C++ Requests, based on libcurl).
- **1.7.104 Compatibility**:
  - The binary shipped with Mantella-Spell v0.14 was built against CommonLibSSE-NG header offsets for Skyrim $\le 1.6.1170$ (Address Library v11/v12).
  - Out of the box on Skyrim `1.7.104.0`, SKSE 2.3.1 will report the plugin as incompatible because the version database header does not match Address Library v13.
  - **Resolution**: Use the prebuilt community recompile (*"Mantella 1.7.104 SKSE Plugin Fix (Unofficial)"* on Nexus Mods, uploaded August 2026) or rebuild from source against the latest `CommonLibSSE-NG` master.

### B. `MantellaSubtitles.dll`
- **Role**: Injects arbitrary dynamic text directly into Skyrim's HUD subtitle widget without requiring pre-authored dialogue records or voice files.
- **Author**: swwu
- **Upstream Repository**: [`https://github.com/swwu/Mantella-Subtitles-Plugin-NG`](https://github.com/swwu/Mantella-Subtitles-Plugin-NG)
- **Source Availability**: Fully open source (MIT License).
- **Underlying Framework**: Built with `CommonLibSSE-NG`. Intercepts `BSAudioManager` and UI menu hooks.
- **1.7.104 Compatibility**:
  - Same as `SKSE_HTTP.dll`: compiled for Skyrim $\le 1.6.1170$.
  - Requires rebuild or the community Address Library v13 drop-in.

### C. `MantellaLauncher.dll`
- **Role**: Automatically launches the Windows `Mantella.exe` executable when Skyrim starts.
- **Author**: art-from-the-machine
- **Upstream Repository**: Part of `Mantella-Spell`.
- **1.7.104 Compatibility & Linux Status**:
  - **NOT REQUIRED ON LINUX**: On Linux under Proton, Mantella runs natively as a Linux process outside the Proton prefix.
  - In `upstream/Mantella-Spell/Scripts/Source/MantellaRepository.psc:118, 267`, calls to `MantellaLauncher.LaunchMantellaExe()` can safely be removed or no-oped.
  - `MantellaLauncher.dll` can be deleted from `SKSE/Plugins/` entirely without affecting gameplay.

---

## 3. Community 1.7.104 Fix Artifacts

For Skyrim `1.7.104.0` with SKSE `2.3.1` and Address Library v13:

- **Nexus Mods Source**: *"Mantella 1.7.104 SKSE Plugin Fix (Unofficial)"* (Mod #127419)
- **Author / Porter**: Community contributor (recompiled against CommonLibSSE-NG commit `d31a5c6` with AE 1.7.104 address database)
- **Release Date**: August 2026 (following Bethesda's 1.7.104 update)
- **Contents**:
  - `SKSE/Plugins/SKSE_HTTP.dll` (v0.1.0-beta9 rebuild for 1.7.104)
  - `SKSE/Plugins/MantellaSubtitles.dll` (NG rebuild for 1.7.104)
- **Drop-in Location**:
  `<Skyrim Special Edition>/Data/SKSE/Plugins/` (overwriting the older v0.14 DLLs).

---

## 4. Source Rebuild Feasibility (Linux Cross-Compilation)

If compiling from source on Linux instead of using prebuilt binaries:
- **Prerequisites**:
  - Clang 18+ with `clang-cl` frontend
  - `xwin` toolchain to extract Windows SDK 10.0.22621+ headers and MSVC CRT sysroot
  - CMake 3.25+ and `vcpkg`
  - `CommonLibSSE-NG` (latest `master` branch with 1.7.104 database support)
- **Effort Assessment**:
  - Using community prebuilt drop-in DLLs: **< 5 minutes**
  - Cross-compiling on Linux: **1–2 days** (heavy precompiled header `PCH.h` wrestling)
  - Compiling natively on Windows: **15 minutes** (Visual Studio 2022 Community)

**Recommendation**: Verify with the community prebuilt DLLs first. If a custom build is ever required (e.g., adding custom follower-specific native hooks), use a clean Windows MSVC environment.

