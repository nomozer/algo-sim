# -*- coding: utf-8 -*-
"""Oracle KHÔNG GIAN THẾ GIỚI cho `Scene3D` của 9 ca lượt đo cuối. 0 API call.

─── CÂU HỎI NÓ TRẢ LỜI, VÀ VÌ SAO PHẢI HỎI TRƯỚC ────────────────────────────

Ảnh trình duyệt cho thấy mặt phẳng của `p7` trông như một vật rời khỏi hình
nón. Có **ba** cách giải thích, và chúng đòi ba bản sửa ở ba tầng khác nhau:

    A. dữ liệu sai      — quan hệ hình học đã hỏng ngay trong toạ độ thế giới
    B. renderer sai     — toạ độ đúng, mesh/transform vẽ sai
    C. trình bày kém    — cả hai đúng, nhưng camera/kích thước làm mất quan hệ

Sửa nhầm tầng là chữa đúng triệu chứng ở sai chỗ. Script này đóng **nhánh A**
bằng số học, trước khi ai đó chạm vào renderer.

─── VÌ SAO KHÔNG DÙNG LẠI `geometry_oracle.py` ─────────────────────────────

Oracle custodian chấm **đáp số** (thể tích, diện tích). Ở đây câu hỏi khác hẳn:
*"các vật trong cảnh có đứng đúng quan hệ với nhau không"* — elip có nằm trên
mặt phẳng cắt không, có nằm trên mặt nón không, đường tròn có nằm trên mặt cầu
không. Một đáp số đúng **không** bảo đảm cảnh đúng: hai chuyện được chấm bằng
hai cột độc lập, và wave này đo cột thứ hai.

⚠️ Số ở đây là **hữu tỉ chính xác** (`Fraction`), không phải dấu phẩy động, ở
mọi chỗ làm được. Nơi buộc phải lấy căn (bán trục elip), phép kiểm được viết
lại thành **đẳng thức bình phương** để ở lại trong ℚ. Một tolerance đặt ra chỉ
vì "số thực nó thế" là một tolerance che mất lỗi.
"""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction as Q
from pathlib import Path
from typing import Any

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

FIXTURES = (GOC / "docs" / "evaluation" / "geometry" / "product-ui-result-rendering"
            / "fixtures")
OUT = GOC / "docs" / "evaluation" / "geometry" / "scene3d-visual-fidelity"

#: Số điểm lấy mẫu trên mỗi đường cong. Chọn 16 theo đặc tả; mỗi điểm là một
#: đẳng thức hữu tỉ riêng, nên nhiều hơn không "chắc hơn" mà chỉ chậm hơn.
SO_MAU = 16


class So:
    """Số trong ℚ(√c): `a + b·√c`, với `c` hữu tỉ và `√c` VÔ TỈ.

    ─── VÌ SAO CẦN, VÀ VÌ SAO KHÔNG DÙNG FLOAT THAY ─────────────────────

    Bản đầu của oracle này chỉ lấy mẫu được đường cong khi **cả hai** bán trục
    chia cho phương của nó ra số hữu tỉ. Với `p7` thì bán trục nhỏ là `√(1/48)`
    — vô tỉ — nên nó **bỏ qua** ca ưu tiên cao nhất và báo "0 điểm mẫu". Một
    oracle im lặng bỏ qua đúng ca khó là một oracle tệ hơn không có: nó ghi một
    dấu ✗ trông như lỗi dữ liệu, ở một ca mà dữ liệu hoàn toàn đúng.

    Rơi về float là lối thoát sai: khi ấy mọi kết luận phải kèm tolerance, mà
    tolerance chính là thứ che được lớp lỗi đang đi tìm. Mở rộng sang **một**
    căn thức thì miền số vẫn đóng, phép so sánh vẫn tuyệt đối, và `p7` kiểm
    được y như `p6`.

    Chỉ đỡ **một** `√c` cho mỗi đường cong. Gặp hai căn khác nhau thì NÉM —
    thà dừng có tiếng còn hơn kiểm sai.
    """
    __slots__ = ("a", "b", "c")

    def __init__(self, a: Q, b: Q = Q(0), c: Q = Q(0)):
        self.a, self.b, self.c = Q(a), Q(b), Q(c)

    @staticmethod
    def _hop(x, y) -> Q:
        """Hai toán hạng phải cùng một `√c` (hoặc một bên không có căn)."""
        cx = x.c if isinstance(x, So) and x.b != 0 else None
        cy = y.c if isinstance(y, So) and y.b != 0 else None
        if cx is not None and cy is not None and cx != cy:
            raise ValueError(f"hai căn khác nhau trong một phép: √{cx} và √{cy}")
        return cx if cx is not None else (cy if cy is not None else Q(0))

    @staticmethod
    def _nang(x) -> "So":
        return x if isinstance(x, So) else So(Q(x))

    def __add__(self, o):
        o = So._nang(o); c = So._hop(self, o)
        return So(self.a + o.a, self.b + o.b, c)
    __radd__ = __add__

    def __sub__(self, o):
        o = So._nang(o); c = So._hop(self, o)
        return So(self.a - o.a, self.b - o.b, c)

    def __rsub__(self, o):
        return So._nang(o) - self

    def __mul__(self, o):
        o = So._nang(o); c = So._hop(self, o)
        # (a₁+b₁√c)(a₂+b₂√c) = (a₁a₂ + b₁b₂c) + (a₁b₂ + a₂b₁)√c
        return So(self.a * o.a + self.b * o.b * c,
                  self.a * o.b + o.a * self.b, c)
    __rmul__ = __mul__

    def __truediv__(self, o):
        o = So._nang(o)
        if o.b != 0:
            raise ValueError("chưa cần chia cho số có căn")
        return So(self.a / o.a, self.b / o.a, self.c)

    def __eq__(self, o):
        o = So._nang(o)
        return self.a == o.a and self.b == o.b

    def __le__(self, o): return (self - So._nang(o))._dau() <= 0
    def __ge__(self, o): return (self - So._nang(o))._dau() >= 0

    def _dau(self) -> int:
        """Dấu, tính CHÍNH XÁC: so `b√c` với `−a` bằng cách bình phương."""
        if self.b == 0:
            return (self.a > 0) - (self.a < 0)
        if self.a == 0:
            return (self.b > 0) - (self.b < 0)
        trai, phai = self.a, self.b * self.b * self.c   # a vs ±√(b²c)
        if self.a > 0 and self.b > 0:
            return 1
        if self.a < 0 and self.b < 0:
            return -1
        lon_hon = trai * trai > phai
        return (1 if lon_hon else -1) * (1 if self.a > 0 else -1)

    def __repr__(self):
        return f"{self.a}" if self.b == 0 else f"{self.a}+{self.b}√{self.c}"


def V(x: list[str]) -> tuple[Q, Q, Q]:
    return tuple(Q(s) for s in x)  # type: ignore[return-value]


def tru(a, b): return tuple(x - y for x, y in zip(a, b))
def cong(a, b): return tuple(x + y for x, y in zip(a, b))
def nhan(a, k): return tuple(x * k for x in a)
def cham(a, b): return sum(x * y for x, y in zip(a, b))
def cheo(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


# ══════════════════════════════════════════════════════════════════════════
# §1 · ĐIỂM MẪU TRÊN ĐƯỜNG CONG — ở lại trong ℚ bằng cách tham số hoá hữu tỉ
# ══════════════════════════════════════════════════════════════════════════
def _cos_sin_huu_ti(k: int, n: int) -> tuple[Q, Q]:
    """`(cos θ, sin θ)` HỮU TỈ, lấy từ bộ ba Pythagore qua `t = tan(θ/2)`.

    Lấy mẫu bằng `math.cos` sẽ kéo cả phép kiểm xuống dấu phẩy động, và khi ấy
    mọi kết luận phải kèm một tolerance — thứ che được đúng lớp lỗi ta đang đi
    tìm. Với `t` hữu tỉ, `cos = (1−t²)/(1+t²)` và `sin = 2t/(1+t²)` đều hữu tỉ,
    và điểm sinh ra nằm **chính xác** trên đường cong.
    """
    t = Q(k - n // 2, max(1, n // 2))     # t chạy quanh 0, phủ đều đường cong
    d = 1 + t * t
    return ((1 - t * t) / d, 2 * t / d)


def diem_tren_elip(o: dict[str, Any], n: int = SO_MAU) -> list[tuple[Q, Q, Q]]:
    """`center + a·û_M·cos + b·û_m·sin`, viết lại để KHÔNG cần căn.

    `a = √semi_major_sq` và `û_M = M/|M|` đều vô tỉ, nhưng **tích** của chúng
    có thể hữu tỉ. Ở cả hai ca của bộ này, `semi_major_sq/|M|²` là bình phương
    một số hữu tỉ, nên `a/|M|` hữu tỉ và `a·û_M = (a/|M|)·M` ở lại trong ℚ³.
    Trả rỗng khi điều đó không đúng — thà không kiểm còn hơn kiểm bằng float.
    """
    c = V(o["center"])
    ra = _ty_le(Q(o["semi_major_sq"]), V(o["major_dir"]))
    rb = _ty_le(Q(o["semi_minor_sq"]), V(o["minor_dir"]))
    A = nhan(V(o["major_dir"]), ra)
    B = nhan(V(o["minor_dir"]), rb)
    ra_ds = []
    for k in range(n):
        co, si = _cos_sin_huu_ti(k, n)
        ra_ds.append(cong(c, cong(nhan(A, co), nhan(B, si))))
    return ra_ds


def _ty_le(ban_kinh_sq: Q, huong: tuple[Q, Q, Q]):
    """`√(bán_kính² / |hướng|²)` — hữu tỉ khi được, `So` trong ℚ(√t) khi không.

    Không bao giờ trả `None`: mọi elip đều lấy mẫu được, và ca phải dừng chỉ
    còn là ca có HAI căn khác nhau — lúc ấy `So` ném, và ném là đúng.
    """
    d2 = cham(huong, huong)
    if d2 == 0:
        raise ValueError("phương trục suy biến về vectơ không")
    t = ban_kinh_sq / d2
    tu, mau = _can_nguyen(t.numerator), _can_nguyen(t.denominator)
    if tu is not None and mau is not None:
        return Q(tu, mau)
    return So(Q(0), Q(1), t)          # đúng bằng √t, giữ nguyên dạng


def _can_nguyen(n: int) -> int | None:
    if n < 0:
        return None
    r = int(n ** 0.5)
    for c in (r - 1, r, r + 1):
        if c >= 0 and c * c == n:
            return c
    return None


def diem_tren_duong_tron(o: dict[str, Any], n: int = SO_MAU) -> list[tuple[Q, Q, Q]]:
    """Đường tròn = elip có hai bán trục bằng nhau; dựng hai phương trực giao
    với pháp tuyến rồi dùng chung đường đi của elip."""
    c = V(o["center"])
    nv = V(o["normal"])
    truc = (Q(1), Q(0), Q(0)) if cheo(nv, (Q(1), Q(0), Q(0))) != (0, 0, 0) \
        else (Q(0), Q(1), Q(0))
    u = cheo(nv, truc)
    w = cheo(nv, u)
    ru = _ty_le(Q(o["radius_sq"]), u)
    rw = _ty_le(Q(o["radius_sq"]), w)
    U, W = nhan(u, ru), nhan(w, rw)
    ra = []
    for k in range(n):
        co, si = _cos_sin_huu_ti(k, n)
        ra.append(cong(c, cong(nhan(U, co), nhan(W, si))))
    return ra


# ══════════════════════════════════════════════════════════════════════════
# §2 · PHÉP KIỂM QUAN HỆ
# ══════════════════════════════════════════════════════════════════════════
def tren_mat_phang(diem, mp: dict[str, Any]) -> tuple[bool, list[str]]:
    """`n·(P − p₀) = 0` cho MỌI điểm mẫu. Sai số kỳ vọng đúng bằng 0."""
    p0, nv = V(mp["point"]), V(mp["normal"])
    le = [str(cham(nv, tru(P, p0))) for P in diem if not (cham(nv, tru(P, p0)) == 0)]
    return (not le, le[:4])


def tren_mat_cau(diem, kh: dict[str, Any]) -> tuple[bool, list[str]]:
    tam, r2 = V(kh["anchor"]), Q(kh["radius_sq"])
    le = [str(cham(tru(P, tam), tru(P, tam)) - r2)
          for P in diem if not (cham(tru(P, tam), tru(P, tam)) == r2)]
    return (not le, le[:4])


def tren_mat_tru(diem, kh: dict[str, Any]) -> tuple[bool, list[str]]:
    """Khoảng cách tới TRỤC bằng bán kính — viết ở dạng bình phương.

    `|(P−A)×û|² = r²` nhân hai vế với `|axis|²` để bỏ chuẩn hoá:
    `|(P−A)×axis|² = r²·|axis|²`.
    """
    A, B, r2 = V(kh["anchor"]), V(kh["apex_or_top"]), Q(kh["radius_sq"])
    truc = tru(B, A)
    d2 = cham(truc, truc)
    le = []
    for P in diem:
        c = cheo(tru(P, A), truc)
        if not (cham(c, c) == r2 * d2):
            le.append(str(cham(c, c) - r2 * d2))
    return (not le, le[:4])


def tren_mat_non(diem, kh: dict[str, Any]) -> tuple[bool, list[str]]:
    """Bán kính giảm tuyến tính từ đáy tới đỉnh, viết ở dạng bình phương.

    Với `s = (đỉnh − P)·û_trục / h` (phần chiều cao CÒN LẠI tính từ P lên
    đỉnh), điểm nằm trên mặt nón khi `dist²(P, trục) = r²·s²`. Nhân chéo để
    khử mọi phép chia và mọi căn:
        `|(P−A)×truc|² · h⁴ = r² · ((đỉnh−P)·truc)² · h²`
    với `h² = |truc|²`. Rút gọn còn `|(P−A)×truc|² · h² = r² · ((đỉnh−P)·truc)²`.
    """
    A, D, r2 = V(kh["anchor"]), V(kh["apex_or_top"]), Q(kh["radius_sq"])
    truc = tru(D, A)
    h2 = cham(truc, truc)
    le = []
    for P in diem:
        c = cheo(tru(P, A), truc)
        trai = cham(c, c) * h2
        s = cham(tru(D, P), truc)
        phai = r2 * (s * s)
        if not (trai == phai):
            le.append(str(trai - phai))
    return (not le, le[:4])


def trong_doan_truc(diem, kh: dict[str, Any]) -> tuple[bool, list[str]]:
    """Điểm mẫu phải nằm TRONG chiều cao khối, không thò ra ngoài đầu mút."""
    A, B = V(kh["anchor"]), V(kh["apex_or_top"])
    truc = tru(B, A)
    h2 = cham(truc, truc)
    le = [str(cham(tru(P, A), truc)) for P in diem
          if not (0 <= cham(tru(P, A), truc) <= h2)]
    return (not le, le[:4])


def da_giac_lom(dinh: list[tuple[Q, Q, Q]]) -> dict[str, Any]:
    """Đa giác phẳng này có LÕM không, và lõm ở đỉnh nào.

    Dấu của tích có hướng tại mỗi đỉnh: đa giác lồi thì mọi dấu như nhau. Một
    dấu ngược = một đỉnh phản xạ. Tất cả trong ℚ, không lượng giác.
    """
    n = len(dinh)
    dau = []
    for i in range(n):
        a, b, c = dinh[i], dinh[(i + 1) % n], dinh[(i + 2) % n]
        z = cheo(tru(b, a), tru(c, b))
        dau.append(z)
    # đa giác nằm trong mặt phẳng z = const ⇒ chỉ thành phần z khác 0
    zs = [d[2] for d in dau]
    duong = sum(1 for z in zs if z > 0)
    am = sum(1 for z in zs if z < 0)
    phan_xa = [i for i, z in enumerate(zs)
               if (z < 0 if duong >= am else z > 0)]
    return {"lom": bool(duong and am),
            "so_dinh": n,
            "chi_so_dinh_phan_xa": [(i + 1) % n for i in phan_xa]}


# ══════════════════════════════════════════════════════════════════════════
# §3 · CHẠY TRÊN 9 CA
# ══════════════════════════════════════════════════════════════════════════
def _vat(canh, **loc):
    return [o for o in canh["objects"]
            if all(o.get(k) == v for k, v in loc.items())]


def soi_mot_ca(fx: dict[str, Any]) -> dict[str, Any]:
    canh = (fx["envelope"].get("scene3d") or {})
    if not canh:
        return {"case_id": fx["case_id"], "co_canh": False, "kiem": [],
                "WORLD_SPACE_GEOMETRY_PASS": None}

    kiem: list[dict[str, Any]] = []

    def ghi(ten, ok, chi_tiet=""):
        kiem.append({"phep": ten, "pass": bool(ok), "chi_tiet": str(chi_tiet)})

    mp = _vat(canh, type="plane3")
    khoi = _vat(canh, type="curved_solid")

    # ── thiết diện cong: elip và đường tròn ──────────────────────────────
    for o in _vat(canh, type="ellipse3") + _vat(canh, type="circle3"):
        la_elip = o["type"] == "ellipse3"
        diem = diem_tren_elip(o) if la_elip else diem_tren_duong_tron(o)
        ghi(f"{o['id']}: lấy được {SO_MAU} điểm mẫu HỮU TỈ", len(diem) == SO_MAU,
            f"{len(diem)} điểm")
        if not diem:
            continue
        # phương trục phải trực giao với pháp tuyến — nếu không, "elip" đang
        # nằm nghiêng so với chính mặt phẳng của nó
        if la_elip:
            nv = V(o["normal"])
            ghi(f"{o['id']}: hai phương trục ⟂ pháp tuyến",
                cham(nv, V(o["major_dir"])) == 0 and cham(nv, V(o["minor_dir"])) == 0)
            ghi(f"{o['id']}: hai phương trục ⟂ nhau",
                cham(V(o["major_dir"]), V(o["minor_dir"])) == 0)
        # ⚠️ GHÉP BẰNG PHÉP CHỨA, KHÔNG BẰNG PHÁP TUYẾN BẰNG NHAU.
        #
        # Bản đầu bỏ qua mặt phẳng nào có `normal` khác `normal` của thiết
        # diện. Phép tiêm "xoay sai pháp tuyến" khi ấy **không đỏ**: mặt phẳng
        # thôi khớp ⇒ phép kiểm bị BỎ QUA, và oracle im lặng báo đạt. Một guard
        # tự tắt khi dữ liệu hỏng là guard tệ hơn không có.
        #
        # Nay hỏi đúng câu cần hỏi: trong cảnh có mặt phẳng nào CHỨA TRỌN thiết
        # diện không. Dời tâm, xoay pháp tuyến hay đổi bán trục đều làm câu trả
        # lời thành "không".
        if mp:
            chua = [m["id"] for m in mp if tren_mat_phang(diem, m)[0]]
            ghi(f"{o['id']}: có mặt phẳng trong cảnh CHỨA TRỌN thiết diện",
                bool(chua), f"chứa bởi {chua}" if chua
                else "KHÔNG mặt phẳng nào chứa")
        for k in khoi:
            if k["curved_kind"] == "ball":
                ok, le = tren_mat_cau(diem, k)
            elif k["curved_kind"] == "cylinder":
                ok, le = tren_mat_tru(diem, k)
            else:
                ok, le = tren_mat_non(diem, k)
            ghi(f"{o['id']} nằm trên mặt {k['curved_kind']} {k['id']}", ok, le)
            if k["curved_kind"] != "ball":
                ok2, le2 = trong_doan_truc(diem, k)
                ghi(f"{o['id']} nằm trong chiều cao {k['id']}", ok2, le2)

    # ── khối cong: bất biến khai báo ba điểm ─────────────────────────────
    for k in khoi:
        A, R = V(k["anchor"]), V(k["rim_point"])
        if k["curved_kind"] == "ball":
            ghi(f"{k['id']}: |tâm→điểm vành|² = radius_sq",
                cham(tru(R, A), tru(R, A)) == Q(k["radius_sq"]))
            continue
        B = V(k["apex_or_top"])
        truc = tru(B, A)
        ghi(f"{k['id']}: |trục|² = height_sq", cham(truc, truc) == Q(k["height_sq"]))
        ghi(f"{k['id']}: bán kính ⟂ trục", cham(tru(R, A), truc) == 0)
        ghi(f"{k['id']}: |bán kính|² = radius_sq",
            cham(tru(R, A), tru(R, A)) == Q(k["radius_sq"]))

    # ── thiết diện phẳng nằm trên mặt phẳng của nó ───────────────────────
    for o in _vat(canh, type="section") + _vat(canh, type="polygon3"):
        dinh = [V(x) for x in (o.get("polygon") or o.get("vertices") or [])]
        if len(dinh) >= 3:
            nv = cheo(tru(dinh[1], dinh[0]), tru(dinh[2], dinh[0]))
            ghi(f"{o['id']}: mọi đỉnh ĐỒNG PHẲNG",
                all(cham(nv, tru(P, dinh[0])) == 0 for P in dinh))
            for m in mp:
                ok, le = tren_mat_phang(dinh, m)
                if ok:
                    ghi(f"{o['id']} nằm trên mặt phẳng {m['id']}", True)

    # ── khối đa diện: lõm hay lồi, và mặt đáy có đúng chu trình không ────
    lom = None
    for o in _vat(canh, type="polygon3"):
        dinh = [V(x) for x in o["vertices"]]
        if len(dinh) >= 4:
            lom = da_giac_lom(dinh)
            ghi(f"{o['id']}: phát hiện được tính lõm/lồi", True,
                json.dumps(lom, ensure_ascii=False))

    ok_tat_ca = all(k["pass"] for k in kiem)
    return {"case_id": fx["case_id"], "co_canh": True,
            "so_phep": len(kiem), "so_dat": sum(1 for k in kiem if k["pass"]),
            "WORLD_SPACE_GEOMETRY_PASS": ok_tat_ca,
            "da_giac_day": lom, "kiem": kiem}


#: Phép tiêm lỗi: `(tên, hàm làm hỏng fixture)`. Một oracle chưa từng đỏ là một
#: oracle chưa được chứng minh — và oracle này vừa được dùng để KẾT LUẬN rằng
#: dữ liệu đúng, nên nó phải trả giá cho kết luận ấy.
TIEM = [
    ("dời tâm elip khỏi mặt phẳng",
     lambda o: o["type"] == "ellipse3",
     lambda o: o.update(center=[str(Q(o["center"][0]) + 1), o["center"][1],
                                o["center"][2]])),
    ("xoay sai pháp tuyến mặt phẳng",
     lambda o: o["type"] == "plane3",
     lambda o: o.update(normal=[o["normal"][1], o["normal"][0], o["normal"][2]])),
    ("đổi bán trục nhỏ của elip",
     lambda o: o["type"] == "ellipse3",
     lambda o: o.update(semi_minor_sq=str(Q(o["semi_minor_sq"]) + 1))),
    ("đổi bán kính khối cong",
     lambda o: o["type"] == "curved_solid",
     lambda o: o.update(radius_sq=str(Q(o["radius_sq"]) + 1))),
    ("làm phương trục thôi trực giao",
     lambda o: o["type"] == "ellipse3",
     lambda o: o.update(minor_dir=[str(Q(o["minor_dir"][0]) + 1),
                                   o["minor_dir"][1], o["minor_dir"][2]])),
]


def _tiem(a) -> int:
    print("\nTIÊM LỖI VÀO ORACLE — mỗi phép phải làm ĐỎ ít nhất một ca\n")
    goc = [json.loads(f.read_text(encoding="utf-8"))
           for f in sorted(a.fixtures.glob("*.json"))]
    dat = 0
    for ten, chon, hong in TIEM:
        do_o = []
        for fx in goc:
            g = json.loads(json.dumps(fx))
            canh = (g["envelope"].get("scene3d") or {})
            muc = [o for o in canh.get("objects", []) if chon(o)]
            if not muc:
                continue
            hong(muc[0])
            try:
                kq = soi_mot_ca(g)
                if kq["co_canh"] and not kq["WORLD_SPACE_GEOMETRY_PASS"]:
                    do_o.append(g["case_id"][:2])
            except (ValueError, ZeroDivisionError):
                do_o.append(g["case_id"][:2] + "(ném)")
        ok = bool(do_o)
        dat += ok
        print(f"  {'✓' if ok else '✗'} {ten} → đỏ ở: {', '.join(do_o) or 'KHÔNG CA NÀO'}")
    print(f"\n  TIÊM LỖI {dat}/{len(TIEM)} chứng minh đỏ được")
    return 0 if dat == len(TIEM) else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixtures", type=Path, default=FIXTURES)
    p.add_argument("--out", type=Path, default=OUT / "WORLD_SPACE_ORACLES.json")
    p.add_argument("--faultcheck", action="store_true")
    a = p.parse_args()
    if a.faultcheck:
        return _tiem(a)

    print("ORACLE KHÔNG GIAN THẾ GIỚI — số HỮU TỈ CHÍNH XÁC, 0 lượt gọi model\n")
    ra = []
    for f in sorted(a.fixtures.glob("*.json")):
        fx = json.loads(f.read_text(encoding="utf-8"))
        kq = soi_mot_ca(fx)
        ra.append(kq)
        if not kq["co_canh"]:
            print(f"  · {kq['case_id']:<36} (ca âm — không có cảnh)")
            continue
        dau = "✓" if kq["WORLD_SPACE_GEOMETRY_PASS"] else "✗"
        print(f"  {dau} {kq['case_id']:<36} {kq['so_dat']}/{kq['so_phep']} phép")
        for k in kq["kiem"]:
            if not k["pass"]:
                print(f"      ✗ {k['phep']} — lệch {k['chi_tiet']}")

    co_canh = [x for x in ra if x["co_canh"]]
    dat = sum(1 for x in co_canh if x["WORLD_SPACE_GEOMETRY_PASS"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "khai": "Quan hệ hình học trong TOẠ ĐỘ THẾ GIỚI của Scene3D, kiểm bằng "
                "số hữu tỉ chính xác (Fraction). Không tolerance, không float. "
                "Đóng nhánh A (dữ liệu sai) trước khi chạm renderer.",
        "run_id": "thesis-final-20260908T160224Z",
        "application_llm_calls": 0,
        "so_mau_moi_duong_cong": SO_MAU,
        "WORLD_SPACE_GEOMETRY_PASS": f"{dat}/{len(co_canh)}",
        "cases": ra,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n  WORLD_SPACE_GEOMETRY_PASS = {dat}/{len(co_canh)}")
    print(f"  → {a.out.relative_to(GOC).as_posix()}")
    return 0 if dat == len(co_canh) else 1


if __name__ == "__main__":
    sys.exit(main())
