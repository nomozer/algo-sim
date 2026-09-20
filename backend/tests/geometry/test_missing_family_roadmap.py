# -*- coding: utf-8 -*-
"""`MISSING_FAMILY_ROADMAP_REFRESH` — ma trận năng lực phải KIỂM ĐƯỢC.

**0 lượt gọi model.**

Một bản đồ năng lực không kiểm được là một **danh sách mong muốn**: nó đúng
đúng một lần, vào hôm viết ra. Bộ test này đọc `CAPABILITY_MATRIX.json` rồi
đối chiếu **từng khẳng định** với mã nguồn và registry đang chạy.

⚠️ Nó cố ý kiểm CẢ HAI CHIỀU:
· thứ ma trận nói **đã sẵn sàng** thì phải thật sự có mặt;
· thứ ma trận nói **chưa có** thì phải thật sự vắng — vì đó mới là chỗ một
  bản đồ cũ nói dối, và nói dối theo hướng làm người đọc bỏ lỡ việc dễ.
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[3]
MT = (GOC / "docs" / "evaluation" / "geometry"
      / "missing-family-roadmap-refresh" / "CAPABILITY_MATRIX.json")


@pytest.fixture(scope="module")
def mt() -> dict:
    assert MT.exists(), "thiếu CAPABILITY_MATRIX.json"
    return json.loads(MT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ho(mt) -> dict:
    return {h["FAMILY"]: h for h in mt["families"]}


# ══ A · HÌNH DẠNG — mỗi hàng đủ mười một cột của §5 ═════════════════════
def test_01_moi_hang_du_cot(mt):
    can = {"FAMILY", "CURRENT_STATUS", "IR_PATH", "KERNEL_AUTHORITY",
           "CHECKER", "TRACE", "SCENE3D", "MODEL_DISCOVERABILITY_EVIDENCE",
           "ACCEPTANCE_EVIDENCE", "KNOWN_BOUNDARY", "CODE_OR_TEST_CITATION"}
    for h in mt["families"]:
        assert can <= set(h), (h["FAMILY"], sorted(can - set(h)))


def test_02_bon_chieu_va_muc_bang_chung(mt):
    hop_le = {"YES", "NO", "PARTIAL", "NOT_MEASURED"}
    muc = {"CODE_PROVED", "TEST_PROVED", "LIVE_MEASURED", "HYPOTHESIS",
           "NOT_MEASURED"}
    for h in mt["families"]:
        for c in ("SYSTEM_EXPRESSIBLE", "DETERMINISTICALLY_CORRECT",
                  "MODEL_DISCOVERABLE", "STABILITY_UNDER_ACCEPTANCE"):
            assert h[c] in hop_le, (h["FAMILY"], c, h[c])
        assert h["MUC_BANG_CHUNG"] in muc, h["FAMILY"]


def test_03_trang_thai_thuoc_bang_da_chuan_hoa(mt):
    cho = {"UNSUPPORTED", "EXPRESSIBLE_ONLY", "FOUNDATION_ONLY",
           "DEVELOPMENT_CONFIRMED", "SUPPORTED", "OUT_OF_SCOPE"}
    for h in mt["families"]:
        assert h["CURRENT_STATUS"] in cho, (h["FAMILY"], h["CURRENT_STATUS"])


def test_04_TONG_KET_dan_dung_tu_cac_hang(mt):
    """Tổng kết phải DẪN XUẤT, không được gõ tay — hai bảng thì hai bảng lệch."""
    that: dict[str, list[str]] = {}
    for h in mt["families"]:
        that.setdefault(h["CURRENT_STATUS"], []).append(h["FAMILY"])
    for k, v in mt["TONG_KET"].items():
        assert sorted(v) == sorted(that.get(k, [])), k


def test_05_khong_ho_nao_khai_STABILITY(mt):
    """Chưa lượt acceptance nào chạy, nên KHÔNG hàng nào được khai khác
    `NOT_MEASURED`. Đây là chỗ một bản đồ dễ hứa quá nhất."""
    for h in mt["families"]:
        assert h["STABILITY_UNDER_ACCEPTANCE"] == "NOT_MEASURED", h["FAMILY"]


# ══ B · DANH TÍNH — ma trận nói về ĐÚNG bản mã này ══════════════════════
def test_06_danh_tinh_khop_he_hien_tai(mt):
    from app.main import CACHE_VERSION

    # Ma tran ghi `93` -- danh tinh luc LAP BAN DO, giu nguyen. He o `94`
    # sau `OBLIQUE_CONE_SECTION_FOUNDATION`, dung ho ma ma tran da chon.
    assert mt["cache_version"] == "93"
    # ⚠️ 94 → 95 (`DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH`, 2026-09-10):
    #    bump vì NỘI DUNG envelope `ok` đổi (nhãn `ellipse3`), **không** vì
    #    bề mặt mô hình — năm băm model-facing giữ nguyên từng byte, và
    #    chúng mới là thứ ô này bảo vệ.
    # ⚠️ 95 → 96 (`SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE`, 2026-09-20):
    #    bump vì PHÁN QUYẾT PHỤC VỤ đổi — cổng phủ nghĩa vụ TRỰC QUAN biến một
    #    lớp kết quả `served` → `rejected`. Cũng KHÔNG đụng bề mặt mô hình: năm
    #    băm model-facing giữ nguyên từng byte, và chúng mới là thứ ô này bảo vệ.
    # ⚠️ 96 → 97 (`SECTION_PROVENANCE_NORMALIZATION`, 2026-09-20): bump vì NỘI
    #    DUNG CẢNH trong envelope `ok` đổi (`polygon3` đủ bằng chứng plane–solid
    #    nay ra `section`). Cũng KHÔNG đụng bề mặt mô hình: năm băm model-facing
    #    giữ nguyên từng byte, và chúng mới là thứ ô này bảo vệ.
    assert CACHE_VERSION == "97"


# ══ C · THỨ ma trận nói ĐÃ SẴN SÀNG thì phải CÓ MẶT ════════════════════
def test_07_ellipse3_di_TRON_duong_san_pham():
    """Bốn tầng, bốn thẩm quyền khác nhau — ma trận khai `SCENE3D_GAP = KHONG`
    cho `oblique_cone_section` dựa trên đúng bốn ô này."""
    from app.simulation.semantic_program.ir_static_check import ELIP
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO
    from app.simulation.semantic_program.contract import MemoryType

    assert ELIP == "ellipse3"
    # ① kiểu bộ nhớ
    assert "ellipse3" in MemoryType.__args__
    # ② hợp đồng phép đo — `area` NHẬN ellipse3
    assert "ellipse3" in BANG_PHEP_DO["area"].kieu_of
    # ③ cảnh backend ánh xạ ellipse3 → render kind `ellipse`
    src = (GOC / "backend" / "app" / "simulation" / "semantic_program"
           / "scene3d.py").read_text(encoding="utf-8")
    assert '"ellipse3": "ellipse"' in src
    # ④ frontend biết vẽ `ellipse`
    fe = (GOC / "frontend" / "src" / "simulations" / "domains" / "geometry"
          / "scene3d-model.ts").read_text(encoding="utf-8")
    assert '"ellipse",' in fe


def test_08_checker_area_DAN_XUAT_nen_tu_nhan_kieu_moi():
    """Ma trận khai `CHECKER_GAP = KHONG`. Điều đó chỉ đúng nếu `check_area`
    **dẫn** kiểu chủ thể từ `BANG_PHEP_DO` thay vì liệt kê tay."""
    from app.simulation.semantic_program import geometry_obligations as GO

    src = Path(GO.__file__).read_text(encoding="utf-8")
    i = src.index("def check_area")
    than = src[i:i + 2500]
    assert "kieu_chu_the_nghia_vu" in than
    assert "area" in GO.GEOMETRY_CHECKERS


def test_09_phep_giao_elip_DA_CO_chu_ky():
    """⚠️ **ĐỔI 2026-09-08.** Bản trước ghim `if s.kind != "cylinder": raise`
    và chú thích *"nhánh cone đã mở? cập nhật ma trận"* — tức nó ghim một
    **khoảng trống**. `OBLIQUE_CONE_SECTION_FOUNDATION` đã mở nhánh ấy, nên ô
    này chuyển sang ghim **năng lực**: cùng một chữ ký phép, nay phục vụ hai
    họ, và `NEW_IR_OPERATIONS = 0` của roadmap thành sự thật đo được."""
    from app.simulation.geometry import curved as CV

    assert hasattr(CV, "intersect_plane_curved_ellipse")
    src = Path(CV.__file__).read_text(encoding="utf-8")
    assert 'if s.kind == "cone":' in src
    assert hasattr(CV, "phan_xu_conic") and hasattr(CV, "_elip_non")
    # Vẫn là MỘT phép: không có `intersect_plane_cone_ellipse` thứ hai.
    assert not hasattr(CV, "intersect_plane_cone_ellipse")


# ══ D · THỨ ma trận nói CHƯA CÓ thì phải THẬT SỰ VẮNG ══════════════════
#
# Chiều này quan trọng hơn chiều trên: một bản đồ cũ nói dối theo hướng làm
# người đọc **bỏ lỡ việc dễ** (`curved_oblique_section` từng bị khai
# `unsupported` vì *"không có kiểu conic trong IR"* — câu ấy SAI).
def test_10_KHONG_co_tham_quyen_tich_phan(ho):
    assert ho["solid_of_revolution_general"]["CURRENT_STATUS"] == "OUT_OF_SCOPE"
    goc = GOC / "backend" / "app" / "simulation"
    dinh = []
    for p in goc.rglob("*.py"):
        t = p.read_text(encoding="utf-8").lower()
        if "sympy" in t or "def tich_phan" in t or "def integrate" in t:
            dinh.append(p.name)
    assert dinh == [], dinh
    # …và không có kiểu BIỂU THỨC HÀM nào trong `MemoryType`.
    from app.simulation.semantic_program.contract import MemoryType

    assert not {"function", "expression", "curve"} & set(MemoryType.__args__)


def test_11_KHONG_co_tham_quyen_boolean(ho):
    assert ho["composite_boolean"]["CURRENT_STATUS"] == "OUT_OF_SCOPE"
    hh = GOC / "backend" / "app" / "simulation" / "geometry"
    dinh = []
    for p in hh.glob("*.py"):
        t = p.read_text(encoding="utf-8").lower()
        for k in ("def hop_khoi", "def hieu_khoi", "def csg", "def boolean"):
            if k in t:
                dinh.append(f"{p.name}:{k}")
    assert dinh == [], dinh


def test_12_dieu_kien_TOAN_CUC_van_chua_kiem_duoc():
    """Lý do `composite_boolean` ngoài phạm vi KHÔNG phải *"chưa ai làm"* mà là
    *"nó cần đúng điều kiện hệ ĐÃ KHAI là không kiểm được"*: hai MẶT KHÁC NHAU
    xuyên qua nhau — thứ biên CSG sinh ra thường xuyên."""
    from app.simulation.geometry import section as SEC

    doc = SEC.dinh_huong_bien.__doc__ or ""
    assert "xuyên qua nhau" in doc and "KHÔNG kiểm" in doc
    assert hasattr(SEC, "kiem_mat_phang_don")


# ══ E · PHÂN XỬ CONIC — phép đo BÁC ghi chú registry ═══════════════════
#
# Registry ghi *"nón cắt xiên cho elip, parabol hoặc hyperbol tuỳ độ dốc — ba
# nhánh chưa phân xử"*. Đó là câu về CÔNG VIỆC CHƯA LÀM. Ba ô dưới đây đo rằng
# nó KHÔNG đồng thời là một câu về MIỀN SỐ.
def _phan_xu(r2: F, h2: F, nu2: F, nn: F, uu: F) -> str:
    trai, phai = nu2 * (r2 + h2), r2 * nn * uu
    return "ellipse" if trai > phai else ("parabol" if trai == phai
                                          else "hyperbol")


@pytest.mark.parametrize("m,mong", [
    (F(1, 4), "ellipse"), (F(3, 4), "ellipse"),
    (F(4, 3), "parabol"), (F(2), "hyperbol"), (F(3), "hyperbol"),
])
def test_13_phan_xu_conic_la_phep_so_HUU_TI(m, mong):
    """Nón `r = 3, h = 4`; mặt phẳng `z = m·x + c` ⇒ `n = (−m, 0, 1)`,
    `u = (0,0,1)`. Không một phép khai căn nào."""
    r2, h2 = F(9), F(16)
    assert _phan_xu(r2, h2, F(1), m * m + 1, F(1)) == mong
    # Kiểm CHÉO bằng dấu của `k = 1 − m²·tan²α`, một đường dẫn khác hẳn.
    k = 1 - m * m * (r2 / h2)
    assert (mong == "ellipse") == (k > 0)
    assert (mong == "parabol") == (k == 0)


@pytest.mark.parametrize("m,c,a2,b2", [
    (F(1, 4), F(4), F(626688, 61009), F(2304, 247)),
    (F(1, 2), F(6), F(20736, 605), F(1296, 55)),
    (F(0), F(4), F(9), F(9)),
    (F(-1, 3), F(5), F(160, 9), F(15)),
])
def test_14_hai_ban_truc_cua_thiet_dien_non_deu_HUU_TI(m, c, a2, b2):
    """`a² = c²t(1+m²)/k²` · `b² = c²t/k` với `t = r²/h²`, `k = 1 − m²t`.

    Cả hai `Fraction` ⇒ diện tích `π√(a²b²)` nằm trọn trong `Radical`. Bốn bộ
    số này đã đối chiếu một oracle SỐ độc lập (lấy mẫu 400 000 điểm trên giao
    tuyến rồi shoelace 3D), lệch `~1e-9`.
    """
    t = F(9, 16)
    k = 1 - m * m * t
    assert k > 0
    assert c * c * t * (1 + m * m) / (k * k) == a2
    assert c * c * t / k == b2
    assert isinstance(a2 * b2, F)


def test_15_dien_tich_thiet_dien_non_o_trong_mien_Radical():
    """`Radical(he·√can·π^mu)` chở được `π√(hữu tỉ)` — nên không cần miền số
    mới. Đây là ô biến `NUMBER_DOMAIN_GAP = KHONG` thành một phép kiểm."""
    from app.simulation.geometry.radical import Radical, display

    # Ca `m = 0, c = 4`: a² = b² = 9 ⇒ S = 9π.
    assert display(Radical(he=F(9), can=1, mu=1)) == "9π"
    # Ca có căn: a²b² = 800/3·… — dạng tổng quát vẫn là π√(hữu tỉ).
    r = Radical(he=F(1), can=2, mu=1)
    assert "π" in display(r) and "√2" in display(r)


# ══ F · QUYẾT ĐỊNH phải khớp bằng chứng, không khớp mong muốn ═══════════
def test_16_quyet_dinh_DA_THUC_HIEN__pham_vi_tinh_nang_dong(mt, ho):
    """⚠️ **ĐỔI 2026-09-08.** Bản trước ghim quyết định *"chọn
    `oblique_cone_section`, `FEATURE_SCOPE_COMPLETE = NO`"*.
    `OBLIQUE_CONE_SECTION_FOUNDATION` đã làm xong họ ấy, nên ma trận cập nhật
    và ô này ghim **trạng thái sau khi thực hiện**.

    Lịch sử quyết định giữ trong `QUYET_DINH.LICH_SU` — xoá nó là xoá bằng
    chứng rằng phạm vi đóng lại vì đã LÀM XONG, không phải vì đổi ý.
    """
    q = mt["QUYET_DINH"]
    assert q["FEATURE_SCOPE_COMPLETE"] == "YES"
    assert q["NEXT_FOUNDATION_FAMILY"] is None
    assert q["NEXT_ACTION"] == "THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION"
    assert "oblique_cone_section" in q["LICH_SU"]["2026-09-08_lap_ban_do"]

    # Họ từng được chọn nay ĐÃ có foundation, và GAP của nó khai đã đóng.
    chon = ho["oblique_cone_section"]
    assert chon["CURRENT_STATUS"] == "FOUNDATION_ONLY"
    assert chon["GAP"]["NEW_MEMORY_TYPES_REQUIRED"] == 0
    assert chon["GAP"]["NEW_IR_OPERATIONS_REQUIRED"] == 0
    assert "OBLIQUE_CONE_SECTION_FOUNDATION" in chon["GAP"]["DA_DONG"]

    # KHÔNG còn họ nào ở `EXPRESSIBLE_ONLY` hay `UNSUPPORTED`.
    assert mt["TONG_KET"]["EXPRESSIBLE_ONLY"] == []
    assert mt["TONG_KET"]["UNSUPPORTED"] == []


def test_17_moi_ho_OUT_OF_SCOPE_deu_neu_LY_DO_KIEN_TRUC(ho):
    """*"Chưa ai làm"* KHÔNG phải một lý do ngoài phạm vi. Mỗi hàng
    `OUT_OF_SCOPE` phải nêu một khoảng trống KIẾN TRÚC đo được."""
    for ten, h in ho.items():
        if h["CURRENT_STATUS"] != "OUT_OF_SCOPE":
            continue
        assert "GAP" in h, ten
        assert h["MUC_BANG_CHUNG"] == "CODE_PROVED", ten
        assert len(h["KNOWN_BOUNDARY"]) > 60, ten


def test_18_ho_da_DEVELOPMENT_CONFIRMED_deu_co_artifact_LIVE(ho):
    ra = GOC / "docs" / "evaluation" / "geometry"
    for ten in ("nonconvex_polyhedron", "oblique_cylinder_ellipse"):
        h = ho[ten]
        assert h["MUC_BANG_CHUNG"] == "LIVE_MEASURED", ten
        assert h["MODEL_DISCOVERABLE"] == "YES", ten
    # …và artifact ấy có thật trên đĩa.
    assert (ra / "nonconvex-polyhedron-model-discoverability"
            / "SCORING.json").exists()
    assert (ra / "oblique-ellipse-final-card-rerun" / "SCORING.json").exists()


def test_19_registry_san_pham_va_ma_tran_KHONG_mau_thuan(ho):
    """Ma trận chia họ mịn hơn registry (registry gom `cone` với thiết diện
    xiên của nó). Ô này khoá rằng chúng không nói NGƯỢC nhau ở phần chung."""
    from app.simulation.product_capability import NANG_LUC_SAN_PHAM as R

    assert R["polyhedron"].trang_thai == "supported"
    assert R["section"].trang_thai == "supported"
    for k in ("ball", "cylinder", "cone", "nonconvex_polyhedron",
              "curved_oblique_section"):
        assert R[k].trang_thai == "foundation_only", k
    for k in ("solid_of_revolution", "composite_subtractive"):
        assert R[k].trang_thai == "unsupported", k
    # ⚠️ Ma trận KHÔNG nâng registry: `nonconvex_polyhedron` và
    # `oblique_cylinder_ellipse` đạt `DEVELOPMENT_CONFIRMED` ở ma trận, nhưng
    # năng lực SẢN PHẨM vẫn `foundation_only` — hai câu khác nhau, và wave này
    # không đổi câu thứ hai.
    assert ho["nonconvex_polyhedron"]["CURRENT_STATUS"] == "DEVELOPMENT_CONFIRMED"
    assert ho["oblique_cylinder_ellipse"]["ACCEPTANCE_EVIDENCE"].startswith(
        "DEVELOPMENT_REGRESSION_SIGNAL")
