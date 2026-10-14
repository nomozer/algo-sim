# Two-line plane section implementation plan

**Goal:** new bounded goal composition on the existing Hybrid Planner, preserving strict line/plane semantics.
**Spec:** `docs/architecture/TWO_LINE_PLANE_SECTION_CONTRACT.md` (user task provides design/implementation authority).
**Stack:** existing Python/Fraction/Pydantic IR/React Scene3D; no dependency addition.

## Preflight

Branch research/goal-directed-two-line-plane-section, base main=origin/main5270f3dd; dirty only user frontend/public/.
Classification CORE (bounded construction capability), supporting oracle/browser/tests. Source of truth code/tests+spec.
Reuse Planner `_mat_qua_diem`, `KeHoach.derived_planes`, `translate_point`, Kernel predicates, section IR and Scene3D.
Files: planner/registry/engine, B fact_extraction prompt, focused tests/research oracle/export/harness, docs/candidate.
Schema B changes intentional; A/IR/default/cache unchanged. Duplicate/cycle risk constrained by one existing authority,
depth1/MAX_CALLS64/MAX_DERIVED_PLANES4. Exclude general parser/search, DSL, new engine, live/default/merge/push.
Stop if architecture must expand, wrong served remains or mandatory review unavailable. Preserve all protected data.

- [x] Preregister corpus and independent math oracle, seal heldout; commit before Planner edits.
- [x] RED minimal positive/strict-contained/parallel-direction/source/adversarial controls at base.
- [x] Extend schema and SAME rule plumbing: point + two lines, fresh translates, shared plane, strict postconditions.
- [x] GREEN exact oracle and mutation/metamorphic/adapter/dependency checks; baseline 30 cases separately.
- [x] A acceptance before deciding B; B deferred if reuse/gates insufficient.
- [x] Independent LOCAL read-only review; fixes RED→GREEN plus final rereview.
- [x] Real Hybrid Scene3D exports; existing harness, SwiftShader + available GPU; no API/product-page claim.
- [x] Product commit, clean refreeze + additive candidate divergence; clean detached T3/doc/identity gates.
- [x] Commit receipts/handoff; clean only this task's verification worktrees/junction/temp/processes; main remains base.

Ruling: A is the frozen accepted scope; B remains a separate unaudited containment/source variant, not an A alias. Math reuse is available; this is not a claim that architecture must grow. Cost: B questions still refuse.
Ruling: exact local WinError10013 fixture retries are bounded3 and reported; all geometry/assertion failures stop. Cost: local infrastructure can still block the gate after three tries.
Verification: T3 clean69ff3a16 PASS backend9274/frontend1053; initial taxonomy FAIL, fixture ERROR and interrupted run retained as receipts, never credited. Native physical cleanup removed all three owned trees; shared node_modules protected.
