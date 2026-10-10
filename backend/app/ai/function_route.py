# -*- coding: utf-8 -*-
"""ĐIỂM VÀO đường text → geometry functions (run `text-to-geometry-functions`, nhánh nghiên cứu).

    run_function_route(đề, {"calls": [...]}) → geometry_functions.dung_tu_loi_goi (dựng · kiểm · thực thi)
                                             → build_simulation_state → build_scene3d + chart_metric

Nằm ở `app/ai` vì đây là tầng điều phối được phép bày cảnh (cùng chỗ với `pipeline._dung_scene3d`; `app/simulation`
không nhập `scene3d`) và là nơi bước kế sẽ gắn bộ sinh lời gọi hàm (Gemini function calling). Hôm nay đầu vào là lời
gọi đã có sẵn: module này KHÔNG gọi provider, KHÔNG nhập `pipeline`/`gemini`, KHÔNG lùi về `LLM_ONLY` — không dựng
được ⇒ `REFUSED` có mã. `run_pipeline` / `/api/analyze` không tham chiếu module này: mặc định sản phẩm không đổi.
"""
from __future__ import annotations

from typing import Any

from app.simulation.geometry import metric as _metric
from app.simulation.geometry_functions import KetQuaTuyen, dung_tu_loi_goi
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


def run_function_route(problem_text: str, plan: Any) -> KetQuaTuyen:
    r = dung_tu_loi_goi(problem_text, plan)
    if r.status != "SERVED":
        return r
    try:
        with _metric.using(r.chart_metric):
            canh = build_scene3d(build_simulation_state(r.spec, r.exec_result))
    except Exception as e:  # noqa: BLE001 — cảnh hỏng ⇒ từ chối có mã, không phục vụ nửa vời
        return KetQuaTuyen("REFUSED", "SCENE_BUILD_FAILED", f"{type(e).__name__}: {e}", trace=r.trace)
    if not canh.get("objects"):
        return KetQuaTuyen("REFUSED", "SCENE_BUILD_FAILED", "cảnh rỗng", trace=r.trace)
    r.scene3d = {**canh, "chart_metric": r.metric}
    return r
