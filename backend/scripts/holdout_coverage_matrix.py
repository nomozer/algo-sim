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


#: `slot → nguồn đang nhắm`. Giống `O_HO`: **phán đoán của người**, không suy
#: ra được từ dữ liệu — nên để ở đây, đọc được và sửa được, thay vì nằm rải
#: trong một bảng markdown mà không cổng nào canh.
#:
#: Bảng ấy đã trôi thật: `CANDIDATE_REVIEW §3` từng ghi số bài cần cho từng ô
#: như một hạn ngạch cứng, trong khi `HOLDOUT_EXPANSION_PLAN §1` cố ý để mềm
#: (*"mỗi ô cần ≥1 bài; tổng ≥40 ⇒ trung bình 2 bài/ô. Ô nào dễ tìm thì lấy"*).
O_NGUON: dict[str, str] = {
    **{o: "Quan hệ song song Toán 11 (32tr, 0 trắc nghiệm)"
       for o in ("A01", "A02", "A03", "A04", "A05", "A13")},
    **{o: "Quan hệ vuông góc — Lê Minh Tâm (117tr, 0 trắc nghiệm)"
       for o in ("A06", "A07", "A08", "A09", "A10")},
    "A11": "—", "A12": "—",
    "A14": "Khối đa diện & thể tích, tr 80–94 (2 ứng viên đã soi)",
    **{o: "bất kỳ — không cần đáp án đúng, chỉ cần đúng LOẠI"
       for o in ("B01", "B02", "B03", "B04", "B05", "B06")},
}

#: Ô đang chờ **quyết định**, không chờ dữ liệu. Ghi riêng vì hai thứ ấy có
#: hai người gỡ khác nhau, và gộp chúng vào "blocker" làm mất mất thông tin ấy.
O_CHO_QUYET_DINH: dict[str, str] = {
    o: "chờ quyết định ①: chỉ nhận `distance` hữu tỉ, hay mở ô tầng B cho lớp "
       "vô tỉ (mở ⇒ N đổi khỏi 20 ⇒ chốt lại ngân sách)"
    for o in ("A11", "A12")
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


def _bang_ke_hoach(m: dict) -> list[str]:
    """Bảng KẾ HOẠCH từng ô — `oracle`, chỉ số sẽ chấm, nguồn, việc kế tiếp.

    Sinh ra chứ không gõ: mọi cột trừ `nguồn` **dẫn thẳng** từ `BANG_O` và
    `NANG_LUC`. Bảng gõ tay của cùng nội dung này đã sai một lần (khai hạn
    ngạch cứng cho thứ kế hoạch cố ý để mềm), và sai kiểu ấy không làm test
    nào đỏ vì không cổng nào đọc markdown.
    """
    SH = _nap_seal()
    d = ["", "---", "", "## 1b. KẾ HOẠCH TỪNG Ô — sinh từ `BANG_O` + `NANG_LUC`",
         "",
         f"Ngưỡng pool (`HOLDOUT_PROTOCOL §3①`): **mỗi ô ≥ "
         f"{SH.MOI_O_TOI_THIEU} bài** *và* **tổng ≥ {SH.TONG_TOI_THIEU} bài**.",
         "Hai vế, hai câu hỏi — đủ ô mà thiếu bài thì mọi seed cho ra cùng một",
         "tập. Kế hoạch **không** đặt hạn ngạch cứng cho từng ô: ô nào dễ tìm",
         "thì lấy nhiều, miễn không ô nào rỗng và tổng đủ.", "",
         "| Ô | Cần | `capability_tag` | oracle | Chỉ số chấm | Nguồn | Có | Chặn ở | Việc kế tiếp |",
         "|---|---|---|---|---|---|--:|---|---|"]
    for o in SH.BANG_O:
        tag, hinh, tang_a = next(
            (t, h, a) for t, (os_, h, a) in SH.NANG_LUC.items() if o in os_)
        nv = SH.BANG_O[o][0]
        n = len(m["theo_o"].get(o, []))
        oracle = (f"`{hinh}` → `{nv}`" if tang_a else f"`{hinh}` — **bỏ trống**")
        # ⚠️ Ô A10 trả `sin²` dưới cùng tên trường `angle_cos_sq`. Đánh dấu ở
        # đây vì đó là chỗ duy nhất trong bảng khai sai mà KHÔNG cổng nào báo.
        if tag == "angle_sin_sq":
            oracle += " ⚠️ **`sin²`**, không phải `cos²`"
        chi_so = ("① ② ③a ③b ⑤" if tang_a else "**từ chối trung thực** — thang KHÁC")
        if chan := O_CHO_QUYET_DINH.get(o):
            chan_txt, viec = "⛔ **quyết định**", chan
        elif n < SH.MOI_O_TOI_THIEU:
            chan_txt, viec = "⛔ chưa có bài", "người mở nguồn, chép nguyên văn, ký"
        else:
            chan_txt, viec = "—", "đủ tối thiểu; thêm bài để tổng đạt ngưỡng"
        d.append(f"| **{o}** | ≥{SH.MOI_O_TOI_THIEU} | `{tag}` | {oracle} | "
                 f"{chi_so} | {O_NGUON.get(o, '—')} | {n} | {chan_txt} | {viec} |")
    return d


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

    d += _bang_ke_hoach(m)

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
        # Đường dẫn tương đối được ghép vào GỐC KHO, nên `../docs/…` — cách gõ
        # tự nhiên khi đang đứng ở `backend/` — lặng lẽ trỏ RA NGOÀI kho và
        # `mkdir(parents=True)` dựng luôn một cây tài liệu lạc ở đó (xảy ra
        # thật 2026-08-28). Báo cáo ghi ngoài kho thì không ai thấy nó nữa.
        try:
            f.resolve().relative_to(GOC)
        except ValueError:
            print(f"TỪ CHỐI: {f.resolve()} nằm NGOÀI kho {GOC}.")
            print("Đường dẫn tương đối tính từ GỐC KHO, không từ thư mục hiện "
                  "tại — viết `docs/evaluation/…`, không `../docs/evaluation/…`.")
            return 2
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
