"""Pipeline LLM (M3): analyze → classify → simulate → validate → envelope.

Ranh giới cứng: LLM chỉ trích xuất, phân loại và điền CONFIG đầu vào.
Timeline/diễn biến/kết quả do engine tất định phía frontend sinh ra.
SimulationEnvelope hợp lệ CHỈ được phát hành sau server-side validation —
không bao giờ trả thẳng JSON của Gemini cho frontend (M3 §6).
"""

from __future__ import annotations

import json

from app.simulation.catalog import CATALOG, catalog_text, llm_choices
from app.simulation.computation_gate import check_computation_ownership
from app.simulation.families import selector_for_token
from app.simulation.families.sorting import PRESCRIBED_PROCEDURES
from app.simulation.mechanism_gate import (
    ROUTE_MECHANISM_FAMILY_MISMATCH_MSG as _MISMATCH_MSG,
    check_mechanism_consistency_for_target,
    check_mechanism_ownership,
    check_variant_consistency,
)
from app.simulation.mechanisms import canonical_mechanism, mechanism_family
from app.simulation.error_codes import ErrorCode


def _emit(observer, event_type: str, **data) -> None:
    """M14 §F2 — phát event cho observer THỤ ĐỘNG (None → no-op, hành vi
    production không đổi một bit)."""
    if observer is not None:
        observer.emit(event_type, data)
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
        # M14 §E4 — cơ chế THỦ TỤC đề YÊU CẦU (nếu ép cụ thể). Nullable +
        # fail-closed: thiếu → mechanism gate xử như KHÔNG khớp owned (không phá
        # analyze domain khác). Mô tả CƠ CHẾ (thao tác), KHÔNG tên thuật toán,
        # KHÔNG kết quả (§O7).
        "prescribed_procedure": {
            "type": "STRING",
            "enum": list(PRESCRIBED_PROCEDURES),
            "nullable": True,
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
                # M14 §C2 — menu = llm_choices (concrete llm-facing + selector token);
                # bubble/insertion ẩn, comparison_sort thay chỗ.
                "enum": llm_choices(),
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


async def stage_classify(
    text: str, analysis: dict, api_key: str, extra_note: str | None = None
) -> dict:
    # M7.8: cho classify thấy NĂNG LỰC thực tế của generic (từ manifest) để
    # định tuyến theo capability, không theo tên môn học → tránh unsupported oan.
    user = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"{catalog_text()}\n\n"
        f"{manifest_capability_summary()}"
    )
    # M15 Task 6: reclassify note ghép CUỐI — extra_note=None → user y NGUYÊN
    # (hành vi cũ bit-một-bit; sync-lock các test hiện có không đổi).
    if extra_note is not None:
        user = f"{user}\n\n{extra_note}"
    result = await _call_json(
        api_key, "classify", user, _classify_schema(), 0.0, 1,
        "Lần trước không phải JSON hợp lệ. Trả về đúng một đối tượng JSON theo schema.",
    )
    # M14: hợp lệ = trong llm_choices (CATALOG concrete llm-facing HOẶC selector token)
    if result.get("status") == "ok" and result.get("simulation_id") not in set(llm_choices()):
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
    observer=None,
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
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=None, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        config, error = spec.validate(candidate)
        if config is None:
            last_error = error or "không rõ"
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.STRUCTURAL_INVALID.value, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue

        # M7.13A: spec ↔ scene_mode phải nhất quán (tất định, check trước semantic)
        if scene_mode:
            mode_error = check_scene_consistency(scene_mode, config)
            if mode_error:
                last_error = mode_error
                _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.SCENE_MODE_MISMATCH.value, message=last_error)
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        # M8-PRE (S2): sơ đồ hệ thống thông tin phải nêu CHIỀU luồng dữ liệu.
        # Cổng TẤT ĐỊNH — đo live cho thấy prompt một mình KHÔNG đủ (LLM dựng đúng
        # node vai trò nhưng bỏ qua `directed` → mất chính giá trị sư phạm cần có).
        if simulation_id == "generic.rule_scene":
            flow_error = check_system_flow_consistency(config)
            if flow_error:
                last_error = flow_error
                _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.SYSTEM_FLOW_INVALID.value, message=last_error)
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
                _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.SEMANTIC_INCOMPAT.value, message=last_error)
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue

        _emit(observer, "simulate_attempt", n=_attempt, ok=True, error_code=None, message="")
        return config, None

    return None, last_error


async def stage_simulate_family(
    text: str, analysis: dict, selector, api_key: str, observer=None
) -> tuple[dict | None, str | None]:
    """M14 §E — sinh FamilySpec (selector.config_schema/contract) + validate
    fail-closed + VARIANT-CONSISTENCY (E4 tầng 2, so analysis × variant). Retry
    tối đa 3 lần kèm message lỗi. Trả (family_config, None) hoặc (None, lỗi cuối)."""
    base = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"simulation_id đã chọn: {selector.selector_token}\n\n{selector.contract}"
    )
    prompt = base
    last_error = "không rõ"
    for _attempt in range(3):
        raw = await call_gemini(api_key, load_skill("simulate"), prompt, selector.config_schema, 0.1)
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError:
            last_error = "Kết quả không phải JSON hợp lệ."
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=None, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        config, error = selector.validate_family_spec(candidate)
        if config is None:
            last_error = error or "không rõ"
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=ErrorCode.FAMILY_SPEC_INVALID.value, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        # E4 tầng 2: variant có khớp cơ chế đề yêu cầu không (không chỉ nhìn FamilySpec)
        mism = check_variant_consistency(analysis, selector, config["variant"])
        if mism is not None:
            last_error = mism[1]
            _emit(observer, "simulate_attempt", n=_attempt, ok=False, error_code=mism[0].value, message=last_error)
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        _emit(observer, "simulate_attempt", n=_attempt, ok=True, error_code=None, message="")
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


# ── M15 Task 6: route-consistency recovery (bounded, TRƯỚC route-dependent gate) ──

def _family_mismatch(analysis: dict, sim_id: str) -> tuple[ErrorCode, str] | None:
    """CHỈ nhánh 3 (family mismatch) — cho cả selector token lẫn direct entry.
    Ownership (nhánh 2) là route-dependent gate, chạy SAU trên FINAL route
    (check_mechanism_consistency_for_target). MỘT nguồn message (_MISMATCH_MSG)."""
    pres = canonical_mechanism(analysis.get("prescribed_procedure"))
    if pres is None:
        return None
    sel = selector_for_token(sim_id)
    fams = (
        {sel.family_id.value}
        if sel is not None
        else {m.family_id.value for m in CATALOG[sim_id].family_memberships}
    )
    if mechanism_family(pres) not in fams:
        return (ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH, _MISMATCH_MSG)
    return None


async def classify_with_one_route_recovery(
    text: str, analysis: dict, classification: dict, api_key: str, observer=None
) -> tuple[dict, tuple[ErrorCode, str] | None]:
    """Khóa 3 — bounded, KHÔNG recursion, KHÔNG pipeline thứ hai, KHÔNG gọi
    analyze/simulate, KHÔNG chạy route-dependent gate nào. Trả
    (classification_final, mismatch_gap|None).

    - status ≠ ok → passthrough.
    - không mismatch (nhánh 3) → passthrough.
    - mismatch → phát event + ĐÚNG 1 reclassify (extra_note); reclassify ra
      unsupported → passthrough (từ chối trung thực của classify); reclassify VẪN
      lệch → (second, verdict) để caller fail-closed (KHÔNG lượt 3)."""
    if classification.get("status") != "ok":
        return classification, None
    verdict = _family_mismatch(analysis, classification["simulation_id"])
    if verdict is None:
        return classification, None
    _emit(observer, "gate_checked", gate="route_mechanism", fired=True,
          reason_code=verdict[0].value)
    _emit(observer, "reclassify_attempted",
          from_simulation_id=classification["simulation_id"],
          canonical_prescribed=canonical_mechanism(analysis.get("prescribed_procedure")))
    second = await stage_classify(
        text, analysis, api_key,
        extra_note=(
            "Phân tích xác định cơ chế đề yêu cầu thuộc họ năng lực khác với "
            "simulation_id đã chọn. Chọn lại đúng mô phỏng biểu diễn cơ chế đó, "
            "hoặc trả unsupported."
        ),
    )
    _emit(observer, "reclassify_result", status=second.get("status"),
          simulation_id=second.get("simulation_id"))
    if second.get("status") != "ok":
        return second, None  # từ chối trung thực của classify
    if _family_mismatch(analysis, second["simulation_id"]) is not None:
        return second, verdict  # VẪN lệch → caller fail-closed, KHÔNG lượt 3
    return second, None


# ── Orchestrator ──────────────────────────────────────────────

async def run_pipeline(text: str, api_key: str, pattern_store=None, observer=None) -> dict:
    """Chạy trọn pipeline; trả ValidatedSimulationEnvelope hoặc unsupported.

    Ném RuntimeError khi stage simulate thất bại sau retry (API trả 422).

    M7.13B: `pattern_store` (inject, optional) bật pattern reuse — CHỈ sau
    classify và CHỈ cho generic.rule_scene (bảo vệ specialized selection).
    None → hành vi compose cũ nguyên vẹn.

    M14 §F2: `observer` (inject, optional) THỤ ĐỘNG — thu event có cấu trúc; None
    → hành vi production KHÔNG đổi một bit (evaluation dùng CHUNG orchestration
    này, bất biến #22).
    """
    analysis = await stage_analyze(text, api_key)
    _emit(observer, "analyze_done",
          result_ownership=analysis.get("result_ownership") if isinstance(analysis, dict) else None,
          prescribed_procedure=analysis.get("prescribed_procedure") if isinstance(analysis, dict) else None,
          canonical_prescribed=canonical_mechanism(analysis.get("prescribed_procedure")) if isinstance(analysis, dict) else None)

    # M7.11: Representation Plan TẤT ĐỊNH (analysis → semantic requirements → plan).
    plan = build_representation_plan(analysis)
    _emit(observer, "plan_built", unsupported_capabilities=list(plan.get("unsupported_capabilities", [])))

    classification = await stage_classify(text, analysis, api_key)  # lần 1
    _emit(observer, "classify_done",
          status=classification.get("status"), simulation_id=classification.get("simulation_id"))

    # M15 Task 6 (khóa 3, Global Constraint 15): route/mechanism-family consistency
    # + ĐÚNG 1 reclassify TRƯỚC mọi route-dependent gate. Vẫn lệch sau 1 lượt →
    # capability_gap fail-closed (KHÔNG simulate target mâu thuẫn, KHÔNG lượt 3).
    classification, mismatch_gap = await classify_with_one_route_recovery(
        text, analysis, classification, api_key, observer
    )
    if mismatch_gap is not None:
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="capability_gap")
        return {
            "status": "unsupported",
            "reason": mismatch_gap[1],
            "failure_category": "capability_gap",
            "error_code": mismatch_gap[0].value,
            "representation_plan": plan,
            "analysis": analysis,
        }

    # ─── FINAL ROUTE — mọi route-dependent gate chạy DƯỚI dòng này ───
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
        _emit(observer, "gate_checked", gate="computation", fired=bool(gate_reason),
              reason_code=ErrorCode.GATE_RESULT_OWNERSHIP.value if gate_reason else None)
        if gate_reason:
            env = {
                "status": "unsupported",
                "reason": gate_reason,
                "failure_category": "capability_gap",
                "representation_plan": plan,
                "analysis": analysis,
            }
            _emit(observer, "envelope", status="unsupported", simulation_id=None,
                  failure_category="capability_gap")
            return env

    if classification.get("status") != "ok":
        _emit(observer, "envelope", status="unsupported", simulation_id=None, failure_category=None)
        return {
            "status": "unsupported",
            "reason": classification.get("reason")
            or "Bài này chưa có mô phỏng phù hợp trong danh mục.",
            "representation_plan": plan,
        }

    simulation_id = classification["simulation_id"]

    # M14 §E — NHÁNH FAMILY SELECTOR (vd comparison_sort): mechanism gate (tầng 1)
    # → sinh FamilySpec → resolve TẤT ĐỊNH → validate concrete → envelope mang
    # CONCRETE id (token selector KHÔNG BAO GIỜ là envelope id, §D).
    selector = selector_for_token(simulation_id)
    if selector is not None:
        gate = check_mechanism_ownership(analysis, selector)
        _emit(observer, "gate_checked", gate="mechanism", fired=bool(gate),
              reason_code=gate[0].value if gate else None)
        if gate is not None:
            _emit(observer, "envelope", status="unsupported", simulation_id=None,
                  failure_category="capability_gap")
            return {
                "status": "unsupported",
                "reason": gate[1],
                "failure_category": "capability_gap",
                "error_code": gate[0].value,
                "representation_plan": plan,
                "analysis": analysis,
            }
        family_config, ferr = await stage_simulate_family(text, analysis, selector, api_key, observer=observer)
        if family_config is None:
            raise RuntimeError(
                f"Không sinh được FamilySpec hợp lệ cho {simulation_id} sau 3 lần thử "
                f"(lỗi cuối: {ferr})."
            )
        concrete_id, concrete_config = selector.resolve(family_config, analysis)
        _emit(observer, "family_resolved", family_id=selector.family_id.value,
              variant=family_config["variant"], concrete_id=concrete_id)
        concrete_spec = CATALOG.get(concrete_id)
        if concrete_spec is None:  # adapter trỏ target không tồn tại (lock C4 chống)
            raise RuntimeError(f"Adapter trỏ tới target không tồn tại: {concrete_id}.")
        validated, verr = concrete_spec.validate(concrete_config)
        if validated is None:  # validation kép qua validator concrete hiện có
            raise RuntimeError(
                f"Config sau adapter không qua validator concrete ({concrete_id}): {verr}"
            )
        _emit(observer, "envelope", status="ok", simulation_id=concrete_id, source="family_resolved")
        return {
            "status": "ok",
            "simulation_id": concrete_id,
            "domain": concrete_spec.domain,
            "visual_mode": concrete_spec.visual_mode,
            "title": concrete_spec.make_title(validated, analysis),
            "description": f"{analysis.get('input_description', '')} → {analysis.get('output_description', '')}",
            "config": validated,
            "notes": validated.get("notes") if isinstance(validated, dict) else None,
            "analysis": analysis,
            "representation_plan": plan,
            "source": "family_resolved",
            "family_id": selector.family_id.value,
            "variant": family_config["variant"],
        }

    # M15 Task 6 — DIRECT ENTRY (không selector): ownership gate trên FINAL route.
    # Nhánh mismatch (nhánh 3) đã xử ở recovery; ở đây thường chỉ còn ownership
    # (nhánh 2), nhánh mismatch là DEFENSIVE — vẫn fail-closed cùng khuôn.
    direct_verdict = check_mechanism_consistency_for_target(analysis, CATALOG[simulation_id])
    if direct_verdict is not None:
        _emit(observer, "gate_checked", gate="mechanism", fired=True,
              reason_code=direct_verdict[0].value)
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="capability_gap")
        return {
            "status": "unsupported",
            "reason": direct_verdict[1],
            "failure_category": "capability_gap",
            "error_code": direct_verdict[0].value,
            "representation_plan": plan,
            "analysis": analysis,
        }

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
            _emit(observer, "envelope", status="ok", simulation_id=simulation_id, source="pattern_reuse")
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
        text, analysis, simulation_id, api_key, required_semantic_roles=roles, plan=plan,
        observer=observer,
    )
    if config is None and error and error.startswith("__GAP__:"):
        # Retry lộ ra vai trò không cover được (phòng hờ — thường plan chặn trước)
        missing = error[len("__GAP__:"):]
        _emit(observer, "envelope", status="unsupported", simulation_id=None,
              failure_category="capability_gap")
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

    _emit(observer, "envelope", status="ok", simulation_id=simulation_id, source="composed")
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
