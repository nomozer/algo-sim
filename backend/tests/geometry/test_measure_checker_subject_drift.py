# -*- coding: utf-8 -*-
"""CỔNG CHỐNG TRÔI: bộ kiểm phải nhận đúng những chủ thể mà hợp đồng cho phép.

    `VOLUME_VERIFICATION_BRIDGE` §11, 2026-09-03. **0 lượt gọi model.**

─── VÌ SAO CẦN MỘT CỔNG, KHÔNG PHẢI THÊM MỘT CA THỬ ───────────────────────

Cùng một hình lỗi đã xảy ra **hai lần trong bốn ngày**, và lần thứ hai do chính
người vừa sửa lần thứ nhất gây ra:

    RADIUS_OBLIGATION_COVERAGE    mở `radius` ở cổng phủ, không có checker
      → RADIUS_VERIFICATION_BRIDGE  vá `radius` … và không soát dòng `volume`
    CURVED_OBLIGATION_COVERAGE    nới `volume` sang `curved_solid` ở cổng phủ
      → check_volume vẫn đòi `Polyhedron`  →  ball_1: đúng đáp số, servable=False

Một ca thử cho `volume`/`curved_solid` chỉ chặn được **lần này**. Cái chặn được
lần sau là một bất biến duyệt HẾT bảng, và nó phải tự thấy dòng mới mà không ai
đăng ký gì thêm.

─── BẤT BIẾN ──────────────────────────────────────────────────────────────

    Với MỌI nghĩa vụ ĐO đang có checker server-owned:
    đường kiểm chứng của checker ấy phải NHẬN mọi kiểu chủ thể mà
    `BANG_PHEP_DO` cho phép cho (các) lượng đo tương ứng
    — trừ ngoại lệ kiến trúc được KHAI TƯỜNG MINH ở `NGOAI_LE`.

⚠️ Bất biến này **KHÔNG** nói *"mọi lượng đo trong `BANG_PHEP_DO` phải có
checker"*. Câu ấy sẽ đẻ ra nghĩa vụ giả: `lateral_area` và `area` cố ý chưa có
checker, và ép chúng có là mở tuyên bố năng lực không ai xin (§13).

─── ĐO "NHẬN" NHƯ THẾ NÀO ─────────────────────────────────────────────────

Không hỏi *"checker có trả `None` không"* — với chủ thể sai kiểu, phần lớn
checker trả `None` khi nghĩa vụ **không khai giá trị** (mức yếu), nên phép thử
ấy XANH GIẢ. Thay vào đó đưa một nhân chứng **cố tình sai** và đòi checker trả
đúng lời *"giá trị không khớp"*: chỉ khi nó đã TÍNH LẠI được đại lượng từ hình
thì nó mới nói được câu ấy. Từ chối kiểu, hay ném vì không tính nổi, đều không
phải câu đó.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry.curved import Circle3, CurvedSolid
from app.simulation.geometry.exact import Line3, Plane3, Vec3
from app.simulation.geometry.section import box
from app.simulation.semantic_program.geometry_obligations import _LECH
from app.simulation.semantic_program.measure_contract import (
    BANG_PHEP_DO,
    NGHIA_VU_DO,
    kieu_chu_the_nghia_vu,
)
from app.simulation.semantic_program.obligations import (
    OBLIGATION_KINDS,
    Obligation,
    has_server_owned_checker,
)
from app.simulation.semantic_program.postconditions import CHECKERS

v = Vec3.of

#: Kiểu ngữ nghĩa → **hai** vật runtime khác nhau. Hai chứ không một: phép đo
#: hai toán hạng cần `of` và `wrt` phân biệt, và một cặp trùng nhau cho khoảng
#: cách 0 — hợp lệ nhưng là ca yếu nhất có thể chọn.
#:
#: Bảng này thuộc BỘ ĐO, không phải mã sản phẩm: nó **không** khai kiểu nào hợp
#: với lượng đo nào (câu ấy chỉ `BANG_PHEP_DO` được trả lời — §3). Nó chỉ nói
#: *"một `line3` trông như thế này"*.
MAU: dict[str, tuple] = {
    "point3": (v(1, 2, 3), v(4, 0, -1)),
    # Ở runtime `vector3` và `point3` cùng là `Vec3` — phân biệt nằm ở
    # `memory_declarations`, không ở lớp. Bộ đo phản ánh đúng điều đó.
    "vector3": (v(1, 2, 3), v(4, 0, -1)),
    "line3": (Line3.through(v(0, 0, 0), v(1, 0, 0)),
              Line3.through(v(0, 5, 0), v(0, 5, 1))),
    "plane3": (Plane3(v(0, 0, 0), v(0, 0, 1)), Plane3(v(0, 0, 7), v(0, 1, 1))),
    "solid": (box(2, 3, 5), box(1, 1, 1)),
    "curved_solid": (CurvedSolid("ball", v(0, 0, 0), None, v(6, 0, 0)),
                     CurvedSolid("cone", v(0, 0, 0), v(0, 0, 4), v(3, 0, 0))),
    "circle3": (Circle3(v(0, 0, 0), v(0, 0, 1), F(16)),
                Circle3(v(1, 1, 1), v(1, 0, 0), F(9))),
}

#: Nhân chứng CỐ TÌNH SAI. Số nguyên tố lớn: không đại lượng nào trong bảng mẫu
#: bằng nó, và `cos²` thì không thể — nó nằm ngoài `[0, 1]`.
SAI = F(104729)

#: ─── NGOẠI LỆ KIẾN TRÚC — KHAI TƯỜNG MINH, VÀ CHỈ ĐƯỢC NGẮN ĐI ──────────
#:
#: Mỗi dòng phải nêu LÝ DO, và `test_ngoai_le_van_CON_THAT` bắt nó vẫn còn thật:
#: vá xong mà quên xoá dòng là ĐỎ. Nợ chỉ đi xuống — cùng cơ chế `KNOWN_GAPS`
#: của `code-index-sync.test.ts`.
NGOAI_LE: dict[tuple[str, str], str] = {
    ("angle", "vector3"): (
        "`angle` hiện thực hoá bởi HAI lượng đo: `angle_cos_sq` (line3|plane3, "
        "trả cos²) và `angle_cos` (vector3, trả cos CÓ DẤU). `check_angle` chỉ "
        "tính lại cos², nên nó không kiểm được nhân chứng của `angle_cos` — và "
        "ô giá trị mong đợi của nghĩa vụ cũng chỉ có `cos_sq`. Đóng khoảng này "
        "đòi một quyết định NGỮ NGHĨA (nghĩa vụ `angle` trỏ lượng đo nào, và "
        "đáp số có dấu viết vào đâu), không phải một phép nới kiểu — nên nó là "
        "một wave riêng, không phải việc tiện tay của "
        "`VOLUME_VERIFICATION_BRIDGE` (§13)."),
}


def _co_wrt(nghia_vu: str) -> bool:
    """Nghĩa vụ này có lượng đo hai toán hạng không? DẪN XUẤT, không viết tay."""
    return any(BANG_PHEP_DO[q].hai_toan_hang for q in NGHIA_VU_DO[nghia_vu])


def _do_troi() -> list[str]:
    """Duyệt HẾT bảng, trả danh sách chỗ trôi. Rỗng = `MEASURE_CHECKER_SUBJECT_DRIFT = 0`.

    Đọc `NGHIA_VU_DO`/`BANG_PHEP_DO` **lúc gọi**, không lúc import: §12 đổi bảng
    rồi gọi lại hàm này để chứng minh cổng có răng.
    """
    troi: list[str] = []
    for nghia_vu in NGHIA_VU_DO:
        if not has_server_owned_checker(nghia_vu):
            continue                      # mức yếu — không phải chỗ trôi
        fn = CHECKERS[nghia_vu]
        params_wrt = _co_wrt(nghia_vu)
        for kieu in sorted(kieu_chu_the_nghia_vu(nghia_vu)):
            if (nghia_vu, kieu) in NGOAI_LE:
                continue
            mau = MAU.get(kieu)
            if mau is None:
                troi.append(
                    f"{nghia_vu}/{kieu}: KHÔNG CÓ MẪU trong bộ đo. Hợp đồng vừa "
                    f"cho phép một kiểu chủ thể mà bộ đo chưa biết dựng — thêm "
                    f"mẫu vào `MAU`, rồi cổng này mới nói được checker có nhận "
                    f"nó hay không.")
                continue
            a, b = mau
            snap = {"A": a, "B": b, "w": SAI}
            ob = Obligation(
                kind=nghia_vu, container="A",
                params={"witness": "w", **({"wrt": "B"} if params_wrt else {})})
            try:
                loi = fn(snap, ob)
            except Exception as e:        # noqa: BLE001 — cổng không được sập
                troi.append(f"{nghia_vu}/{kieu}: checker NÉM {type(e).__name__}: {e}")
                continue
            if loi is None:
                troi.append(
                    f"{nghia_vu}/{kieu}: checker NUỐT một nhân chứng sai — "
                    f"đường kiểm chứng không chạy trên kiểu này")
            elif not loi.startswith(_LECH):
                troi.append(
                    f"{nghia_vu}/{kieu}: hợp đồng CHO PHÉP kiểu này, checker "
                    f"KHÔNG kiểm được nó → {loi!r}")
    return troi


# ══ §11 · BẤT BIẾN ═══════════════════════════════════════════════════════
def test_MEASURE_CHECKER_SUBJECT_DRIFT_bang_0():
    troi = _do_troi()
    assert troi == [], "\n".join(["Trôi giữa hợp đồng phép đo và bộ kiểm:", *troi])


def test_moi_nghia_vu_do_deu_duoc_soat_that():
    """Cổng phải thật sự chạm tới `volume`/`radius`/`distance` — một cổng duyệt
    tập rỗng cũng "xanh"."""
    da_soat = {nv for nv in NGHIA_VU_DO if has_server_owned_checker(nv)}
    assert {"distance", "angle", "volume", "radius"} <= da_soat, da_soat


def test_bang_dan_xuat_khong_lech_bang_goc():
    """`OBLIGATION_KINDS` phải vẫn là DẪN XUẤT của `BANG_PHEP_DO`, không phải
    một bản chép tay thứ hai — chính bản chép ấy là gốc của cả hai sự cố."""
    for nv in NGHIA_VU_DO:
        assert OBLIGATION_KINDS[nv] == kieu_chu_the_nghia_vu(nv), nv


def test_MEASURE_SUBJECT_COMPATIBILITY_AUTHORITIES_bang_1():
    """Không mã sản phẩm nào được dựng bảng kiểu thứ hai (§3)."""
    import pathlib

    goc = pathlib.Path(__file__).resolve().parents[2] / "app"
    cam = ("VOLUME_ALLOWED_TYPES", "CHECKER_MEASURE_TYPES", "CURVED_VOLUME_TYPES")
    thay = [f"{p.relative_to(goc)}:{t}"
            for p in goc.rglob("*.py")
            for t in cam if t in p.read_text(encoding="utf-8")]
    assert thay == [], thay


# ══ §12 · CỔNG PHẢI CÓ RĂNG ══════════════════════════════════════════════
@pytest.mark.parametrize("nghia_vu,kieu_moi", [
    # KHÔNG chỉ `curved_solid`: nếu cổng chỉ đỏ cho đúng ca vừa vá thì nó chỉ
    # là ca thử ấy viết dài dòng hơn.
    ("volume", "circle3"),
    ("radius", "solid"),
    ("distance", "curved_solid"),
])
def test_cong_DO_khi_hop_dong_noi_ma_checker_khong_theo(monkeypatch, nghia_vu,
                                                        kieu_moi):
    """Tiêm một kiểu chủ thể mới vào hợp đồng **mà không** thêm đường kiểm
    chứng. Cổng phải đỏ, và phải gọi đúng tên chỗ trôi."""
    goc = BANG_PHEP_DO[nghia_vu]
    monkeypatch.setitem(
        BANG_PHEP_DO, nghia_vu,
        type(goc)(goc.quantity, (*goc.kieu_of, kieu_moi), goc.kieu_wrt,
                  goc.nghia, goc.goi_y))

    troi = _do_troi()
    assert any(f"{nghia_vu}/{kieu_moi}" in x for x in troi), troi


def test_cong_BAT_DUOC_dung_con_bug_da_sinh_ra_no(monkeypatch):
    """Phép thử thuyết phục nhất: dựng lại `check_volume` **bản cũ** (chỉ nhận
    `Polyhedron`) và đòi cổng gọi tên đúng chỗ trôi `volume/curved_solid`.

    Một cổng chỉ đỏ trước những mũi tiêm do chính nó nghĩ ra thì chưa chứng
    minh được gì về con bug thật. Đây là con bug thật, nguyên hình dạng đã làm
    `ball_1` mất `servable` trong probe §18.
    """
    from app.simulation.geometry.section import Polyhedron

    def check_volume_BAN_CU(snapshot: dict, ob) -> str | None:
        sol = snapshot.get(ob.container)
        if not isinstance(sol, Polyhedron):
            return "cần một `solid`"
        return _LECH + ": (bản cũ, phần so giá trị không cần cho phép thử này)"

    monkeypatch.setitem(CHECKERS, "volume", check_volume_BAN_CU)
    troi = _do_troi()
    assert any("volume/curved_solid" in x for x in troi), troi


def test_cong_XANH_LAI_sau_khi_go_tiem(monkeypatch):
    """Vế còn lại của §12: gỡ mũi tiêm thì cổng phải xanh trở lại — một cổng
    đỏ vĩnh viễn cũng vô dụng như một cổng không bao giờ đỏ."""
    goc = BANG_PHEP_DO["volume"]
    monkeypatch.setitem(
        BANG_PHEP_DO, "volume",
        type(goc)(goc.quantity, (*goc.kieu_of, "circle3"), goc.kieu_wrt,
                  goc.nghia, goc.goi_y))
    assert _do_troi() != []
    monkeypatch.undo()
    assert _do_troi() == []


def test_kieu_moi_KHONG_CO_MAU_cung_lam_cong_do(monkeypatch):
    """Lỗ hiển nhiên nhất của một cổng dựa trên bảng mẫu: kiểu lạ thì bỏ qua,
    rồi im lặng. Ở đây "không có mẫu" là một chỗ trôi, không phải một lối thoát.
    """
    goc = BANG_PHEP_DO["volume"]
    monkeypatch.setitem(
        BANG_PHEP_DO, "volume",
        type(goc)(goc.quantity, (*goc.kieu_of, "hinh_xuyen"), goc.kieu_wrt,
                  goc.nghia, goc.goi_y))
    troi = _do_troi()
    assert any("KHÔNG CÓ MẪU" in x and "hinh_xuyen" in x for x in troi), troi


# ══ NGOẠI LỆ: NỢ CHỈ ĐƯỢC NGẮN ĐI ════════════════════════════════════════
def test_ngoai_le_van_CON_THAT():
    """Mỗi ngoại lệ phải vẫn là một chỗ trôi THẬT. Vá xong mà quên xoá dòng ⇒
    ĐỎ, bắt xoá. Nhờ vế này `NGOAI_LE` không thể thành bãi rác."""
    for (nghia_vu, kieu), ly_do in NGOAI_LE.items():
        assert kieu in kieu_chu_the_nghia_vu(nghia_vu), (
            f"ngoại lệ ({nghia_vu}, {kieu}) nói về một kiểu mà hợp đồng KHÔNG "
            f"còn cho phép — xoá dòng này")
        assert len(ly_do) > 80, f"ngoại lệ ({nghia_vu}, {kieu}) thiếu lý do"

        a, b = MAU[kieu]
        ob = Obligation(kind=nghia_vu, container="A",
                        params={"witness": "w",
                                **({"wrt": "B"} if _co_wrt(nghia_vu) else {})})
        try:
            loi = CHECKERS[nghia_vu]({"A": a, "B": b, "w": SAI}, ob)
        except Exception:                 # noqa: BLE001
            loi = None
        assert loi is None or not loi.startswith(_LECH), (
            f"({nghia_vu}, {kieu}) NAY đã kiểm được — xoá nó khỏi `NGOAI_LE`")


def test_ngoai_le_khong_duoc_phinh_ra():
    """Đóng băng danh sách: thêm một dòng là tự khai vừa tạo nợ mới, và phải
    làm điều đó một cách cố ý, không phải để một cổng đỏ thành xanh."""
    assert set(NGOAI_LE) == {("angle", "vector3")}
