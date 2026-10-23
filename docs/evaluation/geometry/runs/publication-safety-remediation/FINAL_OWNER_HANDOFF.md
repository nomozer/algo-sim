# Handoff cho Owner: Session 5 post-main remediation

Authorization `GO_SESSION5_POST_MAIN_REMEDIATION_LOCAL_ONLY`. 2026-10-23. Provider calls 0. Không push, không rewrite,
không bật production. **Dừng ở đây để Owner quyết định.**

| trục | phân loại |
|---|---|
| Remote | **`REMOTE_SECURITY_BLOCKED`**: [`REMOTE_PUBLICATION_SECURITY_DECISION.md`](REMOTE_PUBLICATION_SECURITY_DECISION.md) |
| Giao diện | **`VISUAL_FIX_REQUIRED`**: [`VISUAL_ACCEPTANCE_REVIEW.md`](VISUAL_ACCEPTANCE_REVIEW.md); human approval `PENDING` |
| Dọn dẹp | **`CLEANUP_ADMIN_REQUIRED`**: [`ACL_CLEANUP_PLAN.md`](ACL_CLEANUP_PLAN.md); thu hồi thực tế 0 B |

## Danh tính

- Local `main` = `b4ac5e879b35ac3605ba75c51df5bb6b89352734` (không đổi trong lượt này).
- Nhánh `research/publication-safety-remediation` (từ `main`), **chưa merge**:
  `76c6795c37569aebcf41c0d22ffbe0d8268872d9` (tooling, T3 target) → commit docs ngay sau nó (commit ghi file này;
không tự ghi SHA của chính mình).
- Worktree dùng: `.superpowers/worktrees/hybrid-session5-offline-consumer` (dùng lại, không tạo mới).
  Nhánh `research/hybrid-session5-offline-consumer` = `b4ac5e87` được giữ.
- `origin/main` = `43247c9e…` (không đổi). Root checkout: 27 mục bẩn như cũ, không bị đụng.
- Bất biến: `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI=0`, `CACHE_VERSION=127`, `MAX_MEMORY_DECLARATIONS=32`;
  `backend/app` không đổi.

## Owner cần quyết

1. **Ngoại lệ lịch sử**: duyệt hay từ chối từng entry trong `publication_exceptions.json` (27 entry; Owner tự ghi
   `APPROVED_BY_USER`), và sửa hay diễn giải AGENTS.md §4. Hồ sơ:
   [`HISTORICAL_TRACEBACK_EXCEPTION_PROPOSAL.md`](HISTORICAL_TRACEBACK_EXCEPTION_PROPOSAL.md).
2. **Merge** nhánh remediation vào `main` (local), sau khi đọc diff.
3. **Push**: chỉ sau 1, 2, gate exit 0, và một GO riêng.
4. **Sửa A/B giao diện**: mở task riêng (backend `backend/app`, cần chạy đủ pipeline candidate), hoặc chấp nhận như hiện trạng.
5. **Duyệt hình**: 6 ảnh Session 5 và 20 ảnh màn từ chối.
6. **Dọn dẹp bằng admin** theo `ACL_CLEANUP_PLAN.md` §3.
7. **Chép bản bảo toàn offline ra thiết bị độc lập** (hiện cùng SSD).

## Kết quả kiểm

| kiểm | kết quả |
|---|---|
| Full T3 tại `76c6795c` | `FULL_PRODUCT_GATE_PASS`: pytest 11,586 / vitest 1,238 / build / demo 5/5 / crash 6/6; freeze MATCH ([`POST_MAIN_REGRESSION_REPORT.md`](POST_MAIN_REGRESSION_REPORT.md)) |
| gate xuất bản, repo thật | BLOCKED: mọi vi phạm thuộc 27 entry PENDING, 0 vi phạm mới (log trong `gate-runs/`) |
| gate, cơ chế | 12 test xanh; 3 phép tiêm lỗi đều làm test đỏ |
| màn từ chối | 50/50 PASS, 20 ảnh, `tree_clean: true` |
| bản bảo toàn offline | bundle + blob gốc có SHA-256, `git bundle verify` OK. **Cùng một SSD**, nên không chống hỏng ổ |
| dung lượng thu hồi | **0 B** (không xoá gì) |

Hai lượt T3 bị bỏ và lý do (chạy nhầm thư mục; agent ghi vào worktree giữa lượt đo) được khai ở
`POST_MAIN_REGRESSION_REPORT.md` §3.

Phát hiện phụ khi quét: 10 vector test hoặc placeholder trông giống credential, đã công khai từ trước (`.env.example`,
test của các bộ quét secret, mật khẩu fixture). Phân tích hình dạng chuỗi (không in giá trị) cho thấy không có key thật,
nhưng Owner vẫn phải duyệt chúng như các entry khác. Nếu muốn loại hẳn, có thể đổi các test đó sang ghép vector lúc chạy.
