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
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.persistence.db import (
    SessionLocal,
    SimulationCache,
    SimulationPattern,
    bump_metric,
    db_dialect,
    init_db,
    read_metrics,
)
from app.simulation.dsl.manifest import DSL_VERSION, MANIFEST, SUPPORTED_VERSIONS
from app.simulation.patterns import DbPatternStore
from app.ai.edit import edit_simulation
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
# "4": M7.13B — siết định nghĩa "relational" trong analyze (chống nhiễu role
#      phá pattern matching); cache chuyển sang simulation_cache version-aware.
# "5": M7.14C — 8 gap role dẫn xuất (geometric_*/threshold/orbit/freealgo) +
#      analyze/classify policy đổi → đề từng cache có thể đổi phán quyết.
# "6": M8-PRE (S2) — edge có "directed" + node_type mở rộng (actor/process/
#      data_store/input/output) + analyze/classify hỗ trợ sơ đồ hệ thống thông tin.
#      Đề "phân tích hệ thống" TỪNG bị unsupported nay mô phỏng được → phải
#      invalidate cache cũ, nếu không phán quyết cũ sẽ kẹt lại vĩnh viễn.
# "7": M10-AI-ROUTE — network.protocol_encapsulation vào CATALOG (menu classify
#      đổi): đề đóng gói qua tầng TỪNG bị unsupported/định tuyến nhầm nay có
#      module chuyên biệt → invalidate cache cũ.
# "10": M13 — operand coherence + taxonomy arbitrary_algorithm mở rộng +
#       result_ownership (computation-ownership gate, Task 9): đề "mô phỏng
#       thuật toán X có tên" TỪNG bị định tuyến nhầm vào generic.rule_scene
#       (dựng cảnh giả kết quả) nay gap trung thực → invalidate cache cũ.
# "12": M15 W1 — enum analyze mở rộng (positional namespaced) + analyze.md
#       khối positional + mechanism-consistency gate/reclassify (route-dependent
#       gates sau FINAL ROUTE).
CACHE_VERSION = "12"


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


class EditBody(BaseModel):
    """M7.14A: chỉnh sửa TĂNG DẦN mô phỏng generic hiện có — không full pipeline."""

    simulation_id: str
    config: dict
    instruction: str


def _cache_key(text: str) -> str:
    """M7.13B: version KHÔNG nướng vào key nữa — lưu ở CỘT (dsl_version/
    policy_version) và lọc lúc lookup. Row version cũ nhìn thấy được để
    dọn/thống kê thay vì thành rác vô hình."""
    normalized = " ".join(text.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _cache_lookup(session, key: str) -> SimulationCache | None:
    """Exact cache hit CHỈ khi version còn tương thích (version-aware)."""
    row = session.query(SimulationCache).filter_by(key=key).first()
    if row is None:
        return None
    if row.policy_version != CACHE_VERSION or row.dsl_version not in SUPPORTED_VERSIONS:
        return None  # version lệch → miss, không dùng mù (row giữ lại để dọn)
    return row


@app.get("/api/manifest")
def manifest():
    """Capability manifest DSL v1 (M7 §2) — nguồn chân lý cho primitive/rule/limit."""
    return MANIFEST


@app.get("/api/health")
def health():
    with SessionLocal() as session:
        count = session.query(SimulationCache).count()
        patterns = session.query(SimulationPattern).count()
        reuse = read_metrics(session)
    return {
        "ok": True,
        "hasKey": bool(os.getenv("GEMINI_API_KEY")),
        "cachedProblems": count,
        "patterns": patterns,
        "reuse": reuse,
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

    # Bước 2 — TẦNG 1 reuse (M7.13B): exact validated cache, version-aware.
    # Hit = 0 call LLM (tiết kiệm tối thiểu analyze + classify + simulate = 3).
    key = _cache_key(text)
    with SessionLocal() as session:
        row = _cache_lookup(session, key)
        if row:
            row.hit_count += 1
            row.last_used_at = datetime.now(timezone.utc)
            bump_metric(session, "exact_cache_hits")
            bump_metric(session, "estimated_llm_calls_saved", 3)
            session.commit()
            return {**json.loads(row.envelope_json), "cached": True, "source": "exact_cache"}

    if not api_key:
        return JSONResponse(status_code=503, content={"error": MISSING_KEY_MSG})

    # Bước 3: pipeline analyze → classify → (pattern reuse | simulate) → validate.
    # TẦNG 2 (pattern reuse) bật qua store inject — pipeline tự giới hạn nó
    # sau classify và chỉ cho generic.rule_scene.
    try:
        envelope = await run_pipeline(text, api_key, pattern_store=DbPatternStore(CACHE_VERSION))
    except Exception as err:  # pipeline thất bại sau retry → báo người dùng
        return JSONResponse(status_code=422, content={"error": str(err)})

    # M7.8: CHỈ cache kết quả THÀNH CÔNG. Không cache unsupported để tránh kẹt
    # kết quả cũ khi năng lực classify/DSL được cải thiện (chống stale).
    if envelope.get("status") == "ok":
        with SessionLocal() as session:
            src = envelope.get("source", "composed")
            bump_metric(session, "pattern_reuse_hits" if src == "pattern_reuse" else "compose_new_count")
            if src == "pattern_reuse":
                # tiết kiệm 1–3 call simulate; ước lượng bảo thủ trừ đi call adapt
                bump_metric(session, "estimated_llm_calls_saved", 1 if envelope.get("adapt_used") else 2)
            if envelope.get("reuse_fallback"):
                bump_metric(session, "fallback_after_reuse_failure")
            stale = session.query(SimulationCache).filter_by(key=key).first()
            if stale is not None:
                session.delete(stale)  # row version cũ → thay bằng kết quả mới
            session.add(
                SimulationCache(
                    key=key,
                    problem_text=text,
                    simulation_id=str(envelope.get("simulation_id", "")),
                    envelope_json=json.dumps(envelope, ensure_ascii=False),
                    dsl_version=DSL_VERSION,
                    policy_version=CACHE_VERSION,
                )
            )
            session.commit()
    return envelope


MAX_EDIT_CONFIG_BYTES = 32_768


@app.post("/api/edit")
async def edit(body: EditBody):
    """Edit nhẹ (M7.14A): spec hiện tại + yêu cầu → patch → validate → spec mới.

    KHÔNG analyze/classify/simulate. Trả:
    - {"status": "ok", "config", "patch", "note?"} — client thay config, gắn source="edited";
    - {"status": "unsupported_to_verify", "reason"} — từ chối trung thực (200,
      đây là PHÁN QUYẾT learner-facing, không phải lỗi giao thức);
    - 4xx/422 — lỗi input/patch không thành, spec hiện tại nguyên vẹn.
    Không đụng exact cache (không có problem-text key), không persist pattern.
    """
    if body.simulation_id != "generic.rule_scene":
        return JSONResponse(
            status_code=400,
            content={"error": "Chỉnh sửa tăng dần hiện chỉ hỗ trợ mô phỏng generic.rule_scene."},
        )
    instruction = body.instruction.strip()
    if not instruction:
        return JSONResponse(status_code=400, content={"error": "Yêu cầu chỉnh sửa trống."})
    if len(instruction) > 2000:
        return JSONResponse(status_code=400, content={"error": "Yêu cầu quá dài (tối đa 2000 ký tự)."})
    config_size = len(json.dumps(body.config, ensure_ascii=False).encode("utf-8"))
    if config_size > MAX_EDIT_CONFIG_BYTES:
        return JSONResponse(status_code=400, content={"error": "Config quá lớn."})

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return JSONResponse(status_code=503, content={"error": MISSING_KEY_MSG})

    try:
        result = await edit_simulation(body.config, instruction, api_key)
    except Exception as err:
        return JSONResponse(status_code=422, content={"error": str(err)})

    if result["status"] == "valid":
        return {
            "status": "ok",
            "config": result["config"],
            "patch": result["patch"],
            **({"note": result["note"]} if "note" in result else {}),
        }
    if result["status"] == "unsupported_to_verify":
        return {"status": "unsupported_to_verify", "reason": result["reason"]}
    # M7.14D: reason_code phân biệt policy.* (không hợp năng lực cảnh) với
    # structure.* (vi phạm luật DSL) — client hiển thị/xử lý khác nhau được.
    return JSONResponse(
        status_code=422,
        content={
            "error": result.get("error", "Patch không hợp lệ."),
            "reason_code": result.get("reason_code", "structure.invalid"),
        },
    )


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
