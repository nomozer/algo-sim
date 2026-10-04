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
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
CURRENT_WAVE = W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE (w20)
W20_COMMITS = f0edcd11 … aa036c42 + commit trạng thái/báo cáo/handoff (từng vai trò: `RUN.json` của run w20)
PRODUCT_STATE = w20 — kiểm chứng 5fbb397b (worktree tách rời sạch), candidate 27c31de6… (product commit a4f771b3), CACHE_VERSION 111
ORIGIN_MAIN_AT_GATE = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (ls-remote trong w20: không đổi)
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW (w20)
HUMAN_VISUAL_REVIEW = NOT_APPROVED (W18-H1); MERGE_APPROVAL = NO
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
  (`run_reconciliation(out_dir)`).
- Trình bày (w17–w18): backend gắn nghĩa nhãn, frontend chỉ đặt chỗ; hình mặc định gọn, "Hiện tất cả",
  ô soi là nơi giải thích duy nhất, nhân chứng khoảng cách tới chân chính xác.
- Sáu họ đo trong trình duyệt: `triangular_pyramid`, `rectangular_pyramid`, `triangular_prism`,
  `cuboid`, `cube`, `cross_section`.
- Tự động mới nhất (w20, `5fbb397b`): T3 `FULL_PRODUCT_GATE_PASS` (pytest 7077/0, vitest 1058/1058,
  build, demo, bề mặt sập 6/6); census SHIP (AC2 18/18). Trình duyệt không đo lại (w20 không đổi giao
  diện): bằng chứng hình gần nhất là w18 (12/12 dương + 46/46 âm; occlusion `HUMAN_REVIEW_PENDING`).
- Tuyên bố được phép: `docs/research/CLAIM_EVIDENCE_MAP.md` — 0 hàng `HUMAN_REVIEWED`; năm ranh giới ở §0.

## 5. Còn mở — không được che

- **Chặn merge:** chỉ còn review người w18 `NOT_APPROVED` (W18-H1, kèm W17-H1/W16-H1: bốn cảnh W14 đổi
  `HUMAN_REVIEW_PENDING`). `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET` đã đóng ở w20.
- **Câu hỏi mới của w20** (`HANDOFF.md` của run w20): H-W20-1 câu chữ lời từ chối toạ độ, H-W20-2 nhãn loại
  trên thẻ từ chối, H-W20-3 314 mục dọn chờ quyết định, H-W20-4 tàn dư Tin học trong mã.
- **Quyết định chờ người dùng:** W18-H2 (ô soi lặp dòng giá trị), W18-H3
  (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`), W17-H2 (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`), W15-H2
  (vùng chặn ngoài đa diện), W15-H3 (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`).
- **Từ w19–w20:** `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` (180 báo cáo vẫn ở gốc theo AGENTS.md §4 —
  chờ quyết định), `ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED` (w20 xoá 8/212 mục có bằng chứng, 204 chờ quyết
  định), `ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS` (mới: năm test ghi tạm vào tài liệu sống).
  `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE` đã đóng ở w20.
- Các issue khác và trạng thái từng cái: `docs/OPEN_ISSUES.md` (thẩm quyền).

## 6. Bước tiếp theo duy nhất

```text
CANONICAL_NEXT_ACTION = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
TARGET_NEXT_ACTION_AFTER_WAVE = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
```

Người dùng chọn họ hình từ `docs/ROADMAP.md` §0.2 (ứng viên + khoảng trống theo tầng, snapshot W13);
wave làm họ ấy cùng chín chỉnh sửa giao diện đã chốt (§0.1) và giữ hồi quy §0.3. OCR và nhiều khối để
sau, không tuyên bố đã hỗ trợ. Song song, trước merge: review người w18 (W18-H1). Đề xuất (người dùng chưa
chọn): chóp tứ giác đều + chín chỉnh sửa giao diện, nhánh `feat/regular-square-pyramid-and-ui-requests` —
`HANDOFF.md` §2 của run w20.
Ràng buộc: `LLM_ONLY`; 0 lượt gọi live khi chưa có quyết định ngân sách; `CACHE_VERSION` quyết bằng
bằng chứng; sửa `frontend/src` ⇒ đóng băng lại candidate; không push/merge.

## 7. Evidence có thẩm quyền

- W20 (đóng tính đúng + dọn kho): `docs/evaluation/geometry/runs/w20-cleanup-premerge/` (`REPORT.md`,
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

Historical run artifacts are immutable. Run mới phải theo
`docs/evaluation/RUN_NAMING.md` (`wNN-short-slug`; ngày giờ nằm trong `RUN.json`).

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
