# -*- coding: utf-8 -*-
"""Bất biến #31 — khung hình thứ k suy hoàn toàn từ trạng thái bước k.

Test này ĐỎ trước khi Task 3 sửa: `pipeline_adapter` hiện chỉ giữ
`frames[0].objects` rồi vứt mọi khung sau (spec 2026-08-20 E1) — nên lời
thuyết minh chạy tới bước 15 trong khi hình vẫn đứng ở bước 0.
"""
import pytest

from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.validator import validate_semantic_program
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter
from tests.semantic_program.fixtures_coverage_18 import (
    P01_STACK_BRACKET,
    P02_FIND_MAX,
    P09_GRAPH_BFS,
)


def _frames_of(spec):
    val = validate_semantic_program(spec)
    assert val.ok, val.error
    exec_res = SemanticProgramInterpreter(max_steps=300).execute(spec)
    return VisualTraceAdapter(spec).adapt(exec_res)


@pytest.mark.parametrize(
    "spec", [P01_STACK_BRACKET, P02_FIND_MAX, P09_GRAPH_BFS], ids=lambda s: s.title[:24]
)
def test_envelope_giu_du_moi_khung_cua_adapter(spec):
    frames = _frames_of(spec)
    env = compile_semantic_program_to_envelope(spec)

    cfg_frames = env["config"]["frames"]
    assert len(cfg_frames) == len(frames), (
        f"Envelope giữ {len(cfg_frames)} khung nhưng adapter sinh {len(frames)}"
    )
    for k, f in enumerate(frames):
        assert cfg_frames[k]["objects"] == f.objects, (
            f"Khung {k} lệch trạng thái: envelope không phản ánh memory_snapshot"
        )


def test_ngan_xep_khong_dong_bang_o_khung_0():
    """Hồi quy TRỰC TIẾP cho ảnh chụp ở spec §0(b).

    Trên ảnh: thuyết minh đọc "lấy '[' ra khỏi ngăn xếp, so với ']', khớp nhau"
    — chính xác từng chi tiết — trong khi ngăn xếp trên hình RỖNG.
    """
    env = compile_semantic_program_to_envelope(P01_STACK_BRACKET)
    stacks = [
        obj
        for frame in env["config"]["frames"]
        for obj in frame["objects"]
        if obj.get("type") == "stack_view"
    ]
    assert stacks, "Không có stack_view nào trong timeline"
    assert any(s.get("items") for s in stacks), (
        "Mọi khung đều có ngăn xếp RỖNG — hình đóng băng ở bước 0 (lỗi E1)"
    )


def test_gia_tri_bien_doi_theo_thoi_gian_khong_dung_yen():
    """value_box phải đổi giá trị dọc timeline, không kẹt ở khởi tạo."""
    env = compile_semantic_program_to_envelope(P02_FIND_MAX)
    seen: dict[str, set] = {}
    for frame in env["config"]["frames"]:
        for obj in frame["objects"]:
            if obj.get("type") == "value_box":
                seen.setdefault(obj["id"], set()).add(repr(obj.get("value")))
    assert seen, "Không có value_box nào"
    assert any(len(vals) > 1 for vals in seen.values()), (
        "Mọi value_box giữ nguyên một giá trị suốt timeline — hình không diễn tiến"
    )
