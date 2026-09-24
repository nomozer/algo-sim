# -*- coding: utf-8 -*-
"""CHẨN ĐOÁN CỔNG PHỦ CẤU TRÚC (C₁a) — nghĩa vụ nào được yêu cầu, đã phủ, chưa phủ, vì nhánh luật nào. 0 mạng.

`SYNTHESIS_STRUCTURAL_COVERAGE_REJECTION_DIAGNOSIS` (2026-09-15). Benchmark đa ca: B02 (p1 · chóp + thiết diện) bị
loại `ROUTE_STRUCTURAL_COVERAGE / requested_operation_uncovered` mà không biết nghĩa vụ nào chưa phủ. Output live B02
không lưu ⇒ `HISTORICAL_B02_UNCOVERED_OBLIGATION = NOT_RECOVERABLE`; test ở đây KHÔNG dựng lại nó.

Audit (đo được trước bản sửa):
- `check_structural_coverage` duyệt `contract.obligations` theo thứ tự; MƯỜI nhánh kết luận "chưa phủ", nhưng chỉ
  sáu nhánh ghi `chan_doan` có cấu trúc — và ba nhánh khác nhau cùng mang `RANG_BUOC_THIEU`. Witness sai loại phép đo
  và witness là hằng số bị loại mà KHÔNG có dòng `chan_doan` nào.
- `route` gắn `chan_doan_nghia_vu` vào `SemanticRouteOutcome`, nhưng `pipeline` không phát nó cho observer và trace
  chỉ giữ mã lỗi. `chan_doan` cũ còn chở tên chương trình (`container`, `witness`, `ung_vien`) — không ghi được.

Fixture là biến thể nhỏ của chương trình p1 đóng băng (`thesis-final`, đã commit) trên RequestContract p1 dựng từ
`raw/analyze_0.json` đóng băng — không output live nào.
"""

from __future__ import annotations

import hashlib
import json

import httpx
import pytest

from app.ai import gemini
from app.simulation.semantic_program import coverage_gate as CG
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.route import verify_and_compile
from tests.test_photo_problem_live_runner import (  # noqa: F401 — fixture `de`, `kho` dùng qua tên
    CA_P1,
    KHOA_GIA,
    R,
    RNB,
    _chay,
    _json,
    _kich_ban,
    de,
    kho,
)

import acceptance_verdict as AV  # noqa: E402 — `scripts/` đã vào sys.path qua runner test

P1 = RNB.doc_raw_theo_thu_tu(CA_P1)
P1_ANALYZE = P1["semantic_analyze"][0]
P1_PROG = P1["semantic_program"][0]
TEP_TRACE = "C01_SYNTHESIS_REPAIR_TRACE.json"
KHOA_DONG_TRACE = {"obligation_pointer", "pointer_status", "operation_kind", "canonical_operation_kind", "target_kind",
                   "coverage_status", "reason_code", "evidence_kind", "evidence_count"}
KHOA_DONG_NGUON = KHOA_DONG_TRACE | {"obligation_fingerprint"}
KHOA_CHAN_DOAN = {"diagnostic_version", "route_stage", "route_code", "requested_count", "covered_count",
                  "uncovered_count", "not_evaluated_count", "obligations"}
#: Tên trong hợp đồng/chương trình p1 — không bao giờ được xuất hiện trong chẩn đoán.
TEN_THO = ("S.ABCD", "the_volume_sabcd", "area_T", "dist_S_BD", "alpha_plane", "ABCD_base", "measure")
BI_MAT_TRONG_HOP_DONG = "TOKEN-COVERAGE-SECRET-777"


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


def _hd(de, analyze_raw: str = P1_ANALYZE):
    return build_request_contract(json.loads(analyze_raw), problem_text=de["C01"], domain=DOMAIN_HINH_HOC)


def _spec(sua=None):
    d = json.loads(P1_PROG)
    if sua:
        sua(d)
    v = V.validate_semantic_program(d)
    assert v.ok, v.error
    return v.spec


def _dot(sua) -> str:
    d = json.loads(P1_PROG)
    sua(d)
    return json.dumps(d, ensure_ascii=False)


def _bo(target):
    return lambda d: d.__setitem__("statements", [s for s in d["statements"] if s.get("target_var") != target])


def _dat(target, expr):
    def f(d):
        for s in d["statements"]:
            if s.get("target_var") == target:
                s["expr"] = expr
    return f


def _bo_hai(d):
    _bo("the_volume_sabcd")(d)
    _bo("dist_S_BD")(d)


def _lay(doc, con_tro: str):
    for tok in con_tro[1:].split("/"):
        tok = tok.replace("~1", "/").replace("~0", "~")
        doc = doc[int(tok)] if isinstance(doc, list) else doc[tok]
    return doc


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _chua_phu(diag) -> list[dict]:
    return [r for r in diag["obligations"] if r["coverage_status"] == "UNCOVERED"]


def _chay_trace(kho, de, synthesis, analyze=None, ra=None, co_trace=True):
    thay = {("C01", "synthesis"): list(synthesis)}
    if analyze is not None:
        thay[("C01", "analyze")] = [analyze]
    them = ("--synthesis-repair-trace",) if co_trace else ()
    return _chay(kho, "C01", *them, kich_ban=_kich_ban(de, thay), ra=ra)


# ══ A · B · C · thiếu RIÊNG một nghĩa vụ ═════════════════════════════════════
@pytest.mark.parametrize("target, chi_so, kind", [
    ("the_volume_sabcd", 0, "volume"),
    ("area_T", 1, "area"),
    ("dist_S_BD", 2, "distance"),
])
def test_ABC_thieu_RIENG_mot_nghia_vu__chi_dung_nghia_vu_ay_bi_bao(de, target, chi_so, kind):
    hd = _hd(de)
    o = verify_and_compile(hd, _spec(_bo(target)))
    assert (o.stage_reached, o.error_code) == ("structural_coverage", "requested_operation_uncovered")
    diag = o.coverage_diagnostic
    assert set(diag) == KHOA_CHAN_DOAN
    assert (diag["route_stage"], diag["route_code"]) == ("structural_coverage", "requested_operation_uncovered")
    assert (diag["requested_count"], diag["covered_count"], diag["uncovered_count"], diag["not_evaluated_count"]) == (3, 2, 1, 0)
    (r,) = _chua_phu(diag)
    assert (r["obligation_pointer"], r["pointer_status"], r["operation_kind"], r["reason_code"]) == (
        f"/obligations/{chi_so}", "EXACT", kind, "WITNESS_WITHOUT_PRODUCER")
    khac = [x for x in diag["obligations"] if x is not r]
    assert all(x["coverage_status"] == "COVERED" and x["reason_code"] in ("COVERED", "COVERED_WITHOUT_SERVER_CHECKER")
               for x in khac)


# ══ D · thiếu hai ═════════════════════════════════════════════════════════════
def test_D_thieu_HAI__du_hai_dong__thu_tu_theo_chi_so_nguon(de):
    diag = verify_and_compile(_hd(de), _spec(_bo_hai)).coverage_diagnostic
    assert (diag["requested_count"], diag["covered_count"], diag["uncovered_count"]) == (3, 1, 2)
    assert [r["obligation_pointer"] for r in _chua_phu(diag)] == ["/obligations/0", "/obligations/2"]
    assert [r["obligation_pointer"] for r in diag["obligations"]] == ["/obligations/0", "/obligations/1", "/obligations/2"]


# ══ E · phủ đủ ═══════════════════════════════════════════════════════════════
def test_E_phu_DU__route_PASS__khong_phat_chan_doan_tu_choi(de):
    hd = _hd(de)
    spec = _spec()
    o = verify_and_compile(hd, spec)
    assert o.servable and o.coverage_diagnostic is None
    hang = CG.check_structural_coverage(hd, spec).trang_thai_nghia_vu
    assert [(h.chi_so, h.coverage_status) for h in hang] == [(0, "COVERED"), (1, "COVERED"), (2, "COVERED")]
    assert all(h.evidence_kind and h.evidence_count >= 1 for h in hang)


# ══ F · G · hai nghĩa vụ cùng loại, con trỏ đúng nguồn ═══════════════════════
def test_F_hai_nghia_vu_CUNG_loai__con_tro_KHAC_nhau(de):
    hd = _hd(de)
    them = Obligation(kind="volume", container="S.ABCD", params={"witness": "the_volume_2"})
    hd2 = hd.model_copy(update={"obligations": (hd.obligations[0], them)})
    diag = verify_and_compile(hd2, _spec()).coverage_diagnostic
    a, b = diag["obligations"]
    assert a["operation_kind"] == b["operation_kind"] == "volume"
    assert (a["obligation_pointer"], a["coverage_status"]) == ("/obligations/0", "COVERED")
    assert (b["obligation_pointer"], b["coverage_status"], b["reason_code"]) == ("/obligations/1", "UNCOVERED", "WITNESS_NOT_DECLARED")
    assert a["obligation_fingerprint"] != b["obligation_fingerprint"]


def test_G_con_tro_TRO_DUNG_nghia_vu_trong_RequestContract_goc(de):
    hd = _hd(de)
    diag = verify_and_compile(hd, _spec(_bo_hai)).coverage_diagnostic
    goc = hd.model_dump(mode="json")
    for r in diag["obligations"]:
        ob = _lay(goc, r["obligation_pointer"])
        assert ob["kind"] == r["operation_kind"]
        assert r["obligation_fingerprint"] == CG.dau_van_nghia_vu(Obligation.model_validate(ob))
        assert r["obligation_fingerprint"] == hashlib.sha256(_canon(ob)).hexdigest()[:16]


# ══ H · ánh xạ không chắc ═════════════════════════════════════════════════════
def test_H_hop_dong_doc_KHONG_khop__AMBIGUOUS__khong_con_tro_gia(de):
    hd = _hd(de)
    diag = verify_and_compile(hd, _spec(_bo_hai)).coverage_diagnostic
    dung = R.rut_gon_chan_doan_phu(diag, hd)
    assert [(r["obligation_pointer"], r["pointer_status"]) for r in dung["obligations"]] == [
        ("/obligations/0", "EXACT"), ("/obligations/1", "EXACT"), ("/obligations/2", "EXACT")]
    dao = hd.model_copy(update={"obligations": tuple(reversed(hd.obligations))})
    lech = R.rut_gon_chan_doan_phu(diag, dao)
    assert [(r["obligation_pointer"], r["pointer_status"]) for r in lech["obligations"]] == [
        (None, "AMBIGUOUS"), ("/obligations/1", "EXACT"), (None, "AMBIGUOUS")]
    ngan = hd.model_copy(update={"obligations": hd.obligations[:1]})
    assert [r["pointer_status"] for r in R.rut_gon_chan_doan_phu(diag, ngan)["obligations"]] == ["EXACT", "AMBIGUOUS", "AMBIGUOUS"]


# ══ I · không nhãn / giá trị / chương trình ═══════════════════════════════════
def test_I_chan_doan_KHONG_chua_ten_cong_thuc_gia_tri_hay_chuong_trinh(de):
    hd = _hd(de)
    diag = verify_and_compile(hd, _spec(_bo_hai)).coverage_diagnostic
    assert all(set(r) == KHOA_DONG_NGUON for r in diag["obligations"])
    rut = R.rut_gon_chan_doan_phu(diag, hd)
    assert set(rut) == KHOA_CHAN_DOAN and all(set(r) == KHOA_DONG_TRACE for r in rut["obligations"])
    for ban in (json.dumps(diag, ensure_ascii=False), json.dumps(rut, ensure_ascii=False)):
        for vet in TEN_THO:
            assert vet not in ban, vet
    assert "72" not in json.dumps(rut) and "3√6" not in json.dumps(rut, ensure_ascii=False)


# ══ J · bí mật giả trong hợp đồng/chương trình không lọt vào trace ══════════════
def test_J_bi_mat_gia_trong_container_witness__KHONG_vao_trace__ke_ca_khi_TAT_che(kho, de, monkeypatch):
    a = json.loads(P1_ANALYZE)
    a["obligations"].append({"kind": "volume", "container": BI_MAT_TRONG_HOP_DONG, "witness": KHOA_GIA})
    analyze = json.dumps(a, ensure_ascii=False)
    hd = _hd(de, analyze)
    o = verify_and_compile(hd, _spec())
    assert o.error_code == "requested_operation_uncovered"
    assert BI_MAT_TRONG_HOP_DONG in json.dumps(o.details, ensure_ascii=False)  # cửa sổ chứng: chuỗi tự do CÓ chở nó
    monkeypatch.setattr(R.BoKhuBiMat, "chuoi", lambda self, s: s)
    r = _chay_trace(kho, de, [P1_PROG], analyze=analyze)
    noi = (r.ra / TEP_TRACE).read_text(encoding="utf-8")
    (a0,) = json.loads(noi)["attempts"]
    rut = a0["route_coverage_diagnostic"]
    assert (a0["rejection_phase"], a0["rejection_code"]) == ("ROUTE_STRUCTURAL_COVERAGE", "requested_operation_uncovered")
    (x,) = _chua_phu(rut)
    assert (x["obligation_pointer"], x["pointer_status"], x["reason_code"]) == ("/obligations/3", "EXACT", "CONTAINER_NOT_DECLARED")
    assert [s for s in (BI_MAT_TRONG_HOP_DONG, KHOA_GIA) if s in noi] == []


# ══ K · xác định ══════════════════════════════════════════════════════════════
def test_K_cung_input__chan_doan_chinh_tac_GIONG_tung_byte(de):
    hd = _hd(de)
    ban = [_canon(verify_and_compile(hd, _spec(_bo_hai)).coverage_diagnostic) for _ in range(2)]
    assert ban[0] == ban[1]
    rut = [_canon(R.rut_gon_chan_doan_phu(verify_and_compile(hd, _spec(_bo_hai)).coverage_diagnostic, hd)) for _ in range(2)]
    assert rut[0] == rut[1]


# ══ L · ca hợp lệ vẫn được nhận ═══════════════════════════════════════════════
@pytest.mark.parametrize("cid, idx, mong", [
    ("p1_chop_thiet_dien_khoang_cach", 0, {"72", "9", "3√6"}),
    ("p3_mat_cau_va_thiet_dien_tron", 1, {"4500π", "144π"}),
    ("p4_hinh_tru_the_tich_va_xung_quanh", 0, {"360π", "120π"}),
])
def test_L_chuong_trinh_da_duoc_nhan__VAN_phuc_vu__khong_chan_doan_tu_choi(cid, idx, mong):
    raw = RNB.doc_raw_theo_thu_tu(cid)
    hd = build_request_contract(json.loads(raw["semantic_analyze"][0]), problem_text=RNB.doc_de_bai()[cid], domain=DOMAIN_HINH_HOC)
    v = V.validate_semantic_program(json.loads(raw["semantic_program"][idx]))
    o = verify_and_compile(hd, v.spec)
    assert o.servable and o.coverage_diagnostic is None
    assert set(AV.trich_ket_qua(o)["dai_luong"].values()) == mong


# ══ M · fixture B02 thiếu/sai bị loại đúng route, đúng mã, đúng nhánh ══════════
@pytest.mark.parametrize("sua, con_tro, ly_do, bang_chung", [
    (_bo("the_volume_sabcd"), ["/obligations/0"], ["WITNESS_WITHOUT_PRODUCER"], [None]),
    (_bo("area_T"), ["/obligations/1"], ["WITNESS_WITHOUT_PRODUCER"], [None]),
    (_bo("dist_S_BD"), ["/obligations/2"], ["WITNESS_WITHOUT_PRODUCER"], [None]),
    (_bo_hai, ["/obligations/0", "/obligations/2"], ["WITNESS_WITHOUT_PRODUCER"] * 2, [None, None]),
    (_dat("the_volume_sabcd", {"kind": "measure", "quantity": "distance", "of": "S", "wrt": "BD"}),
     ["/obligations/0"], ["WITNESS_NOT_DERIVED_FROM_CONTAINER"], ["WITNESS_RESOLUTION_QUANTITY_LECH"]),
    (_dat("the_volume_sabcd", {"kind": "literal", "value": 72}),
     ["/obligations/0"], ["WITNESS_NOT_DERIVED_FROM_CONTAINER"], ["WITNESS_RESOLUTION_PRODUCER_KHONG_PHAI_MEASURE"]),
])
def test_M_fixture_B02__dung_route_code__dung_nhanh_ly_do(de, sua, con_tro, ly_do, bang_chung):
    o = verify_and_compile(_hd(de), _spec(sua))
    assert (o.stage_reached, o.error_code) == ("structural_coverage", "requested_operation_uncovered")
    ds = _chua_phu(o.coverage_diagnostic)
    assert [r["obligation_pointer"] for r in ds] == con_tro
    assert [r["reason_code"] for r in ds] == ly_do
    assert [r["evidence_kind"] for r in ds] == bang_chung


# ══ N · lỗi provider ══════════════════════════════════════════════════════════
def test_N_loi_provider__KHONG_co_chan_doan_phu_gia(kho, de):
    (a0,) = _json(_chay_trace(kho, de, [httpx.Response(503, json={"error": "qua tai"})]), TEP_TRACE)["attempts"]
    assert a0["result"] == "PROVIDER_ERROR" and a0["route_coverage_diagnostic"] is None
    assert "coverage_status" not in json.dumps(a0)


# ══ O · P · tắt/bật trace ═════════════════════════════════════════════════════
def test_O_trace_bat_tat__request_Gemini_GIONG_tung_byte__chan_doan_chi_o_trace(kho, de):
    chuoi = [_dot(_bo("the_volume_sabcd"))]
    tat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "tat", co_trace=False)
    bat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "bat")
    than = lambda r: [(x["stage"], x["body_sha256"]) for x in _json(r, "PROVIDER_CALLS.json")["records"]]  # noqa: E731
    assert than(tat) == than(bat)
    assert _json(tat, "RUN_SUMMARY.json")["SYNTHESIS_HTTP_REQUESTS"] == _json(bat, "RUN_SUMMARY.json")["SYNTHESIS_HTTP_REQUESTS"] == 1
    (a0,) = _json(bat, TEP_TRACE)["attempts"]
    assert (a0["rejection_phase"], a0["route_coverage_diagnostic"]["uncovered_count"]) == ("ROUTE_STRUCTURAL_COVERAGE", 1)


def test_P_trace_bat_tat__phan_hoi_sua_GIONG_tung_byte(kho, de):
    hong = _dot(lambda d: d["memory_declarations"][0].__setitem__("type", "banana"))
    chuoi = [hong, _dot(_bo("the_volume_sabcd"))]
    tat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "tat", co_trace=False)
    bat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "bat")
    than = lambda r: [x["body_sha256"] for x in _json(r, "PROVIDER_CALLS.json")["records"] if x["stage"] == "synthesis"]  # noqa: E731
    assert than(tat) == than(bat) and len(than(bat)) == 2
    a0, a1 = _json(bat, TEP_TRACE)["attempts"]
    assert a0["route_coverage_diagnostic"] is None and a1["route_coverage_diagnostic"]["uncovered_count"] == 1


# ══ Q · không trạng thái dùng chung ═══════════════════════════════════════════
def test_Q_khong_trang_thai_dung_chung(de):
    hd = _hd(de)
    x1 = verify_and_compile(hd, _spec(_bo("area_T"))).coverage_diagnostic
    y = verify_and_compile(hd, _spec(_bo_hai)).coverage_diagnostic
    x1["obligations"].append({"bi_sua": True})
    x2 = verify_and_compile(hd, _spec(_bo("area_T"))).coverage_diagnostic
    assert len(x2["obligations"]) == 3 and x2["uncovered_count"] == 1 and y["uncovered_count"] == 2
    g1 = [h.model_dump() for h in CG.check_structural_coverage(hd, _spec(_bo("area_T"))).trang_thai_nghia_vu]
    CG.check_structural_coverage(hd, _spec(_bo_hai))
    assert g1 == [h.model_dump() for h in CG.check_structural_coverage(hd, _spec(_bo("area_T"))).trang_thai_nghia_vu]


# ══ R · reader trace lịch sử ══════════════════════════════════════════════════
def test_R_reader_doc_duoc_trace_v1_LICH_SU_va_v2_CU_lan_MOI(kho, de):
    from pathlib import Path

    v1 = json.loads((Path(__file__).parents[1] / "fixtures" / "synthesis_repair_trace_v1_c02_redacted.json").read_text(encoding="utf-8"))
    d1 = R.doc_trace_vong_sua(v1)
    assert all(a["route_coverage_diagnostic"] is None for a in d1["attempts"])
    t = _json(_chay_trace(kho, de, [_dot(_bo("area_T"))]), TEP_TRACE)
    assert t["trace_version"] == "synthesis-repair-trace/2"
    d2 = R.doc_trace_vong_sua(t)
    assert d2["attempts"][0]["route_coverage_diagnostic"]["uncovered_count"] == 1
    cu = json.loads(json.dumps(t))
    for a in cu["attempts"]:
        a.pop("route_coverage_diagnostic", None)
    assert all(a["route_coverage_diagnostic"] is None for a in R.doc_trace_vong_sua(cu)["attempts"])
