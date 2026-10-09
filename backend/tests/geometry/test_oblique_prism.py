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

from app.ai import pipeline as PL
from app.simulation.geometry_compiler import compiler as C
from app.simulation.geometry_compiler import contract_adapter as A
from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen
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


def chay_compiler(rid: str, monkeypatch) -> dict:
    contract = hop_dong(rid)

    async def analyze(*_a, **_k):
        return contract, None

    async def khong_goi(*_a, **_k):
        raise AssertionError("tuyến compiler gọi model")

    monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
    monkeypatch.setattr(PL, "call_gemini", khong_goi)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
    return asyncio.run(PL.run_pipeline(ROWS[rid]["text"], "fake_key"))


def _gia_tri(env: dict, ten: str = "V") -> Fraction:
    return Fraction(next(o["value"] for o in env["scene3d"]["objects"] if o["id"] == ten))


# ══ ORACLE ══════════════════════════════════════════════════════════════════
def test_oracle_doc_lap_dong_y_voi_nhan():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


# ══ TUYẾN COMPILER ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("rid", sorted(ROWS))
def test_quyet_dinh_compiler_theo_nhan(rid):
    e = ROWS[rid]["expect"]["compiler"]
    qd = quyet_dinh_dinh_tuyen(hop_dong(rid), BAT)
    loai, _, ma = e.partition(":")
    if loai == "served":
        assert qd.decision == "USE_COMPILER", (qd.decision, qd.reason_code, qd.diagnostics)
    elif loai == "fallback":
        assert (qd.decision, qd.reason_code) == ("FALLBACK_TO_LLM", ma), (qd.reason_code, qd.diagnostics)
    else:
        assert (qd.decision, qd.reason_code) == ("REFUSE", ma), (qd.reason_code, qd.diagnostics)


@pytest.mark.parametrize("rid", sorted(r for r in ROWS if ROWS[r]["expect"]["compiler"].startswith("served")))
def test_compiler_phuc_vu_qua_route_san_pham(rid, monkeypatch):
    env = chay_compiler(rid, monkeypatch)
    assert env.get("status") == "ok", env
    assert _gia_tri(env) == Fraction(ROWS[rid]["expect"]["compiler"].split(":", 1)[1])
    # chiều cao do KERNEL đo (khoảng cách đỉnh neo tới mặt phẳng đáy), không do compiler khai
    cao = next(o for o in env["scene3d"]["objects"] if o["id"].startswith("chieu_cao_"))
    assert cao["source"].get("provenance") != "GIVEN"


@pytest.mark.parametrize("rid", sorted(r for r in ROWS if ROWS[r]["expect"]["compiler"].startswith("served")))
def test_bat_bien_hinh_hoc_cua_khoi(rid, monkeypatch):
    """Euler · đáy trên = tịnh tiến của đáy dưới · hai đáy song song · mặt bên phẳng · cạnh bên xiên."""
    env = chay_compiler(rid, monkeypatch)
    objs = {o["id"]: o for o in env["scene3d"]["objects"]}
    sp = SemanticProgramSpec.model_validate({"spec_version": "1.0", **C.bien_dich(
        A.build_fact_graph(hop_dong(rid)).graph).program})
    mem = SemanticProgramInterpreter().execute(sp).final_memory
    solid = next(o for o in objs.values() if o["type"] == "solid")
    canh = {frozenset((f[i], f[(i + 1) % len(f)])) for f in solid["faces"] for i in range(len(f))}
    assert len(solid["vertices"]) - len(canh) + len(solid["faces"]) == 2
    t = ROWS[rid]["topology"]
    ids = {p: A.dinh_danh_thuc_the(p)[0] for p in [*t["base"], *t["top"]]}
    P = {p: tuple(Fraction(str(x)) for x in (mem[ids[p]].x, mem[ids[p]].y, mem[ids[p]].z)) for p in ids}
    tru = lambda u, v: tuple(a - b for a, b in zip(P[u], P[v]))  # noqa: E731
    v0 = tru(t["top"][0], t["base"][0])
    assert all(tru(q, p) == v0 for p, q in zip(t["base"], t["top"]))           # một phép tịnh tiến
    assert {P[p][2] for p in t["base"]} == {0} and len({P[q][2] for q in t["top"]}) == 1   # hai đáy song song
    assert v0[0] != 0 or v0[1] != 0                                             # cạnh bên KHÔNG vuông góc đáy
    assert Fraction(str(mem["chieu_cao_" + ids[ROWS[rid]["perp"]["line"][0]]])) == v0[2]


def test_dinh_bo_cuc_la_layout_derived_do_dai_de_cho_la_given():
    bd = C.bien_dich(A.build_fact_graph(hop_dong("OP01_triangle_foot_vertex_height")).graph)
    khai = {m["name"]: m for m in bd.program["memory_declarations"]}
    assert {khai[p]["provenance"] for p in ("A", "B", "C", "A_prime")} == {"LAYOUT_DERIVED"}
    assert khai["A_primeB_length"]["provenance"] == "GIVEN" and khai["A_primeB_length"]["source_fact_id"]
    # ba đỉnh đáy trên KHÔNG khai toạ độ: hai cái là ảnh tịnh tiến do kernel tính
    tinh_tien = [s for s in bd.program["statements"] if s["kind"] == "construct_point"]
    assert {s["expr"]["kind"] for s in tinh_tien} == {"translate"} and len(tinh_tien) == 2


def test_tuyen_compiler_tat_mac_dinh():
    assert quyet_dinh_dinh_tuyen(hop_dong("OP01_triangle_foot_vertex_height"), {}).decision == "DISABLED"


def test_lang_tru_tam_giac_xien_khong_con_bi_bien_dich_thanh_lang_tru_dung():
    """Trước bản này nhánh đáy tam giác bỏ qua `lateral_structure`: đề xiên có AA' ⊥ (ABC) được dựng thành lăng trụ đứng."""
    qd = quyet_dinh_dinh_tuyen(hop_dong("ON05_right_edge_contradicts_oblique"), BAT)
    assert qd.decision == "REFUSE" and "RIGHT_LATERAL_EDGE_FOR_OBLIQUE_PRISM" in qd.diagnostics


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


def test_buoc_dung_ke_bang_ky_hieu_khong_in_repr(monkeypatch):
    """Vectơ cạnh bên được kể "Lấy vectơ AA′." — trước bản này lời kể dùng chung in `Vec3(x=Fraction(…))`."""
    env = chay_compiler("OP01_triangle_foot_vertex_height", monkeypatch)
    loi = [s["learner_text"] for s in env["scene3d"]["formation"]["steps"]]
    assert not any("Vec3(" in t or "Fraction(" in t for t in loi), loi
    assert "Lấy vectơ AA′." in loi
    assert any(t.startswith("Dựng lăng trụ xiên ABC.A′B′C′") for t in loi)
