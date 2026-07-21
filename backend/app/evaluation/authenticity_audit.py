# -*- coding: utf-8 -*-
"""M17-Lite W0 — runner audit authenticity qua production ``run_pipeline``.

Bất biến #22: MỌI case đi qua đúng orchestration production (analyze → plan →
classify → reclassify-bounded → gates → simulate) với ``AttemptObserver`` thụ
động — KHÔNG dựng pipeline mirror. Record dựng THUẦN từ structured events +
envelope (message text không tham gia phân loại — nguyên tắc M16).

Phân loại 6 trạng thái (đóng):
- REAL                — target computation-authority, mọi ok-archetype đạt;
- PARTIAL             — target mang CẢ computation lẫn representation authority
                        (generic: computation CHỈ cho boolean rule DAG);
- REPRESENTATION_ONLY — target chỉ representation authority (hiện: không có);
- GENERIC_LEAK        — đề đòi kết quả thuật toán nhưng generic trả ok;
- BROKEN              — ok-archetype thất bại (validator từ chối exemplar,
                        route sai, infra error);
- UNSUPPORTED         — near-miss/refusal được từ chối trung thực (mức cơ chế).
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import build_scripted_provider
from app.evaluation.authenticity_matrix import (
    AuditCase,
    ai_reachable_ids,
    build_audit_cases,
)
from app.evaluation.observer import AttemptObserver
from app.simulation.catalog import CATALOG
from app.simulation.descriptor import ResultAuthority
from app.simulation.families import FAMILY_SELECTORS

OK_STATUSES = ("ok", "unsupported")
_SELECTOR_TOKENS = frozenset(s.selector_token for s in FAMILY_SELECTORS.values())


@dataclass
class AuditRecord:
    """Quan sát CÓ CẤU TRÚC của một case — chỉ từ observer + envelope."""

    case_id: str
    sim_id: str | None
    archetype: str
    expected_status: str
    expected_route: str | None
    mechanism: str | None
    actual_status: str | None  # "ok"/"unsupported"/None (pipeline error)
    final_route: str | None
    initial_route: str | None
    reclassify_attempted: bool
    gates: list[dict] = field(default_factory=list)
    envelope_error_code: str | None = None
    failure_category: str | None = None
    simulate_attempts: int = 0
    pipeline_error: str | None = None
    matched: bool | None = None  # None cho probe (ghi nhận, không chấm đúng/sai)
    via_production_pipeline: bool = True


async def _run_one(case: AuditCase) -> AuditRecord:
    obs = AttemptObserver()
    envelope: dict | None = None
    pipeline_error: str | None = None
    try:
        envelope = await pipeline.run_pipeline(
            case.prompt_vi, "khoa-gia", pattern_store=None, observer=obs
        )
    except Exception as err:  # simulate thất bại sau retry → RuntimeError
        pipeline_error = str(err)

    classify = obs.classify()
    actual_status = envelope.get("status") if isinstance(envelope, dict) else None
    final_route = (
        envelope.get("simulation_id") if isinstance(envelope, dict) else None
    )
    rec = AuditRecord(
        case_id=case.case_id,
        sim_id=case.sim_id,
        archetype=case.archetype,
        expected_status=case.expected_status,
        expected_route=case.expected_route,
        mechanism=case.mechanism,
        actual_status=actual_status,
        final_route=final_route,
        initial_route=classify.get("simulation_id") if classify else None,
        reclassify_attempted=obs.reclassify_attempted() is not None,
        gates=[dict(g) for g in obs.gates()],
        envelope_error_code=(
            envelope.get("error_code") if isinstance(envelope, dict) else None
        ),
        failure_category=(
            envelope.get("failure_category") if isinstance(envelope, dict) else None
        ),
        simulate_attempts=len(obs.simulate_attempts()),
        pipeline_error=pipeline_error,
    )
    rec.matched = _match(case, rec)
    return rec


def _match(case: AuditCase, rec: AuditRecord) -> bool | None:
    """Chấm đúng/sai THEO CẤU TRÚC. Probe → None (ledger phân loại riêng)."""
    if case.expected_status == "probe":
        return None
    if rec.pipeline_error is not None:
        return False
    if case.expected_status == "ok":
        return (
            rec.actual_status == "ok"
            and rec.final_route == case.expected_route
            and rec.final_route in CATALOG  # id concrete thật
            and rec.final_route not in _SELECTOR_TOKENS  # token không bao giờ leak
        )
    # expected unsupported
    if rec.actual_status != "unsupported":
        return False
    if case.archetype == "near_miss":
        # gap trung thực: failure_category đúng + một gate route/mechanism đã bắn
        gate_fired = any(g.get("fired") for g in rec.gates)
        return rec.failure_category == "capability_gap" and gate_fired
    return True


def run_audit(set_provider) -> list[AuditRecord]:
    """Chạy TOÀN BỘ matrix. ``set_provider(fake)`` cài fake ``call_gemini``
    (test: monkeypatch.setattr; script: gán trực tiếp có try/finally)."""
    records: list[AuditRecord] = []
    for case in build_audit_cases():
        fake, _counts = build_scripted_provider(case.script)
        set_provider(fake)
        records.append(asyncio.run(_run_one(case)))
    return records


# ── phân loại 6 trạng thái per-target ─────────────────────────
def classify_targets(records: list[AuditRecord]) -> dict[str, str]:
    """Derive từ membership (không hard-code): computation+representation →
    PARTIAL; computation-only → REAL; representation-only →
    REPRESENTATION_ONLY; bằng chứng audit hỏng → BROKEN."""
    out: dict[str, str] = {}
    for sid in ai_reachable_ids():
        recs = [r for r in records if r.sim_id == sid]
        assert recs, f"{sid}: không có record audit nào (matrix hụt)"
        if any(r.matched is False for r in recs):
            out[sid] = "BROKEN"
            continue
        authorities = {
            m.result_authority for m in CATALOG[sid].family_memberships
        }
        if ResultAuthority.COMPUTATION in authorities and ResultAuthority.REPRESENTATION in authorities:
            out[sid] = "PARTIAL"
        elif ResultAuthority.COMPUTATION in authorities:
            out[sid] = "REAL"
        else:
            out[sid] = "REPRESENTATION_ONLY"
    return out


# ── generic leak ledger ───────────────────────────────────────
def leak_verdict(rec: AuditRecord) -> str:
    """Phán quyết cho case leak_control/leak_probe — từ structured record."""
    if rec.actual_status == "ok":
        if rec.final_route == "generic.rule_scene":
            return "CONDITIONAL_LEAK_CONFIRMED" if rec.archetype == "leak_probe" else "LEAK"
        # ok nhưng route CHUYÊN BIỆT (vd tree.traversal) → KHÔNG leak (đóng W2A)
        return "ROUTED_SPECIALIZED"
    if rec.actual_status == "unsupported":
        return "BLOCKED_FAIL_CLOSED"
    return "BLOCKED_BY_VALIDATOR"  # simulate không qua validator (pipeline_error)


def build_leak_ledger(records: list[AuditRecord]) -> list[dict]:
    ledger = []
    for r in records:
        if r.archetype not in ("leak_control", "leak_probe"):
            continue
        ledger.append(
            {
                "case_id": r.case_id,
                "archetype": r.archetype,
                "verdict": leak_verdict(r),
                "actual_status": r.actual_status,
                "final_route": r.final_route,
                "gates": r.gates,
                "failure_category": r.failure_category,
            }
        )
    return ledger


# ── metrics tổng hợp ──────────────────────────────────────────
def audit_metrics(records: list[AuditRecord], classifications: dict[str, str]) -> dict:
    by_arch: dict[str, dict] = {}
    for r in records:
        b = by_arch.setdefault(r.archetype, {"total": 0, "matched": 0, "probe": 0})
        b["total"] += 1
        if r.matched is True:
            b["matched"] += 1
        if r.matched is None:
            b["probe"] += 1

    near_miss = [r for r in records if r.archetype == "near_miss"]
    leak_records = [r for r in records if r.archetype in ("leak_control", "leak_probe")]
    unconditional = [
        r for r in leak_records
        if r.archetype == "leak_control" and leak_verdict(r) == "LEAK"
    ]
    conditional = [
        r for r in leak_records
        if r.archetype == "leak_probe" and leak_verdict(r) == "CONDITIONAL_LEAK_CONFIRMED"
    ]
    ok_records = [r for r in records if r.expected_status == "ok"]
    hist: dict[str, int] = {}
    for v in classifications.values():
        hist[v] = hist.get(v, 0) + 1

    return {
        "total_cases": len(records),
        "by_archetype": by_arch,
        "near_miss_gap_recall": {
            "numerator": sum(1 for r in near_miss if r.matched),
            "denominator": len(near_miss),
        },
        "false_refusal_on_ok_archetypes": sum(
            1 for r in ok_records if r.actual_status == "unsupported"
        ),
        "concrete_envelope_integrity": {
            "numerator": sum(
                1 for r in records
                if r.actual_status == "ok"
                and r.final_route in CATALOG
                and r.final_route not in _SELECTOR_TOKENS
            ),
            "denominator": sum(1 for r in records if r.actual_status == "ok"),
        },
        "production_parity": {
            "numerator": sum(1 for r in records if r.via_production_pipeline),
            "denominator": len(records),
        },
        "generic_leak": {
            "controls": len(leak_records),
            "unconditional_leaks": len(unconditional),
            "conditional_leaks_confirmed": len(conditional),
        },
        "classification_histogram": hist,
    }


def records_as_dicts(records: list[AuditRecord]) -> list[dict]:
    return [asdict(r) for r in records]
