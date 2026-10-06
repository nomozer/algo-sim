# regular-square-pyramid-w04 — SHARED_SIMULATION_UI_CLOSURE · bảng kế hoạch

Run tiếp nối W3 (đã đóng, `READY_FOR_HUMAN_VISUAL_REVIEW`, chưa duyệt). Một lượt, máy local, `LLM_ONLY`, 0 lượt gọi
model. Bản tổng hợp yêu cầu của người dùng thay các đoạn bổ sung rời; phần đã làm trước bản tổng hợp (yêu cầu 4/SM,
khung bảng nổi chung) được giữ và nối tiếp, không làm lại.

Mốc nhận: HEAD `f3db0f6f` (W3), candidate `5dec4572…`, cache 114. W3 giữ nguyên: không bước dựng chỉ-mặt-phẳng-đo;
đoạn được hỏi dựng trước nhãn; các cổng W3 khôi phục không nới lại.

| # | Yêu cầu | Hiện trạng (đo/đọc ở đầu lượt) | Nơi sửa | Cách kiểm |
|---|---|---|---|---|
| 3 | Mọi bảng thông tin một cơ chế | chỉ «Các bước dựng» nổi; ô soi là CỘT lưới ở ≥ 1100 px (canvas co, camera đổi tỉ lệ — H-W2-3); Xem đề/Thành phần/Đại lượng dùng MỘT ngăn phủ mép phải (mở cái này đóng cái kia; mobile phủ lên hình); chọn đại lượng đóng ngăn | `scene3d-floating-panel.tsx` (host chung: vị trí, thứ tự lớp, chỗ mặc định tự tránh), `Scene3DExplorer.tsx`, `scene3d-playback.tsx`, `global.css` | hàm thuần (`datViTriTuDong`, `lenTren`, `batTatBang`); đầu dò trình duyệt `w04-panels-probe.mjs` 7 họ × desktop/mobile: mở/đóng/kéo/phím/về mặc định/đổi cỡ/nhiều bảng/chọn đại lượng; canvas + camera + bước trước/sau |
| 4 | Canvas theo chiều cao khả dụng; thanh phát sát đáy; «Bước n/N» trong thanh; mô tả bước trong bảng «Các bước dựng» | canvas `min(58vh, 620px)` cố định ⇒ ~170 px trống dưới ở 1440×900; dòng «Bước n/N + lời kể» dưới thẻ lời giải; lời kể sr-only đã có trong khung | `Scene3DExplorer.tsx` (đo chiều cao khả dụng một lần khi gắn / đổi cỡ cửa sổ — không khi mở bảng), `scene3d-playback.tsx` (bộ đếm bước trong thanh, mô tả bước trong bảng), `global.css` | hàm thuần chiều cao; trình duyệt: đáy thanh điều khiển sát đáy khung nhìn ở 1440×900 và màn thấp 1366×650; mobile cuộn được; nhãn điểm trong khung canvas trung tính/xoay/đổi cỡ |
| 5 | Chọn thành phần: trực tiếp trên hình + bảng «Thành phần» nhóm thu gọn | cây bung sẵn mọi nhóm; vật chưa dựng hiện MỜ (lộ tên vật tương lai) | `Scene3DExplorer.tsx` (`NutCay`: `<details>` theo nhóm, mặc định đóng, giữ trong bài, mở nhóm chứa vật đang chọn; ẩn vật chưa có ở bước) | SSR + hàm thuần; trình duyệt: bấm một đỉnh trên canvas ⇒ chọn + ô soi; kéo ⇒ không chọn; chọn qua cây (kể cả vật khuất) đồng bộ canvas |
| 6 | Câu chữ: "Thiết diện thiết diện là đa giác 4 đỉnh, cắt khối chop bởi mặt phẳng mp." | lời kể interpreter ghép `node.label or node.target_var` ở 8 chỗ ⇒ token IR (`alpha_plane`, `mp_day`, `chop`, `mp`) và lặp danh từ vào `config.frames[].narration` / `events[].explanation` (khe thuyết minh, panel Giải thích) | `geometry_exec.py` + `interpreter.py`: một helper tên-cho-lời-kể (nhãn bỏ danh từ lặp, không thì `ky_hieu_toan`, không thì không tên) | pytest trên lời kể của cả bảy họ: không `_`, không danh từ lặp, giữ ký hiệu đề (`S.ABCD`, `(T)`) |
| 7 | SM trên SA | **đã đo** ở f3db0f6f: vẽ chồng thật (`diagnostics/sm_overlap/before/`) | đã sửa `ce44eb38` (quan hệ chính xác ở `quantity_annotations`, cảnh chỉ tra id, renderer nhường nét + tô khúc) | ca SM vào bộ đo trình duyệt (ảnh sau sửa) |
| 9 | Cache / candidate | backend đổi (SM: `boundary_edge_ids`/`edge_span`; lời kể) ⇒ envelope phục vụ có thể đổi | — | bằng chứng row (tận dụng `proof_cache_row_w03.py`); đóng băng một lần sau khi ổn định |

Không làm: họ hình mới, OCR, chuyển kiến trúc, đợt dọn docs, đổi tên nhóm «Giao điểm của AC và BD».
