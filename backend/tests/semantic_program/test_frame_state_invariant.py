# -*- coding: utf-8 -*-
"""Bất biến #31 — khung hình thứ k suy hoàn toàn từ bước k của trace; envelope mang CẢ timeline (bất biến #32).

Lịch sử: `pipeline_adapter` từng giữ `frames[0]` rồi vứt mọi khung sau (spec 2026-08-20 E1) — thuyết minh chạy tới
bước 15 trong khi hình đứng ở bước 0. Bản trước của file này (và `test_generation_equivalence.py`) khoá điều đó bằng
chương trình Tin học (ngăn xếp, sắp xếp nổi bọt, BFS). /13 gỡ miền Tin học, nên cùng hai bất biến được khoá trên một
chương trình HÌNH HỌC: khung không còn đối tượng 2D (hình đi bằng `scene3d`), nhưng timeline frontend vẫn tua theo
chính dãy khung này, nên "khung k ⇔ trace[k]" và "pacer phủ đủ dãy" vẫn là thứ phải giữ.
"""
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
    validate_semantic_envelope_config,
)

_SPEC = SemanticProgramSpec.model_validate({
    "spec_version": "1.0",
    "title": "Thiết diện qua ba trung điểm",
    "memory_declarations": [
        *({"name": n, "type": "point3", "initial_value": v}
          for n, v in (("A", [0, 0, 0]), ("B", [2, 0, 0]), ("C", [2, 2, 0]), ("D", [0, 2, 0]), ("S", [0, 0, 4]))),
        {"name": "M", "type": "point3"}, {"name": "N", "type": "point3"}, {"name": "P", "type": "point3"},
        {"name": "chop", "type": "solid"}, {"name": "mp", "type": "plane3"}, {"name": "td", "type": "section"},
    ],
    "statements": [
        {"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD", "vertices": ["A", "B", "C", "D", "S"],
         "faces": [["A", "B", "C", "D"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "D"], ["S", "D", "A"]]},
        {"kind": "construct_point", "target_var": "M", "label": "M", "expr": {"kind": "midpoint", "a": "S", "b": "A"}},
        {"kind": "construct_point", "target_var": "N", "label": "N", "expr": {"kind": "midpoint", "a": "S", "b": "B"}},
        {"kind": "construct_point", "target_var": "P", "label": "P", "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
        {"kind": "construct_plane", "target_var": "mp", "label": "(MNP)", "through": ["M", "N", "P"]},
        {"kind": "construct_section", "target_var": "td", "label": "thiết diện", "solid": "chop", "plane": "mp"},
    ],
})


def test_khung_k_la_buoc_k_cua_trace_va_envelope_giu_du_moi_khung():
    trace = SemanticProgramInterpreter(max_steps=300).execute(_SPEC).trace
    cfg = compile_semantic_program_to_envelope(_SPEC)["config"]
    assert len(cfg["frames"]) == len(trace) > 5, "envelope phải giữ MỌI khung, không chỉ khung đầu (lỗi E1)"
    for k, (khung, buoc) in enumerate(zip(cfg["frames"], trace)):
        assert khung["step_index"] == buoc.step_index == k
        assert khung["narration"] == buoc.tier1_narration       # không `pedagogical_intent` ⇒ đúng Tier 1 của bước k
    # Thuyết minh diễn tiến — không phải mọi khung lặp lại khung đầu.
    assert len({f["narration"] for f in cfg["frames"]}) > 1


def test_pacer_phu_du_day_khung_va_khong_cat_cam():
    cfg = compile_semantic_program_to_envelope(_SPEC)["config"]
    assert validate_semantic_envelope_config(cfg) is None
    vs = cfg["view_steps"]
    assert vs[0]["frame_lo"] == 0 and vs[-1]["frame_hi"] == len(cfg["frames"]) - 1
    assert cfg["execution_truncated"] is False
