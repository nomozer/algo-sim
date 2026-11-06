# Axo — Gỡ cơ chế trình bày đáp án, an toàn định danh đề bài ↔ Scene3D, ổn định harness

Ngày: 2026-11-05. Trạng thái: **READY FOR USER REVIEW** — chưa merge, chưa push, 0 lời gọi AI live. Tiếp nối `axo-result-reveal-consistency`.

## A. Trạng thái mã nguồn

| | |
|---|---|
| Worktree / branch | `.superpowers/worktrees/axo-pedagogical-integration` · `integration/axo-pedagogical-construction-hardening` |
| HEAD trước | `d349ee01` (sản phẩm `514d34d4`) |
| Commit mới | `68c05cab` fix(frontend) — gỡ trình bày đáp án + định danh bản ghi · commit eval (con dấu + bằng chứng này) |
| So với `main` | 87 → 88 commit chỉ có trên nhánh; 206 commit chỉ có trên `main` (cutover Hybrid `/4`). Không merge/rebase. |
| Thay đổi của người dùng | `frontend/index.html` (tiêu đề Axo) không stage, không sửa; SHA256 `3B8A5566…A69F` khớp. |
| Backend | 0 file. `measured_system` 118 file `6809d79b…` không đổi; `CACHE_VERSION` 131 giữ nguyên. Con dấu candidate đóng băng lại trong worktree sạch tại `68c05cab`, `--verify` PASS. |

## B. Bản đồ nguyên nhân gốc

| # | Vấn đề | Nguyên nhân gốc | Nơi sửa |
|---|---|---|---|
| 1 | Luồng dựng hình mang theo hệ thống trình bày đáp án | `evaluateStudentPresentationPolicy` dựng `finalConclusions`; `AxoWorkspaceV62` render nút + bảng | `scene3d-student-presentation-policy.ts`, `SimulationWorkspace.tsx`, `global.css` |
| 2 | Cảnh có thể lấy từ bài mẫu chỉ vì trùng tiêu đề | `recoverCatalogScene3D` và `resolveGeometrySampleId` có nhánh khớp theo tiêu đề | `data/offline-catalog.ts` + 3 nơi gọi (`App.tsx`, `SessionCard.tsx`, `SimulationWorkspace.tsx`) |
| 3 | **Hồi quy của run trước:** mở bài mẫu từ Thư viện hiện đề người khác đã gõ | Đề lấy từ `originalInput` của bản ghi lịch sử; bản ghi khoá `simulation_id + config` dùng chung với bài mẫu khi chương trình biên dịch trùng | `state/store.ts` (`ActiveSimulation.problemStatement`), `SimulationWorkspace.tsx` |
| 4 | Gửi lại vào cùng bản ghi ghép đề lần 1 với cảnh lần 2 | `historyStore.record` thay envelope nhưng giữ `originalInput` cũ | `state/history.ts` |
| 5 | Ca 360 px của harness thất bại ở lượt chạy đầy đủ | Harness (xem E) | `scripts/measure-axo-performance.mjs` |

## C. Thành phần đáp án đã gỡ và dữ liệu toán học đã giữ

**Đã gỡ** (không thay bằng popup/bảng/nút khác):
- `StudentPresentationPolicy.finalConclusions` và hai tham số `completed`, `requestedIds` chỉ phục vụ nó (kèm công thức hiển thị riêng cho thể tích/bán kính mặt cầu).
- Nút `#dock-goal-reveal` ("Xem kết quả"/"Thu gọn kết quả"), bảng `#dock-goal-conclusion` ("KẾT LUẬN"), state `ketQuaDaMo`/`cuoiTruoc`/`coKetQua`/`hienKetQua`.
- CSS chỉ dùng cho bảng: `.dock-goal-reveal`, `.dock-goal-list`, `.dock-goal-item` (+ biến thể), `.dock-goal-main`, `.dock-goal-label`, `.dock-goal-val` (+ `.is-masked`), `.dock-goal-witness` (73 dòng).
- Test chỉ khoá chức năng cũ: `scene3d-final-conclusions.test.tsx` (xoá), `scene3d-result-reveal.test.tsx` (đổi thành test chống tái diễn).

**Chủ động giữ** (lý do):
- `buildPedagogicalConstructionPlan(...).goalCompletion` — ràng buộc kết quả đã xác minh (`DERIVED_VERIFIED`, provenance, `valueText`) cho test/harness kiểm chứng; `status`/`detail` vẫn nuôi thông báo **thiếu dữ kiện / mâu thuẫn** (`#dock-goal-summary`, giữ các lớp `.dock-goal-summary/-head/-title/-status-pill/-detail`).
- `tapKetQuaCuoi` — **che** đại lượng mục tiêu trên canvas.
- `coherentFormula`, chứng chỉ kernel, quantity objects trong Scene3D — hợp đồng dữ liệu và thẻ đối tượng (giá trị chỉ hiện với dữ kiện đề cho).
- Dữ kiện đề cho, nhãn độ dài, dấu vuông góc, lời dẫn từng bước: kiểm ở từng bước (`browser-final` "given data and narration remain per step").

**Bề mặt cũ còn trong kho nhưng không gắn vào sản phẩm:** `Scene3DExplorer.tsx` có bảng "Phân tích toán học" riêng; chỉ 12 file test import nó, mã sản phẩm không import. Không xoá trong run này (phạm vi lớn); test mới chặn mã sản phẩm import lại nó. Gỡ hẳn nên là một việc riêng.

**Khoá chống tái diễn:** `scene3d-no-answer-surface.test.tsx` — 11 bài mẫu × bước đầu/giữa/cuối không có nút, bảng, `data-conclusion-id`, "KẾT LUẬN", "Xem kết quả", hay đáp số trong DOM (kể cả nội dung ẩn/aria); khoá tập khoá của policy; quét mã nguồn; dữ kiện đề cho vẫn hiện; bài chỉ dựng hình không có bước "Kết luận mục tiêu"/"Kết luận và tính toán"; `goalCompletion` vẫn cho 3/36π và 4/16π. Đỏ với `HEAD` trước (có nút).

## D. Nhất quán đề bài → Scene3D → bước dựng

| Kịch bản | Kết quả | Bằng chứng |
|---|---|---|
| 11 route bài mẫu: đề, tiêu đề tiếng Việt, đối tượng render thuộc đúng cảnh, không bề mặt đáp án — bước đầu và cuối | PASS 11/11 | `browser-final/receipt.json` |
| Hai đề **trùng tiêu đề**, khác dữ liệu: hai bản ghi riêng; Lịch sử A → B → A giữ đúng đề + cảnh | PASS | `browser-final`, `record-scene-identity.test.tsx` |
| Bản ghi cũ thiếu `scene3d`, tiêu đề giống bài mẫu: thông báo "chưa có dữ liệu không gian 3D hợp lệ", không gán cảnh mẫu | PASS (đỏ trước sửa) | `browser-final/legacy-record-missing-data.png`, test |
| Bản ghi dùng chung với bài mẫu: mở từ Thư viện hiện đề mẫu, mở từ Lịch sử hiện đề đã gõ | PASS (lỗi phát hiện ở `browser-try`, đỏ trước sửa) | `browser-try/receipt.json` (chẩn đoán), test |
| Gửi lại vào cùng bản ghi: đề và cảnh cùng lần gửi | PASS (đỏ trước sửa) | test |
| Tải lại (F5) giữ bản ghi, đề, bước | PASS | `browser-final` |
| Đổi bài liên tục, đổi khi đang phát, Back/Forward | PASS | `browser-final` |

## E. Lỗi harness 360 px — nguyên nhân thực tế

Tái hiện bằng probe trên build production (không phải suy luận):

1. Chọn X ở bước 0 của `cau-cat-mat-phang` → `sel = cau__ref_pt`, chip `cau,I,cau__ref_pt,cau__radius`.
2. Mở bài khác rồi mở lại: khôi phục theo bài đưa về bước 0 **và vẫn chọn X**.
3. Nhảy tới bước 5: X vẫn được chọn; X và IX vẫn được vẽ và có chip trong "Xem thêm" (`renderedX = [cau__ref_pt, cau__radius]`), **ổn định**, không thoáng qua. Click chip vẫn được ở cả 360 và 390 px.

Hành vi sản phẩm nhất quán: một đối tượng phụ đã "nghỉ" vẫn hiện khi đang được chọn (như bật "Hình phụ"). **Lỗi ở harness:** ca responsive đọc danh sách chip **một lần** khi X còn được chọn (trạng thái rò từ ca "X selection…" chạy trước, qua ảnh khôi phục theo bài); chọn chip đầu tiên bỏ chọn X → chip X biến mất → click chờ 20 s. Chỉ 360 px dính vì đó là lượt responsive đầu tiên của bài này (nó tự xoá lựa chọn cho các độ rộng sau); chạy riêng trong ngữ cảnh mới thì không có trạng thái rò.

**Sửa:** ca responsive xoá lựa chọn được khôi phục trước khi đọc chip (chờ theo điều kiện `!__geo3d_selected_id`, không sleep, không bỏ assertion).
**Bằng chứng:** trước — 2/2 lượt đầy đủ FAIL đúng ca này (`axo-result-reveal-consistency/ui-after`, `ui-final`); sau — **3 lượt độc lập, mỗi lượt 40/40 PASS** (`ui-run-1..3`).

## F. Kiểm thử, ảnh, hiệu năng

**Kiểm thử**
- TypeScript (`tsc -b`) + production build: PASS.
- Vitest 124 file / 1807 test trên mã đã commit: **mọi assertion PASS**, nhưng **mỗi lượt trong 4 lượt đầy đủ có 1 test hết giờ 5000 ms** (`axo-cross-family-scene3d-acceptance.test.tsx:383` ×3, `axo-ui-ux-and-pedagogical-presentation-audit.test.tsx:798` ×1). Chạy riêng: ~1.3 s. **Đối chứng trên `HEAD` cũ không sửa (`d349ee01`), cùng thời điểm: 1/2 lượt hết giờ đúng test đó.** Thời lượng cả bộ tăng từ ~23 s (sáng) lên 33–38 s ở cả hai cây ⇒ test nặng nhạy tải máy, có từ trước, **không do thay đổi này**. Chưa xử lý (đặt timeout riêng hay tách test là quyết định riêng).
- Geometry gate trong vitest (75 file hình học): nằm trong các lượt trên; không có assertion đỏ.
- Docs gate 42 PASS; `freeze_evaluation_candidate --verify` PASS; publication safety: xem commit eval.
- Browser E2E `axo-scene-consistency-browser-check`: **23/23** (`browser-final`), 0 lỗi trang, 0 request ra ngoài.
- UI harness đầy đủ: **3 × 40/40**.

**Responsive & zoom**
- 360, 390, 430, 768, 1024, 1440 px: không tràn ngang, canvas đủ cao, không bề mặt đáp án (`browser-final/responsive-*-final.png`; harness: thẻ đối tượng, nhãn, cuộn ở cả 6 độ rộng × 5 bài).
- **Zoom thật 110% của Chrome** (tuỳ chọn `default_zoom_level` trong hồ sơ tạm, **không** giả lập DPR): `devicePixelRatio = 1.1`, CSS width 1293; mép phải dock 1293, đề 1277, nút "Đổi đề toán" 1279, canvas 933 — đều trong viewport, không tràn. Trên máy có thang hiển thị OS 125%, Chrome có giao diện báo DPR 1.375 = 1.25 × 1.1 (cũng là zoom thật). **Ảnh chụp dưới zoom thật bị cắt phải** (Playwright chụp theo kích thước cửa sổ, không theo hệ số zoom) nên ảnh `real-zoom-110-final-cropped-capture.png` chỉ minh hoạ; bằng chứng bố cục là toạ độ phần tử. Phím tắt Ctrl+= thủ công: NOT TESTED.

**Hiệu năng** — Chrome 157.0.8103.38, Intel UHD Graphics, 1440×900, DPR 1, build production; baseline = build `514d34d4` (worktree sạch), candidate = build `68c05cab`; cùng script, tuần tự.

| Cảnh | Frame median ms | Frame P95 ms | Render/frame | Đổi bước median/P95 ms | Long task (orbit 15 s) | GPU buffer tạo/xoá | React commit | WebGL ctx |
|---|---|---|---|---|---|---|---|---|
| thiet-dien-chop | 6.9 → 7.0 | 7.1 → 13.9 | 1/1 → 1/1 | 75.5/104.7 → 76.8/110.3 | 1 → 2 | 5712/5712 → 5712/5712 | 3 → 4 | 1 → 1 |
| cau-cat-mat-phang | 7.0 → 7.0 | 14.1 → 13.9 | 1/1 → 1/1 | 94.6/171.0 → 71.8/98.5 | 2 → 0 | 2412/2412 → 2412/2412 | 3 → 3 | 1 → 1 |
| non-thiet-dien-truc | 6.9 → 7.0 | 7.1 → 14.0 | 1/1 → 1/1 | 55.2/107.8 → 62.4/128.8 | 0 → 0 | 2835/2835 → 1740/1740 | 3 → 3 | 1 → 1 |
| tru-thiet-dien-tron | 7.0 → 7.0 | 13.9 → 13.9 | 1/1 → 1/1 | 52.1/61.4 → 66.2/132.4 | 0 → 0 | 2364/2364 → 2364/2364 | 3 → 3 | 1 → 1 |
| cube-hexagon | 7.0 → 7.0 | 13.7 → 13.9 | 1/1 → 1/1 | 80.0/89.8 → 79.0/102.0 | 2 → 2 | 9984/9984 → 9984/9984 | 3 → 3 | 1 → 1 |
| oblique-prism | 6.9 → 7.0 | 7.1 → 13.9 | 1/1 → 1/1 | 42.7/48.7 → 50.8/68.6 | 0 → 1 | 5064/5064 → 5064/5064 | 3 → 3 | 1 → 1 |
| dense-multi-solid | 6.9 → 7.0 | 13.8 → 13.9 | 1/1 → 1/1 | 87.9/159.5 → 86.2/137.6 | 0 → 1 | 5376/5376 → 5376/5376 | 3 → 3 | 1 → 1 |
| **Gộp** | **7.0 → 7.0** | **13.9 → 13.9** | **1 → 1** | **67.5/149.6 → 71.4/124.8** (n = 168) | **5 → 6** | cân bằng | — | **1** |

- 8 biến thể quay/zoom/chọn/ẩn/cô lập/thu dock/sau bước/quay lại: 7.0/13.9 → 7.0/13.9 ms. Phản hồi zoom bánh xe: 29.8/41.4 → 27.6/40.5 ms (n = 28).
- **Đánh giá:** không thấy hồi quy; chênh lệch từng cảnh (cả hai chiều) nằm trong dao động giữa hai lượt — máy chậm dần trong ngày (xem bộ vitest). Không tuyên bố cải thiện. `non-thiet-dien-truc` baseline tạo 2835 buffer (các lượt trước và candidate: 1740) — cân bằng tạo/xoá ở cả hai nên không phải rò rỉ; nguyên nhân chưa xác định.
- Không đổi camera, renderer, hay quy tắc nét thấy/khuất.

## G. Rủi ro còn lại và điều kiện trước khi merge

- **Hai test vitest nặng hết giờ 5 s dưới tải** (có trên `HEAD` cũ). Cần quyết định: timeout riêng cho test nặng, tách test, hay chạy suite tuần tự trong cổng — trước khi dùng vitest làm cổng merge.
- `Scene3DExplorer` (không gắn vào sản phẩm) còn bảng phân tích toán học riêng; nên gỡ hẳn trong một việc riêng.
- Khoá bản ghi lịch sử vẫn là `simulation_id + config`: hai lần gửi có cùng chương trình biên dịch nhưng khác cảnh vẫn dùng chung một bản ghi (nay nhất quán theo lần gửi gần nhất, nhưng lần trước bị thay). Tách hẳn cần đổi khoá → mọi ID lịch sử cũ, snapshot `history:<id>` và lịch sử máy chủ phải chuyển đổi — **chưa làm, cần quyết định trước** (đánh giá tương thích ở đây).
- Envelope Hybrid `/4` không trả đề gốc; bản ghi mở lại từ máy chủ không có `originalInput` sẽ hiện mô tả envelope (lời lưu ý chung). Cần trường đề gốc ở backend (ngoài phạm vi).
- Nhánh đã phân kỳ với `main`: merge cần hoà giải với cutover Hybrid `/4` và một lượt T3 đầy đủ trên kết quả hoà giải.
- **Không** tuyên bố "sẵn sàng merge" hay "đã tối ưu": điều kiện trên chưa đạt.
