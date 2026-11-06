# Technical Design Brief
## Single-NPC, LLM-Powered Hindi/Hinglish Skyrim Companion

**Project type:** Skyrim Special Edition / Anniversary Edition follower mod with an external AI conversation system.

**Primary objective:** Create one custom Skyrim follower who has a distinct personality, an extensive knowledge base, persistent long-term memory, and dynamically generated conversations. The follower must understand Hindi, Hinglish and English, and speak primarily in conversational Hindi using the Roman alphabet.

---

## 1. Vision and intended experience

I want to create a custom Skyrim follower who behaves like a conventional Skyrim companion in terms of movement, combat, following, waiting, equipment and interaction with the game world.

The difference is their conversational intelligence.

Instead of manually writing hundreds or thousands of dialogue lines and recording each one, I want the follower to generate their own responses dynamically using an LLM.

The follower should have:

- A carefully defined personality, worldview, history, motivations and opinions.
- A dedicated knowledge database containing relevant Elder Scrolls lore and character-specific knowledge.
- Persistent memory of conversations and experiences with the player.
- Awareness of relevant in-game events, locations, quests and surroundings.
- The ability to hold natural, open-ended conversations.
- A consistent, unique voice generated using TTS.
- A consistent personality regardless of the language used by the player.

The intended result is a companion who develops a relationship with the player over an extended playthrough, rather than a conventional follower who simply cycles through prerecorded dialogue.

### Important scope restriction

**This is a single-follower project, NOT a general AI NPC overhaul.**

I do not want:
- Every NPC in Skyrim to become intelligent.
- Random NPCs approaching the player to initiate AI conversations.
- AI-generated conversations between unrelated NPCs.
- A general-purpose AI interaction system for the entire game.
- Other NPCs having their vanilla dialogue or behaviour modified.

Only the custom follower should be connected to the AI system. All other Skyrim NPCs must remain unaffected.

---

## 2. Core character and language requirements

The follower must be designed around Hindi-speaking Indian players.

### Input languages

The player must be able to communicate using either a microphone or an in-game text interface.

Supported input formats:

- Spoken Hindi.
- Spoken Hinglish.
- Spoken English.
- Romanized Hindi (e.g. "Tum kahan ja rahe ho?").
- Devanagari Hindi (e.g. "तुम कहाँ जा रहे हो?").
- Mixed English and Hindi sentences.

Microphone and keyboard input should both remain available during the same conversation. The player should not need to change a global setting to switch between them.

### Output language

The follower's default speaking style is Hindi-dominant conversational Hindi.

Requirements:

1. All visible dialogue and subtitles should use Romanized Hindi.
2. Hindi grammar and sentence structure should be natural and conversational.
3. English vocabulary should be used naturally where appropriate.
4. Proper nouns, Skyrim terminology, character names and location names should generally retain their original spelling.
5. Avoid overly formal or literary Hindi.
6. The follower should understand English but should not automatically switch to English just because the player uses it.
7. The personality must remain consistent across all input languages.

Example:

Player: "Tumhe ye Dwemer machines kaisi lagti hain?"

Follower: "Kaafi interesting hain. In logon ne technology mein toh kamaal kar diya tha, lekin mujhe lagta hai ki inka apni intelligence par kuch zyada hi bharosa tha."

**Important distinction:** Romanized Hindi is the required visible output. The internal TTS representation does not necessarily have to use Roman script.

---

## 3. Proposed technical architecture

My initial preference is to reuse existing Skyrim AI infrastructure, particularly Mantella, rather than building the entire game-to-AI communication system from scratch.

However, Mantella should be treated as a replaceable integration layer. We should not compromise the single-follower requirement or dual-input requirement simply to avoid modifying it.

### Proposed architecture

```text
                 SKYRIM SE / AE
                       |
                       |
          Custom Follower Plugin (ESP/ESL)
                       |
          Normal Follower Functionality
                       |
          Custom AI Conversation Trigger
                       |
                       v
              MANTELLA INTEGRATION
              or Custom SKSE Bridge
                       |
                       v
              PYTHON AI BACKEND
                       |
          +------------+-------------+
          |            |             |
          v            v             v
       Persona      RAG / Lore     Memory
       Database     Database       System
          |            |             |
          +------------+-------------+
                       |
                       v
              MULTILINGUAL LLM
                       |
              Hindi Response
              (Romanized Script)
                       |
              +--------+--------+
              |                 |
              v                 v
          Text Display      TTS Processing
                                |
                       Roman-to-Devanagari
                       Normalization as needed
                                |
                                v
                           XTTS Hindi
                                |
                                v
                         Audio Generation
                                |
                                v
                       Skyrim Voice Playback
```

The game integration and AI backend should operate asynchronously. LLM inference, speech recognition and TTS must never block Skyrim's main game thread.

---

## 4. Skyrim-side implementation

### Custom follower

Create one custom NPC using the Creation Kit.

The NPC should have standard follower functionality:

- Recruitment and dismissal.
- Follow and wait commands.
- Normal combat behaviour.
- Equipment and inventory management.
- Standard sandboxing and package behaviour.
- Compatibility with the intended follower framework.

The follower's normal game behaviour should be independent of the LLM.

The LLM is responsible for conversation and contextual responses, not fundamental follower functionality.

### Single-NPC AI restriction

This is a hard architectural requirement.

The AI conversation service must only accept requests associated with the custom follower's actor identity.

Ideally, the system should use a unique plugin identifier / actor identity rather than relying solely on the NPC's display name.

If using Mantella:

- Add the custom NPC through Mantella's character override system.
- Package the character override with the follower mod.
- Ensure the override resolves to the correct custom NPC.
- Disable radiant conversations, automatic NPC approaches and group conversations.
- Investigate whether Mantella exposes a suitable conversation-target filter.
- If necessary, modify or fork the integration so the AI conversation can only be initiated through the custom follower.

An NPC profile override alone must not be assumed to restrict Mantella's functionality to that NPC.

### Game context

The AI should receive relevant information from the game when available:

- Current location and worldspace.
- Nearby NPCs and enemies.
- Combat state.
- Relevant quest events and stages.
- Important player actions.
- Significant discoveries.
- Follower state and relationship context.

We should prioritise structured game data from Papyrus/SKSE instead of relying entirely on screenshots or LLM visual interpretation.

Context should be event-driven where possible rather than constantly sending large game-state updates.

---

## 5. AI and personality system

The character should have a dedicated personality configuration.

Suggested structure:

```text
character/
    persona.yaml
    biography.md
    personality.yaml
    beliefs.yaml
    relationships.json
    knowledge_boundaries.yaml
    speech_style.yaml
```

The persona should define:

- Identity and history.
- Personality traits.
- Worldview and beliefs.
- Likes and dislikes.
- Opinions about factions, races, people and events.
- Behavioural boundaries.
- Sense of humour.
- Conversational habits.
- Attitude towards the player.
- Speech characteristics.

The personality must be persistent and consistent across conversations.

The AI should not simply receive a generic instruction to roleplay a character. It should receive structured character information and a relevant subset of persistent state every time a response is generated.

Relationship characteristics such as trust, respect, friendship and hostility should be represented as persistent values rather than relying entirely on the model to remember them correctly.

---

## 6. Knowledge base and RAG

The follower needs access to a substantial knowledge database.

I want the character to be able to discuss Elder Scrolls lore, historical events, characters, factions, locations, religion, magic, books and other subjects relevant to their identity.

We should implement Retrieval-Augmented Generation rather than injecting the entire knowledge database into every LLM request.

### Proposed implementation

- SQLite for structured records and metadata.
- A vector index for semantic retrieval.
- Keyword search for exact names, terminology and references.
- Hybrid retrieval combining semantic and keyword results.
- Relevant excerpts injected into the LLM prompt.

Suggested knowledge organisation:

```text
knowledge/
    history/
    characters/
    locations/
    factions/
    religion/
    magic/
    races/
    books/
    events/
    character_specific/
```

Knowledge entries should contain metadata such as:

- Source.
- Era or historical period.
- Subject.
- Relevant locations.
- Reliability / certainty.
- Character awareness or access restrictions.

### Knowledge boundaries

The follower must not automatically know everything in the Elder Scrolls universe.

Their knowledge should be governed by their biography, timeline, experiences and what they could reasonably have learned.

The model should distinguish established facts from legends, speculation and unreliable accounts.

The RAG system should retrieve information relevant to the current conversation, rather than attempting to provide the model with the entire lore database.

---

## 7. Persistent memory

Memory is one of the most important components of this project.

I do not want a follower whose knowledge of the player resets every time a conversation ends or the game is restarted.

Memory should persist between conversations and ideally across game sessions.

I would divide it into three layers:

### A. Conversation history

Store original player and follower messages.

Retain the original input script and language. Do not discard whether a conversation happened in Hindi, Hinglish or English.

### B. Episodic memory

Store significant individual experiences.

Examples:

- The player helped a particular NPC.
- The player and follower explored a Dwemer ruin.
- The player told the follower about a personal preference.
- The follower and player disagreed about a particular faction.
- The player made a promise.

Each memory should have relevance, importance and timestamps.

### C. Long-term character and relationship memory

Maintain consolidated information about the player's preferences, shared history, relationship progression and important recurring events.

Use periodic summarisation and memory consolidation so that every old conversation does not have to be sent to the LLM.

### Important requirement

Memory must be language-independent.

For example, the player might initially mention a character in Hinglish and refer to that same person in English several hours later. The system must recognise that these conversations are connected.

Suggested storage:

- SQLite for persistent memory.
- Vector search for semantically relevant recall.
- Structured relationship variables.
- Periodic memory summarisation.

Mantella's existing conversation history can be evaluated as a baseline, but additional structured memory may be necessary.

---

## 8. Language processing pipeline

The language system should be designed specifically for Romanized Hindi and Hinglish.

### Speech recognition

Use Whisper as the initial multilingual STT implementation.

Benchmark it against Hinglish-specific fine-tuned models.

The selected recogniser must handle natural code-switching between Hindi and English, not just isolated Hindi or English sentences.

The system should output Romanized Hindi where appropriate.

### Text input

The text interface should accept:

- Romanized Hindi.
- Devanagari.
- Hinglish.
- English.

Typed input should bypass speech recognition and enter the same conversation-processing pipeline.

### LLM

Use a multilingual instruct model with strong Hindi comprehension and generation.

The model must:
- Understand the supported input formats.
- Follow the character's language rules.
- Generate Hindi-dominant Romanized dialogue.
- Use retrieved lore and memories.
- Produce structured output.
- Avoid unnecessary English translation.

### Speech generation

XTTS-v2 is the initial preferred TTS engine because I already have an XTTS-based voice-generation pipeline.

Hindi is an officially supported XTTS-v2 language.

However, direct Romanized Hindi input must be benchmarked rather than assumed to work correctly.

I propose a two-representation system:

```text
LLM output:
    Arre, tumne ye jagah pehle dekhi hai kya?

Visible subtitles:
    Arre, tumne ye jagah pehle dekhi hai kya?

Internal TTS representation:
    अरे, तुमने ये जगह पहले देखी है क्या?
```

The normalisation stage should:

- Convert Hindi words to Devanagari where required.
- Preserve English words where possible.
- Protect Skyrim proper nouns.
- Use a custom pronunciation dictionary for difficult names.
- Preserve the original Romanized response for subtitles.

The actual voice generation quality should determine the final implementation.

### Speech consistency

The character should use the same voice model throughout the playthrough.

The system should also support audio caching for repeated responses where appropriate, without caching the entire conversation history as if it were dialogue.

---

## 9. LLM response structure and safety

The LLM should not directly execute arbitrary Skyrim commands.

Instead, responses should use a validated structured format.

For example:

```json
{
    "response_text": "Aaj ka safar kaafi interesting raha.",
    "emotion": "calm",
    "action": null,
    "memory_candidate": {
        "event": "Player explored a Dwemer ruin",
        "importance": 0.5
    }
}
```

The backend should validate the response before sending it to Skyrim.

Any future follower action system should use a strict allowlist of supported actions and deterministic Papyrus/SKSE functions.

For the first version, dynamic conversation is more important than giving the LLM control over the follower's gameplay behaviour.

---

## 10. Latency and performance requirements

Latency is one of my primary concerns.

I do not want a system where the player finishes speaking and then waits an immersion-breaking amount of time for a response.

We should profile the complete pipeline rather than just measure LLM tokens per second.

Measure:

1. Microphone capture and voice activity detection.
2. Speech recognition.
3. Context and memory retrieval.
4. LLM time to first token.
5. Complete response generation.
6. Text normalisation.
7. TTS generation.
8. Audio availability and playback start.

Use a local inference setup wherever practical.

The target should be short, natural responses with minimal delay.

I would also like:
- Preloaded models rather than loading models for individual conversations.
- Persistent ASR/TTS service processes.
- Efficient retrieval and small context payloads.
- Caching where appropriate.
- Asynchronous processing.
- Conversation timeouts and graceful error handling.
- No game freezes during inference.

Please establish measurable P50 and P95 latency baselines on the actual hardware before choosing final models.

---

## 11. Proposed technology choices

These are initial preferences, not mandatory implementation decisions.

| Component | Proposed technology |
|---|---|
| Game | Skyrim Special Edition / Anniversary Edition |
| Plugin | Creation Kit ESP/ESL |
| Game scripting | Papyrus |
| Native integration | SKSE, if necessary |
| Follower framework | Vanilla follower system or compatible existing framework |
| AI integration | Mantella initially, with a custom bridge if required |
| Backend | Python |
| LLM inference | Local multilingual instruct model |
| Speech recognition | Whisper / Hinglish-specific ASR benchmark |
| TTS | Existing XTTS-v2 Hindi voice pipeline |
| Knowledge retrieval | SQLite + vector search |
| Long-term memory | SQLite + semantic retrieval |
| Configuration | JSON / YAML |
| Audio processing | Existing Python audio pipeline |
| Lip sync | Mantella / FaceFX integration |

---

## 12. Critical integration questions

I specifically want the systems designer to investigate these before committing to the architecture.

**1. Mantella suitability**

Can Mantella be used as a conversation and playback engine for one specific custom follower without enabling its functionality for every other NPC?

If not, how much work would be needed to adapt its SKSE and Python components?

**2. Simultaneous input**

Mantella's documented text-input configuration disables microphone input. We require both options to be available in the same session.

Can this be implemented with an external input interface, or will Mantella's input handling need modification?

**3. Linux compatibility**

The intended development environment may be CachyOS, with Skyrim running through Proton.

Mantella's current installation documentation lists Windows 10/11 requirements and does not establish Linux compatibility.

This needs to be an early proof-of-concept, not a problem discovered after the entire system is built.

**4. Voice pipeline integration**

Can the existing XTTS Python pipeline be integrated directly with Mantella's supported XTTS API interface?

Can Romanized Hindi be normalised internally without affecting visible dialogue?

**5. Persistent memory**

How much of Mantella's existing memory functionality can be reused, and where should a custom SQLite/RAG memory layer be introduced?

**6. Game-state access**

Which game events and quest states can be reliably obtained through Papyrus, and which require SKSE-level integration?

**7. Licensing and distribution**

If Mantella is modified or forked, review its AGPL-3.0 licensing requirements before distributing the resulting project.

---

## 13. Development milestones

I would prefer an incremental implementation where every stage produces a working prototype.

| Phase | Deliverable |
|---|---|
| 0. Feasibility | Validate Skyrim integration, Mantella compatibility and runtime environment |
| 1. Follower | Working custom follower with normal Skyrim behaviour |
| 2. AI integration | AI conversations restricted to that follower |
| 3. Language | Typed Hindi/Hinglish/English input and Romanized Hindi generation |
| 4. Voice | XTTS Hindi speech with tested pronunciation normalisation |
| 5. Microphone | Hindi/Hinglish ASR integrated with the same conversation pipeline |
| 6. Memory | Persistent conversations and episodic memories |
| 7. Knowledge | Character-specific RAG database |
| 8. Game awareness | Contextual responses to relevant Skyrim events |
| 9. Polish | Latency improvements, lip sync, compatibility and save testing |

---

## 14. Acceptance criteria for the first playable prototype

Before expanding the system, I want a version that can demonstrate the following:

1. Only the custom follower can initiate AI conversations.
2. The follower functions as a normal Skyrim companion.
3. I can type Romanized Hindi and receive a coherent response.
4. I can type Devanagari Hindi and receive a coherent response.
5. I can speak Hindi/Hinglish through my microphone.
6. The follower answers primarily in conversational Hindi written in Roman script.
7. The follower speaks using the custom XTTS voice.
8. The follower maintains its defined personality.
9. The follower can retrieve relevant character knowledge.
10. The follower remembers previous conversations after the game is restarted.
11. All other NPCs remain completely unaffected.
12. The game remains responsive while the AI services are processing requests.

A small working prototype satisfying these requirements is more valuable than a large unfinished mod with elaborate features.

---

## 15. Overall design philosophy

The most important distinction is between the follower's **gameplay intelligence and conversational intelligence**.

Skyrim should continue handling ordinary gameplay through its existing NPC AI, follower packages, combat system and quest mechanics.

The external AI system should handle:
- What the follower says.
- How the follower says it.
- What the follower knows.
- What the follower remembers.
- How the follower interprets events.
- How the follower's relationship with the player develops.

The follower should feel like a believable character who happens to be living in Skyrim, not an AI chatbot that has been attached to an NPC.

I would rather have one genuinely convincing companion with a deep personality, coherent memories and natural Hindi conversations than an entire world of shallow AI-driven NPCs.