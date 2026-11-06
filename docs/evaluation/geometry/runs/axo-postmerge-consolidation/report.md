# Axo — post-merge consolidation, branding restoration & research scope alignment

Run `axo-postmerge-consolidation` · 2026-11-07 · nhánh `chore/axo-postmerge-branding-consolidation` (từ `main` 64847c1e)
· 0 lượt gọi provider · không merge, không push.

Trạng thái cuối: xem §K.

## A. Kiểm tra `main` sau squash merge

| kiểm | kết quả |
|---|---|
| `origin/main` = `main` = 64847c1e, cây 9eb132ff | khớp cây của nhánh tích hợp `c7ae6947` (bundle khôi phục ra đúng cây này, §D) |
| `freeze_evaluation_candidate.py --verify` trên `main` | **ĐỎ**: `product_commit_sha` 8db058d3 chỉ nằm trên nhánh tích hợp (squash không mang commit ấy); `measured_system` vẫn khớp (103 file, 09c1a089) |
| `test_docs_information_architecture.py` trên nhánh trước khi sửa | 41/42 — `test_inv_20` đỏ cùng nguyên nhân |

Sửa: đóng băng lại trong worktree detached sạch tại 9904265b (commit sản phẩm của run này), commit riêng 14810326.
`measured_system` không đổi ⇒ template K-1/R-1/S-2 (`hybrid-master-backend-replacement/*-owner-approval.template.json`,
ràng buộc vào `measured_system`) **không** cần ràng buộc lại. `CACHE_VERSION` giữ 132 (không đổi ngữ nghĩa dữ liệu).

## B. Nguyên nhân gốc: tab hiện "AlgoSim" và icon quả địa cầu

1. **Favicon.** `frontend/public/favicon.svg` (logo Axo, blob `0ff1b07e`, thêm ở 91a73e17 trên dòng Axo) bị rơi ở merge
   **75d88a31** — thông điệp commit: *"main's favicon removal is kept (index.html, public/favicon.svg)"*. Việc gỡ trên `main`
   (f89a1a8b, 2026-10-09, được chủ kho cho phép) là gỡ **favicon AlgoSim cũ** (blob 5918c602, 561baf61). Merge đã áp quyết định
   đó lên favicon Axo mới; squash 64847c1e mang kết quả sang `main`. `index.html` còn `<link rel="icon" href="data:,">` ⇒
   trình duyệt hiện icon mặc định.
2. **Tiêu đề.** `<title>` chưa bao giờ là Axo trên nhánh nào (`git log -S` trên `frontend/index.html`); app không đặt
   `document.title`. Header đã là Axo (`AxoMarkGeometry`), nên chỉ tab sai.
3. **Chữ "AlgoSim" người học thấy.** Một số thông điệp từ chối của backend (`learner_messages.py`, `hybrid_preview.py`) và
   hai chuỗi cứng trong `SimulationWorkspace.tsx`.

Nhận diện favicon được chứng minh bằng hình học: hai `d=` path và `transform="translate(18.0 59.5)"` của `favicon.svg` trùng
từng ký tự với `AxoMarkGeometry` trong `frontend/src/components/icons.tsx` (khoá trong `branding.test.tsx`). Không vẽ logo mới.

## C. Sửa (commit 9904265b)

| file | thay đổi |
|---|---|
| `frontend/public/favicon.svg` | khôi phục byte-y-hệt blob `0ff1b07e` |
| `frontend/index.html` | `<link rel="icon" type="image/svg+xml" href="/favicon.svg" />`, `<title>Axo — Mô phỏng tương tác</title>` (chữ tiêu đề trang chủ do chủ kho sửa trực tiếp trong lúc run; giữ nguyên) |
| `frontend/src/branding.ts` | `BRAND_NAME`, `HOME_TITLE`, `pageTitle(page)`, `displayBrand(text)` — một nơi duy nhất cho tên hiển thị |
| `frontend/src/App.tsx` | tiêu đề tab theo view: `Thư viện \| Axo`, `Lịch sử \| Axo`, `Mô phỏng hình học 3D \| Axo`, trang chủ = `HOME_TITLE` |
| `SimulationWorkspace.tsx`, `ProblemInput.tsx` | thông điệp người học qua `displayBrand`; hai chuỗi cứng đổi sang "Axo" |
| `branding.test.tsx` (mới), 2 test hợp đồng | khoá: link icon, tiêu đề, hình học favicon = header, không còn "AlgoSim" hiển thị |
| `frontend/scripts/axo-branding-browser-check.mjs` (mới) | kiểm trên production build trong Chrome thật (§I) |

Không đổi: khoá kỹ thuật `algosim.*`, cookie `algosim_session`, tiêu đề backend, báo cáo cũ — đó là hợp đồng/lịch sử, không phải
thương hiệu. Backend vẫn viết "AlgoSim" trong vài thông điệp; sửa tận nguồn chạm `backend/app` ⇒ để task riêng
(`AXO_RESEARCH_SCOPE.md §6`).

## D. Bảo toàn bằng chứng

Nguồn: worktree `axo-hybrid4-integration` (nhánh `integration/axo-hybrid4-reliability` @ c7ae6947). 946 file chưa theo dõi
+ file bị ignore có giá trị.

| lớp | nội dung | xử lý |
|---|---|---|
| A — đã có trong git | mọi file tracked (0 sửa đổi chưa commit) | giữ nhánh; bundle |
| B — bằng chứng duy nhất | 910 file `docs/evaluation/geometry/runs/{axo-end-to-end-authority-scene3d-usability (593), axo-final-educational-viewer-readiness (119), axo-hybrid4-final-premerge-hardening (99), axo-hybrid4-capability-scene3d-reliability (60), axo-hybrid4-integration-reliability (39)}` (png/json/gz) | lưu trữ riêng tư + SHA-256 |
| C — tái tạo được nhưng là build đã đo | 7 thư mục `frontend/dist-*` (35 file) | lưu trữ (nhỏ, giữ fingerprint của lượt đo) |
| D — runtime cục bộ | `backend/algosim.db` (SQLite dev), `frontend/debug.log` (log GPU của Chrome) | lưu trữ riêng tư, **không** commit |
| bỏ | `__pycache__`, `.pytest_cache`, `.vite-cache`, `dist/`, junction `node_modules` | tái tạo được |

Lưu trữ: thư mục riêng tư cục bộ **ngoài** kho và ngoài mọi worktree (`algo-sim-private-archive/axo-hybrid4-integration-2026-11-07/`
cạnh thư mục kho; không tải lên dịch vụ nào). Cùng ổ đĩa với kho — một bản sao, chưa có bản ngoài máy (§K).

| vật | xác minh |
|---|---|
| 947 file (364 993 332 byte), `MANIFEST.json` sha256 `87aa6f09…` | hash nguồn = hash bản chép lúc chép; `sha256sum -c` lại toàn bộ: **947/947 OK**; danh sách: `evidence-archive.sha256` (run này) |
| `integration-axo-hybrid4-reliability.bundle` (278 MB, sha256 `939b4cff…`, tiền đề bb61a804 trên `main`) | `git bundle verify` OK; **khôi phục thử** vào repo trống: `restored` = c7ae6947, cây 9eb132ff = cây nhánh |

Bundle chứa ba blob đã bị đánh dấu publication (23109136, 28be1ef6, f4b76988) ⇒ chỉ lưu riêng tư, không đẩy lên đâu.

## E. Dọn dẹp

| mục | kết quả |
|---|---|
| worktree `axo-hybrid4-integration` | gỡ junction `node_modules` (đích `frontend/node_modules` của kho chính còn nguyên) → `git worktree remove --force`: **đăng ký worktree đã gỡ**, nhưng xoá thư mục dừng giữa chừng (`Invalid argument`). Phần còn lại 27 576 file được kiểm từng file: 27 160 trùng blob của nhánh (đã giữ + bundle), 353 trùng SHA-256 trong lưu trữ, 63 là cache; **0 file lạ**. Lệnh xoá phần còn lại bị bộ phân loại quyền của phiên chặn ⇒ **thư mục vẫn còn** — chủ kho xoá tay (§K) |
| nhánh `integration/axo-hybrid4-reliability` | **giữ** (EVIDENCE_INDEX trích hash của nó; chứa blob đã đánh dấu — không push) |
| 4 metadata worktree prunable (`s3d-hybrid-v2`, `s3d-hybrid-v2-codex`, `scene3d-visual-correction`, `visual-hybrid-integration`) | thư mục đã không tồn tại; HEAD của cả bốn đều nằm trong lịch sử `main` ⇒ `git worktree prune`; nhánh của chúng giữ nguyên |
| worktree tạm của run (`wt-before`, `wt-freeze`, `wt-t3`) | gỡ sau khi dùng (junction gỡ trước) |
| các worktree khác (`axo-pedagogical-integration`, `axo-performance-*`, `axo-v27-frontend-integration`, `independent-section-holdout`, `w3-f2-*`) | không chạm — ngoài phạm vi, có thể thuộc việc khác |

## F. Phạm vi nghiên cứu chính thức

`docs/architecture/AXO_RESEARCH_SCOPE.md` (mới): Axo là gì, 10 giá trị cốt lõi, "tính toán ≠ trình bày đáp số", bảng phân loại
CORE / SUPPORTING / OPTIONAL PRESENTATION / OUT OF SCOPE kèm quyết định và bằng chứng, danh sách không làm, đề xuất cho task sau.

## G. Trình bày hướng đáp số — kiểm toán, không gỡ khi thiếu bằng chứng

- 29 cảnh thật đã phục vụ: 0 bước "Kết luận mục tiêu"/"Kết luận và tính toán"; hai bước "nhấn mạnh kết quả" là **dựng đoạn được
  hỏi**, không phải đáp số.
- Chính sách trình bày (`scene3d-student-presentation-policy.ts`): `showMathResultsPanel: false`, giá trị đáp số bị ẩn.
- `Scene3DExplorer.tsx` (menu "xem kết quả", "Đại lượng") chỉ còn được 13 file test import, sản phẩm không render ⇒ ghi OUT OF
  SCOPE, **chưa gỡ** (gỡ kéo theo viết lại test ⇒ task riêng).
- Không đổi gì ở trình bày trong run này.

## H. Toán học, kernel, verifier, Scene3D — không chạm

`backend/app/**` không đổi (`measured_system` 09c1a089, 103 file, trước = sau); không đổi công thức, toạ độ, planner, registry,
camera. Thay đổi frontend chỉ ở `index.html`, `public/`, `App.tsx` (tiêu đề), chuỗi hiển thị trong hai component.

## I. Kiểm trong trình duyệt (Chrome 157 thật, offline, production build, tuần tự — một trình duyệt mỗi lúc)

| kiểm | trước (`main` 64847c1e) | sau (nhánh) |
|---|---|---|
| tiêu đề `/`, `/library`, `/history`, `/simulation/thiet-dien-chop` | "AlgoSim — Mô phỏng tương tác" ở cả bốn | "Axo — Mô phỏng tương tác", "Thư viện \| Axo", "Lịch sử \| Axo", "Mô phỏng hình học 3D \| Axo" |
| link icon / `/favicon.svg` | `data:,` / 404 | `/favicon.svg` / 200 `image/svg+xml`, sha256 `71eb0df9…` |
| reload, ngữ cảnh mới, 1440×900 và 390×844 | không đổi (vẫn AlgoSim) | tiêu đề giữ nguyên qua reload; 0 request lỗi; 0 lỗi console |
| điều hướng trong app | tiêu đề không đổi | đổi theo view |
| receipt | `branding-before-main/` (chỉ ghi) | `branding-after/` **9/9 PASS** |

Ảnh: `branding-before-main/*.png`, `branding-after/*.png`, `branding-after/favicon-served.png` (icon được phục vụ).
`branding-before/` là lượt "trước" đầu tiên, dừng ở bước chụp favicon (404 làm script ném lỗi) — không có receipt, không tính,
không commit.

Scene3D smoke trên build "sau":

| kiểm | kết quả |
|---|---|
| `axo-camera-views-browser-check.mjs` 1440×900 (chóp + thiết diện, ngũ giác 3 điểm, lăng trụ xiên, lập phương lục giác, cầu ∩ mặt phẳng, mặt tiếp xúc cầu, trụ thiết diện tròn, nón thiết diện qua trục, lăng trụ đứng, chóp lồng) | **10/10** (`scene3d-camera-1440/`) |
| cùng bộ, 390×844 | **10/10** (`scene3d-camera-390/`) |
| `axo-scene-consistency-browser-check.mjs` (bước/phát/xoay/zoom/dock/đổi bài/F5/lịch sử/Back-Forward, 360–1440 px, Chrome zoom 110% thật) | **41/41** (`scene3d-consistency/`) |

Trường `dist` trong ba receipt Scene3D được thay bằng `<worktree>/frontend/dist` trước khi commit (không ghi đường dẫn máy).

## J. Kiểm thử và cổng

| cổng | kết quả |
|---|---|
| vitest đầy đủ trên nhánh (trước commit) | 135 file / 2007 test PASS (≤ 2 worker) |
| vitest liên quan sau sửa CODE_INDEX | 5 file / 144 PASS (branding, code-index-sync, ui-hygiene, 2 test hợp đồng) |
| `npm run build` | PASS; `dist/favicon.svg` = blob `0ff1b07e` |
| seal `--verify` | MATCH sau đóng băng lại (103 file, 09c1a089) |
| docs IA + evaluation candidate | 68/68; `test_current_state_identity.py` 3/3 |
| T3 (`full-gate.mjs`) tại 14810326, worktree detached sạch, 1 lượt | **FULL_PRODUCT_GATE_PASS** — pytest 13 878 passed / 7 skipped / 3 deselected / 9 xfailed; vitest 135 / 2007; build PASS; demo 5/5; bề mặt sập 6/6 |
| node harness (`node --test "scripts/*.node-test.mjs"`), cùng worktree | 155: 153 pass, 0 fail, 2 skip môi trường |
| publication scan | PUBLICATION_SCAN_PLACEHOLDER |

## K. Trạng thái và việc còn mở

Trạng thái: **COMPLETED_WITH_RETAINED_EVIDENCE** — sửa xong và đã kiểm; bằng chứng giữ lại (lưu trữ riêng tư, nhánh tích hợp,
thư mục còn sót chờ chủ kho xoá).

Còn mở / cần chủ kho:

1. Thư mục còn sót `.superpowers/worktrees/axo-hybrid4-integration/` (không còn là worktree; 27 576 file đã kiểm, 0 file lạ).
   Xoá khi đồng ý: `Remove-Item -LiteralPath '\\?\<kho>\.superpowers\worktrees\axo-hybrid4-integration' -Recurse -Force`.
2. Lưu trữ riêng tư chỉ có một bản, cùng ổ đĩa với kho. Nên sao thêm ra phương tiện ngoài trước khi coi là an toàn lâu dài.
3. Nhánh `integration/axo-hybrid4-reliability` giữ lại (bằng chứng, blob đã đánh dấu) — không push.
4. `CLAUDE.md` cục bộ (bị gitignore) §2 còn ghi "`index.html` dùng icon rỗng `data:,`" — đã lỗi thời; run không sửa file cục
   bộ của chủ kho. `AI_CONTEXT_BUNDLE.md` (commit) đã sửa.
5. Backend còn chữ "AlgoSim" trong thông điệp người học; `Scene3DExplorer.tsx` chỉ còn test dùng — đề xuất ở
   `AXO_RESEARCH_SCOPE.md §6`.
6. Có sẵn từ trước: 125 file trong `docs/` (đã commit) chứa đường dẫn hồ sơ người dùng cục bộ; không viết lại lịch sử để gỡ.
7. Nhánh này chưa merge/push — cần quyết định của chủ kho.
