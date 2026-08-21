# Eligibility rubric — định nghĩa population, ĐỘC LẬP với cài đặt

Chốt **2026-08-20, TRƯỚC khi dựng benchmark**. **KHÔNG** tham chiếu Semantic IR.

Tồn tại để phạm vi nghiên cứu thôi tự tham chiếu: nếu population được định nghĩa
bằng "những gì IR biểu diễn được" thì hiện vật đang tự định nghĩa phạm vi của
chính nó, và câu hỏi *"làm sao biết IR không được nắn vừa khít mấy bài đã thử?"*
không có câu trả lời. Ai đọc rubric này cũng phải phân loại được một đề **mà
không cần chạy hệ**.

## In-scope khi thoả TẤT CẢ

1. **Rời rạc, đầu vào hữu hạn.**
2. **Có thủ tục tất định**, execution **hữu hạn / có biên**.
3. **Trạng thái** gồm scalar và cấu trúc dữ liệu rời rạc: dãy/chuỗi · stack ·
   queue · set · map · matrix · tree · graph.
4. **Thao tác** thuộc: gán · so sánh · truy cập · cập nhật · duyệt · push/pop ·
   enqueue/dequeue.
5. **KHÔNG** phụ thuộc solver liên tục, môi trường bên ngoài, hay miền
   phi-thuật-toán.

## Hai trường hợp phải phân biệt

- Không thoả rubric → **NGOÀI population**, không đưa vào benchmark.
- Thoả rubric **nhưng IR hiện tại không diễn đạt được** → **VẪN Ở TRONG
  benchmark**, kết quả `capability_gap`. Đó là **phát hiện phải báo cáo**, không
  phải sự cố cần vá. Sửa IR để cứu nó là phá con dấu (§7.4 của spec).

`expressible_in_ir` trong metadata của mỗi case là **ghi chú MÔ TẢ**, không phải
guard. Nó **không bao giờ** được dùng làm điều kiện loại case, dù trước hay sau
khi thấy hệ chạy.

> **Sửa 2026-08-22.** Trước đó nó bị xếp chung với ba guard held-out và bị bắt
> phải `true`. Làm thế là dùng năng lực hiện tại của IR để chọn population —
> lọc bỏ trước đúng những bài đáng lẽ thành `capability_gap`, khiến tỉ lệ
> executability cao lên một cách giả tạo. Ba guard cứng còn lại
> (`no_specialized_module`, `no_target_template`, `not_prompt_example`) đều nói
> về **nhiễm dữ liệu**, và chỉ loại case vì lý do đó mới hợp lệ.
>
> Khoá bởi `tests/semantic_program/test_sealed_validator.py`:
> `test_expressible_in_ir_FALSE_khong_phai_loi` và
> `test_guard_cung_dung_BA_cai_va_khong_cai_nao_ve_nang_luc_IR`.
