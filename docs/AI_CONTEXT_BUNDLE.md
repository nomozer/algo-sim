# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context

> Handoff cô đọng cho session mới. Code/test thắng khi mâu thuẫn với docs.
> Không chứa secret hoặc raw model output; giới hạn 300 dòng.

## 1. Product và ranh giới

AlgoSim chuyển đề hình học không gian tiếng Việt thành Semantic Program và
Scene3D tương tác. LLM chỉ trích xuất/tổng hợp cấu trúc; engine tất định sở hữu
tọa độ, thực thi, đo lường, correctness và scene state.

- `DEFAULT_MODE = LLM_ONLY`; compiler-first vẫn opt-in.
- `CACHE_VERSION = 104` (w11 bump: envelope `ok` đổi — độ dài đề cho được khai,
  grounding nhận chúng, tham chiếu công thức); provider-facing fingerprint
  `b1714b566e25c912…` không đổi.
- Mọi test/repair gần nhất offline: `LIVE_GEMINI_REQUESTS = 0`.
- Không hardcode case/label/answer vào product; mâu thuẫn phải fail-closed.

## 2. Repository state hiện tại

```text
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
CURRENT_WAVE = W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (w11)
MEASUREMENT_COMMIT = 39e5404686fdf25ddae310759c87c8c64dd8dc41
EVIDENCE_COMMIT = 5e3dbab4 (trace post-processing ac19e03d)
ORIGIN_MAIN_AT_GATE = a9492ee98ff9dc3302d1ff64465f1c06e9001bce
CANDIDATE = df04a613db9c5dd0… (was 8539acbc…), product commit 60292ecf
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
HUMAN_VISUAL_REVIEW = NOT_APPROVED (w10 review = FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR; w11 pending)
USER_DIRTY_STATE = D frontend/public/favicon.svg
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
```

Deletion favicon là thay đổi của người dùng: không restore, sửa, stage hoặc
commit. Không amend/rebase/squash chuỗi commit đã được evidence tham chiếu.

## 3. Wave occlusion đã sửa được gì

- Canonical machine edge IDs dùng endpoint entity IDs (`A_prime`); display label
  (`A′`) là dữ liệu trình bày riêng.
- Mỗi logical edge có một visual owner. Solid phát edge ownership, canonical
  surfaces, `boundary_edge_ids`, `surface_role`, `occludes_edges`.
- Product classifier chia edge thành exact `VISIBLE`/`HIDDEN`/`MIXED` spans bằng
  world-space ray/triangle và adaptive refinement.
- Evidence oracle độc lập dùng projected interval + perspective-correct depth;
  synthetic reference dùng camera ray/triangle.
- Formation events typed ở backend; section endpoints giữ stable semantic
  identity/provenance.
- Năm temporary worktree đã inventory/recover/remove; required/unknown/unique
  commit risk đều 0.

Sáu family đã đo: `triangular_pyramid`, `rectangular_pyramid`,
`triangular_prism`, `cuboid`, `cube`, `cross_section` (mỗi family một fixture
dương + một âm, `inputs/FIXTURE_MANIFEST.json`).

Wave w09 (`VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`) đã khép năm nhóm đỏ:
- 28 test runner khối cong/elip là **lỗi sản phẩm thật**: `scene3d.events[].details`
  mang `Plane3`/`Ellipse3` thô ⇒ HTTP 500 khi ghi cache (P6); sửa ở
  `simulation_state._json_an_toan` (dùng `_than_hinh_hoc`, kiểu lạ ném).
- Mobile recompute mỗi frame: damping làm pose trôi ULP; khoá camera của
  classifier nay 10 chữ số có nghĩa. Harness settle trước khi chụp/mở cửa sổ,
  và xoá bộ đếm cùng lúc reset.
- Camera đóng băng: preimage đã xác minh + tương đương phép chiếu ≤ 0,5 px.
- Guard `boundary` legacy thu hẹp; golden P1/P6 cập nhật sau semantic diff.
- `full-gate.mjs` tìm Python có kiểm chứng (kể cả worktree không venv).

Các gate sau PASS: exact product↔oracle edge IDs/spans, perspective reference,
formation semantics, section identity và worktree recovery.

Wave w10 (`HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE`) trả lời review
người của w09 (`FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR`):
- Playback: bấm Phát một lần đi hết, dừng ở bước cuối, "Xem lại" về bước 0 và
  bỏ chọn; playback không bao giờ tự tạo causal.
- Camera mặc định CHỌN theo số đo cảnh (Z-up, diện tích bao chiếu, độ sâu, khoảng
  đỉnh/đỉnh–cạnh, độ nghiêng mặt), vừa khít theo hình chiếu; "Xem lại toàn hình"
  huỷ đà xoay.
- Nét: cạnh khuất từng KHÔNG có điểm ảnh (GPU kiểm chiều sâu lần hai) — nay phân
  loại CPU là thẩm quyền cho cả hai lớp; mực cạnh riêng; một cạnh một nét.
- Bề mặt học sinh: tên khối theo topology, đáp số + bí danh là một kết luận, lời
  kể có cấu trúc, mặt thiết diện tô ở bước khép; causal phân tầng + làm dịu.
- Bộ đo: kỳ vọng người chuyển sang camera mới chỉ qua khai báo + oracle ở cả hai
  camera; crop chứa trọn cạnh; bấm/kéo không mù.

Wave w11 (`W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW`) trả lời
review người của w10 (`FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR`, W10-H1…H9):
- Công thức: compiler chóp/lăng trụ đáy tam giác vuông khai AB, AC, SA/AD là GIVEN
  (xuất xứ chép từ FactGraph); grounding nhận `XY_length` khớp bất biến độ dài
  của hợp đồng; `references` = đúng vật chữ công thức nhắc tới; "Dựa trên" = nguồn
  số theo thứ tự công thức. Hai ứng viên chiều cao ⇒ không công thức.
- Thị giác: chấm đỉnh theo px CSS (6 / 7,5 hẹp / 9 chọn, token `DAU_DINH_PX`);
  causal bốn tầng theo cạnh `numerical`; đường vô hạn nhạt khi không nhấn; "Xem lại
  toàn hình" bỏ đường vô hạn và chấm đỉnh khỏi khung.
- Bộ đo: cổng ảnh xoay trên ẢNH PHỐI CẢNH, cử chỉ mô phỏng trước (sai số ma trận
  nhìn ≤ 1e-6); nấc con lăn ×DPR; sheet theo họ `images/<họ>/SHEET.png`; chữ ký hình
  của oracle bỏ `quantity` (readout không vẽ).

## 4. Còn mở — không được che

- **Human visual acceptance: NOT_APPROVED** — việc kế tiếp; chưa merge.
- Mới ở w11: `ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED` (tuyến LLM: độ dài chỉ
  có trong fact analyze vẫn làm căn cứ cho GIVEN), `ISSUE-OPS-OFFLINE-SAMPLES-STALE`,
  `ISSUE-OPS-DIST-ACL-OWNERSHIP` (`dist/` cây chính không build được — đo trong worktree).
- Nét vẫn 1 px (WebGL bỏ qua `linewidth`); phân loại khuất theo từng khối (cảnh
  nhiều khối cần `occluders`); script trình duyệt chạy tay còn `URL.pathname`
  (`ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH`).

Tự động tại `39e54046` (detached): browser 12/12 + 12/12 âm, xoay hoạch định đạt
ngay 12/12 · oracle 24/24 · kỳ vọng người `DECLARED_CAMERA_CHANGE` 6/6 · playback
12/12 × 18 kiểm, 60/60 lượt xoay · 64 crop, 0 bất đồng, 0 owner trùng · T3 tại
`5e3dbab4` từ đường dẫn CÓ dấu cách: `FULL_PRODUCT_GATE_PASS` (pytest 6411/0,
vitest 958/0, build, demo, bề mặt sập; 6368/6370/6411 đối soát trong run).

## 5. Bước tiếp theo duy nhất

```text
CANONICAL_NEXT_ACTION = HUMAN_VISUAL_REREVIEW_OF_PEDAGOGICAL_POLISH_EVIDENCE
TARGET_NEXT_ACTION_AFTER_WAVE = HUMAN_VISUAL_REREVIEW_OF_PEDAGOGICAL_POLISH_EVIDENCE
```

Người duyệt theo `HANDOFF.md` của run w11 (sheet từng họ, công thức chóp/lăng trụ
tam giác, crop cạnh khuất, filmstrip playback). Không mở family, image/OCR,
composite geometry trước khi có human visual acceptance; automation không phát
`MERGE_READY`.

## 6. Evidence có thẩm quyền

- Wave hiện hành: `docs/evaluation/geometry/runs/w11-pedagogical-polish/`
  (`REPORT.md`, `HANDOFF.md`, `RUN.json`, `MANIFEST.json`,
  `results/VERIFICATION_SUMMARY.json`, `diagnostics/MEASUREMENT_ATTEMPTS.json`).
- Hai wave trước (bất biến, review người FAIL ghi bổ sung ở run sau):
  `docs/evaluation/geometry/runs/w10-pedagogical-playback/`,
  `docs/evaluation/geometry/runs/w09-verify-cleanup/`.
- Wave bị đính chính (bất biến):
  `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/`.
- Frozen human sets (bất biến): `.../inputs/human_expected_visibility.json` của
  wave occlusion; preimage camera ở `inputs/REGISTERED_CAMERA_PREIMAGES.json` của w09.
- Recovery inventory:
  `docs/evaluation/geometry/worktree-recovery/WORKTREE_RECOVERY_INVENTORY.json`.
- Correction chain owner: `docs/EVIDENCE_INDEX.md`.
- Architecture amendment:
  `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`.

Historical run artifacts are immutable. Run mới phải theo
`docs/evaluation/RUN_NAMING.md` (`wNN-short-slug`; ngày giờ nằm trong `RUN.json`).

## 7. Thứ tự đọc

1. `AGENTS.md`
2. `docs/RULES.md`
3. file này
4. `docs/CURRENT_STATE.md`
5. `docs/OPEN_ISSUES.md`
6. `docs/ROADMAP.md`
7. `docs/CODE_INDEX.md`
8. `docs/EVIDENCE_INDEX.md`
9. Code/test trực tiếp liên quan

## 8. Git và evidence safety

- Staging theo explicit file allowlist; kiểm `git diff --cached --name-only`.
- Không push/merge/rewrite history khi chưa được chỉ định.
- Authoritative measurement chạy từ detached clean worktree tại candidate.
- Product output và oracle output không tự sửa frozen human expectations.
- Historical report/artifact không sửa; sai lệch đi qua correction layer.
