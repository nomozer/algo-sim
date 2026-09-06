# -*- coding: utf-8 -*-
"""Toàn vẹn của runner `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB`.

**0 lượt gọi model thật** — provider stub. Phải xanh TRƯỚC lượt live: một
runner chưa được chứng minh thì con số nó sinh ra không dùng được, và tiền
lệ ở kho này rất rõ (`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`: certifier
xanh vì nó gọi tắt, chưa bao giờ chạy `main_async`).

Các test ở đây chạy **chính** `main_async`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import run_ratio_affordance_ab as R  # noqa: E402
from gold_ratio_ab import CA_DOI_CHUNG, CA_MUC_TIEU, CORPUS  # noqa: E402

from app.ai.pipeline import _dung_scene3d  # noqa: E402
from app.simulation.geometry.radical import display, is_exact_number  # noqa: E402
from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

RA_THAT = GOC.parent / "docs/evaluation/geometry/divide-segment-ratio-ab"


def _ca(cid):
    return next(c for c in CORPUS if c["case_id"] == cid)


# ══ A · CORPUS VÀ ORACLE ═════════════════════════════════════════════════
def test_A1_bon_ca_ba_muc_tieu_mot_doi_chung():
    assert [c["case_id"] for c in CORPUS] == ["r1", "r2", "r3", "r4"]
    assert CA_MUC_TIEU == ("r1", "r2", "r3") and CA_DOI_CHUNG == "r4"


@pytest.mark.parametrize("cid", ["r1", "r2", "r3", "r4"])
def test_A2_gold_di_TRON_duong_san_pham_va_khop_oracle(cid):
    """Gold preflight — nếu ca không tự đi được thì nó không đo được gì."""
    c = _ca(cid)
    rc = RequestContract.model_validate(c["request_contract"])
    sp = SemanticProgramSpec.model_validate(c["gold"])
    oc = verify_and_compile(rc, sp)
    assert oc.stage_reached == "served", oc.details
    dl = {k: display(v) for k, v in (oc.final_memory or {}).items()
          if is_exact_number(v)}
    w = c["witness"]
    assert dl[w] == c["exact_expected_results"][w]
    assert (_dung_scene3d(sp, rc) or {}).get("objects")


def test_A3_r3_BAT_DOI_XUNG_nen_t_phu_thuoc_chieu():
    """Nếu `t` không phụ thuộc chiều thì ca hướng không đo được gì."""
    tt = _ca("r3")["t_theo_thu_tu"]
    assert len(set(tt.values())) == 2, tt
    assert set(tt) == {"E->F", "F->E"}


def test_A4_doi_chung_r4_doi_xung_hai_chieu():
    assert set(_ca("r4")["t_theo_thu_tu"].values()) == {"1/2"}


def test_A5_lich_chay_luan_phien_va_can_bang():
    lich = [R.lich_chay(i) for i in range(len(CORPUS))]
    assert lich == [("A", "B"), ("B", "A"), ("A", "B"), ("B", "A")]
    assert sum(1 for l in lich if l[0] == "A") == sum(1 for l in lich if l[0] == "B")


# ══ B · BỘ CHẤM ══════════════════════════════════════════════════════════
class _Out:
    def __init__(self, stage="served", servable=True, mem=None):
        self.stage_reached, self.servable = stage, servable
        self.executable = stage not in ("semantic_program", "execution")
        self.error_code, self.details = None, []
        self.final_memory = mem or {}


def test_B1_t_cham_theo_CHIEU_THUC_TE_khong_theo_chieu_gia_dinh():
    """`r3` viết `divide_segment(F, E, 4/5)` là ĐÚNG — chiều ngược, t ngược."""
    c = _ca("r3")
    spec = {"memory_declarations": [], "statements": [
        {"kind": "construct_point", "target_var": "P",
         "expr": {"kind": "divide_segment", "a": "F", "b": "E", "ratio": "4/5"}}]}
    k = R.cham(c, spec, _Out(mem={"do_dai_pf": "8"}), True)
    assert k["OPERAND_ORDER"] == "F->E"
    assert k["T_EXPECTED_FOR_ORDER"] == "4/5"
    assert k["T_CORRECT"] == "PASS"
    assert k["POSITION_CORRECT"] == "PASS"


def test_B2_t_dung_so_nhung_SAI_CHIEU_thi_FAIL():
    c = _ca("r3")
    spec = {"memory_declarations": [], "statements": [
        {"kind": "construct_point", "target_var": "P",
         "expr": {"kind": "divide_segment", "a": "F", "b": "E", "ratio": "1/5"}}]}
    assert R.cham(c, spec, _Out(mem={}), False)["T_CORRECT"] == "FAIL"


def test_B3_cach_dung_TUONG_DUONG_van_dung_vi_tri():
    """`midpoint` cho ca đối chứng: `T_CORRECT` = NOT_OBSERVED, vị trí vẫn PASS."""
    c = _ca("r4")
    spec = {"memory_declarations": [], "statements": [
        {"kind": "construct_point", "target_var": "I",
         "expr": {"kind": "midpoint", "a": "G", "b": "H"}}]}
    k = R.cham(c, spec, _Out(mem={"do_dai_ih": "4"}), True)
    assert k["DIVIDE_SEGMENT_USED"] is False
    assert k["PRODUCER_KIND"] == "midpoint"
    assert k["T_CORRECT"] == "NOT_OBSERVED"
    assert k["POSITION_CORRECT"] == "PASS"          # ← không bị trừ điểm


def test_B4_tang_chua_toi_la_NOT_REACHED_khong_phai_FAIL():
    c = _ca("r1")
    spec = {"memory_declarations": [], "statements": []}
    k = R.cham(c, spec, _Out(stage="grounding", servable=False), False)
    assert k["GROUNDING_RESULT"] == "FAIL"
    assert k["COVERAGE_RESULT"] == "NOT_REACHED"
    assert k["POSITION_CORRECT"] == "NOT_REACHED"
    assert k["SCENE3D_RESULT"] == "NOT_REACHED"


def test_B5_dap_so_SAI_thi_vi_tri_FAIL_du_da_served():
    c = _ca("r1")
    spec = {"memory_declarations": [], "statements": [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "divide_segment", "a": "A", "b": "B", "ratio": "3"}}]}
    k = R.cham(c, spec, _Out(mem={"do_dai_mb": "24"}), True)
    assert k["POSITION_CORRECT"] == "FAIL"
    assert k["ANSWER_OBSERVED"] == "24"


# ══ C · CHẠY CHÍNH `main_async` BẰNG PROVIDER STUB ═══════════════════════
class _Stub:
    """Provider giả: đếm lượt, ghi payload, trả gold; báo token giả lập."""

    def __init__(self, cids, hong=()):
        self.goi: list[dict] = []
        self.cids, self.hong = list(cids), set(hong)

    async def __call__(self, api_key, system_prompt, user_text, schema=None,
                       temperature=0.2, image=None):
        from app.ai.telemetry import current_stage, record_usage

        st = str(current_stage())
        self.goi.append({"stage": st, "system": system_prompt, "user": user_text})
        record_usage(st, {"promptTokenCount": 100, "candidatesTokenCount": 20,
                          "thoughtsTokenCount": 5, "totalTokenCount": 125})
        n = sum(1 for g in self.goi if g["stage"] == "semantic_program") - 1
        cid = self.cids[n // 2]
        if cid in self.hong:
            return "{ khong phai JSON"
        return json.dumps(_ca(cid)["gold"])


@pytest.fixture
def chay_stub(monkeypatch, tmp_path):
    def _chay(cids, hong=(), tran_vat_ly=None):
        import asyncio

        from app.ai import gemini as G
        from app.ai import pipeline as PL
        from app.ai.telemetry import reset_usage

        reset_usage()
        stub = _Stub(cids, hong)
        monkeypatch.setattr(G, "call_gemini", stub)
        monkeypatch.setattr(PL, "call_gemini", stub)
        monkeypatch.setenv("ALLOW_LIVE_AI", "1")
        monkeypatch.setenv("GEMINI_API_KEY", "stub-key")
        monkeypatch.setattr(R, "RA", tmp_path)
        if tran_vat_ly is not None:
            monkeypatch.setattr(R, "_tran_vat_ly", lambda: tran_vat_ly)
        for ten in ("card_A.txt", "card_B.txt", "registration.json"):
            (tmp_path / ten).write_text(
                (RA_THAT / ten).read_text(encoding="utf-8"), encoding="utf-8")

        class Args:
            ca = ",".join(cids)

        ma = asyncio.run(R.main_async(Args()))
        art = json.loads(next(tmp_path.glob("ratio_ab_*.json")).read_text(
            encoding="utf-8"))
        return ma, stub, art, tmp_path
    return _chay


def test_C1_ANALYZE_LIVE_BANG_KHONG(chay_stub):
    """Điều kiện trung tâm của thiết kế: hợp đồng cố định, 0 lượt analyze."""
    ma, stub, art, _ = chay_stub(["r1", "r2"])
    assert ma == 0
    assert [g["stage"] for g in stub.goi] == ["semantic_program"] * 4
    assert art["manifest"]["analyze_live_calls"] == 0


def test_C2_ONE_SHOT_moi_arm_dung_MOT_luot(chay_stub):
    _, stub, art, _ = chay_stub(["r1", "r2", "r3", "r4"])
    assert len(stub.goi) == 8                       # 4 ca × 2 arm × 1
    assert art["manifest"]["logical_calls_used_telemetry"] == 8
    assert art["manifest"]["logical_calls_used_telemetry"] <= R.MAX_LOGICAL


def test_C3_tran_san_pham_duoc_KHOI_PHUC_sau_khi_chay(chay_stub):
    from app.ai import pipeline as PL
    truoc = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    chay_stub(["r1"])
    assert PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS == truoc


def test_C4_hai_arm_nhan_CUNG_MOT_RequestContract(chay_stub):
    _, stub, art, _ = chay_stub(["r1"])
    r = art["ket_qua"][0]
    assert r["request_contract"] == _ca("r1")["request_contract"]
    # Thẻ đi trong `user_text`, nên hai payload KHÁC nhau — nhưng phần hợp đồng
    # trong đó phải trùng khít. So bằng chính các chuỗi hợp đồng mang nghĩa.
    us = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert len(us) == 2
    moc = ["do_dai_mb", "M thuộc AB và AM = 9", _ca("r1")["problem_text"]]
    for m in moc:
        assert all(m in u for u in us), m
    # …và hệ thống prompt (phần KHÔNG mang thẻ) phải y hệt.
    ss = {g["system"] for g in stub.goi if g["stage"] == "semantic_program"}
    assert len(ss) == 1


def test_C5_payload_hai_arm_CHI_KHAC_DELTA_DA_DANG_KY(chay_stub):
    _, stub, art, _ = chay_stub(["r1"])
    ss = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert len(set(ss)) == 2
    a, b = sorted(set(ss), key=len)
    assert "ratio:tên" in a and "ratio:tên" not in b
    assert "t = m/(m+n)" in b and "t = m/(m+n)" not in a
    # Khác biệt đúng MỘT dòng, không lan sang phần khác của thẻ.
    da = [x for x in a.splitlines() if x not in b.splitlines()]
    db = [x for x in b.splitlines() if x not in a.splitlines()]
    assert len(da) == len(db) == 1, (da, db)
    assert art["manifest"]["card_delta_bytes"] == len(b.encode()) - len(a.encode())


def test_C6_manifest_ghi_TRUOC_luot_goi_dau_tien(chay_stub, tmp_path):
    _, _, art, td = chay_stub(["r1"])
    mf = json.loads(next(td.glob("manifest_*.json")).read_text(encoding="utf-8"))
    assert "finished_at" not in mf and "run_status" not in mf
    for k in ("corpus_hash", "contract_hash", "oracle_hash", "gold_hash",
              "policy_hash", "runner_hash", "card_A_hash", "card_B_hash",
              "case_order", "logical_budget", "physical_budget",
              "token_ceiling_observed"):
        assert mf.get(k), k


def test_C7_TELEMETRY_token_tach_duoc_theo_tung_arm(chay_stub):
    _, _, art, _ = chay_stub(["r1"])
    arms = art["ket_qua"][0]["arms"]
    for arm in ("A", "B"):
        tk = arms[arm]["tokens"]
        assert tk["total_tokens"] == 125          # đúng MỘT lượt gọi mỗi arm
        assert tk["prompt_tokens"] == 100 and tk["thoughts_tokens"] == 5
    assert art["tokens"]["tong"] == 250


def test_C8_GUARD_NGAN_SACH_chan_va_bao_INCOMPLETE(chay_stub):
    """Trần vật lý thấp ⇒ dừng, báo INCOMPLETE, GIỮ attempt đã gọi."""
    ma, stub, art, _ = chay_stub(["r1", "r2", "r3", "r4"], tran_vat_ly=3)
    assert ma == 3
    mf = art["manifest"]
    assert mf["run_status"] == "INCOMPLETE" and mf["stop_reason"]
    assert mf["cases_planned"] == ["r1", "r2", "r3", "r4"]
    assert len(mf["cases_done"]) < 4
    # Mọi lượt đã gọi vẫn nằm trong artifact — không lượt nào bị giấu.
    assert mf["physical_attempts_used"] == len(stub.goi)
    assert art["tokens"]["tong"] == 125 * len(stub.goi)


def test_C9_ung_vien_hong_LUOC_DO_van_cham_duoc_va_khong_ném(chay_stub):
    _, _, art, _ = chay_stub(["r1"], hong=["r1"])
    for arm in art["ket_qua"][0]["arms"].values():
        assert arm["cham"]["SCHEMA_VALIDATION_RESULT"] == "FAIL"
        assert arm["cham"]["POSITION_CORRECT"] == "NOT_REACHED"


def test_C10_stub_gold_thi_CA_HAI_arm_dung_vi_tri(chay_stub):
    """Chứng minh đường chấm nối thông tới `served` — không chỉ tới schema."""
    _, _, art, _ = chay_stub(["r1", "r3"])
    for r in art["ket_qua"]:
        for arm in r["arms"].values():
            assert arm["servable"] is True
            assert arm["cham"]["POSITION_CORRECT"] == "PASS"
            assert arm["cham"]["T_CORRECT"] == "PASS"
