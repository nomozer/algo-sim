# -*- coding: utf-8 -*-
"""Thu ỨNG VIÊN đề held-out từ HTML thô. **0 API call của hệ.**

    python scripts/harvest_holdout_candidates.py --sitemap https://…/sitemap.xml
    python scripts/harvest_holdout_candidates.py --urls danh-sach.txt --out-dir /tmp/thu

Ra `ung_vien.json` + một bảng thống kê. **KHÔNG ghi vào `pool.json`** — nó chỉ
đặt đề lên bàn; việc nhận hay loại vẫn là của người, và `problem_text_verified`
vẫn phải do người hạ.

─── VÌ SAO CÓ FILE NÀY: HAI KÊNH TRƯỚC ĐỀU HỎNG, VÀ HỎNG IM LẶNG ─────────

Giao thức đòi `problem_text` **NGUYÊN VĂN**. Đã thử và đo:

    công cụ đọc web   → nội dung đi qua một mô hình TÓM TẮT
    trích PDF tự động → rơi ký hiệu toán. Đo trên một chuyên đề 217 trang về
                        QUAN HỆ VUÔNG GÓC: `⊥` xuất hiện ĐÚNG 0 LẦN
                        (√ 0 · ∈ 0 · ∥ 0), trong khi `=` còn 1303.
                        Hai thư viện độc lập (pymupdf, pypdf) cùng kết quả.

Cả hai cho ra văn bản **vẫn đọc như một đề bài** — đó là chỗ nguy hiểm: đề mất
một ký hiệu là một **bài toán khác**, và không ai nhận ra khi đọc lướt.

Kênh ở đây khác về **bản chất**, không phải về chất lượng: `curl` trả **byte
gốc**, và toán nằm sẵn trong HTML dưới dạng LaTeX (`\\(ABCD.MNPQ\\)`). Không có
bước nào diễn giải lại, nên không có bước nào làm mất thông tin.

─── BA CỔNG TRUNG THỰC — thà bỏ sót còn hơn nhận nhầm ────────────────────

    ① có khối ĐỀ BÀI tách được   — không có thì đang đoán đâu là đề
    ② KHÔNG có <img> trong khối  — toán vẽ thành ảnh thì `curl` cũng chịu
    ③ có dấu vết LaTeX           — không có thì hoặc đề không chứa toán,
                                    hoặc toán đã bị mất ở đâu đó

Cổng ② quan trọng nhất và là lý do sản lượng thấp: phần lớn nội dung toán trên
web tiếng Việt là **ảnh chụp**.

─── SẢN LƯỢNG ĐO ĐƯỢC (mathvn.com, 2026-08-27) ───────────────────────────

    3883 url → lọc từ khoá → 60 ứng viên → 11 có khối đề → 2 sạch → 0 trong
    ranh giới năng lực.

Kênh **đúng**, nguồn **cạn**: khuôn `math-box` chỉ có ở một nhúm bài 2026.
Con số ấy là lý do nên chạy script này trên **nhiều site**, và là lý do đường
găng vẫn là **người chép đề**.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent

#: Từ khoá lọc url — hình học không gian THPT.
TU_KHOA = ("hinh-chop", "lang-tru", "lap-phuong", "thiet-dien", "the-tich",
           "goc-giua", "khoang-cach", "vuong-goc", "song-song", "giao-tuyen",
           "hinh-hoc-khong-gian", "tu-dien", "hinh-hop")

#: Dấu vết LaTeX. Có ít nhất một cái ⇒ toán còn nguyên trong HTML.
LATEX = re.compile(r"\\\(|\\\[|\\frac|\\sqrt|\\perp|\\parallel|\\in\b|\$\$")

#: Nhan đề khối đề bài. Thêm khuôn mới thì thêm ở đây, đừng đoán bằng vị trí.
_KHOI_DE = (
    re.compile(r"<h[1-6][^>]*>\s*Đề bài\s*</h[1-6]>(.*?)<h[1-6]", re.S | re.I),
    re.compile(r'<div class="math-box">(.*?)</div>', re.S),
)


def _curl(u: str, f: Path) -> str:
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists() or f.stat().st_size < 1000:
        subprocess.run(["curl", "-sSL", "-A", "Mozilla/5.0", "--max-time", "45",
                        u, "-o", str(f)], capture_output=True)
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""


def go_the(x: str) -> str:
    """Bỏ thẻ HTML, GIỮ nguyên LaTeX. Không chuẩn hoá gì thêm — chuẩn hoá là
    diễn giải, và diễn giải là chỗ thông tin bị mất."""
    x = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", x, flags=re.S | re.I)
    x = re.sub(r"<[^>]+>", " ", x)
    return re.sub(r"\s+", " ", html.unescape(x)).strip()


def tach_khoi_de(trang: str) -> str | None:
    for r in _KHOI_DE:
        if (m := r.search(trang)):
            return m.group(1)
    return None


def soi_mot_trang(u: str, trang: str) -> dict | None:
    khoi = tach_khoi_de(trang)
    if khoi is None:
        return None
    de = go_the(khoi)
    if len(de) < 60:
        return None
    tm = re.search(r"<title>(.*?)</title>", trang, re.S)
    co_anh = bool(re.search(r"<img", khoi, re.I))
    co_latex = bool(LATEX.search(khoi))
    return {
        "url": u,
        "title": go_the(tm.group(1)) if tm else "",
        "co_anh_trong_de": co_anh,
        "co_latex": co_latex,
        # SẠCH = qua cả ba cổng. Chỉ bài sạch mới đáng cho người đọc soát.
        "sach": (not co_anh) and co_latex,
        "problem_text_original": de[:1500],
    }


def _url_tu_sitemap(sm: str, thu_muc: Path) -> list[str]:
    goc = _curl(sm, thu_muc / "sitemap-0.xml")
    trang = re.findall(r"<loc>([^<]+)</loc>", goc)
    tat = []
    for i, t in enumerate(trang if trang else [sm], 1):
        x = _curl(t, thu_muc / f"sitemap-{i}.xml") if t != sm else goc
        tat += re.findall(r"<loc>([^<]+)</loc>", x)
    return sorted({u for u in tat if any(k in u.lower() for k in TU_KHOA)})


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sitemap", help="Sitemap để liệt kê url rồi lọc theo TU_KHOA")
    p.add_argument("--urls", help="File danh sách url, mỗi dòng một url")
    p.add_argument("--out-dir", default=None, help="Thư mục làm việc (mặc định: tạm)")
    a = p.parse_args()
    if not (a.sitemap or a.urls):
        print("Cần --sitemap hoặc --urls.")
        return 2

    d = Path(a.out_dir) if a.out_dir else GOC / ".harvest"
    d.mkdir(parents=True, exist_ok=True)
    urls = ([u.strip() for u in Path(a.urls).read_text(encoding="utf-8").splitlines()
             if u.strip()] if a.urls else _url_tu_sitemap(a.sitemap, d))
    print(f"{len(urls)} url ứng viên\n")

    ra = []
    for i, u in enumerate(urls, 1):
        ten = re.sub(r"[^a-z0-9]+", "-", u.split("/")[-1].lower())[:80] + ".html"
        trang = _curl(u, d / "pages" / ten)
        if not trang:
            continue
        if (x := soi_mot_trang(u, trang)):
            ra.append(x)
            dau = "SẠCH" if x["sach"] else ("ẢNH " if x["co_anh_trong_de"] else "?LTX")
            print(f"[{i}/{len(urls)}] {dau} {u.split('/')[-1][:55]}")

    (d / "ung_vien.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    sach = [x for x in ra if x["sach"]]
    print(f"\n── {len(urls)} url → {len(ra)} có khối đề → {len(sach)} SẠCH ──")
    print(f"   loại vì đề là ẢNH : {sum(1 for x in ra if x['co_anh_trong_de'])}")
    print(f"   loại vì không LaTeX: {sum(1 for x in ra if not x['co_latex'])}")
    print(f"\nGhi {d / 'ung_vien.json'}")
    print("⚠️  ĐÂY LÀ ỨNG VIÊN, KHÔNG PHẢI POOL. Người vẫn phải: đọc soát đề,")
    print("   đối chiếu ranh giới năng lực, rồi mới hạ `problem_text_verified`.")
    return 0 if sach else 1


if __name__ == "__main__":
    raise SystemExit(main())
