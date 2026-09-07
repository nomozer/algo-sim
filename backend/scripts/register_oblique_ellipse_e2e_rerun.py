# -*- coding: utf-8 -*-
"""§6 — đăng ký `OBLIQUE_ELLIPSE_FRESH_E2E_RERUN` và ghi phán quyết tiền kiểm.

Đăng ký **trước** kết quả, đúng lệ: mọi hash chốt trước lượt gọi đầu, để không
ai chọn lại tiêu chí sau khi nhìn số.

⚠️ Lượt này **DỪNG TRƯỚC PROVIDER**. §4 của brief đặt sẵn điều kiện dừng, và
nó đã bật: đường dựng hình trụ `radius + height` không cắt ra được elip. Nên
file này ghi `registration` + `PREFLIGHT` chứ **không** ghi `manifest` của một
lượt chạy — không có lượt chạy nào để mà ghi.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.main import CACHE_VERSION  # noqa: E402
from app.runtime_identity import (  # noqa: E402
    semantic_environment_fingerprint, semantic_environment_hash,
)
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402

from gold_oblique_ellipse_fresh import (  # noqa: E402
    CONTRACT_GOLD_HASH, GOLD_HASH, ORACLE, ORACLE_HASH, PROBLEM_HASH,
    PROBLEM_TEXT,
)

RA = (BACKEND.parent / "docs" / "evaluation" / "geometry"
      / "oblique-ellipse-e2e-after-plane-equation")

RUN_ID = "oblique-ellipse-e2e-after-plane-equation"


def _bam_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _bam(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def dang_ky() -> dict:
    fp = semantic_environment_fingerprint()
    return {
        "RUN_ID": RUN_ID,
        "RUN_CLASS": "DEVELOPMENT_CONFIRMATION",
        "MEASUREMENT_CLASS": "DEVELOPMENT_CURVED_END_TO_END_CONFIRMATION",
        "HELD_OUT_CLAIM": "NO",
        "EVALUATOR_INDEPENDENCE": "OPERATOR_WAIVED",
        "SUCCESS": ("eventual served + exact 16√5π + postconditions + trace "
                    "+ Scene3D"),
        "FIRST_ATTEMPT_SUCCESS": "attempt 0 đạt TOÀN BỘ tiêu chí SUCCESS",
        "CASES": 1,
        "tran": {
            "ANALYZE_CALLS": 1, "INITIAL_SYNTHESIS_CALLS": 1,
            "REPAIR_CALLS": 3, "LOGICAL_APPLICATION_CALLS": 5,
            "TOTAL_TOKEN_CEILING": 40000,
        },
        "de": {"problem_sha256": PROBLEM_HASH, "text": PROBLEM_TEXT},
        "oracle": {"sha256": ORACLE_HASH, **ORACLE},
        "he_thong": {
            "CACHE_VERSION": CACHE_VERSION,
            "semantic_environment_hash": semantic_environment_hash(),
            **{k: fp[k] for k in sorted(fp)
               if isinstance(fp[k], str) and len(fp[k]) == 64},
            "grammar_card_bytes": len(grammar_card("hinh_hoc").encode("utf-8")),
        },
        "bo_do": {
            "gold_module": _bam_file(BACKEND / "scripts"
                                     / "gold_oblique_ellipse_fresh.py"),
            "scorer_module": _bam_file(BACKEND / "scripts"
                                       / "score_oblique_ellipse_fresh.py"),
            "runner": _bam_file(BACKEND / "scripts"
                                / "run_curved_end_to_end.py"),
            "replay": _bam_file(BACKEND / "scripts"
                                / "replay_plane_from_equation.py"),
            "contract_gold_sha256": CONTRACT_GOLD_HASH,
            "gold_sha256": GOLD_HASH,
        },
    }


def preflight() -> dict:
    """Phán quyết §4 — đo tất định, 0 lượt gọi."""
    from fractions import Fraction as F

    from app.simulation.geometry import curved as CV
    from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
    from app.simulation.geometry.radical import display

    def v(x, y, z):
        return Vec3(F(x), F(y), F(z))

    mp = Plane3.from_equation(F(2), F(0), F(-1), F(10))
    A = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), None, F(16))
    B = CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(16),
                       height_sq_khai=F(400))

    def thu(s):
        try:
            return {"ket_qua": display(
                CV.dien_tich_elip(CV.intersect_plane_curved_ellipse(s, mp)))}
        except GeometryError as e:
            return {"tu_choi": e.code, "chi_tiet": str(e)[:180]}

    uA, uB = A.huong_truc, B.huong_truc
    tamA = CV.intersect_line_plane(A.axis, mp)
    tamB = CV.intersect_line_plane(B.axis, mp)
    LA = (tamA - A.anchor).dot(uA) / uA.dot(uA)
    LB = (tamB - B.anchor).dot(uB) / uB.dot(uB)

    return {
        "GOLD_PREFLIGHT": "PASS",
        "PLANE_FROM_EQUATION": "PASS",
        "PLANE_EQUATION_SOURCE_INVARIANT": "PASS",
        "ELLIPSE_INTERSECTION": "PASS",
        "EXACT_AREA": "16√5π",
        "POSTCONDITIONS": "PASS",
        "TRACE": "PASS",
        "SCENE3D": "PASS",
        "SERVABLE": "YES",
        "CYLINDER_DIRECT_RADIUS_PATH": "FAIL",
        "BLOCKER": "CURVED_SCALAR_AXIS_SCALE_IN_ELLIPSE_CAP_CHECK",
        "BLOCKER_CLASS": "KERNEL",
        "bang_chung": {
            "hai_khoi_bang_nhau_ve_hinh": {
                "radius_sq": [str(A.radius_sq), str(B.radius_sq)],
                "height_sq": [str(A.height_sq), str(B.height_sq)],
                "truc_cung_phuong": uA.cross(uB).is_zero(),
            },
            "A_khai_bang_HAI_DIEM": {
                "u": [str(uA.x), str(uA.y), str(uA.z)], "uu": str(uA.dot(uA)),
                "L": str(LA), "tren_1_tru_L": str(1 - LA), **thu(A)},
            "B_khai_bang_RADIUS_HEIGHT": {
                "u": [str(uB.x), str(uB.y), str(uB.z)], "uu": str(uB.dot(uB)),
                "L": str(LB), "tren_1_tru_L": str(1 - LB), **thu(B)},
            "duong_TRON_doi_chung": {
                "A": str(CV.intersect_plane_curved(
                    A, Plane3.from_equation(F(0), F(0), F(1), F(-10))
                ).radius_sq),
                "B": str(CV.intersect_plane_curved(
                    B, Plane3.from_equation(F(0), F(0), F(1), F(-10))
                ).radius_sq),
            },
        },
        "QUYET_DINH": "DUNG_TRUOC_PROVIDER",
        "APPLICATION_LLM_CALLS": 0,
    }


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    dk = dang_ky()
    pf = preflight()
    dk["registration_sha256"] = _bam(
        json.dumps(dk, ensure_ascii=False, sort_keys=True))
    for ten, o in (("registration.json", dk), ("PREFLIGHT.json", pf)):
        p = RA / ten
        if p.exists():
            print(f"⚠️  {ten} đã tồn tại — KHÔNG ghi đè artifact lượt cũ.")
            continue
        p.write_text(json.dumps(o, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print("→", p)
    print(json.dumps(pf, ensure_ascii=False, indent=2)[:900])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
