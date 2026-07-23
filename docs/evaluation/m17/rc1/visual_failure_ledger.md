# M17-RC1 §E — Failure ledger thị giác

Tìm **4** · sửa **2** · còn chặn **0**

## VIS-001 — network · BROKEN_VISUAL · **FIXED**

- **Hiện tượng:** Nhãn tiếng Việt dài ĐÈ LÊN nút — chữ bị chính hình tròn cắt ngang.
- **Bằng chứng:** 5 chồng lấn node-label đo trong Chrome, cả desktop lẫn hẹp; ảnh before: visual/before/graph-vietnamese-long-labels-*.png
- **Nguyên nhân:** `<text>` luôn căn giữa TRONG nút r=16 nên nhãn dài tràn hai bên.
- **Bản sửa:** Nhãn dài (>3 ký tự) vẽ DƯỚI nút, giữ id trong nút — cùng quy ước renderer cây; vòng bố cục co lại và canvas cao thêm để đủ chỗ.
- **Phạm vi:** traverse-module.tsx (chỉ trình bày; KHÔNG đụng engine state)

## VIS-002 — generic · BROKEN_VISUAL · **FIXED**

- **Hiện tượng:** Nhãn dài của các đối tượng cùng hàng ngang dồn thành khối chữ không đọc được; badge hiển thị 'GENERIC' cho học sinh.
- **Bằng chứng:** 1 chồng lấn label-label + thuật ngữ GENERIC ở 12/12 capture generic; ảnh before: visual/before/… (chụp trước bản sửa).
- **Nguyên nhân:** Mọi nhãn dùng chung một đường cơ sở; badge lấy thẳng `mod.domain.toUpperCase()`.
- **Bản sửa:** So le đường cơ sở cho nhãn dài (>8 ký tự) theo thứ tự khai báo; badge ánh xạ sang tiếng Việt ('MÔ PHỎNG THEO MÔ TẢ').
- **Phạm vi:** generic/ui.tsx + SimulationWorkspace.tsx (trình bày; engine state.pos KHÔNG đụng)

## VIS-003 — *(dùng chung)* · NOT_A_DEFECT · **NOT_A_DEFECT_MEASUREMENT_ARTEFACT**

- **Hiện tượng:** NGHI NGỜ ban đầu: ở viewport 768px, panel phải không xuống dòng nên workspace bị cắt (tiêu đề, canvas, panel, tường thuật, nút 'Đặt lại').
- **Bằng chứng:** Chẩn đoán DOM THẬT (diagnose-responsive.mjs) trên CẢ 4 route dùng chung app shell, hai viewport: scrollWidth 758 ≤ clientWidth 768 · 0 nút bị cắt · 0 nội dung bị tổ tiên cắt · 0 min-width cứng vượt viewport. before/VIS-003/ và after/VIS-003/ cho cùng kết quả.
- **Nguyên nhân:** LỖI TRONG PHÉP ĐO CỦA TÔI, không phải lỗi sản phẩm: script audit đổi viewport SAU khi trang đã dựng ở 1440px, nên ảnh ra khung 768 nhưng bố cục vẫn của 1440 — trông y hệt bị cắt. App shell THỰC SỰ có responsive đúng.
- **Bản sửa:** Sửa PHÉP ĐO: đặt viewport TRƯỚC rồi mới nạp trang (viewport thành vòng ngoài); bổ sung assertion page_overflow_x, clipped_content (bị tổ tiên cắt), rigid_min_width và key_elements vào audit. KHÔNG đổi một dòng CSS/layout production nào.
- **Phạm vi:** frontend/scripts/visual-stress-audit.mjs (chỉ công cụ đo)
- **Vì sao chưa sửa:** Không có gì để sửa trong sản phẩm. Ghi lại đầy đủ thay vì xoá, vì đây là cảnh báo về chính phương pháp audit: ảnh chụp có thể phản ánh sai hiện thực nếu quy trình đo sai, và tôi đã suýt sửa app shell theo một lỗi không tồn tại.

## VIS-004 — generic · PARTIAL_VISUAL · **FIXED_PARTIAL**

- **Hiện tượng:** Ba nhãn tiếng Việt dài trên cùng một đường ngang vẫn sát nhau sau bản so le HAI hàng của VIS-002.
- **Bằng chứng:** visual/generic/generic-vietnamese-labels-*-*.png (trước bản so le ba hàng).
- **Nguyên nhân:** So le hai hàng ⇒ với ba đối tượng, hai trong số đó vẫn dùng chung một đường cơ sở.
- **Bản sửa:** Nâng lên BA hàng so le và đẩy nhãn RA XA điểm (lên trên khi nhãn ở trên, xuống dưới khi đã lật) nên chữ không chồng marker. Trình bày thuần — `state.pos` không đụng.
- **Phạm vi:** generic/ui.tsx
- **Vì sao chưa sửa:** Vẫn giữ PARTIAL_VISUAL theo §8: nhãn CỰC dài với số đối tượng nhiều hơn số hàng so le thì vẫn chật. Không che nút/trạng thái, không làm sai cơ chế ⇒ không chặn.

