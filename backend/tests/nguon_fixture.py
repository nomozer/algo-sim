# -*- coding: utf-8 -*-
"""W14 5a — lối vào CÓ KHAI cho test cô lập một cổng trên hợp đồng tổng hợp KHÔNG đề.

Chính sách sản phẩm mặc định là `NguonDe.CAN_DE`: hợp đồng không mang đề bị từ chối
`SOURCE_TEXT_MISSING`. Module test nào lấy `check_grounding` / `verify_and_compile` từ
đây là đã KHAI mình thuộc lớp ISOLATED_UNIT_FIXTURE: nó đo một cổng khác, trên hợp đồng
chưa bao giờ có đề; nó KHÔNG đo bằng chứng nguồn đề và cổng giả định. Phân loại và lý
do của từng module: `docs/evaluation/geometry/runs/w14-generic-formation-assumption/
diagnostics/TRUST_POLICY_CALLERS.json`. Không phải file test (không có tiền tố `test_`).
"""
from __future__ import annotations

from app.simulation.semantic_program.grounding_gate import NguonDe
from app.simulation.semantic_program.grounding_gate import check_grounding as _check_grounding
from app.simulation.semantic_program.route import verify_and_compile as _verify_and_compile


def check_grounding(contract, spec):
    return _check_grounding(contract, spec, nguon=NguonDe.FIXTURE_TIN_CAY)


def verify_and_compile(contract, spec, **kw):
    return _verify_and_compile(contract, spec, nguon=NguonDe.FIXTURE_TIN_CAY, **kw)
