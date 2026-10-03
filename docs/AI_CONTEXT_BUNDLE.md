# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context

> Handoff cô đọng cho session mới. Code/test thắng khi mâu thuẫn với docs.
> Không chứa secret hoặc raw model output; giới hạn 300 dòng.

## 1. Product và ranh giới

AlgoSim chuyển đề hình học không gian tiếng Việt thành Semantic Program và
Scene3D tương tác. LLM chỉ trích xuất/tổng hợp cấu trúc; engine tất định sở hữu
tọa độ, thực thi, đo lường, correctness và scene state.

- `DEFAULT_MODE = LLM_ONLY`; compiler-first vẫn opt-in.
- `CACHE_VERSION = 108` (w16 bump: mười hai yêu cầu được phục vụ trước W16 — mặt phẳng
  mang phương trình của mặt phẳng khác, yêu cầu chứng minh làm tiền đề — nay bị từ chối mà
  vẫn HIT dưới 107, served → rejected); provider-facing fingerprint `b1714b566e25c912…`
  không đổi.
- Mọi test/repair gần nhất offline: `LIVE_GEMINI_REQUESTS = 0`.
- Không hardcode case/label/answer vào product; mâu thuẫn phải fail-closed.

## 2. Repository state hiện tại

```text
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
CURRENT_WAVE = W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE (w16)
MEASUREMENT_COMMIT = 7f3658b00f48dae854e5ab2527ca0ff3f701f828 (second candidate freeze)
EVIDENCE_COMMIT = 705970dd (browser, occlusion, playback, sheets, T3, gates)
ORIGIN_MAIN_AT_GATE = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (re-fetched in w16, unchanged)
CANDIDATE = 9bb0aaa7bddecf94… (was b3b7eb79…; intermediate 8d14469b…), product commit 6b120036
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
HUMAN_VISUAL_REVIEW = NOT_APPROVED for w16 (four W14-changed scenes HUMAN_REVIEW_PENDING + section fill under the edges + refusal panels); MERGE_APPROVAL = NO
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

Wave w12 (`W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE`) trả lời review
người của w11 (`NEEDS_CHANGES`, W11-H1…H5):
- Grounding nguồn: GIVEN phải được CÂU ĐỀ chứng minh (độ dài: nguyên/thập phân
  `.`/`,`/phân số/căn ngay sau nhãn đoạn; P1 tính lại từ đề, một hàm dùng chung);
  lời khai toạ độ có chữ số đề không ghi ⇒ từ chối điểm; ba mã ổn định, không gửi
  đi sửa; lời từ chối nói đúng "độ dài AD"/"toạ độ điểm S". Bất biến #36.
- Dòng thời gian HÌNH HỌC (#35): bước mới chỉ ở sự kiện dựng làm đổi hình; khung
  hiện = sự kiện cuối đoạn (#31/#32 giữ); Phát dừng ở bước dựng cuối. Bảng lời giải
  dưới thanh bước (Kết quả · Dữ kiện · Các bước tính); dải số trên canvas đã gỡ.
- Màu: một bảng vai trò (`scene3d-roles.ts`): xanh = đang xét (được chọn / vừa
  dựng), cam đậm = dữ kiện số, cam nhạt = trung gian, xám = ngữ cảnh (cả NÉT của
  thiết diện/đường/mặt phẳng trong chuỗi), mờ = ngoài chuỗi.
- Bộ đo: bước dựng + lớp lời giải tính độc lập; cổng `CAUSAL_CANVAS_ROLE_HUE` đếm
  sắc độ trên khung causal (lớp phủ HTML bị che), thử trên đáp án đã biết trước khi
  tin. Candidate đóng băng ba lần: `product_commit_sha` = commit cuối chạm
  backend/app HOẶC frontend/src — sửa frontend cũng phải đóng băng lại.

Wave w13 (`W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION`,
chỉ tài liệu) ghi review w12 (`NEEDS_CHANGES`: chóp/lăng trụ tam giác thiếu bước
đường cao, cạnh bên, đáy trên, khép khối; không vá riêng hai họ; kênh giả định còn
mở) và kiểm kê: gốc H1/H2 là mỗi họ compiler tự viết chuỗi câu lệnh; 67 giả định
tuyệt đối (10 cần sửa); ma trận 17 nhóm × 17 tầng
(`docs/architecture/geometry_capability_matrix_v2.json`); tiền đăng ký W14
(`docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`).

Wave w14 (`W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION`) làm tiền đăng ký ấy:
MỘT bước bổ sung dựng hình theo lớp hình (`semantic_program/formation.py`, lá
`solid_faces.py`) chạy trong `verify_and_compile` và `_dung_scene3d` cho chương
trình compiler LẪN LLM (S4); compiler thôi tự viết đường cao/cạnh bên/đáy trên; vai
trò sinh ở `simulation_state`, `scene3d` chỉ chở. Hợp đồng thiếu đề ⇒
`SOURCE_TEXT_MISSING` trừ khi nơi gọi khai `NguonDe.FIXTURE_TIN_CAY`. `dài`/`có độ
dài` vào một từ vựng nối. Cổng giả định đo trên corpus gắn nhãn trước rồi DỪNG
(AC2 0/18). `CACHE_VERSION` 106; candidate đóng băng một lần.

Wave w15 (`W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE`) đóng kênh giả định trong vùng đa
diện:
- Bộ đọc ràng buộc từ đề `semantic_program/shape_constraint.py` dùng từ vựng ĐÓNG và chỉ
  xác nhận. Chứng chỉ `semantic_program/assumption_gate.py` có ba phần: C0 (literal là dữ
  kiện đề CÙNG thực thể, tại định nghĩa với tới duy nhất), C1 (khuôn T1–T6, thể tích, diện
  tích, khoảng cách) và phản ví dụ chỉ khi đề đọc trọn. Thẩm quyền:
  `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`.
- Route có thêm chặng `assumption`. U3: chỉ TỪ CHỐI khi đề nêu khối đa diện theo từ vựng;
  U5: nhiều định nghĩa ⇒ từ chối ở mọi vùng.
- AC2 18/18 `PROVEN_SAFE`, hai phép dò W12 bị từ chối.
- Phần tô thiết diện là vật riêng, không kiểm chiều sâu (trước đó bị lớp chiều sâu đục
  của khối loại ở mọi điểm ảnh).
- `CACHE_VERSION` 107. Candidate đóng băng BA lần: lần 2 sau lỗi phần tô do lượt trình
  duyệt đầu bắt; lần 3 sau một lỗ chứng chỉ do đánh giá cuối toàn nhánh bắt.

Wave w16 (`W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE`) sửa trước merge, không mở
năng lực (amendment §14, đăng ký trước bản sửa):
- §14.1: literal `construct_plane_from_equation` chỉ là dữ kiện khi gắn được với ĐÚNG mặt
  phẳng đề — theo tên (`plane_equation.doc_mat_phang_de`, `ten_mat_phang_cua_bien`, dấu phẩy
  trên là một phần của tên) hoặc duy nhất theo đếm; trùng bộ số không là căn cứ.
- §14.2: mệnh đề mục tiêu (`chứng minh`, `CMR`, `kiểm tra`, `hỏi`, câu `…?`) bị che trước mọi
  bộ đọc tiền đề (`shape_constraint.khoang_muc_tieu`/`che_muc_tieu`).
- Phép dò trước sửa: 12 chương trình sai được PHỤC VỤ; sau sửa từ chối hết, AC2 vẫn 18/18,
  0 ca hợp lệ mới bị từ chối. Bốn nhánh đóng an toàn có test + tiêm lỗi.
- Phần tô thiết diện vẽ ở thứ tự 7 (sau mặt, trước nét) để cạnh khối đè lên nó; cổng ảnh
  mới `SECTION_FILL_UNDER_EDGES`. Sheet nay có đủ sáu ô từ chối; thiếu/trắng ⇒ bộ dựng thất bại.
- Candidate đóng băng HAI lần: lần 2 sau bí danh tên phẩy (P′) ↔ (P) do tự rà soát trước
  bằng chứng bắt. Giới hạn khai A′: C0 không kiểm phép dựng dùng đúng thực thể đề nói.

## 4. Còn mở — không được che

- **Human visual acceptance: chưa duyệt** cho w16 — chưa merge. `HANDOFF.md` run w16:
  **W16-H1** (duyệt bốn cảnh W14 đổi, đang `HUMAN_REVIEW_PENDING`, phần tô thiết diện dưới
  cạnh và sáu ô từ chối mỗi sheet), **W15-H2** (mở rộng vùng chặn ngoài đa diện), **W15-H3**
  (mở rộng từ vựng — cũng là đường đóng giới hạn A′).
- Ở w16: `ISSUE-ARCH-ASSUMPTION-C0-PLANE-EQUATION-ENTITY` và
  `ISSUE-EVAL-ASSUMPTION-GATE-UNTESTED-GUARDS` = RESOLVED. Mới:
  `ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND` (giới hạn A′, strict xfail),
  `ISSUE-ARCH-GROUNDING-GOAL-CLAUSE-AS-DATUM` (grounding vẫn đọc độ dài trong `Chứng minh …`),
  `ISSUE-ARCH-SECTION-FILL-OPAQUE-AUXILIARY-LINES` (nét ĐỤC phụ vẫn dưới phần tô).
- Ở w15: `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION` = PARTIAL (đóng trong vùng đa
  diện; ngoài vùng chỉ ghi, không từ chối — U3). `ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE`
  = RESOLVED theo W15-D1 (n2 bị từ chối đúng, không bắt buộc có dựng hình).
  `ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4` vẫn OPEN. Mới:
  `ISSUE-ARCH-SHAPE-CONSTRAINT-VOCABULARY-COVERAGE` (lối viết ngoài từ vựng ⇒ từ chối),
  `ISSUE-ARCH-ASSUMPTION-C0-PLANE-EQUATION-ENTITY`,
  `ISSUE-EVAL-ASSUMPTION-GATE-UNTESTED-GUARDS`.
- Mới ở w14: `ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4` (kỳ vọng khuất/hiện
  của người không chuyển được sang bốn cảnh S4 đổi — oracle tái tạo đúng tập đã
  duyệt 4/4, cổng vẫn đỏ theo thiết kế). Đã đóng ở w14:
  `ISSUE-ARCH-SOURCE-LENGTH-UNLABELLED-PHRASE`, `ISSUE-OPS-TEST-EXTERNAL-EVIDENCE-PATH`,
  `ISSUE-ARCH-TEXTLESS-CONTRACT-UNCHECKED`. `ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE`
  = PARTIAL (n2); `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION` vẫn OPEN.
- Thiết diện hổ phách ở khung trung tính là câu hỏi thiết kế (W12-D1), không phải lỗi.
- Mới ở w13: `ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE`,
  `ISSUE-ARCH-SOURCE-LENGTH-UNLABELLED-PHRASE` (*"AB dài 5 cm"* ⇒ khai `AC = 5` lọt),
  `ISSUE-OPS-TEST-EXTERNAL-EVIDENCE-PATH` (một test đòi `D:/tmp/...`),
  `ISSUE-ARCH-PROMPT-OBLIQUE-SECTION-STALE`, `ISSUE-ARCH-EXACT-PLACEMENT-FEASIBILITY`,
  `ISSUE-DOCS-STALE-CAPABILITY-CLAIMS`. Hai issue prism cũ đã đánh dấu RESOLVED
  theo mã.
- Mới ở w12: `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION` (toạ độ bố cục/giả
  thiết vẫn có thể cố định một kích thước đề không cho — không gắn GIVEN),
  `ISSUE-EVAL-CDP-SEND-NO-TIMEOUT` (một phản hồi DevTools mất làm treo lượt đo —
  chạy đo có watchdog). Đã đóng: `ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED`.
- Còn mở: `ISSUE-OPS-OFFLINE-SAMPLES-STALE`, `ISSUE-OPS-DIST-ACL-OWNERSHIP`
  (`dist/` cây chính không build được — đo trong worktree),
  `ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH`; nét vẫn 1 px; phân loại khuất theo khối.

Tự động tại `7f3658b0` (detached):
- browser 12/12 dương + 36/36 âm (ba loại, mỗi loại mã riêng); `SECTION_FILL_DISTINGUISHABLE`
  34,20/34,11 (desktop), 34,19/33,74 (mobile); `SECTION_FILL_UNDER_EDGES` ρ ≤ 0,485 < 1;
- occlusion `HUMAN_REVIEW_PENDING` (bốn cảnh W14 đổi, như w15), 0 lỗi;
- playback 12/12 × 19 kiểm; 64 crop, 0 bất đồng, 0 owner trùng; 6 sheet × 6 ô từ chối;
- T3 từ đường dẫn CÓ dấu cách: `FULL_PRODUCT_GATE_PASS` (pytest 6854/0, 1 xfailed = A′,
  vitest 1018/1018, build, demo 5/5, bề mặt sập 6/6).

Worktree tạm của w16 đã gỡ hết.

## 5. Bước tiếp theo duy nhất

```text
CANONICAL_NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_PREMERGE_CLOSURE_EVIDENCE
TARGET_NEXT_ACTION_AFTER_WAVE = HUMAN_VISUAL_REVIEW_OF_PREMERGE_CLOSURE_EVIDENCE
```

Việc của NGƯỜI. Mở `HANDOFF.md` của run w16, duyệt bốn cảnh W14 đổi, phần tô thiết diện
dưới cạnh và các ô từ chối (W16-H1), rồi quyết định W15-H2 và W15-H3. Automation không ghi `APPROVED_BY_USER`,
không sửa registry kỳ vọng người; 0 lượt gọi model; không push/merge; không mở họ mới,
khối cong, nhiều khối, image/OCR.

## 6. Evidence có thẩm quyền

- Wave hiện hành: `docs/evaluation/geometry/runs/w16-premerge-closure/`
  (`REPORT.md`, `HANDOFF.md`, `RUN.json`, `MANIFEST.json`,
  `diagnostics/MEASUREMENT_ATTEMPTS.json`, `diagnostics/ASSUMPTION_MECHANISM_DECISION_W16_R2.json`,
  `diagnostics/PROBE_W16_PHASE1_6d01511.json`, `diagnostics/browser-attempt1-55cde06e/`,
  `images/<họ>/SHEET.png`); phạm vi đăng ký: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §14.
- W15 (bất biến; `READY_FOR_HUMAN_VISUAL_REVIEW`, hai lỗ chứng chỉ do w16 đóng):
  `docs/evaluation/geometry/runs/w15-assumption-closure/`.
- W14 (bất biến; `FORMATION_FOUNDATION_INCOMPLETE`, Track B STOP):
  `docs/evaluation/geometry/runs/w14-generic-formation-assumption/`.
- Tiền đăng ký (chỉ tài liệu): `docs/evaluation/geometry/runs/w13-geometry-preregistration/`.
- Tự động trước đó: `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/`
  (bất biến; review người NEEDS_CHANGES ghi ở run w13).
- Ba wave trước (bất biến, review người ghi bổ sung ở run sau):
  `docs/evaluation/geometry/runs/w11-pedagogical-polish/`,
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
  `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`; kiểm kê và tiền
  đăng ký w13: `docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md`,
  `docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`.

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
