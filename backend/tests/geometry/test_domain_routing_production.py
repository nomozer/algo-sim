# -*- coding: utf-8 -*-
"""MIỀN HÌNH HỌC PHẢI ĐƯỢC NỐI VÀO ĐƯỜNG SẢN PHẨM. **0 API call.**

─── SỰ CỐ ─────────────────────────────────────────────────────────────────

Học sinh dán đề *"hình chóp S.ABCD … dựng thiết diện (PMN), xác định giao tuyến
d"* vào sản phẩm và nhận **"NGOÀI DANH MỤC MÔ PHỎNG"**, sau khoảng bảy lượt LLM.

Không mảnh nào hỏng. `SEMANTIC_ROUTE_MODE=serve` đã bật, `geometry_analyze.md`
và `geometry_program_generator.md` đều có, `detect_domain` đã viết, kernel hình
học đã chạy, Scene3D đã dựng. Chỉ là **không ai gọi chúng**:

    _semantic_route_attempt  →  stage_semantic_analyze(text, api_key)   ← thiếu domain
    stage_semantic_program   →  load_skill("semantic_program")          ← viết cứng
    program_skill_for / detect_domain                                   ← 0 người gọi

Nên đề hình học được **đọc và viết bằng prompt Tin học**, dựng không nổi IR, rồi
rơi xuống classifier — nơi không có target hình học nào.

Đây là bất biến #22 lần thứ ba: mảnh nào cũng xanh mà chưa mảnh nào được ghép.
Test này khoá **ĐƯỜNG DÂY**, không khoá chất lượng sinh.
"""
from __future__ import annotations

import ast
import asyncio
import inspect
from pathlib import Path

import pytest

from app.ai import pipeline
from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_TIN_HOC,
)

DE_HINH_HOC = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với "
    "mặt phẳng đáy và SA=5. Gọi M, N lần lượt là trung điểm của SB, SD; P là "
    "trung điểm của AB. Hãy dựng mặt phẳng (PMN), xác định giao tuyến d của "
    "hai mặt phẳng (PMN) và (ABCD)."
)
DE_TIN_HOC = (
    "Kiểm tra tính hợp lệ của chuỗi đóng mở ngoặc bằng ngăn xếp Stack với "
    "chuỗi {[()]}."
)


# ══ ĐƯỜNG DÂY: MIỀN ĐI XUỐNG CẢ HAI LƯỢT LLM ═════════════════════════════
def test_de_hinh_hoc_dung_CA_HAI_skill_hinh_hoc(monkeypatch):
    """Đổi một lượt mà quên lượt kia là đúng lỗi Phase 5 đo được: skill viết
    chương trình đã sang hình học, skill đọc đề thì không, nên mô hình khai
    nghĩa vụ Tin học cho bài hình học ở 3/6 ca hợp lệ."""
    da_goi: dict = {}

    async def gia_analyze(text, api_key, domain=None):
        da_goi["analyze_domain"] = domain
        return None, "dừng ở đây — chỉ đo đường dây"

    monkeypatch.setattr(pipeline, "stage_semantic_analyze", gia_analyze)
    asyncio.run(pipeline._semantic_route_attempt(
        DE_HINH_HOC, {}, "k", None, DOMAIN_HINH_HOC))
    assert da_goi["analyze_domain"] == DOMAIN_HINH_HOC


def test_stage_semantic_program_KHONG_con_viet_cung_ten_skill():
    """`geometry_program_generator.md` từng không có MỘT người gọi nào trong
    `app/` — chỉ harness đo với tới nó bằng cách bọc `load_skill` từ ngoài."""
    src = inspect.getsource(pipeline.stage_semantic_program)
    assert 'load_skill("semantic_program")' not in src
    assert "program_skill_for" in src


def test_program_skill_for_co_NGUOI_GOI_trong_app():
    """Hàm có mà không ai gọi thì không phải tính năng, chỉ là mã chết trông
    như tính năng — và nó đã trông như tính năng suốt bốn wave."""
    goc = Path(pipeline.__file__).resolve().parents[1]
    goi = 0
    for f in goc.rglob("*.py"):
        cay = ast.parse(f.read_text(encoding="utf-8"))
        goi += sum(1 for n in ast.walk(cay)
                   if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Name)
                   and n.func.id in ("program_skill_for", "detect_domain"))
    assert goi >= 2, "cả program_skill_for lẫn detect_domain phải có người gọi"


def test_domain_MAC_DINH_None_giu_nguyen_hanh_vi_Tin_hoc():
    """Đường Tin học không được đổi một bit: 24 module đang chạy trên nó."""
    ts = inspect.signature(pipeline.stage_semantic_program).parameters
    assert ts["domain"].default is None
    ta = inspect.signature(pipeline.stage_semantic_analyze).parameters
    assert ta["domain"].default is None


# ══ CỔNG PHẠM VI: NGOẠI LỆ HẸP ĐÚNG BẰNG CHỖ CẦN ═════════════════════════
def _analysis(scope: str, kind: str = "MEANINGFUL_TRACE") -> dict:
    return {"domain_scope": scope, "simulatability": kind,
            "result_ownership": "rule_derivable"}


# ─── VIẾT LẠI SAU LEGACY_INFORMATICS_REMOVAL (2026-09-02) ──────────────────
#
# Bốn test dưới đây từng gọi `pipeline._semantic_shadow(text, analysis, …)` —
# tức đi qua ba cổng Tin học với một `analysis` tiêm tay. Cả `_semantic_shadow`
# lẫn `analysis` ấy **không còn tồn tại**: đường hình học nay là đường CHÍNH,
# rẽ ngay đầu `run_pipeline`, và không đề nào tới sản phẩm còn sinh ra một bản
# phân tích Tin học.
#
# Ý ĐỊNH của cả bốn thì không đổi một chữ, và nay diễn đạt được ở đúng nơi
# người dùng chạm vào — `run_pipeline` — thay vì ở một hàm nội bộ. Đó là SIẾT:
# test cũ có thể xanh trong khi đường thật hỏng, test mới thì không.
def _chan_route(monkeypatch) -> list:
    """Chặn `_semantic_route_attempt` để đếm xem route CÓ được thử không."""
    goi: list = []

    async def _di_tiep(*a, **k):
        goi.append({"domain": a[4] if len(a) > 4 else k.get("domain")})
        return None

    monkeypatch.setattr(pipeline, "_semantic_route_attempt", _di_tiep)
    return goi


def test_de_hinh_hoc_di_thang_vao_duong_HINH_HOC(monkeypatch):
    """Đề hình học phải tới route sinh, mang đúng miền, không cổng nào chặn.

    Trước cutover, câu này phải nói *"`domain_scope = OUT_OF_SCOPE` không được
    giết đề hình học"* — vì đề phải đi qua một cổng đọc nhãn ấy. Nay không có
    cổng ấy trên đường hình học nữa, nên câu đúng là câu đơn giản này.
    """
    goi = _chan_route(monkeypatch)
    asyncio.run(pipeline.run_pipeline(DE_HINH_HOC, "k"))
    assert goi and goi[0]["domain"] == DOMAIN_HINH_HOC


def test_de_MON_KHAC_bi_chan_va_KHONG_ton_mot_luot_nao(monkeypatch):
    """Đề hoá học ⇒ `tin_hoc` ⇒ fail-closed, và chặn TRƯỚC mọi lượt LLM."""
    goi = _chan_route(monkeypatch)
    kq = asyncio.run(pipeline.run_pipeline(
        "Cân bằng phương trình phản ứng NaOH + HCl và mô phỏng quá trình.", "k"))
    assert kq["status"] == "unsupported"
    assert kq["failure_category"] == "out_of_scope"
    assert not goi, "đề ngoài miền không được chạm route sinh"


def test_de_hinh_hoc_KHONG_co_duong_thuc_thi_van_bi_chan(monkeypatch):
    """Hình học về từ vựng ≠ hệ dựng và kiểm chứng được.

    Nửa quan trọng của luật cũ được giữ nguyên: server KHÔNG blanket-accept mọi
    thứ nghe như hình học. Khác biệt là thẩm quyền — trước hỏi enum
    `simulatability` của `analyze.md` (đo được ở canary V2 2026-08-29: bài A10
    trong năng lực bị chính vế ấy giết, còn A09 cùng dạng thì không — phán
    quyết ngẫu nhiên đúng nghĩa đen), nay hỏi `co_duong_thuc_thi` của chính
    miền hình học.
    """
    from app.simulation.semantic_program.domain_profile import co_duong_thuc_thi

    de = ("Cho hình lập phương ABCD.A'B'C'D'. Hãy vẽ hình chiếu của nó lên "
          "một mặt phẳng theo phương chiếu AC'.")
    assert not co_duong_thuc_thi(de, DOMAIN_HINH_HOC), "đề này phải KHÔNG có đường"
    goi = _chan_route(monkeypatch)
    kq = asyncio.run(pipeline.run_pipeline(de, "k"))
    assert kq["failure_category"] == "not_simulation_suitable"
    assert not goi, "bị chặn thì không được tiêu một lượt nào"


def test_de_TRONG_nang_luc_KHONG_bi_chan(monkeypatch):
    """Nửa còn lại: đề trong năng lực phải đi tiếp.

    Đây là ca đã hỏng thật trên live — A10, góc đường–mặt, có checker.
    """
    goi = _chan_route(monkeypatch)
    de = ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính góc giữa đường "
          "thẳng AC' và mặt phẳng (ABCD).")
    asyncio.run(pipeline.run_pipeline(de, "k"))
    assert goi, "đề trong năng lực vẫn bị một cổng phủ quyết"


# ══ BỘ DÒ MIỀN TRÊN ĐÚNG ĐỀ ĐÃ HỎNG ══════════════════════════════════════
def test_de_that_cua_hoc_sinh_duoc_do_dung_mien():
    from app.simulation.semantic_program.domain_profile import detect_domain

    assert detect_domain(DE_HINH_HOC) == DOMAIN_HINH_HOC
    assert detect_domain(DE_TIN_HOC) == DOMAIN_TIN_HOC


# ══ ĐỀ TIN HỌC MƯỢN TỪ VỰNG HÌNH HỌC ═════════════════════════════════════
#
# ĐO ĐƯỢC 2026-08-26: bốn trên năm đề Tin học HỢP LỆ bị kéo sang hình học chỉ vì
# đủ ba cụm yếu. Chúng không phải đề bịa cho vui — hình học tính toán, đồ hoạ và
# bài toán lưới đều nằm trong chương trình, và đều nói "tam giác", "hình chữ
# nhật", "song song", "thể tích" một cách hoàn toàn tự nhiên.
#
# Docstring cũ của `detect_domain` ĐÃ khai giới hạn này và chấp nhận nó, với lý
# do "thất bại lộ ra ở C₁a chứ không âm thầm". Phép đo cho thấy lý do ấy sai ở
# hai chỗ: nó KHÔNG hiếm, và "lộ ra" với học sinh nghĩa là tấm thẻ **NGOÀI DANH
# MỤC MÔ PHỎNG** giáng xuống một đề mà hệ vốn mô phỏng được — tức route hình học
# ăn mất chính 24 target đang chạy tốt.
#
# CHIỀU NÀY MỚI NGUY: `hinh_hoc` đoán nhầm thành `tin_hoc` chỉ rơi về hành vi cũ
# (fail-safe, có chủ đích). Ngược lại thì mở nhầm cửa. Nên test dưới không khoan
# nhượng đúng một chiều.

#: Đề Tin học THẬT, mỗi đề ≥3 cụm yếu hình học. Giữ nguyên văn: sửa cho "sạch
#: từ hình học" là làm hỏng chính thứ đang kiểm.
DE_TIN_HOC_MUON_TU_HINH_HOC = (
    "Cho toạ độ ba đỉnh một tam giác. Viết chương trình kiểm tra tam giác đó "
    "có vuông góc ở đỉnh A không, và tính trung điểm cạnh BC.",
    "Cho danh sách hình chữ nhật trên mặt phẳng toạ độ. Sắp xếp theo diện tích "
    "rồi kiểm tra hai hình bất kỳ có song song cạnh nhau không.",
    "Nhập chiều dài đáy và chiều cao, viết chương trình tính thể tích khối hộp "
    "và khoảng cách từ tâm tới một mặt.",
    "Cho mảng các đoạn thẳng. Dùng ngăn xếp kiểm tra xem có hai đường thẳng "
    "nào song song hoặc vuông góc không.",
    "Cho lưới ô vuông 8x8. Robot chỉ đi song song với hai trục. Tính khoảng "
    "cách từ ô xuất phát tới ô đích bằng thuật toán BFS.",
)


def test_de_TIN_HOC_muon_tu_hinh_hoc_KHONG_bi_keo_sang():
    from app.simulation.semantic_program.domain_profile import detect_domain

    nham = [d for d in DE_TIN_HOC_MUON_TU_HINH_HOC
            if detect_domain(d) != DOMAIN_TIN_HOC]
    assert not nham, (
        "Đề Tin học bị kéo sang hình học — route hình học sẽ ăn mất một đề mà "
        f"hệ vốn mô phỏng được:\n" + "\n".join(f"  - {d[:80]}…" for d in nham)
    )


def test_de_hinh_hoc_KHONG_co_cum_manh_van_qua_duoc():
    """Bản vá KHÔNG được siết tới mức giết `geo_08`.

    `geo_08` là hình vuông PHẲNG: **0 cụm mạnh**, chỉ đủ cụm yếu. Nó là lý do
    ngưỡng bằng 3 chứ không phải 5. Một bản vá làm nó trượt là đã đổi một lỗ
    lấy một lỗ khác.
    """
    from app.simulation.semantic_program.domain_profile import (
        _DAU_HIEU_MANH,
        detect_domain,
    )

    geo_08 = ("Cho hình vuông ABCD cạnh 1 nằm trong mặt phẳng. Tính góc giữa "
              "đường thẳng AB và đường chéo AC.")
    assert not any(c in geo_08.lower() for c in _DAU_HIEU_MANH)  # thật sự 0 cụm mạnh
    assert detect_domain(geo_08) == DOMAIN_HINH_HOC


def test_cum_MANH_van_thang_du_de_noi_giong_lap_trinh():
    """Cụm mạnh là bằng chứng dứt khoát — dấu hiệu Tin học chỉ phủ quyết đường YẾU.

    "Dựng thiết diện" không xuất hiện trong đề Tin học, nên một đề nói cả
    "viết chương trình" lẫn "thiết diện" vẫn là hình học.
    """
    from app.simulation.semantic_program.domain_profile import detect_domain

    de = ("Viết chương trình dựng thiết diện của hình chóp S.ABCD cắt bởi mặt "
          "phẳng qua trung điểm SA.")
    assert detect_domain(de) == DOMAIN_HINH_HOC
