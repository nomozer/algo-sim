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

#: Engine-derived section vertex choice (`plane-section-certificate/1`) → provenance (`stated` is always False).
_NGUON_GOC_THIET_DIEN = {
    "reuse_through_point": "THROUGH_POINT_REUSE",
    "solid_vertex": "SOLID_VERTEX_INTERSECTION",
    "engine_derived_edge_cut": "ENGINE_DERIVED_EDGE_CUT",
}


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
    seen = set()
    for d in (r.planner or {}).get("auxiliary") or [] if served else []:
        if d.get("rule") != DINH_CAT_CANH:
            continue
        seen.add(d["goal"])
        sections.append({
            "section_id": d["goal"],
            "boundary": (d.get("closure") or {}).get("boundary"),
            "vertices": [{"label": v["label"], "edge": list(v["edge"]), "provenance": _NGUON_GOC[v["choice"]],
                          "stated": bool(v.get("stated"))} for v in d["vertices"]],
            "closure_certificate": d.get("closure"),
            "declared_boundary": d.get("declared_boundary"),
        })
    for cert in (r.section_certificates or ()) if served else ():
        if cert.get("section_id") in seen:
            continue
        seen.add(cert.get("section_id"))
        sections.append(deepcopy(cert))
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
        _validate_sections(route["sections"], objects, result)
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


def _validate_sections(sections: list[dict], objects: dict[str, dict], result: KetQuaTuyen | None = None) -> None:
    """Check certificates against the emitted scene, without performing new geometry."""
    from app.ai.hybrid_preview import PreviewInvalid
    from app.simulation.geometry_functions.registry import DINH_CAT_CANH

    def cycle(a, b):
        return bool(a) and len(a) == len(b) and any(
            a == ring[i:] + ring[:i] for ring in (b, list(reversed(b))) for i in range(len(b)))

    def name(value):
        return value.replace("″", "''").replace("′", "'").replace("’", "'")

    dinh_cat_ids = {
        d.get("goal")
        for d in ((result.planner or {}).get("auxiliary") or () if result is not None else ())
        if d.get("rule") == DINH_CAT_CANH
    }
    ids = set()
    for section in sections:
        sid = section["section_id"]
        obj = objects.get(f"td_{sid}", {})
        if sid in ids or obj.get("type") != "section":
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        ids.add(sid)
        is_cat_b = section.get("certificate_category") == "ENGINE_DERIVED_SECTION" or "certificate_version" in section
        if sid in dinh_cat_ids and is_cat_b:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        if is_cat_b:
            _validate_engine_derived_section(section, obj, objects, result, name)
            continue
        vertices = section["vertices"]
        labels = [v["label"] for v in vertices]
        if len(labels) != len(set(labels)) or len(labels) != len(obj["polygon"]):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
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


def _polygon_area_squared(poly_pts: list, metric) -> Any:
    """Exact rational squared area of a planar convex polygon in chart coordinates under `metric`."""
    from fractions import Fraction
    from app.ai.hybrid_preview import PreviewInvalid

    if len(poly_pts) < 3:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    p0 = poly_pts[0]
    c1 = (poly_pts[1] - p0).cross(poly_pts[2] - p0)
    c1_sq = c1.dot(c1)
    if c1_sq == 0:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    u1 = poly_pts[1] - p0
    v1 = poly_pts[2] - p0
    det1 = (metric.dot(u1, u1) * metric.dot(v1, v1) - metric.dot(u1, v1) ** 2) / Fraction(4)
    if det1 <= 0:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    total_ratio = Fraction(0)
    for k in range(1, len(poly_pts) - 1):
        uk = poly_pts[k] - p0
        vk = poly_pts[k + 1] - p0
        ck = uk.cross(vk)
        if ck.is_zero() or not ck.cross(c1).is_zero():
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        lam = ck.dot(c1) / c1_sq
        if lam <= 0:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        detk = (metric.dot(uk, uk) * metric.dot(vk, vk) - metric.dot(uk, vk) ** 2) / Fraction(4)
        if detk != lam * lam * det1:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        total_ratio += lam
    area_sq = (total_ratio ** 2) * det1
    if area_sq <= 0:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    return area_sq


def _validate_engine_derived_section(
    section: dict,
    obj: dict,
    objects: dict[str, dict],
    result: KetQuaTuyen | None,
    name,
) -> None:
    """Verify all 10 mathematical and structural invariants of a Category B (`plane-section-certificate/1`) certificate."""
    from fractions import Fraction
    from app.ai.hybrid_preview import PreviewInvalid
    from app.simulation.geometry.exact import Plane3, Vec3
    from app.simulation.geometry.metric import using
    from app.simulation.geometry.section import Polyhedron, cross_section, same_section_cycle
    from app.simulation.geometry_functions.engine import (
        PLANE_SECTION_CERTIFICATE_PRODUCER,
        PLANE_SECTION_CERTIFICATE_RULE,
        PLANE_SECTION_CERTIFICATE_VERSION,
        _binh_phuong,
        ir_name,
    )
    from app.simulation.geometry_functions.registry import MAT_HAI_DUONG, MAT_SONG_SONG, MAT_VUONG_DUONG

    if section.get("certificate_version") != PLANE_SECTION_CERTIFICATE_VERSION:
        raise PreviewInvalid("PREVIEW_IDENTITY_CHANGED")
    sid = section.get("section_id")
    if (section.get("certificate_category") != "ENGINE_DERIVED_SECTION"
            or section.get("section_object_id") != obj["id"]
            or obj["id"] != f"td_{sid}"
            or section.get("declared_boundary") is not None
            or obj.get("closed") is not True
            or bool(obj.get("identity_diagnostics"))):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")

    # Invariant 1: Referenced solid exists and matches the verified solid.
    solid_id = section.get("solid_object_id")
    solid = objects.get(solid_id or "", {})
    if (solid.get("type") != "solid"
            or solid_id not in (obj.get("depends") or ())
            or name(str(solid.get("notation") or "")) != name(str(section.get("solid") or ""))):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    if any(o["type"] == "solid" and o["id"] != solid["id"] and obj["id"] in (o.get("depends") or ())
           for o in objects.values()):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    v_ids = solid.get("vertex_ids") or []
    solid_verts_raw = solid.get("vertices") or []
    faces_raw = solid.get("faces") or []
    if len(v_ids) != len(solid_verts_raw) or len(v_ids) < 4 or not faces_raw:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    faces = [tuple(int(i) for i in f) for f in faces_raw]
    solid_edges = {
        (min(f[i], f[(i + 1) % len(f)]), max(f[i], f[(i + 1) % len(f)]))
        for f in faces for i in range(len(f))
    }
    solid_pts: list[tuple[Fraction, Fraction, Fraction]] = []
    for idx, vid in enumerate(v_ids):
        po = objects.get(vid, {})
        if po.get("type") != "point3" or po.get("xyz") != solid_verts_raw[idx]:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        solid_pts.append(tuple(Fraction(c) for c in po["xyz"]))

    # Invariant 2: Cutting plane is the verified source-requested plane.
    plane_id = section.get("plane_object_id")
    plane_obj = objects.get(plane_id or "", {})
    plane_points = section.get("plane_points") or []
    if (plane_obj.get("type") != "plane3"
            or plane_id != f"mp_td_{sid}"
            or plane_id not in (obj.get("depends") or ())
            or len(plane_points) != 3
            or {ir_name(p) for p in plane_points} != set(plane_obj.get("depends") or ())):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    eq = section.get("plane_equation") or {}
    normal_raw = eq.get("normal") or []
    offset_raw = eq.get("offset")
    if len(normal_raw) != 3 or offset_raw is None:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    normal = tuple(Fraction(x) for x in normal_raw)
    offset = Fraction(offset_raw)
    if next((x for x in normal if x != 0), Fraction(0)) != Fraction(1):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    p_plane = tuple(Fraction(c) for c in plane_obj["point"])
    n_plane = tuple(Fraction(c) for c in plane_obj["normal"])
    nz_plane = next((x for x in n_plane if x != 0), Fraction(0))
    if (nz_plane == 0
            or tuple(x / nz_plane for x in n_plane) != normal
            or sum(a * b for a, b in zip(normal, p_plane)) != offset):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    for p_lbl in plane_points:
        po = objects.get(ir_name(p_lbl), {})
        if po.get("type") != "point3":
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        if sum(a * b for a, b in zip(normal, (Fraction(c) for c in po["xyz"]))) != offset:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")

    plane_rule = section.get("plane_rule")
    rel = section.get("plane_relation") or {}
    tp = section.get("through_point")
    if plane_rule == "explicit_plane":
        if tp is not None or rel.get("kind") != "explicit_points" or len(rel.get("points") or ()) < 3:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        if list(rel["points"][:3]) != plane_points:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        for p_lbl in rel["points"]:
            po = objects.get(ir_name(p_lbl), {})
            if po.get("type") != "point3" or sum(a * b for a, b in zip(normal, (Fraction(c) for c in po["xyz"]))) != offset:
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    elif plane_rule in {MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG}:
        if not isinstance(tp, str) or not tp or rel.get("through_point") != tp:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        tp_obj = objects.get(ir_name(tp), {})
        if tp_obj.get("type") != "point3" or sum(a * b for a, b in zip(normal, (Fraction(c) for c in tp_obj["xyz"]))) != offset:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        if result is not None:
            dan = next(
                (d for d in ((result.planner or {}).get("auxiliary") or ())
                 if d.get("rule") == plane_rule and sid in (d.get("targets") or ())),
                None,
            )
            if dan is None or dan.get("point") != tp or [dan["point"], *dan["labels"]] != plane_points:
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        # Derived cutting plane cannot be a boundary face of the solid.
        dau = [sum(a * b for a, b in zip(normal, pt)) - offset for pt in solid_pts]
        if sum(x == 0 for x in dau) >= 3 and {x > 0 for x in dau if x != 0} != {True, False}:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    else:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")

    # Invariants 3, 4, 5, 6, 7: Section vertices, supporting edges, exact interpolation, canonicalization, cyclic order.
    vertices = section.get("vertices") or []
    poly_raw = obj.get("polygon") or []
    v_sources = obj.get("vertex_sources") or []
    ep_entities = obj.get("endpoint_entities") or []
    if (len(vertices) < 3
            or len(vertices) != len(poly_raw)
            or len(vertices) != len(v_sources)
            or len(vertices) != len(ep_entities)):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")

    seen_xyz: set[tuple[Fraction, Fraction, Fraction]] = set()
    seen_entity_ids: set[str] = set()
    poly_pts: list[Vec3] = []
    tp_xyz = (tuple(Fraction(c) for c in objects[ir_name(tp)]["xyz"])
              if isinstance(tp, str) and ir_name(tp) in objects else None)

    for idx, (vertex, poly_xyz, v_src, ep) in enumerate(zip(vertices, poly_raw, v_sources, ep_entities)):
        if vertex.get("ordinal") != idx or vertex.get("xyz") != poly_xyz:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        pt_q = tuple(Fraction(c) for c in poly_xyz)
        poly_pts.append(Vec3(*pt_q))
        # Invariant 3: Lies on cutting plane in exact arithmetic.
        if sum(a * b for a, b in zip(normal, pt_q)) != offset:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        # Invariant 6: Duplicate intersections canonicalized.
        if pt_q in seen_xyz:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        seen_xyz.add(pt_q)
        entity_id = vertex.get("entity_id")
        if (not isinstance(entity_id, str) or not entity_id
                or entity_id in seen_entity_ids
                or ep.get("entity_id") != entity_id
                or ep.get("section_vertex_ordinal") != idx
                or ep.get("anonymous_coordinate_fallback") is not False):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        seen_entity_ids.add(entity_id)

        # Invariants 4 & 5: Lies on solid boundary and supporting edge with exact rational parameter t in [0, 1].
        edge_labels = vertex.get("edge") or []
        edge_indices = vertex.get("solid_edge_vertex_indices") or []
        if len(edge_labels) != 2 or len(edge_indices) != 2:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        ia, ib = edge_indices[0], edge_indices[1]
        if (not (isinstance(ia, int) and isinstance(ib, int) and 0 <= ia < ib < len(v_ids))
                or (ia, ib) not in solid_edges
                or [ir_name(x) for x in edge_labels] != [v_ids[ia], v_ids[ib]]):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        t_val = Fraction(vertex.get("t"))
        va, vb = solid_pts[ia], solid_pts[ib]
        if any((1 - t_val) * va[j] + t_val * vb[j] != pt_q[j] for j in range(3)):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")

        src_kind = vertex.get("source_kind")
        if src_kind != v_src.get("kind"):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        is_tp = tp_xyz is not None and pt_q == tp_xyz
        choice = vertex.get("choice")
        prov = vertex.get("provenance")
        if choice not in _NGUON_GOC_THIET_DIEN or prov != _NGUON_GOC_THIET_DIEN[choice] or vertex.get("stated") is not False:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")

        if src_kind == "SOLID_VERTEX":
            iv = vertex.get("solid_vertex_index")
            if (iv != v_src.get("solid_vertex_index")
                    or iv not in (ia, ib)
                    or t_val != (Fraction(0) if iv == ia else Fraction(1))
                    or solid_pts[iv] != pt_q
                    or entity_id != v_ids[iv]
                    or ep.get("provenance_kind") != "SOLID_VERTEX"):
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
            expected_choice = "reuse_through_point" if is_tp else "solid_vertex"
            if (choice != expected_choice
                    or vertex.get("label") != v_ids[iv]
                    or objects[v_ids[iv]].get("notation") is None):
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        elif src_kind == "SOLID_EDGE_INTERSECTION":
            src_pair = v_src.get("solid_edge_vertex_indices") or []
            expected_eid = f"section:{obj['id']}:point:on:{solid['id']}::edge:{v_ids[ia]}-{v_ids[ib]}"
            if (vertex.get("solid_vertex_index") is not None
                    or v_src.get("solid_vertex_index") is not None
                    or len(src_pair) != 2
                    or (min(src_pair), max(src_pair)) != (ia, ib)
                    or not (Fraction(0) < t_val < Fraction(1))
                    or any(sv == pt_q for sv in solid_pts)
                    or entity_id != expected_eid
                    or ep.get("provenance_kind") != "SOLID_EDGE_INTERSECTION"):
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
            expected_choice = "reuse_through_point" if is_tp else "engine_derived_edge_cut"
            expected_lbl = ir_name(tp) if is_tp else None
            if choice != expected_choice or vertex.get("label") != expected_lbl:
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
            if is_tp and objects[ir_name(tp)].get("notation") is None:
                raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        else:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")

    # Invariant 7: Cyclic face adjacency and closure certificate.
    m = len(vertices)
    for i in range(m):
        vc, vn = vertices[i], vertices[(i + 1) % m]
        fc = {
            fi for fi, f in enumerate(faces)
            if (vc["solid_vertex_index"] in f if vc["source_kind"] == "SOLID_VERTEX"
                else set(vc["solid_edge_vertex_indices"]) <= set(f))
        }
        fn = {
            fi for fi, f in enumerate(faces)
            if (vn["solid_vertex_index"] in f if vn["source_kind"] == "SOLID_VERTEX"
                else set(vn["solid_edge_vertex_indices"]) <= set(f))
        }
        if not (fc & fn):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")

    boundary = section.get("boundary")
    cert = section.get("closure_certificate") or {}
    expected_boundary = [v["entity_id"] for v in vertices]
    if (boundary != expected_boundary
            or cert.get("verified") is not True
            or cert.get("version") != PLANE_SECTION_CERTIFICATE_VERSION
            or cert.get("rule") != PLANE_SECTION_CERTIFICATE_RULE
            or cert.get("producer") != PLANE_SECTION_CERTIFICATE_PRODUCER
            or cert.get("boundary") != expected_boundary
            or cert.get("polygon") != poly_raw):
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")

    # Invariants 8, 9, 10: Nondegeneracy, kernel cross_section agreement, and exact Gram-metric area agreement.
    if result is not None:
        sec_mem = result.exec_result.final_memory.get(obj["id"])
        if (sec_mem is None or not getattr(sec_mem, "is_closed", False)
                or list(sec_mem.polygon) != poly_pts):
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        with using(result.chart_metric):
            p3 = [Vec3(*(Fraction(c) for c in objects[ir_name(p)]["xyz"])) for p in plane_points]
            cs = cross_section(Polyhedron(tuple(Vec3(*p) for p in solid_pts), tuple(faces)), Plane3.through(*p3))
        if not same_section_cycle(poly_pts, cs.polygon) or list(cs.polygon) != poly_pts:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        area_sq = _polygon_area_squared(poly_pts, result.chart_metric)
        if Fraction(cert.get("area_squared")) != area_sq:
            raise PreviewInvalid("PREVIEW_RESULT_INVALID")
        for c in result.calls:
            if c.get("fn") != "ask_section_area" or (c.get("args") or {}).get("solid") != section.get("solid"):
                continue
            c_plane = (c.get("args") or {}).get("plane") or []
            if c_plane and all(
                ir_name(p) in objects
                and sum(a * b for a, b in zip(normal, (Fraction(x) for x in objects[ir_name(p)]["xyz"]))) == offset
                for p in c_plane
            ):
                if _binh_phuong(result.exec_result.final_memory.get(f"kq_{c['id']}")) != area_sq:
                    raise PreviewInvalid("PREVIEW_RESULT_INVALID")
