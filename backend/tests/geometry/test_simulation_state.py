# -*- coding: utf-8 -*-
"""PHASE 5B — lớp trạng thái mô phỏng. **0 API call.**

    Semantic Program → Interpreter → **Simulation State** → Renderer 3D

Bốn nhóm test theo đúng STEP 8: `GeometryScene` · `DependencyGraph` ·
`Timeline` · ranh giới kiến trúc.

Điều file này khoá chặt nhất **không** phải hình dạng JSON mà là hai ranh giới:

  ① Lớp này **CHIẾU, KHÔNG TÍNH**. Không một phép hình học nào.
  ② Số là **chuỗi phân số**, không bao giờ là `float`.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.simulation_state import (
    build_scene,
    build_simulation_state,
    build_timeline,
    dependency_graph,
)


def _chay(ct: dict):
    spec = SemanticProgramSpec.model_validate(ct)
    return spec, SemanticProgramInterpreter().execute(spec)


#: Chóp S.ABCD đáy vuông cạnh 1, SA ⊥ đáy, SA = 2. Dựng khối, mặt đáy, trung
#: điểm M của AB, rồi đo thể tích — phủ cả năm loại đối tượng.
def _chuong_trinh() -> dict:
    diem = {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0],
            "D": [0, 1, 0], "S": [0, 0, 2]}
    return {
        "spec_version": "1.0",
        "title": "Chóp S.ABCD — cảnh mô phỏng",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v,
             "model_assumption": "hệ trục đã chọn"}
            for n, v in diem.items()
        ] + [
            {"name": "M", "type": "point3"},
            {"name": "day", "type": "plane3"},
            {"name": "chop", "type": "solid"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_point", "target_var": "M", "label": "M",
             "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
            {"kind": "construct_plane", "target_var": "day",
             "through": ["A", "B", "C"], "label": "(ABCD)"},
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": ["A", "B", "C", "D", "S"],
             "faces": [["A", "B", "C", "D"], ["A", "B", "S"], ["B", "C", "S"],
                       ["C", "D", "S"], ["D", "A", "S"]],
             "label": "S.ABCD"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
        ],
        "visual_bindings": {},
    }


@pytest.fixture(scope="module")
def st():
    spec, kq = _chay(_chuong_trinh())
    return build_simulation_state(spec, kq)


def _obj(st, i):
    return next(o for o in st["scene"]["objects"] if o["id"] == i)


# ══ 1. GEOMETRY SCENE ════════════════════════════════════════════════════
def test_scene_giu_dung_NAM_LOAI_doi_tuong(st):
    loai = {o["id"]: o["type"] for o in st["scene"]["objects"]}
    assert loai["A"] == "point3" and loai["M"] == "point3"
    assert loai["day"] == "plane3"
    assert loai["chop"] == "solid"
    assert loai["V"] == "quantity"


def test_toa_do_dung_va_CHINH_XAC(st):
    assert _obj(st, "S")["xyz"] == ["0", "0", "2"]
    # M = trung điểm AB = (1/2, 0, 0). Đây là chỗ float sẽ lộ ra ngay.
    assert _obj(st, "M")["xyz"] == ["1/2", "0", "0"]


def test_KHONG_CO_FLOAT_o_bat_ky_dau(st):
    """Ranh giới ② — quét toàn cây, không chỉ vài trường đã nghĩ ra.

    Kernel so **bằng đúng**, không epsilon. Một `0.5` lọt vào JSON là vứt bỏ
    đúng thứ làm hệ này khác một bộ vẽ hình, ở đúng chỗ không ai nhìn.
    """
    def di(x, p="") -> None:
        if isinstance(x, float):
            raise AssertionError(f"float lọt vào SimulationState tại {p}: {x}")
        if isinstance(x, dict):
            for k, v in x.items():
                di(v, f"{p}.{k}")
        elif isinstance(x, (list, tuple)):
            for i, v in enumerate(x):
                di(v, f"{p}[{i}]")

    di(st)


def test_moi_so_deu_DOC_NGUOC_duoc_thanh_Fraction(st):
    """Chuỗi phân số phải là biểu diễn KHÔNG MẤT MÁT, không phải cách hiển thị."""
    for o in st["scene"]["objects"]:
        for s in o.get("xyz", []) + [o.get("value")]:
            if s is not None:
                Fraction(s)
    assert Fraction(_obj(st, "V")["value"]) == Fraction(2, 3)


def test_FREE_va_DERIVED_phan_biet_dung(st):
    for t in "ABCDS":
        assert _obj(st, t)["origin"] == "free", t
    for t in ("M", "day", "chop", "V"):
        assert _obj(st, t)["origin"] == "derived", t
    assert st["free_objects"] == ["A", "B", "C", "D", "S"]


def test_DERIVED_mang_theo_PHEP_DUNG_sinh_ra_no(st):
    """"Biểu diễn được hình học được tạo ra THẾ NÀO" — đây là chỗ câu đó thành
    dữ liệu."""
    # `construct_point.midpoint`, không phải `construct_point` trần: PHÉP DỰNG
    # nào sinh ra M mới là thứ học sinh cần thấy. Cùng khuôn `measure.volume`.
    assert _obj(st, "M")["producer"] == "construct_point.midpoint"
    assert _obj(st, "M")["sources"] == ["A", "B"]
    assert _obj(st, "day")["producer"] == "construct_plane"
    assert _obj(st, "day")["sources"] == ["A", "B", "C"]
    assert _obj(st, "chop")["sources"] == ["A", "B", "C", "D", "S"]
    assert _obj(st, "V")["producer"] == "measure.volume"


def test_FREE_khong_co_producer(st):
    assert _obj(st, "A")["producer"] is None and _obj(st, "A")["sources"] == []


def test_line3_va_plane3_CHO_PROVENANCE_thay_vi_bien(st):
    """Ranh giới ① dưới dạng cụ thể nhất.

    `Plane3` là `n·x = d` — VÔ HẠN. Muốn vẽ thì cần biên hữu hạn, và biên ấy
    KHÔNG có trong kernel. Lớp này **không tính** biên: nó chở tên ba điểm định
    nghĩa, và renderer dựng biên từ toạ độ đã có sẵn trong cảnh.
    """
    p = _obj(st, "day")
    assert "boundary" not in p, "lớp chiếu đã TÍNH biên — vi phạm ranh giới"
    assert p["sources"] == ["A", "B", "C"]
    assert set(p) >= {"point", "normal"}


def test_nhan_LABEL_do_chuong_trinh_dat(st):
    assert _obj(st, "day")["label"] == "(ABCD)"
    assert _obj(st, "chop")["label"] == "S.ABCD"
    assert _obj(st, "A")["label"] == "A"


def test_doi_tuong_CHUA_DUNG_khong_vao_canh():
    """Khai `initial_value: null` mà câu lệnh chưa chạy tới ⇒ `None` trong bộ
    nhớ. Dựng một ô rỗng trong cảnh là mời renderer vẽ một thứ không tồn tại."""
    ct = _chuong_trinh()
    ct["memory_declarations"].append({"name": "H", "type": "point3"})
    spec, kq = _chay(ct)
    assert "H" not in {o["id"] for o in build_scene(spec, kq.final_memory)["objects"]}


def test_bien_TIN_HOC_khong_vao_canh_3D():
    """Một `array` không thuộc cảnh hình học. Nhét vào là mời renderer đoán."""
    spec, kq = _chay({
        "spec_version": "1.0", "title": "Dãy số Tin học",
        "memory_declarations": [
            {"name": "day", "type": "array", "initial_value": [3, 1, 2]},
            {"name": "n", "type": "int", "initial_value": 3},
        ],
        "statements": [], "visual_bindings": {},
    })
    assert build_scene(spec, kq.final_memory)["objects"] == []


# ══ 2. DEPENDENCY GRAPH ══════════════════════════════════════════════════
def test_diem_phu_thuoc_DIEM(st):
    assert st["dependencies"]["M"] == ["A", "B"]


def test_mat_phang_phu_thuoc_DIEM(st):
    assert st["dependencies"]["day"] == ["A", "B", "C"]


def test_khoi_phu_thuoc_DIEM(st):
    assert st["dependencies"]["chop"] == ["A", "B", "C", "D", "S"]


def test_dai_luong_phu_thuoc_KHOI(st):
    assert st["dependencies"]["V"] == ["chop"]


def test_duong_phu_thuoc_DIEM():
    ct = _chuong_trinh()
    ct["memory_declarations"].append({"name": "d", "type": "line3"})
    ct["statements"].insert(1, {"kind": "construct_line", "target_var": "d",
                                "through_a": "A", "through_b": "S"})
    spec, _ = _chay(ct)
    assert dependency_graph(spec)["d"] == ["A", "S"]


def test_thiet_dien_phu_thuoc_KHOI_va_MAT():
    """⚠️ Bản đầu của test này cắt khối bằng chính MẶT ĐÁY của nó, và kernel ném
    `CONTAINED_INFINITE_INTERSECTION` — **kernel đúng, test sai**: mặt đáy nằm
    TRONG mặt phẳng cắt nên thiết diện suy biến thành chính mặt đó. Ghi lại vì
    đây là đúng loại lỗi mà một bộ vẽ hình dùng epsilon sẽ nuốt mất."""
    ct = _chuong_trinh()
    ct["memory_declarations"] += [
        {"name": "P1", "type": "point3"}, {"name": "P2", "type": "point3"},
        {"name": "P3", "type": "point3"}, {"name": "mp", "type": "plane3"},
        {"name": "td", "type": "polygon3"},
    ]
    ct["statements"] += [
        {"kind": "construct_point", "target_var": "P1",
         "expr": {"kind": "midpoint", "a": "A", "b": "S"}},
        {"kind": "construct_point", "target_var": "P2",
         "expr": {"kind": "midpoint", "a": "B", "b": "S"}},
        {"kind": "construct_point", "target_var": "P3",
         "expr": {"kind": "midpoint", "a": "C", "b": "S"}},
        {"kind": "construct_plane", "target_var": "mp",
         "through": ["P1", "P2", "P3"]},
        {"kind": "construct_section", "target_var": "td",
         "solid": "chop", "plane": "mp"},
    ]
    spec, _ = _chay(ct)
    assert dependency_graph(spec)["td"] == ["chop", "mp"]


def test_do_thi_chi_chua_TEN_DA_KHAI():
    """Rác trong đồ thị làm renderer tô sáng một đối tượng không tồn tại."""
    spec, _ = _chay(_chuong_trinh())
    khai = {d.name for d in spec.memory_declarations}
    for nguon in dependency_graph(spec).values():
        assert set(nguon) <= khai


def test_KHONG_dung_do_thi_de_tham_dinh():
    """Ghi thành test vì nó là ranh giới, không phải lời dặn: C₁a có bản riêng
    và bản đó mới là cổng. Dùng bản này để gác cửa thì tầng TRÌNH BÀY trở thành
    tầng THẨM ĐỊNH, và một thay đổi thẩm mỹ sẽ đổi được phán quyết."""
    import ast
    from pathlib import Path

    goc = Path(__file__).resolve().parents[2] / "app" / "simulation"
    for f in goc.rglob("*.py"):
        if f.name == "simulation_state.py":
            continue
        cay = ast.parse(f.read_text(encoding="utf-8"))
        ten = {n.func.attr for n in ast.walk(cay)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        ten |= {n.func.id for n in ast.walk(cay)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert "dependency_graph" not in ten, (
            f"{f.name} gọi dependency_graph — nó là API TRÌNH BÀY, không phải "
            "cổng thẩm định"
        )


# ══ 3. TIMELINE ══════════════════════════════════════════════════════════
def test_timeline_dung_THU_TU_va_KHONG_MAT_BUOC(st):
    """⚠️ Bước ĐẦU TIÊN là `system` — interpreter phát một bước khởi tạo bộ nhớ
    trước mọi câu lệnh. Bản đầu của test này bỏ qua nó và ĐỎ; interpreter đúng.

    Bước ấy có nghĩa sư phạm thật: nó là *"đây là những gì đề cho, trước khi ta
    dựng gì cả"* — khung hình đầu của mô phỏng."""
    tl = st["timeline"]
    assert [b["step_index"] for b in tl] == list(range(len(tl)))
    assert tl[0]["action"] == "init"
    assert [b["created"] for b in tl[1:]] == ["M", "day", "chop", "V"]


def test_moi_buoc_du_NAM_thanh_phan(st):
    for b in st["timeline"]:
        for k in ("step_index", "action", "created", "depends_on",
                  "explanation"):
            assert k in b, k
        assert b["explanation"], "bước không có lời kể"


def test_buoc_mang_dung_PHU_THUOC(st):
    b = next(x for x in st["timeline"] if x["created"] == "day")
    assert b["depends_on"] == ["A", "B", "C"]


def test_timeline_khop_MOT_DOI_MOT_voi_trace(st):
    """Bất biến #31 (`frame k ⇔ trace[k]`) áp thẳng — không gộp, không cắt."""
    spec, kq = _chay(_chuong_trinh())
    assert len(build_timeline(spec, kq)) == len(kq.trace) == kq.total_steps


def test_THIET_DIEN_sinh_MOT_BUOC_MOI_CANH():
    """Bài "dựng thiết diện" có timeline đúng như học sinh làm trên giấy — và
    điều đó ĐÃ CÓ SẴN trong trace, không phải thêm gì."""
    ct = _chuong_trinh()
    ct["memory_declarations"] += [
        {"name": "M1", "type": "point3"}, {"name": "M2", "type": "point3"},
        {"name": "M3", "type": "point3"}, {"name": "mp", "type": "plane3"},
        {"name": "td", "type": "polygon3"},
    ]
    ct["statements"] += [
        {"kind": "construct_point", "target_var": "M1",
         "expr": {"kind": "midpoint", "a": "A", "b": "S"}},
        {"kind": "construct_point", "target_var": "M2",
         "expr": {"kind": "midpoint", "a": "B", "b": "S"}},
        {"kind": "construct_point", "target_var": "M3",
         "expr": {"kind": "midpoint", "a": "C", "b": "S"}},
        {"kind": "construct_plane", "target_var": "mp",
         "through": ["M1", "M2", "M3"]},
        {"kind": "construct_section", "target_var": "td",
         "solid": "chop", "plane": "mp"},
    ]
    spec, kq = _chay(ct)
    canh = [b for b in build_timeline(spec, kq) if b["action"] == "section_edge"]
    assert len(canh) >= 3, "thiết diện không sinh bước theo từng cạnh"
    assert all("mat" in b["details"] for b in canh), "bước cạnh thiếu face_index"


# ══ 4. RANH GIỚI KIẾN TRÚC ═══════════════════════════════════════════════
def test_lop_nay_KHONG_TINH_hinh_hoc():
    """Ranh giới ① ở tầng import — bắt cả thứ chưa ai viết.

    Test hành vi chỉ bắt được ca ta nghĩ ra. Cấm gọi kernel ở tầng cú pháp thì
    một `cross`/`dot`/`intersect_*` lẻn vào sau này sẽ ĐỎ ngay, kể cả khi tác
    giả của nó tin là mình đang tối ưu.
    """
    import ast
    from pathlib import Path

    p = (Path(__file__).resolve().parents[2] / "app" / "simulation"
         / "semantic_program" / "simulation_state.py")
    cay = ast.parse(p.read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    goi |= {n.func.id for n in ast.walk(cay)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    cam = {"cross", "dot", "det3", "intersect_line_plane", "intersect_plane_plane",
           "project_point_onto_plane", "project_point_onto_line", "midpoint",
           "divide_segment", "cross_section", "volume_tetrahedron",
           "volume_pyramid_fan", "distance_sq", "cos_sq_between_lines"}
    lo = goi & cam
    assert not lo, f"lớp chiếu gọi phép hình học: {sorted(lo)}"

    nhap: list[str] = []
    for n in ast.walk(cay):
        if isinstance(n, ast.ImportFrom) and n.module:
            nhap += [f"{n.module}.{a.name}" for a in n.names]
    xau = [x for x in nhap if "kernel" in x or "measure" in x or "predicates" in x]
    assert not xau, f"lớp chiếu nhập module tính toán: {xau}"


def test_KHONG_module_nao_o_TANG_DUOI_nhap_lop_nay():
    """Hướng phụ thuộc một chiều: interpreter/validator/kernel KHÔNG được biết
    tới tầng mô phỏng. Đảo chiều là buộc engine vào nhu cầu trình bày."""
    import ast
    from pathlib import Path

    goc = Path(__file__).resolve().parents[2] / "app" / "simulation"
    for f in goc.rglob("*.py"):
        if f.name == "simulation_state.py":
            continue
        cay = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            mod = (n.module if isinstance(n, ast.ImportFrom) else None)
            assert not (mod and "simulation_state" in mod), f.name


def test_serialize_duoc_ra_JSON(st):
    import json

    json.dumps(st, ensure_ascii=False)
