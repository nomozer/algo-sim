# -*- coding: utf-8 -*-
"""regular-prisms — transition probe beyond the 25 labelled rows (cache decision input). Run from backend/ on any tree.

Two families the slice could move: (1) C0 — the text pins every vertex by rational coordinates and calls the prism
"tam giác đều" / "lục giác đều" (right and skewed lateral direction; stated lateral edge / base side); (2) Euclidean layout — a model-style program with a
Euclidean (not lattice) equilateral base and a translated top, text with / without a height. 0 model calls."""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

RUNS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUNS / "regular-prisms" / "diagnostics"))
sys.path.insert(0, str(RUNS / "c0-whole-solid-grounding" / "diagnostics"))

from app.ai.pipeline import _dung_scene3d  # noqa: E402
from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter  # noqa: E402
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

import c0_whole_solid_cases as M  # noqa: E402
import cases  # noqa: E402

HEX = {"A": [1, -1, 0], "B": [1, 0, -1], "C": [0, 1, -1], "D": [-1, 1, 0], "E": [-1, 0, 1], "F": [0, -1, 1]}
TRI = {"A": [1, 0, 0], "B": [0, 1, 0], "C": [0, 0, 1]}
PHRASE = {"tri": "lăng trụ tam giác đều", "hex": "lăng trụ lục giác đều", "tri_right": "lăng trụ đứng",
          "hex_right": "lăng trụ đứng"}


def _ket(out, value) -> dict:
    return {"servable": out.servable, "stage": out.stage_reached, "reason": out.reason_code,
            "certificate": out.assumption_certificate, "value": value}


def c0(rid: str, base: dict, shift: list, phrase: str, suffix: str = "") -> None:
    pts = {**base, **{p + "'": [a + b for a, b in zip(v, shift)] for p, v in base.items()}}
    n, t = "".join(base), "".join(p + "'" for p in base)
    M.LABELS[rid] = {"text": f"Cho hình {phrase} {n}.{t}{suffix} với {{coords}}. Tính thể tích khối lăng trụ {n}.{t}.",
                     "points": pts, "solid": {"kind": "prism", "base": list(base), "top": [p + "'" for p in base]}}
    _de, c, sp = M.hop_dong_va_chuong_trinh(rid)
    out = verify_and_compile(c, sp)
    v = str(Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"]))) if out.servable else None
    print(json.dumps({"row": rid, **_ket(out, v)}, ensure_ascii=False))


def euclid(rid: str, text: str) -> None:
    cases.LABELS[rid] = {**cases.LABELS["T1_side_height"], "text": text, "dims": {}}
    c, sp = cases.hop_dong_va_chuong_trinh(rid)
    p = sp.model_dump(mode="json", exclude_none=True)
    ten = ["A", "B", "C", "A_prime", "B_prime", "C_prime"]
    for m in p["memory_declarations"]:
        if m["type"] == "point3":
            i = ten.index(m["name"])
            m["initial_value"] = [str(x + (i >= 3)) for x in list(TRI.values())[i % 3]]
    sp = SemanticProgramSpec.model_validate(p)
    out = verify_and_compile(c, sp)
    v = next(o["value"] for o in _dung_scene3d(sp, c)["objects"] if o["id"] == "V") if out.servable else None
    print(json.dumps({"row": rid, **_ket(out, v)}, ensure_ascii=False))


if __name__ == "__main__":
    for nm, base in (("hex", HEX), ("tri", TRI)):
        c0(f"C0_{nm}_right", base, [1, 1, 1], PHRASE[nm])
        c0(f"C0_{nm}_skew", base, [1, 1, 0] if nm == "hex" else [2, 1, 0], PHRASE[nm])
        kind = "lục giác đều" if nm == "hex" else "tam giác đều"
        c0(f"C0_{nm}_right_prism_phrase", base, [1, 1, 1], "lăng trụ đứng", f" có đáy {''.join(base)} là {kind}")
        c0(f"C0_{nm}_plain_prism_skew", base, [1, 1, 0] if nm == "hex" else [2, 1, 0], "lăng trụ")
        c0(f"C0_{nm}_lateral_matches", base, [1, 1, 1], PHRASE[nm], " có cạnh bên bằng √3")
        c0(f"C0_{nm}_lateral_contradicts", base, [1, 1, 1], PHRASE[nm], " có cạnh bên bằng 2")
        c0(f"C0_{nm}_base_side_contradicts", base, [1, 1, 1], PHRASE[nm], " có cạnh đáy bằng 1")
    q = "Tính thể tích khối lăng trụ ABC.A'B'C'."
    euclid("EU_height_matches", f"Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng √2, chiều cao bằng √3. {q}")
    euclid("EU_height_differs", f"Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng √2, chiều cao bằng 2√3. {q}")
    euclid("EU_missing_height", f"Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng √2. {q}")
    euclid("EU_right_prism_phrase", "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh √2, cạnh bên "
           f"bằng √3. {q}")
