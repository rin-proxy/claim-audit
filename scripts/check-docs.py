#!/usr/bin/env python3
"""Check declared documentation, local Markdown links and documented CLI flags."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT / "docs-contract.json").read_text())
errors = []

for name in cfg.get("documents", []) + cfg.get("required_files", []):
    if not (ROOT / name).is_file():
        errors.append(f"missing declared file: {name}")

for name in cfg.get("documents", []):
    path = ROOT / name
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
        target = target.split("#", 1)[0]
        if not target or re.match(r"^(https?|mailto):", target):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.exists():
            errors.append(f"{name}: broken local link {target}")

for contract in cfg.get("cli", []):
    source = ROOT / contract["source"]
    document = ROOT / contract["document"]
    if not source.is_file() or not document.is_file():
        continue
    source_text = source.read_text(encoding="utf-8")
    document_text = document.read_text(encoding="utf-8")
    for flag in contract.get("flags", []):
        if flag not in source_text:
            errors.append(f"{contract['source']}: missing declared flag {flag}")
        if flag not in document_text:
            errors.append(f"{contract['document']}: undocumented flag {flag}")

expected = cfg.get("checker_sha256")
if expected and expected != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
    errors.append("documentation checker hash differs from docs-contract.json")

print(json.dumps({"passed": not errors, "errors": errors}, indent=2))
raise SystemExit(0 if not errors else 1)
