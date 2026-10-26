"""Point–line /4 browser corpus (second slice). Same contract as make_browser_corpus.py. Usage (from backend/):
python make_point_line_corpus.py <out_dir>"""
import json, sys
from fractions import Fraction as F
from pathlib import Path

from tests.geometry.test_typed_fact_next_v2_named_plane import _cuboid, _prism_goal, _pyramid, _regular

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)
q = lambda p, ln: f"Tính khoảng cách từ {p} đến đường thẳng {''.join(ln)}."
pl = lambda p, ln, **kw: _prism_goal("distance", {"point": p, "line": ln}, quote=q(p, ln), **kw)
x, y, h, s, sh = 6, 8, 12, 4, 3
CASES = [  # id, family, payload, expected, squared oracle or refusal code
    ("right-prism-base-altitude", "#12", pl("A", ["B", "C"]), "SERVE", F(x*x*y*y, x*x+y*y)),
    ("right-prism-three-perpendiculars", "#12", pl("A'", ["B", "C"]), "SERVE", h*h + F(x*x*y*y, x*x+y*y)),
    ("pyramid-sa-a-to-sc", "#3", _pyramid("distance", {"point": "A", "line": ["S", "C"]}, quote=q("A", "SC")), "SERVE",
     F(2*sh*sh*s*s, sh*sh+2*s*s)),
    ("pyramid-sa-s-to-bd", "#3", _pyramid("distance", {"point": "S", "line": ["B", "D"]}, quote=q("S", "BD")), "SERVE",
     sh*sh + F(s*s, 2)),
    ("regular-pyramid-a-to-sc", "#4", _regular("distance", {"point": "A", "line": ["S", "C"]}), "SERVE", 2*16 - F(256, 9)),
    ("cuboid-top-vertex-to-base-diagonal", "#11", _cuboid("distance", {"point": "A'", "line": ["B", "D"]}), "SERVE",
     144 + F(144, 25)),
    ("right-prism-undetermined-point", "#12", pl("X", ["B", "C"]), "REFUSE", "UNDERDETERMINED_POINT"),
    ("right-prism-quote-names-another-line", "#12",
     _prism_goal("distance", {"point": "A", "line": ["B", "C"]}, quote=q("A", ["B", "C'"])), "REFUSE",
     "SOURCE_OBJECT_MISMATCH"),
]
outputs, fixtures = {}, []
for cid, fam, payload, expected, oracle in CASES:
    text = payload["problem_text"]
    assert text not in outputs, cid
    outputs[text] = payload
    row = {"id": cid, "family": fam, "problem_text": text, "expected": expected}
    row["oracle_value_squared" if expected == "SERVE" else "expected_code"] = str(oracle) if expected == "SERVE" else oracle
    fixtures.append(row)
(out / "local-replay-corpus.json").write_text(json.dumps({"schema": "hybrid-v2-local-replay-corpus/1", "outputs": outputs},
                                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(out / "browser-fixtures.json").write_text(json.dumps({"classification": "AUTHORED_REGRESSION_BROWSER_NOT_HOLDOUT_NOT_PROVIDER",
                                                       "fixtures": fixtures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(fixtures), "fixtures")
