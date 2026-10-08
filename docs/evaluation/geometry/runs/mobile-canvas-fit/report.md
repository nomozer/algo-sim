# mobile-canvas-fit — báo cáo (D5: mô phỏng trên điện thoại)

Việc: khép D5 (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`) trên tuyến sản phẩm và đưa nhánh tới trạng thái
nghiệm thu. Phân loại CORE. `LLM_ONLY`, 0 lượt gọi model; không họ hình mới, không đổi DSL/compiler/prompt/IR/lược đồ.

## 1. Nguyên nhân gốc (tái hiện trước khi sửa)

Đo bằng đầu dò mới `frontend/scripts/check-mobile-layout.mjs` trên bản dựng của `38a19c65` (`diagnostics/baseline_38a19c65/`):

1. `caoKhungKhaDung` (W4) cho canvas TRỌN phần chiều cao dưới đỉnh của nó — brief W5 bỏ trần ⇒ 390×844: canvas 519 px.
2. Camera đặt hình lấp `TI_LE_LAP_KHUNG` = 0,68 của chiều RÀNG BUỘC (`scene3d-camera.ts`). Trên điện thoại dọc đó là
   bề NGANG, nên phần chiều cao còn lại là dải trắng: 7/8 họ chỉ lấp 0,48–0,60 chiều cao canvas, trắng 206–270 px.
3. Khổ hẹp: bảng chảy dưới thanh điều khiển, mà thanh nằm sát đáy khung nhìn theo thiết kế ⇒ mọi bảng mở ra dưới nếp
   gấp; bảng tự cuộn vào tầm nhìn và đẩy hình ra khỏi khung (cross-section, chóp tứ giác đều, chóp tam giác đều: mở
   «Các bước dựng» cuộn 338 px, hình rời khỏi khung nhìn).
4. Tìm thêm khi đo: bảng bước dài không giữ bước đang xem trong vùng nhìn khi tua — bị giấu ở 19/40 lượt họ × khổ,
   cả desktop.

## 2. Giải pháp (phương án (b), thu hẹp)

| Phương án | Kết luận |
|---|---|
| (a) chiều cao theo bề ngang, hệ số cố định | loại (thu nhỏ chóp tứ giác ràng theo chiều cao; brief W5) |
| (c) nút nổi về lại canvas · (d) thanh công cụ một hàng | chỉ được ~50 px, không bỏ dải trắng; (c) đảo bản sửa w10, (d) đổi lưới W5 R3 |
| **(b) cao theo tỉ lệ hình chiếu** | **chọn**, chỉ ở khổ hẹp ≤ 48rem (cùng điểm gãy bảng chảy dưới hình) |

- `scene3d-playback.caoKhungVuaHinh`: canvas = rộng × tỉ lệ hình, ≤ chiều cao khả dụng, ≥ `CAO_KHUNG_MIN` (320 px). Hình
  ràng theo bề ngang giữ nguyên cỡ (bề ngang không đổi); hình ràng theo chiều cao giữ trọn phần khả dụng — không trần,
  không thu nhỏ. Desktop/màn thấp không đổi.
- `scene3d-view.tiLeKhungHinh`: tỉ lệ cao/rộng của hình ở góc nhìn mặc định từ CÙNG điểm, CÙNG phép xoay hiển thị
  (`quayHienThi`) và CÙNG hướng `chonHuongNhin` mà phép vừa khung dùng (`cauTrucTheGioi` dùng chung). Chỉ phụ thuộc
  cảnh ⇒ bước, lựa chọn, bảng, tách khối không đổi canvas hay camera. `vuaKhungRef` đồng bộ cỡ bộ vẽ trước khi vừa
  khung (chiều cao nay có thể đổi theo cảnh, đặt ở hiệu ứng bố cục của trình phát, trước hiệu ứng vừa khung của con).
- `scene3d-camera.tiLeHinhChieu`: tỉ lệ hình chiếu song song trên cơ sở phải/lên của `khungNhinSuPham`.
- Bảng bước: đổi bước ⇒ cuộn THÂN bảng cho mục bước đang xem (kèm mô tả) vào vùng nhìn; không `scrollIntoView` (cuộn
  cả trang, dời canvas trên điện thoại).
- Tái sử dụng: `caoKhungKhaDung`, `CAO_KHUNG_MIN`, `chonHuongNhin`, `cauTrucGocNhin`, `diemHuuHan`, `dayVaDinhChop`/
  `huongLenHienThi`, `chieu`, `BangNoi`, điểm gãy 48rem. Không file sản phẩm mới, không lớp CSS mới, không đổi CSS.

## 3. Kết quả đo (candidate cuối)

Đo tại `90921f53`, worktree tách rời sạch CRLF có dấu cách (`D:/tmp/mobile fit`, `node_modules` nối tới bản cài của cây
chính), candidate `7f3f0423…` (product `c9bcdcdb`), `CACHE_VERSION` 118; chính sách ảnh `toi-thieu` + tập duyệt chọn
trước (`inputs/REVIEW_SET.json`); log ở `diagnostics/logs_90921f53/`.

Điện thoại dọc 390×844 (`results/MOBILE_LAYOUT_PROBE.json` so với `diagnostics/baseline_38a19c65/`):

| họ | canvas trước → sau | hình lấp chiều cao | dải trắng trên+dưới (px) | mở «Các bước dựng»: hình còn trong khung · px thân bảng thấy |
|---|---|---|---|---|
| triangular_pyramid | 519 → 393 | 0.58 → 0.72 | 218 → 111 | có · 242 → có · 242 |
| rectangular_pyramid | 519 → 519 | 0.71 → 0.71 | 150 → 150 | có · 242 → có · 242 |
| triangular_prism | 519 → 406 | 0.48 → 0.59 | 270 → 167 | có · 242 → có · 242 |
| cuboid | 519 → 485 | 0.60 → 0.64 | 206 → 174 | có · 242 → có · 242 |
| cube | 519 → 389 | 0.51 → 0.67 | 255 → 130 | có · 242 → có · 242 |
| cross_section | 519 → 369 | 0.54 → 0.72 | 238 → 103 | không · 338 → có · 338 |
| regular_square_pyramid | 519 → 320 | 0.49 → 0.73 | 263 → 87 | không · 338 → có · 338 |
| regular_triangular_pyramid | 519 → 344 | 0.53 → 0.72 | 244 → 95 | không · 338 → có · 338 |

"Hình lấp" đo bằng hộp bao các nhãn điểm ở bước 0 (nhãn nằm ngoài đỉnh vài px). Chóp tứ giác ràng theo chiều cao nên
giữ nguyên — đúng luật không thu nhỏ.

| Bộ đo (8 họ) | Kết quả |
|---|---|
| D5 `check-mobile-layout` (5 khổ) | **39/40** (trước 18/40). Còn 1: `triangular_prism/low` nhãn rời canvas sau cú xoay — y hệt trước sửa, ngoài nhánh khổ hẹp (`ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`). Chiều cao canvas + camera không đổi qua bảng/chọn/bước ở 40/40; không cuộn ngang; bước đang xem trong bảng 40/40 (trước 21/40) |
| Suite tier-A | 7/8 tại `90921f53`; họ chóp tam giác đều đỏ vì kỳ vọng CŨ của bộ đo cho ca thiếu chiều cao (`ASSUMPTION_INVARIANCE_UNPROVEN/UNKNOWN`) trong khi sản phẩm đã đúng `ASSUMPTION_DETERMINES_ANSWER/SOURCE` từ `f967ba24` — sửa kỳ vọng `a51c788b`, chạy lại riêng bước đỏ: **PASS** (`results/rerun/`, `diagnostics/logs_a51c788b/`) |
| Điều khiển cảnh (W02) | 16/16 |
| Bảng nổi + bố cục (W04) | 24/24 (luật "thanh sát đáy" nay chỉ cho bố cục rộng; khổ hẹp: thanh không bị đẩy khỏi vùng nhìn — `b8615356`) |
| Chế độ tập trung (W05) | 24/24 |
| Occlusion | PASS, 0 lỗi; 4 cảnh W14 vẫn `human_review_pending` (nay có ảnh ở candidate cuối) |
| Phát lại | PASS 16/16 |
| Bộ dựng bằng chứng | 72 crop cạnh khuất, 0 bất đồng oracle, 0 owner trùng |
| Ảnh | 164 + 4 (chạy lại) |

## 4. Bằng chứng chuyển tiếp cho gói duyệt cũ

| Mục cũ (gói duyệt hình) | Ở candidate cuối |
|---|---|
| exact-dimensions R8 · RTP-W01 R5 (lời từ chối thiếu kích thước) | `images/regular-triangular-pyramid/negative/*/desktop/refusal.png` — lời mới: «Đề bài chưa cho độ dài chiều cao, mà đáp số lại phụ thuộc vào số liệu này…» (`ASSUMPTION_DETERMINES_ANSWER`, `reason_subjects` = chiều cao, `SOURCE`) |
| W5 R1 · R2 · R3 | `images/focus/<họ>/{desktop,low,mobile}/focus_layout.png`, `images/focus/regular-square-pyramid/mobile/menu_hien_thi.png` |
| W5 R9 | `images/<họ>/desktop/neutral_final.png` của bốn cảnh + `results/OCCLUSION_MEASUREMENT.json` |

## 5. Sai lệch tìm thấy và đã sửa (bộ đo, tài liệu)

- Bộ đo node 96/97 tại `38a19c65`: băm `oracle_source` của hai kịch bản lệch (đổi chú thích `23aff0ad`, thêm test
  `f967ba24`), suite từ chối chạy — ghim lại `b8615356` (ký hiệu oracle không đổi).
- Kỳ vọng ca thiếu chiều cao của suite (trên) — `a51c788b`.
- `AI_CONTEXT_BUNDLE.md` §1 ghi `CACHE_VERSION = 117` (nguồn: 118); `ROADMAP.md` §0 ghi danh tính `docs-cleanup` là
  `b4a33205…`/117 (cuối cùng: `7f3f0423…`/118, product `f967ba24`) — sửa ở tài liệu sống.

## 6. Danh tính

Product `c9bcdcdb` · candidate `7f3f0423…` (102 file, cây đo không đổi; chỉ `product_commit_sha` dời `f967ba24 → c9bcdcdb`,
đóng băng `002185a8`, log `diagnostics/freeze_c9bcdcdb.log`) · `CACHE_VERSION` 118 (không bump: không envelope nào đổi,
chỉ frontend) · đo `90921f53` (+ chạy lại `a51c788b`) · bằng chứng `3f874fed` · `LLM_ONLY` · bề mặt mô hình không đổi.

## 7. Giới hạn và việc chờ người dùng

- Duyệt hình **NOT_APPROVED**: `review.md` E-R1–E-R6 + mục chuyển tiếp; E-R6 cần thao tác tay trên điện thoại thật.
- Điện thoại nhỏ 360×640: canvas ở sàn 320 px, bảng vẫn dưới nếp gấp (8/8, như trước) — muốn hơn phải hạ sàn.
- Điện thoại ngang: `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD` (có từ trước, chờ chọn).
- Xoay trên màn thấp: `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN` (có từ trước, chờ quyết).
- Không merge, không push, không xoá nhánh.
