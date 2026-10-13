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

from fractions import Fraction
from typing import Any

from app.simulation.geometry import metric as _metric
from app.simulation.geometry_functions import KetQuaTuyen, dung_tu_loi_goi
from app.simulation.semantic_program.quantity_annotations import _nhan_chung
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


def _gan_nhan_chung_hinh_chieu(canh: dict[str, Any], spec: Any, mem: dict[str, Any]) -> None:
    """Điểm dựng bằng `project_onto` mang đoạn vuông góc PHỤ (điểm → chân) + hai phương ký hiệu vuông góc tại chân, cùng
    helper với nhân chứng khoảng cách. Chân phải trùng toạ độ điểm đã dựng; lệch ⇒ ném (cảnh bị từ chối)."""
    theo_id = {o["id"]: o for o in canh["objects"]}
    for s in spec.statements:
        e = getattr(s, "expr", None)
        if getattr(s, "kind", None) != "construct_point" or getattr(e, "kind", None) != "project_onto":
            continue
        w = _nhan_chung(e.point, e.target, mem)
        o = theo_id.get(s.target_var)
        if w is None or o is None:
            continue
        if list(map(Fraction, w["foot"])) != list(map(Fraction, o["xyz"])):
            raise ValueError(f"chân vuông góc của {s.target_var} lệch toạ độ đã dựng")
        o["perpendicular_witness"] = w


def run_function_route(problem_text: str, plan: Any, auxiliary: tuple[dict, ...] = (),
                       read_quotes: tuple[str, ...] = ()) -> KetQuaTuyen:
    """`auxiliary` chỉ do `run_fact_route` truyền (điểm phụ của planner); nhánh A không có đường nào đặt nó.
    `read_quotes` cũng vậy: quote của goal / mệnh đề phủ định mà planner giữ và route kiểm trên hình — đã đọc, không là
    giả thiết (cổng phủ tiền đề tính chúng là đã đọc)."""
    r = dung_tu_loi_goi(problem_text, plan, auxiliary, read_quotes)
    if r.status != "SERVED":
        return r
    try:
        with _metric.using(r.chart_metric):
            canh = build_scene3d(build_simulation_state(r.spec, r.exec_result, r.declared_topology))
            _gan_nhan_chung_hinh_chieu(canh, r.spec, r.exec_result.final_memory)
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
    của nhánh A từ lược đồ trở đi). Checker chỉ quan sát một cấu hình dựng từ giả thiết, không là bộ chứng minh tổng quát:
    mọi goal/negated được ghi tách biệt với proof status. Hình không duy nhất ⇒ từ chối, KHÔNG lấy một hình mẫu."""
    from app.simulation.geometry_functions import TuChoi
    from app.simulation.geometry_functions.planner import PLANNER_VERSION, lap_ke_hoach

    try:
        k = lap_ke_hoach(facts, problem_text)
    except TuChoi as e:
        return KetQuaTuyen("REFUSED", e.code, e.reason, e.calls, details=e.data, planner={"version": PLANNER_VERSION})
    doc = tuple(q for g in (*k.goals, *k.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
    r = run_function_route(problem_text, {"calls": k.calls}, tuple(k.auxiliary), doc)
    r.planner = {"version": PLANNER_VERSION, "calls": k.calls, "trace": k.trace, "auxiliary": k.auxiliary,
                 "goal_checks": {}, "negated_checks": {}}
    if r.status != "SERVED":
        if r.code == "UNDERDETERMINED_POINT" and (khong := _hinh_khong_duy_nhat(k, r.details.get("points") or [])):
            return KetQuaTuyen("REFUSED", "FIGURE_NOT_UNIQUE", khong, r.failed_calls, trace=r.trace,
                               details={**r.details, "quantity_invariant": "volume = ⅓·S_đáy·h"}, planner=r.planner)
        return r
    for g in k.goals:
        r.planner["goal_checks"][g["fact"]] = _quan_sat_cau_hinh(r.checker(g["call"]))
    for n in k.negated:
        r.planner["negated_checks"][n["fact"]] = _quan_sat_cau_hinh(r.checker(n["call"]))
    # Không có certificate chứng minh cho phủ định, bất kể phép kiểm trên một cấu hình cho kết quả gì.
    if dung := list(r.planner["negated_checks"]):
        return KetQuaTuyen("REFUSED", "NEGATED_CLAUSE",
                           f"mệnh đề phủ định {dung} chưa có chứng chỉ chứng minh độc lập; không phân loại giả thiết này",
                           tuple(dung), trace=r.trace, planner=r.planner)
    # Không có câu hỏi số học để phục vụ: các goal trên một cấu hình không đủ làm proof certificate.
    if k.goals and not r.answers:
        return KetQuaTuyen("REFUSED", "PROOF_UNVERIFIABLE",
                           "checker chỉ quan sát trên một cấu hình; chưa có chứng chỉ suy diễn từ giả thiết",
                           tuple(r.planner["goal_checks"]), trace=r.trace, planner=r.planner)
    return r


def _quan_sat_cau_hinh(value: bool | None) -> dict[str, Any]:
    """Ghi nhận checker như một quan sát thực nghiệm, tuyệt đối không nâng thành chứng minh định lý."""
    return {
        "evidence_state": {True: "TRUE_ON_CONFIGURATION", False: "FALSE_ON_CONFIGURATION", None: "UNVERIFIABLE"}[value],
        "proof_status": "UNVERIFIABLE",
        "can_present_as_proven": False,
    }


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
