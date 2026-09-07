# -*- coding: utf-8 -*-
"""Toàn vẹn của runner cho `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`.

**0 lượt gọi model thật** — provider stub. Phải xanh TRƯỚC lượt live.

Chạy **chính** `run_curved_end_to_end.main_async` trên **đúng registration** của
wave này, nên nó đi qua `pipeline.run_pipeline` của **sản phẩm** — chỉ thay
provider. Runner nay nạp **gold module và scorer module theo đăng ký**, nên bộ
test này khoá đúng cơ chế ấy: một wave sau chạy đề khác **không** được sửa
module của lượt trước.

⚠️ **ĐỀ CỦA WAVE NÀY KHÔNG QUA ĐƯỢC CỔNG PHẠM VI**, và bộ test này ghi đúng
điều đó thay vì giả vờ ngược lại. `co_duong_thuc_thi` từ chối mọi đề chỉ hỏi
*"tính diện tích …"* vì bảng manh mối thiếu bốn nghĩa vụ đại lượng —
`test_scope_gate_quantity_obligation_gap.py` là nơi lỗ ấy được tái hiện và định
vị. Hệ quả: **0 lượt gọi model**, và phép đo về hành vi mô hình KHÔNG chạy được
cho tới khi lỗ được vá.

Nên các test dưới đây chỉ khoá những gì runner THẬT SỰ làm được ở trạng thái
hiện tại: nạp gold/scorer theo đăng ký · canh thẻ sản phẩm · ghi manifest trước
lượt gọi · trả budget toàn cục · và hai bộ chấm (kiểm bằng ĐƠN VỊ, không cần
pipeline). Khi lỗ được vá, `test_A2` sẽ ĐỎ — đó là dấu hiệu đúng để mở lại phần
đo end-to-end.
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


def test_A2_de_BI_CONG_PHAM_VI_CHAN__khong_luot_goi_nao(chay_stub):
    """⚠️ HÀNH VI THẬT của trạng thái hiện tại, ghi ra thay vì giấu.

    Đề đúng miền hình học, hệ có đủ đường để giải nó (gold preflight 20 pass),
    nhưng `co_duong_thuc_thi` trả `False` vì bảng manh mối thiếu `area`. Nên
    pipeline dừng ở `scope`, **0 lượt gọi model** — và câu hỏi của wave (*mô
    hình có tự tìm ra phép elip không*) chưa trả lời được.

    Test này ĐỎ khi lỗ được vá. Đó là lúc mở lại phần đo end-to-end.
    """
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC, co_duong_thuc_thi,
    )
    from gold_oblique_ellipse_fresh import PROBLEM_TEXT

    ma, stub, art, _ = chay_stub([GOLD])
    assert stub.goi == [], "KHÔNG được gọi model một lượt nào"
    assert (art["envelope"] or {}).get("status") == "unsupported"
    assert art["cham"]["ket_qua"]["STAGE"] == "scope"
    assert art["cham"]["EVENTUAL_SERVABLE"] is False
    assert art["manifest"]["bo_dem"]["logical_application_calls"] == 0
    assert art["manifest"]["bo_dem"]["candidate_attempts"] == 0
    # …và lý do là ĐÚNG cái lỗ đã định vị, không phải một lỗi khác.
    assert co_duong_thuc_thi(PROBLEM_TEXT, DOMAIN_HINH_HOC) is False
    assert ma == 0          # runner chạy trọn, không sập — envelope từ chối


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
