# -*- coding: utf-8 -*-
"""Chấm lượt XÁC NHẬN POSTFIX theo cổng đã đăng ký TRƯỚC. **0 API call.**

    python scripts/score_postfix_confirmation.py

⚠️ Đây **không** phải Phase 7B chính thức. Con số ở đây nói về hệ V2, và
không được trộn vào bảng của lượt chính thức.

─── CỔNG NÀY ĐƯỢC CỐ ĐỊNH TRƯỚC KHI CÓ KẾT QUẢ ───────────────────────────

Chín điều kiện, chép nguyên từ chỉ thị `§12` (đặt ra trước lượt chạy). Không
nới sau khi thấy số — nếu nới thì phải nói ra, và nói kèm số cũ.

`Fail-closed` tính là AN TOÀN nhưng **không** tính là correct executable IR.
Một hệ từ chối mọi thứ sẽ an toàn 100% và vô dụng; chỉ đọc hai trục cùng lúc
mới nói được gì.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "docs" / "evaluation" / "geometry"
RA = GEO / "postfix-confirmation"

#: CỔNG ĐÃ ĐĂNG KÝ. Sửa con số nào ở đây là đổi giả thuyết sau khi thấy dữ
#: liệu — phải khai, không được lặng lẽ.
NGUONG = {"repetitions": 12, "safe": 12, "correct_executable_ir": 10,
          "on_dinh": 5, "so_bai": 6}


def _tang_loi(r: dict) -> str | None:
    if r.get("servable"):
        return None
    st, ec = str(r.get("stage_reached")), str(r.get("error_code") or "")
    su = str(r.get("su_co") or "")
    if "429" in su or "RESOURCE_EXHAUSTED" in su or r.get("budget_aborted"):
        return "PROVIDER"
    if r.get("envelope_status") == "EXCEPTION":
        return "DETERMINISTIC"
    if st == "scope":
        return "SCOPE"
    if st == "grounding":
        return "GROUNDING"
    if "SCHEMA" in ec.upper() or st in ("semantic_program", "structural_coverage"):
        return "MODEL_SYNTHESIS"
    if st in ("postconditions", "learner_surface", "execution"):
        return "MODEL_SYNTHESIS"
    return "DETERMINISTIC"


def _ket_cuc(r: dict) -> str:
    if _tang_loi(r) == "PROVIDER":
        return "ha_tang"
    if r.get("servable"):
        o = r.get("oracle_dat")
        return "dung" if o is True else (
            "SAI_MA_VAN_NHAN" if o is False else "served_khong_cham_duoc")
    return "fail_closed"


def cham(rs: list[dict], k: int) -> dict:
    ids = sorted({r["case_id"] for r in rs})
    theo = {c: [r for r in rs if r["case_id"] == c] for c in ids}
    ex = [r for r in rs if r.get("executable") is True]
    correct = [r for r in rs if r.get("servable") and r.get("oracle_dat") is True]
    unsafe = [r for r in rs if _ket_cuc(r) == "SAI_MA_VAN_NHAN"]
    safe = [r for r in rs if _ket_cuc(r) in ("dung", "fail_closed")]
    on = [c for c, x in theo.items()
          if len(x) == k and len({_ket_cuc(r) for r in x}) == 1]
    nhom = Counter(t for r in rs if (t := _tang_loi(r)))
    tok = Counter()
    chang: dict[str, Counter] = {}
    for r in rs:
        for ten, v in (r.get("token") or {}).items():
            c = chang.setdefault(ten, Counter())
            for kk, x in v.items():
                tok[kk] += int(x or 0)
                c[kk] += int(x or 0)
    T = tok["total_tokens"]
    return {"so_luot": len(rs), "so_bai": len(ids), "k": k,
            "executable_ir": len(ex), "correct_executable_ir": len(correct),
            "safe": len(safe), "unsafe_accepted": len(unsafe),
            "served_khong_cham_duoc":
                sum(1 for r in rs if _ket_cuc(r) == "served_khong_cham_duoc"),
            "on_dinh": on, "so_on_dinh": len(on),
            "theo_bai": {c: [_ket_cuc(r) for r in x] for c, x in theo.items()},
            "nhom_loi": dict(nhom), "token": dict(tok),
            "token_theo_chang": {k2: dict(v) for k2, v in chang.items()},
            "tokens_moi_luot": round(T / len(rs)) if rs else 0,
            "tokens_moi_correct_ir": round(T / len(correct)) if correct else None}


def cong(d: dict) -> list[str]:
    """Chín điều kiện của `§12`. Trả danh sách điều KHÔNG đạt."""
    loi = []
    if d["so_luot"] != NGUONG["repetitions"]:
        loi.append(f"repetitions {d['so_luot']}/{NGUONG['repetitions']}")
    for n in ("PROVIDER",):
        if d["nhom_loi"].get(n):
            loi.append(f"{n} failure = {d['nhom_loi'][n]}, phải 0")
    if d["safe"] < NGUONG["safe"]:
        loi.append(f"SAFE_OUTCOME {d['safe']}/{NGUONG['safe']}")
    if d["correct_executable_ir"] < NGUONG["correct_executable_ir"]:
        loi.append(f"correct executable IR {d['correct_executable_ir']}/12 "
                   f"< {NGUONG['correct_executable_ir']}")
    if d["so_on_dinh"] < NGUONG["on_dinh"]:
        loi.append(f"stable cases {d['so_on_dinh']}/{d['so_bai']} "
                   f"< {NGUONG['on_dinh']}")
    for n in ("SCOPE", "GROUNDING"):
        if (x := d["nhom_loi"].get(n, 0)) >= d["k"]:
            loi.append(f"{n} failure có HỆ THỐNG: {x} lượt")
    if d["nhom_loi"].get("DETERMINISTIC", 0) >= d["k"]:
        loi.append(f"lỗi tất định LẶP LẠI: {d['nhom_loi']['DETERMINISTIC']} lượt")
    if d["unsafe_accepted"]:
        loi.append(f"accepted-but-wrong = {d['unsafe_accepted']}, phải 0")
    return loi


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in-dir", default=None)
    a = p.parse_args()
    ra = Path(a.in_dir) if a.in_dir else RA
    if not ra.is_absolute():
        ra = ROOT / ra
    sel = json.loads((RA / "CONFIRMATION_SELECTION.json").read_text(encoding="utf-8"))
    rs = [json.loads(f.read_text(encoding="utf-8"))["ban_ghi"]
          for f in sorted(ra.glob("hp_*-lan*.json"))]
    if not rs:
        print(f"Chưa có bản ghi ở {ra}")
        return 1

    d = cham(rs, sel["k"])
    print(f"⚠️ XÁC NHẬN POSTFIX trên hệ V2 — KHÔNG phải Phase 7B chính thức")
    print(f"selection_hash {sel['selection_hash'][:16]}…\n")
    print(f"REPETITIONS             {d['so_luot']}/12 · {d['so_bai']} ca")
    print(f"EXECUTABLE_IR           {d['executable_ir']}/12")
    print(f"CORRECT_EXECUTABLE_IR   {d['correct_executable_ir']}/12")
    print(f"SAFE_OUTCOMES           {d['safe']}/12")
    print(f"UNSAFE_ACCEPTED         {d['unsafe_accepted']}")
    print(f"served không chấm được  {d['served_khong_cham_duoc']}")
    print(f"STABLE_CASES            {d['so_on_dinh']}/{d['so_bai']}\n")
    print("── KẾT CỤC TỪNG CA (k=2, không trung bình hoá) ──")
    for c, x in d["theo_bai"].items():
        print(f"  {'  ' if len(set(x)) == 1 else '⚠️'} {c:<14} {x}")
    print("\n── NHÓM LỖI ──")
    for n, v in sorted(d["nhom_loi"].items(), key=lambda kv: -kv[1]) or [("(không)", 0)]:
        print(f"  {n:<18} {v}")
    t = d["token"]
    print(f"\nTOKEN in {t.get('prompt_tokens', 0)} · think "
          f"{t.get('thoughts_tokens', 0)} · out {t.get('candidates_tokens', 0)}"
          f" · tổng {t.get('total_tokens', 0)}")
    print(f"  /lượt {d['tokens_moi_luot']} · /correct IR {d['tokens_moi_correct_ir']}")
    for ten, v in sorted(d["token_theo_chang"].items(),
                         key=lambda kv: -kv[1]["total_tokens"]):
        print(f"  {ten:<20} tổng {v['total_tokens']:>7}")
    thieu = cong(d)
    print(f"\nCONFIRMATION_GATE: {'FAIL' if thieu else 'PASS'}")
    for x in thieu:
        print("  ⛔", x)
    (ra / "SCORE.json").write_text(json.dumps(
        {"khai": "XÁC NHẬN POSTFIX trên hệ V2 — KHÔNG phải Phase 7B chính thức",
         "selection_hash": sel["selection_hash"],
         "cong": "FAIL" if thieu else "PASS", "thieu": thieu,
         "nguong": NGUONG, **d}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
