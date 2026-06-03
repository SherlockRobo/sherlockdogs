from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ingest import write_ingest


def main() -> int:
    parser = argparse.ArgumentParser(prog="sdogs")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="ingest one text payload")
    ingest.add_argument("text")
    ingest.add_argument("--vault", default="./vault")

    ingest_file = sub.add_parser("ingest-file", help="ingest text from a local file")
    ingest_file.add_argument("path")
    ingest_file.add_argument("--vault", default="./vault")

    args = parser.parse_args()
    if args.command == "ingest":
        result = write_ingest(args.text, Path(args.vault))
    else:
        result = write_ingest(Path(args.path).read_text(encoding="utf-8"), Path(args.vault))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

