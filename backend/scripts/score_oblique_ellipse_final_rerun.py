# -*- coding: utf-8 -*-
"""§10 + §11 — chấm lượt cuối và so với hai raw candidate lịch sử. 0 lượt gọi.

Artifact lượt chạy giữ nguyên từng byte; file này ghi `SCORING.json` cạnh nó.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from score_oblique_ellipse_fresh import cham_analyze, cham_synthesis  # noqa: E402

EVAL = BACKEND.parent / "docs" / "evaluation" / "geometry"
RA = EVAL / "oblique-ellipse-final-card-rerun"

#: Hai raw candidate lịch sử, khoá bằng băm ở registration.
LICH_SU = {
    "150ab4f1d6e7656f87795e0b61c2f65d349c458972131f48915426adb2ad9602":
        "oblique-ellipse-after-axis-scale-repair · attempt 0",
    "da8e60afaab37bc2a0054f5af9b2d413b17c7c12b31bd4a66eaed0b9b86fbe07":
        "oblique-ellipse-fresh-confirmation · attempt 1",
}


def _dap_so(final_memory: str, sc: dict) -> str:
    """`16π√5` nếu CẢ HAI nguồn đồng ý; nếu lệch thì nói ra là lệch."""
    radical = ("Radical(he=Fraction(16, 1), can=5, mu=1)" in str(final_memory))
    hien_thi = any("16π√5" in str(e.get("explanation"))
                   for e in sc.get("events", []))
    if radical and hien_thi:
        return "16π√5"
    if radical or hien_thi:
        return f"LECH_HAI_NGUON (radical={radical}, trace={hien_thi})"
    return "KHONG DOC DUOC"


def main() -> int:
    art = sorted(glob.glob(str(RA / "e2e_*.json")))
    if not art:
        print("Khong tim thay artifact luot chay.")
        return 1
    p = Path(art[-1])
    tho = p.read_text(encoding="utf-8")
    d = json.loads(tho)

    uv = [u["raw"] for u in d.get("ung_vien_tho", [])]
    attempts = []
    for i, raw in enumerate(uv):
        su = next((a for a in d.get("attempts", []) if a.get("n") == i), {})
        muc = {"attempt": i,
               "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()}
        muc.update(cham_synthesis(json.loads(raw)))
        muc["STAGE_CUOI"] = su.get("gate") or d["cham"]["ket_qua"]["STAGE"]
        muc["LOI_DAU_TIEN"] = su.get("message")
        muc["REPAIRABLE"] = su.get("repairable")
        attempts.append(muc)

    dr = sum(1 for a in attempts if a.get("DIRECT_RADIUS_USED"))
    rim = sum(1 for a in attempts if a.get("RIM_POINT_USED"))
    rim_hong = sum(1 for a in attempts
                   if a.get("RIM_POINT_USED")
                   and a.get("RIM_POINT_GROUNDED") is False)
    kq = d["cham"]["ket_qua"]
    sc = (d.get("envelope") or {}).get("scene3d") or {}

    ra = {
        "khai": "Cham artifact BAT BIEN, 0 luot goi model.",
        "wave": "OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN",
        "artifact": p.name,
        "sha256_artifact": hashlib.sha256(tho.encode("utf-8")).hexdigest(),
        # ⚠️ `nguon="RAW_ANALYZE"` là BẮT BUỘC. Thiếu nó, `cham_analyze` mặc
        # định `"KHONG_CO"` và trả `NOT_CAPTURED` cho mọi chiều fact — ĐÚNG
        # theo hợp đồng của nó (*"nguồn không mang nội dung fact ⇒
        # NOT_CAPTURED"*), nhưng SAI với thực tế: raw analyze có đủ nội dung.
        # Bộ chấm nói "không quan sát được" cho thứ nó quan sát được.
        "analyze": cham_analyze(
            json.loads(d["raw_theo_tang"]["semantic_analyze"][0]),
            nguon="RAW_ANALYZE"),
        "attempts": attempts,
        "hieu_qua_dong_card": {
            "HISTORICAL_DIRECT_RADIUS": "0/2",
            "HISTORICAL_RIM_POINT": "2/2",
            "raw_lich_su_sha256": sorted(LICH_SU),
            "CURRENT_DIRECT_RADIUS_CANDIDATES": dr,
            "CURRENT_RIM_POINT_CANDIDATES": rim,
            "CURRENT_UNGROUNDED_RIM_FAILURES": rim_hong,
            "CARD_LINE_ASSOCIATED_WITH_DESIRED_SELECTION":
                "YES" if dr and not rim else "NO",
            "CAUSAL_ATTRIBUTION": "LIMITED",
            "nhieu_da_khai": (
                "⚠️ HOP DONG ANALYZE cua luot nay TOT HON luot truoc — "
                "`ANALYZE_CONTRACT_CORRECT` PASS (6 fact, du toa do + ban "
                "kinh + truc + phuong trinh) so voi FAIL (4 o NOT_CAPTURED) "
                "o luot truoc. Do la mot BIEN SO THU HAI thay doi cung luc "
                "voi dong Card, nen khong quy duoc ket qua cho rieng dong "
                "Card. Day chinh la ly do `CAUSAL_ATTRIBUTION = LIMITED` va "
                "vi sao §2 cam ghi thanh ket luan A/B."),
        },
        "ket_qua": {
            "FIRST_ATTEMPT_SERVABLE": d["cham"]["FIRST_ATTEMPT_SERVABLE"],
            "EVENTUAL_SERVABLE": d["cham"]["EVENTUAL_SERVABLE"],
            "CANDIDATE_PROGRAM_ATTEMPTS": len(uv),
            "REPAIR_CALLS": 0,
            "STAGE": kq["STAGE"],
            "ENVELOPE_STATUS": kq["ENVELOPE_STATUS"],
            # ⚠️ Đọc từ HAI nguồn độc lập, không một. `FINAL_MEMORY` lưu
            # `repr` của `Radical` (`he=16, can=5, mu=1`), còn chuỗi hiển thị
            # `16π√5` chỉ có ở lời kể của trace. Bản đầu chỉ tra chuỗi trong
            # `FINAL_MEMORY` và trả `KHONG DOC DUOC` cho một đáp số ĐÚNG —
            # bộ chấm hỏi sai chỗ, không phải chương trình sai.
            "EXACT_ANSWER": _dap_so(kq["FINAL_MEMORY"], sc),
            "EXACT_ANSWER_NGUON": {
                "radical_trong_final_memory":
                    "Radical(he=Fraction(16, 1), can=5, mu=1)"
                    in str(kq["FINAL_MEMORY"]),
                "chuoi_hien_thi_trong_trace": any(
                    "16π√5" in str(e.get("explanation"))
                    for e in sc.get("events", [])),
            },
            "POSTCONDITIONS": "PASS" if kq["SERVABLE"] else "NOT_REACHED",
            "TRACE": "PASS" if any(
                "16π√5" in str(e.get("explanation"))
                for e in sc.get("events", [])) else "FAIL",
            "SCENE3D": "PASS" if any(
                o.get("type") == "ellipse3"
                for o in sc.get("objects", [])) else "FAIL",
            "scene3d_objects": len(sc.get("objects", [])),
            "scene3d_events": len(sc.get("events", [])),
        },
        "token": d["tokens"],
    }
    (RA / "SCORING.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=2), encoding="utf-8")
    print("→", RA / "SCORING.json")
    print(json.dumps({k: ra[k] for k in ("hieu_qua_dong_card", "ket_qua")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
