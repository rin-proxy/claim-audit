# Standard Fast Path

Use this path for Standard research. It is complete; do not load the full protocol, implementation
scripts or schemas unless finalization reports an unexplained error.

## One-pass flow

1. Define one bounded question and completion rule.
2. List/read relevant sources in a batch. Start with no more than three independent evidence
   families; expand to five only for a gap, conflict or necessary counterevidence.
3. Write one `research/evidence-pack.json` using the exact fields below. Do not create derived files.
4. Run:

   ```bash
   python3 skills/research-verifier/scripts/finalize-research.py \
     research/evidence-pack.json research
   ```

5. If status is `PASS`, answer from `report.md`. If status is `FAIL`, inspect `final-audit.json`, fix
   only the pack and rerun with `--replace-managed`. Stop rather than guessing if evidence is weak.

## Exact pack contract

```json
{
  "schema": 1,
  "plan": {
    "question": "Bounded question",
    "scope": "Included population/version and exclusions",
    "as_of_time": "2026-09-23T00:00:00Z or not time-sensitive",
    "completion_rule": "Specific sufficient evidence and stop condition"
  },
  "sources": [{
    "id": "S001",
    "url": "https://example.test/source",
    "title": "Source title",
    "publisher": "Publisher",
    "source_type": "official",
    "independent_group": "origin-a",
    "retrieved": true,
    "accessed_at": "2026-09-23T00:00:00Z"
  }],
  "claims": [{
    "id": "C001",
    "text": "Bounded factual claim.",
    "kind": "fact",
    "status": "verified",
    "citations": ["S001"],
    "evidence": [{
      "source_id": "S001",
      "relation": "supports",
      "locator": "Section 2",
      "excerpt": "Short evidence locator or faithful paraphrase."
    }]
  }],
  "contradictions": [],
  "report": {
    "title": "Research result",
    "sections": [{
      "claim_id": "C001",
      "text": "User-facing claim without hand-authored C/S markers."
    }]
  }
}
```

Allowed source types: `official`, `primary`, `peer_reviewed`, `preprint`,
`independent_reporting`, `community`, `opinion`.

Allowed claim kinds: `fact`, `current_fact`, `number`, `inference`, `opinion`.
`current_fact` also requires `checked_at` on the claim.

Claim status:

- `verified`: direct eligible primary/official/peer-reviewed support, or two independent eligible
  groups directly support it.
- `supported`: eligible direct support exists, but the verified rule is not met or scope is limited.
- `inference`: derived from cited facts rather than directly stated.
- `conflicted`: eligible sources materially disagree; add a contradiction record.
- `unverified`: evidence is missing, inaccessible, stale or too weak.
- `refuted`: eligible evidence directly contradicts the tested claim; record relation `contradicts`.

A contradiction record uses `id`, `claim_ids`, `source_ids`, `summary`, `resolution_status` and
`disclosed_in_report`. Use the same `independent_group` for copies of one press release, dataset,
wire story or paper. Search snippets and remembered pages are not retrieved evidence.

The renderer creates `research-plan.md`, the three ledgers, adjacent `[Cnnn][Snnn]` markers,
`report.md`, `final-audit.json` and a drift manifest. One report section must cover each claim exactly
once. Do not put credentials, private reasoning or copyrighted full text in the pack.
