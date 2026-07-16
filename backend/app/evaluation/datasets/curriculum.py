# -*- coding: utf-8 -*-
"""Pool CURRICULUM — phủ chương trình SGK một cách ĐẠI DIỆN, không vét cạn.

Nguồn: 5 SGK "Kết nối tri thức với cuộc sống" (NXB Giáo dục Việt Nam, GDPT 2018)
trong data/knowledge/sources — Tin học 10, 11-CS, 11-ICT, 12-CS, 12-ICT. Xem
docs/COVERAGE.md §1 để biết CHÍNH XÁC nguồn này chứng minh được điều gì và
KHÔNG chứng minh được điều gì (không OCR toàn văn; neo ở mức TÊN BÀI).

NGUYÊN TẮC (docs/COVERAGE.md §4): một chủ đề CÓ trong chương trình KHÔNG phải là
lý do để thêm đề. Chỉ thêm chủ đề có CƠ CHẾ ẨN + biến thiên/nhân quả + lợi thế rõ
so với text/ảnh/video/quiz. Các chủ đề đạo đức, hướng nghiệp, kĩ năng dùng phần
mềm, tổng quan AI → CỐ Ý KHÔNG có đề nào (xem §7 "low-value/decorative").
"""

from __future__ import annotations

from app.evaluation.dataset import EvalItem

CURRICULUM_ITEMS: list[EvalItem] = [
    EvalItem(
        id="cur-t10-binary",
        text="Số 37 được biểu diễn trong hệ nhị phân như thế nào?",
        group="specialized",
        expect_simulation_id="binary.decimal_to_binary",
        tags=("curriculum",),
        curriculum_area="T10.CD1",
        curriculum_topic="Hệ nhị phân và dữ liệu số nguyên (Bài 4)",
        capability_family="data_representation",
        complexity="L1",
        result_mode="executable_simulation",
        cross_domain_group="weighted_sum",
        learning_objective="Đổi được số thập phân sang nhị phân và giải thích vai trò trọng số của từng bit.",
        pedagogical_rationale=(
            "Cơ chế ẩn: mỗi bit ĐÓNG GÓP một trọng số vào giá trị cuối. Bảng tính tay chỉ cho "
            "kết quả; bật/tắt từng bit và thấy số thập phân đổi theo mới cho thấy quan hệ "
            "nhân quả giữa bit và giá trị."
        ),
    ),
    EvalItem(
        id="cur-t10-stairs-xor",
        text=(
            "Đèn cầu thang được điều khiển bởi hai công tắc ở hai đầu: gạt bất kì công tắc "
            "nào cũng làm đèn đổi trạng thái. Mô phỏng mạch đèn cầu thang này."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "boolean_gate", "op": "xor"},
        tags=("curriculum",),
        curriculum_area="T10.CD1",
        curriculum_topic="Dữ liệu lôgic (Bài 5)",
        capability_family="boolean_rule",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="boolean_rule",
        learning_objective="Nhận ra mạch đèn cầu thang quen thuộc chính là phép XOR.",
        pedagogical_rationale=(
            "Cơ chế ẩn: XOR nấp sau một thiết bị đời thường. Học sinh thuộc bảng chân trị XOR "
            "nhưng không nối được với cái công tắc ở nhà mình. Gạt từng công tắc và thấy đèn "
            "đổi trạng thái theo đúng bảng chân trị làm lộ ra sự đồng nhất đó — bảng chân trị "
            "in trên giấy không tạo được liên hệ này."
        ),
    ),
    EvalItem(
        id="cur-t11cs-binsearch",
        text=(
            "Danh sách mã học sinh đã được sắp xếp tăng dần: 102, 115, 128, 134, 147, 156, 163. "
            "Hãy tìm nhanh mã 147 bằng cách chia đôi phạm vi tìm kiếm."
        ),
        group="specialized",
        expect_simulation_id="algorithm.binary_search",
        tags=("curriculum", "smoke_v2", "flagship"),
        curriculum_area="T11CS.CD6",
        curriculum_topic="Bài toán tìm kiếm (Bài 19)",
        capability_family="search_path",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Giải thích vì sao tìm kiếm nhị phân nhanh hơn tìm kiếm tuần tự.",
        pedagogical_rationale=(
            "Cơ chế ẩn: NỬA BỊ LOẠI ở mỗi bước. Học sinh thường nghĩ tìm kiếm nhị phân chỉ là "
            "'nhảy cóc cho nhanh' mà không thấy phạm vi tìm kiếm co lại một nửa mỗi lần. "
            "Timeline làm hiện rõ vùng còn xét và vùng vừa bị loại — thứ không nhìn thấy được "
            "trên một dãy số in ra giấy."
        ),
    ),
    EvalItem(
        id="cur-t10-count",
        text="Lớp có 8 bạn với điểm 7,5; 9; 6; 8; 5; 9,5; 7; 8,5. Đếm số bạn đạt từ 8 điểm trở lên.",
        group="specialized",
        expect_simulation_id="algorithm.count_if",
        tags=("curriculum",),
        curriculum_area="T10.CD5",
        curriculum_topic="Câu lệnh lặp và rẽ nhánh trên danh sách (Bài 19–23)",
        capability_family="conditional_accumulator",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Hiểu biến đếm là TRẠNG THÁI được giữ lại qua các vòng lặp.",
        pedagogical_rationale=(
            "Cơ chế ẩn: biến đếm sống SÓT giữa các vòng lặp, và điều kiện quyết định có tăng "
            "nó hay không. Đây đúng là chỗ học sinh mới học lập trình vấp: họ thấy kết quả "
            "cuối mà không thấy biến thay đổi ở đâu. Timeline gắn với dòng mã giả cho thấy "
            "từng lần so sánh và từng lần biến đếm nhích lên."
        ),
    ),
    EvalItem(
        id="cur-t12-webbuild",
        text=(
            "Mô phỏng quá trình tạo một trang web giới thiệu câu lạc bộ Tin học: hình thành "
            "từng bước gồm tiêu đề trang, đoạn văn giới thiệu, rồi khung thông tin liên hệ."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "progressive_reveal", "min_steps": 3},
        tags=("curriculum",),
        curriculum_area="T12.CD4",
        curriculum_topic="HTML và cấu trúc trang web (Bài 7–9)",
        capability_family="structural_construction",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Hiểu trang web là cấu trúc được LẮP GHÉP từ các phần tử lồng nhau.",
        pedagogical_rationale=(
            "Cơ chế ẩn: TRÌNH TỰ và QUAN HỆ LỒNG NHAU của các phần tử. Một ảnh chụp trang web "
            "hoàn chỉnh không cho thấy nó được dựng theo thứ tự nào, phần nào chứa phần nào. "
            "Hình thành từng bước làm hiện cấu trúc cây nằm sau giao diện phẳng."
        ),
    ),
    EvalItem(
        id="cur-t12-packet",
        text=(
            "Một máy tính trong phòng thực hành gửi yêu cầu tới máy chủ web qua switch của "
            "phòng và router của trường. Minh hoạ đường đi của gói tin."
        ),
        group="specialized",
        expect_simulation_id="network.packet_routing",
        tags=("curriculum",),
        curriculum_area="T12.CD2",
        curriculum_topic="Giao thức mạng, thiết bị mạng (Bài 3–4)",
        capability_family="node_edge_graph+movement",
        complexity="L2",
        result_mode="executable_simulation",
        cross_domain_group="node_edge_flow",
        learning_objective="Hiểu gói tin đi QUA TỪNG CHẶNG chứ không nhảy thẳng tới đích.",
        pedagogical_rationale=(
            "Cơ chế ẩn: các CHẶNG trung gian và việc đường đi được TÍNH RA từ topology (BFS "
            "tất định), không phải do người vẽ tuỳ ý. Học sinh hình dung Internet như một "
            "đường ống thẳng; đi từng chặng phá vỡ hình dung đó."
        ),
    ),

    # ── M10-AI-ROUTE: định tuyến NL cho network.protocol_encapsulation ──
    # Bộ 5 case tự chứa (tag "m10_route") cho một lần live smoke có mục tiêu:
    # 2 encapsulation rõ + 1 mixed (ranh giới) + 1 routing tương phản + 1
    # unsupported nâng cao. Phân biệt PHẢI ngữ nghĩa: đường đi qua NÚT
    # (packet_routing) ↔ biến đổi PDU qua TẦNG (encapsulation).
    EvalItem(
        id="cur-t12-encap1",
        text=(
            "Mô phỏng cách dữ liệu từ ứng dụng được đóng gói qua các tầng TCP/IP "
            "rồi truyền tới máy nhận."
        ),
        group="specialized",
        expect_simulation_id="network.protocol_encapsulation",
        tags=("curriculum", "m10_route"),
        curriculum_area="T12.CD2",
        curriculum_topic="Giao thức mạng, mô hình TCP/IP (Bài 3–4)",
        capability_family="layered_transformation",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Hiểu dữ liệu được THÊM DẦN thông tin giao thức khi đi xuống từng tầng ở máy gửi.",
        pedagogical_rationale=(
            "Cơ chế ẩn: PDU BIẾN ĐỔI qua từng tầng — mỗi tầng thêm đúng phần thông tin của "
            "mình theo THỨ TỰ cố định. Sơ đồ tĩnh 4 tầng không cho thấy thứ tự thêm/gỡ và "
            "tính đối xứng gửi–nhận; mô phỏng từng bước làm hiện cả hai."
        ),
    ),
    EvalItem(
        id="cur-t12-encap2",
        text=(
            "Dữ liệu thay đổi thế nào khi đi từ tầng ứng dụng xuống tầng truy cập mạng "
            "và được tháo gói ở máy nhận?"
        ),
        group="specialized",
        expect_simulation_id="network.protocol_encapsulation",
        tags=("curriculum", "m10_route"),
        curriculum_area="T12.CD2",
        curriculum_topic="Giao thức mạng, mô hình TCP/IP (Bài 3–4)",
        capability_family="layered_transformation",
        complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Mô tả được PDU ở từng tầng và giải thích tháo gói là quá trình NGƯỢC của đóng gói.",
        pedagogical_rationale=(
            "Cơ chế ẩn: tính ĐỐI XỨNG gửi–nhận — máy nhận gỡ đúng phần thông tin theo thứ tự "
            "ngược lại. Học sinh thường thuộc lòng tên 4 tầng nhưng không thấy dữ liệu THAY "
            "ĐỔI ra sao; theo dõi PDU từng bước mới lộ cơ chế đó."
        ),
    ),
    EvalItem(
        id="cur-t12-encap-mixed",
        text=(
            "Dữ liệu từ máy tính được đóng gói qua các tầng TCP/IP, truyền qua router "
            "tới máy chủ, rồi được tháo gói ở đó."
        ),
        group="specialized",
        expect_simulation_id="network.protocol_encapsulation",
        tags=("curriculum", "boundary", "m10_route"),
        curriculum_area="T12.CD2",
        curriculum_topic="Giao thức mạng, mô hình TCP/IP (Bài 3–4)",
        capability_family="layered_transformation",
        complexity="L3",
        result_mode="executable_simulation",
        learning_objective="Phân biệt được cơ chế ĐÓNG GÓI theo tầng với việc gói tin ĐI QUA thiết bị trung gian.",
        pedagogical_rationale=(
            "Case RANH GIỚI có cả hai tín hiệu (tầng + router): cơ chế ẩn được HỎI là biến "
            "đổi PDU (đóng gói/tháo gói) — router chỉ là ngữ cảnh trung chuyển. Classify phải "
            "phân biệt theo cơ chế, không theo từ khóa thiết bị."
        ),
    ),
    EvalItem(
        id="cur-t12-route-contrast",
        text="Gói tin đi từ máy khách qua router và ISP tới máy chủ theo đường nào?",
        group="specialized",
        expect_simulation_id="network.packet_routing",
        tags=("curriculum", "boundary", "m10_route"),
        curriculum_area="T12.CD2",
        curriculum_topic="Thiết bị mạng và đường truyền (Bài 3–4)",
        capability_family="node_edge_graph+movement",
        complexity="L2",
        result_mode="executable_simulation",
        cross_domain_group="node_edge_flow",
        learning_objective="Xác định được đường đi từng chặng của gói tin trên một topology cho sẵn.",
        pedagogical_rationale=(
            "Cặp TƯƠNG PHẢN với cur-t12-encap*: cùng bề mặt 'mạng máy tính' nhưng cơ chế ẩn "
            "là ĐƯỜNG ĐI qua các NÚT (BFS trên topology), không phải biến đổi PDU theo tầng. "
            "Khóa ranh giới hai module network để routing không nuốt encapsulation và ngược lại."
        ),
    ),
    EvalItem(
        id="cur-t12-tcp-advanced",
        text=(
            "Mô phỏng chi tiết bắt tay TCP ba bước, số thứ tự sequence, ACK, "
            "retransmission khi mất gói và congestion control."
        ),
        group="unsupported",
        tags=("boundary", "m10_route"),
        curriculum_area="T12.CD2",
        curriculum_topic="Giao thức mạng (kiến thức nâng cao ngoài phạm vi)",
        capability_family="layered_transformation",
        complexity="L4",
        result_mode="unsupported",
        learning_objective="(Ngoài phạm vi v1 — case ranh giới để kiểm tính trung thực năng lực.)",
        pedagogical_rationale=(
            "Cơ chế được hỏi (handshake, seq/ACK, retransmission, congestion) đòi mô hình "
            "TRẠNG THÁI GIAO THỨC hai chiều mà engine v1 (9 bước đóng gói một chiều) KHÔNG có. "
            "Thà unsupported trung thực còn hơn ép vào mô phỏng đơn giản gây hiểu lầm (bất biến #8/#9)."
        ),
    ),

    # ── M11: composition boolean LỒNG qua giá trị trung gian (tag "m11_compose") ──
    # Bộ 5 case tự chứa cho live smoke có mục tiêu: 2 case lồng AND(x, OR(y,z))
    # khác miền bề mặt + 1 case NOT + 1 paraphrase probe ("ít nhất một trong") +
    # 1 capability_gap thật (vòng lặp có điều kiện dừng). Đây là case
    # DEVELOPMENT/REGRESSION — dùng để soi lỗi và mài prompt, KHÔNG được trình
    # bày về sau như held-out benchmark chưa đụng tới.
    EvalItem(
        id="m11-nested-canonical",
        text=(
            "Có ba công tắc A, B, C và một bóng đèn. Đèn sáng khi công tắc A bật và "
            "(công tắc B hoặc công tắc C) bật. Mô phỏng mạch để học sinh bật/tắt "
            "từng công tắc và quan sát đèn."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "nested_boolean", "expr": {"op": "and", "args": ["x", {"op": "or", "args": ["y", "z"]}]}},
        tags=("curriculum", "m11_compose"),
        curriculum_area="T10.CD1",
        curriculum_topic="Dữ liệu lôgic — biểu thức lôgic ghép (Bài 5)",
        capability_family="boolean_rule_chain",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="boolean_rule_chain",
        learning_objective=(
            "Giải thích được vì sao đèn sáng/tắt theo biểu thức ghép có nhóm: kết quả "
            "đi qua một GIÁ TRỊ TRUNG GIAN (B hoặc C) rồi mới kết hợp với A."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: cấu trúc NHÓM của biểu thức lôgic — giá trị trung gian B∨C "
            "không nhìn thấy được trong biểu thức phẳng hay đáp án cuối. Nghiên cứu "
            "CS-education (Herman et al., TOCE 2012) ghi nhận dịch đặc tả lời văn sang "
            "biểu thức Boolean là kỹ năng khó có misconception hệ thống. Bật từng công "
            "tắc và thấy trung gian đổi TRƯỚC đèn chính làm lộ cấu trúc hai tầng. Về "
            "kiến trúc: đây là bằng chứng LLM compose ĐƯỢC hai rule nối chuỗi qua object "
            "trung gian — điều chưa case nào đo (mọi case boolean cũ đều một rule)."
        ),
    ),
    EvalItem(
        id="m11-nested-access",
        text=(
            "Hệ thống quản lí học tập của trường chỉ cho phép vào trang quản trị khi "
            "tài khoản hợp lệ và người dùng là giáo viên hoặc quản trị viên. Mô phỏng "
            "quy tắc truy cập này với các điều kiện bật/tắt và một đèn báo được phép truy cập."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "nested_boolean", "expr": {"op": "and", "args": ["x", {"op": "or", "args": ["y", "z"]}]}},
        tags=("curriculum", "m11_compose"),
        curriculum_area="T11.CD4 / T10.CD2",
        curriculum_topic="Kiểm soát truy cập, phân quyền người dùng (Bài 15 / Bài 9)",
        capability_family="boolean_rule_chain",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="boolean_rule_chain",
        learning_objective=(
            "Nhận ra phân quyền truy cập là một biểu thức lôgic GHÉP: điều kiện vai trò "
            "(giáo viên HOẶC quản trị viên) là một giá trị trung gian trước khi VÀ với tài khoản hợp lệ."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: cùng cấu trúc AND(x, OR(y,z)) như case canonical nhưng ở miền "
            "PHÂN QUYỀN — cặp cùng-capability-khác-miền cho chuỗi rule lồng, nối tiếp "
            "bằng chứng tái sử dụng của xd-access-boolean (một tầng). Học sinh tắt "
            "'tài khoản hợp lệ' và thấy đèn tắt DÙ vai trò đúng — lộ ra điều kiện "
            "chặn tổng ở tầng ngoài, điều một bảng phân quyền tĩnh không cho thấy."
        ),
    ),
    EvalItem(
        id="m11-paraphrase-atleast",
        text=(
            "Có ba công tắc A, B, C và một bóng đèn. Đèn sáng khi A bật và ít nhất "
            "một trong hai công tắc B hoặc C bật. Mô phỏng mạch này."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "nested_boolean", "expr": {"op": "and", "args": ["x", {"op": "or", "args": ["y", "z"]}]}},
        tags=("curriculum", "boundary", "m11_compose"),
        curriculum_area="T10.CD1",
        curriculum_topic="Dữ liệu lôgic — biểu thức lôgic ghép (Bài 5)",
        capability_family="boolean_rule_chain",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="boolean_rule_chain",
        learning_objective=(
            "Như m11-nested-canonical — cùng mạch, chỉ khác cách phát biểu điều kiện OR."
        ),
        pedagogical_rationale=(
            "PARAPHRASE ROBUSTNESS PROBE: 'ít nhất một trong HAI' với k=1 tương đương "
            "thuần OR — DSL biểu diễn được, nên từ chối là ROUTING UNDER-CLAIM, không "
            "phải capability_gap thật (ngưỡng thật sự là 'ít nhất 2 trong 3' — case "
            "c-threshold). Câu chữ này va chạm bề mặt với hướng dẫn numeric_threshold "
            "trong analyze.md; case này ghi nhận baseline và khóa kỳ vọng cuối M11: "
            "phải về generic composition lồng."
        ),
    ),
    EvalItem(
        id="m11-nested-not",
        text=(
            "Máy tính ở phòng thực hành truy cập được Internet khi công tắc mạng bật "
            "và chế độ khóa của giáo viên đang tắt. Mô phỏng quy tắc này với các công "
            "tắc và một đèn báo có mạng."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "nested_boolean", "expr": {"op": "and", "args": ["x", {"op": "not", "args": ["y"]}]}},
        tags=("curriculum", "m11_compose"),
        curriculum_area="T10.CD1",
        curriculum_topic="Dữ liệu lôgic — phép phủ định (Bài 5)",
        capability_family="boolean_rule_chain",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="boolean_rule_chain",
        learning_objective=(
            "Hiểu điều kiện PHỦ ĐỊNH trong quy tắc ghép: 'đang tắt' nghĩa là NOT — "
            "bật chế độ khóa làm mất mạng dù công tắc mạng vẫn bật."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: phủ định trong điều kiện ghép — chỗ misconception kinh điển "
            "(học sinh đọc 'khóa đang tắt' thành điều kiện thuận). Cần rule NOT nuôi "
            "rule AND qua trung gian — một biến thể chuỗi KHÁC cấu trúc AND-OR, kiểm "
            "khả năng khái quát của composition thay vì lặp lại một khuôn."
        ),
    ),
    EvalItem(
        id="m11-loop-gap",
        text=(
            "Cho biến x = 2. Mỗi vòng lặp x tăng thêm 3. Vòng lặp dừng khi x lớn hơn "
            "14. Hãy mô phỏng quá trình thay đổi của x qua từng vòng lặp."
        ),
        group="unsupported",
        tags=("boundary", "m11_compose"),
        curriculum_area="T10.CD5",
        curriculum_topic="Câu lệnh lặp trong lập trình (mô phỏng thực thi vòng lặp ngoài năng lực v1)",
        capability_family="control_flow_loop",
        complexity="L4",
        result_mode="unsupported",
        learning_objective="(Ngoài phạm vi v1 — case ranh giới kiểm tính trung thực năng lực.)",
        pedagogical_rationale=(
            "Cơ chế được hỏi là VÒNG LẶP CÓ TRẠNG THÁI với điều kiện dừng theo ngưỡng — "
            "đúng hai gap-role numeric_threshold + arbitrary_algorithm mà manifest cố ý "
            "không cover. LLM tự tính dãy 2→5→8→11→14→17 rồi nhét vào reveal_sequence "
            "sẽ là LLM sở hữu tiến trình canonical (vi phạm R0) — phải unsupported "
            "trung thực, không render ảnh tĩnh giả."
        ),
    ),
]
