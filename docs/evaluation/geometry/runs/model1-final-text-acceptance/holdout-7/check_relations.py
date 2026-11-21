# -*- coding: utf-8 -*-
"""Oracle review: every gold relation of Holdout-7 must hold (float, 1e-9) on the builder's independent coordinates.

usage: python check_relations.py   (imports build_holdout.py from this folder; writes nothing)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_holdout as B  # noqa: E402


def pts(seg):
    return re.findall(r"[A-Z][0-9]*'?", seg)


def vec(P, seg):
    a, b = pts(seg)
    return B.sub(P[b], P[a])


def holds(P, r):
    k, args = r[0], r[1:]
    if k == "len2":
        return abs(B.dot(vec(P, args[0]), vec(P, args[0])) - args[1]) < 1e-9
    if k == "eq":
        return abs(B.dot(vec(P, args[0]), vec(P, args[0])) - B.dot(vec(P, args[1]), vec(P, args[1]))) < 1e-9
    if k == "perp_ll":
        return abs(B.dot(vec(P, args[0]), vec(P, args[1]))) < 1e-9
    if k == "par_ll":
        return B.norm(B.cross(vec(P, args[0]), vec(P, args[1]))) < 1e-9
    if k == "perp_lp":
        a, b, c = pts(args[1])
        d = vec(P, args[0])
        return abs(B.dot(d, B.sub(P[b], P[a]))) < 1e-9 and abs(B.dot(d, B.sub(P[c], P[a]))) < 1e-9
    if k == "mid":
        x, y = pts(args[1])
        return all(abs(2 * P[args[0]][i] - P[x][i] - P[y][i]) < 1e-9 for i in range(3))
    raise KeyError(k)


# `pos` does not keep the coordinates: re-run the case definitions with a capturing `pos`
bad = 0
captured = {}
orig = B.pos


def capture(cid, stratum, text, fam, goal=None, gold=None, intent=None, aux=None, extra_rel=None):
    out = orig(cid, stratum, text, fam, goal, gold, intent, aux, extra_rel)
    captured[cid] = (fam[0], out)
    return out


B.pos = capture
src = Path(B.__file__).read_text(encoding="utf-8")
body = src[src.index("V = []"):src.index('M, X, Q, O =')]
ns = dict(vars(B))
exec(body, ns)
for cid, (P, case) in captured.items():
    assert set(case["gold_entities"]["solid_vertices"]) <= set(P), (cid, "vertex not in model")
    for r in case["gold_relations"]:
        if not holds(P, r):
            bad += 1
            print("RELATION_FAILS", cid, r)
print(f"cases {len(captured)} relations {sum(len(c['gold_relations']) for _, c in captured.values())} failing {bad}")
sys.exit(1 if bad else 0)
