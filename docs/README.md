# AlgoSim Documentation Hub

> **Cổng điều hướng tài liệu trung tâm của dự án AlgoSim.**
> Hệ thống tài liệu được tổ chức theo 11 information domain chuẩn tắc. Bắt đầu từ mục **Start Here** bên dưới.

---

## 1. Start Here (Bắt Đầu Từ Đây)
- [`AGENTS.md`](../AGENTS.md) — Điểm truy cập nhanh cho AI sessions và Coding Agents (quy tắc an toàn, thứ tự đọc, bảo vệ working tree).
- [`docs/RULES.md`](RULES.md) — Quy tắc phát triển cứng, phân loại phạm vi (Scope Guard: Core, Supporting, Deep Hardening, Out of Scope), checklist chống viết trùng.
- [`docs/AI_CONTEXT_BUNDLE.md`](AI_CONTEXT_BUNDLE.md) — Bản tóm tắt ngữ cảnh cô đọng (<= 300 dòng) dành cho bàn giao phiên làm việc mới.

## 2. Current State & Baseline (Trạng Thái Hệ Thống)
- [`docs/CURRENT_STATE.md`](CURRENT_STATE.md) — Nguồn sự thật canonical về trạng thái triển khai, cơ sở kho mã (`PRODUCT_AND_EVIDENCE_BASE_HEAD`), sync-lock danh tính runtime và các năng lực hình học đã chứng minh.
- [`docs/MIGRATION_CHECKLIST.md`](MIGRATION_CHECKLIST.md) — 20 cổng kiểm soát điều kiện cần và đủ trước khi chuyển giao từ `LLM_ONLY` sang `COMPILER_FIRST`.

## 3. Architecture & Design (Kiến Trúc & Thiết Kế)
- [`docs/ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md) — Bản đồ kiến trúc hệ thống, luồng xử lý từ input → Analyze LLM → FactGraph → Primitive Compiler / LLM Synthesis → Visual Obligation Gate → Scene3D Replay.
- [`docs/CORRECTNESS.md`](CORRECTNESS.md) — Mô hình đúng đắn giữa hệ thống chuẩn (canonical) và người học (learner).
- [`docs/COVERAGE.md`](COVERAGE.md) — Nguyên tắc sư phạm, phạm vi phủ chương trình và các tuyên bố bị cấm.

## 4. Planning & Issues (Kế Hoạch & Vấn Đề Đang Mở)
- [`docs/ROADMAP.md`](ROADMAP.md) — Lộ trình ưu tiên khóa luận phân tầng từ P0 đến P6, chứa bước tiếp theo duy nhất (`CANONICAL_NEXT_ACTION`).
- [`docs/OPEN_ISSUES.md`](OPEN_ISSUES.md) — Danh mục theo dõi các vấn đề kỹ thuật đang mở với mã định danh ổn định (`ISSUE-ARCH-*`, `ISSUE-EVAL-*`, etc.).

## 5. Indexes & Memory (Chỉ Mục & Bộ Nhớ Kiến Trúc)
- [`docs/CODE_INDEX.md`](CODE_INDEX.md) — Chỉ mục toàn bộ module mã nguồn, tooling, test và lịch sử các thành phần đã gỡ (ngăn chặn viết trùng helper hoặc phá vỡ abstraction sẵn có).
- [`docs/STATUS_LEDGER.md`](STATUS_LEDGER.md) — Sổ trạng thái theo thời gian ghi nhận lịch sử các wave phát triển và đánh giá.
- [`docs/EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) — Chỉ mục bằng chứng đánh giá, báo cáo nghiệm thu và chuỗi đính chính (correction chains).

## 6. Historical Reports & Artifacts (Báo Cáo & Dữ Liệu Lịch Sử)
- **Thư mục báo cáo lịch sử:** Các file báo cáo riêng lẻ trong `docs/*.md` ghi nhận từng wave phát triển cụ thể. Chúng là bằng chứng lịch sử bất biến.
- **Thư mục dữ liệu máy:** `docs/evaluation/` chứa toàn bộ artifact JSON, telemetry máy, JUnit XML và contact sheet kiểm chứng qua từng thời kỳ.
- **Quy tắc tra cứu:** Không tra cứu ngẫu nhiên hàng trăm file báo cáo; luôn tra cứu thông qua [`docs/EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) và [`docs/STATUS_LEDGER.md`](STATUS_LEDGER.md).

## 7. Thesis-Facing Evidence (Bằng Chứng Phục Vụ Khóa Luận)
- [`docs/THESIS_READINESS.md`](THESIS_READINESS.md) — Ma trận tổng thể đối chiếu giữa Tuyên bố ↔ Bằng chứng ↔ Giới hạn của đề tài.
- [`docs/THESIS_ARCHITECTURE.md`](THESIS_ARCHITECTURE.md) — Kiến trúc tổng thể và các ranh giới lý thuyết phục vụ viết chương kiến trúc trong khóa luận.
- [`docs/thesis/`](thesis/) — Bản thảo các chương khóa luận và ma trận trích dẫn nghiên cứu liên quan.
