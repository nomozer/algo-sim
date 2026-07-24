# M17 W2B-VR — Failure ledger thị giác `database`

Tìm **7** · sửa **7** · còn chặn **0**

Mọi bản sửa chỉ chạm lớp TRÌNH BÀY — engine trace/executor/spec KHÔNG đổi. Ảnh trước: `visual/database/before/` · sau: `visual/database/after/`.

## VDB-1 — BROKEN_VISUAL · **FIXED**
- **Hiện tượng:** Badge miền lộ 'DATABASE' cho học sinh.
- **Bản sửa:** Thêm ánh xạ domainBadge 'database' → 'TRUY VẤN BẢNG'.
- **Phạm vi:** SimulationWorkspace.tsx (trình bày)

## VDB-2 — BROKEN_VISUAL · **FIXED**
- **Hiện tượng:** Giữ/loại chỉ phân biệt bằng MÀU — không nhãn chữ (§7).
- **Bản sửa:** Thêm cột trạng thái với badge icon SVG + chữ (✓ Giữ / ✕ Loại / ▶ Đang xét / — Không lấy) + viền; icon dùng component (guard ui-hygiene cấm ký tự Unicode).
- **Phạm vi:** table-module.tsx (trình bày)

## VDB-3 — BROKEN_VISUAL · **FIXED**
- **Hiện tượng:** Cột không được chọn mờ NGAY TỪ bước 0, trước giai đoạn chiếu.
- **Bản sửa:** Chỉ mờ cột non-projected SAU khi cursor đã qua bước projection (đọc stagesReached từ trace).
- **Phạm vi:** table-module.tsx (trình bày)

## VDB-4 — BROKEN_VISUAL · **FIXED**
- **Hiện tượng:** Ô trống trong tổng hợp trông Y HỆT hàng được tính → hiểu nhầm ô trống = 0.
- **Bản sửa:** Ô trống hiện '— trống —' in nghiêng; bước tích luỹ nêu rõ 'bỏ qua, không tính là 0'.
- **Phạm vi:** table-module.tsx (trình bày)

## VDB-5 — BROKEN_VISUAL · **FIXED**
- **Hiện tượng:** Sắp xếp KHÔNG quan sát được — bảng luôn giữ thứ tự gốc.
- **Bản sửa:** Sau bước sắp xếp, hiển thị hàng theo thứ tự ĐÃ SẮP (đọc sort.detail.after từ trace); limit hiện hàng bị cắt với nhãn 'Không lấy'. Renderer KHÔNG tự sắp.
- **Phạm vi:** table-module.tsx (trình bày; engine trace không đổi)

## VDB-6 — BROKEN_VISUAL · **FIXED**
- **Hiện tượng:** Tường thuật + panel + Inspector lộ id cột kỹ thuật ('diem_kt', 'diem') thay vì nhãn.
- **Bản sửa:** Renderer dựng tường thuật learner-facing TỪ structured detail + nhãn cột; aggLabel/Inspector dùng nhãn. Engine narration giữ nguyên (chỉ để explain/debug, không hiển thị).
- **Phạm vi:** table-module.tsx (trình bày; engine trace không đổi)

## VDB-7 — BROKEN_VISUAL · **FIXED**
- **Hiện tượng:** Thông báo 'hai truy vấn độc lập' hiện tiêu đề 'CHƯA ĐỦ DỮ KIỆN' — sai bản chất (đề không thiếu dữ kiện, chỉ hỏi hai việc).
- **Bản sửa:** UnsupportedNotice thêm nhánh failure_category='semantic_incomplete' → tiêu đề 'TÁCH THÀNH TỪNG YÊU CẦU'.
- **Phạm vi:** SimulationWorkspace.tsx (trình bày dùng chung)

