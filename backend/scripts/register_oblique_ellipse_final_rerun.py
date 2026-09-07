# -*- coding: utf-8 -*-
"""§4 + §5 + §7 — tiền kiểm GOLD, tiền kiểm BỘ CHẤM, và đăng ký lượt cuối.

`APPLICATION_LLM_CALLS = 0`. File này là **CỔNG**: `main()` thoát khác 0 nếu
một trong hai tiền kiểm chưa đạt, nên không ai rút được ca khi bộ đo còn đỏ.

⚠️ Vì sao §5 tồn tại, và nó mới có từ wave này: lượt
`OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR` chấm `PLANE_CONSTRUCTION_CORRECT
= FAIL` cho một chương trình dựng mặt phẳng **đúng từng hệ số** — bộ chấm tụt
lại sau hệ đúng một wave. Một tiền kiểm bộ chấm chạy TRƯỚC provider là cách rẻ
nhất để chuyện ấy không lặp lại.
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
from score_oblique_ellipse_fresh import cham_synthesis  # noqa: E402

RUN_ID_PREFIX = "oblique-ellipse-final-card-rerun"
RA = BACKEND.parent / "docs" / "evaluation" / "geometry" / RUN_ID_PREFIX
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


def _point_mode(**doi) -> dict:
    g = copy.deepcopy(GOLD)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] not in ("P1", "P2", "P3")]
    lenh = dict(MP)
    lenh.update(doi)
    g["statements"] = [lenh if s.get("kind") == "construct_plane" else s
                       for s in g["statements"]]
    return g


def _scalar_mode(do_bang_measure: bool = True) -> dict:
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


def _rim_mode(nguon: str | None) -> dict:
    g = _point_mode()
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] != "r"]
    d = {"name": "P_rim", "type": "point3", "initial_value": [4, 0, 0]}
    if nguon:
        d["source_fact_id"] = nguon
    else:
        d["model_assumption"] = "Chọn một điểm trên vành đáy dưới."
    g["memory_declarations"].append(d)
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            s.pop("radius", None)
            s["rim_point"] = "P_rim"
    return g


def _chay(p: dict):
    return verify_and_compile(_hd(), SemanticProgramSpec.model_validate(p))


def _dap_so(kq):
    return {k: display(x) for k, x in (kq.final_memory or {}).items()
            if is_exact_number(x)}.get(WITNESS)


def _canh(p: dict) -> dict:
    from app.ai.pipeline import _dung_scene3d

    return _dung_scene3d(SemanticProgramSpec.model_validate(p), _hd()) or {}


def tien_kiem_gold() -> dict:
    """§4 — gold + sáu phản ví dụ."""
    kp, ks = _chay(_point_mode()), _chay(_scalar_mode())
    canh = _canh(_point_mode())
    vat = {str(o.get("id")): o for o in canh.get("objects", [])}
    buoc = [e for e in canh.get("events", []) if e.get("object") == "alpha"]

    pv: dict[str, str] = {}
    k11 = _chay(_point_mode(d=11))
    pv["mp_2x_z_11_bi_bat_bien_bac"] = (
        "PASS" if (not k11.servable
                   and k11.source_invariant_stats.get("violated") == 1
                   and _dap_so(k11) == DAP_SO) else "FAIL")
    r20 = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _scalar_mode(do_bang_measure=False)))
    pv["height_20_thieu_nguon_giu_verdict"] = (
        "PASS" if not r20.ok and any(x.startswith("h|")
                                     for x in r20.unjustified_literals)
        else "FAIL")
    rr = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _rim_mode(None)))
    pv["rim_point_tu_tao_thieu_nguon_bi_bac"] = (
        "PASS" if not rr.ok
        and rr.error_code == "UNANCHORED_DERIVED_ASSUMPTION" else "FAIL")
    rg = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _rim_mode("ban_kinh_day")))
    pv["grounded_named_rim_point_van_hop_le"] = (
        "PASS" if not any(x.startswith("P_rim|")
                          for x in rg.unjustified_literals) else "FAIL")

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
    pv["elip_vuot_day_bi_bac"] = ("PASS" if _ma(thap, Plane3.from_equation(
        F(2), F(0), F(-1), F(2))) == CV.ERR_ELIP_CAT_DAY else "FAIL")
    cao = CV.CurvedSolid("cylinder", _v(0, 0, 0), _v(0, 0, 20), None, F(16))
    pv["mp_song_song_truc_giu_ma_bien"] = (
        "PASS" if _ma(cao, Plane3.from_equation(F(1), F(0), F(0), F(-3)))
        == CV.ERR_ELIP_NGOAI_BAO_DONG else "FAIL")

    ra = {
        "scope": "PASS",
        "plane_from_equation": "PASS" if kp.servable else "FAIL",
        "plane_equation_source_invariant": (
            "PASS" if (kp.source_invariant_stats.get("passed") == 1
                       and ks.source_invariant_stats.get("passed") == 1)
            else "FAIL"),
        "point_mode": (f"{kp.stage_reached} · {_dap_so(kp)}"
                       if kp.servable else f"FAIL {kp.error_code}"),
        "scalar_mode": (f"{ks.stage_reached} · {_dap_so(ks)}"
                        if ks.servable else f"FAIL {ks.error_code}"),
        "point_scalar_parity": (
            "PASS" if (kp.servable and ks.servable
                       and _dap_so(kp) == _dap_so(ks) == DAP_SO) else "FAIL"),
        "direct_radius_ellipse_path": "VALID" if ks.servable else "INVALID",
        "postconditions": "PASS" if kp.servable else "FAIL",
        "trace": ("PASS" if len(buoc) == 1 and buoc[0]["action"] == "CREATE"
                  and "2x - z + 10 = 0" in buoc[0]["explanation"] else "FAIL"),
        "Scene3D": ("PASS" if any(o.get("type") == "ellipse3"
                                  for o in vat.values()) else "FAIL"),
        "phan_vi_du": pv,
    }
    ra["GOLD_PREFLIGHT"] = (
        "PASS" if all(v == "PASS" for v in pv.values())
        and ra["point_scalar_parity"] == "PASS"
        and ra["plane_equation_source_invariant"] == "PASS"
        and ra["trace"] == ra["Scene3D"] == "PASS"
        and ra["direct_radius_ellipse_path"] == "VALID" else "FAIL")
    return ra


def tien_kiem_scorer() -> dict:
    """§5 — bộ chấm chạy trên fixture tổng hợp, TRƯỚC provider."""
    pm = cham_synthesis(_point_mode())
    ti_le = cham_synthesis(_point_mode(a=-4, b=0, c=2, d=-20))
    rim = cham_synthesis(_rim_mode(None))
    kq_pm = _chay(_point_mode())
    kq_rim = _chay(_rim_mode(None))
    canh = _canh(_point_mode())

    ra = {
        "① plane_from_equation": {
            "PLANE_OPERATION": pm["PLANE_OPERATION"],
            "PLANE_COEFFICIENTS": pm["PLANE_COEFFICIENTS"],
            "PLANE_CONSTRUCTION_CORRECT": pm["PLANE_CONSTRUCTION_CORRECT"]},
        "② hệ số TỈ LỆ": {
            "PLANE_COEFFICIENTS": ti_le["PLANE_COEFFICIENTS"],
            "PLANE_COEFFICIENTS_CORRECT": ti_le["PLANE_COEFFICIENTS_CORRECT"]},
        "③ direct-radius cylinder": {
            "DIRECT_RADIUS_USED": pm["DIRECT_RADIUS_USED"],
            "RIM_POINT_USED": pm["RIM_POINT_USED"],
            "AXIS_TWO_POINTS": pm["AXIS_TWO_POINTS"]},
        "④ ungrounded rim_point": {
            "RIM_POINT_USED": rim["RIM_POINT_USED"],
            "RIM_POINT_GROUNDED": rim["RIM_POINT_GROUNDED"],
            "DIRECT_RADIUS_USED": rim["DIRECT_RADIUS_USED"]},
        "⑤ exact result": {"dap_so": _dap_so(kq_pm)},
        "⑥ dừng ở grounding": {
            "servable": kq_rim.servable, "stage": kq_rim.stage_reached,
            "dap_so": _dap_so(kq_rim)},
        "⑦ trace + Scene3D của gold": {
            "so_su_kien": len(canh.get("events", [])),
            "co_ellipse3": any(o.get("type") == "ellipse3"
                               for o in canh.get("objects", []))},
    }
    ra["SCORER_RECOGNIZES_PLANE_FROM_EQUATION"] = (
        "YES" if (pm["PLANE_OPERATION"] == "construct_plane_from_equation"
                  and pm["PLANE_CONSTRUCTION_CORRECT"] == "PASS"
                  and ti_le["PLANE_COEFFICIENTS_CORRECT"] == "PASS") else "NO")
    ra["SCORER_DISTINGUISHES_RADIUS_AND_RIM"] = (
        "YES" if (pm["DIRECT_RADIUS_USED"] and not pm["RIM_POINT_USED"]
                  and rim["RIM_POINT_USED"] and not rim["DIRECT_RADIUS_USED"]
                  and rim["RIM_POINT_GROUNDED"] is False) else "NO")
    ra["SCORER_STAGE_SEMANTICS"] = (
        "PASS" if (_dap_so(kq_pm) == DAP_SO and kq_pm.stage_reached == "served"
                   and not kq_rim.servable
                   and kq_rim.stage_reached == "grounding"
                   and _dap_so(kq_rim) is None) else "FAIL")
    ra["SCORER_PREFLIGHT"] = (
        "PASS" if (ra["SCORER_RECOGNIZES_PLANE_FROM_EQUATION"] == "YES"
                   and ra["SCORER_DISTINGUISHES_RADIUS_AND_RIM"] == "YES"
                   and ra["SCORER_STAGE_SEMANTICS"] == "PASS") else "FAIL")
    return ra


def dang_ky() -> dict:
    the = grammar_card("hinh_hoc")
    fp = semantic_environment_fingerprint()
    return {
        "wave": "OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN",
        "dang_ky_luc": datetime.now(timezone.utc).isoformat(),
        "RUN_CLASS": "DEVELOPMENT_REGRESSION_E2E",
        "measurement_class": "DEVELOPMENT_REGRESSION_SIGNAL",
        "held_out_claim": False,
        "evaluator_independence": "OPERATOR_WAIVED",
        "cau_hoi": ("Sau khi Card noi ra luat chon o dai luong, mo hinh co "
                    "dung `radius` thay vi tu tao `rim_point` khong — va duong "
                    "end-to-end co toi `served` khong?"),
        "pham_vi_ket_luan": {
            "loai": "DEVELOPMENT_REGRESSION_SIGNAL",
            "khai": ("Ca nay DA duoc dung trong qua trinh phat trien. Quan he "
                     "nhan qua RIENG cua dong Card ghi o muc QUAN SAT "
                     "truoc/sau, KHONG ghi thanh ket luan A/B."),
            "STABILITY_UNDER_ACCEPTANCE": "NOT_MEASURED",
            "CURVED_OBLIQUE_SECTION": "foundation_only",
            "PRODUCT_PROMOTION_ELIGIBLE": "NO",
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
            "token_reservation_per_call": 8000,
            "token_ceiling_observed": 40000,
            "transport_retry_limit": G.MAX_ATTEMPTS,
            "transport_retry_nguon": "gemini.MAX_ATTEMPTS (gia tri san pham)",
            "cuong_che": ("ApiBudget(max_logical_calls=5) — chan o BIEN THAT "
                          "cua `call_gemini`."),
        },
        "tieu_chi_thanh_cong": {
            "SUCCESS": "served + exact 16√5π + postconditions + trace + Scene3D",
            "FIRST_ATTEMPT_SUCCESS": "attempt 0 dat TOAN BO SUCCESS",
        },
        "lich_su_de_so_sanh": {
            "HISTORICAL_DIRECT_RADIUS": "0/2",
            "HISTORICAL_RIM_POINT": "2/2",
            "raw_sha256": [
                "150ab4f1d6e7656f87795e0b61c2f65d349c458972131f48915426adb2ad9602",
                "da8e60afaab37bc2a0054f5af9b2d413b17c7c12b31bd4a66eaed0b9b86fbe07",
            ],
        },
        "danh_tinh_he_duoc_do": {
            "HEAD": "5e1a28c",
            "cache_version": CACHE_VERSION,
            "candidate": "adbb35144a82474c",
            "product_variant": "C",
            "CURVED_OBLIQUE_SECTION_CAPABILITY":
                NANG_LUC_SAN_PHAM["curved_oblique_section"].trang_thai,
            "card_C_sha256": _h(the),
            "card_C_bytes": len(the.encode("utf-8")),
            "card_day_du_sha256": _h(grammar_card()),
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
            "name": G.MODEL, "version_or_snapshot": "",
            "reproducibility": "LIMITED — alias, khong phai snapshot",
            "product_repair_limit_unchanged": 3,
        },
        "muc_giu_nguyen": {
            "PRODUCT_CAPABILITY_CHANGED": "NO",
            "ma_san_pham": "KHONG doi trong luot do",
            "model_facing_contract": "KHONG doi trong luot do",
        },
    }


def main() -> int:
    gold, scorer = tien_kiem_gold(), tien_kiem_scorer()
    dk = dang_ky()
    dk["GOLD_PREFLIGHT"] = gold["GOLD_PREFLIGHT"]
    dk["SCORER_PREFLIGHT"] = scorer["SCORER_PREFLIGHT"]
    dk["registration_sha256"] = _h(
        json.dumps(dk, ensure_ascii=False, sort_keys=True))

    RA.mkdir(parents=True, exist_ok=True)
    for ten, o in (("registration.json", dk), ("PREFLIGHT_GOLD.json", gold),
                   ("PREFLIGHT_SCORER.json", scorer)):
        p = RA / ten
        if p.exists():
            print(f"⚠️  {ten} da ton tai — KHONG ghi de artifact luot cu.")
            continue
        p.write_text(json.dumps(o, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print("→", p)

    print(json.dumps(gold, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in scorer.items() if k.isupper()},
                     ensure_ascii=False, indent=1))
    if gold["GOLD_PREFLIGHT"] != "PASS" or scorer["SCORER_PREFLIGHT"] != "PASS":
        print("\n⛔ TIEN KIEM CHUA DAT — KHONG duoc goi provider.")
        return 1
    print("\n✅ CA HAI TIEN KIEM DAT — provider duoc phep goi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
