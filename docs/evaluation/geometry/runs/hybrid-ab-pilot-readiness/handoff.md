# Hybrid A/B readiness handoff

Status: `HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW`; environment LOCAL; live Gemini0.
Branch `feat/text-to-geometry-functions`; product `cfe2ada5`; candidate `12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52`;
cache125; default `LLM_ONLY`. Main unchanged at `28ac1d61cbaa6b33085bb12392e5f0f5815eb787`; no push/merge/history rewrite.
Documentation commit role SELF; user-owned untracked `frontend/public/favicon.svg` preserved and excluded from staging.

Implementation: safety commits `9823a61e`, `ef1a9ae6`, clause fix `2e4b87b6`, runner `e20e681e`, bounded review fix `cfe2ada5`, final taxonomy `8aad0673`, refusal-metadata/scoring completion `2f1b457c`.
344 focused PASS + 9 mutation killed; 312 fake operations through real adapters with network/live0. Clean full backend8068 PASS /1 skip /2 deselected,359.12s at `2f1b457c`; clean final docs153 PASS,38.27s at `475defaa`, audit PASS,48 artifact hashes verified. Consult [`report.md`](report.md) for the final result, not historical count summaries.

Authoritative protocol/plan: [`protocol.md`](protocol.md), [`plan.md`](plan.md). Machine identity and caps: [`run.json`](run.json).
Current fake certification: [`fake-provider/verified/CERTIFICATION.json`](fake-provider/verified/CERTIFICATION.json).
Historical hybrid evidence remains byte-identical; old fake artifacts within this run remain prior-identity snapshots (including the first review-fix certification).
Current divergence authority: [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json), guarded by the existing
thesis acceptance test; it does not reinterpret historical measurement results.

Offline readiness GO (bounded wiring/guard certification), not real-model quality or storage-reliability proof. SMOKE live NO-GO; FULL live NO-GO. Payload bytes+4096 is unverified for
provider tokenization/overhead; strict billed cap containment and live truncation/thinking allocation remain unproven; local atomic-I/O failures remain UNKNOWN
and require risk acceptance/resolution. Failed journals are retained without resume/retry. Caps stay
USD0.60 /7; shared output3072; accounted500k /6M. Zero errors do not prove safety. Renderer metric is not visual acceptance.

Do not send Gemini generation or countTokens requests, including free tier. Do not create human approval records, merge main,
push, change default/cache or mutate old artifacts. An explicit future live approval must match the frozen exact per-mode identity;
FULL requires separate approval after smoke review. Pending/uncertain journals are never automatically retried/resumed.

Next: user reviews final verification journals, protocol/identities/budget uncertainty and unresolved local persistence risk. If the user later authorizes
real calls, use a dedicated output directory outside docs, mode-specific approval and stop on the first uncertain-cost/error condition.
No live command is suggested here because no live execution is currently authorized.
