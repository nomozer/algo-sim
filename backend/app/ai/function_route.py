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
import re
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


def _gan_nhan_chung_duong_cao_chinh_xac(
    canh: dict[str, Any],
    chart_metric: Any = None,
    *,
    trace: list[dict[str, Any]] | None = None,
) -> None:
    """Gắn chứng chỉ vuông góc chính xác (`perpendicular_witness`) theo hệ đo Gram đối xứng xác định dương (SPD)
    và nguồn gốc dựng hình cho các đoạn thẳng vuông góc với mặt đáy (`certificates.py`)."""
    from app.simulation.geometry_functions.certificates import attach_scene_perpendicular_certificates

    attach_scene_perpendicular_certificates(canh, chart_metric, trace=trace)


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


class _KhoiKhongKhai(ValueError):
    """A solid named on unnamed cut vertices without the planner's `derived` record. The Source Gate admits that solid
    only through the record, so this is our own inconsistency, refused at the route boundary (run
    `scene3d-section-inspector-c0`), never labelled or valued by guesswork."""


def _thay_ten(s: str, cu: list[tuple[str, str]]) -> str:
    """Rewrite each old notation (longest first) as a WHOLE name: never inside a dotted or primed name ("MII1" in
    "S.MII1", review F3). "Thiết diện HMH1" becomes the new name; a sentence that starts with it keeps its capital."""
    for truoc, sau in cu:
        hoa = sau[:1].upper() + sau[1:]
        s = re.sub(rf"[Tt]hiết diện {re.escape(truoc)}(?![\w'′])", lambda m: hoa if m[0][0] == "T" else sau, s)
        s = re.sub(rf"(?<![\w'′.]){re.escape(truoc)}(?![\w'′])",
                   lambda m: hoa if m.start() == 0 or s[:m.start()].rstrip().endswith((".", ":")) else sau, s)
    return s


def _vai_mat_cat(canh: dict[str, Any], auxiliary: tuple[dict, ...]) -> None:
    """Presentation only (run `scene3d-plane-section-display-identity`): a section plane's role states the SOURCE relation
    the planner read ("qua M và song song với (ABC)"), not its construction points ("qua M, H, H1": translates the source
    never names). Depends, coordinates and the construction itself are unchanged."""
    from app.simulation.geometry_functions.engine import ir_name
    from app.simulation.geometry_functions.registry import MAT_HAI_DUONG, MAT_SONG_SONG, MAT_VUONG_DUONG

    objs = {o["id"]: o for o in canh["objects"]}
    ky = lambda xs: "".join(xs).replace("'", "′")

    def ten_nguon(d: dict, nhan: list[str]) -> str:
        """The reference plane as the SOURCE writes it (review F2): a source "(ABCD)" is planned through A, B, C only,
        while another source writes "(ABC)" for the same base. Pick the candidate its quotes contain."""
        cau = " ".join(d.get("quotes") or ()).replace("′", "'")
        mat_ = mat_khoi(d["solid"], nhan)
        return next((c for c in (mat_, f"({ky(nhan)})") if c.replace("′", "'") in cau), mat_)

    def mat_khoi(khoi: str, nhan: list[str]) -> str:
        """The solid face holding the planner's reference points; no such face ⇒ the planner's points."""
        can = {ir_name(x) for x in nhan}
        for o in objs.values():
            if o.get("type") != "solid" or o.get("notation") != ky([khoi]) or not o.get("faces"):
                continue
            for f in sorted(o["faces"], key=len):
                mat_ = [o["vertex_ids"][i] for i in f]
                if can <= set(mat_):
                    k = mat_.index(ir_name(nhan[0]))
                    mat_ = mat_[k:] + mat_[:k]
                    if mat_[1] != ir_name(nhan[1]):          # read the cycle in the source's direction
                        mat_ = mat_[:1] + mat_[1:][::-1]
                    return "(" + "".join((objs.get(v) or {}).get("notation") or v for v in mat_) + ")"
        return f"({ky(nhan)})"

    for d in auxiliary:
        mat = objs.get(f"mp_td_{ir_name(d['goal'])}") if d.get("goal") else None
        if mat is None:
            continue
        if d.get("rule") == MAT_SONG_SONG:
            quan_he = f"song song với {ten_nguon(d, d['parallel_to'])}"
        elif d.get("rule") == MAT_HAI_DUONG:
            quan_he = "song song với " + " và ".join(ky(x) for x in d["lines"])
        elif d.get("rule") == MAT_VUONG_DUONG:
            quan_he = f"vuông góc với {ky(d['perpendicular_to'])}"
        else:
            continue
        mat["role"] = f"Mặt phẳng qua {ky(d['point'])} và {quan_he}"
        # Review R1 (run `scene3d-section-inspector-c0`): the fallback explanation read "Dựng mặt phẳng (α) qua ba điểm
        # M, H, H1." as if H, H1 defined (α). Source definition first, then the real construction and its auxiliaries.
        ten = mat.get("display_label") or mat.get("label")
        phu = ", ".join(ky([x]) for x in d.get("labels") or ())
        for e in canh["events"]:
            if e.get("object") == mat["id"] and e.get("action") == "CREATE" and phu:
                e["explanation"] = (f"Dựng {ten}: mặt phẳng qua {ky(d['point'])} và {quan_he}; dựng qua "
                                    f"{ky(d['point'])} và các điểm dựng phụ {phu}.")


def _an_dinh_thiet_dien_phu(canh: dict[str, Any], auxiliary: tuple[dict, ...]) -> None:
    """Presentation only (run `typedfactnext-planner-bridge`): a section vertex the source does not name (`DINH_CAT_CANH`
    fresh label) and anything built on it carry descriptive Vietnamese text and no notation, so a planner label (I, I1)
    never reaches the learner as if the problem had named it — the Adapter /3 policy. No id, coordinate or relation moves."""
    from app.simulation.geometry_functions.engine import ir_name
    from app.simulation.geometry_functions.registry import DINH_CAT_CANH

    objs = {o["id"]: o for o in canh["objects"]}
    buoc = canh.get("formation", {}).get("steps", [])

    def doi(oid: str, nhan: str, cau: str, lo: re.Pattern | None = None) -> None:
        """`lo`: rewrite only the events whose text leaks it (keeps a section's per-face steps informative)."""
        o = objs[oid]
        o.update(label=nhan, display_label=nhan, reference=nhan[:1].lower() + nhan[1:], notation=None)
        for e in canh["events"]:
            if e.get("object") == oid and (lo is None or any(
                    lo.search(str(e.get(k) or "")) for k in ("display_label", "learner_text", "explanation"))):
                e.update(display_label=nhan, learner_text=cau, explanation=cau)
                if isinstance(e.get("details"), dict) and "label" in e["details"]:
                    e["details"]["label"] = nhan
                if 0 <= e["step_index"] < len(buoc):
                    buoc[e["step_index"]]["learner_text"] = cau

    for d in auxiliary:
        if d.get("rule") != DINH_CAT_CANH:
            continue
        mat = objs.get(f"mp_td_{ir_name(d['goal'])}") or {}
        ten = mat.get("display_label") or mat.get("label") or "mặt cắt"
        for v in d["vertices"]:                          # the IR operand plane of each cut is the section plane again:
            if v.get("call") and (dup := objs.get(f"derived_{ir_name(v['label'])}_plane")):   # one visible owner only
                dup.update(render="non_visual", display_role="non_visual")
                canh_cat = "".join(v["edge"]).replace("'", "′")      # primes as the UI writes them (review P1)
                doi(dup["id"], ten, f"Xét mặt phẳng {ten} để tìm giao điểm với {canh_cat}.")
        # The planner's point-built plane name ("(MHH1)") is not the source's: learner text says the source name (review 2).
        # Rebuilt from the planner's operand order (`depends` is sorted): the plane's own notation is already the source
        # name, but each cut's operand plane (`derived_*_plane`) still composes "(MHH1)" into "Giao điểm của SB và (MHH1)".
        ky = "(" + "".join(d["plane"]).replace("'", "′") + ")" if d.get("plane") else mat.get("notation")
        if ky and ky != ten:
            def ve_ten(x: Any) -> Any:
                return x.replace(ky, ten) if isinstance(x, str) else x
            for o in canh["objects"]:
                for k in ("role", "label", "display_label", "reference"):
                    if k in o:
                        o[k] = ve_ten(o[k])
            for e in canh["events"]:
                for k in ("display_label", "learner_text", "explanation"):
                    if k in e:
                        e[k] = ve_ten(e[k])
            for s in buoc:
                if "learner_text" in s:
                    s["learner_text"] = ve_ten(s["learner_text"])
        phu = {v["label"]: v["edge"] for v in d["vertices"] if v["choice"] in ("fresh_intersection", "derived_fresh")}
        # Primes as the rest of the UI writes them (BB′): the inspector shows this label (review N2).
        hien = {x: f"giao điểm của {''.join(e).replace(chr(39), '′')} và {ten}" for x, e in phu.items()}
        for x, mo_ta in hien.items():
            if ir_name(x) in objs:
                objs[ir_name(x)]["role"] = "Điểm dựng phụ"
                doi(ir_name(x), mo_ta[:1].upper() + mo_ta[1:], f"Xác định {mo_ta}.")
        kd = d.get("derived")
        if not phu:
            continue
        an = re.compile(r"(?<![\w'])[A-Z0-9'.]*(?:" + "|".join(map(re.escape, sorted(phu, key=len, reverse=True)))
                        + r")[A-Z0-9'.]*(?![\w'])")
        # Lateral edges of the derived pyramid (formation expansion `canh_ben_<apex>_<v>`; run
        # `backend-hybrid-contract-unification`): edges of that solid, not segments of the section.
        canh_ben = ({f"canh_ben_{ir_name(kd['apex'])}_{ir_name(v)}" for v in kd["base"]} if kd else set())
        ben = f"Cạnh bên của khối chóp đỉnh {kd['apex']} cắt bởi {ten}" if kd else ""
        # Old notation of a renamed section / derived solid → how learner text now calls it (run
        # `scene3d-plane-section-display-identity`): quantities and events naming them are rewritten through it.
        cu: list[tuple[str, str]] = []
        for o in canh["objects"]:
            # This cut's section never keeps a vertex cycle: a cycle would name an unnamed vertex, also when a
            # construction point coincides with it (prism: translate H ≡ cut BB′∩(α), so the cycle read "HMH1").
            la_td = o.get("type") == "section" and mat.get("id") in (o.get("depends") or ())
            if (o["id"] in {ir_name(x) for x in phu} or o.get("type") == "quantity"
                    or not (la_td or an.search(str(o.get("notation") or o.get("label") or "")))):
                continue
            truoc = o.get("notation")
            if o.get("type") == "solid" and not kd:
                raise _KhoiKhongKhai(o["id"])
            if o.get("type") == "solid" and kd:
                doi(o["id"], f"Khối chóp đỉnh {kd['apex']} cắt bởi {ten}", f"Dựng khối chóp đỉnh {kd['apex']} cắt bởi {ten}.")
                o["role"] = f"Đỉnh {kd['apex']}, đáy là thiết diện bởi {ten}"
            elif o.get("type") in ("polygon3", "section") and an.search(str(o.get("notation") or o.get("label") or "")):
                doi(o["id"], f"Thiết diện bởi {ten}", f"Dựng thiết diện bởi {ten}.", an)
            elif o.get("type") in ("polygon3", "section"):
                # Named only through a coincident construction point: rename the object; its events keep their own
                # text ("Thiết diện khép lại thành tam giác …") and only the old cycle name is rewritten below.
                nhan = f"Thiết diện bởi {ten}"
                o.update(label=nhan, display_label=nhan, reference=nhan[:1].lower() + nhan[1:], notation=None)
            elif o["id"] in canh_ben:
                doi(o["id"], ben, f"Dựng {ben[:1].lower()}{ben[1:]}.", an)
            else:
                doi(o["id"], "Đoạn của thiết diện", "Nối các giao điểm của thiết diện.", an)
            if truoc and o.get("type") in ("solid", "polygon3", "section"):
                cu.append((truoc, o["reference"]))
            if isinstance(o.get("role"), str) and an.search(o["role"]):
                o["role"] = an.sub(lambda m: hien.get(m[0], "thiết diện"), o["role"])
        cu.sort(key=lambda p: len(p[0]), reverse=True)

        thay_cu = lambda s: _thay_ten(s, cu)

        def thay(s: str) -> str:
            return an.sub(lambda m: hien.get(m[0], "thiết diện"), thay_cu(s))

        # A quantity on a renamed object keeps its kind ("Diện tích", "Tỉ số"): only the names inside it change, and
        # it has no notation, since that notation cannot be written without naming an unnamed vertex.
        for o in canh["objects"]:
            nguon = [o.get("label"), o.get("notation"), (o.get("formula") or {}).get("text")]
            if o.get("type") != "quantity" or not any(isinstance(s, str) and thay(s) != s for s in nguon):
                continue
            nhan = thay(str(o.get("label") or ""))
            o.update(label=nhan, display_label=nhan, reference=nhan[:1].lower() + nhan[1:], notation=None)
            if isinstance((o.get("formula") or {}).get("text"), str):
                o["formula"]["text"] = thay(o["formula"]["text"])
            if isinstance(o.get("role"), str):
                o["role"] = thay(o["role"])
        for e in canh["events"]:
            for k in ("display_label", "learner_text", "explanation"):
                if isinstance(e.get(k), str):
                    e[k] = thay_cu(e[k])
        for s in buoc:
            if isinstance(s.get("learner_text"), str):
                s["learner_text"] = thay_cu(s["learner_text"])
        for e in canh["events"]:                         # the group step building those lateral edges
            if set(e.get("objects") or ()) & canh_ben:
                nhom = f"Các cạnh bên của khối chóp đỉnh {kd['apex']} cắt bởi {ten}"
                cau = f"Dựng {nhom[:1].lower()}{nhom[1:]}."
                e.update(display_label=nhom, learner_text=cau, explanation=cau)
                if isinstance(e.get("details"), dict) and "label" in e["details"]:
                    e["details"]["label"] = nhom
                if 0 <= e["step_index"] < len(buoc):
                    buoc[e["step_index"]]["learner_text"] = cau
        for e in canh["events"]:                         # remaining event text naming a fresh label
            for k in ("display_label", "learner_text", "explanation"):
                if isinstance(e.get(k), str) and an.search(e[k]):
                    e[k] = an.sub(lambda m: "đỉnh thiết diện" if m[0] in hien else "thiết diện", e[k])
            if isinstance(e.get("details"), dict):
                for k, v in list(e["details"].items()):
                    if isinstance(v, list) and any(isinstance(x, str) and x in hien for x in v):
                        e["details"][k] = [hien.get(x, x) if isinstance(x, str) else x for x in v]
                    elif isinstance(v, str) and an.search(v):
                        e["details"][k] = an.sub(lambda m: hien.get(m[0], "thiết diện"), v)
        for s in buoc:
            if isinstance(s.get("learner_text"), str) and an.search(s["learner_text"]):
                s["learner_text"] = an.sub(lambda m: "đỉnh thiết diện" if m[0] in hien else "thiết diện", s["learner_text"])


def run_function_route(problem_text: str, plan: Any, auxiliary: tuple[dict, ...] = (),
                       read_quotes: tuple[str, ...] = ()) -> KetQuaTuyen:
    """`auxiliary` chỉ do `run_fact_route` truyền (điểm phụ của planner); nhánh A không có đường nào đặt nó.
    `read_quotes` cũng vậy: quote của goal / mệnh đề phủ định mà planner giữ và route kiểm trên hình — đã đọc, không là
    giả thiết (cổng phủ tiền đề tính chúng là đã đọc)."""
    r = dung_tu_loi_goi(problem_text, plan, auxiliary, read_quotes)
    if r.status != "SERVED":
        return r
    try:
        from app.simulation.geometry_functions.registry import (
            DINH_CAT_CANH, MAT_HAI_DUONG, MAT_SONG_SONG, MAT_VUONG_DUONG)
        from app.simulation.geometry_functions.engine import ir_name
        two_line = [d for d in auxiliary if d.get('rule') == MAT_HAI_DUONG]
        # A derived section plane's source name (α) is not rebuildable from its construction points either (the
        # planner's parallel-plane translates H, H1 gave "(MHH1)"); keep it as notation/reference, with or without
        # stated cut edges (run `scene3d-plane-section-display-identity`, review F1).
        cut = any(d.get('rule') in (DINH_CAT_CANH, MAT_SONG_SONG, MAT_VUONG_DUONG) for d in auxiliary)
        with _metric.using(r.chart_metric):
            state = build_simulation_state(r.spec, r.exec_result, r.declared_topology,
                                           prefer_declared_plane_names=bool(two_line) or cut)
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
            _gan_nhan_chung_duong_cao_chinh_xac(canh, r.chart_metric, trace=r.trace)
            _an_dinh_thiet_dien_phu(canh, auxiliary)
            _vai_mat_cat(canh, auxiliary)
    except _KhoiKhongKhai as e:
        return KetQuaTuyen("REFUSED", "SCENE_BUILD_FAILED",
                           f"khối {e} dựng trên đỉnh thiết diện không tên mà không có khối dẫn xuất đã khai", trace=r.trace)
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


def run_typed_fact_next_planner_route(raw: Any) -> KetQuaTuyen:
    """TypedFactNext → pure bridge → the ONE planner / Source Gate / engine of route B (`run_fact_route`). Research
    only (run `typedfactnext-planner-bridge`): not wired to `/api/analyze`; Adapter /3 (`run_typed_fact_next_route`) is
    left as it is. A construct `TypedFact` cannot express is refused (`BRIDGE_UNSUPPORTED_*`), never re-routed."""
    from app.simulation.geometry_functions import TuChoi
    from app.simulation.geometry_functions.typed_fact_next_bridge import BRIDGE_VERSION, bridge

    try:
        b = bridge(raw)
    except TuChoi as e:
        return KetQuaTuyen("REFUSED", e.code, e.reason, e.calls, details=e.data,
                           planner={"bridge": {"version": BRIDGE_VERSION}})
    except (KeyError, TypeError):
        # PremiseSpec.args is an open dictionary; malformed operands must not escape this input boundary.
        return KetQuaTuyen("REFUSED", "INVALID_TYPED_FACT_NEXT", "đối số giả thiết bị thiếu hoặc sai kiểu",
                           planner={"bridge": {"version": BRIDGE_VERSION}})
    return chay_sau_cau_noi(b)


def chay_sau_cau_noi(b: dict[str, Any]) -> KetQuaTuyen:
    """The ONE route after a TypedFactNext bridge (`/1` and `/2`, run `hybrid-contract-v2`): planner → Source Gate →
    engine → Scene3D (`run_fact_route`), then the declared length unit and plane names checked against the gated output."""
    r = run_fact_route(b["bridge"]["problem_text"], {"facts": b["facts"]})
    r.planner = {**(r.planner or {}), "bridge": {k: v for k, v in b["bridge"].items() if k != "problem_text"}}
    unit = b["bridge"]["declared_length_unit"]
    if r.status == "SERVED" and unit is not None and unit != (r.length_unit or "1"):
        code = "NON_HOMOGENEOUS_LENGTHS" if unit == "1" else "BRIDGE_UNSUPPORTED_LENGTH_UNIT"
        return KetQuaTuyen("REFUSED", code, "đơn vị đã khai không được biểu diễn bởi dữ kiện trên planner",
                           planner=r.planner)
    if r.status == "SERVED":
        from app.simulation.geometry_functions.engine import ir_name

        objects = {o["id"]: o for o in r.scene3d["objects"]}
        for section_id, name in b["bridge"]["declared_plane_names"].items():
            plane = objects.get(f"mp_td_{ir_name(section_id)}", {})
            if plane.get("display_label") != f"({name})":
                return KetQuaTuyen("REFUSED", "SOURCE_OBJECT_MISMATCH", "tên mặt đã khai không khớp mặt được Source Gate xác minh",
                                   planner=r.planner)
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
