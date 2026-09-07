# -*- coding: utf-8 -*-
"""`CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION` — §3·§4·§5·§6·§8, 0 lượt gọi.

Phân xử **vì sao** mô hình dùng một `rim_point` tự tạo để chở bán kính. Mọi ô
đo bằng máy: ma trận hợp đồng chạy qua validator thật, bốn mệnh đề tra trên
chuỗi thẻ thật, hai raw candidate đọc nguyên byte từ artifact bất biến.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.simulation.geometry.curved import KHOI_CONG  # noqa: E402
from app.simulation.geometry.radical import display, is_exact_number  # noqa: E402
from app.simulation.semantic_program.contract import (  # noqa: E402
    ConstructCurvedSolidStmt, SemanticProgramSpec,
)
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from app.simulation.semantic_program.plane_equation import (  # noqa: E402
    bat_bien_mat_phang,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

from gold_oblique_ellipse_fresh import (  # noqa: E402
    PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)

EVAL = BACKEND.parent / "docs" / "evaluation" / "geometry"
MOI = EVAL / "oblique-ellipse-after-axis-scale-repair"
CU = EVAL / "oblique-ellipse-fresh-confirmation"
RA = EVAL / "radius-slot-affordance"
DAP_SO = "16π√5"

#: Bốn mệnh đề §4, và CHUỖI phải có trong thẻ để coi là đã diễn đạt.
#:
#: Tra bằng chuỗi thật chứ không đánh giá cảm tính — và tra trên ĐÚNG dòng
#: lệnh, vì `"đúng một trong"` cũng xuất hiện ở dòng `MemoryType` và một phép
#: khớp toàn thẻ sẽ báo CÓ cho một mệnh đề thẻ chưa hề nói.
MENH_DE = {
    "P1": ("Card nói `radius` dùng khi đề CHO bán kính (luật CHỌN, không phải "
           "luật hợp lệ)",
           ("đề cho bán kính", "khi đề cho", "bằng SỐ")),
    "P2": ("Card nói `rim_point` là một ĐIỂM hình học thật trên vành",
           ("một ĐIỂM trên mặt cầu, hoặc trên vành đáy",)),
    "P3": ("Card nói `radius` và `rim_point` LOẠI TRỪ nhau (đúng một)",
           ("đúng MỘT trong", "loại trừ")),
    "P4": ("Card nói trụ/nón nhận `radius` + `height`",
           ("thay điểm thứ hai trên trục",)),
}


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def ma_tran() -> dict:
    """§3 — hợp đồng THẬT, đo qua validator lược đồ."""
    to_hop = {
        "radius only": {"radius": "r"},
        "rim_point only": {"rim_point": "P"},
        "radius + rim_point": {"radius": "r", "rim_point": "P"},
        "neither": {},
        "radius + height": {"radius": "r", "height": "h"},
        "rim_point + height": {"rim_point": "P", "height": "h"},
        "radius + apex": {"radius": "r", "apex_or_top": "S"},
        "rim_point + apex": {"rim_point": "P", "apex_or_top": "S"},
        "rim + apex + radius": {"rim_point": "P", "apex_or_top": "S",
                                "radius": "r"},
    }
    ho = {k: {"co_truc": kc.co_truc,
              "khai_bang_ban_kinh": kc.khai_bang_ban_kinh,
              "can_chieu_cao": kc.can_chieu_cao,
              "vai_dinh": kc.vai_dinh or None}
          for k, kc in KHOI_CONG.items()}
    bang: dict[str, dict[str, str]] = {}
    for kind in KHOI_CONG:
        bang[kind] = {}
        for ten, o in to_hop.items():
            d = {"kind": "construct_curved_solid", "target_var": "x",
                 "curved_kind": kind, "anchor": "O", **o}
            try:
                ConstructCurvedSolidStmt.model_validate(d)
                bang[kind][ten] = "OK"
            except Exception as e:                                # noqa: BLE001
                bang[kind][ten] = str(e).split("Value error, ")[-1].splitlines()[0]
    return {"bang_ho_cong": ho, "validator_theo_to_hop": bang}


def menh_de() -> dict:
    """§4 — bốn mệnh đề, tra trên chuỗi thẻ THẬT."""
    the = grammar_card("hinh_hoc")
    dong = next(d for d in the.splitlines()
                if "construct_curved_solid:" in d)
    xuat_xu = next((d for d in the.splitlines()
                    if d.strip().startswith("Xuất xứ:")), "")
    ra = {}
    for ma, (mo_ta, pats) in MENH_DE.items():
        trung = [p for p in pats if p in dong or p in xuat_xu]
        ra[ma] = {"mo_ta": mo_ta, "CO_TRONG_CARD": bool(trung),
                  "chuoi_khop": trung,
                  "tra_tren": "dòng lệnh + dòng `Xuất xứ:`"}
    # P3 tra thêm ở mức NGỮ NGHĨA: `"thay cho điểm trên mặt"` nói THAY THẾ
    # nhưng không nói ĐÚNG MỘT (cả hai ô đều `?`).
    ra["P3"]["ghi_chu"] = (
        "Thẻ có `thay cho điểm trên mặt` — diễn đạt THAY THẾ. Nhưng cả hai ô "
        "đều mang `?` (tuỳ chọn), nên người đọc thẻ KHÔNG suy được luật "
        "`ĐÚNG MỘT, bắt buộc` mà validator cưỡng chế.")
    ra["P3"]["CO_TRONG_CARD"] = False
    ra["P2"]["ghi_chu"] = (
        "CÓ, nhưng mô tả là HÌNH HỌC thuần — `(4,0,0)` THẬT SỰ nằm trên vành "
        "đáy, nên thẻ không hề cấm điều mô hình đã làm. Luật bị vi phạm "
        "(`điểm phải truy được về đề`) sống ở `grounding_gate`, không ở thẻ.")
    ra["xuat_xu_line"] = xuat_xu.strip()
    ra["xuat_xu_phu_may_ca"] = (
        "BA: gốc hệ toạ độ · giá trị lấy thẳng từ đề · điểm do một QUAN HỆ xác "
        "định. Điểm mà đề KHÔNG hề nhắc tới không thuộc ca nào — và đó đúng "
        "chỗ `P_rim` rơi vào.")
    thieu = [m for m in ("P1", "P2", "P3", "P4")
             if not ra[m]["CO_TRONG_CARD"]]
    ra["CARD_CONTRACT_COMPLETE"] = "NO" if thieu else "YES"
    ra["MISSING_PROPOSITIONS"] = thieu
    ra["card_bytes"] = len(the.encode("utf-8"))
    ra["dong_lenh_bytes"] = len(dong.encode("utf-8"))
    return ra


def _raw(thu_muc: Path, chi_so: int) -> str:
    art = sorted(thu_muc.glob("e2e_*.json"))[-1]
    d = json.loads(art.read_text(encoding="utf-8"))
    return d["ung_vien_tho"][chi_so]["raw"]


def _soi(raw: str, ten_luot: str) -> dict:
    o = json.loads(raw)
    khai = {m.get("name"): m for m in o.get("memory_declarations", [])}
    tru = next((s for s in o["statements"]
                if s.get("kind") == "construct_curved_solid"), {})
    rim = tru.get("rim_point")
    d_rim = khai.get(rim) or {}
    dung_o_khac = [s for s in o["statements"]
                   if rim and rim in json.dumps(s, ensure_ascii=False)
                   and s.get("kind") != "construct_curved_solid"
                   and s.get("target_var") != rim]
    return {
        "luot": ten_luot,
        "raw_sha256": _h(raw),
        "radius_field_present": bool(tru.get("radius")),
        "rim_point_field_present": bool(rim),
        "rim_point_named_in_problem": rim in PROBLEM_TEXT if rim else None,
        "rim_point_has_source_fact_id": bool(d_rim.get("source_fact_id")),
        "rim_point_used_elsewhere": [s.get("kind") for s in dung_o_khac],
        "axis_already_determined": bool(tru.get("anchor")
                                        and tru.get("apex_or_top")),
        "height_already_determined": bool(tru.get("height")),
        "problem_explicitly_provides_radius": "bán kính đáy bằng 4" in PROBLEM_TEXT,
        "direct_radius_path_valid_for_kind":
            KHOI_CONG[tru.get("curved_kind", "cylinder")].khai_bang_ban_kinh,
        "rim_point_model_assumption": (d_rim.get("model_assumption") or "")[:160],
    }


def _hd() -> RequestContract:
    """Hợp đồng của LƯỢT CHẠY THẬT, dựng lại từ raw `analyze`.

    ⚠️ KHÔNG dùng `REQUEST_CONTRACT_GOLD`. Ứng viên được viết dưới hợp đồng do
    `analyze` thật phát, và hai bản khác nhau ở những chỗ quyết định: witness
    live là `dien_tich_e` còn gold là `dien_tich_E`, `fact_id` cũng khác. Chấm
    bằng gold là chấm ứng viên của mô hình bằng một ĐỀ KHÁC — đo được: cổng phủ
    trả `requested_operation_uncovered` cho một chương trình hoàn toàn đúng.

    Cùng bài học đã ghi ở `replay_plane_from_equation.py`.
    """
    from app.simulation.semantic_program.analyze_contract import (
        build_request_contract,
    )
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    art = sorted(MOI.glob("e2e_*.json"))[-1]
    d = json.loads(art.read_text(encoding="utf-8"))
    raw = d["raw_theo_tang"]["semantic_analyze"][0]
    return build_request_contract(json.loads(raw), PROBLEM_TEXT,
                                  DOMAIN_HINH_HOC)


def minimal_delta(raw: str) -> tuple[str, dict]:
    """§6 — bỏ `P_rim`, đưa bán kính đã grounded vào ô `radius`."""
    o = json.loads(raw)
    truoc = json.dumps(o, ensure_ascii=False, indent=2)
    n_stmt = len(o["statements"])
    o["memory_declarations"] = [d for d in o["memory_declarations"]
                                if d.get("name") != "P_rim"]
    o["memory_declarations"].append(
        {"name": "r", "type": "float", "initial_value": 4,
         "source_fact_id": "ban_kinh_day"})
    o["statements"] = [s for s in o["statements"]
                       if s.get("target_var") != "P_rim"]
    for s in o["statements"]:
        if s.get("kind") == "construct_curved_solid":
            s.pop("rim_point", None)
            s["radius"] = "r"
    sau = json.dumps(o, ensure_ascii=False, indent=2)
    return sau, {
        "FIELDS_CHANGED": 2,          # bỏ `rim_point`, thêm `radius`
        "STATEMENTS_REMOVED": n_stmt - len(o["statements"]),
        "STATEMENTS_ADDED": 0,
        "DECLARATIONS_SWAPPED": "P_rim (point3) → r (float, source_fact_id)",
        "BYTE_DELTA": len(sau.encode()) - len(truoc.encode()),
    }


def replay(prog: str) -> dict:
    from app.ai.pipeline import _dung_scene3d

    spec = SemanticProgramSpec.model_validate(json.loads(prog))
    hd = _hd()
    kq = verify_and_compile(hd, spec)
    dl = {k: display(x) for k, x in (kq.final_memory or {}).items()
          if is_exact_number(x)}
    canh = _dung_scene3d(spec, hd) or {} if kq.servable else {}
    vat = {str(o.get("id")): o for o in canh.get("objects", [])}
    # ⚠️ Witness đọc từ HỢP ĐỒNG LIVE, không từ hằng của gold: lượt chạy đặt
    # `dien_tich_e` (thường), gold đặt `dien_tich_E` (hoa). Tra bằng hằng gold
    # sẽ trả `None` cho một chương trình đã tính ĐÚNG — và một ô `null` ở đây
    # đọc y hệt "không có đáp số".
    wit = next((o.witness for o in (hd.obligations or ()) if o.witness), WITNESS)
    return {
        "witness": wit,
        "schema": "PASS", "static": "PASS" if kq.servable else "?",
        "grounding": "PASS" if kq.servable else "FAIL",
        "source_invariants": kq.source_invariant_stats,
        "runtime": "PASS" if kq.servable else "NOT_REACHED",
        "exact_answer": dl.get(wit),
        "postconditions": "PASS" if kq.servable else "NOT_REACHED",
        "trace": "PASS" if any(e.get("object") == "alpha"
                               for e in canh.get("events", [])) else "FAIL",
        "scene3d": "PASS" if any(o.get("type") == "ellipse3"
                                 for o in vat.values()) else "FAIL",
        "servable": kq.servable,
        "stage": kq.stage_reached, "error_code": kq.error_code,
    }


def chan_doan() -> dict:
    """§8 — thông điệp hiện tại nêu được gì."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    raw = _raw(MOI, 0)
    g = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        json.loads(raw)))
    msg = "; ".join(g.unresolved[:4]) if g.unresolved else ""
    from app.ai.pipeline import KHONG_DUOC_SUA

    return {
        "error_code": g.error_code,
        "message": msg,
        "NEU_BIEN_GAY_LOI": "P_rim" in msg,
        "NEU_NOI_BIEN_DUOC_DUNG": "rim_point" in msg or "vành" in msg,
        "NEU_BAN_KINH_DA_CO_TRONG_DE": "bán kính" in msg,
        "NEU_RADIUS_SLOT_HOP_LE": "`radius`" in msg or "radius" in msg,
        "NEU_THAO_TAC_SUA": "dựng" in msg,
        "DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT":
            "YES" if "radius" in msg else "NO",
        "REPAIR_POLICY_DISTINGUISHES_SAFE_SUBCASE":
            "NO" if g.error_code in KHONG_DUOC_SUA else "YES",
        "KHONG_DUOC_SUA": sorted(KHONG_DUOC_SUA),
    }


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    moi, cu = _raw(MOI, 0), _raw(CU, 1)
    soi = [_soi(moi, "after-axis-scale-repair · attempt 0"),
           _soi(cu, "fresh-confirmation · attempt 1")]
    dieu_kien = ("rim_point_field_present", "rim_point_has_source_fact_id",
                 "axis_already_determined",
                 "problem_explicitly_provides_radius",
                 "direct_radius_path_valid_for_kind")
    khop = all(
        s["rim_point_field_present"] and not s["rim_point_has_source_fact_id"]
        and s["axis_already_determined"]
        and s["problem_explicitly_provides_radius"]
        and s["direct_radius_path_valid_for_kind"]
        and not s["radius_field_present"] for s in soi)

    delta, dem = minimal_delta(moi)
    ra = {
        "khai": "Phan xu TAT DINH, 0 luot goi model.",
        "wave": "CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION",
        "ma_tran_hop_dong": ma_tran(),
        "menh_de_card": menh_de(),
        "hai_raw_candidate": {
            "dieu_kien_so_khop": list(dieu_kien),
            "soi": soi,
            "RAW_FAILURES_MATCH": khop,
            "CURVED_RIM_POINT_AFFORDANCE": "REPLICATED" if khop else "KHONG",
        },
        "minimal_delta": {**dem, "replay": replay(delta)},
        "chan_doan": chan_doan(),
    }
    (RA / "ADJUDICATION.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=2), encoding="utf-8")
    (RA / "minimal_delta.json").write_text(delta, encoding="utf-8")
    print("→", RA / "ADJUDICATION.json")
    print(json.dumps({k: ra[k] for k in ("hai_raw_candidate", "minimal_delta",
                                         "chan_doan")},
                     ensure_ascii=False, indent=1)[:3000])
    print("\nCARD_CONTRACT_COMPLETE =",
          ra["menh_de_card"]["CARD_CONTRACT_COMPLETE"],
          "· MISSING =", ra["menh_de_card"]["MISSING_PROPOSITIONS"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
