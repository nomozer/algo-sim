# -*- coding: utf-8 -*-
"""Sinh `PHASE7B_HUMAN_COPY_PACKET.txt` — MỘT file cho toàn bộ phần con người.

    python scripts/make_human_copy_packet.py            # in ra
    python scripts/make_human_copy_packet.py --ghi      # ghi file gói

**0 API call.** Không tạo đề, không tạo đáp án, không ký thay.

─── VÌ SAO MỘT GÓI CHỨ KHÔNG 40 LƯỢT HỎI ──────────────────────────────────

Phần máy làm được của tập held-out đã xong từ lâu; phần còn lại là **gõ lại đề
nguyên văn**, và nó không chia nhỏ được thành 40 lượt trao đổi mà không tiêu
hết thời gian của người chép vào việc mở lại tài liệu. Gói này gom mọi ô về
**một file, xếp theo NGUỒN**, để mỗi tài liệu chỉ phải mở đúng một lần.

─── MÁY ĐIỀN GÌ, NGƯỜI ĐIỀN GÌ ────────────────────────────────────────────

Máy điền **mọi thứ suy ra được**: `slot` · `capability_tag` · `answer_shape` ·
nghĩa vụ oracle · thang chấm · nguồn nhắm tới · ràng buộc riêng của ô. Với hai
ứng viên đã soi tận trang thì điền luôn `NGUỒN` và `ĐÁP ÁN`.

Người điền **đúng một thứ**: `ĐỀ NGUYÊN VĂN`, cộng **một** chữ ký ở đầu file.

⚠️ `problem_text` **không** được prefill bằng bản máy đọc lại — kể cả bản tôi
đã đọc từ ảnh trang. `HOLDOUT_SOURCE_POLICY §4`: hành vi chép của người CHÍNH
LÀ bước xác minh, nên một bản nháp máy đặt sẵn ở đó chỉ mời người ta bấm qua.

─── KHÔNG HẠN NGẠCH CỨNG ──────────────────────────────────────────────────

`HOLDOUT_PROTOCOL §3①` đòi **mỗi ô ≥1** và **tổng ≥40** — không đòi ô nào đúng
mấy bài. Gói phát dư (~47 khối) để sau lượt loại của người vẫn còn ≥40: tỉ lệ
đạt đo được ở vùng đã soi là **≈25%** với tầng A có oracle.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
RA = GOC / "docs" / "evaluation" / "geometry" / "holdout" / \
    "PHASE7B_HUMAN_COPY_PACKET.txt"

#: Số **khối phát ra** mỗi ô. Không phải hạn ngạch — xem docstring. Ô nào khó
#: tìm thì phát dư hơn, vì cái đắt là mở lại tài liệu chứ không phải gõ thêm.
PHAT: dict[str, int] = {
    **{o: 2 for o in ("A01", "A02", "A03", "A04", "A05",
                      "A06", "A07", "A08")},
    "A09": 3, "A10": 3, "A13": 3,
    # Khó nhất: `distance` phải ra HỮU TỈ. Phát dư nhất.
    "A11": 3, "A12": 3,
    # Đã soi được 2 ứng viên tận trang ⇒ 2 khối đầu có sẵn nguồn + đáp án.
    "A14": 4,
    **{o: 2 for o in ("B01", "B02", "B03", "B04", "B05", "B06")},
}

#: Ứng viên **đã soi tận trang** ở lượt trước (đọc ảnh trang, không phải trích
#: PDF). Chỉ nguồn + đáp án được prefill — đề vẫn phải do người gõ.
DA_SOI: dict[str, list[dict]] = {
    "A14": [
        {"nguon": "Tài liệu chuyên đề khối đa diện và thể tích khối đa diện — "
                  "trang 80, Câu 1 · https://toanmath.com/2023/07/tai-lieu-"
                  "chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html",
         "dap_an": "2/3",
         "goi_y": "ABC vuông tại A · AB = a · AC = 2a · SA ⊥ đáy · SA = 2a",
         "vi_sao": "đề NGẮN NHẤT; không bước nào sinh căn; lời giải cùng trang",
         "rui_ro": "thấp nhất trong vùng đã soi"},
        {"nguon": "Tài liệu chuyên đề khối đa diện và thể tích khối đa diện — "
                  "trang 82, Câu 7 · https://toanmath.com/2023/07/tai-lieu-"
                  "chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html",
         "dap_an": "8/3",
         "goi_y": "đáy chữ nhật · SA ⊥ (ABCD) · AB = 3a · AD = 2a · SB = 5a",
         "vi_sao": "đi qua Pythagoras mà VẪN hữu tỉ (bộ ba 3-4-5)",
         "rui_ro": "trung bình — SA là SUY RA, phải xác nhận lời giải nguồn "
                   "cho V = 8a³/3 chứ đừng tự tính"},
    ],
}

#: Ô chưa tra được nguồn nào — `PHASE 6` đòi đánh dấu chứ không đổi giao thức.
SOURCE_GAP = ("A11", "A12")

#: Luật sàng nhanh, dán ngay chỗ cần dùng. Luật ĐỦ chỉ có một, ở `_MO_DAU`.
_GOI_Y_O: dict[str, str] = {
    "A09": "`cos²` giữa HAI ĐƯỜNG. Toạ độ hữu tỉ ⇒ `cos²` luôn hữu tỉ, nên ô "
           "này KHÔNG vướng rào vô tỉ ở đáp án — dễ hơn A11/A12 nhiều.",
    "A10": "⚠️ Đường–MẶT trả **`sin²`**, KHÔNG phải `cos²`. Chép nhầm thì chấm "
           "sai mà không cổng nào báo. Đáp án sách hay cho góc α ⇒ ghi `sin²α`.",
    "A11": "Khoảng cách điểm → MẶT. Chỉ nhận khi ra phân số HỮU TỈ.\n"
           "Mẹo: d = |…| / √(a²+b²+c²) — hữu tỉ khi pháp tuyến có chuẩn hữu "
           "tỉ,\n"
           "tức các cạnh góc vuông làm thành bộ ba Pythagore (3-4-5, 6-8-10, "
           "5-12-13).",
    "A12": "Khoảng cách điểm → ĐƯỜNG. Cùng luật hữu tỉ như A11.",
    "A13": "Cần khối **LỒI**. Đề thiết diện hay kèm hình vẽ — bỏ bài nào phải "
           "nhìn hình mới hiểu.",
    "A14": "Thể tích. Gán `a = 1` rồi chép phân số (`2a³/3` → `2/3`).",
}

_MO_DAU = """\
# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 7B — GÓI CHÉP TAY  ·  MỘT FILE CHO TOÀN BỘ PHẦN CON NGƯỜI
# ═══════════════════════════════════════════════════════════════════════════
#
#  Bạn chỉ phải làm HAI việc:
#
#    ①  điền chữ ký ở dòng `NGƯỜI CHÉP:` ngay dưới — MỘT lần cho cả file
#    ②  gõ đề nguyên văn vào mỗi chỗ `<GÕ NGUYÊN VĂN …>`
#
#  Mọi thứ khác đã điền sẵn bằng cách dẫn từ `BANG_O` + `NANG_LUC`.
#  Không cần điền hết mới chạy được: **xoá nguyên khối nào bạn bỏ qua**.
#
# ─── LUẬT SÀNG — ĐỌC MỘT LẦN, DÙNG CHO CẢ FILE ────────────────────────────
#
#  Luật ĐỦ, và là luật DUY NHẤT đủ:
#
#        « ĐẶT ĐƯỢC CẢ HÌNH VÀO TOẠ ĐỘ HỮU TỈ KHÔNG? »
#
#  Kernel dựng trên `Fraction` — số hữu tỉ chính xác, không có epsilon. Một
#  toạ độ đỉnh vô tỉ là bài NGOÀI phủ, dù đề và đáp án trông sạch thế nào.
#
#  Loại nhanh bằng mắt (đều là luật PHỤ, không đủ):
#      √ trong dữ kiện hoặc đáp án      → bỏ
#      tam giác đều · vuông cân         → bỏ  (tỉ số 1:√2, đường cao a√3/2)
#      góc 30° · 60° · 120°             → bỏ  (tan/cos sinh √3)
#      mặt cầu · nón · trụ              → bỏ khỏi TẦNG A (nhưng hợp ô B05!)
#      Oxyz cho sẵn toạ độ              → bỏ khỏi TẦNG A (hợp ô B04)
#      "như hình vẽ" mà không có hình   → bỏ  (thiếu dữ kiện)
#      trắc nghiệm A. B. C. D.          → bỏ  (7B chỉ nhận tự luận)
#
#  ⚠️ Vì sao "nhìn đáp án có căn không" KHÔNG đủ: tr 80 Câu 2 có dữ kiện sạch
#     (`SA = BC = a`) và đáp án sạch (`a³/12`), vẫn ngoài phủ — vuông cân ⇒
#     `AB : BC = 1 : √2` ⇒ không hệ trục nào đặt cả ba đỉnh vào toạ độ hữu tỉ.
#     Cạnh KHÔNG dùng tới thì được phép vô tỉ; cái quyết định là TOẠ ĐỘ ĐỈNH.
#
# ─── HAI THANG CHẤM, ĐỪNG TRỘN ────────────────────────────────────────────
#
#  TẦNG A (A01–A14) hỏi: *hệ tính ĐÚNG không* → cần `ĐÁP ÁN:`
#  TẦNG B (B01–B06) hỏi: *hệ có BIẾT mình không tính được không*
#                        → KHÔNG có `ĐÁP ÁN:`; dùng `ĐÁP ÁN NGUỒN:` để ghi
#                          đáp án sách (chỉ để tra ngược, không dùng chấm)
#
#  Tầng B là phần DỄ NHẤT của cả gói: không cần đáp án đúng, không cần soi
#  toạ độ, không luật sàng nào — chỉ cần đề ĐÚNG LOẠI.
#
# ─── XONG THÌ CHẠY ────────────────────────────────────────────────────────
#
#    cd backend
#    python scripts/validate_human_copy_packet.py \\
#        ../docs/evaluation/geometry/holdout/PHASE7B_HUMAN_COPY_PACKET.txt
#    python scripts/run_phase7b_data_pipeline.py \\
#        ../docs/evaluation/geometry/holdout/PHASE7B_HUMAN_COPY_PACKET.txt --ghi
#
# ═══════════════════════════════════════════════════════════════════════════

NGƯỜI CHÉP: <tên bạn> · <YYYY-MM-DD> · <chép từ tài liệu nào>
"""


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_pk_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"_pk_{ten}"] = m
    spec.loader.exec_module(m)
    return m


def _khoi(o: str, SH, MT, da_soi: dict | None,
          thu: int = 1, tong: int = 1) -> list[str]:
    """Một khối cho một ứng viên. Siêu dữ liệu đi bằng dòng `#` — `ingest` gỡ
    sạch chúng trước khi lấy `problem_text`, nên chúng không lọt vào đề."""
    tag, hinh, tang_a = next(
        (t, h, a) for t, (os_, h, a) in SH.NANG_LUC.items() if o in os_)
    nv = SH.BANG_O[o][0]
    dau = f"{o} ({thu}/{tong}) · {SH.BANG_O[o][1]}"
    d = [f"#   ─── {dau} " + "─" * max(3, 60 - len(dau)),
         f"#     CAPABILITY : {tag}",
         f"#     ANSWER     : {hinh}" + (f" → nghĩa vụ `{nv}`" if nv else ""),
         f"#     THANG CHẤM : " + ("oracle + ③a/③b/⑤" if tang_a
                                   else "TỪ CHỐI TRUNG THỰC — không oracle")]
    if o in ("A10",):
        d.append("#     ⚠️ ĐƠN VỊ   : sin² (đường–mặt), KHÔNG phải cos²")
    if goi := _GOI_Y_O.get(o):
        for i, g in enumerate(goi.split("\n")):
            d.append(f"#     TÌM BÀI    : {g}" if i == 0
                     else f"#                  {g}")
    if them := MT.O_RANG_BUOC_THEM.get(o):
        d.append("#     RÀNG BUỘC  : " + them.replace("**", ""))
    if o in SOURCE_GAP:
        d.append(f"#     ⛔ SOURCE_GAP_{o} — chưa tra được nguồn nào có sẵn "
                 f"bài loại này. Bỏ qua được.")
    if da_soi:
        d += [f"#     ĐÃ SOI     : {da_soi['goi_y']}",
              f"#     VÌ SAO CHỌN: {da_soi['vi_sao']}",
              f"#     RỦI RO     : {da_soi['rui_ro']}",
              "#     → NGUỒN và ĐÁP ÁN đã điền sẵn. Chỉ còn gõ ĐỀ."]

    d.append(f"[{o}] <GÕ NGUYÊN VĂN ĐỀ VÀO ĐÂY — giữ đủ = ⊥ ∥ ∈ √ ·>")
    d.append(f"      NGUỒN: {da_soi['nguon'] if da_soi else '<sách · trang · câu>   hoặc   <url>'}")
    if tang_a:
        d.append(f"      ĐÁP ÁN: {da_soi['dap_an'] if da_soi else '<đáp án của nguồn, dạng phân số hoặc true/false>'}")
    else:
        d += ["      ĐÁP ÁN NGUỒN: <đáp án in trong sách — chỉ để tra ngược>",
              f"      NGOÀI PHỦ VÌ: {SH.BANG_O[o][1]} — ngoài ranh giới kernel"]
    d.append("")
    return d


def dung_goi() -> str:
    SH, MT = _nap("seal_geometry_holdout"), _nap("holdout_coverage_matrix")
    d = _MO_DAU.splitlines() + [""]

    # Xếp theo NGUỒN để mỗi tài liệu chỉ phải mở một lần — đó là toàn bộ lý do
    # gói này tồn tại thay vì 40 lượt hỏi.
    theo_nguon: dict[str, list[str]] = {}
    for o in SH.BANG_O:
        theo_nguon.setdefault(MT.O_NGUON[o], []).append(o)

    for i, (nguon, cac_o) in enumerate(theo_nguon.items(), 1):
        tong = sum(PHAT[o] for o in cac_o)
        d += ["", "# " + "═" * 71,
              f"#  NGUỒN {i} — {nguon}",
              f"#  {len(cac_o)} ô · {tong} khối · ô: {' '.join(cac_o)}",
              "# " + "═" * 71, ""]
        for o in cac_o:
            soi = DA_SOI.get(o, [])
            for k in range(PHAT[o]):
                d += _khoi(o, SH, MT, soi[k] if k < len(soi) else None,
                           k + 1, PHAT[o])

    tong = sum(PHAT.values())
    d += ["# " + "═" * 71,
          f"#  HẾT — {tong} khối / {len(SH.BANG_O)} ô.",
          f"#  Cần ≥{SH.MOI_O_TOI_THIEU} bài mỗi ô và ≥{SH.TONG_TOI_THIEU} "
          f"tổng ⇒ gói phát dư {tong - SH.TONG_TOI_THIEU} khối làm dự phòng.",
          "#  Khối nào bỏ qua thì XOÁ NGUYÊN KHỐI, đừng để chỗ trống.",
          "# " + "═" * 71, ""]
    return "\n".join(d)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ghi", action="store_true", help="Ghi file gói")
    a = p.parse_args()

    goi = dung_goi()
    if a.ghi:
        if RA.exists():
            # Gói đã điền là CÔNG SỨC CỦA NGƯỜI. Ghi đè nó là xoá phần duy
            # nhất của tập held-out mà máy không dựng lại được.
            print(f"ĐÃ CÓ: {RA}")
            print("KHÔNG ghi đè — gói có thể đã điền dở. Xoá tay nếu muốn dựng lại.")
            return 1
        RA.write_text(goi, encoding="utf-8")
        print(f"Đã ghi {RA}")
    else:
        print(goi)
    print(f"\n{sum(PHAT.values())} khối · {len(PHAT)} ô · "
          f"SOURCE_GAP: {', '.join(SOURCE_GAP)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
