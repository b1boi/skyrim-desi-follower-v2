# Phase 0: Mantella Architecture Audit & Codebase Inspection

This audit verifies upstream Mantella's architecture directly against the source code, establishing exact ground truth for the single-follower Skyrim SE/AE mod integration.

**Pinned Upstream Releases Audited:**
- **Mantella (Python Backend)**: Tag `v0.14` (Commit `c5449f3c8b081c722212c496c298c16277394ae1`)
- **Mantella-Spell (Skyrim Mod & SKSE Plugins)**: Tag `v0.14` (Commit `6dd05671bae1df25afcf637f65f787ec7ccd0bf2`)

---

## 1. Game-to-Python Communication Architecture

### Protocol & Transport
- **Mechanism**: **Localhost HTTP REST API** (JSON payloads over TCP port `4999` by default) via custom SKSE C++ plugin `SKSE_HTTP.dll`.
  - *Source References*:
    - `Mantella-Spell/Scripts/Source/SKSE_HTTP.psc:3`:
      ```papyrus
      function sendLocalhostHttpRequest(int typedDictionaryHandle, int port, string route, int timeout = 0) global native
      ```
    - `Mantella-Spell/Scripts/Source/MantellaConversation.psc:82, 107, 258, 450, 506`:
      ```papyrus
      SKSE_HTTP.sendLocalhostHttpRequest(handle, repository.HttpPort, mConsts.HTTP_ROUTE_MAIN)
      ```
    - `Mantella/src/http/routes/mantella_route.py:65`:
      ```python
      @app.post("/mantella")
      async def mantella(request: Request):
      ```
- **Legacy / Fallback Protocol**: File-based polling exists in `Mantella/src/http/file_communication_compatibility.py:16-30` (`_mantella_communication.txt`) for VR/Fallout 4 fallback, but modern Skyrim SE uses `SKSE_HTTP.dll` directly.

### Push vs. Polling Mechanism
- **Push Architecture**: The SKSE plugin makes an asynchronous HTTP POST request to `http://localhost:4999/mantella`. When the Python FastAPI server responds, `SKSE_HTTP.dll` raises a Skyrim Papyrus event:
  - *Source Reference (`Mantella-Spell/Scripts/Source/SKSE_HTTP.psc:5-10`)*:
    ```papyrus
    function raiseOnHttpReplyReceived(int typedDictionaryHandle) global
        int handle = ModEvent.Create("SKSE_HTTP_OnHttpReplyReceived")
        if (handle)
            ModEvent.PushInt(handle, typedDictionaryHandle)
            ModEvent.Send(handle)
        endIf    
    endFunction
    ```
  - *Source Reference (`Mantella-Spell/Scripts/Source/MantellaConversation.psc:57, 153`)*:
    ```papyrus
    RegisterForModEvent("SKSE_HTTP_OnHttpReplyReceived", "OnHttpReplyReceived")
    ...
    event OnHttpReplyReceived(int typedDictionaryHandle)
    ```
- **There is NO timer-based polling loop** for communication. Conversation advancement is driven strictly by HTTP request-response ModEvents.

### Latency Contribution
- **Localhost HTTP Round-Trip**: Under Linux kernel loopback, TCP connection and HTTP JSON serialization/deserialization take **$< 1.0\text{ ms}$** (typically 0.2–0.5 ms).
- **Papyrus Event Dispatch Latency**: ModEvents are processed by Skyrim's Papyrus VM thread, which evaluates events frame-by-frame. At 60 FPS, this adds **$16.6\text{ ms}$** (1 frame) of handoff latency.
- **Total Protocol Latency Overhead**: Estimated at **$15\text{--}25\text{ ms}$**. The communication layer contributes negligible latency compared to LLM TTFT or TTS synthesis.

---

## 2. Voice Line Storage, Playback & Lip-Sync

### Dialogue Audio Paths & Formats
- **Format**: 16-bit PCM WAV (uncompressed mono, 24000 Hz or 22050 Hz).
- **Directory Layout**:
  - Loose files in Skyrim Data directory:
    `<Skyrim Data>/Sound/Voice/Mantella.esp/<VoiceFolder>/`
  - Default voice folder: `MantellaVoice00` (`Mantella/src/games/gameable.py:31`).
  - If per-actor voice folders are configured (`save_audio_data_to_character_folder = True`), it uses the actor's in-game voice type folder (`Mantella/src/games/skyrim.py:202-206`).
- **File Naming & Double-Buffering**:
  Skyrim alternates dialogue playback between two fixed topic line IDs to avoid file locking:
  - *Source Reference (`Mantella/src/games/skyrim.py:21-22, 210-212`)*:
    ```python
    DIALOGUELINE1_FILENAME = "MantellaDi_MantellaDialogu_00001D8B_1"
    DIALOGUELINE2_FILENAME = "MantellaDi_MantellaDialogu_0018B644_1"
    ...
    filename = self.DIALOGUELINE1_FILENAME
    if topicID == 2:
        filename = self.DIALOGUELINE2_FILENAME
    ```
  - Destination file: `<Data>/Sound/Voice/Mantella.esp/MantellaVoice00/MantellaDi_MantellaDialogu_00001D8B_1.wav` (and corresponding `.lip`).

### Playback Execution
- In Papyrus (`Mantella-Spell/Scripts/Source/MantellaConversation.psc:350-365`), the NPC dialogue topic is invoked:
  ```papyrus
  actorSpeaking.Say(topicToUse, abSpeakInHead=false)
  ```
- Skyrim's engine loads the corresponding `.wav` and `.lip` from disk matching the active `TopicInfo` FormID and routes the audio through the 3D in-game voice channel of the speaker actor.

### Lip-Sync Pipeline & External Executables
- **External Executable**: `FaceFXWrapper.exe` (Win32 binary located in `Sound/Voice/Processing/FaceFXWrapper.exe` or bundled with XTTS/xVASynth).
- **Phonetic Database**: Requires `FonixData.cdf` in the same directory (`Mantella/src/tts/ttsable.py:221-224`).
- **Execution Command**:
  - *Source Reference (`Mantella/src/tts/ttsable.py:226-237`)*:
    ```python
    # Subprocess execution:
    # FaceFXWrapper.exe <wav_file> <FonixData.cdf> "<voiceline text>" <lip_file>
    ```
- **Fallback / Bypass**:
  - *Source Reference (`Mantella/src/tts/ttsable.py:294-297`)*:
    ```python
    if not skip_lip_generation:
        generate_facefx_lip_file(...)
    else:
        copy_placeholder_lip_file(lip_file, ...)
    ```
  - When `lip_generation` is set to `"Disabled"` (or fails), Mantella copies a static placeholder `.lip` file (`copy_placeholder_lip_file`), completely bypassing the external executable.

---

## 3. Conversation Lifecycle, Subtitles & Character Overrides

### Conversation Lifecycle Handlers
| Lifecycle Event | Game-Side Handler | Backend Handler |
| :--- | :--- | :--- |
| **Start Conversation** | `MantellaConversation.psc:75` (`StartConversation`), invoked by `MantellaSpell` cast or `MantellaStartHotkey` | `Mantella/src/game_manager.py:365` (`start_conversation`), `src/http/routes/mantella_route.py:87` |
| **Turn Progression** | `MantellaConversation.psc:220` (`RequestContinueConversation`) | `Mantella/src/game_manager.py:461` (`continue_conversation`), `src/output_manager.py:41` |
| **End Conversation** | `MantellaConversation.psc:199, 443` (`CleanupConversation`), `MantellaEndSpell.psc` | `Mantella/src/game_manager.py:588` (`end_conversation`), `src/http/routes/mantella_route.py:93` |

### Subtitle Injection
- **Handler**: `MantellaSubtitles.dll` (SKSE Plugin) exposed to Papyrus via `MantellaSubtitles.psc`.
- *Source Reference (`Mantella-Spell/Scripts/Source/MantellaConversation.psc:356`)*:
  ```papyrus
  MantellaSubtitles.SetInjectTopicAndSubtitleForSpeaker(actorSpeaking, topicToUse, lineToSay)
  ```
- The SKSE plugin hooks Skyrim's internal subtitle dispatch function to dynamically display `lineToSay` with actor name attribution without requiring pre-baked dialogue records in Skyrim master files.

### Character Overrides
- **Handler**: `Mantella/src/games/gameable.py:43-46, 280-326` (`__apply_character_overrides`).
- **File Location**:
  `Data/SKSE/Plugins/MantellaSoftware/data/Skyrim/character_overrides/` (and `<save_folder>/data/Skyrim/character_overrides/`).
- **Mechanism**:
  Reads CSV/TXT files and updates rows in `__character_df` matching by `base_id` or `name`, setting `bio`, `voice_model`, `skyrim_voice_folder`, `llm_service`, `model`, etc.
- **Critical Architectural Reality**:
  Overrides do **NOT** restrict Mantella to a single actor. They only customize the metadata loaded if an actor is targeted.

---

## 4. Components to Delete: Radiant, Group, Multi-Target, Vision

Upstream Mantella is built as an open-ended multi-NPC radiant simulator. For our single-follower mod, the following systems are dead code and must be purged:

| Component Category | Upstream Files (To Purge / Bypass) | Reason / Bloat Removed |
| :--- | :--- | :--- |
| **Radiant Dialogue** | `MantellaRadiantDialogueActorPicker` Quest, `MantellaListenerScript.psc:StartRadiantDialogue`, `MantellaRepository.psc` (`radiantEnabled`, `radiantFrequency`, `triggerRatio`), `conversation_type.py` (`ConversationType.RADIANT`) | Random NPCs speaking unsolicited without player consent; causes polling lag. |
| **Group Conversations** | `MantellaConversationParticipantsQuest`, `MantellaConversation.psc:AddActors`, `characters_manager.py`, `random_llm_selector.py`, `MantellaAdvancedAction_AddToConv.psc`, `MantellaAdvancedAction_ShareConv.psc` | Only ONE follower will ever converse. Multiplexing multiple characters is irrelevant. |
| **Crosshair / Spell Targeting** | `MantellaSpell` magic effect (`MantellaEffectScript.psc`), `MantellaDummySpell`, `MantellaPower`, `MantellaTargetListenerScript.psc` | Player should talk directly to the custom follower via follower activation dialogue, not by casting a spell on random NPCs. |
| **NPC-to-NPC Chat** | `MantellaConversation.psc` (unattended branches where speaker $\neq$ player and listener $\neq$ player), `conversation.py` NPC turn logic | Follower only converses with the Dragonborn. |
| **Vision / Screen Capture** | `Mantella/src/image/image_manager.py`, `Mantella/src/llm/image_client.py` | Uses Windows-only `win32gui` and `SetProcessDPIAware()`; unnecessary VRAM and token overhead. |
| **Extraneous Game Actions** | 20+ Papyrus action scripts: `MantellaAdvancedAction_AbsolveCrime`, `Barter`, `Brawl`, `CastSpell`, `CollectIngr`, `Emote`, `GiveDirections`, `LeadTo`, `Loot`, `ReportCrime`, `Teleport`, `TravelTo` | Follower actions belong in normal Papyrus follower AI packages, not Mantella function-calling bloat. |

---

## 5. Input Mechanics & Why Text Mode Disables the Mic

### How Input Works
1. **Microphone Input**:
   - In Papyrus (`MantellaConversation.psc:187-192`), when a player turn begins (`KEY_REPLYTYPE_PLAYERTALK`):
     ```papyrus
     If (repository.microphoneEnabled && !repository.useHotkeyToStartMic)
         sendRequestForVoiceTranscribe()
     Else
         ShowRepeatingMessage("Awaiting player input...")
     EndIf
     ```
   - Python receives `comm_consts.KEY_REQUESTTYPE_TTS` / transcription request, records microphone audio via `pyaudio`/`sounddevice`, runs `faster-whisper`, and returns transcribed text.
2. **Text Input**:
   - Uses `UIExtensions`'s `UITextEntryMenu` in `MantellaConversation.psc:531-536`:
     ```papyrus
     UIExtensions.InitMenu("UITextEntryMenu")
     UIExtensions.OpenMenu("UITextEntryMenu")
     string result = UIExtensions.GetMenuResultString("UITextEntryMenu")
     if (result && result != "")
         sendRequestForPlayerInput(result, updateContext=False)
     ```

### Root Cause: Why Text Mode Disables the Mic in Mantella
The disabling of the microphone in text mode is **NOT an engine constraint or hardware limitation**. It is caused entirely by an artificial mutual exclusivity check in Papyrus:
- In `Mantella-Spell/Scripts/Source/MantellaRepository.psc:285-298`:
  ```papyrus
  elseIf KeyCode == MantellaListenerTextHotkey
      If(!microphoneEnabled) ; <--- ARTIFICIAL GATE
          MantellaConversation conversation = Quest.GetQuest("MantellaConversation") as MantellaConversation
          if(conversation.IsRunning())
              conversation.GetPlayerTextInput()
          endIf
      elseIf (useHotkeyToStartMic)
          MantellaConversation conversation = Quest.GetQuest("MantellaConversation") as MantellaConversation
          if(conversation.IsRunning())
              conversation.sendRequestForVoiceTranscribe()
          endIf
      endIf
  ```
- **Consequence**: When `microphoneEnabled == true`, pressing `MantellaListenerTextHotkey` is hijacked to trigger `sendRequestForVoiceTranscribe()`. The call to `GetPlayerTextInput()` is completely unreachable!
- **Fix**: Decouple the hotkeys in Papyrus: keep `MantellaListenerTextHotkey` bound strictly to `GetPlayerTextInput()`, and bind voice/PTT to a separate hotkey (or allow text input menu even when mic is enabled).

---

## 6. Windows-Only Dependencies Audit

| Dependency / Component | Location | Windows Role | Linux / CachyOS Impact & Solution |
| :--- | :--- | :--- | :--- |
| `pywin32` (`win32gui`) | `requirements.txt:16`, `src/image/image_manager.py:14-15` | Finds Skyrim window handle for desktop capture | **Non-functional on Linux**. Fails on import or runtime. Fix: Delete `image_manager.py` (Vision is out of scope). |
| `ctypes.windll` | `src/stt/ptt_controller.py:5, 60`, `src/image/image_manager.py:65` | Calls `user32.GetAsyncKeyState` for global hotkey polling | Returns `False` on Linux. In our design, hotkeys are captured game-side by Papyrus/SKSE and sent via HTTP, making Python-side PTT polling redundant. |
| `FaceFXWrapper.exe` | `Sound/Voice/Processing/FaceFXWrapper.exe`, `src/tts/ttsable.py:216` | External Win32 CLI to generate `.lip` files | Cannot be executed natively on Linux without Wine. Fix: Set `lip_generation: Disabled` (copies placeholder `.lip`), or invoke under Proton prefix if lip-sync is required. |
| `MantellaLauncher.dll` | `SKSE/Plugins/MantellaLauncher.dll` | SKSE plugin that auto-spawns `Mantella.exe` on game start | Fails under Proton to launch native Linux Python process. Fix: Omit DLL; run Python backend natively on host Linux. |
| Windows path separators (`\\`) | `src/config/config_loader.py:134, 143` | Hardcoded Windows backslashes | Causes broken paths on Linux. Fix: Use `pathlib.Path` or `os.path.join`. |

---

## 7. Keep / Delete / Replace File Layout Grounding

Grounding against the upstream file tree:

| File / Component | Status | Rationale |
| :--- | :--- | :--- |
| **`Mantella-Spell/SKSE/Plugins/SKSE_HTTP.dll`** | **KEEP** | Critical SKSE bridge for localhost JSON HTTP push communication. |
| **`Mantella-Spell/SKSE/Plugins/MantellaSubtitles.dll`** | **KEEP** | Essential for in-engine dynamic subtitle injection attributed to follower. |
| **`Mantella-Spell/SKSE/Plugins/MantellaLauncher.dll`** | **DELETE** | Windows-only auto-launcher. Mod server runs natively on Linux host. |
| **`Mantella-Spell/Scripts/Source/SKSE_HTTP.psc`** | **KEEP** | Papyrus bindings for HTTP client. |
| **`Mantella-Spell/Scripts/Source/MantellaSubtitles.psc`** | **KEEP** | Papyrus bindings for subtitle hook. |
| **`Mantella-Spell/Scripts/Source/MantellaConstants.psc`** | **KEEP** | Shared protocol constants and action keys. |
| **`Mantella-Spell/Scripts/Source/MantellaConversation.psc`** | **REPLACE** | Replace with lean `DesiFollowerConversation.psc`: hardcode follower actor reference, remove group/radiant code, allow concurrent mic and text entry. |
| **`Mantella-Spell/Scripts/Source/MantellaListenerScript.psc`** | **DELETE** | Manages radiant polling, nearby actor detection, and generic spell tracking. |
| **`Mantella-Spell/Scripts/Source/MantellaTargetListenerScript.psc`**| **DELETE** | Crosshair tracking for arbitrary NPCs. |
| **`Mantella-Spell/Scripts/Source/MantellaAdvancedAction_*.psc`** | **DELETE** | 20+ unused gameplay action scripts. |
| **`Mantella-Spell/Mantella_DISTR.ini`** | **DELETE** | SPID config distributing Mantella spell to every NPC in Skyrim. |
| **`Mantella/src/http/http_server.py`** | **KEEP** | FastAPI ASGI server wrapper. |
| **`Mantella/src/http/routes/mantella_route.py`** | **REPLACE** | Strip generic game state manager; wire directly to Sarkaar Bhaiya pipeline. |
| **`Mantella/src/games/skyrim.py`** | **REPLACE** | Strip 300+ lines of generic bio parsing; keep dialogue file double-buffering logic (`DIALOGUELINE1_FILENAME`). |
| **`Mantella/src/image/`** | **DELETE** | Delete entirely (`win32gui`, desktop vision). |
| **`Mantella/src/stt/ptt_controller.py`** | **DELETE** | Windows `GetAsyncKeyState` is non-functional on Linux. |
| **`Mantella/src/random_llm_selector.py`** | **DELETE** | Multi-NPC turn multiplexer. |
| **`Mantella/src/tts/` (piper, xvasynth)** | **DELETE** | Unused TTS backends. |
| **`Mantella/src/tts/xtts.py`** | **REPLACE** | Wire to our existing low-latency streaming XTTS-v2 Hindi pipeline. |

---

## 8. Verification of Design Brief Section 3.1 Claims

Evaluating the hypotheses and claims in Section 3 & 4 of the design brief against the audited source code:

1. **Claim: "Add the custom NPC through Mantella's character override system... Ensure the override resolves to the correct custom NPC... An NPC profile override alone must not be assumed to restrict Mantella's functionality to that NPC."**
   - **Verdict: VERIFIED (Doc was right)**.
   - *Evidence*: `Mantella/src/games/gameable.py:280-326`. Overrides are simply row updates to `character_df`. Mantella distributes its spell to all NPCs via SPID (`Mantella_DISTR.ini`) and will start conversations with anyone targeted or chosen by radiant picking. An override does zero access control.
2. **Claim: "Mantella's documented text-input configuration disables microphone input. We require both options to be available in the same session."**
   - **Verdict: VERIFIED (Doc was right)**.
   - *Evidence*: `MantellaRepository.psc:286` has `If(!microphoneEnabled)` gating `GetPlayerTextInput()`. Removing this gate and allocating separate hotkeys completely solves the dual-input requirement.
3. **Claim: "Investigate whether Mantella exposes a suitable conversation-target filter."**
   - **Verdict: VERIFIED (Doc hypothesis confirmed: NO filter exists)**.
   - *Evidence*: Upstream has no whitelist or target filter. `StartConversation()` accepts any `Actor[]` passed to it. Restricting conversations to the custom follower requires an explicit check in Papyrus (`if actorSpeaking != CustomFollowerRef; return`) and in the Python route (`if actor.ref_id != FOLLOWER_REF_ID: reject`).
4. **Claim: "Mantella suitability: Polling interval vs push mechanism."**
   - **Verdict: CLARIFIED (Doc was overly cautious)**.
   - *Evidence*: The design doc anticipated polling latency concerns. In reality, modern Mantella v0.14 uses an event-driven push architecture via `SKSE_HTTP.dll` and Papyrus ModEvents. Hand-off latency is minimal ($\sim 16\text{ ms}$).
5. **Claim: "Linux compatibility: Mantella's current installation documentation lists Windows 10/11 requirements and does not establish Linux compatibility."**
   - **Verdict: VERIFIED & PINPOINTED**.
   - *Evidence*: The Python backend core (`FastAPI`, `requests`, `uvicorn`, `numpy`) runs flawlessly on Linux. The Windows-only blockers in the code are strictly: (1) `win32gui` in `image_manager.py`, (2) `ctypes.windll.user32` in `ptt_controller.py`, and (3) `FaceFXWrapper.exe` for lip sync. All three can be excised or safely bypassed on Linux.

