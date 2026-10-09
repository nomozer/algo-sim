# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context

> Handoff cô đọng cho session mới. Code/test thắng khi mâu thuẫn với docs.
> Không chứa secret hoặc raw model output; giới hạn 300 dòng. Lịch sử từng wave:
> `docs/STATUS_LEDGER.md`; bằng chứng và chuỗi đính chính: `docs/EVIDENCE_INDEX.md`.

## 1. Product và ranh giới

AlgoSim chuyển đề hình học không gian tiếng Việt thành Semantic Program và
Scene3D tương tác. LLM chỉ trích xuất/tổng hợp cấu trúc; engine tất định sở hữu
tọa độ, thực thi, đo lường, correctness và scene state.

- `DEFAULT_MODE = LLM_ONLY`; compiler-first vẫn opt-in (20 cổng ở `docs/MIGRATION_CHECKLIST.md`).
- `CACHE_VERSION = 118` (run docs-cleanup: envelope từ chối T8 thiếu kích thước đổi nguyên nhân `UNKNOWN` → `SOURCE`;
  117 ở exact-dimensions — bộ đọc độ dài không lấy vế đầu của biểu thức); provider-facing fingerprint `b1714b566e25c912…`
  không đổi. Run mobile-canvas-fit không bump (chỉ frontend).
- Mọi wave từ w09 chạy offline: `LIVE_GEMINI_REQUESTS = 0`.
- Không hardcode case/label/answer vào product; mâu thuẫn phải fail-closed.

## 2. Repository state hiện tại

```text
CURRENT_BRANCH = feat/regular-square-pyramid (rẽ từ main = 38d41588; W1 + W2 trên origin, W3–W5 và việc regular-triangular-pyramid W1 chỉ ở local; chưa merge)
CURRENT_WAVE = FRONTEND_FREEZE (run frontend-freeze: người dùng hoãn phát triển frontend — chưa hài lòng chất lượng UI; ưu tiên kiến trúc hình học + backend; không đổi mã; máy local; cùng nhánh)
PRODUCT_STATE = candidate 7f3f042309dd1c54… (102 file; product commit 45f5a7f0 — cây đo không đổi, chỉ product_commit_sha dời; đóng băng 83db0e97), CACHE_VERSION 118, LLM_ONLY
MEASUREMENT = 6a1801e7 lần 3, trọn một lượt (dải lớp 3 vai × 8 khổ 24/24, trước 9/24; không dải lớp 55/56 — còn ca xoay màn thấp có từ trước; Tier-A 8/8 một lượt; W02 16/16, W04 24/24, W05 23/24 — một trang không tải); bằng chứng 3095e4f0 (worktree tách rời sạch CRLF, có dấu cách)
ORIGIN_MAIN = 38d4158826cbbffd013d971a9484b9f0fd2a6130 (không đổi)
FINAL_DECISION = WAITING_FOR_EXPLICIT_MERGE_APPROVAL (fast-forward được; C1–C6 đã xem nhưng chưa phê duyệt chất lượng, P1–P6 PENDING, UX debt OPEN/DEFERRED — runs/frontend-freeze/report.md; T3 tại ac55186e phủ cây mã hiện tại)
HUMAN_VISUAL_REVIEW = NOT_APPROVED (gói runs/phone-landscape-layout/review.md F-R1–F-R7 + runs/mobile-canvas-fit/review.md E-R1–E-R6 + runs/exact-dimensions/review.md R1–R10 + runs/regular-triangular-pyramid-w01/REVIEW.md R1–R12 + gói W5 R1–R10 + gói W4 R1–R10, gộp W1–W3)
USER_DIRTY_STATE = không — xoá frontend/public/favicon.svg và dòng .playwright-cli/ của .gitignore đã commit theo lệnh người dùng (f89a1a8b); phần dọn Tin học đã kiểm đã commit (0d4c4f8b)
MAIN_PUSH_EXECUTED = NO · MERGE_EXECUTED = NO · PR_CREATED = NO
NEXT_ACTION = người dùng quyết: tích hợp baseline frontend tạm thời có ngoại lệ? merge + push main? xoá nhánh? — nếu có, agent ghi runs/frontend-freeze/APPROVAL.md nguyên văn rồi fast-forward main; sau đó Cloud theo runs/frontend-freeze/handoff.md (kiến trúc hình học + backend; frontend đóng băng)
```

Thay đổi chưa commit của người dùng: không restore, sửa, stage hoặc commit khi chưa được cho phép rõ ràng (xoá favicon đã
được cho phép và commit ở f89a1a8b). Không amend/rebase/squash chuỗi commit đã được evidence tham chiếu.

## 3. Tài liệu nằm ở đâu

- Gốc `docs/`: tài liệu chuẩn tắc/dự án và 11 contract/report ngoại lệ có ràng buộc đường dẫn cụ thể. Catalog
  `docs/evaluation/HISTORICAL_REPORTS.md` trỏ 167 báo cáo: 33 report nằm cạnh package artifact, 123 report ở
  `docs/evaluation/reports/`, 11 ngoại lệ ở gốc. `audit_docs_layout` kiểm cả root đóng và đích catalog.
- `docs/research/`: `CLAIM_EVIDENCE_MAP.md` (thẩm quyền duy nhất tuyên bố ↔ bằng chứng ↔ giới hạn),
  `thesis/` (bản thảo, chương, tài liệu tham khảo, hình), `paper/`, phương pháp và tài liệu tham khảo.
- `docs/evaluation/`: run (`geometry/runs/wNN-slug/`), `README.md`, catalog báo cáo cũ.
- `docs/architecture/`: contract đang hiệu lực + snapshot kiểm kê (`README.md` phân biệt).
- `docs/legacy/`: hết hiệu lực — kế hoạch/spec skill, tài liệu giai đoạn chuyển đề, quyết định đã thực
  thi, `CURRENT_STATE_HISTORY.md` (nhật ký cũ của CURRENT_STATE), ba bảng tuyên bố cũ. Loại khỏi grep
  khi tìm luật/trạng thái hiện hành.
- Đường report cũ → mới: inventory hợp nhất `docs/evaluation/geometry/runs/docs-cleanup/inventory.md`; bản đồ máy W19
  lịch sử vẫn ở `docs/evaluation/geometry/runs/w19-docs-organization/inventory/MIGRATION_MAP.json`.
- Hub: `docs/README.md` (năm câu hỏi: hệ làm gì · kiến trúc và cách chạy · việc mở · khoá luận/bài
  báo · bằng chứng).

## 4. Hệ hiện tại (sau regular-square-pyramid-w01) — mỗi dòng một chỗ đọc thêm

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
- Chóp tứ giác đều (regular-square-pyramid-w01): bộ đọc "đều"/cạnh đáy/cạnh bên/trung đoạn/tâm đáy, khuôn C1 T7,
  tâm O gắn theo danh tính (giao hai đường chéo), chiều cao đo được của thể tích; chiều cao vô tỉ, góc, chóp tam
  giác đều chưa phục vụ; cạnh bên đọc cả từ `SA = 3` (tự rà soát cuối, `ad7172ab`), chuỗi `SA = SB = … = 3` chưa
  (`ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY`). Giao diện ROADMAP §0.1: card Kết quả ẩn khi thu gọn, ngăn «Đại lượng», panel «Các bước
  dựng», gỡ dải «Đang dựng»; cổng phạm vi nhận "độ dài".
- Khép sư phạm (regular-square-pyramid-w02): nhãn đoạn chỉ khi đoạn mang nó đã dựng; bảng nổi «Các bước dựng» (kéo,
  phím, kẹp; mobile thu gọn); đoạn SO qua bước bổ sung (`formation._tam_day_deu`); chiều cao của công thức theo quan hệ
  ⊥ (`quantity_annotations.chieu_cao_the_tich`); hình phụ (`scene3d-auxiliary.ts`) và lưới tuỳ chọn; độ dài ≤ 0 do
  đề ghi ⇒ `NON_POSITIVE_LENGTH`/SOURCE trên tuyến mặc định (PARTIAL).
- Nghiệm thu local (regular-square-pyramid-w03): mặt phẳng phụ chỉ để đo không mở bước dựng (`measurementOnlyPlanes`;
  miễn trừ W2 ở ba cổng đã gỡ); đoạn đề hỏi độ dài được dựng trước đáp số (`formation._doan_duoc_hoi`; giới hạn
  `ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE`). Đo `a5d233ce`: suite 7/7, 14/14 lượt dương xanh, đầu dò W2 14/14,
  occlusion 0 lỗi, phát lại không miễn trừ.
- Giao diện chung (regular-square-pyramid-w04): mọi bảng thông tin là `BangNoi` (`scene3d-floating-panel.tsx`; không
  cột, không đổi canvas/camera/bước; nhiều bảng cùng mở; khổ hẹp là tấm trong dòng chảy); canvas theo chiều cao khả
  dụng (`caoKhungKhaDung`), «Bước n/N» trong thanh; cây «Thành phần» theo bước (`treeAt`, nhóm `<details>` thu gọn);
  lời kể theo ký hiệu đề (`ten_trong_loi_ke`); đoạn con trên cạnh khối nhường nét (`doan_tren_canh`, `edge_span`).
  Đo `103494c4`: suite 7/7, đầu dò W2 14/14, đầu dò W4 21/21 (7 họ × 3 khổ), occlusion 0 lỗi, phát lại pass.
- Chế độ tập trung (regular-square-pyramid-w05): cảnh 3D không dựng `nav-bar` (`App`, gốc `la-tap-trung`, một hàng lưới),
  nút quay lại về trang trước (`returnView`/`roiXuong`), công cụ nhóm qua `MenuCongCu` (`scene3d-tool-menu.tsx`), toàn
  màn hình tuỳ chọn; thẻ lời giải `scene3d-solution.tsx` đã gỡ (đại lượng ở «Đại lượng», công thức ở ô soi, chú giải trong
  «Hiển thị»); bộ đọc độ dài nguồn đọc chuỗi bằng nhau (`segment_relation.cac_doan_truoc`). Đo `f01df0e5`: suite 7/7,
  W2 14/14, W4 21/21, W05 21/21, occlusion 0 lỗi, phát lại 14/14.
- Điện thoại (mobile-canvas-fit, D5): khổ hẹp ≤ 48rem canvas cao vừa hình (`scene3d-playback.caoKhungVuaHinh`, tỉ lệ
  `scene3d-view.tiLeKhungHinh` cùng điểm/phép xoay/hướng với phép vừa khung; ≤ phần khả dụng, ≥ 320 px; hình ràng theo
  chiều cao giữ nguyên); bảng bước giữ bước đang xem trong thân bảng. 390×844: canvas 519 → 320–485 px, bảng mở thấy
  cùng hình. Đầu dò `frontend/scripts/check-mobile-layout.mjs`.
- Điện thoại ngang (phone-landscape-layout): ngang thấp (`(orientation: landscape) and (max-height: 30rem)`) ⇒ thanh điều khiển
  thành cột 10rem cạnh canvas (canvas giữ chiều cao, hình giữ cỡ; hai nút xem ở đầu cột; ≤ 48rem dùng bố cục rộng, bảng nổi);
  360 px: ba nút phát một hàng. 844×390 · 667×375 · 844×340 · 360×640 điều khiển trong khung; xoay máy giữ bước/lựa chọn/camera.
- Bảy họ đo trong trình duyệt: `triangular_pyramid`, `rectangular_pyramid`, `triangular_prism`,
  `cuboid`, `cube`, `cross_section`, `regular_square_pyramid`.
- Đo mới nhất (regular-square-pyramid-w01, `ed37f9fa`): bảy họ 14/14 dương, 54/54 âm, 6/6 phục vụ, chọn đại lượng
  68/68, ngăn đại lượng + panel bước 14/14; occlusion 0 lỗi (bốn cảnh W14 `HUMAN_REVIEW_PENDING`); playback 14/14;
  T3 ở commit tài liệu (log trong run).
- Tự động trước đó (run `cuboid-final-review`, `a1c53cdb`): T3 `FULL_PRODUCT_GATE_PASS` (pytest 7079/0,
  vitest 1061/1061, build, demo 5/5, bề mặt sập 6/6); thẻ từ chối trong trình duyệt 12/12 (desktop +
  mobile). Sáu họ không đo lại: bằng chứng hình gần nhất của chúng là w18 (12/12 dương + 46/46 âm;
  occlusion `HUMAN_REVIEW_PENDING`); census SHIP (AC2 18/18) của w20.
- Tài liệu (run `cuboid-final-review`): phần thời Tin học của CODE_INDEX, STATUS_LEDGER, COVERAGE, CORRECTNESS,
  ARCHITECTURE_MAP, DESIGN_BRIEF, POST_THESIS_BACKLOG nằm nguyên văn ở `docs/legacy/*_INFORMATICS_ERA.md` và
  `legacy/CODE_INDEX_REMOVED_ENTRIES.md`; wave đánh số theo từng việc (`docs/evaluation/RUN_NAMING.md`).
- Bất biến (run `cuboid-acceptance`): 24 hàng §5 của ARCHITECTURE_MAP có con trỏ chết đã đối chiếu tới assertion —
  9 đang khoá, 1 chưa đủ bằng chứng (#14), 14 **LỊCH SỬ**, 0 vi phạm; cột con trỏ chỉ còn file sống
  (`results/INVARIANT_RECONCILIATION.json` của run). Run `repo-cleanup` gỡ `editViaServer`, `AIHelpPanel` + `/api/explain`,
  `AttemptObserver` và mọi mã chết Tin học khác; còn lại có lý do: `specDrift`, chính sách `threeD`, `SamplePreview`, prompt
  và từ vựng IR (`ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE`, `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`).
- Tuyên bố được phép: `docs/research/CLAIM_EVIDENCE_MAP.md` — 0 hàng `HUMAN_REVIEWED`; năm ranh giới ở §0.

## 5. Còn mở — không được che

- **frontend-freeze (2026-10-09):** người dùng hoãn phát triển frontend (chưa hài lòng chất lượng UI) để ưu tiên kiến trúc
  hình học + backend. C1–C6 đã xem, chưa phê duyệt; P1–P6 PENDING; UX debt OPEN/DEFERRED; W05 23/24; W14 registry chưa có.
  Chờ quyết định merge tường minh; handoff Cloud `runs/frontend-freeze/handoff.md`.
- **merge-readiness (chờ người dùng):** danh sách nghiệm thu tối thiểu `runs/merge-readiness/report.md` §4. 671 hồ sơ cũ
  `%TEMP%\w12-*` đã xoá sau xác nhận (C: trống 43,87 → 77,43 GB); `scoped_dir*` không đụng. Favicon + `.gitignore` đã commit.
- **browser-temp-lifecycle (hạ tầng kiểm thử):** `ISSUE-OPS-BROWSER-SESSION-PROFILE-LEAK` RESOLVED — hồ sơ Chrome của bộ đo ở
  `D:/tmp/algosim-browser`, xoá khi phiên đóng/hỏng, orphan dọn theo `owner.json`. Còn: 20 script trình duyệt độc lập.
- **classroom-band-fit chờ người dùng:** `runs/classroom-band-fit/review.md` H-1…H-3 (ảnh, quyết chip chỉ hiện chấm màu ở
  640–667 px ngang) và C-1…C-4 (thao tác tay chế độ lớp). `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` RESOLVED (chờ duyệt;
  24/24, trước 9/24); giới hạn còn lại ghi trong issue.
- **final-acceptance chờ người dùng:** thao tác tay G-1…G-9 (= E-R6 + F-R7; chạm giả lập 8/8 chỉ là hỗ trợ) và D-2…D-4 của
  `runs/final-acceptance/review.md` (D-1 đã xử lý ở classroom-band-fit). UX debt người dùng chấp nhận tạm, vẫn OPEN: bảng nổi
  che canvas khi ngang, nhãn rời canvas ở màn thấp, `ISSUE-ARCH-MOBILE-HEADER-TOOLBAR-LAYOUT`.
- **phone-landscape-layout chờ người dùng:** duyệt `review.md` F-R1–F-R7 (F-R7 + E-R6 cần thao tác tay). Quyết: bảng nổi phủ
  canvas hẹp khi ngang (`ISSUE-ARCH-LANDSCAPE-FLOATING-PANEL-COVERS-CANVAS`), ca xoay màn thấp (`ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`,
  khôi phục bằng «Xem lại toàn hình» 56/56). `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD` RESOLVED (chờ duyệt).
- **mobile-canvas-fit chờ người dùng:** duyệt `review.md` E-R1–E-R6 của run (D5 RESOLVED, chờ duyệt). Mở mới (có từ trước, chờ
  quyết): `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD`, `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`. Sửa ở bộ đo: băm
  oracle_source lệch (node 96/97 tại 38a19c65) và kỳ vọng cũ của suite cho ca T8 thiếu chiều cao.
- **Đã tích hợp:** người dùng ACCEPTED A–F của `REVIEW.md` (run `cuboid-merge`, `APPROVAL.md`); `main` fast-forward
  tới `c282a5f3` và push. Giới hạn F1–F5 được **hoãn, vẫn mở** (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`, vùng đa
  diện của #37, `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`, `ROADMAP.md` §0.4,
  `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`); registry khuất/hiện mới vẫn chưa có (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`).
- **Đã quyết (người dùng, brief `cuboid-acceptance`):** H-CFR-2 giữ chữ thường và "toạ độ"; H-CFR-1 = backlog giao
  diện, không sửa sản phẩm lúc này; H-CFR-3 `THESIS_DRAFT` §1.8 là bản chính đề xuất, chưa xoá `RELATED_WORK_DRAFT`
  khi chưa đối chiếu nội dung riêng; 204 mục `D:/tmp` + 108 mục `.superpowers` giữ nguyên, không chặn merge.
- **Câu hỏi còn mở từ w20:** H-W20-4 (tàn dư Tin học trong mã) — xử lý ở run `repo-cleanup`; phần còn lại có lý do ở hai
  issue `ISSUE-ARCH-*-INFORMATICS-*`. H-W20-1/H-W20-2 đã sửa, chờ xem ảnh.
- **docs-cleanup (2026-10-08):** tên test theo hành vi (123 hàm, 118 tiêu đề), `docs/legacy/` 42 → 15 file (Superpowers M9–M17,
  W13 và tài liệu chuyển đề gỡ; thiết kế route → `legacy/architecture/`; contract cuboid về `architecture/`), 12 lớp CSS chết;
  còn `SamplePreview`/`threeD`/`specDrift` và sáu prompt + IR Tin học — kiểm kê: `runs/docs-cleanup/inventory.md`.
- **repo-cleanup (2026-10-08):** gỡ 132 file Tin học hết vai trò, 325 selector CSS chết, đổi tên 29 file theo chức năng;
  `ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE` khép; inventory + lý do giữ: `runs/repo-cleanup/report.md`.
- **exact-dimensions chờ người dùng:** duyệt `review.md` R1–R10 của run. Khép: `ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES`
  (khung affine + metric Gram; kích thước chữ, tổng căn vẫn từ chối). Mở mới: `ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART`.
  `ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED` vẫn mở (mọi khung nay phục vụ; mô hình chưa đo). D5 đã triển khai ở run mobile-canvas-fit (chờ duyệt).
- **regular-triangular-pyramid-w01 chờ người dùng:** duyệt hình `REVIEW.md` R1–R12 của run; D5
  (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`) đã triển khai ở run mobile-canvas-fit. Mở mới: `ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES` (miền ℚ³),
  `ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED`, `ISSUE-ARCH-TETRAHEDRON-OUTSIDE-POLYHEDRAL-REGION`. Khung nhìn ban đầu
  đã sửa cho mọi họ (hình nay ở giữa) — ảnh trung tính khác W5 (dịch ngang).
- **W5 (IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE) chờ người dùng:** duyệt hình theo `REVIEW.md` của run
  regular-square-pyramid-w05 cùng gói W4. R4 của W4 (trần chiều cao canvas mobile) đã được brief W5 trả lời: không trần.
- **W4 (SHARED_SIMULATION_UI_CLOSURE):** gói duyệt R1–R10 của run regular-square-pyramid-w04. Người dùng không chấp nhận hoãn H-W2-3 ⇒ W4 đưa mọi bảng thông tin lên một
  cơ chế bảng nổi (`ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS` RESOLVED); SM trên SA nhường nét
  (`ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE` RESOLVED); tên nhóm «Giao điểm của AC và BD» giữ theo yêu cầu.
- **W3 (đã đóng):** H-W2-2, H-W2-4 đã sửa (lỗi); hai worktree đo của W3 đã gỡ.
- **W1 chờ người dùng:** H-W1-1 (duyệt hình — chặn merge), H-W1-2 (chiều cao hiện `d(S, (ABC))`, không vẽ SO),
  H-W1-3 (mặt phẳng phụ để đo), H-W1-4 (bước dựng phụ AC, BD, O), H-W1-5
  (`ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE`) — `HANDOFF.md` §1 của run regular-square-pyramid-w01.
- **Quyết định chờ người dùng:** W18-H2 (ô soi lặp dòng giá trị), W18-H3 đã giải quyết ở W1
  (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE` RESOLVED), W17-H2 (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`), W15-H2
  (vùng chặn ngoài đa diện), W15-H3 (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`).
- **Sau lần report organization trong `docs-cleanup`:** `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` = `RESOLVED` (156 report chuyển,
  11 ngoại lệ root); `ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED` (w20 xoá 8/212; 204 + 108 mục chờ quyết
  định); `ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS` (năm test ghi tạm vào tài liệu sống); mới:
  `ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE` (8/10 script T1 trỏ miền đã gỡ); run `cuboid-acceptance`:
  `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM` (smoke script Tin học đã retire, còn `run_rectangular_pyramid_live_analyze.py`; không chặn merge).
  Đã đóng: `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE` (`cuboid-acceptance`),
  `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE` (w20).
- Các issue khác và trạng thái từng cái: `docs/OPEN_ISSUES.md` (thẩm quyền).

## 6. Bước tiếp theo duy nhất

```text
CANONICAL_NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_REGULAR_PYRAMID_EVIDENCE
TARGET_NEXT_ACTION_AFTER_WAVE = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
```

Việc `phone-landscape-layout` (máy local, cùng nhánh) đưa điều khiển vào khung khi ngang và ở 360 px, chạy nghiệm thu cuối (Tier-A
8/8 một lượt, T3); việc kế tiếp: người dùng duyệt `review.md` của run này cùng các gói dưới. Việc `mobile-canvas-fit` (máy local, cùng nhánh) khép D5 theo phương án (b) thu hẹp ở khổ hẹp và đo lại tám họ trên candidate
cuối; việc kế tiếp: người dùng duyệt `review.md` của run này cùng các gói dưới. Việc `docs-cleanup` (máy local, cùng nhánh) khép đổi tên test, xử lý `docs/legacy/` + kế hoạch Superpowers và CSS chết, không
đổi hành vi; việc kế tiếp không đổi. Việc `repo-cleanup` (máy local, cùng nhánh) gỡ phần Tin học hết vai trò và chuẩn hoá tên, không đổi hành vi; việc kế tiếp
không đổi. Việc `exact-dimensions` (máy local, cùng nhánh) phục vụ chóp tam giác đều/tứ diện đều với kích thước hữu tỉ bằng khung
affine + metric Gram suy từ đề, chụp ảnh quyết tại nguồn (109 → 15 ảnh cùng ca) và chuẩn hoá tên; việc kế tiếp: người dùng
duyệt `review.md` của run `exact-dimensions` cùng các gói dưới. Việc `regular-triangular-pyramid` W1 (máy local, cùng nhánh) đã thêm chóp tam giác đều + tứ diện đều trong miền ℚ³ trên route
sản phẩm, sửa D1–D4, xoay hiển thị đáy nghiêng và khung nhìn ban đầu; việc kế tiếp: người dùng duyệt `REVIEW.md` của run
`regular-triangular-pyramid-w01` (R1–R12) cùng gói W5/W4 và chọn phương án D5. Bối cảnh trước đó: W5 của việc `regular-square-pyramid` (máy local) đã làm chế độ tập trung (không thanh trên toàn cục, quay lại, công cụ
nhóm, toàn màn hình tuỳ chọn, bỏ thẻ lời giải lặp) và lát cắt backend "chuỗi bằng nhau" trên route thật. Việc kế tiếp:
người dùng duyệt hình theo `docs/evaluation/geometry/runs/regular-square-pyramid-w05/REVIEW.md` cùng gói W4
(gộp duyệt W1–W3); khi có phê duyệt
tường minh thì merge thẳng `feat/regular-square-pyramid` vào `main` (không PR), push, xoá nhánh. Sau đó (phần dưới
là bối cảnh trước W1, giữ để tra): người dùng chọn họ hình từ `docs/ROADMAP.md` §0.2 (ứng viên + khoảng trống theo tầng, snapshot W13);
wave làm họ ấy cùng chín chỉnh sửa giao diện đã chốt (§0.1) và giữ hồi quy §0.3. OCR và nhiều khối để
sau, không tuyên bố đã hỗ trợ. Trước đó, để merge: duyệt hình theo `REVIEW.md` của run `cuboid-merge` (A–F); khi có
phê duyệt tường minh thì merge thẳng vào `main` (không PR), chạy cổng trên cây tích hợp,
push, kiểm SHA remote, xoá nhánh đã merge. Việc kế tiếp chạy trên **nhánh mới rẽ từ `main` đã tích hợp và cập
nhật**, bắt đầu ở **W1**. Đề xuất (người dùng chưa chọn): chóp tứ giác đều + chín chỉnh sửa giao diện, slug
`regular-square-pyramid`, run đầu `regular-square-pyramid-w01` — `HANDOFF.md` §4 của run `cuboid-acceptance`.
Ràng buộc: `LLM_ONLY`; 0 lượt gọi live khi chưa có quyết định ngân sách; `CACHE_VERSION` quyết bằng
bằng chứng; sửa `frontend/src` ⇒ đóng băng lại candidate; không push/merge.

## 7. Evidence có thẩm quyền

- Run `phone-landscape-layout` (PHONE_LANDSCAPE_LAYOUT): `docs/evaluation/geometry/runs/phone-landscape-layout/` (`review.md`, `report.md`,
  `handoff.md`, `run.json`, `plan.md`, `MEASUREMENT_ATTEMPTS.json`, `inputs/REVIEW_SET.json`, `results/`, `images/`, `diagnostics/`).
- Run `mobile-canvas-fit` (MOBILE_CANVAS_FIT): `docs/evaluation/geometry/runs/mobile-canvas-fit/` (`review.md`, `report.md`,
  `handoff.md`, `run.json`, `plan.md`, `inputs/REVIEW_SET.json`, `results/`, `images/`, `diagnostics/`).
- Run `docs-cleanup` (DOCUMENTATION_AND_NAMING_CLEANUP): `docs/evaluation/geometry/runs/docs-cleanup/` (`report.md`,
  `handoff.md`, `run.json`, `inventory.md`, `diagnostics/`).
- Run `repo-cleanup` (REPO_CLEANUP): `docs/evaluation/geometry/runs/repo-cleanup/` (`report.md`, `handoff.md`, `run.json`,
  `inventory.json`, `code_index_removed_entries.md`, `relocated/`, `inputs/candidate_divergence.json`, `diagnostics/`).
- Run `exact-dimensions` (EXACT_DIMENSIONS_AND_CAPTURE_POLICY): `docs/evaluation/geometry/runs/exact-dimensions/`
  (`review.md`, `report.md`, `handoff.md`, `run.json`, `plan.md`, `labels.json`, `capture_counts.json`, `results/`, `images/`,
  `diagnostics/attempt1–3/`).
- Run `regular-triangular-pyramid-w01` (REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE):
  `docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `MEASUREMENT_ATTEMPTS.json`, `results/`, `images/`, `diagnostics/`, `corrections/W05_RECORD_CORRECTION.json`).
- Run `regular-square-pyramid-w05` (IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w05/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `MEASUREMENT_ATTEMPTS.json`, `results/`, `images/`, `diagnostics/`).
- Run `regular-square-pyramid-w04` (SHARED_SIMULATION_UI_CLOSURE):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w04/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `MEASUREMENT_ATTEMPTS.json`, `results/`, `images/`, `diagnostics/`).
- Run `regular-square-pyramid-w03` (nghiệm thu local W2 + H-W2-2, H-W2-4):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w03/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `results/`, `images/`, `diagnostics/baseline_fe68b4ca/`).
- Run `regular-square-pyramid-w01` (chóp tứ giác đều + giao diện §0.1):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w01/` (`REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `results/BROWSER_EVIDENCE.json`, `results/OCCLUSION_MEASUREMENT.json`, `results/PLAYBACK_EVIDENCE.json`, `images/`).

- Run `cuboid-merge` (gói duyệt + chuyển tiếp ảnh W18 sang `b2d4187a`): `docs/evaluation/geometry/runs/cuboid-merge/`
  (`REVIEW.md`, `HANDOFF.md`, `RUN.json`, `results/FIXTURE_TRANSFER.json`, `results/logs/`).
- Run `cuboid-acceptance` (đối chiếu 24 bất biến + hồ sơ nghiệm thu, chỉ tài liệu):
  `docs/evaluation/geometry/runs/cuboid-acceptance/` (`REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `results/INVARIANT_RECONCILIATION.json`, `results/logs/`).
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

Artifact còn làm căn cứ cho claim/repro giữ nguyên byte; artifact hết consumer có thể xoá qua inventory có kiểm theo
AGENTS §4. Run mới theo `docs/evaluation/RUN_NAMING.md` (mục đầu, từ run `exact-dimensions`):
tên theo việc, không mã lượt; lần thứ hai của cùng việc thêm ngày; ngày, nhánh, commit, candidate nằm trong `run.json`.

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
- Evidence còn dùng không sửa byte; sai lệch đi qua correction layer. Mục hết vai trò được xoá qua inventory + kiểm consumer.
- Báo cáo wave mới nằm trong thư mục run, không ở gốc `docs/`.
