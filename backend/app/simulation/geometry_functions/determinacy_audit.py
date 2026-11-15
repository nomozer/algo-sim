# -*- coding: utf-8 -*-
"""Exact structural, scale, and constructive counterexample determinacy audit (`mathematical-determinacy-audit/1`).

Mathematical soundness rule (Stage P0):
A problem is classified `PROVED_UNDERDETERMINED` (`MATHEMATICALLY_UNDERDETERMINED`) ONLY when all source clauses/values
were grounded and the system produces a machine-verified non-uniqueness certificate:
  1. `TWO_VALID_REALIZATIONS_DIVERGE`: Two Exact-Kernel-certified Euclidean realizations (passing `do_dai` consistency,
     `dung.kiem()` on 100% of verified calls, and `SemanticProgramInterpreter` execution with `kernel_check == True`)
     yield distinct exact goal values (or distinct similarity-invariant aspect-ratio spectra when no quantitative goal
     is asked).
  2. `HOMOTHETY_SCALE_DEGREE_POSITIVE`: Zero dimensional premises exist in the call graph (all constraints are
     homothety-invariant under X -> k*X, k > 0), at least one unit-scale realization is kernel-certified, and at least
     one asked goal has positive homogeneity degree (`BAC_DAI_LUONG[fn] > 0`).
  3. `EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS`: Explicit proven locus non-uniqueness (`PLANE_NOT_UNIQUE` pencil,
     `FIGURE_NOT_UNIQUE` unfixed apex projection with invariant volume, bare topological solid with zero constraints,
     or standalone curved solid missing an independent radius/height with zero unconsumed coupling constraints).
  4. `MULTI_ROOT_OR_MIRROR_BRANCH_DIVERGENCE`: Multiple valid mirror-sign / algebraic branches with distinct answers.

Constructive inability (`MISSING_DIMENSION`, `UNDERDETERMINED_POINT`, `FOOT_NOT_DETERMINED`) NEVER implies mathematical
underdeterminacy by itself: when unconsumed angle/metric/equality constraints remain or fewer than two diverging valid
realizations are certified, the audit returns `UNPROVED_DUE_TO_CAPABILITY_GAP` with an honest bounded scope note.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from typing import Any

from .registry import TuChoi, doc_ke_hoach

DETERMINACY_AUDIT_VERSION = "mathematical-determinacy-audit/1"

_BARE_TOPOLOGY_FNS = frozenset({"pyramid", "prism"})
_COUPLING_CONSTRAINT_FNS = frozenset({
    "segment_length",
    "equal_length",
    "segment_ratio",
    "polygon_area",
    "solid_volume",
    "height",
    "right_angle",
    "vertex_angle",
    "perpendicular_lines",
    "perpendicular_line_plane",
    "face_perpendicular_base",
    "line_plane_angle",
    "plane_plane_angle",
    "dihedral_angle",
    "line_line_angle",
    "parallel_lines",
    "parallel_line_plane",
    "parallel_planes",
    "altitude",
    "orthogonal_projection",
    "orthogonal_projection_line",
    "midpoint",
    "centroid",
    "divide_segment",
    "sphere_tangent_plane",
    "curved_solid",
})
MAX_COUNTEREXAMPLE_TRIALS = 8


def _canonical_line_sig(line_obj: Any) -> tuple[str, ...]:
    p = getattr(line_obj, "point", None)
    d = getattr(line_obj, "direction", None)
    if p is None or d is None:
        return (str(line_obj),)
    dv = (Fraction(d.x), Fraction(d.y), Fraction(d.z))
    pv = (Fraction(p.x), Fraction(p.y), Fraction(p.z))
    idx = next((i for i, c in enumerate(dv) if c != 0), None)
    if idx is None:
        return ("degenerate",)
    k = dv[idx]
    d_hat = tuple(c / k for c in dv)
    t0 = pv[idx]
    p_hat = tuple(pv[i] - t0 * d_hat[i] for i in range(3))
    return (*(str(x) for x in p_hat), *(str(x) for x in d_hat))


def _answer_signature(
    res: Any,
    has_asks: bool,
    has_sections: bool = False,
    intersection_line_ids: tuple[str, ...] = (),
) -> tuple:
    """Exact rational/radical signature of a kernel-certified realization."""
    if has_asks:
        exact = res.answer_exact or {}
        return tuple(
            (gid, str(v.get("coef")), int(v.get("dim") or 0), v.get("unit"))
            for gid, v in sorted(exact.items())
        )
    if has_sections:
        # Cross-section construction goal (`asks == []`, `section_calls != []`): compare combinatorial/incidence
        # section signature (solid, boundary entity IDs, vertex choices/edges, polygon vertex count), omitting
        # metric `area_squared` since `ask_section_area` was not asked.
        if res.section_certificates:
            return tuple(
                (
                    sc.get("solid"),
                    tuple(sc.get("boundary") or ()),
                    tuple(
                        (v.get("entity_id"), v.get("choice"), tuple(v.get("edge") or ()))
                        for v in (sc.get("vertices") or ())
                    ),
                    len(sc.get("vertices") or ()),
                )
                for sc in res.section_certificates
            )
        sec_trace = tuple(
            (st.get("step"), st.get("object"), tuple(st.get("edge") or ()), st.get("choice"))
            for st in (res.trace or ())
            if st.get("step") in ("certify_section_vertex", "certify_section_closure")
        )
        if sec_trace:
            return sec_trace
        return tuple(sorted(res.targets or ()))
    if intersection_line_ids and res.exec_result is not None:
        fm = getattr(res.exec_result, "final_memory", None) or {}
        line_sigs = tuple(
            (cid, _canonical_line_sig(fm[f"gt_{cid}"]))
            for cid in intersection_line_ids
            if f"gt_{cid}" in fm
        )
        if line_sigs:
            return line_sigs
    # Pure solid construction goal (`asks == []`, `sections == []`): compare similarity-invariant squared-distance spectrum.
    pts = res.points or {}
    G = res.chart_metric
    if G is None or len(pts) < 2:
        return ()
    m = G.g
    names = sorted(pts.keys())
    d2s: list[tuple[str, str, Fraction]] = []
    for i, a in enumerate(names):
        pa = pts[a]
        for b in names[i + 1:]:
            pb = pts[b]
            dx, dy, dz = pa[0] - pb[0], pa[1] - pb[1], pa[2] - pb[2]
            # Gram inner product in the chart metric (`Metric.g`)
            d2 = (
                dx * (m[0][0] * dx + m[0][1] * dy + m[0][2] * dz)
                + dy * (m[1][0] * dx + m[1][1] * dy + m[1][2] * dz)
                + dz * (m[2][0] * dx + m[2][1] * dy + m[2][2] * dz)
            )
            if d2 > 0:
                d2s.append((a, b, Fraction(d2)))
    if not d2s:
        return ()
    base_d2 = d2s[0][2]
    return tuple((a, b, str(d2 / base_d2)) for a, b, d2 in d2s)


def _collect_open_segment_representatives(calls: tuple, problem_text: str) -> list[frozenset[str]]:
    """Return one representative per `equal_length` class of base edges and diagonals not yet directly fixed."""
    from .engine import _Dung, _don_vi

    goc = next((c for c in calls if c.fn in ("pyramid", "regular_pyramid", "prism")), None)
    if goc is None:
        return []
    try:
        ky_hieu = _don_vi(calls)
        probe = _Dung(calls, problem_text, ky_hieu)
        probe.thu_khoi()
    except TuChoi:
        return []

    base = list(goc.args.base)
    k = len(base)
    candidates: list[tuple[str, str]] = [(base[i], base[(i + 1) % k]) for i in range(k)]
    if k == 4:
        candidates.extend([(base[0], base[2]), (base[1], base[3])])

    seen_classes: list[frozenset[frozenset[str]]] = []
    reps: list[frozenset[str]] = []
    for u, v in candidates:
        seg = frozenset((u, v))
        if probe.do_dai(u, v, _suy=False):
            continue
        eq_cls = frozenset(s for s, _ids in probe._lop_bang(seg))
        if any(seg in cls for cls in seen_classes):
            continue
        seen_classes.append(eq_cls)
        reps.append(seg)
    return reps


def _build_trial_specs(
    open_reps: list[frozenset[str]],
    *,
    scale_free_premises: bool,
) -> list[tuple[str, Fraction | None, Fraction | None, tuple[tuple[frozenset[str], Fraction], ...]]]:
    """Deterministic exact trial parameterizations `(label, _scale_unit, _free_h2_sample, _shape_units)`."""
    trials: list[tuple[str, Fraction | None, Fraction | None, tuple[tuple[frozenset[str], Fraction], ...]]] = []

    if scale_free_premises:
        # 1) Pure homothety scale trials
        trials.append(("scale=1", Fraction(1), None, ()))
        trials.append(("scale=2", Fraction(2), None, ()))
        # 2) Scale + open height trials (including homothetic pairs (1, 1) vs (2, 4) for 45°, (1, 3) vs (2, 12) for 60°)
        trials.append(("scale=1,h2=1", Fraction(1), Fraction(1), ()))
        trials.append(("scale=2,h2=4", Fraction(2), Fraction(4), ()))
        # 3) Scale + secondary open shape edge/diagonal trials (e.g. rectangle aspect ratio, rhombus diagonal)
        sec = open_reps[1:] if open_reps else []
        if sec:
            s0 = sec[0]
            trials.append(("scale=1,shape0=1", Fraction(1), None, ((s0, Fraction(1)),)))
            trials.append(("scale=1,shape0=2", Fraction(1), None, ((s0, Fraction(2)),)))
            trials.append(("scale=1,shape0=6/5,h2=1", Fraction(1), Fraction(1), ((s0, Fraction(6, 5)),)))
            trials.append(("scale=1,shape0=10/13,h2=1", Fraction(1), Fraction(1), ((s0, Fraction(10, 13)),)))
        else:
            trials.append(("scale=1,h2=3", Fraction(1), Fraction(3), ()))
            trials.append(("scale=2,h2=12", Fraction(2), Fraction(12), ()))
            trials.append(("scale=1,h2=1/3", Fraction(1), Fraction(1, 3), ()))
            trials.append(("scale=2,h2=4/3", Fraction(2), Fraction(4, 3), ()))
    else:
        # 1) Open height trials (base already fixed, apex height open)
        trials.append(("h2=1", None, Fraction(1), ()))
        trials.append(("h2=4", None, Fraction(4), ()))
        # 2) First open base segment/diagonal trials (e.g. uncoupled base vs apex, missing rectangle side, rhombus/isosceles)
        if open_reps:
            s0 = open_reps[0]
            trials.append(("shape0=1", None, None, ((s0, Fraction(1)),)))
            trials.append(("shape0=2", None, None, ((s0, Fraction(2)),)))
            trials.append(("shape0=6/5", None, None, ((s0, Fraction(6, 5)),)))
            trials.append(("shape0=10/13", None, None, ((s0, Fraction(10, 13)),)))
        if len(open_reps) >= 2 and len(trials) < MAX_COUNTEREXAMPLE_TRIALS:
            s0, s1 = open_reps[0], open_reps[1]
            trials.append(("shape0=1,shape1=6/5", None, None, ((s0, Fraction(1)), (s1, Fraction(6, 5)))))
            trials.append(("shape0=1,shape1=10/13", None, None, ((s0, Fraction(1)), (s1, Fraction(10, 13)))))

    return trials[:MAX_COUNTEREXAMPLE_TRIALS]


def audit_determinacy(
    problem_text: str,
    plan: Any,
    auxiliary: tuple[dict, ...] = (),
    read_quotes: tuple[str, ...] = (),
    refused_result: Any = None,
) -> dict[str, Any]:
    """Audit whether a refused plan is machine-certified `PROVED_UNDERDETERMINED` or `UNPROVED_DUE_TO_CAPABILITY_GAP`."""
    from .engine import BAC_DAI_LUONG, _SCALE_FREE_VALUED, _dung_mot_nhanh, _gia_tri_so

    code = getattr(refused_result, "code", None) or ""
    details = getattr(refused_result, "details", None) or {}
    consumed_ids = set(details.get("consumed_call_ids") or ())

    try:
        calls = doc_ke_hoach(plan)
    except TuChoi:
        return {
            "schema_version": DETERMINACY_AUDIT_VERSION,
            "status": "UNPROVED_DUE_TO_CAPABILITY_GAP",
            "witness_kind": "PLAN_DECODE_FAILED",
            "terminal_code": code,
            "unconsumed_constraint_ids": [],
            "counterexample_models": [],
            "trials_executed": 0,
            "scope_note": "Không giải mã được danh sách lời gọi để kiểm chứng tính xác định.",
        }

    ask_calls = [c for c in calls if c.fn.startswith("ask_")]
    section_calls = [c for c in calls if c.fn in ("section", "curved_section")]
    intersection_line_ids = tuple(sorted(c.id for c in calls if c.fn == "intersection_line"))
    non_ask_calls = [c for c in calls if not c.fn.startswith("ask_")]
    unconsumed_ids = sorted(
        c.id for c in non_ask_calls if c.fn not in _BARE_TOPOLOGY_FNS and c.id not in consumed_ids
    )
    unconsumed_coupling_ids = sorted(
        c.id for c in non_ask_calls if c.fn in _COUPLING_CONSTRAINT_FNS and c.id not in consumed_ids
    )
    dimensional_ids = sorted(
        c.id
        for c in non_ask_calls
        if c.fn not in _SCALE_FREE_VALUED and any(_gia_tri_so(v) for v in c.args.model_dump().values())
    )
    positive_deg_goals = sorted(c.id for c in ask_calls if BAC_DAI_LUONG.get(c.fn, 0) > 0)

    # 1. Explicit planner/locus non-uniqueness certificates
    if code in ("PLANE_NOT_UNIQUE", "FIGURE_NOT_UNIQUE"):
        return {
            "schema_version": DETERMINACY_AUDIT_VERSION,
            "status": "PROVED_UNDERDETERMINED",
            "witness_kind": "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS",
            "terminal_code": code,
            "unconsumed_constraint_ids": unconsumed_ids,
            "dimensional_premise_ids": dimensional_ids,
            "positive_degree_goal_ids": positive_deg_goals,
            "counterexample_models": [],
            "trials_executed": 0,
            "scope_note": "Các ràng buộc xác định một họ vô số mặt phẳng hoặc vị trí đỉnh tự do trên quỹ tích.",
        }

    # Bare topological solid declaration with zero geometric constraints
    if code in ("MISSING_DIMENSION", "UNDERDETERMINED_POINT", "FOOT_NOT_DETERMINED") and not unconsumed_ids and not consumed_ids:
        return {
            "schema_version": DETERMINACY_AUDIT_VERSION,
            "status": "PROVED_UNDERDETERMINED",
            "witness_kind": "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS",
            "terminal_code": code,
            "unconsumed_constraint_ids": [],
            "dimensional_premise_ids": dimensional_ids,
            "positive_degree_goal_ids": positive_deg_goals,
            "counterexample_models": [],
            "trials_executed": 0,
            "scope_note": "Đề chỉ khai báo tên khối đa diện mà chưa nêu bất kỳ số đo hay quan hệ hình học nào.",
        }

    # Standalone curved solid missing an independent radius/height with 0 unconsumed non-curved constraints,
    # gated on goal dependence (e.g. degree-0 `ask_curved_volume_ratio` or `ask_radius` when radius is already supplied
    # MUST NOT be marked underdetermined without a diverging model pair).
    poly_calls = [c for c in non_ask_calls if c.fn in ("pyramid", "regular_pyramid", "prism")]
    curved_calls = [c for c in non_ask_calls if c.fn == "curved_solid"]
    if len(curved_calls) == 1 and not poly_calls and code == "MISSING_DIMENSION":
        k0 = curved_calls[0]
        other_coupling = [c.id for c in non_ask_calls if c.fn != "curved_solid" and c.id not in consumed_ids]
        ask_fns = {c.fn for c in ask_calls}
        goal_depends_on_missing = not ask_calls or (
            bool(positive_deg_goals)
            and not (ask_fns == {"ask_radius"} and bool(getattr(k0.args, "radius", None)))
        )
        if not other_coupling and goal_depends_on_missing:
            return {
                "schema_version": DETERMINACY_AUDIT_VERSION,
                "status": "PROVED_UNDERDETERMINED",
                "witness_kind": "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS",
                "terminal_code": code,
                "unconsumed_constraint_ids": unconsumed_ids,
                "dimensional_premise_ids": dimensional_ids,
                "positive_degree_goal_ids": positive_deg_goals,
                "counterexample_models": [],
                "trials_executed": 0,
                "scope_note": "Khối tròn xoay độc lập còn thiếu bán kính hoặc chiều cao/đường sinh mà không có ràng buộc phụ.",
            }

    # Multi-branch mirror/root divergence recorded by engine
    if code == "AMBIGUOUS_FACT" and details.get("divergent_branches"):
        return {
            "schema_version": DETERMINACY_AUDIT_VERSION,
            "status": "PROVED_UNDERDETERMINED",
            "witness_kind": "MULTI_ROOT_OR_MIRROR_BRANCH_DIVERGENCE",
            "terminal_code": code,
            "unconsumed_constraint_ids": unconsumed_ids,
            "dimensional_premise_ids": dimensional_ids,
            "positive_degree_goal_ids": positive_deg_goals,
            "counterexample_models": list(details["divergent_branches"])[:2],
            "trials_executed": 0,
            "scope_note": "Tồn tại ít nhất hai nhánh hình học hợp lệ thỏa toàn bộ giả thiết nhưng cho kết quả khác nhau.",
        }

    # 2. Constructive two-model counterexample search (capped at MAX_COUNTEREXAMPLE_TRIALS, pure Fraction arithmetic)
    open_reps = _collect_open_segment_representatives(calls, problem_text)
    scale_free = len(dimensional_ids) == 0
    trial_specs = _build_trial_specs(open_reps, scale_free_premises=scale_free)

    valid_by_sig: dict[tuple, dict[str, Any]] = {}
    valid_count = 0
    trials_run = 0

    for label, sc_unit, free_h2, sh_units in trial_specs:
        trials_run += 1
        rk, _anc, _tr = _dung_mot_nhanh(
            problem_text,
            plan,
            deepcopy(auxiliary),
            read_quotes,
            _scale_unit=sc_unit,
            _free_h2_sample=free_h2,
            _shape_units=sh_units,
        )
        if rk.status != "SERVED" or rk.kernel_check is not True:
            continue
        valid_count += 1
        sig = _answer_signature(rk, bool(ask_calls), bool(section_calls), intersection_line_ids)
        if sig not in valid_by_sig:
            entry: dict[str, Any] = {
                "trial": label,
                "answers": dict(rk.answers or {}),
                "answer_exact": deepcopy(rk.answer_exact or {}),
            }
            if not ask_calls:
                entry["construction_signature"] = [str(x) for x in sig]
            valid_by_sig[sig] = entry
        # Homothety positive-degree shortcut: 0 dimensional premises + 1 certified unit model + positive-degree goal
        if scale_free and positive_deg_goals and sc_unit == Fraction(1) and len(valid_by_sig) == 1:
            # Running the second scale trial confirms divergence explicitly when next in list; if already >=2 sigs, exit below
            pass
        if len(valid_by_sig) >= 2:
            m1, m2 = list(valid_by_sig.values())[:2]
            is_pure_scale = (
                scale_free
                and bool(positive_deg_goals)
                and m1["trial"].startswith("scale=")
                and m2["trial"].startswith("scale=")
                and "," not in m1["trial"]
                and "," not in m2["trial"]
            )
            return {
                "schema_version": DETERMINACY_AUDIT_VERSION,
                "status": "PROVED_UNDERDETERMINED",
                "witness_kind": (
                    "HOMOTHETY_SCALE_DEGREE_POSITIVE" if is_pure_scale else "TWO_VALID_REALIZATIONS_DIVERGE"
                ),
                "terminal_code": code,
                "unconsumed_constraint_ids": unconsumed_ids,
                "dimensional_premise_ids": dimensional_ids,
                "positive_degree_goal_ids": positive_deg_goals,
                "counterexample_models": [m1, m2],
                "trials_executed": trials_run,
                "scope_note": (
                    "Đã kiểm chứng bằng hai mô hình Euclid chính xác thỏa 100% giả thiết nhưng cho kết quả khác nhau."
                ),
            }

    if valid_count >= 2 and len(valid_by_sig) == 1:
        return {
            "schema_version": DETERMINACY_AUDIT_VERSION,
            "status": "UNPROVED_DUE_TO_CAPABILITY_GAP",
            "witness_kind": "CONSTANT_ACROSS_SAMPLED_REALIZATIONS_UNPROVED_INVARIANCE",
            "terminal_code": code,
            "unconsumed_constraint_ids": unconsumed_ids,
            "unconsumed_coupling_constraint_ids": unconsumed_coupling_ids,
            "dimensional_premise_ids": dimensional_ids,
            "positive_degree_goal_ids": positive_deg_goals,
            "counterexample_models": list(valid_by_sig.values()),
            "trials_executed": trials_run,
            "scope_note": (
                "Các cấu hình hợp lệ thử nghiệm cho cùng một kết quả, nhưng hệ chưa có chứng chỉ bất biến tổng quát "
                "cho mọi cấu hình thỏa đề."
            ),
        }

    return {
        "schema_version": DETERMINACY_AUDIT_VERSION,
        "status": "UNPROVED_DUE_TO_CAPABILITY_GAP",
        "witness_kind": "NO_DIVERGING_REALIZATION_PAIR_FOUND",
        "terminal_code": code,
        "unconsumed_constraint_ids": unconsumed_ids,
        "unconsumed_coupling_constraint_ids": unconsumed_coupling_ids,
        "dimensional_premise_ids": dimensional_ids,
        "positive_degree_goal_ids": positive_deg_goals,
        "counterexample_models": list(valid_by_sig.values()),
        "trials_executed": trials_run,
        "scope_note": (
            "Không tìm được cặp mô hình hợp lệ cho kết quả khác nhau; còn giả thiết chưa được suy diễn hết hoặc hệ "
            "chưa chứng minh được tính xác định duy nhất của bài toán."
        ),
    }


def audit_determinacy_from_typed_facts(
    problem_text: str,
    typed_facts_payload: dict[str, Any],
    *,
    terminal_code: str = "MISSING_DIMENSION",
) -> dict[str, Any]:
    """Run `audit_determinacy` on a `TypedFactNext /2` payload (stripping `missing_operand[dimension]` unresolved entries
    when auditing whether the extracted geometric premises actually leave the target underdetermined)."""
    from .engine import _dung_mot_nhanh
    from .planner import lap_ke_hoach
    from .registry import _CHINH_SACH_XUAT
    from .typed_fact_next_bridge import bridge_v2

    if terminal_code in ("PLANE_NOT_UNIQUE", "FIGURE_NOT_UNIQUE"):
        return {
            "schema_version": DETERMINACY_AUDIT_VERSION,
            "status": "PROVED_UNDERDETERMINED",
            "witness_kind": "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS",
            "terminal_code": terminal_code,
            "unconsumed_constraint_ids": [],
            "counterexample_models": [],
            "trials_executed": 0,
            "scope_note": "Các ràng buộc đã trích xuất để ngỏ một họ vô số mặt phẳng hoặc vị trí đỉnh.",
        }

    cleaned = deepcopy(typed_facts_payload)
    unresolved = list(cleaned.get("unresolved") or [])
    if unresolved:
        # Only strip dimension-only missing_operand markers so we can test whether other extracted premises couple the scale
        dim_only = all(
            u.get("kind") == "missing_operand" and list(u.get("missing_roles") or []) == ["dimension"]
            for u in unresolved
        )
        if not dim_only:
            if all(
                u.get("kind") == "missing_operand"
                and set(u.get("missing_roles") or ()) <= {"solid_notation", "dimension"}
                for u in unresolved
            ) and not (cleaned.get("premises") or []):
                return {
                    "schema_version": DETERMINACY_AUDIT_VERSION,
                    "status": "PROVED_UNDERDETERMINED",
                    "witness_kind": "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS",
                    "terminal_code": terminal_code,
                    "unconsumed_constraint_ids": [],
                    "counterexample_models": [],
                    "trials_executed": 0,
                    "scope_note": "Đề chưa nêu ký hiệu đỉnh và kích thước của khối cần dựng.",
                }
            return {
                "schema_version": DETERMINACY_AUDIT_VERSION,
                "status": "UNPROVED_DUE_TO_CAPABILITY_GAP",
                "witness_kind": "UNRESOLVED_SEMANTIC_OPERAND",
                "terminal_code": terminal_code,
                "unconsumed_constraint_ids": [],
                "counterexample_models": [],
                "trials_executed": 0,
                "scope_note": "Còn toán hạng hoặc tham chiếu ngữ nghĩa chưa được phân giải duy nhất.",
            }
        cleaned["unresolved"] = []

    try:
        b = bridge_v2(cleaned)
    except TuChoi as e:
        return {
            "schema_version": DETERMINACY_AUDIT_VERSION,
            "status": "UNPROVED_DUE_TO_CAPABILITY_GAP",
            "witness_kind": f"BRIDGE_OR_PLANNER_REFUSED:{e.code}",
            "terminal_code": e.code,
            "unconsumed_constraint_ids": list(e.calls or ()),
            "counterexample_models": [],
            "trials_executed": 0,
            "scope_note": "Chưa lập được kế hoạch thực thi đầy đủ để chứng minh tính bất định toán học.",
        }

    out_pols = b["bridge"].get("output_policies")
    tok = _CHINH_SACH_XUAT.set(out_pols)
    try:
        try:
            k = lap_ke_hoach({"facts": b["facts"]}, b["bridge"]["problem_text"])
        except TuChoi as e:
            if e.code in ("PLANE_NOT_UNIQUE", "FIGURE_NOT_UNIQUE"):
                return {
                    "schema_version": DETERMINACY_AUDIT_VERSION,
                    "status": "PROVED_UNDERDETERMINED",
                    "witness_kind": "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS",
                    "terminal_code": e.code,
                    "unconsumed_constraint_ids": [],
                    "counterexample_models": [],
                    "trials_executed": 0,
                    "scope_note": "Bộ lập kế hoạch xác nhận ràng buộc để ngỏ quỹ tích mặt phẳng hoặc đỉnh.",
                }
            return {
                "schema_version": DETERMINACY_AUDIT_VERSION,
                "status": "UNPROVED_DUE_TO_CAPABILITY_GAP",
                "witness_kind": f"BRIDGE_OR_PLANNER_REFUSED:{e.code}",
                "terminal_code": e.code,
                "unconsumed_constraint_ids": list(e.calls or ()),
                "counterexample_models": [],
                "trials_executed": 0,
                "scope_note": "Chưa lập được kế hoạch thực thi đầy đủ để chứng minh tính bất định toán học.",
            }

        plan_dict = {"calls": k.calls, "named_planes": k.named_planes}
        doc = tuple(q for g in (*k.goals, *k.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
        r0, _anc0, _tr0 = _dung_mot_nhanh(b["bridge"]["problem_text"], plan_dict, tuple(k.auxiliary), doc)
        if r0.status == "SERVED" and r0.kernel_check is True:
            return {
                "schema_version": DETERMINACY_AUDIT_VERSION,
                "status": "UNPROVED_DUE_TO_CAPABILITY_GAP",
                "witness_kind": "CONSTRUCTIBLE_WHEN_DIMENSION_COUPLED_BY_OTHER_PREMISES",
                "terminal_code": terminal_code,
                "unconsumed_constraint_ids": [],
                "counterexample_models": [
                    {
                        "trial": "coupled_exact_kernel",
                        "answers": dict(r0.answers or {}),
                        "answer_exact": deepcopy(r0.answer_exact or {}),
                    }
                ],
                "trials_executed": 1,
                "scope_note": (
                    "Các giả thiết khác trong đề đã khóa kích thước trong nhân chính xác, nhưng bộ đọc cục bộ hiện tại "
                    "yêu cầu nêu trực tiếp cạnh đáy."
                ),
            }
        return audit_determinacy(
            b["bridge"]["problem_text"],
            plan_dict,
            tuple(k.auxiliary),
            doc,
            r0,
        )
    finally:
        _CHINH_SACH_XUAT.reset(tok)
