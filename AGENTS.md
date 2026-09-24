# AGENTS.md — AlgoSim Agent Entry Point & Safety Rules

> **Entry Point duy nhất cho Coding Agents và AI Sessions.**
> File này là cổng định hướng ngắn gọn. Tài liệu quy tắc ổn định và chi tiết là [`docs/RULES.md`](docs/RULES.md).
> Nếu tài liệu mâu thuẫn với code hoặc test thật: **CODE/TESTS THẮNG**.

---

## 1. Thứ Tự Đọc Bắt Buộc Trước Mọi Thay Đổi

1. **File này (`AGENTS.md`)** — Quy tắc an toàn và bootstrap.
2. **[`docs/RULES.md`](docs/RULES.md)** — Quy tắc cứng, scope guard, checklist chống viết trùng.
3. **[`docs/AI_CONTEXT_BUNDLE.md`](docs/AI_CONTEXT_BUNDLE.md)** — Bản tóm tắt ngữ cảnh bàn giao phiên (handoff).
4. **[`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md)** — Cơ sở sản phẩm, trạng thái kiến trúc, mốc đã chứng minh.
5. **[`docs/OPEN_ISSUES.md`](docs/OPEN_ISSUES.md)** — Các vấn đề kỹ thuật đang mở.
6. **[`docs/ROADMAP.md`](docs/ROADMAP.md)** — Lộ trình ưu tiên khóa luận (P0–P6).
7. **[`docs/CODE_INDEX.md`](docs/CODE_INDEX.md)** — Tra cứu vị trí module / tooling / test đã có (chống viết trùng).
8. **[`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md)** — Tra cứu báo cáo và artifact kiểm chứng.
9. **Code và Test thực tế liên quan trực tiếp.**

---

## 2. Git & Working Tree Safety

- **Bảo toàn thay đổi của người dùng:** Tuyệt đối không sửa, khôi phục (restore), stage hoặc commit bất kỳ thay đổi nào của người dùng ngoài phạm vi nhiệm vụ được giao. Mọi trạng thái working tree chưa commit của người dùng phải được giữ nguyên.
- **Staging Allowlist:** Luôn dùng `git add <từng file cụ thể>`. Tuyệt đối không dùng `git add .` hoặc `git add -A`. Trước khi commit, kiểm tra `git diff --cached --name-only`.
- **Nhánh & Lịch sử:** Làm việc trên nhánh được chỉ định. Tuyệt đối **không merge vào `main`**, **không push**, và **không rewrite lịch sử** (`git commit --amend` trên commit đã công bố, `git rebase`).
- **Kiểm chứng độc lập:** Khi cần xác minh có thẩm quyền (authoritative verification), tạo git worktree detached sạch tại commit tương ứng.

---

## 3. Architecture & Product Safety

- **Ranh giới LLM và Tất định:** LLM chỉ trích xuất ngữ nghĩa và cấu trúc dữ kiện (`RequestContract`). Engine tất định sở hữu hoàn toàn trạng thái, tọa độ và tính toán hình học.
- **Không hardcode:** Tuyệt đối không hardcode case ID, nhãn đỉnh, dữ kiện đề bài, hoặc đáp số kỳ vọng vào mã sản phẩm.
- **Fail-closed:** Bất kỳ mâu thuẫn dữ kiện nào trong đề bài phải dẫn đến từ chối an toàn (`unsupported` / `inconsistent`), không xấp xỉ gây hiểu lầm.
- **Chế độ mặc định:** Mặc định của sản phẩm hiện tại vẫn là `LLM_ONLY`. Tuyệt đối không tự ý đổi default mode sang compiler-first khi chưa vượt qua đủ 20 cổng tại [`docs/MIGRATION_CHECKLIST.md`](docs/MIGRATION_CHECKLIST.md).

---

## 4. Evidence & Documentation Safety

- **Tính bất biến của lịch sử:** Báo cáo (`docs/*.md`) và artifact (`docs/evaluation/**`) từ các wave trước là bất biến. Không được sửa, di chuyển hoặc xóa.
- **Correction Layer:** Khi phát hiện báo cáo cũ có sai sót hoặc cần đính chính cách diễn giải, tạo một wave mới với lớp đính chính (correction layer) và đăng ký chuỗi `CORRECTED_BY` vào [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md).
- **Tính trung thực của bằng chứng:**
  - Dữ liệu thiếu hoặc lỗi đo lường phải ghi rõ `UNKNOWN` hoặc `NOT_RECOVERABLE`, không được gán bằng `0`.
  - Không nâng mối tương quan (association) thành quan hệ nhân quả (causality).
  - Khẳng định `PROVED` bắt buộc phải có hash bằng chứng máy đi kèm.
- **Bảo mật & Tối giản:** Không lưu API key, token bí mật, traceback thô hoặc model output raw vào tài liệu hay git tree.
- **Đo lường có trần:** Mọi request live ra provider bên ngoài phải đăng ký trước ngân sách và luật dừng bắt buộc.
