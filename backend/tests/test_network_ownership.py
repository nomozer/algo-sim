# -*- coding: utf-8 -*-
"""M15 Task 14 (W4) — network ownership: routing owned unweighted_hop_bfs +
known_gaps Dijkstra máy-đọc; encap owned encap_decap_4layer, known_gaps giữ nguyên.

K1 (test_formalized_families_owned_khong_rong trong test_capability_descriptors.py)
buộc mọi family đã formalize phải có owned_mechanisms ≠ () trên MỌI membership —
mở rộng FORMALIZED_FAMILIES sang GRAPH_TRAVERSAL + LAYERED_PDU_TRANSFORM (mechanisms.py)
là RED-trigger cho routing/encap cho tới khi khai owned ở đây.
"""
from __future__ import annotations


def test_routing_owned_bfs_va_khai_gap_dijkstra():
    from app.simulation.catalog import CATALOG

    spec = CATALOG["network.packet_routing"]
    mems = [m for m in spec.family_memberships if m.family_id.value == "graph_traversal"]
    assert mems, "network.packet_routing phải có membership graph_traversal"
    assert mems[0].owned_mechanisms == ("graph_traversal.unweighted_hop_bfs",)
    assert any("Dijkstra" in g for g in spec.known_gaps)


def test_encap_owned_va_known_gaps_giu_nguyen():
    from app.simulation.catalog import CATALOG

    spec = CATALOG["network.protocol_encapsulation"]
    mems = [m for m in spec.family_memberships if m.family_id.value == "layered_pdu_transform"]
    assert mems, "network.protocol_encapsulation phải có membership layered_pdu_transform"
    assert mems[0].owned_mechanisms == ("layered_pdu_transform.encapsulate_decapsulate_4layer",)
    # M10 giữ nguyên — encap known_gaps KHÔNG bị Task 14 sửa
    assert "phân mảnh" in spec.known_gaps
    assert spec.known_gaps == (
        "bắt tay TCP ba bước", "phân mảnh", "retransmission", "congestion", "DNS",
    )


def test_dijkstra_gap_lock_van_nguyen():
    """Pin case cap-dijkstra-gap trong datasets/capability.py: group == "unsupported".

    Chống sửa nhầm — Dijkstra vẫn CAPABILITY_GAP, khóa 12: Task 14 CHỈ khai
    known_gaps máy-đọc trên network.packet_routing, KHÔNG cấp quyền sở hữu
    Dijkstra (weighted shortest-path) cho bất kỳ engine nào. Chỉ đọc — không sửa dataset.
    """
    from app.evaluation.datasets.capability import CAPABILITY_ITEMS

    items = [it for it in CAPABILITY_ITEMS if it.id == "cap-dijkstra-gap"]
    assert len(items) == 1, "case cap-dijkstra-gap phải tồn tại đúng 1 lần trong pool capability"
    assert items[0].group == "unsupported"
