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
    if r.length_unit:
        # Toạ độ khung đo theo đơn vị a (a = 1 là TỈ LỆ hiển thị, không phải dữ kiện đề); đáp số mang a^bậc.
        r.scene3d["length_unit"] = {"symbol": r.length_unit, "display_scale": f"{r.length_unit} = 1 đơn vị dựng",
                                    "is_given": False}
    return r


def run_fact_route(problem_text: str, facts: Any) -> KetQuaTuyen:
    """NHÁNH B (thực nghiệm, run `hybrid-compiler-selection`): dữ kiện có kiểu → planner → `run_function_route` (ĐÚNG đường
    của nhánh A từ lược đồ trở đi). Sau khi dựng: điều phải chứng minh phải ĐÚNG trên hình (sai ⇒ PROOF_GOAL_FALSE), mệnh đề
    phủ định phải SAI (đúng ⇒ INCONSISTENT_FACTS). Hình không duy nhất ⇒ từ chối, KHÔNG lấy một hình mẫu."""
    from app.simulation.geometry_functions import TuChoi
    from app.simulation.geometry_functions.planner import PLANNER_VERSION, lap_ke_hoach

    try:
        k = lap_ke_hoach(facts)
    except TuChoi as e:
        return KetQuaTuyen("REFUSED", e.code, e.reason, e.calls, details=e.data, planner={"version": PLANNER_VERSION})
    r = run_function_route(problem_text, {"calls": k.calls})
    r.planner = {"version": PLANNER_VERSION, "calls": k.calls, "trace": k.trace, "goal_checks": {}, "negated_checks": {}}
    if r.status != "SERVED":
        if r.code == "UNDERDETERMINED_POINT" and (khong := _hinh_khong_duy_nhat(k, r.details.get("points") or [])):
            return KetQuaTuyen("REFUSED", "FIGURE_NOT_UNIQUE", khong, r.failed_calls, trace=r.trace,
                               details={**r.details, "quantity_invariant": "volume = ⅓·S_đáy·h"}, planner=r.planner)
        return r
    ten = {True: "HOLDS", False: "FAILS", None: "UNVERIFIABLE"}
    for g in k.goals:
        r.planner["goal_checks"][g["fact"]] = ten[r.checker(g["call"])]
    for n in k.negated:
        r.planner["negated_checks"][n["fact"]] = ten[r.checker(n["call"])]
    if sai := [f for f, v in r.planner["goal_checks"].items() if v == "FAILS"]:
        return KetQuaTuyen("REFUSED", "PROOF_GOAL_FALSE", f"điều phải chứng minh {sai} SAI trên hình dựng từ giả thiết",
                           tuple(sai), trace=r.trace, planner=r.planner)
    if dung := [f for f, v in r.planner["negated_checks"].items() if v == "HOLDS"]:
        return KetQuaTuyen("REFUSED", "INCONSISTENT_FACTS",
                           f"mệnh đề phủ định {dung} lại ĐÚNG trên hình dựng từ các giả thiết khác — đề mâu thuẫn",
                           tuple(dung), trace=r.trace, planner=r.planner)
    # Phủ định là giả thiết: không kiểm được nó SAI ⇒ hình có thể trái đề ⇒ không phục vụ (mã như nhánh A).
    if mo := [f for f, v in r.planner["negated_checks"].items() if v == "UNVERIFIABLE"]:
        return KetQuaTuyen("REFUSED", "NEGATED_CLAUSE",
                           f"mệnh đề phủ định {mo} không kiểm được trên hình — không phục vụ một hình có thể trái đề",
                           tuple(mo), trace=r.trace, planner=r.planner)
    return r


def _hinh_khong_duy_nhat(k: Any, thieu: list[str]) -> str | None:
    """Chẩn đoán — KHÔNG phục vụ: điểm duy nhất chưa xác định là đỉnh của một khối chóp có dữ kiện chiều cao, và mọi câu hỏi là
    thể tích khối ấy ⇒ đại lượng bất biến (V = ⅓·S·h) nhưng hình không duy nhất. Trường hợp khác: giữ UNDERDETERMINED_POINT."""
    hoi = [c for c in k.calls if c["fn"].startswith("ask_")]
    for kh in k.solids.values():
        if (kh.loai == "pyramid" and thieu == [kh.dinh] and kh.ten in k.heights and hoi
                and all(c["fn"] == "ask_volume" and c["args"]["solid"] == kh.ten for c in hoi)):
            return (f"vị trí đỉnh {kh.dinh} không xác định (chân đường cao chưa biết) — thể tích là bất biến ⅓·S_đáy·h nên "
                    "duy nhất, nhưng không có MỘT hình để hiển thị mà không thêm giả thiết; không lấy hình mẫu")
    return None
