from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import (
    LOCAL_PARSE_AMBIGUOUS,
    LOCAL_PARSE_COMPLETE,
    parse_geometry_problem_locally,
)
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2


def _run_kernel(text: str):
    lp = parse_geometry_problem_locally(text)
    if lp.status == LOCAL_PARSE_AMBIGUOUS or lp.payload is None:
        return lp.status, lp.reason_code
    b = bridge_v2(lp.payload)
    p = planner.lap_ke_hoach({"facts": b["facts"]}, text)
    tok = registry._CHINH_SACH_XUAT.set(b["bridge"].get("output_policies"))
    try:
        kr = engine.dung_tu_loi_goi(
            text,
            {"calls": p.calls},
            auxiliary=tuple(p.auxiliary),
            read_quotes=tuple(
                q for g in (*p.goals, *p.negated) if g.get("call") for q in g["call"]["source"]["quotes"]
            ),
        )
    finally:
        registry._CHINH_SACH_XUAT.reset(tok)
    return kr.status, kr.code


def test_v12_similarity_policy_serves_1dof_regular_solids_and_refuses_multi_dof() -> None:
    """§17 integration: 1-DOF similarity-unique SIMULATE_ONLY solids (D02, D03) serve with UNIT_SIMILARITY_REPRESENTATIVE
    and answers={}, while multi-DOF underdetermined solids (D01, D04, D05) stay explicitly refused."""
    for cid, text in (
        ("D02", "Vẽ hình lập phương ABCD.A'B'C'D'."),
        ("D03", "Dựng hình tứ diện đều ABCD."),
    ):
        status, code = _run_kernel(text)
        assert status == "SERVED" and code is None, (cid, status, code)
        out = route_text_input(text, allow_live_ai=False)
        assert out.status == "SERVED", (cid, out.response)
        rd = out.response["route_d"]
        assert rd.get("scale_policy") == "UNIT_SIMILARITY_REPRESENTATIVE", (cid, rd)
        assert rd.get("answers") == {}, (cid, rd.get("answers"))
        assert rd.get("scene_configuration", {}).get("kind") == "SIMILARITY_SCALE_ILLUSTRATIVE", (cid, rd)

    for cid, text, expected_code in (
        ("D01", "Hãy mô phỏng hình chóp S.ABCD có đáy ABCD là hình vuông và SA vuông góc với đáy.", "AMBIGUOUS_FACT"),
        ("D04", "Mô phỏng hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều.", "AMBIGUOUS_FACT"),
        ("D05", "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với (ABC). Hãy vẽ hình.", "MISSING_DIMENSION"),
    ):
        status, code = _run_kernel(text)
        assert status in (LOCAL_PARSE_AMBIGUOUS, "REFUSED"), (cid, status, code)
        assert code == expected_code, (cid, code)


def test_v12_metric_goal_on_unitless_cube_stays_fail_closed() -> None:
    """Unit-similarity policy must NEVER silently invent scale for metric queries ('Tính thể tích...')."""
    text = "Vẽ hình lập phương ABCD.A'B'C'D' và tính thể tích khối lập phương đó."
    lp = parse_geometry_problem_locally(text)
    assert lp.status == LOCAL_PARSE_COMPLETE and lp.payload is not None
    status, code = _run_kernel(text)
    assert status == "REFUSED"
    assert code == "MISSING_DIMENSION"
