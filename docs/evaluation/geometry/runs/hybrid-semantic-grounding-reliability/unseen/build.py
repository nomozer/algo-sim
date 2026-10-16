"""Turns the independently authored unseen items (`authored.json`, frozen, sha256 in preregistration.md) into cases.

The author wrote text + semantic labels only, without reading any repository file. This script (implementing agent)
adds the extraction an ideal extractor would return in the CURRENT TypedFact schema:
  - `faithful`: the facts say exactly what the item asks  ⇒ expect follows the author's label
    (ANSWER_ALL / CONSTRUCT ⇒ SERVE, REFUSE / PARTIAL_MUST_DECLARE ⇒ REFUSE);
  - `schema_gap`: the schema cannot express the request (described solid, unnamed constructed point, squared or half
    value, yes/no question) ⇒ the nearest typed extraction is given and must be REFUSED; the item counts as a
    capability gap, never as a pass.
NO_VALUE = refused, or served with no numeric answer (proof / yes-no items whose nearest extraction is a proof goal).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREMISE = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 3."
FACTS = [
    {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD"], "solid": "S.ABCD", "solid_type": "pyramid"},
    {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["đáy ABCD là hình vuông cạnh 2"],
     "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
    {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)"],
     "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
    {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3"], "points": ["S", "A"], "measure": "segment", "value": "3"},
]


def L(s):
    out = []
    for ch in s:
        if ch == "'":
            out[-1] += "'"
        else:
            out.append(ch)
    return out


def q(qid, quote, quantity, **kw):
    return {"id": qid, "kind": "question", "role": "question", "quotes": [quote], "quantity": quantity, **kw}
def dist(qid, quote, p, target): return q(qid, quote, "distance", points_a=L(p), points_b=L(target))
def dmid(qid, quote, seg, target): return q(qid, quote, "distance", point_kind="midpoint", points=L(seg), points_b=L(target))
def length(qid, quote, seg): return q(qid, quote, "length", points=L(seg))
def vol(qid, quote): return q(qid, quote, "volume", solid="S.ABCD")
def angle(qid, quote, line, plane): return q(qid, quote, "angle", points_a=L(line), points_b=L(plane))
def proj(fid, quote, p, onto, at): return {"id": fid, "kind": "projection", "role": "premise", "quotes": [quote], "point": p,
                                           "points": L(onto), "at": at}
def inter(fid, quote, a, b): return {"id": fid, "kind": "intersection_line", "role": "premise", "quotes": [quote],
                                     "points_a": L(a), "points_b": L(b)}
def perp(fid, quote, a, b, role): return {"id": fid, "kind": "perpendicular", "role": role, "quotes": [quote],
                                          "points_a": L(a), "points_b": L(b)}

def r_pp(rid, p, plane): return {"id": rid, "q": "dist_point_plane", "point": p, "plane": L(plane)}
def r_pl(rid, p, line): return {"id": rid, "q": "dist_point_line", "point": p, "line": ["named", L(line)]}
def r_len(rid, a, b): return {"id": rid, "q": "length", "a": a, "b": b}
def r_vol(rid): return {"id": rid, "q": "volume_pyramid", "apex": "S", "base": ["A", "B", "C", "D"]}
MSC = ["mid", "S", "C"]

# index → (extraction kind, facts(text), expect, oracle requests, note). `T` is the item text.
SPEC = {
    0: ("faithful", lambda T: [dist("q", T, "A", "SBC")], [r_pp("q", "A", "SBC")]),
    1: ("faithful", lambda T: [dmid("q", T, "SC", "ABCD")], [r_pp("q", MSC, "ABCD")]),
    2: ("faithful", lambda T: [dist("q", T, "D", "SB")], [r_pl("q", "D", "SB")]),
    3: ("faithful", lambda T: [length("q", T, "SC")], [r_len("q", "S", "C")]),
    4: ("faithful", lambda T: [vol("q", T)], [r_vol("q")]),
    5: ("faithful", lambda T: [dist("q", T, "C", "SAD")], [r_pp("q", "C", "SAD")]),
    6: ("schema_gap", lambda T: [vol("q", T)], None),                         # volume of a described solid
    7: ("schema_gap", lambda T: [proj("p", T, "A", "SBC", "H")], None),       # unnamed projection point
    8: ("faithful", lambda T: [proj("p", T, "A", "SB", "H")], []),
    9: ("schema_gap", lambda T: [proj("p", T, "A", "SD", "H")], None),
    10: ("schema_gap", lambda T: [proj("p", T, "A", "SCD", "H")], None),
    11: ("faithful", lambda T: [inter("g", T, "SAB", "SCD")], []),
    12: ("faithful", lambda T: [proj("p", T, "A", "SC", "K")], []),
    13: ("faithful", lambda T: [length("q1", T, "SC"), dist("q2", T, "A", "SCD")], [r_len("q1", "S", "C"), r_pp("q2", "A", "SCD")]),
    14: ("faithful", lambda T: [proj("p", T, "A", "SBC", "H"), length("q", T, "AH")],
         [{"id": "q", "q": "dist_point_plane", "point": "A", "plane": ["S", "B", "C"]}]),   # AH = d(A, (SBC))
    15: ("faithful", lambda T: [vol("q1", "Tính thể tích khối chóp."),
                                dist("q2", "Từ đó suy ra khoảng cách từ D đến mặt phẳng (SBC).", "D", "SBC")],
         [r_vol("q1"), r_pp("q2", "D", "SBC")]),
    16: ("faithful", lambda T: [length("q1", T, "SB"), length("q2", T, "SD"), dist("q3", T, "B", "SD")],
         [r_len("q1", "S", "B"), r_len("q2", "S", "D"), r_pl("q3", "B", "SD")]),
    17: ("faithful", lambda T: [dist("q1", T, "A", "SC"), dist("q2", T, "B", "SAC")], [r_pl("q1", "A", "SC"), r_pp("q2", "B", "SAC")]),
    18: ("faithful", lambda T: [length("q1", T, "BD"), dist("q2", T, "S", "BD")], [r_len("q1", "B", "D"), r_pl("q2", "S", "BD")]),
    19: ("faithful", lambda T: [dist("q", T, "A", "SBC")], None),             # E is not in the figure: must not serve A only
    20: ("schema_gap", lambda T: [length("q", T, "SC")], None),              # squared length
    21: ("schema_gap", lambda T: [dist("q", T, "A", "SBD")], None),           # half a distance
    22: ("schema_gap", lambda T: [proj("p", T, "S", "ABCD", "H")], None),
    23: ("schema_gap", lambda T: [{"id": "p", "kind": "point_def", "role": "premise", "quotes": [T], "point": "O",
                                   "point_kind": "intersect_line_plane", "points_a": ["A", "C"], "points_b": ["S", "B", "D"]}], None),
    24: ("faithful", lambda T: [angle("q", T, "SC", "ABCD")],
         [{"id": "q", "q": "angle_line_plane_cos2", "line": ["S", "C"], "plane": ["A", "B", "C", "D"]}]),
    25: ("faithful", lambda T: [q("q", T, "distance", points_a=["A", "B"], points_b=["S", "C"])],
         [{"id": "q", "q": "dist_lines", "l1": ["A", "B"], "l2": ["S", "C"]}]),
    26: ("faithful", lambda T: [dist("q", T, "D", "SB")], [r_pl("q", "D", "SB")]),   # foot inside SB: segment distance = line distance
    27: ("faithful", lambda T: [vol("q", T)], None),
    28: ("faithful", lambda T: [perp("g", T, "BC", "SAB", "prove")], "NO_VALUE"),
    29: ("schema_gap", lambda T: [dist("q", T, "A", "SBC")], None),           # yes/no question typed as a value
    30: ("faithful", lambda T: [length("q", T, "SD")], [r_len("q", "S", "D")]),
    31: ("schema_gap", lambda T: [perp("g", T, "SC", "BD", "prove")], "NO_VALUE"),
    32: ("schema_gap", lambda T: [perp("g", T, "AM", "SC", "prove")], "NO_VALUE"),
    33: ("faithful", lambda T: [dist("q", "mình muốn biết khoảng cách từ B đến đường thẳng SC cơ.", "B", "SC")], [r_pl("q", "B", "SC")]),
    34: ("faithful", lambda T: [dist("q", T, "E", "SBC")], None),
    35: ("faithful", lambda T: [dist("q", T, "D", "SAB")], None),             # (SABC) shortened by the extractor
    36: ("faithful", lambda T: [{"id": "f9", "kind": "length", "role": "premise", "quotes": ["SA = 5"], "points": ["S", "A"],
                                 "measure": "segment", "value": "5"}, vol("q", "hãy tính thể tích khối chóp S.ABCD.")], None),
    37: ("faithful", lambda T: [{"id": "u", "kind": "unsupported", "role": "question", "quotes": [T], "reason": "total surface area"}], None),
    38: ("faithful", lambda T: [dist("q", T, "C", "SBD")], None),
    39: ("faithful", lambda T: [length("q", T, "SO")], None),
}
#: extra near-miss extraction of item 33: the negated request typed as the asked one
EXTRA = {"33n": (33, lambda T: [dist("q", "Mình không hỏi khoảng cách từ B đến (SAC) đâu", "B", "SAC")])}


def main() -> int:
    items = json.loads((HERE / "authored.json").read_text(encoding="utf-8"))["items"]
    cases = []
    for i, it in enumerate(items):
        kind, facts, req = SPEC[i]
        if req == "NO_VALUE":
            expect, reqs = "NO_VALUE", []
        elif req is None:
            expect, reqs = "REFUSE", []
        else:
            expect, reqs = "SERVE", req
        cases.append({"id": f"U{i:02d}", "group": "F", "figure": "pyramid", "text": f"{PREMISE} {it['text']}",
                      "payload": {"facts": FACTS + facts(it["text"])}, "expect": expect, "requests": reqs,
                      "source_requests": len(it["requests"]), "refuse_codes": [], "mechanism": "none",
                      "extraction": kind, "author_family": it["family"], "author_behaviour": it["correct_system_behaviour"]})
    for cid, (i, facts) in EXTRA.items():
        it = items[i]
        cases.append({"id": f"U{cid}", "group": "F", "figure": "pyramid", "text": f"{PREMISE} {it['text']}",
                      "payload": {"facts": FACTS + facts(it["text"])}, "expect": "REFUSE", "requests": [],
                      "source_requests": len(it["requests"]), "refuse_codes": [], "mechanism": "none",
                      "extraction": "near-miss (negated request typed as asked)", "author_family": it["family"],
                      "author_behaviour": it["correct_system_behaviour"]})
    for c in cases:                                   # every quote must be verbatim in the text
        for f in c["payload"]["facts"]:
            assert all(qt in c["text"] for qt in f["quotes"]), (c["id"], f["quotes"])
    out = {"status": "UNSEEN_WORDING_INDEPENDENT_AUTHOR_NOT_HUMAN_HELD_OUT", "cases": cases}
    text = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    target = HERE / "cases.json"
    if target.exists() and target.read_text(encoding="utf-8") != text:
        print("cases.json exists with different content — refusing to overwrite", file=sys.stderr)
        return 1
    target.write_text(text, encoding="utf-8")
    print(f"{len(cases)} unseen cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
