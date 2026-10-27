# review.md — Independent review, `hybrid-v2-planner-premerge-review`

- **Marks:** `INDEPENDENT_CODE_REVIEW` · `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` ·
  `LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`.
- **Reviewer:** a read-only subagent in a separate context (conversation `5fa9d4f1-72dd-4bf2-a1af-b1b91c94ad1d`). It did
  not write any of the reviewed code. It read the code, ran its own offline probes (about 90 `run_fact_route` cases) and
  targeted pytest. It changed no file and made no provider call.
- **Lead reviewer (this run):** also read the code directly (see §3). It did not rely on the predecessor's report.

## 1. Deltas reviewed

| Delta | Content | Verdict |
|---|---|---|
| `70ba1577..de7b2813` | Planner `/16` (`_mat_vuong_duong`: prism anchors); registry `/15` (`_TU_KHOI`, `_cum_goi_khoi`) | PASS_WITH_FINDINGS (the findings are the kind-only gap below) |
| `81b545a2..0a5ec06f` | Registry `/16` Source Gate fix (`_loai_cum_dung`, `_GOI_NGUON`) | PASS_WITH_FINDINGS (I-1 open for the Owner, I-2 fixed, MINOR 1/3 fixed) |
| `0a5ec06f..37e84352` | Remediation: per-run reset of `_GOI_NGUON`; "tứ diện đều" also requires `regular_pyramid` | **INDEPENDENT_REVIEW_PASS** |

## 2. Findings

### BLOCKER

None.

### IMPORTANT

1. **I-1 — OPEN, needs an Owner decision: a correct solid symbol outranks a contradicting kind word.**
   - Code: `registry._khoi_khop` (no kind check when `sym` is present) and the symbol branch of `_cum_goi_khoi`.
   - The policy was pinned on purpose by `test_hybrid_ask_operand_binding.py::test_solid_symbol_outranks_the_solid_word`
     (run `hybrid-semantic-hardening`).
   - Reproduced on both candidates. All of these are still served:
     - `"thiết diện của hình lập phương ABC.A'B'C'"` and `"hình chóp ABC.A'B'C'"` for the right triangular prism;
     - `"hình lập phương ABCD.A'B'C'D'"` for the 6 × 8 × 12 box.
   - The served solid is unambiguous, but the source contradicts itself. Registry `/16` makes this inconsistent: the same
     kind word written without the symbol is refused.
   - This run did NOT change it, because doing so reverses a pinned earlier decision. It is pinned as
     `test_solid_kind_source_binding.py::test_correct_symbol_with_contradicting_kind_word_is_still_served`
     (`xfail(strict=True)`), so changing it later cannot happen silently.
2. **I-2 — FIXED (`d7ed5832`):** the GREEN evidence `results/green-after.json` was untracked. It is now committed.

### MINOR

1. **M-1 — FIXED (`37e84352`):** `_GOI_NGUON` was never reset, so a specific kind could be "verified" with the calls of a
   previous request. `kiem_nguon` is now a wrapper that sets the context with a token and resets it in `finally`.
   - Test: after a served run the context is `()`.
   - No live leak existed: no post-gate consumer reads it (`engine.py` ~L1838 handles `ask_distance_lines` only).
2. **M-2 — documented, not fixed:** "xiên" and "ngũ giác" can be written in `_khoi_cum` / `_KHOI_NGU` only through the
   "cắt … theo" branch.
   - "lăng trụ xiên" is therefore refused: a conservative false refusal, outside the registered wording.
   - "xiên" is defined as `right == False`. That is a flag, not a geometric fact. If the wording is widened later, a
     geometrically right prism without the flag would pass.
3. **M-3 — FIXED (`37e84352`):** "tứ diện đều" now also requires `k.fn == "regular_pyramid"`. Before, the definition quote
   alone was checked.
4. **M-4 — documented:** "hộp" is narrower than geometry. A parallelogram- or rhombus-based prism that the source does not
   call a box is refused (conservative).
5. **M-5 — informational:** the planner's spanning argument assumes no three collinear base vertices. A degenerate input
   fails closed in `engine._plane` / `Plane3.through`.
6. **M-6 — informational, pre-existing:** `_KHOI_MO_TA` is set at gate entry and never reset. Its default lookups return
   `"?"` (refuse), so it cannot serve a wrong answer.

## 3. Planner `/16` — correctness argument (checked by both reviewers)

- **Layers:** `tang = [base, [apex]]` for a pyramid and `[base, top]` for a prism, cuboid or cube.
- **Anchors:**
  - If `d` lies inside one layer: a vertex of that layer off `d`, plus the first vertex of the other layer.
  - Otherwise (`d` joins the layers): the first two base vertices off `d`.
- **Why `d ∪ {Z1, Z2}` spans space:**
  - **`d` in a layer:** `d` and the extra vertex span that layer's plane, and the other-layer vertex is off it.
  - **`d` joins the layers:** `d` has exactly one base endpoint. That endpoint and the two other base vertices span the
    base plane (three distinct vertices of a polygon), and the other endpoint of `d` is off the base.
- **No metric used:** the argument holds for oblique prisms unchanged.
- **Pyramid anchors are byte-for-byte the `/15` choice:**
  - `d` in the base gives `[first base vertex off d, apex]`;
  - the apex in `d` gives the first two base vertices off `d`.
- **No coordinates, no computed values, no fixture IDs.** Producers are keyed `(solid, M, "perpendicular_line", {d})`, so
  the section goal and the area goal share one construction.
- **Engine re-checks** (`engine.py` ~L1451–1506):
  - Gram ⊥ of both directions;
  - independence (`_plane([p, x1, x2])` raises on collinear points);
  - equality with `plane_through_point_perpendicular_to`;
  - refusal of a face plane.
- **Corpus:** 10/10 positives agree exactly with the independent rational edge-clipping oracle (`tools/oracle.py`, no
  product imports), on both candidates.

## 4. Adapter `/4`

- Untouched: `git diff --stat 70ba1577 99faf026 -- backend/app/ai/adapter4_route.py` is empty.
- Plane-only derived sections are still refused with `PREVIEW_RESULT_INVALID`, because no `DINH_CAT_CANH` certificate
  exists for them. Pinned by `test_canonical_v2_existing_schema_serves_same_section_and_adapter4_fails_closed`.
- This is `ADAPTER_INTEGRATION_GAP` and is NOT an E2E Hybrid PASS.
