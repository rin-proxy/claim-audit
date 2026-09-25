# Release notes — 2.1.0

ClaimAudit is now a self-contained Apache-2.0 project. Public users can clone and test it without
credentials or access to another Rin repository. The release adds an update checker, drift export,
community contribution and security policies, Python 3.11–3.13 CI, CodeQL, and reproducible source,
manifest, SPDX SBOM and checksum assets.

The public-launch audit scanned every Git ref and historical file with Gitleaks 8.30.1, reviewed
additional credential and internal-path patterns, and inspected all pre-launch GitHub Actions logs.
No secret or private operational reference was found. Standard GitHub runner paths were the only
private-path pattern in Actions logs.

## 2.0.0

The project is now named **ClaimAudit** with the skill ID `claim-audit`. The repository moves from
`rin-proxy/research-verifier` to `rin-proxy/claim-audit`. This is a major release because OpenClaw
discovers skills by ID and the installed directory changes.

Existing installations must uninstall the old ID with its own lifecycle script, then install the
new package. The old package is archived rather than deleted, research artifacts remain in place,
and intentional code customizations can be ported after review. Evidence directories carrying the
legacy `.research-verifier-render.json` manifest remain eligible for drift-safe replacement.

## 1.1.0

Standard research now authors one evidence pack. A deterministic finalizer renders the plan, ledgers,
claim/source markers, report, drift manifest and final audit in one command. Repair verifies hashes
before replacing managed artifacts and preserves unrelated owner files.

Routing now favors Quick for a narrow low-risk official lookup, caps the initial Standard source
budget at three independent evidence families, and stops repeated-origin searching. Deep research
retains the complete manual protocol. In the published same-case comparison, the candidate retained
60/60 artifact audits and source preservation while reducing median wall time by 34.0%, mean total
tokens by 37.3% and mean model calls by 31.3%. See `BENCHMARK.md` for the protocol and limits.

## 1.0.0

This release introduces an inspectable research workflow with claim statuses, source provenance,
contradiction disclosure and adjacent citation auditing. It uses no background service and makes no
production or channel changes. Passing validation proves the declared structural relationships, not
the truth of external sources or universal model accuracy.

The isolated 120-attempt evaluation found passing artifact audits on all 58 runtime-valid skill
attempts versus none of 59 runtime-valid baseline attempts. It did not establish improved central
answer accuracy and measured material latency/token overhead. See `BENCHMARK.md` and the sanitized
evidence under `evaluations/20260923/`.
