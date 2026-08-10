"""M14 Task 4 — lock prescribed_procedure trong ANALYZE_SCHEMA (§E4, nullable, enum đóng)."""

from __future__ import annotations

from app.ai.pipeline import ANALYZE_SCHEMA
from app.simulation.families.sorting import (
    PRESCRIBED_PROCEDURES,
    PROC_ADJACENT_SWAP,
    PROC_NONE,
    PROC_PARTITION,
    PROC_SELECT_EXTREME,
    PROC_SHIFT_INSERT,
)


def test_field_ton_tai_nullable_khong_bat_buoc():
    props = ANALYZE_SCHEMA["properties"]
    assert "prescribed_procedure" in props
    field = props["prescribed_procedure"]
    assert field["type"] == "STRING"
    assert field.get("nullable") is True
    # KHÔNG nằm trong required (không phá analyze domain khác — N7)
    assert "prescribed_procedure" not in ANALYZE_SCHEMA["required"]


def test_enum_dong_dung_sau_gia_tri():
    # M15 Task 7: enum giờ dẫn xuất từ analyze_exposed_values() (superset của
    # PRESCRIBED_PROCEDURES legacy sorting + giá trị positional mới) — vẫn ĐÓNG,
    # legacy sorting giữ nguyên giá trị (rev2 điểm 2).
    field = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]
    assert set(PRESCRIBED_PROCEDURES) <= set(field["enum"])
    assert set(field["enum"]) == {
        PROC_NONE,
        PROC_ADJACENT_SWAP,
        PROC_SHIFT_INSERT,
        PROC_SELECT_EXTREME,
        PROC_PARTITION,
        "other_unspecified",
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
        # M17 W3-LIVE-C1 — cơ chế tra BẢNG MÃ ký tự. Trước đây họ positional
        # được liệt kê bằng string VIẾT TAY nên giá trị này bị bỏ sót khi W3
        # thêm nó vào FAMILY_MECHANISMS: analyze KHÔNG THỂ phát ra cơ chế mà
        # `binary.character_encoding` sở hữu ⇒ mechanism gate luôn gap. Enum nay
        # splat thẳng từ taxonomy (anti-pattern #1).
        "positional_representation.character_code_mapping",
        # M17 W2A — cơ chế duyệt cây (nuôi route-consistency gate)
        "tree_traversal.preorder",
        "tree_traversal.inorder",
        "tree_traversal.postorder",
        "tree_traversal.level_order",
        # M17 W2C — cơ chế luồng điều khiển hữu hạn (cùng lý do: nuôi
        # route-consistency gate, KHÔNG keyword-match đề bài)
        "bounded_control_flow.assignment",
        "bounded_control_flow.conditional_branch",
        "bounded_control_flow.bounded_loop",
        # W4B-2Z — cơ chế thuộc tính trình bày có ràng buộc. Phơi ra để
        # `_family_mismatch` nhìn thấy được đề CSS bị định tuyến sang
        # `generic.rule_scene` (định tuyến theo SỞ HỮU, không theo chuỗi).
        "web_presentation.bounded_style_properties",
    }


def test_khong_chua_gia_tri_dang_ket_qua_hay_ten_thuat_toan():
    # §O7: enum mô tả CƠ CHẾ, không chứa result/trace, không tên thuật toán
    field = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]
    banned = {"bubble", "insertion", "selection", "quick", "sorted", "result", "trace", "timeline"}
    for val in field["enum"]:
        assert val not in banned


def test_analyze_schema_enum_dan_xuat_tu_mechanisms():
    from app.ai.pipeline import ANALYZE_SCHEMA
    from app.simulation.mechanisms import analyze_exposed_values
    assert ANALYZE_SCHEMA["properties"]["prescribed_procedure"]["enum"] == list(analyze_exposed_values())


def test_enum_giu_legacy_sorting_va_co_positional():
    from app.ai.pipeline import ANALYZE_SCHEMA
    e = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]["enum"]
    assert "adjacent_compare_swap" in e and "positional_representation.non_binary_base" in e


# ── M17 W3-LIVE-C2 — GUIDANCE LOCK ───────────────────────────────
# Phơi một giá trị ra enum mà KHÔNG dạy analyze khi nào phát nó là lỗi đã cắn
# HAI lần: `_GENERIC_SCHEMA` thiếu `drag` (Gemini không thể phát dù prompt cho
# phép), và `character_code_mapping` bị bỏ quên khiến cơ chế DUY NHẤT của
# `binary.character_encoding` bất khả phát ⇒ mechanism gate không bao giờ thoả
# mãn. Lock này biến "im lặng nhiều wave" thành ĐỎ ngay.
#
# `analyze.md` VẪN là source of truth của hướng dẫn — test chỉ đọc, không dựng
# registry guidance song song, không parse Markdown tổng quát, không phụ thuộc
# prompt fixture nào.

def _analyze_skill_text() -> str:
    """Đọc qua CHÍNH loader production — không tự mở đường đọc file thứ hai."""
    from app.ai.gemini import load_skill
    return load_skill("analyze")


def _uncovered_exposed_values() -> list[str]:
    from app.simulation.mechanisms import analyze_exposed_values, canonical_mechanism
    text = _analyze_skill_text()
    missing = []
    for raw in analyze_exposed_values():
        if canonical_mechanism(raw) is None:
            continue                      # "none" — trạng thái vắng tín hiệu
        if raw not in text:
            missing.append(raw)
        # Giá trị namespaced phải xuất hiện ĐỦ ĐỊNH DANH, không chỉ phần đuôi:
        # trùng đuôi giữa hai family sẽ làm lock mất hiệu lực.
    return missing


def test_moi_gia_tri_exposed_deu_co_huong_dan_trong_analyze_md():
    """Khoá chính: enum ⊆ hướng dẫn. Thêm cơ chế exposed mà quên dạy ⇒ ĐỎ."""
    missing = _uncovered_exposed_values()
    assert missing == [], (
        "Các giá trị được phơi cho analyze nhưng KHÔNG có hướng dẫn trong "
        f"analyze.md: {missing}. Phơi mà không dạy = LLM không thể phát ra."
    )


def test_day_ma_khong_phoi_cung_la_LOI(monkeypatch):
    """Khoá NGƯỢC (W4B-2Z): hướng dẫn ⊆ enum.

    Lock trên chỉ bắt chiều "phơi mà không dạy". Chiều còn lại nguy hiểm không
    kém và ĐÃ ĐO ĐƯỢC bằng tiêm lỗi: gỡ một family khỏi `analyze_exposed_values`
    trong khi `analyze.md` vẫn dạy cơ chế đó thì prompt bảo LLM phát ra một giá
    trị mà SCHEMA từ chối — đúng tiền lệ W3-LIVE-C1 (`character_code_mapping`).
    Triệu chứng ở đời thực không phải lỗi rõ ràng, mà là im lặng chọn hàng xóm
    gần nhất rồi rơi vào `capability_gap`.

    Suy từ nguồn: mọi cơ chế trong taxonomy được analyze.md gọi ĐÍCH DANH thì
    phải có mặt trong enum.
    """
    from app.simulation.mechanisms import FAMILY_MECHANISMS, analyze_exposed_values

    text = _analyze_skill_text()
    exposed = set(analyze_exposed_values())
    taught_but_hidden = sorted(
        mech
        for mechs in FAMILY_MECHANISMS.values()
        for mech in mechs
        if mech in text and mech not in exposed
    )
    assert taught_but_hidden == [], (
        f"analyze.md dạy nhưng enum KHÔNG phơi: {taught_but_hidden}. "
        "Dạy mà không phơi = LLM được bảo phát ra giá trị schema sẽ từ chối."
    )


def test_guidance_phu_ho_positional_va_bounded_control_flow():
    """Sáu giá trị W3-LIVE-C2 nhắm tới — nêu đích danh để hồi quy đọc được."""
    text = _analyze_skill_text()
    for mech in (
        "positional_representation.character_code_mapping",
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
        "bounded_control_flow.assignment",
        "bounded_control_flow.conditional_branch",
        "bounded_control_flow.bounded_loop",
    ):
        assert mech in text, f"analyze.md thiếu hướng dẫn cho {mech}"


def test_guidance_positional_quyet_theo_HINH_DANG_DAU_VAO_khong_theo_target():
    """Luật phải nói về đầu vào ký tự ↔ số, và KHÔNG được nhắc tên target."""
    text = _analyze_skill_text()
    assert "KÝ TỰ" in text and "SỐ" in text
    for target_id in ("binary.character_encoding", "binary.decimal_to_binary",
                      "binary.base_conversion", "generic.rule_scene"):
        assert target_id not in text, f"analyze.md không được nhắc target id: {target_id}"


def test_lock_chi_rang_buoc_gia_tri_EXPOSED():
    """Cơ chế KHÔNG phơi cho analyze thì analyze.md không cần nhắc — lock không
    được lan sang toàn taxonomy (vd họ relational_table_query, layered_pdu)."""
    from app.simulation.mechanisms import FAMILY_MECHANISMS, analyze_exposed_values
    exposed = set(analyze_exposed_values())
    all_mechs = {m for ms in FAMILY_MECHANISMS.values() for m in ms}
    unexposed = all_mechs - exposed
    assert unexposed, "phải còn cơ chế không phơi — nếu không, test này vô nghĩa"
    text = _analyze_skill_text()
    # KHÔNG assert chúng vắng mặt (analyze.md có thể nhắc vì lý do khác);
    # chỉ khẳng định chúng KHÔNG nằm trong tập bị lock.
    assert not (unexposed & set(_uncovered_exposed_values()))
    assert isinstance(text, str) and text
