# -*- coding: utf-8 -*-
"""Target-invariance proofs for figures with a free SHAPE parameter (`target-invariance-certificate/2`).

A figure the source fixes neither in size nor in shape may still fix the asked ANGLE. This module searches a bounded
SYNTHETIC proof over the verified calls and a separate verifier re-checks every step.

DOMAIN (soundness): one pyramid (`pyramid` / `regular_pyramid` call) and only ITS vertices. For a pyramid with a convex
base every claim below holds on EVERY configuration: two distinct vertices span a line; three distinct vertices are never
collinear; a label set is a plane iff it has three labels or lies in the base (canonical plane of base labels = the whole
base); two planes with different canonical sets are distinct. Anything else (prisms, derived points) is out of domain
and the caller refuses — non-degeneracy is never assumed from one drawn figure.

RULES (closed):
  RIGHT_ANGLE              right_angle(V; X, Y)                              ⇒ VX ⊥ VY
  PERPENDICULAR_LINES      perpendicular_lines(a, b)                         ⇒ a ⊥ b
  SOURCE_LINE_PERP_PLANE   perpendicular_line_plane(l, Π)                    ⇒ l ⊥ Π
  PERP_PLANE_TO_LINE       l ⊥ Π, m ⊂ Π, m ≠ l                               ⇒ l ⊥ m
  PERP_TWO_LINES           m ⊥ a, m ⊥ b, a ≠ b meet in one vertex, m ⊄ Π(a,b) ⇒ m ⊥ Π(a, b)
  TRIANGLE_SHAPE_FIXED     triangle XUV: regular, or right at W with a known ratio of its legs (equal_length /
                           segment_ratio), or right at X                     ⇒ cos²∠X is one number
  PLANE_ANGLE              ℓ = P ∩ Q (two shared vertices), X ∈ ℓ, XU ⊂ P, XV ⊂ Q, XU ⊥ ℓ, XV ⊥ ℓ
                                                                             ⇒ ∠(P, Q) = ∠(XU, XV) ∈ [0°, 90°]
  PERP_PLANES              d ⊂ P, d ⊥ Q                                      ⇒ ∠(P, Q) = 90°
  LINE_PLANE_ANGLE         X ∈ Π, Y ∉ Π, H ∈ Π, H ≠ X, YH ⊥ Π               ⇒ ∠(XY, Π) = ∠(XY, XH) = ∠YXH
  LINE_PERP_PLANE_ANGLE    l ⊥ Π                                             ⇒ ∠(l, Π) = 90°
  LINE_ANGLE               a = XU, b = XV (one common vertex)                ⇒ ∠(a, b) = ∠(XU, XV) ∈ [0°, 90°]
  LINES_PERPENDICULAR      a ⊥ b (also for skew lines: of directions)        ⇒ ∠(a, b) = 90°

ANGLES are structured: `witness = {vertex, ray_1: [vertex, U], ray_2: [vertex, V], domain}` — never a bare triple (the
/1 triple put the vertex FIRST, so ["B","S","A"] read as ∠BSA; run `proof-soundness-generalized-angle-invariance`).
All angles are unoriented angles of LINES in [0°, 90°]; the certificate proves `cos_sq`, which is the same for an angle
and its supplement, and the engine's signed-cosine construction is bound separately (`_thu_bat_bien_muc_tieu`).
Oriented / dihedral angles are out of scope.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Any, Iterable

TARGET_INVARIANCE_VERSION = "target-invariance-certificate/2"
MAX_DERIVED = 256
ANGLE_DOMAIN = "UNORIENTED_LINE_ANGLE_0_90"
DERIVATION_RULES = ("RIGHT_ANGLE", "PERPENDICULAR_LINES", "SOURCE_LINE_PERP_PLANE", "PERP_PLANE_TO_LINE", "PERP_TWO_LINES")
GOAL_RULES = ("PLANE_ANGLE", "PERP_PLANES", "LINE_PLANE_ANGLE", "LINE_PERP_PLANE_ANGLE", "LINE_ANGLE", "LINES_PERPENDICULAR")
RULES = (*DERIVATION_RULES, "TRIANGLE_SHAPE_FIXED", *GOAL_RULES)
GOAL_FUNCTIONS = ("ask_angle_plane_plane", "ask_angle_line_plane", "ask_angle_lines")


def _ln(a: Iterable[str]) -> tuple[str, str]:
    return tuple(sorted(a))  # type: ignore[return-value]


def _args(c: Any) -> dict:
    return c.args.model_dump() if hasattr(c.args, "model_dump") else dict(c.args)


class _Budget(Exception):
    pass


class _Domain:
    """The pyramid the proof speaks about (one solid call, its vertices)."""

    def __init__(self, calls) -> None:
        solids = [c for c in calls if c.fn in ("pyramid", "regular_pyramid", "prism", "curved_solid")]
        self.ok = len(solids) == 1 and solids[0].fn in ("pyramid", "regular_pyramid")
        self.call_id = solids[0].id if self.ok else None
        a = _args(solids[0]) if self.ok else {}
        self.base = frozenset(a.get("base") or ())
        self.labels = self.base | ({a["apex"]} if self.ok else set())
        self.ok = self.ok and len(self.base) >= 3 and len(self.labels) == len(self.base) + 1

    def line(self, x) -> tuple[str, str] | None:
        x = list(x)
        return _ln(x) if len(x) == 2 and x[0] != x[1] and set(x) <= self.labels else None

    def plane(self, p) -> frozenset | None:
        s = frozenset(p)
        if len(s) < 3 or not s <= self.labels:
            return None
        if s <= self.base:
            return self.base
        return s if len(s) == 3 else None


def _ratio_sq(calls, dom: _Domain) -> dict[tuple, tuple[Fraction, str]]:
    """(segment a, segment b) → ((|a|/|b|)², call id) from equal_length / segment_ratio calls on the solid's vertices."""
    from app.simulation.geometry_functions.registry import doc_so
    out: dict[tuple, tuple[Fraction, str]] = {}
    for c in calls:
        a = _args(c)
        if c.fn not in ("equal_length", "segment_ratio"):
            continue
        sa, sb = dom.line(a["segment_a"]), dom.line(a["segment_b"])
        if sa is None or sb is None or sa == sb:
            continue
        try:
            k2 = Fraction(1) if c.fn == "equal_length" else doc_so(str(a["ratio"]))[0]
        except Exception:  # noqa: BLE001 — an unreadable ratio is simply no fact
            continue
        if k2 > 0:
            out.setdefault((sa, sb), (k2, c.id))
            out.setdefault((sb, sa), (1 / k2, c.id))
    return out


class _Search:
    def __init__(self, calls, dom: _Domain) -> None:
        self.calls, self.dom = calls, dom
        self.steps: list[dict] = []
        self.perp: dict[frozenset, str] = {}
        self.lpp: dict[tuple, str] = {}
        self.ratio = _ratio_sq(calls, dom)
        self.regular = {frozenset(_args(c)["vertices"]): c.id for c in calls
                        if c.fn == "regular_polygon" and len(_args(c)["vertices"]) == 3 and set(_args(c)["vertices"]) <= dom.labels}

    def add(self, rule, premises, concl) -> str:
        if len(self.steps) >= MAX_DERIVED:
            raise _Budget()
        self.steps.append({"id": f"t{len(self.steps) + 1}", "rule": rule, "premises": list(premises), "conclusion": concl})
        return self.steps[-1]["id"]

    def add_perp(self, a, b, rule, premises) -> bool:
        k = frozenset((a, b))
        if a is None or b is None or a == b or k in self.perp:
            return False
        self.perp[k] = self.add(rule, premises, {"perpendicular": [list(a), list(b)]})
        return True

    def saturate(self) -> None:
        d = self.dom
        for c in self.calls:
            a = _args(c)
            if c.fn == "right_angle" and len(set((a["vertex"], *a["rays"]))) == 3:
                self.add_perp(d.line((a["vertex"], a["rays"][0])), d.line((a["vertex"], a["rays"][1])), "RIGHT_ANGLE", [c.id])
            elif c.fn == "perpendicular_lines":
                self.add_perp(d.line(a["line1"]), d.line(a["line2"]), "PERPENDICULAR_LINES", [c.id])
            elif c.fn == "perpendicular_line_plane":
                l, p = d.line(a["line"]), d.plane(a["plane"])
                if l and p and not set(l) <= p and (l, p) not in self.lpp:
                    self.lpp[(l, p)] = self.add("SOURCE_LINE_PERP_PLANE", [c.id], {"line_perp_plane": [list(l), sorted(p)]})
        changed = True
        while changed:
            changed = False
            for (l, p), sid in list(self.lpp.items()):
                for m in combinations(sorted(p), 2):
                    if self.add_perp(l, _ln(m), "PERP_PLANE_TO_LINE", [sid]):
                        changed = True
            lines = sorted({x for k in self.perp for x in k})
            for m in lines:
                partners = [x for x in lines if frozenset((m, x)) in self.perp]
                for a, b in combinations(partners, 2):
                    if len(set(a) & set(b)) != 1:
                        continue
                    p = d.plane(set(a) | set(b))
                    if p is None or set(m) <= p or (m, p) in self.lpp:
                        continue
                    self.lpp[(m, p)] = self.add("PERP_TWO_LINES", [self.perp[frozenset((m, a))], self.perp[frozenset((m, b))]],
                                                {"line_perp_plane": [list(m), sorted(p)]})
                    changed = True

    def shape(self, X, U, V) -> dict | None:
        """A TRIANGLE_SHAPE_FIXED step for cos²∠X of triangle XUV, or None."""
        tri = frozenset((X, U, V))
        if len(tri) != 3:
            return None
        if tri in self.regular:
            return {"premises": [self.regular[tri]], "by": "REGULAR_TRIANGLE", "cos_sq": Fraction(1, 4)}
        for W in (X, U, V):
            o = sorted(tri - {W})
            k = frozenset((_ln((W, o[0])), _ln((W, o[1]))))
            if k not in self.perp:
                continue
            if W == X:
                return {"premises": [self.perp[k]], "by": f"RIGHT_ANGLE_AT_{W}", "cos_sq": Fraction(0)}
            other = next(x for x in o if x != X)
            adj, opp = _ln((W, X)), _ln((W, other))
            if (opp, adj) in self.ratio:
                r2, cid = self.ratio[(opp, adj)]
                return {"premises": [self.perp[k], cid], "by": f"RIGHT_AT_{W}_LEG_RATIO", "cos_sq": 1 / (1 + r2)}
        return None


def _witness(X, U, V) -> dict:
    return {"vertex": X, "ray_1": [X, U], "ray_2": [X, V], "domain": ANGLE_DOMAIN}


def prove_angle_goal(calls, goal) -> dict | None:
    """A `/2` certificate that the angle asked by `goal` (an `ask_angle_*` call) takes ONE value on every configuration of
    the cited facts, None when no proof is found, or `{"status": "PROOF_SEARCH_BUDGET_EXCEEDED"}`."""
    dom = _Domain(calls)
    if not dom.ok or goal.fn not in GOAL_FUNCTIONS:
        return None
    s = _Search(calls, dom)
    try:
        s.saturate()
        final = _prove(s, dom, goal)
    except _Budget:
        return {"status": "PROOF_SEARCH_BUDGET_EXCEEDED", "derived": len(s.steps)}
    if final is None:
        return None
    used = _closure(s.steps, final["step_ids"])
    return {"schema_version": TARGET_INVARIANCE_VERSION, "status": "PROVEN", "goal_id": goal.id,
            "goal": {"function": goal.fn, **{k: v for k, v in _args(goal).items() if v is not None}},
            "certification_level": "MATHEMATICALLY_PROVEN",
            "domain": {"solid_call": dom.call_id, "labels": sorted(dom.labels), "base": sorted(dom.base),
                       "non_degeneracy": "pyramid with a convex base: distinct vertices, no three collinear, apex off the base"},
            "conclusion": {"cos_sq": str(final["cos_sq"]), "angle_domain": "[0°, 90°]", "witness": final.get("witness"),
                           "holds_for": "every configuration satisfying the cited calls (the figure need not be unique)"},
            "steps": [x for x in s.steps if x["id"] in used], "rules": list(RULES)}


def _prove(s: _Search, dom: _Domain, goal) -> dict | None:
    a = _args(goal)
    if goal.fn == "ask_angle_plane_plane":
        p, q = dom.plane(a["plane1"]), dom.plane(a["plane2"])
        if p is None or q is None or p == q:
            return None
        for (l, pl), sid in sorted(s.lpp.items()):
            if (pl == q and set(l) <= p) or (pl == p and set(l) <= q):
                sid2 = s.add("PERP_PLANES", [sid], {"plane_1": sorted(p), "plane_2": sorted(q), "contained_line": list(l),
                                                     "perpendicular_to": sorted(pl), "cos_sq": "0"})
                return {"cos_sq": Fraction(0), "step_ids": [sid2]}
        ell = p & q
        if len(ell) != 2:
            return None
        lt = _ln(ell)
        for X in sorted(ell):
            for U in sorted(p - ell):
                for V in sorted(q - ell):
                    k1, k2 = frozenset((_ln((X, U)), lt)), frozenset((_ln((X, V)), lt))
                    sh = s.shape(X, U, V) if k1 in s.perp and k2 in s.perp else None
                    if sh is None:
                        continue
                    w = _witness(X, U, V)
                    pa = s.add("PLANE_ANGLE", [s.perp[k1], s.perp[k2]],
                               {"plane_1": sorted(p), "plane_2": sorted(q), "intersection_line": list(lt), "witness": w})
                    return _finish(s, sh, w, pa)
        return None
    if goal.fn == "ask_angle_line_plane":
        l, p = dom.line(a["line"]), dom.plane(a["plane"])
        if l is None or p is None or set(l) <= p:
            return None
        if (l, p) in s.lpp:
            sid = s.add("LINE_PERP_PLANE_ANGLE", [s.lpp[(l, p)]], {"line": list(l), "plane": sorted(p), "cos_sq": "0"})
            return {"cos_sq": Fraction(0), "step_ids": [sid]}
        on = [x for x in l if x in p]
        if len(on) != 1:
            return None
        X, Y = on[0], next(x for x in l if x != on[0])
        for H in sorted(p - {X}):
            hy = _ln((Y, H))
            sh = s.shape(X, Y, H) if (hy, p) in s.lpp else None
            if sh is None:
                continue
            w = _witness(X, Y, H)
            st = s.add("LINE_PLANE_ANGLE", [s.lpp[(hy, p)]], {"line": list(l), "plane": sorted(p), "foot": H,
                                                              "projection": [X, H], "witness": w})
            return _finish(s, sh, w, st)
        return None
    l1, l2 = dom.line(a["line1"]), dom.line(a["line2"])
    if l1 is None or l2 is None or l1 == l2:
        return None
    if frozenset((l1, l2)) in s.perp:
        sid = s.add("LINES_PERPENDICULAR", [s.perp[frozenset((l1, l2))]], {"line_1": list(l1), "line_2": list(l2), "cos_sq": "0"})
        return {"cos_sq": Fraction(0), "step_ids": [sid]}
    common = set(l1) & set(l2)
    if len(common) != 1:
        return None                                   # skew, not proven perpendicular: no parallel-transport rule yet
    X = next(iter(common))
    U, V = next(x for x in l1 if x != X), next(x for x in l2 if x != X)
    sh = s.shape(X, U, V)
    if sh is None:
        return None
    w = _witness(X, U, V)
    st = s.add("LINE_ANGLE", [], {"line_1": list(l1), "line_2": list(l2), "witness": w})
    return _finish(s, sh, w, st)


def _finish(s: _Search, sh: dict, w: dict, goal_step: str) -> dict:
    tri = s.add("TRIANGLE_SHAPE_FIXED", sh["premises"], {"triangle": sorted((w["vertex"], w["ray_1"][1], w["ray_2"][1])),
                                                         "angle_at": w["vertex"], "by": sh["by"], "cos_sq": str(sh["cos_sq"])})
    return {"cos_sq": sh["cos_sq"], "witness": w, "step_ids": [goal_step, tri]}


def _closure(steps, roots):
    by = {s["id"]: s for s in steps}
    seen, stack = set(), list(roots)
    while stack:
        x = stack.pop()
        if x in by and x not in seen:
            seen.add(x)
            stack += by[x]["premises"]
    return seen


# ── independent verifier ───────────────────────────────────────────────────────────────────────────────────────────
# Shares with the search only `_ln`, `_args`, `_Domain` (the declared domain) and `_ratio_sq` (reading two call kinds).
# It never calls `_Search` / `_prove`: every step is re-derived here from the calls and EARLIER steps, and the final
# conclusion is recomputed and compared with the asked goal.
def verify_target_invariance_certificate(cert: dict, calls, goal=None) -> dict:
    """{"verified": bool, "failed_step": id | None, "reason": str}. `goal` (the `ask_angle_*` call) is required: a
    certificate proves ONE asked angle and is never accepted for another."""
    def bad(sid, why):
        return {"verified": False, "failed_step": sid, "reason": why}

    if not isinstance(cert, dict) or cert.get("schema_version") != TARGET_INVARIANCE_VERSION or cert.get("status") != "PROVEN":
        return bad(None, "not a proven target-invariance-certificate/2")
    if goal is None or goal.fn not in GOAL_FUNCTIONS or cert.get("goal_id") != goal.id:
        return bad(None, "the certificate is not bound to this asked goal")
    dom = _Domain(calls)
    if not dom.ok:
        return bad(None, "outside the proof domain (one pyramid)")
    byid = {c.id: c for c in calls}
    ratio = _ratio_sq(calls, dom)
    perp: dict[str, frozenset] = {}
    lpp: dict[str, tuple] = {}
    shapes: dict[str, dict] = {}
    finals: list[tuple[str, dict]] = []

    def line(x):
        return dom.line(x) if isinstance(x, (list, tuple)) else None

    def plane(x):
        return dom.plane(x) if isinstance(x, (list, tuple)) else None

    def wit(w, sid):
        if not isinstance(w, dict) or w.get("domain") != ANGLE_DOMAIN:
            return None
        r1, r2 = w.get("ray_1"), w.get("ray_2")
        if line(r1) is None or line(r2) is None or r1[0] != w.get("vertex") or r2[0] != w.get("vertex") or r1[1] == r2[1]:
            return None
        return w["vertex"], r1[1], r2[1]

    for s in cert.get("steps") or ():
        sid, rule, prem, c = s.get("id"), s.get("rule"), list(s.get("premises") or ()), s.get("conclusion") or {}
        if rule not in RULES or not isinstance(sid, str) or sid in perp or sid in lpp or sid in shapes:
            return bad(sid, f"unknown rule or repeated step id ({rule!r})")
        if rule in ("RIGHT_ANGLE", "PERPENDICULAR_LINES"):
            call = byid.get(prem[0]) if len(prem) == 1 else None
            want_fn = "right_angle" if rule == "RIGHT_ANGLE" else "perpendicular_lines"
            if call is None or call.fn != want_fn:
                return bad(sid, f"premise is not a {want_fn} call")
            a = _args(call)
            pair = ((line((a["vertex"], a["rays"][0])), line((a["vertex"], a["rays"][1]))) if rule == "RIGHT_ANGLE"
                    else (line(a["line1"]), line(a["line2"])))
            got = [line(x) for x in c.get("perpendicular") or ()]
            if None in pair or pair[0] == pair[1] or len(got) != 2 or frozenset(got) != frozenset(pair):
                return bad(sid, "conclusion is not the perpendicularity the call states")
            perp[sid] = frozenset(pair)
        elif rule == "SOURCE_LINE_PERP_PLANE":
            call = byid.get(prem[0]) if len(prem) == 1 else None
            if call is None or call.fn != "perpendicular_line_plane":
                return bad(sid, "premise is not a perpendicular_line_plane call")
            a = _args(call)
            l, p = (c.get("line_perp_plane") or [None, None])[:2]
            if line(l) is None or plane(p) is None or line(l) != line(a["line"]) or plane(p) != plane(a["plane"]) or set(line(l)) <= plane(p):
                return bad(sid, "conclusion differs from the call or is degenerate")
            lpp[sid] = (line(l), plane(p))
        elif rule == "PERP_PLANE_TO_LINE":
            src = lpp.get(prem[0]) if len(prem) == 1 else None
            got = [line(x) for x in c.get("perpendicular") or ()]
            if src is None or len(got) != 2 or None in got or src[0] not in got:
                return bad(sid, "premise is not an earlier line ⊥ plane containing this line")
            m = got[1] if got[0] == src[0] else got[0]
            if m == src[0] or not set(m) <= src[1]:
                return bad(sid, "the other line does not lie in the plane")
            perp[sid] = frozenset(got)
        elif rule == "PERP_TWO_LINES":
            ps = [perp.get(x) for x in prem]
            l, p = (c.get("line_perp_plane") or [None, None])[:2]
            m, pl = line(l), plane(p)
            if len(ps) != 2 or None in ps or m is None or pl is None or not all(m in q for q in ps):
                return bad(sid, "premises are not two earlier perpendicularities of this line")
            a, b = [next(iter(q - {m})) for q in ps]
            if a == b or len(set(a) & set(b)) != 1 or dom.plane(set(a) | set(b)) != pl or set(m) <= pl:
                return bad(sid, "the two lines do not span exactly this plane, or the line lies in it")
            lpp[sid] = (m, pl)
        elif rule == "TRIANGLE_SHAPE_FIXED":
            tri, X, by = c.get("triangle"), c.get("angle_at"), str(c.get("by") or "")
            if not isinstance(tri, list) or len(set(tri)) != 3 or not set(tri) <= dom.labels or X not in tri:
                return bad(sid, "not a triangle of three distinct vertices with its angle vertex")
            if by == "REGULAR_TRIANGLE":
                call = byid.get(prem[0]) if len(prem) == 1 else None
                if call is None or call.fn != "regular_polygon" or frozenset(_args(call)["vertices"]) != frozenset(tri):
                    return bad(sid, "premise is not this regular triangle")
                val = Fraction(1, 4)
            else:
                W = (by[len("RIGHT_ANGLE_AT_"):] if by.startswith("RIGHT_ANGLE_AT_")
                     else by[len("RIGHT_AT_"):-len("_LEG_RATIO")] if by.startswith("RIGHT_AT_") and by.endswith("_LEG_RATIO") else None)
                if W not in tri or not prem:
                    return bad(sid, "malformed right-triangle shape step")
                o = sorted(set(tri) - {W})
                if perp.get(prem[0]) != frozenset((_ln((W, o[0])), _ln((W, o[1])))):
                    return bad(sid, "the right angle is not proven between the two legs at that vertex")
                if by == f"RIGHT_ANGLE_AT_{W}" and W == X and len(prem) == 1:
                    val = Fraction(0)
                elif by == f"RIGHT_AT_{W}_LEG_RATIO" and W != X and len(prem) == 2:
                    other = next(x for x in o if x != X)
                    r = ratio.get((_ln((W, other)), _ln((W, X))))
                    if r is None or r[1] != prem[1]:
                        return bad(sid, "the legs' ratio is not stated by that call")
                    val = 1 / (1 + r[0])
                else:
                    return bad(sid, "shape rule does not match the angle vertex")
            if str(val) != c.get("cos_sq"):
                return bad(sid, "cos² of the fixed angle differs from what the premises give")
            shapes[sid] = {"tri": frozenset(tri), "at": X, "cos_sq": val}
        elif rule == "PLANE_ANGLE":
            p, q, lt, w = plane(c.get("plane_1")), plane(c.get("plane_2")), line(c.get("intersection_line")), wit(c.get("witness"), sid)
            if p is None or q is None or p == q or lt is None or w is None or p & q != frozenset(lt):
                return bad(sid, "planes, their common line or the angle witness are malformed")
            X, U, V = w
            if X not in lt or U not in p - set(lt) or V not in q - set(lt):
                return bad(sid, "the witness vertex is not on the common line, or a ray does not lie in its plane off that line")
            if [perp.get(x) for x in prem] != [frozenset((_ln((X, U)), lt)), frozenset((_ln((X, V)), lt))]:
                return bad(sid, "the rays are not proven perpendicular to the common line")
            finals.append((rule, {"planes": frozenset((p, q)), "witness": w}))
        elif rule == "PERP_PLANES":
            p, q, d, t = plane(c.get("plane_1")), plane(c.get("plane_2")), line(c.get("contained_line")), plane(c.get("perpendicular_to"))
            src = lpp.get(prem[0]) if len(prem) == 1 else None
            if None in (p, q, d, t) or p == q or src != (d, t) or t not in (p, q) or not set(d) <= (q if t == p else p) or c.get("cos_sq") != "0":
                return bad(sid, "no line of one plane is proven perpendicular to the other plane")
            finals.append((rule, {"planes": frozenset((p, q)), "cos_sq": Fraction(0)}))
        elif rule == "LINE_PLANE_ANGLE":
            l, p, H, w = line(c.get("line")), plane(c.get("plane")), c.get("foot"), wit(c.get("witness"), sid)
            src = lpp.get(prem[0]) if len(prem) == 1 else None
            if l is None or p is None or w is None or src is None:
                return bad(sid, "line, plane, witness or premise malformed")
            X, Y, Hw = w
            if set(l) != {X, Y} or X not in p or Y in p or Hw != H or H not in p or H == X or src != (_ln((Y, H)), p) \
                    or c.get("projection") != [X, H]:
                return bad(sid, "the witness is not the line with its orthogonal projection on the plane")
            finals.append((rule, {"line": l, "plane": p, "witness": w}))
        elif rule == "LINE_PERP_PLANE_ANGLE":
            l, p = line(c.get("line")), plane(c.get("plane"))
            if l is None or p is None or (lpp.get(prem[0]) if len(prem) == 1 else None) != (l, p) or c.get("cos_sq") != "0":
                return bad(sid, "the line is not proven perpendicular to the plane")
            finals.append((rule, {"line": l, "plane": p, "cos_sq": Fraction(0)}))
        elif rule == "LINE_ANGLE":
            l1, l2, w = line(c.get("line_1")), line(c.get("line_2")), wit(c.get("witness"), sid)
            if l1 is None or l2 is None or l1 == l2 or w is None or prem:
                return bad(sid, "lines or witness malformed")
            X, U, V = w
            if _ln((X, U)) != l1 or _ln((X, V)) != l2:
                return bad(sid, "the rays are not the two asked lines from their common vertex")
            finals.append((rule, {"lines": frozenset((l1, l2)), "witness": w}))
        elif rule == "LINES_PERPENDICULAR":
            l1, l2 = line(c.get("line_1")), line(c.get("line_2"))
            if l1 is None or l2 is None or (perp.get(prem[0]) if len(prem) == 1 else None) != frozenset((l1, l2)) or c.get("cos_sq") != "0":
                return bad(sid, "the lines are not proven perpendicular")
            finals.append((rule, {"lines": frozenset((l1, l2)), "cos_sq": Fraction(0)}))
        for x in prem:
            if x not in byid and x not in perp and x not in lpp and x not in shapes:
                return bad(sid, f"premise {x!r} is neither a call nor an earlier step")
    if len(finals) != 1:
        return bad(None, "the certificate must conclude with exactly one goal step")
    rule, f = finals[0]
    a = _args(goal)
    if goal.fn == "ask_angle_plane_plane":
        ok = rule in ("PLANE_ANGLE", "PERP_PLANES") and f["planes"] == frozenset((dom.plane(a["plane1"]), dom.plane(a["plane2"])))
    elif goal.fn == "ask_angle_line_plane":
        ok = rule in ("LINE_PLANE_ANGLE", "LINE_PERP_PLANE_ANGLE") and f["line"] == dom.line(a["line"]) and f["plane"] == dom.plane(a["plane"])
    else:
        ok = rule in ("LINE_ANGLE", "LINES_PERPENDICULAR") and f["lines"] == frozenset((dom.line(a["line1"]), dom.line(a["line2"])))
    if not ok:
        return bad(None, "the goal step does not prove the asked angle (other planes / lines)")
    concl = cert.get("conclusion") or {}
    if "witness" in f:
        X, U, V = f["witness"]
        sh = [x for x in shapes.values() if x["tri"] == frozenset((X, U, V)) and x["at"] == X]
        if len(sh) != 1 or len(shapes) != 1:
            return bad(None, "no shape step fixes the angle AT THE WITNESS VERTEX of the witness triangle")
        value = sh[0]["cos_sq"]
        if concl.get("witness") != {"vertex": X, "ray_1": [X, U], "ray_2": [X, V], "domain": ANGLE_DOMAIN}:
            return bad(None, "the stated witness is not the one the goal step proves")
    else:
        value = f["cos_sq"]
        if shapes or concl.get("witness") is not None:
            return bad(None, "a perpendicularity conclusion carries no triangle or witness")
    if concl.get("cos_sq") != str(value):
        return bad(None, "the stated cos² is not the proven one")
    return {"verified": True, "failed_step": None, "reason": "every step re-derived from the calls; goal and value bound",
            "cos_sq": str(value)}
