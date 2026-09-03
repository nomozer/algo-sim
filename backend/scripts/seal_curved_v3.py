# -*- coding: utf-8 -*-
"""Niêm phong pool V3 hình cong, và rút tập đo bằng SEED TỪ NGOÀI. **0 API call.**

    python scripts/seal_curved_v3.py --niem-phong          # đóng băng pool
    python scripts/seal_curved_v3.py --rut --seed <SỐ>     # rút tập đo

─── VÌ SAO POOL PHẢI ĐÓNG BĂNG TRƯỚC KHI CÓ SEED ──────────────────────────

Tôi đã đọc toàn bộ 8 ca hỏng của V1 và V2 trước khi soạn pool này. Nên tôi
**không độc lập** với nó: biết mô hình hay bịa điểm phụ, tôi soạn được một tập
đề né đúng chỗ ấy, hoặc nhắm thẳng vào nó — cả hai đều cho một con số không nói
gì về năng lực. `HOLDOUT_PROTOCOL §5②` xử đúng chuyện này: người soạn pool
KHÔNG được là người chọn seed.

Nên hai bước tách hẳn: pool đóng băng và băm **trước**, seed đọc **sau**. Băm
pool nằm trong con dấu, nên "pool không sửa sau khi biết seed" là thứ kiểm được
chứ không phải lời hứa.

Script này **không có seed mặc định** — thiếu là dừng, không tự sinh.

─── PHÂN TẦNG THEO Ô ──────────────────────────────────────────────────────

Rút một bài mỗi Ô. Seed quyết định *bài nào trong ô*, không quyết định *ô nào
có mặt* — cùng lý do `seal_geometry_holdout.py` bỏ lối rút theo tỉ lệ: 13 bài
rút ngẫu nhiên có thể ra 13 bài thể tích khối cầu.

Bốn ô `N*` là **từ chối**, chấm bằng thang khác: gặp đề ngoài khả năng, hệ nói
thẳng hay bịa một hình gần giống? Không gộp với chín ô dương.

─── KỲ VỌNG DO SCRIPT TÍNH LẠI, KHÔNG DO NGƯỜI GÕ ─────────────────────────

Mỗi bài khai `cong_thuc` + tham số; script tính lại `mong` và **từ chối niêm
phong** nếu lệch. Gõ tay 26 đáp số thì sẽ có đáp số sai, và một kỳ vọng sai
biến thành "mô hình hỏng" trong báo cáo — lỗi tệ nhất một bộ đo có thể mắc.

Phép tính ở đây dùng `Fraction` + căn nguyên, **độc lập với nhân hình học** của
sản phẩm: nó đi từ công thức SGK, không gọi `geometry/`. Trùng kết quả là hai
đường khác nhau gặp nhau, không phải một đường tự soi gương.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from fractions import Fraction
from math import isqrt
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

THU_MUC = BACKEND.parent / "docs" / "evaluation" / "geometry" / "curved-v3"
POOL = THU_MUC / "POOL.json"
DAU = THU_MUC / "V3_SEAL.json"


# ══ Số chính xác đủ dùng cho công thức SGK ═══════════════════════════════
#
# Dạng: `he * √can * π^mu`, `he` hữu tỉ. Đúng miền mà `radical.py` biểu diễn
# được — nhưng cài LẠI ở đây, cố ý. Dùng `radical.py` để sinh kỳ vọng rồi so
# với kết quả cũng do `radical.py` tính là kiểm tra chính nó.
class So:
    __slots__ = ("he", "can", "mu")

    def __init__(self, he: Fraction | int, can: int = 1, mu: int = 0):
        assert can >= 1 and mu in (0, 1)
        self.he, self.can, self.mu = Fraction(he), can, mu

    def __mul__(self, o: "So | int | Fraction") -> "So":
        o = o if isinstance(o, So) else So(o)
        assert self.mu + o.mu <= 1, "π² ngoài miền"
        can, he = self.can * o.can, self.he * o.he
        # rút thừa số chính phương ra ngoài dấu căn
        d = 2
        while d * d <= can:
            while can % (d * d) == 0:
                can //= d * d
                he *= d
            d += 1
        return So(he, can, self.mu + o.mu)

    __rmul__ = __mul__

    def __str__(self) -> str:
        if self.can == 1 and self.mu == 0:
            return str(self.he) if self.he.denominator > 1 else str(self.he.numerator)
        t = ""
        if self.he != 1 or (self.can == 1 and self.mu == 0):
            t += (str(self.he) if self.he.denominator > 1
                  else str(self.he.numerator)) if self.he != 1 else ""
        if self.mu:
            t += "π"
        if self.can != 1:
            t += f"√{self.can}"
        return t or "1"


def _can(x: Fraction | int) -> So:
    """√x cho x hữu tỉ ⇒ dạng `he√can`. Chỉ nhận x làm được chính xác."""
    x = Fraction(x)
    a, b = x.numerator, x.denominator
    # √(a/b) = √(a·b)/b
    ab = a * b
    r = isqrt(ab)
    goc, he = ab, Fraction(1, b)
    if r * r == ab:
        return So(Fraction(r, b))
    d = 2
    while d * d <= goc:
        while goc % (d * d) == 0:
            goc //= d * d
            he *= d
        d += 1
    return So(he, goc)


PI = So(1, 1, 1)

# ══ Công thức SGK — MỘT nơi, dùng cho cả 26 bài ══════════════════════════
CONG_THUC = {
    "the_tich_cau":       lambda R: So(Fraction(4, 3)) * PI * So(R ** 3),
    "dien_tich_mat_cau":  lambda R: So(4) * PI * So(R ** 2),
    "dien_tich_hinh_tron": lambda r: PI * So(Fraction(r) ** 2),
    # đường tròn giao của mặt phẳng cách tâm d: r = √(R² − d²)
    "ban_kinh_thiet_dien_cau": lambda R, d: _can(R ** 2 - d ** 2),
    "the_tich_tru":       lambda r, h: PI * So(Fraction(r) ** 2) * So(h),
    "xung_quanh_tru":     lambda r, h: So(2) * PI * So(r) * So(h),
    # thiết diện qua trục của trụ: chữ nhật 2r × h
    "thiet_dien_truc_tru": lambda r, h: So(2 * Fraction(r) * h),
    # mặt phẳng ⊥ trục trụ ⇒ đường tròn bán kính ĐÚNG BẰNG bán kính đáy. Ô
    # C5 từng mượn `ban_kinh_thiet_dien_cau` với d=0 — ra đúng số, nhưng khai
    # sai lý do, và một bộ đo khai sai lý do thì lần sau sửa nó sẽ sai số.
    "ban_kinh_lat_cat_tru": lambda r: So(r),
    "the_tich_non":       lambda r, h: So(Fraction(1, 3)) * PI * So(Fraction(r) ** 2) * So(h),
    "duong_sinh_non":     lambda r, h: _can(Fraction(r) ** 2 + Fraction(h) ** 2),
    "xung_quanh_non":     lambda r, l: PI * So(r) * So(l),
    # thiết diện qua trục của nón: tam giác cân đáy 2r, cao h ⇒ S = r·h
    "thiet_dien_truc_non": lambda r, h: So(Fraction(r) * h),
    # mặt phẳng ⊥ trục nón, cách ĐỈNH một khoảng d ⇒ r′ = r·d/h (đồng dạng)
    "ban_kinh_lat_cat_non": lambda r, h, d: So(Fraction(r) * Fraction(d, h)),
    # tứ diện vuông tại O, ba cạnh a,b,c ⇒ R = √(a²+b²+c²)/2
    "ngoai_tiep_vuong_goc": lambda a, b, c: _can(
        Fraction(a ** 2 + b ** 2 + c ** 2, 4)),
}


def _tinh(ct: dict) -> list[str]:
    ra = []
    for ten, tham in ct.items():
        ra.append(str(CONG_THUC[ten](**tham)))
    return ra


def _bam(x) -> str:
    return hashlib.sha256(
        json.dumps(x, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _he_thong() -> tuple[str, int]:
    import freeze_evaluation_candidate as F

    return F.measured_system_hash()


def _nap() -> list[dict]:
    if not POOL.exists():
        sys.exit(f"DỪNG: chưa có {POOL}")
    return json.loads(POOL.read_text(encoding="utf-8"))["bai"]


def _kiem(bai: list[dict]) -> None:
    """Kỳ vọng phải khớp công thức. Lệch ⇒ KHÔNG niêm phong."""
    loi = []
    for b in bai:
        if b["loai"] == "am":
            if b["mong"]:
                loi.append(f"{b['id']}: ca ÂM không được có `mong`")
            continue
        tinh = sorted(_tinh(b["cong_thuc"]))
        if tinh != sorted(b["mong"]):
            loi.append(f"{b['id']}: khai {sorted(b['mong'])} · công thức cho {tinh}")
    ids = [b["id"] for b in bai]
    if len(set(ids)) != len(ids):
        loi.append("id trùng")
    if loi:
        sys.exit("DỪNG — pool KHÔNG nhất quán:\n  " + "\n  ".join(loi))


def _niem_phong() -> int:
    bai = _nap()
    _kiem(bai)
    o = sorted({b["o"] for b in bai})
    thieu = [x for x in o if sum(1 for b in bai if b["o"] == x) < 2]
    if thieu:
        sys.exit(f"DỪNG: ô chỉ có 1 bài ⇒ seed không chọn được gì: {thieu}")
    he, n_file = _he_thong()
    dau = {
        "khai": "POOL V3 hình cong đã đóng băng. Rút bằng `--rut --seed <SỐ>`; "
                "seed phải đến từ người KHÔNG soạn pool này. Sửa pool sau khi "
                "biết seed ⇒ `pool_hash` lệch ⇒ phát hiện được.",
        "niem_phong_luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pool_hash": _bam(bai),
        "pool_size": len(bai),
        "o": o,
        "o_duong": [x for x in o if not x.startswith("N")],
        "o_am": [x for x in o if x.startswith("N")],
        "measured_system_hash": he,
        "measured_system_files": n_file,
        "seed": None,
        "da_rut": None,
        "ghi_chu_doc_lap":
            "⚠️ Pool do CHÍNH TÔI soạn sau khi đọc hết 8 ca hỏng của V1+V2. "
            "Tính độc lập ở đây KHÔNG đến từ người soạn, mà từ hai thứ kiểm "
            "được: pool băm trước khi có seed, và seed do người khác chọn. "
            "Nếu seed cũng do tôi chọn thì phải khai, và con số mất một bậc "
            "giá trị.",
    }
    THU_MUC.mkdir(parents=True, exist_ok=True)
    DAU.write_text(json.dumps(dau, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"→ {DAU}")
    print(f"  pool            {len(bai)} bài · {len(o)} ô · {dau['pool_hash'][:16]}…")
    print(f"  hệ được đo      {n_file} file · {he[:16]}…")
    print(f"  ô dương / âm    {len(dau['o_duong'])} / {len(dau['o_am'])}")
    print("  seed            CHƯA CÓ — cần người ngoài")
    return 0


def _rut(seed: int) -> int:
    if not DAU.exists():
        sys.exit("DỪNG: chưa niêm phong pool")
    dau = json.loads(DAU.read_text(encoding="utf-8"))
    bai = _nap()
    if _bam(bai) != dau["pool_hash"]:
        sys.exit("DỪNG: pool ĐÃ TRÔI khỏi con dấu — băm lệch")
    he, _ = _he_thong()
    if he != dau["measured_system_hash"]:
        sys.exit("DỪNG: hệ đã đổi sau khi niêm phong — niêm phong lại trước")
    if dau.get("seed") is not None:
        sys.exit(f"DỪNG: đã rút bằng seed {dau['seed']} — không rút lần hai")

    rng = random.Random(seed)
    chon = [rng.choice(sorted([b for b in bai if b["o"] == x],
                              key=lambda b: b["id"]))["id"]
            for x in dau["o"]]
    dau["seed"], dau["da_rut"] = seed, chon
    dau["rut_luc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    dau["case_set_hash"] = _bam([b for b in bai if b["id"] in set(chon)])
    DAU.write_text(json.dumps(dau, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"→ {DAU}\n  seed {seed} · {len(chon)} bài\n  " + "\n  ".join(chon))
    print(f"\n  CASE_SET_HASH  {dau['case_set_hash'][:16]}…")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--niem-phong", action="store_true")
    p.add_argument("--rut", action="store_true")
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args()
    if a.niem_phong:
        return _niem_phong()
    if a.rut:
        if a.seed is None:
            sys.exit("DỪNG: `--rut` cần `--seed`. Script KHÔNG tự sinh seed — "
                     "xem phần đầu file.")
        return _rut(a.seed)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
