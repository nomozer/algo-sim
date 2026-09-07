# -*- coding: utf-8 -*-
"""Chấm BA CHIỀU ĐỘC LẬP cho `MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`.

**0 lượt gọi model** — chấm lại artifact đã có.

    cd backend && .venv/Scripts/python.exe scripts/score_minimal_card_confirmation.py

Ba chiều **không trộn vào nhau**, và đó là chủ đích:

    HIỂU QUAN HỆ      đọc từ `statements` — thứ tự toán hạng, `t` theo Fraction
    PROVENANCE        đọc từ `memory_declarations` của RAW CANDIDATE, nên nó
                      ĐỘC LẬP với việc lượt ấy có `served` hay không
    KẾT QUẢ SẢN PHẨM  đọc từ outcome — grounding … served

Tầng chưa chạy ghi `NOT_REACHED`. ⚠️ `semantic_program` **thuộc** tập
`NOT_REACHED` — đính chính của `PROVENANCE_AFFORDANCE_AB_4_LUOT §6`; chấm PASS
cho một tầng chưa bao giờ chạy là lỗi đã mắc một lần.
"""
from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gold_minimal_card_confirmation import BO, CORPUS, RA  # noqa: E402

CA = {c["case_id"]: c for c in CORPUS}
NR = "NOT_REACHED"
#: Tầng mà lượt chạy DỪNG ở đó ⇒ mọi tầng sau chưa từng chạy.
DUNG_SOM = {"semantic_program", "execution", "grounding", "coverage",
            "source_invariant", "runtime", "postconditions"}


def _fr(x) -> Fraction | None:
    try:
        return Fraction(str(x))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def _decl(ct: dict, ten: str) -> dict:
    for m in (ct.get("memory_declarations") or []):
        if m.get("name") == ten:
            return m
    return {}


def _lenh_dung(ct: dict, ten: str) -> dict | None:
    for s in (ct.get("statements") or []):
        if s.get("target_var") == ten:
            return s
    return None


def cham_quan_he(cid: str, ct: dict) -> dict[str, Any]:
    """Thứ tự toán hạng + `t` — đọc chiều THỰC TẾ, không giả định."""
    goc, kia, diem, t_thuan, _, _ = BO[cid]
    st = _lenh_dung(ct, diem)
    ex = (st or {}).get("expr") or {}
    if ex.get("kind") != "divide_segment":
        return {"DIVIDE_SEGMENT_USED": False, "OPERAND_ORDER": None,
                "T_WRITTEN": None, "T_RESOLVED": None,
                "T_EXPECTED_FOR_ORDER": None, "RATIO_CORRECT": "FAIL"}
    a, b = ex.get("a"), ex.get("b")
    order = f"{a}->{b}"
    mong = CA[cid]["t_theo_thu_tu"].get(order)
    viet = ex.get("ratio")

    # `ratio` có thể là TÊN một biến; giải nó ra để tách hai câu hỏi khác nhau:
    # "số học có đúng không" và "cách viết có groundable không".
    giai = viet
    gian_tiep = False
    if _fr(viet) is None and isinstance(viet, str):
        d = _decl(ct, viet)
        if d:
            gian_tiep = True
            giai = d.get("initial_value")

    fv, fm = _fr(giai), _fr(mong)
    dung = fv is not None and fm is not None and fv == fm
    return {
        "DIVIDE_SEGMENT_USED": True,
        "OPERAND_ORDER": order,
        "T_WRITTEN": viet,
        "T_RESOLVED": str(giai) if giai is not None else None,
        "T_LA_THAM_CHIEU_GIAN_TIEP": gian_tiep,
        "T_EXPECTED_FOR_ORDER": mong,
        # Tiêu chí đăng ký: "dung `t` bang Fraction". Một tham chiếu gián tiếp
        # KHÔNG phải Fraction ⇒ FAIL, dù số học bên trong có thể đúng. Ghi cả
        # hai để người đọc sau không phải đoán.
        "RATIO_ARITHMETIC_CORRECT": "PASS" if dung else "FAIL",
        "RATIO_CORRECT": "PASS" if (dung and not gian_tiep) else "FAIL",
    }


def cham_provenance(cid: str, ct: dict) -> dict[str, Any]:
    """Đọc từ RAW CANDIDATE ⇒ độc lập với tầng hỏng phía sau."""
    goc, kia, diem, _, _, _ = BO[cid]
    d_goc, d_kia, d_diem = _decl(ct, goc), _decl(ct, kia), _decl(ct, diem)

    def _kenh(d):
        if d.get("model_assumption"):
            return "ma"
        if d.get("source_fact_id"):
            return "sfid"
        return "THIEU"

    kenh_goc = _kenh(d_goc)
    kia_truy_duoc = bool(d_kia.get("source_fact_id")
                         or d_kia.get("model_assumption"))
    st = _lenh_dung(ct, diem)
    diem_do_lenh_tao = bool(st) and d_diem.get("initial_value") in (None, [])
    ok = (kenh_goc != "THIEU") and kia_truy_duoc and diem_do_lenh_tao
    return {
        "PROVENANCE": "PASS" if ok else "FAIL",
        "GOC_KENH": kenh_goc,
        "GOC_CO_CA_HAI_KENH": bool(d_goc.get("model_assumption")
                                   and d_goc.get("source_fact_id")),
        "KIA_TRUY_DUOC": kia_truy_duoc,
        "DIEM_DAN_XUAT_DO_LENH_TAO": diem_do_lenh_tao,
        "DIEM_DAN_XUAT_KHAI_THANG_TOA_DO": d_diem.get("initial_value") not in (None, []),
    }


def cham_san_pham(cid: str, a: dict) -> dict[str, Any]:
    """Bảy tầng; tầng chưa chạy là `NOT_REACHED`, không phải PASS."""
    _, _, diem, _, wit, dap = BO[cid]
    c = a.get("cham") or {}
    stage = a.get("stage")
    scene = a.get("scene3d_objects")
    M = None
    for o in (scene or []) if isinstance(scene, list) else []:
        if str(o.get("id")) == diem:
            M = o
    return {
        "GROUNDING": c.get("GROUNDING_RESULT", NR),
        "SOURCE_INVARIANT": c.get("SOURCE_INVARIANT_RESULT", NR),
        "RUNTIME": c.get("RUNTIME_RESULT", NR),
        "POSTCONDITIONS": c.get("POSTCONDITIONS_RESULT", NR),
        "EXACT_ANSWER": ("PASS" if c.get("ANSWER_OBSERVED") == dap
                         else (NR if stage in DUNG_SOM else "FAIL")),
        "ANSWER_OBSERVED": c.get("ANSWER_OBSERVED"),
        "ANSWER_EXPECTED": dap,
        "SCENE3D": c.get("SCENE3D_RESULT", NR),
        "SERVABLE": bool(a.get("servable")),
        "STAGE": stage,
        "PRODUCER": (M or {}).get("producer"),
        "ORIGIN": (M or {}).get("origin"),
        "DEPENDS": (M or {}).get("depends"),
        "SCENE_OBJS": len(scene) if isinstance(scene, list) else None,
    }


def main() -> int:
    arts = sorted(RA.glob("ratio_ab_*.json"))
    if not arts:
        print("Không tìm thấy artifact lượt chạy.")
        return 2
    art = arts[-1]
    raw = art.read_bytes()
    d = json.loads(raw.decode("utf-8"))
    nhan = d["manifest"]["arm_labels"]

    rows: list[dict[str, Any]] = []
    for r in d["ket_qua"]:
        cid = r["case_id"]
        for khoa, a in r["arms"].items():
            ct = a.get("chuong_trinh") or {}
            rows.append({
                "cid": cid, "arm": nhan.get(khoa, khoa),
                **cham_quan_he(cid, ct),
                **cham_provenance(cid, ct),
                **cham_san_pham(cid, a),
                "tokens": a.get("tokens") or {},
                "card_hash": a.get("card_hash"),
            })

    def _dem(arm, khoa, gt="PASS"):
        return sum(1 for x in rows if x["arm"] == arm and x[khoa] == gt)

    def _tok(arm, truong):
        return sum((x["tokens"] or {}).get(truong) or 0
                   for x in rows if x["arm"] == arm)

    tong: dict[str, Any] = {}
    for arm in ("A0", "C"):
        n = sum(1 for x in rows if x["arm"] == arm)
        srv = sum(1 for x in rows if x["arm"] == arm and x["SERVABLE"])
        tot = _tok(arm, "total_tokens")
        tong[arm] = {
            "n": n,
            "RATIO_CORRECT": f"{_dem(arm, 'RATIO_CORRECT')}/{n}",
            "RATIO_ARITHMETIC_CORRECT": f"{_dem(arm, 'RATIO_ARITHMETIC_CORRECT')}/{n}",
            "PROVENANCE_CORRECT": f"{_dem(arm, 'PROVENANCE')}/{n}",
            "DERIVED_POINT_CONSTRUCTED":
                f"{sum(1 for x in rows if x['arm'] == arm and x['DIEM_DAN_XUAT_DO_LENH_TAO'])}/{n}",
            "CORRECT_SERVABLE": f"{srv}/{n}",
            "tokens": {t: _tok(arm, t) for t in
                       ("prompt_tokens", "candidates_tokens", "thoughts_tokens",
                        "cached_content_tokens", "total_tokens")},
            "TOKENS_PER_CORRECT_SERVABLE": (
                round(tot / srv) if srv else f"UNDEFINED (0 ca; tổng {tot})"),
            "TOKENS_PER_PROVENANCE_CORRECT": (
                round(tot / _dem(arm, "PROVENANCE"))
                if _dem(arm, "PROVENANCE")
                else f"UNDEFINED (0 ca; tổng {tot})"),
        }

    # Ghép cặp trên trục `served` đúng — cùng ca, hai arm.
    thang = thua = hoa = 0
    for cid in ("f1", "f2"):
        a0 = next(x for x in rows if x["cid"] == cid and x["arm"] == "A0")
        cc = next(x for x in rows if x["cid"] == cid and x["arm"] == "C")
        if cc["SERVABLE"] and not a0["SERVABLE"]:
            thang += 1
        elif a0["SERVABLE"] and not cc["SERVABLE"]:
            thua += 1
        else:
            hoa += 1

    ra = {
        "khai": "Cham 3 chieu DOC LAP (quan he / provenance / san pham). "
                "0 luot goi them. Tang chua chay = NOT_REACHED.",
        "wave": "MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION",
        "artifact": art.name,
        "sha256_artifact": hashlib.sha256(raw).hexdigest(),
        "arm_labels": nhan,
        "rows": rows,
        "tong_hop": tong,
        "PAIRED_servable": {"WINS_C": thang, "LOSSES_C": thua, "TIES": hoa},
        "A0_CORRECT_AND_C_INCORRECT": sum(
            1 for cid in ("f1", "f2")
            if next(x for x in rows if x["cid"] == cid and x["arm"] == "A0")["SERVABLE"]
            and not next(x for x in rows if x["cid"] == cid and x["arm"] == "C")["SERVABLE"]),
        "TOTAL_TOKENS": (d.get("tokens") or {}).get("tong"),
        "bo_dem": d["manifest"].get("bo_dem"),
    }
    p = RA / "SCORING.json"
    p.write_text(json.dumps(ra, ensure_ascii=False, indent=2),
                 encoding="utf-8", newline="\n")
    print(f"→ {p}")
    for x in rows:
        print(f"  {x['cid']} {x['arm']:3} ratio={x['RATIO_CORRECT']:4}"
              f" (số học {x['RATIO_ARITHMETIC_CORRECT']:4})"
              f" prov={x['PROVENANCE']:4} goc={x['GOC_KENH']:5}"
              f" served={str(x['SERVABLE']):5} stage={x['STAGE']}")
    for arm in ("A0", "C"):
        t = tong[arm]
        print(f"  {arm}: ratio {t['RATIO_CORRECT']} · prov {t['PROVENANCE_CORRECT']}"
              f" · dựng điểm {t['DERIVED_POINT_CONSTRUCTED']}"
              f" · served {t['CORRECT_SERVABLE']}"
              f" · token {t['tokens']['total_tokens']}")
    print(f"  ghép cặp (served): C thắng {thang} · thua {thua} · hoà {hoa}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
