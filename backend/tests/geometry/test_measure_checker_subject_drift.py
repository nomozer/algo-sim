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
from app.simulation.geometry.section import cross_section, box
from app.simulation.semantic_program.geometry_obligations import (
    KHONG_KIEM_DUOC,
    _LECH,
    kieu_kiem_chung_duoc,
)
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
    # ─── HAI KIỂU PHẲNG, thêm 2026-09-04 ────────────────────────────────
    #
    # `ANALYZE_OBLIGATION_SURFACE_COMPLETION` mở nghĩa vụ `area`, và hợp đồng
    # phép đo cho nó ba kiểu chủ thể. Chính cổng này đòi mẫu cho hai kiểu mới —
    # nó nói đúng: không có mẫu thì nó không kết luận được checker nhận hay
    # không, và một cổng im lặng vì thiếu dữ liệu là một cổng không gác.
    #
    # `polygon3` ở runtime là một TUPLE các đỉnh, không có lớp riêng — mẫu phải
    # phản ánh đúng điều đó, y như `vector3` phản ánh việc nó dùng chung `Vec3`.
    "polygon3": ((v(0, 0, 0), v(4, 0, 0), v(4, 3, 0)),
                 (v(0, 0, 0), v(2, 0, 0), v(2, 2, 0), v(0, 2, 0))),
    "section": (cross_section(box(2, 2, 2), Plane3(v(0, 0, 1), v(0, 0, 1))),
                cross_section(box(4, 4, 4), Plane3(v(0, 0, 2), v(0, 0, 1)))),
}

#: Nhân chứng CỐ TÌNH SAI. Số nguyên tố lớn: không đại lượng nào trong bảng mẫu
#: bằng nó, và `cos²` thì không thể — nó nằm ngoài `[0, 1]`.
SAI = F(104729)

#: ─── NGOẠI LỆ KIẾN TRÚC ─────────────────────────────────────────────────
#:
#: ⚠️ **ĐÃ DỜI SANG MÃ SẢN PHẨM** 2026-09-03 (`VERIFICATION_CAPABILITY_IDENTITY`):
#: nay là `geometry_obligations.KHONG_KIEM_DUOC`, nằm cạnh chính bảng đăng ký
#: checker, và `capability_fingerprint()` băm hiệu của nó.
#:
#: Vì sao phải dời: chừng nào nó còn nằm trong file test thì **vân tay năng lực
#: của sản phẩm phụ thuộc một file test** — bộ đo không được làm thẩm quyền của
#: thứ nó đo. Test giữ đúng vai của mình: CHỨNG MINH lời khai ấy trung thực
#: (`test_ngoai_le_van_CON_THAT`), không sở hữu nó.
#:
#: Nợ vẫn chỉ đi xuống, và nay còn đắt hơn: thêm một mục là **đổi
#: `stable_capability_hash`**, nên nó không thể lặng lẽ.
NGOAI_LE = KHONG_KIEM_DUOC


def _co_wrt(nghia_vu: str) -> bool:
    """Nghĩa vụ này có lượng đo hai toán hạng không? DẪN XUẤT, không viết tay."""
    return any(BANG_PHEP_DO[q].hai_toan_hang for q in NGHIA_VU_DO[nghia_vu])


def _chay_checker(nghia_vu: str, kieu: str):
    """Thả một nhân chứng CỐ TÌNH SAI vào checker. Trả `(loi, nem)`.

    Mẫu thiếu ⇒ `KeyError` để người gọi phân biệt *"chưa biết dựng kiểu này"*
    với *"checker không kiểm được"* — hai kết luận rất khác nhau.
    """
    a, b = MAU[kieu]
    ob = Obligation(
        kind=nghia_vu, container="A",
        params={"witness": "w", **({"wrt": "B"} if _co_wrt(nghia_vu) else {})})
    try:
        return CHECKERS[nghia_vu]({"A": a, "B": b, "w": SAI}, ob), None
    except Exception as e:                # noqa: BLE001 — cổng không được sập
        return None, e


def _kiem_chung_duoc(nghia_vu: str, kieu: str) -> bool:
    """ĐO — checker có thật sự chứng thực được kiểu chủ thể này không?

    Tiêu chí: nó phải trả đúng lời *"giá trị không khớp"*. Chỉ khi đã TÍNH LẠI
    được đại lượng từ hình thì nó mới nói được câu ấy; từ chối kiểu, hay ném vì
    không tính nổi, đều không phải câu đó.
    """
    loi, nem = _chay_checker(nghia_vu, kieu)
    return nem is None and loi is not None and loi.startswith(_LECH)


def _do_troi() -> list[str]:
    """Duyệt HẾT bảng, trả danh sách chỗ trôi. Rỗng = `MEASURE_CHECKER_SUBJECT_DRIFT = 0`.

    Đọc `NGHIA_VU_DO`/`BANG_PHEP_DO` **lúc gọi**, không lúc import: §12 đổi bảng
    rồi gọi lại hàm này để chứng minh cổng có răng.
    """
    troi: list[str] = []
    for nghia_vu in NGHIA_VU_DO:
        if not has_server_owned_checker(nghia_vu):
            continue                      # mức yếu — không phải chỗ trôi
        for kieu in sorted(kieu_chu_the_nghia_vu(nghia_vu)):
            if (nghia_vu, kieu) in NGOAI_LE:
                continue
            if kieu not in MAU:
                troi.append(
                    f"{nghia_vu}/{kieu}: KHÔNG CÓ MẪU trong bộ đo. Hợp đồng vừa "
                    f"cho phép một kiểu chủ thể mà bộ đo chưa biết dựng — thêm "
                    f"mẫu vào `MAU`, rồi cổng này mới nói được checker có nhận "
                    f"nó hay không.")
                continue
            loi, nem = _chay_checker(nghia_vu, kieu)
            if nem is not None:
                troi.append(
                    f"{nghia_vu}/{kieu}: checker NÉM {type(nem).__name__}: {nem}")
            elif loi is None:
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


def test_loi_KHAI_nang_luc_kiem_chung_khop_thuc_te_DO_DUOC():
    """Khoá vòng: mã sản phẩm KHAI `kieu_kiem_chung_duoc(nv)`, và
    `capability_fingerprint` băm chính lời khai ấy. Ở đây ta ĐO thật rồi so.

    Không có vòng khoá này thì lời khai là một lời hứa — và một vân tay năng
    lực dựng trên lời hứa còn tệ hơn không có vân tay, vì nó trông như bằng
    chứng.
    """
    for nghia_vu in NGHIA_VU_DO:
        if not has_server_owned_checker(nghia_vu):
            continue
        khai = kieu_kiem_chung_duoc(nghia_vu)
        do_duoc = {
            kieu for kieu in kieu_chu_the_nghia_vu(nghia_vu)
            if _kiem_chung_duoc(nghia_vu, kieu)}
        assert khai == do_duoc, (
            f"{nghia_vu}: KHAI kiểm được {sorted(khai)}, ĐO ĐƯỢC "
            f"{sorted(do_duoc)} — vân tay năng lực đang nói dối")


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
        assert not _kiem_chung_duoc(nghia_vu, kieu), (
            f"({nghia_vu}, {kieu}) NAY đã kiểm được — xoá nó khỏi "
            f"`KHONG_KIEM_DUOC`. Để nguyên là vân tay năng lực khai THẤP hơn "
            f"thứ sản phẩm làm được.")


def test_ngoai_le_khong_duoc_phinh_ra():
    """Đóng băng danh sách: thêm một dòng là tự khai vừa tạo nợ mới, và phải
    làm điều đó một cách cố ý, không phải để một cổng đỏ thành xanh."""
    assert set(NGOAI_LE) == {("angle", "vector3")}
