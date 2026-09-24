# -*- coding: utf-8 -*-
"""CHỨNG MINH OFFLINE cho launcher `STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION`.

0 request thật. Mọi lượt đi qua `httpx.MockTransport` bọc trong CHÍNH cổng
`CongQuetCam` mà lượt live dùng — chứng minh cổng, chứ không chứng minh một bản
sao của cổng.

Mười lăm kịch bản A–O của §5 đặc tả wave nằm ở đây, mỗi kịch bản một test có
tên nói rõ nó chứng minh điều gì. Ba điều KHÔNG được chứng minh ở đây, và cố ý:
mô hình thật có khai đúng không · token thật · độ trễ thật.
"""
from __future__ import annotations

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

import run_structured_relation_analyze_live as R  # noqa: E402
from run_photo_problem_live import BoKhuBiMat, ChanMangThat  # noqa: E402

KEY_GIA = "AIzaKHOA_GIA_CHO_TEST_KHONG_PHAI_KHOA_THAT"


# ══ HẠ TẦNG ═════════════════════════════════════════════════════════════════
def _mf():
    return R.doc_manifest()


def _gt():
    return R.doc_ground_truth()


def _payload_dung() -> dict:
    """Đầu ra Analyze ĐÚNG — hai quan hệ, có xuất xứ, không giả định."""
    return {
        "input_facts": [
            {"id": "f_ab", "label": "AB", "values": ["3"]},
            {"id": "f_ac", "label": "AC", "values": ["4"]},
            {"id": "f_sa", "label": "SA", "values": ["5"]},
            {"id": "f_right", "label": "tam giác ABC vuông tại A",
             "values": ["tam giác ABC vuông tại A"]},
            {"id": "f_perp", "label": "SA vuông góc (ABC)",
             "values": ["SA ⊥ (ABC)"]},
        ],
        "obligations": [{"kind": "volume", "container": "SABC", "witness": "V"}],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"],
             "other_line": ["A", "C"], "source_fact_id": "f_right"},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"],
             "plane": ["A", "B", "C"], "source_fact_id": "f_perp"},
        ],
    }


def _tra_loi(van_ban: str) -> httpx.Response:
    return httpx.Response(200, json={
        "candidates": [{"content": {"parts": [{"text": van_ban}]}}],
        "usageMetadata": {"promptTokenCount": 111, "candidatesTokenCount": 22,
                          "totalTokenCount": 133},
    })


def _cong(gt: dict, xu_ly, max_http: int = R.MAX_HTTP,
          tran=None) -> R.CongQuetCam:
    cong = R.CongQuetCam(
        httpx.MockTransport(xu_ly), max_http, BoKhuBiMat((KEY_GIA,)),
        dung_sau_loi=True,
        tran_theo_tang=R.TRAN_THEO_TANG if tran is None else tran,
        chuoi_cam=R.chuoi_cam_tu_ground_truth(gt))
    cong.dat_ca(gt["case_id"])
    return cong


def _chay(payload, *, van_ban: str | None = None):
    """Một lượt ĐẦY ĐỦ qua đường sản phẩm, với đầu ra model do test quyết."""
    mf, gt = _mf(), _gt()
    tra = van_ban if van_ban is not None else json.dumps(payload, ensure_ascii=False)
    cong = _cong(gt, lambda _req: _tra_loi(tra))
    with ChanMangThat() as chan:
        hd, err, no = asyncio.run(R.mot_luot(R.de_bai(mf), KEY_GIA, cong))
    assert chan.attempts == [], "lượt chứng minh KHÔNG được chạm mạng thật"
    ss = R.so_sanh_quan_he(hd, gt) if hd is not None else None
    ds = R.chay_downstream(hd, mf, gt) if hd is not None else None
    ket = R.phan_loai(ss, ds, err or no, cong.tong_hop())
    return {"ket": ket, "ss": ss, "ds": ds, "cong": cong, "err": err, "no": no}


# ══ A — ĐẦU RA ĐÚNG ═════════════════════════════════════════════════════════
def test_A_hai_quan_he_dung_thi_PASS_va_dap_so_bang_10():
    r = _chay(_payload_dung())
    assert r["ket"] == "PASS", r["ss"]
    ss, ds = r["ss"], r["ds"]
    assert ss["ACTUAL_GIVEN_RELATION_COUNT"] == 2
    assert ss["CRITICAL_RELATION_ACCURACY"] == 1.0
    assert ss["MISSING_RELATION_COUNT"] == 0
    assert ss["MODEL_ASSUMPTION_COUNT"] == 0
    assert ss["UNVERIFIED_EXTRA_RELATION_COUNT"] == 0
    assert ds["COMPILER_ELIGIBILITY"] == "SUPPORTED"
    assert ds["DERIVED_PERPENDICULAR_COUNT"] == 3
    assert ds["DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH"] is True
    assert ds["EVERY_DERIVED_RELATION_HAS_PARENT_PROOF"] is True
    assert ds["CHAM"]["answer_ok"] is True
    assert ds["CHAM"]["topology_ok"] is True
    assert ds["CHAM"]["visual_gate"] == "COVERED"
    assert r["cong"].tong_hop()["ANALYZE_HTTP_REQUESTS"] == 1


# ══ B, C — THIẾU QUAN HỆ ════════════════════════════════════════════════════
@pytest.mark.parametrize("bo,ten", [(0, "perpendicular_lines"),
                                    (1, "perpendicular_line_plane")])
def test_BC_thieu_mot_quan_he_bat_buoc_thi_ANALYZE_RELATION_INCOMPLETE(bo, ten):
    p = _payload_dung()
    del p["geometric_relations"][bo]
    r = _chay(p)
    assert r["ket"] == "ANALYZE_RELATION_INCOMPLETE"
    assert r["ss"]["MISSING_RELATION_COUNT"] == 1
    assert r["ss"]["MISSING_RELATIONS"][0]["kind"] == ten


# ══ D — XUẤT XỨ TRỎ VÀO HƯ KHÔNG ════════════════════════════════════════════
def test_D_source_fact_id_khong_ton_tai_thi_ANALYZE_RELATION_UNGROUNDED():
    p = _payload_dung()
    p["geometric_relations"][1]["source_fact_id"] = "f_khong_he_co"
    r = _chay(p)
    assert r["ket"] == "ANALYZE_RELATION_UNGROUNDED"
    assert r["ss"]["SOURCE_FACT_RESOLUTION"] == "FAIL"
    assert r["ss"]["SOURCE_FACT_UNRESOLVED"][0]["source_fact_id"] == "f_khong_he_co"
    # Quan hệ VẪN khớp ground truth về mặt hình học — lỗi nằm ở xuất xứ. Trộn
    # hai điều ấy vào một nhãn là mất đúng thứ phân biệt được wave này đo.
    assert r["ss"]["MISSING_RELATION_COUNT"] == 0


# ══ E — GIẢ ĐỊNH CỦA MÔ HÌNH ════════════════════════════════════════════════
def test_E_model_assumption_khong_duoc_tang_dung_dung_lam_du_kien():
    p = _payload_dung()
    p["geometric_relations"][1]["model_assumption"] = True
    r = _chay(p)
    assert r["ket"] != "PASS"
    assert r["ss"]["MODEL_ASSUMPTION_COUNT"] == 1
    usable = [x["usable_by_construction"] for x in r["ss"]["RELATIONS"]
              if x["kind"] == "perpendicular_line_plane"]
    assert usable == [False]
    # Và tầng dựng THẬT SỰ không dùng nó: thiếu quan hệ đường–mặt thì họ bài
    # không còn phân xử được.
    assert r["ds"]["COMPILER_ELIGIBILITY"] != "SUPPORTED"


# ══ F — HỆ QUẢ BỊ GHI THÀNH DỮ KIỆN ĐỀ CHO ══════════════════════════════════
def test_F_quan_he_suy_ra_khai_thanh_GIVEN_thi_EXTRA_DERIVED_RELATION_AS_GIVEN():
    p = _payload_dung()
    # SA ⟂ BC là HỆ QUẢ của SA ⟂ (ABC); đề không phát biểu nó.
    p["geometric_relations"].append(
        {"kind": "perpendicular_lines", "line": ["S", "A"],
         "other_line": ["B", "C"], "source_fact_id": "f_perp"})
    r = _chay(p)
    assert r["ket"] == "EXTRA_DERIVED_RELATION_AS_GIVEN"
    assert r["ss"]["EXTRA_DERIVED_AS_GIVEN_COUNT"] == 1
    assert r["ss"]["EXTRA_DERIVED_AS_GIVEN"][0]["args"] == ["A", "S", "B", "C"]
    # KHÔNG được âm thầm bỏ để output trông hợp lệ.
    assert r["ss"]["MISSING_RELATION_COUNT"] == 0


# ══ G — NHÃN ĐIỂM LẠ ════════════════════════════════════════════════════════
def test_G_nhan_diem_khong_co_trong_hop_dong_thi_bi_tu_choi():
    p = _payload_dung()
    p["geometric_relations"][0]["other_line"] = ["A", "Z"]
    r = _chay(p)
    assert r["ket"] in ("ANALYZE_RELATION_INCOMPLETE", "ANALYZE_RELATION_UNGROUNDED")
    assert r["ss"]["POINT_REFERENCE_VALIDATION"] == "FAIL"
    assert any(e["code"] == "STRUCTURED_RELATION_REFERENCE_UNKNOWN"
               for e in r["ss"]["REJECTED_RELATION_CODES"])
    assert "Z" not in r["ss"]["CONTRACT_POINT_LABELS"]


# ══ H — JSON HỎNG ═══════════════════════════════════════════════════════════
def test_H_json_khong_parse_duoc_thi_MODEL_OUTPUT_INVALID():
    r = _chay(None, van_ban="{ĐÂY KHÔNG PHẢI JSON")
    assert r["ket"] == "MODEL_OUTPUT_INVALID"
    assert r["ss"] is None


# ══ I — PYDANTIC TỪ CHỐI ════════════════════════════════════════════════════
def test_I_pydantic_tu_choi_thi_MODEL_OUTPUT_INVALID():
    r = _chay(None, van_ban=json.dumps({"input_facts": "không phải mảng",
                                        "obligations": 7}))
    assert r["ket"] == "MODEL_OUTPUT_INVALID"


# ══ J — ANALYZE ĐÚNG NHƯNG COMPILER THIẾU ĐIỀU KIỆN ═════════════════════════
def test_J_nghia_vu_ngoai_ho_bai_thi_DOWNSTREAM_COMPILER_UNSUPPORTED():
    p = _payload_dung()
    # Quan hệ vẫn ĐÚNG và vẫn truy được; chỉ nghĩa vụ rơi ngoài họ lát cắt.
    p["obligations"] = [{"kind": "distance", "container": "SABC", "witness": "d"}]
    r = _chay(p)
    assert r["ket"] == "DOWNSTREAM_COMPILER_UNSUPPORTED"
    # Nhãn phải nói đúng TẦNG nào hỏng — Analyze không hỏng.
    assert r["ss"]["MISSING_RELATION_COUNT"] == 0
    assert r["ss"]["SOURCE_FACT_RESOLUTION"] == "PASS"
    assert r["ss"]["CRITICAL_RELATION_ACCURACY"] == 1.0
    assert r["ds"]["COMPILER_ELIGIBILITY"] != "SUPPORTED"


def test_J_bis_do_dai_do_SERVER_neo_tu_cau_de_chu_khong_tu_input_facts():
    """Gỡ mục `input_facts` chở `SA = 5` KHÔNG gỡ được độ dài.

    Đo được khi test J bản đầu chấm ca này thành `PASS` một cách bất ngờ:
    `build_request_contract` trích literal từ `problem_text` rồi neo vào mục dữ
    kiện còn lại có nhắc `SA`. Ghi lại thành test vì đây là một đường phụ thuộc
    THẬT của tầng dựng — nó không đọc câu chữ, nhưng thứ nuôi nó thì có.
    """
    p = _payload_dung()
    p["input_facts"] = [f for f in p["input_facts"] if f["id"] != "f_sa"]
    r = _chay(p)
    assert r["ket"] == "PASS"
    hd = build_request_contract(p, problem_text=R.de_bai(_mf()), domain="hinh_hoc")
    canh = {tuple(b.points): b.expected for b in hd.source_invariants}
    assert canh[("A", "S")] == "5"
    assert "f_sa" not in [f.fact_id for f in hd.input_facts]


# ══ K, L — VISION VÀ SYNTHESIS BỊ CHẶN Ở TRANSPORT ══════════════════════════
@pytest.mark.parametrize("nhan_telemetry,tang", [("transcribe", "vision"),
                                                 ("semantic_program", "synthesis")])
def test_KL_tang_ngoai_analyze_bi_chan_truoc_transport(nhan_telemetry, tang):
    gt = _gt()
    cong = _cong(gt, lambda _r: _tra_loi("{}"))

    async def thu():
        with R.cai_cong_http(cong), R.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=R.MAX_HTTP, max_attempts=1,
                                 max_logical_calls=1)):
            with stage_scope(nhan_telemetry):
                await gemini.call_gemini(KEY_GIA, "hệ thống", "người dùng", None, 0.1)

    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(thu())
    t = cong.tong_hop()
    assert t[f"{tang.upper()}_HTTP_REQUESTS"] == 0
    assert t["HTTP_REQUESTS_SENT"] == 0
    assert t["BLOCKED_BY_STAGE"][tang] == 1
    assert cong.inner_invocations == 0, "không byte nào được gửi xuống transport"


# ══ M, N — LƯỢT LOGIC THỨ HAI VÀ REQUEST THỨ HAI ════════════════════════════
def test_MN_request_thu_hai_bi_chan_truoc_transport():
    gt = _gt()
    cong = _cong(gt, lambda _r: _tra_loi(json.dumps(_payload_dung(),
                                                    ensure_ascii=False)))

    async def thu():
        with R.cai_cong_http(cong), R.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=R.MAX_HTTP, max_attempts=1,
                                 max_logical_calls=1)):
            with stage_scope("semantic_analyze"):
                await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)
            with stage_scope("semantic_analyze"):
                await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

    with pytest.raises(gemini.BudgetExceeded):
        asyncio.run(thu())
    t = cong.tong_hop()
    assert t["ANALYZE_HTTP_REQUESTS"] == 1
    assert t["SENT_WITHIN_BUDGET"] is True
    assert cong.inner_invocations == 1


def test_M_vong_sua_khong_the_chay_vi_tran_luot_logic_bang_1():
    """Repair = một lượt gọi logic nữa. `max_logical_calls=1` giết nó ở `note_call`."""
    b = gemini.ApiBudget(max_api_calls=1, max_attempts=1, max_logical_calls=1)
    b.note_call()
    with pytest.raises(gemini.BudgetExceeded):
        b.note_call()
    assert b.http_requests == 0, "chặn XẢY RA TRƯỚC khi có request nào"


def test_N_retry_bi_tat_vi_max_attempts_bang_1():
    cong = _cong(_gt(), lambda _r: httpx.Response(503, json={"e": "transient"}))

    async def thu():
        with R.cai_cong_http(cong), R.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=R.MAX_HTTP, max_attempts=1,
                                 max_logical_calls=1)):
            with stage_scope("semantic_analyze"):
                await gemini.call_gemini(KEY_GIA, "s", "u", None, 0.1)

    with pytest.raises(RuntimeError):
        asyncio.run(thu())
    t = cong.tong_hop()
    assert t["RETRIES"] == 0 and t["ANALYZE_HTTP_REQUESTS"] == 1


# ══ O — GROUND TRUTH KHÔNG LỌT VÀO REQUEST ══════════════════════════════════
def test_O_ground_truth_va_dap_so_khong_nam_trong_than_request():
    r = _chay(_payload_dung())
    bc = r["cong"].bang_chung_danh_tinh()
    assert bc["GROUND_TRUTH_ABSENT_FROM_REQUEST"] is True
    assert bc["GROUND_TRUTH_NEEDLES_FOUND"] == []


def test_O_cua_so_chung_bo_quet_THAT_SU_bat_duoc_dau_vet_ground_truth():
    """Đo một quãng mà câu trả lời đã biết trước: có needle ⇒ PHẢI báo.

    Không có test này thì `GROUND_TRUTH_ABSENT_FROM_REQUEST = True` chỉ chứng
    minh *bộ quét không chạy*. Đã đo: tắt hẳn vòng quét mà **cả 25 test vẫn
    xanh** — đúng chế độ hỏng `CLAUDE.md §2b·3b` gọi là guard chưa từng đỏ.
    """
    gt = _gt()
    cong = _cong(gt, lambda _r: _tra_loi("{}"))
    needle = R.chuoi_cam_tu_ground_truth(gt)[0]
    assert needle, "danh sách chuỗi cấm không được rỗng"

    async def thu():
        with R.cai_cong_http(cong), R.dung_ngan_sach(
                gemini.ApiBudget(max_api_calls=R.MAX_HTTP, max_attempts=1,
                                 max_logical_calls=1)):
            with stage_scope("semantic_analyze"):
                await gemini.call_gemini(
                    KEY_GIA, "hệ thống", f"đề bài {needle} lẫn vào đây", None, 0.1)

    asyncio.run(thu())
    bc = cong.bang_chung_danh_tinh()
    assert bc["GROUND_TRUTH_ABSENT_FROM_REQUEST"] is False
    assert len(bc["GROUND_TRUTH_NEEDLES_FOUND"]) == 1
    assert bc["GROUND_TRUTH_NEEDLES_FOUND"][0]["needle_sha256"] == R._sha(needle)


def test_O_than_request_chi_cho_DUNG_van_ban_de_da_dong_bang():
    mf = _mf()
    r = _chay(_payload_dung())
    mong = R._sha(f'Đề bài:\n"""\n{R.de_bai(mf)}\n"""')
    assert r["cong"].bang_chung_danh_tinh()["USER_TEXT_SHA256"] == [mong]


# ══ DANH TÍNH REQUEST — launcher KHÔNG được đổi cấu hình mô hình ════════════
def test_request_dung_prompt_va_schema_cua_san_pham():
    r = _chay(_payload_dung())
    bc = r["cong"].bang_chung_danh_tinh()
    assert bc["SYSTEM_PROMPT_SHA256"] == [R._sha(gemini.load_skill("geometry_analyze"))]
    assert bc["TEMPERATURE_OBSERVED"] == [_mf()["temperature"]]


def test_launcher_khong_them_thinking_config_hay_max_output_tokens():
    r = _chay(_payload_dung())
    bc = r["cong"].bang_chung_danh_tinh()
    assert bc["FORBIDDEN_CONFIG_KEYS_PRESENT"] == []
    assert bc["GENERATION_CONFIG_UNEXPECTED_KEYS"] == []


def test_launcher_goi_dung_ham_analyze_cua_san_pham():
    """Đổi `stage_semantic_analyze` thì launcher phải đổi theo — không có bản sao."""
    import inspect

    from app.ai import pipeline
    nguon = inspect.getsource(R.mot_luot)
    assert "pipeline.stage_semantic_analyze" in nguon
    assert "call_gemini" not in nguon, "launcher KHÔNG được dựng request riêng"
    assert callable(pipeline.stage_semantic_analyze)


# ══ HỒ SƠ CA — đóng băng phải khớp chính nó ═════════════════════════════════
def test_input_text_sha256_khop_van_ban_da_dong_bang():
    mf = _mf()
    de = R.de_bai(mf)
    assert de.encode("utf-8").decode("utf-8") == de
    assert "\r" not in de, "đóng băng là LF, không CRLF"
    assert R.bam_van_ban(de) == (
        "fe681f54d9e688866dd51722927e52cfcb4f13350126773b7a7a7fdb08df7960")


def test_manifest_khong_chua_dap_so_va_ground_truth_nam_o_tep_rieng():
    van = R.MANIFEST.read_text(encoding="utf-8")
    for cam in ("expected_answer", "expected_squared_lengths", "volume\": \"10"):
        assert cam not in van, f"manifest KHÔNG được chở ground truth: {cam}"
    gt = _gt()
    assert gt["expected_answer"]["volume"] == "10"
    assert "witness" not in _mf()["structure"]


def test_bang_phan_loai_dong_va_moi_nhan_co_next_action():
    assert set(R.NEXT_THEO_KET_QUA) == set(R.KET_QUA)


def test_tran_tung_tang_la_vision_0_analyze_1_synthesis_0():
    assert R.TRAN_THEO_TANG == {"vision": 0, "analyze": 1, "synthesis": 0}
    assert R.MAX_HTTP == 1
