# regular-square-pyramid-w05 — IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE · bảng kế hoạch

Run tiếp nối W4 (đóng `READY_FOR_HUMAN_VISUAL_REVIEW`, chưa duyệt). Một lượt, máy local, `LLM_ONLY`, 0 lượt gọi
model, 0 subagent. Mốc nhận (chỉ để đối chiếu, không khôi phục): HEAD `73bc404e`, sản phẩm `53e4bec5`, candidate
`8a27a58b…`, cache 115. Cây làm việc lúc nhận: chỉ ` D frontend/public/favicon.svg` (của người dùng, không stage).

## 1. Giữ nguyên từ W3/W4 (không làm lại, không đo lại nếu không đổi)

Bảng nổi dùng chung (`BangNoiHost`/`BangNoi`), nhãn theo bước, không bước chỉ-dựng-mặt-phẳng-đo, SM không vẽ hai lần,
đường khuất, dữ kiện nguồn và danh tính phép dựng, canvas theo chiều cao khả dụng (`caoKhungKhaDung`), cây «Thành
phần» theo bước. Mọi cổng W3/W4 giữ nguyên ngưỡng.

## 2. Nguồn thiết kế đã đọc

- `DESIGN.md` (gốc kho) — **có**, đúng tệp người dùng nhắc. Áp dụng: một màu nhấn xanh (`--primary`), nút tiện ích
  bo 8 px, viền hairline, nền canvas ấm, chữ `--ink*`; không thêm hệ màu/ bóng/ bo góc mới. `docs/DESIGN_BRIEF.md`
  §2 (một thanh trên) — chế độ tập trung là ngoại lệ có chủ đích cho trang mô phỏng 3D, ghi ở đây và ở báo cáo.
- Không có `PRODUCT.md` (Impeccable `context.mjs` báo thiếu); không tạo — lượt này là tinh chỉnh bề mặt có sẵn.
- UI UX Pro Max (đã chạy đầu lượt, ghi `diagnostics/SKILL_NOTES.md`): ưu tiên điều hướng quay lại dự đoán được,
  nút chính có chữ, menu phụ có `aria-expanded`/Escape/phím mũi tên, vùng chạm ≥ 44 px trên mobile, không cuộn ngang.
  Impeccable (chế độ Operate, tinh chỉnh): bớt thứ lặp, một hệ thống — không dựng UI thứ hai cạnh bảng nổi W4.

## 3. Bảng yêu cầu

| # | Yêu cầu | Hiện trạng (đọc ở `73bc404e`) | Sửa / giữ | Cách kiểm |
|---|---|---|---|---|
| C1 | Mở mô phỏng ⇒ không gian lấp trang, ẩn header đăng nhập/đăng ký | header `nav-bar` (sticky) luôn hiện trong xưởng 3D, kèm nút «Giải thích» **không tác dụng** với cảnh 3D (`rightOpen` không đi vào `Scene3DExplorer`) | sửa: `App` không dựng `nav-bar` khi `canvasFirst`; gốc nhận lớp `la-tap-trung`; trần 1320 px của xưởng bỏ trong chế độ này | vitest SSR (header vắng khi cảnh 3D, còn ở trang khác); trình duyệt: không phần tử header, không cuộn ngang |
| C2 | Lối thoát rõ về thư viện/trang trước | không có — đường ra là thanh trên toàn cục | sửa: store nhớ `returnView` lúc `loadEnvelope`; nút «← <tên trang>» gọi `roiXuong()` (dọn như `goHome`, về đúng trang trước) | vitest store; trình duyệt: vào từ Thư viện ⇒ về Thư viện |
| C3 | Toàn màn hình là thao tác riêng, có khi trình duyệt hỗ trợ | không có | sửa: mục «Toàn màn hình» trong menu «Thêm» chỉ khi `document.fullscreenEnabled`; nghe `fullscreenchange` | vitest (vắng khi không hỗ trợ); trình duyệt: vào/ra, bước + chọn + camera giữ nguyên |
| C4 | Đổi chế độ/mở bảng/đổi cỡ giữ camera, bước, lựa chọn, phát | W4 đã đo cho bảng + đổi cỡ | giữ; đo thêm cho toàn màn hình và quay lại | đầu dò W5 |
| C5 | Bố cục: hàng trên mảnh · canvas phần còn lại · thanh phát dưới | hàng trên «Hình dựng theo từng bước» + 7 chip; canvas đo bằng `caoKhungKhaDung` | sửa hàng trên (nút quay lại, tên bài, nhóm công cụ); giữ cơ chế chiều cao | trình duyệt 1440×900, 1366×650, 390×844: đáy thanh điều khiển trong khung nhìn (desktop), không cuộn ngang, không khoảng trống lớn |
| D1 | Kiểm kê công cụ trước khi sửa | — | `diagnostics/TOOL_INVENTORY.md` | — |
| D2 | Nhóm công cụ | 7 chip phẳng: Xem đề · Thành phần · Đại lượng · Hiện tất cả · Hình phụ · Lưới · Chi tiết; nút nổi Tách khối (vô hiệu khi không có mặt) · Xem lại toàn hình | sửa: «Đề bài» (nút chính) · menu «Khám phá» (Thành phần, Đại lượng) · menu «Hiển thị» (Hiện tất cả, Hình phụ, Lưới, chú giải màu) · menu «Thêm» (Cách máy dựng, Toàn màn hình); Xem lại toàn hình giữ nút nổi; Tách khối **chỉ dựng khi cảnh có mặt** | vitest SSR + hành vi menu (Escape, mũi tên, trả tiêu điểm); trình duyệt mọi mục 7 họ |
| D3 | Chọn trực tiếp mở chi tiết; bỏ «Chi tiết» thường trực nếu không còn chức năng riêng | «Chi tiết» còn chức năng riêng (dòng «Dựa trên» phụ thuộc hình học + «Giả thiết») | chuyển vào «Thêm» thành «Cách máy dựng» (không xoá chức năng) | vitest |
| E1 | Bỏ thẻ lời giải lặp lại dưới mô phỏng | `Scene3DSolution` dưới thanh phát: Kết quả/Dữ kiện/Các bước tính — cùng tập `quantityChoices` mà bảng «Đại lượng» liệt kê; công thức + nguồn số có ở ô soi | sửa: gỡ `Scene3DSolution`; công thức luôn ở ô soi (không còn nhánh "lời giải mở") | vitest; trình duyệt: mỗi đại lượng chọn được qua «Đại lượng», ô soi mang công thức + nguồn |
| E2 | Chú giải màu trong «Hiển thị» | chú giải là khối dưới thẻ lời giải | sửa: mục chú giải trong menu «Hiển thị» | vitest + trình duyệt |
| F | Lát cắt backend | §4 | §4 | §4 |
| G | Kiểm thật | — | đầu dò W5 + bộ đo W4 cập nhật cho bề mặt mới (không hạ ngưỡng) | `diagnostics/` |
| H | Cache/candidate/tài liệu | — | quyết bằng bằng chứng row; đóng băng sau khi ổn định | `REPORT.md` |

## 4. Lát cắt backend — bộ đọc độ dài nguồn đọc chuỗi bằng nhau (ghi TRƯỚC khi sửa)

Căn cứ: tiền đăng ký `GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md` §4 (hàng `AB = AC = 5`: *"backlog: chuỗi bằng
nhau = cùng một giá trị cho mọi đoạn"*) và `ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY` (OPEN, có tiêu chí chấp nhận).
Đây là phần "chuẩn hoá dữ kiện/quan hệ có nguồn" mà brief ưu tiên; ranh giới dữ kiện đề ↔ toạ độ bố cục đã có
(chứng chỉ giả định W15) và không đổi.

- **Phần hiện tại:** `semantic_program/segment_relation.py` — `MAU_DO_DAI` + `_moi_doan_co_do_dai` (mọi đoạn đề cho độ
  dài số), `_do_dai_doan` (bản regex thứ hai của cùng phép đọc), `nhan_doan_truoc` (đoạn đề gắn cho con số).
  Nơi gọi: `grounding_gate._bang_chung` (bằng chứng GIVEN — ① mâu thuẫn, ③ nhãn đoạn), `do_dai_trong_de` ←
  `refusal_cause` (nguyên nhân từ chối), `bat_bien_do_dai` ← `analyze_contract` + `assumption_gate` (bất biến nguồn,
  chứng chỉ), `shape_constraint.phan_chua_doc` (`MAU_DO_DAI.sub` — phần dữ kiện chưa đọc), `quantity_annotations.
  _do_dai_de_cho` (đoạn mang nhãn số đề cho).
- **Thay/bổ sung:** một mẫu duy nhất đọc tiền tố chuỗi `X1 = X2 = … =` trước đoạn mang số; mọi đoạn của chuỗi nhận
  cùng giá trị, luật mâu thuẫn hiện có giữ nguyên (một đoạn hai giá trị ⇒ bỏ). `nhan_doan_truoc` → `cac_doan_truoc`
  trả MỌI đoạn của chuỗi (đổi tên để nơi gọi cũ vỡ to). `_do_dai_doan` dùng lại `_moi_doan_co_do_dai` (bỏ regex thứ
  hai).
- **Đầu vào/đầu ra:** chữ đề (đã/không `_chuan`) → `{frozenset({A,B}): Fraction}`; tiền tố trước con số → tuple đoạn.
  Không đọc `InputFact` mới, không thêm lượt gọi model, không đổi lược đồ/prompt/thẻ văn phạm (bề mặt mô hình không đổi).
- **Tiêu chí hoàn tất:** (a) `SA = SB = SC = SD = 3` gắn cả bốn; (b) chuỗi trộn giá trị khác nhau giữ mâu thuẫn;
  (c) chuỗi không có số không gắn gì; (d) `R2_L1` phục vụ `V = 16/3` qua route thật (lớp nhãn W5 đính chính
  `product_limit`, lớp W1 không sửa); (e) ca thiếu dữ kiện (chuỗi không số) ⇒ từ chối, toạ độ bố cục không thành dữ
  kiện; (f) chương trình khai sai giá trị/đoạn trong chuỗi ⇒ từ chối; (g) full suite xanh; cache quyết bằng row.
- **Họ dùng nó:** mọi họ đọc độ dài đoạn từ đề — chóp đều (cạnh bên bằng nhau), chóp có cạnh bên bằng nhau, lăng
  trụ đều/đứng (`AA′ = BB′ = …`), tam giác cân/đều trong đáy (`AB = AC = a`), tứ diện đều.

Không làm: họ hình mới, OCR, đổi kiến trúc route, đợt dọn docs, thêm bộ đọc quan hệ khác.
