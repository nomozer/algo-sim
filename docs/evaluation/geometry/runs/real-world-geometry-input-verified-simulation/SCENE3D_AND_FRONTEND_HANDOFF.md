# SCENE3D_AND_FRONTEND_HANDOFF — Xác Minh Cảnh 3D, Hợp Đồng Xác Nhận & Bàn Giao Frontend

- **Run ID:** `real-world-geometry-input-verified-simulation`
- **Branch / Product:** `feat/local-first-geometry-understanding` · Product `6de23b196b711674b2610c8436ef617195947fa7`, `0dcc3840a5e7ff88989911d76a14e3b17e1a4821` · `measured_system = 14fb41dbb6c5bbc032c57302be9cc6e0c09023da1f763f16f01f8df5fae28028` (`CACHE_VERSION = 144`)

---

## 1. Xác Minh Toán Học & Sư Phạm Trên `Scene3D`

Tất cả các cấu hình hình học phục vụ qua text, OCR tự chấp nhận, OCR xác nhận tối thiểu, và giả lập fallback Vision đều được kiểm chứng độc lập bằng Exact Kernel `/24` và kiểm tra liên tục dựng hình (`validate_construction_continuity(scene3d) == []`):

- **`total_scene3d_continuity_errors = 0`** trên toàn bộ chiến dịch (`NC-1..21` NL & Gold, `A4` & depth, `reasoning_matrix`, `r1_probe`, `DEV37`, `COMP112`, `PROBES39`, `REAL27_TEXT`, `REAL27` ảnh, `External16`, `new_external_12`, `new_image_corpus_8`, và luồng Vision fallback mô phỏng).
- **`mode_a_trig_no_answer_leak = true`:** Trên mục tiêu dựng/lượng giác (`output-policy/1` Mode A, điển hình `cos²=1/2` và 3 ca `REAL27` được kiểm tra `vmmu_r258`, `vmmu_r498`, `vmmu_r559`), `source_goal_completion` giữ `schema_version = "source-goal-completion/1"`, `numeric_answer_shown = false`, và `numeric_source_goal = "NOT_ANSWERED"`.
- **Ví dụ đầu cuối Ảnh -> Scene3D xác thực trong chiến dịch:**
  - `vmmu_r559` (ảnh thật `fresh_external_evaluation`, tự chấp nhận `LOCAL_OCR_ACCEPT`, `CER = 0.0214`, `0` thao tác sửa): `SERVED` `cos²=1/12` (khớp exact key `B. √3/6`), `10` đối tượng `Scene3D`, `0` lỗi liên tục.
  - `ext_prt_01_hd_q_5259753` (ảnh thật `External16`, `LOCAL_OCR_ACCEPT`, `CER = 0.0`): `SERVED` `{'q1': 'a³√3/3', 'q2': 'a√21/21'}`, `16` đối tượng `Scene3D`, `0` lỗi liên tục.
  - `new_vmmu_full_r446` (tập ngoài chưa đụng tới `frozen_external_evaluation`, xác nhận tối thiểu `1` edit `4, -> A,` / `2` ký tự gõ): `SERVED` `{'q1': '√3/3'}`, `12` đối tượng `Scene3D`, `0` lỗi liên tục.
  - Luồng Vision fallback offline (`AIR.route_image_or_prepare_outcome` với mock `extraction_method="vlm"`): `SERVED` (`chosen_route = "VISION_THEN_LOCAL_DETERMINISTIC"`, `0` lời gọi `TypedFactNext`, `{'q1': 'a³√3/3'}`, `0` lỗi liên tục).

---

## 2. Hợp Đồng Xác Nhận & Xuất Xứ Đầu Vào Cho Frontend (`/api/input/prepare` -> `/api/analyze`)

| Điểm chạm API | Trường hợp đồng | Nghĩa & Bắt buộc ở Frontend / Kiểm chứng |
|---|---|---|
| `POST /api/input/prepare` | `provenance.confirmation_contract_version` (`"ocr-confirmation-provenance/1"`), `raw_ocr_text_sha256`, `prepared_text_sha256`, `prepared_region_sha256` | Mọi phản hồi chuẩn bị ảnh (cả local OCR lẫn VLM) mang băm SHA-256 của văn bản thô ban đầu và ảnh vùng đã chuẩn bị để gửi kèm khi người dùng bấm dựng hình. |
| `POST /api/input/prepare` (`status = "needs_selection"`) | `candidates[]` (`candidate_id`, `label`, `problem_text`, `source_bbox`) + truyền lại `selected_candidate_id` | Đã kiểm chứng kích hoạt tách dải/bài trên `ext_prt_03_hd_q_7907931` (`2` bài `text-p1-1`, `text-p1-2`) và `ext_prt_08_hd_q_7509702` (`4` dải `page~band-1..4`). |
| `POST /api/analyze` (`input.source_provenance`) | `origin` (`text_direct`, `local_ocr_auto_verified`, `local_ocr_student_confirmed`, `vision_ocr_auto_verified`, `vision_ocr_student_confirmed`, `selection_band_confirmed`), `raw_ocr_text_sha256`, `prepared_region_sha256`, `student_edited`, `confirmed_span_count`, `selected_candidate_id`, `selected_bbox` | Tùy chọn tương thích ngược; khi văn bản gửi lên khác `raw_ocr_text_sha256`, backend (`build_verified_input_provenance`) tự động hạ cấp `origin` về `*_student_confirmed` và ép `counted_as_unmodified_auto_ocr = false`, đồng thời trả `input_provenance` (`"verified-input-provenance/1"`) trên bản sao JSON phản hồi HTTP mà không làm bẩn cache DB. |
| Invalidation cache | `CACHE_VERSION = "144"`, `ROUTE_D_CACHE_POLICY = "144:route-d"` | Phiên bản draft và phiên bản đã sửa (`SA = a.` -> `SA = 2a.`) tạo `cache_key` tách biệt; mọi dòng `143:route-d` cũ bị miss và tính lại tường minh (`test_confirmation_provenance_edited_cache_key_and_144_invalidation`). |

---

## 3. Kiểm Chứng Frontend Trong Repo Chính & Ranh Giới Sở Hữu `FE-2/3/4/6`

- **Cổng hồi quy Frontend trong worktree hiện hành (`npm --prefix frontend run test:wave`):**
  - `Test Files`: **`142 passed (142)`**
  - `Tests`: **`2062 passed (2062)`** (`52.24s`)
  - `tsc -b`: **PASS**
  - `vite build`: **PASS** (`4.21s`)
- **Kiểm chứng fixture hợp đồng Hybrid → Scene3D (`export_hybrid_preview_fixtures.py --verify`):**
  - Thư mục hợp lệ hiện hành `docs/evaluation/geometry/runs/dimension-aware-verified-construction/fixtures-dimension-aware`: **`41` verified, `problems = []`** (ghi chú: bundle lịch sử `hybrid-preview-contract-hardening/fixtures-adapter-2` là gói kế thừa đã bị thay thế từ CACHE 130/140 như tài liệu trong `test_hybrid_preview_fixtures.py`).
- **Tình trạng sở hữu `FE-2 / FE-3 / FE-4 / FE-6`:** **`BLOCKED_OWNERSHIP`** (giữ nguyên đúng ranh giới quy định — không sửa bất kỳ file nào tại `D:\Documents\projects\axo-geometry-library`, cũng như không sửa `frontend/public/favicon.svg` hay mở lại các issue đang chờ Frontend `ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D`, `gridShown={false}`, `FE-4` trace auxiliary dots). Nếu nhóm Frontend cần tiêu thụ các trường mới `provenance.confirmation_contract_version` / `raw_ocr_text_sha256` để điền `input.source_provenance` từ `PhotoProblemPanel.tsx`, các trường này hoàn toàn tùy chọn và tương thích ngược với client hiện có.
