# -*- coding: utf-8 -*-
"""Continuous 3D construction state enrichment & exact geometric continuity validation.

Enriches Route D `scene3d.formation.steps` in a backward-compatible way with:
- stable `step_id` and `coordinate_frame_id` (`canonical_chart_v1`);
- explicit `depends_on`, `preconditions`, `created_ids`, `reused_ids`, `highlighted_ids`, `retired_ids`;
- `verification_refs` linked to deterministic kernel/engine certificates;
- structured 5-part pedagogical `step_summary` (`what`, `inputs`, `validity`, `result`, `next_use`).

Validates cumulative geometric continuity fail-closed (`validate_construction_continuity`) with zero LLM calls.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from app.simulation.geometry.exact import GeometryError
from app.simulation.geometry.metric import Metric

CANONICAL_COORDINATE_FRAME_ID = "canonical_chart_v1"

_PRIMARY_PERSISTENT_TYPES = frozenset({"solid", "curved_solid", "section"})


def _clean_text(text: Any) -> str:
    s = str(text or "").strip()
    return s.replace("_", " ") if "_" in s else s


def _obj_ref_name(obj: dict[str, Any]) -> str:
    for key in ("notation", "display_label", "label", "reference"):
        val = obj.get(key)
        if isinstance(val, str) and val.strip() and "_" not in val:
            return val.strip()
    return "đối tượng hình học"


def _step_validity(
    step_idx: int,
    step: dict[str, Any],
    step_events: list[dict[str, Any]],
    created_objs: list[dict[str, Any]],
    objects: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    refs: list[str] = []
    if step_idx == 0 or any(e.get("action") == "INIT" for e in step_events):
        return (
            "Các đỉnh và dữ kiện xuất phát trực tiếp từ giả thiết đã kiểm tra của đề bài trong hệ quy chiếu chuẩn.",
            ["source_gate:verified", f"frame:{CANONICAL_COORDINATE_FRAME_ID}"],
        )

    for ev in step_events:
        if ev.get("justification_text"):
            oid = ev.get("object")
            if oid:
                refs.append(f"section_cut:{oid}")
            return (_clean_text(ev["justification_text"]), refs or ["section_cut:verified"])

    primary = created_objs[0] if created_objs else objects.get((step_events[0].get("object") or "") if step_events else "")
    if primary is not None:
        oid = primary["id"]
        prod = str(primary.get("producer") or "")
        otype = str(primary.get("type") or "")
        if primary.get("perpendicular_witness"):
            refs.append(f"perpendicular_witness:{oid}")
        if prod == "construct_point.midpoint":
            refs.append(f"midpoint:{oid}")
            return ("Hai đầu mút của đoạn thẳng đã xác định nên trung điểm tồn tại duy nhất.", refs)
        if prod == "construct_point.centroid":
            refs.append(f"centroid:{oid}")
            return ("Các đỉnh của đa giác đã xác định nên trọng tâm được xác định duy nhất.", refs)
        if prod == "construct_point.divide_segment":
            refs.append(f"divide_segment:{oid}")
            return ("Đoạn thẳng và tỉ số chia từ giả thiết đã xác định nên điểm chia là duy nhất.", refs)
        if prod.startswith("construct_point.project_onto"):
            refs.append(f"orthogonal_projection:{oid}")
            return (
                "Điểm gốc và đối tượng nhận hình chiếu đã xác định trong hệ đo Euclid chính xác nên chân đường vuông góc là duy nhất.",
                refs,
            )
        if prod == "construct_point.intersect_line_plane":
            refs.append(f"intersect_line_plane:{oid}")
            return ("Đường thẳng cắt mặt phẳng tại một giao điểm duy nhất thỏa phương trình mặt phẳng.", refs)
        if prod in ("construct_point.intersect_lines", "construct_point.line_line_intersection"):
            refs.append(f"intersect_lines:{oid}")
            return ("Hai đường thẳng đồng phẳng và không song song nên cắt nhau tại đúng một điểm.", refs)
        if prod == "construct_point.translate" or otype == "vector3":
            refs.append(f"vector_translation:{oid}")
            return ("Điểm gốc và vectơ dịch chuyển đã xác định trong cùng hệ tọa độ nên ảnh tịnh tiến là duy nhất.", refs)
        if otype == "plane3":
            refs.append(f"plane_unique:{oid}")
            return ("Mặt phẳng được xác định duy nhất từ các điểm không thẳng hàng và quan hệ hình học đã kiểm tra.", refs)
        if otype == "section":
            refs.append(f"section_closed:{oid}")
            return ("Mặt phẳng cắt giao với các mặt của khối tạo thành đa giác thiết diện khép kín hợp lệ.", refs)
        if otype == "circle3":
            refs.append(f"curved_section:{oid}")
            return ("Mặt phẳng cắt khối tròn xoay theo đường tròn giao tuyến có tâm nằm trên mặt phẳng cắt và bán kính dương.", refs)
        if otype in ("solid", "curved_solid", "polygon3", "segment3", "line3"):
            refs.append(f"construct:{oid}")
            return ("Các đỉnh và yếu tố xác định đối tượng đã có đủ từ các bước trước trong cùng hệ quy chiếu.", refs)
        if otype == "quantity":
            refs.append(f"exact_kernel:{oid}")
            return ("Các đối tượng tham gia phép tính đã xác định chính xác và giá trị khớp chứng chỉ đại số.", refs)

    sk = str(step.get("semantic_kind") or "")
    if sk in ("MEASUREMENT", "FINAL_RESULT"):
        return (
            "Đại lượng được tính chính xác từ các đối tượng hình học đã dựng ở các bước trước.",
            ["exact_kernel:quantity"],
        )
    return (
        "Bước dựng kế thừa trực tiếp trạng thái hình học hợp lệ của bước liền trước.",
        [f"frame:{CANONICAL_COORDINATE_FRAME_ID}"],
    )


def enrich_construction_continuity(
    scene3d: dict[str, Any],
    *,
    trace: list[dict[str, Any]] | None = None,
) -> None:
    """Populate cumulative continuity fields and 5-part `step_summary` on `scene3d['formation']['steps']`."""
    steps = (scene3d.get("formation") or {}).get("steps") or []
    if not steps:
        return
    objects: dict[str, dict[str, Any]] = {o["id"]: o for o in scene3d.get("objects") or () if "id" in o}
    events_by_step: dict[int, list[dict[str, Any]]] = {}
    for ev in scene3d.get("events") or ():
        idx = ev.get("step_index")
        if isinstance(idx, int):
            events_by_step.setdefault(idx, []).append(ev)

    trace_certs: dict[str, list[str]] = {}
    for item in trace or ():
        st = item.get("step")
        obj = item.get("object")
        if st == "certify_answer" and obj:
            trace_certs.setdefault(f"kq_{obj}", []).append(f"certify_answer:{obj}")
        elif st == "certify_section_closure" and obj:
            trace_certs.setdefault(str(obj), []).append(f"certify_section_closure:{obj}")

    given_inputs = [
        f"{o.get('notation') or o['label']} = {o['value']}"
        for o in scene3d.get("objects") or ()
        if o.get("type") == "quantity"
        and o.get("origin") == "given"
        and o.get("value") is not None
        and "_" not in str(o.get("notation") or o.get("label") or "")
    ]

    prev_state: set[str] = set()
    prev_visible: set[str] = set()
    produced_by_step: list[set[str]] = []

    for idx, st in enumerate(steps):
        vis_list = list(st.get("visible_ids") or ())
        read_list = list(st.get("readout_ids") or ())
        focus_list = list(st.get("focus_ids") or ())
        curr_visible = set(vis_list)
        curr_state = curr_visible | set(read_list)
        order_key = {oid: i for i, oid in enumerate([*vis_list, *read_list])}

        created_ids = sorted(curr_state - prev_state, key=lambda x: order_key.get(x, 10**6))
        created_set = set(created_ids)
        retired_ids = sorted(prev_visible - curr_visible)

        step_evs = events_by_step.get(idx, [])
        raw_deps: list[str] = []
        for oid in created_ids:
            for d in (objects.get(oid) or {}).get("depends") or ():
                if d in prev_state and d not in created_set and d not in raw_deps:
                    raw_deps.append(d)
        for ev in step_evs:
            ev_obj = ev.get("object")
            if ev_obj and ev_obj in prev_state and ev_obj not in created_set and ev_obj not in raw_deps:
                raw_deps.append(ev_obj)
            for d in ev.get("depends") or ():
                if d in prev_state and d not in created_set and d not in raw_deps:
                    raw_deps.append(d)

        depends_on = list(raw_deps)
        reused_ids = list(raw_deps)
        highlighted_ids = [oid for oid in focus_list if oid in prev_state and oid not in created_set]

        preconditions = (
            [f"frame:{CANONICAL_COORDINATE_FRAME_ID}", "premises_verified"]
            if idx == 0
            else [f"constructed:{d}" for d in depends_on] or [f"state_inherited:step_{idx - 1}"]
        )

        created_objs = [objects[oid] for oid in created_ids if oid in objects]
        validity, v_refs = _step_validity(idx, st, step_evs, created_objs, objects)
        for oid in created_ids:
            for extra_ref in trace_certs.get(oid, ()):
                if extra_ref not in v_refs:
                    v_refs.append(extra_ref)

        what_text = _clean_text(st.get("learner_text") or (step_evs[0].get("learner_text") if step_evs else "Thực hiện bước dựng."))
        if idx == 0:
            inputs_text = given_inputs[:] if given_inputs else [_obj_ref_name(objects[oid]) for oid in created_ids if oid in objects][:6]
        else:
            inputs_text = [_obj_ref_name(objects[oid]) for oid in reused_ids if oid in objects]

        if created_objs:
            if len(created_objs) == 1 and created_objs[0].get("type") == "quantity":
                qo = created_objs[0]
                result_text = _clean_text(
                    (qo.get("formula") or {}).get("text")
                    or f"{_obj_ref_name(qo)} = {qo.get('value')}"
                )
            else:
                names = [_obj_ref_name(o) for o in created_objs[:6]]
                result_text = "Đã xác định: " + ", ".join(names) + "."
        else:
            result_text = what_text

        st["step_id"] = f"step_{idx}"
        st["coordinate_frame_id"] = CANONICAL_COORDINATE_FRAME_ID
        st["depends_on"] = depends_on
        st["preconditions"] = preconditions
        st["created_ids"] = created_ids
        st["reused_ids"] = reused_ids
        st["highlighted_ids"] = highlighted_ids
        st["retired_ids"] = retired_ids
        st["verification_refs"] = v_refs
        st["step_summary"] = {
            "what": what_text,
            "inputs": inputs_text,
            "validity": validity,
            "result": result_text,
            "next_use": [],
        }

        produced = set(created_ids)
        for ev in step_evs:
            if ev.get("action") == "EXTEND" and ev.get("object"):
                produced.add(str(ev["object"]))
        produced_by_step.append(produced)
        prev_state = curr_state
        prev_visible = curr_visible

    # Second pass: link each step's `next_use` to exact downstream consumer steps.
    total = len(steps)
    for idx, st in enumerate(steps):
        produced = produced_by_step[idx]
        uses: list[str] = []
        for j in range(idx + 1, total):
            later = steps[j]
            consumed = produced & (set(later.get("depends_on") or ()) | set(later.get("reused_ids") or ()))
            if consumed:
                target_txt = _clean_text(later.get("learner_text") or f"bước {j + 1}")
                uses.append(f"Bước {j + 1}: {target_txt}")
            if len(uses) >= 3:
                break
        if not uses:
            if st.get("semantic_kind") == "FINAL_RESULT" or idx == total - 1:
                uses = ["Là kết quả cần tìm ở bước kết luận của bài toán."]
            else:
                uses = ["Giữ trong mô hình 3D để quan sát và đối chiếu trực quan."]
        st["step_summary"]["next_use"] = uses


def _frac_vec(coords: Any) -> tuple[Fraction, Fraction, Fraction] | None:
    if not isinstance(coords, (list, tuple)) or len(coords) != 3:
        return None
    try:
        return (Fraction(coords[0]), Fraction(coords[1]), Fraction(coords[2]))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _point_on_plane_covector(
    pt: tuple[Fraction, Fraction, Fraction],
    p0: tuple[Fraction, Fraction, Fraction],
    normal: tuple[Fraction, Fraction, Fraction],
) -> bool:
    return sum(normal[i] * (pt[i] - p0[i]) for i in range(3)) == 0


def _point_on_line(
    pt: tuple[Fraction, Fraction, Fraction],
    l0: tuple[Fraction, Fraction, Fraction],
    direction: tuple[Fraction, Fraction, Fraction],
) -> bool:
    dx, dy, dz = pt[0] - l0[0], pt[1] - l0[1], pt[2] - l0[2]
    vx, vy, vz = direction
    return (dy * vz - dz * vy == 0) and (dz * vx - dx * vz == 0) and (dx * vy - dy * vx == 0)


def validate_construction_continuity(
    scene3d: dict[str, Any],
    *,
    trace: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Verify all 7 cumulative geometric continuity invariants (§IV.4). Empty list == valid."""
    issues: list[dict[str, str]] = []

    raw_objs = scene3d.get("objects")
    if not isinstance(raw_objs, list) or not raw_objs:
        return [{"code": "MISSING_OBJECT_PROVENANCE", "detail": "scene3d.objects is empty"}]

    # 1. Object identity stability (`OBJECT_IDENTITY_MUTATION`)
    objects: dict[str, dict[str, Any]] = {}
    point_notations: dict[str, str] = {}
    for o in raw_objs:
        oid = o.get("id")
        if not isinstance(oid, str) or not oid:
            issues.append({"code": "OBJECT_IDENTITY_MUTATION", "detail": "object with missing id"})
            continue
        if oid in objects:
            issues.append({"code": "OBJECT_IDENTITY_MUTATION", "detail": f"duplicate object id {oid!r}"})
            continue
        objects[oid] = o
        if o.get("type") == "point3" and isinstance(o.get("notation"), str) and o["notation"].strip():
            nt = o["notation"].strip()
            if nt in point_notations and point_notations[nt] != oid:
                issues.append({
                    "code": "OBJECT_IDENTITY_MUTATION",
                    "detail": f"point notation {nt!r} bound to both {point_notations[nt]!r} and {oid!r}",
                })
            point_notations[nt] = oid

    # 2. Coordinate chart & metric consistency (`GEOMETRIC_STEP_CONTRADICTION`)
    matrix = scene3d.get("chart_metric")
    if matrix is not None:
        try:
            if len(matrix) != 3 or any(len(r) != 3 for r in matrix):
                raise ValueError("bad metric shape")
            Metric(tuple(tuple(Fraction(v) for v in r) for r in matrix))
        except (TypeError, ValueError, ZeroDivisionError, GeometryError):
            issues.append({"code": "GEOMETRIC_STEP_CONTRADICTION", "detail": "chart_metric is not SPD"})

    for oid, o in objects.items():
        if o.get("type") == "segment3" and o.get("endpoint_ids"):
            eids = o["endpoint_ids"]
            if len(eids) == 2 and eids[0] in objects and eids[1] in objects:
                pa, pb = _frac_vec(o.get("point_a")), _frac_vec(o.get("point_b"))
                xa, xb = _frac_vec(objects[eids[0]].get("xyz")), _frac_vec(objects[eids[1]].get("xyz"))
                if pa is None or pb is None or xa is None or xb is None or {pa, pb} != {xa, xb} or pa == pb:
                    issues.append({"code": "GEOMETRIC_STEP_CONTRADICTION", "detail": f"segment {oid!r} endpoints mismatch"})
        if o.get("type") == "point3" and isinstance(o.get("perpendicular_witness"), dict):
            foot = _frac_vec(o["perpendicular_witness"].get("foot"))
            xyz = _frac_vec(o.get("xyz"))
            if foot is None or xyz is None or foot != xyz:
                issues.append({"code": "GEOMETRIC_STEP_CONTRADICTION", "detail": f"perpendicular witness foot mismatch on {oid!r}"})

    # 3. Object provenance (`MISSING_OBJECT_PROVENANCE`)
    for oid, o in objects.items():
        origin = o.get("origin")
        if origin not in ("free", "given") and not o.get("producer"):
            issues.append({"code": "MISSING_OBJECT_PROVENANCE", "detail": f"derived object {oid!r} has no producer"})
        for dep in o.get("depends") or ():
            if dep not in objects:
                issues.append({"code": "MISSING_OBJECT_PROVENANCE", "detail": f"object {oid!r} depends on missing {dep!r}"})

    steps = (scene3d.get("formation") or {}).get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append({"code": "GEOMETRIC_STEP_CONTRADICTION", "detail": "formation.steps is empty"})
        return issues

    events = scene3d.get("events") or []
    event_created_at: dict[str, int] = {}
    for ev in events:
        sidx = ev.get("step_index")
        if isinstance(sidx, int):
            for oid in (ev.get("object"), *(ev.get("objects") or ())):
                if isinstance(oid, str) and oid:
                    event_created_at.setdefault(oid, sidx)

    # 4 & 5. Step-by-step dependency ordering, frame continuity, and object persistence
    prev_state: set[str] = set()
    prev_visible: set[str] = set()
    ever_seen: set[str] = set()
    active_primary_vertices: set[str] = set()

    for idx, st in enumerate(steps):
        if st.get("step_index") != idx:
            issues.append({"code": "GEOMETRIC_STEP_CONTRADICTION", "detail": f"step {idx} has mismatched step_index"})
        frame_id = st.get("coordinate_frame_id")
        if frame_id != CANONICAL_COORDINATE_FRAME_ID:
            issues.append({
                "code": "GEOMETRIC_STEP_CONTRADICTION",
                "detail": f"step {idx} switched coordinate_frame_id to {frame_id!r}",
            })

        vis = set(st.get("visible_ids") or ())
        read = set(st.get("readout_ids") or ())
        curr_state = vis | read

        for oid in curr_state:
            if oid not in objects:
                issues.append({"code": "MISSING_OBJECT_PROVENANCE", "detail": f"step {idx} references unknown object {oid!r}"})

        # `depends_on`, `reused_ids`, `highlighted_ids` must already exist in cumulative state before this step
        for key in ("depends_on", "reused_ids", "highlighted_ids"):
            for dep in st.get(key) or ():
                if dep not in ever_seen:
                    issues.append({
                        "code": "DEPENDENCY_BEFORE_CREATION",
                        "detail": f"step {idx} {key} references {dep!r} before creation",
                    })

        newly_created = curr_state - ever_seen
        for oid in newly_created:
            o = objects.get(oid)
            if o is None:
                continue
            if idx > 0 and o.get("origin") not in ("free", "given") and oid not in event_created_at:
                issues.append({
                    "code": "MISSING_OBJECT_PROVENANCE",
                    "detail": f"object {oid!r} appeared at step {idx} without any construction event",
                })
            for dep in o.get("depends") or ():
                if dep in objects and objects[dep].get("render") != "non_visual" and dep not in ever_seen and dep not in curr_state:
                    issues.append({
                        "code": "DEPENDENCY_BEFORE_CREATION",
                        "detail": f"object {oid!r} at step {idx} depends on uncreated {dep!r}",
                    })

        # Unexplained disappearance check (`UNEXPLAINED_OBJECT_DISAPPEARANCE`)
        retired = set(st.get("retired_ids") or ())
        vanished = prev_visible - vis
        unexplained = vanished - retired
        if unexplained:
            issues.append({
                "code": "UNEXPLAINED_OBJECT_DISAPPEARANCE",
                "detail": f"step {idx} dropped visible objects {sorted(unexplained)} without retirement",
            })
        for oid in vanished:
            o = objects.get(oid)
            if o is not None and (o.get("type") in _PRIMARY_PERSISTENT_TYPES or oid in active_primary_vertices):
                issues.append({
                    "code": "UNEXPLAINED_OBJECT_DISAPPEARANCE",
                    "detail": f"step {idx} dropped persistent primary object {oid!r}",
                })

        for oid in vis:
            o = objects.get(oid)
            if o is not None and o.get("type") == "solid":
                active_primary_vertices.update(o.get("vertex_ids") or ())
            elif o is not None and o.get("type") == "curved_solid":
                active_primary_vertices.update(d for d in (o.get("depends") or ()) if (objects.get(d) or {}).get("type") == "point3")
        if idx == 0:
            active_primary_vertices.update(
                oid for oid in vis if (objects.get(oid) or {}).get("type") == "point3" and (objects.get(oid) or {}).get("origin") in ("free", "given")
            )

        # Measurement steps (`MEASUREMENT_USES_UNDETERMINED_OBJECT`)
        for qid in read:
            qo = objects.get(qid)
            if qo is None or qo.get("type") != "quantity" or qo.get("value") is None or qo.get("exact") is None:
                issues.append({
                    "code": "MEASUREMENT_USES_UNDETERMINED_OBJECT",
                    "detail": f"readout quantity {qid!r} at step {idx} has undetermined value/exact",
                })

        prev_state = curr_state
        prev_visible = vis
        ever_seen |= curr_state

    for ev in events:
        sk = ev.get("semantic_kind")
        if sk in ("MEASUREMENT", "FINAL_RESULT"):
            qid = ev.get("object")
            qo = objects.get(qid or "")
            if qo is None:
                issues.append({
                    "code": "MEASUREMENT_USES_UNDETERMINED_OBJECT",
                    "detail": f"measurement event for {qid!r} references missing object",
                })
                continue
            if sk == "FINAL_RESULT" or qo.get("type") == "quantity":
                if qo.get("type") != "quantity" or qo.get("value") is None or qo.get("exact") is None:
                    issues.append({
                        "code": "MEASUREMENT_USES_UNDETERMINED_OBJECT",
                        "detail": f"measurement event for {qid!r} references undetermined quantity",
                    })
                    continue
            elif qo.get("type") == "vector3" and _frac_vec(qo.get("xyz")) is None:
                issues.append({
                    "code": "MEASUREMENT_USES_UNDETERMINED_OBJECT",
                    "detail": f"vector assignment {qid!r} has undetermined xyz",
                })
                continue
            for dep in qo.get("depends") or ():
                do = objects.get(dep)
                if do is None or (do.get("render") != "non_visual" and dep not in ever_seen):
                    issues.append({
                        "code": "MEASUREMENT_USES_UNDETERMINED_OBJECT",
                        "detail": f"object {qid!r} depends on undetermined object {dep!r}",
                    })

    # 7. Exact section & intersection geometric incidence (`SECTION_OR_INTERSECTION_MISMATCH`)
    for oid, o in objects.items():
        otype = o.get("type")
        if otype == "section":
            poly = o.get("polygon") or []
            if o.get("closed") is not True or len(poly) < 3:
                issues.append({
                    "code": "SECTION_OR_INTERSECTION_MISMATCH",
                    "detail": f"section {oid!r} is open or has <3 vertices",
                })
                continue
            pts = [_frac_vec(v) for v in poly]
            if any(p is None for p in pts):
                issues.append({"code": "SECTION_OR_INTERSECTION_MISMATCH", "detail": f"section {oid!r} has invalid coordinates"})
                continue
            planes = [objects[d] for d in o.get("depends") or () if (objects.get(d) or {}).get("type") == "plane3"]
            solids = [objects[d] for d in o.get("depends") or () if (objects.get(d) or {}).get("type") == "solid"]
            for mp in planes:
                p0, nvec = _frac_vec(mp.get("point")), _frac_vec(mp.get("normal"))
                if p0 is None or nvec is None or nvec == (0, 0, 0):
                    issues.append({"code": "SECTION_OR_INTERSECTION_MISMATCH", "detail": f"cutting plane {mp['id']!r} degenerate"})
                    continue
                for pt in pts:
                    assert pt is not None
                    if not _point_on_plane_covector(pt, p0, nvec):
                        issues.append({
                            "code": "SECTION_OR_INTERSECTION_MISMATCH",
                            "detail": f"section {oid!r} vertex {pt} does not lie on cutting plane {mp['id']!r}",
                        })
                        break
            for sol in solids:
                sverts = [_frac_vec(v) for v in sol.get("vertices") or ()]
                if sverts and all(v is not None for v in sverts):
                    bounds = [(min(v[i] for v in sverts if v is not None), max(v[i] for v in sverts if v is not None)) for i in range(3)]
                    for pt in pts:
                        assert pt is not None
                        if any(not (bounds[i][0] <= pt[i] <= bounds[i][1]) for i in range(3)):
                            issues.append({
                                "code": "SECTION_OR_INTERSECTION_MISMATCH",
                                "detail": f"section {oid!r} vertex {pt} lies outside host solid {sol['id']!r} convex hull bounds",
                            })
                            break
        elif otype == "circle3" and o.get("producer") == "intersect_plane_curved":
            center = _frac_vec(o.get("center"))
            try:
                rsq = Fraction(o.get("radius_sq"))
            except (TypeError, ValueError, ZeroDivisionError):
                rsq = Fraction(0)
            if center is None or rsq <= 0:
                issues.append({"code": "SECTION_OR_INTERSECTION_MISMATCH", "detail": f"circle section {oid!r} non-positive radius"})
                continue
            for d in o.get("depends") or ():
                mp = objects.get(d)
                if mp and mp.get("type") == "plane3":
                    p0, nvec = _frac_vec(mp.get("point")), _frac_vec(mp.get("normal"))
                    if p0 is None or nvec is None or not _point_on_plane_covector(center, p0, nvec):
                        issues.append({
                            "code": "SECTION_OR_INTERSECTION_MISMATCH",
                            "detail": f"circle section {oid!r} center does not lie on plane {d!r}",
                        })
        elif otype == "point3" and o.get("producer") == "construct_point.intersect_line_plane":
            pt = _frac_vec(o.get("xyz"))
            if pt is None:
                issues.append({"code": "SECTION_OR_INTERSECTION_MISMATCH", "detail": f"intersection point {oid!r} missing xyz"})
                continue
            for d in o.get("depends") or ():
                do = objects.get(d)
                if do and do.get("type") == "plane3":
                    p0, nvec = _frac_vec(do.get("point")), _frac_vec(do.get("normal"))
                    if p0 is None or nvec is None or not _point_on_plane_covector(pt, p0, nvec):
                        issues.append({
                            "code": "SECTION_OR_INTERSECTION_MISMATCH",
                            "detail": f"intersection point {oid!r} off plane {d!r}",
                        })
                elif do and do.get("type") == "line3":
                    l0, dvec = _frac_vec(do.get("point")), _frac_vec(do.get("direction"))
                    if l0 is None or dvec is None or not _point_on_line(pt, l0, dvec):
                        issues.append({
                            "code": "SECTION_OR_INTERSECTION_MISMATCH",
                            "detail": f"intersection point {oid!r} off line {d!r}",
                        })

    return issues
