# -*- coding: utf-8 -*-
"""W18 — backend fault injections for the construction binding (§16.1–16.4), the learner messages and
the annotation data (§16.5–16.7) (pytest plugin, 0 model calls).

`W18_FI=<id>` selects ONE injection: an exact source substitution applied IN MEMORY to one module (the
file on disk is never touched), with the W15 mechanism (`w15-assumption-closure/diagnostics/
fault_injection_w15._tiem`: the substitution must match exactly once, or the run aborts — a stale
injection never passes silently).

    W18_FI=FB1 PYTHONPATH=<this dir> python -m pytest -p fault_injection_w18 <tests>

Driver: `run_fault_injections_w18.py` (same directory). The brief's minimum list maps to: SA→SB with the
same value = FB1 (B4: d(M, (ABCD)) = 3 either way); target changed with the same coordinates = FB2
(renamed target) and FB3 (one shared endpoint accepted: B9, H ≡ A in coordinates); binding check
removed = FB4. The frontend ones (label on the wrong subject, result too early, all labels on by
default, two detail panels, highlight turning dashed lines solid) are in the frontend driver.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "w15-assumption-closure" / "diagnostics"))
from fault_injection_w15 import _tiem  # noqa: E402

SP = "app.simulation.semantic_program."
BIND, ROUTE, ANN, SCENE = SP + "construction_binding", SP + "route", SP + "quantity_annotations", SP + "scene3d"
MSG = "app.learner_messages"

#: id → (module, old text, new text, what it simulates, predicted catch)
INJECTIONS: dict[str, tuple[str, str, str, str, str]] = {
    "FB1": (BIND, '        return (MATCHED, "same unordered endpoints") if th == R.toan_hang else (MISMATCHED, "other endpoints")\n',
            '        return (MATCHED, "same unordered endpoints")\n',
            "any midpoint accepted for the text's midpoint (SA→SB with the same value served)",
            "test_w18_tuyen_san_pham_theo_nhan[B2, B4, B5, B19] + binding statuses"),
    "FB2": (BIND, "            thay = [R for R in qh.values() if R.dich not in co and _so(R, p)[0] == MATCHED]\n",
            "            thay = []\n",
            "the text relation built under another name taken as an auxiliary point (renamed target)",
            "test_w18_tuyen_san_pham_theo_nhan[B7] + test_w18_trang_thai_doi_chieu_cua_phep_dung[B7]"),
    "FB3": (BIND, '        return (MATCHED, "same unordered endpoints") if th == R.toan_hang else (MISMATCHED, "other endpoints")\n',
            '        return (MATCHED, "same unordered endpoints") if th & R.toan_hang else (MISMATCHED, "other endpoints")\n',
            "one shared endpoint accepted (M = midpoint(S, A) for the text's midpoint of SH, H ≡ A in coordinates)",
            "test_w18_tuyen_san_pham_theo_nhan[B9, B2]"),
    "FB4": (ROUTE, "        if dc.reason_code == MA_LECH_PHEP_DUNG or (\n"
                   "                dc.reason_code == MA_CHUA_DOI_CHIEU and neu_khoi_da_dien(contract.problem_text)):\n",
            "        if False:\n",
            "the construction_binding stage removed from the route (statuses still recorded)",
            "test_w18_tuyen_san_pham_theo_nhan[every MUST_REFUSE row and B16]"),
    "FB5": (BIND, '    return (MATCHED, "same source and receiver") if _cung_nhan(R.toan_hang[1], nhan) else (MISMATCHED, "other receiver")\n',
            '    return (MATCHED, "same source and receiver")\n',
            "projection receiver not compared (foot on the wrong line or plane served)",
            "test_w18_tuyen_san_pham_theo_nhan[B11, B13]"),
    "FB6": (BIND, "            for x, (a, b) in zip(dich, doan):\n",
            "            for x, (a, b) in zip(dich, reversed(doan)):\n",
            "a 'lần lượt' list paired in reverse order",
            "test_w18_doc_trung_diem_mot_dich_va_danh_sach_lan_luot_theo_thu_tu + B5/B6"),
    "FB7": (MSG, '    "giới hạn của hệ, không phải lỗi của đề. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm "\n',
            '    "lỗi của đề, em kiểm tra lại đề. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm "\n',
            "an unverified binding told to the learner as a faulty text",
            "test_w18_loi_chua_doi_chieu_khong_noi_de_sai"),
    "FB8": (ROUTE, "                dc.reason_code == MA_CHUA_DOI_CHIEU and neu_khoi_da_dien(contract.problem_text)):\n",
            "                False):\n",
            "UNVERIFIED never enforced (the polyhedral scope ignored)",
            "test_w18_tuyen_san_pham_theo_nhan[B16]"),
    "FA1": (ANN, "        chan, u = K.project_point_onto_line(p, r), r.direction\n",
            "        chan, u = r.point, r.direction\n",
            "the witness foot is not the exact projection (label on the wrong subject point)",
            "test_w18_nhan_chung_khoang_cach_diem_duong_thang"),
    "FA2": (SCENE, '            o["annotation"] = {**{k: v for k, v in g.items() if not (k == "same_as" and vai == "result")},\n',
            '            o["annotation"] = {**g,\n',
            "the asked result merged into a given of the same subject (two roles, one label)",
            "test_w18_hai_vai_tro_cung_chu_the_giu_hai_nhan"),
    "FA3": (SCENE, '            vai = "result" if o["id"] in ket_qua else "given" if o.get("origin") == "free" else "intermediate"\n',
            '            vai = "result" if o["id"] in ket_qua else "intermediate"\n',
            "given data lose their role (the compact default would show no data)",
            "test_w18_vai_tro_du_kien_trung_gian_ket_qua"),
    "FA4": (ANN, '        k = (gan[q]["kind"], gan[q]["anchor"], frozenset(gan[q]["subject_ids"]))\n',
            '        k = (gan[q]["kind"], str(final_memory.get(q)))\n',
            "merge by equal value instead of the same subject",
            "test_w18_cung_gia_tri_khac_chu_the_khong_gop"),
}


def pytest_sessionstart(session):
    fi = os.environ.get("W18_FI")
    if fi:
        ten, cu, moi, *_ = INJECTIONS[fi]
        for m in (ROUTE, "app.ai.pipeline", MSG, SCENE, ANN, BIND, ten):   # bind importers before the swap
            importlib.import_module(m)
        _tiem(ten, cu, moi)
