"""Independent Planning Oracle & Registry Contract Auditor (Continuation 11 §§4.1, 4.4, 7).

Evaluation/verification utility built strictly from `registry.py` (`FunctionSpec`, `PlanningContract`,
`doc_ke_hoach`, `kiem_nguon`) and Exact Geometry Kernel (`engine._Dung` + `SemanticProgramInterpreter`)
execution + Gram/affine postcondition checks. Zero imports from `planner.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from app.simulation.geometry import metric as _metric
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.validator import validate_semantic_program


def sub(a: tuple[Fraction, ...], b: tuple[Fraction, ...]) -> tuple[Fraction, Fraction, Fraction]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a: tuple[Fraction, ...], b: tuple[Fraction, ...]) -> Fraction:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: tuple[Fraction, ...], b: tuple[Fraction, ...]) -> tuple[Fraction, Fraction, Fraction]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def point_on_line(x: tuple[Fraction, ...], line: tuple[tuple[Fraction, ...], tuple[Fraction, ...]]) -> bool:
    return line[0] != line[1] and cross(sub(x, line[0]), sub(line[1], line[0])) == (0, 0, 0)


def point_on_plane(x: tuple[Fraction, ...], plane: tuple[tuple[Fraction, ...], tuple[Fraction, ...], tuple[Fraction, ...]]) -> bool:
    n = cross(sub(plane[1], plane[0]), sub(plane[2], plane[0]))
    return n != (0, 0, 0) and dot(sub(x, plane[0]), n) == 0

from app.simulation.geometry_functions import engine, registry
from app.simulation.geometry_functions.registry import (
    FunctionSpec,
    LoiGoi,
    PlanningContract,
    REGISTRY,
    TuChoi,
    doc_ke_hoach,
    planning_contracts,
)

UNSUPPORTED_PRIMITIVES: frozenset[str] = frozenset({
    "circumcenter",
    "incenter",
    "orthocenter",
    "angle_bisector_foot",
    "sphere_circumscribed_radius",
    "sphere_inscribed_radius",
    "locus_extremum",
})

UNSUPPORTED_EXACT_DOMAINS: frozenset[str] = frozenset({
    "transcendental_arccos_degree_sum",
    "curved_oblique_plane_section",
    "curved_point_plane_distance",
    "irrational_general_eigen_angle",
})

ORACLE_STEP_LIMIT = 8
ORACLE_CANDIDATE_LIMIT = 256


@dataclass(frozen=True)
class FunctionContractRecord:
    name: str
    kind: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    needs: tuple[tuple[str, ...], ...]
    effects: tuple[str, ...]
    object_types: tuple[str, ...]
    source_requirements: dict[str, Any]
    derived_dependencies: tuple[str, ...]
    computational_limitations: tuple[str, ...]
    verification_authority: str


@dataclass(frozen=True)
class OracleVerdict:
    classification: str
    plan_exists: bool | None
    min_extra_steps: int | None
    total_calls: int | None
    witness_functions: tuple[str, ...]
    preconditions_satisfied: bool
    has_ungrounded_object: bool
    has_dependency_cycle: bool
    kernel_confirmed: bool
    exact_answers: dict[str, str]
    explored_dag_candidates: int
    reason: str


def _infer_outputs(spec: FunctionSpec) -> tuple[str, ...]:
    if spec.name in ("pyramid", "regular_pyramid", "prism"):
        return ("PolyhedralSolid3D", "VertexSet")
    if spec.name == "curved_solid":
        return ("CurvedSolid3D",)
    if spec.name == "curved_subsolid":
        return ("CurvedSubsolid3D",)
    if spec.name in ("curved_section",):
        return ("CurvedSection2D",)
    if spec.name == "section":
        return ("PolygonSection3D",)
    if spec.name == "intersection_line":
        return ("Line3D",)
    if spec.kind == "construct":
        return ("Point3D",)
    if spec.kind == "fact":
        return ("GeometricConstraint",)
    if spec.kind == "ask":
        return ("ExactScalarMetric",)
    return ("EscapeRefusal",)


def _infer_preconditions(spec: FunctionSpec) -> tuple[str, ...]:
    pre: list[str] = ["acyclic_depends_on", "schema_valid_args"]
    if spec.kind == "construct":
        pre.append("distinct_non_degenerate_operands")
        if "intersect" in spec.name:
            pre.append("transversal_unique_intersection")
        if "projection" in spec.name:
            pre.append("gram_metric_determinable_on_target")
        if spec.name == "section":
            pre.extend(["three_non_collinear_plane_points", "strict_polyhedral_cut_ge_3_vertices"])
    elif spec.kind == "ask":
        pre.extend(["solid_coordinates_determinable_up_to_isometry", "target_operands_constructed"])
    elif spec.kind == "fact":
        pre.append("compatible_with_declared_topology_and_metric_constraints")
    return tuple(pre)


def _infer_postconditions(spec: FunctionSpec) -> tuple[str, ...]:
    if spec.name == "section":
        return ("cyclic_coplanar_convex_polygon_on_boundary", "section_certificate_verified")
    if spec.kind == "construct":
        return ("exact_affine_or_gram_coordinates", "independent_witness_verified")
    if spec.kind == "ask":
        return ("exact_fraction_or_quadratic_radical_value", "gram_formula_cross_checked")
    if spec.kind == "fact":
        return ("metric_or_incidence_constraint_satisfied",)
    return ("explicit_out_of_scope_refusal",)


def _contract_summary(c: PlanningContract) -> tuple[tuple[str, ...], str]:
    return tuple(f"{t.kind}:{','.join(t.operands)}" for t in c.inputs), f"{c.effect.kind}:{c.descriptor or c.source_policy}"


def audit_registry_contracts() -> dict[str, Any]:
    """Machine-verifiable §4.1 audit of every registered FunctionSpec and 6 cross-cutting composition axes."""
    records: list[FunctionContractRecord] = []
    by_effect_kind: dict[str, list[str]] = {}
    for name, spec in sorted(REGISTRY.items()):
        in_fields = tuple(spec.args.model_fields.keys())
        pcs = planning_contracts(spec)
        needs_list: list[tuple[str, ...]] = []
        effects_list: list[str] = []
        phrases: list[str] = []
        for pc in pcs:
            nds, eff = _contract_summary(pc)
            needs_list.append(nds)
            effects_list.append(eff)
            by_effect_kind.setdefault(pc.effect.kind, []).append(name)
            if pc.phrase:
                phrases.append(pc.phrase if isinstance(pc.phrase, str) else "|".join(pc.phrase))
        obj_types = sorted({spec.kind, *_infer_outputs(spec)})
        lim: list[str] = ["exact_rational_or_quadratic_radical_only"]
        if "curved" in name or name in ("sphere_tangent_plane", "ask_lateral_area", "ask_surface_area", "ask_radius"):
            lim.append("curved_solid_canonical_relations_only_no_arbitrary_oblique_plane_cut")
        if name in ("ask_angle_lines", "ask_angle_line_plane", "ask_angle_plane_plane"):
            lim.append("returns_exact_cos2_or_sin2_not_transcendental_arccos_float")
        rec = FunctionContractRecord(
            name=name,
            kind=spec.kind,
            inputs=in_fields,
            outputs=_infer_outputs(spec),
            preconditions=_infer_preconditions(spec),
            postconditions=_infer_postconditions(spec),
            needs=tuple(needs_list),
            effects=tuple(effects_list),
            object_types=tuple(obj_types),
            source_requirements={
                "keywords_groups": len(spec.keywords),
                "value_fields": list(spec.value_fields),
                "plane_fields": list(spec.plane_fields),
                "segment_fields": list(spec.segment_fields),
                "point_fields": list(spec.point_fields),
                "auxiliary_only": spec.auxiliary_only,
                "provider_offered": spec.provider_offered,
                "has_descriptor_phrase": bool(phrases),
            },
            derived_dependencies=("explicit_depends_on_dag",),
            computational_limitations=tuple(lim),
            verification_authority="SourceGate(registry.kiem_nguon)+ExactKernel(engine.dung_tu_loi_goi)",
        )
        records.append(rec)

    multi_producers = {
        eff_kind: sorted(set(fns))
        for eff_kind, fns in sorted(by_effect_kind.items())
        if len(set(fns)) >= 2
    }
    point_producers = sorted(
        n for n, s in REGISTRY.items()
        if s.kind == "construct" and n not in ("pyramid", "regular_pyramid", "prism", "section", "intersection_line", "curved_solid", "curved_section", "curved_subsolid")
    )
    multi_step_consumers = sorted(
        n for n, s in REGISTRY.items()
        if (s.kind == "ask" and n not in ("ask_volume", "ask_curved_volume", "ask_lateral_area", "ask_surface_area", "ask_radius"))
        or n in ("section", "intersection_line", "translate_point")
    )
    cross_topology = {
        "polyhedral_agnostic": sorted(
            n for n, s in REGISTRY.items()
            if n not in ("pyramid", "regular_pyramid", "prism", "altitude", "curved_solid", "sphere_tangent_plane",
                         "ask_curved_volume", "ask_lateral_area", "ask_surface_area", "ask_radius", "curved_section",
                         "curved_subsolid", "ask_curved_section_area", "ask_curved_section_radius",
                         "ask_curved_volume_ratio", "ask_curved_residual_volume", "unsupported")
        ),
        "pyramid_specific": ["pyramid", "regular_pyramid", "altitude"],
        "prism_specific": ["prism"],
        "curved_isolated": sorted(
            n for n in REGISTRY
            if "curved" in n or n in ("sphere_tangent_plane", "ask_lateral_area", "ask_surface_area", "ask_radius")
        ),
    }
    return {
        "registry_version": registry.REGISTRY_VERSION,
        "total_functions": len(records),
        "functions": [
            {
                "name": r.name,
                "kind": r.kind,
                "inputs": list(r.inputs),
                "outputs": list(r.outputs),
                "preconditions": list(r.preconditions),
                "postconditions": list(r.postconditions),
                "needs": [list(x) for x in r.needs],
                "effects": list(r.effects),
                "object_types": list(r.object_types),
                "source_requirements": r.source_requirements,
                "derived_dependencies": list(r.derived_dependencies),
                "computational_limitations": list(r.computational_limitations),
                "verification_authority": r.verification_authority,
            }
            for r in records
        ],
        "cross_cutting": {
            "multi_producer_effects": {
                **multi_producers,
                "Point3D_construct_producers": point_producers,
            },
            "multi_step_intermediate_consumers": multi_step_consumers,
            "reusable_intermediate_producers": sorted([*point_producers, "intersection_line", "section"]),
            "shared_dependency_multi_goal_pairs": [
                ["section", "ask_section_area"],
                ["ask_length", "ask_distance_point_plane"],
                ["ask_section_area", "ask_distance_point_plane"],
                ["ask_angle_lines", "ask_length"],
            ],
            "cross_topology_composability": cross_topology,
            "invalidating_constraints": [
                "skew_or_parallel_lines_for_intersect_line_line",
                "line_parallel_or_in_plane_for_intersect_line_plane",
                "plane_coincides_with_face_or_misses_solid_PLANE_DOES_NOT_CUT",
                "collinear_three_point_plane_definition",
                "contradictory_shape_class_claim_INCONSISTENT_FACTS",
                "underdetermined_metric_degree_of_freedom_UNDERDETERMINED_POINT",
                "role_swapped_or_ungrounded_source_span_SOURCE_MISMATCH",
            ],
        },
    }


def verify_point_postcondition(
    kind: str,
    out_label: str,
    spec: dict[str, Any],
    pts: dict[str, tuple[Fraction, Fraction, Fraction]],
    gram: Any | None = None,
) -> bool:
    """Independent mathematical witness check on exact 3D coordinates / Gram form."""
    if out_label not in pts:
        return False
    x = pts[out_label]
    if kind == "midpoint":
        a, b = pts[spec["segment"][0]], pts[spec["segment"][1]]
        return a != b and all(2 * x[i] == a[i] + b[i] for i in range(3))
    if kind == "centroid":
        a, b, c = (pts[p] for p in spec["polygon"])
        return cross(sub(b, a), sub(c, a)) != (0, 0, 0) and all(3 * x[i] == a[i] + b[i] + c[i] for i in range(3))
    if kind == "intersect_line_line":
        a0, a1 = pts[spec["line1"][0]], pts[spec["line1"][1]]
        b0, b1 = pts[spec["line2"][0]], pts[spec["line2"][1]]
        return cross(sub(a1, a0), sub(b1, b0)) != (0, 0, 0) and point_on_line(x, (a0, a1)) and point_on_line(x, (b0, b1))
    if kind == "intersect_line_plane":
        l0, l1 = pts[spec["line"][0]], pts[spec["line"][1]]
        q0, q1, q2 = pts[spec["plane"][0]], pts[spec["plane"][1]], pts[spec["plane"][2]]
        n = cross(sub(q1, q0), sub(q2, q0))
        return n != (0, 0, 0) and dot(sub(l1, l0), n) != 0 and point_on_line(x, (l0, l1)) and point_on_plane(x, (q0, q1, q2))
    if kind == "orthogonal_projection_line":
        p_ref = spec["point"] if isinstance(spec["point"], str) else spec.get("_resolved_point", "")
        if p_ref not in pts:
            return False
        p, l0, l1 = pts[p_ref], pts[spec["line"][0]], pts[spec["line"][1]]
        u, xp = sub(l1, l0), sub(p, x)
        ip = (lambda v1, v2: gram(v1, v2)) if gram is not None else dot
        return l0 != l1 and point_on_line(x, (l0, l1)) and ip(xp, u) == 0
    if kind == "orthogonal_projection":
        p_ref = spec["point"] if isinstance(spec["point"], str) else spec.get("_resolved_point", "")
        if p_ref not in pts:
            return False
        p = pts[p_ref]
        q0, q1, q2 = pts[spec["plane"][0]], pts[spec["plane"][1]], pts[spec["plane"][2]]
        u, v, xp = sub(q1, q0), sub(q2, q0), sub(p, x)
        ip = (lambda v1, v2: gram(v1, v2)) if gram is not None else dot
        return cross(u, v) != (0, 0, 0) and point_on_plane(x, (q0, q1, q2)) and ip(xp, u) == 0 and ip(xp, v) == 0
    return True


def _execute_raw_calls_in_kernel(problem_text: str, raw_calls: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], Any]:
    """Validate DAG via `doc_ke_hoach` and execute directly in `_Dung` + `SemanticProgramInterpreter`."""
    calls: tuple[LoiGoi, ...] = doc_ke_hoach({"calls": raw_calls})
    dung = engine._Dung(calls, problem_text, None)
    dung.thu_khoi()
    dung.bo_cuc_day()
    dung.giai_phu_thuoc()
    dung.chon_ba_mat([])
    dung.kiem()
    program, hoi = dung.bien_dich()
    vr = validate_semantic_program(program)
    if not vr.ok:
        raise TuChoi("ENGINE_IR_INVALID", str(vr.error))
    g_metric = dung.metric()
    try:
        with _metric.using(g_metric):
            ket = SemanticProgramInterpreter().execute(vr.spec)
    except Exception as exc:  # noqa: BLE001
        if getattr(exc, "code", None) in engine._MA_THIET_DIEN_SUY_BIEN:
            raise TuChoi(exc.code, str(exc)) from None
        raise TuChoi("ENGINE_EXECUTION_FAILED", f"{type(exc).__name__}: {exc}") from None
    fm = ket.final_memory
    if any(not fm[t].is_closed for t in dung.sections):
        raise TuChoi("SECTION_EMPTY", "mặt cắt không tạo thiết diện đóng")
    dung.kiem_chung_chi_thiet_dien(fm, hoi)
    answers = {cid: engine.dinh_dang(fm[var]) for cid, var in hoi.items() if var in fm}
    return dict(dung.pts), answers, dung.g


def verify_reachability_oracle(
    *,
    source_text: str,
    base_calls: list[dict[str, Any]],
    goals: list[dict[str, Any]],
    solid_vertices: list[str] | None = None,
    max_extra_steps: int = ORACLE_STEP_LIMIT,
    max_candidates: int = ORACLE_CANDIDATE_LIMIT,
    require_source_gate: bool = False,
) -> OracleVerdict:
    """Check finite-domain plan existence from Registry specs + Exact Geometry Kernel execution."""
    if max_extra_steps > ORACLE_STEP_LIMIT or max_candidates > ORACLE_CANDIDATE_LIMIT:
        return OracleVerdict(
            classification="NOT_ESTABLISHED",
            plan_exists=None,
            min_extra_steps=None,
            total_calls=None,
            witness_functions=(),
            preconditions_satisfied=False,
            has_ungrounded_object=False,
            has_dependency_cycle=False,
            kernel_confirmed=False,
            exact_answers={},
            explored_dag_candidates=0,
            reason="requested bounds exceed finite oracle domain",
        )

    for g in goals:
        if g.get("domain") in UNSUPPORTED_EXACT_DOMAINS:
            return OracleVerdict(
                classification="UNSUPPORTED_EXACT_DOMAIN",
                plan_exists=False,
                min_extra_steps=None,
                total_calls=None,
                witness_functions=(),
                preconditions_satisfied=False,
                has_ungrounded_object=False,
                has_dependency_cycle=False,
                kernel_confirmed=False,
                exact_answers={},
                explored_dag_candidates=1,
                reason=f"goal domain {g['domain']!r} outside exact rational/quadratic-radical kernel",
            )
        if g.get("kind") in UNSUPPORTED_PRIMITIVES:
            return OracleVerdict(
                classification="MISSING_PRIMITIVE",
                plan_exists=False,
                min_extra_steps=None,
                total_calls=None,
                witness_functions=(),
                preconditions_satisfied=False,
                has_ungrounded_object=False,
                has_dependency_cycle=False,
                kernel_confirmed=False,
                exact_answers={},
                explored_dag_candidates=1,
                reason=f"primitive {g['kind']!r} not in REGISTRY",
            )

    aux_pool = [f"X{i}" for i in range(1, 20)]
    used_labels: set[str] = set(solid_vertices or [])
    known_label_call: dict[str, str] = {}
    solid_call_id = base_calls[0]["id"] if base_calls else "c1"
    for c in base_calls:
        for k_arg in ("apex", "point", "image", "foot", "vertex"):
            v = c["args"].get(k_arg)
            if isinstance(v, str):
                used_labels.add(v)
                if c["fn"] in ("midpoint", "centroid", "divide_segment", "intersect_line_line", "intersect_line_plane",
                               "orthogonal_projection", "orthogonal_projection_line"):
                    known_label_call[v] = c["id"]
        for k_list in ("base", "bottom", "top", "polygon", "segment", "line", "line1", "line2", "plane"):
            for v in c["args"].get(k_list) or ():
                if isinstance(v, str):
                    used_labels.add(v)

    def fresh_label() -> str:
        lbl = next(x for x in aux_pool if x not in used_labels)
        used_labels.add(lbl)
        return lbl

    extra_calls: list[dict[str, Any]] = []
    point_memo: dict[str, tuple[str, str]] = {}
    plane_memo: dict[str, tuple[list[str], list[str]]] = {}
    point_checks: list[tuple[str, str, dict[str, Any]]] = []
    counter = [0]
    explored = 0

    def mk_call(fn: str, args: dict[str, Any], deps: list[str]) -> str:
        counter[0] += 1
        cid = f"orc_{counter[0]}"
        extra_calls.append({
            "id": cid,
            "fn": fn,
            "args": args,
            "source": {"quote": source_text[:80] if source_text else "oracle"},
            "depends_on": sorted(set(deps)),
        })
        return cid

    def ensure_point(pspec: str | dict[str, Any]) -> tuple[str, str | None, str | None]:
        nonlocal explored
        explored += 1
        if isinstance(pspec, str):
            return pspec, known_label_call.get(pspec), None
        key = repr(pspec)
        if key in point_memo:
            lbl, cid = point_memo[key]
            return lbl, cid, None
        kind = pspec["kind"]
        if kind in UNSUPPORTED_PRIMITIVES:
            return "", None, "MISSING_PRIMITIVE"
        lbl = fresh_label()
        if kind == "midpoint":
            seg = list(pspec["segment"])
            deps = [solid_call_id, *(known_label_call[x] for x in seg if x in known_label_call)]
            cid = mk_call("midpoint", {"point": lbl, "segment": seg}, deps)
            spec_copy = dict(pspec)
        elif kind == "centroid":
            poly = list(pspec["polygon"])
            deps = [solid_call_id, *(known_label_call[x] for x in poly if x in known_label_call)]
            cid = mk_call("centroid", {"point": lbl, "polygon": poly}, deps)
            spec_copy = dict(pspec)
        elif kind == "intersect_line_line":
            l1, l2 = list(pspec["line1"]), list(pspec["line2"])
            deps = [solid_call_id, *(known_label_call[x] for x in [*l1, *l2] if x in known_label_call)]
            cid = mk_call("intersect_line_line", {"point": lbl, "line1": l1, "line2": l2}, deps)
            spec_copy = dict(pspec)
        elif kind == "intersect_line_plane":
            ln, pl = list(pspec["line"]), list(pspec["plane"])
            deps = [solid_call_id, *(known_label_call[x] for x in [*ln, *pl] if x in known_label_call)]
            cid = mk_call("intersect_line_plane", {"point": lbl, "line": ln, "plane": pl[:3]}, deps)
            spec_copy = dict(pspec)
        elif kind == "orthogonal_projection_line":
            sub_lbl, sub_cid, err = ensure_point(pspec["point"])
            if err:
                return "", None, err
            ln = list(pspec["line"])
            deps = [solid_call_id, *([sub_cid] if sub_cid else []), *(known_label_call[x] for x in ln if x in known_label_call)]
            cid = mk_call("orthogonal_projection_line", {"point": sub_lbl, "line": ln, "image": lbl}, deps)
            spec_copy = {**pspec, "_resolved_point": sub_lbl}
        elif kind == "orthogonal_projection":
            sub_lbl, sub_cid, err = ensure_point(pspec["point"])
            if err:
                return "", None, err
            pl = list(pspec["plane"])
            deps = [solid_call_id, *([sub_cid] if sub_cid else []), *(known_label_call[x] for x in pl if x in known_label_call)]
            cid = mk_call("orthogonal_projection", {"point": sub_lbl, "plane": pl[:3], "image": lbl}, deps)
            spec_copy = {**pspec, "_resolved_point": sub_lbl}
        else:
            return "", None, "MISSING_PRIMITIVE"
        known_label_call[lbl] = cid
        point_memo[key] = (lbl, cid)
        point_checks.append((kind, lbl, spec_copy))
        return lbl, cid, None

    def ensure_auxiliary_plane(pl_spec: dict[str, Any]) -> tuple[list[str], list[str], str | None]:
        nonlocal explored
        explored += 1
        key = repr(pl_spec)
        if key in plane_memo:
            pts3, deps = plane_memo[key]
            return pts3, deps, None
        m_lbl, m_cid, err = ensure_point(pl_spec["through"])
        if err:
            return [], [], err
        base_deps = [solid_call_id, *([m_cid] if m_cid else [])]
        rel = pl_spec["relation"]
        if rel == "parallel_plane":
            ref = list(pl_spec["target_plane"])
            x1, x2 = fresh_label(), fresh_label()
            c1 = mk_call("translate_point", {"point": m_lbl, "vector": [ref[0], ref[1]], "image": x1}, base_deps)
            c2 = mk_call("translate_point", {"point": m_lbl, "vector": [ref[0], ref[2]], "image": x2}, base_deps)
            res = ([m_lbl, x1, x2], [*base_deps, c1, c2])
            plane_memo[key] = res
            return res[0], res[1], None
        if rel == "perpendicular_line":
            ln = list(pl_spec["target_line"])
            anchors = list(pl_spec["anchors"])[:2]
            ln_deps = [known_label_call[x] for x in ln if x in known_label_call]
            f1, f2, x1, x2 = fresh_label(), fresh_label(), fresh_label(), fresh_label()
            cf1 = mk_call("orthogonal_projection_line", {"point": anchors[0], "line": ln, "image": f1}, [*base_deps, *ln_deps])
            cf2 = mk_call("orthogonal_projection_line", {"point": anchors[1], "line": ln, "image": f2}, [*base_deps, *ln_deps])
            cx1 = mk_call("translate_point", {"point": m_lbl, "vector": [f1, anchors[0]], "image": x1}, [*base_deps, cf1])
            cx2 = mk_call("translate_point", {"point": m_lbl, "vector": [f2, anchors[1]], "image": x2}, [*base_deps, cf2])
            res = ([m_lbl, x1, x2], [*base_deps, cx1, cx2])
            plane_memo[key] = res
            return res[0], res[1], None
        return [], [], "MISSING_PRIMITIVE"

    for g in goals:
        explored += 1
        gkind = g["kind"]
        if gkind in ("section", "ask_section_area"):
            pts3, p_deps, err = ensure_auxiliary_plane(g["plane_spec"])
            if err:
                return OracleVerdict(err, False, None, None, (), False, False, False, False, {}, explored, f"missing primitive for {gkind}")
            mk_call(gkind, {"solid": g["solid"], "plane": pts3}, p_deps)
        elif gkind == "ask_length":
            a_lbl, a_cid, e1 = ensure_point(g["a"])
            b_lbl, b_cid, e2 = ensure_point(g["b"])
            if e1 or e2:
                return OracleVerdict(e1 or e2 or "MISSING_PRIMITIVE", False, None, None, (), False, False, False, False, {}, explored, "missing point primitive")
            mk_call("ask_length", {"segment": [a_lbl, b_lbl]}, [x for x in (solid_call_id, a_cid, b_cid) if x])
        elif gkind == "ask_distance_point_plane":
            p_lbl, p_cid, err = ensure_point(g["point"])
            if err:
                return OracleVerdict(err, False, None, None, (), False, False, False, False, {}, explored, "missing point primitive")
            mk_call("ask_distance_point_plane", {"point": p_lbl, "plane": list(g["plane"])[:3]}, [x for x in (solid_call_id, p_cid) if x])
        elif gkind == "ask_angle_line_plane":
            a_lbl, a_cid, e1 = ensure_point(g["line"][0])
            b_lbl, b_cid, e2 = ensure_point(g["line"][1])
            if e1 or e2:
                return OracleVerdict(e1 or e2 or "MISSING_PRIMITIVE", False, None, None, (), False, False, False, False, {}, explored, "missing point primitive")
            mk_call("ask_angle_line_plane", {"line": [a_lbl, b_lbl], "plane": list(g["plane"])[:3]}, [x for x in (solid_call_id, a_cid, b_cid) if x])
        elif gkind == "ask_angle_lines":
            a0, c0, e0 = ensure_point(g["line1"][0])
            a1, c1, e1 = ensure_point(g["line1"][1])
            b0, c2, e2 = ensure_point(g["line2"][0])
            b1, c3, e3 = ensure_point(g["line2"][1])
            if e0 or e1 or e2 or e3:
                return OracleVerdict(e0 or e1 or e2 or e3 or "MISSING_PRIMITIVE", False, None, None, (), False, False, False, False, {}, explored, "missing point primitive")
            mk_call("ask_angle_lines", {"line1": [a0, a1], "line2": [b0, b1]}, [x for x in (solid_call_id, c0, c1, c2, c3) if x])
        elif gkind == "ask_area":
            poly_lbls: list[str] = []
            deps_s = [solid_call_id]
            for pv in g["polygon"]:
                plb, pcid, perr = ensure_point(pv)
                if perr:
                    return OracleVerdict(perr, False, None, None, (), False, False, False, False, {}, explored, "missing point primitive")
                poly_lbls.append(plb)
                if pcid:
                    deps_s.append(pcid)
            mk_call("ask_area", {"polygon": poly_lbls}, deps_s)
        else:
            return OracleVerdict("MISSING_PRIMITIVE", False, None, None, (), False, False, False, False, {}, explored, f"goal {gkind!r} unsupported")

    if len(extra_calls) > max_extra_steps + len(goals):
        return OracleVerdict(
            classification="NOT_ESTABLISHED",
            plan_exists=None,
            min_extra_steps=len(extra_calls),
            total_calls=len(base_calls) + len(extra_calls),
            witness_functions=tuple(c["fn"] for c in extra_calls),
            preconditions_satisfied=False,
            has_ungrounded_object=False,
            has_dependency_cycle=False,
            kernel_confirmed=False,
            exact_answers={},
            explored_dag_candidates=explored,
            reason=f"witness needs {len(extra_calls)} extra calls beyond bound {max_extra_steps + len(goals)}",
        )

    all_raw = [*base_calls, *extra_calls]
    try:
        typed_calls = doc_ke_hoach({"calls": all_raw})
    except TuChoi as exc:
        return OracleVerdict(
            classification="NOT_ESTABLISHED",
            plan_exists=False,
            min_extra_steps=None,
            total_calls=None,
            witness_functions=tuple(c["fn"] for c in extra_calls),
            preconditions_satisfied=False,
            has_ungrounded_object=False,
            has_dependency_cycle=(exc.code == "DEPENDENCY_CYCLE"),
            kernel_confirmed=False,
            exact_answers={},
            explored_dag_candidates=explored,
            reason=f"{exc.code}: {exc.reason}",
        )

    if require_source_gate:
        try:
            registry.kiem_nguon(typed_calls, source_text, (), ())
        except TuChoi as exc:
            return OracleVerdict(
                classification="SOURCE_UNVERIFIED",
                plan_exists=False,
                min_extra_steps=len(extra_calls),
                total_calls=len(all_raw),
                witness_functions=tuple(c["fn"] for c in extra_calls),
                preconditions_satisfied=False,
                has_ungrounded_object=True,
                has_dependency_cycle=False,
                kernel_confirmed=False,
                exact_answers={},
                explored_dag_candidates=explored,
                reason=f"{exc.code}: {exc.reason}",
            )

    try:
        pts, answers, gram = _execute_raw_calls_in_kernel(source_text, all_raw)
    except TuChoi as exc:
        if "UNDERDETERMINED" in exc.code or exc.code in ("MISSING_DIMENSION", "MISSING_METRIC", "INSUFFICIENT_FACTS", "FIGURE_NOT_UNIQUE", "FOOT_NOT_DETERMINED"):
            cls = "INSUFFICIENT_GIVENS"
        elif exc.code == "INCONSISTENT_FACTS":
            cls = "INCONSISTENT_GIVENS"
        else:
            cls = "UNSUPPORTED_EXACT_DOMAIN"
        return OracleVerdict(
            classification=cls,
            plan_exists=False,
            min_extra_steps=None,
            total_calls=None,
            witness_functions=tuple(c["fn"] for c in extra_calls),
            preconditions_satisfied=False,
            has_ungrounded_object=False,
            has_dependency_cycle=False,
            kernel_confirmed=False,
            exact_answers={},
            explored_dag_candidates=explored,
            reason=f"{exc.code}: {exc.reason}",
        )

    for kind, lbl, pspec in point_checks:
        if not verify_point_postcondition(kind, lbl, pspec, pts, gram):
            return OracleVerdict(
                classification="NOT_ESTABLISHED",
                plan_exists=False,
                min_extra_steps=len(extra_calls),
                total_calls=len(all_raw),
                witness_functions=tuple(c["fn"] for c in extra_calls),
                preconditions_satisfied=False,
                has_ungrounded_object=False,
                has_dependency_cycle=False,
                kernel_confirmed=False,
                exact_answers={},
                explored_dag_candidates=explored,
                reason=f"postcondition failed for {kind}({lbl})",
            )

    return OracleVerdict(
        classification="REACHABLE",
        plan_exists=True,
        min_extra_steps=len(extra_calls),
        total_calls=len(all_raw),
        witness_functions=tuple(c["fn"] for c in extra_calls),
        preconditions_satisfied=True,
        has_ungrounded_object=False,
        has_dependency_cycle=False,
        kernel_confirmed=True,
        exact_answers=answers,
        explored_dag_candidates=explored,
        reason="exact kernel and independent postconditions confirmed",
    )
