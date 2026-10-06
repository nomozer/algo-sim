# regular-square-pyramid-w04 — SHARED_SIMULATION_UI_CLOSURE

Việc `regular-square-pyramid`, lượt W4, máy local, `DEFAULT_MODE = LLM_ONLY`, 0 lượt gọi model. Tiếp nối W3 (đã đóng,
chờ duyệt hình) theo bản yêu cầu tổng hợp của người dùng; phần làm trước bản tổng hợp (SM trên SA, khung bảng nổi chung)
được giữ và nối tiếp, không làm lại. Bảng yêu cầu → hiện trạng → nơi sửa → cách kiểm: [`PLAN.md`](PLAN.md).

## 1. Tiếp nhận

- Mốc nhận: HEAD `f3db0f6f` (W3), candidate `5dec4572…`, `CACHE_VERSION` 114. Giữ nguyên các bản sửa W3: không bước
  dựng chỉ-mặt-phẳng-đo; đoạn được hỏi dựng trước nhãn; các cổng W3 khôi phục không nới lại.
- Xoá `frontend/public/favicon.svg` của người dùng giữ nguyên, không stage, không restore.
- Không họ hình mới, không OCR, không đổi kiến trúc, không đợt dọn docs; tên nhóm «Giao điểm của AC và BD» giữ nguyên.

## 2. Yêu cầu 3 — một cơ chế bảng nổi cho mọi bảng thông tin

Kiểm kê: [`diagnostics/PANEL_INVENTORY.md`](diagnostics/PANEL_INVENTORY.md) — ô soi, Xem đề, Thành phần, Đại lượng,
Các bước dựng. Trước W4 chỉ «Các bước dựng» nổi; ô soi thành CỘT lưới ở ≥ 1100 px (canvas co lại, camera đổi tỉ lệ);
ba ngăn dùng chung một ngăn phủ mép phải (mở cái này đóng cái kia; mobile phủ lên hình); chọn đại lượng đóng ngăn.

Sau W4 (`98b1ce8d`, `c8c49f3c`): `scene3d-floating-panel.tsx` — `BangNoiHost` giữ vị trí từng bảng và thứ tự lớp;
`BangNoi` kéo bằng tiêu đề, phím mũi tên, Escape trả tiêu điểm, về mặc định, thu gọn, kẹp khi đổi cỡ; khổ hẹp tĩnh
trong dòng chảy, nút đầu bảng 44 px. Chỗ mặc định tự tránh nút nổi và bảng đang mở (`datViTriTuDong`: cột phải, cột
trái, rồi sát hai bên từng vật cản; hết chỗ thì bậc thang không phủ dải tiêu đề bảng khác). Ba lỗi do đầu dò trình
duyệt mới bắt và đã sửa trước khi đo nghiệm thu:

| Lỗi | Gốc | Sửa |
|---|---|---|
| ba bảng chồng đúng một góc, nút đóng bảng dưới không bấm được | nhớ cả chỗ TỰ ĐỘNG qua đóng/mở | chỉ chỗ người dùng kéo mới nhớ; chỗ tự động đặt lại khi mở |
| thu cửa sổ 1100×700 với năm bảng: «Các bước dựng» bị phủ kín | bảng đã kéo kẹp vào khung nhỏ phủ lên bảng khác | khung đổi cỡ mà tiêu đề bị phủ kín ⇒ đặt lại tự động + đưa lên trên (`tieuDeBiPhuKin`) |
| camera "đổi" khi mở bảng (1e-4) | giảm chấn quỹ đạo của cử chỉ xoay trước đó (lỗi của đầu dò) | đầu dò đo bảng trước mọi cử chỉ xoay |

## 3. Yêu cầu 4 — canvas theo chiều cao khả dụng, «Bước n/N» trong thanh

- `caoKhungKhaDung` (`scene3d-playback.tsx`): canvas = phần cửa sổ dưới đỉnh canvas trừ thanh điều khiển và lề 12 px,
  sàn 320 px (màn thấp cuộn); đo khi gắn, khi đổi cỡ cửa sổ và khi cỡ trang đổi — không khi mở bảng hay chọn vật (đo
  lại ra cùng số vì đỉnh canvas không dời). Bản đầu chỉ đo lúc gắn và lệch ~100 px — đầu dò bắt.
- «Bước n/N» trong `.geo3d-controls`; dòng lời kể dài dưới thanh gỡ; mô tả đầy đủ nằm dưới mục hiện tại của «Các bước
  dựng»; trình đọc màn hình nghe lời kể qua `.geo3d-narration` `aria-live="polite"`.
- Lượt đo 1 bắt lỗi sản phẩm: trên mobile `<canvas>` WebGL giữ cỡ cũ (503 px trong khung 456 px) vì renderer chỉ đổi
  cỡ theo sự kiện cửa sổ — nay theo dõi chính khung chứa (`ResizeObserver`, `ecbe55c0`).

## 4. Yêu cầu 5 — chọn thành phần

- Lối chính: bấm thẳng lên hình ⇒ chọn + ô soi; kéo ⇒ xoay, không đổi lựa chọn (`assessDirectSelect`).
- «Thành phần» là lối phụ: nhóm là `<details>` thu gọn mặc định, có mũi tên; trạng thái mở gắn với bài; chọn vật ở
  đâu thì nhóm chứa nó mở; Enter chọn được bằng bàn phím. Vật chưa dựng KHÔNG còn hiện mờ (vẫn là lộ tên vật tương
  lai) — `treeAt`; vật cha chưa có mà con đã có (đỉnh S…D trước khối S.ABCD) thì con lên một tầng, nhóm cùng tên gộp.
- Đại lượng vẫn đọc được ở bảng «Đại lượng» khi nhãn thiếu chỗ (đầu dò W2 `unplaced_reachable`).

## 5. Yêu cầu 6 — câu chữ tại nguồn

"Thiết diện thiết diện là đa giác 4 đỉnh, cắt khối chop bởi mặt phẳng mp." sinh ở `interpreter.py` bằng cách ghép thẳng
`label or target_var`. Nay mọi lời kể đi qua `geometry_exec.ten_trong_loi_ke` (`270cae4e`): nhãn câu lệnh bỏ danh từ
đứng trước và đuôi ": phương trình"; chỉ nhận khi TRÔNG như ký hiệu (`(T)`, `(α)`, `S.ABCD`, `A′`, `d`); không thì ký
hiệu toán của tên biến; không có thì không tên — không đoán ("alpha" của P6 ⇒ không tên). Câu khép thiết diện gọi mặt
phẳng theo nhãn câu lệnh đã dựng nó: "Thiết diện (T) là đa giác 4 đỉnh, giao của mặt phẳng (α) với khối S.ABCD."
Test quét lời kể cả bảy họ + SM: không token IR, không lặp danh từ. Băm cảnh P1/P6 đổi chỉ ở 4 chuỗi lời kể mỗi cảnh
(`diagnostics/scene_hash/SCENE_DIFF.json`: 0 trường thêm/xoá, final memory giữ nguyên).

## 6. Yêu cầu 7 — SM trên SA

Đo trước bản sửa tại `f3db0f6f`: SM vẽ nét riêng đè lên SA (`diagnostics/sm_overlap/before/`). Sửa `ce44eb38`:
`quantity_annotations.doan_tren_canh` quyết CHÍNH XÁC (thẳng hàng + tham số trong [0, 1]); tầng cảnh chỉ tra id cạnh
(`boundary_edge_ids` + `edge_span`, không phép hình học); renderer để cạnh chuẩn sở hữu nét, chọn SM chỉ sáng khúc
S–M. Soát lượt đo 3 thấy khúc ấy không sáng thật trên trình duyệt: khối ngoài chuỗi nhân quả của SM bị làm dịu, kéo
theo owner cạnh mang khúc sáng — sửa `53e4bec5` (test đỏ trước trên `buildObject3D` + `lamDiu` +
`updateCanonicalEdgeVisibility`; tiêm lỗi cho độ mờ 0.3). Chọn, nhãn, xuất xứ của SM giữ nguyên.

## 7. Cache và candidate

- `CACHE_VERSION` 114 → **115** (`aa754cb9`) theo bằng chứng row: 59 row (corpus W3 + ca SM), 36 envelope phục vụ dưới
  114 vẫn HIT dù W4 dựng envelope khác; bump làm chúng MISS (`diagnostics/PROOF_CACHE_ROW_W04.json`). Bề mặt mô hình
  `b1714b56` không đổi.
- Candidate `5dec4572…` → **`8a27a58b…`** (110 file). Ba lần đóng băng, cùng tree hash, mỗi lần trong worktree tách
  rời sạch: `c8c49f3c`, `ecbe55c0` (sau lượt đo 1), `53e4bec5` (sau soát lượt đo 3) — hai bản sửa sau chỉ ở
  `frontend/src`. Khai ở `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` (đính chính lớp W3) và sổ sống.

## 8. Đo có thẩm quyền

Script `diagnostics/w04_measure.sh` (bản chép W3 + đầu dò W4 + ca SM), worktree tách rời sạch `D:/tmp/rsp w04c`
(CRLF, có dấu cách), log ngoài worktree rồi chép vào. Bốn lần đo, chỉ lần 4 dùng để nghiệm thu
([`MEASUREMENT_ATTEMPTS.json`](MEASUREMENT_ATTEMPTS.json)):

| Lần | Commit | Kết quả | Dùng |
|---|---|---|---|
| 1 | `d7154ab8` | mobile: canvas WebGL không theo khung (lỗi sản phẩm) + kiểm bí danh cây của suite (lỗi harness) | không — sửa `ecbe55c0` |
| 2 | `643b7d7a` | một cổng đỏ: `camera_settled_rotated_neutral` chóp đều desktop (camera đứng yên, quá ít khung được vẽ) | không — không đổi gì, chạy lại trọn vẹn |
| 3 | `643b7d7a` | mọi cổng xanh; soát ca SM thì chọn SM không sáng khúc S–M (lỗi sản phẩm) | không — sửa `53e4bec5` |
| 4 | `103494c4` | **xanh trọn** | **có** (`b4f924c1`) |

Lần 4: suite 7/7 họ, 14/14 lượt dương; đầu dò W2 14/14; đầu dò W4 21/21 (bảng nổi: mở/đóng/kéo/phím/về mặc
định/Escape/đổi cỡ/nhiều bảng/chọn đại lượng, canvas + camera + bước trước/sau; bố cục: thanh sát đáy, «Bước n/N»,
không dòng lời kể, `aria-live`, không tràn ngang, đỉnh/nhãn không bị cắt ở khung trung tính/xoay/đổi cỡ, canvas WebGL
theo khung; chọn trên hình; cây); ca SM; occlusion pass (4 cảnh chờ duyệt, U2); phát lại pass; 68 crop, 0 bất đồng
oracle, 0 owner trùng. Không cổng nào bị nới hay bỏ.

## 9. Skill thực dùng

Impeccable (Operate, tinh chỉnh bản sắc có sẵn; kiểm ảnh trình duyệt từng vòng), Superpowers (kế hoạch ngắn
`PLAN.md`, systematic-debugging cho từng lỗi đầu dò bắt, TDD đỏ-trước cho mọi bản sửa, verification-before-completion),
Karpathy (sửa đúng chỗ, không trừu tượng thừa), Ponytail (review diff trước đo nghiệm thu: một chỗ lặp gộp lại, phần
còn lại gọn). Không subagent.
