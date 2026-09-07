# -*- coding: utf-8 -*-
"""Toàn vẹn của runner cho `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`.

**0 lượt gọi model thật** — provider stub. Phải xanh TRƯỚC lượt live.

Chạy **chính** `run_curved_end_to_end.main_async` trên **đúng registration** của
wave này, nên nó đi qua `pipeline.run_pipeline` của **sản phẩm** — chỉ thay
provider. Runner nay nạp **gold module và scorer module theo đăng ký**, nên bộ
test này khoá đúng cơ chế ấy: một wave sau chạy đề khác **không** được sửa
module của lượt trước.

✅ **Đề của wave nay ĐI VÀO ĐƯỢC pipeline.** Lượt trước nó chết ở tầng `scope`
vì bảng manh mối thiếu `area`; Pha A của
`SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION` đã vá,
và `test_A2` dưới đây khoá điều đó — nó ĐỎ nếu cổng đóng lại.
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
import score_oblique_ellipse_fresh as S  # noqa: E402
from gold_oblique_ellipse_fresh import GOLD, ORACLE, WITNESS  # noqa: E402

RA_THAT = (GOC.parent / "docs/evaluation/geometry"
           / "oblique-ellipse-fresh-confirmation")
DANG_KY = json.loads((RA_THAT / "registration.json").read_text(encoding="utf-8"))

#: Đầu ra `analyze` giả — đúng hình dạng lược đồ hình học.
ANALYZE_OK = {
    "input_facts": [
        {"id": "tam_day_duoi", "kind": "str", "label": "Tâm đáy dưới O(0,0,0)",
         "value": ["O", "(0,0,0)"]},
        {"id": "tam_day_tren", "kind": "str", "label": "Tâm đáy trên O'(0,0,20)",
         "value": ["O'", "(0,0,20)"]},
        {"id": "ban_kinh_day", "kind": "float", "label": "Bán kính đáy",
         "value": ["4"]},
        {"id": "mat_phang_alpha", "kind": "str",
         "label": "Mặt phẳng (α): 2x - z + 10 = 0", "value": ["2x - z + 10 = 0"]},
        {"id": "thiet_dien", "kind": "str",
         "label": "(α) cắt hình trụ theo elip (E)", "value": ["(E)"]},
    ],
    "obligations": [
        {"kind": "area", "container": "(E)", "witness": "dien_tich_E"},
    ],
}


class _Stub:
    """Provider giả: lượt 1 = analyze, lượt 2+ = synthesis/repair."""

    def __init__(self, chuong_trinh, analyze=None):
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
        from app.simulation.semantic_program.grammar_card import grammar_card

        reset_usage()
        stub = _Stub(chuong_trinh, analyze)
        monkeypatch.setattr(G, "call_gemini", stub)
        monkeypatch.setattr(PL, "call_gemini", stub)
        monkeypatch.setenv("ALLOW_LIVE_AI", "1")
        monkeypatch.setenv("GEMINI_API_KEY", "stub-key")
        # Bản sao trong tmp_path ghim thẻ HIỆN HÀNH; nếu thẻ trôi thì `test_A4`
        # là chỗ bắt, không phải ở đây.
        dk = json.loads((RA_THAT / "registration.json").read_text(
            encoding="utf-8"))
        dk["danh_tinh_he_duoc_do"]["card_C_sha256"] = hashlib.sha256(
            grammar_card("hinh_hoc").encode("utf-8")).hexdigest()
        (tmp_path / "registration.json").write_text(
            json.dumps(dk, ensure_ascii=False, indent=2), encoding="utf-8")

        class Args:
            ra, gold = str(tmp_path), None

        ma = asyncio.run(R.main_async(Args()))
        art = json.loads(next(tmp_path.glob("e2e_*.json")).read_text(
            encoding="utf-8"))
        return ma, stub, art, tmp_path
    return _chay


def _hong_toan_tu() -> dict:
    """Ứng viên hỏng đúng lớp `c5b`/`c9b`: `construct_section` cho khối CONG."""
    p = copy.deepcopy(GOLD)
    for i, s in enumerate(p["statements"]):
        if s.get("target_var") == "E":
            p["statements"][i] = {"kind": "construct_section", "target_var": "E",
                                  "solid": "tru", "plane": "alpha"}
    for m in p["memory_declarations"]:
        if m["name"] == "E":
            m["type"] = "section"
    return p


# ══ A · NẠP ĐÚNG GOLD/SCORER · CANH THẺ · GHI MANIFEST ═══════════════════
def test_A1_gold_va_scorer_nap_TU_DANG_KY(chay_stub):
    """Manifest ghi TRƯỚC khi pipeline chạy, nên đọc được kể cả khi đề bị chặn."""
    _, _, art, _ = chay_stub([GOLD])
    mf = art["manifest"]
    assert mf["gold_module"] == "gold_oblique_ellipse_fresh"
    assert mf["scorer_module"] == "score_oblique_ellipse_fresh"
    h = DANG_KY["hash_bo_do"]
    assert mf["gold_module_sha256"] == h["gold_module_sha256"]
    assert mf["problem_sha256"] == DANG_KY["ca"]["problem_sha256"]
    assert mf["oracle_sha256"] == DANG_KY["ca"]["oracle_sha256"]


def test_A2_de_QUA_duoc_cong_pham_vi_va_toi_duoc_ANALYZE(chay_stub):
    """Chống tái phát cho Pha A, đo trên chính đường sản phẩm.

    Lượt trước đề này chết ở `scope` với 0 lượt gọi. Nay nó phải đi qua
    `analyze` rồi tới `semantic_program` — nếu cổng đóng lại, test này ĐỎ.
    """
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC, co_duong_thuc_thi, nghia_vu_ung_vien,
    )
    from gold_oblique_ellipse_fresh import PROBLEM_TEXT

    assert co_duong_thuc_thi(PROBLEM_TEXT, DOMAIN_HINH_HOC) is True
    assert "area" in nghia_vu_ung_vien(PROBLEM_TEXT)

    ma, stub, art, _ = chay_stub([GOLD])
    assert ma == 0
    tang = [g["stage"] for g in stub.goi]
    assert tang[0] == "semantic_analyze", tang
    assert tang[1] == "semantic_program", tang
    assert art["nguon_hop_dong"] == "RAW_ANALYZE"
    assert art["manifest"]["entrypoint"].startswith("app.ai.pipeline.run_pipeline")


def test_A2b_luot_dau_di_TRON_toi_served_voi_dap_so_dung(chay_stub):
    _, stub, art, _ = chay_stub([GOLD])
    assert art["cham"]["FIRST_ATTEMPT_SERVABLE"] is True
    assert art["cham"]["EVENTUAL_SERVABLE"] is True
    assert art["cham"]["REPAIR_ATTEMPTS"] == 0
    assert (art["envelope"] or {}).get("status") == "ok"
    assert art["cham"]["ket_qua"]["STAGE"] == "served"
    fm = str(art["cham"]["ket_qua"]["FINAL_MEMORY"])
    assert WITNESS in fm
    assert art["cham"]["ket_qua"]["EXACT_ANSWER_EXPECTED"] == "16π√5"


def test_A2c_diagnostic_THAT_duoc_chuyen_vao_vong_sua(chay_stub):
    _, stub, art, _ = chay_stub([_hong_toan_tu(), GOLD])
    us = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert len(us) == 2, "phải có đúng một lượt sửa"
    assert "curved_solid" in us[1] and us[1] != us[0]
    assert art["cham"]["REPAIR_ATTEMPTS"] == 1
    assert art["cham"]["FIRST_ATTEMPT_SERVABLE"] is False
    assert art["cham"]["EVENTUAL_SERVABLE"] is True


def test_A2d_Scene3D_di_qua_duong_ghep_canh_cua_san_pham(chay_stub):
    _, _, art, _ = chay_stub([GOLD])
    sc = (art["envelope"] or {}).get("scene3d") or {}
    vat = {str(o.get("id")): o for o in (sc.get("objects") or [])}
    assert {"tru", "alpha", "E", WITNESS} <= set(vat), sorted(vat)
    assert vat["E"]["render"] == "ellipse"
    assert vat["E"]["producer"] == "intersect_plane_curved_ellipse"


def test_A2e_bo_dem_phan_ra_theo_tang(chay_stub):
    _, stub, art, _ = chay_stub([_hong_toan_tu(), GOLD])
    bd = art["manifest"]["bo_dem"]
    # Stub thay hẳn `call_gemini` ⇒ hai trường DẪN XUẤT bằng 0. Đó là ĐÚNG.
    assert bd["logical_application_calls"] == 0
    assert bd["physical_api_attempts"] == 0
    assert bd["candidate_attempts"] == len(stub.goi) == 3
    assert bd["phan_ra"]["candidate_attempts_theo_tang"] == {
        "semantic_analyze": 1, "semantic_program": 2}


def test_A3_the_SAN_PHAM_duoc_canh_va_ghi_vao_manifest(chay_stub):
    from app.simulation.semantic_program.grammar_card import grammar_card

    _, _, art, _ = chay_stub([GOLD])
    the = grammar_card("hinh_hoc")
    assert art["manifest"]["card_C_sha256"] == hashlib.sha256(
        the.encode("utf-8")).hexdigest()
    # Thẻ PHẢI nói ra phép elip — nếu không, phép đo hỏi một câu vô nghĩa.
    assert "intersect_plane_curved_ellipse" in the
    assert "ellipse3" in next(d for d in the.splitlines()
                              if "type nhận đúng một trong" in d)


def test_A4_runner_TU_CHOI_chay_khi_the_da_troi(monkeypatch, tmp_path):
    from app.ai import gemini as G
    from app.simulation.semantic_program import grammar_card as GC

    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "stub-key")
    monkeypatch.setattr(GC, "grammar_card", lambda domain=None: "THẺ KHÁC")
    (tmp_path / "registration.json").write_text(
        (RA_THAT / "registration.json").read_text(encoding="utf-8"),
        encoding="utf-8")

    class Args:
        ra, gold = str(tmp_path), None

    assert asyncio.run(R.main_async(Args())) == 2
    assert not list(tmp_path.glob("e2e_*.json"))
    assert G.BUDGET is None


# ══ B · HAI BỘ CHẤM — kiểm bằng ĐƠN VỊ, không cần pipeline ═══════════════
def test_B1_cham_synthesis_doc_dung_MUOI_chieu_tren_GOLD():
    s = S.cham_synthesis(GOLD)
    assert s["OPERATOR_CHOSEN"] == "intersect_plane_curved_ellipse"
    assert s["OPERATOR_CORRECT"] == "PASS"
    assert s["RESULT_TYPE_KHAI"] == "ellipse3"
    assert s["RESULT_TYPE_CORRECT"] == "PASS"
    assert s["CYLINDER_KIND"] == "cylinder"
    assert s["CYLINDER_CONSTRUCTION_CORRECT"] == "PASS"
    assert s["PLANE_CONSTRUCTION_CORRECT"] == "PASS"
    assert s["ELLIPSE_PRODUCER_PRESENT"] == "PASS"
    assert s["MEASURE_QUANTITY"] == "area"
    assert s["MEASURE_DUNG_CHU_THE"] is True
    # Ba điểm mặt phẳng thoả `2x − z + 10 = 0`, chấm bằng SỐ HỌC.
    assert set(s["PLANE_POINTS_ON_EQUATION"].values()) == {True}


def test_B2_cham_synthesis_phan_loai_dung_TOAN_TU_SAI():
    s = S.cham_synthesis(_hong_toan_tu())
    assert s["OPERATOR_CORRECT"] == "FAIL"
    assert s["OPERATOR_CHOSEN"] == "construct_section"
    assert s["RESULT_TYPE_CORRECT"] == "FAIL"


def test_B3_cham_analyze_PASS_tren_hop_dong_dung():
    a = S.cham_analyze(dict(ANALYZE_OK), nguon="RAW_ANALYZE")
    assert a["ANALYZE_OBLIGATION_CORRECT"] == "PASS"
    assert a["ANALYZE_FACTS_CORRECT"] == "PASS"
    assert a["ANALYZE_CONTRACT_CORRECT"] == "PASS"


def test_B4_cham_analyze_bat_duoc_hop_dong_SAI():
    ct = {"input_facts": [{"id": "x", "label": "không có số nào"}],
          "obligations": [{"kind": "volume", "container": "tru",
                           "witness": "V"}]}
    a = S.cham_analyze(ct, nguon="RAW_ANALYZE")
    assert a["CO_NGHIA_VU_AREA"] is False
    assert a["ANALYZE_OBLIGATION_CORRECT"] == "FAIL"
    assert a["ANALYZE_FACTS_CORRECT"] == "FAIL"
    assert a["ANALYZE_CONTRACT_CORRECT"] == "FAIL"


def test_B5_cham_KHONG_QUAN_SAT_DUOC_thi_noi_NOT_CAPTURED():
    """Không quan sát được ≠ sai — đính chính đã khoá ở wave trước, giữ tiếp."""
    ct = {"obligations": [{"kind": "area", "container": "(E)",
                           "witness": "dien_tich_E"}]}
    r = S.cham_analyze(ct, nguon="SU_KIEN_DEM", so_fact_quan_sat=5)
    assert r["ANALYZE_CONTRACT_CORRECT"] == S.NOT_CAPTURED
    assert r["CO_PHUONG_TRINH_MP"] == S.NOT_CAPTURED
    assert r["SO_FACT"] == 5
    assert r["ANALYZE_OBLIGATION_CORRECT"] == "PASS"
    assert S.cham_analyze(None)["ANALYZE_CONTRACT_CORRECT"] == S.NOT_CAPTURED


def test_B6_oracle_dung_dang_ma_bo_cham_doc():
    assert ORACLE["area_display"] == "16π√5"
    assert WITNESS == "dien_tich_E"


# ══ C · NGÂN SÁCH VÀ VỆ SINH ═════════════════════════════════════════════
def test_C1_ngan_sach_lay_TU_DANG_KY_khong_hard_code(chay_stub):
    _, _, art, _ = chay_stub([GOLD])
    mf, ns = art["manifest"], DANG_KY["ngan_sach"]
    assert mf["logical_application_call_limit"] == \
        ns["logical_application_call_limit"] == 5
    assert mf["token_ceiling_observed"] == ns["OBSERVED_TOKEN_CEILING"] == 40_000
    assert mf["product_repair_limit"] == 3


def test_C2_budget_toan_cuc_duoc_TRA_lai(chay_stub):
    from app.ai import gemini as G

    chay_stub([GOLD])
    assert G.BUDGET is None


def test_C3_tran_sua_cua_SAN_PHAM_khong_bi_runner_doi(chay_stub):
    from app.ai import pipeline as PL

    truoc = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    chay_stub([GOLD])
    assert PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS == truoc == 3


def test_C4_manifest_ghi_TRUOC_luot_goi_dau(chay_stub):
    _, _, _, td = chay_stub([GOLD])
    mf = json.loads(next(td.glob("manifest_*.json")).read_text(encoding="utf-8"))
    assert "finished_at" not in mf and "run_status" not in mf
    assert "bo_dem" not in mf
    for k in ("problem_sha256", "oracle_sha256", "gold_sha256", "card_C_sha256",
              "policy_sha256", "runner_sha256", "gold_module",
              "scorer_module", "logical_application_call_limit"):
        assert mf.get(k), k
