# Third-Party Notices & Acknowledgements

This repository incorporates, references, or builds upon open-source software, community tools, and publicly licensed Elder Scrolls lore resources. We gratefully acknowledge the contributions of the following upstream projects and authors.

---

## 1. Mantella

- **Project**: Mantella (Skyrim AI NPC Dialogue Integration)
- **Author**: art-from-the-machine
- **Repository**: [https://github.com/art-from-the-machine/Mantella](https://github.com/art-from-the-machine/Mantella)
- **License**: GNU Affero General Public License v3.0 (AGPL-3.0)
- **Notice**:
  This project forks and adapts components of the Mantella Python server under the terms of the AGPL-3.0 license. The original copyright belongs to art-from-the-machine and Mantella contributors. A copy of the AGPL-3.0 license is provided in [`LICENSE`](LICENSE).

- **Project**: Mantella-Spell (Papyrus Mod & Game-Side Integration)
- **Author**: art-from-the-machine
- **Repository**: [https://github.com/art-from-the-machine/Mantella-Spell](https://github.com/art-from-the-machine/Mantella-Spell)
- **License**: MIT License
- **Notice**:
  Copyright (c) 2023 art-from-the-machine. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files under the standard MIT License.

---

## 2. Elder Scrolls Lore & Knowledge Base Data

### Unofficial Elder Scrolls Pages (UESP)
- **Source**: [https://en.uesp.net](https://en.uesp.net)
- **License**: Creative Commons Attribution-ShareAlike 2.5 Generic (CC BY-SA 2.5)
- **Notice**:
  Lore summaries, historical background entries, NPC profiles, and location cross-references compiled in `data/` are derived from the Unofficial Elder Scrolls Pages (UESP). Content is licensed under CC BY-SA 2.5. See [`data/LICENSE`](data/LICENSE) for full license text. All credit for canonical lore documentation belongs to UESP community contributors.

### The Elder Scrolls Wiki (Fandom)
- **Source**: [https://elderscrolls.fandom.com](https://elderscrolls.fandom.com)
- **License**: Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)
- **Notice**:
  Supplementary dialogue references, quest progression data, and item categorization schemas utilize metadata referenced from The Elder Scrolls Wiki on Fandom under CC BY-SA 3.0.

---

## 3. Native Skyrim & SKSE Plugins

### `SKSE_HTTP`
- **Author**: Leidtier
- **Repository**: [https://github.com/Leidtier/SKSE_HTTP](https://github.com/Leidtier/SKSE_HTTP)
- **License**: MIT License
- **Notice**:
  Provides native localhost HTTP request handling and JSON dictionary storage for Skyrim Papyrus scripts.

### `MantellaSubtitles` (Mantella-Subtitles-Plugin-NG)
- **Author**: swwu
- **Repository**: [https://github.com/swwu/Mantella-Subtitles-Plugin-NG](https://github.com/swwu/Mantella-Subtitles-Plugin-NG)
- **License**: MIT License
- **Notice**:
  Provides dynamic real-time subtitle rendering on the Skyrim HUD widget via CommonLibSSE-NG hooks.

### `CommonLibSSE-NG`
- **Authors**: CharmedBaryon, alandtse, and community contributors
- **Repository**: [https://github.com/CharmedBaryon/CommonLibSSE-NG](https://github.com/CharmedBaryon/CommonLibSSE-NG)
- **License**: MIT License
- **Notice**:
  Provides modern multi-runtime C++ reverse engineering headers and Address Library binding infrastructure for Skyrim SE/AE plugins.

### `SkyUI SDK`
- **Authors**: SkyUI Team (schlangster et al.)
- **Repository**: [https://github.com/schlangster/skyui](https://github.com/schlangster/skyui)
- **License**: MIT License
- **Notice**:
  Provides the Mod Configuration Menu (MCM) Papyrus framework (`SKI_ConfigBase.psc`).

### `UIExtensions`
- **Author**: expired6978
- **Source**: [Nexus Mods #17561](https://www.nexusmods.com/skyrimspecialedition/mods/17561)
- **License**: Community Mod License / Open Script Interface
- **Notice**:
  Provides the in-game text entry Scaleform menu (`UITextEntryMenu`) used for player text input.

---

## 4. Bethesda Game Studios Assets Disclaimer

> [!IMPORTANT]
> **NO PROPRIETARY BETHESDA ASSETS INCLUDED**
> 
> This repository contains **NO copyrighted assets, proprietary game files, or binary game media** owned by Bethesda Game Studios, ZeniMax Media Inc., or Microsoft Corporation.
> 
> Specifically, this repository does NOT contain or distribute:
> - Any official Skyrim master files (`Skyrim.esm`, `Update.esm`, `Dawnguard.esm`, `HearthFires.esm`, `Dragonborn.esm`).
> - Any Bethesda sound archives, music files, or voice files (`.bsa`, `.ba2`, `.fuz`, `.xwm`, `.wav`).
> - Any vanilla meshes (`.nif`), textures (`.dds`), or animations (`.hkx`).
> 
> The *Sarkaar Bhaiya* mod is an independent modification that requires an authentic, legally purchased copy of *The Elder Scrolls V: Skyrim Special Edition* or *Anniversary Edition* to function. All Elder Scrolls trademarks, titles, and lore settings are the property of Bethesda Softworks / ZeniMax Media.
