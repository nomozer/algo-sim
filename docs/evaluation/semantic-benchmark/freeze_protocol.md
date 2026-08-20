# Freeze protocol

## Đóng băng TRƯỚC khi seal — không sửa về sau

- eligibility rubric (`eligibility_rubric.md`)
- **N** và cách lấy mẫu
- primary metrics — **A và B ĐỒNG-primary**
- assurance policy (thanh STRONG/WEAK cố định)
- ground-truth procedure
- cách tính refusal / success
- các trường hợp bị loại khỏi thống kê
- obligation taxonomy (chọn từ **DEV**)

## Không đặt pass mark tuỳ tiện

**KHÔNG** ghi kiểu *"≥80% thì luận văn thành công"* khi chưa có cơ sở nào để
chọn con số đó. Luận văn **báo kết quả như nó là**. Thứ phải đóng băng là **CÁCH
ĐO**, không phải mức điểm mong muốn.

## Release cho học sinh — tiêu chuẩn KHÁC

Canonical case **biết là sai** → **FAIL RELEASE**. Tuyệt đối **không** hạ thanh
assurance để tỉ lệ đẹp hơn.

## Hai chỉ số báo riêng

```
Generative executability rate   ≠   Safe serve rate
```

A hỏi *kiến trúc có thoát module-per-problem không*; B hỏi *bao nhiêu trong số
đó đủ bằng chứng để sản phẩm thật sự dùng được*. Khoảng cách A − B là chỗ đáng
phân tích, không phải chỗ để giấu.

## Chống rủi ro safe-serve ≈ 0 — làm trên DEV, TRƯỚC seal

Thống kê các **lớp nghĩa vụ thực tế** xuất hiện trong bài thuật toán THPT, chọn
một tập checker **nhỏ, đại diện**, rồi **đóng băng taxonomy trước SEALED**.
**Không** thêm checker để cứu từng held-out case.
