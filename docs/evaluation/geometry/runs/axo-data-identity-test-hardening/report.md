# Axo — Định danh dữ liệu, nguồn đề và độ tin cậy kiểm thử

Ngày: 2026-11-05. Trạng thái: **READY FOR USER REVIEW** — chưa merge, chưa push, 0 lời gọi AI live. Kết quả "đã chạy" và "suy luận" được ghi tách bạch.

## A. Baseline và trạng thái Git

| | |
|---|---|
| Worktree / branch | `.superpowers/worktrees/axo-pedagogical-integration` · `integration/axo-pedagogical-construction-hardening` (xác minh lại, khớp báo cáo trước) |
| HEAD trước | `28c7943b` (sản phẩm `68c05cab`) |
| Commit mới | `7a46646e` fix(frontend) · commit eval (con dấu + bằng chứng này) |
| So với `main` (`bb61a804`) | 206 commit chỉ có trên `main` (cutover Hybrid `/4`), 89 → 90 chỉ có trên nhánh. `main` chỉ đọc; không merge/rebase/cherry-pick. |
| File bảo vệ | `frontend/index.html` (tiêu đề Axo của người dùng) không stage/sửa; SHA256 `3B8A5566…A69F` khớp. |
| Backend / Planner / Compiler / Kernel | 0 file. `measured_system` 118 file `6809d79b…` không đổi; `CACHE_VERSION` 131 giữ (không đổi schema, prompt, chính sách sinh kết quả). Con dấu candidate đóng băng lại trong worktree sạch tại `7a46646e`, `--verify` PASS. |
| `Scene3DExplorer` | Không xoá. Vẫn chỉ 12 file test import; mã sản phẩm không import (khoá ở `scene3d-no-answer-surface.test.tsx`). |

## B. Bản đồ dữ liệu (đọc từ mã, không từ báo cáo)

| Tầng | Nguồn có thẩm quyền | Định danh | Lưu ở đâu | Khi nào thay |
|---|---|---|---|---|
| 1. Học sinh nhập đề | `ProblemInput.tsx` (`problemText` của ô soạn) | — | store (tạm) | mỗi lần gõ — **không bao giờ là đề của bài đang mở** |
| 2. Gửi phân tích | `analyzeViaServer` → `POST /api/analyze` | — | — | — |
| 3–5. Backend | nhánh này: `pipeline.py` → `compile_semantic_program_to_envelope` (`description = spec.description or spec.title`, chữ do mô hình viết); `main`: Hybrid `/4` `adapter4_route.py` (`description` = lời lưu ý chung; đề gốc chỉ được băm nội bộ `source_sha256`, **không trả về**) | `simulation_id` + `config` (chương trình biên dịch), `scene3d` | — | mỗi lần phân tích |
| 6. Frontend nhận | `loadEnvelope(env, sampleId?, originalInput?)` | `activeSampleId`, `activeHistoryId`, `active.problemStatement` | store | mỗi lần mở |
| 7. Bài mẫu ↔ bài tự nhập | `GEOMETRY_SAMPLES` (danh mục) | `historyIdOf` (sau sửa: chỉ cho lần mở không kèm đề) | — | — |
| 8. Lịch sử | `historyStore.record` (localStorage `algosim.history.v1`, schema 2, tối đa 30); khi đăng nhập `POST /api/history` (`history_key` ≤ 80 ký tự, duy nhất theo người dùng, `original_input` thay khi có gửi) | trước: `historyIdOf`; sau: `submissionIdOf` cho lần gửi | local + máy chủ | xem C1 |
| 9. Reload / Back / Forward | URL `/simulation/<slug của activeSampleId ?? activeHistoryId>` → `resolveLocationRoute` (bài mẫu theo slug, hoặc bản ghi lịch sử theo id) | như trên | URL + history state | mỗi lần điều hướng |
| 9'. Trạng thái UI theo bài | `learner-recovery-snapshot` khoá `sample:<id>` ưu tiên, rồi `history:<id>` | khoá snapshot | sessionStorage/localStorage | mỗi thao tác |
| 10. Khôi phục từ máy chủ | `fetchServerHistory` → `replaceAll` | `history_key` mờ | local | khi đăng nhập |

Fallback âm thầm từng có: (i) `recoverCatalogScene3D`/`resolveGeometrySampleId` theo **tiêu đề** — đã gỡ ở run trước; (ii) `activeSampleId` suy theo chương trình biên dịch cho **mọi** lần mở — gỡ ở run này (C2).

## C. Nguyên nhân gốc

| # | Lỗi (đã tái hiện bằng test/trình duyệt) | Nguyên nhân | Ảnh hưởng |
|---|---|---|---|
| C1 | Hai đề KHÁC nhau biên dịch ra cùng chương trình dùng chung một bản ghi: bản ghi `h19k4q8p` nhận đề và cảnh của lần gửi sau, lần trước mất | Khoá lịch sử = `historyIdOf` = `simulation_id + config` (đã xác nhận trong `history.ts` và `POST /api/history`) | mất bản ghi học tập; đề/cảnh của lần trước bị ghi đè cả local lẫn máy chủ |
| C2 | Lần gửi trùng chương trình với bài mẫu bị trình bày như bài mẫu: URL bài mẫu, snapshot `sample:<id>` dùng chung, **tải lại hiện đề mẫu** | `loadEnvelope`/`reopenFromHistory` suy `activeSampleId` theo chương trình biên dịch kể cả khi có đề | sai đề sau reload; lựa chọn/bước của bài mẫu và bài tự nhập trộn nhau |
| C3 | Mở bài mẫu không kèm đề trúng bản ghi lần gửi cũ cùng khoá ⇒ ghi đè envelope của lần gửi | `record` luôn thay envelope | mất cảnh của lần gửi |
| C4 | **Mở lại một lần gửi tạo bản ghi trùng** (chỉ thấy trong trình duyệt thật) | `scene3d-view.tsx` ghi cờ UI `_auxiliaryShown` thẳng vào đối tượng mặt cầu của envelope; cache lịch sử dùng chung tham chiếu nên bản ghi có thể bị lưu kèm cờ; băm cảnh đổi ⇒ khoá lần gửi đổi | nhân bản lịch sử; dữ liệu có thẩm quyền bị tầng UI sửa |
| C5 | Bản ghi không có đề gốc hiện `description` của envelope như đề (lời lưu ý Hybrid `/4` hoặc chữ do mô hình viết) | Chuỗi dự phòng `problemStatement → description → title` | đề "giả" không ai nhập |
| C6 | 5 s timeout ở bộ vitest đầy đủ | **Tranh chấp CPU**: vitest 4 mặc định mở (luồng logic − 1) = 11 fork trên máy 12 luồng/16 GiB; hai test hình học nặng (riêng ~1.3 s) lên 2.5–6.5 s | cổng kiểm thử chập chờn |
| C7 | Fixture "Khối chóp và khối thành phần" (family07) | Lời đề đóng băng dùng chữ **D cho hai điểm** (trung điểm SA và đỉnh khối thứ hai); cảnh đặt `D` (trung điểm) và `D1` (đỉnh) | ký hiệu gây hiểu nhầm; dữ liệu toán học **nhất quán** (xem G) |

## D. Thay đổi triển khai

**Ba định danh, tái dùng cấu trúc sẵn có (không thêm trường lưu trữ, không đổi schema):**
- `historyIdOf(env)` — định danh chương trình biên dịch (giữ nguyên): nhận bài mẫu, khoá cho lần mở không kèm đề.
- `sceneDigestOf(env)` — định danh Scene3D (cyrb53 của `scene3d`, bỏ khoá `_…` chạy-thời-gian).
- `submissionIdOf(env, đề)` — định danh lần gửi `s…` = chương trình + đề chuẩn hoá (NFC, gộp khoảng trắng) + cảnh. Cùng đề cùng kết quả ⇒ một lần học (chạm, không nhân bản); khác đề hoặc khác cảnh ⇒ bản ghi riêng.
- **Ngữ cảnh trình bày:** `activeSampleId` chỉ suy theo chương trình khi lần mở không kèm đề; mở bài mẫu tường minh bỏ qua mọi đề kèm theo; bản ghi có đề không bao giờ mở lại như bài mẫu. Nguồn đề: `learner` (đề của chính lần mở) → `catalog` (lấy từ `GEOMETRY_SAMPLES`, không từ envelope đã lưu) → `missing` ("Bản ghi này không lưu đề gốc.", mô tả envelope chỉ hiện sau nhãn "Mô tả mô hình do hệ thống tạo:"); lộ ra qua `data-statement-source`.

**Tương thích lịch sử (đã kiểm):** bản ghi cũ giữ nguyên ID `h…`, đọc như cũ (schema 2 không đổi); được **dùng lại** khi gửi lại đúng đề, đúng chương trình, đúng cảnh; không bao giờ bị viết lại khi mở bài mẫu. Không xoá, không chuyển đổi hàng loạt. Snapshot `history:<id>` của bản ghi cũ giữ khoá. Máy chủ: `history_key` là chuỗi mờ ⇒ khoá `s…` (≈ 12 ký tự) hợp lệ, **không cần sửa backend**; bản ghi cũ trên máy chủ đọc và mở lại đúng (test). Hệ quả có chủ đích: bản ghi cũ đã bị ghép (C1, trước sửa) **không thể tách lại** — dữ liệu lần gửi bị ghi đè trước đây không còn.

**Trình xem:** `_auxiliaryShown` gắn vào bản sao khi dựng (`scene3d-view.tsx`), không còn sửa envelope.

**Vitest:** `vite.config.ts` `test.maxWorkers = floor(availableParallelism / 2)`. Không đổi timeout, không bỏ assertion.

**Fixture:** test định danh điểm cho mọi cảnh audit/danh mục; lời đề đã sửa cho fixture tổng hợp family07 (`DENSE_MULTI_SOLID_STATEMENT`), harness dùng nó; `audit_scenes.json` (bằng chứng đóng băng) không sửa.

**File:** `state/history.ts`, `state/store.ts`, `components/SimulationWorkspace.tsx`, `simulations/domains/geometry/scene3d-view.tsx`, `vite.config.ts`, `scripts/measure-axo-performance.mjs`, `scripts/axo-scene-consistency-browser-check.mjs`; test mới `components/submission-identity.test.tsx` (9), `geometry/fixture-point-identity.test.tsx` (28); cập nhật `record-scene-identity.test.tsx` (ngữ nghĩa bản ghi riêng), `axo-error-navigation-matrix.test.tsx` (dùng ID do `record` cấp thay vì tự dựng công thức khoá). Mọi test mới đỏ trước sửa (tiêm lỗi cho C4).

## E. Kiểm thử (đã chạy)

| Lệnh | Kết quả |
|---|---|
| `npx tsc -b` + `vite build` | PASS |
| `npx vitest run` — **cấu hình mới, 7 lượt độc lập** (5 lượt sau sửa cấu hình + 2 lượt trên mã cuối `7a46646e`) | **7 × 0 FAIL, 0 TIMEOUT**; mã cuối 2 × **1843/1843**; hai test nặng 1.5–2.0 s |
| Thí nghiệm worker (cùng cây, trước sửa cấu hình): mặc định 11 | test nặng 2.8/2.5 s và 6.5/6.3 s; **2 TIMEOUT** ở lượt 2 |
| — `--maxWorkers=6` (×2) / `=4` (×2) | test nặng 1.4–1.9 s / 1.5–1.9 s; 0 timeout; thời gian bộ 27–28 s / 30–34 s (mặc định 25–32 s) |
| Docs gate + candidate test (pytest) | PASS (xem commit eval) |
| Browser E2E `axo-scene-consistency-browser-check` | **27/27** (`browser-final`) |
| UI harness đầy đủ | **2 × 40/40** trên mã cuối (`ui-final-1/2`), thêm 2 × 40/40 trước sửa trình xem (`ui-run-1/2`) |

E2E phủ: 11 route mẫu; dữ kiện từng bước; trùng tiêu đề A → B → A; bản ghi cũ thiếu Scene3D; **trình xem không sửa Scene3D, mở lại không nhân bản**; lần gửi trùng chương trình mẫu (URL riêng `/simulation/s…`, đề còn sau reload, bài mẫu không động vào bản ghi); hai đề cùng chương trình + lựa chọn không lan; bản ghi thiếu đề gốc; F5; đổi nhanh; đổi khi phát; Back/Forward; 6 độ rộng; zoom thật 110%. Lượt E2E đầu (`browser`, 25/26) là bằng chứng phát hiện C4.

Bản thời gian chi tiết: `vitest-timing.json`. Lưu ý: `axo-runtime-recovery` (mở Chromium thật trong vitest) chạy 4.0–4.5 s, sát mặc định 5 s, chưa từng hết giờ trong 13 lượt — **theo dõi**, không đổi.

## F. Hiệu năng (đã chạy, cùng máy, cùng script, tuần tự)

Chrome 157.0.8103.38, Intel UHD Graphics, 1440×900, DPR 1, build production. Baseline = build `68c05cab` (worktree sạch), candidate = build `7a46646e`.

| Cảnh | Frame median ms | Frame P95 ms | Render/frame | Đổi bước median/P95 ms | Mở bài median ms | Long task | GPU buffer tạo/xoá | WebGL ctx |
|---|---|---|---|---|---|---|---|---|
| thiet-dien-chop | 7.0 → 6.9 | 13.9 → 7.1 | 1/1 → 1/1 | 85.9/148.7 → 68.1/90.0 | 145.2 → 180.9 | 2 → 1 | 5712/5712 → 5712/5712 | 1 → 1 |
| cau-cat-mat-phang | 7.0 → 6.9 | 14.0 → 13.8 | 1/1 → 1/1 | 65.4/94.9 → 61.3/75.4 | 119.2 → 102.3 | 1 → 0 | 2412/2412 → 2412/2412 | 1 → 1 |
| non-thiet-dien-truc | 7.0 → 6.9 | 13.7 → 7.0 | 1/1 → 1/1 | 44.4/59.8 → 37.3/39.9 | 95.4 → 84.3 | 0 → 0 | 1740/1740 → 1740/1740 | 1 → 1 |
| tru-thiet-dien-tron | 7.0 → 7.0 | 14.0 → 13.8 | 1/1 → 1/1 | 59.4/129.8 → 45.8/61.4 | 167.2 → 112.7 | 2 → 0 | 2364/2364 → 2364/2364 | 1 → 1 |
| cube-hexagon | 7.0 → 6.9 | 13.8 → 7.1 | 1/1 → 1/1 | 100.8/171.4 → 74.5/94.2 | 178.7 → 156.1 | 2 → 2 | 9984/9984 → 9984/9984 | 1 → 1 |
| oblique-prism | 6.9 → 6.9 | 7.0 → 7.0 | 1/1 → 1/1 | 44.0/49.3 → 38.7/56.0 | 96.3 → 97.8 | 0 → 0 | 5064/5064 → 5064/5064 | 1 → 1 |
| dense-multi-solid | 6.9 → 6.9 | 7.0 → 7.0 | 1/1 → 1/1 | 53.9/62.3 → 54.8/69.9 | 136.8 → 109.4 | 0 → 0 | 5376/5376 → 5376/5376 | 1 → 1 |
| **Gộp** | **7.0 → 6.9** | **13.9 → 7.1** | **1 → 1** | **58.9/133.4 → 53.1/85.3** (n = 168) | **119.7/356.2 → 111.6/207.2** (n = 21) | **7 → 3** | cân bằng | **1** |

- Biến thể quay/zoom/chọn/ẩn/cô lập/thu dock/sau bước/quay lại: 7.0/13.9 → 6.9/7.1 ms; phản hồi zoom 26.1/38.4 → 25.5/30.2 ms.
- Điều hướng (12 chu kỳ, median/P95 ms): Thư viện lạnh 141.5/199.2 → 143.1/206.1; mở bài lạnh 171.7/264.2 → 173.3/270.5; mở lại/chuyển bài ấm 117.2/135.0 → 114.9/140.3; Back 65.9/69.0 → 66.1/73.1; Forward 117.6/144.8 → 116.0/141.0. "Khôi phục lịch sử" đi cùng đường mở lại ấm; không có phép đo riêng.
- 22 lần đổi bài: 1 WebGL context; heap sau GC 17.28 → 19.92 MiB.
- **Đánh giá:** không có hồi quy. Candidate thấp hơn ở P95 nhưng các lượt cặp trước trong ngày dao động cả hai chiều ⇒ **không** tuyên bố cải thiện.

## G. Tính toán học và sư phạm

- family07 (đã chạy, số học chính xác theo metric Gram của cảnh, G = 4I): D = trung điểm SA (`construct_point.midpoint`, toạ độ = (A+S)/2); D1 ≠ D; |SA|² = 36, |D1A|² = 4, |AB|² = |AC|² = 4; D1A ⊥ AB và D1A ⊥ AC ⇒ D1A ⊥ (ABC). V(S.ABC) = 4, V(D1.ABC) = 4/3 khớp lượng trong cảnh. ⇒ Dữ liệu nhất quán; lỗi là **ký hiệu trong lời đề**. Lời đề tổng hợp đã sửa gọi đúng D (trung điểm) và D1 (đỉnh); test khoá mọi chữ cái điểm trong lời đề đều có trong cảnh và không còn "D.ABC"/"DA".
- 24 cảnh audit + 11 bài mẫu: không có hai điểm trùng ký hiệu hay trùng vị trí; chỉ family07 có nhãn "đỉnh D của khối D.ABC" dùng lại chữ của điểm khác.
- family07 có sự kiện MEASURE mang đáp số ("bằng 4/3"); kiểm: bước đầu và cuối không hiện thể tích, không có bề mặt đáp án (test).
- Không tái xuất hiện "Xem kết quả", "Thu gọn kết quả", "KẾT LUẬN", popup, bước kết luận tính đáp số: `scene3d-no-answer-surface.test.tsx` + E2E (mọi route, mọi bước kiểm). Dữ kiện đề cho, lời dẫn, dấu vuông góc, nét thấy/khuất, chứng chỉ giữ nguyên (bộ hình học 76 file xanh).

## H. Rủi ro tồn đọng

| Hạng mục | Trạng thái |
|---|---|
| Tách định danh lần gửi / chương trình / cảnh / ngữ cảnh trình bày (frontend + lịch sử local/máy chủ) | **DONE** |
| Tương thích lịch sử cũ (đọc, dùng lại, không viết lại) | **DONE** — bản ghi đã bị ghép trước đây không tách lại được (dữ liệu đã mất trước khi sửa) |
| Nguồn đề trung thực khi thiếu | **DONE** (frontend) |
| Đề gốc từ máy chủ cho bản ghi không có `originalInput` | **BLOCKED (backend `/4`)** — envelope không mang đề gốc; xem I |
| Bản ghi lần gửi cũ thiếu đề nhưng trùng chương trình bài mẫu | **PARTIAL** — hiện đề danh mục (cùng chương trình, không phải chữ học sinh); lịch sử local cũ không lưu `sampleId` để phân biệt |
| Timeout vitest | **DONE** — nguyên nhân chứng minh; 7 lượt sạch; `axo-runtime-recovery` sát ngưỡng (theo dõi) |
| Fixture family07 | **DONE** (lời đề tổng hợp); bản đóng băng giữ nguyên |
| Trình xem sửa dữ liệu cảnh ở nơi khác (ngoài `_auxiliaryShown`) | **NOT TESTED** ngoài phép so JSON sau 1.5 s dựng trong E2E (cảnh mặt cầu) |
| Chrome Ctrl+= thủ công, thiết bị di động thật, trình duyệt khác | **NOT TESTED** |
| Hai lần gửi đồng thời trên hai tab | **NOT TESTED** (localStorage không khoá giao dịch) |

## I. Chuẩn bị tích hợp Hybrid `/4`

**Đề xuất contract (chưa triển khai, chỉ để giai đoạn tích hợp):** thêm vào envelope thành công một khối tương thích ngược, giữ `description` như hiện tại:

```json
"problem": { "source": "learner_submission", "text": "<đề gốc đã chuẩn hoá>", "sha256": "<= route_d.ai.source_sha256>" }
```

- Vị trí: `backend/app/ai/adapter4_route.py::build_adapter4_response` (đã có `problem_text` và `source_sha256`), và nhánh preview `hybrid_preview.py` nếu cần cùng contract.
- Schema: trường mới là tuỳ chọn ⇒ client cũ bỏ qua; frontend ưu tiên `problem.text` khi `sha256` khớp, sau đó tới `originalInput`, rồi `catalog`, rồi `missing`.
- `CACHE_VERSION`: envelope cache đổi hình dạng ⇒ cần bump + test invalidation theo quy ước (`tests/test_cache_*_invalidation.py`), bảng danh tính `CURRENT_STATE.md`, `cache_identity.lock.json`.
- Test cần cập nhật: `test_hybrid_cutover_verification.py`, `test_final_backend_product_completion.py`, schema/envelope sync tests, kiểm "proof text" (`_noi_chung_minh`) phải bỏ qua `problem.text` (đó là đề, không phải lời chứng minh).
- Lịch sử máy chủ đã lưu `original_input` theo `history_key` ⇒ không cần migration bảng; khoá `s…` dùng được ngay.

**Xung đột tiềm ẩn khi hoà giải:** `main` đã sửa nhiều file frontend trong 206 commit (cùng `SimulationWorkspace.tsx`, `store.ts`); `main` không có các thay đổi Axo của nhánh này. Điều kiện trước merge: hoà giải riêng, chạy lại toàn bộ bộ test (với `maxWorkers` mới), E2E, UI harness, T3 đầy đủ trên kết quả hoà giải, và quyết định contract đề gốc ở trên.
