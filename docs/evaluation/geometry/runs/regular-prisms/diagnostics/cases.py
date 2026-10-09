# -*- coding: utf-8 -*-
"""regular-prisms — shared cases: contract + model-style program per labelled row (0 model calls).

Base declared in an AFFINE lattice chart (60° basis): hexagon centre (1, 1) with vertices O±u, O±v, O±(v−u); triangle
(0,0), (1,0), (0,1). Top = base + (0, 0, 1). Regular only under the metric the product derives from the text. Used by
probe.py and backend/tests/geometry/test_regular_prisms.py."""
from __future__ import annotations

import json
import re
from pathlib import Path

LABELS = json.loads((Path(__file__).resolve().parents[1] / "labels.json").read_text(encoding="utf-8"))["rows"]
BASES = {
    6: [(2, 1), (1, 2), (0, 2), (0, 1), (1, 0), (2, 0)],
    3: [(0, 0), (1, 0), (0, 1)],
    5: [(2, 0), (3, 2), (1, 3), (-1, 2), (0, 0)],
}
NHAN = {"base": "cạnh đáy", "height": "chiều cao", "lateral": "cạnh bên"}


def _ten(p: str) -> str:
    return p.replace("'", "_prime")


def hop_dong_va_chuong_trinh(rid: str):
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    r = LABELS[rid]
    day, tren, k = r["base"], r["top"], r["k"]
    base = [(*xy, 0) for xy in BASES[k]]
    if r["program"] == "irregular_base":
        base[0] = (3, 1, 0)
    top = [(x, y, 1) for x, y, _ in base]
    if r["program"] == "top_not_translation":
        top[-1] = (top[-1][0] + 1, top[-1][1], 1)
    facts = [{"id": f"f_{key}", "kind": "float", "label": NHAN[key], "value": [v]} for key, v in r["dims"].items()]
    khoi = f"{''.join(day)}.{''.join(tren)}"
    payload = {"input_facts": [{"id": "f_khoi", "kind": "str", "label": "Khối lăng trụ", "value": [khoi]}, *facts],
               "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}],
               # vertex universe for grounding of LAYOUT_DERIVED points (as every prism corpus); not regularity evidence
               "solid_topology": {"solid_kind": "prism", "base_cycle": day, "top_cycle": tren,
                                  "correspondence": [[a, b] for a, b in zip(day, tren)]}}
    contract = build_request_contract(payload, problem_text=r["text"], domain="hinh_hoc")
    D, T = [_ten(p) for p in day], [_ten(p) for p in tren]
    mem = [{"name": f"g_{key}", "type": "float", "provenance": "GIVEN", "source_fact_id": f"f_{key}",
            "initial_value": v} for key, v in r["dims"].items() if re.fullmatch(r"[\d/]+", v)]
    mem += [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in (*D, *T)]
    mem += [{"name": "khoi", "type": "solid"}, {"name": "V", "type": "float"}]
    st = [{"kind": "declare_point", "target_var": p, "at": [str(c) for c in xyz]}
          for p, xyz in (*zip(D, base), *zip(T, top))]
    st += [{"kind": "construct_solid", "target_var": "khoi", "vertices": [*D, *T],
            "faces": [D, T[::-1]] + [[D[i], D[(i + 1) % k], T[(i + 1) % k], T[i]] for i in range(k)], "label": khoi},
           {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}]
    prog = {"spec_version": "1.0", "title": f"Lăng trụ {khoi}", "memory_declarations": mem, "statements": st}
    return contract, SemanticProgramSpec.model_validate(prog)
