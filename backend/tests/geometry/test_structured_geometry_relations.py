# -*- coding: utf-8 -*-
"""`structured_relations` (`GeometricRelation`) + lược đồ quan hệ có kiểu + guard không nạp động / không còn module legacy."""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.simulation.semantic_program import structured_relations as SR
from app.simulation.semantic_program.analyze_contract import (
    SEMANTIC_ANALYZE_SCHEMA,
    analyze_schema_for,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import InputFact, RequestContract
from app.simulation.semantic_program.scale_normalization import SourceInvariant
from app.simulation.semantic_program.structured_relations import GeometricRelation

R = GeometricRelation


def hop_dong(dv="A", c1="B", c2="C", ap="S", l1="3", l2="4", cao="5", *,
             quan_he=None, loi_van=None, witness="the_tich_khoi",
             them_do_dai=()):
    bb = [SourceInvariant(points=p, expected=e, source_fact_id=f,
                          scale_symbol="", source_text="")
          for p, e, f in (((dv, c1), l1, "f_l1"), ((dv, c2), l2, "f_l2"),
                          ((dv, ap), cao, "f_cao"), *them_do_dai)]
    if quan_he is None:
        quan_he = (
            R(kind="perpendicular_lines", line=(dv, c1), other_line=(dv, c2),
              source_fact_id="f_day"),
            R(kind="perpendicular_line_plane", line=(ap, dv),
              plane=(dv, c1, c2), source_fact_id="f_cao_vg"),
        )
    if loi_van is None:
        loi_van = (f"tam giác {dv}{c1}{c2} vuông tại {dv}",
                   f"{ap}{dv} ⊥ ({dv}{c1}{c2})")
    facts = tuple(InputFact(fact_id=i, label="quan hệ", values=(t,))
                  for i, t in zip(("f_day", "f_cao_vg"), loi_van))
    do_dai = [(f"{dv}{c1}", l1), (f"{dv}{c2}", l2), (f"{ap}{dv}", cao)] + [
        ("".join(p), e) for p, e, _ in them_do_dai]
    de = (f"Cho hình chóp {ap}.{dv}{c1}{c2}. "
          + ". ".join(loi_van) + ". "
          + ", ".join(f"{s} = {e}" for s, e in do_dai) + ". Tính thể tích khối chóp.")
    return RequestContract(
        obligations=(Obligation(kind="volume", container="khoi_chop",
                                params={"witness": witness}),),
        input_facts=facts, source_invariants=tuple(bb),
        geometric_relations=tuple(quan_he), problem_text=de)


def test_A_perpendicular_lines_parse_va_chuan_hoa():
    kq = SR.kiem_va_chuan_hoa(hop_dong())
    assert kq.hop_le, kq.loi
    q = [x for x in kq.relations if x.kind == "perpendicular_lines"]
    assert len(q) == 1
    assert q[0].args == ("A", "B", "A", "C")
    assert q[0].source_fact_id == "f_day"


def test_B_perpendicular_line_plane_parse_dung():
    kq = SR.kiem_va_chuan_hoa(hop_dong())
    q = [x for x in kq.relations if x.kind == "perpendicular_line_plane"]
    assert len(q) == 1
    assert q[0].duong == ("A", "S") and q[0].mat == ("A", "B", "C")


@pytest.mark.parametrize("d1,d2", [(("A", "B"), ("A", "C")),
                                   (("B", "A"), ("A", "C")),
                                   (("A", "B"), ("C", "A")),
                                   (("B", "A"), ("C", "A"))])
def test_C_AB_va_BA_chuan_hoa_ve_cung_mot_khoa(d1, d2):
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="perpendicular_lines", line=d1, other_line=d2, source_fact_id="f_day"),
    )))
    assert kq.hop_le and kq.relations[0].args == ("A", "B", "A", "C")


@pytest.mark.parametrize("mat", [("A", "B", "C"), ("A", "C", "B"),
                                 ("B", "A", "C"), ("B", "C", "A"),
                                 ("C", "A", "B"), ("C", "B", "A")])
def test_D_moi_hoan_vi_mat_phang_chuan_hoa_ve_cung_mot_bo(mat):
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="perpendicular_line_plane", line=("S", "A"), plane=mat, source_fact_id="f_cao_vg"),
    )))
    assert kq.hop_le and kq.relations[0].mat == ("A", "B", "C")


@pytest.mark.parametrize("d", [("A", "A"), ("A",), ()])
def test_F_line_suy_bien_bi_TU_CHOI(d):
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="perpendicular_lines", line=d, other_line=("A", "C"), source_fact_id="f_day"),
    )))
    assert not kq.hop_le and kq.loi[0].ma == SR.MA_LINE_DEGENERATE


@pytest.mark.parametrize("m", [("A", "B", "B"), ("A", "B"), ("A", "B", "C", "S")])
def test_G_plane_suy_bien_bi_TU_CHOI(m):
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="perpendicular_line_plane", line=("S", "A"), plane=m, source_fact_id="f_cao_vg"),
    )))
    assert not kq.hop_le and kq.loi[0].ma == SR.MA_PLANE_DEGENERATE


def test_G2_o_SAI_duoc_dien_bi_TU_CHOI():
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          plane=("A", "B", "C"), source_fact_id="f_day"),
    )))
    assert not kq.hop_le and kq.loi[0].ma == SR.MA_RELATION_INVALID


def test_G3_kind_ngoai_bang_dong_bi_TU_CHOI():
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="parallel_lines", line=("A", "B"), other_line=("A", "C"), source_fact_id="f_day"),
    )))
    assert not kq.hop_le and kq.loi[0].ma == SR.MA_RELATION_INVALID


def test_H_quan_he_trung_duoc_khu_TAT_DINH():
    lap = (
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"), source_fact_id="f_day"),
        R(kind="perpendicular_lines", line=("B", "A"), other_line=("C", "A"), source_fact_id="f_day"),
        R(kind="perpendicular_line_plane", line=("S", "A"), plane=("A", "B", "C"), source_fact_id="f_cao_vg"),
        R(kind="perpendicular_line_plane", line=("A", "S"), plane=("C", "B", "A"), source_fact_id="f_cao_vg"),
    )
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=lap))
    assert kq.hop_le and len(kq.relations) == 2


def test_H2_khu_trung_GIU_ban_truy_duoc_ve_de():
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"), source_fact_id=None, model_assumption=True),
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"), source_fact_id="f_day"),
    )))
    assert len(kq.relations) == 1 and kq.relations[0].dung_duoc_cho_tang_dung()


def test_V_luoc_do_phan_tich_giu_dung_tu_vung_quan_he():
    hh = analyze_schema_for("hinh_hoc")
    o = hh["properties"]["geometric_relations"]["items"]
    assert o["properties"]["kind"]["enum"] == list(SR.RELATION_KINDS)
    for k in ("line", "other_line"):
        assert o["properties"][k]["minItems"] == SR.SO_DIEM_DUONG
        assert o["properties"][k]["maxItems"] == SR.SO_DIEM_DUONG
    assert o["properties"]["plane"]["minItems"] == SR.SO_DIEM_MAT
    assert "source_fact_id" in o["required"] and "kind" in o["required"]
    assert "geometric_relations" not in SEMANTIC_ANALYZE_SCHEMA["properties"]


def test_W_tap_ma_quan_he_on_dinh():
    assert set(SR.MA_QUAN_HE) == {
        SR.MA_REFERENCE_UNKNOWN,
        SR.MA_LINE_DEGENERATE,
        SR.MA_PLANE_DEGENERATE,
        SR.MA_RELATION_INVALID,
    }


def test_X_structured_relations_khong_co_request_mang_nao():
    src = inspect.getsource(SR)
    for cam in ("httpx", "requests", "gemini", "call_gemini", "ALLOW_LIVE_AI", "GEMINI_API_KEY"):
        assert cam not in src, cam


_NAP_DONG_TEN = {"__import__", "exec", "eval", "compile", "__builtins__", "__loader__"}
_NAP_DONG_THUOC_TINH = {
    "import_module", "__import__", "spec_from_file_location", "spec_from_loader",
    "module_from_spec", "exec_module", "load_module", "find_spec", "find_module", "reload",
}
_NAP_DONG_MODULE = {"importlib", "imp", "builtins", "runpy", "pkgutil", "zipimport"}


def _goc_app() -> Path:
    goc = Path(SR.__file__).resolve().parents[2]
    assert goc.name == "app", goc
    return goc


def _nap_dong(nguon: str) -> list[str]:
    ra = []
    for n in ast.walk(ast.parse(nguon)):
        if isinstance(n, ast.Name) and n.id in _NAP_DONG_TEN:
            ra.append(f"{n.lineno}:{n.id}")
        elif isinstance(n, ast.Attribute) and (n.attr in _NAP_DONG_THUOC_TINH or (
                n.attr == "modules" and isinstance(n.value, ast.Name) and n.value.id == "sys")):
            ra.append(f"{n.lineno}:.{n.attr}")
        elif isinstance(n, ast.Import) and any(a.name.split(".")[0] in _NAP_DONG_MODULE for a in n.names):
            ra.append(f"{n.lineno}:import")
        elif isinstance(n, ast.ImportFrom) and not n.level and (n.module or "").split(".")[0] in _NAP_DONG_MODULE:
            ra.append(f"{n.lineno}:from-import")
    return ra


def test_Y_ma_san_pham_khong_co_co_che_nap_dong():
    goc = _goc_app()
    lo = {str(p.relative_to(goc)): v for p in goc.rglob("*.py") if (v := _nap_dong(p.read_text(encoding="utf-8")))}
    assert lo == {}, f"nạp động trong mã sản phẩm: {lo}"


@pytest.mark.parametrize("cach_lach", [
    '__import__("app.ai." + "function_route")',
    'import importlib\nimportlib.import_module("app.ai." + "function_route")',
    'from importlib import import_module as nap\nnap("app.ai." + "function_route")',
    'getattr(__builtins__, "__imp" + "ort__")("app.ai.function_route")',
    'exec("import app.ai." + "function_route")',
    'import builtins\nbuiltins.__dict__["__imp" + "ort__"]("app.ai.function_route")',
    'import sys\nm = sys.modules["builtins"]',
    'import importlib.util as u\nu.spec_from_file_location("x", "app/ai/function_route.py")',
])
def test_Y_bo_do_bat_moi_cach_lach_import(cach_lach):
    goc_nguon = (_goc_app() / "ai" / "route_policy.py").read_text(encoding="utf-8")
    assert _nap_dong(goc_nguon) == []
    tiem = goc_nguon + "\n\ndef _lach():\n" + "".join(f"    {d}\n" for d in cach_lach.splitlines())
    assert _nap_dong(tiem), cach_lach


def test_Y_ma_san_pham_khong_con_tham_chieu_compiler_cu_hay_pipeline_cu():
    goc = _goc_app()
    assert not (goc / "ai" / "pipeline.py").exists()
    assert not (goc / "ai" / "adapter3_simulation.py").exists()
    assert not (goc / "simulation" / "geometry_compiler").exists()
    for p in goc.rglob("*.py"):
        src = p.read_text(encoding="utf-8")
        assert "geometry_compiler" not in src, p
        assert "adapter3_simulation" not in src, p
        assert "app.ai.pipeline" not in src, p
