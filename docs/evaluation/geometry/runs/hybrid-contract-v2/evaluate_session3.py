# -*- coding: utf-8 -*-
"""P7 Comprehensive Offline Evaluation (`DEVELOPMENT_EVALUATION_NOT_BLIND`) for Backend Hybrid Session 3 (`hybrid-contract-v2`).

Evaluates Families A–H, dual-run `/1` vs `/2` (`convert_v1_to_v2`), independent exact oracle comparisons,
Source Gate authority coverage, planner composition/reuse metrics, and IR memory budget audit (`D4 KEEP 32`).
0 live provider calls (`ALLOW_LIVE_AI = 0`).

Run from `backend/`:
    python ../docs/evaluation/geometry/runs/hybrid-contract-v2/evaluate_session3.py ../docs/evaluation/geometry/runs/hybrid-contract-v2/verification/evaluation
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
from itertools import permutations
from pathlib import Path

import importlib.util

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(HERE))

def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

S1 = _load_mod("evaluate", HERE.parent / "typedfactnext-planner-bridge" / "evaluate.py")
S2 = _load_mod("evaluate_s2", HERE.parent / "backend-hybrid-contract-unification" / "evaluate.py")
import evaluate_grammar_set as GS  # noqa: E402
from app.ai.adapter3_simulation import run_typed_fact_next_route as A3  # noqa: E402
from app.ai.adapter4_route import run_typed_fact_next_v2_route as A4  # noqa: E402
from app.ai.function_route import run_typed_fact_next_planner_route as BR1  # noqa: E402
from app.simulation.geometry_functions import TuChoi  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError, convert_v1_to_v2  # noqa: E402

CLASSIFICATION = "DEVELOPMENT_EVALUATION_NOT_BLIND"


def run_v2(payload_v2: dict, want: dict | None = None) -> dict:
    t0 = time.perf_counter()
    r = A4(deepcopy(payload_v2))
    row = {
        "status": r.status,
        "code": r.code,
        "seconds": round(time.perf_counter() - t0, 4),
    }
    if r.status == "SERVED":
        got = S2.exact(r)
        row["answers"] = {k: str(v) for k, v in got.items()}
        row["scene_valid"] = S1.scene_ok(r.scene3d)[0]
        row["label_leaks"] = len(S1.leaks(r.scene3d, ["I", "I1", "I2", "I3"]))
        row["source_authority"] = (r.route_d or {}).get("source_verification", {}).get("authority")
        row["wrong_served"] = want is None or (bool(want) and {k: got.get(k) for k in want} != want)
    else:
        row["wrong_served"] = False
    return row


def run_converted(payload_v1: dict, route_label: str, want: dict | None = None) -> dict:
    t0 = time.perf_counter()
    try:
        v2 = convert_v1_to_v2(deepcopy(payload_v1), route=route_label)
    except (TuChoi, TypedFactNextValidationError) as e:
        return {
            "status": "REFUSED",
            "code": e.code,
            "seconds": round(time.perf_counter() - t0, 4),
            "wrong_served": False,
            "converted": False,
        }
    row = run_v2(v2, want)
    row["converted"] = True
    return row


def _build_s1_60() -> list[tuple[str, dict, dict | None, str]]:
    """Reconstruct the exact 60-case Session 1 suite `(cid, payload, meta, expect)`."""
    out: list[tuple[str, dict, dict | None, str]] = []

    def go(cid, pv, expect="SERVED"):
        payload, meta = pv
        out.append((cid, payload, meta, expect))

    shapes = [("equilateral", (F(1),)), ("equilateral", (F(2),)), ("square", (F(1),)), ("square", (F(2),)),
              ("rectangle", (F(3), F(4))), ("right", (F(3), F(4)))]
    for si, (shape, dims) in enumerate(shapes):
        for t in (F(1, 2), F(1, 3), F(2, 3)):
            for plane in ("parallel", "perpendicular"):
                sym = shape in ("equilateral", "square")
                go(f"B-{shape}{si}-t{t.numerator}{t.denominator}-{plane}",
                   S1.variant(shape, dims, h=F(2) if not sym else F(1), sym=sym, t=t, plane=plane, residual=True))
    rep = dict(shape="equilateral", dims=(F(2),), h=F(3), sym=False, t=F(1, 3), residual=True)
    go("MR-ref", S1.variant(**rep))
    go("MR-relabel", S1.variant(**rep, labels={"S": "T", "A": "E", "B": "F", "C": "G", "M": "U", "N": "V", "P": "X"}))
    go("MR-premise-order", S1.variant(**rep, premise_order=[2, 1, 0]))
    go("MR-goal-order", S1.variant(**rep, goal_order="residual_first"))
    go("MR-inverted", S1.variant(**{**rep, "residual": False}, inverted=True))
    go("MR-scaled", S1.variant(**{**rep, "dims": (F(6),), "h": F(9)}))
    go("MR-plane-equivalence", S1.variant(**rep, plane="perpendicular"))
    for shape, dims in (("equilateral", (F(1),)), ("square", (F(1),)), ("right", (F(3), F(4)))):
        for plane in ("parallel", "perpendicular"):
            go(f"C-{shape}-{plane}", S1.variant(shape, dims, h=F(2), sym=shape != "right", t=F(1, 3), plane=plane, names=False))
    p, m = S1.variant()
    q = deepcopy(p); q["problem_text"] += " Biết SA = 2a."; q["premises"].append(
        {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}, "quote": "Biết SA = 2a."})
    go("N-contradictory-length", (q, m), "REFUSED")
    q = deepcopy(p); q["problem_text"] = q["problem_text"].replace(" SA = a.", ""); q["premises"] = [
        x for x in q["premises"] if x["quote"] != "SA = a."]
    go("N-missing-height", (q, m), "REFUSED")
    q = deepcopy(p); q["problem_text"] = q["problem_text"].replace("song song với (ABC)", "song song với (SBC)")
    q["derived_sections"][0].update(parallel_plane=["S", "B", "C"],
                                    quote=q["derived_sections"][0]["quote"].replace("(ABC)", "(SBC)"))
    go("N-degenerate-parallel-edge", (q, m), "REFUSED")
    q = deepcopy(p); q["derived_sections"][0].update(cut_edges=[], named_intersections={})
    go("S-cut-edges-not-in-payload", (q, m), "REFUSED_BRIDGE_SCOPE")
    q = deepcopy(p); q["derived_sections"][0]["named_intersections"] = {"S-B": "P", "S-C": "N"}
    go("N-swapped-names", (q, m), "REFUSED")
    q = deepcopy(p); q["solids"][0]["vertex_bindings"] = {"S": "S1"}
    go("S-shared-label-identity", (q, m), "REFUSED_BRIDGE_SCOPE")
    q = deepcopy(p); q["derived_sections"][0].update(plane_kind="plane_equation", equation_coeffs=("0", "0", "1", "-1"))
    go("S-plane-equation", (q, m), "REFUSED_BRIDGE_SCOPE")
    q = deepcopy(p); q["solids"].append({"solid_id": "cone", "solid_type": "cone", "notation": "S.O", "center": "O",
                                         "quote": "Cho hình chóp S.ABC."})
    go("S-curved-solid", (q, m), "REFUSED_BRIDGE_SCOPE")
    pa, ma = S1.variant(names=False)
    q = deepcopy(pa); q["problem_text"] += " Tính tỉ số thể tích."
    q["math_goals"] = [{"goal_id": "g_ratio", "kind": "volume_ratio", "numerator_solid_id": "sub",
                        "denominator_solid_id": "pyr", "quote": "Tính tỉ số thể tích."}]
    go("N-anonymous-ratio-operand", (q, ma), "REFUSED")
    q = deepcopy(pa); q["problem_text"] = q["problem_text"].replace("cắt SB, SC.", "cắt SB.")
    q["derived_sections"][0].update(cut_edges=[["S", "B"]], quote=q["derived_sections"][0]["quote"].replace("SB, SC", "SB"))
    go("S-open-cycle", (q, ma), "REFUSED_BRIDGE_SCOPE")
    q = deepcopy(p); q["problem_text"] = q["problem_text"].replace("lần lượt tại N, P.", "lần lượt tại N, P sao cho NP = BC.")
    q["derived_sections"][0]["quote"] = q["derived_sections"][0]["quote"].replace("N, P.", "N, P sao cho NP = BC.")
    go("N-unread-condition", (q, m), "REFUSED")
    return out


def family_b_session1_dual_run(s1_out: Path) -> dict:
    """Replay the 60 Session 1 cases across `/1` Bridge, `/1` Adapter /3, and `/2` Adapter /4 (via `convert_v1_to_v2`)."""
    S1.main(s1_out)
    s1_agg = json.loads(s1_out.read_text(encoding="utf-8"))["aggregate"]
    rows = []
    for cid, p, meta, expect in _build_s1_60():
        # On `/2`, `S-open-cycle` ("cắt SB." + "Dựng khối chóp đỉnh S cắt bởi (α).") is a valid D6 partial-cut case!
        want = S1.oracle(meta) if (meta and (expect == "SERVED" or cid == "S-open-cycle")) else None
        _, r_br1 = S2.run(BR1, p)
        r_a4 = run_converted(p, "bridge", want)
        rows.append({
            "id": cid,
            "expect_v1": expect,
            "v1_bridge": r_br1,
            "v2_adapter4": r_a4,
            "v1_v2_agree_on_v1_served": (
                r_br1["status"] == r_a4["status"] and r_br1.get("answers") == r_a4.get("answers")
            ) if expect == "SERVED" else None,
        })
    exp_served = [r for r in rows if r["expect_v1"] == "SERVED"]
    exp_invalid = [r for r in rows if r["expect_v1"] == "REFUSED"]
    return {
        "cases": len(rows),
        "v1_session1_aggregate": {
            "goal_coverage": s1_agg["goal_coverage"],
            "exact_correct_of_served_with_answers": s1_agg["exact_correct_of_served_with_answers"],
            "wrong_served": s1_agg["wrong_served"],
            "refusal_correct": s1_agg["refusal_correct"],
            "scene_valid": s1_agg["scene_valid"],
            "label_leaks": s1_agg["label_leaks"],
        },
        "v2_adapter4_on_49_v1_served": f"{sum(r['v2_adapter4']['status'] == 'SERVED' for r in exp_served)}/{len(exp_served)}",
        "v1_v2_answer_agreement_on_49_served": f"{sum(bool(r['v1_v2_agree_on_v1_served']) for r in exp_served)}/{len(exp_served)}",
        "v2_adapter4_d6_newly_served_open_cycle": [
            r["id"] for r in rows if r["expect_v1"] == "REFUSED_BRIDGE_SCOPE" and r["v2_adapter4"]["status"] == "SERVED"
        ],
        "v2_adapter4_invalid_refused": f"{sum(r['v2_adapter4']['status'] == 'REFUSED' for r in exp_invalid)}/{len(exp_invalid)}",
        "v2_adapter4_wrong_served": sum(r["v2_adapter4"]["wrong_served"] for r in rows),
        "v2_adapter4_scene_valid": f"{sum(bool(r['v2_adapter4'].get('scene_valid')) for r in rows if r['v2_adapter4']['status'] == 'SERVED')}/{sum(r['v2_adapter4']['status'] == 'SERVED' for r in rows)}",
        "v2_adapter4_label_leaks": sum(r["v2_adapter4"].get("label_leaks", 0) for r in rows if r["v2_adapter4"]["status"] == "SERVED"),
        "v2_adapter4_gate_authority_100pct": all(
            r["v2_adapter4"].get("source_authority") == "registry.kiem_nguon"
            for r in rows if r["v2_adapter4"]["status"] == "SERVED"
        ),
        "rows": rows,
    }


def family_c_contract_parity_v2() -> dict:
    """316-case contract parity grid across `/1` Bridge, `/1` Adapter /3, and `/2` Adapter /4 (`convert_v1_to_v2`)."""
    par_s2 = S2.contract_parity()
    v2_bridge_served = 0
    v2_adapter3_served = 0
    v2_wrong_served = 0
    v2_disagree = 0
    for base in ("ABC", "ABCD"):
        edges = [f"S{x}" for x in base]
        for plane in ("parallel", "perpendicular"):
            for t in ("1/2", "1/3"):
                want = {"g_ratio": (F(t) ** 3) ** 2}
                for n in range(1, len(edges) + 1):
                    for cut in permutations(edges, n):
                        p1 = S2._payload(base, plane, list(cut), t)
                        rb = run_converted(p1, "bridge", want)
                        ra = run_converted(p1, "adapter3", want)
                        if rb["status"] == "SERVED":
                            v2_bridge_served += 1
                            if rb["wrong_served"]:
                                v2_wrong_served += 1
                        if ra["status"] == "SERVED":
                            v2_adapter3_served += 1
                            if ra["wrong_served"]:
                                v2_wrong_served += 1
                        if rb["status"] == "SERVED" and ra["status"] == "SERVED" and rb.get("answers") != ra.get("answers"):
                            v2_disagree += 1
    return {
        "cases": len(par_s2),
        "v1_bridge_served": sum(x["bridge"]["status"] == "SERVED" for x in par_s2),
        "v1_adapter3_served": sum(x["adapter3"]["status"] == "SERVED" for x in par_s2),
        "v2_adapter4_from_bridge_served": v2_bridge_served,
        "v2_adapter4_from_adapter3_served": v2_adapter3_served,
        "v1_both_served": sum(x["both_served_agree"] is not None for x in par_s2),
        "v1_both_served_disagree": sum(x["both_served_agree"] is False for x in par_s2),
        "v2_both_served_disagree": v2_disagree,
        "wrong_served": {
            "v1_bridge": sum(bool(x["bridge"].get("wrong_served")) for x in par_s2),
            "v1_adapter3": sum(bool(x["adapter3"].get("wrong_served")) for x in par_s2),
            "v2_adapter4": v2_wrong_served,
        },
    }


def family_d_metamorphic_v2() -> dict:
    """Metamorphic family (33 cases) on `/1` Bridge, `/1` Adapter /3, and `/2` Adapter /4."""
    mr_s2 = S2.metamorphic()
    v_sq, t3 = F(1, 9), F(1, 8)
    want = {"g_ratio": t3 ** 2, "g_res": ((1 - t3) ** 2) * v_sq}
    ref_v1 = S2._payload("ABCD", "perpendicular", S2.FULL, residual=True)

    def to_v2_full_stated(p1: dict) -> dict:
        return convert_v1_to_v2(deepcopy(p1), route="bridge")

    v2_rows = []
    v2_rows.append({"id": "MR-ref", "relation": "reference", "v2_adapter4": run_v2(to_v2_full_stated(ref_v1), want)})
    for order in permutations(range(4)):
        p1 = S2._sentences(ref_v1, list(order))
        v2_rows.append({"id": f"MR-premise-{''.join(map(str, order))}", "relation": "premise_permutation",
                        "v2_adapter4": run_v2(to_v2_full_stated(p1), want)})
    for i, m in enumerate(({"S": "T", "A": "E", "B": "F", "C": "G", "D": "H", "M": "U", "N": "V", "P": "X", "Q": "Y"},
                           {"S": "O", "A": "K", "B": "L", "C": "J", "D": "R", "M": "E", "N": "F", "P": "G", "Q": "I"})):
        s = json.dumps(ref_v1, ensure_ascii=False)
        s = re.sub(r"(?<![a-zà-ỹ])[SABCDMNPQ](?![a-zà-ỹ])", lambda x: m[x[0]], s)
        p1 = json.loads(s)
        p1["derived_sections"][0]["named_intersections"] = {
            f"{m['S']}-{m['A']}": m["M"],
            f"{m['S']}-{m['B']}": m["N"],
            f"{m['S']}-{m['C']}": m["P"],
            f"{m['S']}-{m['D']}": m["Q"],
        }
        v2_rows.append({"id": f"MR-relabel-{i}", "relation": "relabel",
                        "v2_adapter4": run_v2(to_v2_full_stated(p1), want)})
    g = deepcopy(ref_v1)
    g["math_goals"].reverse()
    v2_rows.append({"id": "MR-goal-order", "relation": "goal_order", "v2_adapter4": run_v2(to_v2_full_stated(g), want)})
    for i, para in enumerate(S2.PARAPHRASES):
        q = deepcopy(S2._payload("ABCD", "parallel", S2.FULL, residual=True))
        q["problem_text"] = q["problem_text"].replace(q["derived_sections"][0]["quote"], para)
        q["derived_sections"][0]["quote"] = para
        q["derived_sections"][0]["named_intersections"] = {"S-A": "M", "S-B": "N", "S-C": "P", "S-D": "Q"}
        v2_rows.append({"id": f"MR-paraphrase-{i}", "relation": "paraphrase",
                        "v2_adapter4": run_v2(to_v2_full_stated(q), want)})

    by_rel = {}
    for rel in ("reference", "premise_permutation", "relabel", "goal_order", "paraphrase"):
        xs_s2 = [x for x in mr_s2 if x["relation"] == rel]
        xs_v2 = [x for x in v2_rows if x["relation"] == rel]
        by_rel[rel] = {
            "v1_bridge": f"{sum(x['bridge']['status'] == 'SERVED' and not x['bridge']['wrong_served'] for x in xs_s2)}/{len(xs_s2)}",
            "v1_adapter3": f"{sum(x['adapter3']['status'] == 'SERVED' and not x['adapter3']['wrong_served'] for x in xs_s2)}/{len(xs_s2)}",
            "v2_adapter4_stated_4edges": f"{sum(x['v2_adapter4']['status'] == 'SERVED' and not x['v2_adapter4']['wrong_served'] for x in xs_v2)}/{len(xs_v2)}",
        }
    return {"by_relation": by_rel, "rows_v2": v2_rows}


def family_e_negatives_v2() -> dict:
    """20 negative payloads (`10 × 2` conventions) across `/1` Bridge, `/1` Adapter /3, and `/2` Adapter /4."""
    neg_s2 = S2.negatives()
    base = S2._payload("ABCD", residual=True)
    sec = base["derived_sections"][0]["quote"]
    cases = {}

    def edit(text_from: str, text_to: str, fix=None) -> dict:
        p = deepcopy(base)
        p["problem_text"] = p["problem_text"].replace(text_from, text_to)
        for o in (*p["premises"], *p["derived_sections"], *p["simulation_goals"], *p["math_goals"]):
            o["quote"] = o["quote"].replace(text_from, text_to)
        if fix:
            fix(p)
        return p

    p = deepcopy(base)
    p["derived_sections"][0]["named_intersections"] = {"S-B": "P", "S-C": "N", "S-D": "Q"}
    cases["N-swapped-names-4"] = p
    cases["N-unread-condition"] = edit("lần lượt tại N, P, Q.", "lần lượt tại N, P, Q sao cho NP = 2BC.")
    cases["N-negated-relation"] = edit("song song với (ABC)", "không song song với (ABC)")
    cases["N-conditional-plane"] = edit(sec, "Nếu " + sec[0].lower() + sec[1:-1] + " thì thiết diện là gì?")
    cases["N-wrong-number"] = edit("SA = a.", "SA = 2a.", lambda p: p["premises"][2]["args"].update(value="a"))
    cases["N-ratio-orientation-unstated"] = edit("Tính tỉ số thể tích của hai khối chóp S.MNPQ và S.ABCD.",
                                                 "Tính tỉ số thể tích.")
    cases["N-residual-ownership-unstated"] = edit(
        "Tính thể tích phần còn lại của khối chóp S.ABCD sau khi cắt bỏ khối chóp S.MNPQ.", "Tính thể tích phần còn lại.")
    p = deepcopy(base)
    p["problem_text"] = p["problem_text"].replace(" SA = a.", "")
    p["premises"] = [x for x in p["premises"] if x["quote"] != "SA = a."]
    cases["N-missing-height"] = p
    p = deepcopy(base)
    p["premises"][3]["quote"] = "Gọi M là trung điểm của SB."
    cases["N-quote-not-in-source"] = p
    cases["N-anonymous-ratio-operand-triangle"] = S2._anon_ratio()

    v2_rows = []
    for cid, p1 in cases.items():
        conv = deepcopy(p1)
        conv["derived_sections"][0]["cut_edges"] = []
        r_b = run_converted(p1, "bridge", None)
        r_a = run_converted(conv, "adapter3", None)
        v2_rows.append({"id": cid, "v2_from_bridge": r_b, "v2_from_adapter3_convention": r_a})

    v2_served = [
        r["id"] + ("/bridge" if k == "v2_from_bridge" else "/adapter3")
        for r in v2_rows
        for k in ("v2_from_bridge", "v2_from_adapter3_convention")
        if r[k]["status"] == "SERVED"
    ]
    return {
        "payloads": 20,
        "v1_bridge_served": [
            x["id"] + ("" if v is x["bridge_style"] else "/convention")
            for x in neg_s2 for v in (x["bridge_style"], x["adapter_convention"])
            if v["bridge"]["status"] == "SERVED"
        ],
        "v1_adapter3_served": [
            x["id"] + ("" if v is x["bridge_style"] else "/convention")
            for x in neg_s2 for v in (x["bridge_style"], x["adapter_convention"])
            if v["adapter3"]["status"] == "SERVED"
        ],
        "v2_adapter4_served": v2_served,
        "rows": v2_rows,
    }


def family_g_adapter3_dev_corpus_dual_run() -> dict:
    """Dual-run the 20-case Adapter /3 dev corpus (`typedfact-next-adapter3-simulation/corpus-dev.json`) on `/1` Adapter /3 and `/2` Adapter /4."""
    corpus_path = HERE.parent / "typedfact-next-adapter3-simulation" / "corpus-dev.json"
    cases = json.loads(corpus_path.read_text(encoding="utf-8"))["cases"]
    rows = []
    for c in cases:
        p = c["payload"]
        _, r3 = S2.run(A3, p)
        r4 = run_converted(p, "adapter3", None)
        rows.append({
            "id": c.get("case_id") or c.get("id"),
            "expected_status_v1": c.get("expected_status"),
            "v1_adapter3": {"status": r3["status"], "code": r3["code"], "authority": getattr(A3(deepcopy(p)), "source_verification", None) if r3["status"] == "SERVED" else None},
            "v2_adapter4_raw_converted": {"status": r4["status"], "code": r4["code"]},
        })
    return {
        "cases": len(rows),
        "v1_adapter3_status": dict(Counter(r["v1_adapter3"]["status"] for r in rows)),
        "v2_adapter4_raw_converted_codes": dict(Counter(r["v2_adapter4_raw_converted"]["code"] for r in rows)),
        "rows": rows,
    }


def family_h_route_b_benchmark() -> dict:
    """30-case × 2-arm (`facts` and `pipeline`) Route-B compiler benchmark."""
    from tests.geometry import hybrid_compiler_benchmark as HB

    cases = HB.cases()
    rows = []
    for c in cases:
        for arm in ("facts", "pipeline"):
            res = HB.classify(c, HB.run(c, arm))
            rows.append({"id": c["id"], "arm": arm, "gap": c.get("gap"), **res})
    return {
        "cases": len(cases),
        "evaluations": len(rows),
        "outcomes": dict(Counter(r["outcome"] for r in rows)),
        "wrong_served": sum(r["outcome"] == "wrong_served" for r in rows),
    }


def main(out_dir: Path) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    # Family A: Locked 47-case `/2` grammar/contract evaluation
    gs_out = out_dir / "family-a-locked-grammar-v2.json"
    GS.main(gs_out)
    fam_a = json.loads(gs_out.read_text(encoding="utf-8"))["aggregate"]

    # Family B: Session 1 60-case dual-run (`/1` Bridge vs `/1` Adapter /3 vs `/2` Adapter /4)
    fam_b = family_b_session1_dual_run(out_dir / "session1-family-replay.json")

    # Family C, F: Contract parity (316), IR budget (8), composition (40)
    fam_c = family_c_contract_parity_v2()
    bud = S2.budget()
    comp = S2.composition()

    # Family D: Metamorphic invariance (33)
    fam_d = family_d_metamorphic_v2()

    # Family E: Negative controls (20)
    fam_e = family_e_negatives_v2()

    # Family G: Adapter /3 20-case dev corpus dual-run
    fam_g = family_g_adapter3_dev_corpus_dual_run()

    # Family H: Route-B 30x2 compiler benchmark
    fam_h = family_h_route_b_benchmark()

    wall_s = round(time.perf_counter() - t0, 3)

    summary = {
        "classification": CLASSIFICATION,
        "provider_calls": 0,
        "wall_seconds": wall_s,
        "family_a_locked_grammar_v2": {
            k: fam_a[k] for k in ("lock_sha256", "cases", "match", "wrong_served", "by_expected", "confusion", "served_without_gate", "mismatches")
        },
        "family_b_session1_dual_run": {k: v for k, v in fam_b.items() if k != "rows"},
        "family_c_contract_parity": fam_c,
        "family_d_metamorphic": fam_d["by_relation"],
        "family_e_negative_controls": {k: v for k, v in fam_e.items() if k != "rows"},
        "family_f_ir_budget_and_composition": {
            "budget": [
                {
                    "id": x["id"],
                    "status": x["status"],
                    "code": x["code"],
                    "declarations_uncapped": x["uncapped"]["declarations"],
                    "duplicate_constructs_uncapped": x["uncapped"]["derived_duplicates"],
                }
                for x in bud
            ],
            "composition": comp,
        },
        "family_g_adapter3_dev_corpus": {k: v for k, v in fam_g.items() if k != "rows"},
        "family_h_route_b_benchmark": fam_h,
    }

    (out_dir / "session3-evaluation-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (out_dir / "session3-evaluation-full.json").write_text(
        json.dumps(
            {
                "summary": summary,
                "family_b_rows": fam_b["rows"],
                "family_d_rows": fam_d["rows_v2"],
                "family_e_rows": fam_e["rows"],
                "family_g_rows": fam_g["rows"],
            },
            ensure_ascii=False,
            indent=1,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
