# Compatibility

ClaimAudit 2.1 targets Linux, Bash, Git, Python 3.11–3.13 and OpenClaw 2026.9.3. Offline validators
use only Python's standard library. Python 3.14 is also exercised locally but is not part of the
required CI matrix. Model behavior is evaluated separately with the runtime, model, reasoning and
retrieval tools recorded in `BENCHMARK.md`.

Other OpenClaw versions may discover the Markdown instructions but are not covered until the same
functional and behavioral checks are repeated. The skill does not provide a search API or browser.
The Standard Fast Path uses only Python's standard library and adds no runtime dependency.
