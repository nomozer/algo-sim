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
    """Bảy tầng của chỉ thị. Thứ tự CÓ nghĩa: cái nào chắc chắn hơn hỏi trước.

    ─── VÌ SAO TÁCH `VALIDATOR` VÀ `TOOLING` RA (2026-08-29, TRƯỚC khi chấm) ─

    Bản trước gộp cả hai vào `MODEL_SYNTHESIS`/`DETERMINISTIC`, nên hai câu hỏi
    khác hẳn nhau đọc ra cùng một con số: *"mô hình viết sai chương trình"* và
    *"khung đo tự ném lỗi"*. Cái thứ hai là lỗi CỦA TA, và cổng đòi nó bằng 0 —
    gộp vào là tự miễn cho mình.

    Tách trước khi chạy `cham()` lần đầu, không phải sau khi thấy số: ngưỡng ở
    `NGUONG` không đổi một chữ, chỉ nhãn mịn hơn.
    """
    if r.get("servable"):
        return None
    st, ec = str(r.get("stage_reached")), str(r.get("error_code") or "")
    su = str(r.get("su_co") or "")
    if "429" in su or "RESOURCE_EXHAUSTED" in su or r.get("budget_aborted"):
        return "PROVIDER"
    # `su_co` còn sót sau khi đã loại nhà cung cấp = khung đo ném ngoại lệ.
    # Đó là TOOLING: không có kết luận ngữ nghĩa nào rút ra được từ nó.
    if su:
        return "TOOLING"
    if r.get("envelope_status") == "EXCEPTION":
        return "DETERMINISTIC"
    if st == "scope":
        return "SCOPE"
    if st == "grounding":
        return "GROUNDING"
    # ── CHẶNG THẮNG MÃ LỖI ──────────────────────────────────────────────────
    #
    # Bản đầu hỏi `"INVALID" in error_code` TRƯỚC khi hỏi chặng, và nó sai ở
    # V3: bốn lượt chết ở `execution` vì `GEOMETRY_OPERAND_TYPE` đều mang
    # `error_code = semantic_program_invalid` — route dùng lại mã ấy cho cả
    # lỗi hình thức lẫn lỗi toán hạng lúc chạy. Kết quả là bốn lỗi SINH bị
    # dán nhãn VALIDATOR, và bảng nhóm lỗi chỉ sai chỗ quan trọng nhất: chỗ
    # nói cho ta biết nút thắt nằm ở đâu.
    #
    # VALIDATOR chỉ còn đúng một nghĩa: IR KHÔNG QUA nổi thẩm định hình thức,
    # tức chết ngay ở chặng `semantic_program`.
    if st == "semantic_program":
        return "VALIDATOR"
    if st in ("structural_coverage", "realized_coverage", "postconditions",
              "learner_surface", "execution"):
        return "MODEL_SYNTHESIS"
    if "SCHEMA" in ec.upper() or "INVALID" in ec.upper():
        return "VALIDATOR"
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
            "tokens_moi_executable_ir": round(T / len(ex)) if ex else None,
            "tokens_moi_correct_ir": round(T / len(correct)) if correct else None,
            "duong_di": [_duong_di(r) for r in rs]}


#: Tám chặng của một lượt, theo đúng thứ tự chỉ thị đòi ghi. `stage_reached` là
#: chặng CUỐI đã tới, nên mọi chặng trước nó là ĐÃ QUA — trừ chặng chết.
_CHANG = ("scope", "semantic_program", "validator", "grounding",
          "execution", "oracle", "verification")
#: `stage_reached` → chặng nào trong `_CHANG` đã chết. Chặng không có tên riêng
#: trong route thì quy về chặng gần nhất mà nó thuộc về.
_QUY_VE = {"scope": "scope", "execution_authority": "scope",
           "semantic_analyze": "semantic_program",
           "semantic_program": "validator",
           "grounding": "grounding", "execution": "execution",
           "structural_coverage": "verification",
           "realized_coverage": "verification",
           "postconditions": "verification", "learner_surface": "verification"}


def _duong_di(r: dict) -> dict:
    """Một lượt = một hàng: chặng nào QUA, chặng nào CHẾT, kết cục là gì."""
    st = str(r.get("stage_reached"))
    chet = None if r.get("servable") else _QUY_VE.get(st, st)
    qua: dict[str, str] = {}
    for c in _CHANG:
        if chet is None:
            qua[c] = "qua"
        elif c == chet:
            qua[c] = "CHẾT"
        elif chet in _CHANG and _CHANG.index(c) < _CHANG.index(chet):
            qua[c] = "qua"
        else:
            qua[c] = "—"
    if qua.get("oracle") == "qua":
        qua["oracle"] = {True: "qua", False: "SAI", None: "không chấm được"}[
            r.get("oracle_dat")]
    return {"case_id": r["case_id"], "lan": r.get("lan"), **qua,
            "ket_cuc": _ket_cuc(r), "tang_loi": _tang_loi(r)}


def cong(d: dict) -> list[str]:
    """Chín điều kiện của `§12`. Trả danh sách điều KHÔNG đạt."""
    loi = []
    if d["so_luot"] != NGUONG["repetitions"]:
        loi.append(f"repetitions {d['so_luot']}/{NGUONG['repetitions']}")
    # `TOOLING` vào cùng ô với `PROVIDER`: chỉ thị đòi *"provider/tooling
    # failures = 0"*. Cả hai đều là lượt KHÔNG nói gì về ngữ nghĩa, nên một
    # lượt như thế lọt vào là tập 12 lượt đã mất một điểm quan sát.
    for n in ("PROVIDER", "TOOLING"):
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
    # `ra`, KHÔNG phải `RA`: với `--in-dir` trỏ sang V2/V3 mà đọc con dấu của
    # V1 thì bộ chấm so kết quả vòng này với tập ca của vòng khác — và nó sẽ
    # im lặng, vì cả hai đều tồn tại và đều đọc đúng khuôn.
    sel = json.loads((ra / "CONFIRMATION_SELECTION.json").read_text(encoding="utf-8"))
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
    print("\n── ĐƯỜNG ĐI TỪNG LƯỢT (scope → synth → IR → ground → exec → "
          "oracle → verify) ──")
    _K = {"qua": "✓", "CHẾT": "✗", "—": " ", "SAI": "S",
          "không chấm được": "?"}
    for x in d["duong_di"]:
        o = "".join(_K.get(x[c], "?") for c in _CHANG)
        print(f"  {x['case_id']:<14} lần{x['lan']} [{o}] {x['ket_cuc']:<16}"
              f"{x['tang_loi'] or ''}")
    print("\n── NHÓM LỖI ──")
    for n, v in sorted(d["nhom_loi"].items(), key=lambda kv: -kv[1]) or [("(không)", 0)]:
        print(f"  {n:<18} {v}")
    t = d["token"]
    print(f"\nTOKEN in {t.get('prompt_tokens', 0)} · think "
          f"{t.get('thoughts_tokens', 0)} · out {t.get('candidates_tokens', 0)}"
          f" · tổng {t.get('total_tokens', 0)}")
    print(f"  /lượt {d['tokens_moi_luot']} · /executable IR "
          f"{d['tokens_moi_executable_ir']} · /correct IR "
          f"{d['tokens_moi_correct_ir']}")
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
