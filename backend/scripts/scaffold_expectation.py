# -*- coding: utf-8 -*-
"""Dựng KHUNG `expectations/holdout.json` từ pool. **0 API call.**

    python scripts/scaffold_expectation.py            # in ra
    python scripts/scaffold_expectation.py --ghi      # ghi file

─── NÓ ĐIỀN GÌ, VÀ CỐ Ý KHÔNG ĐIỀN GÌ ────────────────────────────────────

Chia theo **một** đường: thứ **suy ra được** thì máy điền, thứ cần **phán
đoán** thì để trống cho người. Trộn hai loại là cách chắc chắn nhất để một
kỳ vọng do máy suy ra được đọc như một kỳ vọng đã có người phán.

    MÁY ĐIỀN            người kiểm rồi giữ
      case_id           chép từ pool — không gõ lại, không lệch
      slot              chép từ pool
      problem_text      chép từ pool — cùng một chuỗi ⇒ `kiem_noi_oracle`
                        không bao giờ báo "đề LỆCH giữa hai file"
      oracle_ref        trỏ vào `oracle_result` của chính bài ấy
      verification_obligations[].kind
                        suy từ `BANG_O[slot]` — ô đã định nghĩa nghĩa vụ

    NGƯỜI ĐIỀN          máy KHÔNG được đoán
      nguoi_danh_gia    ai phán, và `loai` PHẢI khác `nguoi_do`
      ly_do             vì sao đề đòi nghĩa vụ ấy
      trich_de          cụm chữ trong đề làm căn cứ
      construction_obligations
                        vật đề RA LỆNH DỰNG — đọc động từ của đề mới biết

─── VÌ SAO `construction_obligations` ĐỂ TRỐNG ───────────────────────────

`BANG_O` chỉ định nghĩa nghĩa vụ **KIỂM** cho mỗi ô. Nghĩa vụ **DỰNG** đọc từ
động từ của đề (*"hãy dựng"*, *"gọi M là"*, *"xác định giao tuyến"*) — không
suy ra được từ ô. Máy điền bừa vào đấy là tái lập đúng lỗi mà Phase 7A.2 đi
tách: một mệnh lệnh dựng bị xếp nhầm vào tập kiểm, rồi 8 lượt liên tiếp báo
*"mô hình sai"* ở chỗ mô hình đọc đề đúng.

Khung sinh ra **CHƯA nạp được**: `geometry_expectations.nap()` từ chối chỗ
trống `<…>`. Đó là tính năng — khung không phải tập kỳ vọng.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
GEO = GOC / "docs" / "evaluation" / "geometry"
POOL = GEO / "holdout" / "pool.json"
RA = GEO / "expectations" / "holdout.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_sc_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def dung_khung(pool_cases: list[dict], SH) -> dict:
    nhan = [c for c in pool_cases if c.get("status", "accepted") == "accepted"]
    cases = []
    for c in nhan:
        o = c.get("slot", "")
        nv = SH.BANG_O.get(o, (None,))[0]
        muc: dict = {
            "case_id": c["case_id"],
            "slot": o,
            "capability_tag": c.get("capability_tag"),
            "answer_shape": c.get("answer_shape"),
            # Chép TỪ POOL, không gõ lại: hai bản khác nhau một ký tự là
            # `kiem_noi_oracle` báo "đề LỆCH", và lúc ấy không biết bản nào đúng.
            "problem_text": c.get("problem_text"),
            "construction_obligations": [],
            "__can_nguoi_dien__": [
                "construction_obligations: vật đề RA LỆNH DỰNG. Đọc động từ "
                "của đề (\"hãy dựng\", \"gọi M là\", \"xác định giao tuyến\"). "
                "Đề chỉ TÍNH thì để `[]` và ghi `ghi_chu_dung` nói vì sao rỗng.",
                "ly_do + trich_de của từng nghĩa vụ kiểm bên dưới.",
            ],
            "verification_obligations": ([{
                "kind": nv,
                "trich_de": "<cụm chữ trong đề yêu cầu kiểm mệnh đề này>",
                "ly_do": "<vì sao đúng `kind` này: chủ thể kiểu gì, witness là vật nào>",
            }] if nv else []),
        }
        if o.startswith("A") and c.get("oracle_ref"):
            muc["oracle_ref"] = {
                "pool_case_id": c["case_id"],
                "khoa": c["oracle_ref"],
                "ghi_chu": "CON TRỎ, không chép giá trị. Đáp án ở pool.json.",
            }
        elif o.startswith("B"):
            muc["ghi_chu_kiem"] = (
                "<ô ngoài phủ: chấm bằng 'từ chối trung thực', không bằng đáp án>")
        cases.append(muc)

    return {
        "__khai__": [
            "KHUNG do `scaffold_expectation.py` sinh — CHƯA phải tập kỳ vọng.",
            "Mọi chỗ <...> là chỗ NGƯỜI phải điền; `nap()` từ chối chừng nào còn.",
            "Máy chỉ điền thứ SUY RA ĐƯỢC (case_id · slot · problem_text ·",
            "oracle_ref · kind theo BANG_O). Thứ cần PHÁN ĐOÁN để trống.",
        ],
        "dataset": "geometry_expectation_set",
        "tap": "holdout",
        "version": 1,
        "ngay": str(date.today()),
        "nguoi_danh_gia": {
            "loai": "<de_thi_cong_khai | sach_giao_khoa | sach_chuyen_de — "
                    "KHÔNG được là nguoi_do>",
            "ai": "<lời giải chính thức của nguồn — ghi tên tài liệu>",
            "cach_phan": "<Nghĩa vụ đọc từ ĐỘNG TỪ của đề: 'dựng/gọi/xác định' "
                         "⇒ nghĩa vụ DỰNG; 'chứng minh/chỉ ra/tính' ⇒ KIỂM.>",
            "khai_han_che": "<người soạn đã đọc mọi đề, nên bảo đảm thật là "
                            "'không viết ra đề và không sửa được đáp án'>",
        },
        "sinh_tu_model_output": False,
        "chua_chay_he": True,
        "cases": cases,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ghi", action="store_true", help="Ghi expectations/holdout.json")
    a = p.parse_args()

    SH = _nap("seal_geometry_holdout")
    cases = (json.loads(POOL.read_text(encoding="utf-8")).get("cases") or []
             if POOL.exists() else [])
    nhan = [c for c in cases if c.get("status", "accepted") == "accepted"]
    if not nhan:
        print("⛔ Pool chưa có bài `accepted` nào.")
        print("   Kỳ vọng chỉ soạn được SAU khi pool có bài — soạn trước là")
        print("   soạn kỳ vọng cho những bài chưa biết có nhận được không.")
        return 2

    khung = dung_khung(cases, SH)
    print(f"Dựng khung cho {len(nhan)} bài `accepted`:")
    for c in khung["cases"]:
        nv = [o["kind"] for o in c["verification_obligations"]]
        print(f"  {c['case_id']:<18} ô {c['slot']}  nghĩa vụ kiểm {nv or '—'}")
    if not a.ghi:
        print("\n(soi thôi — thêm `--ghi` để ghi file)")
        return 0
    if RA.exists():
        print(f"\n⛔ ĐÃ CÓ {RA} — không ghi đè.")
        print("   Ghi đè một tập kỳ vọng đã soạn là xoá phán quyết của người.")
        return 1
    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(json.dumps(khung, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8")
    print(f"\nĐã ghi {RA}")
    print("Việc của người: điền mọi chỗ <…>, rồi chạy")
    print("  python scripts/freeze_expectation_check.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
