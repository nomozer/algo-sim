# -*- coding: utf-8 -*-
"""GÓC NHỊ DIỆN DỰNG BẰNG PRIMITIVE ĐÃ CÓ — không thêm từ vựng. **0 API call.**

─── CÂU HỎI CỦA WAVE ──────────────────────────────────────────────────────

Một dạng bài mới có bắt buộc kéo theo một primitive mới không? Góc nhị diện là
**phép thử**: nó là ô UNSUPPORTED cuối cùng còn nằm trong chương trình THPT, và
phản xạ tự nhiên là thêm `measure_dihedral()`. File này hỏi trước:

    IR hiện tại đã đủ để VIẾT RA phép dựng ấy chưa?

Nếu đủ thì thêm primitive là làm nghèo hệ đi: mỗi primitive chuyên biệt là một
lối tắt mà mô hình phải học riêng, và là một nhánh runtime phải nuôi mãi.

─── PHÂN RÃ CHUẨN, VIẾT BẰNG TỪ VỰNG ĐANG CÓ ──────────────────────────────

    d = intersect_plane_plane(α, β)     cạnh chung
    H = project_onto(P, d)              P ∈ α, P ∉ d  ⇒  HP ⟂ d và HP ⊂ α
    K = project_onto(Q, d)              Q ∈ β, Q ∉ d  ⇒  KQ ⟂ d và KQ ⊂ β
    a = construct_line(H, P)
    b = construct_line(K, Q)
    θ = measure angle_cos_sq(a, b)

Hai điều làm phân rã này ĐÚNG, và cả hai đều là định lý chứ không phải mẹo:

  · `HP ⊂ α` vì P ∈ α và H ∈ d ⊂ α — hai điểm của một mặt phẳng xác định một
    đường nằm trong mặt ấy.
  · Góc giữa hai đường cùng vuông góc với `d` KHÔNG phụ thuộc chỗ đặt chân trên
    `d` — tịnh tiến dọc `d` không đổi phương. Nên `H ≠ K` vẫn cho đúng góc, và
    phân rã không cần ép hai chân về một điểm.

─── ĐIỀU FILE NÀY KHÔNG CHỨNG MINH ────────────────────────────────────────

`angle_cos_sq` giữa hai ĐƯỜNG trả `cos²`, mất dấu. Nó không phân biệt được θ
với 180°−θ, tức **không** trả lời được "nhị diện tù hay nhọn". Đó là một GAP
thật, ghi ở `test_domain_awareness` bên dưới — không vá bằng ca đặc biệt.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.geometry import measure as M
from app.simulation.geometry import predicates as P
from app.simulation.geometry.exact import Line3, Plane3, Vec3
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.validator import validate_semantic_program

F = Fraction
V = Vec3.of


def _chuong_trinh(dinh: dict[str, list[int]], goc_alpha: list[str],
                  goc_beta: list[str], p_ngoai: str, q_ngoai: str) -> dict:
    """Dựng chương trình phân rã — CÙNG một khuôn cho mọi biến thể.

    Tham số hoá đỉnh/mặt chứ không viết tay từng bài: nếu mỗi biến thể cần một
    chương trình khác nhau thì "phân rã tổng quát" chỉ là một lời nói.
    """
    return {
        "spec_version": "1.0",
        "simulation_id": "geometry.dihedral_composition",
        "title": "Góc nhị diện dựng bằng phép chiếu",
        "description": "Dựng cạnh chung rồi hai đường đại diện vuông góc với nó.",
        "pedagogical_intent": "Cho thấy góc nhị diện là một phép DỰNG, không phải một công thức.",
        "memory_declarations": [
            {"name": ten, "type": "point3", "initial_value": xyz,
             "model_assumption": "đỉnh của khối, chọn hệ trục theo đề"}
            for ten, xyz in dinh.items()
        ] + [
            {"name": "alpha", "type": "plane3"},
            {"name": "beta", "type": "plane3"},
            {"name": "d", "type": "line3"},
            {"name": "H", "type": "point3"},
            {"name": "K", "type": "point3"},
            {"name": "a", "type": "line3"},
            {"name": "b", "type": "line3"},
            {"name": "cos2", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_plane", "target_var": "alpha", "through": goc_alpha,
             "label": f"Dựng mặt ({''.join(goc_alpha)})"},
            {"kind": "construct_plane", "target_var": "beta", "through": goc_beta,
             "label": f"Dựng mặt ({''.join(goc_beta)})"},
            {"kind": "assign", "target_var": "d",
             "expr": {"kind": "intersect_plane_plane", "plane_a": "alpha",
                      "plane_b": "beta"},
             "label": "Giao tuyến d của hai mặt — cạnh của góc nhị diện"},
            {"kind": "construct_point", "target_var": "H",
             "expr": {"kind": "project_onto", "point": p_ngoai, "target": "d"},
             "label": f"Chiếu {p_ngoai} xuống d, được chân H"},
            {"kind": "construct_point", "target_var": "K",
             "expr": {"kind": "project_onto", "point": q_ngoai, "target": "d"},
             "label": f"Chiếu {q_ngoai} xuống d, được chân K"},
            {"kind": "construct_line", "target_var": "a",
             "through_a": "H", "through_b": p_ngoai,
             "label": f"Dựng H{p_ngoai} — nằm trong mặt thứ nhất, vuông góc d"},
            {"kind": "construct_line", "target_var": "b",
             "through_a": "K", "through_b": q_ngoai,
             "label": f"Dựng K{q_ngoai} — nằm trong mặt thứ hai, vuông góc d"},
            {"kind": "assign", "target_var": "cos2",
             "expr": {"kind": "measure", "quantity": "angle_cos_sq",
                      "of": "a", "wrt": "b"},
             "label": "Góc nhị diện = góc giữa hai đường đại diện"},
        ],
        "obligations": [
            {"kind": "perpendicular", "container": "a", "witness": "d"},
            {"kind": "perpendicular", "container": "b", "witness": "d"},
        ],
    }


#: Bài gốc: lập phương cạnh 1. Nhị diện cạnh AB giữa mặt đáy và mặt (ABB'A')
#: là 90°; đổi sang một cấu hình cho góc KHÔNG tầm thường bên dưới.
LAP_PHUONG = {
    "A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "D": [0, 1, 0],
    "S": [0, 0, 1],
}


def _chay(ct: dict):
    val = validate_semantic_program(ct)
    assert val.ok, f"IR không thẩm định được: {val.error}"
    return val.spec, SemanticProgramInterpreter().execute(val.spec)


# ══ ① IR CÓ ĐỦ TỪ VỰNG KHÔNG ═════════════════════════════════════════════
def test_phan_ra_THAM_DINH_duoc_bang_tu_vung_hien_co():
    """Câu hỏi số một của wave. Trượt ở đây ⇒ mới được bàn tới primitive mới."""
    ct = _chuong_trinh(LAP_PHUONG, ["A", "B", "C"], ["A", "B", "S"], "D", "S")
    val = validate_semantic_program(ct)
    assert val.ok, val.error


def test_khong_dung_mot_tu_vung_NAO_ngoai_bo_hien_co():
    """Guard chống tự lừa: nếu chương trình lén dùng một `kind` chưa có thì
    "phân rã bằng primitive hiện tại" là một câu sai."""
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    ct = _chuong_trinh(LAP_PHUONG, ["A", "B", "C"], ["A", "B", "S"], "D", "S")
    dung = {st["kind"] for st in ct["statements"]}
    biet = set(SemanticProgramSpec.model_json_schema()["$defs"].keys())
    # Mọi `kind` phải nằm trong schema ĐANG CÓ — không có `dihedral` nào.
    for k in dung:
        assert "dihedral" not in k, f"lén thêm từ vựng chuyên biệt: {k}"
    assert biet, "không đọc được schema"


# ══ ② CHẠY RA SỐ ĐÚNG ════════════════════════════════════════════════════
def test_hai_duong_dai_dien_THUC_SU_vuong_goc_canh_chung():
    """Tính chất làm phân rã ĐÚNG — kiểm bằng vị từ chính xác, không bằng số.

    Sai ở đây thì con số vẫn ra, chỉ là nó không phải góc nhị diện.
    """
    ct = _chuong_trinh(LAP_PHUONG, ["A", "B", "C"], ["A", "B", "S"], "D", "S")
    _, kq = _chay(ct)
    mem = kq.final_memory
    assert P.perpendicular_lines(mem["a"], mem["d"])
    assert P.perpendicular_lines(mem["b"], mem["d"])


def test_hai_duong_dai_dien_NAM_TRONG_dung_mat_cua_no():
    """`HP ⊂ α` vì P ∈ α và H ∈ d ⊂ α. Kiểm cả hai đầu mút, không suy luận."""
    ct = _chuong_trinh(LAP_PHUONG, ["A", "B", "C"], ["A", "B", "S"], "D", "S")
    _, kq = _chay(ct)
    mem = kq.final_memory
    assert P.point_on_plane(mem["H"], mem["alpha"])
    assert P.point_on_plane(mem["D"], mem["alpha"])
    assert P.point_on_plane(mem["K"], mem["beta"])
    assert P.point_on_plane(mem["S"], mem["beta"])


def test_goc_ra_dung_gia_tri_CHINH_XAC():
    """Lập phương cạnh 1, cạnh chung AB: mặt đáy (ABC) ⟂ mặt bên (ABS).

    `cos² = 0` ⇔ vuông góc. Giá trị tính TAY từ hình, không lấy từ engine.
    """
    ct = _chuong_trinh(LAP_PHUONG, ["A", "B", "C"], ["A", "B", "S"], "D", "S")
    _, kq = _chay(ct)
    assert kq.final_memory["cos2"] == F(0)


def test_goc_KHONG_TAM_THUONG_ra_dung():
    """Nhị diện cạnh BC của chóp S.ABCD với S(0,0,1), đáy vuông cạnh 1.

    Mặt (BCD) là đáy z=0; mặt (BCS) qua B(1,0,0), C(1,1,0), S(0,0,1).
    Cạnh chung BC: x=1, z=0, phương (0,1,0).
    Chiếu D(0,1,0) xuống BC → H(1,1,0); HD phương (−1,0,0).
    Chiếu S(0,0,1) xuống BC → K(1,0,0); KS phương (−1,0,1).
    cos²θ = 1²/(1·2) = 1/2  ⇒  θ = 45°.
    """
    ct = _chuong_trinh(LAP_PHUONG, ["B", "C", "D"], ["B", "C", "S"], "D", "S")
    _, kq = _chay(ct)
    assert kq.final_memory["cos2"] == F(1, 2)


# ══ ③ CỔNG CHẤM TỰ TÍNH LẠI ══════════════════════════════════════════════
def test_nghia_vu_vuong_goc_duoc_CHAM_bang_cong_that():
    """Không tin con số chương trình khai — cổng dựng lại từ hình."""
    from app.simulation.semantic_program.geometry_obligations import GEOMETRY_CHECKERS

    ct = _chuong_trinh(LAP_PHUONG, ["B", "C", "D"], ["B", "C", "S"], "D", "S")
    _, kq = _chay(ct)

    class _Ob:
        def __init__(self, c, w):
            self.kind, self.container, self.witness, self.params = \
                "perpendicular", c, w, {}

    for ten in ("a", "b"):
        assert GEOMETRY_CHECKERS["perpendicular"](kq.final_memory, _Ob(ten, "d")) is None


def test_cong_cham_BAT_duoc_phan_ra_SAI():
    """Đổi `a` thành một đường KHÔNG vuông góc `d` — cổng phải kêu.

    Không có ca này thì ca trên vô nghĩa: một cổng luôn PASS cũng qua được nó.
    """
    from app.simulation.semantic_program.geometry_obligations import GEOMETRY_CHECKERS

    ct = _chuong_trinh(LAP_PHUONG, ["B", "C", "D"], ["B", "C", "S"], "D", "S")
    _, kq = _chay(ct)
    mem = dict(kq.final_memory)
    mem["a"] = Line3.through(V(0, 0, 0), V(0, 1, 0))   # cùng phương d

    class _Ob:
        kind, container, witness, params = "perpendicular", "a", "d", {}

    assert GEOMETRY_CHECKERS["perpendicular"](mem, _Ob()) is not None


# ══ ④ GAP THẬT — MIỀN GÓC ════════════════════════════════════════════════
def test_domain_awareness_LA_GAP_chua_bieu_dien_duoc():
    """`cos²` KHÔNG phân biệt được nhị diện NHỌN với TÙ. Ghi ra, không vá.

    Hai cấu hình dưới đây có góc nhị diện bù nhau (θ và 180°−θ) nhưng cho CÙNG
    một `cos²`. Đó không phải lỗi cài đặt: `angle_cos_sq` giữa hai ĐƯỜNG là đại
    lượng không dấu theo định nghĩa, và IR chưa có cách nào nói "hướng".

    Ca này ĐỎ khi ai đó thêm được miền góc — lúc ấy nó phải được viết lại thành
    một khẳng định về giá trị, không phải về giới hạn.
    """
    u = V(1, 0, 0)
    goc_nhon = Line3.through(V(0, 0, 0), V(1, 1, 0))     # 45° với Ox
    goc_tu = Line3.through(V(0, 0, 0), V(-1, 1, 0))      # 135° với Ox
    ox = Line3.through(V(0, 0, 0), u)
    assert M.cos_sq_between_lines(ox, goc_nhon) == M.cos_sq_between_lines(ox, goc_tu)


def test_dau_SUY_DUOC_tu_hinh_du_IR_chua_noi_duoc():
    """Điều quan trọng cho quyết định §14: thông tin KHÔNG mất, chỉ chưa có TỪ.

    Server dựng lại được dấu từ chính hai vector đã có (`(P−H)·(Q−K)`), nên
    primitive còn thiếu là một **đại lượng có dấu** — tổng quát, dùng cho mọi
    góc định hướng — chứ không phải một hàm riêng cho nhị diện.
    """
    ct = _chuong_trinh(LAP_PHUONG, ["B", "C", "D"], ["B", "C", "S"], "D", "S")
    _, kq = _chay(ct)
    mem = kq.final_memory
    u = mem["D"] - mem["H"]
    v = mem["S"] - mem["K"]
    assert isinstance(u.dot(v), Fraction), "dấu tính được bằng số hữu tỉ chính xác"


# ══ ⑤ TÍNH TỔNG QUÁT — cùng chương trình, khác dữ liệu (§11) ═════════════
BIEN_THE = [
    pytest.param(
        {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0], "S": [0, 0, 2]},
        F(1, 2), id="đổi-số-liệu (cạnh 2)"),
    pytest.param(
        {"A": [0, 0, 0], "B": [3, 0, 0], "C": [3, 1, 0], "D": [0, 1, 0], "S": [0, 0, 1]},
        F(9, 10), id="đổi-tỉ-lệ (hộp chữ nhật: a=3, h=1)"),
    pytest.param(
        {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "D": [0, 1, 0], "S": [0, 0, 2]},
        F(1, 5), id="đổi-chiều-cao (S cao 2)"),
]


@pytest.mark.parametrize("dinh, mong", BIEN_THE)
def test_CUNG_MOT_chuong_trinh_chay_ba_bien_the(dinh, mong):
    """CÙNG khuôn IR, khác dữ liệu — không một dòng code riêng nào giữa các ca.

    `cos²` với đáy cạnh a×b và S(0,0,h): chân chiếu D→BC cho phương (−1,0,0),
    S→BC cho phương (−a,0,h); cos² = a²/(a²+h²).
    """
    ct = _chuong_trinh(dinh, ["B", "C", "D"], ["B", "C", "S"], "D", "S")
    _, kq = _chay(ct)
    assert kq.final_memory["cos2"] == mong


def test_ba_bien_the_dung_DUNG_MOT_bo_cau_lenh():
    """Bằng chứng của §11: khác nhau CHỈ ở dữ liệu, không ở chương trình."""
    khuon = None
    for dinh, _ in [(p.values[0], p.values[1]) for p in BIEN_THE]:
        ct = _chuong_trinh(dinh, ["B", "C", "D"], ["B", "C", "S"], "D", "S")
        chuoi = [(s["kind"], s.get("target_var")) for s in ct["statements"]]
        if khuon is None:
            khuon = chuoi
        assert chuoi == khuon, "biến thể cần một chương trình khác ⇒ chưa tổng quát"


# ══ ⑥ LỖI ĐO ĐƯỢC TỪ LƯỢT LIVE — sửa ĐÚNG TẦNG (§4) ═════════════════════
def _ct_do(quantity: str, of: str, wrt: str | None):
    ct = {
        "spec_version": "1.0", "simulation_id": "geometry.measure_arity",
        "title": "Kiểm số ngôi của phép đo",
        "description": "Phép đo thiếu đối tượng thứ hai phải chết ở thẩm định.",
        "pedagogical_intent": "Cho thấy cổng bắt lỗi trước khi kernel chạy.",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
             "model_assumption": "gốc"},
            {"name": "B", "type": "point3", "initial_value": [1, 0, 0],
             "model_assumption": "trục x"},
            {"name": "C", "type": "point3", "initial_value": [0, 1, 0],
             "model_assumption": "trục y"},
            {"name": "D", "type": "point3", "initial_value": [0, 0, 1],
             "model_assumption": "trục z"},
            {"name": "L", "type": "line3"},
            {"name": "kh", "type": "solid"},
            {"name": "x", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_line", "target_var": "L",
             "through_a": "A", "through_b": "B"},
            {"kind": "construct_solid", "target_var": "kh",
             "vertices": ["A", "B", "C", "D"],
             "faces": [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]},
            {"kind": "assign", "target_var": "x",
             "expr": {"kind": "measure", "quantity": quantity, "of": of,
                      **({"wrt": wrt} if wrt else {})}},
        ],
    }
    return ct


@pytest.mark.parametrize("quantity", ["angle_cos_sq", "distance"])
def test_phep_do_THIEU_wrt_chet_o_THAM_DINH_khong_phai_runtime(quantity):
    """Ca THẬT từ lượt live 2026-08-31 (probe nhị diện, «đổi tên đỉnh»).

    Mô hình phát `angle_cos_sq` chỉ có `of`. Schema cho qua (`wrt` là
    `Optional` vì `volume`), thẩm định tĩnh cho qua, rồi kernel ném
    `GEOMETRY_OPERAND_TYPE`.

    Vì sao tầng quan trọng: **lỗi runtime KHÔNG được gửi ngược cho mô hình
    sửa**, chỉ lỗi validator mới được. Nên một sai sót sửa được trong một lượt
    lại giết cả ca — và ca ấy tính vào thống kê như "mô hình không làm được",
    trong khi thật ra ta không cho nó biết nó sai gì.
    """
    r = validate_semantic_program(_ct_do(quantity, "L", None))
    assert not r.ok, "phép đo thiếu `wrt` vẫn lọt qua thẩm định tĩnh"
    assert "wrt" in r.error


def test_volume_VAN_do_duoc_tren_MOT_doi_tuong():
    """Luật mới không được bắt oan `volume` — nó vốn là phép đo một ngôi."""
    r = validate_semantic_program(_ct_do("volume", "kh", None))
    assert r.ok, r.error


def test_phep_do_DU_wrt_van_qua():
    r = validate_semantic_program(_ct_do("distance", "A", "L"))
    assert r.ok, r.error
