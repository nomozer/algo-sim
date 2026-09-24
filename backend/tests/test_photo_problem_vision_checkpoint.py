# -*- coding: utf-8 -*-
"""TIẾP TỤC TỪ CHECKPOINT ĐỌC ẢNH — `run_photo_problem_live.py --vision-checkpoint`. 0 request mạng.

`C01_DOWNSTREAM_CHECKPOINT_ACCEPTANCE` (2026-09-14). Một lượt đọc ảnh THẬT đã thành công và được
lưu (`VISION_LIVE_RESULT_REDACTED.json` của `GEMINI_VISION_SCHEMA_COMPATIBILITY_FIX`). Chế độ này
dùng lại đúng bản ghi ấy để đo tầng B mà KHÔNG gọi lại vision — và vì thế nó phải chứng minh ba
điều mà chế độ thường không cần:

  ① checkpoint là của ĐÚNG ảnh · đúng prompt · đúng hai lược đồ · đúng model · đúng ground truth,
    và bản ghi vẫn qua Pydantic ĐẦY ĐỦ hiện tại — sai một thứ ⇒ `CHECKPOINT_PROVENANCE_FAILED`,
    0 request;
  ② tầng vision KHÔNG THỂ được gọi: không đường mã nào tới `extract_problem_from_image`, và cổng
    HTTP chặn tầng vision với trần 0;
  ③ văn bản đi vào analyze là văn bản CỦA CHECKPOINT (bản xem lại), không phải ground truth.

Provider giả đứng ở ranh giới HTTP như `test_photo_problem_live_runner.py`; tầng B phát lại byte
đóng băng p1 của lượt `thesis-final`.
"""

from __future__ import annotations

import asyncio
import hashlib
import json

import httpx
import pytest

from app.ai import gemini
from app.ai.telemetry import stage_scope
from app.ingestion import image_extraction as ie
from app.ingestion.image import normalize_image
from tests.test_photo_problem_live_runner import (  # noqa: F401 — fixture `de`, `kho` dùng qua tên
    BI_MAT,
    CA_P1,
    R,
    RNB,
    _anh,
    _ban_ghi,
    _ca,
    _chay,
    _json,
    _kich_ban,
    _than_chua_bi_mat,
    _vision_dung,
    de,
    kho,
)

HAI_TANG_B = [("C01", "analyze"), ("C01", "synthesis")]
_XOA = object()


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


def _checkpoint(kho, ban_ghi: str, **thay) -> dict:
    """Checkpoint hợp lệ cho ảnh C01 của `kho`, dựng từ danh tính HIỆN TẠI của mã sản phẩm."""
    goc = (kho.anh / "C01.png").read_bytes()
    x = ie.parse_extraction(ban_ghi)
    cp = {
        "wave": "GEMINI_VISION_SCHEMA_COMPATIBILITY_FIX",
        "git_head": "0" * 40,
        "VISION_MODEL": gemini.MODEL,
        "PROMPT_SHA256": _sha(gemini.load_skill(ie.VISION_PROMPT_SKILL)),
        "FULL_SCHEMA_SHA256": ie.VISION_RESPONSE_SCHEMA_SHA256,
        "TRANSPORT_SCHEMA_SHA256": ie.VISION_TRANSPORT_SCHEMA_SHA256,
        "VISION_SCHEMA_IDENTITY": ie.VISION_SCHEMA_IDENTITY,
        "c01_sha256_at_request": _sha(goc),
        "normalized_image_sha256": normalize_image(goc).sha256,
        "gt_file_sha256_at_request": _sha(kho.gt.read_bytes()),
        "VISION_HTTP_STATUS": 200,
        "VISION_HTTP_REQUESTS": 1,
        "RETRIES": 0,
        "JSON_PARSE_RESULT": "PASS",
        "PYDANTIC_VALIDATION_RESULT": "PASS",
        "VISION_RESULT": "PASS",
        "usage_metadata": {"promptTokenCount": 806, "candidatesTokenCount": 547,
                           "thoughtsTokenCount": 964, "totalTokenCount": 2317},
        "extraction": x.model_dump(),
        "assessment": ie.assess_extraction(x).to_dict(),
    }
    for k, v in thay.items():
        if v is _XOA:
            cp.pop(k)
        else:
            cp[k] = v
    return cp


def _ghi_cp(kho, cp: dict, ten: str = "CHECKPOINT.json"):
    p = kho.tmp / ten
    p.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _chay_cp(kho, p, *them, kich_ban, ra=None, **kw):
    return _chay(kho, "C01", "--vision-checkpoint", str(p), "--max-http-requests", "4", *them,
                 kich_ban=kich_ban, ra=ra, **kw)


def _tu_choi_truoc_request(r, ma: str):
    assert r.code == R.EXIT_USAGE, (r.out, r.err)
    assert "CHECKPOINT_PROVENANCE_FAILED" in r.err and ma in r.err, r.err
    assert r.cong is None, "không được dựng cổng HTTP — chưa có request nào được phép"
    assert not r.ra.exists() or not any(r.ra.iterdir())


# ══ K1 · CHECKPOINT HỢP LỆ ═════════════════════════════════════════════════
def test_K01_checkpoint_HOP_LE__0_vision__tang_B_chay__nhan_AUTOMATED_khong_phai_HUMAN(kho, de):
    cp = _checkpoint(kho, _vision_dung(de, "C01"))
    p = _ghi_cp(kho, cp)
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    assert r.prov.calls == HAI_TANG_B
    tt = _json(r, "RUN_SUMMARY.json")
    assert (tt["VISION_HTTP_REQUESTS"], tt["ANALYZE_HTTP_REQUESTS"], tt["SYNTHESIS_HTTP_REQUESTS"]) == (0, 1, 1)
    assert (tt["VISION_SOURCE"], tt["RUN_KIND"]) == ("CHECKPOINT", "DOWNSTREAM_FROM_VISION_CHECKPOINT")
    assert tt["SINGLE_RUN_END_TO_END"] == "NOT_RUN"
    prov = tt["VISION_CHECKPOINT"]
    assert prov["CHECKPOINT_FILE_SHA256"] == _sha(p.read_bytes())
    assert prov["CHECKPOINT_EXTRACTION_SHA256"] == _sha(ie.canonical_json_bytes(cp["extraction"]))
    assert prov["CHECKPOINT_PROVENANCE"] == "PASS" and prov["GROUND_TRUTH_BINDING"] == "DIRECT"
    raw = _json(r, "C01_RAW_EXTRACTION.json")
    assert raw["VISION_SOURCE"] == "CHECKPOINT" and raw["http"] == []
    assert raw["extraction"] == cp["extraction"]
    xn = _json(r, "C01_CONFIRMED_INPUT.json")
    assert xn["REVIEW_KIND"] == xn["CONFIRMATION_SOURCE"] == "AUTOMATED_CHECKPOINT_REPLAY"
    assert tt["REVIEW_KIND"] == "AUTOMATED_CHECKPOINT_REPLAY"
    assert tt["HUMAN_CRITICAL_FACT_REVIEW"] == "PENDING"
    for f in r.ra.iterdir():
        noi_dung = f.read_text(encoding="utf-8")
        assert '"REVIEW_KIND": "HUMAN"' not in noi_dung and "HUMAN_EDIT" not in noi_dung, f.name


def test_K01b_ground_truth_RUN_ENVELOPE_gan_qua_derived_from_duoc_nhan(kho, de):
    goc = json.loads(kho.gt.read_text(encoding="utf-8"))
    nguon = "f" * 64
    kho.gt.write_text(json.dumps({**goc, "derived_from_ground_truth_sha256": nguon}, ensure_ascii=False),
                      encoding="utf-8")
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01"), gt_file_sha256_at_request=nguon))
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    assert _json(r, "RUN_SUMMARY.json")["VISION_CHECKPOINT"]["GROUND_TRUTH_BINDING"] == "DERIVED_FROM_DECLARED"


# ══ K2–K5 · NGUỒN GỐC SAI ⇒ DỪNG TRƯỚC REQUEST ═══════════════════════════════
def test_K02_sai_bam_C01__checkpoint_cua_ANH_KHAC_bi_chan(kho, de):
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01")))
    (kho.anh / "C01.png").write_bytes(_anh((10, 20, 30)))
    _tu_choi_truoc_request(_chay_cp(kho, p, kich_ban=_kich_ban(de)), "c01_sha256_at_request")


@pytest.mark.parametrize("truong, gia_tri", [
    ("VISION_MODEL", "gemini-2.5-pro"),
    ("PROMPT_SHA256", "0" * 64),
    ("FULL_SCHEMA_SHA256", "0" * 64),
    ("TRANSPORT_SCHEMA_SHA256", "0" * 64),
    ("VISION_SCHEMA_IDENTITY", "photo-problem-extraction/1"),
    ("normalized_image_sha256", "0" * 64),
    ("gt_file_sha256_at_request", "0" * 64),
    ("VISION_HTTP_STATUS", 400),
    ("VISION_RESULT", "SCHEMA_REJECTED"),
    ("JSON_PARSE_RESULT", "FAIL"),
    ("PYDANTIC_VALIDATION_RESULT", "NOT_REACHED"),
    ("VISION_HTTP_REQUESTS", 2),
    ("RETRIES", 1),
    ("PROMPT_SHA256", _XOA),
    ("assessment", _XOA),
])
def test_K03_sai_danh_tinh_model_prompt_luoc_do_hay_ket_qua_bi_chan(kho, de, truong, gia_tri):
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01"), **{truong: gia_tri}))
    _tu_choi_truoc_request(_chay_cp(kho, p, kich_ban=_kich_ban(de)), truong)


def _ban_ghi_sua(de, **thay) -> dict:
    d = json.loads(_vision_dung(de, "C01"))
    d.update(thay)
    return d


@pytest.mark.parametrize("ten, sua", [
    ("confidence_1_5", lambda d: {**d, "confidence": 1.5}),
    ("named_points_81", lambda d: {**d, "named_points": [f"P{i}" for i in range(81)]}),
    ("truong_thua", lambda d: {**d, "provider_tu_them": True}),
    ("thieu_truong", lambda d: {k: v for k, v in d.items() if k != "missing_regions"}),
])
def test_K04_extraction_KHONG_qua_Pydantic_DAY_DU_bi_chan(kho, de, ten, sua):
    cp = _checkpoint(kho, _vision_dung(de, "C01"))
    cp["extraction"] = sua(cp["extraction"])
    _tu_choi_truoc_request(_chay_cp(kho, _ghi_cp(kho, cp), kich_ban=_kich_ban(de)), "extraction")


def test_K05_phan_quyet_bi_THAY_bang_ground_truth_bi_chan(kho, de):
    cp = _checkpoint(kho, _vision_dung(de, "C01"))
    gt = json.loads(kho.gt.read_text(encoding="utf-8"))["cases"][0]["expected_text"]
    cp["assessment"] = {**cp["assessment"], "problem_text": gt + " "}
    _tu_choi_truoc_request(_chay_cp(kho, _ghi_cp(kho, cp), kich_ban=_kich_ban(de)), "assessment")


def test_K05b_payload_analyze_la_VAN_BAN_CHECKPOINT_khong_phai_ground_truth(kho, de):
    doc = de["C01"].replace("Oxyz, cho", "Oxyz cho")
    assert doc != de["C01"]
    ban = json.loads(_vision_dung(de, "C01"))
    ban.update(problem_text_verbatim=doc, problem_text_normalized=doc)
    p = _ghi_cp(kho, _checkpoint(kho, json.dumps(ban, ensure_ascii=False)))
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    than = r.cong.van_ban_analyze["C01"]
    assert len(than) == 1 and f'"""\n{doc}\n"""' in than[0] and f'"""\n{de["C01"]}\n"""' not in than[0]
    c01 = _ca(_json(r, "RUN_SUMMARY.json"), "C01")
    assert c01["ANALYZE_PAYLOAD_TEXT_SHA256"] == [_sha(doc)] != [_sha(de["C01"])]


# ══ K6 · TẦNG VISION KHÔNG THỂ ĐƯỢC GỌI ══════════════════════════════════════
def test_K06_che_do_checkpoint_KHONG_THE_goi_vision(kho, de, monkeypatch):
    # (a) Không đường mã nào tới hàm đọc ảnh — kể cả phép dò chính sách thử lại trước lượt chạy.
    goi: list[str] = []

    async def cam(*_a, **_k):
        goi.append("extract_problem_from_image")
        raise AssertionError("chế độ checkpoint gọi tầng vision")

    monkeypatch.setattr(ie, "extract_problem_from_image", cam)
    kb = _kich_ban(de)  # kịch bản CÓ SẴN phản hồi vision đúng — 0 lượt là do bị cấm, không do hết kịch bản
    r = _chay_cp(kho, _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01"))), kich_ban=kb)
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    assert goi == [] and ("C01", "vision") not in r.prov.calls
    assert r.cong.tran_theo_tang == {"vision": 0, "analyze": 1, "synthesis": 3}
    assert _json(r, "RUN_SUMMARY.json")["RETRY_POLICY_PROBE"] == {"analyze": 1, "synthesis": 1}
    monkeypatch.undo()

    # (b) Cổng: trần tầng vision = 0 ⇒ request vision bị chặn TRƯỚC transport.
    trong = {"n": 0}

    def tra(_req):
        trong["n"] += 1
        return R._phan_hoi_gemini(_vision_dung(de, "C01"))

    cong = R.CongHttp(httpx.MockTransport(tra), 4, R.BoKhuBiMat(), tran_theo_tang=dict(R.TRAN_THEO_TANG_CHECKPOINT))
    cong.dat_ca("C01")
    anh = normalize_image((kho.anh / "C01.png").read_bytes())
    with R.dung_ngan_sach(R.tao_ngan_sach_nghiem_thu()), R.cai_cong_http(cong), \
            pytest.raises(R.HttpBudgetExceeded, match="STAGE_BUDGET_EXHAUSTED"):
        asyncio.run(ie.extract_problem_from_image(anh, "khoa-gia", cache_version=None))
    assert trong["n"] == 0 == cong.inner_invocations and cong.blocked_by_stage["vision"] == 1


def test_K06b_tran_THEO_TANG_chan_luot_analyze_thu_hai():
    cong = R.CongHttp(httpx.MockTransport(lambda _r: R._phan_hoi_gemini("{}")), 4, R.BoKhuBiMat(),
                      tran_theo_tang={"vision": 0, "analyze": 1, "synthesis": 3})
    cong.dat_ca("C01")

    async def hai_luot():
        for _ in range(2):
            with stage_scope("semantic_analyze"):
                await gemini.call_gemini("khoa-gia", "system", "lượt analyze")

    with R.dung_ngan_sach(R.tao_ngan_sach_nghiem_thu()), R.cai_cong_http(cong), \
            pytest.raises(R.HttpBudgetExceeded, match="STAGE_BUDGET_EXHAUSTED"):
        asyncio.run(hai_luot())
    assert (cong.sent, cong.blocked, cong.inner_invocations) == (1, 1, 1)


# ══ K7 · NGANG BẰNG VĂN BẢN XEM LẠI ↔ PAYLOAD ANALYZE ════════════════════════
def test_K07_ngang_bang_payload__khong_sua_va_co_sua(kho, de):
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01")))
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de))
    c01 = _ca(_json(r, "RUN_SUMMARY.json"), "C01")
    xn = _json(r, "C01_CONFIRMED_INPUT.json")
    assert xn["REVIEW_TEXT_SHA256"] == xn["CONFIRMED_TEXT_SHA256"] == _sha(de["C01"])
    assert c01["ANALYZE_PAYLOAD_TEXT_SHA256"] == [xn["CONFIRMED_TEXT_SHA256"]]
    assert c01["REVIEW_PAYLOAD_PARITY"] is True

    sua = de["C01"].replace("Oxyz, cho", "Oxyz cho")
    ban_sua = kho.tmp / "xac_nhan.json"
    ban_sua.write_text(json.dumps({"C01": sua}, ensure_ascii=False), encoding="utf-8")
    r2 = _chay_cp(kho, p, "--confirmed-text", str(ban_sua), kich_ban=_kich_ban(de), ra=kho.tmp / "ra2")
    c2 = _ca(_json(r2, "RUN_SUMMARY.json"), "C01")
    xn2 = _json(r2, "C01_CONFIRMED_INPUT.json")
    assert (xn2["EDITED"], xn2["CONFIRMED_TEXT_SHA256"]) == (True, _sha(sua))
    assert xn2["REVIEW_TEXT_SHA256"] == _sha(de["C01"])
    assert c2["ANALYZE_PAYLOAD_TEXT_SHA256"] == [_sha(sua)] and c2["REVIEW_PAYLOAD_PARITY"] is True


def test_K07b_ngang_bang_payload_DO_duoc_khi_lech():
    boc = lambda t: f'Đề bài:\n"""\n{t}\n"""'  # noqa: E731
    assert R.van_ban_trong_than_analyze(boc("đề A")) == "đề A"
    assert R.van_ban_trong_than_analyze("không đúng khuôn") is None
    dung = R.kiem_ngang_bang_payload("đề A", "đề A", [boc("đề A")])
    assert dung["REVIEW_PAYLOAD_PARITY"] is True
    assert R.kiem_ngang_bang_payload("đề A", "đề A", [boc("đề B")])["REVIEW_PAYLOAD_PARITY"] is False
    assert R.kiem_ngang_bang_payload("đề A", "đề A", [])["REVIEW_PAYLOAD_PARITY"] is False
    # Người sửa: payload phải là bản SỬA; gửi bản xem lại chưa sửa là lệch.
    assert R.kiem_ngang_bang_payload("đề A", "đề A2", [boc("đề A2")])["REVIEW_PAYLOAD_PARITY"] is True
    assert R.kiem_ngang_bang_payload("đề A", "đề A2", [boc("đề A")])["REVIEW_PAYLOAD_PARITY"] is False


# ══ K8 · CHƯA XÁC NHẬN / BỊ TỪ CHỐI ⇒ ANALYZE KHÔNG CHẠY ═════════════════════
def test_K08_checkpoint_BI_TU_CHOI_thi_analyze_KHONG_chay(kho, de):
    p = _ghi_cp(kho, _checkpoint(kho, _ban_ghi(co_hinh=True)))
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_CASE_FAIL
    assert r.prov.calls == [] and r.cong.sent == 0
    assert any("VISION_REJECTED" in x for x in _ca(_json(r, "RUN_SUMMARY.json"), "C01")["fail_reasons"])


def test_K08b_can_XAC_NHAN_ma_chua_co_ban_xac_nhan_thi_analyze_KHONG_chay(kho, de):
    ban = json.loads(_vision_dung(de, "C01"))
    ban["uncertain_tokens"] = [{"token": "3", "alternatives": ["8"], "location": "z = 3", "reason": "nét mờ"}]
    p = _ghi_cp(kho, _checkpoint(kho, json.dumps(ban, ensure_ascii=False)))
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_CASE_FAIL
    assert r.prov.calls == []
    assert "REVIEW_CONFIRMATION_REQUIRED" in _ca(_json(r, "RUN_SUMMARY.json"), "C01")["fail_reasons"]
    # Có bản xác nhận ⇒ dựng được.
    xn = kho.tmp / "xac_nhan.json"
    xn.write_text(json.dumps({"C01": de["C01"]}, ensure_ascii=False), encoding="utf-8")
    r2 = _chay_cp(kho, p, "--confirmed-text", str(xn), kich_ban=_kich_ban(de), ra=kho.tmp / "ra2")
    assert r2.code == R.EXIT_PASS, (r2.out, r2.err)
    assert _json(r2, "C01_CONFIRMED_INPUT.json")["REVIEW_KIND"] == "AUTOMATED_CHECKPOINT_REPLAY_WITH_CONFIRMED_TEXT_FILE"


# ══ K9 · NGÂN SÁCH ≤ 4 VÀ PHÂN LOẠI LỖI TẦNG B ═══════════════════════════════
def test_K09_tran_HTTP_checkpoint_KHONG_vuot_4(kho, de):
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01")))
    r = _chay(kho, "C01", "--vision-checkpoint", str(p), "--max-http-requests", "5", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_USAGE and r.cong is None and "4" in r.err


@pytest.mark.parametrize("kieu, mong, gui", [
    ("analyze_503", "ANALYZE_PROVIDER_ERROR", {"analyze": 1, "synthesis": 0}),
    ("analyze_json_hong", "ANALYZE_OUTPUT_INVALID", {"analyze": 1, "synthesis": 0}),
    ("synthesis_503", "SYNTHESIS_PROVIDER_ERROR", {"analyze": 1, "synthesis": 1}),
    ("synthesis_het_luot_sua", "SYNTHESIS_REPAIR_EXHAUSTED", {"analyze": 1, "synthesis": 3}),
])
def test_K10_loi_tang_B_duoc_PHAN_LOAI_va_KHONG_la_tu_choi_an_toan(kho, de, kieu, mong, gui):
    hong = "{ day khong phai json"
    thay = {
        "analyze_503": {("C01", "analyze"): [httpx.Response(503, json={"error": "qua tai"})]},
        "analyze_json_hong": {("C01", "analyze"): [hong]},
        "synthesis_503": {("C01", "synthesis"): [httpx.Response(503, json={"error": "qua tai"})]},
        "synthesis_het_luot_sua": {("C01", "synthesis"): [hong] * 4},
    }[kieu]
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01")))
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de, thay))
    assert r.code == R.EXIT_CASE_FAIL
    tt = _json(r, "RUN_SUMMARY.json")
    c01 = _ca(tt, "C01")
    assert c01["DOWNSTREAM_FAILURE_CLASS"] == mong
    assert {"analyze": tt["ANALYZE_HTTP_REQUESTS"], "synthesis": tt["SYNTHESIS_HTTP_REQUESTS"]} == gui
    assert (tt["VISION_HTTP_REQUESTS"], tt["RETRIES"], tt["HTTP_REQUESTS_SENT"]) == (0, 0, sum(gui.values()))
    assert tt["HTTP_REQUESTS_SENT"] <= 4
    assert "SAFE_REJECTION" not in json.dumps(c01, ensure_ascii=False)


# ══ K11 · SECRET ════════════════════════════════════════════════════════════
def test_K11_secret_KHONG_lot_trong_che_do_checkpoint(kho, de, capsys):
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01")))
    r = _chay_cp(kho, p, kich_ban=_kich_ban(de, {("C01", "analyze"): [httpx.Response(403, text=_than_chua_bi_mat())]}))
    assert r.code == R.EXIT_CASE_FAIL
    cap = capsys.readouterr()
    be_mat = {"stdout": r.out, "stderr": r.err, "capsys": cap.out + cap.err}
    be_mat.update({f.name: f.read_text(encoding="utf-8") for f in sorted(r.ra.iterdir())})
    ro = sorted({(ten, s[:6]) for ten, nd in be_mat.items() for s in BI_MAT if s in nd})
    assert ro == [], f"secret lọt: {ro}"
    assert "MARKER-DA-TOI" in be_mat["RUN_SUMMARY.json"]


# ══ K12 · TOKEN THEO TẦNG ═══════════════════════════════════════════════════
def _voi_token(van_ban: str, prompt: int, cand: int, nghi: int) -> httpx.Response:
    return httpx.Response(200, json={
        "candidates": [{"content": {"parts": [{"text": van_ban}]}}],
        "usageMetadata": {"promptTokenCount": prompt, "candidatesTokenCount": cand, "thoughtsTokenCount": nghi,
                          "totalTokenCount": prompt + cand + nghi,
                          "promptTokensDetails": [{"modality": "TEXT", "tokenCount": prompt}]},
        "modelVersion": "gemini-2.5-flash", "responseId": "khong-duoc-ghi"})


def test_K12_token_ghi_THEO_TUNG_REQUEST_va_tach_PRIOR_voi_NEW(kho, de):
    p1 = RNB.doc_raw_theo_thu_tu(CA_P1)
    kb = _kich_ban(de, {("C01", "analyze"): [_voi_token(p1["semantic_analyze"][0], 1000, 200, 300)],
                        ("C01", "synthesis"): [_voi_token(p1["semantic_program"][0], 2000, 400, 600)]})
    r = _chay_cp(kho, _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01"))), kich_ban=kb)
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    theo_req = tt["TOKENS_BY_REQUEST"]
    assert [(x["stage"], x["logical_call"], x["attempt"], x["http_status"]) for x in theo_req] == [
        ("analyze", 1, 1, 200), ("synthesis", 2, 1, 200)]
    assert theo_req[0]["usage_metadata"]["promptTokensDetails"] == [{"modality": "TEXT", "tokenCount": 1000}]
    assert "responseId" not in json.dumps(theo_req) and '"candidates"' not in json.dumps(theo_req)
    assert tt["TOKENS_BY_STAGE"]["analyze"]["totalTokenCount"] == 1500
    assert tt["TOKENS_BY_STAGE"]["synthesis"]["totalTokenCount"] == 3000
    assert (tt["PRIOR_VISION_TOKENS"], tt["NEW_ANALYZE_TOKENS"], tt["NEW_SYNTHESIS_TOKENS"]) == (2317, 1500, 3000)
    assert (tt["NEW_DOWNSTREAM_TOKENS"], tt["COMPOSITE_PIPELINE_TOKENS"]) == (4500, 6817)
    assert tt["REFERENCE_VISION_TOKENS_NOT_RESPENT"] == 2317


# ══ K13 · ENVELOPE ĐỦ ĐỂ PHÁT LẠI VÀ CHẤM ═══════════════════════════════════
def test_K13_envelope_duoc_GHI_nguyen_de_phat_lai_trinh_duyet(kho, de):
    r = _chay_cp(kho, _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01"))), kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    env = _json(r, "C01_ENVELOPE.json")
    assert env["status"] == "ok" and len(env["scene3d"]["objects"]) == _json(r, "C01_SCENE_RESULT.json")[
        "scene_object_count"] > 0


# ══ K14 · TỔ HỢP CỜ SAI ═════════════════════════════════════════════════════
@pytest.mark.parametrize("them", [
    ("--case", "all"),
    ("--case", "C03"),
    ("--dry-run",),
    ("--vision-checkpoint", "tuong-doi/CHECKPOINT.json"),
])
def test_K14_to_hop_co_SAI_bi_tu_choi_truoc_request(kho, de, them):
    p = _ghi_cp(kho, _checkpoint(kho, _vision_dung(de, "C01")))
    argv = ["--case", "C01", "--input-dir", str(kho.anh), "--ground-truth", str(kho.gt),
            "--output-dir", str(kho.ra), "--vision-checkpoint", str(p), "--max-http-requests", "4"]
    for i in range(0, len(them), 2):
        if them[i] in argv and i + 1 < len(them):
            argv[argv.index(them[i]) + 1] = them[i + 1]
        else:
            argv.extend(them[i:i + 2] if i + 1 < len(them) else them[i:i + 1])
    r = _chay(kho, "C01", kich_ban=_kich_ban(de), argv=argv)
    assert r.code == R.EXIT_USAGE and r.cong is None, (r.out, r.err)
