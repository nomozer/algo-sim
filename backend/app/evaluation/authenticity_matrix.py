# -*- coding: utf-8 -*-
"""M17-Lite W0 — case matrix audit SINH TỪ REGISTRY (không hard-code test ID).

``build_audit_cases()`` duyệt CATALOG thật (AI-reachable) × archetype, cộng
near-miss dedupe theo cơ chế trong AUTHENTICITY_CONTRACTS, cộng control/
regression. Hệ quả cấu trúc:

- Thêm target thứ 15 mà quên fixture → KeyError ngay khi build (lock cứng,
  không lặng lẽ bỏ sót);
- Thêm cơ chế vào INTENTIONAL_GAP_MECHANISMS mà quên near-miss fixture →
  KeyError (mỗi intentional gap LUÔN có case gap-trigger);
- Không case nào được chọn theo id — id là DẪN XUẤT từ (target, archetype).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.evaluation.authenticity_fixtures import (
    CONTROL_FIXTURES,
    NEAR_MISS_FIXTURES,
    OK_ARCHETYPES,
    TARGET_FIXTURES,
    CaseScript,
)
from app.simulation.authenticity import AUTHENTICITY_CONTRACTS
from app.simulation.catalog import CATALOG
from app.simulation.descriptor import ReachabilityLevel


@dataclass(frozen=True)
class AuditCase:
    case_id: str
    sim_id: str | None  # target được audit; None cho case control/near-miss
    archetype: str  # direct|paraphrase|changed_input|boundary|near_miss|leak_control|refusal_control|leak_probe
    prompt_vi: str
    script: CaseScript
    expected_status: str  # "ok" | "unsupported" | "probe"
    expected_route: str | None  # id CONCRETE kỳ vọng khi ok
    mechanism: str | None = None
    note: str = ""
    # M17-RC1 §C — metadata quy kết slot/target cho case control (mặc định None,
    # không đổi hành vi W0/W1). Xem ControlFixture.audit_slot.
    audit_slot: str | None = None
    audit_target: str | None = None


def _slug(sim_id: str) -> str:
    return sim_id.replace(".", "-").replace("_", "-")


def ai_reachable_ids() -> list[str]:
    return sorted(
        sid
        for sid, spec in CATALOG.items()
        if ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
    )


def build_audit_cases() -> list[AuditCase]:
    cases: list[AuditCase] = []

    # ── per-target × archetype (sinh từ CATALOG, thứ tự tất định) ──
    for sid in ai_reachable_ids():
        fx = TARGET_FIXTURES[sid]  # KeyError = target mới thiếu fixture → đỏ
        for arch in OK_ARCHETYPES:
            if arch not in fx.scripts:
                continue
            assert arch in fx.prompts, f"{sid}: fixture có script {arch} nhưng thiếu prompt"
            cases.append(
                AuditCase(
                    case_id=f"aud-{_slug(sid)}-{arch.replace('_', '-')}",
                    sim_id=sid,
                    archetype=arch,
                    prompt_vi=fx.prompts[arch],
                    script=fx.scripts[arch],
                    expected_status="ok",
                    expected_route=sid,
                )
            )

    # ── near-miss: dedupe theo cơ chế khai trong contract ──
    mechanisms = sorted(
        {nm for c in AUTHENTICITY_CONTRACTS.values() for nm in c.near_miss_mechanisms}
    )
    for mech in mechanisms:
        fx = NEAR_MISS_FIXTURES[mech]  # KeyError = intentional gap thiếu fixture → đỏ
        cases.append(
            AuditCase(
                case_id=fx.case_id,
                sim_id=None,
                archetype="near_miss",
                prompt_vi=fx.prompt,
                script=fx.script,
                expected_status="unsupported",
                expected_route=None,
                mechanism=mech,
                note=fx.note,
            )
        )

    # ── control + regression (leak / refusal / probe) ──
    for fx in CONTROL_FIXTURES:
        cases.append(
            AuditCase(
                case_id=fx.case_id,
                sim_id=None,
                archetype=fx.kind,
                prompt_vi=fx.prompt,
                script=fx.script,
                expected_status=fx.expected_status,
                expected_route=(
                    fx.expected_route or "generic.rule_scene"
                ) if fx.expected_status == "ok" else None,
                mechanism=fx.mechanism,
                note=fx.note,
                audit_slot=fx.audit_slot,
                audit_target=fx.audit_target,
            )
        )

    # id duy nhất (phòng fixture trùng)
    ids = [c.case_id for c in cases]
    assert len(ids) == len(set(ids)), "case_id trùng trong audit matrix"
    return cases
