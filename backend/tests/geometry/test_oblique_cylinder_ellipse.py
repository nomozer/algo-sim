# -*- coding: utf-8 -*-
"""THIẾT DIỆN ELIP CỦA HÌNH TRỤ — nền tất định. **0 lượt gọi model.**

    `docs/CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION.md`
    2026-09-07.

Bộ test này chứng minh **hai** mức, và **chỉ** hai:

    SYSTEM_EXPRESSIBLE        IR diễn đạt được lớp bài này
    DETERMINISTICALLY_CORRECT engine tính đúng, chính xác tuyệt đối

`MODEL_DISCOVERABLE` và `STABILITY_UNDER_ACCEPTANCE` **NOT_MEASURED** — không
một lượt gọi model nào ở đây, nên không dòng nào được đọc như bằng chứng về
hành vi mô hình.

─── HAI ORACLE ĐỘC LẬP ────────────────────────────────────────────────────

① **Giải tích**: `b = r`, `a = r/|cos θ|`, `S = πab`. Dẫn từ `u` và `n`.
② **Thế thẳng**: bốn đầu mút trục elip phải nằm ĐỒNG THỜI trên mặt trụ
   (`dist²(P, trục) = r²`) và trên mặt phẳng (`n·(P − C) = 0`).

Hai lối tới cùng một số. Một mình lối ① là kiểm công thức bằng chính công thức.
"""
from __future__ import annotations

import copy
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.geometry import curved as CV
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))


def v(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


#: Ca chuẩn: `r = 3`, `h = 20`, trục `Oz`, mặt phẳng `z = 10 + x`.
def tru(radius_sq=F(9), cao=20, **kw) -> CV.CurvedSolid:
    return CV.CurvedSolid(kind="cylinder", anchor=v(0, 0, 0),
                          apex_or_top=v(0, 0, cao), rim_point=None,
                          radius_sq_khai=radius_sq, height_sq_khai=None,
                          pose_canonical=True, **kw)


def mp_xien(z0=10) -> Plane3:
    """`z = z0 + x` ⇔ `x − z + z0 = 0`, pháp tuyến `(1, 0, −1)`."""
    return Plane3(point=v(0, 0, z0), normal=v(1, 0, -1))


# ══ ① CA CHUẨN — 9√2π, HAI ORACLE ════════════════════════════════════════
def test_01_ca_chuan_cho_dung_9can2pi():
    e = CV.intersect_plane_curved_ellipse(tru(), mp_xien())
    assert e.center == v(0, 0, 10)
    assert e.semi_minor_sq == F(9)              # b = 3
    assert e.semi_major_sq == F(18)             # a = 3√2
    assert display(CV.sqrt_rational(e.semi_minor_sq)) == "3"
    assert display(CV.sqrt_rational(e.semi_major_sq)) == "3√2"
    assert display(CV.dien_tich_elip(e)) == "9π√2"


def test_02_ORACLE_DOC_LAP_the_thang_phuong_trinh():
    """Oracle ②: bốn đầu mút trục nằm ĐỒNG THỜI trên mặt trụ và mặt phẳng.

    Không dùng lại `a²`/`b²` mà kernel vừa tính để suy ngược — kiểm bằng toạ độ
    **hữu tỉ độc lập**, đọc thẳng từ đề: mặt trụ `x² + y² = 9`, mặt phẳng
    `z = 10 + x`.
    """
    e = CV.intersect_plane_curved_ellipse(tru(), mp_xien())
    n, C = e.normal, e.center
    # Đầu mút trục LỚN: `C ± t·major_dir` với `t² = a²/|major_dir|²`.
    mm = e.major_dir.dot(e.major_dir)
    t2 = e.semi_major_sq / mm
    assert t2 == F(9, 400), t2                 # t = 3/20, HỮU TỈ
    t = F(3, 20)
    # …và tương tự cho trục NHỎ.
    s2 = e.semi_minor_sq / e.minor_dir.dot(e.minor_dir)
    assert s2 == F(9, 400)
    s = F(3, 20)
    dau_mut = [
        Vec3(C.x + t * e.major_dir.x, C.y + t * e.major_dir.y,
             C.z + t * e.major_dir.z),
        Vec3(C.x - t * e.major_dir.x, C.y - t * e.major_dir.y,
             C.z - t * e.major_dir.z),
        Vec3(C.x + s * e.minor_dir.x, C.y + s * e.minor_dir.y,
             C.z + s * e.minor_dir.z),
        Vec3(C.x - s * e.minor_dir.x, C.y - s * e.minor_dir.y,
             C.z - s * e.minor_dir.z),
    ]
    assert dau_mut[0] == v(3, 0, 13) and dau_mut[1] == v(-3, 0, 7)
    assert {dau_mut[2], dau_mut[3]} == {v(0, 3, 10), v(0, -3, 10)}
    for P in dau_mut:
        assert P.x * P.x + P.y * P.y == F(9), f"{P} KHÔNG trên mặt trụ"
        assert n.dot(Vec3(P.x - C.x, P.y - C.y, P.z - C.z)) == 0, \
            f"{P} KHÔNG trên mặt phẳng"
    # Oracle ② dẫn tới cùng một diện tích: `S = π·a·b = π·√(a²b²)`.
    assert display(CV.dien_tich_elip(e)) == "9π√2"


def test_03_hai_phuong_truc_VUONG_GOC_va_o_trong_mat_phang():
    e = CV.intersect_plane_curved_ellipse(tru(), mp_xien())
    assert e.major_dir.dot(e.minor_dir) == 0
    assert e.normal.dot(e.major_dir) == 0
    assert e.normal.dot(e.minor_dir) == 0
    # Trục NHỎ ⊥ trục hình trụ — đó là lý do `b` luôn bằng `r`.
    assert e.minor_dir.dot(v(0, 0, 1)) == 0


# ══ ② ĐƯỜNG TRÒN CŨ KHÔNG SUY SUYỂN ═════════════════════════════════════
def test_04_mat_phang_VUONG_GOC_truc_van_di_duong_circle3_cu():
    c = CV.intersect_plane_curved(
        tru(), Plane3(point=v(0, 0, 10), normal=v(0, 0, 1)))
    assert isinstance(c, CV.Circle3)
    assert c.radius_sq == F(9)
    assert display(CV.dien_tich_hinh_tron(c)) == "9π"
    # …và phép ELIP từ chối đúng ca ấy, kèm tên phép đúng.
    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(
            tru(), Plane3(point=v(0, 0, 10), normal=v(0, 0, 1)))
    assert ex.value.code == CV.ERR_ELIP_NGOAI_BAO_DONG
    assert "intersect_plane_curved" in str(ex.value)


def test_05_cau_va_non_giu_nguyen_hanh_vi_duong_tron():
    cau = CV.CurvedSolid("ball", v(0, 0, 0), None, v(5, 0, 0))
    c = CV.intersect_plane_curved(cau, Plane3(v(0, 0, 3), v(0, 0, 1)))
    assert c.radius_sq == F(16)


# ══ ③ HAI CÁCH KHAI TRỤ CHO KẾT QUẢ TƯƠNG ĐƯƠNG ═════════════════════════
def test_06_khai_bang_DIEM_VANH_va_bang_VO_HUONG_tuong_duong():
    """`radius_sq` là MỘT cửa — hai cách khai không được đẻ hai đường tính."""
    bang_diem = CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), v(3, 0, 0))
    bang_vh = tru()
    a = CV.intersect_plane_curved_ellipse(bang_diem, mp_xien())
    b = CV.intersect_plane_curved_ellipse(bang_vh, mp_xien())
    assert (a.center, a.semi_major_sq, a.semi_minor_sq) == \
           (b.center, b.semi_major_sq, b.semi_minor_sq)
    assert display(CV.dien_tich_elip(a)) == display(CV.dien_tich_elip(b))


# ══ ④⑤ BIÊN CỦA "NẰM TRỌN GIỮA HAI ĐÁY" ═════════════════════════════════
def test_07_elip_GAN_day_nhung_van_nam_tron():
    """Tâm ở `z = 3`, nửa trục dọc `= 3` ⇒ chạm đúng `z = 0`. Vẫn hợp lệ."""
    e = CV.intersect_plane_curved_ellipse(tru(), mp_xien(z0=3))
    assert e.center == v(0, 0, 3)
    assert display(CV.dien_tich_elip(e)) == "9π√2"


@pytest.mark.parametrize("z0", [2, 1, 18, 19])
def test_08_elip_VUOT_day_bi_tu_choi_bang_MA_ON_DINH(z0):
    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(tru(), mp_xien(z0=z0))
    assert ex.value.code == CV.ERR_ELIP_CAT_DAY
    assert "cung elip ghép cung tròn" in str(ex.value)


# ══ ⑥⑦⑧ BA BIÊN CÒN LẠI ═════════════════════════════════════════════════
def test_09_mat_phang_SONG_SONG_truc_ngoai_bao_dong_v1():
    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(
            tru(), Plane3(point=v(1, 0, 0), normal=v(1, 0, 0)))
    assert ex.value.code == CV.ERR_ELIP_NGOAI_BAO_DONG
    assert "SONG SONG" in str(ex.value)


def test_10_mat_phang_NGOAI_khoi_bi_tu_choi():
    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(tru(), mp_xien(z0=99))
    assert ex.value.code == CV.ERR_KHONG_CAT


def test_11_TIEP_XUC_suy_bien_khong_lot_qua():
    """Mặt phẳng tiếp xúc mặt trụ **song song trục** — nó bị bắt ở chốt ∥.

    Ghi thành một test riêng chứ không gộp vào `test_09`: với hình trụ, tiếp
    xúc và song-song-trục là **cùng một điều kiện hình học**, và nói ra điều ấy
    đáng giá hơn là để người đọc sau tự suy.
    """
    tx = Plane3(point=v(3, 0, 10), normal=v(1, 0, 0))   # x = 3, tiếp xúc
    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(tru(), tx)
    assert ex.value.code == CV.ERR_ELIP_NGOAI_BAO_DONG


def test_12_truyen_HINH_NON_vao_duong_elip_bi_phan_loai_dung():
    """⚠️ **ĐỔI 2026-09-08** (`OBLIQUE_CONE_SECTION_FOUNDATION`).

    Bản trước khẳng định nón bị từ chối bằng `ERR_ELIP_NGOAI_BAO_DONG` với lý
    do *"ba nhánh chưa phân xử"*, và ghim thêm `code != ERR_ELIP_CAT_DAY`.

    Nay ba nhánh **đã phân xử**, và phép đo cho một câu trả lời **khác điều tôi
    đoán lúc viết lại ô này**. Tôi ngờ ca ấy là hyperbol; đo ra là **ELIP**:
    nón `r = 12, h = 18` có `tan α = 2/3`, và ngưỡng elip là `m < cot α = 3/2`,
    **không** phải `m < tan α`. Mặt phẳng `z = x + 10` có `m = 1 < 3/2` ⇒ elip.

    Nhưng nó vẫn bị từ chối, và bằng đúng cái mã mà bản cũ ghim là *"khác"*:
    ở `z = 0` mặt phẳng cắt qua đĩa đáy (`x = −10`, trong bán kính 12), nên
    giao tuyến là cung elip ghép cung tròn ⇒ `ERR_ELIP_CAT_DAY`.

    Ô này giữ nguyên vai trò gác — nón KHÔNG lặng lẽ trả về một elip ở cấu
    hình này — nhưng lý do gác nay là lý do ĐÚNG, và dòng `!= ERR_ELIP_CAT_DAY`
    của bản cũ hoá ra khẳng định một điều SAI về chính ca nó chọn.
    """
    non = CV.CurvedSolid("cone", v(0, 0, 0), v(0, 0, 18), v(12, 0, 0))
    assert CV.phan_xu_conic(non, mp_xien()) == CV.CONIC_ELIP
    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(non, mp_xien())
    assert ex.value.code == CV.ERR_ELIP_CAT_DAY
    assert "nón" in str(ex.value).lower()


def test_12b_nón_o_cau_hinh_ELIP_nay_ĐƯỢC_phuc_vu():
    """Mặt kia của cùng một đồng xu: hạ độ dốc xuống dưới `tan α` thì chính
    khối nón ấy cho một elip đầy đủ. Nếu ô này đỏ thì `test_12` đang gác một
    thứ rộng hơn nó nên gác."""
    non = CV.CurvedSolid("cone", v(0, 0, 0), v(0, 0, 18), v(12, 0, 0))
    # `z = x/2 + 6` ⇒ `x − 2z + 12 = 0`, dốc 1/2 < 2/3.
    e = CV.intersect_plane_curved_ellipse(
        non, Plane3.from_equation(F(1), F(0), F(-2), F(12)))
    assert e.semi_major_sq > 0 and e.semi_minor_sq > 0
    assert CV.dien_tich_elip(e).mu == 1


# ══ ⑩ PHÉP TIÊM ① — HỆ SỐ BÁN TRỤC LỚN ══════════════════════════════════
def test_13_TIEM_bo_he_so_goc_thi_dien_tich_SAI(monkeypatch):
    """Bỏ `|n|²|u|²/(n·u)²` ⇒ elip thành đường tròn, `S = 9π` thay vì `9√2π`.

    Đây là điểm chịu lực số một: nếu ai đó "đơn giản hoá" `a² = r²` thì mọi
    test cấu trúc vẫn xanh, chỉ ĐÁP SỐ sai. Test này là thứ duy nhất đỏ.
    """
    goc = CV.intersect_plane_curved_ellipse

    def hong(s, pl):
        e = goc(s, pl)
        return CV.Ellipse3(e.center, e.normal, e.major_dir, e.minor_dir,
                           e.semi_minor_sq, e.semi_minor_sq)  # a² := b²

    monkeypatch.setattr(CV, "intersect_plane_curved_ellipse", hong)
    e = CV.intersect_plane_curved_ellipse(tru(), mp_xien())
    assert display(CV.dien_tich_elip(e)) == "9π"          # ← SAI, và lộ ra
    assert display(CV.dien_tich_elip(e)) != "9π√2"


def test_13b_XANH_LAI_sau_khi_go_tiem():
    e = CV.intersect_plane_curved_ellipse(tru(), mp_xien())
    assert display(CV.dien_tich_elip(e)) == "9π√2"


# ══ PHÉP TIÊM ② — KIỂM ELIP NẰM GIỮA HAI ĐÁY ════════════════════════════
def test_14_TIEM_go_kiem_nam_tron_thi_ca_VUOT_DAY_lot_qua(monkeypatch):
    """Gỡ chốt `duoi_sq < h_half_sq` ⇒ `z0 = 1` đi lọt và trả một elip DỐI.

    Chốt ấy là điểm chịu lực số hai: không có nó, hệ trả `9√2π` cho một hình
    **không phải elip** (cung elip ghép cung tròn), và không tầng nào phía sau
    biết để mà cãi.
    """
    import app.simulation.geometry.curved as M

    goc_loi = M.GeometryError

    class _BoQua(Exception):
        pass

    def raise_gia(code, msg=""):
        if code == M.ERR_ELIP_CAT_DAY:
            raise _BoQua
        raise goc_loi(code, msg)

    # Xác nhận ca ấy ĐANG bị chặn…
    with pytest.raises(GeometryError) as ex:
        CV.intersect_plane_curved_ellipse(tru(), mp_xien(z0=1))
    assert ex.value.code == CV.ERR_ELIP_CAT_DAY
    # …và chốt ấy là thứ DUY NHẤT chặn: gỡ nó ra thì ca đi lọt.
    monkeypatch.setattr(M, "GeometryError", raise_gia)
    with pytest.raises(_BoQua):
        CV.intersect_plane_curved_ellipse(tru(), mp_xien(z0=1))


# ══ ĐƯỜNG IR ĐẦY ĐỦ ═════════════════════════════════════════════════════
DE = ("Hình trụ tròn xoay có tâm hai đáy O và O', bán kính đáy bằng 3 và "
      "chiều cao OO' bằng 20. Ba điểm K, L, N nằm trên mặt trụ xác định mặt "
      "phẳng (P) cắt hình trụ theo elip (E). Tính diện tích của (E).")
LY = "Đặt hệ trục: tâm đáy dưới làm gốc, trục Oz dọc trục hình trụ."
RC = {
    "problem_text": DE,
    "input_facts": [
        {"fact_id": "hinh_tru", "label": "Hình trụ tâm hai đáy O và O'",
         "values": ["OO'"], "provenance": "confirmed"},
        {"fact_id": "ban_kinh", "label": "Bán kính đáy", "values": [3],
         "provenance": "confirmed"},
        {"fact_id": "chieu_cao", "label": "Chiều cao OO'", "values": [20],
         "provenance": "confirmed"},
        {"fact_id": "diem_K", "label": "Điểm K trên mặt trụ", "values": ["K"],
         "provenance": "confirmed"},
        {"fact_id": "diem_L", "label": "Điểm L trên mặt trụ", "values": ["L"],
         "provenance": "confirmed"},
        {"fact_id": "diem_N", "label": "Điểm N trên mặt trụ", "values": ["N"],
         "provenance": "confirmed"},
        {"fact_id": "mp_cat",
         "label": "Mặt phẳng (P) cắt hình trụ theo elip (E)",
         "values": ["(E)"], "provenance": "confirmed"},
    ],
    "obligations": [{"kind": "area", "container": "(E)",
                     "params": {"witness": "dt_E"}}],
}
GOLD = {
    "spec_version": "1.0", "title": "Thiết diện elip của hình trụ",
    "description": "Cắt hình trụ bằng mặt phẳng xiên rồi đo diện tích.",
    "memory_declarations": [
        {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": LY},
        {"name": "O2", "type": "point3", "initial_value": [0, 0, 20],
         "source_fact_id": "chieu_cao"},
        {"name": "r", "type": "float", "initial_value": 3,
         "source_fact_id": "ban_kinh"},
        {"name": "tru", "type": "curved_solid"},
        {"name": "K", "type": "point3", "initial_value": [3, 0, 13],
         "source_fact_id": "diem_K"},
        {"name": "L", "type": "point3", "initial_value": [-3, 0, 7],
         "source_fact_id": "diem_L"},
        {"name": "N", "type": "point3", "initial_value": [0, 3, 10],
         "source_fact_id": "diem_N"},
        {"name": "mp", "type": "plane3"},
        {"name": "E", "type": "ellipse3"},
        {"name": "dt_E", "type": "float"},
    ],
    "statements": [
        {"kind": "construct_curved_solid", "target_var": "tru",
         "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "O2",
         "radius": "r", "label": "Hình trụ"},
        {"kind": "construct_plane", "target_var": "mp",
         "through": ["K", "L", "N"], "label": "(P)"},
        {"kind": "assign", "target_var": "E",
         "expr": {"kind": "intersect_plane_curved_ellipse", "solid": "tru",
                  "plane": "mp"}},
        {"kind": "assign", "target_var": "dt_E",
         "expr": {"kind": "measure", "quantity": "area", "of": "E"}},
    ],
}


def _hd() -> RequestContract:
    return RequestContract.model_validate(RC)


def _chay(p: dict):
    return verify_and_compile(_hd(), SemanticProgramSpec.model_validate(p))


def _canh(p: dict) -> dict:
    return _dung_scene3d(SemanticProgramSpec.model_validate(p), _hd()) or {}


def test_15_IR_di_TRON_duong_va_dap_so_CHINH_XAC():
    oc = _chay(GOLD)
    assert oc.stage_reached == "served", oc.details
    assert oc.servable is True
    dl = {k: display(x) for k, x in (oc.final_memory or {}).items()
          if is_exact_number(x)}
    assert dl["dt_E"] == "9π√2"


def test_16_TAI_HIEN_khoang_trong_TRUOC_khi_sua():
    """Đường CŨ (`intersect_plane_curved`) vẫn từ chối đúng ca này.

    Giữ phép tái hiện lại làm test: nếu ai đó "sửa" phép cũ để nó nhận mặt
    phẳng xiên, thì hai phép sẽ chồng nhau và kiểu trả về tĩnh mất nghĩa.
    """
    p = copy.deepcopy(GOLD)
    for s in p["statements"]:
        if s.get("target_var") == "E":
            s["expr"]["kind"] = "intersect_plane_curved"
    for m in p["memory_declarations"]:
        if m["name"] == "E":
            m["type"] = "circle3"
    oc = _chay(p)
    assert oc.servable is False
    assert oc.stage_reached == "execution"
    assert any("CURVED_SECTION_OUTSIDE_V1_CLOSURE" in str(x)
               for x in (oc.details or []))


def test_17_kieu_DUNG_RA_thang_kieu_KHAI__hanh_vi_co_san_tu_truoc():
    """Khai `E` là `circle3` rồi gán bằng phép elip ⇒ **KHÔNG bị chặn**.

    ⚠️ Ghi ra như một TÍNH CHẤT ĐO ĐƯỢC, không phải một lời khen. Bản đầu của
    test này khẳng định `ir_static` bắt ca ấy; chạy thử cho thấy nó **không**,
    và khẳng định sai đã được thay bằng hành vi thật.

    Vì sao hành vi ấy đúng theo thiết kế hiện có: `bang_ky_hieu` nói thẳng rằng
    kiểu của một vật DỰNG RA suy dẫn tất định từ `_KIEU_DUNG`/`_CHU_KY`, và
    chương trình **không bắt buộc** phải khai nó cho đủ — bắt viết thêm là đẻ
    boilerplate cho thứ máy tự biết. Nên với vật dựng ra, dòng khai báo là
    trang trí, và kiểu THẬT thắng ở mọi tầng phía sau.

    Hệ quả kiểm được: đáp số vẫn CHÍNH XÁC, cảnh vẫn nhận đúng `ellipse3`, và
    renderer vẫn vẽ elip — không tầng nào bị lời khai sai dắt đi.

    Đây là hành vi **có sẵn từ trước**, không do wave elip sinh ra; siết nó lại
    là một lượt riêng chạm mọi chương trình đang khai lỏng, không phải việc của
    wave này.
    """
    p = copy.deepcopy(GOLD)
    for m in p["memory_declarations"]:
        if m["name"] == "E":
            m["type"] = "circle3"
    oc = _chay(p)
    assert oc.servable is True and oc.stage_reached == "served"
    dl = {k: display(x) for k, x in (oc.final_memory or {}).items()
          if is_exact_number(x)}
    assert dl["dt_E"] == "9π√2", "lời khai sai KHÔNG được làm sai đáp số"
    o = next(x for x in _canh(p)["objects"] if x["id"] == "E")
    assert o["type"] == "ellipse3" and o["render"] == "ellipse"


# ══ ⑪ TRACE VÀ SCENE3D ══════════════════════════════════════════════════
def test_18_trace_co_DUNG_MOT_buoc_sinh_elip_va_dependency_dung():
    v_ = {str(o.get("id")): o for o in _canh(GOLD).get("objects", [])}
    assert v_["E"]["type"] == "ellipse3"
    assert v_["E"]["origin"] == "derived"
    assert v_["E"]["producer"] == "intersect_plane_curved_ellipse"
    assert {"tru", "mp"} <= set(v_["E"].get("depends") or [])
    assert v_["dt_E"]["producer"] == "measure.area"
    assert "E" in (v_["dt_E"].get("depends") or [])
    ev = _canh(GOLD).get("events") or []
    sinh_E = [e for e in ev if e.get("object") == "E"]
    assert len(sinh_E) == 1, sinh_E


def test_19_BAO_DONG_phu_thuoc_tu_dien_tich_ve_du_chuoi_dung():
    """Từ đáp số truy ngược phải tới được cả hình trụ lẫn mặt phẳng nguồn."""
    v_ = {str(o.get("id")): o for o in _canh(GOLD).get("objects", [])}
    bao, hang_doi = set(), ["dt_E"]
    while hang_doi:
        t = hang_doi.pop()
        for d in (v_.get(t, {}).get("depends") or []):
            if d not in bao:
                bao.add(d)
                hang_doi.append(d)
    assert {"E", "tru", "mp", "O", "O2", "r", "K", "L", "N"} <= bao, sorted(bao)


def test_20_Scene3D_cho_elip_CHO_DU_sau_truong_exact():
    o = next(x for x in _canh(GOLD)["objects"] if x["id"] == "E")
    assert o["render"] == "ellipse"
    for f in ("center", "normal", "major_dir", "minor_dir",
              "semi_major_sq", "semi_minor_sq"):
        assert f in o, f
    # Số CHÍNH XÁC, dạng chuỗi — không float nào lọt xuống dây.
    assert o["semi_major_sq"] == "18" and o["semi_minor_sq"] == "9"
    assert all(isinstance(x, str) for x in o["center"])


# ══ PHÉP TIÊM ③ — LIÊN KẾT PRODUCER / DEPENDENCY ════════════════════════
def test_21_TIEM_bo_dependency_thi_bao_dong_DUT(monkeypatch):
    """Điểm chịu lực số ba: `depends` của elip.

    Mất nó thì mô phỏng vẫn ra `9√2π` và vẫn `served` — chỉ chuỗi nhân quả đứt,
    và học sinh không truy được elip từ đâu ra. Đúng loại hỏng câm mà
    `GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE` đã phải đi sửa một lần.
    """
    import app.simulation.semantic_program.validator as V

    # ⚠️ Bảng đúng là `validator._BIEU_THUC_HINH_HOC`, KHÔNG phải
    # `simulation_state._NGUON_CUA_PHEP_DUNG` — và nó được `simulation_state`
    # nhập **bên trong hàm**, nên phải vá ở MODULE SỞ HỮU.
    # `E` sinh bởi `assign` + biểu thức, nên nó đi nhánh biểu thức. Bản đầu của
    # phép tiêm này nhắm sai bảng và **vẫn xanh** — tức nó không gác gì; sửa
    # lại rồi mới thấy nó thật sự chịu lực.
    #
    # Và bảng ấy **dẫn xuất** từ `_CHU_KY` (`validator` §111), nên phép mới tự
    # có `depends` mà không phải khai thêm ở đâu — đó chính là thứ phép tiêm
    # này chứng minh: bỏ bảng đi thì bao đóng đứt ngay.
    goc = V._BIEU_THUC_HINH_HOC
    monkeypatch.setattr(V, "_BIEU_THUC_HINH_HOC", {})
    v_ = {str(o.get("id")): o for o in _canh(GOLD).get("objects", [])}
    # Hệ quả MẠNH HƠN dự đoán, và ghi đúng nó: bỏ bảng thì elip **biến mất
    # khỏi cảnh**, không chỉ mất `depends`. Vật không có xuất xứ thì tầng cảnh
    # không nhận nó là vật dựng ra, nên nó rơi khỏi danh sách luôn — và đáp số
    # `dt_E` khi ấy treo lơ lửng, không truy về đâu được.
    assert "E" not in v_, (
        "bỏ bảng nguồn mà elip vẫn ở trong cảnh — cổng này không gác gì cả")
    monkeypatch.setattr(V, "_BIEU_THUC_HINH_HOC", goc)
    v2 = {str(o.get("id")): o for o in _canh(GOLD).get("objects", [])}
    assert {"tru", "mp"} <= set(v2["E"].get("depends") or [])


def test_21b_bang_nguon_bieu_thuc_DAN_XUAT_tu_chu_ky():
    """Phép mới KHÔNG phải khai `depends` ở đâu — nó dẫn từ chữ ký.

    Đây là lý do `test_21` chứng minh được điều nó nói: nếu bảng ấy viết tay
    thì phép elip đã phải có một dòng riêng, và một dòng riêng là một chỗ để
    quên.
    """
    from app.simulation.semantic_program.ir_static_check import _CHU_KY
    from app.simulation.semantic_program.validator import _BIEU_THUC_HINH_HOC

    assert _BIEU_THUC_HINH_HOC["intersect_plane_curved_ellipse"] ==         tuple(o[0] for o in _CHU_KY["intersect_plane_curved_ellipse"][0])
    assert set(_BIEU_THUC_HINH_HOC) >= set(_CHU_KY)


# ══ ⑫ PARITY: REGISTRY KHÔNG ĐƯỢC TRÔI ══════════════════════════════════
def test_22_registry_kieu_va_producer_KHONG_TROI():
    """Bốn bảng phải cùng biết `ellipse3`; thiếu một là một tầng câm."""
    import typing

    from app.simulation.semantic_program import contract as C
    from app.simulation.semantic_program.geometry_exec import GEOMETRY_TYPES
    from app.simulation.semantic_program.ir_static_check import _CHU_KY
    from app.simulation.semantic_program.learner_surface import SURFACE_POLICY
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS
    from app.simulation.semantic_program.scene3d import RENDER_HINT, _TRUONG

    assert "ellipse3" in typing.get_args(C.MemoryType)
    assert "ellipse3" in GEOMETRY_TYPES
    assert "ellipse3" in SURFACE_POLICY
    assert _CHU_KY["intersect_plane_curved_ellipse"][1] == "ellipse3"
    assert "ellipse3" in BANG_PHEP_DO["area"].kieu_of
    assert "ellipse3" in OBLIGATION_KINDS["area"]     # DẪN từ BANG_PHEP_DO
    assert RENDER_HINT["ellipse3"] == "ellipse"
    assert set(_TRUONG["ellipse3"]) == {
        "center", "normal", "major_dir", "minor_dir",
        "semi_major_sq", "semi_minor_sq"}


def test_23_the_van_pham_NOI_RA_phep_moi_va_kieu_moi():
    """Mô hình không đọc được `_CHU_KY`; nó chỉ đọc thẻ."""
    from app.simulation.semantic_program.grammar_card import grammar_card

    t = grammar_card("hinh_hoc")
    assert "intersect_plane_curved_ellipse" in t
    dong = next(d for d in t.splitlines() if "type nhận đúng một trong" in d)
    assert "ellipse3" in dong
    assert "ellipse3" in next(d for d in t.splitlines() if "area(of:" in d)


def test_24_nang_luc_khai_dung_bac_foundation_only():
    from app.simulation.product_capability import NANG_LUC_SAN_PHAM, da_ho_tro

    nl = NANG_LUC_SAN_PHAM["curved_oblique_section"]
    assert nl.trang_thai == "foundation_only"
    assert not da_ho_tro("curved_oblique_section")
    assert "MÔ HÌNH: chưa đo" in nl.bang_chung
