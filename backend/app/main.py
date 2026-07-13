"""Backend AlgoSim — FastAPI (M3).

Hai luồng:
1. POST /api/analyze — pipeline analyze → classify → simulate → validate
   → ValidatedSimulationEnvelope (cache PostgreSQL theo đề).
2. POST /api/explain — giải thích trạng thái thật của engine (tùy chọn).

Chạy: docker compose up -d --build (key trong backend/.env: GEMINI_API_KEY=...)
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.persistence.db import Problem, SessionLocal, db_dialect, init_db
from app.simulation.dsl.manifest import MANIFEST
from app.ai.explain import explain_state
from app.ingestion.input import IngestError, ingest_to_text
from app.ai.pipeline import run_pipeline

app = FastAPI(title="AlgoSim backend", version="0.3.0")

# Dev dùng vite proxy nên CORS không bắt buộc; mở sẵn cho trường hợp gọi thẳng
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

MISSING_KEY_MSG = (
    "Máy chủ chưa cấu hình GEMINI_API_KEY. Tạo file algo-sim/backend/.env "
    "với nội dung: GEMINI_API_KEY=<key của bạn> rồi chạy lại: docker compose up -d"
)

MAX_EXPLAIN_CONTEXT_BYTES = 16_384

# Phiên bản chính sách định tuyến/DSL. Tăng số này khi thay đổi classify/manifest
# để VÔ HIỆU HÓA cache cũ (đề từng lưu với sim_id cũ sẽ được phân tích lại) — M7.9 §7.
# "3": M7.13A — drag interaction + scene-mode consistency (manifest/prompt đổi).
CACHE_VERSION = "3"


class InputPayload(BaseModel):
    """Đầu vào chuẩn hóa — M4 thêm document/code/image, contract không đổi."""

    type: Literal["text", "document", "code", "image"]
    content: str
    filename: str | None = None
    mime_type: str | None = None


class AnalyzeBody(BaseModel):
    input: InputPayload


class ExplainBody(BaseModel):
    simulation_id: str
    explain_context: dict
    question: str
    recent_history: list[dict] = []


def _cache_key(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    # Gộp CACHE_VERSION vào khóa → đổi policy là mọi entry cũ tự động "miss"
    return hashlib.sha256(f"{CACHE_VERSION}|{normalized}".encode("utf-8")).hexdigest()


@app.get("/api/manifest")
def manifest():
    """Capability manifest DSL v1 (M7 §2) — nguồn chân lý cho primitive/rule/limit."""
    return MANIFEST


@app.get("/api/health")
def health():
    with SessionLocal() as session:
        count = session.query(Problem).count()
    return {
        "ok": True,
        "hasKey": bool(os.getenv("GEMINI_API_KEY")),
        "cachedProblems": count,
        "db": db_dialect(),
    }


@app.post("/api/analyze")
async def analyze(body: AnalyzeBody):
    api_key = os.getenv("GEMINI_API_KEY")

    # Bước 1: chuẩn hóa MỌI loại input về text (M4) — sau bước này, text/docx/
    # code/image đi CHUNG một đường qua pipeline, không loại nào bypass.
    try:
        text = await ingest_to_text(
            body.input.type,
            body.input.content,
            body.input.filename,
            body.input.mime_type,
            api_key,
        )
    except IngestError as err:
        # Ảnh cần key để phiên dịch nhưng chưa cấu hình → 503 (không phải lỗi input)
        if str(err) == "__NEED_KEY__":
            return JSONResponse(status_code=503, content={"error": MISSING_KEY_MSG})
        return JSONResponse(status_code=400, content={"error": str(err)})

    if len(text) < 10:
        return JSONResponse(
            status_code=400,
            content={"error": "Nội dung đề quá ngắn — hãy nhập/chọn đầy đủ bài toán."},
        )

    # Bước 2: cache theo text đã chuẩn hóa (ảnh trùng → đề đã phiên dịch trùng)
    key = _cache_key(text)
    with SessionLocal() as session:
        row = session.query(Problem).filter_by(key=key).first()
        if row:
            return {**json.loads(row.envelope_json), "cached": True}

    if not api_key:
        return JSONResponse(status_code=503, content={"error": MISSING_KEY_MSG})

    # Bước 3: pipeline analyze → classify → simulate → validate (M3, không đổi)
    try:
        envelope = await run_pipeline(text, api_key)
    except Exception as err:  # pipeline thất bại sau retry → báo người dùng
        return JSONResponse(status_code=422, content={"error": str(err)})

    # M7.8: CHỈ cache kết quả THÀNH CÔNG. Không cache unsupported để tránh kẹt
    # kết quả cũ khi năng lực classify/DSL được cải thiện (chống stale).
    if envelope.get("status") == "ok":
        with SessionLocal() as session:
            session.add(
                Problem(key=key, problem_text=text, envelope_json=json.dumps(envelope, ensure_ascii=False))
            )
            session.commit()
    return envelope


@app.post("/api/explain")
async def explain(body: ExplainBody):
    question = body.question.strip()
    if not question:
        return JSONResponse(status_code=400, content={"error": "Câu hỏi trống."})
    if len(question) > 2000:
        return JSONResponse(status_code=400, content={"error": "Câu hỏi quá dài (tối đa 2000 ký tự)."})
    context_size = len(json.dumps(body.explain_context, ensure_ascii=False).encode("utf-8"))
    if context_size > MAX_EXPLAIN_CONTEXT_BYTES:
        return JSONResponse(
            status_code=400,
            content={"error": "explain_context quá lớn — chỉ gửi snapshot từ getExplainContext."},
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return JSONResponse(status_code=503, content={"error": MISSING_KEY_MSG})

    try:
        reply = await explain_state(
            body.simulation_id, body.explain_context, question, body.recent_history, api_key
        )
    except Exception as err:
        return JSONResponse(status_code=422, content={"error": str(err)})
    return {"reply": reply}
