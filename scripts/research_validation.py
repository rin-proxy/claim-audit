#!/usr/bin/env python3
"""Deterministic validation for research-verifier evidence artifacts."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

CLAIM_ID = re.compile(r"C[0-9]{3,}")
SOURCE_ID = re.compile(r"S[0-9]{3,}")
CONFLICT_ID = re.compile(r"X[0-9]{3,}")
STATUSES = {"verified", "supported", "inference", "conflicted", "unverified", "refuted"}
KINDS = {"fact", "current_fact", "number", "inference", "opinion"}
SOURCE_TYPES = {"official", "primary", "peer_reviewed", "preprint", "independent_reporting", "community", "opinion"}
ELIGIBLE = {"official", "primary", "peer_reviewed", "preprint", "independent_reporting"}
PRIMARY = {"official", "primary", "peer_reviewed"}


def load_object(path: Path, key: str, errors: list[str]) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path.name}: unreadable JSON ({exc.__class__.__name__})")
        return []
    if not isinstance(value, dict) or value.get("schema") != 1 or not isinstance(value.get(key), list):
        errors.append(f"{path.name}: expected schema=1 and array {key}")
        return []
    if not all(isinstance(row, dict) for row in value[key]):
        errors.append(f"{path.name}: every {key} entry must be an object")
        return []
    return value[key]


def iso8601(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def unique(rows: list[dict], pattern: re.Pattern[str], label: str, errors: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        identity = row.get("id")
        if not isinstance(identity, str) or pattern.fullmatch(identity) is None:
            errors.append(f"{label}: invalid id {identity!r}")
        elif identity in result:
            errors.append(f"{label}: duplicate id {identity}")
        else:
            result[identity] = row
    return result


def validate(root: Path) -> dict:
    root = root.resolve()
    errors: list[str] = []
    sources = unique(load_object(root / "source-register.json", "sources", errors), SOURCE_ID, "source", errors)
    claims = unique(load_object(root / "claim-ledger.json", "claims", errors), CLAIM_ID, "claim", errors)
    conflicts = unique(load_object(root / "contradictions.json", "contradictions", errors), CONFLICT_ID, "contradiction", errors)

    for identity, row in sources.items():
        for field in ("url", "title", "publisher", "source_type", "independent_group"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{identity}: missing {field}")
        try:
            parsed = urlsplit(row.get("url", ""))
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{identity}: url must be canonical HTTPS")
        except ValueError:
            errors.append(f"{identity}: invalid url")
        if row.get("source_type") not in SOURCE_TYPES:
            errors.append(f"{identity}: invalid source_type")
        if row.get("retrieved") is not True:
            errors.append(f"{identity}: retrieved must be true before citation")
        if not iso8601(row.get("accessed_at")):
            errors.append(f"{identity}: accessed_at must be ISO-8601")

    conflicted_claims: set[str] = set()
    for identity, row in conflicts.items():
        claim_ids = row.get("claim_ids")
        source_ids = row.get("source_ids")
        if not isinstance(claim_ids, list) or not claim_ids:
            errors.append(f"{identity}: claim_ids must be non-empty")
            claim_ids = []
        if not isinstance(source_ids, list) or len(source_ids) < 2:
            errors.append(f"{identity}: source_ids must contain at least two sources")
            source_ids = []
        for claim_id in claim_ids:
            if claim_id not in claims:
                errors.append(f"{identity}: unknown claim {claim_id}")
            else:
                conflicted_claims.add(claim_id)
        for source_id in source_ids:
            if source_id not in sources:
                errors.append(f"{identity}: unknown source {source_id}")
        if row.get("resolution_status") not in {"resolved", "unresolved"}:
            errors.append(f"{identity}: invalid resolution_status")
        if not isinstance(row.get("summary"), str) or not row["summary"].strip():
            errors.append(f"{identity}: summary is required")
        if row.get("disclosed_in_report") is not True:
            errors.append(f"{identity}: conflict must be disclosed in report")

    for identity, row in claims.items():
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            errors.append(f"{identity}: text is required")
        kind = row.get("kind")
        status = row.get("status")
        if kind not in KINDS:
            errors.append(f"{identity}: invalid kind")
        if status not in STATUSES:
            errors.append(f"{identity}: invalid status")
        citations = row.get("citations")
        evidence = row.get("evidence")
        if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
            errors.append(f"{identity}: citations must be an array of source IDs")
            citations = []
        if len(citations) != len(set(citations)):
            errors.append(f"{identity}: duplicate citation")
        if not isinstance(evidence, list) or not all(isinstance(item, dict) for item in evidence):
            errors.append(f"{identity}: evidence must be an array of objects")
            evidence = []
        for source_id in citations:
            if source_id not in sources:
                errors.append(f"{identity}: unknown citation {source_id}")
        supporting: set[str] = set()
        contradicting: set[str] = set()
        for item in evidence:
            source_id = item.get("source_id")
            relation = item.get("relation")
            if source_id not in sources:
                errors.append(f"{identity}: evidence has unknown source {source_id}")
            if source_id not in citations:
                errors.append(f"{identity}: evidence source {source_id} is not cited")
            if relation not in {"supports", "contradicts"}:
                errors.append(f"{identity}: evidence relation must support or contradict")
            elif relation == "supports":
                supporting.add(source_id)
            else:
                contradicting.add(source_id)
            for field in ("locator", "excerpt"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    errors.append(f"{identity}: evidence {field} is required")
        eligible_support = [sources[s] for s in supporting if s in sources and sources[s].get("source_type") in ELIGIBLE]
        groups = {s.get("independent_group") for s in eligible_support if s.get("independent_group")}
        if status == "verified" and not (any(s.get("source_type") in PRIMARY for s in eligible_support) or len(groups) >= 2):
            errors.append(f"{identity}: verified requires primary evidence or two independent eligible groups")
        if status == "supported" and not eligible_support:
            errors.append(f"{identity}: supported requires retrieved eligible support")
        if status == "refuted" and not contradicting:
            errors.append(f"{identity}: refuted requires contradicting evidence")
        if status == "conflicted" and identity not in conflicted_claims:
            errors.append(f"{identity}: conflicted claim requires a contradiction record")
        if kind == "current_fact" and not iso8601(row.get("checked_at")):
            errors.append(f"{identity}: current_fact requires checked_at")
        if kind in {"fact", "current_fact", "number"} and status in {"verified", "supported"} and not citations:
            errors.append(f"{identity}: supported factual claim requires citations")

    return {
        "schema": 1,
        "passed": not errors,
        "claims": len(claims),
        "sources": len(sources),
        "contradictions": len(conflicts),
        "errors": sorted(set(errors)),
    }
