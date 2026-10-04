# -*- coding: utf-8 -*-
"""W20 — fault injections for amendment §16.5 (a text-relation target defined by coordinates), pytest plugin,
0 model calls.

`W20_FI=<id>` selects ONE exact source substitution applied IN MEMORY (the file on disk is never touched),
with the W15 mechanism (`w15-assumption-closure/diagnostics/fault_injection_w15._tiem`: the text must match
exactly once, or the run aborts — a stale injection never passes silently).
`W20_STAGES=<file>` also writes the route stage of every W20 LABELS row under the injection: the success
criterion of FL8/FL9 (grounding guards removed) is that NOTHING turns red because `construction_binding`
still refuses those rows — the stages show that the refusal moved there.

    W20_FI=FL1 PYTHONPATH=<this dir> python -m pytest -p fault_injection_w20 <tests>

Driver: `run_fault_injections_w20.py` (same directory).
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "w15-assumption-closure" / "diagnostics"))
from fault_injection_w15 import _tiem  # noqa: E402

SP = "app.simulation.semantic_program."
BIND, ROUTE, GROUND, MSG = SP + "construction_binding", SP + "route", SP + "grounding_gate", "app.learner_messages"
#: ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE. Under an FE injection the module constant RECONCILIATION_DIR is
#: pointed at a TEMPORARY COPY of the frozen folder after the swap, so an injected write never reaches evidence.
RECON = "reconcile_second_family_live_measurement"
_VONG = "        if len(k) != 1 or not any(map(dt.toa_do, chuoi)):\n"

#: id → (module, old text, new text, what it simulates, predicted outcome)
INJECTIONS: dict[str, tuple[str, str, str, str, str]] = {
    "FL1": (BIND, _VONG, "        if True:\n",
            "§16.5 removed: a relation target defined by coordinates gets no status",
            "CAUGHT — L10–L14 and L16–L18 served or refused by the assumption gate again"),
    "FL2": (BIND, "        chuoi = dt.chuoi(n)\n", "        chuoi = [n]\n",
            "the alias chain is not followed (only the name's own coordinates count)",
            "CAUGHT — L17 (H = var A) and L18 (H = var Q, Q by coordinates)"),
    "FL3": (BIND, '        return m.get("type") == "point3" and not _is_seed(m.get("initial_value"))\n',
            '        return m.get("type") == "point3"\n',
            "a declaration WITHOUT coordinates counted as coordinates (over-refusal)",
            "CAUGHT — declared-then-constructed and W18 B8 (alias of a constructed point) refused"),
    "FL4": (BIND, "        R = qh[k.pop()]\n",
            "        R = qh[k.pop()]\n"
            '        if any(_so(R, _quan_he_ct(s["expr"], dt))[0] == MATCHED for s in dung if s["target_var"] != n):\n'
            "            continue\n",
            "a matching construction under ANOTHER name excuses the coordinates (equal coordinates as identity)",
            "CAUGHT — L15 at the binding level and the projection twin (H by coordinates, K constructed)"),
    "FL5": (ROUTE, "        if dc.reason_code in (MA_LECH_PHEP_DUNG, MA_TOA_DO_THAY_DUNG) or (\n",
            "        if dc.reason_code == MA_LECH_PHEP_DUNG or (\n",
            "the route records the status but does not refuse",
            "CAUGHT — every route-level §16.5 test"),
    "FL6": (MSG, '    return cau + " đúng là điểm đề nói. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm chứng."'
                 " + _DUOI_LOI_HE\n",
            '    return cau + "." + _DUOI_LECH_PHEP_DUNG\n',
            "the learner told the answer is on a different figure instead of 'not verifiable'",
            "CAUGHT — the two pipeline-boundary message tests"),
    "FL7": (BIND, _VONG,
            '        if len(k) != 1 or not any(map(dt.toa_do, chuoi)) or n in {s["target_var"] for s in dung}:\n',
            "a construction of the SAME name excuses its earlier coordinates",
            "CAUGHT — L16 (coordinates, then midpoint(S, A))"),
    "FL8": (GROUND, "        if (decl.initial_value is not None\n"
                    "                and _diem_phai_dung(contract) & chuan_hoa_ten(decl.name)):\n",
            "        if False:\n",
            "grounding guard ⑦ (division/midpoint targets) removed — defense in depth",
            "NOT CAUGHT — L2–L4 and L6–L8 still refused, now by construction_binding (stages)"),
    "FL9": (GROUND, "            elif la_ten_suy_ra(decl.name, contract.problem_text):\n",
            "            elif False:\n",
            "grounding guard ⑥ (text-introduced point declared by coordinates) removed — defense in depth",
            "NOT CAUGHT — L9 still refused, now by construction_binding (stages)"),
    "FE1": (RECON, "    if out_dir.resolve() == RECONCILIATION_DIR.resolve():\n", "    if False:\n",
            "the frozen reconciliation folder accepted as an output folder",
            "CAUGHT — test_w20_reconciliation_refuses_the_frozen_folder"),
    "FE2": (RECON, "    out_dir = Path(out_dir)\n    if out_dir.resolve() == RECONCILIATION_DIR.resolve():\n",
            "    out_dir = RECONCILIATION_DIR\n    if False:\n",
            "the pre-W20 behaviour: the four outputs written into the frozen folder whatever out_dir says",
            "CAUGHT — test_w20_reconciliation_writes_only_to_its_explicit_output_folder and the refusal test"),
}
_BAN_SAO: list[str] = []


def pytest_sessionstart(session):
    fi = os.environ.get("W20_FI")
    if fi:
        ten, cu, moi, *_ = INJECTIONS[fi]
        sys.path.insert(0, str(HERE.parents[5] / "backend" / "scripts"))
        for m in (ROUTE, "app.ai.pipeline", MSG, BIND, GROUND, ten):   # bind importers before the swap
            importlib.import_module(m)
        _tiem(ten, cu, moi)
        if ten == RECON:
            import shutil
            import tempfile

            m = sys.modules[RECON]
            _BAN_SAO.append(tempfile.mkdtemp(prefix="w20-fe-"))
            m.RECONCILIATION_DIR = Path(shutil.copytree(m.RECONCILIATION_DIR, Path(_BAN_SAO[0]) / "frozen-copy"))
    ra = os.environ.get("W20_STAGES")
    if ra:
        from tests.geometry import test_construction_binding_literal as T20
        from tests.geometry import w14_cases as W

        stages = {}
        for ca in sorted(T20.CA):
            _sp, o, _sc = W.chay(*T20.CA[ca]())
            stages[ca] = [o.stage_reached, o.reason_code, o.servable]
        Path(ra).write_text(json.dumps(stages, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def pytest_sessionfinish(session, exitstatus):
    import shutil

    for d in _BAN_SAO:
        shutil.rmtree(d, ignore_errors=True)
