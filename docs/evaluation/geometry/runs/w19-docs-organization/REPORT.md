# W19 — Tổ chức lại tài liệu và tuyển chọn bằng chứng nghiên cứu

`W19_DOCS_REORGANIZATION_AND_RESEARCH_EVIDENCE_CURATION` · 2026-10-04 · nhánh `fix/cuboid-visual-semantic-closure` ·
base `6d0e6321` · **chỉ tài liệu và công cụ kiểm tài liệu** · 0 lượt gọi model · 0 thay đổi sản phẩm.

## 1. Kết luận

**`DOCS_REORGANIZED_AND_VERIFIED`** — tài liệu hiện hành, bản thảo nghiên cứu và hồ sơ wave đã tách thành bốn vùng
có ranh giới kiểm bằng máy; mỗi loại thông tin có một nơi có thẩm quyền; bằng chứng lịch sử trùng blob với base.
Trạng thái sản phẩm không đổi: vẫn là của W18 (`READY_FOR_HUMAN_VISUAL_REVIEW`, người duyệt `NOT_APPROVED`).

## 2. Vấn đề và nguyên nhân gốc

- Gốc `docs/` có 208 file: 11 tài liệu chuẩn tắc, vài tài liệu dự án, ~180 báo cáo wave, và bản thảo khoá luận
  (`THESIS_DRAFT`, tài liệu tham khảo, ma trận trích dẫn…) nằm lẫn nhau. Nguyên nhân: không có luật hay bộ kiểm nào
  ngăn một wave đặt báo cáo ở gốc; từ w09 các wave đã dùng thư mục run nhưng không gì khoá điều đó.
- Ba bảng tuyên bố ↔ bằng chứng cùng tồn tại (`THESIS_READINESS.md`, `thesis/CLAIM_EVIDENCE_MATRIX.md`,
  `research/CLAIM_TO_EVIDENCE_MAP.md`) với các mốc khác nhau (09-09, 09-10, tới W18).
- `CURRENT_STATE.md` dài 5 475 dòng; chính phần đầu của nó ghi rằng phần lớn là nhật ký phát triển (hệ Tin học đã
  gỡ), và W13 đã đánh dấu §3/§4 là cũ. Agent đọc nó ở bước bootstrap.
- Kế hoạch/spec của skill (`superpowers/`), tài liệu giai đoạn chuyển đề (`geometry/`) và quyết định đã thực thi nằm
  cạnh contract đang hiệu lực.

## 3. Quyết định (chi tiết: `inputs/W19_SCOPE_DECISIONS.json`)

| | quyết định | căn cứ |
|---|---|---|
| R1 | Báo cáo wave và artifact giữ **nội dung và đường dẫn**; điều hướng bằng catalog + link | brief §5; AGENTS.md §4; 190/208 tài liệu gốc được artifact đóng băng nêu tên |
| R2 | Tài liệu chuẩn tắc và tài liệu bị ghim đường dẫn ở lại gốc; không đụng `backend/app`, `frontend/src` | bootstrap trong `.claude/settings.json` (không đọc/sửa), hook, bộ kiểm, chú thích mã sản phẩm (candidate / `sourceFingerprint`), test frontend |
| R3 | Không tạo `docs/project/` | tài liệu dự án hiện hành chính là bộ ở gốc bị ghim |
| R4 | Vùng lưu trữ = `docs/legacy/` có sẵn | `RULES_v0.3.md` bị `rules-hygiene.test.ts` ghim; một thư mục lưu trữ, không hai |
| R5 | Bản thảo → `research/thesis/`, `research/paper/` | brief §4 |
| R6 | Một bản đồ tuyên bố `research/CLAIM_EVIDENCE_MAP.md`; ba bảng cũ lưu nguyên byte | brief §5–§6 |
| R7 | `CURRENT_STATE` = trạng thái + con trỏ; nhật ký sang `legacy/CURRENT_STATE_HISTORY.md` nguyên văn | brief §5 |
| R8 | Gốc `docs/` là danh sách đóng (`audit_docs_layout`) | nguyên nhân gốc ở §2 |
| R9 | `POST_THESIS_BACKLOG.md` là phụ lục của ROADMAP | RULES §3 trích đường dẫn |
| R10 | 212 mục `D:/tmp` của wave trước (210 `UNKNOWN`, 2 bản sao lưu settings không mở): giữ | brief §7 |
| R11 | `CLAUDE.md` cục bộ: sửa 6 con trỏ cũ, không commit | phạm vi "tham chiếu cần thiết" |
| R12 | Việc kế tiếp = họ hình mới + chỉnh sửa giao diện đã chốt; review W18 và issue literal-target chặn merge | brief "Mục tiêu sau W19" |

## 4. Việc đã làm

| commit | nội dung |
|---|---|
| `a5c2e6f2` | 62 `git mv` (33 sang `research/`, 29 sang `legacy/`); nhật ký `CURRENT_STATE` (dòng 88–5475) sang `legacy/CURRENT_STATE_HISTORY.md` nguyên văn; viết lại tất định 54 dòng đường dẫn trong tài liệu sống (`inventory/REWRITE_LOG.json`); reader duy nhất đổi đường dẫn: `test_curriculum_coverage.py`; inventory + bảng di chuyển |
| `a44631a9` | `research/CLAIM_EVIDENCE_MAP.md` (26 hàng); 3 bảng cũ sang `legacy/research/` nguyên byte; 10 con trỏ thẩm quyền đổi sang bản đồ (`inventory/AUTHORITY_RETARGET.json`); hub: `docs/README.md` viết lại theo năm câu hỏi, README của `research/`, `evaluation/`, `legacy/`, `architecture/`; catalog đóng `evaluation/HISTORICAL_REPORTS.md` (180 báo cáo); guard `audit_docs_layout` + mở rộng kiểm link sang các hub (4 test, đỏ trước rồi xanh); xoá một file lạc ngoài kho đã xác minh trùng byte |
| commit tài liệu | `CURRENT_STATE` (khối trạng thái + bảng W19), ROADMAP §0 (việc kế tiếp, chặn merge, 9 chỉnh sửa giao diện, ứng viên họ hình, hồi quy), OPEN_ISSUES (3 issue mới, 1 ghi chú tham chiếu không khôi phục được), AI_CONTEXT_BUNDLE (gọn lại 288 → 134 dòng), EVIDENCE_INDEX, STATUS_LEDGER, CODE_INDEX, AGENTS.md §4, README gốc; gói run này |

## 5. Inventory (`inventory/INVENTORY.json`, tại `6d0e6321`)

- 286 tài liệu/file gốc ngoài `docs/evaluation/` — mỗi dòng có: đường dẫn, tiêu đề, loại
  (`CURRENT_PROJECT` 24 · `RESEARCH_WRITING` 41 · `EXPERIMENT_PROTOCOL` 12 · `EXECUTION_EVIDENCE` 168 ·
  `ARCHIVED_DECISION` 41), quyết định (`KEEP` 221 · `MOVE` 33 · `ARCHIVE` 29 · `MERGE` 3 · `DELETE` 0 ·
  `REVIEW_REQUIRED` 0), thẩm quyền/bản thay thế, ai tham chiếu (theo vùng: bằng chứng đóng băng, mã sản phẩm, test,
  công cụ, tài liệu), giá trị nghiên cứu, khả năng tái lập, người đọc.
- 275 nhóm artifact của `docs/evaluation/` (8 439 file), mỗi nhóm kèm git tree id hoặc digest — tất cả `KEEP`.
- 17 mục ngoài `docs/` (kế hoạch, ledger, output bị ignore; ba mục nhạy cảm chỉ ghi có/không) và 215 mục tạm.

## 6. Bản đồ tuyên bố ↔ bằng chứng

`docs/research/CLAIM_EVIDENCE_MAP.md`: 7 nhóm (kiến trúc/R0, tính đúng tất định, thẩm định và chứng chỉ, mô phỏng và
trình bày, tổng hợp live, phạm vi, người học), 26 hàng, mỗi hàng đủ trường brief yêu cầu. Mức: `MEASURED` 22
(cột phạm vi ghi live hay offline), `IMPLEMENTED` 2 (F2, phần ảnh của F4), `PLANNED` 3 (E4, phần nhiều khối của F4,
G1), `HUMAN_REVIEWED` **0**.
Năm ranh giới đứng đầu bản đồ: test kỹ thuật ≠ thực nghiệm sư phạm; replay offline ≠ đánh giá provider live; tự động
PASS ≠ người chấp nhận; 18 bài gold ≠ đúng mọi bài; renderer vẽ được ≠ pipeline hỗ trợ. Không có số mới; phản ví dụ,
lượt thất bại (V3 `FAIL`) và chuỗi đính chính (D-1…D-4, w15→w18) được giữ và trỏ tới bản gốc.

## 7. Việc kế tiếp đã đăng ký

- ROADMAP §0: `CANONICAL_NEXT_ACTION = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES`; chín chỉnh sửa giao diện của
  người dùng (§0.1); bảng ứng viên G03, G04, G05, G16, G06, G17 kèm tầng MISSING và chặn chính từ ma trận v2
  (snapshot W13 — W19 không chọn họ); hồi quy bắt buộc (§0.3); OCR và nhiều khối để sau, không tuyên bố hỗ trợ (§0.4).
- OPEN_ISSUES: `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET` (chặn merge; đóng bằng probe ở biên sản phẩm và
  bằng chứng backstop chặn đúng danh tính; không coi là minor), `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT`,
  `ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED`, `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE` (pytest toàn bộ ở cây chính ghi đè
  một artifact đóng băng; W19 phát hiện khi stage, khôi phục blob đã commit, không commit thay đổi).

## 8. Kiểm chứng

| kiểm | kết quả | file |
|---|---|---|
| `git diff --check` / `--cached --check` | sạch ở cả ba commit | — |
| bộ kiểm tài liệu | PASS: link chuẩn tắc + hub 0 hỏng, CODE_INDEX 0 đường cũ, gốc đóng 198 = 11 + 7 + 180 | `verification/logs/DOCS_AUDIT.log` |
| link / anchor / đường dẫn `docs/…` | tài liệu sống: 0 hỏng do W19; 1 có từ trước (OPEN_ISSUES, tham chiếu tới file chưa từng commit — đã ghi chú); đóng băng 12 và lưu trữ 16, đều có từ trước | `verification/LINKS_BEFORE.json`, `LINKS_FINAL.json` |
| ai còn nhắc đường cũ | 0 trong tài liệu sống, mã, test, công cụ; chỉ evidence đóng băng, bản lưu trữ và bản ghi W19 | `verification/OLD_PATH_CONSUMERS_FINAL.json` |
| danh tính bằng chứng lịch sử | PASS: 8 439 file `docs/evaluation` + 192 tài liệu đóng băng trùng blob; digest trước = sau; 55 file chuyển trùng byte, 10 đổi có nhật ký; 18 hash lịch sử khớp | `verification/FROZEN_IDENTITY.json` |
| candidate / cache | `--verify` exit 0 (`d3b4cab9…`, 110 file) · khoá cache exit 0 (110, `b1714b56…`) | `verification/logs/` |
| test tài liệu | backend 85/85 (thêm 4) · frontend đọc tài liệu 36/36 | `verification/logs/DOCS_TESTS.log` |
| backend toàn bộ | cây chính còn sửa đổi W19 chưa commit: 7003 qua / 2 đỏ — cả hai đọc `git status` và đòi chỉ favicon bẩn; worktree detached sạch của cây cuối `6b926494`: **7005 qua / 0 đỏ** | `verification/logs/PYTEST_FULL_*.log` |
| vitest toàn bộ | 1058/1058 | `verification/logs/VITEST_FULL_MAIN_TREE.log` |

T3 `full-gate.mjs` không chạy: wave chỉ đổi tài liệu và công cụ kiểm tài liệu; mã sản phẩm trùng candidate (verify).

## 9. Giới hạn và phần còn lại

- 180 báo cáo wave cũ vẫn nằm ở gốc `docs/` (R1); chuyển chúng cần người dùng sửa AGENTS.md §4.
- `CODE_INDEX.md` (8,5 nghìn dòng) và `STATUS_LEDGER.md` (1,6 nghìn dòng) không được rà gọn trong W19; W19 chỉ sửa
  đường dẫn và thêm mục của mình.
- Bản thảo khoá luận chưa phản ánh w09–w18 và còn hai thân Chương 4 rời nhau (bản đồ §4; ROADMAP P6).
- Ma trận v2 dùng cho bảng ứng viên là snapshot W13; vài ô có thể đã đổi.
- `D:/tmp` còn 212 mục của các wave trước (210 `UNKNOWN`, 2 bản sao lưu settings); một file lạc duy nhất ngoài kho được giữ (`UNKNOWN`).
- Trong lưu trữ, link tương đối viết cho vị trí cũ (giải bằng bảng di chuyển; bộ kiểm làm đúng điều đó).

## 10. Skill

Đọc trong phiên (invoked cho W18, hiện lại sau khi nén ngữ cảnh) và áp dụng cho W19: writing-plans, executing-plans
(inline + ledger), test-driven-development (guard), systematic-debugging (lỗi guard/link, hai test phụ thuộc trạng
thái cây), verification-before-completion, karpathy-guidelines (thủ công), ponytail-review
(`diagnostics/PONYTAIL_REVIEW_W19.md`). Không dùng: subagent (brief: một agent), impeccable (không sửa giao diện).
