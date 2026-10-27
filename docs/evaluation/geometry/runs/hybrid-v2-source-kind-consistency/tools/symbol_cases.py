# -*- coding: utf-8 -*-
"""Supplementary symbol + kind cases for run `hybrid-v2-source-kind-consistency` (AUTHORED_DEVELOPMENT_NOT_HOLDOUT).

Owner decision SOURCE_CONTRADICTION_MUST_FAIL_CLOSED: a correct solid symbol identifies the object; an explicit kind word
that contradicts that object's grounded identity must refuse. Expectations below were written BEFORE any run, from
geometry. The registered 124-case corpus (`../hybrid-v2-planner-premerge-review/tools/adversarial.py`) is reused unchanged;
this file only ADDS cases. Offline, 0 provider calls.

Run from `backend/`:  python <this file> <out.json>
"""
from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / "backend"))
_spec = importlib.util.spec_from_file_location(
    "premerge_adversarial", ROOT / "docs/evaluation/geometry/runs/hybrid-v2-planner-premerge-review/tools/adversarial.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

PR = A.PRISMS


def _both(rid: str, word: str, reverse: bool = False) -> dict:
    row = A._edit(A._edit(A.ROW[rid], A._prism_area(rid, PR[rid]), A._prism_area(rid, word)),
                  A._prism_sec(rid, PR[rid]), A._prism_sec(rid, word))
    if reverse:
        row["payload"]["facts"].reverse()
    return row


def _volume(rid: str, word: str) -> dict:
    row = deepcopy(A.ROW[rid])
    fs = [f for f in row["payload"]["facts"] if f["id"] not in ("sec", "q")]
    quote = f"Tính thể tích {word}."
    fs.append(dict(id="volume", kind="question", role="question", quotes=[quote], quantity="volume",
                   solid=next(f["solid"] for f in fs if f["id"] == "solid")))
    return {"text": " ".join(dict.fromkeys(q for f in fs for q in f["quotes"])), "payload": {"facts": fs}}


def _cube_dims_cuboid() -> dict:
    """The 'hình hộp chữ nhật' fixture with AB = AD = AA' = 4: a cube metrically, but the gate reads no lengths."""
    row = A.ROW["cuboid-base"]
    for old, new in (("AB = 6.", "AB = 4."), ("AD = 8.", "AD = 4."), ("AA' = 12.", "AA' = 4.")):
        row = A._edit(row, old, new)
    for f in row["payload"]["facts"]:
        if f["id"] in ("ab", "ad", "height"):
            f["value"] = "4"
    return row


def _two_solids(word: str) -> dict:
    """Two source-grounded solids in one chart: root prism ABC.A'B'C' and derived pyramid M.ABC (`len(khoi) == 2`)."""
    row = deepcopy(A.ROW["right-base"])
    extra = "Cho hình chóp M.ABC."
    row["text"] = extra + " " + row["text"]
    row["payload"]["facts"].append({"id": "solid2", "kind": "solid", "role": "premise", "quotes": [extra],
                                    "solid": "M.ABC", "solid_type": "pyramid"})
    return A._edit(A._edit(row, A._prism_area("right-base", PR["right-base"]), A._prism_area("right-base", word)),
                   A._prism_sec("right-base", PR["right-base"]), A._prism_sec("right-base", word))


#: (id, builder, expectation, class)
CASES = [
    # correct symbol + compatible generic / specific kind
    ("sym-generic|right|lăng trụ", lambda: _both("right-base", "lăng trụ ABC.A'B'C'"), "SERVED", "symbol_compatible"),
    ("sym-generic|right|khối lăng trụ đứng", lambda: _both("right-base", "khối lăng trụ đứng ABC.A'B'C'"), "SERVED", "symbol_compatible"),
    ("sym-generic|cuboid|hình hộp", lambda: _both("cuboid-base", "hình hộp ABCD.A'B'C'D'"), "SERVED", "symbol_compatible"),
    ("sym-generic|cube|hình hộp chữ nhật", lambda: _both("cube-diagonal", "hình hộp chữ nhật ABCD.A'B'C'D'"), "SERVED", "symbol_compatible"),
    ("sym-generic|cube|lăng trụ đứng", lambda: _both("cube-diagonal", "lăng trụ đứng ABCD.A'B'C'D'"), "SERVED", "symbol_compatible"),
    ("sym-generic|oblique|lăng trụ", lambda: _both("oblique-base", "lăng trụ ABC.A'B'C'"), "SERVED", "symbol_compatible"),
    # correct symbol, no kind word
    ("sym-nokind|right", lambda: _both("right-base", "ABC.A'B'C'"), "SERVED", "symbol_no_kind"),
    # correct symbol + contradictory specific kind
    ("sym-specific|right|hình hộp", lambda: _both("right-base", "hình hộp ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    ("sym-specific|right|lăng trụ tứ giác", lambda: _both("right-base", "lăng trụ tứ giác ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    ("sym-specific|right|lăng trụ tam giác đều", lambda: _both("right-base", "lăng trụ tam giác đều ABC.A'B'C'"), "REFUSED", "insufficient_evidence"),
    ("sym-specific|oblique|lăng trụ đứng", lambda: _both("oblique-base", "lăng trụ đứng ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    ("sym-specific|oblique|hình hộp chữ nhật", lambda: _both("oblique-base", "hình hộp chữ nhật ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    ("sym-specific|cuboid|lăng trụ tứ giác đều", lambda: _both("cuboid-base", "lăng trụ tứ giác đều ABCD.A'B'C'D'"), "REFUSED", "insufficient_evidence"),
    ("sym-specific|cuboid-4x4x4|hình lập phương", lambda: A._edit(A._edit(_cube_dims_cuboid(),
        A._prism_area("cuboid-base", PR["cuboid-base"]), A._prism_area("cuboid-base", "hình lập phương ABCD.A'B'C'D'")),
        A._prism_sec("cuboid-base", PR["cuboid-base"]), A._prism_sec("cuboid-base", "hình lập phương ABCD.A'B'C'D'")),
     "REFUSED", "insufficient_evidence"),
    ("sym-specific|cuboid-4x4x4|hình hộp chữ nhật", lambda: _cube_dims_cuboid(), "SERVED", "symbol_compatible"),
    # correct symbol + contradictory generic family
    ("sym-family|right|hình chóp", lambda: _both("right-base", "hình chóp ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    ("sym-family|cube|tứ diện", lambda: _both("cube-diagonal", "tứ diện ABCD.A'B'C'D'"), "REFUSED", "symbol_contradiction"),
    # fact-order permutation of a contradiction and of a compatible symbol
    ("sym-reversed|cuboid|hình lập phương", lambda: _both("cuboid-base", "hình lập phương ABCD.A'B'C'D'", True), "REFUSED", "symbol_contradiction"),
    ("sym-reversed|cube|hình lập phương", lambda: _both("cube-diagonal", "hình lập phương ABCD.A'B'C'D'", True), "SERVED", "symbol_compatible"),
    # volume question with a symbol
    ("vol-sym|right|khối lập phương", lambda: _volume("right-base", "khối lập phương ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    ("vol-sym|right|khối chóp", lambda: _volume("right-base", "khối chóp ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    ("vol-sym|right|khối lăng trụ", lambda: _volume("right-base", "khối lăng trụ ABC.A'B'C'"), "SERVED", "symbol_compatible"),
    ("vol-sym|cuboid|khối lập phương", lambda: _volume("cuboid-base", "khối lập phương ABCD.A'B'C'D'"), "REFUSED", "symbol_contradiction"),
    ("vol-sym|cuboid|khối hộp chữ nhật", lambda: _volume("cuboid-base", "khối hộp chữ nhật ABCD.A'B'C'D'"), "SERVED", "symbol_compatible"),
    ("vol-sym|cube|khối lập phương", lambda: _volume("cube-diagonal", "khối lập phương ABCD.A'B'C'D'"), "SERVED", "symbol_compatible"),
    ("vol-sym|oblique|khối lăng trụ đứng", lambda: _volume("oblique-base", "khối lăng trụ đứng ABC.A'B'C'"), "REFUSED", "symbol_contradiction"),
    # two solids (`ABC.A'B'C'` and `M.ABC`): symbol isolates the cut solid; bare word or wrong kind/symbol must refuse
    ("multi|sym-right", lambda: _two_solids("lăng trụ đứng ABC.A'B'C'"), "SERVED", "multi_solid"),
    ("multi|sym-other", lambda: _two_solids("hình chóp M.ABC"), "REFUSED", "multi_solid"),
    ("multi|sym-right-cube-word", lambda: _two_solids("hình lập phương ABC.A'B'C'"), "REFUSED", "multi_solid"),
    ("multi|sym-right-pyramid-word", lambda: _two_solids("hình chóp ABC.A'B'C'"), "REFUSED", "multi_solid"),
    ("multi|bare-without-symbol", lambda: _two_solids("lăng trụ đứng"), "REFUSED", "multi_solid"),
]


def main(out: Path) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    for cid, build, expect, cls in CASES:
        r = A._run(build())
        rows.append({"id": cid, "class": cls, "expect": expect, **r,
                     "kind": ("FAIL_OPEN" if r["status"] == "SERVED" and expect == "REFUSED" else
                              "FALSE_REFUSAL" if r["status"] != "SERVED" and expect == "SERVED" else "OK")})
    agg = {"cases": len(rows), "agree": sum(r["kind"] == "OK" for r in rows),
           "fail_open": [r["id"] for r in rows if r["kind"] == "FAIL_OPEN"],
           "false_refusal": [{"id": r["id"], "code": r["code"]} for r in rows if r["kind"] == "FALSE_REFUSAL"]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"classification": "AUTHORED_DEVELOPMENT_NOT_HOLDOUT", "provider_calls": 0,
                               "aggregate": agg, "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
