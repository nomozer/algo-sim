# -*- coding: utf-8 -*-
"""M17 W2C — Validator FAIL-CLOSED cho `algorithm.bounded_control_flow`.

Chạy TRƯỚC executor. Mọi từ vựng/giới hạn đọc từ `simulation/program_spec.py`
(một nguồn) — cấm magic number ở đây.

Cấu trúc spec là DANH SÁCH PHẲNG + THAM CHIẾU ID (đúng tiền lệ
`logic.boolean_dag`): schema structured-output của Gemini KHÔNG biểu diễn được
kiểu đệ quy, nên `statements[]` và `expressions[]` là bảng phẳng, còn lồng nhau
diễn đạt bằng danh sách id trong `then_body`/`else_body`/`body`.

KHÔNG coercion: `"5"` không thành `5`, `true` không thành `1`, `1` không thành
`true`. Sai kiểu là TỪ CHỐI, không phải "đoán ý".
"""
from __future__ import annotations

import re

from app.simulation.program_spec import (
    ARITHMETIC_OPS,
    COMPARE_OPS,
    EQUALITY_OPS,
    EXPRESSION_KINDS,
    FORBIDDEN_SPEC_KEYS,
    INT_MAX,
    INT_MIN,
    LIMITS,
    LOGIC_OPS,
    ORDER_COMPARE_OPS,
    SPEC_VERSION,
    STATEMENT_KINDS,
    UNARY_OPS,
    VALUE_TYPES,
    VARIABLE_NAME_MAX_LEN,
)

_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

INTEGER = "integer"
BOOLEAN = "boolean"

_TYPE_VI = {INTEGER: "số nguyên", BOOLEAN: "đúng/sai"}


def _is_int(v: object) -> bool:
    """int thật — `True` là `bool` nên PHẢI loại ra (không coercion)."""
    return isinstance(v, int) and not isinstance(v, bool)


def _is_bool(v: object) -> bool:
    return isinstance(v, bool)


def _err(msg: str) -> tuple[None, str]:
    return None, msg


def validate_program_config(raw) -> tuple[dict | None, str | None]:
    """`(config_sạch, None)` hoặc `(None, lý_do)`. Lý do là tiếng Việt, dành cho
    vòng retry của `stage_simulate` — không phải thông điệp học sinh."""
    if not isinstance(raw, dict):
        return _err("Config phải là một đối tượng JSON.")

    leaked = sorted(k for k in raw if k in FORBIDDEN_SPEC_KEYS)
    if leaked:
        return _err(
            f"Config KHÔNG được chứa kết quả hay diễn biến chạy: {', '.join(leaked)}. "
            "Chỉ mô tả chương trình (biến ban đầu + câu lệnh); engine tự chạy."
        )

    version = raw.get("program_version") or SPEC_VERSION
    if version != SPEC_VERSION:
        return _err(f"program_version phải là '{SPEC_VERSION}'.")

    variables, err = _check_variables(raw.get("variables"))
    if err:
        return _err(err)

    expressions, err = _check_expressions(raw.get("expressions"), variables)
    if err:
        return _err(err)

    statements, main, err = _check_statements(raw.get("statements"), raw.get("main"), expressions)
    if err:
        return _err(err)

    err = _check_types(statements, expressions, variables)
    if err:
        return _err(err)

    return {
        "program_version": SPEC_VERSION,
        "variables": variables,
        "expressions": expressions,
        "statements": statements,
        "main": main,
        **({"notes": raw["notes"]} if isinstance(raw.get("notes"), str) else {}),
    }, None


# ── biến ────────────────────────────────────────────────────────────────────

def _check_variables(raw) -> tuple[list[dict], str | None]:
    if not isinstance(raw, list) or not raw:
        return [], "Cần ít nhất một biến ban đầu trong 'variables'."
    if len(raw) > LIMITS["max_variables"]:
        return [], f"Tối đa {LIMITS['max_variables']} biến, đề đang có {len(raw)}."

    out: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            return [], "Mỗi biến phải là một đối tượng {name, type, int_value|bool_value}."
        name = item.get("name")
        if not isinstance(name, str) or not _NAME_RE.match(name):
            return [], f"Tên biến không hợp lệ: {name!r} (chữ cái đầu, chỉ chữ/số/gạch dưới)."
        if len(name) > VARIABLE_NAME_MAX_LEN:
            return [], f"Tên biến '{name}' dài quá {VARIABLE_NAME_MAX_LEN} ký tự."
        if name in seen:
            return [], f"Biến '{name}' được khai báo hai lần."
        seen.add(name)

        vtype = item.get("type")
        if vtype not in VALUE_TYPES:
            return [], f"Kiểu của biến '{name}' phải là một trong {list(VALUE_TYPES)}."

        iv, bv = item.get("int_value"), item.get("bool_value")
        if vtype == INTEGER:
            if not _is_int(iv):
                return [], f"Biến '{name}' khai kiểu số nguyên nên cần 'int_value' là số nguyên."
            if bv is not None:
                return [], f"Biến '{name}' là số nguyên thì 'bool_value' phải để trống."
            if not (INT_MIN <= iv <= INT_MAX):
                return [], f"Giá trị của '{name}' phải trong khoảng {INT_MIN}..{INT_MAX}."
            out.append({"name": name, "type": INTEGER, "int_value": iv, "bool_value": None})
        else:
            if not _is_bool(bv):
                return [], f"Biến '{name}' khai kiểu đúng/sai nên cần 'bool_value' là true/false."
            if iv is not None:
                return [], f"Biến '{name}' là đúng/sai thì 'int_value' phải để trống."
            out.append({"name": name, "type": BOOLEAN, "int_value": None, "bool_value": bv})
    return out, None


# ── biểu thức ───────────────────────────────────────────────────────────────

def _check_expressions(raw, variables: list[dict]) -> tuple[list[dict], str | None]:
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        return [], "'expressions' phải là danh sách."

    known_vars = {v["name"] for v in variables}
    out: list[dict] = []
    ids: set[str] = set()

    for item in raw:
        if not isinstance(item, dict):
            return [], "Mỗi biểu thức phải là một đối tượng có 'id' và 'kind'."
        eid = item.get("id")
        if not isinstance(eid, str) or not eid.strip():
            return [], "Mỗi biểu thức phải có 'id' không rỗng."
        if eid in ids:
            return [], f"Biểu thức trùng id: '{eid}'."
        ids.add(eid)

        kind = item.get("kind")
        if kind not in EXPRESSION_KINDS:
            return [], f"Loại biểu thức không hỗ trợ: {kind!r}. Chỉ có {list(EXPRESSION_KINDS)}."

        node = {"id": eid, "kind": kind, "int_value": None, "bool_value": None,
                "name": None, "op": None, "left": None, "right": None, "operand": None}

        if kind == "int":
            iv = item.get("int_value")
            if not _is_int(iv):
                return [], f"Biểu thức '{eid}' kiểu 'int' cần 'int_value' là số nguyên."
            if not (INT_MIN <= iv <= INT_MAX):
                return [], f"Hằng số ở '{eid}' phải trong khoảng {INT_MIN}..{INT_MAX}."
            node["int_value"] = iv
        elif kind == "bool":
            bv = item.get("bool_value")
            if not _is_bool(bv):
                return [], f"Biểu thức '{eid}' kiểu 'bool' cần 'bool_value' là true/false."
            node["bool_value"] = bv
        elif kind == "var":
            name = item.get("name")
            if not isinstance(name, str) or name not in known_vars:
                return [], (
                    f"Biểu thức '{eid}' dùng biến {name!r} chưa được khai báo giá trị ban đầu. "
                    "Mọi biến phải có mặt trong 'variables'."
                )
            node["name"] = name
        elif kind == "unary":
            op = item.get("op")
            if op not in UNARY_OPS:
                return [], f"Toán tử một ngôi không hỗ trợ: {op!r}. Chỉ có {list(UNARY_OPS)}."
            if not isinstance(item.get("operand"), str):
                return [], f"Biểu thức '{eid}' cần 'operand' là id của biểu thức con."
            node["op"], node["operand"] = op, item["operand"]
        else:  # binary | compare | logic
            allowed = {"binary": ARITHMETIC_OPS, "compare": COMPARE_OPS, "logic": LOGIC_OPS}[kind]
            op = item.get("op")
            if op not in allowed:
                return [], f"Toán tử {op!r} không dùng được với loại '{kind}'. Chỉ có {list(allowed)}."
            if not isinstance(item.get("left"), str) or not isinstance(item.get("right"), str):
                return [], f"Biểu thức '{eid}' cần 'left' và 'right' là id của biểu thức con."
            node["op"], node["left"], node["right"] = op, item["left"], item["right"]

        out.append(node)

    by_id = {n["id"]: n for n in out}
    for node in out:
        for ref_key in ("operand", "left", "right"):
            ref = node[ref_key]
            if ref is not None and ref not in by_id:
                return [], f"Biểu thức '{node['id']}' tham chiếu '{ref}' không tồn tại."

    err = _check_expression_depth(out, by_id)
    if err:
        return [], err
    return out, None


def _check_expression_depth(nodes: list[dict], by_id: dict[str, dict]) -> str | None:
    """Độ sâu + phát hiện vòng (biểu thức là DAG, KHÔNG được có vòng)."""
    depth: dict[str, int] = {}
    visiting: set[str] = set()

    def walk(eid: str) -> int | None:
        if eid in depth:
            return depth[eid]
        if eid in visiting:
            return None  # vòng
        visiting.add(eid)
        node = by_id[eid]
        children = [node[k] for k in ("operand", "left", "right") if node[k] is not None]
        best = 0
        for c in children:
            d = walk(c)
            if d is None:
                return None
            best = max(best, d)
        visiting.discard(eid)
        depth[eid] = best + 1
        return depth[eid]

    for node in nodes:
        d = walk(node["id"])
        if d is None:
            return f"Biểu thức '{node['id']}' tham chiếu vòng — không tính được."
        if d > LIMITS["max_expression_depth"]:
            return (
                f"Biểu thức '{node['id']}' lồng {d} tầng, vượt giới hạn "
                f"{LIMITS['max_expression_depth']} tầng của mô phỏng."
            )
    return None


# ── câu lệnh ────────────────────────────────────────────────────────────────

def _check_statements(raw, main, expressions: list[dict]) -> tuple[list[dict], list[str], str | None]:
    if not isinstance(raw, list) or not raw:
        return [], [], "Cần ít nhất một câu lệnh trong 'statements'."
    if len(raw) > LIMITS["max_statement_nodes"]:
        return [], [], (
            f"Chương trình có {len(raw)} câu lệnh, vượt giới hạn "
            f"{LIMITS['max_statement_nodes']} câu lệnh của mô phỏng."
        )

    expr_ids = {e["id"] for e in expressions}
    out: list[dict] = []
    ids: set[str] = set()

    for item in raw:
        if not isinstance(item, dict):
            return [], [], "Mỗi câu lệnh phải là một đối tượng có 'id' và 'kind'."
        sid = item.get("id")
        if not isinstance(sid, str) or not sid.strip():
            return [], [], "Mỗi câu lệnh phải có 'id' không rỗng."
        if sid in ids:
            return [], [], f"Câu lệnh trùng id: '{sid}'."
        ids.add(sid)

        kind = item.get("kind")
        if kind not in STATEMENT_KINDS:
            return [], [], (
                f"Loại câu lệnh không hỗ trợ: {kind!r}. Mô phỏng chỉ có "
                f"{list(STATEMENT_KINDS)} — không có hàm, đệ quy, break/continue."
            )

        node = {"id": sid, "kind": kind, "target": None, "value": None,
                "condition": None, "then_body": [], "else_body": [], "body": [],
                "max_iterations": None}

        if kind == "assign":
            target = item.get("target")
            if not isinstance(target, str):
                return [], [], f"Câu lệnh gán '{sid}' cần 'target' là tên biến."
            if item.get("value") not in expr_ids:
                return [], [], f"Câu lệnh gán '{sid}' cần 'value' là id của một biểu thức."
            node["target"], node["value"] = target, item["value"]
        elif kind == "output":
            if item.get("value") not in expr_ids:
                return [], [], f"Câu lệnh hiển thị '{sid}' cần 'value' là id của một biểu thức."
            node["value"] = item["value"]
        elif kind == "if":
            if item.get("condition") not in expr_ids:
                return [], [], f"Câu lệnh rẽ nhánh '{sid}' cần 'condition' là id của một biểu thức."
            node["condition"] = item["condition"]
            for key in ("then_body", "else_body"):
                block = item.get(key) or []
                if not isinstance(block, list) or not all(isinstance(x, str) for x in block):
                    return [], [], f"'{key}' của '{sid}' phải là danh sách id câu lệnh."
                node[key] = list(block)
            if not node["then_body"]:
                return [], [], f"Câu lệnh rẽ nhánh '{sid}' phải có ít nhất một câu lệnh ở nhánh đúng."
        else:  # while
            if item.get("condition") not in expr_ids:
                return [], [], f"Vòng lặp '{sid}' cần 'condition' là id của một biểu thức."
            node["condition"] = item["condition"]
            block = item.get("body") or []
            if not isinstance(block, list) or not all(isinstance(x, str) for x in block):
                return [], [], f"'body' của '{sid}' phải là danh sách id câu lệnh."
            if not block:
                return [], [], f"Vòng lặp '{sid}' phải có ít nhất một câu lệnh trong thân."
            node["body"] = list(block)
            mi = item.get("max_iterations")
            if not _is_int(mi) or mi < 1:
                return [], [], (
                    f"Vòng lặp '{sid}' phải khai 'max_iterations' — số lượt tối đa "
                    "(mô phỏng không chạy vòng lặp vô biên)."
                )
            if mi > LIMITS["max_while_iterations"]:
                return [], [], (
                    f"'max_iterations' của '{sid}' là {mi}, vượt giới hạn "
                    f"{LIMITS['max_while_iterations']} lượt của mô phỏng."
                )
            node["max_iterations"] = mi

        out.append(node)

    by_id = {s["id"]: s for s in out}

    if not isinstance(main, list) or not main or not all(isinstance(x, str) for x in main):
        return [], [], "'main' phải là danh sách id câu lệnh mức ngoài cùng (theo thứ tự chạy)."

    # Mỗi câu lệnh xuất hiện ĐÚNG một lần trong toàn cây (main + các khối con).
    used: dict[str, int] = {}
    for sid in main:
        used[sid] = used.get(sid, 0) + 1
    for node in out:
        for key in ("then_body", "else_body", "body"):
            for sid in node[key]:
                used[sid] = used.get(sid, 0) + 1

    for sid, count in used.items():
        if sid not in by_id:
            return [], [], f"Tham chiếu tới câu lệnh '{sid}' không tồn tại."
        if count > 1:
            return [], [], f"Câu lệnh '{sid}' bị dùng ở {count} chỗ — mỗi câu lệnh chỉ thuộc một khối."
    orphan = sorted(set(by_id) - set(used))
    if orphan:
        return [], [], f"Câu lệnh không nằm trong chương trình: {', '.join(orphan)}."

    err = _check_nesting(main, by_id)
    if err:
        return [], [], err
    return out, list(main), None


def _check_nesting(main: list[str], by_id: dict[str, dict]) -> str | None:
    """Độ sâu lồng: thân của if/while ở mức ngoài cùng là độ sâu 1."""
    max_depth = LIMITS["max_nesting_depth"]

    def walk(ids: list[str], depth: int) -> str | None:
        for sid in ids:
            node = by_id[sid]
            children = [*node["then_body"], *node["else_body"], *node["body"]]
            if children:
                if depth + 1 > max_depth:
                    return (
                        f"Câu lệnh '{sid}' lồng sâu {depth + 1} tầng, vượt giới hạn "
                        f"{max_depth} tầng của mô phỏng."
                    )
                err = walk(children, depth + 1)
                if err:
                    return err
        return None

    return walk(main, 0)


# ── kiểu ────────────────────────────────────────────────────────────────────

def _check_types(statements: list[dict], expressions: list[dict], variables: list[dict]) -> str | None:
    var_types = {v["name"]: v["type"] for v in variables}
    by_id = {e["id"]: e for e in expressions}
    cache: dict[str, str] = {}

    def type_of(eid: str) -> tuple[str | None, str | None]:
        if eid in cache:
            return cache[eid], None
        node = by_id[eid]
        kind = node["kind"]

        if kind == "int":
            t = INTEGER
        elif kind == "bool":
            t = BOOLEAN
        elif kind == "var":
            t = var_types[node["name"]]
        elif kind == "unary":
            inner, err = type_of(node["operand"])
            if err:
                return None, err
            want = INTEGER if node["op"] == "-" else BOOLEAN
            if inner != want:
                return None, (
                    f"Toán tử '{node['op']}' ở '{eid}' cần {_TYPE_VI[want]}, "
                    f"nhưng nhận {_TYPE_VI[inner]}."
                )
            t = want
        else:
            lt, err = type_of(node["left"])
            if err:
                return None, err
            rt, err = type_of(node["right"])
            if err:
                return None, err

            if kind == "binary":
                if lt != INTEGER or rt != INTEGER:
                    return None, (
                        f"Phép '{node['op']}' ở '{eid}' chỉ dùng cho số nguyên "
                        f"(đang nhận {_TYPE_VI[lt]} và {_TYPE_VI[rt]})."
                    )
                if node["op"] in ("//", "%"):
                    right = by_id[node["right"]]
                    if right["kind"] == "int" and right["int_value"] == 0:
                        return None, f"Phép '{node['op']}' ở '{eid}' chia cho 0."
                t = INTEGER
            elif kind == "compare":
                if node["op"] in ORDER_COMPARE_OPS and (lt != INTEGER or rt != INTEGER):
                    return None, (
                        f"So sánh '{node['op']}' ở '{eid}' chỉ dùng cho số nguyên."
                    )
                if node["op"] in EQUALITY_OPS and lt != rt:
                    return None, (
                        f"So sánh '{node['op']}' ở '{eid}' cần hai vế cùng kiểu "
                        f"({_TYPE_VI[lt]} ≠ {_TYPE_VI[rt]}) — hệ không tự đổi kiểu."
                    )
                t = BOOLEAN
            else:  # logic
                if lt != BOOLEAN or rt != BOOLEAN:
                    return None, (
                        f"Phép '{node['op']}' ở '{eid}' cần hai vế đúng/sai "
                        f"(đang nhận {_TYPE_VI[lt]} và {_TYPE_VI[rt]})."
                    )
                t = BOOLEAN

        cache[eid] = t
        return t, None

    for st in statements:
        if st["kind"] == "assign":
            if st["target"] not in var_types:
                return (
                    f"Câu lệnh '{st['id']}' gán cho biến '{st['target']}' chưa khai báo. "
                    "Mọi biến phải có giá trị ban đầu trong 'variables'."
                )
            t, err = type_of(st["value"])
            if err:
                return err
            want = var_types[st["target"]]
            if t != want:
                return (
                    f"Biến '{st['target']}' là {_TYPE_VI[want]} nhưng câu lệnh "
                    f"'{st['id']}' gán {_TYPE_VI[t]} — hệ không tự đổi kiểu."
                )
        elif st["kind"] == "output":
            _, err = type_of(st["value"])
            if err:
                return err
        else:
            t, err = type_of(st["condition"])
            if err:
                return err
            if t != BOOLEAN:
                label = "rẽ nhánh" if st["kind"] == "if" else "vòng lặp"
                return (
                    f"Điều kiện của {label} '{st['id']}' phải là đúng/sai, "
                    f"đang là {_TYPE_VI[t]}."
                )
    return None


__all__ = ["validate_program_config"]
