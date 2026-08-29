# -*- coding: utf-8 -*-
"""Chấm lượt MINI theo cổng đã đăng ký TRƯỚC. **0 API call.**

    python scripts/score_mini_stability.py --in-dir docs/.../wave2-mini

─── HAI TRỤC KHÁC NHAU, KHÔNG GỘP ────────────────────────────────────────

**AN TOÀN** hỏi: hệ có bao giờ nhận một diễn giải SAI như hợp lệ rồi cho đi
tiếp không? Fail-closed tính là AN TOÀN — một bài bị chặn vì hệ tự thấy chưa
đủ điều kiện thì không hại ai.

**ĐÚNG** hỏi: hệ có ra được một chương trình chạy được và đúng không.
Fail-closed **không** tính là đúng.

Gộp hai trục là chỗ hỏng kinh điển của một benchmark mô phỏng: một hệ từ chối
mọi thứ sẽ "an toàn 100%" và vô dụng, còn một hệ nhận mọi thứ sẽ "phục vụ
100%" và nguy hiểm. Chỉ đọc cùng lúc hai con số mới nói được gì.

─── UNSAFE ĐỊNH NGHĨA HẸP, CÓ CHỦ ĐÍCH ───────────────────────────────────

`UNSAFE` = **served** (hệ nhận và cho đi tiếp tới mô phỏng) **và** oracle nói
SAI. Đó đúng là ca "biến lỗi ngữ nghĩa thành một hình 3D trông hợp lệ".

`oracle = None` trên một lượt `served` KHÔNG phải unsafe — nó là *không chấm
được*, và ghi nó thành unsafe là kết tội hệ bằng một khuyết tật của bộ đo.
Nhưng nó cũng không được biến mất: nó có ô riêng, `served_khong_cham_duoc`.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "docs" / "evaluation" / "geometry"


def _tang_loi(r: dict) -> str | None:
    """FIRST_FAILING_STAGE → nhóm. `None` khi lượt không hỏng."""
    if r.get("servable"):
        return None
    st = str(r.get("stage_reached"))
    ec = str(r.get("error_code") or "")
    su = str(r.get("su_co") or "")
    if "429" in su or "RESOURCE_EXHAUSTED" in su:
        return "PROVIDER"
    if r.get("budget_aborted"):
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
        # Chạy được rồi mới bị chặn ⇒ chương trình mô hình sinh chưa đủ, trừ
        # khi chính cổng sai — và cái đó phải CHỨNG MINH được, không mặc định.
        return "MODEL_SYNTHESIS"
    return "DETERMINISTIC"


def _ket_cuc(r: dict) -> str:
    """Bốn kết cục của §5, loại trừ nhau."""
    if _tang_loi(r) in ("PROVIDER", "TOOLING"):
        return "ha_tang"
    if r.get("servable"):
        return "dung" if r.get("oracle_dat") is True else (
            "SAI_MA_VAN_NHAN" if r.get("oracle_dat") is False
            else "served_khong_cham_duoc")
    return "fail_closed"


def cham(rs: list[dict], k: int) -> dict:
    ids = sorted({r["case_id"] for r in rs})
    theo = {c: [r for r in rs if r["case_id"] == c] for c in ids}

    executable = [r for r in rs if r.get("executable") is True]
    correct = [r for r in executable if r.get("oracle_dat") is True]
    unsafe = [r for r in rs if _ket_cuc(r) == "SAI_MA_VAN_NHAN"]
    safe = [r for r in rs if _ket_cuc(r) in ("dung", "fail_closed")]
    khong_cham = [r for r in rs if _ket_cuc(r) == "served_khong_cham_duoc"]

    on_dinh = [c for c, x in theo.items()
               if len(x) == k and len({_ket_cuc(r) for r in x}) == 1]
    nhom = Counter(t for r in rs if (t := _tang_loi(r)))

    tok = {"prompt_tokens": 0, "candidates_tokens": 0,
           "thoughts_tokens": 0, "total_tokens": 0}
    theo_chang: dict[str, Counter] = {}
    for r in rs:
        for chang, v in (r.get("token") or {}).items():
            c = theo_chang.setdefault(chang, Counter())
            for kk in tok:
                tok[kk] += int(v.get(kk) or 0)
                c[kk] += int(v.get(kk) or 0)
    T = tok["total_tokens"]
    return {
        "so_luot": len(rs), "k": k, "so_bai": len(ids),
        "executable_ir": len(executable), "correct_executable_ir": len(correct),
        "safe": len(safe), "unsafe_accepted": len(unsafe),
        "served_khong_cham_duoc": len(khong_cham),
        "on_dinh": on_dinh, "so_on_dinh": len(on_dinh),
        "theo_bai": {c: [_ket_cuc(r) for r in x] for c, x in theo.items()},
        "nhom_loi": dict(nhom),
        "token": tok,
        "token_theo_chang": {k2: dict(v) for k2, v in theo_chang.items()},
        "tokens_moi_luot": round(T / len(rs)) if rs else 0,
        "tokens_moi_executable_ir": round(T / len(executable)) if executable else None,
        "tokens_moi_correct_ir": round(T / len(correct)) if correct else None,
    }


#: CỔNG ĐÃ ĐĂNG KÝ TRƯỚC. Không đổi ngưỡng sau khi thấy số.
NGUONG = {
    "repetitions": 12, "executable_ir": 10, "correct_executable_ir": 9,
    "on_dinh": 3,
}


def cong(d: dict) -> list[str]:
    loi = []
    if d["so_luot"] != NGUONG["repetitions"]:
        loi.append(f"repetitions {d['so_luot']}/{NGUONG['repetitions']}")
    for nhom in ("PROVIDER", "TOOLING"):
        if d["nhom_loi"].get(nhom):
            loi.append(f"{nhom} failure = {d['nhom_loi'][nhom]}, phải 0")
    if d["executable_ir"] < NGUONG["executable_ir"]:
        loi.append(f"executable IR {d['executable_ir']}/12 < {NGUONG['executable_ir']}")
    if d["correct_executable_ir"] < NGUONG["correct_executable_ir"]:
        loi.append(f"correct executable IR {d['correct_executable_ir']}/12 "
                   f"< {NGUONG['correct_executable_ir']}")
    if d["so_on_dinh"] < NGUONG["on_dinh"]:
        loi.append(f"stable cases {d['so_on_dinh']}/{d['so_bai']} < {NGUONG['on_dinh']}")
    # "Hệ thống" = xảy ra ở MỌI lượt của MỌI bài — một lượt lẻ là dao động.
    for nhom in ("SCOPE", "GROUNDING"):
        n = d["nhom_loi"].get(nhom, 0)
        if n >= d["k"]:
            loi.append(f"{nhom} failure có HỆ THỐNG: {n} lượt")
    if d["unsafe_accepted"]:
        loi.append(f"unsafe accepted = {d['unsafe_accepted']}, phải 0")
    return loi


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in-dir", default="docs/evaluation/geometry/wave2-mini")
    p.add_argument("--k", type=int, default=3)
    a = p.parse_args()
    d = Path(a.in_dir)
    ra = d if d.is_absolute() else ROOT / d
    rs = [json.loads(f.read_text(encoding="utf-8"))["ban_ghi"]
          for f in sorted(ra.glob("*-lan*.json"))]
    if not rs:
        print(f"Chưa có bản ghi ở {ra}")
        return 1

    r = cham(rs, a.k)
    print(f"REPETITIONS            {r['so_luot']}/12 · {r['so_bai']} bài")
    print(f"EXECUTABLE_IR          {r['executable_ir']}/12")
    print(f"CORRECT_EXECUTABLE_IR  {r['correct_executable_ir']}/12")
    print(f"SAFE_OUTCOMES          {r['safe']}/12")
    print(f"UNSAFE_ACCEPTED        {r['unsafe_accepted']}")
    print(f"served không chấm được {r['served_khong_cham_duoc']}")
    print(f"STABLE_CASES           {r['so_on_dinh']}/{r['so_bai']} · {r['on_dinh']}")
    print()
    print("── KẾT CỤC TỪNG BÀI (3 lượt, không trung bình hoá) ──")
    for c, x in r["theo_bai"].items():
        print(f"  {'  ' if len(set(x)) == 1 else '⚠️'} {c:<18} {x}")
    print()
    print("── NHÓM LỖI ──")
    for n, v in sorted(r["nhom_loi"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:<18} {v}")
    t = r["token"]
    print()
    print(f"TOKEN in {t['prompt_tokens']} · think {t['thoughts_tokens']} · "
          f"out {t['candidates_tokens']} · tổng {t['total_tokens']}")
    print(f"  /lượt {r['tokens_moi_luot']} · /executable IR "
          f"{r['tokens_moi_executable_ir']} · /correct IR {r['tokens_moi_correct_ir']}")
    for chang, v in sorted(r["token_theo_chang"].items(),
                           key=lambda kv: -kv[1]["total_tokens"]):
        print(f"  {chang:<20} in {v['prompt_tokens']:>7} · think "
              f"{v['thoughts_tokens']:>6} · out {v['candidates_tokens']:>5} · "
              f"tổng {v['total_tokens']:>7}")
    thieu = cong(r)
    print()
    print(f"MINI_GATE: {'FAIL' if thieu else 'PASS'}")
    for x in thieu:
        print("  ⛔", x)
    (ra / "SCORE.json").write_text(
        json.dumps({"cong": "FAIL" if thieu else "PASS", "thieu": thieu,
                    "nguong": NGUONG, **r}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
