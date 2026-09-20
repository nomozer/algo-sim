# -*- coding: utf-8 -*-
"""COMPILER HÌNH HỌC TẤT ĐỊNH — lát cắt dọc đầu tiên.

    RequestContract → GeometryFactGraph → primitive compiler → SemanticProgram
                    → validator/route/scene HIỆN CÓ

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20).

⚠️ **KHÔNG phải mặc định sản phẩm.** Chế độ mặc định vẫn `LLM_ONLY`; nhánh
compiler chỉ chạy khi bật `DETERMINISTIC_FIRST`. Xem `routing.py`.
"""
from .compiler import COMPILER_VERSION, SUPPORTED_FAMILY, bien_dich  # noqa: F401
from .contract_adapter import ADAPTER_VERSION, build_fact_graph  # noqa: F401
from .fact_graph import FACT_GRAPH_VERSION, GeometryFactGraph  # noqa: F401
from .primitives import PRIMITIVE_REGISTRY_VERSION  # noqa: F401
