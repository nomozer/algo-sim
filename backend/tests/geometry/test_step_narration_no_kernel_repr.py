# -*- coding: utf-8 -*-
"""Step narration of a served Hybrid /4 result never prints a kernel object's Python repr (run `hybrid-backend-reliability`).

Found by the HTTP end-to-end replay of every stored `/2` payload: the interpreter's generic `assign` narration formatted
the assigned value with `str()`, so a step that builds a section circle, a bisector plane or the axis line of a
circumscribed sphere was narrated as "Ghi nhận giá trị vừa tính được: Circle3(center=Vec3(x=Fraction(0, 1), …)" in
`envelope.config.frames[].narration` and `view_steps[].narration` (24 narrations, 15 served problems). The earlier fix of
the same fallback (`ISSUE-ARCH-LLM-VECTOR-ASSIGN-NARRATION`) was gated on compiler programs, which no longer exist.
Scalars (`9/2`, `4π`, `2π√3`) keep their value; only geometric objects are named instead of printed.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

_TOOLS = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_C, _S = _load("curved_probe"), _load("circumscribed_sphere_probe")
CASES = [(f"curved:{x[0]}", _C.payload(x[1], x[2], x[3])) for x in _C.CASES if x[4] != "REFUSE"] + \
        [(f"circumscribed:{x[0]}", x[1]) for x in _S.POSITIVE_CASES]
REPR = re.compile(r"\b(Fraction|Vec3|Plane3|Line3|Circle3|Ellipse3|Radical|CurvedSolid)\(")


@pytest.mark.parametrize("cid,payload", CASES, ids=[c[0] for c in CASES])
def test_served_step_narration_names_objects_instead_of_printing_them(cid, payload):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED", (cid, r.code)
    config = build_adapter4_response(r, payload["problem_text"])["envelope"]["config"]
    narrations = [f["narration"] for f in config["frames"]] + [v["narration"] for v in config["view_steps"]]
    leaked = [n for n in narrations if REPR.search(n)]
    assert not leaked, leaked[:2]


def test_scalar_values_keep_their_exact_value_in_the_narration():
    """Control: the fix must not drop the value of a scalar (the injected fault would be "never print any value")."""
    cyl = next(c for c in CASES if c[0].startswith("curved:") and "area" in str(c[1]["math_goals"]))
    config = build_adapter4_response(run_typed_fact_next_v2_route(cyl[1]), cyl[1]["problem_text"])["envelope"]["config"]
    assert any(re.search(r"\d", v["narration"]) and "π" in v["narration"] for v in config["view_steps"])
