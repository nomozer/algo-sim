# SIMULATION_GOAL_SEMANTICS_REPORT (`AXO HYBRID /12` P7 §17)

## 1. Phạm vi & Ranh giới Sở hữu (`A4`)

- Các module `backend/app/simulation/geometry_functions/planner.py` và `backend/app/simulation/geometry_functions/engine.py` **được giữ khóa (`0` diff)** trong chiến dịch AXO HYBRID /12 theo `OWNERSHIP_MATRIX.md` (`A4`).
- Tài liệu và bộ kiểm thử `backend/tests/geometry/test_v12_similarity_semantics_handoff.py` ghi nhận hành vi hiện hành và hợp đồng bàn giao (handoff specification) cho nhóm phụ trách `planner.py` / `engine.py`.

## 2. Kết quả Xác minh Hành vi Hiện hành trên Nhóm `D01..D05`

| Case | Đề bài | Parser (`local-geometry-parser/3`) | Trạng thái Kernel Hiện hành | Mã từ chối | Phân tích |
| --- | --- | --- | --- | --- | --- |
| `D01` | Hãy mô phỏng hình chóp S.ABCD có đáy ABCD là hình vuông và SA vuông góc với đáy. | `LOCAL_PARSE_AMBIGUOUS` | `AMBIGUOUS_FACT` | `AMBIGUOUS_FACT` | Chưa có số đo cạnh đáy và chiều cao `SA`; không xác định duy nhất tỷ lệ hình dạng. |
| `D02` | Vẽ hình lập phương ABCD.A'B'C'D'. | `LOCAL_PARSE_COMPLETE` | `REFUSED` (`kernel`) | `MISSING_DIMENSION` | Đồng dạng 1-tham số (tỷ lệ thuần), hiện bị engine từ chối vì `regular_polygon` đáy chưa có độ dài cạnh. |
| `D03` | Dựng hình tứ diện đều ABCD. | `LOCAL_PARSE_COMPLETE` | `REFUSED` (`kernel`) | `MISSING_DIMENSION` | Đồng dạng 1-tham số (tỷ lệ thuần), hiện bị engine từ chối vì `regular_polygon` đáy chưa có độ dài cạnh. |
| `D04` | Mô phỏng hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều. | `LOCAL_PARSE_AMBIGUOUS` | `AMBIGUOUS_FACT` | `AMBIGUOUS_FACT` | Thiếu tỷ lệ giữa cạnh đáy và chiều cao. |
| `D05` | Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với (ABC). Hãy vẽ hình. | `LOCAL_PARSE_COMPLETE` | `REFUSED` (`kernel`) | `MISSING_DIMENSION` | Thiếu độ dài ba cạnh/góc xác định hình dạng. |

## 3. Đặc tả Bàn giao Tương lai (ngoài `/12`)

1. Nếu sản phẩm phê duyệt chính sách *unit-similarity representative* chỉ cho intent `SIMULATE_ONLY` trên họ đồng dạng 1-tham số (`D02` lập phương, `D03` tứ diện đều):
   - Chỉ kích hoạt khi `len(math_goals) == 0` **và** mọi `simulation_goals` đều không đòi hỏi số đo tuyệt đối (`construct_object`).
   - Bắt buộc gắn metadata `scale_policy = "UNIT_SIMILARITY_REPRESENTATIVE"` và nhãn hiển thị trong `Scene3D` rõ đây là mô hình đại diện theo tỷ lệ, **tuyệt đối không** cho phép trả kết quả số cho `volume` / `segment_length` / `area` / `distance` (kiểm chứng trong `test_v12_metric_goal_on_unitless_cube_stays_fail_closed` vẫn phải trả `REFUSED / MISSING_DIMENSION`).
2. Các case thiếu nhiều bậc tự do (`D01`, `D04`, `D05`) giữ nguyên fail-closed (`AMBIGUOUS_FACT` / `MISSING_DIMENSION`) để tránh bịa giả thiết hình học.
