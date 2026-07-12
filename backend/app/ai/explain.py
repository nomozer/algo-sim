"""Kênh giải thích trạng thái (M3 §7) — thay tutor flow cũ.

AI chỉ GIẢI THÍCH trạng thái thật của engine (explain_context đến từ
module.getExplainContext phía frontend). Không step_status, không lệnh
điều khiển, không thay đổi state — engine là nguồn chân lý duy nhất.
"""

from __future__ import annotations

import json

from app.ai.gemini import call_gemini, load_skill

EXPLAIN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reply": {"type": "STRING"},
    },
    "required": ["reply"],
}


async def explain_state(
    simulation_id: str,
    explain_context: dict,
    question: str,
    recent_history: list[dict],
    api_key: str,
) -> str:
    history_text = "\n".join(
        f'{"Người học" if h.get("role") == "user" else "Trợ giúp"}: {h.get("text", "")}'
        for h in recent_history[-8:]
    )
    user = (
        f"MÔ PHỎNG ĐANG XEM: {simulation_id}\n\n"
        f"TRẠNG THÁI HIỆN TẠI (explain_context từ engine):\n"
        f"{json.dumps(explain_context, ensure_ascii=False)}\n\n"
        f"HỘI THOẠI GẦN NHẤT:\n{history_text or '(chưa có)'}\n\n"
        f"NGƯỜI HỌC HỎI: {question}"
    )
    raw = await call_gemini(api_key, load_skill("explain"), user, EXPLAIN_SCHEMA, 0.4)
    try:
        parsed = json.loads(raw)
        reply = parsed.get("reply") if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        reply = raw
    return str(reply or "")[:2000]
