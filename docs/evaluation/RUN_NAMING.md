# Evaluation run naming policy

Mọi evaluation run mới dùng định danh ngắn, ổn định, **không có ngày**:

```text
wNN-short-slug
```

Ví dụ: `w09-verify-cleanup`, `w10-pedagogical-playback`, `w11-pedagogical-polish`.

## Quy tắc

- Dùng `lower-kebab-case`; độ dài toàn bộ run ID nên không quá 40 ký tự.
- `short-slug` chỉ mô tả một mục tiêu chính. Không dùng nguyên câu hoặc toàn bộ
  task name làm tên thư mục.
- `wNN` là số wave trong chuỗi đánh giá liên quan. Khi phải lặp cùng một run,
  thêm hậu tố `-r1`, `-r2`, ...; không ghi đè artifact đã commit.
- Ngày, giờ, full task name, phase, branch, product/candidate/measurement commit
  SHA và môi trường chạy thuộc về `RUN.json`, không thuộc tên thư mục.
- Các run đã commit trước policy này giữ tên cũ (`LEGACY_DATED_RUN_ID` /
  `LEGACY_LONG_RUN_ID`): không đổi tên, không di chuyển, không sửa liên kết lịch
  sử — trừ các ngoại lệ do người dùng quyết ở bảng dưới. Run
  `20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair` là
  một ví dụ được giữ nguyên.

## Đổi tên do người dùng quyết (2026-09-29, wave w11)

| thư mục hiện tại | tên cũ (vẫn là `run_id` trong `RUN.json` của run) |
|---|---|
| `runs/w09-verify-cleanup/` | `20260928-w09-verify-cleanup` |
| `runs/w10-pedagogical-playback/` | `20260928-w10-pedagogical-playback` |

Nội dung hai run giữ nguyên từng byte (534/534 tệp); chỉ đường dẫn đổi. Test và
tài liệu sống trỏ tên mới; báo cáo lịch sử bên trong các run có thể còn nhắc
tên cũ — tra bảng này.

## Cấu trúc chuẩn

```text
<run-id>/
  README.md
  REPORT.md
  HANDOFF.md
  RUN.json
  MANIFEST.json
  inputs/
  results/
  images/
    overview/          # chỉ mục lục, không thay ảnh của từng họ
    <family>/          # contact sheet riêng + ảnh nguồn full-resolution
  diagnostics/         # không bao giờ nằm trong contact sheet nghiệm thu
```

Run không phải run ảnh có thể bỏ `images/`. Nếu một nhánh không có artifact
(ví dụ không có diagnostics), manifest phải ghi rõ `NOT_APPLICABLE`; không tạo
dữ liệu giả chỉ để lấp thư mục.
