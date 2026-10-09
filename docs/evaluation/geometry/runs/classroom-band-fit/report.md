# classroom-band-fit — báo cáo (dải lớp học trên điện thoại)

Việc: sửa tối thiểu `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` trước nghiệm thu. Máy local, 0 lượt gọi model,
`LLM_ONLY`, `CACHE_VERSION` 118 (không bump — chỉ frontend, envelope không đổi). Product `45f5a7f0`; candidate
`7f3f0423…` (102 file, cây đo không đổi; đóng băng lại `83db0e97`); đo có thẩm quyền: lần 3 tại `6a1801e7`, worktree tách rời
sạch có dấu cách, trọn mọi bước một lượt; bằng chứng `3095e4f0`. Không họ hình, DSL, FactGraph, compiler, prompt, schema.

## 1. Nguyên nhân (đo trước khi sửa)

- **Ngang thấp** (`(orientation: landscape) and (max-height: 30rem)`): hàng trên bị ép một dòng (`flex-wrap: nowrap`,
  `95a56a17`). Tên bài `flex: 1 1 0; min-width: 0` chỉ nhận phần dư ⇒ có dải lớp thì 0 px. Nhóm công cụ
  `.geo3d-thanh-nut` vẫn mang `flex-wrap: wrap` của luật gốc ⇒ co về bề rộng một nút, bốn nút xếp dọc (hàng trên 148–224 px).
  Nút quay lại co, chữ «Bài thực hành» xuống ba dòng (77 px). Canvas + cột điều khiển bị đẩy dưới mép.
- **Dọc hẹp 360×640**: hàng trên được xuống dòng; mỗi mục dải lớp thành một dòng; chữ quay lại dài đẩy tên bài xuống
  dòng riêng ⇒ thanh phát dưới mép (743–865 px trong khung 640).
- **Ngân sách**: không dải lớp, 360×640 dư 7 px, 640×360 dư 26 px (sàn canvas 320 px, vùng chạm 44 px — giữ theo quyết
  định trước). Bản sửa gốc đưa dải xuống dòng hai đạt 15/24; chín ca 640×360 · 844×340 · 360×640 thiếu 14–103 px. Người
  dùng chọn «chip lớp học gọn» (2026-10-09).

## 2. Sửa (`45f5a7f0`) — nơi sửa và cái tái dùng

| Nơi | Thay đổi |
|---|---|
| `styles/global.css` | `.geo3d-ten-bai` `min-width: 4rem`; `.geo3d-quay-lai` `flex: none; white-space: nowrap`; khối ngang thấp `.geo3d-thanh-nut` `flex: none; flex-wrap: nowrap`; mục mới «dải lớp gọn»: `.geo3d-lop*` màn rộng `display: contents`, màn chật `(orientation: landscape) and (max-height: 30rem), (max-width: 48rem) and (max-height: 50rem)` ⇒ chip, hộp thả neo cả hàng trên; ≤ 48rem có chip ⇒ nút quay lại chỉ còn mũi tên |
| `scene3d-tool-menu.tsx` | `NhomLop` — disclosure (`aria-expanded`/`aria-controls`), bấm ngoài/Escape đóng theo đúng mẫu `MenuCongCu`; không phải menu ARIA vì trong hộp có nút, nhóm chọn, hộp thoại |
| `Scene3DExplorer.tsx` | prop `daiLopTomTat`; `co-lop` trên hàng trên; chữ nút quay lại trong `geo3d-quay-lai-nhan`, `aria-label` = trang đích |
| `LiveClassStrip.tsx` | `tomTat`: bản chỉ đọc cho chip (chấm trạng thái + số em giơ tay + tên lớp / chỉ báo học sinh + «Đã báo cô/thầy»); không hỏi phiên lần hai |
| `SimulationWorkspace.tsx` | chỉ truyền dải lớp khi có bài được giao hoặc là giáo viên ⇒ mô phỏng tự học không có chip |

Tái dùng: lớp nút `.geo3d-menu-nut`, dáng hộp `.geo3d-menu-hop` (viền, nền, bóng), mẫu bấm-ngoài/Escape của `MenuCongCu`,
`StudentLiveIndicator`, `.live-cham`/`.live-canh-bao`/`.live-lop`, điểm gãy 48rem và điều kiện ngang thấp có sẵn. Không
framework, không hệ responsive song song. Dock giáo viên, «Giao cho lớp», nút giơ tay giữ nguyên — chỉ đổi chỗ chứa.

## 3. Kết quả — 24 ca lớp học (`results/CLASS_BAND_PROBE.json`; nền `diagnostics/baseline_95a56a17/`)

**Trước 9/24 → sau 24/24.** Ô: đạt trước → sau · chiều cao hàng trên. Hai cột cuối: học sinh — bề rộng tên bài, phần trạng
thái lớp thấy được (px).

| Khổ | Giáo viên chưa dạy | Giáo viên đang dạy | Học sinh theo cô | Tên bài | Trạng thái |
|---|---|---|---|---|---|
| 640×360 | ✗→✓ 200→44 | ✗→✓ 212→44 | ✗→✓ 200→44 | 71 | 34 (chip) |
| 667×375 | ✗→✓ 200→44 | ✗→✓ 212→44 | ✗→✓ 148→44 | 89 | 43 (chip) |
| 844×390 | ✗→✓ 84→36 | ✗→✓ 168→36 | ✗→✓ 80→36 | 131 | 85 (chip) |
| 844×340 | ✗→✓ 84→36 | ✗→✓ 168→36 | ✗→✓ 80→36 | 131 | 85 (chip) |
| 360×640 | ✗→✓ 304→152 | ✗→✓ 384→152 | ✗→✓ 262→152 | 131 | 85 (chip) |
| 390×844 | ✓→✓ 270 | ✓→✓ 350 | ✓→✓ 228 | 211 | 125 |
| 1366×650 | ✓→✓ 84 | ✓→✓ 84 | ✓→✓ 36 | 238 | 125 |
| 1440×900 | ✓→✓ 84 | ✓→✓ 84 | ✓→✓ 36 | 312 | 125 |

Mỗi ca kiểm: không cuộn ngang; tên bài ≥ 64 px; trạng thái lớp thấy được; nút đang hiện trong khung và chạm trúng; nút phát,
thanh trượt, «Các bước dựng» trong khung (360×640: 633/640 px — bằng khi không có dải lớp); canvas ≥ 320 px, tâm không bị
che; «Bước sau»/«Bước trước» bấm thật đổi bước; mở/đóng «Các bước dựng» giữ bước, lựa chọn, camera và trạng thái lớp; chế độ
chip: chip mở, mọi nút trong hộp (vd giáo viên đang dạy: «Giao cho lớp», dock, «Theo cô/thầy», «Cho tự khám phá», «Gọi cả lớp
về đây», «Theo dõi», «Kết thúc») hiện, trong khung, chạm trúng, nhãn bài hiện, Escape đóng. Hai ca qua lần thử lại đã đăng ký
cho môi trường (`ENV_STYLESHEET_NOT_APPLIED`, ghi trong `env_retries`). Ảnh «sau»: `images/class-band/` (3); «trước»:
`runs/final-acceptance/images/class-band__student__640x360.png`.

Nền đỏ + tiêm lỗi (unit, `scene3d-focus-mode.test.tsx` «dải lớp gọn»): trả `min-width` tên bài về 0 và bỏ `NhomLop` ⇒ 2
test đỏ; khôi phục ⇒ xanh. Bộ đo trình duyệt có cửa sổ chứng: không dải lớp, đầu dò chuẩn đo hàng trên 36–44 px.

## 4. Hồi quy (lần 3, `diagnostics/logs_6a1801e7/`)

| Bộ đo | Kết quả |
|---|---|
| Điện thoại/ngang KHÔNG dải lớp (8 họ × 7 khổ) | **55/56** — như `phone-landscape-layout`; còn đúng ca có từ trước `triangular_prism/low` `FIGURE_LEFT_CANVAS_AFTER_ORBIT` |
| Tier-A (`compiler-scene-replay --suite`, không lọc họ) | **8/8 một lượt** (product `45f5a7f0`, cây `7f3f0423…`) |
| W02 điều khiển cảnh · W04 bảng nổi · W05 chế độ tập trung | 16/16 · 24/24 · **23/24** — `cuboid/desktop` `RUN_ERROR POLL_TIMEOUT` (trang không tải, không khẳng định nào được chạy; cảnh không có dải lớp). Kiểm lại riêng họ cuboid cùng commit 3/3 — chẩn đoán, KHÔNG ghép (`diagnostics/w05_recheck_6a1801e7/`) |
| vitest | 1040/1040 (1034 + 6 test mới) · `tsc -b` sạch |

Không chạy lại occlusion, phát lại, bộ dựng bằng chứng (`plan.md` §3): renderer, khung camera, cỡ canvas không đổi. Hai
lần đo trước là môi trường/bộ đo (`MEASUREMENT_ATTEMPTS.json`), không ghép kết quả. T3 + cổng danh tính: `handoff.md` §2.

## 5. Còn lại — phân loại

- **Giới hạn chức năng còn mở (của bản sửa này):** ở 640×360 và 667×375 chip chỉ đủ chỗ cho chấm trạng thái + «…» (34–43
  px): phiên đang dạy hay chưa đọc qua MÀU chấm; chế độ «theo cô/tự khám phá», tên lớp, số em giơ tay của giáo viên chỉ đọc
  được sau MỘT chạm (hoặc qua trình đọc màn hình — chữ đầy đủ vẫn trong cây truy cập). Ở 844 px và 360×640 dọc thấy
  «● Đang the…» (85 px). Học sinh giơ tay cần hai chạm trên màn chật. Ghi vào issue (vẫn theo dõi), không sửa thêm lượt này.
- **UX debt người dùng chấp nhận tạm (vẫn OPEN):** bảng nổi che canvas khi ngang; nhãn rời canvas sau cú xoay ở màn thấp;
  header/thanh công cụ mobile (`ISSUE-ARCH-MOBILE-HEADER-TOOLBAR-LAYOUT`) — nút quay lại chỉ còn mũi tên khi có chip là một
  phần của debt này.
- **Không đổi:** E-R6, F-R7, duyệt hình — vẫn chờ người dùng.
