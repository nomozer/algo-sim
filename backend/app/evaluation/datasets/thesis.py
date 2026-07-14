# -*- coding: utf-8 -*-
"""Pool THESIS — bộ flagship đại diện cho luận văn (12 case).

Tiêu chí chọn: mỗi case chứng minh MỘT tính chất sư phạm hoặc kiến trúc RIÊNG.
Không nhồi biến thể AND/OR/XOR chứng minh lặp lại cùng một năng lực.

Phần lớn case là THAM CHIẾU tới đề đã có (lịch sử hoặc pool mới) — bộ flagship là
một CÁCH CHỌN, không phải một tập đề mới. Nhờ vậy không phát sinh đề trùng.

Bảng: case → điều nó chứng minh
  cap-bubble          sắp xếp — engine có sẵn nhưng TRƯỚC ĐÂY KHÔNG có bằng chứng
  cur-t11cs-binsearch định tuyến theo NĂNG LỰC ("tìm nhanh"/"đã sắp xếp" → chia đôi)
  a-sumif             điều kiện + biến tích luỹ; và capability gate KHÔNG nổ oan
  a-binconv           biểu diễn dữ liệu (trọng số vị trí)
  b-xor               DSL generic compose được cổng logic
  a-and               engine chuyên biệt cho cùng khái niệm → cặp với b-xor chứng
                      minh ranh giới specialized ↔ generic (DUY NHẤT được phép trùng)
  a-packet            đường đi do BFS TẤT ĐỊNH sinh, không phải LLM
  d-webbuild          cấu trúc + thời gian (hình thành từng bước)
  d-webstatic         TRUNG THỰC scene-mode: cảnh tĩnh KHÔNG được giả vờ có diễn biến
  xd-access-boolean   TÁI SỬ DỤNG năng lực: boolean ở miền bảo mật, không thêm module
  xd-order-workflow   TÁI SỬ DỤNG node+edge+moving_entity ngoài miền mạng (S2)
  c-geo-complex       TỪ CHỐI TRUNG THỰC bài "nhìn có vẻ vẽ được" → capability_gap
"""

from __future__ import annotations

from dataclasses import replace

from app.evaluation.dataset import DATASET, EvalItem
from app.evaluation.datasets.capability import CAPABILITY_ITEMS
from app.evaluation.datasets.cross_domain import CROSS_DOMAIN_ITEMS
from app.evaluation.datasets.curriculum import CURRICULUM_ITEMS

_BY_ID: dict[str, EvalItem] = {
    it.id: it for it in (*DATASET, *CURRICULUM_ITEMS, *CAPABILITY_ITEMS, *CROSS_DOMAIN_ITEMS)
}

# Case lịch sử được viết TRƯỚC khi có metadata → mang giá trị mặc định (complexity
# "L1", result_mode None). Bộ flagship cần nhãn ĐÚNG, nhưng dataset.py ĐÓNG BĂNG.
# Giải: `dataclasses.replace` tạo BẢN SAO có nhãn — DATASET không hề bị sửa
# (khoá bằng test_datasets::test_flagship_khong_mutate_dataset_lich_su).
_ANNOTATIONS: dict[str, dict] = {
    "a-sumif": dict(
        curriculum_area="T10.CD5", curriculum_topic="Lặp + rẽ nhánh trên dãy số",
        capability_family="conditional_accumulator", complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Hiểu biến tích luỹ là trạng thái sống sót qua các vòng lặp.",
        pedagogical_rationale=(
            "Cơ chế ẩn: giá trị của biến tổng GIỮA các vòng lặp và điều kiện quyết định có "
            "cộng hay không — thứ học sinh không thấy khi chỉ nhìn kết quả cuối."
        ),
    ),
    "a-binconv": dict(
        curriculum_area="T10.CD1", curriculum_topic="Hệ nhị phân (Bài 4)",
        capability_family="data_representation", complexity="L1",
        result_mode="executable_simulation", cross_domain_group="weighted_sum",
        learning_objective="Đổi thập phân sang nhị phân và giải thích trọng số từng bit.",
        pedagogical_rationale="Cơ chế ẩn: đóng góp trọng số của từng bit vào giá trị cuối.",
    ),
    "b-xor": dict(
        curriculum_area="T10.CD1", curriculum_topic="Dữ liệu lôgic (Bài 5)",
        capability_family="boolean_rule", complexity="L1",
        result_mode="interactive_visualization", cross_domain_group="boolean_rule",
        learning_objective="Đầu ra phụ thuộc TỔ HỢP đầu vào, không phải từng đầu vào riêng lẻ.",
        pedagogical_rationale=(
            "Cơ chế ẩn: bảng chân trị nằm sau một bóng đèn. Chứng minh DSL generic compose "
            "được cổng logic mà không cần engine riêng."
        ),
    ),
    "a-and": dict(
        curriculum_area="T10.CD1", curriculum_topic="Dữ liệu lôgic (Bài 5)",
        capability_family="boolean_rule", complexity="L1",
        result_mode="interactive_visualization", cross_domain_group="boolean_rule",
        learning_objective="Hiểu cổng AND qua thao tác bật/tắt hai đầu vào.",
        pedagogical_rationale=(
            "Cùng khái niệm với b-xor nhưng chạy bằng ENGINE CHUYÊN BIỆT — cặp a-and/b-xor "
            "là bằng chứng ranh giới specialized ↔ generic. Trùng lặp DUY NHẤT được phép."
        ),
    ),
    "a-packet": dict(
        curriculum_area="T12.CD2", curriculum_topic="Đường đi của gói tin (Bài 3–4)",
        capability_family="node_edge_graph+movement", complexity="L2",
        result_mode="executable_simulation", cross_domain_group="node_edge_flow",
        learning_objective="Hiểu gói tin đi qua từng chặng và đường đi được TÍNH RA từ topology.",
        pedagogical_rationale=(
            "Cơ chế ẩn: các chặng trung gian. Đường đi do BFS TẤT ĐỊNH sinh — bằng chứng LLM "
            "không hề sinh timeline."
        ),
    ),
    "d-webbuild": dict(
        curriculum_area="T12.CD4", curriculum_topic="HTML và cấu trúc trang web (Bài 7)",
        capability_family="structural_construction", complexity="L2",
        result_mode="executable_simulation",
        learning_objective="Hiểu trang web là cấu trúc lồng nhau được lắp ghép dần.",
        pedagogical_rationale=(
            "Cơ chế ẩn: trình tự dựng và quan hệ chứa nhau của các phần tử — ảnh chụp trang "
            "hoàn chỉnh không cho thấy điều đó."
        ),
    ),
    "d-webstatic": dict(
        curriculum_area="T12.CD4", curriculum_topic="Cấu trúc trang web (Bài 7)",
        capability_family="structural_static", complexity="L1",
        result_mode="interactive_visualization",
        learning_objective="Xem cấu trúc một trang web cho sẵn.",
        pedagogical_rationale=(
            "Giá trị nằm ở chỗ hệ TỪ CHỐI bịa diễn biến: đề 'hiển thị cấu trúc' phải ra cảnh "
            "TĨNH, không được gắn reveal giả. Bằng chứng trung thực scene-mode."
        ),
    ),
    "c-geo-complex": dict(
        curriculum_area="Ngoài chương trình Tin học (Toán hình)",
        curriculum_topic="Quan hệ hình học dẫn xuất (chân đường cao, giao điểm, quỹ tích)",
        capability_family="capability_gap", complexity="L4", result_mode="unsupported",
        learning_objective="(không mô phỏng — hệ phải từ chối trung thực)",
        pedagogical_rationale=(
            "Bài 'nhìn có vẻ vẽ được' bằng node/edge. Nếu để LLM đoán toạ độ sẽ ra hình SAI "
            "BẢN CHẤT (kéo M thì E/F/P đứng yên) — dạy sai còn tệ hơn không dạy. Case quan "
            "trọng nhất của luận văn: chứng minh hệ thà từ chối còn hơn mô phỏng xấp xỉ."
        ),
    ),
}


def _flagship(item_id: str) -> EvalItem:
    base = _BY_ID[item_id]
    ann = _ANNOTATIONS.get(item_id)
    return replace(base, **ann) if ann else base

FLAGSHIP_IDS: tuple[str, ...] = (
    "cap-bubble",           # L2 · sắp xếp (lỗ hổng bằng chứng lớn nhất trước M8)
    "cur-t11cs-binsearch",  # L2 · tìm kiếm nhị phân
    "a-sumif",              # L2 · điều kiện + tích luỹ (+ gate không nổ oan)
    "a-binconv",            # L1 · biểu diễn dữ liệu
    "b-xor",                # L1 · boolean qua DSL generic
    "a-and",                # L1 · boolean qua engine chuyên biệt (cặp có chủ đích)
    "a-packet",             # L2 · định tuyến tất định
    "d-webbuild",           # L2 · cấu trúc + thời gian
    "d-webstatic",          # L1 · trung thực scene-mode (tĩnh vẫn là tĩnh)
    "xd-access-boolean",    # L2 · tái sử dụng năng lực (khác miền)
    "xd-order-workflow",    # L3 · luồng dữ liệu chạy được (sau S2)
    "c-geo-complex",        # L4 · từ chối trung thực (capability_gap)
)

FLAGSHIP_ITEMS: list[EvalItem] = [_flagship(i) for i in FLAGSHIP_IDS]
