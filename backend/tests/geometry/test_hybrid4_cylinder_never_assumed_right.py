"""Hybrid /4: a cylinder whose axis is not certified ⊥ to its base never gets the right-cylinder volume.

Ported from the retired Axo `test_construction_integrity_audit.py::test_mandatory_regression_5_2_…` (it ran on Adapter /3
and on a `/1` `oblique_cylinder` fact that main does not have; `oblique_cylinder` is deliberately NOT added to /4). The
naive reading of each text below is r = OA = √5, h = OO' = 3 ⇒ V = π·5·3 = 15π; that number is only correct when the
source certifies OO' ⊥ (base). A right circular cylinder whose axis is merely tilted in the coordinate frame is a
different thing and stays served (`test_curved_foundation.py`, `test_oblique_cylinder_ellipse.py`).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route

_P = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/curved_probe.py"
_spec = importlib.util.spec_from_file_location("curved_probe", _P)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

Q = "Tính thể tích khối trụ."


def _run(given: str):
    p = C.payload((given, C.solid("cylinder", "O.O'", "O", "O'", "A", "√5", "3", given[:-1]), []), "volume", Q)
    return run_typed_fact_next_v2_route(p)


@pytest.mark.parametrize("given, code", [
    ("Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O. Biết OO' = 3, OA = √5 và OO' không vuông góc với OA.",
     "NEGATED_CLAUSE"),
    ("Cho hình trụ xiên có hai tâm đáy O, O', bán kính đáy OA = √5, độ dài đoạn nối tâm OO' = 3, OO' tạo với mặt đáy một góc 60 độ.",
     "CURVED_WORDING_UNSUPPORTED"),
    ("Cho hình trụ có tâm hai đáy O và O', điểm A nằm trên đường tròn đáy tâm O sao cho OO' = 3, OA = √5 và OO' vuông góc với bán kính OA.",
     "CURVED_WORDING_UNSUPPORTED"),
], ids=["oo_not_perp_oa", "explicit_oblique_60deg", "perp_to_one_radius_only"])
def test_uncertified_axis_never_serves_15pi(given: str, code: str) -> None:
    r = _run(given)
    assert (r.status, r.code) == ("REFUSED", code), f"{r.status} {r.code} {r.answers}: axis not certified ⊥ base"
    assert "15π" not in str(r.answers or {})


def test_control_stated_radius_and_height_is_served_15pi() -> None:
    given = "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng √5 và chiều cao bằng 3."
    r = _run(given)
    assert r.status == "SERVED", r.code
    assert r.answers == {"mg1": "15π"}
