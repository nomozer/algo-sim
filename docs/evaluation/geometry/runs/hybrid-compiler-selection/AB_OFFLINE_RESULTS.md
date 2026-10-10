# Kết quả A/B offline, oracle độc lập, phân tích đúng ngữ nghĩa và từ chối

Run `hybrid-compiler-selection`. **0 lượt gọi model.** `MEASUREMENT_CLASS = FOUNDATION_ONLY_OFFLINE_FIXTURES` ·
`HELD_OUT_CLAIM = NO` · `EVALUATOR_INDEPENDENCE = PARTIAL`. Đầu ra "AI" của cả hai nhánh viết tay hoặc sinh cơ học, đóng vai
một mô hình trích **đúng**. Không kết quả nào ở đây là bằng chứng về Gemini.

Tái lập (từ `backend/`, `PYTHONIOENCODING=utf-8`):

```bash
.venv/Scripts/python.exe -m pytest tests/geometry/test_hybrid_compiler_selection.py -q          # 107 test
.venv/Scripts/python.exe scripts/hybrid_ab_offline.py --out-dir <tạm>                          # ab_results.json + 16 cảnh
.venv/Scripts/python.exe ../docs/evaluation/geometry/runs/hybrid-compiler-selection/diagnostics/mutation_check.py
.venv/Scripts/python.exe ../docs/evaluation/geometry/runs/hybrid-compiler-selection/diagnostics/independent_oracle_check.py
```

## 1. Bộ đối chứng

| tập | số ca | nguồn của đầu ra "AI" | kiểm cái gì |
|---|---|---|---|
| `text_to_functions_cases.json` | 27 | A: lời gọi đã commit · B: `facts_from_calls` (cơ học) | parity |
| `paraphrase_cases.json` | 23 | như trên | parity |
| `geometry_expansion_cases.json` | 8 | như trên | parity |
| `hybrid_holdout_cases.json` | 14 | A và B đều viết tay; kỳ vọng + hạng + oracle commit ở `f6b1a551`, **trước** planner | so sánh |

Yêu cầu phủ của đề bài và ca đáp ứng:

| yêu cầu | ca |
|---|---|
| diễn đạt khác nhau | 23 ca paraphrase (parity) — với B, phần diễn đạt nằm hết ở mô hình, offline **không** kiểm được |
| cặp gần giống | H04 ↔ H08 (mặt bên ⊥ đáy ↔ hai mặt bên ⊥ nhau) · H05 ↔ H06 (chiều cao ↔ một cạnh bên) · H07 ↔ H13 (BC ⊥ (SAB) là điều phải chứng minh ↔ là mệnh đề phủ định) |
| thiếu dữ kiện | H10 |
| mâu thuẫn | H09 (số) · H13 (quan hệ phủ định) |
| mặt bên ⊥ đáy | H04 |
| chân đường cao tại trung điểm / tại đỉnh | H04 (suy ra), H12 (cho sẵn) / ca SA ⊥ đáy của bộ cũ (PYR1 …) và H07, H13 |
| độ dài ký hiệu | H01, H02, H03, H07, H11, H12, H14 |
| hình chiếu | H12 |
| khoảng cách / góc | H02, H11 / H03, H12 |
| hợp thành nhiều phép dựng | H01, H02, H11 |
| hình hợp lệ nhưng không duy nhất | H05 |
| đại lượng hỏi không duy nhất | H06 |

## 2. Sáu hạng kết cục

`correct_served` (phục vụ, đáp số khớp oracle) · `wrong_served` · `correct_refusal` (đề sai/thiếu, từ chối) · `false_refusal`
(đề đủ, từ chối) · `unsupported` (đề hợp lệ, thư viện chưa có phép dựng; từ chối có mã) · `infrastructure` (lỗi provider/mạng/
parse). Hạng **kỳ vọng** của từng ca ghi trong fixture trước khi chạy. Bộ chấm: `scripts/hybrid_ab_offline.py::phan_hang`.

| tập | nhánh | correct_served | wrong_served | correct_refusal | false_refusal | unsupported | infrastructure |
|---|---|---|---|---|---|---|---|
| parity (58) | A | 27 | 0 | 31 | 0 | 0 | 0 |
| parity (58) | B | 27 | 0 | 31 | 0 | 0 | 0 |
| holdout (14) | A | 8 | 0 | 4 | 0 | 2 | 0 |
| holdout (14) | B | 8 | 0 | 4 | 0 | 2 | 0 |

Parity: trạng thái + mã trùng 58/58, đáp số trùng trên mọi ca phục vụ. Holdout: khớp kỳ vọng 14/14 ở cả hai nhánh. `VERIFIED`
(`diagnostics/ab_offline.log`, `offline/ab_results.json`). Hạng `infrastructure` = 0 vì offline không có provider. Các mã
hạ tầng của adapter (`RESPONSE_TRUNCATED`, `NO_CANDIDATE`, `JSON_INVALID`, `PROVIDER_REFUSED`) chỉ được kiểm bằng phản hồi giả.

## 3. Từng ca holdout

| ca | A | B | đáp số / ghi chú |
|---|---|---|---|
| H01 lập phương | SERVED | SERVED | V = a³, AC′ = a√3 |
| H02 hộp chữ nhật | SERVED | SERVED | V = 6a³, d(A, (A′BD)) = 6a/7 |
| H03 chóp tứ giác đều | SERVED | SERVED | V = a³√6/6, cos²(SA, đáy) = 1/4 |
| H04 mặt bên ⊥ đáy, SA = SB | SERVED | SERVED | V = 8√2/3 (chân là trung điểm AB, engine suy ra) |
| H05 hình không duy nhất | `UNDERDETERMINED_POINT` | `FIGURE_NOT_UNIQUE` | hạng `unsupported` cả hai; V = √3 duy nhất nhưng **không** lấy hình mẫu |
| H06 đại lượng không duy nhất | `UNDERDETERMINED_POINT` | `UNDERDETERMINED_POINT` | từ chối đúng |
| H07 điều phải chứng minh | SERVED | SERVED, goal f7 `HOLDS` | V = a³√3/3; A không kiểm mục tiêu |
| H08 hai mặt bên ⊥ nhau | `UNSUPPORTED_PLANE` | `UNSUPPORTED_CAPABILITY` | hạng `unsupported` |
| H09 lập phương mâu thuẫn | `INCONSISTENT_FACTS` | `INCONSISTENT_FACTS` | AC′² phải là 12, đề cho 9 |
| H10 hộp thiếu chiều cao | `MISSING_DIMENSION` | `MISSING_DIMENSION` | |
| H11 khoảng cách chéo nhau | SERVED | SERVED | 2a/3 |
| H12 hình chiếu tại trung điểm | SERVED | SERVED | V = a³/8, cos² = 1/2 |
| H13 phủ định mâu thuẫn | `NEGATED_CLAUSE` | `INCONSISTENT_FACTS`, negated f6 `HOLDS` | A từ chối vì quote có phủ định; B chứng minh mệnh đề phủ định sai |
| H14 tứ diện đều | SERVED | SERVED | V = a³√2/12 |

Cảnh A và B của 8 ca phục vụ có cùng tập điểm và cùng `chart_metric` (test `test_holdout_nhanh_B` đọc độ dài trên Scene3D).
Renderer: `veKhongGian` cho độ dài Euclid trùng metric khung trên 16/16 cảnh, 256 cặp điểm, sai số tương đối lớn nhất cỡ 5·10⁻¹⁰
(`diagnostics/renderer_metric_check.log`). `VERIFIED`.

## 4. Oracle độc lập

Ba lớp, độc lập với nhau ở mức khác nhau:

1. **Lời giải tay** trong ô `oracle` của fixture, commit ở `f6b1a551` trước khi có planner. Cùng tác giả với engine.
2. **Oracle toạ độ số thực** `diagnostics/independent_oracle_check.py`: toạ độ đặt tay, chỉ dùng `math`, **không** import
   engine/kernel/registry. Đặt hình theo cách khác engine (engine dùng khung affine + Gram hữu tỉ; oracle dùng toạ độ Descartes
   cụ thể với a = 1). Kiểm 28 đại lượng của 12 ca: thể tích, độ dài, khoảng cách, cos², tích vô hướng cho các quan hệ ⊥. Với
   H05 kiểm hai vị trí đỉnh cùng V nhưng khác SA (hình không duy nhất). Với H06 kiểm hai vị trí cùng SA = 3 nhưng khác V. Kết
   quả: `ORACLE_OK` 28/28. Chuỗi khớp: oracle toạ độ = dạng đóng trong `expect_*` = chuỗi đáp số engine (test A/B khoá bằng
   đúng chuỗi đó). H08 và H10 không có đại lượng để kiểm (ngoài năng lực / thiếu dữ kiện).
3. **Renderer** (lớp 3 của §3): kiểm cảnh đã phát, không kiểm đáp số.

`EVALUATOR_INDEPENDENCE = PARTIAL`: không có người thứ hai. Oracle custodian của kho
(`docs/evaluation/geometry/custodian/geometry_oracle.py`) không được dùng vì nó đọc Semantic Program của `LLM_ONLY`, không đọc
lời gọi hàm.

## 5. Đúng ngữ nghĩa và từ chối

**Mã từ chối B thêm, ở planner** (trước engine, test `test_planner_tu_choi_co_ma` và các test riêng):

| mã | khi nào |
|---|---|
| `SCHEMA_INVALID` | sai lược đồ, rỗng, id trùng |
| `FACT_INCOMPLETE` | thiếu ô bắt buộc theo `kind`; ký hiệu khối không đọc được |
| `AMBIGUOUS_FACT` | mô hình gắn `ambiguous = true` — planner không đoán |
| `CONDITIONAL_CLAUSE` | có dữ kiện `role = condition` |
| `AMBIGUOUS_REFERENCE` | "cạnh bên" của chóp không đều; "cạnh đáy" của đáy không đều; "cạnh" của khối không đều mọi cạnh |
| `UNKNOWN_SOLID` | dữ kiện nhắc khối không khai |
| `UNSUPPORTED_CAPABILITY` | cặp kiểu quan hệ / câu hỏi chưa có luật; mặt ⊥ mặt không phải (mặt bên, đáy) |
| `PLAN_TOO_LARGE` | quá `MAX_CALLS` = 64 lời gọi |

**Mã B thêm, sau khi dựng** (`run_fact_route`):

| mã | khi nào |
|---|---|
| `PROOF_GOAL_FALSE` | điều phải chứng minh SAI trên hình dựng từ giả thiết |
| `INCONSISTENT_FACTS` | mệnh đề phủ định lại ĐÚNG trên hình |
| `NEGATED_CLAUSE` | mệnh đề phủ định không kiểm được trên hình (mã giống A) |
| `FIGURE_NOT_UNIQUE` | đỉnh chóp chưa xác định, có chiều cao, chỉ hỏi thể tích; `details.quantity_invariant` ghi bất biến; **không** phục vụ |

**Không suy đại lượng duy nhất từ một hình mẫu.** H05 bị từ chối dù V bất biến. Tham số tự do của bố cục (khung affine + Gram,
modulo đồng dạng) khác với tham số tự do của **đề** (vị trí đỉnh). Engine chỉ chọn cái thứ nhất. `VERIFIED` (H05, H06, đột
biến m5).

**Tự rà soát tìm hai lỗi, đã sửa ở `91e2edf9`**, test đỏ trước:

1. Một mệnh đề phủ định mà checker không kiểm được (ví dụ nhắc điểm M không có trên hình) bị **phục vụ im lặng**. Hình có thể
   trái đề. Nay từ chối `NEGATED_CLAUSE`.
2. Checker coi câu hỏi và mệnh đề `unsupported` là ĐÚNG. Một mệnh đề phủ định ngoài thư viện vì thế thành `INCONSISTENT_FACTS`
   (sai lý do). Nay là `UNVERIFIABLE`.

Bằng chứng A/B tạo lại sau bản sửa trùng từng byte (không ca nào chạm hai đường này). Đột biến m9, m10 bắt hai lỗi.

**Đột biến:** 10/10 bị bắt (`diagnostics/mutation_check.log`). Các đột biến: mục tiêu dùng làm giả thiết · bỏ kiểm phủ định ·
mặt ⊥ mặt bất kỳ thành mặt bên ⊥ đáy · cạnh bên chóp không đều gán SA · bỏ chẩn đoán hình không duy nhất · bỏ từ chối điều kiện ·
bỏ mở rộng "chóp đều ⇒ đáy đều" · mục tiêu không kiểm · phủ định không kiểm được coi là sai · checker coi câu hỏi là đúng.

**Chưa kiểm (`NOT_VERIFIED`):**

- mô hình thật có gắn đúng `role`, `negated`, `ambiguous`, `measure` không — đây là nơi B dồn rủi ro;
- dữ kiện B bị bỏ sót (planner không biết điều đề có mà mô hình không trích);
- `UNVERIFIABLE` cho điều phải chứng minh: vẫn phục vụ đáp số.

## 6. Khai báo: cổng nguồn được nới cho cả hai nhánh

Ở `65fd0328`, từ khoá cổng nguồn trong `registry.py` thêm:

- `regular_polygon` chấp nhận "lập phương";
- `prism` chấp nhận "lập phương", và lăng trụ đứng cũng chấp nhận "lập phương";
- `rectangle` đổi từ "hình chữ nhật" thành "chữ nhật". "hình hộp chữ nhật" không chứa cụm "hình chữ nhật" liền nhau.

Vì sao: tiền đăng ký ghi H01, H02 phục vụ và H09, H10 từ chối vì nội dung. Với từ khoá cũ, A từ chối cả bốn ở cổng nguồn
(`PREDICATE_NOT_IN_QUOTE`) dù quote đúng. Đã thử lại bằng cách khôi phục từ khoá cũ trong bộ nhớ:
`diagnostics/old_cue_probe.log`. Đó là từ chối oan theo định nghĩa: đáy lập phương là hình vuông, đáy hộp chữ nhật là hình
chữ nhật.

Thay đổi chỉ **nới** cổng. Nó áp cho A và B như nhau, nên không làm lệch so sánh. Quote vẫn phải có trong đề; cổng tầng khác
không đổi. 27 fixture gốc và 31 ca diễn đạt + mở rộng giữ nguyên kết cục (test cũ không sửa). Rủi ro còn lại: "chữ nhật" có thể
cho phép gọi `rectangle` trên một mặt của hộp chữ nhật. Điều đó đúng về hình học, nhưng **không** có test âm riêng cho từ khoá
mới.
