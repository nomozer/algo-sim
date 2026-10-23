# Kế hoạch ACL và dung lượng ổ D:

**Phân loại: `CLEANUP_ADMIN_REQUIRED`.** Lượt này **không xoá gì**. Thu hồi thực tế: **0 B**.
Kiểm kê đọc-chỉ ngày 2026-10-23. Không giành quyền ACL, không đổi owner, không dùng admin hay `--force`.

## 1. Vì sao không có mục nào `CLEANUP_SAFE_TO_EXECUTE` cho agent

Điều kiện Owner đặt: user hiện tại có quyền xoá, không process nào dùng, đã bảo toàn đủ, không có junction tới dữ liệu
khác, và đã xác minh ownership. Mỗi mục lớn đều trượt ít nhất một điều kiện:

- Thư mục Codex tạo kế thừa ACE `CodexSandboxOffline:(F)`, còn Bunny chỉ có `Users:(RX,W)`, tức không có DELETE.
  Đã chứng minh bằng thực tế: `git switch` không xoá được 42 file của run Session 5.
- Worktree của chiến dịch khác: lúc kiểm kê, phiên `scene3d-unified-visual-language` **đang chạy** `tsc -b`/`vitest`
  (PID 23684). Ownership không xác minh độc lập được từ đây.
- Mục nhỏ an toàn (root `.superpowers/session5-t3`, 18,963 B, trùng byte với `verification/full-t3/` đã commit) chưa
  đáng phá ổn định; giữ.

## 2. Danh sách chính xác

D: free lúc kiểm kê: 23,724,105,728 B (chỉ là quan sát, không phải số thu hồi). Kích thước đo bằng `du -sb`, không tính
junction `node_modules`. Cột "dirty" là `git status --porcelain` (tracked + untracked không ignore).

### 2.1 Mục được nêu đích danh

| mục | trạng thái kiểm được | phân loại |
|---|---|---|
| worktree `hybrid-backend-s1` (`82d3d255`, nhánh `…-integration-session1`, ⊂ `main`) | 1,893,372,193 B; 8 log untracked mang ACL Codex (Users không có Delete), đã bảo toàn byte-exact trong `main` ở `77f7aaf7` | `CLEANUP_ADMIN_REQUIRED`, không đụng |
| worktree Session 5 `hybrid-session5-offline-consumer` | 1,926,264,315 B; đang giữ nhánh `research/publication-safety-remediation` chưa merge; 42 file của run `hybrid-offline-consumer` mang ACL Codex (đã chứng minh không xoá được); hai thư mục `.superpowers/session5-backend-final`, `session5-tools-final` trả "Access is denied"; bản duy nhất của log thô bị giữ lại (`session5-raw` 2,718 B, `session5-attempts` 6,432 B); junction `frontend/node_modules` → `D:\Documents\projects\algo-sim\frontend\node_modules` (Mount Point) | `CLEANUP_ADMIN_REQUIRED`; giữ ít nhất đến khi remediation được merge |
| phần dư S4A `.superpowers/worktrees/hybrid-session4a-readiness` (đã de-register) | 369,893 B; 30 file = **26 file tracked trùng byte blob `ef6829d3`** + 4 `.pyc` sinh lại được; ACL Codex; 2 thư mục không đọc được (`.superpowers/session4a-test-final`, `verification-pytest-temp`) | `CLEANUP_ADMIN_REQUIRED` |
| hai thư mục `session5-*-final` | không liệt kê được nội dung (Access denied), nên không xác minh được bảo toàn | `CLEANUP_ADMIN_REQUIRED`; đọc trước khi xoá |

### 2.2 Worktree đã đăng ký khác (19), ownership chưa xác minh

| worktree | HEAD | ⊂ `main` | dirty | junction | bytes |
|---|---|---|---|---|---|
| `t3-scene3d-metric-boundary` (detached) | `2160fbcf` | có | 0 | 1 | 1,860,609,344 |
| `t3-scene3d-pre-main` (detached) | `61668c93` | có | 2 | 1 | 1,858,150,168 |
| `t3-scene3d-pre-main-2` (detached) | `8e2235e7` | có | 2 | 1 | 1,860,048,813 |
| `freeze-scene3d-metric-boundary` (detached) | `cb1f4954` | có | 1 | 0 | 1,838,877,946 |
| `freeze-scene3d-metric-final` (detached) | `216bbf84` | có | 1 | 0 | 1,838,879,242 |
| `verify-geometric-visual-correctness-framing` (detached) | `7868db0a` | không | 0 | 1 | 1,992,149,304 |
| `verify-visual-ux-final-quality` (detached) | `9343e8d0` | không | 0 | 1 | 1,967,366,239 |
| `hybrid-route-d-preview-wiring` | `65d6ee97` | có | 0 | 1 | 1,845,251,474 |
| `semantic-extraction-v3` | `7168d269` | có | 0 | 0 | 1,828,325,958 |
| `semantic-extraction-v3-runtime-revision` | `bb014eb8` | có | 0 | 0 | 1,890,572,171 |
| `simulation-coverage-visual-validation` | `d86c7203` | có | 2 | 0 | 1,873,305,231 |
| `scene3d-plane-grid-camera` | `551a3541` | có | 1 | 1 | 1,854,582,723 |
| `scene3d-unified-visual-language` (**đang chạy**) | `8618d84c` | không | 302 | 2 | 2,424,891,585 |
| `extraction-v2-safety` | `330a222a` | không | 3 | 0 | 1,824,559,997 |
| `geometric-visual-correctness-framing` | `f9559671` | không | 0 | 1 | 1,975,733,246 |
| `hybrid-semantic-extraction-v2` | `dc27009f` | không | 0 | 0 | 1,830,295,758 |
| `nl-to-scene3d-e2e-readiness` | `25f57e31` | không | 0 | 1 | 1,895,847,452 |
| `simulation-visual-consistency-learning-ux` | `f6a8e30f` | không | 0 | 1 | 1,920,238,193 |
| `visual-ux-final-quality` | `164a5e25` | không | 0 | 1 | 1,958,808,275 |

Ứng viên retire hợp lý nhất (detached, ⊂ `main`, sạch): `t3-scene3d-metric-boundary`. Nó vẫn thuộc chiến dịch scene3d
đang hoạt động, nên cần chủ chiến dịch xác nhận. Không mục nào ở bảng này được agent dọn.

### 2.3 Thư mục mồ côi (không đăng ký, không có `.git`, ACE Codex) — không đụng

`composite-baseline`, `composite-verification`, `docs`, `goal-bounded`, `goal-fixed`, `hybrid-backend-continuation-verify`,
`hybrid-offline-readiness-finalization`, `hybrid-session4a-s3-verify`, `semantic-grounding-base-20261017`,
`simulation-evidence-repair`, `t3-scene3d-metric-final`, `verify-simulation-go-main`. Kích thước: `UNKNOWN` (chưa đo, để
không tranh I/O với T3). Cần xác minh ownership và nội dung duy nhất trước mọi quyết định.

### 2.4 Mục nhỏ của chính các phiên Session 5

Root `.superpowers/session5-t3` (18,963 B, trùng byte log T3 đã commit) và `.superpowers/session5-go-main` (bàn giao lượt
trước, có `SHA256SUMS`): giữ. Lợi ích không đáng so với rủi ro.

## 3. Quy trình cho Owner (cần quyền admin)

Với mỗi worktree định retire (ví dụ Session 5, sau khi remote đã xong):

1. Bảo toàn file chỉ có ở local. Session 5: `.superpowers/session5-raw` (2,718 B), `session5-attempts` (6,432 B),
   `takeover-backup/hybrid-preview-adapter.fixed.ts`. Chép ra `D:\AlgoSim-Offline-Archive\…` kèm SHA-256.
2. Dừng mọi Vite/browser/agent dùng cây đó (`Get-CimInstance Win32_Process` lọc theo đường dẫn).
3. PowerShell elevated: `takeown /f <wt> /r /d y` rồi `icacls <wt> /reset /t /c`. Hai thư mục `session5-*-final` và
   `session4a-test-final`/`verification-pytest-temp` chỉ đọc được sau bước này. **Đọc và kiểm kê chúng trước khi xoá.**
4. `cmd /c rmdir <wt>\frontend\node_modules`: gỡ junction, kiểm `fsutil reparsepoint query` trước. **Không** xoá đích
   `D:\Documents\projects\algo-sim\frontend\node_modules`.
5. `git worktree remove <wt>` (không `--force`), rồi `git worktree prune`.
6. Phần dư S4A (đã de-register): sau bước 3, xoá đúng 26 đường dẫn đã kiểm trùng blob `ef6829d3` và 4 `.pyc`, rồi rmdir.
7. Đo D: free trước/sau **và** `du` của đúng thư mục đã xoá. Chỉ con số `du` là dung lượng thu hồi; D: free biến động vì
   các chiến dịch khác cũng ghi đĩa.
