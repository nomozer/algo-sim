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

from fastapi import Cookie, FastAPI
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
from app.learner_messages import attach_learner_reason, learner_error_message
from app.runtime_identity import runtime_identity
from app.accounts import service as accounts_service
from app.accounts.policy import Role as AccountRole, entitlement_for
from app.accounts.router import router as accounts_router
from app.accounts.classroom_router import router as classroom_router
from app.persistence.classroom_models import User as AccountUser

app = FastAPI(title="AlgoSim backend", version="0.3.0")

# Dev dùng vite proxy nên CORS không bắt buộc; mở sẵn cho trường hợp gọi thẳng
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# M18 — tầng tài khoản/lớp học. Đăng ký SAU init_db để bảng có mặt trên SQLite.
app.include_router(accounts_router)
app.include_router(classroom_router)

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
# "13": M15 T11 hotfix (1 prompt-only fix, root cause chứng minh live): bề mặt
#       classify của binary_search từng khoá "dãy ĐÃ SẮP" — mâu thuẫn policy
#       normalize-not-refuse (CORRECTNESS §9) → đề chưa-sắp bị từ chối oan.
#       Vá description + classify.md 2c → invalidate cache classify cũ.
# "14": M17-Lite W1 — MỞ RỘNG 4 family bằng 4 target mới (algorithm.selection_sort,
#       binary.base_conversion, logic.boolean_dag, network.graph_traversal) +
#       classify.md 2d/2e/4c cập nhật (hex/octal → base_conversion; BFS/DFS →
#       graph_traversal đã hỗ trợ; mạch nhiều cổng/bảng chân trị → boolean_dag).
#       Menu classify (catalog_text) đổi + hai gap flip owned (select_extreme,
#       non_binary_base) → đề TỪNG bị unsupported (đổi hex, sắp xếp chọn, duyệt
#       đồ thị BFS/DFS) nay mô phỏng được → phải invalidate cache cũ. MỘT bump
#       cho toàn bộ coherent Wave 1 release (user duyệt scope, W1.E).
# "15": M17-Lite W2A — family MỚI tree_traversal (tree.traversal, duyệt cây nhị
#       phân 4 biến thể) + classify.md 2e/2f (tree vs graph traversal; thiếu cấu
#       trúc cây → unsupported, KHÔNG dựng cây mặc định). Menu classify đổi
#       (thêm target) + đề duyệt cây TỪNG unsupported/generic nay route
#       tree.traversal → invalidate cache cũ. MỘT bump cho coherent Wave 2A.
# "16": M17-RC1 §D — SEMANTIC COMPLETENESS GATE. analyze.md + ANALYZE_SCHEMA
#       thêm `requested_mechanisms` (đề hỏi mấy thao tác). Cache cũ giữ analysis
#       KHÔNG có trường này → gate không thấy gì để đối chiếu và cho qua: đúng
#       cái đề "cả 4 kiểu duyệt cây" vừa bị bắt lại lọt như cũ. Đây là lý do
#       BẮT BUỘC bump: hành vi từ chối phụ thuộc trường analyze mới.
# "17": M17-RC1 §C1 — analyze thêm `requested_operations` (danh tính YÊU CẦU là
#       OPERATION, không phải mechanism: find_max/find_min là hai việc dùng
#       chung một cơ chế). Cache cũ giữ analysis KHÔNG có trường này → cổng
#       completeness không thấy gì và cho qua: đề "tìm cả max lẫn min" lại trả
#       ok rồi bỏ im lặng một nửa. Kèm frontend HISTORY_SCHEMA_VERSION 1→2 (bỏ
#       envelope lưu trước cổng — có thể là mô phỏng nửa vời).
# "18": M17 W2B — family THỨ 10 `relational_table_query` + target
#       `database.relational_table_query`. Menu classify đổi (thêm lựa chọn) +
#       classify.md 2g (bảng vs dãy số đơn lẻ; JOIN/subquery/mutation →
#       unsupported). Đề truy vấn bảng TỪNG bị unsupported/generic nay mô phỏng
#       được → phải invalidate cache cũ.
# "19": M17 W2B-S1 — analyze thêm `requested_requirements` (yêu cầu KÈM MỤC
#       TIÊU có cấu trúc). Cache cũ giữ analysis KHÔNG có trường này → cổng
#       không phân biệt được "đếm tổ A" với "đếm tổ B", gộp thành một và trả ok
#       cho một nửa. History KHÔNG bump: hợp đồng envelope đã lưu không đổi.
# "33": 2026-08-20 — Task 4 đường sinh ngữ nghĩa. `semantic_program.md` viết lại
#       (bỏ phần schema đã cưỡng chế, giữ phần không mã hoá được) + thêm
#       `stage_semantic_program`. Bề mặt LLM và policy định tuyến đổi ⇒ analysis
#       cache cũ không còn đáng tin dưới luật mới. Bump CÓ CHỦ ĐÍCH, không phải
#       "bump cho chắc".
# "34": 2026-08-21 — route sinh ngữ nghĩa được NỐI vào `run_pipeline` (trước đó
#       `stage_semantic_program` không có một ai gọi). Thêm `stage_semantic_analyze`
#       + skill `semantic_analyze.md`, và `semantic_program.md` nay dạy ghim
#       `source_fact_id`. Bề mặt LLM đổi VÀ chính sách định tuyến đổi — đề
#       `algorithmic` từng bị `computation_gate` từ chối nay có thể đi tiếp qua
#       `execution_authority_gate`. Analysis cache cũ sinh dưới luật đó không còn
#       đáng tin.
#   35 (2026-08-23, vNext): route ngữ nghĩa NỐI THẬT vào đường sản phẩm. Trước
#       đó `main.py` gọi `run_pipeline` mà quên `semantic_route`, nên nó rơi về
#       `"off"` và `stage_semantic_program` chưa từng chạy cho người dùng thật.
#       Envelope cache cũ là kết quả của đường KHÔNG có route sinh.
CACHE_VERSION = "35"

#: Ba chế độ của route sinh ngữ nghĩa, SERVER sở hữu — không phải cờ của client,
#: không suy từ nội dung đề, không hard-code riêng bài nào.
SEMANTIC_ROUTE_MODES = ("off", "shadow", "serve")


def semantic_route_mode() -> str:
    """Chế độ route sinh ngữ nghĩa cho lượt phân tích này.

    VÌ SAO HÀM NÀY TỒN TẠI: trước vNext, `main.py` gọi `run_pipeline(text,
    api_key, pattern_store=...)` mà KHÔNG truyền `semantic_route`. Tham số ấy
    mặc định `"off"` ở `ai/pipeline.py`, nên `stage_semantic_program` **chưa bao
    giờ chạy trong sản phẩm** — mọi bài đều rơi về classifier legacy. Bài thuật
    toán không khớp module nào thì xuống `generic.rule_scene`, miền khai báo
    tĩnh: narration kể "đẩy '(' vào ngăn xếp" trong khi hình ngăn xếp rỗng.
    Cùng họ với bất biến #22 (mảnh nào cũng xanh mà chưa mảnh nào được ghép).

    Mặc định giữ `"off"`: bật là một quyết định vận hành tường minh, không phải
    tác dụng phụ của việc nâng cấp. Giá trị lạ ⇒ ép về `"off"` chứ không tạo ra
    một chế độ thứ tư im lặng.
    """
    v = os.getenv("SEMANTIC_ROUTE_MODE", "off")
    return v if v in SEMANTIC_ROUTE_MODES else "off"


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


def _consume_guest_trial(session, token: str | None) -> None:
    """Ghi nhận khách vừa tiêu một lượt. Không phải khách ⇒ no-op.

    Đặt ở đây (chứ không trong `accounts.service`) vì nó là luật của ĐIỂM VÀO
    analyze: chỉ lượt chạy RA ĐƯỢC mô phỏng mới tính.
    """
    auth = accounts_service.load_session(session, token)
    if auth is not None:
        accounts_service.consume_guest_trial(session, auth)


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
        # M17-RC1 §A — danh tính runtime để phát hiện container chạy code cũ.
        "runtime": runtime_identity(),
    }


@app.get("/api/diagnostics/runtime")
def diagnostics_runtime():
    """M17-RC1 §A — danh tính runtime máy-đọc (nguồn cho `runtime-doctor`).
    Tách khỏi /api/health để công cụ chẩn đoán không phụ thuộc DB."""
    return runtime_identity()


@app.post("/api/analyze")
async def analyze(body: AnalyzeBody, algosim_session: str | None = Cookie(default=None)):
    """M18 — CỔNG LƯỢT DÙNG THỬ ĐỨNG TRƯỚC MỌI THỨ KHÁC.

    Khách được chạy MỘT mô phỏng thật (cùng pipeline này, không phải renderer
    giả), rồi phải đăng nhập. Cổng đếm ở PHIÊN MÁY CHỦ chứ không ở localStorage:
    một cờ phía client thì xoá cache là có lượt mới.

    Đặt TRƯỚC ingestion có chủ đích — hết lượt thì không tiêu một byte xử lý ảnh
    nào, và không có đường nào chạm tới LLM.
    """
    with SessionLocal() as session:
        auth = accounts_service.load_session(session, algosim_session)
        role = None
        if auth is not None and auth.user_id is not None:
            user = session.get(AccountUser, auth.user_id)
            role = AccountRole(user.role) if user else None
        used = auth.guest_trials_used if auth is not None else 0
        ent = entitlement_for(role, guest_trials_used=used)
        if not ent.can_run_simulation:
            session.commit()
            return JSONResponse(status_code=402, content={
                "error": "Em đã dùng hết lượt mô phỏng thử. Đăng nhập để tiếp tục thực hành.",
                "reason_code": "guest_trial_exhausted",
            })
        session.commit()

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
            _consume_guest_trial(session, algosim_session)
            session.commit()
            return {**json.loads(row.envelope_json), "cached": True, "source": "exact_cache"}

    if not api_key:
        return JSONResponse(status_code=503, content={"error": MISSING_KEY_MSG})

    # Bước 3: pipeline analyze → classify → (pattern reuse | simulate) → validate.
    # TẦNG 2 (pattern reuse) bật qua store inject — pipeline tự giới hạn nó
    # sau classify và chỉ cho generic.rule_scene.
    try:
        envelope = await run_pipeline(
            text,
            api_key,
            pattern_store=DbPatternStore(CACHE_VERSION),
            # Thiếu đúng tham số này là lý do route sinh ngữ nghĩa chưa bao giờ
            # chạy trong sản phẩm — xem `semantic_route_mode()`. Khoá bởi
            # `tests/test_semantic_route_wired_to_production.py`.
            semantic_route=semantic_route_mode(),
        )
    except Exception as err:  # pipeline thất bại sau retry → báo người dùng
        # M17 W0 — học sinh thấy thông điệp thân thiện; chi tiết kỹ thuật đi
        # field riêng (FE không render, dev đọc qua devtools/log).
        return JSONResponse(
            status_code=422,
            content={"error": learner_error_message(), "error_detail": str(err)},
        )

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
    # M17 W0 — lớp trình bày: envelope unsupported mang thêm learner_reason
    # (bản sao tại biên API; envelope pipeline/eval không đổi — bất biến #22).
    # Lượt dùng thử chỉ TÍNH khi mô phỏng ra được — đề bị từ chối trung thực
    # không ăn mất lượt duy nhất của khách.
    if envelope.get("status") == "ok":
        with SessionLocal() as session:
            _consume_guest_trial(session, algosim_session)
            session.commit()
    return attach_learner_reason(envelope)


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
