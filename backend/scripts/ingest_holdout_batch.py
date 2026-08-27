# -*- coding: utf-8 -*-
"""Nạp một LÔ đề held-out do NGƯỜI chép, thành mục `pool.json`. **0 API call.**

    python scripts/ingest_holdout_batch.py lo1.txt            # soi, không ghi
    python scripts/ingest_holdout_batch.py lo1.txt --ghi      # ghi vào pool.json

─── VÌ SAO FILE NÀY TỒN TẠI ───────────────────────────────────────────────

Ba lượt quét, **673 url**, cho **0** bài tự luận trong ranh giới. Kênh tự động
cạn, và kết luận là **người phải chép đề**. Nhưng phần người phải làm thì nhỏ
hơn nhiều so với việc điền JSON: chỉ cần **ba dòng mỗi bài**. File này lo phần
còn lại — xếp trường, gán thẻ năng lực, dựng `oracle_result`, chạy cổng.

─── AI HẠ `problem_text_verified`, VÀ VÌ SAO KHÔNG PHẢI TÔI ───────────────

Giao thức đòi đề **NGUYÊN VĂN**, và đã đo được rằng **mọi kênh tự động đều
hỏng IM LẶNG**: công cụ đọc web đi qua một mô hình tóm tắt; trích PDF rơi ký
hiệu toán (`⊥` xuất hiện **0 lần** trong một chuyên đề 217 trang về quan hệ
vuông góc). Văn bản hỏng vẫn **đọc như một đề bài** — đó là chỗ nguy hiểm.

Thứ duy nhất chưa hỏng là **người mở sách ra đọc và gõ lại**. Nên hành vi chép
ấy **CHÍNH LÀ** bước xác minh, và file lô phải mang một dòng khai ai đã chép:

    NGƯỜI CHÉP: <tên> · <ngày> · <chép từ đâu: sách/PDF nào, trang nào>

Không có dòng ấy ⇒ script **từ chối**, và mọi bài đi ra mang
`problem_text_verified: false` + `status: rejected_unverified`.

⚠️ **Dòng ấy do NGƯỜI viết.** Tôi tự viết nó vào file lô là tự cấp cho mình một
chứng nhận mà tôi không có tư cách cấp — và nó bỏ đúng cái cổng vừa dựng.

─── KHUÔN FILE LÔ ─────────────────────────────────────────────────────────

    NGƯỜI CHÉP: Nguyễn Văn A · 2026-08-28 · SGK Toán 11 tập 2 KNTT

    [A14] Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, cạnh bên SA
          vuông góc với mặt phẳng đáy và SA = 3. Tính thể tích khối chóp S.ABCD.
          NGUỒN: SGK Toán 11 tập 2 KNTT, bài 7.15 trang 62
          ĐÁP ÁN: 4

    [A09] …

Dòng `ĐÁP ÁN` chép **đáp án của nguồn**, đúng đơn vị checker
(`pool.json.__don_vi_oracle__`): `distance`/`volume` là phân số · `angle` là
`cos²` (đường–đường, mặt–mặt) hoặc **`sin²`** (đường–mặt) · quan hệ là
`true`/`false`. Ô `B*` **bỏ trống** dòng ấy.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
POOL = GOC / "docs" / "evaluation" / "geometry" / "holdout" / "pool.json"

_NGUOI = re.compile(r"^\s*NGƯỜI CHÉP\s*:\s*(.+?)\s*$", re.M)
_BAI = re.compile(r"^\s*\[([AB]\d{2})\]\s*(.+?)(?=^\s*\[[AB]\d{2}\]|\Z)",
                  re.M | re.S)
_NGUON = re.compile(r"^\s*NGUỒN\s*:\s*(.+?)\s*$", re.M)
_DAPAN = re.compile(r"^\s*ĐÁP ÁN\s*:\s*(.+?)\s*$", re.M)

#: Dấu hiệu bài KHÔNG hợp luật nhận của Phase 7B.1 — cảnh báo, không tự loại:
#: phán quyết cuối là của người, script chỉ chỉ chỗ.
_CANH_BAO = (
    (re.compile(r"\bA\.\s.*\bB\.\s.*\bC\.\s", re.S),
     "có vẻ là TRẮC NGHIỆM 4 phương án — luật 7B.1 chỉ nhận tự luận"),
    (re.compile(r"√|\\sqrt"),
     "đề chứa CĂN THỨC — kiểm tỉ số dữ kiện có hữu tỉ hoá được không"),
    (re.compile(r"tham khảo hình vẽ|hình vẽ bên|như hình", re.I),
     "đề tham chiếu HÌNH VẼ không có trong văn bản ⇒ thiếu dữ kiện"),
    (re.compile(r"mặt cầu|hình nón|hình trụ", re.I),
     "MẶT CONG — ngoài ranh giới (kernel dựng trên đa diện)"),
    (re.compile(r"Oxyz|hệ (?:tọa|toạ) độ", re.I),
     "Oxyz cho sẵn toạ độ ⇒ mô hình không phải tự đặt hệ trục"),
)


def _nap_seal():
    dd = Path(__file__).resolve().parent / "seal_geometry_holdout.py"
    spec = importlib.util.spec_from_file_location("_ing_seal", dd)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _khoa_oracle(SH, tag: str) -> str | None:
    return {"rational_distance": "distance", "rational_volume": "volume",
            "angle_cos_sq": "angle", "angle_sin_sq": "angle"}.get(tag)


def _the_cho_o(SH, o: str) -> str | None:
    """Ô → thẻ năng lực. Ô có NHIỀU thẻ thì trả `None` — không đoán."""
    hop = [t for t, (os_, _, _) in SH.NANG_LUC.items() if o in os_]
    return hop[0] if len(hop) == 1 else None


#: Dấu CHỖ TRỐNG chưa điền. Bịt ở đây vì khuôn `batch_001.txt` mang sẵn chúng,
#: và một `NGƯỜI CHÉP: <tên người chép>` lọt qua thì cổng xác minh thành ô
#: trống — đúng cái nó sinh ra để chặn.
#: CHỈ `<…>` và `TODO`. Không bắt `…`/`...` đứng một mình — dấu ba chấm xuất
#: hiện hợp lệ trong đề thật, và bắt nó là từ chối dữ liệu ĐÚNG.
_CHO_TRONG = re.compile(r"<[^>]*>|\bTODO\b")


def _con_cho_trong(s: str | None) -> bool:
    return bool(s) and bool(_CHO_TRONG.search(s))


def _bo_chu_thich(van_ban: str) -> str:
    """Bỏ dòng bắt đầu bằng `#`.

    KHÔNG phải tiện nghi: khuôn `batch_001.txt` có khối hướng dẫn ở cuối, và
    không bỏ thì cả khối ấy bị nuốt vào **đề bài của bài cuối cùng** — một đề
    dài ngoằng vẫn qua được mọi cổng về mặt kiểu, rồi vào tập đã niêm phong.
    """
    return "\n".join(d for d in van_ban.splitlines()
                     if not d.lstrip().startswith("#"))


def phan_tich(van_ban: str, SH) -> tuple[str | None, list[dict], list[str]]:
    """Trả `(người chép, danh sách bài, danh sách lỗi)`."""
    van_ban = _bo_chu_thich(van_ban)
    loi: list[str] = []
    m = _NGUOI.search(van_ban)
    nguoi = m.group(1).strip() if m else None
    if not nguoi:
        loi.append(
            "THIẾU dòng `NGƯỜI CHÉP:` — không có nó thì không ai chịu trách "
            "nhiệm cho việc đề đúng NGUYÊN VĂN, và mọi kênh tự động đã đo được "
            "là hỏng IM LẶNG. Xem docstring.")
    elif _con_cho_trong(nguoi):
        loi.append(
            f"`NGƯỜI CHÉP: {nguoi}` vẫn là CHỖ TRỐNG chưa điền. Một chứng nhận "
            "xác minh mang tên `<tên người chép>` thì không chứng nhận gì cả — "
            "điền tên thật, ngày thật, và chép từ đâu.")

    bai: list[dict] = []
    for i, (o, than) in enumerate(_BAI.findall(van_ban), 1):
        ma = f"hp_{o.lower()}_{i:03d}"
        de = _NGUON.sub("", _DAPAN.sub("", than)).strip()
        de = re.sub(r"\s+", " ", de)
        nguon = (g.group(1) if (g := _NGUON.search(than)) else None)
        dap_an = (g.group(1) if (g := _DAPAN.search(than)) else None)
        tag = _the_cho_o(SH, o)

        if len(de) < 40:
            loi.append(f"{ma}: đề quá ngắn ({len(de)} ký tự) — chép thiếu?")
        for ten, gt in (("đề", de), ("NGUỒN", nguon), ("ĐÁP ÁN", dap_an)):
            if _con_cho_trong(gt):
                loi.append(f"{ma}: {ten} vẫn là CHỖ TRỐNG chưa điền ({gt!r})")
        if not nguon:
            loi.append(f"{ma}: thiếu dòng `NGUỒN:` — đáp án không tra ngược "
                       "được thì không phải oracle độc lập")
        if tag is None:
            loi.append(f"{ma}: ô {o} ứng với NHIỀU thẻ năng lực — khai tay "
                       "`capability_tag`, script không đoán")
        if o.startswith("A") and not dap_an:
            loi.append(f"{ma}: ô tầng A phải có dòng `ĐÁP ÁN:`")
        if o.startswith("B") and dap_an:
            loi.append(f"{ma}: ô tầng B chấm bằng 'từ chối trung thực', "
                       "KHÔNG được có `ĐÁP ÁN:`")

        canh_bao = [msg for r, msg in _CANH_BAO if r.search(de)]
        bai.append({"ma": ma, "o": o, "de": de, "nguon": nguon,
                    "dap_an": dap_an, "tag": tag, "canh_bao": canh_bao})
    if not bai:
        loi.append("Không đọc được bài nào — mỗi bài phải mở đầu bằng `[A14]`.")
    return nguoi, bai, loi


def thanh_case(b: dict, nguoi: str, SH) -> dict:
    o, tag = b["o"], b["tag"]
    _, dang, _ = SH.NANG_LUC[tag]
    # NGHĨA VỤ KIỂM dẫn từ `BANG_O`, không hỏi người.
    #
    # Bỏ sót chỗ này là lỗ đã có thật: lô nạp xong trông hợp lệ, `answer_shape`
    # đúng, oracle đúng — rồi trượt `kiem_pool` ở dòng *"ô A14 đòi nghĩa vụ
    # 'volume'"*, tức gãy GIỮA hai chặng mà từng chặng đều xanh. Test đầu-cuối
    # bắt được; test từng chặng thì không.
    nghia_vu = [nv] if (nv := SH.BANG_O[o][0]) else []
    c = {
        "case_id": b["ma"],
        "status": "accepted",
        "slot": o, "coverage_slot": o,
        "capability_tag": tag, "answer_shape": dang,
        "expected_obligations": nghia_vu,
        "expected_verification_types": nghia_vu,
        "domain": "geometry_3d",
        "problem_text": b["de"], "problem_text_original": b["de"],
        # Chính hành vi CHÉP của người là bước xác minh — xem docstring.
        "problem_text_verified": True,
        "nguon": {"ten": b["nguon"], "url": b["nguon"], "vi_tri": b["nguon"]},
        "evaluator": b["nguon"],
        "answer_available": bool(b["dap_an"]),
        "dap_an_chinh_thuc": b["dap_an"],
        "chua_chay_he": True,
        # AI xác minh — TRƯỜNG RIÊNG, không chôn trong một câu văn.
        #
        # Trước bản này danh tính người chép chỉ nằm trong `verifier_note` dạng
        # văn xuôi. Câu *"ai đã xác minh bài này"* khi ấy chỉ trả lời được bằng
        # cách bóc chuỗi — tức không kiểm được bằng máy, mà đây đúng là thứ cần
        # kiểm được: nó là chữ ký cho toàn bộ bước xác minh nguyên văn.
        "human_verifier": nguoi,
        "verification_note": (
            f"Đề do NGƯỜI chép nguyên văn từ nguồn: {nguoi}. Không qua OCR, "
            "không qua công cụ đọc web, không qua mô hình viết lại."),
        "verifier_note": f"NGƯỜI CHÉP: {nguoi}",
    }
    if (khoa := _khoa_oracle(SH, tag)) and b["dap_an"]:
        c["oracle_result"] = {khoa: b["dap_an"]}
        # KHOÁ NÀO trong `oracle_result` là oracle — khai tường minh.
        #
        # `oracle_result` có thể mang nhiều khoá (khoá văn xuôi làm ghi chú cho
        # người đọc, như `hinh_chieu_la`), và `dev/cases.json §luat_soan` đã
        # phải viết cả một đoạn dặn *"khoá văn xuôi KHÔNG dùng để chấm"*. Một
        # dặn dò bằng văn xuôi thì bộ chấm không đọc được. Trường này biến nó
        # thành thứ máy tra được.
        c["oracle_ref"] = khoa
        c["phep_chuyen"] = (
            f"Đáp án nguồn chép thẳng vào đơn vị checker (`{khoa}`). "
            "Nếu nguồn viết dạng khác (căn thức, số làm tròn) thì bài NGOÀI "
            "ranh giới — xem pool.json.__don_vi_oracle__.")
    if tag in SH.DOI_DOMAIN_CONDITION:
        c["domain_condition"] = ("CẦN NGƯỜI KHAI: thẻ này chỉ đúng dưới một "
                                 "điều kiện miền — xem CAPABILITY_BOUNDARY.")
    return c


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file_lo", help="File văn bản chứa lô đề do người chép")
    p.add_argument("--ghi", action="store_true",
                   help="Ghi vào pool.json. Không có cờ này thì chỉ soi.")
    a = p.parse_args()

    SH = _nap_seal()
    nguoi, bai, loi = phan_tich(
        Path(a.file_lo).read_text(encoding="utf-8"), SH)

    print(f"NGƯỜI CHÉP: {nguoi or '⛔ THIẾU'}")
    print(f"Đọc được {len(bai)} bài\n")
    for b in bai:
        print(f"  [{b['o']}] {b['ma']}  thẻ={b['tag']}")
        print(f"        {b['de'][:90]}…")
        for cb in b["canh_bao"]:
            print(f"        ⚠️  {cb}")

    if loi:
        print(f"\n⛔ {len(loi)} LỖI — không ghi gì:")
        for d in loi:
            print("   ·", d)
        return 2

    cases = [thanh_case(b, nguoi, SH) for b in bai]
    tat_ca_loi = [d for c in cases for d in SH.check_capability_boundary(c)]
    if tat_ca_loi:
        print(f"\n⛔ CỔNG RANH GIỚI NĂNG LỰC từ chối {len(tat_ca_loi)} chỗ:")
        for d in tat_ca_loi:
            print("   ·", d)
        return 2

    print("\n✅ Cả lô qua `check_capability_boundary`")
    if not a.ghi:
        print("   (soi thôi — thêm `--ghi` để ghi vào pool.json)")
        return 0

    d = json.loads(POOL.read_text(encoding="utf-8"))
    co = {c["case_id"] for c in d["cases"]}
    them = [c for c in cases if c["case_id"] not in co]
    d["cases"] += them
    POOL.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"   Đã ghi {len(them)} bài vào {POOL}")
    print("   Chạy tiếp: seal_geometry_holdout.py --seed 0 --chi-kiem-pool")
    print("              holdout_coverage_matrix.py --md …/COVERAGE_MATRIX.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
