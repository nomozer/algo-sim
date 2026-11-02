# ALGOSIM PEDAGOGICAL SIMULATION INTEGRATION REPORT

**Master Epic:** `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · **Run:** `pedagogical-simulation-integration` ·
**Ngày:** 2026-11-03 · **Lượt gọi Gemini live:** `0` (`USD 0.00`)

Báo cáo này chỉ ghi điều đã đo. Bằng chứng nằm trong thư mục run này; mọi biên nhận của candidate trước giữ nguyên byte.

---

## 1. Baseline và định danh Git

| | Trước (checkpoint bàn giao, đã xác minh) | Sau |
|---|---|---|
| Nhánh | `research/hybrid-master-backend-replacement` | như cũ (không merge, không push) |
| HEAD | `5abf8c20` | `ea9a6064` + commit ghi ngược/báo cáo |
| Candidate commit | `123e57da` | `fba8b7a7` |
| Product commit | `d17116cb` | `adf4a113` |
| `measured_system` | `730045ff…` (118 file) | `39e9f54baf8c2a7ec2368a3c7a383d023a353ab0e9ab79a6b7c6fa25b6c66ed7` (118 file) |
| Registry / Planner / TypedFactNext / Adapter | `/31` · `/26` · `/2` · `/4` | **không đổi** |
| Engine | `geometry-function-engine/22` | `geometry-function-engine/23` (chỉ cảnh — §5.3) |
| `CACHE_VERSION` | `131` | `131` (không bump — §5.3) |
| `DEFAULT_MODE` / `HYBRID_ROUTE_MODE` mặc định | `LLM_ONLY` / `off` | **không đổi** |

Checkpoint được xác minh bằng `git log`, `grep CACHE_VERSION backend/app/main.py` và `freeze_evaluation_candidate.py
--verify` trước khi sửa dòng nào.

Commit của run (không commit nào có trailer `Co-Authored-By`):

- Vòng đầu: `3223fdf4` (frontend trình bày) · `6679b8fc` (engine /23) · `dfcf0ea8` (xuất lại fixture preview) ·
  `d938689b` (E2E + ghi ngược) · `444b8c95` (đóng băng) · `e8fc37fb` (biên nhận E2E) · `627b7dee` (kiểm toán trước sửa,
  T3, nháp báo cáo).
- Sau review vòng 1: `928fb880` (F1, F6) · `adf4a113` (F7) · `6910ef64` (F2–F4) · `fba8b7a7` (đóng băng lại) ·
  `c62b3aa1` (bộ dò, sau đối chứng dương) · `dbc0316c` (biên nhận E2E) · `ea9a6064` (biên nhận T3).

## 2. Hành vi UI thực tế trước khi sửa

Đo bằng trình duyệt thật (Playwright Chromium headless) trên `frontend/dist` build từ `5abf8c20`, backend `uvicorn` thật
ở `HYBRID_ROUTE_MODE=staging-replay` (`REPLAY_STAGING_SIMULATED`), **30/30 ca SERVED** của corpus 16 lớp, chạy liền nhau
không tải lại trang. Ở mỗi ca, probe ghi toàn bộ chữ người học nhận được (chữ hiển thị, vùng `aria-live`,
`title`/`aria-label`): lúc tải → sau từng «Bước sau» → bảng «Các bước dựng» → «Hiện tất cả số đo» → ô soi từng đại
lượng → ô soi từng thành phần → bảng «Đề bài» → cuối cùng mới mở «Phân tích toán học». Bằng chứng:
`prefix-ui-audit.json` (tóm tắt từng ca), `prefix-ui-audit-probe.mjs` (probe), `prefix-ui-audit-analyze.mjs` (bước
phân tích). Bản dump DOM thô **không commit** (sha256 ghi trong `prefix-ui-audit.json`), nên tóm tắt không dựng lại
được chỉ từ kho; muốn dựng lại phải chạy lại probe tại `5abf8c20` rồi chạy bước phân tích. 0 lỗi trang/console.

Trả lời mười câu hỏi của §III:

| # | Câu hỏi | Đo được trước khi sửa |
|---|---|---|
| 1 | Nhập đề thì hiện gì? | Xưởng 3D ở **Bước 1/N** (dữ kiện đề), thanh hướng dẫn «Đang dựng (bước 1/N)… Bấm Phát hoặc Bước sau», các nút «Đề bài», «Phân tích toán học», menu «Khám phá/Hiển thị/Thêm». |
| 2 | Tự xuất đáp số? | **Không** — 0 lần nêu đáp số (`=`/`bằng`/`là` + giá trị) ở mọi giai đoạn của 30 ca. |
| 3 | Tự trình bày lời giải? | **Không** — không có thẻ lời giải (đã gỡ từ W05); danh sách bước nêu hành động dựng, không nêu giá trị. |
| 4 | Tự chạy các bước dựng? | **Không** — 0/30 tự phát; 30/30 mở ở bước 1. |
| 5 | Hiện điểm/đường/mặt học sinh phải tự xác định? | Chỉ khi học sinh tự tiến bước hoặc mở «Các bước dựng» (§18, L1). Không tự hiện. |
| 6 | Quantity panel hiện gì? | Dữ kiện + đại lượng trung gian; đại lượng kết quả bị lọc (`tapKetQuaCuoi`); chỉ mở khi học sinh chọn «Khám phá → Đại lượng». |
| 7 | Step playback tự chạy, lộ chuỗi giải? | Không tự chạy. |
| 8 | Inspector công bố kết luận? | Ô soi của đại lượng kết quả chỉ ghi vai trò và «Đo trên …», **không** giá trị, **không** công thức. |
| 9 | Kết quả backend lên UI ngoài ý muốn? | Không ở chế độ học sinh. Envelope vẫn mang đáp số và lời kể «Thể tích … bằng √3.» (cần cho Chế độ B) nhưng không được render (§18, L4). |
| 10 | Trạng thái cũ còn khi chuyển bài? | Không — 30 ca liền nhau đều về bước 1, không giữ lựa chọn/bảng của bài trước. |

**Lỗi tìm thấy:**

- **P-1 (xác nhận, 30/30 ca):** nút «Đề bài» hiện câu miễn trừ *«Quan sát mô hình dựng từ dữ kiện; các kiểm tra trên
  hình không phải chứng minh tổng quát.»* thay cho đề. Mọi giả thiết — kể cả «SA vuông góc với mặt phẳng (ABCD)» —
  biến mất khỏi giao diện. Nguyên nhân gốc: `SimulationWorkspace` đọc `envelope.description`, còn adapter `/4` cố ý
  đặt câu miễn trừ vào trường ấy (`adapter4_route.py:263`; không đặt đề được vì `_noi_chung_minh` quét trường này).
- **P-2 (xác nhận ở dữ liệu, 2 đề corpus + 1 fixture preview):** giả thiết ⊥ không thành vật trên cảnh khi chính nó
  đặt điểm ngoài đáy: «hình chiếu vuông góc của A′ lên (ABC) là H» (`S2-B-A03_control_with_dimensions`) và «Hình
  chiếu vuông góc của S lên (ABC) là trung điểm H của AB» (`served-H12_PROJECTION_MIDPOINT_ANGLE`). Toán đúng (√3,
  a³/8, cos² = 1/2), nhưng không có A′H/SH, không dấu góc vuông — giả thiết vuông góc (và độ dài SH đề cho) vô hình.
  Phát hiện nhờ phép đếm witness ⊥ trong E2E (0 ở `S2-B-A03`).
- **P-3 (tiềm ẩn):** kết quả kiểm MỤC TIÊU của đề (`planner.goal_checks`, vd «chứng minh BC ⊥ (SAB)») hiện thành chip
  trên sân khấu Chế độ A ở bước cuối — *«Quan hệ vuông góc… (điều đề yêu cầu): trên hình đã dựng, điều này đúng…»*,
  tức kết luận học sinh phải tự đi tới. Xác nhận bằng fixture `served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED` và ảnh
  chụp trình duyệt cũ (`hybrid-offline-readiness-finalization/p3-offline-e2e/browser/…__step4.png`). **Không tái hiện
  được trên đường sản phẩm hiện tại**: TypedFactNext `/2` không có mục tiêu chứng minh quan hệ (0/30 ca có quan sát).

## 3. Hành vi đã đúng và được giữ nguyên

Không sửa: `tapKetQuaCuoi` (lọc kết quả cuối ở Chế độ A, gồm tỉ số thể tích, thể tích phần còn lại, `cos²`), bảng
«Đại lượng», nhãn số đo (`hiddenIds`), ô soi, trình phát bước (không tự phát, mở ở bước 1), Chế độ B «Phân tích toán
học» (người học tự mở — hợp đồng `DESIGN_BRIEF.md §79–80`, `ARCHITECTURE_MAP.md:281`), luật «Hình phụ», cổng nhân chứng
vuông góc, từ chối/hỏi lại, phục hồi sau lỗi hạ tầng. Bằng chứng: §2 (trước sửa) và §13 (sau sửa) cho cùng kết quả ở
những phần này. Không thêm chế độ giáo viên hay nút «xem lời giải» mới.

## 4. Vấn đề sư phạm được xác nhận

| ID | Phân loại nội dung | Mức | Trạng thái |
|---|---|---|---|
| P-1 | `SOURCE_GIVEN` bị thay bằng câu miễn trừ (cả đường giao bài cho lớp — review F1) | MAJOR (mất giả thiết, kể cả ⊥) | sửa §5.1 |
| P-2 | `SOURCE_GIVEN` (quan hệ ⊥, độ dài SH) không được biểu diễn | MAJOR với ca bị ảnh hưởng | sửa §5.3 |
| P-3 | `SOLUTION_REVEAL` (kết luận mục tiêu) trên sân khấu Chế độ A | tiềm ẩn | sửa §5.2 |

## 5. Thay đổi đã triển khai

1. **«Đề bài» = đề nguyên văn** (`3223fdf4`, hoàn chỉnh ở `928fb880`): `store.loadEnvelope(env, sampleId, originalInput)`
   đóng dấu đề người học đã gửi (gõ tay, hoặc văn bản đã duyệt từ ảnh) vào **chính envelope**, trường hiển thị
   `problem_statement`. Vì nằm trong envelope, đề đi theo **bài giao cho lớp** (máy chủ lưu nguyên dict envelope —
   `classroom_router._validated_envelope`). `SimulationWorkspace` đọc `problem_statement || description || title`. Bản
   đầu chỉ giữ đề ở `active` (không theo bài giao) — reviewer bắt ở vòng 1 (F1, MAJOR), đã sửa và có test. **Lịch sử**
   giữ đề chỉ qua `item.originalInput` (đề gõ tay hoặc đã duyệt từ ảnh): `history.ts::sanitizeEnvelope` không lưu
   `problem_statement` — và cũng không lưu `scene3d` (lỗi có sẵn, review vòng 2 R2/R3,
   `ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D`). Bài mẫu Thư viện không có đề đã gửi, lùi về `description` như trước.
2. **Kết luận mục tiêu chỉ ở Chế độ B** (`3223fdf4`): chip `[data-route-d-observation]` rời cụm nút nổi trên sân khấu,
   vào bảng «Phân tích toán học», mục «Kiểm tra trên hình đã dựng» — vẫn theo luật neo F4 (`hybridTaiBuoc`), vẫn nói
   «quan sát trên một hình, không phải chứng minh tổng quát». Nút Chế độ B có mặt cả khi cảnh chỉ có quan sát.
3. **Vẽ đường ⊥ của giả thiết** (`6679b8fc`, engine `/23`): trong `bien_dich`, đọc thẩm quyền chuẩn hoá duy nhất
   `_rang_buoc_vuong()` (gom `perpendicular_line_plane` · `altitude` · `orthogonal_projection`); một đường ⊥ đáy mà
   **chính ràng buộc ấy đã đặt** điểm ngoài đáy (bước `place_point` mang đúng luật của nó) và không trùng cạnh khối
   ⇒ một `construct_segment` sẵn có của IR. Tên do `display_names.py` («Đoạn thẳng nối A′ và H», ký hiệu `A′H`), nhân
   chứng góc vuông chính xác do `certificates.attach_scene_perpendicular_certificates`. Bỏ qua: chiếu xuôi (điểm H đã
   mang witness), cạnh khối có sẵn (SA ⊥ đáy giữ witness trên `canh_ben_S_A`), cặp suy biến. Mục tiêu chứng minh không
   nằm trong `self.calls`, nên một mục tiêu không bao giờ bị vẽ thành giả thiết (reviewer xác nhận). `ENGINE_VERSION`
   /22 → /23 vì khoá cache Route D chứa phiên bản Engine; delta định danh khai ở `IDENTITY_DELTAS`. `CACHE_VERSION` giữ
   `131`: prompt và chính sách định tuyến không đổi.
4. **E2E trình duyệt khoá hợp đồng** (`d938689b`, `6910ef64`, `c62b3aa1`): `verify-hybrid-product-e2e.mjs`
   (`verifyStudentModeDisclosure`, flow 7, đối chứng dương, `--out-dir`, từ chối ghi đè biên nhận).

## 6. Thành phần bị ảnh hưởng

- Frontend: `frontend/src/simulations/types.ts` (`SimulationEnvelope.problem_statement`), `frontend/src/state/store.ts`,
  `frontend/src/components/SimulationWorkspace.tsx`, `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx`,
  `frontend/scripts/verify-hybrid-product-e2e.mjs`.
- Backend: `backend/app/simulation/geometry_functions/engine.py` (`bien_dich`, `ENGINE_VERSION`),
  `backend/scripts/export_hybrid_preview_fixtures.py` (một delta định danh).
- Test: `hybrid-product-integration.test.tsx`, `hybrid-preview-contract.test.tsx`, `test_hybrid_product_integration.py`
  (A′H/SA, SH ⊥ đáy và đường cao tới trung điểm, cổng giao bài), `test_hybrid_wave1_exact_certificates.py` (17 → 18
  witness, có lý do), 4 test ghim phiên bản Engine, `test_hybrid_preview_fixtures.py` (trỏ bộ fixture mới).
- Tài liệu: `HYBRID_PREVIEW_FRONTEND_CONTRACT.md §3.4`, `ARCHITECTURE_MAP.md:281`, `CODE_INDEX.md`, `CURRENT_STATE.md`,
  `EVIDENCE_INDEX.md` (C23; C22 `CORRECTED_BY`), `STATUS_LEDGER.md`, `HYBRID_MASTER_EPIC_CURRENT_STATE.md`.
- Không chạm: Planner, Registry, Kernel/`geometry/`, Source Gate, adapter `/4`, lược đồ IR, prompt, `client.ts`, backend
  lớp học.

## 7. Chính sách dữ kiện gốc so với kết quả suy ra

| Lớp | Ví dụ | Chế độ A (mặc định) | Chế độ B (người học tự mở) |
|---|---|---|---|
| `SOURCE_GIVEN` | đề nguyên văn; «SA ⊥ (ABCD)»; AB = 2 | luôn có: «Đề bài» nguyên văn; quan hệ ⊥ thành vật + dấu góc vuông | như A |
| `SCENE_REPRESENTATION` | đỉnh, cạnh, mặt, đáy, A′H của giả thiết | hiện theo bước dựng | như A |
| `USER_REQUESTED_EXPLORATION` | tiến bước, «Các bước dựng», «Đại lượng», «Hiện tất cả số đo», ô soi | chỉ khi học sinh thao tác | như A |
| `DERIVED_GEOMETRY` | giao điểm, chân đường vuông góc phụ, thiết diện | xuất hiện ở bước dựng của nó khi học sinh tiến tới | như A |
| `SOLUTION_REVEAL` | giá trị đại lượng mục tiêu; công thức của nó; kết luận kiểm mục tiêu | **không** ở bất kỳ bước/bảng/ô soi nào | «Phân tích toán học» |

Che bằng cách **không render**, không bằng CSS: kết quả cuối không vào DOM ở Chế độ A (kiểm trên `textContent` và
thuộc tính ARIA, không chỉ chữ hiển thị). Backend giữ nguyên dữ liệu chính xác.

## 8. Mathematical correctness

- Đáp số không đổi: E2E kiểm từng đáp số của **30/30 ca SERVED** xuất hiện đúng trong Chế độ B (vd `8/3`, `72`, `9π`,
  `81π/16`, `√3`, `1`, `3√2/2`, `2304/625`, `cos²=2/3` → `2/3`); test backend ghim `√3` (`S2-B-A03`), `8/3`
  (`S2-B-I07`), `4` (SH ⊥ đáy và đường cao tới trung điểm); H12 vẫn `a³/8`, `cos²=1/2`.
- `test_staging_replay_serves_and_refuses_all_16_scope_classes` (16/16 lớp, ≥ 40 ca, oracle độc lập) xanh.
- Witness ⊥ mới qua `verify_perpendicular_witness` (Gram chính xác) — 18/18 witness của 12 ca served-spec hợp lệ.
- `export_hybrid_preview_fixtures.py --verify` trên bộ cũ: mọi fixture chỉ khác bằng cặp định danh đã khai, trừ H12
  (thêm SH có witness). Thứ tự sư phạm O1–O4 của H12 và hai ca SH tới trung điểm đều sạch.

## 9. Scene3D interaction correctness

E2E (37 lần kiểm chế độ học sinh trên 30 ca khác nhau): kéo xoay + lăn chuột thu phóng trên canvas, duyệt mọi bước dựng,
mở «Các bước dựng», bật/tắt «Hiện tất cả số đo», mở ô soi của **mọi** đại lượng và **mọi** thành phần trong cây,
«Đề bài», «Phân tích toán học». **0 lượt `/api/analyze`** phát sinh trong lúc xoay/thu phóng/tua/soi; 0 lỗi trang, 0 lỗi
console. Không đổi camera, cây, ô soi, tách khối.

## 10. Answer-disclosure tests

- Luật phát hiện (`statesAnswer` + `mentionsAnswer`): `(=|bằng|là) <giá trị>`; với giá trị đặc trưng (có √, π hoặc
  phân số) thì cả giá trị đứng trần, trừ khi đề đã nêu nó và bỏ bộ đếm «Bước n/N». Không cấm mọi chuỗi số, nên dữ kiện
  đề và số đếm không bị che nhầm.
- Giá trị dò: oracle (chuẩn hoá vế trái như `cos²=`), **chuỗi Chế độ B thật sự render** cho từng ca, và giá trị ở tỉ lệ
  hình dựng (`answer_exact.coef`, vd `√3/4` của `a²√3/4`).
- **Đối chứng dương** (cửa sổ chứng): cùng bộ dò phải bắt được đáp số trong bảng Chế độ B — **43/44** giá trị đáp số
  (tổng `detector_positive_control` của 37 lần kiểm). Giá trị còn lại (`4`, `cr.cube_section_plus_inscribed_sphere`) là
  số nguyên nhỏ hiện không kèm `=`, ghi ở `detector_blind_values`, không bị giấu. Đối chứng dương còn tìm ra một điểm mù
  thật của bộ dò đầu (`9π` hiện không có `=` khi đại lượng không có ký hiệu), đã đóng ở `c62b3aa1`. Giá trị tỉ lệ hình
  dựng (`√3/4`) được dò ở chế độ học sinh nhưng **không có** đối chứng dương: Chế độ B chỉ hiện dạng ký hiệu, nên đối
  chứng ấy không dựng được (review vòng 2, R5).
- Trước sửa: 0 lần ở 30 ca, với luật `(=|bằng|là) giá trị` — **yếu hơn** bộ dò cuối (chưa dò giá trị đứng trần). Sau
  sửa: 0 lần ở 37 lần kiểm, với bộ dò cuối.
- Vitest: `hybrid-preview-contract.test.tsx` khoá vị trí của quan sát (nền đỏ trên mã cũ), cùng các test SIMULATION-FIRST
  sẵn có.

## 11. Construction trace behavior

Không tự phát; mở ở bước 1; bước chỉ tiến khi học sinh bấm. Danh sách bước nêu hành động dựng («Dựng H là trung điểm
của đoạn BC», «Dựng đoạn thẳng nối A′ và H»), không nêu giá trị — sự kiện `FINAL_RESULT` chỉ đóng một bước, không mở
bước (test sẵn có). `construction_trace` kỹ thuật không hiển thị; lời kể có lọc định danh máy (`learnerTextIsSafe`).

## 12. Refusal và clarification

Flow 5: đề mơ hồ `S2-C-A01_goc_chieu` → câu hỏi lại `[data-clarification-question]` đúng nguyên văn backend, 0 canvas;
đề mâu thuẫn `S2-D-D03_contradictory_length` → thẻ từ chối, câu hỏi lại cũ bị xoá, 0 canvas. Flow 6: lỗi hạ tầng HTTP
503 `LIVE_AI_DISABLED` → băng lỗi, không bị gán nhầm là từ chối toán học, 0 canvas, không lộ khoá/traceback; nhập lại đề
→ phục vụ bình thường **và** qua lại toàn bộ phép kiểm chế độ học sinh.

## 13. Browser E2E evidence

Biên nhận có thẩm quyền: `e2e-review-round-1/pedagogical-e2e-browser-receipt.json`
(`REAL_BROWSER_AND_UVICORN_NETWORK_E2E_STAGING_REPLAY`, `live_provider_calls 0`, `dist` build từ `fba8b7a7`):
**7/7 flow**, 0 page error, 0 console error (miễn đúng lỗi tải tài nguyên 503 `/api/analyze` mà flow 6 cố ý gây ra).
Flow 1–4, 6 có phép kiểm chế độ học sinh; flow 7 = **30/30 ca SERVED** liền nhau; witness ⊥ có ở `S2-B-I07` (SA) và
`S2-B-A03` (A′H). `e2e-review-round-1/flow1-student-mode-final-step.png`: bước 4/4, ô soi «Thể tích S.ABCD» không có
giá trị, dấu góc vuông tại A. Biên nhận trước review (`pedagogical-e2e-browser-receipt.json`, candidate `444b8c95`)
giữ nguyên.

Báo riêng theo §VIII:

| Trục | Kết quả đo |
|---|---|
| Mathematical correctness | 30/30 đáp số đúng trong Chế độ B; 16/16 lớp backend; witness Gram chính xác |
| Pedagogical disclosure correctness | 0 lần nêu đáp số / 37 lần kiểm (đối chứng dương 43/44); 0 quan sát trên sân khấu; «Đề bài» nguyên văn 37/37 (trước sửa 0/30) |
| User interaction correctness | mọi bước, mọi ô soi, xoay/thu phóng; 0 lượt pipeline thừa |
| Rendering correctness | canvas ≥ 200×150 ở mọi ca; witness ⊥ cho giả thiết ⊥ |
| Runtime reliability | 0 lỗi trang/console; phục hồi sau 503 |

## 14. Frontend and backend regression

- Frontend `npx vitest run`: **85/85 file, 1502/1502 test** (trước run: 1486). Test mới đều đỏ trên mã cũ — kiểm bằng
  cách đưa file sản phẩm về HEAD rồi chạy lại (15 đỏ ở vòng đầu; ca bài giao F1 đỏ ở vòng 1).
- Backend: full suite sau thay đổi Engine (cây bẩn) có 28 lỗi, phân loại hết — 10 do thay đổi Engine (sửa: bỏ đoạn khi
  chiếu xuôi/suy biến; 17 → 18 witness; delta định danh + xuất lại fixture), 18 do candidate/cây bẩn (đóng băng lại +
  gắn lại template). Một lần `test_I2_every_historical_candidate…` đỏ do `git log` trả rỗng nhất thời; gọi trực tiếp và
  chạy lại đều xanh. Kết quả có thẩm quyền là Full T3 (§16).

## 15. Independent review

Reviewer fresh-context, đối kháng, chỉ đọc.

- **Vòng 1 — `NOT_READY`** (0 BLOCKER, 1 MAJOR, 5 MINOR, 3 NIT):
  - F1 MAJOR: bài giao cho lớp mất đề → sửa ở `928fb880` (đề nằm trong envelope) + test store và cổng lớp học.
  - F2: bộ dò chưa có đối chứng dương và chưa dò giá trị render/tỉ lệ hình → `6910ef64`, `c62b3aa1`.
  - F3: số kiểm toán trước sửa không dựng lại được → commit bước phân tích.
  - F4: E2E ghi đè biên nhận → `--out-dir` + từ chối ghi đè.
  - F5: chưa ghi ngược tài liệu sống, blob template cũ → đã ghi ngược (§6).
  - F6: thiếu test `perpendicular_line_plane`/`altitude`; SH là hình phụ sau khi đóng khối → thêm test; thứ tự ghi ở L5.
  - F7–F9 (NIT): tên hàm trong comment, test kiểm chuỗi nguồn, dòng trạng thái báo cáo → sửa.
- **Vòng 2 — `READY`** (0 BLOCKER, 0 MAJOR, 4 MINOR, 2 NIT):
  - R1: số đối chứng dương ghi 47/48, biên nhận là 43/44 → đã sửa mọi nơi.
  - R2/R3: `history.ts::sanitizeEnvelope` không lưu `problem_statement` và `scene3d` — mở lại từ Lịch sử mất «Đề bài»
    của bài giao và mất cảnh 3D (lỗi có sẵn từ trước Scene3D) → câu chữ báo cáo đã sửa; ghi
    `ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D` (cần quyết định lưu trữ, ngoài run này).
  - R4–R6 (NIT): tham chiếu `independent-review.md` trước khi có file; giới hạn của bộ dò và của kiểm toán trước sửa;
    `problem_statement` là chữ tự do của giáo viên → đã ghi (§10, L10).
- Chi tiết hai vòng: `independent-review.md`.

## 16. Full T3

`full-t3-dbc0316c.json`: **`FULL_PRODUCT_GATE_PASS`** trên worktree detached sạch tại `dbc0316c` (candidate `fba8b7a7`) —
pytest **16,652 passed, 0 failed** (7 skipped, 2 deselected, 15 xfailed), vitest **1502/1502**, `tsc -b && vite build`
PASS, demo 5/5, bề mặt sập 0 lỗi 500; `--verify` trước và sau MATCH; cây sạch sau khi chạy; junction và worktree đã gỡ.
Lần T3 trước review (`full-t3-e8fc37fb.json`, PASS, 16,649 / 1,501) giữ nguyên.

## 17. Candidate identity

`docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` + lớp đính chính `candidate_divergence.json` (đính chính
`../hybrid-master-product-integration/candidate_divergence.json`): product `adf4a113`, `39e9f54b…`, 118 file, đóng băng
trên worktree detached sạch tại `6910ef64` (`cay_lam_viec_sach = true`), `--verify` MATCH. Candidate `123e57da` và
biên nhận C18/C19/C21 + product-integration giữ nguyên, không chấm lại. Ba template pilot vẫn `PENDING_OWNER_DECISION`,
`paid_project_confirmed: false`, chỉ `measured_system` được gắn lại; blob mới `k1` `011136001a6d…`, `s2`
`39a4a5645241…`, `r1` `065892131daf…` — lệnh phê duyệt của Owner phải khoá theo các blob này.

## 18. Giới hạn chưa giải quyết

- **L1 — Kế hoạch dựng mở bằng một cú bấm.** Bảng «Các bước dựng» liệt kê mọi bước kể cả bước chưa tới; với bài khoảng
  cách, bước như «Dựng H1: hình chiếu của C lên (SAB)» chính là phương pháp giải. Chỉ hiện khi học sinh chủ động mở bảng
  hoặc tiến bước (`USER_REQUESTED_EXPLORATION`), nên giữ nguyên; có giới hạn danh sách tới bước hiện tại hay không là
  **quyết định sản phẩm của Owner**, chưa làm.
- **L2 — Đại lượng trung gian** (vd diện tích đáy) hiện khi học sinh mở «Đại lượng» hoặc «Hiện tất cả số đo» — đúng hợp
  đồng hiện hành, nhưng là một phần đường giải theo yêu cầu.
- **L3 — P-3 chỉ kiểm bằng vitest** (cấu trúc nguồn + SSR + fixture H07); đường sản phẩm `/4` hiện không tạo được
  `goal_checks`, nên chưa có bằng chứng trình duyệt.
- **L4 — Dữ liệu envelope** vẫn mang đáp số và lời kể có giá trị (cần cho Chế độ B); xem được qua công cụ nhà phát triển.
  Đây không phải hiển thị cho học sinh.
- **L5 — Đoạn giả thiết A′H/SH** mang vai `CONSTRUCT_AUXILIARY_GEOMETRY`, hiện ở bước sau khi khối đã đóng (không theo
  đáy → đường cao → cạnh bên), nhãn chung «Đoạn thẳng nối S và H», witness của luật `orthogonal_projection` xếp
  `ENGINE_VERIFIED` thay vì `GIVEN`. Hiển thị đúng; thứ tự và nhãn xuất xứ có thể chặt hơn.
- **L6 — Dấu góc vuông vẽ trên canvas**: kiểm bằng dữ liệu witness + cổng tự nhất quán + một ảnh chụp, không so pixel.
- **L7 — Phép phát hiện là theo mẫu**: cách nói khác (chữ viết bằng lời, độ thay cho cos², LaTeX) không được bắt; số
  nguyên nhỏ hiện không kèm `=` là điểm mù đã ghi (1/44 trong đối chứng dương).
- **L8 — Chỉ replay**: mọi số ở đây là `staging-replay`, không phải độ chính xác đọc đề của Gemini.
- **L9 — Tải tệp trực tiếp** (không qua bước duyệt ảnh), bài mẫu offline và bài giao trước `928fb880` không có đề đã
  gửi ⇒ «Đề bài» lùi về `description`/`title` như trước run.
- **L10 — Mở lại từ Lịch sử** làm rơi `scene3d` và `problem_statement` (`ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D`, có từ
  trước run, chưa có test tái hiện). `problem_statement` là chữ tự do do trình duyệt giáo viên gửi (React escape; cùng
  mức tin cậy với `title`/`description`/`instruction`), không có trần độ dài riêng ngoài `MAX_ENVELOPE_BYTES`, và có
  thể lệch với hình đã dựng nếu bị sửa tay.

## 19. Live Gemini status

`LIVE_PROVIDER_NOT_MEASURED` — 0 request live trong run này. `HYBRID_LIVE_VALIDATED` **không** được tuyên bố.

## 20. Production release blockers

`PRODUCTION_CUTOVER_READY` **không** được tuyên bố. Chặn: (1) `PAID_PROJECT_NOT_VERIFIED`; (2) pilot live K-1/S-2/R-1 và
đánh giá held-out độc lập H-1 `NOT_MEASURED`; (3) cổng cutover `docs/MIGRATION_CHECKLIST.md` (D-04, D-11, D-13,
GATE-16) và quyết định merge/push của Owner; (4) L1 cần quyết định sản phẩm. `GENUINE_DISCOVERY_NOT_ESTABLISHED` giữ
nguyên; không thêm Geometry Function, không sửa Planner.

## 21. Git and publication status

Nhánh `research/hybrid-master-backend-replacement`; không merge vào `main`, không push, không viết lại lịch sử.
Publication safety `check_publication_safety.py --range f986e897..HEAD`: `CHỜ` (chạy lại sau commit cuối).
`PEDAGOGICAL_SIMULATION_VERIFIED` chỉ được ghi khi review vòng 2 không còn BLOCKER/MAJOR.
