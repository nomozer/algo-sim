# -*- coding: utf-8 -*-
"""Chẩn đoán CHẤT LƯỢNG ĐẦU RA ĐƯỢC NHẬN — bốn lớp phủ cho TỪNG nghĩa vụ. CHỈ QUAN SÁT, 0 mạng.

`SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS` (2026-09-15). Lượt follow-up B02 được route PHỤC VỤ với final_memory và
đáp số đúng 3/3 nhưng cảnh không có vật `section`. Route hỏi *"có phép tính ra witness không"*; nó không hỏi *"vật
được đo có được DỰNG và HIỆN đúng loại không"*. Module này đo khoảng cách ấy mà không đổi một quyết định nào:

    COMPUTATION_COVERAGE   witness do đúng một câu lệnh `measure` (đúng lượng đo, toán hạng đúng kiểu) sinh ra VÀ
                           có giá trị chính xác trong final_memory
    CONSTRUCTION_COVERAGE  chủ thể của phép đo được một câu lệnh dựng ra; yêu cầu thiết diện ⇒ đúng `construct_section`
    SCENE_COVERAGE         cảnh chứa chủ thể với đúng loại; thiết diện: khép kín, đúng tập đỉnh, đúng mặt phẳng nguồn
                           (khi có tham chiếu)
    ANSWER_COVERAGE        giá trị hiển thị của witness trùng đáp số đăng ký và hiện đúng trên readout của cảnh

Yêu cầu hình (`required_scene_kind`) CHỈ đến từ hai nguồn, không suy từ tên:
  · `REQUEST_CONTRACT` — nghĩa vụ `section_matches` trên cùng container (tham chiếu dựng lại bằng `cross_section`);
  · `REGISTERED_REFERENCE` — yêu cầu đăng ký trước của bộ đo (con trỏ nghĩa vụ + đỉnh + mặt phẳng).

Không tự làm hình học: bản đồ tên (`check_structural_coverage`), phân giải witness (`phan_giai_witness`), câu lệnh dựng
(`_cau_lenh_dung`), chu trình thiết diện (`same_section_cycle` · `cross_section`), mặt phẳng (`point_on_plane` ·
`parallel_planes`), hiển thị số (`radical.display`) đều là hàm sản phẩm. Đầu ra chỉ có con trỏ, loại, trạng thái,
số đếm và mã lý do — không tên, toạ độ, giá trị, công thức, chương trình hay cảnh.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

PHIEN_BAN = "accepted-output-quality/1"
PASS, FAIL = "PASS", "FAIL"
KHONG_AP_DUNG, CHUA_DANH_GIA, CHUA_KIEM_CHUNG = "NOT_APPLICABLE", "NOT_EVALUATED", "UNVERIFIED"
TRANG_THAI = (PASS, FAIL, KHONG_AP_DUNG, CHUA_DANH_GIA, CHUA_KIEM_CHUNG)
NGUON_YEU_CAU = ("REQUEST_CONTRACT", "REGISTERED_REFERENCE")
NGOAI_TU_VUNG = "OUT_OF_VOCABULARY"

#: Trạng thái `coverage_gate.phan_giai_witness` → mã lý do lớp PHÉP TÍNH. Một nhánh, một mã.
_MA_PHAN_GIAI = {
    "WITNESS_KHONG_KHAI": "WITNESS_MISSING_IN_CONTRACT",
    "WITNESS_KHONG_CO_PRODUCER": "WITNESS_WITHOUT_PRODUCER",
    "WITNESS_NHIEU_PRODUCER": "WITNESS_MULTIPLE_PRODUCERS",
    "PRODUCER_KHONG_PHAI_MEASURE": "WITNESS_NOT_MEASURED",
    "QUANTITY_LECH": "WITNESS_QUANTITY_MISMATCH",
    "THIEU_TOAN_HANG": "WITNESS_OPERAND_MISSING",
    "TOAN_HANG_SAI_KIEU": "WITNESS_OPERAND_TYPE_MISMATCH",
}
#: Hai trạng thái CÓ một câu lệnh `measure` đúng lượng đo với toán hạng đúng kiểu. `KHONG_GAN_VOI_CHU_THE` chỉ nói toán
#: hạng nằm ngoài bao đóng dựng của container — hình dạng đúng của phép đo quan hệ (khoảng cách điểm–đường); câu hỏi
#: "witness có dẫn xuất từ container không" là của cổng phủ cấu trúc, không phải của lớp này.
_DO_THAT = frozenset({"OK", "KHONG_GAN_VOI_CHU_THE"})

MA_LY_DO = (
    # lớp phép tính
    *_MA_PHAN_GIAI.values(), "WITNESS_RESOLUTION_UNCLASSIFIED", "WITNESS_NOT_REALIZED",
    # lớp phép dựng
    "SUBJECT_NOT_CONSTRUCTED", "SUBJECT_MULTIPLE_PRODUCERS", "MISSING_SECTION_CONSTRUCTION",
    # lớp cảnh
    "SCENE_UNAVAILABLE", "SUBJECT_SCENE_OBJECT_MISSING", "CONSTRUCTED_SUBJECT_ABSENT_FROM_SCENE",
    "MISSING_SECTION_SCENE_OBJECT", "POLYGON_WITHOUT_SECTION_PROVENANCE", "SCENE_KIND_MISMATCH",
    # topology thiết diện
    "SECTION_NOT_CLOSED", "SECTION_VERTEX_SET_MISMATCH", "SECTION_PLANE_MISMATCH", "SECTION_PLANE_UNRESOLVED",
    "SECTION_REFERENCE_UNREADABLE",
    # lớp đáp số
    "ANSWER_NOT_REALIZED", "ANSWER_MISMATCH", "ANSWER_NOT_IN_SCENE_READOUT",
)
KHOA_DONG = ("obligation_pointer", "pointer_status", "operation_kind", "computation_coverage", "construction_coverage",
             "scene_coverage", "answer_coverage", "required_scene_kind", "required_kind_source", "subject_statement_kinds",
             "observed_subject_scene_kinds", "observed_scene_count", "topology_status", "reason_codes")


def _tu_vung() -> frozenset[str]:
    from typing import get_args

    from pydantic import BaseModel

    from app.simulation.semantic_program import contract as C
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    kieu_lenh = {v.model_fields["kind"].default for v in vars(C).values()
                 if isinstance(v, type) and issubclass(v, BaseModel) and "kind" in getattr(v, "model_fields", {})
                 and isinstance(v.model_fields["kind"].default, str)}
    return frozenset({*TRANG_THAI, *MA_LY_DO, *NGUON_YEU_CAU, PHIEN_BAN, NGOAI_TU_VUNG, "EXACT", "AMBIGUOUS",
                      "memory_initial_value", "multiple", "quantity", *OBLIGATION_KINDS, *get_args(C.MemoryType), *kieu_lenh})


#: Mọi chuỗi được phép xuất hiện trong chẩn đoán (ngoài con trỏ nghĩa vụ). Test riêng tư khoá tập này.
CHUOI_CHO_PHEP = _tu_vung()


def _ma(v: Any) -> Any:
    return v if v is None or (isinstance(v, str) and v in CHUOI_CHO_PHEP) else NGOAI_TU_VUNG


def _vec(xyz: Any):
    from app.simulation.geometry.exact import Vec3

    try:
        return Vec3.of(*(Fraction(str(c)) for c in xyz)) if isinstance(xyz, (list, tuple)) and len(xyz) == 3 else None
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def _mat_phang_canh(o: dict):
    from app.simulation.geometry.exact import Plane3

    p, n = _vec(o.get("point")), _vec(o.get("normal"))
    return None if p is None or n is None or n.is_zero() else Plane3(point=p, normal=n)


def _yeu_cau(contract, anh, mem: dict, dang_ky) -> dict[str, dict]:
    """`con trỏ nghĩa vụ → {kind, source, ref}`. `ref = None` ⇒ không có tham chiếu đọc được (topology không đánh giá)."""
    from app.simulation.geometry.exact import Plane3
    from app.simulation.geometry.section import Polyhedron, cross_section

    ra: dict[str, dict] = {}
    theo_container: dict[str, dict] = {}
    for ob in contract.obligations:
        if ob.kind != "section_matches":
            continue
        sol, pl, ref = mem.get(anh(ob.params.get("solid"))), mem.get(anh(ob.params.get("plane"))), None
        if isinstance(sol, Polyhedron) and isinstance(pl, Plane3):
            try:
                ref = {"vertices": tuple(cross_section(sol, pl).polygon), "plane": pl}
            except Exception:  # noqa: BLE001 — không dựng lại được thì không có tham chiếu, không đoán
                ref = None
        theo_container[anh(ob.container)] = {"kind": "section", "source": "REQUEST_CONTRACT", "ref": ref, "ref_unreadable": False}
    for i, ob in enumerate(contract.obligations):
        if anh(ob.container) in theo_container:
            ra[f"/obligations/{i}"] = theo_container[anh(ob.container)]
    for y in dang_ky or ():
        ref, doc_hong = None, False
        r = y.get("reference") or None
        if r:
            dinh = [_vec(v) for v in r.get("vertices") or ()]
            pl = r.get("plane") or {}
            n = _vec(pl.get("normal"))
            try:
                c = Fraction(str(pl.get("c")))
            except (ValueError, ZeroDivisionError, TypeError):
                c = None
            if dinh and None not in dinh and n is not None and not n.is_zero() and c is not None:
                ref = {"vertices": tuple(dinh), "plane": Plane3.from_equation(n.x, n.y, n.z, -c)}
            else:
                doc_hong = True
        ra[y["obligation_pointer"]] = {"kind": y.get("required_scene_kind"), "source": "REGISTERED_REFERENCE",
                                       "ref": ref, "ref_unreadable": doc_hong}
    return ra


def _kiem_thiet_dien(o: dict, vat: dict, yc: dict) -> tuple[str, list[str]]:
    from app.simulation.geometry.predicates import parallel_planes, point_on_plane
    from app.simulation.geometry.section import same_section_cycle

    ma: list[str] = []
    poly = [_vec(v) for v in o.get("polygon") or ()]
    doc_duoc = bool(poly) and None not in poly
    if o.get("closed") is not True or not doc_duoc or len(poly) < 3:
        ma.append("SECTION_NOT_CLOSED")
    ref = yc.get("ref")
    if ref is None:
        if yc.get("ref_unreadable"):
            ma.append("SECTION_REFERENCE_UNREADABLE")
        return (FAIL if ma else CHUA_DANH_GIA), ma
    if doc_duoc and len(poly) >= 3 and not same_section_cycle(poly, ref["vertices"]):
        ma.append("SECTION_VERTEX_SET_MISMATCH")
    # Mặt phẳng nguồn: `construct_section` chở nó trong `depends` (bảng
    # `_NGUON_CUA_PHEP_DUNG` cho `construct_section` = (solid, plane)). Một thiết
    # diện ĐÃ CHUẨN HOÁ từ `polygon3` thì `depends` là các ĐỈNH — nguồn plane–solid
    # của nó nằm ở `section_source` (`SECTION_PROVENANCE_NORMALIZATION`, 2026-09-20).
    # Đọc cả hai đường, theo đúng thứ tự thẩm quyền; không có đường nào ⇒ UNRESOLVED.
    ten_mp = (o.get("section_source") or {}).get("plane")
    if ten_mp and (vat.get(ten_mp) or {}).get("type") == "plane3":
        nguon = [vat[ten_mp]]
    else:
        nguon = [vat[n] for n in o.get("depends") or () if (vat.get(n) or {}).get("type") == "plane3"]
    if len(nguon) != 1:
        ma.append("SECTION_PLANE_UNRESOLVED")
    else:
        mp = _mat_phang_canh(nguon[0])
        if mp is None or not (parallel_planes(mp, ref["plane"]) and point_on_plane(mp.point, ref["plane"])
                              and all(point_on_plane(v, mp) for v in (poly if doc_duoc else ()))):
            ma.append("SECTION_PLANE_MISMATCH")
    return (FAIL if ma else PASS), ma


def chan_doan_chat_luong_dau_ra(contract, spec, final_memory: dict | None, scene3d: dict | None, *,
                                route_served: bool | None = None, visual_requirements=None,
                                registered_answers: dict[str, str] | None = None) -> dict[str, Any]:
    """RequestContract + chương trình + final_memory + cảnh → chẩn đoán bốn lớp, một hàng mỗi nghĩa vụ (thứ tự nguồn).

    Thuần tuý: không ghi, không mạng, không trạng thái chung, không đổi đầu vào. `route_served` chỉ dùng để dựng hai cờ
    tổng hợp; `None` ⇒ hai cờ `None`.
    """
    from app.simulation.geometry.radical import display, is_exact_number
    from app.simulation.semantic_program import coverage_gate as CG
    from app.simulation.semantic_program.ir_static_check import bang_ky_hieu
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS, WITNESS_FREE_KINDS

    mem = dict(final_memory or {})
    ten = dict(CG.check_structural_coverage(contract, spec).ten_da_hoa_giai)

    def anh(n):
        return ten.get(n, n) if isinstance(n, str) else n

    declared = bang_ky_hieu(spec)
    vat = ({o.get("id"): o for o in scene3d.get("objects") or () if isinstance(o, dict)}
           if isinstance(scene3d, dict) else None)
    goc = contract.model_dump(mode="json").get("obligations") or []
    yeu_cau = _yeu_cau(contract, anh, mem, visual_requirements)
    khai_gia_tri = {d.name for d in spec.memory_declarations if d.initial_value is not None}
    dong: list[dict[str, Any]] = []

    for i, ob in enumerate(contract.obligations):
        con_tro = f"/obligations/{i}"
        ma: list[str] = []
        yc = yeu_cau.get(con_tro)
        w = None
        # ── PHÉP TÍNH ────────────────────────────────────────────────────────
        if ob.kind in WITNESS_FREE_KINDS:
            tinh, chu_the = KHONG_AP_DUNG, [anh(ob.container)]
        else:
            w = anh(ob.witness) if ob.witness else None
            ob_m = ob.model_copy(update={"container": anh(ob.container),
                                         "params": {**ob.params, **({"witness": w} if w else {})}})
            pg = CG.phan_giai_witness(spec, ob_m, declared)
            co_gia_tri = bool(w) and is_exact_number(mem.get(w))
            tinh = PASS if pg.diagnostic_status in _DO_THAT and co_gia_tri else FAIL
            if pg.diagnostic_status not in _DO_THAT:
                ma.append(_MA_PHAN_GIAI.get(pg.diagnostic_status, "WITNESS_RESOLUTION_UNCLASSIFIED"))
            if not co_gia_tri:
                ma.append("WITNESS_NOT_REALIZED")
            toan_hang = ([v for v in (pg.operands or {}).values() if isinstance(v, str)]
                         if pg.diagnostic_status in _DO_THAT else [])
            chu_the = toan_hang or [anh(ob.container)]

        # ── PHÉP DỰNG ────────────────────────────────────────────────────────
        kieu_dung: list[str | None] = []
        dung = PASS
        for s in chu_the:
            cau = CG._cau_lenh_dung(spec.statements, s)
            if len(cau) == 1:
                kieu_dung.append(getattr(cau[0], "kind", None))
            elif len(cau) > 1:
                kieu_dung.append("multiple")
                dung = FAIL
                ma.append("SUBJECT_MULTIPLE_PRODUCERS")
            elif s in khai_gia_tri:
                kieu_dung.append("memory_initial_value")
            else:
                kieu_dung.append(None)
                dung = FAIL
                ma.append("SUBJECT_NOT_CONSTRUCTED")
        if yc and yc.get("kind") == "section" and kieu_dung[0] != "construct_section":
            dung = FAIL
            ma.append("MISSING_SECTION_CONSTRUCTION")

        # ── CẢNH ─────────────────────────────────────────────────────────────
        topo = KHONG_AP_DUNG if not (yc and yc.get("kind") == "section") else CHUA_DANH_GIA
        if vat is None:
            canh, quan_sat, dem = FAIL, [None] * len(chu_the), 0
            ma.append("SCENE_UNAVAILABLE")
        else:
            quan_sat = [(vat.get(s) or {}).get("type") for s in chu_the]
            canh = PASS
            for loai, kd in zip(quan_sat, kieu_dung):
                if loai is None:
                    canh = FAIL
                    ma.append("SUBJECT_SCENE_OBJECT_MISSING")
                    if kd not in (None, "multiple"):
                        ma.append("CONSTRUCTED_SUBJECT_ABSENT_FROM_SCENE")
            if yc and yc.get("kind"):
                if quan_sat[0] != yc["kind"]:
                    canh = FAIL
                    if yc["kind"] == "section":
                        ma.append("MISSING_SECTION_SCENE_OBJECT")
                        if quan_sat[0] == "polygon3":
                            ma.append("POLYGON_WITHOUT_SECTION_PROVENANCE")
                    if quan_sat[0] not in (None, "polygon3"):
                        ma.append("SCENE_KIND_MISMATCH")
                elif yc["kind"] == "section":
                    topo, ma_topo = _kiem_thiet_dien(vat[chu_the[0]], vat, yc)
                    ma += ma_topo
                    if topo == FAIL:
                        canh = FAIL
            dich = yc["kind"] if yc and yc.get("kind") else quan_sat[0]
            dem = sum(1 for o in vat.values() if dich is not None and o.get("type") == dich)

        # ── ĐÁP SỐ ───────────────────────────────────────────────────────────
        if ob.kind in WITNESS_FREE_KINDS:
            dap = KHONG_AP_DUNG
        elif not (w and is_exact_number(mem.get(w))):
            dap = FAIL
            ma.append("ANSWER_NOT_REALIZED")
        else:
            hien = display(mem[w])
            mong = (registered_answers or {}).get(con_tro)
            if mong is not None and hien != mong:
                dap = FAIL
                ma.append("ANSWER_MISMATCH")
            elif vat is not None and (vat.get(w) or {}).get("value") != hien:
                dap = FAIL
                ma.append("ANSWER_NOT_IN_SCENE_READOUT")
            else:
                dap = PASS if mong is not None else CHUA_KIEM_CHUNG

        khop = i < len(goc) and CG.dau_van_nghia_vu(goc[i]) == CG.dau_van_nghia_vu(ob)
        dong.append({
            "obligation_pointer": con_tro if khop else None,
            "pointer_status": "EXACT" if khop else "AMBIGUOUS",
            "operation_kind": ob.kind if ob.kind in OBLIGATION_KINDS else None,
            "computation_coverage": tinh,
            "construction_coverage": dung,
            "scene_coverage": canh,
            "answer_coverage": dap,
            "required_scene_kind": _ma(yc.get("kind")) if yc else None,
            "required_kind_source": yc["source"] if yc else None,
            "subject_statement_kinds": [_ma(k) for k in kieu_dung],
            "observed_subject_scene_kinds": [_ma(k) for k in quan_sat],
            "observed_scene_count": dem,
            "topology_status": topo,
            "reason_codes": list(dict.fromkeys(ma)),
        })

    co_fail = any(h[k] == FAIL for h in dong
                  for k in ("computation_coverage", "construction_coverage", "scene_coverage", "answer_coverage"))
    # ⚠️ `SECTION_PROVENANCE_NORMALIZATION` (2026-09-20) — cờ này TỪNG OR cả
    # `construction_coverage`, và sau khi có chuẩn hoá xuất xứ thì cách tính ấy
    # NÓI SAI TÊN CỦA CHÍNH NÓ.
    #
    # Một chương trình dựng đúng các đỉnh thiết diện bằng `midpoint` rồi
    # `construct_polygon` có `construction_coverage = FAIL` (nó không gọi
    # `construct_section` — quan sát ĐÚNG, giữ nguyên), nhưng sau chuẩn hoá cảnh
    # MANG vật `section` thật: học sinh NHÌN THẤY thiết diện. Gọi đó là *bỏ sót
    # TRỰC QUAN* là mô tả sai thứ đang xảy ra.
    #
    # Cờ nay chỉ hỏi đúng câu nó mang tên: *cảnh có thiếu vật cần thấy không*.
    # `construction_coverage = FAIL` vẫn vào `SILENT_QUALITY_FAILURE` qua
    # `co_fail`, nên không quan sát nào bị mất.
    #
    # KHÔNG làm yếu phép phát hiện B02: ở đó cảnh KHÔNG có vật `section` nào
    # (`scene_coverage = FAIL`) nên cờ vẫn bật. Fixture B (đa giác đáy, sai chu
    # trình) không qua được `same_section_cycle` ⇒ không chuẩn hoá ⇒ cũng vẫn bật.
    thi_giac = any(h["computation_coverage"] in (PASS, KHONG_AP_DUNG)
                   and h["answer_coverage"] in (PASS, CHUA_KIEM_CHUNG, KHONG_AP_DUNG)
                   and h["scene_coverage"] == FAIL for h in dong)
    return {
        "version": PHIEN_BAN,
        "route_served": route_served,
        "obligation_count": len(dong),
        "requirement_sources": sorted({v["source"] for v in yeu_cau.values()}),
        "SILENT_QUALITY_FAILURE": None if route_served is None else bool(route_served and co_fail),
        "SILENT_VISUAL_OMISSION": None if route_served is None else bool(route_served and thi_giac),
        "obligations": dong,
    }
