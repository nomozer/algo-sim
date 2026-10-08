# Kế hoạch cleanup tài liệu/artifact tiếp nối

1. Đọc 180 báo cáo lịch sử và toàn bộ cây `docs/evaluation` theo file/folder, không suy từ tên hiển thị.
2. Với mỗi nhóm: xác định nội dung, consumer, claim/chương nghiên cứu, giá trị tái lập và hành động.
3. Sửa policy bất biến tuyệt đối thành policy bảo toàn evidence còn dùng; không sửa byte evidence giữ lại.
4. Xoá phần Tin học hết vai trò, đổi tên folder hoạt động khó hiểu, cập nhật consumer/index/test.
5. Chạy docs audit, focused tests, frontend suite/typecheck/build và full gate phù hợp; 0 live call, 0 ảnh mới.

Loại trừ: gỡ prompt, nhánh `semantic_*`, từ vựng IR, đổi guard hình học, model live và chụp mô phỏng.

## Khép hồ sơ chung (2026-10-08)

1. Hợp nhất trách nhiệm của `docs-cleanup-2026-10-08` và `docs-organization` vào bốn tài liệu của chính run này;
   giữ hai manifest đo độc lập và log full-backend dưới tên chức năng, không sửa byte.
2. Xoá hai folder run dư sau khi kiểm consumer; mọi link sống trỏ về `docs-cleanup`, reference trong artifact lịch sử
   giữ nguyên vì mô tả checkout tại thời điểm đo.
3. Audit tên còn lại: đổi tên vật lý khi không buộc sửa byte evidence; ghi ngoại lệ cụ thể cho package tự ghim path.
4. Đối chiếu tag `SEMANTIC_PROGRAM_CONTRACT_V1`, tuyến request → Scene3D và đóng đúng một backend gap đã mở;
   không mở prompt/IR, OCR, UI hay họ hình mới.
5. Vì lý do từ chối API thay đổi, bump cache 117 → 118, relock identity, refreeze candidate sau product commit;
   chạy focused tests rồi full gates trên detached clean worktree.
