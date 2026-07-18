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
        tags=("capability", "smoke_v2", "flagship", "m14_sorting"),
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
        tags=("capability", "m14_sorting"),
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
    # ── M14 paraphrase THEO CƠ CHẾ (không nêu tên "nổi bọt") ──────────
    EvalItem(
        id="cap-bubble-paraphrase",
        text=(
            "Xếp các bạn theo điểm tăng dần bằng cách lần lượt so sánh HAI bạn ĐỨNG KỀ "
            "nhau và đổi chỗ nếu bạn trước có điểm cao hơn. Dãy điểm: 6, 3, 8, 4."
        ),
        group="specialized",
        expect_simulation_id="algorithm.bubble_sort",
        tags=("capability", "m14_sorting", "m15_wave1"),
        curriculum_area="T11CS.CD6",
        curriculum_topic="Các thuật toán sắp xếp đơn giản (Bài 21)",
        capability_family="sorting_movement",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Nhận ra cơ chế đổi-chỗ-cặp-kề của sắp xếp nổi bọt qua MÔ TẢ, không qua tên gọi.",
        pedagogical_rationale=(
            "Cơ chế ẩn: so sánh và ĐỔI CHỖ hai phần tử KỀ nhau — đặc trưng của nổi bọt. "
            "Đề diễn đạt cơ chế bằng lời (không gọi tên thuật toán) để kiểm hệ định tuyến "
            "theo CƠ CHẾ chứ không theo từ khóa tên thuật toán."
        ),
    ),
    # ── M14 near-miss: cơ chế NGOÀI family → capability_gap trung thực ──
    EvalItem(
        id="cap-selection-sort-gap",
        text="Sắp xếp dãy 5, 2, 9, 1 tăng dần bằng thuật toán sắp xếp chọn: mỗi bước tìm phần tử nhỏ nhất của phần còn lại rồi đưa lên đầu.",
        group="unsupported",
        expect_simulation_id=None,
        tags=("capability", "boundary", "m14_sorting", "m15_wave1"),
        curriculum_area="T11CS.CD6 (biến thể sắp xếp — cơ chế chưa có engine)",
        curriculum_topic="Sắp xếp chọn (selection sort)",
        capability_family="sorting_mechanism_gap",
        complexity="L4",
        result_mode="unsupported",
        learning_objective="Hệ từ chối trung thực khi đề ép một cơ chế sắp xếp mà không executor nào sở hữu, thay vì minh hoạ bằng thuật toán khác.",
        pedagogical_rationale=(
            "Cơ chế ẩn của sắp xếp CHỌN — CHỌN CỰC TIỂU LẶP trên phần chưa sắp — khác hẳn "
            "đổi-chỗ-cặp-kề (nổi bọt) và dời-vào-phần-đã-sắp (chèn). Engine hiện có KHÔNG sở "
            "hữu cơ chế này; dựng cảnh nổi bọt/chèn để 'minh hoạ' selection sort là dạy SAI "
            "cơ chế. capability_gap trung thực (mechanism gate) tốt hơn."
        ),
    ),
    EvalItem(
        id="cap-quicksort-gap",
        text="Mô phỏng sắp xếp nhanh (quick sort) dãy 5, 3, 8, 1, 9: chọn một mốc, chia dãy quanh mốc rồi sắp mỗi phần một cách đệ quy.",
        group="unsupported",
        expect_simulation_id=None,
        tags=("capability", "boundary"),
        curriculum_area="ngoài phạm vi sắp xếp đơn giản THPT — cơ chế phân hoạch đệ quy",
        curriculum_topic="Sắp xếp nhanh (quick sort)",
        capability_family="sorting_mechanism_gap",
        complexity="L4",
        result_mode="unsupported",
        learning_objective="Hệ từ chối cơ chế phân hoạch đệ quy khi không có engine tất định sở hữu.",
        pedagogical_rationale=(
            "Cơ chế ẩn của quick sort — CHIA quanh mốc + ĐỆ QUY hai nửa — không thuộc họ so "
            "sánh-đổi-chỗ tuyến tính mà engine hiện có biểu diễn. Ép về nổi bọt/chèn là dạy "
            "sai; mechanism gate trả capability_gap."
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
    # ── M15 wave 1: đổi cơ số KHÁC nhị phân — capability_gap trung thực ──────
    # SGK T10 B4 (Hệ nhị phân và dữ liệu số nguyên) CHỈ dạy đổi sang cơ số 2;
    # binary.decimal_to_binary CHỈ sở hữu positional_representation.binary_positional_weights
    # (xem catalog.py) — hex/octal là positional_representation.non_binary_base, một
    # INTENTIONAL_GAP_MECHANISM (mechanisms.py): KHÔNG target nào sở hữu. Hai lớp
    # phòng thủ độc lập cùng từ chối: (A) ownership gate trên direct entry
    # binary.decimal_to_binary, (B) route-mismatch recovery khi bị misroute sang
    # generic.rule_scene (xem test_pipeline_mechanism_consistency.py, Task 9).
    EvalItem(
        id="m15-hex-gap",
        text="Đổi số 200 sang hệ thập lục phân và giải thích từng bước biểu diễn.",
        group="unsupported",
        expect_simulation_id=None,
        tags=("m15_wave1",),
        curriculum_area="T10.CD1 chỉ phủ đổi sang NHỊ PHÂN (Bài 4) — hệ thập lục phân ngoài phạm vi anchor",
        curriculum_topic="Đổi cơ số ngoài nhị phân (thập lục phân — ngoài anchor SGK Tin 10 Bài 4)",
        capability_family="positional_representation_base_gap",
        complexity="L4",
        result_mode="unsupported",
        learning_objective=(
            "Hệ từ chối trung thực khi đề yêu cầu đổi sang cơ số khác nhị phân (thập lục phân) mà "
            "không engine tất định nào sở hữu cơ chế biểu diễn vị trí ở cơ số đó."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn của đổi cơ số thập lục phân — chia lấy dư LẶP theo cơ số 16, không phải "
            "trọng số bit 8/4/2/1 của nhị phân — KHÔNG có engine tất định nào sở hữu "
            "(binary.decimal_to_binary chỉ sở hữu binary_positional_weights). Ép vào engine nhị "
            "phân sẽ ra kết quả SAI cơ số một cách im lặng; dựng cảnh generic minh hoạ đáp án cũng "
            "là AI tự giải thay engine. capability_gap trung thực tốt hơn cả hai."
        ),
    ),
    EvalItem(
        id="m15-octal-gap",
        text="Đổi số 200 sang hệ bát phân và giải thích từng bước biểu diễn.",
        group="unsupported",
        expect_simulation_id=None,
        tags=("m15_wave1",),
        curriculum_area="T10.CD1 chỉ phủ đổi sang NHỊ PHÂN (Bài 4) — hệ bát phân ngoài phạm vi anchor",
        curriculum_topic="Đổi cơ số ngoài nhị phân (bát phân — ngoài anchor SGK Tin 10 Bài 4)",
        capability_family="positional_representation_base_gap",
        complexity="L4",
        result_mode="unsupported",
        learning_objective=(
            "Hệ từ chối trung thực khi đề yêu cầu đổi sang cơ số khác nhị phân (bát phân) mà không "
            "engine tất định nào sở hữu cơ chế biểu diễn vị trí ở cơ số đó."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn của đổi cơ số bát phân — chia lấy dư LẶP theo cơ số 8, không phải trọng số "
            "bit 8/4/2/1 của nhị phân — KHÔNG có engine tất định nào sở hữu (binary.decimal_to_binary "
            "chỉ sở hữu binary_positional_weights). Ép vào engine nhị phân sẽ ra kết quả SAI cơ số "
            "một cách im lặng; dựng cảnh generic minh hoạ đáp án cũng là AI tự giải thay engine. "
            "capability_gap trung thực tốt hơn cả hai."
        ),
    ),
    EvalItem(
        id="m15-binary-positive",
        text="Số 173 được biểu diễn trong hệ nhị phân như thế nào? Hãy chỉ rõ những bit trọng số nào đang bật.",
        group="specialized",
        expect_simulation_id="binary.decimal_to_binary",
        tags=("m15_wave1",),
        curriculum_area="T10.CD1",
        curriculum_topic="Hệ nhị phân và dữ liệu số nguyên (Bài 4)",
        capability_family="data_representation",
        complexity="L1",
        result_mode="executable_simulation",
        learning_objective="Đổi được số thập phân sang nhị phân và giải thích vai trò trọng số của từng bit.",
        pedagogical_rationale=(
            "Cơ chế ẩn: mỗi bit ĐÓNG GÓP một trọng số (128/64/32/16/8/4/2/1) vào giá trị cuối. Học "
            "sinh tính tay ra đúng dãy bit nhưng không thấy TỪNG bit bật/tắt góp phần thế nào vào "
            "tổng — timeline bật/tắt từng trọng số và cộng dồn cho thấy quan hệ nhân quả đó. Case "
            "này là ĐỐI CHỨNG DƯƠNG cho m15-hex-gap/m15-octal-gap: cùng domain đổi cơ số, nhưng "
            "trong phạm vi engine sở hữu (cơ số 2) → PHẢI chạy được, không bị gate chặn oan."
        ),
    ),
    EvalItem(
        id="m15-binsearch-unsorted",
        text=(
            "Cho dãy số 15, 3, 42, 8, 23, 4, 16 (chưa được sắp xếp). Hãy tìm nhanh số 23 trong dãy "
            "này bằng cách chia đôi phạm vi tìm kiếm."
        ),
        group="specialized",
        expect_simulation_id="algorithm.binary_search",
        tags=("m15_wave1",),
        curriculum_area="T11CS.CD6",
        curriculum_topic="Bài toán tìm kiếm (Bài 19)",
        capability_family="search_path",
        complexity="L4",
        result_mode="executable_simulation",
        learning_objective=(
            "Nhận ra tìm kiếm nhị phân đòi hỏi dãy có thứ tự — và thấy hệ TỰ SẮP XẾP trước khi "
            "chạy thay vì áp thuật toán sai tiền đề hoặc từ chối oan vì thiếu từ khoá 'đã sắp'."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: interval_elimination.halve_sorted_interval CHỈ đúng trên dãy ĐÃ có thứ tự — "
            "một TIỀN ĐỀ hay bị bỏ qua khi học sinh chỉ nhớ 'chia đôi cho nhanh'. Đề cố ý cho dãy "
            "CHƯA sắp nhưng vẫn nêu đúng cơ chế ('tìm nhanh', 'chia đôi') để kiểm: (1) hệ định "
            "tuyến theo CƠ CHẾ chứ không theo từ khoá 'đã sắp'; (2) validator tự sắp dãy trước khi "
            "mô phỏng (app/validation/simulation.py) và chú thích sư phạm rõ ràng, thay vì chạy sai "
            "tiền đề hoặc từ chối oan."
        ),
    ),
]
