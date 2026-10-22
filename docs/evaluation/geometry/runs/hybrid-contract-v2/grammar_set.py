# -*- coding: utf-8 -*-
"""Preregistered Source-Gate grammar / contract evaluation set (run `hybrid-contract-v2`, P4a). LOCKED before any grammar
or `/2` implementation change: `grammar-set.json` + its SHA-256 are committed first; expectations are never edited
afterwards (a later disagreement is diagnosed, not "fixed" in the lock).

Classification: DEVELOPMENT_EVALUATION_NOT_BLIND — authored by the same agent that implements the changes; preregistered
(expectations fixed before tuning), NOT independent, NOT blind.

Each case: problem text, a `typed-fact-next/2` payload (shape of CONTRACT_DECISION_PROPOSAL.md §3 of run
`backend-hybrid-contract-unification`), the expected class of a correct system, and — for SERVE — exact answers from a
closed-form oracle (plain Fraction arithmetic, no engine import):

    SERVE            the problem is well-posed and in the declared scope; answers are the oracle's
    REFUSE_SOURCE    the source does not support a fact / goal the payload asserts (wording, ownership, negation, …)
    REFUSE_GEOMETRY  the geometry is contradictory, degenerate, or the declared boundary is wrong
    REFUSE_KERNEL    well-posed, but outside what the kernel / planner / IR budget supports (a capability gap)

Run: python grammar_set.py <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

CLASSIFICATION = "DEVELOPMENT_EVALUATION_NOT_BLIND (preregistered, same author)"
SHAPES = {"ABC": ("Đáy {b} là tam giác đều cạnh a.", "base_is_equilateral_triangle", F(3, 16)),
          "ABCD": ("Đáy {b} là hình vuông cạnh a.", "base_is_square", F(1))}


def pyramid(base="ABC", apex="S", m="M", t="1/2", plane="parallel", plane_name="α", section_sentence=None,
            stated=None, declared=None, request=None, ratio=True, residual=False, residual_first=False,
            premise_order=None, ratio_text=None, residual_text=None, sub_name=None, extra_premise=None,
            drop_height=False, height_text="SA = a.", height_value="a", perp_text=None):
    """A pyramid problem in the template family: base side a, SA ⊥ base, SA = a, point m on SA with SM = t·SA."""
    b, A = list(base), base[0]
    S = apex
    sa = f"{S}{A}"
    shape_t, shape_k, area2 = SHAPES[base] if base in SHAPES else SHAPES[{3: "ABC", 4: "ABCD"}[len(base)]]
    shape_t = shape_t.format(b=base)
    perp_t = perp_text or f"{sa} vuông góc với mặt phẳng ({base[:3]})."
    m_t = f"Gọi {m} là trung điểm của {sa}." if t == "1/2" else f"Điểm {m} thuộc cạnh {sa} sao cho {S}{m} = {t} {sa}."
    m_p = ({"kind": "point_is_midpoint", "args": {"point": m, "segment": [S, A]}} if t == "1/2" else
           {"kind": "point_divides_segment", "args": {"point": m, "segment": [S, A], "ratio": t}})
    prem = [(shape_t, {"kind": shape_k, "args": {"vertices": b, "side": "a"}}),
            (perp_t, {"kind": "line_perp_plane", "args": {"line": [S, A], "plane": b[:3]}}),
            (height_text, {"kind": "segment_length", "args": {"segment": [S, A], "value": height_value}}), (m_t, m_p)]
    if drop_height:
        prem.pop(2)
    if extra_premise:
        prem.append(extra_premise)
    order = premise_order or range(len(prem))
    stated = stated if stated is not None else [(f"{S}{x}", n) for x, n in zip(b[1:], "NPQ")]
    rel = f"song song với ({base[:3]})" if plane == "parallel" else f"vuông góc với {sa}"
    if section_sentence is None:
        names = [n for _e, n in stated]
        cut = (f" cắt {', '.join(e for e, _ in stated)}" + (f" lần lượt tại {', '.join(names)}" if all(names) else "")
               if stated else "")
        section_sentence = f"Mặt phẳng ({plane_name}) qua {m} và {rel}{cut}."
    sub = sub_name or f"{S}.{m}{''.join(n for e, n in stated if n and e != sa)}"
    req = request if request is not None else f"Dựng thiết diện của hình chóp {S}.{base} bởi ({plane_name})."
    ratio_q = ratio_text or f"Tính tỉ số thể tích của hai khối chóp {sub} và {S}.{base}."
    res_q = residual_text or f"Tính thể tích phần còn lại của khối chóp {S}.{base} sau khi cắt bỏ khối chóp {sub}."
    asks = ([("g_ratio", ratio_q)] if ratio else []) + ([("g_res", res_q)] if residual else [])
    if residual_first:
        asks.reverse()
    text = " ".join([f"Cho hình chóp {S}.{base}.", *(prem[i][0] for i in order), section_sentence, req, *(q for _g, q in asks)])
    sec = {"section_id": "sec", "plane_name": plane_name, "target_solid_id": "pyr", "through_point": m,
           "quote": section_sentence.rstrip("."),
           "stated_intersections": [{"edge": list(e), "point": n, "quote": section_sentence.rstrip(".")} for e, n in stated],
           **({"declared_boundary": [list(e) for e in declared]} if declared else {}),
           **({"plane_kind": "through_point_parallel_plane", "parallel_plane": b[:3]} if plane == "parallel" else
              {"plane_kind": "through_point_perpendicular_line", "perpendicular_line": [S, A]})}
    sim = [{"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec", "quote": req.rstrip(".")}]
    math = []
    if asks:
        sim.append({"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub", "target_section_id": "sec",
                    "apex_ref": S, "parent_solid_id": "pyr", "quote": asks[0][1].rstrip(".")})
        for g, q in asks:
            math.append({"goal_id": g, "kind": "volume_ratio", "numerator_solid_id": "sub", "denominator_solid_id": "pyr",
                         "quote": q.rstrip(".")} if g == "g_ratio" else
                        {"goal_id": g, "kind": "residual_volume", "parent_solid_id": "pyr", "cut_solid_id": "sub",
                         "quote": q.rstrip(".")})
    payload = {"schema_version": "typed-fact-next/2", "problem_text": text,
               "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": f"{S}.{base}", "quote": f"Cho hình chóp {S}.{base}"}],
               "premises": [{**p, "quote": q.rstrip(".")} for q, p in (prem[i] for i in order)],
               "derived_sections": [sec], "simulation_goals": sim, "math_goals": math}
    tt = F(t) ** 3                        # oracle: a plane ∥ base (≡ ⊥ SA when SA ⊥ base) through M cuts every lateral edge at t
    v2 = area2 / 9                        # V² = S²·h²/9, h = a
    answers = {}
    if ratio:
        answers["g_ratio"] = str(tt * tt)
    if residual:
        answers["g_res"] = str((1 - tt) ** 2 * v2)
    return payload, answers


def construction_only(p: dict, request: str) -> dict:
    """Drop the math goals; the request asks to build the section and the derived pyramid only."""
    q = json.loads(json.dumps(p))
    old_req = next(g["quote"] for g in q["simulation_goals"] if g["kind"] == "construct_plane_section")
    head = q["problem_text"].split(old_req)[0]
    q["problem_text"] = head + request
    q["math_goals"] = []
    q["simulation_goals"] = [{"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec",
                              "quote": request.rstrip(".")},
                             {"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                              "target_section_id": "sec", "apex_ref": q["solids"][0]["notation"].split(".")[0],
                              "parent_solid_id": "pyr", "quote": request.rstrip(".")}]
    return q


def cases() -> list[dict]:
    out = []

    def add(cid, category, expected, payload, answers=None, note=""):
        out.append({"id": cid, "category": category, "expected": expected, "answers": answers or {}, "note": note,
                    "payload": payload})

    full = [("SA", "M"), ("SB", "N"), ("SC", "P"), ("SD", "Q")]
    paraphrases = (
        "Mặt phẳng (α) qua M và song song với (ABC) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q.",
        "Mặt phẳng (α) đi qua M, song song với mặt phẳng (ABC), cắt SA, SB, SC, SD lần lượt tại M, N, P, Q.",
        "Gọi (α) là mặt phẳng qua M và song song với (ABC); (α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q.",
        "Qua M dựng mặt phẳng (α) song song với (ABC), (α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q.",
        "Mặt phẳng (α) chứa M và song song với (ABC) cắt các cạnh SA, SB, SC, SD lần lượt tại M, N, P, Q.",
        "Mặt phẳng (α) qua M song song với (ABC) và cắt SA tại M, cắt SB tại N, cắt SC tại P, cắt SD tại Q.",
    )
    for i, s in enumerate(paraphrases):
        p, a = pyramid("ABCD", stated=full, section_sentence=s, residual=True)
        add(f"PARA-{i}", "known_paraphrase" if i else "paraphrase_reference", "SERVE", p, a,
            "Session 2 paraphrase family (PARA-1..5); PARA-0 is the reference wording")

    # Adapter /3 dev-corpus section sentences, construction-only requests in the corpus's own wording
    dev = [
        ("DEV01", "ABCD", "Mặt phẳng (α) đi qua M và song song với đáy (ABCD) cắt các cạnh SB, SC, SD.", "parallel",
         "Dựng thiết diện của hình chóp cắt bởi (α), khối chóp cắt bởi (α) chứa đỉnh S."),
        ("DEV03", "ABC", "Mặt phẳng (α) qua M và vuông góc với SA cắt SB, SC.", "perpendicular",
         "Dựng từng bước hình chóp, thiết diện bởi (α), khối chóp đỉnh S cắt bởi (α), làm nổi bật thiết diện."),
        ("DEV06", "ABC", "Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC.", "parallel",
         "Dựng từng bước hình chóp, thiết diện bởi (α), khối chóp đỉnh S cắt bởi (α), làm nổi bật thiết diện."),
        ("DEV09", "ABCD", "Mặt phẳng (α) qua M và song song với (ABCD) cắt SB, SC, SD.", "parallel",
         "Dựng thiết diện, khối chóp đỉnh S cắt bởi (α)."),
    ]
    for cid, base, sent, plane, req in dev:
        stated = [(f"S{x}", None) for x in base[1:]]
        p, _a = pyramid(base, plane=plane, stated=stated, section_sentence=sent, ratio=False)
        add(f"CORPUS-{cid}-construct", "dev_corpus_section_sentence", "SERVE", construction_only(p, req), {},
            "section sentence verbatim from the Adapter /3 dev corpus; corpus ratio question replaced by a construction "
            "request (the original asks 'tính tỉ số thể tích' without operands, see OWN-*)")
        p, _a = pyramid(base, plane=plane, stated=stated, section_sentence=sent, ratio=True,
                        ratio_text="Tính tỉ số thể tích.", sub_name="x")
        add(f"CORPUS-{cid}-ratio-unowned", "ratio_without_operands", "REFUSE_SOURCE", p, {},
            "the corpus' own 'tính tỉ số thể tích' names neither solid: orientation not in the source (P1.4)")

    # prism corpus sentence (A3-DEV-10): area of the section, a triangle congruent to the base
    text = ("Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh a và AA' = 2a. Gọi M là trung điểm của AA'. "
            "Mặt phẳng (α) qua M và song song với (ABC) cắt BB', CC'. Dựng lăng trụ, thiết diện bởi (α) và tính diện tích "
            "thiết diện.")
    sec_q = "Mặt phẳng (α) qua M và song song với (ABC) cắt BB', CC'"
    add("CORPUS-DEV10-prism-area", "dev_corpus_section_sentence", "SERVE", {
        "schema_version": "typed-fact-next/2", "problem_text": text,
        "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho lăng trụ đứng ABC.A'B'C'"}],
        "premises": [{"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                      "quote": "Cho lăng trụ đứng ABC.A'B'C'"},
                     {"kind": "base_is_equilateral_triangle", "args": {"vertices": ["A", "B", "C"], "side": "a"},
                      "quote": "đáy ABC là tam giác đều cạnh a"},
                     {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "2a"}, "quote": "AA' = 2a"},
                     {"kind": "point_is_midpoint", "args": {"point": "M", "segment": ["A", "A'"]}, "quote": "Gọi M là trung điểm của AA'"}],
        "derived_sections": [{"section_id": "sp", "plane_name": "α", "target_solid_id": "pr", "through_point": "M",
                              "plane_kind": "through_point_parallel_plane", "parallel_plane": ["A", "B", "C"], "quote": sec_q,
                              "stated_intersections": [{"edge": ["B", "B'"], "point": None, "quote": sec_q},
                                                       {"edge": ["C", "C'"], "point": None, "quote": sec_q}]}],
        "simulation_goals": [{"goal_id": "g", "kind": "construct_plane_section", "target_section_id": "sp",
                              "quote": "thiết diện bởi (α)"}],
        "math_goals": [{"goal_id": "g_area", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sp"},
                        "quote": "tính diện tích thiết diện"}]}, {"g_area": str(F(3, 16))},
        "A3-DEV-10 verbatim; area² of an equilateral triangle of side a = 3/16")

    # partial / plane-only statements: the other cut vertices are DERIVED (D6)
    p, a = pyramid("ABC", stated=[("SB", "N")], section_sentence="Mặt phẳng (α) qua M và song song với (ABC) cắt SB tại N.",
                   ratio=False)
    add("PARTIAL-1of2-construct", "partial_intersections", "SERVE",
        construction_only(p, "Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp đỉnh S cắt bởi (α)."), {},
        "SC's cut is not stated: derived (D6), never presented as a source fact")
    p, a = pyramid("ABCD", stated=[("SB", "N"), ("SD", "Q")],
                   section_sentence="Mặt phẳng (α) qua M và song song với (ABCD) cắt SB, SD lần lượt tại N, Q.", ratio=False)
    add("PARTIAL-2of3-construct", "partial_intersections", "SERVE",
        construction_only(p, "Dựng thiết diện của hình chóp S.ABCD bởi (α) và khối chóp đỉnh S cắt bởi (α)."), {})
    p, a = pyramid("ABC", stated=[], section_sentence="Mặt phẳng (α) qua M và song song với (ABC).", ratio=False)
    add("PLANE-ONLY-construct", "plane_only", "SERVE",
        construction_only(p, "Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp đỉnh S cắt bởi (α)."), {})
    p, a = pyramid("ABC", stated=[], section_sentence="Mặt phẳng (α) qua M và song song với (ABC).", ratio=True,
                   ratio_text="Tính tỉ số thể tích của khối chóp đỉnh S cắt bởi (α) và khối chóp S.ABC.", sub_name="x")
    add("PLANE-ONLY-ratio-described", "plane_only", "SERVE", p, a,
        "the derived pyramid is named by description ('khối chóp đỉnh S cắt bởi (α)'), both operands in order")

    # relabeling, premise order, goal order
    p, a = pyramid("DEF", apex="T", m="K", stated=[("TE", "X"), ("TF", "Y")], residual=True, height_text="TD = a.",
                   perp_text="TD vuông góc với mặt phẳng (DEF).")
    add("RELABEL-TDEF", "relabel", "SERVE", p, a)
    for i, order in enumerate(([3, 2, 1, 0], [1, 0, 3, 2])):
        p, a = pyramid("ABCD", premise_order=order, residual=True)
        add(f"ORDER-premises-{i}", "premise_order", "SERVE", p, a)
    p, a = pyramid("ABCD", residual=True, residual_first=True)
    add("ORDER-goals", "goal_order", "SERVE", p, a)
    p, a = pyramid("ABCD", "S", "M", "1/3", "perpendicular", residual=True)
    add("PERP-square-third", "reference", "SERVE", p, a, "⊥ SA with SA ⊥ base: the same plane as ∥ base")

    # negations, conditions, missing data, numbers on the wrong object / relation, goals without operands
    p, _a = pyramid("ABC", section_sentence="Mặt phẳng (α) qua M và không song song với (ABC) cắt SB, SC lần lượt tại N, P.")
    add("NEG-negated-plane", "negation", "REFUSE_SOURCE", p)
    p, _a = pyramid("ABC", section_sentence="Nếu mặt phẳng (α) qua M và song song với (ABC) thì (α) cắt SB, SC lần lượt tại N, P.")
    add("NEG-conditional-plane", "condition", "REFUSE_SOURCE", p)
    p, _a = pyramid("ABC", drop_height=True)
    add("NEG-missing-height", "missing_data", "REFUSE_SOURCE", p, note="SA's length not given: the solid is not determined")
    p, _a = pyramid("ABC", height_text="SB = a.")
    add("NEG-number-wrong-object", "number_wrong_object", "REFUSE_SOURCE", p, note="the quote states SB = a; payload claims SA = a")
    p, _a = pyramid("ABC", perp_text="SA vuông góc với SB.")
    add("NEG-wrong-relation", "wrong_relation", "REFUSE_SOURCE", p, note="the quote states SA ⊥ SB; payload claims SA ⊥ (ABC)")
    p, _a = pyramid("ABC", ratio_text="Tính tỉ số thể tích.")
    add("NEG-ratio-unowned-named", "ratio_without_operands", "REFUSE_SOURCE", p)
    p, _a = pyramid("ABC", stated=[], section_sentence="Mặt phẳng (α) qua M và song song với (ABC).",
                    ratio_text="Tính tỉ số thể tích.", sub_name="x")
    add("NEG-ratio-unowned-anonymous", "ratio_without_operands", "REFUSE_SOURCE", p,
        note="Session 2 known invalid serve (anonymous operand): must refuse on /2 (P1.4)")
    p, _a = pyramid("ABC", ratio=False, residual=True, residual_text="Tính thể tích phần còn lại.")
    add("NEG-residual-unowned", "residual_without_operands", "REFUSE_SOURCE", p)
    p, _a = pyramid("ABC", stated=[("SB", "P"), ("SC", "N")],
                    section_sentence="Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC lần lượt tại N, P.", sub_name="S.MPN")
    add("NEG-swapped-names", "wrong_naming", "REFUSE_SOURCE", p)
    p, _a = pyramid("ABC", section_sentence="Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC lần lượt tại N, P sao cho NP = BC.")
    add("NEG-unread-condition", "unread_condition", "REFUSE_SOURCE", p)
    p, _a = pyramid("ABC", stated=[("SA", None), ("SB", "N"), ("SC", "P")],
                    section_sentence="Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC lần lượt tại N, P.")
    add("NEG-stated-edge-not-in-text", "stated_not_in_source", "REFUSE_SOURCE", p,
        note="payload states a cut on SA; the text states only SB, SC (use declared_boundary for a boundary)")
    p, _a = pyramid("ABC", section_sentence="Mặt phẳng (α) chứa SA và song song với BC cắt SB, SC lần lượt tại N, P.")
    add("NEG-contains-a-line", "grammar_negative_control", "REFUSE_SOURCE", p,
        note="'chứa SA' is a line, not 'qua M' — must not bind as the through-point clause")
    p, _a = pyramid("ABC", section_sentence="Mặt phẳng (α) qua M và song song với (ABC); (β) cắt SB, SC lần lượt tại N, P.")
    add("NEG-other-plane-subject", "grammar_negative_control", "REFUSE_SOURCE", p,
        note="the restated subject is a different plane (β)")
    p, _a = pyramid("ABC", stated=[("SB", "N"), ("SC", "N")],
                    section_sentence="Mặt phẳng (α) qua M song song với (ABC) và cắt SB tại N, cắt SC tại N.", sub_name="S.MNN")
    add("NEG-per-edge-same-name", "grammar_negative_control", "REFUSE_SOURCE", p)
    p, _a = pyramid("ABC", section_sentence="Qua M dựng mặt phẳng (α) song song với (SBC), (α) cắt SB, SC lần lượt tại N, P.")
    add("NEG-point-first-wrong-reference", "grammar_negative_control", "REFUSE_SOURCE", p,
        note="point-first wording names (SBC); payload claims ∥ (ABC)")
    p, _a = pyramid("ABC", section_sentence="Mặt phẳng (α) qua M và song song với (ABC) và cắt SB tại N, cắt SC tại P.")
    add("POS-per-edge-with-va-cat", "grammar_positive_control", "SERVE", p, pyramid("ABC")[1],
        note="positive control for the per-edge form with 'và cắt' (same facts as the reference)")

    # geometry: contradictory / degenerate / wrong declared boundary
    p, _a = pyramid("ABC", extra_premise=("Biết SA = 2a.", {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}}))
    add("GEO-contradictory-length", "contradiction", "REFUSE_GEOMETRY", p)
    p, _a = pyramid("ABC", plane="parallel", section_sentence="Mặt phẳng (α) qua M và song song với (SBC) cắt SB, SC lần lượt tại N, P.")
    p["derived_sections"][0]["parallel_plane"] = ["S", "B", "C"]
    add("GEO-parallel-to-cut-edges", "degenerate", "REFUSE_GEOMETRY", p, note="(α) ∥ (SBC) is parallel to SB and SC")
    p, a = pyramid("ABCD", stated=[("SB", "N"), ("SC", "P"), ("SD", "Q")], declared=[("S", "A"), ("S", "C"), ("S", "B"), ("S", "D")])
    add("GEO-declared-boundary-crossed", "declared_boundary", "REFUSE_GEOMETRY", p, note="crossed cyclic order")
    p, a = pyramid("ABCD", stated=[("SB", "N"), ("SC", "P"), ("SD", "Q")], declared=[("S", "B"), ("S", "C"), ("S", "D")])
    add("GEO-declared-boundary-partial", "declared_boundary", "REFUSE_GEOMETRY", p, note="M on SA missing from the boundary")
    p, a = pyramid("ABCD", stated=[("SB", "N"), ("SC", "P"), ("SD", "Q")], declared=[("S", "D"), ("S", "C"), ("S", "B"), ("S", "A")],
                   residual=True)
    add("GEO-declared-boundary-reversed", "declared_boundary", "SERVE", p, a, note="reversed and rotated cycle: the same polygon")

    # kernel / capability
    p, _a = pyramid("ABC")
    p["derived_sections"][0].update(plane_kind="plane_equation", equation_coeffs=["0", "0", "1", "-1"])
    p["derived_sections"][0].pop("parallel_plane")
    add("KER-plane-equation", "unsupported_plane_kind", "REFUSE_KERNEL", p)
    p, _a = pyramid("ABC", plane="parallel", stated=[("SA", None), ("AB", None), ("AC", None)],
                    section_sentence="Mặt phẳng (α) qua M và song song với (SBC) cắt SA, AB, AC.", ratio=False)
    p["derived_sections"][0]["parallel_plane"] = ["S", "B", "C"]
    add("KER-section-on-base-edges", "unsupported_section_shape", "REFUSE_KERNEL",
        construction_only(p, "Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp đỉnh S cắt bởi (α)."),
        note="geometry is valid, but a derived pyramid with apex S over a section cutting base edges is not in scope")
    return out


def main(out: Path) -> None:
    body = {"classification": CLASSIFICATION, "lock_rule": "expectations are never edited after the lock commit",
            "cases": cases()}
    raw = json.dumps(body, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    out.write_text(raw, encoding="utf-8", newline="\n")
    print(len(body["cases"]), hashlib.sha256(raw.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main(Path(sys.argv[1]))
