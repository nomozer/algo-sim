# -*- coding: utf-8 -*-
"""CHÍNH SÁCH ĐỊNH TUYẾN — compiler là OPT-IN, mặc định KHÔNG đổi một byte.

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20).

─── VÌ SAO MẶC ĐỊNH PHẢI TRÙNG START_HEAD ──────────────────────────────────

Lát cắt này chưa được đo trên lượt provider thật nào. Bật nó làm mặc định là
đổi đường sản phẩm dựa trên một fixture — đúng thứ kho đã trả giá nhiều lần.
Nên `che_do()` trả `LLM_ONLY` khi biến môi trường vắng mặt hoặc không hợp lệ, và
ở chế độ ấy **không một dòng nào của compiler được chạm tới**.

─── BỐN KẾT CỤC, VÀ VÌ SAO CHÚNG KHÁC NHAU ─────────────────────────────────

    USE_COMPILER      SUPPORTED ⇒ dùng chương trình đã biên dịch, KHÔNG gọi
                      transport synthesis
    FALLBACK_TO_LLM   UNSUPPORTED ⇒ compiler KHÔNG tự gọi provider; nó trả
                      quyết định để CALLER quyết. Ranh giới ấy là điều kiện để
                      đếm được "bao nhiêu lượt gọi đã tránh được"
    REFUSE            INVALID ⇒ dữ kiện mâu thuẫn hoặc phi lý. Fallback ở đây là
                      lấy LLM che một mâu thuẫn của đề — fail-closed thay vì che
    DISABLED          chế độ tắt ⇒ hành vi trùng START_HEAD
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

CHE_DO_MAC_DINH = "LLM_ONLY"
CHE_DO_COMPILER = "DETERMINISTIC_FIRST"
CHE_DO_HOP_LE: tuple[str, ...] = (CHE_DO_MAC_DINH, CHE_DO_COMPILER)

BIEN_MOI_TRUONG = "GEOMETRY_COMPILER_MODE"

QUYET_DINH: tuple[str, ...] = (
    "DISABLED", "USE_COMPILER", "FALLBACK_TO_LLM", "REFUSE",
)


def che_do(env: dict[str, str] | None = None) -> str:
    """Chế độ hiện hành. Thiếu biến, hoặc giá trị lạ ⇒ MẶC ĐỊNH, không đoán."""
    v = (env if env is not None else os.environ).get(BIEN_MOI_TRUONG, "")
    return v if v in CHE_DO_HOP_LE else CHE_DO_MAC_DINH


@dataclass(frozen=True)
class QuyetDinhDinhTuyen:
    decision: str
    program: dict[str, Any] | None = None
    reason_code: str | None = None
    compile_result: Any = None
    adapter_status: str | None = None
    diagnostics: tuple[str, ...] = field(default_factory=tuple)


def quyet_dinh_dinh_tuyen(contract: Any, env: dict[str, str] | None = None
                          ) -> QuyetDinhDinhTuyen:
    """Có dùng compiler cho hợp đồng này không. KHÔNG gọi provider, KHÔNG mạng."""
    if che_do(env) != CHE_DO_COMPILER:
        return QuyetDinhDinhTuyen("DISABLED")

    from .compiler import bien_dich
    from .contract_adapter import build_fact_graph

    kq = build_fact_graph(contract)
    if kq.status == "INVALID_CONFLICT":
        # Dữ kiện tự mâu thuẫn. Gọi LLM ở đây là mời nó chọn một nửa mâu thuẫn
        # rồi trình bày như thể đề nhất quán.
        return QuyetDinhDinhTuyen("REFUSE", None, kq.reason_code,
                                  adapter_status=kq.status,
                                  diagnostics=kq.diagnostics)
    if kq.status != "VALID" or kq.graph is None:
        return QuyetDinhDinhTuyen("FALLBACK_TO_LLM", None, kq.reason_code,
                                  adapter_status=kq.status,
                                  diagnostics=kq.diagnostics)

    bd = bien_dich(kq.graph)
    if bd.status == "COMPILED" and bd.program is not None:
        return QuyetDinhDinhTuyen("USE_COMPILER", bd.program, None, bd,
                                  kq.status, bd.diagnostics)
    if (bd.reason_code or "").startswith("NON_POSITIVE") or \
            bd.reason_code == "INVALID_CONFLICT":
        return QuyetDinhDinhTuyen("REFUSE", None, bd.reason_code, bd,
                                  kq.status, bd.diagnostics)
    return QuyetDinhDinhTuyen("FALLBACK_TO_LLM", None, bd.reason_code, bd,
                              kq.status, bd.diagnostics)
