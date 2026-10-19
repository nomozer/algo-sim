# -*- coding: utf-8 -*-
"""ADAPTER GEMINI FUNCTION CALLING cho đường text → geometry functions (run `ai-function-route`). Offline-first.

    đề → build_request (khai báo hàm từ REGISTRY, ANY + allowedFunctionNames, maxOutputTokens)
       → transport(payload) → body `generateContent`
       → parse_response (finishReason, functionCall song song, call_id/quotes/depends_on, trùng, phụ thuộc)
       → app/ai/function_route.run_function_route (lược đồ → cổng nguồn → engine → kiểm → Scene3D)

─── CẤU HÌNH PROVIDER — ĐÃ TRA TÀI LIỆU, KHÔNG ĐOÁN (2026-10-10) ───────────────
· `toolConfig.functionCallingConfig.mode`: ANY = "constrained to always predicting a function call only", kèm
  `allowedFunctionNames` = đúng tên trong REGISTRY ⇒ mô hình không trả lời bằng văn bản tự do, không gọi hàm lạ.
  VALIDATED ("validate function calls with constrained decoding") nhận làm nhánh ablation; AUTO/NONE bị từ chối — AUTO
  cho phép trả lời văn bản, tức đường thoát khỏi registry.
· Nhiều `functionCall` trong MỘT ứng viên (gọi song song) ⇒ cả đề trong MỘT lượt gọi API, không một mệnh đề một lượt.
  Không gửi `functionResponse` ngược lại: hàm không "chạy" phía mô hình, engine nhận cả kế hoạch một lần.
· `FunctionCall.id` là TUỲ CHỌN phía provider ⇒ `call_id` nằm trong `args` (bắt buộc trong khai báo).
· Lược đồ tham số: tập con OpenAPI (Type viết hoa, `nullable`, `enum`, `pattern`, `minItems`…), không `$ref`/`anyOf`.
· finishReason: STOP ⇒ đọc; MAX_TOKENS ⇒ RESPONSE_TRUNCATED (kế hoạch cụt KHÔNG thực thi); MALFORMED_FUNCTION_CALL;
  mọi lý do khác (SAFETY, RECITATION, TOO_MANY_TOOL_CALLS, …) ⇒ PROVIDER_REFUSED.
Nguồn: ai.google.dev/api/caching (FunctionCallingConfig, Mode), ai.google.dev/api/generate-content (FinishReason,
UsageMetadata), proto generativelanguage v1beta (FunctionDeclaration, FunctionCall, Schema).

─── KHÔNG LÙI VỀ LLM_ONLY, KHÔNG GỌI MẠNG KHI CHƯA BẬT ─────────────────────────
Module không nhập `pipeline`/`gemini`/`httpx` ở đầu tệp. `live_transport` chỉ gửi khi `ALLOW_LIVE_AI=1` trong tiến
trình, khoá đi trong header `x-goog-api-key` (không trong URL — bài học pilot G05: URL có khoá lọt vào log httpx).
Lượt này KHÔNG gọi nó: mọi test dùng provider giả.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable

from app.ai.function_route import run_function_route
from app.simulation.geometry_functions import PROVIDER_FUNCTIONS, REGISTRY, KetQuaTuyen, function_declarations

MODES = ("ANY", "VALIDATED")
#: Trần output gồm cả thinking (tài liệu Gemini) — trần TOKEN CỨNG mỗi lượt, bài học R1 của pilot G05. Cần đo lại.
MAX_OUTPUT_TOKENS = 8192
TEMPERATURE = 0.0

SYSTEM_PROMPT = (
    "Bạn đọc một đề hình học không gian và CHỈ được gọi các hàm dựng hình đã cung cấp.\n"
    "1. Đọc từng mệnh đề. Mỗi dữ kiện, mỗi phép dựng, mỗi câu hỏi ⇒ một lời gọi hàm. Gọi TẤT CẢ trong một lượt trả lời.\n"
    "2. `quotes`: chép NGUYÊN VĂN các đoạn đề làm căn cứ cho lời gọi; không diễn đạt lại, không thêm số.\n"
    "3. Không thêm dữ kiện đề không nói, không suy hệ quả. Điều phải chứng minh, mệnh đề 'nếu … thì', câu phủ định "
    "KHÔNG phải dữ kiện.\n"
    "4. Mệnh đề không có hàm phù hợp ⇒ gọi `unsupported` với lý do.\n"
    "5. `call_id` dạng c1, c2, …; `depends_on` liệt kê các lời gọi tạo ra điểm/khối mà lời gọi này dùng.\n"
    "6. Không viết toạ độ, không viết mã."
)

_KIEU = {"string": "STRING", "integer": "INTEGER", "number": "NUMBER", "boolean": "BOOLEAN", "array": "ARRAY",
         "object": "OBJECT"}
_GIU = ("description", "enum", "required", "minItems", "maxItems", "pattern", "minLength", "maxLength", "nullable")


class LiveAIDisabled(RuntimeError):
    """`live_transport` được gọi khi tiến trình chưa bật `ALLOW_LIVE_AI=1`."""


class _TuChoiAI(Exception):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(code)
        self.code, self.reason = code, reason


def _openapi(node: Any, defs: dict[str, Any]) -> Any:
    """JSON Schema (Pydantic) → tập con OpenAPI của Gemini: giải `$ref`, `anyOf[X, null]` → X + nullable, Type viết hoa,
    bỏ `title`/`default`/`additionalProperties`."""
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        return _openapi(defs[node["$ref"].rsplit("/", 1)[-1]], defs)
    if "anyOf" in node:
        khac = [x for x in node["anyOf"] if x.get("type") != "null"]
        if len(khac) != 1:
            raise ValueError("anyOf nhiều nhánh không biểu diễn được trong tập con OpenAPI")
        ra = _openapi(khac[0], defs)
        ra["nullable"] = True
        if "description" in node:
            ra["description"] = node["description"]
        return ra
    ra: dict[str, Any] = {"type": _KIEU[node["type"]]}
    for k in _GIU:
        if k in node:
            ra[k] = node[k]
    if "items" in node:
        ra["items"] = _openapi(node["items"], defs)
    if "properties" in node:
        ra["properties"] = {k: _openapi(v, defs) for k, v in node["properties"].items()}
    return ra


def gemini_function_declarations() -> list[dict[str, Any]]:
    """Một `FunctionDeclaration` cho MỖI hàm của REGISTRY — dẫn xuất từ `function_declarations()`, không gõ tay."""
    ra = []
    for d in function_declarations():
        p = d["parameters"]
        ra.append({"name": d["name"], "description": d["description"],
                   "parameters": _openapi({k: v for k, v in p.items() if k != "$defs"}, p.get("$defs", {}))})
    return ra


def build_request(problem_text: str, mode: str = "ANY") -> dict[str, Any]:
    """Payload `generateContent` cho MỘT lượt gọi: cả đề, mọi khai báo hàm, ép gọi hàm trong REGISTRY."""
    if mode not in MODES:
        raise ValueError(f"mode {mode!r} không được phép (chỉ {MODES}) — AUTO cho phép trả lời văn bản ngoài registry")
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": f'Đề bài:\n"""\n{problem_text}\n"""'}]}],
        "tools": [{"functionDeclarations": gemini_function_declarations()}],
        "toolConfig": {"functionCallingConfig": {"mode": mode, "allowedFunctionNames": sorted(PROVIDER_FUNCTIONS)}},
        "generationConfig": {"temperature": TEMPERATURE, "maxOutputTokens": MAX_OUTPUT_TOKENS},
    }


def surface_fingerprint() -> str:
    """Vân tay bề mặt mô hình của đường mới (prompt + khai báo hàm + cấu hình) — ghi vào mọi báo cáo đo."""
    p = build_request("", "ANY")
    p.pop("contents")
    return hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def parse_response(body: Any, diag: dict[str, Any]) -> dict[str, Any]:
    """Thân phản hồi → `{"calls": [...]}`. Không thực thi gì. Hỏng ⇒ `_TuChoiAI` có mã; `diag` được điền dần."""
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
    cand = cands[0]
    diag["finish_reason"] = finish = cand.get("finishReason")
    if finish == "MAX_TOKENS":
        raise _TuChoiAI("RESPONSE_TRUNCATED", "phản hồi bị cắt ở trần token — kế hoạch có thể thiếu lời gọi, không thực thi")
    if finish == "MALFORMED_FUNCTION_CALL":
        raise _TuChoiAI("MALFORMED_FUNCTION_CALL", "provider báo lời gọi hàm hỏng")
    if finish not in (None, "STOP"):
        raise _TuChoiAI("PROVIDER_REFUSED", f"finishReason = {finish}")
    content = cand.get("content") or {}
    if not isinstance(content, dict) or not isinstance(content.get("parts", []), list):
        raise _TuChoiAI("MALFORMED_RESPONSE_PART", "content.parts phải là danh sách")
    parts = content.get("parts") or []
    if any(not isinstance(p, dict) or "functionCall" in p and not isinstance(p["functionCall"], dict) for p in parts):
        raise _TuChoiAI("MALFORMED_RESPONSE_PART", "functionCall phải là đối tượng JSON")
    fcs = [p["functionCall"] for p in parts if isinstance(p, dict) and isinstance(p.get("functionCall"), dict)]
    diag["n_calls"] = len(fcs)
    if not fcs:
        raise _TuChoiAI("NO_FUNCTION_CALL", "mô hình không gọi hàm nào")
    calls, da_co = [], {}
    for fc in fcs:
        if not isinstance(fc.get("args", {}), dict):
            raise _TuChoiAI("MALFORMED_RESPONSE_PART", "functionCall.args phải là đối tượng JSON")
        if (spec := REGISTRY.get(fc.get("name"))) is not None and not spec.provider_offered:
            raise _TuChoiAI("FUNCTION_NOT_OFFERED", f"hàm {fc.get('name')!r} không được mời cho tuyến A (chỉ planner nhánh B)")
        args = dict(fc.get("args", {}))
        cid = args.pop("call_id", None)
        if not isinstance(cid, str) or not cid.strip():
            raise _TuChoiAI("CALL_ID_MISSING", f"lời gọi {fc.get('name')!r} thiếu call_id")
        quotes = args.pop("quotes", None)
        call = {"id": cid, "fn": fc.get("name"), "args": args,
                "source": {"quotes": quotes} if quotes is not None else {}, "depends_on": args.pop("depends_on", None) or []}
        khoa = json.dumps(call, ensure_ascii=False, sort_keys=True)
        if cid in da_co:
            if da_co[cid] != khoa:
                raise _TuChoiAI("DUPLICATE_CALL_ID", f"hai lời gọi khác nhau cùng call_id {cid!r}")
            diag["dropped_identical_duplicates"] += 1            # lời gọi y hệt lặp lại: bỏ, ghi lại
            continue
        da_co[cid] = khoa
        calls.append(call)
    return {"calls": calls}


def run_ai_function_route(problem_text: str, transport: Callable[[dict[str, Any]], Any], mode: str = "ANY") -> KetQuaTuyen:
    """Đề → MỘT lượt gọi provider (qua `transport`) → lời gọi hàm → engine → Scene3D. Mọi hỏng hóc ⇒ REFUSED có mã."""
    diag: dict[str, Any] = {"mode": mode, "model_calls": 1, "n_calls": 0, "dropped_identical_duplicates": 0,
                            "usage": {}, "finish_reason": None, "surface": surface_fingerprint()}
    payload = build_request(problem_text, mode)
    try:
        body = transport(payload)
    except LiveAIDisabled as e:
        return KetQuaTuyen("REFUSED", "LIVE_AI_DISABLED", str(e), ai=diag)
    except Exception as e:  # noqa: BLE001 — lỗi provider/mạng: từ chối có mã, không lùi về đường khác
        return KetQuaTuyen("REFUSED", "PROVIDER_ERROR", type(e).__name__, ai=diag)
    try:
        plan = parse_response(body, diag)
    except _TuChoiAI as e:
        return KetQuaTuyen("REFUSED", e.code, e.reason, ai=diag)
    r = run_function_route(problem_text, plan)
    r.ai = diag
    return r


class ProviderHTTPError(RuntimeError):
    """HTTP failure with recoverable JSON metadata; credentials/body are not included in the exception message."""

    def __init__(self, status_code: int, body: Any) -> None:
        super().__init__(f"Gemini HTTP {status_code}")
        self.status_code, self.body = status_code, body


def live_transport(api_key: str, model: str | None = None, timeout_seconds: float = 60.0) -> Callable[[dict], dict]:
    """Transport THẬT (không dùng trong lượt này). Kiểm `ALLOW_LIVE_AI` ở MỖI lần gửi; khoá trong header; ghi `ApiBudget`
    và `usageMetadata` như `gemini.call_gemini` để trần ngân sách của bộ đo áp được."""
    def gui(payload: dict) -> dict:
        if os.environ.get("ALLOW_LIVE_AI") != "1":
            raise LiveAIDisabled("ALLOW_LIVE_AI != 1 — không gửi request thật")
        import httpx

        from app.ai import gemini
        from app.ai.telemetry import record_usage

        if gemini.BUDGET:
            gemini.BUDGET.note_call()
            gemini.BUDGET.note_request(is_retry=False)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or gemini.MODEL}:generateContent"
        res = httpx.post(url, json=payload, headers={"x-goog-api-key": api_key}, timeout=timeout_seconds)
        if res.status_code != 200:
            try:
                error_body = res.json()
            except ValueError:
                error_body = None  # Raw HTML/text may contain credentials: do not retain it.
            raise ProviderHTTPError(res.status_code, error_body)
        body = res.json()
        record_usage("function_calling", body.get("usageMetadata") if isinstance(body, dict) else None)
        return body

    return gui
