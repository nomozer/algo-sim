# phone-landscape-layout — báo cáo (điện thoại ngang, 360 px, nghiệm thu cuối)

Việc: hoàn thiện phần responsive còn lại sau D5 và kiểm chứng lần cuối trước khi người dùng duyệt tích hợp. CORE.
`LLM_ONLY`, 0 lượt gọi model; không họ hình mới, không đổi OCR/DSL/FactGraph/compiler/prompt; candidate `7f3f0423…`
(cây đo không đổi), product `95a56a17`, `CACHE_VERSION` 118 (không bump — chỉ frontend).

## 1. Đo trước khi sửa (`diagnostics/baseline_f6ebe946/`, bản dựng của `f6ebe946`)

Đầu dò `check-mobile-layout.mjs` mở rộng TRƯỚC lượt đo này (điều khiển trong khung, tua bước không cuộn trang, nhãn trong
canvas ở bước cuối, «Xem lại toàn hình» trả camera, ba bảng giữ hình + điều khiển + đầu bảng, xoay máy giữ trạng thái):
**15/40** (sáu khổ) và **0/8** ở 667×375.

| Khổ | Lỗi |
|---|---|
| 844×390 | canvas ở sàn 320 px, thanh phát y = 392–427 trong khung 390 px; mở «Đại lượng»/«Đề bài» thì điều khiển ngoài khung |
| 667×375 | bố cục khổ hẹp khi nằm ngang: lưới 2 × 2 + hàng nút xem + canvas ⇒ điều khiển ngoài khung, mọi bảng đẩy hình khỏi khung |
| 360×640 | ba nút phát xuống ba hàng (129 px), hàng cuối y = 645–680 |
| xoay 390 → 844 · 360 → 640 | rơi vào hai lỗi trên |

## 2. Sửa (`d8ad153b`, `95a56a17`)

- **Ngang thấp** (`(orientation: landscape) and (max-height: 30rem)`, một khối CSS + cùng điều kiện `NGANG_THAP` ở
  `scene3d-playback`): chiều cao khan, bề ngang thừa (hình ràng theo chiều cao chỉ lấp ~¼ bề ngang canvas) ⇒ thanh điều
  khiển thành **cột 10rem bên phải canvas** (`.geo3d-player` lưới hai cột). Canvas giữ cùng chiều cao ⇒ hình giữ cỡ;
  không gì phủ lên hình; hai nút xem ở đầu cột. Khổ ≤ 48rem nằm ngang dùng lại bố cục rộng: bảng nổi, nút nhóm một hàng
  cạnh tên bài (một dòng, tên cắt «…»). `scene3d-playback`: thanh nằm cạnh canvas thì không trừ khỏi chiều cao khả dụng
  (`duoiKhung`); D5 (vừa hình) không áp ở ngang thấp.
- **360 px**: khe ngang của nút phát hẹp lại (≤ 48rem) ⇒ ba nút chung một hàng, thanh phát hai hàng.
- **Giữ, có lý do**: sàn canvas 320 px (lệnh: không hạ sàn) — ở 667×375 / 844×340 chỉ dải trống dưới hình rơi dưới mép,
  điều khiển ở cột bên cạnh nên vẫn trong khung. Bảng nổi phủ một phần canvas hẹp khi mở (cơ chế W4: thu gọn một chạm,
  kéo được, canvas/camera không đổi khi mở — đổi điều này là phá bất biến W4). Ca xoay trên màn thấp (§4).
- Tái sử dụng: `caoKhungKhaDung`, `CAO_KHUNG_MIN`, `caoKhungVuaHinh`, `BangNoi` (`dangNoi` đọc vị trí từ CSS nên bảng tự
  thành nổi), `.geo3d-noi`, điểm gãy 48rem. Không file/component/lớp CSS mới.

## 3. Đo trên candidate cuối (lần 3, `221ec0a0`, một lượt trọn mọi bước)

| Bộ đo (8 họ) | Kết quả |
|---|---|
| Điện thoại/ngang `check-mobile-layout` (7 khổ: 390×844, 360×640, 844×390, 667×375, 844×340, màn thấp, desktop) | **55/56** (trước 15/40 + 0/8). Còn 1: lăng trụ tam giác/màn thấp `FIGURE_LEFT_CANVAS_AFTER_ORBIT` (có từ trước, §4) |
| Tier-A (`compiler-scene-replay --suite`, KHÔNG lọc họ) | **8/8 trong một lượt** |
| Điều khiển cảnh W02 · bảng nổi W04 · chế độ tập trung W05 | 16/16 · 24/24 · 24/24 |
| Occlusion · phát lại · bộ dựng bằng chứng | PASS (0 lỗi; 4 cảnh W14 chờ người duyệt) · PASS · 72 crop, 0 bất đồng oracle |

Chi tiết đầu dò: ba khổ ngang 8/8 mỗi khổ, điều khiển cuối cùng kết thúc ở y ≤ 334 px, canvas 320 px (hình giữ cỡ), hai nút
xem trong khung và không phủ canvas; 360×640 8/8, mở bảng vẫn thấy ≥ 94 % hình; «Xem lại toàn hình» trả đúng camera ban đầu
56/56; tua bước cuộn trang 0 px (322 lần đo); nhãn điểm + 78 nhãn số đo trong canvas ở bước cuối; xoay máy giữ bước, lựa chọn,
camera 40/40; không cuộn ngang. Điện thoại dọc, màn thấp, desktop: chiều cao canvas y hệt D5 (320–519 · 435 · 685 px).

Các lần đo trước (`MEASUREMENT_ATTEMPTS.json`):
- Lần 1 (`9af3e8a3`, product `d8ad153b`): lỗi SẢN PHẨM — máy 360×640 xoay ngang (640×360) để cột điều khiển dưới mép ⇒ sửa
  `95a56a17`, thêm khổ 844×340. Ba lỗi khác chạy lại trên CÙNG bản dựng đều xanh (trang thiếu stylesheet, sai 4 mức màu sau
  bỏ chọn, một lần mở bảng hụt) — môi trường/thời điểm.
- Lần 2 (`221ec0a0`): hai lần mở «Các bước dựng» hụt ngay sau khi tải (W02 dừng giữa chừng, để lại một Chrome) rồi bốn
  `WS_OPEN_TIMEOUT`. Điều tra: 35/35 lần chạm đầu mở được trên cùng bản dựng (đúng nhịp của bộ đo và chậm 2 s), nút không dịch
  chỗ trong 3 s sau tải; dừng Chrome rò (cổng 9414, hồ sơ của bộ đo) rồi đo lại TRỌN lần 3. Không ghép kết quả các lần.

## 4. Nhãn rời canvas sau cú xoay (màn thấp) — đánh giá, không sửa

Một họ (lăng trụ tam giác), một khổ (1366×650), một cú kéo 120 × 40 px; 55/56 lượt khác giữ nhãn trong canvas. Khôi phục:
«Xem lại toàn hình» trả đúng camera ban đầu ở 56/56 lượt, nút luôn trong khung (cột ngang, hàng trên khổ hẹp, góc canvas
desktop). Sửa ở cơ chế chung chỉ có một đường — vừa khung theo cả cung xoay/mặt cầu bao — làm hình NHỎ hơn ở mọi màn hình (bất
biến kích thước hình đã duyệt) ⇒ giữ issue, chờ người dùng.

## 5. Kiểm chứng oracle và việc sửa kỳ vọng Tier-A (lượt trước)

- Ghim `oracle_source` (`b8615356`): băm cũ = blob ngay trước commit đổi (`23aff0ad~1`, `f967ba24~1`); `chuong_trinh` trùng byte;
  `thesis_acceptance_corpus.py` cũ ↔ mới cùng AST (chỉ đổi một dòng chú thích) ⇒ oracle không đổi nội dung.
- Kỳ vọng ca thiếu chiều cao (`a51c788b`): khớp ba thẩm quyền độc lập — test backend `test_exact_dimensions` (N01 →
  `ASSUMPTION_DETERMINES_ANSWER`/`SOURCE`/["chiều cao"]; ca mâu thuẫn không bị phân loại lại), khẳng định của bộ sinh fixture,
  envelope fixture sinh ở product (0 lượt LLM). Lượt này chạy Tier-A trọn 8 họ một lần: 8/8.

## 6. Giới hạn và việc chờ người dùng

- Duyệt hình **NOT_APPROVED**: `review.md` F-R1–F-R7 (+ E-R6 của `mobile-canvas-fit`); F-R7, E-R6 cần thao tác tay.
- Quyết: bảng nổi phủ canvas hẹp khi ngang (giữ cơ chế W4 hay đổi bất biến); ca xoay màn thấp (§4).
- Chưa đo: dải lớp học (`daiLop`) trong hàng trên khi ngang — hàng trên nay một dòng, dải ấy có thể làm chật ở 640 px.
- Không merge, không push, không xoá nhánh.
