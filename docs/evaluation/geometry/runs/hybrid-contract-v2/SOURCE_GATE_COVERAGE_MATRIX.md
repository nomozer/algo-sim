# SOURCE_GATE_COVERAGE_MATRIX.md — Unified Source Authority (`D2`) & Closed Grammar (`D3`, `G1`–`G7`)

- **Run**: `hybrid-contract-v2` (Backend Hybrid Session 3)
- **Authorization**: `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH` (`D2 GO-conditional`, `D3 GO`, `D6 GO-limited`)
- **Locked Corpus**: `docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json`
- **Lock File**: `docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.lock.json`
- **Lock Commit**: `4268f4e214125fe20c858930bc92b0c5798dfc67` (committed before any grammar code change)
- **Locked SHA-256**: `10c57be7b485d7b3f1a97183ff41b28988e70641e297e01cccf68d1434cc4abe` (`47` cases)

---

## 1. Before vs After Closed Grammar Expansion (`G1`–`G7`)

| Metric | Before Grammar (`baseline-before-grammar.json`) | Mid-Session Claude Snapshot (before limit) | Final Session 3 (`after-p4b-grammar.json`) |
|---|---:|---:|---:|
| Locked cases (`grammar-set.json`) | `47` | `47` | `47` |
| Positive cases (`expect: SERVE`) | `10 / 22` (`45.5%`) | `19 / 22` (`86.4%`) | **`22 / 22` (`100.0%`)** |
| `REFUSE_GEOMETRY` | `4 / 4` | `4 / 4` | **`4 / 4` (`100.0%`)** |
| `REFUSE_KERNEL` | `2 / 2` | `2 / 2` | **`2 / 2` (`100.0%`)** |
| `REFUSE_SOURCE` | `18 / 19` (`+1 REFUSE_OTHER`) | `17 / 19` | **`18 / 19` (`+1 REFUSE_OTHER`)*** |
| Binary Serve vs Refuse Accuracy | `35 / 47` (`74.5%`) | `44 / 47` (`93.6%`) | **`47 / 47` (`100.0%`)** |
| Exact Category Match (`match`) | `34 / 47` | `42 / 47` | **`46 / 47` (`97.9%`)** |
| `wrong_served` (oracle mismatch or invalid served) | `0` (`[]`) | `0` (`[]`) | **`0` (`[]`)** |
| `served_without_gate` (`authority != "registry.kiem_nguon"`) | `0` (`[]`) | `0` (`[]`) | **`0` (`[]`)** |

*\*Note on the single category difference (`46/47` match): `NEG-per-edge-same-name` (`"cắt SB tại N, cắt SC tại N"`) is refused even earlier at the `typed-fact-next/2` Pydantic schema boundary (`DerivedPlaneSectionSpecV2._validate_section_v2`) with `INVALID_DERIVED_SECTION` (`REFUSE_OTHER`), pinned by `test_v2_section_shape_is_closed`.*

---

## 2. Closed Grammar Extensions (`G1`–`G7`) & Security Invariants

| Gate ID | Grammatical Construction Admitted | Implementation Location | Positive / Paraphrase Cases | Adversarial / Negative Controls Refused |
|---|---|---|---|---|
| **G1** | Per-edge named cut list: `"cắt (cạnh) SB tại (điểm) N, (và) (cắt (cạnh)) SC tại (điểm) P"` | `registry.py`: `_cum_cat_canh` | `PARA-5`, `POS-per-edge-with-va-cat` | `NEG-per-edge-same-name` (`INVALID_DERIVED_SECTION`), `NEG-swapped-names` (`SOURCE_OBJECT_MISMATCH`), `NEG-stated-edge-not-in-text` (`SOURCE_OBJECT_MISMATCH`) |
| **G2** | Restated plane subject after `;` or `,`: `"... song song với (ABC); (α) cắt ..."` / `", (α) cắt ..."` | `registry.py`: `_cum_cat_canh`, `_CHU_NGU_CAT` | `PARA-2`, `PARA-3` | `NEG-other-plane-subject` (`"(β) cắt ..."` when plane is `(α)` $\to$ `SOURCE_OBJECT_MISMATCH`) |
| **G3** | Through-point synonym: `"chứa (điểm) M"` for a single 1-letter point token | `registry.py`: `_QUA_CHUA` (`(?P<diem>{_P1})(?![\w'])`) | `PARA-4` | `NEG-contains-a-line` (`"chứa SA"` $\to$ `SOURCE_OBJECT_MISMATCH`) |
| **G4** | Point-first plane definition: `"Qua M dựng mặt phẳng (α) song song với ... / vuông góc với ..."` | `registry.py`: `_DIEM_TRUOC_SONG_SONG`, `_DIEM_TRUOC_VUONG_DUONG` | `PARA-3` | `NEG-point-first-wrong-reference` (`SOURCE_OBJECT_MISMATCH`) |
| **G5** | Described derived pyramid in volume ratio / residual: `"khối/hình chóp (đỉnh) S (được) cắt (ra)/tạo bởi (mặt phẳng/mp) (α)"` | `registry.py`: `_KHOI_MO_TA`, `_khoi_ro_cum`, `_sym_khoi` | `D6-ABC-cut-SB-only`, `D6-ABCD-cut-SB-SC-only`, `D6-ABC-cut-none-stated`, `CORPUS-DEV01`, `CORPUS-DEV02`, `CORPUS-DEV03` | `NEG-ratio-unowned-anonymous`, `NEG-residual-unowned`, `NEG-ratio-swapped-operands`, `NEG-residual-swapped-operands`, `CORPUS-DEV01-ratio-unowned`, `CORPUS-DEV02-ratio-unowned`, `CORPUS-DEV03-ratio-unowned` |
| **G6** | Multi-item construction lead-in: `"Dựng từng bước hình chóp, thiết diện bởi (α), khối chóp đỉnh S cắt bởi (α), làm nổi bật thiết diện"` & general triangle base `"Đáy ABC là tam giác có AB = ..., BC = ..., AC = ..."` | `registry.py`: `_C_DAY_TG_THUONG`, `_C_MP_CHUA_SS`, `_C_TRUNG_DIEM`, `_C_CHIA_DOAN`, `_DUNG_THIET_DIEN`, `_HOI_DT_THIET_DIEN`, `_kiem_du_kien_cau_hoi` | `CORPUS-DEV01`, `CORPUS-DEV02`, `CORPUS-DEV03`, `CORPUS-DEV09-construct`, `CORPUS-DEV10-prism-area` | `NEG-unread-extra-constraint`, `NEG-negated-parallel`, `NEG-conditional-section`, `NEG-wrong-number-in-premise`, `NEG-quote-not-in-text` |
| **G7** | Redundant stated through-point cut: `"cắt SA, SB, SC, SD lần lượt tại M, N, P, Q"` where `M` is already the through-point on `SA` | `planner.py`: `_dinh_cat_canh` (`reuse_through_point` cost 0 + `stated_point`); `registry.py`: `_kiem_dinh_cat` | `PARA-0`, `PARA-1`, `PARA-2`, `PARA-3`, `PARA-4`, `PARA-5`, `POS-per-edge-with-va-cat` | `NEG-through-point-renamed` (`"cắt SA, SB, SC lần lượt tại K, N, P"` when `M` is on `SA` $\to$ `AMBIGUOUS_REFERENCE`) |

---

## 3. Resolution of the 3 Mid-Session Non-SERVE Cases (`19/22` $\to$ `22/22`)

At the checkpoint immediately before Claude hit the session limit (`match: 42`, `SERVE: 19/22`), three positive cases in `grammar-set.json` were still failing:
1. **`PARA-3` (`QUESTION_CONTEXT_UNSUPPORTED`)**:
   - **Root Cause**: `"Qua M dựng mặt phẳng (α) song song với (ABC), (α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q."` starts with `"Qua M dựng..."`. In `registry._kiem_du_kien_cau_hoi`, `first` matched `"dựng"` at offset `6` inside the already-covered construction span `(0, 44)` (`phep_dung_spans`), splitting the sentence into `(0, 6)` and `(6, 93)`. Because `cover(a, b)` checked `a <= x < y <= b` instead of partial overlap `max(a, x) < min(b, y)`, `(0, 6)` (`"Qua M "`) was treated as an uncovered question segment.
   - **Fix**: Updated `cover(a, b)` in `_kiem_du_kien_cau_hoi` (`registry.py:2206`) to check `max(a, x) < min(b, y)`.
2. **`CORPUS-DEV09-construct` (`SOURCE_PREMISE_UNREAD`)**:
   - **Root Cause**: `"Gọi P là điểm trên cạnh BB' sao cho BP = BB'/3."` uses `"điểm trên cạnh BB'"` (whereas `_C_CHIA_DOAN` only matched `"thuộc (cạnh)"`) and fractional slash notation `"BP = BB'/3"` (whereas `_C_CHIA_DOAN` only matched prefix ratio `"1/3 BB'"`). Additionally, `"Dựng thiết diện của hình chóp S.ABC cắt bởi mặt phẳng (α)."` without `"từng bước"` was not matched by `_DUNG_THIET_DIEN`.
   - **Fix**: Extended `_C_CHIA_DOAN` (`registry.py:1302–1311`) to admit `(?:thuộc|trên|nằm\s+trên)` and `BP = BB'/q` (`1/q` when segment starts at `B`), and made `"từng bước"` optional in `_DUNG_THIET_DIEN`.
3. **`CORPUS-DEV10-prism-area` (`SECTION_PLANE_NOT_COMPILED`)**:
   - **Root Cause**: In `engine.py`, `self.calls` is sorted lexicographically by `c.fn`, where `"ask_section_area" < "section"`. In `_bien_dich_mat_cat` (`engine.py:1444`), iterating `self.of("section", "ask_section_area")` visited `g_area` (`ask_section_area`) before `sp` (`section`), naming the section plane `mp_td_g_area` instead of `mp_td_sp` and causing `chay_sau_cau_noi` to fail looking up `mp_td_sp`.
   - **Fix**: Changed `engine.py:1444` to `for c in (*self.of("section"), *self.of("ask_section_area")):` (matching `kiem_mat_cat` at line 1266), ensuring `section` always owns `mp_td_<section_id>`.

---

## 4. Complete 47-Case Locked Evaluation Matrix (`after-p4b-grammar.json`)

| Category | Case IDs | Expected | Observed | Exact Oracle / Refusal Verification |
|---|---|---|---|---|
| **Paraphrases (`G1`–`G4`, `G7`)** | `PARA-0`, `PARA-1`, `PARA-2`, `PARA-3`, `PARA-4`, `PARA-5`, `POS-per-edge-with-va-cat` (`7` cases) | `SERVE` | `7/7 SERVE` | `g_ratio = 1/64`, `g_res = 49/576` (`100%` exact match) |
| **Stated Cut Baseline** | `BASE-ABC-stated-2`, `BASE-ABCD-stated-3`, `BASE-ABCD-perp-stated-3` (`3` cases) | `SERVE` | `3/3 SERVE` | Exact `g_ratio` & `g_res` match |
| **Bounded Unstated Cut Derivation (`D6`, `G5`)** | `D6-ABC-cut-SB-only`, `D6-ABCD-cut-SB-SC-only`, `D6-ABC-cut-none-stated`, `D6-ABCD-perp-cut-none-stated`, `D6-ABC-cut-SB-unnamed`, `D6-declared-boundary-complete`, `D6-declared-boundary-reversed` (`7` cases) | `SERVE` | `7/7 SERVE` | Exact `g_ratio` & `g_res` match; internal `I, I1` labels stripped from `Scene3D` |
| **Re-authored Adapter `/3` Dev Corpus Positives (`G5`, `G6`)** | `CORPUS-DEV01`, `CORPUS-DEV02`, `CORPUS-DEV03`, `CORPUS-DEV09-construct`, `CORPUS-DEV10-prism-area` (`5` cases) | `SERVE` | `5/5 SERVE` | `DEV01`: `1/64, 49/192, 3/256`; `DEV02`: `1/729, 64/243, 1/81`; `DEV03`: `1/64, 49/64, 9/16`; `DEV10`: `3/16` |
| **Source Gate Negative Controls** | `NEG-through-point-renamed`, `NEG-swapped-names`, `NEG-per-edge-same-name`*, `NEG-other-plane-subject`, `NEG-contains-a-line`, `NEG-point-first-wrong-reference`, `NEG-stated-edge-not-in-text`, `NEG-unread-extra-constraint`, `NEG-negated-parallel`, `NEG-conditional-section`, `NEG-wrong-number-in-premise`, `NEG-quote-not-in-text`, `NEG-ratio-unowned-anonymous`, `NEG-residual-unowned`, `NEG-ratio-swapped-operands`, `NEG-residual-swapped-operands`, `CORPUS-DEV01-ratio-unowned`, `CORPUS-DEV02-ratio-unowned`, `CORPUS-DEV03-ratio-unowned` (`19` cases) | `REFUSE_SOURCE` | `18/19 REFUSE_SOURCE` + `1/19 REFUSE_OTHER`* | `19/19` refused (`0` false serves) |
| **Geometry Boundary Negative Controls** | `GEO-declared-boundary-incomplete`, `GEO-declared-boundary-crossed`, `GEO-declared-boundary-wrong-edge`, `GEO-missing-height` (`4` cases) | `REFUSE_GEOMETRY` | `4/4 REFUSE_GEOMETRY` | `SECTION_BOUNDARY_INCOMPLETE` (`3`), `UNDERDETERMINED_SOLID` (`1`) |
| **Kernel Degeneracy / Disconnected Negative Controls** | `KERN-degenerate-plane-contains-apex`, `KERN-corpus-dev04-nonexistent-intersection` (`2` cases) | `REFUSE_KERNEL` | `2/2 REFUSE_KERNEL` | `DEGENERATE_CONFIGURATION` (`1`), `LINE_PARALLEL_TO_PLANE` (`1`) |
