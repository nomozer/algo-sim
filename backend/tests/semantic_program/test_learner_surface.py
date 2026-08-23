# -*- coding: utf-8 -*-
"""CỔNG BỀ MẶT HỌC SINH — chạy được ≠ xem được.

Cổng này ra đời từ một sự cố ĐÃ CHỤP ĐƯỢC MÀN HÌNH: chương trình chạy đúng, lời
kể đúng, envelope biên dịch sạch, mọi cổng xanh — và ngăn xếp trên hình rỗng
suốt bảy bước.

Hai nửa của bộ test này quan trọng như nhau:
  - nửa TIÊM LỖI chứng minh cổng ĐỎ ĐƯỢC (`ARCHITECTURE_MAP §8` #14);
  - nửa KHÔNG-KÊU-OAN chứng minh nó không chặn mô phỏng đúng. Một cổng kêu oan
    là một cổng sẽ bị tắt, và khi ấy nó tệ hơn là không có.
"""
import pytest

from app.simulation.error_codes import SEMANTIC_FAILURE_CATEGORY, ErrorCode
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.learner_surface import check_learner_surface
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)

from .fixtures_coverage_18 import P01_STACK_BRACKET, P02_FIND_MAX


def _chay(spec):
    return SemanticProgramInterpreter().execute(spec)


def _envelope(spec):
    return compile_semantic_program_to_envelope(spec)


#: Ghim `source_fact_id` như đường sản phẩm đòi. Fixture `P01` viết tay từ trước
#: khi P2 tồn tại nên để trống hết — dùng nguyên bản thì mọi test tích hợp chết ở
#: `grounding` chứ không bao giờ chạm tới cổng đang cần kiểm.
_GHIM = {"bracket_strip": "I1", "pairs": "I2"}


def _spec_co_provenance(spec=P01_STACK_BRACKET):
    decls = [
        d.model_copy(update={"source_fact_id": _GHIM[d.name]}) if d.name in _GHIM else d
        for d in spec.memory_declarations
    ]
    return spec.model_copy(update={"memory_declarations": decls})


def _contract(witness: str = "result") -> RequestContract:
    return RequestContract(
        obligations=(
            Obligation(
                kind="membership",
                container="bracket_strip",
                params={"witness": witness},
            ),
        ),
        input_facts=(
            InputFact(
                fact_id="I1",
                label="chuỗi ngoặc",
                values=("{[()]}", "{", "[", "(", ")", "]", "}"),
            ),
            InputFact(
                fact_id="I2",
                label="cặp ngoặc tương ứng",
                values=("(", ")", "[", "]", "{", "}"),
            ),
        ),
    )


def _bo_binding_container(spec, ten: str):
    """Gỡ ĐÚNG một container khỏi hợp đồng thị giác, giữ nguyên chương trình."""
    vb = spec.visual_bindings
    moi = vb.model_copy(
        update={"containers": [c for c in (vb.containers or []) if c.semantic_id != ten]}
    )
    return spec.model_copy(update={"visual_bindings": moi})


# ── Nửa 1: KHÔNG kêu oan ────────────────────────────────────────────────────


def test_chuong_trinh_dung_thi_di_qua():
    spec = P01_STACK_BRACKET
    kq = check_learner_surface(_contract(), spec, _chay(spec), _envelope(spec))
    assert kq.ok, kq.invisible


def test_bang_tra_HANG_khong_bi_doi_phai_co_hinh():
    """`pairs` là bảng ghép ngoặc — hằng, không đổi suốt lượt chạy.

    Đòi nó phải hiện là đòi vẽ mọi thứ, và đó là cách một cổng trở nên vô dụng.
    Luật chỉ chạm container BIẾN ĐỘNG.
    """
    spec = P01_STACK_BRACKET
    assert "pairs" in {d.name for d in spec.memory_declarations}
    assert not any(
        c.semantic_id == "pairs" for c in (spec.visual_bindings.containers or [])
    )
    assert check_learner_surface(_contract(), spec, _chay(spec), _envelope(spec)).ok


# ── Nửa 2: TIÊM LỖI — cổng phải ĐỎ ─────────────────────────────────────────


def test_container_bien_dong_khong_co_binding_thi_DO():
    """Đúng sự cố gốc: ngăn xếp đổi suốt lượt chạy mà không có đường lên hình."""
    spec = _bo_binding_container(P01_STACK_BRACKET, "stack")
    kq = check_learner_surface(_contract(), spec, _chay(spec), _envelope(spec))
    assert not kq.ok
    assert kq.error_code == "LEARNER_SURFACE_INCOMPLETE"
    assert any("'stack'" in u for u in kq.invisible), kq.invisible


def test_witness_khong_hien_thi_DO():
    """Chạy xong mà học sinh không thấy đáp án ở đâu."""
    spec = P01_STACK_BRACKET
    kq = check_learner_surface(
        _contract(witness="khong_bao_gio_hien"), spec, _chay(spec), _envelope(spec)
    )
    assert not kq.ok
    assert any("khong_bao_gio_hien" in u for u in kq.invisible), kq.invisible


def test_chuoi_ky_thuat_ro_len_be_mat_thi_DO():
    spec = P01_STACK_BRACKET
    env = _envelope(spec)
    env["config"]["frames"][0]["objects"][0]["items"] = ["undefined"]
    kq = check_learner_surface(_contract(), spec, _chay(spec), env)
    assert not kq.ok
    assert any("undefined" in u for u in kq.invisible), kq.invisible


def test_khong_co_khung_nao_thi_DO():
    spec = P01_STACK_BRACKET
    env = _envelope(spec)
    env["config"]["frames"] = []
    kq = check_learner_surface(_contract(), spec, _chay(spec), env)
    assert not kq.ok


# ── Nửa 3: nối vào quyết định `servable` thật ──────────────────────────────
#
# Dùng CẶP ĐÃ BIẾT LÀ ĐI LỌT của `test_route_wiring.py` (P02 + nghĩa vụ
# `extremum`), không dựng cặp mới: mọi cổng phía trước phải xanh thì mới chạm
# được tới cổng đang cần kiểm, và tự chế một cặp khác chỉ tốn thì giờ dò C₁/C₂.

_PAYLOAD_P02 = {
    "input_facts": [
        {"id": "day_so", "kind": "array", "label": "dãy số đề cho",
         "value": [str(v) for v in [12, 45, 67, 23, 89, 34]]},
    ],
    "obligations": [
        {"kind": "extremum", "container": "arr", "witness": "max_val", "cmp": "max"},
    ],
}


def _p02():
    from app.simulation.semantic_program.analyze_contract import build_request_contract

    spec = P02_FIND_MAX.model_copy(deep=True)
    spec.memory_declarations[0] = spec.memory_declarations[0].model_copy(
        update={"source_fact_id": "day_so"}
    )
    return build_request_contract(_PAYLOAD_P02), spec


def _bo_value_box(spec, box_id: str):
    vb = spec.visual_bindings
    return spec.model_copy(
        update={
            "visual_bindings": vb.model_copy(
                update={
                    "value_boxes": [b for b in (vb.value_boxes or []) if b.box_id != box_id]
                }
            )
        }
    )


def test_route_van_serve_khi_be_mat_du():
    from app.simulation.semantic_program.route import verify_and_compile

    contract, spec = _p02()
    kq = verify_and_compile(contract, spec)
    assert kq.servable is True, kq.reason
    assert kq.stage_reached == "served"


def test_route_ha_servable_va_giu_executable():
    """Cổng phải đổi ĐƯỢC phán quyết, không chỉ trả về một object.

    Gỡ ô hiển thị `max_val`: chương trình vẫn TÍNH ra đáp án (C₁/C₂ vẫn xanh, vì
    biến vẫn tồn tại và vẫn được sinh ra) — chỉ là học sinh không bao giờ thấy
    nó. Đó đúng là lớp lỗi mà mọi cổng phía trước bỏ lọt theo thiết kế: chúng
    nhìn về phía chương trình, không nhìn về phía màn hình.

    Và cổng phải hạ ĐÚNG VẾ: `executable=True` giữ nguyên vì hệ thực thi được
    bài này. Xếp sang `capability_gap` là tự khai năng lực thấp hơn thực tế —
    đúng ranh giới nơi hai tỉ lệ của luận văn tách nhau.
    """
    from app.simulation.semantic_program.route import verify_and_compile

    contract, spec = _p02()
    kq = verify_and_compile(contract, _bo_value_box(spec, "max_box"))

    assert kq.executable is True
    assert kq.servable is False
    assert kq.error_code == ErrorCode.LEARNER_SURFACE_INCOMPLETE.value
    assert kq.failure_category == "verification_gap"
    assert kq.stage_reached == "learner_surface"
    assert any("max_val" in d for d in kq.details), kq.details


@pytest.mark.parametrize("code", [ErrorCode.LEARNER_SURFACE_INCOMPLETE])
def test_ma_loi_moi_co_category_hop_le(code):
    assert SEMANTIC_FAILURE_CATEGORY[code.value] == "verification_gap"
