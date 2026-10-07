# -*- coding: utf-8 -*-
"""exact-dimensions — chóp tam giác đều / tứ diện đều có kích thước HỮU TỈ qua route sản phẩm (`verify_and_compile`).

Nhãn ghi TRƯỚC thay đổi: `docs/evaluation/geometry/runs/exact-dimensions/labels.json`; oracle độc lập `oracle.py` cùng
thư mục. Bố cục chương trình là KHUNG affine (`charts` của nhãn); metric khung dẫn xuất từ đề
(`assumption_gate.do_luong_cua` → `geometry.metric`).
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry import metric as M
from app.simulation.geometry.exact import Vec3
from tests.geometry import test_regular_triangular_pyramid as T
from tests.geometry import w14_cases as W

_RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/exact-dimensions"
NHAN = json.loads((_RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
#: Đính chính có ngày + lý do của chính nhãn run này (tệp nhãn giữ nguyên từng byte).
_DINH_CHINH = json.loads((_RUN / "label_corrections.json").read_text(encoding="utf-8"))["this_run_rows"]["rows"]
NHAN = {k: ({**v, "expect": _DINH_CHINH[k]["now"]} if k in _DINH_CHINH else v) for k, v in NHAN.items()}


def _khung(ten: str, b: F, h: F) -> dict:
    """Khung affine theo `labels.json#charts` — b, h chỉ là SỐ KHUNG (xấp xỉ hữu tỉ khi đề cho căn)."""
    if ten == "axis":
        return {"day": ((F(0), F(0), F(0)), (b, F(0), F(0)), (F(0), b, F(0))), "apex": (b / 3, b / 3, h)}
    if ten == "approx":
        return {"day": ((F(0), F(0), F(0)), (b, F(0), F(0)), (b / 2, F("0.866") * b, F(0))),
                "apex": (b / 2, F("0.2887") * b, h)}
    if ten == "unit":
        return {"day": ((F(0), F(0), F(0)), (F(1), F(0), F(0)), (F(0), F(1), F(0))), "apex": (F(1, 3), F(1, 3), F(1))}
    if ten == "over_vertex":
        return {"day": ((F(0), F(0), F(0)), (b, F(0), F(0)), (F(0), b, F(0))), "apex": (F(0), F(0), h)}
    if ten == "flat":
        return {"day": ((F(0), F(0), F(0)), (b, F(0), F(0)), (F(0), b, F(0))), "apex": (F(1), F(1), F(0))}
    if ten in ("tetra_axis", "tetra_axis_as_pyramid"):
        return {"day": ((b, F(0), F(0)), (F(0), b, F(0)), (F(0), F(0), b)), "apex": (F(0), F(0), F(0))}
    if ten == "N1":
        return {}                                   # khung nghiêng Euclid cũ của builder (k=3, t=1)
    raise KeyError(ten)


DAY, CAO, BEN = "cạnh đáy", "chiều cao", "cạnh bên"
#: ca → (kích thước khung b, h; GIVEN (tên, nhãn fact, giá trị đề); tham số builder)
CA = {
    "P01_base_height": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {}),
    "P02_approx_chart": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {}),
    "P03_unit_chart": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {}),
    "P04_fractions": (F(3, 2), F(5, 3), [("canh_day", DAY, "3/2"), ("chieu_cao", CAO, "5/3")], {}),
    "P05_decimal_comma": (F(5, 2), 6, [("canh_day", DAY, "2.5"), ("chieu_cao", CAO, "6")], {}),
    "P06_tetrahedron": (6, 0, [("canh", "cạnh", "6")], {"dinh": ("A", "B", "C", "D"), "ky_hieu_khoi": "ABCD"}),
    "P07_tetrahedron_fraction": (F(5, 2), 0, [("canh", "cạnh", "5/2")],
                                 {"dinh": ("A", "B", "C", "D"), "ky_hieu_khoi": "ABCD"}),
    "P08_tetrahedron_height": (6, 0, [("canh", "cạnh", "6")],
                               {"dinh": ("A", "B", "C", "D"), "ky_hieu_khoi": "ABCD", "hoi": "height"}),
    "P09_base_lateral": (6, 4, [("canh_day", DAY, "6"), ("canh_ben", BEN, "5")], {}),
    "P10_all_edges": (4, 3, [("canh", "cạnh", "4")], {}),
    "P11_renamed": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {"dinh": ("M", "N", "P", "Q")}),
    "P12_phrasing": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {}),
    "P13_named_centroid": (6, 4, [("canh_day", DAY, "6"), ("SG_length", "SG", "4")], {}),
    "P14_lateral_length": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {"hoi": "distance"}),
    "P15_old_radical_N1": (0, 0, [("canh_day", DAY, "3√2"), ("chieu_cao", CAO, "√3")], {}),
    "P16_old_radical_axis": (F(21, 5), F(7, 4), [("canh_day", DAY, "3√2"), ("chieu_cao", CAO, "√3")], {}),
    "P17_radical_base_rational_height": (F(7, 2), 2, [("canh_day", DAY, "2√3"), ("chieu_cao", CAO, "2")], {}),
    "P18_apex_drawn_over_vertex": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {}),
    "N01_missing_height": (6, 4, [("canh_day", DAY, "6")], {}),
    "N02_contradiction": (6, 4, [("canh_day", DAY, "6"), ("canh_ben", BEN, "5"), ("chieu_cao", CAO, "4")], {}),
    "N03_lateral_mixed": (6, 4, [("canh_day", DAY, "6"), ("SA_length", "SA", "5"), ("SB_length", "SB", "6")], {}),
    "N04_declared_value_conflict": (6, 4, [("AB_length", "AB", "6"), ("SA_length", "SA", "7")], {}),
    "N05_lateral_too_short": (6, 4, [("canh_day", DAY, "6"), ("canh_ben", BEN, "3")], {}),
    "N06_zero_base": (6, 4, [("canh_day", DAY, "0"), ("chieu_cao", CAO, "4")], {}),
    "N07_wrong_centroid_identity": (6, 4, [("canh_day", DAY, "6"), ("SG_length", "SG", "4")],
                                    {"trong_tam": "trung_diem_BC"}),
    "N08_laterals_base_not_stated": (6, 4, [("SA_length", "SA", "5"), ("AB_length", "AB", "6")], {}),
    "N09_regular_is_not_tetrahedron": (6, 0, [("canh_day", DAY, "6")], {}),
    "N10_no_size": (6, 4, [], {}),
    "N11_flat_chart": (6, 4, [("canh_day", DAY, "6"), ("chieu_cao", CAO, "4")], {}),
    "U01_symbolic": (6, 4, [], {}),
    "U02_sum_of_radicals": (6, 4, [("chieu_cao", CAO, "4")], {}),
}


def chuong_trinh(ca: str):
    b, h, given, tham = CA[ca]
    hang = NHAN[ca]
    kw = dict(tham)
    if hang["chart"] != "N1":
        kw.update(_khung(hang["chart"], F(b), F(h)))
    kw.update(T._g(*given))
    return T.chop_deu(ca, van=hang["text"], **kw)


def ket_qua(ca: str) -> dict:
    contract, prog = chuong_trinh(ca)
    _sp, out, scene = W.chay(contract, prog)
    if out.servable:
        dich = next(s["target_var"] for s in reversed(prog["statements"]) if s.get("kind") == "assign")
        v = next(o for o in scene["objects"] if o["id"] == dich)
        return {"served": v.get("value"), "scene": scene, "out": out}
    return {"stage": out.stage_reached, "reason_code": out.reason_code, "details": out.details, "out": out}


def test_moi_nhan_co_chuong_trinh():
    assert set(CA) == set(NHAN)


@pytest.mark.parametrize("ca", sorted(NHAN))
def test_ket_cuc_route_theo_nhan(ca):
    mong, kq = NHAN[ca]["expect"], ket_qua(ca)
    if mong.startswith("served:"):
        assert kq.get("served") == mong.removeprefix("served:"), (ca, kq.get("stage"), kq.get("reason_code"),
                                                                    kq.get("details"))
        return
    assert "served" not in kq, (ca, "served", kq.get("served"))
    phan = mong.split(":")
    if len(phan) > 1:
        assert kq["stage"] == phan[1], (ca, kq["stage"], kq["reason_code"], kq["details"])
    if len(phan) > 2:
        assert kq["reason_code"] == phan[2], (ca, kq["stage"], kq["reason_code"], kq["details"])


# ── metric khung: tính nhất quán, không chỉ đáp số cuối ─────────────────────────────────────────

def _phuc_vu(ca: str) -> dict:
    kq = ket_qua(ca)
    assert "served" in kq, (ca, kq.get("stage"), kq.get("reason_code"), kq.get("details"))
    return kq


def test_moi_dai_luong_trung_gian_dung_theo_de():
    """b = 6, h = 4: diện tích đáy 9√3, chiều cao SG = 4, V = 12√3 — ở BA khung khác nhau (affine, xấp xỉ, đơn vị)."""
    for ca in ("P01_base_height", "P02_approx_chart", "P03_unit_chart", "P18_apex_drawn_over_vertex"):
        gt = {o["id"]: o.get("value") for o in _phuc_vu(ca)["scene"]["objects"] if o.get("type") == "quantity"}
        assert gt["dien_tich_day_ABC"] == "9√3" and gt["chieu_cao_SG"] == "4" and gt["V"] == "12√3", (ca, gt)


def test_canh_va_trong_tam_theo_metric_khung():
    """Trong metric dẫn xuất: ba cạnh đáy 6, ba cạnh bên 2√7, trọng tâm dựng bằng trung tuyến là chân đường cao."""
    from app.simulation.semantic_program.assumption_gate import do_luong_cua
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter

    contract, prog = chuong_trinh("P01_base_height")
    m = do_luong_cua(contract.problem_text, prog)
    assert m is not None and not M.is_identity(m)
    with M.using(m):
        mem = SemanticProgramInterpreter().execute(W.spec_cua(prog)).final_memory
        S, A, B, C, G = (mem[k] for k in "SABCG")
        assert [M.norm_sq(p - q) for p, q in ((A, B), (B, C), (C, A))] == [36, 36, 36]
        assert [M.norm_sq(S - p) for p in (A, B, C)] == [28, 28, 28]
        assert M.dot(S - G, B - A) == 0 and M.dot(S - G, C - A) == 0 and M.norm_sq(S - G) == 16


def test_khung_euclid_cu_khong_co_metric():
    """Khung N1 (Euclid đúng) ⇒ metric đồng nhất ⇒ `None` — đường cũ giữ nguyên từng byte."""
    from app.simulation.semantic_program.assumption_gate import do_luong_cua
    contract, prog = chuong_trinh("P15_old_radical_N1")
    assert do_luong_cua(contract.problem_text, prog) is None
    assert "chart_metric" not in _phuc_vu("P15_old_radical_N1")["scene"]


def test_canh_co_metric_mang_chart_metric():
    kq = _phuc_vu("P01_base_height")
    g = [[F(x) for x in r] for r in kq["scene"]["chart_metric"]]
    assert g == [[1, F(1, 2), 0], [F(1, 2), 1, 0], [0, 0, 1]], g


def test_gram_tu_do_dai_duy_nhat_va_xac_dinh_duong():
    o, x, y, z = Vec3.of(0, 0, 0), Vec3.of(1, 0, 0), Vec3.of(0, 1, 0), Vec3.of(0, 0, 1)
    m = M.gram_from_lengths((o, x, y, z), {(0, 1): 1, (0, 2): 1, (0, 3): 1, (1, 2): 2, (1, 3): 2, (2, 3): 2})
    assert M.is_identity(m)
    with pytest.raises(Exception):      # độ dài không phải của một tứ diện Euclid (bất đẳng thức tam giác hỏng)
        M.gram_from_lengths((o, x, y, z), {(0, 1): 1, (0, 2): 1, (0, 3): 1, (1, 2): 9, (1, 3): 9, (2, 3): 9})
    with pytest.raises(Exception):      # khung phẳng
        M.gram_from_lengths((o, x, y, Vec3.of(1, 1, 0)), {(i, j): 1 for i in range(4) for j in range(i + 1, 4)})


def test_khoi_cong_tu_choi_trong_khung_co_metric():
    from app.simulation.geometry.exact import GeometryError
    with M.using(M.Metric(((F(2), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(1))))):
        with pytest.raises(GeometryError) as e:
            M.require_euclidean("a curved solid")
    assert e.value.code == M.ERR_CAN_EUCLID
