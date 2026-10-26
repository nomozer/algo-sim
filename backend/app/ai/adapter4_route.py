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

from copy import deepcopy
from hashlib import sha256
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

    source = raw.get("problem_text") if isinstance(raw, dict) else getattr(raw, "problem_text", None)

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
    if isinstance(source, str):
        r.ai["source_sha256"] = sha256(source.encode("utf-8")).hexdigest()
    r.route_d = deepcopy(_phong_bi(r))
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


def build_adapter4_response(result: KetQuaTuyen, problem_text: str) -> dict[str, Any]:
    """Compose the consumer wrapper, refusing malformed output without exposing diagnostics."""
    from app.ai.hybrid_preview import PreviewInvalid, _noi_chung_minh, _validate_scene, classify_refusal
    from app.simulation.geometry.metric import using
    from app.simulation.semantic_program.pipeline_adapter import (
        compile_semantic_program_to_envelope, validate_semantic_envelope_config,
    )
    from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION
    from app.simulation.geometry_functions.engine import BAC_DAI_LUONG, _hien_thi_ky_hieu, dinh_dang
    from app.simulation.geometry_functions.registry import chuan_hoa
    from app.simulation.geometry_functions.planner import PLANNER_VERSION

    identity = {"schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION, "adapter_version": ADAPTER_V4_VERSION,
                "contract_version": TYPED_FACT_NEXT_V2_SCHEMA_VERSION}

    def refuse(code: str, *, adapter: bool = False) -> dict[str, Any]:
        kind = classify_refusal(code, result.planner, adapter=adapter, problem_text=problem_text)
        return {"schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
                "envelope": {"status": "unsupported", "reason_code": code, "reason": kind.message,
                             "learner_reason": kind.message, "failure_category": kind.failure_category,
                             "refusal_cause": kind.refusal_cause},
                "route_d": {**identity, "status": "REFUSED", "refusal": {"code": code}}}

    if result.status != "SERVED":
        return refuse(result.code or "PREVIEW_RESULT_INVALID")
    try:
        if result.kernel_check is not True or result.spec is None or not result.scene3d:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        route = deepcopy(result.route_d)
        if (any(route.get(k) != v for k, v in identity.items()) or route.get("status") != "SERVED"
                or route.get("refusal") is not None
                or route.get("source_verification") != {"authority": SOURCE_GATE_AUTHORITY}):
            raise PreviewInvalid("PREVIEW_IDENTITY_CHANGED")
        # Substring quotes alone allow appending an unanswered question to an already served result.
        if (not problem_text or result.ai.get("source_sha256") != sha256(problem_text.encode("utf-8")).hexdigest()):
            raise PreviewInvalid("SOURCE_OBJECT_MISMATCH")
        # The gate uses canonical quotes; provenance keeps the planner's verbatim spelling only when it is
        # canonically identical to the verified quote. Raw substring and source-identity checks still apply.
        provenance = deepcopy(result.calls)
        sources = {c["id"]: c["source"] for c in (result.planner or {}).get("calls", [])}
        for c in provenance:
            source = sources.get(c["id"], {})
            quotes = ([source["quote"]] if source.get("quote") else []) + list(source.get("quotes") or [])
            if quotes and [chuan_hoa(q) for q in quotes] == c.get("quotes"):
                c["quotes"] = quotes
        if not provenance or any(
                not c.get("quotes") or any(not isinstance(q, str) or not q or q not in problem_text for q in c["quotes"])
                for c in provenance):
            raise PreviewInvalid("QUOTE_NOT_IN_SOURCE")
        planner = deepcopy(result.planner)
        if planner.get("version") != PLANNER_VERSION or route.get("planner", {}).get("version") != PLANNER_VERSION:
            raise PreviewInvalid("PREVIEW_IDENTITY_CHANGED")
        for group in ("goal_checks", "negated_checks"):
            for observation in planner.get(group, {}).values():
                if (observation.get("proof_status") != "UNVERIFIABLE"
                        or observation.get("can_present_as_proven") is not False
                        or observation.get("evidence_state") not in {
                            "TRUE_ON_CONFIGURATION", "FALSE_ON_CONFIGURATION", "UNVERIFIABLE"}):
                    raise PreviewInvalid("PREVIEW_PROOF_STATUS_INVALID")
        scene = deepcopy(result.scene3d)
        metric = _validate_scene(scene)
        if metric != result.chart_metric or metric.as_json() != result.metric:
            raise PreviewInvalid("PREVIEW_METRIC_MISMATCH")
        unit = scene.get("length_unit")
        if ((result.length_unit and (not unit or unit.get("symbol") != result.length_unit
                                     or unit.get("is_given") is not False))
                or (not result.length_unit and unit) or route.get("length_unit") != result.length_unit):
            raise PreviewInvalid("PREVIEW_LENGTH_UNIT_INVALID")
        if (route.get("answers") != result.answers or route.get("answer_exact") != result.answer_exact
                or set(result.answers) != set(result.answer_exact)):
            raise PreviewInvalid("RESULT_BINDING_UNVERIFIED")
        objects = {o["id"]: o for o in scene["objects"]}
        asks = {c["id"]: c["fn"] for c in result.calls if c["fn"] in BAC_DAI_LUONG}
        if set(result.answer_exact) != set(asks):
            raise PreviewInvalid("RESULT_BINDING_UNVERIFIED")
        for key, answer in result.answer_exact.items():
            dim = answer.get("dim")
            degree = BAC_DAI_LUONG[asks[key]]
            value = result.exec_result.final_memory[f"kq_{key}"]
            coefficient = dinh_dang(value)
            symbolic = (f"cos²={coefficient}" if asks[key].startswith("ask_angle_")
                        else _hien_thi_ky_hieu(value, degree, result.length_unit)
                        if result.length_unit and degree else coefficient)
            if (type(dim) is not int or dim < 0 or not isinstance(result.answers[key], str)
                    or not result.answers[key].strip()
                    or dim != (degree if result.length_unit else 0)
                    or answer.get("coef") != coefficient or result.answers[key] != symbolic
                    or answer.get("unit") != (result.length_unit if dim else None)):
                raise PreviewInvalid("PREVIEW_LENGTH_UNIT_INVALID")
            quantity = objects.get(f"kq_{key}", {})
            if quantity.get("type") != "quantity" or str(quantity.get("value")) != answer.get("coef"):
                raise PreviewInvalid("RESULT_BINDING_UNVERIFIED")
        # Intermediate quantities are also authoritative; a changed intermediate must not accompany a valid answer.
        for obj in objects.values():
            if obj["type"] == "quantity" and str(result.exec_result.final_memory[obj["id"]]) != str(obj["value"]):
                raise PreviewInvalid("RESULT_BINDING_UNVERIFIED")
            if obj["type"] == "point3":
                point = result.exec_result.final_memory[obj["id"]]
                if obj["xyz"] != [str(point.x), str(point.y), str(point.z)]:
                    raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        if route.get("sections") != _phong_bi(result)["sections"]:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        _validate_sections(route["sections"], objects)
        with using(metric):
            envelope = compile_semantic_program_to_envelope(result.spec)
        if validate_semantic_envelope_config(envelope["config"]) or envelope["config"]["execution_truncated"]:
            raise PreviewInvalid("PREVIEW_ENVELOPE_INVALID")
        envelope.update(domain="geometry", source="hybrid_route_d", scene3d=scene)
        envelope["description"] = "Quan sát mô hình dựng từ dữ kiện; các kiểm tra trên hình không phải chứng minh tổng quát."
        texts = [envelope["title"], envelope["description"]]
        texts += [f.get("narration", "") for f in envelope["config"]["frames"]]
        texts += [e.get(k, "") for e in scene["events"] for k in ("learner_text", "explanation")]
        texts += [s.get("learner_text", "") for s in scene["formation"]["steps"]]
        if any(_noi_chung_minh(t) for t in texts):
            raise PreviewInvalid("PREVIEW_PROOF_TEXT_INVALID")
        route.update(planner=planner, source_provenance=provenance, construction_trace=deepcopy(result.trace))
        return {"schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION, "envelope": envelope, "route_d": route}
    except PreviewInvalid as exc:
        return refuse(str(exc), adapter=True)
    except Exception:  # malformed internal output is a technical refusal, never raw traceback text
        return refuse("PREVIEW_VALIDATION_FAILED", adapter=True)


def _validate_sections(sections: list[dict], objects: dict[str, dict]) -> None:
    """Check certificates against the emitted scene, without performing new geometry."""
    from app.ai.hybrid_preview import PreviewInvalid

    def cycle(a, b):
        return bool(a) and len(a) == len(b) and any(
            a == ring[i:] + ring[:i] for ring in (b, list(reversed(b))) for i in range(len(b)))

    def name(value):
        return value.replace("″", "''").replace("′", "'").replace("’", "'")

    ids = set()
    for section in sections:
        sid = section["section_id"]
        obj = objects.get(f"td_{sid}", {})
        vertices = section["vertices"]
        labels = [v["label"] for v in vertices]
        if (sid in ids or obj.get("type") != "section" or len(labels) != len(set(labels))
                or len(labels) != len(obj["polygon"])):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        ids.add(sid)
        solid = next(o for o in objects.values() if o["type"] == "solid" and o["id"] in obj["depends"])
        for vertex in vertices:
            point = objects[vertex["label"]]
            if point["type"] != "point3" or vertex["provenance"] not in _NGUON_GOC.values():
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
            index = obj["polygon"].index(point["xyz"])
            source = obj["vertex_sources"][index]
            edge = [next(o["id"] for o in objects.values() if o["type"] == "point3"
                         and (o["id"] == label or name(o.get("notation") or "") == name(label)))
                    for label in vertex["edge"]]
            indices = source.get("solid_edge_vertex_indices")
            if (len(edge) != 2 or (indices is not None and set(edge) != {solid["vertex_ids"][i] for i in indices})
                    or (indices is None and solid["vertex_ids"][source["solid_vertex_index"]] not in edge)):
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
            provenance = vertex["provenance"]
            auxiliary = point.get("notation") is None and point.get("role") == "Điểm dựng phụ"
            if ((provenance in {"DERIVED_FRESH", "STATED_UNNAMED"} and not auxiliary)
                    or (provenance in {"SOURCE_NAMED", "THROUGH_POINT_REUSE"} and point.get("notation") is None)
                    or (provenance in {"SOURCE_NAMED", "STATED_UNNAMED"} and vertex["stated"] is not True)
                    or (provenance == "DERIVED_FRESH" and (vertex["stated"] is not False or point.get("origin") != "derived"))):
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        boundary, cert = section["boundary"], section["closure_certificate"]
        if boundary is None and cert is None:
            if any(o["type"] == "solid" and o["id"] != solid["id"] for o in objects.values()):
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        elif (not cert or cert.get("verified") is not True or not cert.get("rule")
              or len(boundary) < 3 or len(boundary) != len(set(boundary)) or set(boundary) != set(labels)
              or not cycle(boundary, cert["boundary"])
              or not cycle([objects[label]["xyz"] for label in boundary], obj["polygon"])):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    if len(ids) != sum(o["type"] == "section" for o in objects.values()):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
