# Hybrid A/B readiness handoff

Status: `HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW`; environment LOCAL; live Gemini0.
Branch `feat/text-to-geometry-functions`; product `cfe2ada5`; candidate `12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52`;
cache125; default `LLM_ONLY`. Main unchanged at `28ac1d61cbaa6b33085bb12392e5f0f5815eb787`; no push/merge/history rewrite.
Documentation commit role SELF; user-owned untracked `frontend/public/favicon.svg` preserved and excluded from staging.

Implementation: safety commits `9823a61e`, `ef1a9ae6`, clause fix `2e4b87b6`, runner `e20e681e`, bounded review fix `cfe2ada5`.
341 focused PASS + 9 mutation killed; 312 fake operations through real adapters with network/live0. Full clean suite/doc gates
are pending final journal; consult [`report.md`](report.md) for the final result, not historical count summaries.

Authoritative protocol/plan: [`protocol.md`](protocol.md), [`plan.md`](plan.md). Machine identity and caps: [`run.json`](run.json).
Current fake certification: [`fake-provider/review-fix/CERTIFICATION.json`](fake-provider/review-fix/CERTIFICATION.json).
Historical hybrid evidence remains byte-identical; old fake artifacts within this run remain pre-review snapshots.
Current divergence authority: [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json), guarded by the existing
thesis acceptance test; it does not reinterpret historical measurement results.

Offline readiness PENDING final clean regression. SMOKE live NO-GO; FULL live NO-GO. Payload bytes+4096 is unverified for
provider tokenization/overhead; strict billed cap containment and live truncation/thinking allocation remain unproven. Caps stay
USD0.60 /7; shared output3072; accounted500k /6M. Zero errors do not prove safety. Renderer metric is not visual acceptance.

Do not send Gemini generation or countTokens requests, including free tier. Do not create human approval records, merge main,
push, change default/cache or mutate old artifacts. An explicit future live approval must match the frozen exact per-mode identity;
FULL requires separate approval after smoke review. Pending/uncertain journals are never automatically retried/resumed.

Next: finish/read final full regression journal, then user reviews protocol/identities/budget uncertainty. If the user later authorizes
real calls, use a dedicated output directory outside docs, mode-specific approval and stop on the first uncertain-cost/error condition.
No live command is suggested here because no live execution is currently authorized.
