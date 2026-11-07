# Skyrim Desi Follower (Sarkaar Bhaiya)

An LLM-powered companion mod for *The Elder Scrolls V: Skyrim Special Edition / Anniversary Edition* featuring ONE custom follower—**Sarkaar Bhaiya**—who speaks Romanized Hindi / Hinglish.

The mod uses a native Linux fork of [Mantella](https://github.com/art-from-the-machine/Mantella) as the game-to-backend communication layer, communicating with Skyrim running under Proton on Linux (CachyOS) over localhost HTTP.

---

## Architecture Overview

- **Target Game Version**: Skyrim SE/AE `1.7.104.0` (Anniversary Edition, Build ID `24914197`) under Proton Experimental
- **Script Extender**: SKSE64 `2.3.1` with Address Library v13 ("All in One 1.7.104.0")
- **Hardware Profile**: AMD Radeon RX 6800 (16GB VRAM, ROCm 6.4 / Vulkan 1.4, **no CUDA**) on Linux (CachyOS)
- **Backend**: Runs **natively on Linux**, listening on `http://127.0.0.1:4999/mantella`
- **Follower Persona**: Sarkaar Bhaiya—cunning, political, witty, speaking in colloquial Romanized Hindi / Hinglish

---

## Repository Structure

```text
├── docs/
│   ├── design_brief_v2.md          # Architectural and technical specification
│   ├── persona_sarkaar_bhaiya.md   # Sarkaar Bhaiya character bible & tone guidelines
│   └── phase0/
│       ├── env.md                  # Hardware, VRAM, and runtime environment report
│       ├── mantella_audit.md       # Upstream Mantella source code audit (v0.14)
│       ├── skse_decision.md        # SKSE 2.3.1 / 1.7.104 compatibility assessment
│       ├── mantella_linux_stub.patch # Patch for native Linux execution with stubs
│       ├── patch_log.md            # Detailed log of all upstream modifications
│       └── manual_steps.md         # Manual instructions for in-game testing
├── scripts/
│   ├── check_secrets.sh            # Pre-commit secret and .env scanner
│   ├── install_hooks.sh            # Pre-commit hook installer
│   ├── run_server.sh               # Starts the native Linux Mantella server
│   └── latency_report.py           # Analyzes trace JSONL and reports P50/P90/P95 stats
├── src/
│   └── latency_trace.py            # High-resolution monotonic pipeline turn tracer
├── tests/
│   ├── test_mantella_stub.py       # End-to-end SKSE HTTP conversation mock test
│   └── test_trace.py               # Unit tests for tracer and percentile reporting
├── upstream/                       # Git-ignored upstream submodules/clones
│   ├── Mantella/                   # Upstream Python server pinned at v0.14
│   └── Mantella-Spell/             # Upstream Papyrus/SKSE mod pinned at v0.14
├── LICENSE                         # GNU Affero General Public License v3 (AGPL-3.0)
├── requirements.txt                # Direct Python dependencies
└── requirements.lock.txt           # Fully locked environment dependencies
```

---

## Quickstart & Setup

### 1. Prerequisites
- Linux (tested on CachyOS / Arch Linux)
- Python 3.11 (`python3.11`)
- Git

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/b1boi/skyrim-desi-follower-v2.git
cd skyrim-desi-follower-v2

# Create and activate a Python 3.11 virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.lock.txt
# (or install minimal direct requirements: pip install -r requirements.txt)

# Install pre-commit hooks (sets core.hooksPath to .githooks)
bash scripts/install_hooks.sh
```

### 3. Upstream Mantella Setup & Patching

Clone upstream Mantella and Mantella-Spell at their pinned `v0.14` tags, then apply the Linux compatibility patch:

```bash
mkdir -p upstream
cd upstream

# Clone Mantella Python server @ v0.14
git clone --depth 1 --branch v0.14 https://github.com/art-from-the-machine/Mantella.git Mantella

# Clone Mantella-Spell Papyrus/SKSE mod @ v0.14
git clone --depth 1 --branch v0.14 https://github.com/art-from-the-machine/Mantella-Spell.git Mantella-Spell

# Apply the Linux native compatibility patch to Mantella
cd Mantella
git apply ../../docs/phase0/mantella_linux_stub.patch

cd ../..
```

The patch applies minimal necessary fixes:
- Fixes Windows-only `subprocess.CREATE_NO_WINDOW` raising `AttributeError` on Linux.
- Adds placeholder `.lip` copying fallback when Windows lip generators are absent.
- Registers `StubTTS` and `StubLLM` to allow offline testing with Romanized Hindi mock voicelines.
- Redirects user directories to `run/mantella_user` to avoid read-only permissions on `~/Documents`.
- Makes the Gradio settings UI optional so the server runs headless.

---

## Running the Server

Start the native Python server:

```bash
bash scripts/run_server.sh
```

The server listens on `http://127.0.0.1:4999/mantella` and responds to all SKSE Papyrus HTTP events.

---

## Running Tests

Verify the server, mock conversation protocol, and latency tracing module:

```bash
PYTHONPATH=. pytest tests/
```

To generate a latency report across a recorded benchmark session:

```bash
python scripts/latency_report.py run/mantella_user/trace.jsonl --format markdown
```

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See [`LICENSE`](file:///home/bepis/git/skyrim-desi-follower-v2/LICENSE) for details.
Upstream Mantella is licensed under GPL-3.0 by art-from-the-machine.

