# -*- coding: utf-8 -*-
"""9-dimensional + symmetry/solution-invariant semantic deduplication audit for Holdout Wave 3.

Implements Section 6 of the Owner GO:
Compares every Wave 3 case (`W3-B01..W3-B54`, `W3-A01..W3-A18`, `W3-N01..W3-N72`) against:
1. Holdout Wave 1 (`hybrid-v2-independent-vietnamese-section-holdout`, 84 cases).
2. Holdout Wave 2 (`hybrid-v2-independent-vietnamese-section-holdout-wave2`, 96 cases).
3. W2-M1/M2/M3 development (`hybrid-v2-holdout-failure-repair`, 32 cases).
4. Source Gate `/19` development (`hybrid-v2-wave2-source-gate-language-generalization`).
5. W2-M4 development (`hybrid-v2-w2-m4-exact-radical-normalization`).
6. W2-M5 development (`hybrid-v2-w2-m5-adapter4-category-a-identity-repair`).
7. Backend test fixtures (`backend/tests/**`).
8. All other committed evaluation runs (`docs/evaluation/geometry/runs/**`).
9. Internal pairwise comparison across all 144 Wave 3 cases.

Checks all 9 required dimensions + dihedral symmetry & oracle solution invariance:
1. Exact normalized Vietnamese text match.
2. Character 5-gram Jaccard similarity (< 0.75 external, < 0.80 internal, < 0.75 internal positive).
3. Solid topology (`pyramid_3`, `pyramid_4`, `prism_3_right`, `prism_3_oblique`, `cuboid`, `cube`, `other`).
4. Cutting-plane construction (`plane_kind`, `through_point` topological role, reference line/plane topological role).
5. Vertex-relabelling invariance under all dihedral base symmetries (rotations and reflections of base/top cycles).
6. Scale invariance (projective normalization of squared metric lengths by dividing by the minimum positive squared length).
7. Exact cut-ratio profile.
8. Mathematical goal / question type (`section_only`, `area_only`, `section_and_area`).
9. Solution / Oracle invariance under symmetry and coordinate change (`vertex_count`, sorted canonical cut parameters
   `min(t, 1-t)`, and dimensionless `area_squared / (min_length_squared ** 2)`).

Usage:
    python dedup_check_wave3.py <wave3_corpus_json> <out_json>
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
WAVE2_CORPUS = (
    ROOT.parent / "independent-section-holdout-wave2"
    / "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/inputs/holdout-wave2.json"
)
WAVE2_EXPECTED = (
    ROOT.parent / "independent-section-holdout-wave2"
    / "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/oracle/expected.json"
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


def _dihedral_orders(seq: list[str]) -> list[list[str]]:
    if not seq:
        return [[]]
    k = len(seq)
    orders: list[list[str]] = []
    for base in (seq, list(reversed(seq))):
        for i in range(k):
            orders.append(base[i:] + base[:i])
    return orders


def _extract_semantic_signature(item: dict[str, Any], exp: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compute a 9-dimensional relabelling-, dihedral-, and scale-invariant signature from a case/payload."""
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else item
    text = item.get("problem_text") or payload.get("problem_text") or ""

    solids = payload.get("solids") or []
    premises = payload.get("premises") or []
    sections = payload.get("derived_sections") or []
    sim_goals = payload.get("simulation_goals") or []
    math_goals = payload.get("math_goals") or []

    topology = "other"
    base_v: list[str] = []
    top_v: list[str] = []
    apex: str | None = None
    stype = None

    if solids:
        s0 = solids[0]
        stype = s0.get("solid_type")
        notation = str(s0.get("notation") or "")
        base_v = list(s0.get("base_vertices") or [])
        top_v = list(s0.get("top_vertices") or [])
        apex = s0.get("apex")
        if not base_v and "." in notation:
            parts = notation.split(".", 1)
            tok = lambda s: re.findall(r"[A-Za-z]\d*(?:'+|′+|″+)?", s)
            if stype == "pyramid":
                ap_t = tok(parts[0])
                apex = ap_t[0] if ap_t else parts[0]
                base_v = tok(parts[1])
            elif stype == "prism":
                base_v = tok(parts[0])
                top_v = tok(parts[1])

        if stype == "pyramid":
            topology = f"pyramid_{len(base_v)}"
        elif stype == "prism":
            is_right = any(p.get("kind") == "right_prism" for p in premises)
            is_sq = any(p.get("kind") in ("base_is_square", "regular_polygon") for p in premises)
            is_rect = any(p.get("kind") in ("rectangle", "base_is_rectangle") for p in premises)
            if len(base_v) == 4 and is_right and is_sq:
                topology = "cube_or_square_prism"
            elif len(base_v) == 4 and is_right and is_rect:
                topology = "cuboid"
            elif len(base_v) == 3:
                topology = "prism_3_right" if is_right else "prism_3_oblique"
            else:
                topology = f"prism_{len(base_v)}"

    def _structure_for_order(b_ord: list[str], t_ord: list[str]) -> tuple:
        v_role: dict[str, str] = {}
        if stype == "pyramid":
            if apex:
                v_role[str(apex)] = "APEX"
            for i, v in enumerate(b_ord):
                v_role[str(v)] = f"BASE_{i}"
        elif stype == "prism":
            for i, v in enumerate(b_ord):
                v_role[str(v)] = f"BASE_{i}"
            for i, v in enumerate(t_ord):
                v_role[str(v)] = f"TOP_{i}"

        for p in premises:
            pk = p.get("kind")
            args = p.get("args") or {}
            if pk in ("midpoint", "point_is_midpoint"):
                pt = str(args.get("point", ""))
                seg = [v_role.get(str(x), str(x)) for x in (args.get("segment") or [])]
                v_role[pt] = f"MID({','.join(sorted(seg))})"
            elif pk in ("point_on_segment_ratio", "divide_segment", "point_divides_segment"):
                pt = str(args.get("point", ""))
                seg = [v_role.get(str(x), str(x)) for x in (args.get("segment") or [])]
                r_str = str(args.get("ratio", ""))
                if len(seg) == 2:
                    v_role[pt] = f"RATIO({seg[0]}->{seg[1]}:{r_str})"

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
                for ln in (sec0.get("parallel_lines") or [sec0.get("parallel_line_a") or [], sec0.get("parallel_line_b") or []]):
                    if ln:
                        mapped = ",".join(sorted(v_role.get(str(x), str(x)) for x in ln))
                        lines.append(mapped)
                ref_role = "PAR_TWO_LINES(" + ";".join(sorted(lines)) + ")"
            for si in sec0.get("stated_intersections") or []:
                ed = [v_role.get(str(x), str(x)) for x in (si.get("edge") or [])]
                pt = si.get("point")
                pt_r = "NAMED" if pt else "UNNAMED"
                stated_cuts_role.append(f"{','.join(sorted(ed))}@{pt_r}")
        return (topology, plane_kind, tp_role, ref_role, tuple(sorted(stated_cuts_role)))

    # Canonicalize over all dihedral symmetries of the base
    if base_v:
        b_orders = _dihedral_orders(base_v)
        if stype == "prism" and len(top_v) == len(base_v):
            t_orders = _dihedral_orders(top_v)
            candidates = [_structure_for_order(b_o, t_o) for b_o, t_o in zip(b_orders, t_orders)]
        else:
            candidates = [_structure_for_order(b_o, []) for b_o in b_orders]
        relabelled_structure = min(candidates)
    else:
        relabelled_structure = _structure_for_order([], [])

    point_ratios: list[str] = []
    raw_sq_lengths: list[F] = []
    for p in premises:
        pk = p.get("kind")
        args = p.get("args") or {}
        if pk in ("midpoint", "point_is_midpoint"):
            point_ratios.append("1/2")
        elif pk in ("point_on_segment_ratio", "divide_segment", "point_divides_segment"):
            r_raw = str(args.get("ratio", ""))
            try:
                rf = F(r_raw)
                point_ratios.append(str(min(rf, F(1) - rf)))
            except Exception:
                point_ratios.append(r_raw)
        for k in ("value", "length", "side"):
            if k in args:
                val_sq = _parse_len_val(args[k])
                if val_sq is not None and val_sq > 0:
                    raw_sq_lengths.append(val_sq)

    sorted_sq_lengths = sorted(raw_sq_lengths)
    if sorted_sq_lengths:
        min_l = sorted_sq_lengths[0]
        scale_invariant_lengths = [str(x / min_l) for x in sorted_sq_lengths]
    else:
        min_l = F(1)
        scale_invariant_lengths = []

    has_sec_goal = any(g.get("kind") == "construct_plane_section" for g in sim_goals)
    has_area_goal = any(g.get("goal_type") == "area" for g in math_goals)
    q_obj = item.get("question_type") or (
        "section_and_area" if (has_sec_goal and has_area_goal) else ("area_only" if has_area_goal else "section_only")
    )

    scale_invariant_config = (
        relabelled_structure,
        tuple(scale_invariant_lengths),
        tuple(sorted(point_ratios)),
    )
    exact_config = (
        scale_invariant_config,
        tuple(str(x) for x in sorted_sq_lengths),
        q_obj,
    )

    # Dimension 9: Solution / Oracle invariant signature under symmetry and scale
    oracle_invariant = None
    if isinstance(exp, dict) and "boundary" in exp and "area_squared" in exp:
        try:
            v_cnt = int(exp["vertex_count"])
            cut_ts = []
            solid_v_cnt = 0
            for b in exp["boundary"]:
                if "vertex" in b:
                    solid_v_cnt += 1
                elif "t" in b:
                    tf = F(str(b["t"]))
                    cut_ts.append(str(min(tf, F(1) - tf)))
            norm_area_sq = str(F(str(exp["area_squared"])) / (min_l * min_l)) if sorted_sq_lengths else str(F(str(exp["area_squared"])))
            oracle_invariant = (topology, v_cnt, solid_v_cnt, tuple(sorted(cut_ts)), norm_area_sq)
        except Exception:
            oracle_invariant = None

    return {
        "text": text,
        "norm_text": _norm_text(text),
        "ngrams": _char_ngrams(text, 5),
        "topology": topology,
        "question_objective": q_obj,
        "exact_sq_lengths": [str(x) for x in sorted_sq_lengths],
        "scale_invariant_lengths": scale_invariant_lengths,
        "point_ratios": sorted(point_ratios),
        "relabelled_structure": relabelled_structure,
        "scale_invariant_config": scale_invariant_config,
        "exact_config": exact_config,
        "oracle_invariant": oracle_invariant,
    }


def _load_historical_corpora() -> list[dict[str, Any]]:
    historical: list[dict[str, Any]] = []
    seen_sources: set[str] = set()

    # 1. Wave 1 Holdout (84 cases)
    if WAVE1_CORPUS.exists():
        w1 = json.loads(WAVE1_CORPUS.read_text(encoding="utf-8"))
        for c in w1.get("cases") or []:
            src = f"wave1_holdout:{c['id']}"
            seen_sources.add(src)
            historical.append({"source": src, "item": c, "exp": None})

    # 2. Wave 2 Holdout (96 cases) + Expected Oracle
    w2_exp = json.loads(WAVE2_EXPECTED.read_text(encoding="utf-8")) if WAVE2_EXPECTED.exists() else {}
    if WAVE2_CORPUS.exists():
        w2 = json.loads(WAVE2_CORPUS.read_text(encoding="utf-8"))
        for c in w2.get("cases") or []:
            src = f"wave2_holdout:{c['id']}"
            seen_sources.add(src)
            historical.append({"source": src, "item": c, "exp": w2_exp.get(c["id"])})

    # 3. All JSON corpora in docs/evaluation/geometry/runs/** (excluding wave3 itself)
    runs_dir = ROOT / "docs/evaluation/geometry/runs"
    if runs_dir.exists():
        for jf in sorted(runs_dir.rglob("*.json")):
            if "hybrid-v2-independent-vietnamese-geometry-holdout-wave3" in str(jf).replace("\\", "/"):
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
                        src = f"{rel}:{cid}"
                        if src not in seen_sources:
                            seen_sources.add(src)
                            historical.append({"source": src, "item": c, "exp": None})

    # 4. Existing test fixtures in backend/tests/**
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
                        src = f"{rel}:{cid}"
                        if src not in seen_sources:
                            seen_sources.add(src)
                            historical.append({"source": src, "item": c, "exp": None})
        for pf in sorted((tests_dir / "simulation").rglob("*.py")) if (tests_dir / "simulation").exists() else []:
            try:
                txt = pf.read_text(encoding="utf-8")
            except Exception:
                continue
            rel = pf.relative_to(ROOT).as_posix()
            for idx, m in enumerate(re.finditer(r'["\'](Cho\s+(?:hình|khối|tứ diện|lăng trụ)[^"\']{25,})["\']', txt)):
                src = f"{rel}:str_{idx}"
                if src not in seen_sources:
                    seen_sources.add(src)
                    historical.append({"source": src, "item": {"problem_text": m.group(1)}, "exp": None})

    return historical


def run_dedup_audit(wave3_path: Path, expected_path: Path | None = None) -> dict[str, Any]:
    w3_data = json.loads(wave3_path.read_text(encoding="utf-8"))
    w3_cases = w3_data["cases"]
    w3_exp = json.loads(expected_path.read_text(encoding="utf-8")) if (expected_path and expected_path.exists()) else {}
    w3_sigs = {c["id"]: _extract_semantic_signature(c, w3_exp.get(c["id"])) for c in w3_cases}

    historical = _load_historical_corpora()
    hist_sigs = [(h["source"], _extract_semantic_signature(h["item"], h.get("exp"))) for h in historical]

    external_text_flags: list[dict[str, Any]] = []
    external_exact_config_flags: list[dict[str, Any]] = []
    external_scale_invariant_flags: list[dict[str, Any]] = []
    external_oracle_invariant_flags: list[dict[str, Any]] = []
    internal_duplicate_flags: list[dict[str, Any]] = []

    max_external_jaccard = 0.0
    max_external_pair = None

    for c in w3_cases:
        cid = c["id"]
        sig = w3_sigs[cid]
        for h_src, h_sig in hist_sigs:
            if not h_sig["norm_text"]:
                continue
            if sig["norm_text"] == h_sig["norm_text"]:
                external_text_flags.append({"wave3_id": cid, "historical_source": h_src, "exact_text_match": True})
            jac = _jaccard(sig["ngrams"], h_sig["ngrams"])
            if jac > max_external_jaccard:
                max_external_jaccard = jac
                max_external_pair = (cid, h_src, round(jac, 4))
            if jac >= 0.75:
                external_text_flags.append({"wave3_id": cid, "historical_source": h_src, "jaccard_5gram": round(jac, 4)})
            if c.get("expected_disposition") == "SERVE" and sig["scale_invariant_lengths"]:
                if sig["exact_config"] == h_sig["exact_config"]:
                    external_exact_config_flags.append({"wave3_id": cid, "historical_source": h_src})
                elif sig["scale_invariant_config"] == h_sig["scale_invariant_config"]:
                    external_scale_invariant_flags.append({"wave3_id": cid, "historical_source": h_src})
                if (
                    sig["oracle_invariant"] is not None
                    and h_sig["oracle_invariant"] is not None
                    and sig["oracle_invariant"] == h_sig["oracle_invariant"]
                    and sig["relabelled_structure"] == h_sig["relabelled_structure"]
                ):
                    external_oracle_invariant_flags.append({"wave3_id": cid, "historical_source": h_src})

    max_internal_jaccard = 0.0
    max_internal_positive_jaccard = 0.0
    for i in range(len(w3_cases)):
        for j in range(i + 1, len(w3_cases)):
            c1, c2 = w3_cases[i], w3_cases[j]
            s1, s2 = w3_sigs[c1["id"]], w3_sigs[c2["id"]]
            jac = _jaccard(s1["ngrams"], s2["ngrams"])
            if jac > max_internal_jaccard:
                max_internal_jaccard = jac
            both_pos = c1["expected_disposition"] == "SERVE" and c2["expected_disposition"] == "SERVE"
            if both_pos and jac > max_internal_positive_jaccard:
                max_internal_positive_jaccard = jac
            thresh = 0.75 if both_pos else 0.80
            if jac >= thresh or (both_pos and s1["scale_invariant_config"] == s2["scale_invariant_config"]):
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
        and len(external_oracle_invariant_flags) == 0
        and len(internal_duplicate_flags) == 0
    )
    return {
        "schema": "HOLDOUT_WAVE3_DEDUPLICATION_AUDIT/1",
        "wave3_case_count": len(w3_cases),
        "historical_comparison_items_count": len(historical),
        "dimensions_checked": [
            "exact_normalized_text_match",
            "char_5gram_jaccard_similarity",
            "solid_topology",
            "plane_relation_and_roles",
            "dihedral_vertex_relabelling_invariance",
            "projective_scale_invariance",
            "exact_cut_ratio_profile",
            "question_objective",
            "oracle_solution_invariance_under_symmetry_and_scale",
        ],
        "max_external_5gram_jaccard": round(max_external_jaccard, 4),
        "max_external_pair": max_external_pair,
        "max_internal_5gram_jaccard": round(max_internal_jaccard, 4),
        "max_internal_positive_5gram_jaccard": round(max_internal_positive_jaccard, 4),
        "external_text_flags": external_text_flags,
        "external_exact_config_flags": external_exact_config_flags,
        "external_scale_invariant_flags": external_scale_invariant_flags,
        "external_oracle_invariant_flags": external_oracle_invariant_flags,
        "internal_duplicate_flags": internal_duplicate_flags,
        "passed": passed,
    }


if __name__ == "__main__":
    w3_p = Path(sys.argv[1])
    out_p = Path(sys.argv[2])
    exp_p = Path(sys.argv[3]) if len(sys.argv) > 3 else (RUN / "oracle/expected.json")
    report = run_dedup_audit(w3_p, exp_p)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"passed={report['passed']} wave3={report['wave3_case_count']} "
        f"hist={report['historical_comparison_items_count']} "
        f"max_ext_jaccard={report['max_external_5gram_jaccard']} "
        f"max_int_pos_jaccard={report['max_internal_positive_5gram_jaccard']}"
    )
    sys.exit(0 if report["passed"] else 1)
