# -*- coding: utf-8 -*-
"""Toàn vẹn của runner cho `MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`.

**0 lượt gọi model thật** — provider stub. Phải xanh TRƯỚC bốn lượt live.

Chạy **chính** `run_ratio_affordance_ab.main_async` trên **đúng thư mục
artifact và đúng registration** của wave này — không gọi tắt một hàm con.
Tiền lệ bắt buộc phải làm vậy: `V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`,
một certifier xanh vì nó chưa bao giờ chạy đường thật.

Điểm mới so với `test_runner_ratio_ab.py`: nhãn arm `A0`/`C` đọc từ
`registration.arm_labels`, corpus đọc từ `registration.corpus_module`, và ba
bộ đếm theo chuẩn `REPAIR_PROBE_COUNTER_DECOMPOSITION`.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import run_ratio_affordance_ab as R  # noqa: E402
from gold_minimal_card_confirmation import BO, CORPUS, LY_DO_GOC  # noqa: E402

RA_THAT = (GOC.parent / "docs/evaluation/geometry"
           / "minimal-card-fresh-confirmation")
FILE_NEN = ("card_A0.txt", "card_C.txt", "registration.json")
DANG_KY = json.loads((RA_THAT / "registration.json").read_text(encoding="utf-8"))


def _ca(cid):
    return next(c for c in CORPUS if c["case_id"] == cid)


def _gold_dung_dac_ta(cid: str) -> dict:
    """Gold của wave: gốc toạ độ đi kênh `model_assumption`."""
    goc, kia, diem, t, _, _ = BO[cid]
    p = json.loads(json.dumps(_ca(cid)["gold"]))
    for m in p["memory_declarations"]:
        if m["name"] == goc:
            m.pop("source_fact_id", None)
            m["model_assumption"] = LY_DO_GOC
    for s in p["statements"]:
        if s.get("target_var") == diem:
            s["expr"] = {"kind": "divide_segment", "a": goc, "b": kia,
                         "ratio": t}
    return p


class _Stub:
    """Provider giả — ghi lại mọi payload, trả gold đúng đặc tả wave."""

    def __init__(self, cids, hong=()):
        self.cids, self.hong, self.goi = list(cids), set(hong), []

    async def __call__(self, api_key, system_prompt, user_text, schema=None,
                       temperature=0.2, image=None):
        from app.ai.telemetry import current_stage, record_usage

        st = str(current_stage())
        self.goi.append({"stage": st, "system": system_prompt,
                         "user": user_text, "temperature": temperature})
        record_usage(st, {"promptTokenCount": 100, "candidatesTokenCount": 20,
                          "thoughtsTokenCount": 5, "totalTokenCount": 125})
        n = sum(1 for g in self.goi if g["stage"] == "semantic_program") - 1
        cid = self.cids[n // 2]
        if cid in self.hong:
            return "{ khong phai JSON"
        return json.dumps(_gold_dung_dac_ta(cid))


@pytest.fixture
def chay_stub(monkeypatch, tmp_path):
    def _chay(cids, hong=(), tran_vat_ly=None):
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
        for ten in FILE_NEN:
            (tmp_path / ten).write_text(
                (RA_THAT / ten).read_text(encoding="utf-8"), encoding="utf-8")

        class Args:
            ca, ra, corpus = ",".join(cids), None, None

        ma = asyncio.run(R.main_async(Args()))
        art = json.loads(next(tmp_path.glob("ratio_ab_*.json")).read_text(
            encoding="utf-8"))
        return ma, stub, art, tmp_path
    return _chay


# ══ A · NHÃN ARM, CORPUS VÀ LỊCH — ĐỌC TỪ ĐĂNG KÝ ════════════════════════
def test_A1_nhan_arm_A0_C_doc_tu_DANG_KY(chay_stub):
    """`A0`/`C`, KHÔNG phải `A`/`B` — `A` là tên PRODUCT VARIANT đang chạy."""
    ma, _, art, _ = chay_stub(["f1", "f2"])
    assert ma == 0
    mf = art["manifest"]
    assert mf["arm_labels"] == {"A": "A0", "B": "C"}
    assert mf["card_files"] == {"A": "card_A0.txt", "B": "card_C.txt"}


def test_A2_corpus_doc_tu_DANG_KY_va_KHONG_dung_corpus_cu(chay_stub):
    _, _, art, _ = chay_stub(["f1"])
    mf = art["manifest"]
    assert mf["corpus_module"] == "gold_minimal_card_confirmation"
    assert mf["corpus_hash"] == DANG_KY["hash_bo_do"]["corpus_hash"]
    assert mf["contract_hash"] == DANG_KY["hash_bo_do"]["contract_hash"]
    assert mf["oracle_hash"] == DANG_KY["hash_bo_do"]["oracle_hash"]
    assert mf["gold_hash"] == DANG_KY["hash_bo_do"]["gold_hash"]


def test_A3_lich_dung_ban_DA_DANG_KY_khong_phai_lich_chay(chay_stub):
    _, _, art, _ = chay_stub(["f1", "f2"])
    mf = art["manifest"]
    assert mf["case_order"]["f1"] == ["A0", "C"]
    assert mf["case_order"]["f2"] == ["C", "A0"]
    assert [r["thu_tu"] for r in art["ket_qua"]] == [["A0", "C"], ["C", "A0"]]


def test_A4_the_khop_HASH_da_dang_ky(chay_stub):
    _, _, art, _ = chay_stub(["f1"])
    mf = art["manifest"]
    d = DANG_KY["delta_dang_ky"]
    assert mf["card_A_hash"] == d["card_A0_sha256"]
    assert mf["card_B_hash"] == d["card_C_sha256"]
    assert mf["card_A_bytes"] == d["card_A0_bytes"] == 5472
    assert mf["card_B_bytes"] == d["card_C_bytes"] == 5855
    assert mf["card_delta_bytes"] == d["delta_bytes"] == 383


# ══ B · MỘT SYNTHESIS MỖI ARM · KHÔNG ANALYZE · KHÔNG REPAIR ═════════════
def test_B1_moi_arm_DUNG_MOT_synthesis_va_khong_tang_nao_khac(chay_stub):
    ma, stub, art, _ = chay_stub(["f1", "f2"])
    assert ma == 0
    assert [g["stage"] for g in stub.goi] == ["semantic_program"] * 4, (
        "có tầng khác được gọi — analyze hoặc repair đã lọt vào phép đo")
    assert art["manifest"]["analyze_live_calls"] == 0
    assert art["manifest"]["repair_calls_configured"] == 0
    assert art["manifest"]["logical_calls_used_telemetry"] == 4


def test_B2_tran_sua_cua_SAN_PHAM_duoc_khoi_phuc(chay_stub):
    from app.ai import pipeline as PL

    truoc = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    chay_stub(["f1"])
    assert PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS == truoc == 3


def test_B3_budget_toan_cuc_duoc_TRA_lai_sau_khi_chay(chay_stub):
    """`ApiBudget` là trạng thái TOÀN CỤC — rò rỉ nó là làm hỏng mọi test sau."""
    from app.ai import gemini as G

    chay_stub(["f1"])
    assert G.BUDGET is None


# ══ C · HAI ARM NHẬN CÙNG HỢP ĐỒNG, PAYLOAD CHỈ KHÁC THẺ ════════════════
def test_C1_hai_arm_nhan_CUNG_MOT_RequestContract(chay_stub):
    _, stub, art, _ = chay_stub(["f1"])
    assert art["ket_qua"][0]["request_contract"] == _ca("f1")["request_contract"]
    us = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert len(us) == 2
    for moc in ("do_dai_mb", "M thuộc AB và AM:MB = 5:4",
                _ca("f1")["problem_text"]):
        assert all(moc in u for u in us), moc
    assert len({g["system"] for g in stub.goi}) == 1


def test_C2_payload_CHI_KHAC_dung_hai_thay_doi_da_dang_ky(chay_stub):
    _, stub, _, _ = chay_stub(["f1"])
    us = [g["user"] for g in stub.goi if g["stage"] == "semantic_program"]
    assert len(set(us)) == 2
    a, b = sorted(set(us), key=len)          # a = A0, b = C
    da = [x for x in a.splitlines() if x not in b.splitlines()]
    db = [x for x in b.splitlines() if x not in a.splitlines()]
    # 1 dòng bị SỬA (ratio) ⇒ mất ở a, khác ở b; 1 dòng được THÊM (xuất xứ).
    assert len(da) == 1 and len(db) == 2, (da, db)
    assert "ratio:tên" in da[0]
    assert any("t = m/(m+n)" in x for x in db)
    assert any("Xuất xứ:" in x for x in db)


def test_C3_hai_arm_cung_temperature(chay_stub):
    _, stub, _, _ = chay_stub(["f1"])
    assert len({g["temperature"] for g in stub.goi}) == 1


# ══ D · SOURCE INVARIANTS GẮN NHƯ ĐƯỜNG SẢN PHẨM ════════════════════════
def test_D1_source_invariants_duoc_gan_du_HAI_loai(chay_stub, monkeypatch):
    """Không gắn thì cổng bất biến nguồn KHÔNG chạy, và phép đo sẽ báo
    `served` cho đúng lớp chương trình mà sản phẩm đang từ chối."""
    thay: list = []
    goc = R.chay_arm

    async def bat(c, contract, the, api_key):
        thay.append(contract)
        return await goc(c, contract, the, api_key)

    monkeypatch.setattr(R, "chay_arm", bat)
    chay_stub(["f1", "f2"])
    assert len(thay) == 4
    for ct in thay:
        kinds = {b.kind for b in (ct.source_invariants or ())}
        assert kinds == {"segment_length", "segment_division"}, kinds


def test_D2_ratio_SAI_trong_doan_bi_chan_ngay_tren_duong_runner(chay_stub,
                                                                monkeypatch):
    """Tiêm lỗi: nếu cổng bất biến nguồn không chạy, test này XANH SAI."""
    goc_gold = _gold_dung_dac_ta

    def gold_sai(cid):
        p = goc_gold(cid)
        for s in p["statements"]:
            if s.get("target_var") == BO[cid][2]:
                s["expr"]["ratio"] = "1/2"
        return p

    monkeypatch.setitem(sys.modules[__name__].__dict__,
                        "_gold_dung_dac_ta", gold_sai)
    _, _, art, _ = chay_stub(["f1"])
    for arm in art["ket_qua"][0]["arms"].values():
        assert arm["servable"] is False
        assert arm["stage"] == "source_invariant", arm["stage"]


def test_D3_toa_do_TRAI_do_dai_de_cho_bi_chan_TREN_DUONG_RUNNER(chay_stub,
                                                                monkeypatch):
    """Phép tiêm cho cổng VỪA SỬA (`RUNNER_SOURCE_INVARIANT_UNDERBINDING`).

    Trước khi sửa, runner không gắn `bat_bien_do_dai`, nên chương trình dưới
    đây — `B` đặt ở `[99,0,0]` trong khi đề nói `AB = 18` — sẽ đi tới `served`
    và phép đo báo THÀNH CÔNG cho một chương trình sai dữ kiện.
    """
    goc_gold = _gold_dung_dac_ta

    def gold_sai_do_dai(cid):
        p = goc_gold(cid)
        kia = BO[cid][1]
        for m in p["memory_declarations"]:
            if m["name"] == kia:
                # Bỏ `source_fact_id` và khai `model_assumption`: nếu giữ
                # fact id thì GROUNDING bắt trước, và phép tiêm sẽ xanh nhờ
                # một cổng KHÁC — đúng kiểu "đỏ nhờ tầng khác" mà kho này cấm.
                m.pop("source_fact_id", None)
                m["model_assumption"] = LY_DO_GOC
                m["initial_value"] = [99, 0, 0]
        return p

    monkeypatch.setitem(sys.modules[__name__].__dict__,
                        "_gold_dung_dac_ta", gold_sai_do_dai)
    _, _, art, _ = chay_stub(["f1"])
    for nhan_arm, arm in art["ket_qua"][0]["arms"].items():
        assert arm["servable"] is False, (
            f"{nhan_arm}: toạ độ trái độ dài đề cho ĐI LỌT — cổng "
            "`segment_length` không nằm trên đường chạy")
        assert arm["stage"] == "source_invariant", arm["stage"]


# ══ E · ĐƯỜNG CHẤM NỐI THÔNG TỚI `served` ═══════════════════════════════
def test_E1_stub_gold_thi_CA_HAI_arm_di_tron_va_dung(chay_stub):
    _, _, art, _ = chay_stub(["f1", "f2"])
    for r in art["ket_qua"]:
        for arm in r["arms"].values():
            assert arm["servable"] is True
            assert arm["stage"] == "served"
            assert arm["cham"]["POSITION_CORRECT"] == "PASS"
            assert arm["cham"]["T_CORRECT"] == "PASS"


def test_E2_dap_so_doc_tu_final_memory_KE_CA_huu_ti_khong_nguyen(chay_stub):
    _, _, art, _ = chay_stub(["f2"])
    for arm in art["ket_qua"][0]["arms"].values():
        assert arm["cham"].get("ANSWER_OBSERVED") == "28/3", arm["cham"]


def test_E3_ung_vien_duoc_GIU_truoc_khi_cham(chay_stub):
    _, _, art, _ = chay_stub(["f1"], hong=["f1"])
    for arm in art["ket_qua"][0]["arms"].values():
        assert arm.get("raw_candidate"), (
            "raw candidate phải được giữ dù chấm hỏng — không giữ thì không "
            "còn cách nào định vị nguyên nhân từ bằng chứng")
        assert arm["cham"]["SCHEMA_VALIDATION_RESULT"] == "FAIL"
        assert arm["cham"]["POSITION_CORRECT"] == "NOT_REACHED"


def test_E4_Scene3D_di_qua_duong_san_pham(chay_stub):
    _, _, art, _ = chay_stub(["f1"])
    for arm in art["ket_qua"][0]["arms"].values():
        assert arm["cham"].get("SCENE3D_RESULT") == "PASS", arm["cham"]


# ══ F · BA BỘ ĐẾM ════════════════════════════════════════════════════════
def test_F1_ba_bo_dem_dung_chuan_dinh_chinh(chay_stub):
    """Dưới stub, HAI trường dẫn xuất phải bằng 0 — và đó là điều ĐÚNG.

    Stub thay hẳn `call_gemini`, nên `ApiBudget` không được chạm. Nếu hai
    trường ấy khác 0 ở đây thì nghĩa là có ai đó đang đếm SONG SONG thay vì
    dẫn xuất — đúng cái lỗi mà đính chính đi sửa. Bằng chứng cho chiều ngược
    lại (bộ đếm CÓ chạy trên đường thật) nằm ở `test_F3`.
    """
    _, stub, art, _ = chay_stub(["f1", "f2"])
    bd = art["manifest"]["bo_dem"]
    assert bd["logical_application_calls"] == 0
    assert bd["physical_api_attempts"] == 0
    assert bd["candidate_attempts"] == len(stub.goi) == 4
    assert bd["phan_ra"]["candidate_attempts_tu_artifact"] == 0
    assert bd["phan_ra"]["candidate_attempts_tu_api"] == 4


@pytest.mark.anyio
async def test_F3_bo_dem_NAM_TREN_duong_that_khong_chi_tren_stub(monkeypatch):
    """Gọi **chính** `call_gemini` với transport giả — `ApiBudget` phải nhúc nhích.

    Không có test này thì `test_F1` chỉ chứng minh bộ đếm im lặng khi bị bỏ
    qua, chứ không chứng minh nó ĐẾM khi chạy thật. Đó đúng là hình dạng của
    `V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`: một cổng xanh vì nó chưa
    bao giờ nằm trên đường chạy.

    Transport giả thay `gemini.httpx.AsyncClient` — cách mà `conftest.py` nêu
    đích danh là hợp lệ, và nó không đụng guard ở biên mạng thật.
    """
    from app.ai import gemini as G
    from wave_counters import TU_API, BoDemWave

    class _Res:
        status_code = 200

        @staticmethod
        def json():
            return {"candidates": [{"content": {"parts": [{"text": "{}"}]}}],
                    "usageMetadata": {"promptTokenCount": 7,
                                      "totalTokenCount": 9}}

    class _Client:
        def __init__(self):
            self.so_post = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None):
            self.so_post += 1
            return _Res()

    client = _Client()
    monkeypatch.setattr(G.httpx, "AsyncClient", lambda **kw: client)

    ng = G.ApiBudget()
    bo_dem = BoDemWave(ng)
    monkeypatch.setattr(G, "BUDGET", ng)
    try:
        await G.call_gemini("k", "sys", "user")
        bo_dem.ghi_ung_vien(TU_API, ghi_chu="lượt thật")
    finally:
        monkeypatch.setattr(G, "BUDGET", None)

    assert client.so_post == 1, "transport giả phải thật sự được gọi"
    r = bo_dem.bao_cao()
    assert r["logical_application_calls"] == 1, (
        "`call_gemini` không gọi `budget.note_call()` — bộ đếm KHÔNG nằm trên "
        "đường thật")
    assert r["physical_api_attempts"] == 1 == client.so_post, (
        "`physical_api_attempts` phải khớp số POST thật")
    assert r["candidate_attempts"] == 1


def test_F2_ten_cu_van_con_nhung_da_duoc_dan_nhan_lai(chay_stub):
    _, _, art, _ = chay_stub(["f1"])
    mf = art["manifest"]
    assert mf["provider_invocations"] == mf["physical_attempts_used"]
    assert mf["counter_semantics"] == "REPAIR_PROBE_COUNTER_DECOMPOSITION (2026-09-07)"


# ══ G · NGÂN SÁCH DỪNG ĐÚNG CHỖ ═════════════════════════════════════════
def test_G1_ngan_sach_luot_chay_la_4_luot_30000_token(chay_stub):
    _, _, art, _ = chay_stub(["f1", "f2"])
    mf = art["manifest"]
    assert mf["logical_budget"] == 4
    assert mf["token_ceiling_observed"] == 30_000
    assert mf["token_per_call_budget"] == 7_500
    assert mf["run_status"] == "COMPLETE"


def test_G2_guard_chan_va_GIU_moi_luot_da_goi(chay_stub):
    ma, stub, art, _ = chay_stub(["f1", "f2"], tran_vat_ly=3)
    assert ma == 3
    mf = art["manifest"]
    assert mf["run_status"] == "INCOMPLETE" and mf["stop_reason"]
    assert mf["cases_planned"] == ["f1", "f2"]
    assert len(mf["cases_done"]) < 2
    assert mf["provider_invocations"] == len(stub.goi)
    assert art["tokens"]["tong"] == 125 * len(stub.goi), (
        "mọi lượt đã gọi phải nằm trong mẫu số, kể cả lượt bị ngân sách cắt")


def test_G3_manifest_ghi_TRUOC_luot_goi_dau_tien(chay_stub):
    _, _, _, td = chay_stub(["f1"])
    mf = json.loads(next(td.glob("manifest_*.json")).read_text(encoding="utf-8"))
    assert "finished_at" not in mf and "run_status" not in mf
    assert "bo_dem" not in mf
    for k in ("corpus_hash", "contract_hash", "oracle_hash", "gold_hash",
              "policy_hash", "runner_hash", "card_A_hash", "card_B_hash",
              "case_order", "logical_budget", "physical_budget",
              "token_ceiling_observed", "corpus_module", "arm_labels"):
        assert mf.get(k), k
