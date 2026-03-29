from __future__ import annotations

import argparse
import json

from .engine import TSVCompressionEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="TSV Compression Research CLI")
    parser.add_argument("--session", default="demo", help="session id")
    args = parser.parse_args()

    engine = TSVCompressionEngine()
    print(f"TSV Compression CLI session={args.session}. Type 'exit' to quit.")

    while True:
        try:
            query = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query or query.lower() in {"exit", "quit"}:
            break
        response = engine.process_query(args.session, query)
        print("\nTSV> " + response.answer)
        print("\n[packed_context]")
        print(response.packed_context.packed_text)
        print("\n[metrics]")
        print(json.dumps(response.metrics.to_dict(), indent=2, ensure_ascii=False))

    archive = engine.get_archive(args.session)
    print("\n[archive]")
    print(json.dumps(archive, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
