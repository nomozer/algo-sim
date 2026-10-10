"""Preregistered exact oracles; fake payloads are handwritten for BOTH adapters.

No kernel import in the oracle: square side 2, perpendicular height 3 gives
Euclidean A=(0,0,0), B=(2,0,0), C=(2,2,0), D=(0,2,0), S=(0,0,3).
Affine Gram is diag(4,4,9). A live model's extraction quality is NOT tested.
Mutations targeted: wrong operand, result-coordinate injection, metric loss,
missing incidence/orthogonality check, source role swap, provenance loss.
"""
from __future__ import annotations

import copy
import json
import re
import socket
from fractions import Fraction as F

import pytest

from app.ai import fact_extraction as FE, function_calling as FC

BASE = ["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2.",
        "SA vuông góc với (ABCD).", "SA = 3."]
CALLS = [
    ("pyramid", {"apex": "S", "base": list("ABCD")}, BASE[0]),
    ("regular_polygon", {"vertices": list("ABCD"), "side": "2"}, BASE[1]),
    ("perpendicular_line_plane", {"line": list("SA"), "plane": list("ABCD")}, BASE[2]),
    ("segment_length", {"segment": list("SA"), "value": "3"}, BASE[3]),
]
FACTS = [
    {"kind": "solid", "solid": "S.ABCD", "solid_type": "pyramid"},
    {"kind": "polygon_shape", "points": list("ABCD"), "shape": "square", "value": "2"},
    {"kind": "perpendicular", "points_a": list("SA"), "points_b": list("ABCD")},
    {"kind": "length", "points": list("SA"), "measure": "segment", "value": "3"},
]

# Literal independent solutions of 2x2 line equations / Euclidean normal equations.
POSITIVE = [
    ("intersect_line_line", {"point": "O", "line1": list("AC"), "line2": list("BD")},
     {"kind": "point_def", "point": "O", "point_kind": "intersect_line_line", "points_a": list("AC"), "points_b": list("BD")},
     "Gọi O là giao điểm của AC và BD.", "O", ("1/2", "1/2", "0"), "2"),
    ("intersect_line_plane", {"point": "H", "line": list("SC"), "plane": list("ABD")},
     {"kind": "point_def", "point": "H", "point_kind": "intersect_line_plane", "points_a": list("SC"), "points_b": list("ABD")},
     "Gọi H là giao điểm của SC và (ABD).", "H", ("1", "1", "0"), "8"),
    ("orthogonal_projection_line", {"point": "D", "line": list("AC"), "image": "H"},
     {"kind": "projection", "point": "D", "points": list("AC"), "at": "H"},
     "Gọi H là hình chiếu vuông góc của D lên AC.", "H", ("1/2", "1/2", "0"), "2"),
    ("orthogonal_projection", {"point": "D", "plane": list("SBC"), "image": "H"},
     {"kind": "projection", "point": "D", "points": list("SBC"), "at": "H"},
     "Gọi H là hình chiếu vuông góc của D lên (SBC).", "H", ("9/13", "1", "4/13"), "88/13"),
    ("orthogonal_projection", {"point": "A", "plane": list("ABC"), "image": "H"},
     {"kind": "projection", "point": "A", "points": list("ABC"), "at": "H"},
     "Gọi H là hình chiếu vuông góc của A lên (ABC).", "H", ("0", "0", "0"), "0"),
    ("orthogonal_projection_line", {"point": "C", "line": list("AB"), "image": "H"},
     {"kind": "projection", "point": "C", "points": list("AB"), "at": "H"},
     "Gọi H là hình chiếu vuông góc của C lên AB.", "H", ("1", "0", "0"), "4"),
    ("orthogonal_projection_line", {"point": "A", "line": list("AB"), "image": "H"},
     {"kind": "projection", "point": "A", "points": list("AB"), "at": "H"},
     "Gọi H là hình chiếu vuông góc của A lên AB.", "H", ("0", "0", "0"), "0"),
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("NETWORK_FORBIDDEN")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")


def run(arm, extra, scale=1, rename=None, reverse=False):
    """Exercise real provider payload/parser/selector/engine/IR/scene; no direct kernel call."""
    calls = copy.deepcopy(CALLS) + [(fn, args, q) for fn, args, fact, q in extra]
    facts = copy.deepcopy(FACTS) + [fact for fn, args, fact, q in extra]
    quotes = BASE + [q for fn, args, fact, q in extra]
    query = "Tính thể tích hình chóp S.ABCD."
    calls.append(("ask_volume", {"solid": "S.ABCD"}, query))
    facts.append({"kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABCD"})
    quotes.append(query)
    if scale != 1:
        calls[1][1]["side"] = facts[1]["value"] = str(2 * scale)
        calls[3][1]["value"] = facts[3]["value"] = str(3 * scale)
        quotes = [q.replace("cạnh 2", f"cạnh {2 * scale}").replace("= 3", f"= {3 * scale}") for q in quotes]
    call_data = [{"fn": fn, "args": args, "id": f"c{i}", "source": {"quotes": [quotes[i]]}}
                 for i, (fn, args, _) in enumerate(calls)]
    fact_data = [{"id": f"c{i}", "role": "premise", **f, "quotes": [quotes[i]]} for i, f in enumerate(facts)]
    text = " ".join(quotes)
    if rename:
        def ren(s):
            return re.sub(r"[A-Z][0-9]*'?", lambda m: rename.get(m[0], m[0]), s)
        text = ren(text)
        call_data = json.loads(ren(json.dumps(call_data, ensure_ascii=False)))
        fact_data = json.loads(ren(json.dumps(fact_data, ensure_ascii=False)))
    if reverse:
        call_data.reverse()
        fact_data.reverse()
    captured = []
    def fake(payload):
        captured.append(payload)
        parts = ([{"functionCall": {"name": c["fn"], "args": {**c["args"], "call_id": c["id"], "quotes": c["source"]["quotes"]}}}
                  for c in call_data] if arm == "A" else [{"text": json.dumps({"facts": fact_data}, ensure_ascii=False)}])
        return {"candidates": [{"finishReason": "STOP", "content": {"parts": parts}}],
                "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1}}
    result = (FC.run_ai_function_route if arm == "A" else FE.run_ai_fact_route)(text, fake)
    assert len(captured) == 1
    return result, captured[0]


def item(case):
    return [case[:4]]


def scene_point(r, label):
    return next(o for o in r.scene3d["objects"] if o["type"] == "point3" and o["display_label"] == label)


def point_oracle(r, label, xyz, length_sq):
    assert r.status == "SERVED", (r.code, r.reason)
    o = scene_point(r, label)
    assert tuple(map(F, o["xyz"])) == tuple(map(F, xyz))
    # Independent Euclidean coordinates, not product metric method.
    physical = [F(x) * v for x, v in zip(o["xyz"], (2, 2, 3))]
    assert sum(v * v for v in physical) == F(length_sq)
    assert o["origin"] == "DERIVED" and o["producer"] and o["depends"] and o["dependency_edges"]
    assert r.kernel_check is True
    stmt = next(s for s in r.program["statements"] if s.get("target_var") == o["id"])
    assert stmt["kind"] == "construct_point" and "coords" not in stmt
    assert stmt["expr"]["kind"] in {"project_onto", "intersect_line_line", "intersect_line_plane"}
    trace = next(s for s in r.trace if s.get("step") == "place_point" and s.get("object") == label)
    assert trace["provenance"] == "DERIVED" and trace["producer"] and trace["dependencies"]
    assert trace["relation_verified"] is True


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("case", POSITIVE, ids=lambda c: c[0] + "_" + c[3])
def test_new_points_adapter_oracle_provenance(arm, case):
    r, payload = run(arm, item(case))
    point_oracle(r, *case[4:])
    assert list(r.answers.values()) == ["4"]
    if arm == "A":
        assert case[0] in payload["toolConfig"]["functionCallingConfig"]["allowedFunctionNames"]
    else:
        assert any(c["fn"] == case[0] for c in r.calls)
        assert r.planner


NEGATIVE = [
    ("intersect_line_line", {"point": "H", "line1": list("AB"), "line2": list("DC")}, "AB", "DC", "PARALLEL_NO_INTERSECTION"),
    ("intersect_line_line", {"point": "H", "line1": list("AB"), "line2": list("BA")}, "AB", "BA", "CONTAINED_INFINITE_INTERSECTION"),
    ("intersect_line_line", {"point": "H", "line1": list("SA"), "line2": list("BC")}, "SA", "BC", "SKEW_NO_INTERSECTION"),
    ("intersect_line_line", {"point": "H", "line1": list("AA"), "line2": list("BC")}, "AA", "BC", "DEGENERATE_POINTS"),
    ("intersect_line_plane", {"point": "H", "line": list("CD"), "plane": list("SAB")}, "CD", "(SAB)", "PARALLEL_NO_INTERSECTION"),
    ("intersect_line_plane", {"point": "H", "line": list("AB"), "plane": list("SAB")}, "AB", "(SAB)", "CONTAINED_INFINITE_INTERSECTION"),
    ("intersect_line_plane", {"point": "H", "line": list("SA"), "plane": list("AAA")}, "SA", "(AAA)", "COLLINEAR_POINTS"),
    ("intersect_line_plane", {"point": "H", "line": list("SA"), "plane": list("SABC")}, "SA", "(SABC)", "NON_COPLANAR_POINTS"),
    ("intersect_line_line", {"point": "H", "line1": list("AX"), "line2": list("BD")}, "AX", "BD", "UNDERDETERMINED_POINT"),
]


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("fn,args,left,right,code", NEGATIVE)
def test_intersection_fail_closed(arm, fn, args, left, right, code):
    fact = {"kind": "point_def", "point": "H", "point_kind": fn,
            "points_a": args.get("line1", args.get("line")), "points_b": args.get("line2", args.get("plane"))}
    r, _ = run(arm, [(fn, args, fact, f"Gọi H là giao điểm của {left} và {right}.")])
    assert (r.status, r.code) == ("REFUSED", code), r.reason
    assert r.scene3d is None and not r.answers


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("fn,target,code", [("orthogonal_projection_line", "AA", "DEGENERATE_POINTS"),
                                           ("orthogonal_projection", "AAA", "COLLINEAR_POINTS"),
                                           ("orthogonal_projection", "SABC", "NON_COPLANAR_POINTS")])
def test_projection_degenerate(arm, fn, target, code):
    key = "line" if fn.endswith("_line") else "plane"
    fact = {"kind": "projection", "point": "D", "points": list(target), "at": "H"}
    token = target if key == "line" else f"({target})"
    r, _ = run(arm, [(fn, {"point": "D", key: list(target), "image": "H"}, fact,
                     f"Gọi H là hình chiếu vuông góc của D lên {token}.")])
    assert (r.status, r.code) == ("REFUSED", code), r.reason


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("case", POSITIVE[:4])
def test_rename_scale_permutation(arm, case):
    rename = dict(zip("SABCDOH", ["T1", "E'", "F'", "G'", "I'", "J'", "K'"]))
    r, _ = run(arm, item(case), scale=3, rename=rename, reverse=True)
    assert r.status == "SERVED", (r.code, r.reason)
    assert tuple(map(F, scene_point(r, rename[case[4]])["xyz"])) == tuple(map(F, case[5]))
    assert list(r.answers.values()) == ["108"]
    assert r.scene3d["chart_metric"] == [["36", "0", "0"], ["0", "36", "0"], ["0", "0", "81"]]


@pytest.mark.parametrize("arm", ["A", "B"])
def test_composition_midpoint_intersection_projection_quantity(arm):
    extra = [("midpoint", {"point": "M", "segment": list("SA")},
              {"kind": "point_def", "point": "M", "point_kind": "midpoint", "points": list("SA")}, "Gọi M là trung điểm SA."),
             ("intersect_line_plane", {"point": "P", "line": list("SD"), "plane": list("MBC")},
              {"kind": "point_def", "point": "P", "point_kind": "intersect_line_plane", "points_a": list("SD"), "points_b": list("MBC")},
              "Gọi P là giao điểm của SD và (MBC)."),
             ("orthogonal_projection_line", {"point": "P", "line": list("BD"), "image": "H"},
              {"kind": "projection", "point": "P", "points": list("BD"), "at": "H"}, "Gọi H là hình chiếu vuông góc của P lên BD.")]
    r, _ = run(arm, extra, reverse=True)
    point_oracle(r, "P", ("0", "1/2", "1/2"), "13/4")
    point_oracle(r, "H", ("1/4", "3/4", "0"), "5/2")
    placed = [s["object"] for s in r.trace if s["step"] == "place_point"]
    assert placed.index("M") < placed.index("P") < placed.index("H")


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("case", POSITIVE[:4])
def test_wrong_source_roles_rejected(arm, case):
    fn, args, fact, q = copy.deepcopy(case[:4])
    if fn.startswith("intersect"):
        args["point"] = fact["point"] = "A"
    else:
        args["point"], args["image"] = args["image"], args["point"]
        fact["point"], fact["at"] = fact["at"], fact["point"]
    r, _ = run(arm, [(fn, args, fact, q)])
    assert r.status == "REFUSED" and r.code == "SOURCE_OBJECT_MISMATCH", (r.code, r.reason)


@pytest.mark.parametrize("arm", ["A", "B"])
def test_inconsistent_two_definitions(arm):
    c1 = POSITIVE[2][:4]
    fn, args, fact, q = copy.deepcopy(POSITIVE[3][:4])
    r, _ = run(arm, [c1, (fn, args, fact, q)])
    assert r.status == "REFUSED" and r.code == "INCONSISTENT_FACTS", (r.code, r.reason)
