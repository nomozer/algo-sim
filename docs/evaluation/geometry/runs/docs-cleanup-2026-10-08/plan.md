# Kế hoạch cleanup tài liệu/artifact tiếp nối

1. Đọc 180 báo cáo lịch sử và toàn bộ cây `docs/evaluation` theo file/folder, không suy từ tên hiển thị.
2. Với mỗi nhóm: xác định nội dung, consumer, claim/chương nghiên cứu, giá trị tái lập và hành động.
3. Sửa policy bất biến tuyệt đối thành policy bảo toàn evidence còn dùng; không sửa byte evidence giữ lại.
4. Xoá phần Tin học hết vai trò, đổi tên folder hoạt động khó hiểu, cập nhật consumer/index/test.
5. Chạy docs audit, focused tests, frontend suite/typecheck/build và full gate phù hợp; 0 live call, 0 ảnh mới.

Loại trừ: gỡ prompt, nhánh `semantic_*`, từ vựng IR, đổi guard hình học, model live và chụp mô phỏng.
