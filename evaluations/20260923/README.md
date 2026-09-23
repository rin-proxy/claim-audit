# Isolated evaluation — 2026-09-23

This directory contains the publishable evidence for the initial `research-verifier` comparison.
The planned matrix completed 120 attempts: 20 cases, three repetitions and before/after arms.

- [`cases.json`](cases.json) contains exact synthetic sources, questions and strict expected fields.
- [`results.json`](results.json) contains sanitized per-attempt results and check outcomes.
- [`summary.json`](summary.json) contains aggregate strict, audit, latency and token measures.
- [`interpretation.json`](interpretation.json) preserves strict failures while explaining the
  post-run classification.
- [`PROTOCOL.md`](PROTOCOL.md) records isolation, runtime pins and amendments.

Raw traces are intentionally excluded. OpenClaw traces contain provider reasoning-replay payloads and
are unnecessary to verify the published scores. The sanitized results retain final structured values,
per-field checks, usage, timing, model identity, skill-read evidence and audit outcomes.

The result supports improved auditability. It does not establish universal factual accuracy or an
accuracy improvement over the already strong baseline central answers.
