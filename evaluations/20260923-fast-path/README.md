# Standard Fast Path evaluation — 2026-09-23

This directory contains publishable evidence for the `research-verifier` 1.0 control versus the 1.1
Standard Fast Path candidate. The planned matrix completed 120 attempts: 20 synthetic cases, three
repetitions and two arms.

- [`../20260923/cases.json`](../20260923/cases.json) contains the unchanged cases, source fixtures and
  frozen expected fields.
- [`results.json`](results.json) contains sanitized per-attempt measurements and check outcomes.
- [`summary.json`](summary.json) contains aggregate accuracy, audit, latency and token measures.
- [`interpretation.json`](interpretation.json) preserves strict mismatches and records the post-run
  acceptance review.
- [`PROTOCOL.md`](PROTOCOL.md) records isolation, exact behavior commits and the quota amendment.

Raw traces are excluded because OpenClaw traces contain provider reasoning-replay payloads. The
sanitized results retain structured values, per-field checks, usage, timing, model identity,
skill-read evidence and audit outcomes.

The candidate preserved the audited research contract while reducing median wall time, mean total
tokens and mean model calls by more than 30 percent. The evaluation does not establish universal
factual accuracy.
