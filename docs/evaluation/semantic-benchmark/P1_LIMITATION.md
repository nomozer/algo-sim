# Giới hạn P1 — khai tường minh, không lấp liếm

Ngày: 2026-08-20 (Task 7) · Trạng thái: **CÒN HỞ CÓ CHỦ ĐÍCH**

## Chuỗi provenance hai đoạn

```
Original problem text
        │
        │  P1   ← CÒN HỞ
        ▼
RequestContract input fact   (id, label, values)
        │
        │  P2   ← ĐÃ ĐÓNG
        ▼
SemanticProgram declaration  (initial_value, source_fact_id)
```

## P2 — đã đóng, kiểm tất định

`semantic_input_grounding_gate` đòi mỗi `initial_value` **không phải hạt khởi
tạo** phải khai `source_fact_id`, và kiểm:

- mục dữ liệu đó **tồn tại** trong `RequestContract`;
- mọi giá trị khai đều **có trong mục ĐƯỢC CHỈ ĐÍCH DANH**.

Cố ý **không** làm kiểu *"tìm xem giá trị này có xuất hiện đâu đó trong hợp đồng
không"*. Khớp theo giá trị đơn thuần cho qua cả trường hợp **khai sai nguồn** —
`test_tham_chieu_NHAM_muc_du_gia_tri_co_trong_hop_dong_thi_van_fail` khoá đúng
điểm này.

## P1 — còn hở, và đây là kịch bản cụ thể

```
Đề thật:            "tìm max của 4, 7, 2"
analyze bịa:        input_fact I1 = [4, 7, 2, 9]
IR khai:            initial_value = [4,7,2,9], source_fact_id = "I1"
P2:                 PASS  ← tham chiếu đúng, giá trị khớp mục
```

Giá trị `9` không có trong đề, nhưng nó **có** trong hợp đồng, và IR **ghim
đúng** mục chứa nó. P2 không thể phát hiện — lỗi nằm ở đoạn trên.

## Hệ quả với cách phát biểu

> **KHÔNG được tuyên bố `semantic_input_grounding_gate` đã diệt mọi
> hallucination của `analyze`.**

Nó là điều kiện **CẦN, CHƯA ĐỦ**: đóng hoàn toàn P2, **thu hẹp chứ không đóng**
P1.

Cách phát biểu đúng:

> *Mọi dữ liệu chương trình dùng đều truy được về một mục dữ liệu mà `analyze`
> đã khai. Việc mục dữ liệu đó có trung thành với đề gốc hay không thì chưa
> được kiểm tất định trong wave này.*

## Đóng P1 cần gì — và vì sao KHÔNG làm bây giờ

Cần một trong ba: `source_span` (vị trí ký tự trong đề gốc) · vị trí nguồn có
cấu trúc · bằng chứng từ extractor tất định.

**Không làm ở Task 7** vì nó là một dự án provenance riêng, và ranh giới 5 của
§1.1 cấm mở tối ưu phụ. Ghi vào `POST_THESIS_BACKLOG.md` nếu muốn theo tiếp.
