# -*- coding: utf-8 -*-
"""M17 W1 — lock network.graph_traversal: validator BE fail-closed + catalog.

Executor/oracle sống ở FE (traverse.test.tsx — oracle BFS/DFS độc lập, đường
đi ngắn nhất, unreachable hợp lệ); BE lock validator mirror. Pipeline
end-to-end do audit matrix chạy (test_authenticity_audit).
"""

from __future__ import annotations

import pytest

from app.simulation.catalog import CATALOG
from app.validation.simulation import validate_traverse_config


def _cfg(nodes=None, edges=None, start="A", variant="bfs", **extra):
    return {
        "nodes": nodes if nodes is not None else [{"id": "A"}, {"id": "B"}],
        "edges": edges if edges is not None else [["A", "B"]],
        "start": start,
        "variant": variant,
        **extra,
    }


def test_hop_le_chuan():
    cfg, err = validate_traverse_config(_cfg(goal="B"))
    assert err is None
    assert cfg["variant"] == "bfs"
    assert cfg["goal"] == "B"
    assert cfg["directed"] is False


def test_canh_tham_chieu_nut_khong_ton_tai_reject():
    cfg, err = validate_traverse_config(_cfg(edges=[["A", "Z"]]))
    assert cfg is None and "không tồn tại" in err


def test_self_loop_reject():
    cfg, err = validate_traverse_config(_cfg(edges=[["A", "A"]]))
    assert cfg is None and "tự nối" in err


def test_start_goal_phai_la_nut_that():
    cfg, err = validate_traverse_config(_cfg(start="Z"))
    assert cfg is None and "start" in err
    cfg, err = validate_traverse_config(_cfg(goal="Z"))
    assert cfg is None and "goal" in err


def test_goal_khac_start():
    cfg, err = validate_traverse_config(_cfg(goal="A"))
    assert cfg is None and "khác" in err


def test_variant_ngoai_enum_reject():
    cfg, err = validate_traverse_config(_cfg(variant="dijkstra"))
    assert cfg is None and "bfs" in err


def test_id_trung_reject():
    cfg, err = validate_traverse_config(_cfg(nodes=[{"id": "A"}, {"id": "A"}]))
    assert cfg is None and "trùng" in err


@pytest.mark.parametrize("n", [1, 11])
def test_bound_node_reject(n):
    cfg, err = validate_traverse_config(
        _cfg(nodes=[{"id": f"n{k}"} for k in range(n)], edges=[], start="n0")
    )
    assert cfg is None and "2–10" in err


def test_bound_edge_reject():
    nodes = [{"id": f"n{k}"} for k in range(3)]
    edges = [["n0", "n1"]] * 21
    cfg, err = validate_traverse_config(_cfg(nodes=nodes, edges=edges, start="n0"))
    assert cfg is None and "20 cạnh" in err


def test_goal_bo_trong_hop_le():
    cfg, err = validate_traverse_config(_cfg())  # không goal
    assert err is None and cfg["goal"] is None


def test_directed_flag():
    cfg, err = validate_traverse_config(_cfg(directed=True))
    assert err is None and cfg["directed"] is True


def test_forbidden_keys_reject():
    raw = _cfg()
    raw["steps"] = [1]
    cfg, err = validate_traverse_config(raw)
    assert cfg is None and "bị cấm" in err


def test_catalog_entry_descriptor_day_du():
    spec = CATALOG["network.graph_traversal"]
    assert spec.domain == "network"
    assert spec.config_contract_version == "traverse-1.0"
    owned = {m for mb in spec.family_memberships for m in mb.owned_mechanisms}
    assert owned == {"graph_traversal.breadth_first", "graph_traversal.depth_first"}
    # packet_routing GIỮ NGUYÊN cơ chế cũ (application variant, không đổi)
    routing = {m for mb in CATALOG["network.packet_routing"].family_memberships for m in mb.owned_mechanisms}
    assert routing == {"graph_traversal.unweighted_hop_bfs"}
