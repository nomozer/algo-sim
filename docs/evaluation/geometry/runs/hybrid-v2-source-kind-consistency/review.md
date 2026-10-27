# review.md — Independent Review, `hybrid-v2-source-kind-consistency`

- **Marks:** `INDEPENDENT_CODE_REVIEW` · `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` · `LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`.
- **Reviewer:** a read-only subagent in an isolated context (conversation `fade27d4-582f-474f-a80e-dc4cb618f1d2`). It did not author any of the reviewed code, tests, or evaluation artifacts. It audited the full `9b5697be..71029809` commit range (`18` changed files + surrounding context in `registry.py`), changed no file, and made `0` live provider calls.

## 1. Deltas Reviewed

| Delta | Content | Verdict |
|---|---|---|
| `9b5697be..ff48db2a` | Registry `/17` (`SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`, reversing `I-1`): symbol+kind consistency across `_khoi_khop`, `_cum_goi_khoi`, `_doc_phep_dung_cau_hoi`, `_mat_hai_duong_dung_nguon`, `mat_cat_dung_nguon`, `_khoi_ro_cum`, `_ten_khoi_khop`, `_ds_khoi_khop`, `ask_volume_ratio`, `ask_residual_volume`; test & fixture migration | **INDEPENDENT_REVIEW_PASS** |
| `ff48db2a..71029809` | GREEN receipts (`124/124`, `31/31`, `10/10` + `8/8`), candidate freeze (`4581886f`), `candidate_divergence.json` (`71029809`) | **INDEPENDENT_REVIEW_PASS** |

## 2. Verification of the 8 `I-1` Exemption Sites in `registry.py`

1. **`_khoi_khop` (`registry.py:2741`)**:
   - Removed `and not sym and not tu`. Whenever a kind capture group `m[n + "k"]` is matched in `ask_volume`, `ask_section_area`, or `_CUM_DUNG_THIET_DIEN` (`_khoi_thiet_dien`), `_loai_cum_dung(m.string[m.start(n + "k"):m.end()], solid)` is enforced regardless of whether `sym` or `tu` is also present.
2. **`_cum_goi_khoi` (`registry.py:3552`)**:
   - Replaced the early symbol-only return with `return all(set(x) == set(solid) and (".", x.find(".")) == (solid_dot, solid.find(".")) for x in ky) and _loai_cum_dung(cum, solid, calls)`. Both symbol identity and kind compatibility must hold in `mat_song_song_dung_nguon` (`registry.py:3614, 3633`).
3. **`_doc_phep_dung_cau_hoi` (`registry.py:3418`)**:
   - Added `and _cum_goi_khoi(m[0], c.args.solid, calls)` when accepting `_CAT_BOI[3]` question spans.
4. **`_mat_hai_duong_dung_nguon` (`registry.py:4023`)**:
   - Added `or not _cum_goi_khoi(m[0], c.args.solid, calls)` alongside the `symbols != {c.args.solid}` check.
5. **`mat_cat_dung_nguon` (`registry.py:4054`)**:
   - Added `and _cum_goi_khoi(m[0], c.args.solid, calls)` on `_CAT_BOI` matches.
6. **`_khoi_ro_cum`, `_ten_khoi_khop`, `_ds_khoi_khop`, `ask_volume_ratio`, `ask_residual_volume` (`registry.py:2832, 2862–2864, 2888–2905, 2959–2991`)**:
   - Captured optional kind phrase before symbol (`(?P<{n}k>...)` in `_khoi_ro_cum` and `(?P<hk>...)` in `ask_volume_ratio`) and enforced `if kw and not _loai_cum_dung(kw, solid): return False` in `_ten_khoi_khop` and `_ds_khoi_khop`.
7. **`_GOI_NGUON` ContextVar Lifecycle (`registry.py:1960–1967`)**:
   - `kiem_nguon` sets `token = _GOI_NGUON.set(tuple(calls))` before `_kiem_nguon` and resets it in `finally: _GOI_NGUON.reset(token)`. Every symbol+kind check executes within this dynamic scope and resets cleanly to `()` on exit.
8. **Architecture & Safety Invariants**:
   - Zero hardcoded case IDs, vertex labels, or expected answers in product code.
   - `REGISTRY_VERSION = "geometry-functions/17"`; `PLANNER_VERSION = "geometry-fact-planner/16"`, `ENGINE_VERSION = "geometry-function-engine/14"`, `Adapter /2`, `/3`, `/4`, `CACHE_VERSION = 130` (`NO_BUMP`), and `DEFAULT_MODE = LLM_ONLY` are unchanged.

## 3. Findings by Severity

### BLOCKER
- None (`0`).

### MAJOR
- None (`0`).

### MINOR (Non-Blocking Adjacent Coverage Observations Outside Historical `I-1` Exemption Sites)
1. **`MINOR-1` — Unchecked `của (?:hình|khối) ...` tail in `_SAU_HOP_LE` (`registry.py:3125`) and bare-`V` volume ask (`registry.py:2912`)**:
   - `_SAU_HOP_LE` (used by `_vung_hoi` at `registry.py:1894` to validate the suffix after an asked object phrase) contains `r"|của\s+(?:hình|khối)\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện)(?:\s+(?-i:[A-Z][0-9]*'?)+(?:\.(?-i:[A-Z][0-9]*'?)+)?)?"`. When an asked phrase ends before `"của hình/khối <loại> <ký hiệu>"` (such as bare `V` in `_CUM_HOI["ask_volume"][1]`, anaphoric `"thiết diện đó"`, or `ask_area`/`ask_length`), `_SAU_HOP_LE` consumes the trailing suffix without calling `_loai_cum_dung`. Standard `"Tính thể tích V của khối ..."` matches `_CUM_HOI["ask_volume"][0]` and is checked by `_khoi_khop`.
2. **`MINOR-2` — `_CUM_DUNG_THIET_DIEN_PHU` / `_MO_KHOI_DUNG` span masking in `_doc_phep_dung_cau_hoi` (`registry.py:3420–3423, 3967–3976`)**:
   - Auxiliary section spans matched by `_CUM_DUNG_THIET_DIEN_PHU` and the optional lead-in `_MO_KHOI_DUNG` do not call `_cum_goi_khoi` during span masking. When the construction sentence is quoted by `sec`/`q` (standard planner path), `mat_song_song_dung_nguon` (`registry.py:3614, 3633`) still checks `_cum_goi_khoi` on `_DAN_THIET_DIEN` and refuses contradictions.
3. **`MINOR-3` — `"hình chóp|khối chóp"` in `_DANH_TU_TRUNG_TINH` (`registry.py:2388, 2540–2543`)**:
   - `_DANH_TU_TRUNG_TINH` lists `hình chóp|khối chóp` as neutral object nouns in `_TEN_DOI_TUONG` during premise coverage masking rather than role/kind nouns checked by `_vai_tro_doi_tuong_khop`.

### NIT
1. **`NIT-1` — Shared plural kind header in `ask_volume_ratio` (`registry.py:2967–2968`) and `_ds_khoi_khop` (`registry.py:2888–2904`)**:
   - In `ask_volume_ratio`, `m.groupdict().get("xk") or m.groupdict().get("hk")` checks `xk` in preference to `hk`; in `_ds_khoi_khop`, a plural quantifier before the first item attaches `kw` to the first item only if the second item has no explicit kind word of its own.

## 4. Assessment of `I-1` Closure & Final Verdict

- **`I-1` (`solid_symbol_outranks_the_solid_word`) Status:** **CLOSED** under Owner decision `SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`. All `6/6` previously failing cases on the 124-case adversarial suite (`118/124 -> 124/124`) and all `15/15` previously failing cases on the 31-case symbol+kind suite (`16/31 -> 31/31`) now fail closed with `SOURCE_OBJECT_MISMATCH`, with `0` false refusals and `10/10` + `8/8` preserved on the development regression corpus.
- **Final Verdict:** **`INDEPENDENT_REVIEW_PASS`** (`PASS`).
