# -*- coding: utf-8 -*-
"""Toàn vẹn của probe `POINT_INITIALIZATION_REPAIR_EFFICACY`.

**0 lượt gọi model thật** — provider stub. Phải xanh TRƯỚC lượt live: một
probe chưa được chứng minh thì con số nó sinh ra không dùng được, và tiền lệ ở
kho này rất rõ (`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL` — certifier xanh
vì nó gọi tắt, chưa bao giờ chạy đường thật).

Các test ở đây chạy **chính** `probe_point_init_repair.main_async`, tức đi qua
`pipeline.stage_semantic_program` và `_prompt_sua` của **sản phẩm**.
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

import probe_point_init_repair as P  # noqa: E402
from gold_ratio_ab import CORPUS  # noqa: E402

RA_THAT = (GOC.parent / "docs/evaluation/geometry"
           / "point-initialization-repair-efficacy")
CA = {c["case_id"]: c for c in CORPUS}


def _gold_sua(raw: str) -> str:
    """Bản SỬA ĐÚNG: chuyển `at` sang `declare_point`, giữ nguyên phần còn lại."""
    q = json.loads(raw)
    lenh = []
    for m in q["memory_declarations"]:
        if m.get("at") is not None:
            s = {"kind": "declare_point", "target_var": m["name"],
                 "at": m.pop("at")}
            if m.get("model_assumption"):
                s["model_assumption"] = m["model_assumption"]
            if m.get("source_fact_id"):
                s["source_fact_id"] = m["source_fact_id"]
            lenh.append(s)
    q["statements"] = lenh + q["statements"]
    return json.dumps(q, ensure_ascii=False)


class _Stub:
    """Provider giả cho lượt SỬA. Lượt 0 do probe tự trả raw lịch sử."""

    def __init__(self, tra):
        self.goi: list[dict] = []
        self.tra = tra

    async def __call__(self, api_key, system_prompt, user_text, schema=None,
                       temperature=0.2, image=None):
        from app.ai.telemetry import current_stage, record_usage

        self.goi.append({"stage": str(current_stage()),
                         "system": system_prompt, "user": user_text})
        record_usage(str(current_stage()),
                     {"promptTokenCount": 200, "candidatesTokenCount": 40,
                      "thoughtsTokenCount": 10, "totalTokenCount": 250})
        return self.tra


@pytest.fixture
def chay(tmp_path):
    """Chạy probe, và GỠ HẾT bản vá ngay khi `_chay` trả về.

    Cố ý **không** dùng fixture `monkeypatch` sẵn có: `monkeypatch` chỉ hoàn
    nguyên lúc TEARDOWN, tức sau khi thân test đã chạy xong — nên không thể
    viết trong thân test một khẳng định về trạng thái *sau khi* gỡ vá. Với
    context riêng, ranh giới "đã gỡ" nằm gọn trong `_chay`, và `test_A2c` mới
    quan sát được đúng thứ nó cần quan sát.
    """
    def _chay(tra_ve):
        import asyncio

        from app.ai import gemini as G
        from app.ai import pipeline as PL
        from app.ai.telemetry import reset_usage

        reset_usage()
        stub = _Stub(tra_ve)
        with pytest.MonkeyPatch.context() as mp:
            # ⚠️ PHẢI vá CẢ HAI chỗ, và lý do rất cụ thể: probe lưu
            # `goc_call = G.call_gemini` rồi ở `finally` ghi nó ngược vào
            # **cả** `G` **lẫn** `PL`. Nếu chỉ vá `G`, thì `goc_call` chính là
            # stub, và `PL.call_gemini` bị bỏ lại = stub VĨNH VIỄN — bộ gỡ vá
            # không biết về `PL` để hoàn nguyên. Hệ quả đo được: guard offline
            # ở `test_offline_guard` hết raise, im lặng, cho MỌI test chạy sau.
            mp.setattr(G, "call_gemini", stub)
            mp.setattr(PL, "call_gemini", stub)
            mp.setenv("ALLOW_LIVE_AI", "1")
            mp.setenv("GEMINI_API_KEY", "stub-key")
            mp.setattr(P, "RA", tmp_path)
            for ten in ("registration.json", "raw_candidate_nguon.json"):
                (tmp_path / ten).write_text(
                    (RA_THAT / ten).read_text(encoding="utf-8"),
                    encoding="utf-8")

            ma = asyncio.run(P.main_async(object()))
        art = json.loads(next(tmp_path.glob("repair_*.json")).read_text(
            encoding="utf-8"))
        return ma, stub, art, tmp_path, PL
    return _chay


RAW = (RA_THAT / "raw_candidate_nguon.json").read_text(encoding="utf-8")


# ══ A · ĐƯỜNG SỬA LÀ ĐƯỜNG SẢN PHẨM ══════════════════════════════════════
def test_A1_dung_MOT_luot_sua_va_dem_dung(chay):
    ma, stub, art, _, _ = chay(_gold_sua(RAW))
    assert ma == 0
    # Lượt 0 do probe trả raw lịch sử ⇒ stub chỉ thấy ĐÚNG một lượt.
    assert len(stub.goi) == 1
    mf = art["manifest"]
    assert mf["repair_logical_calls"] == 1
    assert mf["application_llm_calls"] == 1
    assert mf["initial_synthesis_calls_this_wave"] == 0
    assert mf["physical_attempts"] == 2          # lượt 0 (giả) + lượt sửa


def test_A2_tran_san_pham_duoc_KHOI_PHUC(chay):
    from app.ai import pipeline as PL
    truoc = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    chay(_gold_sua(RAW))
    assert PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS == truoc


def test_A2b_tien_de_cua_probe_hai_module_TRO_CUNG_MOT_ham():
    """Probe lưu `goc_call = G.call_gemini` rồi khôi phục nó vào **cả hai**
    module. Việc đó chỉ đúng nhờ `pipeline.py` viết
    `from app.ai.gemini import call_gemini` ⇒ hai thuộc tính là **một** đối
    tượng. Đó là tiền đề IM LẶNG của probe: đổi import bên `pipeline.py` sang
    `import gemini as G` + gọi `G.call_gemini(...)` sẽ khiến probe ghi đè
    `PL.call_gemini` bằng thứ nó không hề mượn. Khoá tiền đề ở đây thay vì sửa
    probe, vì `runner_sha256` của probe đã nằm trong artifact live BẤT BIẾN.
    """
    from app.ai import gemini as G
    from app.ai import pipeline as PL
    assert PL.call_gemini is G.call_gemini


def test_A2c_provider_KHONG_RO_RI_sang_pipeline_sau_khi_chay(chay):
    """Sau lượt chạy, `PL.call_gemini` phải trở lại đúng hàm ban đầu.

    Hồi quy có thật, đã đo: bản đầu của fixture chỉ `monkeypatch.setattr(G, …)`,
    nên `goc_call` mà probe khôi phục **chính là stub**, và `PL.call_gemini` ở
    lại = stub sau khi monkeypatch gỡ (monkeypatch không biết về `PL`). Hậu quả
    KHÔNG đỏ ở file này mà đỏ ở file khác chạy sau —
    `test_offline_guard::test_pipeline_quen_mock_cung_bi_chan` hết raise, tức
    chốt chặn mạng offline mất tác dụng trong im lặng.
    """
    from app.ai import gemini as G
    from app.ai import pipeline as PL
    that = G.call_gemini
    _, stub, _, _, _ = chay(_gold_sua(RAW))
    assert PL.call_gemini is not stub and G.call_gemini is not stub
    assert PL.call_gemini is that and G.call_gemini is that


def test_A3_payload_sua_chua_DU_BA_thu(chay):
    """Raw hỏng · chẩn đoán validator · hợp đồng — cả ba phải có mặt."""
    _, stub, art, _, _ = chay(_gold_sua(RAW))
    u = stub.goi[0]["user"]
    assert "memory_declarations" in u and '"at"' in u   # chương trình đã hỏng
    assert "at" in u and "declare_point" in u           # chẩn đoán
    assert CA["r2"]["problem_text"][:40] in u           # đề/hợp đồng
    # SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT: chẩn đoán nay mang JSON Pointer RFC 6901 + mã ổn định.
    assert art["chan_doan_gui_di"] and "/memory_declarations/0/at" in \
        art["chan_doan_gui_di"]


def test_A4_luu_candidate_TRUOC_khi_cham(chay):
    _, _, art, _, _ = chay(_gold_sua(RAW))
    assert art["repair_payload_user"] and art["repair_payload_sha256"]
    assert art["chuong_trinh_sua"] is not None


def test_A5_telemetry_ghi_du(chay):
    _, _, art, _, _ = chay(_gold_sua(RAW))
    assert art["tokens"]["tong"] == 250
    st = art["tokens"]["theo_stage"]["semantic_program"]
    assert st["prompt_tokens"] == 200 and st["thoughts_tokens"] == 10


# ══ B · BỘ CHẤM ĐI ĐÚNG ĐƯỜNG SẢN PHẨM ═══════════════════════════════════
def test_B1_ban_SUA_DUNG_cho_ket_qua_tron_duong(chay):
    _, _, art, _, _ = chay(_gold_sua(RAW))
    c = art["cham"]
    for k in ("SLOT_REPAIRED", "PROVENANCE_PRESERVED", "RATIO_PRESERVED",
              "GROUNDING", "SOURCE_INVARIANTS", "POSTCONDITIONS",
              "EXACT_ANSWER", "TRACE_CONSTRUCTION", "SCENE3D", "SERVABLE"):
        assert c[k] == "PASS", (k, c[k])
    assert c["ANSWER_OBSERVED"] == "6"
    assert c["DERIVED_POINT_PRODUCER"] == "construct_point.divide_segment"
    assert set(c["DERIVED_POINT_DEPENDS"]) >= {"C", "D"}


def test_B2_van_SAI_SLOT_thi_cham_ra_that_bai(chay):
    """Bản sửa vẫn để `at` ở chỗ cũ ⇒ validator bác ⇒ mọi chiều NOT_REACHED."""
    _, _, art, _, _ = chay(RAW)
    assert art["chuong_trinh_sua"] is None
    assert art["cham"]["SLOT_REPAIRED"] == "NOT_REACHED"
    assert art["loi_pipeline"] and "at" in art["loi_pipeline"]


def test_B3_sua_slot_nhung_HONG_RATIO_bi_bat_rieng(chay):
    q = json.loads(_gold_sua(RAW))
    for s in q["statements"]:
        if s.get("target_var") == "N":
            s["expr"]["ratio"] = "1/2"
    _, _, art, _, _ = chay(json.dumps(q, ensure_ascii=False))
    c = art["cham"]
    assert c["SLOT_REPAIRED"] == "PASS"          # slot ĐÚNG
    assert c["RATIO_PRESERVED"] == "FAIL"        # nhưng ratio hỏng
    assert c["SOURCE_INVARIANTS"] == "FAIL" and c["SERVABLE"] == "FAIL"


def test_B4_sua_slot_nhung_MAT_PROVENANCE_bi_bat_rieng(chay):
    q = json.loads(_gold_sua(RAW))
    for s in q["statements"]:
        if s.get("kind") == "declare_point" and s["target_var"] == "C":
            s.pop("model_assumption", None)
            s.pop("source_fact_id", None)
    for m in q["memory_declarations"]:
        if m["name"] == "C":
            m.pop("model_assumption", None)
            m.pop("source_fact_id", None)
    _, _, art, _, _ = chay(json.dumps(q, ensure_ascii=False))
    c = art["cham"]
    assert c["SLOT_REPAIRED"] == "PASS"
    assert c["PROVENANCE_PRESERVED"] == "FAIL"
    assert c["GROUNDING"] == "FAIL"


def test_B5_manifest_ghi_TRUOC_luot_goi(chay):
    _, _, _, td, _ = chay(_gold_sua(RAW))
    mf = json.loads(next(td.glob("manifest_*.json")).read_text(encoding="utf-8"))
    assert "finished_at" not in mf and "repair_logical_calls" not in mf
    for k in ("raw_candidate_sha256", "contract_sha256", "policy_sha256",
              "runner_sha256", "repair_logical_call_limit",
              "token_quan_sat_mot_luot"):
        assert mf.get(k), k
