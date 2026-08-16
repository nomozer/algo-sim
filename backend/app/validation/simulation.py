"""Validator config THEO DOMAIN — chốt chặn bắt buộc trước khi phát hành
SimulationEnvelope (M3 §6).

Lõi không giả định mọi simulation có array/target/condition/order/timeline
(M3 §9): mỗi domain tự định nghĩa validator cho schema riêng của mình;
thêm domain mới = thêm một validator, không sửa lõi.
"""

from __future__ import annotations

import re

ALGORITHM_IDS = [
    "find_max",
    "find_min",
    "sum_if",
    "count_if",
    "linear_search",
    "binary_search",
    "bubble_sort",
    "insertion_sort",
    "selection_sort",
]

ALGORITHM_NAMES_VI = {
    "find_max": "Tìm giá trị lớn nhất",
    "find_min": "Tìm giá trị nhỏ nhất",
    "sum_if": "Tính tổng theo điều kiện",
    "count_if": "Đếm theo điều kiện",
    "linear_search": "Tìm kiếm tuần tự",
    "binary_search": "Tìm kiếm nhị phân",
    "bubble_sort": "Sắp xếp nổi bọt",
    "insertion_sort": "Sắp xếp chèn",
    "selection_sort": "Sắp xếp chọn",
}

CONDITION_OPS = [">", ">=", "<", "<=", "==", "!="]

# Khóa CẤM ở mọi domain: LLM không được sinh diễn biến — engine tự sinh (M3 §5)
FORBIDDEN_CONFIG_KEYS = {"steps", "timeline", "state", "frames", "transitions", "animations"}


def check_forbidden_keys(raw: dict) -> str | None:
    bad = FORBIDDEN_CONFIG_KEYS.intersection(raw.keys())
    if bad:
        return (
            f"Config chứa khóa bị cấm: {', '.join(sorted(bad))}. "
            "Diễn biến mô phỏng do engine tất định sinh ra — chỉ điền dữ liệu đầu vào."
        )
    return None


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_algorithm_config(algorithm_id: str, raw) -> tuple[dict | None, str | None]:
    """Validator của domain algorithm — schema RIÊNG của domain này.

    Trả (config chuẩn hóa, None) khi hợp lệ, (None, lỗi tiếng Việt) khi sai —
    lỗi được gửi ngược cho LLM retry ở stage simulate.
    """
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."

    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden

    data = raw.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("array"), list):
        return None, 'Thiếu "data.array".'

    array = data["array"]
    if len(array) < 2 or len(array) > 15:
        return None, (
            f'"data.array" phải có 2–15 phần tử (đang có {len(array)}). '
            'Đề cho nhiều hơn → lấy 12 phần tử đầu và ghi chú vào "notes".'
        )
    if not all(_is_number(v) for v in array):
        return None, '"data.array" phải toàn số hữu hạn.'
    nums = list(array)

    labels = None
    raw_labels = data.get("labels")
    if isinstance(raw_labels, list) and len(raw_labels) > 0:
        if len(raw_labels) != len(nums):
            return None, (
                f'"data.labels" ({len(raw_labels)}) phải khớp độ dài "data.array" ({len(nums)}).'
            )
        if not all(isinstance(l, str) for l in raw_labels):
            return None, '"data.labels" phải toàn chuỗi.'
        labels = raw_labels

    target = None
    if algorithm_id in ("linear_search", "binary_search"):
        if not _is_number(data.get("target")):
            return None, f'Mô phỏng "{algorithm_id}" bắt buộc có "data.target" là số.'
        target = data["target"]

    condition = None
    if algorithm_id in ("sum_if", "count_if"):
        c = data.get("condition")
        if (
            not isinstance(c, dict)
            or c.get("op") not in CONDITION_OPS
            or not _is_number(c.get("value"))
        ):
            return None, (
                f'Mô phỏng "{algorithm_id}" bắt buộc có "data.condition" dạng '
                f'{{op: một trong {" ".join(CONDITION_OPS)}, value: số}}.'
            )
        condition = {"op": c["op"], "value": c["value"]}

    order = None
    if algorithm_id in ("bubble_sort", "insertion_sort", "selection_sort"):
        if data.get("order") not in ("asc", "desc"):
            return None, f'Mô phỏng "{algorithm_id}" bắt buộc có "data.order" là "asc" hoặc "desc".'
        order = data["order"]

    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    final_array = nums
    final_labels = labels

    # Tiền đề: tìm kiếm nhị phân cần dãy đã sắp — hệ tự sắp + chú thích sư phạm
    if algorithm_id == "binary_search":
        is_sorted = all(nums[i - 1] <= nums[i] for i in range(1, len(nums)))
        if not is_sorted:
            indexed = sorted(range(len(nums)), key=lambda i: nums[i])
            final_array = [nums[i] for i in indexed]
            final_labels = [labels[i] for i in indexed] if labels else None
            note = "Dãy đã được sắp xếp trước — tìm kiếm nhị phân chỉ chạy trên dãy có thứ tự."
            notes = f"{notes} {note}" if notes else note

    problem = raw.get("problem") if isinstance(raw.get("problem"), dict) else {}
    def _text(key: str, default: str) -> str:
        v = problem.get(key)
        return v if isinstance(v, str) and v else default

    config = {
        "problem": {
            "summary": _text("summary", ALGORITHM_NAMES_VI[algorithm_id]),
            "input": _text("input", "Dữ liệu dạng dãy số"),
            "output": _text("output", "Kết quả sau khi chạy thuật toán"),
        },
        "algorithm_id": algorithm_id,
        "data": {
            "array": final_array,
            "labels": final_labels,
            "target": target,
            "condition": condition,
            "order": order,
        },
        "data_generated": raw.get("data_generated") is True,
        "notes": notes,
    }
    return config, None


# ── Domain logic (M5) ─────────────────────────────────────────

def _as_bit(v) -> int | None:
    if v is True or v == 1:
        return 1
    if v is False or v == 0:
        return 0
    return None


def validate_logic_config(raw) -> tuple[dict | None, str | None]:
    """logic.and_gate — config chỉ gồm hai đầu vào 0/1. Output do engine tính."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    a = _as_bit(raw.get("inputA"))
    b = _as_bit(raw.get("inputB"))
    if a is None or b is None:
        return None, '"inputA" và "inputB" phải là 0 hoặc 1.'
    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {"inputA": a, "inputB": b, "notes": notes}, None


# ── Domain binary (M5) ────────────────────────────────────────

def validate_binary_config(raw) -> tuple[dict | None, str | None]:
    """binary.decimal_to_binary — số thập phân + số bit. Các bit do engine tính."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    dec = raw.get("decimalValue")
    if not isinstance(dec, int) or isinstance(dec, bool) or dec < 0 or dec > 255:
        return None, '"decimalValue" phải là số nguyên từ 0 đến 255.'
    width = raw.get("bitWidth")
    if not isinstance(width, int) or isinstance(width, bool) or width < 1 or width > 8:
        return None, '"bitWidth" phải là số nguyên từ 1 đến 8.'
    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    # Số bit không đủ chứa giá trị → tự nới rộng + chú thích (engine vẫn tất định)
    needed = max(1, dec.bit_length())
    if needed > width:
        note = f"Đã tăng số bit lên {needed} để biểu diễn đủ giá trị {dec}."
        notes = f"{notes} {note}" if notes else note
        width = needed
    return {"decimalValue": dec, "bitWidth": width, "notes": notes}, None


# ── Domain color (W5A) ────────────────────────────────────────

COLOR_CHANNELS = ("red", "green", "blue")
COLOR_CHANNEL_MAX = 255


def validate_color_config(raw) -> tuple[dict | None, str | None]:
    """color.rgb_model — BA kênh nguyên 0..255.

    Vì sao validator KHÔNG nhận `hex`/`colorName`/`preview`: màu kết quả là thứ
    engine TÍNH từ ba kênh, nên nhận thêm một cách nói khác về cùng giá trị là
    mở đúng cửa hậu mà M5 §6 đóng — LLM sẽ có hai đường để nói "màu gì", và khi
    hai đường lệch nhau thì không ai là nguồn sự thật. Ba số, một sự thật.
    """
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    channels: dict[str, int] = {}
    for name in COLOR_CHANNELS:
        v = raw.get(name)
        if not isinstance(v, int) or isinstance(v, bool) or v < 0 or v > COLOR_CHANNEL_MAX:
            return None, f'"{name}" phải là số nguyên từ 0 đến {COLOR_CHANNEL_MAX}.'
        channels[name] = v
    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {**channels, "notes": notes}, None


# ── binary.base_conversion (M17 W1) ───────────────────────────

CONV_BASES = (2, 8, 10, 16)
CONV_MAX_VALUE = 65535  # bound 16 bit — bounded capability
_CONV_DIGITS = "0123456789ABCDEF"


def _conv_strategy(source: int, target: int) -> str:
    """Chiến lược DẪN XUẤT TẤT ĐỊNH từ cặp cơ số — LLM không được chọn khác."""
    if source == 10:
        return "quotient_remainder"
    if target == 10:
        return "positional_weights"
    return "two_stage"


def validate_base_conversion_config(raw) -> tuple[dict | None, str | None]:
    """binary.base_conversion — đổi cơ số {2,8,10,16}. Trace chia-lấy-dư /
    trọng số vị trí / hai giai đoạn + KẾT QUẢ do engine tất định tính."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    src = raw.get("sourceBase")
    tgt = raw.get("targetBase")
    for name, v in (("sourceBase", src), ("targetBase", tgt)):
        if not isinstance(v, int) or isinstance(v, bool) or v not in CONV_BASES:
            return None, f'"{name}" phải thuộc {{2, 8, 10, 16}}.'
    if src == tgt:
        return None, '"sourceBase" phải KHÁC "targetBase".'
    value_raw = raw.get("inputValue")
    if not isinstance(value_raw, str) or not (1 <= len(value_raw) <= 16):
        return None, '"inputValue" phải là chuỗi chữ số (1–16 ký tự) theo sourceBase.'
    canonical = value_raw.upper()
    allowed = _CONV_DIGITS[:src]
    if not all(ch in allowed for ch in canonical):
        return None, (
            f'"inputValue" chứa ký tự không hợp lệ với cơ số {src} '
            f"(chỉ được dùng: {' '.join(allowed)})."
        )
    canonical = canonical.lstrip("0") or "0"
    value = int(canonical, src)
    if value > CONV_MAX_VALUE:
        return None, f"Giá trị vượt giới hạn {CONV_MAX_VALUE} — ngoài phạm vi mô phỏng."
    derived = _conv_strategy(src, tgt)
    strategy = raw.get("strategy")
    if strategy is not None and strategy != derived:
        return None, f'"strategy" (nếu có) phải là "{derived}" — dẫn xuất từ cặp cơ số.'
    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {
        "sourceBase": src,
        "targetBase": tgt,
        "inputValue": canonical,
        "strategy": derived,
        "notes": notes,
    }, None


# ── tree.traversal (M17 W2A) ──────────────────────────────────

TREE_VARIANTS = ("preorder", "inorder", "postorder", "level_order")
TREE_SPEC_VERSION = "tree-1.0"
TREE_MAX_NODES = 15
TREE_MAX_DEPTH = 5


def validate_tree_traversal_config(raw) -> tuple[dict | None, str | None]:
    """tree.traversal — duyệt cây nhị phân bounded. Thứ tự thăm/stack/queue/
    kết quả do engine FE tính. Hai tầng: structural + semantic (cây thật)."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    if raw.get("specVersion") != TREE_SPEC_VERSION:
        return None, f'"specVersion" phải là "{TREE_SPEC_VERSION}".'
    variant = raw.get("variant")
    if variant not in TREE_VARIANTS:
        return None, '"variant" phải là preorder/inorder/postorder/level_order.'
    nodes_raw = raw.get("nodes")
    if not isinstance(nodes_raw, list) or not (1 <= len(nodes_raw) <= TREE_MAX_NODES):
        return None, f'"nodes" phải có 1–{TREE_MAX_NODES} node.'

    ids: set[str] = set()
    nodes = []
    for it in nodes_raw:
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"]:
            return None, "Mỗi node phải là object có id chuỗi."
        if it["id"] in ids:
            return None, f"Id node trùng: {it['id']}."
        ids.add(it["id"])
        label = it.get("label")
        label = label if isinstance(label, str) and label else it["id"]
        if len(label) > 24:
            return None, f"Nhãn node {it['id']} quá dài."
        left = it.get("left")
        right = it.get("right")
        if left is not None and not isinstance(left, str):
            return None, f"left của {it['id']} phải là id hoặc rỗng."
        if right is not None and not isinstance(right, str):
            return None, f"right của {it['id']} phải là id hoặc rỗng."
        nodes.append({"id": it["id"], "label": label, "left": left, "right": right})

    root_id = raw.get("rootId")
    if not isinstance(root_id, str) or root_id not in ids:
        return None, '"rootId" phải là id một node có thật.'

    by_id = {n["id"]: n for n in nodes}
    parent_of: dict[str, str] = {}
    for n in nodes:
        for child in (n["left"], n["right"]):
            if child is None:
                continue
            if child not in ids:
                return None, f"Node {n['id']} tham chiếu con không tồn tại: {child}."
            if child == n["id"]:
                return None, f"Node {n['id']} tự trỏ tới chính nó."
            if child in parent_of:
                return None, f"Node {child} có NHIỀU cha ({parent_of[child]}, {n['id']}) — không phải cây."
            parent_of[child] = n["id"]
    if root_id in parent_of:
        return None, f"rootId {root_id} lại là con của {parent_of[root_id]} — không phải gốc."

    seen: set[str] = {root_id}
    queue: list[tuple[str, int]] = [(root_id, 1)]
    while queue:
        nid, depth = queue.pop(0)
        if depth > TREE_MAX_DEPTH:
            return None, f"Cây sâu quá {TREE_MAX_DEPTH} tầng."
        node = by_id[nid]
        for child in (node["left"], node["right"]):
            if child is not None and child not in seen:
                seen.add(child)
                queue.append((child, depth + 1))
    if len(seen) != len(nodes):
        orphan = sorted(n["id"] for n in nodes if n["id"] not in seen)
        return None, f"Node không nối tới gốc (rời rạc): {', '.join(orphan)}."

    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {
        "specVersion": TREE_SPEC_VERSION,
        "variant": variant,
        "rootId": root_id,
        "nodes": nodes,
        "notes": notes,
    }, None


# ── logic.boolean_dag (M17 W1) ────────────────────────────────

DAG_OPS = ("AND", "OR", "NOT", "XOR")
DAG_MAX_INPUTS = 4
DAG_MAX_GATES = 8


def validate_boolean_dag_config(raw) -> tuple[dict | None, str | None]:
    """logic.boolean_dag — DAG cổng {AND,OR,NOT,XOR} bounded. Thứ tự đánh giá,
    output từng cổng, bảng chân trị, kết quả — TẤT CẢ do engine FE tính."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden

    inputs_raw = raw.get("inputs")
    if not isinstance(inputs_raw, list) or not (1 <= len(inputs_raw) <= DAG_MAX_INPUTS):
        return None, f'"inputs" phải có 1–{DAG_MAX_INPUTS} đầu vào.'
    gates_raw = raw.get("gates")
    if not isinstance(gates_raw, list) or not (1 <= len(gates_raw) <= DAG_MAX_GATES):
        return None, f'"gates" phải có 1–{DAG_MAX_GATES} cổng.'

    ids: set[str] = set()
    inputs = []
    for it in inputs_raw:
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"]:
            return None, "Mỗi đầu vào phải là object có id chuỗi."
        if it["id"] in ids:
            return None, f"Id trùng: {it['id']}."
        ids.add(it["id"])
        if it.get("value") not in (0, 1) or isinstance(it.get("value"), bool):
            return None, f'Đầu vào {it["id"]}: "value" phải là 0 hoặc 1.'
        label = it.get("label")
        inputs.append({
            "id": it["id"],
            "label": label if isinstance(label, str) else None,
            "value": it["value"],
        })

    gates = []
    for it in gates_raw:
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"]:
            return None, "Mỗi cổng phải là object có id chuỗi."
        if it["id"] in ids:
            return None, f"Id trùng: {it['id']}."
        ids.add(it["id"])
        op = it.get("op")
        if op not in DAG_OPS:
            return None, f'Cổng {it["id"]}: "op" phải thuộc {{AND, OR, NOT, XOR}}.'
        refs = it.get("inputs")
        if not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
            return None, f'Cổng {it["id"]}: "inputs" phải là mảng id.'
        need = 1 if op == "NOT" else 2
        if len(refs) != need:
            return None, f'Cổng {it["id"]} ({op}) cần đúng {need} đầu vào.'
        gates.append({"id": it["id"], "op": op, "inputs": list(refs)})

    for g in gates:
        for ref in g["inputs"]:
            if ref not in ids:
                return None, f"Cổng {g['id']} tham chiếu id không tồn tại: {ref}."

    output = raw.get("output")
    gate_ids = {g["id"] for g in gates}
    if not isinstance(output, str) or output not in gate_ids:
        return None, '"output" phải là id của MỘT cổng trong mạch.'

    # cycle check (DFS ba màu) — đầu vào là lá
    input_ids = {i["id"] for i in inputs}
    gate_by_id = {g["id"]: g for g in gates}
    done: set[str] = set()
    visiting: set[str] = set()

    def visit(nid: str) -> bool:
        if nid in input_ids or nid in done:
            return True
        if nid in visiting:
            return False
        visiting.add(nid)
        for ref in gate_by_id[nid]["inputs"]:
            if not visit(ref):
                return False
        visiting.discard(nid)
        done.add(nid)
        return True

    for g in gates:
        if not visit(g["id"]):
            return None, "Mạch chứa CYCLE — phải là DAG (không vòng)."

    # mọi cổng phải góp vào output (không cổng rác lơ lửng)
    used = {output}
    stack = [output]
    while stack:
        nid = stack.pop()
        if nid in gate_by_id:
            for ref in gate_by_id[nid]["inputs"]:
                if ref not in used:
                    used.add(ref)
                    stack.append(ref)
    dangling = sorted(g["id"] for g in gates if g["id"] not in used)
    if dangling:
        return None, f"Cổng không góp vào đầu ra: {', '.join(dangling)}."

    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {"inputs": inputs, "gates": gates, "output": output, "notes": notes}, None


# ── network.graph_traversal (M17 W1) ──────────────────────────

TRAVERSE_VARIANTS = ("bfs", "dfs")
TRAVERSE_MAX_NODES = 10
TRAVERSE_MAX_EDGES = 20


def validate_traverse_config(raw) -> tuple[dict | None, str | None]:
    """network.graph_traversal — BFS/DFS trên đồ thị KHÔNG trọng số. Frontier,
    thứ tự thăm, predecessor, đường đi, reachable — TẤT CẢ do engine FE tính.
    Không-đến-được là KẾT QUẢ hợp lệ (không phải lỗi validate)."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden

    nodes_raw = raw.get("nodes")
    if not isinstance(nodes_raw, list) or not (2 <= len(nodes_raw) <= TRAVERSE_MAX_NODES):
        return None, f'"nodes" phải có 2–{TRAVERSE_MAX_NODES} nút.'
    ids: set[str] = set()
    nodes = []
    for it in nodes_raw:
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"]:
            return None, "Mỗi nút phải là object có id chuỗi."
        if it["id"] in ids:
            return None, f"Id nút trùng: {it['id']}."
        ids.add(it["id"])
        label = it.get("label")
        nodes.append({"id": it["id"], "label": label if isinstance(label, str) else None})

    edges_raw = raw.get("edges")
    if not isinstance(edges_raw, list) or len(edges_raw) > TRAVERSE_MAX_EDGES:
        return None, f'"edges" phải là mảng tối đa {TRAVERSE_MAX_EDGES} cạnh.'
    edges = []
    for e in edges_raw:
        if (
            not isinstance(e, list)
            or len(e) != 2
            or not all(isinstance(x, str) for x in e)
        ):
            return None, "Mỗi cạnh phải là cặp [idA, idB]."
        if e[0] not in ids or e[1] not in ids:
            return None, f"Cạnh [{e[0]}, {e[1]}] tham chiếu nút không tồn tại."
        if e[0] == e[1]:
            return None, "Không nhận cạnh tự nối (self-loop)."
        edges.append([e[0], e[1]])

    start = raw.get("start")
    if not isinstance(start, str) or start not in ids:
        return None, '"start" phải là id một nút có thật.'
    goal = raw.get("goal")
    if goal is not None:
        if not isinstance(goal, str) or goal not in ids:
            return None, '"goal" (nếu có) phải là id một nút có thật.'
        if goal == start:
            return None, '"goal" phải khác "start".'
    variant = raw.get("variant")
    if variant not in TRAVERSE_VARIANTS:
        return None, '"variant" phải là "bfs" hoặc "dfs".'

    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {
        "nodes": nodes,
        "edges": edges,
        "directed": raw.get("directed") is True,
        "start": start,
        "goal": goal,
        "variant": variant,
        "notes": notes,
    }, None


# ── Domain network (M5) ───────────────────────────────────────

_NODE_TYPES = {"client", "router", "server", "switch", "isp"}


def validate_network_config(raw) -> tuple[dict | None, str | None]:
    """network.packet_routing — topo mạng. Route/timeline do engine BFS tất định."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden

    nodes = raw.get("nodes")
    if not isinstance(nodes, list) or not (2 <= len(nodes) <= 8):
        return None, '"nodes" phải là danh sách 2–8 nút.'
    node_ids: list[str] = []
    norm_nodes: list[dict] = []
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or not n["id"]:
            return None, 'Mỗi nút phải có "id" là chuỗi.'
        ntype = n.get("type") if n.get("type") in _NODE_TYPES else "router"
        if n["id"] in node_ids:
            return None, f'Trùng id nút "{n["id"]}".'
        node_ids.append(n["id"])
        norm_nodes.append({"id": n["id"], "type": ntype})

    links = raw.get("links")
    if not isinstance(links, list) or len(links) < 1:
        return None, '"links" phải có ít nhất một liên kết.'
    norm_links: list[list[str]] = []
    adj: dict[str, set[str]] = {nid: set() for nid in node_ids}
    for lk in links:
        if not isinstance(lk, list) or len(lk) != 2 or lk[0] not in node_ids or lk[1] not in node_ids:
            return None, "Mỗi liên kết phải là cặp id nút có thật."
        if lk[0] == lk[1]:
            return None, "Liên kết không được nối một nút với chính nó."
        norm_links.append([lk[0], lk[1]])
        adj[lk[0]].add(lk[1])
        adj[lk[1]].add(lk[0])

    source = raw.get("source")
    dest = raw.get("destination")
    if source not in node_ids or dest not in node_ids or source == dest:
        return None, '"source" và "destination" phải là hai nút khác nhau có thật.'

    # Kiểm tra tồn tại đường đi (BFS) — không có thì reject
    seen = {source}
    queue = [source]
    while queue:
        cur = queue.pop(0)
        if cur == dest:
            break
        for nxt in adj[cur]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    if dest not in seen:
        return None, "Không có đường đi từ nguồn tới đích trong topo này."

    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {
        "nodes": norm_nodes,
        "links": norm_links,
        "source": source,
        "destination": dest,
        "notes": notes,
    }, None


# Khóa v1 KHÔNG cho LLM tự mô hình hoá — tầng/PDU/gói thuộc engine tất định (M10)
_ENCAP_OWNED_BY_ENGINE = {"layers", "pdu", "headers", "packets", "protocols"}
_ENCAP_PAYLOAD_MAX = 80
_ENCAP_PROTOCOL_MAX = 24


def validate_scan_config(raw) -> tuple[dict | None, str | None]:
    """algorithm.scan (M12) — ScanSpec khai báo cho scan-interpreter.

    LLM chỉ CẤU HÌNH việc quét (enum đóng: seed/compare/update/marking/stop
    + dãy số của đề); interpreter tất định (frontend core/scan.ts, mirror
    scan_engine.py) sở hữu vòng lặp/thứ tự/điểm dừng/kết quả (R0).
    """
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    from app.simulation.scan_engine import validate_scan_spec

    return validate_scan_spec(raw)


def validate_encapsulation_config(raw) -> tuple[dict | None, str | None]:
    """network.protocol_encapsulation (M10-AI-ROUTE) — bề mặt config v1 NHỎ.

    LLM chỉ được điền nhãn ngữ cảnh: payloadLabel + appProtocol (+ notes).
    Mô hình 4 tầng TCP/IP, 9 bước, PDU, timeline — engine frontend tất định
    sở hữu toàn bộ (khớp validateEncapConfig trong frontend encap.ts: mọi
    field optional, có mặc định an toàn).
    """
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    engine_owned = _ENCAP_OWNED_BY_ENGINE.intersection(raw.keys())
    if engine_owned:
        return None, (
            f"Config chứa khóa ngoài hợp đồng v1: {', '.join(sorted(engine_owned))}. "
            "Mô hình tầng giao thức và PDU do engine tất định sở hữu — "
            "chỉ điền payloadLabel/appProtocol/notes."
        )

    payload = raw.get("payloadLabel")
    if payload is not None and not isinstance(payload, str):
        return None, '"payloadLabel" phải là chuỗi.'
    payload = (payload or "").strip() or "Dữ liệu ứng dụng"
    if len(payload) > _ENCAP_PAYLOAD_MAX:
        return None, f'"payloadLabel" tối đa {_ENCAP_PAYLOAD_MAX} ký tự.'

    proto = raw.get("appProtocol")
    if proto is not None and not isinstance(proto, str):
        return None, '"appProtocol" phải là chuỗi.'
    proto = (proto or "").strip() or None
    if proto and len(proto) > _ENCAP_PROTOCOL_MAX:
        return None, f'"appProtocol" tối đa {_ENCAP_PROTOCOL_MAX} ký tự.'

    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {"payloadLabel": payload, "appProtocol": proto, "notes": notes}, None


# ── Domain web (W4B-2Z) — thuộc tính trình bày CÓ RÀNG BUỘC ───

# Bảng màu GỢI Ý — ô bấm nhanh trên giao diện, KHÔNG còn là toàn bộ miền hợp lệ.
# Mirror ở `frontend/src/simulations/domains/web/props.ts` (kiểm hai tầng).
_WEB_BG_COLORS = ("#ffffff", "#fde68a", "#fca5a5", "#a7f3d0", "#bfdbfe", "#e9d5ff", "#1f2937")
_WEB_TEXT_COLORS = ("#1f2937", "#b91c1c", "#1d4ed8", "#047857", "#ffffff")

# M20 W5 §2 — MIỀN MÀU LÀ 24 BIT, KHÔNG PHẢI BẢY Ô.
#
# Bài học của T12.CD4 là "ba kênh R, G, B quyết định màu, và quan hệ đó hiện ra
# trong CSS". Bảng bảy ô không dạy được điều đó: học sinh chọn "Xanh dương nhạt"
# rồi không biết vì sao nó xanh, và không có cách nào giữ hai kênh cố định để
# xem kênh thứ ba làm gì. Muốn có vòng lặp "đổi một biến → quan sát quan hệ" thì
# miền phải liên tục trên từng kênh.
#
# ⚠️ VẪN ĐÓNG — và đây là ranh giới an toàn, không phải chi tiết:
# miền mở rộng đúng bằng tập chuỗi khớp `^#[0-9a-f]{6}$`, tức chỉ có thể là MỘT
# MÀU. Không phải "CSS tự do": không hàm, không `url()`, không `expression`,
# không dấu chấm phẩy để thoát ra khai báo khác. Nới sang "chuỗi màu CSS bất kỳ"
# (`red`, `rgb(...)`, `var(--x)`) sẽ mở đúng cánh cửa mà tập đóng đang giữ.
_WEB_HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$", re.IGNORECASE)
# W4B-3F — TRANG CÓ CẤU TRÚC, KHÔNG CÒN MỘT KHỐI.
#
# Trước wave này miền chỉ mô tả MỘT khối chữ, nên bài "HTML/CSS" không có gì để
# nói về quan hệ THẺ ↔ HIỂN THỊ — thứ mà `html_css` (T12 CĐ4) thật sự dạy. Một
# div không có tổ tiên, không có anh em, và bảng CSS chỉ ra đúng một luật.
#
# Nay trang có `h1` và `p` nằm trong một khung, nên:
#   - sân khấu ĐỌC RA là một trang web, không phải một ô trôi giữa khoảng trống;
#   - bảng CSS có BA bộ chọn thật (`.page`, `.page h1`, `.page p`);
#   - đổi cỡ chữ tiêu đề và cỡ chữ đoạn văn là hai việc khác nhau — đó chính là
#     bài học về phân cấp.
# Vẫn ĐÓNG hoàn toàn: thêm hai thuộc tính, không mở thêm một đường tự do nào.
_WEB_NUMERIC = {
    "fontSize": (12, 48),        # .page p
    "headingSize": (16, 56),     # .page h1
    "padding": (0, 48),
    "borderRadius": (0, 40),
}
# Mặc định phải TRÙNG với `props.ts::DEFAULT_STYLE` — không chỉ cho gọn: mẫu
# offline chỉ đi qua validate FE, đề thật đi qua cả hai; hai bảng mặc định lệch
# nhau nghĩa là CÙNG một config cho ra hai khối trông khác nhau.
# Chọn nền xanh nhạt + cỡ chữ 20 (thay vì trắng/16) để khối MẶC ĐỊNH ĐÃ nhìn
# thấy được trên nền trang — bắt đầu bằng một khối trắng vô hình thì thao tác
# đầu tiên của học sinh là đi tìm đối tượng, không phải quan sát.
_WEB_DEFAULT_STYLE = {
    "backgroundColor": "#bfdbfe", "color": "#1f2937",
    "headingColor": "#1f2937", "headingSize": 28,
    "fontSize": 20, "padding": 16, "borderRadius": 8,
}
_WEB_CONTENT_MAX = 120
# Đoạn văn dài hơn tiêu đề — nhưng vẫn ĐÓNG, không phải ô nhập tự do.
_WEB_PARAGRAPH_MAX = 240


def validate_web_style_config(raw) -> tuple[dict | None, str | None]:
    """web.style_model — nội dung một dòng + năm thuộc tính trình bày.

    FAIL-CLOSED theo cả hai chiều: khoá lạ bị từ chối (không im lặng bỏ qua) và
    giá trị ngoài miền bị từ chối (không kẹp về biên). Kẹp im lặng sẽ dạy học
    sinh một điều SAI: rằng em đã đặt được giá trị đó.

    Khoá thiếu thì điền mặc định — nhờ vậy config LUÔN mang đủ năm thuộc tính,
    và `EXPLICIT_TARGET_OPERATIONS` mới nói đúng rằng spec biểu diễn cả năm.
    """
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden

    heading = raw.get("heading")
    if not isinstance(heading, str) or not heading.strip():
        return None, '"heading" phải là chuỗi không rỗng (tiêu đề trang).'
    if len(heading) > _WEB_CONTENT_MAX:
        return None, f'"heading" tối đa {_WEB_CONTENT_MAX} ký tự.'

    paragraph = raw.get("paragraph", "")
    if not isinstance(paragraph, str):
        return None, '"paragraph" phải là chuỗi.'
    if len(paragraph) > _WEB_PARAGRAPH_MAX:
        return None, f'"paragraph" tối đa {_WEB_PARAGRAPH_MAX} ký tự.'

    style = raw.get("style", {})
    if style is None:
        style = {}
    if not isinstance(style, dict):
        return None, '"style" phải là đối tượng.'

    out = dict(_WEB_DEFAULT_STYLE)
    for key, value in style.items():
        if key in ("backgroundColor", "color", "headingColor"):
            # Chuẩn hoá về CHỮ THƯỜNG để hai tầng so sánh được từng byte: "#FF0000"
            # và "#ff0000" là một màu, nhưng là hai chuỗi — và mọi test đối chiếu
            # ở đây đều so chuỗi.
            if not isinstance(value, str) or not _WEB_HEX_COLOR.match(value):
                return None, (
                    f'"{key}" phải là mã màu 6 chữ số hex dạng "#rrggbb" '
                    f'(ví dụ "#ff0000"). Không nhận tên màu, rgb(...) hay biến CSS.'
                )
            value = value.lower()
        elif key in _WEB_NUMERIC:
            lo, hi = _WEB_NUMERIC[key]
            if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
                return None, f'"{key}" phải là số nguyên trong [{lo}, {hi}].'
        else:
            return None, (
                f'Thuộc tính "{key}" không được hỗ trợ. '
                f'Chỉ có: {", ".join(sorted(_WEB_DEFAULT_STYLE))}.'
            )
        out[key] = value

    notes = raw.get("notes") if isinstance(raw.get("notes"), str) and raw.get("notes") else None
    return {
        "heading": heading.strip(),
        "paragraph": paragraph.strip(),
        "style": out,
        "notes": notes,
    }, None


def web_style_domain() -> dict:
    """MIỀN GIÁ TRỊ dạng máy-đọc của `web.style_model` — nguồn CANONICAL.

    Đi ra `capability_descriptors()` để frontend cross-lock được từng giá trị
    (`web-contract-parity.test.ts`), thay vì hai bảng viết tay trôi độc lập.

    Vì sao vẫn là MIRROR chứ không phải import thẳng: descriptor là artifact
    TEST/GENERATED, production FE không import nó (quyết định M14 §C4 điểm 6).
    Nên hợp đồng ở đây là NGUỒN, `props.ts` là bản sao, và sync-lock chứng minh
    hai bên khớp TỪNG GIÁ TRỊ — quên đồng bộ là ĐỎ, không phải trôi âm thầm.
    """
    return {
        # Đổi tên nghĩa từ W5: đây là ô GỢI Ý trên giao diện, không phải toàn bộ
        # miền hợp lệ. Miền thật là `color_pattern` bên dưới.
        "background_colors": list(_WEB_BG_COLORS),
        "text_colors": list(_WEB_TEXT_COLORS),
        "color_pattern": _WEB_HEX_COLOR.pattern,
        "color_channels": ["r", "g", "b"],
        "channel_bounds": {"min": 0, "max": 255},
        "numeric_bounds": {k: {"min": lo, "max": hi} for k, (lo, hi) in _WEB_NUMERIC.items()},
        "defaults": dict(_WEB_DEFAULT_STYLE),
        "content_max_length": _WEB_CONTENT_MAX,
        "paragraph_max_length": _WEB_PARAGRAPH_MAX,
    }
