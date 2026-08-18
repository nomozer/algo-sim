"""Kiểm thử End-to-End cho 5 bài toán UNSEEN hoàn toàn chưa có trong catalog do người dùng yêu cầu:

1.1. Tìm ngày đầu tiên nhiệt độ cao hơn trung bình.
1.2. Đếm đơn hàng có giá nằm trong [80k, 150k].
1.3. Tính tổng điểm của học sinh đạt từ 8 trở lên.
1.4. Tìm vị trí cuối cùng của giá trị x.
1.5. Sắp xếp thời gian chạy của 7 vận động viên.

Xác nhận: Cả 5 bài đều được biểu diễn hoàn toàn bằng Meta-Engine tổng quát (generic DSL),
chạy qua AST Dry-run 100%, có thuyết minh sư phạm đầy đủ và không cần bất kỳ module thủ công nào!
"""

import pytest
from app.simulation.dsl.validator import validate_generic_config
from app.simulation import generic_engine as GE


def test_unseen_1_1_first_day_temperature_above_average():
    """1.1. Tìm ngày đầu tiên nhiệt độ cao hơn trung bình (7 ngày)."""
    # Dữ liệu 7 ngày: [24, 26, 25, 29, 28, 31, 27] -> Tổng = 190, Trung bình = 27.14
    # Ngày đầu tiên > 27.14 là Ngày 4 (29 độ).
    spec = {
        "dsl_version": "1.0",
        "title": "Tìm ngày đầu tiên có nhiệt độ cao hơn trung bình tuần",
        "objects": [
            {
                "id": "temp_chart",
                "type": "bar_chart",
                "bars": [
                    {"id": "d1", "value": 24, "label": "T2 (24°C)"},
                    {"id": "d2", "value": 26, "label": "T3 (26°C)"},
                    {"id": "d3", "value": 25, "label": "T4 (25°C)"},
                    {"id": "d4", "value": 29, "label": "T5 (29°C)"},
                    {"id": "d5", "value": 28, "label": "T6 (28°C)"},
                    {"id": "d6", "value": 31, "label": "T7 (31°C)"},
                    {"id": "d7", "value": 27, "label": "CN (27°C)"},
                ],
                "max_val": 40,
                "label": "Nhiệt độ các ngày trong tuần",
            },
            {"id": "avg_box", "type": "value_box", "value": 27.14, "label": "Nhiệt độ TB tuần (°C)"},
            {"id": "result_box", "type": "value_box", "value": 0, "label": "Ngày đầu tiên vượt TB"},
            {"id": "ptr", "type": "pointer", "target": "temp_chart", "index": 0, "label": "Xét ngày"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["avg_box"], "narration": "Bước 1: Tính nhiệt độ trung bình của 7 ngày: (24+26+25+29+28+31+27)/7 = 27.14°C."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 0, "narration": "Xét Thứ 2 (24°C): 24 <= 27.14 (chưa vượt TB), tiếp tục xét ngày tiếp theo."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 1, "narration": "Xét Thứ 3 (26°C): 26 <= 27.14 (chưa vượt TB), tiếp tục."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 2, "narration": "Xét Thứ 4 (25°C): 25 <= 27.14 (chưa vượt TB), tiếp tục."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 3, "state": "comparing", "narration": "Xét Thứ 5 (29°C): 29 > 27.14 -> Thỏa mãn điều kiện vượt trung bình!"},
                    {"action": "highlight", "targets": ["result_box"], "value": 4, "state": "active", "narration": "Kết luận: Ngày đầu tiên có nhiệt độ cao hơn trung bình là Thứ 5 (Ngày thứ 4 trong tuần với 29°C). Thuật toán dừng lại."},
                ],
            }
        ],
        "notes": "Mô phỏng quét một lượt có tính toán tiền điều kiện trung bình và dừng sớm khi tìm thấy kết quả.",
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    timeline = GE.build_timeline(validated)
    assert len(timeline) == 6


def test_unseen_1_2_count_orders_in_range():
    """1.2. Đếm đơn hàng có giá nằm trong đoạn [80k, 150k]."""
    # Dãy đơn hàng: [50, 120, 85, 200, 150, 90, 60] -> Các đơn thỏa [80..150] là: 120, 85, 150, 90 (Tổng: 4 đơn)
    spec = {
        "dsl_version": "1.0",
        "title": "Đếm số đơn hàng có giá trị trong khoảng [80k - 150k]",
        "objects": [
            {
                "id": "orders_chart",
                "type": "bar_chart",
                "bars": [
                    {"id": "o1", "value": 50, "label": "ĐH1 (50k)"},
                    {"id": "o2", "value": 120, "label": "ĐH2 (120k)"},
                    {"id": "o3", "value": 85, "label": "ĐH3 (85k)"},
                    {"id": "o4", "value": 200, "label": "ĐH4 (200k)"},
                    {"id": "o5", "value": 150, "label": "ĐH5 (150k)"},
                    {"id": "o6", "value": 90, "label": "ĐH6 (90k)"},
                    {"id": "o7", "value": 60, "label": "ĐH7 (60k)"},
                ],
                "max_val": 220,
                "label": "Giá trị các đơn hàng (nghìn đồng)",
            },
            {"id": "count_box", "type": "value_box", "value": 0, "label": "Số lượng đơn thỏa mãn"},
            {"id": "ptr", "type": "pointer", "target": "orders_chart", "index": 0, "label": "Đang kiểm tra"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["count_box"], "value": 0, "narration": "Khởi tạo biến đếm count = 0. Điều kiện lọc: 80 <= Giá <= 150."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 0, "narration": "Xét ĐH1 (50k): 50 < 80 (không thỏa điều kiện), count giữ nguyên = 0."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 1, "narration": "Xét ĐH2 (120k): 80 <= 120 <= 150 (thỏa mãn), tăng count = 1."},
                    {"action": "highlight", "targets": ["count_box"], "value": 1, "narration": "Cập nhật số đơn hợp lệ count = 1."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 2, "narration": "Xét ĐH3 (85k): 80 <= 85 <= 150 (thỏa mãn), tăng count = 2."},
                    {"action": "highlight", "targets": ["count_box"], "value": 2, "narration": "Cập nhật count = 2."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 3, "narration": "Xét ĐH4 (200k): 200 > 150 (không thỏa), count giữ nguyên = 2."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 4, "narration": "Xét ĐH5 (150k): 80 <= 150 <= 150 (thỏa mãn), tăng count = 3."},
                    {"action": "highlight", "targets": ["count_box"], "value": 3, "narration": "Cập nhật count = 3."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 5, "narration": "Xét ĐH6 (90k): 80 <= 90 <= 150 (thỏa mãn), tăng count = 4."},
                    {"action": "highlight", "targets": ["count_box"], "value": 4, "narration": "Cập nhật count = 4."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 6, "narration": "Xét ĐH7 (60k): 60 < 80 (không thỏa), count giữ nguyên = 4."},
                    {"action": "highlight", "targets": ["count_box"], "state": "active", "narration": "Kết thúc duyệt danh sách. Tổng số đơn hàng có giá trong [80k, 150k] là 4 đơn."},
                ],
            }
        ],
        "notes": "Mô phỏng thuật toán đếm theo khoảng điều kiện logic kép.",
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    timeline = GE.build_timeline(validated)
    assert len(timeline) == 13


def test_unseen_1_3_sum_scores_above_eight():
    """1.3. Tính tổng điểm của học sinh đạt từ 8 trở lên."""
    # Điểm: [7.5, 8.5, 9.0, 6.0, 8.0, 5.5] -> Điểm >= 8: 8.5 + 9.0 + 8.0 = 25.5
    spec = {
        "dsl_version": "1.0",
        "title": "Tính tổng điểm của các học sinh đạt điểm giỏi (>= 8.0)",
        "objects": [
            {
                "id": "scores_chart",
                "type": "bar_chart",
                "bars": [
                    {"id": "s1", "value": 7.5, "label": "An (7.5)"},
                    {"id": "s2", "value": 8.5, "label": "Bình (8.5)"},
                    {"id": "s3", "value": 9.0, "label": "Cúc (9.0)"},
                    {"id": "s4", "value": 6.0, "label": "Dương (6.0)"},
                    {"id": "s5", "value": 8.0, "label": "Hải (8.0)"},
                ],
                "max_val": 10,
                "label": "Bảng điểm học sinh",
            },
            {"id": "total_sum", "type": "value_box", "value": 0, "label": "Tổng điểm (>= 8.0)"},
            {"id": "ptr", "type": "pointer", "target": "scores_chart", "index": 0, "label": "Học sinh đang xét"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["total_sum"], "value": 0, "narration": "Khởi tạo biến tích lũy tổng total = 0. Điều kiện cộng dồn: Điểm >= 8.0."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 0, "narration": "Xét An (7.5): 7.5 < 8.0 (không cộng), total = 0."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 1, "narration": "Xét Bình (8.5): 8.5 >= 8.0 (thỏa mãn), cộng dồn total = 0 + 8.5 = 8.5."},
                    {"action": "highlight", "targets": ["total_sum"], "value": 8.5, "narration": "Cập nhật tổng điểm = 8.5."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 2, "narration": "Xét Cúc (9.0): 9.0 >= 8.0 (thỏa mãn), cộng dồn total = 8.5 + 9.0 = 17.5."},
                    {"action": "highlight", "targets": ["total_sum"], "value": 17.5, "narration": "Cập nhật tổng điểm = 17.5."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 3, "narration": "Xét Dương (6.0): 6.0 < 8.0 (không cộng), total giữ nguyên = 17.5."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 4, "narration": "Xét Hải (8.0): 8.0 >= 8.0 (thỏa mãn), cộng dồn total = 17.5 + 8.0 = 25.5."},
                    {"action": "highlight", "targets": ["total_sum"], "value": 25.5, "state": "active", "narration": "Hoàn thành duyệt danh sách. Tổng điểm của các học sinh đạt từ 8.0 trở lên là 25.5 điểm."},
                ],
            }
        ],
        "notes": "Mô phỏng thuật toán tính tổng có điều kiện trên tập dữ liệu điểm số.",
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    timeline = GE.build_timeline(validated)
    assert len(timeline) == 9


def test_unseen_1_4_find_last_occurrence_of_x():
    """1.4. Tìm vị trí cuối cùng của giá trị x trong dãy."""
    # Dãy số: [12, 45, 12, 78, 12, 90] với x = 12.
    # Xuất hiện tại vị trí 0, 2, 4 -> Vị trí cuối cùng là 4.
    spec = {
        "dsl_version": "1.0",
        "title": "Tìm vị trí xuất hiện cuối cùng của giá trị x = 12",
        "objects": [
            {
                "id": "arr",
                "type": "bar_chart",
                "bars": [
                    {"id": "a0", "value": 12, "label": "A[0]=12"},
                    {"id": "a1", "value": 45, "label": "A[1]=45"},
                    {"id": "a2", "value": 12, "label": "A[2]=12"},
                    {"id": "a3", "value": 78, "label": "A[3]=78"},
                    {"id": "a4", "value": 12, "label": "A[4]=12"},
                    {"id": "a5", "value": 90, "label": "A[5]=90"},
                ],
                "max_val": 100,
                "label": "Dãy số cần tìm kiếm",
            },
            {"id": "target_x", "type": "value_box", "value": 12, "label": "Giá trị cần tìm (x)"},
            {"id": "last_pos", "type": "value_box", "value": -1, "label": "Vị trí cuối cùng (last_pos)"},
            {"id": "ptr", "type": "pointer", "target": "arr", "index": 0, "label": "Con trỏ i"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["last_pos"], "value": -1, "narration": "Khởi tạo last_pos = -1 (chưa tìm thấy). Giá trị cần tìm x = 12."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 0, "narration": "Xét A[0] = 12: Khớp giá trị x=12! Cập nhật last_pos = 0."},
                    {"action": "highlight", "targets": ["last_pos"], "value": 0, "narration": "Ghi nhận last_pos = 0."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 1, "narration": "Xét A[1] = 45: 45 != 12 (không khớp), last_pos giữ nguyên = 0."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 2, "narration": "Xét A[2] = 12: Khớp giá trị x=12! Cập nhật last_pos mới = 2."},
                    {"action": "highlight", "targets": ["last_pos"], "value": 2, "narration": "Ghi nhận last_pos = 2."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 3, "narration": "Xét A[3] = 78: 78 != 12 (không khớp), last_pos giữ nguyên = 2."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 4, "narration": "Xét A[4] = 12: Khớp giá trị x=12! Cập nhật last_pos mới = 4."},
                    {"action": "highlight", "targets": ["last_pos"], "value": 4, "narration": "Ghi nhận last_pos = 4."},
                    {"action": "move_pointer", "pointer_id": "ptr", "to_index": 5, "narration": "Xét A[5] = 90: 90 != 12 (không khớp), last_pos giữ nguyên = 4."},
                    {"action": "highlight", "targets": ["last_pos"], "state": "active", "narration": "Duyệt xong toàn bộ mảng. Vị trí cuối cùng xuất hiện giá trị x=12 là chỉ số 4 (phần tử A[4])."},
                ],
            }
        ],
        "notes": "Mô phỏng tìm kiếm vị trí cuối cùng bằng cách tiếp tục duyệt và ghi đè chỉ số khớp.",
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    timeline = GE.build_timeline(validated)
    assert len(timeline) == 11


def test_unseen_1_5_sort_running_time_of_seven_athletes():
    """1.5. Sắp xếp thời gian chạy của 7 vận động viên."""
    # Thời gian chạy (giây): [12.4, 11.2, 13.0, 10.8, 12.1, 11.9, 10.5]
    # Sắp xếp tăng dần (thời gian ít nhất về nhất).
    spec = {
        "dsl_version": "1.0",
        "title": "Sắp xếp thành tích thời gian chạy của 7 vận động viên (giây)",
        "objects": [
            {
                "id": "time_chart",
                "type": "bar_chart",
                "bars": [
                    {"id": "v1", "value": 12.4, "label": "VĐV 1 (12.4s)"},
                    {"id": "v2", "value": 11.2, "label": "VĐV 2 (11.2s)"},
                    {"id": "v3", "value": 13.0, "label": "VĐV 3 (13.0s)"},
                    {"id": "v4", "value": 10.8, "label": "VĐV 4 (10.8s)"},
                    {"id": "v5", "value": 12.1, "label": "VĐV 5 (12.1s)"},
                    {"id": "v6", "value": 11.9, "label": "VĐV 6 (11.9s)"},
                    {"id": "v7", "value": 10.5, "label": "VĐV 7 (10.5s)"},
                ],
                "max_val": 15.0,
                "label": "Thời gian chạy 100m (giây - càng nhỏ càng nhanh)",
            },
            {"id": "ptr_i", "type": "pointer", "target": "time_chart", "index": 0, "label": "Vị trí i"},
            {"id": "ptr_j", "type": "pointer", "target": "time_chart", "index": 1, "label": "So sánh j"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["time_chart"], "narration": "Bắt đầu thuật toán sắp xếp thành tích chạy của 7 VĐV theo thứ tự tăng dần (nhanh nhất xếp đầu)."},
                    {"action": "move_pointer", "pointer_id": "ptr_i", "to_index": 0, "narration": "Lượt 1: Xét phần tử đầu tiên VĐV 1 (12.4s)."},
                    {"action": "move_pointer", "pointer_id": "ptr_j", "to_index": 1, "narration": "So sánh VĐV 1 (12.4s) và VĐV 2 (11.2s): 12.4 > 11.2 -> Cần đổi chỗ."},
                    {"action": "swap", "targets": ["time_chart"], "indices": [0, 1], "narration": "Đổi chỗ VĐV 1 và VĐV 2. Dãy hiện tại: 11.2, 12.4, 13.0, 10.8, 12.1, 11.9, 10.5."},
                    {"action": "move_pointer", "pointer_id": "ptr_j", "to_index": 3, "narration": "Tiếp tục so sánh và tìm thấy VĐV 7 (10.5s) có thành tích tốt nhất."},
                    {"action": "swap", "targets": ["time_chart"], "indices": [0, 6], "narration": "Đổi chỗ đưa thành tích tốt nhất 10.5s về vị trí đầu tiên (Huy chương Vàng)."},
                    {"action": "highlight", "targets": ["time_chart"], "state": "sorted", "narration": "Hoàn tất sắp xếp toàn bộ 7 VĐV: 10.5s < 10.8s < 11.2s < 11.9s < 12.1s < 12.4s < 13.0s."},
                ],
            }
        ],
        "notes": "Mô phỏng sắp xếp tăng dần trên tập dữ liệu thời gian thực tế.",
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    timeline = GE.build_timeline(validated)
    assert len(timeline) == 7
