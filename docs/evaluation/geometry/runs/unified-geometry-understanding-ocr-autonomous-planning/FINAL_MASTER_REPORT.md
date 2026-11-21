# FINAL_MASTER_REPORT — Chiến Dịch Hợp Nhất Hiểu Đề, OCR & Lập Kế Hoạch Hình Học Tự Động (`unified-geometry-understanding-ocr-autonomous-planning`)

- **Run ID:** `unified-geometry-understanding-ocr-autonomous-planning`
- **Branch:** `feat/local-first-geometry-understanding` (chỉ kiểm thử offline `ALLOW_LIVE_AI = 0`, `MODEL_REQUEST_COUNT = 0`; chưa merge vào `main`)
- **Chuỗi commit chiến dịch:**
  - Baseline anchor (`start_head`): `5c1713997540de91d2b6c10fcdbd0d8724aced1c` (`CACHE_VERSION = "142"`, candidate trước `009c06df12b3612ed95ecdf7f44bbba56758c2f7`, `measured_system = a9e6a372da73497b...`)
  - Product Stage 1: `65a393212b68710ba1712f2aff431191127b78aa` (Stream A/B/C & `CACHE_VERSION = "143"`)
  - Forward Fix: `fff0e63bde0e5be9f6897a1909750b8995fdd310` (tách nhóm regex `_td_mat_truoc_khoi`, giới hạn phân tách câu ghép/đơn vị cục bộ, cập nhật ô `**143**` trong `docs/CURRENT_STATE.md`)
  - Tooling & Template Refresh: `b954a8e229d7a7a06296a343beccef38890228bf`, `5a22b3d27e0f87ba028ee082ac84aa379a56de91`, `a27473ef6cdd4d588ba1bde42596ddb587cfc7db`
  - **Evaluated Frozen Candidate:** `dbf61030357c477dc80c90adb3efc1a7342e4f1f` (`measured_system = 9aa3eaa3b5bddab90d3d45f437a8e08ad7517db674755cef3fc88fd9be25e3bf`, `120` file, `CACHE_VERSION = "143"`, `ROUTE_D_CACHE_POLICY = "143:route-d"`, `SEALED = DA_NIEM_PHONG`)

---

## 1. Tóm Tắt Trước / Sau Trên Toàn Chiến Dịch (Streams A / B / C)

### 1.1 Stream A — Hiểu Đề Hình Học Tiếng Việt Tổ Hợp & Ràng Buộc `A4`

| Bộ chuẩn / Chỉ số (`ALLOW_LIVE_AI = 0`) | Baseline (`5c1713997`) | Hiện hành (`dbf610303`) | Ghi chú kỹ thuật |
|---|---:|---:|---|
| `NC-*` Gold `TypedFactNext /2` | `21 / 21` | `21 / 21` | `p50 = 279.296 ms`, `p95 = 502.043 ms`, `continuity_errors = 0` |
| `NC-*` Tiếng Việt tự nhiên (NL) | `4 / 21` (`19.0%`) | **`21 / 21` (`100.0%`)** | `p50 = 40.487 ms`, `p95 = 80.316 ms`, **`0` provider calls** |
| Ca phủ định tự hành (`autonomous_negatives`) | `11 / 11` | `11 / 11` | `0` ca bị phục vụ nhầm (`false_served = 0`) |
| `A4` `contains_points` (`@id`) & depth bound | Bị chặn `INVALID_QUALIFIED_REF` | **`6 / 6` đạt** | `A4_nl_dir`, `A4_nl_3pt`, `A4_gold_contains_points`, `DEPTH2_centroid_proj_served` -> `SERVED`; `A4_neg_parallel_to_line_refused` -> `INVALID_QUALIFIED_REF`; `DEPTH3_fail_closed` -> `PLAN_TOO_LARGE` |
| `reasoning_matrix` (72 ca: 62 pos / 10 neg) | `61 / 62` pos, `10 / 10` neg | `61 / 62` pos, `10 / 10` neg | `p50 = 170.362 ms`, `p95 = 713.528 ms`, `peak_memory_p95 = 2038.86 KiB`, `false_served = 0`; `MG9` planner `33 <= 48` (`21` pruned vs `54`/`0` baseline), fail-closed `IR_MEMORY_BUDGET_EXCEEDED` |
| `r1_probe` (19 ca: 13 pos / 6 adv neg) | `13 / 13` + `6 / 6` | `13 / 13` + `6 / 6` | `false_served = 0` |
| Bộ phát triển lộ thiên (`dev37`, `comp112`, `probes39`, `real27_text`) | Thiếu `diagram_benign`, `sec_do_P_cat`, `dp_unnamed_through_point` | **`dev37 = 30/37`**, **`comp112 = 66/112`**, **`probes39 = 23/39`**, **`real27_text = 18/27`** | `diagram_benign`, `sec_do_P_cat`, `dp_unnamed_through_point` -> `SERVED`; **`0` wrong/false-served trên mọi tập** (`9/27` ca `real27_text` từ chối sạch `REFUSED`) |

### 1.2 Stream B — OCR Hình Học Tin Cậy & Đối Chiếu Hai Họ (`layout-aware-ocr-reconcile/2`)

| Chỉ số / Tập ảnh | Kết quả trên `dbf610303` | An toàn / Ý nghĩa |
|---|---|---|
| Kiểm chứng hình học nét chữ (`_analyze_crop_glyph_topology`) | **`10 / 10` đạt** | Phân biệt `a²`/`a2`, `a³`/`a3`, `a√3`/`aV3`, `4cm²`, `⊥`/`L`, `∥` thuần bitmap |
| Tách cache OCR | `_RAW_OCR_CACHE = 32`, `_REREAD_CACHE = 64` | Không còn đẩy mất kết quả OCR toàn trang khi đọc lại nhiều crop |
| Ảnh render tổng hợp chuẩn (`rendered_positive`) | **`4 / 4` `LOCAL_OCR_ACCEPT` -> `SERVED`** | `pos_area_a2` (`a√6/3`), `pos_2a_sqrt3` (`4a³√3/3`), `pos_area_frac_a2_2` (`a³/6`), `pos_cm_cm2` (`√6`) khớp chính xác |
| Mẫu đối kháng tổng hợp (`adversarial_negative`) | **`3 / 3` bị chặn (`false_auto_accepts = 0`)** | `neg_inline_a2`, `neg_blurry_crop`, `neg_diagram_ref` đều về `LOCAL_OCR_REVIEW_REQUIRED` (`needs_confirmation`) |
| Ảnh chụp thực tế `real27_images` (`27` ảnh) | **`27 / 27` `LOCAL_OCR_REVIEW_REQUIRED`** | `median_cer = 0.0944`, `p50 = 2218.54 ms`, `p95 = 3487.11 ms`, **`auto_served_wrong = 0`** |
| Ảnh in ngoài `external16_printed_images` (`15` ảnh đánh giá) | `1` `LOCAL_OCR_ACCEPT` (`ext_prt_01_hd_q_5259753`, `CER = 0.0`), `12` `LOCAL_OCR_REVIEW_REQUIRED`, `2` `needs_selection` | **`auto_served_wrong = 0`** |

### 1.3 Stream C — Bất Biến Kiến Trúc, Cảnh 3D & Cache `143`

- **Bốn bề mặt trích xuất khóa cứng:** Giữ nguyên bit-identical (`function_calling = 7ea511a6...`, `fact_extraction_flat = 485d3834...`, `fact_extraction_v3 = 4bff35bb...`, `typed_fact_next = 33197a45...`).
- **Tính liên tục `Scene3D`:** `total_scene3d_continuity_errors = 0`.
- **Chính sách trưng bày `output-policy/1` Mode A:** `mode_a_trig_no_answer_leak = true` (`0` rò đáp số ở mục tiêu dựng/lượng giác).
- **Cache SQLite `142 -> 143`:** `CACHE_VERSION = "143"`, `ROUTE_D_CACHE_POLICY = "143:route-d"`, `semantic_environment_hash = 6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b`, xác nhận loại bỏ dòng `142:route-d` qua `POST /api/analyze`.

---

## 2. Xác Nhận Hồi Quy & Cổng Kiểm Chuẩn (Gate F) Trên `dbf610303`

- **Full Backend Pytest:** `14860 passed, 7 skipped, 3 deselected, 12 xfailed, 1 warning in 792.50s (0:13:12)` (`0 failed`, `ALLOW_LIVE_AI = 0`, `LOCAL_OCR_PYTHON`/`LOCAL_OCR_TESSDATA`/`HYBRID_ROUTE_MODE` unset).
- **Targeted Parser/Regression Subset (`fff0e63bd` check, 11 files):** `367 passed, 0 failed in 23.37s`.
- **Frontend Wave (`npm --prefix frontend run test:wave`):** `Test Files 142 passed (142), Tests 2062 passed (2062) in 50.31s`, `tsc -b OK`, `vite build OK (3.70s)`.
- **Canonical Backend Gates:**
  - `replay_demo_cases.py --json`: `DEMO_REPLAY_PASS="5/5"`, `REDUCED_CHAIN_CASES="1/1"`.
  - `audit_demo_crash_surface.py --json`: `6/6` (`khop=true, nem=false`).
  - `export_hybrid_preview_fixtures.py --verify docs/evaluation/geometry/runs/dimension-aware-verified-construction/fixtures-dimension-aware`: `verified=41, problems=[]`.
  - `freeze_evaluation_candidate.py --verify`: Khớp (`120` file, `9aa3eaa3b5bddab90d3d45f437a8e08ad7517db674755cef3fc88fd9be25e3bf`, `SEALED = DA_NIEM_PHONG`).
  - `lock_cache_identity.py --verify`: Khớp (`CACHE_VERSION 143`, `semantic_environment_hash = 6233c43c395c9b49...`).

---

## 3. Trạng Thái Cổng Phát Hành & Giới Hạn Trung Thực

- `OFFLINE_DEVELOPMENT_EVIDENCE`: **ĐẠT** trên toàn bộ tập phát triển và hồi quy nội bộ (`0` lượt gọi AI live).
- `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`: **0** hàng H-1 niêm phong được mở hoặc đo trong chiến dịch này.
- `REAL_STUDENT_USABILITY = NOT_MEASURED`: Chưa đo thử nghiệm học sinh thật.
- `PHYSICAL_LOW_END = NOT_MEASURED`: Chưa đo trên thiết bị phần cứng cấu hình thấp thực tế.
- `K-1 / S-2 / R-1 = PENDING_OWNER_DECISION`: Chỉ làm mới siêu dữ liệu `measured_system` sang `9aa3eaa3b5bddab90d3d45f437a8e08ad7517db674755cef3fc88fd9be25e3bf` (`paid_project_confirmed: false`); chờ quyết định của Owner.
- `FE-2 / FE-3 / FE-4 / FE-6 = BLOCKED_OWNERSHIP`: Thuộc worktree riêng `D:\Documents\projects\axo-geometry-library`, hoàn toàn không chỉnh sửa trong chiến dịch này.
- `PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW`: Không tự động merge vào `main` hay push; chờ Owner xem xét.

---

## 4. Bảng Chứng Từ & Hàm Băm SHA-256 (Các Tạo Tác Trong Thư Mục Run)

> Ghi chú chống vòng lặp: Bảng dưới đây ghi nhận SHA-256 chính xác của mọi tệp chứng cứ khác trong run; `run.json` ghi nhận SHA-256 và dung lượng byte cho **toàn bộ** tệp bao gồm cả `FINAL_MASTER_REPORT.md`.

| Tệp (`docs/evaluation/geometry/runs/unified-geometry-understanding-ocr-autonomous-planning/...`) | Kích thước (bytes) | SHA-256 |
|---|---:|---|
| `END_TO_END_CAPABILITY_EVALUATION.json` | 214,654 | `6bcabf3e764b2d8e93029892f82d3c2ada6d9800a322bd3a29993c499ca90859` |
| `UNDERSTANDING_AND_OCR_BASELINE.md` | 8,136 | `d7cbc4a7f4596c77b975af21f7c4c4d79300e88f093dcde8c9a4b45b1d02c674` |
| `UNIFIED_IMPLEMENTATION_REPORT.md` | 9,641 | `7251d270b1aef530077d5b08abbf36bfe19b4b20b7f12a5aa81e375be51e8157` |
| `INTEGRATION_AND_SAFETY_REPORT.md` | 7,917 | `8b775be6b5c9193a961f1910587ff889b15046cee2cccc3ff5fba6bf452674d4` |
| `pending_template_refresh.json` | 3,564 | `bc7496529402fba7bf21cd30ce697ce4b582bf6d55c9deaf08c62ccb3005c01c` |
| `logs/prior-k1-owner-approval.template.json` | 782 | `63f4ba18cc43f1c103207d0d07ebf39fc8183619cb5b6691bf915198b6a60a5c` |
| `logs/prior-r1-owner-approval.template.json` | 782 | `7e1be48f34fb35b58766d35bd0520270b553da1dff37391461a9593deb6ef9c1` |
| `logs/prior-s2-owner-approval.template.json` | 782 | `809bb35537768937948f1e0cdb9cbf4eebc38cd555683551a5e8d28dd5d56d7d` |
| `tools/evaluate_unified_campaign.py` | 43,400 | `f22a0f01bc85b3cf886cae2fbcc0110f7d90dbb549de682b307879ee4834023e` |
| `tools/refresh_pending_templates.py` | 3,473 | `3c078c4154ef9d2f61ef83c041d230a1bac6f147faf904b60966818886e6f270` |
