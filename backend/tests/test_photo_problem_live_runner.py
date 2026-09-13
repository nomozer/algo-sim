# -*- coding: utf-8 -*-
"""RUNNER NGHIỆM THU ẢNH ĐỀ BÀI — từng ca, trần HTTP cứng, CER, khử secret. 0 request mạng.

`PHOTO_PROBLEM_LIVE_RUNNER_HARDENING` §11 — test đánh số theo mười tám yêu cầu.

Provider giả đứng ĐÚNG ranh giới HTTP: nó là transport BÊN TRONG `CongHttp`
(`R.TransportKichBan`), không phải một bản thay `call_gemini`. Nên vòng thử lại của
`call_gemini`, `image_extraction`, pipeline, kernel và scene3d đều là mã sản phẩm
đang chạy, và cổng đếm đúng thứ nó sẽ đếm khi chạy thật. Tầng B phát lại byte đóng
băng của lượt `thesis-final` (p1 chóp + thiết diện, p6 trụ + elip).

⚠️ Không test nào ở đây chứng minh provider thật đọc được ảnh chụp thật.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image

from app.ai import gemini
from app.ai.telemetry import stage_scope
from app.ingestion import image_extraction as ie
from app.ingestion.image import normalize_image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import replay_negative_boundaries as RNB  # noqa: E402
import run_photo_problem_live as R  # noqa: E402

CA_P1 = "p1_chop_thiet_dien_khoang_cach"
CA_P6 = "p6_thiet_dien_elip_cua_hinh_tru"
#: Secret GIẢ — không khớp mẫu khoá Google (thiếu độ dài), không bao giờ được lọt ra.
KHOA_GIA = "AIzaSyFAKE-SECRET-0123456789abcdef"
BI_MAT = (KHOA_GIA, "TOKEN-KHAC-987", "TOKEN-AUTH-555", "COOKIE-777", "QUERYKEY-999")
ENV_LIVE = {"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": KHOA_GIA}
TRU = "−"  # dấu trừ Unicode, đúng như đề p6
DUOI_ANH = {".png", ".jpg", ".jpeg", ".webp"}
BA_TANG_C01 = [("C01", "vision"), ("C01", "analyze"), ("C01", "synthesis")]


# ══ NỀN ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def de() -> dict[str, str]:
    d = RNB.doc_de_bai()
    return {"C01": d[CA_P1], "C02": d[CA_P6]}


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    """Lượt thử lại (nếu có) không được làm test chậm — SỐ lần thử vẫn nguyên."""
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


def _gt(de: dict[str, str]) -> dict:
    return {"cases": [
        {"case_id": "C01", "expected_text": de["C01"], "critical_facts": {
            "point_labels": ["S", "A", "B", "C", "D"], "formulas": ["z = 3"], "objects": ["S.ABCD"],
            "relations": [["ABCD là hình vuông", "đáy ABCD là hình vuông"]],
            "request": "khoảng cách từ điểm S đến đường thẳng BD"}},
        {"case_id": "C02", "expected_text": de["C02"], "critical_facts": {
            "point_labels": ["O", "K", "A"], "formulas": [f"2x {TRU} z + 12 = 0"], "objects": [],
            "relations": [], "request": "Tính diện tích hình elip (E)"}},
        {"case_id": "C03", "expected_outcome": "SAFE_REJECTION"},
    ]}


def _anh(mau, dinh_dang="PNG") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (96, 64), mau).save(buf, format=dinh_dang)
    return buf.getvalue()


@pytest.fixture
def kho(tmp_path, de):
    anh = tmp_path / "anh"
    anh.mkdir()
    for cid, mau in (("C01", (250, 250, 250)), ("C02", (225, 235, 255)), ("C03", (255, 235, 225))):
        (anh / f"{cid}.png").write_bytes(_anh(mau))
    gt = tmp_path / "GROUND_TRUTH.json"
    gt.write_text(json.dumps(_gt(de), ensure_ascii=False), encoding="utf-8")
    return SimpleNamespace(tmp=tmp_path, anh=anh, gt=gt, ra=tmp_path / "ra")


def _ban_ghi(text="", diem=(), cong_thuc=(), khoi=(), quan_he=(), co_hinh=False) -> str:
    return json.dumps({
        "problem_text_verbatim": text, "problem_text_normalized": text,
        "math_expressions": [{"verbatim": f, "normalized": f} for f in cong_thuc],
        "named_points": list(diem), "named_lines": [], "named_planes": [], "named_solids": list(khoi),
        "given_relations": list(quan_he), "has_diagram": co_hinh,
        "diagram_observations": ["Chỉ có hình vẽ."] if co_hinh else [],
        "text_diagram_conflicts": [], "uncertain_tokens": [], "missing_regions": [], "confidence": 0.95,
    }, ensure_ascii=False)


def _vision_dung(de, cid) -> str:
    if cid == "C01":
        return _ban_ghi(de["C01"], "SABCD", ["z = 3"], ["S.ABCD"], ["ABCD là hình vuông"])
    if cid == "C02":
        return _ban_ghi(de["C02"], "OKA", [f"2x {TRU} z + 12 = 0"])
    return _ban_ghi(co_hinh=True)


def _kich_ban(de, thay: dict | None = None) -> dict:
    p1, p6 = RNB.doc_raw_theo_thu_tu(CA_P1), RNB.doc_raw_theo_thu_tu(CA_P6)
    kb = {
        ("C01", "vision"): [_vision_dung(de, "C01")],
        ("C01", "analyze"): p1["semantic_analyze"],
        ("C01", "synthesis"): p1["semantic_program"],
        ("C02", "vision"): [_vision_dung(de, "C02")],
        ("C02", "analyze"): p6["semantic_analyze"],
        ("C02", "synthesis"): p6["semantic_program"],
        ("C03", "vision"): [_vision_dung(de, "C03")],
    }
    kb.update(thay or {})
    return kb


def _args(kho, case, *them, ra=None) -> list[str]:
    return ["--case", case, "--input-dir", str(kho.anh), "--ground-truth", str(kho.gt),
            "--output-dir", str(ra or kho.ra), *them]


def _chay(kho, case, *them, kich_ban, env=ENV_LIVE, ra=None, argv=None):
    ra = ra or kho.ra
    giu: dict = {}

    def nha_may(cong):
        giu["cong"] = cong
        giu["prov"] = R.TransportKichBan(cong, kich_ban)
        return giu["prov"]

    out, err = io.StringIO(), io.StringIO()
    code = R.main(argv if argv is not None else _args(kho, case, *them, ra=ra),
                  inner_transport_factory=nha_may, env=env, stdout=out, stderr=err)
    return SimpleNamespace(code=code, out=out.getvalue(), err=err.getvalue(),
                           cong=giu.get("cong"), prov=giu.get("prov"), ra=ra)


def _json(r, ten: str) -> dict:
    return json.loads((r.ra / ten).read_text(encoding="utf-8"))


def _ca(tt: dict, cid: str) -> dict:
    return next(c for c in tt["cases"] if c["case_id"] == cid)


# ══ 1–5 · TỪNG CA, TUẦN TỰ, DỪNG KHI HỎNG ═════════════════════════════════
def test_01_case_C01_CHI_chay_C01(kho, de):
    # Ảnh của ca không được yêu cầu vắng mặt cũng không sao — runner không đọc tới.
    (kho.anh / "C02.png").unlink()
    (kho.anh / "C03.png").unlink()
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    assert (tt["cases_requested"], tt["cases_run"], tt["cases_not_run"]) == (["C01"], ["C01"], [])
    assert r.prov.calls == BA_TANG_C01
    assert not [p.name for p in r.ra.iterdir() if p.name.startswith(("C02", "C03"))]
    assert tt["HTTP_REQUESTS_SENT"] == 3 and tt["ACCEPTANCE"] == "PASS"


def test_02_case_all_chay_TUAN_TU_C01_C02_C03(kho, de):
    r = _chay(kho, "all", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    assert tt["cases_run"] == ["C01", "C02", "C03"]
    assert r.prov.calls == [*BA_TANG_C01, ("C02", "vision"), ("C02", "analyze"), ("C02", "synthesis"),
                            ("C03", "vision")]
    assert (tt["HTTP_REQUESTS_SENT"], tt["VISION_HTTP_REQUESTS"], tt["ANALYZE_HTTP_REQUESTS"],
            tt["SYNTHESIS_HTTP_REQUESTS"], tt["HTTP_REQUESTS_BLOCKED"]) == (7, 3, 2, 2, 0)
    assert tt["STAGE_SUM_EQUALS_SENT"] is True and tt["ACCEPTANCE"] == "PASS"
    # Transport tiêm vào KHÔNG BAO GIỜ được ghi thành bằng chứng provider thật.
    assert tt["run_mode"] == "INJECTED_TRANSPORT" and tt["REAL_PROVIDER_CALLS"] == 0
    assert tt["APPLICATION_LLM_CALLS"] == 0 and tt["FIXTURE_LOGICAL_CALLS"] == 7
    assert tt["REAL_PROVIDER_EVIDENCE"] == "NOT_APPLICABLE_INJECTED_TRANSPORT"
    assert tt["NETWORK_REQUESTS"] == 0


@pytest.mark.parametrize("kieu", ["nhan_sai_o_tang_doc_anh", "tong_hop_tra_400"])
def test_03_C01_HONG_thi_C02_C03_KHONG_request_nao(kho, de, kieu):
    if kieu == "nhan_sai_o_tang_doc_anh":
        sai = de["C01"].replace("S.ABCD", "S.ABCE")
        thay = {("C01", "vision"): [_ban_ghi(sai, "SABCE", ["z = 3"], ["S.ABCE"], ["ABCD là hình vuông"])]}
    else:
        thay = {("C01", "synthesis"): [httpx.Response(400, json={"error": {"message": "bad request"}})]}
    r = _chay(kho, "all", kich_ban=_kich_ban(de, thay))
    assert r.code == R.EXIT_CASE_FAIL, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    assert tt["cases_run"] == ["C01"]
    assert tt["cases_not_run"] == [{"case_id": c, "status": "NOT_RUN_PREVIOUS_CASE_FAILED"} for c in ("C02", "C03")]
    assert all(cid == "C01" for cid, _ in r.prov.calls), r.prov.calls
    assert not [p.name for p in r.ra.iterdir() if p.name.startswith(("C02", "C03"))]
    c01 = _ca(tt, "C01")
    assert c01["result"] == "FAIL" and tt["ACCEPTANCE"] == "FAIL"
    if kieu == "nhan_sai_o_tang_doc_anh":
        assert r.prov.calls == [("C01", "vision")], "đọc ảnh hỏng thì tầng B không được tiêu quota"
        assert c01["vision_scoring"]["RAW_TEXT_CER"] < R.NGUONG_CER["C01"]
        assert any("POINT_LABEL_ACCURACY" in x for x in c01["fail_reasons"])
    else:
        assert r.prov.calls == BA_TANG_C01
        assert any("ANALYZE_OR_SYNTHESIS_PROVIDER_ERROR" in x for x in c01["fail_reasons"])


def test_04_C02_vision_503_thi_C03_KHONG_request_va_KHONG_thu_lai(kho, de):
    # Lượt thứ hai trong kịch bản là một phản hồi ĐÚNG: nếu runner thử lại, nó sẽ qua.
    # Nên "không thử lại" ở đây là do bị ép, không phải do tình cờ không còn gì để thử.
    thay = {("C02", "vision"): [httpx.Response(503, json={"error": "qua tai"}), _vision_dung(de, "C02")]}
    r = _chay(kho, "all", kich_ban=_kich_ban(de, thay))
    assert r.code == R.EXIT_CASE_FAIL, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    assert tt["cases_run"] == ["C01", "C02"]
    assert [c["case_id"] for c in tt["cases_not_run"]] == ["C03"]
    assert r.prov.calls.count(("C02", "vision")) == 1
    assert not [k for k in r.prov.calls if k[0] == "C03"]
    assert tt["RETRIES"] == 0 and tt["APIBUDGET_RETRY_REQUESTS"] == 0
    assert tt["PROVIDER_ERROR"] == "HTTP 503"
    assert _ca(tt, "C02")["http"] == {"sent": 1, "blocked": 0, "vision_sent": 1, "analyze_sent": 0,
                                      "synthesis_sent": 0}


@pytest.mark.parametrize("anh_c03, ma, an_toan", [
    ("chi_co_hinh", R.EXIT_PASS, True),
    ("co_de_day_du", R.EXIT_CASE_FAIL, False),
])
def test_05_C03_KHONG_bao_gio_goi_analyze_hay_synthesis(kho, de, anh_c03, ma, an_toan):
    p1 = RNB.doc_raw_theo_thu_tu(CA_P1)
    # Kịch bản CÓ SẴN phản hồi tầng B cho C03 — nếu runner gọi, nó sẽ được phục vụ.
    thay = {("C03", "analyze"): p1["semantic_analyze"], ("C03", "synthesis"): p1["semantic_program"]}
    if anh_c03 == "co_de_day_du":
        thay[("C03", "vision")] = [_vision_dung(de, "C01")]
    r = _chay(kho, "C03", kich_ban=_kich_ban(de, thay))
    assert r.code == ma, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    c03 = _ca(tt, "C03")
    assert r.prov.calls == [("C03", "vision")]
    assert (tt["ANALYZE_HTTP_REQUESTS"], tt["SYNTHESIS_HTTP_REQUESTS"]) == (0, 0)
    assert c03["C03_SAFE_REJECTION"] is an_toan
    assert not (r.ra / "C03_ANALYZE_RESULT.json").exists() and not (r.ra / "C03_SCENE_RESULT.json").exists()
    if an_toan:
        assert c03["REJECTION_CODE"] == "MISSING_PROBLEM_TEXT"
    else:
        assert c03["fail_reasons"][0].startswith("C03_NOT_REJECTED")


# ══ 6–8 · TỪ CHỐI TRƯỚC MỌI REQUEST ═══════════════════════════════════════
@pytest.mark.parametrize("env", [
    {},
    {"ALLOW_LIVE_AI": "1"},
    {"GEMINI_API_KEY": KHOA_GIA},
    {"ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": KHOA_GIA},
], ids=["khong_gi", "thieu_khoa", "thieu_ALLOW_LIVE_AI", "ALLOW_LIVE_AI_0"])
def test_06_THIEU_khoa_thoat_TRUOC_moi_request(kho, de, env):
    r = _chay(kho, "all", kich_ban=_kich_ban(de), env=env)
    assert r.code == R.EXIT_NO_KEY
    assert r.prov is None and r.cong is None, "nhà máy transport không được gọi"
    assert not kho.ra.exists()
    assert "NOT_ESTABLISHED" in r.err and KHOA_GIA not in r.err + r.out


def test_07_dry_run_KHONG_cham_mang(kho, de, monkeypatch):
    gt = _gt(de)
    gt["cases"][0]["dry_run_replay_case"] = CA_P1
    gt["cases"][1]["dry_run_replay_case"] = CA_P6
    kho.gt.write_text(json.dumps(gt, ensure_ascii=False), encoding="utf-8")
    dung_transport_mang: list[int] = []
    goc = httpx.AsyncHTTPTransport.__init__

    def dem(self, *a, **k):
        dung_transport_mang.append(1)
        goc(self, *a, **k)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "__init__", dem)
    out, err = io.StringIO(), io.StringIO()
    code = R.main(_args(kho, "all", "--dry-run"), env={}, stdout=out, stderr=err)
    assert code == R.EXIT_PASS, (out.getvalue(), err.getvalue())
    tt = json.loads((kho.ra / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    assert tt["run_mode"] == "DRY_RUN" and tt["NETWORK_REQUESTS"] == 0
    assert (tt["REAL_PROVIDER_CALLS"], tt["APPLICATION_LLM_CALLS"]) == (0, 0)
    assert (tt["FIXTURE_LOGICAL_CALLS"], tt["FAKE_OR_INNER_TRANSPORT_INVOCATIONS"]) == (7, 7)
    assert tt["REAL_PROVIDER_EVIDENCE"] == "NOT_APPLICABLE_DRY_RUN" and tt["ACCEPTANCE"] == "PASS"
    assert dung_transport_mang == [], "không một transport mạng nào được DỰNG"


def _hong_dau_vao(kho, ten: str) -> list[str]:
    a = _args(kho, "all")

    def dat(co: str, gia: str) -> None:
        a[a.index(co) + 1] = gia

    def sua_gt(fn) -> None:
        d = json.loads(kho.gt.read_text(encoding="utf-8"))
        fn(d["cases"])
        kho.gt.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")

    if ten == "khong_co_case":
        del a[0:2]
    elif ten == "case_la":
        dat("--case", "C04")
    elif ten == "input_tuong_doi":
        dat("--input-dir", "anh")
    elif ten == "input_khong_ton_tai":
        dat("--input-dir", str(kho.tmp / "khong-co"))
    elif ten == "ground_truth_tuong_doi":
        dat("--ground-truth", "GROUND_TRUTH.json")
    elif ten == "ground_truth_khong_ton_tai":
        dat("--ground-truth", str(kho.tmp / "khong-co.json"))
    elif ten == "output_tuong_doi":
        dat("--output-dir", "ra")
    elif ten == "output_khong_rong":
        kho.ra.mkdir()
        (kho.ra / "RUN_SUMMARY.json").write_text("{}", encoding="utf-8")
    elif ten == "max_http_12":
        a += ["--max-http-requests", "12"]
    elif ten == "max_http_0":
        a += ["--max-http-requests", "0"]
    elif ten == "max_attempts_la":
        a += ["--max-attempts", "2"]
    elif ten == "anh_sach_khong_xac_nhan":
        a += ["--include-sanitized-images"]
    elif ten == "gt_thieu_C02":
        sua_gt(lambda cs: cs.pop(1))
    elif ten == "C03_khong_phai_tu_choi":
        sua_gt(lambda cs: cs[2].update(expected_outcome="ACCEPT"))
    elif ten == "point_labels_rong":
        sua_gt(lambda cs: cs[0]["critical_facts"].update(point_labels=[]))
    elif ten == "hai_anh_C01":
        (kho.anh / "C01.jpg").write_bytes(_anh((1, 2, 3), "JPEG"))
    elif ten == "anh_hong":
        (kho.anh / "C02.png").write_bytes(b"khong phai anh")
    elif ten == "confirmed_text_khoa_la":
        p = kho.tmp / "xac_nhan.json"
        p.write_text(json.dumps({"C03": "đề bịa"}, ensure_ascii=False), encoding="utf-8")
        a += ["--confirmed-text", str(p)]
    elif ten == "confirmed_text_tuong_doi":
        a += ["--confirmed-text", "xac_nhan.json"]
    else:  # pragma: no cover
        raise AssertionError(ten)
    return a


@pytest.mark.parametrize("ten", [
    "khong_co_case", "case_la", "input_tuong_doi", "input_khong_ton_tai", "ground_truth_tuong_doi",
    "ground_truth_khong_ton_tai", "output_tuong_doi", "output_khong_rong", "max_http_12", "max_http_0",
    "max_attempts_la", "anh_sach_khong_xac_nhan", "gt_thieu_C02", "C03_khong_phai_tu_choi",
    "point_labels_rong", "hai_anh_C01", "anh_hong", "confirmed_text_khoa_la", "confirmed_text_tuong_doi",
])
def test_08_dau_vao_SAI_bi_tu_choi_TRUOC_request(kho, de, ten):
    argv = _hong_dau_vao(kho, ten)
    truoc = sorted(p.name for p in kho.ra.iterdir()) if kho.ra.exists() else None
    r = _chay(kho, "all", kich_ban=_kich_ban(de), argv=argv)
    assert r.code == R.EXIT_USAGE, (ten, r.out, r.err)
    assert r.prov is None, "không một transport nào được dựng"
    assert (sorted(p.name for p in kho.ra.iterdir()) if kho.ra.exists() else None) == truoc
    if ten == "khong_co_case":
        assert "Thiếu --case" in r.err


# ══ 9–13 · TRẦN HTTP, BỘ ĐẾM THEO TẦNG, MỘT LẦN THỬ ═══════════════════════
def test_09_CONG_HTTP_chan_request_thu_12_TRUOC_transport():
    dem = {"n": 0}

    def tra(_req):
        dem["n"] += 1
        return R._phan_hoi_gemini("{}")

    cong = R.CongHttp(httpx.MockTransport(tra), 11, R.BoKhuBiMat())
    cong.dat_ca("C01")
    bi_chan: list[int] = []

    async def muoi_hai_luot():
        for i in range(1, 13):
            try:
                with stage_scope("semantic_program"):
                    await gemini.call_gemini("khoa-gia", "system", f"lượt logic {i}")
            except R.HttpBudgetExceeded:
                bi_chan.append(i)

    budget = gemini.ApiBudget(max_attempts=1)
    with R.dung_ngan_sach(budget), R.cai_cong_http(cong):
        asyncio.run(muoi_hai_luot())
    assert dem["n"] == 11 == cong.inner_invocations
    assert (cong.attempted, cong.sent, cong.blocked) == (12, 11, 1)
    assert bi_chan == [12]
    assert cong.records[-1]["block_reason"] == "HTTP_BUDGET_EXHAUSTED"
    assert cong.records[-1]["http_status"] is None
    assert (budget.logical_calls, budget.http_requests) == (12, 12)

    # Không lối vòng: request KHÔNG khai tầng cũng bị chặn, dù trần còn chỗ.
    cong2 = R.CongHttp(httpx.MockTransport(tra), 11, R.BoKhuBiMat())
    cong2.dat_ca("C01")
    with R.cai_cong_http(cong2), pytest.raises(R.HttpBudgetExceeded, match="STAGE_UNKNOWN"):
        asyncio.run(gemini.call_gemini("khoa-gia", "system", "không có stage_scope"))
    assert cong2.inner_invocations == 0 and cong2.blocked_by_stage["unknown"] == 1
    assert isinstance(httpx.AsyncClient, type), "cổng phải được gỡ sạch sau khối"


def test_10_TRAN_runner_chan_dung_cho_va_11_VUA_DU_duong_xau_nhat(kho, de):
    # (a) trần 2: C01 cần 3 ⇒ lượt tổng hợp bị chặn TRƯỚC transport.
    r = _chay(kho, "C01", "--max-http-requests", "2", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_CASE_FAIL
    tt = _json(r, "RUN_SUMMARY.json")
    assert r.prov.calls == BA_TANG_C01[:2]
    assert (tt["HTTP_REQUESTS_ATTEMPTED"], tt["HTTP_REQUESTS_SENT"], tt["HTTP_REQUESTS_BLOCKED"]) == (3, 2, 1)
    assert tt["FAKE_OR_INNER_TRANSPORT_INVOCATIONS"] == 2 and tt["BLOCKED_BY_STAGE"]["synthesis"] == 1
    assert any("HTTP_BLOCKED" in x for x in _ca(tt, "C01")["fail_reasons"])

    # (b) đường xấu nhất mà cả ba ca vẫn ĐẠT: tổng hợp hỏng JSON hai lượt, lượt sửa thứ ba đúng.
    hong = "{ day khong phai json"
    p1, p6 = RNB.doc_raw_theo_thu_tu(CA_P1), RNB.doc_raw_theo_thu_tu(CA_P6)
    xau = _kich_ban(de, {("C01", "synthesis"): [hong, hong, *p1["semantic_program"]],
                         ("C02", "synthesis"): [hong, hong, *p6["semantic_program"]]})
    r11 = _chay(kho, "all", kich_ban=xau, ra=kho.tmp / "ra11")
    tt11 = _json(r11, "RUN_SUMMARY.json")
    assert r11.code == R.EXIT_PASS, tt11["cases"]
    assert (tt11["HTTP_REQUESTS_SENT"], tt11["HTTP_REQUESTS_BLOCKED"], tt11["SYNTHESIS_HTTP_REQUESTS"]) == (
        R.MAX_HTTP_REQUESTS, 0, 6)
    # Lượt sửa 2 và 3 gửi thân Y HỆT nhau (cùng đầu ra hỏng, cùng lời báo lỗi) — đó là hai lượt
    # gọi LOGIC, không phải thử lại. Bản đếm theo băm thân từng ghi RETRIES = 2 ở đây.
    assert (tt11["RETRIES"], tt11["APIBUDGET_RETRY_REQUESTS"]) == (0, 0)

    # (c) cùng đường ấy dưới trần 10: ảnh C03 bị chặn, không lọt qua.
    r10 = _chay(kho, "all", "--max-http-requests", "10", kich_ban=xau, ra=kho.tmp / "ra10")
    tt10 = _json(r10, "RUN_SUMMARY.json")
    assert r10.code == R.EXIT_CASE_FAIL
    assert (tt10["HTTP_REQUESTS_SENT"], tt10["HTTP_REQUESTS_BLOCKED"]) == (10, 1)
    assert tt10["BLOCKED_BY_STAGE"]["vision"] == 1 and r10.prov.calls.count(("C03", "vision")) == 0


def test_11_RETRY_duoc_DEM_o_cong_va_cong_mac_dinh_CHAN_luot_thu_lai():
    def mot_luot(dung_sau_loi: bool):
        dap = [httpx.Response(503, json={"error": "qua tai"}), R._phan_hoi_gemini("{}")]
        cong = R.CongHttp(httpx.MockTransport(lambda _r: dap.pop(0)), 11, R.BoKhuBiMat(),
                          dung_sau_loi=dung_sau_loi)
        cong.dat_ca("C01")
        budget = gemini.ApiBudget(max_attempts=2)
        loi = None

        async def goi():
            with stage_scope("semantic_analyze"):
                return await gemini.call_gemini("khoa-gia", "system", "một lượt logic")

        with R.dung_ngan_sach(budget), R.cai_cong_http(cong):
            try:
                asyncio.run(goi())
            except R.HttpBudgetExceeded as err:
                loi = err
        return cong, budget, loi

    cong, budget, loi = mot_luot(dung_sau_loi=False)
    assert loi is None
    assert (cong.sent, cong.retries_attempted, cong.retries_sent) == (2, 1, 1)
    assert cong.sent_by_stage == {"vision": 0, "analyze": 2, "synthesis": 0}
    assert [x["retry"] for x in cong.records] == [False, True]
    assert (budget.logical_calls, budget.retry_requests) == (1, 1)

    cong, _budget, loi = mot_luot(dung_sau_loi=True)
    assert isinstance(loi, R.HttpBudgetExceeded)
    assert (cong.sent, cong.blocked, cong.retries_attempted, cong.retries_sent) == (1, 1, 1, 0)
    assert cong.records[-1]["block_reason"] == "STOPPED_AFTER_PROVIDER_ERROR"


def test_12_TONG_theo_tang_BANG_tong_gui_ke_ca_khi_co_chan(kho, de):
    r = _chay(kho, "all", "--max-http-requests", "4", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_CASE_FAIL
    tt, pc = _json(r, "RUN_SUMMARY.json"), _json(r, "PROVIDER_CALLS.json")
    theo_tang = {s: tt[f"{s.upper()}_HTTP_REQUESTS"] for s in R.STAGES}
    assert theo_tang == {"vision": 2, "analyze": 1, "synthesis": 1}
    assert sum(theo_tang.values()) == tt["HTTP_REQUESTS_SENT"] == 4
    assert sum(tt["BLOCKED_BY_STAGE"].values()) == tt["HTTP_REQUESTS_BLOCKED"] == 1
    assert tt["BLOCKED_BY_STAGE"]["analyze"] == 1
    rec = pc["records"]
    assert len(rec) == tt["HTTP_REQUESTS_ATTEMPTED"] == tt["APIBUDGET_HTTP_COUNT"] == 5
    assert [x["provider_call_number"] for x in rec] == [1, 2, 3, 4, 5]
    for s in R.STAGES:
        assert sum(1 for x in rec if x["sent"] and x["stage"] == s) == theo_tang[s]
    assert sum(c["http"]["sent"] for c in tt["cases"]) == tt["HTTP_REQUESTS_SENT"]
    assert tt["STAGE_SUM_EQUALS_SENT"] is True and tt["APIBUDGET_MATCHES_GATE"] is True
    assert all("?" not in x["endpoint"] for x in rec), "endpoint không bao giờ mang query"
    # Ca hỏng giữa chừng không mang theo cảnh của ca trước.
    c02 = _ca(tt, "C02")
    assert "scene_kinds" not in c02 and not (r.ra / "C02_SCENE_RESULT.json").exists()


def test_13_MOT_lan_thu_moi_luot_goi_duoc_EP_va_TU_KIEM_truoc_khi_chay(kho, de, monkeypatch):
    assert R.MAX_ATTEMPTS_PER_LOGICAL_CALL == 1
    assert asyncio.run(R.do_so_lan_thu_moi_tang()) == {"vision": 1, "analyze": 1, "synthesis": 1}
    assert R.tao_ngan_sach_nghiem_thu().max_attempts == 1
    with pytest.raises(ValueError, match="RETRY_POLICY_NOT_ENFORCEABLE"):
        R.tao_ngan_sach_nghiem_thu(2)
    r = _chay(kho, "C01", "--max-attempts", "2", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_USAGE and r.prov is None

    # Ai đó nới hằng số ⇒ phép dò trên ĐÚNG ba hàm sản phẩm thấy 2/2/2 và chặn cả lượt.
    monkeypatch.setattr(R, "MAX_ATTEMPTS_PER_LOGICAL_CALL", 2)
    r2 = _chay(kho, "C01", kich_ban=_kich_ban(de))
    assert r2.code == R.EXIT_RETRY_POLICY, (r2.out, r2.err)
    assert r2.prov is None and not kho.ra.exists()
    assert "RETRY_POLICY_NOT_ENFORCEABLE" in r2.err and "'vision': 2" in r2.err


# ══ 14–15 · CER VÀ DỮ KIỆN QUAN TRỌNG ═════════════════════════════════════
@pytest.mark.parametrize("ref, pred, mong", [
    ("abc", "abd", 1 / 3),
    ("", "xyz", 3.0),
    ("abc", "", 1.0),
    ("abc", "abc", 0.0),
    ("Hình chóp", "Hinh chop", 2 / 9),
    ("SA = 3", "SA=3", 2 / 6),
    ("dòng 1\ndòng 2", "dòng 1  \r\ndòng 2", 0.0),
    ("Hình chóp", unicodedata.normalize("NFD", "Hình chóp"), 0.0),
    ("ABCD", "abcd", 1.0),
    ("x = -2", "x = 2", 1 / 6),
    ("kitten", "sitting", 3 / 6),
    ("ab", "abcd", 1.0),
    ("abcd", "ab", 0.5),
], ids=["thay", "ref_rong", "pred_rong", "trung", "dau_tieng_viet", "khoang_trang", "crlf_cuoi_dong",
        "nfd", "hoa_thuong", "dau_tru", "kinh_dien", "mau_la_ref_1", "mau_la_ref_2"])
def test_14_CER_levenshtein_DUNG_mau_so_va_chuan_hoa(ref, pred, mong):
    assert R.cer(ref, pred) == pytest.approx(mong)


def test_15_loi_NHAN_hay_CONG_THUC_KHONG_bi_CER_thap_che(de):
    g = _gt(de)["cases"][0]
    dung = R.cham_doc_anh("C01", g, ie.parse_extraction(_vision_dung(de, "C01")), de["C01"])
    assert dung["fail_reasons"] == [] and dung["RAW_TEXT_CER"] == 0.0, dung  # cửa sổ chứng

    nhan = de["C01"].replace("S.ABCD", "S.ABCE")
    k1 = R.cham_doc_anh("C01", g, ie.parse_extraction(
        _ban_ghi(nhan, "SABCE", ["z = 3"], ["S.ABCE"], ["ABCD là hình vuông"])), nhan)
    assert k1["RAW_TEXT_CER"] <= R.NGUONG_CER["C01"]
    assert (k1["POINT_LABEL_ACCURACY"], k1["OBJECT_ACCURACY"], k1["HALLUCINATED_CRITICAL_FACTS"]) == (0.8, 0.0, 2)
    assert any("POINT_LABEL_ACCURACY" in x for x in k1["fail_reasons"])

    ct = de["C01"].replace("z = 3", "z = 8")
    k2 = R.cham_doc_anh("C01", g, ie.parse_extraction(
        _ban_ghi(ct, "SABCD", ["z = 8"], ["S.ABCD"], ["ABCD là hình vuông"])), ct)
    assert k2["RAW_TEXT_CER"] == pytest.approx(1 / len(de["C01"]), abs=1e-6)
    assert (k2["FORMULA_ACCURACY"], k2["POINT_LABEL_ACCURACY"]) == (0.0, 1.0)
    assert any("FORMULA_ACCURACY" in x for x in k2["fail_reasons"])

    # Nhãn khai trong `named_points` mà không hiện như KÝ HIỆU trong văn bản ⇒ không tính là đọc đúng.
    mat_d = de["C01"].replace("D(0;6;0)", "(0;6;0)").replace("S.ABCD", "S.ABC").replace(
        "ABCD là", "ABC là").replace("BD.", "B.")
    k3 = R.cham_doc_anh("C01", g, ie.parse_extraction(_ban_ghi(mat_d, "SABCD", ["z = 3"])), mat_d)
    assert "D" in k3["details"]["point_labels_missing"]


# ══ 16–18 · SECRET, ẢNH, TRẠNG THÁI RÒ GIỮA CÁC CA ═════════════════════════
def _than_chua_bi_mat(url: str = "") -> str:
    return (f"MARKER-DA-TOI {url} API {KHOA_GIA} x-goog-api-key: TOKEN-KHAC-987 "
            "Authorization: Bearer TOKEN-AUTH-555 Set-Cookie: sid=COOKIE-777 cb?key=QUERYKEY-999")


@pytest.mark.parametrize("kieu", ["vision_403", "analyze_403", "synthesis_connect_error"])
def test_16_secret_KHONG_lot_ra_stdout_stderr_artifact(kho, de, capsys, kieu):
    if kieu == "vision_403":
        thay = {("C01", "vision"): [httpx.Response(403, text=_than_chua_bi_mat())]}
    elif kieu == "analyze_403":
        thay = {("C01", "analyze"): [httpx.Response(403, text=_than_chua_bi_mat())]}
    else:
        # URL request mang `?key=<khoá thật>` — lỗi mạng chép nguyên URL vào thông điệp.
        thay = {("C01", "synthesis"): [lambda req: httpx.ConnectError(_than_chua_bi_mat(str(req.url)))]}
    r = _chay(kho, "C01", kich_ban=_kich_ban(de, thay))
    assert r.code == R.EXIT_CASE_FAIL, (r.out, r.err)
    cap = capsys.readouterr()
    be_mat = {"stdout": r.out, "stderr": r.err, "capsys": cap.out + cap.err}
    be_mat.update({p.name: p.read_text(encoding="utf-8") for p in sorted(r.ra.iterdir())})
    ro = sorted({(ten, s[:6]) for ten, noi_dung in be_mat.items() for s in BI_MAT if s in noi_dung})
    assert ro == [], f"secret lọt: {ro}"
    # Cửa sổ chứng: thông điệp chở secret THẬT SỰ đã tới các bề mặt — nếu không thì "sạch" là rỗng nghĩa.
    assert "MARKER-DA-TOI" in r.out and "MARKER-DA-TOI" in be_mat["RUN_SUMMARY.json"]
    assert R.REDACTED in be_mat["RUN_SUMMARY.json"]

    khu = R.BoKhuBiMat((KHOA_GIA,))
    assert khu({"Authorization": "Bearer abc", "headers": {"X-Goog-Api-Key": "zzz", "cookie": "a=b"},
                "GEMINI_API_KEY": "xyz", "ok": "giữ nguyên"}) == {
        "Authorization": R.REDACTED, "headers": {"X-Goog-Api-Key": R.REDACTED, "cookie": R.REDACTED},
        "GEMINI_API_KEY": R.REDACTED, "ok": "giữ nguyên"}
    assert khu("GEMINI_API_KEY=sk-live-123456") == f"GEMINI_API_KEY={R.REDACTED}"
    assert khu("refresh_token: rt-9 access_token=at-8") == f"refresh_token: {R.REDACTED} access_token={R.REDACTED}"


def test_17_KHONG_chep_anh_theo_mac_dinh(kho, de):
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    assert not [p.name for p in r.ra.iterdir() if p.suffix.lower() in DUOI_ANH]
    assert (tt["RAW_PHOTOS_COPIED"], tt["SANITIZED_IMAGES_WRITTEN"]) == (0, 0)
    goc = (kho.anh / "C01.png").read_bytes()
    assert _json(r, "C01_RAW_EXTRACTION.json")["image"]["IMAGE_SHA256"] == hashlib.sha256(goc).hexdigest()
    mau_b64 = normalize_image(goc).base64()[:64]
    assert not [p.name for p in r.ra.iterdir() if mau_b64 in p.read_text(encoding="utf-8")]

    # Có xin ảnh đã làm sạch mà thiếu cam kết ⇒ từ chối; có cam kết ⇒ đúng một JPEG không metadata.
    r1 = _chay(kho, "C01", "--include-sanitized-images", kich_ban=_kich_ban(de), ra=kho.tmp / "ra1")
    assert r1.code == R.EXIT_USAGE and not (kho.tmp / "ra1").exists()
    r2 = _chay(kho, "C01", "--include-sanitized-images", "--confirm-no-personal-data",
               kich_ban=_kich_ban(de), ra=kho.tmp / "ra2")
    assert r2.code == R.EXIT_PASS, (r2.out, r2.err)
    anh = [p for p in r2.ra.iterdir() if p.suffix.lower() in DUOI_ANH]
    assert [p.name for p in anh] == ["C01_SANITIZED.jpg"]
    du_lieu = anh[0].read_bytes()
    assert du_lieu[:2] == b"\xff\xd8" and du_lieu != goc
    with Image.open(io.BytesIO(du_lieu)) as im:
        assert len(im.getexif()) == 0
    assert _json(r2, "RUN_SUMMARY.json")["RAW_PHOTOS_COPIED"] == 0


def test_18_KHONG_ro_ket_qua_giua_cac_ca(kho, de):
    truoc = len(ie.EXTRACTION_CACHE)
    r = _chay(kho, "all", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    assert len(ie.EXTRACTION_CACHE) == truoc, "runner đọc ảnh KHÔNG qua cache"
    for cid, khac in (("C01", "C02"), ("C02", "C01")):
        assert _json(r, f"{cid}_RAW_EXTRACTION.json")["extraction"]["problem_text_verbatim"] == de[cid]
        xn = _json(r, f"{cid}_CONFIRMED_INPUT.json")
        assert (xn["USER_CONFIRMED_TEXT"], xn["EDITED"]) == (de[cid], False)
        than = r.cong.van_ban_analyze[cid]
        assert len(than) == 1 and de[cid] in than[0] and de[khac] not in than[0]
        assert _ca(_json(r, "RUN_SUMMARY.json"), cid)["USER_EDIT_PAYLOAD_PARITY"] is True
    k1 = _json(r, "C01_SCENE_RESULT.json")["scene_kinds"]
    k2 = _json(r, "C02_SCENE_RESULT.json")["scene_kinds"]
    assert "section" in k1 and "curved_solid" not in k1
    assert "curved_solid" in k2 and "section" not in k2
    assert len({_json(r, f"{c}_RAW_EXTRACTION.json")["image"]["NORMALIZED_IMAGE_SHA256"] for c in R.CASE_IDS}) == 3


def test_18b_ban_XAC_NHAN_la_thu_DUY_NHAT_di_vao_luot_doc_de(kho, de):
    sua = de["C01"].replace("Oxyz, cho", "Oxyz cho")
    assert sua != de["C01"]
    p = kho.tmp / "xac_nhan.json"
    p.write_text(json.dumps({"C01": sua}, ensure_ascii=False), encoding="utf-8")
    r = _chay(kho, "C01", "--confirmed-text", str(p), kich_ban=_kich_ban(de))
    c01 = _ca(_json(r, "RUN_SUMMARY.json"), "C01")
    xn = _json(r, "C01_CONFIRMED_INPUT.json")
    assert (xn["EDITED"], xn["CONFIRMATION_SOURCE"]) == (True, "CONFIRMED_TEXT_FILE")
    assert c01["USER_EDIT_PAYLOAD_PARITY"] is True
    than = r.cong.van_ban_analyze["C01"]
    assert sua in than[0] and f'"""\n{de["C01"]}\n"""' not in than[0]
    assert c01["vision_scoring"]["RAW_TEXT_CER"] == 0.0 and c01["vision_scoring"]["CONFIRMED_TEXT_CER"] > 0
