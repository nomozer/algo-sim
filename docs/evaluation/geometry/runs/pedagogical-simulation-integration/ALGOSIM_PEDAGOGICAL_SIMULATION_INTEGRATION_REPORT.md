# ALGOSIM PEDAGOGICAL SIMULATION INTEGRATION REPORT

**Master Epic:** `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · **Run:** `pedagogical-simulation-integration` ·
**Ngày:** 2026-11-03 · **Lượt gọi Gemini live:** `0` (`USD 0.00`)

Báo cáo này chỉ ghi điều đã đo. Bằng chứng nằm trong thư mục run này; mọi biên nhận của candidate trước giữ nguyên byte.

---

## 1. Baseline và định danh Git

| | Trước (checkpoint bàn giao, đã xác minh) | Sau |
|---|---|---|
| Nhánh | `research/hybrid-master-backend-replacement` | như cũ (không merge, không push) |
| HEAD | `5abf8c20` | `e8fc37fb` + commit báo cáo |
| Candidate commit | `123e57da` | `444b8c95` |
| Product commit | `d17116cb` | `6679b8fc` |
| `measured_system` | `730045ff…` (118 file) | `828da106083226004127245128fbcacd6cff7b507904e0cb21b74c164b9885a4` (118 file) |
| Registry / Planner / TypedFactNext / Adapter | `/31` · `/26` · `/2` · `/4` | **không đổi** |
| Engine | `geometry-function-engine/22` | `geometry-function-engine/23` (chỉ cảnh — §5.3) |
| `CACHE_VERSION` | `131` | `131` (không bump — §5.3) |
| `DEFAULT_MODE` / `HYBRID_ROUTE_MODE` mặc định | `LLM_ONLY` / `off` | **không đổi** |

Checkpoint được xác minh bằng `git log`, `grep CACHE_VERSION backend/app/main.py` và `freeze_evaluation_candidate.py
--verify` trước khi sửa dòng nào.

Commit của run (đều không có trailer `Co-Authored-By`):
`3223fdf4` (frontend trình bày) · `6679b8fc` (engine /23) · `dfcf0ea8` (xuất lại fixture preview) · `d938689b` (E2E +
ghi ngược) · `444b8c95` (đóng băng candidate, gắn lại template pilot) · `e8fc37fb` (biên nhận E2E).

## 2. Hành vi UI thực tế trước khi sửa

Đo bằng trình duyệt thật (Playwright Chromium headless) trên `frontend/dist` build từ `5abf8c20`, backend `uvicorn`
thật ở `HYBRID_ROUTE_MODE=staging-replay` (`REPLAY_STAGING_SIMULATED`), **30/30 ca SERVED** của corpus 16 lớp, chạy
liền nhau không tải lại trang. Ở mỗi ca, probe ghi toàn bộ chữ người học nhận được (chữ hiển thị, vùng `aria-live`,
`title`/`aria-label`): lúc tải → sau từng «Bước sau» → bảng «Các bước dựng» → «Hiện tất cả số đo» → ô soi từng đại
lượng → ô soi từng thành phần → bảng «Đề bài» → cuối cùng mới mở «Phân tích toán học». Bằng chứng:
`prefix-ui-audit.json` (tóm tắt từng ca) + `prefix-ui-audit-probe.mjs` (probe). 0 lỗi trang/console.

Trả lời mười câu hỏi của §III:

| # | Câu hỏi | Đo được trước khi sửa |
|---|---|---|
| 1 | Nhập đề thì hiện gì? | Xưởng 3D ở **Bước 1/N** (dữ kiện đề), thanh hướng dẫn «Đang dựng (bước 1/N)… Bấm Phát hoặc Bước sau», các nút «Đề bài», «Phân tích toán học», menu «Khám phá/Hiển thị/Thêm». |
| 2 | Tự xuất đáp số? | **Không** — 0 lần nêu đáp số (`=`/`bằng`/`là` + giá trị) ở mọi giai đoạn của 30 ca. |
| 3 | Tự trình bày lời giải? | **Không** — không có thẻ lời giải (đã gỡ từ W05); danh sách bước nêu hành động dựng, không nêu giá trị. |
| 4 | Tự chạy các bước dựng? | **Không** — 0/30 tự phát; 30/30 mở ở bước 1. |
| 5 | Hiện điểm/đường/mặt học sinh phải tự xác định? | Chỉ khi học sinh tự tiến bước hoặc mở «Các bước dựng» (xem §18, L1). Không tự hiện. |
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

Không sửa: `tapKetQuaCuoi` (lọc kết quả cuối ở Chế độ A), bảng «Đại lượng», nhãn số đo (`hiddenIds`), ô soi, trình
phát bước (không tự phát, mở ở bước 1), Chế độ B «Phân tích toán học» (người học tự mở — hợp đồng `DESIGN_BRIEF.md
§79–80`, `ARCHITECTURE_MAP.md:281`), luật «Hình phụ», cổng nhân chứng vuông góc, từ chối/hỏi lại, phục hồi sau lỗi hạ
tầng. Bằng chứng: §2 (trước sửa) và §13 (sau sửa) cho cùng kết quả ở những phần này. Không thêm chế độ giáo viên hay
nút «xem lời giải» mới.

## 4. Vấn đề sư phạm được xác nhận

| ID | Phân loại nội dung | Mức | Trạng thái |
|---|---|---|---|
| P-1 | `SOURCE_GIVEN` bị thay bằng câu miễn trừ | MAJOR (mất giả thiết, kể cả ⊥) | sửa §5.1 |
| P-2 | `SOURCE_GIVEN` (quan hệ ⊥, độ dài SH) không được biểu diễn | MAJOR với ca bị ảnh hưởng | sửa §5.3 |
| P-3 | `SOLUTION_REVEAL` (kết luận mục tiêu) trên sân khấu Chế độ A | tiềm ẩn | sửa §5.2 |

## 5. Thay đổi đã triển khai

1. **«Đề bài» = đề nguyên văn** (`3223fdf4`): `loadEnvelope(env, sampleId, originalInput)` vốn đã nhận đề nhưng chỉ
   ghi lịch sử; nay `active.originalInput` mang nó (cả khi `reopenFromHistory`), `SimulationWorkspace` đọc
   `active.originalInput || envelope.description || envelope.title`. Bài mẫu offline/thư viện không có đề gửi vẫn lùi
   về `description` như trước.
2. **Kết luận mục tiêu chỉ ở Chế độ B** (`3223fdf4`): chip `[data-route-d-observation]` rời cụm nút nổi trên sân khấu,
   vào bảng «Phân tích toán học», mục «Kiểm tra trên hình đã dựng» — vẫn theo luật neo F4 (`hybridTaiBuoc`) và vẫn
   nói «quan sát trên một hình, không phải chứng minh tổng quát». Nút Chế độ B có mặt cả khi cảnh chỉ có quan sát.
3. **Vẽ đường ⊥ của giả thiết** (`6679b8fc`, engine `/23`): trong `bien_dich`, đọc thẩm quyền chuẩn hoá duy nhất
   `_rang_buoc_vuong()` (gom `perpendicular_line_plane` · `altitude` · `orthogonal_projection`); một đường ⊥ đáy mà
   **chính ràng buộc ấy đã đặt** điểm ngoài đáy (bước `place_point` mang đúng luật của nó) và không trùng cạnh khối
   ⇒ một `construct_segment` sẵn có của IR. Tên do `display_names.py` («Đoạn thẳng nối A′ và H», ký hiệu `A′H`),
   nhân chứng góc vuông chính xác do `certificates.py`. Bỏ qua: chiếu xuôi (điểm H đã mang witness), cạnh khối có sẵn
   (SA ⊥ đáy giữ witness trên `canh_ben_S_A`), cặp suy biến. `ENGINE_VERSION` /22 → /23 vì cache Route D khoá theo
   phiên bản Engine; delta định danh khai ở `export_hybrid_preview_fixtures.py::IDENTITY_DELTAS`. `CACHE_VERSION` giữ
   `131`: prompt và chính sách định tuyến không đổi.
4. **E2E trình duyệt khoá hợp đồng** (`d938689b`): `verify-hybrid-product-e2e.mjs::verifyStudentModeDisclosure` + flow 7
   (§13); biên nhận ghi vào run này, biên nhận của `123e57da` giữ nguyên.

## 6. Thành phần bị ảnh hưởng

- Frontend: `frontend/src/state/store.ts`, `frontend/src/components/SimulationWorkspace.tsx`,
  `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx`, `frontend/scripts/verify-hybrid-product-e2e.mjs`.
- Backend: `backend/app/simulation/geometry_functions/engine.py` (`bien_dich`, `ENGINE_VERSION`),
  `backend/scripts/export_hybrid_preview_fixtures.py` (một delta định danh).
- Test: `hybrid-product-integration.test.tsx`, `hybrid-preview-contract.test.tsx`, `test_hybrid_product_integration.py`,
  `test_hybrid_wave1_exact_certificates.py` (17 → 18 witness, có lý do), 4 test ghim phiên bản Engine,
  `test_hybrid_preview_fixtures.py` (trỏ bộ fixture mới).
- Tài liệu: `HYBRID_PREVIEW_FRONTEND_CONTRACT.md §3.4`, `ARCHITECTURE_MAP.md:281`, `CODE_INDEX.md`.
- Không chạm: Planner, Registry, Kernel/`geometry/`, Source Gate, adapter `/4`, lược đồ IR, prompt, `client.ts`.

## 7. Chính sách dữ kiện gốc so với kết quả suy ra

| Lớp | Ví dụ | Chế độ A (mặc định) | Chế độ B (người học tự mở) |
|---|---|---|---|
| `SOURCE_GIVEN` | đề nguyên văn; «SA ⊥ (ABCD)»; AB = 2 | luôn có: «Đề bài» nguyên văn; quan hệ ⊥ thành vật + dấu góc vuông | như A |
| `SCENE_REPRESENTATION` | đỉnh, cạnh, mặt, đáy, A′H của giả thiết | hiện theo bước dựng | như A |
| `USER_REQUESTED_EXPLORATION` | tiến bước, «Các bước dựng», «Đại lượng», «Hiện tất cả số đo», ô soi | chỉ khi học sinh thao tác | như A |
| `DERIVED_GEOMETRY` | giao điểm, chân đường vuông góc phụ, thiết diện | xuất hiện ở bước dựng của nó khi học sinh tiến tới | như A |
| `SOLUTION_REVEAL` | giá trị đại lượng mục tiêu; công thức của nó; kết luận kiểm mục tiêu | **không** ở bất kỳ bước/bảng/ô soi nào | «Phân tích toán học» |

Che bằng cách **không render**, không bằng CSS: kết quả cuối không vào DOM ở Chế độ A (đã kiểm trên `textContent` và
thuộc tính ARIA, không chỉ chữ hiển thị). Backend giữ nguyên dữ liệu chính xác.

## 8. Mathematical correctness

- Đáp số không đổi: E2E kiểm từng đáp số của **30/30 ca SERVED** xuất hiện đúng trong Chế độ B (vd `8/3`, `72`, `9π`,
  `81π/16`, `√3`, `1`, `3√2/2`, `2304/625`, `cos²=2/3` → `2/3`); test backend ghim `√3` (`S2-B-A03`), `8/3`
  (`S2-B-I07`); H12 vẫn `a³/8`, `cos²=1/2`.
- `test_staging_replay_serves_and_refuses_all_16_scope_classes` (16/16 lớp, ≥ 40 ca, oracle độc lập) xanh.
- Witness ⊥ mới qua `verify_perpendicular_witness` (Gram chính xác) — 18/18 witness của 12 ca served-spec hợp lệ.
- `export_hybrid_preview_fixtures.py --verify` trên bộ cũ: mọi fixture chỉ khác bằng cặp định danh đã khai, trừ H12
  (thêm SH có witness). Thứ tự sư phạm O1–O4 của H12 sạch.

## 9. Scene3D interaction correctness

E2E (37 lần kiểm chế độ học sinh trên 30 ca khác nhau): kéo xoay + lăn chuột thu phóng trên canvas, duyệt **295 bước
dựng**, mở «Các bước dựng», bật/tắt «Hiện tất cả số đo», mở ô soi của **mọi** đại lượng và **mọi** thành phần trong cây
(vd 25/25, 50/50 …), «Đề bài», «Phân tích toán học». **0 lượt `/api/analyze`** phát sinh trong lúc xoay/thu phóng/tua/soi;
0 lỗi trang, 0 lỗi console. Không đổi camera, cây, ô soi, tách khối.

## 10. Answer-disclosure tests

- Luật phát hiện: `(=|bằng|là) <giá trị>` không theo sau bởi chữ số/phân số/căn/π, với giá trị lấy từ chuỗi Chế độ B
  render ra và oracle — **không** cấm mọi chuỗi số (dữ kiện đề và số đếm «Bước 1/14» không bị che nhầm).
- Trước sửa: 0 lần ở 30 ca (P-1/P-2/P-3 là lỗi khác loại). Sau sửa: 0 lần ở 37 lần kiểm.
- Vitest: `hybrid-preview-contract.test.tsx` khoá vị trí của quan sát (nền đỏ trên mã cũ), cùng các test SIMULATION-FIRST
  sẵn có.

## 11. Construction trace behavior

Không tự phát; mở ở bước 1; bước chỉ tiến khi học sinh bấm. Danh sách bước nêu hành động dựng («Dựng H là trung điểm
của đoạn BC», «Dựng đoạn thẳng nối A′ và H»), không nêu giá trị — sự kiện `FINAL_RESULT` chỉ đóng một bước, không mở
bước (test sẵn có). `construction_trace` kỹ thuật không được hiển thị; lời kể có lọc định danh máy (`learnerTextIsSafe`).

## 12. Refusal và clarification

Flow 5: đề mơ hồ `S2-C-A01_goc_chieu` → câu hỏi lại `[data-clarification-question]` đúng nguyên văn backend, 0 canvas;
đề mâu thuẫn `S2-D-D03_contradictory_length` → thẻ từ chối, câu hỏi lại cũ bị xoá, 0 canvas. Flow 6: lỗi hạ tầng HTTP
503 `LIVE_AI_DISABLED` → băng lỗi, không bị gán nhầm là từ chối toán học, 0 canvas, không lộ khoá/traceback; nhập lại đề
→ phục vụ bình thường **và** qua lại toàn bộ phép kiểm chế độ học sinh.

## 13. Browser E2E evidence

`pedagogical-e2e-browser-receipt.json` (`REAL_BROWSER_AND_UVICORN_NETWORK_E2E_STAGING_REPLAY`, `live_provider_calls 0`,
`dist/index.html` sha256 `4f046510…`): **7/7 flow**, 0 page error, 0 console error (miễn đúng lỗi tải tài nguyên 503
`/api/analyze` mà flow 6 cố ý gây ra). Flow 1–4, 6 có phép kiểm chế độ học sinh; flow 7 = **30/30 ca SERVED** liền nhau;
witness ⊥ có mặt ở `S2-B-I07` (SA) và `S2-B-A03` (A′H). `flow1-student-mode-final-step.png`: bước 4/4, ô soi «Thể tích
S.ABCD» không có giá trị, dấu góc vuông tại A.

Báo riêng theo §VIII:

| Trục | Kết quả đo |
|---|---|
| Mathematical correctness | 30/30 đáp số đúng trong Chế độ B; 16/16 lớp backend; witness Gram chính xác |
| Pedagogical disclosure correctness | 0 lần nêu đáp số / 37 lần kiểm; 0 quan sát trên sân khấu; «Đề bài» nguyên văn 37/37 (trước sửa 0/30) |
| User interaction correctness | 295 bước, mọi ô soi, xoay/thu phóng; 0 lượt pipeline thừa |
| Rendering correctness | canvas ≥ 200×150 ở mọi ca; witness ⊥ cho giả thiết ⊥ |
| Runtime reliability | 0 lỗi trang/console; phục hồi sau 503 |

## 14. Frontend and backend regression

- Frontend `npx vitest run`: **85/85 file, 1501/1501 test** (trước: 1486; +15 test mới, đỏ trên mã cũ — đã kiểm bằng
  cách đưa ba file sản phẩm về HEAD rồi chạy lại).
- Backend full suite sau thay đổi Engine (cây bẩn): 28 lỗi, phân loại hết — 10 do thay đổi Engine (đã sửa: bỏ đoạn khi
  chiếu xuôi/suy biến; 17 → 18 witness; delta định danh + xuất lại fixture), 18 do candidate/cây bẩn (đóng băng lại +
  gắn lại template; `test_holdout_readiness` cần cây sạch). Sau đóng băng: các nhóm ấy xanh (158 + 78 + 16 + 421 test
  kiểm lại). Kết quả có thẩm quyền: Full T3 §16.

## 15. Independent review

`CHỜ` — xem `independent-review.md`.

## 16. Full T3

`CHỜ` — `full-t3-e8fc37fb.json`.

## 17. Candidate identity

`docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` + lớp đính chính `candidate_divergence.json` (đính chính
`../hybrid-master-product-integration/candidate_divergence.json`): product `6679b8fc`, `828da106…`, 118 file, đóng băng
trên worktree detached sạch tại `d938689b` (`cay_lam_viec_sach = true`), `--verify` MATCH. Candidate `123e57da` và
biên nhận C18/C19/C21 + product-integration giữ nguyên, không chấm lại. Ba template pilot K-1/S-2/R-1 vẫn
`PENDING_OWNER_DECISION`, `paid_project_confirmed: false`; chỉ `measured_system` được gắn lại.

## 18. Giới hạn chưa giải quyết

- **L1 — Kế hoạch dựng mở bằng một cú bấm.** Bảng «Các bước dựng» liệt kê mọi bước kể cả bước chưa tới; với bài khoảng
  cách, bước như «Dựng H1: hình chiếu của C lên (SAB)» chính là phương pháp giải. Chỉ hiện khi học sinh chủ động mở
  bảng hoặc tiến bước (`USER_REQUESTED_EXPLORATION`), nên giữ nguyên; có nên giới hạn danh sách tới bước hiện tại là
  **quyết định sản phẩm của Owner**, chưa làm.
- **L2 — Đại lượng trung gian** (vd diện tích đáy) hiện khi học sinh mở «Đại lượng» hoặc «Hiện tất cả số đo» — đúng hợp
  đồng hiện hành, nhưng là một phần đường giải theo yêu cầu.
- **L3 — P-3 chỉ kiểm bằng vitest** (cấu trúc nguồn + SSR + fixture H07); đường sản phẩm `/4` hiện không tạo được
  `goal_checks`, nên chưa có bằng chứng trình duyệt.
- **L4 — Dữ liệu envelope** vẫn mang đáp số và lời kể có giá trị (cần cho Chế độ B); xem được qua công cụ nhà phát
  triển. Đây không phải hiển thị cho học sinh.
- **L5 — A′H mang vai `CONSTRUCT_AUXILIARY_GEOMETRY`** (không phải `CONSTRUCT_HEIGHT`) và witness của luật
  `orthogonal_projection` xếp `ENGINE_VERIFIED` thay vì `GIVEN` (phân loại sẵn có của `certificates.py`); hiển thị
  đúng, nhãn xuất xứ có thể chặt hơn.
- **L6 — Dấu góc vuông vẽ trên canvas**: kiểm bằng dữ liệu witness + cổng tự nhất quán + một ảnh chụp (flow 1), không
  so pixel cho mọi ca.
- **L7 — Phép phát hiện là theo mẫu** `(=|bằng|là) giá trị`; cách nói khác (chữ số viết bằng lời, LaTeX) không được bắt.
- **L8 — Chỉ replay**: mọi số ở đây là `staging-replay`, không phải độ chính xác đọc đề của Gemini.

## 19. Live Gemini status

`LIVE_PROVIDER_NOT_MEASURED` — 0 request live trong run này. `HYBRID_LIVE_VALIDATED` **không** được tuyên bố.

## 20. Production release blockers

`PRODUCTION_CUTOVER_READY` **không** được tuyên bố. Chặn: (1) `PAID_PROJECT_NOT_VERIFIED`; (2) pilot live K-1/S-2/R-1
và đánh giá held-out độc lập H-1 `NOT_MEASURED`; (3) cổng cutover `docs/MIGRATION_CHECKLIST.md` (D-04, D-11, D-13,
GATE-16) và quyết định merge/push của Owner; (4) L1 cần quyết định sản phẩm. `GENUINE_DISCOVERY_NOT_ESTABLISHED` giữ
nguyên; không thêm Geometry Function, không sửa Planner.

## 21. Git and publication status

Nhánh `research/hybrid-master-backend-replacement`, không merge vào `main`, không push, không viết lại lịch sử.
Publication safety: `CHỜ`. Trạng thái của run: `PEDAGOGICAL_SIMULATION_VERIFIED` chỉ khi §15 và §16 đạt — xem dòng
kết luận cuối.
