# -*- coding: utf-8 -*-
"""P4 development evaluation (`DEVELOPMENT_EVALUATION_NOT_BLIND`) of run `typedfactnext-planner-bridge`.

Generates TypedFactNext payloads + their Vietnamese text from a closed template family, runs each through
(a) the bridge route `run_typed_fact_next_planner_route` (bridge → planner → Source Gate → engine) and
(b) Adapter /3 `run_typed_fact_next_route`, and scores them against an INDEPENDENT closed-form oracle (plain Fraction
arithmetic; no engine call) plus metamorphic relations. Offline, 0 provider calls. Inputs are authored JSON — this does
NOT measure natural-language extraction. Run from `backend/`:

    PYTHONIOENCODING=utf-8 ../backend/.venv/Scripts/python.exe <this file> <out.json>
"""
from __future__ import annotations

import json
import re
import sys
import time
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.ai.adapter3_simulation import run_typed_fact_next_route  # noqa: E402
from app.ai.function_route import run_typed_fact_next_planner_route  # noqa: E402

CLASSIFICATION = "DEVELOPMENT_EVALUATION_NOT_BLIND"


# ── independent oracle ──────────────────────────────────────────────────────────────────────────────────────────────

def square_of(coef: str) -> Fraction:
    """Square of an exact display coefficient "p", "p/q", "p√r", "p√r/q", "√r/q" — independent reader."""
    m = re.fullmatch(r"(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?", coef or "")
    if not m or not (m["p"] or m["r"]):
        raise ValueError(coef)
    p, r, q = Fraction(m["p"] or 1), Fraction(m["r"] or 1), Fraction(m["q"] or 1)
    return p * p * r / (q * q)


def base_area_sq(shape: str, dims: tuple[Fraction, ...]) -> Fraction:
    """Squared base area (keeps √3 exact): equilateral s²√3/4, square s², rectangle pq, right triangle pq/2."""
    if shape == "equilateral":
        s = dims[0]
        return s ** 4 * 3 / 16
    if shape == "square":
        return dims[0] ** 4
    if shape == "rectangle":
        return (dims[0] * dims[1]) ** 2
    return (dims[0] * dims[1] / 2) ** 2


def oracle(v: dict) -> dict:
    """Expected exact answers (squared coefficients) of a served variant: SA ⊥ base ⇒ V = ⅓·S·h; a plane ∥ base (or ⊥ SA,
    the same plane when SA ⊥ base) through M with SM/SA = t cuts every lateral edge at t ⇒ V(sub)/V = t³."""
    v_sq = base_area_sq(v["shape"], v["dims"]) * v["h"] ** 2 / 9
    t3 = v["t"] ** 3
    out = {}
    if v.get("ratio"):
        out["g_ratio"] = (1 / t3) ** 2 if v.get("inverted") else t3 ** 2
    if v.get("residual"):
        out["g_res"] = (1 - t3) ** 2 * v_sq
    return out


# ── template family ─────────────────────────────────────────────────────────────────────────────────────────────────

def num(x: Fraction, sym: bool) -> str:
    s = str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
    return ("a" if s == "1" else f"{s}a") if sym else s


def variant(shape="equilateral", dims=(Fraction(1),), h=Fraction(1), sym=True, t=Fraction(1, 2), plane="parallel",
            names=True, ratio=True, residual=False, inverted=False, labels=None, premise_order=None, goal_order="ratio_first"):
    L = {"S": "S", "A": "A", "B": "B", "C": "C", "D": "D", "M": "M", "N": "N", "P": "P", "Q": "Q", **(labels or {})}
    n_base = 4 if shape in ("square", "rectangle") else 3
    base = [L[x] for x in "ABCD"[:n_base]]
    S, A, M = L["S"], base[0], L["M"]
    cut = [[S, b] for b in base[1:]]
    pts = [L[x] for x in "NPQ"[:len(cut)]]
    ten = "".join(base)
    sentences, premises = [], []

    def add(text: str, prem: dict | None):
        sentences.append(text)
        if prem:
            premises.append({**prem, "quote": text})
    solid_q = f"Cho hình chóp {S}.{ten}."
    if shape == "equilateral":
        base_s = (f"Đáy {ten} là tam giác đều cạnh {num(dims[0], sym)}.",
                  {"kind": "base_is_equilateral_triangle", "args": {"vertices": base, "side": num(dims[0], sym)}})
        extra = []
    elif shape == "square":
        base_s = (f"Đáy {ten} là hình vuông cạnh {num(dims[0], sym)}.",
                  {"kind": "base_is_square", "args": {"vertices": base, "side": num(dims[0], sym)}})
        extra = []
    elif shape == "rectangle":
        base_s = (f"Đáy {ten} là hình chữ nhật.", {"kind": "base_is_rectangle", "args": {"vertices": base}})
        extra = [(f"{base[0]}{base[1]} = {num(dims[0], sym)}.",
                  {"kind": "segment_length", "args": {"segment": base[:2], "value": num(dims[0], sym)}}),
                 (f"{base[1]}{base[2]} = {num(dims[1], sym)}.",
                  {"kind": "segment_length", "args": {"segment": base[1:3], "value": num(dims[1], sym)}})]
    else:
        base_s = (f"Đáy {ten} là tam giác vuông tại {A}.",
                  {"kind": "base_is_right_triangle", "args": {"vertices": base, "right_at": A}})
        extra = [(f"{A}{base[1]} = {num(dims[0], sym)}.",
                  {"kind": "segment_length", "args": {"segment": [A, base[1]], "value": num(dims[0], sym)}}),
                 (f"{A}{base[2]} = {num(dims[1], sym)}.",
                  {"kind": "segment_length", "args": {"segment": [A, base[2]], "value": num(dims[1], sym)}})]
    perp = (f"{S}{A} vuông góc với mặt phẳng ({''.join(base[:3])}).",
            {"kind": "line_perp_plane", "args": {"line": [S, A], "plane": base[:3]}})
    sa = (f"{S}{A} = {num(h, sym)}.", {"kind": "segment_length", "args": {"segment": [S, A], "value": num(h, sym)}})
    block = [base_s, *extra, perp, sa]
    for i in (premise_order or range(len(block))):
        add(*block[i])
    if t == Fraction(1, 2):
        add(f"Gọi {M} là trung điểm của {S}{A}.", {"kind": "point_is_midpoint", "args": {"point": M, "segment": [S, A]}})
    else:
        add(f"Điểm {M} thuộc cạnh {S}{A} sao cho {S}{M} = {t.numerator}/{t.denominator} {S}{A}.",
            {"kind": "point_divides_segment", "args": {"point": M, "segment": [S, A], "ratio": f"{t.numerator}/{t.denominator}"}})
    rel = f"song song với ({''.join(base[:3])})" if plane == "parallel" else f"vuông góc với {S}{A}"
    edges = ", ".join("".join(e) for e in cut)
    sec_q = f"Mặt phẳng (α) qua {M} và {rel} cắt {edges}" + (f" lần lượt tại {', '.join(pts)}." if names else ".")
    sentences.append(sec_q)
    sec = {"section_id": "sec", "plane_name": "α", "target_solid_id": "pyr", "through_point": M, "quote": sec_q,
           "cut_edges": cut, "named_intersections": {f"{u}-{w}": p for (u, w), p in zip(cut, pts)} if names else {}}
    sec.update({"plane_kind": "through_point_parallel_plane", "parallel_plane": base[:3]} if plane == "parallel" else
               {"plane_kind": "through_point_perpendicular_line", "perpendicular_line": [S, A]})
    req = f"Dựng thiết diện của hình chóp {S}.{ten} bởi (α)."
    sentences.append(req)
    sim = [{"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec", "quote": req}]
    math = []
    sub = f"{S}.{M}{''.join(pts)}"
    if names:
        q_ratio = (f"Tính tỉ số thể tích của hai khối chóp {S}.{ten} và {sub}." if inverted
                   else f"Tính tỉ số thể tích của hai khối chóp {sub} và {S}.{ten}.")
        q_res = f"Tính thể tích phần còn lại của khối chóp {S}.{ten} sau khi cắt bỏ khối chóp {sub}."
        asks = []
        if ratio:
            asks.append((q_ratio, {"goal_id": "g_ratio", "kind": "volume_ratio",
                                   **({"numerator_solid_id": "pyr", "denominator_solid_id": "sub"} if inverted
                                      else {"numerator_solid_id": "sub", "denominator_solid_id": "pyr"})}))
        if residual:
            asks.append((q_res, {"goal_id": "g_res", "kind": "residual_volume", "parent_solid_id": "pyr",
                                 "cut_solid_id": "sub"}))
        if goal_order == "residual_first":
            asks.reverse()
        for q, g in asks:
            sentences.append(q)
            math.append({**g, "quote": q})
        if asks:
            sim.append({"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                        "target_section_id": "sec", "apex_ref": S, "parent_solid_id": "pyr", "quote": asks[0][0]})
    else:
        dq = f"Dựng khối chóp đỉnh {S} cắt bởi (α)."
        sentences.append(dq)
        sim.append({"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                    "target_section_id": "sec", "apex_ref": S, "parent_solid_id": "pyr", "quote": dq})
    text = " ".join([solid_q, *sentences])
    payload = {"schema_version": "typed-fact-next/1", "problem_text": text,
               "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": f"{S}.{ten}", "quote": solid_q}],
               "premises": premises, "derived_sections": [sec], "simulation_goals": sim, "math_goals": math}
    meta = {"shape": shape, "dims": dims, "h": h, "t": t, "ratio": ratio and names, "residual": residual and names,
            "inverted": inverted, "names": names, "plane": plane, "sym": sym}
    return payload, meta


# ── scoring ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def depth(calls: list[dict]) -> int:
    """Longest producer chain of a plan (points produced by one call and consumed by another; solids by name)."""
    out, solids = {}, {}
    for c in calls:
        a = c["args"]
        p = a.get("image") if c["fn"] in ("translate_point", "orthogonal_projection_line", "orthogonal_projection") else (
            a.get("point") if c["fn"] in ("midpoint", "centroid", "divide_segment", "intersect_line_line", "intersect_line_plane")
            else None)
        if p:
            out[p] = c["id"]
        if c["fn"] in ("pyramid", "regular_pyramid"):
            solids[f"{a['apex']}.{''.join(a['base'])}"] = c["id"]
    by = {c["id"]: c for c in calls}
    memo: dict[str, int] = {}

    def d(cid: str) -> int:
        if cid in memo:
            return memo[cid]
        memo[cid] = 0
        a, deps = by[cid]["args"], set()
        for v in a.values():
            for x in (v if isinstance(v, list) else [v]):
                if isinstance(x, str) and out.get(x) not in (None, cid):
                    deps.add(out[x])
                if isinstance(x, str) and x in solids and solids[x] != cid:
                    deps.add(solids[x])
        memo[cid] = 1 + max((d(x) for x in deps), default=0)
        return memo[cid]
    return max((d(c["id"]) for c in calls), default=0)


def leaks(scene: dict, fresh: list[str]) -> list[str]:
    if not fresh:
        return []
    tok = re.compile(r"(?<![\w'])[A-Z0-9'.]*(?:" + "|".join(map(re.escape, fresh)) + r")[A-Z0-9'.]*(?![\w'])")
    txt = [str(o.get(k)) for o in scene["objects"] for k in ("label", "display_label", "reference", "notation", "role")]
    txt += [str(e.get(k)) for e in scene["events"] for k in ("display_label", "learner_text", "explanation")]
    txt += [s.get("learner_text", "") for s in scene["formation"]["steps"]]
    return [s for s in txt if tok.search(s)]


def scene_ok(scene: dict) -> tuple[bool, str]:
    """Structural Scene3D check reused from the operator preview (same births/dependency/metric rules)."""
    from app.ai.hybrid_preview import PreviewInvalid, _validate_scene
    try:
        _validate_scene(deepcopy(scene))
        return True, ""
    except PreviewInvalid as e:
        return False, str(e)


def adapter_convention(payload: dict) -> dict:
    """Adapter /3 reads `cut_edges` as the COMPLETE section cycle (its corpus omits it: every lateral edge, the through-
    point reused); the bridge reads it as the edges the source STATES are cut. Each route gets its own convention."""
    q = deepcopy(payload)
    for s in q["derived_sections"]:
        s["cut_edges"] = []
    return q


def _a3(payload: dict):
    try:
        a = run_typed_fact_next_route(deepcopy(payload))
        return a, {"status": a.status, "code": a.code}
    except Exception as e:  # noqa: BLE001 — an Adapter /3 crash is a finding, recorded, not a harness failure
        return None, {"status": "CRASH", "code": type(e).__name__}


def run_case(cid: str, payload: dict, meta: dict | None, expect: str, codes: tuple[str, ...] = ()) -> dict:
    t0 = time.perf_counter()
    r = run_typed_fact_next_planner_route(deepcopy(payload))
    dt = time.perf_counter() - t0
    a, a3 = _a3(adapter_convention(payload))
    same, same_row = _a3(payload)                 # the bridge's payload as is: does Adapter /3 notice the open cycle?
    a3["same_payload"] = {**same_row, "answers": (same.answers if same is not None and same.status == "SERVED" else {})}
    row = {"id": cid, "expect": expect, "status": r.status, "code": r.code, "adapter3": a3, "seconds": round(dt, 4)}
    want = oracle(meta) if (meta and expect == "SERVED") else {}
    if r.status == "SERVED":
        ex = {k: square_of(v["coef"]) for k, v in (r.answer_exact or {}).items()}
        row["exact_correct"] = ex == want
        calls = (r.planner or {}).get("calls") or []
        trace = (r.planner or {}).get("trace") or []
        sel = [s for s in trace if s.get("step") == "effect_resolution" and str(s.get("need", "")).startswith("SectionVertex")]
        cert = next((d for d in (r.planner or {}).get("auxiliary") or [] if d.get("vertices")), {})
        row["pattern"] = [sorted({c["fn"] for c in calls
                                  if c["fn"] in ("translate_point", "orthogonal_projection_line", "intersect_line_plane")}),
                          [s["selection"] for s in sel]]
        row.update(planner_calls=len(calls), planner_selected_operations=sum(
            1 for c in calls if c["fn"] in ("translate_point", "orthogonal_projection_line", "intersect_line_plane")
            or (c["fn"] == "pyramid" and c["id"] not in ("pyr",))), dag_depth=depth(calls),
            vertex_needs=len(sel), vertex_reused=sum(1 for s in sel if s["cost"] == 0),
            plane_constructions=sum(1 for c in calls if c["fn"] == "translate_point") // 2,
            fresh_labels=cert.get("labels", []))
        row["scene_valid"], row["scene_problem"] = scene_ok(r.scene3d)
        row["label_leaks"] = len(leaks(r.scene3d, row["fresh_labels"]))
        # review round 2: the planner's point-built plane name ("(MHH1)") in learner TEXT (object notation not counted)
        ky = next((o.get("notation") for o in r.scene3d["objects"] if o["id"].startswith("mp_td_")), None)
        txt = [str(o.get("role")) for o in r.scene3d["objects"]]
        txt += [str(e.get(k)) for e in r.scene3d["events"] for k in ("display_label", "learner_text", "explanation")]
        txt += [s.get("learner_text", "") for s in r.scene3d["formation"]["steps"]]
        row["planner_plane_name_in_text"] = sum(1 for s in txt if (ky and ky in s) or "mặt phẳng qua" in s)
        # one visible owner per plane: the IR operand plane of each cut must not show as a second (α)
        row["visible_duplicate_planes"] = sum(1 for o in r.scene3d["objects"] if re.fullmatch(r"derived_\w+_plane", o["id"])
                                              and o.get("render") != "non_visual")
        # pre-existing route B policy, reported not fixed: relation-plane auxiliary points (H…) are visible by label
        row["visible_auxiliary_plane_points"] = sum(1 for o in r.scene3d["objects"] if o.get("type") == "point3"
                                                    and re.fullmatch(r"H\d*", str(o.get("notation") or "")))
        row["quotes_in_source"] = all(q in payload["problem_text"] for c in calls for q in c["source"]["quotes"])
    def correct(res) -> bool:
        try:
            return {k: square_of(v["coef"]) for k, v in (res.answer_exact or {}).items() if k in want} == want
        except (ValueError, KeyError, TypeError):
            return False
    if a is not None and a.status == "SERVED" and want:
        row["adapter3"]["exact_correct"] = correct(a)
    if same is not None and same.status == "SERVED" and want:
        a3["same_payload"]["exact_correct"] = correct(same)
    # `REFUSED` = an invalid problem every sound route must refuse; `REFUSED_BRIDGE_SCOPE` = refused by the bridge by
    # design (Adapter /3 may legitimately serve it, so its serving is not counted as wrong).
    row["wrong_served"] = r.status == "SERVED" and (expect != "SERVED" or not row.get("exact_correct", False))
    row["refusal_correct"] = expect.startswith("REFUSED") and r.status == "REFUSED" and (not codes or r.code in codes)
    row["adapter3"]["wrong_served"] = a is not None and a.status == "SERVED" and (expect == "REFUSED" or (
        bool(want) and not row["adapter3"].get("exact_correct", False)))
    return row


def main(out: Path) -> None:
    rows, meta_of, groups = [], {}, {}
    F = Fraction

    def go(cid, pv, expect="SERVED", codes=(), group="base"):
        payload, meta = pv
        meta_of[cid] = meta
        groups.setdefault(group, []).append(cid)
        rows.append(run_case(cid, payload, meta, expect, codes))

    shapes = [("equilateral", (F(1),)), ("equilateral", (F(2),)), ("square", (F(1),)), ("square", (F(2),)),
              ("rectangle", (F(3), F(4))), ("right", (F(3), F(4)))]
    for si, (shape, dims) in enumerate(shapes):
        for t in (F(1, 2), F(1, 3), F(2, 3)):
            for plane in ("parallel", "perpendicular"):
                sym = shape in ("equilateral", "square")
                go(f"B-{shape}{si}-t{t.numerator}{t.denominator}-{plane}",
                   variant(shape, dims, h=F(2) if not sym else F(1), sym=sym, t=t, plane=plane, residual=True))
    # metamorphic families on one representative (triangle base: within the IR budget for both plane kinds)
    rep = dict(shape="equilateral", dims=(F(2),), h=F(3), sym=False, t=F(1, 3), residual=True)
    go("MR-ref", variant(**rep), group="mr")
    go("MR-relabel", variant(**rep, labels={"S": "T", "A": "E", "B": "F", "C": "G", "M": "U", "N": "V", "P": "X"}), group="mr")
    go("MR-premise-order", variant(**rep, premise_order=[2, 1, 0]), group="mr")
    go("MR-goal-order", variant(**rep, goal_order="residual_first"), group="mr")
    go("MR-inverted", variant(**{**rep, "residual": False}, inverted=True), group="mr")
    go("MR-scaled", variant(**{**rep, "dims": (F(6),), "h": F(9)}), group="mr")
    go("MR-plane-equivalence", variant(**rep, plane="perpendicular"), group="mr")
    # construction-only, unnamed vertices
    for shape, dims in (("equilateral", (F(1),)), ("square", (F(1),)), ("right", (F(3), F(4)))):
        for plane in ("parallel", "perpendicular"):
            go(f"C-{shape}-{plane}", variant(shape, dims, h=F(2), sym=shape != "right", t=F(1, 3), plane=plane, names=False),
               group="construction_only")
    # negative / refusal families
    p, m = variant()
    q = deepcopy(p); q["problem_text"] += " Biết SA = 2a."; q["premises"].append(
        {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}, "quote": "Biết SA = 2a."})
    go("N-contradictory-length", (q, m), "REFUSED", group="negative")
    q = deepcopy(p); q["problem_text"] = q["problem_text"].replace(" SA = a.", ""); q["premises"] = [
        x for x in q["premises"] if x["quote"] != "SA = a."]
    go("N-missing-height", (q, m), "REFUSED", group="negative")
    q = deepcopy(p); q["problem_text"] = q["problem_text"].replace("song song với (ABC)", "song song với (SBC)")
    q["derived_sections"][0].update(parallel_plane=["S", "B", "C"],
                                    quote=q["derived_sections"][0]["quote"].replace("(ABC)", "(SBC)"))
    go("N-degenerate-parallel-edge", (q, m), "REFUSED", group="negative")
    q = deepcopy(p); q["derived_sections"][0].update(cut_edges=[], named_intersections={})
    go("S-cut-edges-not-in-payload", (q, m), "REFUSED_BRIDGE_SCOPE", ("BRIDGE_CUT_EDGES_NOT_STATED",), group="bridge_scope")
    q = deepcopy(p); q["derived_sections"][0]["named_intersections"] = {"S-B": "P", "S-C": "N"}
    go("N-swapped-names", (q, m), "REFUSED", group="negative")
    q = deepcopy(p); q["solids"][0]["vertex_bindings"] = {"S": "S1"}
    go("S-shared-label-identity", (q, m), "REFUSED_BRIDGE_SCOPE", ("BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY",),
       group="bridge_scope")
    q = deepcopy(p); q["derived_sections"][0].update(plane_kind="plane_equation", equation_coeffs=("0", "0", "1", "-1"))
    go("S-plane-equation", (q, m), "REFUSED_BRIDGE_SCOPE", ("BRIDGE_UNSUPPORTED_PLANE_KIND",), group="bridge_scope")
    q = deepcopy(p); q["solids"].append({"solid_id": "cone", "solid_type": "cone", "notation": "S.O", "center": "O",
                                         "quote": "Cho hình chóp S.ABC."})
    go("S-curved-solid", (q, m), "REFUSED_BRIDGE_SCOPE", ("BRIDGE_UNSUPPORTED_CURVED",), group="bridge_scope")
    pa, ma = variant(names=False)
    q = deepcopy(pa); q["problem_text"] += " Tính tỉ số thể tích."
    q["math_goals"] = [{"goal_id": "g_ratio", "kind": "volume_ratio", "numerator_solid_id": "sub",
                        "denominator_solid_id": "pyr", "quote": "Tính tỉ số thể tích."}]
    go("N-anonymous-ratio-operand", (q, ma), "REFUSED", group="negative")
    q = deepcopy(pa); q["problem_text"] = q["problem_text"].replace("cắt SB, SC.", "cắt SB.")
    q["derived_sections"][0].update(cut_edges=[["S", "B"]], quote=q["derived_sections"][0]["quote"].replace("SB, SC", "SB"))
    # conservative by design: the planner does not add a cut (SC) the source did not state, even though it exists
    go("S-open-cycle", (q, ma), "REFUSED_BRIDGE_SCOPE", ("SECTION_NOT_CLOSED_ON_LATERAL_EDGES",), group="bridge_scope")
    q = deepcopy(p); q["problem_text"] = q["problem_text"].replace("lần lượt tại N, P.", "lần lượt tại N, P sao cho NP = BC.")
    q["derived_sections"][0]["quote"] = q["derived_sections"][0]["quote"].replace("N, P.", "N, P sao cho NP = BC.")
    go("N-unread-condition", (q, m), "REFUSED", group="negative")

    by = {r["id"]: r for r in rows}

    def ans(cid):
        return by[cid].get("exact_correct"), by[cid]["status"]
    mr = {
        "relabel_invariance": by["MR-relabel"]["status"] == by["MR-ref"]["status"] == "SERVED"
        and by["MR-relabel"].get("exact_correct") is True,
        "premise_order_invariance": ans("MR-premise-order") == (True, "SERVED"),
        "goal_order_invariance": ans("MR-goal-order") == (True, "SERVED"),
        "ratio_inversion_reciprocal": ans("MR-inverted") == (True, "SERVED"),
        "scaling_ratio_invariant_residual_k3": ans("MR-scaled") == (True, "SERVED"),
        "parallel_base_equals_perpendicular_SA": ans("MR-plane-equivalence") == (True, "SERVED"),
    }
    served = [r for r in rows if r["status"] == "SERVED"]
    expect_served = [r for r in rows if r["expect"] == "SERVED"]
    expect_refused = [r for r in rows if r["expect"].startswith("REFUSED")]
    invalid = [r for r in rows if r["expect"] == "REFUSED"]
    from collections import Counter
    agg = {
        "cases": len(rows), "expected_served": len(expect_served), "expected_refused_invalid": len(invalid),
        "expected_refused_bridge_scope": len(expect_refused) - len(invalid),
        "goal_coverage": f"{sum(r['status'] == 'SERVED' for r in expect_served)}/{len(expect_served)}",
        "not_covered_codes": dict(Counter(r["code"] for r in expect_served if r["status"] != "SERVED")),
        "exact_correct_of_served_with_answers": f"{sum(r.get('exact_correct') for r in served if oracle(meta_of[r['id']]))}"
                                                 f"/{sum(1 for r in served if oracle(meta_of[r['id']]))}",
        "wrong_served": sum(r["wrong_served"] for r in rows),
        "refusal_correct": f"{sum(r['refusal_correct'] for r in expect_refused)}/{len(expect_refused)}",
        "scene_valid": f"{sum(r.get('scene_valid', False) for r in served)}/{len(served)}",
        "label_leaks": sum(r.get("label_leaks", 0) for r in served),
        "visible_duplicate_planes": sum(r.get("visible_duplicate_planes", 0) for r in served),
        "planner_plane_name_in_text": sum(r.get("planner_plane_name_in_text", 0) for r in served),
        "served_with_visible_auxiliary_H_points": sum(1 for r in served if r.get("visible_auxiliary_plane_points")),
        "selection_counts": dict(Counter(s for r in served for s in r["pattern"][1])),
        "quotes_in_source": f"{sum(r.get('quotes_in_source', False) for r in served)}/{len(served)}",
        "planner_selected_operations_mean": round(sum(r["planner_selected_operations"] for r in served) / max(1, len(served)), 2),
        "dag_depth_max": max((r["dag_depth"] for r in served), default=0),
        "dag_depth_min": min((r["dag_depth"] for r in served), default=0),
        "vertex_reuse_rate": f"{sum(r['vertex_reused'] for r in served)}/{sum(r['vertex_needs'] for r in served)}",
        "plane_constructions_per_served": sorted({r["plane_constructions"] for r in served}),
        # distinct (decomposition functions, per-edge selections) the planner produced: not one fixed chain
        "distinct_composition_patterns": sorted({json.dumps(r["pattern"]) for r in served}),
        "seconds_p50": sorted(r["seconds"] for r in rows)[len(rows) // 2], "seconds_max": max(r["seconds"] for r in rows),
        "metamorphic_relations": mr,
        "adapter3": {
            "served": sum(r["adapter3"]["status"] == "SERVED" for r in rows),
            "wrong_served": sum(r["adapter3"]["wrong_served"] for r in rows),
            "exact_correct_when_served": f"{sum(r['adapter3'].get('exact_correct') is True for r in rows)}"
                                         f"/{sum('exact_correct' in r['adapter3'] for r in rows)}",
            "served_invalid": [r["id"] for r in invalid if r["adapter3"]["status"] == "SERVED"],
            "served_bridge_scope": [r["id"] for r in expect_refused if r["expect"] != "REFUSED"
                                    and r["adapter3"]["status"] == "SERVED"],
            "crashes": [(r["id"], r["adapter3"]["code"]) for r in rows if r["adapter3"]["status"] == "CRASH"],
            "same_payload_wrong_served": [r["id"] for r in rows if r["adapter3"]["same_payload"].get("exact_correct") is False],
            "same_payload_served": sum(r["adapter3"]["same_payload"]["status"] == "SERVED" for r in rows),
        },
    }
    out.write_text(json.dumps({"classification": CLASSIFICATION, "provider_calls": 0, "groups": groups, "aggregate": agg,
                               "rows": rows}, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
