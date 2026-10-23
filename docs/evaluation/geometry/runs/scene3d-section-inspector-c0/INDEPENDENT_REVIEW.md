# Review độc lập: C0, R1, F5, nhánh `kd`

Reviewer: subagent Claude, đọc-chỉ (không ghi repo/git, không mạng, không gọi model; probe ở thư mục tạm ngoài repo),
đối chiếu **diff thật và dữ liệu**, không chỉ báo cáo. Reviewer không chạy vitest vì cache của nó sẽ ghi vào
`node_modules` (junction tới root). Vitest do agent chính chạy (Full T3 74/1245).

**Kết luận cuối: vòng 3 `PASS`.**

## Vòng 1: `9978e512..c3916629`: `PASS_WITH_FINDINGS`

Năm luận điểm đều được xác nhận bằng dữ liệu:

1. C0 chỉ tác động khi tra toạ độ nhập nhằng. Không chọn theo thứ tự hay tên. Dữ liệu lăng trụ khớp luật. Không nâng
   provenance. Cạnh và chu trình không đổi. `depends` của sub-entity [] → [I] không gây phụ thuộc sớm.
2. Reviewer quét độc lập 399 lần xuất hiện cảnh có thiết diện trong `docs/` và `frontend/src`: chỉ hai đỉnh lăng trụ
   nhập nhằng.
3. R1 trung thực, kể cả H2/H3 của ca ⊥.
4. F5: đường mã không thể render narration của frames. Không sửa builder dùng chung là hợp lý.
5. `kd` là bắt buộc. Thiếu nó thì Source Gate từ chối `AUXILIARY_RULE_MISMATCH`. Probe cảnh hai thiết diện: SERVED.

| id | mức | phát hiện | xử lý |
|---|---|---|---|
| N1 | MINOR | Phép kiểm trình duyệt F5 chỉ thấy panel mặc định, không đọc `title`/`aria-label`, không bắt narration bị biến đổi ⇒ nhân chứng, không phải chứng minh | tài liệu gọi nó là nhân chứng; bằng chứng là nhánh return sớm. Agent bổ sung negative control |
| N2 | MINOR | Inspector nay hiện "Giao điểm của BB' và (α)" (dấu `'` ASCII) | **sửa** `048d58bd` (test đỏ trước) |
| N2b | MINOR | `source.instruction` của sub-entity viết hoa giữa câu | không sửa: reviewer xác nhận không mã frontend nào render nó |
| N3 | NOTE | Luật không kiểm `producer` của điểm | không làm: lớp trình bày cấm suy kiểu từ `producer` |
| N4 | NOTE | Từ chối `kd` mới thể hiện trên một ca của corpus; tổng quát nhờ cơ chế `khoi_dan_xuat` | chấp nhận |

## Vòng 2: `c3916629..d268c222`: `PASS_WITH_FINDINGS`

N2 đúng: export đổi đúng 16 chuỗi `'` → `′`, `route_d` bằng nhau, freeze đúng.

| id | mức | phát hiện | xử lý |
|---|---|---|---|
| P1 | MINOR | Bước 11 lăng trụ, có hiển thị: "… giao điểm với BB'." do bộ dựng chuỗi thứ hai (`function_route.py:183`) | **sửa** `4d3b8849` (test đỏ trước) |

## Vòng 3: `d268c222..ce2aa0f1`: `PASS`

- P1 đã sửa.
- Quét toàn bộ trường learner-facing của export cuối: không còn tên ghép nào ((MHH1), (MH2H3), (KHH1), HMH1, MII1,
  "qua ba điểm M, H, H1", "Đoạn của thiết diện").
- Còn hai `'` ASCII, có từ trước và không render (ghi chú NOTE): `explanation` dự phòng "Dựng khối ABC.A'B'C' từ 6 đỉnh
  và 5 mặt." và `details.label` "ABC.A'B'C'". Không mã frontend nào đọc `details`.
- Freeze `--verify` MATCH (116 file, `4acdac53…`, product `4d3b8849`). 163 test backend liên quan xanh.

## Lệnh reviewer (tóm tắt)

`git log/diff` (0) · quét JSON tìm đỉnh nhập nhằng (0) · probe phụ thuộc lăng trụ và R1 (0; một lượt đầu exit 1 do lỗi
probe của reviewer) · so sánh export (0) · probe tuyến D offline với audit-hook chặn mạng (0) · `pytest
test_section_display_identity.py test_typedfactnext_planner_bridge.py` (163 passed) · `freeze --verify` (0) · grep
`source.instruction`, `details.label` (không có người dùng) · `git status --porcelain` rỗng.
