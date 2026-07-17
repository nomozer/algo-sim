"""Harness đánh giá live AI composition (M7 §4, §5, §7).

Chạy pipeline thật (analyze → classify → simulate → validate) cho từng đề,
ghi classification, spec validity, số lần retry, semantic check, phân loại lỗi,
rồi tổng hợp metrics. Dùng chung cho offline (mock call_gemini) và live (Gemini
thật) — CI không phụ thuộc mạng.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.ai import pipeline
from app.ai.gemini import ApiBudget, BudgetExceeded
from app.evaluation.observer import AttemptObserver
from app.simulation.catalog import CATALOG
from app.evaluation.dataset import DATASET, EvalItem
from app.simulation.representation import (
    build_representation_plan,
    check_scene_consistency,
    scene_mode_guidance,
)
from app.simulation.semantic import check_semantic, check_system_flow_consistency

# Phân loại lỗi (§5)
FAIL_WRONG_SELECTION = "wrong_selection"
FAIL_UNKNOWN_PRIMITIVE = "unknown_primitive"
FAIL_UNKNOWN_RULE = "unknown_rule"
FAIL_DANGLING_REF = "dangling_reference"
FAIL_CYCLE = "cycle"
FAIL_MISSING_FIELD = "missing_field"
FAIL_INVALID_VALUE = "invalid_value"
FAIL_OVER_LIMIT = "over_limit"
FAIL_SEMANTIC_WRONG = "semantic_wrong"
FAIL_UNSUPPORTED_AS_GENERIC = "unsupported_as_generic"
FAIL_SCENE_MODE = "scene_mode_mismatch"  # M7.13A: spec trái với scene_mode của plan
# M13 hotfix: nhóm riêng cho role-typing mismatch (validator.py operand
# coherence, §3.2/blocker 3) — message của nhóm này CHỨA cụm "object type"
# trong câu gợi ý ("dùng object type ... làm target"), nên từng bị nhánh
# unknown_primitive bên dưới khớp nhầm và làm chẩn đoán live đi sai hướng
# (known-issue 7f — canonical đỏ ×2 bị dán nhãn unknown_primitive trong khi
# validator KHÔNG hề chặn ở primitive allowlist). Phải kiểm nhóm này TRƯỚC.
FAIL_ROLE_MISMATCH = "role_mismatch"


def classify_error(msg: str) -> str:
    """Ánh xạ thông báo lỗi validation → nhóm lỗi (§5)."""
    m = (msg or "").lower()
    # M13 hotfix: role mismatch TRƯỚC unknown_primitive — không dựa vào cụm
    # chung "object type" (message role-typing cũng chứa cụm đó trong gợi ý),
    # mà dựa vào cụm ĐẶC THÙ của chính hai nhánh role-typing trong validator.py
    # (check (a) target-role, check (b) derived-source-role — cả hai đều nêu
    # "vai trò" theo cách unknown_primitive/unknown_rule không dùng).
    if "không nhận được vai trò" in m or ("không tương thích" in m and "vai trò" in m):
        return FAIL_ROLE_MISMATCH
    if "object type" in m or "type không hợp lệ" in m and "rule" not in m:
        return FAIL_UNKNOWN_PRIMITIVE
    if "rule type" in m or "boolean rule" in m or "weighted_sum" in m:
        return FAIL_UNKNOWN_RULE
    if "không tồn tại" in m or "tham chiếu" in m:
        return FAIL_DANGLING_REF
    if "vòng" in m or "circular" in m:
        return FAIL_CYCLE
    if "tối đa" in m or "phải có 1" in m or "1–" in m:
        return FAIL_OVER_LIMIT
    if "bắt buộc" in m or "phải là" in m or "thiếu" in m:
        return FAIL_MISSING_FIELD
    return FAIL_INVALID_VALUE


@dataclass
class ItemResult:
    id: str
    group: str
    predicted: str | None
    classified_ok: bool
    spec_valid: bool | None = None  # None nếu không tới bước simulate
    retry_count: int = 0
    semantic_ok: bool | None = None
    failure: str | None = None
    detail: str = ""
    # M7.14T: capability gate THẬT (representation plan) có bắt được đề này
    # không — metric SONG SONG, KHÔNG đổi ngữ nghĩa các metric cũ (§8 phương án c).
    gap_gate_fired: bool | None = None
    # M14 §F3 — metric split (family/variant/final-route) + kênh gate. predicted
    # là output CLASSIFY (có thể là selector token); final là envelope id (concrete).
    classify_simulation_id: str | None = None
    final_simulation_id: str | None = None
    variant: str | None = None
    computation_gate_fired: bool | None = None
    mechanism_gate_fired: bool | None = None


@dataclass
class EvalReport:
    results: list[ItemResult] = field(default_factory=list)
    # M7.14T: ngân sách API + lý do dừng sớm (nếu chạm trần)
    planned: int = 0
    budget: ApiBudget | None = None
    aborted_reason: str | None = None

    def _by_group(self, g: str) -> list[ItemResult]:
        return [r for r in self.results if r.group == g]

    def metrics(self) -> dict:
        total = len(self.results)
        classified_ok = sum(1 for r in self.results if r.classified_ok)
        spec_a = self._by_group("specialized")
        spec_b = self._by_group("generic")
        spec_c = self._by_group("unsupported")

        # unsupported precision = đúng-unsupported / tất-cả-dự-đoán-unsupported
        predicted_unsupported = [r for r in self.results if r.predicted is None]
        correct_unsupported = [r for r in predicted_unsupported if r.group == "unsupported"]

        composed = [r for r in self.results if r.spec_valid is not None]  # có tới simulate
        valid = [r for r in composed if r.spec_valid]
        valid_first = [r for r in valid if r.retry_count == 0]

        errors: dict[str, int] = {}
        for r in self.results:
            if r.failure:
                errors[r.failure] = errors.get(r.failure, 0) + 1

        def rate(num: int, den: int) -> float:
            return round(num / den, 3) if den else 0.0

        # M7.14T: gap_gate_recall — metric MỚI, đo capability gate THẬT
        # (build_representation_plan) chứ không phải classify. Chạy SONG SONG,
        # không thay đổi cách tính bất kỳ metric cũ nào (so sánh lịch sử giữ nguyên).
        gap_gate_expected = [r for r in spec_c if r.gap_gate_fired is not None]
        gap_gate_hits = [r for r in gap_gate_expected if r.gap_gate_fired]
        # Precision: gate KHÔNG được nổ oan với đề supported (specialized/generic)
        supported = [r for r in self.results if r.group != "unsupported" and r.gap_gate_fired is not None]
        false_gaps = [r.id for r in supported if r.gap_gate_fired]

        return {
            "total": total,
            "classification_accuracy": rate(classified_ok, total),
            "gap_gate_recall": rate(len(gap_gate_hits), len(gap_gate_expected)),
            "gap_gate_false_positives": false_gaps,
            "specialized_selection_accuracy": rate(sum(1 for r in spec_a if r.classified_ok), len(spec_a)),
            "generic_selection_accuracy": rate(sum(1 for r in spec_b if r.classified_ok), len(spec_b)),
            "unsupported_recall": rate(sum(1 for r in spec_c if r.classified_ok), len(spec_c)),
            "unsupported_precision": rate(len(correct_unsupported), len(predicted_unsupported)),
            "valid_spec_first_attempt_rate": rate(len(valid_first), len(composed)),
            "valid_spec_after_retry_rate": rate(len(valid), len(composed)),
            "avg_retry_count": round(sum(r.retry_count for r in composed) / len(composed), 2) if composed else 0.0,
            "semantic_pass_rate": rate(
                sum(1 for r in composed if r.semantic_ok), sum(1 for r in composed if r.semantic_ok is not None)
            ),
            "error_categories": errors,
        }


async def _simulate_with_metrics(
    text: str, analysis: dict, simulation_id: str, api_key: str
) -> tuple[dict | None, int, str | None, str]:
    """Bản có đo của stage_simulate: trả (config, số_retry, nhóm_lỗi, message_lỗi_cuối).

    M7.13A: mirror pipeline — chèn scene_mode guidance vào prompt và check
    scene consistency, để metric đo ĐÚNG hành vi live."""
    spec = CATALOG[simulation_id]
    scene_mode = None
    if simulation_id == "generic.rule_scene":
        scene_mode = build_representation_plan(analysis)["scene_mode"]
    base = (
        f'Đầu vào gốc:\n"""\n{text}\n"""\n\n'
        f"Kết quả phân tích:\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"simulation_id đã chọn: {simulation_id}\n\n{spec.contract}"
    )
    if scene_mode:
        base += f"\n\n{scene_mode_guidance(scene_mode)}"
    prompt = base
    last_error = None
    scene_mode_failed = False
    for attempt in range(3):
        raw = await pipeline.call_gemini(api_key, pipeline.load_skill("simulate"), prompt, spec.config_schema, 0.1)
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError:
            last_error = "Kết quả không phải JSON hợp lệ."
            scene_mode_failed = False
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue
        config, error = spec.validate(candidate)
        if config is not None and scene_mode:
            mode_error = check_scene_consistency(scene_mode, config)
            if mode_error:
                last_error = mode_error
                scene_mode_failed = True
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue
        # M8-PRE (S2): mirror pipeline — cùng cổng tất định, nếu không metric live
        # sẽ đo một hành vi KHÁC với sản phẩm (known issue #1: harness mirror pipeline).
        if config is not None and simulation_id == "generic.rule_scene":
            flow_error = check_system_flow_consistency(config)
            if flow_error:
                last_error = flow_error
                scene_mode_failed = False
                prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
                continue
        if config is not None:
            return config, attempt, None, ""
        last_error = error
        scene_mode_failed = False
        prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
    # M13 Task 14: trả kèm message lỗi cuối — trước đây bị vứt, khiến ca
    # canonical đỏ ×2 (unknown_primitive) KHÔNG chẩn đoán nổi vì bằng chứng mất.
    return None, 2, FAIL_SCENE_MODE if scene_mode_failed else classify_error(last_error or ""), (last_error or "")[:200]


async def _evaluate_item_legacy(item: EvalItem, api_key: str) -> ItemResult:
    """M7.14T (DEPRECATED — chờ retire ở M14 Task 10 sau parity proof).

    Tái dựng chuỗi stage RIÊNG (KHÔNG qua run_pipeline) → vi phạm #22. Giữ tạm để
    parity test so với evaluate_item mới. Xóa cùng _simulate_with_metrics."""
    analysis = await pipeline.stage_analyze(item.text, api_key)
    plan = build_representation_plan(analysis)
    gap_gate_fired = bool(plan["unsupported_capabilities"])

    classification = await pipeline.stage_classify(item.text, analysis, api_key)
    predicted = classification.get("simulation_id") if classification.get("status") == "ok" else None

    if item.group == "unsupported":
        ok = classification.get("status") != "ok"
        fail = None
        if not ok:
            fail = FAIL_UNSUPPORTED_AS_GENERIC if predicted == "generic.rule_scene" else FAIL_WRONG_SELECTION
        return ItemResult(item.id, item.group, predicted, ok, failure=fail, gap_gate_fired=gap_gate_fired)

    classified_ok = predicted == item.expect_simulation_id
    if not classified_ok:
        return ItemResult(
            item.id, item.group, predicted, False,
            failure=FAIL_WRONG_SELECTION, gap_gate_fired=gap_gate_fired,
        )

    config, retry, err_cat, err_msg = await _simulate_with_metrics(item.text, analysis, predicted, api_key)
    if config is None:
        return ItemResult(
            item.id, item.group, predicted, True, spec_valid=False, retry_count=retry,
            failure=err_cat, detail=err_msg, gap_gate_fired=gap_gate_fired,
        )

    semantic_ok, detail = True, ""
    if predicted == "generic.rule_scene":
        semantic_ok, detail = check_semantic(config, item.semantic)
    return ItemResult(
        item.id, item.group, predicted, True,
        spec_valid=True, retry_count=retry, semantic_ok=semantic_ok,
        failure=None if semantic_ok else FAIL_SEMANTIC_WRONG, detail=detail,
        gap_gate_fired=gap_gate_fired,
    )


def _retry_count(attempts: list[dict]) -> int:
    """retry_count đồng bộ _simulate_with_metrics: n của attempt THÀNH CÔNG, hoặc
    n của attempt cuối nếu thất bại (3 attempt → 2)."""
    if not attempts:
        return 0
    ok = next((a for a in attempts if a.get("ok")), None)
    return ok["n"] if ok is not None else attempts[-1]["n"]


def _item_result_from(
    item: EvalItem, obs: AttemptObserver, envelope: dict | None, pipeline_error: str | None
) -> ItemResult:
    """M14 §F2/§F3 — dựng ItemResult TỪ observer + envelope (production lifecycle).
    Bao gồm metric split family/variant/final-route (Task 11 đọc thêm)."""
    classify = obs.classify() or {}
    predicted = classify.get("simulation_id") if classify.get("status") == "ok" else None
    gap_gate_fired = obs.gap_gate_fired()
    attempts = obs.simulate_attempts()
    env = envelope or {}
    env_ok = env.get("status") == "ok"
    final_id = env.get("simulation_id") if env_ok else None
    fam = obs.family_resolved() or {}

    common = dict(
        gap_gate_fired=gap_gate_fired,
        classify_simulation_id=predicted,
        final_simulation_id=final_id,
        variant=fam.get("variant"),
        computation_gate_fired=any(g.get("gate") == "computation" and g.get("fired") for g in obs.gates()),
        mechanism_gate_fired=any(g.get("gate") == "mechanism" and g.get("fired") for g in obs.gates()),
    )

    # nhóm unsupported: ĐÚNG khi pipeline KHÔNG ra envelope ok (từ chối trung thực)
    if item.group == "unsupported":
        refused = pipeline_error is None and not env_ok
        fail = None
        if not refused:
            fail = FAIL_UNSUPPORTED_AS_GENERIC if final_id == "generic.rule_scene" else FAIL_WRONG_SELECTION
        return ItemResult(item.id, item.group, predicted, refused, failure=fail, **common)

    # specialized/generic: classify đúng nếu classify-output HOẶC final-route == expect
    classified_ok = predicted == item.expect_simulation_id or final_id == item.expect_simulation_id
    if not classified_ok:
        return ItemResult(item.id, item.group, predicted, False, failure=FAIL_WRONG_SELECTION, **common)

    if env_ok:
        semantic_ok, detail = True, ""
        if final_id == "generic.rule_scene":
            semantic_ok, detail = check_semantic(env.get("config", {}), item.semantic)
        return ItemResult(
            item.id, item.group, predicted, True, spec_valid=True,
            retry_count=_retry_count(attempts),
            semantic_ok=semantic_ok, detail=detail,
            failure=None if semantic_ok else FAIL_SEMANTIC_WRONG, **common,
        )

    # classify đúng nhưng KHÔNG ra envelope: simulate thất bại (raise) hoặc gap
    last = attempts[-1] if attempts else {}
    err_cat = last.get("error_code") or classify_error(last.get("message") or pipeline_error or "")
    return ItemResult(
        item.id, item.group, predicted, True, spec_valid=False,
        retry_count=_retry_count(attempts) if attempts else 2,
        failure=err_cat, detail=(last.get("message") or pipeline_error or "")[:200], **common,
    )


async def evaluate_item(item: EvalItem, api_key: str) -> ItemResult:
    """M14 §F2 (bất biến #22) — chấm QUA production orchestration `run_pipeline`
    với observer THỤ ĐỘNG; KHÔNG tái dựng stage, KHÔNG ghi cache/pattern
    (pattern_store=None → reuse/persist bị guard bỏ qua; cache sống ở main.py)."""
    obs = AttemptObserver()
    pipeline_error: str | None = None
    envelope: dict | None = None
    try:
        envelope = await pipeline.run_pipeline(item.text, api_key, pattern_store=None, observer=obs)
    except BudgetExceeded:
        raise  # chạm trần → để run_eval dừng cả bộ
    except Exception as err:  # simulate thất bại sau retry (RuntimeError) hoặc lỗi khác
        pipeline_error = str(err)
    return _item_result_from(item, obs, envelope, pipeline_error)


# ── Suite selection (M7.14T) — dataset.py vẫn là benchmark definition ──

def select_suite(name: str, items: list[EvalItem] | None = None) -> list[EvalItem]:
    """"full" = toàn bộ; "smoke" = các item gắn tag smoke; tên khác = lọc theo tag."""
    pool = DATASET if items is None else items
    if name == "full":
        return list(pool)
    return [it for it in pool if name in it.tags]


async def run_eval(
    items: list[EvalItem], api_key: str, budget: ApiBudget | None = None
) -> EvalReport:
    report = EvalReport(planned=len(items))
    for item in items:
        try:
            report.results.append(await evaluate_item(item, api_key))
        except BudgetExceeded as err:  # chạm trần API → DỪNG cả bộ, vẫn in report
            report.aborted_reason = str(err)
            break
        except Exception as err:  # lỗi mạng/pipeline → ghi nhận, không dừng cả bộ
            report.results.append(
                ItemResult(item.id, item.group, None, False, failure="pipeline_error", detail=str(err)[:200])
            )
    if budget is not None:
        report.budget = budget
    return report


def format_report(report: EvalReport) -> str:
    m = report.metrics()
    lines = [
        "=== KẾT QUẢ ĐÁNH GIÁ LIVE AI COMPOSITION ===",
        f"Đề dự kiến: {report.planned} · đã chạy: {m['total']}",
        "",
    ]
    for key in (
        "classification_accuracy",
        "specialized_selection_accuracy",
        "generic_selection_accuracy",
        "unsupported_recall",
        "unsupported_precision",
        "valid_spec_first_attempt_rate",
        "valid_spec_after_retry_rate",
        "semantic_pass_rate",
        "avg_retry_count",
    ):
        lines.append(f"  {key}: {m[key]}")
    lines.append(f"  error_categories: {m['error_categories']}")
    lines.append("")
    # M7.14T: metric SONG SONG — đo capability gate thật, không đụng metric cũ
    lines.append("--- Capability gate (metric mới, M7.14C) ---")
    lines.append(f"  gap_gate_recall: {m['gap_gate_recall']}")
    lines.append(f"  gap_gate_false_positives: {m['gap_gate_false_positives'] or 'không có'}")

    if report.budget is not None:
        b = report.budget
        lines.append("")
        lines.append("--- Ngân sách API ---")
        lines.append(f"  logical_calls (call_gemini): {b.logical_calls}")
        lines.append(f"  http_requests (thật, kể cả retry): {b.http_requests}")
        lines.append(f"  retry_requests: {b.retry_requests}")
        lines.append(f"  transient_hits (429/5xx): {b.transient_hits}")
        lines.append(f"  max_api_calls: {b.max_api_calls if b.max_api_calls is not None else 'không giới hạn'}")
    if report.aborted_reason:
        lines.append(f"  ⚠ DỪNG SỚM: {report.aborted_reason}")

    lines.append("")
    lines.append("Chi tiết từng đề:")
    for r in report.results:
        status = "OK" if (r.classified_ok and r.failure is None) else f"LỖI[{r.failure}]"
        gate = " gate=fired" if r.gap_gate_fired else ""
        lines.append(f"  [{status}] {r.id} ({r.group}) → {r.predicted} retry={r.retry_count}{gate} {r.detail}")
    return "\n".join(lines)


DATASET_ITEMS = DATASET
