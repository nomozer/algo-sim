# Plan — pedagogical construction sequencing (2026-10-14)

Branch `research/goal-directed-two-line-plane-section` after `5bd28d73`; main `5270f3dd`; no push, no Gemini, Hybrid off.
Closes `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`.

**Audit → option A (minimal).** The learner sees `trace[k]` at frame k (invariant #31), so a frontend-only timeline (B)
would break that. The IR order IS the learner order, and it comes from two Hybrid-only places:
- `geometry_functions/engine.py::bien_dich` emits every point block (M, vectors, H, H1) before the solids. Fix: a pure
  topological split — point blocks a solid needs (transitive) first, then solids, then the remaining blocks in their
  original order. Same statements, same values; kernel results unchanged by construction.
- `hop_dong_to_po_da_khai` declares topology only for pyramids, so the existing formation completion
  (`formation.hoan_thien_dung_hinh`, shared, unchanged) cannot classify prisms/cuboids and shows them in one step. Fix:
  declare `PrismTopologySpec` only when the source quote writes the `ABC.A'B'C'` notation matching the call.
- Narration "Dựng M." (`scene3d.py`, shared with LLM_ONLY — not touched): the Hybrid scene layer
  (`ai/function_route.py`) rewrites the step text of constructed points from producer + operand notation.

Not done: changing the shared prism formation order (base → top face → lateral edges) to lateral-before-top — it is the
default-route contract (`TOI_THIEU`) and would change LLM_ONLY scenes.

Corpus registered before the fix: `inputs/corpus.json` (6 development, 30 ordering-check never used for ordering, two-line
heldout 32 excluded). Baselines: `before/development.json` (ordering RED), `before/ordering_check_math_only.json`.
