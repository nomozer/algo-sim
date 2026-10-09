# OPEN_ISSUES.md — Danh mục các vấn đề kỹ thuật đang mở

> **Tài liệu Canonical cho việc theo dõi các vấn đề và giới hạn kỹ thuật của hệ thống.**
> Mọi issue đều có Stable ID theo tiền tố chuẩn: `ISSUE-ARCH-*`, `ISSUE-EVAL-*`, `ISSUE-DOCS-*`, `ISSUE-OPS-*`, `ISSUE-RESEARCH-*`.
> Chỉ ghi nhận các vấn đề được xác nhận bởi bằng chứng thực tế từ repository.

---

### ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE
- **description:** The compiler writes one hand-made statement sequence per family. The triangular pyramid (`bien_dich`) and triangular prism (`_bien_dich_prism`) emit no height segment, no lateral-edge group and (prism) no top face, so their timeline is only givens/points → base → whole solid; the rectangular pyramid and box paths have those steps. Root cause of the w12 human findings W12-H1/H2.
- **evidence:** `backend/app/simulation/geometry_compiler/compiler.py` (`bien_dich` ~917, `_bien_dich_prism` ~1046, `_bien_dich_rectangular_pyramid` ~1153, `_bien_dich_cuboid` ~1315); `docs/evaluation/geometry/runs/w13-geometry-preregistration/inputs/W12_HUMAN_VISUAL_REVIEW.json`; inventory item NA-18.
- **impact:** Formation quality depends on which family a problem lands in; patching the two families alone would repeat the defect for every new shape.
- **scope:** `backend/app/simulation/geometry_compiler/`, trace events / `scene3d` formation.
- **status:** RESOLVED (w15, decision W15-D1 of the brief) — a program the product refuses and for which no learner scene exists is not required to show a complete formation. The gold negative `n2_khoi_ghep_bu_can_boolean` keeps its job of being refused correctly: at `structural_coverage` with `REQUESTED_OPERATION_UNCOVERED`, structured fields filled, and no answer or scene (`tests/geometry/test_product_response_contract.py::test_n2_bon_truong_cau_truc_NHAT_QUAN`, green in T3 at `c57ebd1b`). Its untyped box is not guessed into `COMPLETED`, and no composite geometry was built for it. The w14 formation pass is kept unchanged: six families × desktop/mobile role coverage 12/12 and playback 12/12 × 19 at `c57ebd1b` (`docs/evaluation/geometry/runs/w15-assumption-closure/`). The four scenes it changed still need a person (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`).
- **w14:** PARTIAL (w14, `44f2dd32`) — one shape-class completion pass (`semantic_program/formation.py::hoan_thien_dung_hinh`, face-table leaf `solid_faces.py`) runs in `route.verify_and_compile` and `pipeline._dung_scene3d` for compiler **and** LLM programs; the compiler no longer hand-writes height, lateral or top statements; roles are produced in `simulation_state` and only carried by `scene3d`; an AST guard forbids family branches. Measured at `380db58c`: role coverage 12/12 (six families × desktop/mobile) against an independent expectation, playback 12/12 × 19, filmstrips in `docs/evaluation/geometry/runs/w14-generic-formation-assumption/images/<family>/FILMSTRIP.png`; served gold p1, p2 `COMPLETED`, answers unchanged. **Not closed:** the refused thesis-gold negative `n2_khoi_ghep_bu_can_boolean` (an untyped box) stays `AMBIGUOUS_TOPOLOGY` — the enforced set as written includes it (user decision W14-D1 in the run's `HANDOFF.md`); the frozen hidden-line expectations no longer transfer to the four scenes S4 changed (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`). No human has reviewed the new formation.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** — (resolved; human re-review of the changed scenes is tracked in `ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`)
- **default_switch_blocker:** NO
- **acceptance:** S1–S3 of the preregistration: every pyramid/prism family shows the required semantic roles as separate observable steps from one code path, with no branch on a family ID.
- **verify:** the semantic-coverage tests and AST guard named in the preregistration.

### ISSUE-ARCH-G05-REMAINING-BASES
- **description:** G05 now serves convex bases fixed by a chain of k − 2 consecutive right angles (both routes). Still refused or not compiled: (1) regular polygons other than the square (`lục giác đều`, `ngũ giác đều`) — not read by `shape_constraint` and irrational in an axis frame; (2) parallelogram/rhombus bases given by an angle in degrees; (3) concave bases (kernel volume is exact, no reader/template); (4) polygons given by COORDINATES on the compiler route — the adapter reads only `segment_length`, so the compiler falls back to the LLM, which serves them through C0 (probe: S.ABCDE with coordinates, V = 8, LLM_ONLY served); (5) right trapezoid phrased `hình thang ABCD vuông tại A và B` or `góc A = góc B = 90°` with a non-adjacent wording.
- **evidence:** `docs/evaluation/geometry/runs/general-polygon-base/labels.json` rows N04, N05, N06; `plan.md` §1.
- **impact:** Correct refusals; coverage of common textbook bases (regular hexagon, rhombus by angle) remains missing.
- **scope:** `shape_constraint.py`, `assumption_gate.py`, `geometry_compiler/` (a coordinate fact kind in `fact_graph.py` for item 4).
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** user decision (item 4 is the cheapest: no model-surface change)
- **default_switch_blocker:** NO

### ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION
- **description:** The rectangular-pyramid and cuboid compiler families accept a quadrilateral base with NO `base_shape` and a single stated right angle as a rectangle. general-polygon-base removed the case of exactly two adjacent right angles (now the G05 family) but kept the single-right-angle case unchanged to avoid moving served compiler rows.
- **evidence:** `geometry_compiler/compiler.py` (`_danh_gia_eligibility_rectangular_pyramid`, `_danh_gia_eligibility_cuboid_prism`, `_uu_tien_day_chuoi`). LOCAL (2026-10-09): `tests/geometry/test_general_polygon_base.py::test_mot_goc_vuong_khong_phuc_vu_hinh_chu_nhat_tu_gia_dinh` (pyramid + prism through `run_pipeline`, `DETERMINISTIC_FIRST`) — compiler picks the rectangle family, route refuses `ASSUMPTION_INVARIANCE_UNPROVEN`, no Scene3D; fault injection (polyhedral gate switched off) turns both red with `status: ok`, so the shared assumption gate is the only barrier.
- **impact:** Compiler-only (opt-in): the program models an unproven rectangle; the assumption gate still refuses it on the route unless the TEXT states a rectangle/square, so no wrong value is served.
- **scope:** `geometry_compiler/compiler.py`.
- **status:** RESOLVED (geometry-grounding-safety, 2026-10-09, `fbade46`) — `compiler._da_chung_minh_chu_nhat`: an untagged quadrilateral is a rectangle only with right angles (between adjacent edges) at ≥ 3 vertices; one right angle ⇒ `UNSUPPORTED_STRUCTURED_RELATION_MISSING` / `BASE_RECTANGLE_NOT_PROVEN` (fallback to LLM) in both the rectangular-pyramid and cuboid families. Eligibility no longer relies on the assumption gate. Declared rectangles/squares/boxes and the G05 chain unchanged (`tests/geometry/test_geometry_grounding_safety.py` R01–R07, `test_general_polygon_base.py::test_mot_goc_vuong_…`).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** before compiler-first routing
- **default_switch_blocker:** YES

### ISSUE-ARCH-C0-SHAPE-TEXT-NOT-CHECKED-AGAINST-COORDINATES
- **description:** When the text pins every vertex by coordinates, certificate C0 makes the coordinates the authority: shape constraints the server reads from the same text (for example the right-trapezoid phrase added by general-polygon-base) are not checked against those coordinates. A text whose shape phrase contradicts its own coordinates (`hình thang vuông tại C và D` while the coordinates put the right angles at A and B) is served from the coordinates instead of being refused as contradictory.
- **evidence:** `docs/evaluation/geometry/runs/general-polygon-base/diagnostics/probe_c0_shape_text_vs_coordinates.py` + `.log` (offline, 0 model calls): both the consistent and the contradictory text are `PROVEN_SAFE` C0, served `V = 6`, with a byte-identical route outcome at `d5287ff7` (before G05) and at `9666b861` — the behaviour predates G05 and G05 does not change it.
- **impact:** The served value follows the stated coordinates, so it is the volume of the solid the coordinates define; the learner is not told that the text's shape description disagrees with them. No served value changed; the gap is a missing contradiction refusal (repository rule: contradictions fail closed).
- **scope:** `backend/app/simulation/semantic_program/assumption_gate.py` (C0 branch: check read `shape_constraint` relations on the pinned coordinates), `shape_constraint.py`.
- **status:** RESOLVED (geometry-grounding-safety, 2026-10-09, `fbade46`) — amendment §21: before C0 is certified, every read `line_perp_line`, `line_perp_plane`, `right_triangle`, `base_rectangle`, `base_square` (+ side), `base_parallelogram`, `base_rhombus`, `base_equilateral` (+ side) whose points exist in the program is checked exactly on the given coordinates; a broken one ⇒ refused `SOURCE_SHAPE_CONTRADICTS_COORDINATES` (cause `SOURCE`, not sent for repair, no Scene3D). `CACHE_VERSION` 118 → 119 (served → refused, `runs/geometry-grounding-safety/cache/decision.json`). Not checked (no reader/predicate): whole-solid kinds (`right_prism`, `cuboid`, `cube`, regular pyramids, `height`) and relations whose points are absent from the program. **LOCAL (`765291ab`):** a point the program does not declare now takes the coordinate the TEXT gives (`point_coordinate` invariant), so `E(5;5;0) … AE vuông góc với AB` is refused even when the program omits E (before: served); a point with no coordinate anywhere is still skipped (missing ≠ contradiction) — `tests/geometry/test_geometry_grounding_safety.py::test_c0_diem_vang_trong_chuong_trinh_kiem_bang_toa_do_de` (fault-injected). Whole-solid kinds stay open: `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** user decision (a refusal turns served C0 rows into refusals ⇒ `CACHE_VERSION` bump by evidence)
- **default_switch_blocker:** NO

### ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED
- **description:** The §21 C0 shape check covers eight relation kinds (perpendicular line–line, line–plane, right triangle, rectangle, square + side, parallelogram, rhombus, equilateral triangle + side). Whole-solid constraints the reader also emits — `right_prism`, `cuboid`, `cube`, regular pyramids, `height` — have no exact predicate in `_KIEM_C0`, so a coordinate text that contradicts one of them (e.g. "lăng trụ đứng" whose given lateral edges are not perpendicular to the base) is still certified C0 and served from the coordinates.
- **evidence:** `backend/app/simulation/semantic_program/assumption_gate.py` (`_KIEM_C0`, `_mau_thuan_c0`); `docs/evaluation/geometry/runs/geometry-grounding-safety/report.md` §5.
- **impact:** Same class as the resolved C0 issue, narrower: the served value follows the stated coordinates; the contradiction is not refused.
- **scope:** `assumption_gate.py` (one exact predicate per whole-solid kind, reusing the template definitions), `shape_constraint.py`.
- **status:** RESOLVED on branch `fix/c0-whole-solid-grounding` (c0-whole-solid-grounding, 2026-10-09, `c11e8c9`; LOCAL verified: candidate `8c4c0128…` frozen at `d838cc5b`, T3 PASS; on `main` since `11be6092`; 15 labelled rows served → refused — LOCAL correction of the 16 in the run report) — amendment §22: before C0 is certified, the whole-solid claims read on a NAMED solid are checked exactly on the coordinates (program, else the text's own `point_coordinate`): `right_prism`, `oblique_prism`, `cuboid`, `cube`, `cube_edge`, `regular_square_pyramid`, `regular_triangular_pyramid`, `regular_tetrahedron`, `edge_all`, `lateral_edge`, `apothem`, `base_centre`, `height` (distance to the base plane, not the lateral edge); broken ⇒ `SOURCE_SHAPE_CONTRADICTS_COORDINATES` (§21 path, no Scene3D, not sent for repair). Baseline `9762f441`: 16 contradictory texts served; now 29/29 labelled rows match (`runs/c0-whole-solid-grounding/diagnostics/probe_9762f441.log` vs `probe_c11e8c9.log`). `CACHE_VERSION` 119 → 120 (`cache/decision.json`). Not checked by design (missing ≠ contradiction): unnamed solids (`entities = ()`), points with no coordinate anywhere, plain `prism` (a non-translated top is already refused at execution). Claims the reader never emits: `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** user decision (served C0 rows may turn into refusals ⇒ `CACHE_VERSION` decided by evidence)
- **default_switch_blocker:** NO

### ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ
- **description:** §22 checks only claims the server reader (`shape_constraint.doc_rang_buoc`) emits. A regular pyramid stated without the `S.ABCD` notation ("hình chóp tứ giác đều có đỉnh S và đáy ABCD", "hình chóp tứ giác đều" with no name) or as "hình chóp đều S.ABCD" (no base-shape word) emits no regularity claim, so contradictory coordinates (apex over a vertex) are still certified C0 and served.
- **evidence:** `docs/evaluation/geometry/runs/c0-whole-solid-grounding/diagnostics/probe_reader_gap.py` → `probe_reader_gap_c11e8c9.log` (3/3 served at `c11e8c9`). LOCAL (2026-10-09): re-run on the branch and on `main` `9762f441` — identical (3/3 served on both, so not a regression of §22); all three are READER gaps, not checker errors: the reader emits no regularity claim (`read: []` for the two phrasings without `S.ABCD`, only `pyramid` for "hình chóp đều S.ABCD"), so `regular_square_pyramid` is never called; when the claim IS read ("hình chóp tứ giác đều S.ABCD", row `RSP_C_apex_over_vertex`) the checker refuses the same coordinates. C0 whole-solid safety is therefore incomplete for these phrasings.
- **impact:** Same class as the resolved C0 issues: the served value follows the stated coordinates; the contradiction is not refused.
- **scope:** `shape_constraint.py` reader phrasings (also feeds the C1 templates — changing it moves C1 rows, so it needs its own labels and a cache decision).
- **status:** OPEN — narrowed (c0-whole-solid-reader, 2026-10-09, branch `fix/c0-whole-solid-reader`, `7d55153`; LOCAL verified: C0 + C1 probes re-run on `a1350da3` and the branch reproduce Cloud's logs byte for byte; candidate `c3f83399…` frozen at `1396878e`, T3 PASS; on `main` since `81ff8899`). **Fixed:** "hình chóp tứ/tam giác đều có đỉnh S và đáy ABCD" (also `đỉnh là S, đáy là ABCD`) and "hình chóp đều S.ABCD/S.ABC" — the reader emits exactly what the canonical notation emits, so §22 refuses contradictory coordinates (10 labelled C0 rows served → refused) and C1 treats them like the canonical notation (equivalence over both regular-pyramid corpora, 94/94); a negated claim ("không phải (là) hình chóp … đều …", canonical notation included) is no longer a premise. Evidence: `runs/c0-whole-solid-reader/` (`labels.json`, `oracle.py`, `diagnostics/probe_*`). **Still open:** the unnamed "hình chóp tứ giác đều" (no apex/base named in the givens): no claim is emitted (no unique binding from the text) and the text is outside the route's polyhedron refusal zone (`neu_khoi_da_dien`), so contradictory coordinates stay served (`P2_*` rows). Fixing it means widening the zone or binding unnamed pyramids in C1 — see `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`. **Further narrowed (unnamed-regular-pyramid-grounding, 2026-10-09, branch `fix/unnamed-regular-pyramid-grounding`, `12edf57`; LOCAL verification + candidate freeze pending):** the unnamed "hình chóp tứ/tam giác đều" is now read (`regular_*_pyramid ()`, names never guessed) and, when every point the text names has coordinates, bound to the program's single solid and checked on each face-table reading (amendment §24): 3 labelled unnamed C0 contradictions refused, 6 consistent/negated/goal rows served (`runs/unnamed-regular-pyramid-grounding/labels.json` `c0_rows`). **Still open:** an unnamed regular pyramid whose text ALSO names a point without coordinates (`U_X_extra_point_without_coordinates`: "Gọi M là trung điểm của SA") or mentions two solids (`U_X_two_solids`) is not bound, so contradictory coordinates stay served — same root as `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** user decision
- **default_switch_blocker:** NO

### ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE
- **description:** A regular pyramid stated with no solid notation anywhere ("Cho hình chóp tứ giác đều có cạnh đáy bằng 4, chiều cao bằng 3. Tính thể tích khối chóp.") is outside the route's polyhedron refusal zone (U3: `neu_khoi_da_dien` = named pyramid/prism or unnamed right prism). The assumption gate runs but is not enforced, so whatever the program computes is served — including answers the same text with `S.ABCD` refuses.
- **evidence:** `docs/evaluation/geometry/runs/c0-whole-solid-reader/diagnostics/unnamed_gap_a1350da3.json` (from `probe_c1_equivalence_a1350da3.log`, variant `unnamed_everywhere`, both regular-pyramid corpora, corpus programs): 37 served — 22 equal the label, 4 serve another value (e.g. `U3_regular_triangular` 5 vs 3√3), 11 serve where the label refuses (e.g. missing height ⇒ 16, irrational height ⇒ 4/3). Unchanged by c0-whole-solid-reader (`probe_c1_equivalence_candidate.log`).
- **impact:** Wrong or assumption-dependent values served on the default `LLM_ONLY` route for unnamed regular pyramids. Widening the zone alone would refuse all 37, the 22 correct ones included, because C1 has no binding for an unnamed pyramid (only an unnamed right prism + square base is bound by its face table).
- **scope:** `shape_constraint.neu_khoi_da_dien` (zone) together with an unnamed-pyramid binding in `assumption_gate._nhan_khuon` (face table, like the unnamed right prism) — a C1 expansion with its own labels and cache decision.
- **LOCAL (2026-10-09):** recomputed from LOCAL re-runs of `probe_c1_equivalence.py` against the corpus labels: 47 rows, 37 served — 22 equal to the label, 4 with a different value, 11 where the label requires a refusal — IDENTICAL on `main` `a1350da3` and on `fix/c0-whole-solid-reader` (pre-existing; the reader fix does not touch it). Not fixed: widening the zone alone would also refuse the 22 correct rows, and no apex/base binding is invented for an unnamed pyramid.
- **status:** OPEN — narrowed (unnamed-regular-pyramid-grounding, 2026-10-09, branch `fix/unnamed-regular-pyramid-grounding`, `12edf57`; LOCAL verified: C1 + C0 probes re-run on `ede8d329` and the branch reproduce Cloud's logs byte for byte; all 47 rows checked by group against the labels; candidate `d07a92de…` frozen at `97db084f`, T3 PASS; on `main` since `2d3c510c`). **Fixed for texts that name no point without coordinates** (26 of the 47 corpus rows, amendment §24): the unnamed claim is bound to the program's single solid and verified like `S.ABCD` (T7/T8 templates, T8 metric, missing-dimension branch); the zone includes these texts. Result vs `ede8d329`: 13 correct kept, the 4 wrong values now served correctly (5 → 3√3, 3/2 → 9/2, 5/2 → 3√3/2, 9/2 → 3√3), 8 label-refused rows refused with the canonical reasons, 1 refused kept — every row equals its corpus label (`runs/unnamed-regular-pyramid-grounding/results/transitions.json`). **Still open (21 rows, unchanged):** texts that name points without coordinates and no solid notation ("có AB = 4, SA = 3", "cạnh bên SA", "SA = SB = SC = SD"): the text does not say which point is the apex — `AB = 4, SA = 3` fits apex S (V = 16/3) and apex B (another volume), checked in `oracle.py` `ambiguity_witness` — so binding them would let the program's labelling decide. 9 are served correctly, 3 are served although their label refuses (`square/N5_apex_over_vertex` 3, `square/R2_N9_contradiction_program_fits_lengths` 16, `square/W5_C_chain_without_value` 16/3), 9 refused. Options (architecture decision): (a) extend the zone to them and refuse as `labelling not fixed by the text` — 9 correct-by-convention answers become refusals; (b) a labelling check in the gate: every injective map of the named points onto the bound solid that satisfies the text must give the same answer — serve only then; (c) keep.
- **LOCAL (2026-10-09, after the §24 fix):** the 21 rows that name points without coordinates are identical on `main` and on the branch; the three served against their label are reproduced and wrong on the text's own data — `square/N5_apex_over_vertex` (a = 4, h = 3 ⇒ SA = √17; served 3), `square/R2_N9_contradiction_program_fits_lengths` (regular ⇒ SA = SB, text says SA = 3, SB = 5; served 16), `square/W5_C_chain_without_value` (SA = SB = SC = SD with no value ⇒ height undetermined; served 16/3).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** user decision recorded 2026-10-09: option (b) — in a SEPARATE Cloud run after the §24 fix is integrated: check every finite, justified assignment of the text's named points to positions of the bound solid; serve only if every valid assignment satisfies the text and gives the same answer; the program's naming is never source data; equal answers alone are not proof of correct geometry; no general constraint solver without new approval
- **default_switch_blocker:** NO

### ISSUE-ARCH-OBLIQUE-PRISM-FOOT-VOCABULARY
- **description:** G04 is served only when the problem states `T F ⊥ (base)` with F a NAMED base vertex (`A'B vuông góc với (ABC)`). The common textbook forms are refused: the foot of the lateral height is a midpoint/centroid/centre (`hình chiếu vuông góc của A' lên (ABC) là trung điểm H của BC`), the projection is phrased `hình chiếu … là (điểm) B`, or the obliquity is an angle (`cạnh bên tạo với đáy góc 60°`).
- **evidence:** `docs/evaluation/geometry/runs/oblique-prism/labels.json` rows ON03, ON08 (refused on both routes); `tests/geometry/test_oblique_prism.py`.
- **impact:** Correct refusals, but the served G04 domain is narrow. Missing links, by layer: (1) `RequestContract`/`RELATION_KINDS` has no structured `midpoint`/`centroid` relation for the foot (model-surface change ⇒ schema export, prompt line, live measurement, cache decision); (2) `shape_constraint` does not read the `hình chiếu … là F` phrase as `line_perp_plane`; (3) angle-defined heights are usually irrational (ℚ³ layout) — needs the affine chart of exact-dimensions or stays out of scope.
- **scope:** `semantic_program/structured_relations.py`, `analyze_contract.py`, `shape_constraint.py`, `assumption_gate.py` (T9), `geometry_compiler/compiler.py`.
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** next G04 slice (user decision: contract extension needs a live budget)
- **default_switch_blocker:** NO

### ISSUE-ARCH-LLM-VECTOR-ASSIGN-NARRATION
- **description:** On the LLM route an `assign v = vector_from_points(P, Q)` is narrated by the shared interpreter fallback as `"Ghi nhận giá trị vừa tính được: Vec3(x=Fraction(…), …)."` — a Python repr in a learner-facing step text. The oblique-prism run fixed it for compiler programs only (`interpreter.py`, `_compiler_geometry`), so that LLM_ONLY envelopes stay byte-identical without a cache bump.
- **evidence:** `backend/app/simulation/semantic_program/interpreter.py` (fallback narration of `AssignStmt`); `tests/geometry/test_oblique_prism.py::test_buoc_dung_ke_bang_ky_hieu_khong_in_repr` (compiler side).
- **impact:** A served LLM program that builds a vector shows the repr in «Các bước dựng».
- **scope:** `semantic_program/interpreter.py`; `CACHE_VERSION` (served envelope content changes ⇒ bump, precedent 103/112).
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** next change that already bumps `CACHE_VERSION`
- **default_switch_blocker:** NO

### ISSUE-ARCH-SOURCE-LENGTH-UNLABELLED-PHRASE
- **description:** A labelled length the source reader does not recognise (*"AB dài 5 cm"*) binds no segment, so the number falls under the standalone-value rule and a program may declare a different segment (`AC = 5`) as GIVEN without any gate objecting.
- **evidence:** `docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json` row `standalone_wrong_segment` (offline, 0 model calls); inventory item NA-57.
- **impact:** A GIVEN value can be attached to the wrong segment; the figure and the answer can be wrong while every gate is green.
- **scope:** `backend/app/simulation/semantic_program/segment_relation.py`, `grounding_gate.py` (one length reader).
- **status:** RESOLVED (w14, `2f2c97b2`; `CACHE_VERSION` 105 → 106 in `733435ac`, served → rejected) — one closed connector vocabulary `segment_relation._NOI_DO_DAI` (`=`, `bằng`, `dài`, `có độ dài`) for the length reader and the GIVEN-evidence labeler (`nhan_doan_truoc`; `_NHAN_TRUOC` and `_DO_DAI_CO` deleted). The w13 probe rerun differs in exactly the two registered rows (`docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/SOURCE_GROUNDING_PHRASING_PROBE_W14.json`); `"cạnh AB có độ dài 5"` with `AC = 5` is refused (`tests/geometry/test_source_length_reader.py`). No fuzzy matching: `"AB dài hơn 5"` stays unread.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** `W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION` (Track C)
- **default_switch_blocker:** NO
- **acceptance:** `XY dài v [unit]` is read as a labelled length; the probe row is refused and every other probe row keeps its result.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/source_grounding_probe.py <new-output.json>` and compare its rows with the w13 file (the probe refuses to overwrite an existing result).

### ISSUE-OPS-TEST-EXTERNAL-EVIDENCE-PATH
- **description:** `test_raw_response_identity_reproduced` asserts that `D:/tmp/live_retry_evidence/PRISM_SCHEMA_LIVE_P01_raw_response.json` exists. The file lives outside git and the test has no marker or skip, so it runs in the default pytest and in T3.
- **evidence:** `backend/tests/geometry/test_evidence_identity_reconciliation.py:97-107`; inventory item NA-05.
- **impact:** T3 passes only on the machine that holds that directory; a clean checkout fails for a reason unrelated to the product. The raw model output cannot be committed (AGENTS.md §4).
- **scope:** Backend test environment only.
- **status:** RESOLVED (w14, `0daa6354`) — the test carries the opt-in marker `external_evidence` (deselected by default in `backend/pytest.ini`) and reads `ALGOSIM_LIVE_RETRY_EVIDENCE_DIR`, failing with `NOT_PORTABLE_EXTERNAL_EVIDENCE` when it is unset; `tests/test_test_portability.py` (AST) forbids absolute paths outside opt-in tests.
- **owner_class:** TEST HARNESS
- **suggested_wave:** backlog item 1 of the W13 preregistration
- **default_switch_blocker:** NO
- **acceptance:** the check sits behind an opt-in marker and reports `NOT_PORTABLE_EXTERNAL_EVIDENCE` when the file is absent; the default suite never reads a path outside the repository.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_evidence_identity_reconciliation.py -q` on a checkout without `D:/tmp/live_retry_evidence`.

### ISSUE-ARCH-PROMPT-OBLIQUE-SECTION-STALE
- **description:** The production geometry synthesis prompt (`program_skill_for` → `geometry_program_generator.md`) still tells the model that an oblique plane through a cylinder or cone "cannot be expressed", while the IR has `intersect_plane_curved_ellipse` (cylinder 2026-09-07, cone 2026-09-08) and the grammar card sent with the prompt lists it.
- **evidence:** `backend/app/ai/skills/geometry_program_generator.md:85-86`; `backend/app/simulation/semantic_program/ir_static_check.py` (`_CHU_KY`); inventory item NA-52.
- **impact:** Contradictory model-facing guidance. The final acceptance still served both ellipse cases, so the card wins today; the contradiction can cost repairs on other problems.
- **scope:** Model-facing surface (prompt hash ⇒ `CACHE_VERSION` decision and re-measurement).
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** a wave allowed to change the model surface (backlog item 2)
- **default_switch_blocker:** NO
- **acceptance:** the prompt states the oblique-section capability and its closure (ellipse only; parabola/hyperbola refused) consistently with the card; the surface change is measured.
- **verify:** `grep -n "xiên" backend/app/ai/skills/geometry_program_generator.md` and the prompt fingerprint in `runtime_doctor.py`.

### ISSUE-ARCH-EXACT-PLACEMENT-FEASIBILITY
- **description:** Points live in Q³ only. A figure without a rational placement (an equilateral triangle in a coordinate plane needs √3; a regular pyramid given by base and lateral edge usually needs an irrational height) cannot be built exactly, and there is no stable refusal code for it. `geometry/exact.py::hf` turns a JSON float into `Fraction(x).limit_denominator(10**9)` while its docstring says floats keep their exact binary value, so approximate decimal coordinates enter the exact kernel looking exact.
- **evidence:** `backend/app/simulation/geometry/exact.py:71-93`; inventory items NA-42, NA-54; matrix v2 groups G01–G04.
- **impact:** Regular solids and angle-defined oblique solids are not exactly constructible; whether approximate coordinates are ever served is NOT_MEASURED.
- **scope:** `backend/app/simulation/geometry/` (kernel boundary), grounding of coordinates.
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** backlog item 3 (measure first with a 0-call probe)
- **default_switch_blocker:** NO
- **acceptance:** a deterministic placement-feasibility check with a stable refusal code; the float policy is either a refusal or a stated contract; the docstring matches the code.
- **verify:** the probe named in the W13 preregistration §7.

### ISSUE-DOCS-STALE-CAPABILITY-CLAIMS
- **description:** Living docs still state retired capability absolutes: "8 expressions · 6 statements · 5 measures" and `CURVED_GEOMETRY_SUPPORT = NONE` (CURRENT_STATE §3), curved and non-convex solids as deliberate gaps (CURRENT_STATE §4), "convex polyhedra only, no curved surfaces" (README §9–10), non-convex out of scope (THESIS_ARCHITECTURE §A/§J).
- **evidence:** inventory item NA-53; sync-locked identity row of CURRENT_STATE (11 · 9 · 7); `backend/app/simulation/product_capability.py`.
- **impact:** A reader of the "current" sections learns the opposite of the code.
- **scope:** `docs/CURRENT_STATE.md`, `README.md`, `docs/research/thesis/THESIS_ARCHITECTURE.md`.
- **status:** PARTIAL — W13 added correction banners to CURRENT_STATE §3/§4; README and THESIS_ARCHITECTURE are not edited yet.
- **owner_class:** DOCS
- **suggested_wave:** documentation wave (backlog item 8)
- **default_switch_blocker:** NO
- **acceptance:** no living doc states a capability list that differs from `runtime_identity()` / `product_capability.py`; lists link to the authority instead of copying it.
- **verify:** `grep -n "CURVED_GEOMETRY_SUPPORT\|LỒI" README.md docs/CURRENT_STATE.md docs/research/thesis/THESIS_ARCHITECTURE.md`

### ISSUE-OPS-FRONTEND-TESTS-SPACE-PATH
- **description:** 11 frontend test files build repository paths from `new URL(..., import.meta.url).pathname`, which keeps `%20`; from a worktree path containing a space they fail with ENOENT (and `spawnSync git` with a bad cwd).
- **evidence:** `docs/evaluation/geometry/runs/w09-verify-cleanup/diagnostics/logs/T3_FULL_GATE_SPACED_PATH_fe3eccee.log` (vitest 23 failed / 860).
- **impact:** Authoritative runs must use a path without spaces; `full-gate.mjs` itself is space-safe (`repoRootOf`).
- **scope:** Frontend test path resolution only.
- **status:** RESOLVED (w10, `1eca93d7` + `c7fee8f8`) — 12 test files and the two scripts they import (`evidence.mjs`, `certify-sweep-w12.mjs`) use `fileURLToPath`/`URL`; a guard in `src/test-tiers.test.ts` follows test imports transitively and forbids the old pattern (red on 12 files, then on the 2 scripts, before the fixes). T3 from `D:/tmp/w10 space/algo-sim` at `40ce889f`: `FULL_PRODUCT_GATE_PASS`. Evidence: `docs/evaluation/geometry/runs/w10-pedagogical-playback/diagnostics/logs/T3_FULL_GATE_SPACED_40ce889f.log`. Residual (hand-run browser scripts): `ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH`
- **owner_class:** TEST HARNESS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** every test resolves paths with `fileURLToPath`; `npm run test:full` passes from a detached worktree whose path contains a space.
- **verify:** `git worktree add --detach "<tmp with space>" HEAD` then `cd "<tmp with space>/frontend" && npm ci --offline && npm run test:full`

### ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH
- **description:** Hand-run browser scripts in `frontend/scripts/` still build paths from `new URL(...).pathname`, which keeps `%20`. After `repo-cleanup` (Informatics scripts removed) the remaining ones are geometry tools: `accept-live-classroom`, `accept-product-scope`, `certify-product-ui-rendering`, `certify-scene3d-hidden-lines`, `certify-scene3d-visual-fidelity`, `replay-cuboid-cube-browser`, `replay-rectangular-pyramid-browser`, five `spot-check-*`.
- **evidence:** `grep -n "\.pathname" frontend/scripts/*.mjs` (w10); the test graph itself is clean (`src/test-tiers.test.ts` guard).
- **impact:** Those scripts fail when run by hand from a checkout whose path contains a space; no gate or test depends on them.
- **scope:** Hand-run browser tooling only.
- **status:** OPEN
- **owner_class:** TEST HARNESS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** every script under `frontend/scripts/` resolves paths with `fileURLToPath`; the guard is extended from the test import graph to the whole directory.
- **verify:** `grep -c "\.pathname\.replace" frontend/scripts/*.mjs` = 0

### ISSUE-EVAL-ORBIT-EVIDENCE-INTERMITTENT
- **description:** The browser orbit evidence can abort with `ORBIT_EVIDENCE_TIMEOUT` when point labels are still at their unprojected positions; the immediate rerun at the same commit passes.
- **evidence:** `docs/evaluation/geometry/runs/w09-verify-cleanup/diagnostics/logs/BROWSER_ATTEMPT1_ORBIT_TIMEOUT_defb77ed.log`, `diagnostics/MEASUREMENT_ATTEMPTS.json`.
- **impact:** An authoritative run may need a second attempt; every attempt is recorded, none is hidden.
- **scope:** Browser evidence harness (label readiness before orbit).
- **status:** RESOLVED (w10) — root causes named: fixed pixel drags could end at a view that changes no hidden edge (the gate then waited for something that never came), and clicks/drags acted blind (a click under the sticky navigation bar opened the sign-in overlay). Now the orbit is PLANNED from the product's own view metrics (`planOrbit`: keeps depth AND changes the predicted hidden set), readiness is condition-based (camera settle within tolerance → gesture → hidden set changed) with transitions and timeout reasons recorded, and `trustedClick`/`trustedOrbit` verify the target is uncovered (`5e6e1583`, `40ce889f`). Authoritative run `40ce889f`: suite orbit 12/12 with the planned gesture passing first time 12/12; learner runner 60/60 orbit laps (5 per family × viewport). Evidence: `docs/evaluation/geometry/runs/w10-pedagogical-playback/`
- **owner_class:** EVALUATION
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** root cause named; 5 consecutive authoritative runs without an orbit abort.
- **verify:** `node frontend/scripts/compiler-scene-replay.mjs --suite frontend/scripts/generic-tier-a-scenarios.json --fixture-root <inputs> --ra <out>` (x5)

### ISSUE-EVAL-CDP-SEND-NO-TIMEOUT
- **description:** `BrowserSession._send` (`frontend/scripts/browser-runner.mjs`) returns a promise with no deadline, and pending requests are never rejected when the DevTools socket closes or errors. One DevTools request whose response never arrives stalls a browser run forever instead of failing it with a reason.
- **evidence:** w12 attempt PLAYBACK-2a (`docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/diagnostics/logs/PLAYBACK_attempt1_HANG_7b039621.log`, `diagnostics/MEASUREMENT_ATTEMPTS.json`): the learner runner wrote all nine captures of cuboid/desktop, then printed nothing for about 20 minutes in an orbit lap; a separate DevTools probe of the same page answered at once (render loop running, "Bước 5/5", nothing selected). The rerun at the same commit passed 12/12 under a `timeout` watchdog.
- **impact:** A stalled run produces no verdict and has to be found and killed by hand; until then authoritative browser runs need an external watchdog.
- **scope:** Browser evidence harness (`browser-runner.mjs`, used by the suite and the playback runner).
- **status:** OPEN — found in w12; the harness was not changed in that wave (a deadline turns a hang into a failure, not into a pass).
- **owner_class:** TEST HARNESS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** every `_send` has a deadline and pending requests are rejected on socket close/error; a run fails with a named reason instead of hanging.
- **verify:** a node test that drops one DevTools response and expects a rejection within the deadline.

### ISSUE-EVAL-OCCLUSION-TERMINAL-CAMERA-IDENTITY
- **description:** Fixed-camera evidence đang băm snapshot trước khi OrbitControls damping đạt terminal state; 2 cases (`triangular_prism`, `cube`) lệch frozen identity.
- **evidence:** `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/results/VERIFICATION_SUMMARY.json` (`FROZEN_CAMERA_IDENTITY_MISMATCH`).
- **impact:** Frozen human expected sets không thể được dùng làm authority cho hai case cho tới khi terminal camera được canonicalize và đăng ký bằng commit test-only riêng.
- **scope:** Browser evidence harness / camera snapshot registration.
- **status:** RESOLVED (w09, 7b8528a9 + fe3eccee) — verified preimages of the registered hashes + projection equivalence ≤ 0.5 px; 3 EXACT, 3 CANONICAL_EQUIVALENT; registry byte-identical. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** EVALUATION / VISUALIZATION
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Camera hash lấy sau khi damping dừng (float canonicalized); 0 `FROZEN_CAMERA_IDENTITY_MISMATCH` trên sáu family trong một run mới, registry đóng băng không bị sửa bởi product/oracle.
- **verify:** `cd frontend && node scripts/compiler-scene-suite.mjs` rồi `backend/.venv/Scripts/python.exe backend/scripts/measure_scene3d_occlusion.py` (run mới theo `docs/evaluation/RUN_NAMING.md`)

### ISSUE-EVAL-OCCLUSION-IMMUTABLE-AFTER-SETTLE
- **description:** Mobile immutable-frame gate bắt đầu trước khi camera thực sự settled, nên 5 families ghi nhận recomputation trong 120 frame được coi là immutable.
- **evidence:** Cùng `VERIFICATION_SUMMARY.json`, mobile `immutable_120_frames` failures.
- **impact:** Performance evidence chưa sạch dù product classifier correctness đã khớp oracle.
- **scope:** Browser/performance gate scheduling.
- **status:** RESOLVED (w09, 7b8528a9 + 91d3e9c3) — root cause was also in the product: the classifier keyed on raw floats while idle damping rewrote the pose every mobile frame; canonical camera key, settle gate, and zeroed window counters. 12/12 windows, 0 recomputes. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** EVALUATION / PERFORMANCE
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Cửa sổ 120 frame chỉ bắt đầu sau khi camera settled; mobile `immutable_120_frames` PASS 6/6 family, fault gate vẫn đỏ khi tiêm recomputation.
- **verify:** `cd frontend && npx vitest run src/simulations/domains/geometry/scene3d-occlusion-gates.test.ts && node scripts/compiler-scene-suite.mjs`

### ISSUE-EVAL-FRONTEND-BOUNDARY-GUARD-FALSE-POSITIVE
- **description:** Legacy frontend whole-source regex cấm chuỗi `boundary` quá rộng và bắt nhầm field hợp lệ `boundary_edge_ids`.
- **evidence:** Frontend full result 904 pass, 1 fail trong correction report 2026-09-28.
- **impact:** Full frontend gate đỏ dù failure hiện được chẩn đoán là guard defect; phải thay bằng assertion đúng ranh giới trước khi gọi sạch.
- **scope:** Frontend architecture/source guard test only.
- **status:** RESOLVED (w09, 1f151f8d) — assertion on declared field names; frontend full 906/0. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** TEST HARNESS
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Regex `/boundary|corners|extent/` tại `frontend/src/simulations/domains/geometry/scene3d.test.tsx` thay bằng assertion cấm đúng field cũ nhưng cho `boundary_edge_ids`; guard vẫn đỏ khi tiêm field bị cấm; frontend full 0 fail.
- **verify:** `cd frontend && npx vitest run src/simulations/domains/geometry/scene3d.test.tsx && npm test`

### ISSUE-EVAL-BACKEND-35-FAILURES-UNCLASSIFIED
- **description:** 35 backend full-suite failures chưa được phân loại riêng thành intended golden update, stale candidate/report guard, harness/environment defect hoặc real product regression.
- **evidence:** Backend full result 6268 pass, 35 fail, 1 skip, 1 deselect trong correction report 2026-09-28.
- **impact:** Không được suy tất cả là stale test hoặc tất cả là product regression; verification vẫn đỏ cho tới khi từng failure có classification và rerun evidence.
- **scope:** Backend full regression triage.
- **status:** RESOLVED (w09) — fresh reproduction 31 (main) + 3 (detached-only) = 34, each reconciled; 28 were a REAL_PRODUCT_REGRESSION (raw kernel objects in scene3d.events, HTTP 500 at the cache write), fixed in f337323f. The 35th of the prior count was never itemized: NOT_RECOVERABLE. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`results/BACKEND_FAILURE_RECONCILIATION.json
- **owner_class:** EVALUATION / TEST HARNESS / PRODUCT
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Mỗi failure có một nhãn (golden update có chủ đích · stale guard · harness/env · product regression) kèm rerun; không đổi golden/hash khi chưa có classification.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q -rf`

### ISSUE-OPS-FULL-GATE-PYTHON-ENV-RESOLUTION
- **description:** Full-gate runner chưa resolve Python interpreter/environment một cách độc lập khi chạy trong detached worktree.
- **evidence:** Handoff và verification summary của run occlusion 2026-09-28.
- **impact:** Authoritative clean-worktree verification có thể thất bại do environment path thay vì product state.
- **scope:** Full-gate runner / detached-worktree environment discovery.
- **status:** RESOLVED (w09, 1d1397fa + defb77ed) — resolvePython with structured failure; detached T3 FULL_PRODUCT_GATE_PASS with main_worktree_venv. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** OPERATIONS / TEST HARNESS
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** `full-gate.mjs` chạy trong detached worktree sạch mà tìm được interpreter backend có khai báo (không ngầm dựa vào `.venv` của cây chính), ghi đường dẫn interpreter vào artifact.
- **verify:** `git worktree add --detach <tmp> HEAD` rồi `cd <tmp>/frontend && npm run test:full`

### ISSUE-ARCH-COMPILER-COVERAGE-NARROW
- **description:** Primitive compiler hiện tại chỉ hỗ trợ một họ bài toán đơn lẻ là tính thể tích khối chóp có đáy tam giác vuông (`right_triangle_base_pyramid_volume`).
- **evidence:** `backend/app/simulation/compiler/primitive_compiler.py`, báo cáo `docs/evaluation/reports/GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE.md`.
- **impact:** Hệ thống chưa thể biên dịch tất định các họ hình học không gian phổ biến khác trong chương trình THPT.
- **scope:** `backend/app/simulation/compiler/`
- **status:** OPEN
- **w13_audit:** the description and paths are stale at `bf5a7907` — the package is `backend/app/simulation/geometry_compiler/` and `compiler.py:41-53` supports six families (right-triangle pyramid and prism, rectangular pyramid, cuboid, cube, right square prism). What remains narrow is listed by layer in `docs/architecture/geometry_capability_matrix_v2.json` (`L08 compiler_rule`) and in `ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE`.
- **oblique-prism (2026-10-09):** seventh family `oblique_prism_volume` (G04: right-triangle/rectangle/square base, foot of a lateral height at a named base vertex, rational height) — `docs/evaluation/geometry/runs/oblique-prism/`. Still narrow: foot at a midpoint/centroid and angle-defined obliquity are refused (`ISSUE-ARCH-OBLIQUE-PRISM-FOOT-VOCABULARY`).
- **general-polygon-base (2026-10-09):** families `polygon_base_pyramid_volume` / `polygon_base_right_prism_volume` (G05: convex base fixed by k − 2 consecutive right angles — right trapezoid, right triangle with the apex edge at any vertex, n-gons). Still narrow: `ISSUE-ARCH-G05-REMAINING-BASES`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-COMPILER-FIRST-ROUTING
- **description:** Cổng định tuyến compiler-first trong pipeline chính chưa được xây dựng; hệ thống hiện tại vẫn đi qua LLM synthesis mặc định.
- **evidence:** `backend/app/ai/pipeline.py`, cờ `DEFAULT_MODE = LLM_ONLY`.
- **impact:** Người dùng chưa được hưởng lợi từ tốc độ và tính tất định của compiler trong luồng chạy thực tế.
- **scope:** `backend/app/ai/pipeline.py`
- **status:** OPEN
- **cfr_audit:** (2026-10-05, `cuboid-final-review`) the description is stale: the routing gate exists and is wired opt-in — `backend/app/simulation/geometry_compiler/routing.py::quyet_dinh_dinh_tuyen`, called from `backend/app/ai/pipeline.py` after analyze; the compiler runs only with `GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST`, the default `LLM_ONLY` returns `DISABLED`. What stays open is the default switch itself (`MIGRATION_CHECKLIST.md` GATE-11 audit line); the status is left to the migration wave.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-FALLBACK-MECHANISM
- **description:** Chưa có cơ chế chuyển giao tự động và an toàn từ compiler sang LLM synthesis khi bài toán nằm ngoài tập primitive được hỗ trợ.
- **evidence:** `backend/app/simulation/compiler/` chưa có module router/fallback adapter.
- **impact:** Nếu bật compiler-first mà gặp bài toán không thuộc diện hỗ trợ thì hệ thống sẽ dừng thay vì fallback.
- **scope:** `backend/app/ai/pipeline.py`
- **status:** OPEN
- **cfr_audit:** (2026-10-05, `cuboid-final-review`) the evidence path is stale (the package is `backend/app/simulation/geometry_compiler/`) and so is the description: `routing.py` returns `FALLBACK_TO_LLM` for `UNSUPPORTED` (unit test `backend/tests/geometry/test_geometry_primitive_compiler.py::test_AD_unsupported_tra_fallback_cho_caller_chu_khong_tu_gui`) and `pipeline.py` sends every decision other than `USE_COMPILER`/`REFUSE` on to `stage_semantic_program`. No test drives that fallback branch through `run_pipeline` yet (`MIGRATION_CHECKLIST.md` GATE-12 audit line); the status is left to the migration wave.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-CANARY-OR-ROLLBACK
- **description:** Chưa có cơ chế phân luồng canary để thử nghiệm tỉ lệ nhỏ trên production và chưa có kịch bản rollback tức thì khi gặp lỗi biên dịch.
- **evidence:** Chưa có middleware/routing layer hỗ trợ canary splitting trong `backend/app/main.py`.
- **impact:** Rủi ro gián đoạn dịch vụ khi kích hoạt tính năng mới trên toàn hệ thống.
- **scope:** `backend/app/`
- **status:** OPEN
- **owner_class:** OPERATIONS / ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-SPATIAL-LAYOUT-SOLVER
- **description:** Chưa có bộ giải bố cục không gian 3D tự động; tọa độ các điểm hiện do các bước dựng hình cơ sở xác định cục bộ, có thể gây mất cân đối thị giác ở các góc phức tạp.
- **evidence:** `backend/app/simulation/` thiếu solver tối ưu hóa ràng buộc tọa độ toàn cục.
- **impact:** Một số hình vẽ phức tạp có thể bị dồn góc hoặc khó nhìn trong không gian 3D.
- **scope:** `backend/app/simulation/` & `frontend/src/`
- **status:** OPEN
- **owner_class:** VISUALIZATION
- **suggested_wave:** P3 (Visualization)
- **default_switch_blocker:** NO

### ISSUE-ARCH-NO-HIDDEN-LINES
- **description:** Product repair đã triển khai dynamic hidden-line spans và oracle độc lập, nhưng verification browser/camera/performance tổng vẫn chưa sạch.
- **evidence:** `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md`; architecture amendment `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`.
- **impact:** Không còn là missing implementation; vẫn chưa được nâng thành human-accepted hoặc merge-ready cho tới khi năm issue verification ở đầu file được khép bằng evidence mới.
- **scope:** `frontend/src/simulations/domains/geometry/`
- **status:** REPAIR_VERIFIED_PENDING_HUMAN_VISUAL_REVIEW (w09: all automated gates PASS)
- **owner_class:** VISUALIZATION
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO

### ISSUE-ARCH-NO-OCR-IMAGE-PIPELINE
- **description:** Chưa triển khai đường ống bóc tách vùng đề bài và OCR nhận diện văn bản toán học từ ảnh chụp camera điện thoại.
- **evidence:** `backend/app/ingestion/input.py` chỉ tiếp nhận text đầu vào.
- **impact:** Người dùng phải gõ lại đề bài bằng văn bản thay vì chụp ảnh trực tiếp từ sách giáo khoa.
- **scope:** `backend/app/ingestion/`
- **status:** OPEN
- **w13_audit:** the evidence line is stale — a photo route exists (`POST /api/image/extract`, `backend/app/ingestion/image_extraction.py`: multimodal transcription, deterministic assessment, learner review before analyze). A dedicated OCR pipeline is still absent; whether this issue is still wanted is a scope decision.
- **owner_class:** INGESTION
- **suggested_wave:** P4 (Image Acquisition)
- **default_switch_blocker:** NO

### ISSUE-EVAL-TOKEN-OPTIMIZATION-NOT-ESTABLISHED
- **description:** Việc giảm token tiêu thụ của compiler so với LLM synthesis mới chỉ là quan sát thực nghiệm trên một lát cắt nhỏ, chưa được xác lập như một đặc tính đo lường tin cậy ở quy mô production.
- **evidence:** `docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/report.md`, `FINAL_DECISION.json`.
- **impact:** Không được tuyên bố trong luận văn rằng compiler đã tối ưu hóa token ở mức độ hệ thống hoàn chỉnh.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P6 (Thesis Evaluation)
- **default_switch_blocker:** NO

### ISSUE-EVAL-STATISTICAL-SIGNIFICANCE-UNESTABLISHED
- **description:** Số lượng mẫu kiểm thử (n-count) của các phép đo live hiện tại còn nhỏ, chưa đủ để đưa ra các kết luận có ý nghĩa thống kê.
- **evidence:** `docs/legacy/research/THESIS_READINESS.md §7`, `docs/EVIDENCE_INDEX.md`.
- **impact:** Các công bố định lượng cần được giới hạn trong phạm vi thực nghiệm định tính hoặc nghiên cứu tình huống (case study).
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P6 (Thesis Evaluation)
- **default_switch_blocker:** NO

### ISSUE-EVAL-P03-P05-HISTORICAL-CAUSE-NOT-ESTABLISHED
- **description:** Nguyên nhân gốc rễ của cụm lỗi lịch sử Analyze P03/P05 (`MODEL_MALFORMED_RELATION`) chưa được xác lập chắc chắn vì hai ca live retry đều trả về kết quả hợp lệ mà không tái hiện lỗi.
- **evidence:** `docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/report.md`, `FINAL_DECISION.json` (`HISTORICAL_ROOT_CAUSE = NOT_ESTABLISHED`).
- **impact:** Cần duy trì giả thuyết về tính biến thiên tự nhiên của mô hình (model variance) và tiếp tục theo dõi qua các lần đo sau.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** NO

### ISSUE-EVAL-P03-P05-TOKEN-UNKNOWN
- **description:** Lượng token sử dụng của hai request P03 và P05 trong đợt live retry trước đây được ghi nhận là 0 do giới hạn của client HTTP, sau đó được đính chính thành UNKNOWN.
- **evidence:** `MACHINE_RAW_OUTPUT.json` of `docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/` — the file was never committed (raw model output stays out of git), so the pointer is `NOT_RECOVERABLE` in the repository; the committed run keeps only `*_REDACTED.json` files (W19 link check).
- **impact:** Số liệu token của wave đó không được đưa vào bảng phân tích so sánh định lượng của luận văn.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** NO

### ISSUE-DOCS-CRLF-GITATTRIBUTES-RISK
- **description:** Rủi ro chuyển đổi ký tự kết thúc dòng (CRLF / LF) giữa môi trường phát triển Windows và máy chủ Linux có thể ảnh hưởng đến hash SHA-256 của các artifact văn bản.
- **evidence:** `.gitattributes` hiện quản lý chuẩn hóa LF cho các file text và JSON.
- **impact:** Cần đảm bảo mọi công cụ đo lường và kiểm chứng đều áp dụng chuẩn hóa LF trước khi băm nội dung.
- **scope:** Repository configuration
- **status:** OPEN
- **owner_class:** DOCUMENTATION / OPS
- **suggested_wave:** P0 (Documentation Hardening)
- **default_switch_blocker:** NO

### ISSUE-OPS-ORPHANED-TEMP-DIRECTORIES
- **description:** Các thư mục tạm được tạo trong quá trình chạy test worktree (ví dụ `D:/tmp/mvep-*`, `D:/tmp/algo-sim-*`) có thể tồn đọng nếu quy trình dọn dẹp gặp sự cố ngoài ý muốn.
- **evidence:** Thư mục `D:/tmp/` chứa các artifacts bằng chứng máy từ các wave trước. w10 để lại, NGOÀI git: `D:/tmp/w10-out` và `D:/tmp/w10-build.log` (bản dựng/thử nghiệm dev), `D:/tmp/w10-freeze4` (worktree đóng băng đã gỡ khỏi git; xoá thư mục bị từ chối vì một tiến trình đang giữ — chỉ còn bản sao file đã commit), `D:/Documents/projects/tmp-dist-exp` (bản dựng thử nghiệm depth test). Không chứa gì cần giữ; mọi bằng chứng đã nằm trong run w10. w11 để lại: hai worktree detached CÒN ĐĂNG KÝ — `D:/tmp/w11-d1` (đo) và `D:/tmp/w11 space/algo-sim` (T3) — gỡ bằng `git worktree remove <path>`; `D:/tmp/w11-before` (đã gỡ đăng ký, xoá bị từ chối quyền); `D:/tmp/w11-gen`, `D:/tmp/w11-attempt1`, `D:/tmp/w11-*.log`, `D:/tmp/w11-schema-*.txt`. Mọi thứ cần giữ đã nằm trong run w11. **w12 (2026-10-01) dọn:** cả tám worktree tạm đã đăng ký (hai của w11, sáu của w12) đã gỡ bằng `git worktree remove <đường dẫn>`, không ép, sau khi so từng file chưa commit với blob đã commit (0 artifact duy nhất có rủi ro) — chi tiết `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/diagnostics/WORKTREE_CLEANUP.json`. Còn lại, KHÔNG đăng ký, đánh dấu `SAFE_TO_DELETE` (không tự xoá): thư mục rỗng `D:/tmp/w11-d1`, `D:/tmp/w11 space`, `D:/tmp/w12 space`; `D:/tmp/w11-before` (383 MB), `D:/tmp/w10-freeze4` (324 MB), `D:/tmp/w11-attempt1`, `D:/tmp/w11-gen`, `D:/tmp/w10-out` và các log `D:/tmp/w10-*.log`, `D:/tmp/w11-*`, `D:/tmp/w12-backend-*.log`.
- **impact:** Chiếm dụng dung lượng đĩa và có nguy cơ gây nhầm lẫn nếu không được quản lý vòng đời rõ ràng.
- **scope:** Scripts & Test harnesses
- **status:** OPEN
- **owner_class:** OPERATIONS
- **suggested_wave:** P0 (Documentation Hardening)
- **default_switch_blocker:** NO

### ISSUE-ARCH-PRISM-COMPILER-GAP
- **description:** Primitive compiler thiếu primitive construct_prism(name, base_cycle, top_cycle, correspondence), FactGraph thiếu loại nút prism, và 10 tầng phối hợp khác (RequestContract, relations, adapter, eligibility, IR, gates, topology, measurement, routing, frontend renderer) chưa hỗ trợ họ lăng trụ đứng đáy tam giác vuông đã tiền đăng ký (right_triangle_base_right_prism_volume).
- **evidence:** `docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/report.md`, `docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/VERTICAL_SLICE_SCOPE_MAP.json`.
- **impact:** Họ bài `right_triangle_base_right_prism_volume` chưa thể biên dịch tất định cho đến khi hoàn thành vertical slice qua đủ 12 tầng kỹ thuật.
- **scope:** `backend/app/simulation/geometry_compiler/`
- **status:** RESOLVED — verified by the W13 audit at `bf5a7907`: `geometry_compiler/primitives.py` has `construct_prism`, `fact_graph.py::LOAI_NUT` has `prism`, `compiler.py` supports `right_triangle_base_right_prism_volume` (vertical slice `5a5534fe`, 2026-09-22, `docs/EVIDENCE_INDEX.md`).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-REQUEST-CONTRACT-PRISM-GAP
- **description:** `RequestContract` tại baseline thiếu trường chở `prism identity`, `base_cycle`, `top_cycle`, hay `correspondence` (`REQUEST_CONTRACT = CHANGE_REQUIRED`). Bế tắc kiến trúc giữa Direction A và Direction B đã được giải quyết về mặt thiết kế tại `docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md` thông qua kiến trúc 2 lớp (Internal Discriminated Union vs Model Transport Flattened Schema). Vấn đề hiện tại là triển khai mã nguồn sản phẩm trong vertical slice.
- **evidence:** `docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/report.md`, `docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md`.
- **impact:** Cần áp dụng hợp đồng đã thiết kế vào `request_contract.py` và `contract_adapter.py` trong vertical slice tiếp theo.
- **scope:** `backend/app/simulation/semantic_program/request_contract.py`, `backend/app/simulation/geometry_compiler/contract_adapter.py`
- **status:** RESOLVED — verified by the W13 audit at `bf5a7907`: `request_contract.py` carries `solid_topology: PrismTopologySpec | PyramidTopologySpec | None` (base cycle, top cycle, correspondence). The remaining contract gaps (one solid only, no regularity, no curved topology) are tracked by layer in `docs/architecture/geometry_capability_matrix_v2.json`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED
- **description:** On the default `LLM_ONLY` route a length that exists only in an analyze-authored `input_fact` — not in the problem text, so absent from the server-extracted length invariants — can ground a GIVEN quantity: the grounding gate checks program ↔ contract, not contract ↔ text. A volume problem whose height is not stated can then be served with an invented height.
- **evidence:** `docs/evaluation/geometry/runs/w11-pedagogical-polish/diagnostics/logs/INVENTED_HEIGHT_PROBE_48c676d5.log` (offline, 0 model calls): prism contract with the `AD` invariant removed and `AD = 5` removed from the text — compiler route `FALLBACK_TO_LLM` (`REQUIRED_LENGTH_MISSING AD`), the program is served `ok` because the analyze fact still carries `5`; the pyramid analogue is refused (`input_not_grounded`) because its SA fact carries no value. The fact-value channel dates from `2bdd2f73` (before w11); the w11 channel `_do_dai_bat_bien` requires a server-extracted invariant and does not widen this.
- **impact:** A hallucinated length in the analyze output is not caught deterministically on the LLM route; the opt-in compiler route fails closed.
- **scope:** `backend/app/simulation/semantic_program/grounding_gate.py` (fact-value channel) and analyze-contract provenance.
- **status:** RESOLVED (w12, `79eb1e59` + `8aaeae80`; `CACHE_VERSION` 104 → 105 in `d17550c3`, served → rejected) — a GIVEN length (integer, decimal with `.` or `,`, fraction, radical) and every P1-only atom must be backed by the problem text itself (`gia_tri_khong_chung_minh_duoc`, recomputed from the text, shared by the frozen boundary, the gate and the invariant builders); a point pinned to a coordinate claim whose digits the text does not state is refused. Stable codes `GIVEN_VALUE_NOT_IN_SOURCE` / `SOURCE_SPAN_MISMATCH` / `SOURCE_EVIDENCE_CONFLICT`, never sent to repair; the envelope carries `reason_code` + `reason_subjects` and a point- or segment-aware Vietnamese message. The probe's prism case now returns `unsupported` (`input_not_grounded`, `GIVEN_VALUE_NOT_IN_SOURCE`, subject `AD`). Evidence: `backend/tests/geometry/test_source_grounding_closure.py`; red logs and the browser negatives (one ungrounded fixture per family, refused with no canvas and no answer) in `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/`. Residual: `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO (an argument for compiler-first)
- **acceptance:** a GIVEN `XY_length` whose literal has no server-extracted length invariant is refused or labelled; the probe returns `unsupported` for the prism case.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_source_grounding_closure.py -q`

### ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION
- **description:** After w12 a length the problem does not state can no longer reach the answer as a GIVEN, but it can still fix a dimension through coordinates: a program that places a vertex with `LAYOUT_DERIVED` provenance or a `model_assumption` (the LLM's documented channel for free choices of axes) can encode an unstated height, and the volume follows from those coordinates. Neither channel claims GIVEN, so the grounding gate has nothing to check.
- **evidence:** `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/diagnostics/logs/ASSUMPTION_CHANNEL_PROBE_79eb1e59.log` (offline, 0 model calls): prism text without "AD = 5" — the program with the `AD_length` GIVEN is refused (`GIVEN_VALUE_NOT_IN_SOURCE`); the same placement through `LAYOUT_DERIVED` vertices or through `model_assumption` is served with `V = 30`.
- **impact:** A hallucinated dimension can still surface as a coordinate choice on the LLM route. It is never labelled as given by the problem, and the compiler route does not use this channel.
- **scope:** `backend/app/simulation/semantic_program/` (which free coordinate choices may carry a metric the text does not state).
- **status:** PARTIAL (w15) — CLOSED inside the polyhedral scope, RECORDED but not refused outside it. A server-owned constraint reader (`semantic_program/shape_constraint.py`, closed vocabulary) and the assumption certificate (`semantic_program/assumption_gate.py`: C0 · C1 templates T1–T6 · counterexample from a fully read text) are wired into the route as stage `assumption`. In scope (U3: the text names a polyhedral solid in the vocabulary), only `PROVEN_SAFE` is served. `DEPENDENT` is refused `ASSUMPTION_DETERMINES_ANSWER` and names the missing quantity; `UNDETERMINED` is refused `ASSUMPTION_INVARIANCE_UNPROVEN`. Neither is sent to repair. Multiple reaching definitions are refused in every scope (U5). Remainder: on texts outside that scope (segments, planar figures, curved solids without the vocabulary) the gate records `assumption_enforced = false` and the pre-W15 behaviour stays (user decision U3, `docs/evaluation/geometry/runs/w15-assumption-closure/inputs/W15_SCOPE_DECISIONS.json`; enforcing there today refuses about 170 served, text-determined cases outside C0/C1).
- **w15:** measured at `41a26f11`/`c57ebd1b`: AC2 **18/18** `PROVEN_SAFE` (8 C0, 10 C1) and served; the probe's `LAYOUT_DERIVED` and `model_assumption` variants refused at `assumption` (`ASSUMPTION_DETERMINES_ANSWER`, AD); AC1 3/3 and adversarial 7/7 refused; W14's 11 false counterexamples → 0; census round 3 SHIP (`diagnostics/ASSUMPTION_MECHANISM_DECISION_W15_R3.json`); `CACHE_VERSION` 106 → 107 (`0579d559`, real rows). Corpus result inside the registered scope (`docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`), not a general proof — the final self-review still found one hole (fixed in `41a26f11`).
- **w13:** policy and acceptance criteria preregistered (`docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md` §3: GIVEN_VALUE / DERIVED_VALUE / MODEL_ASSUMPTION / VISUAL_DEFAULT, rules P1–P6, AC1–AC7); w12 human review lists this issue as W12-H4.
- **w14:** STILL OPEN — Track B stopped (`ASSUMPTION_POLICY_INCOMPLETE`). A three-valued gate (certificates C0/C1 ⇒ `PROVEN_SAFE`, validated counterexample ⇒ `UNSAFE`, else `UNDETERMINED`, both refused) was measured on a corpus hand-labelled before any mechanism ran: 0 `PROVEN_SAFE` on DEPENDS rows and every AC1/adversarial row refused, but **0/18** contract-bearing gold rows certified (C1 blocked: the compiler families' relations cite facts not confirmed as InputFacts; LLM gold/demo programs are not compiler-recognized), and the counterexample search raised 11 false counterexamples on invariant rows. No gate shipped; the probe's two variants are still served; 16 gate tests are strict xfail. Corpus result inside the certificate scope only, not a soundness proof. Evidence: `docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/ASSUMPTION_CENSUS.json`, `ASSUMPTION_MECHANISM_DECISION.json`, `ASSUMPTION_COUNTEREXAMPLES.md`. Next: user decision W14-D2 (certificate scope).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** after human review of w15 — user decision W15-H2 (enforcement outside the polyhedral vocabulary needs more certificate coverage first, `ISSUE-ARCH-SHAPE-CONSTRAINT-VOCABULARY-COVERAGE`)
- **default_switch_blocker:** NO (an argument for compiler-first)
- **acceptance:** a dimension that the answer depends on is either stated in the text, derived from stated facts, or shown to the learner as an assumption; the probe's layout and assumption variants are refused or labelled.
- **verify:** rerun the script embedded in the probe log; `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_assumption_gate.py tests/geometry/test_assumption_certificate.py tests/geometry/test_shape_constraint.py -q`; census: `backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/assumption_census_w15_r2.py <next round>`.

### ISSUE-OPS-OFFLINE-SAMPLES-STALE
- **description:** `frontend/src/data/geometry-samples.json` (offline demo problems) is no longer what `backend/scripts/build_geometry_samples.py` produces from the current product, and the drift test its header names (`frontend/src/data/geometry-samples.test.ts`) does not exist.
- **evidence:** measured in the w11 worktree at `ac19e03d` (restored afterwards): regenerating changes the file by +4343/−274 lines; the committed samples date from `47c255d9` (2026-09-03), 66 `backend/app` commits ago, and lack `dependency_edges`, `edge_ownership`, `surfaces`, `occludes_edges`, `display_label` — so offline scenes have no typed provenance (causal tiers) and no canonical edge ownership.
- **impact:** Opening the app without an API key shows scenes built by an older engine; no gate reads these samples.
- **scope:** Offline demo data (`frontend/src/data/`).
- **status:** OPEN — not regenerated in w11 (a product-file change outside the reviewed families).
- **owner_class:** OPERATIONS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** samples regenerated in a product commit; a test fails when the committed JSON differs from the generator's output.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/build_geometry_samples.py` then `git diff --stat frontend/src/data/geometry-samples.json` (empty).

### ISSUE-OPS-DIST-ACL-OWNERSHIP
- **description:** In the main working tree `frontend/dist/assets` is owned by another Windows account (`CodexSandboxOffline`); `npm run build` cannot replace it and fails with `EPERM`.
- **evidence:** `docs/evaluation/geometry/runs/w11-pedagogical-polish/diagnostics/logs/DIAG1_SUITE_BUILD_EPERM_main-tree.log`.
- **impact:** Builds, browser measurements and T3 must run in a worktree; running them in the main tree fails at the build step.
- **scope:** Local environment (ACL outside git).
- **status:** OPEN — ownership not changed by the agent (needs the user).
- **owner_class:** OPERATIONS
- **suggested_wave:** any
- **default_switch_blocker:** NO
- **acceptance:** `cd frontend && npm run build` succeeds in the main tree.
- **verify:** `icacls frontend\dist\assets`

### ISSUE-ARCH-TEXTLESS-CONTRACT-UNCHECKED
- **description:** Before w14, a `RequestContract` with an empty `problem_text` made `check_grounding` skip every source check, so a contract without its text was treated as trusted by default.
- **evidence:** `docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/TRUST_POLICY_CALLERS.json` (20 test callers and 44 scripts classified one by one) and `diagnostics/logs/TRUST_POLICY_TRACE.json`.
- **impact:** A production path that lost the text would have served answers no gate had checked against the problem.
- **scope:** `backend/app/simulation/semantic_program/grounding_gate.py`, `route.py`, `backend/app/ai/pipeline.py` (`KHONG_SUA_NGUON`).
- **status:** RESOLVED (w14, `d537cf74`) — `NguonDe.CAN_DE` is the default; an empty text is refused `SOURCE_TEXT_MISSING` at stage `grounding` and never sent to repair; only an explicit `NguonDe.FIXTURE_TIN_CAY` argument takes the unchecked path and records `source_check = UNCHECKED_TRUSTED_FIXTURE`. The policy is a Python argument only: not parsed from HTTP payloads, headers or model output; no reference from `app/ai`, `app/main.py` or `app/api` (AST test).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** —
- **default_switch_blocker:** NO
- **acceptance:** a textless production contract is refused; isolated unit fixtures declare the policy explicitly.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_assumption_gate.py -q -k "fixture_tin_cay or thieu_de or bypass or NguonDe"`

### ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4
- **description:** The frozen human hidden-line expectations (`docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json`) were reviewed on scenes that w14's formation pass changed: the triangular pyramid, triangular prism and cross-section gain drawn segments/faces, and the rectangular pyramid's lateral IDs are renamed (declared Q1 delta). `transfer_expectation` refuses, by design, to carry a reviewed expectation onto changed geometry.
- **evidence:** `docs/evaluation/geometry/runs/w14-generic-formation-assumption/results/OCCLUSION_MEASUREMENT.json` (product = oracle 24/24; 4 × `SCENE_GEOMETRY_CHANGED`, cuboid and cube transfer) and `diagnostics/OCCLUSION_TRANSFER_DIAGNOSTIC.json` (the oracle reproduces the reviewed sets 4/4 at the registered and the new camera; known-answer fault caught).
- **impact:** For those four scenes the hidden-line gate cannot be green without a person; no visibility regression is measured.
- **scope:** Evaluation evidence (human registry); no product code.
- **status:** OPEN — needs human re-review of the four scenes and a new registry layer (the reviewed registry stays byte-identical).
- **cmerge:** (2026-10-05, `cuboid-merge`) the four scenes are group C of `docs/evaluation/geometry/runs/cuboid-merge/REVIEW.md`; their w18 images transfer to candidate `b2d4187a` (regenerated fixtures equal except the two identity fields). The user ACCEPTED group C on 2026-10-05 (`cuboid-merge/APPROVAL.md`); the issue stays OPEN until a reviewed registry layer of expected visibility sets exists, which that visual approval does not create.
- **w15:** with the opt-in flag `--pending-human-review` (user decision U2), the four scenes count as `HUMAN_REVIEW_PENDING`, not as failures. That holds only while the independent oracle reproduces the reviewed sets at the registered and at the new camera and the product equals the oracle on every state; anything else is still a failure. Measured at `c57ebd1b`: verdict `HUMAN_REVIEW_PENDING`, product = oracle 24/24, cuboid and cube `DECLARED_CAMERA_CHANGE` (`docs/evaluation/geometry/runs/w15-assumption-closure/results/OCCLUSION_MEASUREMENT.json`). The cross-section's closed fill is now visible, so the reviewer also sees that change. Automation writes no `APPROVED_BY_USER`.
- **owner_class:** EVALUATION
- **suggested_wave:** `HUMAN_VISUAL_REVIEW_OF_ASSUMPTION_CLOSURE_EVIDENCE` (W15-H1)
- **default_switch_blocker:** NO
- **acceptance:** a reviewed registry layer for the current scenes; the occlusion measurement passes against it.
- **verify:** `measure_scene3d_occlusion.py` with the new registry (command at the top of `diagnostics/logs/OCCLUSION_c57ebd1b.log` in the w15 run).

### ISSUE-ARCH-SHAPE-CONSTRAINT-VOCABULARY-COVERAGE
- **description:** The assumption certificate's premises come only from what `shape_constraint.doc_rang_buoc` and the existing text-invariant builders read, in a closed vocabulary. A polyhedral problem whose text determines the answer in another phrasing gets no certificate and is refused `ASSUMPTION_INVARIANCE_UNPROVEN` (fail-closed). Examples: an angle (`góc giữa SC và đáy bằng 45°`), an equality of segments (`SA = AB`), `vuông cân`, a length with a radical (`SB = 3√2`), a division ratio written `M thuộc cạnh AB …`, or a regular solid without coordinates. The reader also reads perpendicularity phrases anywhere in the text, so a `Chứng minh …` claim acts as a premise, which is a true consequence in a consistent problem.
- **evidence:** `docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/assumption_corpus_w15/LABELS.json` and the `W15_OUT_OF_VOCAB` / `W15B_UNREAD_TEXT` groups of `ASSUMPTION_CENSUS_W15_R3.json` (all `UNDETERMINED`, refused); `tests/geometry/test_assumption_certificate.py` (unread-text and ratio-phrasing tests).
- **impact:** Determined problems in those phrasings are refused inside the polyhedral scope instead of served; a learner must rephrase.
- **scope:** `backend/app/simulation/semantic_program/shape_constraint.py`, `segment_relation.py` (division reader), `assumption_gate.py` (template table).
- **status:** OPEN (w15) — coverage limit of the registered scope, not a soundness defect.
- **w16:** the last sentence of the description no longer holds for the certificate. Since `93d4ec69`, `shape_constraint.khoang_muc_tieu` marks goal clauses: `chứng minh`, `chứng tỏ`, `CMR`, `kiểm tra`, `hỏi`, and any clause ending in `?`. Every certificate premise is read from the text with those clauses masked, so a `Chứng minh …` relation is never a premise; it still blocks the counterexample (ASSUMPTION_CERTIFICATE_AMENDMENT §14.2). This is measured on the seven W16 goal rows, all refused. The W16 probe also surfaced one more gap of this issue, one that existed before W16: in `Tính …, biết chiều cao bằng …`, the height comes after `Tính`, and the height reader only reads the data part. The request is refused as `UNDETERMINED` before and after W16 (over-refusal, fail-closed), never as `DEPENDENT` (row `B6b_tinh_biet_chieu_cao`).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** user decision W15-H3, then one reader rule + one registered certificate rule per phrase
- **default_switch_blocker:** NO
- **acceptance:** each added phrase has a reader test (right entity, wrong entity, paraphrase), a certificate rule registered before code, and census rows labelled before the run.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_shape_constraint.py tests/geometry/test_assumption_certificate.py -q`

### ISSUE-ARCH-ASSUMPTION-C0-PLANE-EQUATION-ENTITY
- **description:** C0 accepts a plane-equation literal as `SOURCE_DATUM` when it is proportional to *some* plane equation of the text. The `plane_equation` invariant family carries no entity (`points=()`), so in a text with two planes a program could assign one plane's equation to the other plane and still pass C0.
- **evidence:** `backend/app/simulation/semantic_program/assumption_gate.py::_vai_tro` (branch `mat_phang`), `plane_equation.bat_bien_mat_phang`; final self-review of w15 (`docs/evaluation/geometry/runs/w15-assumption-closure/REPORT.md`, limitations).
- **impact:** A misassigned but stated plane equation is not caught by the certificate; other gates may or may not catch it. The amendment says "same entity", which holds for points, lengths and ratios.
- **scope:** `plane_equation.py` (entity binding of the invariant), `assumption_gate.py`.
- **status:** RESOLVED (w16, `24161657` + `6b120036`; `CACHE_VERSION` 107 → 108 in `2ec02b3a`, served → rejected).
  - **How it is fixed.** `plane_equation.doc_mat_phang_de` reads each text equation together with the name written in its clause and its span. `assumption_gate.gan_mat_phang` binds a program plane to its text plane in one of two ways: by name (`ten_mat_phang_cua_bien`, closed Greek table; a written prime or a following `_prime`/`_phay` token is part of the name), or as unique by counting (the text mentions planes once and the program builds one equation plane). The coefficients must then be proportional. Equal numbers never bind.
  - **Measured.** Seven wrong-entity programs are refused: β given α's equation, α/β swapped (it showed 9 where the text gives 16), four unnamed planes without a unique basis, and (P′) given (P)'s equation through the variable `mp_P_prime` (found by the pre-evidence self-review, red in `2dc55f1b`, fixed in `6b120036`). Nine valid bindings, including (P′) with its own equation, and the gold rows p1, p6 and p7 stay C0. Fault injections FA1–FA4 turn the tests red.
  - **Product invariant unchanged.** The product `SourceInvariant plane_equation` (a postcondition that a proportional plane exists) is not modified.
  - **Evidence:** `docs/evaluation/geometry/runs/w16-premerge-closure/` (`diagnostics/PROBE_W16_PHASE1_6d01511.json`, `ASSUMPTION_CENSUS_W16_R2.json` with its decision `ASSUMPTION_MECHANISM_DECISION_W16_R2.json`, `logs/FAULT_INJECTION_W16_FINAL.log`).
  - **Residual:** `ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND` — a correctly bound plane used by the wrong construction.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** with the next grounding change
- **default_switch_blocker:** NO
- **acceptance:** plane invariants carry the plane's name; C0 compares the literal's owner with it; a swapped-planes test is refused.
- **verify:** the new swapped-planes test in `tests/geometry/test_assumption_certificate.py`.

### ISSUE-EVAL-ASSUMPTION-GATE-UNTESTED-GUARDS
- **description:** Four fail-closed branches of the assumption gate are reached by no test and no census row: `TEMPLATE_CONSTRAINT_VIOLATED` (template vertices that violate the template), `FRAME_DEPENDENT` (a frame-dependent construction on a C1 slice), `CLOSURE_UNSUPPORTED_KIND` (control flow), and `FORMATION_REJECTED` in `danh_gia_doc_lap`.
- **evidence:** w15 ponytail review mandatory check "dead branches in kiem_gia_dinh" (`docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/PONYTAIL_REVIEW.json`).
- **impact:** Each guard refuses (never serves); a regression that deletes one would go unnoticed by the suite.
- **scope:** `backend/tests/geometry/test_assumption_certificate.py` (tests only, no product change).
- **status:** RESOLVED (w16, `6d015112`) — each branch is reached from a VALID spec, with reason code `ASSUMPTION_INVARIANCE_UNPROVEN` and a valid counterpart that stays C1: a no-op `if` (`CLOSURE_UNSUPPORTED_KIND control flow`), S moved off the normal at A (`T1 TEMPLATE_CONSTRAINT_VIOLATED apex edge ⊥ base`), `(P): z = 2` on a C1 slice (`FRAME_DEPENDENT construct_plane_from_equation` as the only failure), a two-vertex face (`FORMATION_REJECTED`). Fault injections FG1–FG4 remove each branch and turn exactly its test red (`docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/logs/FAULT_INJECTION_W16_FINAL.log`).
- **owner_class:** TEST HARNESS
- **suggested_wave:** any (test-only; no refreeze)
- **default_switch_blocker:** NO
- **acceptance:** one test per guard, each with a fault injection that removes the guard and turns the test red.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_assumption_certificate.py -q`

### ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND
- **description:** C0 binds every literal on a shown value's slice to its own text entity. It does not check that each construction uses the entity the text names. Example: the text says the section (T) is cut by (β), and the program cuts (T) with (α). Both planes' equations are bound correctly, yet the served area is that of the wrong section (9 instead of 16). This is the same class as a midpoint built on the wrong segment: a reading error of the model, not a literal without a source.
- **evidence:** `backend/tests/geometry/test_assumption_certificate.py::test_gioi_han_A_phay_cat_bang_mat_phang_khac_mat_phang_de_noi` (strict xfail). The declared-limit row `A2b_cat_bang_alpha_khi_de_noi_beta` (PROVEN_SAFE C0, served) is in `docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/ASSUMPTION_MECHANISM_DECISION_W16_R2.json`. Registered as limit A′ in ASSUMPTION_CERTIFICATE_AMENDMENT §14.1.
- **impact:** A program that substitutes a determined entity for the one the text names can still be certified. If the text's entity is undetermined (an unnamed or unpinned plane), the served value hides a free parameter. With planes, the strict unnamed-binding rule refuses the common forms (A6b, A8); the named form (A2b) is served.
- **scope:** a closed reader for construction relations in `shape_constraint.py`, for example `(X) cắt <khối> theo thiết diện (T)` and `M là trung điểm của XY`, plus a C0 rule that matches each slice construction against it.
- **status:** RESOLVED for section cuts (w17, `2678b363` + the final-review fix `d3817d5f`; `CACHE_VERSION` 108 → 109 in `fadfd10e`, served → rejected).
  - **How it is fixed.** `shape_constraint.doc_quan_he_cat` reads the text's cut relations (closed vocabulary §15.1: three phrasings; a plane named, written as an equation or through three points; the object of "song song/vuông góc với (X)" is never the cutting plane). `assumption_gate._kiem_phep_dung` makes every `construct_section` on a shown value's slice an extra condition of PROVEN_SAFE: same plane identity (by source `source_fact_id` → verbatim fact located once in the text, then the W16 name/unique rule; point-named planes by point set; equal equations never the same entity) and same solid (vertex set).
  - **Verdicts.** A definite mismatch (both identities known and different) refuses with `CONSTRUCTION_NOT_TEXT_BOUND` (cause CONSTRUCTION). An identity the server cannot pin refuses with `ASSUMPTION_INVARIANCE_UNPROVEN` (cause UNKNOWN).
  - **Measured.** A2b (A′) is refused; the W16 strict xfail passes; O1–O10 match their labels; census rounds 1–2 SHIP with A2b the only gate change since W16 (`docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/ASSUMPTION_MECHANISM_DECISION_W17_R2.json`); the browser wrong-plane fixture is refused and the correct-plane fixture served (area 16).
  - **Residual:** `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT` (other constructions) and `ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL` (planes the vocabulary cannot pin).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** with W15-H3
- **default_switch_blocker:** NO
- **acceptance:** the strict xfail turns green, and a census row per relation is labelled before the run.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_assumption_certificate.py -q -k gioi_han_A_phay`

### ISSUE-ARCH-GROUNDING-GOAL-CLAUSE-AS-DATUM
- **description:** The goal-clause masking of W16 (§14.2) applies to the assumption certificate only. The product grounding gate (`grounding_gate.bang_chung_doan` and the source-length reader) still reads lengths and coordinates on the whole text. A value written only inside a proof request, as in `Chứng minh rằng SA = 5`, can therefore back a GIVEN.
- **evidence:** `test_quan_he_trong_yeu_cau_chung_minh_khong_la_tien_de[B7_chung_minh_do_dai]`: the certificate refuses, while grounding alone would accept the length (W16 Phase 1 probe, `docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/PROBE_W16_PHASE1_6d01511.json`).
- **impact:** Inside the polyhedral scope (U3) the certificate refuses such a request. Outside it, the gate only records, so a request whose only data sits in a proof request can be served.
- **scope:** `backend/app/simulation/semantic_program/grounding_gate.py`, `segment_relation.py` (read on `che_muc_tieu(text)`).
- **status:** RESOLVED (w17, `0b71502b` + the final-review fix `d3817d5f`). `check_grounding` reads GIVEN evidence on `che_muc_tieu(text)` in every route (the grounding stage is not limited to the polyhedral scope); a second pass on the unmasked text only classifies the refusal as `GIVEN_ONLY_IN_GOAL_CLAUSE`. `, biết` ends a goal clause, and in "…, biết Y?" the biết clause is a premise. Measured: G1, G3 and G4 (cylinder, outside the polyhedral scope) refused at `grounding`; G2, G5, G6, G7 served (`test_source_grounding_closure.py`, census W17/W17C rows).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** with W15-H2 (enforcement outside the polyhedral scope)
- **default_switch_blocker:** NO
- **acceptance:** a GIVEN backed only by a goal clause is refused at `grounding`; hypotheses before the request stay readable.
- **verify:** a grounding test in `tests/geometry/test_source_grounding_closure.py`.

### ISSUE-ARCH-SECTION-FILL-OPAQUE-AUXILIARY-LINES
- **description:** The W16 fill order (`THU_TU_TO_THIET_DIEN = 7`) puts the section fill under every line in the transparent queue. That covers the canonical solid edges and every dashed hidden part. three.js draws the whole opaque queue first, however, so opaque lines still sit under the fill and are tinted where they cross the section region. Opaque lines here are the solid part of `duongHaiLuot` segments and lines, the section polygon outline, edge-type objects and the perpendicular marker.
- **evidence:** `frontend/src/simulations/domains/geometry/scene3d-section.test.ts` (W16 ordering test, transparent queue only), ASSUMPTION_CERTIFICATE_AMENDMENT §14.4. No auxiliary opaque line crosses a section region in the six evidence scenes.
- **impact:** An auxiliary segment drawn across a section (for example a height inside the cut) would read amber-tinted, still visible at 55 % of its colour.
- **scope:** `scene3d-view.tsx` (`duongHaiLuot` visible pass, polygon outline): make them transparent-queue lines with opacity 1, as `canonicalEdgeMaterial` already is.
- **status:** OPEN (w16) — renderer limit recorded, not in the brief's minimal layering fix.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** next renderer change
- **default_switch_blocker:** NO
- **acceptance:** the W16 ordering test extended to opaque lines; `SECTION_FILL_UNDER_EDGES` on a scene with an auxiliary segment inside a section.
- **verify:** `cd frontend && npx vitest run src/simulations/domains/geometry/scene3d-section.test.ts`

### ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT
- **description:** The W17 operation check covers `construct_section` only. Other constructions on a shown value's slice are not matched against the text relation that defines them. A midpoint of SB where the text says "M là trung điểm của SA", or a foot of a perpendicular to the wrong plane, is certified when every literal is pinned (C0) or the template holds (C1).
- **evidence:** `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §15.1 (scope: section cuts); W17 final self-review (`docs/evaluation/geometry/runs/w17-operation-annotations/REPORT.md`, limitations).
- **impact:** A program that builds a determined but wrong point can still serve a wrong value. No registered corpus row exercises it.
- **scope:** a closed reader for midpoint / foot / intersection relations in `shape_constraint.py`, and a matching rule beside `_kiem_phep_dung`.
- **status:** PARTIALLY RESOLVED (w18) — midpoints and projections/feet of perpendiculars, in every route, at their own stage.
  - **How it is fixed.** `construction_binding.doc_quan_he_dung` reads the midpoint ("lần lượt" lists in order) and projection relations the text states (closed vocabulary, ASSUMPTION_CERTIFICATE_AMENDMENT §16.1). `doi_chieu_phep_dung` matches each point construction by identity, never by coordinates or values. The route stage `construction_binding` (after execution, before `source_invariant`) refuses MISMATCHED everywhere (`CONSTRUCTION_NOT_TEXT_BOUND`, cause CONSTRUCTION) and UNVERIFIED in the polyhedral scope (`CONSTRUCTION_BINDING_UNVERIFIED`, cause UNKNOWN); `CACHE_VERSION` 109 → 110 (`1e8c5658`).
  - **Measured.** The 23-row W18 corpus matches its registered expectations (route-level census): the 8 MUST_REFUSE rows are refused at the new stage with both relations named, and the correct out-of-vocabulary row is refused as UNVERIFIED; census SHIP with 18/18 gold and no served row of W14–W17C refused (`docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json`); fault injections FB1–FB8 caught.
  - **Residual:** intersection points, centres, centroids and symmetric points are OUT_OF_SCOPE (unchecked, as before W18); phrasing outside the vocabulary is UNVERIFIED (over-refusal in U3) — `ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** with W15-H3 (vocabulary)
- **default_switch_blocker:** NO
- **acceptance:** red tests for a midpoint on the wrong segment and a foot on the wrong plane; census rows labelled before the run.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_construction_binding.py -q`

### ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL
- **description:** A cutting plane defined by a point and a parallel or perpendicular plane ("(Q) qua M và song song với (ABCD) cắt hình chóp theo thiết diện (T)") cannot be pinned by the closed vocabulary. Since W17 such a request is refused with `ASSUMPTION_INVARIANCE_UNPROVEN` even when the program is right. W16 served it, because the certificate had no operation check. A plane named by four or more points binds only to a `construct_plane` through exactly that point set.
- **evidence:** W17C rows Q1/Q2 (`docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/ASSUMPTION_MECHANISM_DECISION_W17_R2.json`); `test_mat_phang_cat_khong_ghim_duoc_la_chua_chung_minh_khong_phai_lech_phep_dung`.
- **impact:** An over-refusal on a common textbook phrasing, with a truthful learner message ("chưa chứng minh được … quan hệ theo cách hệ chưa đọc được"). It is never a wrong answer.
- **scope:** `shape_constraint.doc_quan_he_cat` (read "qua <điểm> và song song/vuông góc với (X)"), and a pinning rule in `assumption_gate` that checks, on the executed memory, that the program's plane contains the point and is parallel or perpendicular to (X).
- **status:** OPEN (w17) — needs the user's vocabulary decision W15-H3.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** with W15-H3
- **default_switch_blocker:** NO
- **acceptance:** Q1 served with the right section; a program through another point or not parallel is refused CONSTRUCTION_NOT_TEXT_BOUND; census rows labelled before the run.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_assumption_certificate.py tests/geometry/test_shape_constraint.py -q`

### ISSUE-ARCH-ANNOTATION-UNANCHORED-QUANTITIES
- **description:** On-figure labels (W17 §15.4) exist only for quantities with a registered anchor: areas of polygons and sections, volumes of polyhedra, distances with a point operand, and given lengths whose segment the text names. Curved objects, angles, distances between two non-point objects and bare-number data ("hình lập phương cạnh bằng 4") have no label; their values stay in the details panel with an `ANNOTATION_UNBOUND` diagnostic. The served correct-plane caption calls an equation plane "Mặt phẳng cho bằng phương trình", not by its name in the text.
- **evidence:** `backend/app/simulation/semantic_program/quantity_annotations.py` (`_DO`, `_do_dai_de_cho`); `scene3d.diagnostics` of the gold p4–p7 scenes; the W17 browser evidence (`results/BROWSER_EVIDENCE.json`, cube: 3 labels).
- **impact:** Fewer labels on curved scenes and on cubes given by a bare edge; nothing is mislabelled.
- **scope:** registered anchors for angles (vertex), curved solids (axis/centre) and named edges of a cube (edge reader), each decided by the backend; display names for equation planes.
- **status:** OPEN (w17) — outside the W17 brief ("Giữ nguyên phạm vi hình và phép đo hiện có").
  - **W18 update.** A point-to-line or point-to-plane distance now anchors at its exact witness (segment to the kernel foot plus a right-angle mark, drawn only while its label shows; §16.7). Distances between two non-point objects still have no witness and no on-figure label; their value stays in the details. The witness overlay draws on top and is not occlusion-classified (declared limit, §16.7 correction). Display names: the served W18 witness case calls the base plane "(ABC)" while the text says "(ABCD)".
- **owner_class:** PRODUCT
- **suggested_wave:** next presentation wave
- **default_switch_blocker:** NO
- **acceptance:** each new anchor kind has a backend binding test and a browser placement check (≤ 24 px, inside, no overlap).
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_scene3d_annotations.py -q`

### ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY
- **description:** The W18 construction binding (§16) reads only the closed midpoint/projection vocabulary. Four declared limits follow. (1) A correct construction phrased outside the vocabulary ("Gọi M là điểm chính giữa của đoạn SA", row B16) is UNVERIFIED and refused in the polyhedral scope (U3). (2) Points whose text role is a centre, centroid, orthocentre, intersection or symmetric point are OUT_OF_SCOPE whatever operation builds them, so a wrong construction of them is not identity-checked (§16.3 correction (i)). (3) A receiver line or plane through a point that is not a text entity, an equation plane or a derived line cannot be pinned: UNVERIFIED (§16.3 correction (ii)). (4) A text vertex built by a construction operation without a W18 relation is layout, governed by the W15 certificate, not by the binding (§16.3 correction (iii)).
- **evidence:** W18 corpus rows B16 (`out_of_vocab_ok`, refused UNVERIFIED) and the W15 row `oov:chia_doan_canh` (refused earlier, now at `construction_binding`) in `docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json`; `tests/geometry/test_construction_binding.py`.
- **impact:** Over-refusal of correct programs on unread phrasings, with a truthful message ("AlgoSim chưa đối chiếu được … Đây là giới hạn của hệ, không phải lỗi của đề"). For limit (2), a wrong centre or intersection point is caught only by the coordinate invariants and the W15 certificate, as before W18.
- **scope:** `construction_binding.py` vocabulary (divisions with a ratio, unnamed receivers, centres and intersections), each with labelled corpus rows before the change.
- **status:** OPEN (w18) — the brief keeps the vocabulary narrow ("Giữ vocabulary mở rộng hẹp cho trung điểm và phép chiếu đã hỗ trợ"); widening belongs to the user's vocabulary decision W15-H3.
- **w01:** PARTIAL (regular-square-pyramid-w01, `3bdada32`) — limit (2) narrowed: "X là giao điểm (của) PQ và RT" (two lines named by two points each) and "X là tâm (của) (mặt) đáy / hình vuông ABCD" of the unique solid are bound by identity (`intersect_line_line` on the same two lines, or the midpoint of a diagonal for a centre); corpus rows S7 (MATCHED, served) and N4 (midpoint of AB for O, MISMATCHED, refused CONSTRUCTION), labelled before the change. Centroids, orthocentres, symmetric points and intersections with planes remain OUT_OF_SCOPE; `intersect_line_line` is not added to `PHEP_TRONG_PHAM_VI`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** with W15-H3
- **default_switch_blocker:** NO
- **acceptance:** each new phrasing has a MATCHED and a MISMATCHED corpus row labelled before the run; no served gold row changes.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_construction_binding.py -q`

### ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE
- **description:** The product scope gate (`co_duong_thuc_thi`) has no clue for "độ dài". A request whose only question is "Tính độ dài đoạn MC", with no other clue in the text (no named solid type, no other measure), is refused at the `scope` stage before any construction is checked.
- **evidence:** W18 Phase 1 reproduction through the product boundary: rows B18/B19 (`docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_84ce7b70.json`) stop at `scope`; the same rows reach `construction_binding` in the route-level census. The gold p1 rows pass only through "hình vuông".
- **impact:** An over-refusal of a plain length question on a text without a solid keyword; never a wrong answer.
- **scope:** the scope-gate clue table (routing policy). A change here moves requests from refused to served, so it needs the corpus re-run and a `CACHE_VERSION` decision.
- **status:** RESOLVED (regular-square-pyramid-w01, `9d66c603`; `CACHE_VERSION` 111 → 112 in `de5b2331`) — `_MANH_MOI_NGHIA_VU["distance"]` += "độ dài" (the length of a segment is the distance between its endpoints). Found again by the W1 cache probe through `run_pipeline` (corpus row S5 "Tính độ dài cạnh bên SA", served by the route, refused at `scope`). Acceptance probe through the product boundary: B18 served, B19 refused at `construction_binding` (`docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/SCOPE_LENGTH_CLUE_PROBE_1310658b.json`); refused → served only, so no stale cache row (refusals are never cached); the bump is for other served-envelope changes of W1.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** next routing wave
- **default_switch_blocker:** NO
- **acceptance:** B18 served and B19 refused at `construction_binding` through the product boundary; no served gold row changes.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/reproduce_construction_binding.py` (writes `CONSTRUCTION_BINDING_REPRODUCTION_<sha>.json`; refuses to overwrite)

### ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE
- **description:** On the default `LLM_ONLY` route a text that itself states a zero length ("cạnh đáy bằng 0") is refused by the kernel at `execution` (coincident base vertices), with `refusal_cause` UNKNOWN, so the learner is not told the text is at fault. `NON_POSITIVE_LENGTH` (cause SOURCE) is produced only by the deterministic compiler's eligibility check, which the older families' browser negatives use (`DETERMINISTIC_FIRST`).
- **evidence:** fixture `regular_square_pyramid_non_positive` (`docs/evaluation/geometry/runs/regular-square-pyramid-w01/inputs/fixtures/`), first registered with the compiler-route code and corrected before any browser run (`diagnostics/PREREGISTRATION_CORRECTIONS.json` PC1).
- **impact:** Fail-closed (no answer, no scene) but the refusal does not point at the text; the same holds for the six older families on the default route.
- **scope:** a source-level non-positive length check on the default route (server-side reader of the text), shared by every family.
- **status:** PARTIAL (regular-square-pyramid-w02, `c86cf53c`) — when execution fails on the default route and the premise text (goal clauses masked) states a length ≤ 0 that the server reader reads (a named segment, or a single solid's base edge, height, lateral edge, apothem, cube edge), the refusal is `NON_POSITIVE_LENGTH` with cause SOURCE and the learner's subject ("cạnh đáy"); otherwise UNKNOWN stays (a valid text whose program degenerates is not called wrong). Labelled red-then-green rows: `tests/geometry/test_regular_square_pyramid_height.py` (`cạnh đáy bằng 0` ⇒ SOURCE; `cạnh đáy bằng 4` with a degenerate program ⇒ UNKNOWN); the regular-pyramid browser negative now expects SOURCE. **Not closed:** the six older families have no labelled rows on the default route (their browser negatives use the compiler route), and a text-stated ≤ 0 length refused at an EARLIER stage keeps that stage's cause.
- **w01:** OPEN (regular-square-pyramid-w01) — outside the W1 scope (changes every family's refusal).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** next refusal-message wave
- **default_switch_blocker:** NO
- **acceptance:** a text stating a length ≤ 0 is refused with cause SOURCE on the default route for every family; labelled rows before the change.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/generate_generic_tier_a_fixtures.py --out <scratch>` (asserts the current refusal of `regular_square_pyramid_non_positive`)

### ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY
- **description:** The source length reader binds a number only to the segment written next to it. In "SA = SB = SC = SD = 3" it reads SD = 3 and nothing for SA, SB, SC, so a program that cites SA = 3 is refused at `grounding` with `SOURCE_EVIDENCE_CONFLICT` although the text determines the answer.
- **evidence:** corpus row `R2_L1_chained_equal_lateral_edges` (`docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/corpus/LABELS_R2.json`, `product_limit: true`; the independent oracle derives V = 16/3); `segment_relation.do_dai_trong_de` on that text returns {AB: 4, SD: 3}.
- **impact:** Over-refusal (never a wrong answer) of a common way to state equal lateral edges; the refusal cause is CONSTRUCTION, so the learner is not told the text is at fault.
- **scope:** `backend/app/simulation/semantic_program/segment_relation.py` (one length reader, shared by grounding and the certificate) — a chain `X1 = X2 = … = v` of segment names.
- **status:** RESOLVED (regular-square-pyramid-w05, `c15e6fab`) — `segment_relation.MAU_DO_DAI` reads the chain prefix and every segment of the chain gets the value (one value per segment, a segment with two values still dropped); `cac_doan_truoc` replaces `nhan_doan_truoc` for GIVEN evidence and quantity annotations. Labels registered first (`runs/regular-square-pyramid-w05/diagnostics/corpus/LABELS_W05.json`, RED log before the fix): R2_L1 and W5_A served V = 16/3; mixed chains, a chain without a value, a wrong value and a segment outside the chain refused. The two W13 probe rows for `AB = AC = 5` moved to the registered-change set (`test_source_length_reader.py`). `CACHE_VERSION` kept at 115 by row proof (`diagnostics/cache_proof/CACHE_DECISION_W05.json`).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** next source-reader wave
- **default_switch_blocker:** NO
- **acceptance:** a chain of segment names ending in one value binds every segment of the chain; a chain mixing segments of different lengths in the text stays a conflict; labelled rows before the change; CACHE_VERSION decided by rows (refused → served).
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_regular_square_pyramid.py -q -k R2_L1`

### ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET
- **description:** A text relation of the W18 vocabulary (midpoint, projection; amendment §16.1) whose target point the program declares as a literal — coordinates, not a construction operation — is neither matched by `construction_binding` nor recorded `NOT_REALIZED`. The binding only sees construction operations. Safety then rests on backstops: the `segment_division` coordinate invariant for midpoints and the W15 assumption certificate for projections, the latter only inside the polyhedral scope (U3).
- **evidence:** W18 final self-review, deferred minor (`docs/evaluation/geometry/runs/w18-binding-focus/HANDOFF.md` § Known leftovers; `REPORT.md` limitations). No probe through the production boundary exists yet, so whether the backstops block the wrong identity in every case is unmeasured.
- **impact:** unknown until probed. A literal target with the right coordinates but the wrong identity, or a projection outside U3, may be served without the identity check W18 promises for constructed points.
- **scope:** `backend/app/simulation/semantic_program/construction_binding.py` (record `NOT_REALIZED` or check the literal's value against the relation), probes and corpus rows.
- **status:** RESOLVED (w20, `65c90bde`; `CACHE_VERSION` 110 → 111 in `bedb1040`, served → rejected) — `construction_binding` follows each name that directly denotes a §16.1 relation target along its `assign X = var Y` chain; coordinates anywhere on it give `DEFINED_BY_COORDINATES`, refused in every scope with `CONSTRUCTION_REPLACED_BY_COORDINATES`, cause CONSTRUCTION (amendment §17). Probe through `run_pipeline` with labels registered before the fix: 20/27 → 26/27 (the remaining row C7 is refused by the domain gate for a reason recorded before the fix); census of the W14–W18 corpora: 179 rows compared with W18, no route change, AC2 18/18; fault injections FL1–FL7 caught, FL8/FL9 (grounding guards removed) still refused by this stage. No longer blocks merge.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** pre-merge correctness probe
- **default_switch_blocker:** NO
- **acceptance:** a probe through the production boundary (the route, not the census helper) with literal-declared targets for a midpoint and a projection, inside and outside U3, labelled before the run; evidence that each wrong identity is refused with a named code by a backstop, or a fix that makes the binding refuse or record it; no served gold row changes.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/probe_literal_target.py --tag <tag>` (writes a new artifact, refuses to overwrite) + `.venv/Scripts/python.exe -m pytest tests/geometry/test_construction_binding_literal.py tests/geometry/test_construction_binding.py -q`

### ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT
- **description:** Historical reports formerly occupied the `docs/` root beside living documents.
- **evidence:** `docs/evaluation/HISTORICAL_REPORTS.md`; `docs/evaluation/geometry/runs/docs-cleanup/inventory.md`.
- **impact:** resolved: 156/167 retained reports moved; the root contains only 11 report/contract exceptions with file-level path constraints.
- **scope:** complete; catalog paths, consumers and byte-identity guard updated without rewriting report content.
- **status:** RESOLVED (`docs-cleanup`, lần tổ chức report 2026-10-08).
- **owner_class:** DOCUMENTATION
- **suggested_wave:** none
- **default_switch_blocker:** NO
- **acceptance:** every catalogued report moved byte-identical; migration map; 0 broken links in living documents; frozen artifacts unchanged.
- **verify:** `cd backend && .venv/Scripts/python.exe scripts/audit_docs_information_architecture.py`

### ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED
- **description:** `D:/tmp` holds 212 entries left by waves before W19: 210 scripts, logs, output folders and stale worktree copies (one folder contains a `.git`), and two settings backups that were not opened. W19 inventoried them but deleted none, because "unknown" outputs must be kept until verified.
- **evidence:** `docs/evaluation/geometry/runs/w19-docs-organization/inventory/INVENTORY.json` (`temp`, class `UNKNOWN_EARLIER_WAVE`).
- **impact:** disk use and confusion with live worktrees; possible unsaved diagnostics inside.
- **scope:** a verification pass (each entry: duplicate of a committed file, reproducible output, or unique) or the user's decision to discard.
- **status:** OPEN (w19); PARTIAL (w20) — a bounded mechanical pass deleted 8 entries by exact path: 6 files equal to blobs reachable from a ref, 1 empty file and 1 clean clone whose HEAD and refs all exist in this repository (`docs/evaluation/geometry/runs/w20-cleanup-premerge/inventory/DELETION_LOG.json`). 204 entries stay `REVIEW_REQUIRED`: 126 loose files and 76 folders that match nothing in git, and the two settings backups (not opened).
- **cfr_check:** (2026-10-05, `cuboid-final-review`) `D:/tmp` holds exactly the 204 registered entries — none new, none gone; nothing outside the repository deleted (no entry verified anew). Inside `docs/`, two git-ignored `__pycache__` folders were deleted by exact path after a hash check (`docs/evaluation/geometry/runs/cuboid-final-review/inventory/CLEANUP_LOG.json`).
- **owner_class:** OPERATIONS
- **suggested_wave:** housekeeping, any time
- **default_switch_blocker:** NO
- **acceptance:** every entry classified with evidence; deletion only by exact path of verified duplicates or reproducible outputs.
- **verify:** re-run `inventory_cleanup_w20.py` of the W20 run (writes a new inventory; refuses to overwrite).

### ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE
- **description:** Running the full backend suite in the main working tree rewrites committed evidence. `backend/tests/geometry/test_second_family_live_measurement_reconciliation.py` calls `run_reconciliation()` of `backend/scripts/reconcile_second_family_live_measurement.py` (lines 65 and 165), which writes four files into the frozen run folder `docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/`. Three come back byte-identical; `SOURCE_EVIDENCE_INTEGRITY.json` changes its `note` when the scratch raw-response file is absent. A later test that reads `git status` (`test_second_family_preregistration_evidence_repair.py::test_10_working_tree_co_favicon_deletion_khong_ghi_clean`) then sees a tree dirtier than the user's favicon deletion.
- **evidence:** W19 main-tree run (`docs/evaluation/geometry/runs/w19-docs-organization/verification/logs/PYTEST_FULL_MAIN_TREE_DIRTY.log`); file mtime inside the run window; W19 restored the file to its committed blob `4d9fad55` before staging and did not commit the mutation.
- **impact:** a full run outside a detached worktree mutates frozen evidence that can then be committed by accident, and one test becomes dependent on tree state and test order. Detached clean worktrees (the repository's rule for authoritative runs) are not affected in practice: the change is discarded with the worktree.
- **scope:** `backend/scripts/reconcile_second_family_live_measurement.py` (write to a caller-given directory) and its test (use `tmp_path`, compare instead of writing); no product code, no candidate change.
- **status:** RESOLVED (w20, `4e647861` + `654beda3`) — `run_reconciliation(out_dir)` takes a required output folder and refuses the frozen folder and any folder inside it; the CLI needs `--out`; the tests pass `tmp_path` and check that the frozen folder keeps its hashes and its `git status`. Root cause: the frozen `note` depends on a file outside the repository that no longer exists (`docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/FROZEN_WRITER_REPRODUCTION.json`). A full backend run in the main tree (`8b6a1a3a`) left `git status` identical and `test_10_…` passed with only the user's favicon deletion; fault injections FE1–FE3 caught.
- **owner_class:** TEST
- **suggested_wave:** the next wave that touches backend tests
- **default_switch_blocker:** NO
- **acceptance:** a full backend run in the main tree leaves `git status --porcelain -- docs/evaluation` empty, and `test_10_…` passes in the main tree with only the user's favicon deletion.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest -q && git status --porcelain -- ../docs/evaluation`

### ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS
- **description:** Five docs fault-injection tests write into the working tree. `test_fi_07` and `test_fi_08` append a line to `AGENTS.md`, `test_fi_11` to `docs/ROADMAP.md`, and each restores the original text in `finally`; `test_fi_14` and `test_fi_17` create a file under `docs/` and delete it.
- **evidence:** `backend/tests/geometry/test_docs_information_architecture.py` (`test_fi_07`, `test_fi_08`, `test_fi_11`, `test_fi_14`, `test_fi_17`); found by the W20 scan for tests that write outside a temporary folder (`docs/evaluation/geometry/runs/w20-cleanup-premerge/REPORT.md`).
- **impact:** a run killed between the write and the restore leaves a living document changed or a stray file at the docs root, and a concurrent reader (another test process, a docs audit) can see the injected line. No frozen evidence is written, so the rule of `AGENTS.md` §4 holds.
- **scope:** the five tests only (inject into a temporary copy of the files the audit function reads); no product code, no candidate change.
- **status:** OPEN (w20) — registered, not fixed (outside the scope of the W20 issues).
- **owner_class:** TEST
- **suggested_wave:** the next wave that touches the docs tests
- **default_switch_blocker:** NO
- **acceptance:** a full backend run leaves the bytes of `AGENTS.md` and of every file under `docs/` unchanged (hash before and after the run).
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_docs_information_architecture.py -q` with a hash of `AGENTS.md` and `docs/**` before and after.

### ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE
- **description:** Eight of the ten T1 scripts in `frontend/package.json` (`test:domain:algorithm`, `binary`, `logic`, `network`, `database`, `web`, `generic`, `tree`) point at informatics domain folders removed by `LEGACY_INFORMATICS_REMOVAL` (2026-09-02); only `shared-ui` and `classroom` still select tests. The geometry domain has no T1 script and no owner entry in `frontend/scripts/impact.mjs`, so a change under `src/simulations/domains/geometry/` makes T0 report `IMPACT_MAPPING_MISSING` and escalate to all of `src/` plus pytest.
- **evidence:** `frontend/package.json` lines 13–22; `node frontend/scripts/impact.mjs --dry --files src/simulations/domains/geometry/scene3d-view.tsx` (2026-10-05, `cuboid-final-review`); `docs/TEST_TIERS.md` (dated note under the tier table).
- **impact:** T1 cannot be run for the only product domain; T0 is slow for geometry edits (it still never selects 0 tests, so no false green).
- **scope:** `frontend/package.json` (drop the eight dead scripts, add `test:domain:geometry`) and the owner tables of `frontend/scripts/impact.mjs`; tooling only, no product code, no candidate change.
- **status:** RESOLVED (run `repo-cleanup`, 2026-10-08) — the eight dead scripts are gone, `test:domain:geometry` (33 files) and `test:domain:semantic` exist; `impact.mjs` lists geometry and semantic in `DOMAIN_TESTS` and maps `frontend/src/simulations/domains/geometry/**` by folder (no `IMPACT_MAPPING_MISSING`). The old verify command passed a frontend-relative path, which the selector never matched; the path is repo-relative.
- **owner_class:** OPERATIONS
- **suggested_wave:** the next wave that touches the test tooling
- **default_switch_blocker:** NO
- **acceptance:** every `test:domain:*` script selects at least one test file, a geometry script exists, and `impact.mjs --dry` maps a geometry file without `IMPACT_MAPPING_MISSING`.
- **verify:** `cd frontend && npm run test:domain:geometry && node scripts/impact.mjs --dry --files frontend/src/simulations/domains/geometry/scene3d-view.tsx`

### ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE
- **description:** In the numbered invariant table of `docs/ARCHITECTURE_MAP.md` §5, the *enforced at* and *test* cells were written when each row was added. In 22 rows (#1–#8, #10, #11, #14–#16, #18, #20–#26, #29) at least one named file no longer exists, mostly removed with the informatics domain; in #1–#8, #11, #14 and #15 none of the named files exists. The principle of such a row may still hold, but its current lock is not recorded.
- **evidence:** `docs/evaluation/geometry/runs/cuboid-final-review/inventory/DOCS_INVENTORY.json` (`architecture_map_invariant_pointers`: per row, the named files that exist and those that do not); dated note under the §5 heading.
- **impact:** a reader can take a row as test-locked when nothing locks it any more; tests and docs cite rows by number (`#11/#12`, `#14`, `#31`), so the numbering must stay.
- **scope:** per row: name the current lock, or mark the row as retired with the date and the removal that retired it; keep every number. Rows #27–#39 already point at live code.
- **status:** RESOLVED (`cuboid-acceptance`, 2026-10-05) — the count was 24, not 22: #9 and #12 write "như trên" and inherited the dead pointers of #8 and #11. Each of the 24 rows was reconciled against the running system down to the assertion: 9 `CURRENT_ENFORCED` (#1, #2, #3, #8, #9, #11, #21, #22, #29), 1 `CURRENT_UNVERIFIED` (#14 → `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`), 14 `HISTORICAL_NOT_APPLICABLE` (marked **LỊCH SỬ** in the map, with the product-path reason and the successor row), 0 `VIOLATED`. The pointer cells now name only live files; requirement text kept verbatim; every number kept. Old pointers and the commit that deleted each file: `docs/evaluation/geometry/runs/cuboid-acceptance/results/INVARIANT_RECONCILIATION.json`.
- **owner_class:** DOCUMENTATION
- **suggested_wave:** the next architecture or docs wave
- **default_switch_blocker:** NO
- **acceptance:** `architecture_map_invariant_pointers` reports no missing file for a row that is not marked retired. Met: 39/39 rows, 0 missing files (`cuboid-acceptance`, `results/logs/DOCS_GATES_FINAL.log`).
- **verify:** re-run `docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/inventory_docs_cfr.py --check` (or its `invariant_pointers` function) on the updated map.

### ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM
- **description:** Invariant #14 (live evaluation is opt-in) has no lock over `backend/scripts` as a whole. Thirty scripts check `ALLOW_LIVE_AI` and five require `--live` or `--execute-live --confirm-live-execution`. Ban đầu ghi nhận hai script gọi live không cần opt-in: `run_live_gemini_semantic_smoke.py` (2026-08-20, đề Tin học; đã xoá/retire vì không còn consumer hay chức năng hình học) và `run_rectangular_pyramid_live_analyze.py` (2026-09-24; một live Analyze request mặc định, `--offline-eval` opts out instead of in). Vấn đề vẫn MỞ và tiếp tục áp dụng cho script hình học còn lại.
- **evidence:** static probe, part 5 of `docs/evaluation/geometry/runs/cuboid-acceptance/diagnostics/invariant_checks_cacc.sh` (54 scripts listed with their opt-in tokens, `call_gemini` stub and call sites), then scripts read by hand. Not reproduced by a run: that would need a live call and reading `backend/.env`.
- **impact:** running the remaining script by name spends quota without the `ALLOW_LIVE_AI=1` decision the repository requires (`CLAUDE.md` §6). No effect on the product, the learner, the candidate or any acceptance measurement (all made 0 live calls).
- **scope:** `backend/scripts` only: `run_live_gemini_semantic_smoke.py` đã retire; cần bổ sung opt-in cho `run_rectangular_pyramid_live_analyze.py` và thêm một AST test chặn script gọi model mà thiếu opt-in; no product code, no candidate change.
- **status:** OPEN (`cuboid-acceptance`) — registered, partially mitigated by retiring the legacy smoke script, not fully fixed for the pyramid script.
- **owner_class:** OPERATIONS
- **suggested_wave:** the next task that touches `backend/scripts`
- **default_switch_blocker:** NO
- **acceptance:** every `backend/scripts/*.py` that can reach the model aborts without `ALLOW_LIVE_AI=1` (or an explicit live flag), locked by a test.
- **verify:** `bash docs/evaluation/geometry/runs/cuboid-acceptance/diagnostics/invariant_checks_cacc.sh --no-vitest` (part 5) plus the new AST test.

### ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS
- **description:** regular-square-pyramid-w02 moved «Các bước dựng» to a floating panel (`scene3d-floating-panel.tsx`) so opening it no longer resizes the canvas. The inspector (`.geo3d-soi`) still becomes a grid COLUMN at ≥ 1100 px when an object is selected (decision recorded in `global.css` §2: a column does not cover the figure), so selecting an object still narrows the canvas and changes the camera aspect; the drawers («Thành phần», «Đề bài», «Đại lượng») are already overlays.
- **evidence:** `frontend/src/styles/global.css` (`.geo3d-san:has(.geo3d-soi)` grid); the W2 brief asks the floating mechanism to be used "for the information panels where it fits" without naming the inspector.
- **impact:** Presentation only; no wrong value. The causal-restore gate already measures the camera at equal selection states.
- **scope:** `Scene3DExplorer.tsx` (inspector), `global.css`, the causal-restore and inspector browser gates.
- **status:** RESOLVED (regular-square-pyramid-w04, `98b1ce8d` + `c8c49f3c`) — the user did not accept the W3 deferral and asked for one shared mechanism: the inspector is a `BangNoi` like every information panel and the ≥ 1100 px grid column is removed (`scene3d-panels.test.tsx` locks its absence). Browser evidence `runs/regular-square-pyramid-w04/results/W04_PANELS_PROBE.json` (canvas and camera unchanged while opening, closing and selecting; 7 families × desktop, 1366×650, mobile). The visual result awaits the human review (`runs/regular-square-pyramid-w04/REVIEW.md`).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** next UI wave, after the user decides
- **default_switch_blocker:** NO
- **acceptance:** the decided layout, with the browser gates re-measured on desktop and mobile.
- **verify:** `node frontend/scripts/check-scene-controls.mjs …` (extend with the inspector) and the main suite's causal restore.
- **W3 note (regular-square-pyramid-w03):** re-assessed as a presentation choice (no wrong value, no lost operation); still a user decision — the W3 `REVIEW.md` §3 proposes keeping the column on this branch. Not accepted by the user yet.

### ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE
- **description:** regular-square-pyramid-w03 (H-W2-2) builds the segment whose length the problem asks for (`formation._doan_duoc_hoi`) when no segment, polygon edge or solid face edge joins its two points. The check is on endpoint identity only: a requested segment that lies ON an existing edge without sharing both endpoints (SM with M the midpoint of SA) is built and drawn over that edge.
- **evidence:** `backend/app/simulation/semantic_program/formation.py` (`_canh_da_dung`); no row of the construction-binding corpus or the W1/W2 corpora has this shape (`runs/regular-square-pyramid-w03/diagnostics/PROOF_CACHE_ROW_W03.json`).
- **impact:** Presentation only — two coincident strokes; the value and the label are right.
- **scope:** formation planner (IR level, no coordinates) or the renderer's visual-owner rule.
- **status:** RESOLVED (regular-square-pyramid-w04, `ce44eb38`) — observed in the browser before the fix (`runs/regular-square-pyramid-w04/diagnostics/sm_overlap/before/`: SM drawn over SA). `quantity_annotations.doan_tren_canh` decides exactly (collinear + parameter in [0, 1]) that SM lies on edge SA; the scene only looks the edge id up (`boundary_edge_ids` + `edge_span`, no geometry in `scene3d.py`); the renderer lets the canonical edge own the stroke and highlights only the S–M span when SM is selected; selection, label and provenance kept. Verify: `pytest tests/geometry/test_segment_on_solid_edge.py -q`, `npx vitest run src/simulations/domains/geometry/scene3d-sub-edge.test.ts`, browser `runs/regular-square-pyramid-w04/results/SM_OVERLAP_AFTER_<sha>.json`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** when a corpus row needs it
- **default_switch_blocker:** NO
- **acceptance:** a requested collinear sub-segment is not drawn twice, with a test on a real program.
- **verify:** `pytest tests/geometry/test_asked_segment_construction.py -q`

### ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES
- **description:** Points live in ℚ³. An equilateral triangle with rational vertices has side² = 2N·q² (N an Eisenstein norm; never a rational square) and the apex height over it is a rational multiple of √3, so a regular triangular pyramid or regular tetrahedron with a RATIONAL edge ("cạnh đáy bằng 3", "tứ diện đều cạnh a = 2") has no exact layout. Template T8 serves only b² ∈ {2k², 6k²}, h² = 3t² (ASSUMPTION_CERTIFICATE_AMENDMENT §18.2); other rational realisations (N = 7, …) have no canonical frame; the apothem of a regular triangular pyramid is not read.
- **evidence:** `runs/regular-triangular-pyramid-w01/PLAN.md` §1 (brute force), `test_regular_triangular_pyramid.py::test_tam_giac_deu_nguyen_khong_bao_gio_co_canh_huu_ti`, corpus rows U1–U4 (refused with `TEMPLATE_NOT_REPRESENTABLE T8`).
- **impact:** most textbook regular-triangular problems (rational or symbolic edges) are refused honestly, not served; the family is narrow (`product_capability.regular_triangular_pyramid` = `foundation_only`).
- **scope:** a similarity frame (lay out a rational similar copy, scale every measured length by λ with λ² ∈ ℚ, area by λ², volume by λ³) — touches interpreter measures, postconditions, grounding and scene labels; decision of the user 2026-10-07: NOT in this task (risk of silently wrong answers).
- **status:** RESOLVED (run `exact-dimensions`, `de6d3e35`, 2026-10-07) — not by a similarity frame (one λ cannot fix an independent base and height) but by an affine chart + rational Gram metric derived from the text's six edge lengths (`geometry/metric.py`, `assumption_gate.do_luong_cua`); rational, fractional and decimal base + height, base + lateral edge and rational tetrahedron edge are served on the route, radical cases byte-identical; corpus 31 rows, oracle 18/18 (`runs/exact-dimensions/labels.json`, `report.md` §1). Remaining limits, still refused: symbolic sizes, sums of radicals; the metric covers this family only. Verify: `pytest tests/geometry/test_exact_dimensions.py -q`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** —
- **default_switch_blocker:** NO

### ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED
- **exact-dimensions update (2026-10-07):** the layout restriction is gone — any affinely independent chart is served (axis chart, rough chart, tilted frames); what stays unmeasured is whether the model extracts the sizes and declares the four vertices with literal coordinates. Still 0 model calls.
- **description:** The deterministic route serves a regular triangular pyramid only when the program lays the base on a tilted rational plane (x+y+z=k); prompts, grammar card and schema are unchanged, and no live measurement shows that the model chooses such a layout. Offline evidence uses LLM-style programs written in `test_regular_triangular_pyramid.py`.
- **evidence:** `runs/regular-triangular-pyramid-w01/` (0 model calls; model surface fingerprint `b1714b56…` unchanged).
- **impact:** product reach for this family is unknown; the honest product status is `foundation_only`.
- **scope:** a model-surface change (layout hint) + a pre-registered live measurement with budget — needs the user's decision.
- **status:** OPEN (regular-triangular-pyramid-w01)
- **owner_class:** EVALUATION
- **suggested_wave:** the next task with a live budget
- **default_switch_blocker:** NO

### ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART
- **description:** A regular triangular pyramid whose text lacks a size (no height, no lateral edge) cannot have a metric (`do_luong_cua` returns None), so a program on a non-Euclidean chart is checked in its chart's Euclidean metric: the template sees no regular figure and the gate refuses with `ASSUMPTION_INVARIANCE_UNPROVEN` (cause UNKNOWN) instead of the precise "the missing size determines the answer".
- **evidence:** `runs/exact-dimensions/labels.json` rows N01/N09/N10; fixture `regular_triangular_pyramid_assumption` (expected INVARIANCE_UNPROVEN/UNKNOWN); browser refusal image `runs/exact-dimensions/images/regular-triangular-pyramid/negative/assumption/desktop/refusal.png`.
- **impact:** refusal is correct; its reason is less informative for the learner.
- **scope:** detect "regular family + missing size" before the chart check and report the determining size.
- **status:** RESOLVED (2026-10-08) — cổng chỉ kết luận khi dependency slice thực tế chứa `measure(volume)`, source
  reader đọc trọn đúng quan hệ T8 và `kich_thuoc_t8` xác nhận kích thước thiếu mà không có mâu thuẫn. Quan hệ
  `V = √3·b²·h/12` tạo chứng minh giải tích trước chart check; N01/N09 trả thiếu `chiều cao`, N10 trả thiếu `AB` và
  `chiều cao`, đều giữ `unsupported` nhưng đổi sang `ASSUMPTION_DETERMINES_ANSWER`/`SOURCE`. Ca mâu thuẫn, target
  khác, quan hệ ngoài vocabulary và tứ diện đều vẫn đi đường fail-closed cũ. Test route + API/pipeline:
  `test_exact_dimensions.py`, `test_mocked_production_e2e.py`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** with the next change to the assumption gate
- **default_switch_blocker:** NO

### ISSUE-ARCH-TETRAHEDRON-OUTSIDE-POLYHEDRAL-REGION
- **description:** A plain "tứ diện ABCD" (not "đều") is not read as a solid, so its problems stay outside the polyhedral region where the assumption gate refuses (decision U3): they are served without a certificate. Before regular-triangular-pyramid-w01 the same held for "tứ diện đều": "Cho tứ diện đều ABCD có cạnh bằng 3" with a non-regular rational layout was SERVED with V = 5/2 (true value 9√2/4) — that case is now refused (row U2).
- **evidence:** `runs/regular-triangular-pyramid-w01/diagnostics/logs/RED_BASELINE.log` (U2 before the change); attempt to read every "tứ diện" as a pyramid turned three served tetrahedron tests red (trirectangular OABC, circumsphere, scalar data) — dated correction to §18.1.
- **impact:** a non-regular tetrahedron problem whose program realises another configuration can be served with a wrong value (no template certifies it).
- **scope:** templates for the common tetrahedra (trirectangular, "AB, AC, AD đôi một vuông góc") before bringing plain "tứ diện" into the region.
- **status:** OPEN (regular-triangular-pyramid-w01)
- **owner_class:** ARCHITECTURE
- **suggested_wave:** a tetrahedron template task
- **default_switch_blocker:** NO

### ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL
- **description:** On mobile (390×844) the canvas is 356×517 CSS px and the camera fits the figure to 68 % of its binding dimension: width-bound families fill 32–57 % of the canvas height (regular triangular pyramid 32 %, regular square pyramid 40 %), so the canvas shows blank bands above and below the figure, and an opened panel (steps, detail) lands below the fold — the learner scrolls between figure and panel.
- **evidence:** `runs/regular-triangular-pyramid-w01` diagnostic browser run (label boxes per family, mobile): fill_w 0.68 for seven families, the rectangular pyramid is height-bound (figure aspect 1.77 > canvas 1.45, fill_h 0.68).
- **impact:** usability on phones; no wrong value.
- **scope / options (decision needed):** (a) canvas height tied to width (e.g. 1.25×) removes the blank band but shrinks the height-bound rectangular pyramid by ~14 % — excluded by the brief ("không áp trần … làm hình nhỏ") and by the W5 answer to W4 R4 ("không trần"); (b) a per-scene height from the figure's projected aspect (no shrink, more code, camera-coupled); (c) overlay the two floating buttons on the canvas again (+~50 px for panels) — reverses the w10 fix that moved them out of the apex's way; (d) a one-row tool bar on mobile (+~55 px) — touches W5 review item R3 (2 × 2 grid). Nothing applied in regular-triangular-pyramid-w01.
- **status:** RESOLVED (run `mobile-canvas-fit`, product `c9bcdcdb`) — waiting for the user's visual review (`runs/mobile-canvas-fit/review.md` E-R1–E-R6). The user asked to choose and implement; option (b) kept, narrowed: on the narrow layout only (≤ 48rem, where panels flow below) the canvas is width × projected figure aspect (same points, display rotation and view direction as the camera fit — `scene3d-view.tiLeKhungHinh`), capped by the available height, floored at 320 px (`scene3d-playback.caoKhungVuaHinh`). Height-bound figures keep the full height (no cap, no shrink); desktop/low screens unchanged; the aspect depends on the scene only, so steps, selection and panels never move the canvas or camera. Measured (`results/MOBILE_LAYOUT_PROBE.json`, 8 families × 5 viewports): portrait canvas 519 → 320–485 px for the seven width-bound families (rectangular pyramid, height-bound, stays 519), figure 0.59–0.73 of the canvas height (before: 0.48–0.60). Found on the way and fixed in the same commit: the current step of a long steps panel left the panel's view while stepping (19/40 runs, desktop too). Residuals: `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD`, `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** — (resolved; human review pending)
- **default_switch_blocker:** NO

### ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD
- **description:** A phone held in landscape (844×390) is wider than 48rem, so it gets the desktop layout: floating panels, canvas at the 320 px floor (`CAO_KHUNG_MIN`) because less than that is available, and the play bar (Bước trước · Phát · Bước sau · «Bước n/N») sits below the fold — the learner scrolls ~40 px to reach it, and the top row scrolls away when they do.
- **evidence:** `runs/mobile-canvas-fit/results/MOBILE_LAYOUT_PROBE.json` (`landscape` runs: canvas 320 px at y = 60, controls at y ≈ 392 in a 390 px viewport); unchanged before the D5 change (`diagnostics/baseline_38a19c65/`).
- **impact:** usability in landscape on phones; no wrong value.
- **scope / options (decision needed):** lower the floor only for short landscape viewports (the figure there is height-bound, so this shrinks it — the user's rule against shrinking applies), or keep the floor and pin the play bar to the viewport bottom in that layout (overlaps the canvas bottom band).
- **status:** RESOLVED (run `phone-landscape-layout`, product `d8ad153b` + `95a56a17`) — waiting for the user's visual review (`runs/phone-landscape-layout/review.md` F-R1–F-R7). The user asked for neither option above (no lower floor everywhere, no bar pinned over the figure). Short landscape (`(orientation: landscape) and (max-height: 30rem)`): the controls become a 10rem column beside the canvas (width is the spare dimension); the canvas keeps its height, so the figure keeps its size; the view buttons sit at the top of the column; on widths ≤ 48rem the wide layout is used there (floating panels, one-line top row). 360×640 portrait: narrower button padding keeps the play buttons on one row. Measured at `221ec0a0`: 844×390, 667×375, 844×340 8/8 each, last control at y ≤ 334 px; rotation keeps step/selection/camera 40/40. The 320 px floor is kept: at 667×375 and 844×340 only the blank band under the figure falls below the fold.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** — (resolved; human review pending)
- **default_switch_blocker:** NO

### ISSUE-ARCH-LANDSCAPE-FLOATING-PANEL-COVERS-CANVAS
- **description:** In short landscape the information panels float over the canvas, as on desktop (W4). The canvas there is narrow (640 px at 844×390, 463 px at 667×375), so an opened panel (17–20rem wide) covers part of the figure — about half of the canvas at 667×375.
- **evidence:** `runs/phone-landscape-layout/images/mobile/cross-section/{landscape,landscape_small}/steps_last.png`; the probe keeps the figure in the viewport (`panels.*.figure_visible` = 1) but does not measure overlap by a floating panel.
- **impact:** the learner collapses (one tap) or drags the panel; canvas and camera do not change when it opens (W4 invariant). No wrong value.
- **scope / options (decision needed):** keep (W4 floating design); narrower panels in short landscape (less text per line); or give the panel its own column when open — the canvas would resize and the camera re-aspect on open, breaking the approved W4 invariant "opening a panel does not resize the canvas".
- **status:** OPEN (run `phone-landscape-layout`)
- **final-acceptance (2026-10-09):** the user accepts the current behaviour as temporary UX debt, to prioritise architecture work; not fixed, not a final approval — stays OPEN.
- **frontend-freeze (2026-10-09):** frontend development paused by the user to prioritise the geometry architecture and backend; this item stays OPEN/DEFERRED (not accepted as done, not PASS). Fix only if it blocks verifying geometry capability or using a core function.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** after the user decides
- **default_switch_blocker:** NO

### ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN
- **description:** On the low screen (1366×650, canvas 435 px) a 120 × 40 px drag on the triangular prism moves point labels past the canvas edge. The default view fills 68 % of the binding dimension, and an orbit can enlarge the projection beyond the remaining margin (known since w11: the playback evidence zooms out before its rotated images).
- **evidence:** `runs/mobile-canvas-fit/results/MOBILE_LAYOUT_PROBE.json` row `triangular_prism/low` `FIGURE_LEFT_CANVAS_AFTER_ORBIT`; identical before the change (`diagnostics/baseline_38a19c65/`); the other 39 family × viewport runs keep the labels inside after the same drag.
- **impact:** the learner may need «Xem lại toàn hình» or a zoom after rotating; no wrong value.
- **scope / options (decision needed):** accept (the reset button exists), or fit by the bounding sphere instead of the default projection (smaller figure on every screen).
- **status:** OPEN (run `mobile-canvas-fit`) — pre-existing, not touched. Evaluated in run `phone-landscape-layout`: one family, one viewport, one 120 × 40 px drag (55/56 other runs keep the labels inside); «Xem lại toàn hình» restores the exact initial camera in 56/56 runs over seven viewports and is always in view. The only shared fix (fit over the orbit sweep / bounding sphere) makes the figure smaller on every screen — an approved invariant — so it waits for the user.
- **final-acceptance (2026-10-09):** the user accepts it as temporary UX debt («Xem lại toàn hình» is the recovery); not fixed, not a final approval — stays OPEN.
- **frontend-freeze (2026-10-09):** frontend development paused by the user to prioritise the geometry architecture and backend; this item stays OPEN/DEFERRED (not accepted as done, not PASS). Fix only if it blocks verifying geometry capability or using a core function.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** after the user decides
- **default_switch_blocker:** NO

### ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW
- **description:** The classroom band (`daiLop`: assignment label, the teacher's «Giao cho lớp», the live-class dock or the student's indicator + help button) sits in the scene's top row. On short landscape the row is forced onto one line (`.geo3d-thanh { flex-wrap: nowrap }`, `95a56a17`) while the tool group `.geo3d-thanh-nut` may still wrap inside and the lesson title has `min-width: 0`: the band takes the width, the title shrinks to 0 px (gone), the four tool buttons stack vertically, the row grows to 148–224 px and the canvas and control column are pushed below the screen edge. In narrow portrait (360×640) the band adds one or two rows to the top row and the play bar falls below the edge.
- **evidence:** `docs/evaluation/geometry/runs/final-acceptance/results/CLASS_BAND_PROBE.json` (API stubbed, 0 model calls; teacher idle/live, student live × 8 viewports): branch `95a56a17` 11/24, `main` `38d41588` 5/24, no row passes on `main` and fails on the branch; `images/class-band__student__640x360.png`. Witness: without the band the official probe measures a 36–44 px top row and controls in view on every landscape viewport (`runs/phone-landscape-layout/results/MOBILE_LAYOUT_PROBE.json`).
- **impact:** in a class with an assignment open on a phone (landscape ≤ 667 px wide or with the browser bar, 360 px portrait; teacher during a live session also at 844×390) the learner or teacher scrolls to reach the play controls and loses the lesson title in landscape; no wrong value. Pre-existing on `main` (worse there: also horizontal scroll at 360/390 px).
- **scope / options (proposal, not measured):** in the short-landscape block keep the tool group on one line (`.geo3d-thanh-nut { flex-wrap: nowrap; flex-shrink: 0 }`), give the title a floor (`min-width: 5rem`) and let the assignment label shrink first (`.nav-assignment { flex: 0 1 auto; min-width: 0 }`); default the teacher dock to its existing collapsed state (`live-dock-thu`) at ≤ 48rem. Re-measure with the probe above plus `check-mobile-layout.mjs`.
- **status:** RESOLVED (run `classroom-band-fit`, product `45f5a7f0`) — waiting for the user's review (`runs/classroom-band-fit/review.md` H-1…H-3, C-1…C-4). The proposal above was measured as a prototype: title floor + tool group that neither shrinks nor wraps + band on a second line reached 15/24; the remaining nine cases (640×360, 844×340, 360×640 × three roles) lacked 14–103 px of height under the kept 320 px canvas floor and 44 px touch targets. User decision (2026-10-09): compact classroom chip. Shipped: `.geo3d-ten-bai` `min-width: 4rem`; `.geo3d-quay-lai` no shrink/wrap; short-landscape `.geo3d-thanh-nut` `flex: none; flex-wrap: nowrap`; `NhomLop` (disclosure next to `MenuCongCu`) keeps the band as top-row items on wide screens (`display: contents`) and folds it into one chip on tight screens — the chip carries the read-only class status (`LiveClassStrip tomTat`) and opens the full band in a dropdown anchored to the top row; ≤ 48rem with a chip ⇒ icon-only back button (`aria-label` kept); no chip without a class context. Measured at `6a1801e7` (`results/CLASS_BAND_PROBE.json`): 24/24 (baseline 9/24 with the same probe); scenes without a band 55/56 as before; Tier-A 8/8.
- **residual (tracked here, not fixed):** at 640×360 and 667×375 the chip has room only for the status dot + «…» (34–43 px): live/not live reads by colour; mode, class name and the teacher's help count need one tap (the full text stays in the accessibility tree). A student asking for help takes two taps on tight screens. User decision H-3 pending.
- **frontend-freeze (2026-10-09):** frontend development paused by the user to prioritise the geometry architecture and backend; this item stays OPEN/DEFERRED (not accepted as done, not PASS). Fix only if it blocks verifying geometry capability or using a core function.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** — (resolved; human review pending)
- **default_switch_blocker:** NO

### ISSUE-ARCH-MOBILE-HEADER-TOOLBAR-LAYOUT
- **description:** On phones the scene's top row (back button, lesson title, grouped tools) and the tool bar are functional but not visually finished: the 2 × 2 tool grid in portrait, the truncated one-line title in landscape and the spacing of the control column were shaped for fit, not designed.
- **evidence:** the user's review on 2026-10-09 (brief of run `final-acceptance`); images `runs/phone-landscape-layout/images/mobile/<family>/{portrait,landscape,landscape_small}/layout.png`.
- **impact:** appearance only; every control measured in view and usable (`runs/phone-landscape-layout/results/MOBILE_LAYOUT_PROBE.json`).
- **status:** OPEN — accepted by the user as temporary UX debt (2026-10-09) to prioritise architecture work; no redesign now; not a final approval.
- **classroom-band-fit (2026-10-09):** with a classroom chip on tight screens (≤ 48rem) the back button shows only its arrow (label kept in `aria-label`/`title`) — part of this debt, not a redesign.
- **frontend-freeze (2026-10-09):** frontend development paused by the user to prioritise the geometry architecture and backend; this item stays OPEN/DEFERRED (not accepted as done, not PASS). Fix only if it blocks verifying geometry capability or using a core function.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** a later UI design wave
- **default_switch_blocker:** NO

### ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY
- **description:** After `repo-cleanup` the remaining Informatics content sits on the measured model surface and in the live IR, both outside what a cleanup may change. (1) Prompts `app/ai/skills/{adapt,analyze,classify,edit,explain,simulate,semantic_analyze,semantic_program}.md` still describe the Informatics product; `adapt`, `edit`, `explain`, `simulate` have no loader in `app/` or `scripts/`, `semantic_analyze`/`semantic_program` serve only the `domain=None` branch of `pipeline.stage_semantic_{analyze,program}` that the product never takes (out-of-domain text fails closed first). (2) The Semantic Program IR keeps the container vocabulary (`ContainerType` array/stack/queue/matrix/map/set/tree_node/graph, container operations, visual bindings) with its interpreter, gates, the 2D `domains/semantic` renderer and their tests (`tests/semantic_program/*`, `test_cross_domain_matrix.py` + `scripts/cross_domain_matrix.py`).
- **evidence:** `backend/cache_identity.lock.json` `components.prompts` = hash of every `skills/*.md` (`runtime_identity.skill_fingerprint`); `image_extraction.SEMANTIC_PROMPT_SKILLS` keys the image cache on `semantic_analyze`/`semantic_program`; `components.synthesis_schema` hashes the IR schema; inventory of run `repo-cleanup`.
- **impact:** no wrong value; dead prompt text and IR vocabulary the geometry product never uses.
- **callers (re-read at run `docs-cleanup`, 2026-10-08):** the count above is short by two — `analyze.md` and `classify.md` have no loader either (only dated comments in `main.py` name them), so **six** prompts are unloaded: `adapt`, `analyze`, `classify`, `edit`, `explain`, `simulate`. `pipeline._call_json` (`app/ai/pipeline.py`) has no caller left. The `domain=None` branch: `pipeline.stage_semantic_analyze` (`load_skill(analyze_skill_for(domain) if domain else "semantic_analyze")`, `SEMANTIC_ANALYZE_SCHEMA`) and `stage_semantic_program` (`skill = program_skill_for(domain) if domain else "semantic_program"`, `grammar_card(domain)` full card); `domain_profile.analyze_skill_for`/`program_skill_for` map every non-geometry domain to the same two skills. Image cache key: `image_extraction.SEMANTIC_PROMPT_SKILLS` (all four semantic/geometry skills). Every `skills/*.md` is in `runtime_identity.skill_fingerprint` → `cache_identity.lock.json` `components.prompts`.
- **scope:** a model-surface wave: delete the six unloaded prompts, `_call_json` and the `domain=None` branch (plus the two `semantic_*` skills and their entry in `SEMANTIC_PROMPT_SKILLS`), prune the IR vocabulary (contract, static check, interpreter, schema export, frontend schema copy, semantic renderer), re-lock the cache identity with a `CACHE_VERSION` bump and re-measure — not a cleanup (briefs of `repo-cleanup` and `docs-cleanup`: no DSL/IR change, no live calls).
- **status:** OPEN (run `repo-cleanup`; callers re-read, nothing changed, at run `docs-cleanup`)
- **owner_class:** ARCHITECTURE
- **suggested_wave:** the next wave that changes prompts or the IR anyway
- **default_switch_blocker:** NO
- **acceptance:** no `skills/*.md` without a loader; `ContainerType` holds only what the geometry route emits; cache identity re-locked; model surface measured.
- **verify:** `git grep -n "ContainerType = Literal" backend/app/simulation/semantic_program/contract.py` · `ls backend/app/ai/skills`

### ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE
- **description:** Live shell code still carries Informatics-era pieces that need a visual/contract pass: `components/SamplePreview.tsx` maps eleven Informatics `simulation_id`s to preview glyphs; the module-contract fields `threeD` and `specDrift`. Artifact M20 và các comment chỉ trỏ tới chúng đã được dọn ở `docs-cleanup`.
- **evidence:** inventory of run `repo-cleanup` (kept items); `frontend/src/components/SamplePreview.tsx` `KIND_BY_SIM_ID`.
- **impact:** presentation/maintenance only; no wrong value.
- **scope:** a UI pass with a before/after visual check (SamplePreview glyphs, dead geo3d CSS) and a shell-contract pass (`threeD`, `specDrift`); comment edits when those files are next touched.
- **status:** PARTIALLY RESOLVED (run `docs-cleanup`, 2026-10-08) — H-W20-4 (Informatics residue in code) is otherwise closed by run `repo-cleanup`.
  - **Done.** Dead CSS: the nine classes above plus `geo3d-focus`, `geo3d-lead`, `geo3d-tree-type` (12 classes, 17 rules; no product module renders them — the first two are named only by absence tests; parser check: every kept rule identical, page unchanged). `offline-catalog.ts` comment now names the geometry samples.
  - **Kept by decision.** The comments that cite removed measurement scripts state how a value was measured at a named commit; they stay true there (git keeps the script), as `RUN_NAMING.md` rules for old evidence.
  - **Left (needs a visual check or a contract pass):** `SamplePreview.tsx` `KIND_BY_SIM_ID` (eleven Informatics ids; old history entries still render with them), the `threeD` policy (`simulations/renderer.ts`, `types.ts`) and `specDrift` (`SimulationWorkspace.tsx`). Also `frontend/scripts/demo-geometry-interaction.mjs` reads `.geo3d-tree-type`, which the product no longer renders (its `loai` field is always empty).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** the next UI wave
- **default_switch_blocker:** NO

### ISSUE-OPS-BROWSER-SESSION-PROFILE-LEAK
- **description:** `frontend/scripts/browser-runner.mjs` created a Chrome user-data profile `%TEMP%\w12-*` (~50 MB, SwiftShader caches) on every `BrowserSession.open()` and never removed it; a failure inside `open()` left the Chrome process running, and `compiler-scene-suite.openFixture` dropped the session (Chrome kept running to the end of the script) when a step after `open()` failed. One `measure.sh` run opens roughly 150 sessions.
- **evidence:** code (pre-fix `browser-runner.mjs` lines 118, 209, 132–135, 390–395; `openFixture`); reproduction `runs/browser-temp-lifecycle/diagnostics/repro-leak.mjs` (3 sessions ⇒ 3 leaked profiles); inventory `runs/browser-temp-lifecycle/results/TEMP_INVENTORY.json` (671 profiles, 33.5 GB left after the user's partial cleanup; the user reports > 1,700 before it).
- **impact:** fills drive C: (free space went from 1.54 GB to 43.32 GB after the user's partial cleanup); orphaned software-WebGL Chrome processes add load during long probe runs. No wrong value.
- **status:** RESOLVED (run `browser-temp-lifecycle`, `3cb0630a`) — sessions own `<root>/w12-XXXX/{owner.json, profile, tmp}` under `D:/tmp/algosim-browser` (`ALGOSIM_BROWSER_TMP`, `%TEMP%/algosim-browser` fallback), Chrome's own TEMP/TMP point inside the session, teardown kills only the session's process tree and removes the directory on close, failed open, reopen and process exit; a hard-killed runner's directory is removed by the next process after `laOrphan` proves the owner dead. Verified with real Chrome: sequential 5, parallel 3, startup death, in-session error, crash, `openFixture` failure, hard kill — 7/7, `%TEMP%` unchanged (`results/LIFECYCLE_VERIFICATION.json`).
- **residual:** the 671 legacy `%TEMP%\w12-*` profiles (`VERIFIED_ORPHAN`) were deleted after the user's confirmation (run `merge-readiness`, `results/TEMP_CLEANUP.json`: 671 deleted, 0 failed, 0 skipped; C: free 43.87 → 77.43 GB); 229 `%TEMP%\scoped_dir*` (1.3 GB) stay `UNKNOWN` and untouched (any Chromium creates them). Twenty standalone scripts (`certify-*`, `accept-*`, `spot-check-*`, `audit-layout`, `measure-*`, `diagnose-refusal-flake`) still create an un-removed profile per run (other prefixes; none present now) — move them to `BrowserSession` when touched.
- **owner_class:** OPERATIONS / TEST HARNESS
- **suggested_wave:** — (resolved; legacy cleanup is the user's decision)
- **default_switch_blocker:** NO
