# -*- coding: utf-8 -*-
"""PHASE 7A.1 — SỬA SAI LỆCH ĐO LƯỜNG. **0 API call.**

Hai lỗi lộ ra ở pilot Phase 7A. Cả hai bóp méo số **theo hướng THẤP HƠN thực
tế**, và cả hai **đổ cho mô hình** cái lỗi thuộc về hệ. Với một đề tài mà luận
điểm là *"AI sinh được chương trình đáng tin cậy hay không"*, đó là loại sai
lệch tệ nhất — nó kết tội đúng chỗ mô hình làm đúng.

    ① learner_surface   hợp đồng đòi `Q`, chương trình dựng `Q_point`
                        oracle = True, servable = FALSE
    ② known_gap_roles   gap của DSL 2D chặn đường sinh HÌNH HỌC
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[3]
PILOT = GOC / "docs" / "evaluation" / "geometry" / "phase7a-pilot"


# ══ ① learner_surface — CỔNG THỨ TƯ CỦA CÙNG MỘT LỚP LỖI ════════════════
def test_luot_pilot_tung_TRUOT_OAN_nay_PHAI_QUA():
    """Hiện trường thật: `3-pmn-giao-tuyen-lan1`.

    `executable = True`, oracle độc lập xác nhận `Q_point` LÀ trung điểm `AD`,
    mà `servable = False` vì `check_learner_surface` tra witness `Q` (tên HỢP
    ĐỒNG) trong một tập toàn tên CHƯƠNG TRÌNH. Chương trình đúng, học sinh không
    nhận được gì.
    """
    d = json.loads((PILOT / "3-pmn-giao-tuyen-lan1.json").read_text(
        encoding="utf-8"))
    kq = verify_and_compile(
        RequestContract.model_validate(d["request_contract"]),
        SemanticProgramSpec.model_validate(d["generated_program"]))
    assert kq.executable and kq.servable, f"{kq.stage_reached}: {kq.details}"
    # Đáp án vẫn đúng — qua cổng mà sai số thì bản vá chỉ mở đường cho lỗi khác.
    q = (kq.final_memory or {}).get("Q_point")
    assert q is not None and (str(q.x), str(q.y), str(q.z)) == ("0", "2", "0")


def test_learner_surface_NHAN_anh_xa_nhu_ba_cong_kia():
    """C₁a, C₁b, C₂ đã nhận từ Phase 6.7.1. Cổng thứ tư đứng ngoài suốt hai pha."""
    import inspect

    from app.simulation.semantic_program import route
    from app.simulation.semantic_program.learner_surface import (
        check_learner_surface,
    )

    assert "ten_da_hoa_giai" in inspect.signature(
        check_learner_surface).parameters
    # Soi cả MODULE, không soi riêng `verify_and_compile`: nó là hàm bao mỏng,
    # ba lời gọi thật nằm ở `_sau_grounding`. Soi nhầm chỗ thì test đỏ oan.
    src = inspect.getsource(route)
    assert src.count("ten_da_hoa_giai=c1a.ten_da_hoa_giai") >= 3, (
        "cả C₁b, C₂ và learner_surface phải dùng CHUNG một ánh xạ")


def test_witness_KHONG_hien_that_van_bi_chan():
    """Vế còn lại: bản vá KHÔNG được biến cổng thành cái bù nhìn.

    Chương trình dựng đủ hình nhưng witness là một biến `bool` vô hướng không
    lên được cảnh — cổng vẫn phải từ chối.
    """
    spec = SemanticProgramSpec.model_validate({
        "title": "witness khong len duoc canh",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v,
             "model_assumption": "chọn hệ trục"}
            for n, v in [("A", [0, 0, 0]), ("B", [1, 0, 0]), ("C", [0, 1, 0])]
        ] + [{"name": "mp", "type": "plane3"},
             {"name": "co_thuoc", "type": "bool"}],
        "statements": [
            {"kind": "construct_plane", "target_var": "mp",
             "through": ["A", "B", "C"]},
            {"kind": "assign", "target_var": "co_thuoc",
             "expr": {"kind": "literal", "value": True}},
        ],
    })
    from app.simulation.semantic_program.obligations import Obligation

    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="mp",
                   params={"witness": "co_thuoc"}),))
    assert not verify_and_compile(hd, spec).servable


# ══ ② ĐÃ XOÁ: known_gap_roles / execution_authority ═══════════════════════
#
# Sáu test ở đây khẳng định *"gap của DSL 2D không được chặn hình học"* —
# tức chúng canh một CỔNG TIN HỌC (`check_execution_authority`) mà đường hình
# học buộc phải đi qua. Sau `LEGACY_INFORMATICS_REMOVAL`, cổng ấy không còn
# tồn tại và đường hình học không đi qua cổng nào của miền khác.
#
# Mối lo thì không mất — nó chỉ được giải quyết ở tầng CẤU TRÚC thay vì bằng
# một danh sách miễn trừ, và `tests/geometry/test_geometry_route_independence.py`
# khoá đúng điều đó: không lời gọi thẩm quyền Tin học nào trên đường hình học.
