# -*- coding: utf-8 -*-
"""G05 — chóp / lăng trụ đứng đáy đa giác xác định bởi chuỗi góc vuông (run `general-polygon-base`). 0 lượt gọi model.

Nhãn ghi trước: `docs/evaluation/geometry/runs/general-polygon-base/labels.json`, giá trị phục vụ kiểm bằng `oracle.py`
(chỉ từ kích thước của đề). Mỗi hàng chạy HAI tuyến: compiler (`DETERMINISTIC_FIRST` qua `run_pipeline`, 0 lượt gọi
synthesis) và LLM_ONLY với chương trình kiểu mô hình viết tay qua `verify_and_compile` — năng lực HỆ, không phải bằng
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
from app.simulation.semantic_program.shape_constraint import doc_rang_buoc, phan_chua_doc

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/general-polygon-base"
ROWS = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
BAT = {"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"}
DUONG = sorted(r for r in ROWS if ROWS[r]["expect"]["compiler"].startswith("served"))


def _payload(r: dict) -> dict:
    facts = [{"id": f"fact_{k}", "kind": "float", "label": k, "value": [v]} for k, v in r["lengths"].items()]
    rels = []
    for i, (a, b, c, d) in enumerate(r["right_angles"]):
        rels.append({"kind": "perpendicular_lines", "line": [a, b], "other_line": [c, d],
                     "source_fact_id": f"fact_right_{i}", "model_assumption": False})
        facts.append({"id": f"fact_right_{i}", "kind": "str", "label": "góc vuông của đáy", "value": [f"{a}{b} ⊥ {c}{d}"]})
    if r["perp"]:
        p = r["perp"]
        rels.append({"kind": "perpendicular_line_plane", "line": p["line"], "plane": p["plane"],
                     "source_fact_id": "fact_perp", "model_assumption": False})
        facts.append({"id": "fact_perp", "kind": "str", "label": "đường vuông góc với đáy",
                      "value": ["".join(p["line"]) + " ⊥ (" + "".join(p["plane"]) + ")"]})
    t = r["topology"]
    if t["solid_kind"] == "pyramid":
        topo = {"solid_kind": "pyramid", "apex": t["apex"], "base_cycle": t["base"]}
    else:
        topo = {"solid_kind": "prism", "base_cycle": t["base"], "top_cycle": t["top"],
                "correspondence": [list(x) for x in zip(t["base"], t["top"])]}
    return {"input_facts": facts, "geometric_relations": rels, "solid_topology": topo,
            "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}]}


def hop_dong(rid: str):
    r = ROWS[rid]
    return build_request_contract(_payload(r), problem_text=r["text"], domain="hinh_hoc")


def _dinh_mat(t: dict) -> tuple[list[str], list[list[str]]]:
    day, k = t["base"], len(t["base"])
    if t["solid_kind"] == "pyramid":
        return [t["apex"], *day], [list(day)] + [[t["apex"], day[i], day[(i + 1) % k]] for i in range(k)]
    tren = t["top"]
    return [*day, *tren], [list(day), list(tren)] + [[day[i], day[(i + 1) % k], tren[(i + 1) % k], tren[i]]
                                                      for i in range(k)]


def chuong_trinh_kieu_llm(rid: str) -> SemanticProgramSpec:
    ch = ROWS[rid]["chart"]
    dinh, mat = _dinh_mat(ROWS[rid]["topology"])
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Thể tích khối đa diện",
        "memory_declarations": [
            *({"name": p, "type": "point3", "initial_value": [str(c) for c in ch[p]],
               "model_assumption": "Đặt điểm trong hệ trục tiện dựng"} for p in dinh),
            {"name": "khoi", "type": "solid"}, {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "khoi", "vertices": dinh, "faces": mat},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}},
        ]})


# ══ ORACLE · BỘ ĐỌC NGUỒN ═══════════════════════════════════════════════════
def test_oracle_doc_lap_dong_y_voi_nhan():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


def test_bo_doc_hinh_thang_vuong_phat_hai_goc_vuong_tai_dinh_ke():
    de = ROWS["P01_trapezoid_pyramid"]["text"]
    rb = {(r.kind, r.entities) for r in doc_rang_buoc(de)}
    assert ("line_perp_line", ("A", "D", "A", "B")) in rb and ("line_perp_line", ("B", "A", "B", "C")) in rb
    assert phan_chua_doc(de) == ()
    # hai đỉnh không kề: không phát, cụm còn chưa đọc
    sai = de.replace("tại A và B", "tại A và C")
    assert not any(r.kind == "line_perp_line" for r in doc_rang_buoc(sai)) and phan_chua_doc(sai)


# ══ TUYẾN LLM_ONLY (chương trình kiểu mô hình) ══════════════════════════════
@pytest.mark.parametrize("rid", sorted(ROWS))
def test_llm_only_theo_nhan(rid):
    e = ROWS[rid]["expect"]["llm"]
    sp = chuong_trinh_kieu_llm(rid)
    out = verify_and_compile(hop_dong(rid), sp)
    if e.startswith("served:"):
        assert out.servable, (out.stage_reached, out.reason_code, out.details)
        assert Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"])) == Fraction(e.split(":", 1)[1])
    else:
        assert not out.servable
        if ":" in e:
            assert out.reason_code == e.split(":", 1)[1], (out.reason_code, out.details)
