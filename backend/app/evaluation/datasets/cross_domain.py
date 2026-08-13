# -*- coding: utf-8 -*-
"""Pool CROSS-DOMAIN — CÙNG năng lực ngữ nghĩa, KHÁC miền bề mặt.

Tuyên bố kiến trúc trung tâm của AlgoSim: định tuyến theo NĂNG LỰC, không theo
tên môn học; một primitive dùng lại được cho nhiều chủ đề. Benchmark cũ hầu như
không kiểm điều này (weighted_sum xuất hiện 2 lần thì cả 2 đều là "công tắc có
trọng số"). Mỗi case dưới đây dùng lại một năng lực ĐÃ CÓ ở một chủ đề KHÁC —
KHÔNG thêm module, KHÔNG thêm primitive.

`cross_domain_group` nối case mới với case lịch sử cùng năng lực:
  boolean_rule   ← a-and (logic.and_gate) / b-xor
  weighted_sum   ← a-binconv (binary) / b-wsum
  node_edge_flow ← a-packet (network.packet_routing)
"""

from __future__ import annotations

from app.evaluation.dataset import EvalItem

CROSS_DOMAIN_ITEMS: list[EvalItem] = [
    EvalItem(
        id="xd-access-boolean",
        text=(
            "Cửa phòng máy của trường chỉ mở khi học sinh vừa quẹt thẻ hợp lệ VÀ vân tay "
            "khớp. Mô phỏng quy tắc mở cửa với hai điều kiện bật/tắt và một đèn báo cửa mở."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "boolean_gate", "op": "and"},
        tags=("cross_domain", "smoke_v2", "flagship"),
        curriculum_area="T11.CD4 / T10.CD2",
        curriculum_topic="Bảo mật, kiểm soát truy cập (Bài 15 / Bài 9)",
        capability_family="boolean_rule",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="boolean_rule",
        learning_objective="Nhận ra kiểm soát truy cập chính là một QUY TẮC LOGIC trên các điều kiện.",
        pedagogical_rationale=(
            "Cơ chế ẩn: quy tắc AND nằm sau một cánh cửa. Học sinh học cổng AND ở bài 'dữ "
            "liệu lôgic' rồi coi nó là chuyện của mạch điện; khi gặp bảo mật lại không nhận "
            "ra cùng một cấu trúc. Bật/tắt từng điều kiện và thấy cửa KHÔNG mở khi thiếu một "
            "điều kiện làm lộ ra quan hệ nhân quả. Dùng lại NGUYÊN năng lực boolean — bằng "
            "chứng 'cùng capability, khác miền', không thêm module nào."
        ),
    ),
    EvalItem(
        id="xd-ascii-weighted",
        text=(
            "Mã ASCII của kí tự 'A' là 65. Mô phỏng bảng 7 công tắc bit có trọng số 64, 32, "
            "16, 8, 4, 2, 1; ban đầu bật các bit sao cho tổng bằng 65. Hiển thị tổng trọng "
            "số của các bit đang bật."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "weighted_sum", "value": 65},
        tags=("cross_domain",),
        curriculum_area="T10.CD1",
        curriculum_topic="Một số kiểu dữ liệu và dữ liệu văn bản (Bài 3) ↔ Hệ nhị phân (Bài 4)",
        capability_family="weighted_sum",
        complexity="L2",
        result_mode="interactive_visualization",
        cross_domain_group="weighted_sum",
        learning_objective="Hiểu mã hoá kí tự dùng ĐÚNG cơ chế trọng số vị trí như đổi số sang nhị phân.",
        pedagogical_rationale=(
            "Cơ chế ẩn: TRỌNG SỐ VỊ TRÍ. Học sinh học 8-4-2-1 ở bài nhị phân rồi học bảng mã "
            "ASCII như một bảng tra cứu thuộc lòng, không thấy đó vẫn là tổng trọng số. Bật/"
            "tắt từng bit và thấy 65 hình thành làm hai bài học nhập lại thành một. Dùng lại "
            "năng lực weighted_sum ở một chủ đề khác."
        ),
    ),
    EvalItem(
        id="xd-order-workflow",
        text=(
            "Mô phỏng quy trình xử lí đơn hàng của một cửa hàng trực tuyến: khách gửi đơn "
            "tới bộ phận kiểm tra kho, kho ghi thông tin vào cơ sở dữ liệu đơn hàng, sau đó "
            "bộ phận giao hàng nhận đơn và giao cho khách. Cho thấy dữ liệu đơn hàng đi qua "
            "từng công đoạn."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "system_flow", "min_directed": 2, "moving": True},
        tags=("cross_domain", "L3", "system_flow", "flagship"),
        curriculum_area="T11.CD4 / T12CS.CD7",
        curriculum_topic="Hệ thống thông tin phục vụ quản lí; mô phỏng trong giải quyết vấn đề (Bài 29)",
        capability_family="data_flow",
        complexity="L3",
        result_mode="executable_simulation",
        cross_domain_group="node_edge_flow",
        learning_objective="Mô tả được một quy trình nghiệp vụ như dữ liệu đi qua các công đoạn xử lí và kho lưu trữ.",
        pedagogical_rationale=(
            "Cơ chế ẩn: dữ liệu KHÔNG nhảy thẳng từ đầu đến cuối — nó dừng lại ở từng công "
            "đoạn, được ghi vào kho, rồi mới đi tiếp. Sơ đồ tĩnh cho thấy các mũi tên nhưng "
            "không cho thấy TRÌNH TỰ. Cho một thực thể dữ liệu chạy qua path làm lộ ra thứ tự "
            "và các điểm dừng. Dùng lại ĐÚNG bộ primitive của định tuyến gói tin "
            "(node+edge+moving_entity+move_along_path) ở một miền hoàn toàn phi mạng — bằng "
            "chứng mạnh nhất cho tuyên bố tái sử dụng năng lực."
        ),
    ),
    # ── WAVE 2A: trả nợ ĐƠN VỊ MỎNG ────────────────────────────────────────
    # Báo cáo phủ đo theo ĐƠN VỊ chương trình, và hai đơn vị dưới ngưỡng 3 case:
    # T10.CD2 (2) và T12CS.CD7 (1). Ba case dưới đây bổ sung đúng hai đơn vị ấy,
    # KHÔNG thêm vào đơn vị vốn đã dày — thêm case thứ 26 cho T11CS.CD6 không
    # làm phép đo tốt hơn chút nào.
    EvalItem(
        id="xd-wifi-access-rule",
        text=(
            "Mạng Wi-Fi của thư viện chỉ cho một thiết bị vào mạng khi thiết bị đã "
            "đăng kí địa chỉ MAC VÀ tài khoản đang trong thời hạn. Mô phỏng quy tắc "
            "cho phép truy cập với hai điều kiện này."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "boolean_rule", "min_inputs": 2},
        tags=("cross_domain", "L2", "boolean_rule", "w2a_thin_unit"),
        curriculum_area="T10.CD2 / T11.CD4",
        curriculum_topic="Mạng máy tính, kiểm soát truy cập (Bài 9 / Bài 15)",
        capability_family="boolean_rule",
        complexity="L2",
        result_mode="executable_simulation",
        cross_domain_group="access_rule",
        learning_objective=(
            "Đọc được một quy tắc truy cập mạng thành phép AND hai điều kiện, và "
            "thấy đủ cả bốn tổ hợp chứ không chỉ tổ hợp cho phép."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: quy tắc mạng viết bằng lời ('chỉ khi … và …') che mất việc "
            "chỉ MỘT trong bốn tổ hợp đầu vào cho kết quả cho-phép. Học sinh đọc câu "
            "đó thường nhớ điều kiện chứ không nhớ nó chặt tới mức nào. Bật/tắt từng "
            "điều kiện và thấy ba tổ hợp còn lại đều bị chặn mới làm lộ ra độ chặt. "
            "Cùng cơ chế với `xd-access-boolean` nhưng bề mặt là hạ tầng mạng thay vì "
            "cửa phòng máy — đo được rằng hệ đọc cơ chế, không khớp mẫu chữ 'quẹt thẻ'."
        ),
    ),
    EvalItem(
        id="xd-library-loan-flow",
        text=(
            "Mô phỏng quy trình mượn sách của thư viện trường: học sinh gửi yêu cầu "
            "tới quầy thủ thư, thủ thư tra sổ mượn trong cơ sở dữ liệu, sau đó kho "
            "sách chuyển cuốn sách ra quầy và giao cho học sinh. Cho thấy yêu cầu "
            "mượn đi qua từng công đoạn."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "system_flow", "min_directed": 2, "moving": True},
        tags=("cross_domain", "L3", "system_flow", "w2a_thin_unit"),
        curriculum_area="T12CS.CD7 / T11.CD4",
        curriculum_topic="Hệ thống thông tin phục vụ quản lí (Bài 29)",
        capability_family="data_flow",
        complexity="L3",
        result_mode="executable_simulation",
        cross_domain_group="node_edge_flow",
        learning_objective=(
            "Mô tả được một nghiệp vụ quản lí quen thuộc như dữ liệu đi qua các công "
            "đoạn xử lí và một kho lưu trữ."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: KHO DỮ LIỆU là một điểm dừng, không phải một mũi tên. Sơ đồ "
            "tĩnh vẽ 'thủ thư → sổ mượn' giống hệt 'thủ thư → kho sách', nên học sinh "
            "không phân biệt được cái nào là tra cứu và cái nào là luân chuyển vật lí. "
            "Cho yêu cầu mượn chạy qua path làm lộ ra thứ tự và các điểm dừng. Cùng bộ "
            "primitive với `xd-order-workflow` ở một nghiệp vụ khác — chứng cứ tái sử "
            "dụng nằm ở chỗ KHÔNG phải viết thêm năng lực nào."
        ),
    ),
    EvalItem(
        id="xd-attendance-report-flow",
        text=(
            "Mô phỏng quy trình tổng hợp báo cáo chuyên cần: giáo viên bộ môn nhập "
            "điểm danh từng tiết, dữ liệu được ghi vào cơ sở dữ liệu của trường, cuối "
            "tuần bộ phận giáo vụ đọc lại và gửi báo cáo cho giáo viên chủ nhiệm."
        ),
        group="generic",
        expect_simulation_id="generic.rule_scene",
        semantic={"kind": "system_flow", "min_directed": 2, "moving": True},
        tags=("cross_domain", "L3", "system_flow", "w2a_thin_unit"),
        curriculum_area="T12CS.CD7",
        curriculum_topic="Hệ thống thông tin phục vụ quản lí (Bài 29)",
        capability_family="data_flow",
        complexity="L3",
        result_mode="executable_simulation",
        cross_domain_group="node_edge_flow",
        learning_objective=(
            "Nhận ra dữ liệu được GHI ở một thời điểm và ĐỌC LẠI ở thời điểm khác, "
            "chứ không đi thẳng từ người nhập tới người nhận."
        ),
        pedagogical_rationale=(
            "Cơ chế ẩn: ĐỘ TRỄ giữa ghi và đọc. Đây là điểm khác biệt thật giữa một "
            "hệ thống thông tin và một cuộc trao đổi trực tiếp, và là thứ lời văn giấu "
            "kĩ nhất — câu 'giáo vụ đọc lại' nghe như bước kế tiếp, trong khi nó xảy "
            "ra sau nhiều lượt ghi. Cho từng lượt điểm danh chạy vào kho rồi mới cho "
            "lượt đọc chạy ra làm lộ ra rằng kho đứng GIỮA hai người, không nối họ."
        ),
    ),
]
