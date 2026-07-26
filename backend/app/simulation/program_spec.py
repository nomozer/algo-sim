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

SPEC_VERSION = "program-2.0"

# ── Từ vựng ĐÓNG ────────────────────────────────────────────────────────────
VALUE_TYPES: tuple[str, ...] = ("integer", "boolean")

STATEMENT_KINDS: tuple[str, ...] = ("assign", "if", "while", "output")

# ── W2C-C1 §L2 — BIỂU THỨC INLINE (bề mặt LLM) ──────────────────────────────
# Live W2C cho thấy bảng biểu thức PHẲNG + tham chiếu id là gánh nặng biểu diễn:
# 3/3 lượt Gemini quên nối `left`/`right` sang id con. Gánh nặng đó KHÔNG mang
# giá trị học tập nào. Bề mặt mới là biểu thức **inline, NÔNG, PHI ĐỆ QUY** —
# vẫn biểu diễn được bằng structured output vì độ sâu CỐ ĐỊNH.
#
#   Operand        := {kind: int|bool|var, int_value?|bool_value?|name?}
#   ValueExpr      := {left: Operand, op: số học|null, right: Operand|null}
#   ConditionAtom  := {left: ValueExpr, op: so sánh|null, right: ValueExpr|null,
#                      negated: bool}
#   ConditionExpr  := {op: and|or|null, atoms: [ConditionAtom]}   (op null ⇒ 1 atom)
#
# KHÔNG lồng nhóm logic trong nhóm logic, KHÔNG tham chiếu chéo id, KHÔNG cây
# đệ quy tuỳ ý. Biểu thức nhiều tầng (vd `x*2 + 1`) diễn đạt bằng CÂU LỆNH
# TRUNG GIAN — giữ ngữ pháp đóng thay vì mở AST vô hạn.
OPERAND_KINDS: tuple[str, ...] = ("int", "bool", "var")

# Biểu diễn NỘI BỘ (implementation detail của engine) — LLM KHÔNG sinh cái này.
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
    # Giới hạn NỘI BỘ (lưới an toàn). Từ C1, độ nông của biểu thức được bảo đảm
    # bằng CHÍNH HÌNH DẠNG của ngữ pháp inline chứ không bằng bộ đếm này.
    "max_expression_depth": 6,
    "max_condition_atoms": 3,    # số vế trong MỘT nhóm logic (không lồng nhóm)
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


class NormalizeError(ValueError):
    """Biểu thức inline nằm ngoài ngữ pháp — normalizer TỪ CHỐI, không đoán."""


def _operand_node(raw: object, where: str, emit) -> str:
    if not isinstance(raw, dict):
        raise NormalizeError(f"{where}: toán hạng phải là một đối tượng.")
    kind = raw.get("kind")
    if kind not in OPERAND_KINDS:
        raise NormalizeError(f"{where}: loại toán hạng không hỗ trợ: {kind!r}.")
    if kind == "int":
        v = raw.get("int_value")
        if not isinstance(v, int) or isinstance(v, bool):
            raise NormalizeError(f"{where}: hằng số nguyên thiếu 'int_value'.")
        if not (INT_MIN <= v <= INT_MAX):
            raise NormalizeError(f"{where}: hằng số ngoài khoảng {INT_MIN}..{INT_MAX}.")
        return emit({"kind": "int", "int_value": v})
    if kind == "bool":
        v = raw.get("bool_value")
        if not isinstance(v, bool):
            raise NormalizeError(f"{where}: hằng đúng/sai thiếu 'bool_value'.")
        return emit({"kind": "bool", "bool_value": v})
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise NormalizeError(f"{where}: tham chiếu biến thiếu 'name'.")
    return emit({"kind": "var", "name": name})


def _value_node(raw: object, where: str, emit) -> str:
    """ValueExpr := Operand | Operand <số học> Operand (KHÔNG sâu hơn)."""
    if not isinstance(raw, dict):
        raise NormalizeError(f"{where}: biểu thức giá trị phải là một đối tượng.")
    left = _operand_node(raw.get("left"), where, emit)
    op = raw.get("op")
    if op in (None, ""):
        if raw.get("right") not in (None, {}):
            raise NormalizeError(f"{where}: có 'right' thì phải có toán tử.")
        return left
    if op not in ARITHMETIC_OPS:
        raise NormalizeError(
            f"{where}: toán tử số học không hỗ trợ: {op!r}. Chỉ có {list(ARITHMETIC_OPS)}.")
    right = _operand_node(raw.get("right"), where, emit)
    return emit({"kind": "binary", "op": op, "left": left, "right": right})


def _atom_node(raw: object, where: str, emit) -> str:
    """ConditionAtom := ValueExpr (đúng/sai) | ValueExpr <so sánh> ValueExpr, có
    thể phủ định."""
    if not isinstance(raw, dict):
        raise NormalizeError(f"{where}: vế điều kiện phải là một đối tượng.")
    left = _value_node(raw.get("left"), where, emit)
    op = raw.get("op")
    if op in (None, ""):
        node = left
    elif op not in COMPARE_OPS:
        raise NormalizeError(
            f"{where}: toán tử so sánh không hỗ trợ: {op!r}. Chỉ có {list(COMPARE_OPS)}.")
    else:
        right = _value_node(raw.get("right"), where, emit)
        node = emit({"kind": "compare", "op": op, "left": left, "right": right})
    if raw.get("negated") is True:
        node = emit({"kind": "unary", "op": "not", "operand": node})
    return node


def _condition_node(raw: object, where: str, emit) -> str:
    """ConditionExpr := 1 atom | nhóm logic PHẲNG các atom (không lồng nhóm)."""
    if not isinstance(raw, dict):
        raise NormalizeError(f"{where}: điều kiện phải là một đối tượng.")
    atoms = raw.get("atoms")
    if not isinstance(atoms, list) or not atoms:
        raise NormalizeError(f"{where}: điều kiện cần ít nhất một vế trong 'atoms'.")
    if len(atoms) > LIMITS["max_condition_atoms"]:
        raise NormalizeError(
            f"{where}: điều kiện có {len(atoms)} vế, tối đa "
            f"{LIMITS['max_condition_atoms']} vế trong một nhóm.")
    op = raw.get("op")
    if len(atoms) == 1:
        if op not in (None, "", *LOGIC_OPS):
            raise NormalizeError(f"{where}: toán tử logic không hỗ trợ: {op!r}.")
        return _atom_node(atoms[0], where, emit)
    if op not in LOGIC_OPS:
        raise NormalizeError(
            f"{where}: nhiều vế thì cần toán tử {list(LOGIC_OPS)}, đang là {op!r}.")
    node = _atom_node(atoms[0], where, emit)
    for extra in atoms[1:]:                      # gộp TRÁI SANG PHẢI, tất định
        node = emit({"kind": "logic", "op": op, "left": node,
                     "right": _atom_node(extra, where, emit)})
    return node


def normalize_inline_program(raw_statements: object) -> tuple[list[dict], list[dict]]:
    """Biểu thức inline (bề mặt LLM) → bảng biểu thức NỘI BỘ + câu lệnh tham
    chiếu bằng id.

    TẤT ĐỊNH tuyệt đối: id sinh theo thứ tự duyệt (`_e1`, `_e2`…), cùng đầu vào
    cho cùng đầu ra. KHÔNG gọi LLM, KHÔNG đoán ý, KHÔNG bù toán tử thiếu, KHÔNG
    sửa tên biến, KHÔNG giá trị mặc định. Sai ngữ pháp thì ném `NormalizeError`.
    """
    if not isinstance(raw_statements, list):
        raise NormalizeError("'statements' phải là danh sách.")

    expressions: list[dict] = []
    seen: dict[str, str] = {}          # chữ ký → id (gộp nút trùng, vẫn tất định)

    def emit(node: dict) -> str:
        key = repr(sorted(node.items()))
        if key in seen:
            return seen[key]
        eid = f"_e{len(expressions) + 1}"
        node = {"id": eid, **node}
        expressions.append(node)
        seen[key] = eid
        return eid

    out: list[dict] = []
    for raw in raw_statements:
        if not isinstance(raw, dict):
            raise NormalizeError("Mỗi câu lệnh phải là một đối tượng.")
        sid = raw.get("id")
        kind = raw.get("kind")
        where = f"câu lệnh '{sid}'"
        st: dict = {"id": sid, "kind": kind}
        if kind == "assign":
            st["target"] = raw.get("target")
            st["value"] = _value_node(raw.get("value"), where, emit)
        elif kind == "output":
            st["value"] = _value_node(raw.get("value"), where, emit)
        elif kind == "if":
            st["condition"] = _condition_node(raw.get("condition"), where, emit)
            st["then_body"] = raw.get("then_body") or []
            st["else_body"] = raw.get("else_body") or []
        elif kind == "while":
            st["condition"] = _condition_node(raw.get("condition"), where, emit)
            st["body"] = raw.get("body") or []
            st["max_iterations"] = raw.get("max_iterations")
        else:
            raise NormalizeError(
                f"Loại câu lệnh không hỗ trợ: {kind!r}. Chỉ có {list(STATEMENT_KINDS)} "
                "— không có hàm, đệ quy, break/continue.")
        out.append(st)
    return expressions, out


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
