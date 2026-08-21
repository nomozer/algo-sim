# -*- coding: utf-8 -*-
"""`graph_view` — primitive thị giác cho `MemoryType` đã được admit (2026-08-21).

VÌ SAO NÓ ĐƯỢC THÊM, và vì sao đó KHÔNG phải "cứu một ca":
`graph` là một `MemoryType` hệ thống đã thừa nhận và eligibility rubric §7.2 đã
nhận bài đồ thị vào population từ trước. Nhưng hợp đồng THỊ GIÁC không có cách
nào biểu diễn nó — L5a chụp được hậu quả: bài BFS chạy đúng mà trên màn hình chỉ
thấy hàng đợi, cơ chế trung tâm (đi qua đỉnh nào, thứ tự nào) không xuất hiện.
Đó là khoảng trống của HỢP ĐỒNG, không phải nhu cầu của một bài.

RANH GIỚI v1 (chốt cùng lúc): 2D · đọc topology từ snapshot · layout tất định ·
KHÔNG physics · KHÔNG camera/zoom · KHÔNG editor · KHÔNG renderer riêng theo
thuật toán · KHÔNG thêm statement kind / MemoryType / checker.

ĐIỀU QUAN TRỌNG NHẤT: renderer **không bao giờ tự suy ra** đỉnh nào đã thăm.
Chương trình KHAI BÁO biến mang trạng thái đó (`visited_ref`/`current_ref`), và
adapter đọc thẳng từ `memory_snapshot`. Tự chạy lại BFS trong tầng trình bày là
dựng một engine thứ hai — đúng thứ R0 cấm.
"""
import typing

import pytest

from app.simulation.semantic_program.contract import (
    VisualContainerBinding,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import (
    VisualBindingUnresolved,
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter
from tests.semantic_program.fixtures_coverage_18 import P09_GRAPH_BFS


def _graph_objects(spec):
    exec_res = SemanticProgramInterpreter(max_steps=300).execute(spec)
    frames = VisualTraceAdapter(spec).adapt(exec_res)
    return [
        [o for o in f.objects if o.get("type") == "graph_view"]
        for f in frames
    ]


def test_graph_view_co_trong_enum_va_co_nhanh_adapter():
    """Bất biến #33 áp cho primitive mới ngay từ đầu."""
    declared = set(
        typing.get_args(VisualContainerBinding.model_fields["primitive"].annotation)
    )
    assert "graph_view" in declared
    assert "graph_view" in VisualTraceAdapter.HANDLED_PRIMITIVES


def test_topology_doc_tu_snapshot_khong_bia():
    per_frame = _graph_objects(P09_GRAPH_BFS)
    assert per_frame and per_frame[0], "không dựng được object graph_view nào"
    g = per_frame[0][0]

    # Đúng tập đỉnh của đề: 1..5
    assert g["nodes"] == ["1", "2", "3", "4", "5"]

    # Cạnh KHÔNG hướng, đã chuẩn hoá và không trùng lặp.
    assert ["1", "2"] in g["edges"]
    assert ["3", "5"] in g["edges"]
    assert len(g["edges"]) == len({tuple(e) for e in g["edges"]})
    for u, v in g["edges"]:
        assert u <= v, "cạnh chưa chuẩn hoá ⇒ cùng một cạnh đếm hai lần"


def test_trang_thai_dinh_LON_DAN_theo_buoc_va_doc_tu_bien_khai_bao():
    """`visited` phải đi theo BIẾN THẬT trong snapshot, không do renderer đoán."""
    per_frame = _graph_objects(P09_GRAPH_BFS)
    sizes = [len(fr[0].get("visited", [])) for fr in per_frame if fr]
    assert sizes[0] == 0, "khung đầu đã có đỉnh thăm ⇒ không đọc từ snapshot"
    assert max(sizes) >= 3, "tập đã thăm không lớn lên ⇒ đồ thị đứng yên"
    assert sizes == sorted(sizes), "tập đã thăm co lại — không thể xảy ra với BFS"


def test_dinh_dang_xet_thay_doi_doc_timeline():
    per_frame = _graph_objects(P09_GRAPH_BFS)
    currents = [fr[0].get("current") for fr in per_frame if fr]
    assert len({c for c in currents if c}) >= 2, "đỉnh đang xét không bao giờ đổi"


def test_khong_khai_tham_chieu_thi_KHONG_to_trang_thai():
    """Không khai thì im lặng — KHÔNG được đoán bằng cách chạy lại BFS."""
    spec = P09_GRAPH_BFS.model_copy(deep=True)
    for cb in spec.visual_bindings.containers:
        if cb.primitive == "graph_view":
            cb.visited_ref = None
            cb.current_ref = None
    g = _graph_objects(spec)[-1][0]
    assert "visited" not in g
    assert "current" not in g
    # nhưng topology thì vẫn phải có
    assert g["nodes"]


def test_graph_view_buoc_vao_container_khong_ton_tai_thi_fail_closed():
    """Bất biến #34 áp cho primitive mới — không render một phần.

    Ai bắt: `validator.py` bắt TĨNH (container chưa khai báo là kiểm được mà
    không cần chạy) và ném `ValueError`; `_assert_bindings_resolvable` là lưới
    thứ hai cho những gì chỉ lộ ra lúc chạy. Test nhận cả hai vì điều phải giữ
    là **không phát envelope**, không phải "đúng lớp ngoại lệ nào".
    """
    spec = P09_GRAPH_BFS.model_copy(deep=True)
    for cb in spec.visual_bindings.containers:
        if cb.primitive == "graph_view":
            cb.semantic_id = "do_thi_ma"
    with pytest.raises((VisualBindingUnresolved, ValueError)):
        compile_semantic_program_to_envelope(spec)


def test_envelope_mang_graph_view_qua_duoc_toan_bo_duong():
    env = compile_semantic_program_to_envelope(P09_GRAPH_BFS)
    kinds = {
        o["type"]
        for f in env["config"]["frames"]
        for o in f["objects"]
    }
    assert "graph_view" in kinds
