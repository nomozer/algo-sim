# -*- coding: utf-8 -*-
"""c0-whole-solid-grounding — shared C0 cases (text pins every vertex by coordinates) + the LLM-style program that
declares those points from their facts, builds the solid and measures its volume. 0 model calls.

Used by the probe (`probe.py`, run on any tree from its backend/ directory) and by
`backend/tests/geometry/test_c0_whole_solid_grounding.py`. Labels: `../labels.json`."""
from __future__ import annotations

import json
from pathlib import Path

LABELS = json.loads((Path(__file__).resolve().parents[1] / "labels.json").read_text(encoding="utf-8"))["rows"]


def toa_do(P: dict) -> str:
    return ", ".join(f"{k}({';'.join(map(str, v))})" for k, v in P.items())


def hop_dong_va_chuong_trinh(rid: str):
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    r = LABELS[rid]
    pts, s = r["points"], r["solid"]
    text = r["text"].replace("{coords}", toa_do(pts))
    payload = {"input_facts": [{"id": f"d_{p.replace(chr(39), 'p')}", "kind": "point3", "label": p,
                                "value": [f"({';'.join(map(str, v))})"]} for p, v in pts.items()],
               "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}]}
    contract = build_request_contract(payload, problem_text=text, domain="hinh_hoc")
    ten = {p: p.replace("'", "_prime") for p in pts}
    day = s["base"]
    k = len(day)
    if s["kind"] == "pyramid":
        dinh = [s["apex"], *day]
        mat = [list(day)] + [[s["apex"], day[i], day[(i + 1) % k]] for i in range(k)]
    else:
        tren = s["top"]
        dinh = [*day, *tren]
        mat = [list(day), list(tren)] + [[day[i], day[(i + 1) % k], tren[(i + 1) % k], tren[i]] for i in range(k)]
    an = set(r.get("omit_from_program", []))
    khai = [{"name": ten[p], "type": "point3", "initial_value": [str(c) for c in pts[p]],
             "source_fact_id": f"d_{p.replace(chr(39), 'p')}"} for p in pts if p not in an]
    sp = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Thể tích khối đa diện",
        "memory_declarations": khai + [{"name": "khoi", "type": "solid"}, {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "khoi", "vertices": [ten[p] for p in dinh],
             "faces": [[ten[p] for p in f] for f in mat]},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}]})
    return text, contract, sp
