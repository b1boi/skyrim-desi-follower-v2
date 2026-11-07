"""
latency_trace.py - Pipeline Latency Instrumentation for Skyrim Desi Follower

Records high-resolution monotonic timestamps (via time.perf_counter()) per turn
across the full speech-to-speech interaction pipeline:
- t_mic_open
- t_vad_speech_start
- t_vad_speech_end
- t_asr_start
- t_asr_end
- t_llm_request
- t_llm_first_token
- t_llm_first_sentence_end
- t_llm_stream_end
- t_tts_first_chunk_start
- t_tts_first_chunk_end
- t_tts_all_chunks_end
- t_handoff_write_wav
- t_playback_triggered (marked manual if unobserved in-game)

Computes derived duration metrics (P50/P90/P95 friendly):
- ASR latency
- LLM TTFT (time-to-first-token)
- LLM sentence 1 time
- TTS chunk 1 latency & Real-Time Factor (RTF)
- Backend handoff latency
- Total round-trip latency (player stop speaking -> first audio playable)

Saves traces as newline-delimited JSON (JSONL).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional


# Monotonic clock helper
def clock() -> float:
    return time.perf_counter()


@dataclass
class TurnTrace:
    """Represents a single conversation turn's timing metrics."""
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = "default"
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Metadata
    speaker: str = "NPC"
    input_text: str = ""
    output_text: str = ""
    chunk1_text: str = ""
    audio_duration_first_chunk_s: float = 0.0
    audio_duration_total_s: float = 0.0
    tokens_first_sentence: int = 0
    tokens_total: int = 0
    
    # Monotonic timestamps (seconds from time.perf_counter())
    t_mic_open: Optional[float] = None
    t_vad_speech_start: Optional[float] = None
    t_vad_speech_end: Optional[float] = None
    t_asr_start: Optional[float] = None
    t_asr_end: Optional[float] = None
    t_llm_request: Optional[float] = None
    t_llm_first_token: Optional[float] = None
    t_llm_first_sentence_end: Optional[float] = None
    t_llm_stream_end: Optional[float] = None
    t_tts_first_chunk_start: Optional[float] = None
    t_tts_first_chunk_end: Optional[float] = None
    t_tts_all_chunks_end: Optional[float] = None
    t_handoff_write_wav: Optional[float] = None
    t_playback_triggered: Optional[float] = None
    
    # Flags
    playback_triggered_manual: bool = False
    
    # Extra user metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark(self, event_name: str, ts: Optional[float] = None) -> None:
        """Record an explicit timestamp event."""
        if not hasattr(self, event_name):
            raise AttributeError(f"Unknown trace event '{event_name}'")
        setattr(self, event_name, ts if ts is not None else clock())

    @property
    def asr_latency_ms(self) -> Optional[float]:
        if self.t_asr_start is not None and self.t_asr_end is not None:
            return max(0.0, (self.t_asr_end - self.t_asr_start) * 1000.0)
        return None

    @property
    def vad_speech_duration_ms(self) -> Optional[float]:
        if self.t_vad_speech_start is not None and self.t_vad_speech_end is not None:
            return max(0.0, (self.t_vad_speech_end - self.t_vad_speech_start) * 1000.0)
        return None

    @property
    def llm_ttft_ms(self) -> Optional[float]:
        """Time to First Token (TTFT)."""
        if self.t_llm_request is not None and self.t_llm_first_token is not None:
            return max(0.0, (self.t_llm_first_token - self.t_llm_request) * 1000.0)
        return None

    @property
    def llm_sentence1_time_ms(self) -> Optional[float]:
        """Time until sentence 1 generation completes."""
        if self.t_llm_request is not None and self.t_llm_first_sentence_end is not None:
            return max(0.0, (self.t_llm_first_sentence_end - self.t_llm_request) * 1000.0)
        return None

    @property
    def llm_total_time_ms(self) -> Optional[float]:
        if self.t_llm_request is not None and self.t_llm_stream_end is not None:
            return max(0.0, (self.t_llm_stream_end - self.t_llm_request) * 1000.0)
        return None

    @property
    def tts_chunk1_latency_ms(self) -> Optional[float]:
        """Time to synthesize the first audio chunk."""
        if self.t_tts_first_chunk_start is not None and self.t_tts_first_chunk_end is not None:
            return max(0.0, (self.t_tts_first_chunk_end - self.t_tts_first_chunk_start) * 1000.0)
        return None

    @property
    def tts_chunk1_rtf(self) -> Optional[float]:
        """Real-time factor for first audio chunk: synthesis_time / audio_duration."""
        if (
            self.t_tts_first_chunk_start is not None
            and self.t_tts_first_chunk_end is not None
            and self.audio_duration_first_chunk_s > 0
        ):
            synth_s = self.t_tts_first_chunk_end - self.t_tts_first_chunk_start
            return synth_s / self.audio_duration_first_chunk_s
        return None

    @property
    def tts_total_latency_ms(self) -> Optional[float]:
        if self.t_tts_first_chunk_start is not None and self.t_tts_all_chunks_end is not None:
            return max(0.0, (self.t_tts_all_chunks_end - self.t_tts_first_chunk_start) * 1000.0)
        return None

    @property
    def handoff_latency_ms(self) -> Optional[float]:
        """Time between first audio ready and file written to game directory."""
        if self.t_tts_first_chunk_end is not None and self.t_handoff_write_wav is not None:
            return max(0.0, (self.t_handoff_write_wav - self.t_tts_first_chunk_end) * 1000.0)
        return None

    @property
    def total_roundtrip_ms(self) -> Optional[float]:
        """
        Total speech-to-speech round-trip latency:
        From player finish speaking (t_vad_speech_end or t_asr_end)
        to first audio playable (t_handoff_write_wav or t_playback_triggered).
        """
        end_ref = self.t_playback_triggered or self.t_handoff_write_wav
        start_ref = self.t_vad_speech_end or self.t_asr_end or self.t_llm_request
        if end_ref is not None and start_ref is not None:
            return max(0.0, (end_ref - start_ref) * 1000.0)
        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Return all computed duration metrics."""
        return {
            "vad_speech_duration_ms": self.vad_speech_duration_ms,
            "asr_latency_ms": self.asr_latency_ms,
            "llm_ttft_ms": self.llm_ttft_ms,
            "llm_sentence1_time_ms": self.llm_sentence1_time_ms,
            "llm_total_time_ms": self.llm_total_time_ms,
            "tts_chunk1_latency_ms": self.tts_chunk1_latency_ms,
            "tts_chunk1_rtf": self.tts_chunk1_rtf,
            "tts_total_latency_ms": self.tts_total_latency_ms,
            "handoff_latency_ms": self.handoff_latency_ms,
            "total_roundtrip_ms": self.total_roundtrip_ms,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the trace including both raw timestamps and computed metrics."""
        data = asdict(self)
        data["metrics"] = self.get_metrics()
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class TurnTracer:
    """Session-level tracer that manages active turns and appends to JSONL."""

    def __init__(self, jsonl_path: Optional[str | Path] = None, session_id: str = "default"):
        self.session_id = session_id
        self.jsonl_path = Path(jsonl_path) if jsonl_path else None
        if self.jsonl_path:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self.active_turn: Optional[TurnTrace] = None
        self.completed_turns: list[TurnTrace] = []

    def start_turn(self, turn_id: Optional[str] = None, **kwargs) -> TurnTrace:
        """Starts a new trace turn."""
        self.active_turn = TurnTrace(
            turn_id=turn_id or str(uuid.uuid4())[:8],
            session_id=self.session_id,
            **kwargs,
        )
        return self.active_turn

    def mark(self, event_name: str, ts: Optional[float] = None) -> None:
        """Mark an event on the active turn."""
        if not self.active_turn:
            self.start_turn()
        assert self.active_turn is not None
        self.active_turn.mark(event_name, ts)

    @contextmanager
    def stage(self, stage_name: str) -> Iterator[TurnTrace]:
        """
        Convenience context manager to record standard stage boundaries.
        Supported stages:
        - 'vad': marks t_vad_speech_start / t_vad_speech_end
        - 'asr': marks t_asr_start / t_asr_end
        - 'llm': marks t_llm_request / t_llm_stream_end
        - 'tts_chunk1': marks t_tts_first_chunk_start / t_tts_first_chunk_end
        - 'tts_all': marks t_tts_first_chunk_start / t_tts_all_chunks_end
        """
        if not self.active_turn:
            self.start_turn()
        assert self.active_turn is not None

        start_map = {
            "vad": "t_vad_speech_start",
            "asr": "t_asr_start",
            "llm": "t_llm_request",
            "tts_chunk1": "t_tts_first_chunk_start",
            "tts_all": "t_tts_first_chunk_start",
        }
        end_map = {
            "vad": "t_vad_speech_end",
            "asr": "t_asr_end",
            "llm": "t_llm_stream_end",
            "tts_chunk1": "t_tts_first_chunk_end",
            "tts_all": "t_tts_all_chunks_end",
        }

        if stage_name in start_map:
            self.active_turn.mark(start_map[stage_name])
        try:
            yield self.active_turn
        finally:
            if stage_name in end_map:
                self.active_turn.mark(end_map[stage_name])

    def finish_turn(self, **kwargs) -> TurnTrace:
        """Finalizes the active turn, updates metadata, and writes to JSONL."""
        if not self.active_turn:
            raise RuntimeError("No active turn to finish")

        for k, v in kwargs.items():
            if hasattr(self.active_turn, k):
                setattr(self.active_turn, k, v)
            else:
                self.active_turn.metadata[k] = v

        turn = self.active_turn
        self.completed_turns.append(turn)
        self.active_turn = None

        if self.jsonl_path:
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(turn.to_json() + "\n")

        return turn

