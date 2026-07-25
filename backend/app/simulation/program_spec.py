# -*- coding: utf-8 -*-
"""M17 W2C — HỢP ĐỒNG `ProgramSpec`: luồng điều khiển HỮU HẠN, ngữ pháp ĐÓNG.

Đây là NGUỒN DUY NHẤT của từ vựng + giới hạn cho `algorithm.bounded_control_flow`.
Schema Gemini trong `catalog.py`, validator (`validation/program.py`) và mirror
TypeScript (`frontend/src/core/program.ts`) đều PHẢI dẫn xuất từ các hằng ở đây —
cấm viết tay enum song song (anti-pattern #1: enum viết tay từng làm Gemini
KHÔNG THỂ phát ra một giá trị hợp lệ, fail cả 3 retry mà không manh mối).

ĐÂY KHÔNG PHẢI TRÌNH THÔNG DỊCH PYTHON. Không hàm, không đệ quy, không danh
sách/chuỗi/số thực, không nhập/xuất tệp, không `break/continue`, không
`eval/exec`, không chạy mã thật. Vòng lặp BẮT BUỘC có biên: executor dừng theo
giới hạn tất định và báo trạng thái "chưa kết thúc trong giới hạn mô phỏng" —
KHÔNG treo, KHÔNG trình bày như đã chạy xong.

Spec chỉ mô tả CHƯƠNG TRÌNH (biến đầu, câu lệnh). Spec KHÔNG được chứa môi
trường sau từng bước, kết quả điều kiện, số lượt lặp thực tế, output cuối hay
trace — đó là việc của engine tất định (R0).
"""
from __future__ import annotations

SPEC_VERSION = "program-1.0"

# ── Từ vựng ĐÓNG ────────────────────────────────────────────────────────────
VALUE_TYPES: tuple[str, ...] = ("integer", "boolean")

STATEMENT_KINDS: tuple[str, ...] = ("assign", "if", "while", "output")

EXPRESSION_KINDS: tuple[str, ...] = (
    "int", "bool", "var", "unary", "binary", "compare", "logic",
)

ARITHMETIC_OPS: tuple[str, ...] = ("+", "-", "*", "//", "%")
COMPARE_OPS: tuple[str, ...] = ("==", "!=", "<", "<=", ">", ">=")
LOGIC_OPS: tuple[str, ...] = ("and", "or")
UNARY_OPS: tuple[str, ...] = ("-", "not")

# Toán tử so sánh chỉ dùng được cho số nguyên (== và != cho phép cả boolean,
# miễn HAI VẾ CÙNG KIỂU — không có coercion).
ORDER_COMPARE_OPS: tuple[str, ...] = ("<", "<=", ">", ">=")
EQUALITY_OPS: tuple[str, ...] = ("==", "!=")

# ── GIỚI HẠN CỨNG — MỘT NGUỒN DUY NHẤT ──────────────────────────────────────
# Validator và executor đều đọc từ đây. Cấm rải magic number.
LIMITS: dict[str, int] = {
    "max_statement_nodes": 12,   # tổng số câu lệnh kể cả lồng trong then/else/body
    "max_nesting_depth": 2,      # thân của if/while là độ sâu 1; lồng thêm 1 tầng
    "max_variables": 8,
    "max_expression_depth": 4,
    "max_execution_steps": 200,  # tổng số bước engine phát ra
    "max_while_iterations": 50,  # mỗi câu lệnh while
    "max_output_entries": 30,
}

# Giá trị nguyên nằm ngoài khoảng này bị từ chối (giữ mô phỏng trong tầm học
# sinh THPT và tránh số khổng lồ làm hỏng trình bày).
INT_MIN = -10_000
INT_MAX = 10_000

VARIABLE_NAME_MAX_LEN = 12

# Trạng thái kết thúc của một lượt chạy (engine sở hữu — KHÔNG nằm trong spec).
COMPLETION_COMPLETED = "completed"
COMPLETION_LIMIT_REACHED = "limit_reached"
COMPLETION_STATES: tuple[str, ...] = (COMPLETION_COMPLETED, COMPLETION_LIMIT_REACHED)

# Thông điệp học sinh khi chạm giới hạn — KHÔNG được trình bày như chạy xong.
LIMIT_REACHED_MESSAGE = (
    "Chương trình chưa kết thúc trong giới hạn mô phỏng "
    "({limit} bước). Hệ dừng lại thay vì chạy mãi — em hãy kiểm tra điều kiện "
    "lặp xem nó có bao giờ sai không."
)

# Khoá chỉ được xuất hiện trong KẾT QUẢ, cấm nằm trong spec ứng viên (R0).
FORBIDDEN_SPEC_KEYS: frozenset[str] = frozenset({
    "trace", "steps", "environment", "final_environment", "final_state",
    "result", "output_values", "condition_results", "iterations", "timeline",
})


def structures_present(config: object) -> dict[str, bool]:
    """Cấu trúc mà spec ĐÃ VALIDATE thực sự dựng được — đọc THẲNG `statements[]`,
    KHÔNG đọc `notes`/lời văn (chữ trong ghi chú không chứng minh được gì).

    Đối xứng với `table_query_engine.stages_of`: nuôi kênh đủ-ngữ-nghĩa để
    "target khai đáp ứng cả 4 cấu trúc" không còn khiến MỌI spec đều được coi là
    đủ (đúng lớp defect L4 của family bảng)."""
    present = {"assign": False, "branch": False, "loop": False, "output": False}
    if not isinstance(config, dict):
        return present
    statements = config.get("statements")
    if not isinstance(statements, list):
        return present
    for st in statements:
        if not isinstance(st, dict):
            continue
        kind = st.get("kind")
        if kind == "assign":
            present["assign"] = True
        elif kind == "if":
            present["branch"] = True
        elif kind == "while":
            present["loop"] = True
        elif kind == "output":
            present["output"] = True
    return present


def statement_kind_enum() -> list[str]:
    """Cho schema Gemini — dẫn xuất, không viết tay."""
    return list(STATEMENT_KINDS)


def expression_kind_enum() -> list[str]:
    return list(EXPRESSION_KINDS)


def all_operators() -> list[str]:
    """Hợp mọi toán tử (schema dùng một enum `op` chung; validator mới là nơi
    ràng buộc op nào hợp lệ với kind nào — schema chỉ cần đóng tập)."""
    seen: list[str] = []
    for op in (*ARITHMETIC_OPS, *COMPARE_OPS, *LOGIC_OPS, *UNARY_OPS):
        if op not in seen:
            seen.append(op)
    return seen


__all__ = [
    "SPEC_VERSION", "VALUE_TYPES", "STATEMENT_KINDS", "EXPRESSION_KINDS",
    "ARITHMETIC_OPS", "COMPARE_OPS", "LOGIC_OPS", "UNARY_OPS",
    "ORDER_COMPARE_OPS", "EQUALITY_OPS", "LIMITS", "INT_MIN", "INT_MAX",
    "VARIABLE_NAME_MAX_LEN", "COMPLETION_COMPLETED", "COMPLETION_LIMIT_REACHED",
    "COMPLETION_STATES", "LIMIT_REACHED_MESSAGE", "FORBIDDEN_SPEC_KEYS",
    "statement_kind_enum", "expression_kind_enum", "all_operators",
]
