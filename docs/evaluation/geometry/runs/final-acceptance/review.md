# Nghiệm thu cuối — việc của người dùng (final-acceptance)

Trạng thái: **NOT_APPROVED**. Chỉ người dùng ghi `APPROVED_BY_USER`. Bản dựng: product `95a56a17`, candidate `7f3f0423…`,
`CACHE_VERSION` 118, `LLM_ONLY`. Bài mẫu offline (thư viện bài mẫu) chạy không cần backend, 0 lượt gọi model.

## 1. Mở AlgoSim trên điện thoại (local, không đổi cấu hình bảo mật)

```bash
cd frontend && npm run build
npx vite preview --host --port 4173 --strictPort     # Ctrl+C khi xong — cổng đóng lại
```

- **Cùng Wi-Fi:** mở `http://172.16.8.185:4173` trên điện thoại (IP Wi-Fi của máy lúc 2026-10-09; đổi mạng thì xem lại bằng
  `ipconfig`, đừng dùng IP của Radmin/VMware). Máy đã có sẵn luật tường lửa cho phép `node.exe` nhận kết nối ở mạng Public
  (luật có từ trước, run này không tạo, không sửa) ⇒ không cần thêm luật; tắt `vite preview` là hết phơi cổng.
- **Android qua cáp USB (không mở cổng ra mạng):** bỏ `--host`; bật gỡ lỗi USB; trên máy tính mở `chrome://inspect#devices` →
  *Port forwarding* `4173 → localhost:4173`; trên điện thoại mở `http://localhost:4173`.
- Trên trang chủ chọn bài mẫu, ví dụ «Thiết diện của hình chóp cắt bởi mặt phẳng qua ba trung điểm» (nhiều bước, bảng dài) và
  «Thể tích khối chóp và khoảng cách từ đỉnh đến đáy».

## 2. Thao tác tay (E-R6 của `mobile-canvas-fit`, F-R7 của `phone-landscape-layout`)

Hỗ trợ tự động đã chạy (`results/TOUCH_PROXY_PROBE.json`, chạm giả lập 8/8) — **không** thay các ô dưới đây.

| # | Tư thế | Làm | Đạt khi | Đánh dấu |
|---|---|---|---|---|
| G-1 | dọc | kéo một ngón trên hình | hình xoay, trang không cuộn | ☐ |
| G-2 | dọc | chạm một cạnh/mặt trên hình | thành phần được chọn, tô nổi | ☐ |
| G-3 | dọc | Phát → Tạm dừng; «Bước sau» / «Bước trước» | bước đổi đúng, dừng là đứng yên | ☐ |
| G-4 | dọc | mở «Các bước dựng», «Đại lượng», «Đề bài»; tua bước khi bảng mở; đóng | thấy hình + điều khiển, bước đang xem hiện trong bảng | ☐ |
| G-5 | ngang | chạm từng nút trong cột điều khiển bên phải | mọi nút chạm được, không bị che | ☐ |
| G-6 | ngang | mở «Các bước dựng»; thu gọn, mở rộng, kéo bảng bằng ngón tay | bảng thu gọn/kéo được; canvas không đổi cỡ | ☐ |
| G-7 | ngang | xoay hình, chuyển bước | như G-1, G-3 | ☐ |
| G-8 | xoay máy giữa chừng | chọn một thành phần ở bước 3, xoay hình, rồi xoay máy dọc ↔ ngang | cùng bước, cùng lựa chọn, cùng góc nhìn | ☐ |
| G-9 | cả hai | thanh địa chỉ trình duyệt hiện/ẩn khi cuộn | điều khiển vẫn chạm được | ☐ |

Ghi kèm: tên máy, trình duyệt, cỡ màn hình; ô nào trượt thì mô tả + ảnh chụp màn hình.

## 3. Quyết định cần người dùng

| # | Mục | Bằng chứng | Gợi ý |
|---|---|---|---|
| D-1 | Dải lớp học làm vỡ hàng trên trên điện thoại (`ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW`) — có từ `main`, nhánh không làm tệ hơn (11/24 so với 5/24) | `report.md` §2, `images/class-band__student__640x360.png` | không chặn merge; sửa tối thiểu ở lượt sau (đề xuất §2) |
| D-2 | Bốn cảnh W14 — nhìn `runs/phone-landscape-layout/images/{triangular-pyramid,triangular-prism,rectangular-pyramid,cross-section}/desktop/neutral_final.png` (+ `hidden-edges/desktop/`): nét đứt/liền đúng không | `report.md` §4 | không chặn merge (`default_switch_blocker: NO`) |
| D-3 | Gói duyệt hình còn mở: `runs/phone-landscape-layout/review.md` F-R1–F-R6, `runs/mobile-canvas-fit/review.md` E-R1–E-R5 và các gói cũ ở `AI_CONTEXT_BUNDLE.md` §2 | — | duyệt hoặc ghi lý do |
| D-4 | UX debt chấp nhận tạm (bảng nổi che canvas khi ngang; nhãn rời canvas sau cú xoay ở màn thấp; header/thanh công cụ mobile) | `report.md` §5 | giữ OPEN |

## 4. Sau khi duyệt

Ghi quyết định (G-1…G-9, D-1…D-4) vào tệp phê duyệt do người dùng viết. Merge thẳng vào `main`, push, xoá nhánh là một lượt
LOCAL riêng có lệnh (AGENTS §2) — run này không làm.
