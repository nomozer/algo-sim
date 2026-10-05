# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context

> Handoff cô đọng cho session mới. Code/test thắng khi mâu thuẫn với docs.
> Không chứa secret hoặc raw model output; giới hạn 300 dòng. Lịch sử từng wave:
> `docs/STATUS_LEDGER.md`; bằng chứng và chuỗi đính chính: `docs/EVIDENCE_INDEX.md`.

## 1. Product và ranh giới

AlgoSim chuyển đề hình học không gian tiếng Việt thành Semantic Program và
Scene3D tương tác. LLM chỉ trích xuất/tổng hợp cấu trúc; engine tất định sở hữu
tọa độ, thực thi, đo lường, correctness và scene state.

- `DEFAULT_MODE = LLM_ONLY`; compiler-first vẫn opt-in (20 cổng ở `docs/MIGRATION_CHECKLIST.md`).
- `CACHE_VERSION = 111` (w20: served → rejected cho điểm đề định nghĩa bằng quan hệ mà chương trình đặt
  bằng toạ độ); provider-facing fingerprint `b1714b566e25c912…` không đổi.
- Mọi wave từ w09 chạy offline: `LIVE_GEMINI_REQUESTS = 0`.
- Không hardcode case/label/answer vào product; mâu thuẫn phải fail-closed.

## 2. Repository state hiện tại

```text
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure (task slug cuboid-visual-semantic-closure)
CURRENT_WAVE = COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (run cuboid-final-review — lượt chốt, không đánh số)
RUN_COMMITS = 42dd1af5 … a1c53cdb + commit tài liệu + commit log cổng tài liệu cuối (vai trò: `RUN.json` của run)
PRODUCT_STATE = kiểm chứng a1c53cdb (worktree tách rời sạch), candidate b2d4187a… (product commit 284a9bfa), CACHE_VERSION 111
ORIGIN_MAIN_AT_GATE = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (ls-remote đầu và cuối run: không đổi; nhánh chưa có trên remote)
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW (cuboid-final-review)
HUMAN_VISUAL_REVIEW = NOT_APPROVED (W18-H1 + thẻ từ chối §17 mới); MERGE_APPROVAL = NO
USER_DIRTY_STATE = D frontend/public/favicon.svg
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
```

Deletion favicon là thay đổi của người dùng: không restore, sửa, stage hoặc
commit. Không amend/rebase/squash chuỗi commit đã được evidence tham chiếu.

## 3. Tài liệu nằm ở đâu (từ W19)

- Gốc `docs/`: 11 tài liệu chuẩn tắc + 7 tài liệu dự án (`CORRECTNESS`, `COVERAGE`, `DESIGN_BRIEF`,
  `OPERATIONS`, `DEMO_RUNBOOK`, `TEST_TIERS`, `POST_THESIS_BACKLOG`) + 180 báo cáo wave cũ (bất biến;
  catalog `docs/evaluation/HISTORICAL_REPORTS.md`). Gốc là danh sách ĐÓNG: `audit_docs_layout` đỏ khi
  thêm file chưa phân lớp — báo cáo wave mới chỉ nằm trong thư mục run.
- `docs/research/`: `CLAIM_EVIDENCE_MAP.md` (thẩm quyền duy nhất tuyên bố ↔ bằng chứng ↔ giới hạn),
  `thesis/` (bản thảo, chương, tài liệu tham khảo, hình), `paper/`, phương pháp và tài liệu tham khảo.
- `docs/evaluation/`: run (`geometry/runs/wNN-slug/`), `README.md`, catalog báo cáo cũ.
- `docs/architecture/`: contract đang hiệu lực + snapshot kiểm kê (`README.md` phân biệt).
- `docs/legacy/`: hết hiệu lực — kế hoạch/spec skill, tài liệu giai đoạn chuyển đề, quyết định đã thực
  thi, `CURRENT_STATE_HISTORY.md` (nhật ký cũ của CURRENT_STATE), ba bảng tuyên bố cũ. Loại khỏi grep
  khi tìm luật/trạng thái hiện hành.
- Đường cũ → mới: `docs/evaluation/geometry/runs/w19-docs-organization/inventory/MIGRATION_MAP.json`.
- Hub: `docs/README.md` (năm câu hỏi: hệ làm gì · kiến trúc và cách chạy · việc mở · khoá luận/bài
  báo · bằng chứng).

## 4. Hệ hiện tại (sau w20) — mỗi dòng một chỗ đọc thêm

- Occlusion và danh tính cảnh: edge ID máy theo entity ID (`A_prime`), nhãn hiển thị riêng, một visual
  owner mỗi cạnh, span `VISIBLE`/`HIDDEN`/`MIXED`, oracle cài độc lập —
  `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`.
- Dựng hình theo lớp (w14): `semantic_program/formation.py` chạy cho cả chương trình compiler và LLM.
- Grounding nguồn (w12–w14): độ dài `GIVEN` cần chữ số của đề ngay sau nhãn đoạn.
- Chứng chỉ giả định (w15–w17): C0/C1 trong vùng đa diện; hệ số mặt phẳng gắn đúng mặt phẳng; mệnh đề
  mục tiêu không làm tiền đề; phép cắt gắn câu cắt —
  `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §2–§15.
- Ràng buộc phép dựng (w18, §16): trung điểm/hình chiếu đối chiếu theo danh tính, chặng route
  `construction_binding` (`CONSTRUCTION_NOT_TEXT_BOUND` / `CONSTRUCTION_BINDING_UNVERIFIED`).
- Đích quan hệ đặt bằng toạ độ (w20, §17): trực tiếp hay qua bí danh ⇒ `DEFINED_BY_COORDINATES` ⇒
  `CONSTRUCTION_REPLACED_BY_COORDINATES`, từ chối mọi vùng. Test không ghi bằng chứng đông cứng
  (`run_reconciliation(out_dir)`). Thẻ từ chối (run `cuboid-final-review`): lời ghép từ `reason_subjects`
  ("Hệ chưa kiểm chứng được ‹quan hệ›, vì điểm này ‹cách đặt›…"), không hứa gửi lại; nhãn "chưa kiểm chứng được
  phép dựng" (frontend đọc `reason_code`, không hiển thị).
- Trình bày (w17–w18): backend gắn nghĩa nhãn, frontend chỉ đặt chỗ; hình mặc định gọn, "Hiện tất cả",
  ô soi là nơi giải thích duy nhất, nhân chứng khoảng cách tới chân chính xác.
- Sáu họ đo trong trình duyệt: `triangular_pyramid`, `rectangular_pyramid`, `triangular_prism`,
  `cuboid`, `cube`, `cross_section`.
- Tự động mới nhất (run `cuboid-final-review`, `a1c53cdb`): T3 `FULL_PRODUCT_GATE_PASS` (pytest 7079/0,
  vitest 1061/1061, build, demo 5/5, bề mặt sập 6/6); thẻ từ chối trong trình duyệt 12/12 (desktop +
  mobile). Sáu họ không đo lại: bằng chứng hình gần nhất của chúng là w18 (12/12 dương + 46/46 âm;
  occlusion `HUMAN_REVIEW_PENDING`); census SHIP (AC2 18/18) của w20.
- Tài liệu (run `cuboid-final-review`): phần thời Tin học của CODE_INDEX, STATUS_LEDGER, COVERAGE, CORRECTNESS,
  ARCHITECTURE_MAP, DESIGN_BRIEF, POST_THESIS_BACKLOG nằm nguyên văn ở `docs/legacy/*_INFORMATICS_ERA.md` và
  `legacy/CODE_INDEX_REMOVED_ENTRIES.md`; wave đánh số theo từng việc (`docs/evaluation/RUN_NAMING.md`).
- Tuyên bố được phép: `docs/research/CLAIM_EVIDENCE_MAP.md` — 0 hàng `HUMAN_REVIEWED`; năm ranh giới ở §0.

## 5. Còn mở — không được che

- **Chặn merge:** review người w18 `NOT_APPROVED` (W18-H1, kèm W17-H1/W16-H1: bốn cảnh W14 đổi
  `HUMAN_REVIEW_PENDING`) và các thẻ từ chối §17 mới (ảnh: `HANDOFF.md` §1 của run `cuboid-final-review`).
  `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET` đã đóng ở w20.
- **Câu hỏi** (`HANDOFF.md` của run `cuboid-final-review` §2): H-CFR-1 bỏ câu mời gửi lại ở các lời CONSTRUCTION
  khác, H-CFR-2 chữ hoa/chính tả của nhãn và lời, H-CFR-3 bản công trình liên quan nào ở lại; từ w20: H-W20-3
  (mục dọn ngoài kho chưa kiểm), H-W20-4 (tàn dư Tin học trong mã). H-W20-1/H-W20-2 đã sửa, chờ xem ảnh.
- **Quyết định chờ người dùng:** W18-H2 (ô soi lặp dòng giá trị), W18-H3
  (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`), W17-H2 (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`), W15-H2
  (vùng chặn ngoài đa diện), W15-H3 (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`).
- **Từ w19 tới run `cuboid-final-review`:** `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` = `INTENDED_LIMITATION`
  (180 báo cáo ở gốc, catalog đóng); `ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED` (w20 xoá 8/212; 204 + 108 mục chờ quyết
  định); `ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS` (năm test ghi tạm vào tài liệu sống); mới:
  `ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE` (8/10 script T1 trỏ miền đã gỡ), `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE`
  (22 bất biến có nơi khoá đã gỡ). `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE` đã đóng ở w20.
- Các issue khác và trạng thái từng cái: `docs/OPEN_ISSUES.md` (thẩm quyền).

## 6. Bước tiếp theo duy nhất

```text
CANONICAL_NEXT_ACTION = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
TARGET_NEXT_ACTION_AFTER_WAVE = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
```

Người dùng chọn họ hình từ `docs/ROADMAP.md` §0.2 (ứng viên + khoảng trống theo tầng, snapshot W13);
wave làm họ ấy cùng chín chỉnh sửa giao diện đã chốt (§0.1) và giữ hồi quy §0.3. OCR và nhiều khối để
sau, không tuyên bố đã hỗ trợ. Trước đó, để merge: review người W18-H1 + thẻ từ chối §17 mới; khi duyệt thì
merge thẳng vào `main`, push, xoá nhánh đã merge. Việc kế tiếp chạy trên **nhánh mới rẽ từ `main` đã tích hợp và
cập nhật**, bắt đầu ở **W1** (định danh `<task-slug>-w01`). Đề xuất (người dùng chưa chọn): chóp tứ giác đều + chín
chỉnh sửa giao diện, nhánh `feat/regular-square-pyramid-and-ui-requests` — `HANDOFF.md` §2 của run w20.
Ràng buộc: `LLM_ONLY`; 0 lượt gọi live khi chưa có quyết định ngân sách; `CACHE_VERSION` quyết bằng
bằng chứng; sửa `frontend/src` ⇒ đóng băng lại candidate; không push/merge.

## 7. Evidence có thẩm quyền

- Run `cuboid-final-review` (rà soát trọn tài liệu + thẻ từ chối §17):
  `docs/evaluation/geometry/runs/cuboid-final-review/` (`REPORT.md`, `HANDOFF.md`, `RUN.json`, `MANIFEST.json`,
  `inventory/DOCS_INVENTORY.json`, `inventory/HISTORY_SPLIT.json`, `results/BROWSER_REFUSAL_CFR.json`, `images/`).
- W20 (đóng tính đúng + dọn kho có giới hạn): `docs/evaluation/geometry/runs/w20-cleanup-premerge/` (`REPORT.md`,
  `HANDOFF.md`, `RUN.json`, `MANIFEST.json`, `inventory/DELETION_LOG.json`); luật:
  `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §17.
- W19 (tài liệu): `docs/evaluation/geometry/runs/w19-docs-organization/` (`REPORT.md`, `HANDOFF.md`,
  `inventory/INVENTORY.json`, `inventory/MIGRATION_MAP.json`, `verification/`).
- Hình ảnh hiện hành, chờ người duyệt (w18): `docs/evaluation/geometry/runs/w18-binding-focus/` (`REPORT.md`,
  `HANDOFF.md`, `RUN.json`, `MANIFEST.json`, `diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json`);
  phạm vi đăng ký: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §16.
- Run trước (bất biến) và chủ đề: `docs/evaluation/README.md`; chuỗi đính chính: `docs/EVIDENCE_INDEX.md`.
- Frozen human sets (bất biến): `inputs/human_expected_visibility.json` của wave occlusion; preimage
  camera ở `inputs/REGISTERED_CAMERA_PREIMAGES.json` của w09.

Historical run artifacts are immutable. Run mới phải theo `docs/evaluation/RUN_NAMING.md`: wave đánh số trong
từng việc (việc mới bắt đầu ở W1), định danh đầy đủ `<task-slug>-wNN`; ngày, nhánh, commit, candidate nằm trong
`RUN.json`.

## 8. Thứ tự đọc

1. `AGENTS.md`
2. `docs/RULES.md`
3. file này
4. `docs/CURRENT_STATE.md`
5. `docs/OPEN_ISSUES.md`
6. `docs/ROADMAP.md`
7. `docs/CODE_INDEX.md`
8. `docs/EVIDENCE_INDEX.md`
9. Code/test trực tiếp liên quan

## 9. Git và evidence safety

- Staging theo explicit file allowlist; kiểm `git diff --cached --name-only`.
- Không push/merge/rewrite history khi chưa được chỉ định.
- Authoritative measurement chạy từ detached clean worktree tại candidate.
- Product output và oracle output không tự sửa frozen human expectations.
- Historical report/artifact không sửa; sai lệch đi qua correction layer.
- Báo cáo wave mới nằm trong thư mục run, không ở gốc `docs/`.
