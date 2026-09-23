# Standard Fast Path evaluation protocol

## Design

- Control behavior source: `5a1288c8dcd4ae398d2aeccfa354ef53924a972f`.
- Candidate behavior source: `2976a9972de3d2a7ba650f15e14c2ecbda6b2f44`.
- Runtime: OpenClaw 2026.9.3 in separate bubblewrap workspaces and state directories.
- Model: `openai/gpt-5.6-sol`; reasoning: low.
- Matrix: 20 unchanged cases x three repetitions x two arms = 120 attempts.
- Both arms received the same prompt, source fixtures, tool policy and 180-second task limit.
- External services, messages, browsers, scheduling, gateways, nodes and sub-agents were disabled.
- Strict expected values remained outside both model workspaces.
- Every attempt compared source fixture contents byte-for-byte after execution.
- The candidate commit was frozen before the first pilot attempt.
- Existing result files were skipped on resume; completed attempts were not rerun.

## Acceptance gate

The candidate required a passing artifact audit and preserved source fixtures on every runtime-valid
attempt, no new substantive central-answer failure in post-run review, and a meaningful reduction in
median wall time or token use. Strict scores remained frozen and authoritative.

## Runtime amendment

The first control attempt for `unsupported-rumor` ended with an OpenClaw `incomplete_turn` after the
ChatGPT subscription reached its usage limit. The attempt remains invalid and scored zero. A separate
quota probe succeeded before the matrix resumed; the failed attempt was not deleted or rerun. The
paired candidate attempt completed normally.

## Reproduction limits

Reproduction requires an authorized ChatGPT subscription, the same OpenClaw/model route and an
equivalent isolated tool environment. Provider behavior and quota availability can change. Raw
traces, auth profiles and reasoning-replay payloads are not published.
