# Goal-directed section planning — LOCAL Windows, 2026-10-12/13

Branch `research/goal-directed-section-planning` from `main` = `origin/main` = `132e9b23`. No merge, no push.
Hybrid stays a research route: `LLM_ONLY` default, `CACHE_VERSION` 125, IR schema and renderer unchanged; 0 live calls.

## A. Semantic correctness — follow-up hypothesis change

Root cause: the ask grammar `_SAU_HOP_LE` accepts a next-task connector (rồi, sau đó, từ đó, bằng cách) after the asked
phrase and stops reading; the coverage gate opened obligations only at given markers. So "Tính SC, sau đó thay SA bằng
5 và tính lại SC." served the old figure on routes A and B, for asks and for construction requests.

Fix (bounded fail-closed, one authority — `registry._kiem_du_kien_cau_hoi`; no new parser, no fact overwrite):
- one constant `_VIEC_KE_TIEP` (now also tiếp theo / tiếp đó) feeds the ask grammar and the gate;
- a follow-up span is read like a given fragment: after covering length/shape assertions against validated calls,
  only a closed vocabulary may remain (given words, comparison of named objects, rounding, scene presentation,
  further connectors); a goal clause covers itself up to ";"; "bằng cách" only names a formula or theorem;
- a length asserted after the first request must match a validated call, whatever its position or lead word;
- a modified re-request (the asked object as the request verb's direct object again: "tính lại SC", "SC lần nữa",
  "SC mới") is refused — the request only makes sense under a changed hypothesis.

Evidence: `test_question_followup_context.py`, 125 tests on routes A/B: 34 changed-hypothesis forms refused (27 ask,
5 construction, 2 goal + ";"; same and next sentence; short quotes), multi-step and multi-part controls served, fault injection per rule.
RED at `132e9b23`: 32 failing of the first 70. The first token-based attempt (`87118b61`) was replaced after review.
Unsupported by design (documented conservative refusals): open follow-up wording ("sau đó gọi M là trung điểm SC",
"so sánh SC với 4", "kết luận …"), "Tính SC. Tính lại SC.". Still open: a change after "," / "và" inside a goal clause
and a premise sentence outside every quote — both pre-existing at `132e9b23` (`ISSUE-ARCH-HYBRID-QUESTION-LOCAL-GIVENS`).

## B. Goal-directed construction planning

Reuse audit (read in code, not inferred from names):

| Capability | Existed | Missing | Authority used |
|---|---|---|---|
| Midpoint | Registry `midpoint`, engine placement, IR `midpoint` | — | unchanged |
| Plane through point ∥ plane | kernel `plane_through_point_parallel_to` (no caller); IR note: express it by translating M along two directions of (ABC) | a planner rule and a call shape | IR `vector_from_points` + `translate` via planner-only `translate_point` |
| Plane representation | IR `construct_plane` through three named points; engine `_plane` | a typed way to say "(P) through M ∥ (Q)" | Typed Facts `plane_relation` (+ prompt rule 8) |
| Plane–solid section | IR `construct_section`, kernel `section.py`, engine `kiem_mat_cat` | — | unchanged; degenerate codes kept |
| Dependency ordering | engine `giai_phu_thuoc` | translate as a construction | engine construction loop |
| Postconditions | construction relations, `kiem_mat_cat` | derived-plane checks | engine `_kiem_mat_phu` |
| Scene3D replay | function route → Scene3D, step trace | — | unchanged |

`geometry_compiler` was not changed and not reused: it compiles whole programs for contract families and has no per-goal
rule table on the Hybrid call surface; adding the rule there would create a second authority for the same route.

Planner (`planner._mat_qua_diem`, rule `MAT_SONG_SONG`, depth 1, ≤ 4 derived planes): `Section(solid, Plane(M ∥ Q))`
→ `translate_point(M, Q₀Q₁→) = X₁`, `translate_point(M, Q₀Q₂→) = X₂` (fresh auxiliary labels) → `section` /
`ask_section_area` on (M, X₁, X₂). One derived plane per (solid, M, Q), shared by the construction and the area question.
Trace step `decompose_goal` records goal, dependencies (`VerifiedPoint M → ParallelPlane → Section`), calls and reason.
`translate_point` is planner-only: not declared to the provider (route A surface `912b22ef`, declarations `f2ec9698`
unchanged), refused anywhere else (`AUXILIARY_ONLY_FUNCTION`). Perpendicular to a plane ⇒ `PLANE_NOT_UNIQUE`.
Engine: places M, X₁, X₂ in dependency order (kernel `translate`, checked by an independent parallelogram relation),
checks the plane is parallel to Q (`predicates.parallel_planes`), is not Q (`DERIVED_PLANE_IS_REFERENCE`) and is not a
face (`SECTION_PLANE_IS_FACE`; vertex/edge touching keep the kernel codes). Source gate: "(P) [đi] qua M [và] song song
với (Q)" must end its sentence (or be followed only by the section request on (P)), be a premise, not negated, and be
referred to by the section phrase or written inside it; the asked area must be that section; a second definition of (P)
in the same grammar is refused. The plane is labelled by its source name "(P)" (else "(α)").

Measured on the three exported problems (0 model calls): 9 calls / 8 distinct functions for a pyramid section + area
(7 / 6 for the prism); 2 `translate_point` per derived plane; planner median 0.61–0.67 ms; full route 12–16 ms.

Exact oracle (independent brute-force section in the test file, canonical Euclidean coordinates, exact angle ordering,
area² by cross products; prism by squared Heron): pyramid M = mid SC ∥ (ABCD) area² 1; M = mid SA ∥ (ABCD) 1; mid SC ∥
(SAB), mid SB ∥ (SAD), mid SD ∥ (SBC) — all equal to the engine; prism M = mid AA' ∥ (ABC) area² 3. Relabelling keeps
the answer; doubling all lengths gives area² 16. Reviewer probes added cube and more prism planes, all agreeing.
Tests: `test_goal_directed_section_planning.py`, 36 tests; RED 18/21 at `062b204f` (before Phase B).

Supported new problem shape: "M là trung điểm (đoạn có tên). Dựng (P) đi qua M và song song với (mặt có tên). Xác định /
tính diện tích thiết diện của (khối) với (P)." for pyramids and prisms, in route B. Limits: `ISSUE-ARCH-HYBRID-DERIVED-PLANE-LIMITS`.

Scene3D (harness `scripts/hybrid-section-visual.html` on real route output — not the product page): three scenes on
SwiftShader and on the hardware GPU (Intel UHD, ANGLE D3D11): no failures, no console error, the section draws its own
pixels at the default view and after orbit, appears after its dependencies (step 10/16, prism 8/13), orbit and zoom
settle, reset returns to the first frame (residual 0). Screenshots show the section at half height, M on it and the
plane through M; in the prism the two translates are exactly the midpoints of BB′ and CC′. The section caption reads
"… cắt bởi (MHH1)" (shared display layer, unchanged). Page loads were retried 15 (SwiftShader) / 9 (GPU) times on the
known local-connection resets, each reported by the harness.

## C. Verification

- Independent LOCAL reviews ×2 + one verification (`review.md`): one BLOCKING round (I1–I3) and the follow-ups closed
  RED → GREEN; residuals recorded open.
- Candidate refrozen in a clean detached worktree at product commit `68fbc844`, committed separately as `a443d2a2`:
  `6110cd67d51838375cc3500f0833bd1c26ef4028dd6cf0c17f042266c0e5ddb5`, 110 files, `--verify` PASS; divergence chain
  extended in `inputs/candidate_divergence.json` (corrects `question-local-givens-final-review`).
- Provider surfaces: A `912b22ef…` and declarations `f2ec9698…` unchanged; B `396f1c9c…` → `4a20601f…` (one optional
  Typed Fact field + prompt rule 8), pin updated in `test_hybrid_goal_decomposition.py`. Real-provider extraction of
  the new field is unmeasured.
- Benchmark 30 cases, both arms 19/9/0/2, metrics SHA256 `febb5b60…` byte-identical (taxonomy +4 codes only).
- Clean detached T3 at `a443d2a2`: **FULL_PRODUCT_GATE_PASS**, exit 0; backend 8925 passed / 0 failed / 1 skipped /
  2 deselected / 5 xfailed; frontend 1053 passed (68 files); typecheck/build PASS; demo 5/5; crash surface PASS.
  `verification/t3.log` SHA256 `1845f98054c9e3bb31f63136d903c3f428d37d268ae8cdfee010291d0d12dc86`.

## D. Recommendation

GO for a bounded local integration of this research branch after the user's decision (no product enablement, no
default change, no live claim). Process notes: a temporary verification worktree was once removed with `--force`
(own patch, nothing lost) and one test edit used `sed -i` instead of Edit — both against the stated rules, recorded here.
