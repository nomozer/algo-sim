# -*- coding: utf-8 -*-
"""M16 Task 3 (W3) — module metric M16: 17 metric + failure taxonomy +
aggregation trên `M16CaseRecord` (Task 2). Nguồn yêu cầu (công thức KHÓA,
không tự chế biến): .superpowers/sdd/m16-task-3-brief.md (Phụ lục §4/§5).

Lớp này SONG SONG với `EvalReport.metrics()` (harness cũ, M7–M15) — KHÔNG
import, KHÔNG sửa `EvalReport`/`harness.py`. Metric M16 là bộ số MỚI, độc lập,
không thay thế/ghi đè số cũ.

## Vì sao có tham số `m16_by_case` (map case_id → M16Expectation gốc)

`M16CaseRecord` (Task 2) phẳng hoá `expected_family`/`expected_initial_route`/
`expected_final_route` từ `EvalItem.m16`, nhưng KHÔNG phẳng hoá 3 field chỉ
dùng cho công thức Task 3 — `analyze_mechanism_expected`, `algorithmic_request`,
`recovery_route_exists` (brief ký hiệu "m16.<field>" để phân biệt tường minh
với field record trực tiếp, vd "canonical_prescribed"/"expected_family" —
xem bảng công thức #1/#12/#14). Vì Task 3 CHỈ được sửa file này + file test
(brief: "Files được phép ... KHÔNG sửa file nào khác" — không được đụng
`m16_record.py`), 3 field này được truyền riêng qua `m16_by_case` (map
case_id → `M16Expectation` gốc, đúng đối tượng `item.m16` mà Task 2 đã đọc)
thay vì mở rộng dataclass `M16CaseRecord`. Caller thực (Task 4/5 — pool
đánh giá) có sẵn `item.m16` khi build record nên map này dựng tự nhiên
(`{it.id: it.m16 for it in pool if it.m16 is not None}`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from app.evaluation.m16_record import M16CaseRecord
from app.evaluation.m16_schema import M16Expectation
from app.simulation.catalog import CATALOG
from app.simulation.descriptor import ReachabilityLevel
from app.simulation.families import FAMILY_SELECTORS

# ── hằng số dẫn xuất (không hardcode lặp lại nơi khác) ──────────────────
_SUPPORTED_GROUPS: frozenset[str] = frozenset({"specialized", "generic"})
_SELECTOR_TOKENS: frozenset[str] = frozenset(sel.selector_token for sel in FAMILY_SELECTORS.values())

# Metric #3 (variant_selection_accuracy): brief cho phép hardcode giá trị này
# TẠI ĐỊNH NGHĨA metric (khác #16 — nơi selector token phải tra cứu
# FAMILY_SELECTORS, không hardcode) vì "algorithm.comparison_sort" là ĐỊNH
# NGHĨA của chính metric M16 hiện tại (chỉ có một family có selector).
_VARIANT_SELECTION_INITIAL_ROUTE = "algorithm.comparison_sort"

_VALID_RUN_LABELS: frozenset[str] = frozenset({"offline", "live_baseline", "live_postfix"})

# Enum "đóng" (bảng brief §5) — plain string, không dùng class Enum vì chỉ cần
# nhãn văn bản làm khóa dict cho failure_distribution.
FAILURE_CATEGORIES: tuple[str, ...] = (
    "TRANSIENT_PROVIDER_ERROR",
    "EVALUATION_INFRASTRUCTURE_ERROR",
    "ANALYZE_MECHANISM_ERROR",
    "INITIAL_FAMILY_SELECTION_ERROR",
    "INITIAL_VARIANT_SELECTION_ERROR",
    "ROUTE_MECHANISM_FAMILY_MISMATCH",
    "ROUTE_RECOVERY_FAILED",
    "GATE_MECHANISM_OWNERSHIP",
    "FAMILY_SPEC_INVALID",
    "CONCRETE_CONFIG_INVALID",
    "SEMANTIC_VALIDATION_FAILED",
    "FALSE_REFUSAL",
    "FALSE_POSITIVE_SIMULATION",
    "GENERIC_FALLBACK_LEAK",
    "EXECUTOR_ORACLE_MISMATCH",
)

_SEMANTIC_FAIL_ERROR_CODES: frozenset[str] = frozenset(
    {"semantic_incompat", "scene_mode_mismatch", "system_flow_invalid"}
)


@dataclass(frozen=True)
class MetricValue:
    """Kết quả MỘT metric tỉ lệ (brief §4: dataclass {name, numerator,
    denominator, value}). `denominator == 0` → `value=None` (N/A) — KHÔNG BAO
    GIỜ trả `0.0` giả cho mẫu số rỗng."""

    name: str
    numerator: int
    denominator: int
    value: float | None

    @staticmethod
    def of(name: str, numerator: int, denominator: int) -> "MetricValue":
        value = (numerator / denominator) if denominator else None
        return MetricValue(name=name, numerator=numerator, denominator=denominator, value=value)


@dataclass(frozen=True)
class RetryChannels:
    """Metric #15 — BA kênh retry RIÊNG (không phải một rate đơn, không trộn):
    semantic (simulate retry trong CÙNG một case), transient (HTTP retry hạ
    tầng, từ `budget_delta['retry_requests']`), reclassify (route-consistency
    recovery, M15 khóa 3). Count + avg per case."""

    semantic_retries_total: int
    semantic_retries_avg: float | None
    transient_retries_total: int
    transient_retries_avg: float | None
    reclassify_count_total: int
    reclassify_count_avg: float | None


def quality_band(value: float | None) -> str:
    """None→"N/A"; ≥0.90 "STRONG"; ≥0.75 "MODERATE"; else "WEAK" (brief §4)."""
    if value is None:
        return "N/A"
    if value >= 0.90:
        return "STRONG"
    if value >= 0.75:
        return "MODERATE"
    return "WEAK"


# ── truy cập field CHỈ có trên M16Expectation (xem docstring module) ────
def _m16_for(record: M16CaseRecord, m16_by_case: Mapping[str, M16Expectation] | None) -> M16Expectation | None:
    if not m16_by_case:
        return None
    return m16_by_case.get(record.case_id)


def _analyze_mechanism_expected(
    record: M16CaseRecord, m16_by_case: Mapping[str, M16Expectation] | None
) -> str | None:
    m16 = _m16_for(record, m16_by_case)
    return m16.analyze_mechanism_expected if m16 is not None else None


def _algorithmic_request(record: M16CaseRecord, m16_by_case: Mapping[str, M16Expectation] | None) -> bool:
    m16 = _m16_for(record, m16_by_case)
    return bool(m16.algorithmic_request) if m16 is not None else False


def _recovery_route_exists(record: M16CaseRecord, m16_by_case: Mapping[str, M16Expectation] | None) -> bool:
    m16 = _m16_for(record, m16_by_case)
    return bool(m16.recovery_route_exists) if m16 is not None else False


# ── quy ước chung (brief §4 preamble) ────────────────────────────────────
def _is_supported(record: M16CaseRecord) -> bool:
    """'supported' = record.group ∈ {"specialized","generic"}."""
    return record.group in _SUPPORTED_GROUPS


def _is_refused(record: M16CaseRecord) -> bool:
    """'refused' = envelope_status == "unsupported"."""
    return record.envelope_status == "unsupported"


def _route_is_internal_fixture(route: str | None) -> bool:
    """Route trỏ tới một CATALOG entry mang `ReachabilityLevel.INTERNAL_FIXTURE`.
    Hiện KHÔNG entry CATALOG thật nào mang cờ này (dùng cho fixture nội bộ
    test hạ tầng eval, không phải curriculum case) — test khóa rule bằng
    `unittest.mock.patch.dict(CATALOG, ...)` tạm thời (brief: "test bằng
    record tổng hợp reachability-flag vì catalog hiện 0 fixture")."""
    if route is None:
        return False
    spec = CATALOG.get(route)
    if spec is None:
        return False
    return ReachabilityLevel.INTERNAL_FIXTURE in spec.reachability


def _is_internal_fixture_case(record: M16CaseRecord) -> bool:
    """Case "chạm" một route internal-fixture ở BẤT KỲ điểm nào quan sát được
    (route ban đầu / route cuối / route kỳ vọng) — loại bảo thủ (an toàn hơn
    là bỏ sót nhiễu hạ tầng lẫn vào số liệu sản phẩm)."""
    return (
        _route_is_internal_fixture(record.final_route)
        or _route_is_internal_fixture(record.initial_route)
        or _route_is_internal_fixture(record.expected_final_route)
    )


def _is_product_case(record: M16CaseRecord) -> bool:
    """'product case' = record không infra_error VÀ không internal-fixture
    (brief §4 preamble). Dùng làm cổng CHUNG cho mọi metric tỉ lệ + #15 (xem
    `_gate_product_case`) — KHÔNG riêng metric #13 (dù #13 là metric duy nhất
    có mẫu số CHỈ LÀ product case, không thêm điều kiện nào khác)."""
    return record.infra_error is None and not _is_internal_fixture_case(record)


def _all_attempts_failed(record: M16CaseRecord) -> bool:
    attempts = record.simulate_attempts
    return len(attempts) > 0 and all(a.get("ok") is False for a in attempts)


def _last_attempt_error_code(record: M16CaseRecord) -> str | None:
    attempts = record.simulate_attempts
    return attempts[-1].get("error_code") if attempts else None


# ── 16 metric tỉ lệ (đăng ký (name, rule mô tả, mẫu-số predicate, tử-số
# predicate) — DÙNG CHUNG cho micro/per-family/applicability_report, tránh
# lặp logic mẫu-số hai nơi) ───────────────────────────────────────────────
_Pred = Callable[[M16CaseRecord, Mapping[str, M16Expectation] | None], bool]

_PRODUCT_CASE_RULE = "product case (không infra_error, không internal-fixture route)"


def _gate_product_case(pred: _Pred) -> _Pred:
    """Bọc mẫu-số riêng của một metric bằng cổng "product case" chung (brief
    §4 Aggregation: "micro: mỗi metric trên toàn product cases"; đóng bằng
    câu cuối §4: "internal-fixture record bị loại khỏi product **metrics**"
    — số NHIỀU, áp dụng cho CẢ 16 metric tỉ lệ + #15, không riêng #13)."""

    def gated(r: M16CaseRecord, m: Mapping[str, M16Expectation] | None, _inner: _Pred = pred) -> bool:
        return _is_product_case(r) and _inner(r, m)

    return gated


def _metric_entry(
    name: str, extra_rule: str, den_pred: _Pred, num_pred: _Pred
) -> tuple[str, str, _Pred, _Pred]:
    rule = _PRODUCT_CASE_RULE if not extra_rule else f"{_PRODUCT_CASE_RULE} ∧ {extra_rule}"
    return (name, rule, _gate_product_case(den_pred), num_pred)


_METRIC_REGISTRY: tuple[tuple[str, str, _Pred, _Pred], ...] = (
    _metric_entry(
        "analyze_mechanism_accuracy",
        "case có m16.analyze_mechanism_expected khác None",
        lambda r, m: _analyze_mechanism_expected(r, m) is not None,
        lambda r, m: r.canonical_prescribed == _analyze_mechanism_expected(r, m),
    ),
    _metric_entry(
        "family_selection_accuracy",
        "case supported (group specialized|generic) có expected_family",
        lambda r, m: _is_supported(r) and r.expected_family is not None,
        lambda r, m: r.final_family == r.expected_family,
    ),
    _metric_entry(
        "variant_selection_accuracy",
        f"case supported có expected_initial_route == '{_VARIANT_SELECTION_INITIAL_ROUTE}'",
        lambda r, m: _is_supported(r) and r.expected_initial_route == _VARIANT_SELECTION_INITIAL_ROUTE,
        lambda r, m: r.final_route == r.expected_final_route,
    ),
    _metric_entry(
        "initial_route_accuracy",
        "case supported (group specialized|generic)",
        lambda r, m: _is_supported(r),
        lambda r, m: r.initial_route == r.expected_initial_route,
    ),
    _metric_entry(
        "final_route_accuracy",
        "case supported",
        lambda r, m: _is_supported(r),
        lambda r, m: r.envelope_status == "ok" and r.final_route == r.expected_final_route,
    ),
    _metric_entry(
        "valid_spec_first_attempt_rate",
        "case supported có ít nhất 1 simulate_attempt",
        lambda r, m: _is_supported(r) and len(r.simulate_attempts) >= 1,
        lambda r, m: r.first_attempt_ok is True,
    ),
    _metric_entry(
        "semantic_pass_rate",
        "case supported có semantic_ok khác None",
        lambda r, m: _is_supported(r) and r.semantic_ok is not None,
        lambda r, m: r.semantic_ok is True,
    ),
    _metric_entry(
        "false_refusal_rate",
        "case supported",
        lambda r, m: _is_supported(r),
        lambda r, m: _is_refused(r),
    ),
    _metric_entry(
        "unsupported_recall",
        "case group == 'unsupported'",
        lambda r, m: r.group == "unsupported",
        lambda r, m: _is_refused(r),
    ),
    _metric_entry(
        "unsupported_precision",
        "case bị refused (envelope_status == 'unsupported')",
        lambda r, m: _is_refused(r),
        lambda r, m: r.group == "unsupported",
    ),
    _metric_entry(
        "false_positive_simulation_rate",
        "case group == 'unsupported'",
        lambda r, m: r.group == "unsupported",
        lambda r, m: r.envelope_status == "ok",
    ),
    _metric_entry(
        "generic_fallback_leak_rate",
        "case group == 'unsupported' có m16.algorithmic_request == True",
        lambda r, m: r.group == "unsupported" and _algorithmic_request(r, m),
        lambda r, m: r.envelope_status == "ok" and r.final_route == "generic.rule_scene",
    ),
    _metric_entry(
        "reclassification_rate",
        "",  # mẫu số CHÍNH LÀ product case, không thêm điều kiện nào khác
        lambda r, m: True,
        lambda r, m: r.reclassify_attempted is True,
    ),
    _metric_entry(
        "route_recovery_success_rate",
        "case reclassify_attempted có m16.recovery_route_exists == True",
        lambda r, m: r.reclassify_attempted and _recovery_route_exists(r, m),
        lambda r, m: (
            r.reclassify_attempted and r.envelope_status == "ok" and r.final_route == r.expected_final_route
        ),
    ),
    _metric_entry(
        "concrete_envelope_integrity",
        "mọi ok envelope",
        lambda r, m: r.envelope_status == "ok",
        lambda r, m: (
            r.final_route is not None and r.final_route in CATALOG and r.final_route not in _SELECTOR_TOKENS
        ),
    ),
    # #17 KHÔNG gate product-case (phân xử review Task 3): brief cố ý dùng
    # "mọi evaluated case" — nếu lọc infra_error thì parity tự-triệt-tiêu đúng
    # tín hiệu nó phải bắt (record không đi qua production pipeline / harness
    # crash trước pipeline), làm mù bất biến #22.
    (
        "production_evaluation_parity",
        "mọi evaluated case (KHÔNG lọc product-case — bắt cả infra_error)",
        lambda r, m: True,
        lambda r, m: r.via_production_pipeline is True,
    ),
)


def _compute_metric(
    name: str,
    rule: str,
    den_pred: _Pred,
    num_pred: _Pred,
    records: Sequence[M16CaseRecord],
    m16_by_case: Mapping[str, M16Expectation] | None,
) -> MetricValue:
    den_records = [r for r in records if den_pred(r, m16_by_case)]
    num = sum(1 for r in den_records if num_pred(r, m16_by_case))
    return MetricValue.of(name, num, len(den_records))


def _excluded_case_ids(
    den_pred: _Pred, records: Sequence[M16CaseRecord], m16_by_case: Mapping[str, M16Expectation] | None
) -> list[str]:
    return [r.case_id for r in records if not den_pred(r, m16_by_case)]


def _metric_by_name(name: str) -> tuple[str, str, _Pred, _Pred]:
    for entry in _METRIC_REGISTRY:
        if entry[0] == name:
            return entry
    raise KeyError(f"metric M16 không tồn tại: {name!r}")


def _make_public_metric_fn(name: str) -> Callable[..., MetricValue]:
    def fn(
        records: Sequence[M16CaseRecord],
        m16_by_case: Mapping[str, M16Expectation] | None = None,
    ) -> MetricValue:
        _, rule, den_pred, num_pred = _metric_by_name(name)
        return _compute_metric(name, rule, den_pred, num_pred, records, m16_by_case)

    fn.__name__ = f"metric_{name}"
    return fn


# 16 hàm public — metric_<name>(records, m16_by_case=None) -> MetricValue.
metric_analyze_mechanism_accuracy = _make_public_metric_fn("analyze_mechanism_accuracy")
metric_family_selection_accuracy = _make_public_metric_fn("family_selection_accuracy")
metric_variant_selection_accuracy = _make_public_metric_fn("variant_selection_accuracy")
metric_initial_route_accuracy = _make_public_metric_fn("initial_route_accuracy")
metric_final_route_accuracy = _make_public_metric_fn("final_route_accuracy")
metric_valid_spec_first_attempt_rate = _make_public_metric_fn("valid_spec_first_attempt_rate")
metric_semantic_pass_rate = _make_public_metric_fn("semantic_pass_rate")
metric_false_refusal_rate = _make_public_metric_fn("false_refusal_rate")
metric_unsupported_recall = _make_public_metric_fn("unsupported_recall")
metric_unsupported_precision = _make_public_metric_fn("unsupported_precision")
metric_false_positive_simulation_rate = _make_public_metric_fn("false_positive_simulation_rate")
metric_generic_fallback_leak_rate = _make_public_metric_fn("generic_fallback_leak_rate")
metric_reclassification_rate = _make_public_metric_fn("reclassification_rate")
metric_route_recovery_success_rate = _make_public_metric_fn("route_recovery_success_rate")
metric_concrete_envelope_integrity = _make_public_metric_fn("concrete_envelope_integrity")
metric_production_evaluation_parity = _make_public_metric_fn("production_evaluation_parity")


def metric_retry_channels(
    records: Sequence[M16CaseRecord],
    m16_by_case: Mapping[str, M16Expectation] | None = None,  # không dùng — chữ ký nhất quán
) -> RetryChannels:
    """Metric #15 — BA kênh RIÊNG, không trộn (brief §4 #15). Là MỘT trong 17
    metric nên cũng đo trên "product case" (brief Aggregation: "micro: mỗi
    metric trên toàn product cases") — loại infra_error/internal-fixture
    trước khi đếm/tính avg."""
    del m16_by_case
    product_records = [r for r in records if _is_product_case(r)]
    n = len(product_records)
    semantic_total = sum(max(0, len(r.simulate_attempts) - 1) for r in product_records)
    transient_total = sum(r.budget_delta.get("retry_requests", 0) for r in product_records)
    reclassify_total = sum(1 for r in product_records if r.reclassify_attempted)

    def _avg(total: int) -> float | None:
        return (total / n) if n else None

    return RetryChannels(
        semantic_retries_total=semantic_total,
        semantic_retries_avg=_avg(semantic_total),
        transient_retries_total=transient_total,
        transient_retries_avg=_avg(transient_total),
        reclassify_count_total=reclassify_total,
        reclassify_count_avg=_avg(reclassify_total),
    )


# ── failure taxonomy (brief §5 — CHỈ field có cấu trúc, không đọc message) ─
def classify_failures(
    record: M16CaseRecord,
    m16_by_case: Mapping[str, M16Expectation] | None = None,
    *,
    oracle_mismatch: bool = False,
) -> list[str]:
    """Trả list category (có thể RỖNG hoặc NHIỀU phần tử — một case có thể
    đồng thời sai ở nhiều tầng, vd lỗi initial-family NHƯNG cuối cùng recovery
    đúng vẫn giữ CẢ hai bản ghi). `oracle_mismatch`: cờ CALLER truyền cho
    EXECUTOR_ORACLE_MISMATCH — reserved, hiện không record nào có nguồn thật
    (brief §5, field record-level tương lai)."""
    cats: list[str] = []

    if record.budget_delta.get("transient_hits", 0) > 0:
        cats.append("TRANSIENT_PROVIDER_ERROR")

    if record.infra_error is not None:
        cats.append("EVALUATION_INFRASTRUCTURE_ERROR")

    expected_mech = _analyze_mechanism_expected(record, m16_by_case)
    if expected_mech is not None and record.canonical_prescribed != expected_mech:
        cats.append("ANALYZE_MECHANISM_ERROR")

    supported = _is_supported(record)
    if supported and record.initial_family != record.expected_family:
        cats.append("INITIAL_FAMILY_SELECTION_ERROR")

    if supported and any(a.get("error_code") == "mechanism_variant_mismatch" for a in record.simulate_attempts):
        cats.append("INITIAL_VARIANT_SELECTION_ERROR")

    if any(g.get("gate") == "route_mechanism" and g.get("fired") is True for g in record.gates):
        cats.append("ROUTE_MECHANISM_FAMILY_MISMATCH")

    if record.reclassify_attempted and _recovery_route_exists(record, m16_by_case):
        recovered = record.envelope_status == "ok" and record.final_route == record.expected_final_route
        if not recovered:
            cats.append("ROUTE_RECOVERY_FAILED")

    gate_ownership_fired = any(
        g.get("gate") == "mechanism" and g.get("fired") is True and g.get("reason_code") == "gate_mechanism_ownership"
        for g in record.gates
    )
    if record.envelope_error_code == "gate_mechanism_ownership" or gate_ownership_fired:
        cats.append("GATE_MECHANISM_OWNERSHIP")

    all_fail = _all_attempts_failed(record)
    last_code = _last_attempt_error_code(record)

    if all_fail and last_code == "family_spec_invalid":
        cats.append("FAMILY_SPEC_INVALID")

    if all_fail and last_code == "structural_invalid":
        cats.append("CONCRETE_CONFIG_INVALID")

    if record.semantic_ok is False or (all_fail and last_code in _SEMANTIC_FAIL_ERROR_CODES):
        cats.append("SEMANTIC_VALIDATION_FAILED")

    if supported and _is_refused(record):
        cats.append("FALSE_REFUSAL")

    if record.group == "unsupported" and record.envelope_status == "ok":
        cats.append("FALSE_POSITIVE_SIMULATION")

    if (
        record.group == "unsupported"
        and _algorithmic_request(record, m16_by_case)
        and record.envelope_status == "ok"
        and record.final_route == "generic.rule_scene"
    ):
        cats.append("GENERIC_FALLBACK_LEAK")

    if oracle_mismatch:
        cats.append("EXECUTOR_ORACLE_MISMATCH")

    return cats


def failure_distribution(
    records: Sequence[M16CaseRecord],
    m16_by_case: Mapping[str, M16Expectation] | None = None,
    *,
    oracle_mismatch_ids: frozenset[str] = frozenset(),
) -> dict[str, int]:
    """Đếm failure category theo taxonomy trên TOÀN BỘ `records` — KHÁC với
    16 metric tỉ lệ + #15 (đều gate qua `_is_product_case`, brief Aggregation
    "micro: mỗi metric trên toàn product cases"): taxonomy là view CHẨN ĐOÁN
    thô, cần thấy CẢ case infra để EVALUATION_INFRASTRUCTURE_ERROR có ý
    nghĩa (nếu lọc trước, category này không bao giờ bắn được)."""
    dist: dict[str, int] = {}
    for r in records:
        for cat in classify_failures(r, m16_by_case, oracle_mismatch=r.case_id in oracle_mismatch_ids):
            dist[cat] = dist.get(cat, 0) + 1
    return dist


# ── aggregation (brief §4 "Aggregation") ─────────────────────────────────
def _family_bucket(record: M16CaseRecord) -> str:
    return record.expected_family if record.expected_family is not None else "unlabeled"


@dataclass(frozen=True)
class MetricAggregate:
    """Một metric tỉ lệ gộp đủ 3 tầng: micro (toàn quần thể), per_family
    (dict family→MetricValue, kể cả bucket "unlabeled" — case không m16),
    macro (mean per-family value, LOẠI "unlabeled" và LOẠI family value=None
    — brief §4 Aggregation), `excluded_families` liệt kê family bị loại khỏi
    macro (vì lý do nào trong hai lý do trên)."""

    name: str
    micro: MetricValue
    per_family: dict[str, MetricValue]
    macro: float | None
    excluded_families: list[str]


def confusion_matrix(records: Sequence[M16CaseRecord]) -> dict[str, dict[str, int]]:
    """rows = expected_final_route (None → "expected_refusal"); cols = actual
    outcome (final_route khi ok; "refused" khi unsupported; "error" khi
    envelope_status None) — dict lồng {expected: {actual: count}}."""
    matrix: dict[str, dict[str, int]] = {}
    for r in records:
        row = r.expected_final_route if r.expected_final_route is not None else "expected_refusal"
        if r.envelope_status == "ok":
            col = r.final_route if r.final_route is not None else "error"
        elif r.envelope_status == "unsupported":
            col = "refused"
        else:
            col = "error"
        row_bucket = matrix.setdefault(row, {})
        row_bucket[col] = row_bucket.get(col, 0) + 1
    return matrix


def applicability_report(
    records: Sequence[M16CaseRecord], m16_by_case: Mapping[str, M16Expectation] | None = None
) -> dict[str, dict]:
    """Mỗi metric tỉ lệ → {rule: mô tả predicate một câu, excluded_case_ids}
    — MÁY-ĐỌC (derive từ CHÍNH predicate mẫu-số dùng để tính metric, không
    loại case thủ công). #15 (retry_channels) dùng CÙNG cổng product-case
    (xem `metric_retry_channels`) nên excluded_case_ids tính tương tự."""
    report: dict[str, dict] = {}
    for name, rule, den_pred, _num_pred in _METRIC_REGISTRY:
        report[name] = {
            "rule": rule,
            "excluded_case_ids": _excluded_case_ids(den_pred, records, m16_by_case),
        }
    report["retry_channels"] = {
        "rule": _PRODUCT_CASE_RULE,
        "excluded_case_ids": [r.case_id for r in records if not _is_product_case(r)],
    }
    return report


@dataclass(frozen=True)
class AggregateResult:
    run_label: str
    case_count: int
    metrics: dict[str, MetricAggregate]  # 16 metric tỉ lệ, key = name
    retry_channels: RetryChannels  # metric #15 — kênh riêng
    confusion_matrix: dict[str, dict[str, int]]
    failure_distribution: dict[str, int]
    applicability_report: dict[str, dict]


def aggregate(
    records: Sequence[M16CaseRecord],
    run_label: str,
    m16_by_case: Mapping[str, M16Expectation] | None = None,
    *,
    oracle_mismatch_ids: frozenset[str] = frozenset(),
) -> AggregateResult:
    """Tổng hợp đủ 17 metric + taxonomy + confusion matrix trên `records`.

    `run_label` ∈ {"offline","live_baseline","live_postfix"} — tham số THUẦN
    (đưa vào kết quả để caller phân biệt, hàm này KHÔNG lưu trạng thái toàn
    cục nên gọi hai lần với hai run KHÁC NHAU không bao giờ ghi đè lẫn nhau —
    caller tự giữ hai `AggregateResult` riêng)."""
    if run_label not in _VALID_RUN_LABELS:
        raise ValueError(f"run_label không hợp lệ: {run_label!r} (phải ∈ {sorted(_VALID_RUN_LABELS)})")

    records = list(records)

    families = sorted({_family_bucket(r) for r in records})
    metrics: dict[str, MetricAggregate] = {}
    for name, rule, den_pred, num_pred in _METRIC_REGISTRY:
        micro = _compute_metric(name, rule, den_pred, num_pred, records, m16_by_case)
        per_family: dict[str, MetricValue] = {}
        for fam in families:
            subset = [r for r in records if _family_bucket(r) == fam]
            per_family[fam] = _compute_metric(name, rule, den_pred, num_pred, subset, m16_by_case)
        macro_inputs = [mv.value for fam, mv in per_family.items() if fam != "unlabeled" and mv.value is not None]
        excluded = sorted(fam for fam, mv in per_family.items() if fam == "unlabeled" or mv.value is None)
        macro = (sum(macro_inputs) / len(macro_inputs)) if macro_inputs else None
        metrics[name] = MetricAggregate(
            name=name, micro=micro, per_family=per_family, macro=macro, excluded_families=excluded
        )

    return AggregateResult(
        run_label=run_label,
        case_count=len(records),
        metrics=metrics,
        retry_channels=metric_retry_channels(records, m16_by_case),
        confusion_matrix=confusion_matrix(records),
        failure_distribution=failure_distribution(records, m16_by_case, oracle_mismatch_ids=oracle_mismatch_ids),
        applicability_report=applicability_report(records, m16_by_case),
    )


__all__ = [
    "MetricValue",
    "RetryChannels",
    "MetricAggregate",
    "AggregateResult",
    "FAILURE_CATEGORIES",
    "quality_band",
    "classify_failures",
    "failure_distribution",
    "confusion_matrix",
    "applicability_report",
    "aggregate",
    "metric_analyze_mechanism_accuracy",
    "metric_family_selection_accuracy",
    "metric_variant_selection_accuracy",
    "metric_initial_route_accuracy",
    "metric_final_route_accuracy",
    "metric_valid_spec_first_attempt_rate",
    "metric_semantic_pass_rate",
    "metric_false_refusal_rate",
    "metric_unsupported_recall",
    "metric_unsupported_precision",
    "metric_false_positive_simulation_rate",
    "metric_generic_fallback_leak_rate",
    "metric_reclassification_rate",
    "metric_route_recovery_success_rate",
    "metric_retry_channels",
    "metric_concrete_envelope_integrity",
    "metric_production_evaluation_parity",
]
