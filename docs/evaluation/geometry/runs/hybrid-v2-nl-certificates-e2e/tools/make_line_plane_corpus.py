"""Line–plane / plane–plane distance /4 browser corpus (run `hybrid-v2-nl-certificates-e2e`). Same contract as
make_point_line_corpus.py. Usage (from backend/): python make_line_plane_corpus.py <fresh out_dir>"""
import json, re, sys
from fractions import Fraction as F
from pathlib import Path

from tests.geometry.test_typed_fact_next_v2_named_plane import _prism_goal, _pyramid, _regular
from tests.geometry.test_typed_fact_next_v2_line_plane_distance import _cub

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)
LP = "Tính khoảng cách giữa đường thẳng {l} và mặt phẳng ({p})."
PP = "Tính khoảng cách giữa hai mặt phẳng ({p}) và ({q})."


def regular_lp(line, plane, quote):                       # the shared builder only words point/angle questions
    p = _regular("angle", {"u": ["A", "B"], "v": ["A", "D"]})
    old = p["math_goals"][0]["quote"]
    p["problem_text"] = p["problem_text"].replace(old, quote)
    p["math_goals"][0].update(goal_type="distance", target={"line": line, "plane": plane}, quote=quote)
    return p


s, h = 4, 3
x, y, hp = 6, 8, 12
CASES = [  # id, family, payload, expected, squared oracle (closed form from the stated facts) or refusal code
    ("pyramid-sa-line-parallel-to-face", "#3", _pyramid("distance", {"line": ["A", "B"], "plane": ["S", "C", "D"]}, quote=LP.format(l="AB", p="SCD")),
     "SERVE", F(h * h * s * s, h * h + s * s)),
    ("pyramid-sa-edge-parallel-to-face-ad", "#3", _pyramid("distance", {"line": ["B", "C"], "plane": ["S", "A", "D"]}, quote=LP.format(l="BC", p="SAD")),
     "SERVE", F(s * s)),
    ("regular-pyramid-line-parallel-to-face", "#4", regular_lp(["A", "B"], ["S", "C", "D"], LP.format(l="AB", p="SCD")),
     "SERVE", F(s * s * (3 * 3 - F(s * s, 2)), 3 * 3 - F(s * s, 4))),
    ("right-prism-base-planes", "#12", _prism_goal("distance", {"plane1": ["A", "B", "C"], "plane2": ["A'", "B'", "C'"]},
                                                   quote=PP.format(p="ABC", q="A'B'C'"), x=x, y=y, h=hp), "SERVE", F(hp * hp)),
    ("right-prism-edge-to-lateral-face", "#12", _prism_goal("distance", {"line": ["A", "A'"], "plane": ["B", "C", "C'", "B'"]},
                                                            quote=LP.format(l="AA'", p="BCC'B'"), x=x, y=y, h=hp), "SERVE", F(x * x * y * y, x * x + y * y)),
    ("cuboid-opposite-faces", "#11", _cub({"plane1": ["A", "B", "B'", "A'"], "plane2": ["D", "C", "C'", "D'"]}, PP.format(p="ABB'A'", q="DCC'D'")),
     "SERVE", F(4 * 4)),
    ("cuboid-edge-to-base-plane", "#11", _cub({"line": ["A'", "B'"], "plane": ["A", "B", "C", "D"]}, LP.format(l="A'B'", p="ABCD")), "SERVE", F(12 * 12)),
    ("pyramid-sa-quote-names-another-plane", "#3",
     _pyramid("distance", {"line": ["A", "B"], "plane": ["S", "C", "D"]}, quote=LP.format(l="AB", p="SBC")), "REFUSE", "SOURCE_OBJECT_MISMATCH"),
    ("pyramid-sa-three-label-line", "#3",
     _pyramid("distance", {"line": ["A", "B", "C"], "plane": ["S", "C", "D"]}, quote=LP.format(l="ABC", p="SCD")), "REFUSE", "INVALID_MATH_GOAL"),
]
outputs, fixtures = {}, []
for cid, fam, payload, expected, oracle in CASES:
    text = payload["problem_text"]
    assert text not in outputs, cid
    outputs[text] = payload
    row = {"id": cid, "family": fam, "problem_text": text, "expected": expected}
    if expected == "SERVE":
        g = payload["math_goals"][0]
        shown = lambda ls: "(" + "".join(ls).replace("'", "′") + ")" if len(ls) > 2 else "".join(ls).replace("'", "′")
        t = g["target"]
        a, b = (t["line"], t["plane"]) if "line" in t else (t["plane1"], t["plane2"])
        row["expected_goal_notation"] = f"d({shown(a)}, {shown(b) if len(b) > 2 else shown(b)})"
        row["oracle_value_squared"] = str(oracle)
    else:
        row["expected_code"] = oracle
    fixtures.append(row)
(out / "local-replay-corpus.json").write_text(json.dumps({"schema": "hybrid-v2-local-replay-corpus/1", "outputs": outputs},
                                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(out / "browser-fixtures.json").write_text(json.dumps({"classification": "AUTHORED_REGRESSION_BROWSER_NOT_HOLDOUT_NOT_PROVIDER",
                                                       "fixtures": fixtures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(fixtures), "fixtures")
