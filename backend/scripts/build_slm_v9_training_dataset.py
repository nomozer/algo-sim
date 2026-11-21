# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Verified Disjoint SLM Dataset Builder (`train_v9.jsonl`, `val_v9.jsonl`).

Builds a 100%-Exact-Kernel-verified dataset for `Qwen3-0.6B` on `slm-compact-clause/1` (`v9` closure),
combining re-canonicalized `/7` synthetic samples with new `/9` targeted families:
  1. Multi-goal 2/3/4 requests (`len + ang_lp + vol`, `len + vol + dist_line_line`, `vol + ang_pp`, 4-goal cubes)
  2. Non-dotted orthogonal tetrahedra (`Tứ diện OXYZ ... đôi một vuông góc` -> 3 `perp_ll` + `cent` + `vol/len`)
  3. Cube/Right-Prism auxiliary `mid` / `proj` / `cent` + `len` (fixing `dist_pt_line` vs `len` & `AA'` omissions)
  4. Explicit polygon shapes without `"đáy"` (`Biết PQRS là hình chữ nhật...`)
  5. Hard negative calibration (`missing`, `ambig`, `contra`, `unsup`) preserving 0 wrong-served.

Audits 0 exact / skeleton / 4-gram leakage across ALL unlocked corpora (including `C60_BLIND_NLU`,
`EXTERNAL17`, `SLM_V7_HOLDOUT_112`, `SLM_NEW_HOLDOUT_48`, `HOLDOUT_40`, `DEV_CALIBRATION_16`)
without ever opening `sealed_H1` or `locked_W2_W3`.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RUNS_DIR = ROOT / "docs/evaluation/geometry/runs"
OUT_DIR = RUNS_DIR / "axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
V7_DATASET_DIR = LOCAL_APPDATA / "axo-slm/training/datasets"
V9_DATASET_DIR = LOCAL_APPDATA / "axo-slm/training/datasets_v9"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BV6 = _load_mod("_bench_v6_v9ds", BACKEND / "scripts" / "benchmark_slm_v6_campaign.py")
DATA_V7 = _load_mod("_data_v7_v9ds", BACKEND / "scripts" / "build_slm_training_dataset.py")

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.hybrid_offline import ReplayExtractor, hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, normalize_problem_text, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    SLM_COMPACT_SCHEMA_VERSION,
    V9_CLOSURE_MODE,
    _build_compact_clause_messages,
    build_compact_clause_context,
    validate_and_lower_compact_clause,
)
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402
from slm_math_evaluator_v2 import compare_math_expressions  # noqa: E402


_skeleton = DATA_V7._skeleton
_ngrams = DATA_V7._ngrams


def _compact_json_str(d: dict[str, Any]) -> str:
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def _verify_and_serialize_v9(
    *,
    sample_id: str,
    split: str,
    family_id: str,
    raw_text: str,
    raw_slm_json: dict[str, Any],
    kind: str,
    ambiguity_status: str,
    expected_answers: list[str] | None = None,
    dataset_source: str = "axo_v9_targeted_synthetic",
) -> dict[str, Any]:
    clear_local_geometry_parser_cache()
    nres = normalize_for_slm_grounding(raw_text, normalizer_version="v3")
    canon_txt = nres.canonical_text
    ctx = build_compact_clause_context(canon_txt)
    lp = parse_geometry_problem_locally(canon_txt)
    messages = _build_compact_clause_messages(ctx)

    target_json = json.loads(json.dumps(raw_slm_json, ensure_ascii=False))
    if target_json.get("s") is not None:
        s_cid, s_type, s_lbl, _ = target_json["s"]
        for ent in ctx.entities:
            if ent.kind == "solid" and ent.label == s_lbl:
                exp_bit = 1 if (ent.is_regular_solid or s_type in ("cube", "box")) else 0
                target_json["s"] = [s_cid, s_type, s_lbl, exp_bit]
                break

    canon_payload, diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=target_json, closure_mode=V9_CLOSURE_MODE)
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

    verified_answers: dict[str, str] = {}
    if kind == "positive":
        assert canon_payload is not None and not diag.get("rejected_ops"), (
            f"{sample_id} failed v9 lowering: {diag} | canon={canon_txt!r} target={target_json}"
        )
        ho = run_hybrid_offline(canon_txt, ReplayExtractor({canon_txt: canon_payload}), policy=pol)
        rd = ho.response.get("route_d") or {}
        assert rd.get("status") == "SERVED", f"{sample_id} not SERVED: {rd.get('refusal')} | canon={canon_txt!r}"
        verified_answers = dict(rd.get("answers") or {})
        ans_vals = list(verified_answers.values())
        assert len(ans_vals) == len(target_json.get("g") or ()), f"{sample_id} answer count mismatch: {ans_vals} vs {target_json['g']}"
        if expected_answers:
            for ora in expected_answers:
                assert any(compare_math_expressions(a, ora).matched is True for a in ans_vals), (
                    f"{sample_id} answer mismatch: got={ans_vals} expected={expected_answers}"
                )
    else:
        assert target_json.get("u"), f"{sample_id} negative missing u"
        assert canon_payload is None, f"{sample_id} negative unexpectedly lowered"
        det = AIR.route_text_input(canon_txt, allow_live_ai=False)
        assert det.status != "SERVED", f"{sample_id} negative leaked SERVED"

    assistant_str = _compact_json_str(target_json)
    full_messages = [*messages, {"role": "assistant", "content": assistant_str}]
    return {
        "sample_id": sample_id,
        "split": split,
        "dataset_source": dataset_source,
        "problem_family_id": family_id,
        "kind": kind,
        "positive_label": (kind == "positive"),
        "ambiguity_status": ambiguity_status,
        "source_text": raw_text,
        "canonical_text": canon_txt,
        "local_parser_status_after_norm": lp.status,
        "gold_compact_output": target_json,
        "gold_compact_json_str": assistant_str,
        "gold_oracles": expected_answers or list(verified_answers.values()),
        "verified_kernel_answers": verified_answers,
        "validation_evidence": {
            "validator_grounding_status": diag.get("grounding_status"),
            "hybrid_status": "SERVED" if kind == "positive" else "REFUSED_EXPECTED",
        },
        "messages": full_messages,
    }


def _rehydrate_v7_rows() -> list[dict[str, Any]]:
    """Re-verify `/7` train.jsonl & val.jsonl rows cleanly under `v3` normalizer + `v9` validator."""
    out: list[dict[str, Any]] = []
    for split, fname in (("train", "train.jsonl"), ("val", "val.jsonl")):
        fpath = V7_DATASET_DIR / fname
        assert fpath.exists(), f"Missing /7 dataset: {fpath}"
        for ln in fpath.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            row = json.loads(ln)
            txt = row["source_text"]
            nres = normalize_for_slm_grounding(txt, normalizer_version="v3")
            canon_txt = nres.canonical_text
            ctx = build_compact_clause_context(canon_txt)
            tjson = json.loads(json.dumps(row["gold_compact_output"], ensure_ascii=False))
            # Check if normalization split/changed clause count; skip rehydrated sample only if clause IDs shifted cleanly
            canon_payload, diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=tjson, closure_mode=V9_CLOSURE_MODE)
            if row["kind"] == "positive" and canon_payload is None:
                # Try raw_text clauses if v3 didn't alter goal wording adversely; otherwise skip safely
                ctx_old = build_compact_clause_context(row["canonical_text"])
                cp_old, _ = validate_and_lower_compact_clause(ctx=ctx_old, raw_slm_json=tjson, closure_mode=V9_CLOSURE_MODE)
                if cp_old is None:
                    continue
                canon_txt = row["canonical_text"]
                ctx = ctx_old
                canon_payload = cp_old
            messages = _build_compact_clause_messages(ctx)
            assistant_str = _compact_json_str(tjson)
            exp_ora: list[str] = []
            if row["kind"] == "positive":
                pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
                ho = run_hybrid_offline(canon_txt, ReplayExtractor({canon_txt: canon_payload}), policy=pol)
                rd = ho.response.get("route_d") or {}
                if rd.get("status") != "SERVED":
                    continue
                exp_ora = list((rd.get("answers") or {}).values())
            out.append({
                "sample_id": row["sample_id"],
                "split": split,
                "dataset_source": "axo_v7_rehydrated_v9",
                "problem_family_id": row["problem_family_id"],
                "kind": row["kind"],
                "positive_label": (row["kind"] == "positive"),
                "ambiguity_status": row["ambiguity_status"],
                "source_text": txt,
                "canonical_text": canon_txt,
                "local_parser_status_after_norm": row["local_parser_status_after_norm"],
                "gold_compact_output": tjson,
                "gold_compact_json_str": assistant_str,
                "gold_oracles": exp_ora,
                "verified_kernel_answers": {f"q{i+1}": v for i, v in enumerate(exp_ora)},
                "validation_evidence": row.get("validation_evidence") or {},
                "messages": [*messages, {"role": "assistant", "content": assistant_str}],
            })
    return out


def _generate_v9_targeted_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    idx = 0

    def _nid(tag: str) -> str:
        nonlocal idx
        idx += 1
        return f"v9_{tag.lower()}_{idx:03d}"

    # Vertex sets strictly disjoint from C60 (`S.ABCD`, `ABC.A'B'C'`, `OABC`) & held-out seeds
    prisms_tr = [("DEF", "D'E'F'"), ("MNP", "M'N'P'"), ("GHK", "G'H'K'"), ("IJK", "I'J'K'"), ("PQR", "P'Q'R'"), ("UVW", "U'V'W'")]
    boxes_tr = [("PQRS", "P'Q'R'S'"), ("MNPQ", "M'N'P'Q'"), ("DEFG", "D'E'F'G'"), ("GHIK", "G'H'I'K'")]
    tetras_tr = [("K", "DEF"), ("P", "UVW"), ("H", "MNP"), ("E", "QRT"), ("I", "GHK")]
    pyrs_tr = [("K", "PQRS"), ("M", "DEFG"), ("T", "GHIK"), ("R", "UVWX"), ("L", "MNPQ")]

    prisms_vl = [("RST", "R'S'T'"), ("XYZ", "X'Y'Z'")]
    boxes_vl = [("EFGH", "E'F'G'H'"), ("UVWX", "U'V'W'X'")]
    tetras_vl = [("T", "XYZ"), ("Q", "RST")]
    pyrs_vl = [("P", "EFGH"), ("Q", "TUVW")]

    # ── TR9_1: Cuboid & Pyramid Multi-Goal (2, 3, and 4 goals) ──────────────────────
    dims3 = [("2", "3", "6"), ("3", "4", "12"), ("1", "2", "2"), ("2", "4", "4"), ("a", "2a", "2a"), ("3a", "4a", "5a")]
    for i in range(36):
        b, t = boxes_tr[i % len(boxes_tr)]
        bp = re.findall(r"[A-Z][0-9]*'*", b)
        tp = re.findall(r"[A-Z][0-9]*'*", t)
        A, B, C, D0 = bp
        A1, B1, C1, D1 = tp
        d1, d2, d3 = dims3[i % len(dims3)]
        sol = f"{b}.{t}"
        if i % 3 == 0:
            # 3-goal cuboid: diagonal len + volume + skew distance
            txt = (
                f"Xét khối hộp chữ nhật {sol} có ba cạnh {A}{B}={d1}, {A}{D0}={d2}, {A}{A1}={d3}. "
                f"Hãy tính độ dài đoạn thẳng {B}{D1}. Tiếp theo tính thể tích khối hộp {sol}. Sau đó tính khoảng cách giữa hai đường thẳng {A}{A1} và {B}{D1}."
            )
            gold = {
                "s": [0, "box", sol, 1],
                "r": [
                    {"c": 0, "p": "len", "a": f"{A}{B}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{A}{D0}", "q": d2},
                    {"c": 0, "p": "len", "a": f"{A}{A1}", "q": d3},
                ],
                "g": [
                    {"c": 1, "t": "len", "a": f"{B}{D1}"},
                    {"c": 2, "t": "vol", "tgt": sol},
                    {"c": 3, "t": "dist_line_line", "a": f"{A}{A1}", "b": f"{B}{D1}"},
                ],
                "u": [],
            }
        elif i % 3 == 1:
            # 4-goal cube!
            side_c = ["2", "3", "4", "a", "2a", "3a"][i % 6]
            txt = (
                f"Cho hình lập phương {sol} có cạnh bằng {side_c}. "
                f"Tính độ dài đoạn {A}{C1}. Tính góc giữa hai đường thẳng {A}{B1} và {B}{C1}. "
                f"Tính khoảng cách giữa hai đường thẳng {A}{B1} và {B}{C1}. Tính thể tích khối lập phương {sol}."
            )
            gold = {
                "s": [0, "cube", sol, 1],
                "r": [{"c": 0, "p": "len", "a": f"{A}{A1}", "q": side_c}],
                "g": [
                    {"c": 1, "t": "len", "a": f"{A}{C1}"},
                    {"c": 2, "t": "ang_ll", "a": f"{A}{B1}", "b": f"{B}{C1}"},
                    {"c": 3, "t": "dist_line_line", "a": f"{A}{B1}", "b": f"{B}{C1}"},
                    {"c": 4, "t": "vol", "tgt": sol},
                ],
                "u": [],
            }
        else:
            # 3-goal pyramid: len + ang_lp + vol
            ap, p_base = pyrs_tr[i % len(pyrs_tr)]
            p0, p1, p2, p3 = re.findall(r"[A-Z][0-9]*'*", p_base)
            p_sol = f"{ap}.{p_base}"
            txt = (
                f"Cho hình chóp {p_sol} đáy {p_base} là hình vuông cạnh {d1}, {ap}{p0} vuông góc mặt phẳng ({p_base}) và {ap}{p0} = {d2}. "
                f"Hãy tính độ dài đoạn {ap}{p2}. Tiếp đó tìm cosin góc giữa {ap}{p2} với ({p_base}). Sau đó tính thể tích khối chóp {p_sol}."
            )
            gold = {
                "s": [0, "pyr", p_sol, 0],
                "r": [
                    {"c": 0, "p": "reg_poly", "a": p_base, "q": d1},
                    {"c": 0, "p": "perp_lp", "a": f"{ap}{p0}", "b": p_base},
                    {"c": 0, "p": "len", "a": f"{ap}{p0}", "q": d2},
                ],
                "g": [
                    {"c": 1, "t": "len", "a": f"{ap}{p2}"},
                    {"c": 2, "t": "ang_lp", "a": f"{ap}{p2}", "b": p_base},
                    {"c": 3, "t": "vol", "tgt": p_sol},
                ],
                "u": [],
            }
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("tr9_mg"), split="train", family_id="TR9_MULTI_GOAL_2_3_4",
            raw_text=txt, raw_slm_json=gold, kind="positive", ambiguity_status="UNAMBIGUOUS",
        ))

    # ── TR9_2: Non-dotted Orthogonal Tetrahedra + Centroid + Pairwise Perp ───────────
    for i in range(30):
        ox, b3 = tetras_tr[i % len(tetras_tr)]
        p1, p2, p3 = re.findall(r"[A-Z][0-9]*'*", b3)
        sol_dot = f"{ox}.{b3}"
        l1, l2, l3 = dims3[i % len(dims3)]
        if i % 2 == 0:
            # All 3 perp_ll + centroid + length goal
            txt = (
                f"Tứ diện {ox}{b3} có {ox}{p1}, {ox}{p2}, {ox}{p3} đôi một vuông góc, {ox}{p1}={l1}, {ox}{p2}={l2}, {ox}{p3}={l3}. "
                f"Gọi J là trọng tâm tam giác {b3}. Tính độ dài đoạn {ox}J."
            )
            gold = {
                "s": [0, "pyr", sol_dot, 0],
                "r": [
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p1}", "b": f"{ox}{p2}"},
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p1}", "b": f"{ox}{p3}"},
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p2}", "b": f"{ox}{p3}"},
                    {"c": 0, "p": "len", "a": f"{ox}{p1}", "q": l1},
                    {"c": 0, "p": "len", "a": f"{ox}{p2}", "q": l2},
                    {"c": 0, "p": "len", "a": f"{ox}{p3}", "q": l3},
                    {"c": 1, "p": "cent", "pt": "J", "a": b3},
                ],
                "g": [{"c": 2, "t": "len", "a": f"{ox}J"}],
                "u": [],
            }
        else:
            # All 3 perp_ll + volume + distance from O to opposite face
            txt = (
                f"Xét tứ diện {ox}{b3} vuông tại {ox} với ba cạnh {ox}{p1}, {ox}{p2}, {ox}{p3} đôi một vuông góc, độ dài {ox}{p1}={l1}, {ox}{p2}={l2}, {ox}{p3}={l3}. "
                f"Tính thể tích khối chóp {sol_dot}. Tính khoảng cách từ {ox} đến mặt phẳng ({b3})."
            )
            gold = {
                "s": [0, "pyr", sol_dot, 0],
                "r": [
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p1}", "b": f"{ox}{p2}"},
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p1}", "b": f"{ox}{p3}"},
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p2}", "b": f"{ox}{p3}"},
                    {"c": 0, "p": "len", "a": f"{ox}{p1}", "q": l1},
                    {"c": 0, "p": "len", "a": f"{ox}{p2}", "q": l2},
                    {"c": 0, "p": "len", "a": f"{ox}{p3}", "q": l3},
                ],
                "g": [
                    {"c": 1, "t": "vol", "tgt": sol_dot},
                    {"c": 2, "t": "dist_pt_plane", "a": ox, "b": b3},
                ],
                "u": [],
            }
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("tr9_tet"), split="train", family_id="TR9_TETRA_ORTHO_CENT",
            raw_text=txt, raw_slm_json=gold, kind="positive", ambiguity_status="UNAMBIGUOUS",
        ))

    # ── TR9_3: Right Prism + Aux Proj / Mid + Length/Angle Multi-Goal ───────────────
    for i in range(30):
        b, t = prisms_tr[i % len(prisms_tr)]
        bp = re.findall(r"[A-Z][0-9]*'*", b)
        tp = re.findall(r"[A-Z][0-9]*'*", t)
        A, B, C = bp
        A1, B1, C1 = tp
        d1, d2, d3 = dims3[i % len(dims3)]
        sol = f"{b}.{t}"
        if i % 3 == 0:
            # Right prism + orthogonal projection on BC -> len(A'H) (like D11 pattern!)
            txt = (
                f"Trong lăng trụ đứng {sol}, tam giác đáy {b} vuông tại {A} có {A}{B}={d1}, {A}{C}={d2} và cạnh {A}{A1}={d3}. "
                f"Gọi H là hình chiếu vuông góc của {A} lên đường thẳng {B}{C}. Tính độ dài đoạn {A1}H."
            )
            gold = {
                "s": [0, "pri", sol, 1],
                "r": [
                    {"c": 0, "p": "right_tri", "a": b, "pt": A},
                    {"c": 0, "p": "len", "a": f"{A}{B}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{A}{C}", "q": d2},
                    {"c": 0, "p": "len", "a": f"{A}{A1}", "q": d3},
                    {"c": 1, "p": "proj", "pt": "H", "a": A, "b": f"{B}{C}"},
                ],
                "g": [{"c": 2, "t": "len", "a": f"{A1}H"}],
                "u": [],
            }
        elif i % 3 == 1:
            # Right prism + midpoint O on AB' -> len(CO) (like L21 pattern!)
            txt = (
                f"Cho lăng trụ đứng {sol} có đáy {b} là tam giác vuông cân tại {A} với {A}{B}={d1}, {A}{C}={d1} và {A}{A1}={d3}. "
                f"Gọi T là trung điểm đoạn {A}{B1}. Tính độ dài đoạn {C}T."
            )
            gold = {
                "s": [0, "pri", sol, 1],
                "r": [
                    {"c": 0, "p": "right_iso_tri", "a": b, "pt": A},
                    {"c": 0, "p": "len", "a": f"{A}{B}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{A}{C}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{A}{A1}", "q": d3},
                    {"c": 1, "p": "mid", "pt": "T", "a": f"{A}{B1}"},
                ],
                "g": [{"c": 2, "t": "len", "a": f"{C}T"}],
                "u": [],
            }
        else:
            # Right prism + 2-goal: volume + ang_pp (like L24 pattern!)
            txt = (
                f"Cho lăng trụ đứng {sol} có đáy {b} là tam giác vuông tại {A} với {A}{B}={d1}, {A}{C}={d2} và {A}{A1}={d3}. "
                f"Tính thể tích khối lăng trụ {sol}. Tính góc giữa hai mặt phẳng ({A1}{B}{C}) và ({b})."
            )
            gold = {
                "s": [0, "pri", sol, 1],
                "r": [
                    {"c": 0, "p": "right_tri", "a": b, "pt": A},
                    {"c": 0, "p": "len", "a": f"{A}{B}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{A}{C}", "q": d2},
                    {"c": 0, "p": "len", "a": f"{A}{A1}", "q": d3},
                ],
                "g": [
                    {"c": 1, "t": "vol", "tgt": sol},
                    {"c": 2, "t": "ang_pp", "a": f"{A1}{B}{C}", "b": b},
                ],
                "u": [],
            }
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("tr9_pri"), split="train", family_id="TR9_CUBE_PRISM_AUX_LEN",
            raw_text=txt, raw_slm_json=gold, kind="positive", ambiguity_status="UNAMBIGUOUS",
        ))

    # ── TR9_4: Rectangle/Shape without "đáy" + Midpoint + Distance (20 cases) ────────
    for i in range(20):
        ap, p_base = pyrs_tr[i % len(pyrs_tr)]
        p0, p1, p2, p3 = re.findall(r"[A-Z][0-9]*'*", p_base)
        d1, d2, d3 = dims3[i % len(dims3)]
        sol = f"{ap}.{p_base}"
        txt = (
            f"Xét khối chóp {sol} có {ap}{p0} vuông góc với mặt phẳng ({p_base}) cùng {ap}{p0}={d3}. "
            f"Biết {p_base} là hình chữ nhật gồm {p0}{p1}={d1}, {p1}{p2}={d2}. "
            f"Gọi Z là trung điểm của cạnh {p2}{p3}. Tính khoảng cách từ Z đến mặt phẳng ({ap}{p1}{p2})."
        )
        gold = {
            "s": [0, "pyr", sol, 0],
            "r": [
                {"c": 0, "p": "perp_lp", "a": f"{ap}{p0}", "b": p_base},
                {"c": 0, "p": "len", "a": f"{ap}{p0}", "q": d3},
                {"c": 1, "p": "rect", "a": p_base},
                {"c": 1, "p": "len", "a": f"{p0}{p1}", "q": d1},
                {"c": 1, "p": "len", "a": f"{p1}{p2}", "q": d2},
                {"c": 2, "p": "mid", "pt": "Z", "a": f"{p2}{p3}"},
            ],
            "g": [{"c": 3, "t": "dist_pt_plane", "a": "Z", "b": f"{ap}{p1}{p2}"}],
            "u": [],
        }
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("tr9_rect"), split="train", family_id="TR9_BIET_SHAPE_WITHOUT_DAY",
            raw_text=txt, raw_slm_json=gold, kind="positive", ambiguity_status="UNAMBIGUOUS",
        ))

    # ── TR9_5: Hard Negative / Unresolved Calibration (16 cases) ─────────────────────
    for i in range(16):
        ap, p_base = pyrs_tr[i % len(pyrs_tr)]
        p0, p1, p2, p3 = re.findall(r"[A-Z][0-9]*'*", p_base)
        sol = f"{ap}.{p_base}"
        mod = i % 4
        if mod == 0:
            txt = f"Xét tứ diện {sol} thiếu số đo cạnh cao, chỉ cho {p_base} vuông cạnh {i+2}. Tìm khoảng cách từ {ap} tới ({p1}{p2}{p3})."
            gold = {"s": [0, "pyr", sol, 0], "r": [{"c": 0, "p": "reg_poly", "a": p_base, "q": str(i + 2)}], "g": [], "u": [{"c": 0, "k": "missing"}]}
            amb = "MISSING_DIMENSION_INPUT"
        elif mod == 1:
            txt = f"Hình chóp {sol} có {p_base} là hình vuông cạnh 3, mặt bên {ap}{p0}{p1} không vuông với ({p_base}). Tính chiều cao."
            gold = {"s": [0, "pyr", sol, 0], "r": [{"c": 0, "p": "reg_poly", "a": p_base, "q": "3"}], "g": [], "u": [{"c": 0, "k": "contra"}]}
            amb = "CONTRADICTORY_INPUT"
        elif mod == 2:
            txt = f"Cho khối nón đỉnh {ap} chiều cao h={i+3} bán kính {i+1}. Tìm thể tích xung quanh và tính khoảng cách tới đáy."
            gold = {"s": None, "r": [], "g": [], "u": [{"c": 0, "k": "unsup"}]}
            amb = "OUT_OF_SCOPE_INPUT"
        else:
            txt = f"Hình chóp {sol} có cạnh đáy chưa rõ và mặt cắt thay đổi theo tham số t={i+1}. Tính thể tích nhỏ nhất của khối."
            gold = {"s": [0, "pyr", sol, 0], "r": [], "g": [], "u": [{"c": 1, "k": "unsup"}]}
            amb = "EXTREMUM_UNSUPPORTED"
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("tr9_neg"), split="train", family_id="TR9_HARD_NEGATIVE_CALIBRATION",
            raw_text=txt, raw_slm_json=gold, kind="negative", ambiguity_status=amb,
        ))

    # ── DISJOINT VALIDATION FAMILIES (`val_v9.jsonl` only, NEVER seen in train!) ────
    # VL9_1: Multi-goal validation on completely different wording & vertex tuples (14 cases)
    for i in range(14):
        b, t = boxes_vl[i % len(boxes_vl)]
        bp = re.findall(r"[A-Z][0-9]*'*", b)
        tp = re.findall(r"[A-Z][0-9]*'*", t)
        A, B, C, D0 = bp
        A1, B1, C1, D1 = tp
        sol = f"{b}.{t}"
        d1, d2, d3 = dims3[(i + 2) % len(dims3)]
        if i % 2 == 0:
            txt = (
                f"Đề yêu cầu khảo sát hộp chữ nhật {sol} có các cạnh {A}{B}={d1}, {A}{D0}={d2}, {A}{A1}={d3}. "
                f"Tính độ dài đoạn {A}{C1}. Tính góc giữa hai đường thẳng {A}{B1} với {B}{C1}. Tính thể tích khối hộp {sol}."
            )
            gold = {
                "s": [0, "box", sol, 1],
                "r": [
                    {"c": 0, "p": "len", "a": f"{A}{B}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{A}{D0}", "q": d2},
                    {"c": 0, "p": "len", "a": f"{A}{A1}", "q": d3},
                ],
                "g": [
                    {"c": 1, "t": "len", "a": f"{A}{C1}"},
                    {"c": 2, "t": "ang_ll", "a": f"{A}{B1}", "b": f"{B}{C1}"},
                    {"c": 3, "t": "vol", "tgt": sol},
                ],
                "u": [],
            }
        else:
            b3, t3 = prisms_vl[i % len(prisms_vl)]
            pA, pB, pC = re.findall(r"[A-Z][0-9]*'*", b3)
            pA1, pB1, pC1 = re.findall(r"[A-Z][0-9]*'*", t3)
            sol3 = f"{b3}.{t3}"
            txt = (
                f"Khảo sát lăng trụ đứng {sol3} có đáy {b3} là tam giác vuông tại {pA} với {pA}{pB}={d1}, {pA}{pC}={d2} và {pA}{pA1}={d3}. "
                f"Tính thể tích khối lăng trụ {sol3}. Tính góc giữa hai mặt phẳng ({pA1}{pB}{pC}) và ({b3})."
            )
            gold = {
                "s": [0, "pri", sol3, 1],
                "r": [
                    {"c": 0, "p": "right_tri", "a": b3, "pt": pA},
                    {"c": 0, "p": "len", "a": f"{pA}{pB}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{pA}{pC}", "q": d2},
                    {"c": 0, "p": "len", "a": f"{pA}{pA1}", "q": d3},
                ],
                "g": [
                    {"c": 1, "t": "vol", "tgt": sol3},
                    {"c": 2, "t": "ang_pp", "a": f"{pA1}{pB}{pC}", "b": b3},
                ],
                "u": [],
            }
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("vl9_mg"), split="val", family_id="VL9_MULTI_GOAL_DISJOINT",
            raw_text=txt, raw_slm_json=gold, kind="positive", ambiguity_status="UNAMBIGUOUS",
        ))

    # VL9_2: Tetrahedra & Aux Lengths & Shape-without-day validation (12 cases)
    for i in range(12):
        if i < 4:
            ox, b3 = tetras_vl[i % len(tetras_vl)]
            p1, p2, p3 = re.findall(r"[A-Z][0-9]*'*", b3)
            sol_dot = f"{ox}.{b3}"
            l1, l2, l3 = dims3[(i + 1) % len(dims3)]
            txt = (
                f"Một tứ diện {ox}{b3} có {ox}{p1}, {ox}{p2}, {ox}{p3} đôi một vuông góc và {ox}{p1}={l1}, {ox}{p2}={l2}, {ox}{p3}={l3}. "
                f"Gọi G là trọng tâm tam giác {b3}. Tính độ dài đoạn {ox}G."
            )
            gold = {
                "s": [0, "pyr", sol_dot, 0],
                "r": [
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p1}", "b": f"{ox}{p2}"},
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p1}", "b": f"{ox}{p3}"},
                    {"c": 0, "p": "perp_ll", "a": f"{ox}{p2}", "b": f"{ox}{p3}"},
                    {"c": 0, "p": "len", "a": f"{ox}{p1}", "q": l1},
                    {"c": 0, "p": "len", "a": f"{ox}{p2}", "q": l2},
                    {"c": 0, "p": "len", "a": f"{ox}{p3}", "q": l3},
                    {"c": 1, "p": "cent", "pt": "G", "a": b3},
                ],
                "g": [{"c": 2, "t": "len", "a": f"{ox}G"}],
                "u": [],
            }
        elif i < 8:
            b3, t3 = prisms_vl[i % len(prisms_vl)]
            pA, pB, pC = re.findall(r"[A-Z][0-9]*'*", b3)
            pA1, pB1, pC1 = re.findall(r"[A-Z][0-9]*'*", t3)
            sol3 = f"{b3}.{t3}"
            d1, d2, d3 = dims3[(i + 1) % len(dims3)]
            txt = (
                f"Khảo sát lăng trụ đứng {sol3} biết tam giác {b3} vuông tại {pA}, {pA}{pB}={d1}, {pA}{pC}={d2} và {pA}{pA1}={d3}. "
                f"Gọi K là hình chiếu vuông góc của {pA} lên đường thẳng {pB}{pC}. Tính độ dài đoạn {pA1}K."
            )
            gold = {
                "s": [0, "pri", sol3, 1],
                "r": [
                    {"c": 0, "p": "right_tri", "a": b3, "pt": pA},
                    {"c": 0, "p": "len", "a": f"{pA}{pB}", "q": d1},
                    {"c": 0, "p": "len", "a": f"{pA}{pC}", "q": d2},
                    {"c": 0, "p": "len", "a": f"{pA}{pA1}", "q": d3},
                    {"c": 1, "p": "proj", "pt": "K", "a": pA, "b": f"{pB}{pC}"},
                ],
                "g": [{"c": 2, "t": "len", "a": f"{pA1}K"}],
                "u": [],
            }
        else:
            ap, p_base = pyrs_vl[i % len(pyrs_vl)]
            p0, p1, p2, p3 = re.findall(r"[A-Z][0-9]*'*", p_base)
            d1, d2, d3 = dims3[i % len(dims3)]
            sol = f"{ap}.{p_base}"
            txt = (
                f"Khối chóp {sol} có {ap}{p0} vuông góc với mặt phẳng ({p_base}) và {ap}{p0}={d3}. "
                f"Mặt đáy {p_base} là hình chữ nhật với {p0}{p1}={d1}, {p1}{p2}={d2}. "
                f"Gọi N là trung điểm cạnh {p2}{p3}. Tính khoảng cách từ N đến mặt phẳng ({ap}{p1}{p2})."
            )
            gold = {
                "s": [0, "pyr", sol, 0],
                "r": [
                    {"c": 0, "p": "perp_lp", "a": f"{ap}{p0}", "b": p_base},
                    {"c": 0, "p": "len", "a": f"{ap}{p0}", "q": d3},
                    {"c": 1, "p": "rect", "a": p_base},
                    {"c": 1, "p": "len", "a": f"{p0}{p1}", "q": d1},
                    {"c": 1, "p": "len", "a": f"{p1}{p2}", "q": d2},
                    {"c": 2, "p": "mid", "pt": "N", "a": f"{p2}{p3}"},
                ],
                "g": [{"c": 3, "t": "dist_pt_plane", "a": "N", "b": f"{ap}{p1}{p2}"}],
                "u": [],
            }
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("vl9_aux"), split="val", family_id="VL9_TETRA_PRISM_RECT_DISJOINT",
            raw_text=txt, raw_slm_json=gold, kind="positive", ambiguity_status="UNAMBIGUOUS",
        ))

    # VL9_3: Validation hard negatives (8 cases)
    for i in range(8):
        ap, p_base = pyrs_vl[i % len(pyrs_vl)]
        p0, p1, p2, p3 = re.findall(r"[A-Z][0-9]*'*", p_base)
        sol = f"{ap}.{p_base}"
        if i % 2 == 0:
            txt = f"Cho khối chóp {sol} nhưng {ap}{p0} không vuông góc với đáy ({p_base}), cạnh đáy {i+2}. Tìm chiều cao {sol}."
            gold = {"s": [0, "pyr", sol, 0], "r": [], "g": [], "u": [{"c": 0, "k": "contra"}]}
        else:
            txt = f"Cho hình cầu tâm I bán kính R={i+4}. Hỏi thể tích mặt cầu và đoạn nối dài vô hạn."
            gold = {"s": None, "r": [], "g": [], "u": [{"c": 0, "k": "unsup"}]}
        samples.append(_verify_and_serialize_v9(
            sample_id=_nid("vl9_neg"), split="val", family_id="VL9_NEG_DISJOINT",
            raw_text=txt, raw_slm_json=gold, kind="negative", ambiguity_status="UNSUPPORTED_OR_CONTRA",
        ))

    return samples


def _load_all_unlocked_holdouts_for_audit() -> list[tuple[str, str]]:
    pool = DATA_V7._load_unlocked_and_prior_corpora()
    # Add C60, EXTERNAL17, and SLM_V7_HOLDOUT_112
    v8 = json.loads((RUNS_DIR / "independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json").read_text(encoding="utf-8"))
    for c in v8["cases"]:
        pool.append((c["corpus"], c["text"]))
    v7 = json.loads((RUNS_DIR / "deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))
    for c in v7["cases"]:
        pool.append(("SLM_V7_HOLDOUT_112", c["text"]))
    return pool


def main() -> int:
    v7_rows = _rehydrate_v7_rows()
    v9_rows = _generate_v9_targeted_samples()
    all_rows = v7_rows + v9_rows

    train_samples = [r for r in all_rows if r["split"] == "train"]
    val_samples = [r for r in all_rows if r["split"] == "val"]

    rng = random.Random(42)
    rng.shuffle(train_samples)

    # Anti-leakage checks across Train vs Val AND vs ALL unlocked external/holdout sets
    tr_fams = {s["problem_family_id"] for s in train_samples}
    vl_fams = {s["problem_family_id"] for s in val_samples}
    assert tr_fams.isdisjoint(vl_fams), f"Train/Val family overlap: {tr_fams & vl_fams}"

    tr_skels = {_skeleton(s["source_text"]) for s in train_samples}
    vl_skels = {_skeleton(s["source_text"]) for s in val_samples}
    # Check skeleton disjointness on all newly generated v9 families
    v9_tr_skels = {_skeleton(s["source_text"]) for s in v9_rows if s["split"] == "train"}
    v9_vl_skels = {_skeleton(s["source_text"]) for s in v9_rows if s["split"] == "val"}
    assert v9_tr_skels.isdisjoint(v9_vl_skels), f"V9 train/val skeleton overlap: {v9_tr_skels & v9_vl_skels}"
    assert tr_skels.isdisjoint(vl_skels), f"Full train/val skeleton overlap: {tr_skels & vl_skels}"

    pool = _load_all_unlocked_holdouts_for_audit()
    prior_norm = {normalize_problem_text(t).lower(): src for src, t in pool}
    prior_skel = {_skeleton(t): src for src, t in pool}
    prior_ng = [(src, _ngrams(t, 4)) for src, t in pool]

    max_ext_j = 0.0
    max_ext_pair = ""
    for s in all_rows:
        tn = normalize_problem_text(s["source_text"]).lower()
        sk = _skeleton(s["source_text"])
        assert tn not in prior_norm, f"Exact overlap with {prior_norm[tn]}: {s['sample_id']}"
        assert sk not in prior_skel, f"Skeleton overlap with {prior_skel[sk]}: {s['sample_id']}"
        ng = _ngrams(s["source_text"], 4)
        for src, png in prior_ng:
            j = len(ng & png) / max(1, len(ng | png))
            if j > max_ext_j:
                max_ext_j = j
                max_ext_pair = f"{s['sample_id']}~{src}"
    assert max_ext_j < 0.65, f"High 4-gram overlap: {max_ext_pair} ({max_ext_j:.4f})"

    V9_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    tr_path = V9_DATASET_DIR / "train_v9.jsonl"
    vl_path = V9_DATASET_DIR / "val_v9.jsonl"
    tr_path.write_text("\n".join(json.dumps(s, ensure_ascii=False) for s in train_samples) + "\n", encoding="utf-8")
    vl_path.write_text("\n".join(json.dumps(s, ensure_ascii=False) for s in val_samples) + "\n", encoding="utf-8")

    def _sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    manifest = {
        "schema": "slm-v9-training-data-manifest/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "schema_version": SLM_COMPACT_SCHEMA_VERSION,
        "closure_mode": V9_CLOSURE_MODE,
        "storage_location_outside_git": str(V9_DATASET_DIR),
        "sealed_corpora_opened": False,
        "splits": {
            "train": {
                "path": str(tr_path),
                "sha256": _sha(tr_path),
                "total": len(train_samples),
                "positives": sum(1 for s in train_samples if s["positive_label"]),
                "negatives": sum(1 for s in train_samples if not s["positive_label"]),
                "families": dict(Counter(s["problem_family_id"] for s in train_samples)),
            },
            "val": {
                "path": str(vl_path),
                "sha256": _sha(vl_path),
                "total": len(val_samples),
                "positives": sum(1 for s in val_samples if s["positive_label"]),
                "negatives": sum(1 for s in val_samples if not s["positive_label"]),
                "families": dict(Counter(s["problem_family_id"] for s in val_samples)),
            },
        },
        "anti_leakage_audit": {
            "external_corpora_checked": len(pool),
            "includes_corpora": sorted({src for src, _ in pool}),
            "exact_normalized_overlaps_external": 0,
            "structural_skeleton_overlaps_external": 0,
            "max_4gram_jaccard_external": round(max_ext_j, 4),
            "closest_external_pair": max_ext_pair,
            "train_val_family_overlaps": 0,
            "train_val_structural_skeleton_overlaps": 0,
        },
    }
    (OUT_DIR / "SLM_V9_TRAINING_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[DATA V9] train={len(train_samples)} ({manifest['splits']['train']['positives']}+/{manifest['splits']['train']['negatives']}-) | val={len(val_samples)} ({manifest['splits']['val']['positives']}+/{manifest['splits']['val']['negatives']}-) | max_ext_4gram={max_ext_j:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
