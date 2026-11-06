# Axo — Học sinh chủ động xem kết quả, đề bài khớp mô hình, nghiệm thu Scene3D

Ngày: 2026-11-05. Trạng thái: **READY FOR USER REVIEW** — chưa merge, chưa push, không có lời gọi AI live.

## A. Trạng thái mã nguồn

| | |
|---|---|
| Worktree | `.superpowers/worktrees/axo-pedagogical-integration` |
| Branch | `integration/axo-pedagogical-construction-hardening` |
| HEAD trước | `219434ea` (commit sản phẩm `34c779e1`) |
| Commit mới | `69b9497f` fix(frontend): xem kết quả theo yêu cầu + đề bài gắn với bản ghi đang mở · `514d34d4` fix(scene3d): lời dẫn tiếp diện · commit eval (con dấu candidate + bằng chứng này) |
| Thay đổi người dùng | `frontend/index.html` (đổi tiêu đề AlgoSim → Axo) **không stage, không sửa**; SHA256 `3B8A5566…A69F` khớp trước/sau. Các thư mục chẩn đoán chưa track của run trước giữ nguyên. |
| Backend | 0 file sửa. `measured_system` 118 file `6809d79b…` không đổi, `CACHE_VERSION` 131 giữ nguyên (không có thay đổi prompt/policy). |
| Lưu ý nhánh | Nhánh đi trước `main` 84 commit và **đã phân kỳ** với `main` `bb61a804` (cutover Hybrid `/4` chỉ có trên `main`). Merge sẽ cần hoà giải riêng — không làm trong run này. |

File sản phẩm đã sửa: `frontend/src/components/SimulationWorkspace.tsx`, `frontend/src/styles/global.css`, `frontend/src/simulations/domains/geometry/scene3d-semantic-policy.ts`. Test/tooling: 3 test mới, 7 suite cập nhật kỳ vọng, `scripts/axo-result-reveal-browser-check.mjs` (mới), `scripts/measure-axo-performance.mjs` (sửa fixture).

## B. Danh sách lỗi

### B1 (P0) — Đáp án tự hiện ở bước cuối
- **Triệu chứng:** tới bước cuối là thấy R = 3, V = 36π; r = 4, S = 16π; tương tự trụ, nón, khoảng cách.
- **Nguyên nhân gốc:** `AxoWorkspaceV62` render `#dock-goal-conclusion` mỗi khi `presentationPolicy.finalConclusions` khác rỗng (có chủ đích ở run trước, ghi là "chờ quyết định").
- **Cách sửa:** nút **Xem kết quả** (`#dock-goal-reveal`, `aria-expanded`), chỉ có khi có kết luận đã xác minh (`DERIVED_VERIFIED`, thuộc tập mục tiêu — chính sách lọc cũ giữ nguyên). Trạng thái mở gắn với đúng đối tượng cảnh + `problemSnapshotKey` + `replayNonce` và bị xoá **ngay trong lượt render** khi rời bước cuối, nên không có khung hình nào lộ đáp án bài cũ trên bài mới. Thu gọn bằng chính nút đó; hình 3D không đổi. Khi chưa bấm, nội dung đáp án không nằm trong DOM (kể cả nhãn cho trình đọc màn hình).
- **Bằng chứng:** `browser-final/desktop-final-before-reveal.png` → `desktop-final-after-reveal.png`; camera và số GPU buffer không đổi khi mở (`browser-final/receipt.json`).
- **Khoá hồi quy:** `scene3d-result-reveal.test.tsx` (9 bài mẫu có kết quả: không có giá trị/lý do trong SSR; bài chỉ dựng hình không có nút; bước sớm không có nút). Tiêm lỗi (render panel khi `coKetQua`) ⇒ 9/9 đỏ. 12 khẳng định SSR cũ trong 7 suite đổi từ "phải hiện đáp án" sang "phải có nút, không có đáp án".

### B2 (P0) — Đề bài S.ABCD hiện cạnh cảnh `greatCircleScene`/`tangentScene`
- **Phân loại:** lỗi **fixture kiểm thử**, không phải route sản phẩm.
- **Nguyên nhân gốc:** `measure-axo-performance.mjs` nạp fixture mặt cầu bằng `{ ...samples[0].envelope, title: name, scene3d }`. Fixture thừa hưởng `description`, `config.title`, `config.frames` của bài `thiet-dien-chop`; store định danh bản ghi theo `simulation_id + config` nên còn **gán nhầm fixture vào bài mẫu S.ABCD** (URL, bước đã lưu, đề bài), và tiêu đề là tên kỹ thuật.
- **Cách sửa:** mỗi fixture có tiêu đề + đề tiếng Việt riêng, `config.title` riêng, `source: synthetic_fixture`, đánh dấu `synthetic: true`; harness khẳng định `activeSampleId === null` và đề trong dock khớp fixture.
- **Bằng chứng:** `ui-final/greatCircleScene.png`, `tangentScene.png` — tiêu đề "Mặt phẳng tiếp xúc với mặt cầu", đề đúng.
- **Đính chính:** ảnh `axo-performance-completeness/ui-final/{greatCircleScene,tangentScene}.png` hiển thị đề/tiêu đề của bài khác; các khẳng định hình học trong đó vẫn đúng.

### B3 (P0, phát hiện thêm) — Đề bài thật bị thay bằng lời lưu ý / chữ ô soạn cũ
- **Triệu chứng (route sản phẩm):** `SimulationWorkspace` ưu tiên `envelope.description` trước văn bản học sinh đã gửi. Envelope Hybrid `/4` (`backend/app/ai/adapter4_route.py`, có cả trên `main`) ghi `description` = "Quan sát mô hình dựng từ dữ kiện; …" ⇒ ô **Đề bài** hiện lời lưu ý thay vì đề. Khi bản ghi không có `description`, chuỗi dự phòng lại lấy `problemText` của ô soạn — có thể là đề của bài khác.
- **Cách sửa (frontend, không đụng backend):** đề = `originalInput` của chính bản ghi lịch sử đang mở → `description` → tiêu đề; bỏ `problemText`.
- **Khoá:** `problem-statement-source.test.tsx` (2 ca; đỏ với thứ tự cũ).
- **Phạm vi backend (chỉ báo cáo):** nếu muốn bản ghi không có `originalInput` (vd. mở lại từ máy chủ) vẫn có đề, adapter cần trả đề gốc trong một trường riêng thay vì dùng `description` làm lời lưu ý.

### B4 (P1, phát hiện thêm) — Tiếp diện (d = R) được giải thích như có đường tròn giao tuyến
- **Triệu chứng:** bước "Xác định hình chiếu vuông góc H của tâm K và đoạn KH — … điểm H là **tâm của đường tròn giao tuyến**" — sai toán (d = R không có đường tròn), lặp lại nội dung bước trước.
- **Nguyên nhân gốc:** lời dẫn bước phụ mặt cầu–mặt phẳng (`scene3d-semantic-policy.ts`) dùng chung câu của trường hợp cắt.
- **Cách sửa:** đối tượng phụ tiếp diện mang nhóm `sphere_plane_tangent`; bước bán kính đọc "Nối bán kính KH tới tiếp điểm H … H là điểm chung duy nhất (tiếp điểm)". Cấu trúc hai bước chân vuông góc → bán kính (khoá §6 của run trước) giữ nguyên.
- **Khoá:** `scene3d-sphere-tangent-narration.test.ts` (đỏ trước sửa).

### B5 — Nút "Xem kết quả" giãn hết chiều ngang dock
Trông như ô nhập. `align-self: flex-start` trong `.dock-goal-reveal`; tái dùng kiểu `.step-evidence-toggle` sẵn có.

## C. Kiểm thử toán học và hình học

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Mặt cầu tâm I qua A (IA = 3): bước 1 dùng chính IA, không thêm X | PASS | `sphere-audit/probe.json` (`I, A, cau__radius, cau`) |
| Mặt cầu bán kính 5 (không có điểm cho trước): X là điểm tham chiếu có giải thích, rút khỏi cảnh từ bước 3 | PASS | `sphere-audit/probe.json` |
| d = 0, 0 < d < R, d = R, d > R; mặt phẳng nghiêng n = (1,2,2), R = 5, d = 3: IH = 3, IM = 5, HM = 4, IH ⊥ mặt phẳng, H ∈ mặt phẳng — số học chính xác trên ℚ³ | PASS | `axo-sphere-and-cross-family-pedagogical-gate.test.tsx` (test có sẵn, chạy trong bộ 124 file) |
| Mặt phẳng pháp tuyến bất lợi n = (3,−8,0), bất biến đa họ hình | PASS | cùng file trên |
| Đường tròn tham chiếu mờ hơn thiết diện, không vẽ chồng, nét thấy/khuất đổi theo góc | PASS (kiểm mắt 3 góc) | `sphere-audit/cau-cat-mat-phang-a{0,1,2}.png`, `cau-the-tich-a0.png` |
| Tiếp diện không có đường tròn giao tuyến, lời dẫn đúng | PASS sau B4 | `scene3d-sphere-tangent-narration.test.ts`, `ui-final/tangentScene.png` |
| d > R: chẩn đoán mâu thuẫn, không có nút/đáp án | PASS | `ui-final/receipt.json` (synthetic) |
| Đề bài ↔ cảnh ↔ đối tượng render ↔ kết luận, 11/11 bài mẫu, bước đầu và bước cuối | PASS | `browser-final/receipt.json` (route thật `/simulation/<id>`) |
| Họ hình khác (chóp, lập phương lục giác, lăng trụ đứng/xiên, trụ nghiêng/xiên, nón, khoảng cách) | Không sửa mã. Kiểm mắt sau khi quay: lập phương (thiết diện lục giác khép kín, nét khuất hợp lý), lăng trụ xiên (đường cao A′H tách khỏi cạnh bên AA′), nón (thiết diện qua trục khép kín); các họ còn lại chỉ qua bộ test hình học có sẵn | `perf-after/{cube-hexagon-angle-1,oblique-prism-angle-2,non-thiet-dien-truc-angle-1}.png` |

Fixture tổng hợp (`greatCircleScene`, `tangentScene`, `nonIntersectingScene`, `cube-hexagon`, `oblique-prism`, `dense-multi-solid`) **không** phải bằng chứng cho route sản phẩm.

## D. Hiệu năng

Môi trường: bản build production, Chrome 157.0.8103.38 có giao diện, 1440×900, DPR 1, Intel UHD Graphics (ANGLE D3D11), 0 lời gọi mạng ra ngoài. Baseline = build của `34c779e1` (worktree sạch `axo-performance-verifier`), candidate = build của `69b9497f`. Cùng script, chạy tuần tự, không chạy gì song song. (`514d34d4` chỉ đổi lời dẫn tiếp diện, không có cảnh tiếp diện trong bộ đo.)

| Cảnh | Frame median ms | Frame P95 ms | FPS median | Render/frame med/max | Đổi bước median/P95 ms | GPU buffer tạo/xoá khi đổi bước |
|---|---|---|---|---|---|---|
| thiet-dien-chop | 6.9 → 6.9 | 7.1 → 7.1 | 144.9 → 144.9 | 1/1 → 1/1 | 73.6/88.8 → 68.1/82.6 | 5712/5712 → 5712/5712 |
| cau-cat-mat-phang | 7.0 → 7.0 | 14.0 → 13.9 | 142.9 → 142.9 | 1/1 → 1/1 | 72.5/102.2 → 60.0/96.2 | 2412/2412 → 2412/2412 |
| non-thiet-dien-truc | 6.9 → 6.9 | 7.1 → 7.0 | 144.9 → 144.9 | 1/1 → 1/1 | 73.5/142.6 → 40.6/72.0 | 1740/1740 → 1740/1740 |
| tru-thiet-dien-tron | 7.0 → 7.0 | 13.9 → 13.8 | 142.9 → 142.9 | 1/1 → 1/1 | 58.8/79.6 → 53.7/77.2 | 2364/2364 → 2364/2364 |
| cube-hexagon | 6.9 → 6.9 | 7.1 → 7.1 | 144.9 → 144.9 | 1/1 → 1/1 | 82.0/133.7 → 78.6/108.6 | 9984/9984 → 9984/9984 |
| oblique-prism | 6.9 → 7.0 | 7.1 → 13.8 | 144.9 → 142.9 | 1/1 → 1/1 | 52.1/85.7 → 44.8/61.8 | 5064/5064 → 5064/5064 |
| dense-multi-solid | 6.9 → 6.9 | 7.1 → 7.0 | 144.9 → 144.9 | 1/1 → 1/1 | 65.5/97.1 → 58.8/121.3 | 5376/5376 → 5376/5376 |
| **Gộp 7 cảnh** | **7.0 → 6.9** (n 14204 → 14606) | **13.8 → 7.1** | — | **1/1 → 1/1** | **68.2/111.3 → 58.1/95.7** (n = 168) | cân bằng |

- 8 biến thể quay/zoom/chọn/ẩn/cô lập/thu dock/sau bước/quay lại, gộp: 7.0/13.9 → 6.9/13.8 ms. 1 WebGL context mọi cảnh.
- Mở/đóng "Xem kết quả" tới khung hình kế: 12.5/12.8 ms (median/P95), n = 20; không tạo GPU buffer, camera không đổi.
- Đổi bài 22 lần (sau GC): 1 context; heap 17.33 → 19.97 MiB (run trước 15.40 → 18.67).
- **Đánh giá:** không có hồi quy. Cảnh không hề có bảng kết luận cũng dao động mạnh giữa hai lượt (vd. `non-thiet-dien-truc` P95 142.6 → 72.0; `dense-multi-solid` P95 97.1 → 121.3; `oblique-prism` frame P95 7.1 → 13.8), nên **không** quy phần giảm độ trễ đổi bước cho thay đổi này — chỉ kết luận được là bảng kết luận không còn mount khi đổi bước. Heap tăng chậm ~0.12 MiB/lần đổi bài trong 22 lần: chưa đủ để kết luận có hay không có rò rỉ.
- Số liệu thuộc một máy, một trình duyệt; không phải trải nghiệm chung cho mọi thiết bị.
- NOT TESTED: GPU timer query, React profiler build, trình duyệt khác Chrome, thiết bị di động thật.

## E. Giao diện

- Trước/sau mở kết quả: `browser-final/desktop-final-{before,after}-reveal.png`, `mobile-390-before-reveal.png`, `responsive-{390,1440}-after-reveal.png`, `zoom-110-after-reveal.png`.
- 7 độ rộng (360, 390, 430, 768, 1024, 1280, 1440) với kết quả đang mở: không tràn ngang trang, bảng kết luận nằm trong viewport và ≤ 45% chiều cao, canvas 3D đủ cao (`browser-final`).
- Harness cũ (thẻ đối tượng, nhãn, cuộn, tooltip, 6 độ rộng × 5 bài, zoom 110% tương đương bằng DPR 1.1): 39/40 PASS (`ui-final`). Ca lỗi `responsive 360 cau-cat-mat-phang` (chờ chip `cau__ref_pt`) lặp lại ở cả hai lượt chạy đủ, nhưng PASS 5/5 khi chạy riêng (`ui-360-recheck`) và 6/6 khi chạy cùng ca trước nó (`ui-360-sequence`); run trước gặp đúng ca này. **Suy luận, chưa xác minh:** trước ca này harness chọn/ẩn X trên cùng bài, ảnh khôi phục của bài khiến danh sách chip của bước cũ hiện thoáng qua trước khi nhảy tới bước cuối. Trạng thái cuối luôn đúng (X không có ở bước 5).
- Ảnh góc khó mặt cầu/thiết diện: `sphere-audit/`.
- Zoom trình duyệt thật bằng phím tắt: NOT TESTED (dùng CDP DPR 1.1 tương đương).

## F. Rủi ro và nghiệm thu

| Cổng | Trạng thái |
|---|---|
| Không tự hiện đáp án (Next, Play, thu gọn/mở lại, lùi/tiến, phát lại, đổi bài, A→B→A, đổi nhanh, đổi khi đang Play, Back/Forward) | **PASS** — trình duyệt thật, `browser-final` 24/24 |
| Bài chỉ dựng hình không có nút | **PASS** |
| Đề bài ↔ cảnh nhất quán, tiêu đề tiếng Việt | **PASS** (11/11 route sản phẩm); fixture tổng hợp đã sửa |
| Hình cầu: trình tự dựng, tham chiếu/thiết diện, 4 chế độ d | **PASS** |
| Hiệu năng giữ nguyên | **PASS** (đo cặp cùng môi trường) |
| Responsive + zoom 110% tương đương | **PASS** (1 ca harness chập chờn, ghi ở E) |
| Vitest 124 file / 1803 test · `tsc -b && vite build` · docs gate 42 · `freeze_evaluation_candidate --verify` | **PASS** |

**Chưa xử lý / chỉ suy luận:**
- Nguyên nhân ca chập chờn 360 px (E) — chưa xác minh.
- `recoverCatalogScene3D` vẫn khớp bản ghi cũ thiếu `scene3d` với bài mẫu theo **tiêu đề**; một đề tự gõ trùng tiêu đề bài mẫu có thể nhận cảnh của bài mẫu. Chỉ ảnh hưởng bản ghi lịch sử cũ; chưa tái hiện, chưa sửa.
- Định danh bản ghi theo `simulation_id + config` (gốc của B2) vẫn vậy; với envelope backend thật, config khác nhau theo đề nên chưa thấy va chạm.
- Lời lưu ý chung của envelope Hybrid không còn hiện ở ô Đề bài (B3); nếu cần giữ, nên có chỗ hiển thị riêng.
- Họ hình khác: không có lỗi mới được tái hiện; không sửa.

**Đề xuất:** đủ điều kiện để chủ sở hữu duyệt. Merge vào `main` cần hoà giải với cutover Hybrid `/4` (nhánh đã phân kỳ) và một lượt T3 đầy đủ trên kết quả hoà giải — nên làm như một việc riêng.
