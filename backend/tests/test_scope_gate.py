# -*- coding: utf-8 -*-
"""M20 W3 — CỔNG PHẠM VI & KHẢ-MÔ-PHỎNG.

Lỗ được bịt: trước wave này KHÔNG cổng tất định nào hỏi "đề này có thuộc môn Tin
học không". Một đề hoá học không đụng gap-role nào, `result_ownership` là
"provided", nên nó đi thẳng qua cổng tính toán — và thứ duy nhất chặn nó là việc
LLM tự từ chối. Tức phán quyết phạm vi do LLM sở hữu, vi phạm R0.

Ba nhóm dưới đây khoá: cổng phán đúng · cổng KHÔNG từ chối oan · cổng nằm đúng
chỗ trong pipeline.
"""

from __future__ import annotations

import asyncio
import json

from app.ai import pipeline
from app.simulation.error_codes import ErrorCode
from app.simulation.scope import DomainScope, Simulatability
from app.simulation.scope_gate import (
    SCOPE_FAILURE_CATEGORY,
    check_scope_and_simulatability,
)

BASE = {
    "objects": ["dãy số"],
    "data": [{"description": "dãy điểm", "values": [7, 9, 6], "labels": None}],
    "relations": [],
    "processes": ["duyệt dãy"],
    "constraints": [],
    "goal": "Tìm phần tử lớn nhất",
    "input_description": "Dãy 3 số",
    "output_description": "Giá trị lớn nhất",
    "notes": None,
    "result_ownership": "provided",
    "domain_scope": "THPT_INFORMATICS",
    "simulatability": "MEANINGFUL_TRACE",
}


def _an(**over) -> dict:
    return {**BASE, **over}


# ── 1. CỔNG PHÁN ĐÚNG ────────────────────────────────────────────────────────

class TestCongPhanDung:
    def test_de_mon_khac_bi_tu_choi(self):
        got = check_scope_and_simulatability(_an(domain_scope="OUT_OF_SCOPE"))
        assert got is not None
        assert got[0] is ErrorCode.GATE_OUT_OF_SCOPE
        assert SCOPE_FAILURE_CATEGORY[got[0]] == "out_of_scope"

    def test_de_chi_giai_thich_duoc_bi_tu_choi_voi_HANG_MUC_RIENG(self):
        """`explanation_only` KHÔNG được gộp vào "ngoài danh mục".

        Chủ đề vẫn thuộc chương trình — nói "ngoài danh mục" làm học sinh tưởng
        hệ không hỗ trợ chủ đề đó. Hai ca cần hai lời khuyên ngược nhau.
        """
        for kind in ("EXPLANATION_ONLY", "NOT_SIMULATION_SUITABLE"):
            got = check_scope_and_simulatability(_an(simulatability=kind))
            assert got is not None, kind
            assert got[0] is ErrorCode.GATE_NOT_SIMULATION_SUITABLE, kind
            assert SCOPE_FAILURE_CATEGORY[got[0]] == "not_simulation_suitable"

    def test_PHAM_VI_phan_TRUOC_kha_mo_phong(self):
        """Đề ngoài môn thì dù mô phỏng đẹp tới đâu cũng không dựng."""
        got = check_scope_and_simulatability(
            _an(domain_scope="OUT_OF_SCOPE", simulatability="INTERACTIVE_MODEL"))
        assert got[0] is ErrorCode.GATE_OUT_OF_SCOPE

    def test_thieu_truong_la_LOI_HOP_DONG_khong_phai_phan_quyet(self):
        for missing in ("domain_scope", "simulatability"):
            an = _an()
            del an[missing]
            got = check_scope_and_simulatability(an)
            assert got is not None, missing
            assert got[0] is ErrorCode.GATE_SCOPE_UNDECLARED, missing

    def test_gia_tri_la_KHONG_duoc_doan_thanh_gia_tri_gan_nhat(self):
        got = check_scope_and_simulatability(_an(domain_scope="MAYBE_INFORMATICS"))
        assert got[0] is ErrorCode.GATE_SCOPE_UNDECLARED


# ── 2. CỔNG KHÔNG TỪ CHỐI OAN ────────────────────────────────────────────────

class TestKhongTuChoiOan:
    def test_de_Tin_hoc_di_tiep(self):
        for kind in ("INTERACTIVE_MODEL", "INTERACTIVE_ARTIFACT", "MEANINGFUL_TRACE"):
            assert check_scope_and_simulatability(_an(simulatability=kind)) is None, kind

    def test_boi_canh_mon_khac_ma_co_che_van_la_Tin_hoc_thi_DI_TIEP(self):
        """"Đếm số cây cao hơn 2m" là `count_if`, không phải sinh học.

        Xếp nó OUT_OF_SCOPE là từ chối oan một bài Tin học thật — đó là lý do
        `ADJACENT_CONTEXT` tồn tại.
        """
        assert check_scope_and_simulatability(_an(domain_scope="ADJACENT_CONTEXT")) is None

    def test_AMBIGUOUS_KHONG_bi_tu_choi_du_cong_ben_canh_fail_closed(self):
        """Bất đối xứng CÓ CHỦ ĐÍCH so với `check_computation_ownership`.

        Không chắc về NGUỒN KẾT QUẢ ⇒ rủi ro là hệ tự giải rồi vẽ đáp án, tức
        nói dối ⇒ từ chối. Không chắc về PHẠM VI ⇒ rủi ro là từ chối oan một bài
        Tin học thật ⇒ đi tiếp. Hai cổng fail về hai hướng vì hai rủi ro ngược
        nhau; sửa test này thành "cũng từ chối" là làm hệ nản học sinh.
        """
        assert check_scope_and_simulatability(_an(domain_scope="AMBIGUOUS")) is None


# ── 3. CỔNG NẰM ĐÚNG CHỖ TRONG PIPELINE ──────────────────────────────────────

def _fake_gemini(responses: list[str]):
    calls: list[dict] = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2):
        calls.append({"system": system_prompt, "user": user_text})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


GENERIC_PICK = {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}


def _run(monkeypatch, analysis: dict, pick=None) -> tuple[dict, list]:
    fake, calls = _fake_gemini([json.dumps(analysis), json.dumps(pick or GENERIC_PICK)])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Đề thử.", "khóa-giả"))
    return env, calls


class TestViTriTrongPipeline:
    def test_de_ngoai_mon_bi_chan_du_classify_CHON_generic(self, monkeypatch):
        """Mock classify chọn generic — trường hợp lạc quan nhất cho việc dựng
        cảnh. Cổng vẫn phải chặn, vì phán quyết là TẤT ĐỊNH chứ không phụ thuộc
        classify. Đây chính là lỗ R0 mà wave này bịt."""
        env, calls = _run(monkeypatch, _an(domain_scope="OUT_OF_SCOPE"))
        assert env["status"] == "unsupported"
        assert env["failure_category"] == "out_of_scope"
        assert env["error_code"] == ErrorCode.GATE_OUT_OF_SCOPE.value
        assert len(calls) == 2, "simulate KHÔNG được chạm sau khi cổng phạm vi chặn"

    def test_de_chi_giai_thich_bi_chan_truoc_khi_dung_canh(self, monkeypatch):
        env, _ = _run(monkeypatch, _an(simulatability="EXPLANATION_ONLY"))
        assert env["failure_category"] == "not_simulation_suitable"

    def test_loi_hop_dong_KHONG_nuot_mat_phan_quyet_nang_luc_THAT(self, monkeypatch):
        """Thiếu trường phạm vi + đề đòi cơ chế engine không có ⇒ học sinh phải
        nghe lời từ chối NĂNG LỰC (có nêu vai trò), không phải "không rõ đề thuộc
        môn gì". Lỗi hợp đồng prompt lùi xuống cuối hàng."""
        an = _an(relation_roles=["numeric_threshold"], entity_roles=["logical"])
        del an["domain_scope"]
        env, _ = _run(monkeypatch, an)
        assert env["failure_category"] == "capability_gap"
        assert "numeric_threshold" in env["reason"]

    def test_khong_cong_nao_co_gi_noi_thi_loi_hop_dong_MOI_len_tieng(self, monkeypatch):
        an = _an()
        del an["domain_scope"]
        env, _ = _run(monkeypatch, an)
        assert env["status"] == "unsupported"
        assert env["error_code"] == ErrorCode.GATE_SCOPE_UNDECLARED.value

    def test_target_CHUYEN_BIET_khong_bi_cong_pham_vi_cham(self, monkeypatch):
        """Cùng lý do với cổng tính toán: target chuyên biệt tồn tại được là vì
        đã có người neo nó vào một đơn vị chương trình. Chặn ở đó là chặn nhầm."""
        an = _an(domain_scope="OUT_OF_SCOPE")
        pick = {"status": "ok", "simulation_id": "algorithm.find_max", "reason": None}
        fake, _ = _fake_gemini([json.dumps(an), json.dumps(pick), json.dumps({
            "problem": {"summary": "Tìm max", "input": "Dãy 3 số", "output": "Max"},
            "data": {"array": [7, 9, 6], "labels": None, "target": None,
                     "condition": None, "order": None},
            "data_generated": False, "notes": None,
        })])
        monkeypatch.setattr(pipeline, "call_gemini", fake)
        env = asyncio.run(pipeline.run_pipeline("Tìm số lớn nhất.", "khóa-giả"))
        assert env["status"] == "ok"


# ── 4. HỢP ĐỒNG PROMPT ↔ ENUM KHÔNG ĐƯỢC TRÔI ────────────────────────────────

class TestHopDongPrompt:
    def test_schema_analyze_ep_dung_bo_gia_tri_cua_enum(self):
        props = pipeline.ANALYZE_SCHEMA["properties"]
        assert props["domain_scope"]["enum"] == [s.value for s in DomainScope]
        assert props["simulatability"]["enum"] == [s.value for s in Simulatability]
        for field in ("domain_scope", "simulatability"):
            assert field in pipeline.ANALYZE_SCHEMA["required"], (
                f"{field} phải nằm trong `required`: cổng fail-closed khi THIẾU "
                "trường, nên structured output phải bảo đảm nó có mặt")

    def test_prompt_analyze_giai_thich_TUNG_gia_tri(self):
        """Enum có mặt trong schema mà prompt không dạy nghĩa thì model đoán bừa,
        và cổng sẽ phán trên một lời khai vô nghĩa."""
        from app.ai.gemini import load_skill

        text = load_skill("analyze")
        for value in [s.value for s in DomainScope] + [s.value for s in Simulatability]:
            assert value in text, f"prompt analyze chưa giải thích {value}"
