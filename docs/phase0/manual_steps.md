# Phase 0: Manual Steps & Action Items

This document records the exact manual steps and inputs required from the user during Phase 0.

---

## 1. SKSE Installation & Runtime Compatibility

- **Status**: **ACTION REQUIRED**
- **System Findings**:
  - Skyrim executable: `/home/bepis/.local/share/Steam/steamapps/common/Skyrim Special Edition/SkyrimSE.exe`
  - Version: `1.7.104.0` (Build ID `24914197`)
  - Proton: `Proton - Experimental` (`experimental-11.0-20261027b-x86_64`)
  - No SKSE binaries (`skse64_loader.exe`, `skse64_1_*.dll`) are currently installed in the Skyrim directory.
- **Action for User**:
  - Please confirm or place the appropriate SKSE build in the Skyrim directory:
    - If you are running Skyrim SE 1.6.1170 (or downgraded), provide SKSE64 build 2.2.6.
    - If running the latest Bethesda build (1.7.104.0), provide the corresponding SKSE build.
  - Test launching Skyrim via SKSE under Proton.

---

## 2. Audio Recordings for ASR Benchmark (Task T8)

- **Status**: **BLOCKED PENDING RECORDINGS**
- **Action for User**:
  - Please provide ~20 short audio clips in `tests/asr_audio/` with reference text in `tests/asr_audio/refs.yaml`.
  - Content should mix Hindi, English, and Skyrim proper nouns (e.g., "Whiterun", "Dovahkiin", "Balgruuf", "Dwemer", "Sovngarde").

---

## 3. In-Game Smoke Test Observation (Task T4)

- **Status**: **PENDING T3 & T4 COMPLETION**
- **Pass Criteria to verify in-game**:
  1. SKSE and game-side plugins (`SKSE_HTTP.dll`, `MantellaSubtitles.dll`) load under Proton without crashing.
  2. A dialogue event reaches the native Python backend on `http://127.0.0.1:4999`.
  3. The fixed subtitle appears in-game.
  4. The generated WAV plays in-game on the NPC voice channel.
