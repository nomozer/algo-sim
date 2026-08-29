# -*- coding: utf-8 -*-
"""WAVE 1 sau Phase 7B — ĐO ỔN ĐỊNH TRÊN DEV. **TIÊU QUOTA THẬT.**

    ALLOW_LIVE_AI=1 python scripts/run_wave1_dev_stability.py --k 3

Ba đề DEV **mới**, viết cho đúng hai họ mà wave này vừa sửa, cộng năm đề
pilot đã đăng ký để thấy phép sửa không làm hỏng thứ đang chạy được.

─── ĐỀ Ở ĐÂY LÀ DEV, KHÔNG PHẢI HELD-OUT ─────────────────────────────────

Taxonomy của lượt chính thức chỉ **dẫn đường** (*"họ GÓC hỏng"*, *"grounding
6 lượt"*). Ba đề dưới đây do wave này viết ra: khác số, khác cách hỏi, khác
khối. Lấy chính 20 đề held-out làm ca sửa thì tập đo biến thành tập DEV
không hoàn tác được — `test_phase7b_baseline_immutable` khoá điều đó.

─── VÌ SAO ĐÚNG BA ĐỀ NÀY ────────────────────────────────────────────────

`w1-goc-dd`  góc đường–đường trên hình lập phương. Trước phép sửa, đề dạng
             này chết ở cổng phạm vi vì `hình lập phương` không nằm trong
             cụm MẠNH và đề quá ngắn để gom đủ ba cụm yếu.

`w1-goc-dm`  góc đường–MẶT, cùng khối. Tách khỏi đề trên có chủ đích: đơn vị
             checker là **sin²**, không phải cos², và một đề 45° sẽ không
             phân biệt được hai quy ước. Chọn góc mà hai quy ước cho hai số
             khác nhau.

`w1-phay`    vuông góc giữa hai đường mang KÝ HIỆU PHẨY (`A'C'`). Trước phép
             sửa, `geometry_symbol_key("A'")` trả `None` nên witness của hợp
             đồng không nối được biến nào của chương trình.

Đáp án tính tay, hữu tỉ, trong ranh giới kernel — xem từng `oracle`.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        ten, BACKEND / "scripts" / f"{ten}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


M = _nap("measure_geometry_stability")
PILOT = _nap("run_phase7a_pilot")

#: Hình lập phương cạnh 2, đặt `A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0)`, tầng
#: trên `z = 2`. Ba đáp án tính tay:
#:
#:   w1-goc-dd  AC = (2,2,0), B'C' = C'−B' = (0,2,0)
#:              cos² = |4|² / (8 · 4) = 16/32 = 1/2          (45°)
#:   w1-goc-dm  AC' = (2,2,2) với mặt (ABCD) pháp tuyến (0,0,1)
#:              sin² = |2|² / (12 · 1) = 4/12 = 1/3          (≠ 45° ⇒ phân
#:              biệt được sin² với cos² = 2/3)
#:   w1-phay    AC ⊥ B'D' : AC = (2,2,0), B'D' = D'−B' = (−2,2,0), tích vô
#:              hướng = −4+4 = 0 ⇒ true
BAI_W1 = [
    {
        "id": "w1-goc-dd",
        "de": ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính góc giữa hai "
               "đường thẳng AC và B'C'."),
        "oracle": "w1_cos_sq_1_2",
    },
    {
        "id": "w1-goc-dm",
        "de": ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính góc giữa "
               "đường thẳng AC' và mặt phẳng (ABCD)."),
        "oracle": "w1_sin_sq_1_3",
    },
    {
        "id": "w1-phay",
        "de": ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Chứng minh rằng "
               "AC vuông góc với B'D'."),
        "oracle": "w1_vuong_goc_true",
    },
]

_ORACLE_PILOT = PILOT.cham_oracle


def cham_oracle(ten: str, fm: dict, hd=None):
    if ten == "w1_cos_sq_1_2":
        return PILOT._tim_so(fm, Fraction(1, 2))
    if ten == "w1_sin_sq_1_3":
        return PILOT._tim_so(fm, Fraction(1, 3))
    if ten == "w1_vuong_goc_true":
        # Quan hệ: checker server-owned trả `None` khi thoả, nên ở đây chỉ hỏi
        # chương trình có khẳng định nó không — cùng quy ước `DEV.cham_oracle`.
        co = [v for v in fm.values() if v is True]
        return (bool(co), "có khẳng định true" if co else "không khẳng định")
    return _ORACLE_PILOT(ten, fm, hd)


#: TRẦN CỨNG của wave này. Mục tiêu KHÔNG phải benchmark rộng — nó là phép
#: chứng minh end-to-end sau khi sửa, nên trần đặt sát: canary 3×1 và bộ ổn
#: định nhỏ 4×3, cộng đệm.
TRAN_LOGIC_WAVE, TRAN_HTTP_WAVE = 90, 120

#: Bốn đề của BỘ ỔN ĐỊNH NHỎ. Ba canary cộng một đề nhiều bước đã đăng ký
#: (`3-pmn-giao-tuyen` — dựng thiết diện rồi suy vị trí một điểm, chuỗi phụ
#: thuộc dài nhất trong tập pilot).
TEN_MINI = ("w1-goc-dd", "w1-goc-dm", "w1-phay", "3-pmn-giao-tuyen")


def _bang_token(ket: list[dict]) -> dict:
    """Cộng token theo bốn trường, và theo BA mẫu số khác nhau.

    Một con số *tổng token* không trả lời được câu hỏi về hạn chế token. Ba
    mẫu số dưới đây trả lời ba câu khác nhau: mỗi LƯỢT tốn bao nhiêu · mỗi IR
    **chạy được** tốn bao nhiêu (lượt hỏng vẫn tiêu token) · mỗi IR **đúng**
    tốn bao nhiêu. Con số thứ ba mới là giá thật của một kết quả dùng được.
    """
    tong = {"prompt_tokens": 0, "candidates_tokens": 0,
            "thoughts_tokens": 0, "total_tokens": 0}
    for r in ket:
        for chang in (r.get("token") or {}).values():
            for k in tong:
                tong[k] += int(chang.get(k) or 0)
    chay_duoc = sum(1 for r in ket if r.get("servable"))
    dung = sum(1 for r in ket if r.get("oracle_dat") is True)
    tt = tong["total_tokens"]
    return {**tong, "so_luot": len(ket),
            "executable_ir": chay_duoc, "correct_ir": dung,
            "tokens_moi_luot": round(tt / len(ket)) if ket else 0,
            "tokens_moi_executable_ir": round(tt / chay_duoc) if chay_duoc else None,
            "tokens_moi_correct_ir": round(tt / dung) if dung else None}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--canary", action="store_true",
                   help="3 đề × 1 lượt. Chứng minh end-to-end trước, dừng sớm.")
    p.add_argument("--mini", action="store_true",
                   help="Bộ ổn định NHỎ 4 đề × k. Chỉ chạy SAU canary PASS.")
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--out-dir",
                   default="docs/evaluation/geometry/wave1-dev-stability")
    p.add_argument("--chi-moi", action="store_true",
                   help="Chỉ ba đề MỚI, bỏ năm đề pilot. Rẻ hơn.")
    a = p.parse_args()

    if a.canary:
        bai, a.k = BAI_W1, 1
    elif a.mini:
        moi = {b["id"]: b for b in list(PILOT.BAI_PILOT) + BAI_W1}
        bai = [moi[x] for x in TEN_MINI]
    else:
        bai = BAI_W1 if a.chi_moi else list(PILOT.BAI_PILOT) + BAI_W1
    d = Path(a.out_dir)
    M.RA = d if d.is_absolute() else ROOT / d
    M.RUN_ID = "wave1-dev-stability"
    M.TRAN_LOGIC, M.TRAN_HTTP = 6, 8
    M.BAI = bai
    M.cham_oracle = cham_oracle
    M.TAP_KY_VONG = "wave1"
    M._KY_VONG_CACHE.clear()

    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print(f"Thiếu ALLOW_LIVE_AI=1 — {len(bai)}×{a.k} lượt tiêu quota thật.")
        return 2
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Thiếu GEMINI_API_KEY.")
        return 2

    from app.runtime_identity import runtime_identity
    from app.ai import gemini
    r = runtime_identity()
    print(f"sha={r['git_sha'][:12]} cache={r['cache_version']} "
          f"model={gemini.MODEL}")
    print(f"{len(bai)} đề × {a.k} lượt · DEV, KHÔNG phải held-out\n")

    async def chay():
        out = []
        tl = th = 0
        for b in bai:
            for lan in range(1, a.k + 1):
                f = M.RA / f"{b['id']}-lan{lan}.json"
                if f.exists():
                    out.append(json.loads(f.read_text(encoding="utf-8"))["ban_ghi"])
                    continue
                if tl + 6 > TRAN_LOGIC_WAVE or th + 8 > TRAN_HTTP_WAVE:
                    print(f"⛔ CHẠM TRẦN WAVE: {tl}/{TRAN_LOGIC_WAVE} logic · "
                          f"{th}/{TRAN_HTTP_WAVE} HTTP — dừng TRƯỚC khi vượt.")
                    return out
                rr = await M.mot_luot(b, lan, key)
                out.append(rr)
                tl += rr.get("logical_calls") or 0
                th += rr.get("http_requests") or 0
                print(f"{'✅' if rr['servable'] else '❌'} {b['id']:<16} "
                      f"{lan}/{a.k} · {rr['do_tre_giay']:>5}s · "
                      f"{str(rr['stage_reached']):<20} oracle={rr['oracle_dat']} "
                      f"kiểm={rr['verification_match']} "
                      f"dựng={rr['construction_match']}", flush=True)
        return out

    ket = asyncio.run(chay())

    # DỪNG SỚM (§3): hỏng vì NHÀ CUNG CẤP thì không được đọc như hỏng vì hệ.
    # Phân biệt này là toàn bộ giá trị của trường `su_co` vừa thêm — trước đó
    # lời nhắn 429 bị rơi mất, và một lượt hết quota đọc y hệt một lượt hệ
    # ném lỗi.
    nha_cc = [r for r in ket
              if "429" in str(r.get("su_co") or "")
              or "RESOURCE_EXHAUSTED" in str(r.get("su_co") or "")]
    if nha_cc:
        print(f"\n⛔ PROVIDER_BLOCKED — {len(nha_cc)}/{len(ket)} lượt hỏng vì "
              "nhà cung cấp, không phải vì hệ:")
        print("   ", str(nha_cc[0].get("su_co"))[:160])
        print("   KHÔNG đọc lượt này như tín hiệu ngữ nghĩa.")

    print("\n── ỔN ĐỊNH DEV (x/k, không trung bình hoá) ──")
    for b in bai:
        x = [t for t in ket if t["case_id"] == b["id"]]
        print(f"  {b['id']:<16} served={sum(1 for t in x if t['servable'])}/{a.k}"
              f" oracle={sum(1 for t in x if t['oracle_dat'] is True)}/{a.k}"
              f" kiểm={sum(1 for t in x if t['verification_match'])}/{a.k}"
              f" dựng={sum(1 for t in x if t['construction_match'])}/{a.k}"
              f" nv={sorted({t['so_nghia_vu'] for t in x})}"
              f" stage={sorted({str(t['stage_reached']) for t in x})}")
    tok = _bang_token(ket)
    print("\n── TOKEN ──")
    for k2, v in tok.items():
        print(f"  {k2:<26} {v}")
    (M.RA / "tong_hop.json").write_text(
        json.dumps({"k": a.k, "token": tok, "runs": ket},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 2 if nha_cc else 0


if __name__ == "__main__":
    raise SystemExit(main())
