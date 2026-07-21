# -*- coding: utf-8 -*-
"""M17 W2A — lock tree.traversal: validator BE (structural + semantic) + catalog.

Executor/oracle sống ở FE (tree.test.tsx — oracle đệ quy độc lập 4 variant);
BE lock validator mirror + descriptor. Routing/regression end-to-end do audit
matrix (test_authenticity_audit::test_tree_regression_dong_route_specialized).
"""

from __future__ import annotations

import pytest

from app.simulation.catalog import CATALOG
from app.simulation.descriptor import FamilyId
from app.simulation.mechanisms import FAMILY_MECHANISMS, INTENTIONAL_GAP_MECHANISMS
from app.validation.simulation import validate_tree_traversal_config

_ABC = [
    {"id": "A", "left": "B", "right": "C"},
    {"id": "B", "left": "D", "right": "E"},
    {"id": "C", "left": "F", "right": "G"},
    {"id": "D"}, {"id": "E"}, {"id": "F"}, {"id": "G"},
]


def _cfg(nodes=None, root="A", variant="preorder", **extra):
    return {
        "specVersion": "tree-1.0",
        "variant": variant,
        "rootId": root,
        "nodes": nodes if nodes is not None else _ABC,
        **extra,
    }


def test_hop_le_chuan():
    cfg, err = validate_tree_traversal_config(_cfg())
    assert err is None
    assert cfg["variant"] == "preorder" and cfg["rootId"] == "A"
    assert len(cfg["nodes"]) == 7


@pytest.mark.parametrize("variant", ["preorder", "inorder", "postorder", "level_order"])
def test_bon_variant_hop_le(variant):
    cfg, err = validate_tree_traversal_config(_cfg(variant=variant))
    assert err is None and cfg["variant"] == variant


def test_spec_version_variant_sai_reject():
    cfg, err = validate_tree_traversal_config(_cfg(specVersion="x"))
    assert cfg is None and "specVersion" in err
    cfg, err = validate_tree_traversal_config(_cfg(variant="bfs"))
    assert cfg is None and "variant" in err


def test_child_ref_khong_ton_tai_va_self_loop():
    cfg, err = validate_tree_traversal_config(_cfg(nodes=[{"id": "A", "left": "Z"}]))
    assert cfg is None and "không tồn tại" in err
    cfg, err = validate_tree_traversal_config(_cfg(nodes=[{"id": "A", "left": "A"}]))
    assert cfg is None and "tự trỏ" in err


def test_multi_parent_reject():
    cfg, err = validate_tree_traversal_config(_cfg(nodes=[
        {"id": "A", "left": "B", "right": "C"},
        {"id": "B", "left": "D"}, {"id": "C", "left": "D"}, {"id": "D"},
    ]))
    assert cfg is None and "NHIỀU cha" in err


def test_root_co_cha_reject():
    cfg, err = validate_tree_traversal_config(_cfg(nodes=[
        {"id": "A", "left": "B"}, {"id": "B", "left": "A"},
    ]))
    assert cfg is None  # A vừa là root vừa là con của B


def test_disconnected_reject():
    cfg, err = validate_tree_traversal_config(_cfg(nodes=[
        {"id": "A", "left": "B"}, {"id": "B"}, {"id": "orphan"},
    ]))
    assert cfg is None and "rời rạc" in err


def test_root_khong_ton_tai_va_node_count():
    cfg, err = validate_tree_traversal_config(_cfg(root="Z"))
    assert cfg is None and "rootId" in err
    cfg, err = validate_tree_traversal_config(_cfg(nodes=[]))
    assert cfg is None and "1–15" in err


def test_depth_qua_bound_reject():
    chain = [{"id": f"n{i}", "left": f"n{i+1}"} for i in range(6)] + [{"id": "n6"}]
    cfg, err = validate_tree_traversal_config(_cfg(nodes=chain, root="n0"))
    assert cfg is None and "5 tầng" in err


def test_id_trung_va_forbidden_keys():
    cfg, err = validate_tree_traversal_config(_cfg(nodes=[{"id": "A"}, {"id": "A"}]))
    assert cfg is None and "trùng" in err
    raw = _cfg()
    raw["steps"] = [1]
    cfg, err = validate_tree_traversal_config(raw)
    assert cfg is None and "bị cấm" in err


def test_catalog_entry_descriptor_day_du():
    spec = CATALOG["tree.traversal"]
    assert spec.domain == "tree"
    assert spec.config_contract_version == "tree-1.0"
    owned = {m for mb in spec.family_memberships for m in mb.owned_mechanisms}
    assert owned == {
        "tree_traversal.preorder", "tree_traversal.inorder",
        "tree_traversal.postorder", "tree_traversal.level_order",
    }
    # mechanism prefix = family_id (canonical convention — không dùng binary_tree.*)
    assert set(FAMILY_MECHANISMS[FamilyId.TREE_TRAVERSAL]) == owned
    # tree không có intentional gap mechanism (mọi cơ chế cây đều owned)
    assert not (owned & INTENTIONAL_GAP_MECHANISMS)
