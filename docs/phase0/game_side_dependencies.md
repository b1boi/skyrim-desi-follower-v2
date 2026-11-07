# Phase 0: Game-Side Mod & Plugin Dependencies

**Target Runtime**: The Elder Scrolls V: Skyrim Special Edition / Anniversary Edition `1.7.104.0` (Build ID `24914197`)  
**Target SKSE64**: `2.3.1`  
**Address Library**: Version 13 ("All in One 1.7.104.0")  
**Proton Environment**: Linux (CachyOS) host running native Python server, Skyrim running under Proton Experimental  

This document inventories every game-side mod, SKSE plugin DLL, and Papyrus library referenced by upstream Mantella v0.14 (`Mantella-Spell`), including its role, source, version, and compatibility status with Skyrim `1.7.104.0` / SKSE `2.3.1`.

---

## 1. Master Dependency Matrix

| Mod / Component | Required / Optional | Code / Doc Version | Upstream Source | 1.7.104 / SKSE 2.3.1 Status | Verification Evidence / Mechanism |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **SKSE64** | **Required** | `2.3.1` | [Silverlock SKSE](https://skse.silverlock.org/) | **VERIFIED** | Official release supporting Skyrim AE 1.7.104.0. |
| **Address Library for SKSE Plugins** | **Required** | `v13` (1.7.104.0) | [Nexus Mods #32444](https://www.nexusmods.com/skyrimspecialedition/mods/32444) | **VERIFIED** | Specifically authored and published for Skyrim runtime `1.7.104.0` (`bin-1.7.104.0.bin`). |
| **`SKSE_HTTP.dll`** | **Required** | `v0.1.0-beta9` | [Leidtier/SKSE_HTTP](https://github.com/Leidtier/SKSE_HTTP) (MIT) | **UNVERIFIED** | CommonLibSSE-NG plugin. Original binary built for $\le 1.6.1170$. User testing with `skse64.log` will establish if runtime Address Library v13 resolves offsets cleanly or requires recompile. |
| **`MantellaSubtitles.dll`** | **Required** | `NG release` | [swwu/Mantella-Subtitles-Plugin-NG](https://github.com/swwu/Mantella-Subtitles-Plugin-NG) (MIT) | **UNVERIFIED** | CommonLibSSE-NG plugin. Original binary built for $\le 1.6.1170$. User testing with `skse64.log` will establish runtime compatibility. |
| **SkyUI SE** | **Required (for MCM)** | `v5.2SE` | [Nexus Mods #12604](https://www.nexusmods.com/skyrimspecialedition/mods/12604) | **VERIFIED** | Pure Scaleform SWF + Papyrus scripts (`SKI_ConfigBase.psc`). No native C++ DLL; scripts run identically on all Skyrim SE/AE editions. |
| **UIExtensions** | **Required (for Text Input)** | `v1.2.0` | [Nexus Mods #17561](https://www.nexusmods.com/skyrimspecialedition/mods/17561) | **VERIFIED** | Pure Scaleform SWF + Papyrus scripts (`UIExtensions.psc` / `UITextEntryMenu`). Contains no native DLL; completely version-independent across 1.6.x and 1.7.x. |
| **PapyrusUtil** | **Not Required** (Legacy) | `v4.6` | [Nexus Mods #13048](https://www.nexusmods.com/skyrimspecialedition/mods/13048) | **UNVERIFIED** | Commented out in `upstream/Mantella-Spell/skyrimse.ppj:24`. Mantella v0.14 replaced PapyrusUtil dictionaries with `SKSE_HTTP` native dictionary functions. |
| **Spell Perk Item Distributor (SPID)** | **Optional** | `v7.0+` | [Nexus Mods #36869](https://www.nexusmods.com/skyrimspecialedition/mods/36869) | **UNVERIFIED** | Only used to parse `Mantella_DISTR.ini` for third-party followers. Sarkaar Bhaiya will define follower keywords directly in his own ESP/ESL, making SPID unnecessary. |
| **`MantellaLauncher.dll`** | **Omit on Linux** | `v0.14` | [Mantella-SKSE-Launcher](https://github.com/art-from-the-machine/Mantella-SKSE-Launcher) | **NOT NEEDED** | Windows-only launcher intended to start `Mantella.exe`. On Linux, backend runs natively outside Proton. Must be removed from `SKSE/Plugins/`. |

---

## 2. Component Analysis & Inspection

### A. Core Communication: `SKSE_HTTP.dll`
- **Script Interface**: `Scripts/Source/SKSE_HTTP.psc`
- **Native Methods**:
  - `sendLocalhostHttpRequest(int typedDictionaryHandle, int port, string route, int timeout = 0) global native`
  - `createDictionary() global native`
  - `getString(...)`, `setInt(...)`, `setNestedDictionary(...)`, etc.
- **ModEvent Callbacks**:
  - `SKSE_HTTP_OnHttpReplyReceived(int typedDictionaryHandle)`
  - `SKSE_HTTP_OnHttpErrorReceived(int typedDictionaryHandle)`
- **1.7.104 Status**: Shipped with Mantella-Spell v0.14 (`SHA-256: df8a616...`). Built with CommonLibSSE-NG. Unverified whether SKSE 2.3.1 loads it without warning or fails on plugin version handshake. If incompatible, rebuild using GitHub Actions MSVC runner (see `docs/phase0/dll_build_plan.md`).

### B. Dynamic Subtitles: `MantellaSubtitles.dll`
- **Script Interface**: `Scripts/Source/MantellaSubtitles.psc`
- **Native Methods**:
  - `SetSubtitle(string speakerName, string subtitleText) global native`
  - `ClearSubtitle() global native`
- **1.7.104 Status**: Shipped with Mantella-Spell v0.14 (`SHA-256: 6bdcc60...`). CommonLibSSE-NG plugin intercepting HUD menu subtitle display. Unverified until user inspects `skse64.log`.

### C. Menu & Interface: `SkyUI` & `UIExtensions`
- **SkyUI**:
  - Code reference: `Scripts/Source/MantellaMCM.psc:1` (`Scriptname MantellaMCM extends SKI_ConfigBase`).
  - Provides the Mod Configuration Menu in the game pause menu.
  - Since it contains no C++ binary (it is compiled Papyrus bytecode `.pex` and ActionScript `.swf`), it works seamlessly on Skyrim 1.7.104.
- **UIExtensions**:
  - Code reference: `Scripts/Source/MantellaConversation.psc:531-534`:
    ```papyrus
    UIExtensions.InitMenu("UITextEntryMenu")
    UIExtensions.OpenMenu("UITextEntryMenu")
    string result = UIExtensions.GetMenuResultString("UITextEntryMenu")
    ```
  - Provides the text entry box for typing dialogue.
  - Pure Scaleform/Papyrus implementation with zero native binary DLLs. Fully compatible with Skyrim 1.7.104.

### D. Redundant or Windows-Only Components to Exclude
1. **`MantellaLauncher.dll`**:
   - Exclusively designed to call `CreateProcess` on `Mantella.exe` upon Skyrim startup.
   - On Linux under Proton, Mantella is executed natively on the host via `scripts/run_server.sh`.
   - `MantellaLauncher.dll` must be deleted from `<Skyrim Data>/SKSE/Plugins/` to avoid unnecessary Wine subprocess overhead.
2. **`PapyrusUtil`**:
   - Earlier versions of Mantella used `StorageUtil.psc` and `JsonUtil.psc`.
   - Mantella v0.14 has completely replaced external JSON parsing with `SKSE_HTTP` native dictionary functions. PapyrusUtil is not required.
3. **`SPID` (Spell Perk Item Distributor)**:
   - Used only by `Mantella_DISTR.ini` to inject `MantellaSuperFollower` keyword into third-party custom followers (e.g. Inigo, Auri, Lucien).
   - Sarkaar Bhaiya is a dedicated standalone follower with his own form definitions, so SPID distribution is not needed.
