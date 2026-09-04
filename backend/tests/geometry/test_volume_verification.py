# -*- coding: utf-8 -*-
"""CHECKER `volume` — đóng khoảng safe-serve cho khối cong. **0 lượt gọi model.**

    `VOLUME_VERIFICATION_BRIDGE`, 2026-09-03.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

`CURVED_OBLIGATION_COVERAGE_BRIDGE` nới `volume` sang `curved_solid` ở **cổng
phủ**; `check_volume` vẫn đòi `Polyhedron`. Probe ecgônômi §18 phơi ra hậu quả
bằng quota thật:

    ball_1   chương trình ĐÚNG · engine ra R = 6, V = 288π
             postconditions · postcondition_violated · ['cần một `solid`']
             executable True · servable **False**

Hệ tính xong rồi từ chối phục vụ chính con số nó vừa tính. Wave này đóng đúng
khoảng đó, và không đóng gì khác.

─── ĐIỀU FILE NÀY CANH, NGOÀI VIỆC CHECKER CHẠY ───────────────────────────

**Checker phải CÓ RĂNG trên cả ba hình.** `V2/V4/V6` cho giá trị sai và đòi bác.
Một checker chỉ biết nói PASS là một checker chưa được chứng minh — và đây là
lần thứ hai kho này phải viết câu ấy ra (`RADIUS_VERIFICATION_BRIDGE` là lần
đầu).

**Nhân chứng phải đi ĐÚNG đường sản phẩm với ĐÚNG bộ nghĩa vụ.** Nhân chứng cũ
(`test_radius_verification.test_T6`) đọc `288π` từ `final_memory` trong khi chỉ
truyền nghĩa vụ `radius` — nó **chưa bao giờ** đi qua `check_volume`, mà lại đọc
như một lượt kiểm đầu-cuối cho thể tích. `test_A1` ở đây truyền **cả hai** nghĩa
vụ, đúng như `RequestContract` mà `analyze` đã sinh ra trong probe.
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry.curved import CurvedSolid
from app.simulation.geometry.exact import Vec3
from app.simulation.geometry.radical import radical
from app.simulation.geometry.section import box
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS,
    check_volume,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

v = Vec3.of
PROBE = (Path(__file__).resolve().parents[3]
         / "docs/evaluation/geometry/curved-ergonomics-probe"
         / "stage_8a_one_shot.json")


def _ob(container: str, witness: str, **params) -> Obligation:
    return Obligation(kind="volume", container=container,
                      params={"witness": witness, **params})


# Ba khối cong với thể tích ĐÓNG (hữu tỉ × π), dựng bằng ba điểm neo hữu tỉ.
#   cầu    V = 4/3·πR³   R = 6            → 288π
#   trụ    V = πr²h      r² = 5, h = 3    →  15π
#   nón    V = 1/3·πr²h  r² = 9, h = 4    →  12π
# Trụ cố ý lấy `r = √5` VÔ TỈ: toạ độ vẫn ở lại ℚ³, và một bộ chấm dùng float
# sẽ nói dối ở đúng ca này.
BA_HINH = [
    ("ball", v(0, 0, 0), None, v(6, 0, 0), radical(288, 1, mu=1)),
    ("cylinder", v(0, 0, 0), v(0, 0, 3), v(1, 2, 0), radical(15, 1, mu=1)),
    ("cone", v(0, 0, 0), v(0, 0, 4), v(3, 0, 0), radical(12, 1, mu=1)),
]


# ══ V1 · V3 · V5 — THỂ TÍCH ĐÚNG ĐƯỢC NHẬN ═══════════════════════════════
@pytest.mark.parametrize("loai,neo,dinh,vanh,V", BA_HINH)
def test_V1_V3_V5_the_tich_cong_DUNG_duoc_nhan(loai, neo, dinh, vanh, V):
    """`SHAPE_SPECIFIC_VOLUME_CHECKERS = 0` — chứng minh bằng cách chạy cùng
    MỘT hàm trên cả ba `curved_kind`."""
    s = CurvedSolid(loai, neo, dinh, vanh)
    assert check_volume({"S": s, "V": V}, _ob("S", "V")) is None


@pytest.mark.parametrize("loai,neo,dinh,vanh,V", BA_HINH)
def test_V1b_gia_tri_MONG_cua_de_cung_di_qua_cua_ay(loai, neo, dinh, vanh, V):
    """Hai đường vào đều phải chạy: giá trị chương trình KHAI (`witness`) và
    giá trị ĐỀ MONG (`params.value`)."""
    from app.simulation.geometry.radical import display

    s = CurvedSolid(loai, neo, dinh, vanh)
    assert check_volume({"S": s}, _ob("S", "", value=display(V))) is None


# ══ V2 · V4 · V6 — CHECKER CÓ RĂNG ═══════════════════════════════════════
@pytest.mark.parametrize("loai,neo,dinh,vanh,V", BA_HINH)
def test_V2_V4_V6_the_tich_cong_SAI_bi_bac(loai, neo, dinh, vanh, V):
    s = CurvedSolid(loai, neo, dinh, vanh)
    for sai in (F(1), radical(999, 1, mu=1), radical(1, 2)):
        loi = check_volume({"S": s, "V": sai}, _ob("S", "V"))
        assert loi and "không khớp" in loi, (loai, sai, loi)


def test_V2b_hai_hinh_KHAC_nhau_khong_duoc_nhan_lan_nhau():
    """Ca mà một checker 'chỉ cần ra một con số π' sẽ nuốt: trụ và nón cùng
    `r² = 9, h = 4` lệch nhau đúng hệ số 3."""
    tru = CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 4), v(3, 0, 0))
    non = CurvedSolid("cone", v(0, 0, 0), v(0, 0, 4), v(3, 0, 0))
    assert check_volume({"S": tru, "V": radical(36, 1, mu=1)},
                        _ob("S", "V")) is None
    assert check_volume({"S": non, "V": radical(12, 1, mu=1)},
                        _ob("S", "V")) is None
    # Thể tích của hình KIA phải bị bác ở cả hai chiều.
    assert check_volume({"S": non, "V": radical(36, 1, mu=1)},
                        _ob("S", "V")) is not None
    assert check_volume({"S": tru, "V": radical(12, 1, mu=1)},
                        _ob("S", "V")) is not None


# ══ §9 — HỒI QUY ĐA DIỆN: KHÔNG ĐƯỢC ĐỔI ═════════════════════════════════
def test_R1_da_dien_dung_van_PASS():
    assert check_volume({"K": box(2, 3, 5), "V": F(30)},
                        _ob("K", "V")) is None


def test_R2_da_dien_SAI_van_FAIL():
    loi = check_volume({"K": box(2, 3, 5), "V": F(31)}, _ob("K", "V"))
    assert loi and "không khớp" in loi, loi


def test_R3_khong_khai_gia_tri_van_la_MUC_YEU_khong_phai_PASS_gia():
    """Không có `witness` lẫn `value` ⇒ chỉ kiểm được cấu trúc. Trả `None` ở
    đây là *"không có gì để so"*, không phải *"đã kiểm và đúng"* — hai câu ấy
    khác nhau, và §9 cấm làm nhoè chúng bằng cách nhận bừa một con số."""
    assert check_volume({"K": box(1, 1, 1)}, _ob("K", "")) is None
    assert check_volume({"K": box(1, 1, 1), "V": F(1)},
                        _ob("K", "V")) is None
    assert check_volume({"K": box(1, 1, 1), "V": F(2)},
                        _ob("K", "V")) is not None


@pytest.mark.parametrize("gt", [v(1, 2, 3), F(5), None, "x", (v(0, 0, 0),)])
def test_R4_chu_the_sai_van_bi_bac(gt):
    loi = check_volume({"X": gt, "V": F(1)}, _ob("X", "V"))
    assert loi and "solid" in loi, loi


# ══ §8 — NHÂN CHỨNG SAFE-SERVE, ĐÚNG ĐƯỜNG SẢN PHẨM ══════════════════════
def test_A1_ball_1_cua_probe_18_nay_SERVABLE():
    """`DEV_PROBE_BALL_1_SYSTEM_BLOCKER = CLOSED`.

    Chương trình VÀ `RequestContract` lấy nguyên văn từ artifact §18 — cả hai
    nghĩa vụ (`radius`, `volume`) đi qua đúng cổng của chúng. Trước bản vá:
    `servable=False`, chặn ở `postconditions` với *'cần một `solid`'*.

    ⚠️ Artifact §18 là **bằng chứng của bản hệ CŨ** và không bị viết lại;
    `ONE_SHOT_CORRECT = 0` của nó vẫn đúng cho bản ấy. Đây là một lượt CHẤM LẠI
    tất định, không phải một điểm số mới.
    """
    from app.simulation.geometry.radical import display

    r = next(x for x in json.loads(PROBE.read_text(encoding="utf-8"))["ca"]
             if x["id"] == "ball_1")
    kq = verify_and_compile(
        RequestContract.model_validate(r["request_contract"]),
        SemanticProgramSpec.model_validate(r["chuong_trinh"]))

    assert kq.executable, f"bị chặn ở '{kq.stage_reached}': {kq.reason}"
    assert kq.servable, f"vẫn không phục vụ được: {kq.reason} · {kq.weak_kinds}"
    assert not kq.weak_kinds, kq.weak_kinds
    so = {display(x) for x in (kq.final_memory or {}).values()
          if type(x).__name__ in ("Fraction", "Radical")}
    assert {"6", "288π"} <= so, so


def test_A2_nghia_vu_volume_mot_minh_cung_di_het_duong():
    """Tách riêng `volume` khỏi `radius`: nếu chỉ ca hai-nghĩa-vụ xanh thì
    không biết cổng nào đã thật sự chạy."""
    r = next(x for x in json.loads(PROBE.read_text(encoding="utf-8"))["ca"]
             if x["id"] == "ball_1")
    rc = RequestContract.model_validate(r["request_contract"])
    chi_volume = rc.model_copy(update={
        "obligations": tuple(o for o in rc.obligations if o.kind == "volume")})
    kq = verify_and_compile(
        chi_volume, SemanticProgramSpec.model_validate(r["chuong_trinh"]))
    assert kq.executable and kq.servable, f"{kq.stage_reached}: {kq.reason}"


def test_A3_nhan_chung_ay_CO_RANG_neu_hinh_khac_di():
    """Nhân chứng phải bác được. Đổi `A` cho `R = 3` thì `V = 36π`, và nghĩa vụ
    khai `288π` phải trượt — nếu không, `test_A1` chỉ chứng minh 'chạy được'."""
    r = next(x for x in json.loads(PROBE.read_text(encoding="utf-8"))["ca"]
             if x["id"] == "ball_1")
    raw = json.loads(json.dumps(r["chuong_trinh"]))
    for d in raw["memory_declarations"]:
        if d["name"] == "A":
            d["initial_value"] = [3, 0, 0]
    rc = RequestContract.model_validate(r["request_contract"])
    obs = tuple(
        o.model_copy(update={"params": {**o.params, "value": "288π"}})
        if o.kind == "volume" else o
        for o in rc.obligations)
    kq = verify_and_compile(
        rc.model_copy(update={"obligations": obs}),
        SemanticProgramSpec.model_validate(raw))
    assert not kq.servable, "checker nuốt một thể tích SAI"


# ══ §13 · §14 — KHÔNG MỞ THÊM GÌ ═════════════════════════════════════════
def test_Z1_khong_them_checker_nao_khac():
    """Wave này chỉ nới `volume`. Thêm tiện tay một checker khác là mở một
    tuyên bố năng lực không ai xin."""
    assert set(GEOMETRY_CHECKERS) == {
        "point_on_line", "point_on_plane", "parallel", "perpendicular",
        "coplanar", "section_matches", "distance", "angle", "volume",
        # +`area`, +`lateral_area` 2026-09-04
        # (`ANALYZE_OBLIGATION_SURFACE_COMPLETION`): preflight V3 đo được
        # 14/18 ca dương bị `analyze` loại im lặng vì thiếu đúng hai kind này.
        "radius", "area", "lateral_area"}
    # `lateral_area` ĐÃ RỜI danh sách cấm 2026-09-04 — xem chú thích trong tập
    # trên. `surface_area` thì Ở LẠI, và lý do vẫn nguyên: `S_tp` của nón có
    # hai căn thức khác nhau, miền số cố ý từ chối tổng ấy.
    for cam in ("surface_area", "skew_lines", "line_in_plane"):
        assert cam not in GEOMETRY_CHECKERS


def test_Z2_radius_khong_bi_dong_cham():
    """§14 — `radius` giữ nguyên ngữ nghĩa, kể cả trên bán kính vô tỉ."""
    from app.simulation.geometry.curved import Circle3
    from app.simulation.semantic_program.geometry_obligations import check_radius

    def ob_r(c, w):
        return Obligation(kind="radius", container=c, params={"witness": w})

    assert check_radius({"C": Circle3(v(0, 0, 0), v(0, 0, 1), F(16)), "R": F(4)},
                        ob_r("C", "R")) is None
    s = CurvedSolid("ball", v(0, 0, 0), None, v(1, 1, 1))   # R = √3
    assert check_radius({"S": s, "R": radical(1, 3)}, ob_r("S", "R")) is None
    assert check_radius({"S": s, "R": F(2)}, ob_r("S", "R")) is not None


def test_Z3_MOT_tham_quyen_tuong_thich_kieu():
    """`MEASURE_SUBJECT_COMPATIBILITY_AUTHORITIES = 1`.

    Checker trả lời *"con số này có đúng không"*; `BANG_PHEP_DO` trả lời *"chủ
    thể này có hợp không"*. Bản vá này **không** đụng tới câu thứ hai — nó
    không thêm `VOLUME_ALLOWED_TYPES` nào cả.
    """
    import inspect

    from app.simulation.semantic_program.measure_contract import (
        BANG_PHEP_DO,
        kieu_chu_the_nghia_vu,
    )
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    assert OBLIGATION_KINDS["volume"] == kieu_chu_the_nghia_vu("volume")
    assert OBLIGATION_KINDS["volume"] == frozenset(
        BANG_PHEP_DO["volume"].kieu_of) == {"solid", "curved_solid"}
    # Checker hỏi LỚP RUNTIME (`isinstance`), không chép danh sách kiểu khai.
    than = inspect.getsource(check_volume).split('"""')[-1]
    assert '"curved_solid"' not in than and '"solid"' not in than


def test_Z4_dieu_phoi_the_tich_KHONG_phan_nhanh_theo_hinh():
    """`CHECK_VOLUME_FAMILY_DISPATCH = 0` — ba công thức thuộc `KHOI_CONG`,
    không thuộc checker lẫn bộ điều phối."""
    import inspect

    from app.simulation.semantic_program.geometry_exec import volume_of

    for fn in (check_volume, volume_of):
        than = inspect.getsource(fn).split('"""')[-1]
        for hinh in ("ball", "cylinder", "cone"):
            assert f'"{hinh}"' not in than, (fn.__name__, hinh)


def test_Z5_duong_chay_va_duong_cham_dung_CHUNG_mot_tham_quyen():
    """Bản sao thứ hai của phép điều phối chính là con bug wave này đi dọn.
    Cả hai phải gọi `volume_of`, không ai được tự `isinstance` rồi tự tính."""
    import inspect

    from app.simulation.semantic_program import geometry_exec

    assert "volume_of" in inspect.getsource(check_volume)
    do = inspect.getsource(geometry_exec._do)
    assert "volume_of(a)" in do
    assert "CV.the_tich" not in do, "đường chạy tự tính lại thay vì đi qua cửa chung"
