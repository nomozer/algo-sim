"""Harness đánh giá live AI composition (M7 §4, §5, §7).

Chạy pipeline thật (analyze → classify → simulate → validate) cho từng đề,
ghi classification, spec validity, số lần retry, semantic check, phân loại lỗi,
rồi tổng hợp metrics. Dùng chung cho offline (mock call_gemini) và live (Gemini
thật) — CI không phụ thuộc mạng.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ai import pipeline
from app.ai.gemini import ApiBudget, BudgetExceeded
from app.evaluation.observer import AttemptObserver
from app.evaluation.dataset import DATASET, EvalItem
from app.evaluation.m16_record import build_m16_record
from app.simulation.families import FAMILY_SELECTORS
from app.simulation.semantic import check_semantic


def _selector_token_for_concrete(concrete_id: str | None) -> str | None:
    """M14 §F3 — token selector mà một concrete id nằm SAU (None nếu concrete
    không thuộc family nào có selector). Dùng để đo family/variant selection."""
    if not concrete_id:
        return None
    for sel in FAMILY_SELECTORS.values():
        for v in sel.variants:
            if v.concrete_simulation_id == concrete_id:
                return sel.selector_token
    return None

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
    # M14 §F3 — cờ dẫn xuất để tách metric (đo trên final ENVELOPE, không phải
    # classify output — vì classify nay có thể trả selector token).
    expected_family_routed: bool = False       # expect nằm sau một family selector
    final_route_correct: bool | None = None     # final_simulation_id == expect
    family_selection_correct: bool | None = None  # classify token == selector kỳ vọng
    variant_selection_correct: bool | None = None  # variant resolve đúng concrete


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

        # M14 §F3 — metric TÁCH BẠCH đo trên FINAL ENVELOPE (không phải classify
        # output — vì classify nay có thể trả selector token). classification_accuracy
        # CŨ vẫn tính trên classified_ok (đã dung nạp final==expect ở
        # _item_result_from) → cho item KHÔNG family-routed, hai số TRÙNG (so sánh
        # baseline hợp lệ); cho item family-routed, đọc final_route_accuracy.
        sup_all = spec_a + spec_b
        routed = [r for r in sup_all if r.expected_family_routed]

        return {
            "total": total,
            "classification_accuracy": rate(classified_ok, total),
            "final_route_accuracy": rate(sum(1 for r in sup_all if r.final_route_correct), len(sup_all)),
            "family_selection_accuracy": rate(sum(1 for r in routed if r.family_selection_correct), len(routed)),
            "variant_selection_accuracy": rate(sum(1 for r in routed if r.variant_selection_correct), len(routed)),
            "family_routed_count": len(routed),
            "gap_gate_recall": rate(len(gap_gate_hits), len(gap_gate_expected)),
            "gap_gate_false_positives": false_gaps,
            "mechanism_gate_fired_ids": [r.id for r in self.results if r.mechanism_gate_fired],
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


# M14 Task 10: `_simulate_with_metrics` + `_evaluate_item_legacy` ĐÃ RETIRE sau
# transcript parity proof (test_eval_parity — non-gate cases khớp; gate-refusal
# là khác biệt hợp lệ đã ghi). Eval nay đi CHUNG production `run_pipeline` +
# observer (bất biến #22). `classify_error` còn dùng làm FALLBACK khi attempt
# không mang error_code có cấu trúc (_item_result_from).


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

    expected_token = _selector_token_for_concrete(item.expect_simulation_id)
    common = dict(
        gap_gate_fired=gap_gate_fired,
        classify_simulation_id=predicted,
        final_simulation_id=final_id,
        variant=fam.get("variant"),
        computation_gate_fired=any(g.get("gate") == "computation" and g.get("fired") for g in obs.gates()),
        mechanism_gate_fired=any(g.get("gate") == "mechanism" and g.get("fired") for g in obs.gates()),
        # M14 §F3 — đo trên FINAL envelope (không phải classify output)
        expected_family_routed=expected_token is not None,
        final_route_correct=(final_id == item.expect_simulation_id) if item.group != "unsupported" else None,
        family_selection_correct=(predicted == expected_token) if expected_token else None,
        variant_selection_correct=(final_id == item.expect_simulation_id) if expected_token else None,
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


_BUDGET_COUNTERS = ("logical_calls", "http_requests", "retry_requests", "transient_hits")


def _budget_snapshot(budget: ApiBudget | None) -> dict:
    """M16 Task 2 (W2) — 4 counter tại một thời điểm (0 khi không có budget,
    §c: budget_delta luôn là dict 4 khoá, không None)."""
    if budget is None:
        return {k: 0 for k in _BUDGET_COUNTERS}
    return {k: getattr(budget, k) for k in _BUDGET_COUNTERS}


async def evaluate_item(
    item: EvalItem,
    api_key: str,
    budget: ApiBudget | None = None,
    record_sink: list | None = None,
) -> ItemResult:
    """M14 §F2 (bất biến #22) — chấm QUA production orchestration `run_pipeline`
    với observer THỤ ĐỘNG; KHÔNG tái dựng stage, KHÔNG ghi cache/pattern
    (pattern_store=None → reuse/persist bị guard bỏ qua; cache sống ở main.py).

    M16 Task 2 (W2, cả hai tham số optional, mặc định None — chữ ký cũ gọi
    KHÔNG đổi hành vi): `budget` — snapshot 4 counter TRƯỚC/SAU run_pipeline →
    `budget_delta` (KHÔNG đưa vào ItemResult, metric cũ không đổi một bit).
    `record_sink` — nếu có, append một `M16CaseRecord` (quan sát có cấu trúc
    SONG SONG, không thay ItemResult/metric hiện có)."""
    obs = AttemptObserver()
    pipeline_error: str | None = None
    envelope: dict | None = None
    before = _budget_snapshot(budget)
    try:
        envelope = await pipeline.run_pipeline(item.text, api_key, pattern_store=None, observer=obs)
    except BudgetExceeded:
        raise  # chạm trần → để run_eval dừng cả bộ
    except Exception as err:  # simulate thất bại sau retry (RuntimeError) hoặc lỗi khác
        pipeline_error = str(err)
    after = _budget_snapshot(budget)
    budget_delta = {k: after[k] - before[k] for k in _BUDGET_COUNTERS}
    result = _item_result_from(item, obs, envelope, pipeline_error)
    if record_sink is not None:
        record_sink.append(
            build_m16_record(
                item, obs, envelope, pipeline_error, budget_delta, semantic_ok=result.semantic_ok
            )
        )
    return result


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
            report.results.append(await evaluate_item(item, api_key, budget=budget))
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
    # M14 §F3 — metric TÁCH BẠCH (đo trên FINAL envelope). classification_accuracy
    # ở trên đo classify_ok (dung nạp final==expect); các số dưới tách rõ.
    lines.append("--- Family routing (metric mới M14, đo trên FINAL envelope) ---")
    lines.append(f"  final_route_accuracy: {m['final_route_accuracy']}")
    lines.append(f"  family_selection_accuracy: {m['family_selection_accuracy']} (n={m['family_routed_count']})")
    lines.append(f"  variant_selection_accuracy: {m['variant_selection_accuracy']} (n={m['family_routed_count']})")
    lines.append(f"  mechanism_gate_fired: {m['mechanism_gate_fired_ids'] or 'không có'}")
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
