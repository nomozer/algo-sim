# -*- coding: utf-8 -*-
"""PHASE 5C — Scene3D adapter. **0 API call.**

    SimulationState → **Scene3D** → Renderer 3D (Phase 5D)

Bốn nhóm theo STEP 9: Adapter · Exact value · Dependency · Architecture boundary.

Thứ file này khoá chặt nhất là **ranh giới import**: `scene3d.py` nhận `dict`,
trả `dict`, và **không biết gì** về kernel/validator/oracle. Ở
`simulation_state.py` phải quét `ast` tìm lời gọi bị cấm; ở đây ranh giới rút
gọn thành *"danh sách import phải rỗng"* — máy kiểm được trong một dòng, và
không có cách nào lách.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import (
    RENDER_HINT,
    build_scene3d,
    build_scene_events,
)
from app.simulation.semantic_program.simulation_state import build_simulation_state


def _chuong_trinh() -> dict:
    """Chóp S.ABCD cạnh 1, SA ⊥ đáy, SA = 2 — phủ điểm · đường · mặt · khối ·
    thiết diện · đại lượng."""
    diem = {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0],
            "D": [0, 1, 0], "S": [0, 0, 2]}
    return {
        "spec_version": "1.0",
        "title": "Chóp S.ABCD — cảnh 3D",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v,
             "model_assumption": "hệ trục đã chọn"} for n, v in diem.items()
        ] + [
            {"name": "M", "type": "point3"},
            {"name": "d", "type": "line3"},
            {"name": "day", "type": "plane3"},
            {"name": "chop", "type": "solid"},
            {"name": "P1", "type": "point3"}, {"name": "P2", "type": "point3"},
            {"name": "P3", "type": "point3"}, {"name": "mp", "type": "plane3"},
            {"name": "td", "type": "polygon3"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_point", "target_var": "M", "label": "M",
             "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
            {"kind": "construct_line", "target_var": "d", "label": "AS",
             "through_a": "A", "through_b": "S"},
            {"kind": "construct_plane", "target_var": "day",
             "through": ["A", "B", "C"], "label": "(ABCD)"},
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": ["A", "B", "C", "D", "S"],
             "faces": [["A", "B", "C", "D"], ["A", "B", "S"], ["B", "C", "S"],
                       ["C", "D", "S"], ["D", "A", "S"]], "label": "S.ABCD"},
            {"kind": "construct_point", "target_var": "P1",
             "expr": {"kind": "midpoint", "a": "A", "b": "S"}},
            {"kind": "construct_point", "target_var": "P2",
             "expr": {"kind": "midpoint", "a": "B", "b": "S"}},
            {"kind": "construct_point", "target_var": "P3",
             "expr": {"kind": "midpoint", "a": "C", "b": "S"}},
            {"kind": "construct_plane", "target_var": "mp",
             "through": ["P1", "P2", "P3"], "label": "(P1P2P3)"},
            {"kind": "construct_section", "target_var": "td",
             "solid": "chop", "plane": "mp", "label": "thiết diện"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
        ],
        "visual_bindings": {},
    }


@pytest.fixture(scope="module")
def sc():
    spec = SemanticProgramSpec.model_validate(_chuong_trinh())
    kq = SemanticProgramInterpreter().execute(spec)
    return build_scene3d(build_simulation_state(spec, kq))


def _o(sc, i):
    return next(x for x in sc["objects"] if x["id"] == i)


# ══ 1. ADAPTER — từng loại chuyển đúng ═══════════════════════════════════
def test_POINT_chuyen_dung(sc):
    p = _o(sc, "M")
    assert p["type"] == "point3" and p["render"] == "point_marker"
    assert p["xyz"] == ["1/2", "0", "0"]


def test_LINE_chuyen_dung_va_KHONG_co_doan(sc):
    """`Line3` VÔ HẠN. Cắt nó thành đoạn là quyết định TRÌNH BÀY — renderer làm,
    dựa trên `depends` mà toạ độ đã có sẵn trong cùng cảnh."""
    l = _o(sc, "d")
    assert l["render"] == "line"
    assert set(l) >= {"point", "direction"}
    assert "segment" not in l and "endpoints" not in l
    assert l["depends"] == ["A", "S"]


def test_PLANE_chuyen_dung_va_KHONG_co_hinh_chu_nhat(sc):
    """Yêu cầu tường minh của STEP 4: không được biến `Plane3` thành hình chữ
    nhật cố định trong tầng ngữ nghĩa."""
    p = _o(sc, "day")
    assert p["render"] == "surface"
    for cam in ("boundary", "rect", "corners", "size", "extent"):
        assert cam not in p, f"tầng ngữ nghĩa đã chốt {cam} — renderer mất quyền"
    assert p["depends"] == ["A", "B", "C"]


def test_SOLID_chuyen_dung(sc):
    s = _o(sc, "chop")
    assert s["render"] == "mesh"
    assert len(s["vertices"]) == 5 and len(s["faces"]) == 5
    assert s["faces"][0] == [0, 1, 2, 3]


def test_SECTION_chuyen_dung(sc):
    t = _o(sc, "td")
    assert t["render"] == "polygon"
    assert len(t["polygon"]) >= 3 and t["closed"] is True


def test_DAI_LUONG_khong_ve_duoc_nhung_VAN_hien(sc):
    """Bỏ nó khỏi cảnh thì mô phỏng chạy xong mà học sinh không thấy đáp số —
    đúng điều `learner_surface` sinh ra để chặn."""
    v = _o(sc, "V")
    assert v["render"] == "readout"
    assert Fraction(v["value"]) == Fraction(2, 3)


def test_bang_RENDER_HINT_la_bang_DONG(sc):
    """Không `cylinder`/`sphere`/`curve`: chúng chưa có trong hợp đồng ngữ
    nghĩa. Thêm ở đây là để tầng TRÌNH BÀY đẻ ra năng lực mà tầng SINH không
    có — renderer sẽ vẽ được thứ không chương trình nào tạo ra nổi."""
    assert set(RENDER_HINT) == {
        "point3", "line3", "plane3", "solid", "polygon3", "section", "quantity",
    }
    for cam in ("cylinder", "sphere", "curve", "torus", "cone"):
        assert cam not in RENDER_HINT.values()


def test_loai_LA_bi_BO_QUA_khong_doan_hinh(sc):
    lac = build_scene3d({"scene": {"objects": [
        {"id": "x", "label": "x", "type": "graph", "origin": "free"},
    ]}})
    assert lac["objects"] == []


# ══ 2. EXACT VALUE ═══════════════════════════════════════════════════════
def test_KHONG_CO_FLOAT_o_bat_ky_dau(sc):
    def di(x, p=""):
        if isinstance(x, float):
            raise AssertionError(f"float lọt vào Scene3D tại {p}: {x}")
        if isinstance(x, dict):
            for k, v in x.items():
                di(v, f"{p}.{k}")
        elif isinstance(x, (list, tuple)):
            for i, v in enumerate(x):
                di(v, f"{p}[{i}]")

    di(sc)


def test_moi_toa_do_DOC_NGUOC_duoc_thanh_Fraction(sc):
    for o in sc["objects"]:
        for nhom in ("xyz", "point", "normal", "direction", "value"):
            v = o.get(nhom)
            if isinstance(v, str):
                Fraction(v)
            elif isinstance(v, list):
                for s in v:
                    Fraction(s)


def test_toa_do_KHONG_MAT_MAT_qua_ca_chuoi():
    """Bằng chứng đầu-cuối: `1/2` đi từ kernel tới Scene3D vẫn là `1/2`, không
    phải `0.5` hay `0.49999999999999994`."""
    spec = SemanticProgramSpec.model_validate(_chuong_trinh())
    kq = SemanticProgramInterpreter().execute(spec)
    assert kq.final_memory["M"].x == Fraction(1, 2)
    sc = build_scene3d(build_simulation_state(spec, kq))
    assert _o(sc, "M")["xyz"][0] == "1/2"


def test_serialize_duoc_ra_JSON(sc):
    import json

    json.dumps(sc, ensure_ascii=False)


# ══ 3. DEPENDENCY — provenance không được phẳng hoá ══════════════════════
def test_derived_giu_PRODUCER(sc):
    assert _o(sc, "M")["producer"] == "construct_point.midpoint"
    assert _o(sc, "day")["producer"] == "construct_plane"
    assert _o(sc, "chop")["producer"] == "construct_solid"
    assert _o(sc, "V")["producer"] == "measure.volume"
    assert _o(sc, "td")["producer"] == "construct_section"


def test_free_va_derived_phan_biet(sc):
    assert all(_o(sc, t)["origin"] == "free" for t in "ABCDS")
    assert all(_o(sc, t)["origin"] == "derived"
               for t in ("M", "d", "day", "chop", "mp", "td", "V"))
    assert sc["free_objects"] == ["A", "B", "C", "D", "S"]


def test_dependency_KHONG_bi_mat(sc):
    assert _o(sc, "M")["depends"] == ["A", "B"]
    assert _o(sc, "chop")["depends"] == ["A", "B", "C", "D", "S"]
    assert _o(sc, "td")["depends"] == ["chop", "mp"]
    assert _o(sc, "V")["depends"] == ["chop"]


def test_KHONG_PHANG_HOA_thanh_toa_do_tran(sc):
    """`M = [1,2,3]` là hình dạng bị cấm: nó mất `producer` và `depends`, tức
    mất khả năng mô phỏng thay đổi (Phase 5E không biết kéo cái gì hợp lệ)."""
    for o in sc["objects"]:
        assert "origin" in o and "depends" in o
        if o["origin"] == "derived":
            assert o["producer"], f"{o['id']} là derived mà mất producer"


# ══ 4. EVENTS — phát từng bước ═══════════════════════════════════════════
def test_events_MOT_DOI_MOT_voi_timeline(sc):
    spec = SemanticProgramSpec.model_validate(_chuong_trinh())
    kq = SemanticProgramInterpreter().execute(spec)
    st = build_simulation_state(spec, kq)
    assert len(build_scene_events(st)) == len(st["timeline"]) == len(kq.trace)


def test_events_dung_THU_TU_va_HANH_DONG(sc):
    ev = sc["events"]
    assert [e["step_index"] for e in ev] == list(range(len(ev)))
    assert ev[0]["action"] == "INIT"
    assert ev[1]["action"] == "CREATE" and ev[1]["object"] == "M"
    assert any(e["action"] == "MEASURE" and e["object"] == "V" for e in ev)


def test_THIET_DIEN_phat_EXTEND_tung_canh(sc):
    """Kernel sinh MỘT bước cho MỖI CẠNH — đó là dãy thao tác học sinh làm trên
    giấy: nối dần từng cạnh, không phải hiện cả đa giác một lúc."""
    ex = [e for e in sc["events"] if e["action"] == "EXTEND"]
    assert len(ex) >= 3, "thiết diện không phát sự kiện theo từng cạnh"


def test_moi_event_co_LOI_KE(sc):
    assert all(e["explanation"] for e in sc["events"])


# ══ 5. RANH GIỚI KIẾN TRÚC — cưỡng chế ở tầng IMPORT ═════════════════════
def _imports(ten: str) -> list[str]:
    import ast
    from pathlib import Path

    p = (Path(__file__).resolve().parents[2] / "app" / "simulation"
         / "semantic_program" / ten)
    cay = ast.parse(p.read_text(encoding="utf-8"))
    ra: list[str] = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module:
            ra.append(n.module)
    return ra


def test_scene3d_KHONG_nhap_gi_tu_tang_hinh_hoc():
    """Ranh giới mạnh nhất trong cả chuỗi, và nó rút gọn thành MỘT mệnh đề:
    module này nhận `dict`, trả `dict`, không biết gì về hình học.

    `simulation_state.py` **buộc** phải biết `Vec3` để đọc bộ nhớ, nên ở đó
    ranh giới phải quét tên hàm bị cấm. Ở đây không cần biết gì cả — nên không
    có cách nào để một phép hình học lẻn vào, kể cả khi ai đó rất muốn.
    """
    xau = [m for m in _imports("scene3d.py")
           if m not in ("__future__", "typing")]
    assert not xau, f"scene3d nhập ngoài phạm vi: {xau}"


@pytest.mark.parametrize("cam", [
    "geometry", "kernel", "predicates", "measure", "exact", "section",
    "validator", "postconditions", "coverage_gate", "grounding_gate",
    "obligations", "interpreter", "contract", "route",
])
def test_scene3d_KHONG_cham_kernel_validator_oracle(cam):
    assert not any(cam in m for m in _imports("scene3d.py"))


def test_KHONG_module_nao_o_TANG_DUOI_nhap_scene3d():
    """Hướng phụ thuộc một chiều. Đảo chiều là buộc engine vào nhu cầu trình
    bày — một đổi màu sẽ làm bẩn `measured_system_hash`."""
    import ast
    from pathlib import Path

    goc = Path(__file__).resolve().parents[2] / "app" / "simulation"
    for f in goc.rglob("*.py"):
        if f.name == "scene3d.py":
            continue
        cay = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            mod = n.module if isinstance(n, ast.ImportFrom) else None
            assert not (mod and "scene3d" in mod), f.name


def test_KHONG_trung_ten_voi_VisualTraceAdapter_da_co():
    """`visual_adapter.VisualTraceAdapter` đã tồn tại và làm việc KHÁC HẲN: nó
    biến trace thành `VisualFrame[]` cho chín nguyên thuỷ 2D qua
    `visual_bindings`. Trùng tên là mời người sau đọc nhầm hai đường."""
    from app.simulation.semantic_program import scene3d, visual_adapter

    assert hasattr(visual_adapter, "VisualTraceAdapter")
    assert not hasattr(scene3d, "VisualTraceAdapter")
