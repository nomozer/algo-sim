# Evaluation run naming policy

Mọi evaluation run mới dùng định danh ngắn, ổn định, **không có ngày**. Từ 2026-10-05 wave được đánh số **trong
từng việc** (mục *Đánh số wave theo từng việc* dưới đây):

```text
<task-slug>-wNN          wave thứ NN của việc <task-slug>; cũng là tên thư mục run
<task-slug>-<mục-đích>   run không đánh số của việc ấy (vd lượt chốt trước khi merge)
```

Run đặt tên trước đó dùng `wNN-short-slug` (ví dụ `w09-verify-cleanup`, `w10-pedagogical-playback`,
`w11-pedagogical-polish`) và giữ nguyên tên.

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

## Đánh số wave theo từng việc (2026-10-05, run `cuboid-final-review`)

- **Việc** = một mục tiêu làm trên một nhánh riêng. `task-slug` là `lower-kebab-case`, ngắn (≤ 28 ký tự để định danh
  đầy đủ không quá 40), đặt khi tạo nhánh và **không đổi** — kể cả sau khi nhánh đã merge và bị xoá. `RUN.json` ghi
  `task_slug` và `branch`.
- Việc mới trên nhánh mới **bắt đầu ở W1**, rồi W2, W3…; số wave không nối tiếp từ việc trước.
- **Định danh đầy đủ** `<task-slug>-wNN` (hai chữ số, `-w01`) là thứ được ghi vào manifest, `RUN.json`,
  `EVIDENCE_INDEX`, `STATUS_LEDGER`, `CURRENT_STATE`, `OPEN_ISSUES` và mọi chỉ mục — **không bao giờ** `W1`/`W2` trần,
  vì việc nào cũng có W1. Văn xuôi bên trong chính run được viết tắt khi không thể nhầm.
- Tên thư mục run là định danh đầy đủ (ngắn); ngày, nhánh, commit đo, candidate và môi trường ghi trong `RUN.json`,
  không ghi vào tên. Chạy lại cùng một wave: hậu tố `-r1`, `-r2` như trên.
- Nhánh của việc mới **chỉ rẽ từ `main` đã tích hợp và cập nhật**: `git fetch`, `main` trùng `origin/main`, việc trước
  đã merge (hoặc được ghi rõ là bỏ) — không rẽ từ một nhánh tính năng khác.
- Các wave đặt tên trước quy tắc này — **W1–W20**, gồm các thư mục `w09-…` … `w20-…` và các `WAVE_ID` đã commit — giữ
  nguyên tên. Việc đang làm khi quy tắc ra đời có slug `cuboid-visual-semantic-closure` (nhánh
  `fix/cuboid-visual-semantic-closure`); trích các wave của nó ở mục mới bằng `cuboid-visual-semantic-closure-w20` hoặc
  bằng tên thư mục run. Lượt chốt của việc ấy là run `cuboid-final-review`: không đánh số, không bắt đầu lại W1. Việc
  kế tiếp, trên nhánh mới từ `main` đã cập nhật, bắt đầu ở W1.

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
