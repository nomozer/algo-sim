# -*- coding: utf-8 -*-
"""`predicate_verdict` — nghĩa vụ PHÁN QUYẾT, và bộ kiểm độc lập của nó.

VÌ SAO KIND NÀY ĐƯỢC MỞ (2026-08-23, nguồn DEV): ma trận xuyên miền cho thấy bài
"chuỗi ngoặc hợp lệ" không có kind nào diễn đạt được — `membership` hỏi *phần tử
có thuộc container không*, còn bài này hỏi *toàn bộ dữ liệu có thoả một tính chất
không*. Hệ quả đo được: `executable=True` mà không bao giờ `servable`, cho cả
một lớp bài.

ĐIỀU BỘ TEST NÀY PHẢI CHỨNG MINH, và là điều kiện để việc mở kind không trở
thành hạ chuẩn: **checker KHÔNG được tin witness**. Nó tính lại phán quyết từ dữ
liệu đề, rồi mới đem so. Nửa "test âm" dưới đây chính là chỗ đó được chứng minh
— nếu chương trình khai sai, C₂ phải bắt.
"""
import pytest

from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import OBLIGATION_KINDS, Obligation
from app.simulation.semantic_program.postconditions import (
    PREDICATE_CHECKERS,
    check_postconditions,
)
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

from .fixtures_coverage_18 import P01_STACK_BRACKET

CHUOI = ["{", "[", "(", ")", "]", "}"]


# ── §3 — bộ kiểm vị từ: bảng chân trị ─────────────────────────────────────


@pytest.mark.parametrize(
    "vao,mong",
    [
        ("{[()]}", True),
        ("([)]", False),      # lồng SAI thứ tự — cân về số lượng vẫn phải FALSE
        ("", True),           # chuỗi rỗng cân bằng theo định nghĩa
        ("((", False),        # thừa mở
        ("}{", False),        # đóng trước mở
        ("()[]{}", True),     # nối tiếp, không lồng
        ("(a+b)*[c]", True),  # ký tự không phải ngoặc bị bỏ qua
        (list("{[()]}"), True),   # nhận cả dãy ký tự, không chỉ chuỗi
        (list("([)]"), False),
    ],
)
def test_bang_chan_tri_cua_balanced_delimiters(vao, mong):
    assert PREDICATE_CHECKERS["balanced_delimiters"](vao) is mong


def test_checker_KHONG_doc_ket_qua_cua_chuong_trinh():
    """Bộ kiểm nhận ĐÚNG dữ liệu vào, không nhận witness, không nhận bộ nhớ.

    Chữ ký một tham số là ràng buộc kiến trúc chứ không phải tiện tay: nó khiến
    "dùng đáp án của LLM làm oracle" trở thành bất khả, không phải bị cấm bằng
    lời dặn.
    """
    import inspect

    fn = PREDICATE_CHECKERS["balanced_delimiters"]
    assert list(inspect.signature(fn).parameters) == ["chuoi"]


def test_bang_cap_ngoac_KHONG_lay_tu_chuong_trinh():
    """Chương trình tự khai bảng ghép thì checker mất tính độc lập ngay tại đó."""
    from app.simulation.semantic_program import postconditions as pc

    assert pc._CAP_NGOAC == {")": "(", "]": "[", "}": "{"}


# ── §4 — TEST ÂM: chương trình khai sai thì C₂ phải bắt ───────────────────


def _spec_voi_ket_qua(chuoi: list[str], ket_qua):
    """P01 nhưng ép `bracket_strip` và `result` — để dựng ca khai SAI."""
    d = []
    for x in P01_STACK_BRACKET.memory_declarations:
        if x.name == "bracket_strip":
            x = x.model_copy(update={"initial_value": chuoi, "source_fact_id": "I1"})
        elif x.name == "result":
            x = x.model_copy(update={"initial_value": ket_qua})
        elif x.name == "pairs":
            x = x.model_copy(update={"source_fact_id": "I2"})
        d.append(x)
    return P01_STACK_BRACKET.model_copy(update={"memory_declarations": d})


def _hop_dong(witness="result", pred="balanced_delimiters", container="bracket_strip"):
    return RequestContract(
        obligations=(
            Obligation(kind="predicate_verdict", container=container,
                       params={"witness": witness, "pred": pred}),
        )
    )


def _chay(spec):
    return SemanticProgramInterpreter(max_steps=300).execute(spec)


def _spec_noi_doi(chuoi: list[str], khai):
    """Chương trình KHÔNG làm việc, chỉ khai một phán quyết.

    VÌ SAO PHẢI DỰNG SPEC RIÊNG thay vì ép `initial_value` của P01: P01 TỰ TÍNH
    ra kết quả và ghi đè giá trị khởi tạo, nên ép nó không tạo ra được một
    chương trình nói dối — C₂ pass, và pass ĐÚNG. Muốn kiểm "checker có tin
    witness không" thì phải có một chương trình mà witness KHÔNG đến từ phép
    tính nào cả. Đây chính là hình dạng mà một LLM đoán bừa đáp án sẽ sinh ra.
    """
    from app.simulation.semantic_program.contract import (
        AssignStmt,
        LiteralExpr,
        MemoryDeclaration,
        SemanticProgramSpec,
        VisualBindings,
        VisualContainerBinding,
        VisualValueBoxBinding,
    )

    return SemanticProgramSpec(
        title="Khai phán quyết mà không làm việc",
        memory_declarations=[
            MemoryDeclaration(name="bracket_strip", type="array", element_type="str",
                              initial_value=chuoi, source_fact_id="I1"),
            MemoryDeclaration(name="result", type="str", initial_value=""),
        ],
        statements=[AssignStmt(target_var="result", expr=LiteralExpr(value=khai))],
        visual_bindings=VisualBindings(
            containers=[VisualContainerBinding(semantic_id="bracket_strip",
                                               primitive="array_strip", label="Chuỗi")],
            pointers=[],
            value_boxes=[VisualValueBoxBinding(box_id="r", var_ref="result",
                                               label="Kết quả")],
        ),
    )


def test_khai_TRUE_cho_chuoi_SAI_thi_C2_bat():
    """`([)]` không hợp lệ. Chương trình khai "HỢP LỆ" ⇒ vi phạm."""
    spec = _spec_noi_doi(list("([)]"), "HỢP LỆ")
    kq = check_postconditions(_hop_dong(), spec, _chay(spec))
    assert not kq.ok
    assert kq.violations, "phải KẾT TỘI, không phải mức yếu"
    assert "balanced_delimiters" in kq.violations[0]


def test_khai_FALSE_cho_chuoi_DUNG_thi_C2_bat():
    """`{[()]}` hợp lệ. Chương trình khai "KHÔNG HỢP LỆ" ⇒ vi phạm."""
    spec = _spec_noi_doi(CHUOI, "KHÔNG HỢP LỆ")
    kq = check_postconditions(_hop_dong(), spec, _chay(spec))
    assert not kq.ok and kq.violations


def test_chuong_trinh_TU_TINH_dung_thi_KHONG_bi_ket_toi():
    """Đối chứng: P01 chạy trên `([)]` tự ra "KHÔNG HỢP LỆ" ⇒ C₂ phải PASS.

    Không có vế này thì hai test trên có thể xanh vì checker khắt khe bừa, chứ
    không phải vì nó bắt đúng lời khai sai.
    """
    spec = _spec_voi_ket_qua(list("([)]"), "HỢP LỆ")  # giá trị khởi tạo bị ghi đè
    res = _chay(spec)
    assert res.final_memory["result"] == "KHÔNG HỢP LỆ"
    assert check_postconditions(_hop_dong(), spec, res).ok


def test_witness_khong_duoc_ghi_thi_FAIL():
    spec = _spec_voi_ket_qua(CHUOI, "HỢP LỆ")
    kq = check_postconditions(_hop_dong(witness="khong_ton_tai"), spec, _chay(spec))
    assert not kq.ok and kq.violations


def test_witness_sai_KIEU_thi_FAIL():
    """Phán quyết phải ĐỌC ĐƯỢC. Một con số không phải câu trả lời đúng/sai."""
    spec = _spec_voi_ket_qua(CHUOI, "HỢP LỆ")
    kq = check_postconditions(_hop_dong(witness="stack"), spec, _chay(spec))
    assert not kq.ok and kq.violations


def test_vi_tu_KHONG_co_bo_kiem_thi_YEU_chu_khong_ket_toi():
    """§2 — `executable` có thể true, `servable` phải false, KHÔNG kết tội."""
    spec = _spec_voi_ket_qua(CHUOI, "HỢP LỆ")
    kq = check_postconditions(_hop_dong(pred="vi_tu_chua_ai_kiem"), spec, _chay(spec))
    assert not kq.ok
    assert kq.violations == []
    assert kq.weak_kinds == ["predicate_verdict"]


@pytest.mark.parametrize("nhan,mong_vi_pham", [
    ("HỢP LỆ", False), ("Hợp lệ", False), ("true", False), ("Đúng", False),
    ("KHÔNG HỢP LỆ", True), ("false", True), ("Sai", True),
])
def test_nhan_tieng_VIET_van_doc_duoc_thanh_phan_quyet(nhan, mong_vi_pham):
    """Bề mặt học sinh nói tiếng Việt, nên `result = "HỢP LỆ"` là hợp lý.

    Ép witness phải là `bool` thuần sẽ từ chối oan mọi chương trình viết đúng
    theo tinh thần của hệ — và đẩy LLM sang đặt tên biến kiểu máy.
    """
    spec = _spec_voi_ket_qua(CHUOI, nhan)
    kq = check_postconditions(_hop_dong(), spec, _chay(spec))
    assert bool(kq.violations) is mong_vi_pham, kq.violations


# ── §5 — bài ngoặc đi trọn đường và ĐƯỢC PHÁT ─────────────────────────────


def _payload(pred="balanced_delimiters"):
    return {
        "input_facts": [
            {"id": "I1", "kind": "array", "label": "chuỗi ngoặc", "value": CHUOI},
            {"id": "I2", "kind": "map", "label": "cặp ngoặc",
             "value": ["(", ")", "[", "]", "{", "}"]},
        ],
        "obligations": [{"kind": "predicate_verdict", "container": "bracket_strip",
                         "witness": "result", "pred": pred}],
    }


def test_bai_ngoac_SERVABLE_va_trace_co_dien_tien_that():
    kq = verify_and_compile(build_request_contract(_payload()), _spec_voi_ket_qua(CHUOI, "HỢP LỆ"))

    assert kq.stage_reached == "served"
    assert kq.executable is True and kq.servable is True, kq.reason
    assert kq.final_memory["result"] == "HỢP LỆ"

    # Ngăn xếp phải ĐỔI THẬT — triệu chứng gốc của cả wave là hình đứng yên.
    day, truoc = [], None
    for f in kq.envelope["config"]["frames"]:
        o = next(x for x in f["objects"] if x["id"] == "stack")
        cur = tuple(o.get("items") or ())
        if cur != truoc:
            day.append(cur)
            truoc = cur
    assert day == [(), ("{",), ("{", "["), ("{", "[", "("), ("{", "["), ("{",), ()]


def test_vi_tu_la_thi_CHAY_DUOC_nhung_KHONG_duoc_phat():
    """§2 — không hạ assurance để một bài được serve."""
    kq = verify_and_compile(
        build_request_contract(_payload(pred="vi_tu_la")), _spec_voi_ket_qua(CHUOI, "HỢP LỆ")
    )
    assert kq.executable is True
    assert kq.servable is False
    assert kq.failure_category == "verification_gap"


def test_witness_khong_hien_thi_thi_learner_surface_chan():
    """Phán quyết phải NHÌN THẤY ĐƯỢC, không chỉ tính ra được."""
    spec = _spec_voi_ket_qua(CHUOI, "HỢP LỆ")
    vb = spec.visual_bindings
    khong_hien = spec.model_copy(
        update={"visual_bindings": vb.model_copy(update={"value_boxes": []})}
    )
    kq = verify_and_compile(build_request_contract(_payload()), khong_hien)
    assert kq.executable is True and kq.servable is False
    assert kq.error_code == "learner_surface_incomplete"
    assert any("result" in d for d in kq.details), kq.details


# ── §6 — KHÔNG có module mô phỏng chuyên biệt nào được thêm ───────────────


def test_khong_co_module_mo_phong_rieng_cho_bai_ngoac():
    """Checker là bộ KIỂM, không phải một mô phỏng dựng sẵn.

    Mô phỏng vẫn phải do `generic.semantic_program` sinh từ IR của LLM. Nếu ở
    đâu đó xuất hiện một template khung/lời kể cho riêng bài ngoặc thì luận điểm
    R0 của đề tài sụp: hệ không còn *sinh* mô phỏng, nó *tra* mô phỏng.
    """
    import pathlib

    goc = pathlib.Path(__file__).resolve().parents[3]
    cam = ["StackBracketSimulation", "BracketTemplate", "bracket_template",
           "BRACKET_FRAMES", "stack_bracket_frames"]
    pham = []
    for p in list((goc / "backend" / "app").rglob("*.py")) + list(
        (goc / "frontend" / "src").rglob("*.ts*")
    ):
        noi = p.read_text(encoding="utf-8", errors="ignore")
        for c in cam:
            if c in noi:
                pham.append(f"{p.name}: {c}")
    assert pham == [], pham


def test_kind_da_vao_taxonomy_va_co_mien_kieu():
    assert "predicate_verdict" in OBLIGATION_KINDS
    assert "array" in OBLIGATION_KINDS["predicate_verdict"]
