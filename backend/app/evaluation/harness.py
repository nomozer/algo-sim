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
from app.simulation.catalog import CATALOG
from app.evaluation.dataset import DATASET, EvalItem
from app.simulation.representation import (
    build_representation_plan,
    check_scene_consistency,
    scene_mode_guidance,
)
from app.simulation.semantic import check_semantic

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


def classify_error(msg: str) -> str:
    """Ánh xạ thông báo lỗi validation → nhóm lỗi (§5)."""
    m = (msg or "").lower()
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


@dataclass
class EvalReport:
    results: list[ItemResult] = field(default_factory=list)

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

        return {
            "total": total,
            "classification_accuracy": rate(classified_ok, total),
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
) -> tuple[dict | None, int, str | None]:
    """Bản có đo của stage_simulate: trả (config, số_retry, nhóm_lỗi).

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
        if config is not None:
            return config, attempt, None
        last_error = error
        scene_mode_failed = False
        prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
    return None, 2, FAIL_SCENE_MODE if scene_mode_failed else classify_error(last_error or "")


async def evaluate_item(item: EvalItem, api_key: str) -> ItemResult:
    analysis = await pipeline.stage_analyze(item.text, api_key)
    classification = await pipeline.stage_classify(item.text, analysis, api_key)
    predicted = classification.get("simulation_id") if classification.get("status") == "ok" else None

    if item.group == "unsupported":
        ok = classification.get("status") != "ok"
        fail = None
        if not ok:
            fail = FAIL_UNSUPPORTED_AS_GENERIC if predicted == "generic.rule_scene" else FAIL_WRONG_SELECTION
        return ItemResult(item.id, item.group, predicted, ok, failure=fail)

    classified_ok = predicted == item.expect_simulation_id
    if not classified_ok:
        return ItemResult(item.id, item.group, predicted, False, failure=FAIL_WRONG_SELECTION)

    config, retry, err_cat = await _simulate_with_metrics(item.text, analysis, predicted, api_key)
    if config is None:
        return ItemResult(item.id, item.group, predicted, True, spec_valid=False, retry_count=retry, failure=err_cat)

    semantic_ok, detail = True, ""
    if predicted == "generic.rule_scene":
        semantic_ok, detail = check_semantic(config, item.semantic)
    return ItemResult(
        item.id, item.group, predicted, True,
        spec_valid=True, retry_count=retry, semantic_ok=semantic_ok,
        failure=None if semantic_ok else FAIL_SEMANTIC_WRONG, detail=detail,
    )


async def run_eval(items: list[EvalItem], api_key: str) -> EvalReport:
    report = EvalReport()
    for item in items:
        try:
            report.results.append(await evaluate_item(item, api_key))
        except Exception as err:  # lỗi mạng/pipeline → ghi nhận, không dừng cả bộ
            report.results.append(
                ItemResult(item.id, item.group, None, False, failure="pipeline_error", detail=str(err)[:200])
            )
    return report


def format_report(report: EvalReport) -> str:
    m = report.metrics()
    lines = ["=== KẾT QUẢ ĐÁNH GIÁ LIVE AI COMPOSITION ===", f"Tổng số đề: {m['total']}", ""]
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
    lines.append("Chi tiết từng đề:")
    for r in report.results:
        status = "OK" if (r.classified_ok and r.failure is None) else f"LỖI[{r.failure}]"
        lines.append(f"  [{status}] {r.id} ({r.group}) → {r.predicted} retry={r.retry_count} {r.detail}")
    return "\n".join(lines)


DATASET_ITEMS = DATASET
