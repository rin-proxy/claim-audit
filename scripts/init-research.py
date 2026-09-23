#!/usr/bin/env python3
"""Create an empty research-verifier evidence directory without overwriting files."""
import argparse
import json
from pathlib import Path
import sys


FILES = {
    "research-plan.md": "# Research plan\n\nQuestion:\nScope:\nAs-of time:\nCompletion rule:\n",
    "report.md": "# Research report\n\nDraft claims with adjacent `[Cnnn][Snnn]` markers.\n",
    "claim-ledger.json": json.dumps({"schema": 1, "claims": []}, indent=2) + "\n",
    "source-register.json": json.dumps({"schema": 1, "sources": []}, indent=2) + "\n",
    "contradictions.json": json.dumps({"schema": 1, "contradictions": []}, indent=2) + "\n",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory.expanduser().resolve()
    if root == Path("/"):
        parser.error("refusing filesystem root")
    root.mkdir(parents=True, exist_ok=True)
    conflicts = [name for name in FILES if (root / name).exists()]
    if conflicts:
        print("refusing to overwrite: " + ", ".join(conflicts), file=sys.stderr)
        return 1
    for name, content in FILES.items():
        (root / name).write_text(content, encoding="utf-8")
    print(json.dumps({"status": "INITIALIZED", "directory": str(root), "files": sorted(FILES)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
