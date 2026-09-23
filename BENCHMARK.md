# Research verifier benchmark

The initial release evaluation compares isolated OpenClaw agents before and after installation. It
completed the planned 120 attempts: 20 synthetic cases, three repetitions and two arms. Ten cases
were held out from the pilot iterations. Both arms used OpenClaw 2026.9.3,
`openai/gpt-5.6-sol`, low reasoning, identical prompts, source fixtures, tools and 180-second limits.
The evaluated behavior source is commit
`5a1288c8dcd4ae398d2aeccfa354ef53924a972f`.

## Recorded results

| Measure | Before | After |
|---|---:|---:|
| Planned attempts | 60 | 60 |
| Runtime-valid attempts | 59 | 58 |
| Strict passes, all attempts | 0/60 | 40/60 |
| Mean strict score, all attempts | 0.8125 | 0.9187 |
| Passing structural artifact audit, valid runtime | 0/59 | 58/58 |
| Correct source-fixture preservation | 60/60 | 60/60 |
| Median wall time | 37.76 s | 84.75 s |
| p95 wall time | 59.66 s | 135.82 s |
| Mean total tokens, valid runtime | 29,163 | 77,035 |
| Mean model calls, valid runtime | 5.05 | 8.88 |

The skill produced the claimed inspectable artifacts consistently on every runtime-valid after
attempt. It also cost about 2.2 times the median wall time and 2.6 times the mean tokens. Use Quick
mode when a full Standard audit is unnecessary.

## Interpretation

Strict scoring is intentionally retained. Eighteen runtime-valid after attempts failed at least one
strict field. A non-blinded post-run review found that all eighteen had an acceptable central answer
and passing artifact audit; the differences involved status taxonomy, abstention representation or
conservative contradiction disclosure. Two after attempts and one before attempt were invalid when
the ChatGPT subscription reached its usage limit. They remain in the denominator and were not rerun.

The central answer on these small synthetic fixtures was already strong before installation: the
same review accepted all 59 runtime-valid baseline central answers. This benchmark therefore supports
an **auditability and traceability improvement**, not a demonstrated central-answer accuracy gain.
It does not show that the skill makes every research result more accurate.

## Evidence and limits

The exact cases, strict gold values, sanitized per-attempt results, summary and interpretation are in
[`evaluations/20260923`](evaluations/20260923/README.md). Raw traces are excluded because they contain
provider reasoning-replay data. Source files were compared byte-for-byte after every attempt.

The fixtures cannot establish real-world truth discovery, source honesty, citation entailment or
performance on other models and tools. A structural audit proves that declared relationships meet the
contract; it is not an independent fact checker. No workflow can guarantee 100% factual accuracy.

## Standard Fast Path optimization

Version 1.1 was evaluated against the version 1.0 behavior with the same 20 cases, three repetitions,
OpenClaw 2026.9.3 runtime, `openai/gpt-5.6-sol` model, low reasoning and isolated tools. The control
used commit `5a1288c8dcd4ae398d2aeccfa354ef53924a972f`; the candidate used the frozen pre-evaluation
commit `2976a9972de3d2a7ba650f15e14c2ecbda6b2f44`.

| Measure | 1.0 control | 1.1 candidate | Change |
|---|---:|---:|---:|
| Planned attempts | 60 | 60 | — |
| Runtime-valid attempts | 59 | 60 | +1 |
| Strict passes, all attempts | 40/60 | 41/60 | +1 |
| Mean strict score, all attempts | 0.9313 | 0.9458 | +0.0145 |
| Passing artifact audit, valid runtime | 59/59 | 60/60 | maintained |
| Correct source-fixture preservation | 60/60 | 60/60 | maintained |
| Median wall time | 82.79 s | 54.66 s | -34.0% |
| p95 wall time | 131.23 s | 78.24 s | -40.4% |
| Mean total tokens, valid runtime | 73,520 | 46,129 | -37.3% |
| Mean model calls, valid runtime | 8.54 | 5.87 | -31.3% |

The candidate met the acceptance gate. Its artifacts and source preservation passed on every attempt,
and a non-blinded review found no candidate central-answer failure among the 60 runtime-valid runs.
Nineteen candidate runs missed at least one frozen strict field; the differences concerned status or
abstention taxonomy, conservative contradiction disclosure, or one equivalent `80` versus `80%`
representation. The single control runtime failure was a retained, non-rerun subscription quota error.

The exact sanitized results, protocol and post-run interpretation are in
[`evaluations/20260923-fast-path`](evaluations/20260923-fast-path/README.md).
