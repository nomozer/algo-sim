# Axo — dọn branch, worktree và thư mục tồn dư

Run `axo-git-cleanup` · 2026-11-07 · trên `main` · 0 lượt gọi provider · không đổi mã sản phẩm, không chạy lại test sản phẩm.

Kết luận: **CLEANUP_COMPLETED_WITH_BLOCKERS**. Blocker còn lại: quyền ACL do sandbox Codex để lại (không đổi quyền theo luật) và
`EXTERNAL_BACKUP_PENDING`.

## A. Baseline

| | trước | sau |
|---|---|---|
| `main` / `origin/main` | `30e26353` / `30e26353` | `30e26353` + commit báo cáo này (push thường) |
| branch local | 11 | 8 |
| worktree đăng ký (gồm `main`) | 7 | 4 |
| thư mục tồn dư không đăng ký | 13 + 13 file log rời | 11 (7 chỉ còn file do Codex sở hữu, 4 bị ACL chặn đọc) |
| ổ D: trống | 9,4 GB | 56 GB |

Phân loại dựa trên quan hệ lịch sử **và** nội dung: mọi file được băm thành blob Git (thô và CRLF→LF) và so với tập blob reachable
từ mọi ref; phần còn lại so SHA-256 với archive riêng tư; không đi theo junction.

## B. Branch đã xoá

| branch | HEAD | lý do / bằng chứng |
|---|---|---|
| `research/hybrid-v2-w3-f2-ratio-projection-language-grounding` | `15a8e1ac` | tổ tiên của `main` (`git branch -d`) |
| `feat/axo-v27-frontend-integration` | `6b980f2b` | tổ tiên của `integration/axo-hybrid4-reliability` (giữ) và có trong bundle khôi phục thử; nội dung đã squash vào `main` (`-D`) |
| `integration/axo-pedagogical-construction-hardening` | `67f780ca` | như trên; bản cũ hơn còn ở `origin/` (`-D`) |

Cộng các branch đã xoá ở run `axo-repository-baseline` (`chore/axo-postmerge-branding-consolidation`, ba `research/scene3d-*`).

## C. Worktree đã gỡ (`git worktree remove`, không `--force`, gỡ junction `node_modules` trước)

| worktree | trạng thái | bằng chứng an toàn | kết quả |
|---|---|---|---|
| `axo-v27-frontend-integration` | `frontend/index.html` sửa chưa commit = đúng bản `main` (`git diff main` rỗng, blob `9e8f4275`) | bản sửa + `algosim.db` lưu archive; khôi phục file về HEAD rồi gỡ; 0 thư mục do Codex sở hữu | gỡ hết |
| `w3-f2-solid-scope-t3`, `w3-f2-unified-scope-t3` | sạch; HEAD trong `main`; 4 560 file tạm T3 (pytest tmp, db test) | lưu archive 2 × 4 560 file; 0 thư mục Codex | gỡ hết |

## D. Thư mục tồn dư

| thư mục | file | phân loại | kết quả |
|---|---|---|---|
| `hm-t3-7e9e479d` | 26 044 | 26 033 Git + 11 cache | **xoá hết** |
| `w4-geometry-pedagogy` | 0 | rỗng | **xoá hết** |
| 13 file `*.log` rời trong `.superpowers/worktrees/` | 13 | log T3/E2E cũ, không chứa khoá | lưu archive rồi **xoá** |
| `axo-hybrid4-integration` | 27 576 | Git 27 179 + archive 337 + cache 60 | xoá phần được phép; **còn 264 file** do Codex sở hữu |
| `axo-performance-baseline` | 287 | Git 282 + archive 2 + cache 3 | còn 6 |
| `planner-generalization` | 26 142 | Git 25 498 + cache 644 | còn 87 |
| `ratio-projection-publication-verification` | 26 386 | Git 26 325 + cache 61 | còn 61 |
| `hybrid-session5-offline-consumer` | 16 851 | Git 16 230 + cache 620 + `algosim.db` (archive) | còn 170 |
| `w3-f2-…/.superpowers/worktrees/w3-f2-target-grammar-identity-compat` | 26 645 | Git 26 308 + archive 1 + cache 336 | còn 123 |
| `hybrid-master-backend-replacement` | 3 | Git 3 | còn 3 (cả 3 do Codex sở hữu) |
| `hybrid-primary-b1-b2-offline` | 21 972 | 3 thư mục không đọc được, 4 637 file lạ (pytest tmp, ghi chép T3), junction | **giữ nguyên** (ACL) |
| `source-gate-language-generalization`, `source-gate-language-t3` | ~26 000 mỗi thư mục | 1 thư mục không đọc được + `algosim.db` | **giữ nguyên** (ACL) |
| `windows-watchdog-recovery` | 8 770 | 1 thư mục không đọc được, 5 file lạ | **giữ nguyên** (ACL) |

"Còn N file": file và thư mục do `CodexSandboxOffline` sở hữu cấp cho `Users` quyền ghi nhưng không có quyền xoá. Theo luật, không dùng
`takeown`/`icacls`. Mọi file còn lại đã được phân loại Git/archive/cache (0 file lạ). Chủ kho xoá được trong PowerShell **chạy
quyền Administrator** (Administrators có FullControl), từng đường dẫn chính xác:
`Remove-Item -LiteralPath 'D:\Documents\projects\algo-sim\.superpowers\worktrees\<tên>' -Recurse -Force`.

## E. Còn giữ

| đối tượng | lý do |
|---|---|
| `integration/axo-hybrid4-reliability` (local, không push) | 146 commit ngoài `main`, 3 blob bị đánh dấu; bundle hợp lệ nhưng chỉ có một bản trên cùng ổ vật lý ⇒ giữ tới khi có bản ngoài máy |
| `feat/real-model-pilot-tooling` | 1 commit chưa có trên `origin/`; 70 file khác `main`; được tài liệu trên `main` trích dẫn |
| `research/compact-geometry-dsl`, `research/hybrid-next-architecture-gap-audit`, `research/hybrid-semantic-extraction-v2`, `research/hybrid-v2-independent-vietnamese-section-holdout`, `research/nl-to-scene3d-e2e-readiness` | nội dung (báo cáo nghiên cứu) không có trên `main` và được `docs/` trên `main` trích dẫn (11–39 file mỗi nhánh); không tự merge |
| worktree `axo-pedagogical-integration` (detached tại `67f780ca`) | 17 thư mục run do Codex sở hữu ⇒ không gỡ sạch được; 221 file độc nhất đã lưu archive; `index.html` sửa = bản `main` |
| worktree `w3-f2-adapter3-t3`, `w3-f2-ratio-projection-language-grounding` (detached) | thư mục tạm bị ACL chặn đọc ⇒ không kiểm được |
| `refs/archive/evidence-index/4a218d2d…`, `…/e3827c00…` | hai commit `EVIDENCE_INDEX` trích dẫn đã dangling từ trước (không ref nào giữ); ghim lại để `git gc` không xoá, kèm bundle riêng. Không phải branch, không push |
| remote: `origin/research/scene3d-section-inspector-c0` (đã nằm trong `origin/main`) | **đề xuất xoá**; chưa xoá vì `gh` chưa đăng nhập, không kiểm được PR |
| remote: `origin/integration/axo-pedagogical-construction-hardening` | nằm trong nhánh tích hợp local; đề xuất xoá sau khi có bản sao ngoài máy |
| remote: `origin/docs/real-model-e2e-readiness`, `origin/feat/real-model-pilot-tooling` | chưa tích hợp; giữ |

## F. Kiểm tra cuối

- `main` = `origin/main` (`git ls-remote`); `git status`: chỉ `.playwright-mcp/` chưa theo dõi (có từ trước).
- `git worktree prune --dry-run`: không còn đăng ký treo.
- 861 commit `EVIDENCE_INDEX` trích dẫn: tất cả reachable sau khi ghim 2 commit dangling.
- Bundle khôi phục thử của nhánh tích hợp chứa `6b980f2b`, `67f780ca` và các commit `8db058d3`, `9a7c0ce9`, `cee124a1`, `33e1cda2`,
  `c5cef563`, `b0c2dfe5`, `667fff7a`.
- Archive `algo-sim-private-archive/` (836 MB): 11 manifest, 10 316 file, SHA-256 khớp toàn bộ; 2 bundle `git bundle verify` OK
  (`939b4cff…`, `324c75e9…`). `EXTERNAL_BACKUP_PENDING`: máy chỉ có một ổ vật lý.
- Publication của commit báo cáo: xem thông điệp commit (quét `--range` trước push).
- Còn mở (không thuộc task): `POSTGRES_NOT_TESTED`; production chưa `alembic upgrade head` (`e437149641fa`); 97 publication
  finding cũ chờ chủ kho.
