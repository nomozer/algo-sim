"""M15 Task 13 (W3) — boolean dual-surface: hai bề mặt KHÔNG hợp nhất, owned tách bạch.

`logic.and_gate` (chuyên biệt, 1 cổng cố định) và `generic.rule_scene` (LLM tự
ghép rule qua đối tượng trung gian — DAG, có thể lồng NOT/AND/OR) CÙNG thuộc
family `boolean_composition` nhưng sở hữu hai cơ chế canonical KHÁC nhau:
`single_gate_truth_table` (and_gate) vs `composed_rule_dag` (generic). Đây
KHÔNG phải hợp nhất hai bề mặt thành một selector — and_gate vẫn là choice
độc lập trên menu classify (không FamilySelector cho boolean_composition,
giống scan ở Task 12 nhưng lý do khác: ở đây hai target có NGỮ NGHĨA cơ chế
khác nhau, không phải "variant cùng họ").

Ranh giới and_gate ↔ generic.rule_scene đã live-verify ở M11 (case NOT →
generic, case a-and đối chứng → and_gate); test 2 pin lại đúng expectation đó
trong dataset để tránh sửa nhầm dataset làm trôi ranh giới đã chứng minh live.

Khóa 11: wave này KHÔNG thêm production gate kiểu "check truth table" — ranh
giới and_gate/generic tiếp tục do classify quyết định (LLM chọn simulation_id
theo capability, không phải một validator mới so bảng chân trị). Test 3 khoá
điều đó bằng source-scan trên app.ai.pipeline.
"""

from __future__ import annotations


def test_hai_be_mat_boolean_khong_hop_nhat_va_owned_khac_nhau():
    from app.simulation.catalog import CATALOG

    and_mems = [
        m for m in CATALOG["logic.and_gate"].family_memberships
        if m.family_id.value == "boolean_composition"
    ]
    gen_mems = [
        m for m in CATALOG["generic.rule_scene"].family_memberships
        if m.family_id.value == "boolean_composition"
    ]
    assert and_mems and gen_mems
    assert and_mems[0].owned_mechanisms == ("boolean_composition.single_gate_truth_table",)
    assert gen_mems[0].owned_mechanisms == ("boolean_composition.composed_rule_dag",)
    # hai target KHÔNG sở hữu chung một cơ chế (dual surface thật, không trùng)
    assert set(and_mems[0].owned_mechanisms).isdisjoint(set(gen_mems[0].owned_mechanisms))


def test_boundary_lock_m11_expectations_giu_nguyen():
    """Pin ranh giới đã live-verify M11: case NOT (m11-nested-not, pool curriculum)
    → generic.rule_scene; case a-and đối chứng (DATASET đóng băng) → logic.and_gate.
    Lock chống sửa nhầm dataset làm trôi ranh giới đã chứng minh live."""
    from app.evaluation.dataset import DATASET
    from app.evaluation.datasets.curriculum import CURRICULUM_ITEMS

    a_and = next(it for it in DATASET if it.id == "a-and")
    assert a_and.expect_simulation_id == "logic.and_gate"

    m11_not = next(it for it in CURRICULUM_ITEMS if it.id == "m11-nested-not")
    assert m11_not.expect_simulation_id == "generic.rule_scene"
    assert "m11_compose" in m11_not.tags


def test_khong_them_production_truth_table_gate():
    """Khóa 11 — wave này không thêm symbol production kiểu check_truth_table/
    truth_table_gate: ranh giới and_gate/generic vẫn do classify quyết định,
    không phải một validator/gate mới so bảng chân trị."""
    import inspect

    import app.ai.pipeline as p

    src = inspect.getsource(p)
    assert "truth_table" not in src
