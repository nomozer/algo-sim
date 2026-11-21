# Fair Planner Comparison Design & Results (`AXO CONSTRUCTION /2`)

## 1. Thiết kế so sánh công bằng 4 nhánh (4-Arm Protocol)

Trong `/1`, `Baseline A` nhận đầu vào quote nguyên bản vốn bị 6 lỗi `Source Gate` do phrasing nhân tạo trong file đánh giá (`B01, B02, B06, B07, B08, C08` + `A10` `"solid_type": "cube"`), đồng thời file đánh giá `/1` chỉ gọi `engine.dung_tu_loi_goi` trực tiếp thay vì toàn tuyến `function_route.run_fact_route`. Thiết kế `/2` tách rõ 4 nhánh trên cùng `40` ca (`seed=0`):

1. **`Arm A1 — Original Product Pipeline`:** chạy trực tiếp `function_route.run_fact_route` trên quote nguyên bản `/1`.
2. **`Arm A2 — Source-Gate-Faithful Product Pipeline`:** giữ nguyên `0` sửa đổi `Source Gate`, `Planner /26`, `Registry /33`, `Engine /24`; chỉ chuẩn hóa diễn đạt `typed-facts/2` trong script đánh giá (`A10`, `B01`, `B02`, `B06`, `B07`, `B08`, `C08`) để tách lỗi trích dẫn đầu vào khỏi năng lực Planner.
3. **`Arm B — Dynamic Planner /1`:** phiên bản khởi đầu (`dynamic-construction-planner/1`).
4. **`Arm C — Dynamic Planner /2 + VerifiedInputBridge`:** phiên bản đã gia cố (`dynamic-construction-planner/2`, `construction-exact-verifier/2`), đo cả **thời gian Planner-only** và **tổng thời gian E2E (`Bridge + Source Gate + Dynamic Search + L0–L4 Replay`)**.

## 2. Kết quả đối chiếu đo thực tế ([FAIR_PLANNER_COMPARISON_RESULTS.json](FAIR_PLANNER_COMPARISON_RESULTS.json))

| Chỉ số đo được | `Arm A1` (Quote gốc `/1`) | `Arm A2` (Input chuẩn Source Gate) | `Arm B` (`/1`) | `Arm C` (`/2` + `VerifiedInputBridge`) |
| --- | --- | --- | --- | --- |
| Dương đúng chính sách `P_strict` | `26/33` | `32/33` *(trượt duy nhất `B09` `IR_MEMORY_BUDGET_EXCEEDED`)* | `33/33` | **`33/33` (`L0`–`L4` Strict Pass)** |
| Tổng 40 ca dưới `P_strict` | `32/40` | `38/40` | `40/40` *(sửa nhãn D02)* | **`40/40`** |
| Tổng 40 ca dưới `P_metric` (`AA=0`) | `33/40` | `39/40` | `39/40` | **`40/40`** *(chọn `point_distance`)* |
| Lỗi `Source Gate` trên ca dương | `6` | `0` | — | **`0` bypass (`VerifiedInputBridge`)** |
| Ca dương có witness phụ **thực sự phi-cạnh** trong `Scene3D` | `1/33` (`C06`) | `2/33` (`C06`, `C08`) | — | **`33/33` (`16/16` implicit aux có đối tượng phụ + `perpendicular_witness` kiểm chứng)** |
| Đa phương án hợp lệ trên `Group E` | `0/33` | `0/33` | — | **`5/5` (`E01`–`E05` đổi Scene3D độc lập)** |
| Độ trễ trung bình (`ms`) | `21.949 ms` | `17.666 ms` | `38.513 ms` *(planner only)* | `65.463 ms` *(planner only)* / `85.641 ms` *(E2E Bridge+Search+L0–L4)* |

## 3. Kết luận công bằng từ 4 nhánh

- Khi cung cấp đầu vào `typed-facts/2` chuẩn `Source Gate`, **`Planner /26` + `Engine /24` hiện hành giải đúng `32/33` ca dương** (nhanh gấp ~3.7x so với tìm kiếm mở rộng ở Planner `/2`).
- Tuy nhiên, kiến trúc cũ (`Arm A2`) vẫn thiếu: (1) không dựng đối tượng phụ tìm được (`H`, đường truyền song song, tia nhị diện) vào `Scene3D` trên `14/16` ca có đối tượng phụ ngầm định (`B03..B05`, `C01..C05`, `C07`, `E01..E05`); (2) không tạo và kiểm chứng được đa phương án dựng hình (`0/33` vs `5/5` ở Group E); (3) đụng trần `MAX_MEMORY_DECLARATIONS = 32` trên chuỗi `B09` (19 bước).
