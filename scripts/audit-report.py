#!/usr/bin/env python3
"""Audit report markers against a validated claim ledger and write final-audit.json."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from research_validation import validate


def audit(root: Path, write: bool = True) -> dict:
    root = root.expanduser().resolve()
    result = validate(root)
    errors = list(result["errors"])
    try:
        ledger = json.loads((root / "claim-ledger.json").read_text(encoding="utf-8"))["claims"]
        sources = json.loads((root / "source-register.json").read_text(encoding="utf-8"))["sources"]
        report = (root / "report.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError) as exc:
        errors.append(f"report audit input unavailable ({exc.__class__.__name__})")
        ledger, sources, report = [], [], ""
    paragraphs = [part for part in re.split(r"\n\s*\n", report) if part.strip()]
    for claim in ledger:
        claim_id = claim.get("id")
        matching = [part for part in paragraphs if f"[{claim_id}]" in part]
        if len(matching) != 1:
            errors.append(f"{claim_id}: report must contain exactly one claim marker")
            continue
        paragraph = matching[0]
        for source_id in claim.get("citations", []):
            if f"[{source_id}]" not in paragraph:
                errors.append(f"{claim_id}: citation {source_id} is not adjacent in its report paragraph")
        if claim.get("status") in {"unverified", "conflicted"} and f"[{claim.get('status')}]" not in paragraph.lower():
            errors.append(f"{claim_id}: report must expose {claim.get('status')} status")
    registered = {row.get("url") for row in sources}
    for url in re.findall(r"https://[^\s)>]+", report):
        clean = url.rstrip(".,;]")
        if clean not in registered:
            errors.append(f"report contains unregistered URL host {urlsplit(clean).netloc or 'invalid'}")
    result = {
        "schema": 1,
        "passed": not errors,
        "claims": len(ledger),
        "sources": len(sources),
        "unsupported_claims": sum(1 for row in ledger if row.get("status") == "unverified"),
        "conflicted_claims": sum(1 for row in ledger if row.get("status") == "conflicted"),
        "errors": sorted(set(errors)),
        "limit": "Structural support audit; human review is still required for source truth and entailment.",
    }
    if write:
        (root / "final-audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
