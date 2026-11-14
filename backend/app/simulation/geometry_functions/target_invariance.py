# -*- coding: utf-8 -*-
"""Target-invariance proofs for figures with a free SHAPE parameter (`target-invariance-certificate/1`).

Run `target-invariant-regular-solid-semantics`. A figure the source fixes neither in size nor in shape (e.g. a right
triangle whose leg ratio is open) may still fix the asked quantity. For the angle between two planes this module looks
for a SYNTHETIC proof over the verified calls, using a closed table of theorems:

  R1 RIGHT_ANGLE            right_angle(V; X, Y)                         ⇒ VX ⊥ VY
  R1b PERPENDICULAR_LINES   perpendicular_lines(a, b)                    ⇒ a ⊥ b
  R2 PERP_PLANE_TO_LINE     PQ ⊥ Π, both ends of m lie in Π, m ≠ PQ       ⇒ PQ ⊥ m
  R3 PERP_TWO_LINES         m ⊥ a, m ⊥ b, a ≠ b share exactly one point   ⇒ m ⊥ plane(a ∪ b)
  R5 PLANE_ANGLE            X ∈ ℓ = P1 ∩ P2 (two shared labels), XU ⊂ P1 with XU ⊥ ℓ, XV ⊂ P2 with XV ⊥ ℓ, U, V ∉ ℓ
                            ⇒ ∠(P1, P2) = ∠(XU, XV)          (the angle between planes, in [0°, 90°])
  R6 TRIANGLE_SHAPE_FIXED   triangle XUV with a right angle at one vertex and its two legs equal (a source
                            `equal_length`), or a regular triangle   ⇒ its angles are fixed

Conclusion: the asked angle equals an angle of triangle XUV, whose shape the facts on its three vertices alone fix — so
it takes ONE value on every configuration of the source, whatever the free parameters (non-degeneracy: distinct labels,
U, V off ℓ, which the cited facts imply). `verify_target_invariance_certificate` re-checks every step against the
calls independently of the search. Search is bounded (`MAX_DERIVED`); beyond it: `PROOF_SEARCH_BUDGET_EXCEEDED`.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

TARGET_INVARIANCE_VERSION = "target-invariance-certificate/1"
MAX_DERIVED = 256
RULES = ("RIGHT_ANGLE", "PERPENDICULAR_LINES", "PERP_PLANE_TO_LINE", "PERP_TWO_LINES", "PLANE_ANGLE", "TRIANGLE_SHAPE_FIXED")


def _ln(a: Iterable[str]) -> tuple[str, str]:
    a = list(a)
    return tuple(sorted(a))  # type: ignore[return-value]


def _args(c: Any) -> dict:
    return c.args.model_dump() if hasattr(c.args, "model_dump") else dict(c.args)


def _facts(calls) -> dict[str, Any]:
    """Closed reading of the calls the proof may cite (ids → typed premises)."""
    f = {"right": [], "perp": [], "lineplane": [], "equal": [], "regular": [], "base": {}}
    for c in calls:
        a = _args(c)
        if c.fn == "right_angle":
            f["right"].append((c.id, a["vertex"], tuple(a["rays"])))
        elif c.fn == "perpendicular_lines":
            f["perp"].append((c.id, _ln(a["line1"]), _ln(a["line2"])))
        elif c.fn == "perpendicular_line_plane":
            f["lineplane"].append((c.id, _ln(a["line"]), frozenset(a["plane"])))
        elif c.fn == "equal_length":
            f["equal"].append((c.id, _ln(a["segment_a"]), _ln(a["segment_b"])))
        elif c.fn == "regular_polygon" and len(a["vertices"]) == 3:
            f["regular"].append((c.id, frozenset(a["vertices"])))
        elif c.fn in ("pyramid", "regular_pyramid"):
            f["base"][c.id] = frozenset(a["base"])
    return f


def _planes(facts, goal_planes) -> list[frozenset]:
    """Planes a line may be shown to lie in: the goal planes, the planes of ⊥ facts, solid bases."""
    out = {frozenset(p) for p in goal_planes} | {p for _i, _l, p in facts["lineplane"]} | set(facts["base"].values())
    return [p for p in out if len(p) >= 3]


def prove_plane_angle(calls, goal_id: str, plane1, plane2) -> dict | None:
    """A certificate that ∠(plane1, plane2) is fixed by a triangle of fixed shape, or None. Pure search."""
    facts = _facts(calls)
    ell = frozenset(plane1) & frozenset(plane2)
    if len(ell) != 2 or frozenset(plane1) == frozenset(plane2):
        return None
    steps: list[dict] = []
    perp: dict[frozenset, int] = {}          # unordered pair of lines → step index
    perp_plane: dict[tuple, int] = {}        # (line, plane) → step index

    def add(rule, premises, concl):
        if len(steps) >= MAX_DERIVED:
            raise _Budget()
        steps.append({"id": f"t{len(steps) + 1}", "rule": rule, "premises": premises, "conclusion": concl})
        return len(steps) - 1

    def add_perp(a, b, rule, premises):
        k = frozenset((a, b))
        if a != b and k not in perp:
            perp[k] = add(rule, premises, {"perpendicular": [list(a), list(b)]})
            return True
        return False

    try:
        for cid, v, (x, y) in facts["right"]:
            add_perp(_ln((v, x)), _ln((v, y)), "RIGHT_ANGLE", [cid])
        for cid, a, b in facts["perp"]:
            add_perp(a, b, "PERPENDICULAR_LINES", [cid])
        for cid, l, p in facts["lineplane"]:
            perp_plane[(l, p)] = add("SOURCE_LINE_PERP_PLANE", [cid], {"line_perp_plane": [list(l), sorted(p)]})
        planes = _planes(facts, (plane1, plane2))
        changed = True
        while changed:
            changed = False
            for (l, p), si in list(perp_plane.items()):              # R2
                for m in combinations(sorted(p), 2):
                    m = _ln(m)
                    if m != l and add_perp(l, m, "PERP_PLANE_TO_LINE", [steps[si]["id"]]):
                        changed = True
            lines = {x for k in perp for x in k}
            for m in lines:                                          # R3
                partners = [x for x in lines if frozenset((m, x)) in perp]
                for a, b in combinations(partners, 2):
                    shared = set(a) & set(b)
                    if len(shared) != 1 or m in (a, b):
                        continue
                    span = frozenset(a) | frozenset(b)
                    for p in planes:
                        if span <= p and len(span) == 3 and (m, p) not in perp_plane and not (set(m) <= p):
                            perp_plane[(m, p)] = add("PERP_TWO_LINES", [steps[perp[frozenset((m, a))]]["id"],
                                                                         steps[perp[frozenset((m, b))]]["id"]],
                                                     {"line_perp_plane": [list(m), sorted(p)]})
                            changed = True
                    # the plane spanned by a ∪ b itself (e.g. (SAB)), when it is a 3-label plane
                    if len(span) == 3 and (m, span) not in perp_plane and not (set(m) <= span):
                        perp_plane[(m, span)] = add("PERP_TWO_LINES", [steps[perp[frozenset((m, a))]]["id"],
                                                                        steps[perp[frozenset((m, b))]]["id"]],
                                                    {"line_perp_plane": [list(m), sorted(span)]})
                        planes.append(span)
                        changed = True
    except _Budget:
        return {"status": "PROOF_SEARCH_BUDGET_EXCEEDED", "derived": len(steps)}
    lt = _ln(ell)
    for X in sorted(ell):
        for U in sorted(frozenset(plane1) - ell):
            for V in sorted(frozenset(plane2) - ell):
                u, v = _ln((X, U)), _ln((X, V))
                if frozenset((u, lt)) not in perp or frozenset((v, lt)) not in perp:
                    continue
                shape = _shape_fixed(facts, perp, steps, X, U, V)
                if shape is None:
                    continue
                pa = add("PLANE_ANGLE", [steps[perp[frozenset((u, lt))]]["id"], steps[perp[frozenset((v, lt))]]["id"]],
                         {"angle_of_planes": [sorted(plane1), sorted(plane2)], "equals_angle": [X, U, V],
                          "intersection": list(lt)})
                sh = add("TRIANGLE_SHAPE_FIXED", shape["premises"], {"triangle": [X, U, V], "by": shape["by"]})
                used = _closure(steps, [steps[pa]["id"], steps[sh]["id"]])
                return {"schema_version": TARGET_INVARIANCE_VERSION, "status": "PROVEN", "goal_id": goal_id,
                        "certification_level": "MATHEMATICALLY_PROVEN",
                        "claim": f"for every configuration satisfying the cited facts, ∠({''.join(sorted(plane1))}, "
                                 f"{''.join(sorted(plane2))}) = ∠({U}{X}{V}) of a triangle whose shape the facts fix",
                        "free_parameters": "every parameter not constrained by the cited facts (the figure need not be unique)",
                        "non_degeneracy": ["the two planes share exactly the line " + "".join(lt),
                                           f"{U}, {V} lie off {''.join(lt)} (distinct labels of the planes)",
                                           f"triangle {X}{U}{V} has three distinct vertices"],
                        "steps": [s for s in steps if s["id"] in used], "rules": list(RULES)}
    return None


def _shape_fixed(facts, perp, steps, X, U, V):
    tri = {X, U, V}
    for cid, p in facts["regular"]:
        if p == tri:
            return {"by": "REGULAR_TRIANGLE", "premises": [cid]}
    for apex in (X, U, V):
        others = sorted(tri - {apex})
        l1, l2 = _ln((apex, others[0])), _ln((apex, others[1]))
        if frozenset((l1, l2)) not in perp:
            continue
        for cid, a, b in facts["equal"]:
            if {a, b} == {l1, l2}:
                return {"by": f"RIGHT_ISOSCELES_AT_{apex}", "premises": [steps[perp[frozenset((l1, l2))]]["id"], cid]}
    return None


def _closure(steps, roots):
    by = {s["id"]: s for s in steps}
    seen, stack = set(), list(roots)
    while stack:
        x = stack.pop()
        if x in by and x not in seen:
            seen.add(x)
            stack += by[x]["premises"]
    return seen


class _Budget(Exception):
    pass


# ── independent verifier: re-checks each step against the calls, never searches ─────────────────────────────────────
def verify_target_invariance_certificate(cert: dict, calls) -> dict:
    """{"verified": bool, "failed_step": id | None, "reason": str}. Each step's premises must be calls of the right kind
    or EARLIER steps, and its conclusion must be exactly what its rule yields from them."""
    def bad(sid, why):
        return {"verified": False, "failed_step": sid, "reason": why}
    if not isinstance(cert, dict) or cert.get("schema_version") != TARGET_INVARIANCE_VERSION or cert.get("status") != "PROVEN":
        return bad(None, "not a proven target-invariance certificate")
    byid = {c.id: c for c in calls}
    seen: dict[str, dict] = {}
    for s in cert.get("steps") or ():
        rule, prem, concl = s.get("rule"), s.get("premises") or [], s.get("conclusion") or {}
        if rule not in RULES + ("SOURCE_LINE_PERP_PLANE",):
            return bad(s.get("id"), f"unknown rule {rule!r}")
        def perp_of(x):
            if x in seen and "perpendicular" in seen[x]:
                return frozenset(_ln(l) for l in seen[x]["perpendicular"])
            return None
        if rule == "RIGHT_ANGLE":
            c = byid.get(prem[0]) if len(prem) == 1 else None
            if c is None or c.fn != "right_angle":
                return bad(s["id"], "premise is not a right_angle call")
            a = _args(c)
            want = frozenset((_ln((a["vertex"], a["rays"][0])), _ln((a["vertex"], a["rays"][1]))))
            if frozenset(_ln(l) for l in concl.get("perpendicular", ())) != want:
                return bad(s["id"], "conclusion is not the right angle's two rays")
        elif rule == "PERPENDICULAR_LINES":
            c = byid.get(prem[0]) if len(prem) == 1 else None
            if c is None or c.fn != "perpendicular_lines":
                return bad(s["id"], "premise is not a perpendicular_lines call")
            a = _args(c)
            if frozenset(_ln(l) for l in concl.get("perpendicular", ())) != frozenset((_ln(a["line1"]), _ln(a["line2"]))):
                return bad(s["id"], "conclusion differs from the call")
        elif rule == "SOURCE_LINE_PERP_PLANE":
            c = byid.get(prem[0]) if len(prem) == 1 else None
            if c is None or c.fn != "perpendicular_line_plane":
                return bad(s["id"], "premise is not a perpendicular_line_plane call")
            a = _args(c)
            l, p = concl.get("line_perp_plane", [None, None])
            if _ln(l) != _ln(a["line"]) or frozenset(p) != frozenset(a["plane"]):
                return bad(s["id"], "conclusion differs from the call")
        elif rule == "PERP_PLANE_TO_LINE":
            src = seen.get(prem[0]) if len(prem) == 1 else None
            if not src or "line_perp_plane" not in src:
                return bad(s["id"], "premise is not an earlier line ⊥ plane")
            l, p = src["line_perp_plane"]
            pair = [_ln(x) for x in concl.get("perpendicular", ())]
            if len(pair) != 2 or _ln(l) not in pair:
                return bad(s["id"], "conclusion does not involve the perpendicular line")
            m = pair[1] if pair[0] == _ln(l) else pair[0]
            if not set(m) <= set(p) or m == _ln(l):
                return bad(s["id"], "the other line does not lie in the plane")
        elif rule == "PERP_TWO_LINES":
            ps = [perp_of(x) for x in prem]
            l, p = concl.get("line_perp_plane", [None, None])
            if len(ps) != 2 or None in ps or l is None:
                return bad(s["id"], "premises are not two earlier perpendicularities")
            m = _ln(l)
            if not all(m in q for q in ps):
                return bad(s["id"], "the line is not perpendicular to both")
            a, b = [next(iter(q - {m})) for q in ps]
            if a == b or len(set(a) & set(b)) != 1 or not (set(a) | set(b)) <= set(p) or set(m) <= set(p):
                return bad(s["id"], "the two lines do not meet in one point inside the plane")
        elif rule == "PLANE_ANGLE":
            ps = [perp_of(x) for x in prem]
            p1, p2 = concl.get("angle_of_planes", [None, None])
            X, U, V = concl.get("equals_angle", [None] * 3)
            lt = _ln(concl.get("intersection") or ())
            if len(ps) != 2 or None in ps or p1 is None:
                return bad(s["id"], "premises are not two earlier perpendicularities")
            if frozenset(p1) & frozenset(p2) != frozenset(lt) or len(lt) != 2 or X not in lt:
                return bad(s["id"], "the intersection line is not the planes' common line")
            if U not in p1 or V not in p2 or U in lt or V in lt:
                return bad(s["id"], "the angle's arms do not lie in the planes off their common line")
            if ps[0] != frozenset((_ln((X, U)), lt)) or ps[1] != frozenset((_ln((X, V)), lt)):
                return bad(s["id"], "the arms are not proven perpendicular to the common line")
        elif rule == "TRIANGLE_SHAPE_FIXED":
            X, U, V = concl.get("triangle", [None] * 3)
            by = concl.get("by", "")
            if len({X, U, V}) != 3:
                return bad(s["id"], "degenerate triangle")
            if by == "REGULAR_TRIANGLE":
                c = byid.get(prem[0]) if len(prem) == 1 else None
                if c is None or c.fn != "regular_polygon" or frozenset(_args(c)["vertices"]) != frozenset((X, U, V)):
                    return bad(s["id"], "premise is not this regular triangle")
            elif by.startswith("RIGHT_ISOSCELES_AT_"):
                apex = by.rsplit("_", 1)[1]
                if apex not in (X, U, V) or len(prem) != 2:
                    return bad(s["id"], "malformed right-isosceles step")
                o = sorted({X, U, V} - {apex})
                legs = frozenset((_ln((apex, o[0])), _ln((apex, o[1]))))
                if perp_of(prem[0]) != legs:
                    return bad(s["id"], "the right angle is not between the two legs")
                c = byid.get(prem[1])
                if c is None or c.fn != "equal_length" or frozenset((_ln(_args(c)["segment_a"]), _ln(_args(c)["segment_b"]))) != legs:
                    return bad(s["id"], "the legs are not stated equal")
            else:
                return bad(s["id"], f"unknown shape rule {by!r}")
        for x in prem:
            if x not in byid and x not in seen:
                return bad(s["id"], f"premise {x!r} is neither a call nor an earlier step")
        seen[s["id"]] = concl
    kinds = [s.get("rule") for s in cert.get("steps") or ()]
    if "PLANE_ANGLE" not in kinds or "TRIANGLE_SHAPE_FIXED" not in kinds:
        return bad(None, "the certificate does not conclude")
    pa = next(s for s in cert["steps"] if s["rule"] == "PLANE_ANGLE")["conclusion"]
    sh = next(s for s in cert["steps"] if s["rule"] == "TRIANGLE_SHAPE_FIXED")["conclusion"]
    if frozenset(pa["equals_angle"]) != frozenset(sh["triangle"]):
        return bad(None, "the fixed triangle is not the triangle of the plane angle")
    return {"verified": True, "failed_step": None, "reason": "every step re-derived from the calls"}
