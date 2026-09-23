# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context

> **Tài liệu bàn giao phiên (handoff) có thẩm quyền cao, mật độ thông tin lớn.**
> Dành cho agent / AI session mới tiếp quản kho mã mà không cần đọc lại toàn bộ lịch sử dài hàng trăm file.
> Giới hạn dung lượng: <= 300 dòng. Không chứa secret hay raw model output.

---

## 1. AlgoSim Là Gì?
AlgoSim là hệ thống mô phỏng 3D tương tác hỗ trợ dạy và học môn Hình học không gian cấp THPT (Toán 11–12) theo chương trình giáo dục phổ thông Việt Nam. Hệ thống tiếp nhận đề bài bằng ngôn ngữ tự nhiên (tiếng Việt) và hình ảnh, chuyển đổi thành các bước dựng hình hình học không gian trực quan, sinh cảnh 3D có thể tương tác xoay/tua, và kiểm chứng các tính chất hình học (thể tích, khoảng cách, góc) một cách chính xác tuyệt đối.

## 2. Mục Tiêu Khóa Luận
- **Đề tài:** Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian.
- **Trọng tâm nghiên cứu:** Giải quyết bài toán chuyển hóa từ đề bài tự nhiên sang mô phỏng trực quan đáng tin cậy. Thay vì để LLM trực tiếp tính toán tọa độ hay sinh code tự do (vốn dễ gây ảo giác và sai lệch hình học), đề tài nghiên cứu phân tách ranh giới rõ ràng: LLM chỉ chịu trách nhiệm bóc tách dữ kiện ngữ nghĩa có cấu trúc, còn toàn bộ việc dựng hình, tính toán đại số và kết xuất cảnh 3D do engine tất định đảm nhiệm.

## 3. Kiến Trúc Hiện Tại (Current Architecture)
- **Chế độ chạy mặc định:** `DEFAULT_MODE = LLM_ONLY`.
- **Luồng xử lý:**
  1. Đầu vào đề bài → Chuẩn hóa văn bản (`backend/app/ingestion/input.py`).
  2. `stage_semantic_analyze` (Gemini call #1): Bóc tách dữ kiện và nghĩa vụ hình học → Đóng băng thành `RequestContract` kèm `structured_relations`.
  3. `stage_semantic_program` (Gemini call #2): Tổng hợp chương trình ngữ nghĩa ứng viên (`SemanticProgramSpec`).
  4. Cổng tất định (`verify_and_compile`): Kiểm tra tĩnh, ràng buộc dữ kiện, thực thi tính toán tọa độ bằng số học chính xác (hữu tỉ + căn thức), và kiểm tra độ bao phủ trực quan (Visual Obligation Gate C1/C2).
  5. Frontend: Nhận `ValidatedSimulationEnvelope` và diễn hoạt trên Scene3D Explorer (Three.js).
- **Phân định:** Gemini **KHÔNG** làm toàn bộ pipeline; Gemini hiện bóc tách dữ kiện có cấu trúc và đề xuất bước dựng, còn engine tất định kiểm định và làm chủ tính toán.

## 4. Kiến Trúc Đích (Target Architecture: Compiler-First + Fallback)
- **Mục tiêu:** `COMPILER_FIRST` kết hợp `LLM_FALLBACK`.
- **Nguyên lý hoạt động:**
  - Sau khi Analyze trích xuất dữ kiện có cấu trúc, mạng dữ kiện `FactGraph` kiểm tra tính hợp lệ và xác định họ bài toán.
  - Nếu bài toán thuộc diện hỗ trợ (`eligible`) → Chuyển sang `primitive_compiler` để biên dịch trực tiếp ra chương trình ngữ nghĩa 100% tất định (0 call LLM synthesis, tiết kiệm token, loại bỏ hoàn toàn độ trễ và ảo giác).
  - Nếu bài toán nằm ngoài tập primitive đã hỗ trợ → Chuyển tiếp an toàn sang LLM synthesis fallback có kiểm soát.
  - **Lưu ý:** Kiến trúc đích này CHƯA được đặt làm mặc định; cần đạt đủ 20 cổng tại `docs/MIGRATION_CHECKLIST.md`.

## 5. Đã Chứng Minh (Empirical Evidence)
- Hợp đồng dữ kiện quan hệ có cấu trúc (`RequestContract.structured_relations`).
- Mạng quan hệ dữ kiện hình học `FactGraph`.
- Lát cắt dọc primitive compiler trên họ bài chóp đáy tam giác vuông (`right_triangle_base_pyramid_volume`).
- Tiền đăng ký họ bài hình học thứ hai: Lăng trụ đứng có đáy là tam giác vuông (`right_triangle_base_right_prism_volume`) với manifest 8 ca (5 dương, 3 âm), ground truth giải tích độc lập, gap audit cho `construct_prism` và nút `prism` trong `FactGraph` (`docs/PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION.md`).
- Đính chính và chuẩn hóa bằng chứng tiền đăng ký họ bài thứ hai (`docs/SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.md`): Phân loại CURRICULUM_EVIDENCE = NOT_ESTABLISHED_OFFLINE, tái tính ma trận lựa chọn thực chứng (Candidate B đạt 94.375% chuẩn hóa), vạch rõ 12 tầng kỹ thuật của vertical slice, và telemetry full backend cân bằng (6086 passed, 1 skipped, 1 deselected, exit code 0).
- Đối soát toàn diện danh tính mã nguồn và ranh giới kỹ thuật thật sự của họ lăng trụ (`docs/SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.md`): Đính chính điểm Candidate B: 95.5 / 100 (điểm đo 75.5 / 80 = 94.375%); xác định `primitives.py:REGISTRY` có đúng 6 hàm, `SourceInvariant` có 5 kind; IR (`construct_solid`), kernel và frontend được tái sử dụng nguyên trạng; xác định `RequestContract = CHANGE_REQUIRED` và bế tắc giữa Direction A (mở rộng schema, bump cache, unfreeze candidate, live revalidation) và Direction B (suy diễn nội bộ không đọc `problem_text`), dẫn đến `FINAL_DECISION = INCOMPLETE`, `VERTICAL_SLICE_ALLOWED = NO`.
- Hoàn thành lát cắt dọc Primitive Compiler cho họ lăng trụ đứng đáy tam giác vuông (`right_triangle_base_right_prism_volume`) offline (`docs/PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE.md`): 25/25 test prism mới, 41/41 test pyramid lịch sử, bump `CACHE_VERSION = 100`, khóa candidate mới.
- Đính chính và chuẩn hóa khớp nối benchmark tiền đăng ký họ bài thứ hai (`docs/SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE.md`): Sửa các sai lệch ghi nhầm trong báo cáo và artifact cũ (P02: 168, P04: 180, P05: 240); siết chặt 3 tầng kiểm thử cho N01–N03; 26/26 tests prism xanh; đo synthesis schema 0 hồi quy; xác lập 11 bước trace sư phạm.
- Tính đúng đắn tất định: kết quả topology, `final_memory` và đáp số thể tích đạt 100% qua các lần chạy lặp.
- Cổng kiểm định nghĩa vụ trực quan C1/C2 ngăn chặn hoàn toàn việc phát cảnh rỗng hoặc thiếu đối tượng.
- Chuẩn hóa provenance cho mặt cắt tiết diện.
- Diễn hoạt mượt mà trên trình duyệt desktop và mobile; Docker backend auto-refresh ổn định.

## 6. Chưa Làm & Vấn Đề Đang Mở (Open Items)
- Mở rộng coverage sang các họ hình học khác (lăng trụ khác, hộp, chóp đáy tứ giác, khối cong).
- Xây dựng router compiler-first và cơ chế fallback tự động.
- Triển khai canary deployment và circuit breaker rollback.
- Bộ giải bố cục không gian 3D tự động (spatial layout solver) và camera thông minh.
- Nhận diện nét khuất động học (dynamic hidden lines) theo góc xoay camera.
- Pipeline xử lý ảnh / OCR tự động từ ảnh chụp đề bài.
- Tối ưu hóa token production chưa được xác lập chính thức.
- Chưa có thử nghiệm sư phạm định lượng trên người học.

## 7. Ràng Buộc Cốt Lõi (Invariants & Constraints)
1. **Ranh giới R0:** LLM không bao giờ sở hữu runtime; không phát tọa độ, không sinh kết quả. Engine tất định sở hữu sự thật.
2. **Fail-closed:** Dữ kiện mâu thuẫn hoặc thiếu căn cứ → từ chối an toàn (`unsupported` / `inconsistent`), không đoán.
3. **Chế độ kiểm thử:** Mặc định 0 API call mạng; các wave kiểm thử và sửa lỗi là 100% offline.
4. **Không can thiệp candidate/cache bừa bãi:** Candidate hash và `CACHE_VERSION = 100` được bảo vệ bằng sync-lock.

## 8. Bước Tiếp Theo Duy Nhất (Single Canonical Next Action)
```text
CANONICAL_NEXT_ACTION = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
TARGET_NEXT_ACTION_AFTER_WAVE = SECOND_FAMILY_SEMANTIC_FAILURE_DIAGNOSIS_OFFLINE
```
- Chẩn đoán offline nguyên nhân mô hình trích xuất nhãn dữ kiện tự nhiên dẫn đến semantic extraction failure.
- Chi tiết các pha xem tại [`docs/ROADMAP.md`](ROADMAP.md).



## 9. Thứ Tự Đọc Bắt Buộc
1. `AGENTS.md` (Entry point)
2. `docs/RULES.md` (Quy tắc cứng)
3. `docs/AI_CONTEXT_BUNDLE.md` (File này)
4. `docs/CURRENT_STATE.md` (Trạng thái hiện tại)
5. `docs/OPEN_ISSUES.md` (Vấn đề đang mở)
6. `docs/ROADMAP.md` (Lộ trình P0–P6)
7. `docs/CODE_INDEX.md` (Chỉ mục mã nguồn)
8. `docs/EVIDENCE_INDEX.md` (Chỉ mục bằng chứng)
9. Code / Test liên quan trực tiếp.

## 10. Git Verification & Safety
- Không commit trực tiếp vào `main`, không push, không merge.
- Dùng Staging Allowlist: kiểm tra `git diff --cached --name-only` trước khi commit.
- Khi cần kiểm chứng authoritative, tạo git worktree detached sạch.

## 11. Chính Sách Correction Layer
- Báo cáo và artifact lịch sử là bất biến.
- Khi phát hiện sai lệch số liệu hoặc nhãn vai trò commit từ wave trước, tạo wave mới với lớp đính chính (correction layer), dẫn chứng bằng dữ liệu máy từ git/pytest và ghi nhận vào `docs/EVIDENCE_INDEX.md`.

## 12. Bảo Vệ Thay Đổi Của Người Dùng
- Working tree có thể có thay đổi xóa file `frontend/public/favicon.svg` của người dùng.
- Tuyệt đối **KHÔNG khôi phục, KHÔNG sửa, KHÔNG stage và KHÔNG commit** file này.
