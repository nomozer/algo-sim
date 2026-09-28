# Evaluation run naming policy

Mọi evaluation run mới dùng định danh ngắn, ổn định:

```text
YYYYMMDD-wNN-short-slug
```

Ví dụ: `20260928-w09-verify-cleanup`, `20261001-w10-cuboid-acceptance`.

## Quy tắc

- Dùng `lower-kebab-case`; độ dài toàn bộ run ID nên không quá 40 ký tự.
- `short-slug` chỉ mô tả một mục tiêu chính. Không dùng nguyên câu hoặc toàn bộ
  task name làm tên thư mục.
- `wNN` là số wave trong chuỗi đánh giá liên quan. Khi phải lặp cùng một run,
  thêm hậu tố `-r1`, `-r2`, ...; không ghi đè artifact đã commit.
- Full task name, phase, branch, product/candidate/measurement commit SHA và
  thời điểm chạy thuộc về `RUN.json`, không thuộc tên thư mục.
- Các run dài đã commit trước policy này là `LEGACY_LONG_RUN_ID`: không đổi tên,
  không di chuyển, không sửa liên kết lịch sử. Run
  `20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair` là
  một ví dụ được giữ nguyên theo luật này.

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
    desktop/
    mobile/
    formation/
    crops/
  diagnostics/
```

Nếu một nhánh không có artifact (ví dụ không có diagnostics), manifest phải ghi
rõ `NOT_APPLICABLE`; không tạo dữ liệu giả chỉ để lấp thư mục.
