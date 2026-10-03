# -*- coding: utf-8 -*-
"""W16 Phase 1 — reproduce every risk of the brief BEFORE any fix, including the cases that
turn out not to be exploitable (0 model calls).

Each case is a builder of `backend/tests/geometry/test_assumption_certificate.py` (the RED
tests of the same commit), so the probe and the tests measure the same inputs. Per case:
the assumption gate (`danh_gia_doc_lap`), the product route (`verify_and_compile`: served
or refused, stage), and the value the learner would be shown. Output:
`PROBE_W16_PHASE1_<commit7>.json` next to this script; refuses to overwrite. Run from the
repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/probe_w16_phase1.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from tests.geometry import test_assumption_certificate as X  # noqa: E402
from tests.geometry import w14_cases as W  # noqa: E402

HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
OUT = HERE.with_name(f"PROBE_W16_PHASE1_{HEAD[:7]}.json")

#: (risk, group, expectation after the fix) per case family.
NHOM = [
    ("A_plane_binding", "MUST_NOT_CERTIFY", X.MP_SAI_THUC_THE),
    ("A_plane_binding", "MUST_STAY_C0", X.MP_DUNG_THUC_THE),
    ("A_prime_construction_relation", "LIMIT_RECORDED", {
        "A2b_cat_bang_alpha_khi_de_noi_beta": lambda: X._p1_mat_phang(
            X.HAI_MP, [("alpha_plane", (0, 0, 1, -3)), ("beta_plane", (0, 0, 1, -2))], "alpha_plane")}),
    ("B_premise_vs_goal", "MUST_NOT_CERTIFY", {k: (lambda t=t: X._t1_cau(t)) for k, t in X.MUC_TIEU_THANH_TIEN_DE.items()}),
    ("B_premise_vs_goal", "MUST_STAY_C1", {k: (lambda t=t: X._t1_cau(t)) for k, t in X.GIA_THIET_GIU_NGUYEN.items()}),
    ("B_premise_vs_goal", "NOT_EXPLOITABLE", {k: (lambda t=t: X._t1_cau(t)) for k, t in X.KHONG_KHAI_THAC_DUOC.items()}),
    ("B_premise_vs_goal", "OVER_REFUSAL_FAIL_CLOSED", {"B6b_tinh_biet_chieu_cao": lambda: X._t1_cau(
        X.NEN_T1 + X.DAY_T1 + ", cạnh bên SA vuông góc với đáy. Tính thể tích khối chóp S.ABC, "
                              "biết chiều cao của khối chóp bằng 5.")}),
    ("C_guards", "GUARD_FIRES", X.BON_NHANH),
    ("C_guards", "VALID_COUNTERPART", {"T1_doi_chung": X._t1}),
]


def _gia_tri(raw: dict) -> dict:
    mem = W.bo_nho_cuoi(W.spec_cua(raw))
    return {k: str(mem[k]) for k in ("area_T", "the_tich_khoi") if k in mem}


def do(build) -> dict:
    ct, raw = build()
    kq = X._kq(ct, raw)
    _sp, out, _sc = W.chay(ct, raw)
    try:
        shown = _gia_tri(raw)
    except Exception as e:  # noqa: BLE001 — a program the interpreter rejects has no shown value
        shown = {"error": type(e).__name__}
    return {"gate": {"status": kq.status, "certificate": kq.certificate, "reason_code": kq.reason_code,
                     "details": [d for d in kq.details if not d.startswith("RELATION")][:6]},
            "route": {"servable": out.servable, "stage_reached": out.stage_reached,
                      "reason_code": out.reason_code, "assumption_enforced": out.assumption_enforced},
            "shown_value": shown}


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rows = []
    for risk, group, cases in NHOM:
        for cid, build in cases.items():
            r = {"risk": risk, "group": group, "id": cid, **do(build)}
            rows.append(r)
            g, rt = r["gate"], r["route"]
            print(f"{risk:30} {group:24} {cid:52} gate={g['status']}/{g['certificate']} "
                  f"route={'SERVED' if rt['servable'] else 'REFUSED@' + str(rt['stage_reached'])} "
                  f"shown={r['shown_value']}")
    OUT.write_text(json.dumps({"probe": "W16_PHASE1", "measured_at_commit": HEAD, "model_calls": 0,
                               "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, len(rows))


if __name__ == "__main__":
    main()
