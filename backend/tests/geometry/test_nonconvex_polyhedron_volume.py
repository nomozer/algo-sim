# -*- coding: utf-8 -*-
"""`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` — thể tích đúng cho khối LÕM.

─── LỖI ĐÃ TÁI HIỆN, KHÔNG PHẢI GIẢ ĐỊNH ─────────────────────────────────

Chóp đáy lõm `A(0,0,0) B(4,0,0) C(4,4,0) D(2,1,0) E(0,4,0)`, đỉnh `S(2,½,6)`.
Ba oracle độc lập cho **20**; mã cũ cho **28** — và trả `served` với 28, vì
runtime lẫn checker dùng CHUNG một hàm sai. Một thẩm quyền duy nhất bảo vệ
được tính NHẤT QUÁN, không bảo vệ được tính ĐÚNG.

Gốc: `abs` lấy cho TỪNG tứ diện. Với khối lồi mọi đóng góp cùng dấu nên vô
hại; với khối lõm, phần lõm phải đóng góp ÂM để trừ đi.

─── PHẠM VI ĐƯỢC CHỨNG MINH ──────────────────────────────────────────────

Đa diện **đóng, định hướng được, liên thông** — kiểm bằng ba điều kiện TỔ HỢP
trên bảng mặt. ⚠️ Tự giao trong không gian **KHÔNG** kiểm được, nên bao đóng
V1 khai theo đường DỰNG chứ không khai là *"mọi đa diện không lồi"*.
"""
from __future__ import annotations

import json
from fractions import Fraction as F

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.geometry import measure as M
from app.simulation.geometry import section as SEC
from app.simulation.geometry.exact import GeometryError, Vec3
from app.simulation.geometry.radical import display
from app.simulation.geometry.section import Polyhedron, the_tich_da_dien
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.geometry_exec import volume_polyhedron
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.simulation_state import dependency_graph


def v(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


A, B, C, D, E = v(0, 0, 0), v(4, 0, 0), v(4, 4, 0), v(2, 1, 0), v(0, 4, 0)
S = v(2, F(1, 2), 6)
DAY = [A, B, C, D, E]
#: Đáy khai NGƯỢC để hướng ra ngoài; năm mặt bên.
MAT_LOM = tuple([(4, 3, 2, 1, 0)] + [(i, (i + 1) % 5, 5) for i in range(5)])
LOM = Polyhedron((A, B, C, D, E, S), MAT_LOM)

TU_DIEN = Polyhedron((v(0, 0, 0), v(1, 0, 0), v(0, 1, 0), v(0, 0, 1)),
                     ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)))
_H = (v(0, 0, 0), v(2, 0, 0), v(2, 3, 0), v(0, 3, 0),
      v(0, 0, 5), v(2, 0, 5), v(2, 3, 5), v(0, 3, 5))
HOP = Polyhedron(_H, ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
                      (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)))
CHOP_VUONG = Polyhedron(
    (v(0, 0, 0), v(2, 0, 0), v(2, 2, 0), v(0, 2, 0), v(1, 1, 3)),
    ((0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)))
CHOP_TAM_GIAC = Polyhedron(
    (v(0, 0, 0), v(3, 0, 0), v(0, 3, 0), v(1, 1, 4)),
    ((0, 1, 2), (0, 1, 3), (1, 2, 3), (2, 0, 3)))


def _doi(kh: Polyhedron, d: Vec3) -> Polyhedron:
    return Polyhedron(tuple(p + d for p in kh.vertices), kh.faces)


def _scale(kh: Polyhedron, s) -> Polyhedron:
    return Polyhedron(tuple(v(p.x * s, p.y * s, p.z * s) for p in kh.vertices),
                      kh.faces)


# ══ §5 · BA ORACLE ĐỘC LẬP ═════════════════════════════════════════════
def test_01_ba_oracle_doc_lap_cung_cho_20():
    """Neo con số `20` vào ba đường tính KHÁC NHAU, không vào kernel."""
    # ① shoelace CÓ DẤU của đáy × chiều cao ÷ 3
    sh = sum(DAY[i].x * DAY[(i + 1) % 5].y - DAY[(i + 1) % 5].x * DAY[i].y
             for i in range(5))
    assert abs(sh) / 2 == 10
    assert abs(sh) / 2 * 6 / 3 == 20

    # ② tổng determinant CÓ DẤU của các tứ diện quạt
    from app.simulation.geometry.exact import det3

    tong = sum(det3(DAY[0] - S, DAY[i] - S, DAY[i + 1] - S)
               for i in range(1, 4))
    assert abs(tong) / 6 == 20

    # ③ phân rã đáy thành hai miền LỒI không chồng nhau: ABCD và ADE
    def _dt(pts):
        s = sum(pts[i].x * pts[(i + 1) % len(pts)].y
                - pts[(i + 1) % len(pts)].x * pts[i].y
                for i in range(len(pts)))
        return abs(s) / 2

    assert _dt([A, B, C, D]) + _dt([A, D, E]) == 10


# ══ §12 · CA BẮT BUỘC ══════════════════════════════════════════════════
def test_02_day_LOM_cho_dung_20():
    assert the_tich_da_dien(LOM) == 20
    assert volume_polyhedron(LOM) == 20
    assert M.volume_pyramid_fan(S, DAY) == 20


def test_03_cyclic_shift_thu_tu_day_khong_doi_ket_qua():
    xoay = Polyhedron(LOM.vertices,
                      tuple(tuple(f[1:] + f[:1]) for f in LOM.faces))
    assert the_tich_da_dien(xoay) == 20


def test_04_dao_thu_tu_moi_mat_khong_doi_ket_qua():
    """Đảo TOÀN BỘ hướng chỉ đổi dấu tổng; `abs` cuối nuốt nó."""
    dao = Polyhedron(LOM.vertices,
                     tuple(tuple(reversed(f)) for f in LOM.faces))
    assert the_tich_da_dien(dao) == 20


def test_05_tinh_tien_bat_bien():
    assert the_tich_da_dien(_doi(LOM, v(7, -3, 11))) == 20
    assert the_tich_da_dien(_doi(LOM, v(-100, 250, -7))) == 20


@pytest.mark.parametrize("s", [F(3), F(1, 2), F(5, 3)])
def test_06_scale_nhan_s_mu_ba(s):
    assert the_tich_da_dien(_scale(LOM, s)) == 20 * s ** 3


@pytest.mark.parametrize("ten,kh,mong", [
    ("tứ diện", TU_DIEN, F(1, 6)),
    ("hình hộp", HOP, 30),
    ("chóp đáy tam giác", CHOP_TAM_GIAC, 6),
    ("chóp đáy vuông", CHOP_VUONG, 4),
])
def test_07_HOI_QUY_khoi_loi_giu_nguyen_gia_tri(ten, kh, mong):
    """⚠️ Ba khối này khai mặt KHÔNG nhất quán hướng — đo được trước khi sửa.

    Một phép tính có dấu đòi mô hình khai đúng chiều sẽ làm sai cả ba, và sai
    theo hướng tệ nhất (số nhỏ đi, im lặng). `dinh_huong_bien` tự lật nên hợp
    đồng khai mặt không đổi một byte.
    """
    assert the_tich_da_dien(kh) == mong, ten
    assert volume_polyhedron(kh) == mong, ten
    assert the_tich_da_dien(_doi(kh, v(5, 5, 5))) == mong, ten


# ══ §7 · TOPOLOGY FAIL-CLOSED ══════════════════════════════════════════
def test_08_bien_HO_bi_tu_choi():
    ho = Polyhedron(TU_DIEN.vertices, TU_DIEN.faces[:3] + (TU_DIEN.faces[0],))
    with pytest.raises(GeometryError) as e:
        the_tich_da_dien(ho)
    assert e.value.code in (SEC.ERR_BIEN_HO, SEC.ERR_KHONG_DINH_HUONG)


def test_09_thieu_mat_bi_tu_choi():
    with pytest.raises(GeometryError) as e:
        the_tich_da_dien(Polyhedron(HOP.vertices, HOP.faces[:-1]))
    assert e.value.code == SEC.ERR_BIEN_HO


def test_10_canh_suy_bien_bi_tu_choi():
    with pytest.raises(GeometryError) as e:
        the_tich_da_dien(Polyhedron(
            TU_DIEN.vertices,
            ((0, 1, 1), (0, 1, 3), (0, 2, 3), (1, 2, 3))))
    assert e.value.code == SEC.ERR_KHOI_HONG


def test_11_khoi_SUY_BIEN_the_tich_0_bi_tu_choi():
    """Bốn đỉnh đồng phẳng — không phải một khối."""
    phang = Polyhedron(
        (v(0, 0, 0), v(1, 0, 0), v(1, 1, 0), v(0, 1, 0)),
        ((0, 1, 2), (0, 2, 3), (0, 1, 2), (0, 2, 3)))
    with pytest.raises(GeometryError):
        the_tich_da_dien(phang)


def test_12_hai_vo_ROI_NHAU_bi_tu_choi():
    """Mỗi vỏ kín, nhưng hợp của chúng không có một dấu duy nhất."""
    d = tuple(TU_DIEN.vertices) + tuple(p + v(10, 0, 0)
                                        for p in TU_DIEN.vertices)
    f = TU_DIEN.faces + tuple(tuple(i + 4 for i in mat)
                              for mat in TU_DIEN.faces)
    with pytest.raises(GeometryError) as e:
        the_tich_da_dien(Polyhedron(d, f))
    assert e.value.code == SEC.ERR_BIEN_HO
    assert "liên thông" in str(e.value)


def test_13_day_KHONG_PHANG_van_bi_tu_choi_o_duong_chop():
    with pytest.raises(GeometryError):
        M.volume_pyramid_fan(S, [A, B, C, v(2, 1, 3), E])


# ══ §12.13 · RUNTIME VÀ CHECKER CÙNG TRẢ 20 ════════════════════════════
def test_14_runtime_va_checker_dung_CHUNG_tham_quyen():
    """Một thẩm quyền, hai người đọc — và nay nó ĐÚNG, không chỉ nhất quán."""
    from app.simulation.semantic_program.geometry_exec import volume_of

    assert volume_of(LOM) == 20
    assert volume_polyhedron(LOM) == volume_of(LOM) == the_tich_da_dien(LOM)


def test_15_gia_tri_SAI_cu_khong_con_xuat_hien_o_dau():
    """`28` là con số bản cũ trả. Không đường nào còn cho nó."""
    for f in (the_tich_da_dien, volume_polyhedron):
        assert f(LOM) != 28
    assert M.volume_pyramid_fan(S, DAY) != 28


# ══ §13 · TIÊM LỖI ═════════════════════════════════════════════════════
def test_TIEM_1_lay_abs_tung_tam_giac__gia_tri_SAI_quay_lai(monkeypatch):
    """Tiêm đúng đường lỗi cũ: `abs` từng tứ diện thay vì tổng có dấu."""
    from app.simulation.geometry.exact import det3

    def hong(sol):
        f = SEC.dinh_huong_bien(sol.faces)
        goc = sol.vertices[0]
        tong = F(0)
        for mat in f:
            for i in range(1, len(mat) - 1):
                tong += abs(det3(sol.vertices[mat[0]] - goc,
                                 sol.vertices[mat[i]] - goc,
                                 sol.vertices[mat[i + 1]] - goc)) / 6
        return tong

    monkeypatch.setattr(SEC, "the_tich_da_dien", hong)
    assert SEC.the_tich_da_dien(LOM) == 28          # sai số quay lại
    assert SEC.the_tich_da_dien(TU_DIEN) == F(1, 6)  # khối lồi vẫn đúng


def test_TIEM_2_bo_kiem_bien_KIN__khoi_ho_lot_qua(monkeypatch):
    """Tiêm: bỏ phép kiểm mỗi-cạnh-hai-mặt ⇒ khối thiếu mặt cho một số SAI.

    ⚠️ **Phải bỏ đúng mặt.** Bản đầu của test này bỏ mặt CUỐI của hình hộp
    (`3-0-4-7`) và khẳng định kết quả sai — đo ra `30`, tức **đúng**, nên
    phép tiêm không chứng minh gì. Lý do: mặt ấy chứa đỉnh `0`, mà `0` là gốc
    quạt, nên mọi tứ diện của nó suy biến và đóng góp **0**. Bỏ nó đi không
    đổi tổng.

    Mặt `4-5-6-7` thì không chứa gốc quạt: bỏ nó cho `20 ≠ 30`.
    """
    goc = SEC.dinh_huong_bien
    monkeypatch.setattr(SEC, "dinh_huong_bien",
                        lambda faces: tuple(tuple(f) for f in faces))
    ho = Polyhedron(HOP.vertices, HOP.faces[:1] + HOP.faces[2:])
    assert SEC.the_tich_da_dien(ho) == 20        # một con số, và nó SAI
    monkeypatch.setattr(SEC, "dinh_huong_bien", goc)
    with pytest.raises(GeometryError) as e:
        SEC.the_tich_da_dien(ho)
    assert e.value.code == SEC.ERR_BIEN_HO


def test_TIEM_3_bo_dinh_huong_lai__mot_mat_lon_lam_HONG_ket_qua(monkeypatch):
    """Tiêm: giữ nguyên hướng mô hình khai (không lật).

    ⚠️ **Đo đã BÁC một khẳng định tôi định viết ở đây.** Bản đầu ghi *"ba
    fixture lồi khai mặt không nhất quán, nên bỏ định hướng lại là làm sai
    chính chúng"*. Chạy thử: cả bốn fixture (kể cả chóp lõm) cho **đúng số**
    kể cả khi KHÔNG định hướng lại. Phép đếm cạnh-có-hướng nói chúng "không
    nhất quán", nhưng phần lệch ấy tự triệt tiêu trong tổng.

    Nên phép định hướng lại **không** load-bearing cho bốn fixture ấy — nó
    load-bearing cho một bảng mặt khai TUỲ Ý, và đây là ca chứng minh: lật
    ĐÚNG MỘT mặt của chóp lõm.

    ⚠️ **Phải lật đúng mặt, và đây là lần thứ HAI cùng một cái bẫy** (xem
    `TIEM_2`). Mặt chứa đỉnh `0` — gốc quạt — có mọi tứ diện suy biến nên đóng
    góp **0**; lật nó không đổi gì. Đo từng mặt của chóp lõm khi KHÔNG định
    hướng lại:

        mặt 0 (4,3,2,1,0)  chứa đỉnh 0 → 20   (không đổi)
        mặt 1 (0,1,5)      chứa đỉnh 0 → 20   (không đổi)
        mặt 2 (1,2,5)                  → 12
        mặt 3 (2,3,5)                  → 28   ← dùng ca này
        mặt 4 (3,4,5)                  →  4
        mặt 5 (4,0,5)      chứa đỉnh 0 → 20   (không đổi)

    Mặt 3 cho đúng `28` — trùng con số của lỗi lịch sử, tình cờ nhưng tiện để
    nhớ rằng hai bệnh khác nhau có thể cho cùng một triệu chứng.
    """
    f = list(LOM.faces)
    f[3] = tuple(reversed(f[3]))
    lon = Polyhedron(LOM.vertices, tuple(f))

    goc = SEC.dinh_huong_bien
    monkeypatch.setattr(SEC, "dinh_huong_bien",
                        lambda faces: tuple(tuple(x) for x in faces))
    assert SEC.the_tich_da_dien(lon) == 28      # không lật ⇒ SAI
    monkeypatch.setattr(SEC, "dinh_huong_bien", goc)
    assert SEC.the_tich_da_dien(lon) == 20      # định hướng lại ⇒ ĐÚNG


def test_TIEM_4_dao_huong_MOT_mat__phep_dinh_huong_lai_sua_lai_duoc():
    """Đảo một mặt KHÔNG được đổi kết quả — BFS lật nó về."""
    for i in range(len(LOM.faces)):
        f = list(LOM.faces)
        f[i] = tuple(reversed(f[i]))
        assert the_tich_da_dien(Polyhedron(LOM.vertices, tuple(f))) == 20, i


# ══ §10 · GOLD ĐI TRỌN CHUỖI — 0 lượt gọi model ════════════════════════
#
# Ba ô trên chứng minh KERNEL đúng. Chúng KHÔNG chứng minh khối lõm **biểu đạt
# được bằng IR**, và đó là câu hỏi riêng: một con số đúng ở tầng kernel mà
# không có đường nào dẫn tới nó từ một đề bằng lời thì hệ vẫn chưa làm được gì.
#
# `NEW_IR_OPERATIONS = 0` đo được ở đây: gold dưới đây dùng **đúng
# `construct_solid` đã có**. Bảng mặt là cấu trúc tổ hợp, và một ngũ giác lõm
# không cần từ vựng nào mà một ngũ giác lồi không cần.

_TEN_DIEM = ["A", "B", "C", "D", "E", "S"]
#: Đáy khai NGƯỢC (E→A) cho hướng ra ngoài, y hệt `MAT_LOM`.
_MAT_TEN = [["E", "D", "C", "B", "A"]] + [
    [_TEN_DIEM[i], _TEN_DIEM[(i + 1) % 5], "S"] for i in range(5)]


def _ct_lom() -> RequestContract:
    return RequestContract(
        problem_text=(
            "Cho khối chóp S.ABCDE có đáy ABCDE là ngũ giác LÕM với "
            "A(0;0;0), B(4;0;0), C(4;4;0), D(2;1;0), E(0;4;0) và đỉnh "
            "S(2;1/2;6). Tính thể tích khối chóp."),
        input_facts=[
            {"fact_id": f"d_{t}", "label": f"điểm {t}", "values": [t],
             "provenance": "confirmed"} for t in _TEN_DIEM],
        obligations=(
            Obligation(kind="volume", container="chop",
                       params={"witness": "V"}),))


def _spec_lom(**doi) -> SemanticProgramSpec:
    toa_do = {"A": [0, 0, 0], "B": [4, 0, 0], "C": [4, 4, 0],
              "D": [2, 1, 0], "E": [0, 4, 0], "S": [2, "1/2", 6]}
    d = {
        "title": "Thể tích khối chóp đáy ngũ giác lõm",
        "memory_declarations": [
            {"name": t, "type": "point3", "initial_value": toa_do[t],
             "source_fact_id": f"d_{t}"} for t in _TEN_DIEM
        ] + [
            {"name": "chop", "type": "solid"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": _TEN_DIEM, "faces": _MAT_TEN, "label": "S.ABCDE"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
        ],
    }
    d.update(doi)
    return SemanticProgramSpec.model_validate(d)


def test_16_SYSTEM_EXPRESSIBLE__gold_lom_qua_MOI_cong():
    """Không chỉ chạy được: **phục vụ được**. `servable` là cổng cuối, sau
    static check · grounding · phủ nghĩa vụ · checker hình học."""
    oc = verify_and_compile(_ct_lom(), _spec_lom())
    assert oc.servable, oc.details
    assert oc.error_code is None
    assert display(oc.final_memory["V"]) == "20"


def test_17_DETERMINISTICALLY_CORRECT__checker_doc_lap_da_chay():
    """`servable` chỉ có nghĩa nếu checker thể tích THẬT SỰ chạy trên ca này.
    Nghĩa vụ nằm ở mức yếu (không checker) thì `servable` là một lời hứa suông."""
    oc = verify_and_compile(_ct_lom(), _spec_lom())
    assert "volume" not in oc.weak_kinds, oc.weak_kinds


def test_18_TRACE_PASS__trace_bay_ra_CAC_BUOC_DUNG():
    """Trace phải cho thấy khối được DỰNG rồi mới được ĐO — không phải một con
    số rơi từ trên xuống. Bất biến #31: một mục cho đúng một bước."""
    kq = SemanticProgramInterpreter().execute(_spec_lom())
    assert kq.trace, "trace rỗng"
    hd = [(s.action, s.target) for s in kq.trace]
    # Dựng khối đứng TRƯỚC phép đo, và cả hai đều có mặt.
    i_dung = next(i for i, s in enumerate(kq.trace) if s.target == "chop")
    i_do = next(i for i, s in enumerate(kq.trace) if s.target == "V")
    assert i_dung < i_do, hd
    assert "solid" in kq.trace[i_dung].action, hd
    # Lời kể tiếng Việt phải NÓI RA bước dựng, không để trace câm.
    assert kq.trace[i_dung].tier1_narration.strip(), hd


def test_19_DEPENDENCY_PASS__the_tich_TRUY_duoc_ve_sau_dinh():
    """Mô hình **dựng phụ thuộc**, không khai thẳng kết quả. Nếu `V` không phụ
    thuộc `chop`, hoặc `chop` không phụ thuộc đủ sáu đỉnh, thì con số 20 là
    một hằng số may mắn chứ không phải một phép dựng."""
    g = dependency_graph(_spec_lom())
    assert "chop" in g["V"], g
    assert set(_TEN_DIEM) <= set(g["chop"]), g


def test_20_SCENE3D_PASS__canh_giu_NGUYEN_ngu_giac_lom():
    """Cảnh phải giao cho renderer **đúng năm đỉnh đáy theo thứ tự vòng
    quanh** — không tam giác hoá sẵn, không sắp lại thành lồi.

    Đây là chỗ phần lõm sống hay chết: kernel quyết thứ tự đỉnh, renderer chỉ
    nối. Nếu cảnh giao ra một đáy đã bị sắp lại thì `polygon-triangulate.ts` có
    đúng đến mấy cũng vẽ ra một hình lồi.
    """
    sc = _dung_scene3d(_spec_lom())
    assert sc is not None
    khoi = next(o for o in sc["objects"] if o["id"] == "chop")
    assert khoi["render"] == "mesh"
    assert len(khoi["vertices"]) == 6
    day = [f for f in khoi["faces"] if len(f) == 5]
    assert len(day) == 1, khoi["faces"]

    # …và đáy ấy THẬT SỰ lõm: đúng một đỉnh phản xạ. Không có ô này thì test
    # trên vẫn xanh với một ngũ giác lồi, và cả wave mất đối tượng.
    xy = [(F(khoi["vertices"][j][0]), F(khoi["vertices"][j][1]))
          for j in day[0]]
    cheo = []
    for i in range(5):
        p, q, r = xy[i], xy[(i + 1) % 5], xy[(i + 2) % 5]
        cheo.append((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
    assert 0 not in cheo, cheo                 # không đỉnh nào thẳng hàng
    assert min(sum(1 for c in cheo if c > 0),
               sum(1 for c in cheo if c < 0)) == 1, cheo


def test_21_canh_TAT_DINH__cung_chuong_trinh_cung_canh():
    a = json.dumps(_dung_scene3d(_spec_lom()), sort_keys=True, ensure_ascii=False)
    b = json.dumps(_dung_scene3d(_spec_lom()), sort_keys=True, ensure_ascii=False)
    assert a == b


def test_22_doi_TEN_dinh_khong_doi_ket_qua():
    """Giải pháp áp cho mọi bài cùng cấu trúc, không bám tên nào."""
    ten = ["P", "Q", "R", "T", "U", "X"]
    doi = dict(zip(_TEN_DIEM, ten))
    spec = _spec_lom(
        memory_declarations=[
            {"name": doi[t], "type": "point3",
             "initial_value": v_, "source_fact_id": f"d_{t}"}
            for t, v_ in zip(_TEN_DIEM,
                             [[0, 0, 0], [4, 0, 0], [4, 4, 0],
                              [2, 1, 0], [0, 4, 0], [2, "1/2", 6]])
        ] + [{"name": "khoi", "type": "solid"}, {"name": "W", "type": "float"}],
        statements=[
            {"kind": "construct_solid", "target_var": "khoi",
             "vertices": ten, "faces": [[doi[t] for t in m] for m in _MAT_TEN]},
            {"kind": "assign", "target_var": "W",
             "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}},
        ])
    ct = RequestContract(
        problem_text=_ct_lom().problem_text,
        input_facts=[{"fact_id": f"d_{t}", "label": f"điểm {doi[t]}",
                      "values": [doi[t]], "provenance": "confirmed"}
                     for t in _TEN_DIEM],
        obligations=(Obligation(kind="volume", container="khoi",
                                params={"witness": "W"}),))
    oc = verify_and_compile(ct, spec)
    assert oc.servable, oc.details
    assert display(oc.final_memory["W"]) == "20"


def test_30_TIEM_7_ban_CU_o_muc_ROUTE__envelope_OK_mang_so_SAI(monkeypatch):
    """Bằng chứng của quyết định `CACHE_VERSION` (§15), đo ở mức ROUTE.

    `TIEM_1` chứng minh kernel cũ cho `28`. Ô này chứng minh điều nặng hơn:
    con số ấy đi trọn ra tới **envelope `status = "ok"`** — và `main.py` cache
    CẢ envelope (`envelope_json`). Nên một row cache sinh trước bản vá sẽ đọc
    to `28` dưới cùng `CACHE_VERSION`, không cổng nào chặn.

    Đó là chiều nguy hiểm mà các bump 87/88/90/91 KHÔNG có: chúng chỉ biến
    từ-chối → phục-vụ. Bump 92 có cả chiều `phục vụ số SAI → phục vụ số ĐÚNG`.
    """
    def the_tich_CU(sol):
        goc = sol.vertices[0]
        t = F(0)
        for mat in sol.faces:
            for i in range(1, len(mat) - 1):
                t += M.volume_tetrahedron(goc, sol.vertices[mat[0]],
                                          sol.vertices[mat[i]],
                                          sol.vertices[mat[i + 1]])
        return t

    monkeypatch.setattr(SEC, "the_tich_da_dien", the_tich_CU)
    oc = verify_and_compile(_ct_lom(), _spec_lom())
    assert oc.servable
    assert (oc.envelope or {}).get("status") == "ok"
    assert display(oc.final_memory["V"]) == "28"


def _spec_chu_trinh(chu: list[str]) -> SemanticProgramSpec:
    """Cùng sáu điểm, đổi CHU TRÌNH đáy — thứ mô hình thật sự viết ra."""
    return _spec_lom(statements=[
        {"kind": "construct_solid", "target_var": "chop",
         "vertices": _TEN_DIEM,
         "faces": [list(reversed(chu))]
                  + [[chu[i], chu[(i + 1) % 5], "S"] for i in range(5)]},
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
    ])


def test_24_chu_trinh_day_KHAC__cho_hinh_KHAC_va_so_KHAC():
    """⚠️ ĐÍNH CHÍNH một lần đo sai của chính wave này (2026-09-07).

    Lượt đầu tôi ghi `A→B→D→C→E` là "đáy TỰ CẮT mà hệ vẫn phục vụ 24" và định
    coi đó là một lỗ. Đo lại: chu trình ấy **KHÔNG** tự cắt — nó là một ngũ
    giác lõm KHÁC, shoelace `12`, nên `V = 24` là ĐÚNG cho hình ấy. Hệ không
    sai chỗ nào cả.

    Giữ ô này lại vì nó khoá một điều thật: bảng mặt là thứ MÔ HÌNH viết, và
    hai chu trình khác nhau trên cùng sáu điểm phải cho hai khối khác nhau.
    Nếu cả hai cùng ra `20` thì `faces` đang bị bỏ qua.
    """
    a = verify_and_compile(_ct_lom(), _spec_chu_trinh(["A", "B", "C", "D", "E"]))
    b = verify_and_compile(_ct_lom(), _spec_chu_trinh(["A", "B", "D", "C", "E"]))
    assert a.servable and b.servable, (a.details, b.details)
    assert display(a.final_memory["V"]) == "20"
    assert display(b.final_memory["V"]) == "24"


def test_25_mat_TU_CAT_bi_tu_choi_co_MA():
    """Bow-tie thật: `A→C→B→D→E` — cạnh `A-C` (y=x) cắt cạnh `D-E` tại
    `(8/5, 8/5)`. Biên vẫn KÍN và vẫn định hướng được, nên ba điều kiện tổ hợp
    của `dinh_huong_bien` cho nó đi qua. Chỉ phép soát TỪNG MẶT bắt được."""
    oc = verify_and_compile(_ct_lom(), _spec_chu_trinh(["A", "C", "B", "D", "E"]))
    assert not oc.servable
    assert any(SEC.ERR_MAT_KHONG_DON in d for d in oc.details), oc.details


def test_26_TIEM_6_bo_soat_mat__so_VO_NGHIA_quay_lai(monkeypatch):
    """Bỏ phép soát mặt ⇒ bow-tie được phục vụ với `V = 4`.

    `4` không phải thể tích của vật nào: shoelace của chu trình nút bằng `2`
    vì hai thuỳ trừ nhau. Đây đúng lớp lỗi của wave — một con số đọc lên trơn
    tru mà không có hình nào ứng với nó.
    """
    monkeypatch.setattr(SEC, "kiem_mat_phang_don", lambda sol: None)
    oc = verify_and_compile(_ct_lom(), _spec_chu_trinh(["A", "C", "B", "D", "E"]))
    assert oc.servable, oc.details
    assert display(oc.final_memory["V"]) == "4"


def test_27_mat_KHONG_PHANG_bi_tu_choi_co_MA():
    """Mặt không phẳng cho một con số phụ thuộc cách chia tam giác trong mặt —
    nên nó không phải thể tích của cái gì cả."""
    lech = Polyhedron(
        (A, B, C, D, v(0, 4, 1), S),          # E nhấc lên khỏi mặt phẳng đáy
        MAT_LOM)
    with pytest.raises(GeometryError) as e:
        the_tich_da_dien(lech)
    assert e.value.code == SEC.ERR_MAT_KHONG_PHANG


def test_28_mat_LAP_DINH_bi_tu_choi():
    """Đỉnh xuất hiện hai lần trong một mặt lọt qua phép đếm cạnh (cạnh lặp
    được đếm hai lần trong CÙNG một mặt), nên phải chặn riêng."""
    f = list(MAT_LOM)
    f[0] = (4, 3, 2, 3, 1, 0)
    with pytest.raises(GeometryError) as e:
        the_tich_da_dien(Polyhedron(LOM.vertices, tuple(f)))
    assert e.value.code in (SEC.ERR_MAT_KHONG_DON, SEC.ERR_BIEN_HO)


def test_29_khoi_LOI_va_khoi_LOM_hop_le_KHONG_bi_soat_mat_chan():
    """Phép soát mới không được rộng tay: mọi fixture cũ phải đi qua."""
    for kh in (LOM, TU_DIEN, HOP, CHOP_VUONG, CHOP_TAM_GIAC):
        SEC.kiem_mat_phang_don(kh)          # không ném


def test_23_TIEM_5_bang_mat_SAI__gold_khong_con_cho_20():
    """Bảng mặt là thứ MÔ HÌNH viết ra, nên nó sai được. Khai đáy như một ngũ
    giác LỒI (bỏ đỉnh lõm `D` ra khỏi đúng chỗ của nó) phải đổi đáp số —
    ngược lại thì `faces` không hề được dùng và cả wave đo nhầm chỗ."""
    sai = [["E", "C", "D", "B", "A"]] + _MAT_TEN[1:]
    spec = _spec_lom(statements=[
        {"kind": "construct_solid", "target_var": "chop",
         "vertices": _TEN_DIEM, "faces": sai},
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
    ])
    oc = verify_and_compile(_ct_lom(), spec)
    # ĐO ĐƯỢC: bị từ chối bằng `POLYHEDRON_BOUNDARY_OPEN` — đáy đổi chu trình
    # mà mặt bên giữ nguyên thì bốn cạnh mất bạn. Ghim đúng mã ấy, không ghim
    # "hoặc từ chối hoặc số khác": một điều kiện lỏng như thế xanh cả khi cổng
    # hỏng theo một cách chẳng liên quan.
    assert not oc.servable
    assert any(SEC.ERR_BIEN_HO in d for d in oc.details), oc.details
