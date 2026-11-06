# Phase 0: Patch Log

All modifications, excisions, and patches to upstream Mantella code are recorded here with rationale.

---

## T3 Patches: Native Linux Execution with Stub LLM & Stub TTS

The following minimal set of patches was applied to `upstream/Mantella` to run the backend natively on Linux (CachyOS) with stub LLM and stub TTS:

### 1. `src/tts/ttsable.py`
- **Lines 207 & 253**: Replaced `creationflags=subprocess.CREATE_NO_WINDOW` with `creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)`.
  - *Rationale*: `subprocess.CREATE_NO_WINDOW` is a Windows-only Python attribute; referencing it on Linux raises `AttributeError: module 'subprocess' has no attribute 'CREATE_NO_WINDOW'`.
- **Lines 294–300**: Added exception handling around `generate_facefx_lip_file` to fall back to `copy_placeholder_lip_file`.
  - *Rationale*: Upstream Mantella intended to fall back to placeholder `.lip` files when LipGen/FaceFXWrapper was missing or failed, but `FileNotFoundError` was not caught inside the generation block, preventing placeholder copying.

### 2. `data/Skyrim/placeholder/placeholder.lip`
- **Added**: Copied placeholder `.lip` asset into `data/Skyrim/placeholder/`.
  - *Rationale*: Upstream only included `data/Fallout4/placeholder/placeholder.lip`. For Skyrim, `copy_placeholder_lip_file` threw `FileNotFoundError: The source file does not exist: .../data/Skyrim/placeholder/placeholder.lip`.

### 3. Stub TTS Integration (`src/tts/stub_tts.py`, `src/tts/tts_factory.py`, `src/config/definitions/tts_definitions.py`)
- **Added**: `src/tts/stub_tts.py` implementing `StubTTS(TTSable)`.
- **Modified**: `src/config/definitions/tts_definitions.py` to add `TTSEnum.STUB`.
- **Modified**: `src/tts/tts_factory.py` to map `'stub'` to `StubTTS`.
  - *Rationale*: Allows Phase 0 feasibility testing and game protocol validation without GPU, CUDA, or external TTS server dependencies. Generates 1.0s 24kHz mono PCM WAV tones and valid `.lip` files in < 5 ms.

### 4. Stub LLM Integration (`src/llm/llm_client.py`, `src/utils.py`)
- **Modified**: `src/llm/llm_client.py` to detect `config.llm_api == 'Stub'` or `config.llm == 'stub'`. Overrides `streaming_call` and `request_call` to yield Romanized Hindi dialogue ("Bhaiyo aur behno, Swagat hai! Sarkaar Bhaiya aapke saath hai. Skyrim ke maamle hum suljha lenge.") without requiring external API keys or network connection.
- **Modified**: `src/utils.py` in `is_local_url` to recognize `'stub'` and `'localhost'` as local URLs.
  - *Rationale*: Bypasses OpenAI/OpenRouter network calls and `GPT_SECRET_KEY.txt` lookups for mock/offline testing.

### 5. Linux CWD & Path Resolution (`src/setup.py`, `custom_user_folder.ini`, `main.py`)
- **Modified**: `src/setup.py` (`_set_cwd_to_exe_dir`) to `os.chdir(utils.resolve_path())` when running as a Python script.
- **Modified**: `src/setup.py` (`_get_custom_user_folder`) to resolve `custom_user_folder.ini` via `utils.resolve_path()`.
- **Modified**: `custom_user_folder.ini` to set `custom_user_folder = <workspace>/run/mantella_user`.
- **Modified**: `main.py` to resolve `data/language_support.csv` using `utils.resolve_path()` and ensure `logger` is initialized before the main `try` block.
  - *Rationale*: On Linux under standard user permissions, Mantella's default hardcoded path `/home/<user>/Documents/My Games/Mantella` can fail with `OSError: [Errno 30] Read-only file system` or `FileNotFoundError` if Documents does not exist. Using `custom_user_folder.ini` keeps runtime files inside the workspace, and path resolution ensures Mantella can be run from any working directory.

### 6. Headless Server Support (`main.py`)
- **Modified**: `main.py` to make `StartUI` (Gradio) import optional with a fallback to headless FastAPI serving.
  - *Rationale*: Gradio is only used for the web settings UI; the SKSE game integration only interacts with `mantella_route` over HTTP. Making Gradio optional prevents startup crashes in minimal or headless Linux environments.

---

## What Remains Windows-Only in Upstream Mantella

The following upstream Mantella features currently have Windows-only dependencies or logic and are bypassed or disabled in our Linux deployment:

1. **In-Process Lip-Sync Generation (`LipGenerator.exe` / `FaceFXWrapper.exe`)**:
   - `FaceFXWrapper.exe` and Bethesda `LipGenerator.exe` are Windows PE executables. While upstream attempts `wine <command>` in `src/tts/ttsable.py:174`, running Wine inside Proton/Linux backend adds 2-5s per sentence and is prone to COM/registry errors. On Linux, placeholder `.lip` copying or offline Linux phoneme synthesis is preferred.
2. **Push-To-Talk Controller (`PTTController`)**:
   - In `src/stt/ptt_controller.py:17`, upstream explicitly has:
     ```python
     if not sys.platform.startswith('win'):
         return False
     ```
     PTT uses Windows raw input / DirectInput hooks and does not function on Linux without X11/Wayland input grabbing.
3. **Vision / Screenshot Capture (`ImageManager`)**:
   - In `src/llm/image_client.py` and `ImageManager`, upstream uses `win32gui` (`win32gui.FindWindow`, `win32gui.GetWindowRect`) to capture Skyrim's DirectX window directly. On Linux under Proton, `win32gui` does not exist. (Design brief explicitly marks vision as out of scope for Phase 0 and deleted for Sarkaar Bhaiya).
4. **Fast Response Mode Internal Audio Playback (`winsound`)**:
   - Fast response mode uses `winsound.PlaySound` in `src/games/skyrim.py:165` to play the first line through the host speakers before game playback. On Linux it falls back to `playsound` (or is disabled when Skyrim plays voice natively).


