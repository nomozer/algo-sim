"""Validator config THEO DOMAIN — chốt chặn bắt buộc trước khi phát hành
SimulationEnvelope (M3 §6).

Lõi không giả định mọi simulation có array/target/condition/order/timeline
(M3 §9): mỗi domain tự định nghĩa validator cho schema riêng của mình;
thêm domain mới = thêm một validator, không sửa lõi.
"""

from __future__ import annotations

ALGORITHM_IDS = [
    "find_max",
    "find_min",
    "sum_if",
    "count_if",
    "linear_search",
    "binary_search",
    "bubble_sort",
    "insertion_sort",
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
    if algorithm_id in ("bubble_sort", "insertion_sort"):
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
