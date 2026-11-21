# SCENE3D_AND_FRONTEND_HANDOFF — Xác Minh Cảnh 3D, Hợp Đồng Xác Nhận & Bàn Giao Frontend

- **Run ID:** `real-world-geometry-input-verified-simulation`
- **Branch / Frozen Candidate:** `feat/local-first-geometry-understanding` · Product `b806e359fcceb268c065013d5cf7fb2ff278f1c1` · Frozen Candidate `003104fd5a116f38f05fe200d013b7e9ba93a05a` (`measured_system = e1c6428ed558a722442e0f32b362fb41d053795a81cf92a4c267d48e2bbd7a04`, `CACHE_VERSION = 144`)

---

## 1. Xác Minh Toán Học & Sư Phạm Trên `Scene3D`

Tất cả cấu hình hình học phục vụ qua text, OCR tự chấp nhận, OCR xác nhận tối thiểu, chọn dải đa bài, và giả lập fallback Vision đều được kiểm chứng độc lập bằng Exact Kernel `/24` và kiểm tra liên tục dựng hình (`validate_construction_continuity(scene3d) == []`):

- **`total_scene3d_continuity_errors = 0`** trên toàn bộ chiến dịch (`NC-1..21` NL & Gold, `A4` & depth, `reasoning_matrix`, `r1_probe`, `DEV37`, `COMP112`, `PROBES39`, `REAL27_TEXT`, `REAL27` ảnh, `External16`, `new_external_12`, `new_image_corpus_8`, và luồng Vision fallback mô phỏng).
- **`mode_a_trig_no_answer_leak = true`:** Trên mục tiêu dựng/lượng giác (`output-policy/1` Mode A, điển hình `cos²=1/2` và 3 ca `REAL27` `vmmu_r258`, `vmmu_r498`, `vmmu_r559`), `source_goal_completion` giữ `schema_version = "source-goal-completion/1"`, `numeric_answer_shown = false`, và `numeric_source_goal = "NOT_ANSWERED"`.
- **Tổng hợp chuyển hóa Ảnh -> `Scene3D` đã kiểm chứng (`0` wrong served):**
  - `REAL27` (`27` ảnh thật): **`0 / 27`** tự động chấp nhận (`0` false auto-accepts) → **`13 / 27`** `SERVED` sau xác nhận span tối thiểu (gồm **`vmmu_r247`** `18` obj và **`vmmu_r270`** `13` obj mới được giải cứu; `+5` ca bổ sung chỉ phục vụ nếu học sinh tự sửa ở ô toàn văn bản `whole_draft_confirmation_fallback`: `r258`, `r284`, `r375`, `r460`, `r463`).
  - `External15` (`15` ảnh in ngoài): **`1 / 15`** tự động chấp nhận (`ext_prt_01`, `16` obj) + **`8 / 12`** xác nhận span tối thiểu (`ext_prt_02`, `04`, `05`, `06`, `07`, `09`, `11`, `12` — **gồm 4 ảnh mới phục vụ đúng** `ext_prt_05` [`21` obj], `ext_prt_06` [`19` obj], `ext_prt_07` [`15` obj], `ext_prt_09` [`10` obj]) = **`9 / 15`** ảnh đơn phục vụ `Scene3D`, cộng **`2 / 6` dải chọn đa bài** phục vụ đúng (`ext_prt_03 #1 -> a√2/2` [`0` edit], `ext_prt_03 #2 -> a³/4` [`1` edit]).
  - Tập ngoài chưa đụng tới: `new_external_12` phục vụ `new_ext_05_vmmu_full_r411` (`cos²=1/2`, `12` obj); `new_image_corpus_8` (`frozen_external_evaluation`) phục vụ `new_vmmu_full_r446` (`√3/3`, `12` obj).
  - Luồng Vision fallback offline (`AIR.route_image_or_prepare_outcome` với mock `extraction_method="vlm"`): `SERVED` (`chosen_route = "VISION_THEN_LOCAL_DETERMINISTIC"`, `0` lời gọi `TypedFactNext`, `{'q1': 'a³√3/3'}`, `0` lỗi liên tục).

---

## 2. Hợp Đồng Xác Nhận & Xuất Xứ Đầu Vào Cho Frontend (`/api/input/prepare` → `/api/analyze`)

| Điểm chạm API | Trường hợp đồng | Nghĩa & Bắt buộc ở Frontend / Kiểm chứng |
|---|---|---|
| `POST /api/input/prepare` | `provenance.confirmation_contract_version` (`"ocr-confirmation-provenance/1"`), `raw_ocr_text_sha256`, `prepared_text_sha256`, `prepared_region_sha256` | Mọi phản hồi chuẩn bị ảnh (cả local OCR lẫn VLM) mang băm SHA-256 của văn bản thô ban đầu và ảnh vùng đã chuẩn bị để gửi kèm khi người dùng bấm dựng hình. |
| `POST /api/input/prepare` (`status = "needs_selection"`) | `candidates[]` (`candidate_id`, `label`, `problem_text`, `source_bbox`) + truyền lại `selected_candidate_id` | Đã kiểm chứng tách đúng trên `ext_prt_03_hd_q_7907931` (`2` bài `text-p1-1`, `text-p1-2`, phục vụ cả `2/2` sau xác nhận) và `ext_prt_08_hd_q_7509702` (`4` dải `page~band-1..4`, từ chối an toàn `0` wrong-served). |
| `POST /api/analyze` (`input.source_provenance`) | `origin` (`text_direct`, `local_ocr_auto_verified`, `local_ocr_student_confirmed`, `vision_ocr_auto_verified`, `vision_ocr_student_confirmed`, `selection_band_confirmed`), `raw_ocr_text_sha256`, `prepared_region_sha256`, `student_edited`, `confirmed_span_count`, `selected_candidate_id`, `selected_bbox` | Tùy chọn tương thích ngược (`_analyze_once` giữ nguyên đường gọi 4 tham số cho stub cũ); khi văn bản gửi lên khác `raw_ocr_text_sha256`, `build_verified_input_provenance` tự hạ cấp `origin` về `*_student_confirmed` và ép `counted_as_unmodified_auto_ocr = false`, đồng thời trả `input_provenance` (`"verified-input-provenance/1"`) trên bản sao phản hồi HTTP mà không làm bẩn cache DB. |
| Invalidation cache | `CACHE_VERSION = "144"`, `ROUTE_D_CACHE_POLICY = "144:route-d"` | Bản draft và bản đã chỉnh (`SA = a.` → `SA = 2a.`) tạo `cache_key` tách biệt; mọi dòng `143:route-d` cũ bị miss rõ ràng (`test_confirmation_provenance_edited_cache_key_and_144_invalidation`). |

---

## 3. Kiểm Chứng Frontend Trong Repo Chính & Ranh Giới Sở Hữu `FE-2/3/4/6`

- **Không sửa `frontend/` từ mốc `ce280140b`:** `git diff ce280140bf89ad72e8724993f75f98edcce01e55..003104fd5a116f38f05fe200d013b7e9ba93a05a -- frontend/` hoàn toàn rỗng (`0` file thay đổi), nên kết quả hồi quy Frontend trong worktree (`npm --prefix frontend run test:wave`: **`142` files / `2,062` tests PASSED (`69.53s`), `tsc -b` PASS, `vite build` PASS (`4.70s`)**) vẫn nguyên giá trị.
- **Kiểm chứng fixture hợp đồng Hybrid → Scene3D (`export_hybrid_preview_fixtures.py --verify`):**
  - Thư mục hợp lệ hiện hành `docs/evaluation/geometry/runs/dimension-aware-verified-construction/fixtures-dimension-aware`: **`41` verified, `problems = []`** (`backend_app_dirty = false`, `product_commit = b806e359fcce...`).
- **Tình trạng sở hữu `FE-2 / FE-3 / FE-4 / FE-6`:** **`BLOCKED_OWNERSHIP`** — giữ nguyên 100% ranh giới quy định: không sửa `D:\Documents\projects\axo-geometry-library` và `frontend/public/favicon.svg`, cũng như chưa trực tiếp mở UI hiển thị các ảnh mới trên Frontend bên ngoài bài test tự động của repo chính. Việc truyền `input.source_provenance` từ `PhotoProblemPanel.tsx` hoàn toàn tương thích ngược với client hiện có.
