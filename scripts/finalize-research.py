#!/usr/bin/env python3
"""Render one evidence pack into audited research artifacts with drift-safe replacement."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


MANIFEST = ".claim-audit-render.json"
LEGACY_MANIFEST = ".research-verifier-render.json"
MANAGED = (
    "research-plan.md",
    "source-register.json",
    "claim-ledger.json",
    "contradictions.json",
    "report.md",
    "final-audit.json",
)
MARKER = re.compile(r"\[(?:C|S)[0-9]{3,}\]")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_pack(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ValueError("evidence pack must be an object with schema=1")
    for key in ("plan", "sources", "claims", "contradictions", "report"):
        if key not in value:
            raise ValueError(f"evidence pack is missing {key}")
    if not isinstance(value["plan"], dict) or not isinstance(value["report"], dict):
        raise ValueError("plan and report must be objects")
    if not all(isinstance(value[key], list) for key in ("sources", "claims", "contradictions")):
        raise ValueError("sources, claims and contradictions must be arrays")
    return value, raw


def require_text(row: dict, field: str, owner: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner}.{field} must be non-empty text")
    return value.strip()


def render(pack: dict) -> dict[str, bytes]:
    plan = pack["plan"]
    plan_text = "# Research plan\n\n" + "\n".join((
        f"Question: {require_text(plan, 'question', 'plan')}",
        f"Scope: {require_text(plan, 'scope', 'plan')}",
        f"As-of time: {require_text(plan, 'as_of_time', 'plan')}",
        f"Completion rule: {require_text(plan, 'completion_rule', 'plan')}",
    )) + "\n"

    claims = pack["claims"]
    claim_ids = [row.get("id") for row in claims if isinstance(row, dict)]
    if len(claim_ids) != len(claims) or any(not isinstance(identity, str) for identity in claim_ids):
        raise ValueError("every claim must be an object with an id")
    by_id = {row["id"]: row for row in claims}
    if len(by_id) != len(claims):
        raise ValueError("claim ids must be unique")

    report = pack["report"]
    title = require_text(report, "title", "report")
    sections = report.get("sections")
    if not isinstance(sections, list) or not all(isinstance(row, dict) for row in sections):
        raise ValueError("report.sections must be an array of objects")
    section_ids = [row.get("claim_id") for row in sections]
    if len(section_ids) != len(set(section_ids)) or set(section_ids) != set(by_id):
        raise ValueError("report.sections must cover every claim exactly once")
    paragraphs = []
    for section in sections:
        identity = section["claim_id"]
        text = require_text(section, "text", f"report section {identity}")
        if MARKER.search(text):
            raise ValueError(f"report section {identity} must not author claim/source markers")
        claim = by_id[identity]
        citations = claim.get("citations")
        if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
            raise ValueError(f"claim {identity} citations must be an array of source ids")
        markers = f"[{identity}]" + "".join(f"[{source}]" for source in citations)
        status = claim.get("status")
        suffix = f" [{status}]" if status in {"unverified", "conflicted"} else ""
        paragraphs.append(f"{text} {markers}{suffix}")
    report_text = f"# {title}\n\n" + "\n\n".join(paragraphs) + "\n"

    json_files = {
        "source-register.json": {"schema": 1, "sources": pack["sources"]},
        "claim-ledger.json": {"schema": 1, "claims": claims},
        "contradictions.json": {"schema": 1, "contradictions": pack["contradictions"]},
    }
    files = {
        "research-plan.md": plan_text.encode(),
        "report.md": report_text.encode(),
    }
    files.update({name: (json.dumps(value, indent=2) + "\n").encode() for name, value in json_files.items()})
    return files


def existing_manifest(root: Path) -> dict:
    path = root / MANIFEST
    if not path.exists() and (root / LEGACY_MANIFEST).exists():
        path = root / LEGACY_MANIFEST
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"managed replacement requires a readable render manifest ({exc.__class__.__name__})") from exc
    if value.get("schema") != 1 or not isinstance(value.get("files"), dict):
        raise ValueError(f"invalid render manifest: {path.name}")
    return value


def verify_replace(root: Path) -> None:
    manifest = existing_manifest(root)
    for name in MANAGED:
        path = root / name
        expected = manifest["files"].get(name)
        if path.is_symlink() or not path.is_file() or not isinstance(expected, str):
            raise ValueError(f"managed artifact is missing or unsafe: {name}")
        if digest(path.read_bytes()) != expected:
            raise ValueError(f"managed artifact has owner drift: {name}")


def finalize(pack_path: Path, root: Path, replace: bool = False) -> dict:
    pack_path = pack_path.expanduser().resolve()
    root = root.expanduser().resolve()
    if root == Path("/") or root.is_symlink():
        raise ValueError("unsafe output directory")
    pack, raw = read_pack(pack_path)
    rendered = render(pack)
    root.mkdir(parents=True, exist_ok=True)
    if replace:
        verify_replace(root)
    else:
        conflicts = [name for name in (*MANAGED, MANIFEST, LEGACY_MANIFEST) if (root / name).exists()]
        if conflicts:
            raise ValueError("refusing to overwrite managed artifacts: " + ", ".join(conflicts))

    temporary = Path(tempfile.mkdtemp(prefix=".claim-audit-render-", dir=root.parent))
    try:
        for name, data in rendered.items():
            (temporary / name).write_bytes(data)
        audit_script = Path(__file__).with_name("audit-report.py")
        process = subprocess.run(
            [sys.executable, str(audit_script), str(temporary)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        audit = json.loads((temporary / "final-audit.json").read_text(encoding="utf-8"))
        files = {name: digest((temporary / name).read_bytes()) for name in MANAGED}
        manifest = {
            "schema": 1,
            "pack_sha256": digest(raw),
            "files": files,
        }
        (temporary / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for name in (*MANAGED, MANIFEST):
            os.replace(temporary / name, root / name)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
    return {
        "status": "PASS" if process.returncode == 0 else "FAIL",
        "directory": str(root),
        "audit": audit,
        "replaced": replace,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--replace-managed", action="store_true")
    args = parser.parse_args()
    try:
        result = finalize(args.pack, args.directory, args.replace_managed)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
