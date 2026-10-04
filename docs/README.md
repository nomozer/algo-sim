# docs/ — cổng tài liệu

> Bắt đầu ở đây. Mỗi câu hỏi dưới đây có **một** nơi trả lời. Từ W19 (2026-10-04) `docs/` chia bốn vùng:
> **tài liệu dự án** ở gốc `docs/`, **nghiên cứu** ở [`research/`](research/), **bằng chứng** ở
> [`evaluation/`](evaluation/), **lưu trữ** ở [`legacy/`](legacy/). Gốc `docs/` là danh sách đóng — bộ kiểm
> `backend/scripts/audit_docs_information_architecture.py` (`audit_docs_layout`) từ chối file mới không được phân lớp.
> Nếu tài liệu mâu thuẫn với code hoặc test: **code/test thắng**.

## 0. Thứ tự đọc (agent và người mới)

[`../AGENTS.md`](../AGENTS.md) → [`RULES.md`](RULES.md) → [`AI_CONTEXT_BUNDLE.md`](AI_CONTEXT_BUNDLE.md) →
[`CURRENT_STATE.md`](CURRENT_STATE.md) → [`OPEN_ISSUES.md`](OPEN_ISSUES.md) → [`ROADMAP.md`](ROADMAP.md) →
[`CODE_INDEX.md`](CODE_INDEX.md) → [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) → code và test liên quan.

## 1. Hệ thống làm gì

- [`../README.md`](../README.md) — đề tài, nguyên lý R0 (*LLM đọc đề, engine tất định diễn hoạt*), demo, giới hạn.
- [`ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md) — hệ đang chạy: luồng từ đề tới cảnh 3D, ai sở hữu gì.
- [`CORRECTNESS.md`](CORRECTNESS.md) — đúng đắn chuẩn tắc (canonical) khác đúng đắn phía người học.
- [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md) — hệ **được phép nói** đã làm được gì, và giới hạn.

## 2. Kiến trúc và cách chạy

- [`ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md) — sở hữu, hướng phụ thuộc, bất biến đánh số, anti-pattern.
- [`architecture/`](architecture/README.md) — contract đang hiệu lực (chứng chỉ giả định, occlusion/scene identity) và
  snapshot kiểm kê năng lực (bất biến).
- [`OPERATIONS.md`](OPERATIONS.md) — cơ sở dữ liệu, migration, dependency, vòng sửa code.
- [`TEST_TIERS.md`](TEST_TIERS.md) — bốn tầng test; chỉ T3 được nói "sản phẩm xanh".
- [`DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md) — chạy buổi demo từ bản dựng, 0 lượt gọi model.
- [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md) — brief UI/UX (khác `../DESIGN.md` là token giao diện).
- [`MIGRATION_CHECKLIST.md`](MIGRATION_CHECKLIST.md) — 20 cổng trước khi đổi `LLM_ONLY` sang compiler-first.
- Lệnh chạy và kiểm thử: [`../README.md`](../README.md) §11.

## 3. Việc còn mở

- [`CURRENT_STATE.md`](CURRENT_STATE.md) — trạng thái và con trỏ: danh tính kho mã (sync-lock), cơ sở, wave cuối.
- [`ROADMAP.md`](ROADMAP.md) §0 — **việc kế tiếp duy nhất** (`CANONICAL_NEXT_ACTION`), việc chặn merge, hàng đợi;
  [`POST_THESIS_BACKLOG.md`](POST_THESIS_BACKLOG.md) là phụ lục của ROADMAP cho ý tưởng ngoài phạm vi khoá luận.
- [`OPEN_ISSUES.md`](OPEN_ISSUES.md) — vấn đề đang mở: mô tả, ảnh hưởng, điều kiện đóng (`ISSUE-*`).

## 4. Khoá luận và bài báo

- [`research/README.md`](research/README.md) — cổng nghiên cứu: phương pháp, tài liệu tham khảo, khoá luận, bài báo.
- [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md) — **thẩm quyền duy nhất** tuyên bố ↔ bằng chứng ↔ giới
  hạn, kèm mức (PLANNED/IMPLEMENTED/MEASURED/HUMAN_REVIEWED) và mục khoá luận/bài báo dùng được.
- [`research/thesis/`](research/thesis/) — bản thảo, chương 4–5, tài liệu tham khảo, hình.
- [`research/paper/`](research/paper/) — đánh giá sẵn sàng bài báo.

## 5. Bằng chứng theo hạng mục

- [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) — **thẩm quyền**: wave → báo cáo → artifact → chuỗi đính chính
  (`CORRECTED_BY`).
- [`evaluation/README.md`](evaluation/README.md) — cách tổ chức run, đặt tên, run mới nhất.
- [`evaluation/HISTORICAL_REPORTS.md`](evaluation/HISTORICAL_REPORTS.md) — báo cáo wave cũ ở gốc `docs/` theo chủ đề
  (danh sách đóng; bất biến, đọc như bằng chứng tại thời điểm đo).
- [`STATUS_LEDGER.md`](STATUS_LEDGER.md) — lịch sử các wave theo thời gian.
- Run mới nhất: [`w20-cleanup-premerge`](evaluation/geometry/runs/w20-cleanup-premerge/) (đóng tính đúng trước merge,
  dọn kho) · [`w19-docs-organization`](evaluation/geometry/runs/w19-docs-organization/) (tổ chức tài liệu) ·
  [`w18-binding-focus`](evaluation/geometry/runs/w18-binding-focus/) (hình ảnh hiện hành, chờ người duyệt).

## 6. Mỗi loại thông tin — một nơi có thẩm quyền

| thông tin | nơi | không đặt ở |
|---|---|---|
| trạng thái hiện tại + con trỏ | `CURRENT_STATE.md` | README, báo cáo wave |
| vấn đề mở, ảnh hưởng, điều kiện đóng | `OPEN_ISSUES.md` | ROADMAP |
| việc tương lai, thứ tự | `ROADMAP.md` (+ phụ lục `POST_THESIS_BACKLOG.md`) | CURRENT_STATE |
| mã, vai trò, producer → consumer | `CODE_INDEX.md` | tài liệu kiến trúc |
| bằng chứng, chuỗi đính chính | `EVIDENCE_INDEX.md` | STATUS_LEDGER |
| lịch sử wave (không chép báo cáo) | `STATUS_LEDGER.md` | CURRENT_STATE |
| nguyên tắc, contract | `ARCHITECTURE_MAP.md`, `architecture/` | bảng test |
| tuyên bố khoá luận/bài báo | `research/CLAIM_EVIDENCE_MAP.md` | README, bản thảo |
| báo cáo của một wave | thư mục run của wave đó | gốc `docs/` |

## 7. Lưu trữ

[`legacy/README.md`](legacy/README.md) — tài liệu hết hiệu lực nhưng đáng giữ: kế hoạch/spec của skill, tài liệu giai
đoạn chuyển đề, quyết định đã thực thi, nhật ký phát triển cũ của CURRENT_STATE, ba bảng tuyên bố cũ. **Không** dùng
làm căn cứ hiện hành. Khi tìm luật hay trạng thái hiện hành, loại `docs/legacy/` và `docs/evaluation/` khỏi grep.
Đường dẫn cũ của file đã di chuyển ở W19: [`MIGRATION_MAP.json`](evaluation/geometry/runs/w19-docs-organization/inventory/MIGRATION_MAP.json).
Mục đã xoá ở W20 (bản trùng hoặc tái tạo được, kèm cách khôi phục): [`DELETION_LOG.json`](evaluation/geometry/runs/w20-cleanup-premerge/inventory/DELETION_LOG.json).

## 8. Thêm tài liệu mới

- Báo cáo wave: `REPORT.md`/`HANDOFF.md` trong thư mục run ([`evaluation/RUN_NAMING.md`](evaluation/RUN_NAMING.md)),
  **không** ở gốc `docs/`.
- Tài liệu dự án mới ở gốc: thêm tên vào `PROJECT_DOCS` của bộ kiểm, kèm lý do.
- Báo cáo và artifact đã commit là bất biến: đính chính bằng wave mới và `CORRECTED_BY`.
