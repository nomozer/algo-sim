# Generalized Goal Entry — research result

Status: GENERALIZED_GOAL_ENTRY_READY_FOR_INTEGRATION_DECISION (see §K; written by the Codex session, closed on handoff by Claude). Branch `research/generalized-goal-entry` from verified96569792; no merge/push, Gemini0, defaultLLM_ONLY, HybridNO-GO, cache125.

## A–D: capability and architecture

**A:** New goal = length from an unnamed described midpoint to one named point, e.g. “Tính độ dài đoạn nối trung điểm của SC với A.” The resolver composes existing midpoint→ask_length; four solid families measured.

**B:** Goal metadata selects an answer effect; bounded search selects producers and call templates. Zero new goal-specific function-composition recipes. One mathematical answer contract added to ask_length; it never names midpoint. Flat point-pair decoding and source/engine verification remain bounded to supported meanings. Area/volume/angle cannot yet be promised from catalog data alone.

**C:** Adding a centroid producer contract as data enables2/2 length forms without Planner/gate/Engine edits. Its independent descriptor predicate already exists. This demonstrates recomposition within known effects/predicates, not arbitrary function invention.

**D:** Reused Registry templates, resolver, source coverage, Gram metric, exact kernel, IR, interpreter, Scene3D and shared renderer. New geometry functions0; functions reused2 (midpoint,ask_length), experimental producer1(centroid). New composition forms2, not8 algorithms. Missing: nested descriptors, two unnamed operands, generic non-length measurement verification and live extraction. Contract: `docs/architecture/GENERALIZED_GOAL_ENTRY_CONTRACT.md`. TypedFact fields/schema and provider prompts/declarations unchanged; admissibility expands an already precise representation.

## E–F: preregistered measurements

Corpus/oracle/labels registered before product edits;21 new cases DEVELOPMENT_NOT_HELD_OUT. Same Typed Facts for every arm; no label edited after RED. Results in `results/comparison.json`, summary in `results/summary.json`.

| Arm | New correct / false refusal | Negative correct code / wrong code | Wrong served |
|---|---|---|---|
| FIXED2a3c0787 | 0/8 | 5/6 | 0 |
| BOUNDED8c24cb52 | 0/8 | 5/6 | 0 |
| DISCOVERY96569792 | 0/8 | 0/11 | 0 |
| NEW production | 8/0 | 10/1 | 0 |
| NEW+centroid | 8/0, plus2/2centroid | 10/1 | 0 on new length corpus |

One new wrong-code refusal is a registration error: contradictory SA lengths were labelled INCONSISTENT_CONSTRAINTS, established Engine policy uses INCONSISTENT_FACTS. Label preserved, mismatch counted; strict expected-failure benchmark assertion retained alongside a passing assertion of the actual fail-closed code. Previous D-1 unchanged. No product error policy was altered to satisfy a mistaken oracle label.

NEW vs DISCOVERY: **0 changed outcomes on153 prior rows** (125 older benchmark/result-binding/two-line +28 FD). These are not153 new held-out cases. Reversed Registry retains outcomes174/174. Removing length or midpoint contracts removes new capability. Lying descriptor and answer contracts are rejected independently by Engine.

Centroid variant serves one old conditional negative (centroid-without-contract); raw classifier calls that wrong-served although its answer matches the existing independent centroid oracle. Report separately; do not relabel or pool into production safety.

New positives: needs5, candidates2, depth2, calls5–7; route8.8–21.7ms, planner4.82–7.43ms under tracemalloc, peak81,485–86,034bytes. One host/run/order, descriptive only. Composition branch addition0. RED43fail/1pass; focused GREEN183pass/2xfail; final new-slice49pass/1xfail after supplemental tests. Metamorphic rename/order/reversal/scale, repeat/mixed goals, named reuse, five budgets and certificate/source forgery tested.

## G: Scene3D and checks

Independent W1–W3 review PASS_WITH_FINDINGS (`review.md`). One inherited hidden-source witness defect fixed in shared renderer RED→GREEN; seven prose errors corrected via `scene-corrections.md`, originals untouched. No new renderer or Kernel.

`visual/browser-attempt3/receipt.json`: Product store injection of unchanged exact route scenes, first/middle/final steps, midpoint selection, identical rendered-object sets in shared harness, and existing projection scene hide/source/witness check;0 page exceptions. Minimal shell config bypasses API/provider; this is not NL product E2E. First browser sandbox attempt interrupted by environment; second failed from a tooling selector; third passed. Human acceptance NOT_APPROVED; earlier user screenshots unavailable.

T1 frontend geometry709pass; T2 full frontend1062pass+typecheck/build. First T2 missing CODE_INDEX entry fixed. Broad T0 interrupted after sandbox permission errors and stale candidate identity; no PASS claim for that attempt. Final detached verification is recorded separately below/in run.json.

## H: identities and integration

Stack main2a3c0787→ResultBindingf83b4ed1→Scene3D8c24cb52→FD96569792→this branch. Product/candidate/refreeze/T3/evidence identities in run.json and receipts are distinct. Final T3 pending at this checkpoint. User frontend/public untouched. No merge/push/cherry-pick/branch deletion.

READY_FOR_USER_DECISION requires final detached T3 and identity checks. This concerns bounded offline research integration only; historical source grammar residuals continue to block Hybrid activation. Human review remains separate.

## I–J: claims and next work

MEASURED offline:8/8new exact lengths vs0/8three old planners,0wrong served,10correct-code/1wrong-code negative,153previous outcomes unchanged,2extra length forms from one producer contract without algorithm changes. Author-designed corpus; no new held-out, universal generality or learner-effect claim.

NOT_MEASURED: Gemini intent/reference extraction, free Vietnamese understanding, live latency/tokens/cost, learner outcomes. Five-layer NL evaluation design in semantic-corpus.json; no provider change/call.

Next research priority: semantic-understanding/grounding evaluation design and known source false-serve closure before G16. Both planner slices now work on authored facts, while extraction is unmeasured and source residuals can omit requests. G16 still lacks a measured angle-construction/annotation path; evidence does not justify Kernel expansion first. Live evaluation needs separately approved budget/stopping rules.

Postflight: Registry/resolver/gate/Engine/IR/renderer reused; new product modules0; created measurement/test/docs only; no duplicate engine/state or import cycle.

## K. Handoff verification (Claude Code, after the Codex session hit its usage limit)

Nothing of the Codex session was committed. Before any edit the uncommitted work was copied outside the repository (tracked
patch + untracked tar; restore onto a detached worktree verified byte-identical, three docs identical modulo line endings,
raw copies kept). It was then committed as found, in order: preregistration/oracle/corpus/baselines `067147d5`, tests
`b41b4181`, product `193e634a`, Scene3D witness fix `289007a4`, tooling `3d07ddb4`, Codex evidence `140ae4ed`.

| check | result |
|---|---|
| preregistration order | mtimes put preregistration/oracle/corpus (20:41) before the last product edits (20:43-20:55); git cannot prove they preceded the first edit — reported as such |
| freshness of Codex numbers | `planner.py` was last edited (20:55) after the comparison (20:49) and browser receipt (20:52) ⇒ all arms re-measured on committed `193e634a` (`results/final-193e634a/`): identical to the Codex measurement on 174/174 rows |
| regression | 153 earlier rows identical to Function Discovery in status/code/answers **and** plan stats (calls, functions, fresh labels, planner errors); reversed registry identical; 0 wrong served in every production/ablation arm |
| red test the Codex session did not run | the positional-binding mutant still targeted the old source line; rebound to `child.contract.effect.operands` (same kill check) in `b41b4181` |
| scenes / browser | `visual/scenes.json` re-exported byte-identical from the committed product; frontend unchanged since the Codex browser run ⇒ `visual/browser-attempt3/receipt.json` holds; key images inspected |
| independent review of the final planner edit | a read-only review agent was started and stopped by a provider usage limit before reporting; replaced by 21 adversarial probes run here (below) — not an independent reviewer |
| frontend | vitest 1062/1062, `tsc -b` exit 0, `git diff --check` clean |

Adversarial probes (`run_fact_route`, real route): other target/descriptor in the text, reversed phrase, two targets, follow-up
volume, "nửa", asserted value, target not in source, two/three-label targets, `line_ref`, `points_a`, area quantity, named
length with 1/3 points, repeated ask — **0 wrong served**; the descriptor operand itself as target (S) is served correctly
(√17/2). Conservative false refusals recorded: "… bằng bao nhiêu?" (`QUESTION_CONTEXT_UNSUPPORTED`, the closed sentence only
reads "Tính …") and "đoạn nối A với trung điểm của SC" (`SOURCE_OBJECT_MISMATCH`). Inherited presentation limits (same on the
named route-D length "Gọi M là trung điểm SC. Tính độ dài MA."): the asked segment MA is not drawn by default (it appears
with the quantity) and the narration says "khoảng cách" for a length.

Final identities, refreeze and authoritative T3: `run.json` and `verification/`.
