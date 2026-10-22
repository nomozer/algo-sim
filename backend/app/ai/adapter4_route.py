# -*- coding: utf-8 -*-
"""Adapter /4 (`hybrid-simulation-adapter/4`, route-D `/4`) — run `hybrid-contract-v2`, owner D1/D2/D5.

A THIN layer: `typed-fact-next/2` → bridge `/2` → the ONE planner / Registry Source Gate / exact engine / Scene3D path
(`function_route.chay_sau_cau_noi`). It compiles nothing itself and has no legacy path: what the planner cannot express is
refused with its code (curved solids, qualified multi-solid identity, unsupported plane kinds …) — `/1` Adapter /3 stays,
isolated and labelled, for those. Every SERVED result is therefore verified by the Source Gate (strict by construction).
The envelope reports what the engine certified: section boundaries with per-vertex provenance and closure certificates.
Research only: not wired to `/api/analyze`.
"""
from __future__ import annotations

from typing import Any

from app.simulation.geometry_functions import KetQuaTuyen

ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"
ROUTE_D_SIMULATION_V4_SCHEMA_VERSION = "hybrid-route-d-simulation/4"
SOURCE_GATE_AUTHORITY = "registry.kiem_nguon"

#: Planner choice of a section vertex → provenance shown to consumers (never a source fact unless the source states it).
_NGUON_GOC = {"reuse_through_point": "THROUGH_POINT_REUSE", "named_intersection": "SOURCE_NAMED",
              "fresh_intersection": "STATED_UNNAMED", "reuse_intersection": "REUSED_INTERSECTION",
              "derived_fresh": "DERIVED_FRESH"}


def run_typed_fact_next_v2_route(raw: Any) -> KetQuaTuyen:
    """`/2` payload → `KetQuaTuyen` with `route_d` (`/4` envelope). The public boundary never raises: input errors keep
    their codes, an unexpected fault of ours is `ROUTE_INTERNAL_ERROR` (technical, never presented as bad input)."""
    from app.ai import function_route as FR
    from app.simulation.geometry_functions import TuChoi
    from app.simulation.geometry_functions.typed_fact_next_bridge import BRIDGE_V2_VERSION, bridge_v2

    try:
        try:
            b = bridge_v2(raw)
        except TuChoi as e:
            r = KetQuaTuyen("REFUSED", e.code, e.reason, e.calls, details=e.data,
                            planner={"bridge": {"version": BRIDGE_V2_VERSION}})
        else:
            r = FR.chay_sau_cau_noi(b)
    except Exception as exc:  # noqa: BLE001 — boundary record of OUR fault, typed; input errors were refused above
        r = KetQuaTuyen("REFUSED", "ROUTE_INTERNAL_ERROR", f"{type(exc).__name__}: {exc}",
                        planner={"bridge": {"version": BRIDGE_V2_VERSION}})
    r.route_d = _phong_bi(r)
    return r


def _phong_bi(r: KetQuaTuyen) -> dict[str, Any]:
    from app.simulation.geometry_functions.registry import DINH_CAT_CANH
    from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION

    served = r.status == "SERVED"
    sections = []
    for d in (r.planner or {}).get("auxiliary") or [] if served else []:
        if d.get("rule") != DINH_CAT_CANH:
            continue
        sections.append({
            "section_id": d["goal"],
            "boundary": (d.get("closure") or {}).get("boundary"),
            "vertices": [{"label": v["label"], "edge": list(v["edge"]), "provenance": _NGUON_GOC[v["choice"]],
                          "stated": bool(v.get("stated"))} for v in d["vertices"]],
            "closure_certificate": d.get("closure"),
            "declared_boundary": d.get("declared_boundary"),
        })
    return {
        "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
        "adapter_version": ADAPTER_V4_VERSION,
        "contract_version": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        "status": r.status,
        "refusal": None if served else {"code": r.code, "detail": r.reason, "calls": list(r.failed_calls)},
        # every served `/4` result passed the Registry Source Gate; there is no other authority on this route
        "source_verification": {"authority": SOURCE_GATE_AUTHORITY} if served else None,
        "sections": sections,
        "answers": dict(r.answers),
        "answer_exact": dict(r.answer_exact),
        "length_unit": r.length_unit,
        "planner": {k: (r.planner or {}).get(k) for k in ("version", "bridge")},
    }
