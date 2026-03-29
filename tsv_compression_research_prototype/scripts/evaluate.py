from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

import yaml

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.compressor import compress_messages_lossless
from app.embeddings import estimate_tokens
from app.engine import TSVCompressionEngine
from app.memory import utc_now
from app.models import Message


def run_full_history_baseline(turns: list[str]) -> dict[str, Any]:
    history: list[str] = []
    total_input_tokens = 0
    total_output_tokens = 0
    for turn in turns:
        history.append(turn)
        prompt = "\n".join(history)
        total_input_tokens += estimate_tokens(prompt)
        answer = f"[full-history] answer for: {turn}"
        total_output_tokens += estimate_tokens(answer)
    return {
        "name": "full_history",
        "estimated_input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
    }


def run_lossy_summary_baseline(turns: list[str]) -> dict[str, Any]:
    summary = ""
    total_input_tokens = 0
    total_output_tokens = 0
    for turn in turns:
        summary = (summary + " " + turn).strip()[:180]
        prompt = f"SUMMARY:{summary}\nQUERY:{turn}"
        total_input_tokens += estimate_tokens(prompt)
        answer = f"[lossy-summary] answer for: {turn}"
        total_output_tokens += estimate_tokens(answer)
    return {
        "name": "lossy_summary",
        "estimated_input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
        "note": "This baseline is intentionally lossy because it rewrites history into a short summary.",
    }


def run_exact_pack(turns: list[str]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = TSVCompressionEngine(db_path=str(Path(tmpdir) / "eval.db"))
        total_input_tokens = 0
        total_output_tokens = 0
        cache_hits = 0
        last_archive = None
        answers: list[str] = []
        for turn in turns:
            result = engine.process_query("eval", turn)
            total_input_tokens += result.metrics.estimated_input_tokens
            total_output_tokens += result.metrics.estimated_output_tokens
            cache_hits += 1 if result.cache_hit else 0
            last_archive = result.archive_metrics.to_dict()
            answers.append(result.answer)
        return {
            "name": "extractive_exact_pack",
            "estimated_input_tokens": total_input_tokens,
            "estimated_output_tokens": total_output_tokens,
            "cache_hits": cache_hits,
            "final_archive_metrics": last_archive,
            "answers": answers,
        }


def run_storage_lossless(turns: list[str]) -> dict[str, Any]:
    messages = [Message(role="user", content=turn, created_at=utc_now()) for turn in turns]
    _, metrics = compress_messages_lossless(messages)
    return {
        "name": "storage_lossless",
        **metrics.to_dict(),
        "note": "This is true lossless compression for storage/archive, verified by round-trip decompression.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()

    data = yaml.safe_load(Path(args.dataset).read_text(encoding="utf-8"))
    turns = data["turns"]

    baseline = run_full_history_baseline(turns)
    lossy = run_lossy_summary_baseline(turns)
    exact_pack = run_exact_pack(turns)
    storage = run_storage_lossless(turns)

    report = {
        "dataset": args.dataset,
        "results": {
            "baseline": baseline,
            "lossy_summary": lossy,
            "exact_pack": exact_pack,
            "storage_lossless": storage,
        },
        "comparison": {
            "exact_pack_reduction_vs_full_history": baseline["estimated_input_tokens"] - exact_pack["estimated_input_tokens"],
            "lossy_summary_reduction_vs_full_history": baseline["estimated_input_tokens"] - lossy["estimated_input_tokens"],
            "baseline_input_tokens": baseline["estimated_input_tokens"],
            "exact_pack_input_tokens": exact_pack["estimated_input_tokens"],
            "lossy_summary_input_tokens": lossy["estimated_input_tokens"],
        },
        "interpretation": {
            "lossy_summary": "Rewrites history; cheaper but information can be lost.",
            "exact_pack": "Does not paraphrase selected evidence spans; loss comes only from not selecting every span.",
            "storage_lossless": "Bit-exact archive compression; no information loss after decompression.",
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
