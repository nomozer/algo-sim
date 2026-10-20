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
