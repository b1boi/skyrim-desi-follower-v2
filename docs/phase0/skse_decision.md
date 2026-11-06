# Phase 0: SKSE & Runtime 1.7.104 Compatibility Assessment

**Date**: 2026-11-07  
**Target Skyrim Version**: `1.7.104.0` (Anniversary Edition, Build ID `24914197`)  
**Target SKSE Version**: SKSE64 `2.3.1`  
**Address Library**: Version 13 ("All in One 1.7.104.0")  

---

## 1. Upstream Mantella 1.7.104 Compatibility Check

### Status of Upstream Repositories
- **Mantella (`art-from-the-machine/Mantella`)**:
  - Latest release: `v0.14` (our pinned tag).
  - Upstream `v0.14` pre-dates Skyrim 1.7.104. The DLLs shipped in `Mantella-Spell/SKSE/Plugins` (`SKSE_HTTP.dll`, `MantellaSubtitles.dll`, `MantellaDialogue.dll`, `MantellaLauncher.dll`) were compiled against CommonLibSSE-NG for Skyrim $\le 1.6.1170$ (Address Library v11/v12).
  - Out of the box, upstream Mantella `v0.14` binaries will fail on Skyrim 1.7.104 with a fatal SKSE popup:
    `"plugin incompatible, must be recompiled for new address library"`.
- **`Leidtier/SKSE_HTTP`**:
  - Latest release tag: `v0.1.0-beta9`.
  - Built with `CommonLibSSE-NG`. The binary in Mantella-Spell v0.14 has older version headers.
- **`swwu/Mantella-Subtitles-Plugin-NG`**:
  - Main branch is active with CommonLibSSE-NG support.
- **Community Resolution**:
  - An unofficial community release on Nexus Mods (*"Mantella 1.7.104 SKSE Plugin Fix (Unofficial)"*) provides rebuilt versions of `SKSE_HTTP.dll` and `MantellaSubtitles.dll` compiled against CommonLibSSE-NG with Address Library v13 support.
  - Applying these drop-in DLLs (or compiling from source) allows Mantella to run on Skyrim 1.7.104 without downgrade.

### Rebuilding the DLLs for 1.7.104 (If Needed)
- **Toolchain Required**:
  - C++23 compatible compiler: MSVC v143 (Visual Studio 2022) or `clang-cl`.
  - CMake 3.21+.
  - `vcpkg` package manager with `commonlibsse-ng` (latest master), `cpr`, and `nlohmann-json`.
- **Can it be cross-compiled on Linux?**
  - **Theoretically yes, practically high-friction**: CommonLibSSE-NG uses heavy MSVC-specific precompiled headers (`PCH.h`), Windows SDK COM interfaces, and MSVC SEH exceptions. Cross-compiling on Linux requires `clang` with MSVC sysroot headers extracted via `xwin`.
  - **Estimated Effort**:
    - Using prebuilt community fix DLLs: **< 5 minutes** (drop-in replacement of `SKSE_HTTP.dll` and `MantellaSubtitles.dll`).
    - Cross-compiling on Linux: **1–2 days** of toolchain wrestling.
    - Compiling in Windows VM / dual-boot: **~15 minutes**.
  - **Recommendation**: Use the community prebuilt 1.7.104 drop-in DLLs or provide the updated binaries directly.

---

## 2. Launching SKSE Under Proton from Steam

Skyrim is launched through Proton Experimental on CachyOS. SKSE requires launching `skse64_loader.exe` instead of `SkyrimSELauncher.exe` or `SkyrimSE.exe`.

### Method 1: Steam Launch Options Wrapper (Recommended, Non-Destructive)
In Steam $\rightarrow$ Right-click *The Elder Scrolls V: Skyrim Special Edition* $\rightarrow$ **Properties** $\rightarrow$ **General** $\rightarrow$ **Launch Options**:

```bash
echo "%command%" | sed "s/SkyrimSE.exe/skse64_loader.exe/" | sh
```

- **Status**: Untested on this prefix until SKSE install is complete.
- **How it works**: Steam normally executes `proton waitforexitandrun SkyrimSE.exe`. The `sed` substitution swaps the target binary to `skse64_loader.exe`, preserving all Proton environment variables, prefix paths, and steam overlay hooks.

### Method 2: Executable Swap / Renaming (Fallback)
If Steam Launch Options fail:
1. In `/home/bepis/.local/share/Steam/steamapps/common/Skyrim Special Edition/`:
   ```bash
   mv SkyrimSELauncher.exe SkyrimSELauncher.exe.bak
   cp skse64_loader.exe SkyrimSELauncher.exe
   ```
2. When launching the game from Steam, Steam executes `SkyrimSELauncher.exe`, which is actually `skse64_loader.exe`.

---

## 3. How to Read `skse64.log` and What to Look For

### Log Location Inside Prefix
Inside the Proton compatdata prefix:
```text
/home/bepis/.local/share/Steam/steamapps/compatdata/489830/pfx/drive_c/users/steamuser/Documents/My Games/Skyrim Special Edition/SKSE/
```
Key log files:
- `skse64.log`: SKSE core runtime log.
- `SKSE_HTTP.log`: HTTP client plugin log.
- `MantellaSubtitles.log`: Subtitle injector log.

### What to Look For in `skse64.log`
1. **Core SKSE Initialization**:
   ```text
   SKSE64 runtime: initialize (version = 2.3.1 ... runtime = 1.7.104.0)
   ```
   *Failure symptom*: `unsupported runtime version`.
2. **Address Library Resolution**:
   ```text
   loaded address library successfully
   found database for 1.7.104.0
   ```
   *Failure symptom*: `could not find version database file for runtime 1.7.104.0`.
3. **Plugin Validation & Loading**:
   ```text
   checking plugin SKSE_HTTP.dll
   plugin SKSE_HTTP.dll (00000001 ...) reported as compatible
   checking plugin MantellaSubtitles.dll
   plugin MantellaSubtitles.dll (00000001 ...) reported as compatible
   ```
   *Failure symptom*:
   `plugin SKSE_HTTP.dll is disabled, incompatible with current version of the game`.

---

## 4. Downgrade Fallback Plan (Skyrim 1.6.1170)

> [!WARNING]
> This is a contingency reference only. Do not perform this unless runtime 1.7.104 is completely unworkable.

If Address Library v13 or SKSE 2.3.1 fails to load the necessary DLLs:

### Steps to Downgrade:
1. **Download Depots via Steam Console**:
   Open Steam console (`steam://open/console` in browser or `steam -console` in terminal):
   ```text
   download_depot 489830 489831 4940892828028256588
   download_depot 489830 489832 5728778377666085157
   download_depot 489830 489833 4886117324142477814
   ```
   (Depot 489833 contains the 1.6.1170 `SkyrimSE.exe` binary).
2. **Copy Overwrite**: Replace `SkyrimSE.exe` and data files in the Skyrim directory with the downloaded depot files.
3. **Install SKSE 2.2.6**: Install SKSE64 2.2.6 (built for 1.6.1170) and Address Library v11.
4. **Prevent Automatic Steam Updates**:
   - In Steam game properties, set Updates to: *"Only update this game when I launch it"*.
   - Make the appmanifest read-only to prevent Steam from queuing updates:
     ```bash
     chmod 444 /home/bepis/.local/share/Steam/steamapps/appmanifest_489830.acf
     ```
   - Only launch Skyrim via `skse64_loader.exe`, never through the standard Steam Play button.
