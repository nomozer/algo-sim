# classroom-band-fit — kế hoạch (ghi TRƯỚC lượt đo có thẩm quyền)

Việc: sửa tối thiểu `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` trước khi nghiệm thu. Máy local, nhánh
`feat/regular-square-pyramid`, 0 lượt gọi model, `LLM_ONLY`, `CACHE_VERSION` 118 (không bump — chỉ frontend, envelope
không đổi). Không họ hình mới, không đổi DSL/FactGraph/compiler/prompt/schema, không redesign header.

## 1. Nguyên nhân (đo, `diagnostics/baseline_95a56a17/CLASS_BAND_PROBE.json` + `runs/final-acceptance/results/`)

- **Ngang thấp** (`(orientation: landscape) and (max-height: 30rem)`): hàng trên bị ép một dòng (`flex-wrap: nowrap`,
  `95a56a17`), tên bài `flex: 1 1 0; min-width: 0` chỉ nhận phần dư ⇒ có dải lớp thì còn 0 px; nhóm công cụ
  `.geo3d-thanh-nut` vẫn `flex-wrap: wrap` nên co về bề rộng một nút ⇒ bốn nút xếp dọc, hàng trên 148–224 px, canvas và
  cột điều khiển xuống dưới mép; nút quay lại co lại, chữ «Bài thực hành» xuống ba dòng.
- **Dọc hẹp** (360×640): hàng trên được xuống dòng; mỗi mục dải lớp (nhãn bài, «Giao cho lớp», dock, chỉ báo) thành
  một dòng, chữ quay lại dài («Bài thực hành») đẩy tên bài xuống dòng riêng ⇒ thanh phát dưới mép.
- **Ngân sách chiều cao** (người dùng giữ sàn canvas 320 px, vùng chạm 44 px): không dải, 360×640 chỉ dư 7 px, 640×360
  dư 26 px ⇒ một dòng dải lớp riêng (≥ 32 px + khe) không vừa ở 640×360, 844×340, 360×640 với bất kỳ vai nào. Bản
  sửa gốc (tên bài có sàn, công cụ không co, dải xuống dòng hai, dock thu gọn) đo được 15/24; người dùng chọn phương án
  «chip lớp học gọn» cho chín ca còn lại (2026-10-09).

## 2. Sửa (`45f5a7f0`; candidate đóng băng lại `83db0e97`, cây đo không đổi)

`.geo3d-ten-bai` `min-width: 4rem`; `.geo3d-quay-lai` không co/không xuống dòng; ngang thấp `.geo3d-thanh-nut`
`flex: none; flex-wrap: nowrap`; `NhomLop` (cạnh `MenuCongCu`) bọc dải lớp — màn rộng `display: contents` (y như cũ),
màn chật `(orientation: landscape) and (max-height: 30rem), (max-width: 48rem) and (max-height: 50rem)` gom dải vào một
chip disclosure mang trạng thái lớp (`LiveClassStrip tomTat`, chỉ đọc, không hỏi phiên lần hai) và mở dải đầy đủ trong
hộp thả neo cả hàng trên; ≤ 48rem có chip ⇒ nút quay lại chỉ còn mũi tên (`aria-label` giữ tên). `SimulationWorkspace`
chỉ truyền dải lớp khi có bài giao hoặc là giáo viên ⇒ mô phỏng tự học không có chip.

## 3. Đo (đăng ký trước)

- **Đầu dò dải lớp** `diagnostics/probe-class-band-v2.mjs` — 3 vai (giáo viên chưa dạy / đang dạy, học sinh theo cô)
  × 8 khổ (640×360, 667×375, 844×390, 844×340, 360×640, 390×844, 1366×650, 1440×900), API giả qua CDP. Đạt khi đủ: không
  cuộn ngang; tên bài ≥ 64 px trong khung; trạng thái lớp thấy được (cả hộp trong khung, hoặc chấm trạng thái hiện trọn
  trong chip — bề rộng chữ thấy được GHI LẠI); mọi nút đang hiện ở hàng trên trong khung và chạm trúng; nút phát, thanh
  trượt, «Các bước dựng» trong khung; canvas ≥ 320 px, tâm không bị che; «Bước sau»/«Bước trước» bấm thật đổi bước; mở rồi
  đóng «Các bước dựng» giữ bước, lựa chọn, camera (dung sai 1e-6 như `check-mobile-layout`) và trạng thái lớp; ở chế độ chip:
  bấm chip mở, mọi nút trong hộp hiện, trong khung, chạm trúng, nhãn bài hiện, Escape đóng. Một lần thử lại có ghi log
  CHỈ khi môi trường hỏng (Chrome không mở / trang thiếu stylesheet). Nền: 9/24 trên bản dựng `95a56a17`.
- **Hồi quy không dải lớp**: `check-mobile-layout.mjs` (8 họ × 7 khổ, như run `phone-landscape-layout`).
- **Tier-A** trọn tám họ một lượt; W02 · W04 · W05 (hàng trên và menu đổi).
- **Không chạy lại** occlusion, phát lại, bộ dựng bằng chứng: renderer, khung camera, cỡ canvas không đổi; bố cục không
  dải lớp do đầu dò điện thoại đo. Bốn cảnh W14 giữ nguyên trạng thái (chờ người).
- **Ảnh**: JSON trước. Ảnh của các bộ đo chuẩn ghi ngoài kho (thư mục log, không phải bằng chứng); trong run chỉ ba ảnh
  «sau» của đầu dò dải lớp: `student_live:landscape_640`, `teacher_live:landscape_640`, `student_live:portrait_small`
  (ảnh «trước»: `runs/final-acceptance/images/class-band__student__640x360.png`).
- Worktree tách rời sạch có dấu cách trong đường dẫn; `diagnostics/measure.sh`; sau đó T3 + cổng danh tính ở commit tài
  liệu cuối.
