# Preregistration — grounded Semantic Extraction v2

2026-10-17. The authoritative lock is the commit adding this preregistration, corrected corpus/gold, oracle, protocol and scorer. **No product prompt change or provider request precedes that commit.** Later changes to this protocol/scorer require a declared amendment and invalidate live identities. Prior locked D/L items are historical diagnostics, never new heldout data.

## Questions and arms

Does a clarified existing TypedFact contract improve faithful source extraction without invented geometry? Distinguish model extraction, source grammar, schema gaps and planner capability. No schema/planner/kernel/frontend redesign.

Two prompt arms use the same candidate downstream code: BASELINE (saved original SYSTEM_PROMPT), V2 (candidate prompt). Both retain model gemini-2.5-flash, temperature0, maxOutputTokens8192, one structured-output pass, no retries. A paired prompt ablation on fresh items estimates prompt effects; an offline before/after GOLD comparison estimates the bounded grounding predicate effect independently. Schema/validation are unchanged, so no schema-effect claim. Replay tests are never evidence of prompt effectiveness.

## Data and oracle

Fresh author, separate agent context, instructed not to read repository, prompts or prior corpus. Isolation was **instruction-only**, not enforced permissions. 36 cases:12 development /24 fresh heldout,20 declared structure families,51 source requests,34 independent Fraction numeric oracles. Related contrast pairs remain together. Independent reviewer recomputed34 values from source dimensions:0 mismatches. Labels **INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED**; product gold is **AI_AUTHORED_WITH_IMPLEMENTER_ENCODING_CORRECTIONS**.

Pre-lock review found33 encoding corrections (unsupported fields/quantity, right-angle rays, unrepresentable point/line definitions, proof role); every before/after is in `inputs/prelock_corrections.json`. No numeric oracle or mathematical answerability label changed. Schema-valid gold may intentionally refuse because source semantics exceed product capabilities. Every source request has a gold rid including constructions represented as premises.

Overlap audit: normalized character five-gram intersection/minimum set size; maximum old-corpus0.653, dev/heldout0.639, limited74 fixture strings0.618. Not a training-data or complete Python-fixture overlap proof. Parent sees development texts and aggregate audits only until candidate prompt is frozen. Heldout results must not drive prompt/product tuning; if repair becomes necessary, retire this heldout for subsequent measurement.

`inputs/protocol.json` records canonical JSON hashes and LF-normalized oracle/authoring/baseline surface hashes. The lock commit pins all bytes. Any human validation remains pending.

## Scorer /2

`backend/scripts/run_semantic_extraction_evaluation.py`, `grounded-source-obligations/2`. Reuses the frozen evaluator's execution, budget, persistence, secret redaction and approval transport through a private module instance. Historical scorer/receipts are unchanged.

Served-answer scoring **has no extraction-pair input**. Match each independently annotated request one-to-one with the actual executed call's mathematical quantity and operands, then exact independent squared magnitude/cos². Named/derived identity comes from actual calls and executed producer evidence. A matching number for another object is WRONG_SERVED. An extra unused TypedFact slot cannot make a correctly bound answer wrong (L01 regression). Ordinary coplanar source planes may use containing label sets only after the served engine has verified every written label. Complex result-line/effect bindings outside this scorer's implemented vocabulary are UNSCORABLE, never silently correct.

All source requests count, including constructs, unsupported, proof, explanation and interaction. Missing construction execution, second numeric goal or unsupported goal is PARTIAL_SERVED even if the first answer is correct. Extra answer is OVER_SERVED. Missing receipt/oracle/form evidence is UNSCORABLE; source angle vs cos² response-form mismatch is FORM_MISMATCH. No scene-presence shortcut for construction completion. Refusal dispositions distinguish safe refusals from mathematically answerable false refusals; gold-route refusal codes identify capability/grammar/schema gaps separately. NO_PARSE is separate.

Extraction matching reuses fact equivalences after ignoring product-unused solid/question slots; it does not alter provider output or product acceptance. Source requests, not question-role facts, define goal completeness. Intent is a **kind/role/quantity proxy** because TypedFact has no separate calculate-vs-simulate intent field; report this limitation. Premise precision/recall remain parsed-row diagnostics; source-goal, operand and solid denominators include parse failures. Missing unparsed premise observations are UNKNOWN rather than a precision success. Hallucinated-entity rows, unsupported detection/approximation, operand/solid agreement and complete multi-goal rows are separate metrics.

## Decisions and metrics

P1 corpus safety:0 WRONG_SERVED/PARTIAL_SERVED/OVER_SERVED/FORM_MISMATCH; any UNSCORABLE blocks readiness. P2:all-planned expressible goal/entity agreement≥0.85, operand correctness≥0.85, solid association≥0.85 and no observed invented entities. Report unsupported and multi-goal rates without hiding small denominators. All requests form a second unconditional denominator; no parsed-only accuracy headline. Report paired changes by case and structure family, descriptive corpus results only; no iid population CI over correlated goals. Pilot must have complete receipts, no unsafe/unknown served outcome, no secret/model drift and valid usage before proposing a separate LOCKED GO. No tuning after heldout results.

Required table: intent proxy, goal/entity, operands, solid, multi-goal, unsupported, hallucinated entity rows, premise precision/recall, correct/wrong served, safe/false refusal, capability gaps, token/cost/latency. Old44 locked baseline remains a nonpaired historical reference with both frozen UNSAFE and correction P1 PASS/P2 NO. Only new paired baseline/v2 arms support a prompt-effect comparison.

## Live approval and budgets

**LIVE_NOT_AUTHORIZED.** No historical approval is reusable. New identities include candidate product hash, prompt/schema surface, corpus/gold/oracle/protocol/preregistration, executor/helper/scorer hashes, arm, mode and schedule/caps.

Proposed PILOT:dev12×2 arms=24 calls,0 retries, combined capUSD1.00 (0.50/arm),800k accounted tokens. Proposed LOCKED:heldout24×2=48 calls,0 retries, combined capUSD2.00 (1.00/arm),1.6m tokens; **separate later GO**. Exact reservation/cost estimate and identities published after freeze. 90s/request. Stop before cap, on HTTP400/401/403/429, secret, model drift, persistence failure, unknown usage/reservation violation, or3 consecutive infrastructure failures. Cost/usage UNKNOWN must stop live. No retries or uncertain pending-request resend. Raw live output goes only to ignored `.superpowers/`; publish sanitized metrics and hashes, never raw output or secrets in Git.

## Pre-lock amendments (2026-10-17, before the lock commit, before any prompt change)

Codex stopped mid-scorer-fix (usage limit); Claude continued in the same worktree (`plan.md` § Takeover). Scorer changes
before the lock, each with a RED→GREEN test, none touching corpus, gold, oracle or the frozen V1 evaluator:

- Operand semantics per role, not blanket sorting: segment endpoints unordered; plane = label set (containment, incl.
  section planes); polygon = vertex cycle up to rotation/reflection (`ACBD` ≠ `ABCD`); distance and unsigned angle between
  two objects symmetric; projection point/image positional; solid = vertex structure (`OPQR` = planner's `R.OPQ`; pyramid
  apex + base cycle; prism corresponding bases).
- `capability_gap` requests are fulfilled by matching executed evidence (found on the GOLD route: an executed projection
  was counted missing); `unsupported`/`ambiguous`/`missing_source` must never be served.
- False refusals split by the GOLD route on the same product: `_CAPABILITY_GAP` (GOLD refuses) vs `_EXTRACTION` (GOLD
  serves). Transport failures are `PROVIDER_OR_HARNESS_ERROR`; a served route is scored whatever the parse status.
- Extraction agreement: rightness as the planner derives it; equal_lengths can match; operand numerator and denominator
  share one population; solid-slot labels count as invented entities.
- Published receipts: derived metrics, execution class, identity, usage/latency and the source manifest row hash; no
  model fact/answer ids or non-label strings; secret scan; LIVE raw output only under ignored `.superpowers/`.
- Known conservative limitation: a point-to-point "distance" served by `ask_length` scores WRONG_SERVED (no corpus item).

Independent AI review of the scorer: first round NOT_READY (2 blockers, 4 important, 5 minor), all addressed or dispositioned;
verdict of the second round is recorded in `review.md`.

**GOLD ceiling observed before any prompt change** (authored facts, current product, 0 calls): dev 1/12 served correct,
5 safe refusals, 6 capability/grounding refusals; heldout 2/24 served correct, 4 safe, 18 capability/grounding; 0 unsafe,
0 unscorable. Most requests are therefore not servable even with perfect extraction; served-answer gains from a prompt
change are bounded by this ceiling, and extraction metrics are the primary prompt outcome.

**Heldout exposure disclosure.** To diagnose the scorer defect the implementer saw aggregate heldout outcomes/refusal
codes and one heldout row's structure (request ids, intents, target labels, executed call names — no source text); the
reviewer used heldout targets/labels/outcomes, no texts. Heldout is therefore *structurally implementer-exposed*, not
implementer-blind. No heldout observation drives a product change.

**Declared product change (fixed now, before results).** (1) Prompt v2 = clarified rules within the unchanged TypedFact
schema: atomic request coverage, question operand matrix, measure→solid ownership, two-ray right angles, all labels for
operand planes (three only for `line_ref` intersection-line producers), no invented labels/properties, explicit
`unsupported` without approximation. (2) Two Source Grounding vocabulary entries with negative tests: `hộp chữ nhật` names
a cuboid/prism (dev01 `PREDICATE_NOT_IN_QUOTE`, reuses the existing `_HOP_CHU_NHAT` pattern) and `dài bao nhiêu` asks a
length (baseline L02). GOLD before/after reports the grounding effect separately from the prompt arms. Other grammar gaps
(`… thì … bằng mấy`, `Tính cos²`, repeated `tính` boundaries, `rồi suy ra`, projection wording) stay open issues.

## Amendment 1 (after the lock, before any model call) — third grounding entry from the DEV split

The GOLD route after the declared change moved dev01 from `PREDICATE_NOT_IN_QUOTE` to `SOURCE_PREMISE_UNREAD`: a
sentence-initial indefinite article ("Một hộp chữ nhật …") is not premise connective vocabulary. Added, with negatives:
`Một` at the start of a premise sentence directly before a solid noun is an article; `một` elsewhere ("một cạnh",
"một nửa", a number) stays content. Evidence is DEV only (tuning split); no heldout observation drove it. Corpus, gold,
oracle, scorer and protocol are unchanged; GOLD before/after is reported per split.

## Amendment 2 (whole-change review, before any model call)

Independent review of the product commit: GO, no unsafe serve in ~40 adversarial inputs, with findings applied before
the prompt is frozen: rule 7 asked three labels for section/intersection planes while the gate requires the written
label group (contradicting rule 11) — rule 7 now asks the written group; unnamed-point targets go in `points_b`; the
unused `dài là/bằng bao nhiêu` variants were removed. A pre-existing unsafe path on main was closed: a bare "hình hộp"
(possibly oblique) certified a right prism, serving AC′ from an unstated right box; rightness now needs
đứng/đều/hộp chữ nhật/lập phương. Historical GOLD outcomes unchanged by these fixes. The draft B surface `cc6316fb…`
was never sent to a provider and is superseded by `c4e4392c…` (`provider-surfaces.json`).

## Integration

Independent review → fixes → verification → refreeze → clean detached authoritative T3 for this changed candidate. Integration and Hybrid enablement require separate owner decisions. At the first live gate retain a clean committed research checkpoint; do not merge/push or remove its unintegrated branch/worktree. Default LLM_ONLY and cache125 unless actual cache-consumer evidence demands invalidation.
