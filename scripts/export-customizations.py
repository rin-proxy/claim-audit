#!/usr/bin/env python3
"""Export changed ClaimAudit package files without modifying the installation."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile


SLUG = "claim-audit"
IGNORED = {".git", "node_modules", "__pycache__", ".pytest_cache"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"refusing symlinked package path: {relative}")
        if path.is_file():
            result[str(relative)] = digest(path)
    return result


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o644
    info.mtime = 0
    archive.addfile(info, io.BytesIO(data))


def export(workspace: Path, output: Path) -> dict:
    workspace = workspace.expanduser().resolve()
    target = workspace / "skills" / SLUG
    state = workspace / ".openclaw-skill-state" / SLUG
    receipt_path = state / "receipt.json"
    if workspace == Path("/") or not workspace.is_dir() or target.is_symlink() or state.is_symlink():
        raise ValueError("unsafe or missing workspace")
    if not target.is_dir() or not receipt_path.is_file() or receipt_path.is_symlink():
        raise ValueError("managed ClaimAudit installation and receipt are required")
    receipt = json.loads(receipt_path.read_text())
    baseline = receipt.get("files")
    if not isinstance(baseline, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in baseline.items()):
        raise ValueError("receipt has no valid file inventory")
    current = inventory(target)
    added = sorted(set(current) - set(baseline))
    deleted = sorted(set(baseline) - set(current))
    modified = sorted(path for path in set(current) & set(baseline) if current[path] != baseline[path])
    manifest = {"schema": 1, "skill": SLUG, "added": added, "modified": modified, "deleted": deleted}
    if not any((added, modified, deleted)):
        return {**manifest, "archive": None, "drift": False}
    output = output.expanduser().resolve()
    if output.is_relative_to(target) or output.is_symlink() or output.suffixes[-2:] != [".tar", ".gz"]:
        raise ValueError("output must be a non-symlink .tar.gz path outside the installed package")
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"{SLUG}-customizations"
    with tarfile.open(output, "w:gz") as archive:
        add_bytes(archive, f"{prefix}/manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
        for relative in added + modified:
            data = (target / relative).read_bytes()
            add_bytes(archive, f"{prefix}/files/{relative}", data)
    return {**manifest, "archive": str(output), "drift": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = export(args.workspace, args.output)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, tarfile.TarError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
