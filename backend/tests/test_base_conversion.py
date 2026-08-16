# -*- coding: utf-8 -*-
"""M17 W1 — lock binary.base_conversion: validator fail-closed + catalog entry.

Executor/oracle sống ở FE (convert.test.tsx — oracle parseInt/toString 12 cặp
cơ số); BE lock: validator hai-tầng phía server + descriptor đầy đủ. Pipeline
end-to-end (route hex → base_conversion → envelope ok) do audit matrix chạy
(test_authenticity_audit — 4 archetype qua production run_pipeline).
"""

from __future__ import annotations

import pytest

from app.simulation.catalog import CATALOG
from app.simulation.descriptor import ReachabilityLevel
from app.validation.simulation import (
    CONV_BASES,
    CONV_MAX_VALUE,
    validate_base_conversion_config,
)


def _v(source=10, target=16, value="2026", **extra):
    return validate_base_conversion_config(
        {"sourceBase": source, "targetBase": target, "inputValue": value, **extra}
    )


def test_hop_le_chuan_hoa_canonical():
    cfg, err = _v(16, 10, "009c")
    assert err is None
    assert cfg["inputValue"] == "9C"  # HOA + bỏ 0 thừa đầu
    assert cfg["strategy"] == "positional_weights"


@pytest.mark.parametrize("source,target", [(5, 10), (10, 3), (0, 10), (10, 100)])
def test_co_so_ngoai_pham_vi_reject(source, target):
    cfg, err = _v(source, target, "44")
    assert cfg is None and "{2, 8, 10, 16}" in err


def test_cung_co_so_reject():
    cfg, err = _v(10, 10, "44")
    assert cfg is None and "KHÁC" in err


@pytest.mark.parametrize("source,value", [(8, "79"), (2, "102"), (16, "9G"), (10, "12A")])
def test_chu_so_sai_co_so_reject(source, value):
    cfg, err = _v(source, 10 if source != 10 else 16, value)
    assert cfg is None and "không hợp lệ" in err


def test_vuot_gioi_han_reject():
    cfg, err = _v(10, 16, str(CONV_MAX_VALUE + 1))
    assert cfg is None and str(CONV_MAX_VALUE) in err
    cfg, _err = _v(10, 16, str(CONV_MAX_VALUE))
    assert cfg is not None  # đúng biên vẫn hợp lệ


def test_strategy_khai_sai_reject_va_dan_xuat():
    cfg, err = _v(10, 16, "44", strategy="two_stage")
    assert cfg is None and "quotient_remainder" in err
    cfg, _ = _v(8, 16, "755")
    assert cfg["strategy"] == "two_stage"


def test_forbidden_keys_reject():
    cfg, err = _v(10, 16, "44", steps=[1, 2])
    assert cfg is None and "bị cấm" in err


def test_gia_tri_0_hop_le():
    cfg, err = _v(2, 16, "000")
    assert err is None and cfg["inputValue"] == "0"


def test_catalog_entry_descriptor_day_du():
    spec = CATALOG["binary.base_conversion"]
    assert spec.domain == "binary"
    assert spec.config_contract_version == "baseconv-1.0"
    owned = {m for mb in spec.family_memberships for m in mb.owned_mechanisms}
    assert "positional_representation.non_binary_base" in owned  # gap flip W1
    assert "positional_representation.binary_positional_weights" in owned
    # W4B-3D — nay CÓ mẫu offline công khai nên `library_discoverable` là khai
    # ĐÚNG SỰ THẬT. Chốt cũ ("chưa có mẫu") mô tả một trạng thái không còn tồn
    # tại; giữ nó lại sẽ khoá kho mã vào một giới hạn đã được gỡ.
    assert ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
    # W5P — `binary.base_conversion` thuộc TẦNG HAI (ngoài ba điểm nghẽn), nên
    # nó thôi được quảng bá ở Thư viện. Vẫn AI tới được: học sinh gõ đề đổi cơ
    # số thì hệ vẫn phải dựng được, từ chối lúc ấy mới là sai.
    assert ReachabilityLevel.LIBRARY_DISCOVERABLE not in spec.reachability
    assert ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
    assert CONV_BASES == (2, 8, 10, 16)
