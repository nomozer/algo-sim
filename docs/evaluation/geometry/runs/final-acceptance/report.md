# final-acceptance — báo cáo (nghiệm thu cuối trước khi tích hợp `main`)

Việc: kiểm lại danh tính và bằng chứng của nhánh `feat/regular-square-pyramid`, đo phần báo cáo trước bỏ sót (dải lớp học ở
640 px), chuẩn bị bản chạy cho thao tác tay trên điện thoại (E-R6, F-R7). **Không sửa sản phẩm**, 0 lượt gọi model, không đo
lại bộ ảnh. Trạng thái: `READY_FOR_USER_ACCEPTANCE` — chờ quyết định của người dùng; run này không ghi `APPROVED_BY_USER`.

## 1. Danh tính và bằng chứng — khớp, không đo lại

| Mục | Kiểm | Kết quả |
|---|---|---|
| HEAD | `bc989cd2` trên `feat/regular-square-pyramid`; `main` = `38d41588` là tổ tiên (161 commit trước) | khớp |
| Sản phẩm | `git diff 95a56a17 HEAD` ngoài `docs/`: chỉ `frontend/scripts/generic-tier-a-scenarios.json` (`product_commit_sha` d8ad153b → 95a56a17, `5892fefd`); `frontend/src`, `backend/app` trùng `95a56a17`; cây làm việc chỉ có `D frontend/public/favicon.svg` của người dùng | không có thay đổi sản phẩm chưa kiểm |
| Candidate | `freeze_evaluation_candidate.py --verify` | `7f3f0423…`, 102 file, khớp |
| Cache / chế độ | `CACHE_VERSION = "118"` (`main.py:783`); `CHE_DO_MAC_DINH = "LLM_ONLY"`; test candidate + schema sync + bảng danh tính | 18/18 pass |
| Tier-A | `runs/phone-landscape-layout/results/BROWSER_EVIDENCE.json`: product `95a56a17`, cây `7f3f0423…`, đo `221ec0a0` | 8/8 trong một lượt |
| T3 | `runs/phone-landscape-layout/diagnostics/t3_d32bdb8d.log` tại `d32bdb8d` (sau đó chỉ docs) | `FULL_PRODUCT_GATE_PASS`: pytest 7239 passed / 1 skipped / 2 deselected; vitest 67 file / 1034 |

Kết luận: bằng chứng của `phone-landscape-layout` thuộc đúng phiên bản cuối; không có căn cứ đo lại.

## 2. Dải lớp học trong hàng trên (`daiLop`) — lỗi thật, có từ `main`

Đầu dò mới, bỏ đi sau run (`diagnostics/probe-class-band.mjs`, API giả qua CDP, 0 model): giáo viên chưa/đang dạy, học sinh
trong tiết; tám khổ. Cửa sổ chứng: không có dải (người dùng `null`), cùng họ hình, đầu dò chính thức đo hàng trên 36–44 px và
điều khiển trong khung ở mọi khổ ngang.

| Bản dựng | Đạt | Lỗi |
|---|---|---|
| nhánh (`95a56a17`) | **11/24** | điều khiển phát ngoài khung: 640×360, 667×375, 844×340 cả ba vai; 844×390 giáo viên đang dạy; 360×640 cả ba vai |
| `main` (`38d41588`) | **5/24** | như trên + 844×390 mọi vai, 1366×650 giáo viên đang dạy; cuộn ngang ở 360/390 px dọc (và giáo viên ở 640×360) |

Không dòng nào đạt ở `main` mà trượt ở nhánh ⇒ **không hồi quy**; nhánh bớt lỗi (hết cuộn ngang). Nguyên nhân
(`results/CLASS_BAND_PROBE.json`, `children`): khối ngang thấp ép hàng trên một dòng (`.geo3d-thanh { flex-wrap: nowrap }`,
`95a56a17`) nhưng nhóm công cụ `.geo3d-thanh-nut` vẫn được xuống dòng bên trong, còn tên bài `min-width: 0`. Dải lớp (nhãn bài
≤ 260 px, «Giao cho lớp», bảng điều khiển lớp) chiếm chỗ ⇒ tên bài co về **0 px** (mất hẳn), bốn nút công cụ xếp dọc, hàng trên
cao 148–224 px, canvas và cột điều khiển bị đẩy xuống dưới mép (`images/class-band__student__640x360.png`). Ở khổ dọc hẹp,
hàng trên được xuống dòng, dải lớp thêm 1–2 hàng (262–384 px) ⇒ thanh phát dưới mép 360×640.

Đề xuất sửa tối thiểu (chưa làm, chưa đo): trong khối `(orientation: landscape) and (max-height: 30rem)` giữ nhóm công cụ một
dòng (`.geo3d-thanh-nut { flex-wrap: nowrap; flex-shrink: 0 }`), cho tên bài một sàn (`min-width: 5rem`) và để nhãn bài co trước
(`.nav-assignment { flex: 0 1 auto; min-width: 0 }`); bảng điều khiển lớp của giáo viên dùng trạng thái thu gọn đã có
(`live-dock-thu`, một chạm mở) làm mặc định ở khổ ≤ 48rem. Không redesign; đo lại bằng chính đầu dò này + bộ đo điện thoại.
Issue: `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW`.

## 3. E-R6 / F-R7 — hỗ trợ tự động, KHÔNG thay thao tác tay

`diagnostics/probe-touch.mjs`: chạm giả lập (`Input.dispatchTouchEvent`, Chrome headless, DPR 2) — 2 họ (chóp tứ giác đều,
thiết diện) × 4 khổ (390×844, 360×640, 844×390, 640×360): **8/8** — kéo một ngón xoay camera không cuộn trang; chạm «Xem lại
toàn hình» trả đúng camera; «Bước sau»/«Bước trước»; Phát rồi Tạm dừng (bước đứng yên sau 1,5 s); chạm hình chọn được thành phần;
mở/thu gọn/mở rộng/đóng «Các bước dựng»; kéo bảng nổi bằng ngón tay (khổ ngang). Lần chạy đầu 0/8 do lỗi của đầu dò (cảnh mở ở
bước 1, «Bước trước» không làm gì) — đã sửa đầu dò, chạy lại cùng bản dựng. Xoay máy giữ bước/lựa chọn/camera đã đo 40/40 ở
`phone-landscape-layout`. Chạm giả lập không chứng minh cảm ứng thật, cử chỉ hai ngón, thanh trình duyệt co giãn, bàn phím ảo hay
vùng an toàn ⇒ E-R6, F-R7 vẫn `REQUIRES_INTERACTIVE_HUMAN_CHECK` (`review.md`).

## 4. Bốn cảnh W14 (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`)

Tự động (đã có, candidate cuối, `runs/phone-landscape-layout/results/OCCLUSION_MEASUREMENT.json`): 0 lỗi; với chóp tam giác,
lăng trụ tam giác, chóp tứ giác, thiết diện — oracle độc lập tái tạo đúng tập khuất/hiện đã duyệt ở camera đăng ký và camera mới
(`REVIEWED_SETS_REPRODUCED` 4/4), sản phẩm = oracle ở mọi trạng thái. Cần người: nhìn bốn ảnh và xác nhận nét đứt/liền đúng như
người học mong đợi; một lớp registry đã duyệt mới (người dùng ghi). Người dùng đã chấp nhận nhóm C bằng mắt ngày 2026-10-05
(`runs/cuboid-merge/APPROVAL.md`); issue vẫn mở vì chưa có registry, `default_switch_blocker: NO`.

## 5. UX debt người dùng chấp nhận tạm (2026-10-09) — vẫn OPEN

Bảng nổi che một phần canvas khi điện thoại ngang (`ISSUE-ARCH-LANDSCAPE-FLOATING-PANEL-COVERS-CANVAS`); nhãn rời canvas sau cú
xoay ở màn thấp, «Xem lại toàn hình» khôi phục (`ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`); bố cục header/thanh công cụ
mobile chưa đẹp (`ISSUE-ARCH-MOBILE-HEADER-TOOLBAR-LAYOUT`). Hoãn sửa ≠ duyệt: trạng thái các issue không đổi thành RESOLVED.

## 6. Giới hạn

Không sửa sản phẩm, không đổi candidate/cache, không chụp lại bộ ảnh (1 ảnh mới cho lỗi mới). Hai đầu dò là công cụ một lần,
không vào T3. Không merge, push, PR, xoá nhánh.
