# -*- coding: utf-8 -*-
"""G04 — lăng trụ xiên (run `oblique-prism`). 0 lượt gọi model.

Nhãn ghi trước: `docs/evaluation/geometry/runs/oblique-prism/labels.json`, giá trị phục vụ kiểm bằng `oracle.py` (chỉ
từ kích thước của đề). Mỗi hàng chạy HAI tuyến:
  · compiler — `GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST` qua `run_pipeline` (0 lượt gọi synthesis);
  · LLM_ONLY — chương trình kiểu mô hình viết tay (`chart`) qua `verify_and_compile`: năng lực HỆ, không phải bằng
    chứng mô hình sinh được chương trình ấy.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import subprocess
import sys
from fractions import Fraction

import pytest

from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.route import verify_and_compile

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/oblique-prism"
ROWS = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
BAT = {"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"}


def _payload(r: dict) -> dict:
    facts = [{"id": f"fact_{k}", "kind": "float", "label": k, "value": [v]} for k, v in r["lengths"].items()]
    rels = []
    if r["right_angle"]:
        a, b, c, d = r["right_angle"]
        rels.append({"kind": "perpendicular_lines", "line": [a, b], "other_line": [c, d],
                     "source_fact_id": "fact_base_right_angle", "model_assumption": False})
        facts.append({"id": "fact_base_right_angle", "kind": "str", "label": "góc vuông của đáy",
                      "value": [f"{a}{b} ⊥ {c}{d}"]})
    if r["perp"]:
        p = r["perp"]
        rels.append({"kind": "perpendicular_line_plane", "line": p["line"], "plane": p["plane"],
                     "source_fact_id": "fact_lateral_foot", "model_assumption": False})
        facts.append({"id": "fact_lateral_foot", "kind": "str", "label": "đường vuông góc với đáy",
                      "value": ["".join(p["line"]) + " ⊥ (" + "".join(p["plane"]) + ")"]})
    t = r["topology"]
    topo = {"solid_kind": "prism", "base_cycle": t["base"], "top_cycle": t["top"],
            "correspondence": [list(x) for x in zip(t["base"], t["top"])]}
    for k in ("lateral_structure", "base_shape"):
        if t.get(k):
            topo[k] = t[k]
    return {"input_facts": facts, "geometric_relations": rels, "solid_topology": topo,
            "obligations": [{"kind": "volume", "container": "khoi_lang_tru", "witness": "V"}]}


def hop_dong(rid: str):
    r = ROWS[rid]
    return build_request_contract(_payload(r), problem_text=r["text"], domain="hinh_hoc")


def chuong_trinh_kieu_llm(rid: str) -> SemanticProgramSpec:
    """Cách một mô hình viết lăng trụ xiên: khai mọi đỉnh bằng toạ độ (kèm lý do), một khối, đo thể tích."""
    r = ROWS[rid]
    ch, t = r["chart"], r["topology"]
    k = len(t["base"])
    dinh = [*t["base"], *t["top"]]
    mat = [list(range(k)), list(range(k, 2 * k))] + [[i, (i + 1) % k, k + (i + 1) % k, k + i] for i in range(k)]
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Thể tích lăng trụ xiên",
        "memory_declarations": [
            *({"name": p, "type": "point3", "initial_value": [str(c) for c in ch[p]],
               "model_assumption": "Đặt điểm trong hệ trục tiện dựng"} for p in dinh),
            {"name": "lang_tru", "type": "solid"}, {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "lang_tru", "vertices": dinh,
             "faces": [[dinh[i] for i in f] for f in mat]},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "lang_tru"}},
        ]})


# ══ ORACLE ══════════════════════════════════════════════════════════════════
def test_oracle_doc_lap_dong_y_voi_nhan():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


# ══ TUYẾN LLM_ONLY (chương trình kiểu mô hình) ══════════════════════════════
@pytest.mark.parametrize("rid", sorted(ROWS))
def test_llm_only_theo_nhan(rid):
    e = ROWS[rid]["expect"]["llm"]
    sp = chuong_trinh_kieu_llm(rid)
    out = verify_and_compile(hop_dong(rid), sp)
    if e.startswith("served:"):
        assert out.servable, (out.stage_reached, out.reason_code, out.details)
        mem = SemanticProgramInterpreter().execute(sp).final_memory
        assert Fraction(str(mem["V"])) == Fraction(e.split(":", 1)[1])
    else:
        assert not out.servable
        if ":" in e:
            assert out.reason_code == e.split(":", 1)[1], (out.reason_code, out.details)
