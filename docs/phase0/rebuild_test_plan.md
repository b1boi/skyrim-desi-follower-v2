# Phase 0: SKSE Rebuild Artifact Deployment & In-Game Test Plan

**Target Mod**: `Mantella DLL test` (in Mod Organizer 2)  
**Target Runtime**: Skyrim Special Edition / Anniversary Edition `1.7.104.0`  
**Target Extender**: SKSE64 `2.3.1`  
**Target Address Library**: Version 13 ("All in One 1.7.104.0", Nexus Mods #32444)  
**Platform**: CachyOS (Linux x86_64), Proton Experimental, Mod Organizer 2  

This test plan provides step-by-step instructions to verify the rebuilt DLL artifacts produced by the GitHub Actions workflow (`.github/workflows/build.yml`), deploy them into MO2, launch under Proton, and inspect `skse64.log` for pass/fail confirmation.

---

## Step 1: Download Artifacts from GitHub Actions

1. In your web browser, navigate to your repository's GitHub Actions page:
   `https://github.com/b1boi/skyrim-desi-follower-v2/actions`
2. Click on the completed workflow run titled **"Build SKSE Plugins (Option A)"**.
3. Under the **Artifacts** section at the bottom of the summary, download both zip packages:
   - `SKSE_HTTP-sarkaar.zip`
   - `MantellaSubtitles-sarkaar.zip`
4. Extract the contents of both zip archives into a local directory (e.g., `~/Downloads/skse_rebuild/`). Each archive contains:
   - The compiled `.dll`
   - The matching `.dll.sha256` checksum file

---

## Step 2: Verify Cryptographic SHA-256 Hashes

Open a terminal on your Linux host and run:

```bash
cd ~/Downloads/skse_rebuild/

# Verify SKSE_HTTP
sha256sum -c SKSE_HTTP.dll.sha256

# Verify MantellaSubtitles
sha256sum -c MantellaSubtitles.dll.sha256
```

### Pass Criteria for Hashes:
- Terminal output must print:
  ```text
  SKSE_HTTP.dll: OK
  MantellaSubtitles.dll: OK
  ```
- If a hash check fails, do NOT deploy the binary; re-download the artifact or inspect the CI build log.

---

## Step 3: Deploy to MO2 Mod "Mantella DLL test"

1. Open **Mod Organizer 2** (running under Proton / Wine).
2. In the left-hand mod list, locate the mod named:
   **`Mantella DLL test`**
3. Right-click **`Mantella DLL test`** and select **"Open in Explorer"** (or navigate directly to its path in your MO2 `mods/` directory).
4. Navigate into the plugin folder:
   ```text
   <MO2_mods_directory>/Mantella DLL test/SKSE/Plugins/
   ```
5. Copy the verified binaries from `~/Downloads/skse_rebuild/`:
   - Replace `SKSE_HTTP.dll`
   - Replace `MantellaSubtitles.dll`
6. Verify in MO2:
   - `Mantella DLL test` is checked (enabled) in the left panel.
   - `Address Library for SKSE Plugins` (v13 for 1.7.104.0) is enabled.
   - Any older or conflicting Mantella plugin mods are disabled.

---

## Step 4: Launch Skyrim via SKSE under Proton

1. In the top-right launcher dropdown of MO2, select **`SKSE`**.
2. Click **Run**.
3. Observe the game startup sequence.

---

## Step 5: Read and Inspect `skse64.log`

After Skyrim starts (or if it halts), inspect the log file located inside your Proton prefix:

### Log File Path:
```text
<Skyrim_Proton_Prefix>/drive_c/users/steamuser/Documents/My Games/Skyrim Special Edition/SKSE/skse64.log
```
*(Common path: `~/.local/share/Steam/steamapps/compatdata/489830/pfx/drive_c/users/steamuser/Documents/My Games/Skyrim Special Edition/SKSE/skse64.log`)*

### What to Look For in `skse64.log`:
1. **SKSE64 Runtime Header**:
   Confirm SKSE version 2.3.1 is active:
   ```text
   SKSE64 runtime: initialize (version = 2.3.1.0 ...)
   ```
2. **`SKSE_HTTP` Load Status**:
   Search for lines mentioning `SKSE_HTTP`:
   ```text
   checking plugin "<path>/SKSE/Plugins/SKSE_HTTP.dll"
   plugin "<path>/SKSE/Plugins/SKSE_HTTP.dll" - loaded successfully (handle 1)
   ```
   *(or `registering plugin listener for SKSE_HTTP`)*
3. **`MantellaSubtitles` Load Status**:
   Search for lines mentioning `MantellaSubtitles`:
   ```text
   checking plugin "<path>/SKSE/Plugins/MantellaSubtitles.dll"
   plugin "<path>/SKSE/Plugins/MantellaSubtitles.dll" - loaded successfully (handle 2)
   ```

---

## Step 6: Pass / Fail Verification Gate

### PASS Criteria:
1. **No Error Dialog**: Skyrim launches without any SKSE warning popup (specifically: **NO** popup stating `"A DLL plugin has failed to load... must be recompiled for your game version"`).
2. **Log Confirmation**: In `skse64.log`, **both** `SKSE_HTTP.dll` and `MantellaSubtitles.dll` are explicitly reported with status `loaded successfully`.
3. **Main Menu Reached**: The game reaches the Skyrim main menu (Imperial logo and menu options) without crashing to desktop (CTD).

### FAIL Criteria:
- Any popup appears stating the DLL is incompatible or requires recompilation.
- `skse64.log` reports `fatal error occurred during plugin load` or `reported as incompatible during query`.
- Game crashes immediately on startup.

> **Decision Rule**: If the PASS criteria are met, Phase 0 in-game feasibility gate is proven for SKSE 2.3.1. If FAIL criteria are triggered and cannot be resolved within the 1-working-day budget, we immediately switch to **Plan B (Skyrim 1.6.1170 downgrade or mock backend)** for all subsequent follower development.
