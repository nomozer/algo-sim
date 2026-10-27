# -*- coding: utf-8 -*-
"""Preregistered evaluator for Hybrid V2 Independent Vietnamese Section Holdout Wave 2.

Implements `preregistration.md` and `scoring-contract.md` exactly.
- Zero live provider calls (`ALLOW_LIVE_AI = "0"`).
- Evaluates Track A (deterministic Hybrid V2 pipeline: `run_typed_fact_next_v2_route` -> `build_adapter4_response`),
  Track B (contract representability), and Scene3D learner-facing semantics (Track 10.A source-identity correctness
  vs. Track 10.B O4/R1 pedagogical auxiliary display).
- Provides `score_observed_response(...)` decoupled from product execution so that synthetic positive and negative
  scorer controls (`test_evaluate_holdout_wave2.py`) can verify all 17 mandatory safeguards independently of product code.

Usage:
    python evaluate_holdout_wave2.py <out_dir>
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]

CORPUS = RUN / "inputs/holdout-wave2.json"
EXPECTED = RUN / "oracle/expected.json"
TAXONOMY = RUN / "tools/refusal_taxonomy.json"


def _norm_label(x: Any) -> str:
    return (
        str(x or "")
        .replace("_prime", "'")
        .replace("″", "''")
        .replace("′", "'")
        .replace("’", "'")
        .strip()
    )


def _code_category(code: str | None, reason: str | None, tax: dict[str, Any]) -> tuple[str, str | None]:
    """Map `(code, reason)` to `(category, subcode)` using frozen `refusal_taxonomy.json`."""
    if not code:
        return "UNMAPPED", None
    base = code.split(":")[0].strip()
    reason_str = str(reason or "")
    if base == "ENGINE_EXECUTION_FAILED":
        if "Không tách được căn" in reason_str:
            return "UNSUPPORTED_CAPABILITY", "RADICAL_DOMAIN_OVERFLOW"
        degen_markers = (
            "trùng nhau",
            "thẳng hàng",
            "song song",
            "không cắt",
            "suy biến",
            "không tạo thành mặt phẳng",
        )
        if any(m in reason_str.lower() for m in degen_markers):
            return "GEOMETRY_DEGENERATE", "KERNEL_GEOMETRY_DEGENERATE"
        return "INTERNAL_OR_VALIDATION", None
    for cat, codes in tax["categories"].items():
        if base in codes:
            return cat, None
    return "UNMAPPED", None


def _square(v: Any) -> F:
    if hasattr(v, "he") and hasattr(v, "can"):
        return F(v.he) ** 2 * F(v.can)
    if isinstance(v, dict) and "he" in v and "can" in v:
        return F(v["he"]) ** 2 * F(v["can"])
    return F(v) ** 2


def wilson(k: int, n: int, z: float = 1.959964) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def _same_cycle(ring_a: list[Any], ring_b: list[Any]) -> bool:
    if not ring_a or len(ring_a) != len(ring_b):
        return False
    m = len(ring_b)
    for cand in (ring_b, list(reversed(ring_b))):
        for i in range(m):
            if ring_a == cand[i:] + cand[:i]:
                return True
    return False


def _oracle_descriptors(exp: dict[str, Any]) -> tuple[list[tuple], Counter, Counter]:
    boundary = exp["boundary"]
    if not isinstance(boundary, list) or len(boundary) < 3:
        raise ValueError("oracle boundary must be a list of >= 3 vertices")
    ring: list[tuple] = []
    verts: Counter = Counter()
    edges: Counter = Counter()
    for b in boundary:
        if not isinstance(b, dict):
            raise TypeError("oracle boundary item must be a dict")
        if "vertex" in b:
            v_lbl = _norm_label(b["vertex"])
            desc = ("VERTEX", v_lbl)
            verts[v_lbl] += 1
            ring.append(desc)
        elif "edge" in b and "t" in b:
            u, v = (_norm_label(x) for x in b["edge"])
            t_raw = F(str(b["t"]))
            if t_raw == 0:
                desc = ("VERTEX", u)
                verts[u] += 1
            elif t_raw == 1:
                desc = ("VERTEX", v)
                verts[v] += 1
            elif F(0) < t_raw < F(1):
                a, b_lbl = sorted((u, v))
                t_canon = t_raw if u == a else (F(1) - t_raw)
                desc = ("EDGE", a, b_lbl, t_canon)
                edges[(a, b_lbl, t_canon)] += 1
            else:
                raise ValueError(f"oracle edge parameter t={t_raw} out of [0, 1]")
            ring.append(desc)
        else:
            raise KeyError("oracle boundary item must contain 'vertex' or ('edge', 't')")
    return ring, verts, edges


def _find_point_xyz(objects_by_id: dict[str, dict], label: str) -> list[F] | None:
    norm_target = _norm_label(label)
    for o in objects_by_id.values():
        if o.get("type") != "point3":
            continue
        if _norm_label(o.get("id")) == norm_target or _norm_label(o.get("notation")) == norm_target:
            xyz = o.get("xyz")
            if isinstance(xyz, list) and len(xyz) == 3:
                return [F(str(c)) for c in xyz]
    return None


def _check_section_boundary(
    sec: dict[str, Any],
    obj: dict[str, Any],
    objects_by_id: dict[str, dict],
    exp: dict[str, Any],
    is_cat_b: bool,
) -> list[str]:
    oracle_ring, o_verts, o_edges = _oracle_descriptors(exp)
    poly_raw = obj.get("polygon") or []
    vertices = sec.get("vertices") or []
    bad: list[str] = []

    if len(vertices) != exp["vertex_count"]:
        bad.append(f"section.vertices count {len(vertices)} != oracle {exp['vertex_count']}")

    p_verts: Counter = Counter()
    p_edges: Counter = Counter()
    indexed_descs: list[tuple[int, tuple]] = []

    for idx_fallback, v in enumerate(vertices):
        # Resolve polygon index for cyclic ordering check
        poly_idx = idx_fallback
        if is_cat_b and isinstance(v.get("ordinal"), int):
            poly_idx = v["ordinal"]
        elif v.get("xyz") in poly_raw:
            poly_idx = poly_raw.index(v["xyz"])
        elif v.get("label") and v["label"] in objects_by_id:
            pt_xyz = objects_by_id[v["label"]].get("xyz")
            if pt_xyz in poly_raw:
                poly_idx = poly_raw.index(pt_xyz)

        edge_raw = v.get("edge") or []
        if len(edge_raw) != 2:
            bad.append(f"vertex {v} does not have a 2-endpoint edge")
            continue
        u, w = (_norm_label(x) for x in edge_raw)
        if u == w:
            bad.append(f"degenerate edge [{u}, {w}] on vertex {v}")
            continue

        if is_cat_b:
            if v.get("t") is None:
                bad.append(f"Category B vertex {v} missing parameter t")
                continue
            t_val = F(str(v["t"]))
            src_kind = v.get("source_kind")
            if src_kind == "SOLID_VERTEX" or t_val in (F(0), F(1)):
                if src_kind != "SOLID_VERTEX" or t_val not in (F(0), F(1)):
                    bad.append(f"Category B vertex {v} inconsistent source_kind={src_kind} and t={t_val}")
                    continue
                expected_ep = u if t_val == 0 else w
                lab = _norm_label(v.get("label") or v.get("entity_id") or expected_ep)
                if lab != expected_ep:
                    bad.append(f"Category B SOLID_VERTEX label {lab} != endpoint {expected_ep} at t={t_val}")
                    continue
                desc = ("VERTEX", lab)
                p_verts[lab] += 1
                indexed_descs.append((poly_idx, desc))
            elif src_kind == "SOLID_EDGE_INTERSECTION":
                if not (F(0) < t_val < F(1)):
                    bad.append(f"Category B edge cut parameter t={t_val} not in (0, 1)")
                    continue
                a, b_lbl = sorted((u, w))
                t_canon = t_val if u == a else (F(1) - t_val)
                desc = ("EDGE", a, b_lbl, t_canon)
                p_edges[(a, b_lbl, t_canon)] += 1
                indexed_descs.append((poly_idx, desc))
            else:
                bad.append(f"Category B unknown source_kind={src_kind}")
        else:
            # Category A (DINH_CAT_CANH): distinguish solid vertices (t=0 or t=1) from interior edge cuts (0 < t < 1)
            xyz_p = (
                [F(str(c)) for c in v["xyz"]]
                if isinstance(v.get("xyz"), list) and len(v["xyz"]) == 3
                else _find_point_xyz(objects_by_id, v.get("label", ""))
            )
            xyz_u = _find_point_xyz(objects_by_id, u)
            xyz_w = _find_point_xyz(objects_by_id, w)
            t_val: F | None = None

            if xyz_p is not None and xyz_u is not None and xyz_w is not None:
                diff_idx = next((j for j in range(3) if xyz_w[j] != xyz_u[j]), None)
                if diff_idx is None:
                    bad.append(f"Category A edge [{u}, {w}] has identical endpoint coordinates")
                    continue
                t_coord = (xyz_p[diff_idx] - xyz_u[diff_idx]) / (xyz_w[diff_idx] - xyz_u[diff_idx])
                if any((F(1) - t_coord) * xyz_u[j] + t_coord * xyz_w[j] != xyz_p[j] for j in range(3)):
                    bad.append(f"Category A vertex {v.get('label')} at {xyz_p} not collinear with edge [{u}, {w}]")
                    continue
                if v.get("t") is not None and F(str(v["t"])) != t_coord:
                    bad.append(f"Category A vertex {v.get('label')} stated t={v['t']} != coordinate t={t_coord}")
                    continue
                t_val = t_coord
            elif v.get("t") is not None:
                t_val = F(str(v["t"]))
            elif _norm_label(v.get("label")) == u:
                t_val = F(0)
            elif _norm_label(v.get("label")) == w:
                t_val = F(1)
            else:
                bad.append(f"Category A vertex {v.get('label')} on [{u}, {w}] lacks coordinates and t parameter")
                continue

            if t_val == F(0):
                desc = ("VERTEX", u)
                p_verts[u] += 1
                indexed_descs.append((poly_idx, desc))
            elif t_val == F(1):
                desc = ("VERTEX", w)
                p_verts[w] += 1
                indexed_descs.append((poly_idx, desc))
            elif F(0) < t_val < F(1):
                a, b_lbl = sorted((u, w))
                t_canon = t_val if u == a else (F(1) - t_val)
                desc = ("EDGE", a, b_lbl, t_canon)
                p_edges[(a, b_lbl, t_canon)] += 1
                indexed_descs.append((poly_idx, desc))
            else:
                bad.append(f"Category A vertex {v.get('label')} parameter t={t_val} outside [0, 1]")

    if p_verts != o_verts:
        bad.append(f"solid-vertex set {sorted(p_verts.elements())} != oracle {sorted(o_verts.elements())}")
    if p_edges != o_edges:
        fmt = lambda c: sorted(f"{k[0]}-{k[1]}@{k[2]}" for k in c.elements())
        bad.append(f"interior edge cuts {fmt(p_edges)} != oracle {fmt(o_edges)}")
    if not bad:
        prod_ring = [d for _, d in sorted(indexed_descs, key=lambda item: item[0])]
        if not _same_cycle(prod_ring, oracle_ring):
            bad.append(f"polygon cyclic order {prod_ring} != oracle cycle {oracle_ring}")
    return bad


def _evaluate_scene3d_semantics(planner_dict: dict[str, Any], scene: dict[str, Any], text: str) -> dict[str, Any]:
    """Evaluate Section 10.A (Source-identity correctness) and Section 10.B (Pedagogical auxiliary display) separately."""
    aux_candidates: set[str] = set()
    for d in planner_dict.get("auxiliary") or []:
        aux_candidates |= set(d.get("labels") or []) | set(d.get("feet") or [])
        if d.get("label"):
            aux_candidates.add(d["label"])
    # Unicode-aware standalone token check so 'H' never matches inside Vietnamese 'Hình'
    aux_fresh = {
        a for a in aux_candidates
        if isinstance(a, str) and a and not re.search(rf"(?<![\w']){re.escape(a)}(?![\w'])", text)
    }

    source_identity_leaks: set[str] = set()
    pedagogical_aux_points: list[dict[str, Any]] = []

    for o in scene.get("objects") or []:
        oid = o.get("id", "")
        otype = o.get("type", "")
        if otype == "section" and o.get("identity_diagnostics"):
            source_identity_leaks.add(f"{oid}.identity_diagnostics:{o.get('identity_diagnostics')}")

        for a in sorted(aux_fresh):
            # Matches standalone token OR uppercase vertex inside concatenated polygon/plane name (e.g. 'HMN', 'MHP'),
            # while never matching Vietnamese capitalized words like 'Hình' (followed by lowercase 'ì') or 'H' inside 'H1'.
            pat = rf"(?<![a-zà-ỹ0-9_']){re.escape(a)}(?![a-zà-ỹ0-9_'])"
            if otype == "point3" and (_norm_label(oid) == _norm_label(a) or _norm_label(o.get("notation")) == _norm_label(a)):
                origin = o.get("origin")
                role = o.get("role")
                notation = o.get("notation")
                if origin == "given" or role == "Điểm cho trước":
                    source_identity_leaks.add(f"{oid}.false_given_origin:{a}")
                if notation is not None:
                    pedagogical_aux_points.append({
                        "id": oid,
                        "label": a,
                        "notation": notation,
                        "origin": origin,
                        "role": role,
                        "visibly_distinguished_from_given": (origin == "derived" and role == "Điểm dựng phụ"),
                    })
            elif otype in ("section", "plane3", "solid", "quantity"):
                for key in ("name", "label", "notation"):
                    s = o.get(key)
                    if isinstance(s, str) and re.search(pat, s):
                        source_identity_leaks.add(f"{oid}.{key}:{a}")

    return {
        "source_identity_leaks": sorted(source_identity_leaks),
        "pedagogical_auxiliary_points": pedagogical_aux_points,
        "r2_auxiliary_notation_observed": len(pedagogical_aux_points) > 0,
        "all_auxiliary_visibly_distinguished": all(
            p["visibly_distinguished_from_given"] for p in pedagogical_aux_points
        ),
    }


def score_observed_response(
    case: dict[str, Any],
    exp: dict[str, Any] | None,
    tax: dict[str, Any],
    r: Any,
    resp: dict[str, Any],
) -> dict[str, Any]:
    """Pure scoring function over an observed `(r, resp)` pair. Used by both live evaluation and synthetic self-tests."""
    payload = case["payload"]
    rec: dict[str, Any] = {
        "id": case["id"],
        "stratum": case["stratum"],
        "family": case["family"],
        "plane_relation": case["plane_relation"],
        "question_type": case["question_type"],
        "negative_class": case.get("negative_class"),
        "negative_origin": case.get("negative_origin"),
        "expected": case["expected_disposition"],
        "acceptable_categories": case.get("acceptable_categories") or [],
    }
    rd = resp.get("route_d") or {}
    env = resp.get("envelope") or {}
    served = (
        getattr(r, "status", None) == "SERVED"
        and rd.get("status") == "SERVED"
        and env.get("status") == "ok"
    )
    code = None if served else ((rd.get("refusal") or {}).get("code") or getattr(r, "code", None))
    reason = None if served else ((rd.get("refusal") or {}).get("detail") or getattr(r, "reason", None))
    cat, subcode = (None, None) if served else _code_category(code, reason, tax)
    rec.update(
        served=served,
        route_status=getattr(r, "status", None),
        route_code=getattr(r, "code", None),
        adapter4_status=rd.get("status"),
        envelope_status=env.get("status"),
        code=code,
        subcode=subcode,
        reason=reason,
        refusal_layer=None if served else ("route" if getattr(r, "status", None) != "SERVED" else "adapter4"),
        category=cat,
    )
    if not served:
        return _verdict(rec)

    try:
        checks: list[str] = []
        secs = rd.get("sections") or []
        n_decl = len(payload.get("derived_sections") or [])
        if len(secs) != n_decl or len(secs) == 0:
            checks.append(f"route_d.sections count {len(secs)} != declared {n_decl}")

        scene = env.get("scene3d") or {}
        objects_list = scene.get("objects") or []
        objects_by_id = {o["id"]: o for o in objects_list if isinstance(o, dict) and "id" in o}
        planner_dict = getattr(r, "planner", None) or {}

        sem = _evaluate_scene3d_semantics(planner_dict, scene, payload.get("problem_text", ""))
        rec["source_identity_leaks"] = sem["source_identity_leaks"]
        rec["pedagogical_auxiliary_points"] = sem["pedagogical_auxiliary_points"]
        rec["r2_auxiliary_notation_observed"] = sem["r2_auxiliary_notation_observed"]
        rec["all_auxiliary_visibly_distinguished"] = sem["all_auxiliary_visibly_distinguished"]

        if exp is None:
            checks.append("no oracle entry for a served case")
        else:
            sid = exp["section_id"]
            sec_objs = [o for o in objects_list if o.get("type") == "section"]
            obj = next((o for o in sec_objs if o.get("id") == f"td_{sid}"), sec_objs[0] if len(sec_objs) == 1 else None)
            if obj is None:
                checks.append(f"no scene section object for {sid}")
            else:
                if obj.get("closed") is False:
                    checks.append(f"scene section object td_{sid} is not closed")
                if len(obj.get("polygon") or []) != exp["vertex_count"]:
                    checks.append(f"vertex count {len(obj.get('polygon') or [])} != oracle {exp['vertex_count']}")

                # Solid identity check (Control 12)
                if exp.get("solid"):
                    dep_solids = [
                        o for o in objects_list
                        if o.get("type") == "solid" and o.get("id") in (obj.get("depends") or [])
                    ]
                    if not dep_solids:
                        dep_solids = [o for o in objects_list if o.get("type") == "solid"]
                    if not dep_solids:
                        checks.append("no solid object in scene3d")
                    else:
                        got_solid = _norm_label(dep_solids[0].get("notation"))
                        exp_solid = _norm_label(exp["solid"])
                        if got_solid != exp_solid:
                            checks.append(f"solid identity {got_solid!r} != oracle {exp_solid!r}")

            sec = next((s for s in secs if s.get("section_id") == sid), secs[0] if len(secs) == 1 else None)
            if sec is None:
                checks.append(f"missing section certificate entry for {sid}")
            else:
                # Section certificate presence check (Control 13)
                cert = sec.get("closure_certificate")
                if not isinstance(cert, dict) or cert.get("verified") is not True or not cert.get("rule"):
                    checks.append("missing or unverified section closure_certificate")

                is_cat_b = (
                    sec.get("certificate_category") == "ENGINE_DERIVED_SECTION"
                    or "certificate_version" in sec
                )
                obs_cat = "ENGINE_DERIVED_SECTION" if is_cat_b else "DINH_CAT_CANH"
                rec["certificate_category"] = [obs_cat]

                # Category A/B certificate mixing check (Control 14)
                exp_cat = exp.get("expected_certificate_category")
                if exp_cat and obs_cat != exp_cat:
                    checks.append(f"Category A/B certificate mismatch: observed {obs_cat} != expected {exp_cat}")
                dinh_cat_goals = {
                    d.get("goal")
                    for d in (planner_dict.get("auxiliary") or [])
                    if isinstance(d, dict) and d.get("rule") == "dinh-cat-canh"
                }
                if is_cat_b:
                    if sec.get("certificate_version") != "plane-section-certificate/1":
                        checks.append(f"Category B certificate_version={sec.get('certificate_version')!r} invalid")
                    if sid in dinh_cat_goals:
                        checks.append("Category A/B mixing: Category B certificate on DINH_CAT_CANH planner goal")
                    if any(v.get("stated") is True for v in (sec.get("vertices") or [])):
                        checks.append("Category A/B mixing: Category B vertex has stated=True")
                    if exp.get("solid") and sec.get("solid") and _norm_label(sec["solid"]) != _norm_label(exp["solid"]):
                        checks.append(f"Category B certificate solid {sec.get('solid')!r} != oracle {exp['solid']!r}")
                    if isinstance(cert, dict) and cert.get("area_squared") is not None and exp.get("area_squared") is not None:
                        if F(str(cert["area_squared"])) != F(str(exp["area_squared"])):
                            checks.append(
                                f"certificate area² {cert['area_squared']} != oracle {exp['area_squared']}"
                            )
                else:
                    if "certificate_version" in sec or sec.get("certificate_category") == "ENGINE_DERIVED_SECTION":
                        checks.append("Category A/B mixing: Category A section carries Category B version/category")

                if obj is not None:
                    checks += _check_section_boundary(sec, obj, objects_by_id, exp, is_cat_b)

            # Area squared check (Control 11)
            if exp.get("area_goal_id"):
                key = f"kq_{exp['area_goal_id']}"
                exec_res = getattr(r, "exec_result", None)
                mem = getattr(exec_res, "final_memory", None) or {}
                if key not in mem:
                    checks.append(f"area answer {key} missing from final_memory")
                else:
                    got = _square(mem[key])
                    rec["area_squared"] = str(got)
                    if got != F(str(exp["area_squared"])):
                        checks.append(f"area² {got} != oracle {exp['area_squared']}")

        rec["oracle_mismatches"] = checks
    except Exception:
        rec["outcome"] = "HARNESS_ERROR"
        rec["detail"] = traceback.format_exc(limit=3)[-500:]
        return rec
    return _verdict(rec)


def score_case(case: dict[str, Any], exp: dict[str, Any] | None, tax: dict[str, Any]) -> dict[str, Any]:
    if str(ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(ROOT / "backend"))
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route  # noqa: E402

    payload = deepcopy(case["payload"])
    try:
        r = run_typed_fact_next_v2_route(payload)
        resp = build_adapter4_response(r, payload["problem_text"])
    except Exception as e:
        rec = {
            "id": case["id"],
            "stratum": case["stratum"],
            "family": case["family"],
            "plane_relation": case["plane_relation"],
            "question_type": case["question_type"],
            "negative_class": case.get("negative_class"),
            "negative_origin": case.get("negative_origin"),
            "expected": case["expected_disposition"],
            "acceptable_categories": case.get("acceptable_categories") or [],
            "outcome": "PRODUCT_EXCEPTION",
            "served": False,
            "code": type(e).__name__,
            "category": "INTERNAL_OR_VALIDATION",
            "detail": str(e)[:300],
        }
        return _verdict(rec)
    return score_observed_response(case, exp, tax, r, resp)


def _verdict(rec: dict[str, Any]) -> dict[str, Any]:
    if rec.get("outcome") == "HARNESS_ERROR":
        return rec
    if rec.get("outcome") == "PRODUCT_EXCEPTION":
        rec["product_exception"] = True
    if rec["expected"] == "SERVE":
        if rec["served"]:
            rec["outcome"] = "SERVED_CORRECT" if not rec.get("oracle_mismatches") else "WRONG_SERVED"
        else:
            rec["outcome"] = "FALSE_REFUSAL"
    else:
        if rec["served"]:
            rec["outcome"] = "WRONG_SERVED"
        elif rec.get("category") in rec["acceptable_categories"] and rec.get("category") != "INTERNAL_OR_VALIDATION":
            rec["outcome"] = "REFUSED_CORRECT_REASON"
        else:
            rec["outcome"] = "REFUSED_REASON_DISAGREEMENT"
    return rec


def _tally(rows: list[dict[str, Any]]) -> dict[str, Any]:
    c = Counter(r["outcome"] for r in rows)
    n = len(rows)
    serve = [r for r in rows if r["expected"] == "SERVE"]
    ref = [r for r in rows if r["expected"] == "REFUSE"]
    sc = sum(r["outcome"] == "SERVED_CORRECT" for r in serve)
    fr = sum(r["outcome"] == "FALSE_REFUSAL" for r in serve)
    ws_s = sum(r["outcome"] == "WRONG_SERVED" for r in serve)
    ws_r = sum(r["outcome"] == "WRONG_SERVED" for r in ref)
    rc = sum(r["outcome"] == "REFUSED_CORRECT_REASON" for r in ref)
    refused = sum(not r.get("served") for r in ref)
    prod_exc = sum(bool(r.get("product_exception")) for r in rows)
    return {
        "n": n,
        "outcomes": dict(c),
        "serve_cases": len(serve),
        "served_correct": sc,
        "served_correct_ci95": wilson(sc, len(serve)),
        "false_refusals": fr,
        "false_refusal_ci95": wilson(fr, len(serve)),
        "wrong_served_on_serve_cases": ws_s,
        "refuse_cases": len(ref),
        "refuse_cases_refused": refused,
        "refuse_cases_refused_ci95": wilson(refused, len(ref)),
        "refused_correct_reason": rc,
        "reason_agreement_ci95": wilson(rc, refused),
        "wrong_served_on_refuse_cases": ws_r,
        "wrong_served_total": ws_s + ws_r,
        "wrong_served_ci95": wilson(ws_s + ws_r, n),
        "internal_exceptions": prod_exc,
    }


def main(out_dir: Path) -> dict[str, Any]:
    tax = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    rows = [score_case(c, expected.get(c["id"]), tax) for c in corpus["cases"]]

    served_serve = [r for r in rows if r["expected"] == "SERVE" and r.get("served")]
    by = lambda key: {
        k: _tally([r for r in rows if (r.get(key) or "none") == k])
        for k in sorted({r.get(key) or "none" for r in rows})
    }
    summary = {
        "schema": "HOLDOUT_WAVE2_TRACK_A_SUMMARY/1",
        "live_provider_calls": 0,
        "product_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip(),
        "product_tree_backend_app": subprocess.run(
            ["git", "rev-parse", "HEAD:backend/app"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip(),
        "overall": _tally(rows),
        "exact_oracle_agreement_among_served_serve_cases": {
            "agree": sum(not r.get("oracle_mismatches") for r in served_serve),
            "served": len(served_serve),
            "ci95": wilson(sum(not r.get("oracle_mismatches") for r in served_serve), len(served_serve)),
        },
        "adapter_validation": {
            "route_served": sum(r.get("route_status") == "SERVED" for r in rows),
            "adapter4_served_given_route_served": sum(r.get("served", False) for r in rows),
            "certificate_or_preview_failures": sum((r.get("code") or "").startswith("PREVIEW_") for r in rows),
        },
        "scene3d_semantics": {
            "served_cases_checked": sum("source_identity_leaks" in r for r in rows),
            "track_10a_source_identity_leak_cases": [
                r["id"] for r in rows if r.get("source_identity_leaks")
            ],
            "track_10b_r2_auxiliary_notation_cases": [
                r["id"] for r in rows if r.get("r2_auxiliary_notation_observed")
            ],
            "track_10b_all_auxiliary_visibly_distinguished": all(
                r.get("all_auxiliary_visibly_distinguished", True)
                for r in rows
                if "all_auxiliary_visibly_distinguished" in r
            ),
        },
        "harness_errors": [r["id"] for r in rows if r["outcome"] == "HARNESS_ERROR"],
        "by_stratum": by("stratum"),
        "by_family": by("family"),
        "by_plane_relation": by("plane_relation"),
        "by_question_type": by("question_type"),
        "by_negative_class": by("negative_class"),
        "false_refusals_by_category": dict(
            Counter(r.get("category") for r in rows if r["outcome"] == "FALSE_REFUSAL")
        ),
        "false_refusals_by_code": dict(
            Counter(r.get("code") for r in rows if r["outcome"] == "FALSE_REFUSAL")
        ),
        "refused_disagreements_by_code": dict(
            Counter(r.get("code") for r in rows if r["outcome"] == "REFUSED_REASON_DISAGREEMENT")
        ),
    }
    track_b = {
        "schema": "HOLDOUT_WAVE2_TRACK_B/1",
        "representability": dict(Counter(c["track_b"]["representability"] for c in corpus["cases"])),
        "by_disposition": {
            d: dict(
                Counter(
                    c["track_b"]["representability"]
                    for c in corpus["cases"]
                    if c["expected_disposition"] == d
                )
            )
            for d in ("SERVE", "REFUSE")
        },
        "cases": [
            {
                "id": c["id"],
                "stratum": c["stratum"],
                "expected_disposition": c["expected_disposition"],
                "representability": c["track_b"]["representability"],
                "note": c["track_b"].get("note"),
            }
            for c in corpus["cases"]
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in (
        ("track-a.json", {"cases": rows}),
        ("summary.json", summary),
        ("track-b.json", track_b),
    ):
        with (out_dir / name).open("x", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    s = main(Path(sys.argv[1]))
    o = s["overall"]
    print(
        f"cases={o['n']} serve={o['serve_cases']} served_correct={o['served_correct']} "
        f"false_refusals={o['false_refusals']} refuse={o['refuse_cases']} "
        f"refused={o['refuse_cases_refused']} correct_reason={o['refused_correct_reason']} "
        f"wrong_served={o['wrong_served_total']} harness_errors={len(s['harness_errors'])}"
    )
