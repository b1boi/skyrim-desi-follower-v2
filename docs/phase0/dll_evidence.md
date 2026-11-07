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
- **1.7.104 Compatibility Status (Unverified Hypothesis)**:
  - The binary shipped with Mantella-Spell v0.14 was compiled against `CommonLibSSE-NG` headers when Skyrim $\le 1.6.1170$ was standard.
  - *Hypothesis to verify*: The DLL may either load seamlessly via Address Library v13 ("All in One 1.7.104.0") runtime offset resolution, or SKSE 2.3.1 may reject it during plugin load if the internal version header is bound to earlier runtime versions. This is an unverified hypothesis pending live verification via `skse64.log`.
  - Do not assume a recompile is required until `skse64.log` confirms an incompatible version error.

### B. `MantellaSubtitles.dll`
- **Role**: Injects arbitrary dynamic text directly into Skyrim's HUD subtitle widget without requiring pre-authored dialogue records or voice files.
- **Author**: swwu
- **Upstream Repository**: [`https://github.com/swwu/Mantella-Subtitles-Plugin-NG`](https://github.com/swwu/Mantella-Subtitles-Plugin-NG)
- **Source Availability**: Fully open source (MIT License).
- **Underlying Framework**: Built with `CommonLibSSE-NG`. Intercepts `BSAudioManager` and UI menu hooks.
- **1.7.104 Compatibility Status (Unverified Hypothesis)**:
  - Like `SKSE_HTTP.dll`, compatibility with Skyrim `1.7.104.0` / SKSE 2.3.1 remains an unverified hypothesis. CommonLibSSE-NG plugins that rely on Address Library database IDs often resolve offsets across minor Skyrim versions without code changes, provided the Address Library database supports the runtime and SKSE's compatibility check passes.
  - Live testing with `skse64.log` will establish whether the original binary loads or fails.

### C. `MantellaLauncher.dll`
- **Role**: Automatically launches the Windows `Mantella.exe` executable when Skyrim starts.
- **Author**: art-from-the-machine
- **Upstream Repository**: Part of `Mantella-Spell`.
- **1.7.104 Compatibility & Linux Status**:
  - **NOT REQUIRED ON LINUX**: On Linux under Proton, Mantella runs natively as a Linux process outside the Proton prefix.
  - In `upstream/Mantella-Spell/Scripts/Source/MantellaRepository.psc:118, 267`, calls to `MantellaLauncher.LaunchMantellaExe()` can safely be removed or no-oped.
  - `MantellaLauncher.dll` can be deleted from `SKSE/Plugins/` entirely without affecting gameplay.

---

## 3. Evaluation of Unofficial Fixes

Earlier notes referenced an unconfirmed community fix titled *"Mantella 1.7.104 SKSE Plugin Fix (Unofficial)"*.

- **Verification Status**: **UNVERIFIED / UNPROVEN**
- **Finding**: No verifiable download URL, author identity, cryptographic hash, or public source repository exists for this alleged fix.
- **Policy**: Per Phase 0 rules (no unverified claims, never trust third-party binaries without source and provenance), this fix is **completely removed from recommendations and must not be used or relied upon**.

---

## 4. Rebuild Strategy & Recommendations

If testing reveals that the original upstream DLLs fail to load under SKSE 2.3.1:
- **Primary Fallback**: Build `SKSE_HTTP.dll` and `MantellaSubtitles.dll` directly from their official MIT GitHub repositories using a GitHub Actions `windows-latest` CI runner with MSVC (Visual Studio 2022) against the latest `CommonLibSSE-NG` and Address Library v13 headers (detailed build workflow provided in `docs/phase0/dll_build_plan.md`).
- **Linux Cross-Compilation**: Not recommended. Cross-compiling CommonLibSSE-NG with Clang/xwin on Linux introduces fragile MSVC header and PCH emulation issues. A clean GitHub Actions Windows runner provides a reproducible, auditable binary build in under 10 minutes.

**Action Plan**:
1. Test the original upstream Mantella v0.14 DLLs (`SKSE_HTTP.dll` and `MantellaSubtitles.dll`) in Skyrim 1.7.104 with SKSE 2.3.1 and Address Library v13.
2. Inspect `skse64.log` to determine exact loading behavior.
3. If SKSE loads both DLLs without error, continue without rebuilding.
4. If either DLL fails to load, trigger the GitHub Actions clean build per `docs/phase0/dll_build_plan.md`.

