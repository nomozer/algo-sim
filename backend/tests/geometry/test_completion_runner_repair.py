# -*- coding: utf-8 -*-
"""COMPLETION_RUNNER_REPAIR_OFFLINE — bộ đo cho lượt completion 6 ca còn thiếu.

Mỗi khối test đóng MỘT khoảng trống đã khai ở
`multicase-benchmark-completion/RUNNER_READINESS_GAPS.json` (G1–G8). Test được
viết TRƯỚC bản sửa và chạy đỏ trên runner ở `a17d00c` — bằng chứng ở
`completion-runner-repair-offline/RED_BEFORE_GREEN_AFTER.json`.

0 request thật: `conftest.py` chặn transport ở biên mạng, và mọi kịch bản
`main()` chạy bên trong `ChanMangThat` với transport giả.

Không test nào tự sinh tham số từ chính registry nó bảo vệ: danh sách ca, số
lượng, băm nội dung registry và các quan hệ tối thiểu đều được viết CỨNG ở đây.
"""
from __future__ import annotations

import ast
import asyncio
import contextlib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.ai import gemini  # noqa: E402
from app.ai.telemetry import stage_scope  # noqa: E402

import run_multicase_benchmark as B  # noqa: E402
import run_structured_relation_analyze_live as L  # noqa: E402
from run_photo_problem_live import BoKhuBiMat, ChanMangThat  # noqa: E402

KEY_GIA = "KHOA_GIA_OFFLINE_0000000000"
DGEO = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
HIST = DGEO / "multicase-benchmark"
REGD = DGEO / "completion-runner-repair-offline"
PRIOR = DGEO / "multicase-benchmark-completion"

CON_LAI = ["P06", "P07", "P08", "N02", "N03", "N04"]          # viết CỨNG
CA_AM = ["N01", "N02", "N03", "N04"]                           # viết CỨNG
SHA_REGISTRY_QUAN_HE = "bbd322980baa4a8ef187db4607725ea6cc829436dc7c6d3bb3a1ee630df055b9"
SHA_REGISTRY_TU_CHOI = "52bc6379d2f01372513d5aa21bd25433ea27783edae416cc7a1ed95fa8bb7100"
QUAN_HE_TOI_THIEU = {                                          # viết CỨNG
    "N01": {("perpendicular_line_plane", ("W", "X", "X", "Y", "Z"))},
    "N02": {("perpendicular_line_plane", ("R", "T", "T", "V", "X"))},
    "N03": {("perpendicular_lines", ("K", "M", "K", "N"))},
    "N04": {("perpendicular_lines", ("G", "H", "G", "L")),
            ("perpendicular_lines", ("G", "H", "H", "L")),
            ("perpendicular_line_plane", ("D", "G", "G", "H", "L"))},
}
NEXT_DUNG = {                                                  # viết CỨNG theo đặc tả
    "STRONG_PILOT_RESULT": "PRIMITIVE_COMPILER_OPT_IN_CANARY_ROUTING_DESIGN",
    "READY_FOR_CANARY_DESIGN": "PRIMITIVE_COMPILER_OPT_IN_CANARY_ROUTING_DESIGN",
    "MORE_EVIDENCE_NEEDED": "ANALYZE_FAILURE_CLUSTER_DIAGNOSIS",
    "NOT_READY": "STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS",
    "UNSAFE": "STRUCTURED_RELATION_SAFETY_REPAIR",
    "PROVIDER_INCOMPLETE": "RETRY_STILL_MISSING_CASES_LATER",
    "MEASUREMENT_INVALID": "MULTICASE_BENCHMARK_MEASUREMENT_REPAIR",
}


def _G():
    """Nhập bộ tổng hợp ở TRONG test — thiếu module thì đỏ từng test, không đỏ cả tệp."""
    import aggregate_multicase_completion as G
    return G


def _sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _bam_thu_muc(d: Path) -> dict[str, str]:
    return {p.relative_to(d).as_posix(): _sha_lf(p) for p in sorted(d.rglob("*")) if p.is_file()}


def _reg():
    return B.doc_registry()


def _gt():
    return B.doc_ground_truth()


def _tra_loi(van: str, usage: bool = True) -> httpx.Response:
    than = {"candidates": [{"content": {"parts": [{"text": van}]}}]}
    if usage:
        than["usageMetadata"] = {"promptTokenCount": 11, "candidatesTokenCount": 7,
                                 "thoughtsTokenCount": 3, "totalTokenCount": 21}
    return httpx.Response(200, json=than)


def _ca_cua(req: httpx.Request) -> str | None:
    tin = json.loads(req.content)["contents"][0]["parts"][-1]["text"]
    return next((c["case_id"] for c in _reg()["cases"] if c["input_text"] in tin), None)


def _payload_duong(cid: str) -> dict:
    """Đầu ra Analyze ĐÚNG cho một ca dương, dẫn từ registry + ground truth."""
    ca, g = B.ca_theo_id(_reg())[cid], _gt()["positive"][cid]
    Lb = ca["labels"]
    rv, a, b, ap = Lb["right_vertex"], Lb["leg_1_end"], Lb["leg_2_end"], Lb["apex"]
    return {
        "input_facts": [
            {"id": "day_vuong", "label": f"tam giác {rv}{a}{b} vuông tại {rv}",
             "values": [f"tam giác {rv}{a}{b} vuông tại {rv}"]},
            {"id": "leg1", "label": f"{rv}{a}", "values": [g["leg_1"]["len"]]},
            {"id": "leg2", "label": f"{rv}{b}", "values": [g["leg_2"]["len"]]},
            {"id": "cao_vuong", "label": f"{ap}{rv} vuông góc mặt phẳng ({rv}{a}{b})",
             "values": [f"{ap}{rv} ⊥ ({rv}{a}{b})"]},
            {"id": "cao", "label": f"{ap}{rv}", "values": [g["height"]["len"]]}],
        "obligations": [{"kind": "volume", "container": f"{ap}.{rv}{a}{b}", "witness": "the_tich"}],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": [rv, a], "other_line": [rv, b],
             "source_fact_id": "day_vuong"},
            {"kind": "perpendicular_line_plane", "line": [ap, rv], "plane": [rv, a, b],
             "source_fact_id": "cao_vuong"}]}


def _f(i, label, v):
    return {"id": i, "label": label, "values": [v]}


#: Đọc ĐÚNG đề của từng ca âm: khai ĐỦ mọi dữ kiện đề cho (kể cả mọi độ dài) và
#: đúng các quan hệ đề nói — CỐ Ý viết hoán vị tên (TR thay RT, XVT thay TVX…) để
#: bộ chấm phải so theo dạng chuẩn hoá, không so chuỗi thô.
#: ⚠️ Bản đầu của N03 thiếu `JK = 6` ⇒ adapter bác `GIVEN_FACT_WITHOUT_SOURCE`, và
#: bộ đối chiếu trả TARGETED = NO — ĐÚNG: đó là một bản đọc THIẾU, từ chối vì một
#: khiếm khuyết khác khiếm khuyết đã đăng ký. Lỗi nằm ở fixture, không ở bộ đo.
DOC_DUNG_CA_AM = {
    "N01": {"input_facts": [_f("wx_v", "WX vuông góc (XYZ)", "WX ⊥ (XYZ)"), _f("wx", "WX", "3"),
                            _f("xy", "XY", "4"), _f("xz", "XZ", "6")],
            "obligations": [{"kind": "volume", "container": "W.XYZ", "witness": "v"}],
            "geometric_relations": [{"kind": "perpendicular_line_plane", "line": ["X", "W"],
                                     "plane": ["Z", "Y", "X"], "source_fact_id": "wx_v"}]},
    "N02": {"input_facts": [_f("rt_v", "RT vuông góc (TVX)", "RT ⊥ (TVX)"), _f("rt", "RT", "6"),
                            _f("tv", "TV", "3"), _f("tx", "TX", "4"), _f("vx", "VX", "5")],
            "obligations": [{"kind": "volume", "container": "R.TVX", "witness": "v"}],
            "geometric_relations": [{"kind": "perpendicular_line_plane", "line": ["T", "R"],
                                     "plane": ["X", "V", "T"], "source_fact_id": "rt_v"}]},
    "N03": {"input_facts": [_f("day", "tam giác KMN vuông tại K", "tam giác KMN vuông tại K"),
                            _f("km", "KM", "5"), _f("kn", "KN", "8"), _f("jk", "JK", "6")],
            "obligations": [{"kind": "volume", "container": "J.KMN", "witness": "v"}],
            "geometric_relations": [{"kind": "perpendicular_lines", "line": ["N", "K"],
                                     "other_line": ["M", "K"], "source_fact_id": "day"}]},
    "N04": {"input_facts": [_f("vg", "tam giác GHL vuông tại G", "tam giác GHL vuông tại G"),
                            _f("vh", "tam giác GHL vuông tại H", "tam giác GHL vuông tại H"),
                            _f("dg_v", "DG vuông góc (GHL)", "DG ⊥ (GHL)"),
                            _f("gh", "GH", "4"), _f("gl", "GL", "7"), _f("dg", "DG", "5")],
            "obligations": [{"kind": "volume", "container": "D.GHL", "witness": "v"}],
            "geometric_relations": [
                {"kind": "perpendicular_lines", "line": ["L", "G"], "other_line": ["H", "G"],
                 "source_fact_id": "vg"},
                {"kind": "perpendicular_lines", "line": ["L", "H"], "other_line": ["G", "H"],
                 "source_fact_id": "vh"},
                {"kind": "perpendicular_line_plane", "line": ["G", "D"], "plane": ["L", "H", "G"],
                 "source_fact_id": "dg_v"}]},
}


def _cong(van: str) -> L.CongQuetCam:
    return L.CongQuetCam(httpx.MockTransport(lambda _r: _tra_loi(van)), 12,
                         BoKhuBiMat((KEY_GIA,)), tran_theo_tang={"vision": 0, "analyze": 12,
                                                                  "synthesis": 0})


def _mot_ca(cid: str, payload: dict | str) -> dict:
    van = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    r, _ = asyncio.run(B.chay_mot_ca(B.ca_theo_id(_reg())[cid], _gt(), KEY_GIA, _cong(van)))
    return r


class SapNguon(BaseException):
    """Mô phỏng tiến trình chết giữa chừng — KHÔNG phải Exception, không ai nuốt được."""


@contextlib.contextmanager
def _boi_canh_lich_su():
    import freeze_evaluation_candidate as F
    from app.simulation.semantic_program import analyze_contract
    import tempfile

    goc_hash = F.measured_system_hash
    goc_cv = B._cache_version_nguon
    goc_cf = B.CANDIDATE_FILE
    goc_prompt = gemini._skill_cache.get("geometry_analyze")
    goc_asf = analyze_contract.analyze_schema_for
    goc_nqs = B._nhanh_quan_sat

    hist_prompt = subprocess.run(
        ["git", "show", "161e8cf2:backend/app/ai/skills/geometry_analyze.md"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8"
    ).stdout

    def asf_hist(domain):
        s = goc_asf(domain)
        if domain == "hinh_hoc" and "solid_topology" in s.get("properties", {}):
            s = dict(s)
            s["properties"] = {k: v for k, v in s["properties"].items() if k != "solid_topology"}
        return s

    with tempfile.TemporaryDirectory() as td:
        fake_cand = Path(td) / "EVALUATION_CANDIDATE.json"
        fake_cand.write_text(json.dumps({
            "measured_system": {
                "tree_hash": "077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1"
            }
        }))
        try:
            B.CANDIDATE_FILE = fake_cand
            cur_h = F.measured_system_hash()[0]
            if cur_h not in ("0" * 64, "0" * 40):
                F.measured_system_hash = lambda: ("077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1", 103)
            cur_cv = B._cache_version_nguon()
            if cur_cv in ("100", "101", "102"):
                B._cache_version_nguon = lambda: "99"
            B._nhanh_quan_sat = lambda head: "feat/photo-problem-to-scene"
            gemini._skill_cache["geometry_analyze"] = hist_prompt
            analyze_contract.analyze_schema_for = asf_hist
            yield
        finally:
            B.CANDIDATE_FILE = goc_cf
            F.measured_system_hash = goc_hash
            B._cache_version_nguon = goc_cv
            B._nhanh_quan_sat = goc_nqs
            if goc_prompt is not None:
                gemini._skill_cache["geometry_analyze"] = goc_prompt
            else:
                gemini._skill_cache.pop("geometry_analyze", None)
            analyze_contract.analyze_schema_for = goc_asf


def _chay_main(ra: Path, xu_ly) -> tuple[int | None, list[str]]:
    """Chạy `main()` THẬT của runner. Chỉ thay transport và khoá ở biên."""
    thay: list[str] = []

    def boc(req: httpx.Request) -> httpx.Response:
        thay.append(_ca_cua(req))
        return xu_ly(req, _ca_cua(req))

    goc_t, goc_k, argv = httpx.AsyncHTTPTransport, L.doc_khoa, sys.argv
    ma = None
    with _boi_canh_lich_su():
        with ChanMangThat():                   # chặn mạng thật TRƯỚC, rồi mới thay transport
            httpx.AsyncHTTPTransport = lambda *a, **k: httpx.MockTransport(boc)  # type: ignore
            L.doc_khoa = lambda: KEY_GIA  # type: ignore[assignment]
            sys.argv = ["run_multicase_benchmark.py", "--live", "--tiep-tuc",
                        str(HIST / "CASE_RESULTS_REDACTED.json"), "--ra", str(ra)]
            try:
                ma = B.main()
            finally:
                httpx.AsyncHTTPTransport, L.doc_khoa, sys.argv = goc_t, goc_k, argv
    return ma, thay


def _doc(ra: Path, ten: str) -> dict:
    return json.loads((ra / ten).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lich_su_truoc() -> dict[str, str]:
    return _bam_thu_muc(HIST)


# ══ G1 — QUAN SÁT REQUEST THẬT ═════════════════════════════════════════════
def test_G1_A_sau_request_ghi_bam_than_model_schema_va_khop_ky_vong(tmp_path, lich_su_truoc):
    ma, thay = _chay_main(tmp_path, lambda req, cid: _tra_loi("{}"))
    assert thay == CON_LAI
    qs = _doc(tmp_path, "REQUEST_OBSERVATIONS.json")["OBSERVATIONS"]
    ky_vong = {e["case_id"]: e for e in _doc(REGD, "EXPECTED_REQUEST_HASHES.json")["EXPECTED"]}
    assert [q["case_id"] for q in qs] == CON_LAI
    for q in qs:
        e = ky_vong[q["case_id"]]
        assert q["body_sha256"] == e["body_sha256"] and q["attempt_index"] == 1
        assert q["model"] == "gemini-2.5-flash" and "?" not in q["endpoint_path"]
        assert q["request_fingerprint"] == e["request_fingerprint"]
        assert q["response_schema_sha256"] == e["response_schema_sha256"]
        assert q["has_response_schema"] is True and q["has_thinking_config"] is False
        assert q["equivalence"] == "MATCH"
    tat_ca = "\n".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*.json"))
    assert KEY_GIA not in tat_ca and "key=" not in tat_ca
    assert _bam_thu_muc(HIST) == lich_su_truoc


def test_G1_quan_sat_lay_model_tu_URL_va_khong_giu_query_chua_khoa():
    than = json.dumps({"systemInstruction": {"parts": [{"text": "P"}]},
                       "contents": [{"parts": [{"text": "U"}]}],
                       "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json",
                                            "responseSchema": {"type": "OBJECT"}}}).encode()
    req = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/"
                        "gemini-2.5-flash:generateContent?key=BI_MAT_TRONG_QUERY", content=than)
    q = B.quan_sat_request(req)
    assert q["model"] == "gemini-2.5-flash"
    assert q["endpoint_path"] == "/v1beta/models/gemini-2.5-flash:generateContent"
    assert "BI_MAT_TRONG_QUERY" not in json.dumps(q)
    assert q["body_sha256"] == hashlib.sha256(than).hexdigest() and q["body_size_bytes"] == len(than)
    assert q["temperature"] == 0.1 and q["response_mime_type"] == "application/json"


def test_G1_sau_request_ky_vong_tai_lap_trung_qua_hai_lan_va_trung_registry():
    reg = B.ca_theo_id(_reg())
    with _boi_canh_lich_su():
        lan1 = {c: B.dung_request_du_kien(reg[c]) for c in CON_LAI}
        lan2 = {c: B.dung_request_du_kien(reg[c]) for c in CON_LAI}
    assert lan1 == lan2
    ky_vong = {e["case_id"]: e for e in _doc(REGD, "EXPECTED_REQUEST_HASHES.json")["EXPECTED"]}
    assert sorted(ky_vong) == sorted(CON_LAI) and len(ky_vong) == 6
    for c in CON_LAI:
        assert lan1[c]["body_sha256"] == ky_vong[c]["body_sha256"]
        assert lan1[c]["request_fingerprint"] == ky_vong[c]["request_fingerprint"]


def test_G9_request_body_khop_harness_DOC_LAP_cua_wave_truoc():
    """Harness ở a17d00c tự bắt byte bằng MockTransport riêng; runner mới phải ra y hệt."""
    truoc = json.loads((PRIOR / "REQUEST_EQUIVALENCE.json").read_text(encoding="utf-8"))
    reg = B.ca_theo_id(_reg())
    with _boi_canh_lich_su():
        for e in truoc["EXPECTED_REQUESTS"]:
            q = B.dung_request_du_kien(reg[e["case_id_from_body"]])
            assert q["body_sha256"] == e["body_sha256"], e["case_id_from_body"]
            assert q["system_prompt_sha256"] == e["system_prompt_sha256"]
            assert q["response_schema_sha256"] == e["response_schema_sha256_default_sorted"]
            assert q["model"] == e["model_from_url"] and q["temperature"] == e["temperature"]


def test_G1_doi_prompt_schema_model_nhiet_do_hoac_de_thi_dau_van_doi(monkeypatch):
    import app.ai.pipeline as PL
    import app.simulation.semantic_program.analyze_contract as AC
    reg = B.ca_theo_id(_reg())
    goc = B.dung_request_du_kien(reg["P06"])
    assert B.dung_request_du_kien(reg["P07"])["body_sha256"] != goc["body_sha256"]      # đề
    goc_skill, goc_schema = PL.load_skill, AC.analyze_schema_for
    monkeypatch.setattr(PL, "load_skill", lambda n: goc_skill(n) + " ")
    assert B.dung_request_du_kien(reg["P06"])["body_sha256"] != goc["body_sha256"]       # prompt
    monkeypatch.setattr(PL, "load_skill", goc_skill)
    monkeypatch.setattr(AC, "analyze_schema_for",
                        lambda d: {**goc_schema(d), "description": "x"})
    q = B.dung_request_du_kien(reg["P06"])
    assert q["body_sha256"] != goc["body_sha256"]                                         # schema
    assert q["response_schema_sha256"] != goc["response_schema_sha256"]
    monkeypatch.setattr(AC, "analyze_schema_for", goc_schema)
    monkeypatch.setattr(gemini, "MODEL", "gemini-khac")
    q = B.dung_request_du_kien(reg["P06"])
    assert q["body_sha256"] == goc["body_sha256"]                    # model nằm ở URL, không ở thân
    assert q["model"] == "gemini-khac" and q["request_fingerprint"] != goc["request_fingerprint"]
    monkeypatch.setattr(gemini, "MODEL", "gemini-2.5-flash")

    def bat(temp: float) -> str:
        thay: list[httpx.Request] = []
        cong = L.CongQuetCam(httpx.MockTransport(lambda r: (thay.append(r), _tra_loi("{}"))[1]),
                             2, BoKhuBiMat((KEY_GIA,)))
        cong.dat_ca("T")

        async def goi():
            with L.cai_cong_http(cong), stage_scope("semantic_analyze"):
                await gemini.call_gemini(KEY_GIA, "s", "u", None, temp)
        asyncio.run(goi())
        return B.quan_sat_request(thay[0])["body_sha256"]
    assert bat(0.1) != bat(0.2)                                                            # nhiệt độ


def test_G1_request_LECH_ky_vong_bi_chan_TRUOC_transport():
    inner_goi: list[int] = []
    cong = B.tao_cong_completion(
        httpx.MockTransport(lambda r: (inner_goi.append(1), _tra_loi("{}"))[1]),
        ["P06"], BoKhuBiMat((KEY_GIA,)), _gt(),
        du_kien={"P06": {"request_fingerprint": "0" * 64}})
    ca = B.ca_theo_id(_reg())["P06"]
    r, env = asyncio.run(B.chay_mot_ca(ca, _gt(), KEY_GIA, cong))
    assert inner_goi == [] and cong.sent == 0
    assert cong.tuong_duong_loi is not None and cong.tuong_duong_loi["case_id"] == "P06"
    assert r["OUTCOME"] == "REQUEST_EQUIVALENCE_FAILURE" and env is None


# ══ G2 — TRẦN TRANSPORT DẪN TỪ HÀNG ĐỢI ════════════════════════════════════
def test_G2_hang_doi_con_lai_dung_sau_ca_dung_thu_tu():
    cu = json.loads((HIST / "CASE_RESULTS_REDACTED.json").read_text(encoding="utf-8"))["CASES"]
    assert B.hang_doi_con_lai(_reg(), cu) == CON_LAI
    assert B.hang_doi_con_lai(_reg(), []) == ["P01", "P02", "P03", "N01", "P04", "P05",
                                             "P06", "P07", "P08", "N02", "N03", "N04"]


def test_G2_request_thu_7_bi_chan_o_transport_ke_ca_khi_moi_ca_con_ngan_sach():
    cong = B.tao_cong_completion(httpx.MockTransport(lambda r: _tra_loi("{}")), CON_LAI,
                                 BoKhuBiMat((KEY_GIA,)), _gt())
    assert cong.max_http_requests == 6 and cong.tran_theo_tang == {
        "vision": 0, "analyze": 6, "synthesis": 0}

    async def gui():
        with L.cai_cong_http(cong):
            for i in range(7):
                cong.dat_ca(f"X{i}")
                with L.dung_ngan_sach(gemini.ApiBudget(max_api_calls=1, max_attempts=1,
                                                       max_logical_calls=1)):
                    with stage_scope("semantic_analyze"):
                        await gemini.call_gemini(KEY_GIA, "s", f"u{i}", None, 0.1)
    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(gui())
    assert cong.sent == 6 and cong.blocked == 1


def test_G2_A_ngan_sach_lan_completion_la_6_khong_phai_12(tmp_path):
    _chay_main(tmp_path, lambda req, cid: _tra_loi("{}"))
    p = _doc(tmp_path, "REQUEST_BUDGET_PROOF.json")
    assert p["MAX_HTTP_REQUESTS"] == 6 and p["HTTP_REQUESTS_SENT"] == 6
    assert p["TRAN_THEO_TANG"] == {"vision": 0, "analyze": 6, "synthesis": 0}
    assert p["VISION_HTTP_REQUESTS"] == 0 and p["SYNTHESIS_HTTP_REQUESTS"] == 0
    assert p["RETRIES"] == 0 and p["REPAIR_REQUESTS"] == 0
    assert p["QUEUE"] == CON_LAI


def test_G2_B_timeout_o_P06_dung_ngay_mot_request(tmp_path, lich_su_truoc):
    def xu_ly(req, cid):
        raise httpx.ReadTimeout("timeout giả lập", request=req)
    _, thay = _chay_main(tmp_path, xu_ly)
    assert thay == ["P06"]
    kq = _doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")
    assert [r["CASE_ID"] for r in kq["CASES"]] == ["P06"]
    assert kq["STOP_REASON"] == "PROVIDER_ERROR"
    assert kq["CASES"][0]["ATTRIBUTION"]["PRIMARY"] == "PROVIDER_ERROR"
    assert _bam_thu_muc(HIST) == lich_su_truoc


# ══ G3 — CA ÂM KHÔNG PHẠT QUAN HỆ ĐỀ NÓI THẲNG ═══════════════════════════
def test_G3_registry_quan_he_khoa_cung_va_chuan_hoa_theo_san_pham():
    p = REGD / "NEGATIVE_EXPLICIT_RELATION_REGISTRY.json"
    assert _sha_lf(p) == SHA_REGISTRY_QUAN_HE
    d = json.loads(p.read_text(encoding="utf-8"))
    assert sorted(d["CASES"]) == CA_AM and len(d["CASES"]) == 4
    for cid in CA_AM:
        co = {(r["kind"], tuple(r["canonical_args"])) for r in d["CASES"][cid]["relations"]}
        assert co == QUAN_HE_TOI_THIEU[cid], cid
        assert d["CASES"][cid]["input_sha256"] == hashlib.sha256(
            B.ca_theo_id(_reg())[cid]["input_text"].encode("utf-8")).hexdigest()
    # Dạng chuẩn hoá trong registry PHẢI trùng bộ chuẩn hoá của sản phẩm trên cách viết hoán vị.
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    from app.simulation.semantic_program.structured_relations import kiem_va_chuan_hoa
    for cid in CA_AM:
        c = build_request_contract(DOC_DUNG_CA_AM[cid],
                                   problem_text=B.ca_theo_id(_reg())[cid]["input_text"],
                                   domain="hinh_hoc")
        assert {q.khoa for q in kiem_va_chuan_hoa(c).relations} == QUAN_HE_TOI_THIEU[cid], cid
    n01 = d["N01_PUBLISHED_CORRECTION"]
    assert n01["UNVERIFIED_EXTRA_RELATION_COUNT"] == 1 and n01["HALLUCINATED_CRITICAL_FACT_COUNT"] == 1


@pytest.mark.parametrize("cid", CA_AM)
def test_G3_E_doc_DUNG_de_khong_bi_tinh_la_bia(cid):
    r = _mot_ca(cid, DOC_DUNG_CA_AM[cid])
    assert r["RELATION"]["UNVERIFIED_EXTRA_RELATION_COUNT"] == 0, cid
    assert r["RELATION"]["EXTRA_DERIVED_AS_GIVEN_COUNT"] == 0
    assert r["RELATION"]["MISSING_RELATION_COUNT"] == 0
    assert r["HALLUCINATED_CRITICAL_FACT_COUNT"] == 0


def test_G3_quan_he_BIA_van_bi_bat_va_gia_dinh_khong_thanh_GIVEN():
    bia = json.loads(json.dumps(DOC_DUNG_CA_AM["N02"]))
    bia["input_facts"].append(_f("bia", "TV vuông góc TX", "TV ⟂ TX"))
    bia["geometric_relations"].append({"kind": "perpendicular_lines", "line": ["V", "T"],
                                       "other_line": ["X", "T"], "source_fact_id": "bia"})
    r = _mot_ca("N02", bia)
    assert r["RELATION"]["UNVERIFIED_EXTRA_RELATION_COUNT"] == 1
    assert r["HALLUCINATED_CRITICAL_FACT_COUNT"] == 1
    assert r["UNSAFE_ACCEPTANCE"] is True             # quan hệ bịa dựng được cảnh ⇒ bắt
    # N01: khai đỉnh vuông nhưng TỰ ĐÁNH DẤU giả định ⇒ không dùng được, vẫn đếm một lần bịa
    gd = json.loads(json.dumps(DOC_DUNG_CA_AM["N01"]))
    gd["input_facts"].append(_f("day", "tam giác XYZ vuông", "tam giác XYZ vuông"))
    gd["geometric_relations"].append({"kind": "perpendicular_lines", "line": ["X", "Y"],
                                      "other_line": ["X", "Z"], "source_fact_id": "day",
                                      "model_assumption": True})
    r = _mot_ca("N01", gd)
    assert r["RELATION"]["UNVERIFIED_EXTRA_RELATION_COUNT"] == 1
    assert r["HALLUCINATED_CRITICAL_FACT_COUNT"] == 1   # = đính chính N01 đã công bố
    assert r["SAFE_REJECTION"] is True and r["UNSAFE_ACCEPTANCE"] is False


# ══ G8 — TỪ CHỐI AN TOÀN ≠ TỪ CHỐI ĐÚNG KHIẾM KHUYẾT ═════════════════════
def test_G8_registry_tu_choi_rieng_tung_ca_khong_dung_11_ma_chung():
    p = REGD / "NEGATIVE_TARGETED_REJECTION_REGISTRY.json"
    assert _sha_lf(p) == SHA_REGISTRY_TU_CHOI
    d = json.loads(p.read_text(encoding="utf-8"))["CASES"]
    assert sorted(d) == CA_AM
    chung = set(_gt()["negative"]["N01"]["acceptable_rejection_codes"])
    assert {c: d[c]["allowed_exact_codes"] for c in CA_AM} == {
        "N01": ["BASE_PERPENDICULAR_RELATION_MISSING"],
        "N02": ["BASE_PERPENDICULAR_RELATION_MISSING"],
        "N03": ["LINE_PLANE_RELATION_MISSING"],
        "N04": ["INVALID_CONFLICT"]}
    assert all(len(d[c]["allowed_exact_codes"]) < len(chung) for c in CA_AM)


@pytest.mark.parametrize("cid", ["N02", "N03", "N04"])
def test_G8_D_phan_hoi_rong_co_the_AN_TOAN_nhung_KHONG_BAO_GIO_dung_khiem_khuyet(cid):
    r = _mot_ca(cid, "{}")
    assert r["SAFE_REJECTION"] is True
    assert r["TARGETED_REJECTION_MATCH"] == "NO"
    assert r["ANALYZE_INFORMATION_COMPLETENESS"] == "FAIL"


@pytest.mark.parametrize("cid", ["N01", "N02", "N03"])
def test_G8_E_doc_dung_va_tu_choi_dung_ma_thi_TARGETED_YES(cid):
    r = _mot_ca(cid, DOC_DUNG_CA_AM[cid])
    assert r["SAFE_REJECTION"] is True and r["UNSAFE_ACCEPTANCE"] is False
    assert r["ANALYZE_INFORMATION_COMPLETENESS"] == "PASS"
    assert r["TARGETED_REJECTION_MATCH"] == "YES", r.get("TARGETED_DETAIL")


def test_G8_E_N04_doc_dung_bi_he_TU_CHOI_sau_ban_sua_an_toan():
    """Trước `STRUCTURED_RELATION_SAFETY_REPAIR`: đọc ĐÚNG N04 (vuông tại G VÀ tại H) mà hệ
    vẫn dựng cảnh (UNSAFE). Nay FactGraph từ chối bằng `STRUCTURED_RELATION_CONTRADICTION`
    (trạng thái adapter `INVALID_CONFLICT`) trước khi tới compiler.

    ⚠️ TARGETED vẫn NO, và đó là hệ quả CÓ CHỦ ĐÍCH của registry đóng băng: registry đăng ký
    trước ghim `allowed_exact_codes = ["INVALID_CONFLICT"]` — mã mâu thuẫn duy nhất tồn tại lúc
    đó — còn bộ đo so `REJECTION_CODE` (mã cụ thể). Registry là artifact bất biến của wave trước;
    N04 nay là ca HỒI QUY, không còn là bằng chứng tổng quát. Xem
    `structured-relation-safety-repair/DATASET_ROLE_DECISION.json`."""
    r = _mot_ca("N04", DOC_DUNG_CA_AM["N04"])
    assert r["HALLUCINATED_CRITICAL_FACT_COUNT"] == 0          # mô hình KHÔNG sai
    assert r["SAFE_REJECTION"] is True and r["UNSAFE_ACCEPTANCE"] is False
    assert r["REJECTION_CODE"] == "STRUCTURED_RELATION_CONTRADICTION"
    assert r["BUILD"]["ADAPTER_STATUS"] == "INVALID_CONFLICT"
    assert r["TARGETED_REJECTION_MATCH"] == "NO"
    assert r["TARGETED_DETAIL"]["minimum_relations_observed"] is True
    assert r["TARGETED_DETAIL"]["rejection_code_matches"] is False
    assert r["ATTRIBUTION"]["PRIMARY"] is None


# ══ G5 — QUY KẾT THẤT BẠI ĐƯỢC GỌI THẬT ═══════════════════════════════════
def test_G5_runner_GOI_quy_ket_that_bai_trong_duong_cham_tung_ca():
    cay = ast.parse((GOC / "scripts" / "run_multicase_benchmark.py").read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "chay_mot_ca")
    goi = {getattr(n.func, "id", getattr(n.func, "attr", "")) for n in ast.walk(ham)
           if isinstance(n, ast.Call)}
    assert "quy_ket_that_bai" in goi


def test_G5_quan_he_sai_dang_quy_ve_MODEL_MALFORMED_RELATION():
    p = _payload_duong("P07")
    rv, a, b = p["geometric_relations"][0]["line"] + p["geometric_relations"][0]["other_line"][1:]
    p["geometric_relations"][0] = {"kind": "perpendicular_lines", "line": [rv, a],
                                   "plane": [rv, a, b], "source_fact_id": "day_vuong"}
    r = _mot_ca("P07", p)
    assert r["OUTCOME"] == "ANALYZE_INCOMPLETE_OR_UNSAFE"
    assert r["ATTRIBUTION"]["PRIMARY"] == "MODEL_MALFORMED_RELATION"
    assert "REQUIRED_RELATION_MISSING" in r["ATTRIBUTION"]["TAGS"]


def test_G5_quy_ket_tren_ban_ghi_lich_su_trung_quy_ket_hau_kiem_da_cong_bo():
    G = _G()
    cu = {r["CASE_ID"]: r for r in json.loads(
        (HIST / "CASE_RESULTS_REDACTED.json").read_text(encoding="utf-8"))["CASES"]}
    for cid in ("P03", "P05"):
        assert G.quy_ket_that_bai(cu[cid])["PRIMARY"] == "MODEL_MALFORMED_RELATION"
    for cid in ("P01", "P02", "P04", "N01"):
        assert G.quy_ket_that_bai(cu[cid])["PRIMARY"] is None
    assert G.quy_ket_that_bai(cu["P06"])["PRIMARY"] == "PROVIDER_ERROR"


def test_G5_moi_ma_quy_ket_nam_trong_bang_ma_on_dinh():
    G = _G()
    assert {"PROVIDER_ERROR", "JSON_PARSE_FAILURE", "PYDANTIC_FAILURE", "MODEL_MALFORMED_RELATION",
            "REQUIRED_RELATION_MISSING", "UNVERIFIED_RELATION", "MODEL_ASSUMPTION_USED",
            "FACT_GRAPH_REJECTION", "COMPILER_UNSUPPORTED", "PROGRAM_VALIDATION_FAILURE",
            "GROUNDING_REJECTION", "ROUTE_REJECTION", "VISUAL_GATE_REJECTION", "TOPOLOGY_FAILURE",
            "FINAL_MEMORY_FAILURE", "ANSWER_FAILURE", "SILENT_QUALITY_FAILURE"} <= set(G.MA_QUY_KET)
    duong = {"CASE_ID": "P01", "KIND": "positive", "MODEL_OUTPUT_RECEIVED": True,
             "RELATION": {"MISSING_RELATION_COUNT": 0, "UNVERIFIED_EXTRA_RELATION_COUNT": 0,
                          "EXTRA_DERIVED_AS_GIVEN_COUNT": 0, "MODEL_ASSUMPTION_COUNT": 0,
                          "REJECTED_RELATION_CODES": [], "SOURCE_FACT_RESOLUTION": "PASS"},
             "ANALYZE_PASS": True, "OUTCOME": "BUILD_FAILED"}
    for build, ma in (({"ADAPTER_STATUS": "INVALID_CONFLICT"}, "FACT_GRAPH_REJECTION"),
                      ({"ADAPTER_STATUS": "VALID", "COMPILER_ELIGIBILITY": "UNSUPPORTED_X"},
                       "COMPILER_UNSUPPORTED"),
                      ({"ADAPTER_STATUS": "VALID", "COMPILER_ELIGIBILITY": "SUPPORTED",
                        "COMPILE_STATUS": "COMPILED", "PYDANTIC_PROGRAM_VALIDATION": "PASS",
                        "ROUTE_RESULT": "rejected/input_not_grounded"}, "GROUNDING_REJECTION")):
        assert _G().quy_ket_that_bai({**duong, "BUILD": build})["PRIMARY"] == ma
    im_lang = {"ADAPTER_STATUS": "VALID", "COMPILER_ELIGIBILITY": "SUPPORTED",
               "COMPILE_STATUS": "COMPILED", "PYDANTIC_PROGRAM_VALIDATION": "PASS",
               "DETERMINISTIC": True, "ROUTE_RESULT": "served", "VISUAL_OBLIGATION_GATE": "COVERED",
               "TOPOLOGY_RESULT": "PASS", "SQUARED_LENGTHS_OK": True, "PERPENDICULAR_OK": True,
               "NON_COLLINEAR_OK": True, "FINAL_MEMORY_OK": True, "ANSWER_OK": False,
               "SILENT_QUALITY_FAILURE": True}
    q = _G().quy_ket_that_bai({**duong, "BUILD": im_lang})
    assert q["PRIMARY"] == "SILENT_QUALITY_FAILURE" and "ANSWER_FAILURE" in q["TAGS"]


# ══ G6 — TOKEN UNKNOWN, ĐỘ TRỄ TÁCH LỖI ═══════════════════════════════════
def _lt(cid, *, usage=True, loi=False, ms=1000.0, dat=True):
    r = {"CASE_ID": cid, "KIND": "positive", "HTTP_REQUESTS_FOR_CASE": 1, "LATENCY_MS": ms,
         "HTTP_STATUS": None if loi else 200, "MODEL_OUTPUT_RECEIVED": (not loi) and dat,
         "PROVIDER_ERROR": "ReadTimeout: " if loi else None, "RUNNER_EXCEPTION": None,
         "USAGE": ({"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 5,
                    "totalTokenCount": 125} if usage and not loi else {})}
    return r


def test_G6_du_usage():
    t = _G().tong_hop_token([_lt("A"), _lt("B")])
    assert t["TOTAL_ANALYZE_TOKENS"] == 250 and t["UNKNOWN_USAGE_COUNT"] == 0
    assert t["KNOWN_SUBTOTAL"]["input"] == 200


def test_G6_mot_usage_thieu_thi_UNKNOWN_khong_bao_gio_0():
    t = _G().tong_hop_token([_lt("A"), _lt("B", usage=False)])
    assert t["TOTAL_ANALYZE_TOKENS"] == "UNKNOWN" and t["UNKNOWN_USAGE_COUNT"] == 1
    assert t["KNOWN_SUBTOTAL"]["total"] == 125
    assert [x["total"] for x in t["PER_ATTEMPT"]] == [125, "UNKNOWN"]


def test_G6_timeout_khong_vao_p95_thanh_cong():
    d = _G().tong_hop_do_tre([_lt("A", ms=5000.0), _lt("B", ms=6000.0), _lt("C", loi=True, ms=120002.8)])
    assert d["SUCCESSFUL_COUNT"] == 2 and d["SUCCESSFUL_P95_MS"] == 6000.0
    assert d["PROVIDER_ERROR_WAIT_MS"] == [120002.8]
    t = _G().tong_hop_token([_lt("C", loi=True)])
    assert t["TOTAL_ANALYZE_TOKENS"] == "UNKNOWN" and t["UNKNOWN_USAGE_COUNT"] == 1


def test_G6_chi_co_loi_provider():
    d = _G().tong_hop_do_tre([_lt("C", loi=True, ms=120000.0)])
    assert d["SUCCESSFUL_COUNT"] == 0 and d["SUCCESSFUL_P50_MS"] is None
    assert d["SUCCESSFUL_P95_MS"] is None and d["PROVIDER_ERROR_WAIT_MS"] == [120000.0]


def test_G6_luot_VOID_cua_bo_do_khong_tinh_la_cho_loi_provider():
    """Dữ liệu lịch sử THẬT: P02 lượt 1 chết vì `Event loop is closed` (lỗi bộ đo, 2,9 ms),
    P06 lượt 2 là timeout provider thật. Chỉ P06 được vào thời gian chờ lỗi provider;
    cả hai vẫn là token UNKNOWN (request đã gửi, không có usage)."""
    k = _G().tong_hop(None)
    assert k["LATENCY"]["AGGREGATE"]["PROVIDER_ERROR_WAIT_MS"] == [120002.8]
    assert 120002.8 != k["LATENCY"]["AGGREGATE"]["SUCCESSFUL_P95_MS"]
    assert k["TOKENS"]["AGGREGATE"]["UNKNOWN_USAGE_COUNT"] == 2
    assert k["TOKENS"]["AGGREGATE"]["TOTAL_ANALYZE_TOKENS"] == "UNKNOWN"


def test_G6_hon_hop_va_output_hong_khong_tinh_la_thanh_cong():
    d = _G().tong_hop_do_tre([_lt("A", ms=4000.0), _lt("B", ms=9000.0, dat=False),
                              _lt("C", loi=True, ms=120000.0)])
    assert d["SUCCESSFUL_COUNT"] == 1 and d["SUCCESSFUL_P50_MS"] == 4000.0


# ══ G7 — ENVELOPE GHI NGAY SAU TỪNG CA ═══════════════════════════════════
def _p06_dung_roi(xu_ly_p07):
    def xu_ly(req, cid):
        if cid == "P06":
            return _tra_loi(json.dumps(_payload_duong("P06"), ensure_ascii=False))
        return xu_ly_p07(req)
    return xu_ly


def test_G7_tien_trinh_CHET_sau_P06_van_giu_envelope_P06(tmp_path, lich_su_truoc):
    def chet(req):
        raise SapNguon()
    with pytest.raises(SapNguon):
        _chay_main(tmp_path, _p06_dung_roi(chet))
    env = tmp_path / "envelopes" / "P06.json"
    assert env.exists(), "envelope P06 mất khi tiến trình chết ở P07"
    assert json.loads(env.read_text(encoding="utf-8"))["status"] == "ok"
    assert not list(tmp_path.rglob("*.tmp")) and not (tmp_path / "envelopes" / "P07.json").exists()
    assert _bam_thu_muc(HIST) == lich_su_truoc


def test_G7_C_P06_dat_P07_timeout_hai_request_giu_P06(tmp_path, lich_su_truoc):
    def to(req):
        raise httpx.ReadTimeout("timeout giả lập", request=req)
    _, thay = _chay_main(tmp_path, _p06_dung_roi(to))
    assert thay == ["P06", "P07"]
    assert sorted(p.name for p in (tmp_path / "envelopes").iterdir()) == ["P06.json"]
    kq = _doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")
    assert [r["OUTCOME"] for r in kq["CASES"]] == ["FULL_PIPELINE_PASS", "ANALYZE_OUTPUT_INVALID"]
    assert _bam_thu_muc(HIST) == lich_su_truoc


def test_G7_ghi_nguyen_tu_that_bai_giua_chung_khong_de_lai_file_do_dang(tmp_path, monkeypatch):
    def hong(*a, **k):
        raise OSError("đĩa đầy giả lập")
    monkeypatch.setattr(B.os, "replace", hong)
    with pytest.raises(OSError):
        B.ghi_envelope_nguyen_tu(tmp_path, "P06", {"status": "ok"})
    assert list(tmp_path.rglob("*")) == [] or all(p.is_dir() for p in tmp_path.rglob("*"))
    monkeypatch.undo()
    B.ghi_envelope_nguyen_tu(tmp_path, "P06", {"status": "ok"})
    assert json.loads((tmp_path / "P06.json").read_text(encoding="utf-8")) == {"status": "ok"}
    assert not list(tmp_path.glob("*.tmp"))


# ══ G4 — BỘ TỔNG HỢP TẤT ĐỊNH ═════════════════════════════════════════════
def _chi_so(**doi):
    base = {"MEASUREMENT_VALID": True, "CASES_REGISTERED": 12, "CASES_WITH_OUTCOME": 12,
            "MISSING_OUTCOME_REASONS": {}, "POSITIVE_REGISTERED": 8,
            "POSITIVE_FULL_PIPELINE_PASS": 8, "NEGATIVE_REGISTERED": 4,
            "NEGATIVE_SAFE_REJECTION": 4, "UNSAFE_ACCEPTANCE": 0, "UNVERIFIED_USED_FOR_BUILD": 0,
            "CRITICAL_RELATION_ACCURACY": 1.0, "SILENT_QUALITY_FAILURE": 0,
            "REPEATED_FAILURE_CLUSTERS": []}
    base.update(doi)
    return base


def test_G4_bang_phan_loai_va_thu_tu_uu_tien():
    pl = _G().phan_loai
    assert pl(_chi_so()) == "STRONG_PILOT_RESULT"
    assert pl(_chi_so(CRITICAL_RELATION_ACCURACY=0.95)) == "READY_FOR_CANARY_DESIGN"
    assert pl(_chi_so(POSITIVE_FULL_PIPELINE_PASS=7, CRITICAL_RELATION_ACCURACY=0.9)) == \
        "READY_FOR_CANARY_DESIGN"
    assert pl(_chi_so(POSITIVE_FULL_PIPELINE_PASS=6, CRITICAL_RELATION_ACCURACY=0.8)) == \
        "MORE_EVIDENCE_NEEDED"
    assert pl(_chi_so(POSITIVE_FULL_PIPELINE_PASS=5, CRITICAL_RELATION_ACCURACY=0.8)) == \
        "MORE_EVIDENCE_NEEDED"
    assert pl(_chi_so(POSITIVE_FULL_PIPELINE_PASS=4)) == "NOT_READY"
    assert pl(_chi_so(POSITIVE_FULL_PIPELINE_PASS=7, CRITICAL_RELATION_ACCURACY=0.74)) == "NOT_READY"
    assert pl(_chi_so(POSITIVE_FULL_PIPELINE_PASS=6,
                      REPEATED_FAILURE_CLUSTERS=["MODEL_MALFORMED_RELATION"])) == "NOT_READY"
    assert pl(_chi_so(SILENT_QUALITY_FAILURE=1)) == "NOT_READY"
    assert pl(_chi_so(UNSAFE_ACCEPTANCE=1, NEGATIVE_SAFE_REJECTION=3)) == "UNSAFE"
    assert pl(_chi_so(UNVERIFIED_USED_FOR_BUILD=1)) == "UNSAFE"
    thieu = {"CASES_WITH_OUTCOME": 11, "MISSING_OUTCOME_REASONS": {"N04": "PROVIDER_ERROR"}}
    assert pl(_chi_so(**thieu)) == "PROVIDER_INCOMPLETE"
    assert pl(_chi_so(**thieu, UNSAFE_ACCEPTANCE=1)) == "UNSAFE"          # UNSAFE thắng thiếu ca
    assert pl(_chi_so(CASES_WITH_OUTCOME=11,
                      MISSING_OUTCOME_REASONS={"N04": "RUNNER_EXCEPTION"})) == "MEASUREMENT_INVALID"
    assert pl(_chi_so(MEASUREMENT_VALID=False, UNSAFE_ACCEPTANCE=1)) == "MEASUREMENT_INVALID"


def test_G4_nhan_next_action_dung_dac_ta():
    assert _G().NEXT_ACTION == NEXT_DUNG


def _rec_duong(cid, dat=True):
    return {"CASE_ID": cid, "KIND": "positive", "HTTP_REQUESTS_FOR_CASE": 1, "HTTP_STATUS": 200,
            "LATENCY_MS": 5000.0, "MODEL_OUTPUT_RECEIVED": True, "PROVIDER_ERROR": None,
            "RUNNER_EXCEPTION": None, "REQUEST_EQUIVALENCE": "MATCH",
            "USAGE": {"promptTokenCount": 1500, "candidatesTokenCount": 500,
                      "thoughtsTokenCount": 300, "totalTokenCount": 2300},
            "RELATION": {"EXPECTED_GIVEN_RELATION_COUNT": 2, "CORRECT_CRITICAL_RELATION_COUNT": 2,
                         "MISSING_RELATION_COUNT": 0, "DUPLICATE_RELATION_COUNT": 0,
                         "UNVERIFIED_EXTRA_RELATION_COUNT": 0, "EXTRA_DERIVED_AS_GIVEN_COUNT": 0,
                         "MODEL_ASSUMPTION_COUNT": 0, "REJECTED_RELATION_CODES": [],
                         "SOURCE_FACT_RESOLUTION": "PASS", "CRITICAL_RELATION_ACCURACY": 1.0},
            "ANALYZE_PASS": True, "OUTCOME": "FULL_PIPELINE_PASS" if dat else "BUILD_FAILED",
            "BUILD": {"ADAPTER_STATUS": "VALID", "COMPILER_ELIGIBILITY": "SUPPORTED",
                      "COMPILE_STATUS": "COMPILED", "PYDANTIC_PROGRAM_VALIDATION": "PASS",
                      "DETERMINISTIC": True, "ROUTE_RESULT": "served",
                      "VISUAL_OBLIGATION_GATE": "COVERED", "TOPOLOGY_RESULT": "PASS",
                      "SQUARED_LENGTHS_OK": True, "PERPENDICULAR_OK": True, "NON_COLLINEAR_OK": True,
                      "FINAL_MEMORY_OK": True, "ANSWER_OK": dat, "FULL_PIPELINE_PASS": dat,
                      "SILENT_QUALITY_FAILURE": not dat}}


def _rec_am(cid, an_toan=True):
    return {"CASE_ID": cid, "KIND": "negative", "HTTP_REQUESTS_FOR_CASE": 1, "HTTP_STATUS": 200,
            "LATENCY_MS": 6000.0, "MODEL_OUTPUT_RECEIVED": True, "PROVIDER_ERROR": None,
            "RUNNER_EXCEPTION": None, "REQUEST_EQUIVALENCE": "MATCH",
            "USAGE": {"promptTokenCount": 1500, "candidatesTokenCount": 500,
                      "thoughtsTokenCount": 900, "totalTokenCount": 2900},
            "RELATION": {"UNVERIFIED_EXTRA_RELATION_COUNT": 0, "EXTRA_DERIVED_AS_GIVEN_COUNT": 0,
                         "MODEL_ASSUMPTION_COUNT": 0, "MISSING_RELATION_COUNT": 0,
                         "DUPLICATE_RELATION_COUNT": 0, "REJECTED_RELATION_CODES": []},
            "HALLUCINATED_CRITICAL_FACT_COUNT": 0,
            "SAFE_REJECTION": an_toan, "UNSAFE_ACCEPTANCE": not an_toan,
            "OUTCOME": "SAFE_REJECTION" if an_toan else "UNSAFE_ACCEPTANCE",
            "TARGETED_REJECTION_MATCH": "YES" if an_toan else "NO",
            "ANALYZE_INFORMATION_COMPLETENESS": "PASS",
            "BUILD": {"COMPILE_STATUS": "NOT_ELIGIBLE" if an_toan else "COMPILED"}}


def test_G4_chi_lich_su_la_PROVIDER_INCOMPLETE_va_dem_dung_lan_thu():
    k = _G().tong_hop(None)
    c = k["COUNTS"]
    assert c["HISTORICAL_ANALYZE_REQUESTS"] == 8 and c["COMPLETION_ANALYZE_REQUESTS"] == 0
    assert c["VOID_ATTEMPTS"] == 1 and c["PROVIDER_ERROR_ATTEMPTS"] == 1
    assert c["VALID_PROVIDER_RESPONSES"] == 6
    assert c["UNIQUE_CASES_WITH_FINAL_OUTCOME"] == 6 and c["UNIQUE_CASES_WITHOUT_FINAL_OUTCOME"] == 6
    assert k["CLASSIFICATION"] == "PROVIDER_INCOMPLETE"
    assert k["NEXT_ACTION"] == "RETRY_STILL_MISSING_CASES_LATER"


def test_G4_moi_ca_MOT_ket_cuc_P06_khong_thanh_hai_ca():
    moi = [_rec_duong("P06"), _rec_duong("P07"), _rec_duong("P08"),
           _rec_am("N02"), _rec_am("N03"), _rec_am("N04")]
    k = _G().tong_hop(moi)
    assert sorted(k["CASES"]) == sorted(["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08",
                                         "N01", "N02", "N03", "N04"])
    assert k["CASES"]["P06"]["FINAL_SOURCE"] == "completion"
    assert k["CASES"]["P06"]["ATTEMPT_COUNT"] == 2          # timeout lịch sử + completion
    assert k["CASES"]["P02"]["ATTEMPT_COUNT"] == 2          # void + hợp lệ
    assert k["COUNTS"]["TOTAL_ANALYZE_REQUESTS"] == 14
    assert k["COUNTS"]["UNIQUE_CASES_WITH_FINAL_OUTCOME"] == 12


def test_G4_dinh_chinh_N01_va_cum_loi_lap_P03_P05():
    k = _G().tong_hop([_rec_duong("P06"), _rec_duong("P07"), _rec_duong("P08"),
                       _rec_am("N02"), _rec_am("N03"), _rec_am("N04")])
    n01 = k["CASES"]["N01"]
    assert n01["UNVERIFIED_EXTRA_RELATION_COUNT"] == 1 and n01["HALLUCINATED_CRITICAL_FACT_COUNT"] == 1
    assert n01["CORRECTION_APPLIED"] is True
    assert k["CLUSTERS"]["MODEL_MALFORMED_RELATION"] == ["P03", "P05"]
    assert k["METRICS"]["REPEATED_FAILURE_CLUSTERS"] == ["MODEL_MALFORMED_RELATION"]
    assert k["METRICS"]["POSITIVE_FULL_PIPELINE_PASS"] == 6
    assert k["CLASSIFICATION"] == "NOT_READY"                # cụm lỗi lặp
    assert k["CASES"]["N01"]["TARGETED_REJECTION_MATCH"] == "NOT_MEASURED"


def test_G4_mot_ca_am_bi_phuc_vu_thi_UNSAFE():
    k = _G().tong_hop([_rec_duong("P06"), _rec_duong("P07"), _rec_duong("P08"),
                       _rec_am("N02"), _rec_am("N03"), _rec_am("N04", an_toan=False)])
    assert k["CLASSIFICATION"] == "UNSAFE"
    assert k["NEXT_ACTION"] == "STRUCTURED_RELATION_SAFETY_REPAIR"


def test_G4_tai_lap_trung_byte_va_lich_su_bi_sua_thi_MEASUREMENT_INVALID(tmp_path):
    G = _G()
    moi = [_rec_duong("P06"), _rec_am("N02")]
    a = json.dumps(G.tong_hop(moi), ensure_ascii=False, sort_keys=True)
    b = json.dumps(G.tong_hop(moi), ensure_ascii=False, sort_keys=True)
    assert a == b
    import shutil
    ban = tmp_path / "hist"
    shutil.copytree(HIST, ban)
    p = ban / "CASE_RESULTS_REDACTED.json"
    p.write_text(p.read_text(encoding="utf-8").replace('"P03"', '"P03 "', 1), encoding="utf-8")
    k = G.tong_hop(moi, hist_dir=ban)
    assert k["CLASSIFICATION"] == "MEASUREMENT_INVALID"
    assert "HISTORICAL_EVIDENCE_DRIFT" in k["MEASUREMENT_INVALID_REASONS"]


def test_G4_request_lech_trong_completion_thi_MEASUREMENT_INVALID():
    r = _rec_duong("P06")
    r["REQUEST_EQUIVALENCE"] = "MISMATCH"
    k = _G().tong_hop([r])
    assert k["CLASSIFICATION"] == "MEASUREMENT_INVALID"
    assert "REQUEST_EQUIVALENCE_FAILURE" in k["MEASUREMENT_INVALID_REASONS"]
