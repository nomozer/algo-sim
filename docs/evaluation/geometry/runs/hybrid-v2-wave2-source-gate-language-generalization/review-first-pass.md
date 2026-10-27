# Independent Source Gate review — first pass

Reviewer: `independent_review`, separate agent context. Date: 2026-10-28.
Reviewed baseline HEAD `6554d733203619dad9ea8c4c640fc80ee5782a34` plus uncommitted Registry `/19` implementation.
Registry file SHA-256 at review: `324aceefdf1257c1f9a03de369053e0b3e9a45df3d0abc89aa6a7f1cecdb9b49`.
Locked development corpus SHA-256: `d5d8d8ac94071bcced3522fe8f4bc7b93313fe927a70c7c8902122902663d9fa`.
No product, locked input, expected outcome, or raw result was modified by this review.

Verdict: **REVIEW_FINDINGS_REQUIRE_ADJUDICATION; NOT_READY**. No product fail-open was established in this pass. Two acceptance/evidence issues below require explicit resolution; Full T3 and final freeze review remain pending.

1. **MAJOR — one preregistered negative is mathematically a valid positive.**
   `NEG-unproven-two-line-premise` copies `DEV-4-2` and appends `Biết AC vuông góc với AB.` The payload already states that triangle ABC is right at A. This is the same perpendicular pair, not an unsupported or contradictory extra premise. Source Gate `_cau_tien_de_dong_hop_le` already matches a perpendicular-lines assertion to the `right_angle` call by its vertex/rays; accepting this redundant assertion preserves the existing authority.

   Independent exact coordinates: A=(0,0,0), B=(12,0,0), C=(0,18,0), A'=(12,0,10), B'=(24,0,10), C'=(12,18,10). Then AB·AC=0, A' projects onto B, and A'B=10. M divides AA' with t=4/9; the cutting plane is z=40/9. The section is the translated triangle with vertices at t=4/9 on AA', BB', CC'; its area is 108 and area squared is 11664. An independent product execution with the positive oracle confirms route SERVED, Adapter4 SERVED, envelope ok, Category B, `area_squared=11664`, and zero oracle mismatches. This is a corpus expected-label error, not a genuine wrong-served product result.

   Required action: preserve `development.json`, `red-before.json`, and every GREEN attempt byte-identically; add an explicit adjudication receipt correcting interpretation and reporting raw vs adjudicated counts separately. Do not weaken the gate to reject this valid redundant assertion. Add a truly unproved or contradictory MAT premise control independently. Reviewer executed `Biết AC vuông góc với BC.`: REFUSED/SOURCE_PREMISE_UNREAD; `Biết AC song song với AB.` and `Biết AB = AC.`: REFUSED/QUESTION_CONTEXT_UNSUPPORTED.

2. **MAJOR — the locked positive acceptance gate is incomplete.**
   `DEV-1-3` is a mathematically correct horizontal section of triangular pyramid T.EFG with EF=13, EG=19, TE=11, TJ/TE=5/11. Its expected area squared `38130625/58564` is correct. The engine refuses an intermediate radical above the existing ceiling (reported radicand 2233081922500), so raw GREEN remains 23/24 on the original positive subset. This is the explicitly excluded W2-M4 class; changing Engine/Kernel would exceed this authorization. It must remain a disclosed false refusal, not be called fixed or silently omitted.

   Required action: keep the failed row and its exact interpretation. Any supplemental positive or task-scope acceptance layer must be independently preregistered, additive, and reported apart from the original locked 24-positive denominator. Current plan/preregistration still demand every locked positive to serve, so no READY claim is supported merely by replacing the difficult row. Record the unmet literal acceptance condition or obtain the necessary scope decision if it remains mandatory.

Product binding assessment:

- W2-M1 uses one regex with separate point-first/inverted captures and the existing exact Fraction solver. It checks three distinct labels, same-clause equation operands, canonical unordered subsegment lengths, endpoint order, and complementary ratio on a reversed source edge. `_ty_so_tron_cau` verifies the complete premise with only bounded introducers and sentence punctuation. No second ratio authority or geometry inference was added.
- W2-M2's new `đỉnh` target branch requires exactly one solid containing the source point and target-plane labels and requires the image in that same solid's vertices. Context is request-local via the existing `_GOI_NGUON` set/reset wrapper. Reviewer constructed a geometrically consistent projection onto midpoint P of AB: with noun `điểm P` the full path serves; with `đỉnh P` it refuses SOURCE_PREMISE_UNREAD. This demonstrates the noun cannot turn a derived midpoint into a solid vertex.
- W2-M3 reuses `_ty_so_tron_cau` for the whole standalone ratio premise. Generic prism wording expands only the grammar guard; existing notation, kind, rightness and `_loai_cum_dung` checks still decide admissibility. The added right-angle standalone form delegates operand matching to `construction_source_bound`.
- The unchanged I-1 contradiction policy remains in force. No change to engine arithmetic, planner geometry, adapter, schema, default routing, OCR, or frontend was found in the product diff reviewed.
- All 36 genuinely adversarial locked rows refuse in their registered codes. The apparent 37th negative is the valid redundant premise adjudicated above. No accepted refusal here relies on an internal exception code.

Independent oracle/scorer assessment:

- Recomputed all 24 positive oracles independently using rational orthonormal coordinates, lateral-edge/constant-z plane intersection, and the polygon cross-product area vector. **24/24** match the locked `area_squared`, boundary edge parameters, and vertex counts exactly. This independent calculation imports no geometry product/oracle code. Pyramid sections scale by the parameter measured from the apex; sheared-prism sections retain base area.
- The new evaluator loads the historical corrected scorer from pinned Git commit `ecdc26b0` and asserts its exact SHA-256. It requires route + Adapter4 + envelope served and checks exact boundary/certificate/area against independent expectations. It preserves raw attempts using exclusive output creation. The broad negative code list excludes generic engine/internal failures; the reporting layer must still state exact observed codes.
- The scorer cannot distinguish a wrongly authored negative expectation from a genuine wrong serve without independent mathematical adjudication. That is precisely the first finding; raw outcome labels must not be silently rewritten.
- Original-corpus identity, RED provenance, and baseline historical receipts remain intact. Supplemental corpus, Wave2 replay, identity pins, cache decision, candidate freeze and Full T3 were still in progress and are outside this first-pass approval.

Independent execution in the new worktree, with `ALLOW_LIVE_AI=0` and bytecode/cache writes disabled:

`python -B -m pytest backend/tests/geometry/test_solid_kind_source_binding.py backend/tests/geometry/test_two_line_plane_section.py -q -p no:cacheprovider`

Result: **218 passed in 9.05s**. These are targeted I-1/two-line regression tests, not Full T3. Additional manual product controls above all behaved as stated. Final independent review must check the adjudication, retained raw denominators, remaining literal acceptance gap, full six-family/Category A+B regression, product commit identity, freeze MATCH, and complete authoritative T3 receipt before any READY status.
