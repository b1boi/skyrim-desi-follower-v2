# Phase 0: Option A SKSE Plugin Rebuild Feasibility Report

**Task**: Option A (Rebuild from source via `github.com/b1boi` forks)  
**Time Limit**: One working day for the initial compilation attempt  
**Target DLLs**: `SKSE_HTTP.dll` and `MantellaSubtitles.dll`  
**Target Runtime**: Skyrim Special Edition / Anniversary Edition `1.7.104.0` (SKSE64 `2.3.1`, Address Library v13)  
**Forks**:  
- `https://github.com/b1boi/SKSE_HTTP_sarkaar` (forked from `Leidtier/SKSE_HTTP`, MIT License)  
- `https://github.com/b1boi/Mantella-Subtitles-Plugin-sarkaar` (forked from `swwu/Mantella-Subtitles-Plugin-NG`, MIT License)  
**Branch**: `rebuild-skse-plugins` (Local only; no builds or pushes executed)  

---

## 1. Upstream Release Date & Provenance Verification

### A. Mantella (art-from-the-machine)
- **Claim**: The last official Mantella release was late April (29 April 2026).
- **GitHub Release Tag**: [`v0.14`](https://github.com/art-from-the-machine/Mantella/releases/tag/v0.14) was tagged and released on **April 21, 2026** (commit `c5449f3` "Update to latest CSV (#717)").
- **Nexus Mods Release**: The packaged mod archive on [Nexus Mods #98163](https://www.nexusmods.com/skyrimspecialedition/mods/98163) was published on **April 28/29, 2026** (depending on timezone).
- **Verification Result**: **VERIFIED**. The claim accurately reflects the final official release window of the Mantella v0.14 suite.

### B. `SKSE_HTTP` (Leidtier)
- **Claim Check**: Was `SKSE_HTTP` also updated or released on 29 April 2026?
- **Finding**: **FALSE / NOT TRUE**.
  - Upstream repository: [`https://github.com/Leidtier/SKSE_HTTP`](https://github.com/Leidtier/SKSE_HTTP).
  - The latest tagged release remains `v0.1.0-beta9`, originally authored and released in late 2023 / early 2024.
  - In `upstream/Mantella-Spell/README.md:13`, the author explicitly notes:
    > *"The latest version of Leidtier's SKSE HTTP plugin can be found here (the version in this repo is out of date)."*
  - The binary shipped inside Mantella-Spell v0.14 was a static freeze of an older build compiled for Skyrim $\le 1.6.1170$. Leidtier did not produce an update for 1.7.104.

### C. `Mantella-Subtitles-Plugin-NG` (swwu)
- **Claim Check**: Was `Mantella-Subtitles-Plugin-NG` updated or released on 29 April 2026?
- **Finding**: **FALSE / NOT TRUE**.
  - Upstream repository: [`https://github.com/swwu/Mantella-Subtitles-Plugin-NG`](https://github.com/swwu/Mantella-Subtitles-Plugin-NG).
  - This project was authored in 2023/2024 as a Next-Gen (NG) adaptation. No release was made in April 2026.
  - Like `SKSE_HTTP.dll`, it was statically bundled into `Mantella-Spell` prior to Bethesda's 1.7.104 release.

---

## 2. CommonLibSSE-NG Dependency & 1.7.104 Support

### A. Identification of CommonLibSSE-NG Lineage
- **Original Upstream (`CharmedBaryon/CommonLibSSE-NG`)**:
  - Ceased active maintenance around Skyrim version 1.6.640 / 1.6.1130 (last tag `v3.3.7`).
  - Does NOT contain support or address offsets for Skyrim `1.7.104`.
- **Active Successor Fork (`alandtse/CommonLibSSE-NG`)**:
  - Repository: [`https://github.com/alandtse/CommonLibSSE-NG`](https://github.com/alandtse/CommonLibSSE-NG)
  - Default Branch: `ng`
  - Actively maintained by the community to track modern AE point updates.
- **Specific 1.7.104 Commit Citation**:
  - We state plainly: **An isolated individual commit hash or release tag explicitly titled "Add 1.7.104" cannot be independently cited from indexed release tags.** The repository tracks AE point releases continuously on the `ng` branch rather than tagging per Skyrim sub-build.
- **How We Determine & Verify a Working Version**:
  1. Inspect the `ng` branch of `alandtse/CommonLibSSE-NG`.
  2. Verify that `include/SKSE/Impl/PluginDeclaration.h` supports `UsesAddressLibrary()` without hardcoded runtime bounds.
  3. In the GitHub Actions workflow, print the exact checked-out commit SHA and log entry (`git rev-parse HEAD` and `git log -1`) to record full build provenance.

### B. Current Fork Pinning vs. Required Changes
1. **`b1boi/SKSE_HTTP_sarkaar`**:
   - *Currently pins*: `extern/CommonLibSSE-NG` pointing to `CharmedBaryon/CommonLibSSE-NG` commit from 2023/2024.
   - *Required change*: Update `.gitmodules` to point to `https://github.com/alandtse/CommonLibSSE-NG.git` on branch `ng`, and configure CMake for SE+AE runtime support.
2. **`b1boi/Mantella-Subtitles-Plugin-sarkaar`**:
   - *Currently pins*: Older `CharmedBaryon` CommonLibSSE-NG submodule.
   - *Required change*: Update `.gitmodules` to point to `alandtse/CommonLibSSE-NG` on branch `ng`.

---

## 3. Rebuild Complexity Classification: Which Applies?

We evaluate the rebuild effort across three categories:
1. Expected to be a version bump, unverified until the first build succeeds
2. Small code fixes
3. Real rework

### Assessment:
- **`SKSE_HTTP`**:
  - Interfaces strictly with `SKSE::GetPapyrusInterface()` and `SKSE::GetMessagingInterface()`.
  - Papyrus registration and ModEvent dispatch APIs have not changed between 1.6.1170 and 1.7.104.
  - **Effort**: **Expected to be a version bump, unverified until the first build succeeds.**
- **`MantellaSubtitles`**:
  - Calls `RE::SubtitleManager` / `RE::HUDMenu` via Address Library IDs.
  - **Effort**: **Expected to be a version bump, unverified until the first build succeeds** (with a fallback to small code fixes if method parameter constness in CommonLib changed).
- **Summary**:
  - Real rework (3) does NOT apply to either plugin.
  - **Time-box Enforcement**: If unexpected compiler/linker errors stall the build past the **one working day limit**, we immediately switch to **Plan B (downgrade to 1.6.1170 or mock backend)** for development only.

---

## 4. Multi-Version Targeting Status & Scope

### Build Configuration:
The build is configured strictly for **SE + AE**; VR has been removed:
```cmake
set(ENABLE_SKYRIM_SE ON CACHE BOOL "Enable Skyrim SE 1.5.97 support" FORCE)
set(ENABLE_SKYRIM_AE ON CACHE BOOL "Enable Skyrim AE 1.6.x and 1.7.x support" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "Disable VR target" FORCE)
```

### Verified Target vs. Multi-Version Hypothesis:
- **Hypothesis**: The claim that a single rebuilt DLL will serve all game versions (SE 1.5.97, AE 1.6.x, AE 1.7.x) via Address Library is an **unverified hypothesis**.
- **Only Verified Target**: **Skyrim AE `1.7.104.0`** is the only game version present in our test environment and the **only target that will be tested and verified** in Phase 0. Older game versions will remain untested and unverified.

---

## 5. Local Branch Artifacts (`rebuild-skse-plugins` Only)

All workflow and patch files are prepared strictly in local branch `rebuild-skse-plugins`. Nothing has been pushed or executed.

1. **GitHub Actions Workflow**: [`.github/workflows/build.yml`](.github/workflows/build.yml)
   - Targets `b1boi/SKSE_HTTP_sarkaar` and `b1boi/Mantella-Subtitles-Plugin-sarkaar`.
   - `workflow_dispatch` only, zero secrets, all actions pinned by full 40-character commit SHA.
   - Outputs compiled DLLs and SHA-256 hash files as artifacts.
   - Logs the exact CommonLibSSE-NG commit SHA used in the build.
2. **Patches**:
   - [`patches/skse_http_multitarget.patch`](patches/skse_http_multitarget.patch)
   - [`patches/mantella_subtitles_multitarget.patch`](patches/mantella_subtitles_multitarget.patch)
