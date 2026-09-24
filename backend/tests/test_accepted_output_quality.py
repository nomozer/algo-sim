# -*- coding: utf-8 -*-
"""CHẤT LƯỢNG ĐẦU RA ĐƯỢC NHẬN — bốn lớp phủ: phép tính · phép dựng · cảnh · đáp số. 0 mạng.

`SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS` (2026-09-15). Lượt follow-up B02 được route PHỤC VỤ với final_memory
và đáp số đúng 3/3 nhưng cảnh không có vật `section` (`SILENT_QUALITY_FAILURE`). Output lượt ấy không lưu ⇒
`HISTORICAL_LIVE_OUTPUT_CAUSE = NOT_RECOVERABLE`; test ở đây KHÔNG dựng lại nó.

Đo được trên START_HEAD (trước bộ chẩn đoán), bằng chương trình p1 đóng băng và biến thể nhỏ:
- đa giác vuông ở đáy thay thiết diện ⇒ route `served`, đáp số 72 · 9 · 3√6 đúng, cảnh không có `section`;
- `polygon3` cùng toạ độ thiết diện ⇒ `served`; thêm cả nghĩa vụ `section_matches` vào hợp đồng vẫn `served`
  (chính sách nghĩa vụ nhận `polygon3` là thiết diện), trong khi cảnh phát `polygon3`;
- thiết diện của KHỐI KHÁC ⇒ `served` với diện tích `9/2`.

Bộ chẩn đoán CHỈ QUAN SÁT: không đổi route, envelope, request hay phản hồi sửa.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.ai import gemini, pipeline
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.coverage_gate import check_structural_coverage
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.route import verify_and_compile
from tests.test_photo_problem_live_runner import (  # noqa: F401 — fixture `de`, `kho` dùng qua tên
    CA_P1,
    R,
    RNB,
    _chay,
    _json,
    _kich_ban,
    de,
    kho,
)

GOC = Path(__file__).resolve().parents[2]
MANIFEST = GOC / "docs/evaluation/geometry/photo-problem-to-scene/multicase-synthesis-token-benchmark/MULTICASE_BENCHMARK_MANIFEST.json"
CASES = {c["case_id"]: c for c in json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]}
P1 = RNB.doc_raw_theo_thu_tu(CA_P1)
P0 = json.loads(P1["semantic_program"][0])
TEP_CL = "C01_ACCEPTED_OUTPUT_QUALITY.json"
BI_MAT = "TOKEN-QUALITY-SECRET-555"
KHOA_DONG = {"obligation_pointer", "pointer_status", "operation_kind", "computation_coverage", "construction_coverage",
             "scene_coverage", "answer_coverage", "required_scene_kind", "required_kind_source", "subject_statement_kinds",
             "observed_subject_scene_kinds", "observed_scene_count", "topology_status", "reason_codes"}


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


@pytest.fixture
def AQ():
    import accepted_output_quality as m  # noqa: PLC0415 — nạp trễ: test phải ĐỎ từng ca trước khi module tồn tại

    return m


# ══ dữ liệu đóng băng ══════════════════════════════════════════════════════════
def _hd(de):
    return build_request_contract(json.loads(P1["semantic_analyze"][0]), problem_text=de["C01"], domain=DOMAIN_HINH_HOC)


def _con_tro_kind(hd, kind: str) -> str:
    (i,) = [i for i, o in enumerate(hd.obligations) if o.kind == kind]
    return f"/obligations/{i}"


def _yeu_cau_thiet_dien(hd, ca="B02", kind="area"):
    """Yêu cầu hình ĐÃ ĐĂNG KÝ (manifest benchmark): chủ thể của nghĩa vụ đo `kind` phải là một thiết diện."""
    exp = CASES[ca]["expected"]
    sec = next(t for t in exp["topology"] if t["check"] == "section_polygon")
    mp = next(r for r in exp["relations"] if r["check"] == "plane")
    return [{"obligation_pointer": _con_tro_kind(hd, kind), "required_scene_kind": "section",
             "reference": {"vertices": sec["vertices"], "plane": {"normal": mp["normal"], "c": mp["c"]}}}]


def _dap_so(hd, ca="B02"):
    theo = {s["kind"]: s["display"] for s in CASES[ca]["expected"]["final_memory_by_obligation"]}
    return {f"/obligations/{i}": theo[o.kind] for i, o in enumerate(hd.obligations) if o.kind in theo}


def _vt(d, t):
    return next(i for i, s in enumerate(d["statements"]) if s.get("target_var") == t)


def _trung_diem(ds):
    return [{"kind": "construct_point", "target_var": t, "expr": {"kind": "midpoint", "a": a, "b": b}} for t, a, b in ds]


def _polygon_thay_thiet_dien(diem, dinh):
    def f(d):
        i = _vt(d, "T")
        d["statements"][i:i + 1] = _trung_diem(diem) + [{"kind": "construct_polygon", "target_var": "T", "vertices": dinh}]
        for x in d["memory_declarations"]:
            if x["name"] == "T":
                x["type"] = "polygon3"
    return f


def _thiet_dien_khoi_khac(d):
    d["statements"].insert(_vt(d, "S.ABCD") + 1, {"kind": "construct_solid", "target_var": "S_ABC", "vertices": ["S", "A", "B", "C"],
                                                  "faces": [["A", "B", "C"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "A"]]})
    d["statements"][_vt(d, "T")]["solid"] = "S_ABC"


def _bo_witness_dien_tich(d):
    d["statements"] = [s for s in d["statements"] if s.get("target_var") != "area_T"]


def _hang_so_khong_dung_hinh(d):
    d["statements"] = [s for s in d["statements"] if s.get("target_var") != "T"]
    d["memory_declarations"] = [x for x in d["memory_declarations"] if x["name"] != "T"]
    d["statements"][_vt(d, "area_T")]["expr"] = {"kind": "literal", "value": 9}


def _hai_thiet_dien(d):
    i = _vt(d, "T")
    d["statements"][i + 1:i + 1] = _trung_diem([("N1", "S", "A"), ("N2", "S", "B"), ("N3", "A", "C")]) + [
        {"kind": "construct_plane", "target_var": "P2", "through": ["N1", "N2", "N3"]},
        {"kind": "construct_section", "target_var": "T2", "solid": "S.ABCD", "plane": "P2"}]


FIX = {
    "A": None,
    "B": _polygon_thay_thiet_dien([("Q1", "A", "B"), ("Q2", "A", "C"), ("Q3", "A", "D")], ["A", "Q1", "Q2", "Q3"]),
    "C": _polygon_thay_thiet_dien([("M1", "S", "A"), ("M2", "S", "B"), ("M3", "S", "C"), ("M4", "S", "D")], ["M1", "M2", "M3", "M4"]),
    "D": _thiet_dien_khoi_khac,
    "F": _bo_witness_dien_tich,
    "G": _hang_so_khong_dung_hinh,
    "I": _hai_thiet_dien,
}


def _chuong_trinh(ten):
    d = copy.deepcopy(P0)
    if FIX[ten]:
        FIX[ten](d)
    return d


def _chay_offline(hd, d):
    v = V.validate_semantic_program(copy.deepcopy(d))
    assert v.ok, v.error
    o = verify_and_compile(hd, v.spec)
    mem = o.final_memory if o.final_memory is not None else SemanticProgramInterpreter().execute(v.spec).final_memory
    return v.spec, o, mem, pipeline._dung_scene3d(v.spec, hd)


def _chan_doan(AQ, hd, ten, *, canh_sua=None, yeu_cau="dang_ky", dap_so=True):
    spec, o, mem, canh = _chay_offline(hd, _chuong_trinh(ten))
    if canh_sua:
        canh = copy.deepcopy(canh)
        canh_sua(canh)
    kq = AQ.chan_doan_chat_luong_dau_ra(
        hd, spec, mem, canh, route_served=o.servable,
        visual_requirements=_yeu_cau_thiet_dien(hd) if yeu_cau == "dang_ky" else None,
        registered_answers=_dap_so(hd) if dap_so else None)
    return o, kq


def _hang(kq, con_tro):
    (h,) = [h for h in kq["obligations"] if h["obligation_pointer"] == con_tro]
    return h


def _lop(h):
    return (h["computation_coverage"], h["construction_coverage"], h["scene_coverage"], h["answer_coverage"])


def _gom_chuoi(o, ra=None):
    ra = [] if ra is None else ra
    if isinstance(o, dict):
        [_gom_chuoi(v, ra) for v in o.values()]
    elif isinstance(o, list):
        [_gom_chuoi(v, ra) for v in o]
    elif isinstance(o, str):
        ra.append(o)
    return ra


# ══ A · đủ bốn lớp ═════════════════════════════════════════════════════════════
def test_A_chuong_trinh_du__bon_lop_PASS__khong_that_bai_im_lang(AQ, de):
    hd = _hd(de)
    o, kq = _chan_doan(AQ, hd, "A")
    assert o.servable and kq["version"] == "accepted-output-quality/1"
    assert all(set(h) == KHOA_DONG for h in kq["obligations"])
    assert all(_lop(h) == ("PASS", "PASS", "PASS", "PASS") for h in kq["obligations"]), kq
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert (h["required_scene_kind"], h["required_kind_source"], h["subject_statement_kinds"], h["observed_scene_count"],
            h["topology_status"], h["reason_codes"]) == ("section", "REGISTERED_REFERENCE", ["construct_section"], 1, "PASS", [])
    assert (kq["SILENT_QUALITY_FAILURE"], kq["SILENT_VISUAL_OMISSION"]) == (False, False)


# ══ B · đáp số đúng, không thiết diện ═════════════════════════════════════════
def test_B_dap_so_dung_nhung_thieu_thiet_dien__route_VAN_phuc_vu__chan_doan_bat_that_bai_im_lang(AQ, de):
    hd = _hd(de)
    o, kq = _chan_doan(AQ, hd, "B")
    spec = _chay_offline(hd, _chuong_trinh("B"))[0]
    assert check_structural_coverage(hd, spec).ok and o.servable  # cửa sổ chứng: hành vi hiện tại KHÔNG đổi
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert _lop(h) == ("PASS", "FAIL", "FAIL", "PASS")
    assert {"MISSING_SECTION_CONSTRUCTION", "MISSING_SECTION_SCENE_OBJECT", "POLYGON_WITHOUT_SECTION_PROVENANCE"} <= set(h["reason_codes"])
    assert (h["observed_scene_count"], h["observed_subject_scene_kinds"]) == (0, ["polygon3"])
    assert (kq["SILENT_QUALITY_FAILURE"], kq["SILENT_VISUAL_OMISSION"]) == (True, True)


# ══ C · đa giác cùng toạ độ ════════════════════════════════════════════════════
def test_C_polygon_cung_toa_do_KHONG_duoc_tinh_la_thiet_dien__ke_ca_khi_hop_dong_co_section_matches(AQ, de):
    hd = _hd(de)
    o, kq = _chan_doan(AQ, hd, "C")
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert o.servable and _lop(h)[1:3] == ("FAIL", "FAIL") and "POLYGON_WITHOUT_SECTION_PROVENANCE" in h["reason_codes"]
    # ⚠️ ĐÁP ÁN CŨ CHÍNH LÀ LỖI (`SECTION_PROVENANCE_NORMALIZATION`, 2026-09-20).
    #
    # Bản trước khẳng định: có `section_matches` thì cảnh VẪN `FAIL` và VẪN
    # `SILENT_VISUAL_OMISSION = True`. Đó đúng là bệnh wave này chữa, không phải
    # một bất biến cần giữ: đa giác ở đây dựng từ trung điểm SA·SB·SC·SD, tức
    # ĐÚNG thiết diện z = 3, và nghĩa vụ `section_matches` khai đủ `solid`+`plane`
    # giải được. Kernel dựng lại `cross_section` và chu trình KHỚP ⇒ đây là thiết
    # diện thật, và giữ nó ở `polygon3` mới là thứ làm frontend không vẽ được.
    #
    # Nửa đầu test (không có `section_matches`) KHÔNG đổi: không quan hệ nào nói
    # đa giác ấy là thiết diện ⇒ vẫn `POLYGON_WITHOUT_SECTION_PROVENANCE`.
    hd_sm = hd.model_copy(update={"obligations": hd.obligations + (
        Obligation(kind="section_matches", container="T", params={"solid": "S.ABCD", "plane": "alpha_plane"}),)})
    spec, o2, mem, canh = _chay_offline(hd_sm, _chuong_trinh("C"))
    assert o2.servable
    assert next(x for x in canh["objects"] if x["id"] == "T")["type"] == "section", \
        "chuẩn hoá xuất xứ phải biến đa giác ĐÚNG thiết diện thành `section`"
    kq2 = AQ.chan_doan_chat_luong_dau_ra(hd_sm, spec, mem, canh, route_served=o2.servable)
    for con_tro in (_con_tro_kind(hd_sm, "area"), _con_tro_kind(hd_sm, "section_matches")):
        h2 = _hang(kq2, con_tro)
        assert (h2["required_scene_kind"], h2["required_kind_source"], h2["scene_coverage"]) == ("section", "REQUEST_CONTRACT", "PASS")
        assert "POLYGON_WITHOUT_SECTION_PROVENANCE" not in h2["reason_codes"]
    assert kq2["SILENT_VISUAL_OMISSION"] is False


# ══ D · thiết diện sai tập đỉnh ════════════════════════════════════════════════
def test_D_thiet_dien_sai_tap_dinh__topology_FAIL__dap_so_FAIL(AQ, de):
    hd = _hd(de)
    o, kq = _chan_doan(AQ, hd, "D")
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert o.servable and _lop(h) == ("PASS", "PASS", "FAIL", "FAIL")
    assert h["topology_status"] == "FAIL" and "SECTION_VERTEX_SET_MISMATCH" in h["reason_codes"]
    assert "SECTION_PLANE_MISMATCH" not in h["reason_codes"] and "ANSWER_MISMATCH" in h["reason_codes"]


# ══ E · đúng đỉnh, sai mặt phẳng ═══════════════════════════════════════════════
def _sai_mat_phang(canh):
    t = next(x for x in canh["objects"] if x["id"] == "T")
    mp = next(x for x in canh["objects"] if x["id"] in t["depends"] and x["type"] == "plane3")
    mp["normal"] = ["1", "0", "0"]


def test_E_thiet_dien_dung_dinh_nhung_mat_phang_nguon_SAI__topology_FAIL(AQ, de):
    hd = _hd(de)
    _o, kq = _chan_doan(AQ, hd, "A", canh_sua=_sai_mat_phang)
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert (h["scene_coverage"], h["topology_status"]) == ("FAIL", "FAIL")
    assert "SECTION_PLANE_MISMATCH" in h["reason_codes"] and "SECTION_VERTEX_SET_MISMATCH" not in h["reason_codes"]


# ══ F · thiết diện đúng, thiếu witness ════════════════════════════════════════
def test_F_thiet_dien_dung_nhung_thieu_witness__computation_FAIL(AQ, de):
    hd = _hd(de)
    o, kq = _chan_doan(AQ, hd, "F")
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert not o.servable and o.stage_reached == "structural_coverage"
    assert _lop(h) == ("FAIL", "PASS", "PASS", "FAIL")
    assert {"WITNESS_WITHOUT_PRODUCER", "ANSWER_NOT_REALIZED"} <= set(h["reason_codes"])
    assert kq["SILENT_QUALITY_FAILURE"] is False


# ══ G · witness hằng số, không phép dựng ═══════════════════════════════════════
def test_G_witness_ghi_truc_tiep_KHONG_thay_the_phep_tinh_phep_dung_hay_canh(AQ, de):
    hd = _hd(de)
    o, kq = _chan_doan(AQ, hd, "G")
    h = _hang(kq, _con_tro_kind(hd, "area"))
    _spec, _o, mem, canh = _chay_offline(hd, _chuong_trinh("G"))
    # Cửa sổ chứng: giá trị ghi thẳng TRÙNG đáp số đăng ký trong final_memory — nhưng cảnh không phát readout cho nó
    # (đo được; kỳ vọng ban đầu `answer = PASS` là giả định sai của test, sửa trước commit).
    assert mem["area_T"] == 9 and "area_T" not in {x["id"] for x in canh["objects"] if x["type"] == "quantity"}
    assert not o.servable
    assert _lop(h) == ("FAIL", "FAIL", "FAIL", "FAIL")  # đáp số trùng giá trị mà không lớp nào được nâng lên
    assert {"WITNESS_NOT_MEASURED", "MISSING_SECTION_CONSTRUCTION", "MISSING_SECTION_SCENE_OBJECT",
            "ANSWER_NOT_IN_SCENE_READOUT"} <= set(h["reason_codes"])


# ══ H · tầng cảnh làm rơi thiết diện ═══════════════════════════════════════════
def _roi_thiet_dien(canh):
    canh["objects"] = [x for x in canh["objects"] if x["id"] != "T"]


def test_H_canh_lam_roi_thiet_dien__phep_dung_PASS_canh_FAIL__phan_lop_dung(AQ, de):
    hd = _hd(de)
    _o, kq = _chan_doan(AQ, hd, "A", canh_sua=_roi_thiet_dien)
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert _lop(h) == ("PASS", "PASS", "FAIL", "PASS")
    assert {"MISSING_SECTION_SCENE_OBJECT", "CONSTRUCTED_SUBJECT_ABSENT_FROM_SCENE"} <= set(h["reason_codes"])


def test_J2_vat_mang_loai_section_nhung_KHONG_khep_kin__topology_FAIL(AQ, de):
    hd = _hd(de)

    def ho(canh):
        t = next(x for x in canh["objects"] if x["id"] == "T")
        t["polygon"], t["closed"] = t["polygon"][:2], False

    _o, kq = _chan_doan(AQ, hd, "A", canh_sua=ho)
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert (h["scene_coverage"], h["topology_status"]) == ("FAIL", "FAIL") and "SECTION_NOT_CLOSED" in h["reason_codes"]


# ══ I · nhiều thiết diện, thứ tự xác định ══════════════════════════════════════
def test_I_nhieu_thiet_dien__chan_doan_theo_DUNG_chu_the__thu_tu_xac_dinh(AQ, de):
    hd = _hd(de)
    o, kq = _chan_doan(AQ, hd, "I")
    h = _hang(kq, _con_tro_kind(hd, "area"))
    assert o.servable and _lop(h) == ("PASS", "PASS", "PASS", "PASS") and h["observed_scene_count"] == 2
    assert [x["obligation_pointer"] for x in kq["obligations"]] == [f"/obligations/{i}" for i in range(len(hd.obligations))]
    _o2, kq2 = _chan_doan(AQ, hd, "I")
    assert json.dumps(kq, sort_keys=True) == json.dumps(kq2, sort_keys=True)


# ══ J · con trỏ ════════════════════════════════════════════════════════════════
def test_J_con_tro_tro_DUNG_nghia_vu_trong_RequestContract_nguon(AQ, de):
    hd = _hd(de)
    _o, kq = _chan_doan(AQ, hd, "A")
    goc = hd.model_dump(mode="json")["obligations"]
    for h in kq["obligations"]:
        i = int(h["obligation_pointer"].rsplit("/", 1)[1])
        assert h["pointer_status"] == "EXACT" and goc[i]["kind"] == h["operation_kind"]


# ══ K · L · riêng tư ═══════════════════════════════════════════════════════════
def test_K_chan_doan_KHONG_chua_gia_tri_chuong_trinh_hay_canh_tho(AQ, de):
    hd = _hd(de)
    for ten in ("A", "B", "D"):
        spec, _o, mem, canh = _chay_offline(hd, _chuong_trinh(ten))
        _o, kq = _chan_doan(AQ, hd, ten)
        ten_ct = {d.name for d in spec.memory_declarations} | {getattr(s, "target_var", None) for s in spec.statements} - {None}
        toa_do = {c for x in canh["objects"] for k in ("xyz", "polygon", "normal", "point") for c in _gom_chuoi(x.get(k))}
        gia_tri = {x.get("value") for x in canh["objects"] if x["type"] == "quantity"}
        chuoi = set(_gom_chuoi(kq))
        assert not chuoi & ten_ct and not chuoi & gia_tri and not chuoi & toa_do and not chuoi & {"72", "9", "3√6"}
        assert chuoi <= AQ.CHUOI_CHO_PHEP | {h["obligation_pointer"] for h in kq["obligations"]}, chuoi - AQ.CHUOI_CHO_PHEP


def test_L_bi_mat_gia_trong_ten_va_gia_tri__KHONG_lot_chan_doan_hay_artifact(AQ, kho, de, monkeypatch):
    hd = _hd(de)
    hd_x = hd.model_copy(update={"obligations": hd.obligations + (Obligation(kind="volume", container=BI_MAT, params={"witness": BI_MAT}),)})
    d = _chuong_trinh("A")
    d["statements"][_vt(d, "T")]["label"] = BI_MAT
    spec, o, mem, canh = _chay_offline(hd_x, d)
    assert BI_MAT in json.dumps(canh, ensure_ascii=False)  # cửa sổ chứng: cảnh THẬT SỰ chở nó
    kq = AQ.chan_doan_chat_luong_dau_ra(hd_x, spec, mem, canh, route_served=o.servable)
    assert BI_MAT not in json.dumps(kq, ensure_ascii=False)
    monkeypatch.setattr(R.BoKhuBiMat, "chuoi", lambda self, s: s)
    r = _chay(kho, "C01", "--accepted-output-quality",
              kich_ban=_kich_ban(de, {("C01", "synthesis"): [json.dumps(d, ensure_ascii=False)]}))
    noi = (r.ra / TEP_CL).read_text(encoding="utf-8")
    assert BI_MAT in (r.ra / "C01_ENVELOPE.json").read_text(encoding="utf-8") and BI_MAT not in noi


# ══ M · N · O · bật/tắt ════════════════════════════════════════════════════════
def _cap(kho, de, synthesis=None, ten="x", bat=False):
    thay = None if synthesis is None else {("C01", "synthesis"): list(synthesis)}
    them = ("--accepted-output-quality",) if bat else ()
    return _chay(kho, "C01", *them, kich_ban=_kich_ban(de, thay), ra=kho.tmp / ten)


def test_M_bat_tat__request_Gemini_GIONG_tung_byte(kho, de):
    tat, bat = _cap(kho, de, ten="tat"), _cap(kho, de, ten="bat", bat=True)
    than = lambda r: [(x["stage"], x["body_sha256"]) for x in _json(r, "PROVIDER_CALLS.json")["records"]]  # noqa: E731
    assert than(tat) == than(bat) and tat.code == bat.code == R.EXIT_PASS
    assert not (tat.ra / TEP_CL).exists() and (bat.ra / TEP_CL).exists()


def test_N_bat_tat__phan_hoi_sua_GIONG_tung_byte(kho, de):
    hong = copy.deepcopy(P0)
    hong["memory_declarations"][0]["type"] = "banana"
    chuoi = [json.dumps(hong, ensure_ascii=False), P1["semantic_program"][0]]
    tat, bat = _cap(kho, de, chuoi, "tat"), _cap(kho, de, chuoi, "bat", bat=True)
    than = lambda r: [x["body_sha256"] for x in _json(r, "PROVIDER_CALLS.json")["records"] if x["stage"] == "synthesis"]  # noqa: E731
    assert than(tat) == than(bat) and len(than(bat)) == 2


def test_O_bat_tat__envelope_GIONG(kho, de):
    for ten, synthesis in (("du", None), ("thieu", [json.dumps(_chuong_trinh("B"), ensure_ascii=False)])):
        tat, bat = _cap(kho, de, synthesis, f"{ten}_tat"), _cap(kho, de, synthesis, f"{ten}_bat", bat=True)
        assert _json(tat, "C01_ENVELOPE.json") == _json(bat, "C01_ENVELOPE.json")


# ══ P · Q · ca đã được nhận giữ chất lượng ═════════════════════════════════════
@pytest.mark.parametrize("ca, cid, idx", [("B03", "p3_mat_cau_va_thiet_dien_tron", 1), ("B04", "p4_hinh_tru_the_tich_va_xung_quanh", 0)])
def test_P_B03_B04_chuong_trinh_lich_su__van_du_bon_lop(AQ, ca, cid, idx):
    raw = RNB.doc_raw_theo_thu_tu(cid)
    hd = build_request_contract(json.loads(raw["semantic_analyze"][0]), problem_text=RNB.doc_de_bai()[cid], domain=DOMAIN_HINH_HOC)
    spec, o, mem, canh = _chay_offline(hd, json.loads(raw["semantic_program"][idx]))
    kq = AQ.chan_doan_chat_luong_dau_ra(hd, spec, mem, canh, route_served=o.servable, registered_answers=_dap_so(hd, ca))
    assert o.servable and all(_lop(h) == ("PASS", "PASS", "PASS", "PASS") for h in kq["obligations"]), kq
    assert kq["SILENT_QUALITY_FAILURE"] is False


def test_Q_C01_C02_phat_lai_dong_bang__canh_final_memory_dap_so_KHONG_doi__chat_luong_du(kho, de):
    for cid in ("C01", "C02"):
        tat = _chay(kho, cid, kich_ban=_kich_ban(de), ra=kho.tmp / f"{cid}_tat")
        bat = _chay(kho, cid, "--accepted-output-quality", kich_ban=_kich_ban(de), ra=kho.tmp / f"{cid}_bat")
        e_tat, e_bat = _json(tat, f"{cid}_ENVELOPE.json"), _json(bat, f"{cid}_ENVELOPE.json")
        assert e_tat["scene3d"] == e_bat["scene3d"] and _json(tat, "RUN_SUMMARY.json")["AUTOMATED_CHECKS"] == _json(bat, "RUN_SUMMARY.json")["AUTOMATED_CHECKS"]
        cl = _json(bat, f"{cid}_ACCEPTED_OUTPUT_QUALITY.json")
        assert cl["applicable"] is True and cl["route_served"] is True
        assert all(h["computation_coverage"] == "PASS" and h["construction_coverage"] == "PASS" and h["scene_coverage"] == "PASS"
                   for h in cl["obligations"]), cl


# ══ R · không trạng thái dùng chung ════════════════════════════════════════════
def test_R_khong_trang_thai_dung_chung(AQ, de):
    hd = _hd(de)
    _o, kq1 = _chan_doan(AQ, hd, "B")
    _chan_doan(AQ, hd, "A")
    kq1["obligations"].append({"bi_sua": True})
    _o, kq2 = _chan_doan(AQ, hd, "B")
    assert len(kq2["obligations"]) == len(hd.obligations) and kq2["SILENT_VISUAL_OMISSION"] is True
