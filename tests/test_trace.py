import json
import os
import subprocess
import tempfile
from pathlib import Path
from src.trace import TurnTrace, TurnTracer
from scripts.latency_report import compute_percentiles, summarize_metric, generate_report, format_markdown_table


def test_turn_trace_metrics_calculation():
    trace = TurnTrace(
        turn_id="turn-001",
        speaker="Sarkaar Bhaiya",
        audio_duration_first_chunk_s=1.2,
        t_vad_speech_start=10.0,
        t_vad_speech_end=11.5,
        t_asr_start=11.5,
        t_asr_end=11.75,
        t_llm_request=11.75,
        t_llm_first_token=11.95,
        t_llm_first_sentence_end=12.10,
        t_llm_stream_end=12.50,
        t_tts_first_chunk_start=12.10,
        t_tts_first_chunk_end=12.46,
        t_tts_all_chunks_end=12.90,
        t_handoff_write_wav=12.48,
    )

    metrics = trace.get_metrics()
    assert abs(metrics["vad_speech_duration_ms"] - 1500.0) < 1e-4
    assert abs(metrics["asr_latency_ms"] - 250.0) < 1e-4
    assert abs(metrics["llm_ttft_ms"] - 200.0) < 1e-4
    assert abs(metrics["llm_sentence1_time_ms"] - 350.0) < 1e-4
    assert abs(metrics["llm_total_time_ms"] - 750.0) < 1e-4
    assert abs(metrics["tts_chunk1_latency_ms"] - 360.0) < 1e-4
    # RTF = 0.36s synth / 1.2s audio = 0.30
    assert abs(metrics["tts_chunk1_rtf"] - 0.30) < 1e-4
    # Handoff = 12.48 - 12.46 = 20ms
    assert abs(metrics["handoff_latency_ms"] - 20.0) < 1e-4
    # Total roundtrip = 12.48 (write wav) - 11.5 (vad speech end) = 980ms
    assert abs(metrics["total_roundtrip_ms"] - 980.0) < 1e-4


def test_turn_tracer_stages_and_jsonl_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        jsonl_path = Path(tmpdir) / "test_traces.jsonl"
        tracer = TurnTracer(jsonl_path=jsonl_path, session_id="smoke_test")

        # Turn 1
        tracer.start_turn(speaker="Sarkaar Bhaiya", input_text="Hello", audio_duration_first_chunk_s=1.0)
        with tracer.stage("vad"):
            pass
        with tracer.stage("asr"):
            pass
        with tracer.stage("llm"):
            tracer.mark("t_llm_first_token")
            tracer.mark("t_llm_first_sentence_end")
        with tracer.stage("tts_chunk1"):
            pass
        tracer.mark("t_handoff_write_wav")
        turn1 = tracer.finish_turn(output_text="Bhaiyo aur behno!")

        assert turn1.t_vad_speech_start is not None
        assert turn1.t_vad_speech_end is not None
        assert turn1.t_llm_first_token is not None
        assert turn1.output_text == "Bhaiyo aur behno!"

        # Verify JSONL file exists and is readable
        assert jsonl_path.exists()
        lines = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").strip().split("\n")]
        assert len(lines) == 1
        assert lines[0]["turn_id"] == turn1.turn_id
        assert lines[0]["speaker"] == "Sarkaar Bhaiya"
        assert "metrics" in lines[0]


def test_percentile_computation():
    vals = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    pcts = compute_percentiles(vals, [50.0, 90.0, 95.0])
    assert abs(pcts[50.0] - 55.0) < 1e-4
    assert abs(pcts[90.0] - 91.0) < 1e-4
    assert abs(pcts[95.0] - 95.5) < 1e-4

    summary = summarize_metric(vals)
    assert summary["count"] == 10
    assert summary["min"] == 10.0
    assert summary["max"] == 100.0
    assert abs(summary["mean"] - 55.0) < 1e-4


def test_latency_report_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        jsonl_path = Path(tmpdir) / "traces.jsonl"
        tracer = TurnTracer(jsonl_path=jsonl_path)
        for i in range(5):
            t = tracer.start_turn(audio_duration_first_chunk_s=1.0)
            t.mark("t_vad_speech_start", 10.0 + i)
            t.mark("t_vad_speech_end", 11.0 + i)
            t.mark("t_asr_start", 11.0 + i)
            t.mark("t_asr_end", 11.2 + i)
            t.mark("t_llm_request", 11.2 + i)
            t.mark("t_llm_first_token", 11.4 + i)
            t.mark("t_llm_first_sentence_end", 11.5 + i)
            t.mark("t_llm_stream_end", 11.7 + i)
            t.mark("t_tts_first_chunk_start", 11.5 + i)
            t.mark("t_tts_first_chunk_end", 11.8 + i)
            t.mark("t_tts_all_chunks_end", 12.0 + i)
            t.mark("t_handoff_write_wav", 11.82 + i)
            tracer.finish_turn()

        # Run latency_report.py
        cmd = [
            "/home/bepis/git/skyrim-desi-follower-v2/.venv/bin/python",
            "/home/bepis/git/skyrim-desi-follower-v2/scripts/latency_report.py",
            str(jsonl_path),
            "--format", "markdown"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        assert "# Phase 0 Pipeline Latency Report" in res.stdout
        assert "Total Evaluated Turns" in res.stdout
        assert "5" in res.stdout
        assert "LLM TTFT" in res.stdout
