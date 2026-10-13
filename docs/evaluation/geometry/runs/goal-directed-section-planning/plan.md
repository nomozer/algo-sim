# Plan — goal-directed section planning (LOCAL, 2026-10-12/13)

Branch `research/goal-directed-section-planning` from `main` = `origin/main` = `132e9b23`. No merge, no push.

## Phase A — semantic correctness (follow-up hypothesis change)

- [x] Root cause: `_SAU_HOP_LE` accepts a next-task connector after the asked phrase and stops reading; the coverage gate
      opened obligations only at given markers ⇒ "Tính SC, sau đó thay SA bằng 5 và tính lại SC." served the old figure.
- [x] RED (route A/B, ask + construction, short quotes) → closed fix in `registry._kiem_du_kien_cau_hoi` (one constant
      `_VIEC_KE_TIEP` for grammar and gate; closed follow-up vocabulary; lengths after the first request must match;
      modified re-request refused). The first token-based attempt (87118b61) was replaced after independent review.
- [x] Independent review ×2 + verification; Critical/Important closed RED → GREEN; residuals recorded as open.

## Phase B — goal-directed construction planning

- [x] Reuse audit (kernel `plane_through_point_parallel_to` unused; IR note: the plane through M ∥ (ABC) is expressed by
      translating M along two directions of (ABC); engine `construct_section` via a plane through three points;
      planner `_phan_ra` + `AUXILIARY_RULES` as the decomposition precedent; `geometry_compiler` not reused — it emits
      whole programs for contract families and has no per-goal rule table for the Hybrid route).
- [x] Representation gap proved (Typed Facts relate named objects only; `section.points` needs three named points) ⇒
      one optional field `plane_relation` + prompt rule 8; route A surface unchanged (planner-only `translate_point`).
- [x] RED 18/21 at 062b204f → GREEN; independent exact oracle; metamorphic (labels, scale); degenerate contract;
      fault injection; Playwright harness on SwiftShader and GPU.
- [x] Candidate refreeze (separate commit), clean detached T3, benchmark, docs.
