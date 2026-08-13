# CLASSROOM_AUTH_CONTRACT.md — LUẬT CÒN HIỆU LỰC

> Đây là `*_CONTRACT.md`: **luật đang áp dụng**, không phải bằng chứng đông
> cứng của một wave. Sửa tầng tài khoản/lớp học thì mở file này trước.
> Số sống (đếm test, số target) ở `docs/CURRENT_STATE.md`.

## 0. Ranh giới — tầng này KHÔNG được lớn thêm

AlgoSim là **hệ mô phỏng tương tác**. Tầng lớp học tồn tại để hỗ trợ đúng việc
đó và **dừng ở đây**:

```
TÀI KHOẢN · VAI TRÒ · LỚP · MÃ VÀO LỚP · GIAO MÔ PHỎNG
· HỌC SINH THỰC HÀNH · GIÁO VIÊN QUAN SÁT · TIẾP TỤC Ở NHÀ
```

**KHÔNG** sổ điểm · **KHÔNG** điểm danh · **KHÔNG** thời khoá biểu · **KHÔNG**
học phí · **KHÔNG** diễn đàn · **KHÔNG** trình dựng khoá học. Một yêu cầu rơi
vào danh sách ấy là `OUT_OF_SCOPE` theo `RULES.md §3` — dừng và hỏi.

## 1. Ai sở hữu cái gì

| Câu hỏi | Chủ sở hữu |
|---|---|
| Ai đang gọi | `auth_sessions` (token đục trong bảng) |
| Vai trò | cột `users.role` — **SERVER**, không đọc từ request |
| Được làm gì | `accounts/policy.py::entitlement_for` (hàm thuần) |
| Lớp của ai | `classrooms.teacher_id` + `class_memberships` |
| Mô phỏng chạy thế nào | **engine tất định** — tầng này không đụng tới |
| Học sinh đúng hay sai | **engine tất định**, `predict.check`. Tầng này KHÔNG BAO GIỜ |

## 2. Bất biến

1. **Vai trò do máy chủ quyết.** `POST /api/auth/register` nhận trường `role`
   nhưng KHÔNG tin nó: `resolve_signup_role` trả `student` trừ khi trình đúng mã
   mời. Không cấu hình mã ⇒ đường giáo viên ĐÓNG (fail-closed).
2. **Mật khẩu không bao giờ rời tầng lưu trữ.** Không vào response, không vào
   log. PBKDF2-HMAC-SHA256, salt riêng từng tài khoản, so constant-time.
3. **Mã lớp là LỜI MỜI, không phải chứng chỉ.** Vào lớp vẫn phải đăng nhập
   trước. Mã lộ ⇒ người lạ vào lớp, KHÔNG phải người lạ mạo danh học sinh.
   Mã thu hồi/sinh lại được, và mã cũ chết ngay.
4. **Giáo viên chỉ thấy lớp MÌNH sở hữu; học sinh chỉ thấy lớp mình đã vào.**
   "Là giáo viên" không đủ để quan sát một lớp bất kỳ.
5. **Giao bài = giao envelope ĐÃ VALIDATE.** Đi qua đúng `SimSpec.validate` mà
   pipeline LLM đi. Chữ của giáo viên là CHỮ, không bao giờ là tham số.
   Mở bài KHÔNG gọi LLM — ba mươi học sinh mở ra một mô phỏng, không phải ba mươi.
6. **Quan sát bằng trạng thái CÓ CẤU TRÚC.** Không chiếu màn hình, không chụp
   DOM. Các trường đọc qua hợp đồng `timeline` của module, không đọc renderer.
7. **Không trường đúng/sai nào trong tầng lớp học.** Bảng quan sát nói học sinh
   đang ở đâu, không nói em ấy làm đúng chưa.
8. **Khách có ĐÚNG một lượt mô phỏng thật**, đếm ở phiên máy chủ. Lượt chỉ tính
   khi mô phỏng RA ĐƯỢC — đề bị từ chối trung thực không ăn mất lượt.

## 3. Giới hạn đã biết — khai, không giấu

- **Xác minh giáo viên: PARTIAL.** `ALGOSIM_TEACHER_SIGNUP_CODE` là **mã mời
  dùng chung**. Nó chặn việc tự nâng quyền bằng cách sửa một trường JSON; nó
  KHÔNG chặn được người đã biết mã. Hệ xác minh thật (trường cấp / quản trị
  duyệt) chưa có.
- **Giáo viên cấp tài khoản cho học sinh: MISSING.** Chỉ có đường học sinh tự
  đăng ký rồi vào lớp bằng mã. Không dựng nửa vời: cấp tài khoản an toàn cần
  đường trao mật khẩu tạm và bắt đổi lần đầu — cột `must_change_password` đã có
  sẵn cho việc đó, luồng thì chưa.
- **Lượt thử của khách chống được xoá localStorage, KHÔNG chống được xoá
  cookie.** Đó là giới hạn cố hữu của phiên ẩn danh; khoá bằng test để hành vi
  không âm thầm đổi.
- **Quan sát là gần-thời-gian-thực (5 giây), không phải tức thời.** Repo không
  có websocket/SSE và một bảng đổi vài giây một lần không đáng dựng nó.

## 4. Vận hành

```bash
# bảng: Postgres do Alembic sở hữu (bất biến #19)
cd backend && .venv/Scripts/python.exe -m alembic upgrade head

# mở đăng ký tài khoản giáo viên (không đặt = đóng)
ALGOSIM_TEACHER_SIGNUP_CODE=<mã do trường cấp>

# dữ liệu demo cho nghiệm thu (mật khẩu từ env, không có mặc định trong mã)
ALGOSIM_FIXTURE_PASSWORD=<...> .venv/Scripts/python.exe scripts/seed_classroom_fixture.py
```

⚠️ **Container Docker cũ có thể chiếm cổng 8000** và trả 404 cho mọi endpoint
mới, làm mọi phép nghiệm thu vô nghĩa. `accept-classroom-m18.mjs` kiểm danh
tính backend trước khi tin kết quả; nếu chạy tay thì `docker compose stop
backend` trước.
