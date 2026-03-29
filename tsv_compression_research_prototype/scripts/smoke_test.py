from __future__ import annotations

import json
import tempfile
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.engine import TSVCompressionEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = TSVCompressionEngine(db_path=str(Path(tmpdir) / "smoke.db"))
        turns = [
            "Project goal: build a TSV research prototype that reduces repeated prompt cost.",
            "Constraint: do not summarize; prefer exact spans and reversible compression.",
            "Please design the experiment and show the memory strategy.",
        ]
        results = []
        for turn in turns:
            results.append(engine.process_query("smoke", turn).to_dict())
        archive = engine.get_archive("smoke")
        print(json.dumps({"results": results, "archive": archive}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
