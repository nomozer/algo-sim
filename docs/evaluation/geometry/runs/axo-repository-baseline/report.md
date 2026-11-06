# Axo — repository baseline after the Hybrid + branding merge

Run `axo-repository-baseline` · 2026-11-07 · trên `main` · 0 lượt gọi provider · không đổi mã sản phẩm.

## 1. `main`

| | trước | sau |
|---|---|---|
| `main` | `64847c1e` | `3a8a2f31` + commit tài liệu của run này |
| `origin/main` | `64847c1e` | `3a8a2f31` (`git ls-remote` khớp local), rồi commit tài liệu này (push thường) |

`3a8a2f31` = `git merge --no-ff` nhánh `chore/axo-postmerge-branding-consolidation` (`7976cd2e`). Merge được mô phỏng trước
trong worktree tạm: cây merge `42571f08` = cây nhánh (đã qua T3 tại `14810326`, sau đó chỉ đổi docs); seal khớp với merge commit
(`product_commit` vẫn `9904265b`). Không force push, không viết lại lịch sử.

Kiểm sau merge trên `main`: publication `--range 64847c1e..3a8a2f31` PASS (141 blob, 5 thông điệp, 0 vi phạm); seal MATCH
(103 file, `09c1a089`); docs IA + candidate + identity 71/71; branding vitest 26/26; `tsc -b` + `vite build` PASS; Chrome thật:
branding 9/9 (tiêu đề `Axo — Mô phỏng tương tác`, `/favicon.svg` 200), camera Scene3D 10/10 (1440×900).

## 2. Branch

| branch | phân loại | xử lý |
|---|---|---|
| `chore/axo-postmerge-branding-consolidation` | đã merge (tổ tiên của `origin/main`) | **đã xoá** (`git branch -d`) |
| `research/scene3d-hybrid-v2-codex`, `research/scene3d-owner-math-visual-final`, `research/scene3d-to-hybrid-v2-replacement` | đã merge theo lịch sử, không worktree | **đã xoá** (`git branch -d`) |
| `integration/axo-hybrid4-reliability` | tích hợp bằng squash (cây = cây squash `9eb132ff`); 146 commit chỉ có ở đây; chứa 3 blob bị đánh dấu | **giữ local, không push** — bundle hợp lệ nhưng chỉ nằm trên cùng ổ vật lý; `EVIDENCE_INDEX` trích các commit này |
| `integration/axo-pedagogical-construction-hardening` | tổ tiên của nhánh trên (tích hợp qua squash); hơn `origin/` 23 commit | giữ — worktree có thay đổi chưa commit |
| `feat/axo-v27-frontend-integration` | tổ tiên của nhánh tích hợp | giữ — worktree có thay đổi chưa commit |
| `research/hybrid-v2-w3-f2-ratio-projection-language-grounding` | đã merge | giữ — worktree của nó chưa gỡ được (§3) |
| `feat/real-model-pilot-tooling` | chưa tích hợp; hơn `origin/` 1 commit | giữ (commit độc nhất) |
| `research/compact-geometry-dsl` (8), `research/hybrid-semantic-extraction-v2` (14), `research/hybrid-v2-independent-vietnamese-section-holdout` (4), `research/hybrid-next-architecture-gap-audit` (1), `research/nl-to-scene3d-e2e-readiness` (1) | chưa tích hợp (số commit ngoài `main`) | giữ |
| nhánh remote (`docs/real-model-e2e-readiness`, `feat/real-model-pilot-tooling`, `integration/axo-pedagogical-construction-hardening`, `research/scene3d-section-inspector-c0`) | trên GitHub | không đụng (xoá remote không thuộc quyền của task) |

## 3. Worktree

| worktree | trạng thái | xử lý |
|---|---|---|
| `axo-performance-verifier`, `independent-section-holdout` | sạch; HEAD giữ bởi nhánh còn lại | `algosim.db` lưu trữ (SHA-256 OK), gỡ junction, `git worktree remove` (không `--force`): **đã gỡ hết** |
| `axo-performance-baseline`, `w3-f2-…/w3-f2-target-grammar-identity-compat` | sạch | gỡ đăng ký thành công nhưng git dừng khi xoá thư mục (`Invalid argument` / `Permission denied`). Phần còn lại kiểm từng file: 281 + 26 308 file trùng blob của commit, 1 trùng lưu trữ, 342 cache, **0 file lạ** — thư mục giữ nguyên (xoá cần lệnh đệ quy, bị cấm) |
| `w3-f2-adapter3-t3`, `w3-f2-solid-scope-t3`, `w3-f2-unified-scope-t3`, `w3-f2-ratio-projection-language-grounding` | sạch, HEAD trong `main` | **giữ**: `.superpowers/` bị ignore chứa log (vd `adapter3-*.log`) và thư mục tạm bị ACL chặn đọc (sandbox Codex) ⇒ không kiểm/lưu trữ được, và `git worktree remove` sẽ dừng giữa chừng |
| `axo-pedagogical-integration` | `frontend/index.html` sửa chưa commit + 287 file chưa theo dõi | giữ (thay đổi của người dùng) |
| `axo-v27-frontend-integration` | `frontend/index.html` sửa chưa commit; `node_modules` thật (từng là đích junction của worktree khác) | giữ |
| `.superpowers/worktrees/axo-hybrid4-integration/` (không đăng ký) | 27 576 file đã kiểm, 0 file lạ | giữ — `BACKUP_REQUIRED` |
| 10 thư mục không đăng ký khác (`hm-t3-7e9e479d`, `hybrid-master-backend-replacement`, `hybrid-primary-b1-b2-offline`, `hybrid-session5-offline-consumer`, `planner-generalization`, `ratio-projection-publication-verification`, `source-gate-language-generalization`, `source-gate-language-t3`, `w4-geometry-pedagogy`, `windows-watchdog-recovery`) | từ phiên trước, chưa kiểm | giữ, chưa phân loại nội dung |

Không có worktree nào hoạt động gần đây (index mới nhất trước run là 11-06 23:57, của merge).

## 4. Bảo toàn

Kho riêng tư `algo-sim-private-archive/` (cạnh thư mục kho, không tải lên đâu), kiểm lại toàn bộ trong run này:

| mục | SHA-256 |
|---|---|
| `axo-hybrid4-integration-2026-11-07` | 947/947 OK; bundle `939b4cff…` `git bundle verify` OK (khôi phục thử ra `c7ae6947` ở run trước) |
| `axo-postmerge-consolidation-2026-11-07` | 9/9 OK |
| `worktree-cleanup-2026-11-07/*` (3 × `algosim.db`) | 3/3 OK |

Máy chỉ có **một ổ vật lý** (C: và D: cùng NVMe 0) ⇒ chưa có bản độc lập ⇒ `BACKUP_REQUIRED`.

## 5. Tài liệu / branding

- `CURRENT_STATE.md`: dòng tích hợp 2026-11-07. `AI_CONTEXT_BUNDLE.md §2`: dòng `AXO` (bỏ "seal đỏ… NOT merged").
- `CLAUDE.md` (cục bộ, bị gitignore, không commit): bỏ chỉ dẫn cũ "`index.html` dùng icon rỗng `data:,`".
- `frontend/index.html` trên `main`: `<link rel="icon" type="image/svg+xml" href="/favicon.svg" />`, `<title>Axo — Mô phỏng tương tác</title>`. Không đổi branding.

## 6. Rủi ro còn mở

1. `BACKUP_REQUIRED`: cần phương tiện ngoài cho `algo-sim-private-archive/` trước khi xoá thư mục tồn dư hay nhánh tích hợp.
2. `POSTGRES_NOT_TESTED`; production chưa chạy `alembic upgrade head` (`e437149641fa`).
3. Publication toàn cây: 97 `PENDING_OWNER_DECISION` có từ trước; không mục mới.
4. 13 thư mục tồn dư không đăng ký (`axo-hybrid4-integration`, 2 thư mục gỡ dở ở run này, 10 thư mục cũ) và 6 worktree giữ lại
   (§3) — cần quyết định của chủ kho hoặc một lần xoá đệ quy có kiểm.

## 7. Kết luận

Trạng thái: **BASELINE_READY_WITH_RETAINED_ITEMS** (không phải CLEAN). Task tiếp theo rẽ nhánh từ `main` `origin/main` mới; không phụ
thuộc worktree hay thư mục cũ nào.
