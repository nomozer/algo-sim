# report.md — `hybrid-v2-source-kind-consistency`

**Task:** `HYBRID_V2_SOURCE_GATE_I1_CONSISTENCY_HARDENING` (`OWNER GO — SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`, 2026-10-27).

**Marks:** `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_CODE_REVIEW` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` · `LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`.

**Where:** branch `research/hybrid-v2-planner-generalization`, worktree `.superpowers/worktrees/planner-generalization`.
No merge, no push, no worktree cleanup. `0` live provider calls (`ALLOW_LIVE_AI = 0`). `DEFAULT_MODE = LLM_ONLY`. Hybrid remains opt-in only. Planner `/16`, Engine `/14`, and Adapter `/4` untouched.

## 1. Baseline and Owner Decision

- **Baseline before wave:** doc commit `9b5697be`, candidate `99faf026bdcbcaa2f32e07a9f1687416a820dffd`, product `37e8435213303f54f37a19b6ce85f896fc0631a0` (`registry /16`).
- **Owner Decision (`SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`):** reverses the historical `solid_symbol_outranks_the_solid_word` policy (`I-1`, originally pinned in `hybrid-semantic-hardening`). Whenever an explicit solid-kind phrase (`_TU_KHOI` / `_TU_LOAI`) is written alongside a solid symbol (`sym` / `tu` / `ky`), **both** the symbol identity **and** the solid-kind phrase (`_loai_cum_dung`) must be true of the grounded solid.
- **Policy amendment record:** [`decision-amendment.md`](decision-amendment.md).

## 2. RED Baseline on `99faf026` (`registry /16`)

1. **124-case adversarial suite** (`../hybrid-v2-planner-premerge-review/tools/adversarial.py`, recorded in [`results/red-124-before.json`](results/red-124-before.json)):
   - `118/124` agree, **`6` `fail_open`**, `0` `false_refusal`.
   - All 6 `fail_open` rows are symbol-bearing contradictions:
     - `prism|both|hình lập phương ABC.A'B'C'`
     - `prism|area-only|hình lập phương ABC.A'B'C'`
     - `prism|sec-only|hình lập phương ABC.A'B'C'`
     - `prism|both|hình chóp ABC.A'B'C'`
     - `prism|reversed-facts|hình lập phương ABC.A'B'C'`
     - `cuboid-not-cube|both|hình lập phương ABCD.A'B'C'D'`
2. **31-case symbol+kind supplementary suite** ([`tools/symbol_cases.py`](tools/symbol_cases.py), recorded in [`results/red-symbol-before.json`](results/red-symbol-before.json)):
   - `16/31` agree, **`15` `fail_open`**, `0` `false_refusal`.
   - Covers compatible generic/specific kinds with symbols, contradictory kinds with symbols across triangular prisms, oblique prisms, rectangular cuboids, a `4×4×4` cuboid without a cube premise, pyramids (`S.ABC`, `S.ABCD`), volume questions, and two-solid disambiguation.

## 3. Fix (`registry /17`, product `ff48db2a`)

- **`REGISTRY_VERSION = "geometry-functions/17"`** (`backend/app/simulation/geometry_functions/registry.py`):
  1. `_khoi_khop` (`L2741`): removed `and not sym and not tu` so `_loai_cum_dung(m.string[m.start(n + "k"):m.end()], solid)` runs whenever `m[n + "k"]` is matched (`ask_volume`, `ask_section_area`, `_CUM_DUNG_THIET_DIEN`).
  2. `_cum_goi_khoi` (`L3552`): requires both symbol match (`ky`) and `_loai_cum_dung(cum, solid, calls)`.
  3. `_doc_phep_dung_cau_hoi` (`L3418`), `_mat_hai_duong_dung_nguon` (`L4023`), and `mat_cat_dung_nguon` (`L4054`): require `_cum_goi_khoi(m[0], c.args.solid, calls)` on matched `_CAT_BOI` phrases.
  4. `_khoi_ro_cum` (`L2832`), `_ten_khoi_khop` (`L2862–2864`), `_ds_khoi_khop` (`L2888–2905`), `ask_volume_ratio` (`L2959–2978`), and `ask_residual_volume` (`L2981–2991`): capture optional kind phrase before symbol (`(?P<{n}k>...)` and `(?P<hk>...)`) and verify `_loai_cum_dung(kw, solid)`.
- **Test & fixture migrations:**
  - `backend/tests/geometry/test_hybrid_ask_operand_binding.py`: migrated `test_solid_symbol_outranks_the_solid_word` to assert `SOURCE_CONTRADICTION_MUST_FAIL_CLOSED` (plus positive control) and updated `MUTANTS[4]` to target `/17`.
  - `backend/tests/geometry/test_geometry_library_expansion.py`: updated `test_projection_waits_for_right_prism_top` to pass `kind="hình lập phương"` matching its `Cho hình lập phương ABCD.EFGH` source text.
  - `backend/tests/geometry/test_solid_kind_source_binding.py`: removed `@pytest.mark.xfail(strict=True)`, converted to `test_correct_symbol_with_contradicting_kind_word_is_refused` (6 cases), added `test_symbol_and_kind_consistency_suite` (31 cases), and added `test_volume_ratio_and_residual_volume_reject_contradictory_kind_with_correct_symbol`.

## 4. Before / After (`99faf026` vs `71029809`)

| Measure | `99faf026` (`registry /16`, RED) | `71029809` (`registry /17`, GREEN) |
|---|---|---|
| 124-case adversarial suite (`adversarial.py`) | `118/124` agree (`6` `fail_open`, `0` `false_refusal`) | **`124/124` agree (`0` `fail_open`, `0` `false_refusal`)** ([`results/green-124-after.json`](results/green-124-after.json)) |
| 31-case symbol+kind suite (`symbol_cases.py`) | `16/31` agree (`15` `fail_open`, `0` `false_refusal`) | **`31/31` agree (`0` `fail_open`, `0` `false_refusal`)** ([`results/green-symbol-after.json`](results/green-symbol-after.json)) |
| Development positives served / exact oracle agreement | `10/10` · `10/10` | **`10/10` · `10/10`** ([`results/development-regression-registry17.json`](results/development-regression-registry17.json)) |
| Development negatives refused with registered code | `8/8` | **`8/8`** |
| Wrong-served across corpus + adversarial + symbol suites | `6` (124-suite) + `15` (31-suite) | **`0`** |

## 5. Test Tiers, Candidate Freeze, and Authoritative Full T3

| Gate | Result |
|---|---|
| T0 `node frontend/scripts/impact.mjs --base 9b5697be --dry` | `IMPACT_GATE` (`18` changed files → `src/code-index-sync.test.ts` + `PYTEST`) |
| T1 targeted & geometry/semantic suites | `429 passed` (targeted geometry/source-binding/version pins) + `52 passed` (`test_thesis_acceptance_matrix.py`) + `12,382 passed` in Full T3 |
| T2 `npx vitest run` (`frontend/`) | `83` test files, `1,417 passed` (`8.57s`) |
| Freeze (`4581886f`) | Product `ff48db2a0c3f4424fc91c313a9bfaee8e3646bc1`, `118` files, `tree_hash = 31bb915d3550e58ca9985afa607c0664f480acacdcb223b82451cc06d649f8b8` |
| Divergence (`71029809`) | [`candidate_divergence.json`](candidate_divergence.json) (`corrects` `hybrid-v2-planner-premerge-review/candidate_divergence.json`, `CACHE_VERSION = 130` `NO_BUMP`) |
| **Full T3** (clean detached checkout `71029809` in `premerge-red`) | **`FULL_PRODUCT_GATE_PASS`**: `12,382 passed, 1 skipped, 2 deselected, 15 xfailed, 1 warning in 495.98s`; frontend `83 files / 1,417 passed`; build PASS; post-T3 freeze `MATCH` (`118 file, 31bb915d3550e58c…`, [`full-t3/receipt.json`](full-t3/receipt.json)) |

Note on `xfail` count: backend `xfail` decreased from `18` (`registry /16`) back to `15` (`registry /17`) because the 3 `xfail(strict=True)` symbol+kind contradiction pins in `test_solid_kind_source_binding.py` are now strict passes (expanded to 6 + 31 + 2 = 39 new passing assertions).

## 6. Independent Review (`review.md`)

Audited by independent read-only subagent `fade27d4-582f-474f-a80e-dc4cb618f1d2` ([`review.md`](review.md)):
- **`BLOCKER`**: `0`.
- **`MAJOR`**: `0`.
- **`MINOR`**: `3` non-blocking adjacent coverage observations outside the historical `I-1` exemption sites (`_SAU_HOP_LE` suffix tail on bare-`V`/anaphoric asks, `_CUM_DUNG_THIET_DIEN_PHU` / `_MO_KHOI_DUNG` unquoted span masking, `"hình chóp|khối chóp"` in `_DANH_TU_TRUNG_TINH`).
- **`NIT`**: `1` (`xk`/`hk` precedence and plural header attachment in `_ds_khoi_khop`).
- **`I-1` Status**: **CLOSED**.
- **Verdict**: **`INDEPENDENT_REVIEW_PASS`**.

## 7. Remaining Open Items & Honesty Boundaries

- **`ADAPTER_INTEGRATION_GAP` (`/4` plane-only derived sections)**: unchanged by authorization. Adapter `/4` continues to fail closed with `PREVIEW_RESULT_INVALID` on plane-only derived sections (`test_canonical_v2_existing_schema_serves_same_section_and_adapter4_fails_closed`).
- **Adjacent vocabulary & suffix boundaries**: documented in `review.md` (`MINOR-1..3` from this wave and `M-2`, `M-4` from `hybrid-v2-planner-premerge-review`).
- **Evaluation scope**: `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` · `LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`. `0` live provider calls.

## 8. Status

`READY_FOR_OWNER_GO_MAIN_REVIEW` — see [`handoff.md`](handoff.md).
