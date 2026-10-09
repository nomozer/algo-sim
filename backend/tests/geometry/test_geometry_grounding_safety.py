# -*- coding: utf-8 -*-
"""geometry-grounding-safety — C0 kiểm ràng buộc hình dạng của đề trên toạ độ; compiler không tự coi đáy là hình chữ nhật.

Nhãn ghi trước: `docs/evaluation/geometry/runs/geometry-grounding-safety/labels.json` (oracle `oracle.py`, chỉ từ đề).
0 lượt gọi model.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import subprocess
import sys
from fractions import Fraction

import pytest

from app.ai import pipeline as PL
from app.simulation.geometry_compiler import compiler as C
from app.simulation.geometry_compiler import contract_adapter as A
from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.refusal_cause import theo_ma
from app.simulation.semantic_program.route import verify_and_compile

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/geometry-grounding-safety"
ROWS = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
C0 = sorted(r for r in ROWS if ROWS[r]["route"] == "llm_c0")
COMP = sorted(r for r in ROWS if ROWS[r]["route"] == "compiler")
BAT = {"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"}


def _c0(rid: str):
    r = ROWS[rid]
    pts = r["points"]
    payload = {"input_facts": [{"id": f"d_{p}", "kind": "point3", "label": p,
                                "value": [f"({';'.join(map(str, v))})"]} for p, v in pts.items()],
               "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}]}
    contract = build_request_contract(payload, problem_text=r["text"], domain="hinh_hoc")
    S, day = r["solid"]["apex"], r["solid"]["base"]
    k = len(day)
    sp = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Thể tích khối chóp",
        "memory_declarations": [{"name": p, "type": "point3", "initial_value": [str(c) for c in pts[p]],
                                 "source_fact_id": f"d_{p}"} for p in pts]
        + [{"name": "khoi", "type": "solid"}, {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "khoi", "vertices": [S, *day],
             "faces": [list(day)] + [[S, day[i], day[(i + 1) % k]] for i in range(k)]},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}]})
    return contract, sp


def _payload(r: dict) -> dict:
    facts = [{"id": f"fact_{k}", "kind": "float", "label": k, "value": [v]} for k, v in r["lengths"].items()]
    rels = [{"kind": "perpendicular_lines", "line": [a, b], "other_line": [c, d],
             "source_fact_id": f"fact_right_{i}", "model_assumption": False}
            for i, (a, b, c, d) in enumerate(r["right_angles"])]
    facts += [{"id": f"fact_right_{i}", "kind": "str", "label": "góc vuông", "value": [f"{a}{b} ⊥ {c}{d}"]}
              for i, (a, b, c, d) in enumerate(r["right_angles"])]
    p = r["perp"]
    rels.append({"kind": "perpendicular_line_plane", "line": p["line"], "plane": p["plane"],
                 "source_fact_id": "fact_perp", "model_assumption": False})
    facts.append({"id": "fact_perp", "kind": "str", "label": "vuông góc đáy", "value": ["⊥"]})
    t = r["topology"]
    if t["solid_kind"] == "pyramid":
        topo = {"solid_kind": "pyramid", "apex": t["apex"], "base_cycle": t["base"]}
    else:
        topo = {"solid_kind": "prism", "base_cycle": t["base"], "top_cycle": t["top"],
                "correspondence": [list(x) for x in zip(t["base"], t["top"])]}
    if t.get("base_shape"):
        topo["base_shape"] = t["base_shape"]
    return {"input_facts": facts, "geometric_relations": rels, "solid_topology": topo,
            "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}]}


def _hop_dong(rid: str):
    return build_request_contract(_payload(ROWS[rid]), problem_text=ROWS[rid]["text"], domain="hinh_hoc")


def test_oracle_doc_lap_dong_y_voi_nhan():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


# ══ C0 — toạ độ ĐỀ CHO vs quan hệ ĐỀ NÓI ═════════════════════════════════════
@pytest.mark.parametrize("rid", C0)
def test_c0_theo_nhan(rid):
    contract, sp = _c0(rid)
    out = verify_and_compile(contract, sp)
    loai, _, gia_tri = ROWS[rid]["expect"].partition(":")
    if loai == "served":
        assert out.servable, (out.stage_reached, out.reason_code, out.details)
        assert out.assumption_certificate == "C0"
        assert Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"])) == Fraction(gia_tri)
    else:
        assert not out.servable and out.stage_reached == "assumption", (out.stage_reached, out.reason_code)
        assert out.reason_code == gia_tri, (out.reason_code, out.details)
        assert any(d.startswith("C0_SHAPE_CONTRADICTION") for d in out.details)
        assert out.reason_subjects


_HINH_THANG = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 4, 0), "S": (0, 0, 3)}
_DE_HINH_THANG = "Cho khối chóp S.ABCD với A(0;0;0), B(2;0;0), C(2;2;0), D(0;4;0) và đỉnh S(0;0;3)"


@pytest.mark.parametrize("cau_e, mong", [
    ("điểm E(5;5;0) sao cho AE vuông góc với AB", "SOURCE_SHAPE_CONTRADICTS_COORDINATES"),  # đề tự mâu thuẫn
    ("điểm E(0;5;0) sao cho AE vuông góc với AB", None),                                    # nhất quán
    ("điểm E sao cho AE vuông góc với AB", None),                                           # E không toạ độ: thiếu ≠ sai
], ids=["mau_thuan", "nhat_quan", "khong_toa_do"])
def test_c0_diem_vang_trong_chuong_trinh_kiem_bang_toa_do_de(cau_e, mong):
    """LOCAL: quan hệ có điểm chương trình KHÔNG khai (E) vẫn kiểm bằng toạ độ chính đề cho — bỏ qua điểm ấy không được
    biến một đề tự mâu thuẫn kiểm chứng được thành đề được phục vụ."""
    de = f"{_DE_HINH_THANG} và {cau_e}. Tính thể tích khối chóp."
    payload = {"input_facts": [{"id": f"d_{p}", "kind": "point3", "label": p,
                                "value": [f"({';'.join(map(str, v))})"]} for p, v in _HINH_THANG.items()],
               "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}]}
    contract = build_request_contract(payload, problem_text=de, domain="hinh_hoc")
    day = ["A", "B", "C", "D"]
    sp = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Thể tích khối chóp",
        "memory_declarations": [{"name": p, "type": "point3", "initial_value": [str(c) for c in v],
                                 "source_fact_id": f"d_{p}"} for p, v in _HINH_THANG.items()]
        + [{"name": "khoi", "type": "solid"}, {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "khoi", "vertices": ["S", *day],
             "faces": [day] + [["S", day[i], day[(i + 1) % 4]] for i in range(4)]},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}]})
    out = verify_and_compile(contract, sp)
    if mong is None:
        assert out.servable and out.assumption_certificate == "C0", (out.stage_reached, out.reason_code, out.details)
    else:
        assert not out.servable and out.reason_code == mong, (out.stage_reached, out.reason_code, out.details)
        assert any(d.startswith("C0_SHAPE_CONTRADICTION line_perp_line(A,E,A,B)") for d in out.details)


def test_mau_thuan_la_loi_cua_de_khong_gui_di_sua():
    assert theo_ma("SOURCE_SHAPE_CONTRADICTS_COORDINATES") == "SOURCE"
    assert "SOURCE_SHAPE_CONTRADICTS_COORDINATES" in PL.KHONG_SUA_NGUON


def test_c0_mau_thuan_khong_co_scene3d_qua_pipeline(monkeypatch):
    rid = "C02_trapezoid_phrase_contradicts"
    contract, sp = _c0(rid)

    async def analyze(*_a, **_k):
        return contract, None

    async def program(*_a, **_k):
        return sp, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
    monkeypatch.setattr(PL, "stage_semantic_program", program)
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    env = asyncio.run(PL.run_pipeline(ROWS[rid]["text"], "fake_key"))
    assert env.get("status") != "ok" and not env.get("scene3d"), env
    assert env.get("reason_code") == "SOURCE_SHAPE_CONTRADICTS_COORDINATES" and env.get("refusal_cause") == "SOURCE"


# ══ COMPILER — không tự giả định hình chữ nhật ══════════════════════════════
@pytest.mark.parametrize("rid", COMP)
def test_compiler_theo_nhan(rid, monkeypatch):
    loai, _, gia_tri = ROWS[rid]["expect"].partition(":")
    contract = _hop_dong(rid)
    qd = quyet_dinh_dinh_tuyen(contract, BAT)
    if loai == "fallback":
        assert (qd.decision, qd.reason_code) == ("FALLBACK_TO_LLM", gia_tri), (qd.decision, qd.reason_code)
        assert C.bien_dich(A.build_fact_graph(contract).graph).program is None
        return
    assert qd.decision == "USE_COMPILER", (qd.reason_code, qd.diagnostics)
    if loai == "compiled":
        return

    async def analyze(*_a, **_k):
        return contract, None

    async def khong_goi(*_a, **_k):
        raise AssertionError("tuyến compiler gọi model")

    monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
    monkeypatch.setattr(PL, "call_gemini", khong_goi)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
    env = asyncio.run(PL.run_pipeline(ROWS[rid]["text"], "fake_key"))
    assert env.get("status") == "ok", env
    assert Fraction(next(o["value"] for o in env["scene3d"]["objects"] if o["id"] == "V")) == Fraction(gia_tri)
