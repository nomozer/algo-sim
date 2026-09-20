# -*- coding: utf-8 -*-
"""CHUẨN HOÁ XUẤT XỨ THIẾT DIỆN — `polygon3` chỉ thành `section` khi CÓ BẰNG CHỨNG. 0 mạng.

`SECTION_PROVENANCE_NORMALIZATION` (2026-09-20).

─── HAI TẦNG ĐANG TRẢ LỜI KHÁC NHAU, VÀ CẢ HAI ĐỀU ĐÚNG THEO TIÊU CHÍ RIÊNG ──

`OBLIGATION_KINDS['section_matches'] = {section, polygon3}` và `check_section_matches`
nhận cả một dãy `Vec3` — tầng nghĩa vụ công nhận theo **quan hệ semantic đã kiểm chứng**
(`same_section_cycle` với `cross_section(solid, plane)`).

`_than_hinh_hoc` phân loại theo **lớp runtime**, frontend nhận đúng `type === "section"`
— tầng cảnh công nhận theo **phép dựng**.

Hệ quả: một chương trình dựng đa giác bằng `construct_polygon` với ĐÚNG các đỉnh thiết
diện, kèm nghĩa vụ `section_matches` đã qua C₂, vẫn ra cảnh là `polygon3` ⇒ frontend
không vẽ thiết diện, và visual gate (863c912) từ chối.

─── ĐƯỜNG DUY NHẤT SINH RA `polygon3` LÀ THIẾT DIỆN ────────────────────────

`exec_construct_section` LUÔN trả `Section` — không nhánh nào trả dãy đỉnh trần. Nên
không có `polygon3` nào "sinh trực tiếp từ `construct_section`". Đường duy nhất là:
chương trình dùng `construct_polygon`, và **hợp đồng** có `section_matches(container,
params={solid, plane})`. Bằng chứng plane–solid vì thế nằm ở QUAN HỆ SEMANTIC.

Đó là lý do luật chuẩn hoá phải đọc `contract.obligations`, và vì `build_scene` không
nhận `contract`, chuẩn hoá là một LƯỢT SAU trên cảnh đã dựng.

─── KHÔNG BAO GIỜ DÙNG LÀM BẰNG CHỨNG ──────────────────────────────────────

tên chứa "section"/"thiết diện" · ID có tiền tố · có ba đỉnh · đồng phẳng · đáp số diện
tích đúng · vật tự khai là thiết diện mà không có nguồn plane–solid.
"""

from __future__ import annotations

import json

import pytest

from app.ai import gemini
from app.simulation.semantic_program import section_provenance as SP
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile
from tests.test_photo_problem_live_runner import (  # noqa: F401 — fixture `de` dùng qua tên
    CA_P1,
    RNB,
    de,
    kho,
)
from tests.test_photo_problem_semantic_integration import R

P1 = RNB.doc_raw_theo_thu_tu(CA_P1)
P1_ANALYZE = P1["semantic_analyze"][0]
P1_PROG = P1["semantic_program"][0]

#: Thiết diện THẬT của p1 — mặt phẳng z = 3 cắt chóp S.ABCD. Dẫn từ kernel, không chép tay.
DINH_THIET_DIEN = [["0", "0", "3"], ["3", "0", "3"], ["3", "3", "3"], ["0", "3", "3"]]

TEN_THO = ("S.ABCD", "alpha_plane", "area_T", "the_volume_sabcd", "dist_S_BD")


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


# ══ dựng fixture ════════════════════════════════════════════════════════════
def _hd(de) -> RequestContract:
    return build_request_contract(json.loads(P1_ANALYZE), problem_text=de["C01"], domain=DOMAIN_HINH_HOC)


def _spec(prog: dict | None = None):
    d = prog if prog is not None else json.loads(P1_PROG)
    v = V.validate_semantic_program(d)
    assert v.ok, v.error
    return v.spec


def _prog_polygon_thay_section(alias: int = 0) -> dict:
    """p1 nhưng `T` dựng bằng `construct_polygon` trên bốn điểm thiết diện THẬT.

    Đây là `DERIVED_STRUCTURAL_FIXTURE`: chương trình p1 đã được nhận, đổi ĐÚNG một
    câu lệnh. `alias` > 0 thì thêm bấy nhiêu cấp `assign`.
    """
    d = json.loads(P1_PROG)
    ten_dinh = [f"Q{i + 1}" for i in range(4)]
    # Đỉnh phải DẪN XUẤT, không được KHAI: cổng grounding từ chối một điểm có
    # `initial_value` mà không `source_fact_id` (đã đo — và nó đúng). Thiết diện
    # z = 3 của chóp S(0,0,6) trên đáy ABCD chính là trung điểm SA · SB · SC · SD,
    # nên `midpoint` dựng được chúng mà không bịa một toạ độ nào.
    khai = [{"kind": "construct_point", "target_var": t,
             "expr": {"kind": "midpoint", "a": "S", "b": p}}
            for t, p in zip(ten_dinh, ("A", "B", "C", "D"))]
    moi = []
    for s in d["statements"]:
        if s.get("target_var") == "T":
            moi.extend(khai)
            moi.append({"kind": "construct_polygon", "target_var": "T",
                        "vertices": ten_dinh, "label": "Đa giác (T)"})
            for i in range(alias):
                moi.append({"kind": "assign", "target_var": f"T_bd{i + 1}",
                            "expr": {"kind": "var", "name": "T" if i == 0 else f"T_bd{i}"}})
        else:
            moi.append(s)
    d["statements"] = moi
    kieu = {"T": "polygon3", **{t: "point3" for t in ten_dinh}}
    for i in range(alias):
        kieu[f"T_bd{i + 1}"] = "polygon3"
    d["memory_declarations"] = [
        ({**m, "type": kieu[m["name"]]} if m["name"] in kieu else m)
        for m in d["memory_declarations"]
    ] + [{"name": n, "type": t} for n, t in kieu.items()
         if n not in {m["name"] for m in d["memory_declarations"]}]
    return d


def _hd_them_section_matches(hd: RequestContract, container: str = "T",
                             solid: str = "S.ABCD", plane: str = "alpha_plane") -> RequestContract:
    ob = Obligation(kind="section_matches", container=container,
                    params={"witness": None, "solid": solid, "plane": plane})
    return hd.model_copy(update={"obligations": hd.obligations + (ob,)})


def _canh_va_bo_nho(spec, hd):
    """Cảnh THÔ — `build_scene3d` thuần, CHƯA qua chuẩn hoá.

    ⚠️ Cố ý KHÔNG dùng `_dung_scene3d`: hàm ấy nay đã gọi normalizer, nên lấy nền
    "trước chuẩn hoá" từ nó là lấy một nền ĐÃ chuẩn hoá — và mọi test so trước/sau
    sẽ so hai thứ giống nhau mà vẫn xanh.
    """
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import build_simulation_state

    ket = SemanticProgramInterpreter().execute(spec)
    return build_scene3d(build_simulation_state(spec, ket, hd)), dict(ket.final_memory)


def _vat(canh: dict, oid: str) -> dict | None:
    return next((o for o in (canh or {}).get("objects", ()) if o.get("id") == oid), None)


def _chuan_hoa(canh, bo_nho, hd):
    return SP.normalize_section_provenance(canh, bo_nho, hd)


# ══ A · nền: phép giao plane–solid đang cho `polygon3` CHƯA chuẩn hoá ═══════
def test_A_nen__plane_solid_cho_polygon3_chua_duoc_chuan_hoa(de):
    """CỬA SỔ CHỨNG cho cả tệp: fixture đúng là đa giác trùng thiết diện thật."""
    hd, spec = _hd(de), _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    t = _vat(canh, "T")
    assert t is not None and t["type"] == "polygon3", "fixture hỏng: T phải là polygon3"
    assert [list(v) for v in t["vertices"]] == DINH_THIET_DIEN


def test_A_chuan_hoa_thanh_canonical_section_khi_co_section_matches(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    t = _vat(kq.scene, "T")
    assert t["type"] == SP.CANONICAL_SECTION_KIND == "section"
    assert [list(v) for v in t["polygon"]] == DINH_THIET_DIEN
    assert t["closed"] is True


def test_A_chuan_hoa_GIU_provenance_va_topology(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)
    truoc = _vat(canh, "T")

    t = _vat(_chuan_hoa(canh, bo_nho, hd).scene, "T")

    assert t["producer"] == truoc["producer"], "producer bị đổi — mất xuất xứ phép dựng"
    assert t["depends"] == truoc["depends"]
    assert t["origin"] == truoc["origin"]


def test_A_chuan_hoa_KHONG_dung_toi_final_memory_hay_dap_so(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)
    truoc = json.dumps({k: str(v) for k, v in bo_nho.items()}, sort_keys=True)

    _chuan_hoa(canh, bo_nho, hd)

    assert json.dumps({k: str(v) for k, v in bo_nho.items()}, sort_keys=True) == truoc


def test_A_KHONG_sua_canh_dau_vao(de):
    """Kiến trúc ưu tiên kết quả immutable — chuẩn hoá trả cảnh MỚI."""
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)
    truoc = json.dumps(canh, sort_keys=True, ensure_ascii=False)

    _chuan_hoa(canh, bo_nho, hd)

    assert json.dumps(canh, sort_keys=True, ensure_ascii=False) == truoc


# ══ B · đa giác THƯỜNG không được promote ══════════════════════════════════
def test_B_da_giac_thuong_KHONG_bi_promote(de):
    """`ABCD_base` là đáy hình vuông — không nghĩa vụ nào nói nó là thiết diện."""
    hd, spec = _hd(de), _spec()
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    day = _vat(kq.scene, "ABCD_base")
    assert day["type"] == "polygon3"
    assert "polygon" not in day


def test_B_da_giac_KHAC_khong_bi_keo_theo_khi_CO_mot_thiet_dien_hop_le(de):
    """⚠️ Test này sinh ra vì PHÉP TIÊM G2 KHÔNG BẮT ĐƯỢC GÌ.

    `test_B_da_giac_thuong_KHONG_bi_promote` chạy trên hợp đồng KHÔNG có
    `section_matches`, nên nhánh chuẩn hoá chưa từng chạy — nó chứng minh
    "không làm gì khi không có gì để làm", không chứng minh "không kéo theo vật
    khác". Ở đây hợp đồng CÓ một thiết diện hợp lệ, và `ABCD_base` (đáy hình
    vuông, z = 0) phải đứng yên."""
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert _vat(kq.scene, "T")["type"] == "section", "nền: T phải được chuẩn hoá"
    day = _vat(kq.scene, "ABCD_base")
    assert day["type"] == "polygon3", "đa giác đáy bị kéo theo — chuẩn hoá quá tay"
    assert "section_source" not in day
    assert kq.normalized_count == 1


def test_B_KHONG_co_section_matches_thi_polygon3_giu_nguyen(de):
    """Hợp đồng p1 gốc KHÔNG có `section_matches` ⇒ không gì để chuẩn hoá."""
    hd, spec = _hd(de), _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert _vat(kq.scene, "T")["type"] == "polygon3"
    assert kq.normalized_count == 0


# ══ C · tự khai `section` mà thiếu nguồn ═══════════════════════════════════
def test_C_doi_ten_thanh_section_ma_thieu_provenance_van_bi_TU_CHOI(de):
    """Vật MANG loại `section` nhưng không nghĩa vụ nào có plane+solid cho nó."""
    hd, spec = _hd(de), _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)
    gia = {"objects": [{**o, "type": "section", "polygon": o.get("vertices")}
                       if o["id"] == "T" else o for o in canh["objects"]]}

    kq = _chuan_hoa(gia, bo_nho, hd)
    hang = kq.hang_theo_id.get("T")

    assert hang is None or hang.reason_code != "NORMALIZED_FROM_PLANE_SOLID_INTERSECTION"
    assert kq.normalized_count == 0


# ══ D · E · thiếu plane / thiếu solid ══════════════════════════════════════
def test_D_co_plane_thieu_solid__KHONG_chuan_hoa(de):
    hd = _hd_them_section_matches(_hd(de), solid="KHONG_TON_TAI")
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert _vat(kq.scene, "T")["type"] == "polygon3"
    assert kq.hang_theo_id["T"].reason_code == "SOURCE_SOLID_UNRESOLVED"


def test_E_co_solid_thieu_plane__KHONG_chuan_hoa(de):
    hd = _hd_them_section_matches(_hd(de), plane="KHONG_TON_TAI")
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert _vat(kq.scene, "T")["type"] == "polygon3"
    assert kq.hang_theo_id["T"].reason_code == "SOURCE_PLANE_UNRESOLVED"


# ══ F · G · bí danh ════════════════════════════════════════════════════════
def test_F_alias_MOT_cap_giu_provenance(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section(alias=1))
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    for oid in ("T", "T_bd1"):
        v = _vat(kq.scene, oid)
        assert v is not None and v["type"] == "section", f"{oid} mất thiết diện"


def test_G_alias_NHIEU_cap_giu_provenance(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section(alias=3))
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    for oid in ("T", "T_bd1", "T_bd2", "T_bd3"):
        v = _vat(kq.scene, oid)
        assert v is not None and v["type"] == "section", f"{oid} mất thiết diện"


def test_G_nghia_vu_tro_vao_BI_DANH_van_chuan_hoa_duoc(de):
    hd = _hd_them_section_matches(_hd(de), container="T_bd2")
    spec = _spec(_prog_polygon_thay_section(alias=3))
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert _vat(kq.scene, "T_bd2")["type"] == "section"


# ══ H · mâu thuẫn ══════════════════════════════════════════════════════════
def test_H_hai_nghia_vu_mau_thuan_nguon__KHONG_doan(de):
    """Cùng chủ thể, hai `section_matches` khai HAI mặt phẳng khác nhau."""
    hd = _hd_them_section_matches(_hd(de))
    hd = hd.model_copy(update={"obligations": hd.obligations + (
        Obligation(kind="section_matches", container="T",
                   params={"witness": None, "solid": "S.ABCD", "plane": "KHAC"}),)})
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert _vat(kq.scene, "T")["type"] == "polygon3"
    assert kq.hang_theo_id["T"].reason_code == "AMBIGUOUS_SECTION_SOURCE"


# ══ I · J · tất định ═══════════════════════════════════════════════════════
def test_I_chuan_hoa_HAI_LAN_cho_canonical_JSON_trung_byte(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    mot = _chuan_hoa(canh, bo_nho, hd).scene
    hai = _chuan_hoa(mot, bo_nho, hd).scene

    def canon(o):
        return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    assert canon(mot) == canon(hai), "chuẩn hoá KHÔNG idempotent"


def test_J_thu_tu_nghia_vu_khong_doi_ket_qua(de):
    hd = _hd_them_section_matches(_hd(de))
    dao = hd.model_copy(update={"obligations": tuple(reversed(hd.obligations))})
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    def canon(s):
        return json.dumps(s, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    assert canon(_chuan_hoa(canh, bo_nho, hd).scene) == canon(_chuan_hoa(canh, bo_nho, dao).scene)


# ══ K · L · topology ═══════════════════════════════════════════════════════
def test_K_section_hop_le_duoc_phuc_vu(de):
    """Biên khép kín, ≥ 3 đỉnh phân biệt, đồng phẳng."""
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    t = _vat(_chuan_hoa(canh, bo_nho, hd).scene, "T")

    assert t["closed"] is True
    assert len({tuple(v) for v in t["polygon"]}) >= 3


def test_L_da_giac_KHONG_trung_chu_trinh_thiet_dien__CYCLE_MISMATCH(de):
    """Đa giác đáy (`ABCD_base`) không phải thiết diện của z = 3."""
    hd = _hd_them_section_matches(_hd(de), container="ABCD_base")
    spec = _spec()
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert _vat(kq.scene, "ABCD_base")["type"] == "polygon3"
    assert kq.hang_theo_id["ABCD_base"].reason_code == "CYCLE_MISMATCH"


# ══ M · N · B02 derived ════════════════════════════════════════════════════
def test_M_B02_derived_co_section_THAT_va_het_silent_visual_omission(de):
    """Sau chuẩn hoá, cảnh có vật `section` thật ⇒ visual gate CHO QUA."""
    from app.simulation.semantic_program import visual_obligations as VO

    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    truoc = VO.check_visual_obligations(hd, canh, {})
    assert truoc.verdict != "COVERED", "nền: chưa chuẩn hoá thì gate phải từ chối"

    sau_canh = _chuan_hoa(canh, bo_nho, hd).scene
    sau = VO.check_visual_obligations(hd, sau_canh, {})

    assert sau.verdict == "COVERED"
    assert sum(1 for o in sau_canh["objects"] if o["type"] == "section") >= 1


def test_N_polygon3_gia_lam_thiet_dien_VAN_bi_tu_choi(de):
    """Không có bằng chứng plane–solid ⇒ chuẩn hoá không xảy ra ⇒ gate vẫn từ chối."""
    from app.simulation.semantic_program import visual_obligations as VO

    hd = _hd_them_section_matches(_hd(de), solid="KHONG_TON_TAI")
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    sau = _chuan_hoa(canh, bo_nho, hd).scene

    assert VO.check_visual_obligations(hd, sau, {}).verdict != "COVERED"


# ══ O · parity ca hợp lệ ═══════════════════════════════════════════════════
def test_O_p1_nguyen_ven_KHONG_bi_chuan_hoa_dung_toi(de):
    """`construct_section` đã cho `section` — chuẩn hoá phải là no-op trùng byte."""
    hd, spec = _hd(de), _spec()
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    def canon(s):
        return json.dumps(s, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    kq = _chuan_hoa(canh, bo_nho, hd)

    assert canon(kq.scene) == canon(canh), "ca hợp lệ bị đổi"
    assert kq.normalized_count == 0


def test_O_route_decision_va_final_memory_khong_doi(de):
    hd, spec = _hd(de), _spec()
    o = verify_and_compile(hd, spec)

    assert (o.stage_reached, o.servable) == ("served", True)


# ══ P · ĐƯỜNG CHẠY THẬT ════════════════════════════════════════════════════
def test_P_normalizer_DUOC_GOI_trong_pipeline(de):
    """Quét AST — `_dung_scene3d` phải gọi normalizer SAU `build_scene3d`."""
    import ast
    import inspect

    from app.ai import pipeline as P

    than = inspect.getsource(P._dung_scene3d)
    ten = {getattr(g.func, "id", None) or getattr(g.func, "attr", None)
           for g in ast.walk(ast.parse(than.strip())) if isinstance(g, ast.Call)}
    assert "normalize_section_provenance" in ten, "pipeline KHÔNG gọi normalizer"
    assert than.index("build_scene3d") < than.index("normalize_section_provenance")


def test_P_run_pipeline_THAT_phuc_vu_ca_da_chuan_hoa(monkeypatch, de):
    """END-TO-END, 0 mạng: chương trình dùng `construct_polygon` + hợp đồng có
    `section_matches` ⇒ cảnh ra `section` và route phục vụ."""
    import asyncio

    from app.ai import pipeline as P

    raw = dict(RNB.doc_raw_theo_thu_tu(CA_P1))
    ana = json.loads(raw["semantic_analyze"][0])
    ana.setdefault("obligations", []).append(
        {"kind": "section_matches", "container": "T", "witness": None,
         "solid": "S.ABCD", "plane": "alpha_plane"})
    raw["semantic_analyze"] = [json.dumps(ana, ensure_ascii=False)]
    raw["semantic_program"] = [json.dumps(_prog_polygon_thay_section(), ensure_ascii=False)]

    monkeypatch.setattr(P, "call_gemini", R.ProviderPhatLaiTheoThuTu(raw))
    with R.NetworkGuard() as g:
        env = asyncio.run(P.run_pipeline(de["C01"], "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))

    assert list(g.attempts) == [], "lượt này phải 0 request mạng"
    assert env["status"] == "ok", (env.get("stage_reached"), env.get("error_code"))
    sec = [o for o in env["scene3d"]["objects"] if o["type"] == "section"]
    assert len(sec) >= 1, "đường chạy thật KHÔNG sinh được vật section"


def test_P_run_pipeline_ca_p1_goc_van_phuc_vu(monkeypatch, de):
    """Cửa sổ chứng cho test trên: p1 nguyên vẹn vẫn `ok`."""
    import asyncio

    from app.ai import pipeline as P

    monkeypatch.setattr(P, "call_gemini", R.ProviderPhatLaiTheoThuTu(R.doc_raw_theo_thu_tu(CA_P1)))
    with R.NetworkGuard() as g:
        env = asyncio.run(P.run_pipeline(de["C01"], "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))

    assert list(g.attempts) == []
    assert env["status"] == "ok", (env.get("stage_reached"), env.get("error_code"))


# ══ Q · R · không rò rỉ, không mạng ════════════════════════════════════════
def _moi_chuoi(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _moi_chuoi(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _moi_chuoi(v)


def test_Q_chan_doan_KHONG_cho_raw_program_scene_hay_ten_tho(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    d = SP.chan_doan_chuan_hoa(_chuan_hoa(canh, bo_nho, hd))
    chuoi = set(_moi_chuoi(d))

    assert not (chuoi & set(TEN_THO)), "tên thô rò rỉ"
    for cam in ("statements", "objects", "polygon", "vertices", "xyz", "problem_text", "input", "msg", "ctx"):
        assert cam not in chuoi, f"khoá cấm rò rỉ: {cam}"


def test_Q_cua_so_chung__phep_do_ro_ri_CO_do_duoc(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)
    d = SP.chan_doan_chuan_hoa(_chuan_hoa(canh, bo_nho, hd))
    d["obligations"][0]["reason_code"] = "S.ABCD"  # tiêm

    assert set(_moi_chuoi(d)) & set(TEN_THO), "phép đo mù"


def test_Q_chan_doan_chi_dung_TU_VUNG_DONG(de):
    hd = _hd_them_section_matches(_hd(de))
    spec = _spec(_prog_polygon_thay_section())
    canh, bo_nho = _canh_va_bo_nho(spec, hd)

    d = SP.chan_doan_chuan_hoa(_chuan_hoa(canh, bo_nho, hd))

    assert d["normalization_version"] == SP.NORMALIZATION_VERSION
    for h in d["obligations"]:
        assert h["status"] in SP.TRANG_THAI
        assert h["reason_code"] in SP.MA_LY_DO
