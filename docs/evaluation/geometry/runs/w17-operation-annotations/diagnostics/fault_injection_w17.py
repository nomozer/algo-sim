# -*- coding: utf-8 -*-
"""W17 — fault injections for the operation binding (§15.1), the goal-clause grounding (§15.2),
the refusal cause (§15.3), the on-figure annotations (§15.4) and the group-step label
(pytest plugin, 0 model calls).

`W17_FI=<id>` selects ONE injection: an exact source substitution applied IN MEMORY to one
module (the file on disk is never touched), with the W15 mechanism
(`w15-assumption-closure/diagnostics/fault_injection_w15._tiem`: the substitution must match
exactly once, or the run aborts — a stale injection never passes silently).

    W17_FI=FO1 PYTHONPATH=<this dir> python -m pytest -p fault_injection_w17 <tests>

Driver: `run_fault_injections_w17.py` (same directory).
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
GATE, GROUND, READER = SP + "assumption_gate", SP + "grounding_gate", SP + "shape_constraint"
CAUSE, ANN, SCENE, ROUTE = SP + "refusal_cause", SP + "quantity_annotations", SP + "scene3d", SP + "route"
MSG = "app.learner_messages"

#: id → (module, old text, new text, what it simulates, predicted catch)
INJECTIONS: dict[str, tuple[str, str, str, str, str]] = {
    "FO1": (GATE, "        if ma is None:\n            return _ket_qua(PROVEN_SAFE, chi_tiet + them, certificate=cc)\n",
            "        return _ket_qua(PROVEN_SAFE, chi_tiet + them, certificate=cc)\n",
            "operation check removed (§15.1 is no longer a condition of PROVEN_SAFE)",
            "test_w17_phep_dung_lech_quan_he_cua_de_khong_duoc_chung_nhan + the route test"),
    # Run 3 (after the final-review fix d3817d5f): FO2/FO3 target the new definite-mismatch branches;
    # runs 1-2 (logs FAULT_INJECTION_W17*.log) targeted `if mp_d is None or mp_d != mp_c:` etc.
    "FO2": (GATE, "        elif mp_d != mp_c:\n", "        elif False:\n",
            "plane identity not compared (any text-bound plane accepted: α where the text says β)",
            "test_w17_phep_dung_lech_quan_he_cua_de_khong_duoc_chung_nhan (wrong-plane cases)"),
    "FO3": (GATE, "        elif khoi_d != khoi_c:\n", "        elif False:\n",
            "solid identity not compared (the program may cut another solid)",
            "test_w17_phep_dung_lech_quan_he_cua_de_khong_duoc_chung_nhan (wrong-solid case)"),
    "FO7": (READER, '            if _TAN_NGU_VOI.search(de, max(0, m.start(f"mp{k}") - 40), m.start(f"mp{k}")):\n'
                    "                continue\n", "",
            "the object of 'song song/vuông góc với (X)' read as the cutting plane (final-review defect 1)",
            "test_w17_mat_phang_sau_voi_la_tan_ngu_khong_phai_mat_phang_cat + Q1"),
    "FO8": (GATE, "        if mp_d is None or mp_c is None:\n", "        if False:\n",
            "an unpinned plane identity reported as a definite mismatch (final-review defect 2)",
            "test_w17_mat_phang_cat_khong_ghim_duoc_la_chua_chung_minh_khong_phai_lech_phep_dung[Q2]"),
    "FG4": (READER, '        while ranh and nfc[ranh[-1].start()] == "," and _MO_BIET.match(nfc, ranh[-1].end()):\n'
                    "            cuoi = ranh.pop().start()\n", "",
            "the premise ', biết Y?' masked as the question (final-review defect 3)",
            "test_w17_cau_hoi_ket_bang_biet_menh_de_biet_la_gia_thiet + test_w17_cau_hoi_bao_nhieu_biet_van_la_du_kien"),
    "FO4": (GATE, "    for v in _gia_tri_fact(contract, fid):\n", "    for v in ():\n",
            "source binding ignored (W16 name/uniqueness rule only)",
            "test_w17_ten_bien_va_nguon_chi_hai_mat_phang_khac_nhau_thi_khong_co_danh_tinh + O7"),
    "FO5": (GATE, "    if ten and nguon.ten not in ten:\n", "    if False:\n",
            "name/source conflict resolved silently in favour of the source",
            "test_w17_ten_bien_va_nguon_chi_hai_mat_phang_khac_nhau_thi_khong_co_danh_tinh"),
    "FO6": (GATE, '    if re.fullmatch(rf"(?:{_D}){{3,}}", q.mat_phang):\n', "    if False:\n",
            "a point-named plane (MNP) looked up among the equations (no point-set identity)",
            "test_w17_mat_phang_goi_qua_diem_co_danh_tinh_la_tap_diem"),
    "FG1": (GROUND, "    kq = _kiem_grounding(contract, spec, che_muc_tieu(goc))\n",
            "    kq = _kiem_grounding(contract, spec, goc)\n",
            "grounding reads goal clauses as premises (no masking)",
            "test_w17_gia_tri_chi_trong_yeu_cau_chung_minh_khong_thanh_GIVEN"),
    "FG2": (GROUND, '        return kq.model_copy(update={"error_code": ERR_CHI_TRONG_MUC_TIEU})\n', "        return kq\n",
            "a goal-only value keeps the generic source code (not classified)",
            "test_w17_gia_tri_chi_trong_yeu_cau_chung_minh_khong_thanh_GIVEN (code)"),
    "FG3": (READER, r'_HET_MENH_DE = re.compile(r"[?!;\n]|\.(?=\s|$)|,\s*biết(?![^\W\d_])")' + "\n",
            r'_HET_MENH_DE = re.compile(r"[?!;\n]|\.(?=\s|$)")' + "\n",
            "a ', biết …' clause after the goal stays inside the goal",
            "test_w17_menh_de_biet_sau_yeu_cau_chung_minh_la_gia_thiet + "
            "test_w17_chung_minh_biet_du_kien_sau_biet_van_la_du_kien"),
    "FC1": (CAUSE, '    "CONSTRUCTION_NOT_TEXT_BOUND": CONSTRUCTION,\n', '    "CONSTRUCTION_NOT_TEXT_BOUND": SOURCE,\n',
            "cause swapped: a construction mismatch blamed on the text",
            "test_w17_lech_phep_dung_la_nguyen_nhan_dung + test_w17_bang_nguyen_nhan_theo_ma_da_dang_ky"),
    "FC2": (CAUSE, '            "refusal_cause": SOURCE if de_ghi else CONSTRUCTION}\n', '            "refusal_cause": SOURCE}\n',
            "a non-positive length always blamed on the text",
            "test_w17_do_dai_khong_duong_DE_KHONG_GHI_la_nguyen_nhan_dung"),
    "FC3": (CAUSE, '        return {"reason_code": MA_KHONG_CAT, "reason_subjects": [], "refusal_cause": CONSTRUCTION}\n',
            '        return {"reason_code": MA_KHONG_CAT, "reason_subjects": [], "refusal_cause": SOURCE}\n',
            "a system-chosen plane that misses the solid blamed on the text",
            "test_w17_mat_phang_chuong_trinh_tu_dat_khong_cat_khoi_la_nguyen_nhan_dung"),
    "FC4": (ROUTE, '    extra.setdefault("refusal_cause", theo_ma(extra.get("reason_code")))\n', "",
            "route refusals carry no cause",
            "test_w17_lech_phep_dung_la_nguyen_nhan_dung (route)"),
    "FM1": (MSG, '_DUOI_LOI_HE = " Đây là lỗi dựng hình của hệ, đề không cần sửa — em có thể gửi lại để hệ dựng lại."\n',
            '_DUOI_LOI_HE = " Em kiểm tra lại đề rồi gửi lại nhé."\n',
            "construction-cause messages tell the learner to fix the text",
            "test_w17_*_khong_bao_sua_de + test_w17_so_lieu_he_doc_lech_de_la_loi_he"),
    "FM2": (MSG, '    return {**envelope, "refusal_cause": envelope.get("refusal_cause") or "UNKNOWN",\n',
            '    return {**envelope, "refusal_cause": envelope.get("refusal_cause") or "SOURCE",\n',
            "an unclassified refusal defaults to SOURCE",
            "test_w17_nguyen_nhan_chua_ro_khong_bao_sua_de"),
    "FA1": (ANN, "        chu_the = [x for x in (expr.of, expr.wrt) if x]\n",
            "        chu_the = [x for x in (expr.of, expr.wrt) if x][:1]\n",
            "a measured distance keeps only its first operand (wrong subject set)",
            "test_w17_thiet_dien_va_khoang_cach_gan_mien_va_cap"),
    "FA2": (SCENE, '            o["annotation"] = {**g, "category": "result" if o["id"] in ket_qua else "measurement"}\n',
            '            o["annotation"] = {**g, "category": "measurement"}\n',
            "every quantity a measurement (the answer label would show at its MEASUREMENT step: early result)",
            "test_w17_lang_tru_du_kien_so_do_va_ket_qua_gan_dung_chu_the"),
    "FA3": (ANN, "        if k in da_co:\n", "        if False:\n",
            "dedup removed (one subject, two labels)", "test_w17_mot_chu_the_mot_nhan_du_kien_truoc"),
    "FA4": (ANN, "        bang = d.dot(d) == v * v\n", "        bang = True\n",
            "exact-distance check removed (a given length labels a segment of another length)",
            "test_w17_do_dai_de_cho_kiem_bang_khoang_cach_chinh_xac"),
    "FN1": (SCENE, '            "display_label": labels.get(main_obj) or nhan_lenh or "Bước dựng hình",\n',
            '            "display_label": labels.get(main_obj) or "Bước dựng hình",\n',
            "the group step loses its own label (the W16 'given data' symptom)",
            "test_w17_buoc_dung_nhom_canh_mang_nhan_cua_cau_lenh_nhom"),
}


def pytest_sessionstart(session):
    fi = os.environ.get("W17_FI")
    if fi:
        ten, cu, moi, *_ = INJECTIONS[fi]
        for m in (ROUTE, "app.ai.pipeline", MSG, SCENE, ANN, ten):   # bind importers before the swap
            importlib.import_module(m)
        _tiem(ten, cu, moi)
