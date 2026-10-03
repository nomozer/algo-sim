# -*- coding: utf-8 -*-
"""W15 Task 6 — fault injections for the assumption gate (pytest plugin, 0 model calls).

`W15_FI=<id>` selects ONE injection: an exact source substitution applied IN MEMORY to one
product module (the file on disk is never touched). The substitution must match exactly
once, or the run aborts — a stale injection never passes silently. Names the patched module
exported are rebound in every loaded module that imported them by name (`from x import f`).

    W15_FI=FI2 PYTHONPATH=<this dir> python -m pytest -p fault_injection_w15 <tests>

Driver: `run_fault_injections_w15.py` (same directory) → `logs/FAULT_INJECTION_ASSUMPTION_GATE.log`.
"""
from __future__ import annotations

import importlib
import os
import sys

GATE = "app.simulation.semantic_program.assumption_gate"
READER = "app.simulation.semantic_program.shape_constraint"
ROUTE = "app.simulation.semantic_program.route"

#: id → (module, old text, new text, what it simulates, predicted catch)
INJECTIONS: dict[str, tuple[str, str, str, str, str]] = {
    "FI1": (GATE,
            "    hong = [n for n, g in khuon.rang_buoc + _ap_do_dai(khuon, do_dai) if not g(V2)]\n"
            "    if hong:\n        return None, f\"CE_INVALID breaks {hong[0]}\"",
            "    hong = []\n    if hong:\n        return None, \"\"",
            "CE validity ignores the template's shape constraints and stated lengths",
            "a false DEPENDENT returns (W15 expectation: MASKED — the stretch maps keep every template "
            "constraint by construction (amendment §7) and the same validity rule re-checks stated "
            "lengths through the text invariants)"),
    "FI2": (GATE,
            "if i.kind == \"point_coordinate\" and [_khoa(p) for p in i.points] == [_khoa(lit[1])]:",
            "if False:",
            "C0 back to class-B-only: a text coordinate never pins a point literal",
            "the 8 coordinate rows lose C0"),
    "FI3": (GATE,
            "              if i.kind == \"segment_length\" and len(i.points) == 2 and i.expected}",
            "              if i.kind == \"segment_length\" and len(i.points) == 2 and i.expected}\n"
            "    do_dai.update({frozenset(_id(p) for p in mm.groups()): _F(m[\"initial_value\"])\n"
            "                   for m in prog[\"memory_declarations\"]\n"
            "                   if (mm := _TEN_DO_DAI.fullmatch(m[\"name\"])) and m.get(\"initial_value\") is not None})",
            "given-dimension / CE-validity evidence also reads the program's own XY_length literals",
            "adversarial (1)/AC1 lose their counterexample"),
    "FI4": (GATE,
            "            details.append(f\"{khuon.loai} MISSING {kt.nhan}: {ly_do}\")\n"
            "        return _ket_qua(UNDETERMINED, details + tien_de)",
            "            details.append(f\"{khuon.loai} MISSING {kt.nhan}: {ly_do}\")\n"
            "        return _ket_qua(PROVEN_SAFE, details + tien_de, certificate=\"C1\")",
            "an inconclusive counterexample search is treated as safe",
            "adversarial (2)/(6) served"),
    "FI5": (GATE,
            "    rb = doc_rang_buoc(de)\n",
            "    rb = doc_rang_buoc(de)\n"
            "    rb = rb + tuple(RangBuoc(\"right_prism\", x.entities, None, (0, 0)) for x in rb\n"
            "                    if x.kind == \"prism\" and any(r.kind == \"perpendicular_line_plane\"\n"
            "                                                   for r in contract.geometric_relations))\n",
            "server confirmation replaced by the model's relation annotation",
            "test (10) text-silent variants get C1"),
    "FI6": (GATE,
            "        tinh, dong = self.tinh.get(n, []), self.dong.get(n, [])\n",
            "        tinh, dong = self.tinh.get(n, []), self.dong.get(n, [])\n"
            "        if tinh:\n"
            "            return _DinhNghia(tinh[-1][0], tinh[-1][1],\n"
            "                              dong[-1].memory_snapshot.get(n) if dong else self.dau.get(n))\n",
            "reaching definitions replaced by the final (last-written) value",
            "overwrite/alias/restore cases get certified"),
    "FI7": (GATE,
            "    if loai == \"ti_so\":\n",
            "    if loai == \"ti_so\":\n        return \"SOURCE_DATUM\"\n",
            "role check replaced by dimensional analysis alone (a ratio is dimensionless)",
            "the unstated division ratio gets certified"),
    "FI8": (GATE, "        if chua_doc or ngoai:\n", "        if ngoai:\n",
            "the fully-read rule is removed from the counterexample",
            "the unread-text texts get DEPENDENT again"),
    "FI9": (GATE, "        if chua_doc or ngoai:\n", "        if chua_doc:\n",
            "read constraints outside the template's premises are not required",
            "AC ⊥ BD on a rectangle base gets DEPENDENT again"),
    "FI10": (GATE, "    return geometry_symbol_key(str(x)) or _id(x)\n", "    return _id(x)\n",
             "program names bound to text entities without the symbol key",
             "A1/Aprime spellings lose C1"),
    "FI11": (ROUTE, "            gd_chan = neu_khoi_da_dien(contract.problem_text)\n",
             "            gd_chan = True\n",
             "the gate refuses everywhere (U3 scope removed)",
             "the out-of-scope segment problem is refused"),
    "FI12": (READER, "_TAI = r\"(?:tại|ở\\s+đỉnh|ở|đỉnh)\"", "_TAI = r\"(?:tại)\"",
             "the right-angle phrasings added by U4 · G1 are removed",
             "the G1 phrasing tests fail"),
    "FI13": (GATE,
             "        if [k for k, _ in tinh] == [\"khai\", \"cau_lenh\"] and len(dong) == 1 "
             "and not self._doc_truoc(n, tinh[1][1]):\n",
             "        if False:\n",
             "U5 refinement removed: a declared literal overwritten by its own construction counts twice",
             "the B3 idiom is flagged as multiple definitions"),
    "FI14": (ROUTE,
             "    gd_chan = gd_chan or any(d.startswith(MA_NHIEU_DINH_NGHIA) for d in gd_chi_tiet)\n",
             "",
             "multiple definitions refused only inside the polyhedral scope (U5 removed)",
             "the overwrite/alias cases on the planar rhombus are served"),
}


def _tiem(ten_module: str, cu: str, moi: str) -> None:
    m = importlib.import_module(ten_module)
    src = open(m.__file__, encoding="utf-8").read()
    if src.count(cu) != 1:
        raise SystemExit(f"FAULT INJECTION STALE: {cu[:60]!r} found {src.count(cu)}x in {ten_module}")
    truoc = dict(vars(m))
    exec(compile(src.replace(cu, moi), m.__file__, "exec"), vars(m))
    doi = {id(v): vars(m)[k] for k, v in truoc.items() if k in vars(m) and vars(m)[k] is not v}
    for mod in list(sys.modules.values()):
        if mod is m or not hasattr(mod, "__dict__"):
            continue
        for k, v in list(vars(mod).items()):
            if id(v) in doi:
                setattr(mod, k, doi[id(v)])


def pytest_sessionstart(session):
    fi = os.environ.get("W15_FI")
    if fi:
        ten, cu, moi, *_ = INJECTIONS[fi]
        importlib.import_module(ROUTE)            # bind importers before the swap
        _tiem(ten, cu, moi)
