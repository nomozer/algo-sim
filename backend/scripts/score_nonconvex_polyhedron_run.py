# -*- coding: utf-8 -*-
"""§6 + §7 — chấm lượt live của `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY`.

0 lượt gọi. Artifact lượt chạy giữ nguyên từng byte; file này ghi `SCORING.json`
cạnh nó.

Năm nhãn của §2 được tách bạch **có chủ đích**, và tiền kiểm đã chứng minh
chúng tách được: phản ví dụ ① (đáy khai bằng quạt tam giác) cho `EXACT_VOLUME
= PASS` cùng lúc với `FACE_TABLE_VALID = FAIL` và
`SCENE3D_CONCAVITY_PRESERVED = False`. Gộp chúng làm một là cho điểm tuyệt đối
một chương trình vẽ sai hình.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gold_nonconvex_polyhedron import ORACLE  # noqa: E402
from score_nonconvex_polyhedron import cham_analyze, cham_synthesis  # noqa: E402

EVAL = BACKEND.parent / "docs" / "evaluation" / "geometry"
RA = EVAL / "nonconvex-polyhedron-model-discoverability"
DAP_SO = ORACLE["dap_so_hien_thi"]


def _lom_con_nguyen(sc: dict) -> tuple[bool, dict]:
    """`SCENE3D_CONCAVITY_PRESERVED` — đo trên CẢNH ĐÃ DỰNG của envelope.

    Chương trình đúng mà cảnh làm phẳng chỗ lõm thì thứ học sinh nhìn thấy vẫn
    sai, nên chiều này KHÔNG được suy từ bảng mặt.
    """
    khoi = next((o for o in sc.get("objects", [])
                 if o.get("render") == "mesh" and o.get("faces")), None)
    if not khoi:
        return False, {"ly_do": "cảnh không có khối mesh"}
    day = [f for f in khoi["faces"] if len(f) == 5]
    if len(day) != 1:
        return False, {"ly_do": "không có đúng một mặt 5 đỉnh",
                       "faces": khoi["faces"]}
    xy = [(F(khoi["vertices"][j][0]), F(khoi["vertices"][j][1]))
          for j in day[0]]
    cheo = []
    for i in range(5):
        p, q, r = xy[i], xy[(i + 1) % 5], xy[(i + 2) % 5]
        cheo.append((q[0] - p[0]) * (r[1] - p[1])
                    - (q[1] - p[1]) * (r[0] - p[0]))
    duong = sum(1 for c in cheo if c > 0)
    am = sum(1 for c in cheo if c < 0)
    ok = 0 not in cheo and min(duong, am) == 1
    return ok, {"day_chi_so": day[0], "tich_co_huong": [str(c) for c in cheo],
                "so_dinh_phan_xa": min(duong, am),
                "thang_hang": 0 in cheo}


def _dap_so(fm, sc: dict) -> str:
    """Đọc từ HAI nguồn độc lập; lệch thì NÓI RA là lệch.

    Bản đầu của bộ chấm lượt elip chỉ tra một nguồn và trả `KHONG DOC DUOC`
    cho một đáp số ĐÚNG — bộ chấm hỏi sai chỗ, không phải chương trình sai.
    """
    fraction = f"Fraction({DAP_SO}, 1)" in str(fm)
    trace = any(DAP_SO in str(e.get("explanation")) for e in sc.get("events", []))
    if fraction and trace:
        return DAP_SO
    if fraction or trace:
        return f"LECH_HAI_NGUON (memory={fraction}, trace={trace})"
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
        try:
            muc.update(cham_synthesis(json.loads(raw)))
        except json.JSONDecodeError as e:                         # noqa: PERF203
            muc["SYNTHESIS_SCORED"] = False
            muc["json_error"] = str(e)[:200]
        muc["STAGE_CUOI"] = su.get("gate") or d["cham"]["ket_qua"].get("STAGE")
        muc["LOI_DAU_TIEN"] = su.get("message")
        muc["REPAIRABLE"] = su.get("repairable")
        attempts.append(muc)

    kq = d["cham"]["ket_qua"]
    sc = (d.get("envelope") or {}).get("scene3d") or {}
    lom_ok, lom_chi_tiet = _lom_con_nguyen(sc)
    cuoi = attempts[-1] if attempts else {}
    dap_so = _dap_so(kq.get("FINAL_MEMORY"), sc)

    exact = "PASS" if dap_so == DAP_SO else "FAIL"
    bang_mat = cuoi.get("FACE_TABLE_VALID", "NOT_REACHED")
    servable = bool(kq.get("SERVABLE"))
    dau_tien = bool(d["cham"]["FIRST_ATTEMPT_SERVABLE"])
    # THÀNH CÔNG = mọi chiều, không chỉ `served`.
    thanh_cong = (servable and exact == "PASS" and bang_mat == "PASS"
                  and lom_ok and kq.get("ENVELOPE_STATUS") == "ok")

    ra = {
        "khai": "Cham artifact BAT BIEN, 0 luot goi model.",
        "wave": "NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY",
        "artifact": p.name,
        "sha256_artifact": hashlib.sha256(tho.encode("utf-8")).hexdigest(),
        "analyze": cham_analyze(
            json.loads(d["raw_theo_tang"]["semantic_analyze"][0]),
            nguon="RAW_ANALYZE") if d.get("raw_theo_tang", {}).get(
                "semantic_analyze") else {"ANALYZE_CONTRACT_CORRECT":
                                          "NOT_CAPTURED"},
        "attempts": attempts,
        "ket_qua": {
            "FIRST_ATTEMPT_DISCOVERABLE": "YES" if (dau_tien and thanh_cong)
                                          else "NO",
            "REPAIR_ASSISTED_DISCOVERABLE": (
                "YES" if (thanh_cong and not dau_tien)
                else "NOT_NEEDED" if thanh_cong else "NO"),
            "MODEL_DISCOVERABLE_ON_THIS_PROBE": "YES" if thanh_cong else "NO",
            "FACE_TABLE_VALID": bang_mat,
            "EXACT_VOLUME": exact,
            "EXACT_VOLUME_DOC_DUOC": dap_so,
            "SCENE3D_CONCAVITY_PRESERVED": "YES" if lom_ok else "NO",
            "scene3d_lom_chi_tiet": lom_chi_tiet,
            "FIRST_ATTEMPT_SERVABLE": dau_tien,
            "EVENTUAL_SERVABLE": bool(d["cham"]["EVENTUAL_SERVABLE"]),
            "CANDIDATE_PROGRAM_ATTEMPTS": len(uv),
            "REPAIR_CALLS": max(0, len(uv) - 1),
            "STAGE": kq.get("STAGE"),
            "ENVELOPE_STATUS": kq.get("ENVELOPE_STATUS"),
            "FAILURE_STAGE": None if thanh_cong else kq.get("STAGE"),
            "FAILURE_ATTRIBUTION": (
                "NONE" if thanh_cong
                # Gold cùng cấu trúc đã PASS ở tiền kiểm ⇒ không phải lỗi hệ.
                else "MODEL_FAILURE" if bang_mat == "FAIL"
                else "ATTRIBUTION_UNRESOLVED"),
            "TRACE": "PASS" if any(DAP_SO in str(e.get("explanation"))
                                   for e in sc.get("events", [])) else "FAIL",
            "scene3d_objects": len(sc.get("objects", [])),
            "scene3d_events": len(sc.get("events", [])),
        },
        "ke_toan": {
            "LOGICAL_APPLICATION_CALLS":
                d["manifest"]["bo_dem"]["logical_application_calls"],
            "PHYSICAL_API_ATTEMPTS":
                d["manifest"]["bo_dem"]["physical_api_attempts"],
            "TRANSPORT_RETRIES":
                d["manifest"]["bo_dem"]["phan_ra"]["retry_requests"],
            "TOTAL_TOKENS": d["tokens"].get("tong"),
            "TOKEN_CEILING": d["manifest"]["token_ceiling_observed"],
            "theo_stage": d["tokens"].get("theo_stage"),
            "RUN_STATUS": d["manifest"]["run_status"],
        },
        "pham_vi_ket_luan": {
            "STABILITY_UNDER_ACCEPTANCE": "NOT_MEASURED",
            "khai": ("MOT ca, MOT luot. Khong noi duoc gi ve on dinh, va "
                     "khong khai quat sang hinh khac."),
            "CAPABILITY_STATUS": "foundation_only",
            "PRODUCT_PROMOTION_ELIGIBLE": "NO",
        },
    }
    if thanh_cong:
        ra["pham_vi_ket_luan"]["NONCONVEX_POLYHEDRON_SEQUENCE"] = \
            "CLOSED_AT_DEVELOPMENT_LEVEL"

    (RA / "SCORING.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=2), encoding="utf-8")
    print("→", RA / "SCORING.json")
    print(json.dumps({"ket_qua": ra["ket_qua"], "ke_toan": ra["ke_toan"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
