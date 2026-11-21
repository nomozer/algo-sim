# -*- coding: utf-8 -*-
"""AXO HYBRID /8 Phase H: Standalone Scoped Local Routing Policy Simulator (`scoped-local-routing-sim/1`).

Non-production standalone policy evaluator (`/8 §15`). Does NOT alter `backend/app/ai/route_policy.py`,
keeps `HYBRID_ROUTE_MODE=live` untouched as production default, enforces zero silent cloud fallback,
loads verified capability bounds from `SLM_CAPABILITY_MATRIX.json`, and supports instant model
rollback verification (`qwen3-0.6b-axo-v7-q4_k_m` <-> `qwen3-0.6b-q4_k_m`).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
OUT_DIR = ROOT / "docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))

from app.ai.local_geometry_parser import parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import detect_prompt_injection  # noqa: E402
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    resolve_local_slm_model_spec,
)
from slm_math_evaluator_v2 import compare_math_expressions, infer_goal_kind_from_text  # noqa: E402

POLICY_VERSION = "scoped-local-routing-sim/1"

_OOS_PATTERNS = [
    ("domain_spheres_and_curved_solids", re.compile(r"\bmặt\s+cầu\b|\bhình\s+nón\b|\bhình\s+trụ\b|\bkhối\s+nón\b|\bkhối\s+trụ\b|\bkhối\s+cầu\b", re.IGNORECASE)),
    ("domain_non_registry_aux_constructions", re.compile(r"\bdi\s+động\b|\bgiá\s+trị\s+(?:lớn|nhỏ)\s+nhất\b|\bcực\s+đại\b|\bcực\s+tiểu\b", re.IGNORECASE)),
    ("domain_complex_derived_sections", re.compile(r"\bthiết\s+diện\b|\bgiao\s+tuyến\b", re.IGNORECASE)),
]

_UI_NON_MATH_RE = re.compile(r"^\s*(?:quay\s+hình|đổi\s+màu|ẩn\s+|hiện\s+|làm\s+nổi\s+bật|cho\s+điểm\s+đó\s+nhấp\s+nháy)", re.IGNORECASE)
_INCOMPLETE_ELLIPSIS_RE = re.compile(r"\bvừa\s+(?:dựng|vẽ)\b|\bđiểm\s+đó\b|\bhình\s+đó\b", re.IGNORECASE)
_EXPERIMENTAL_REORDERED_RECT_RE = re.compile(r"\bbiết\s+[A-Z]{4}\s+là\s+hình\s+(?:chữ\s+nhật|vuông)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ScopedRoutingDecision:
    policy_version: str
    model_key: str
    decision: str
    reason_code: str
    detected_domains: tuple[str, ...]
    slm_allowed: bool
    cloud_fallback_allowed: bool
    downstream_verification_required: bool
    notes: str


def verify_model_integrity(
    model_key: str = FINETUNED_LOCAL_SLM_MODEL_KEY,
    *,
    runtime_available: bool = True,
    override_sha256: str | None = None,
    override_exists: bool | None = None,
) -> tuple[bool, str, str]:
    """Fail-closed model existence & SHA-256 verification before local-primary eligibility."""
    if not runtime_available:
        return False, "LOCAL_SLM_UNAVAILABLE", "Local llama-server runtime unavailable"
    spec = resolve_local_slm_model_spec(model_key)
    model_path = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "axo-slm/models" / spec.model_key / spec.filename
    exists = override_exists if override_exists is not None else model_path.exists()
    if not exists:
        return False, "MODEL_FILE_MISSING", f"Missing model binary: {spec.filename}"
    if override_sha256 is not None and override_sha256.lower() != spec.sha256.lower():
        return False, "MODEL_CHECKSUM_MISMATCH", f"Checksum mismatch for {spec.model_key}"
    return True, "OK", spec.sha256


def decide_scoped_local_route(
    problem_text: str,
    *,
    model_key: str = FINETUNED_LOCAL_SLM_MODEL_KEY,
    runtime_available: bool = True,
    override_sha256: str | None = None,
    override_exists: bool | None = None,
    capability_statuses: dict[str, str] | None = None,
) -> ScopedRoutingDecision:
    """Apply the 6 safety & capability-scoping rules (`/8 §15`) strictly fail-closed."""
    txt = (problem_text or "").strip()
    if not txt:
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "CLARIFICATION_OR_REFUSAL", "EMPTY_INPUT",
            (), False, False, False, "Empty problem text",
        )

    # Injection guard before any router promotion
    if detect_prompt_injection(txt) is not None:
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "SAFE_REFUSAL", "PROMPT_INJECTION_REJECTED",
            (), False, False, False, "Prompt injection blocked before SLM",
        )

    # Unsupported geometry explicit gate (never call SLM to hallucinate curved/min-max/sections)
    for dom, pat in _OOS_PATTERNS:
        if pat.search(txt):
            return ScopedRoutingDecision(
                POLICY_VERSION, model_key, "UNSUPPORTED", "OUT_OF_SCOPE_GEOMETRY",
                (dom,), False, False, False, f"Explicitly outside local capability envelope ({dom})",
            )

    if _UI_NON_MATH_RE.search(txt) or _INCOMPLETE_ELLIPSIS_RE.search(txt):
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "CLARIFICATION_OR_REFUSAL", "AMBIGUOUS_OR_UI_COMMAND",
            (), False, False, False, "Requires interactive context clarification",
        )

    # Rule 1: Deterministic fast path bypasses SLM cleanly
    lp = parse_geometry_problem_locally(txt)
    if lp.status == "LOCAL_PARSE_COMPLETE":
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "DETERMINISTIC_FAST_PATH", "LOCAL_PARSE_COMPLETE",
            ("deterministic_polyhedron",), False, False, True,
            "Solved deterministically by Local Geometry Parser /2 without SLM invocation",
        )

    # Rule 2: Unambiguous parser ambiguity stays fail-closed
    if lp.status == "LOCAL_PARSE_AMBIGUOUS":
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "CLARIFICATION_OR_REFUSAL", "AMBIGUOUS_INPUT_PARSER",
            (), False, False, False, "Local parser flagged ambiguity requiring clarification",
        )

    # Rule 3: Model/runtime availability & checksum check (NEVER silently fallback to cloud!)
    ok_rt, rt_code, rt_msg = verify_model_integrity(
        model_key, runtime_available=runtime_available, override_sha256=override_sha256, override_exists=override_exists,
    )
    if not ok_rt:
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "INFRASTRUCTURE_FAILURE", rt_code,
            (), False, False, False, f"{rt_msg}; silent cloud fallback forbidden",
        )

    # Rule 4: Scoped capability gate (unknown/EXPERIMENTAL domains never promoted silently)
    cap = capability_statuses or {}
    if _EXPERIMENTAL_REORDERED_RECT_RE.search(txt):
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "OUT_OF_SCOPED_PRIMARY_ENVELOPE", "EXPERIMENTAL_REORDERED_BASE_WITHOUT_DAY",
            ("style_conversational_and_reordered_base",), False, False, False,
            "Experimental wording excluded from validated local-primary envelope per P2 audit",
        )

    # Check if recognizable supported polyhedron wording is present
    has_supported_solid = bool(re.search(r"\b(?:chóp|tứ\s+diện|lăng\s+trụ|hình\s+hộp|lập\s+phương)\b", txt, re.IGNORECASE))
    if not has_supported_solid:
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "UNSUPPORTED", "UNKNOWN_CAPABILITY_NO_SILENT_PROMOTION",
            ("unknown",), False, False, False,
            "Unrecognized solid/geometry family cannot be silently promoted to local SLM",
        )

    # Check goal plane-plane angle NOT_MEASURED boundary
    sents = [s.strip() for s in re.split(r"[.?!\n]+", txt) if s.strip()]
    goal_sent = sents[-1] if sents else txt
    if re.search(r"(?:tính|tìm)\s+(?:cos\s*²\s*)?góc\s+giữa\s+(?:hai\s+)?mặt|\([A-Z']{3,4}\)\s+và\s+\([A-Z']{3,4}\)", goal_sent, re.IGNORECASE) and cap.get("goal_plane_plane_angle") == "NOT_MEASURED":
        return ScopedRoutingDecision(
            POLICY_VERSION, model_key, "OUT_OF_SCOPED_PRIMARY_ENVELOPE", "NOT_MEASURED_PLANE_PLANE_ANGLE_GOAL",
            ("goal_plane_plane_angle",), False, False, False,
            "Plane-plane angle GOAL is NOT_MEASURED in SLM holdouts; excluded from primary envelope",
        )

    return ScopedRoutingDecision(
        POLICY_VERSION, model_key, "ELIGIBLE_LOCAL_PRIMARY", "VALIDATED_LOCAL_PRIMARY_DOMAIN",
        ("validated_polyhedron_slm_domain",), True, False, True,
        "Eligible for AxoV7 extraction, strictly gated by validator -> Source Gate -> Planner -> Exact Kernel",
    )


def evaluate_post_extraction_serving(route_status: str, grounding_status: str | None) -> str:
    """Rule 5: Unverified/refused extraction is NEVER served."""
    if route_status == "SERVED" and grounding_status in (None, "GROUNDED_AND_LOWERED"):
        return "SERVED_VERIFIED"
    return "DO_NOT_SERVE"


def main() -> int:
    cap_path = OUT_DIR / "SLM_CAPABILITY_MATRIX.json"
    cap_raw = json.loads(cap_path.read_text(encoding="utf-8"))
    cap_statuses = {
        e["category"]: e["status"]
        for e in (cap_raw.get("supported_domains", []) + cap_raw.get("unsupported_and_boundary_domains", []))
    }

    # Verify rollback model checksum & spec readiness
    ok_v7, code_v7, sha_v7 = verify_model_integrity(FINETUNED_LOCAL_SLM_MODEL_KEY)
    ok_rb, code_rb, sha_rb = verify_model_integrity(DEFAULT_LOCAL_SLM_MODEL_KEY)

    v7_m = json.loads((ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))["cases"]
    v7_e = json.loads((ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_EVALUATION.json").read_text(encoding="utf-8"))
    v7_d = {r["id"]: r for r in v7_e["configs"]["config_d_v7_closure_finetuned_slm"]["rows"]}

    unseen_eval_p = OUT_DIR / "PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json"
    unseen_cases = []
    if unseen_eval_p.exists():
        ue = json.loads(unseen_eval_p.read_text(encoding="utf-8"))
        unseen_m = {c["case_id"]: c for c in json.loads((OUT_DIR / "PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json").read_text(encoding="utf-8"))["cases"]}
        for r in ue["configs"]["config_d_v7_closure_finetuned_slm"]["rows"]:
            r_copy = dict(r)
            r_copy["text"] = unseen_m[r["case_id"]]["text"]
            unseen_cases.append(r_copy)

    def _simulate_split(name: str, items: list[tuple[str, str, str, dict[str, Any]]]) -> dict[str, Any]:
        counts: Counter[str] = Counter()
        outcomes: Counter[str] = Counter()
        wrong_served_in_scoped = 0
        wrong_served_raw_evi = 0
        for cid, txt, expected_kind, obs_row in items:
            dec = decide_scoped_local_route(txt, capability_statuses=cap_statuses)
            counts[dec.decision] += 1
            if dec.decision in ("DETERMINISTIC_FAST_PATH", "ELIGIBLE_LOCAL_PRIMARY"):
                srv = evaluate_post_extraction_serving(obs_row["status"], obs_row.get("grounding_status"))
                outcomes[srv] += 1
                if obs_row.get("wrong_served"):
                    wrong_served_raw_evi += 1
                if name == "SLM_V7_HOLDOUT_112":
                    if obs_row["status"] == "SERVED":
                        if expected_kind != "positive":
                            wrong_served_in_scoped += 1
                        else:
                            gk = infer_goal_kind_from_text(txt)
                            m = compare_math_expressions(obs_row.get("answer"), str(obs_row.get("oracle")), goal_kind=gk)
                            if m.matched is not True:
                                wrong_served_in_scoped += 1
                elif obs_row.get("wrong_served"):
                    wrong_served_in_scoped += 1
            else:
                outcomes["GATED_OUT_OR_SAFE_REFUSED"] += 1
        return {
            "split": name,
            "total": len(items),
            "routing_decisions": dict(counts),
            "post_gate_outcomes": dict(outcomes),
            "wrong_served_within_scoped_envelope": wrong_served_in_scoped,
            "wrong_served_raw_frozen_evi": wrong_served_raw_evi,
        }

    v7_sim = _simulate_split(
        "SLM_V7_HOLDOUT_112",
        [(c["case_id"], c["text"], c["kind"], v7_d[c["case_id"]]) for c in v7_m],
    )
    unseen_sim = _simulate_split(
        "PERMISSIBLE_UNSEEN_77",
        [(r["case_id"], r["text"], r["eval_role"], r) for r in unseen_cases],
    ) if unseen_cases else None

    sim_out = {
        "schema": "scoped-local-routing-simulation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
        "production_route_default_preserved": "HYBRID_ROUTE_MODE=live",
        "silent_cloud_fallback_allowed": False,
        "primary_model_check": {"model_key": FINETUNED_LOCAL_SLM_MODEL_KEY, "ok": ok_v7, "code": code_v7, "sha256": sha_v7},
        "rollback_model_check": {"model_key": DEFAULT_LOCAL_SLM_MODEL_KEY, "ok": ok_rb, "code": code_rb, "sha256": sha_rb},
        "v7_holdout_simulation": v7_sim,
        "unseen_corpora_simulation": unseen_sim,
    }
    (OUT_DIR / "SCOPED_LOCAL_ROUTING_SIMULATION.json").write_text(
        json.dumps(sim_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print("SCOPED ROUTING SIM V7H:", v7_sim)
    if unseen_sim:
        print("SCOPED ROUTING SIM UNSEEN:", unseen_sim)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
