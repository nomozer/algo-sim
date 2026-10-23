# Plan — Backend Hybrid Session 3 (`hybrid-contract-v2`)

Authorization `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH` (owner decisions D1 GO, D2 GO-conditional, D3 GO, D4 KEEP 32,
D5 GO, D6 GO-limited). Branch `research/hybrid-backend-session3-contract-v2`, worktree `.superpowers/worktrees/hybrid-backend-s3`,
from Session 2 branch HEAD `227d447f` (= T3 target `f1ae2238` + one docs-only commit: T3 receipts and handoff).
Baseline measured system `96962736…` (115 files) verified MATCH at start.

Takeover rule: every checkpoint below ends in a commit; read `git log` + this file + the newest `verification/*` receipt.

## Findings that shape the plan (read before changing the gate)

- The 4 corpus "false refusals with complete boundary" (A3-DEV-03/04/06/09) are NOT grammar faults: the complete boundary
  adds SA (through-point edge) to `cut_edges`, which the gate reads as a STATED cut the text never states. `/2` separates
  stated intersections from the declared boundary — that is the fix, not a looser gate.
- A3-DEV-10: no stated cut in the payload ⇒ the text's cut clause "cắt BB', CC'" is unread ⇒ refused. `/2`
  `stated_intersections` declares it.
- Real grammar gaps (paraphrases 1–4 of Session 2): restated subject "; (α) cắt …", point-first "Qua M dựng mặt phẳng (α)
  …", "chứa M", per-edge "cắt SA tại M, cắt SB tại N". Each needs a closed alternative + negative controls.

## Checkpoints

1. **P1 safety** — schema-level `PremiseSpec.args` / `named_intersections` validation (input errors →
   `INVALID_TYPED_FACT_NEXT`-family codes); public-boundary record of unexpected exceptions as a TECHNICAL refusal
   (`ADAPTER_INTERNAL_ERROR`, never a data error) with a fuzz receipt requiring 0 escapes and 0 internal errors;
   narrow `_shared_source_gate` except to bridge parsing; engine-owned-name invariant for `gop_doi_tuong_trung`.
2. **P4a locked grammar set** — preregistered evaluation set (positives + negative controls), committed BEFORE any
   grammar change; expected verdict classes: SERVE / REFUSE_SOURCE / REFUSE_KERNEL / REFUSE_GEOMETRY.
3. **P2 contract `/2`** — `typed-fact-next/2` models (stated_intersections with per-intersection quote, optional
   declared_boundary, no input `requires_closed_boundary`), converter `/1 → /2` keyed by an explicit route label,
   bridge `/2`.
4. **P3 D6** — planner derives unstated lateral cut vertices (`derived_fresh`, provenance `DERIVED_FRESH`) only when a
   closed boundary is needed (derived solid / declared boundary), via the Registry planning contract of the
   point-on-(line, plane) producer (ablation: drop the contract ⇒ refuse); gate rule for `derived_fresh`; engine
   closure certificate (`cross_section`) + declared-boundary verification.
5. **P4b grammar** — the four closed alternatives above, evaluated on the locked set.
6. **P5 Adapter `/4` / route-D `/4`** — thin layer over bridge `/2` → planner → engine; envelope with derived
   identities, provenance, closure certificates, goal outcomes, `source_verification` (gate only; no legacy). Curved and
   qualified multi-solid identity refuse precisely on `/2` (legacy `/3` stays isolated, labelled).
7. **P6 IR** — section plane `mp_td_*` vs operand plane; only if provenance / birth order are preserved.
8. **P7 evaluation** — families A–H, dual-run `/1` vs `/2` with independent oracle; migration checklist re-evaluation
   (20 GATE + D-01…D-13).
9. **P8** — independent review → fixes → clean freeze → Authoritative Full T3 → post-verify; focused browser
   acceptance only if product scenes change.
10. **P9** — six reports, receipts, blockers, E2E/live plan (not run).

Invariants: LLM_ONLY · flat · Hybrid NO-GO · ALLOW_LIVE_AI 0 · CACHE_VERSION 127 · no `/api/analyze` change · no
merge / push / delete · pytest one worker, BLAS 1 thread.
