# -*- coding: utf-8 -*-
"""KIẾN TRÚC TEXT → GEOMETRY FUNCTIONS — tầng mô phỏng (run `text-to-geometry-functions`, nhánh nghiên cứu).

    lời gọi hàm có kiểu + nguồn → cổng nguồn → engine tất định (bố cục, phụ thuộc, kiểm) → IR → interpreter

AI chỉ CHỌN hàm trong `REGISTRY`; engine chọn bố cục, dựng, kiểm và thực thi qua IR/kernel sẵn có. Bày Scene3D nằm ở
tầng trên: `app/ai/function_route.py::run_function_route` (điểm vào). Không phải mặc định sản phẩm: `LLM_ONLY` vẫn là
đường của `run_pipeline`.
"""
from .engine import ENGINE_VERSION, KetQuaTuyen, dung_tu_loi_goi  # noqa: F401
from .registry import REGISTRY, REGISTRY_VERSION, TuChoi, function_declarations  # noqa: F401
