# Báo Cáo Kiểm Toán Cuối & Hồ Sơ Đóng Băng Thiết Kế Camera-First (`Photo Fan Stack`)

- **Phiên bản thiết kế:** `camera-photo-fan-stack-v1`
- **Baseline đối chiếu:** `main = origin/main = bb4d6b55346bc35e42bf19796b9c1f2310b9c8c0`
- **Thay đổi mã sản phẩm (`frontend/src/`, `backend/app/`):** `0` tệp (`PRODUCT_CHANGE = NO`, `CAMERA_IMPLEMENTATION_PENDING = YES`)
- **Số request gọi mô hình AI:** `0` (`MODEL_REQUEST_COUNT = 0`)
- **Prototype tự chứa (`SHA-256: ef1ea35a33a4c6af7f3e59afef337144a701c164e55fe5910452b20a442f5fb8`):** [`./prototype/axo_camera_first_ux_prototype.html`](./prototype/axo_camera_first_ux_prototype.html)
- **Đặc tả UX chính thức:** [`../../../../architecture/CAMERA_FIRST_PHOTO_FAN_STACK_SPEC.md`](../../../../architecture/CAMERA_FIRST_PHOTO_FAN_STACK_SPEC.md)
- **Hồ sơ bàn giao Frontend & Backend:** [`./FRONTEND_BACKEND_HANDOFF.md`](./FRONTEND_BACKEND_HANDOFF.md)
- **Số liệu kiểm chứng máy:** [`./results/verification-metrics-final.json`](./results/verification-metrics-final.json) · [`./tools/verify-camera-photo-fan-stack.mjs`](./tools/verify-camera-photo-fan-stack.mjs)

---

## 1. Khóa Phạm Vi Thiết Kế (Scope Freeze)

- **Phần được chốt trong hồ sơ này:** Mobile/Tablet Fullscreen Camera (`Toàn khung` mặc định bảo toàn `100%` tờ đề, Shutter chính giữa, chụp nhiều ảnh liên tiếp không chặn luồng, `Photo Fan Stack` `1` chạm mở khay ảnh, nút `Xong` không lặp số đếm, hỗ trợ safe-area và màn hình thấp), Desktop Camera Dialog gọn (`1` ảnh hiện `1` thumbnail không xòe quạt; từ `2` ảnh xếp chồng và mở quạt khi hover/focus với `0px` dịch chuyển Dialog/Shutter/`Xong`; hỗ trợ `prefers-reduced-motion`), cùng Viewer `Zoom 100%–300%` & `Pan`, `Chụp lại` đúng vị trí, `Xóa` & `Hoàn tác`, phân tách `Đóng` và `Xong`, và `0` tự gọi AI sau khi chụp.
- **Phần giữ nguyên theo sản phẩm trên `main`:** Header, Logo Axo, Navigation, Trang chủ, `ProblemInput.tsx` (Composer tổng thể), Thư viện, Workspace, `Scene3D`, giao diện mô phỏng và các bước dựng hình. Phần Header và Composer trong tệp prototype HTML chỉ đóng vai trò bối cảnh minh họa điểm nối.

---

## 2. Kết Quả Kiểm Toán Cuối 10 Rủi Ro Của `Photo Fan Stack`

Trong đợt rà soát cuối này, đã phát hiện và khóa chặt **2 điểm biên thực tế** trực tiếp trong prototype (không thêm chế độ mới hay chi tiết trang trí):
1. **Khôi phục focus bàn phím khi phiên có `> 5` ảnh:** Khi phiên có `7` ảnh (`indices 0..6`, quạt hiển thị `5` lá mới nhất `2..6`) và người dùng mở Viewer lùi về xem **Ảnh `#1` (`index = 0`)** rồi nhấn `Escape` / `Quay lại máy ảnh`, bộ chọn focus nay kẹp về lá đầu quạt (`#btn-fan-card-0`) thay vì trỏ tới `data-index="0"` không còn trên quạt; đồng thời bổ sung phím `ArrowLeft / ArrowRight` chuyển ảnh ngay ở mức `Zoom 100%` trong Viewer.
2. **Cách ly vùng nhấn các nút điều khiển chính khi quạt mở trên cửa sổ hẹp:** Tỉ lệ hóa bề rộng cầu đệm `.fan-hover-bridge-arc` theo `--fan-spread-scale` và đặt `z-index` ưu tiên cho `.desktop-shutter-group` cùng nút `Xong`, đảm bảo kiểm tra `document.elementFromPoint(cx, cy)` đạt `100%` trên mọi nút điều khiển ở cả `1440×900`, `900×700` và Chrome Zoom `110%`.

| # | Rủi ro kiểm toán bắt buộc | Kết quả | Bằng chứng đo thực tế trên Google Chrome |
| :---: | :--- | :---: | :--- |
| **1** | Quạt có che vùng điều khiển quan trọng khi hover không? | **PASS** | Kiểm tra cả `rectsOverlap` lẫn `document.elementFromPoint` trên `Đóng`, `Chọn ảnh`, `Đổi camera`, `Toàn khung`, `Shutter` và `Xong` tại `1440×900`, `900×700` và Chrome Zoom `110%`: `0` che khuất, dịch chuyển bố cục `0px`. |
| **2** | Hover có bị tự thu khi rê chuột giữa các ảnh không? | **PASS** | Quét chuột qua chuỗi lá `[0 → 1 → 2 → 3 → 4 → 1]` với thời gian dừng `130ms` mỗi bước (`> 95ms` ngưỡng trễ); `MutationObserver` ghi nhận `prematureCollapseCount = 0`. |
| **3** | Ảnh thứ `N` được chọn có khớp đúng dữ liệu gốc không? | **PASS** | Kiểm tra ở cả phiên `5` ảnh và phiên `7` ảnh (`startIdx = 2`): nhấn `#btn-fan-card-0` mở chính xác `sessionCaptures[2]` (`Ảnh thứ 3 trong 7 ảnh`, khớp tuyệt đối `fullDataUrl`). |
| **4** | Khi phiên có trên `5` ảnh, Viewer có truy cập được toàn bộ ảnh không? | **PASS** | Chụp `7` ảnh: quạt giữ trần trực quan `5` lá gọn gàng, trong khi Viewer (Desktop) và Khay ảnh (Mobile) duyệt đủ toàn bộ `7/7` ảnh từ `Ảnh thứ 1 trong 7 ảnh` (`index = 0`) tới `Ảnh thứ 7 trong 7 ảnh` (`index = 6`). |
| **5** | Trên mobile, một lần chạm có mở khay ảnh đúng không? | **PASS** | Trên `390×844` (`pointer: coarse`), chạm `1` lần vào `#btn-session-stack` (`58×48px`) mở thẳng `#cam-session-drawer`, không qua bước xòe quạt trung gian. |
| **6** | Nút `Đóng` và `Xong` có bảo toàn những ảnh đã đính kèm trước đó không? | **PASS** | Kiểm chứng đủ `4` nhánh trên Composer đã có sẵn `5` ảnh (`preIds5`): `Đóng` khi `0` ảnh mới, `Đóng → Bỏ ảnh mới` khi có `2` ảnh mới, `Đóng → Giữ ảnh`, và `Xong` đều bảo toàn nguyên vẹn thứ tự & ID của `preIds5`. |
| **7** | `Zoom/Pan` có sử dụng dữ liệu ảnh gốc thay vì thumbnail không? | **PASS** | `#lightbox-full-img` nạp đúng `photo.fullDataUrl` (`1600×1200`, dung lượng lớn gấp `> 2×` `thumbUrl` `320px`), `Zoom 250%` và kéo `Pan` đọc sắc nét công thức & hình chóp `S.ABCD`. |
| **8** | Keyboard, `Escape`, focus và `reduced motion` có hoạt động không? | **PASS** | `Tab` mở quạt qua `:focus-within`, `ArrowLeft/Right` đổi thẻ, `Escape` thu gọn quạt trước khi đóng camera, khôi phục focus chính xác và `prefers-reduced-motion: reduce` triệt tiêu thời gian chuyển động (`≤ 0.001s`). |
| **9** | Camera dialog có ổn ở Chrome Zoom `110%` không? | **PASS** | Chạy Chrome thật với `partition.default_zoom_level` (`DPR = 1.1`, cửa sổ hiệu dụng `1293×767`): Dialog `576×578px` và quạt `5` lá nằm trọn trong khung nhìn, `overflowX = 0`, `overflowY = 0`. |
| **10** | Có overflow, nút quá nhỏ hoặc giao diện bị che ở màn hình thấp không? | **PASS** | Trên `390×560` và `390×500`: `overflowX = 0`, `overflowY = 0`, `Toàn khung` giữ `100%` tờ đề (`374×281px`), mọi nút chính `≥ 44×44px`, `0` chồng lấp giữa Stack, Shutter và `Xong`. |

---

## 3. Áp Dụng Thực Tế 4 Design Skills Đã Kiểm Tra

1. **`ui-ux-pro-max`:** Cắt bỏ hoàn toàn sự lặp lại của `3` nhãn đếm số lượng trên bề mặt camera, giữ lại trọng tâm thị giác gồm khung đề `Toàn khung`, nút `Shutter` chính tâm, `Photo Fan Stack` bằng ảnh thật và nút `Xong` cố định; tách hành vi con trỏ chuột (hover xòe quạt) khỏi màn cảm ứng (`1` chạm mở khay).
2. **`design-taste-frontend`:** Đồng bộ bảng màu, chữ và độ nổi vật lý của xấp giấy đề toán với [`DESIGN.md`](../../../../../DESIGN.md) và [`tokens.css`](../../../../../frontend/src/styles/tokens.css) (`#0075de`, bo góc `8px`, viền tách lớp `#ffffff`, không nhồi badge kỹ thuật hay trang trí thừa).
3. **`.impeccable`:** Khóa đường cong mở quạt ngắn gọn `200ms cubic-bezier(0.22, 1, 0.36, 1)`, cầu đệm hover hình chữ T chống nhấp nháy, phản hồi chụp `150ms` không khóa bấm liên tiếp và tôn trọng đầy đủ `prefers-reduced-motion: reduce`.
4. **`web-design-guidelines`:** Bảo đảm mọi thẻ ảnh là `<button type="button">` thật có `:focus-visible` rõ nét, không phụ thuộc duy nhất vào hover, đạt chuẩn cảm ứng `≥ 44×44px`, phân tầng `Escape` và kiểm chứng thực tế tại Chrome Zoom `110%`.

---

## 4. Danh Mục Ảnh Nghiệm Thu Chọn Lọc (`screenshots/`)

- [`./screenshots/01-desktop-fan-stack-collapsed.png`](./screenshots/01-desktop-fan-stack-collapsed.png) — Desktop `1440×900`: `Photo Fan Stack` `5` ảnh thu gọn (`69.4px`) cạnh nút `Xong` cố định.
- [`./screenshots/02-desktop-fan-stack-open-hover.png`](./screenshots/02-desktop-fan-stack-open-hover.png) — Desktop `1440×900`: `Photo Fan Stack` xòe quạt `5` ảnh khi hover (`206.2px`), dịch chuyển bố cục `0px`.
- [`./screenshots/03-mobile-390x844-camera-3photos-stack.png`](./screenshots/03-mobile-390x844-camera-3photos-stack.png) — Mobile `390×844`: Fullscreen `Toàn khung` với nhóm `3` ảnh xếp chồng gọn, Shutter chính tâm `x = 195px`.
- [`./screenshots/04-mobile-390x844-photo-tray-open.png`](./screenshots/04-mobile-390x844-photo-tray-open.png) — Mobile `390×844`: Khay xem ảnh mở sau `1` lần chạm.
- [`./screenshots/05-viewer-highres-zoom-pan.png`](./screenshots/05-viewer-highres-zoom-pan.png) — Viewer độ phân giải gốc (`1600×1200`) đang `Zoom 250%` & kéo `Pan`.
- [`./screenshots/06-desktop-real-chrome-zoom-110-fan-open.png`](./screenshots/06-desktop-real-chrome-zoom-110-fan-open.png) — Chrome Zoom `110%` thật (`DPR = 1.1`): quạt `5` ảnh mở gọn trong khung, không che nút.
- [`./screenshots/07-mobile-short-390x500-stack.png`](./screenshots/07-mobile-short-390x500-stack.png) — Màn hình thấp `390×500`: toàn bộ khung đề và điều khiển nằm gọn không tràn.
- [`./screenshots/08-desktop-close-inline-confirm.png`](./screenshots/08-desktop-close-inline-confirm.png) — Thẻ xác nhận nội tuyến khi bấm `Đóng` lúc đã có ảnh mới.

---

## 5. Giới Hạn Chưa Được Kiểm Chứng

- `REAL_CAMERA_DEVICE_VERIFIED = NO`: Prototype sử dụng nguồn tờ đề hình học vẽ bằng `<canvas>` tự chứa, chưa chạy trên cảm biến camera vật lý của điện thoại iOS Safari / Android Chrome hay webcam máy tính thật.
- `LIVE_AI_MULTI_IMAGE_VERIFIED = NO`: Chưa triển khai và chưa đo kiểm live với Gemini cho luồng trích xuất ghép nhiều ảnh chụp liên tiếp trên Backend.
- `CAMERA_IMPLEMENTATION_PENDING = YES` & `BACKEND_FRONTEND_WORKTREES_CREATED = NO`: Chưa sửa mã sản phẩm React/FastAPI và chưa tạo hai worktree triển khai trong task đóng băng thiết kế này.
