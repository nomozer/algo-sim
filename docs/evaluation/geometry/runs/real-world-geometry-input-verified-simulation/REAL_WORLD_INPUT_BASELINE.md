# REAL_WORLD_INPUT_BASELINE — Phân Tích Pháp Y Đầu Vào Thực Tế, Chẩn Đoán 27/27 Ảnh & Cổng Nguồn (`§4.1`, `§6.2`, `§6.3`)

- **Run ID:** `real-world-geometry-input-verified-simulation`
- **Điểm neo trước chiến dịch (`start_head`):** `ce280140bf89ad72e8724993f75f98edcce01e55` (`unified-geometry-understanding-ocr-autonomous-planning`, `CACHE_VERSION = "143"`)
- **Đích đo sau can thiệp:** Candidate đóng băng sạch `003104fd5a116f38f05fe200d013b7e9ba93a05a` (`product_commit = b806e359fcceb268c065013d5cf7fb2ff278f1c1`, `measured_system = e1c6428ed558a722442e0f32b362fb41d053795a81cf92a4c267d48e2bbd7a04`, `CACHE_VERSION = "144"`)
- **Chính sách đo:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `0` lời gọi Gemini/Vision trả phí, `0` hàng `H-1` / `W2` / `W3` niêm phong được mở.

---

## 1. Tóm Tắt Ngưỡng Nền Trước Can Thiệp (`ce280140b`)

1. **`REAL27` (`27` ảnh chụp `anvo25/vmmu`: `6` `development`, `19` `frozen_external_evaluation`, `2` `fresh_external_evaluation`):**
   - Trước can thiệp: `0 / 27` `LOCAL_OCR_ACCEPT` (`27 / 27` `LOCAL_OCR_REVIEW_REQUIRED`), `median CER = 0.0944`, **`81`** `blocking_uncertain_spans` (`34` `SAME_FAMILY_AGREEMENT_ONLY`, `17` `MATH_TOKEN_DISAGREEMENT`, `7` `PRIME_DISAGREEMENT`, `7` `FRACTION_STRUCTURE_LOSS`, `6` `NOT_IN_LEXICON`, `3` `DEGREE_SYMBOL_DISAGREEMENT`, `3` `AMBIGUOUS_DIACRITIC_RESTORATION`, `2` `RADICAL_DISAGREEMENT`, `1` `RELATION_SYMBOL_DISAGREEMENT`, `1` `SINGLE_READER_TOKEN`).
   - Sau can thiệp (`local-ocr-worker/4` + `layout-aware-ocr-reconcile/3`): `median CER = 0.0533` (**`-43.5%`**, `mean = 0.0624`), tổng blocking spans **`44`** (**`-45.7%`**), `27 / 27` vẫn chủ động giữ ở `LOCAL_OCR_REVIEW_REQUIRED` (`false_auto_accepts = 0`), phục vụ sau xác nhận span tối thiểu tăng lên **`13 / 27`** (`0` wrong served).
2. **`External15` (`15` ảnh in ngoài) & `1` ảnh viết tay tách riêng (`ext_hw_b1_01_hd_a_6043187`):**
   - Trước can thiệp: `1` `LOCAL_OCR_ACCEPT` (`ext_prt_01`), `12` `LOCAL_OCR_REVIEW_REQUIRED`, `2` `needs_selection`, `median CER = 0.0333`, `4 / 12` `confirmed_served`, `0 / 6` dải chọn nhiều bài.
   - Sau can thiệp: `median CER = 0.0319`, `1` `LOCAL_OCR_ACCEPT` + **`8 / 12`** `confirmed_served_correct` (= **`9 / 15`** ảnh đơn phục vụ `Scene3D`, `0` wrong), cộng **`2 / 6`** dải `needs_selection` phục vụ đúng (`ext_prt_03 #1, #2`).
3. **Tuyển Văn Bản `REAL27_TEXT` & Cổng Nguồn:** `18 / 27` `SERVED` (`0` wrong-served), `9 / 27` `REFUSED`; `vmmu_r513` hết kẹt `503 LIVE_AI_DISABLED` và đồng bộ `LOCAL_PARSE_COMPLETE -> REFUSED MISSING_DIMENSION` (`determinacy_audit = UNPROVED_DUE_TO_CAPABILITY_GAP`).

---

## 2. Phân Loại Nguyên Nhân Review Ảnh Theo `§4.1` (Không Đánh Đồng Mọi Review Là Lỗi OCR)

### 2.1 Tổng hợp xô phân loại (`diagnostic_4_1_buckets`)

| Xô nguyên nhân (`diagnostic_bucket`) | `REAL27` (27 ảnh) | `External15` in (15 ảnh) | Ý nghĩa kỹ thuật |
|---|---:|---:|---|
| `AUTO_ACCEPTED_SAFE` | 0 | 1 | Đủ 2 họ engine + kiểm tra hình vẽ, không còn span chặn (`ext_prt_01`). |
| `MULTI_PROBLEM_NEEDS_SELECTION` | 0 | 2 | Ảnh chứa nhiều bài độc lập, mở chọn dải đúng luật (`ext_prt_03`, `ext_prt_08`). |
| `INSUFFICIENT_ACCEPTANCE_EVIDENCE_TEXT_ACCURATE` | 0 | 1 | Bản OCR đã chính xác (`CER <= 0.01`, đủ dữ kiện), chỉ thiếu đồng thuận họ thứ 2 (`ext_prt_12`). |
| `GENUINE_DIAGRAM_OR_AMBIGUITY_CONFIRMATION` | 7 | 4 | Chữ đọc tốt nhưng đề có hình vẽ tham chiếu/mất cấu trúc phân số cần học sinh xác nhận. |
| `RECOGNITION_ERROR_NEEDS_CONFIRMATION` | 20 | 7 | Có sai lệch nhận diện ký tự/ký hiệu toán thực sự cần học sinh kiểm tra/sửa. |

### 2.2 Bảng chẩn đoán đầy đủ `REAL27` (`27 / 27` ảnh — 10 câu hỏi `§4.1`)

> Quy ước cột gọn trong bảng: **Q1** chọn vùng đúng (`crop` nếu cắt); **Q2** đủ chữ sạch (`CER<=0.01`); **Q3** lỗi ký hiệu toán thiếu (`ref-tp`); **Q4** lỗi dòng/thứ tự/phân số; **Q5** lỗi dấu phẩy/mũ/độ; **Q6** bất đồng giữa các engine (`reason:count`); **Q7** số ký hiệu xác nhận qua `glyph_topology`; **Q8** crop nhòe / thiếu sáng; **Q9** lý do review; **Q10** điều kiện chặn khi chữ đã gần chuẩn (`CER<=0.03`).

| # | Case ID | Phân vùng | CER (trước → sau) | Blocking | Q1..Q5 (`Vùng/Đủ/LỗiToán/Dòng/PhẩyĐộ`) | Q6 (Bất đồng) | Q7 (`Topo`) | Q8 (`Nhòe/Tối`) | Q9 (Lý do Review) | Q10 (Chặn dù chữ sạch) | Xô phân loại (`§4.1`) | Sau xác nhận span (`Fallback`) |
|---:|---|---|---:|---:|---|---|---:|---|---|---|---|---|
| 1 | `vmmu_r247` | `frozen` | 0.0405→0.0116 | 4 | `T/F/2/F/T` | `PRIME:2, MATH:2` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | `UNCERTAIN, DIAGRAM` | `GENUINE_DIAGRAM_AMBIG` | **`SERVED` (0 edit, 5 act, 18 obj)** |
| 2 | `vmmu_r254` | `frozen` | 0.2117→0.0859 | 3 | `F/F/5/T/F` | `LEX:2, RADICAL:1` | 1 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED LIVE_AI_DISABLED` (`fb: REFUSED`) |
| 3 | `vmmu_r256` | `frozen` | 0.2258→0.1567 | 5 | `F/F/1/T/T` | `SAME_FAM:3, DEG:1, REL:1` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED LIVE_AI_DISABLED` (`fb: REFUSED`) |
| 4 | `vmmu_r258` | `frozen` | 0.1010→0.0556 | 0 | `F/F/3/T/F` | `∅` | 1 | `0 / F` | `DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: SERVED Mode A`) |
| 5 | `vmmu_r266` | `frozen` | 0.0483→0.0414 | 1 | `T/F/6/F/F` | `MATH:1` | 1 | `0 / F` | `UNCERTAIN` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: REFUSED`) |
| 6 | `vmmu_r270` | `dev` | 0.1013→0.0549 | 0 | `T(crop)/F/4/T/F` | `∅` | 0 | `0 / F` | `DIAGRAM` | — | `RECOGNITION_ERR` | **`SERVED` (0 edit, 1 act, 13 obj)** |
| 7 | `vmmu_r273` | `frozen` | 0.0944→0.0611 | 1 | `F/F/4/T/F` | `SAME_FAM:1` | 1 | `0 / F` | `UNCERTAIN` | — | `RECOGNITION_ERR` | **`SERVED` (0 edit, 1 act, 10 obj)** |
| 8 | `vmmu_r277` | `frozen` | 0.0216→0.0172 | 1 | `T/F/2/T/F` | `MATH:1` | 1 | `0 / F` | `UNCERTAIN` | `MATH:1` | `GENUINE_DIAGRAM_AMBIG` | `REFUSED` (`fb: REFUSED`) |
| 9 | `vmmu_r284` | `dev` | 0.1514→0.1633 | 6 | `T/F/4/T/F` | `MATH:2, SGL:1, DIA:1, LEX:2` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: SERVED`) |
| 10 | `vmmu_r295` | `frozen` | 0.0486→0.0378 | 0 | `T(crop)/F/2/F/F` | `∅` | 1 | `0 / F` | `DIAGRAM` | — | `RECOGNITION_ERR` | **`SERVED` (0 edit, 1 act, 18 obj)** |
| 11 | `vmmu_r298` | `frozen` | 0.0947→0.0535 | 1 | `T/F/1/T/T` | `DEG:1` | 0 | `1 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | **`SERVED` (0 edit, 2 act, 13 obj)** |
| 12 | `vmmu_r375` | `frozen` | 0.0489→0.0489 | 0 | `F/F/5/F/F` | `∅` | 0 | `0 / F` | `DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: SERVED`) |
| 13 | `vmmu_r460` | `frozen` | 0.1268→0.1174 | 2 | `F/F/3/T/F` | `SAME_FAM:2` | 0 | `0 / F` | `UNCERTAIN` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: SERVED`) |
| 14 | `vmmu_r461` | `dev` | 0.0186→0.0186 | 2 | `F/F/4/F/F` | `SAME_FAM:2` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | `SAME_FAM:2, DIAGRAM` | `GENUINE_DIAGRAM_AMBIG` | `REFUSED` (`fb: REFUSED`) |
| 15 | `vmmu_r463` | `frozen` | 0.0909→0.1010 | 2 | `T(crop)/F/9/T/T` | `MATH:1, DEG:1` | 0 | `0 / F` | `UNCERTAIN` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: SERVED`) |
| 16 | `vmmu_r475` | `frozen` | 0.0922→0.0533 | 1 | `T/F/1/T/F` | `DIA:1` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: REFUSED`) |
| 17 | `vmmu_r476` | `dev` | 0.0260→0.0260 | 0 | `F/F/5/F/F` | `∅` | 1 | `0 / F` | `DIAGRAM` | `DIAGRAM` | `GENUINE_DIAGRAM_AMBIG` | **`SERVED` (0 edit, 1 act, 14 obj)** |
| 18 | `vmmu_r488` | `dev` | 0.1292→0.1042 | 2 | `T(crop)/F/1/T/T` | `MATH:1, PRIME:1` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: REFUSED`) |
| 19 | `vmmu_r491` | `frozen` | 0.1078→0.1190 | 1 | `T(crop)/F/0/T/F` | `SAME_FAM:1` | 1 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `REFUSED` (`fb: REFUSED`) |
| 20 | `vmmu_r492` | `frozen` | 0.0183→0.0183 | 2 | `F/F/4/F/T` | `RADICAL:1, PRIME:1` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | `RAD:1, PRIME:1, DIAG` | `GENUINE_DIAGRAM_AMBIG` | **`SERVED` (0 edit, 3 act, 15 obj)** |
| 21 | `vmmu_r498` | `frozen` | 0.1061→0.0726 | 3 | `F/F/2/T/F` | `MATH:1, RADICAL:1, LEX:1` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | **`SERVED Mode A` (2 ed, 4 act, 18 obj)** |
| 22 | `vmmu_r513` | `dev` | 0.0933→0.0400 | 1 | `F/F/0/T/F` | `MATH:1` | 2 | `0 / F` | `UNCERTAIN` | — | `RECOGNITION_ERR` | `REFUSED MISSING_DIMENSION` (`fb: REFUSED`) |
| 23 | `vmmu_r520` | `frozen` | 0.0160→0.0213 | 1 | `T/F/4/F/F` | `SAME_FAM:1` | 0 | `0 / F` | `UNCERTAIN, DIAGRAM` | `SAME_FAM:1, DIAG` | `GENUINE_DIAGRAM_AMBIG` | **`SERVED` (0 edit, 2 act, 12 obj)** |
| 24 | `vmmu_r537` | `frozen` | 0.1111→0.0404 | 2 | `T/F/0/T/F` | `SAME_FAM:2` | 2 | `0 / F` | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | **`SERVED` (0 edit, 3 act, 14 obj)** |
| 25 | `vmmu_r538` | `frozen` | 0.0983→0.1040 | 2 | `T/F/7/T/F` | `SAME_FAM:1, FRAC:1` | 0 | `0 / F` | `UNCERTAIN, LAYOUT, DIAG` | — | `RECOGNITION_ERR` | **`SERVED` (0 edit, 3 act, 13 obj)** |
| 26 | `vmmu_r559` | `fresh` | 0.1929→0.0214 | 1 | `T/F/0/T/T` | `PRIME:1` | 1 | `0 / F` | `UNCERTAIN` | `PRIME:1` | `GENUINE_DIAGRAM_AMBIG` | **`SERVED Mode A` (0 edit, 1 act, 10 obj)** |
| 27 | `vmmu_r695` | `fresh` | 0.0406→0.0406 | 0 | `T/F/3/T/F` | `∅` | 2 | `0 / F` | `DIAGRAM` | — | `RECOGNITION_ERR` | **`SERVED` (0 edit, 1 act, 13 obj)** |

### 2.3 Bảng chẩn đoán đầy đủ `External15` ảnh in (`15 / 15` ảnh — 10 câu hỏi `§4.1`)

> Riêng `1` ảnh viết tay (`ext_hw_b1_01_hd_a_6043187`) được tách riêng hoàn toàn khỏi bảng ảnh in (`external16_handwritten_diagnostic`: `cer_after = 2.1228`, `needs_confirmation`, `24` actions, `16` chars, span-only `REFUSED`, `whole_draft_fallback_served = 1`).

| # | Image ID | Trạng thái (`prepare`) | CER (trước → sau) | Blocking | Q1..Q5 | Q6 (Bất đồng chính) | Q7 (`Topo`) | Q8 (`Nhòe`) | Q9 (Lý do Review/Selection) | Q10 | Xô phân loại (`§4.1`) | Kết quả cuối (`Auto` / `Conf` / `Sel`) |
|---:|---|---|---:|---:|---|---|---:|---|---|---|---|---|
| 1 | `ext_prt_01_hd_q_5259753` | `ready` | 0.0000→0.0000 | 0 | `T/T/0/F/F` | `∅` | 0 | 0 | `AUTO_ACCEPTED` | — | `AUTO_ACCEPTED_SAFE` | **`AUTO SERVED_CORRECT`** (`a³√3/3, a√21/21`) |
| 2 | `ext_prt_02_hd_q_7922924` | `needs_conf` | 0.0241→0.0361 | 1 | `T/F/7/F/T` | `PRIME:1` | 1 | 0 | `UNCERTAIN` | — | `RECOGNITION_ERR` | **`CONF SERVED`** (`6`, 0 ed, 1 act, 14 obj) |
| 3 | `ext_prt_03_hd_q_7907931` | `needs_sel` | 0.0734→`band` | 12 | `F(c=2)/F/0/T/F` | `SAME_FAM:4, MATH:5, REL:2, RAD:1` | 0 | 1 | `MULTI_PROBLEM_SEL` | — | `MULTI_PROBLEM_SEL` | **`SEL 2/2 SERVED`** (`#1 a√2/2` 0 ed; `#2 a³/4` 1 ed) |
| 4 | `ext_prt_04_hd_q_8436784` | `needs_conf` | 0.0075→0.0075 | 2 | `T/T/0/T/F` | `MATH:1, FRAC:1` | 0 | 0 | `UNCERTAIN, LAYOUT` | `MATH:1, FRAC:1` | `GENUINE_DIAGRAM_AMBIG` | **`CONF SERVED`** (`1/2`, 0 ed, 2 act, 24 obj) |
| 5 | `ext_prt_05_hd_q_7451806` | `needs_conf` | 0.0153→0.0153 | 12 | `T/F/1/T/F` | `SAME_FAM:8, MATH:3, FRAC:1` | 0 | 0 | `UNCERTAIN, LAYOUT` | `SAME:8, MATH:3, FRAC:1` | `GENUINE_DIAGRAM_AMBIG` | **`CONF SERVED`** (`6/5`, 1 ed, 12 act, 21 obj) |
| 6 | `ext_prt_06_hd_q_1084979` | `needs_conf` | 0.0067→0.0034 | 10 | `T/T/1/F/T` | `PRIME:5, SAME_FAM:5` | 0 | 10 | `UNCERTAIN` | `PRIME:5, SAME:5` | `GENUINE_DIAGRAM_AMBIG` | **`CONF SERVED`** (`a√15/5, a³√15/4`, 1 ed, 10 act, 19 obj) |
| 7 | `ext_prt_07_hd_q_7958052` | `needs_conf` | 0.0738→0.0738 | 10 | `T/F/0/F/T` | `MATH:4, SAME:2, DIA:1, PRIME:1, SGL_M:1, DEG:1` | 0 | 0 | `UNCERTAIN` | — | `RECOGNITION_ERR` | **`CONF SERVED`** (`4,7`, 4 ed, 10 act, 15 obj) |
| 8 | `ext_prt_08_hd_q_7509702` | `needs_sel` | 0.4845→`band` | 16 | `F(c=4)/F/0/F/T` | `MATH:7, SAME:4, DIA:3, MW:1, PRIME:1` | 0 | 0 | `MULTI_PROBLEM_SEL` | — | `MULTI_PROBLEM_SEL` | `SEL 0/4 SERVED` (`REFUSED` an toàn cả 4 dải) |
| 9 | `ext_prt_09_vmmu_page_r4` | `needs_conf` | 0.0333→0.0333 | 2 | `F/F/8/F/F` | `SAME_FAM:2` | 0 | 0 | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | **`CONF SERVED`** (`2`, 0 ed, 3 act, 10 obj) |
| 10 | `ext_prt_10_vmmu_page_r7` | `needs_conf` | 0.0319→0.0319 | 4 | `T/F/1/T/F` | `SAME_FAM:2, MATH:1, DIA:1` | 3 | 0 | `UNCERTAIN` | — | `RECOGNITION_ERR` | `CONF REFUSED` (`LIVE_AI_DISABLED`, 1 ed) |
| 11 | `ext_prt_11_vmmu_page_r10` | `needs_conf` | 0.0337→0.0506 | 1 | `T/F/6/F/F` | `SAME_FAM:1` | 0 | 0 | `UNCERTAIN` | — | `RECOGNITION_ERR` | **`CONF SERVED`** (`30°`, 0 ed, 1 act, 15 obj) |
| 12 | `ext_prt_12_vmmu_page_r11` | `needs_conf` | 0.0048→0.0000 | 1 | `T/T/0/F/F` | `SAME_FAM:1` | 1 | 0 | `UNCERTAIN` | `SAME_FAM:1` | `INSUFF_EVID_TEXT_OK` | **`CONF SERVED`** (`2√3`, 0 ed, 1 act, 14 obj) |
| 13 | `ext_prt_13_vmmu_page_r25` | `needs_conf` | 0.0492→0.0426 | 3 | `T/F/2/F/F` | `DIA:2, SAME_FAM:1` | 0 | 0 | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `CONF REFUSED` (`LIVE_AI_DISABLED`, 1 ed) |
| 14 | `ext_prt_14_vmmu_page_r26` | `needs_conf` | 0.0548→0.0259 | 1 | `T/F/8/F/F` | `DIA:1` | 1 | 0 | `UNCERTAIN, DIAGRAM` | `DIA:1` | `GENUINE_DIAGRAM_AMBIG` | `CONF REFUSED` (`LIVE_AI_DISABLED`, 1 ed) |
| 15 | `ext_prt_15_vmmu_page_r28` | `needs_conf` | 0.1055→0.0802 | 2 | `T/F/0/F/F` | `SAME_FAM:2` | 1 | 0 | `UNCERTAIN, DIAGRAM` | — | `RECOGNITION_ERR` | `CONF REFUSED` (`LIVE_AI_DISABLED`, 2 ed) |

---

## 3. Phân Tích Pháp Y 9 Ca `REAL27_TEXT` Bị Từ Chối Với Cô Lập Gold `TypedFactNext /2` (`§6.2`)

> Tổng kết `REAL27_TEXT`: **`18 / 27` `SERVED` (`0` wrong)** · **`9 / 27` `REFUSED`** · `PLANNER_GAP = 0` · `SCENE3D_GAP = 0`. Từng ca được chạy đối chiếu độc lập giữa `Local Parser` và đầu dò **Gold `TypedFactNext /2` -> `run_typed_fact_next_v2_route`** để tách rạch ròi lỗi Parser vs Registry/Kernel/Source Gate/miền đề.

| # | Case ID (Phân vùng) | Local Parser Status (`route_status` / `reason`) | Gold `TypedFactNext /2` Route Result | Loại chính (`§6.2`) | Loại phụ | Kết luận nguyên nhân gốc |
|---:|---|---|---|---|---|---|
| 1 | `vmmu_r254` (`frozen`) | `LOCAL_PARSE_PARTIAL` (`LIVE_AI_DISABLED`) | `REFUSED INVALID_DESCRIBED_POINT` | `TYPED_FACT_GAP` | `UNDERSTANDING_GAP`, `REGISTRY_GAP`, `KERNEL_EXACT_DOMAIN_GAP` | `TypedFactNext /2` không cho phép `@id` làm operand trong premise; đề còn hỏi thể tích tứ diện con `A'ABC` với góc đáy `30°` ngoài mẫu hiện có. |
| 2 | `vmmu_r256` (`frozen`) | `LOCAL_PARSE_PARTIAL` (`LIVE_AI_DISABLED`) | `REFUSED SOURCE_OBJECT_MISMATCH` (`counterfactual "đến" -> SERVED a√15/5`) | `SOURCE_GROUNDING_GAP` | `UNDERSTANDING_GAP` | Đề gốc có lỗi chính tả `"đên"` (thay `"đến"`). Giữ fail-closed ở Source Gate; counterfactual sửa thành `"đến"` phục vụ đúng `a√15/5`. |
| 3 | `vmmu_r266` (`frozen`) | `LOCAL_PARSE_COMPLETE` (`REFUSED EXACT_DOMAIN_EXCEEDED`) | `REFUSED EXACT_DOMAIN_EXCEEDED` | `KERNEL_EXACT_DOMAIN_GAP` | — | Parser khớp 100% Gold; định lý cosin tạo căn lồng ngoài miền Gram hữu tỉ `ℚ` của Exact Kernel (fail-closed có chủ đích). |
| 4 | `vmmu_r277` (`frozen`) | `LOCAL_PARSE_PARTIAL` (`LIVE_AI_DISABLED`) | `REFUSED BRIDGE_UNSUPPORTED_PREMISE` (`point_reflection`) | `TYPED_FACT_GAP` | `REGISTRY_GAP`, `UNDERSTANDING_GAP` | Thiếu bridge/primitive `point_reflection` qua trung điểm 3 cạnh và dựng khối tứ diện con mới `OMNP` trên 3 đỉnh phản xạ. |
| 5 | `vmmu_r461` (`dev`) | `LOCAL_PARSE_PARTIAL` (`LIVE_AI_DISABLED`) | `OUT_OF_SCOPE CURVED_ROLLED_SECTOR_OUT_OF_SCOPE` | `INTENTIONALLY_UNSUPPORTED` | `UNDERSTANDING_GAP` | Bài toán gấp quạt tròn thành hình nón — chủ đích nằm ngoài phạm vi đa diện/lăng trụ thuần xác minh. |
| 6 | `vmmu_r475` (`frozen`) | `LOCAL_PARSE_UNSUPPORTED` (`LIVE_AI_DISABLED`) | `OUT_OF_SCOPE MULTI_CURVED_FLUID_DISPLACEMENT_OUT_OF_SCOPE` | `INTENTIONALLY_UNSUPPORTED` | — | Tổ hợp nhiều khối cong lồng nhau + tỉ số thể tích nước tràn — chủ đích ngoài phạm vi (fail-closed). |
| 7 | `vmmu_r488` (`dev`) | `LOCAL_PARSE_PARTIAL` (`LIVE_AI_DISABLED`) | `REFUSED SOURCE_OBJECT_MISMATCH` (`host prism counterfactual -> SERVED a³/2`) | `REGISTRY_GAP` | `KERNEL_EXACT_DOMAIN_GAP`, `UNDERSTANDING_GAP` | Gold lăng trụ đơn phục vụ `a³/2` (suy ra `V(B'.ACC'A') = a³/3`), nhưng Registry/Engine chưa hỗ trợ đo trực tiếp thể tích khối chóp con tách từ lăng trụ. |
| 8 | `vmmu_r491` (`frozen`) | `LOCAL_PARSE_PARTIAL` (`LIVE_AI_DISABLED`) | `REFUSED SOURCE_PREMISE_UNREAD` | `TYPED_FACT_GAP` | `INSUFFICIENT_SPECIFICATION`, `UNDERSTANDING_GAP` | Điểm trượt tự do `"I thuộc cạnh BC"` không gắn tỉ số và thiếu `AA'` (đề gốc chỉ giải theo bất biến quỹ tích `(A'BC) ⊥ (ABC)`). |
| 9 | `vmmu_r513` (`dev`) | `LOCAL_PARSE_COMPLETE` (`REFUSED MISSING_DIMENSION`) | `REFUSED MISSING_DIMENSION` | `INSUFFICIENT_SPECIFICATION` | — | Đề gốc thiếu cạnh `BC/AD` của hình hộp chữ nhật; nhờ `_cac_moc_cau`, Local Parser và Gold đồng nhất `REFUSED MISSING_DIMENSION` (`UNPROVED_DUE_TO_CAPABILITY_GAP`). |

---

## 4. Kiểm Toán Riêng 3 Ca Cần Adjudication (`§6.3` — Mode A Output Policy)

> Kiểm chứng 6 tiêu chí bắt buộc trên `vmmu_r258`, `vmmu_r498`, `vmmu_r559`: Axo dựng đúng khối, đạt mục tiêu trực quan hóa góc, và **chủ đích ẩn số đo đáp án (`numeric_answer_shown = false`, `NOT_ANSWERED`)** theo hợp đồng `output-policy/1` Mode A; khác biệt với key bộ đề là **do oracle đề trắc nghiệm hỏi giá trị lượng giác/góc** trong khi mục tiêu sản phẩm của Axo là trực quan hóa không gian.

| Case ID (Phân vùng) | `Scene3D` (Objects / Continuity) | Mô phỏng hình học đúng? | Mục tiêu trực quan đạt? | Mode A ẩn số đo đúng hợp đồng? | Thiếu đối tượng / quan hệ? | Giá trị kernel nội bộ vs Key đề gốc (`EVI.same_value`) | Lý do adjudication (`dataset_oracle_mismatch_reason`) |
|---|---|---:|---:|---:|---|---|---|
| `vmmu_r258` (`frozen`) | `12` đối tượng / `0` lỗi liên tục | **Có (`True`)** | **Có (`GOAL_VISUALIZATION_READY`)** | **Có (`numeric_answer_shown=False`)** | Không (`[]`) | `cos²=1/3` vs key `√2` (`tan α`, biểu diễn khác + `False` ở so chuỗi trực tiếp) | `DATASET_KEY_ASKS_TRIG_VALUE_WHILE_AXO_MODE_A_VISUALIZES_ANGLE_ONLY` |
| `vmmu_r498` (`frozen`) | `18` đối tượng / `0` lỗi liên tục | **Có (`True`)** | **Có (`GOAL_VISUALIZATION_READY`)** | **Có (`numeric_answer_shown=False`)** | Không (`[]`) | `cos²=1/4` (`60°`) vs key `1/2` (`cos 60°`) | `DATASET_KEY_ASKS_TRIG_VALUE_WHILE_AXO_MODE_A_VISUALIZES_ANGLE_ONLY` |
| `vmmu_r559` (`fresh`) | `10` đối tượng / `0` lỗi liên tục | **Có (`True`)** | **Có (`GOAL_VISUALIZATION_READY`)** | **Có (`numeric_answer_shown=False`)** | Không (`[]`) | `cos²=1/12` vs key `√3/6` (`sin α` / góc bổ sung) | `DATASET_KEY_ASKS_TRIG_VALUE_WHILE_AXO_MODE_A_VISUALIZES_ANGLE_ONLY` |
