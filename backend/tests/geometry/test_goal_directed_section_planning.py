"""Goal-directed construction planning (run `goal-directed-section-planning`): the section of a convex solid with the plane
through a verified point M parallel to a named plane (Q). Route B only (the planner chooses the constructions), no provider.

Planner: Section(solid, Plane(M ∥ Q)) → translate_point ×2 (auxiliary, IR's own expression) → section(solid, M, X₁, X₂).
Engine: places M, X₁, X₂ in dependency order, verifies the plane (through M, parallel to Q, not Q, not a face), executes.
Oracle: an independent brute-force section in this file — canonical Euclidean coordinates chosen here, every edge cut by
the plane, vertices ordered by exact angle comparison, area² from cross products. It shares no code with the engine, kernel
or `section.py`, and the engine builds its own layout in its own metric, so agreement is not self-confirmation.
"""
from fractions import Fraction as F
from functools import cmp_to_key

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions import registry as RG
from app.simulation.geometry_functions.planner import lap_ke_hoach
from tests.geometry import hybrid_compiler_benchmark as HB


# ── independent oracle ─────────────────────────────────────────────────────────────────────────────────────────────────
def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def oracle_section_area_sq(points: dict, edges: list[tuple[str, str]], through: tuple, normal: tuple) -> F:
    d = _dot(normal, through)
    cut = set()
    for a, b in edges:
        pa, pb = points[a], points[b]
        sa, sb = _dot(normal, pa) - d, _dot(normal, pb) - d
        if sa == 0:
            cut.add(pa)
        if sb == 0:
            cut.add(pb)
        if sa * sb < 0:
            t = F(sa) / (sa - sb)
            cut.add(tuple(x + t * (y - x) for x, y in zip(pa, pb)))
    pts = list(cut)
    assert len(pts) >= 3, "oracle: the plane does not cut a polygon"
    c = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
    u = _sub(pts[0], c)
    v = _cross(normal, u)

    def half(p):                                   # exact angular order around c in the basis (u, v)
        x, y = _dot(_sub(p, c), u), _dot(_sub(p, c), v)
        return (0 if y > 0 or (y == 0 and x > 0) else 1), x, y

    def cmp(p, q):
        hp, xp, yp = half(p)
        hq, xq, yq = half(q)
        if hp != hq:
            return hp - hq
        cr = xp * yq - yp * xq
        return -1 if cr > 0 else 1 if cr < 0 else 0

    ring = sorted(pts, key=cmp_to_key(cmp))
    s = (0, 0, 0)
    for p, q in zip(ring, ring[1:] + ring[:1]):
        s = tuple(x + y for x, y in zip(s, _cross(_sub(p, c), _sub(q, c))))
    return F(_dot(s, s)) / 4


PYR = {"S": (0, 0, 3), "A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0)}
PYR_EDGES = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("S", "A"), ("S", "B"), ("S", "C"), ("S", "D")]


def _mid3(p, a, b):
    return tuple(F(x + y, 2) for x, y in zip(p[a], p[b]))


def _normal(p, q):
    return _cross(_sub(p[q[1]], p[q[0]]), _sub(p[q[2]], p[q[0]]))


# ── problems ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def _pyramid_problem(m_seg="SC", ref="ABCD", names="SABCD", name_plane="P", inline=False, relation="parallel",
                     construct=True, ask=True):
    text, facts = HB._square(names)
    s = names[0]
    ren = dict(zip("SABCD", names))
    seg = "".join(ren[x] for x in m_seg)
    refn = "".join(ren[x] for x in ref)
    mid = HB._mid("fm", "M", seg[0], seg[1])
    sol = f"{s}.{names[1:]}"
    rel_word = "song song" if relation == "parallel" else "vuông góc"
    if inline:
        define = None
        ask_q = f"Tính diện tích thiết diện của hình chóp {sol} với mặt phẳng đi qua M và {rel_word} với ({refn})."
        build_q = f"Xác định thiết diện của hình chóp {sol} với mặt phẳng đi qua M và {rel_word} với ({refn})."
    else:
        define = f"Dựng mặt phẳng ({name_plane}) đi qua M và {rel_word} với ({refn})."
        ask_q = f"Tính diện tích thiết diện của hình chóp {sol} với ({name_plane})."
        build_q = f"Xác định thiết diện của hình chóp {sol} với ({name_plane})."
    sentences = text + mid["quotes"] + ([define] if define else []) + ([build_q] if construct else []) + ([ask_q] if ask else [])
    common = {"solid": sol, "point": "M", "points_b": list(refn), "plane_relation": relation}
    extra = []
    if construct:
        extra.append({"id": "sec", "kind": "section", "role": "premise", "quotes": [x for x in (define, build_q) if x], **common})
    if ask:
        extra.append({"id": "q", "kind": "question", "role": "question", "quantity": "area",
                      "quotes": [x for x in (define, ask_q) if x], **common})
    return " ".join(sentences), {"facts": facts + [mid] + extra}


def _prism_problem(m_seg="AA'", ref="ABC"):
    q = ["Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.", "AA' = 3."]
    facts = [HB._f("f1", "solid", q[0], solid="ABC.A'B'C'", solid_type="prism", right=True),
             HB._f("f2", "polygon_shape", q[0], points=["A", "B", "C"], shape="equilateral_triangle", value="2"),
             HB._f("f3", "length", q[1], points=["A", "A'"], measure="segment", value="3")]
    a, b = (m_seg[0], m_seg[1:]) if m_seg[1] != "'" else (m_seg[:2], m_seg[2:])
    mid = HB._mid("fm", "M", a, b)
    define = f"Dựng mặt phẳng (P) đi qua M và song song với ({ref})."
    ask_q = "Tính diện tích thiết diện của hình lăng trụ ABC.A'B'C' với (P)."
    common = {"solid": "ABC.A'B'C'", "point": "M", "points_b": _labels(ref), "plane_relation": "parallel"}
    extra = [{"id": "q", "kind": "question", "role": "question", "quantity": "area", "quotes": [define, ask_q], **common}]
    return " ".join(q + mid["quotes"] + [define, ask_q]), {"facts": facts + [mid] + extra}


def _labels(s):
    import re
    return re.findall(r"[A-Z][0-9]*'?", s)


def _triangle_area_sq(a2, b2, c2) -> F:
    """Heron in squared form from squared sides — exact, no coordinates (the equilateral base needs √3 in coordinates)."""
    return F(4 * a2 * b2 - (a2 + b2 - c2) ** 2, 16)


def _prism_area_sq_oracle():
    # A plane through M parallel to (ABC) cuts a right prism in a translate of the base: area² of a triangle of side² 4.
    return _triangle_area_sq(4, 4, 4)


# ── tests ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_section_through_midpoint_parallel_to_base_is_planned_built_and_exact():
    text, payload = _pyramid_problem()
    plan = lap_ke_hoach(payload, text)
    fns = [c["fn"] for c in plan.calls]
    assert fns.count("translate_point") == 2                         # one derived plane, shared by the section and the ask
    assert [d["rule"] for d in plan.auxiliary] == [RG.MAT_SONG_SONG]
    step = next(s for s in plan.trace if s.get("step") == "decompose_goal")
    assert step["dependencies"][0] == "VerifiedPoint M" and step["auxiliary"] == plan.auxiliary[0]["labels"]
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    want = oracle_section_area_sq(PYR, PYR_EDGES, _mid3(PYR, "S", "C"), _normal(PYR, "ABC"))
    assert want == 1 and HB.answer_square(r.answers["q"]) == want
    # dependency order in the engine trace: M, then its two translates, then the verified plane, then the section
    order = [(s["step"], s.get("object")) for s in r.trace]
    i_m = order.index(("place_point", "M"))
    xs = plan.auxiliary[0]["labels"]
    i_x = [order.index(("place_point", x)) for x in xs]
    i_p = next(i for i, (st, _o) in enumerate(order) if st == "construct_plane")
    i_s = next(i for i, (st, _o) in enumerate(order) if st == "construct_section")
    assert i_m < min(i_x) and max(i_x) < i_p < i_s
    assert all(s.get("relation_verified") for s in r.trace if s.get("object") in xs)
    assert r.scene3d is not None


@pytest.mark.parametrize("m_seg, ref", [("SC", "ABCD"), ("SA", "ABCD"), ("SC", "SAB"), ("SB", "SAD"), ("SD", "SBC")])
def test_section_area_matches_the_independent_oracle(m_seg, ref):
    text, payload = _pyramid_problem(m_seg=m_seg, ref=ref, construct=False)
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    want = oracle_section_area_sq(PYR, PYR_EDGES, _mid3(PYR, m_seg[0], m_seg[1]), _normal(PYR, ref))
    assert HB.answer_square(r.answers["q"]) == want, (r.answers, want)


def test_relabelling_does_not_change_the_plan_or_the_answer():
    base = run_fact_route(*_pyramid_problem(construct=False))
    other = run_fact_route(*_pyramid_problem(names="TEFGK", construct=False))
    assert base.status == other.status == "SERVED"
    assert HB.answer_square(base.answers["q"]) == HB.answer_square(other.answers["q"])


def test_scaling_scales_the_area_and_keeps_the_topology():
    text, payload = _pyramid_problem(construct=False)
    text = text.replace("cạnh 2", "cạnh 4").replace("SA = 3", "SA = 6")
    for f in payload["facts"]:
        if f.get("value") == "2":
            f["value"] = "4"
        elif f.get("value") == "3":
            f["value"] = "6"
        f["quotes"] = [x.replace("cạnh 2", "cạnh 4").replace("SA = 3", "SA = 6") for x in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 16                    # (area 1)·2² ⇒ area² 16


def test_inline_plane_wording_is_bound_too():
    r = run_fact_route(*_pyramid_problem(inline=True))
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 1


@pytest.mark.parametrize("inline, label", [(False, "(P)"), (True, "(α)")])
def test_derived_plane_is_named_by_the_source_not_by_auxiliary_labels(inline, label):
    text, payload = _pyramid_problem(inline=inline)
    r = run_fact_route(text, payload)
    planes = [o for o in r.scene3d["objects"] if o["type"] == "plane3"]
    aux = lap_ke_hoach(payload, text).auxiliary[0]["labels"]
    assert [p["label"] for p in planes] == [label] and not any(x in planes[0]["label"] for x in aux)


def test_prism_reuses_the_same_rule():
    r = run_fact_route(*_prism_problem())
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == _prism_area_sq_oracle()


# ── fail-closed contract ───────────────────────────────────────────────────────────────────────────────────────────────
def test_plane_through_a_point_perpendicular_to_a_plane_is_not_unique():
    r = run_fact_route(*_pyramid_problem(relation="perpendicular"))
    assert (r.status, r.code) == ("REFUSED", "PLANE_NOT_UNIQUE")


def test_point_on_the_reference_plane_gives_no_new_plane():
    r = run_fact_route(*_pyramid_problem(m_seg="AB"))               # M on (ABCD): the "parallel" plane is (ABCD) itself
    assert (r.status, r.code) == ("REFUSED", "DERIVED_PLANE_IS_REFERENCE")


def test_plane_through_the_apex_parallel_to_the_base_only_touches_a_vertex():
    text, payload = _pyramid_problem(construct=False)
    text = text.replace("Gọi M là trung điểm SC.", "")
    payload["facts"] = [f for f in payload["facts"] if f["id"] != "fm"]
    text = text.replace("đi qua M", "đi qua S")
    for f in payload["facts"]:
        if f["id"] == "q":
            f["point"] = "S"
            f["quotes"] = [x.replace("đi qua M", "đi qua S") for x in f["quotes"]]
    r = run_fact_route(text, payload)
    assert (r.status, r.code) == ("REFUSED", "PLANE_TOUCHES_VERTEX")


def test_boundary_face_is_not_a_cutting_section():
    r = run_fact_route(*_prism_problem(m_seg="A'B'", ref="ABC"))    # M on the top face: the parallel plane IS that face
    assert (r.status, r.code) == ("REFUSED", "SECTION_PLANE_IS_FACE")


@pytest.mark.parametrize("old, new", [
    ("đi qua M và song song với (ABCD)", "đi qua M"),                      # the relation is not in the source
    ("đi qua M và song song với (ABCD)", "đi qua M và song song với (SAB)"),  # another reference plane
    ("Dựng mặt phẳng (P)", "Nếu dựng được mặt phẳng (P)"),                # a condition, not a construction
    # independent review of 926c0bf9, I2: the definition clause must be read to its end — these are contradictory
    ("song song với (ABCD).", "song song với (ABCD) và song song với (SBC)."),
    ("song song với (ABCD).", "song song với hai mặt phẳng (ABCD) và (SBC)."),
    ("song song với (ABCD).", "song song với (ABCD) và song song với SB."),
    ("song song với (ABCD).", "song song với (ABCD), (P) cắt SB tại N."),   # unread continuation: conservative refusal
    # verification of 16ac524a: ";" does not end the definition sentence; a request verb does not license a new condition
    ("song song với (ABCD).", "song song với (ABCD); (P) song song với (SBC)."),
    ("song song với (ABCD).", "song song với (ABCD); (P) vuông góc với SC."),
    ("song song với (ABCD).", "song song với (ABCD) và dựng (P) song song với (SBC)."),
    ("song song với (ABCD).", "song song với (ABCD), tính chất (P) chứa SB."),
])
def test_derived_plane_must_be_bound_to_its_source_clause(old, new):
    text, payload = _pyramid_problem()
    text = text.replace(old, new)
    for f in payload["facts"]:
        f["quotes"] = [x.replace(old, new) for x in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("asked", ["(MAB)", "(SBD)"])
def test_asked_area_must_name_the_derived_plane(asked):
    # review I1: the area asked is of another section; serving the (P) area would be a wrong answer
    text, payload = _pyramid_problem()
    old = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
    new = f"Tính diện tích thiết diện của hình chóp S.ABCD với {asked}."
    text = text.replace(old, new)
    for f in payload["facts"]:
        f["quotes"] = [x.replace(old, new) for x in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("old, new", [
    # "the section" by anaphora after "(P) cắt … theo thiết diện" (served at 926c0bf9; refused by 16ac524a, fixed)
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P).",
     "(P) cắt hình chóp S.ABCD theo thiết diện. Tính diện tích thiết diện đó."),
    # the section request continuing the definition sentence
    ("song song với (ABCD).", "song song với (ABCD), xác định thiết diện của hình chóp S.ABCD với (P)."),
])
def test_bound_wordings_of_the_derived_section_stay_served(old, new):
    text, payload = _pyramid_problem()
    text = text.replace(old, new)
    for f in payload["facts"]:
        f["quotes"] = [x.replace(old, new) for x in f["quotes"]]
        if f["id"] == "q" and "(P) cắt" in new:
            f["quotes"] = [f["quotes"][0], *new.split(". ")[:1], new.split(". ")[1]]
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 1


_DEF = "Dựng mặt phẳng (P) đi qua M và song song với (ABCD)."
_CUT = "(P) cắt hình chóp S.ABCD theo thiết diện."


@pytest.mark.parametrize("between, anaphor_quote", [
    # final re-review C1: "đó/trên" refers to the NEAREST section in the source, here (MAB)/(SBD), not to (P)
    ("Xác định thiết diện của hình chóp S.ABCD với (MAB). ", "Tính diện tích thiết diện đó."),
    ("Xác định thiết diện của hình chóp S.ABCD với (SBD). ", "Tính diện tích thiết diện trên."),
])
def test_anaphor_is_read_from_the_source_not_from_the_quotes(between, anaphor_quote):
    text, payload = _pyramid_problem(construct=False)
    old_ask = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
    text = text.replace(old_ask, _CUT + " " + between + anaphor_quote)
    for f in payload["facts"]:
        if f["id"] == "q":
            f["quotes"] = [_DEF, _CUT, anaphor_quote]     # the extraction omits the sentence about the other section
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("rest", [" và song song với (SBC).", "; (P) vuông góc với SC."])
def test_definition_is_read_to_the_end_of_the_source_sentence(rest):
    # final re-review I1: a quote cut right after "(ABCD)" must not hide the rest of the SOURCE sentence
    text, payload = _pyramid_problem(construct=False)
    text = text.replace("song song với (ABCD).", "song song với (ABCD)" + rest)
    short = "Dựng mặt phẳng (P) đi qua M và song song với (ABCD)"
    for f in payload["facts"]:
        if f["id"] == "q":
            f["quotes"] = [short, f["quotes"][1]]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED", (r.code, r.answers)


def test_plane_name_defined_twice_is_ambiguous():
    # review minor 5: two definitions of (P) in the source — refuse rather than pick the quoted one
    text, payload = _pyramid_problem()
    text = text.replace("Dựng mặt phẳng (P)", "Gọi N là trung điểm SB. Dựng mặt phẳng (P) đi qua N và song song với (SAD). "
                        "Dựng mặt phẳng (P)", 1)
    payload["facts"].append(HB._mid("fn", "N", "S", "B"))
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED", (r.code, r.answers)


def test_route_a_cannot_call_the_planner_only_construction():
    text, payload = _pyramid_problem()
    r = run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})   # no auxiliary declaration
    assert (r.status, r.code) == ("REFUSED", "AUXILIARY_ONLY_FUNCTION")
    assert "translate_point" not in RG.PROVIDER_FUNCTIONS
    assert "translate_point" not in {d["name"] for d in RG.function_declarations()}


def test_planner_bound_on_derived_planes():
    from app.simulation.geometry_functions import planner as PL
    text, payload = _pyramid_problem(construct=False)
    q = next(f for f in payload["facts"] if f["id"] == "q")
    payload["facts"] += [{**q, "id": f"q{i}", "points_b": refs} for i, refs in
                         enumerate([list("SAB"), list("SAD"), list("SBC"), list("SCD")], 2)]
    with pytest.raises(RG.TuChoi) as e:
        PL.lap_ke_hoach(payload, text)
    assert e.value.code == "PLAN_TOO_LARGE"


# ── fault injection: each postcondition is evaluated, not assumed ─────────────────────────────────────────────────────
def test_engine_parallel_postcondition_is_live(monkeypatch):
    from app.simulation.geometry_functions import engine as E
    monkeypatch.setattr(E, "parallel_planes", lambda p, q: False)
    r = run_fact_route(*_pyramid_problem())
    assert (r.status, r.code) == ("REFUSED", "ENGINE_SELF_CHECK_FAILED")


def test_translate_relation_check_is_independent_of_the_kernel(monkeypatch):
    from app.simulation.geometry_functions import engine as E
    monkeypatch.setattr(E.K, "translate", lambda p, v: p - v)      # a wrong kernel translate is caught by the relation check
    r = run_fact_route(*_pyramid_problem())
    assert (r.status, r.code) == ("REFUSED", "ENGINE_SELF_CHECK_FAILED")
