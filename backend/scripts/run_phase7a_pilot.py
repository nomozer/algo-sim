# -*- coding: utf-8 -*-
"""PHASE 7A — PILOT BENCHMARK. **TIÊU QUOTA THẬT.**

    ALLOW_LIVE_AI=1 python scripts/run_phase7a_pilot.py --k 3

**MỤC TIÊU DUY NHẤT: kiểm BỘ ĐO, không đánh giá mô hình.** Năm đề × `k` lượt là
mẫu quá nhỏ để nói bất cứ điều gì về chất lượng AI; nó đủ để trả lời một câu
khác: *năm chỉ số của `PHASE7_METRIC_CONTRACT.md` có phân biệt được các trường
hợp không, và taxonomy bốn nhóm có phủ hết lỗi không?*

─── DÙNG LẠI MÁY ĐO, KHÔNG VIẾT BẢN THỨ HAI ──────────────────────────────

`measure_geometry_stability` đã có toàn bộ phần khó: bọc hai stage để bắt
`RequestContract` + `SemanticProgramSpec`, ngân sách theo call graph, ghi
artifact từng lượt, cổng chống ghi đè. Viết lại là đẻ ra một nguồn sự thật thứ
hai, và hai nguồn sẽ trôi khỏi nhau đúng lúc cần so hai lượt đo.

Nên file này chỉ **thay dữ liệu và thêm hai oracle**.

─── HAI ĐỀ MỚI, VÀ VÌ SAO CHỌN ĐÚNG HAI SỐ ẤY ────────────────────────────

**khoảng cách** — `d(A, SB)` với đáy cạnh 3, `SA = 4`:

    A(0,0,0) B(3,0,0) S(0,0,4);  SB dài 5
    |AS × AB| / |SB| = 12/5

Chọn `d(A, SB)` chứ **không** chọn `d(B, (SAD))`: cái sau luôn bằng đúng cạnh
đáy, nên một oracle quét "có biến nào bằng 3 không" sẽ khớp nhầm chính độ dài
cạnh. `12/5` không trùng bất kỳ dữ kiện nào của đề.

**góc** — `∠(SB, SD)` với đáy cạnh 2, `SA = 2`:

    SB = (2,0,-2)  SD = (0,2,-2);  SB·SD = 4;  |SB|² = |SD|² = 8
    cos² = 16/64 = 1/4          (góc 60°)

Chọn **đường–đường** có chủ đích: `geometry_exec._do` trả `cos_sq_between_lines`
cho cặp đường nhưng `sin_sq_line_plane` cho cặp đường–mặt. Một đề đường–mặt ở
45° sẽ cho `sin² = cos² = 1/2` và oracle **không phân biệt được hai quy ước** —
nó sẽ xanh kể cả khi engine dùng nhầm công thức.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import os
import sys
from fractions import Fraction
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        ten, Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _nap("measure_geometry_stability")

#: Ba đề đầu GIỮ NGUYÊN từ `stability-6.7` — cùng chữ, cùng oracle. Đổi một chữ
#: là mất khả năng so pilot với hai vòng đo trước.
#:
#: Kỳ vọng nghĩa vụ của **cả năm** đề nằm ở `expectations/pilot.json` từ Phase
#: 7A.2, không còn ở đây (`geometry_expectations.py` giải thích vì sao).
BAI_PILOT = list(M.BAI) + [
    {
        "id": "4-khoang-cach",
        "de": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3, SA "
               "vuông góc với mặt phẳng đáy và SA = 4. Tính khoảng cách từ "
               "điểm A đến đường thẳng SB."),
        "oracle": "khoang_cach_12_5",
    },
    {
        "id": "5-goc",
        "de": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA "
               "vuông góc với mặt phẳng đáy và SA = 2. Tính góc giữa hai đường "
               "thẳng SB và SD."),
        "oracle": "goc_cos_sq_1_4",
    },
]

_GOC_ORACLE = M.cham_oracle


def _tim_so(fm: dict, mong: Fraction) -> tuple[bool, str]:
    """Có biến nào mang đúng đại lượng này không?

    Quét GIÁ TRỊ chứ không tra tên: mô hình tự đặt tên biến, và đoán tên là đúng
    thứ đã đẻ ra cả một lưới hoà giải ở Phase 6.6.
    """
    so = {}
    for k, v in (fm or {}).items():
        if isinstance(v, bool):
            continue
        if isinstance(v, (Fraction, int, str)):
            try:
                so[k] = str(v)
                if Fraction(v) == mong:
                    return True, f"{k} = {mong}"
            except (ValueError, ZeroDivisionError):
                so.pop(k, None)
    return False, f"không biến nào bằng {mong} · số đã đo: {so}"


def cham_oracle(ten: str, fm: dict, hd=None):
    """Ba trạng thái, đúng hợp đồng chỉ số: True · False · **None**.

    `None` = KHÔNG CHẤM ĐƯỢC, khác hẳn `False`. Gộp chúng là ghi một lượt không
    đo được thành một lượt sai.
    """
    if not fm:
        return None, "không có final_memory"
    if ten == "khoang_cach_12_5":
        return _tim_so(fm, Fraction(12, 5))
    if ten == "goc_cos_sq_1_4":
        return _tim_so(fm, Fraction(1, 4))
    return _GOC_ORACLE(ten, fm)


async def _chay(k: int) -> int:
    from app.ai import gemini
    from app.runtime_identity import runtime_identity

    r = runtime_identity()
    print(f"cache={r['cache_version']} model={gemini.MODEL} "
          f"skill={r['skills']['tong'][:8]} card={r['skills']['grammar_card'][:8]}")
    print(f"{len(BAI_PILOT)} đề × {k} lượt · PILOT — kiểm BỘ ĐO, "
          f"KHÔNG kết luận chất lượng mô hình\n")

    tat_ca = []
    for bai in BAI_PILOT:
        for lan in range(1, k + 1):
            rr = await M.mot_luot(bai, lan, os.environ["GEMINI_API_KEY"])
            tat_ca.append(rr)
            print(f"{'✅' if rr['servable'] else '❌'} {bai['id']:<18} "
                  f"{lan}/{k} · {rr['do_tre_giay']:>5}s · "
                  f"{str(rr['stage_reached']):<21} nv={rr['so_nghia_vu']} "
                  f"kiểm={rr['verification_match']} dựng={rr['construction_match']} "
                  f"oracle={rr['oracle_dat']} canh={rr['so_doi_tuong_canh']}")
        print()

    import json

    (M.RA / "tong_hop.json").write_text(
        json.dumps({"k": k, "runs": tat_ca}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("── TỔNG HỢP (served · oracle · verification · construction) ──")
    for bai in BAI_PILOT:
        x = [t for t in tat_ca if t["case_id"] == bai["id"]]
        print(f"  {bai['id']:<18} {sum(1 for t in x if t['servable'])}/{k} · "
              f"{sum(1 for t in x if t['oracle_dat'] is True)}/{k} · "
              f"{M._dong_nghia_vu(x, k)}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--out-dir", default="docs/evaluation/geometry/phase7a-pilot")
    a = p.parse_args()

    d = Path(a.out_dir)
    M.RA = d if d.is_absolute() else ROOT / d
    M.BAI = BAI_PILOT
    M.cham_oracle = cham_oracle          # `mot_luot` tra ở cấp module
    if list(M.RA.glob("*-lan*.json")):
        print(f"THƯ MỤC ĐÃ CÓ BẢN GHI: {M.RA} — dùng --out-dir mới.")
        return 1
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print(f"Thiếu ALLOW_LIVE_AI=1 — {len(BAI_PILOT)}×{a.k} lượt tiêu quota thật.")
        return 2
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    if not os.environ.get("GEMINI_API_KEY"):
        print("Thiếu GEMINI_API_KEY")
        return 2
    return asyncio.run(_chay(a.k))


if __name__ == "__main__":
    raise SystemExit(main())
