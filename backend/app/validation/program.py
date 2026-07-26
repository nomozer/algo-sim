# -*- coding: utf-8 -*-
"""M17 W2C — Validator FAIL-CLOSED cho `algorithm.bounded_control_flow`.

Chạy TRƯỚC executor. Mọi từ vựng/giới hạn đọc từ `simulation/program_spec.py`
(một nguồn) — cấm magic number ở đây.

W2C-C1 §L2: bề mặt LLM là **biểu thức inline, nông, phi đệ quy**; validator gọi
`normalize_inline_program` (tất định) để đổi sang bảng biểu thức NỘI BỘ rồi kiểm
trên đó. LLM KHÔNG còn phải tự đặt id biểu thức và tự nối tham chiếu.

W2C-C1 §L1: biến được phép **khai báo mà chưa khởi tạo**. Hệ KHÔNG bịa 0/false/
null làm giá trị mặc định; thay vào đó có một lượt phân tích *definite
assignment* — đọc biến chưa chắc chắn có giá trị là TỪ CHỐI.

KHÔNG coercion: `"5"` không thành `5`, `true` không thành `1`, `1` không thành
`true`. Sai kiểu là TỪ CHỐI, không phải "đoán ý".
"""
from __future__ import annotations

import re

from app.simulation.program_spec import (
    EQUALITY_OPS,
    FORBIDDEN_SPEC_KEYS,
    INT_MAX,
    INT_MIN,
    LIMITS,
    NormalizeError,
    ORDER_COMPARE_OPS,
    SPEC_VERSION,
    VALUE_TYPES,
    VARIABLE_NAME_MAX_LEN,
    normalize_inline_program,
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
            "Chỉ mô tả chương trình (biến + câu lệnh); engine tự chạy."
        )

    version = raw.get("program_version") or SPEC_VERSION
    if version != SPEC_VERSION:
        return _err(f"program_version phải là '{SPEC_VERSION}'.")

    variables, err = _check_variables(raw.get("variables"))
    if err:
        return _err(err)

    # §L2 — inline → nội bộ, TẤT ĐỊNH. Sai ngữ pháp thì dừng ngay tại đây.
    try:
        expressions, statements_raw = normalize_inline_program(raw.get("statements"))
    except NormalizeError as e:
        return _err(str(e))

    known = {v["name"] for v in variables}
    for node in expressions:
        if node["kind"] == "var" and node["name"] not in known:
            return _err(
                f"Chương trình dùng biến '{node['name']}' chưa được khai báo. "
                "Mọi biến phải có mặt trong 'variables'."
            )

    statements, main, err = _check_statements(statements_raw, raw.get("main"))
    if err:
        return _err(err)

    err = _check_expression_depth(expressions)
    if err:
        return _err(err)

    err = _check_types(statements, expressions, variables)
    if err:
        return _err(err)

    # §L1 — đọc biến chưa chắc chắn có giá trị là TỪ CHỐI.
    err = _check_definite_assignment(statements, main, expressions, variables)
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


# ── biến: KHAI BÁO ≠ KHỞI TẠO (§L1) ─────────────────────────────────────────

def _check_variables(raw) -> tuple[list[dict], str | None]:
    if not isinstance(raw, list) or not raw:
        return [], "Cần ít nhất một biến trong 'variables'."
    if len(raw) > LIMITS["max_variables"]:
        return [], f"Tối đa {LIMITS['max_variables']} biến, đề đang có {len(raw)}."

    out: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            return [], "Mỗi biến phải là một đối tượng {name, type, int_value?|bool_value?}."
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
        # §L1: CẢ HAI để trống ⇒ biến ĐƯỢC KHAI BÁO nhưng CHƯA KHỞI TẠO.
        # Hệ KHÔNG bịa 0/false thay đề — đề "nếu x>0 thì y=1 ngược lại y=-1"
        # vốn không hề nói y ban đầu bằng mấy.
        if iv is None and bv is None:
            out.append({"name": name, "type": vtype,
                        "int_value": None, "bool_value": None, "initialized": False})
            continue

        if vtype == INTEGER:
            if not _is_int(iv):
                return [], f"Biến '{name}' khai kiểu số nguyên nên 'int_value' phải là số nguyên."
            if bv is not None:
                return [], f"Biến '{name}' là số nguyên thì 'bool_value' phải để trống."
            if not (INT_MIN <= iv <= INT_MAX):
                return [], f"Giá trị của '{name}' phải trong khoảng {INT_MIN}..{INT_MAX}."
            out.append({"name": name, "type": INTEGER, "int_value": iv,
                        "bool_value": None, "initialized": True})
        else:
            if not _is_bool(bv):
                return [], f"Biến '{name}' khai kiểu đúng/sai nên 'bool_value' phải là true/false."
            if iv is not None:
                return [], f"Biến '{name}' là đúng/sai thì 'int_value' phải để trống."
            out.append({"name": name, "type": BOOLEAN, "int_value": None,
                        "bool_value": bv, "initialized": True})
    return out, None


# ── biểu thức nội bộ ────────────────────────────────────────────────────────

def _check_expression_depth(nodes: list[dict]) -> str | None:
    """Lưới an toàn của biểu diễn NỘI BỘ (ngữ pháp inline đã đảm bảo độ nông)."""
    by_id = {n["id"]: n for n in nodes}
    depth: dict[str, int] = {}

    def walk(eid: str) -> int:
        if eid in depth:
            return depth[eid]
        node = by_id[eid]
        children = [node[k] for k in ("operand", "left", "right") if node.get(k) is not None]
        d = 1 + max((walk(c) for c in children), default=0)
        depth[eid] = d
        return d

    for node in nodes:
        if walk(node["id"]) > LIMITS["max_expression_depth"]:
            return (f"Biểu thức lồng quá {LIMITS['max_expression_depth']} tầng — "
                    "hãy tách bớt ra câu lệnh trung gian.")
    return None


def _vars_read(eid: str, by_id: dict[str, dict]) -> set[str]:
    node = by_id[eid]
    if node["kind"] == "var":
        return {node["name"]}
    out: set[str] = set()
    for k in ("operand", "left", "right"):
        if node.get(k) is not None:
            out |= _vars_read(node[k], by_id)
    return out


# ── câu lệnh ────────────────────────────────────────────────────────────────

def _check_statements(raw: list[dict], main) -> tuple[list[dict], list[str], str | None]:
    if not raw:
        return [], [], "Cần ít nhất một câu lệnh trong 'statements'."
    if len(raw) > LIMITS["max_statement_nodes"]:
        return [], [], (
            f"Chương trình có {len(raw)} câu lệnh, vượt giới hạn "
            f"{LIMITS['max_statement_nodes']} câu lệnh của mô phỏng."
        )

    out: list[dict] = []
    ids: set[str] = set()
    for item in raw:
        sid = item.get("id")
        if not isinstance(sid, str) or not sid.strip():
            return [], [], "Mỗi câu lệnh phải có 'id' không rỗng."
        if sid in ids:
            return [], [], f"Câu lệnh trùng id: '{sid}'."
        ids.add(sid)
        kind = item["kind"]
        node = {"id": sid, "kind": kind, "target": item.get("target"),
                "value": item.get("value"), "condition": item.get("condition"),
                "then_body": [], "else_body": [], "body": [], "max_iterations": None}
        if kind == "assign":
            if not isinstance(item.get("target"), str):
                return [], [], f"Câu lệnh gán '{sid}' cần 'target' là tên biến."
        elif kind == "if":
            for key in ("then_body", "else_body"):
                block = item.get(key) or []
                if not isinstance(block, list) or not all(isinstance(x, str) for x in block):
                    return [], [], f"'{key}' của '{sid}' phải là danh sách id câu lệnh."
                node[key] = list(block)
            if not node["then_body"]:
                return [], [], f"Câu lệnh rẽ nhánh '{sid}' phải có ít nhất một câu lệnh ở nhánh đúng."
        elif kind == "while":
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
    max_depth = LIMITS["max_nesting_depth"]

    def walk(ids: list[str], depth: int) -> str | None:
        for sid in ids:
            node = by_id[sid]
            children = [*node["then_body"], *node["else_body"], *node["body"]]
            if children:
                if depth + 1 > max_depth:
                    return (f"Câu lệnh '{sid}' lồng sâu {depth + 1} tầng, vượt giới hạn "
                            f"{max_depth} tầng của mô phỏng.")
                err = walk(children, depth + 1)
                if err:
                    return err
        return None

    return walk(main, 0)


# ── §L1 — DEFINITE ASSIGNMENT ───────────────────────────────────────────────

def _check_definite_assignment(statements, main, expressions, variables) -> str | None:
    """Biến chỉ được ĐỌC khi CHẮC CHẮN đã có giá trị tại đúng điểm đó.

    Luật (đúng phạm vi ngữ pháp hiện tại, KHÔNG dựng CFG tổng quát):
    - tuần tự: gán vào v ⇒ v vào tập đã-khởi-tạo;
    - if/else: giao của hai nhánh (cả hai cùng gán thì mới chắc chắn);
    - if không else: KHÔNG mở rộng (nhánh then có thể không chạy);
    - while: KHÔNG mở rộng (vòng lặp có thể chạy 0 lượt).
    """
    by_stmt = {s["id"]: s for s in statements}
    by_expr = {e["id"]: e for e in expressions}
    error: list[str] = []

    def reads(eid: str) -> set[str]:
        return _vars_read(eid, by_expr)

    def check_read(eid: str, init: set[str], where: str) -> None:
        if error:
            return
        missing = sorted(reads(eid) - init)
        if missing:
            error.append(
                f"{where} đọc biến {', '.join(repr(m) for m in missing)} khi biến đó "
                "chưa chắc chắn có giá trị. Hãy gán giá trị cho biến trước khi dùng "
                "(hoặc cho nó giá trị ban đầu)."
            )

    def walk(ids: list[str], init: set[str]) -> set[str]:
        cur = set(init)
        for sid in ids:
            if error:
                return cur
            st = by_stmt[sid]
            if st["kind"] == "assign":
                check_read(st["value"], cur, f"Câu lệnh gán '{sid}'")
                cur.add(st["target"])
            elif st["kind"] == "output":
                check_read(st["value"], cur, f"Câu lệnh hiển thị '{sid}'")
            elif st["kind"] == "if":
                check_read(st["condition"], cur, f"Điều kiện của '{sid}'")
                after_then = walk(st["then_body"], cur)
                if st["else_body"]:
                    after_else = walk(st["else_body"], cur)
                    cur = after_then & after_else      # chỉ chắc khi CẢ HAI cùng gán
                # không else ⇒ giữ nguyên `cur`: nhánh then có thể không chạy
            else:  # while — có thể chạy 0 lượt
                check_read(st["condition"], cur, f"Điều kiện của vòng lặp '{sid}'")
                walk(st["body"], cur)                  # kiểm bên trong, KHÔNG mở rộng
        return cur

    walk(main, {v["name"] for v in variables if v["initialized"]})
    return error[0] if error else None


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
                return None, (f"Toán tử '{node['op']}' cần {_TYPE_VI[want]}, "
                              f"nhưng nhận {_TYPE_VI[inner]}.")
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
                    return None, (f"Phép '{node['op']}' chỉ dùng cho số nguyên "
                                  f"(đang nhận {_TYPE_VI[lt]} và {_TYPE_VI[rt]}).")
                if node["op"] in ("//", "%"):
                    right = by_id[node["right"]]
                    if right["kind"] == "int" and right["int_value"] == 0:
                        return None, f"Phép '{node['op']}' chia cho 0."
                t = INTEGER
            elif kind == "compare":
                if node["op"] in ORDER_COMPARE_OPS and (lt != INTEGER or rt != INTEGER):
                    return None, f"So sánh '{node['op']}' chỉ dùng cho số nguyên."
                if node["op"] in EQUALITY_OPS and lt != rt:
                    return None, (f"So sánh '{node['op']}' cần hai vế cùng kiểu "
                                  f"({_TYPE_VI[lt]} ≠ {_TYPE_VI[rt]}) — hệ không tự đổi kiểu.")
                t = BOOLEAN
            else:  # logic
                if lt != BOOLEAN or rt != BOOLEAN:
                    return None, (f"Phép '{node['op']}' cần hai vế đúng/sai "
                                  f"(đang nhận {_TYPE_VI[lt]} và {_TYPE_VI[rt]}).")
                t = BOOLEAN

        cache[eid] = t
        return t, None

    for st in statements:
        if st["kind"] == "assign":
            if st["target"] not in var_types:
                return (f"Câu lệnh '{st['id']}' gán cho biến '{st['target']}' chưa khai báo. "
                        "Mọi biến phải có mặt trong 'variables'.")
            t, err = type_of(st["value"])
            if err:
                return err
            want = var_types[st["target"]]
            if t != want:
                return (f"Biến '{st['target']}' là {_TYPE_VI[want]} nhưng câu lệnh "
                        f"'{st['id']}' gán {_TYPE_VI[t]} — hệ không tự đổi kiểu.")
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
                return (f"Điều kiện của {label} '{st['id']}' phải là đúng/sai, "
                        f"đang là {_TYPE_VI[t]}.")
    return None


__all__ = ["validate_program_config"]
