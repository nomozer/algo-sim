# -*- coding: utf-8 -*-
"""M8-PRE (S2): edge CÓ CHIỀU + sơ đồ hệ thống thông tin.

Khoá ba thứ:
1. `directed` dẫn xuất đúng kiến trúc (manifest → validator → schema → contract).
   Anti-pattern #1: schema viết tay thiếu field → Gemini KHÔNG THỂ phát ra dù
   prompt cho phép (đã từng xảy ra với `drag`).
2. Cạnh KHÔNG khai directed vẫn y như cũ (thay đổi thuần bổ sung).
3. RANH GIỚI SƯ PHẠM: sơ đồ TĨNH không được tự nhận là mô phỏng chạy được.
"""

from app.simulation.catalog import CATALOG
from app.simulation.dsl import manifest as M
from app.simulation.dsl.validator import validate_generic_config
from app.simulation.patch import ADD_FIELDS
from app.simulation.semantic import check_semantic, check_system_flow_consistency


def _spec(objects, processes=None):
    return {
        "dsl_version": "1.0",
        "title": "Hệ thống quản lí điểm",
        "objects": objects,
        "rules": [],
        "interactions": [],
        "processes": processes or [],
    }


_SYS_OBJECTS = [
    {"id": "gv", "type": "node", "node_type": "actor", "label": "Giáo viên", "x": 15, "y": 30},
    {"id": "nhap", "type": "node", "node_type": "process", "label": "Nhập điểm", "x": 50, "y": 30},
    {"id": "kho", "type": "node", "node_type": "data_store", "label": "CSDL điểm", "x": 85, "y": 30},
    {"id": "f1", "type": "edge", "from": "gv", "to": "nhap", "directed": True},
    {"id": "f2", "type": "edge", "from": "nhap", "to": "kho", "directed": True},
]


# ── 1. Validator: directed dẫn xuất, chỉ nhận bool THẬT, chỉ trên edge ──

def test_validator_giu_directed_tren_edge():
    cfg, err = validate_generic_config(_spec(_SYS_OBJECTS))
    assert err is None, err
    edges = {o["id"]: o for o in cfg["objects"] if o["type"] == "edge"}
    assert edges["f1"]["directed"] is True
    assert edges["f2"]["directed"] is True


def test_edge_khong_khai_directed_giu_nguyen_nhu_cu():
    """Thay đổi THUẦN BỔ SUNG: spec cũ (không có directed) không đổi hành vi."""
    objs = [
        {"id": "a", "type": "node", "x": 10, "y": 10},
        {"id": "b", "type": "node", "x": 40, "y": 40},
        {"id": "e", "type": "edge", "from": "a", "to": "b"},
    ]
    cfg, err = validate_generic_config(_spec(objs))
    assert err is None
    edge = next(o for o in cfg["objects"] if o["type"] == "edge")
    assert "directed" not in edge  # không tự bịa mặc định


def test_directed_khong_phai_bool_thi_bo_qua():
    """0/1/"true" KHÔNG phải bool → bỏ qua, không crash, không coi là có chiều."""
    for bad in (1, 0, "true", "yes", None):
        objs = [
            {"id": "a", "type": "node", "x": 10, "y": 10},
            {"id": "b", "type": "node", "x": 40, "y": 40},
            {"id": "e", "type": "edge", "from": "a", "to": "b", "directed": bad},
        ]
        cfg, err = validate_generic_config(_spec(objs))
        assert err is None
        edge = next(o for o in cfg["objects"] if o["type"] == "edge")
        assert "directed" not in edge, f"directed={bad!r} không được nhận"


def test_directed_tren_object_khong_phai_edge_thi_bo_qua():
    objs = [{"id": "n", "type": "node", "x": 10, "y": 10, "directed": True}]
    cfg, err = validate_generic_config(_spec(objs))
    assert err is None
    assert "directed" not in cfg["objects"][0]


# ── 2. Dẫn xuất từ manifest (chống drift — anti-pattern #1) ──

def test_generic_schema_co_directed_dan_xuat():
    props = CATALOG["generic.rule_scene"].config_schema["properties"]["objects"]["items"]["properties"]
    assert "directed" in props, "schema thiếu directed → Gemini KHÔNG THỂ phát ra"
    assert props["directed"]["type"] == "BOOLEAN"


def test_contract_va_capability_summary_noi_ve_directed_va_vai_tro_he_thong():
    contract = M.manifest_contract_text()
    summary = M.manifest_capability_summary()
    assert "directed" in contract
    for role in ("actor", "process", "data_store"):
        assert role in contract, f"contract chưa nêu node_type {role}"
        assert role in summary, f"capability summary chưa nêu node_type {role}"


def test_node_type_vocabulary_la_goi_y_khong_phai_allowlist():
    vocab = M.node_type_vocabulary()
    assert "actor" in vocab["system"] and "router" in vocab["network"]
    # node_type TỰ DO: validator vẫn nhận giá trị ngoài từ vựng gợi ý
    objs = [{"id": "n", "type": "node", "node_type": "bo_phan_kho", "x": 10, "y": 10}]
    cfg, err = validate_generic_config(_spec(objs))
    assert err is None and cfg["objects"][0]["node_type"] == "bo_phan_kho"


def test_patch_add_fields_co_directed():
    assert "directed" in ADD_FIELDS


# ── 3. Ranh giới sư phạm: tĩnh ≠ chạy được (thực thi, không chỉ tuyên bố) ──

def test_system_flow_tinh_dat():
    ok, detail = check_semantic(
        _spec(_SYS_OBJECTS), {"kind": "system_flow", "min_directed": 2, "moving": False}
    )
    assert ok, detail


def test_system_flow_thieu_chieu_thi_truot():
    objs = [dict(o) for o in _SYS_OBJECTS]
    for o in objs:
        o.pop("directed", None)
    ok, detail = check_semantic(
        _spec(objs), {"kind": "system_flow", "min_directed": 2, "moving": False}
    )
    assert not ok and "chiều" in detail


def test_so_do_tinh_khong_duoc_gia_vo_chay_duoc():
    """Cảnh tĩnh mà nhét process diễn biến → TRƯỢT (chống 'fake executable')."""
    spec = _spec(
        _SYS_OBJECTS,
        processes=[{"type": "reveal_sequence", "steps": [{"objects": ["gv"]}, {"objects": ["nhap"]}]}],
    )
    ok, detail = check_semantic(spec, {"kind": "system_flow", "min_directed": 2, "moving": False})
    assert not ok and "giả vờ" in detail


# ── 3b. CHIỀU được SUY, không đi xin LLM ──
# Đo live (M8-PRE): Gemini dựng đúng actor→process→data_store trong from/to nhưng
# BỎ QUA `directed` kể cả khi prompt yêu cầu tường minh VÀ kể cả sau khi bị từ chối
# kèm lý do. Hướng đã nằm sẵn trong from/to → server tự suy, không phụ thuộc LLM.

def test_validator_SUY_directed_cho_luong_he_thong():
    objs = [dict(o) for o in _SYS_OBJECTS]
    for o in objs:
        o.pop("directed", None)  # LLM không khai — đúng như thực tế live
    cfg, err = validate_generic_config(_spec(objs))
    assert err is None
    edges = [o for o in cfg["objects"] if o["type"] == "edge"]
    assert all(e.get("directed") is True for e in edges), "phải TỰ SUY chiều từ from/to"


def test_KHONG_suy_directed_cho_topology_mang():
    """Liên kết mạng là HAI CHIỀU — không được tự gắn mũi tên."""
    objs = [
        {"id": "pc", "type": "node", "node_type": "client", "x": 10, "y": 50},
        {"id": "r", "type": "node", "node_type": "router", "x": 50, "y": 50},
        {"id": "e1", "type": "edge", "from": "pc", "to": "r"},
    ]
    cfg, err = validate_generic_config(_spec(objs))
    assert err is None
    assert "directed" not in cfg["objects"][-1]


def test_KHONG_suy_directed_cho_hinh_hoc():
    objs = [
        {"id": "A", "type": "node", "x": 10, "y": 10},
        {"id": "B", "type": "node", "x": 40, "y": 40},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
    ]
    cfg, err = validate_generic_config(_spec(objs))
    assert err is None
    assert "directed" not in cfg["objects"][-1]


def test_directed_false_tuong_minh_duoc_ton_trong():
    """LLM khai rõ false → KHÔNG ghi đè (suy chỉ khi vắng mặt); cổng sẽ bắt sau."""
    objs = [dict(o) for o in _SYS_OBJECTS]
    for o in objs:
        if o["type"] == "edge":
            o["directed"] = False
    cfg, err = validate_generic_config(_spec(objs))
    assert err is None
    assert all(e["directed"] is False for e in cfg["objects"] if e["type"] == "edge")
    assert check_system_flow_consistency(cfg) is not None  # cổng vẫn bắt


# ── 4. Cổng TẤT ĐỊNH: sơ đồ hệ thống PHẢI nêu chiều luồng ──
# Đo live (M8-PRE) cho thấy prompt một mình KHÔNG đủ: LLM dựng đúng node
# actor/process/data_store nhưng BỎ QUA directed → mất đúng giá trị sư phạm.

def test_gate_bat_so_do_he_thong_thieu_chieu():
    objs = [dict(o) for o in _SYS_OBJECTS]
    for o in objs:
        o.pop("directed", None)
    err = check_system_flow_consistency(_spec(objs))
    assert err is not None and "directed" in err


def test_gate_thoa_man_khi_co_directed():
    assert check_system_flow_consistency(_spec(_SYS_OBJECTS)) is None


def test_gate_KHONG_dung_toi_hinh_hoc():
    """node không node_type (điểm hình học) → cổng không được đụng vào."""
    objs = [
        {"id": "A", "type": "node", "x": 10, "y": 10},
        {"id": "B", "type": "node", "x": 40, "y": 40},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
    ]
    assert check_system_flow_consistency(_spec(objs)) is None


def test_gate_KHONG_dung_toi_topology_mang():
    """Liên kết mạng là HAI CHIỀU — không được ép directed lên cảnh mạng."""
    objs = [
        {"id": "pc", "type": "node", "node_type": "client", "x": 10, "y": 50},
        {"id": "r", "type": "node", "node_type": "router", "x": 50, "y": 50},
        {"id": "sv", "type": "node", "node_type": "server", "x": 90, "y": 50},
        {"id": "e1", "type": "edge", "from": "pc", "to": "r"},
        {"id": "e2", "type": "edge", "from": "r", "to": "sv"},
    ]
    assert check_system_flow_consistency(_spec(objs)) is None


def test_system_flow_chay_duoc_can_move_along_path_that():
    objs = [*_SYS_OBJECTS, {"id": "d", "type": "moving_entity", "label": "Bảng điểm"}]
    # thiếu process → không được coi là executable
    ok, _ = check_semantic(_spec(objs), {"kind": "system_flow", "min_directed": 2, "moving": True})
    assert not ok
    # có move_along_path đi qua 3 công đoạn → đạt
    spec = _spec(objs, processes=[{"type": "move_along_path", "entity": "d", "path": ["gv", "nhap", "kho"]}])
    ok, detail = check_semantic(spec, {"kind": "system_flow", "min_directed": 2, "moving": True})
    assert ok, detail
