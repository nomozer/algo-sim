from __future__ import annotations

import pytest

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


def test_v12_underdetermined_similarity_cases_fail_closed_without_modifying_locked_planner_or_engine() -> None:
    """§17 / A4 boundary: D01..D05 remain explicitly refused until planner/engine similarity policy is approved."""
    d_cases = [
        ("D01", "Hãy mô phỏng hình chóp S.ABCD có đáy ABCD là hình vuông và SA vuông góc với đáy.", "AMBIGUOUS_FACT"),
        ("D02", "Vẽ hình lập phương ABCD.A'B'C'D'.", "MISSING_DIMENSION"),
        ("D03", "Dựng hình tứ diện đều ABCD.", "MISSING_DIMENSION"),
        ("D04", "Mô phỏng hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều.", "AMBIGUOUS_FACT"),
        ("D05", "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với (ABC). Hãy vẽ hình.", "MISSING_DIMENSION"),
    ]
    for _cid, text, expected_code in d_cases:
        status, code = _run_kernel(text)
        assert status in (LOCAL_PARSE_AMBIGUOUS, "REFUSED")
        assert code == expected_code


def test_v12_metric_goal_on_unitless_cube_stays_fail_closed() -> None:
    """Unit-similarity policy must NEVER silently invent scale for metric queries ('Tính thể tích...')."""
    text = "Vẽ hình lập phương ABCD.A'B'C'D' và tính thể tích khối lập phương đó."
    lp = parse_geometry_problem_locally(text)
    assert lp.status == LOCAL_PARSE_COMPLETE and lp.payload is not None
    status, code = _run_kernel(text)
    assert status == "REFUSED"
    assert code == "MISSING_DIMENSION"
