# V3_PRODUCT_PATH_PARITY_CORRECTION

> 2026-09-05. **Lớp ĐÍNH CHÍNH cho lượt V3 — không phải một lượt V3 mới.**
>
> `APPLICATION_LLM_CALLS = 0` · `PHYSICAL_API_ATTEMPTS = 0` ·
> `V3_REEXECUTED = NO` · `V3_SOURCE_ARTIFACTS_CHANGED = NO` ·
> `PRODUCT_CAPABILITY_CHANGED = NO`.
>
> Giữ nguyên `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED` và
> `MEASUREMENT_CLASS = INTERNAL_ONE_SHOT_ACCEPTANCE`.

## 1. ROOT_CAUSE

Runner V3 chấm đáp số ở **sai tầng**.

```
LEGACY_RUNNER_PATH   verify_and_compile → outcome.envelope["scene3d"]
PRODUCT_POST_MODEL_PATH
                     verify_and_compile
                     → (nếu executable) pipeline._dung_scene3d
                     → env["scene3d"]
```

`route` **cố ý** không dựng `scene3d`: hướng phụ thuộc một chiều — engine
không được biết tới tầng trình bày — và `test_scene3d.py` cấm **mọi** module
dưới `app/simulation` import `scene3d`. Người ghép cảnh là `pipeline`, vốn là
**người gọi** route chứ không phải một tầng của nó.

Runner V3 dừng ở `verify_and_compile`. Nên:

```python
env = getattr(outcome, "envelope", None) or {}
canh = (env.get("scene3d") or {}).get("objects") or []   # ← LUÔN rỗng
ra["dai_luong"] = [...]                                   # ← LUÔN []
ra["dap_so_khop"] = c["mong"] <= set(ra["dai_luong"])      # ← KHÔNG BAO GIỜ True
```

`dap_so_khop` **không thể** True với bất kỳ chương trình nào, kể cả chương
trình đúng hoàn toàn. Đây là một khiếm khuyết của **phép chiếu**, không phải
một phép đo về mô hình.

⚠️ Và thẩm quyền đúng **đã có sẵn**: `acceptance_verdict.trich_ket_qua` trả
`{"nguon": "outcome.final_memory", "dai_luong": {...}}`. Scorer mà manifest V3
ghim (`4f7cae90…`) biết đọc đáp số từ đâu; runner chỉ không gọi nó — nó tự
dựng một phép chiếu thứ hai.

## 2. Hai đường, theo tầng

| tầng | legacy runner | product path |
|---|---|---|
| Contract/spec | ✅ như nhau | ✅ như nhau |
| Interpreter | ✅ (trong `verify_and_compile`) | ✅ |
| Final memory | ✅ **có, nhưng runner không đọc** | ✅ đọc qua `trich_ket_qua` |
| Postconditions | ✅ như nhau | ✅ như nhau |
| Trace | ❌ route không trả | ✅ interpreter chạy lại trong `_dung_scene3d` |
| Scene composition | ❌ **KHÔNG chạy** | ✅ `_dung_scene3d` → `build_scene3d` |
| Exact result extraction | ❌ đọc từ `scene3d` (rỗng) | ✅ đọc từ `final_memory` |

Hai phép chấm độc lập, và bản đính chính này tách chúng ra:

```
EXACT_RESULT  ← outcome.final_memory   (thẩm quyền checker)
SCENE3D_PASS  ← pipeline._dung_scene3d (bằng chứng HIỂN THỊ)
```

Scene quantity object là bằng chứng để **nhìn**, không phải thẩm quyền duy nhất
của một đáp số toán học. Gộp hai thứ là lý do V3 báo `0/9`.

## 3. Replay

Worktree tách biệt tại `85b584c`, đo lại measured-system:

```
a696200e8f8c668c82a1675eab09b4e1845e3c499edaf90c95790f108fe244c2   89 file
```

— đúng candidate V3. Candidate hiện tại (`93c47d9a…`) nằm **ngoài** phép replay.

Mọi hàm `stage_semantic_analyze`, `stage_semantic_program`, `call_gemini`
(cả `pipeline` lẫn `gemini`) bị thay bằng guard **ném**. `provider_guard_trips
= 0` — không đường nào chạm tới model.

Băm artifact nguồn, đo từ file thật:

| | |
|---|---|
| `curved_acceptance.json` | `70d47a9542561209ce5f4f0d50184e638866eca27f49f8594eb6b6e4e05a49b5` |
| `stage_8a_one_shot.json` | `f3439fb6db1d568b3ac2723ad52b6a58358bc9786012dffdff4a0fc4122f53bb` |
| `manifest.json` | `b2a454f0b285c5f1061798a52dc367efcba5ebb3d0a4f30da6eb0e38776c146a` |
| `attribution.json` | `280a3fe1290305b5c21deea4c035bf0a423ce280cc975a9c34839df411d85610` |

## 4. `c7a` — chương trình ĐÚNG bị chấm sai

Đề: *"Cho hình nón đỉnh T, tâm đáy H, bán kính đáy bằng 5 và chiều cao TH = 12.
Tính độ dài đường sinh, thể tích khối nón và diện tích xung quanh."*

| | |
|---|---|
| kỳ vọng | `13` · `100π` · `65π` |
| `final_memory` | `l = 13` · `V = 100π` · `Sxq = 65π` |
| legacy `dai_luong` | `[]` |
| product scene quantities | `["13", "100π", "65π"]` — **3 đối tượng** |
| exact match (final_memory) | **True** |
| Scene3D | **True** |

Mô hình dựng đúng: `H(0,0,0)` · `T(0,0,12)` · `A(5,0,0)` ⇒ `r = 5`, `h = 12`,
`l = 13`. **Cả ba đáp số đúng tuyệt đối.**

### Nhưng nó vẫn KHÔNG servable — và đó là lỗi HỆ

```
stage_reached     postconditions
executable        True
servable          False
error_code        postcondition_violated
failure_category  verification_gap
constraints       distance(hinh_non) · volume(hinh_non) · lateral_area(hinh_non)
```

Nghĩa vụ `distance` gắn vào một `curved_solid` (đường sinh) **không chứng thực
được** — cùng hình dạng với `duong_4_he_hut_verification` của certifier
(`angle` trên `vector3`). Nên:

```
C7A_CORRECTED_VERDICT = SYSTEM_VERIFICATION_FAILURE
```

**không** phải `CORRECT_EXECUTABLE_IR`, và **không** phải
`MODEL_COMPOSITION_FAILURE` như báo cáo gốc.

### ⚠️ Hai bộ phân lớp lệch nhau, và điều đó được ghi ra

| | `c7a` |
|---|---|
| `run_curved_acceptance.phan_lop` (7 lớp, bộ đã sinh số gốc) | `CORRECT_EXECUTABLE_IR` |
| `acceptance_verdict.phan_loai` (13 lớp, **manifest V3 ghim** `4f7cae90…`) | `SYSTEM_VERIFICATION_FAILURE` |

Không phải nhiễu: `phan_lop` **không đọc `servable`**, nên nó mù với
`verification_gap`. Lấy scorer đã ghim làm thẩm quyền; ghi cả hai để người đọc
sau thấy chỗ lệch thay vì phải tự phát hiện lại.

## 5. Replay đối chứng cả 13 ca

| ca | org exec | replay exec | legacy q | scene q | exact | scene3d | đổi |
|---|---|---|---|---|---|---|---|
| c1a · c2b · c3b · c4b · c5b · c6b · c8b · c9b | False | False | 0 | 0 | False | False | — |
| **c7a** | True | True | **0** | **3** | **True** | **True** | ✅ |
| n1a · n2b · n3a · n4b | False | False | 0 | 0 | — | — | — |

**Đúng một ca đổi.** Mọi lỗi schema, grounding và coverage tái hiện y nguyên —
chúng đo ở tầng route và không phụ thuộc phép chiếu cảnh.

## 6. Bảng đính chính

| chỉ số | báo cáo gốc | đính chính | lý do |
|---|---:|---:|---|
| Executable positive | 1/9 | **1/9** | `ORIGINAL_METRIC_CONFIRMED` |
| Exact-answer match | 0/9 | **1/9** | phép chiếu luôn rỗng ⇒ số gốc không diễn giải được |
| Scene3D pass | 0/9 | **1/9** | runner không chạy scene composition |
| Servable | 0/9 | **0/9** | `ORIGINAL_METRIC_CONFIRMED` — c7a chết ở verification gap |
| Negative honest refusal | 4/4 | **4/4** | `ORIGINAL_METRIC_CONFIRMED` |
| MODEL failure (rubric) | 5 | **4** | c7a rời cột mô hình |
| SYSTEM failure (rubric) | 2 | **3** | +1 = c7a (`verification_gap`) |
| `ATTRIBUTION_UNRESOLVED` | 2 | **2** | `ORIGINAL_METRIC_CONFIRMED` |
| **General acceptance** | FAIL | **FAIL** | không đổi |

⚠️ Hai cột "MODEL/SYSTEM failure" phải so **cùng thước**. Báo cáo gốc §7 dùng
bảng attribution (rubric `d44f2b7c…`); cột `phan_lop` trong artifact là bộ 7 lớp
của runner (MODEL 7 → 6). Trộn hai cái cho ra một "đính chính" *tăng* số lỗi mô
hình — ngược hẳn sự thật. Artifact ghi riêng cả hai thước.

## 7. Phạm vi hiệu lực

```
V3_GENERATION_EVIDENCE_VALID   YES   analyze/synthesis đo ở tầng route, không
                                     đụng phép chiếu cảnh
V3_GROUNDING_EVIDENCE_VALID    YES   6 ca chết ở grounding, tái hiện y nguyên
V3_EXACT_SCORING_VALID         NO    đo một phép chiếu luôn rỗng
V3_SCENE3D_SCORING_VALID       NO    runner chưa từng chạy scene composition
V3_OVERALL_THRESHOLD_VERDICT   FAIL  (không đổi)
```

**Kết luận trung tâm của báo cáo V3 vẫn đứng vững**, và lý do thì mạnh hơn chứ
không yếu đi: nút thắt là **CONSTRUCTION-GROUNDING** — 6/9 ca chưa bao giờ tới
được tầng chấm đáp số. Bản đính chính không đụng vào phần ấy.

Nhưng nó đổi **một câu quan trọng**: báo cáo gốc viết *"c7a: executable nhưng
`dai_luong` rỗng — lỗi soạn chương trình"*. Câu ấy **sai**. Chương trình đúng
trọn vẹn; thứ hỏng là bộ đo, và phần còn lại là một lỗ chứng thực của hệ.

## 8. Identity

```
CURRENT_PRODUCT_CODE_CHANGED    NO
CURRENT_CANDIDATE_HASH_CHANGED  NO   (93c47d9a4ff9ffd2… giữ nguyên)
CACHE_VERSION_CHANGED           NO   (79)
V3_POOL_CHANGED                 NO   (36c2153ecefd2dbf…)
V3_SEAL_CHANGED                 NO   (seed 5324284654432805119 · case_set eb1c402a…)
V3_SOURCE_ARTIFACTS_CHANGED     NO   (4/4 băm khớp)
V3_REEXECUTED                   NO
PRODUCT_CAPABILITY_CHANGED      NO
```

Băm bộ đo hiện tại **đổi** vì wave này thêm test + docs: đó là `scripts/` và
`tests/`, ngoài `MEASURED_SYSTEM_PATHS`, nên candidate không đụng.

## 9. Gates

| | |
|---|---|
| `tests/test_v3_product_path_parity.py` (MỚI) | **21 passed** |
| replay tất định × 2 | artifact **byte-stable** (bỏ `do_luc`) |
| full backend pytest | **3597 passed** · 1 skipped · 1 deselected (1 đỏ là cổng "cây sạch", xanh sau commit) |
| candidate verification hiện tại | exit **0** — 89 file, `93c47d9a…` |
| measured-system trong worktree cũ | `a696200e…` ✅ |
| tiêm lỗi băm nguồn | **ĐỎ** đúng 2 test, xanh lại sau khôi phục |
| provider guard | **0 lần chạm** |
| `git diff --check` | exit **0** |

## 10. Giới hạn

**①** Bản đính chính **không** làm V3 thành một phép đo độc lập. `OPERATOR_WAIVED`
giữ nguyên.

**②** `c7a` là ca **duy nhất** đi tới tầng scene composition, nên phép so parity
chỉ có một điểm dữ liệu. Nếu nhiều ca hơn đã executable thì sai lệch còn lớn hơn.

**③** Lỗ chứng thực `distance(curved_solid)` **chưa sửa** — nó nằm ngoài phạm vi
wave này và cần một quyết định riêng.

**④** Runner V3 vẫn chưa được nối lại vào đường sản phẩm đầy đủ. Bản đính chính
sửa **con số**, không sửa **bộ đo**. Lượt đo sau phải chạy qua đường sản phẩm,
nếu không nó sẽ lặp lại đúng lỗi này.

## 11. RECOMMENDED_NEXT_ACTION

```
ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT
```

Không phải `CURVED_OBLIGATION_SURFACE_ALIGNMENT`. Nhánh ấy đúng khi *"parity
issue chỉ ảnh hưởng phép chiếu kết quả/Scene3D"* — và về **số** thì đúng thế,
một ca. Nhưng về **cấu trúc** thì không: runner bỏ qua cả một tầng sản phẩm
(`_dung_scene3d` + trace), và nó sẽ bỏ qua tầng ấy cho **mọi** ca của **mọi**
lượt sau. Hôm nay chỉ một ca chịu ảnh hưởng vì chỉ một ca executable; khi nền
dựng khối cong bắt đầu cho nhiều ca chạy được — đúng thứ wave trước vừa mở —
thì con số sai sẽ thành nhiều ca.

Sửa bộ đo trước, rồi mới tới `CURVED_OBLIGATION_SURFACE_ALIGNMENT`.
