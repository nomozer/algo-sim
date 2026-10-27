# -*- coding: utf-8 -*-
"""Adversarial solid-kind binding cases for run `hybrid-v2-planner-premerge-review` (AUTHORED_DEVELOPMENT_NOT_HOLDOUT).

Offline, 0 provider calls. Each case edits ONE question/section phrase of an already-served development fixture and
records the route outcome next to the expectation written BEFORE running (`expect`: SERVED / REFUSED). The expectation
is the geometric meaning of the Vietnamese kind word against the solid the source defines, never the product output:

  generic  "lăng trụ", "chóp", "hình chóp", "hình lăng trụ"            -> class (prism-like / pyramid-like)
  specific "lăng trụ đứng"  -> right prism       "hình hộp" -> prism on a 4-gon (parallelepiped)
           "hình hộp chữ nhật" -> right prism, rectangle base          "hình lập phương" -> cube
           "tứ diện" -> pyramid on a triangle

Run from `backend/`:  python <this file> <out.json>
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.function_route import run_fact_route  # noqa: E402

DEV = json.loads((ROOT / "docs/evaluation/geometry/runs/hybrid-v2-planner-generalization/inputs/development.json")
                 .read_text(encoding="utf-8"))["cases"]
ROW = {r["id"]: r for r in DEV}


def _edit(row: dict, old: str, new: str) -> dict:
    row = deepcopy(row)
    assert old in row["text"], (row["id"], old)
    row["text"] = row["text"].replace(old, new)
    for f in row["payload"]["facts"]:
        f["quotes"] = [q.replace(old, new) for q in f["quotes"]]
    return row


def _prism_area(rid: str, solid_phrase: str) -> str:
    return f"Tính diện tích thiết diện của {solid_phrase} với (P)."


def _prism_sec(rid: str, solid_phrase: str) -> str:
    return f"Dựng thiết diện của {solid_phrase} với (P)."


#: (fixture id, the phrase the fixture writes for its solid)
PRISMS = {
    "right-base": "lăng trụ đứng ABC.A'B'C'",        # right triangular prism
    "oblique-base": "lăng trụ ABC.A'B'C'",           # oblique triangular prism
    "cuboid-base": "hình hộp chữ nhật ABCD.A'B'C'D'",  # 6 x 8 x 12 rectangular box
    "cube-diagonal": "hình lập phương ABCD.A'B'C'D'",  # 4 x 4 x 4 cube
}

#: Expected outcome of a KIND-ONLY phrase (no symbol) per fixture. Written from geometry, before any run.
KIND_ONLY = {
    "right-base": {"lăng trụ": "SERVED", "hình lăng trụ": "SERVED", "lăng trụ đứng": "SERVED",
                   "khối lăng trụ đứng": "SERVED", "lăng trụ tam giác": "SERVED",
                   "hình hộp": "REFUSED", "hình hộp chữ nhật": "REFUSED", "hình lập phương": "REFUSED",
                   "khối lập phương": "REFUSED", "chóp": "REFUSED", "hình chóp": "REFUSED", "tứ diện": "REFUSED"},
    "oblique-base": {"lăng trụ": "SERVED", "hình lăng trụ": "SERVED", "lăng trụ đứng": "REFUSED",
                     "hình hộp": "REFUSED", "hình lập phương": "REFUSED", "chóp": "REFUSED"},
    "cuboid-base": {"lăng trụ": "SERVED", "lăng trụ đứng": "SERVED", "hình hộp": "SERVED",
                    "hình hộp chữ nhật": "SERVED", "hình lập phương": "REFUSED", "khối lập phương": "REFUSED",
                    "hình chóp": "REFUSED", "tứ diện": "REFUSED", "lăng trụ tam giác": "REFUSED"},
    "cube-diagonal": {"lăng trụ": "SERVED", "hình hộp": "SERVED", "hình hộp chữ nhật": "SERVED",
                      "hình lập phương": "SERVED", "hình chóp": "REFUSED", "tứ diện": "REFUSED"},
}

#: Full symbol present. Wrong symbol must refuse; a right symbol with a contradicting kind word is recorded separately.
SYMBOL = {
    "right-base": {"lăng trụ đứng ABC.A'B'C'": "SERVED", "lăng trụ ABC.A'B'C'": "SERVED",
                   "lăng trụ đứng DEF.D'E'F'": "REFUSED", "hình lập phương ABCD.A'B'C'D'": "REFUSED",
                   "hình chóp S.ABC": "REFUSED", "hình lập phương ABC.A'B'C'": "REFUSED",
                   "hình chóp ABC.A'B'C'": "REFUSED"},
    "cuboid-base": {"hình hộp ABCD.A'B'C'D'": "SERVED", "lăng trụ ABCD.A'B'C'D'": "SERVED",
                    "hình lập phương ABCD.A'B'C'D'": "REFUSED", "hình hộp chữ nhật EFGH.E'F'G'H'": "REFUSED"},
}


def _run(row: dict) -> dict:
    r = run_fact_route(row["text"], deepcopy(row["payload"]))
    return {"status": r.status, "code": r.code, "reason": (r.reason or "")[:240] if r.status != "SERVED" else None}


def prism_cases() -> list[dict]:
    out = []
    for rid, phrase in PRISMS.items():
        base = ROW[rid]
        for table, cls in ((KIND_ONLY, "kind_only"), (SYMBOL, "symbol")):
            for word, expect in table.get(rid, {}).items():
                # (a) the AREA question names the solid this way, the construction clause keeps the source phrase
                row = _edit(base, _prism_area(rid, phrase), _prism_area(rid, word))
                out.append({"id": f"{rid}|area|{word}", "class": cls, "clause": "area", "expect": expect, **_run(row)})
                # (b) the CONSTRUCTION clause names it this way, the area question keeps the source phrase
                row = _edit(base, _prism_sec(rid, phrase), _prism_sec(rid, word))
                out.append({"id": f"{rid}|section|{word}", "class": cls, "clause": "section", "expect": expect,
                            **_run(row)})
    # (c) both clauses rewritten identically, facts reversed (provider order) — meaning unchanged
    for rid, word, expect in (("right-base", "hình lập phương", "REFUSED"), ("right-base", "lăng trụ", "SERVED"),
                              ("cuboid-base", "hình lập phương", "REFUSED"), ("cube-diagonal", "hình lập phương", "SERVED")):
        row = _edit(_edit(ROW[rid], _prism_area(rid, PRISMS[rid]), _prism_area(rid, word)),
                    _prism_sec(rid, PRISMS[rid]), _prism_sec(rid, word))
        row["payload"]["facts"].reverse()
        out.append({"id": f"{rid}|both-reversed|{word}", "class": "kind_only", "clause": "both", "expect": expect,
                    **_run(row)})
    # (d) renamed fixture (DEF.D'E'F') with kind-only wording
    for word, expect in (("hình lập phương", "REFUSED"), ("lăng trụ", "SERVED"), ("tứ diện", "REFUSED")):
        rid = "renamed-changed-reversed"
        row = _edit(ROW[rid], _prism_area(rid, "lăng trụ đứng DEF.D'E'F'"), _prism_area(rid, word))
        out.append({"id": f"{rid}|area|{word}", "class": "kind_only", "clause": "area", "expect": expect, **_run(row)})
    return out


def pyramid_cases() -> list[dict]:
    from tests.geometry import test_geometry_capability_expansion as T
    out = []
    # triangular pyramid S.ABC (Slice B fixture): section + area on one derived plane
    sec = "Dựng thiết diện của hình chóp S.ABC với (P)."
    q = next(x for x in T.B_FACTS if x["id"] == "q")
    for word, expect in (("hình chóp S.ABC", "SERVED"), ("chóp", "SERVED"), ("hình chóp", "SERVED"),
                         ("tứ diện", "SERVED"), ("tứ diện SABC", "SERVED"), ("hình chóp tam giác", "SERVED"),
                         ("lăng trụ", "REFUSED"), ("hình hộp", "REFUSED"), ("hình lập phương", "REFUSED"),
                         ("hình chóp S.ABCD", "REFUSED")):
        new = f"Tính diện tích thiết diện của {word} với (P)."
        facts = [x for x in T.B_FACTS if x["id"] != "q"] + [
            {**q, "id": "sec", "kind": "section", "quotes": [T.B_DEF + " " + sec]}, {**q, "quotes": [T.B_DEF + " " + new]}]
        text = T.B_TEXT.replace(T.B_DEF + " " + T.B_ASK, f"{T.B_DEF} {sec} {T.B_DEF} {new}")
        r = T.run(text, facts)
        out.append({"id": f"pyr3|area|{word}", "class": "pyramid", "clause": "area", "expect": expect,
                    "status": r.status, "code": r.code, "reason": None if r.status == "SERVED" else (r.reason or "")[:240]})
    # quadrilateral pyramid S.ABCD (Slice A fixture): plane through M ⊥ SC
    dfn = "Dựng mặt phẳng (P) đi qua M và vuông góc với SC."
    for word, expect in (("hình chóp S.ABCD", "SERVED"), ("chóp", "SERVED"), ("hình chóp", "SERVED"),
                         ("hình chóp tứ giác", "SERVED"), ("tứ diện", "REFUSED"), ("lăng trụ", "REFUSED"),
                         ("hình lập phương", "REFUSED")):
        ask = f"Tính diện tích thiết diện của {word} với (P)."
        qa = {"id": "q", "kind": "question", "role": "question", "quotes": [dfn, ask], "quantity": "area",
              "solid": "S.ABCD", "point": "M", "points_b": ["S", "C"], "plane_relation": "perpendicular"}
        facts = [x for x in T.A_FACTS if x["id"] != "n"] + [qa]
        text = T.A_TEXT.replace("Gọi N là trung điểm của BC. ", "") + dfn + " " + ask
        r = T.run(text, facts)
        out.append({"id": f"pyr4|area|{word}", "class": "pyramid", "clause": "area", "expect": expect,
                    "status": r.status, "code": r.code, "reason": None if r.status == "SERVED" else (r.reason or "")[:240]})
    return out


def volume_cases() -> list[dict]:
    """The `_khoi_khop` path (volume question) on the same fixtures: kind-only wording, one solid."""
    out = []
    for rid, word, expect in (("right-base", "lăng trụ đứng", "SERVED"), ("right-base", "khối lăng trụ", "SERVED"),
                              ("right-base", "khối lập phương", "REFUSED"), ("right-base", "khối hộp", "REFUSED"),
                              ("right-base", "khối chóp", "REFUSED"), ("oblique-base", "lăng trụ đứng", "REFUSED"),
                              ("cuboid-base", "khối hộp chữ nhật", "SERVED"), ("cuboid-base", "khối lập phương", "REFUSED"),
                              ("cube-diagonal", "khối lập phương", "SERVED"), ("cube-diagonal", "khối hộp", "SERVED")):
        row = deepcopy(ROW[rid])
        fs = [f for f in row["payload"]["facts"] if f["id"] not in ("sec", "q")]
        quote = f"Tính thể tích {word}."
        fs.append(dict(id="volume", kind="question", role="question", quotes=[quote], quantity="volume",
                       solid=next(f["solid"] for f in fs if f["id"] == "solid")))
        source = " ".join(dict.fromkeys(q for f in fs for q in f["quotes"]))
        out.append({"id": f"{rid}|volume|{word}", "class": "kind_only", "clause": "volume", "expect": expect,
                    **_run({"text": source, "payload": {"facts": fs}})})
    # two solids, kind-only area wording: which solid is meant is not determined by the source -> refuse
    row = deepcopy(ROW["right-base"])
    extra = "Cho lăng trụ đứng DEF.D'E'F'."
    row["text"] = extra + " " + row["text"]
    row["payload"]["facts"].append({"id": "solid2", "kind": "solid", "role": "premise", "quotes": [extra],
                                    "solid": "DEF.D'E'F'", "solid_type": "prism", "right": True})
    for word in ("lăng trụ đứng", "lăng trụ"):
        r2 = _edit(row, _prism_area("right-base", PRISMS["right-base"]), _prism_area("right-base", word))
        r2 = _edit(r2, _prism_sec("right-base", PRISMS["right-base"]), _prism_sec("right-base", word))
        out.append({"id": f"two-prisms|both|{word}", "class": "multi_solid", "clause": "both", "expect": "REFUSED",
                    **_run(r2)})
    return out


def main(out: Path) -> None:
    rows = prism_cases() + pyramid_cases() + volume_cases()
    for r in rows:
        r["agree"] = r["status"] == r["expect"]
        r["kind"] = ("FAIL_OPEN" if r["status"] == "SERVED" and r["expect"] == "REFUSED" else
                     "FALSE_REFUSAL" if r["status"] != "SERVED" and r["expect"] == "SERVED" else "OK")
    agg = {"cases": len(rows), "agree": sum(r["agree"] for r in rows),
           "fail_open": [r["id"] for r in rows if r["kind"] == "FAIL_OPEN"],
           "false_refusal": [{"id": r["id"], "code": r["code"]} for r in rows if r["kind"] == "FALSE_REFUSAL"]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"classification": "AUTHORED_DEVELOPMENT_NOT_HOLDOUT", "provider_calls": 0,
                               "aggregate": agg, "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
