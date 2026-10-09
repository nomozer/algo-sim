# -*- coding: utf-8 -*-
"""regular-hexagonal-pyramid — shared cases: contract + model-style program for each labelled row (0 model calls).

The base is declared in an AFFINE chart (lattice basis u, v at 60° in the Euclidean figure): centre O = (1, 1, 0),
vertices O+u, O+v, O+v−u, O−u, O−v, O+u−v — rational, and regular only under the metric the product derives from the
text. The apex is declared above O. Used by probe.py and backend/tests/geometry/test_regular_hexagonal_pyramid.py."""
from __future__ import annotations

import json
import re
from pathlib import Path

LABELS = json.loads((Path(__file__).resolve().parents[1] / "labels.json").read_text(encoding="utf-8"))["rows"]
HEX = [(2, 1, 0), (1, 2, 0), (0, 2, 0), (0, 1, 0), (1, 0, 0), (2, 0, 0)]
LAYOUT = {
    "regular": (HEX, (1, 1, 1)),
    "apex_over_vertex": (HEX, (2, 1, 1)),
    "irregular_base": ([(3, 1, 0), (1, 2, 0), (0, 2, 0), (0, 1, 0), (1, 0, 0), (2, 0, 0)], (1, 1, 1)),
    "pentagon": ([(2, 0, 0), (3, 2, 0), (1, 3, 0), (-1, 2, 0), (0, 0, 0)], (1, 1, 1)),
}
NHAN = {"base": "cạnh đáy", "height": "chiều cao", "lateral": "cạnh bên"}


def hop_dong_va_chuong_trinh(rid: str):
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    r = LABELS[rid]
    S, day = r["names"][0], list(r["names"][1:])
    base, apex = LAYOUT[r["program"]]
    k = len(day)
    facts = [{"id": f"f_{key}", "kind": "float", "label": NHAN[key], "value": [v]} for key, v in r["dims"].items()]
    ask = ({"kind": "volume", "container": "khoi", "witness": "V"} if r["ask"] == "volume"
           else {"kind": "distance", "container": day[0], "witness": "d_SA", "wrt": S})
    payload = {"input_facts": [{"id": "f_khoi", "kind": "str", "label": "Khối chóp", "value": [f"{S}.{''.join(day)}"]},
                               *facts], "obligations": [ask],
               # vertex universe for grounding of LAYOUT_DERIVED points (as every pyramid corpus); not regularity evidence
               "solid_topology": {"solid_kind": "pyramid", "apex": S, "base_cycle": day}}
    contract = build_request_contract(payload, problem_text=r["text"], domain="hinh_hoc")
    mem = [{"name": f"g_{key}", "type": "float", "provenance": "GIVEN", "source_fact_id": f"f_{key}",
            "initial_value": v} for key, v in r["dims"].items() if re.fullmatch(r"[\d/]+", v)]
    mem += [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in (S, *day)]
    mem += [{"name": "day", "type": "polygon3"}, {"name": "khoi", "type": "solid"},
            {"name": "V" if r["ask"] == "volume" else "d_SA", "type": "float"}]
    st = [{"kind": "declare_point", "target_var": p, "at": [str(c) for c in xyz]} for p, xyz in zip(day, base)]
    st += [{"kind": "declare_point", "target_var": S, "at": [str(c) for c in apex]},
           {"kind": "construct_polygon", "target_var": "day", "vertices": day, "label": f"Đáy {''.join(day)}"},
           {"kind": "construct_solid", "target_var": "khoi", "vertices": [S, *day],
            "faces": [day] + [[S, day[i], day[(i + 1) % k]] for i in range(k)], "label": f"{S}.{''.join(day)}"},
           {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}
           if r["ask"] == "volume" else
           {"kind": "assign", "target_var": "d_SA", "expr": {"kind": "measure", "quantity": "distance", "of": S,
                                                               "wrt": day[0]}}]
    prog = {"spec_version": "1.0", "title": f"Chóp {S}.{''.join(day)}", "memory_declarations": mem, "statements": st}
    return contract, SemanticProgramSpec.model_validate(prog)
