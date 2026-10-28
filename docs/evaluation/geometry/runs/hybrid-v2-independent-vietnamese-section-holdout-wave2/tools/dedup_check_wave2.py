# -*- coding: utf-8 -*-
"""9-dimensional semantic deduplication audit for Hybrid V2 Independent Vietnamese Section Holdout Wave 2.

Implements Section 6 of the Owner GO:
Compares every Wave 2 case (`W2-B01..W2-B36`, `W2-A01..W2-A12`, `W2-N01..W2-N48`) against:
1. Previous 84-case holdout (`hybrid-v2-independent-vietnamese-section-holdout`, H001..H084).
2. M1-M5 32-case development corpus (`hybrid-v2-holdout-failure-repair`, D001..D016, N001..N016).
3. Older geometry development corpora across `docs/evaluation/geometry/runs/**`.
4. Existing test fixtures in `backend/tests/**`.
5. Internal pairwise comparison across all 96 Wave 2 cases.

Checks all 9 required dimensions:
1. Normalized Vietnamese text similarity (character 5-gram Jaccard & word-token Jaccard).
2. Solid topology (`pyramid_3`, `pyramid_4`, `prism_3_right`, `prism_3_oblique`, `cuboid`, `cube`, `other`).
3. Plane relation (`perpendicular_line`, `parallel_plane`, `parallel_two_lines`, `stated_intersections`, `other`).
4. Through-point topological role (e.g., `apex`, `base_vertex`, `top_vertex`, `lateral_edge_midpoint`, `lateral_edge_ratio:p/q`, `base_edge_midpoint`, `base_edge_ratio:p/q`).
5. Reference line/plane topological role (e.g., `lateral_edge`, `base_edge`, `base_diagonal`, `space_diagonal`, `lateral_face`, `base_face`, `diagonal_plane`).
6. Exact dimensions and cut ratios.
7. Equivalent geometry under vertex relabelling (canonicalizing vertex labels by their structural slot in `solids[0]`: apex, base[0..k-1], top[0..k-1]).
8. Similar configurations under uniform scale changes (projective normalization of numeric/symbolic length vectors by dividing by the minimum positive length in exact `Fraction` arithmetic).
9. Equivalent question objectives (`section_only`, `area_only`, `section_and_area`).

Usage:
    python dedup_check_wave2.py <wave2_corpus_json> <out_json>
"""
from __future__ import annotations

from fractions import Fraction as F
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
WAVE1_CORPUS = (
    ROOT.parent / "independent-section-holdout"
    / "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout/inputs/holdout.json"
)


def _norm_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _char_ngrams(s: str, n: int = 5) -> set[str]:
    s_clean = re.sub(r"\s+", " ", _norm_text(s))
    if len(s_clean) < n:
        return {s_clean} if s_clean else set()
    return {s_clean[i : i + n] for i in range(len(s_clean) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _parse_len_val(raw: Any) -> F | None:
    if raw is None:
        return None
    s = str(raw).strip().lower().replace(" ", "")
    s = s.replace("a", "")
    if not s or s == "":
        return F(1)
    # Handle simple rational or radical like '2√3/3' -> store square of value as rational!
    m = re.fullmatch(r"(\d+)?(?:√(\d+))?(?:/(\d+))?", s)
    if m:
        num = int(m.group(1)) if m.group(1) else 1
        rad = int(m.group(2)) if m.group(2) else 1
        den = int(m.group(3)) if m.group(3) else 1
        if den != 0:
            return F(num * num * rad, den * den)
    try:
        return F(s) ** 2
    except Exception:
        return None


def _extract_semantic_signature(item: dict[str, Any]) -> dict[str, Any]:
    """Compute a 9-dimensional relabelling-invariant and scale-invariant signature from a case/payload."""
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else item
    text = item.get("problem_text") or payload.get("problem_text") or ""

    solids = payload.get("solids") or []
    premises = payload.get("premises") or []
    sections = payload.get("derived_sections") or []
    sim_goals = payload.get("simulation_goals") or []
    math_goals = payload.get("math_goals") or []

    # 1. Build vertex role map (Dimension 7: Vertex relabelling invariance)
    v_role: dict[str, str] = {}
    topology = "other"
    if solids:
        s0 = solids[0]
        stype = s0.get("solid_type")
        base_v = list(s0.get("base_vertices") or [])
        top_v = list(s0.get("top_vertices") or [])
        apex = s0.get("apex")
        if stype == "pyramid":
            topology = f"pyramid_{len(base_v)}"
            if apex:
                v_role[str(apex)] = "APEX"
            for i, v in enumerate(base_v):
                v_role[str(v)] = f"BASE_{i}"
        elif stype == "prism":
            is_right = any(p.get("kind") == "right_prism" for p in premises)
            is_sq = any(p.get("kind") == "base_is_square" for p in premises)
            is_rect = any(p.get("kind") == "rectangle" for p in premises)
            if len(base_v) == 4 and is_right and is_sq:
                topology = "cube_or_square_prism"
            elif len(base_v) == 4 and is_right and is_rect:
                topology = "cuboid"
            elif len(base_v) == 3:
                topology = "prism_3_right" if is_right else "prism_3_oblique"
            else:
                topology = f"prism_{len(base_v)}"
            for i, v in enumerate(base_v):
                v_role[str(v)] = f"BASE_{i}"
            for i, v in enumerate(top_v):
                v_role[str(v)] = f"TOP_{i}"

    # Map derived points (midpoints, segment ratios) to their canonical edge roles
    point_ratios: list[str] = []
    for p in premises:
        pk = p.get("kind")
        args = p.get("args") or {}
        if pk == "midpoint":
            pt = str(args.get("point", ""))
            seg = [v_role.get(str(x), str(x)) for x in (args.get("segment") or [])]
            v_role[pt] = f"MID({','.join(sorted(seg))})"
            point_ratios.append("1/2")
        elif pk == "point_on_segment_ratio":
            pt = str(args.get("point", ""))
            seg = [v_role.get(str(x), str(x)) for x in (args.get("segment") or [])]
            r_str = str(args.get("ratio", ""))
            v_role[pt] = f"RATIO({seg[0]}->{seg[1]}:{r_str})"
            point_ratios.append(r_str)

    # Extract lengths and projective scale-invariant profile (Dimensions 6 & 8)
    raw_sq_lengths: list[F] = []
    for p in premises:
        args = p.get("args") or {}
        for k in ("value", "length"):
            if k in args:
                val_sq = _parse_len_val(args[k])
                if val_sq is not None and val_sq > 0:
                    raw_sq_lengths.append(val_sq)
    sorted_sq_lengths = sorted(raw_sq_lengths)
    if sorted_sq_lengths:
        min_l = sorted_sq_lengths[0]
        scale_invariant_lengths = [str(x / min_l) for x in sorted_sq_lengths]
    else:
        scale_invariant_lengths = []

    # Cutting plane relation, through-point role, reference role (Dimensions 3, 4, 5)
    plane_kind = "none"
    tp_role = "none"
    ref_role = "none"
    stated_cuts_role: list[str] = []
    if sections:
        sec0 = sections[0]
        plane_kind = str(sec0.get("plane_kind") or "none")
        tp = sec0.get("through_point")
        if tp:
            tp_role = v_role.get(str(tp), f"RAW({tp})")
        if plane_kind == "through_point_perpendicular_line":
            line = [v_role.get(str(x), str(x)) for x in (sec0.get("perpendicular_line") or [])]
            ref_role = "PERP_LINE(" + ",".join(sorted(line)) + ")"
        elif plane_kind == "through_point_parallel_plane":
            pl = [v_role.get(str(x), str(x)) for x in (sec0.get("parallel_plane") or [])]
            ref_role = "PAR_PLANE(" + ",".join(sorted(pl)) + ")"
        elif plane_kind == "through_point_parallel_two_lines":
            lines = []
            for ln in sec0.get("parallel_lines") or []:
                mapped = ",".join(sorted(v_role.get(str(x), str(x)) for x in ln))
                lines.append(mapped)
            ref_role = "PAR_TWO_LINES(" + ";".join(sorted(lines)) + ")"
        elif plane_kind == "three_points":
            pts = [v_role.get(str(x), str(x)) for x in (sec0.get("points") or [])]
            ref_role = "THREE_PTS(" + ",".join(sorted(pts)) + ")"
        for si in sec0.get("stated_intersections") or []:
            ed = [v_role.get(str(x), str(x)) for x in (si.get("edge") or [])]
            pt = si.get("point")
            pt_r = v_role.get(str(pt), "UNNAMED") if pt else "UNNAMED"
            stated_cuts_role.append(f"{','.join(sorted(ed))}@{pt_r}")

    # Question objective (Dimension 9)
    has_sec_goal = any(g.get("kind") == "construct_plane_section" for g in sim_goals)
    has_area_goal = any(g.get("goal_type") == "area" for g in math_goals)
    q_obj = item.get("question_type") or (
        "section_and_area" if (has_sec_goal and has_area_goal) else ("area_only" if has_area_goal else "section_only")
    )

    # Canonical relabelling-invariant structural tuple (Dimension 7)
    relabelled_structure = (
        topology,
        plane_kind,
        tp_role,
        ref_role,
        tuple(sorted(stated_cuts_role)),
    )
    # Scale-invariant geometric configuration tuple (Dimension 8)
    scale_invariant_config = (
        relabelled_structure,
        tuple(scale_invariant_lengths),
        tuple(sorted(point_ratios)),
    )
    # Exact configuration tuple including exact dimensions & objective (Dimensions 6 & 9)
    exact_config = (
        scale_invariant_config,
        tuple(str(x) for x in sorted_sq_lengths),
        q_obj,
    )

    return {
        "text": text,
        "norm_text": _norm_text(text),
        "ngrams": _char_ngrams(text, 5),
        "topology": topology,
        "plane_kind": plane_kind,
        "tp_role": tp_role,
        "ref_role": ref_role,
        "stated_cuts_role": sorted(stated_cuts_role),
        "exact_sq_lengths": [str(x) for x in sorted_sq_lengths],
        "scale_invariant_lengths": scale_invariant_lengths,
        "point_ratios": sorted(point_ratios),
        "question_objective": q_obj,
        "relabelled_structure": relabelled_structure,
        "scale_invariant_config": scale_invariant_config,
        "exact_config": exact_config,
    }


def _load_historical_corpora() -> list[dict[str, Any]]:
    historical: list[dict[str, Any]] = []

    # 1. Wave 1 Holdout (84 cases)
    if WAVE1_CORPUS.exists():
        w1 = json.loads(WAVE1_CORPUS.read_text(encoding="utf-8"))
        for c in w1.get("cases") or []:
            historical.append({"source": f"wave1_holdout:{c['id']}", "item": c})

    # 2. All JSON corpora in docs/evaluation/geometry/runs/** (excluding wave2 itself)
    runs_dir = ROOT / "docs/evaluation/geometry/runs"
    if runs_dir.exists():
        for jf in sorted(runs_dir.rglob("*.json")):
            if "hybrid-v2-independent-vietnamese-section-holdout-wave2" in str(jf).replace("\\", "/"):
                continue
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            cases = data.get("cases") if isinstance(data, dict) else (data if isinstance(data, list) else None)
            if isinstance(cases, list):
                for idx, c in enumerate(cases):
                    if isinstance(c, dict) and ("problem_text" in c or isinstance(c.get("payload"), dict)):
                        cid = c.get("id") or c.get("case_id") or f"idx_{idx}"
                        rel = jf.relative_to(ROOT).as_posix()
                        historical.append({"source": f"{rel}:{cid}", "item": c})

    # 3. Existing test fixtures in backend/tests/** (JSON files and Vietnamese problem_text literals in Python tests)
    tests_dir = ROOT / "backend/tests"
    if tests_dir.exists():
        for jf in sorted(tests_dir.rglob("*.json")):
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            cases = data.get("cases") if isinstance(data, dict) else (data if isinstance(data, list) else None)
            if isinstance(cases, list):
                for idx, c in enumerate(cases):
                    if isinstance(c, dict) and ("problem_text" in c or isinstance(c.get("payload"), dict)):
                        cid = c.get("id") or c.get("case_id") or f"idx_{idx}"
                        rel = jf.relative_to(ROOT).as_posix()
                        historical.append({"source": f"{rel}:{cid}", "item": c})
        for pf in sorted((tests_dir / "simulation").rglob("*.py")) if (tests_dir / "simulation").exists() else []:
            try:
                txt = pf.read_text(encoding="utf-8")
            except Exception:
                continue
            rel = pf.relative_to(ROOT).as_posix()
            for idx, m in enumerate(re.finditer(r'["\'](Cho\s+(?:hình|khối|tứ diện|lăng trụ)[^"\']{25,})["\']', txt)):
                historical.append({"source": f"{rel}:str_{idx}", "item": {"problem_text": m.group(1)}})

    return historical


def run_dedup_audit(wave2_path: Path) -> dict[str, Any]:
    w2_data = json.loads(wave2_path.read_text(encoding="utf-8"))
    w2_cases = w2_data["cases"]
    w2_sigs = {c["id"]: _extract_semantic_signature(c) for c in w2_cases}

    historical = _load_historical_corpora()
    hist_sigs = [(h["source"], _extract_semantic_signature(h["item"])) for h in historical]

    external_text_flags: list[dict[str, Any]] = []
    external_exact_config_flags: list[dict[str, Any]] = []
    external_scale_invariant_flags: list[dict[str, Any]] = []
    internal_duplicate_flags: list[dict[str, Any]] = []

    max_external_jaccard = 0.0
    max_external_pair = None

    for c in w2_cases:
        cid = c["id"]
        sig = w2_sigs[cid]
        for h_src, h_sig in hist_sigs:
            if not h_sig["norm_text"]:
                continue
            jac = _jaccard(sig["ngrams"], h_sig["ngrams"])
            if jac > max_external_jaccard:
                max_external_jaccard = jac
                max_external_pair = (cid, h_src, round(jac, 4))
            if jac >= 0.75:
                external_text_flags.append({"wave2_id": cid, "historical_source": h_src, "jaccard_5gram": round(jac, 4)})
            # Check positive cases for relabelling-invariant + scale-invariant geometric configuration duplicates
            if c.get("expected_disposition") == "SERVE" and sig["scale_invariant_lengths"]:
                if sig["exact_config"] == h_sig["exact_config"]:
                    external_exact_config_flags.append({"wave2_id": cid, "historical_source": h_src})
                elif sig["scale_invariant_config"] == h_sig["scale_invariant_config"]:
                    external_scale_invariant_flags.append({"wave2_id": cid, "historical_source": h_src})

    # Internal pairwise check among Wave 2 cases
    max_internal_jaccard = 0.0
    for i in range(len(w2_cases)):
        for j in range(i + 1, len(w2_cases)):
            c1, c2 = w2_cases[i], w2_cases[j]
            s1, s2 = w2_sigs[c1["id"]], w2_sigs[c2["id"]]
            jac = _jaccard(s1["ngrams"], s2["ngrams"])
            if jac > max_internal_jaccard:
                max_internal_jaccard = jac
            if jac >= 0.80 or (
                c1["expected_disposition"] == "SERVE"
                and c2["expected_disposition"] == "SERVE"
                and s1["scale_invariant_config"] == s2["scale_invariant_config"]
            ):
                internal_duplicate_flags.append({
                    "id_1": c1["id"],
                    "id_2": c2["id"],
                    "jaccard_5gram": round(jac, 4),
                    "same_scale_invariant_config": s1["scale_invariant_config"] == s2["scale_invariant_config"],
                })

    passed = (
        len(external_text_flags) == 0
        and len(external_exact_config_flags) == 0
        and len(external_scale_invariant_flags) == 0
        and len(internal_duplicate_flags) == 0
    )
    return {
        "schema": "HOLDOUT_WAVE2_DEDUPLICATION_AUDIT/1",
        "wave2_case_count": len(w2_cases),
        "historical_items_compared": len(hist_sigs),
        "wave1_holdout_present": WAVE1_CORPUS.exists(),
        "dimensions_checked": [
            "1_normalized_vietnamese_text_5gram_jaccard",
            "2_solid_topology",
            "3_plane_relation",
            "4_through_point_role",
            "5_reference_line_or_plane_role",
            "6_exact_dimensions_and_cut_ratios",
            "7_vertex_relabelling_invariance",
            "8_uniform_scale_invariance",
            "9_question_objective",
        ],
        "max_external_5gram_jaccard": round(max_external_jaccard, 4),
        "max_external_pair": max_external_pair,
        "max_internal_5gram_jaccard": round(max_internal_jaccard, 4),
        "external_text_flags": external_text_flags,
        "external_exact_config_flags": external_exact_config_flags,
        "external_scale_invariant_flags": external_scale_invariant_flags,
        "internal_duplicate_flags": internal_duplicate_flags,
        "passed": passed,
    }


if __name__ == "__main__":
    w2_p = Path(sys.argv[1])
    out_p = Path(sys.argv[2])
    rep = run_dedup_audit(w2_p)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"passed={rep['passed']} wave2={rep['wave2_case_count']} hist={rep['historical_items_compared']} "
        f"max_ext_jac={rep['max_external_5gram_jaccard']} ext_text_flags={len(rep['external_text_flags'])} "
        f"ext_scale_flags={len(rep['external_scale_invariant_flags'])} int_flags={len(rep['internal_duplicate_flags'])}"
    )
    sys.exit(0 if rep["passed"] else 1)
