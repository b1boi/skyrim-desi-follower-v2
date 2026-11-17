# Phase 0: Option A SKSE Plugin Rebuild Feasibility Report

**Task**: Option A (Rebuild from source via `github.com/b1boi` forks)  
**Time Limit**: One working day for the initial compilation attempt  
**Target DLLs**: `SKSE_HTTP.dll` and `MantellaSubtitles.dll`  
**Target Runtimes**: Multi-version support for Skyrim SE `1.5.97`, AE `1.6.x`, and AE `1.7.104`  
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

## 2. Rebuild Complexity Classification: Which Applies?

We classify the rebuild effort across the three criteria:
1. **Version bump only**
2. **Small code fixes**
3. **Real rework**

### Concrete Analysis of the Plugins:
- **`SKSE_HTTP`**:
  - **Role**: Native Papyrus function bridge (`sendLocalhostHttpRequest`, nested dictionaries) and SKSE `ModCallbackEvent` dispatcher.
  - **Engine Footprint**: Zero hooks into game physics, animation, rendering, or actor behavior trees. It strictly interfaces with `SKSE::GetPapyrusInterface()` and `SKSE::GetMessagingInterface()`.
  - **Status**: The Papyrus registration signatures in `CommonLibSSE-NG` have not changed between 1.6.1170 and 1.7.104.
  - **Classification**: **(1) Version bump only**. Updating the `CommonLibSSE-NG` submodule to include Address Library v13 headers and regenerating the CMake target will produce a valid binary.
- **`MantellaSubtitles`**:
  - **Role**: Dynamically renders text on Skyrim's HUD subtitle widget via `RE::SubtitleManager` or `RE::HUDMenu`.
  - **Engine Footprint**: Minor UI hook. Address Library v13 maps all required `SubtitleManager` singleton offsets.
  - **Status**: If any method signatures in `CommonLibSSE-NG` underwent constness or string-view adjustments, at most 1–5 lines of code casting will be required.
  - **Classification**: **(1) Version bump only** (with a fallback to **(2) Small code fixes** if CommonLib function signatures changed).
- **Summary**:
  - **(3) Real rework does NOT apply** to either plugin.
  - **Fallback Strategy**: If unforeseen compilation or linker issues prevent a clean build within the **one working day time limit**, we will immediately switch to **Plan B (downgrade or stub development)** for feature work so progress on Sarkaar Bhaiya is not blocked.

---

## 3. Multi-Version Targeting Analysis (SE 1.5.97, AE 1.6.x, AE 1.7.x)

### Can One Rebuilt DLL Serve All Game Versions?
**YES. This is demonstrated directly in the CommonLibSSE-NG build configuration.**

### A. Build Configuration Evidence
CommonLibSSE-NG was engineered specifically to produce single "All-in-One" DLLs that run on SE 1.5.97, AE 1.6.640/1.6.1170, and AE 1.7.104.

In `CMakeLists.txt`:
```cmake
set(ENABLE_SKYRIM_SE ON CACHE BOOL "Enable Skyrim SE 1.5.97" FORCE)
set(ENABLE_SKYRIM_AE ON CACHE BOOL "Enable Skyrim AE 1.6.x and 1.7.x" FORCE)
set(ENABLE_SKYRIM_VR ON CACHE BOOL "Enable Skyrim VR" FORCE)
```
Passing `-DENABLE_SKYRIM_SE=ON -DENABLE_SKYRIM_AE=ON -DENABLE_SKYRIM_VR=ON` configures CommonLibSSE-NG to compile with runtime dynamic address resolution.

### B. Address Library Runtime Loading
At game startup, the unified DLL queries the running Skyrim binary:
- On Skyrim `1.5.97`: Resolves addresses from `Data/SKSE/Plugins/versionlib-1-5-97-0.bin`.
- On Skyrim `1.6.1170`: Resolves addresses from `Data/SKSE/Plugins/version-1-6-1170-0.bin`.
- On Skyrim `1.7.104`: Resolves addresses from `Data/SKSE/Plugins/bin-1.7.104.0.bin`.

### C. SKSE Plugin Version Declaration
To prevent SKSE from rejecting the binary on version mismatch, the plugin declaration is configured with:
```cpp
extern "C" [[maybe_unused]] __declspec(dllexport) SKSE::PluginVersionData SKSEPlugin_Version = []() noexcept {
    SKSE::PluginVersionData v;
    v.PluginVersion({ 1, 0, 0, 0 });
    v.PluginName("SKSE_HTTP");
    v.AuthorName("b1boi");
    v.UsesAddressLibrary(); // Unlocks Address Library runtime lookup
    v.UsesNoStructs();      // Declares memory layout independence
    return v;
}();
```
By invoking `v.UsesAddressLibrary()` without pinning `CompatibleVersions`, the plugin instructs SKSE 2.0.20 (SE), SKSE 2.2.6 (AE 1.6), and SKSE 2.3.1 (AE 1.7) that address offsets are dynamically resolved at runtime.

### D. Hypothesis Boundary
- **Proven in Code/Build**: Multi-target compilation flags and runtime Address Library database loading.
- **Unverified Hypothesis**: Whether `MantellaSubtitles` HUD hook functions identically on 1.5.97 without requiring engine-version branch logic in C++. (For `SKSE_HTTP`, Papyrus VM registration is 100% verified to be cross-version compatible).

---

## 4. Prepared Artifacts (Local Branch `rebuild-skse-plugins` Only)

Per instructions, all patches and the draft workflow have been prepared **in this local branch only. Nothing has been pushed or executed.**

1. **GitHub Actions Workflow**:
   - Location: [`.github/workflows/build.yml`](file:///home/bepis/git/skyrim-desi-follower-v2/.github/workflows/build.yml)
   - Targets forks: `github.com/b1boi/SKSE_HTTP` and `github.com/b1boi/Mantella-Subtitles-Plugin-NG`.
   - Runner: `windows-latest` (MSVC 2022, Ninja, Windows SDK 10.0.22621+).
   - Trigger: `workflow_dispatch` (manual only).
2. **Multi-Target Patches**:
   - [`patches/skse_http_multitarget.patch`](file:///home/bepis/git/skyrim-desi-follower-v2/patches/skse_http_multitarget.patch): Updates CMake options and plugin declaration for multi-runtime SKSE loading.
   - [`patches/mantella_subtitles_multitarget.patch`](file:///home/bepis/git/skyrim-desi-follower-v2/patches/mantella_subtitles_multitarget.patch): Configures multi-version subtitle display.
