# -*- coding: utf-8 -*-
"""Pool CAPABILITY — phủ các HÌNH THỨC mô phỏng hệ có, không phủ theo môn.

Vá hai lỗ hổng bằng chứng lớn nhất mà PRE-M8 audit tìm ra:
1. SẮP XẾP: engine bubble_sort/insertion_sort ĐÃ ship từ lâu nhưng benchmark cũ
   KHÔNG có case nào → luận văn tuyên bố 8 thuật toán, bằng chứng chỉ có 6.
2. L3 (đa giai đoạn) gần như trống → tuyên bố "compose cảnh phức tạp" thiếu chứng cứ.
3. Sơ đồ HỆ THỐNG THÔNG TIN từng bị TỪ CHỐI IM LẶNG dù DSL biểu diễn được (S2).
"""

from __future__ import annotations

from app.evaluation.dataset import EvalItem

CAPABILITY_ITEMS: list[EvalItem] = [
    # ── Sorting: engine có sẵn, trước đây KHÔNG có bằng chứng ──────────
    EvalItem(
        id="cap-bubble",
        text="Cho dãy 5, 2, 9, 1, 7. Hãy sắp xếp dãy tăng dần bằng thuật toán sắp xếp nổi bọt.",
        group="specialized",
        expect_simulation_id="algorithm.bubble_sort",
        tags=("capability", "smoke_v2", "flagship"),
        curriculum_area="T11CS.CD6",
        curriculum_topic="Các thuật toán sắp xếp đơn giản (Bài 21)",
        capability_family="sorting_movement",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Giải thích một lượt duyệt của sắp xếp nổi bọt làm gì và vì sao thuật toán dừng.",
        pedagogical_rationale=(
            "Cơ chế ẩn: QUYẾT ĐỊNH so sánh → đổi chỗ ở từng cặp kề nhau, và phần đuôi đã "
            "sắp lớn dần sau mỗi lượt. Trên giấy học sinh chỉ thấy dãy đầu và dãy cuối, "
            "không thấy vì sao phần tử lớn 'nổi' lên. Timeline tất định cho xem từng phép "
            "so sánh và từng lần đổi chỗ; what-if branch còn cho học sinh đổi chỗ SAI rồi "
            "quan sát hậu quả — điều ảnh/video/quiz không làm được."
        ),
    ),
    EvalItem(
        id="cap-insertion",
        text="Sắp xếp dãy 8, 3, 5, 2 theo thứ tự tăng dần bằng thuật toán sắp xếp chèn.",
        group="specialized",
        expect_simulation_id="algorithm.insertion_sort",
        tags=("capability",),
        curriculum_area="T11CS.CD6",
        curriculum_topic="Các thuật toán sắp xếp đơn giản (Bài 21)",
        capability_family="sorting_movement",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Phân biệt sắp xếp chèn với sắp xếp nổi bọt qua cách phần tử được đưa vào phần đã sắp.",
        pedagogical_rationale=(
            "Cơ chế ẩn: vùng ĐÃ SẮP ở đầu dãy lớn dần, và mỗi phần tử mới phải LÙI dần "
            "về đúng vị trí. Học sinh thường nhầm hai thuật toán sắp xếp vì kết quả cuối "
            "giống hệt nhau — chỉ có diễn biến từng bước mới phân biệt được."
        ),
    ),
    # ── Sơ đồ hệ thống thông tin TĨNH (đề THẬT từng bị từ chối im lặng) ──
    # Quan trọng: đây là interactive_visualization, KHÔNG phải executable simulation.
    EvalItem(
        id="cap-sysflow-static",
        text=(
            "Phân tích hệ thống quản lí điểm của một trường THPT: xác định người dùng của "
            "hệ thống, dữ liệu được lưu trữ, đầu vào, đầu ra, các chức năng chính và luồng "
            "dữ liệu giữa chúng."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "system_flow", "min_directed": 2, "moving": False},
        tags=("capability", "smoke_v2", "flagship", "system_flow"),
        curriculum_area="T11.CD4",
        curriculum_topic="Lưu trữ dữ liệu và khai thác thông tin phục vụ quản lí (Bài 10)",
        capability_family="data_flow",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="node_edge_flow",
        learning_objective=(
            "Chỉ ra được các thành phần của một hệ thống thông tin (tác nhân, chức năng, "
            "kho dữ liệu) và hướng dữ liệu chảy giữa chúng."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: HƯỚNG và ĐÍCH của dữ liệu. Học sinh liệt kê được 'người dùng, dữ "
            "liệu, chức năng' thành ba danh sách rời rạc nhưng không thấy chúng NỐI với "
            "nhau ra sao — ai ghi vào kho nào, cái gì đi ra đâu. Sơ đồ có mũi tên biến ba "
            "danh sách thành một cấu trúc. Đây là sơ đồ TĨNH: không có process diễn biến, "
            "và semantic check CẤM giả vờ nó chạy được."
        ),
    ),
    # ── L3 thật: dựng cảnh TỪNG BƯỚC rồi CHẠY một quá trình trên cảnh đó ──
    EvalItem(
        id="cap-l3-netbuild",
        text=(
            "Mô phỏng quá trình xây dựng một mạng máy tính: lần lượt thêm máy khách, thêm "
            "switch, thêm router, thêm máy chủ, rồi nối chúng lại với nhau. Sau khi mạng "
            "hoàn chỉnh, cho một gói tin đi từ máy khách tới máy chủ."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "progressive_reveal", "min_steps": 4},
        tags=("capability", "L3"),
        curriculum_area="T12.CD2",
        curriculum_topic="Thiết bị mạng và đường đi của gói tin (Bài 3–4)",
        capability_family="progressive_reveal+movement",
        complexity="L3",
        result_mode="executable_simulation",
        learning_objective="Hiểu mạng là một cấu trúc được LẮP GHÉP, và gói tin chỉ đi được khi đã có liên kết.",
        pedagogical_rationale=(
            "Cơ chế ẩn: quan hệ nhân quả giữa TOPOLOGY và ĐƯỜNG ĐI. Một ảnh mạng hoàn chỉnh "
            "khiến học sinh tưởng đường đi là hiển nhiên. Dựng từng thiết bị/liên kết rồi mới "
            "truyền gói tin cho thấy đường đi là HỆ QUẢ của cấu trúc. Đây là case đa giai đoạn "
            "thật: reveal_sequence (dựng) + move_along_path (chạy) trong cùng một cảnh — "
            "chứng minh hệ compose được cảnh phức tạp, không chỉ cảnh nguyên tử."
        ),
    ),
    # ── M13: capability_gap trung thực cho Dijkstra — xem COVERAGE.md §7b ──
    # Dijkstra KHÔNG có anchor SGK nào (ngoài phạm vi công khai đề tài); case này
    # KHÔNG gán curriculum_area giả để qua admission — dùng chuỗi trung thực.
    EvalItem(
        "cap-dijkstra-gap",
        "Mô phỏng thuật toán Dijkstra tìm đường ngắn nhất từ A đến C trên đồ thị có trọng số.",
        "unsupported", None,
        tags=("boundary", "m13_soundness"),
        curriculum_area="ngoài phạm vi công khai Tin học THPT — không anchor SGK (COVERAGE §Dijkstra-M13)",
        curriculum_topic="Đồ thị có trọng số (ngoài phạm vi)",
        capability_family="algorithmic_computation_gap",
        complexity="L4",
        result_mode="unsupported",
        learning_objective="Hệ từ chối trung thực yêu cầu thuật toán không có engine, thay vì render cảnh giả.",
        pedagogical_rationale=(
            "Cơ chế ẩn của Dijkstra — khoảng cách tạm, extract-min, nới cạnh, tập finalized — "
            "KHÔNG có engine tất định nào sở hữu; cảnh generic với đường đi khai sẵn và tổng trọng số "
            "trên id cạnh dạy SAI cơ chế (LLM tự giải bài thay engine). capability_gap trung thực "
            "tốt hơn một pseudo-simulation trông-hợp-lý."
        ),
    ),
]
