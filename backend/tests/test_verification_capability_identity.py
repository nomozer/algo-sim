# -*- coding: utf-8 -*-
"""VÂN TAY NĂNG LỰC PHẢI THẤY ĐƯỢC NĂNG LỰC KIỂM CHỨNG. **0 lượt gọi model.**

    `VERIFICATION_CAPABILITY_IDENTITY`, 2026-09-03.

─── LỖ NÓ BỊT, ĐO ĐƯỢC ────────────────────────────────────────────────────

    container A   `check_volume` BÁC `curved_solid`
    container B   `check_volume` CHỨNG THỰC `curved_solid`
    →  CÙNG một `stable_capability_hash`

Hai hệ nhận và **phục vụ** hai tập chương trình khác nhau, mà `runtime_doctor`
không phân biệt nổi. Đây là lỗ danh tính thứ BA cùng họ:

    ① `CURVED_OBLIGATION_COVERAGE_BRIDGE`  cổng phủ đổi phán quyết, băm đứng im
       → vá bằng cách thêm `nghia_vu_chu_the` (kiểu chủ thể cổng phủ CHO PHÉP)
    ② `VOLUME_VERIFICATION_BRIDGE`         checker đổi thứ nó kiểm được, băm vẫn
       đứng im — vì `nghia_vu` băm TÊN checker và `nghia_vu_chu_the` băm thứ
       cổng phủ cho phép; không trường nào hỏi *"bộ kiểm có với tới không"*.

─── VÌ SAO KHÔNG BĂM MÃ NGUỒN ─────────────────────────────────────────────

`hash(inspect.getsource(check_volume))` sẽ đổi khi sửa một chú thích, đổi tên
biến, hay tách hàm — tức biến mọi lượt refactor thành "đổi năng lực". Kho này đã
ghi rõ vì sao điều đó nguy hiểm (`runtime_identity._bam`): *báo động giả là cách
nhanh nhất để một cổng bị tắt.* `test_I5` khoá đúng điều ấy.

Cái được băm là **hợp đồng ngữ nghĩa**, dẫn xuất:

    kiểm chứng được = `kieu_chu_the_nghia_vu(nv)` − `KHONG_KIEM_DUOC`
"""
from __future__ import annotations

import pytest

from app.runtime_identity import capability_fingerprint, stable_capability_hash
from app.simulation.semantic_program.geometry_obligations import (
    KHONG_KIEM_DUOC,
    kieu_kiem_chung_duoc,
)
from app.simulation.semantic_program.measure_contract import (
    BANG_PHEP_DO,
    NGHIA_VU_DO,
    kieu_chu_the_nghia_vu,
)


@pytest.fixture
def goc() -> str:
    return stable_capability_hash()


def _them_khong_kiem_duoc(monkeypatch, nghia_vu: str, kieu: str) -> None:
    """Tiêm: khai rằng bộ kiểm KHÔNG với tới được `(nghia_vu, kieu)` nữa."""
    monkeypatch.setitem(KHONG_KIEM_DUOC, (nghia_vu, kieu), "tiêm cho phép thử")


# ══ THÀNH PHẦN CÓ MẶT VÀ NÓI ĐÚNG SỰ THẬT ════════════════════════════════
def test_VERIFICATION_SEMANTICS_IN_CAPABILITY_IDENTITY():
    fp = capability_fingerprint()
    assert "kiem_chung_do" in fp, "vân tay không mang năng lực kiểm chứng"
    assert fp["kiem_chung_do"], "thành phần rỗng thì băm gì cũng như nhau"


def test_thanh_phan_DAN_XUAT_chu_khong_phai_ban_chep():
    """`VERIFICATION_CAPABILITY_AUTHORITIES = 1`.

    Kiểu chủ thể vẫn chỉ `BANG_PHEP_DO` sở hữu; thông tin MỚI duy nhất là phần
    TRỪ ĐI. Nếu thành phần này là một danh sách viết tay thì nó là bản sao thứ
    hai của bảng kiểu — đúng con bug mà cả ba wave vừa rồi đi dọn.
    """
    fp = capability_fingerprint()
    for nv, kiem in fp["kiem_chung_do"].items():
        cho_phep = kieu_chu_the_nghia_vu(nv)
        assert set(kiem) <= cho_phep, (
            f"{nv}: khai kiểm được một kiểu hợp đồng KHÔNG cho phép — {kiem}")
        assert set(kiem) == {k for k in cho_phep
                             if (nv, k) not in KHONG_KIEM_DUOC}


def test_I6_ngoai_le_angle_vector3_duoc_khai_TRUNG_THUC():
    """§9 — vân tay **không được** khai rằng `check_angle` chứng thực
    `angle_cos(vector3)` khi nó chỉ tính lại cos².

    Và chỗ lệch ấy phải NHÌN THẤY ĐƯỢC: `nghia_vu_chu_the` (cổng phủ cho phép)
    có `vector3`, `kiem_chung_do` (kiểm chứng được) thì không. Hai trường cạnh
    nhau kể đúng câu chuyện — một trường thì không.
    """
    fp = capability_fingerprint()
    assert "vector3" in fp["nghia_vu_chu_the"]["angle"]
    assert "vector3" not in fp["kiem_chung_do"]["angle"]
    assert fp["kiem_chung_do"]["angle"] == ["line3", "plane3"]
    assert ("angle", "vector3") in KHONG_KIEM_DUOC


# ══ §14 · RED TESTS ══════════════════════════════════════════════════════
def test_I1_check_volume_BAN_CU_cho_van_tay_KHAC(monkeypatch, goc):
    """Phép thử bắt buộc (§6): hợp đồng kiểm chứng CŨ (`volume` chỉ chứng thực
    `Polyhedron`) phải cho một băm khác hợp đồng hiện tại.

    Đây chính là hai container A/B trong phần mở đầu. Không băm chuỗi mã nguồn
    ở đâu trong đường này.
    """
    truoc = capability_fingerprint()["kiem_chung_do"]["volume"]
    assert truoc == ["curved_solid", "solid"]

    _them_khong_kiem_duoc(monkeypatch, "volume", "curved_solid")

    assert capability_fingerprint()["kiem_chung_do"]["volume"] == ["solid"]
    assert stable_capability_hash() != goc


def test_I2_bo_curved_solid_khoi_kiem_chung_radius_doi_van_tay(monkeypatch, goc):
    """§7 — `radius` chứng thực `circle3` + `curved_solid`. Mất một cái là mất
    năng lực sản phẩm, và băm phải nói ra."""
    assert kieu_kiem_chung_duoc("radius") == {"circle3", "curved_solid"}
    _them_khong_kiem_duoc(monkeypatch, "radius", "curved_solid")
    assert capability_fingerprint()["kiem_chung_do"]["radius"] == ["circle3"]
    assert stable_capability_hash() != goc


def test_I3_them_chu_the_KHONG_kiem_duoc_vao_distance_doi_van_tay(monkeypatch,
                                                                  goc):
    """§8 — nới hợp đồng `distance` sang một kiểu bộ kiểm không với tới.

    Hai trường phải phản ứng KHÁC nhau, và đó là toàn bộ giá trị của việc có cả
    hai: `nghia_vu_chu_the` thấy hợp đồng rộng ra, `kiem_chung_do` thì không —
    tức băm ghi lại đúng *"cổng phủ nhận thêm một kiểu mà bộ kiểm chưa theo"*,
    đúng hình dạng con bug `volume` gốc.
    """
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    p = BANG_PHEP_DO["distance"]
    monkeypatch.setitem(
        BANG_PHEP_DO, "distance",
        type(p)(p.quantity, (*p.kieu_of, "curved_solid"), p.kieu_wrt, p.nghia,
                p.goi_y))
    # ⚠️ Phải vá CẢ `OBLIGATION_KINDS`: nó là ảnh chụp LÚC IMPORT
    # (`_nap_nghia_vu_do`), không phải khung nhìn sống trên `BANG_PHEP_DO`. Ở
    # sản phẩm hai bảng luôn khớp vì cùng dựng lúc nạp module; trong một phép
    # tiêm thì không, và bản đầu của test này vá mỗi một bảng rồi tự triệt tiêu
    # đúng thứ nó định đo.
    monkeypatch.setitem(
        OBLIGATION_KINDS, "distance",
        OBLIGATION_KINDS["distance"] | {"curved_solid"})
    _them_khong_kiem_duoc(monkeypatch, "distance", "curved_solid")

    fp = capability_fingerprint()
    # Hai trường phản ứng KHÁC nhau — đó là lý do phải có cả hai.
    assert "curved_solid" in fp["nghia_vu_chu_the"]["distance"]
    assert "curved_solid" not in fp["kiem_chung_do"]["distance"]
    assert stable_capability_hash() != goc


def test_I3b_thu_hep_kiem_chung_distance_cung_doi_van_tay(monkeypatch, goc):
    """Vế còn lại của §8: mất năng lực chứng thực một kiểu ĐANG hỗ trợ cũng
    phải đổi băm — kể cả khi hợp đồng không nhúc nhích."""
    _them_khong_kiem_duoc(monkeypatch, "distance", "plane3")
    fp = capability_fingerprint()
    assert fp["nghia_vu_chu_the"]["distance"] == ["line3", "plane3", "point3"]
    assert fp["kiem_chung_do"]["distance"] == ["line3", "point3"]
    assert stable_capability_hash() != goc


def test_I4_doi_TEN_checker_van_doi_van_tay(monkeypatch, goc):
    """Chính sách tường minh: tên nghĩa vụ **là** ngữ nghĩa — nó là từ vựng
    `analyze` phát ra và là khoá `CHECKERS` tra. Đổi tên = đổi thứ hệ kiểm
    được, nên băm PHẢI đổi. `nghia_vu` đã phủ điều này từ trước; test này khoá
    lại để chính sách không bị hiểu ngược.
    """
    from app.simulation.semantic_program.geometry_obligations import (
        GEOMETRY_CHECKERS,
        check_volume,
    )

    monkeypatch.delitem(GEOMETRY_CHECKERS, "volume")
    monkeypatch.setitem(GEOMETRY_CHECKERS, "the_tich", check_volume)
    assert stable_capability_hash() != goc


def test_I5_chu_thich_va_dinh_dang_KHONG_duoc_lam_doi_van_tay():
    """Vế cấm của §3: vân tay **không** được dựng trên chuỗi mã nguồn.

    Chứng minh bằng hai vế. ① Không đường nào của `capability_fingerprint` đọc
    mã nguồn. ② Băm là hàm THUẦN của các bảng — gọi hai lần cho cùng một giá
    trị, nên không có gì phụ thuộc bố cục file hay thứ tự dict.
    """
    import inspect

    import app.runtime_identity as ri

    src = inspect.getsource(ri.capability_fingerprint)
    for cam in ("getsource", "getsourcelines", "read_text", "__file__",
                "readlines", "open("):
        assert cam not in src, f"vân tay năng lực chạm mã nguồn qua `{cam}`"

    assert stable_capability_hash() == stable_capability_hash()


def test_I7_go_HET_mui_tiem_thi_van_tay_ve_ĐUNG_ban_goc(monkeypatch, goc):
    """Một băm chỉ biết đổi cũng vô dụng như một băm không bao giờ đổi: nó phải
    quay lại **đúng** giá trị cũ, không phải một giá trị mới nào đó."""
    _them_khong_kiem_duoc(monkeypatch, "volume", "curved_solid")
    _them_khong_kiem_duoc(monkeypatch, "radius", "curved_solid")
    assert stable_capability_hash() != goc

    monkeypatch.undo()
    assert stable_capability_hash() == goc


# ══ KHÔNG ĐỔI HÀNH VI, KHÔNG ĐỔI BỀ MẶT MÔ HÌNH ══════════════════════════
def test_CHECKER_RUNTIME_BEHAVIOR_CHANGED_bang_NO():
    """Wave này thêm một lời KHAI, không đụng một dòng phán quyết nào. Ba
    checker chạy lại đúng như trước."""
    from fractions import Fraction as F

    from app.simulation.geometry.curved import CurvedSolid
    from app.simulation.geometry.exact import Vec3
    from app.simulation.geometry.radical import radical
    from app.simulation.geometry.section import box
    from app.simulation.semantic_program.geometry_obligations import (
        check_radius,
        check_volume,
    )
    from app.simulation.semantic_program.obligations import Obligation

    v = Vec3.of

    def ob(kind, c, w):
        return Obligation(kind=kind, container=c, params={"witness": w})

    cau = CurvedSolid("ball", v(0, 0, 0), None, v(6, 0, 0))
    assert check_volume({"S": cau, "V": radical(288, 1, mu=1)},
                        ob("volume", "S", "V")) is None
    assert check_volume({"S": cau, "V": F(1)}, ob("volume", "S", "V"))
    assert check_volume({"K": box(2, 3, 5), "V": F(30)},
                        ob("volume", "K", "V")) is None
    assert check_radius({"S": cau, "R": F(6)}, ob("radius", "S", "R")) is None


def test_thanh_phan_cu_KHONG_bi_dong_cham():
    """Thêm trường mới không được lặng lẽ đổi nghĩa trường cũ."""
    fp = capability_fingerprint()
    assert fp["nghia_vu_chu_the"]["volume"] == ["curved_solid", "solid"]
    assert fp["nghia_vu_chu_the"]["angle"] == ["line3", "plane3", "vector3"]
    assert "volume" in fp["nghia_vu"] and "radius" in fp["nghia_vu"]
    assert set(fp) == {
        "domain", "bieu_thuc", "cau_lenh_dung", "toan_hang_lenh", "phep_do",
        "kieu_bo_nho", "nghia_vu", "nghia_vu_chu_the", "kiem_chung_do"}


def test_pham_vi_thanh_phan_duoc_khai_dung():
    """Phạm vi có chủ đích: chỉ nghĩa vụ ĐO có checker — đúng tập mà
    `test_measure_checker_subject_drift` CHỨNG MINH được.

    Khai rộng hơn tập đã chứng minh là tuyên bố một thứ chưa đo, và đó đúng là
    cái nết đã đẻ ra ba lỗ danh tính trước.
    """
    from app.simulation.semantic_program.geometry_obligations import (
        GEOMETRY_CHECKERS,
    )

    fp = capability_fingerprint()
    assert set(fp["kiem_chung_do"]) == {
        nv for nv in NGHIA_VU_DO if nv in GEOMETRY_CHECKERS}
    assert set(fp["kiem_chung_do"]) == {"distance", "angle", "volume", "radius"}
