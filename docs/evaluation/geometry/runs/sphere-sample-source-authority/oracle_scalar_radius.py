"""Correction layer over the locked `step-math-validation/oracle.py` (hash-pinned, not edited).

The locked oracle predates the IR's scalar-radius sphere (`construct_curved_solid.radius`, 2026-09-04): it reads a
`rim_point` and fails with "Expected 3-vector" when the sphere is declared by its radius. This layer checks such a
sphere against the GIVEN radius it depends on numerically (radius_sq must equal R²), then hands the locked oracle a
copy whose rim point is anchor + (R, 0, 0) — built from the given R, never from engine output — so every other check
(intersection circle r² = R² − d², volumes, incidence) runs unchanged. Euclidean charts only; any other metric or a
missing/ambiguous given radius is reported as a failure, not silently passed. No `app` or `tests` import.
"""
from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

_LOCKED = Path(__file__).resolve().parent.parent / "step-math-validation"
if str(_LOCKED) not in sys.path:
    sys.path.insert(0, str(_LOCKED))

import oracle as base  # noqa: E402


def _scalar_radius_failures(scene: dict[str, Any]) -> list[str]:
    _, quantities = base.extract_objects_and_quantities(scene)
    euclid = base.parse_metric(scene.get("chart_metric")) == base.IDENTITY_METRIC
    out = []
    for o in scene.get("objects") or []:
        if o.get("type") != "curved_solid" or o.get("rim_point") is not None:
            continue
        nums = [e["source_id"] for e in o.get("dependency_edges") or [] if e.get("relation") == "numerical"]
        given = [base.eval_symbolic_expr(quantities[n]["value"]) for n in nums
                 if n in quantities and quantities[n].get("value") is not None]
        kind = o.get("curved_kind")
        axial = kind in ("cylinder", "cone") and o.get("apex_or_top") is not None
        if (kind != "ball" and not axial) or len(given) != 1 or not euclid:
            out.append(f"Curved solid {o.get('id')}: scalar radius form not verifiable here "
                       f"(kind={kind}, given radii={len(given)}, euclidean={euclid})")
            o["rim_point"] = o["anchor"]          # zero radius: the locked oracle fails it too instead of raising
            continue
        r = given[0]
        if abs(base.eval_symbolic_expr(o["radius_sq"]) - r * r) > 1e-5:
            out.append(f"{kind} {o.get('id')} radius_sq={o['radius_sq']} != given radius^2={r * r}")
        anc = base.parse_vec3(o["anchor"])
        u = (1.0, 0.0, 0.0)
        if axial:                                  # rim direction ⟂ axis, so the locked oracle's height check still holds
            a = base.v_sub(base.parse_vec3(o["apex_or_top"]), anc)
            e = (1.0, 0.0, 0.0) if abs(a[0]) < 0.9 * base.v_norm(a) else (0.0, 1.0, 0.0)
            c = (a[1] * e[2] - a[2] * e[1], a[2] * e[0] - a[0] * e[2], a[0] * e[1] - a[1] * e[0])
            u = tuple(x / base.v_norm(c) for x in c)
        o["rim_point"] = [repr(anc[i] + r * u[i]) for i in range(3)]
    return out


def verify_scene_mathematics(scene: dict[str, Any], **kw: Any):
    sc = deepcopy(scene)
    extra = _scalar_radius_failures(sc)
    rep = base.verify_scene_mathematics(sc, **kw)
    if extra:
        cat = rep.category_results["8_distance_area_volume"]
        cat.passed = False
        cat.failures.extend(extra)
        rep.errors.extend(extra)
        rep.verdict = "INVALID"
    return rep
