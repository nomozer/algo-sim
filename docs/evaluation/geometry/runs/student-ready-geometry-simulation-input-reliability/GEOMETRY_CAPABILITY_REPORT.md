# GEOMETRY CAPABILITY REPORT — `student-ready-geometry-simulation-input-reliability` (`CACHE_VERSION = 145`)

- **Pipeline chính thức:** `Hybrid /4` (`local-geometry-parser/2` · `typed-fact-next/2` · `Planner /26` · `Registry /33` · `Exact Kernel /24` · `Adapter /4`)
- **Product Commit:** `ac0ea63dd462c92a8736b607764d1df552d29329` | **Clean Freeze:** `4c463d154885e99ad9bf07e3898d11c619eb63c4`
- **Measured System Hash:** `8a88dbfe9ddc35e38639c7c81e8c7741b1ea1dd1cd848bc9e7dc6bf16885b0c6` (`120` files)
- **Locked Gemini Surfaces:** `all_match = true` (`typed_fact_next = 33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14`)

---

## 1. Mở Rộng Năng Lực Hình Học Tổng Quát (Không Chạm Gemini Schema)

1. **`point_reflection` & Khai thác đối xứng qua điểm:** Hỗ trợ quan hệ đối xứng điểm chuẩn hóa qua cầu nối xác định (`typed_fact_next.py`, `typed_fact_next_bridge.py`, `registry.py`, `engine.py`, `planner.py`) mà không làm thay đổi surface trích xuất đã khóa của Gemini.
2. **Tham chiếu tiền đề `@id` & phân rã mục tiêu tổng hợp (`local_geometry_parser.py`):** Cải thiện liên kết các mệnh đề phụ thuộc chéo câu, chiếu vuông góc lên trọng tâm đáy không đặt tên điểm chân phụ, và mở rộng hỗ trợ lăng trụ/chóp đa dạng đáy.
3. **Fail-closed & Ngân sách tìm kiếm/IR (`planner.py`, `engine.py`, `height_invariance.py`):** Cắt tỉa nhánh tiền điều kiện không hợp lệ (`precondition`), bảo vệ giới hạn khai báo bộ nhớ IR (`max_memory_declarations = 32`).

---

## 2. Kết Quả `REAL27_TEXT`: Nâng Từ `18/27` → `21/27` (`0` Wrong Served)

### 2.1 Ba Ca Thăng Hạng Mới So Với Baseline `v144`
| Case ID | Phân vùng | Local Parse Status | Trạng thái | Kết quả (`q1`) | Kỳ vọng | Khớp chính xác | Continuity errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `vmmu_r254` | `frozen_external_evaluation` | `LOCAL_PARSE_COMPLETE` | `SERVED` | `9a³√13/2` | `9a³√13/2` | `true` | `0` |
| `vmmu_r277` | `frozen_external_evaluation` | `LOCAL_PARSE_COMPLETE` | `SERVED` | `8a³` | `8a³` | `true` | `0` |
| `vmmu_r488` | `development` | `LOCAL_PARSE_COMPLETE` | `SERVED` | `a³/3` | `a³/3` | `true` | `0` |

### 2.2 Hạch Toán 6 Ca Còn Lại Trên `REAL27_TEXT` (Tất Cả Từ Chối An Toàn)
| Case ID | Phân vùng | Nhóm nguyên nhân | Code / Root cause | Determinacy status | Bằng chứng đối chứng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `vmmu_r256` | `frozen_external_evaluation` | `SOURCE_GROUNDING_GAP` | `LIVE_AI_DISABLED` / `UNRECOGNIZED_GOAL` | `NOT_EVALUATED_SEMANTIC_INCOMPLETE` | Đề gốc dính lỗi chính tả `'đên'` thay vì `'đến'`; phản thực sửa `'đến'` cho `SERVED {'q1': 'a√15/5'}` khớp key |
| `vmmu_r266` | `frozen_external_evaluation` | `KERNEL_EXACT_DOMAIN_GAP` | `EXACT_DOMAIN_EXCEEDED` / `PLANNER_COMPOSITION_UNSUPPORTED` | `PROVED_DETERMINATE_EXACT_DOMAIN_EXCEEDED` | Cosin chứa căn lồng ngoài trường hữu tỉ/Gram bậc hiện hành |
| `vmmu_r461` | `development` | `INTENTIONALLY_UNSUPPORTED` | `LIVE_AI_DISABLED` / `UNRECOGNIZED_GEOMETRIC_ENTITY` | `NOT_EVALUATED_SEMANTIC_INCOMPLETE` | Hình quạt cuộn thành nón — ngoài phạm vi khối đa diện Route D |
| `vmmu_r475` | `frozen_external_evaluation` | `INTENTIONALLY_UNSUPPORTED` | `LIVE_AI_DISABLED` / `UNRECOGNIZED_GEOMETRIC_ENTITY` | `NOT_EVALUATED_SEMANTIC_INCOMPLETE` | Bài toán Ác-si-mét đa mặt cong — ngoài phạm vi Route D |
| `vmmu_r491` | `frozen_external_evaluation` | `TYPED_FACT_GAP` | `LIVE_AI_DISABLED` / `FREE_POINT_UNDERDETERMINED` | `UNPROVED_DUE_TO_CAPABILITY_GAP` | Điểm chiếu trượt `I ∈ BC` và chiều cao `AA'` chưa xác định hoàn toàn |
| `vmmu_r513` | `development` | `INSUFFICIENT_SPECIFICATION` | `MISSING_DIMENSION` / `SHAPE_FREEDOM_UNCERTIFIED` | `UNPROVED_DUE_TO_CAPABILITY_GAP` | Thiếu cạnh đáy chữ nhật `BC`/`AD`; khớp Source Gate (`LOCAL_PARSE_COMPLETE`, không bịa giả thiết) |

---

## 3. Bộ Kiểm Chứng Năng Lực, Tổ Hợp Hàm & Hồi Quy Lịch Sử

### 3.1 Tổng Hợp Các Bộ Benchmark Toán & Tổ Hợp
| Bộ kiểm chứng | Kết quả `v145` | `false_served` / `wrong` | Ghi chú chi tiết & độ trễ |
| :--- | :--- | :---: | :--- |
| `NC NL` (`21` dương) | **`21/21`** *(baseline trước đó: `4/21`)* | `0` | `p50 = 47.600 ms`, `p95 = 100.852 ms`, `provider_calls = 0` |
| `NC Gold` (`21` dương) | **`21/21`** | `0` | `p50 = 253.504 ms`, `p95 = 465.318 ms` |
| `Autonomous Negatives` (`11` âm) | **`11/11` refused** | `0` | Không phục vụ sai trên dữ kiện âm |
| `A4 Plane Constraints & Depth` (`6` ca) | **`6/6`** | `0` | `A4_nl_dir`, `A4_nl_3pt`, `A4_gold_contains_points`, `A4_neg_parallel_to_line_refused` (`INVALID_QUALIFIED_REF`), `DEPTH2_centroid_proj_served` (`2/3`), `DEPTH3_fail_closed` (`PLAN_TOO_LARGE`) |
| `r1_probe_19` (`13` dương + `6` đối kháng) | **`13/13` pos + `6/6` neg** | `0` | Cả 13 ca dương khớp oracle chính xác |
| `Reasoning Matrix 72` (`RM72`) | **`61/62` pos + `10/10` neg** | `0` | Phân loại `61` ca served: `33` `SOURCE_EXPLICIT_SEQUENCE`, `25` `REGISTERED_DECOMPOSITION`, `3` `DISCOVERED_FUNCTION_COMPOSITION`; `8` ca tái sử dụng trung gian; `p50 = 181.546 ms`, `p95 = 702.337 ms`. Ca còn lại `MG9`: từ chối an toàn `IR_MEMORY_BUDGET_EXCEEDED` (`max_memory_declarations = 32`, `33` candidates / `21` pruned so với `54 / 0` trước đó) |
| `DEV37` | **`30/37`** | `0` genuine neg | `diagram_benign = SERVED`, `sec_do_P_cat = SERVED` |
| `PROBES39` | **`23/39`** | `0` neg | Không tăng sai trên câu âm |
| `COMP112` | **`68/112`** *(v144: `66/112`)* | *Xem giải trình §3.2* | `dp_unnamed_through_point_status = SERVED`; chênh `2` nhãn âm lịch sử là thăng hạng năng lực hợp lệ |
| `historical-regression-delta` (`v3_matrix`, `0` model calls) | **`8/24` `CORRECT_COMPLETE`** trên `gold-flat-LOCKED` & `replay-flat-LOCKED` *(v144: `7/24`)* | `0` hồi quy | Sửa `h15` (`FALSE_REFUSAL_CAPABILITY_GAP` `13 -> 12`, xóa `UNSUPPORTED_MULTIPLE_BASES: 1`) trên cả 8 cell so sánh |

### 3.2 Giải Trình Minh Bạch `COMP112`: `66/112` → `68/112` (`false_served_on_negatives: 2`)
Khi đối chiếu trực tiếp hai ca làm `comp_false_served = 2` trong `evaluate_unified_campaign.py`, cả hai đều thuộc nhóm lịch sử `"group": "described_point_unsupported"` vốn được gắn nhãn `"expect": "REFUSE"` từ `v139`/`v140` trước khi hệ hỗ trợ chúng — **không phải lỗi an toàn hay bịa giả thiết**:

1. **`dp_reflection`:** *"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. Gọi E là điểm đối xứng của A qua C. Tính khoảng cách từ E đến mặt phẳng (SBC)."* → `SERVED {'q1': 'a√2/2'}`. Kiểm chứng giải tích: với $A(0,0,0), B(a,0,0), C(a,a,0), S(0,0,a)$, ta có $E = 2C - A = (2a,2a,0)$ và $(SBC): x + z = a$, nên $d(E,(SBC)) = \frac{|2a-a|}{\sqrt{2}} = \frac{a\sqrt{2}}{2}$. Phục vụ chính xác nhờ `point_reflection`.
2. **`dp_projection_unnamed_image`:** *"Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA = a và hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng với trọng tâm của tam giác ABC. Tính khoảng cách từ S đến mặt phẳng (ABC)."* → `SERVED {'q1': 'a√6/3'}`. Kiểm chứng giải tích: $R = a/\sqrt{3}$, $SH = \sqrt{SA^2 - R^2} = \sqrt{a^2 - a^2/3} = a\sqrt{6}/3$. Phục vụ chính xác nhờ hỗ trợ chân đường cao là trọng tâm chưa đặt tên.
