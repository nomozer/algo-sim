# -*- coding: utf-8 -*-
"""Tính toàn vẹn của runner A/B — **0 lượt gọi model thật** (provider stub).

    `docs/MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT.md`, 2026-09-05.

Chạy **entrypoint thật** với một provider giả, để chứng minh trước khi tiêu
quota: mỗi đề analyze đúng một lần và tổng hợp đúng hai lần, hai arm nhận cùng
`RequestContract`, payload chỉ khác đúng phần đã đăng ký, manifest có trước
lượt gọi, raw candidate được giữ khi tầng sau chặn, và one-shot được thực thi
tại **biên gọi provider** chứ không phải bằng lời hứa.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import run_affordance_ab as R  # noqa: E402
from gold_affordance_ab import CORPUS, gold  # noqa: E402

CA = {c["case_id"]: c for c in CORPUS}


# ══ CORPUS ═══════════════════════════════════════════════════════════════
def test_corpus_dung_hinh_dang_da_dang_ky():
    assert len(CORPUS) == 8
    ho = [c["family"] for c in CORPUS]
    assert ho.count("cylinder") == 3      # 2 dương + 1 ca âm
    assert ho.count("cone") == 2 and ho.count("ball") == 2
    assert ho.count("polyhedron") == 1
    lop = [c["expected_operator_class"] for c in CORPUS]
    assert lop.count("intersect_plane_curved") == 6
    assert lop.count("construct_section") == 1 and lop.count("refusal") == 1


def test_corpus_KHONG_trung_de_cua_dev_v1():
    cu = json.loads((GOC.parent / "docs" / "evaluation" / "geometry" /
                     "curved-section-discoverability-dev-v1" /
                     "corpus.json").read_text(encoding="utf-8"))
    de_cu = {c["problem_text"] for c in cu["cases"]}
    assert not (de_cu & {c["problem_text"] for c in CORPUS})
    # Và ký hiệu cũng phải khác — không tái dùng I·J·P, D·T·U·V…
    assert not ({"(σ)", "(δ)", "(λ)", "(ω)", "(γ)", "(κ)"}
                & {t for c in CORPUS for t in c["problem_text"].split()})


# ══ LỊCH CHẠY — khoá trước, luân phiên thật ══════════════════════════════
def test_lich_chay_LUAN_PHIEN_va_can_bang():
    lich = [R.lich_chay(i) for i in range(len(CORPUS))]
    assert lich[0] == ("A", "B") and lich[1] == ("B", "A")
    assert sum(1 for x in lich if x[0] == "A") == 4
    assert sum(1 for x in lich if x[0] == "B") == 4


# ══ BỘ CHẤM — truy từ KẾT QUẢ về producer ════════════════════════════════
def _spec_gold(cid):
    _, spec, ob = gold(cid)
    obl = [{"kind": k, "container": c, "params": {"witness": w}}
           for k, c, w in ob]
    return spec, obl


@pytest.mark.parametrize("cid,mong", [
    ("e1", ["intersect_plane_curved"]), ("e3", ["intersect_plane_curved"]),
    ("e6", ["intersect_plane_curved"]), ("e7", ["construct_section"])])
def test_cham_truy_dung_producer_cua_ket_qua(cid, mong):
    spec, ob = _spec_gold(cid)
    assert R.toan_tu_cho_ket_qua(spec, ob)["producer_set"] == mong


def test_cham_KHONG_tinh_diem_cho_mot_phep_giao_o_VAT_PHU():
    """Yêu cầu §6: xuất hiện ở đối tượng phụ chỉ là 'có xuất hiện'.

    Chương trình dưới đây dựng một `circle3` bằng `intersect_plane_curved`
    nhưng lấy đáp số từ một phép đo trên KHỐI, không trên đường tròn. Đếm nó
    là chọn đúng phép sẽ cho điểm một chương trình trả lời câu khác.
    """
    spec, ob = _spec_gold("e1")
    spec = json.loads(json.dumps(spec))
    do = [s for s in spec["statements"]
          if (s.get("expr") or {}).get("kind") == "measure"][0]
    do["expr"]["of"] = "Tru"                       # đo trên KHỐI, không trên (u)
    do["expr"]["quantity"] = "volume"
    tt = R.toan_tu_cho_ket_qua(spec, ob)
    assert tt["xuat_hien_bat_ky"] is True          # phép giao VẪN còn đó
    assert tt["producer_set"] == ["construct_curved_solid"]
    assert R.cham(CA["e1"], spec, _Out(), ob, False
                  )["FIRST_ATTEMPT_OPERATOR_CORRECT"] == "FAIL"


class _Out:
    stage_reached, executable, servable = "served", True, True
    error_code, details, final_memory = None, [], {}


def test_cham_phan_biet_NOT_REACHED_voi_FAIL__ca_d1_d5_cua_dev_v1():
    """Ca `d1`/`d5` từng bị đếm là 'chọn sai toán tử' khi thật ra là
    **không quan sát được** — lược đồ hỏng nên không có chương trình nào."""
    c = R.cham(CA["e1"], None, _Out(), [], False)
    assert c["FIRST_ATTEMPT_OPERATOR_CORRECT"] == "NOT_OBSERVED"
    assert c["SCHEMA_VALIDATION_RESULT"] == "FAIL"
    assert c["GROUNDING_RESULT"] == "NOT_REACHED"
    assert c["EXACT_MATCH"] == "NOT_REACHED"


def test_cham_ca_AM_dung_BIEN_khong_dung_chon_toan_tu():
    spec, ob = _spec_gold("e8")

    class O:
        stage_reached, executable, servable = "execution", False, False
        error_code = "semantic_program_invalid"
        details = ["CURVED_SECTION_OUTSIDE_V1_CLOSURE: mặt phẳng xiên"]
        final_memory: dict = {}

    c = R.cham(CA["e8"], spec, O(), ob, False)
    assert c["FIRST_ATTEMPT_OPERATOR_CORRECT"] == "NOT_OBSERVED"
    assert c["BOUNDARY_RESULT"] == "PASS"


# ══ ENTRYPOINT THẬT + PROVIDER STUB ══════════════════════════════════════
class _Stub:
    """Provider giả: đếm lượt, ghi payload, trả chương trình gold."""

    def __init__(self, cids):
        self.goi: list[dict] = []
        self.cids = list(cids)

    async def __call__(self, api_key, system_prompt, user_text, schema=None,
                       temperature=0.2, image=None):
        from app.ai.telemetry import current_stage

        st = str(current_stage())
        self.goi.append({"stage": st, "system": system_prompt,
                         "user": user_text})
        if st == "semantic_analyze":
            cid = self.cids[sum(1 for g in self.goi
                                if g["stage"] == "semantic_analyze") - 1]
            _, _, ob = gold(cid)
            f, _, _ = gold(cid)
            return json.dumps({
                "problem_text": CA[cid]["problem_text"], "input_facts": f,
                "obligations": [{"kind": k, "container": c,
                                 "params": {"witness": w}} for k, c, w in ob]})
        cid = self.cids[(sum(1 for g in self.goi
                             if g["stage"] == "semantic_program") - 1) // 2]
        _, spec, _ = gold(cid)
        return json.dumps(spec)


@pytest.fixture
def chay_stub(monkeypatch, tmp_path):
    def _chay(cids):
        import asyncio

        from app.ai import gemini as G
        from app.ai import pipeline as PL

        stub = _Stub(cids)
        monkeypatch.setattr(G, "call_gemini", stub)
        monkeypatch.setattr(PL, "call_gemini", stub)
        monkeypatch.setenv("ALLOW_LIVE_AI", "1")
        monkeypatch.setenv("GEMINI_API_KEY", "stub-key")
        monkeypatch.setattr(R, "RA", tmp_path)
        for ten in ("card_A.txt", "card_B.txt"):
            (tmp_path / ten).write_text(
                (GOC.parent / "docs" / "evaluation" / "geometry" /
                 "operation-affordance-ab-v1" / ten).read_text(
                    encoding="utf-8"), encoding="utf-8")
        (tmp_path / "registration.json").write_text("{}", encoding="utf-8")

        class Args:
            ca = ",".join(cids)

        ma = asyncio.run(R.main_async(Args()))
        art = json.loads(next(tmp_path.glob("ab_*.json")).read_text(
            encoding="utf-8"))
        return ma, stub, art
    return _chay


def test_E1_moi_de_MOT_analyze_va_HAI_synthesis(chay_stub):
    ma, stub, art = chay_stub(["e1", "e3"])
    assert ma == 0
    assert sum(1 for g in stub.goi if g["stage"] == "semantic_analyze") == 2
    assert sum(1 for g in stub.goi if g["stage"] == "semantic_program") == 4
    assert art["manifest"]["physical_attempts_used"] == 6


def test_E2_hai_arm_nhan_CUNG_MOT_RequestContract(chay_stub):
    _, stub, art = chay_stub(["e1"])
    r = art["ket_qua"][0]
    assert set(r["arms"]) == {"A", "B"}
    # Hợp đồng lưu MỘT bản duy nhất ở mức ca, không nhân đôi theo arm.
    assert "request_contract" in r
    assert all("request_contract" not in a for a in r["arms"].values())


def test_E3_payload_hai_arm_CHI_KHAC_phan_da_dang_ky(chay_stub):
    _, stub, art = chay_stub(["e1"])
    ts = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert len(ts) == 2
    a, b = ts
    AB = (GOC.parent / "docs" / "evaluation" / "geometry" /
          "operation-affordance-ab-v1")
    card_A = (AB / "card_A.txt").read_text(encoding="utf-8")
    card_B = (AB / "card_B.txt").read_text(encoding="utf-8")
    assert a.replace(card_A, "<THẺ>") == b.replace(card_B, "<THẺ>")
    assert a != b
    # Và system prompt thì y hệt.
    ss = {g["system"] for g in stub.goi if g["stage"] == "semantic_program"}
    assert len(ss) == 1


def test_E4_manifest_ghi_TRUOC_luot_goi_dau_tien(chay_stub, tmp_path):
    _, stub, art = chay_stub(["e1"])
    m = json.loads(next(tmp_path.glob("manifest_*.json")).read_text(
        encoding="utf-8"))
    for k in ("run_id", "baseline_candidate_hash", "execution_candidate_hash",
              "card_A_hash", "card_B_hash", "corpus_hash",
              "expected_results_hash", "policy_hash", "runner_hash",
              "scorer_hash", "model_name", "temperature_synthesis",
              "logical_budget", "physical_budget", "case_order", "started_at"):
        assert k in m, k
    assert "finished_at" not in m          # bản ghi TRƯỚC, không phải bản tổng


def test_E5_ONE_SHOT_cuong_che_tai_BIEN_GOI_PROVIDER(chay_stub):
    """Trần một-lượt là số lượt THẬT SỰ rời tiến trình, không phải lời hứa."""
    from app.ai import pipeline as PL

    _, stub, art = chay_stub(["e1", "e3", "e5"])
    assert sum(1 for g in stub.goi if g["stage"] == "semantic_program") == 6
    # Và hằng số SẢN PHẨM được trả lại nguyên vẹn sau lượt chạy.
    assert PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS == 3
    assert art["manifest"]["product_repair_limit_unchanged"] == 3
    assert art["manifest"]["repair_calls_configured"] == 0


def test_E6_ngan_sach_VUOT_thi_NEM():
    ns = R.NganSach()
    for _ in range(R.MAX_PHYSICAL):
        ns.ghi("semantic_program")
    with pytest.raises(RuntimeError, match="VƯỢT TRẦN VẬT LÝ"):
        ns.ghi("semantic_program")


def test_E7_raw_candidate_duoc_GIU_khi_tang_sau_chan(chay_stub, monkeypatch):
    """Grounding hỏng vẫn phải còn raw — nếu không thì chiều chính mất số liệu."""
    from app.simulation.semantic_program import route as RT

    goc = RT.verify_and_compile

    class O:
        stage_reached, executable, servable = "grounding", False, False
        error_code = "input_not_grounded"
        details = ["giả lập chặn ở grounding"]
        final_memory: dict = {}

    monkeypatch.setattr(RT, "verify_and_compile", lambda *a, **k: O())
    monkeypatch.setattr("app.ai.pipeline.verify_and_compile",
                        lambda *a, **k: O(), raising=False)
    _, _, art = chay_stub(["e1"])
    for arm in art["ket_qua"][0]["arms"].values():
        assert arm["raw_candidate"]
        assert arm["cham"]["FIRST_ATTEMPT_OPERATOR_CORRECT"] in ("PASS", "FAIL")
    assert goc is not None


def test_E8_hai_the_trong_artifact_KHOP_BYTE_va_KHAC_NHAU():
    """Cả hai arm đọc từ artifact, nên phép đo KHÔNG phụ thuộc biến thể sản
    phẩm hiện hành.

    ⚠️ Bản trước kết bằng `grammar_card("hinh_hoc") == a`, tức khẳng định
    ngược lại chính docstring của nó: nó buộc phép đo vào biến thể đang chạy.
    Biến thể đổi **A → C** ngày 2026-09-07
    (`MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`) làm nó đỏ, và lộ ra
    điều ấy. Bản này khẳng định đúng thứ docstring nói: hai thẻ trong artifact
    ổn định, và thẻ sản phẩm **không cần** trùng cái nào trong hai.
    """
    from app.simulation.semantic_program.grammar_card import grammar_card

    AB = (GOC.parent / "docs" / "evaluation" / "geometry" /
          "operation-affordance-ab-v1")
    a = (AB / "card_A.txt").read_text(encoding="utf-8")
    b = (AB / "card_B.txt").read_text(encoding="utf-8")
    assert R._h(a).startswith("c7c001c4df7c802a")
    assert R._h(b).startswith("86134034116f9c07")
    assert a != b
    # Phép đo ấy vẫn TÁI LẬP được dù sản phẩm đã rời khỏi cả hai arm.
    assert grammar_card("hinh_hoc") not in (a, b)
