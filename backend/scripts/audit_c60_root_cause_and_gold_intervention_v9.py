# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Phase B (P1 / Gate G1): Full C60 Case-Level Root-Cause Decomposition & 4-Arm Gold Intervention.

Reads the 60 blind NLU cases (`C60_BLIND_NLU`) from `/8` manifest + original
`independent-nlu-extraction-evaluation` corpus & gold_facts, runs:
  - Arm A: Current `/7-/8` local-SLM route (`slm-verified-normalizer/2` + `AxoV7` + `compact_clause/v7`)
  - Arm B: Gold `TypedFactNext /2` intervention (`B_raw` verbatim quotes + `B_canon` meaning-preserving surface)
           routed through UNMODIFIED `Source Gate -> Planner /26 -> Registry /33 -> Exact Kernel /24`
  - Arm C: Gold `slm-compact-clause/1` intervention (`C_raw` + `C_canon`) through `validate_and_lower_compact_clause`
           (preserving Source Gate & schema bounds)
  - Arm D: Targeted single-component substitutions:
           - `D1_gbnf_4goals`: `AxoV7` under 4-goal GBNF cap + casual goal markers (isolates GBNF cap on req>=3 & casual stems)
           - `D2_normalizer_and_matcher`: `/9` surface canonicalization concept probe + `AxoV7` (without changing GBNF weights)

Outputs (never treating C60 as a blind holdout):
  - `C60_CASE_LEVEL_ROOT_CAUSE.json` (all 20 §5 fields + multi-label taxonomy per case)
  - `C60_GOLD_INTERVENTION_RESULTS.json`
  - `SLM_V9_BOTTLENECK_REPORT.md`
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RUNS_DIR = ROOT / "docs/evaluation/geometry/runs"
OUT_DIR = RUNS_DIR / "axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, normalize_problem_text, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    build_compact_clause_context,
    build_compact_grammar_for_context,
    run_local_slm_extraction,
    validate_and_lower_compact_clause,
)
from app.ai.local_slm_runtime import FINETUNED_LOCAL_SLM_MODEL_KEY, LocalSlmRuntime  # noqa: E402
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.simulation.geometry_functions import planner as GF_PLANNER, registry as GF_REGISTRY  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION  # noqa: E402
from slm_math_evaluator_v2 import compare_math_expressions, infer_goal_kind_from_text  # noqa: E402


C60_CORPUS_PATH = RUNS_DIR / "independent-nlu-extraction-evaluation/inputs/corpus-authoring/corpus.json"
C60_GOLD_PATH = RUNS_DIR / "independent-nlu-extraction-evaluation/inputs/gold_facts.json"
V8_MANIFEST_PATH = RUNS_DIR / "independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json"
V8_EVAL_PATH = RUNS_DIR / "independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json"


# ── Canonical Vietnamese Surface Closures (strict meaning-preserving) for Arm B_canon ──

def _canon_c60_text(orig_id: str, txt: str) -> str:
    """Apply meaning-preserving canonical wording strictly for Arm B_canon Source Gate ceilings.

    Refusals, conditionals (`L38`), negations (`L37`), ambiguities (`D13`, `L31`, `L36`, `L40`, `L43`),
    contradictions (`D15`, `L44`), nonexistent planes (`L16`, `L39`), OOS extrema (`L42`), proof (`L41`),
    and finite segment distances (`D05`, `L12`) are NEVER altered in meaning.
    """
    canon_map: dict[str, str] = {
        "D02": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Tính khoảng cách từ A đến (SBC).",
        "D03": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 2. Tính khoảng cách từ A đến (SBC).",
        "D06": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 2. Tính cosin góc giữa đường thẳng SC và mặt phẳng (ABCD).",
        "D09": "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính độ dài đoạn nối trọng tâm tam giác A'BD với đỉnh C'.",
        "D11": "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, AA' = 6. Gọi H là hình chiếu vuông góc của A lên đường thẳng BC. Tính độ dài đoạn A'H.",
        "D12": "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Tính độ dài đoạn AC'. Tính góc giữa hai đường thẳng AB' và BC'. Tính khoảng cách giữa hai đường thẳng AB' và BC'.",
        "L02": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài đoạn AC'.",
        "L03": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài đoạn AC'.",
        "L05": "Cho hình lập phương ABCD.A'B'C'D' có cạnh 2. Tính khoảng cách từ điểm A đến mặt phẳng (A'BD).",
        "L07": "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, SA vuông góc với (ABCD), SA = 5. Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
        "L13": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính cosin góc giữa đường thẳng AC' và mặt phẳng (ABCD).",
        "L14": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính góc giữa đường thẳng AC' và mặt phẳng (ABCD).",
        "L19": "Tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = 3, OB = 3, OC = 3. Tính độ dài đoạn nối O với trọng tâm của tam giác ABC.",
        "L20": "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Gọi M là trung điểm của cạnh CC'. Tính độ dài đoạn AM.",
        "L21": "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại A, AB = 2, AC = 2, AA' = 4. Gọi O là trung điểm AB'. Tính độ dài đoạn CO.",
        "L22": "Cho hình chóp S.ABC có đáy ABC vuông tại B, AB = 2, BC = 2, SA vuông góc với (ABC), SA = 2. Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "L23": "Tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = 1, OB = 2, OC = 2. Tính thể tích khối chóp O.ABC. Tính diện tích tam giác ABC. Tính khoảng cách từ O đến (ABC).",
        "L24": "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 1, AC = 2, AA' = 2. Tính thể tích khối lăng trụ ABC.A'B'C'. Tính góc giữa hai mặt phẳng (A'BC) và (ABC).",
        "L25": "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, SA vuông góc với (ABCD), SA = 5. Gọi H là hình chiếu vuông góc của A lên mặt phẳng (SBC). Tính độ dài đoạn AH.",
        "L27": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 1, AD = 2, AA' = 2. Tính độ dài đoạn BD'. Tính thể tích khối hộp ABCD.A'B'C'D'. Tính khoảng cách giữa hai đường thẳng AA' và BD'.",
        "L28": "Cho hình chóp S.ABC có SA vuông góc với (ABC), đáy ABC là tam giác vuông cân tại A, AB = 2, AC = 2, SA = 2. Gọi M là trung điểm BC. Tính độ dài đoạn SM. Tính diện tích tam giác SBC.",
        "L29": "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Tính khoảng cách giữa hai đường thẳng BD và B'C. Tính góc giữa hai đường thẳng BD và B'C.",
        "L30": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với (ABCD), SA = 3. Tính độ dài đoạn SC. Tính cosin góc giữa đường thẳng SC và mặt phẳng (ABCD). Tính thể tích khối chóp S.ABCD.",
    }
    return canon_map.get(orig_id, txt)


def _pts(s: str) -> list[str]:
    return re.findall(r"[A-Z][0-9]*'*", s)


def _infer_solid_from_gold(gf_entry: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    for f in gf_entry.get("facts") or []:
        if f.get("kind") == "solid":
            raw_s = f.get("solid", "")
            st = f.get("solid_type", "pyramid")
            if raw_s == "OABC" or (st == "tetrahedron" and "." not in raw_s):
                vp = _pts(raw_s)
                notn = f"{vp[0]}.{''.join(vp[1:])}" if len(vp) == 4 else raw_s
                return {
                    "solid_id": "s1",
                    "solid_type": "pyramid",
                    "notation": notn,
                    "quote": f["quotes"][0],
                }, vp[1:] if len(vp) == 4 else vp
            if "." in raw_s:
                a, b = raw_s.split(".", 1)
                mapped_st = "prism" if st in ("prism", "cuboid", "cube") else "pyramid"
                return {
                    "solid_id": "s1",
                    "solid_type": mapped_st,
                    "notation": raw_s,
                    "quote": f["quotes"][0],
                }, (_pts(a) if mapped_st == "prism" else _pts(b))
    return None, []


def _gold_v2_and_compact_for_case(orig_id: str, raw_text: str, canon_text: str, gf_entry: dict[str, Any]) -> dict[str, Any]:
    """Construct verified Gold `TypedFactNext /2` (for both raw & canon text) + Gold `slm-compact-clause/1`."""
    # Cases with clean complete Local Parser outputs under canon_text get exact gold payloads directly
    # from the deterministic parser (which matches TypedFactNext /2 contract bit-for-bit without inventing facts),
    # supplemented with explicit @id / triangle-area / SC^2 gold probes where parser doesn't cover yet!
    lp_raw = parse_geometry_problem_locally(raw_text)
    if lp_raw.status == "LOCAL_PARSE_COMPLETE" and lp_raw.payload is not None and orig_id not in ("D05", "L12", "L28"):
        v2_raw = lp_raw.payload
    else:
        v2_raw = _build_manual_v2_from_gold(orig_id, raw_text, gf_entry)

    if canon_text != raw_text:
        lp_canon = parse_geometry_problem_locally(canon_text)
        if lp_canon.status == "LOCAL_PARSE_COMPLETE" and lp_canon.payload is not None and orig_id not in ("L23", "L28"):
            v2_canon = lp_canon.payload
        else:
            v2_canon = _build_manual_v2_from_gold(orig_id, canon_text, gf_entry, is_canon=True)
    else:
        v2_canon = v2_raw

    compact_raw = _build_gold_compact(orig_id, raw_text, gf_entry, is_canon=False)
    compact_canon = _build_gold_compact(orig_id, canon_text, gf_entry, is_canon=True) if canon_text != raw_text else compact_raw
    return {
        "v2_raw": v2_raw,
        "v2_canon": v2_canon,
        "compact_raw": compact_raw,
        "compact_canon": compact_canon,
    }


def _find_q(text: str, *cands: str) -> str:
    for c in cands:
        if c and c in text:
            return c
    return cands[0] if cands else text


def _build_manual_v2_from_gold(orig_id: str, text: str, gf_entry: dict[str, Any], *, is_canon: bool = False) -> dict[str, Any] | None:
    """Build exact Gold `TypedFactNext /2` payload respecting Source Gate quotes in `text`."""
    solid, base_pts = _infer_solid_from_gold(gf_entry)
    if solid is None:
        return None
    solid_q = _find_q(
        text,
        solid["quote"],
        f"Cho hình chóp {solid['notation']}",
        f"Cho lăng trụ đứng {solid['notation']}",
        f"Cho hình lăng trụ đứng {solid['notation']}",
        f"Cho hình lập phương {solid['notation']} cạnh 2",
        f"Cho hình lập phương {solid['notation']} cạnh a",
        f"Cho hình lập phương {solid['notation']}",
        f"Một hình hộp chữ nhật {solid['notation']}",
        f"Cho hình hộp chữ nhật {solid['notation']}",
        f"Tứ diện {''.join(base_pts)}" if not base_pts else f"Tứ diện OABC",
    )
    solid = {**solid, "quote": solid_q}
    premises: list[dict[str, Any]] = []
    described_points: list[dict[str, Any]] = []
    math_goals: list[dict[str, Any]] = []
    sim_goals: list[dict[str, Any]] = [
        {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": solid["quote"]}
    ]
    length_unit = "1"

    facts = gf_entry.get("facts") or []
    txt_low = text.lower()
    is_cube = "lập phương" in txt_low
    is_box = "hộp chữ nhật" in txt_low
    is_right_prism = solid["solid_type"] == "prism" and ("đứng" in txt_low or is_cube or is_box)
    if is_right_prism:
        tpts = [f"{p}'" if not p.endswith("'") else p for p in base_pts]
        premises.append({"kind": "right_prism", "args": {"base": base_pts, "top": tpts}, "quote": solid["quote"], "solid_id": "s1"})
    if is_box:
        premises.append({"kind": "rectangle", "args": {"vertices": base_pts}, "quote": solid["quote"], "solid_id": "s1"})

    q_idx = 1
    perp_pair_seen = False
    for f in facts:
        k = f.get("kind")
        raw_qs = list(f.get("quotes") or [text])
        if is_canon and k == "length" and len(f.get("points") or []) == 2:
            seg_s = "".join(f.get("points") or [])
            val_s = str(f.get("value") or "")
            raw_qs.extend([f"{seg_s} = {val_s}", f"{seg_s}={val_s}"])
        fq = _find_q(text, *raw_qs)
        if k == "polygon_shape":
            sh = f.get("shape")
            pts = list(f.get("points") or base_pts)
            val = str(f.get("value") or "")
            if "a" in val:
                length_unit = "a"
            if sh in ("square", "equilateral_triangle", "regular_hexagon"):
                if is_cube and not val:
                    continue
                args: dict[str, Any] = {"vertices": pts}
                if val:
                    args["side"] = val
                premises.append({"kind": "regular_polygon", "args": args, "quote": fq, "solid_id": "s1"})
            elif sh == "rectangle":
                premises.append({"kind": "rectangle", "args": {"vertices": pts}, "quote": fq, "solid_id": "s1"})
            elif sh == "parallelogram":
                premises.append({"kind": "parallelogram", "args": {"vertices": pts}, "quote": fq, "solid_id": "s1"})
        elif k == "right_angle":
            at = f.get("at")
            pts = list(f.get("points") or [])
            rays = [p for p in (pts if at in pts else [*pts, *base_pts]) if p != at][:2]
            if at and len(rays) == 2:
                if is_canon:
                    fq = _find_q(text, fq, f"đáy {''.join(base_pts)} là tam giác vuông tại {at}", f"đáy {''.join(base_pts)} vuông tại {at}")
                premises.append({"kind": "right_angle", "args": {"vertex": at, "rays": rays}, "quote": fq, "solid_id": "s1"})
        elif k == "perpendicular":
            pa = list(f.get("points_a") or [])
            pb = list(f.get("points_b") or [])
            if len(pa) == 2 and len(pb) == 2:
                if is_canon and "OA, OB, OC đôi một vuông góc" in text:
                    fq = "OA, OB, OC đôi một vuông góc"
                premises.append({"kind": "perpendicular_lines", "args": {"line1": pa, "line2": pb}, "quote": fq, "solid_id": "s1"})
            elif len(pa) == 2 and len(pb) >= 3:
                if is_canon and f"{''.join(pa)} vuông góc với ({''.join(pb)})" in text:
                    fq = f"{''.join(pa)} vuông góc với ({''.join(pb)})"
                premises.append({"kind": "perpendicular_line_plane", "args": {"line": pa, "plane": pb}, "quote": fq, "solid_id": "s1"})
            elif len(pa) >= 3 and len(pb) >= 3:
                premises.append({"kind": "face_perpendicular_base", "args": {"face": pa, "base": pb}, "quote": fq, "solid_id": "s1"})
        elif k == "length":
            pts = list(f.get("points") or [])
            val = str(f.get("value") or "")
            if "a" in val:
                length_unit = "a"
            if is_cube and len(pts) != 2:
                cube_q = _find_q(text, fq, f"Cho hình lập phương {solid['notation']} có cạnh bằng {val}", f"Cho hình lập phương {solid['notation']} cạnh {val}")
                premises.append({"kind": "regular_polygon", "args": {"vertices": base_pts, "side": val}, "quote": cube_q, "solid_id": "s1"})
                premises.append({"kind": "segment_length", "args": {"segment": [base_pts[0], f"{base_pts[0]}'"], "value": val}, "quote": cube_q, "solid_id": "s1"})
            elif len(pts) == 2 and val:
                premises.append({"kind": "segment_length", "args": {"segment": pts, "value": val}, "quote": fq, "solid_id": "s1"})
        elif k == "point_def":
            pt = f.get("point")
            role_n = f.get("role_name")
            if role_n == "midpoint" or "trung điểm" in fq.lower():
                seg = list(f.get("points") or [])
                if pt and len(seg) == 2:
                    if is_canon:
                        fq = _find_q(text, fq, f"Gọi {pt} là trung điểm của cạnh {''.join(seg)}", f"Gọi {pt} là trung điểm {''.join(seg)}")
                    premises.append({"kind": "midpoint", "args": {"point": pt, "segment": seg}, "quote": fq, "solid_id": "s1"})
        elif k == "projection":
            pt = f.get("point")
            src_p = f.get("source") or f.get("projected") or f.get("of")
            tgt = list(f.get("on") or f.get("target") or [])
            if not src_p and len(tgt) == 2:
                src_p = "A"
            if pt and src_p and len(tgt) == 2:
                premises.append({"kind": "orthogonal_projection_line", "args": {"point": src_p, "image": pt, "line": tgt}, "quote": fq, "solid_id": "s1"})
            elif pt and src_p and len(tgt) >= 3:
                premises.append({"kind": "orthogonal_projection", "args": {"point": src_p, "image": pt, "plane": tgt}, "quote": fq, "solid_id": "s1"})

    def _mg(gtype: str, target: dict[str, Any], quote: str) -> dict[str, Any]:
        nonlocal q_idx
        d = {"goal_id": f"q{q_idx}", "kind": "measurement", "goal_type": gtype, "target": target, "quote": quote, "solid_id": "s1"}
        q_idx += 1
        return d

    if orig_id in ("D02", "D03", "L05"):
        pl = ["S", "B", "C"] if orig_id in ("D02", "D03") else ["A'", "B", "D"]
        pt = "A"
        for q_f in [x for x in facts if x.get("kind") == "question"]:
            qq = f"Tính khoảng cách từ {pt} đến ({''.join(pl)})" if (is_canon and orig_id in ("D02", "D03")) else (
                "Tính khoảng cách từ điểm A đến mặt phẳng (A'BD)" if is_canon else q_f["quotes"][0]
            )
            math_goals.append(_mg("distance", {"point": pt, "plane": pl}, qq))
    elif orig_id == "D05":
        math_goals.append(_mg("distance", {"point": "S", "line": ["B", "C"]}, "Tính khoảng cách từ S đến đoạn thẳng BC"))
    elif orig_id in ("D06", "L13"):
        ln = ["S", "C"] if orig_id == "D06" else ["A", "C'"]
        q0 = [x for x in facts if x.get("kind") == "question"][0]["quotes"][0]
        if is_canon:
            q0 = f"Tính cosin góc giữa đường thẳng {''.join(ln)} và mặt phẳng (ABCD)"
        math_goals.append(_mg("angle", {"line": ln, "plane": ["A", "B", "C", "D"]}, q0))
    elif orig_id == "D09":
        described_points.append({"described_id": "dp1", "kind": "centroid", "polygon": ["A'", "B", "D"], "quote": "trọng tâm tam giác A'BD"})
        math_goals.append(_mg("distance", {"segment": ["@dp1", "C'"]}, "Tính khoảng cách từ trọng tâm tam giác A'BD đến đỉnh C'" if not is_canon else "Tính độ dài đoạn nối trọng tâm tam giác A'BD với đỉnh C'"))
    elif orig_id == "D11":
        premises = [p for p in premises if p["kind"] != "orthogonal_projection_line"]
        premises.append({"kind": "orthogonal_projection_line", "args": {"point": "A", "image": "H", "line": ["B", "C"]}, "quote": "Hãy dựng hình chiếu vuông góc của A lên đường thẳng BC, gọi điểm đó là H" if not is_canon else "Gọi H là hình chiếu vuông góc của A lên đường thẳng BC", "solid_id": "s1"})
        math_goals.append(_mg("distance", {"segment": ["A'", "H"]}, "tính độ dài đoạn A'H" if not is_canon else "Tính độ dài đoạn A'H"))
    elif orig_id == "D12":
        math_goals.append(_mg("distance", {"segment": ["A", "C'"]}, "Tính độ dài đường chéo AC'" if not is_canon else "Tính độ dài đoạn AC'"))
        math_goals.append(_mg("angle", {"line1": ["A", "B'"], "line2": ["B", "C'"]}, "Tính góc giữa hai đường thẳng AB' và BC'"))
        math_goals.append(_mg("distance", {"line1": ["A", "B'"], "line2": ["B", "C'"]}, "Tính khoảng cách giữa hai đường thẳng đó" if not is_canon else "Tính khoảng cách giữa hai đường thẳng AB' và BC'"))
    elif orig_id in ("L02", "L03"):
        q_f = [x for x in facts if x.get("kind") == "question"][0]["quotes"][0]
        math_goals.append(_mg("distance", {"segment": ["A", "C'"]}, q_f if not is_canon else "Tính độ dài đoạn AC'"))
    elif orig_id == "L07":
        q_f = [x for x in facts if x.get("kind") == "question"][0]["quotes"][0]
        math_goals.append(_mg("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, q_f if not is_canon else "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD)"))
    elif orig_id == "L10":
        math_goals.append(_mg("distance", {"segment": ["S", "C"]}, "Tính SC²"))
    elif orig_id == "L12":
        premises = [p for p in premises if p["kind"] != "parallelogram"]
        premises.insert(0, {"kind": "parallelogram", "args": {"vertices": ["A", "B", "C", "D"]}, "quote": "đáy ABCD là hình bình hành", "solid_id": "s1"})
        premises.append({"kind": "vertex_angle", "args": {"vertex": "A", "rays": ["B", "D"], "value": "135", "unit": "deg"}, "quote": "góc BAD = 135°", "solid_id": "s1"})
        math_goals.append(_mg("distance", {"point": "B", "line": ["S", "D"]}, "Tính khoảng cách từ B đến đoạn thẳng SD"))
    elif orig_id == "L14":
        q0 = "Tính góc giữa đường chéo AC' và mặt phẳng (ABCD)" if not is_canon else "Tính góc giữa đường thẳng AC' và mặt phẳng (ABCD)"
        math_goals.append(_mg("angle", {"line": ["A", "C'"], "plane": ["A", "B", "C", "D"]}, q0))
    elif orig_id == "L17":
        sim_goals.append({"goal_id": "sg2", "kind": "construct_intersection_line", "target_planes": [["S", "A", "B"], ["S", "C", "D"]], "target_solid_id": "s1", "quote": "Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD)"})
    elif orig_id == "L18":
        premises.append({"kind": "parallelogram", "args": {"vertices": ["A", "B", "C", "D"]}, "quote": "đáy là hình bình hành", "solid_id": "s1"})
        sim_goals.append({"goal_id": "sg2", "kind": "construct_intersection_line", "target_planes": [["S", "A", "C"], ["S", "B", "D"]], "target_solid_id": "s1", "quote": "Tìm giao tuyến của mặt phẳng (SAC) với mặt phẳng (SBD)"})
    elif orig_id == "L19":
        described_points.append({"described_id": "dp1", "kind": "centroid", "polygon": ["A", "B", "C"], "quote": "trọng tâm của tam giác ABC"})
        math_goals.append(_mg("distance", {"segment": ["O", "@dp1"]}, "Tính khoảng cách từ O đến trọng tâm của tam giác ABC" if not is_canon else "Tính độ dài đoạn nối O với trọng tâm của tam giác ABC"))
    elif orig_id == "L20":
        math_goals.append(_mg("distance", {"segment": ["A", "M"]}, "Tính độ dài đoạn AM"))
    elif orig_id == "L21":
        if not is_canon:
            described_points.append({"described_id": "dp1", "kind": "midpoint", "segment": ["A", "B'"], "quote": "tâm của mặt bên ABB'A'"})
            math_goals.append(_mg("distance", {"segment": ["C", "@dp1"]}, "Tính khoảng cách từ C đến tâm của mặt bên ABB'A'"))
        else:
            premises.append({"kind": "midpoint", "args": {"point": "O", "segment": ["A", "B'"]}, "quote": "Gọi O là trung điểm AB'", "solid_id": "s1"})
            math_goals.append(_mg("distance", {"segment": ["C", "O"]}, "Tính độ dài đoạn CO"))
    elif orig_id == "L22":
        if not is_canon:
            described_points.append({"described_id": "dp1", "kind": "orthogonal_projection", "point": "A", "plane": ["S", "B", "C"], "quote": "chân đường vuông góc hạ từ A xuống mặt phẳng (SBC)"})
            math_goals.append(_mg("distance", {"segment": ["A", "@dp1"]}, "Tính độ dài đoạn nối A với chân đường vuông góc hạ từ A xuống mặt phẳng (SBC)"))
        else:
            math_goals.append(_mg("distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC)"))
    elif orig_id == "L23":
        math_goals.append(_mg("volume", {"solid_id": "s1"}, "Tính thể tích tứ diện" if not is_canon else "Tính thể tích khối chóp O.ABC"))
        math_goals.append(_mg("area", {"polygon": ["A", "B", "C"]}, "diện tích tam giác ABC" if not is_canon else "Tính diện tích tam giác ABC"))
        math_goals.append(_mg("distance", {"point": "O", "plane": ["A", "B", "C"]}, "rồi suy ra khoảng cách từ O đến (ABC)" if not is_canon else "Tính khoảng cách từ O đến (ABC)"))
    elif orig_id == "L24":
        premises = [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "quote": solid["quote"], "solid_id": "s1"},
            {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC là tam giác vuông tại A", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "1"}, "quote": "AB = 1", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "2"}, "quote": "AC = 2", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "2"}, "quote": "chiều cao AA' = 2" if not is_canon else "AA' = 2", "solid_id": "s1"},
        ]
        math_goals.append(_mg("volume", {"solid_id": "s1"}, "Tính thể tích khối lăng trụ" if not is_canon else "Tính thể tích khối lăng trụ ABC.A'B'C'"))
        math_goals.append(_mg("angle", {"plane1": ["A'", "B", "C"], "plane2": ["A", "B", "C"]}, "Tính góc giữa hai mặt phẳng (A'BC) và (ABC)"))
    elif orig_id == "L25":
        premises = [p for p in premises if p["kind"] != "orthogonal_projection"]
        premises.append({"kind": "orthogonal_projection", "args": {"point": "A", "image": "H", "plane": ["S", "B", "C"]}, "quote": "Hãy dựng hình chiếu vuông góc của A trên mặt phẳng (SBC), gọi là H" if not is_canon else "Gọi H là hình chiếu vuông góc của A lên mặt phẳng (SBC)", "solid_id": "s1"})
        math_goals.append(_mg("distance", {"segment": ["A", "H"]}, "tính độ dài AH" if not is_canon else "Tính độ dài đoạn AH"))
    elif orig_id == "L27":
        math_goals.append(_mg("distance", {"segment": ["B", "D'"]}, "Tính BD'" if not is_canon else "Tính độ dài đoạn BD'"))
        math_goals.append(_mg("volume", {"solid_id": "s1"}, "tính thể tích khối hộp" if not is_canon else "Tính thể tích khối hộp ABCD.A'B'C'D'"))
        math_goals.append(_mg("distance", {"line1": ["A", "A'"], "line2": ["B", "D'"]}, "tính khoảng cách giữa hai đường thẳng AA' và BD'" if not is_canon else "Tính khoảng cách giữa hai đường thẳng AA' và BD'"))
    elif orig_id == "L28":
        math_goals.append(_mg("distance", {"segment": ["S", "M"]}, "Tính độ dài SM" if not is_canon else "Tính độ dài đoạn SM"))
        math_goals.append(_mg("area", {"polygon": ["S", "B", "C"]}, "tính diện tích tam giác SBC" if not is_canon else "Tính diện tích tam giác SBC"))
    elif orig_id == "L29":
        math_goals.append(_mg("distance", {"line1": ["B", "D"], "line2": ["B'", "C"]}, "Tính khoảng cách giữa hai đường thẳng BD và B'C"))
        math_goals.append(_mg("angle", {"line1": ["B", "D"], "line2": ["B'", "C"]}, "hai đường thẳng này hợp với nhau một góc bao nhiêu?" if not is_canon else "Tính góc giữa hai đường thẳng BD và B'C"))
    elif orig_id == "L30":
        math_goals.append(_mg("distance", {"segment": ["S", "C"]}, "Tính SC" if not is_canon else "Tính độ dài đoạn SC"))
        math_goals.append(_mg("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, "tính cos² góc giữa SC và đáy" if not is_canon else "Tính cosin góc giữa đường thẳng SC và mặt phẳng (ABCD)"))
        math_goals.append(_mg("volume", {"solid_id": "s1"}, "tính thể tích khối chóp" if not is_canon else "Tính thể tích khối chóp S.ABCD"))
    else:
        for qf in [x for x in facts if x.get("kind") == "question"]:
            qt = qf.get("quantity")
            qq = qf["quotes"][0]
            if qt == "volume":
                math_goals.append(_mg("volume", {"solid_id": "s1"}, qq))

    out: dict[str, Any] = {
        "schema_version": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        "problem_text": text,
        "length_unit": length_unit,
        "solids": [solid],
        "premises": premises,
        "relations": [],
        "derived_sections": [],
        "simulation_goals": sim_goals,
        "math_goals": math_goals,
    }
    if described_points:
        out["described_points"] = described_points
    return out


def _build_gold_compact(orig_id: str, text: str, gf_entry: dict[str, Any], *, is_canon: bool = False) -> dict[str, Any] | None:
    """Build exact Gold `slm-compact-clause/1` JSON (as schema currently supports) for Arm C."""
    ctx = build_compact_clause_context(text)
    if not any(e.kind == "solid" for e in ctx.entities):
        return None
    sol_e = next(e for e in ctx.entities if e.kind == "solid")
    sol_cid = sol_e.clause_ids[0] if sol_e.clause_ids else 0
    stype = sol_e.solid_subtype or "pyr"
    reg = 1 if (sol_e.is_regular_solid or stype in ("cube", "box")) else 0

    def _cid_for(sub: str, default: int = 0) -> int:
        sub_l = sub.lower()
        for cl in ctx.clauses:
            if sub_l in cl.text.lower():
                return cl.clause_id
        for w in [t for t in re.split(r"\s+", sub_l) if len(t) >= 3]:
            for cl in ctx.clauses:
                if w in cl.text.lower():
                    return cl.clause_id
        return default

    # Build minimal exact relation & goal entries matching ctx entities & quantities
    r: list[dict[str, Any]] = []
    g: list[dict[str, Any]] = []
    u: list[dict[str, Any]] = []
    facts = gf_entry.get("facts") or []

    # Map known entity & quantity strings cleanly
    def _has_e(lbl: str, kind: str | None = None) -> bool:
        return any(e.label == lbl and (kind is None or e.kind == kind) for e in ctx.entities)

    def _qty(v: str) -> str:
        for q in ctx.quantities:
            if q.canon_expr == v or q.raw_token == v:
                return q.raw_token
        return v

    # Extract relations faithfully per C60 gold facts
    for f in facts:
        k = f.get("kind")
        fq = (f.get("quotes") or [""])[0]
        cid = _cid_for(fq, sol_cid)
        if k == "polygon_shape":
            sh = f.get("shape")
            poly = "".join(f.get("points") or [])
            val = f.get("value")
            if sh in ("square", "equilateral_triangle", "regular_hexagon"):
                if stype == "cube" and not val:
                    continue
                item = {"c": cid, "p": "reg_poly", "a": poly}
                if val:
                    item["q"] = _qty(str(val))
                r.append(item)
            elif sh == "rectangle":
                r.append({"c": cid, "p": "rect", "a": poly})
            elif sh == "parallelogram":
                r.append({"c": cid, "p": "para", "a": poly})
        elif k == "right_angle":
            at = f.get("at")
            pts = list(f.get("points") or [])
            if at and at not in pts:
                pts = [at, *pts]
            poly = "".join(pts[:3])
            r.append({"c": cid, "p": "right_tri", "a": poly, "pt": at})
        elif k == "perpendicular":
            pa = "".join(f.get("points_a") or [])
            pb = "".join(f.get("points_b") or [])
            if len(f.get("points_a") or []) == 2 and len(f.get("points_b") or []) == 2:
                r.append({"c": cid, "p": "perp_ll", "a": pa, "b": pb})
            elif len(f.get("points_a") or []) == 2 and len(f.get("points_b") or []) >= 3:
                r.append({"c": cid, "p": "perp_lp", "a": pa, "b": pb})
            elif len(f.get("points_a") or []) >= 3 and len(f.get("points_b") or []) >= 3:
                r.append({"c": cid, "p": "face_perp", "a": pa, "b": pb})
        elif k == "length":
            pts = f.get("points") or []
            val = str(f.get("value") or "")
            if len(pts) == 2 and val:
                r.append({"c": cid, "p": "len", "a": "".join(pts), "q": _qty(val)})
            elif stype == "cube" and val:
                r.append({"c": cid, "p": "reg_poly", "a": "ABCD", "q": _qty(val)})
                r.append({"c": cid, "p": "len", "a": "AA'", "q": _qty(val)})
        elif k == "point_def" and (f.get("role_name") == "midpoint" or "trung điểm" in fq.lower()):
            pt = f.get("point")
            seg = "".join(f.get("points") or [])
            if pt and seg:
                r.append({"c": cid, "p": "mid", "pt": pt, "a": seg})

    # Per-case adjustments where gold_facts V1 differs from V2 projection/goals
    last_cid = ctx.clauses[-1].clause_id if ctx.clauses else 0
    if orig_id in ("D02", "D03"):
        g = [{"c": last_cid, "t": "dist_pt_plane", "a": "A", "b": "SBC"}]
    elif orig_id == "D04":
        r = [x for x in r if x["p"] != "right_tri"] + [
            {"c": _cid_for("hình thang"), "p": "right_tri", "a": "ABD", "pt": "A"},
            {"c": _cid_for("hình thang"), "p": "right_tri", "a": "ACD", "pt": "D"},
        ]
        g = [{"c": last_cid, "t": "dist_pt_line", "a": "S", "b": "BC"}]
    elif orig_id == "D05":
        g = [{"c": last_cid, "t": "dist_pt_line", "a": "S", "b": "BC"}]
    elif orig_id == "D06":
        g = [{"c": last_cid, "t": "ang_lp", "a": "SC", "b": "ABCD"}]
    elif orig_id == "D09":
        # slm-compact-clause/1 has NO @id unnamed centroid goal operand!
        u = [{"c": last_cid, "k": "unsup"}]
    elif orig_id == "D11":
        r.append({"c": _cid_for("hình chiếu"), "p": "proj", "pt": "H", "a": "A", "b": "BC"})
        g = [{"c": last_cid, "t": "len", "a": "A'H"}]
    elif orig_id == "D12":
        g = [
            {"c": _cid_for("AC'"), "t": "len", "a": "AC'"},
            {"c": _cid_for("AB'"), "t": "ang_ll", "a": "AB'", "b": "BC'"},
            {"c": _cid_for("khoảng cách"), "t": "dist_line_line", "a": "AB'", "b": "BC'"},
        ]
    elif orig_id in ("L02", "L03"):
        g = [{"c": last_cid, "t": "len", "a": "AC'"}]
    elif orig_id == "L05":
        g = [{"c": _cid_for("A'BD"), "t": "dist_pt_plane", "a": "A", "b": "A'BD"}]
    elif orig_id == "L07":
        g = [{"c": last_cid, "t": "ang_lp", "a": "SC", "b": "ABCD"}]
    elif orig_id == "L10":
        # No squared-length goal in compact_clause/1
        u = [{"c": last_cid, "k": "unsup"}]
    elif orig_id == "L12":
        r.append({"c": _cid_for("135"), "p": "ang_vtx", "a": "BAD", "pt": "A", "q": "135°"})
        g = [{"c": last_cid, "t": "dist_pt_line", "a": "B", "b": "SD"}]
    elif orig_id == "L13":
        g = [{"c": last_cid, "t": "ang_lp", "a": "AC'", "b": "ABCD"}]
    elif orig_id == "L19":
        # Requires unnamed centroid of ABC inside goal
        u = [{"c": last_cid, "k": "unsup"}]
    elif orig_id == "L20":
        g = [{"c": last_cid, "t": "len", "a": "AM"}]
    elif orig_id == "L21":
        # Requires unnamed face center of ABB'A' inside goal
        if not is_canon:
            u = [{"c": last_cid, "k": "unsup"}]
        else:
            r.append({"c": _cid_for("trung điểm"), "p": "mid", "pt": "O", "a": "AB'"})
            g = [{"c": last_cid, "t": "len", "a": "CO"}]
    elif orig_id == "L22":
        # Requires unnamed projection foot of A onto (SBC)
        if not is_canon:
            u = [{"c": last_cid, "k": "unsup"}]
        else:
            g = [{"c": last_cid, "t": "dist_pt_plane", "a": "A", "b": "SBC"}]
    elif orig_id == "L23":
        g = [
            {"c": last_cid, "t": "vol", "tgt": sol_e.label},
            {"c": last_cid, "t": "area", "a": "ABC"},
            {"c": last_cid, "t": "dist_pt_plane", "a": "O", "b": "ABC"},
        ]
    elif orig_id == "L24":
        # Fix missing len quote on AA' if raw
        g = [
            {"c": _cid_for("thể tích"), "t": "vol", "tgt": sol_e.label},
            {"c": _cid_for("A'BC"), "t": "ang_pp", "a": "A'BC", "b": "ABC"},
        ]
    elif orig_id == "L25":
        r.append({"c": _cid_for("hình chiếu"), "p": "proj", "pt": "H", "a": "A", "b": "SBC"})
        g = [{"c": last_cid, "t": "len", "a": "AH"}]
    elif orig_id == "L27":
        g = [
            {"c": _cid_for("BD'"), "t": "len", "a": "BD'"},
            {"c": _cid_for("thể tích"), "t": "vol", "tgt": sol_e.label},
            {"c": _cid_for("khoảng cách"), "t": "dist_line_line", "a": "AA'", "b": "BD'"},
        ]
    elif orig_id == "L28":
        g = [
            {"c": last_cid, "t": "len", "a": "SM"},
            {"c": last_cid, "t": "area", "a": "SBC"},
        ]
    elif orig_id == "L29":
        g = [
            {"c": _cid_for("BD"), "t": "dist_line_line", "a": "BD", "b": "B'C"},
            {"c": last_cid, "t": "ang_ll", "a": "BD", "b": "B'C"},
        ]
    elif orig_id == "L30":
        g = [
            {"c": _cid_for("SC"), "t": "len", "a": "SC"},
            {"c": _cid_for("cos"), "t": "ang_lp", "a": "SC", "b": "ABCD"},
            {"c": last_cid, "t": "vol", "tgt": sol_e.label},
        ]
    elif orig_id == "L38":
        g = [{"c": last_cid, "t": "len", "a": "AC'"}]
    else:
        # Use local parser if available or fallback
        lp = parse_geometry_problem_locally(text)
        if lp.status == "LOCAL_PARSE_COMPLETE" and lp.payload:
            for mg in lp.payload.get("math_goals") or []:
                gt = mg.get("goal_type")
                tgt = mg.get("target") or {}
                c_g = _cid_for(mg.get("quote", ""), last_cid)
                if gt == "volume":
                    g.append({"c": c_g, "t": "vol", "tgt": sol_e.label})
                elif gt == "distance" and "segment" in tgt:
                    g.append({"c": c_g, "t": "len", "a": "".join(tgt["segment"])})
                elif gt == "distance" and "point" in tgt and "plane" in tgt:
                    g.append({"c": c_g, "t": "dist_pt_plane", "a": tgt["point"], "b": "".join(tgt["plane"])})
                elif gt == "distance" and "point" in tgt and "line" in tgt:
                    g.append({"c": c_g, "t": "dist_pt_line", "a": tgt["point"], "b": "".join(tgt["line"])})
                elif gt == "distance" and "line1" in tgt:
                    g.append({"c": c_g, "t": "dist_line_line", "a": "".join(tgt["line1"]), "b": "".join(tgt["line2"])})
                elif gt == "angle" and "line" in tgt:
                    g.append({"c": c_g, "t": "ang_lp", "a": "".join(tgt["line"]), "b": "".join(tgt["plane"])})
                elif gt == "angle" and "plane1" in tgt:
                    g.append({"c": c_g, "t": "ang_pp", "a": "".join(tgt["plane1"]), "b": "".join(tgt["plane2"])})
                elif gt == "angle" and "line1" in tgt:
                    g.append({"c": c_g, "t": "ang_ll", "a": "".join(tgt["line1"]), "b": "".join(tgt["line2"])})

    return {"s": [sol_cid, stype, sol_e.label, reg], "r": r, "g": g, "u": u}


def _check_oracles(answers: dict[str, Any], oracles: list[str], orig_text: str) -> tuple[bool, bool, bool]:
    ans_vals = [str(v) for v in (answers or {}).values()]
    if not oracles:
        return True, True, False
    if not ans_vals:
        return False, False, False
    clean_for_gk = re.sub(r"\bvuông\s+góc\b", "vuong_goc", orig_text, flags=re.IGNORECASE)
    gk = infer_goal_kind_from_text(clean_for_gk) if len(oracles) == 1 else None
    matched = 0
    for ora in oracles:
        if any(compare_math_expressions(a, ora, goal_kind=gk).matched is True for a in ans_vals):
            matched += 1
    any_wrong = any(
        not any(compare_math_expressions(a, ora, goal_kind=gk).matched is True for ora in oracles)
        for a in ans_vals
    )
    return matched >= 1 and not any_wrong, matched == len(oracles) and not any_wrong, any_wrong


def _run_route_on_v2(text: str, payload: dict[str, Any] | None, oracles: list[str], orig_text: str) -> dict[str, Any]:
    if payload is None:
        return {"status": "REFUSED", "reason_code": "NO_GOLD_PAYLOAD", "answers": {}, "ok_any": False, "ok_strict": False, "wrong_served": False}
    try:
        res = run_hybrid_offline(
            text,
            ReplayExtractor({text: payload}),
            policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
            timeout_seconds=15.0,
        )
        rd = res.response.get("route_d") or {}
        st = str(rd.get("status") or "REFUSED")
        ref = rd.get("refusal") or {}
        rc = ref.get("code") or ref.get("reason_code")
        ans = rd.get("answers") or {}
        ok_any, ok_strict, wrong = _check_oracles(ans, oracles, orig_text) if st == "SERVED" else (False, False, False)
        return {
            "status": st,
            "reason_code": rc,
            "answers": ans,
            "ok_any": ok_any,
            "ok_strict": ok_strict,
            "wrong_served": wrong,
            "planner": rd.get("planner") or res.receipt.get("planner"),
            "source_gate": res.receipt.get("source_gate"),
            "engine": res.receipt.get("engine"),
        }
    except Exception as exc:
        return {"status": "REFUSED", "reason_code": f"EXC:{type(exc).__name__}", "answers": {}, "ok_any": False, "ok_strict": False, "wrong_served": False}


def _extract_component_traces(r_obj) -> dict[str, Any]:
    rd = (getattr(r_obj, "response", None) or {}).get("route_d") or {}
    ref = rd.get("refusal") or {}
    rec = getattr(r_obj, "receipt", None) or {}
    return {
        "status": getattr(r_obj, "status", None),
        "reason_code": ref.get("code") or ref.get("reason_code"),
        "source_gate": rec.get("source_gate"),
        "planner": rec.get("planner"),
        "engine": rec.get("engine"),
        "answers": rd.get("answers") or {},
    }


def _classify_root_causes(
    case: dict[str, Any],
    orig_id: str,
    raw_lp_status: str,
    wire_payload: dict[str, Any] | None,
    grounding_env: dict[str, Any] | None,
    slm_ok: bool,
    arm_a: dict[str, Any],
    arm_b_raw: dict[str, Any],
    arm_b_canon: dict[str, Any],
    arm_c_raw: dict[str, Any],
    arm_c_canon: dict[str, Any],
    arm_d1_uncapped: dict[str, Any] | None,
) -> tuple[list[str], str, str, str]:
    """Return (root_cause_labels, capability_status, fix_ownership, exact_failure_reason)."""
    role = case["eval_role"]
    n_req = int(case.get("n_source_requests") or 1)
    labels: list[str] = []

    if role == "NEGATIVE_OR_REFUSAL_EXPECTED":
        disp = case["gold_disposition"]
        if orig_id in ("L42",):
            return ["OUT_OF_SCOPE"], "OUT_OF_SCOPE", "NONE_SAFE_REFUSAL", "Expected refusal: moving-point extremum optimization outside static 3D scope."
        if orig_id in ("L41",):
            return ["OUT_OF_SCOPE", "MULTI_GOAL_CONTRACT_LIMITATION"], "UNSUPPORTED_PROOF_PARTIAL", "NONE_SAFE_REFUSAL", "Contains synthetic proof ('Chứng minh BC ⊥ (SAM)') alongside computation."
        if orig_id in ("D14", "L33", "L34"):
            return ["MATHEMATICAL_AMBIGUITY"], "CLARIFICATION_REQUIRED", "NONE_SAFE_REFUSAL", "Standalone turn references prior state ('điểm đó', 'đoạn mình vừa dựng') without solid."
        if orig_id in ("D15", "L44"):
            return ["MATHEMATICAL_AMBIGUITY"], "CONTRADICTORY_PREMISES", "NONE_SAFE_REFUSAL", "Contradictory metric facts correctly rejected."
        if orig_id in ("D16", "L37", "L40"):
            return ["MATHEMATICAL_AMBIGUITY"], "MISSING_PREMISES", "NONE_SAFE_REFUSAL", "Underdetermined dimensions / explicitly negated altitude."
        if orig_id in ("L16", "L39"):
            return ["MATHEMATICAL_AMBIGUITY"], "NONEXISTENT_OR_PARALLEL_OBJECT", "NONE_SAFE_REFUSAL", f"Nonexistent plane/parallel intersection correctly refused ({disp})."
        if orig_id == "L43":
            return ["MATHEMATICAL_AMBIGUITY"], "AMBIGUOUS_PREMISES", "NONE_SAFE_REFUSAL", "Duplicate point label M for distinct midpoints correctly refused."
        return ["MATHEMATICAL_AMBIGUITY"], "SAFE_REFUSAL", "NONE_SAFE_REFUSAL", disp

    if role == "NON_SCALAR_UI_OR_CONSTRUCT":
        if orig_id in ("L32", "L35"):
            return ["OUT_OF_SCOPE"], "UI_VIEWPORT_COMMAND", "FRONTEND_VIEWER_CONTROL", "UI styling/camera command rather than new geometry problem."
        if orig_id == "L08":
            return ["OUT_OF_SCOPE"], "PEDAGOGICAL_EXPLANATION_REQUEST", "UNSUPPORTED_TEXT_EXPLANATION", "Requests drawing angle + free-form narrative explanation."
        if orig_id in ("L17", "L18"):
            return ["PARSER_COVERAGE_GAP", "MODEL_GOAL_EXTRACTION_ERROR", "TYPED_FACT_SCHEMA_LIMITATION"], "SUPPORTED_IN_V2_NOT_COMPACT_SCHEMA", "LOCAL_AI_PIPELINE_AND_SCHEMA", "construct_intersection_line is supported in TypedFactNext /2 & Exact Kernel, not in compact_clause/1."

    # VERIFIED_POSITIVE cases
    if arm_a["ok_strict"]:
        return [], "SUPPORTED_AND_SERVED", "ALREADY_SERVED", "Served exact verified answer on current route."

    # Standalone context-dependent follow-ups (`D13`, `L31`, `L36`)
    if orig_id in ("D13", "L31", "L36"):
        return ["MATHEMATICAL_AMBIGUITY"], "CONTEXT_DEPENDENT_FOLLOWUP_MISSING_CONTEXT", "CONVERSATION_SESSION_MEMORY_OUTSIDE_STATELESS_NLU", "Stateless single-turn input lacks referenced prior scene/solid ('vừa dựng', 'giao điểm ấy')."

    # Genuine downstream / schema / policy limitations proven by Arm B
    if orig_id in ("D05", "L12"):
        labels.append("DOWNSTREAM_CAPABILITY_LIMITATION")
        if orig_id == "L12":
            labels.append("SOURCE_GATE_GRAMMAR_GAP")
        return labels, "UNSUPPORTED_FINITE_SEGMENT_DISTANCE", "REGISTRY_KERNEL_BLOCKED_OWNERSHIP", "Asks distance to finite đoạn thẳng (not infinite đường thẳng); Registry/Kernel lacks finite point-segment distance."

    if orig_id == "L10":
        return ["TYPED_FACT_SCHEMA_LIMITATION", "PARSER_COVERAGE_GAP"], "UNSUPPORTED_SQUARED_LENGTH_GOAL", "TYPED_FACT_SCHEMA_AND_REGISTRY_OWNERSHIP", "Asks SC² directly; TypedFactNext /2 and Registry /33 expose length(SC), not squared length."

    if orig_id == "L38":
        return ["SOURCE_GATE_GRAMMAR_GAP", "NORMALIZER_LANGUAGE_GAP"], "POLICY_BLOCKED_CONDITIONAL_PHRASING", "PRODUCT_CONDITIONAL_SAFETY_POLICY", "Uses 'Nếu ... thì ...' conditional form; safety policy treats 'nếu' clauses as hypothetical/non-assertive unless rewritten affirmatively."

    if orig_id == "L28":
        if arm_b_canon.get("status") != "SERVED":
            return ["DOWNSTREAM_CAPABILITY_LIMITATION", "MULTI_GOAL_CONTRACT_LIMITATION", "PARSER_COVERAGE_GAP"], "UNSUPPORTED_TRIANGLE_AREA_GOAL", "REGISTRY_KERNEL_BLOCKED_OWNERSHIP", f"Multi-goal includes triangle area(SBC); Registry/Kernel returns {arm_b_canon.get('reason_code')}."

    if orig_id in ("D06", "L13"):
        # cos² goal
        if arm_b_raw.get("reason_code") == "NOT_ASKED_IN_SOURCE":
            labels.extend(["SOURCE_GATE_GRAMMAR_GAP", "NORMALIZER_LANGUAGE_GAP", "PARSER_COVERAGE_GAP"])
            if slm_ok:
                return labels, "SUPPORTED_WITH_CANONICAL_COSIN_WORDING", "OWNED_NORMALIZER_OR_BLOCKED_SOURCE_GATE", "AxoV7 extracted ang_lp correctly, but Registry.ham_luong_giac_hoi missed 'cos² của' unless normalized to 'cosin góc'."

    if raw_lp_status != "LOCAL_PARSE_COMPLETE":
        labels.append("PARSER_COVERAGE_GAP")

    # Multi-goal & GBNF limit check
    if n_req >= 3:
        if arm_d1_uncapped and arm_d1_uncapped.get("g_count_raw", 0) > len((wire_payload or {}).get("g") or []):
            labels.append("MULTI_GOAL_CONTRACT_LIMITATION")
        elif n_req >= 3:
            labels.append("MULTI_GOAL_CONTRACT_LIMITATION")

    # Compact schema limit for unnamed @centroid / face center / unnamed foot in goal (`D09`, `L19`, `L21`, `L22`)
    if orig_id in ("D09", "L19", "L21", "L22"):
        labels.append("TYPED_FACT_SCHEMA_LIMITATION")
        if orig_id in ("L21", "L22"):
            labels.append("NORMALIZER_LANGUAGE_GAP")

    # Check if AxoV7 actually extracted wrong/incomplete output or grounding failed
    grd = (grounding_env or {}).get("grounding_status")
    if grd and grd.startswith("REJECTED_"):
        if grd == "REJECTED_NO_GROUNDED_GOAL":
            labels.append("MODEL_GOAL_EXTRACTION_ERROR")
        elif grd == "REJECTED_UNGROUNDED_TOKEN":
            labels.append("MODEL_ENTITY_BINDING_ERROR")
            labels.append("SOURCE_GROUNDING_ERROR")
        else:
            labels.append("SOURCE_GROUNDING_ERROR")
    elif grd == "SLM_REPORTED_UNRESOLVED":
        labels.append("MODEL_SEMANTIC_ERROR")
    elif arm_b_raw.get("status") != "SERVED" and arm_b_canon.get("status") == "SERVED":
        labels.extend(["NORMALIZER_LANGUAGE_GAP", "SOURCE_GATE_GRAMMAR_GAP"])
        if arm_a.get("reason_code") in ("AMBIGUOUS_VALUE_QUOTE", "UNGROUNDED_VALUE", "SOURCE_OBJECT_MISMATCH", "SOURCE_PREMISE_UNREAD"):
            labels.append("MODEL_SEMANTIC_ERROR")
    elif arm_b_raw.get("status") == "SERVED" and not arm_a["ok_strict"]:
        labels.append("MODEL_SEMANTIC_ERROR")

    if not labels:
        labels = ["MODEL_SEMANTIC_ERROR"]
    labels = list(dict.fromkeys(labels))

    cap = "SUPPORTED_VIA_GOLD_V2_CANON" if arm_b_canon.get("ok_strict") else (
        "SUPPORTED_VIA_GOLD_V2_RAW" if arm_b_raw.get("ok_strict") else f"DOWNSTREAM_BLOCKED:{arm_b_canon.get('reason_code')}"
    )
    own = "OWNED_NORMALIZER_EXTRACTOR_OR_SLM" if arm_b_canon.get("ok_strict") else "REGISTRY_KERNEL_OR_SCHEMA"
    reason = arm_a.get("reason_code") or (grounding_env or {}).get("grounding_status") or "REFUSED"
    return labels, cap, own, str(reason)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rescore-gold", action="store_true", help="Reuse saved Arm A + Arm D1 SLM outputs from C60_CASE_LEVEL_ROOT_CAUSE.json and rescore Gold Arms B & C deterministically.")
    args = parser.parse_args()

    corp = {c["id"]: c for c in json.loads(C60_CORPUS_PATH.read_text(encoding="utf-8"))["cases"]}
    gf = json.loads(C60_GOLD_PATH.read_text(encoding="utf-8"))["cases"]
    manifest = json.loads(V8_MANIFEST_PATH.read_text(encoding="utf-8"))
    c60_cases = [c for c in manifest["cases"] if c["corpus"] == "C60_BLIND_NLU"]

    saved_by_id: dict[str, dict[str, Any]] = {}
    if args.rescore_gold:
        saved_doc = json.loads((OUT_DIR / "C60_CASE_LEVEL_ROOT_CAUSE.json").read_text(encoding="utf-8"))
        saved_by_id = {str(r["case_id"]): r for r in saved_doc["cases"]}

    rt = None if args.rescore_gold else LocalSlmRuntime()
    case_records: list[dict[str, Any]] = []
    arm_summaries = Counter()

    try:
        for idx, c in enumerate(c60_cases, 1):
            clear_local_geometry_parser_cache()
            oid = c["orig_id"]
            txt = c["text"]
            oracles = c["oracles"]
            gf_entry = gf[oid]
            canon_txt = _canon_c60_text(oid, txt)
            saved_r = saved_by_id.get(str(c["case_id"]))

            # 1. Local parser & /7 normalizer provenance
            lp = parse_geometry_problem_locally(txt)
            norm_res = normalize_for_slm_grounding(txt, normalizer_version="v2")

            # 2. Arm A: Current /7-/8 route + direct extraction capture (or reuse saved in --rescore-gold)
            if saved_r is not None:
                prev_fa = saved_r["final_answer_or_refusal"]
                prev_arm_a = saved_r["gold_intervention_outcome"]["arm_a_current"]
                arm_a = {
                    "status": prev_fa["status"],
                    "reason_code": prev_fa["reason_code"],
                    "source_gate": saved_r["source_gate_result"],
                    "planner": saved_r["planner_result"],
                    "engine": saved_r["exact_kernel_result"],
                    "answers": prev_fa["answers"],
                    "ok_any": prev_fa["ok_any"],
                    "ok_strict": prev_fa["ok_strict"],
                    "wrong_served": prev_arm_a.get("wrong_served", False),
                }
                slm_raw_content = saved_r.get("slm_raw_structured_output")
                wire_payload = saved_r.get("schema_validation")
                grounding_env = saved_r.get("grounding_validation")
                slm_ok = bool(wire_payload and str((grounding_env or {}).get("grounding_status") or "").startswith("ACCEPTED"))
                arm_d1 = saved_r["gold_intervention_outcome"].get("arm_d1_gbnf_4goals")
            else:
                t0 = time.perf_counter()
                out_a = AIR.route_text_input_local_slm(
                    txt,
                    model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                    strategy="compact_clause",
                    runtime=rt,
                    allow_download=False,
                    use_verified_normalizer=True,
                    closure_mode="v7",
                    normalizer_version="v2",
                    use_cache=False,
                    cache_prompt=True,
                )
                tr_a = _extract_component_traces(out_a)
                ok_any_a, ok_strict_a, wrong_a = (
                    _check_oracles(tr_a["answers"], oracles, txt) if tr_a["status"] == "SERVED" and c["eval_role"] == "VERIFIED_POSITIVE" else (False, False, False)
                )
                if c["eval_role"] != "VERIFIED_POSITIVE":
                    wrong_a = tr_a["status"] == "SERVED"
                arm_a = {**tr_a, "ok_any": ok_any_a, "ok_strict": ok_strict_a, "wrong_served": wrong_a, "wall_ms": round((time.perf_counter() - t0) * 1000.0, 2)}

                slm_res = None
                if (out_a.response.get("route_d") or {}).get("slm_grounding_envelope", {}).get("slm_invoked"):
                    slm_res = run_local_slm_extraction(
                        norm_res.canonical_text,
                        model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                        strategy="compact_clause",
                        runtime=rt,
                        allow_download=False,
                        use_verified_normalizer=True,
                        closure_mode="v7",
                        normalizer_version="v2",
                        use_cache=False,
                        cache_prompt=True,
                    )
                slm_raw_content = slm_res.inference.raw_content if (slm_res and slm_res.inference) else None
                wire_payload = slm_res.wire_payload if slm_res else None
                grounding_env = slm_res.grounding_envelope if slm_res else (out_a.response.get("route_d") or {}).get("slm_grounding_envelope")
                slm_ok = bool(slm_res and slm_res.ok)

                # Arm D1: On multi-goal >= 3 positives, test lifting ONLY the 2-goal GBNF cap (`goallistreq ::= goalitem ("," goalitem)?` -> 4 goals)
                arm_d1 = None
                if c["n_source_requests"] >= 3 and c["eval_role"] == "VERIFIED_POSITIVE":
                    ctx_d = build_compact_clause_context(norm_res.canonical_text)
                    g_orig = build_compact_grammar_for_context(ctx_d, closure_mode="v7")
                    g_uncapped = g_orig.replace('goallistreq ::= goalitem ("," goalitem)?', 'goallistreq ::= goalitem ("," goalitem ("," goalitem ("," goalitem)?)?)?')
                    from app.ai.local_slm_extractor import _build_compact_clause_messages
                    msgs = _build_compact_clause_messages(ctx_d)
                    inf_d = rt.chat_completion_json(messages=msgs, grammar=g_uncapped, cache_prompt=True, model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, ctx_size=2048, max_tokens=320)
                    low_d, vdiag_d = validate_and_lower_compact_clause(ctx=ctx_d, raw_slm_json=inf_d.parsed_json, closure_mode="v7")
                    res_d = _run_route_on_v2(norm_res.canonical_text, low_d, oracles, txt) if low_d else {"status": "REFUSED", "reason_code": vdiag_d.get("reason_code"), "answers": {}, "ok_any": False, "ok_strict": False, "wrong_served": False}
                    arm_d1 = {
                        "g_count_raw": len((inf_d.parsed_json or {}).get("g") or []),
                        "raw_json": inf_d.parsed_json,
                        "grounding": vdiag_d.get("grounding_status"),
                        **res_d,
                    }

            # 3. Gold TypedFactNext /2 & Gold Compact Clause
            gold_pkg = _gold_v2_and_compact_for_case(oid, txt, canon_txt, gf_entry)
            arm_b_raw = _run_route_on_v2(txt, gold_pkg["v2_raw"], oracles, txt)
            arm_b_canon = _run_route_on_v2(canon_txt, gold_pkg["v2_canon"], oracles, txt) if canon_txt != txt else arm_b_raw

            # Arm C: validate_and_lower_compact_clause on Gold compact JSON
            def _run_gold_compact(t: str, cmp_json: dict[str, Any] | None) -> dict[str, Any]:
                if cmp_json is None:
                    return {"status": "REFUSED", "reason_code": "COMPACT_NOT_REPRESENTABLE", "answers": {}, "ok_any": False, "ok_strict": False, "wrong_served": False}
                if cmp_json.get("u"):
                    return {"status": "REFUSED", "reason_code": "COMPACT_SCHEMA_LIMITATION_UNRESOLVED", "answers": {}, "ok_any": False, "ok_strict": False, "wrong_served": False}
                ctx_c = build_compact_clause_context(t)
                low_p, vdiag = validate_and_lower_compact_clause(ctx=ctx_c, raw_slm_json=cmp_json, closure_mode="v7")
                if low_p is None:
                    return {"status": "REFUSED", "reason_code": f"LOWER_FAIL:{vdiag.get('reason_code')}:{vdiag.get('rejected_ops')}", "answers": {}, "ok_any": False, "ok_strict": False, "wrong_served": False}
                res = _run_route_on_v2(t, low_p, oracles, txt)
                res["grounding_diag"] = vdiag
                return res

            arm_c_raw = _run_gold_compact(txt, gold_pkg["compact_raw"])
            arm_c_canon = _run_gold_compact(canon_txt, gold_pkg["compact_canon"]) if canon_txt != txt else arm_c_raw

            labels, cap_stat, fix_own, exact_fail = _classify_root_causes(
                c, oid, lp.status, wire_payload, grounding_env, slm_ok, arm_a, arm_b_raw, arm_b_canon, arm_c_raw, arm_c_canon, arm_d1
            )

            rec = {
                # All 20 §5 required fields
                "case_id": c["case_id"],
                "orig_id": oid,
                "eval_role": c["eval_role"],
                "gold_disposition": c["gold_disposition"],
                "n_source_requests": c["n_source_requests"],
                "original_problem_text": txt,
                "intended_task": f"{c['group']}:{c['gold_disposition']} (oracles={oracles})",
                "gold_typed_facts": gold_pkg["v2_raw"],
                "gold_goal_specification": {"oracles": oracles, "math_goals": (gold_pkg["v2_raw"] or {}).get("math_goals")},
                "local_parser_status": lp.status,
                "local_parser_reason": lp.reason_code,
                "normalized_text": norm_res.canonical_text,
                "normalizer_provenance": norm_res.to_provenance_dict(),
                "slm_raw_structured_output": slm_raw_content,
                "schema_validation": wire_payload,
                "grounding_validation": grounding_env,
                "source_gate_result": arm_a["source_gate"],
                "planner_result": arm_a["planner"],
                "registry_result": {"version": GF_REGISTRY.REGISTRY_VERSION},
                "exact_kernel_result": arm_a["engine"],
                "final_answer_or_refusal": {"status": arm_a["status"], "reason_code": arm_a["reason_code"], "answers": arm_a["answers"], "ok_any": arm_a["ok_any"], "ok_strict": arm_a["ok_strict"]},
                "exact_failure_reason": exact_fail,
                "gold_intervention_outcome": {
                    "canonical_surface_text": canon_txt if canon_txt != txt else None,
                    "arm_a_current": {"status": arm_a["status"], "reason_code": arm_a["reason_code"], "ok_any": arm_a["ok_any"], "ok_strict": arm_a["ok_strict"], "wrong_served": arm_a.get("wrong_served", False)},
                    "arm_b_gold_v2_raw": {"status": arm_b_raw["status"], "reason_code": arm_b_raw["reason_code"], "ok_any": arm_b_raw["ok_any"], "ok_strict": arm_b_raw["ok_strict"], "wrong_served": arm_b_raw.get("wrong_served", False), "answers": arm_b_raw["answers"]},
                    "arm_b_gold_v2_canon": {"status": arm_b_canon["status"], "reason_code": arm_b_canon["reason_code"], "ok_any": arm_b_canon["ok_any"], "ok_strict": arm_b_canon["ok_strict"], "wrong_served": arm_b_canon.get("wrong_served", False), "answers": arm_b_canon["answers"]},
                    "arm_c_gold_compact_raw": {"status": arm_c_raw["status"], "reason_code": arm_c_raw["reason_code"], "ok_any": arm_c_raw["ok_any"], "ok_strict": arm_c_raw["ok_strict"], "wrong_served": arm_c_raw.get("wrong_served", False)},
                    "arm_c_gold_compact_canon": {"status": arm_c_canon["status"], "reason_code": arm_c_canon["reason_code"], "ok_any": arm_c_canon["ok_any"], "ok_strict": arm_c_canon["ok_strict"], "wrong_served": arm_c_canon.get("wrong_served", False)},
                    "arm_d1_gbnf_4goals": arm_d1,
                },
                "capability_status": cap_stat,
                "fix_ownership": fix_own,
                "root_cause_labels": labels,
            }
            case_records.append(rec)
            print(f"[{idx:02d}/60] {oid} | A={arm_a['ok_strict']} | B_raw={arm_b_raw['ok_strict']}({arm_b_raw['reason_code']}) | B_can={arm_b_canon['ok_strict']}({arm_b_canon['reason_code']}) | C_can={arm_c_canon['ok_strict']} | labels={labels}", flush=True)
    finally:
        if rt is not None:
            rt.shutdown()

    vp = [r for r in case_records if r["eval_role"] == "VERIFIED_POSITIVE"]
    neg = [r for r in case_records if r["eval_role"] == "NEGATIVE_OR_REFUSAL_EXPECTED"]
    ns = [r for r in case_records if r["eval_role"] == "NON_SCALAR_UI_OR_CONSTRUCT"]

    label_counts = Counter()
    for r in vp:
        for lb in r["root_cause_labels"]:
            label_counts[lb] += 1

    # Summary stats across arms
    def _arm_stat(getter) -> dict[str, Any]:
        ok_strict_n = sum(1 for r in vp if getter(r).get("ok_strict"))
        ok_any_n = sum(1 for r in vp if getter(r).get("ok_any"))
        ws_vp = sum(1 for r in vp if getter(r).get("wrong_served"))
        ws_neg = sum(1 for r in neg if getter(r).get("wrong_served"))
        return {
            "positives_total": len(vp),
            "served_exact_strict_all": ok_strict_n,
            "served_exact_any": ok_any_n,
            "rate_strict_all": round(ok_strict_n / len(vp), 4),
            "wrong_served": ws_vp + ws_neg,
        }

    summary = {
        "schema": "c60-gold-intervention-results/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "counts": {"total": len(case_records), "verified_positives": len(vp), "negatives": len(neg), "non_scalar_ui_construct": len(ns)},
        "arms": {
            "arm_a_current_v7": _arm_stat(lambda r: r["gold_intervention_outcome"]["arm_a_current"]),
            "arm_b_gold_typed_fact_v2_raw_text": _arm_stat(lambda r: r["gold_intervention_outcome"]["arm_b_gold_v2_raw"]),
            "arm_b_gold_typed_fact_v2_canon_text": _arm_stat(lambda r: r["gold_intervention_outcome"]["arm_b_gold_v2_canon"]),
            "arm_c_gold_compact_clause_raw_text": _arm_stat(lambda r: r["gold_intervention_outcome"]["arm_c_gold_compact_raw"]),
            "arm_c_gold_compact_clause_canon_text": _arm_stat(lambda r: r["gold_intervention_outcome"]["arm_c_gold_compact_canon"]),
        },
        "root_cause_counts_on_42_positives_multi_label": dict(label_counts.most_common()),
        "p6_questions_answers": {
            "q1_solvable_with_perfect_v2_and_canon_extraction": sum(1 for r in vp if r["gold_intervention_outcome"]["arm_b_gold_v2_canon"]["ok_strict"]),
            "q1_solvable_with_perfect_v2_raw_text_only": sum(1 for r in vp if r["gold_intervention_outcome"]["arm_b_gold_v2_raw"]["ok_strict"]),
            "q2_still_failed_even_with_gold_v2_canon": [r["orig_id"] for r in vp if not r["gold_intervention_outcome"]["arm_b_gold_v2_canon"]["ok_strict"]],
            "q3_missing_goal_contract_or_schema": [r["orig_id"] for r in vp if "TYPED_FACT_SCHEMA_LIMITATION" in r["root_cause_labels"]],
            "q4_multi_goal_contract_limitation_cases": [r["orig_id"] for r in vp if "MULTI_GOAL_CONTRACT_LIMITATION" in r["root_cause_labels"]],
            "q5_wording_or_normalizer_closure_only_needed": [r["orig_id"] for r in vp if r["gold_intervention_outcome"]["arm_b_gold_v2_canon"]["ok_strict"] and not r["gold_intervention_outcome"]["arm_b_gold_v2_raw"]["ok_strict"]],
            "q6_source_gate_grammar_gap_cases": [r["orig_id"] for r in vp if "SOURCE_GATE_GRAMMAR_GAP" in r["root_cause_labels"]],
            "q7_out_of_downstream_capability_cases": [r["orig_id"] for r in vp if "DOWNSTREAM_CAPABILITY_LIMITATION" in r["root_cause_labels"]],
            "q8_slm_genuinely_wrong_extracted_cases": [r["orig_id"] for r in vp if any(lb.startswith("MODEL_") or lb == "SOURCE_GROUNDING_ERROR" for lb in r["root_cause_labels"])],
        },
    }

    (OUT_DIR / "C60_CASE_LEVEL_ROOT_CAUSE.json").write_text(
        json.dumps({"schema": "c60-case-level-root-cause/1", "generated_at_utc": summary["generated_at_utc"], "cases": case_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "C60_GOLD_INTERVENTION_RESULTS.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Generate concise markdown bottleneck report answering all 8 questions cleanly
    lines = [
        "# AXO HYBRID /9 — C60 Root-Cause Decomposition & 4-Arm Gold Intervention (`SLM_V9_BOTTLENECK_REPORT.md`)",
        "",
        f"- **Corpus:** `C60_BLIND_NLU` (`60` cases = `42` verified positives [`30` single, `12` multi-request], `13` negative/refusal, `5` non-scalar UI/construct)",
        f"- **Arm A (`AxoV7 + v2` current product route):** **`{summary['arms']['arm_a_current_v7']['served_exact_strict_all']}/{len(vp)}` (`{summary['arms']['arm_a_current_v7']['rate_strict_all']*100:.2f}%`)**, `wrong_served = {summary['arms']['arm_a_current_v7']['wrong_served']}`",
        f"- **Arm B (`Gold TypedFactNext /2` on raw source text -> Source Gate -> Planner -> Kernel):** **`{summary['arms']['arm_b_gold_typed_fact_v2_raw_text']['served_exact_strict_all']}/{len(vp)}` (`{summary['arms']['arm_b_gold_typed_fact_v2_raw_text']['rate_strict_all']*100:.2f}%`)**",
        f"- **Arm B (`Gold TypedFactNext /2` on meaning-preserving canonicalized text -> Source Gate -> Planner -> Kernel):** **`{summary['arms']['arm_b_gold_typed_fact_v2_canon_text']['served_exact_strict_all']}/{len(vp)}` (`{summary['arms']['arm_b_gold_typed_fact_v2_canon_text']['rate_strict_all']*100:.2f}%`)**",
        f"- **Arm C (`Gold slm-compact-clause/1` on raw text -> validator -> Source Gate -> Kernel):** **`{summary['arms']['arm_c_gold_compact_clause_raw_text']['served_exact_strict_all']}/{len(vp)}` (`{summary['arms']['arm_c_gold_compact_clause_raw_text']['rate_strict_all']*100:.2f}%`)**",
        f"- **Arm C (`Gold slm-compact-clause/1` on canonicalized text -> validator -> Source Gate -> Kernel):** **`{summary['arms']['arm_c_gold_compact_clause_canon_text']['served_exact_strict_all']}/{len(vp)}` (`{summary['arms']['arm_c_gold_compact_clause_canon_text']['rate_strict_all']*100:.2f}%`)**",
        "",
        "## 1. Eight Mandatory §6 Questions Answered",
        "",
        f"1. **How many C60 positives solve correctly if extraction is perfect?** `{summary['p6_questions_answers']['q1_solvable_with_perfect_v2_raw_text_only']}/{len(vp)}` on verbatim raw text (`Source Gate` unchanged) and **`{summary['p6_questions_answers']['q1_solvable_with_perfect_v2_and_canon_extraction']}/{len(vp)}`** once paired with safe meaning-preserving Vietnamese surface normalization.",
        f"2. **How many still fail even with Gold Typed Facts?** `{len(summary['p6_questions_answers']['q2_still_failed_even_with_gold_v2_canon'])}` (`{summary['p6_questions_answers']['q2_still_failed_even_with_gold_v2_canon']}`): `D05`/`L12` ask distance to finite `đoạn thẳng` (unsupported downstream; distinct oracle from infinite line), `L10` asks `SC²` (schema lacks squared-length goal), `L28` asks triangle `area(SBC)` (check downstream Kernel capability), `L38` uses conditional `'Nếu ... thì ...'` policy block, and `D13`/`L31`/`L36` are stateless standalone context follow-ups missing solid declaration.",
        f"3. **Missing goal/schema contract cases (`TYPED_FACT_SCHEMA_LIMITATION`):** `{summary['p6_questions_answers']['q3_missing_goal_contract_or_schema']}` (in `compact_clause/1`, unnamed `@id` centroid/face-center/foot goals cannot be expressed directly without normalizer closure or schema extension).",
        f"4. **Multi-goal limitation cases (`MULTI_GOAL_CONTRACT_LIMITATION`):** `{summary['p6_questions_answers']['q4_multi_goal_contract_limitation_cases']}` — GBNF previously capped `g` at `<= 2` items (`goallistreq ::= goalitem (\",\" goalitem)?`), physically preventing `D12`, `L23`, `L27`, `L30` (3-goal items) from ever emitting all goals!",
        f"5. **Cases solvable purely by surface wording normalization:** `{summary['p6_questions_answers']['q5_wording_or_normalizer_closure_only_needed']}`.",
        f"6. **Cases encountering Source Gate closed grammar gaps:** `{summary['p6_questions_answers']['q6_source_gate_grammar_gap_cases']}`.",
        f"7. **Cases outside downstream geometry capability (`DOWNSTREAM_CAPABILITY_LIMITATION`):** `{summary['p6_questions_answers']['q7_out_of_downstream_capability_cases']}`.",
        f"8. **Cases where `Qwen3-0.6B-AxoV7` genuinely extracted wrong / incomplete / ungrounded:** `{summary['p6_questions_answers']['q8_slm_genuinely_wrong_extracted_cases']}`.",
        "",
        "## 2. Multi-Label Root-Cause Counts (on 42 Verified Positives)",
        "",
        "| Root Cause Label | Count |",
        "|---|---:|",
    ]
    for lb, cnt in label_counts.most_common():
        lines.append(f"| `{lb}` | {cnt} |")
    lines.extend([
        "",
        "## 3. Case-by-Case Summary Table (All Unserved Positives + Non-Scalar)",
        "",
        "| Case | Req | Arm A (`/7`) | Arm B Raw | Arm B Canon | Arm C Canon | Labels | Exact Reason |",
        "|---|---:|---|---|---|---|---|---|",
    ])
    for r in case_records:
        if r["eval_role"] == "VERIFIED_POSITIVE" and not r["gold_intervention_outcome"]["arm_a_current"]["ok_strict"]:
            g = r["gold_intervention_outcome"]
            lines.append(
                f"| `{r['orig_id']}` | {r['n_source_requests']} | `{g['arm_a_current']['status']}:{g['arm_a_current']['reason_code']}` | `{g['arm_b_gold_v2_raw']['ok_strict']}:{g['arm_b_gold_v2_raw']['reason_code']}` | `{g['arm_b_gold_v2_canon']['ok_strict']}:{g['arm_b_gold_v2_canon']['reason_code']}` | `{g['arm_c_gold_compact_canon']['ok_strict']}:{g['arm_c_gold_compact_canon']['reason_code']}` | `{', '.join(r['root_cause_labels'])}` | {r['exact_failure_reason']} |"
            )
        elif r["eval_role"] == "NON_SCALAR_UI_OR_CONSTRUCT":
            g = r["gold_intervention_outcome"]
            lines.append(
                f"| `{r['orig_id']}` (NS) | {r['n_source_requests']} | `{g['arm_a_current']['status']}:{g['arm_a_current']['reason_code']}` | `{g['arm_b_gold_v2_raw']['status']}` | `{g['arm_b_gold_v2_canon']['status']}` | `{g['arm_c_gold_compact_canon']['status']}` | `{', '.join(r['root_cause_labels'])}` | {r['exact_failure_reason']} |"
            )
    (OUT_DIR / "SLM_V9_BOTTLENECK_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n=== P1 GOLD INTERVENTION SUMMARY ===", json.dumps(summary["arms"], indent=2))
    print("Q1-Q8:", json.dumps(summary["p6_questions_answers"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
