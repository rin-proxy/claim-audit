---
name: research-verifier
description: Research external or time-sensitive factual questions with traceable sources, claim-level evidence, contradiction handling, and a final support audit. Use when an answer needs web research, citations, fact-checking, or comparison of sources; skip for tasks fully answered by supplied material or direct computation.
version: 1.0.0
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

## Choose the depth

- **Quick:** a narrow low-risk lookup; open the best primary source and cite it directly.
- **Standard:** multiple material claims; keep a claim ledger and run the final audit.
- **Deep:** broad, high-impact, or conflicting evidence; retain all evidence artifacts.

Use one agent by default. Read [the sub-agent policy](references/subagent-policy.md) before splitting
a deep research task. Multiple agents using the same model are not independent evidence.

## Required workflow

1. Define the question, scope, as-of time, and what would count as sufficient evidence.
2. Decompose material factual assertions into claim IDs before drafting conclusions.
3. Prefer primary, official, or peer-reviewed sources. Search results are discovery leads; open the
   source itself. Read [the source policy](references/source-policy.md) for eligibility rules.
4. Record what each source supports or contradicts. Treat copies that depend on one origin as one
   evidence family.
5. Seek disconfirming evidence for consequential claims. Only when eligible sources materially
   disagree, read and follow [the contradiction policy](references/contradiction-policy.md).
6. Draft only at the strength supported by the ledger. Mark inference and uncertainty explicitly.
7. Put `[Cnnn][Snnn]` markers beside each report claim they identify and support. Never invent a URL,
   publication detail, quote, or retrieval result.
8. For standard/deep work, run `python3 scripts/validate-ledger.py RESEARCH_DIR`, then
   `python3 scripts/audit-report.py RESEARCH_DIR` using the configured exec host without overriding
   it. Fix failures or report them as incomplete.

## Stop conditions

Stop and report the limitation when a required source cannot be opened, the evidence remains
conflicted, current information cannot be dated, or further searching only repeats the same origin.
Do not turn missing evidence into a guess. Do not execute recommendations or contact third parties
as a side effect of research.

## Artifacts

Initialize a standard/deep evidence directory with:

```bash
python3 scripts/init-research.py /absolute/output/research
```

The schemas and exact status rules are in [the research protocol](references/research-protocol.md).
Keep credentials, private reasoning, copyrighted full-text copies, and unrelated user data out of
research artifacts. Short evidence excerpts are locators, not substitutes for linking the source.

For installation prerequisites and expected functional results, read [README.md](README.md) and
[VERIFICATION.md](VERIFICATION.md). Installation alone does not prove that a future answer is true.
