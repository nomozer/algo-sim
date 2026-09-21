# -*- coding: utf-8 -*-
"""CHỨNG MINH OFFLINE cho lượt tái kiểm live sau khi sửa prompt.

`STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_REVALIDATION_WITH_BROWSER_CONTACT_SHEET`
(2026-09-21). **0 request thật.**

Tám kịch bản của §3 đặc tả nằm ở đây. Điều đắt nhất chúng canh không phải
"compiler chạy đúng" mà là **compiler KHÔNG chạy khi Analyze chưa đủ**, và
**không có đường lùi sang Synthesis** — vì đó chính là cám dỗ của một wave tái
kiểm: thấy thiếu một quan hệ rồi tự bù để có cái đem khoe.
"""
from __future__ import annotations

import ast
import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

GOC = Path(__file__).resolve().parents[2]
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.ai import gemini  # noqa: E402
from app.ai.telemetry import stage_scope  # noqa: E402
from app.simulation.semantic_program.analyze_contract import (  # noqa: E402
    build_request_contract,
)

import run_structured_relation_analyze_live as L  # noqa: E402
import run_structured_relation_revalidation as R  # noqa: E402
from run_photo_problem_live import BoKhuBiMat, ChanMangThat  # noqa: E402

KEY_GIA = "AIzaKHOA_GIA_CHO_TEST_KHONG_PHAI_KHOA_THAT"
REPLAY = GOC.parent / "frontend" / "scripts" / "compiler-scene-replay.mjs"


def _mf():
    return L.doc_manifest()


def _gt():
    return L.doc_ground_truth()


def _payload(**doi) -> dict:
    """Đầu ra Analyze ĐỦ hai quan hệ — điểm xuất phát của mọi biến thể."""
    p = {
        "input_facts": [
            {"id": "abc_vuong_tai_a", "label": "ABC là tam giác vuông tại A",
             "values": ["ABC là tam giác vuông tại A"]},
            {"id": "ab", "label": "AB", "values": ["3"]},
            {"id": "ac", "label": "AC", "values": ["4"]},
            {"id": "sa_vuong_goc", "label": "SA vuông góc với mặt phẳng (ABC)",
             "values": ["SA ⊥ (ABC)"]},
            {"id": "sa", "label": "SA", "values": ["5"]},
        ],
        "obligations": [{"kind": "volume", "container": "S.ABC",
                         "witness": "the_tich"}],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"],
             "other_line": ["A", "C"], "source_fact_id": "abc_vuong_tai_a"},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"],
             "plane": ["A", "B", "C"], "source_fact_id": "sa_vuong_goc"},
        ],
    }
    p.update(doi)
    return p


def _hop_dong(p: dict):
    return build_request_contract(p, problem_text=L.de_bai(_mf()), domain="hinh_hoc")


def _chay(p: dict) -> dict:
    """Analyze → (nếu đạt) FactGraph + compiler. Đúng đường runner sẽ đi."""
    mf, gt = _mf(), _gt()
    hd = _hop_dong(p)
    ss = L.so_sanh_quan_he(hd, gt)
    ds = (R.chay_compiler_va_chat_luong(hd, mf, gt)
          if R.analyze_dat(ss) else None)
    return {"ss": ss, "ds": ds,
            "ket": R.phan_loai(ss, ds, None, {"PROVIDER_ERROR": None}, True)}


# ══ 1 — ĐỦ HAI QUAN HỆ ⇒ COMPILER ĐƯỢC CHẠY ═══════════════════════════════
def test_1_du_hai_quan_he_thi_compiler_chay_va_ra_dap_so_10():
    r = _chay(_payload())
    assert R.analyze_dat(r["ss"]) is True
    ds = r["ds"]
    assert ds is not None, "Analyze đạt mà compiler không chạy"
    assert ds["COMPILER_ELIGIBILITY"] == "SUPPORTED"
    assert ds["COMPILE_STATUS"] == "COMPILED"
    assert ds["ROUTE_RESULT"] == "served"
    assert ds["VISUAL_OBLIGATION_GATE"] == "COVERED"
    assert ds["ANSWER_RESULT"] == "PASS"
    assert ds["FINAL_MEMORY_RESULT"] == "PASS"
    assert ds["COMPILER_MODEL_TOKENS"] == 0 and ds["SYNTHESIS_REQUESTS"] == 0
    assert ds["FACT_GRAPH_VERSION"] == "geometry-fact-graph/2"
    assert ds["DERIVED_PERPENDICULAR_COUNT"] == 3
    assert ds["DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH"] is True
    assert r["ket"] == "PASS"


def test_1_bis_envelope_du_de_trinh_duyet_phat_lai():
    ds = _chay(_payload())["ds"]
    env = ds["_ENVELOPE"]
    assert env.get("scene3d"), "envelope không mang cảnh ⇒ không phát lại được"
    assert env.get("domain") == "geometry"
    assert env.get("source") == "semantic_program"
    assert ds["ENVELOPE_SHA256"]


# ══ 2 — THIẾU QUAN HỆ ĐÁY ⇒ DỪNG TRƯỚC COMPILER ═══════════════════════════
def test_2_thieu_quan_he_day_thi_DUNG_truoc_compiler():
    p = _payload()
    del p["geometric_relations"][0]
    r = _chay(p)
    assert R.analyze_dat(r["ss"]) is False
    assert r["ds"] is None, "compiler ĐÃ CHẠY dù Analyze chưa đủ"
    assert r["ket"] == "MODEL_NONCOMPLIANCE_AFTER_EXPLICIT_PROMPT"
    assert r["ss"]["MISSING_RELATION_COUNT"] == 1
    assert r["ss"]["MISSING_RELATIONS"][0]["kind"] == "perpendicular_lines"


def test_2_bis_neu_van_ep_chay_thi_compiler_tu_choi_dung_ma():
    """Cổng của tầng dựng vẫn nói đúng lý do — không phải một lời từ chối chung."""
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    p = _payload()
    del p["geometric_relations"][0]
    el = C.danh_gia_eligibility(A.build_fact_graph(_hop_dong(p)).graph)
    assert el.status == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"
    assert el.reason_code == "BASE_PERPENDICULAR_RELATION_MISSING"


# ══ 3 — GIẢ ĐỊNH CỦA MÔ HÌNH KHÔNG PHẢI GIVEN ═════════════════════════════
def test_3_quan_he_day_mang_model_assumption_thi_khong_la_GIVEN():
    p = _payload()
    p["geometric_relations"][0]["model_assumption"] = True
    r = _chay(p)
    assert r["ss"]["MODEL_ASSUMPTION_COUNT"] == 1
    assert R.quan_he_khong_an_toan(r["ss"]) is True
    assert r["ket"] == "ANALYZE_RELATION_UNSAFE"
    assert r["ds"] is None
    usable = [x["usable_by_construction"] for x in r["ss"]["RELATIONS"]
              if x["kind"] == "perpendicular_lines"]
    assert usable == [False]


# ══ 4 — ĐIỂM LẠ ⇒ VALIDATION TỪ CHỐI ══════════════════════════════════════
def test_4_diem_la_bi_tu_choi():
    p = _payload()
    p["geometric_relations"][0]["other_line"] = ["A", "Z"]
    r = _chay(p)
    assert r["ss"]["POINT_REFERENCE_VALIDATION"] == "FAIL"
    assert any(e["code"] == "STRUCTURED_RELATION_REFERENCE_UNKNOWN"
               for e in r["ss"]["REJECTED_RELATION_CODES"])
    assert r["ket"] == "ANALYZE_RELATION_UNSAFE"
    assert r["ds"] is None


# ══ 5 — HỆ QUẢ ĐƯỢC KHAI THÀNH GIVEN ⇒ SAI BIÊN ═══════════════════════════
def test_5_he_qua_line_plane_khai_thanh_GIVEN_bi_phat_hien():
    p = _payload()
    p["geometric_relations"].append(
        {"kind": "perpendicular_lines", "line": ["S", "A"],
         "other_line": ["B", "C"], "source_fact_id": "sa_vuong_goc"})
    r = _chay(p)
    assert r["ss"]["EXTRA_DERIVED_AS_GIVEN_COUNT"] == 1
    assert r["ss"]["EXTRA_DERIVED_AS_GIVEN"][0]["args"] == ["A", "S", "B", "C"]
    assert r["ket"] == "ANALYZE_RELATION_UNSAFE"
    assert r["ds"] is None, "hệ quả hoá dữ kiện mà vẫn dựng hình"


# ══ 6 — PHÁT LẠI TRONG TRÌNH DUYỆT KHÔNG GỌI MODEL ════════════════════════
def test_6_script_phat_lai_khong_the_goi_model():
    nguon = REPLAY.read_text(encoding="utf-8")
    for k in ("GEMINI_API_KEY", "generativelanguage", "ALLOW_LIVE_AI",
              "call_gemini", "openai"):
        assert k not in nguon, f"script phát lại nhắc tới {k}"
    # Mọi `/api/*` phải bị chặn ở biên mạng và trả bản đóng băng.
    assert 'interceptJson("*/api/*"' in nguon
    assert '"/api/analyze"' in nguon and "ENVELOPE" in nguon
    assert 'status: 404' in nguon, "đường /api lạ phải bị từ chối, không đi tiếp"
    assert "APPLICATION_LLM_CALLS: 0" in nguon


def test_6_bis_script_phat_lai_doc_envelope_tu_TEP_chu_khong_tu_mang():
    nguon = REPLAY.read_text(encoding="utf-8")
    assert "readFileSync(ENVELOPE_PATH" in nguon
    for k in ("fetch(", "http.get", "https.get", "axios"):
        assert k not in nguon.split("const MOC")[0], f"script tự đi mạng: {k}"


def test_6_ter_runner_ghi_envelope_ra_tep_cho_trinh_duyet():
    nguon = (GOC / "scripts" / "run_structured_relation_revalidation.py"
             ).read_text(encoding="utf-8")
    assert "REPLAY_ENVELOPE.json" in nguon
    # …và chỉ ghi khi compiler thật sự dựng được cảnh.
    assert "if env is not None:" in nguon


# ══ 7, 8 — NGÂN SÁCH CHẶN TRƯỚC TRANSPORT ═════════════════════════════════
def _cong(gt, xu_ly, tran=None):
    c = L.CongQuetCam(httpx.MockTransport(xu_ly), 1, BoKhuBiMat((KEY_GIA,)),
                      tran_theo_tang=L.TRAN_THEO_TANG if tran is None else tran,
                      chuoi_cam=())
    c.dat_ca(gt["case_id"])
    return c


def _tra_loi(van: str) -> httpx.Response:
    return httpx.Response(200, json={
        "candidates": [{"content": {"parts": [{"text": van}]}}],
        "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 9,
                          "totalTokenCount": 18}})


def test_7_request_analyze_thu_hai_bi_chan_truoc_transport():
    cong = _cong(_gt(), lambda _r: _tra_loi("{}"))

    async def thu():
        with L.cai_cong_http(cong), L.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=1, max_attempts=1,
                                 max_logical_calls=1)):
            for _ in range(2):
                with stage_scope("semantic_analyze"):
                    await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(thu())
    t = cong.tong_hop()
    assert t["ANALYZE_HTTP_REQUESTS"] == 1 and t["SENT_WITHIN_BUDGET"] is True
    assert cong.inner_invocations == 1


def test_8_synthesis_bi_chan_truoc_transport():
    cong = _cong(_gt(), lambda _r: _tra_loi("{}"))

    async def thu():
        with L.cai_cong_http(cong), L.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=1, max_attempts=1,
                                 max_logical_calls=1)):
            with stage_scope("semantic_program"):
                await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(thu())
    t = cong.tong_hop()
    assert t["SYNTHESIS_HTTP_REQUESTS"] == 0
    assert t["BLOCKED_BY_STAGE"]["synthesis"] == 1
    assert cong.inner_invocations == 0, "không byte nào xuống transport"


def test_8_bis_vision_cung_bi_chan():
    cong = _cong(_gt(), lambda _r: _tra_loi("{}"))

    async def thu():
        with L.cai_cong_http(cong), L.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=1, max_attempts=1,
                                 max_logical_calls=1)):
            with stage_scope("transcribe"):
                await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(thu())
    assert cong.tong_hop()["VISION_HTTP_REQUESTS"] == 0


def test_8_ter_khong_co_duong_lui_tu_compiler_sang_synthesis():
    """Runner không được có một nhánh nào gọi tổng hợp khi compiler hỏng."""
    nguon = (GOC / "scripts" / "run_structured_relation_revalidation.py"
             ).read_text(encoding="utf-8")
    cay = ast.parse(nguon)

    def ten(n: ast.Call) -> str:
        f = n.func
        return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")

    goi = {ten(n) for n in ast.walk(cay) if isinstance(n, ast.Call)}
    assert "stage_semantic_program" not in goi
    assert "call_gemini" not in goi
    assert R.TRAN_THEO_TANG_LA["synthesis"] == 0


# ══ DANH TÍNH REQUEST — §3 và §4 ══════════════════════════════════════════
def test_request_dung_model_temperature_schema_va_khong_retry():
    mf = _mf()
    cong = _cong(_gt(), lambda _r: _tra_loi(json.dumps(_payload(), ensure_ascii=False)))
    with ChanMangThat() as chan:
        hd, err, no = asyncio.run(L.mot_luot(L.de_bai(mf), KEY_GIA, cong))
    assert chan.attempts == []
    assert hd is not None and err is None and no is None
    bc = cong.bang_chung_danh_tinh()
    assert bc["TEMPERATURE_OBSERVED"] == [mf["temperature"]]
    assert bc["GENERATION_CONFIG_UNEXPECTED_KEYS"] == []
    assert bc["FORBIDDEN_CONFIG_KEYS_PRESENT"] == []
    assert bc["SYSTEM_PROMPT_SHA256"] == [
        L._sha(gemini.load_skill("geometry_analyze"))]
    t = cong.tong_hop()
    assert t["RETRIES"] == 0 and t["ANALYZE_HTTP_REQUESTS"] == 1
    assert cong.records[0]["endpoint"].endswith(f"{mf['model']}:generateContent")


def test_tuong_duong_request_chi_khac_dung_prompt():
    with ChanMangThat() as chan:
        eq = R.kiem_tuong_duong_request()
    assert chan.attempts == []
    assert eq["REBUILD_MATCHES_COMMITTED_PRIOR"] is True, \
        "dựng lại thân request cũ KHÔNG khớp bản đã commit — phép so vô giá trị"
    assert eq["DIFFERING_JSON_POINTERS"] == ["/systemInstruction/parts/0/text"]
    assert eq["REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT"] is True
    assert eq["ENDPOINT_IDENTICAL"] is True
    assert eq["USER_TEXT_IDENTICAL"] is True
    assert eq["NO_THINKING_CONFIG"] and eq["NO_MAX_OUTPUT_TOKENS"]
    assert eq["PROMPT_DELTA_IS_REGISTERED_BLOCK"] is True


def test_cua_so_chung_bam_request_cu_PHAN_BIET_duoc_hai_prompt():
    """Băm đã commit phải GẮN với prompt CŨ, không phải với mọi prompt.

    ⚠️ Không có phép kiểm này thì `REBUILD_MATCHES_COMMITTED_PRIOR` là một cổng
    chưa từng đỏ: thay cả phép so bằng `True` cũng không test nào thấy, vì giá
    trị thật vốn đã đúng. Đo được — phép tiêm ấy ĐI LỌT ở lượt đầu.
    """
    with ChanMangThat():
        eq = R.kiem_tuong_duong_request()
    assert eq["REBUILT_PRIOR_BODY_SHA256"] == R.PRIOR_REQUEST_BODY_SHA
    # …và thân dựng bằng prompt MỚI thì KHÔNG được khớp băm ấy.
    assert eq["NEW_REQUEST_BODY_SHA256"] != R.PRIOR_REQUEST_BODY_SHA
    assert eq["PRIOR_PROMPT_SHA256"] != eq["NEW_PROMPT_SHA256"]
    assert eq["PRIOR_PROMPT_SHA_MATCHES_EXPECTED"] is True


def test_bang_phan_loai_dong_va_moi_nhan_co_next_action():
    assert set(R.NEXT_THEO_KET_QUA) == set(R.KET_QUA)


def test_ky_vong_GIVEN_khong_chua_he_qua():
    gt = _gt()
    mong = {tuple(m["canonical_args"]) for m in gt["expected_relations"]["items"]}
    suy = {tuple(m["canonical_args"])
           for m in gt["expected_derived_perpendicular"]["items"]}
    assert mong & suy == set(), "hệ quả lọt vào kỳ vọng GIVEN"
    assert len(mong) == 2 and len(suy) == 3
