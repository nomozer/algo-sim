# -*- coding: utf-8 -*-
"""Owner P0 2026-10-26 — ký hiệu vuông góc: nhân chứng do PRODUCER phát, đủ để renderer không phải đoán.

`mp-vuong-goc-duong`: dấu ở chân H của khoảng cách S → (mặt phẳng qua B ⊥ SC) đứng cạnh nhãn "(ABC)" của mặt đáy, nên
học sinh gán nó cho mặt đáy. Sửa ở producer:
  · khoảng cách điểm → vật: `marker.u_to` = điểm CÓ TÊN trên vật nhận, `u` chĩa đúng tới nó (đoạn chứng minh HB);
  · góc ĐO ĐƯỢC bằng 90° (cos² = 0): nhân chứng góc vuông tại giao điểm (G1: BC ⊥ (SAB));
  · mặt phẳng không tên ⇒ `(α)`; tên khai nhiều điểm được kiểm đồng phẳng (không rút `(ABCD)` thành `(ABC)`).
Mọi phép so CHÍNH XÁC (`Fraction`) — không dung sai.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state

DAY = {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0], "S": [0, 0, 4]}
MAT = [["A", "B", "C", "D"], ["A", "B", "S"], ["B", "C", "S"], ["C", "D", "S"], ["D", "A", "S"]]


def _chop(khai: list[tuple[str, str]], cau: list[dict], them_diem: dict | None = None) -> dict:
    diem = {**DAY, **(them_diem or {})}
    spec = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Hình chóp S.ABCD",
        "memory_declarations": [{"name": n, "type": "point3", "initial_value": v} for n, v in diem.items()]
        + [{"name": "chop", "type": "solid"}] + [{"name": n, "type": t} for n, t in khai],
        "statements": [{"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD",
                        "vertices": list("ABCDS"), "faces": MAT}, *cau],
        "visual_bindings": {}})
    return build_scene3d(build_simulation_state(spec, SemanticProgramInterpreter().execute(spec)))


def _q(canh: dict, ten: str) -> dict:
    return next(o for o in canh["objects"] if o["id"] == ten)


def _v(xs) -> tuple[Fraction, ...]:
    return tuple(Fraction(x) for x in xs)


def _tru(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _vh(a, b) -> Fraction:
    return sum(x * y for x, y in zip(a, b))


def _do(ten: str, q: str, of: str, wrt: str) -> dict:
    return {"kind": "assign", "target_var": ten, "expr": {"kind": "measure", "quantity": q, "of": of, "wrt": wrt}}


def _duong(ten: str, a: str, b: str) -> dict:
    return {"kind": "construct_line", "target_var": ten, "through_a": a, "through_b": b, "label": a + b}


MP_VUONG_GOC = [
    _duong("sc", "S", "C"),
    {"kind": "assign", "target_var": "mpb", "expr": {"kind": "plane_perpendicular_to_line", "point": "B", "line": "sc"}},
    _do("kc", "distance", "S", "mpb"),
]


# ══ khoảng cách điểm → mặt phẳng: `u_to` ═════════════════════════════════════════════════════════════════════════

def test_khoang_cach_den_mat_phang_canh_dau_chia_toi_diem_co_ten_tren_mat_phang():
    canh = _chop([("sc", "line3"), ("mpb", "plane3"), ("kc", "float")], MP_VUONG_GOC)
    w = _q(canh, "kc")["annotation"]["witness"]
    chan, mp = _v(w["foot"]), _q(canh, "mpb")
    assert chan == (Fraction(5, 3), Fraction(5, 3), Fraction(2, 3))
    assert w["marker"]["u_to"] == "B"
    u, v = _v(w["marker"]["u"]), _v(w["marker"]["v"])
    assert u == _tru(_v(DAY["B"]), chan)                         # cạnh dấu chĩa ĐÚNG tới B
    assert _vh(_v(mp["normal"]), _tru(chan, _v(mp["point"]))) == 0   # chân thuộc mặt phẳng
    assert _vh(u, v) == 0 and _vh(u, _v(mp["normal"])) == 0
    assert v == _tru(_v(DAY["S"]), chan)


def test_khong_co_diem_co_ten_tren_vat_nhan_thi_khong_co_u_to():
    """(P): z = 1 không chứa điểm có tên nào ⇒ không có đoạn chứng minh để vẽ (không bịa điểm)."""
    canh = _chop([("p", "plane3"), ("kc", "float")], [
        {"kind": "construct_plane_from_equation", "target_var": "p", "label": "(P)", "a": 0, "b": 0, "c": 1, "d": -1},
        _do("kc", "distance", "S", "p")])
    w = _q(canh, "kc")["annotation"]["witness"]
    assert "u_to" not in w["marker"]
    assert _vh(_v(w["marker"]["u"]), _v(w["marker"]["v"])) == 0


# ══ G1 · góc đo được bằng 90° ═════════════════════════════════════════════════════════════════════════════════════

def test_G1_duong_vuong_goc_mat_phang_co_nhan_chung_tai_giao_diem():
    canh = _chop([("sab", "plane3"), ("bc", "line3"), ("goc", "float")], [
        {"kind": "construct_plane", "target_var": "sab", "label": "(SAB)", "through": ["S", "A", "B"]},
        _duong("bc", "B", "C"), _do("goc", "angle_cos_sq", "bc", "sab")])
    g = _q(canh, "goc")
    assert g["value"] == "0"
    a = g["annotation"]
    assert (a["kind"], a["anchor"]) == ("angle", "witness")
    w = a["witness"]
    assert w["relation"] == "line_perpendicular_plane" and w["on"] == "sab"
    assert (_v(w["foot"]), w["from"]) == (_v(DAY["B"]), "C")
    assert w["marker"]["u_to"] in {"A", "S"}
    assert _vh(_v(w["marker"]["u"]), _v(w["marker"]["v"])) == 0
    assert not [d for d in canh["diagnostics"] if d.startswith("ANNOTATION_UNBOUND goc")]


def test_G1_thu_tu_toan_hang_mat_truoc_duong_sau_cho_cung_nhan_chung():
    canh = _chop([("sab", "plane3"), ("bc", "line3"), ("goc", "float")], [
        {"kind": "construct_plane", "target_var": "sab", "label": "(SAB)", "through": ["S", "A", "B"]},
        _duong("bc", "B", "C"), _do("goc", "angle_cos_sq", "sab", "bc")])
    w = _q(canh, "goc")["annotation"]["witness"]
    assert (_v(w["foot"]), w["from"], w["on"]) == (_v(DAY["B"]), "C", "sab")


def test_hai_duong_cat_nhau_vuong_goc_co_nhan_chung_rieng_quan_he_duong_duong():
    canh = _chop([("ab", "line3"), ("ad", "line3"), ("goc", "float")], [
        _duong("ab", "A", "B"), _duong("ad", "A", "D"), _do("goc", "angle_cos_sq", "ab", "ad")])
    w = _q(canh, "goc")["annotation"]["witness"]
    assert w["relation"] == "line_perpendicular_line"
    assert (_v(w["foot"]), w["from"], w["marker"]["u_to"]) == (_v(DAY["A"]), "B", "D")


@pytest.mark.parametrize("cau, ly_do", [
    # SC với (ABCD): cos² = 2/3 — không phải góc vuông, không có điểm neo đăng ký.
    ([_duong("sc", "S", "C"),
      {"kind": "construct_plane", "target_var": "p", "label": "(ABCD)", "through": ["A", "B", "C"]},
      _do("goc", "angle_cos_sq", "sc", "p")], "has no registered anchor"),
    # BD ⊥ SC nhưng CHÉO nhau: không có giao điểm để đặt dấu — không bao giờ đặt "gần đúng".
    ([_duong("sc", "S", "C"), _duong("bd", "B", "D"), _do("goc", "angle_cos_sq", "bd", "sc")], "do not meet"),
])
def test_goc_khong_vuong_hoac_cheo_nhau_KHONG_co_dau(cau, ly_do):
    khai = [("sc", "line3"), ("p", "plane3"), ("bd", "line3"), ("goc", "float")]
    canh = _chop(khai, cau)
    assert "annotation" not in _q(canh, "goc")
    assert any(d.startswith("ANNOTATION_UNBOUND goc") and ly_do in d for d in canh["diagnostics"]), canh["diagnostics"]


# ══ tên mặt phẳng ═════════════════════════════════════════════════════════════════════════════════════════════════

def test_mat_phang_khong_ten_goi_alpha_va_buoc_dung_noi_goi_alpha():
    canh = _chop([("sc", "line3"), ("mpb", "plane3"), ("kc", "float")], MP_VUONG_GOC)
    mp = _q(canh, "mpb")
    assert (mp["notation"], mp.get("notation_assigned")) == ("(α)", True)
    buoc = next(e for e in canh["events"] if e["object"] == "mpb")
    assert buoc["learner_text"] == "Gọi (α) là mặt phẳng qua B và vuông góc với SC."
    assert "Plane3" not in buoc["explanation"] and buoc["semantic_kind"] == "GEOMETRY_CONSTRUCTION"
    assert _q(canh, "kc")["label"] == "Khoảng cách giữa S và (α)"


@pytest.mark.parametrize("nhan, them, ky_hieu", [
    ("(ABCD)", None, "(ABCD)"),                   # D đồng phẳng ⇒ giữ nguyên, không rút thành (ABC)
    ("(ABCE)", {"E": [1, 1, 1]}, "(ABC)"),        # E ngoài mặt phẳng ⇒ nhãn sai không được tin
])
def test_ten_mat_phang_nhieu_diem_kiem_dong_phang_chinh_xac(nhan, them, ky_hieu):
    canh = _chop([("p", "plane3")], [
        {"kind": "construct_plane", "target_var": "p", "label": nhan, "through": ["A", "B", "C"]}], them)
    p = _q(canh, "p")
    assert p["notation"] == ky_hieu
    if ky_hieu != nhan:
        assert nhan not in (p["label"], p["reference"], p["display_label"])
