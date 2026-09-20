# -*- coding: utf-8 -*-
"""Khoá `tests/photo_problem_identity.py` — và chứng minh nó ĐỎ được.

PHOTO_PROBLEM_TO_SCENE_END_TO_END. Các ô danh tính lịch sử dựa vào bằng chứng
này để khai `prompts` là "đổi vì prompt đọc ảnh". Một bằng chứng chưa từng đỏ
thì không đáng để dựa vào, nên có hai phép tiêm.
"""

from __future__ import annotations

from app.runtime_identity import skill_fingerprint
from tests import photo_problem_identity as PI


def test_bam_prompts_lich_su_DUNG_LAI_duoc_chi_bang_transcribe_cu():
    """⚠️ Từ `FACT_GRAPH_CONTRACT_EXTENSION` (2026-09-21) phải hoàn nguyên HAI
    tệp, không còn một: `geometry_analyze.md` cũng đổi. Băm `prompts` gộp mọi
    skill, nên một phép hoàn nguyên thiếu là băm không dựng lại được — và điều
    đó KHÔNG có nghĩa `transcribe.md` sai."""
    from tests.structured_relation_identity import (
        prompts_neu_chua_them_muc_quan_he,
    )

    assert prompts_neu_chua_them_muc_quan_he() == PI.PROMPTS_TRUOC_WAVE


def test_transcribe_THAT_SU_da_doi_va_prompts_THAT_SU_lech():
    vt = skill_fingerprint()
    assert vt["tren_dia"]["transcribe"] != PI.TRANSCRIBE_TAI_085CAE6
    assert vt["tong"] != PI.PROMPTS_TRUOC_WAVE


def test_prompt_doc_anh_TRO_LAI_d8ad614_va_bam_luat_4_9_dung_lai_duoc_chi_bang_transcribe():
    """VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX thêm luật 4/9 vào `transcribe.md` (c50c8c6b → dceff16e); VISION_PROMPT_GUARD_
    SIMPLIFICATION gỡ đúng file ấy về `d8ad614` (dceff16e → c50c8c6b). Cả hai chiều chỉ do MỘT file skill."""
    from tests.structured_relation_identity import (
        prompts_neu_chua_them_muc_quan_he as dung_lai,
    )

    vt = skill_fingerprint()
    assert vt["tren_dia"]["transcribe"] == PI.TRANSCRIBE_TAI_D8AD614
    # `vt["tong"]` nay đã trôi vì `geometry_analyze.md` (wave quan hệ có cấu
    # trúc), nên so THẲNG hết dùng được. Dựng lại rồi mới so — chiều bằng chứng
    # không đổi: hai băm lịch sử ấy vẫn tái tạo được bằng MỘT tệp transcribe.
    assert dung_lai(PI.TRANSCRIBE_TAI_D8AD614) == PI.PROMPTS_TRUOC_PROVENANCE_GUARD
    assert dung_lai(PI.TRANSCRIBE_LUAT_4_9_DA_GO) == PI.PROMPTS_KHI_CO_LUAT_4_9


def _sao_skill(monkeypatch, tmp_path):
    from app.ai import gemini

    gia = tmp_path / "skills"
    gia.mkdir()
    for f in gemini.SKILLS_DIR.glob("*.md"):
        (gia / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(gemini, "SKILLS_DIR", gia)
    return gia


def test_TIEM_sua_them_mot_skill_TANG_B_thi_bang_chung_DO(monkeypatch, tmp_path):
    gia = _sao_skill(monkeypatch, tmp_path)
    (gia / "geometry_program_generator.md").write_text("MỘT CÂU KHÁC — tiêm.", encoding="utf-8")
    assert PI.prompts_neu_transcribe_chua_doi() != PI.PROMPTS_TRUOC_WAVE


def test_TIEM_them_mot_skill_moi_thi_bang_chung_DO(monkeypatch, tmp_path):
    gia = _sao_skill(monkeypatch, tmp_path)
    (gia / "skill_la.md").write_text("nội dung", encoding="utf-8")
    assert PI.prompts_neu_transcribe_chua_doi() != PI.PROMPTS_TRUOC_WAVE
