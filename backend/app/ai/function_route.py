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


def _gan_nhan_chung_duong_cao_chinh_xac(canh: dict[str, Any], chart_metric: Any = None) -> None:
    """Gắn chứng chỉ vuông góc chính xác (`perpendicular_witness`) theo hệ đo Gram cho các đoạn thẳng
    là đường cao hoặc cạnh bên vuông góc với mặt đáy (POC-2, GAP-D1).
    Điều kiện:
      v_seg = P_from - P_foot (với foot nằm trên đáy z=0 hoặc vertex đáy)
      u1, u2 là hai cạnh đáy xuất phát từ chân đường cao (nếu foot là đỉnh đáy) hoặc hai cạnh đáy
      dot_G(v_seg, u1) == 0 và dot_G(v_seg, u2) == 0
      norm_G(v_seg)^2 > 0 và det Gram_G(u1, u2) > 0
    Nếu thoả mãn, gán `perpendicular_witness` vào segment3."""
    objects = canh.get("objects") or []
    if chart_metric is None:
        g_mat = [[Fraction(1 if i == j else 0) for j in range(3)] for i in range(3)]
    elif hasattr(chart_metric, "g"):
        g_mat = [[Fraction(str(x)) for x in row] for row in chart_metric.g]
    elif isinstance(chart_metric, (list, tuple)):
        g_mat = [[Fraction(str(x)) for x in row] for row in chart_metric]
    else:
        g_mat = [[Fraction(1 if i == j else 0) for j in range(3)] for i in range(3)]

    points_by_id: dict[str, list[Fraction]] = {}
    for o in objects:
        if isinstance(o, dict) and o.get("type") == "point3" and isinstance(o.get("xyz"), list):
            points_by_id[o["id"]] = [Fraction(str(x)) for x in o["xyz"]]

    base_polys = [
        o
        for o in objects
        if isinstance(o, dict)
        and o.get("type") == "polygon3"
        and "CONSTRUCT_BASE" in (o.get("formation_roles") or [])
    ]
    if not base_polys:
        return

    base = base_polys[0]
    base_vids = list(base.get("vertex_ids") or [])
    base_pts = [points_by_id[vid] for vid in base_vids if vid in points_by_id]
    if len(base_pts) < 3:
        return

    segments = [o for o in objects if isinstance(o, dict) and o.get("type") == "segment3"]

    def _gram_dot(u: list[Fraction], v: list[Fraction]) -> Fraction:
        return sum(u[i] * g_mat[i][j] * v[j] for i in range(3) for j in range(3))

    def _frac_sub(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
        return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

    for seg in segments:
        if seg.get("perpendicular_witness") is not None:
            continue
        ep_ids = seg.get("endpoint_ids") or []
        if len(ep_ids) != 2 or ep_ids[0] not in points_by_id or ep_ids[1] not in points_by_id:
            continue
        p0_id, p1_id = ep_ids[0], ep_ids[1]
        p0_in_base = p0_id in base_vids or points_by_id[p0_id][2] == 0
        p1_in_base = p1_id in base_vids or points_by_id[p1_id][2] == 0
        if p0_in_base == p1_in_base:
            continue

        foot_id = p1_id if p1_in_base else p0_id
        from_id = p0_id if p1_in_base else p1_id
        foot_pt = points_by_id[foot_id]
        from_pt = points_by_id[from_id]
        v_seg = _frac_sub(from_pt, foot_pt)

        if foot_id in base_vids and len(base_vids) >= 3:
            idx = base_vids.index(foot_id)
            next_pt = points_by_id[base_vids[(idx + 1) % len(base_vids)]]
            prev_pt = points_by_id[base_vids[(idx - 1) % len(base_vids)]]
            u1 = _frac_sub(next_pt, foot_pt)
            u2 = _frac_sub(prev_pt, foot_pt)
        else:
            u1 = _frac_sub(base_pts[1], base_pts[0])
            u2 = _frac_sub(base_pts[-1], base_pts[0])

        dot1 = _gram_dot(v_seg, u1)
        dot2 = _gram_dot(v_seg, u2)
        norm_seg_sq = _gram_dot(v_seg, v_seg)
        gram_det_base = _gram_dot(u1, u1) * _gram_dot(u2, u2) - (_gram_dot(u1, u2) ** 2)

        if norm_seg_sq > 0 and gram_det_base > 0 and dot1 == 0 and dot2 == 0:
            seg["perpendicular_witness"] = {
                "from": from_id,
                "foot": [str(x) for x in foot_pt],
                "on": base["id"],
                "marker": {
                    "u": [str(x) for x in u1],
                    "v": [str(x) for x in v_seg],
                },
                "certificate": "exact-gram-line-plane-orthogonality/1",
            }


def _ke_diem_dung(canh: dict[str, Any], vai: dict[str, str]) -> None:
    """Lời kể bước dựng một điểm: nói PHÉP DỰNG từ producer + ký hiệu toán hạng, thay "Dựng M." (run
    `pedagogical-construction-sequencing`). Producer khác dùng vai do `display_names` đã phát; thiếu ký hiệu ⇒ giữ lời cũ.
    Sửa cả sự kiện lẫn bước hình thành cùng chỉ số (frame k ⇔ trace[k])."""
    theo_id = {o["id"]: o for o in canh["objects"]}
    ky = lambda i: (theo_id.get(i) or {}).get("notation")
    for e in canh["events"]:
        o = theo_id.get(e.get("object") or "")
        if e.get("action") != "CREATE" or not o or o["type"] != "point3" or not ky(o["id"]):
            continue
        n, nguon = ky(o["id"]), [ky(d) for d in o.get("depends") or ()]
        if o.get("producer") == "construct_point.midpoint" and len(nguon) == 2 and all(nguon):
            cau = f"Dựng {n} là trung điểm của đoạn {nguon[0]}{nguon[1]}."
        elif (o.get("producer") == "construct_point.translate" and len(nguon) == 2 and all(nguon)
              and [theo_id[d]["type"] for d in o["depends"]] == ["point3", "vector3"]):   # review C4: point, then vector
            cau = f"Qua {nguon[0]} dựng điểm {n} sao cho vectơ {nguon[0]}{n} bằng vectơ {nguon[1]}."
        elif vai.get(o["id"]):
            cau = f"Dựng {n}: {vai[o['id']][:1].lower()}{vai[o['id']][1:]}."
        else:
            continue
        e["learner_text"] = cau
        canh["formation"]["steps"][e["step_index"]]["learner_text"] = cau


def run_function_route(problem_text: str, plan: Any, auxiliary: tuple[dict, ...] = (),
                       read_quotes: tuple[str, ...] = ()) -> KetQuaTuyen:
    """`auxiliary` chỉ do `run_fact_route` truyền (điểm phụ của planner); nhánh A không có đường nào đặt nó.
    `read_quotes` cũng vậy: quote của goal / mệnh đề phủ định mà planner giữ và route kiểm trên hình — đã đọc, không là
    giả thiết (cổng phủ tiền đề tính chúng là đã đọc)."""
    r = dung_tu_loi_goi(problem_text, plan, auxiliary, read_quotes)
    if r.status != "SERVED":
        return r
    try:
        from app.simulation.geometry_functions.registry import MAT_HAI_DUONG
        from app.simulation.geometry_functions.engine import ir_name
        two_line = [d for d in auxiliary if d.get('rule') == MAT_HAI_DUONG]
        with _metric.using(r.chart_metric):
            state = build_simulation_state(r.spec, r.exec_result, r.declared_topology,
                                           prefer_declared_plane_names=bool(two_line))
            # CONTRACT-BE-1: the third argument carries topology, not obligations, so `targets` came out empty and the
            # asked quantity read as `intermediate` while its event was FINAL_RESULT; the engine names what the source asks.
            state["targets"] = list(r.targets)
            # Presentation of the certified auxiliary binding; no new geometry or semantic authority.
            aux_ids = ({ir_name(p) for d in two_line for p in d['labels']}
                       | {ir_name(d['label']) for d in auxiliary if d.get('effect_binding') and d.get('fresh')}
                       | {ir_name(p) for d in auxiliary if d.get('rule') == 'effect-chain' for p in d['labels']})
            vai = {o['id']: o.get('role') for o in state['scene']['objects'] if (o.get('producer') or '').startswith('construct_point.')}
            for obj in state['scene']['objects']:
                if obj['id'] in aux_ids:
                    obj['role'] = 'Điểm dựng phụ'
                    state['provenance'].setdefault(obj['id'], {})['binding'] = 'AUXILIARY'
            canh = build_scene3d(state)
            # Existing assign IR returns a geometric line. Its verified construction is not a scalar measurement.
            bound_lines = {s['object'] for s in r.trace if s.get('step')=='resolve_line' and s.get('relation_verified')}
            for event in canh['events']:
                if event.get('object') in bound_lines:
                    label = event['display_label']
                    text = f'Dựng {label[:1].lower()}{label[1:]}.'
                    event.update(action='CREATE',semantic_kind='GEOMETRY_CONSTRUCTION',learner_text=text,explanation=text)
                    canh['formation']['steps'][event['step_index']].update(
                        semantic_kind='GEOMETRY_CONSTRUCTION',learner_text=text)
            _ke_diem_dung(canh, vai)
            _gan_nhan_chung_hinh_chieu(canh, r.spec, r.exec_result.final_memory)
            _gan_nhan_chung_duong_cao_chinh_xac(canh, r.chart_metric)
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
