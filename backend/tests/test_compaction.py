# -*- coding: utf-8 -*-
"""M8-PRE (plan C): NÉN DƯ THỪA AN TOÀN — không nâng hạn mức toàn cục.

Bối cảnh đo được (live): Gemini thỉnh thoảng vừa đặt `label` inline cho node/edge
VỪA tạo thêm object `label` rời lặp lại đúng chuỗi đó (11 label rời cho 5 node +
6 edge) → cảnh vượt `max_objects=20` dù NGỮ NGHĨA chỉ có ~12 object.

Ranh giới (bài test này là nơi thực thi):
- Chỉ gỡ thứ TRÙNG HỆT → chứng minh được là dư thừa.
- KHÔNG gỡ chữ có nghĩa. KHÔNG đoán theo khoảng cách. KHÔNG gỡ để lách hạn mức.
- Cảnh đang TRONG hạn mức: không đụng tới (0 regression).
"""

from app.simulation.dsl.validator import MAX_OBJECTS, validate_generic_config

NODES = [
    {"id": "gv", "type": "node", "node_type": "actor", "label": "Giáo viên", "x": 10, "y": 30},
    {"id": "nhap", "type": "node", "node_type": "process", "label": "Nhập điểm", "x": 30, "y": 30},
    {"id": "kho", "type": "node", "node_type": "data_store", "label": "CSDL điểm", "x": 50, "y": 30},
    {"id": "bc", "type": "node", "node_type": "output", "label": "Bảng điểm", "x": 70, "y": 30},
    {"id": "hs", "type": "node", "node_type": "actor", "label": "Học sinh", "x": 90, "y": 30},
]
EDGES = [
    {"id": f"e{i}", "type": "edge", "from": a, "to": b, "label": lbl}
    for i, (a, b, lbl) in enumerate(
        [
            ("gv", "nhap", "nhập điểm"),
            ("nhap", "kho", "ghi dữ liệu"),
            ("kho", "bc", "kết xuất"),
            ("bc", "hs", "xem điểm"),
            ("hs", "gv", "phản hồi"),
            ("nhap", "bc", "in nhanh"),
        ]
    )
]
# 11 label RỜI lặp lại y hệt nhãn inline của 5 node + 6 edge (đúng dạng LLM sinh ra)
DUP_LABELS = [
    {"id": f"lb_{o['id']}", "type": "label", "label": o["label"], "x": 10, "y": 40}
    for o in (*NODES, *EDGES)
]


def _spec(objects, processes=None):
    return {
        "dsl_version": "1.0",
        "title": "Hệ thống quản lí điểm",
        "objects": objects,
        "rules": [],
        "interactions": [],
        "processes": processes or [],
    }


def test_vuot_han_muc_vi_label_trung_thi_nen_lai_hop_le():
    raw = _spec([*NODES, *EDGES, *DUP_LABELS])
    assert len(raw["objects"]) == 22 > MAX_OBJECTS
    cfg, err = validate_generic_config(raw)
    assert err is None, err
    assert len(cfg["objects"]) == 11  # 5 node + 6 edge, gỡ đúng 11 label dư


def test_nen_KHONG_lam_mat_noi_dung():
    """Chữ vẫn còn — nó nằm inline trên node/edge, renderer vẫn vẽ."""
    cfg, _ = validate_generic_config(_spec([*NODES, *EDGES, *DUP_LABELS]))
    labels = {o.get("label") for o in cfg["objects"]}
    for o in (*NODES, *EDGES):
        assert o["label"] in labels, f"mất nội dung {o['label']!r}"
    assert not [o for o in cfg["objects"] if o["type"] == "label"]


def test_label_CO_NGHIA_thi_KHONG_duoc_go():
    """Label rời mang chữ RIÊNG (không trùng ai) → giữ nguyên; vượt hạn mức thì
    vẫn TỪ CHỐI TRUNG THỰC, không gỡ bừa để lách."""
    unique = [
        {"id": f"note{i}", "type": "label", "label": f"Ghi chú số {i}", "x": 5, "y": 5}
        for i in range(11)
    ]
    cfg, err = validate_generic_config(_spec([*NODES, *EDGES, *unique]))
    assert cfg is None and "1–20" in err


def test_label_trung_nhung_DANG_BI_THAM_CHIEU_thi_khong_go():
    """Bị rule/interaction/parent tham chiếu → gỡ sẽ hỏng tham chiếu → giữ."""
    ref_label = {"id": "lb_gv", "type": "label", "label": "Giáo viên", "x": 5, "y": 5}
    others = [o for o in DUP_LABELS if o["id"] != "lb_gv"]
    raw = _spec([*NODES, *EDGES, ref_label, *others])
    raw["interactions"] = [{"type": "drag", "target": "lb_gv"}]
    cfg, err = validate_generic_config(raw)
    # drag chỉ áp cho node → spec sai; điều cần khẳng định: label KHÔNG bị gỡ âm thầm
    assert cfg is None
    assert "1–20" not in (err or ""), "phải báo lỗi THẬT, không phải lỗi hạn mức"


def test_canh_TRONG_han_muc_khong_bi_dung_toi():
    """0 bề mặt regression: label trùng nhưng cảnh chưa vượt hạn mức → giữ nguyên."""
    raw = _spec([*NODES[:2], {"id": "lb_gv", "type": "label", "label": "Giáo viên", "x": 5, "y": 5}])
    cfg, err = validate_generic_config(raw)
    assert err is None
    assert [o["id"] for o in cfg["objects"]] == ["gv", "nhap", "lb_gv"]


def test_nen_rut_id_khoi_reveal_step_va_bo_step_rong():
    """Label bị gỡ phải biến khỏi reveal step (không để tham chiếu treo);
    step rỗng thì bỏ hẳn."""
    raw = _spec(
        [*NODES, *EDGES, *DUP_LABELS],
        processes=[
            {
                "type": "reveal_sequence",
                "steps": [
                    {"objects": ["gv", "lb_gv"]},
                    {"objects": [o["id"] for o in DUP_LABELS[1:]]},  # TOÀN label dư → rỗng
                    {"objects": ["nhap", "kho", "bc", "hs", *[e["id"] for e in EDGES]]},
                ],
            }
        ],
    )
    cfg, err = validate_generic_config(raw)
    assert err is None, err
    steps = cfg["processes"][0]["steps"]
    assert len(steps) == 2  # step toàn label dư đã bị bỏ
    assert steps[0]["objects"] == ["gv"]
    ids = {o["id"] for o in cfg["objects"]}
    for st in steps:
        for i in st["objects"]:
            assert i in ids, "reveal step tham chiếu id đã bị gỡ"


def test_canh_generic_khong_phai_he_thong_khong_regression():
    """Cảnh hình học/logic (không label trùng) — hành vi y như cũ."""
    tri = _spec(
        [
            {"id": "A", "type": "node", "x": 20, "y": 70},
            {"id": "B", "type": "node", "x": 80, "y": 70},
            {"id": "AB", "type": "edge", "from": "A", "to": "B"},
            {"id": "note", "type": "label", "label": "Cạnh đáy", "x": 50, "y": 80},
        ]
    )
    cfg, err = validate_generic_config(tri)
    assert err is None
    assert len(cfg["objects"]) == 4  # label có nghĩa vẫn còn
