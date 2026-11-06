#!/usr/bin/env bash
""":"
exec /home/bepis/git/skyrim-desi-follower-v2/.venv/bin/python "$0" "$@"
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


METRIC_LABELS = {
    "vad_speech_duration_ms": ("VAD Speech Duration", "ms"),
    "asr_latency_ms": ("ASR Decode Latency", "ms"),
    "llm_ttft_ms": ("LLM TTFT (First Token)", "ms"),
    "llm_sentence1_time_ms": ("LLM Sentence 1 Generation", "ms"),
    "llm_total_time_ms": ("LLM Total Stream Time", "ms"),
    "tts_chunk1_latency_ms": ("TTS Chunk 1 Latency", "ms"),
    "tts_chunk1_rtf": ("TTS Chunk 1 Real-Time Factor", "x"),
    "tts_total_latency_ms": ("TTS Total Latency", "ms"),
    "handoff_latency_ms": ("Handoff Latency (WAV Write)", "ms"),
    "total_roundtrip_ms": ("Total S2S Round-Trip Latency", "ms"),
}


def compute_percentiles(values: List[float], percentiles: List[float]) -> Dict[float, float]:
    """Computes percentiles using linear interpolation (matching numpy default)."""
    if not values:
        return {p: float("nan") for p in percentiles}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    results = {}
    for p in percentiles:
        if n == 1:
            results[p] = sorted_vals[0]
            continue
        k = (p / 100.0) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            results[p] = sorted_vals[int(k)]
        else:
            d0 = sorted_vals[int(f)] * (c - k)
            d1 = sorted_vals[int(c)] * (k - f)
            results[p] = d0 + d1
    return results


def summarize_metric(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0}
    n = len(values)
    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    std_val = math.sqrt(variance)
    min_val = min(values)
    max_val = max(values)
    pcts = compute_percentiles(values, [50.0, 90.0, 95.0])

    return {
        "count": n,
        "mean": mean_val,
        "std": std_val,
        "min": min_val,
        "p50": pcts[50.0],
        "p90": pcts[90.0],
        "p95": pcts[95.0],
        "max": max_val,
    }


def parse_trace_file(file_path: Path) -> List[Dict[str, Any]]:
    records = []
    if not file_path.exists():
        raise FileNotFoundError(f"Trace file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(data)
            except json.JSONDecodeError as e:
                print(f"[WARN] Skipping malformed JSON line {line_no}: {e}", file=sys.stderr)
    return records


def generate_report(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    extracted: Dict[str, List[float]] = {k: [] for k in METRIC_LABELS}

    for record in records:
        metrics = record.get("metrics", {})
        for metric_key in METRIC_LABELS:
            val = metrics.get(metric_key)
            if val is not None and isinstance(val, (int, float)) and not math.isnan(val):
                extracted[metric_key].append(float(val))

    summary: Dict[str, Dict[str, Any]] = {}
    for metric_key, values in extracted.items():
        summary[metric_key] = summarize_metric(values)

    return summary


def format_markdown_table(summary: Dict[str, Dict[str, Any]], session_count: int) -> str:
    lines = [
        f"# Phase 0 Pipeline Latency Report",
        f"",
        f"**Total Evaluated Turns**: {session_count}",
        f"",
        "| Metric | Unit | N | Mean | Std | Min | P50 (Med) | P90 | P95 | Max |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for key, (label, unit) in METRIC_LABELS.items():
        stats = summary.get(key, {})
        cnt = stats.get("count", 0)
        if cnt == 0:
            lines.append(f"| {label} | {unit} | 0 | - | - | - | - | - | - | - |")
            continue

        mean_str = f"{stats['mean']:.2f}"
        std_str = f"{stats['std']:.2f}"
        min_str = f"{stats['min']:.2f}"
        p50_str = f"**{stats['p50']:.2f}**"
        p90_str = f"{stats['p90']:.2f}"
        p95_str = f"**{stats['p95']:.2f}**"
        max_str = f"{stats['max']:.2f}"

        lines.append(
            f"| {label} | {unit} | {cnt} | {mean_str} | {std_str} | {min_str} | {p50_str} | {p90_str} | {p95_str} | {max_str} |"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze turn latency JSONL and compute P50/P90/P95 report.")
    parser.add_argument("trace_file", type=str, help="Path to the JSONL trace file")
    parser.add_argument("--format", choices=["markdown", "json", "text"], default="markdown", help="Output format")
    parser.add_argument("--output", type=str, default=None, help="Output file path (default: stdout)")

    args = parser.parse_args()
    trace_path = Path(args.trace_file)

    records = parse_trace_file(trace_path)
    summary = generate_report(records)

    if args.format == "json":
        output_text = json.dumps({"turns": len(records), "metrics": summary}, indent=2)
    elif args.format in ("markdown", "text"):
        output_text = format_markdown_table(summary, len(records))

    if args.output:
        out_file = Path(args.output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(output_text + "\n")
        print(f"[INFO] Latency report written to {out_file}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
