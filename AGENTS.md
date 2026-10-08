# AGENTS.md — AlgoSim Agent Entry Point & Safety Rules

> **Entry Point duy nhất cho Coding Agents và AI Sessions.**
> File này là cổng định hướng ngắn gọn. Tài liệu quy tắc ổn định và chi tiết là [`docs/RULES.md`](docs/RULES.md).
> Tài liệu mâu thuẫn với code hoặc test thật: theo luật **CODE/TESTS** ở [`docs/RULES.md §1`](docs/RULES.md).

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
- **Nhánh & Lịch sử:** Làm việc trên nhánh được chỉ định. Mặc định **không merge vào `main`** và **không push**. Chỉ khi user cho phép rõ ràng **và** mọi điều kiện nghiệm thu của task đã đạt mới merge thẳng vào `main`, push `main` và xoá nhánh đã merge. Không bao giờ **rewrite lịch sử** (`git commit --amend` trên commit đã công bố, `git rebase`, force-push).
- **Kiểm chứng độc lập:** Khi cần xác minh có thẩm quyền (authoritative verification), tạo git worktree detached sạch tại commit tương ứng.
- **Việc mới, nhánh mới, wave từ W1:** việc mới chỉ rẽ nhánh từ `main` đã tích hợp và cập nhật; run mới đặt tên theo việc, không mã lượt (`exact-dimensions`, `repo-cleanup`; lần thực hiện thứ hai của cùng việc thêm ngày), mã việc/lượt, ngày, commit nằm trong `run.json`; run cũ `<task-slug>-wNN` giữ tên. Không bao giờ `W1`/`W2` trần trong manifest hay chỉ mục. Luật đầy đủ (gồm tên file/thư mục): [`docs/evaluation/RUN_NAMING.md`](docs/evaluation/RUN_NAMING.md).

---

## 3. Architecture & Product Safety

- **Ranh giới LLM và Tất định:** LLM chỉ trích xuất ngữ nghĩa và cấu trúc dữ kiện (`RequestContract`). Engine tất định sở hữu hoàn toàn trạng thái, tọa độ và tính toán hình học.
- **Không hardcode:** Tuyệt đối không hardcode case ID, nhãn đỉnh, dữ kiện đề bài, hoặc đáp số kỳ vọng vào mã sản phẩm.
- **Fail-closed:** Bất kỳ mâu thuẫn dữ kiện nào trong đề bài phải dẫn đến từ chối an toàn (`unsupported` / `inconsistent`), không xấp xỉ gây hiểu lầm.
- **Chế độ mặc định:** Mặc định của sản phẩm hiện tại vẫn là `LLM_ONLY`. Tuyệt đối không tự ý đổi default mode sang compiler-first khi chưa vượt qua đủ 20 cổng tại [`docs/MIGRATION_CHECKLIST.md`](docs/MIGRATION_CHECKLIST.md).

---

## 4. Evidence & Documentation Safety

- **Bằng chứng còn được sử dụng phải giữ nguyên nội dung:** Không sửa byte của kết quả đo, input/output, manifest hoặc báo cáo đang làm căn cứ cho sản phẩm, nghiên cứu hiện hành hay khả năng tái lập đã cam kết. Được đổi tên/chuyển file hoặc folder khi cập nhật đồng bộ consumer, manifest và index; run ID giữ trong metadata khi cần. Được xoá tài liệu/artifact đã đọc và xác minh không còn phục vụ ba mục đích trên. Nhãn `historical`/`frozen` hoặc một test pin, tự nó, không phải lý do giữ; việc xoá phải có inventory, kiểm tham chiếu và đường khôi phục bằng commit Git.
- **Nháp của công cụ agent không tự động là bằng chứng bất biến:** plan, brief, report, ledger và gói review do skill/agent sinh (`.superpowers/` — nháp local, gitignore).
- **Kế hoạch/spec của skill theo cấu trúc dự án:** thiết kế là contract đang hiệu lực ⇒ `docs/architecture/`; kế hoạch triển khai ⇒ `plan.md` trong thư mục run của việc. Không tạo `docs/superpowers/` hay thư mục tài liệu mới; không nhân bản một kế hoạch ở nhiều nơi. Chi tiết: [`docs/README.md`](docs/README.md) §8.
- **Dọn có kiểm:** bản trùng, plan bỏ dở, bằng chứng hết consumer và tài liệu ngoài phạm vi được xoá sau khi đọc nội dung, kiểm mọi tham chiếu (code, test, tooling, docs, manifest) và chuyển thông tin duy nhất sang tài liệu có thẩm quyền kèm nguồn; nhóm trộn phải xử lý từng phần; xoá theo đường dẫn chính xác, ghi nhật ký xoá.
- **Test không ghi vào bằng chứng đông cứng:** output tái sinh đi vào thư mục tạm hoặc một run mới.
- **Phê duyệt là của người:** tự động hoá (script, test, agent) không bao giờ ghi `APPROVED_BY_USER`.
- **Báo cáo wave mới nằm trong thư mục run** (`docs/evaluation/geometry/runs/<run>/`), không ở gốc `docs/`. Gốc `docs/` là danh sách đóng: tài liệu chuẩn tắc, tài liệu dự án, và các báo cáo cũ trong [`docs/evaluation/HISTORICAL_REPORTS.md`](docs/evaluation/HISTORICAL_REPORTS.md) — bộ kiểm tài liệu đỏ với file chưa phân lớp. Cổng điều hướng: [`docs/README.md`](docs/README.md).
- **Correction Layer:** Khi phát hiện báo cáo cũ có sai sót hoặc cần đính chính cách diễn giải, tạo một wave mới với lớp đính chính (correction layer) và đăng ký chuỗi `CORRECTED_BY` vào [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md).
- **Tính trung thực của bằng chứng:**
  - Dữ liệu thiếu hoặc lỗi đo lường phải ghi rõ `UNKNOWN` hoặc `NOT_RECOVERABLE`, không được gán bằng `0`.
  - Không nâng mối tương quan (association) thành quan hệ nhân quả (causality).
  - Khẳng định `PROVED` bắt buộc phải có hash bằng chứng máy đi kèm.
- **Bảo mật & Tối giản:** Không lưu API key, token bí mật, traceback thô hoặc model output raw vào tài liệu hay git tree.
- **Đo lường có trần:** Mọi request live ra provider bên ngoài phải đăng ký trước ngân sách và luật dừng bắt buộc.
