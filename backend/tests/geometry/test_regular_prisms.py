# -*- coding: utf-8 -*-
"""regular-prisms (G05) — lăng trụ tam giác đều / lục giác đều qua đúng route sản phẩm (amendment §27, khuôn T12).
0 lượt gọi.

Nhãn ghi trước: `docs/evaluation/geometry/runs/regular-prisms/labels.json` (oracle `oracle.py`, từ kích thước đề).
Chương trình kiểu mô hình: đáy đều trong KHUNG AFFINE (lưới đơn vị), mặt trên z = 1, metric dẫn xuất từ đề
(`do_luong_cua`), như T8/T11.
"""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
from collections import Counter
from fractions import Fraction

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.assumption_gate import do_luong_cua
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.shape_constraint import che_muc_tieu, doc_rang_buoc, phan_chua_doc

RUNS = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs"
RUN = RUNS / "regular-prisms"
# tên module riêng: mỗi run có `diagnostics/cases.py`; `import cases` sẽ lấy nhầm bản của run nạp trước
_spec = importlib.util.spec_from_file_location("regular_prisms_cases", RUN / "diagnostics" / "cases.py")
cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cases)
LABELS, hop_dong_va_chuong_trinh = cases.LABELS, cases.hop_dong_va_chuong_trinh

DEM = {6: (12, 8, 18), 3: (6, 5, 9)}      # đỉnh, mặt, cạnh


def test_oracle_doc_lap():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


@pytest.mark.parametrize("rid", sorted(LABELS))
def test_route_theo_nhan(rid):
    contract, sp = hop_dong_va_chuong_trinh(rid)
    out = verify_and_compile(contract, sp)
    loai, _, gia_tri = LABELS[rid]["expect"].partition(":")
    if loai == "refused":
        assert not out.servable, (out.stage_reached, out.details)
        return
    assert out.servable and out.assumption_certificate == "C1", (out.stage_reached, out.reason_code, out.details)
    canh = _dung_scene3d(sp, contract)
    assert next(o["value"] for o in canh["objects"] if o["id"] == "V") == gia_tri
    assert "chart_metric" in canh                 # toạ độ cảnh là toạ độ khung; renderer dùng metric
    khoi = next(o for o in canh["objects"] if o["id"] == "khoi")
    mat = khoi["faces"]
    dem_canh = Counter(frozenset((f[i], f[(i + 1) % len(f)])) for f in mat for i in range(len(f)))
    cap = set(dem_canh)
    V, F, E = DEM[LABELS[rid]["k"]]
    assert (len(khoi["vertex_ids"]), len(mat), len(cap)) == (V, F, E)
    assert V - E + F == 2                         # Euler: khối đóng
    assert all(len(set(f)) == len(f) >= 3 for f in mat)
    assert set(dem_canh.values()) == {2}           # mỗi cạnh thuộc đúng hai mặt: khép kín, không cạnh treo
    k = LABELS[rid]["k"]
    assert sorted(len(f) for f in mat) == sorted([k, k] + [4] * k)


def test_metric_dan_xuat_tu_de_khong_tu_bo_cuc():
    _, sp = hop_dong_va_chuong_trinh("X1_side_height")
    assert do_luong_cua(LABELS["X1_side_height"]["text"], sp) is not None
    _, sp2 = hop_dong_va_chuong_trinh("NX1_missing_height")
    assert do_luong_cua(LABELS["NX1_missing_height"]["text"], sp2) is None
    _, sp3 = hop_dong_va_chuong_trinh("NX2_contradiction")
    assert do_luong_cua(LABELS["NX2_contradiction"]["text"], sp3) is None


@pytest.mark.parametrize("rid", sorted(LABELS))
def test_bo_doc(rid):
    r = LABELS[rid]
    de = che_muc_tieu(r["text"])
    rb = doc_rang_buoc(de)
    kind = {3: "base_equilateral", 6: "base_regular_hexagon"}.get(r["k"])
    co = any(x.kind == "right_prism" for x in rb) and any(x.kind == kind and set(x.entities) == set(r["base"])
                                                         for x in rb)
    assert co == r["text_states_regular_right_prism"], [(x.kind, x.entities) for x in rb]
    if co:
        assert not phan_chua_doc(de)


_EUCLID = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]     # tam giác đều cạnh √2 trên x + y + z = 1; pháp tuyến (1, 1, 1)


@pytest.mark.parametrize("de, mong", [
    ("Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng √2, chiều cao bằng √3. "
     "Tính thể tích khối lăng trụ ABC.A'B'C'.", "3/2"),
    ("Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng √2, chiều cao bằng 2√3. "
     "Tính thể tích khối lăng trụ ABC.A'B'C'.", "3"),              # chiều cao của ĐỀ quyết, không phải bố cục
    ("Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng √2. "
     "Tính thể tích khối lăng trụ ABC.A'B'C'.", "refused"),        # đề không cố định chiều cao
], ids=["cao_khop", "cao_de_khac_bo_cuc", "thieu_cao"])
def test_bo_cuc_euclid(de, mong, monkeypatch):
    """Bố cục Euclid (không phải lưới khung) vẫn đúng theo đề; thiếu chiều cao ⇒ đáp số phụ thuộc giả định ⇒ từ chối."""
    monkeypatch.setitem(LABELS, "_e", {**LABELS["T1_side_height"], "text": de, "dims": {}})
    c, sp = cases.hop_dong_va_chuong_trinh("_e")
    p = sp.model_dump(mode="json", exclude_none=True)
    ten = ["A", "B", "C", "A_prime", "B_prime", "C_prime"]
    for m in p["memory_declarations"]:
        if m["type"] == "point3":
            i = ten.index(m["name"])
            m["initial_value"] = [str(x + (i >= 3)) for x in _EUCLID[i % 3]]
    sp = SemanticProgramSpec.model_validate(p)
    out = verify_and_compile(c, sp)
    if mong == "refused":
        assert (out.servable, out.reason_code) == (False, "ASSUMPTION_DETERMINES_ANSWER")
        return
    assert out.servable and out.assumption_certificate == "C1"
    assert next(o["value"] for o in _dung_scene3d(sp, c)["objects"] if o["id"] == "V") == mong


_LUC_GIAC = {"A": [1, -1, 0], "B": [1, 0, -1], "C": [0, 1, -1], "D": [-1, 1, 0], "E": [-1, 0, 1], "F": [0, -1, 1]}
_TAM_GIAC = {"A": [1, 0, 0], "B": [0, 1, 0], "C": [0, 0, 1]}


@pytest.mark.parametrize("day, ten, dich, them, mong", [
    (_LUC_GIAC, "lục giác đều", [1, 1, 1], "", "served:9"),       # cạnh √2, cao √3: (3√3/2)·2·√3
    (_LUC_GIAC, "lục giác đều", [1, 1, 0], "", "refused"),        # cạnh bên không ⊥ đáy
    (_TAM_GIAC, "tam giác đều", [1, 1, 1], "", "served:3/2"),     # (√3/4)·2·√3
    (_TAM_GIAC, "tam giác đều", [2, 1, 0], "", "refused"),
    (_LUC_GIAC, "lục giác đều", [1, 1, 1], " có cạnh bên bằng √3", "served:9"),   # cạnh bên lăng trụ = AA′, không
    (_TAM_GIAC, "tam giác đều", [1, 1, 1], " có cạnh bên bằng √3", "served:3/2"),  # phải cạnh bên chóp
    (_TAM_GIAC, "tam giác đều", [1, 1, 1], " có cạnh bên bằng 2", "refused"),
    (_LUC_GIAC, "lục giác đều", [1, 1, 1], " có cạnh đáy bằng 1", "refused"),
], ids=["luc_giac_dung", "luc_giac_xien", "tam_giac_dung", "tam_giac_xien", "luc_giac_canh_ben", "tam_giac_canh_ben",
        "tam_giac_canh_ben_sai", "luc_giac_canh_day_sai"])
def test_c0_lang_tru_deu_toa_do(day, ten, dich, them, mong, monkeypatch):
    """C0: đề cho toạ độ mọi đỉnh — Euclid kiểm khẳng định 'lăng trụ … đều' trên chính toạ độ ấy."""
    sys.path.insert(0, str(RUNS / "c0-whole-solid-grounding" / "diagnostics"))
    import c0_whole_solid_cases as M
    pts = {**day, **{p + "'": [a + b for a, b in zip(v, dich)] for p, v in day.items()}}
    n, t = "".join(day), "".join(p + "'" for p in day)
    monkeypatch.setitem(M.LABELS, "_lt", {
        "text": f"Cho hình lăng trụ {ten} {n}.{t}{them} với {{coords}}. Tính thể tích khối lăng trụ {n}.{t}.",
        "points": pts, "solid": {"kind": "prism", "base": list(day), "top": [p + "'" for p in day]}})
    _de, c, sp = M.hop_dong_va_chuong_trinh("_lt")
    out = verify_and_compile(c, sp)
    if mong == "refused":
        assert (out.servable, out.reason_code) == (False, "SOURCE_SHAPE_CONTRADICTS_COORDINATES")
        return
    assert out.servable and out.assumption_certificate == "C0"
    v = Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"]))
    assert v == Fraction(mong.split(":")[1])


def test_lang_tru_xien_day_deu_khong_la_lang_tru_deu():
    """"lăng trụ xiên tam giác đều" — đáy đều nhưng XIÊN: không phát `right_prism`/đáy đều (T12 không áp), "đều" chưa đọc."""
    de = "Cho hình lăng trụ xiên tam giác đều ABC.DEF có AB = 3. Tính thể tích khối lăng trụ ABC.DEF."
    kinds = {r.kind for r in doc_rang_buoc(de)}
    assert "right_prism" not in kinds and "base_equilateral" not in kinds and "oblique_prism" in kinds
    assert phan_chua_doc(de)
