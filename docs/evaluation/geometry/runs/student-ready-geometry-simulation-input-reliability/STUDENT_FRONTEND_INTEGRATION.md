# STUDENT FRONTEND INTEGRATION & EXPERIENCE REPORT — `student-ready-geometry-simulation-input-reliability` (`CACHE_VERSION = 145`)

- **Trạng Thái Tích Hợp Frontend Trực Tiếp:** `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP` · `Gate C = BLOCKED_OWNERSHIP`
- **Thẩm Quyền Sửa Mã Nguồn:** Mọi thư mục trong `frontend/**` giữ nguyên **0 byte thay đổi** so với gốc chiến dịch (`git diff ce280140bf89ad72e8724993f75f98edcce01e55..4c463d154 -- frontend/` trống).
- **Trạng Thái Nghiệm Thu Người Dùng Thực & Thiết Bị Thật:** `REAL_STUDENT_USABILITY = NOT_MEASURED` · `PHYSICAL_LOW_END = NOT_MEASURED`

---

## 1. Hỗ Trợ Trải Nghiệm Học Sinh Từ Phía Backend (`backend/app/`)

Dù bị chặn quyền chỉnh sửa trực tiếp mã React/Three.js tại `frontend/**`, phía backend đã hoàn thiện đầy đủ hợp đồng dữ liệu và chuẩn đầu ra sư phạm cho học sinh:

1. **Thông điệp sư phạm sạch mã máy (`backend/app/learner_messages.py`):**
   - Chuẩn hóa phản hồi từ chối/thiếu dữ kiện/vượt miền Exact sang tiếng Việt dễ hiểu với học sinh.
   - Kiểm tra tự động `hygiene_and_cache_145.learner_message_machine_token_leaks = []` (`0` rò rỉ token nội bộ/stack trace).
   - Tuân thủ chính sách Mode A (`user_visible_output_policy_mode_a_compliant = true`, `mode_a_trig_no_answer_leak = true`): khi tính toán tỷ số lượng giác (`cos²`), không làm lộ đáp án thô trong các bước dựng trung gian.
2. **Hợp đồng xác nhận OCR kèm ảnh nguồn (`ocr-confirmation-provenance/1` & `verified-input-provenance/1`):**
   - Mỗi span cần xác nhận đều trả `source_crop_png_base64`, ứng viên sửa nhanh và liên kết vùng trang chuẩn hóa để giao diện hiển thị ngay ảnh cắt đối chiếu cạnh ô xác nhận.
   - Tách xuất xứ `local_ocr_student_confirmed` với `local_ocr_auto_verified` và `manual_retype`.
3. **Tính liên tục Scene3D (`construction_continuity.py` & `adapter4_route.py`):**
   - `total_scene3d_continuity_errors = 0` trên toàn bộ mọi tập đánh giá (văn bản + ảnh + 4-viewport E2E + `frozen_unseen_vmmu20`).
   - Fixture kiểm chứng dựng hình xem trước (`export_hybrid_preview_fixtures.py --verify`): `41` fixtures khớp, `0` lỗi (`backend_app_dirty = false`).

---

## 2. Gói Vá Bàn Giao Cho Chủ Sở Hữu Frontend (`handoff/`)

Bốn bản vá sạch áp dụng lên `frontend/` được lưu và xác minh khả năng áp dụng bằng `git apply --check` (`rc = 0` cho cả 4 patch, mô tả tại `handoff/README.md`):

| Patch File | Kích thước (bytes) | SHA-256 | Nội dung tích hợp | `git apply --check` |
| :--- | ---: | :--- | :--- | :--- |
| `handoff/FE-2-multi-layer-aux-pyramid-readout.patch` | 2,534 | `c8eb3097cf82d610f27a905b6d1ebb755964f9704c3d8fe13c84e9e01cfdcd18` | Hiển thị đọc-ra đa tầng cho các thành phần chóp phụ trợ | `PASS` (`rc=0`) |
| `handoff/FE-3-ocr-confirmation-source-provenance.patch` | 8,805 | `93a4caccc49c0b45d22e8e2ac12a30274019c9a46552fe54536f413a0ceef24d` | Hiển thị ảnh cắt `source_crop_png_base64` trong UI xác nhận span & xuất xứ đầu vào | `PASS` (`rc=0`) |
| `handoff/FE-4-scene3d-auxiliary-role-styling.patch` | 4,609 | `c12b77f5a5d04bf2c64323902356418b8309f2a68c142b004d766c80b6d209ca` | Phân biệt trực quan nét chính / đường phụ trợ / mặt cắt trong Scene3D | `PASS` (`rc=0`) |
| `handoff/FE-6-workspace-grid-toggle.patch` | 628 | `9f2aea69cd3560efbff13961329726ab896d24d1d6b72e6f7c1deffce25d1ac1` | Công tắc bật/tắt lưới nền không gian làm việc 3D | `PASS` (`rc=0`) |

---

## 3. Kiểm Thử Trình Duyệt Tự Động 4 Kích Thước Màn Hình (`browser_e2e_4viewports.json`)

> **Phân loại bằng chứng:** `category = "AUTOMATED_BROWSER_NOT_HUMAN_STUDY"`. Thử nghiệm Chromium không đầu chạy trên bản dựng `frontend/dist` **chưa chỉnh sửa** kết nối backend loopback (`HYBRID_ROUTE_MODE=local-first`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, `live_provider_calls = 0`). Bằng chứng này **không** giải tỏa `Gate C = BLOCKED_OWNERSHIP` và **không** thay thế đo lường người dùng thật (`REAL_STUDENT_USABILITY = NOT_MEASURED`).

- **Script kiểm thử:** `tools/student_ready_browser_e2e.mjs` (`6,621` bytes kết quả JSON, SHA-256 `04371df58c20f40d819175b580c493b71ec9d45844c0c9f1ad29b6e7a2acd6f9`).
- **Ngữ cảnh phiên bản đóng dấu:** `git_head_sha = 4c463d154885e99ad9bf07e3898d11c619eb63c4`, `product_commit = ac0ea63dd462c92a8736b607764d1df552d29329`, `measured_system_hash = 8a88dbfe9ddc35e38639c7c81e8c7741b1ea1dd1cd848bc9e7dc6bf16885b0c6` (`120` files), `CACHE_VERSION = "145"`, `ROUTE_D_CACHE_POLICY = "145:route-d"`, `temp_files_cleaned_up = true`.

| Viewport | Reg | `vmmu_r254` (canvas W×H, steps, overflow) | `vmmu_r277` (stale_prev) | Mode A Trig | OCR Confirmation (`needs_confirmation -> SERVED`) | Honest Refusal (`EXACT_DOMAIN_EXCEEDED`, toast sạch, `0` canvas) | Errors (`page`/`console`/`req`) | Kết quả |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `1920×1080` | 200 | `9a³√13/2`, `1560×1034`, `8` steps, `0` px | `8a³`, `12` steps, `false` | `PASS` | `a√6/3` (`PASS`) | `PASS` (`Axo chưa hỗ trợ phép dựng này...`) | `0` / `0` / `0` | `PASS` |
| `1366×768` | 200 | `9a³√13/2`, `1006×722`, `8` steps, `0` px | `8a³`, `12` steps, `false` | `PASS` | `a√6/3` (`PASS`) | `PASS` | `0` / `0` / `0` | `PASS` |
| `768×1024` | 200 | `9a³√13/2`, `472×978`, `8` steps, `0` px | `8a³`, `12` steps, `false` | `PASS` | `a√6/3` (`PASS`) | `PASS` | `0` / `0` / `0` | `PASS` |
| `390×844` | 200 | `9a³√13/2`, `390×438`, `8` steps, `0` px | `8a³`, `12` steps, `false` | `PASS` | `a√6/3` (`PASS`) | `PASS` | `0` / `0` / `0` | `PASS` |

- **Kiểm tra bổ sung trên trình duyệt:**
  - `multi_problem_sheet_1366x768`: `prepare_status = "needs_selection"`, `candidate_count = 2`, sau khi chọn dải -> `picked_status = "ready"`, `zero_neighbor_bleed = true`, `pass = true`.
  - `camera_orbit_1920x1080`: `changed = true` (xoay camera 3D thay đổi khung hình thực tế).
  - **Verdict E2E tổng thể:** `PASS` (nhưng `frontend_integration: "BLOCKED_OWNERSHIP"`, `gate_c: "BLOCKED_OWNERSHIP"`).
