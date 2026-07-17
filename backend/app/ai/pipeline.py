"""Pipeline LLM (M3): analyze → classify → simulate → validate → envelope.

Ranh giới cứng: LLM chỉ trích xuất, phân loại và điền CONFIG đầu vào.
Timeline/diễn biến/kết quả do engine tất định phía frontend sinh ra.
SimulationEnvelope hợp lệ CHỈ được phát hành sau server-side validation —
không bao giờ trả thẳng JSON của Gemini cho frontend (M3 §6).
"""

from __future__ import annotations

import json

from app.simulation.catalog import CATALOG, catalog_text
from app.simulation.computation_gate import check_computation_ownership
from app.simulation.dsl.manifest import manifest_capability_summary
from app.simulation.patterns import (
    deterministic_fill,
    instantiate,
    run_gates,
    validate_params,
)
from app.simulation.representation import (
    build_representation_plan,
    check_scene_consistency,
    required_roles,
    scene_mode_guidance,
)
from app.simulation.semantic import check_semantic_compatibility, check_system_flow_consistency
from app.ai.gemini import call_gemini, load_skill

# ── Schema structured output từng stage ───────────────────────

ANALYZE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "objects": {"type": "ARRAY", "items": {"type": "STRING"}},
        "data": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "values": {"type": "ARRAY", "items": {"type": "NUMBER"}, "nullable": True},
                    "labels": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
                },
                "required": ["description"],
            },
        },
        "relations": {"type": "ARRAY", "items": {"type": "STRING"}},
        "processes": {"type": "ARRAY", "items": {"type": "STRING"}},
        "constraints": {"type": "ARRAY", "items": {"type": "STRING"}},
        "goal": {"type": "STRING"},
        "input_description": {"type": "STRING"},
        "output_description": {"type": "STRING"},
        # M7.9: năng lực đề CẦN — để classify đối chiếu với năng lực từng mô phỏng
        "required_capabilities": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        # "step_by_step" = cảnh được DỰNG/HÌNH THÀNH dần; "prebuilt" = cảnh cho sẵn
        "scene_construction": {
            "type": "STRING",
            "enum": ["prebuilt", "step_by_step"],
            "nullable": True,
        },
        # M7.11: SEMANTIC REQUIREMENTS — vai trò ngữ nghĩa đề cần (taxonomy:
        # structural/textual/logical/numeric/interactive/relational/movement/temporal)
        "entity_roles": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "relation_roles": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "process_roles": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "interaction_needs": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "visual_needs": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "temporal_needs": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        # M13: nguồn kết quả cuối của bài — SERVER dùng để chặn "AI tự giải rồi
        # dựng cảnh minh hoạ đáp án" (computation-ownership gate). Bắt buộc +
        # fail-closed: xem app/simulation/computation_gate.py.
        "result_ownership": {
            "type": "STRING",
            "enum": ["provided", "rule_derivable", "algorithmic"],
        },
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": [
        "objects",
        "data",
        "relations",
        "processes",
        "constraints",
        "goal",
        "input_description",
        "output_description",
        "result_ownership",
    ],
}


def _classify_schema() -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "status": {"type": "STRING", "enum": ["ok", "unsupported"]},
            "simulation_id": {
                "type": "STRING",
                "nullable": True,
                "enum": list(CATALOG.keys()),
            },
            "reason": {"type": "STRING", "nullable": True},
        },
        "required": ["status"],
    }


async def _call_json(
    api_key: str,
    skill: str,
    user_text: str,
    schema: dict,
    temperature: float,
    retries: int,
    on_retry_note: str,
) -> dict:
    """Gọi Gemini + parse JSON, retry khi trả về không phải JSON hợp lệ."""
    prompt = user_text
    for attempt in range(retries + 1):
        raw = await call_gemini(api_key, load_skill(skill), prompt, schema, temperature)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        if attempt < retries:
            prompt = f"{user_text}\n\n{on_retry_note}"
    raise RuntimeError(f"Giai đoạn {skill} không trả về JSON hợp lệ sau {retries + 1} lần.")


# ── Các stage ─────────────────────────────────────────────────

async def stage_analyze(text: str, api_key: str) -> dict:
    user = f'Đầu vào:\n"""\n{text}\n"""'
    return await _call_json(
        api_key, "analyze", user, ANALYZE_SCHEMA, 0.1, 1,
        "Lần trước không phải JSON hợp lệ. Trả về đúng một đối tượng JSON theo schema.",
    )


async def stage_classify(text: str, analysis: dict, api_key: str) -> dict:
    # M7.8: cho classify thấy NĂNG LỰC thực tế của generic (từ manifest) để
    # định tuyến theo capability, không theo tên môn học → tránh unsupported oan.
    user = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"{catalog_text()}\n\n"
        f"{manifest_capability_summary()}"
    )
    result = await _call_json(
        api_key, "classify", user, _classify_schema(), 0.0, 1,
        "Lần trước không phải JSON hợp lệ. Trả về đúng một đối tượng JSON theo schema.",
    )
    if result.get("status") == "ok" and result.get("simulation_id") not in CATALOG:
        # LLM chọn id ngoài danh mục → coi như không hỗ trợ, không gán bừa
        return {
            "status": "unsupported",
            "reason": "Bài này chưa khớp chắc chắn với mô phỏng nào trong danh mục.",
        }
    return result


async def stage_simulate(
    text: str,
    analysis: dict,
    simulation_id: str,
    api_key: str,
    required_semantic_roles: set[str] | None = None,
    plan: dict | None = None,
) -> tuple[dict | None, str | None]:
    """Sinh config + VALIDATE cấu trúc + (với generic) KIỂM SCENE-MODE
    CONSISTENCY và SEMANTIC COMPAT; sai → retry tối đa 2 lần kèm thông báo lỗi.

    Trả (config chuẩn hóa, None) hoặc (None, lỗi cuối cùng).
    """
    spec = CATALOG[simulation_id]
    # M7.13A: scene_mode từ Representation Plan là NGUỒN QUYẾT ĐỊNH chế độ cảnh
    # — truyền vào prompt để LLM không tự ép reveal cho cảnh tĩnh (và ngược lại).
    scene_mode = (plan or {}).get("scene_mode") if simulation_id == "generic.rule_scene" else None
    base = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"simulation_id đã chọn: {simulation_id}\n\n{spec.contract}"
    )
    if scene_mode:
        base += f"\n\n{scene_mode_guidance(scene_mode)}"
    prompt = base
    last_error = "không rõ"

    for _attempt in range(3):
        raw = await call_gemini(api_key, load_skill("simulate"), prompt, spec.config_schema, 0.1)
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError:
            last_error = "Kết quả không phải JSON hợp lệ."
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        config, error = spec.validate(candidate)
        if config is None:
            last_error = error or "không rõ"
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue

        # M7.13A: spec ↔ scene_mode phải nhất quán (tất định, check trước semantic)
        if scene_mode:
            mode_error = check_scene_consistency(scene_mode, config)
            if mode_error:
                last_error = mode_error
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        # M8-PRE (S2): sơ đồ hệ thống thông tin phải nêu CHIỀU luồng dữ liệu.
        # Cổng TẤT ĐỊNH — đo live cho thấy prompt một mình KHÔNG đủ (LLM dựng đúng
        # node vai trò nhưng bỏ qua `directed` → mất chính giá trị sư phạm cần có).
        if simulation_id == "generic.rule_scene":
            flow_error = check_system_flow_consistency(config)
            if flow_error:
                last_error = flow_error
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        # M7.11: kiểm SEMANTIC COMPAT cho generic — spec phải cover vai trò đề cần
        if required_semantic_roles and simulation_id == "generic.rule_scene":
            compat = check_semantic_compatibility(required_semantic_roles, config)
            if not compat["ok"]:
                if compat["kind"] == "capability_gap":
                    # Vai trò không primitive nào cover → không ép sai, báo gap
                    return None, f"__GAP__:{','.join(compat['missing'])}"
                last_error = (
                    f"Spec chưa thể hiện các vai trò ngữ nghĩa đề cần: "
                    f"{', '.join(compat['missing'])}. Hãy dùng primitive phù hợp với các vai trò này."
                )
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        return config, None

    return None, last_error


# ── Pattern reuse (M7.13B) — thay stage_simulate khi có mẫu khớp ──

def _adapt_schema(unresolved: dict) -> dict:
    """Schema structured-output cho stage adapt — SINH TỪ parameter_schema
    của pattern, chỉ chứa đúng các slot chưa resolve."""
    props: dict = {}
    for name, meta in unresolved.items():
        if meta["kind"] == "string":
            props[name] = {"type": "STRING"}
        elif meta["kind"] == "bit":
            props[name] = {"type": "NUMBER"}
        else:  # number_array
            props[name] = {"type": "ARRAY", "items": {"type": "NUMBER"}}
    return {"type": "OBJECT", "properties": props, "required": list(props)}


async def stage_adapt(
    text: str, analysis: dict, pattern_name: str, unresolved: dict, api_key: str
) -> dict:
    """MỘT call LLM nhỏ điền slot chưa resolve — prompt chỉ gồm mô tả slot
    (kèm ví dụ gốc), KHÔNG kèm contract DSL đồ sộ như simulate."""
    slot_lines = "\n".join(
        f'- {name} ({meta["kind"]}'
        + (f', {meta["length"]} số' if meta["kind"] == "number_array" else "")
        + f"): ví dụ từ bài gốc của mẫu: {json.dumps(meta['example'], ensure_ascii=False)}"
        for name, meta in unresolved.items()
    )
    user = (
        f'Đề bài hiện tại:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"Mẫu mô phỏng: {pattern_name}\n"
        f"Các tham số cần điền cho ĐỀ BÀI HIỆN TẠI:\n{slot_lines}"
    )
    return await _call_json(
        api_key, "adapt", user, _adapt_schema(unresolved), 0.1, 1,
        "Lần trước không phải JSON hợp lệ. Trả về đúng một đối tượng JSON theo schema.",
    )


async def try_pattern_reuse(
    text: str, analysis: dict, plan: dict, roles: set[str], api_key: str, pattern_store
) -> tuple[dict | None, dict]:
    """Tầng 2: tìm pattern verified/validated khớp EXACT (scene_mode + roles),
    adapt tham số (deterministic trước, 1 call LLM nhỏ cho phần còn lại) rồi
    chạy ĐỦ 4 cổng. Bất kỳ bước nào fail → (None, meta) để fallback compose —
    không crash, không sửa pattern gốc."""
    row = pattern_store.find(plan["scene_mode"], roles)
    if row is None:
        return None, {"attempted": False}
    meta = {"attempted": True, "pattern_key": row.pattern_key, "adapt_used": False}
    schema = json.loads(row.parameter_schema_json)
    template = json.loads(row.template_json)
    params, unresolved = deterministic_fill(schema, analysis)
    if unresolved:
        meta["adapt_used"] = True
        try:
            llm_params = await stage_adapt(text, analysis, row.name, unresolved, api_key)
        except Exception:
            return None, meta  # adapt hỏng → fallback compose, không poison store
        params.update({k: llm_params[k] for k in unresolved if k in llm_params})
    if validate_params(schema, params) is not None:
        return None, meta
    config, err = run_gates(plan["scene_mode"], roles, instantiate(template, params))
    if config is None or err:
        return None, meta
    pattern_store.bump_usage(row.pattern_key)
    return config, meta


# ── Orchestrator ──────────────────────────────────────────────

async def run_pipeline(text: str, api_key: str, pattern_store=None) -> dict:
    """Chạy trọn pipeline; trả ValidatedSimulationEnvelope hoặc unsupported.

    Ném RuntimeError khi stage simulate thất bại sau retry (API trả 422).

    M7.13B: `pattern_store` (inject, optional) bật pattern reuse — CHỈ sau
    classify và CHỈ cho generic.rule_scene (bảo vệ specialized selection).
    None → hành vi compose cũ nguyên vẹn.
    """
    analysis = await stage_analyze(text, api_key)

    # M7.11: Representation Plan TẤT ĐỊNH (analysis → semantic requirements → plan).
    plan = build_representation_plan(analysis)

    classification = await stage_classify(text, analysis, api_key)

    # M7.11 + M7.14C + M13 Gate B: vai trò không primitive nào cover HOẶC kết
    # quả đòi cơ chế thuật toán không engine nào sở hữu → capability_gap, KHÔNG
    # ép kiến thức vào primitive sai / để AI tự giải rồi dựng cảnh minh hoạ đáp
    # án. Nhưng gate chỉ chặn ĐƯỜNG GENERIC — bài được classify về mô-đun
    # CHUYÊN BIỆT có engine riêng (không dùng DSL) thì đi tiếp bình thường (bug
    # live: sum_if từng bị vạ lây vì analyze gắn numeric_threshold cho điều
    # kiện lọc "lớn hơn 4"). SERVER ra phán quyết cuối, tất định — không đọc
    # text đề (không keyword-patch).
    chosen = classification.get("simulation_id") if classification.get("status") == "ok" else None
    if chosen is None or chosen == "generic.rule_scene":
        gate_reason = check_computation_ownership(analysis, plan)
        if gate_reason:
            return {
                "status": "unsupported",
                "reason": gate_reason,
                "failure_category": "capability_gap",
                "representation_plan": plan,
                "analysis": analysis,
            }

    if classification.get("status") != "ok":
        return {
            "status": "unsupported",
            "reason": classification.get("reason")
            or "Bài này chưa có mô phỏng phù hợp trong danh mục.",
            "representation_plan": plan,
        }

    simulation_id = classification["simulation_id"]
    spec = CATALOG[simulation_id]

    roles = required_roles(analysis)

    # M7.13B tầng 2: pattern reuse CHỈ thay stage_simulate của generic —
    # specialized đi đường cũ nguyên vẹn (không regression selection).
    reuse_meta = {"attempted": False}
    if pattern_store is not None and simulation_id == "generic.rule_scene":
        config, reuse_meta = await try_pattern_reuse(
            text, analysis, plan, roles, api_key, pattern_store
        )
        if config is not None:
            return {
                "status": "ok",
                "simulation_id": simulation_id,
                "domain": spec.domain,
                "visual_mode": spec.visual_mode,
                "title": spec.make_title(config, analysis),
                "description": f"{analysis.get('input_description', '')} → {analysis.get('output_description', '')}",
                "config": config,
                "notes": config.get("notes") if isinstance(config, dict) else None,
                "analysis": analysis,
                "representation_plan": plan,
                "source": "pattern_reuse",
                "pattern_key": reuse_meta.get("pattern_key"),
                "adapt_used": reuse_meta.get("adapt_used", False),
            }

    config, error = await stage_simulate(
        text, analysis, simulation_id, api_key, required_semantic_roles=roles, plan=plan
    )
    if config is None and error and error.startswith("__GAP__:"):
        # Retry lộ ra vai trò không cover được (phòng hờ — thường plan chặn trước)
        missing = error[len("__GAP__:"):]
        return {
            "status": "unsupported",
            "reason": (
                "Đề cần khả năng biểu diễn mà DSL hiện chưa có "
                f"(vai trò: {missing}). Chưa thể mô phỏng đúng bản chất bài này."
            ),
            "failure_category": "capability_gap",
            "representation_plan": plan,
            "analysis": analysis,
        }
    if config is None:
        raise RuntimeError(
            f"Không sinh được cấu hình mô phỏng hợp lệ sau 3 lần thử (lỗi cuối: {error}). "
            "Hãy diễn đạt lại đề rõ ràng hơn rồi thử lại."
        )

    # M7.13B: compose-new thành công → thử persist reusable pattern (best-effort;
    # extraction ngoài safe allowlist / round-trip lệch / cổng fail → không lưu).
    if pattern_store is not None and simulation_id == "generic.rule_scene":
        try:
            pattern_store.persist_from_spec(plan["scene_mode"], roles, config)
        except Exception:
            pass  # lỗi persist không được làm hỏng envelope trả người dùng

    return {
        "status": "ok",
        "simulation_id": simulation_id,
        "domain": spec.domain,
        "visual_mode": spec.visual_mode,
        "title": spec.make_title(config, analysis),
        "description": f"{analysis.get('input_description', '')} → {analysis.get('output_description', '')}",
        "config": config,
        "notes": config.get("notes") if isinstance(config, dict) else None,
        "analysis": analysis,
        "representation_plan": plan,
        "source": "composed",
        "reuse_fallback": bool(reuse_meta.get("attempted")),
    }
