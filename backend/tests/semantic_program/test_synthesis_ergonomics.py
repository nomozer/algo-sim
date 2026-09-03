"""Khoá **ecgônômi** của prompt sinh chương trình hình học.

Bốn guard dưới đây cố ý **không khoá câu chữ**. Prompt là văn tiếng Việt và
phải được viết lại tự do; khoá câu chữ chỉ làm mọi lần sửa prompt thành một
lượt cập nhật test máy móc, và người sửa sẽ học được rằng cách rẻ nhất để đi
tiếp là chép câu mới vào test. Thứ đáng khoá là những điều **đúng hay sai kiểm
được**: có đúng một thẩm quyền, prompt không hứa thứ engine không có, prompt
không chứa lời giải mẫu, và thẻ nhu cầu không nói dối về IR.

Ngân sách byte nằm ở `tests/test_prompt_size_guard.py` — cố ý ở chỗ khác, vì
nó áp cho MỌI prompt chứ không riêng prompt này.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import (
    PointExpr,
    SemanticStatement,
    ValueExpr,
)
from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAINS,
    program_skill_for,
)
from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

SKILLS = Path(__file__).resolve().parents[2] / "app" / "ai" / "skills"
TEN_SKILL = program_skill_for(DOMAIN_HINH_HOC)
PROMPT = (SKILLS / f"{TEN_SKILL}.md").read_text(encoding="utf-8")


def _tags(union) -> frozenset[str]:
    """Rút tên `kind` từ một union đã gắn thẻ phân biệt của Pydantic."""
    return frozenset(re.findall(r"Tag\(tag='([a-z_]+)'\)", repr(union)))


TAG_DIEM = _tags(PointExpr)
TAG_GIA_TRI = _tags(ValueExpr)
TAG_CAU_LENH = _tags(SemanticStatement)


# ── E1 · MỘT thẩm quyền prompt ────────────────────────────────────────────
def test_E1_chi_mot_prompt_synthesis_cho_hinh_hoc():
    """Mỗi miền một skill, và không có prompt cong SONG SONG.

    Cách hỏng thật đã xảy ra hai lần (xem `_kiem_mien`): một bộ chọn thứ hai
    xuất hiện, và một nửa hệ đo hình học bằng hợp đồng của môn khác. Ở đây
    chặn biến thể rẻ nhất của cùng lỗi — tách hướng dẫn khối cong ra một file
    riêng "cho gọn", rồi hai file trôi khỏi nhau.
    """
    assert len({program_skill_for(d) for d in DOMAINS}) == len(DOMAINS)

    mang_khoi_cong = sorted(
        p.name for p in SKILLS.glob("*.md")
        if "construct_curved_solid" in p.read_text(encoding="utf-8")
    )
    assert mang_khoi_cong == [f"{TEN_SKILL}.md"], (
        f"SYNTHESIS_PROMPT_AUTHORITIES phải = 1, đang thấy {mang_khoi_cong}"
    )


# ── E2 · prompt không hứa thứ engine không có ─────────────────────────────
def test_E2_moi_dinh_danh_trong_prompt_deu_co_that():
    """Định danh trong dấu nháy ngược phải tồn tại trong IR.

    Đây là guard chống TRÔI MỘT CHIỀU: đổi tên một phép trong `contract.py`
    thì test hợp đồng đỏ, nhưng prompt vẫn nêu tên cũ và **không có gì đỏ** —
    mô hình sẽ sinh ra tên đã chết, ir_static bác, và lỗi hiện ra như "mô hình
    kém" chứ không như "tài liệu sai". Đã bắt được một lần: thẻ nhu cầu hứa
    "giao hai mặt" trong lúc `ConstructLineStmt` chỉ nhận hai điểm — hoá ra
    phép ấy có thật nhưng ở `ValueExpr`, tới qua `assign`.
    """
    # Từ tiếng Anh thường trong văn xuôi, không phải định danh IR.
    NGOAI_LE = {"float", "kind", "z"}
    truong_schema = {
        "target_var", "at", "model_assumption", "source_fact_id", "label",
        "description", "pedagogical_intent", "statements", "ratio",
        "through", "through_a", "through_b", "expr", "value",
    }
    hop_le = (
        TAG_CAU_LENH | TAG_DIEM | TAG_GIA_TRI | set(BANG_PHEP_DO)
        | truong_schema | NGOAI_LE
    )

    trong_prompt = {
        t for t in re.findall(r"`([a-z][a-z0-9_]*)`", PROMPT)
    }
    ma = sorted(trong_prompt - hop_le)
    assert not ma, f"prompt nêu định danh KHÔNG tồn tại trong IR: {ma}"


# ── E3 · không có lời giải mẫu ────────────────────────────────────────────
def test_E3_prompt_khong_chua_chuong_trinh_mau():
    """`CURVED_PROBLEM_FAMILY_TEMPLATES = 0`.

    Một chương trình mẫu hoàn chỉnh dạy mô hình **chép**, không dạy nó **hợp
    thành**: nó sẽ khớp đề mới vào họ gần nhất và sai lặng lẽ ở chỗ đề lệch
    khỏi mẫu. Ngoại lệ duy nhất được phép là phản ví dụ R0 — một dòng, cố ý
    SAI, để chỉ ra thứ không được viết.
    """
    so_kind = PROMPT.count('"kind"')
    assert so_kind <= 1, (
        f"prompt chứa {so_kind} câu lệnh JSON; >1 nghĩa là đã có chương trình "
        "mẫu — mô hình sẽ chép nó thay vì hợp thành"
    )
    assert '"statements"' not in PROMPT


# ── E4 · thẻ nhu cầu không nói dối ────────────────────────────────────────
@pytest.mark.parametrize(
    "phep,o_dau,hua_gi",
    [
        ("midpoint", TAG_DIEM, "ĐIỂM · trung điểm"),
        ("divide_segment", TAG_DIEM, "ĐIỂM · chia đoạn"),
        ("project_onto", TAG_DIEM, "ĐIỂM · hình chiếu"),
        ("intersect_line_plane", TAG_DIEM, "ĐIỂM · giao"),
        ("intersect_line_line", TAG_DIEM, "ĐIỂM · giao"),
        ("translate", TAG_DIEM, "ĐIỂM · tịnh tiến"),
        ("intersect_plane_plane", TAG_GIA_TRI, "ĐƯỜNG · giao hai mặt"),
        ("plane_perpendicular_to_line", TAG_GIA_TRI, "MẶT · vuông góc một đường"),
    ],
)
def test_E4_the_nhu_cau_van_dung(phep, o_dau, hua_gi):
    """Mỗi phép prompt hứa phải còn trong đúng union nó tới được.

    Prompt bảo mô hình *"cần một vật chưa có thì tra thẻ theo NHU CẦU"* rồi
    liệt kê các nhu cầu bằng tiếng Việt. Gỡ một phép khỏi IR mà quên prompt là
    dạy mô hình một đường dựng không tồn tại — và nó sẽ tin, vì prompt là thứ
    duy nhất nó đọc trước khi viết.

    Union nào cũng quan trọng: `PointExpr` là thứ `construct_point.expr` nhận,
    `ValueExpr` là thứ `assign` nhận. Cùng một tên nằm sai union thì mô hình
    thấy nó ở chỗ không dùng được.
    """
    assert phep in o_dau, f"prompt còn hứa `{hua_gi}` nhưng `{phep}` đã mất"
