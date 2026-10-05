# HANDOFF — regular-square-pyramid-w01

Cho người dùng (chủ kho, người duyệt hình) và phiên agent kế tiếp. Số liệu và lý do: [`REPORT.md`](REPORT.md).

## Trường bắt buộc

```text
TASK = REGULAR_SQUARE_PYRAMID_AND_PEDAGOGICAL_UI
TASK_SLUG = regular-square-pyramid
WAVE = W1
RUN_ID = regular-square-pyramid-w01
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
CURRENT_BRANCH = feat/regular-square-pyramid
BASE_MAIN = 38d4158826cbbffd013d971a9484b9f0fd2a6130 (= origin/main theo git ls-remote, không đổi suốt W1)
START_HEAD = 38d4158826cbbffd013d971a9484b9f0fd2a6130
END_HEAD = SELF (commit chứa bản cuối của file này; tra bằng git log -1)
MEASUREMENT_COMMIT_SHA = ed37f9fa127d50e53ccfde3017b2b5ea7615d03b (bộ trình duyệt, occlusion, playback, ảnh — candidate 4629c3e8) · chuyển tiếp sang candidate 5234c37e tại b5cf4503 (results/FIXTURE_TRANSFER_b5cf4503_r2.json: TRANSFERS, 37/37 envelope trùng byte, frontend/src không đổi)
VERIFICATION_COMMANDS_AND_RESULTS = (1) trước tự rà soát, worktree tách rời sạch 'D:/tmp/rsp w01' @ 96181b87: full-gate → FULL_PRODUCT_GATE_PASS (pytest 7118/0, vitest 1071/1071, build, demo 5/5, bề mặt sập 6/6; lần 1 đỏ 1 test vì log nằm trong worktree), w01_gates.sh đạt — diagnostics/logs/*_96181b87.log · (2) sau bản sửa, worktree tách rời sạch 'D:/tmp/rsp w01b' @ 7b99ccaa (commit tài liệu cuối; npm ci --offline; log ghi NGOÀI worktree): full-gate → FULL_PRODUCT_GATE_PASS (pytest 7131 passed / 0 failed / 1 skipped / 2 deselected · vitest 1071/1071 · build · demo 5/5 · bề mặt sập 6/6 · git status 0 trước và sau) · w01_gates.sh → candidate 5234c37e + cache 112 verify 0, schema export ×2 trùng byte (d852b47c…), LLM_ONLY, 0 file bề mặt mô hình đổi, git diff --check 0, audit tài liệu PASS, node harness 76 pass / 0 fail / 2 skip (môi trường) — diagnostics/logs/T3_FULL_GATE_7b99ccaa.log, GATES_7b99ccaa.log
VERIFIED_AT = 7b99ccaafce273bd2767ec0a42ea699fb052c091 (commit trạng thái sau nó chỉ thêm log, manifest, bản ghi lượt đo và số liệu kiểm chứng vào tài liệu)
BROKEN_LINK_COUNT = 0 (audit tài liệu tại 7b99ccaa và lại ở commit trạng thái)
PRODUCT_COMMITS = 3bdada32 (chóp tứ giác đều) · ae9c72a5 + b2d224f6 (giao diện §0.1) · 98e2b8f7 (chọn chiều cao của công thức) · 9d66c603 (manh mối "độ dài") · de5b2331 (CACHE_VERSION 112) · ad7172ab (T7 đọc cạnh bên gọi bằng tên đoạn — tự rà soát cuối)
CANDIDATE_BEFORE = b2d4187a78ed8bf6df15118edc7e4e251c5f22df536e50b73ac043f108f3b7af
CANDIDATE_AFTER = 5234c37e424c60bae4741e68170a0c95e5361cfbe71e2114b96c08d2310d44fa (product commit ad7172ab; 110 file) — trung gian 4629c3e8e3f5be60dd2bc4176c108a132d5aee5604e0e8f7a9b8d90cca4547ea (de5b2331)
CANDIDATE_REFROZEN_COUNT = 2 (worktree tách rời sạch D:/tmp/rsp-freeze rồi D:/tmp/rsp-freeze2; khai inputs/CANDIDATE_DIVERGENCE_CORRECTION.json) — một lần chạy nhầm --help ghi vào cây chính bẩn, đã khôi phục bằng git checkout, không commit
CACHE_VERSION_BEFORE = 111
CACHE_VERSION_AFTER = 112
CACHE_VERSION_REASON = envelope phục vụ đổi nội dung; hai row v111 vẫn HIT dù W1 dựng envelope khác, bump làm cả hai MISS (diagnostics/PROOF_CACHE_ROW_W01.json); bản sửa ad7172ab giữ 112: 9/9 envelope phục vụ dưới 112 trùng byte, ca mới phục vụ vốn bị từ chối (diagnostics/PROOF_CACHE_ROW_W01_R2.json); môi trường ngữ nghĩa b1714b56 không đổi
MODEL_SURFACE_CHANGED = NO (lược đồ, prompt, thẻ văn phạm, bảng năng lực không đổi)
DEFAULT_MODE = LLM_ONLY
LIVE_GEMINI_REQUESTS = 0
CORPUS_RESULT = 24/24 khớp nhãn đăng ký trước: lớp 1 17/17 (7 phục vụ, 7 từ chối có cấu trúc, 3 ngoài phạm vi W1) + lớp R2 7/7 (3 phục vụ, 3 từ chối, 1 giới hạn của bộ đọc độ dài); 0 nhãn hạ sau khi thấy kết quả (đính chính chặng PC2 có khai)
BROWSER_RESULT = 7/7 họ PASS ở ed37f9fa — 14/14 dương, 54/54 âm, 6/6 phục vụ thêm, chọn đại lượng 68/68, ngăn «Đại lượng» 14/14, panel «Các bước dựng» 14/14, 0 exception
OCCLUSION_RESULT = pass, 0 lỗi; HUMAN_REVIEW_PENDING cho bốn cảnh W14 (như trước); chóp đều product = oracle ở 4/4 trạng thái
PLAYBACK_RESULT = 14/14
MEASUREMENT_ATTEMPTS = trình duyệt 3 (2 hỏng, giữ riêng: manifest hash; bộ đo đọc card Kết quả đã ẩn) · T3 @ 96181b87 2 (1 hỏng: log nằm trong worktree) · chuyển tiếp 2 (1 hỏng: script so hash dạng LF) · T3 @ 7b99ccaa 1 (đạt) — diagnostics/MEASUREMENT_ATTEMPTS.json
PREREGISTRATION_CORRECTIONS = 2 (PC1 ca âm kernel — trước mọi lần chạy trình duyệt; PC2 chặng từ chối của R2 N8/U4 — sau lượt đỏ, trước bản sửa, kết cục không đổi)
DEFECTS_FOUND_AND_FIXED = 3 sản phẩm (công thức thể tích mất khi có hai ứng viên chiều cao; cổng phạm vi từ chối "độ dài"; T7 bỏ qua cạnh bên gọi bằng tên đoạn — tự rà soát cuối) + 3 bộ đo + 1 script chuyển tiếp (so hash ở dạng LF)
FINAL_REVIEW = tự rà soát (brief cấm subagent) theo requesting-code-review/code-reviewer.md: 1 Important đã sửa (ad7172ab, RED 21c172e8 → GREEN), 2 Minor hoãn (nhãn InputFact không lọc gạch dưới; aria-controls của nút «Các bước dựng») — REPORT §5, §8
ISSUES_RESOLVED = ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE
ISSUES_PARTIAL = ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY (tâm + giao điểm hai đường)
ISSUES_OPENED = ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE · ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY
SKILLS_ACTUALLY_USED = Skill tool cho W1: superpowers:test-driven-development · áp dụng từ hướng dẫn đã nạp trong cùng phiên (không gọi lại): superpowers:writing-plans, superpowers:executing-plans, superpowers:systematic-debugging, superpowers:verification-before-completion, andrej-karpathy-skills:karpathy-guidelines, ponytail:ponytail-review · không subagent
LIVING_DOCS_UPDATED = README.md (ab98a2df), docs/README.md, docs/CURRENT_STATE.md, docs/ROADMAP.md, docs/OPEN_ISSUES.md, docs/CODE_INDEX.md, docs/EVIDENCE_INDEX.md, docs/STATUS_LEDGER.md, docs/AI_CONTEXT_BUNDLE.md, docs/research/CLAIM_EVIDENCE_MAP.md (B2, D5, C7 mới), CANDIDATE_DIVERGENCE.json sống, backend/scripts/audit_docs_information_architecture.py (hành động chuẩn tắc mới)
HISTORICAL_ARTIFACTS_BYTE_IDENTICAL = YES — 38d41588..7b99ccaa: ngoài run W1, docs/evaluation chỉ đổi hai registry sống (EVALUATION_CANDIDATE.json, CANDIDATE_DIVERGENCE.json); 0/180 báo cáo lịch sử đổi (dòng "1 of 181" của GATES_7b99ccaa.log là link giới thiệu của catalog tới docs/EVIDENCE_INDEX.md sống — cùng dương tính giả đã khai ở cuboid-final-review)
TEMP_FILES = diagnostics/TEMP_FILE_INVENTORY.json — mọi worktree đã gỡ (không --force); lệnh xoá file tạm của agent bị từ chối ở hộp quyền (không lách); sáng 2026-10-06 các file ấy và cả scratchpad được thấy đã biến mất do một tác nhân khác agent; file tạm của lượt sửa nằm trong scratchpad mới
HUMAN_VISUAL_REVIEW = NOT_APPROVED
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
BRANCH_DELETION_RESULT = NOT_ATTEMPTED — feat/cuboid-prism-specialization đã bị xoá TRƯỚC W1 theo yêu cầu rõ của người dùng (tổ tiên của origin/main, 0 commit riêng); brief W1 nói "không xoá" nhưng việc ấy đã xảy ra trước khi brief đến
USER_FAVICON_DELETION_PRESERVED = YES (không bao giờ stage, restore hay sửa)
NEXT_ACTION = người dùng duyệt hình W1 (§1); sau khi duyệt: kiểm lại origin/main, merge nhánh vào main, push main, xoá nhánh đã merge (AGENTS.md §2); không PR
```

## 1. Việc chờ người dùng

Ảnh đầy đủ: sheet và filmstrip mỗi họ ở `images/<họ>/SHEET.png`, `FILMSTRIP.png` (độ phân giải gốc); chỉ mục
`images/overview/INDEX.png`. Ảnh lẻ ở `images/<họ>/<desktop|mobile>/`.

| id | câu hỏi | xem ở |
|---|---|---|
| **H-W1-1** (chặn merge) | Duyệt W1 gồm hai phần. **(a)** Chóp tứ giác đều: hình, bước dựng, chọn thể tích / diện tích / chiều cao, bốn lời từ chối. **(b)** Chín mục giao diện §0.1 trên **cả bảy họ**: card Kết quả ẩn, ngăn «Đại lượng», panel «Các bước dựng» (desktop cạnh khung, mobile dưới điều khiển), nhảy bước, gỡ dải «Đang dựng». | `images/regular-square-pyramid/SHEET.png`; `images/<họ>/{desktop,mobile}/quantity_picker.png`; `…/formation/steps_panel_{open,closed}.png` |
| H-W1-2 | Chiều cao của chóp đều hiện là `d(S, (ABC)) = 3` (khoảng cách tới mặt phẳng phụ do chương trình dựng), không phải `SO = 3`, và không vẽ đoạn SO. Có cần vẽ SO và gọi tên nó không? Muốn vậy cần một quy tắc trình bày mới: gọi chân đường cao bằng tên tâm đề nêu. | `images/regular-square-pyramid/desktop/selected_volume.png` |
| H-W1-3 | Bước cuối "Mặt phẳng qua A, B, C" vẽ một tấm mặt phẳng lớn chỉ để đo chiều cao. Mặt phẳng phụ chỉ dùng để đo có nên ẩn mặc định không? | `images/regular-square-pyramid/desktop/neutral_final.png` |
| H-W1-4 | Danh sách bước có "Đường thẳng qua A và C", "… B và D", "Giao điểm của AC và BD" — phép dựng phụ để có tâm O. Giữ thành bước riêng, hay gộp vào một bước "Tâm O của đáy"? | `images/regular-square-pyramid/mobile/formation/steps_panel_open.png` |
| H-W1-5 | `ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE`: đề ghi độ dài ≤ 0 bị từ chối, nhưng lời từ chối không nói là đề sai (cả bảy họ, tuyến mặc định). Có mở wave sửa không? | `images/regular-square-pyramid/negative/topology_kernel/*/refusal.png` |
| giữ từ trước | W18-H2 (ô soi lặp dòng giá trị — nay đáp số đọc qua ngăn «Đại lượng», cần người xác nhận đã hết lặp) · W17-H2 · W15-H2 · W15-H3 · H-W20-4 · F1–F5 của cuboid-merge (vẫn mở) | `docs/ROADMAP.md` §0 |

**Khi H-W1-1 được duyệt** (AGENTS.md §2):
1. Kiểm lại `origin/main`.
2. Merge thẳng nhánh vào `main` và push `main`; không force-push, không rebase, không PR.
3. Xoá nhánh đã merge.

Chỉ người dùng ghi `APPROVED_BY_USER`.

## 2. Cho phiên agent kế tiếp

**Năng lực mới:**
- Tra `docs/CODE_INDEX.md`, mục "Chóp tứ giác đều".
- Khuôn T7 ở `assumption_gate._khuon_chop_deu`; bộ đọc ở `shape_constraint`; gắn tâm ở `construction_binding`.
- Corpus và nhãn: `diagnostics/corpus/LABELS.json`; test `tests/geometry/test_regular_square_pyramid.py`.

**Bộ đo:**
- Kịch bản thứ bảy `regular_square_pyramid` ở `frontend/scripts/generic-tier-a-scenarios.json`.
- Cổng `assessQuantityPicker` và `assessStepsPanel`.
- Formation đi với panel bước mở và đọc id của ngăn đại lượng ở mỗi bước.
- Đáp số được chọn qua ngăn.

**Bẫy đã gặp:**
- `freeze_evaluation_candidate.py --help` thực chất đóng băng ngay. Chỉ `--verify` là chỉ đọc.
- Sửa một file làm `oracle_source` thì phải chạy lại `node --test frontend/scripts/*.node-test.mjs` trước khi đo.
- Đầu dò qua `run_pipeline` bắt được hai lỗi mà test route bỏ sót. Kết cục `served` của corpus phải kiểm cả cổng phạm vi.
- Bộ đo băm `FIXTURE_MANIFEST.json` ở byte thô. Trên Windows bộ sinh fixture ghi CRLF, git lưu LF; so hash thì phải so
  đúng dạng (script chuyển tiếp lần đầu so dạng LF và báo sai).
- Log của T3 phải nằm ngoài worktree đo: một file chưa track làm cây "bẩn" và `test_holdout_readiness_7b` đỏ.
- Tự rà soát cuối tìm ra lỗi mà cả corpus đăng ký trước lẫn bộ trình duyệt đều không chạm tới (cách viết `SA = 3`).
  Mỗi họ mới nên có hàng corpus cho **mọi** cách sách giáo khoa nêu cùng một số đo.

**Lát cắt kế tiếp (chưa chọn):**
- Theo `docs/ROADMAP.md` §0.2.
- Các câu hỏi H-W1-2 đến H-W1-4 có thể thành một mục giao diện của wave sau.
