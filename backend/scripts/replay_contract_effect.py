# -*- coding: utf-8 -*-
"""OFFLINE REPLAY — hợp đồng mới CAN NGĂN được bao nhiêu lượt hỏng cũ? 0 call.

─── ĐIỀU SCRIPT NÀY KHÔNG LÀM, VÀ ĐÓ LÀ ĐIỂM CHÍNH ────────────────────────

Nó **không** sửa chương trình cũ rồi tính là thành công. Một chương trình đã
chọn `angle_cos` trên `line3` vẫn sai sau khi hợp đồng đổi — hợp đồng chỉ đổi
việc mô hình có được DẪN tới lựa chọn ấy hay không, và điều đó chỉ đo được
bằng một lượt live mới.

Câu duy nhất trả lời được offline: với mỗi lượt hỏng đã lưu, hợp đồng mới có
**nói ra** điều mà lượt ấy vi phạm không?

    CAN_NGAN   — hợp đồng mới nói thẳng điều bị vi phạm, ngay chỗ mô hình
                 nhìn khi điền trường đó. Bệnh này *có thể* giảm.
    VAN_CHO    — hợp đồng mới im lặng y như cũ. Không có cơ sở kỳ vọng gì.
    KHONG_LIEN — lỗi không thuộc bề mặt prompt (lỗi lập kế hoạch của mô hình,
                 hoặc fail-closed đúng).

`CAN_NGAN` **không phải** dự báo tỉ lệ đúng. Nó là *"ta đã sửa chỗ này"*, không
phải *"mô hình sẽ làm đúng"*. Số duy nhất trả lời câu sau nằm ở §15.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from audit_synthesis_failures import KHUON, _luot  # noqa: E402

GEO = GOC / "docs" / "evaluation" / "geometry"

#: bệnh → (phán quyết, bằng chứng phải CÓ THẬT trong hợp đồng mới).
#:
#: Vế thứ hai là thứ giữ bảng này khỏi thành lời tự khen: mỗi `CAN_NGAN` phải
#: chỉ được ra một chuỗi kiểm được trong thẻ đang chạy. Chuỗi biến mất ⇒ ĐỎ ở
#: `test_replay_contract_effect`, không phải một dòng báo cáo lặng lẽ sai.
PHAN_QUYET: dict[str, tuple[str, tuple[str, ...]]] = {
    # Ký hiệu `tên<T>` từ 2026-09-01 (NAMED_GEOMETRY_OPERAND_ERGONOMICS §3) —
    # cùng mệnh đề, thẻ nay khai luôn KIỂU ô toán hạng nhận.
    "angle_cos_tren_line3": ("CAN_NGAN", ("angle_cos(of:tên<vector3",
                                          "không theo chữ trong đề")),
    "operand_sai_kieu": ("CAN_NGAN", ("distance(of:tên<point3",)),
    "thieu_toan_hang": ("CAN_NGAN", ("volume(of:tên<solid>) — không có wrt",)),
    "toa_do_cho_dan_xuat": ("CAN_NGAN", ("through:[tên<point3>",)),
    "construct_point_arith": ("CAN_NGAN", ("expr:phép dựng ĐIỂM",)),
    "construct_point_diem_goc": ("CAN_NGAN", ("declare_point",)),
    # Thẻ hình học nay KHÔNG liệt kê `enqueue`/`map_set`/`write_index`… nên
    # không gian chọn hẹp lại; nhưng enum sai còn tới từ chỗ khác, nên chỉ
    # khai phần kiểm được.
    "enum_sai": ("VAN_CHO", ()),
    "hinh_dang_wire": ("VAN_CHO", ()),
    "dung_truoc_khi_dung": ("KHONG_LIEN", ()),
    "rua_nang_luc": ("KHONG_LIEN", ()),
    "khai_bao_trung": ("KHONG_LIEN", ()),
    "ngoai_nang_luc": ("KHONG_LIEN", ()),
    "vuot_ngan_sach": ("KHONG_LIEN", ()),
    "khong_do_duoc": ("KHONG_LIEN", ()),
}


def _bam(msg: str) -> str | None:
    for khoa, _, mau, _, _ in KHUON:
        if re.search(mau, msg or "", re.IGNORECASE):
            return khoa
    return None


def thu_thap() -> dict:
    the = grammar_card("hinh_hoc")
    files = sorted(GEO.glob("dihedral-probe*/dihedral-probe.json")) + \
        [GEO / "generalization-matrix" / "matrix.json"]
    files = [f for f in files if f.exists()]

    ra: dict[str, dict] = {}
    thieu_bang_chung: list[str] = []
    for f in files:
        for _nguon, _cid, _idx, msg, _tok in _luot(f):
            khoa = _bam(msg)
            if khoa is None:
                continue
            pq, bang_chung = PHAN_QUYET.get(khoa, ("VAN_CHO", ()))
            if pq == "CAN_NGAN":
                mat = [b for b in bang_chung if b not in the]
                if mat:
                    pq = "VAN_CHO"
                    thieu_bang_chung.append(f"{khoa}: {mat}")
            ra.setdefault(khoa, {"phan_quyet": pq, "n": 0})["n"] += 1
    return {"benh": ra, "the_bytes": len(the.encode("utf-8")),
            "thieu_bang_chung": sorted(set(thieu_bang_chung))}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()
    d = thu_thap()

    tong = {k: 0 for k in ("CAN_NGAN", "VAN_CHO", "KHONG_LIEN")}
    print("━━ OFFLINE REPLAY — hợp đồng mới nói ra điều gì? ━━\n")
    for khoa, b in sorted(d["benh"].items(), key=lambda kv: -kv[1]["n"]):
        tong[b["phan_quyet"]] += b["n"]
        print(f"  {b['phan_quyet']:11s} {b['n']:3d}  {khoa}")
    print()
    for k, v in tong.items():
        print(f"{k:11s} {v:3d} lượt")
    if d["thieu_bang_chung"]:
        print("\n⚠️ HẠ CẤP vì thẻ KHÔNG chứa bằng chứng đã khai:")
        for x in d["thieu_bang_chung"]:
            print(f"  · {x}")
    print("\n⚠️ CAN_NGAN = 'ta đã sửa chỗ này', KHÔNG phải 'mô hình sẽ làm "
          "đúng'. Số sau chỉ đo được bằng lượt live mới (§15).")

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"khai": "Offline replay §11 — hợp đồng mới có NÓI RA điều mà mỗi "
                     "lượt hỏng cũ vi phạm không. KHÔNG sửa chương trình cũ "
                     "rồi tính thành công. 0 API call.",
             "tong": tong, **d}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print(f"\n→ {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
