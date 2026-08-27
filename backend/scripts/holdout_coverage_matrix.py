# -*- coding: utf-8 -*-
"""PHASE 7B-prep — MA TRẬN ĐỘ PHỦ của pool held-out. **0 API call.**

    python scripts/holdout_coverage_matrix.py            # in ra
    python scripts/holdout_coverage_matrix.py --md <f>   # ghi báo cáo

Trả lời **một** câu: *pool còn thiếu ô nào?* Không thêm bài, không chọn bài,
không chấm gì.

─── HAI TRỤC, VÀ VÌ SAO PHẢI HAI ──────────────────────────────────────────

`BANG_O` (20 ô) là trục **thiết kế tập đo**: mỗi ô một loại bài, seed chỉ chọn
*bài nào trong ô* chứ không chọn *ô nào có mặt*. Nó đã có và không đổi.

`geometry_family` (7 họ, đặt ở Phase 7B) là trục **nội dung**: bài nói về cái
gì. Hai trục **trực giao** — một họ trải trên nhiều ô, và biết "thiếu ô A07"
khác với biết "cả họ `line_relation` mới có 2 bài".

Trục thứ ba, nhỏ nhưng là thứ đọc nhanh nhất: `answer_shape` — đề đòi **dựng
một vật**, **phán đúng/sai**, hay **ra một số**. Ba hình dạng ấy chấm bằng ba
kiểu oracle khác nhau, nên lệch phân bố ở đây làm lệch cả ý nghĩa của ②.

─── PHÁT HIỆN ĐÃ BIẾT TRƯỚC KHI CÓ BÀI NÀO ────────────────────────────────

Họ `proof_verification` ánh xạ vào **0 ô riêng**. Không phải sót: trong `BANG_O`
việc *chứng minh* không có ô của riêng nó mà nằm lồng trong sáu ô quan hệ
(A03–A08) — đề dạng *"chứng minh AB ⊥ (SCD)"* rơi vào A06/A07/A08. Ghi ra đây
thay vì ép một ánh xạ cho đủ bảy họ, vì ép thì bảng trông đầy trong khi tập đo
không đổi một chút nào.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
GEO = GOC / "docs" / "evaluation" / "geometry"
POOL = GEO / "holdout" / "pool.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

#: Bảy họ nội dung (Phase 7B) → mô tả. Thứ tự có nghĩa: từ dựng vật đơn giản
#: tới đại lượng, đúng thứ tự chương trình Toán 11 dạy.
HO: dict[str, str] = {
    "point_construction": "dựng điểm · điểm thuộc vật",
    "line_relation": "quan hệ đường–đường, đường–mặt",
    "plane_construction": "dựng mặt · quan hệ mặt–mặt · thiết diện",
    "intersection": "giao tuyến · giao điểm",
    "solid_geometry": "khối đa diện",
    "measurement": "khoảng cách · góc · thể tích",
    "proof_verification": "chứng minh thuần, tách khỏi một quan hệ cụ thể",
}

#: `slot → (họ, hình dạng đáp án)`. Ánh xạ này là **phán đoán thiết kế**, không
#: phải sự thật toán học — nên nó nằm ở đây, đọc được, sửa được, chứ không nằm
#: rải trong đầu người soạn pool.
#:
#: `answer_shape` lấy theo thứ đề ĐÒI CUỐI CÙNG. A01 dựng giao tuyến rồi mới
#: phán điểm thuộc nó ⇒ `construction`; A13 dựng thiết diện nhưng câu hỏi là
#: bốn điểm có đồng phẳng không ⇒ `verdict`.
O_HO: dict[str, tuple[str, str]] = {
    "A01": ("intersection", "construction"),
    "A02": ("point_construction", "verdict"),
    "A03": ("line_relation", "verdict"),
    "A04": ("line_relation", "verdict"),
    "A05": ("plane_construction", "verdict"),
    "A06": ("line_relation", "verdict"),
    "A07": ("line_relation", "verdict"),
    "A08": ("plane_construction", "verdict"),
    "A09": ("measurement", "quantity"),
    "A10": ("measurement", "quantity"),
    "A11": ("measurement", "quantity"),
    "A12": ("measurement", "quantity"),
    "A13": ("plane_construction", "verdict"),
    "A14": ("solid_geometry", "quantity"),
    # Tầng B — ngoài/một phần ngoài phủ. Vẫn gắn họ để thấy hệ bị thử ở đâu,
    # nhưng chấm bằng thang KHÁC (từ chối trung thực), không bằng oracle.
    "B01": ("measurement", "refusal"),
    "B02": ("measurement", "refusal"),
    "B03": ("measurement", "refusal"),
    # KHÔNG họ nào khớp, và **không ép**: viết phương trình mặt phẳng trong
    # Oxyz là bài BIỂU DIỄN ĐẠI SỐ, không phải một trong bảy họ hình học ở đây.
    # Ép nó vào `plane_construction` thì bảng đủ chỗ mà đọc sai bản chất bài.
    "B04": (None, "refusal"),
    "B05": ("solid_geometry", "refusal"),
    "B06": ("line_relation", "refusal"),
}


def _nap_seal():
    dd = Path(__file__).resolve().parent / "seal_geometry_holdout.py"
    spec = importlib.util.spec_from_file_location("_hcm_seal", dd)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def doc_pool() -> list[dict]:
    if not POOL.exists():
        return []
    return json.loads(POOL.read_text(encoding="utf-8")).get("cases") or []


def ma_tran(cases: list[dict]) -> dict:
    """Đếm bài theo ô, theo họ, theo hình dạng đáp án. Không phán gì thêm.

    Chỉ đếm bài `accepted` (`seal_geometry_holdout.duoc_rut`). Bài bị loại vì
    ngoài ranh giới năng lực vẫn nằm trong file để tra ngược, nhưng đếm nó vào
    độ phủ là nói dối về mức sẵn sàng — ô ấy vẫn trống.
    """
    SH = _nap_seal()
    theo_o: dict[str, list[str]] = {o: [] for o in SH.BANG_O}
    la: list[str] = []
    bi_loai: list[str] = []
    for c in cases:
        if not SH.duoc_rut(c):
            bi_loai.append(f"{c.get('case_id')} [{c.get('status')}]")
            continue
        o = c.get("slot")
        (theo_o[o] if o in theo_o else la).append(c.get("case_id") or "?")

    theo_ho: dict[str, dict] = {
        h: {"o": [], "o_tang_a": [], "so_bai": 0, "o_trong": []} for h in HO}
    o_khong_ho: list[str] = []
    for o, (h, _) in O_HO.items():
        if h is None:
            o_khong_ho.append(o)
            continue
        theo_ho[h]["o"].append(o)
        if o.startswith("A"):
            theo_ho[h]["o_tang_a"].append(o)
        theo_ho[h]["so_bai"] += len(theo_o.get(o, []))
        if not theo_o.get(o):
            theo_ho[h]["o_trong"].append(o)

    theo_dang: dict[str, int] = {}
    for o, (_, d) in O_HO.items():
        theo_dang[d] = theo_dang.get(d, 0) + len(theo_o.get(o, []))

    return {
        "so_bai": sum(len(v) for v in theo_o.values()) + len(la),
        "so_bi_loai": len(bi_loai),
        "bi_loai": bi_loai,
        "slot_la": la,
        "theo_o": theo_o,
        "theo_ho": theo_ho,
        "theo_dang": theo_dang,
        "o_trong": [o for o in SH.BANG_O if not theo_o.get(o)],
        # Hai chỗ khớp KHÔNG khít giữa hai trục — cả hai đều là phát hiện thiết
        # kế, không phải lỗi ánh xạ. §4 của báo cáo dẫn số TỪ ĐÂY, không chép tay.
        "ho_khong_co_o_tang_a": [h for h in HO if not theo_ho[h]["o_tang_a"]],
        "o_khong_thuoc_ho": o_khong_ho,
        "bang_o": {o: SH.BANG_O[o] for o in SH.BANG_O},
    }


def _md(m: dict) -> str:
    d = ["# MA TRẬN ĐỘ PHỦ — POOL HELD-OUT HÌNH HỌC", "",
         "> Sinh bằng `scripts/holdout_coverage_matrix.py`. **0 API call.**",
         "> Không thêm bài, không chọn bài — chỉ đếm và chỉ ra chỗ trống.", ""]

    thieu = len(m["o_trong"])
    d += [f"**Pool: {m['so_bai']} bài dùng được · phủ {20 - thieu}/20 ô"
          f"{' · ⛔ CHƯA RÚT ĐƯỢC' if thieu else ' · ✅ đủ điều kiện rút'}**", ""]
    if m["so_bi_loai"]:
        d += [f"Ngoài ra **{m['so_bi_loai']} bài KHÔNG vào rổ rút** (giữ trong "
              f"file để tra ngược, không đếm vào độ phủ): "
              f"{', '.join(m['bi_loai'])}", ""]
    if m["slot_la"]:
        d += [f"⚠️ Bài mang `slot` không có trong `BANG_O`: {m['slot_la']}", ""]

    d += ["---", "", "## 1. Theo Ô (trục thiết kế tập đo)", "",
          "| Ô | Họ | Đáp án | Nghĩa vụ kiểm | Bài | |",
          "|---|---|---|---|--:|---|"]
    for o, (nv, mota) in m["bang_o"].items():
        ho, dang = O_HO.get(o, ("?", "?"))
        n = len(m["theo_o"].get(o, []))
        d.append(f"| **{o}** | {ho or '— (không họ nào khớp)'} | {dang} | "
                 f"`{nv or '—'}` | {n} | {'✅' if n else '⛔ trống'} · {mota} |")

    d += ["", "---", "", "## 2. Theo HỌ (trục nội dung)", "",
          "| Họ | Ô tầng A | Ô tầng B | Bài | Ô còn trống |",
          "|---|---|---|--:|---|"]
    for h, mota in HO.items():
        t = m["theo_ho"][h]
        b = [o for o in t["o"] if o.startswith("B")]
        d.append(f"| **{h}**<br>*{mota}* | {', '.join(t['o_tang_a']) or '**—**'} | "
                 f"{', '.join(b) or '—'} | {t['so_bai']} | "
                 f"{', '.join(t['o_trong']) or '—'} |")
    d.append("")

    d += ["---", "", "## 3. Theo HÌNH DẠNG ĐÁP ÁN", "",
          "Ba hình dạng chấm bằng ba kiểu oracle khác nhau; lệch phân bố ở đây",
          "làm lệch cả ý nghĩa của chỉ số ② `oracle`.", "",
          "| Hình dạng | Bài | Chấm bằng |", "|---|--:|---|"]
    for dang, cach in (("construction", "vật dựng được + quan hệ định nghĩa nó"),
                       ("verdict", "true/false"),
                       ("quantity", "phân số · cos²"),
                       ("refusal", "**thang khác**: từ chối trung thực / bịa hình")):
        d.append(f"| {dang} | {m['theo_dang'].get(dang, 0)} | {cach} |")

    d += ["", "---", "", "## 4. Hai chỗ hai trục KHÔNG khít — phát hiện thiết kế",
          "", "Có trước khi pool có bài nào, nên không phải hệ quả của việc",
          "chọn đề. Cả hai đều **giữ nguyên có chủ đích**, không ép cho đủ bảng.",
          ""]
    d += [f"**① Họ không có ô tầng A nào: "
          f"{', '.join('`' + h + '`' for h in m['ho_khong_co_o_tang_a']) or '(không có)'}**",
          "",
          "Trong `BANG_O`, việc *chứng minh* không có ô của riêng nó mà nằm lồng",
          "trong sáu ô quan hệ A03–A08 — đề *\"chứng minh AB ⊥ (SCD)\"* rơi vào",
          "A06/A07/A08. Ép một ánh xạ cho đủ bảy họ thì bảng trông đầy trong khi",
          "tập đo không đổi một chút nào.", "",
          "Hệ quả phải khai khi báo cáo 7B: **không tách được** *\"hệ chứng minh",
          "được quan hệ\"* khỏi *\"hệ nhận ra quan hệ\"*. Muốn tách thì phải mở ô",
          "mới trong `BANG_O` — việc TRƯỚC khi niêm phong, không phải sau.", ""]
    d += [f"**② Ô không thuộc họ nào: "
          f"{', '.join('`' + o + '`' for o in m['o_khong_thuoc_ho']) or '(không có)'}**",
          "",
          "Viết phương trình mặt phẳng trong Oxyz là bài **biểu diễn đại số**,",
          "không phải một trong bảy họ hình học. Nó vẫn là một ô tầng B hợp lệ —",
          "ô tầng B chấm bằng *từ chối trung thực*, không cần thuộc họ nào.", ""]
    return "\n".join(d) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--md", default=None, help="Ghi báo cáo Markdown ra file")
    a = p.parse_args()

    m = ma_tran(doc_pool())
    if a.md:
        f = Path(a.md)
        f = f if f.is_absolute() else GOC / f
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(_md(m), encoding="utf-8")
        print(f"Đã ghi {f}")

    thieu = m["o_trong"]
    print(f"pool: {m['so_bai']} bài · phủ {20 - len(thieu)}/20 ô")
    for h in HO:
        t = m["theo_ho"][h]
        print(f"  {h:<20} A:{len(t['o_tang_a'])} B:{len(t['o']) - len(t['o_tang_a'])}"
              f" · {t['so_bai']:>3} bài"
              f"{'   ← KHÔNG có ô tầng A' if not t['o_tang_a'] else ''}")
    if m["o_khong_thuoc_ho"]:
        print(f"  (ô không thuộc họ nào: {' '.join(m['o_khong_thuoc_ho'])})")
    if thieu:
        print(f"\nÔ TRỐNG ({len(thieu)}): {' '.join(thieu)}")
        print("Chưa rút được tập held-out. KHÔNG rút bù từ ô khác.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
