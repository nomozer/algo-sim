# -*- coding: utf-8 -*-
"""GENERATION_EQUIVALENCE — envelope sinh ra phải mang TIMELINE, không chỉ khung đầu.

Cập nhật 2026-08-20 theo hợp đồng mới (bất biến #31). Bản cũ assert
`config["objects"]` và `config["processes"][0]["steps"]` — hai khoá đó thuộc
DSL `generic.rule_scene`, và chính vì chỉ kiểm chúng mà lỗi E1 (giữ khung đầu,
vứt phần còn lại) đi lọt qua toàn bộ suite: `objects` vẫn > 0 và `steps` vẫn
> 5 kể cả khi mọi khung sau bị vứt.

Hợp đồng mới: `config["frames"]` (toàn bộ chuỗi khung) + `config["view_steps"]`
(phân nhịp trình bày).
"""
import pytest

from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
)

from .fixtures_coverage_18 import (
    P01_STACK_BRACKET,
    P03_BINARY_SEARCH,
    P04_BUBBLE_SORT,
    P09_GRAPH_BFS,
)

CASES = [
    (P01_STACK_BRACKET, 5),
    (P03_BINARY_SEARCH, 3),
    (P04_BUBBLE_SORT, 5),
    (P09_GRAPH_BFS, 5),
]


@pytest.mark.parametrize("spec,min_steps", CASES, ids=lambda x: getattr(x, "title", "")[:22])
def test_compile_to_envelope_mang_timeline(spec, min_steps):
    envelope = compile_semantic_program_to_envelope(spec)

    assert envelope["status"] == "ok"
    assert envelope["domain"] == "generic"
    assert envelope["simulation_id"] == "generic.semantic_program"
    assert envelope["visual_mode"] == "2d"

    cfg = envelope["config"]
    assert len(cfg["frames"]) > min_steps, "Timeline quá ngắn so với thuật toán"
    assert len(cfg["view_steps"]) > 0

    # Mỗi khung phải mang trạng thái RIÊNG của nó, không phải bản sao khung đầu.
    assert all("objects" in f for f in cfg["frames"])

    # Phân hoạch của pacer phủ đầy đủ dãy khung (bất biến #32).
    vs = cfg["view_steps"]
    assert vs[0]["frame_lo"] == 0
    assert vs[-1]["frame_hi"] == len(cfg["frames"]) - 1

    # Cấm cắt câm: chạm trần thực thi thì phải KHAI, không lặng lẽ giao một phần.
    assert cfg["execution_truncated"] is False


def test_timeline_that_su_dien_tien_khong_lap_lai_khung_dau():
    """Hồi quy cho E1: nếu mọi khung giống khung đầu thì đây là bug cũ quay lại."""
    cfg = compile_semantic_program_to_envelope(P04_BUBBLE_SORT)["config"]
    first = cfg["frames"][0]["objects"]
    assert any(f["objects"] != first for f in cfg["frames"][1:]), (
        "Mọi khung trùng khung đầu — hình đóng băng, lỗi E1 đã quay lại"
    )
