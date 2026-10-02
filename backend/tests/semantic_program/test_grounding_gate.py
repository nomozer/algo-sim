# -*- coding: utf-8 -*-
"""P2 (IR → RequestContract) — kiểm THAM CHIẾU, không tìm-theo-giá-trị.

Chuỗi provenance HAI ĐOẠN (spec §3.4):

    Original input --P1--> RequestContract fact --P2--> SemanticProgram reference

P2 kiểm được tất định và mạnh: `source_fact_id` phải tồn tại, kiểu phù hợp, và
giá trị chuẩn hoá phải khớp.

KHÔNG làm kiểu *"tìm xem [4,7,2] có xuất hiện đâu đó trong RequestContract
không"* — đó lại quay về trùng khớp ngẫu nhiên về giá trị.

P1 vẫn hở, và giới hạn đó được KHAI TƯỜNG MINH ở
`docs/evaluation/semantic-benchmark/P1_LIMITATION.md` — Task 7 không mở
source-span, và không được tuyên bố gate này diệt mọi hallucination của analyze.
"""
from app.simulation.semantic_program.contract import (
    AssignStmt,
    LiteralExpr,
    MemoryDeclaration,
    SemanticProgramSpec,
)
from tests.nguon_fixture import check_grounding  # W14 5a: ISOLATED_UNIT_FIXTURE (hợp đồng không đề)
from app.simulation.semantic_program.request_contract import InputFact, RequestContract

_CONTRACT = RequestContract(
    input_facts=(
        InputFact(fact_id="I1", label="dãy đề cho", values=(4, 7, 2)),
        InputFact(fact_id="I2", label="ngưỡng", values=(5,)),
    )
)


def _spec(values, fact_id="I1", name="a", mtype="array") -> SemanticProgramSpec:
    return SemanticProgramSpec(
        title="Kiểm grounding",
        memory_declarations=[
            MemoryDeclaration(
                name=name, type=mtype, element_type="int",
                initial_value=values, source_fact_id=fact_id,
            ),
            MemoryDeclaration(name="m", type="int", initial_value=0),
        ],
        statements=[AssignStmt(target_var="m", expr=LiteralExpr(value=0))],
    )


def test_tham_chieu_dung_muc_va_khop_gia_tri_thi_pass():
    assert check_grounding(_CONTRACT, _spec([4, 7, 2])).ok


def test_them_gia_tri_khong_co_nguon_thi_fail():
    """Đề cho 4,7,2 mà IR khai [4,7,2,9] → 9 không truy được nguồn."""
    res = check_grounding(_CONTRACT, _spec([4, 7, 2, 9]))
    assert not res.ok
    assert res.error_code == "INPUT_NOT_GROUNDED"
    assert any("9" in u for u in res.unresolved)


def test_thieu_source_fact_id_thi_fail():
    res = check_grounding(_CONTRACT, _spec([4, 7, 2], fact_id=None))
    assert not res.ok
    assert any("source_fact_id" in u for u in res.unresolved)


def test_tham_chieu_muc_khong_ton_tai_thi_fail():
    res = check_grounding(_CONTRACT, _spec([4, 7, 2], fact_id="I_ma"))
    assert not res.ok
    assert any("I_ma" in u for u in res.unresolved)


def test_tham_chieu_NHAM_muc_du_gia_tri_co_trong_hop_dong_thi_van_fail():
    """Điểm cốt lõi: kiểm THAM CHIẾU, không phải tìm-theo-giá-trị.

    `5` có thật trong hợp đồng (mục I2), nhưng khai nó dưới `source_fact_id=I1`
    là sai nguồn. Bản tìm-theo-giá-trị sẽ cho qua ca này.
    """
    res = check_grounding(_CONTRACT, _spec([5], fact_id="I1"))
    assert not res.ok
    assert res.error_code == "INPUT_NOT_GROUNDED"


def test_bien_trung_gian_khong_doi_nguon():
    """`m` là biến làm việc, không phải dữ liệu đề cho — không đòi provenance."""
    assert check_grounding(_CONTRACT, _spec([4, 7, 2])).ok


def test_vo_huong_lay_tu_de_cung_phai_ghim_nguon():
    spec = _spec([4, 7, 2])
    spec.memory_declarations.append(
        MemoryDeclaration(name="nguong", type="int", initial_value=5,
                          source_fact_id="I2")
    )
    assert check_grounding(_CONTRACT, spec).ok


def test_vo_huong_bia_ra_thi_fail():
    spec = _spec([4, 7, 2])
    spec.memory_declarations.append(
        MemoryDeclaration(name="nguong", type="int", initial_value=99,
                          source_fact_id="I2")
    )
    res = check_grounding(_CONTRACT, spec)
    assert not res.ok
    assert any("99" in u for u in res.unresolved)


def test_hop_dong_rong_ma_IR_khai_du_lieu_thi_fail():
    """Đề không cho dữ liệu mà chương trình tự dựng [3,7,1] — chặn."""
    res = check_grounding(RequestContract(), _spec([3, 7, 1]))
    assert not res.ok


def test_hat_khoi_tao_khong_doi_provenance():
    """Biến đếm `= 0` là biến LÀM VIỆC, không phải dữ liệu đề cho.

    Bắt nó ghim nguồn thì mọi biến tích luỹ đều phải bịa ra một mục dữ liệu —
    và cổng mất nghĩa vì ai cũng phải nói dối để đi qua.
    """
    spec = _spec([4, 7, 2])
    for ten, gia_tri in [("dem", 0), ("tong", 0.0), ("co", False), ("s", ""),
                         ("ds", [])]:
        spec.memory_declarations.append(
            MemoryDeclaration(name=ten, type="int", initial_value=gia_tri)
        )
    assert check_grounding(_CONTRACT, spec).ok


def test_gia_tri_khong_phai_hat_khoi_tao_thi_van_phai_ghim():
    """Ngưỡng đặt ở 'giá trị quy ước' — `1` không phải hạt khởi tạo."""
    spec = _spec([4, 7, 2])
    spec.memory_declarations.append(
        MemoryDeclaration(name="bat_dau", type="int", initial_value=1)
    )
    res = check_grounding(_CONTRACT, spec)
    assert not res.ok
    assert any("bat_dau" in u for u in res.unresolved)


# ══ w11 — ĐỘ DÀI SERVER NEO TỪ CÂU ĐỀ ══════════════════════════════════════
#
# `bat_bien_do_dai` đọc `SA = 5` từ ĐỀ rồi neo vào mục dữ kiện có nhắc S, A —
# có khi là mục QUAN HỆ không mang số (`SA ⊥ (ABC)`), vì mô hình analyze bỏ
# sót mục độ dài (`test_J_bis…`). Con số vẫn có trong đề; P2 phải nhìn thấy.
def _hop_dong_neo():
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    return RequestContract(
        input_facts=(InputFact(fact_id="f_perp", label="SA vuông góc (ABC)", values=()),),
        source_invariants=(SourceInvariant(
            kind="segment_length", points=("A", "S"), expected="5",
            source_fact_id="f_perp", scale_symbol="", source_text="SA = 5"),),
    )


def _do_dai(name="SA_length", value="5", fact_id="f_perp"):
    return SemanticProgramSpec(
        title="Kiểm độ dài neo từ đề",
        memory_declarations=[
            MemoryDeclaration(name=name, type="float", initial_value=value,
                              source_fact_id=fact_id, provenance="GIVEN"),
            MemoryDeclaration(name="m", type="int", initial_value=0),
        ],
        statements=[AssignStmt(target_var="m", expr=LiteralExpr(value=0))],
    )


def test_do_dai_khop_bat_bien_neo_tu_de_thi_pass():
    assert check_grounding(_hop_dong_neo(), _do_dai()).ok


def test_do_dai_neo_tu_de_sai_gia_tri_sai_doan_sai_muc_van_fail():
    """Kênh mới hẹp: đúng đoạn, đúng số, đúng mục — lệch một thứ là chết."""
    for spec in (_do_dai(value="6"), _do_dai(name="SB_length"),
                 _do_dai(fact_id="f_khac")):
        assert not check_grounding(_hop_dong_neo(), spec).ok
