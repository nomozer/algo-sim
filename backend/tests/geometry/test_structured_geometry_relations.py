# -*- coding: utf-8 -*-
"""`FACT_GRAPH_CONTRACT_EXTENSION` — quan hệ vuông góc thành dữ kiện CÓ KIỂU.

Điều wave này phải chứng minh, và điều nó KHÔNG được chứng minh nhầm:

  ✔ cùng một quan hệ cấu trúc, lời văn khác nhau ⇒ CÙNG một FactGraph;
  ✔ có câu *"vuông góc"* mà không có quan hệ cấu trúc ⇒ compiler TỪ CHỐI;
  ✔ có quan hệ cấu trúc mà câu văn không nhắc *"vuông góc"* ⇒ compiler NHẬN;
  ✔ quan hệ suy ra mang `DERIVED` và nêu được cha;
  ✘ **không** chứng minh mô hình thật khai đúng ô mới — đó là việc của một lượt
    live, và wave này cố ý không gọi provider.

Nền đỏ tại `e043ca6` (đo trước khi sửa, bằng chính API lúc ấy):
`WORDING_INVARIANCE = False` · câu văn đơn thuần cho `eligibility = SUPPORTED` ·
`RequestContract` không có trường quan hệ nào.
"""
from __future__ import annotations

import ast
import inspect
import json
from fractions import Fraction

import pytest

from app.simulation.geometry_compiler import compiler as C
from app.simulation.geometry_compiler import contract_adapter as A
from app.simulation.semantic_program import structured_relations as SR
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)
from app.simulation.semantic_program.scale_normalization import SourceInvariant
from app.simulation.semantic_program.structured_relations import (
    GeometricRelation,
)

R = GeometricRelation


# ══ FIXTURE — THAM SỐ HOÁ HOÀN TOÀN ════════════════════════════════════════
def hop_dong(dv="A", c1="B", c2="C", ap="S", l1="3", l2="4", cao="5", *,
             quan_he=None, loi_van=None, witness="the_tich_khoi",
             them_do_dai=()):
    """Hợp đồng của họ bài. Quan hệ và LỜI VĂN là hai tham số ĐỘC LẬP.

    Tách chúng ra là toàn bộ điểm của wave: đổi lời văn mà giữ quan hệ, hoặc
    giữ lời văn mà bỏ quan hệ, phải cho hai kết quả khác nhau một cách có luật.
    """
    bb = [SourceInvariant(points=p, expected=e, source_fact_id=f,
                          scale_symbol="", source_text="")
          for p, e, f in ((( dv, c1), l1, "f_l1"), ((dv, c2), l2, "f_l2"),
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
    de = (f"Cho hình chóp {ap}.{dv}{c1}{c2}. "
          + ". ".join(loi_van) + ". Tính thể tích khối chóp.")
    return RequestContract(
        obligations=(Obligation(kind="volume", container="khoi_chop",
                                params={"witness": witness}),),
        input_facts=facts, source_invariants=tuple(bb),
        geometric_relations=tuple(quan_he), problem_text=de)


def _graph(**kw):
    return A.build_fact_graph(hop_dong(**kw))


def _the_tich(l1, l2, cao) -> Fraction:
    return Fraction(l1) * Fraction(l2) / 2 * Fraction(cao) / 3


# ══ A · B — HAI QUAN HỆ PARSE VÀ CHUẨN HOÁ ĐÚNG ════════════════════════════
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


# ══ C · D — CHUẨN HOÁ KHÔNG PHỤ THUỘC THỨ TỰ ═══════════════════════════════
@pytest.mark.parametrize("d1,d2", [(("A", "B"), ("A", "C")),
                                   (("B", "A"), ("A", "C")),
                                   (("A", "B"), ("C", "A")),
                                   (("B", "A"), ("C", "A"))])
def test_C_AB_va_BA_la_CUNG_mot_duong(d1, d2):
    """Và cặp đường cũng chính tắc: đổi chỗ hai đường không tạo quan hệ mới."""
    goc = _graph().graph.graph_hash()
    kw = dict(quan_he=(
        R(kind="perpendicular_lines", line=d1, other_line=d2,
          source_fact_id="f_day"),
        R(kind="perpendicular_line_plane", line=("S", "A"),
          plane=("A", "B", "C"), source_fact_id="f_cao_vg")))
    assert _graph(**kw).graph.graph_hash() == goc


@pytest.mark.parametrize("mat", [("A", "B", "C"), ("A", "C", "B"),
                                 ("B", "A", "C"), ("B", "C", "A"),
                                 ("C", "A", "B"), ("C", "B", "A")])
def test_D_moi_hoan_vi_mat_phang_cho_CUNG_mot_graph(mat):
    goc = _graph().graph.graph_hash()
    kw = dict(quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          source_fact_id="f_day"),
        R(kind="perpendicular_line_plane", line=("S", "A"), plane=mat,
          source_fact_id="f_cao_vg")))
    assert _graph(**kw).graph.graph_hash() == goc


# ══ E · F · G — TỪ CHỐI CÓ TÊN ═════════════════════════════════════════════
def test_E_point_reference_khong_ton_tai_bi_TU_CHOI():
    kq = _graph(quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "Z"),
          source_fact_id="f_day"),))
    assert kq.status == "INVALID_STRUCTURED_RELATION"
    assert kq.reason_code == SR.MA_REFERENCE_UNKNOWN
    assert kq.graph is None


@pytest.mark.parametrize("d", [("A", "A"), ("A",), ()])
def test_F_line_suy_bien_bi_TU_CHOI(d):
    kq = _graph(quan_he=(
        R(kind="perpendicular_lines", line=d, other_line=("A", "C"),
          source_fact_id="f_day"),))
    assert kq.reason_code == SR.MA_LINE_DEGENERATE


@pytest.mark.parametrize("m", [("A", "B", "B"), ("A", "B"), ("A", "B", "C", "S")])
def test_G_plane_suy_bien_bi_TU_CHOI(m):
    kq = _graph(quan_he=(
        R(kind="perpendicular_line_plane", line=("S", "A"), plane=m,
          source_fact_id="f_cao_vg"),))
    assert kq.reason_code == SR.MA_PLANE_DEGENERATE


def test_G2_o_SAI_duoc_dien_bi_TU_CHOI():
    """`perpendicular_lines` mà điền `plane` ⇒ hợp đồng nói một đằng hiểu một nẻo."""
    kq = _graph(quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          plane=("A", "B", "C"), source_fact_id="f_day"),))
    assert kq.reason_code == SR.MA_RELATION_INVALID


def test_G3_kind_ngoai_bang_dong_bi_TU_CHOI():
    kq = _graph(quan_he=(
        R(kind="parallel_lines", line=("A", "B"), other_line=("A", "C"),
          source_fact_id="f_day"),))
    assert kq.reason_code == SR.MA_RELATION_INVALID


# ══ H — KHỬ TRÙNG TẤT ĐỊNH ═════════════════════════════════════════════════
def test_H_quan_he_trung_duoc_khu_TAT_DINH():
    lap = (
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          source_fact_id="f_day"),
        R(kind="perpendicular_lines", line=("B", "A"), other_line=("C", "A"),
          source_fact_id="f_day"),        # cùng quan hệ, viết ngược
        R(kind="perpendicular_line_plane", line=("S", "A"),
          plane=("A", "B", "C"), source_fact_id="f_cao_vg"),
        R(kind="perpendicular_line_plane", line=("A", "S"),
          plane=("C", "B", "A"), source_fact_id="f_cao_vg"),
    )
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=lap))
    assert kq.hop_le
    assert len(kq.relations) == 2, "không khử trùng"
    assert _graph(quan_he=lap).graph.graph_hash() == _graph().graph.graph_hash()


def test_H2_khu_trung_GIU_ban_truy_duoc_ve_de():
    """Trùng khoá mà một bản là giả định ⇒ bản CÓ XUẤT XỨ phải thắng."""
    kq = SR.kiem_va_chuan_hoa(hop_dong(quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          source_fact_id=None, model_assumption=True),
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          source_fact_id="f_day"),
    )))
    assert len(kq.relations) == 1
    assert kq.relations[0].dung_duoc_cho_tang_dung()


# ══ I · J · K — ĐỘC LẬP VỚI LỜI VĂN ════════════════════════════════════════
@pytest.mark.parametrize("loi_van", [
    ("tam giác ABC vuông tại A", "SA ⊥ (ABC)"),
    ("tam giác ABC có góc A là góc vuông", "SA vuông góc mặt phẳng đáy"),
    ("triangle ABC is right-angled at A", "SA is perpendicular to plane ABC"),
    ("đáy là tam giác   ABC   ,   góc  A  =  90 độ", "cạnh bên SA dựng đứng"),
    ("hai cạnh góc vuông xuất phát từ A", "đường cao hạ từ S"),
])
def test_I_CUNG_quan_he_moi_loi_van_cho_CUNG_FactGraph(loi_van):
    """Nền đỏ `e043ca6`: hai dòng đầu đã cho hai graph KHÁC nhau."""
    assert _graph(loi_van=loi_van).graph.graph_hash() == \
        _graph().graph.graph_hash()


def test_J_co_cau_vuong_goc_ma_KHONG_co_quan_he__UNSUPPORTED():
    """Nền đỏ `e043ca6`: ca này cho `SUPPORTED`. Nay phải từ chối CÓ TÊN."""
    lv = ("tam giác ABC vuông tại A",
          "SA vuông góc với mặt phẳng (ABC)")
    kq = _graph(quan_he=(), loi_van=lv)
    assert kq.status == "VALID", "thiếu quan hệ không phải hợp đồng HỎNG"
    assert "vuông góc" in hop_dong(quan_he=(), loi_van=lv).problem_text
    el = C.danh_gia_eligibility(kq.graph)
    assert el.status == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"
    assert C.bien_dich(kq.graph).program is None


def test_J2_thieu_RIENG_quan_he_day__van_tu_choi_co_ten():
    kq = _graph(quan_he=(
        R(kind="perpendicular_line_plane", line=("S", "A"),
          plane=("A", "B", "C"), source_fact_id="f_cao_vg"),))
    el = C.danh_gia_eligibility(kq.graph)
    assert el.status == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"
    assert el.reason_code == "BASE_PERPENDICULAR_RELATION_MISSING"


def test_K_co_quan_he_ma_loi_van_KHONG_nhac_vuong_goc__SUPPORTED():
    lv = ("đáy là một tam giác", "cạnh bên đi từ đỉnh")
    hd = hop_dong(loi_van=lv)
    assert "vuông góc" not in hd.problem_text and "⊥" not in hd.problem_text
    kq = A.build_fact_graph(hd)
    assert C.danh_gia_eligibility(kq.graph).status == "SUPPORTED"
    assert C.bien_dich(kq.graph).status == "COMPILED"


# ══ L · M — TỔNG QUÁT ══════════════════════════════════════════════════════
def test_L_doi_nhan_diem_van_dung():
    bd = C.bien_dich(_graph(dv="P", c1="M", c2="N", ap="Q").graph)
    assert bd.status == "COMPILED"
    v = V.validate_semantic_program(bd.program)
    assert v.ok, v.error


@pytest.mark.parametrize("l1,l2,cao", [("5/2", "4", "9"), ("7/3", "6/5", "2"),
                                       ("1", "1", "1")])
def test_M_do_dai_PHAN_SO_cho_dap_so_dung(l1, l2, cao):
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )

    bd = C.bien_dich(_graph(l1=l1, l2=l2, cao=cao).graph)
    v = V.validate_semantic_program(bd.program)
    assert v.ok, v.error
    mem = SemanticProgramInterpreter().execute(v.spec).final_memory
    assert Fraction(str(mem["the_tich_khoi"])) == _the_tich(l1, l2, cao)


# ══ N · O · P — XUẤT XỨ GIVEN / DERIVED ════════════════════════════════════
def test_N_quan_he_DE_CHO_duoc_ghi_GIVEN():
    g = _graph().graph
    day = [f for f in g.fact_theo_loai("perpendicular_lines")
           if f.args == ("A", "B", "A", "C")]
    assert len(day) == 1
    assert day[0].status == "GIVEN"
    assert day[0].source_fact_id == "f_day"
    assert day[0].derived_from == (), "dữ kiện đề cho không có cha"

    lp = g.fact_theo_loai("perpendicular_line_plane")
    assert len(lp) == 1 and lp[0].status == "GIVEN"
    assert lp[0].source_fact_id == "f_cao_vg"


def test_O_quan_he_SUY_RA_mang_DERIVED_va_NEU_DUOC_CHA():
    g = _graph().graph
    co = {f.fact_id: f for f in g.facts}
    suy = [f for f in g.fact_theo_loai("perpendicular_lines")
           if f.status == "DERIVED"]
    assert {f.args for f in suy} == {("A", "B", "A", "S"),
                                     ("A", "C", "A", "S"),
                                     ("A", "S", "B", "C")}
    for f in suy:
        assert f.source_fact_id is None, "suy ra thì KHÔNG phải đề cho"
        cha = [co[p] for p in f.derived_from]
        assert len(cha) == 2, f.fact_id
        # Cha thứ nhất: quan hệ đường–mặt nguồn. Cha thứ hai: bằng chứng đoạn
        # nằm trong mặt phẳng ấy, qua chính các tham chiếu điểm.
        assert {c.kind for c in cha} == {"perpendicular_line_plane",
                                         "lies_in_plane"}
        nguon = next(c for c in cha if c.kind == "perpendicular_line_plane")
        assert nguon.status == "GIVEN"
        nam = next(c for c in cha if c.kind == "lies_in_plane")
        assert set(nam.args[:2]) <= set(nguon.args[2:])


def test_O2_cha_bien_mat_thi_dung_graph_NEM():
    from app.simulation.geometry_compiler.fact_graph import (
        Fact, MauThuanFact, Nut, dung_graph,
    )

    with pytest.raises(MauThuanFact) as e:
        dung_graph((Nut("A", "point"),), (
            Fact("p", "perpendicular_lines", ("A", "B", "A", "S"), "TRUE",
                 None, "DERIVED", ("khong_co_that",)),))
    assert e.value.ma == "DERIVED_RELATION_PARENT_MISSING"


def test_O3_suy_ra_ma_KHONG_neu_cha_thi_dung_graph_NEM():
    from app.simulation.geometry_compiler.fact_graph import (
        Fact, MauThuanFact, Nut, dung_graph,
    )

    with pytest.raises(MauThuanFact) as e:
        dung_graph((Nut("A", "point"),), (
            Fact("p", "perpendicular_lines", ("A", "B", "A", "S"), "TRUE",
                 None, "DERIVED"),))
    assert e.value.ma == "DERIVED_RELATION_WITHOUT_PROOF"


@pytest.mark.parametrize("rel", [
    R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
      source_fact_id="f_day", model_assumption=True),
    R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
      source_fact_id=None),
])
def test_P_quan_he_KHONG_grounded_khong_duoc_lam_GIVEN(rel):
    kq = _graph(quan_he=(rel, R(
        kind="perpendicular_line_plane", line=("S", "A"),
        plane=("A", "B", "C"), source_fact_id="f_cao_vg")))
    assert kq.status == "VALID"
    assert "RELATION_NOT_GROUNDED" in kq.diagnostics
    day = [f for f in kq.graph.fact_theo_loai("perpendicular_lines")
           if f.args == ("A", "B", "A", "C")]
    assert day == [], "quan hệ chưa xác nhận đã lẻn vào graph"
    assert C.danh_gia_eligibility(kq.graph).status == \
        "UNSUPPORTED_STRUCTURED_RELATION_MISSING"


def test_P2_he_qua_SUY_RA_khong_the_lam_day_vuong():
    """`SA ⟂ AB` là DERIVED, nên nó KHÔNG được đóng vai tam giác đáy vuông.

    Không có luật này thì một quan hệ đường–mặt duy nhất tự nó sinh ra một đáy
    vuông — tức một hệ quả hoá thành dữ kiện thứ hai.
    """
    kq = _graph(quan_he=(R(kind="perpendicular_line_plane", line=("S", "A"),
                           plane=("A", "B", "C"),
                           source_fact_id="f_cao_vg"),))
    suy = [f for f in kq.graph.fact_theo_loai("perpendicular_lines")]
    assert suy and all(f.status == "DERIVED" for f in suy)
    assert C.danh_gia_eligibility(kq.graph).status == \
        "UNSUPPORTED_STRUCTURED_RELATION_MISSING"


# ══ Q · R — ĐƯỜNG COMPILER SẠCH CÂU CHỮ ════════════════════════════════════
def _hang_chuoi_khong_docstring(mod) -> set[str]:
    """Hằng chuỗi CÓ VAI TRÒ TÍNH TOÁN — bỏ docstring của module/hàm/lớp.

    ⚠️ Bản đầu của `test_Q` quét thẳng mọi `ast.Constant` và đỏ vì chính
    docstring của adapter giải thích *"bộ đọc vuông góc đã gỡ"*. Một guard bắt
    lời giải thích về thứ nó cấm thì nó đang đo văn xuôi, không đo mã.
    """
    cay = ast.parse(inspect.getsource(mod))
    bo = set()
    for n in ast.walk(cay):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            d = ast.get_docstring(n, clean=False)
            if d is not None:
                bo.add(d)
    return {n.value for n in ast.walk(cay)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and n.value not in bo}


def test_Q_duong_compiler_KHONG_con_bo_doc_tu_vung_van_ban():
    """Bộ đọc từ vựng của `/1` đã GỠ HẲN, không chuyển sang chế độ legacy.

    ⚠️ Cấm CHỮ là sai hướng, và bản đầu của test này đã sai đúng thế: compiler
    **phải** viết ra *"cạnh góc vuông thứ nhất"* — đó là lời giải thích cho
    người học, tức ĐẦU RA. Thứ phải cấm là phép ĐỐI SÁNH VĂN BẢN: không `re`,
    không `x in "chuỗi"`, không `.find`/`.index`/`.lower`/`.strip`. Một module
    không có phép đối sánh nào thì không thể đọc câu chữ, dù nó in ra bao nhiêu
    tiếng Việt.
    """
    DOC_VAN_BAN = {"find", "index", "startswith", "endswith", "lower",
                   "upper", "strip", "split", "replace", "count",
                   "finditer", "match", "search", "fullmatch"}
    for mod in (A, C):
        cay = ast.parse(inspect.getsource(mod))
        ten = {n.name for n in ast.walk(cay)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert "_doc_quan_he" not in ten
        assert "_nhan_trong" not in ten

        # Không module nào còn nhập `re`: bộ đọc cũ là nơi duy nhất cần nó.
        assert not any(isinstance(n, (ast.Import, ast.ImportFrom))
                       and "re" in {a.name for a in n.names}
                       for n in ast.walk(cay)), mod.__name__

        for n in ast.walk(cay):
            # `… in "<hằng chuỗi>"` — phép dò chuỗi con.
            if isinstance(n, ast.Compare):
                for op, so in zip(n.ops, n.comparators):
                    if isinstance(op, (ast.In, ast.NotIn)) and \
                            isinstance(so, ast.Constant) and \
                            isinstance(so.value, str):
                        raise AssertionError(f"{mod.__name__} dò chuỗi con")
            # `<gì đó>.find(...)` và họ hàng.
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in DOC_VAN_BAN:
                raise AssertionError(
                    f"{mod.__name__} gọi `.{n.func.attr}` — phép đọc văn bản")


def test_Q2_compiler_KHONG_doc_problem_text():
    for mod in (A, C):
        cay = ast.parse(inspect.getsource(mod))
        doc = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
        assert "problem_text" not in doc, mod.__name__
        assert "problem_text" not in _hang_chuoi_khong_docstring(mod), \
            mod.__name__


def test_R_khong_hard_code_nhan_diem_hay_dap_so():
    """Nhãn một chữ cái và số của bộ ca không được xuất hiện thành hằng."""
    for mod in (A, C, SR):
        cay = ast.parse(inspect.getsource(mod))
        chuoi = _hang_chuoi_khong_docstring(mod)
        assert not (chuoi & {"A", "B", "C", "S", "P", "M", "N", "Q"}), \
            f"{mod.__name__} hard-code nhãn điểm"
        so = {n.value for n in ast.walk(cay)
              if isinstance(n, ast.Constant)
              and isinstance(n.value, (int, float))
              and not isinstance(n.value, bool)}
        assert not (so & {10, 96, 72}), f"{mod.__name__} hard-code đáp số"
        assert "case_id" not in chuoi and "expected" not in chuoi


# ══ S — TƯƠNG THÍCH NGƯỢC ══════════════════════════════════════════════════
def test_S_hop_dong_CU_khong_co_truong_moi_van_parse():
    cu = {"obligations": [{"kind": "volume", "container": "khoi_chop",
                           "params": {"witness": "v"}}],
          "input_facts": [{"fact_id": "f", "label": "l", "values": ["x"]}],
          "problem_text": "đề cũ"}
    hd = RequestContract.model_validate(cu)
    assert hd.geometric_relations == ()
    assert SR.kiem_va_chuan_hoa(hd).relations == ()


def test_S2_truong_moi_KHONG_lam_doi_payload_cua_hop_dong_cu():
    """Hợp đồng cũ đi qua `exclude_defaults` phải trùng BYTE với trước wave."""
    hd = RequestContract(
        obligations=(Obligation(kind="volume", container="k",
                                params={"witness": "v"}),),
        input_facts=(InputFact(fact_id="f", label="l"),),
        problem_text="đề cũ")
    tho = hd.model_dump(mode="json", exclude_defaults=True)
    assert "geometric_relations" not in tho
    assert json.dumps(tho, sort_keys=True, ensure_ascii=False) == json.dumps(
        {"obligations": [{"kind": "volume", "container": "k",
                          "params": {"witness": "v"}}],
         "input_facts": [{"fact_id": "f", "label": "l"}],
         "problem_text": "đề cũ"}, sort_keys=True, ensure_ascii=False)


def test_S3_build_request_contract_KHONG_co_o_moi_van_chay():
    from app.simulation.semantic_program.analyze_contract import (
        build_request_contract,
    )

    hd = build_request_contract(
        {"input_facts": [{"id": "f", "kind": "float", "label": "AB",
                          "value": ["3"]}],
         "obligations": [{"kind": "volume", "container": "khoi",
                          "witness": "v"}]},
        problem_text="Cho AB = 3. Tính thể tích khối.", domain="hinh_hoc")
    assert hd.geometric_relations == ()
    assert len(hd.input_facts) == 1 and len(hd.obligations) == 1


def test_S4_o_moi_duoc_LOC_o_bien_dong_bang():
    from app.simulation.semantic_program.analyze_contract import (
        build_request_contract,
    )

    hd = build_request_contract({
        "input_facts": [], "obligations": [],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"],
             "other_line": ["A", "C"], "source_fact_id": "f"},
            {"kind": "parallel_lines", "line": ["A", "B"]},   # ngoài bảng đóng
            "khong-phai-dict",
        ]}, domain="hinh_hoc")
    assert len(hd.geometric_relations) == 1
    assert hd.geometric_relations[0].kind == "perpendicular_lines"


# ══ T — ĐI TRỌN ĐƯỜNG CỔNG SẢN PHẨM ════════════════════════════════════════
@pytest.fixture(scope="module")
def dung():
    hd = hop_dong()
    kq = A.build_fact_graph(hd)
    assert kq.status == "VALID", kq.reason_code
    bd = C.bien_dich(kq.graph)
    assert bd.status == "COMPILED", bd.reason_code
    return hd, bd


def test_T_chuong_trinh_qua_TOAN_BO_cong(dung):
    from app.ai.pipeline import _dung_scene3d
    from app.simulation.semantic_program.ir_static_check import kiem_tinh
    from app.simulation.semantic_program.route import verify_and_compile
    from app.simulation.semantic_program.visual_obligations import (
        check_visual_obligations,
    )

    hd, bd = dung
    v = V.validate_semantic_program(bd.program)
    assert v.ok, v.error                       # Pydantic + type check
    assert kiem_tinh(v.spec).ok                # IR static check

    kq = verify_and_compile(hd, v.spec)        # grounding + coverage + route
    assert kq.servable, (kq.error_code, kq.stage_reached)
    assert kq.stage_reached == "served"

    canh = _dung_scene3d(v.spec, hd) or {}
    assert canh.get("objects"), "cảnh rỗng"
    tv = check_visual_obligations(hd, canh)
    assert tv.verdict == "COVERED", tv
    assert tv.uncovered_count == 0 and tv.unverifiable_count == 0

    # topology · final_memory · đáp số
    vat = {str(o.get("id")): o for o in canh["objects"]}
    assert sum(1 for o in vat.values() if o.get("type") == "point3") == 4
    assert Fraction(str(kq.final_memory["the_tich_khoi"])) == _the_tich("3", "4", "5")


def test_U_hai_lan_bien_dich_TRUNG_BYTE():
    a = C.bien_dich(_graph().graph)
    b = C.bien_dich(_graph().graph)
    assert json.dumps(a.program, sort_keys=True, ensure_ascii=False) == \
        json.dumps(b.program, sort_keys=True, ensure_ascii=False)
    assert _graph().graph.json_chinh_tac() == _graph().graph.json_chinh_tac()


# ══ V — LƯỢC ĐỒ ↔ PROMPT ═══════════════════════════════════════════════════
def test_V_luoc_do_va_prompt_KHOP_TU_VUNG():
    """Một nguồn định nghĩa trường duy nhất: enum và arity DẪN từ module."""
    from app.simulation.semantic_program.analyze_contract import (
        SEMANTIC_ANALYZE_SCHEMA, analyze_schema_for,
    )

    hh = analyze_schema_for("hinh_hoc")
    o = hh["properties"]["geometric_relations"]["items"]
    assert o["properties"]["kind"]["enum"] == list(SR.RELATION_KINDS)
    for k in ("line", "other_line"):
        assert o["properties"][k]["minItems"] == SR.SO_DIEM_DUONG
        assert o["properties"][k]["maxItems"] == SR.SO_DIEM_DUONG
    assert o["properties"]["plane"]["minItems"] == SR.SO_DIEM_MAT
    assert "source_fact_id" in o["required"] and "kind" in o["required"]

    # Lược đồ Tin học KHÔNG được mang khái niệm hình học.
    assert "geometric_relations" not in SEMANTIC_ANALYZE_SCHEMA["properties"]

    # Prompt phải nhắc ĐÚNG tên ô và tên hai kind — không nhắc thì mô hình
    # không biết ô ấy tồn tại, và một trường không ai điền là một trường chết.
    from app.ai.gemini import SKILLS_DIR

    p = (SKILLS_DIR / "geometry_analyze.md").read_text(encoding="utf-8")
    assert "geometric_relations" in p
    for k in SR.RELATION_KINDS:
        assert k in p, k
    # …và KHÔNG chép lại cả lược đồ vào prompt.
    assert "minItems" not in p and "maxItems" not in p


def test_V2_bang_chung_dung_lai_bam_lich_su_LA_THAT():
    """Băm `analyze_schema`/`prompts` trước wave dựng lại được — và phép dựng
    lại ấy phải ĐỎ ĐƯỢC, nếu không nó chỉ là một lời khai."""
    from tests.photo_problem_identity import PROMPTS_TRUOC_WAVE
    from tests.structured_relation_identity import (
        ANALYZE_SCHEMA_TRUOC_WAVE,
        analyze_schema_neu_chua_them_quan_he,
        prompts_neu_chua_them_muc_quan_he,
    )

    assert analyze_schema_neu_chua_them_quan_he() == ANALYZE_SCHEMA_TRUOC_WAVE
    assert prompts_neu_chua_them_muc_quan_he() == PROMPTS_TRUOC_WAVE

    # Cửa sổ chứng: bỏ một ô KHÁC thì băm KHÔNG được trùng giá trị lịch sử.
    from app.runtime_identity import _bam
    from app.simulation.semantic_program.analyze_contract import (
        SEMANTIC_ANALYZE_SCHEMA, analyze_schema_for,
    )

    hh = analyze_schema_for("hinh_hoc")
    khac = dict(hh)
    khac["properties"] = {k: v for k, v in hh["properties"].items()
                          if k != "obligations"}
    assert _bam(json.dumps([SEMANTIC_ANALYZE_SCHEMA, khac],
                           ensure_ascii=False, sort_keys=True)) \
        != ANALYZE_SCHEMA_TRUOC_WAVE


# ══ W · X · Y — PHẠM VI ĐÃ KHAI ════════════════════════════════════════════
def test_W_thieu_quan_he_tra_ly_do_ON_DINH():
    assert "UNSUPPORTED_STRUCTURED_RELATION_MISSING" in C.TRANG_THAI_ELIGIBILITY
    assert set(SR.MA_QUAN_HE) == {
        SR.MA_REFERENCE_UNKNOWN, SR.MA_LINE_DEGENERATE,
        SR.MA_PLANE_DEGENERATE, SR.MA_RELATION_INVALID}
    assert "INVALID_STRUCTURED_RELATION" in A.TRANG_THAI_ADAPTER


def test_W2_quan_he_hop_le_nhung_NOI_VE_MAT_KHAC_bi_tu_choi():
    """Đường cao vuông góc một mặt phẳng KHÔNG phải đáy ⇒ không khớp khối.

    ⚠️ Đổi fixture ở `STRUCTURED_RELATION_SAFETY_REPAIR`: bản cũ dùng `SA ⟂ (ABS)` —
    đường nằm TRONG chính mặt phẳng nó được khai vuông góc, tức quan hệ suy biến.
    Hệ quả suy ra của nó (`SA ⟂ AB`, `SA ⟂ SB`) làm tam giác SAB vuông ở hai đỉnh, nên
    FactGraph nay bác sớm hơn (xem `test_W2b`). Ý định của test — mặt KHÁC đáy bị
    eligibility từ chối — giữ bằng một mặt KHÔNG suy biến: `SA ⟂ (ABD)`.
    """
    kq = _graph(them_do_dai=((("A", "D"), "2", "f_ad"),), quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          source_fact_id="f_day"),
        R(kind="perpendicular_line_plane", line=("S", "A"),
          plane=("A", "B", "D"), source_fact_id="f_cao_vg"),
    ))
    assert kq.status == "VALID"
    el = C.danh_gia_eligibility(kq.graph)
    assert el.status == "UNSUPPORTED_MISSING_FACT"
    assert el.reason_code in ("LINE_PLANE_INCIDENCE_UNEXPECTED",
                              "BASE_RIGHT_ANGLE_VERTEX_MISMATCH",
                              "BASE_PLANE_MISMATCH")


def test_W2b_duong_vuong_goc_mat_CHUA_chinh_no_la_mau_thuan_bi_bac_o_FactGraph():
    """`SA ⟂ (ABS)`: đường nằm trong mặt ⇒ suy ra SA ⟂ AB (vuông tại A) và SA ⟂ SB (vuông
    tại S) — tam giác SAB vuông ở hai đỉnh. Trước `STRUCTURED_RELATION_SAFETY_REPAIR` điều
    này đi qua FactGraph và chỉ bị eligibility chặn tình cờ; nay FactGraph bác có tên."""
    kq = _graph(them_do_dai=((("B", "C"), "5", "f_bc"),), quan_he=(
        R(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"),
          source_fact_id="f_day"),
        R(kind="perpendicular_line_plane", line=("S", "A"),
          plane=("A", "B", "S"), source_fact_id="f_cao_vg"),
    ))
    assert (kq.status, kq.reason_code) == ("INVALID_CONFLICT", "STRUCTURED_RELATION_CONTRADICTION")
    assert kq.rule_id == "MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE" and kq.graph is None


def test_X_khong_co_request_mang_nao():
    """Wave TẤT ĐỊNH. Guard mạng của `conftest` đã gỡ key và vá transport —
    test này ghim thêm rằng ba module KHÔNG nhắc tới provider."""
    for mod in (A, C, SR):
        src = inspect.getsource(mod)
        for cam in ("httpx", "requests", "gemini", "call_gemini",
                    "ALLOW_LIVE_AI", "GEMINI_API_KEY"):
            assert cam not in src, (mod.__name__, cam)


def test_Y_duong_mac_dinh_VAN_khong_tham_chieu_compiler():
    """`DEFAULT_MODE` giữ `LLM_ONLY`, và không tệp sản phẩm nào nhập gói ấy."""
    from pathlib import Path

    from app.simulation.geometry_compiler import routing as RT

    assert RT.CHE_DO_MAC_DINH == "LLM_ONLY"
    assert RT.che_do({}) == "LLM_ONLY"

    goc = Path(A.__file__).resolve().parents[2]          # backend/app
    assert goc.name == "app", goc
    lo = []
    for p in goc.rglob("*.py"):
        if "geometry_compiler" in p.parts or p.name == "__init__.py":
            continue
        if "geometry_compiler" in p.read_text(encoding="utf-8"):
            lo.append(str(p.relative_to(goc)))
    assert lo == [], f"đường sản phẩm đã tham chiếu compiler: {lo}"
