# -*- coding: utf-8 -*-
"""CHẨN ĐOÁN TỪ CHỐI SYNTHESIS — con trỏ JSON + loại lỗi Pydantic trong trace vòng sửa. 0 request mạng.

`SYNTHESIS_REJECTION_POINTER_TRACE_GAP` (2026-09-15). Pilot C02 `20260915T061735Z-7b979fce` bị loại
`PROGRAM_SCHEMA / SCHEMA_VALUE_ERROR` và trace không ghi được CHỖ lỗi: `validator.validate_semantic_program` biến
`ValidationError` thành chuỗi, runner chỉ giữ `SCHEMA_<type>`. Đầu ra thô cố ý không lưu ⇒ lỗi quá khứ KHÔNG khôi
phục được, và test ở đây KHÔNG dựng lại nó.

Hai sự thật đo được quyết định thiết kế:
- `loc` của Pydantic trỏ vào dữ liệu SAU các `model_validator(mode="before")`: `_nang_declare_point` gỡ các
  `declare_point` khỏi `statements`, nên `statements[5]` thô hiện ra là `loc ('statements', 0, …)`. Đổi thẳng `loc`
  thành con trỏ là BỊA con trỏ. Con trỏ chỉ `EXACT` khi dò trên JSON thô ra đúng MỘT ứng viên (thẻ `kind` khớp, lá
  bằng `input` của lỗi — chỉ dùng trong bộ nhớ); còn lại `AMBIGUOUS` với `json_pointer = null`.
- `str(ValidationError)` chở `input_value` ⇒ tóm tắt tự do của trace v1 chở giá trị mô hình cho mọi lỗi Pydantic.
  Trace v2 giữ lại tóm tắt ấy (`WITHHELD_PYDANTIC_MESSAGE`) và ghi `rejection_diagnostics` thay vào.

Biến thể là thay đổi NHỎ trên chương trình p1 đóng băng (`thesis-final`, đã commit) — không đầu ra riêng tư nào.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.ai import gemini, pipeline
from app.ai.telemetry import current_stage
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
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
P1_PROG = P1["semantic_program"][0]
TEP_TRACE = "C01_SYNTHESIS_REPAIR_TRACE.json"
MOC = "MOC-GIA-TRI-QQX"
FIXTURE_V1 = Path(__file__).parent / "fixtures" / "synthesis_repair_trace_v1_c02_redacted.json"
KHOA_CHI_TIET = {"json_pointer", "pointer_status", "pydantic_error_type", "rule_id", "received_json_type"}
KHOA_CHAN_DOAN = {"phase", "code", "error_count", "details"}
#: Tên trường Pydantic mang dữ liệu mô hình hoặc văn bản tự do — không bao giờ được là khoá trong trace.
KHOA_CAM = {"input", "input_value", "msg", "ctx", "url", "expected", "expected_tags", "discriminator", "tag", "error"}


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


def _dot(sua) -> str:
    d = json.loads(P1_PROG)
    sua(d)
    return json.dumps(d, ensure_ascii=False)


def _hd(de):
    return build_request_contract(json.loads(P1["semantic_analyze"][0]), problem_text=de["C01"], domain=DOMAIN_HINH_HOC)


def _chay_trace(kho, de, synthesis, *them, ra=None):
    return _chay(kho, "C01", "--synthesis-repair-trace", *them,
                 kich_ban=_kich_ban(de, {("C01", "synthesis"): list(synthesis)}), ra=ra)


def _lay(doc, con_tro: str):
    """Giải con trỏ RFC 6901 trên JSON thô — độc lập với mã runner."""
    if con_tro == "":
        return doc
    for tok in con_tro[1:].split("/"):
        tok = tok.replace("~1", "/").replace("~0", "~")
        doc = doc[int(tok)] if isinstance(doc, list) else doc[tok]
    return doc


def _moi_khoa(o) -> set[str]:
    if isinstance(o, dict):
        return set(o) | set().union(*(_moi_khoa(v) for v in o.values())) if o else set()
    if isinstance(o, list):
        return set().union(*(_moi_khoa(v) for v in o)) if o else set()
    return set()


# ── biến thể ────────────────────────────────────────────────────────────────
def _type_sai(d):  # literal_error ở phần tử mảng memory_declarations
    d["memory_declarations"][0]["type"] = MOC


def _thieu_ten(d):  # missing ở phần tử mảng
    d["memory_declarations"][1].pop("name")


def _kind_sai(d):  # union_tag_invalid ở câu lệnh (chỉ số thô 5, loc sau biến đổi 0)
    d["statements"][5]["kind"] = "construct_" + MOC


def _long_nhau(d):  # list_type lồng trong câu lệnh construct_polygon
    d["statements"][5]["vertices"] = 4242


def _literal_long(d):  # literal_error lồng sâu: assign → measure → quantity
    d["statements"][9]["expr"]["quantity"] = MOC


def _nhieu_loi(d):
    _type_sai(d)
    _thieu_ten(d)
    _long_nhau(d)
    _literal_long(d)


def _goc_mau_thuan(d, toa_do=None):  # ValueError ở model_validator(mode="before") của gốc ⇒ loc ()
    st = next(s for s in d["statements"] if s.get("kind") == "declare_point")
    d["memory_declarations"].append({"name": st["target_var"], "type": "point3",
                                     "initial_value": toa_do if toa_do is not None else [MOC, 0, 0]})


def _khong_phai_mang(d):  # memory_declarations không phải mảng ⇒ loc trỏ vào dữ liệu đã bị biến đổi
    d["memory_declarations"] = MOC


def _at_khai_bao(d):  # khoá mang dữ liệu bị bỏ im lặng
    d["memory_declarations"][0]["at"] = [1, 2, 3]


# ══ A · lỗi lồng ═════════════════════════════════════════════════════════════
@pytest.mark.parametrize("sua, con_tro, loai, kieu, gia_tri", [
    (_long_nhau, "/statements/5/vertices", "list_type", "integer", 4242),
    (_literal_long, "/statements/9/expr/quantity", "literal_error", "string", MOC),
])
def test_A_loi_LONG__con_tro_that_tren_JSON_tho__khong_phai_loc_sau_bien_doi(de, sua, con_tro, loai, kieu, gia_tri):
    raw = _dot(sua)
    cd = R.phan_loai_ung_vien(raw, _hd(de))["diagnostics"]
    assert (cd["phase"], cd["code"], cd["error_count"]) == ("PROGRAM_SCHEMA", f"SCHEMA_{loai.upper()}", 1)
    assert cd["details"] == [{"json_pointer": con_tro, "pointer_status": "EXACT", "pydantic_error_type": loai,
                              "rule_id": None, "received_json_type": kieu}]
    assert _lay(json.loads(raw), con_tro) == gia_tri
    # Cửa sổ chứng: `loc` thô KHÔNG phải con trỏ này — chỉ số đã dời vì `declare_point` bị nâng.
    with pytest.raises(ValidationError) as e:
        SemanticProgramSpec.model_validate(json.loads(raw))
    assert R.con_tro_json(tuple(e.value.errors(include_url=False)[0]["loc"])) != con_tro


# ══ B · phần tử mảng ═════════════════════════════════════════════════════════
@pytest.mark.parametrize("sua, con_tro, loai, kieu", [
    (_type_sai, "/memory_declarations/0/type", "literal_error", "string"),
    (_thieu_ten, "/memory_declarations/1/name", "missing", "absent"),
])
def test_B_phan_tu_MANG__giu_dung_chi_so(de, sua, con_tro, loai, kieu):
    cd = R.phan_loai_ung_vien(_dot(sua), _hd(de))["diagnostics"]
    assert cd["details"] == [{"json_pointer": con_tro, "pointer_status": "EXACT", "pydantic_error_type": loai,
                              "rule_id": None, "received_json_type": kieu}]


# ══ C · RFC 6901 ═════════════════════════════════════════════════════════════
def test_C_RFC6901__escape_nga_truoc_gach_sau():
    assert R.con_tro_json(("a/b", "c~d", 0, "~1")) == "/a~1b/c~0d/0/~01"
    assert R.con_tro_json(["statements", 12, "vertices"]) == "/statements/12/vertices"
    assert _lay({"a/b": {"c~d": [{"~1": 7}]}}, R.con_tro_json(("a/b", "c~d", 0, "~1"))) == 7


# ══ D · lỗi gốc ══════════════════════════════════════════════════════════════
def test_D_loi_GOC__con_tro_rong__rule_id_la_ham_da_nem(de):
    assert R.con_tro_json(()) == ""
    cd = R.phan_loai_ung_vien(_dot(_goc_mau_thuan), _hd(de))["diagnostics"]
    assert (cd["code"], cd["error_count"]) == ("SCHEMA_VALUE_ERROR", 1)
    assert cd["details"] == [{"json_pointer": "", "pointer_status": "EXACT", "pydantic_error_type": "value_error",
                              "rule_id": "SemanticProgramSpec._nang_declare_point", "received_json_type": "object"}]


# ══ E · loc không chắc chắn ═══════════════════════════════════════════════════
def test_E_loc_KHONG_chac_chan__AMBIGUOUS__khong_con_tro_gia(de):
    cd = R.phan_loai_ung_vien(_dot(_khong_phai_mang), _hd(de))["diagnostics"]
    assert cd["error_count"] == len(cd["details"]) > 1
    assert all(x["json_pointer"] is None and x["pointer_status"] == "AMBIGUOUS" for x in cd["details"])
    # Thẻ union không khớp `kind` thô ⇒ không được bỏ qua thẻ để ra một con trỏ.
    loi = [{"loc": ("statements", 0, "construct_polygon", "vertices"), "type": "list_type", "input": 4242}]
    (x,) = R.chan_doan_tu_loi(loi, {"statements": [{"kind": "assign", "vertices": 4242}]})
    assert (x["json_pointer"], x["pointer_status"]) == (None, "AMBIGUOUS")
    # Hai ứng viên bằng nhau ⇒ không chọn hộ.
    (y,) = R.chan_doan_tu_loi([{"loc": ("statements", 0, "vertices"), "type": "list_type", "input": 1}],
                              {"statements": [{"vertices": 1}, {"vertices": 1}]})
    assert (y["json_pointer"], y["pointer_status"]) == (None, "AMBIGUOUS")


# ══ F · nhiều lỗi ═════════════════════════════════════════════════════════════
def test_F_nhieu_loi__du_so_luong__thu_tu_XAC_DINH_khong_theo_thu_tu_Pydantic(de):
    raw = _dot(_nhieu_loi)
    cd = R.phan_loai_ung_vien(raw, _hd(de))["diagnostics"]
    assert cd["error_count"] == len(cd["details"]) == 4
    assert {x["json_pointer"] for x in cd["details"]} == {
        "/memory_declarations/0/type", "/memory_declarations/1/name", "/statements/5/vertices",
        "/statements/9/expr/quantity"}
    assert all(x["pointer_status"] == "EXACT" for x in cd["details"])
    assert cd["details"] == sorted(cd["details"], key=R.khoa_sap_xep_chan_doan)
    with pytest.raises(ValidationError) as e:
        SemanticProgramSpec.model_validate(json.loads(raw))
    loi = e.value.errors(include_url=False)
    assert R.chan_doan_tu_loi(list(reversed(loi)), json.loads(raw)) == R.chan_doan_tu_loi(loi, json.loads(raw)) \
        == cd["details"]


# ══ G · xác định từng byte ════════════════════════════════════════════════════
def test_G_hai_lan_dung_trace__JSON_chinh_tac_GIONG_tung_byte(kho, de):
    chuoi = [_dot(_nhieu_loi), _dot(_goc_mau_thuan), P1_PROG]
    t1 = _json(_chay_trace(kho, de, chuoi, ra=kho.tmp / "g1"), TEP_TRACE)
    t2 = _json(_chay_trace(kho, de, chuoi, ra=kho.tmp / "g2"), TEP_TRACE)
    assert t1["trace_version"] == R.TRACE_VERSION == "synthesis-repair-trace/2"
    assert R.trace_chuan_hoa(t1) == R.trace_chuan_hoa(t2)
    assert [(a["rejection_diagnostics"] or {}).get("code") for a in t1["attempts"]] == [
        "SCHEMA_LITERAL_ERROR", "SCHEMA_VALUE_ERROR", None]
    c = _hd(de)
    ban = [json.dumps(R.phan_loai_ung_vien(_dot(_nhieu_loi), c)["diagnostics"], sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8") for _ in range(2)]
    assert ban[0] == ban[1]


# ══ H · khoá bị bỏ im lặng giữ nguyên ═════════════════════════════════════════
def test_H_SCHEMA_SILENTLY_DROPPED_KEY__giu_con_tro_cu__tom_tat_hop_dong_van_con(kho, de):
    raw = _dot(_at_khai_bao)
    pl = R.phan_loai_ung_vien(raw, _hd(de))
    assert (pl["phase"], pl["code"]) == ("PROGRAM_SCHEMA", "SCHEMA_SILENTLY_DROPPED_KEY")
    assert "[SCHEMA_SILENTLY_DROPPED_KEY] /memory_declarations/0/at" in pl["message"]
    assert pl["diagnostics"] == {"phase": "PROGRAM_SCHEMA", "code": "SCHEMA_SILENTLY_DROPPED_KEY", "error_count": 1,
                                 "details": [{"json_pointer": "/memory_declarations/0/at", "pointer_status": "EXACT",
                                              "pydantic_error_type": None, "rule_id": "SCHEMA_SILENTLY_DROPPED_KEY",
                                              "received_json_type": "array"}]}
    a0 = _json(_chay_trace(kho, de, [raw, P1_PROG]), TEP_TRACE)["attempts"][0]
    assert a0["rejection_diagnostics"] == pl["diagnostics"]
    assert a0["rejection_summary_status"] == "PRESENT"
    assert "/memory_declarations/0/at" in a0["rejection_summary_redacted"]


# ══ I · lỗi provider ══════════════════════════════════════════════════════════
def test_I_loi_provider__KHONG_co_chan_doan_Pydantic_gia(kho, de):
    (a0,) = _json(_chay_trace(kho, de, [httpx.Response(503, json={"error": "qua tai"})]), TEP_TRACE)["attempts"]
    assert (a0["result"], a0["rejection_phase"]) == ("PROVIDER_ERROR", "PROVIDER")
    assert a0["rejection_diagnostics"] is None
    assert "json_pointer" not in json.dumps(a0) and "pydantic_error_type" not in json.dumps(a0)
    assert R.phan_loai_ung_vien("{ khong phai json", None)["diagnostics"] is None


# ══ J · không dữ liệu mô hình ═════════════════════════════════════════════════
def test_J_trace_KHONG_chua_input_msg_ctx_ung_vien_tho_prompt(kho, de):
    chuoi = [_dot(_nhieu_loi), _dot(_goc_mau_thuan), _dot(_kind_sai)]
    r = _chay_trace(kho, de, chuoi)
    noi_dung = (r.ra / TEP_TRACE).read_text(encoding="utf-8")
    t = json.loads(noi_dung)
    assert [a["rejection_phase"] for a in t["attempts"]] == ["PROGRAM_SCHEMA"] * 3
    assert [(a["rejection_summary_status"], a["rejection_summary_redacted"]) for a in t["attempts"]] == [
        ("WITHHELD_PYDANTIC_MESSAGE", None)] * 3
    for a in t["attempts"]:
        cd = a["rejection_diagnostics"]
        assert set(cd) == KHOA_CHAN_DOAN and all(set(x) == KHOA_CHI_TIET for x in cd["details"])
    assert not (_moi_khoa(t) & KHOA_CAM), _moi_khoa(t) & KHOA_CAM
    for vet in (MOC, "Input should", "Value error", "input_value", "HAI TOẠ ĐỘ", "Đề bài:", de["C01"]):
        assert vet not in noi_dung, vet


# ══ K · bí mật ════════════════════════════════════════════════════════════════
def test_K_bi_mat_trong_GIA_TRI_va_THONG_DIEP_ngoai_le__khong_lot__ke_ca_khi_TAT_che(kho, de, monkeypatch):
    trong_gia_tri = _dot(lambda d: d["memory_declarations"][0].__setitem__("type", KHOA_GIA))
    trong_thong_diep = _dot(lambda d: _goc_mau_thuan(d, toa_do=["TOKEN-AUTH-555", 0, 0]))
    for raw, bi_mat in ((trong_gia_tri, KHOA_GIA), (trong_thong_diep, "TOKEN-AUTH-555")):
        with pytest.raises(ValidationError) as e:  # cửa sổ chứng: bí mật THẬT SỰ nằm trong lời Pydantic / ngoại lệ
            SemanticProgramSpec.model_validate(json.loads(raw))
        assert bi_mat in str(e.value)
    monkeypatch.setattr(R.BoKhuBiMat, "chuoi", lambda self, s: s)  # an toàn phải đến từ việc KHÔNG ghi, không từ che
    r = _chay_trace(kho, de, [trong_gia_tri, trong_thong_diep, P1_PROG])
    noi_dung = (r.ra / TEP_TRACE).read_text(encoding="utf-8")
    assert [s for s in (KHOA_GIA, "TOKEN-AUTH-555") if s in noi_dung] == []


# ══ L · M · N · P · tắt/bật quan trắc ═════════════════════════════════════════
def test_L_tat_quan_trac__hanh_vi_NHU_TRUOC__cung_envelope_va_bo_dem(kho, de):
    chuoi = [_dot(_nhieu_loi), _dot(_goc_mau_thuan), P1_PROG]
    tat = _chay(kho, "C01", kich_ban=_kich_ban(de, {("C01", "synthesis"): list(chuoi)}), ra=kho.tmp / "tat")
    bat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "bat")
    assert tat.code == bat.code == R.EXIT_PASS, (tat.err, bat.err)
    assert not (tat.ra / TEP_TRACE).exists()
    assert _json(tat, "C01_ENVELOPE.json") == _json(bat, "C01_ENVELOPE.json")
    tt_tat, tt_bat = _json(tat, "RUN_SUMMARY.json"), _json(bat, "RUN_SUMMARY.json")
    for k in ("SYNTHESIS_HTTP_REQUESTS", "HTTP_REQUESTS_SENT", "AUTOMATED_CHECKS", "RETRIES"):
        assert tt_tat[k] == tt_bat[k], k


def _chay_route(text: str, dap: dict[str, list[str]], observer):
    ban = {k: list(v) for k, v in dap.items()}

    def tra(_req):
        return R._phan_hoi_gemini(ban[current_stage()].pop(0))

    cong = R.CongHttp(httpx.MockTransport(tra), 20, R.BoKhuBiMat())
    cong.dat_ca("PARITY")
    with R.dung_ngan_sach(R.tao_ngan_sach_nghiem_thu()) as ngan_sach, R.cai_cong_http(cong):
        o = asyncio.run(pipeline._semantic_route_attempt(text, {}, "khoa-gia", observer, domain=DOMAIN_HINH_HOC))
    return o, [(x["stage"], x["body_sha256"]) for x in cong.records], ngan_sach.logical_calls


def test_M_quan_trac_bat_tat__request_Gemini_GIONG_tung_byte__cung_so_luot_logic(de):
    dap = {"semantic_analyze": list(P1["semantic_analyze"]),
           "semantic_program": [_dot(_nhieu_loi), _dot(_goc_mau_thuan), P1_PROG]}
    o0, b0, n0 = _chay_route(de["C01"], dap, None)
    o1, b1, n1 = _chay_route(de["C01"], dap, R.QuanTracVongSua())
    assert b0 == b1 and [s for s, _ in b0].count("synthesis") == 3 and n0 == n1 == 4
    assert o0.servable and o1.servable and o0.scene3d == o1.scene3d
    assert AV.trich_ket_qua(o0) == AV.trich_ket_qua(o1)


def test_N_phan_hoi_sua_GIONG_tung_byte__va_KHONG_mang_chan_doan(kho, de):
    chuoi = [_dot(_nhieu_loi), P1_PROG]
    tat = _chay(kho, "C01", kich_ban=_kich_ban(de, {("C01", "synthesis"): list(chuoi)}), ra=kho.tmp / "tat")
    bat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "bat")
    than = lambda r: [x["body_sha256"] for x in _json(r, "PROVIDER_CALLS.json")["records"]  # noqa: E731
                      if x["stage"] == "synthesis"]
    assert than(tat) == than(bat) and len(than(bat)) == 2
    a0 = _json(bat, TEP_TRACE)["attempts"][0]
    loi = V.validate_semantic_program(json.loads(chuoi[0])).error
    assert a0["feedback_sha256"] == hashlib.sha256(loi.encode("utf-8")).hexdigest()
    assert a0["feedback_delivered_in_next_request"] is True


def test_P_ngan_sach_HTTP_va_thu_lai_KHONG_doi(kho, de):
    chuoi = [_dot(_nhieu_loi), _dot(_goc_mau_thuan), _dot(_kind_sai)]
    tat = _chay(kho, "C01", kich_ban=_kich_ban(de, {("C01", "synthesis"): list(chuoi)}), ra=kho.tmp / "tat")
    bat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "bat")
    bo = []
    for r in (tat, bat):
        tt = _json(r, "RUN_SUMMARY.json")
        bo.append((r.code, tt["SYNTHESIS_HTTP_REQUESTS"], tt["HTTP_REQUESTS_SENT"], tt["RETRIES"], tt["HTTP_REQUESTS_BLOCKED"]))
        assert tt["HTTP_REQUESTS_SENT"] == tt["VISION_HTTP_REQUESTS"] + tt["ANALYZE_HTTP_REQUESTS"] + tt["SYNTHESIS_HTTP_REQUESTS"]
    assert bo[0] == bo[1]
    assert (bo[0][0], bo[0][1], bo[0][3], bo[0][4]) == (R.EXIT_CASE_FAIL, 3, 0, 0)


# ══ O · không trạng thái dùng chung ═══════════════════════════════════════════
def test_O_khong_trang_thai_dung_chung_giua_hai_luot(de):
    c = _hd(de)
    x1 = R.phan_loai_ung_vien(_dot(_long_nhau), c)["diagnostics"]
    y = R.phan_loai_ung_vien(_dot(_nhieu_loi), c)["diagnostics"]
    x2 = R.phan_loai_ung_vien(_dot(_long_nhau), c)["diagnostics"]
    assert x1 == x2 and (x1["error_count"], y["error_count"]) == (1, 4)
    x1["details"].append({"bi_sua": True})
    x3 = R.phan_loai_ung_vien(_dot(_long_nhau), c)["diagnostics"]
    assert x3 == x2 and len(x3["details"]) == 1


# ══ Q · đọc trace cũ ══════════════════════════════════════════════════════════
def test_Q_reader_doc_duoc_trace_v1_LICH_SU_va_v2__phien_ban_la_bi_tu_choi(kho, de):
    v1 = json.loads(FIXTURE_V1.read_text(encoding="utf-8"))
    ban_goc = json.dumps(v1, sort_keys=True)
    assert v1["trace_version"] == "synthesis-repair-trace/1"
    d1 = R.doc_trace_vong_sua(v1)
    assert json.dumps(v1, sort_keys=True) == ban_goc, "reader không được sửa đầu vào"
    assert d1["source_trace_version"] == "synthesis-repair-trace/1"
    a0, a1 = d1["attempts"]
    assert (a0["rejection_phase"], a0["rejection_code"]) == ("PROGRAM_SCHEMA", "SCHEMA_SILENTLY_DROPPED_KEY")
    assert (a0["rejection_diagnostics"], a0["rejection_diagnostics_status"]) == (None, "NOT_CAPTURED_IN_V1")
    assert a1["result"] == "ACCEPTED" and a1["rejection_diagnostics_status"] == "NOT_CAPTURED_IN_V1"
    t2 = _json(_chay_trace(kho, de, [_dot(_long_nhau), P1_PROG]), TEP_TRACE)
    d2 = R.doc_trace_vong_sua(t2)
    assert d2["source_trace_version"] == R.TRACE_VERSION
    b0, b1 = d2["attempts"]
    assert b0["rejection_diagnostics_status"] == "CAPTURED" and b1["rejection_diagnostics_status"] == "NOT_APPLICABLE"
    assert b0["rejection_diagnostics"]["details"][0]["json_pointer"] == "/statements/5/vertices"
    with pytest.raises(ValueError):
        R.doc_trace_vong_sua({**t2, "trace_version": "synthesis-repair-trace/9"})
