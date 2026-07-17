# -*- coding: utf-8 -*-
"""Test validator DSL generic (M6) + classify chọn generic + catalog.

§5: validation bắt buộc, reject ref treo / rule lạ / chu trình / quá giới hạn /
arbitrary code. §4: LLM không sinh state/frames/timeline.
"""

import asyncio
import json

from app.ai import pipeline
from app.simulation.catalog import CATALOG
from app.simulation.dsl.validator import validate_generic_config

AND_SPEC = {
    "dsl_version": "1.0",
    "title": "Cổng AND",
    "objects": [
        {"id": "a", "type": "switch", "value": 0},
        {"id": "b", "type": "switch", "value": 0},
        {"id": "y", "type": "lamp"},
    ],
    "rules": [{"type": "boolean", "op": "and", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}],
    "processes": [],
}

PACKET_SPEC = {
    "dsl_version": "1.0",
    "title": "Gói tin",
    "objects": [
        {"id": "c", "type": "node", "node_type": "client"},
        {"id": "s", "type": "node", "node_type": "server"},
        {"id": "e1", "type": "edge", "from": "c", "to": "s"},
        {"id": "pkt", "type": "moving_entity"},
    ],
    "rules": [],
    "interactions": [],
    "processes": [{"type": "move_along_path", "entity": "pkt", "path": ["c", "s"]}],
}


def test_catalog_co_generic():
    assert "generic.rule_scene" in CATALOG
    assert CATALOG["generic.rule_scene"].domain == "generic"


def test_spec_hop_le_duoc_chuan_hoa():
    cfg, err = validate_generic_config(AND_SPEC)
    assert err is None
    assert cfg["title"] == "Cổng AND"
    assert len(cfg["objects"]) == 3
    assert cfg["rules"][0]["op"] == "and"


def test_packet_spec_hop_le():
    cfg, err = validate_generic_config(PACKET_SPEC)
    assert err is None
    assert cfg["processes"][0]["path"] == ["c", "s"]


def test_object_type_la_bi_reject():
    bad = {"title": "x", "objects": [{"id": "a", "type": "hologram"}]}
    assert validate_generic_config(bad)[0] is None


def test_rule_type_la_bi_reject():
    bad = {
        "title": "x",
        "objects": [{"id": "a", "type": "switch", "value": 0}, {"id": "y", "type": "lamp"}],
        "rules": [{"type": "quantum", "inputs": ["a"], "target": "y"}],
    }
    assert validate_generic_config(bad)[0] is None


def test_dangling_reference_bi_reject():
    bad = {
        "title": "x",
        "objects": [{"id": "a", "type": "switch", "value": 0}],
        "rules": [{"type": "boolean", "op": "and", "inputs": ["khong-co"], "target": "a"}],
    }
    assert validate_generic_config(bad)[0] is None


def test_chu_trinh_rule_bi_reject():
    bad = {
        "title": "x",
        "objects": [{"id": "p", "type": "value_box"}, {"id": "q", "type": "value_box"}],
        "rules": [
            {"type": "weighted_sum", "inputs": ["q"], "weights": [1], "target": "p"},
            {"type": "weighted_sum", "inputs": ["p"], "weights": [1], "target": "q"},
        ],
    }
    config, err = validate_generic_config(bad)
    assert config is None
    assert "vòng" in err


# M11: rule lồng qua giá trị trung gian là pattern HỢP LỆ (cycle-detector đã
# lường trước); hai rule cùng ghi MỘT target thì KHÔNG — với đánh giá điểm bất
# động, rule đứng sau trong mảng thắng mỗi vòng quét → ngữ nghĩa phụ thuộc thứ
# tự khai báo. Mỗi giá trị dẫn xuất phải có đúng một rule sở hữu.

NESTED_SPEC = {
    "dsl_version": "1.0",
    "title": "Đèn A và (B hoặc C)",
    "objects": [
        {"id": "a", "type": "switch", "value": 0},
        {"id": "b", "type": "switch", "value": 0},
        {"id": "c", "type": "switch", "value": 0},
        {"id": "t", "type": "lamp", "label": "B hoặc C"},
        {"id": "y", "type": "lamp", "label": "Đèn"},
    ],
    "rules": [
        {"type": "boolean", "op": "or", "inputs": ["b", "c"], "target": "t"},
        {"type": "boolean", "op": "and", "inputs": ["a", "t"], "target": "y"},
    ],
    "interactions": [
        {"type": "toggle", "target": "a"},
        {"type": "toggle", "target": "b"},
        {"type": "toggle", "target": "c"},
    ],
    "processes": [],
}


def test_rule_long_qua_trung_gian_hop_le():
    """Target của rule này làm input rule khác (DAG) phải được chấp nhận."""
    cfg, err = validate_generic_config(NESTED_SPEC)
    assert err is None
    assert len(cfg["rules"]) == 2


def test_hai_rule_cung_target_bi_reject():
    bad = {
        **NESTED_SPEC,
        "rules": [
            {"type": "boolean", "op": "and", "inputs": ["a", "b"], "target": "y"},
            {"type": "boolean", "op": "or", "inputs": ["b", "c"], "target": "y"},
        ],
    }
    config, err = validate_generic_config(bad)
    assert config is None
    assert "y" in err and "rule" in err.lower()


def test_qua_gioi_han_object_bi_reject():
    bad = {"title": "x", "objects": [{"id": f"o{i}", "type": "label"} for i in range(21)]}
    assert validate_generic_config(bad)[0] is None


def test_forbidden_key_bi_reject():
    """§4: LLM không được sinh timeline/state/frames — engine tự dựng."""
    for key in ("timeline", "state", "frames", "steps"):
        bad = {**AND_SPEC, key: []}
        config, err = validate_generic_config(bad)
        assert config is None, f"khóa {key} phải bị từ chối"
        assert "cấm" in err or "engine" in err.lower()


def test_object_weight_bi_tu_choi_khong_strip_im_lang():
    """M13 Task 2b: field không runtime nào đọc mà prompt lại DẠY → từ chối
    tường minh, không nuốt im lặng (LLM phải biết mô hình của nó sai)."""
    spec = {
        "title": "x",
        "objects": [
            {"id": "b0", "type": "switch", "label": "8", "value": 1, "weight": 8},
            {"id": "out", "type": "value_box", "label": "Giá trị"},
        ],
        "rules": [{"type": "weighted_sum", "target": "out", "inputs": ["b0"], "weights": [8]}],
    }
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không còn được hỗ trợ" in err


def test_binary_weighted_sum_khong_can_object_weight_van_dung():
    """Sample nhị phân sau migrate: chỉ rule.weights — vẫn validate + tính đúng."""
    spec = {
        "title": "x",
        "objects": [
            {"id": "b0", "type": "switch", "label": "8", "value": 1},
            {"id": "b1", "type": "switch", "label": "4", "value": 1},
            {"id": "b2", "type": "switch", "label": "2", "value": 0},
            {"id": "b3", "type": "switch", "label": "1", "value": 1},
            {"id": "out", "type": "value_box", "label": "Giá trị"},
        ],
        "rules": [{"type": "weighted_sum", "target": "out",
                "inputs": ["b0", "b1", "b2", "b3"], "weights": [8, 4, 2, 1]}],
    }
    config, err = validate_generic_config(spec)
    assert err is None and config is not None
    from app.simulation.generic_engine import initial_base, values_of
    assert values_of(config, initial_base(config))["out"] == 13  # 1101₂ = 13


# ── M13 Task 3: operand coherence VỚI role-typing (INVALID_SOURCE) ────
# Sự cố gốc: 2 ô weighted_sum lấy input là id CẠNH (edge_AB, edge_BC) — cạnh
# không mang giá trị số, runtime lặng lẽ tính ra 0, cảnh vẫn chạy 10/10 bước.
# Validator cũ chỉ kiểm id TỒN TẠI, không kiểm toán hạng có NGUỒN GIÁ TRỊ.

def _spec(objects, rules=None, processes=None):
    return {
        "dsl_version": "1.0",
        "title": "M13 operand coherence",
        "objects": objects,
        "rules": rules or [],
        "interactions": [],
        "processes": processes or [],
    }


def test_weighted_sum_input_edge_bi_tu_choi():
    """M13 E6: tồn tại id là KHÔNG đủ — edge không có hợp đồng giá trị số."""
    spec = _spec(
        objects=[
            {"id": "a", "type": "node", "label": "A"},
            {"id": "b", "type": "node", "label": "B"},
            {"id": "e1", "type": "edge", "label": "AB", "from": "a", "to": "b"},
            {"id": "kq", "type": "value_box", "label": "Tổng"},
        ],
        rules=[{"type": "weighted_sum", "target": "kq", "inputs": ["e1"], "weights": [1]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không có nguồn giá trị" in err


def test_chuoi_dan_xuat_khai_bao_dao_van_hop_le():
    """M13 §3.2: UNRESOLVED_DERIVED_SOURCE — rule khai trước provider vẫn hợp lệ."""
    spec = _spec(
        objects=[
            {"id": "x", "type": "switch", "label": "X", "value": 1},
            {"id": "mid", "type": "value_box", "label": "Trung gian"},
            {"id": "kq", "type": "value_box", "label": "Kết quả"},
        ],
        rules=[
            # kq phụ thuộc mid — mid được rule SAU định nghĩa: phải hợp lệ.
            {"type": "weighted_sum", "target": "kq", "inputs": ["mid"], "weights": [2]},
            {"type": "weighted_sum", "target": "mid", "inputs": ["x"], "weights": [3]},
        ],
    )
    config, err = validate_generic_config(spec)
    assert err is None and config is not None


def test_boolean_input_value_box_bi_tu_choi():
    """value_box chỉ numeric, không logical → không được nuôi boolean rule."""
    spec = _spec(
        objects=[
            {"id": "v", "type": "value_box", "label": "V", "value": 5},
            {"id": "den", "type": "lamp", "label": "Đèn"},
        ],
        rules=[{"type": "boolean", "op": "not", "target": "den", "inputs": ["v"]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không có nguồn giá trị" in err


def test_provider_thieu_value_bi_tu_choi():
    """switch (provider hợp lệ) nhưng KHÔNG khai value và không là rule target."""
    spec = _spec(
        objects=[
            {"id": "s", "type": "switch", "label": "S"},  # không value
            {"id": "kq", "type": "value_box", "label": "KQ"},
        ],
        rules=[{"type": "weighted_sum", "target": "kq", "inputs": ["s"], "weights": [1]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không có nguồn giá trị" in err


def test_derived_target_sai_role_bi_tu_choi_weighted_sum_nuoi_boolean():
    """M13 blocker 3: numeric output (weighted_sum target) KHÔNG được nuôi boolean
    input — chính là lớp coercion im lặng v>=1. DENY mặc định."""
    spec = _spec(
        objects=[
            {"id": "v", "type": "value_box", "label": "V", "value": 5},
            {"id": "tong", "type": "value_box", "label": "Tổng"},
            {"id": "den", "type": "lamp", "label": "Đèn"},
        ],
        rules=[
            {"type": "weighted_sum", "target": "tong", "inputs": ["v"], "weights": [1]},
            {"type": "boolean", "op": "not", "target": "den", "inputs": ["tong"]},
        ],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "vai trò" in err  # lỗi nêu rõ mismatch output_role ↔ input_role


def test_derived_target_dung_role_van_hop_le_chain_numeric():
    """weighted_sum target (numeric) nuôi weighted_sum input (numeric) — hợp lệ."""
    spec = _spec(
        objects=[
            {"id": "x", "type": "switch", "label": "X", "value": 1},
            {"id": "mid", "type": "value_box", "label": "TG"},
            {"id": "kq", "type": "value_box", "label": "KQ"},
        ],
        rules=[
            {"type": "weighted_sum", "target": "mid", "inputs": ["x"], "weights": [3]},
            {"type": "weighted_sum", "target": "kq", "inputs": ["mid"], "weights": [2]},
        ],
    )
    config, err = validate_generic_config(spec)
    assert err is None and config is not None


def test_rule_output_ghi_vao_target_sai_role_bi_tu_choi():
    """Ràng buộc 2 (duyệt lần 3): weighted_sum (output numeric) KHÔNG được ghi
    vào node (chỉ relational) — target phải CHẤP NHẬN output role của rule."""
    spec = _spec(
        objects=[
            {"id": "v", "type": "value_box", "label": "V", "value": 3},
            {"id": "n1", "type": "node", "label": "N1"},
        ],
        rules=[{"type": "weighted_sum", "target": "n1", "inputs": ["v"], "weights": [1]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không nhận được" in err


def test_rule_output_ghi_vao_target_dung_role_hop_le():
    """boolean (output logical) ghi vào lamp ({logical, numeric}) — hợp lệ."""
    spec = _spec(
        objects=[
            {"id": "s", "type": "switch", "label": "S", "value": 0},
            {"id": "den", "type": "lamp", "label": "Đèn"},
        ],
        rules=[{"type": "boolean", "op": "not", "target": "den", "inputs": ["s"]}],
    )
    config, err = validate_generic_config(spec)
    assert err is None and config is not None


# ── M13 Task 3 Step 5: regression lock cho 3 nhánh matrix §8 đã đúng sẵn
# trong validate_generic_config — khoá lại trước khi mổ tiếp hàm này.

def test_move_along_path_ref_id_khong_phai_node_bi_reject():
    """matrix §8.1 — validator.py đã chặn đúng (path chứa id không phải node), nay khoá lại."""
    spec = _spec(
        objects=[
            {"id": "n1", "type": "node", "label": "A"},
            {"id": "v1", "type": "value_box", "label": "V", "value": 1},
            {"id": "e", "type": "moving_entity", "label": "Gói"},
        ],
        rules=[],
        processes=[{"type": "move_along_path", "entity": "e", "path": ["n1", "v1"]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None and err


def test_move_along_path_ref_id_khong_ton_tai_bi_reject():
    spec = _spec(
        objects=[
            {"id": "n1", "type": "node", "label": "A"},
            {"id": "e", "type": "moving_entity", "label": "Gói"},
        ],
        rules=[],
        processes=[{"type": "move_along_path", "entity": "e", "path": ["n1", "khong_ton_tai"]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None and err


def test_edge_from_to_ref_object_khong_ton_tai_bi_reject():
    spec = _spec(
        objects=[
            {"id": "n1", "type": "node", "label": "A"},
            {"id": "e1", "type": "edge", "label": "AB", "from": "n1", "to": "khong_ton_tai"},
        ],
        rules=[],
    )
    config, err = validate_generic_config(spec)
    assert config is None and err


def test_truong_la_cap_cao_nhat_bi_reject():
    bad = {**AND_SPEC, "script": "alert(1)"}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "lạ" in err


def test_toggle_gia_tri_dan_xuat_bi_reject():
    """Không cho toggle object là target của rule (giá trị dẫn xuất)."""
    bad = {**AND_SPEC, "interactions": [{"type": "toggle", "target": "y"}]}
    assert validate_generic_config(bad)[0] is None


def test_process_entity_khong_phai_moving_entity_bi_reject():
    bad = {
        "title": "x",
        "objects": [{"id": "n1", "type": "node"}, {"id": "n2", "type": "node"}],
        "processes": [{"type": "move_along_path", "entity": "n1", "path": ["n1", "n2"]}],
    }
    assert validate_generic_config(bad)[0] is None


# ── reveal_sequence (M7.7) ────────────────────────────────────

REVEAL_SPEC = {
    "dsl_version": "1.0",
    "title": "Tam giác ABC",
    "objects": [
        {"id": "A", "type": "node"},
        {"id": "B", "type": "node"},
        {"id": "C", "type": "node"},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
        {"id": "AC", "type": "edge", "from": "A", "to": "C"},
        {"id": "BC", "type": "edge", "from": "B", "to": "C"},
    ],
    "rules": [],
    "interactions": [],
    "processes": [
        {"type": "reveal_sequence", "steps": [
            {"objects": ["A", "B"]},
            {"objects": ["AB"]},
            {"objects": ["C"]},
            {"objects": ["AC"]},
            {"objects": ["BC"]},
        ]},
    ],
}


def test_reveal_spec_hop_le():
    cfg, err = validate_generic_config(REVEAL_SPEC)
    assert err is None
    assert cfg["processes"][0]["type"] == "reveal_sequence"
    assert len(cfg["processes"][0]["steps"]) == 5


def test_reveal_ref_object_khong_ton_tai_bi_reject():
    bad = {**REVEAL_SPEC, "processes": [{"type": "reveal_sequence", "steps": [{"objects": ["KHONG_CO"]}]}]}
    assert validate_generic_config(bad)[0] is None


def test_reveal_field_la_bi_reject():
    bad = {**REVEAL_SPEC, "processes": [{"type": "reveal_sequence", "steps": [{"objects": ["A"], "color": "red"}]}]}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "lạ" in err


def test_reveal_qua_gioi_han_step_bi_reject():
    steps = [{"objects": ["A"]} for _ in range(21)]  # > 20
    bad = {**REVEAL_SPEC, "processes": [{"type": "reveal_sequence", "steps": steps}]}
    assert validate_generic_config(bad)[0] is None


def test_reveal_step_rong_bi_reject():
    bad = {**REVEAL_SPEC, "processes": [{"type": "reveal_sequence", "steps": [{"objects": []}]}]}
    assert validate_generic_config(bad)[0] is None


# ── structural/textual primitives (M7.12) ─────────────────────

WEB_SPEC = {
    "dsl_version": "1.0",
    "title": "Trang giới thiệu",
    "objects": [
        {"id": "page", "type": "container", "text": "Trang giới thiệu"},
        {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
        {"id": "p", "type": "paragraph", "text": "Đây là đoạn văn.", "parent": "page"},
    ],
    "rules": [],
    "interactions": [],
    "processes": [],
}


def test_web_structural_spec_hop_le():
    cfg, err = validate_generic_config(WEB_SPEC)
    assert err is None, err
    assert {o["type"] for o in cfg["objects"]} == {"container", "heading", "paragraph"}
    assert cfg["objects"][1]["text"] == "Xin chào"
    assert cfg["objects"][1]["parent"] == "page"


def test_heading_thieu_text_bi_reject():
    bad = {**WEB_SPEC, "objects": [
        {"id": "page", "type": "container"},
        {"id": "h", "type": "heading", "parent": "page"},  # thiếu text
    ]}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "text" in err


def test_parent_khong_phai_container_bi_reject():
    bad = {**WEB_SPEC, "objects": [
        {"id": "h1", "type": "heading", "text": "A"},
        {"id": "h2", "type": "heading", "text": "B", "parent": "h1"},  # parent là heading, không phải container
    ]}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "parent" in err


def test_parent_chu_trinh_bi_reject():
    bad = {**WEB_SPEC, "objects": [
        {"id": "c1", "type": "container", "parent": "c2"},
        {"id": "c2", "type": "container", "parent": "c1"},  # chu trình chứa
    ]}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "chu trình" in err


def test_text_qua_dai_bi_reject():
    bad = {**WEB_SPEC, "objects": [
        {"id": "p", "type": "paragraph", "text": "x" * 501},  # > max_text_len
    ]}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "quá dài" in err


def test_reveal_structural_tung_buoc_hop_le():
    """Web dựng TỪNG BƯỚC: container hiện trước, rồi heading, rồi paragraph."""
    spec = {**WEB_SPEC, "processes": [
        {"type": "reveal_sequence", "steps": [
            {"objects": ["page"]}, {"objects": ["h"]}, {"objects": ["p"]},
        ]},
    ]}
    cfg, err = validate_generic_config(spec)
    assert err is None, err
    assert cfg["processes"][0]["type"] == "reveal_sequence"


# ── M7.13A: drag interaction ──────────────────────────────────

TRIANGLE_DRAG_SPEC = {
    "dsl_version": "1.0",
    "title": "Tam giác kéo được",
    "objects": [
        {"id": "A", "type": "node", "x": 20, "y": 70},
        {"id": "B", "type": "node", "x": 80, "y": 70},
        {"id": "C", "type": "node", "x": 50, "y": 20},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
        {"id": "AC", "type": "edge", "from": "A", "to": "C"},
        {"id": "BC", "type": "edge", "from": "B", "to": "C"},
    ],
    "rules": [],
    "interactions": [
        {"type": "drag", "target": "A"},
        {"type": "drag", "target": "B", "constraints": {"bounds": {"min_x": 10, "max_x": 90}, "snap": 5}},
        {"type": "drag", "target": "C", "constraints": {"axis": "x"}},
    ],
    "processes": [
        {"type": "reveal_sequence", "steps": [
            {"objects": ["A", "B"]}, {"objects": ["AB"]}, {"objects": ["C"]}, {"objects": ["AC", "BC"]},
        ]},
    ],
}


def test_drag_tren_node_hop_le_va_chuan_hoa_constraints():
    cfg, err = validate_generic_config(TRIANGLE_DRAG_SPEC)
    assert err is None, err
    drags = [i for i in cfg["interactions"] if i["type"] == "drag"]
    assert len(drags) == 3
    assert "constraints" not in drags[0]  # không constraints → không thêm khóa thừa
    assert drags[1]["constraints"] == {"bounds": {"min_x": 10, "max_x": 90}, "snap": 5}
    assert drags[2]["constraints"] == {"axis": "x"}


def test_drag_ngoai_allowlist_bi_reject():
    """v1: drag CHỈ áp cho node — edge (vị trí dẫn xuất) và switch bị chặn."""
    for target in ("AB", ):
        bad = {**TRIANGLE_DRAG_SPEC, "interactions": [{"type": "drag", "target": target}]}
        config, err = validate_generic_config(bad)
        assert config is None
        assert "drag" in err
    bad_switch = {**AND_SPEC, "interactions": [{"type": "drag", "target": "a"}]}
    config, err = validate_generic_config(bad_switch)
    assert config is None
    assert "switch" in err


def test_drag_target_khong_ton_tai_bi_reject():
    bad = {**TRIANGLE_DRAG_SPEC, "interactions": [{"type": "drag", "target": "Z"}]}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "không tồn tại" in err


def test_drag_constraints_sai_bi_reject():
    cases = [
        ({"axis": "z"}, "axis"),
        ({"snap": 0}, "snap"),
        ({"snap": -2}, "snap"),
        ({"bounds": {"min_x": 80, "max_x": 20}}, "min"),
        ({"bounds": {"min_x": -5}}, "0–100"),
        ({"bounds": {"left": 0}}, "bounds"),
        ({"gravity": 1}, "Trường lạ"),
    ]
    for constraints, needle in cases:
        bad = {**TRIANGLE_DRAG_SPEC, "interactions": [{"type": "drag", "target": "A", "constraints": constraints}]}
        config, err = validate_generic_config(bad)
        assert config is None, f"constraints {constraints} phải bị reject"
        assert needle in err, f"lỗi cho {constraints} phải nhắc {needle}, nhận: {err}"


def test_ownership_mot_thuoc_tinh_khong_hai_chu():
    """Điều chỉnh #2: cùng (thuộc tính, object) không được vừa interaction vừa
    process điều khiển. v1 allowlist đã chặn drag moving_entity từ trước —
    test helper trực tiếp để khóa quy tắc cho process tương lai."""
    from app.simulation.dsl.validator import ownership_conflict

    procs = [{"type": "move_along_path", "entity": "pkt", "path": ["a", "b"]}]
    # drag đúng vật process đang điều khiển position → conflict
    assert ownership_conflict([{"type": "drag", "target": "pkt"}], procs) is not None
    # node chỉ là WAYPOINT của path (không bị sở hữu position) → drag hợp lệ
    assert ownership_conflict([{"type": "drag", "target": "a"}], procs) is None
    # toggle không đụng position → không conflict
    assert ownership_conflict([{"type": "toggle", "target": "pkt"}], procs) is None


def test_toggle_object_khong_value_bi_reject():
    """M7.13A (phát hiện từ live verify): LLM hay gán toggle cho node/điểm —
    interaction CHẾT vì node không có value. Reject + retry message chỉ sang drag."""
    bad = {**TRIANGLE_DRAG_SPEC, "interactions": [{"type": "toggle", "target": "A"}]}
    config, err = validate_generic_config(bad)
    assert config is None
    assert "drag" in err  # thông báo lỗi phải chỉ đường sang drag
    # toggle trên switch có value vẫn hợp lệ như cũ
    cfg, err2 = validate_generic_config(AND_SPEC)
    assert err2 is None


def test_drag_node_lam_waypoint_van_hop_le():
    """Kéo một node nằm TRONG path của move_along_path là hợp lệ — position
    của node không bị process sở hữu (process sở hữu position của entity)."""
    spec = {
        "dsl_version": "1.0",
        "title": "Gói tin + kéo node",
        "objects": [
            {"id": "c", "type": "node", "node_type": "client"},
            {"id": "s", "type": "node", "node_type": "server"},
            {"id": "e1", "type": "edge", "from": "c", "to": "s"},
            {"id": "pkt", "type": "moving_entity"},
        ],
        "rules": [],
        "interactions": [{"type": "drag", "target": "c"}],
        "processes": [{"type": "move_along_path", "entity": "pkt", "path": ["c", "s"]}],
    }
    cfg, err = validate_generic_config(spec)
    assert err is None, err
    assert cfg["interactions"][0]["type"] == "drag"


# ── classify chọn generic (pipeline mock) ─────────────────────

def _fake_gemini(responses):
    calls = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        calls.append(user_text)
        return responses.pop(0)

    return fake, calls


def test_classify_chon_generic_va_simulate_sinh_spec(monkeypatch):
    analysis = {
        "objects": ["cổng XOR"],
        "data": [],
        "relations": [],
        "processes": [],
        "constraints": [],
        "goal": "Mô phỏng cổng XOR",
        "input_description": "Hai đầu vào",
        "output_description": "Đầu ra XOR",
        "notes": None,
        # M13: đầu ra cổng logic tính TỪ giá trị công tắc cho sẵn bằng rule — rule_derivable.
        "result_ownership": "rule_derivable",
    }
    xor_spec = {
        "dsl_version": "1.0",
        "title": "Cổng XOR",
        "objects": [
            {"id": "a", "type": "switch", "value": 0},
            {"id": "b", "type": "switch", "value": 0},
            {"id": "y", "type": "lamp"},
        ],
        "rules": [{"type": "boolean", "op": "xor", "inputs": ["a", "b"], "target": "y"}],
        "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}],
        "processes": [],
    }
    fake, calls = _fake_gemini(
        [
            json.dumps(analysis),
            json.dumps({"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}),
            json.dumps(xor_spec),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Mô phỏng cổng XOR gồm hai đầu vào.", "khoa-gia"))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "generic.rule_scene"
    assert env["domain"] == "generic"
    assert env["config"]["rules"][0]["op"] == "xor"
    # danh mục trong prompt classify có generic
    assert "generic.rule_scene" in calls[1]


def test_simulate_generic_retry_khi_spec_sai(monkeypatch):
    # M13: cổng NOT — đầu ra tính TỪ công tắc cho sẵn bằng rule — rule_derivable.
    analysis = {"objects": [], "data": [], "relations": [], "processes": [], "constraints": [],
                "goal": "g", "input_description": "i", "output_description": "o", "notes": None,
                "result_ownership": "rule_derivable"}
    bad_spec = {"title": "x", "objects": [{"id": "a", "type": "hologram"}]}  # type lạ → reject
    good_spec = {"title": "OK", "objects": [{"id": "a", "type": "switch", "value": 0}, {"id": "y", "type": "lamp"}],
                 "rules": [{"type": "boolean", "op": "not", "inputs": ["a"], "target": "y"}],
                 "interactions": [{"type": "toggle", "target": "a"}], "processes": []}
    fake, calls = _fake_gemini(
        [
            json.dumps(analysis),
            json.dumps({"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}),
            json.dumps(bad_spec),
            json.dumps(good_spec),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Cổng NOT.", "khoa-gia"))
    assert env["status"] == "ok"
    assert len(calls) == 4  # analyze + classify + 2 lần simulate
    assert "bị từ chối vì" in calls[3]  # prompt retry chứa lỗi validation
