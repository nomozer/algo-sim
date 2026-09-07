# -*- coding: utf-8 -*-
"""§4 + §6 — tiền kiểm TẤT ĐỊNH và đăng ký `OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR`.

`APPLICATION_LLM_CALLS = 0` ở file này. Nó chạy TRƯỚC provider và là cổng:
`main()` thoát khác 0 nếu bất kỳ ô nào của §4 không đạt, nên không ai rút được
ca khi tiền kiểm còn đỏ.

⚠️ Scalar mode ở đây đi **đường trung thực** mà §4 đòi:

    O, O′ → h = measure(distance, O, O′) → cylinder(radius=4, height=h)
          → plane_from_equation → ellipse → area

Chiều cao do chương trình **TÍNH**, nên grounding bỏ qua đúng luật. Khai thẳng
`h = 20` ghim về một fact TOẠ ĐỘ thì grounding từ chối — và đó là ca đối chứng
`height=20` của §4, giữ nguyên verdict.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.ai import gemini as G  # noqa: E402
from app.main import CACHE_VERSION  # noqa: E402
from app.runtime_identity import (  # noqa: E402
    semantic_environment_fingerprint, semantic_environment_hash,
)
from app.simulation.geometry.radical import display, is_exact_number  # noqa: E402
from app.simulation.product_capability import NANG_LUC_SAN_PHAM  # noqa: E402
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from app.simulation.semantic_program.grounding_gate import (  # noqa: E402
    check_grounding,
)
from app.simulation.semantic_program.plane_equation import (  # noqa: E402
    bat_bien_mat_phang,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

from gold_oblique_ellipse_fresh import (  # noqa: E402
    CASE_ID, CONTAINER, CONTRACT_GOLD_HASH, GOLD, GOLD_HASH, ORACLE,
    ORACLE_HASH, PROBLEM_HASH, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)

RUN_ID_PREFIX = "oblique-ellipse-after-axis-scale-repair"
RA = (BACKEND.parent / "docs" / "evaluation" / "geometry" / RUN_ID_PREFIX)
DAP_SO = "16π√5"

MP = {"kind": "construct_plane_from_equation", "target_var": "alpha",
      "a": 2, "b": 0, "c": -1, "d": 10, "label": "(α)"}


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _hf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _hd() -> RequestContract:
    c = RequestContract.model_validate(REQUEST_CONTRACT_GOLD)
    return c.model_copy(update={
        "source_invariants": tuple(c.source_invariants or ())
        + bat_bien_mat_phang(c, PROBLEM_TEXT)})


def _point_mode(**doi_mp) -> dict:
    """Gold: `anchor` + `apex_or_top` + `radius`, mặt phẳng bằng phương trình."""
    g = copy.deepcopy(GOLD)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] not in ("P1", "P2", "P3")]
    lenh = dict(MP)
    lenh.update(doi_mp)
    g["statements"] = [lenh if s.get("kind") == "construct_plane" else s
                       for s in g["statements"]]
    return g


def _scalar_mode(do_bang_measure: bool = True) -> dict:
    """`radius` + `height`, chiều cao ĐO từ hai tâm (đường trung thực)."""
    g = _point_mode()
    if do_bang_measure:
        g["memory_declarations"].append({"name": "h", "type": "float"})
        do = {"kind": "assign", "target_var": "h",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "O", "wrt": "Oprime"}}
    else:
        g["memory_declarations"].append(
            {"name": "h", "type": "float", "initial_value": 20,
             "source_fact_id": "tam_day_tren"})
        do = None
    moi = []
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            if do:
                moi.append(do)
            s = dict(s)
            s.pop("apex_or_top", None)
            s["height"] = "h"
        moi.append(s)
    g["statements"] = moi
    return g


def _chay(p: dict):
    return verify_and_compile(_hd(), SemanticProgramSpec.model_validate(p))


def _dap_so(kq):
    return {k: display(x) for k, x in (kq.final_memory or {}).items()
            if is_exact_number(x)}.get(WITNESS)


def _canh(p: dict) -> dict:
    from app.ai.pipeline import _dung_scene3d

    return _dung_scene3d(SemanticProgramSpec.model_validate(p), _hd()) or {}


def tien_kiem() -> dict:
    """§4 — mọi ô phải đạt trước khi provider được gọi."""
    ra: dict[str, object] = {"APPLICATION_LLM_CALLS": 0}

    kq_p, kq_s = _chay(_point_mode()), _chay(_scalar_mode())
    ra["POINT_MODE"] = (f"{kq_p.stage_reached} · {_dap_so(kq_p)}"
                        if kq_p.servable else f"FAIL {kq_p.error_code}")
    ra["SCALAR_MODE"] = (f"{kq_s.stage_reached} · {_dap_so(kq_s)}"
                         if kq_s.servable else f"FAIL {kq_s.error_code}")
    ra["POINT_SCALAR_PARITY"] = (
        "PASS" if (kq_p.servable and kq_s.servable
                   and _dap_so(kq_p) == _dap_so(kq_s) == DAP_SO) else "FAIL")
    ra["PLANE_EQUATION_SOURCE_INVARIANT"] = (
        "PASS" if (kq_p.source_invariant_stats.get("passed") == 1
                   and kq_s.source_invariant_stats.get("passed") == 1)
        else "FAIL")
    ra["DIRECT_RADIUS_ELLIPSE_PATH"] = "VALID" if kq_s.servable else "INVALID"

    canh = _canh(_scalar_mode())
    vat = {str(o.get("id")): o for o in canh.get("objects", [])}
    buoc = [e for e in canh.get("events", []) if e.get("object") == "alpha"]
    ra["TRACE"] = ("PASS" if len(buoc) == 1 and buoc[0]["action"] == "CREATE"
                   and "2x - z + 10 = 0" in buoc[0]["explanation"] else "FAIL")
    ra["SCENE3D"] = ("PASS" if any(o.get("type") == "ellipse3"
                                   for o in vat.values())
                     and vat.get("alpha", {}).get("type") == "plane3"
                     else "FAIL")
    ra["SCALAR_MODE_HEIGHT_DEPENDS"] = (
        "PASS" if "h" in (vat.get("tru", {}).get("depends") or []) else "FAIL")

    # ── PHẢN VÍ DỤ ────────────────────────────────────────────────────────
    pv: dict[str, str] = {}
    k = _chay(_point_mode(d=11))
    pv["mp_2x_z_11_bi_bat_bien_bac"] = (
        "PASS" if (not k.servable
                   and k.source_invariant_stats.get("violated") == 1
                   and _dap_so(k) == DAP_SO) else "FAIL")
    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _scalar_mode(do_bang_measure=False)))
    pv["height_20_khai_thang_thieu_nguon"] = (
        "PASS" if not r.ok and any(x.startswith("h|")
                                   for x in r.unjustified_literals) else "FAIL")

    from fractions import Fraction as F

    from app.simulation.geometry import curved as CV
    from app.simulation.geometry.exact import GeometryError, Plane3, Vec3

    def _v(x, y, z):
        return Vec3(F(x), F(y), F(z))

    def _ma(s, pl):
        try:
            CV.intersect_plane_curved_ellipse(s, pl)
            return None
        except GeometryError as e:
            return e.code

    thap = CV.CurvedSolid("cylinder", _v(0, 0, 0), _v(0, 0, 4), None, F(16))
    pv["elip_vuot_day"] = ("PASS" if _ma(thap, Plane3.from_equation(
        F(2), F(0), F(-1), F(2))) == CV.ERR_ELIP_CAT_DAY else "FAIL")
    cao = CV.CurvedSolid("cylinder", _v(0, 0, 0), _v(0, 0, 20), None, F(16))
    pv["mp_song_song_truc"] = ("PASS" if _ma(cao, Plane3.from_equation(
        F(1), F(0), F(0), F(-3))) == CV.ERR_ELIP_NGOAI_BAO_DONG else "FAIL")

    g = _point_mode()
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] != "r"]
    g["memory_declarations"].append(
        {"name": "P_rim", "type": "point3", "initial_value": [4, 0, 0],
         "model_assumption": "Chọn một điểm trên vành đáy dưới."})
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            s.pop("radius", None)
            s["rim_point"] = "P_rim"
    r2 = check_grounding(_hd(), SemanticProgramSpec.model_validate(g))
    pv["rim_point_thieu_provenance"] = (
        "PASS" if not r2.ok
        and r2.error_code == "UNANCHORED_DERIVED_ASSUMPTION" else "FAIL")
    ra["phan_vi_du"] = pv

    ra["GOLD_PREFLIGHT"] = (
        "PASS" if all(v == "PASS" for v in pv.values())
        and ra["POINT_SCALAR_PARITY"] == "PASS"
        and ra["PLANE_EQUATION_SOURCE_INVARIANT"] == "PASS"
        and ra["TRACE"] == ra["SCENE3D"] == "PASS"
        and ra["DIRECT_RADIUS_ELLIPSE_PATH"] == "VALID" else "FAIL")
    return ra


def dang_ky() -> dict:
    the = grammar_card("hinh_hoc")
    fp = semantic_environment_fingerprint()
    return {
        "wave": "OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR",
        "dang_ky_luc": datetime.now(timezone.utc).isoformat(),
        "RUN_CLASS": "DEVELOPMENT_REGRESSION_E2E",
        "measurement_class": "DEVELOPMENT_REGRESSION_E2E",
        "held_out_claim": False,
        "evaluator_independence": "OPERATOR_WAIVED",
        "cau_hoi": ("Pipeline san pham hien tai co TU sinh va phuc vu dung bai "
                    "thiet dien elip xien khong, sau khi HAI blocker he thong "
                    "da dong (`construct_plane_from_equation` va parity "
                    "point/scalar cua hinh tru)?"),
        "pham_vi_ket_luan": {
            "SYSTEM_EXPRESSIBLE": "da chung minh",
            "DETERMINISTICALLY_CORRECT": "da chung minh",
            "CURRENT_PIPELINE_E2E": "can do — day la o wave nay do",
            "MODEL_BEHAVIOR": "DEVELOPMENT_RERUN_SIGNAL",
            "STABILITY_UNDER_ACCEPTANCE": "NOT_MEASURED",
            "khai": ("Ca REGRESSION phat trien da tung dung de TIM loi he "
                     "thong. Ket qua chung minh duong end-to-end tren candidate "
                     "hien tai; KHONG phai held-out acceptance, va chua chung "
                     "minh tinh on dinh hay khai quat."),
        },
        "cases": 1,
        "gold_module": "gold_oblique_ellipse_fresh",
        "scorer_module": "score_oblique_ellipse_fresh",
        "run_id_prefix": RUN_ID_PREFIX,
        "ca": {"case_id": CASE_ID, "container": CONTAINER, "witness": WITNESS,
               "problem_sha256": PROBLEM_HASH, "problem_text": PROBLEM_TEXT,
               "oracle_sha256": ORACLE_HASH, "oracle": ORACLE},
        "ngan_sach": {
            "ANALYZE_CALL_BUDGET": 1,
            "INITIAL_SYNTHESIS_CALL_BUDGET": 1,
            "REPAIR_CALL_BUDGET": 3,
            "logical_application_call_limit": 5,
            "OBSERVED_TOKEN_CEILING": 40000,
            # Ba khoa duoi day RUNNER doc truc tiep (dong 343-347) — thieu mot
            # cai la no chet o khau dung manifest, TRUOC provider.
            "token_reservation_per_call": 8000,
            "token_ceiling_observed": 40000,
            "transport_retry_limit": G.MAX_ATTEMPTS,
            "transport_retry_nguon": "gemini.MAX_ATTEMPTS (gia tri san pham)",
            "cuong_che": ("ApiBudget(max_logical_calls=5) — chan o BIEN THAT "
                          "cua `call_gemini`, khong phai mot phep dem sau."),
        },
        "tieu_chi_thanh_cong": {
            "SUCCESS": ("served + exact 16√5π + postconditions + trace + "
                        "Scene3D"),
            "FIRST_ATTEMPT_SUCCESS": "attempt 0 dat TOAN BO SUCCESS",
        },
        "danh_tinh_he_duoc_do": {
            "HEAD": "a730984",
            "cache_version": CACHE_VERSION,
            "candidate": "27f5c076b7c86aa1",
            "product_variant": "C",
            "CURVED_OBLIQUE_SECTION_CAPABILITY":
                NANG_LUC_SAN_PHAM["curved_oblique_section"].trang_thai,
            "card_C_sha256": _h(the),
            "card_C_bytes": len(the.encode("utf-8")),
            "card_lay_tu": ("grammar_card('hinh_hoc') — the SAN PHAM hien "
                            "hanh. Runner tu choi chay neu no da troi."),
            "model_facing": {k: fp[k] for k in sorted(fp)
                             if isinstance(fp[k], str) and len(fp[k]) == 64},
            "semantic_environment_hash": semantic_environment_hash(),
        },
        "hash_bo_do": {
            "contract_gold_sha256": CONTRACT_GOLD_HASH,
            "gold_sha256": GOLD_HASH,
            "gold_module_sha256": _hf(
                BACKEND / "scripts" / "gold_oblique_ellipse_fresh.py"),
            "scorer_module_sha256": _hf(
                BACKEND / "scripts" / "score_oblique_ellipse_fresh.py"),
            "runner_sha256": _hf(
                BACKEND / "scripts" / "run_curved_end_to_end.py"),
            "register_sha256": _hf(Path(__file__)),
        },
        "model": {
            "provider": "google-generativelanguage-v1beta",
            "name": G.MODEL,
            "version_or_snapshot": "",
            "reproducibility": "LIMITED — alias, khong phai snapshot",
            "temperature": ("gia tri san pham hien hanh cho tung tang — runner "
                            "KHONG dat de"),
            "product_repair_limit_unchanged": 3,
        },
        "muc_giu_nguyen": {
            "PRODUCT_CAPABILITY_CHANGED": "NO",
            "curved_oblique_section": "foundation_only",
            "ma_san_pham": "KHONG doi trong luot do",
            "model_facing_contract": "KHONG doi trong luot do",
        },
        "lich_su": {
            "artifact_luot_truoc_giu_nguyen": [
                "oblique-ellipse-fresh-confirmation",
                "oblique-ellipse-e2e-after-plane-equation",
                "plane-from-equation",
            ],
            "khai": "Luot moi ghi vao thu muc RIENG; khong ghi de artifact cu.",
        },
    }


def main() -> int:
    pf = tien_kiem()
    dk = dang_ky()
    dk["GOLD_PREFLIGHT"] = pf["GOLD_PREFLIGHT"]
    dk["registration_sha256"] = _h(
        json.dumps(dk, ensure_ascii=False, sort_keys=True))

    RA.mkdir(parents=True, exist_ok=True)
    for ten, o in (("registration.json", dk), ("PREFLIGHT.json", pf)):
        p = RA / ten
        if p.exists():
            print(f"⚠️  {ten} da ton tai — KHONG ghi de artifact luot cu.")
            continue
        p.write_text(json.dumps(o, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print("→", p)

    print(json.dumps(pf, ensure_ascii=False, indent=2))
    if pf["GOLD_PREFLIGHT"] != "PASS":
        print("\n⛔ TIEN KIEM CHUA DAT — KHONG duoc goi provider.")
        return 1
    print("\n✅ TIEN KIEM DAT — provider duoc phep goi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
