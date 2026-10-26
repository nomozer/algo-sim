"""Named-plane /4 browser corpus: authored typed-fact-next/2 payloads (the test builders) keyed by exact problem text,
plus browser fixtures with closed-form oracles (square of the displayed value). Authored development cases: not a
holdout, not provider output. Usage (from backend/): python make_browser_corpus.py <out_dir>"""
import json, sys
from fractions import Fraction as F
from pathlib import Path

from tests.geometry.test_typed_fact_next_v2_named_plane import _M_ON_BC, _cuboid, _prism_goal, _pyramid, _regular

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)
sq = lambda f: str(F(f) ** 2)
x, y, h = 6, 8, 12
CASES = [  # id, family, payload, expected, oracle (value as shown, before squaring) or refusal code
    ("pyramid-sa-lateral-edge-base", "#3", _pyramid("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}), "SERVE", F(32, 41)),
    ("pyramid-sa-apex-base-distance", "#3", _pyramid("distance", {"point": "S", "plane": ["A", "B", "C", "D"]}), "SERVE", F(3)),
    ("regular-pyramid-face-base", "#4", _regular("angle", {"plane1": ["S", "C", "D"], "plane2": ["A", "B", "C", "D"]}), "SERVE", F(4, 5)),
    ("regular-pyramid-edge-base", "#4", _regular("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}), "SERVE", F(8, 9)),
    ("cuboid-diagonal-plane-distance", "#11", _cuboid("distance", {"point": "A", "plane": ["B", "D", "D'", "B'"]}), "SERVE", F(12, 5)),
    ("cuboid-diagonal-plane-dihedral", "#11", _cuboid("angle", {"plane1": ["A'", "B'", "C", "D"], "plane2": ["A", "B", "C", "D"]}), "SERVE", F(1, 10)),
    ("right-prism-face-distance", "#12", _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]}), "SERVE", F(24, 5)),
    ("right-prism-collinear-leading", "#12", _prism_goal("distance", {"point": "A", "plane": ["B", "M", "C", "C'"]}, extra=_M_ON_BC), "SERVE", F(24, 5)),
    ("right-prism-line-face-angle", "#12", _prism_goal("angle", {"line": ["A'", "B"], "plane": ["A", "C", "C'", "A'"]}), "SERVE", F(4, 5)),
    ("oblique-prism-face-distance", "#13", _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]}, oblique=True), "SERVE", None),
    ("right-prism-non-coplanar", "#12", _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "A'"]}), "REFUSE", "SOURCE_OBJECT_MISMATCH"),
    ("cuboid-non-coplanar", "#11", _cuboid("distance", {"point": "A", "plane": ["B", "D", "D'", "C'"]}), "REFUSE", "SOURCE_OBJECT_MISMATCH"),
    ("pyramid-apex-in-base", "#3", _pyramid("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "S"]}), "REFUSE", "SOURCE_OBJECT_MISMATCH"),
    ("right-prism-all-collinear", "#12", _prism_goal("distance", {"point": "A", "plane": ["B", "M", "C"]}, extra=_M_ON_BC), "REFUSE", "SOURCE_OBJECT_MISMATCH"),
]
outputs, fixtures = {}, []
for cid, fam, payload, expected, oracle in CASES:
    text = payload["problem_text"]
    assert text not in outputs, cid
    outputs[text] = payload
    row = {"id": cid, "family": fam, "problem_text": text, "expected": expected}
    if expected == "SERVE":
        # oblique: d² = x²y²h²/(y²h²+x²h²+x²y²) is the square of the shown value directly
        row["oracle_value_squared"] = str(F(x * x * y * y * h * h, y * y * h * h + x * x * h * h + x * x * y * y)) \
            if oracle is None else sq(oracle)
    else:
        row["expected_code"] = oracle
    fixtures.append(row)
(out / "local-replay-corpus.json").write_text(json.dumps({"schema": "hybrid-v2-local-replay-corpus/1", "outputs": outputs},
                                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(out / "browser-fixtures.json").write_text(json.dumps({"classification": "AUTHORED_REGRESSION_BROWSER_NOT_HOLDOUT_NOT_PROVIDER",
                                                       "fixtures": fixtures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(fixtures), "fixtures")
