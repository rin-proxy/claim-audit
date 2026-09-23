# Research protocol

Use this protocol for standard and deep research. Quick lookups may answer directly when a single
authoritative source is sufficient, but they still must open the source and cite the supported claim.

## Evidence directory

`init-research.py` creates:

- `research-plan.md`: question, scope, as-of time, constraints and completion rule.
- `claim-ledger.json`: material claims, status, citations and evidence relations.
- `source-register.json`: retrieved source metadata and evidence-family identity.
- `contradictions.json`: material disagreements and their disclosed resolution or non-resolution.
- `report.md`: the user-facing synthesis with adjacent `[Snnn]` citations.
- `final-audit.json`: generated audit evidence; do not author it by hand.

## Claim statuses

- `verified`: an eligible primary/official/peer-reviewed source directly supports the claim, or two
  independent eligible evidence families directly support it.
- `supported`: at least one retrieved eligible source directly supports it, but the verified rule is
  not met or the claim has a stated limitation.
- `inference`: the conclusion is derived from cited facts rather than stated by a source.
- `conflicted`: eligible sources materially disagree and the conflict is unresolved.
- `unverified`: evidence is missing, inaccessible, too stale, or too weak.
- `refuted`: eligible evidence directly contradicts the tested claim.

Do not promote a status because many pages repeat one origin. `independent_group` identifies shared
provenance. A source must have `retrieved: true`; search snippets and remembered pages are not
retrieved evidence.

## Claim ledger contract

Each claim has a unique `Cnnn` ID, concise text, kind (`fact`, `current_fact`, `number`, `inference`,
or `opinion`), status, citation IDs, and evidence records. Evidence records contain `source_id`,
`relation` (`supports` or `contradicts`), a useful locator, and a short excerpt or faithful paraphrase.
`current_fact` claims also require an ISO-8601 `checked_at` timestamp.

The ledger is a review aid, not hidden chain-of-thought. Record externally inspectable evidence and
brief rationale only.

Use these exact field names; the validators intentionally reject aliases such as `claim_id`,
`source_id` at the source-record level, `citation_ids`, `type`, `published`, or `retrieved_at`:

```json
{
  "schema": 1,
  "sources": [{
    "id": "S001", "url": "https://example.test/source", "title": "Source title",
    "publisher": "Publisher", "source_type": "official", "independent_group": "origin-a",
    "retrieved": true, "accessed_at": "2026-09-23T00:00:00Z"
  }]
}
```

```json
{
  "schema": 1,
  "claims": [{
    "id": "C001", "text": "Bounded factual claim.", "kind": "fact",
    "status": "verified", "citations": ["S001"],
    "evidence": [{
      "source_id": "S001", "relation": "supports",
      "locator": "Section 2", "excerpt": "Short supporting passage."
    }]
  }]
}
```

When a conflict exists, use `{"schema":1,"contradictions":[{"id":"X001",
"claim_ids":["C001"],"source_ids":["S001","S002"],"summary":"Exact disagreement",
"resolution_status":"unresolved","disclosed_in_report":true}]}`. Otherwise keep the array empty.

## Completion

Research is complete when every material claim has an honest status, every citation resolves to a
retrieved source, contradictions are disclosed, the report uses no unsupported stronger wording,
and both deterministic audits pass. Passing structural audits does not establish real-world truth;
the reviewer must still inspect whether evidence entails each claim.
