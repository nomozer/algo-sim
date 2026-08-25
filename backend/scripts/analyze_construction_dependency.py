# -*- coding: utf-8 -*-
"""PHASE 6.7.2 — AI DỰNG HÌNH hay KHAI KẾT QUẢ? **0 API call.**

    python scripts/analyze_construction_dependency.py docs/evaluation/geometry/stability-6.7

Đọc artifact của một lượt đo (`*-lan*.json`) và trả lời **một** câu hỏi:

    Chương trình AI sinh ra có thật sự DỰNG các vật từ nhau,
    hay chỉ KHAI SẴN chúng rồi gọi đó là mô phỏng?

Câu ấy khác hẳn *"có qua cổng không"*. Một chương trình khai sẵn mọi toạ độ vẫn
có thể qua mọi cổng và ra đúng đáp số — nó chỉ không còn là một **quá trình
dựng hình**, và khi ấy toàn bộ giá trị sư phạm của đề tài biến mất.

─── BA CHỈ SỐ, VÀ VÌ SAO PHẢI TÁCH BA ─────────────────────────────────────

**① `literal_hop_le`** — điểm gốc khai toạ độ kèm `model_assumption`.
KHÔNG phải lỗi: đề hình học không cho toạ độ, mô hình BUỘC phải tự đặt hệ trục.
Gộp nó vào "khai sẵn" là kết tội đúng thứ prompt bảo nó làm.

**② `literal_thay_the`** — thứ pha này đi tìm. Một vật **đáng lẽ phải được
dựng** mà lại khai sẵn:
  · witness của một nghĩa vụ khai bằng `initial_value`  → khai thẳng ĐÁP ÁN
  · `line3`/`plane3`/`solid`/`polygon3` khai `initial_value` → khai sẵn HÌNH

**③ `dung_phu_thuoc`** — vật sinh ra từ MỘT PHÉP DỰNG đọc tên vật khác.

Ba con số ấy cộng lại không bằng tổng: một điểm gốc không thuộc ② lẫn ③, và đó
là đúng — nó là **dữ kiện**, không phải kết quả.

─── ĐỘ SÂU CHUỖI ─────────────────────────────────────────────────────────

`do_sau_max` = chuỗi phụ thuộc dài nhất. Phase 5G đo được **2** trên toàn bộ IR
của lượt W4 và kết luận nguyên nhân là HỢP ĐỒNG (không có phép nâng đáy thành
khối). Con số ấy ở đây là phép đo lại sau khi có `construct_polygon`.

Dùng `dependency_graph` có sẵn — nó là API mỏng dựng riêng cho việc đọc đồ thị
mà không chạm cổng thẩm định.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

#: Kiểu mà một `initial_value` nghĩa là "khai sẵn hình", không phải "đề cho".
#: Điểm KHÔNG nằm đây: toạ độ điểm gốc là giả thiết mô hình hoá hợp lệ.
_HINH_PHAI_DUNG = frozenset({"line3", "plane3", "solid", "polygon3"})


def _do_sau(dep: dict[str, list[str]], ten: str, tham: frozenset = frozenset()) -> int:
    """Chuỗi phụ thuộc dài nhất tính từ `ten`. Vòng lặp ⇒ dừng, không treo."""
    if ten in tham:
        return 0
    con = dep.get(ten) or []
    if not con:
        return 0
    return 1 + max(_do_sau(dep, c, tham | {ten}) for c in con)


def phan_tich(spec_raw: dict, hd_raw: dict | None) -> dict:
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.simulation_state import dependency_graph

    spec = SemanticProgramSpec.model_validate(spec_raw)
    dep = dependency_graph(spec)
    khai = {d.name: d for d in spec.memory_declarations}
    dung = {st.target_var for st in spec.statements
            if getattr(st, "kind", "").startswith("construct")}
    gan_dan_xuat = {
        st.target_var for st in spec.statements
        if getattr(st, "kind", None) == "assign"
        and getattr(getattr(st, "expr", None), "kind", None) != "literal"
    }
    witness = {(o.get("params") or {}).get("witness")
               for o in ((hd_raw or {}).get("obligations") or [])}
    witness.discard(None)

    literal_hop_le, literal_thay_the, chi_tiet = [], [], []
    for ten, d in khai.items():
        if d.initial_value is None:
            continue
        if ten in witness:
            literal_thay_the.append(ten)
            chi_tiet.append(f"{ten}: WITNESS khai bằng initial_value — khai đáp án")
        elif d.type in _HINH_PHAI_DUNG:
            literal_thay_the.append(ten)
            chi_tiet.append(f"{ten} ({d.type}): HÌNH khai sẵn thay vì dựng")
        elif d.model_assumption:
            literal_hop_le.append(ten)
        else:
            # Có toạ độ, không khai giả thiết, không phải witness. Không kết
            # tội — grounding mới là chỗ phán, và nó phán bằng `source_fact_id`.
            literal_hop_le.append(ten)

    phai_dung = [t for t in khai if t not in literal_hop_le]
    dan_xuat = sorted((dung | gan_dan_xuat) & set(khai))
    do_sau = max((_do_sau(dep, t) for t in dep), default=0)

    return {
        "so_khai": len(khai),
        "literal_hop_le": sorted(literal_hop_le),
        "literal_thay_the": sorted(literal_thay_the),
        "chi_tiet_thay_the": chi_tiet,
        "dung_phu_thuoc": dan_xuat,
        "so_phai_dung": len(phai_dung),
        "do_sau_max": do_sau,
        # Tỉ lệ tính trên PHẦN ĐÁNG LẼ PHẢI DỰNG, không trên tổng khai báo:
        # chia cho tổng thì một chương trình khai nhiều điểm gốc sẽ tự động
        # "tệ" đi, mà điểm gốc là dữ kiện chứ không phải kết quả.
        "ti_le_literal_thay_the": (round(len(literal_thay_the) / len(phai_dung), 3)
                                   if phai_dung else None),
        "ti_le_dung_phu_thuoc": (round(len(dan_xuat) / len(phai_dung), 3)
                                 if phai_dung else None),
        "witness": sorted(witness),
        "witness_dan_xuat": sorted(w for w in witness if w in (dung | gan_dan_xuat)),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("thu_muc")
    a = p.parse_args()
    goc = Path(a.thu_muc)
    if not goc.is_absolute():
        goc = BACKEND.parent / goc

    tat_ca = []
    for f in sorted(goc.glob("*-lan*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("generated_program"):
            print(f"  {f.stem:<26} KHÔNG có chương trình (chết trước khi sinh)")
            tat_ca.append({"ten": f.stem, "chuong_trinh": None,
                           "ban_ghi": d["ban_ghi"]})
            continue
        pt = phan_tich(d["generated_program"], d.get("request_contract"))
        tat_ca.append({"ten": f.stem, **pt, "ban_ghi": d["ban_ghi"]})
        print(f"  {f.stem:<26} khai={pt['so_khai']:>2} "
              f"phải-dựng={pt['so_phai_dung']:>2} "
              f"literal-thay-thế={len(pt['literal_thay_the'])} "
              f"dựng={len(pt['dung_phu_thuoc']):>2} "
              f"sâu={pt['do_sau_max']} "
              f"witness-dẫn-xuất={len(pt['witness_dan_xuat'])}/{len(pt['witness'])}")
        for c in pt["chi_tiet_thay_the"]:
            print(f"      ⚠ {c}")

    co = [x for x in tat_ca if x.get("chuong_trinh") is not False
          and "so_khai" in x]
    print("\n── TỔNG ──")
    print(f"  chương trình đọc được: {len(co)}/{len(tat_ca)}")
    if co:
        n_tt = sum(1 for x in co if x["literal_thay_the"])
        print(f"  có literal thay thế:   {n_tt}/{len(co)}")
        tong_pd = sum(x["so_phai_dung"] for x in co)
        tong_tt = sum(len(x["literal_thay_the"]) for x in co)
        tong_dx = sum(len(x["dung_phu_thuoc"]) for x in co)
        print(f"  tỉ lệ literal thay thế: {tong_tt}/{tong_pd} = "
              f"{tong_tt / tong_pd:.1%}" if tong_pd else "")
        print(f"  tỉ lệ dựng phụ thuộc:   {tong_dx}/{tong_pd} = "
              f"{tong_dx / tong_pd:.1%}" if tong_pd else "")
        print(f"  độ sâu chuỗi: {sorted({x['do_sau_max'] for x in co})}")
        w_t = sum(len(x["witness"]) for x in co)
        w_d = sum(len(x["witness_dan_xuat"]) for x in co)
        print(f"  witness DẪN XUẤT: {w_d}/{w_t}" if w_t else
              "  witness: KHÔNG hợp đồng nào khai")
    (goc / "phan_tich_phu_thuoc.json").write_text(
        json.dumps(tat_ca, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
