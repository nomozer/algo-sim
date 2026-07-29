# M17 W3-LIVE-C2 — quyết định mở hay dừng

> ## ✅ ĐÃ CHỐT (2026-07-29): **OPEN_C2 hẹp, MỘT VÒNG DUY NHẤT**
>
> Người quyết: chủ đề tài. Kèm theo đó, ràng buộc *"không sửa `analyze.md`"* của
> C1 được **gỡ riêng cho đúng phạm vi §"Phạm vi chính xác nếu mở C2"** bên dưới —
> không gỡ cho bất cứ file nào khác.
>
> **Điều kiện dừng cứng đi kèm:** rerun xong mà vẫn PARTIAL ⇒ **đóng ở PARTIAL**,
> không mở C3, không vòng thứ hai. Đây là phần không tách rời của quyết định.
>
> C2 chưa được thi hành trong checkpoint preflight này (preflight là READ-ONLY).

## Khuyến nghị ban đầu: **OPEN_C2**, phạm vi rất hẹp — hoặc **ACCEPT_PARTIAL_AND_STOP** nếu
## muốn giữ nguyên luật "không đụng `analyze.md`".

Đây là quyết định của bạn, không phải của tôi, vì lựa chọn đúng phụ thuộc một
ràng buộc do bạn đặt: C1 xếp *"sửa `analyze.md`"* vào stop condition, mà cách sửa
đúng kiến trúc **bắt buộc** phải chạm đúng file đó.

## Đối chiếu với tiêu chí §7

| Điều kiện OPEN_C2 | Đạt? |
|---|---|
| Ngữ nghĩa rõ ràng | **Có** — `prescribed_procedure` = tín hiệu định tuyến/ràng buộc, đã truy vết đủ đường gọi |
| Có phương án nhỏ, tổng quát, fail-closed | **Có** — thêm một khối luật vào `analyze.md` + một lock; **không** đụng cổng, catalog, spec, validator, engine |
| Không cần redesign pipeline | **Có** |
| Không cần family/target mới | **Có** |
| Không cần nhiều vòng correction | **Có** — một khối prompt, một lock, một rerun |
| Giá trị trực tiếp | **Có** — hoàn tất đường NL → mô phỏng đại diện cho ký tự tiếng Việt `U+1EBF`, mảnh bằng chứng luận văn còn thiếu |

Sáu trên sáu. Nhưng hai lý do chính đáng để vẫn chọn **ACCEPT_PARTIAL_AND_STOP**:

1. Chỉ **một** case (Unicode) bị ảnh hưởng; mọi trục an toàn đã bằng **0**, và
   PARTIAL là trạng thái **trung thực, ghi được vào luận văn**.
2. Sửa prompt là sửa hành vi LLM — thứ **không có oracle tất định**. Rerun có thể
   vẫn PARTIAL vì lý do khác, và cám dỗ "vá thêm một vòng" chính là dấu hiệu
   DEEP_HARDENING trong `RULES §3c`.

**Không** khuyến nghị `DOCUMENTATION_ONLY`: implementation đúng, nhưng prompt
contract **thiếu thật** — có 4 giá trị enum không có luật phát. Gọi đó là "chỉ cần
giới hạn claim" là né một lỗi có thật.

## Phạm vi chính xác nếu mở C2

Chỉ được đụng:

1. `backend/app/ai/skills/analyze.md` — **một** khối luật cho họ positional, phát
   biểu theo **hình dạng đầu vào** (ký tự/chuỗi ↔ số), cấm nhắc tên target.
2. Một test lock: mọi giá trị `analyze_exposed_values()` phải có hướng dẫn trong
   `analyze.md` (hiện **4** vi phạm — sửa luôn 3 cái `bounded_control_flow.*`).
3. `CACHE_VERSION` 24 → 25 (chính sách analyze đổi; đúng tiền lệ W2C 20→21).
4. Rerun **đúng 12 lượt**, artifact mới, **không** đè `w3-live-c1/`.
5. Nếu ENC-3 cho candidate hợp lệ: chạy `E2E-ENC-2` bằng adapter **đã có**
   (`capture-w3-live-e2e.mjs` tự nhận case thứ hai, không cần sửa), ≤3 ảnh.

Cấm tuyệt đối: sửa `mechanism_gate.py`, `owned_mechanisms`, `CharacterEncodingSpec`,
validator, engine, renderer, `classify.md`; thêm chain metadata; thêm family/target;
nâng interaction; chạy quá 12 lượt live; mở C3 nếu vẫn PARTIAL.

**Điều kiện dừng cứng:** nếu rerun vẫn PARTIAL → ghi nhận, **đóng ở PARTIAL**,
không vòng ba.

Ước lượng: **2 file production-adjacent** (1 prompt + 1 hằng số), **1 file test**,
~30 phút offline + 12 request live + tối đa 3 ảnh.

## Claim nếu chọn ACCEPT_PARTIAL_AND_STOP

Câu chữ trung thực dùng được ngay trong luận văn:

> Đường phân tích ngôn ngữ tự nhiên → mô phỏng đã được kiểm chứng bằng LLM thật
> trên 6 đề × 2 lượt. Hệ định tuyến đúng **6/6** cho đề mã hoá ký tự và phân biệt
> sạch ký tự với số (2/2). Với đề nêu đồng thời *tra mã* và *đổi sang nhị phân*,
> hệ **từ chối trung thực** thay vì mô phỏng bằng cơ chế sai. Trên toàn bộ lượt
> chạy: không có mô phỏng sai nào được chấp nhận, không bịa dữ kiện, không rò kết
> quả, không rơi về cảnh generic. Một candidate do LLM sinh đã được chứng minh
> chạy qua engine tất định và hiển thị trên trình duyệt, đối chiếu bằng hash.

Kèm giới hạn phải nêu: `U+1EBF` **chưa** kiểm chứng được ở đường live; bằng chứng
là smoke 6 case, không phải benchmark; chưa đánh giá tác động học tập.

## Người học

Không nâng interaction trong cả hai lựa chọn. Pilot người học chỉ nên mở **sau
khi** trạng thái live được chốt (đóng hoặc chấp nhận), luồng đại diện đủ ổn định
để demo, và learner task đã khoá — hiện đã đạt hai điều kiện sau, còn điều kiện
đầu chính là quyết định này.
