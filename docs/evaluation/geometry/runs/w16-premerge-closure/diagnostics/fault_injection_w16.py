# -*- coding: utf-8 -*-
"""W16 — fault injections for the plane binding, the goal clauses, the four fail-closed
branches and the evidence builder (pytest plugin, 0 model calls).

`W16_FI=<id>` selects ONE injection: an exact source substitution applied IN MEMORY to one
module (the file on disk is never touched), with the W15 mechanism
(`w15-assumption-closure/diagnostics/fault_injection_w15._tiem`: the substitution must match
exactly once, or the run aborts — a stale injection never passes silently).

    W16_FI=FG1 PYTHONPATH=<this dir> python -m pytest -p fault_injection_w16 <tests>

Driver: `run_fault_injections_w16.py` (same directory).
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "w15-assumption-closure" / "diagnostics"))
sys.path.insert(0, str(HERE.parents[5] / "backend" / "scripts"))
from fault_injection_w15 import _tiem  # noqa: E402

GATE = "app.simulation.semantic_program.assumption_gate"
READER = "app.simulation.semantic_program.shape_constraint"
PLANE = "app.simulation.semantic_program.plane_equation"
ROUTE = "app.simulation.semantic_program.route"
BUILDER = "build_scene3d_visual_evidence"

#: id → (module, old text, new text, what it simulates, predicted catch)
INJECTIONS: dict[str, tuple[str, str, str, str, str]] = {
    "FG1": (GATE, '    if any(s.get("kind") in KHONG_HO_TRO for s in prog["statements"]):\n'
                  '        return _ket_qua(UNDETERMINED, ["CLOSURE_UNSUPPORTED_KIND control flow"])\n', "",
            "guard CLOSURE_UNSUPPORTED_KIND removed",
            "test_w16_nhanh_luong_dieu_khien_CLOSURE_UNSUPPORTED_KIND"),
    "FG2": (GATE, '    if hong:\n        return _ket_qua(UNDETERMINED, details + [f"{khuon.loai} '
                  'TEMPLATE_CONSTRAINT_VIOLATED {hong[0]}"])\n', "",
            "guard TEMPLATE_CONSTRAINT_VIOLATED removed",
            "test_w16_nhanh_dinh_khuon_pha_rang_buoc_TEMPLATE_CONSTRAINT_VIOLATED"),
    "FG3": (GATE, '    loi += [f"FRAME_DEPENDENT {x}" for x in sorted(lc.kieu - KHUNG_TU_DO)]\n', "",
            "guard FRAME_DEPENDENT removed",
            "test_w16_nhanh_phep_dung_phu_thuoc_khung_FRAME_DEPENDENT"),
    "FG4": (GATE, '    if dung.hong:\n        return _ket_qua(UNDETERMINED, ["FORMATION_REJECTED"])\n', "",
            "guard FORMATION_REJECTED removed",
            "test_w16_nhanh_bang_mat_hong_FORMATION_REJECTED"),
    "FA1": (GATE, "        m, _ly_do = gan_mat_phang(lit[1], *mp)\n",
            "        m = next((x for x in mp[0] if tuong_duong([_F(c) for c in lit[2]], x.he_so)), None)\n",
            "plane literal bound to ANY proportional text equation (the W15 rule)",
            "test_w16_he_so_mat_phang_khong_gan_duoc_dung_thuc_the_khong_duoc_C0 (A1, A2, A6, A6b, A7, A8)"),
    "FA2": (GATE, "    if duy_nhat and len(mp_de) == 1:\n", "    if mp_de:\n",
            "unnamed program plane bound to the first text equation without uniqueness",
            "test_w16_he_so_mat_phang_khong_gan_duoc_dung_thuc_the_khong_duoc_C0 (A6b, A7, A8)"),
    "FA3": (PLANE, "            phay = i + 1 < len(tu) and tu[i + 1].lower() in (\"prime\", \"phay\") "
                   "and not ten.endswith(\"'\")\n", "            phay = False\n",
            "a _prime/_phay token after a plane name is ignored (mp_P_prime reads as (P))",
            "test_w16_ten_mat_phang_cua_bien (mp_P_prime, P_phay, alpha_prime) + A9/A9b"),
    "FA4": (PLANE, "        ra.append(MatPhangDe(_phay(m.group(1)) if m else None, he, (t, p)))\n",
            "        ra.append(MatPhangDe(m.group(1) if m else None, he, (t, p)))\n",
            "text plane names keep ′/’ (P′ never equals the program's P')",
            "test_w16_doc_mat_phang_de_mang_ten_he_so_va_span (P′, α’) + A9b"),
    "FB1": (GATE, "    de_gt = che_muc_tieu(de)\n", "    de_gt = de\n",
            "goal clauses read as premises (no masking)",
            "test_w16_quan_he_trong_yeu_cau_chung_minh_khong_la_tien_de (7 cases) + route test"),
    "FB2": (GATE, "        if chua_doc or ngoai or muc_tieu:\n", "        if chua_doc or ngoai:\n",
            "a text with a goal clause may still yield a counterexample",
            "test_w16_muc_tieu_sau_tinh_khong_tao_phan_vi_du"),
    "FB3": (READER, '    nfc, vi = _nfc_theo_cum(problem_text or "")\n',
            '    nfc = problem_text or ""\n    vi = list(range(len(nfc) + 1))\n',
            "goal keywords matched on the raw text (NFD input hides them)",
            "test_w16_muc_tieu_nhan_ca_de_go_dang_to_hop_NFD"),
    "FD1": (BUILDER, '    return None if muc >= MUC_TOI_THIEU else f"refusal message unreadable '
                     '(ink {muc:.4f} < {MUC_TOI_THIEU})"\n', "    return None\n",
            "builder accepts a blank refusal capture",
            "test_w16_anh_tu_choi_trang_khong_doc_duoc_thi_that_bai"),
    "FD2": (BUILDER, '    if loi:\n        raise ThieuAnhBangChung(f"{family}: " + "; ".join(loi))\n', "",
            "builder no longer fails on a missing panel",
            "test_w16_thieu_anh_bat_ky_thi_that_bai_khong_thay_o_trang and the other W16 builder tests"),
}


def pytest_sessionstart(session):
    fi = os.environ.get("W16_FI")
    if fi:
        ten, cu, moi, *_ = INJECTIONS[fi]
        importlib.import_module(ROUTE)            # bind importers before the swap
        importlib.import_module(BUILDER)
        importlib.import_module(GATE)
        _tiem(ten, cu, moi)
