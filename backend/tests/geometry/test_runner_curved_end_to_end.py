# -*- coding: utf-8 -*-
"""Toàn vẹn của runner `CURVED_END_TO_END_FRESH_CONFIRMATION`.

**0 lượt gọi model thật** — provider stub. Phải xanh TRƯỚC lượt live.

Chạy **chính** `run_curved_end_to_end.main_async` trên **đúng thư mục artifact
và đúng registration** của wave — nên nó đi qua `pipeline.run_pipeline`,
`stage_semantic_analyze`, `stage_semantic_program` và vòng sửa **của sản phẩm**,
chỉ thay provider. Tiền lệ bắt buộc phải làm vậy:
`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL` — một certifier xanh vì nó gọi
tắt, chưa bao giờ chạy đường thật.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import run_curved_end_to_end as R  # noqa: E402
from gold_curved_end_to_end import (  # noqa: E402
    GOLD, ORACLE, PROBLEM_TEXT, WITNESS,
)

RA_THAT = (GOC.parent / "docs/evaluation/geometry"
           / "curved-end-to-end-fresh-confirmation")
DANG_KY = json.loads((RA_THAT / "registration.json").read_text(encoding="utf-8"))

#: Đầu ra `analyze` giả — đúng hình dạng lược đồ hình học.
ANALYZE_OK = {
    "input_facts": [
        {"id": "hinh_non", "kind": "str", "label": "Hình nón đỉnh S, tâm đáy O",
         "value": ["SO"]},
        {"id": "ban_kinh_day", "kind": "float", "label": "Bán kính đáy",
         "value": ["12"]},
        {"id": "chieu_cao", "kind": "float", "label": "Chiều cao SO",
         "value": ["18"]},
        {"id": "vi_tri_diem", "kind": "str",
         "label": "Vị trí điểm T trên đoạn SO",
         "value": ["T thuộc SO và ST:TO = 1:2"]},
    ],
    "obligations": [
        {"kind": "radius", "container": "(c)", "witness": "ban_kinh_c"},
    ],
}


class _Stub:
    """Provider giả: lượt 1 = analyze, lượt 2+ = synthesis/repair."""

    def __init__(self, chuong_trinh: list[dict | str], analyze=None):
        self.ct = list(chuong_trinh)
        self.analyze = analyze if analyze is not None else ANALYZE_OK
        self.goi: list[dict] = []

    async def __call__(self, api_key, system_prompt, user_text, schema=None,
                       temperature=0.2, image=None):
        from app.ai.telemetry import current_stage, record_usage

        st = str(current_stage())
        self.goi.append({"stage": st, "system": system_prompt,
                         "user": user_text, "temperature": temperature})
        record_usage(st, {"promptTokenCount": 100, "candidatesTokenCount": 20,
                          "thoughtsTokenCount": 5, "totalTokenCount": 125})
        if st == "semantic_analyze":
            return json.dumps(self.analyze)
        n = sum(1 for g in self.goi if g["stage"] == "semantic_program") - 1
        p = self.ct[min(n, len(self.ct) - 1)]
        return p if isinstance(p, str) else json.dumps(p)


@pytest.fixture
def chay_stub(monkeypatch, tmp_path):
    def _chay(chuong_trinh, analyze=None):
        from app.ai import gemini as G
        from app.ai import pipeline as PL
        from app.ai.telemetry import reset_usage

        reset_usage()
        stub = _Stub(chuong_trinh, analyze)
        monkeypatch.setattr(G, "call_gemini", stub)
        monkeypatch.setattr(PL, "call_gemini", stub)
        monkeypatch.setenv("ALLOW_LIVE_AI", "1")
        monkeypatch.setenv("GEMINI_API_KEY", "stub-key")
        # ⚠️ Đăng ký THẬT ghim thẻ Card C — bản đã đo, và nó là bằng chứng
        # đông cứng của lượt chạy ấy. Từ 2026-09-07 thẻ sản phẩm đã đi tiếp
        # (`CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_
        # FOUNDATION` thêm từ vựng elip), nên runner THẬT SỰ từ chối chạy —
        # đúng chức năng của nó, và `test_A4` khoá riêng chiều ấy.
        #
        # Bộ test này đo CƠ CHẾ runner, không đo Card C. Nên bản sao trong
        # tmp_path ghim thẻ HIỆN HÀNH; sửa artifact gốc thì mới là làm giả
        # bằng chứng.
        from app.simulation.semantic_program.grammar_card import grammar_card

        dk = json.loads((RA_THAT / "registration.json").read_text(
            encoding="utf-8"))
        dk["danh_tinh_he_duoc_do"]["card_C_sha256"] = hashlib.sha256(
            grammar_card("hinh_hoc").encode("utf-8")).hexdigest()
        (tmp_path / "registration.json").write_text(
            json.dumps(dk, ensure_ascii=False, indent=2), encoding="utf-8")

        class Args:
            ra = str(tmp_path)

        ma = asyncio.run(R.main_async(Args()))
        art = json.loads(next(tmp_path.glob("e2e_*.json")).read_text(
            encoding="utf-8"))
        return ma, stub, art, tmp_path
    return _chay


def _hong_slot() -> dict:
    """Ứng viên hỏng đúng lớp lỗi `at` — lớp mà vòng sửa ĐÃ chứng minh đóng được."""
    p = copy.deepcopy(GOLD)
    for m in p["memory_declarations"]:
        if m["name"] == "O":
            m["at"] = m.pop("initial_value")
    return p


# ══ A · ĐI ĐÚNG ĐƯỜNG SẢN PHẨM ═══════════════════════════════════════════
def test_A1_de_di_qua_ANALYZE_THAT_roi_moi_toi_synthesis(chay_stub):
    ma, stub, art, _ = chay_stub([GOLD])
    assert ma == 0
    tang = [g["stage"] for g in stub.goi]
    assert tang[0] == "semantic_analyze", tang
    assert tang[1] == "semantic_program", tang
    assert art["manifest"]["entrypoint"].startswith("app.ai.pipeline.run_pipeline")


def test_A2_hop_dong_DONG_BANG_truoc_synthesis(chay_stub):
    """Nghĩa vụ mà synthesis nhìn thấy phải là bản server đã đóng băng."""
    _, stub, art, _ = chay_stub([GOLD])
    us = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert us and "(c)" in us[0] and "radius" in us[0]
    ct = art["request_contract"]
    assert ct, "hợp đồng phải được giữ trong artifact"


def test_A3_synthesis_nhan_THE_SAN_PHAM_hien_hanh(chay_stub):
    from app.simulation.semantic_program.grammar_card import grammar_card

    _, stub, art, _ = chay_stub([GOLD])
    the = grammar_card("hinh_hoc")
    us = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert the in us[0], "thẻ gửi đi KHÔNG phải thẻ sản phẩm"
    # Manifest ghi băm của thẻ THẬT SỰ gửi đi — so với chính thẻ sản phẩm, chứ
    # không so với đăng ký gốc: đăng ký ấy ghim Card C, và thẻ sản phẩm đã đi
    # tiếp (xem chú thích ở fixture).
    assert art["manifest"]["card_C_sha256"] == hashlib.sha256(
        the.encode("utf-8")).hexdigest()
    assert art["manifest"]["card_C_bytes"] == len(the.encode("utf-8"))


def test_A4_runner_TU_CHOI_chay_khi_the_da_troi(monkeypatch, tmp_path):
    """Phép tiêm: sản phẩm rời khỏi Card C ⇒ phép đo không còn nói về Card C."""
    from app.ai import gemini as G
    from app.simulation.semantic_program import grammar_card as GC

    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "stub-key")
    monkeypatch.setattr(GC, "grammar_card", lambda domain=None: "THẺ KHÁC")
    (tmp_path / "registration.json").write_text(
        (RA_THAT / "registration.json").read_text(encoding="utf-8"),
        encoding="utf-8")

    class Args:
        ra = str(tmp_path)

    assert asyncio.run(R.main_async(Args())) == 2
    assert not list(tmp_path.glob("e2e_*.json")), "không được ghi artifact"
    assert G.BUDGET is None


# ══ B · VÒNG SỬA THẬT ════════════════════════════════════════════════════
def test_B1_diagnostic_duoc_chuyen_VAO_vong_sua(chay_stub):
    _, stub, art, _ = chay_stub([_hong_slot(), GOLD])
    us = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert len(us) == 2, "phải có đúng một lượt sửa"
    # Payload sửa mang chẩn đoán validator, và nó trỏ đích danh ô sai.
    assert "at" in us[1]
    assert us[1] != us[0]
    assert art["cham"]["REPAIR_ATTEMPTS"] == 1


def test_B2_vong_sua_DUNG_NGAY_khi_da_served(chay_stub):
    """Gold ngay lượt đầu ⇒ KHÔNG được gọi thêm lượt sửa nào."""
    _, stub, art, _ = chay_stub([GOLD])
    assert sum(1 for g in stub.goi if g["stage"] == "semantic_program") == 1
    assert art["cham"]["REPAIR_ATTEMPTS"] == 0
    assert art["cham"]["FIRST_ATTEMPT_SERVABLE"] is True


def test_B3_tran_sua_cua_SAN_PHAM_khong_bi_runner_doi(chay_stub):
    from app.ai import pipeline as PL

    truoc = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    chay_stub([GOLD])
    assert PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS == truoc == 3


def test_B4_moi_ung_vien_duoc_GIU_truoc_khi_cham(chay_stub):
    _, stub, art, _ = chay_stub([_hong_slot(), GOLD])
    assert len(art["ung_vien_tho"]) == 2
    for e in art["ung_vien_tho"]:
        assert e.get("raw"), "raw candidate phải được giữ"
    assert art["cham"]["CANDIDATE_ATTEMPTS_QUAN_SAT"] == 2


def test_B5_ung_vien_hong_LUOC_DO_van_giu_va_khong_ném(chay_stub):
    ma, _, art, _ = chay_stub(["{ khong phai JSON", GOLD])
    assert ma == 0
    assert len(art["ung_vien_tho"]) >= 1
    assert art["cham"]["EVENTUAL_SERVABLE"] is True


# ══ C · KẾT QUẢ ĐỌC TỪ ĐƯỜNG SẢN PHẨM ════════════════════════════════════
def test_C1_dap_so_doc_tu_FINAL_MEMORY(chay_stub):
    """Đáp số phải đọc từ `final_memory` của outcome — không từ `scene3d`.

    ⚠️ Tiền lệ: runner V3 đọc đáp số từ `scene3d` trong khi `route` cố ý không
    dựng `scene3d`, nên nó chấm 0/9 cho một hệ đang phục vụ được.

    `final_memory` giữ giá trị HỮU TỈ CHÍNH XÁC (`Fraction(4, 1)`), không phải
    chuỗi đã format — đó là chủ đích: bộ đo không được so bằng chữ đã làm tròn.
    """
    _, _, art, _ = chay_stub([GOLD])
    fm = str(art["cham"]["ket_qua"]["FINAL_MEMORY"])
    assert WITNESS in fm
    assert ORACLE["radius_c"] == "4"
    assert f"'{WITNESS}': Fraction(4, 1)" in fm, fm
    # …và KHÔNG phải một số sai nào khác cho cùng witness.
    assert f"'{WITNESS}': Fraction(12" not in fm


def test_C2_Scene3D_di_qua_duong_ghep_canh_cua_san_pham(chay_stub):
    _, _, art, _ = chay_stub([GOLD])
    env = art["envelope"]
    assert env and env.get("status") == "ok"
    sc = env.get("scene3d") or {}
    ids = {str(o.get("id")) for o in (sc.get("objects") or [])}
    assert {"non", "T", "c", WITNESS} <= ids, sorted(ids)


def test_C3_cham_synthesis_doc_dung_SAU_chieu(chay_stub):
    _, _, art, _ = chay_stub([GOLD])
    s = art["cham"]["synthesis"]
    assert s["CURVED_CONSTRUCTION_OPERATOR"] == "construct_curved_solid"
    assert s["CURVED_KIND"] == "cone"
    assert s["CURVED_KHAI_BANG"] == "radius"
    assert s["SECTION_OPERATOR"] == "intersect_plane_curved"
    assert s["SECTION_TARGET_TYPE"] == "circle3"
    assert s["RATIO_WRITTEN"] == "1/3"
    assert s["DIEM_CHIA_DO_LENH_TAO"] is True
    assert s["MEASURE_DUNG_CHU_THE"] is True
    assert s["PROVENANCE_DU"] is True


def test_C5_runner_GIU_raw_cua_tang_analyze(chay_stub):
    """§5 đòi *"lưu analyze output trước synthesis"*.

    Lượt chạy đầu của wave này KHÔNG giữ, nên tầng analyze không chấm được —
    và bộ chấm khi ấy trả `FAIL` cho một tầng nó chưa từng nhìn thấy. Đây là
    cổng chống tái phát.
    """
    _, _, art, _ = chay_stub([GOLD])
    raw = art.get("raw_theo_tang") or {}
    assert "semantic_analyze" in raw, sorted(raw)
    assert json.loads(raw["semantic_analyze"][0])["obligations"]
    assert art["nguon_hop_dong"] == "RAW_ANALYZE"
    assert (art["request_contract"].get("input_facts")), \
        "nội dung fact phải có mặt, không chỉ số đếm"


def test_C6_cham_analyze_noi_NOT_CAPTURED_chu_khong_noi_FAIL():
    """Không quan sát được ≠ sai. Đây là đính chính, khoá bằng test."""
    ct = {"obligations": [{"kind": "radius", "container": "(c)",
                           "witness": "r_c"}]}
    r = R.cham_analyze(ct, nguon="SU_KIEN_DEM", so_fact_quan_sat=8)
    assert r["ANALYZE_CONTRACT_CORRECT"] == R.NOT_CAPTURED
    assert r["CO_BAN_KINH_12"] == R.NOT_CAPTURED
    assert r["SO_FACT"] == 8
    # …nhưng chiều NGHĨA VỤ vẫn chấm được từ nguồn ấy, và nó ĐÚNG.
    assert r["ANALYZE_OBLIGATION_CORRECT"] == "PASS"
    # Không hợp đồng gì cả cũng là NOT_CAPTURED, không phải FAIL.
    assert R.cham_analyze(None)["ANALYZE_CONTRACT_CORRECT"] == R.NOT_CAPTURED


def test_C7_cham_analyze_van_FAIL_duoc_khi_CO_du_lieu_va_du_lieu_SAI():
    """Đính chính không được làm bộ chấm mất răng."""
    xau = {"input_facts": [{"id": "x", "label": "không có số nào"}],
           "obligations": [{"kind": "distance", "container": "S"}]}
    r = R.cham_analyze(xau, nguon="RAW_ANALYZE")
    assert r["ANALYZE_FACTS_CORRECT"] == "FAIL"
    assert r["ANALYZE_OBLIGATION_CORRECT"] == "FAIL"
    assert r["ANALYZE_CONTRACT_CORRECT"] == "FAIL"


def test_C4_cham_analyze_bat_duoc_hop_dong_THIEU(chay_stub):
    """Tiêm: analyze bỏ nghĩa vụ `radius` ⇒ bộ chấm phải nói FAIL, không im."""
    a = copy.deepcopy(ANALYZE_OK)
    a["obligations"] = [{"kind": "distance", "container": "S",
                         "witness": "d"}]
    _, _, art, _ = chay_stub([GOLD], analyze=a)
    assert art["cham"]["analyze"]["ANALYZE_CONTRACT_CORRECT"] == "FAIL"
    assert art["cham"]["analyze"]["CO_NGHIA_VU_RADIUS"] is False


# ══ D · BA BỘ ĐẾM ════════════════════════════════════════════════════════
def test_D1_ba_bo_dem_tach_rieng(chay_stub):
    _, stub, art, _ = chay_stub([_hong_slot(), GOLD])
    bd = art["manifest"]["bo_dem"]
    # Stub thay hẳn `call_gemini` ⇒ hai trường DẪN XUẤT bằng 0. Đó là ĐÚNG:
    # chúng đọc `ApiBudget`, thứ chỉ nhúc nhích khi có request thật.
    assert bd["logical_application_calls"] == 0
    assert bd["physical_api_attempts"] == 0
    # `candidate_attempts` đếm tay ⇒ khớp số lượt provider được gọi.
    assert bd["candidate_attempts"] == len(stub.goi) == 3   # analyze + 2 lượt
    assert bd["phan_ra"]["candidate_attempts_tu_artifact"] == 0


def test_D2_budget_toan_cuc_duoc_TRA_lai(chay_stub):
    from app.ai import gemini as G

    chay_stub([GOLD])
    assert G.BUDGET is None


def test_D3_telemetry_giu_du_NAM_truong_token(chay_stub):
    _, _, art, _ = chay_stub([GOLD])
    ts = art["tokens"]["theo_stage"]
    assert set(ts) >= {"semantic_analyze", "semantic_program"}
    for stage, v in ts.items():
        for truong in ("prompt_tokens", "candidates_tokens",
                       "cached_content_tokens", "total_tokens",
                       "thoughts_tokens"):
            assert truong in v, (stage, truong)
    assert art["tokens"]["tong"] == 125 * 2


# ══ E · MANIFEST GHI TRƯỚC LƯỢT GỌI ĐẦU ══════════════════════════════════
def test_E1_manifest_ghi_TRUOC_va_khop_dang_ky(chay_stub):
    _, _, _, td = chay_stub([GOLD])
    mf = json.loads(next(td.glob("manifest_*.json")).read_text(encoding="utf-8"))
    assert "finished_at" not in mf and "run_status" not in mf
    assert "bo_dem" not in mf
    for k in ("problem_sha256", "oracle_sha256", "gold_sha256",
              "card_C_sha256", "policy_sha256", "runner_sha256",
              "gold_module_sha256", "logical_application_call_limit",
              "token_ceiling_observed", "counter_semantics"):
        assert mf.get(k), k
    h = DANG_KY["hash_bo_do"]
    assert mf["gold_sha256"] == h["gold_sha256"]
    assert mf["gold_module_sha256"] == h["gold_module_sha256"]
    assert mf["problem_sha256"] == DANG_KY["ca"]["problem_sha256"]


def test_E2_tran_logic_lay_TU_DANG_KY_khong_hard_code(chay_stub):
    _, _, art, _ = chay_stub([GOLD])
    assert art["manifest"]["logical_application_call_limit"] == \
        DANG_KY["ngan_sach"]["logical_application_call_limit"] == 5
    assert art["manifest"]["token_ceiling_observed"] == 37_500
    assert art["manifest"]["product_repair_limit"] == 3
