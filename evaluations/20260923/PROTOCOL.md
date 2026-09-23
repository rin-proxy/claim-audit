# Evaluation protocol

## Design

- Behavior source: `5a1288c8dcd4ae398d2aeccfa354ef53924a972f`.
- Runtime: OpenClaw 2026.9.3 in separate bubblewrap workspaces and state directories.
- Model: `openai/gpt-5.6-sol`; reasoning: low.
- Matrix: 20 cases x 3 repetitions x 2 arms = 120 attempts.
- Held out: the final ten cases were not used during pilot adjustment.
- Both arms received the same prompt, synthetic source files, tool policy and 180-second task limit.
- External services, messages, browsers, scheduling, gateways, nodes and sub-agents were disabled.
- Strict expected values remained outside both model workspaces.
- Every attempt compared source fixture contents byte-for-byte after execution.
- The after arm installed the skill; the before arm did not. An external invocation of
  `audit-report.py` evaluated both arms by the same structural contract.

## Strict completion

An attempt passed only when the runtime/model were valid, all six returned fields matched the frozen
gold values, the external artifact audit passed and source fixtures were unchanged. Runtime errors
received score zero. Existing result files were skipped on resume, so completed attempts were not
rerun.

## Pilot and amendments

Pilots exposed ambiguous field names, claim-marker examples and an incorrect exec-host assumption.
Those were corrected before the final matrix began. Pilot outputs are not included in these results.

During the final matrix, a ChatGPT subscription usage limit interrupted `vendor-superlative`. The
harness initially treated one `ok: true` OpenClaw envelope as runtime-valid even though its payload
was `isError` with `incomplete_turn`. Runtime validation was corrected to reject error payloads,
replay-invalid turns and result errors. That attempt and the following failed attempt remain invalid,
scored zero and were not rerun. The run resumed after a separate quota probe succeeded. Gold values
and completed model answers were never changed.

## Interpretation rule

Strict scores are authoritative and unchanged. A separate, non-blinded post-run review classifies
whether a strict mismatch changes the central answer or reflects status/abstention representation.
That review is published in `interpretation.json` and must not be presented as a blinded evaluator.

## Reproduction limits

Reproduction requires an authorized ChatGPT subscription, the same OpenClaw/model route and an
equivalent isolated tool environment. Provider behavior and rate limits can change. The exact cases
and sanitized results are published, but private auth profiles and raw reasoning-replay traces are not.
