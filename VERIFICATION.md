# Verification

## Deterministic acceptance

Run `bash test.sh`, `bash examples/quickstart.sh`, and `python3 scripts/check-docs.py` from a clean
checkout. Success requires unit tests, lifecycle preservation, vendor hashes, shell syntax, the
synthetic evidence audit and documentation contracts to pass without credentials or network access.

Negative fixtures must reject duplicate evidence families presented as independent corroboration,
missing adjacent citations, unregistered report URLs and destructive initialization.

## Isolated OpenClaw acceptance

Use a temporary workspace and the same OpenClaw version, model, reasoning level, tools, task fixtures
and timeout for both arms. The before arm excludes this skill; the after arm installs it. Use fresh
sessions and reset fixtures for every attempt. Retain attempted failures and timeouts.

The evaluation includes primary-versus-secondary evidence, syndicated sources, stale facts,
conflicting values, insufficient evidence, causal overreach, exact numeric claims and adjacent
citations. Score factual correctness, citation entailment, unsupported claims, fabricated citations,
conflict disclosure, abstention and temporal correctness. Token and latency results are secondary.

Do not infer universal accuracy from synthetic tasks, one transcript, a passing packaging test or
agreement among same-model agents. Record exact source and runtime pins in `BENCHMARK.md`.

## Lifecycle E2E

On an isolated workspace, verify install, status, reinstall, a pinned update from a local Git fixture,
rollback and uninstall. Owner instructions and owner memory must remain unchanged. After GitHub merge,
clone the exact `main` commit into a fresh directory and repeat deterministic tests and quickstart.
