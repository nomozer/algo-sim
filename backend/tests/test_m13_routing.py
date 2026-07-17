# -*- coding: utf-8 -*-
"""M13 §4: SERVER quyết accept/gap — tất định, KHÔNG mock LLM thật, hai tín hiệu bổ sung."""
from app.simulation.computation_gate import check_computation_ownership
from app.simulation.representation import build_representation_plan


def _analysis(**over):
    base = {
        "entity_roles": ["relational"], "relation_roles": ["relational"],
        "process_roles": ["movement"], "interaction_needs": [],
        "visual_needs": ["relational"], "temporal_needs": ["temporal"],
        "result_ownership": "provided",
    }
    base.update(over)
    return base


def test_kenh_1_arbitrary_algorithm_role_lam_gap_fired():
    analysis = _analysis(process_roles=["arbitrary_algorithm", "movement"])
    plan = build_representation_plan(analysis)
    assert check_computation_ownership(analysis, plan) is not None


def test_kenh_2_result_ownership_algorithmic_gap_KE_CA_khi_role_bi_bo_sot():
    """Blocker 1: analyze quên arbitrary_algorithm nhưng khai algorithmic →
    server VẪN gap. Phán quyết không phụ thuộc một kênh prompt duy nhất."""
    analysis = _analysis(result_ownership="algorithmic")  # KHÔNG có role gap
    plan = build_representation_plan(analysis)
    assert plan["unsupported_capabilities"] == []  # kênh 1 im
    reason = check_computation_ownership(analysis, plan)
    assert reason is not None and "thuật toán" in reason


def test_canh_cau_truc_hop_le_khong_bi_gap():
    analysis = _analysis()  # provided, không role gap
    plan = build_representation_plan(analysis)
    assert check_computation_ownership(analysis, plan) is None


def test_rule_derivable_khong_bi_gap():
    """Đổi nhị phân / đèn-công tắc: tính bằng rule từ giá trị cho sẵn — đi tiếp."""
    analysis = _analysis(result_ownership="rule_derivable", entity_roles=["numeric", "interactive"])
    plan = build_representation_plan(analysis)
    assert check_computation_ownership(analysis, plan) is None


def test_result_ownership_thieu_hoac_la_bi_tu_choi_an_toan():
    """Ràng buộc duyệt lần 3: fail-closed — thiếu/ngoài enum KHÔNG default."""
    for bad in (None, "", "unknown", "maybe_algorithmic"):
        analysis = _analysis()
        if bad is None:
            analysis.pop("result_ownership")
        else:
            analysis["result_ownership"] = bad
        plan = build_representation_plan(analysis)
        reason = check_computation_ownership(analysis, plan)
        assert reason is not None and "từ chối an toàn" in reason
