# research-verifier

Turn external research into an inspectable claim-and-source record before presenting conclusions.
The skill distinguishes evidence, inference, unresolved conflict and missing support; its validators
check structure and citation linkage without pretending to determine real-world truth.

Navigation: [When to use it](#when-to-use-it) · [Expected result](#expected-result) · [Quick start](#quick-start) · [OpenClaw use](#using-it-from-openclaw) · [Artifacts](#artifacts-and-completion) · [Commands](#commands) · [Install](#install-and-verify) · [Recovery](#update-rollback-and-remove) · [Validation](#validation) · [Limits](#limits) · [Integration](#integration)

## When to use it

Use it for fact-checking, time-sensitive information, source comparisons, cited research, or a
decision whose factual premises must be traceable. Direct computation and questions fully answered
by user-supplied material do not need this workflow. A narrow official-doc lookup can use Quick mode;
multiple material claims use Standard mode; broad or conflicting evidence uses Deep mode.

## Expected result

Example request: **“Compare these two synthetic reports, preserve their disagreement, and state what
can actually be verified.”**

Expected behavior: the answer cites retrieved sources beside each material claim, labels unresolved
conflict, and produces a passing structural audit. A passing audit proves traceability rules were
met; it does not independently prove that a source is honest or correct.

## Quick start

From a reviewed checkout:

```bash
bash examples/quickstart.sh
```

The example creates a private temporary directory, writes one synthetic source and claim, validates
their relationship, and checks the final report. It prints the artifact directory and ends with
`Quickstart passed: research-verifier`. It does not use the network, a model, or production data.

## Using it from OpenClaw

The installer places the package at `skills/research-verifier` in an explicitly selected workspace
and adds a managed instruction pointer. Ask the selected agent to research or verify an external
claim. The agent reads `SKILL.md`, chooses the smallest sufficient depth, and uses whatever authorized
search/retrieval tools are available. The skill does not add a browser, search API, model provider,
channel, scheduler, or background service.

Quick and Standard research use one agent by default. Deep research may divide genuinely independent
tracks, but the coordinating agent must reopen material sources and own the final audit. Agreement
between agents is never counted as source corroboration.

## Artifacts and completion

Standard and Deep research use a directory containing:

- `research-plan.md`
- `claim-ledger.json`
- `source-register.json`
- `contradictions.json`
- `report.md`
- generated `final-audit.json`

Report paragraphs use transparent markers such as `[C001][S001]`. A conflicted or unverified claim
also exposes `[conflicted]` or `[unverified]`. Completion requires every material claim to have an
honest status, adjacent citations where claimed, disclosed contradictions, and passing validators.
The reviewer must still inspect source quality and entailment.

## Commands

```bash
python3 scripts/init-research.py /absolute/output/research
python3 scripts/validate-ledger.py /absolute/output/research
python3 scripts/audit-report.py /absolute/output/research
```

Initialization refuses to overwrite any managed artifact. Validation is offline and does not fetch
URLs. The report audit writes `final-audit.json` even on failure so the exact defects remain visible.
Schemas are under `schemas/`; behavioral policy is under `references/`.

## Private checkout

Use an account or GitHub App with read access to this private repository. Configure authentication on
the machine running OpenClaw; never put a token in the clone URL, prompt, config example, or log.

```bash
git clone https://github.com/rin-proxy/research-verifier.git
cd research-verifier
git fetch origin main
REF=FULL_40_CHARACTER_REVIEWED_COMMIT
git checkout --detach "$REF"
```

Replace the placeholder with the reviewed release commit before executing repository code.

## Compatibility

The initial release is verified with Linux, Bash, Git, Python 3.11+ and OpenClaw 2026.9.3. The
deterministic validators need only Python. Actual research requires authorized retrieval tools in the
selected agent environment. Revalidate model and tool behavior when changing OpenClaw or providers.

## Install and verify

Select an existing non-production workspace explicitly:

```bash
WS=/absolute/test-agent/workspace
bash scripts/install.sh --workspace "$WS"
bash scripts/status.sh --workspace "$WS"
bash examples/quickstart.sh
```

Installation is idempotent and preserves owner data. Code presence and a successful synthetic audit
do not prove that a model will retrieve the right source in a future task.

## Update, rollback and remove

```bash
bash scripts/update.sh --workspace "$WS" \
  --repo https://github.com/rin-proxy/research-verifier.git --ref "$REF"
bash scripts/rollback.sh --workspace "$WS"
bash scripts/uninstall.sh --workspace "$WS"
```

Pinned updates require a full reviewed commit. Rollback restores the previous managed code. Uninstall
archives managed code outside discovery and removes only its instruction pointer; it preserves owner
files and separately created research artifacts.

## Validation

```bash
bash test.sh
python3 scripts/check-docs.py
```

These commands run provider-free unit, lifecycle, provenance, syntax and documentation checks.
[VERIFICATION.md](VERIFICATION.md) defines functional and isolated model acceptance. Measured behavior,
source pins and known limits are recorded in [BENCHMARK.md](BENCHMARK.md).

## Limits

- Structural validation cannot determine whether a source is truthful.
- Citation presence does not prove entailment; a reviewer must inspect the evidence.
- Live sources can change, disappear or correct earlier material.
- A source hierarchy is claim-specific: official sources can still be self-interested.
- No workflow guarantees 100% factual accuracy.
- The skill does not execute recommendations or contact third parties.

## Integration

`operator-reasoning` should hand external or time-sensitive factual research to this skill while
retaining responsibility for broader decision logic. `deep-orchestrator` is optional for independent
research tracks only. `rin-runbook` records the canonical private source and installation choices.

## Shared lifecycle source

Lifecycle code is generated from the reviewed `skill-forge` core. `vendor.json` records its immutable
commit and file hashes; `python3 scripts/vendor.py check` detects drift. No mutable upstream branch is
fetched at runtime.
