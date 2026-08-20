# -*- coding: utf-8 -*-
"""`execution_authority_gate` — LÀM SẮC R0, không nới (spec §3.3).

Luật cũ ở `computation_gate` đọc là *"algorithmic thì từ chối"*. Luật THẬT đằng
sau nó luôn là: **kết quả phải có một AUTHORITY TẤT ĐỊNH sở hữu**. Khi chưa có
interpreter, hai câu đó trùng nhau nên viết tắt được. Có interpreter rồi thì
phải tách — nếu không, hệ sẽ từ chối chính lớp bài mà nó vừa có năng lực làm.

R0 nguyên vẹn: LLM vẫn KHÔNG BAO GIỜ là authority. Thay đổi duy nhất là
`SemanticProgramInterpreter` ĐƯỢC CÔNG NHẬN là một authority tất định.
"""
from app.simulation.execution_authority_gate import check_execution_authority


def test_provided_thi_qua_du_khong_co_interpreter():
    assert check_execution_authority(
        {"result_ownership": "provided"}, {}, has_interpreter=False
    ) is None


def test_rule_derivable_thi_qua_du_khong_co_interpreter():
    assert check_execution_authority(
        {"result_ownership": "rule_derivable"}, {}, has_interpreter=False
    ) is None


def test_algorithmic_khong_co_interpreter_thi_gap():
    """Giữ nguyên hành vi cũ trên đường module — không nới cho đường đó."""
    reason = check_execution_authority(
        {"result_ownership": "algorithmic"}, {}, has_interpreter=False
    )
    assert reason is not None
    assert "authority" in reason.lower()


def test_algorithmic_CO_interpreter_thi_qua():
    """Thay đổi DUY NHẤT so với computation_gate cũ."""
    assert check_execution_authority(
        {"result_ownership": "algorithmic"}, {}, has_interpreter=True
    ) is None


def test_thieu_ownership_thi_fail_closed():
    assert check_execution_authority({}, {}, has_interpreter=True) is not None


def test_gia_tri_ngoai_enum_cung_fail_closed():
    assert check_execution_authority(
        {"result_ownership": "linh_tinh"}, {}, has_interpreter=True
    ) is not None


def test_known_gap_role_van_chan_du_co_interpreter():
    """Interpreter không phải giấy thông hành cho MỌI cơ chế.

    Vai trò không engine nào sở hữu (hình học dẫn xuất, chuyển động liên tục…)
    vẫn bị chặn — có interpreter không có nghĩa là biểu diễn được mọi thứ.
    """
    from app.simulation.dsl.manifest import known_gap_roles

    gap = sorted(known_gap_roles())[0]
    reason = check_execution_authority(
        {"result_ownership": "algorithmic"},
        {"unsupported_capabilities": [gap]},
        has_interpreter=True,
    )
    assert reason is not None
    assert gap in reason
