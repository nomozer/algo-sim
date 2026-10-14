# Independent final targeted re-review — LOCAL

Reviewer: `/root/final_independent_review`, fresh context (`fork_turns=none`), same model family, read-only.
Independent reviewer session; not human approval or a different-model evaluation. Requested by the user; review completed
2026-10-14. Actual source/tests and connected consumers inspected, not solely prior reports.

Reviewed HEAD `d3c7381adbbf46be91382ffa8a38edeae13b2e4b`; final product
`a5a0797ce600734d52eb92c3e763e52a85365b5e`; freeze `f227dd7249d09ee877e024b3fdb1821d7c581b9c`.
Final-fix range `38c304ce..a5a0797c`; sequencing range `09b29d48..a5a0797c` and connected formation/scene/display/frontend
consumers. Reviewer verdict **NONBLOCKING**. Critical: **none found**. Important: **none found**.

## Source findings

- `backend/app/simulation/geometry_functions/engine.py:138`: backward dependency closure is correct for dependency-ordered
  point blocks from `_dat`/`giai_phu_thuoc`; stable partition retains every block and statement. No new geometry authority.
- `engine.py:785`: final height-foot fix uses the same `formation._chan_ung_vien` helper and topology contract as downstream
  formation. Foot, supporting plane and dependencies precede the solid; height step is preserved. Section/measurement
  dependencies remain correct. No dependence on one example's vertex names.
- `engine.py:109`: ordinary/regular pyramid/prism topology requires matching source notation. Right/oblique distinction
  preserved (`right` versus `None`), with ASCII apostrophe, `′` and `’` supported. No invented source topology.
- `backend/app/ai/function_route.py:41`: midpoint endpoints and translation operands are typed and named from presentation
  metadata; `H = M + (C − B)` is narrated as `MH = BC`. Event/formation text stay synchronized; rename/name-collision
  controls pass. No machine-variable explanation or inferred premise added.
- `frontend/src/simulations/domains/geometry/scene3d-model.ts:571,1090`: visibility and learner grouping read authoritative
  snapshots; no second frontend timeline. Object IDs, auxiliary selection, playback and occlusion receipts remain valid.
  LLM_ONLY default unchanged. Prior shared label-overlap fix remains separately documented in scene3d-construction-audit.

## Reviewer's read-only checks

126 offline pytest tests (sequencing + two-line suites) PASS. Reviewer independently reproduced all 36 registered cases:
33 served/3 refused, final records equal, baseline mathematics/coordinates/refusal outcomes unchanged, no lost roles/IDs.
Additional in-memory probes: 6 height controls (ordinary, regular triangular, regular square pyramids, original + renamed),
500 dependency-DAG partitions and 6 prime-mark/right-oblique topology controls PASS. These probe counts are the reviewer's
reported checks; they were not added as permanent tests or claimed as a new held-out corpus.

Four-scene re-export byte-identical SHA-256
`09ca4b4e434d3c11036c0bf2f132459c94a6e73387bae219782e2778140f3d35`. Existing SwiftShader/Intel D3D11 browser receipts pin
that input and show zero failures/console errors, stable occlusion, zero changed pixels on step revisit and correct
auxiliary selection. Chrome was not rerun. Root separately ran clean-detached 220 backend/163 frontend tests, with receipts.

## Nonblocking and evidence limits

1. Permanent height regression test (`test_pedagogical_sequencing.py:38`) covers ordinary square-pyramid projection;
   implementation passed broader reviewer probes. Future parameterization could preserve that coverage; not required here.
2. General ordering checker (`construction_sequencing.py:9`) does not require CONSTRUCT_HEIGHT. Dedicated regression checks
   base → height → closure; inherited limitation remains disclosed.
3. Browser receipts cover three representative served scenes + one refusal, not every height variant or production API/UI.
4. Human visual approval remains pending; orbit gate remains unresolved. No claim of all Vietnamese wording support.

Reviewer did not mutate files/Git or call provider/network. This review fills the post-`a5a0797c` receipt gap. No review fix
was required, so no product change/refreeze/T3 rerun was performed.
