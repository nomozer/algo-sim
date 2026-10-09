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

from app.ai import pipeline as PL
from app.simulation.geometry_compiler import compiler as C
from app.simulation.geometry_compiler import contract_adapter as A
from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen
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


def _bo_nho(rid: str) -> dict:
    sp = SemanticProgramSpec.model_validate({"spec_version": "1.0", **C.bien_dich(
        A.build_fact_graph(hop_dong(rid)).graph).program})
    return SemanticProgramInterpreter().execute(sp).final_memory


def _id(p: str) -> str:
    return A.dinh_danh_thuc_the(p)[0]


def _xyz(mem: dict, p: str) -> tuple[Fraction, ...]:
    v = mem[_id(p)]
    return tuple(Fraction(str(c)) for c in (v.x, v.y, v.z))


def _tru(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cheo(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _cham(a, b):
    return sum(x * y for x, y in zip(a, b))


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


# ══ TUYẾN COMPILER ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("rid", sorted(ROWS))
def test_quyet_dinh_compiler_theo_nhan(rid):
    loai, _, ma = ROWS[rid]["expect"]["compiler"].partition(":")
    qd = quyet_dinh_dinh_tuyen(hop_dong(rid), BAT)
    want = {"served": "USE_COMPILER", "fallback": "FALLBACK_TO_LLM", "refuse": "REFUSE"}[loai]
    assert qd.decision == want, (qd.decision, qd.reason_code, qd.diagnostics)
    if ma and loai != "served":
        assert qd.reason_code == ma, (qd.reason_code, qd.diagnostics)


@pytest.mark.parametrize("rid", DUONG)
def test_compiler_phuc_vu_qua_route_san_pham(rid, monkeypatch):
    env = chay_compiler(rid, monkeypatch)
    assert env.get("status") == "ok", env
    by = {o["id"]: o for o in env["scene3d"]["objects"]}
    assert Fraction(by["V"]["value"]) == Fraction(ROWS[rid]["expect"]["compiler"].split(":", 1)[1])
    solid = next(o for o in by.values() if o["type"] == "solid")
    canh = {frozenset((f[i], f[(i + 1) % len(f)])) for f in solid["faces"] for i in range(len(f))}
    assert len(solid["vertices"]) - len(canh) + len(solid["faces"]) == 2          # Euler, khối kín
    assert all(len(f) >= 3 for f in solid["faces"])


@pytest.mark.parametrize("rid", DUONG)
def test_bat_bien_hinh_hoc(rid):
    """Đáy phẳng + lồi + góc vuông đúng chỗ; chóp: SX ⊥ đáy; lăng trụ: tịnh tiến ⊥ đáy; chiều cao đo = độ dài đề cho."""
    r, mem = ROWS[rid], _bo_nho(rid)
    t = r["topology"]
    day = [_xyz(mem, p) for p in t["base"]]
    k = len(day)
    n = _cheo(_tru(day[1], day[0]), _tru(day[2], day[0]))
    assert all(_cham(_tru(p, day[0]), n) == 0 for p in day)                         # phẳng
    assert all(_cham(_cheo(_tru(day[i], day[i - 1]), _tru(day[(i + 1) % k], day[i])), n) > 0 for i in range(k))  # lồi
    for x, a, _x, b in r["right_angles"]:
        assert _cham(_tru(_xyz(mem, a), _xyz(mem, x)), _tru(_xyz(mem, b), _xyz(mem, x))) == 0
    tren_hay_dinh, chan = r["perp"]["line"]
    lech = _tru(_xyz(mem, tren_hay_dinh), _xyz(mem, chan))
    assert all(_cham(lech, _tru(day[(i + 1) % k], day[i])) == 0 for i in range(k))   # cạnh đứng ⊥ đáy
    if t["solid_kind"] == "prism":
        assert all(_tru(_xyz(mem, q), _xyz(mem, p)) == _tru(_xyz(mem, t["top"][0]), day[0])
                   for p, q in zip(t["base"], t["top"]))
    cao = next(Fraction(v) for k_, v in r["lengths"].items()
               if {_id(x) for x in (k_[0], k_[1:])} == {_id(tren_hay_dinh), _id(chan)})
    ten_cao = next(k_ for k_ in mem if k_.startswith("chieu_cao_"))
    assert Fraction(str(mem[ten_cao])) == cao


def test_diem_bo_cuc_la_layout_derived_do_dai_de_cho_la_given():
    bd = C.bien_dich(A.build_fact_graph(hop_dong("P01_trapezoid_pyramid")).graph)
    khai = {m["name"]: m for m in bd.program["memory_declarations"]}
    assert {khai[p]["provenance"] for p in ("A", "B", "C", "D", "S")} == {"LAYOUT_DERIVED"}
    assert {khai[n]["provenance"] for n in ("AB_length", "BC_length", "AD_length", "SA_length")} == {"GIVEN"}


def test_cung_mot_ham_cho_moi_so_canh():
    """Tam giác, tứ giác, ngũ giác đi qua MỘT bộ dựng: không nhánh theo số cạnh trong họ mới."""
    ho = {C.danh_gia_eligibility(A.build_fact_graph(hop_dong(rid)).graph).binding.family_id
          for rid in ("P01_trapezoid_pyramid", "P05_right_triangle_foot_off_right_vertex",
                      "P06_pentagon_three_right_angles")}
    assert ho == {C.SUPPORTED_FAMILY_POLYGON_PYRAMID}


def test_tuyen_compiler_tat_mac_dinh():
    assert quyet_dinh_dinh_tuyen(hop_dong("P01_trapezoid_pyramid"), {}).decision == "DISABLED"


@pytest.mark.parametrize("hang", [
    {"text": "Cho hình chóp S.ABCD có đáy ABCD, AB vuông góc với AD, AB = 3, AD = 4, SA vuông góc với mặt phẳng "
             "(ABCD), SA = 6. Tính thể tích khối chóp S.ABCD.",
     "lengths": {"AB": "3", "AD": "4", "SA": "6"}, "right_angles": [["A", "B", "A", "D"]],
     "perp": {"line": ["S", "A"], "plane": ["A", "B", "D"]},
     "topology": {"solid_kind": "pyramid", "apex": "S", "base": ["A", "B", "C", "D"]}},
    {"text": "Cho lăng trụ đứng ABCD.A'B'C'D' có AB vuông góc với AD, AB = 3, AD = 4, AA' = 5. Tính thể tích khối "
             "lăng trụ.",
     "lengths": {"AB": "3", "AD": "4", "AA'": "5"}, "right_angles": [["A", "B", "A", "D"]],
     "perp": {"line": ["A'", "A"], "plane": ["A", "B", "D"]},
     "topology": {"solid_kind": "prism", "base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]}},
], ids=["chop", "lang_tru"])
def test_mot_goc_vuong_khong_phuc_vu_hinh_chu_nhat_tu_gia_dinh(hang, monkeypatch):
    """ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION: compiler còn dựng HÌNH CHỮ NHẬT cho đáy tứ giác chỉ có MỘT góc
    vuông đề cho; cổng chứng chỉ giả định (chung hai tuyến) phải từ chối — không đáp số, không Scene3D."""
    contract = build_request_contract(_payload(hang), problem_text=hang["text"], domain="hinh_hoc")

    async def analyze(*_a, **_k):
        return contract, None

    async def khong_goi(*_a, **_k):
        raise AssertionError("tuyến compiler gọi model")

    monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
    monkeypatch.setattr(PL, "call_gemini", khong_goi)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
    env = asyncio.run(PL.run_pipeline(hang["text"], "fake_key"))
    assert env.get("status") != "ok" and not env.get("scene3d"), env
    assert (env.get("error") or {}).get("reason_code", env.get("reason_code")) == "ASSUMPTION_INVARIANCE_UNPROVEN", env


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
