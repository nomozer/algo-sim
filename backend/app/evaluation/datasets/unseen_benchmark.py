# -*- coding: utf-8 -*-
"""UNSEEN_GENERATION_BENCHMARK (40 bài toán thực tế GDPT 2018).

Bộ benchmark đánh giá năng lực tự sinh mô phỏng (Generative Simulation) của Universal Meta-Engine
(`generic.rule_scene`) KHÔNG sử dụng bất kỳ module chuyên biệt nào.

5 Nhóm chủ đề:
1. Thuật toán quét, tìm kiếm & tích luỹ (8 bài)
2. Thuật toán sắp xếp & hoán đổi trực quan (8 bài)
3. Cấu trúc dữ liệu động (Ngăn xếp, Hàng đợi, Cây nhị phân) (8 bài)
4. Số học nhị phân, Mạch logic & Mô hình tham số (8 bài)
5. Cơ sở dữ liệu, Bảng 2 chiều & Ma trận (8 bài)
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UnseenBenchmarkItem:
    id: str
    prompt: str
    category: str
    archetype: str
    expected_primitives: tuple[str, ...]
    learning_objective: str
    pedagogical_trace_action: str
    data_missing_mode: str = "PROVIDED"  # PROVIDED | GENERATED_EXAMPLE


UNSEEN_BENCHMARK_ITEMS: list[UnseenBenchmarkItem] = [
    # ── NHÓM 1: Quét, tìm kiếm & tích luỹ (8 bài) ──────────────────────────
    UnseenBenchmarkItem(
        id="unseen-temp-avg",
        prompt="Cho nhiệt độ 7 ngày trong tuần [24, 26, 25, 29, 28, 31, 27]. Tìm ngày đầu tiên có nhiệt độ cao hơn nhiệt độ trung bình cả tuần.",
        category="algorithms_sequential",
        archetype="scan_average_threshold",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Hiểu cơ chế tính toán giá trị trung bình làm tiền điều kiện lọc và quét dừng sớm.",
        pedagogical_trace_action="move_pointer",
    ),
    UnseenBenchmarkItem(
        id="unseen-order-range",
        prompt="Đếm số lượng đơn hàng có giá trị nằm trong khoảng từ 80k đến 150k trong danh sách các đơn hàng đã đặt.",
        category="algorithms_sequential",
        archetype="range_counting",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Nắm vững thuật toán đếm phần tử thỏa mãn điều kiện kép a <= x <= b.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-score-sum",
        prompt="Tính tổng điểm của tất cả học sinh đạt điểm giỏi (từ 8.0 trở lên) trong danh sách điểm kiểm tra.",
        category="algorithms_sequential",
        archetype="conditional_accumulator",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Hiểu rõ biến tích lũy tổng chỉ cộng dồn khi phần tử thỏa điều kiện lọc.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-last-x",
        prompt="Cho dãy số nguyên A. Tìm vị trí xuất hiện cuối cùng của giá trị x trong dãy, nếu không có trả về -1.",
        category="algorithms_sequential",
        archetype="last_occurrence_search",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Phân biệt tìm kiếm phần tử đầu tiên (dừng sớm) và tìm phần tử cuối cùng (duyệt hết dãy ghi đè).",
        pedagogical_trace_action="move_pointer",
    ),
    UnseenBenchmarkItem(
        id="unseen-neg-first",
        prompt="Tìm vị trí của số âm đầu tiên trong mảng các số nguyên đã cho.",
        category="algorithms_sequential",
        archetype="first_negative_search",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Mô phỏng điều kiện dừng sớm khi gặp phần tử thỏa mãn tính chất x < 0.",
        pedagogical_trace_action="move_pointer",
    ),
    UnseenBenchmarkItem(
        id="unseen-even-count",
        prompt="Đếm có bao nhiêu số chẵn lớn hơn 50 trong một danh sách số nguyên.",
        category="algorithms_sequential",
        archetype="even_threshold_count",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Kết hợp điều kiện chia hết (x % 2 == 0) và so sánh ngưỡng (x > 50).",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-peak-val",
        prompt="Tìm mức tiêu thụ điện cao nhất trong các tháng và kiểm tra xem có tháng nào vượt ngưỡng cảnh báo 400kWh không.",
        category="algorithms_sequential",
        archetype="peak_threshold_scan",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Theo dõi giá trị lớn nhất cực biên kết hợp kiểm tra ngưỡng an toàn.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-min-diff",
        prompt="Tìm phần tử trong dãy có giá trị gần nhất với số mục tiêu T cho trước (độ chênh lệch trị tuyệt đối nhỏ nhất).",
        category="algorithms_sequential",
        archetype="minimum_difference_scan",
        expected_primitives=("bar_chart", "value_box", "pointer"),
        learning_objective="Cập nhật giá trị tối ưu theo hàm khoảng cách tuyệt đối |A[i] - T|.",
        pedagogical_trace_action="move_pointer",
    ),

    # ── NHÓM 2: Sắp xếp, hoán đổi & xếp hạng (8 bài) ────────────────────────
    UnseenBenchmarkItem(
        id="unseen-runner-sort",
        prompt="Sắp xếp thời gian chạy 100m của 7 vận động viên theo thứ tự tăng dần (nhanh nhất xếp đầu).",
        category="algorithms_sorting",
        archetype="sorting_swap",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Quan sát cơ chế so sánh từng cặp và hoán đổi vị trí để đưa phần tử nhỏ nhất lên đầu.",
        pedagogical_trace_action="swap",
    ),
    UnseenBenchmarkItem(
        id="unseen-score-rank",
        prompt="Xếp hạng điểm thi tốt nghiệp của 6 học sinh từ cao nhất đến thấp nhất (giảm dần).",
        category="algorithms_sorting",
        archetype="sorting_descending",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Nắm vững sự đảo ngược của điều kiện so sánh khi sắp xếp giảm dần.",
        pedagogical_trace_action="swap",
    ),
    UnseenBenchmarkItem(
        id="unseen-height-line",
        prompt="Mô phỏng sắp xếp chiều cao của 8 học sinh đứng thành hàng dọc từ thấp đến cao.",
        category="algorithms_sorting",
        archetype="sorting_height",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Hiểu trực quan hóa dãy cột chiều cao tương ứng với vị trí thực tế của học sinh.",
        pedagogical_trace_action="swap",
    ),
    UnseenBenchmarkItem(
        id="unseen-price-asc",
        prompt="Sắp xếp danh sách giá các mặt hàng trong siêu thị theo thứ tự tăng dần.",
        category="algorithms_sorting",
        archetype="sorting_price",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Mô phỏng sắp xếp dữ liệu giá trị tài chính trong thực tiễn.",
        pedagogical_trace_action="swap",
    ),
    UnseenBenchmarkItem(
        id="unseen-file-size",
        prompt="Sắp xếp dung lượng các tệp tải về từ nhỏ nhất đến lớn nhất để giải phóng bộ nhớ.",
        category="algorithms_sorting",
        archetype="sorting_files",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Hiểu vai trò của thuật toán sắp xếp trong quản trị hệ điều hành.",
        pedagogical_trace_action="swap",
    ),
    UnseenBenchmarkItem(
        id="unseen-temp-sort",
        prompt="Sắp xếp nhiệt độ cao nhất ghi nhận được của các ngày trong tuần theo thứ tự tăng dần.",
        category="algorithms_sorting",
        archetype="sorting_temp",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Rèn luyện kỹ năng phân tích diễn biến sắp xếp trên dãy số liệu khí tượng.",
        pedagogical_trace_action="swap",
    ),
    UnseenBenchmarkItem(
        id="unseen-alphabet-rank",
        prompt="Sắp xếp danh sách điểm đánh giá của các chi nhánh công ty theo thứ tự thành tích.",
        category="algorithms_sorting",
        archetype="sorting_ranking",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Quan sát trạng thái đang so sánh (cam), hoán đổi (tím) và đã xếp xong (xanh lá).",
        pedagogical_trace_action="swap",
    ),
    UnseenBenchmarkItem(
        id="unseen-battery-sort",
        prompt="Mô phỏng sắp xếp thời lượng pin (giờ) của 5 dòng máy tính xách tay khác nhau.",
        category="algorithms_sorting",
        archetype="sorting_battery",
        expected_primitives=("bar_chart", "pointer"),
        learning_objective="Củng cố khái niệm bất biến mảng con đã sắp xếp tăng dần từng bước.",
        pedagogical_trace_action="swap",
    ),

    # ── NHÓM 3: Cấu trúc dữ liệu động (8 bài) ──────────────────────────────
    UnseenBenchmarkItem(
        id="unseen-bracket-stack",
        prompt="Mô phỏng kiểm tra tính hợp lệ của chuỗi dấu ngoặc bằng ngăn xếp Stack (gặp mở ngoặc thì push, gặp đóng ngoặc thì pop).",
        category="data_structures",
        archetype="stack_bracket_matching",
        expected_primitives=("stack_view", "value_box"),
        learning_objective="Hiểu nguyên lý LIFO (vào sau ra trước) của ngăn xếp ứng dụng trong phân tích cú pháp.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-browser-history",
        prompt="Mô phỏng lịch sử duyệt trang web với nút Quay lại (Back) hoạt động theo cấu trúc ngăn xếp Stack.",
        category="data_structures",
        archetype="stack_browser_history",
        expected_primitives=("stack_view", "value_box"),
        learning_objective="Mô hình hóa thao tác Push địa chỉ trang web mới và Pop địa chỉ khi nhấn nút Back.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-print-queue",
        prompt="Mô phỏng hàng đợi in ấn tài liệu trong văn phòng: các tài liệu gửi tới được xếp hàng và in lần lượt theo thứ tự đến trước.",
        category="data_structures",
        archetype="queue_printer",
        expected_primitives=("queue_view",),
        learning_objective="Hiểu nguyên lý FIFO (vào trước ra trước) của cấu trúc hàng đợi Queue.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-ticket-queue",
        prompt="Mô phỏng hàng đợi khách hàng mua vé xe buýt: thêm khách vào cuối hàng (Enqueue) và phục vụ khách ở đầu hàng (Dequeue).",
        category="data_structures",
        archetype="queue_ticket",
        expected_primitives=("queue_view",),
        learning_objective="Theo dõi sự thay đổi của hai đầu Front và Rear trong hàng đợi.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-bst-search",
        prompt="Duyệt và tìm kiếm giá trị 45 trên cây nhị phân tìm kiếm BST đã cho.",
        category="data_structures",
        archetype="tree_search",
        expected_primitives=("tree_element",),
        learning_objective="Hiểu quy tắc rẽ nhánh sang cây con trái nếu nhỏ hơn, sang cây con phải nếu lớn hơn.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-genealogy-tree",
        prompt="Mô phỏng cấu trúc cây thư mục hệ điều hành gồm thư mục gốc Root và các thư mục con.",
        category="data_structures",
        archetype="tree_hierarchy",
        expected_primitives=("tree_element",),
        learning_objective="Hình dung trực quan quan hệ cha-con và cấu trúc phân cấp trong khoa học máy tính.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-call-stack",
        prompt="Mô phỏng ngăn xếp gọi hàm (Call Stack) khi thực hiện các lệnh gọi hàm lồng nhau.",
        category="data_structures",
        archetype="stack_call_frame",
        expected_primitives=("stack_view", "value_box"),
        learning_objective="Quan sát khung ngăn xếp được đẩy vào khi gọi hàm và giải phóng khi hàm kết thúc.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-task-scheduler",
        prompt="Hàng đợi điều phối các tác vụ CPU cần xử lý theo thứ tự đến.",
        category="data_structures",
        archetype="queue_cpu_tasks",
        expected_primitives=("queue_view",),
        learning_objective="Hiểu cách hệ điều hành quản lý hàng đợi công việc chờ thực thi.",
        pedagogical_trace_action="highlight",
    ),

    # ── NHÓM 4: Số học nhị phân, Mạch logic & Tham số (8 bài) ───────────────
    UnseenBenchmarkItem(
        id="unseen-rgb-mix",
        prompt="Mô phỏng mô hình phối màu RGB tương tác: học sinh điều chỉnh 3 thanh trượt Đỏ, Lục, Lam từ 0-255 và quan sát ô màu tổng hợp.",
        category="binary_and_parameters",
        archetype="rgb_slider_swatch",
        expected_primitives=("slider", "color_swatch", "value_box"),
        learning_objective="Hiểu nguyên lý pha màu cộng ánh sáng RGB trong đồ họa máy tính.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-half-adder",
        prompt="Mô phỏng mạch cộng bán phần Half Adder: gồm 2 bit đầu vào A, B, đầu ra Tổng S = A XOR B và Nhớ C = A AND B.",
        category="binary_and_parameters",
        archetype="logic_half_adder",
        expected_primitives=("switch", "logic_gate", "lamp"),
        learning_objective="Hiểu cách các cổng logic tổ hợp tạo nên phép cộng nhị phân 1-bit.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-bit-shift",
        prompt="Mô phỏng phép dịch bit nhị phân sang trái (nhân 2) trên thanh ghi 8-bit.",
        category="binary_and_parameters",
        archetype="bit_register_shift",
        expected_primitives=("bit_register", "value_box"),
        learning_objective="Quan sát sự dịch chuyển của các bit và sự thay đổi giá trị thập phân tương ứng.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-parity-check",
        prompt="Mô phỏng mạch kiểm tra bit chẵn lẻ (Parity Bit) bằng cổng XOR để phát hiện lỗi truyền tin.",
        category="binary_and_parameters",
        archetype="logic_parity_gate",
        expected_primitives=("switch", "logic_gate", "lamp"),
        learning_objective="Hiểu ứng dụng của đại số Boole trong kiểm soát lỗi dữ liệu.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-hsl-light",
        prompt="Mô phỏng điều chỉnh độ sáng (Lightness) của một mẫu màu bằng thanh trượt tham số.",
        category="binary_and_parameters",
        archetype="slider_lightness",
        expected_primitives=("slider", "color_swatch", "value_box"),
        learning_objective="Khám phá không gian màu và ảnh hưởng của tham số tới cảm nhận thị giác.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-not-invert",
        prompt="Mô phỏng cổng đảo NOT: đèn đầu ra bật khi công tắc đầu vào tắt và ngược lại.",
        category="binary_and_parameters",
        archetype="logic_not_gate",
        expected_primitives=("switch", "logic_gate", "lamp"),
        learning_objective="Nắm vững bảng chân trị của phép phủ định logic NOT.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-two-complement",
        prompt="Mô phỏng biểu diễn số âm bù 2 trên thanh ghi 8 bit (đảo bit và cộng 1).",
        category="binary_and_parameters",
        archetype="bit_register_twos_comp",
        expected_primitives=("bit_register", "value_box"),
        learning_objective="Hiểu cách máy tính lưu trữ số nguyên có dấu bằng mã bù 2.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-bit-mask",
        prompt="Mô phỏng phép lọc 4 bit thấp (Bitwise AND với mặt nạ 0x0F) trên thanh ghi nhị phân.",
        category="binary_and_parameters",
        archetype="bit_register_mask",
        expected_primitives=("bit_register", "value_box"),
        learning_objective="Hiểu kỹ thuật sử dụng mặt nạ bit trong xử lý dữ liệu cấp thấp.",
        pedagogical_trace_action="highlight",
    ),

    # ── NHÓM 5: Cơ sở dữ liệu & Bảng 2 chiều (8 bài) ────────────────────────
    UnseenBenchmarkItem(
        id="unseen-student-table",
        prompt="Cho bảng danh sách học sinh gồm các cột MãHS, HọTên, ĐiểmToán, ĐiểmTin. Lọc ra các học sinh có ĐiểmTin >= 8.5.",
        category="databases_and_tables",
        archetype="table_filter_query",
        expected_primitives=("table_grid", "value_box"),
        learning_objective="Hiểu phép chọn (Selection) lọc các bản ghi thỏa mãn điều kiện trong CSDL quan hệ.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-product-stock",
        prompt="Cho bảng kho hàng (MãSP, TênSP, SốLượng, ĐơnGiá). Tìm các sản phẩm có số lượng tồn kho dưới 10 để cảnh báo nhập hàng.",
        category="databases_and_tables",
        archetype="table_stock_alert",
        expected_primitives=("table_grid", "value_box"),
        learning_objective="Áp dụng câu lệnh truy vấn lọc trên dữ liệu kinh doanh thực tế.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-truth-table",
        prompt="Mô phỏng bảng chân trị của biểu thức logic A OR (NOT B) cho tất cả các tổ hợp 4 dòng của A và B.",
        category="databases_and_tables",
        archetype="table_truth_matrix",
        expected_primitives=("table_grid",),
        learning_objective="Lập bảng chân trị toàn diện để đánh giá biểu thức logic đa biến.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-sales-matrix",
        prompt="Bảng theo dõi doanh thu 4 quý của 3 chi nhánh công ty: tìm quý có doanh thu cao nhất của Chi nhánh Hà Nội.",
        category="databases_and_tables",
        archetype="table_matrix_scan",
        expected_primitives=("table_grid", "value_box"),
        learning_objective="Phân tích dữ liệu ma trận 2 chiều hàng/cột trong tin học quản lý.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-employee-salary",
        prompt="Cho bảng nhân viên gồm PhòngBan, HọTên, Lương. Đếm số nhân viên thuộc phòng Kỹ thuật có mức lương trên 15 triệu.",
        category="databases_and_tables",
        archetype="table_multi_condition",
        expected_primitives=("table_grid", "value_box"),
        learning_objective="Kết hợp điều kiện lọc văn bản (PhòngBan = 'Kỹ thuật') và điều kiện số (Lương > 15).",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-weather-matrix",
        prompt="Bảng thống kê lượng mưa 12 tháng tại 3 trạm quan trắc: tìm lượng mưa lớn nhất trong năm.",
        category="databases_and_tables",
        archetype="table_weather_matrix",
        expected_primitives=("table_grid", "value_box"),
        learning_objective="Truy vấn cực trị trên bảng số liệu thời gian nhiều chiều.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-book-catalog",
        prompt="Bảng danh mục sách thư viện: lọc các cuốn sách thuộc thể loại 'Tin học' xuất bản sau năm 2020.",
        category="databases_and_tables",
        archetype="table_catalog_filter",
        expected_primitives=("table_grid", "value_box"),
        learning_objective="Thao tác lọc kết hợp trên cơ sở dữ liệu thư viện trường học.",
        pedagogical_trace_action="highlight",
    ),
    UnseenBenchmarkItem(
        id="unseen-flight-schedule",
        prompt="Bảng lịch trình chuyến bay: tìm các chuyến bay khởi hành từ sân bay Nội Bài trước 08:00 sáng.",
        category="databases_and_tables",
        archetype="table_flight_time_filter",
        expected_primitives=("table_grid", "value_box"),
        learning_objective="Xử lý và lọc dữ liệu chuỗi thời gian trong hệ thống thông tin.",
        pedagogical_trace_action="highlight",
    ),
]
