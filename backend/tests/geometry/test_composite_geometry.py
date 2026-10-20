"""Composite geometry research: independent numeric expectations, topology and source safety."""
from copy import deepcopy
from fractions import Fraction as F

import pytest

from app.ai.function_route import run_fact_route


def fact(fid, kind, quote, **kw):
    return dict(id=fid, kind=kind, role="question" if kind == "question" else "premise", quotes=[quote], **kw)


def problem(slice="section", ratio=False):
    text = "Cho hình chóp S.ABC. Đáy ABC là tam giác đều cạnh 4. SA vuông góc với (ABC). SA = 6. "
    fs = [fact("root", "solid", "Cho hình chóp S.ABC.", solid="S.ABC", solid_type="pyramid"),
          fact("base", "polygon_shape", "Đáy ABC là tam giác đều cạnh 4.", points=list("ABC"),
               shape="equilateral_triangle", value="4"),
          fact("perp", "perpendicular", "SA vuông góc với (ABC).", points_a=list("SA"), points_b=list("ABC")),
          fact("height", "length", "SA = 6.", points=list("SA"), measure="segment", value="6")]
    defs = [("M", "SA"), ("N", "SB"), ("P", "SC")] if slice == "section" else [("M", "BC")]
    for p, edge in defs:
        q = f"Gọi {p} là trung điểm của {edge}." if not ratio else f"Gọi {p} thuộc {edge} sao cho {edge[0]}{p} = {edge}/3."
        text += q + " "
        fs.append(fact("point_" + p, "point_def", q, point=p, point_kind="divide_segment" if ratio else "midpoint",
                       points=list(edge), **({"value": "1/3"} if ratio else {})))
    solids = ["S.MNP"] if slice == "section" else ["S.ABM", "S.AMC"]
    for i, solid in enumerate(solids):
        q = f"Xét hình chóp {solid}."
        text += q + " "
        fs.append(fact("child" + str(i), "solid", q, solid=solid, solid_type="pyramid"))
    for i, solid in enumerate(solids):
        q = f"Tính thể tích khối chóp {solid}."
        text += q + " "
        fs.append(fact("volume" + str(i), "question", q, quantity="volume", solid=solid))
    return text, {"facts": fs}


def squared(r, q):
    v = r.exec_result.final_memory["kq_" + q]
    return F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2


@pytest.mark.parametrize("slice,expected", [("section", [F(3)]), ("shared", [F(48), F(48)])])
def test_composite_pyramids_have_exact_independent_volumes(slice, expected):
    # Euclidean base area = 4√3, altitude = 6: V(root) = 8√3.
    # Half-scale section: V(child) = V(root)/8; median split: each V(root)/2.
    text, payload = problem(slice)
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert [squared(r, "volume" + str(i)) for i in range(len(expected))] == expected


@pytest.mark.parametrize("slice", ["section", "shared"])
def test_composite_results_do_not_depend_on_fact_order_or_vertex_names(slice):
    text, payload = problem(slice)
    # Rename the root so its name sorts after the child; no alphabetical root selection.
    names = dict(zip("SABCMNP", "ZUVWDEF"))
    import re
    def rename(v):
        if isinstance(v, str):
            return re.sub(r"[A-Z]", lambda m: names.get(m[0], m[0]), v)
        if isinstance(v, list):
            return [rename(x) for x in v]
        if isinstance(v, dict):
            return {k: (x if k in ("id", "kind", "role") else rename(x)) for k, x in v.items()}
        return v
    payload = rename(payload)
    payload["facts"].reverse()
    r = run_fact_route(rename(text), payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert squared(r, "volume0") == (F(3) if slice == "section" else F(48))


def test_shared_face_uses_the_same_point_ids_and_solid_owned_topology():
    text, payload = problem("shared")
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    objects = r.scene3d["objects"]
    solids = {o["notation"]: o for o in objects if o["type"] == "solid"}
    assert {"S.ABC", "S.ABM", "S.AMC"} <= solids.keys()
    x, y = solids["S.ABM"], solids["S.AMC"]
    faces = lambda o: {frozenset(o["vertex_ids"][i] for i in face) for face in o["faces"]}
    assert faces(x) & faces(y) == {frozenset("SAM")}
    assert len([o for o in objects if o["id"] == "M"]) == 1
    assert len({o["id"] for o in objects}) == len(objects)


def test_composite_missing_point_refuses_instead_of_inventing_a_section():
    text, payload = problem()
    text = text.replace("Gọi P là trung điểm của SC. ", "")
    payload["facts"] = [f for f in payload["facts"] if f["id"] != "point_P"]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code == "UNDERDETERMINED_POINT", (r.code, r.reason)


def test_composite_source_spoofing_is_rejected():
    text, payload = problem()
    next(f for f in payload["facts"] if f["id"] == "point_P")["points"] = list("SB")
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code == "SOURCE_OBJECT_MISMATCH", (r.code, r.reason)


@pytest.mark.parametrize("slice", ["section", "shared"])
def test_original_solid_precedes_its_auxiliaries_and_derived_solids(slice):
    r = run_fact_route(*problem(slice))
    assert r.status == "SERVED", (r.code, r.reason)
    born = {}
    for step in r.scene3d["formation"]["steps"]:
        for obj in step["visible_ids"]:
            born.setdefault(obj, step["step_index"])
    assert born["khoi_S_ABC"] < born["M"] < born["khoi_S_MNP" if slice == "section" else "khoi_S_ABM"]
    solids = [o for o in r.scene3d["objects"] if o["type"] == "solid"]
    assert all(o.get("shape_class") == "PYRAMID_LIKE" for o in solids)
    for o in r.scene3d["objects"]:
        assert all(born[d] <= born[o["id"]] for d in o.get("depends", []) if d in born and o["id"] in born)


def test_derived_base_degeneracy_is_a_safe_refusal():
    text, payload = problem("shared")
    text = text.replace("S.ABM", "S.BMC").replace("Xét hình chóp S.AMC. ", "").replace("Tính thể tích khối chóp S.AMC. ", "")
    payload["facts"] = [f for f in payload["facts"] if f["id"] not in ("child1", "volume1")]
    for f in payload["facts"]:
        if f.get("solid") == "S.ABM":
            f["solid"] = "S.BMC"
            f["quotes"] = [q.replace("S.ABM", "S.BMC") for q in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code in {"COLLINEAR_POINTS", "DEGENERATE_POINTS", "INCONSISTENT_FACTS"}, (r.code, r.reason)


def test_rational_section_and_multiple_goals_reuse_constructed_points():
    text, payload = problem(ratio=True)
    # The ratio grammar's supported equation is SM = MA/2 => SM/SA = 1/3.
    for p, edge in [("M", "SA"), ("N", "SB"), ("P", "SC")]:
        old = f"Gọi {p} thuộc {edge} sao cho S{p} = {edge}/3."
        new = f"Gọi {p} là điểm thuộc cạnh {edge} sao cho {p}{edge[1]} = 2S{p}."
        text = text.replace(old, new)
        next(f for f in payload["facts"] if f["id"] == "point_" + p)["quotes"] = [new]
    ask = "Tính diện tích tam giác MNP."
    text += ask
    payload["facts"].append(fact("area", "question", ask, quantity="area", points=list("MNP")))
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert squared(r, "volume0") == F(64, 243)
    assert squared(r, "area") == F(16, 27)
    assert len([c for c in r.calls if c["fn"] == "divide_segment"]) == 3


def test_parallel_section_matches_child_base_and_numeric_area():
    text, payload = problem()
    ask = "Tính diện tích thiết diện của hình chóp S.ABC cắt bởi mặt phẳng (MNP)."
    text += ask
    payload["facts"].append(fact("area", "question", ask, quantity="area", solid="S.ABC", points=list("MNP")))
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert squared(r, "area") == 3
    sections = [o for o in r.scene3d["objects"] if o["type"] == "section"]
    assert len(sections) == 1
    # S.MNP is exactly a half-scale pyramid; its section is at the same exact z as M,N,P.
    assert r.points["M"][2] == r.points["N"][2] == r.points["P"][2] == F(1, 2)


@pytest.mark.parametrize("mutation,code", [("height", "MISSING_DIMENSION"), ("perp", "UNDERDETERMINED_POINT"),
                                          ("unread", "SOURCE_PREMISE_UNREAD"), ("goal", "REQUEST_NOT_ANSWERED"),
                                          ("conflict", "INCONSISTENT_FACTS")])
def test_composite_missing_data_and_contradictions_refuse(mutation, code):
    text, payload = problem()
    if mutation in ("height", "perp"):
        f = next(f for f in payload["facts"] if f["id"] == mutation)
        text = text.replace(f["quotes"][0] + " ", "")
        payload["facts"].remove(f)
    if mutation == "unread":
        text = text.replace("Tính thể tích", "MN = 10. Tính thể tích")
    if mutation == "goal":
        text += "Tính độ dài đoạn MN."
    if mutation == "conflict":
        text = text.replace("Xét hình chóp", "MN = 10. Xét hình chóp")
        payload["facts"].append(fact("extra", "length", "MN = 10.", points=list("MN"), value="10", measure="segment"))
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code == code, (r.code, r.reason)


def test_two_independent_bases_have_no_inferred_placement():
    text, payload = problem()
    text = text.replace("Xét hình chóp S.MNP.", "Xét hình chóp T.DEF.").replace("khối chóp S.MNP", "khối chóp T.DEF")
    for f in payload["facts"]:
        if f.get("solid") == "S.MNP":
            f["solid"] = "T.DEF"
            f["quotes"] = [q.replace("S.MNP", "T.DEF") for q in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code == "UNSUPPORTED_MULTIPLE_BASES", (r.code, r.reason)


def test_cyclic_constructed_vertices_refuse():
    text, payload = problem()
    text = text.replace("trung điểm của SA", "trung điểm của SN").replace("trung điểm của SB", "trung điểm của SM")
    for f in payload["facts"]:
        if f["id"] in ("point_M", "point_N"):
            other = "N" if f["id"] == "point_M" else "M"
            f["points"] = ["S", other]
            f["quotes"] = [f"Gọi {f['point']} là trung điểm của S{other}."]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code == "DEPENDENCY_CYCLE", (r.code, r.reason)


def test_exact_volume_certificate_agrees_with_independent_oracle():
    r = run_fact_route(*problem())
    assert r.status == "SERVED", (r.code, r.reason)
    certs = {s["object"]: s for s in r.trace if s["step"] == "verify_solid"}
    assert certs["S.ABC"]["volume_squared"] == "192"
    assert certs["S.MNP"]["volume_squared"] == "3"
    assert certs["S.MNP"]["calls"] == ["child0"]
    assert certs["S.MNP"]["provenance"] == "DERIVED"


@pytest.mark.parametrize("face,served", [("SAM", True), ("SAB", False), ("ABC", False), ("SMN", False)])
def test_explicit_shared_face_relation_is_topologically_verified(face, served):
    text, payload = problem("shared")
    relation = f"Hai hình chóp S.ABM và S.AMC có mặt chung ({face})."
    text = text.replace("Tính thể tích khối chóp S.ABM.", relation + " Tính thể tích khối chóp S.ABM.")
    for f in payload["facts"]:
        if f["id"].startswith("child"):
            f["quotes"].append(relation)
    r = run_fact_route(text, payload)
    assert (r.status == "SERVED") == served, (r.code, r.reason)
    if served:
        assert squared(r, "volume0") + squared(r, "volume1") == 96
    else:
        assert r.code in {"INCONSISTENT_FACTS", "SOURCE_OBJECT_MISMATCH"}, (r.code, r.reason)


def test_nonplanar_derived_base_refuses():
    text, payload = problem()
    definition = "Gọi Q là trung điểm của SM."
    text = text.replace("Xét hình chóp", definition + " Xét hình chóp").replace("S.MNP", "S.MNPQ")
    payload["facts"].append(fact("point_Q", "point_def", definition, point="Q", point_kind="midpoint", points=list("SM")))
    for f in payload["facts"]:
        if f.get("solid") == "S.MNP":
            f["solid"] = "S.MNPQ"
            f["quotes"] = [q.replace("S.MNP", "S.MNPQ") for q in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code == "NON_COPLANAR_POINTS", (r.code, r.reason)


@pytest.mark.parametrize("cycle,served", [("MNPQ", True), ("MPNQ", False)])
def test_square_section_or_crossed_section_has_verified_topology(cycle, served):
    text, payload = problem()
    text = text.replace("S.ABC", "S.ABCD").replace("Đáy ABC là tam giác đều", "Đáy ABCD là hình vuông").replace("(ABC)", "(ABCD)")
    text = text.replace("Xét hình chóp", "Gọi Q là trung điểm của SD. Xét hình chóp").replace("S.MNP", "S." + cycle)
    payload["facts"].append(fact("point_Q", "point_def", "Gọi Q là trung điểm của SD.", point="Q", point_kind="midpoint", points=list("SD")))
    for f in payload["facts"]:
        if f.get("solid") == "S.ABC": f["solid"] = "S.ABCD"
        if f.get("solid") == "S.MNP": f["solid"] = "S." + cycle
        if f["id"] == "base": f.update(points=list("ABCD"), shape="square")
        if f["id"] == "perp": f["points_b"] = list("ABCD")
        f["quotes"] = [q.replace("S.ABC", "S.ABCD").replace("Đáy ABC là tam giác đều", "Đáy ABCD là hình vuông").replace("(ABC)", "(ABCD)").replace("S.MNP", "S."+cycle) for q in f["quotes"]]
    r = run_fact_route(text, payload)
    assert (r.status == "SERVED") == served, (r.code, r.reason)
    if served:
        assert squared(r, "volume0") == 16  # Root volume = 32, half-scale child = 4.
    else:
        assert r.code == "POLYHEDRON_FACE_NOT_SIMPLE"


def test_volume_certificate_rejects_a_tampered_interpreter_answer(monkeypatch):
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    execute = SemanticProgramInterpreter.execute
    def tamper(self, *a, **kw):
        result = execute(self, *a, **kw)
        result.final_memory["kq_volume0"] = F(999)
        return result
    monkeypatch.setattr(SemanticProgramInterpreter, "execute", tamper)
    r = run_fact_route(*problem())
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED"


def test_development_corpus_matches_the_independent_oracle():
    import importlib.util
    import json
    from pathlib import Path
    run = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/composite-geometry"
    spec = importlib.util.spec_from_file_location("composite_development_oracle", run / "oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    for c in json.loads((run / "corpus-dev.json").read_text(encoding="utf-8"))["cases"]:
        r = run_fact_route(c["text"], deepcopy(c["payload"]))
        if c["kind"] == "positive":
            assert r.status == "SERVED", (c["id"], r.code, r.reason)
            assert {q: str(squared(r, q)) for q in r.answers} == oracle.expected(c), c["id"]
        else:
            assert r.status == "REFUSED" and r.code in c["expected_codes"], (c["id"], r.code)


@pytest.mark.parametrize("second_side,served", [("6", False), ("4", True)])
def test_review_regular_child_requires_a_regular_base_on_the_direct_route(second_side, served):
    from app.ai.function_route import run_function_route
    calls, sentences = [], []
    def call(cid, fn, quote, **args):
        sentences.append(quote)
        calls.append(dict(id=cid, fn=fn, args=args, source={"quotes": [quote]}))
    call("root", "pyramid", "Cho hình chóp S.ABCD.", apex="S", base=list("ABCD"))
    call("base", "rectangle", "Đáy ABCD là hình chữ nhật.", vertices=list("ABCD"))
    call("ab", "segment_length", "AB = 4.", segment=list("AB"), value="4")
    call("ad", "segment_length", f"AD = {second_side}.", segment=list("AD"), value=second_side)
    call("so", "segment_length", "SO = 8.", segment=list("SO"), value="8")
    call("o", "midpoint", "Gọi O là trung điểm của AC.", point="O", segment=list("AC"))
    call("perp", "perpendicular_line_plane", "SO vuông góc với (ABCD).", line=list("SO"), plane=list("ABCD"))
    for p, b in zip("MNPQ", "ABCD"):
        call("point_"+p, "midpoint", f"Gọi {p} là trung điểm của S{b}.", point=p, segment=["S", b])
    call("child", "regular_pyramid", "Cho hình chóp đều S.MNPQ.", apex="S", base=list("MNPQ"))
    call("vol", "ask_volume", "Tính thể tích khối chóp S.MNPQ.", solid="S.MNPQ")
    r = run_function_route(" ".join(sentences), {"calls": calls})
    assert (r.status == "SERVED") == served, (r.code, r.reason)
    if not served:
        assert r.code == "INCONSISTENT_FACTS"
    else:
        assert squared(r, "vol") == F(256, 9)


def _direct_rectangle_child(second_side, child_fn="regular_pyramid", extra=()):
    from app.ai.function_route import run_function_route
    calls, sentences = [], []
    def call(cid, fn, quote, **args):
        sentences.append(quote)
        calls.append(dict(id=cid, fn=fn, args=args, source={"quotes": [quote]}))
    call("root", "pyramid", "Cho hình chóp S.ABCD.", apex="S", base=list("ABCD"))
    call("base", "rectangle", "Đáy ABCD là hình chữ nhật.", vertices=list("ABCD"))
    call("ab", "segment_length", "AB = 4.", segment=list("AB"), value="4")
    call("ad", "segment_length", f"AD = {second_side}.", segment=list("AD"), value=second_side)
    call("so", "segment_length", "SO = 8.", segment=list("SO"), value="8")
    call("o", "midpoint", "Gọi O là trung điểm của AC.", point="O", segment=list("AC"))
    call("perp", "perpendicular_line_plane", "SO vuông góc với (ABCD).", line=list("SO"), plane=list("ABCD"))
    for p, b in zip("MNPQ", "ABCD"):
        call("point_" + p, "midpoint", f"Gọi {p} là trung điểm của S{b}.", point=p, segment=["S", b])
    word = "hình chóp đều" if child_fn == "regular_pyramid" else "hình chóp"
    call("child", child_fn, f"Cho {word} S.MNPQ.", apex="S", base=list("MNPQ"))
    for cid, fn, quote, args in extra:
        call(cid, fn, quote, **args)
    call("vol", "ask_volume", "Tính thể tích khối chóp S.MNPQ.", solid="S.MNPQ")
    return run_function_route(" ".join(sentences), {"calls": calls})


def test_review_spoofed_regular_base_on_a_rectangle_child_still_refuses():
    # A forged `regular_polygon` premise on the derived base cannot upgrade a 4×6 rectangle to a square.
    r = _direct_rectangle_child("6", extra=[("fake", "regular_polygon", "Đáy MNPQ là hình vuông.",
                                             {"vertices": list("MNPQ")})])
    assert r.status == "REFUSED" and r.code == "INCONSISTENT_FACTS", (r.code, r.reason)


def test_review_generic_child_on_a_rectangle_is_still_served():
    # Same rectangle child WITHOUT the regular flag is a valid generic pyramid: V(child) = V(root)/8 = 64/8.
    r = _direct_rectangle_child("6", child_fn="pyramid")
    assert r.status == "SERVED", (r.code, r.reason)
    assert squared(r, "vol") == 64


def test_review_conflicting_side_lengths_refuse():
    r = _direct_rectangle_child("4", extra=[("mn", "segment_length", "MN = 3.", {"segment": list("MN"), "value": "3"})])
    assert r.status == "REFUSED" and r.code == "INCONSISTENT_FACTS", (r.code, r.reason)


def _planner_regular_child(shape):
    word = "hình chữ nhật" if shape == "rectangle" else "hình vuông"
    side = "6" if shape == "rectangle" else "4"
    text = (f"Cho hình chóp S.ABCD. Đáy ABCD là {word}. AB = 4. AD = {side}. "
            "Gọi O là trung điểm của AC. SO vuông góc với (ABCD). SO = 8. ")
    fs = [fact("root", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
          fact("base", "polygon_shape", f"Đáy ABCD là {word}.", points=list("ABCD"), shape=shape),
          fact("ab", "length", "AB = 4.", points=list("AB"), measure="segment", value="4"),
          fact("ad", "length", f"AD = {side}.", points=list("AD"), measure="segment", value=side),
          fact("o", "point_def", "Gọi O là trung điểm của AC.", point="O", point_kind="midpoint", points=list("AC")),
          fact("perp", "perpendicular", "SO vuông góc với (ABCD).", points_a=list("SO"), points_b=list("ABCD")),
          fact("so", "length", "SO = 8.", points=list("SO"), measure="segment", value="8")]
    for p, b in zip("MNPQ", "ABCD"):
        q = f"Gọi {p} là trung điểm của S{b}."
        text += q + " "
        fs.append(fact("point_" + p, "point_def", q, point=p, point_kind="midpoint", points=["S", b]))
    text += "Xét hình chóp đều S.MNPQ. Tính thể tích khối chóp S.MNPQ."
    fs.append(fact("child", "solid", "Xét hình chóp đều S.MNPQ.", solid="S.MNPQ", solid_type="pyramid", regular=True))
    fs.append(fact("vol", "question", "Tính thể tích khối chóp S.MNPQ.", quantity="volume", solid="S.MNPQ"))
    return text, {"facts": fs}


@pytest.mark.parametrize("shape", ["rectangle", "square"])
def test_review_planner_regular_child_is_never_wrongly_served(shape):
    # Full planner route: the source gate cannot bind the implied regular base of a derived solid, so both refuse
    # safely today. The rectangle must never be served under any route.
    r = run_fact_route(*_planner_regular_child(shape))
    assert r.status == "REFUSED", (r.code, r.reason)


@pytest.mark.parametrize("shape,served", [("rectangle", False), ("square", True)])
def test_review_planner_regular_child_shares_the_engine_invariant(shape, served, monkeypatch):
    # Bypass ONLY the source gate to pin the engine predicate on planner-generated calls (regular_pyramid +
    # regular_polygon on the derived base): it is the same exact check as on the direct route.
    from app.simulation.geometry_functions import engine
    monkeypatch.setattr(engine, "kiem_nguon", lambda *a, **kw: {})
    r = run_fact_route(*_planner_regular_child(shape))
    assert (r.status == "SERVED") == served, (r.code, r.reason)
    if served:
        assert squared(r, "vol") == F(256, 9)   # V(root) = 16·8/3; half-scale child = V/8 = 16/3.
    else:
        assert r.code == "INCONSISTENT_FACTS", (r.code, r.reason)


def test_review_regular_flag_with_equilateral_base_but_oblique_apex_refuses_in_the_engine(monkeypatch):
    # S.MNP has an equilateral base (half-scale of ABC) but SA ⟂ (ABC) puts S over A, not over the centre.
    from app.simulation.geometry_functions import engine
    monkeypatch.setattr(engine, "kiem_nguon", lambda *a, **kw: {})
    text, payload = problem()
    next(f for f in payload["facts"] if f["id"] == "child0")["regular"] = True
    r = run_fact_route(text, payload)
    assert r.status == "REFUSED" and r.code == "INCONSISTENT_FACTS", (r.code, r.reason)


def _direct(spec):
    from app.ai.function_route import run_function_route
    calls = [dict(id=cid, fn=fn, args=args, source={"quotes": [quote]}) for cid, fn, quote, args in spec]
    return run_function_route(" ".join(q for _, _, q, _ in spec), {"calls": calls})


@pytest.mark.parametrize("labels", ["ABC", "XYZ"])
def test_review2_face_perpendicular_base_uses_the_root_regardless_of_labels(labels):
    # Review 2, IMPORTANT-1: (SAB) ⟂ base must bind to the ROOT base even when the derived solid sorts first.
    # Equilateral side 4, SA = SB = 4 ⇒ h² = 16 − 4 = 12, V(root)² = (4√3·√12/3)² = 64; half-scale child V² = 1.
    A, B, C = labels
    T = labels
    spec = [("root", "pyramid", f"Cho hình chóp S.{T}.", dict(apex="S", base=list(T))),
            ("base", "regular_polygon", f"Đáy {T} là tam giác đều cạnh 4.", dict(vertices=list(T), side="4")),
            ("fp", "face_perpendicular_base", f"Mặt phẳng (S{A}{B}) vuông góc với ({T}).", dict(face=["S", A, B], base=list(T))),
            ("sa", "segment_length", f"S{A} = 4.", dict(segment=["S", A], value="4")),
            ("sb", "segment_length", f"S{B} = 4.", dict(segment=["S", B], value="4")),
            *[("point_" + p, "midpoint", f"Gọi {p} là trung điểm của S{b}.", dict(point=p, segment=["S", b]))
              for p, b in zip("MNP", T)],
            ("child", "pyramid", "Xét hình chóp S.MNP.", dict(apex="S", base=list("MNP"))),
            ("vol", "ask_volume", "Tính thể tích khối chóp S.MNP.", dict(solid="S.MNP"))]
    r = _direct(spec)
    assert r.status == "SERVED", (r.code, r.reason)
    assert squared(r, "vol") == 1


def test_review2_skew_equilateral_quadrilateral_is_not_a_square():
    # Review 2, IMPORTANT-2: a regular tetrahedron's SABC has four equal sides and equal centroid distances but is
    # skew; declaring it a square is an impossible premise and must refuse.
    spec = [("root", "regular_pyramid", "Cho hình chóp đều S.ABC.", dict(apex="S", base=list("ABC"))),
            ("base", "regular_polygon", "Đáy ABC là tam giác đều cạnh 2.", dict(vertices=list("ABC"), side="2")),
            ("sa", "segment_length", "SA = 2.", dict(segment=list("SA"), value="2")),
            ("fake", "regular_polygon", "Tứ giác SABC là hình vuông.", dict(vertices=list("SABC"))),
            ("vol", "ask_volume", "Tính thể tích khối chóp S.ABC.", dict(solid="S.ABC"))]
    r = _direct(spec)
    # The forged premise was consumed for equal-side classes, so the post-layout check reports it as a used fact.
    assert r.status == "REFUSED" and r.code in {"INCONSISTENT_FACTS", "ENGINE_SELF_CHECK_FAILED"}, (r.code, r.reason)
