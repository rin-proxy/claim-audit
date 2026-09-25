#!/usr/bin/env python3
"""Check the latest stable ClaimAudit release without installing it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPOSITORY = "rin-proxy/claim-audit"
SEMVER = re.compile(r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def version(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value.strip())
    if not match:
        raise ValueError(f"unsupported stable version: {value}")
    return tuple(map(int, match.groups()))


def current_version() -> str:
    match = re.search(r"^version:\s*([^\s]+)\s*$", (ROOT / "SKILL.md").read_text(), re.M)
    if not match:
        raise ValueError("SKILL.md has no version")
    return match.group(1)


def request_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "claim-audit-update-check",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("GitHub returned a non-object response")
    return value


def resolve_tag(repository: str, tag: str) -> str:
    encoded = urllib.parse.quote(tag, safe="")
    value = request_json(f"https://api.github.com/repos/{repository}/git/ref/tags/{encoded}")
    target = value.get("object", {})
    if target.get("type") == "tag":
        target = request_json(f"https://api.github.com/repos/{repository}/git/tags/{target.get('sha')}").get("object", {})
    commit = target.get("sha")
    if target.get("type") != "commit" or not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        raise ValueError("release tag does not resolve to a full commit")
    return commit


def live_release(repository: str) -> dict:
    value = request_json(f"https://api.github.com/repos/{repository}/releases/latest")
    tag = value.get("tag_name")
    url = value.get("html_url")
    if not isinstance(tag, str) or not isinstance(url, str):
        raise ValueError("latest release is missing tag_name or html_url")
    return {"tag_name": tag, "html_url": url, "commit": resolve_tag(repository, tag)}


def load_release(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("release fixture must be an object")
    return value


def build_result(current: str, repository: str, release: dict) -> dict:
    tag = release.get("tag_name")
    commit = release.get("commit")
    url = release.get("html_url")
    if not isinstance(tag, str) or not isinstance(url, str) or not isinstance(commit, str):
        raise ValueError("release is missing tag_name, html_url or commit")
    if not COMMIT.fullmatch(commit):
        raise ValueError("release commit must be a full lowercase SHA-1")
    current_tuple, latest_tuple = version(current), version(tag)
    state = "update-available" if latest_tuple > current_tuple else "current" if latest_tuple == current_tuple else "ahead"
    return {
        "status": state,
        "repository": repository,
        "current_version": current.lstrip("v"),
        "latest_version": tag.lstrip("v"),
        "update_available": state == "update-available",
        "release_url": url,
        "commit": commit,
        "update_command": (
            "bash scripts/update.sh --workspace /absolute/agent/workspace "
            f"--repo https://github.com/{repository}.git --ref {commit}"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--current", default=current_version())
    parser.add_argument("--release-json", type=Path, help="offline release fixture")
    parser.add_argument("--fail-if-update", action="store_true", help="exit 10 when an update is available")
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
            raise ValueError("repository must be OWNER/NAME")
        release = load_release(args.release_json) if args.release_json else live_release(args.repository)
        result = build_result(args.current, args.repository, release)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 10 if args.fail_if_update and result["update_available"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
