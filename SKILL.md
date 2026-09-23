---
name: research-verifier
description: Research external or time-sensitive factual questions with traceable sources, claim-level evidence, contradiction handling, and a final support audit. Use when an answer needs web research, citations, fact-checking, or comparison of sources; skip for tasks fully answered by supplied material or direct computation.
version: 1.1.0
metadata:
  openclaw:
    emoji: "🔎"
    requires:
      bins: ["python3"]
triggers:
  - "research this"
  - "verify this claim"
  - "fact check this"
  - "compare these sources"
  - "find reliable sources"
  - "cite your sources"
author: Rin
license: UNLICENSED
lastUpdated: 2026-09-23
---

# Research Verifier

Produce a source-grounded answer whose factual claims can be inspected. Do not promise truth from
agreement, a citation count, or confident prose. A claim may be verified, supported, an inference,
conflicted, unverified, or refuted.

## Route before researching

- **Quick:** use when one narrow, low-risk claim is directly answerable by one current primary or
  official source. Open it, check its date/scope and cite it directly; do not build a ledger.
- **Standard:** use for multiple material claims, comparisons, marketing claims, current facts from
  several sources, or decisions that need traceability. Follow only
  [the Standard Fast Path](references/standard-fast-path.md) unless an exception occurs.
- **Deep:** use for broad, high-impact, method-sensitive, or genuinely conflicting evidence. Read
  [the full research protocol](references/research-protocol.md) and retain all evidence artifacts.

Use one agent by default. Read [the sub-agent policy](references/subagent-policy.md) before splitting
a deep research task. Multiple agents using the same model are not independent evidence.

## Required evidence workflow

1. Define the question, scope, as-of time, and what would count as sufficient evidence.
2. Decompose material factual assertions into claim IDs before drafting conclusions.
3. Prefer primary, official, or peer-reviewed sources. Search results are discovery leads; open the
   source itself. Read [the source policy](references/source-policy.md) only when source eligibility,
   dates, independence, or claim strength is unclear.
4. Record what each source supports or contradicts. Treat copies that depend on one origin as one
   evidence family.
5. Seek disconfirming evidence for consequential claims. Only when eligible sources materially
   disagree, read and follow [the contradiction policy](references/contradiction-policy.md).
6. Draft only at the strength supported by the ledger. Mark inference and uncertainty explicitly.
7. Never invent a URL, publication detail, quote, or retrieval result.
8. For Standard work, write one `research/evidence-pack.json`, then run the fast-path finalizer once.
   It renders markers and all managed artifacts and runs the audit. Do not call `init-research.py`,
   author markers, or write the five derived files separately.
9. For Deep/manual work, run `validate-ledger.py` and `audit-report.py`. Use the configured exec host
   without overriding it. Fix failures or report them as incomplete.

Do not read implementation scripts or JSON schemas unless the finalizer returns an error that the
audit does not explain. The fast-path reference contains the complete Standard authoring contract.

## Source budget and stopping

- Quick: one best primary/official source; add one counter-source only when the claim is material.
- Standard: start with at most three independent evidence families. Expand to five only for a gap,
  conflict, or necessary counterevidence; state the reason in the plan.
- Deep: set an explicit source and time budget in the plan.

Stop when a current official source directly answers a narrow claim, or when sufficient independent
eligible evidence supports the bounded claim and a counterevidence check finds no material conflict.
Stop earlier when further results repeat one origin. More URLs are not more evidence.

## Stop conditions

Stop and report the limitation when a required source cannot be opened, the evidence remains
conflicted, current information cannot be dated, or further searching only repeats the same origin.
Do not turn missing evidence into a guess. Do not execute recommendations or contact third parties
as a side effect of research.

## Artifacts

Standard Fast Path:

```bash
python3 skills/research-verifier/scripts/finalize-research.py \
  research/evidence-pack.json research
```

If the audit fails, correct the pack and rerun with `--replace-managed`. Replacement refuses owner
drift. Deep/manual mode may initialize an evidence directory with `init-research.py` and follow
[the research protocol](references/research-protocol.md).

Keep credentials, private reasoning, copyrighted full-text copies, and unrelated user data out of
research artifacts. Short evidence excerpts are locators, not substitutes for linking the source.

For installation prerequisites and expected functional results, read [README.md](README.md) and
[VERIFICATION.md](VERIFICATION.md). Installation alone does not prove that a future answer is true.
