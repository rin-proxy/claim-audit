#!/usr/bin/env python3
"""Build a reproducible source archive, manifest, SPDX SBOM and checksums."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def git(*args: str, binary: bool = False):
    process = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, check=True, timeout=60
    )
    return process.stdout if binary else process.stdout.decode().strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_version() -> str:
    match = re.search(r"^version:\s*([^\s]+)\s*$", (ROOT / "SKILL.md").read_text(), re.M)
    if not match:
        raise ValueError("SKILL.md has no version")
    return match.group(1)


def build(output: Path, requested: str) -> dict:
    match = SEMVER.fullmatch(requested)
    if not match:
        raise ValueError("version must be stable semantic version")
    version = ".".join(match.groups())
    if version != skill_version():
        raise ValueError("requested version differs from SKILL.md")
    if git("status", "--porcelain"):
        raise ValueError("release build requires a clean Git checkout")
    commit, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    committed = datetime.fromisoformat(git("show", "-s", "--format=%cI", "HEAD"))
    created = committed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    prefix = f"claim-audit-v{version}"
    archive = output / f"{prefix}.tar.gz"
    git("archive", "--format=tar.gz", f"--prefix={prefix}/", f"--output={archive}", "HEAD")
    paths = [item.decode() for item in git("ls-files", "-z", binary=True).split(b"\0") if item]
    files = [{"path": path, "sha256": sha256(ROOT / path)} for path in paths]
    manifest_path = output / f"{prefix}-source-manifest.json"
    manifest_path.write_text(json.dumps({"schema": 1, "version": version, "commit": commit, "tree": tree, "files": files}, indent=2) + "\n")
    sbom_path = output / f"{prefix}.spdx.json"
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": prefix,
        "documentNamespace": f"https://github.com/rin-proxy/claim-audit/releases/tag/v{version}#{commit}",
        "creationInfo": {"created": created, "creators": ["Tool: claim-audit-build-release-1"]},
        "packages": [{
            "name": "claim-audit",
            "SPDXID": "SPDXRef-Package-ClaimAudit",
            "versionInfo": version,
            "downloadLocation": f"https://github.com/rin-proxy/claim-audit/archive/refs/tags/v{version}.tar.gz",
            "filesAnalyzed": False,
            "licenseConcluded": "Apache-2.0",
            "licenseDeclared": "Apache-2.0",
            "copyrightText": "Copyright 2026 Rin",
            "externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:github/rin-proxy/claim-audit@v{version}",
            }],
        }],
        "relationships": [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": "SPDXRef-Package-ClaimAudit"}],
    }
    sbom_path.write_text(json.dumps(sbom, indent=2) + "\n")
    artifacts = [archive, manifest_path, sbom_path]
    checksums = output / "SHA256SUMS"
    checksums.write_text("".join(f"{sha256(path)}  {path.name}\n" for path in artifacts))
    return {"version": version, "commit": commit, "tree": tree, "artifacts": [str(path) for path in (*artifacts, checksums)]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.output, args.version)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc) if not isinstance(exc, subprocess.SubprocessError) else "Git command failed"}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
