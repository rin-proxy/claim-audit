# ClaimAudit

[![Verify](https://github.com/rin-proxy/claim-audit/actions/workflows/verify.yml/badge.svg)](https://github.com/rin-proxy/claim-audit/actions/workflows/verify.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Turn external research into an inspectable claim-and-source record. The skill separates evidence,
inference, unresolved conflict and missing support without claiming that structural validation proves
real-world truth.

## Use and expected result

Use it for fact-checking, current information, source comparisons, cited research, or decisions whose
factual premises must be traceable. A narrow official lookup can use Quick mode; multiple material
claims use Standard; broad or conflicting evidence uses Deep.

Example request: **“Compare these reports, preserve their disagreement, and state what can actually
be verified.”** The result should cite sources beside material claims, label unresolved conflicts and
produce a passing structural audit. Quick and Standard use one agent by default; Deep may split truly
independent tracks, but the coordinating agent owns the final audit.

## Quick start

From a reviewed checkout, run:

```bash
bash examples/quickstart.sh
```

The provider-free example renders one synthetic evidence pack and audits the generated bundle. It
ends with `Quickstart passed: claim-audit` and does not access production data.

## Install

Clone the public repository, then check out a reviewed release or full commit. Releases are immutable;
avoid installing from a moving branch when reproducibility matters.

```bash
git clone https://github.com/rin-proxy/claim-audit.git
cd claim-audit
git checkout --detach v2.1.0
WS=/absolute/agent/workspace
bash scripts/install.sh --workspace "$WS"
bash scripts/status.sh --workspace "$WS"
```

Installation adds the package and a managed instruction pointer to the selected workspace. It does
not add a browser, search API, model provider, channel, scheduler or background service.

## Standard workflow

Standard starts with three independent evidence families and expands to five only for a gap,
conflict or counterevidence requirement. Author one pack, then render and audit it:

```bash
python3 scripts/finalize-research.py \
  /absolute/output/research/evidence-pack.json /absolute/output/research
```

The output contains the research plan, claim ledger, source register, contradictions, report,
`final-audit.json`, and a drift manifest. After correcting the pack, replace only unchanged managed
artifacts with `--replace-managed`. Hash checks reject owner drift.

Deep/manual recovery remains available through `init-research.py`, `validate-ledger.py`, and
`audit-report.py`; detailed procedures and status rules stay in [SKILL.md](SKILL.md).

## Update and recovery

Check the latest stable GitHub release without installing it:

```bash
python3 scripts/check-update.py
```

Review its release notes and resolve the selected tag to a full commit before updating:

```bash
git fetch origin --tags
REF=$(git rev-list -n 1 v2.1.0)
bash scripts/update.sh --workspace "$WS" \
  --repo https://github.com/rin-proxy/claim-audit.git --ref "$REF"
bash scripts/rollback.sh --workspace "$WS"
bash scripts/uninstall.sh --workspace "$WS"
```

Pinned updates require a reviewed full commit. Rollback restores managed code; uninstall archives
managed code outside discovery while preserving owner files and research artifacts.

If installed code has changed, update stops instead of overwriting it. Export an inspectable archive
of added and modified files, then reconcile those changes in a Git fork or patch branch:

```bash
python3 scripts/export-customizations.py --workspace "$WS" --output claim-audit-customizations.tar.gz
```

The export includes changed and added files plus a manifest of deleted paths. It can contain the
operator's own sensitive content, so review it before sharing. A forced update archives the previous
package but never attempts an automatic source merge.

### Migrating from `research-verifier`

The new skill ID is a breaking package rename, so the old lifecycle intentionally refuses to update
across the name boundary. Remove the old package with its own uninstall script, then install
ClaimAudit from a reviewed commit:

```bash
bash "$WS/skills/research-verifier/scripts/uninstall.sh" --workspace "$WS"
bash scripts/install.sh --workspace "$WS"
```

Uninstall archives the old managed package under `.openclaw-skill-state/research-verifier/` and
preserves workspace research artifacts. Review and manually port intentional code customizations;
the migration does not guess how to merge them into the renamed package.

## Safety, verification and evidence

- A structural audit checks declared relationships, not whether a source is truthful.
- Citation presence does not prove entailment; inspect material evidence.
- Live sources can change, disappear or correct earlier claims.
- The skill does not execute recommendations or contact third parties.

```bash
bash test.sh
python3 scripts/check-docs.py
```

The initial 1.0 evaluation established auditability but measured substantial overhead. The frozen 1.1
comparison retained artifact audits and source preservation at 60/60 while reducing median Standard
wall time by 34.0%, mean total tokens by 37.3%, and mean model calls by 31.3% versus the 1.0 control.
See [BENCHMARK.md](BENCHMARK.md) for strict-score interpretation, runtime failures and limits.

Detailed documentation: [acceptance and recovery](VERIFICATION.md) ·
[tested compatibility](COMPATIBILITY.md) · [release notes](RELEASE-NOTES.md) ·
[source provenance](PROVENANCE.md) · [contributing](CONTRIBUTING.md) ·
[security](SECURITY.md) · [Apache-2.0 license](LICENSE).
