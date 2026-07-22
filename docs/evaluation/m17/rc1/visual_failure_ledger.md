# M17-RC1 §E — Failure ledger thị giác

Tìm **3** · sửa **2** · còn chặn **1**

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

## VIS-003 — *(dùng chung)* · BROKEN_VISUAL · **OPEN_BLOCKING**

- **Hiện tượng:** Ở viewport hẹp (768px), panel bên phải KHÔNG xuống dòng mà giữ nguyên cột — workspace bị cắt: tiêu đề, canvas, panel trạng thái, tường thuật và nút 'Đặt lại' đều mất phần bên phải.
- **Bằng chứng:** visual/tree/tree-vietnamese-11-nodes-mid-narrow.png · visual/network/graph-vietnamese-long-labels-mid-narrow.png (và mọi renderer ở viewport hẹp).
- **Nguyên nhân:** Layout hai cột của app shell chưa có điểm ngắt responsive; đây là CSS DÙNG CHUNG, không thuộc renderer nào.
- **Bản sửa:** — (chưa sửa)
- **Phạm vi:** app shell CSS — ảnh hưởng CẢ 6 renderer
- **Vì sao chưa sửa:** Đúng điều kiện dừng §13: 'shared layout fix cần thay đổi kiến trúc lớn'. Sửa điểm ngắt responsive của app shell chạm mọi màn hình (kể cả Home/Library/History ngoài phạm vi §E) và theo §10 phải chụp lại TOÀN BỘ renderer. Báo trước, xin quyết định phạm vi.

