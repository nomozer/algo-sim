# -*- coding: utf-8 -*-
"""ADAPTER TRÍCH DỮ KIỆN CÓ KIỂU (nhánh B thực nghiệm, run `hybrid-compiler-selection`). Offline-first.

    đề → build_request (structured output: responseMimeType JSON + responseSchema = TypedFact[], KHÔNG `tools`)
       → transport(payload) → body `generateContent` → parse_response (finishReason, JSON) → run_fact_route

Khác nhánh A (`function_calling.py`): mô hình KHÔNG thấy thư viện hàm; nó chỉ đọc đề và điền dữ kiện (đối tượng, quan hệ, giá trị,
vai trò mệnh đề, phủ định, nguồn). Chọn và kết hợp hàm là việc của planner tất định. Tái dùng của nhánh A: bộ chuyển lược đồ
`_openapi`, trần `MAX_OUTPUT_TOKENS`, `live_transport` (cổng `ALLOW_LIVE_AI`, khoá trong header — KHÔNG dùng ở lượt này).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from app.ai.function_calling import MAX_OUTPUT_TOKENS, TEMPERATURE, LiveAIDisabled, _openapi
from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions import KetQuaTuyen
from app.simulation.geometry_functions.planner import TypedFact

SYSTEM_PROMPT = (
    "Bạn đọc một đề hình học không gian và CHỈ trích dữ kiện theo lược đồ; KHÔNG chọn phép dựng, KHÔNG tính.\n"
    "1. Mỗi mệnh đề ⇒ một dữ kiện: khối, hình dạng đa giác, góc vuông, độ dài, hai đoạn bằng nhau, vuông góc, đường cao, "
    "hình chiếu, điểm định nghĩa (trung điểm/trọng tâm/giao điểm), thiết diện, giao tuyến, câu hỏi.\n"
    "2. `role`: premise (đề cho) · prove (điều phải chứng minh) · condition (trong 'nếu … thì') · question (đề hỏi).\n"
    "3. Mệnh đề phủ định ⇒ `negated = true`. Không chắc cách hiểu ⇒ `ambiguous = true`; không đoán.\n"
    "4. `quotes`: chép NGUYÊN VĂN đoạn đề; không thêm số, không suy hệ quả, không thêm dữ kiện đề không nói.\n"
    "5. Độ dài: `measure` = segment (đoạn có tên) · base_edge · lateral_edge · height · edge (mọi cạnh); giữ ký hiệu a.\n"
    "6. Không viết toạ độ, không viết mã. Giao điểm: point_def, point_kind = intersect_line_line hoặc "
    "intersect_line_plane, point = tên giao điểm, points_a = hai điểm đường thẳng, points_b = đường hoặc mặt. "
    "Hình chiếu: projection, point = điểm gốc, at = ảnh, points = hai điểm đường hoặc ít nhất ba điểm mặt.\n"
    "7. Thiết diện: section, solid = khối, points = ba điểm của mặt cắt. Giao tuyến: intersection_line, points_a / points_b = "
    "ba điểm của mỗi mặt. Diện tích thiết diện: question, quantity = area, solid + points = ba điểm mặt cắt.\n"
    "8. Mặt cắt cho bằng quan hệ ('(P) đi qua M và song song với (ABCD)'): KHÔNG có points; point = điểm đi qua, "
    "points_b = các điểm của mặt kia, plane_relation = parallel (vuông góc ⇒ perpendicular); quotes gồm cả mệnh đề định "
    "nghĩa mặt và mệnh đề thiết diện. Không tự đặt tên điểm cho mặt ấy."
)


class _TuChoiAI(Exception):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(code)
        self.code, self.reason = code, reason


def facts_response_schema() -> dict[str, Any]:
    sch = TypedFact.model_json_schema()
    item = _openapi({k: v for k, v in sch.items() if k != "$defs"}, sch.get("$defs", {}))
    return {"type": "OBJECT", "properties": {"facts": {"type": "ARRAY", "items": item}}, "required": ["facts"]}


def build_request(problem_text: str) -> dict[str, Any]:
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": f'Đề bài:\n"""\n{problem_text}\n"""'}]}],
        "generationConfig": {"temperature": TEMPERATURE, "maxOutputTokens": MAX_OUTPUT_TOKENS,
                             "responseMimeType": "application/json", "responseSchema": facts_response_schema()},
    }


def surface_fingerprint() -> str:
    p = build_request("")
    p.pop("contents")
    return hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def parse_response(body: Any, diag: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise _TuChoiAI("PROVIDER_RESPONSE_INVALID", "thân phản hồi không phải đối tượng JSON")
    diag["usage"] = body.get("usageMetadata") or {}
    cands = body.get("candidates") or []
    if not isinstance(cands, list) or cands and not isinstance(cands[0], dict):
        raise _TuChoiAI("MALFORMED_RESPONSE_PART", "candidates phải là danh sách đối tượng")
    if not cands:
        if (body.get("promptFeedback") or {}).get("blockReason"):
            raise _TuChoiAI("PROVIDER_BLOCKED", f"đề bị chặn: {body['promptFeedback']['blockReason']}")
        raise _TuChoiAI("NO_CANDIDATE", "phản hồi không có ứng viên")
    diag["finish_reason"] = finish = cands[0].get("finishReason")
    if finish == "MAX_TOKENS":
        raise _TuChoiAI("RESPONSE_TRUNCATED", "phản hồi bị cắt ở trần token — danh sách dữ kiện có thể thiếu")
    if finish not in (None, "STOP"):
        raise _TuChoiAI("PROVIDER_REFUSED", f"finishReason = {finish}")
    content = cands[0].get("content") or {}
    if not isinstance(content, dict) or not isinstance(content.get("parts", []), list):
        raise _TuChoiAI("MALFORMED_RESPONSE_PART", "content.parts phải là danh sách")
    parts = content.get("parts") or []
    if any(not isinstance(p, dict) or not isinstance(p.get("text", ""), str) for p in parts):
        raise _TuChoiAI("MALFORMED_RESPONSE_PART", "content.parts.text phải là chuỗi")
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise _TuChoiAI("JSON_INVALID", f"đầu ra không phải JSON ({e.msg})") from None
    if not isinstance(data, dict):
        raise _TuChoiAI("JSON_INVALID", "đầu ra không phải đối tượng JSON")
    if not isinstance(data.get("facts", []), list):
        raise _TuChoiAI("MALFORMED_RESPONSE_PART", "facts phải là danh sách")
    diag["n_facts"] = len(data.get("facts") or [])
    return data


def run_ai_fact_route(problem_text: str, transport: Callable[[dict[str, Any]], Any]) -> KetQuaTuyen:
    """Đề → MỘT lượt gọi provider → dữ kiện có kiểu → planner → engine → Scene3D. Hỏng ⇒ REFUSED có mã; không lùi về LLM_ONLY."""
    diag: dict[str, Any] = {"model_calls": 1, "n_facts": 0, "usage": {}, "finish_reason": None,
                            "surface": surface_fingerprint()}
    try:
        body = transport(build_request(problem_text))
    except LiveAIDisabled as e:
        return KetQuaTuyen("REFUSED", "LIVE_AI_DISABLED", str(e), ai=diag)
    except Exception as e:  # noqa: BLE001
        return KetQuaTuyen("REFUSED", "PROVIDER_ERROR", type(e).__name__, ai=diag)
    try:
        data = parse_response(body, diag)
    except _TuChoiAI as e:
        return KetQuaTuyen("REFUSED", e.code, e.reason, ai=diag)
    r = run_fact_route(problem_text, data)
    r.ai = diag
    return r
