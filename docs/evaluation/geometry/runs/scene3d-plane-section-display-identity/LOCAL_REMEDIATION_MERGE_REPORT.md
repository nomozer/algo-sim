# Merge remediation vào local main

**Đã merge, fast-forward, trạng thái tắt.** Không push, không rebase/rewrite/force. Remote: `REMOTE_SECURITY_BLOCKED`.

| mục | giá trị |
|---|---|
| `main` trước | `b4ac5e879b35ac3605ba75c51df5bb6b89352734` |
| nhánh | `research/publication-safety-remediation` = `50cee9035d664d7d3d39762610af740a8b8cd558` |
| ancestry | `main` ⊂ nhánh; 2 commit (`76c6795c` tooling + gỡ log khỏi tip, `50cee903` docs); 0 thay đổi `backend/app`/`frontend/src` |
| checkout dùng để merge | worktree `.superpowers/worktrees/hybrid-session5-offline-consumer`, tracked sạch trước và sau |
| lệnh | `git switch main` → `git merge --ff-only research/publication-safety-remediation` |
| `main` sau | **`50cee9035d664d7d3d39762610af740a8b8cd558`** (reflog `main@{0}: merge …: Fast-forward`) |
| `origin/main` | `43247c9e…` (không đổi) |
| root checkout | không đụng (27 mục bẩn như cũ) |

## Kiểm sau merge

| kiểm | kết quả |
|---|---|
| `freeze_evaluation_candidate.py --verify` | exit 0, MATCH (116 file, `413ee525…`) |
| docs IA + `test_current_state_identity` + `test_evaluation_candidate` + `test_publication_safety_gate` | exit 0, 83 passed |
| gate `--head` | BLOCKED, 105 dòng, tất cả thuộc entry PENDING, 0 mới (dự kiến; không sửa test cho xanh) |
| gate `--range origin/main..main` | BLOCKED, 5 dòng (`8a515fef`), PENDING, 0 mới |
| `publication_exceptions.json` | 27/27 `PENDING_OWNER_DECISION`, không sửa |

Sau đó worktree chuyển sang nhánh mới `research/scene3d-plane-section-display-identity`, nên `main` không còn checkout ở đâu.
