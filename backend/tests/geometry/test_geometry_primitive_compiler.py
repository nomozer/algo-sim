# -*- coding: utf-8 -*-
"""LÁT CẮT DỌC — FactGraph + primitive compiler, KHÔNG gọi synthesis. 0 mạng.

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20).

Chứng minh: với họ *hình chóp có đáy là tam giác vuông, cạnh bên vuông góc với
đáy, hỏi thể tích*, hệ dựng được chương trình + cảnh + quá trình dựng + đáp số
mà **không** gọi Gemini synthesis.

⚠️ **KHÔNG hard-code**: không `case_id`, không nguyên văn đề, không nhãn
`S/A/B/C`, không số `3/4/5`, không đáp số `10`. Mọi fixture dựng bằng THAM SỐ,
và bộ test chạy lại đúng luật ấy trên nhãn khác và độ dài khác.

Đáp số kỳ vọng chỉ xuất hiện trong ASSERT của test (tính từ chính dữ kiện đầu
vào), không bao giờ trong đầu vào của compiler.
"""
from __future__ import annotations

import json
from fractions import Fraction

import pytest

from app.simulation.geometry_compiler import compiler as C
from app.simulation.geometry_compiler import contract_adapter as A
from app.simulation.geometry_compiler import primitives as P
from app.simulation.geometry_compiler import routing as R
from app.simulation.geometry_compiler.fact_graph import FACT_GRAPH_VERSION
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import InputFact, RequestContract
from app.simulation.semantic_program.scale_normalization import SourceInvariant
from app.simulation.semantic_program.structured_relations import GeometricRelation

BAT = {R.BIEN_MOI_TRUONG: R.CHE_DO_COMPILER}
TAT: dict[str, str] = {}


# ══ FIXTURE — THAM SỐ HOÁ HOÀN TOÀN ════════════════════════════════════════
def hop_dong(dinh_vuong="A", chan_1="B", chan_2="C", dinh_chop="S",
             l1="3", l2="4", cao="5", *, bo_canh=None, bo_cao=False,
             cao_tu=None, them_nghia_vu=None, mau_thuan=False,
             witness="the_tich_khoi"):
    """Dựng `RequestContract` của họ bài — nhãn và độ dài đều là THAM SỐ."""
    bb = []
    if bo_canh != 1:
        bb.append(SourceInvariant(points=(dinh_vuong, chan_1), expected=l1,
                                  source_fact_id="f_canh_1", scale_symbol="",
                                  source_text=""))
    if bo_canh != 2:
        bb.append(SourceInvariant(points=(dinh_vuong, chan_2), expected=l2,
                                  source_fact_id="f_canh_2", scale_symbol="",
                                  source_text=""))
    if not bo_cao:
        # `cao_tu` = đầu mút KIA của đoạn mang độ dài đường cao. Mặc định là
        # đỉnh vuông (đúng họ bài). Đổi sang một chân đáy thì đỉnh chóp VẪN
        # được hợp đồng giới thiệu, nhưng độ dài họ bài CẦN thì thiếu — đó là
        # cách duy nhất phân biệt "hợp đồng THIẾU" với "hợp đồng HỎNG".
        bb.append(SourceInvariant(points=(cao_tu or dinh_vuong, dinh_chop),
                                  expected=cao, source_fact_id="f_cao",
                                  scale_symbol="", source_text=""))
    if mau_thuan:
        bb.append(SourceInvariant(points=(dinh_vuong, chan_1),
                                  expected=str(Fraction(l1) + 1),
                                  source_fact_id="f_canh_1_khac",
                                  scale_symbol="", source_text=""))

    # Quan hệ đi đường CÓ CẤU TRÚC (`FACT_GRAPH_CONTRACT_EXTENSION`). Câu tiếng
    # Việt vẫn ở `InputFact` vì đó là thứ `analyze` vốn khai và người đọc được —
    # nhưng tầng dựng KHÔNG còn đọc nó.
    facts = (
        InputFact(fact_id="f_vuong_day", label="đáy vuông",
                  values=(f"tam giác {dinh_vuong}{chan_1}{chan_2} "
                          f"vuông tại {dinh_vuong}",)),
        InputFact(fact_id="f_vuong_canh_ben", label="cạnh bên vuông góc đáy",
                  values=(f"{dinh_chop}{dinh_vuong} ⊥ "
                          f"({dinh_vuong}{chan_1}{chan_2})",)),
    )
    quan_he = (
        GeometricRelation(kind="perpendicular_lines",
                          line=(dinh_vuong, chan_1),
                          other_line=(dinh_vuong, chan_2),
                          source_fact_id="f_vuong_day"),
        GeometricRelation(kind="perpendicular_line_plane",
                          line=(dinh_chop, dinh_vuong),
                          plane=(dinh_vuong, chan_1, chan_2),
                          source_fact_id="f_vuong_canh_ben"),
    )
    obs = [Obligation(kind="volume", container="khoi_chop",
                      params={"witness": witness})]
    if them_nghia_vu:
        obs.append(them_nghia_vu)
    # `problem_text` có mặt vì cổng grounding hỏi *cái tên này có trong đề
    # không* trước khi nhận `model_assumption`. Câu dưới đây dựng TỪ THAM SỐ —
    # không phải nguyên văn một đề nào, và compiler KHÔNG đọc nó.
    de = (f"Cho hình chóp {dinh_chop}.{dinh_vuong}{chan_1}{chan_2} có đáy "
          f"{dinh_vuong}{chan_1}{chan_2} vuông tại {dinh_vuong}, "
          f"{dinh_vuong}{chan_1} = {l1}, {dinh_vuong}{chan_2} = {l2}, "
          f"{dinh_chop}{dinh_vuong} vuông góc với mặt phẳng đáy và "
          f"{dinh_chop}{dinh_vuong} = {cao}. Tính thể tích khối chóp.")
    return RequestContract(obligations=tuple(obs), input_facts=facts,
                           source_invariants=tuple(bb),
                           geometric_relations=quan_he, problem_text=de)


def _graph(**kw):
    kq = A.build_fact_graph(hop_dong(**kw))
    return kq


def _bien_dich(**kw):
    kq = _graph(**kw)
    assert kq.status == "VALID", kq.reason_code
    return C.bien_dich(kq.graph)


def _the_tich_mong(l1, l2, cao) -> Fraction:
    """Đáp số tính TỪ DỮ KIỆN, không phải hằng số chép tay."""
    return Fraction(l1) * Fraction(l2) / 2 * Fraction(cao) / 3


# ══ A · B · C — FACT GRAPH ═════════════════════════════════════════════════
def test_A_hop_dong_hop_le_tao_duoc_FactGraph_canonical():
    kq = _graph()
    assert kq.status == "VALID"
    g = kq.graph
    assert g.version == FACT_GRAPH_VERSION
    assert {n.kind for n in g.nodes} >= {"point", "segment", "measurement_request"}
    assert len(g.fact_theo_loai("length")) == 3
    # `/2`: quan hệ đi đường CÓ KIỂU. Một fact đề cho (`AB ⟂ AC`) + ba fact suy
    # ra từ quan hệ đường–mặt — `SA` vuông góc với CẢ BA cạnh của `(ABC)`, kể cả
    # `BC` vốn không dính tới đỉnh vuông.
    vg = g.fact_theo_loai("perpendicular_lines")
    assert len([f for f in vg if f.status == "GIVEN"]) == 1
    assert sorted(f.args for f in vg if f.status == "DERIVED") == [
        ("A", "B", "A", "S"), ("A", "C", "A", "S"), ("A", "S", "B", "C")]
    assert len(g.fact_theo_loai("perpendicular_line_plane")) == 1


def test_B_tao_hai_lan_cho_JSON_chinh_tac_TRUNG_BYTE():
    assert _graph().graph.json_chinh_tac() == _graph().graph.json_chinh_tac()


def test_C_dao_thu_tu_facts_KHONG_doi_graph_hash():
    hd = hop_dong()
    dao = hd.model_copy(update={
        "source_invariants": tuple(reversed(hd.source_invariants)),
        "input_facts": tuple(reversed(hd.input_facts))})

    assert A.build_fact_graph(dao).graph.graph_hash() == \
        A.build_fact_graph(hd).graph.graph_hash()


def test_layout_KHONG_BAO_GIO_la_du_kien_de():
    """Toạ độ compiler chọn không được đi vào FactGraph như `GIVEN`.

    ⚠️ `/2` có fact `DERIVED` hợp lệ (`SA ⟂ AB` suy từ `SA ⟂ (ABC)`), nên phép
    kiểm cũ *"mọi fact đều GIVEN"* hết dùng được — và nới nó thành *"có fact
    DERIVED là bình thường"* thì mất luôn điều nó canh. Phát biểu lại đúng thứ
    cần canh: mỗi `DERIVED` phải **nêu được cha**, và không toạ độ nào lọt vào.
    """
    g = _graph().graph
    for f in g.facts:
        if f.status == "DERIVED":
            assert f.derived_from or f.kind == "lies_in_plane", f
        else:
            assert f.status == "GIVEN", f
    assert "0,0,0" not in g.json_chinh_tac().replace(" ", "")


def test_GIVEN_fact_phai_truy_duoc_ve_de():
    """⚠️ Luật này sinh ra vì phép tiêm FK7 ĐI LỌT: ghi toạ độ bố cục vào graph
    dưới nhãn `GIVEN` mà 37/37 vẫn xanh. Nay `dung_graph` chặn, và mọi fact
    `GIVEN` (trừ `requested_operation`) phải có `source_fact_id`."""
    from app.simulation.geometry_compiler.fact_graph import (
        Fact, MauThuanFact, Nut, dung_graph,
    )

    for f in _graph().graph.facts:
        if f.status == "GIVEN" and f.kind != "requested_operation":
            assert f.source_fact_id, f

    with pytest.raises(MauThuanFact) as e:
        dung_graph((Nut("X", "point"),),
                   (Fact("coord_X", "incidence", ("X", "0,0,0"),
                         None, None, "GIVEN"),))
    assert e.value.ma == "GIVEN_FACT_WITHOUT_SOURCE"


def test_compiler_KHONG_tu_khai_mot_fact_GIVEN_nao():
    """Compiler DẪN XUẤT; chỉ adapter mới được báo cáo dữ kiện `GIVEN`.

    ⚠️ Bản trước cấm chuỗi `"GIVEN"` xuất hiện **ở bất kỳ đâu** trong compiler.
    Từ `/2` compiler phải ĐỌC nhãn ấy (nó chỉ nhận quan hệ đề cho, không nhận
    quan hệ suy ra), nên lệnh cấm theo chuỗi sẽ đỏ vì một lý do sai. Phát biểu
    lại đúng điều cần cấm: **so sánh** thì được, **gán** thì không.
    """
    import ast
    import inspect

    cay = ast.parse(inspect.getsource(C))
    duoc_so = {id(x) for n in ast.walk(cay) if isinstance(n, ast.Compare)
               for x in (n.left, *n.comparators)}
    gan = [n for n in ast.walk(cay)
           if isinstance(n, ast.Constant) and n.value == "GIVEN"
           and id(n) not in duoc_so]
    assert gan == [], "compiler GÁN nhãn GIVEN cho thứ nó tự chọn"


# ══ D · E · F — TỔNG QUÁT, KHÔNG HARD-CODE ═════════════════════════════════
def test_D_doi_nhan_diem_van_compile_duoc():
    bd = _bien_dich(dinh_vuong="M", chan_1="N", chan_2="Q", dinh_chop="P")
    assert bd.status == "COMPILED"
    ten = {s["target_var"] for s in bd.program["statements"]}
    assert {"M", "N", "Q", "P"} <= ten
    assert not ({"A", "B", "C", "S"} & ten)


@pytest.mark.parametrize("l1,l2,cao", [("3", "4", "5"), ("6", "7", "2"),
                                       ("5/2", "4", "9"), ("1", "1", "1")])
def test_E_doi_do_dai_thi_dap_so_doi_DUNG_theo_du_kien(l1, l2, cao):
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter

    bd = _bien_dich(l1=l1, l2=l2, cao=cao)
    v = V.validate_semantic_program(bd.program)
    assert v.ok, v.error
    mem = SemanticProgramInterpreter().execute(v.spec).final_memory

    assert Fraction(str(mem["the_tich_khoi"])) == _the_tich_mong(l1, l2, cao)


def test_F_dap_so_KHONG_co_trong_dau_vao_compiler():
    """Compiler suy đáp số, không đọc nó — graph không chứa giá trị ấy."""
    l1, l2, cao = "3", "4", "5"
    g = _graph(l1=l1, l2=l2, cao=cao).graph
    mong = str(_the_tich_mong(l1, l2, cao))

    tho = g.json_chinh_tac()
    assert f'"{mong}"' not in tho, "đáp số kỳ vọng lọt vào đầu vào compiler"


# ══ G → K — ELIGIBILITY ════════════════════════════════════════════════════
@pytest.mark.parametrize("bo", [1, 2])
def test_G_thieu_mot_canh_day__UNSUPPORTED_MISSING_FACT(bo):
    """Hợp đồng ở mức TRẠNG THÁI: thiếu dữ kiện ⇒ `UNSUPPORTED_MISSING_FACT`,
    và tuyệt đối không có chương trình một phần.

    Từ `/2` phép từ chối xảy ra SỚM HƠN một tầng, và mã nói chính xác hơn: nhãn
    điểm chỉ được công nhận khi nó xuất hiện trong một `SourceInvariant`, nên gỡ
    một độ dài cũng gỡ luôn nhãn ấy — hợp đồng thành ra khẳng định một quan hệ
    về một điểm nó **chưa từng giới thiệu**. Đó là hệ quả ĐÚNG của luật *"không
    tự sinh điểm từ một ký hiệu lạ"*, và là một hợp đồng HỎNG, không phải thiếu.
    """
    kq = _graph(bo_canh=bo)
    assert kq.status == "INVALID_STRUCTURED_RELATION"
    assert kq.reason_code == "STRUCTURED_RELATION_REFERENCE_UNKNOWN"
    assert kq.graph is None, "KHÔNG được trả graph một phần"


def test_H_thieu_chieu_cao__tu_choi_co_ten():
    kq = _graph(bo_cao=True)
    assert kq.status == "INVALID_STRUCTURED_RELATION"
    assert kq.reason_code == "STRUCTURED_RELATION_REFERENCE_UNKNOWN"
    assert kq.graph is None


def test_H2_diem_CO_gioi_thieu_ma_thieu_DO_DAI__UNSUPPORTED_MISSING_FACT():
    """Phân biệt hợp đồng THIẾU với hợp đồng HỎNG — hai mã, hai lời đáp.

    Đỉnh chóp vẫn được giới thiệu (qua độ dài `B–S`), nhưng độ dài `A–S` mà họ
    bài cần thì không có. Không có ca này thì `REQUIRED_LENGTH_MISSING` là một
    nhánh chưa ai chứng minh là tới được.
    """
    kq = _graph(cao_tu="B")
    assert kq.status == "VALID", kq.reason_code
    el = C.danh_gia_eligibility(kq.graph)
    assert el.status == "UNSUPPORTED_MISSING_FACT"
    assert el.reason_code == "REQUIRED_LENGTH_MISSING"
    assert "cao" in el.diagnostics
    assert C.bien_dich(kq.graph).program is None


def test_I_du_kien_do_dai_MAU_THUAN__INVALID_CONFLICT():
    kq = _graph(mau_thuan=True)
    assert (kq.status, kq.reason_code) == ("INVALID_CONFLICT", "INVALID_CONFLICT")
    assert kq.graph is None, "KHÔNG được trả graph một phần khi mâu thuẫn"


@pytest.mark.parametrize("cao", ["0", "-2"])
def test_J_do_dai_khong_duong__INVALID_NON_POSITIVE_LENGTH(cao):
    el = C.danh_gia_eligibility(_graph(cao=cao).graph)
    assert el.status == "INVALID_NON_POSITIVE_LENGTH"


def test_K_guard_SUPPORTED_khong_duoc_bo__du_co_binding(monkeypatch):
    """⚠️ Test này sinh ra vì phép tiêm FK8 ĐI LỌT.

    Gỡ điều kiện `status != SUPPORTED` khỏi `bien_dich` mà 39/39 vẫn xanh, vì
    `danh_gia_eligibility` hiện chỉ trả `binding` khi SUPPORTED — guard đang
    ĐÚNG nhưng THỪA, nên không test nào chứng minh nó. Nếu một ngày eligibility
    trả kèm binding cho một trạng thái không hỗ trợ, chương trình một phần sẽ
    lọt ra mà không ai biết. Ở đây guard được gọi thẳng.
    """
    that = C.danh_gia_eligibility
    g = _graph().graph

    def gia(graph):
        ok = that(graph)
        return C.KetQuaEligibility("UNSUPPORTED_EXTRA_OBLIGATION", ok.binding,
                                   "EXTRA_OBLIGATION")

    monkeypatch.setattr(C, "danh_gia_eligibility", gia)
    bd = C.bien_dich(g)

    assert bd.status == "NOT_ELIGIBLE"
    assert bd.program is None, "chương trình một phần lọt ra cho ca KHÔNG hỗ trợ"


def test_K_nghia_vu_thiet_dien_bo_sung__UNSUPPORTED_EXTRA_OBLIGATION():
    them = Obligation(kind="section_matches", container="T",
                      params={"witness": None})
    bd = _bien_dich(them_nghia_vu=them)
    assert bd.status == "NOT_ELIGIBLE"
    assert bd.reason_code == "EXTRA_OBLIGATION"
    assert bd.program is None, "UNSUPPORTED không được sinh chương trình một phần"


# ══ L · M — KHÔNG PHỤ THUỘC CA CỤ THỂ ══════════════════════════════════════
def test_L_compiler_KHONG_doc_case_id_hay_nguyen_van_de():
    """Quét AST, không quét văn bản: chỉ tính LỜI GỌI và TRUY CẬP THUỘC TÍNH
    thật, nên một chữ `problem_text` trong docstring không làm test đỏ (và cũng
    không che được một lượt đọc thật)."""
    import ast
    import inspect

    for mod in (C, A, P, R):
        cay = ast.parse(inspect.getsource(mod))
        thuoc_tinh = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
        chuoi_getattr = {n.args[1].value for n in ast.walk(cay)
                         if isinstance(n, ast.Call)
                         and getattr(n.func, "id", None) == "getattr"
                         and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant)}
        doc = thuoc_tinh | chuoi_getattr
        assert "case_id" not in doc, f"{mod.__name__} đọc case_id"
        assert "problem_text" not in doc, f"{mod.__name__} đọc problem_text"


def test_M_registry_khong_co_primitive_rieng_cho_mot_bai():
    ten = set(P.REGISTRY)
    for cam in ("C01", "B01", "SABC", "3_4_5", "solve_", "answer_10"):
        assert not any(cam.lower() in t.lower() for t in ten), cam
    assert P.danh_tinh_registry()["version"] == P.PRIMITIVE_REGISTRY_VERSION


# ══ N → Q — QUA ĐÚNG VALIDATOR HIỆN CÓ ═════════════════════════════════════
def test_N_chuong_trinh_qua_Pydantic_va_toan_bo_validator():
    v = V.validate_semantic_program(_bien_dich().program)
    assert v.ok, v.error


def test_O_memory_declarations_KHONG_co_khoa_at():
    """`at` là khoá của `declare_point`. Đặt nó vào khai báo là lỗi lược đồ đã
    đo được (`SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT`).

    `model_assumption` thì HỢP LỆ và cần thiết: toạ độ do bố cục chọn phải đi
    qua kênh ấy chứ không qua `source_fact_id` (xem cổng grounding)."""
    cho_phep = {"name", "type", "model_assumption", "source_fact_id"}
    for m in _bien_dich().program["memory_declarations"]:
        assert "at" not in m, m
        assert set(m) <= cho_phep, m


def test_P_Q_khong_khoa_la_va_ignored_keys_rong():
    v = V.validate_semantic_program(_bien_dich().program)
    assert v.ok
    assert list(getattr(v, "ignored_keys", []) or []) == []


# ══ R → Y — CẢNH, HÌNH HỌC, ĐÁP SỐ ═════════════════════════════════════════
@pytest.fixture(scope="module")
def dung():
    from app.ai.pipeline import _dung_scene3d
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter

    bd = C.bien_dich(A.build_fact_graph(hop_dong()).graph)
    v = V.validate_semantic_program(bd.program)
    assert v.ok, v.error
    mem = SemanticProgramInterpreter().execute(v.spec).final_memory
    return bd, v.spec, mem, _dung_scene3d(v.spec, hop_dong())


def test_R_S_scene_khong_rong_va_co_dung_bon_diem(dung):
    _, _, _, canh = dung
    assert canh and canh["objects"]
    assert len([o for o in canh["objects"] if o["type"] == "point3"]) == 4


def test_T_khoi_chop_co_topology_dung(dung):
    _, _, _, canh = dung
    khoi = next(o for o in canh["objects"] if o["type"] == "solid")
    assert len(khoi["vertices"]) == 4
    assert len(khoi["faces"]) == 4, "chóp tam giác có đúng bốn mặt"


def test_U_binh_phuong_do_dai_dung_theo_input(dung):
    from app.simulation.geometry.exact import Vec3

    _, _, mem, _ = dung
    d = {k: mem[k] for k in ("A", "B", "C", "S")}
    def d2(x, y):
        u = d[x] - d[y]
        return u.dot(u)
    assert d2("A", "B") == Fraction(3) ** 2
    assert d2("A", "C") == Fraction(4) ** 2
    assert d2("A", "S") == Fraction(5) ** 2


def test_V_hai_canh_day_VUONG_GOC(dung):
    _, _, mem, _ = dung
    assert (mem["B"] - mem["A"]).dot(mem["C"] - mem["A"]) == 0


def test_W_duong_cao_vuong_goc_hai_phuong_doc_lap_cua_day(dung):
    _, _, mem, _ = dung
    h = mem["S"] - mem["A"]
    assert h.dot(mem["B"] - mem["A"]) == 0
    assert h.dot(mem["C"] - mem["A"]) == 0


def test_X_ba_diem_day_KHONG_thang_hang(dung):
    from app.simulation.geometry.predicates import collinear

    _, _, mem, _ = dung
    assert not collinear(mem["A"], mem["B"], mem["C"])


def test_Y_final_memory_co_the_tich_dung(dung):
    _, _, mem, _ = dung
    assert Fraction(str(mem["the_tich_khoi"])) == _the_tich_mong("3", "4", "5")


# ══ Z — QUÁ TRÌNH DỰNG ═════════════════════════════════════════════════════
def test_Z_construction_trace_du_buoc_va_co_provenance():
    bd = _bien_dich()
    assert len(bd.construction_steps) >= 10, "thiếu bước dựng"
    assert [b.index for b in bd.construction_steps] == \
        list(range(1, len(bd.construction_steps) + 1))
    assert all(b.primitive_id in P.REGISTRY for b in bd.construction_steps)
    co_nguon = [b for b in bd.construction_steps if b.source_fact_ids]
    assert len(co_nguon) >= 3, "bước dựng mất liên kết về dữ kiện đề"
    assert any(b.scene_object_ids for b in bd.construction_steps)


# ══ AA → AD — ĐỊNH TUYẾN ═══════════════════════════════════════════════════
def test_AA_feature_OFF_giu_nguyen_hanh_vi_START_HEAD():
    q = R.quyet_dinh_dinh_tuyen(hop_dong(), env=TAT)
    assert q.decision == "DISABLED"
    assert q.program is None and q.compile_result is None


def test_AB_feature_ON_supported_thi_KHONG_goi_synthesis(monkeypatch):
    from app.ai import pipeline as PL

    dem = {"n": 0}

    async def chan(*a, **k):
        dem["n"] += 1
        raise AssertionError("compiler KHÔNG được gọi transport synthesis")

    monkeypatch.setattr(PL, "call_gemini", chan)
    q = R.quyet_dinh_dinh_tuyen(hop_dong(), env=BAT)

    assert q.decision == "USE_COMPILER" and q.program is not None
    assert dem["n"] == 0


def test_AC_feature_ON_invalid_thi_TU_CHOI_va_0_request(monkeypatch):
    from app.ai import pipeline as PL

    dem = {"n": 0}

    async def chan(*a, **k):
        dem["n"] += 1
        raise AssertionError("không được gọi provider khi dữ kiện mâu thuẫn")

    monkeypatch.setattr(PL, "call_gemini", chan)
    q = R.quyet_dinh_dinh_tuyen(hop_dong(mau_thuan=True), env=BAT)

    assert q.decision == "REFUSE" and q.program is None
    assert dem["n"] == 0


def test_AD_unsupported_tra_fallback_cho_caller_chu_khong_tu_gui():
    them = Obligation(kind="distance", container="BD",
                      params={"witness": "d", "wrt": "S"})
    q = R.quyet_dinh_dinh_tuyen(hop_dong(them_nghia_vu=them), env=BAT)

    assert q.decision == "FALLBACK_TO_LLM"
    assert q.program is None


# ══ AE · AF — TELEMETRY VÀ BIÊN TÍCH HỢP ═══════════════════════════════════
def _moi_chuoi(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _moi_chuoi(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _moi_chuoi(v)


def test_AE_telemetry_KHONG_luu_raw_prompt_contract_hay_program():
    bd = _bien_dich()
    tele = {
        "status": bd.status, "reason_code": bd.reason_code,
        "diagnostics": list(bd.diagnostics),
        "primitive_calls": [{"primitive_id": g.primitive_id,
                             "arg_count": g.arg_count} for g in bd.primitive_calls],
        "compiler_version": bd.compiler_version,
    }
    chuoi = set(_moi_chuoi(tele))
    for cam in ("statements", "memory_declarations", "problem_text", "at",
                "title", "vertices", "faces"):
        assert cam not in chuoi, f"telemetry rò rỉ khoá: {cam}"
    assert "3" not in chuoi and "10" not in chuoi


def test_AF_di_qua_BIEN_TICH_HOP_that_route_va_visual_gate():
    """Không chỉ gọi từng hàm: chương trình phải qua `verify_and_compile` +
    cổng trực quan, đúng đường một chương trình do mô hình viết phải đi."""
    from app.ai.pipeline import _dung_scene3d
    from app.simulation.semantic_program import visual_obligations as VO
    from app.simulation.semantic_program.route import verify_and_compile

    hd = hop_dong()
    bd = C.bien_dich(A.build_fact_graph(hd).graph)
    v = V.validate_semantic_program(bd.program)
    assert v.ok, v.error

    o = verify_and_compile(hd, v.spec)
    assert o.stage_reached == "served", (o.stage_reached, o.error_code, o.details)
    assert o.servable is True

    canh = _dung_scene3d(v.spec, hd)
    assert VO.check_visual_obligations(hd, canh, o.resolved_names).verdict == "COVERED"


def test_AF_deterministic__hai_lan_bien_dich_trung_byte():
    a = json.dumps(_bien_dich().program, sort_keys=True, ensure_ascii=False)
    b = json.dumps(_bien_dich().program, sort_keys=True, ensure_ascii=False)
    assert a == b
