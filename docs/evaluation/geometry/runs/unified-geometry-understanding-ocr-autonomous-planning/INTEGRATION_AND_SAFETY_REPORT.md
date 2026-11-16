# INTEGRATION_AND_SAFETY_REPORT — Kiểm Chứng Tích Hợp, An Toàn & Bất Biến (`unified-geometry-understanding-ocr-autonomous-planning`)

- **Run ID:** `unified-geometry-understanding-ocr-autonomous-planning`
- **Evaluated Frozen Candidate:** `dbf61030357c477dc80c90adb3efc1a7342e4f1f` (`product_commit = fff0e63bde0e5be9f6897a1909750b8995fdd310`, `measured_system = 9aa3eaa3b5bddab90d3d45f437a8e08ad7517db674755cef3fc88fd9be25e3bf`, `120` files)
- **Live AI Budget:** `ALLOW_LIVE_AI = 0` · **`0` lượt gọi AI live** (`MODEL_REQUEST_COUNT = 0`)
- **Blind/Sealed Isolation:** `0` hàng H-1 mở (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`), `0` hàng W2/W3 khóa đọc trong phát triển.

---

## 1. Tính Liên Tục `Scene3D` & Chính Sách Trưng Bày `output-policy/1` (Stream C)

1. **Construction Continuity (`validate_construction_continuity`):**
   - Toàn bộ các ca `SERVED` trong đánh giá hợp nhất (`NC-*` Gold `21/21` và NL `21/21`, `A4` và độ sâu `<= 2`, `reasoning_matrix` `61/62`, `r1_probe` `13/13`, `dev37` `30/37`, `comp112` `66/112`, `probes39` `23/39`, `real27_text` `18/27`, cộng cảnh lượng giác Chế độ A trong `test_unified_understanding_ocr_planning.py`) đều ghi nhận **`total_scene3d_continuity_errors = 0`**.
2. **`output-policy/1` Mode A (Không rò đáp số cho mục tiêu dựng/trực quan lượng giác):**
   - Trong `END_TO_END_CAPABILITY_EVALUATION.json` (`stream_c`): phép kiểm lượng giác Mode A kiểm chứng đáp số chuẩn nội bộ `q1 = "cos²=1/2"` khớp chính xác toán học trong kernel nhưng tuyến phục vụ người học giữ nguyên `mode_a_trig_no_answer_leak = true`.
   - Trong `test_stream_c_mode_a_and_cache_143_invalidation`: gọi `route_text_input` cho đề tính côsin góc `SB` và `(ABC)` trả `SERVED` với `source_goal_completion.numeric_answer_shown == False` và `goals[0]["numeric_source_goal"] == "NOT_ANSWERED"` (**`0` rò đáp số**).

---

## 2. Giới HạnTìm Kiếm Planner & Trần Ngân Sách IR (`MG9`)

| Hạng mục đo (`MG9` — `reasoning_matrix_72`) | Baseline (`5c1713997`, `CACHE 142`) | Hiện hành (`dbf610303`, `CACHE 143`) | Trạng thái an toàn |
|---|---:|---:|---|
| `Planner` status | `PLAN_SUCCEEDED` | `PLAN_SUCCEEDED` | Tất định, `NO_PLANNER_HARDCODING` |
| `candidate_evaluations` / `max_candidates` | `54` | `33` (`<= 48`) | Đạt trần tìm kiếm (`48`) |
| `pruned_nodes` | `0` | `21` | Tỉa nhánh tiền điều kiện hoạt động |
| `explored_states` / `search_depth` | — | `72` / `4` (`<= 4`) | Đạt giới hạn độ sâu |
| `route_ir_budget` / `reason_code` | `REFUSED` (`IR_MEMORY_BUDGET_EXCEEDED`) | `REFUSED` (`IR_MEMORY_BUDGET_EXCEEDED`) | Giữ fail-closed ở `34` decl (`min 33 > 32 = MAX_MEMORY_DECLARATIONS`) |

Cố ý **không** nới trần `MAX_MEMORY_DECLARATIONS = 32` trong chiến dịch này để bảo toàn giới hạn tiêu thụ bộ nhớ IR và khả năng suy luận giới hạn.

---

## 3. An Toàn OCR Hình Học & Cơ Chế Không Tự Động Nhận Sai (`0` False Auto-Accepts)

1. **Chứng thực nét chữ & ngưỡng chấp nhận (`CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY`):**
   - Kiểm tra 10 mẫu bitmap nét chữ chuẩn (`a²,`, `a2,`, `a³.`, `a3.`, `a√3.`, `aV3.`, `4cm²,`, `⊥`, `L`, `∥`): **`10 / 10` đạt**.
   - **Tổng hợp ảnh render chuẩn (`rendered_positive`):** `4 / 4` (`pos_area_a2` -> `a√6/3`, `pos_2a_sqrt3` -> `4a³√3/3`, `pos_area_frac_a2_2` -> `a³/6`, `pos_cm_cm2` -> `√6`) đạt `ocr_decision = LOCAL_OCR_ACCEPT`, `routed_status = SERVED`, đáp án khớp chính xác.
   - **Mẫu đối kháng tổng hợp (`adversarial_negative`):** `3 / 3` (`neg_inline_a2`, `neg_blurry_crop`, `neg_diagram_ref`) đều bị chặn tại `ocr_decision = LOCAL_OCR_REVIEW_REQUIRED` (`prepare_status = needs_confirmation`, **`false_auto_accepts = 0`**).
   - **Ảnh chụp thực tế `real27` (`27` ảnh):** `27 / 27` đi vào `LOCAL_OCR_REVIEW_REQUIRED` (`median_cer = 0.0944`, `p50 = 2218.54 ms`, `p95 = 3487.11 ms`, **`auto_served_wrong = 0`**).
   - **Ảnh in ngoài `external16_printed_images` (`15` ảnh đánh giá):** `1` ca `LOCAL_OCR_ACCEPT` (`ext_prt_01_hd_q_5259753`, `CER = 0.0`), `12` ca `LOCAL_OCR_REVIEW_REQUIRED`, `2` ca `needs_selection` (`ocr_decision = None`), **`auto_served_wrong = 0`**.
2. **Tách cache & toàn vẹn trạng thái:**
   - `_RAW_OCR_CACHE` (`max = 32`) và `_REREAD_CACHE` (`max = 64`) hoạt động độc lập; gọi đọc lại nhiều crop không đẩy bản ghi toàn trang khỏi bộ nhớ đệm thô.

---

## 4. Khóa Bề Mặt Trích Xuất, Vô Hiệu Hóa Cache SQLite `142 -> 143` & Template C21

1. **Bốn bề mặt trích xuất khóa cứng bất biến (`surfaces_ok = true`):**
   - `function_calling`: `7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`
   - `fact_extraction_flat`: `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`
   - `fact_extraction_v3`: `4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f`
   - `typed_fact_next`: `33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14`
2. **Vô hiệu hóa cache SQLite (`CACHE_VERSION = "143"`):**
   - `ROUTE_D_CACHE_POLICY = "143:route-d"`, `semantic_environment_hash = 6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b`, xác nhận khớp bằng `backend/scripts/lock_cache_identity.py --verify`.
   - `test_stream_c_mode_a_and_cache_143_invalidation` bơm trực tiếp bản ghi `SimulationCache` giả lập dưới policy `142:route-d` (`STALE_142_MARKER`) và kiểm chứng `POST /api/analyze` loại bỏ marker cũ và dựng lại dưới `143:route-d`.
3. **Làm mới siêu dữ liệu mẫu chờ C21 (`pending_template_refresh.json`):**
   - Commit `a27473ef6cdd4d588ba1bde42596ddb587cfc7db` (qua `tools/refresh_pending_templates.py`) cập nhật `measured_system` và `measured_system_tree_hash` của 3 mẫu `K-1`, `S-2`, `R-1` từ `c55ffdaf50429d0d8bcb09b9f162f5a626783d4f72f4dc485fb42a8c8f964f6a` sang `9aa3eaa3b5bddab90d3d45f437a8e08ad7517db674755cef3fc88fd9be25e3bf`.
   - Bảo lưu nguyên vẹn bản gốc tại `logs/prior-{k1,s2,r1}-owner-approval.template.json` và giữ cứng `owner_decision = "PENDING_OWNER_DECISION"`, `paid_project_confirmed = false` (`0` phê duyệt giả).

---

## 5. Kết Quả Hồi Quy Toàn Hệ Thống & Cổng Kiểm Chuẩn (Gate F) Trên Candidate `dbf610303`

| Cổng kiểm chứng | Lệnh thực thi | Kết quả quan sát trên `dbf610303` |
|---|---|---|
| Full Backend Pytest | `pytest -c backend/pytest.ini backend/tests -q` (`ALLOW_LIVE_AI=0`, `LOCAL_OCR_PYTHON`/`LOCAL_OCR_TESSDATA`/`HYBRID_ROUTE_MODE` unset) | **`14860 passed, 7 skipped, 3 deselected, 12 xfailed, 1 warning in 792.50s (0:13:12)`** (`0 failed`) |
| Frontend Full Wave (`vitest` + `tsc` + `vite build`) | `npm --prefix frontend run test:wave` | **`Test Files 142 passed (142), Tests 2062 passed (2062) in 50.31s`**, `tsc -b OK`, `vite build OK (3.70s)` |
| Demo Replay Gate | `python backend/scripts/replay_demo_cases.py --json` | `DEMO_REPLAY_PASS="5/5"`, `REDUCED_CHAIN_CASES="1/1"` |
| Demo Crash Surface Audit | `python backend/scripts/audit_demo_crash_surface.py --json` | `6/6` (`khop=true, nem=false`) |
| Hybrid Preview Fixtures | `python backend/scripts/export_hybrid_preview_fixtures.py --verify docs/evaluation/geometry/runs/dimension-aware-verified-construction/fixtures-dimension-aware` | `verified=41, problems=[]` |
| Candidate Freeze Check | `python backend/scripts/freeze_evaluation_candidate.py --verify` | Khớp (`120` file, `9aa3eaa3b5bddab90d3d45f437a8e08ad7517db674755cef3fc88fd9be25e3bf`, `SEALED = DA_NIEM_PHONG`) |
| Cache Identity Lock Check | `python backend/scripts/lock_cache_identity.py --verify` | Khớp (`CACHE_VERSION 143`, `6233c43c395c9b49...`) |
