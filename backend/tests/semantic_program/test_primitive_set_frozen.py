# -*- coding: utf-8 -*-
"""TẬP VISUAL PRIMITIVE — ĐÓNG BĂNG (2026-08-21).

Luật (spec §1.1, sửa cách diễn đạt cùng ngày):

    Tập primitive/type được phép HOÀN THIỆN TỪ DEV cho tới khi SEALED được niêm
    phong; sau thời điểm đó thì ĐÓNG BĂNG, và KHÔNG BAO GIỜ mở thêm vì một kết
    quả SEALED.

Vì sao câu đó phải viết lại: bản đầu ghi "không mở primitive/type mới", và nó tự
mâu thuẫn với chính quy trình — `graph_view` được thêm vào 2026-08-21 vì L5a phơi
ra rằng `graph` là một `MemoryType` đã được admit mà hợp đồng thị giác không có
cách nào biểu diễn. Mở vì **một lớp trạng thái đã admit** thì hợp lệ; mở vì **một
ca chạy chưa đẹp** thì không.

Test này là chỗ ranh giới ấy trở thành thứ cưỡng chế được. Đổi danh sách dưới đây
là ĐỎ, và người đổi phải trả lời: thay đổi đến từ DEV hay từ một case SEALED?
"""
import typing

from app.simulation.semantic_program.contract import VisualContainerBinding
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter

PRIMITIVE_DA_DONG_BANG = {
    "array_strip",
    "stack_view",
    "queue_view",
    "table_grid",
    "tree_element",
    "bit_register",
    "bar_chart",
    "graph_view",  # thêm 2026-08-21 — xem docstring
    # thêm 2026-08-23, CÙNG KHUÔN với `graph_view` và cùng lý do: `map` là một
    # `MemoryType` đã admit mà hợp đồng thị giác không biểu diễn được. Cổng bề
    # mặt học sinh (`learner_surface.py`) phơi ra trên fixture #18 — chương trình
    # dựng bảng tần suất suốt lượt chạy, màn hình không bao giờ có bảng.
    # Nguồn: DEV. KHÔNG phải từ một ca SEALED.
    "map_view",
}

#: Cố ý KHÔNG có mặt, ghi kèm lý do để lần sau khỏi "bổ sung cho đủ".
CO_Y_KHONG_CO = {
    "graph_editor": "học sinh sửa đồ thị là ĐỔI ĐỀ BÀI, không phải tham gia cơ chế",
    "force_layout": "layout phải TẤT ĐỊNH — force-directed cho hình khác nhau mỗi lượt, ảnh chụp hết so được",
    "camera_3d": "route này 2D only (MVP §1.1); 3D không giúp chứng minh claim NL→IR→thực thi→trace",
}


def _khai_trong_contract() -> set[str]:
    return set(
        typing.get_args(VisualContainerBinding.model_fields["primitive"].annotation)
    )


def test_tap_primitive_dung_ban_da_dong_bang():
    assert _khai_trong_contract() == PRIMITIVE_DA_DONG_BANG, (
        "Tập visual primitive đã đổi. Câu hỏi bắt buộc trước khi sửa test này: "
        "thay đổi đến từ DEV hay từ một case SEALED? Từ SEALED ⇒ seal MẤT HIỆU "
        "LỰC (spec §7.4, hard scope lock §1.1)."
    )


def test_adapter_phu_dung_bang_do_khong_thua_khong_thieu():
    """Bất biến #33 — hai chiều, để lỗi câm không quay lại."""
    assert VisualTraceAdapter.HANDLED_PRIMITIVES == PRIMITIVE_DA_DONG_BANG


def test_khong_lang_le_them_lai_cai_da_co_y_loai():
    lan_vao = sorted(set(CO_Y_KHONG_CO) & _khai_trong_contract())
    assert not lan_vao, (
        "Primitive đã cố ý loại nay lại có mặt: "
        + "; ".join(f"{k} — {CO_Y_KHONG_CO[k]}" for k in lan_vao)
    )
