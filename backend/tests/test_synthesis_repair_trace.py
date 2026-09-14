# -*- coding: utf-8 -*-
"""QUAN TRẮC VÒNG SỬA SYNTHESIS — `run_photo_problem_live.py --synthesis-repair-trace`. 0 request mạng.

`SYNTHESIS_REPAIR_OBSERVABILITY_HARDENING` (2026-09-14). Lượt C01 thật tiêu hai lượt synthesis và KHÔNG
biết lượt đầu chết vì gì. Pipeline VỐN phát đủ sự kiện cho một observer thụ động (`_emit`, bất biến #22):
`semantic_program_candidate` (đầu ra thô, trước parse) và `semantic_program_attempt` (lời từ chối gửi
ngược, kèm `gate`). Runner gọi `run_pipeline` với `observer=None`, nên mọi sự kiện rơi vào hư không.

Test ở đây khoá hợp đồng trace — phase · mã ổn định · băm ứng viên/feedback · liên kết lượt sửa · token
từng lượt — và khoá rằng bật quan trắc KHÔNG đổi một byte request nào, không đổi chương trình hay đáp số.

Ứng viên hỏng là biến thể NHỎ của chương trình p1 đóng băng (`thesis-final`, đã commit) — không dùng
đầu ra riêng tư nào. Mỗi biến thể đã được dò trên đúng cổng tất định mà nó phải chạm.
"""

from __future__ import annotations

import asyncio
import hashlib
import json

import httpx
import pytest

from app.ai import gemini, pipeline
from app.ai.telemetry import current_stage
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from tests.test_photo_problem_live_runner import (  # noqa: F401 — fixture `de`, `kho` dùng qua tên
    BI_MAT,
    CA_P1,
    CA_P6,
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
JSON_HONG = "{ day khong phai json"
TEP_TRACE = "C01_SYNTHESIS_REPAIR_TRACE.json"


def _sha(s: str | bytes) -> str:
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, str) else s).hexdigest()


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


def _dot(sua) -> str:
    d = json.loads(P1_PROG)
    sua(d)
    return json.dumps(d, ensure_ascii=False)


# Biến thể — mỗi cái đã dò: cổng nào từ chối, với mã nào.
def _schema(d):  # validator · Pydantic union tag
    d["statements"][5]["kind"] = "construct_banana"


def _type_check(d):  # validator · SemanticTypeChecker
    d["statements"][5]["vertices"] = ["A", "B", "C", "Z"]


def _ir_static(d):  # kiem_tinh
    d["statements"][8]["plane"] = "ABCD_base"


def _grounding(d):  # check_grounding, sửa được
    d["statements"][2].pop("source_fact_id")


def _hau_dieu_kien(d):  # qua vòng sửa, route chặn ở postconditions
    d["statements"][9]["expr"].update(quantity="area", of="T")


def _voi_token(van_ban: str, prompt: int, cand: int, nghi: int) -> httpx.Response:
    return httpx.Response(200, json={
        "candidates": [{"content": {"parts": [{"text": van_ban}]}}],
        "usageMetadata": {"promptTokenCount": prompt, "candidatesTokenCount": cand, "thoughtsTokenCount": nghi,
                          "totalTokenCount": prompt + cand + nghi}})


def _chay_trace(kho, de, synthesis, *them, ra=None):
    return _chay(kho, "C01", "--synthesis-repair-trace", *them,
                 kich_ban=_kich_ban(de, {("C01", "synthesis"): list(synthesis)}), ra=ra)


def _trace(r) -> dict:
    return _json(r, TEP_TRACE)


def _thong_diep_json(raw: str) -> str:
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        return f"JSON không parse được ({e})"
    raise AssertionError("không phải JSON hỏng")


# ══ A · JSON hỏng → bị loại → feedback → lượt sửa được nhận ═══════════════════
def test_A_JSON_hong__phase_code_hash__khong_luu_tho__luot_sua_LIEN_KET_dung(kho, de):
    r = _chay_trace(kho, de, [_voi_token(JSON_HONG, 3000, 50, 100), _voi_token(P1_PROG, 3100, 800, 200)])
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    t = _trace(r)
    assert t["trace_version"] == R.TRACE_VERSION == "synthesis-repair-trace/1"
    a0, a1 = t["attempts"]
    loi = _thong_diep_json(JSON_HONG)
    assert (a0["result"], a0["rejection_phase"], a0["rejection_code"]) == ("REJECTED", "JSON_PARSE", "JSON_DECODE_ERROR")
    assert a0["candidate_sha256"] == _sha(JSON_HONG) and a0["candidate_byte_count"] == len(JSON_HONG.encode("utf-8"))
    assert (a0["feedback_sha256"], a0["feedback_codes"]) == (_sha(loi), ["JSON_DECODE_ERROR"])
    assert a0["feedback_delivered_in_next_request"] is True and a0["repair_attempted"] is True
    assert a0["repaired_by_logical_call"] == a1["logical_call"] and a1["repairs_logical_call"] == a0["logical_call"]
    assert (a1["result"], a1["rejection_phase"], a1["rejection_code"]) == ("ACCEPTED", None, None)
    assert t["links"] == [{"rejected_logical_call": a0["logical_call"], "repaired_by_logical_call": a1["logical_call"],
                           "feedback_sha256": _sha(loi)}]
    assert [(a["usage"]["promptTokenCount"], a["usage"]["totalTokenCount"]) for a in (a0, a1)] == [(3000, 3150), (3100, 4100)]
    run_id = _json(r, "RUN_SUMMARY.json")["run_id"]
    assert all(a["stage"] == "synthesis" and a["run_id"] == run_id for a in (a0, a1))
    noi_dung = (r.ra / TEP_TRACE).read_text(encoding="utf-8")
    # Không đầu ra thô, không prompt: dấu vết riêng của cả hai ứng viên và của đề không có mặt.
    for vet in ("day khong phai json", "construct_plane_from_equation", de["C01"], "Đề bài:"):
        assert vet not in noi_dung, vet


# ══ B · qua JSON nhưng sai ở validator / thẩm định tĩnh / grounding ═════════════
@pytest.mark.parametrize("sua, phase, code", [
    (_schema, "PROGRAM_SCHEMA", "SCHEMA_UNION_TAG_INVALID"),
    (_type_check, "PROGRAM_TYPE_CHECK", None),
    (_ir_static, "IR_STATIC_CHECK", "IR_OPERAND_TYPE"),
    (_grounding, "GROUNDING_GATE", "INPUT_NOT_GROUNDED"),
])
def test_B_loi_nghiep_vu__phan_loai_KHAC_JSON__dung_cong__feedback_khop__luot_sau_nhan(kho, de, sua, phase, code):
    r = _chay_trace(kho, de, [_dot(sua), P1_PROG])
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    a0, a1 = _trace(r)["attempts"]
    assert a0["result"] == "REJECTED" and a0["rejection_phase"] == phase != "JSON_PARSE"
    if code is None:
        assert a0["rejection_code"].startswith("TYPE_CHECK_")
    else:
        assert a0["rejection_code"] == code
    assert a0["rejection_code"] in a0["feedback_codes"]
    assert a0["classification_matches_emitted_message"] is True
    assert a0["feedback_delivered_in_next_request"] is True
    assert 0 < len(a0["rejection_summary_redacted"]) <= 500
    assert a1["result"] == "ACCEPTED" and a1["repairs_logical_call"] == a0["logical_call"]


def test_B2_qua_vong_sua_nhung_ROUTE_hau_dieu_kien_chan__KHONG_feedback_gia(kho, de):
    r = _chay_trace(kho, de, [_dot(_hau_dieu_kien)])
    assert r.code == R.EXIT_CASE_FAIL
    t = _trace(r)
    (a0,) = t["attempts"]
    assert (a0["result"], a0["rejection_phase"], a0["rejection_code"]) == (
        "REJECTED", "ROUTE_POSTCONDITIONS", "postcondition_violated")
    assert a0["synthesis_loop_verdict"] == "PASSED"
    assert (a0["repair_attempted"], a0["feedback_sha256"], a0["feedback_codes"], a0["repaired_by_logical_call"]) == (
        False, None, [], None)
    assert t["links"] == [] and _json(r, "RUN_SUMMARY.json")["SYNTHESIS_HTTP_REQUESTS"] == 1


def test_B3_ma_TYPE_CHECK_ON_DINH_khi_ten_vat_doi__va_chuong_trinh_dung_khong_bi_gan_ma(de):
    c = build_request_contract(json.loads(P1["semantic_analyze"][0]), problem_text=de["C01"], domain=DOMAIN_HINH_HOC)
    k1 = R.phan_loai_ung_vien(_dot(_type_check), c)
    k2 = R.phan_loai_ung_vien(_dot(lambda d: d["statements"][5].__setitem__("vertices", ["A", "B", "C", "QQ9"])), c)
    assert k1["phase"] == k2["phase"] == "PROGRAM_TYPE_CHECK" and k1["code"] == k2["code"]
    assert R.phan_loai_ung_vien(P1_PROG, c)["phase"] is None
    assert R.phan_loai_ung_vien(_dot(lambda d: d["statements"][1].__setitem__("at", [0.5, 0, 0])), c)["code"] == \
        "IR_NOT_EXACT_RATIONAL"


# ══ C · lỗi provider ═════════════════════════════════════════════════════════
def test_C_loi_provider__PROVIDER_ERROR__khong_la_tu_choi_de__khong_feedback_gia(kho, de):
    r = _chay_trace(kho, de, [httpx.Response(503, json={"error": "qua tai"})])
    assert r.code == R.EXIT_CASE_FAIL
    t = _trace(r)
    (a0,) = t["attempts"]
    assert (a0["result"], a0["rejection_phase"], a0["rejection_code"]) == ("PROVIDER_ERROR", "PROVIDER", "PROVIDER_HTTP_503")
    assert a0["http_status"] == 503 and a0["candidate_sha256"] is None
    assert (a0["feedback_sha256"], a0["repaired_by_logical_call"], a0["repair_attempted"]) == (None, None, False)
    assert t["links"] == [] and "SAFE_REJECTION" not in json.dumps(t)


# ══ D · lượt được nhận ═══════════════════════════════════════════════════════
def test_D_luot_DUOC_NHAN__khong_ma_tu_choi_gia__hash_va_token_dung(kho, de):
    r = _chay_trace(kho, de, [_voi_token(P1_PROG, 2000, 400, 600)])
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    (a0,) = _trace(r)["attempts"]
    assert a0["result"] == "ACCEPTED"
    assert (a0["rejection_phase"], a0["rejection_code"], a0["rejection_summary_redacted"]) == (None, None, None)
    assert a0["candidate_sha256"] == _sha(P1_PROG) and a0["candidate_byte_count"] == len(P1_PROG.encode("utf-8"))
    assert a0["usage"] == {"promptTokenCount": 2000, "candidatesTokenCount": 400, "thoughtsTokenCount": 600,
                           "cachedContentTokenCount": None, "totalTokenCount": 3000}
    assert a0["http_status"] == 200 and isinstance(a0["latency_ms"], float)
    assert a0["repairs_logical_call"] is None and a0["synthesis_loop_verdict"] == "PASSED"


# ══ E · tính xác định ═════════════════════════════════════════════════════════
def test_E_hai_lan_chay_cung_fixture__trace_chuan_hoa_GIONG_tung_byte(kho, de):
    chuoi = [JSON_HONG, _dot(_grounding), P1_PROG]
    t1 = _trace(_chay_trace(kho, de, chuoi, ra=kho.tmp / "r1"))
    t2 = _trace(_chay_trace(kho, de, chuoi, ra=kho.tmp / "r2"))
    assert t1["run_id"] != t2["run_id"]
    assert R.trace_chuan_hoa(t1) == R.trace_chuan_hoa(t2)
    assert [a["candidate_sha256"] for a in t1["attempts"]] == [a["candidate_sha256"] for a in t2["attempts"]]
    assert [a["feedback_sha256"] for a in t1["attempts"]] == [a["feedback_sha256"] for a in t2["attempts"]]
    assert [a["result"] for a in t1["attempts"]] == ["REJECTED", "REJECTED", "ACCEPTED"]


# ══ F · bật quan trắc KHÔNG đổi hành vi ══════════════════════════════════════
def test_F_runner__co_va_khong_co_trace__cung_request_cung_envelope(kho, de):
    chuoi = [JSON_HONG, _dot(_grounding), P1_PROG]
    tat = _chay(kho, "C01", kich_ban=_kich_ban(de, {("C01", "synthesis"): list(chuoi)}), ra=kho.tmp / "tat")
    bat = _chay_trace(kho, de, chuoi, ra=kho.tmp / "bat")
    assert tat.code == bat.code == R.EXIT_PASS, (tat.err, bat.err)
    assert not (tat.ra / TEP_TRACE).exists(), "mặc định KHÔNG ghi trace"
    tt_tat, tt_bat = _json(tat, "RUN_SUMMARY.json"), _json(bat, "RUN_SUMMARY.json")
    assert (tt_tat["SYNTHESIS_REPAIR_TRACE"], tt_bat["SYNTHESIS_REPAIR_TRACE"]) == ("DISABLED", "ENABLED")
    assert _json(tat, "C01_ENVELOPE.json") == _json(bat, "C01_ENVELOPE.json")
    than = lambda r: [(x["stage"], x["body_sha256"]) for x in _json(r, "PROVIDER_CALLS.json")["records"]]  # noqa: E731
    assert than(tat) == than(bat), "prompt từng lượt — kể cả feedback gửi sang lượt sửa — phải trùng từng byte"
    for k in ("SYNTHESIS_HTTP_REQUESTS", "HTTP_REQUESTS_SENT", "AUTOMATED_CHECKS", "RETRIES"):
        assert tt_tat[k] == tt_bat[k], k


def _chay_route(text: str, dap: dict[str, list[str]], observer):
    ban = {k: list(v) for k, v in dap.items()}

    def tra(_req):
        return R._phan_hoi_gemini(ban[current_stage()].pop(0))

    cong = R.CongHttp(httpx.MockTransport(tra), 20, R.BoKhuBiMat())
    cong.dat_ca("PARITY")
    with R.dung_ngan_sach(R.tao_ngan_sach_nghiem_thu()), R.cai_cong_http(cong):
        o = asyncio.run(pipeline._semantic_route_attempt(text, {}, "khoa-gia", observer, domain=DOMAIN_HINH_HOC))
    return o, [(x["stage"], x["body_sha256"]) for x in cong.records]


def test_F2_pipeline__final_memory_chuong_trinh_so_luot_GIONG_khi_co_observer(de):
    dap = {"semantic_analyze": list(P1["semantic_analyze"]),
           "semantic_program": [JSON_HONG, _dot(_grounding), P1_PROG]}
    o0, b0 = _chay_route(de["C01"], dap, None)
    q = R.QuanTracVongSua()
    o1, b1 = _chay_route(de["C01"], dap, q)
    assert b0 == b1 and sum(1 for s, _ in b0 if s == "synthesis") == 3
    assert (o0.stage_reached, o0.executable, o0.servable, o0.error_code) == (
        o1.stage_reached, o1.executable, o1.servable, o1.error_code) == ("served", True, True, None)
    assert AV.trich_ket_qua(o0) == AV.trich_ket_qua(o1)
    assert o0.scene3d == o1.scene3d
    assert [t for t, _ in q.su_kien].count("semantic_program_candidate") == 3


# ══ G · cách ly phiên ════════════════════════════════════════════════════════
def test_G_hai_pipeline_SONG_SONG_khong_tron_su_kien_hay_lien_ket(de):
    p6 = RNB.doc_raw_theo_thu_tu(CA_P6)
    theo_de = {
        de["C01"]: {"semantic_analyze": list(P1["semantic_analyze"]), "semantic_program": [JSON_HONG, P1_PROG]},
        de["C02"]: {"semantic_analyze": list(p6["semantic_analyze"]), "semantic_program": list(p6["semantic_program"])},
    }

    def tra(req):
        tin = json.loads(req.content)["contents"][0]["parts"][-1]["text"]
        khoa = next(k for k in theo_de if k in tin)
        return R._phan_hoi_gemini(theo_de[khoa][current_stage()].pop(0))

    cong = R.CongHttp(httpx.MockTransport(tra), 20, R.BoKhuBiMat())
    cong.dat_ca("G")
    qa, qb = R.QuanTracVongSua(), R.QuanTracVongSua()

    async def ca_hai():
        return await asyncio.gather(
            pipeline._semantic_route_attempt(de["C01"], {}, "k", qa, domain=DOMAIN_HINH_HOC),
            pipeline._semantic_route_attempt(de["C02"], {}, "k", qb, domain=DOMAIN_HINH_HOC))

    with R.dung_ngan_sach(gemini.ApiBudget(max_attempts=1)), R.cai_cong_http(cong):
        oa, ob = asyncio.run(ca_hai())
    assert oa.servable and ob.servable

    def ung_vien(q):
        return [(d["n"], _sha(d["raw"])) for t, d in q.su_kien if t == "semantic_program_candidate"]

    assert ung_vien(qa) == [(0, _sha(JSON_HONG)), (1, _sha(P1_PROG))]
    assert ung_vien(qb) == [(0, _sha(p6["semantic_program"][0]))]
    assert R.lien_ket_sua(qa) == [(0, 1)] and R.lien_ket_sua(qb) == []


# ══ H · che bí mật ═══════════════════════════════════════════════════════════
def test_H_bi_mat_trong_ly_do_tu_choi_bi_CHE__may_quet_BAT_duoc_khi_bo_che(kho, de, monkeypatch):
    bearer = _dot(lambda d: d["memory_declarations"].extend(
        [{"name": "Authorization: Bearer TOKEN-AUTH-555", "type": "float"}] * 2))
    url_khoa = _dot(lambda d: d["statements"][5].__setitem__(
        "vertices", ["A", "B", "C", f"https://x.test/cb?key=QUERYKEY-999&k={KHOA_GIA}"]))
    chuoi = [bearer, url_khoa, P1_PROG]

    def quet(r) -> list[str]:
        noi_dung = (r.ra / TEP_TRACE).read_text(encoding="utf-8")
        return [s for s in BI_MAT if s in noi_dung]

    r = _chay_trace(kho, de, chuoi)
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    t = _trace(r)
    assert [a["result"] for a in t["attempts"]] == ["REJECTED", "REJECTED", "ACCEPTED"]
    assert [a["rejection_phase"] for a in t["attempts"][:2]] == ["PROGRAM_TYPE_CHECK", "PROGRAM_TYPE_CHECK"]
    assert quet(r) == []
    # Cửa sổ chứng: thông điệp chở bí mật THẬT SỰ đã tới trace, và đã bị che.
    assert all(R.REDACTED in a["rejection_summary_redacted"] for a in t["attempts"][:2])

    # Bỏ che ⇒ máy quét phải bắt được — không thì "sạch" ở trên là rỗng nghĩa.
    monkeypatch.setattr(R.BoKhuBiMat, "chuoi", lambda self, s: s)
    r2 = _chay_trace(kho, de, chuoi, ra=kho.tmp / "khong_che")
    assert {"TOKEN-AUTH-555", "QUERYKEY-999", KHOA_GIA} <= set(quet(r2))
