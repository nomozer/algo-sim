# -*- coding: utf-8 -*-
"""STRUCTURED_RELATION_SAFETY_REPAIR — một tam giác không thể vuông ở hai đỉnh.

Trước wave này, hợp đồng đọc ĐÚNG đề N04 (đáy GHL vuông tại G VÀ vuông tại H,
cộng DG ⊥ (GHL)) đi qua `kiem_mau_thuan`, compiler chọn góc vuông đầu tiên khớp
chân đường cao, lặng lẽ bỏ quan hệ kia, rồi dựng cảnh và trả đáp số.

Luật mới: với ba điểm PHÂN BIỆT A, B, C, hai quan hệ `AB ⟂ AC` (góc vuông tại A)
và `BA ⟂ BC` (góc vuông tại B) không thể cùng đúng — tổng ba góc của tam giác ABC
đã vượt 180°, và nếu A, B, C thẳng hàng thì không đường nào qua đó vuông góc
được. Hai quan hệ ấy nhắc ĐỦ ba cạnh AB, AC, BC, nên chính chúng xác định tam
giác; adapter không dựng nút `triangle` nào, và luật không cần.

Mọi hợp đồng ở đây dựng TỪ THAM SỐ, có cấu trúc — không output mô hình, không đọc
`problem_text`. 0 request mạng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.simulation.geometry_compiler import compiler as C  # noqa: E402
from app.simulation.geometry_compiler import contract_adapter as A  # noqa: E402
from app.simulation.geometry_compiler import fact_graph as FG  # noqa: E402
from app.simulation.geometry_compiler import routing as R  # noqa: E402
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import InputFact, RequestContract  # noqa: E402
from app.simulation.semantic_program.scale_normalization import SourceInvariant  # noqa: E402
from app.simulation.semantic_program.structured_relations import GeometricRelation  # noqa: E402

MA = "STRUCTURED_RELATION_CONTRADICTION"                      # viết CỨNG — không đọc từ module
LUAT = "MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE"
BAT = {R.BIEN_MOI_TRUONG: R.CHE_DO_COMPILER}
DGEO = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"


# ══ FIXTURE ═════════════════════════════════════════════════════════════════
def ll(p, q, r, s, src="f", ma=False):
    return GeometricRelation(kind="perpendicular_lines", line=(p, q), other_line=(r, s),
                             source_fact_id=src, model_assumption=ma)


def lp(p, q, mat, src="f", ma=False):
    return GeometricRelation(kind="perpendicular_line_plane", line=(p, q), plane=tuple(mat),
                             source_fact_id=src, model_assumption=ma)


def hd(do_dai: list[tuple[str, str, str]], quan_he: list, *, them_nguon=()) -> RequestContract:
    """`RequestContract` có cấu trúc: độ dài (điểm, điểm, giá trị) + quan hệ + một nghĩa vụ thể tích."""
    bb = tuple(SourceInvariant(points=(p, q), expected=v, source_fact_id=f"f_len_{p}{q}",
                               scale_symbol="", source_text="") for p, q, v in do_dai)
    nguon = sorted({r.source_fact_id for r in quan_he if r.source_fact_id} | set(them_nguon))
    facts = tuple(InputFact(fact_id=n, label="quan hệ đề cho", values=("quan hệ",)) for n in nguon)
    diem = sorted({x for p, q, _ in do_dai for x in (p, q)})
    de = "Cho các điểm " + ", ".join(diem) + ". " + " ".join(f"{p}{q} = {v}." for p, q, v in do_dai)
    return RequestContract(obligations=(Obligation(kind="volume", container="khoi",
                                                   params={"witness": "the_tich"}),),
                           input_facts=facts, source_invariants=bb,
                           geometric_relations=tuple(quan_he), problem_text=de)


def chop(ap="S", a="A", b="B", c="C", l1="3", l2="4", cao="5", them=(), day=True):
    """Chóp đáy vuông tại `a`, cạnh bên `ap a` ⊥ đáy — cộng các quan hệ THÊM."""
    qh = ([ll(a, b, a, c, "f_day")] if day else []) + [lp(ap, a, (a, b, c), "f_cao")] + list(them)
    return hd([(a, b, l1), (a, c, l2), (a, ap, cao)], qh)


def n04_tu_registry() -> RequestContract:
    """N04 dựng TỪ registry quan hệ đề nói đã đăng ký (không output mô hình) + độ dài của đề."""
    reg = json.loads((DGEO / "completion-runner-repair-offline"
                      / "NEGATIVE_EXPLICIT_RELATION_REGISTRY.json").read_text(encoding="utf-8"))
    qh = []
    for i, r in enumerate(reg["CASES"]["N04"]["relations"]):
        if r["kind"] == "perpendicular_lines":
            qh.append(ll(*r["line"], *r["other_line"], src=f"reg_{i}"))
        else:
            qh.append(lp(*r["line"], r["plane"], src=f"reg_{i}"))
    return hd([("G", "H", "4"), ("G", "L", "7"), ("D", "G", "5")], qh)


def _chung_cu(kq) -> dict[str, str]:
    return dict(kq.evidence)


# ══ N04 — QUA ADAPTER, ELIGIBILITY, COMPILER, ĐỊNH TUYẾN VÀ RUNNER THẬT ═══
def test_N04_adapter_that_TU_CHOI_bang_ma_va_luat_on_dinh():
    kq = A.build_fact_graph(n04_tu_registry())
    assert kq.status == "INVALID_CONFLICT" and kq.graph is None
    assert kq.reason_code == MA and kq.rule_id == LUAT
    cc = _chung_cu(kq)
    assert cc["DISTINCT_RIGHT_ANGLE_VERTEX_COUNT"] == "2" and cc["PHASE"] == "FACT_GRAPH"
    assert cc["RULE_ID"] == LUAT and len(cc["TRIANGLE_SHA256"]) == 64
    # Chẩn đoán là TỪ VỰNG ĐÓNG: không nhãn điểm, không câu chữ của đề.
    assert kq.diagnostics == ("DISTINCT_RIGHT_ANGLE_VERTEX_COUNT=2", "PHASE=FACT_GRAPH",
                              f"RULE_ID={LUAT}")


def test_N04_dinh_tuyen_TU_CHOI_va_compiler_KHONG_BAO_GIO_duoc_goi(monkeypatch):
    goi: list[str] = []
    goc_el, goc_bd = C.danh_gia_eligibility, C.bien_dich
    monkeypatch.setattr(C, "danh_gia_eligibility", lambda g: (goi.append("el"), goc_el(g))[1])
    monkeypatch.setattr(C, "bien_dich", lambda g: (goi.append("bd"), goc_bd(g))[1])
    qd = R.quyet_dinh_dinh_tuyen(n04_tu_registry(), BAT)
    assert qd.decision == "REFUSE" and qd.reason_code == MA and qd.program is None
    assert goi == [], "compiler bị gọi sau khi FactGraph đã từ chối"


def test_N04_duong_tich_hop_runner_KHONG_program_canh_memory_dap_so(monkeypatch):
    import run_multicase_benchmark as B
    goi: list[str] = []
    goc_bd = C.bien_dich
    monkeypatch.setattr(C, "bien_dich", lambda g: (goi.append("bd"), goc_bd(g))[1])
    ca = B.ca_theo_id(B.doc_registry())["N04"]
    ds = B.chay_tang_dung(n04_tu_registry(), ca, {
        "expected_derived_perpendicular": [], "point_count": 4, "face_count": 4, "edge_count": 6,
        "squared_lengths": {"leg_1": "0", "leg_2": "0", "height": "0"}, "volume": "0"})
    assert ds["ADAPTER_STATUS"] == "INVALID_CONFLICT" and ds["REJECTION_CODE"] == MA
    assert ds["COMPILE_STATUS"] == "NO_GRAPH" and goi == []
    for k in ("PROGRAM_SHA256", "_ENVELOPE", "ENVELOPE_SHA256", "FINAL_MEMORY_OK", "ANSWER_OK",
              "SCENE_NON_EMPTY", "ROUTE_RESULT"):
        assert k not in ds, k


def _graph_mau_thuan_bo_qua_dung_graph() -> FG.GeometryFactGraph:
    """Graph MÂU THUẪN dựng TRỰC TIẾP, vòng qua `dung_graph` — để chứng minh compiler fail closed."""
    kq = A.build_fact_graph(chop())
    assert kq.status == "VALID"
    them = FG.Fact(fact_id="perp_lines__A_B__B_C", kind="perpendicular_lines",
                   args=("A", "B", "B", "C"), value="TRUE", source_fact_id="f_x", status="GIVEN")
    return FG.GeometryFactGraph(nodes=kq.graph.nodes, facts=kq.graph.facts + (them,))


def test_compiler_goi_TRUC_TIEP_voi_graph_mau_thuan_thi_FAIL_CLOSED():
    g = _graph_mau_thuan_bo_qua_dung_graph()
    el = C.danh_gia_eligibility(g)
    assert el.status == "INVALID_CONFLICT" and el.binding is None and el.reason_code == MA
    bd = C.bien_dich(g)
    assert bd.status == "NOT_ELIGIBLE" and bd.program is None and bd.reason_code == MA
    assert not bd.construction_steps


def test_dinh_tuyen_TU_CHOI_chu_khong_LUI_VE_LLM_khi_compiler_bao_mau_thuan(monkeypatch):
    g = _graph_mau_thuan_bo_qua_dung_graph()
    monkeypatch.setattr(A, "build_fact_graph", lambda c: A.KetQuaAdapter("VALID", g))
    qd = R.quyet_dinh_dinh_tuyen(chop(), BAT)
    assert qd.decision == "REFUSE", "mâu thuẫn mà lùi về LLM là mời nó chọn một nửa"
    assert qd.reason_code == MA


# ══ A — MÂU THUẪN: phải bác, bất kể nhãn, chiều cạnh, thứ tự, xuất xứ ═════
@pytest.mark.parametrize("ap,a,b,c", [("D", "G", "H", "L"), ("S", "A", "B", "C"),
                                      ("T", "P", "Q", "R")], ids=["GHL", "ABC", "PQR"])
def test_A_vuong_tai_hai_dinh_bi_bac_moi_bo_nhan(ap, a, b, c):
    kq = A.build_fact_graph(chop(ap, a, b, c, them=[ll(b, a, b, c, "f_hai")]))
    assert (kq.status, kq.reason_code, kq.rule_id) == ("INVALID_CONFLICT", MA, LUAT)
    assert _chung_cu(kq)["DISTINCT_RIGHT_ANGLE_VERTEX_COUNT"] == "2"


def test_A_dao_dau_mut_moi_canh_van_bi_bac():
    qh = [ll("C", "A", "B", "A", "f_day"), lp("A", "S", ("C", "B", "A"), "f_cao"),
          ll("C", "B", "A", "B", "f_hai")]
    kq = A.build_fact_graph(hd([("A", "B", "3"), ("A", "C", "4"), ("A", "S", "5")], qh))
    assert (kq.status, kq.reason_code) == ("INVALID_CONFLICT", MA)


def test_A_dao_thu_tu_quan_he_van_bi_bac_va_cung_bang_chung():
    xuoi = A.build_fact_graph(chop(them=[ll("B", "A", "B", "C", "f_hai")]))
    nguoc = A.build_fact_graph(hd([("A", "B", "3"), ("A", "C", "4"), ("A", "S", "5")],
                                  [ll("B", "A", "B", "C", "f_hai"), lp("S", "A", ("A", "B", "C"), "f_cao"),
                                   ll("A", "B", "A", "C", "f_day")]))
    assert nguoc.reason_code == xuoi.reason_code == MA
    assert _chung_cu(nguoc) == _chung_cu(xuoi)


def test_A_mot_quan_he_EXPLICIT_mot_DEFINITIONAL_van_bi_bac():
    """Luật không đọc câu chữ: nguồn 'tam giác vuông tại B' và nguồn 'AB ⊥ AC' như nhau."""
    c = chop(them=[ll("B", "A", "B", "C", "f_tam_giac_vuong_tai_B")])
    kq = A.build_fact_graph(c)
    assert kq.reason_code == MA
    assert "f_tam_giac_vuong_tai_B" in _chung_cu(kq)["SOURCE_FACT_IDS"].split(",")


def test_A_mot_GIVEN_mot_DERIVED_co_xuat_xu_van_bi_bac():
    """SA ⊥ (ABC) SUY RA SA ⊥ AB (góc vuông tại A của tam giác SAB); đề cho thêm SB ⊥ AB (tại B)."""
    kq = A.build_fact_graph(chop(them=[ll("S", "B", "A", "B", "f_sb")]))
    assert (kq.reason_code, kq.rule_id) == (MA, LUAT)
    assert int(_chung_cu(kq)["DERIVED_FACTS_INVOLVED"]) >= 1


def test_A_ca_ba_dinh_deu_vuong_dem_du_ba():
    kq = A.build_fact_graph(chop(them=[ll("B", "A", "B", "C", "f_b"), ll("C", "A", "C", "B", "f_c")]))
    assert kq.reason_code == MA and _chung_cu(kq)["DISTINCT_RIGHT_ANGLE_VERTEX_COUNT"] == "3"


# ══ B — HỢP LỆ: KHÔNG được bác nhầm ═══════════════════════════════════════
def _hop_le(c) -> A.KetQuaAdapter:
    kq = A.build_fact_graph(c)
    assert kq.status == "VALID", (kq.status, kq.reason_code)
    return kq


def test_B_tam_giac_chi_vuong_tai_mot_dinh_va_compile_duoc():
    bd = C.bien_dich(_hop_le(chop()).graph)
    assert bd.status == "COMPILED" and bd.program is not None


def test_B_cung_mot_goc_vuong_khai_lap_va_dao_canh_KHONG_bi_bac():
    _hop_le(chop(them=[ll("A", "B", "A", "C", "f_lap"), ll("C", "A", "B", "A", "f_dao")]))


def test_B_hai_tam_giac_khac_nhau_moi_tam_giac_mot_goc_vuong_KHONG_bi_bac():
    """Đáy ABC vuông tại A; tam giác SAB vuông tại A (đề nói thẳng) — hai tam giác, mỗi cái một đỉnh."""
    _hop_le(chop(them=[ll("S", "A", "A", "B", "f_sab")]))


def test_B_quan_he_cheo_nhau_khong_tao_goc_KHONG_bi_bac():
    """SA ⊥ BC: hai đường không chung điểm — không phải một góc của tam giác nào."""
    _hop_le(chop(them=[ll("S", "A", "B", "C", "f_cheo")]))


def test_B_he_qua_duong_mat_KHONG_tu_mau_thuan():
    g = _hop_le(chop()).graph
    suy = {f.args for f in g.facts if f.kind == "perpendicular_lines" and f.status == "DERIVED"}
    assert {("A", "B", "A", "S"), ("A", "C", "A", "S"), ("A", "S", "B", "C")} <= suy


def test_B_ham_kiem_KHONG_dem_hai_fact_cung_dinh_la_hai_dinh():
    """GIVEN và DERIVED cùng một góc vuông tại cùng đỉnh: một đỉnh, không mâu thuẫn."""
    fs = (FG.Fact("x1", "perpendicular_lines", ("A", "B", "A", "C"), "TRUE", "f1", "GIVEN"),
          FG.Fact("x2", "perpendicular_lines", ("A", "B", "A", "C"), "TRUE", None, "DERIVED",
                  derived_from=("x1",)),
          FG.Fact("x3", "perpendicular_lines", ("A", "C", "A", "B"), "TRUE", "f2", "GIVEN"))
    FG.kiem_mau_thuan(fs)                 # không ném


@pytest.mark.parametrize("nhan,do", [(("S", "A", "B", "C"), ("3", "4", "5")),
                                     (("P", "M", "N", "Q"), ("6", "8", "2")),
                                     (("S", "A", "B", "C"), ("3/2", "5/2", "7/3"))],
                         ids=["R01_SABC", "doi_nhan", "phan_so"])
def test_B_ca_hop_le_van_compile_va_dap_so_dung(nhan, do):
    from fractions import Fraction
    ap, a, b, c = nhan
    bd = C.bien_dich(_hop_le(chop(ap, a, b, c, *do)).graph)
    assert bd.status == "COMPILED"
    from app.simulation.semantic_program import validator as Va
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    mem = SemanticProgramInterpreter().execute(Va.validate_semantic_program(bd.program).spec).final_memory
    mong = Fraction(do[0]) * Fraction(do[1]) / 2 * Fraction(do[2]) / 3
    assert Fraction(str(mem["the_tich"])) == mong


# ══ C — KHÔNG ĐỦ BẰNG CHỨNG: theo chính sách hiện hành, KHÔNG nâng thành GIVEN ═
def test_C_goc_vuong_thu_hai_la_GIA_DINH_thi_khong_tham_gia():
    kq = _hop_le(chop(them=[ll("B", "A", "B", "C", "f_gd", ma=True)]))
    assert "RELATION_NOT_GROUNDED" in kq.diagnostics


def test_C_goc_vuong_thu_hai_KHONG_NGUON_thi_khong_tham_gia():
    kq = _hop_le(chop(them=[ll("B", "A", "B", "C", src=None)]))
    assert "RELATION_NOT_GROUNDED" in kq.diagnostics


def test_C_diem_la_theo_chinh_sach_tham_chieu_khong_phai_mau_thuan():
    kq = A.build_fact_graph(chop(them=[ll("B", "A", "B", "X", "f_la")]))
    assert kq.status == "INVALID_STRUCTURED_RELATION" and kq.reason_code != MA


def test_C_khong_xac_dinh_duoc_dinh_chung_KHONG_bi_bac():
    """AB ⊥ SC: hai đường không chung điểm; không có góc thứ hai nào để mâu thuẫn."""
    _hop_le(chop(them=[ll("A", "B", "S", "C", "f_khong_chung")]))
