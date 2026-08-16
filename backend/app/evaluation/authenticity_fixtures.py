# -*- coding: utf-8 -*-
"""M17-Lite W0 — fixture audit authenticity: kịch bản per-target + control.

DATA THUẦN (không import pytest, không network). Mỗi AI-reachable target khai
một ``TargetFixture`` gồm đề bài VI + kịch bản provider cho 3–4 archetype
(direct / paraphrase / changed_input / boundary). Control fixture gồm:
near-miss (mỗi cơ chế INTENTIONAL_GAP đúng MỘT case), leak-control,
refusal-control, và 2 case regression duyệt cây (honest + adversarial probe).

Tái dùng builder của ``m16_offline_scripts`` (import tên "_private" CÓ CHỦ
ĐÍCH — đó là nguồn duy nhất về SHAPE kịch bản đúng schema production đã
live-proven; copy lại = tạo nguồn sự thật thứ hai, vi phạm anti-pattern #1;
module m16 giữ nguyên 0 diff). Case matrix KHÔNG hard-code theo test ID:
``authenticity_matrix.build_audit_cases`` duyệt CATALOG thật — target mới
thiếu fixture sẽ đỏ ở lock, không lặng lẽ bị bỏ qua.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.evaluation.m16_offline_scripts import (  # noqa: F401 — tái dùng có chủ đích
    CaseScript,
    build_scripted_provider,
    _algo_cfg,
    _analysis,
    _AND3_GATE,
    _binary_cfg,
    _classify,
    _encap_cfg,
    _j,
    _logic_cfg,
    _MOVING_PATH,
    _net_cfg,
    _scan_cfg,
    _sort_spec,
    _STATION_REVEAL,
    _TRIANGLE_REVEAL,
)

_TOKEN = "algorithm.comparison_sort"
_GENERIC = "generic.rule_scene"
_BINARY = "binary.decimal_to_binary"

# bề mặt analyze-exposed THẬT (bare legacy sorting + positional namespaced)
_P_ADJ = "adjacent_compare_swap"
_P_SHIFT = "shift_into_sorted_prefix"
_P_SELECT = "select_extreme_repeated"
_P_PARTITION = "partition_recursive"
_P_OTHER = "other_unspecified"
_P_BINW = "positional_representation.binary_positional_weights"
_P_NONBIN = "positional_representation.non_binary_base"
_P_RGB = "positional_representation.rgb_channel_composition"

OK_ARCHETYPES = ("direct", "paraphrase", "changed_input", "boundary")


def _web_cfg(heading: str, paragraph: str = "", **style: object) -> str:
    """Config web.style_model (W4B-2Z) — đúng schema validator BE.

    `style` chỉ nhận khoá thuộc tập ĐÓNG; fixture truyền khoá lạ sẽ bị chính
    validator production chặn (fixture không có đường vòng riêng)."""
    return _j({"heading": heading, "paragraph": paragraph, "style": style, "notes": None})


def _baseconv_cfg(source: int, target: int, value: str) -> str:
    """Config binary.base_conversion (M17 W1) — đúng schema validator BE."""
    return _j({"sourceBase": source, "targetBase": target, "inputValue": value})


def _color_cfg(red: int, green: int, blue: int) -> str:
    """Config color.rgb_model (W5A) — đúng schema validator BE."""
    return _j({"red": red, "green": green, "blue": blue})


def _booldag_cfg(inputs: list, gates: list, output: str) -> str:
    """Config logic.boolean_dag (M17 W1) — đúng schema validator BE."""
    return _j({"inputs": inputs, "gates": gates, "output": output})


def _traverse_cfg(nodes: list, edges: list, start: str, variant: str,
                  goal: str | None = None, directed: bool = False) -> str:
    """Config network.graph_traversal (M17 W1) — đúng schema validator BE."""
    cfg: dict = {
        "nodes": [{"id": n} for n in nodes],
        "edges": edges,
        "start": start,
        "variant": variant,
        "directed": directed,
    }
    if goal is not None:
        cfg["goal"] = goal
    return _j(cfg)


def _table_cfg(schema, rows, **q) -> str:
    """Config database.relational_table_query (M17 W2B) — đúng schema validator."""
    cfg = {"specVersion": "table-1.0", "schema": schema, "rows": rows}
    cfg.update({k: v for k, v in q.items() if v is not None})
    return _j(cfg)


def _tree_cfg(variant: str, root: str, nodes: list) -> str:
    """Config tree.traversal (M17 W2A) — nodes = list [id, left|None, right|None]."""
    return _j({
        "specVersion": "tree-1.0",
        "variant": variant,
        "rootId": root,
        "nodes": [{"id": i, "label": i, "left": l, "right": r} for (i, l, r) in nodes],
    })


# Cây chuẩn A(B(D,E), C(F,G)) tái dùng cho fixture tree.
_TREE_ABC = [
    ("A", "B", "C"), ("B", "D", "E"), ("C", "F", "G"),
    ("D", None, None), ("E", None, None), ("F", None, None), ("G", None, None),
]
# analyze THẬT của đề cây có cấu trúc: nút cụ thể + quan hệ trái/phải → qua
# structure gate (M17 W2A). Đề THIẾU cấu trúc thì KHÔNG có các trường này.
_TREE_NODE_OBJECTS = ["A", "B", "C", "D", "E", "F", "G"]
_TREE_RELATIONS = [
    {"type": "left_child", "from": "A", "to": "B"},
    {"type": "right_child", "from": "A", "to": "C"},
]


@dataclass(frozen=True)
class TargetFixture:
    """Kịch bản audit cho MỘT target: archetype → (đề VI, CaseScript).
    ``expected_route`` mặc định = chính sim_id (sorting: concrete id sau
    selector resolve — vẫn chính sim_id vì audit gắn fixture theo target)."""

    prompts: dict[str, str]
    scripts: dict[str, CaseScript]


@dataclass(frozen=True)
class ControlFixture:
    """Case kiểm soát: near-miss gap / leak-control / refusal / probe."""

    case_id: str
    kind: str  # "near_miss" | "leak_control" | "refusal_control" | "leak_probe"
    prompt: str
    script: CaseScript
    mechanism: str | None = None
    expected_status: str = "unsupported"
    # Route kỳ vọng khi expected_status=="ok"; None → mặc định generic.rule_scene
    # (đối chứng representation). Case đóng regression tree đặt "tree.traversal".
    expected_route: str | None = None
    note: str = ""
    # M17-RC1 §C — case control KHÔNG gắn với target nào qua `kind` (một
    # refusal_control có thể là "thiếu dữ kiện" hoặc "biến thể ngoài năng lực").
    # Hai trường METADATA thuần dưới đây khai TƯỜNG MINH nó chứng minh slot nào
    # cho target nào, để ma trận §C khỏi phải đoán từ `kind`. Mặc định None ⇒
    # case cũ không đổi hành vi, artifact W0/W1 không đổi (artifact chỉ
    # serialize AuditRecord, không serialize fixture).
    audit_slot: str | None = None
    audit_target: str | None = None


# M17-RC1 §C2 — analyze THẬT của các đề này LUÔN liệt kê đỉnh/cạnh (hoặc đầu
# vào/cổng), vì đề nêu rõ chúng. Stub cũ để objects=["đối tượng"], relations=[]
# nên trông như đề KHÔNG cho cấu trúc → cổng đủ-dữ-kiện chặn oan 11 case.
_DAG_OBJECTS = ["đầu vào A", "đầu vào B", "đầu vào C", "cổng AND", "cổng OR", "cổng NOT"]
_DAG_REL = ["A và B vào cổng AND", "kết quả AND và NOT C vào cổng OR"]
_GRAPH_OBJECTS = ["đỉnh A", "đỉnh B", "đỉnh C", "đỉnh D", "đỉnh E"]
_GRAPH_REL = ["A nối B", "A nối C", "B nối D", "C nối D", "D nối E"]
_NET_OBJECTS = ["máy tính", "switch", "router", "ISP", "máy chủ"]
_NET_REL = ["máy tính nối switch", "switch nối router", "router nối ISP", "ISP nối máy chủ"]


# M17 W2B — bảng học sinh dùng chung cho fixture truy vấn bảng.
_TB_SCHEMA = [
    {"name": "ten", "type": "text"}, {"name": "diem", "type": "number"},
    {"name": "to", "type": "text"},
]
_TB_ROWS = [
    {"ten": "An", "diem": 8.5, "to": "A"}, {"ten": "Bình", "diem": 6.0, "to": "B"},
    {"ten": "Chi", "diem": 9.0, "to": "A"}, {"ten": "Dũng", "diem": 6.0, "to": "C"},
    {"ten": "Hà", "diem": 7.25, "to": "B"},
]
_TB_OBJECTS = ["bảng điểm học sinh", "cột Tên", "cột Điểm", "cột Tổ"]
_TB_DATA = [
    {"description": "điểm các bạn", "values": [8.5, 6.0, 9.0, 6.0, 7.25],
     "labels": ["An", "Bình", "Chi", "Dũng", "Hà"]},
    {"description": "tổ của các bạn", "labels": ["A", "B", "A", "C", "B"]},
]


# M17 W2C — chương trình hữu hạn. analyze THẬT của đề "cho x = 3, tính y = x*2+1"
# luôn nêu tên biến (objects) và giá trị ban đầu (data.values); fixture phản ánh
# đúng thế để cổng đủ-dữ-kiện không chặn oan.
_PG_OBJECTS = ["biến x", "biến y"]
_PG_DATA = [{"description": "giá trị ban đầu và hằng số trong chương trình",
             "values": [3, 2, 1]}]


# W2C-C1: bề mặt LLM là biểu thức INLINE (không còn bảng expressions + id).
def _pv(n):   return {"kind": "int", "int_value": n}
def _pb(b):   return {"kind": "bool", "bool_value": b}
def _pvar(n): return {"kind": "var", "name": n}
def _val(left, op=None, right=None):
    v = {"left": left}
    if op is not None:
        v["op"] = op
        v["right"] = right
    return v
def _cond(atoms, op=None):
    c = {"atoms": atoms}
    if op is not None:
        c["op"] = op
    return c
def _atom(left, op=None, right=None, negated=False):
    a = {"left": left}
    if op is not None:
        a["op"] = op
        a["right"] = right
    if negated:
        a["negated"] = True
    return a
def _prog(variables, statements, main):
    return _j({"program_version": "program-2.0", "variables": variables,
               "statements": statements, "main": main})


def _program_cfg_assign() -> str:
    """x = 3 ; tich = x*2 ; y = tich + 1  →  y = 7.

    Biểu thức nhiều tầng tách thành CÂU LỆNH TRUNG GIAN — đúng luật C1 §L2 (giữ
    ngữ pháp đóng thay vì mở AST đệ quy)."""
    return _prog(
        [{"name": "x", "type": "integer", "int_value": 3},
         {"name": "tich", "type": "integer"},
         {"name": "y", "type": "integer"}],
        [{"id": "s1", "kind": "assign", "target": "tich",
          "value": _val(_pvar("x"), "*", _pv(2))},
         {"id": "s2", "kind": "assign", "target": "y",
          "value": _val(_pvar("tich"), "+", _pv(1))}],
        ["s1", "s2"],
    )


def _program_cfg_branch() -> str:
    """x = -2 ; nếu x > 0 thì y = 1 ngược lại y = -1  →  y = -1.
    `y` KHAI BÁO mà CHƯA khởi tạo — đề không hề nói y ban đầu bằng mấy."""
    return _prog(
        [{"name": "x", "type": "integer", "int_value": -2},
         {"name": "y", "type": "integer"}],
        [{"id": "s_then", "kind": "assign", "target": "y", "value": _val(_pv(1))},
         {"id": "s_else", "kind": "assign", "target": "y", "value": _val(_pv(-1))},
         {"id": "s_if", "kind": "if",
          "condition": _cond([_atom(_val(_pvar("x")), ">", _val(_pv(0)))]),
          "then_body": ["s_then"], "else_body": ["s_else"]}],
        ["s_if"],
    )


def _program_cfg_loop() -> str:
    """x = 1 ; trong khi x < 5 thì x = x + 1  →  x = 5, lặp 4 lượt."""
    return _prog(
        [{"name": "x", "type": "integer", "int_value": 1}],
        [{"id": "s_body", "kind": "assign", "target": "x",
          "value": _val(_pvar("x"), "+", _pv(1))},
         {"id": "s_while", "kind": "while",
          "condition": _cond([_atom(_val(_pvar("x")), "<", _val(_pv(5)))]),
          "body": ["s_body"], "max_iterations": 10}],
        ["s_while"],
    )


def _program_cfg_boolean() -> str:
    """a = true, b = false ; nếu a và không b thì x = 1 ngược lại x = 0  →  x = 1."""
    return _prog(
        [{"name": "a", "type": "boolean", "bool_value": True},
         {"name": "b", "type": "boolean", "bool_value": False},
         {"name": "x", "type": "integer"}],
        [{"id": "s_then", "kind": "assign", "target": "x", "value": _val(_pv(1))},
         {"id": "s_else", "kind": "assign", "target": "x", "value": _val(_pv(0))},
         {"id": "s_if", "kind": "if",
          "condition": _cond([_atom(_val(_pvar("a"))),
                              _atom(_val(_pvar("b")), negated=True)], op="and"),
          "then_body": ["s_then"], "else_body": ["s_else"]}],
        ["s_if"],
    )


# M17 W3 — mã hoá ký tự. analyze THẬT của đề "mã ASCII của chữ A" nêu ký tự
# trong dấu nháy và tên bảng mã; fixture phản ánh đúng thế để cổng đủ-dữ-kiện
# không chặn oan.
_CE_OBJECTS = ["ký tự 'A'", "bảng mã ASCII"]


def _charenc_cfg(text: str, encoding: str) -> str:
    """Config binary.character_encoding — đúng schema validator BE."""
    return _j({"spec_version": "charenc-1.0", "text": text, "encoding": encoding})


# ══════════════ fixture per-target (14 AI-reachable) ══════════════
TARGET_FIXTURES: dict[str, TargetFixture] = {
    "database.relational_table_query": TargetFixture(
        prompts={
            "direct": "Bảng điểm: An 8.5 tổ A, Bình 6.0 tổ B, Chi 9.0 tổ A, Dũng 6.0 tổ C, Hà 7.25 tổ B. Lọc ra những bạn có điểm trên 7 và hiển thị tên cùng điểm.",
            "paraphrase": "Cho danh sách nhân viên với cột Tên, Điểm, Tổ như trên. Hãy sắp xếp giảm dần theo điểm rồi lấy 3 người đầu.",
            "changed_input": "Với bảng điểm đó, có bao nhiêu bạn thuộc tổ A?",
            "boundary": "Với bảng điểm đó, điểm trung bình của các bạn có điểm từ 7 trở lên là bao nhiêu?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(objects=_TB_OBJECTS, data=_TB_DATA, goal="Lọc học sinh điểm trên 7"),
                [_classify("database.relational_table_query")],
                [_table_cfg(_TB_SCHEMA, _TB_ROWS,
                            filter={"op": ">", "column": "diem", "value": 7},
                            projection=["ten", "diem"])],
            ),
            "paraphrase": CaseScript(
                _analysis(objects=_TB_OBJECTS, data=_TB_DATA, goal="Sắp xếp giảm dần lấy 3 đầu"),
                [_classify("database.relational_table_query")],
                [_table_cfg(_TB_SCHEMA, _TB_ROWS,
                            sort={"column": "diem", "direction": "desc"}, limit=3)],
            ),
            "changed_input": CaseScript(
                _analysis(objects=_TB_OBJECTS, data=_TB_DATA, goal="Đếm học sinh tổ A"),
                [_classify("database.relational_table_query")],
                [_table_cfg(_TB_SCHEMA, _TB_ROWS,
                            filter={"op": "=", "column": "to", "value": "A"},
                            aggregate={"func": "count"})],
            ),
            "boundary": CaseScript(
                _analysis(objects=_TB_OBJECTS, data=_TB_DATA, goal="Điểm trung bình nhóm ≥7"),
                [_classify("database.relational_table_query")],
                [_table_cfg(_TB_SCHEMA, _TB_ROWS,
                            filter={"op": ">=", "column": "diem", "value": 7},
                            aggregate={"func": "avg", "column": "diem"})],
            ),
        },
    ),
    "algorithm.find_max": TargetFixture(
        prompts={
            "direct": "Cho dãy số 12, 7, 25, 9, 18. Tìm phần tử lớn nhất.",
            "paraphrase": "Bốn bạn có chiều cao 165, 172, 158, 180 cm. Ai cao nhất?",
            "changed_input": "Cho dãy 4, 9, 1, 16, 7, 3. Giá trị lớn nhất là bao nhiêu?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm phần tử lớn nhất"),
                [_classify("algorithm.find_max")],
                [_algo_cfg([12, 7, 25, 9, 18], summary="Tìm giá trị lớn nhất")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm người cao nhất"),
                [_classify("algorithm.find_max")],
                [_algo_cfg([165, 172, 158, 180], summary="Tìm giá trị lớn nhất")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm giá trị lớn nhất của dãy khác"),
                [_classify("algorithm.find_max")],
                [_algo_cfg([4, 9, 1, 16, 7, 3], summary="Tìm giá trị lớn nhất")],
            ),
        },
    ),
    "algorithm.find_min": TargetFixture(
        prompts={
            "direct": "Cho dãy 45, 12, 78, 6, 33. Tìm phần tử nhỏ nhất.",
            "paraphrase": "Nhiệt độ các ngày là 18, 15, 21, 12, 19 độ. Ngày nào lạnh nhất?",
            "changed_input": "Cho dãy 7, 3, 11, 2, 9, 5. Số nhỏ nhất là số nào?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm phần tử nhỏ nhất"),
                [_classify("algorithm.find_min")],
                [_algo_cfg([45, 12, 78, 6, 33], summary="Tìm giá trị nhỏ nhất")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm ngày lạnh nhất"),
                [_classify("algorithm.find_min")],
                [_algo_cfg([18, 15, 21, 12, 19], summary="Tìm giá trị nhỏ nhất")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm giá trị nhỏ nhất của dãy khác"),
                [_classify("algorithm.find_min")],
                [_algo_cfg([7, 3, 11, 2, 9, 5], summary="Tìm giá trị nhỏ nhất")],
            ),
        },
    ),
    "algorithm.sum_if": TargetFixture(
        prompts={
            "direct": "Cho dãy 6, 11, 4, 9, 15, 3. Tính tổng các số lớn hơn 5.",
            "paraphrase": "Các khoản chi 20, 50, 10, 80, 35 nghìn. Cộng những khoản từ 30 nghìn trở lên.",
            "changed_input": "Cho dãy 2, 14, 8, 5, 20. Tổng các số lớn hơn 7 là bao nhiêu?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tính tổng các số lớn hơn 5"),
                [_classify("algorithm.sum_if")],
                [_algo_cfg([6, 11, 4, 9, 15, 3], condition={"op": ">", "value": 5}, summary="Tổng theo điều kiện")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Cộng dồn các khoản lớn"),
                [_classify("algorithm.sum_if")],
                [_algo_cfg([20, 50, 10, 80, 35], condition={"op": ">=", "value": 30}, summary="Tổng theo điều kiện")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tổng các số lớn hơn 7"),
                [_classify("algorithm.sum_if")],
                [_algo_cfg([2, 14, 8, 5, 20], condition={"op": ">", "value": 7}, summary="Tổng theo điều kiện")],
            ),
        },
    ),
    "algorithm.count_if": TargetFixture(
        prompts={
            "direct": "Điểm của lớp: 6, 8.5, 7, 9, 5.5, 8. Đếm số bạn đạt từ 8 trở lên.",
            "paraphrase": "Nhiệt độ tủ ghi 3, 6, 2, 8, 5, 7. Bao nhiêu lần tủ vượt 4 độ?",
            "changed_input": "Cho dãy 10, 3, 12, 7, 15, 2. Đếm các số nhỏ hơn 8.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đếm số bạn đạt từ 8 trở lên"),
                [_classify("algorithm.count_if")],
                [_algo_cfg([6, 8.5, 7, 9, 5.5, 8], condition={"op": ">=", "value": 8}, summary="Đếm theo điều kiện")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Đếm số lần tủ quá ấm"),
                [_classify("algorithm.count_if")],
                [_algo_cfg([3, 6, 2, 8, 5, 7], condition={"op": ">", "value": 4}, summary="Đếm theo điều kiện")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Đếm các số nhỏ hơn 8"),
                [_classify("algorithm.count_if")],
                [_algo_cfg([10, 3, 12, 7, 15, 2], condition={"op": "<", "value": 8}, summary="Đếm theo điều kiện")],
            ),
        },
    ),
    "algorithm.linear_search": TargetFixture(
        prompts={
            "direct": "Cho danh sách 305, 118, 227, 194, 260. Tìm xem 194 có trong danh sách không.",
            "paraphrase": "Duyệt lần lượt các mã 71, 34, 90, 12, 58 để tìm mã 90.",
            "changed_input": "Tìm số 42 trong dãy 15, 42, 8, 23, 4 bằng cách xét từng phần tử.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm 194 trong danh sách"),
                [_classify("algorithm.linear_search")],
                [_algo_cfg([305, 118, 227, 194, 260], target=194, summary="Tìm kiếm tuần tự")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm mã 90"),
                [_classify("algorithm.linear_search")],
                [_algo_cfg([71, 34, 90, 12, 58], target=90, summary="Tìm kiếm tuần tự")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm 42 bằng duyệt tuần tự"),
                [_classify("algorithm.linear_search")],
                [_algo_cfg([15, 42, 8, 23, 4], target=42, summary="Tìm kiếm tuần tự")],
            ),
        },
    ),
    "algorithm.binary_search": TargetFixture(
        prompts={
            "direct": "Dãy đã sắp 3, 8, 15, 22, 30, 41, 55. Tìm 30 bằng tìm kiếm nhị phân.",
            "paraphrase": "Tìm 203 trong dãy tăng dần 101, 145, 178, 203, 256 bằng cách xét phần tử giữa.",
            "changed_input": "Dãy 2, 5, 9, 14, 21, 30 đã sắp xếp. Dùng chia đôi để tìm 17.",
            "boundary": "Cho dãy CHƯA sắp 27, 4, 51, 13, 38, 9. Tìm 38 bằng tìm kiếm nhị phân.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm 30 bằng chia đôi"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([3, 8, 15, 22, 30, 41, 55], target=30, summary="Tìm kiếm nhị phân")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm 203 bằng cách xét phần tử giữa"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([101, 145, 178, 203, 256], target=203, summary="Tìm kiếm nhị phân")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm 17 (vắng mặt) bằng chia đôi"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([2, 5, 9, 14, 21, 30], target=17, summary="Tìm kiếm nhị phân")],
            ),
            # M15 policy: input chưa sắp → normalize-not-refuse (validator tự sắp)
            "boundary": CaseScript(
                _analysis(goal="Tìm 38 bằng chia đôi trên dãy chưa sắp"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([27, 4, 51, 13, 38, 9], target=38, summary="Tìm kiếm nhị phân")],
            ),
        },
    ),
    "algorithm.bubble_sort": TargetFixture(
        prompts={
            "direct": "Sắp xếp dãy 9, 4, 7, 2, 6 tăng dần bằng thuật toán nổi bọt.",
            "paraphrase": "Sắp xếp 8, 3, 6, 1 bằng cách so sánh và đổi chỗ hai phần tử kề nhau.",
            "changed_input": "Dùng nổi bọt sắp xếp dãy 5, 1, 4, 2, 8 theo thứ tự tăng.",
            "boundary": "Sắp xếp dãy có phần tử trùng 5, 3, 5, 2, 3 bằng nổi bọt.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Sắp xếp tăng dần bằng nổi bọt", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [9, 4, 7, 2, 6])],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Sắp xếp bằng đổi chỗ cặp kề", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [8, 3, 6, 1])],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Sắp xếp dãy khác bằng nổi bọt", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [5, 1, 4, 2, 8])],
            ),
            "boundary": CaseScript(
                _analysis(goal="Sắp xếp dãy có phần tử trùng", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [5, 3, 5, 2, 3])],
            ),
        },
    ),
    "algorithm.insertion_sort": TargetFixture(
        prompts={
            "direct": "Sắp xếp dãy 7, 2, 9, 4, 5 bằng thuật toán sắp xếp chèn.",
            "paraphrase": "Chèn từng lá bài 6, 2, 8, 3, 5 vào phần đã sắp xếp bên trái.",
            "changed_input": "Dùng sắp xếp chèn cho dãy 10, 6, 3, 8, 1.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Sắp xếp tăng dần bằng chèn", prescribed=_P_SHIFT),
                [_classify(_TOKEN)],
                [_sort_spec("insertion", [7, 2, 9, 4, 5])],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Chèn từng lá bài vào phần đã sắp", prescribed=_P_SHIFT),
                [_classify(_TOKEN)],
                [_sort_spec("insertion", [6, 2, 8, 3, 5])],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Sắp xếp chèn dãy khác", prescribed=_P_SHIFT),
                [_classify(_TOKEN)],
                [_sort_spec("insertion", [10, 6, 3, 8, 1])],
            ),
        },
    ),
    # M17 W1 — Selection Sort (route qua token comparison_sort, variant "selection")
    "algorithm.selection_sort": TargetFixture(
        prompts={
            "direct": "Sắp xếp dãy 9, 2, 7, 4 bằng thuật toán sắp xếp chọn (selection sort).",
            "paraphrase": "Sắp xếp 6, 1, 8, 3, 5 bằng cách mỗi lượt tìm phần tử nhỏ nhất còn lại rồi đưa lên đầu.",
            "changed_input": "Dùng sắp xếp chọn cho dãy 12, 5, 9, 3 theo thứ tự giảm dần.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Sắp xếp bằng chọn cực trị lặp", prescribed=_P_SELECT),
                [_classify(_TOKEN)],
                [_sort_spec("selection", [9, 2, 7, 4])],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Mỗi lượt tìm phần tử nhỏ nhất đưa lên đầu", prescribed=_P_SELECT),
                [_classify(_TOKEN)],
                [_sort_spec("selection", [6, 1, 8, 3, 5])],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Sắp xếp chọn giảm dần", prescribed=_P_SELECT),
                [_classify(_TOKEN)],
                [_sort_spec("selection", [12, 5, 9, 3], order="desc")],
            ),
        },
    ),
    "algorithm.scan": TargetFixture(
        prompts={
            "direct": "Nhiệt độ 7 ngày: 31, 33, 30, 36, 32, 38, 29. Tìm ngày ĐẦU TIÊN vượt 35 độ.",
            "paraphrase": "Áp suất các bình: 12, 15, 11, 18, 14, 20. Dừng ở bình đầu tiên đạt từ 18 bar.",
            "changed_input": "Cho dãy 5, 9, 4, 12, 7. Tìm phần tử đầu tiên lớn hơn 10.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm ngày đầu tiên vượt 35 độ"),
                [_classify("algorithm.scan")],
                [_scan_cfg([31, 33, 30, 36, 32, 38, 29], 35, op=">")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Dừng ở bình đầu tiên ≥ 18 bar"),
                [_classify("algorithm.scan")],
                [_scan_cfg([12, 15, 11, 18, 14, 20], 18, op=">=")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm phần tử đầu tiên lớn hơn 10"),
                [_classify("algorithm.scan")],
                [_scan_cfg([5, 9, 4, 12, 7], 10, op=">")],
            ),
        },
    ),
    "logic.and_gate": TargetFixture(
        prompts={
            "direct": "Mô phỏng cổng AND hai đầu vào, cả hai đang bật.",
            "paraphrase": "Đèn chỉ sáng khi cả hai công tắc cùng đóng — hiện tại một công tắc mở.",
            "changed_input": "Cổng AND với đầu vào A tắt, B bật. Đầu ra là gì?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Cổng AND hai đầu vào"),
                [_classify("logic.and_gate")],
                [_logic_cfg(1, 1)],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Đầu ra 1 chỉ khi cả hai vào 1"),
                [_classify("logic.and_gate")],
                [_logic_cfg(1, 0)],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Cổng AND với A=0, B=1"),
                [_classify("logic.and_gate")],
                [_logic_cfg(0, 1)],
            ),
        },
    ),
    # M17 W1 — mạch logic nhiều cổng (boolean DAG + truth table)
    "logic.boolean_dag": TargetFixture(
        prompts={
            "direct": "Mạch logic: đèn sáng khi (A VÀ B) HOẶC (KHÔNG C). Mô phỏng mạch và bảng chân trị.",
            "paraphrase": "Chuông reo khi đúng MỘT trong hai công tắc bật (XOR). Dựng mạch logic.",
            "changed_input": "Cho biểu thức logic A ∧ ¬B. Lập bảng chân trị bằng mạch cổng.",
            "boundary": "Mạch 4 đầu vào: (A VÀ B) HOẶC (C VÀ D) — bảng chân trị đủ 16 hàng.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(objects=_DAG_OBJECTS, relations=_DAG_REL, goal="Mạch (A AND B) OR (NOT C)", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "A", "value": 1}, {"id": "B", "value": 0}, {"id": "C", "value": 1}],
                    [{"id": "g1", "op": "AND", "inputs": ["A", "B"]},
                     {"id": "g2", "op": "NOT", "inputs": ["C"]},
                     {"id": "g3", "op": "OR", "inputs": ["g1", "g2"]}],
                    "g3",
                )],
            ),
            "paraphrase": CaseScript(
                _analysis(objects=_DAG_OBJECTS, relations=_DAG_REL, goal="Chuông reo khi đúng một công tắc bật (XOR)", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "x", "value": 0}, {"id": "y", "value": 0}],
                    [{"id": "g", "op": "XOR", "inputs": ["x", "y"]}],
                    "g",
                )],
            ),
            "changed_input": CaseScript(
                _analysis(objects=_DAG_OBJECTS, relations=_DAG_REL, goal="Bảng chân trị của A ∧ ¬B", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "A", "value": 0}, {"id": "B", "value": 0}],
                    [{"id": "n", "op": "NOT", "inputs": ["B"]},
                     {"id": "g", "op": "AND", "inputs": ["A", "n"]}],
                    "g",
                )],
            ),
            "boundary": CaseScript(
                _analysis(objects=_DAG_OBJECTS, relations=_DAG_REL, goal="Mạch 4 đầu vào — bảng chân trị 16 hàng", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "A", "value": 0}, {"id": "B", "value": 0},
                     {"id": "C", "value": 0}, {"id": "D", "value": 0}],
                    [{"id": "g1", "op": "AND", "inputs": ["A", "B"]},
                     {"id": "g2", "op": "AND", "inputs": ["C", "D"]},
                     {"id": "g3", "op": "OR", "inputs": ["g1", "g2"]}],
                    "g3",
                )],
            ),
        },
    ),
    "binary.decimal_to_binary": TargetFixture(
        prompts={
            "direct": "Biểu diễn số 156 trong hệ nhị phân 8 bit.",
            "paraphrase": "Bật các công tắc trọng số 128..1 để tổng bằng 89.",
            "changed_input": "Đổi số 37 sang nhị phân 8 bit.",
            "boundary": "Biểu diễn 300 trong 8 bit nhị phân (vượt phạm vi biểu diễn).",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Biểu diễn 156 nhị phân", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(156, 8)],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Bật trọng số 128..1 cho tổng 89", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(89, 8)],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Đổi 37 sang nhị phân", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(37, 8)],
            ),
            # contract-error retry: attempt1 giữ 300 (validator từ chối) → attempt2 hợp lệ
            "boundary": CaseScript(
                _analysis(goal="Biểu diễn 300 nhị phân (vượt phạm vi)", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(300, 8), _binary_cfg(255, 8)],
            ),
        },
    ),
    # W5A — mô hình màu RGB. Bốn đề đi vào cùng một cơ chế bằng bốn lối nói
    # khác nhau: gọi tên màu, cho thẳng ba trị số, hỏi trộn hai kênh, và một đề
    # vượt biên (300) để chứng minh validator chặn chứ không kẹp lặng lẽ.
    "color.rgb_model": TargetFixture(
        prompts={
            "direct": "Màu vàng trong hệ màu RGB gồm những thành phần nào? Hãy cho xem màu đó.",
            "paraphrase": "Cho ba kênh đỏ 120, lục 90, lam 200 — màu thu được trông thế nào?",
            "changed_input": "Trộn đỏ 255 với lục 255 mà không có lam thì ra màu gì?",
            "boundary": "Đặt kênh đỏ bằng 300, lục 0, lam 0 (vượt phạm vi một kênh).",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Thành phần RGB của màu vàng", prescribed=_P_RGB),
                [_classify("color.rgb_model")],
                [_color_cfg(255, 255, 0)],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Màu từ ba kênh 120/90/200", prescribed=_P_RGB),
                [_classify("color.rgb_model")],
                [_color_cfg(120, 90, 200)],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Trộn đỏ và lục ở mức tối đa", prescribed=_P_RGB),
                [_classify("color.rgb_model")],
                [_color_cfg(255, 255, 0)],
            ),
            # contract-error retry: attempt1 giữ 300 (validator từ chối) → attempt2 hợp lệ
            "boundary": CaseScript(
                _analysis(goal="Kênh đỏ 300 (vượt phạm vi)", prescribed=_P_RGB),
                [_classify("color.rgb_model")],
                [_color_cfg(300, 0, 0), _color_cfg(255, 0, 0)],
            ),
        },
    ),
    # M17 W1 — base conversion tổng quát (gap hex/octal flip → owned)
    "binary.base_conversion": TargetFixture(
        prompts={
            "direct": "Đổi số 2026 sang hệ thập lục phân.",
            "paraphrase": "Số bát phân 755 bằng bao nhiêu trong hệ thập phân?",
            "changed_input": "Đổi số thập lục phân 9C sang hệ nhị phân.",
            "boundary": "Đổi 45 sang nhị phân (LLM khai nhầm cùng cơ số ở lượt đầu — validator từ chối, retry).",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đổi 2026 sang thập lục phân", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(10, 16, "2026")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Giá trị thập phân của số bát phân 755", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(8, 10, "755")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Đổi 9C (hex) sang nhị phân", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(16, 2, "9C")],
            ),
            # contract-retry: attempt1 cùng cơ số (validator từ chối) → attempt2 hợp lệ
            "boundary": CaseScript(
                _analysis(goal="Đổi 45 sang nhị phân", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(10, 10, "45"), _baseconv_cfg(10, 2, "45")],
            ),
        },
    ),
    "network.packet_routing": TargetFixture(
        prompts={
            "direct": "Gói tin đi từ máy tính qua switch, router, ISP tới máy chủ. Mô phỏng đường đi.",
            "paraphrase": "Dữ liệu truyền lần lượt qua từng thiết bị mạng từ máy khách tới máy chủ.",
            "changed_input": "Mạng có hai router song song giữa máy khách và máy chủ. Gói tin chọn đường nào?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(objects=_NET_OBJECTS, relations=_NET_REL, goal="Đường đi gói tin qua các chặng"),
                [_classify("network.packet_routing")],
                [_net_cfg(
                    [{"id": "pc", "type": "client"}, {"id": "sw", "type": "switch"},
                     {"id": "r1", "type": "router"}, {"id": "isp", "type": "isp"},
                     {"id": "srv", "type": "server"}],
                    [["pc", "sw"], ["sw", "r1"], ["r1", "isp"], ["isp", "srv"]], "pc", "srv",
                )],
            ),
            "paraphrase": CaseScript(
                _analysis(objects=_NET_OBJECTS, relations=_NET_REL, goal="Dữ liệu đi qua từng thiết bị"),
                [_classify("network.packet_routing")],
                [_net_cfg(
                    [{"id": "cl", "type": "client"}, {"id": "r1", "type": "router"},
                     {"id": "r2", "type": "router"}, {"id": "srv", "type": "server"}],
                    [["cl", "r1"], ["r1", "r2"], ["r2", "srv"]], "cl", "srv",
                )],
            ),
            "changed_input": CaseScript(
                _analysis(objects=_NET_OBJECTS, relations=_NET_REL, goal="Chọn đường khi có hai router song song"),
                [_classify("network.packet_routing")],
                [_net_cfg(
                    [{"id": "cl", "type": "client"}, {"id": "r1", "type": "router"},
                     {"id": "r2", "type": "router"}, {"id": "srv", "type": "server"}],
                    [["cl", "r1"], ["cl", "r2"], ["r1", "srv"], ["r2", "srv"]], "cl", "srv",
                )],
            ),
        },
    ),
    # M17 W1 — duyệt đồ thị BFS/DFS (packet_routing giữ là application variant)
    "network.graph_traversal": TargetFixture(
        prompts={
            "direct": "Duyệt đồ thị 5 đỉnh A,B,C,D,E (A-B, A-C, B-D, C-D, D-E) theo chiều rộng (BFS) từ A.",
            "paraphrase": "Đi thăm các đỉnh của đồ thị bắt đầu từ A, ưu tiên đi SÂU hết một nhánh rồi mới quay lại (DFS).",
            "changed_input": "Tìm đường từ A đến E trong đồ thị (A-B, B-C, C-E, A-D) bằng BFS.",
            "boundary": "Đồ thị hai phần rời: (A-B) và (X-Y). Duyệt BFS từ A tìm Y.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(objects=_GRAPH_OBJECTS, relations=_GRAPH_REL, goal="Duyệt đồ thị theo BFS từ A", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "C", "D", "E"],
                    [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["D", "E"]],
                    "A", "bfs",
                )],
            ),
            "paraphrase": CaseScript(
                _analysis(objects=_GRAPH_OBJECTS, relations=_GRAPH_REL, goal="Duyệt đồ thị theo chiều sâu từ A", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "C", "D", "E"],
                    [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["D", "E"]],
                    "A", "dfs",
                )],
            ),
            "changed_input": CaseScript(
                _analysis(objects=_GRAPH_OBJECTS, relations=_GRAPH_REL, goal="Tìm đường A→E bằng BFS", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "C", "D", "E"],
                    [["A", "B"], ["B", "C"], ["C", "E"], ["A", "D"]],
                    "A", "bfs", goal="E",
                )],
            ),
            # unreachable = kết quả hợp lệ (không phải lỗi)
            "boundary": CaseScript(
                _analysis(objects=_GRAPH_OBJECTS, relations=_GRAPH_REL, goal="Tìm Y từ A trong đồ thị rời", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "X", "Y"],
                    [["A", "B"], ["X", "Y"]],
                    "A", "bfs", goal="Y",
                )],
            ),
        },
    ),
    # M17 W2A — duyệt cây nhị phân (4 biến thể)
    "tree.traversal": TargetFixture(
        prompts={
            "direct": "Duyệt cây nhị phân gốc A (A có con trái B, con phải C; B có con "
                      "trái D, con phải E; C có con trái F, con phải G) theo thứ tự TRƯỚC (preorder).",
            "paraphrase": "Cho cây nhị phân gốc A với B,C là con của A; D,E con của B; F,G con của "
                          "C. Hãy duyệt theo thứ tự GIỮA (trái–gốc–phải).",
            "changed_input": "Duyệt cây nhị phân gốc A (B,C con A; D,E con B; F,G con C) theo thứ "
                             "tự SAU (hậu thứ tự, trái–phải–gốc).",
            "boundary": "Duyệt cây nhị phân gốc A (B,C con A; D,E con B; F,G con C) THEO MỨC "
                        "(từng tầng, level-order).",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Duyệt cây nhị phân theo thứ tự trước", ownership="provided",
                          relation_roles=["relational"], process_roles=["temporal"],
                          objects=_TREE_NODE_OBJECTS, relations=_TREE_RELATIONS),
                [_classify("tree.traversal")],
                [_tree_cfg("preorder", "A", _TREE_ABC)],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Duyệt cây nhị phân theo thứ tự giữa", ownership="provided",
                          relation_roles=["relational"], process_roles=["temporal"],
                          objects=_TREE_NODE_OBJECTS, relations=_TREE_RELATIONS),
                [_classify("tree.traversal")],
                [_tree_cfg("inorder", "A", _TREE_ABC)],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Duyệt cây nhị phân theo thứ tự sau", ownership="provided",
                          relation_roles=["relational"], process_roles=["temporal"],
                          objects=_TREE_NODE_OBJECTS, relations=_TREE_RELATIONS),
                [_classify("tree.traversal")],
                [_tree_cfg("postorder", "A", _TREE_ABC)],
            ),
            "boundary": CaseScript(
                _analysis(goal="Duyệt cây nhị phân theo mức", ownership="provided",
                          relation_roles=["relational"], process_roles=["temporal"],
                          objects=_TREE_NODE_OBJECTS, relations=_TREE_RELATIONS),
                [_classify("tree.traversal")],
                [_tree_cfg("level_order", "A", _TREE_ABC)],
            ),
        },
    ),
    # M17 W2C — luồng điều khiển hữu hạn (gán / rẽ nhánh / lặp có biên)
    "algorithm.bounded_control_flow": TargetFixture(
        prompts={
            "direct": "Cho x = 3. Tính y = x * 2 + 1. Chạy từng bước và cho biết y bằng bao nhiêu.",
            "paraphrase": "Ban đầu x = -2. Nếu x > 0 thì gán y = 1, ngược lại gán y = -1. "
                          "Hãy chạy từng bước xem nhánh nào được thực hiện.",
            "changed_input": "Cho x = 1. Trong khi x < 5 thì tăng x thêm 1. "
                             "Vòng lặp chạy mấy lượt và x cuối cùng bằng bao nhiêu?",
            "boundary": "Cho a = true, b = false. Nếu a và không b thì x = 1, ngược lại x = 0. "
                        "Chạy từng bước cho biết x bằng mấy.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Chạy từng bước đoạn chương trình gán", ownership="provided",
                          objects=_PG_OBJECTS, data=_PG_DATA),
                [_classify("algorithm.bounded_control_flow")],
                [_program_cfg_assign()],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Chạy từng bước đoạn chương trình rẽ nhánh", ownership="provided",
                          objects=_PG_OBJECTS, data=_PG_DATA),
                [_classify("algorithm.bounded_control_flow")],
                [_program_cfg_branch()],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Chạy từng bước vòng lặp while", ownership="provided",
                          objects=_PG_OBJECTS, data=_PG_DATA),
                [_classify("algorithm.bounded_control_flow")],
                [_program_cfg_loop()],
            ),
            "boundary": CaseScript(
                _analysis(goal="Chạy từng bước điều kiện logic", ownership="provided",
                          objects=_PG_OBJECTS, data=_PG_DATA),
                [_classify("algorithm.bounded_control_flow")],
                [_program_cfg_boolean()],
            ),
        },
    ),
    # W4B-2Z — thuộc tính trình bày có ràng buộc (HTML/CSS ở THPT).
    # Bốn archetype đổi THUỘC TÍNH, không đổi cơ chế: đó chính là điều phải
    # chứng minh — một cơ chế phục vụ nhiều bài học khác nhau.
    "web.style_model": TargetFixture(
        prompts={
            "direct": "Một thẻ có dòng chữ \"Chào các bạn\". Hãy đổi màu nền của thẻ "
                      "sang màu vàng nhạt và xem trang thay đổi thế nào.",
            "paraphrase": "Em muốn dòng chữ \"Lớp 12A1\" hiển thị to hơn và có màu đỏ. "
                          "Hãy thử đổi cỡ chữ và màu chữ rồi quan sát.",
            "changed_input": "Cho khối chữ \"Thông báo\". Tăng khoảng đệm bên trong "
                             "để chữ không dính sát mép, rồi so sánh trước và sau.",
            "boundary": "Thẻ giới thiệu \"Câu lạc bộ Tin học\" đang vuông góc. "
                        "Hãy bo tròn góc thẻ ở mức lớn nhất xem trông thế nào.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đổi màu nền của một khối chữ", ownership="provided",
                          objects=["thẻ", "dòng chữ"], data=[]),
                [_classify("web.style_model")],
                [_web_cfg("Chào các bạn", backgroundColor="#fde68a")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Đổi cỡ chữ và màu chữ", ownership="provided",
                          objects=["dòng chữ"], data=[]),
                [_classify("web.style_model")],
                [_web_cfg("Lớp 12A1", fontSize=32, color="#b91c1c")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Đổi khoảng đệm bên trong khối", ownership="provided",
                          objects=["khối chữ"], data=[]),
                [_classify("web.style_model")],
                [_web_cfg("Thông báo", padding=32)],
            ),
            "boundary": CaseScript(
                _analysis(goal="Bo tròn góc ở mức lớn nhất", ownership="provided",
                          objects=["thẻ giới thiệu"], data=[]),
                [_classify("web.style_model")],
                [_web_cfg("Câu lạc bộ Tin học", borderRadius=40)],
            ),
        },
    ),
    "binary.character_encoding": TargetFixture(
        prompts={
            "direct": "Mã ASCII của ký tự 'A' là bao nhiêu? Hãy mô phỏng từng bước "
                      "từ ký tự sang mã số rồi sang nhị phân.",
            "paraphrase": "Máy tính lưu chữ bằng số như thế nào? Lấy chuỗi \"Tin\" "
                          "và cho xem mã ASCII cùng dãy bit của từng ký tự.",
            "changed_input": "Cho biết mã ASCII của ký tự chữ số '7' và biểu diễn "
                             "nhị phân của mã đó.",
            "boundary": "Ký tự tiếng Việt 'ế' có mã Unicode code point là bao nhiêu? "
                        "Hãy đổi mã đó sang nhị phân.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tra mã ASCII của một ký tự", ownership="provided",
                          objects=_CE_OBJECTS),
                [_classify("binary.character_encoding")],
                [_charenc_cfg("A", "ascii")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Mã ASCII của từng ký tự trong chuỗi", ownership="provided",
                          objects=_CE_OBJECTS),
                [_classify("binary.character_encoding")],
                [_charenc_cfg("Tin", "ascii")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Mã ASCII của ký tự chữ số '7'", ownership="provided",
                          objects=["ký tự '7'", "bảng mã ASCII"]),
                [_classify("binary.character_encoding")],
                [_charenc_cfg("7", "ascii")],
            ),
            "boundary": CaseScript(
                _analysis(goal="Unicode code point của ký tự tiếng Việt",
                          ownership="provided",
                          objects=["ký tự 'ế'", "bảng mã Unicode"]),
                [_classify("binary.character_encoding")],
                [_charenc_cfg("\u1ebf", "unicode_codepoint")],
            ),
        },
    ),
    "network.protocol_encapsulation": TargetFixture(
        prompts={
            "direct": "Mô phỏng quá trình đóng gói dữ liệu qua các tầng TCP/IP khi gửi một trang web.",
            "paraphrase": "Mỗi tầng mạng bọc thêm phần đầu vào tin nhắn trước khi truyền đi.",
            "changed_input": "Máy nhận tháo từng lớp gói tin như thế nào? Mô phỏng quá trình mở gói.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đóng gói qua các tầng TCP/IP"),
                [_classify("network.protocol_encapsulation")],
                [_encap_cfg("Dữ liệu ứng dụng")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Mỗi tầng bọc thêm thông tin"),
                [_classify("network.protocol_encapsulation")],
                [_encap_cfg("Tin nhắn")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tháo gói ở máy nhận"),
                [_classify("network.protocol_encapsulation")],
                [_encap_cfg("Gói tin nhận")],
            ),
        },
    ),
    "generic.rule_scene": TargetFixture(
        prompts={
            "direct": "Dựng tam giác ABC từng bước: vẽ AB, thêm C, nối AC và BC.",
            "paraphrase": "Vẽ sơ đồ ba trạm theo mô tả, hiện dần từng trạm một.",
            "changed_input": "Robot đi qua các trạm A→B→C→D→E, mỗi bước một trạm.",
            "boundary": "Đèn chỉ sáng khi CẢ BA công tắc cùng bật. Mô phỏng mạch.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(
                    goal="Dựng tam giác ABC từng bước", ownership="provided",
                    scene_construction="step_by_step", relation_roles=["relational"],
                    process_roles=["temporal"],
                ),
                [_classify(_GENERIC)],
                [_TRIANGLE_REVEAL],
            ),
            "paraphrase": CaseScript(
                _analysis(
                    goal="Vẽ sơ đồ các trạm, hiện dần từng trạm", ownership="provided",
                    scene_construction="step_by_step", relation_roles=["relational"],
                    process_roles=["temporal"],
                ),
                [_classify(_GENERIC)],
                [_STATION_REVEAL],
            ),
            "changed_input": CaseScript(
                _analysis(
                    goal="Robot đi qua các trạm", ownership="provided",
                    scene_construction="step_by_step", process_roles=["movement", "temporal"],
                ),
                [_classify(_GENERIC)],
                [_MOVING_PATH],
            ),
            # computation membership (boolean composed_rule_dag) — AND 3 đầu vào
            "boundary": CaseScript(
                _analysis(
                    goal="Đèn sáng khi cả BA công tắc bật", ownership="rule_derivable",
                    entity_roles=["logical"], interaction_needs=["interactive"],
                ),
                [_classify(_GENERIC)],
                [_AND3_GATE],
            ),
        },
    ),
}


# ══════════════ near-miss per cơ chế INTENTIONAL_GAP (dedupe theo mechanism) ══
# M17 W1: near-miss select_extreme_repeated ĐÃ flip thành ok-case của target
# algorithm.selection_sort (xem TARGET_FIXTURES) — không còn ở đây.
NEAR_MISS_FIXTURES: dict[str, ControlFixture] = {
    "comparison_sort.partition_recursive": ControlFixture(
        case_id="aud-nm-quick-sort",
        kind="near_miss",
        prompt="Sắp xếp dãy 8, 3, 6, 1, 9 bằng cách chọn mốc rồi CHIA dãy quanh mốc và đệ quy (quick sort).",
        script=CaseScript(
            _analysis(goal="Sắp xếp bằng chia quanh mốc + đệ quy", ownership="algorithmic", prescribed=_P_PARTITION),
            [_classify(_TOKEN)],
        ),
        mechanism="comparison_sort.partition_recursive",
        note="Quick sort giữ gap (contract không biểu diễn partition) — không ép.",
    ),
    "comparison_sort.other_unspecified": ControlFixture(
        case_id="aud-nm-sort-unspecified",
        kind="near_miss",
        prompt="Sắp xếp dãy 5, 8, 1 bằng một thuật toán tự chọn hiệu quả nhất.",
        script=CaseScript(
            _analysis(goal="Sắp xếp bằng thuật toán không nêu cơ chế", ownership="algorithmic", prescribed=_P_OTHER),
            [_classify(_TOKEN)],
        ),
        mechanism="comparison_sort.other_unspecified",
        note="Cơ chế không xác định — từ chối trung thực thay vì đoán biến thể.",
    ),
    # M17 W1: near-miss non_binary_base ĐÃ flip thành ok-case của target
    # binary.base_conversion (xem TARGET_FIXTURES) — không còn ở đây.
}


# ══════════════ leak / refusal control + regression duyệt cây ══════════════
# (M17 W2A: _TREE_AS_POINTS đã gỡ — probe adversarial "ép cây thành điểm/đoạn/
# vật di chuyển" nay ĐÓNG: prompt duyệt cây route vào tree.traversal.)

CONTROL_FIXTURES: tuple[ControlFixture, ...] = (
    ControlFixture(
        case_id="aud-leak-dijkstra",
        kind="leak_control",
        prompt="Vẽ sơ đồ các trạm rồi TÍNH đường đi ngắn nhất theo tổng độ dài các cạnh.",
        script=CaseScript(
            _analysis(goal="Vẽ sơ đồ trạm rồi TÍNH đường ngắn nhất có trọng số", ownership="algorithmic"),
            [_classify(_GENERIC)],
        ),
        note="Kết quả thuật toán không engine nào sở hữu → computation gate (bất biến #21).",
        # generic KHÔNG được nhận cơ chế chuyên biệt của family khác.
        audit_slot="cross_family_near_miss",
        audit_target=_GENERIC,
    ),
    # M17 W2A — ĐÓNG regression duyệt cây: prompt duyệt cây NAY route vào
    # specialized tree.traversal (KHÔNG còn generic/gap). Bằng chứng closure của
    # CONDITIONAL_LEAK Wave 0.
    ControlFixture(
        case_id="aud-regression-tree-honest",
        kind="leak_control",
        prompt="Mô phỏng thuật toán duyệt cây nhị phân theo thứ tự trước (preorder) trên cây gốc A (con trái B, con phải C).",
        script=CaseScript(
            _analysis(goal="Duyệt cây nhị phân theo thứ tự trước", ownership="provided",
                      relation_roles=["relational"], process_roles=["temporal"],
                      objects=["A", "B", "C"], relations=_TREE_RELATIONS),
            [_classify("tree.traversal")],
            [_tree_cfg("preorder", "A", [("A", "B", "C"), ("B", None, None), ("C", None, None)])],
        ),
        expected_status="ok",
        expected_route="tree.traversal",
        note="CLOSURE W2A: prompt duyệt cây route vào tree.traversal (KHÔNG generic, KHÔNG gap).",
    ),
    # Prompt CÙNG cây Wave 0 (adversarial) nay với analyze TRUNG THỰC → route
    # tree.traversal. Đóng CONDITIONAL_LEAK bằng bằng chứng: đúng prompt từng leak
    # nay có nhà specialized. (Rủi ro analyze khai man vẫn là giới hạn analyze-
    # honesty đã ghi Wave 0 — không thuộc phạm vi tree_traversal đóng.)
    ControlFixture(
        case_id="aud-regression-tree-adversarial",
        kind="leak_control",
        prompt="Cho cây nhị phân gốc 1, con trái 2, con phải 3, nút 2 có con trái 4. Mô phỏng duyệt cây theo thứ tự trước.",
        script=CaseScript(
            _analysis(goal="Duyệt cây nhị phân theo thứ tự trước", ownership="provided",
                      relation_roles=["relational"], process_roles=["temporal"],
                      objects=["1", "2", "3", "4"],
                      relations=[{"type": "left_child", "from": "1", "to": "2"},
                                 {"type": "right_child", "from": "1", "to": "3"}]),
            [_classify("tree.traversal")],
            [_tree_cfg("preorder", "1", [("1", "2", "3"), ("2", "4", None), ("3", None, None), ("4", None, None)])],
        ),
        expected_status="ok",
        expected_route="tree.traversal",
        note="CLOSURE W2A: đúng prompt từng CONDITIONAL_LEAK ở Wave 0 nay route tree.traversal.",
    ),
    # THIẾU CẤU TRÚC: đề đòi duyệt cây nhưng không cho node/quan hệ → KHÔNG tự
    # dựng cây mặc định; unsupported trung thực (chưa đủ dữ kiện).
    # STRUCTURE GATE (M17 W2A): classify VẪN route tree.traversal (LLM tưởng là
    # bài duyệt cây) NHƯNG analyze KHÔNG thấy cấu trúc (không object/relation cụ
    # thể) → structure gate chặn TRƯỚC simulate → unsupported. Đây test PHÒNG THỦ
    # DETERMINISTIC, không phải classify tự từ chối (LLM đã chứng minh live là
    # KHÔNG tự từ chối — bịa cây).
    ControlFixture(
        case_id="aud-regression-tree-insufficient",
        kind="refusal_control",
        prompt="Mô phỏng thuật toán duyệt cây theo thứ tự trước.",
        script=CaseScript(
            _analysis(goal="Duyệt cây theo thứ tự trước (không cho cấu trúc cây)",
                      ownership="provided", relation_roles=["relational"]),
            [_classify("tree.traversal")],  # LLM route tree — nhưng gate chặn vì thiếu cấu trúc
        ),
        expected_status="unsupported",
        note="Thiếu cấu trúc cây → structure gate chặn (insufficient_specification), KHÔNG dựng cây mặc định.",
        audit_slot="insufficient_input",
        audit_target="tree.traversal",
    ),
    ControlFixture(
        case_id="aud-refusal-tcp-handshake",
        kind="refusal_control",
        prompt="Mô phỏng bắt tay ba bước TCP giữa máy khách và máy chủ.",
        script=CaseScript(
            _analysis(goal="Bắt tay ba bước TCP", ownership="rule_derivable"),
            [_classify(None, status="unsupported",
                       reason="Bắt tay ba bước / máy trạng thái giao thức vượt năng lực v1 — trả unsupported trung thực.")],
        ),
        note="Advanced-TCP từ chối trung thực ở classify (khoá cur-t12-tcp-advanced).",
        # Bắt tay TCP là BIẾN THỂ ngoài năng lực của v1 encapsulation (không
        # phải "thiếu dữ kiện") → chứng minh slot unsupported_variant.
        audit_slot="unsupported_variant_or_parameter",
        audit_target="network.protocol_encapsulation",
    ),
    ControlFixture(
        case_id="aud-control-representation-ok",
        kind="refusal_control",
        prompt="Vẽ sơ đồ ba trạm nối tiếp nhau, hiện dần từng trạm theo mô tả cho sẵn.",
        script=CaseScript(
            _analysis(
                goal="Vẽ sơ đồ các trạm, hiện dần từng trạm", ownership="provided",
                scene_construction="step_by_step", relation_roles=["relational"],
                process_roles=["temporal"],
            ),
            [_classify(_GENERIC)],
            [_STATION_REVEAL],
        ),
        expected_status="ok",
        note="ĐỐI CHỨNG chống chặn oan: biểu diễn khai báo thuần túy PHẢI được generic nhận.",
        audit_slot="supported_canonical",
        audit_target=_GENERIC,
    ),
)
