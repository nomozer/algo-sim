# -*- coding: utf-8 -*-
"""Development evaluation (`DEVELOPMENT_EVALUATION_NOT_BLIND`) of run `backend-hybrid-contract-unification`.

Offline, 0 provider calls, authored TypedFactNext JSON (NOT natural-language extraction). Every family below was written by
the same author who wrote the fixes, so none of it is a blind or held-out result. Reuses, does not copy: the Session 1
template family / independent closed-form oracle / scene check (`../typedfactnext-planner-bridge/evaluate.py`) and the
payload builder of `backend/tests/geometry/test_hybrid_contract_unification.py`. Run from `backend/`:

    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this file> <out-dir>

Writes `<out-dir>/session1-family-replay.json` (the Session 1 60 cases, Session 1 scoring) and `<out-dir>/evaluation.json`.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(HERE.parent / "typedfactnext-planner-bridge"))
import evaluate as S1  # noqa: E402  (Session 1 harness: variant, oracle, square_of, scene_ok, leaks, depth)
from app.ai.adapter3_simulation import run_typed_fact_next_route as A3  # noqa: E402
from app.ai.function_route import run_typed_fact_next_planner_route as BR  # noqa: E402
import app.simulation.semantic_program.validator as V  # noqa: E402
from tests.geometry.test_hybrid_contract_unification import _anonymous_construction, _payload  # noqa: E402

CLASSIFICATION = "DEVELOPMENT_EVALUATION_NOT_BLIND"


def exact(res) -> dict:
    try:
        return {k: S1.square_of(v["coef"]) for k, v in (res.answer_exact or {}).items()}
    except (ValueError, KeyError, TypeError):
        return {"UNREADABLE": True}


def run(route, payload) -> tuple[object, dict]:
    t0 = time.perf_counter()
    try:
        r = route(deepcopy(payload))
        row = {"status": r.status, "code": r.code, "seconds": round(time.perf_counter() - t0, 4)}
    except Exception as e:  # noqa: BLE001 — a crash is a finding, recorded
        return None, {"status": "CRASH", "code": type(e).__name__, "seconds": round(time.perf_counter() - t0, 4)}
    if r.status == "SERVED":
        row["answers"] = {k: str(v) for k, v in exact(r).items()}
        row["scene_valid"] = S1.scene_ok(r.scene3d)[0]
    return r, row


def both(payload, want: dict | None) -> dict:
    """Both routes on one payload; `want` = oracle squared answers (None: an invalid input every route must refuse)."""
    rows = {}
    for name, route in (("bridge", BR), ("adapter3", A3)):
        r, row = run(route, payload)
        if r is not None and r.status == "SERVED":
            got = exact(r)
            row["wrong_served"] = want is None or {k: got.get(k) for k in want} != want
            if name == "adapter3":
                row["source_authority"] = (r.source_verification or {}).get("authority")
        rows[name] = row
    b, a = rows["bridge"], rows["adapter3"]
    rows["both_served_agree"] = (b.get("answers") == a.get("answers")) if b["status"] == a["status"] == "SERVED" else None
    return rows


# ── families ───────────────────────────────────────────────────────────────────────────────────────────────────────

def contract_parity() -> list[dict]:
    """Every ordered subset of the lateral edges as `cut_edges`, both bases, both plane kinds, two ratios."""
    out = []
    for base in ("ABC", "ABCD"):
        edges = [f"S{x}" for x in base]
        for plane in ("parallel", "perpendicular"):
            for t in ("1/2", "1/3"):
                want = {"g_ratio": (F(t) ** 3) ** 2}
                for n in range(1, len(edges) + 1):
                    for cut in permutations(edges, n):
                        out.append({"id": f"P-{base}-{plane}-t{t.replace('/', '')}-{''.join(cut)}",
                                    **both(_payload(base, plane, list(cut), t), want)})
    return out


def _hexagon(plane: str) -> dict:
    """Regular hexagonal base, SA ⊥ base, plane through the midpoint M of SA, every other lateral edge stated as cut."""
    p = _payload("ABCD", plane, residual=True)
    b, names = list("ABCDEF"), ["N", "P", "Q", "R", "T"]
    cut = [f"S{x}" for x in b[1:]]
    s = json.dumps(p, ensure_ascii=False).replace("Đáy ABCD là hình vuông cạnh a.", "Đáy ABCDEF là lục giác đều cạnh a.") \
        .replace("cắt SB, SC, SD lần lượt tại N, P, Q.", f"cắt {', '.join(cut)} lần lượt tại {', '.join(names)}.")
    s = re.sub(r"S\.MNPQ(?![A-Z])", "S.MNPQRT", re.sub(r"S\.ABCD(?![A-Z])", "S.ABCDEF", s))
    p = json.loads(s)
    p["premises"][0] = {"kind": "base_is_regular_polygon", "args": {"vertices": b, "side": "a"},
                        "quote": "Đáy ABCDEF là lục giác đều cạnh a."}
    p["derived_sections"][0].update(cut_edges=[list(e) for e in cut],
                                    named_intersections={f"{e[0]}-{e[1]}": n for e, n in zip(cut, names)})
    return p


def budget() -> list[dict]:
    """IR declarations per plan with the budget lifted (diagnostic only: the product budget stays 32)."""
    rows, real = [], V.MAX_MEMORY_DECLARATIONS
    cases = [(f"BUD-{shape}{si}-{plane}", S1.variant(shape, dims, h=F(2) if shape == "rectangle" else F(1),
                                                     sym=shape != "rectangle", t=F(1, 2), plane=plane, residual=True)[0])
             for si, (shape, dims) in enumerate((("equilateral", (F(1),)), ("square", (F(2),)), ("rectangle", (F(3), F(4)))))
             for plane in ("parallel", "perpendicular")]
    cases += [(f"BUD-hexagon-{plane}", _hexagon(plane)) for plane in ("parallel", "perpendicular")]
    for cid, p in cases:
        _r, row = run(BR, p)
        V.MAX_MEMORY_DECLARATIONS = 10 ** 6
        try:
            r = BR(deepcopy(p))
            size = len(r.program["memory_declarations"]) if r.status == "SERVED" else None
            row["uncapped"] = {"status": r.status, "code": r.code, "declarations": size,
                               "derived_duplicates": _duplicates(r.program) if r.status == "SERVED" else None}
        finally:
            V.MAX_MEMORY_DECLARATIONS = real
        rows.append({"id": cid, **row})
    return rows


def _duplicates(program: dict) -> int:
    d = [(s["kind"], s.get("through_a"), s.get("through_b"), tuple(s.get("through") or ()))
         for s in program["statements"] if s["kind"] in ("construct_line", "construct_plane")]
    return len(d) - len(set(d))


def _sentences(p: dict, order: list[int]) -> dict:
    """Reorder the premise sentences in the text AND the premise list (both orders follow `order`)."""
    q = deepcopy(p)
    old = [x["quote"] for x in p["premises"]]
    joined = " ".join(old)
    assert joined in q["problem_text"]
    q["problem_text"] = q["problem_text"].replace(joined, " ".join(old[i] for i in order))
    q["premises"] = [p["premises"][i] for i in order]
    return q


#: The complete cycle (SA's cut is M itself) is a `cut_edges` value BOTH readings accept, so both routes are measured.
FULL = ["SA", "SB", "SC", "SD"]
PARAPHRASES = (
    "Mặt phẳng (α) đi qua M, song song với mặt phẳng (ABC), cắt SA, SB, SC, SD lần lượt tại M, N, P, Q.",
    "Gọi (α) là mặt phẳng qua M và song song với (ABC); (α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q.",
    "Qua M dựng mặt phẳng (α) song song với (ABC), (α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q.",
    "Mặt phẳng (α) chứa M và song song với (ABC) cắt các cạnh SA, SB, SC, SD lần lượt tại M, N, P, Q.",
    "Mặt phẳng (α) qua M song song với (ABC) và cắt SA tại M, cắt SB tại N, cắt SC tại P, cắt SD tại Q.",
)


def metamorphic() -> list[dict]:
    rows = []
    ref = _payload("ABCD", "perpendicular", FULL, residual=True)     # was over the IR budget in Session 1
    v_sq, t3 = F(1, 9), F(1, 8)
    want = {"g_ratio": t3 ** 2, "g_res": ((1 - t3) ** 2) * v_sq}
    rows.append({"id": "MR-ref", "relation": "reference", **both(ref, want)})
    for order in permutations(range(4)):
        rows.append({"id": f"MR-premise-{''.join(map(str, order))}", "relation": "premise_permutation",
                     **both(_sentences(ref, list(order)), want)})
    for i, m in enumerate(({"S": "T", "A": "E", "B": "F", "C": "G", "D": "H", "M": "U", "N": "V", "P": "X", "Q": "Y"},
                           {"S": "O", "A": "K", "B": "L", "C": "J", "D": "R", "M": "E", "N": "F", "P": "G", "Q": "I"})):
        s = json.dumps(ref, ensure_ascii=False)
        s = re.sub(r"(?<![a-zà-ỹ])[SABCDMNPQ](?![a-zà-ỹ])", lambda x: m[x[0]], s)
        rows.append({"id": f"MR-relabel-{i}", "relation": "relabel", **both(json.loads(s), want)})
    g = deepcopy(ref)
    g["math_goals"].reverse()
    rows.append({"id": "MR-goal-order", "relation": "goal_order", **both(g, want)})
    sec_q = ref["derived_sections"][0]["quote"]
    for i, para in enumerate(PARAPHRASES):
        q = deepcopy(_payload("ABCD", "parallel", FULL, residual=True))
        q["problem_text"] = q["problem_text"].replace(q["derived_sections"][0]["quote"], para)
        q["derived_sections"][0]["quote"] = para
        rows.append({"id": f"MR-paraphrase-{i}", "relation": "paraphrase", **both(q, want)})
    assert sec_q in ref["problem_text"]
    return rows


def negatives() -> list[dict]:
    """Invalid inputs: every sound route must refuse (bridge-style payload AND Adapter /3 convention, no cut_edges)."""
    base = _payload("ABCD", residual=True)
    sec = base["derived_sections"][0]["quote"]
    cases = {}

    def edit(text_from: str, text_to: str, fix=None) -> dict:
        p = deepcopy(base)
        assert text_from in p["problem_text"], text_from
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
    p["premises"][3]["quote"] = "Gọi M là trung điểm của SB."                     # quote not in the text
    cases["N-quote-not-in-source"] = p
    cases["N-anonymous-ratio-operand-triangle"] = _anon_ratio()
    rows = []
    for cid, p in cases.items():
        conv = deepcopy(p)
        conv["derived_sections"][0]["cut_edges"] = []
        rows.append({"id": cid, "bridge_style": both(p, None), "adapter_convention": both(conv, None)})
    return rows


def _anon_ratio() -> dict:
    p = _payload("ABC")
    sec_q = p["derived_sections"][0]["quote"]
    plain = sec_q.replace(" lần lượt tại N, P.", ".")
    p["problem_text"] = p["problem_text"].replace(sec_q, plain).replace(
        "Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC.", "Tính tỉ số thể tích.")
    p["derived_sections"][0].update(quote=plain, named_intersections={})
    for g in (*p["simulation_goals"][1:], *p["math_goals"]):
        g["quote"] = "Tính tỉ số thể tích."
    return p


def composition() -> dict:
    """Plan structure of every served bridge case of the Session 1 family plus the parity family."""
    plans = []
    for cid, p in [(f"S1-{i}", x) for i, x in enumerate(_s1_payloads())] + [
            (f"C-{b}", _anonymous_construction(b)) for b in ("ABC", "ABCD")]:
        r = BR(deepcopy(p))
        if r.status != "SERVED":
            continue
        calls = r.planner["calls"]
        sig = [(c["fn"], json.dumps(c["args"], sort_keys=True, ensure_ascii=False)) for c in calls]
        sel = [s for s in r.planner["trace"] if s.get("step") == "effect_resolution" and "need" in s]
        plans.append({"id": cid, "calls": len(calls), "duplicate_calls": len(sig) - len(set(sig)),
                      "ir_duplicate_constructs": _duplicates(r.program), "dag_depth": S1.depth(calls),
                      "declarations": len(r.program["memory_declarations"]),
                      "selections": Counter(s["selection"] for s in sel),
                      "derived_planes": sum(1 for d in r.planner["auxiliary"] if d.get("rule", "").startswith("section(")),
                      "sections": sum(1 for c in calls if c["fn"] in ("section", "ask_section_area"))})
    sel = Counter()
    for x in plans:
        sel.update(x["selections"])
    return {"plans": len(plans), "duplicate_calls": sum(x["duplicate_calls"] for x in plans),
            "ir_duplicate_constructs": sum(x["ir_duplicate_constructs"] for x in plans),
            "dag_depth": [min(x["dag_depth"] for x in plans), max(x["dag_depth"] for x in plans)],
            "declarations": [min(x["declarations"] for x in plans), max(x["declarations"] for x in plans)],
            "selection_counts": dict(sel), "plane_constructions_per_section": sorted(
                {round(x["derived_planes"] / max(1, x["sections"]), 2) for x in plans})}


def _s1_payloads() -> list[dict]:
    shapes = [("equilateral", (F(1),)), ("equilateral", (F(2),)), ("square", (F(1),)), ("square", (F(2),)),
              ("rectangle", (F(3), F(4))), ("right", (F(3), F(4)))]
    return [S1.variant(shape, dims, h=F(2) if shape not in ("equilateral", "square") else F(1),
                       sym=shape in ("equilateral", "square"), t=t, plane=plane, residual=True)[0]
            for shape, dims in shapes for t in (F(1, 2), F(1, 3), F(2, 3)) for plane in ("parallel", "perpendicular")]


def summarise(par, bud, mr, neg, comp) -> dict:
    def served(rows, r):
        return sum(x[r]["status"] == "SERVED" for x in rows)

    def wrong(rows, r):
        return sum(bool(x[r].get("wrong_served")) for x in rows)
    neg_flat = [v for x in neg for v in (x["bridge_style"], x["adapter_convention"])]
    mr_inv = {}
    for rel in ("premise_permutation", "relabel", "goal_order", "paraphrase"):
        xs = [x for x in mr if x["relation"] == rel]
        mr_inv[rel] = {r: f"{sum(x[r]['status'] == 'SERVED' and not x[r]['wrong_served'] for x in xs)}/{len(xs)}"
                       for r in ("bridge", "adapter3")}
    return {
        "contract_parity": {
            "cases": len(par), "bridge_served": served(par, "bridge"), "adapter3_served": served(par, "adapter3"),
            "both_served": sum(x["both_served_agree"] is not None for x in par),
            "both_served_disagree": sum(x["both_served_agree"] is False for x in par),
            "wrong_served": {"bridge": wrong(par, "bridge"), "adapter3": wrong(par, "adapter3")},
            "crashes": sum(x[r]["status"] == "CRASH" for x in par for r in ("bridge", "adapter3")),
            "adapter3_refusal_codes": dict(Counter(x["adapter3"]["code"] for x in par if x["adapter3"]["status"] != "SERVED")),
            "bridge_refusal_codes": dict(Counter(x["bridge"]["code"] for x in par if x["bridge"]["status"] != "SERVED")),
        },
        "budget": [{"id": x["id"], "status": x["status"], "code": x["code"], "declarations_uncapped": x["uncapped"]["declarations"],
                    "duplicate_constructs_uncapped": x["uncapped"]["derived_duplicates"]} for x in bud],
        "metamorphic_invariance": mr_inv,
        "metamorphic_reference": {r: mr[0][r]["status"] for r in ("bridge", "adapter3")},
        "negatives": {"payloads": len(neg_flat),
                      "served": {r: [x["id"] + ("" if v is x["bridge_style"] else "/convention")
                                     for x in neg for v in (x["bridge_style"], x["adapter_convention"])
                                     if v[r]["status"] == "SERVED"] for r in ("bridge", "adapter3")},
                      "crashes": sum(v[r]["status"] == "CRASH" for v in neg_flat for r in ("bridge", "adapter3"))},
        "scene_valid": {r: f"{sum(bool(v[r].get('scene_valid')) for v in _all(par, mr, neg) if v[r]['status'] == 'SERVED')}"
                           f"/{sum(v[r]['status'] == 'SERVED' for v in _all(par, mr, neg))}" for r in ("bridge", "adapter3")},
        "composition": comp,
        "seconds": {r: {"p50": _p(sorted(v[r]["seconds"] for v in _all(par, mr, neg)), 50),
                        "max": max(v[r]["seconds"] for v in _all(par, mr, neg))} for r in ("bridge", "adapter3")},
    }


def _all(par, mr, neg):
    return [*par, *mr, *(v for x in neg for v in (x["bridge_style"], x["adapter_convention"]))]


def _p(xs, q):
    return xs[min(len(xs) - 1, len(xs) * q // 100)]


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    S1.main(out / "session1-family-replay.json")
    par, bud, mr, neg = contract_parity(), budget(), metamorphic(), negatives()
    comp = composition()
    agg = summarise(par, bud, mr, neg, comp)
    (out / "evaluation.json").write_text(json.dumps(
        {"classification": CLASSIFICATION, "provider_calls": 0, "aggregate": agg,
         "families": {"contract_parity": par, "budget": bud, "metamorphic": mr, "negatives": neg}},
        ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
