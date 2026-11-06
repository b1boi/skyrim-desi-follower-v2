# Phase 0: Hardware & Runtime Environment Report

This report documents the exact hardware, driver, kernel, Proton, and Skyrim configuration on this host, measured directly from the system on 2026-11-07.

---

## 1. Hardware Specifications

| Component | Specification | Measurement / Details |
| :--- | :--- | :--- |
| **GPU Model** | AMD Radeon RX 6800 (RADV NAVI21) | Discrete GPU, PCI ID `1002:73bf`, Revision `c3` |
| **VRAM Total** | 16,368 MiB (16.0 GB / 17,163,091,968 bytes) | Measured from `/sys/class/drm/card1/device/mem_info_vram_total` |
| **VRAM Used (Idle)**| 1,570.88 MiB (1.53 GiB / 1,647,181,824 bytes) | Measured from `/sys/class/drm/card1/device/mem_info_vram_used` |
| **VRAM Free (Idle)**| **14,797.12 MiB (14.45 GiB / 15,515,910,144 bytes)** | Available for local LLM, TTS, ASR, and Skyrim rendering |
| **CPU** | Intel(R) Xeon(R) CPU E5-1660 v3 @ 3.00GHz | 8 physical cores, 16 threads. Max Turbo: 3800 MHz. AVX2, FMA3, BMI2 |
| **System RAM** | 23.37 GiB (25,094,168,576 bytes ~ 24 GB) | Used: ~7.8 GiB, Free/Available: ~17.27 GiB |
| **Swap** | 23.37 GiB (25,093,468,160 bytes) | `zram0` compressed RAM swap device |
| **Disk** | NVMe SSD (`/dev/nvme0n1p2`), Btrfs | Total: 932 GB, Used: 450 GB, Avail: 480 GB (49% used) |

---

## 2. Operating System & Drivers

| Component | Version | Notes |
| :--- | :--- | :--- |
| **OS Distribution** | CachyOS Linux (Arch Linux derivative) | Rolling release |
| **Kernel** | `7.3.1-1-cachyos` | x86_64 SMP PREEMPT_DYNAMIC |
| **Graphics Driver** | Mesa `26.2.5-arch3.1` (RADV driver) | Open-source Vulkan driver for AMD |
| **Vulkan API** | Instance: `1.4.363`, Device: `1.4.354` | RADV NAVI21, Conformance: `1.4.5.3` |
| **CUDA** | **N/A** (AMD Hardware) | System does not possess NVIDIA hardware |
| **ROCm / HIP** | `rocm-core 7.2.4-1.1`, `rocm-hip-sdk 7.2.4-1` | Installed on system |
| **Python** | Python `3.14.9` (System), `uv 0.13.7` available | Venv management via `uv` recommended |

---

## 3. Skyrim & Proton Configuration

| Property | Value | Notes |
| :--- | :--- | :--- |
| **Skyrim Edition** | The Elder Scrolls V: Skyrim Special Edition (with AE free updates) | Steam App ID: `489830` |
| **Steam Build ID** | `24914197` (Last verified: 1793582576) | Stored in `appmanifest_489830.acf` |
| **Binary FileVersion** | `1.7.104.0` | PE resource version extracted from `SkyrimSE.exe` |
| **Installed DLCs / CC** | `Skyrim.esm`, `Update.esm`, `Dawnguard.esm`, `HearthFires.esm`, `Dragonborn.esm`, `ccBGSSSE001-Fish.esm`, `ccBGSSSE025-AdvDSGS.esm`, `ccBGSSSE037-Curios.esl`, `ccQDRSSE001-SurvivalMode.esl`, `_ResourcePack.esl` | Standard modern Anniversary Edition baseline |
| **SKSE Version** | **NOT PRESENT** | No SKSE binaries or scripts found in Skyrim root or Data folder |
| **Proton Build** | `Proton - Experimental` | Tag: `experimental-11.0-20261027b-x86_64` (internal version `11.0-100`) |
| **Proton Prefix Path** | `/home/bepis/.local/share/Steam/steamapps/compatdata/489830/pfx` | Steam default compatdata prefix |
| **Skyrim Host Path** | `/home/bepis/.local/share/Steam/steamapps/common/Skyrim Special Edition` | Host filesystem location |
| **Skyrim Data (Host)** | `/home/bepis/.local/share/Steam/steamapps/common/Skyrim Special Edition/Data` | Directory where ESPs, BSA/loose files reside |
| **Skyrim Data (Prefix)** | `S:\steamapps\common\Skyrim Special Edition\Data` (or `Z:\home\bepis\.local\share\Steam\steamapps\common\Skyrim Special Edition\Data`) | Inside Wine/Proton, `S:` maps to `~/.local/share/Steam`, `Z:` maps to `/` |

---

## 4. Key Takeaways for Stage 1

1. **VRAM Budget**:
   - Idle desktop consumes ~1.53 GiB.
   - 14.45 GiB of VRAM is free for the AI stack and Skyrim.
   - Skyrim SE under Proton typically consumes ~2.5 - 3.5 GiB VRAM at 1080p/1440p without heavy texture mods.
   - Available VRAM for AI stack (LLM + XTTS + ASR) during gameplay is estimated at **~10.5 - 11.5 GiB**.

2. **Backend Execution**:
   - AMD RX 6800 runs Vulkan natively.
   - LM Studio and llama.cpp run natively on Linux using Vulkan (`ggml-vulkan`).
   - Mantella Python backend runs natively on Linux, communicating over localhost HTTP / socket with the game running inside the Proton prefix.

3. **SKSE Status**:
   - The game currently lacks SKSE. The executable version is `1.7.104.0`. SKSE64 matching this build is required for in-game execution.

