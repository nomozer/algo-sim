"""BH2A-01..18 as a KNOWN REGRESSION (run `source-gate-hardening`, P4-D) — 0 model calls, refuses to overwrite.

Texts: `texts.json`, transcribed verbatim from the owner-supplied `original_holdout_report.md`; sha256(text)[:16] equals the
`orig_text_hash` of Gemini's `reconciliation_receipt.json` for all 18 (checked by `check-texts`).
Typed facts: RECONSTRUCTED here from each case's "Facts & Goals (TypedFact)" section of that report — Gemini's own
payload script was not supplied, so they are NOT claimed byte-identical to Gemini's runs (`exec_payload_hash`); the
`wave2a` arm re-runs them on the code Gemini measured (224328a2) to reconcile statuses/codes with Gemini's results.
Expected values: the report's oracle (Gemini's), copied unchanged into ORACLE below; never edited to pass.

    python bh2a_regression.py check-texts
    python bh2a_regression.py arm --name <wave2a|baseline-main|hardened> --code-root <checkout> --out <dir>
    python bh2a_regression.py compare --out <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEXTS = json.loads((HERE / "texts.json").read_text(encoding="utf-8"))["texts"]
TEXT_HASH = dict(zip([f"BH2A-{i:02d}" for i in range(1, 19)], (
    "44dcbf2259b75810 c589c99a877a3978 f9684f47ef81428b 677f75633460659d 203fd3331dfff2a3 a8d31d97cab26b76 "
    "a12db0a4c3a851d2 fa58a532f7b5fae3 7223393ea8c5c7a1 1ea9b7584da63b79 0464680f45c3a8f1 7394463a57f5df27 "
    "ddeda9a881cdfee5 26a17513181110a5 f44c6990ae13c12f d791750754ecf5d7 b6f2cad6b3dfa36c f2550f26d771e5ec").split()))
#: The report's oracle answers (Gemini), unchanged. Sentinel BH2A-13 expects a²√3 once divide_segment + plane ⊥ line exist.
ORACLE = {"BH2A-01": {"q1": "a√6"}, "BH2A-02": {"q1": "a√17"}, "BH2A-03": {"q1": "a√10"}, "BH2A-04": {"q1": "3a²√13/2"},
          "BH2A-05": {"q1": "cos²=4/45"}, "BH2A-06": {"q1": "cos²=49/850"}, "BH2A-07": {"q1": "cos²=2/3"},
          "BH2A-08": {"q1": "cos²=3/4"}, "BH2A-09": {"q1": "cos²=8/11"}, "BH2A-10": {"q1": "a", "q2": "cos²=0"},
          "BH2A-11": {"q1": "a", "q2": "cos²=0"}, "BH2A-12": {"q1": "cos²=25/136", "q2": "a²√3009/4"},
          "BH2A-13": {"q1": "a²√3"}}
KIND = {**{f"BH2A-{i:02d}": "positive" for i in range(1, 13)}, "BH2A-13": "sentinel",
        **{f"BH2A-{i:02d}": "negative" for i in range(14, 19)}}
#: Gemini's results on Wave 2A (bh2a_eval_results.json, locked_results) — for reconciliation only.
GEMINI_WAVE2A = {"BH2A-01": "SOURCE_OBJECT_MISMATCH", "BH2A-02": "UNGROUNDED_VALUE", "BH2A-03": "SOURCE_OBJECT_MISMATCH",
                 "BH2A-04": "AMBIGUOUS_VALUE_QUOTE", "BH2A-05": None, "BH2A-06": "UNGROUNDED_VALUE", "BH2A-07": None,
                 "BH2A-08": "AMBIGUOUS_VALUE_QUOTE", "BH2A-09": None, "BH2A-10": "NOT_ASKED_IN_SOURCE",
                 "BH2A-11": "NOT_ASKED_IN_SOURCE", "BH2A-12": "SOURCE_OBJECT_MISMATCH", "BH2A-13": "PLANE_NOT_UNIQUE",
                 "BH2A-14": "FACT_INCOMPLETE", "BH2A-15": "SOURCE_OBJECT_MISMATCH", "BH2A-16": "NON_HOMOGENEOUS_LENGTHS",
                 "BH2A-17": "SOURCE_OBJECT_MISMATCH", "BH2A-18": "UNDERDETERMINED_POINT"}


def _s(cid: str, i: int) -> str:
    """Sentence i of the case text (split at '. ' — no decimal points in these texts)."""
    parts = TEXTS[cid].split(". ")
    return parts[i] + ("." if not parts[i].endswith(".") else "")


def f(fid, kind, quote, role="premise", **kw):
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote] if isinstance(quote, str) else quote, **kw}


def q(fid, quote, **kw):
    return f(fid, "question", quote, role="question", **kw)


def L(fid, quote, seg, v):
    return f(fid, "length", quote, points=list(seg) if isinstance(seg, (list, tuple)) else _lab(seg), measure="segment", value=v)


def _lab(s):
    import re
    return re.findall(r"[A-Z]'?", s)


def facts(cid: str) -> list[dict]:
    """RECONSTRUCTED TypedFact payload of each case from the report's 'Facts & Goals' (premise quotes = their sentence)."""
    s0, s1 = _s(cid, 0), _s(cid, 1)
    s2 = _s(cid, 2) if len(TEXTS[cid].split(". ")) > 2 else None
    sabc = [f("f1", "solid", s0, solid="S.ABC", solid_type="pyramid")]
    perp_abc = f("f5", "perpendicular", s0, points_a=["S", "A"], points_b=list("ABC"))
    if cid == "BH2A-01":
        return [f("f1", "solid", s0, solid="ABC.A'B'C'", solid_type="prism", right=True),
                f("f2", "right_angle", s0, at="A", points=["B", "C"]), L("f3", s0, "AB", "3a"), L("f4", s0, "AC", "3a"),
                L("f5", s0, "AA'", "2a"),
                q("q1", s1, quantity="length", point_kind="centroid", points=list("ABC"), points_b=["A'"])]
    if cid == "BH2A-02":
        return [f("f1", "solid", s0, solid="S.ABCD", solid_type="pyramid"),
                f("f2", "polygon_shape", s0, points=list("ABCD"), shape="rectangle"), L("f3", s0, "AB", "3a"),
                L("f4", s0, "BC", "6a"), f("f5", "perpendicular", s0, points_a=["S", "A"], points_b=list("ABCD")),
                L("f6", s0, "SA", "3a"),
                q("q1", s1, quantity="distance", point_kind="centroid", points=list("SCD"), points_b=["A", "B"])]
    if cid == "BH2A-03":   # the report's producer names the base by three labels ["A","B","C"] (the text says (ABCD))
        return [f("f1", "solid", s0, solid="S.ABCD", solid_type="pyramid"),
                f("f2", "polygon_shape", s0, points=list("ABCD"), shape="square", value="3a"),
                f("f3", "perpendicular", s0, points_a=["S", "A"], points_b=list("ABCD")), L("f4", s0, "SA", "3a"),
                f("f_gt", "intersection_line", s1, points_a=list("SCD"), points_b=list("ABC")),
                q("q1", s1, quantity="distance", point_kind="centroid", points=list("SAB"), line_ref="f_gt")]
    if cid == "BH2A-04":
        return [f("f1", "solid", s0, solid="S.ABCDEF", solid_type="pyramid", regular=True),
                f("f2", "length", s0, measure="base_edge", solid="S.ABCDEF", value="3a"),
                f("f3", "length", s0, measure="height", solid="S.ABCDEF", value="3a"),
                q("q1", s1, quantity="area", point_kind="centroid", points=list("SAB"), points_b=["C", "D"])]
    if cid == "BH2A-05":
        return [f("f1", "solid", s0, solid="ABCD.A'B'C'D'", solid_type="cuboid"), L("f2", s0, "AB", "a"),
                L("f3", s0, "AD", "2a"), L("f4", s0, "AA'", "2a"),
                f("f5", "point_def", s1, point="M", point_kind="midpoint", points=["A", "D"]),
                q("q1", s2, quantity="angle", points_a=["A'", "M"], points_b=["B", "D'"])]
    if cid == "BH2A-06":
        return [f("f1", "solid", s0, solid="S.ABCD", solid_type="pyramid"),
                f("f2", "polygon_shape", s0, points=list("ABCD"), shape="rectangle"), L("f3", s0, "AB", "5a"),
                L("f4", s0, "BC", "3a"), f("f5", "right_angle", s1, at="S", points=["A", "B"]), L("f6", s1, "SA", "3a"),
                L("f7", s1, "SB", "4a"), f("f8", "perpendicular", s1, points_a=list("SAB"), points_b=list("ABCD")),
                q("q1", s2, quantity="angle", points_a=["S", "C"], points_b=["B", "D"])]
    right_abc = [*sabc, f("f2", "right_angle", s0, at="A", points=["B", "C"]), L("f3", s0, "AB", "3a"),
                 L("f4", s0, "AC", "3a"), perp_abc, L("f6", s0, "SA", "3a")]
    if cid == "BH2A-07":
        return right_abc + [q("q1", s1, quantity="angle", point_kind="centroid", points=list("SBC"), points_a=["A"],
                              points_b=list("SAC"))]
    if cid == "BH2A-09":
        return right_abc + [q("q1", s1, quantity="angle", point_kind="centroid", points=list("ABC"), points_a=["S"],
                              points_b=["S", "B"])]
    if cid == "BH2A-08":
        return [f("f1", "solid", s0, solid="ABC.A'B'C'", solid_type="prism", regular=True),
                f("f2", "length", s0, measure="base_edge", solid="ABC.A'B'C'", value="2a"), L("f3", s0, "AA'", "a"),
                q("q1", s1, quantity="angle", point_kind="midpoint", points=["B", "C"], points_a=["A'"], points_b=list("ABC"))]
    eq_abc = [*sabc, f("f2", "polygon_shape", s0, points=list("ABC"), shape="equilateral_triangle", value="3a"),
              f("f3", "perpendicular", s0, points_a=["S", "A"], points_b=list("ABC")), L("f4", s0, "SA", "3a")]
    if cid == "BH2A-10":
        return eq_abc + [f("f5", "point_def", s1, point="G", point_kind="centroid", points=list("SBC")),
                         q("q1", s2, quantity="distance", point_kind="centroid", points=list("SBC"), points_b=list("ABC")),
                         q("q2", s2, quantity="angle", points_a=["A", "G"], points_b=["B", "C"])]
    if cid == "BH2A-11":   # questions first, premises after (the report's deliberate fact order)
        return [q("q1", s2, quantity="distance", point_kind="centroid", points=list("SAB"), points_b=list("ABC")),
                q("q2", s2, quantity="angle", points_a=["S", "H"], points_b=["B", "C"]),
                f("f5", "perpendicular", s1, points_a=["S", "H"], points_b=["A", "B"]),
                f("f6", "perpendicular", s1, points_a=["S", "H"], points_b=["A", "C"]), L("f7", s1, "SH", "3a"),
                f("f4", "point_def", s1, point="H", point_kind="midpoint", points=["B", "C"]),
                L("f2", s0, "AB", "6a"), L("f3", s0, "AC", "6a"), f("f1", "right_angle", s0, at="A", points=["B", "C"]),
                f("f0", "solid", s0, solid="S.ABC", solid_type="pyramid")]
    if cid == "BH2A-12":
        return [*sabc, L("f2", s0, "AB", "5a"), L("f3", s0, "AC", "8a"), L("f4", s0, "BC", "7a"), perp_abc,
                L("f6", s0, "SA", "3a"), q("q1", s1, quantity="angle", points_a=["S", "B"], points_b=["A", "C"]),
                q("q2", s1, quantity="area", point_kind="midpoint", points=["A", "B"], points_b=["S", "C"])]
    if cid == "BH2A-13":   # Wave 2B fact forms: divide_segment (t = SM/SA = 2/3), plane through M ⊥ the line SA
        s3 = _s(cid, 3)
        return eq_abc + [f("m", "point_def", s1, point="M", point_kind="divide_segment", points=["S", "A"], value="2/3"),
                         q("q1", [s2, s3], quantity="area", solid="S.ABC", point="M", points_b=["S", "A"],
                           plane_relation="perpendicular")]
    if cid == "BH2A-14":
        return [f("f1", "solid", s0, solid="S.ABCD", solid_type="pyramid"),
                f("f2", "polygon_shape", s0, points=list("ABCD"), shape="square", value="2a"),
                f("f3", "perpendicular", s0, points_a=["S", "A"], points_b=list("ABCD")), L("f4", s0, "SA", "2a"),
                q("q1", s1, quantity="distance", point_kind="centroid", points=list("ABCD"), points_b=list("SBC"))]
    if cid == "BH2A-15":
        return eq_abc + [f("f5", "point_def", s1, point="M", point_kind="midpoint", points=["B", "C"]),
                         q("q1", s2, quantity="area", point_kind="centroid", points=list("SBC"), points_b=["S", "M"])]
    if cid == "BH2A-16":
        return [*sabc, f("f2", "right_angle", s0, at="A", points=["B", "C"]), L("f3", s0, "AB", "2a"),
                L("f4", s0, "AC", "3"), perp_abc, L("f6", s0, "SA", "2a"),
                q("q1", s1, quantity="angle", points_a=["S", "B"], points_b=["A", "C"])]
    if cid == "BH2A-17":   # spoofed producer: the question names "điểm M", the fact describes a centroid
        return eq_abc + [f("f5", "point_def", s1, point="M", point_kind="midpoint", points=["B", "C"]),
                         q("q1", s2, quantity="distance", point_kind="centroid", points=list("SBC"), points_b=list("SAB"))]
    if cid == "BH2A-18":
        return [*sabc, f("f2", "polygon_shape", s0, points=list("ABC"), shape="equilateral_triangle", value="3a"),
                f("f3", "perpendicular", s0, points_a=["S", "A"], points_b=["B", "C"]), L("f4", s0, "SA", "3a"),
                q("q1", s1, quantity="angle", points_a=["S", "B"], points_b=["A", "C"])]
    raise KeyError(cid)


#: Diagnostic variant (not counted): BH2A-03 with the producer's base plane written as the text writes it, (ABCD).
def facts_variant_03() -> list[dict]:
    fs = facts("BH2A-03")
    next(x for x in fs if x["id"] == "f_gt")["points_b"] = list("ABCD")
    return fs


def arm(name: str, code_root: Path, out: Path) -> None:
    sys.path.insert(0, str(code_root / "backend"))
    os.chdir(code_root / "backend")
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions.registry import REGISTRY_VERSION

    rows = []
    cases = [(cid, facts(cid)) for cid in TEXTS] + [("BH2A-03-variant-ABCD", facts_variant_03())]
    for cid, payload in cases:
        base = cid[:7]
        try:
            r = run_fact_route(TEXTS[base], {"facts": deepcopy(payload)})
            status, code, answers = r.status, r.code, dict(r.answers)
            reason = r.reason
        except Exception as e:                                # noqa: BLE001  (a crash is recorded, never hidden)
            status, code, answers, reason = "EXCEPTION", type(e).__name__, {}, str(e)[:200]
        kind = "diagnostic" if cid != base else KIND[cid]
        want = ORACLE.get(base, {})
        if kind in ("positive", "sentinel", "diagnostic") and want:
            verdict = ("EXACT" if status == "SERVED" and answers == want else
                       "WRONG_SERVE" if status == "SERVED" else "REFUSED")
        else:
            verdict = "FALSE_SERVE" if status == "SERVED" else "REFUSED"
        rows.append({"id": cid, "kind": kind, "status": status, "code": code, "reason": reason, "answers": answers,
                     "oracle": want, "verdict": verdict,
                     "payload_sha256_16": hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True)
                                                         .encode()).hexdigest()[:16]})
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=code_root, capture_output=True, text=True).stdout.strip()
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"arm-{name}.json"
    if target.exists():
        raise SystemExit(f"refusing to overwrite {target}")
    target.write_text(json.dumps({"schema": "bh2a-regression-arm/1", "arm": name, "code_root_head": head,
                                  "registry_version": REGISTRY_VERSION, "model_calls": 0,
                                  "facts": "RECONSTRUCTED_FROM_REPORT", "rows": rows},
                                 ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def compare(out: Path) -> None:
    arms = {p.stem[4:]: {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))["rows"]}
            for p in sorted(out.glob("arm-*.json"))}
    summary = {}
    for a, rows in arms.items():
        pos = [r for r in rows.values() if r["kind"] == "positive"]
        neg = [r for r in rows.values() if r["kind"] == "negative"]
        summary[a] = {"positive_exact": f"{sum(r['verdict'] == 'EXACT' for r in pos)}/{len(pos)}",
                      "positive_goals_exact": f"{sum(r['answers'].get(g) == v for r in pos for g, v in r['oracle'].items())}/"
                                              f"{sum(len(r['oracle']) for r in pos)}",
                      "negative_refused": f"{sum(r['status'] == 'REFUSED' for r in neg)}/{len(neg)}",
                      "wrong_or_false_serves": sum(r["verdict"] in ("WRONG_SERVE", "FALSE_SERVE") for r in rows.values()),
                      "exceptions": sum(r["status"] == "EXCEPTION" for r in rows.values()),
                      "sentinel_BH2A-13": [rows["BH2A-13"]["status"], rows["BH2A-13"]["code"], rows["BH2A-13"]["answers"]],
                      "still_refused_positive": {r["id"]: r["code"] for r in pos if r["status"] != "SERVED"}}
    recon = None
    if "wave2a" in arms:
        recon = {cid: {"gemini": GEMINI_WAVE2A[cid], "reconstructed": arms["wave2a"][cid]["code"],
                       "same": GEMINI_WAVE2A[cid] == arms["wave2a"][cid]["code"]} for cid in GEMINI_WAVE2A}
    (out / "metrics.json").write_text(json.dumps({
        "schema": "bh2a-regression-metrics/1", "status": "KNOWN_REGRESSION_NOT_BLIND", "facts": "RECONSTRUCTED_FROM_REPORT",
        "model_calls": 0, "arms": summary, "reconciliation_vs_gemini_wave2a": recon,
        "reconciled": None if recon is None else f"{sum(v['same'] for v in recon.values())}/{len(recon)}"},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("check-texts", "arm", "compare"))
    ap.add_argument("--name")
    ap.add_argument("--code-root", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.cmd == "check-texts":
        bad = [k for k, h in TEXT_HASH.items() if hashlib.sha256(TEXTS[k].encode("utf-8")).hexdigest()[:16] != h]
        print("texts identical to Gemini's executed texts:", 18 - len(bad), "/ 18", bad)
        return 1 if bad else 0
    if a.cmd == "arm":
        arm(a.name, a.code_root.resolve(), a.out.resolve())
        return 0
    compare(a.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
