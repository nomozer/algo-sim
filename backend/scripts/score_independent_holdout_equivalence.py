# -*- coding: utf-8 -*-
"""Pre-registered three-tier scorer (Mathematical / Semantic Goal / Strict Contract) & H-1 corpus sealing verifier.

STRICT OFFLINE & ISOLATION CONTRACT:
- Zero live network calls (`ALLOW_LIVE_AI=0`); zero edits to frozen `backend/app/**` or locked C16/C21/C26 scripts.
- Reuses `run_paired_route_evaluation`, `run_s2_student_language_pilot`, and `score_s2_student_language_pilot` directly.
- Separates three orthogonal evaluation axes required before H-1:
  (A) `mathematical_correctness` — exact oracle answer match + verified engine certificate + 0 served negatives.
  (B) `semantic_goal_correctness` — bounded pre-registered equivalence policy (`h1-section-determination-equivalence/1`)
      grounded in product contracts: `construct_plane_section(section_id=S)` alongside `area/radius(section_id=S)` is
      semantically valid iff `problem_text` explicitly requests section determination (`xác định/tìm/dựng/vẽ thiết diện`)
      for that declared section `S`; never auto-accepts unasked goals or dropped goals.
  (C) `strict_contract_correctness` — valid `TypedFactNextPayloadV2` schema + exact `facts_signature`, exact `goals`,
      exact `operands`, and verbatim source quotes.
- Validates and seals an incoming 60-case H-1 corpus (format, 45+5+5+5 stratification, exact `radical.parse_exact`
  oracles, repo-wide contamination scan, `corpus_sha256`, `oracle_sha256`), or emits an honest `NOT_ESTABLISHED` /
  `NOT_MEASURED` integrity receipt when no independent corpus has been supplied yet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_paired_route_evaluation as P  # noqa: E402
import run_s2_student_language_pilot as R  # noqa: E402
from score_s2_student_language_pilot import _rate_or_unknown  # noqa: E402

SEMANTIC_EQUIVALENCE_POLICY = "h1-section-determination-equivalence/1"
INTEGRITY_SCHEMA = "h1-corpus-integrity/1"

#: Explicit Vietnamese imperative clauses requesting section determination/construction in the source text.
#: Matches e.g. "Xác định thiết diện...", "Tìm thiết diện...", "Dựng thiết diện...", "Vẽ thiết diện...".
#: Does NOT match "Tính diện tích thiết diện..." or "Biết thiết diện...".
_EXPLICIT_SECTION_DETERMINATION_RE = re.compile(
    r"(?<!không\s)(?<!chẳng\s)\b(?:xác\s+định|tìm|dựng|vẽ)\s+(?:hình\s+dạng\s+)?(?:của\s+)?thiết\s+diện\b",
    flags=re.IGNORECASE | re.UNICODE,
)


def _assert_offline() -> None:
    if os.environ.get("ALLOW_LIVE_AI", "0") not in ("0", "", "false", "False"):
        raise RuntimeError("score_independent_holdout_equivalence.py is strictly offline; run with ALLOW_LIVE_AI=0.")


def has_explicit_section_determination_request(problem_text: str) -> bool:
    """True iff `problem_text` explicitly asks to determine/find/construct/draw a plane section."""
    return bool(problem_text and _EXPLICIT_SECTION_DETERMINATION_RE.search(problem_text))


def _section_owner_map(payload: Any) -> dict[str, str]:
    """Map canonical projected section token (`section:<plane_name>`) -> canonical solid token (`solid:<notation>`)."""
    if not isinstance(payload, dict):
        return {}
    solids = {
        str(s.get("solid_id")): f"solid:{s.get('notation')}"
        for s in (payload.get("solids") or ())
        if isinstance(s, dict) and s.get("solid_id")
    }
    owners: dict[str, str] = {}
    for sec in payload.get("derived_sections") or ():
        if isinstance(sec, dict) and sec.get("plane_name") and sec.get("target_solid_id") in solids:
            owners[f"section:{sec.get('plane_name')}"] = solids[str(sec["target_solid_id"])]
    return owners


def _normalize_projected_goal(goal_json: str, section_owners: dict[str, str]) -> tuple[str, dict[str, Any]] | None:
    """Parse a projected goal entry `["sim"|"math", {...}]`, stripping redundant owning `target_solid_id` on
    `construct_plane_section` ONLY when it matches the declared `target_solid_id` of `target_section_id`."""
    try:
        kind_tag, spec = json.loads(goal_json)
    except (TypeError, ValueError):
        return None
    if not isinstance(kind_tag, str) or not isinstance(spec, dict):
        return None
    cleaned = dict(spec)
    if (
        kind_tag == "sim"
        and cleaned.get("kind") == "construct_plane_section"
        and "target_solid_id" in cleaned
        and section_owners.get(str(cleaned.get("target_section_id"))) == cleaned.get("target_solid_id")
    ):
        cleaned.pop("target_solid_id", None)
    return kind_tag, cleaned


def _measured_sections(goals: list[tuple[str, dict[str, Any]]]) -> set[str]:
    """Sections targeted by an explicit `area` or `radius` measurement math goal."""
    out: set[str] = set()
    for tag, spec in goals:
        if tag == "math" and spec.get("kind") == "measurement" and spec.get("goal_type") in ("area", "radius"):
            target = spec.get("target")
            if isinstance(target, dict) and isinstance(target.get("section_id"), str):
                out.add(target["section_id"])
    return out


def semantic_goals_equivalent(
    expected_goals: list[str] | None,
    observed_goals: list[str] | None,
    *,
    problem_text: str,
    raw_extraction: Any = None,
    gold_extraction: Any = None,
) -> bool | str:
    """Evaluate Semantic Goal Correctness under `h1-section-determination-equivalence/1`.

    - Returns `"UNKNOWN"` when `expected_goals` is `None` (e.g., `CLARIFY` cases where `unresolved` exits honestly).
    - Requires every expected goal to be preserved (zero dropped goals).
    - Allows an extra `["sim", {"kind": "construct_plane_section", "target_section_id": S}]` iff:
      1. `has_explicit_section_determination_request(problem_text)` is True, AND
      2. `S` is already targeted by an expected `area` or `radius` measurement goal in `expected_goals`.
    - Rejects any other extra simulation or math goal, and rejects `construct_plane_section` when `problem_text`
      asks only `"Tính diện tích thiết diện..."` without an explicit section-determination clause.
    """
    if expected_goals is None:
        return "UNKNOWN"
    owners = {**_section_owner_map(gold_extraction), **_section_owner_map(raw_extraction)}
    exp_parsed = [_normalize_projected_goal(g, owners) for g in expected_goals]
    obs_parsed = [_normalize_projected_goal(g, owners) for g in (observed_goals or [])]
    if any(x is None for x in exp_parsed) or any(x is None for x in obs_parsed):
        return False
    exp_set = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in exp_parsed if x is not None}
    obs_set = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in obs_parsed if x is not None}
    if len(exp_set) != len(exp_parsed) or len(obs_set) != len(obs_parsed):
        # Duplicate identical goals are invalid.
        if sorted(expected_goals) != sorted(observed_goals or []):
            return False
    missing = exp_set - obs_set
    if missing:
        return False
    extra = obs_set - exp_set
    if not extra:
        return True
    if not has_explicit_section_determination_request(problem_text):
        return False
    allowed_sections = _measured_sections([x for x in exp_parsed if x is not None])
    for item_json in extra:
        tag, spec = json.loads(item_json)
        if tag != "sim" or spec != {"kind": "construct_plane_section", "target_section_id": spec.get("target_section_id")}:
            return False
        if spec.get("target_section_id") not in allowed_sections:
            return False
    return True


def _payload_schema_valid(raw_extraction: Any) -> bool:
    if not isinstance(raw_extraction, dict):
        return False
    from app.simulation.geometry_functions.typed_fact_next import (
        TypedFactNextValidationError,
        parse_typed_fact_next_v2,
    )

    try:
        parse_typed_fact_next_v2(raw_extraction)
        return True
    except TypedFactNextValidationError:
        return False


def score_three_tier_rows(rows: list[dict[str, Any]], *, gold_by_id: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Score runner JSONL rows across Tier A (Mathematical), Tier B (Semantic Goal), and Tier C (Strict Contract)
    without mutating any input row or benchmark gold annotation."""
    _assert_offline()
    if not rows:
        unk = {"numerator": "UNKNOWN", "denominator": 0, "rate": "NOT_MEASURED"}
        return {
            "schema": "h1-three-tier-score/1",
            "policy": SEMANTIC_EQUIVALENCE_POLICY,
            "measurement_status": "NOT_MEASURED",
            "total_rows": 0,
            "tiers": {
                "mathematical_served_correct": unk,
                "mathematical_wrong_served": unk,
                "semantic_goal_completeness": unk,
                "semantic_served_correct": unk,
                "semantic_wrong_served": unk,
                "strict_goal_completeness": unk,
                "strict_contract_accuracy": unk,
                "strict_served_correct": unk,
                "strict_wrong_served": unk,
            },
            "strict_vs_semantic_divergences": [],
            "per_case": [],
        }

    math_sc_num = serve_expected_den = 0
    math_ws_num = evaluable_den = 0
    sem_goal_num = strict_goal_num = goal_den = 0
    sem_sc_num = strict_sc_num = 0
    sem_ws_num = strict_ws_num = 0
    strict_contract_num = contract_den = 0
    divergences: list[str] = []
    per_case: list[dict[str, Any]] = []

    for r in rows:
        cid = r.get("case_id", "UNKNOWN_ID")
        expected = r.get("expected") or {}
        observed = r.get("observed") or {}
        raw = r.get("raw_extraction")
        gold_case = (gold_by_id or {}).get(cid) or {}
        gold_ext = gold_case.get("gold_extraction")
        problem_text = (
            gold_case.get("problem_text")
            or (raw.get("problem_text") if isinstance(raw, dict) else None)
            or ""
        )

        if r.get("technical_failure") or observed.get("status") in (None, "UNKNOWN", "NOT_RECOVERABLE"):
            per_case.append({"case_id": cid, "measurement": "NOT_RECOVERABLE"})
            continue

        evaluable_den += 1
        exp_outcome = expected.get("outcome")
        obs_status = observed.get("status")
        if exp_outcome == "SERVED":
            serve_expected_den += 1

        # Tier A: Mathematical correctness (oracle + verified certificate + no served negative)
        answers_ok = (
            obs_status == "SERVED"
            and exp_outcome == "SERVED"
            and observed.get("answers") == expected.get("expected_answers")
            and bool(observed.get("certificate_verified", False))
        )
        math_wrong_served = obs_status == "SERVED" and not answers_ok
        if answers_ok:
            math_sc_num += 1
        if math_wrong_served:
            math_ws_num += 1

        # Goal & contract checks (evaluated where `expected_goals` exists)
        exp_goals = expected.get("expected_goals")
        obs_goals = observed.get("extracted_goals") or []
        if exp_goals is not None:
            goal_den += 1
            strict_goal_ok: bool | str = sorted(obs_goals) == sorted(exp_goals)
            sem_goal_ok = semantic_goals_equivalent(
                exp_goals,
                obs_goals,
                problem_text=problem_text,
                raw_extraction=raw,
                gold_extraction=gold_ext,
            )
            if strict_goal_ok is True:
                strict_goal_num += 1
            if sem_goal_ok is True:
                sem_goal_num += 1
        else:
            strict_goal_ok = "UNKNOWN"
            sem_goal_ok = "UNKNOWN"

        operands_ok = (
            bool(observed.get("quotes_verbatim_in_raw", False))
            and observed.get("operands") == expected.get("expected_operands")
            if "expected_operands" in expected
            else "UNKNOWN"
        )
        facts_ok = (
            observed.get("facts_signature") == expected.get("expected_facts_signature")
            if "expected_facts_signature" in expected
            else "UNKNOWN"
        )
        schema_ok = True if r.get("failure_stage") == "domain_gate" else _payload_schema_valid(raw)

        if "expected_facts_signature" in expected:
            contract_den += 1
            strict_contract_ok: bool | str = bool(
                schema_ok and facts_ok is True and strict_goal_ok is True and operands_ok is True
            )
            if strict_contract_ok:
                strict_contract_num += 1
        else:
            strict_contract_ok = "UNKNOWN"

        # Tier B & Tier C end-to-end served correctness / wrong-served
        sem_wrong_served = obs_status == "SERVED" and (
            not answers_ok or sem_goal_ok is False or operands_ok is False
        )
        strict_wrong_served = obs_status == "SERVED" and (
            not answers_ok or strict_goal_ok is False or operands_ok is False
        )
        sem_served_correct = obs_status == "SERVED" and not sem_wrong_served
        strict_served_correct = obs_status == "SERVED" and not strict_wrong_served

        if sem_served_correct:
            sem_sc_num += 1
        if strict_served_correct:
            strict_sc_num += 1
        if sem_wrong_served:
            sem_ws_num += 1
        if strict_wrong_served:
            strict_ws_num += 1
        if sem_goal_ok != strict_goal_ok:
            divergences.append(cid)

        per_case.append({
            "case_id": cid,
            "expected_outcome": exp_outcome,
            "observed_status": obs_status,
            "mathematical_served_correct": answers_ok if exp_outcome == "SERVED" else None,
            "mathematical_wrong_served": math_wrong_served,
            "semantic_goal_correct": sem_goal_ok,
            "semantic_served_correct": sem_served_correct if exp_outcome == "SERVED" else None,
            "semantic_wrong_served": sem_wrong_served,
            "strict_goal_correct": strict_goal_ok,
            "strict_contract_correct": strict_contract_ok,
            "strict_served_correct": strict_served_correct if exp_outcome == "SERVED" else None,
            "strict_wrong_served": strict_wrong_served,
        })

    return {
        "schema": "h1-three-tier-score/1",
        "policy": SEMANTIC_EQUIVALENCE_POLICY,
        "measurement_status": "SCORED_OFFLINE",
        "total_rows": len(rows),
        "evaluable_rows": evaluable_den,
        "serve_expected_rows": serve_expected_den,
        "tiers": {
            "mathematical_served_correct": _rate_or_unknown(math_sc_num, serve_expected_den),
            "mathematical_wrong_served": _rate_or_unknown(math_ws_num, evaluable_den),
            "semantic_goal_completeness": _rate_or_unknown(sem_goal_num, goal_den),
            "semantic_served_correct": _rate_or_unknown(sem_sc_num, serve_expected_den),
            "semantic_wrong_served": _rate_or_unknown(sem_ws_num, evaluable_den),
            "strict_goal_completeness": _rate_or_unknown(strict_goal_num, goal_den),
            "strict_contract_accuracy": _rate_or_unknown(strict_contract_num, contract_den),
            "strict_served_correct": _rate_or_unknown(strict_sc_num, serve_expected_den),
            "strict_wrong_served": _rate_or_unknown(strict_ws_num, evaluable_den),
        },
        "strict_vs_semantic_divergences": divergences,
        "per_case": per_case,
    }


def compute_oracle_sha256(cases: list[dict[str, Any]]) -> str:
    """Canonical SHA-256 over case expectations and exact parsed mathematical oracles / refusal classes."""
    canonical = []
    for c in sorted(cases, key=lambda item: str(item.get("id", ""))):
        expect = c.get("expect") or (c.get("expected") or {}).get("outcome")
        raw_oracle = c.get("oracle") if "oracle" in c else (c.get("expected") or {}).get("oracle")
        parsed_oracle = (
            {k: sorted(str(P.parse_oracle(v)) for v in vs) for k, vs in sorted(raw_oracle.items())}
            if isinstance(raw_oracle, dict)
            else None
        )
        canonical.append({
            "id": c.get("id"),
            "expect": expect,
            "oracle": parsed_oracle,
            "refusal_class": c.get("refusal_class"),
        })
    blob = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _candidate_summary(repo_root: Path) -> dict[str, Any]:
    cand_path = repo_root / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
    cand = json.loads(cand_path.read_text(encoding="utf-8"))
    from app.ai.adapter4_route import ADAPTER_V4_VERSION
    from app.ai.pipeline import route_policy_snapshot
    from app.main import hybrid_route_mode
    from app.simulation.geometry_functions.engine import ENGINE_VERSION
    from app.simulation.geometry_functions.planner import PLANNER_VERSION
    from app.simulation.geometry_functions.registry import REGISTRY_VERSION
    from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION

    return {
        "candidate_manifest_path": "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json",
        "candidate_manifest_sha256": R.sha256_file(cand_path),
        "frozen_candidate_commit": "180db769",
        "product_commit_sha": cand["product_commit_sha"],
        "measured_system_tree_hash": cand["measured_system"]["tree_hash"],
        "measured_system_file_count": cand["measured_system"]["so_file"],
        "registry_version": REGISTRY_VERSION,
        "planner_version": PLANNER_VERSION,
        "engine_version": ENGINE_VERSION,
        "typed_fact_next_version": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        "adapter_version": ADAPTER_V4_VERSION,
        "default_mode": route_policy_snapshot({}).geometry_compiler_mode,
        "hybrid_route_mode_default": hybrid_route_mode(),
        "cache_version": cand["cache_version"],
    }


def build_h1_corpus_integrity_receipt(
    corpus_path: Path | None = None,
    *,
    repo_root: Path = REPO,
) -> dict[str, Any]:
    """Validate and seal a paired 60-case H-1 corpus if present, or emit an honest pre-corpus receipt."""
    _assert_offline()
    ident = R.runtime_identity()
    ident["equivalence_scorer_sha256"] = R.sha256_file(Path(__file__))
    cand = _candidate_summary(repo_root)
    if cand["measured_system_tree_hash"] != ident["measured_system"]:
        raise P.LiveRefused("measured_system tree_hash drifted from frozen EVALUATION_CANDIDATE.json")

    head_sha = subprocess.run(
        ["git", "rev-parse", "--short=8", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()

    sealing_steps = {
        "1_format_validated": False,
        "2_duplication_and_contamination_checked": False,
        "3_count_and_stratification_45_5_5_5_verified": False,
        "4_independent_oracle_parsed_exact": False,
        "5_corpus_and_oracle_sha256_recorded": False,
        "6_evaluation_manifest_sealed": False,
        "7_candidate_scorer_model_budget_acceptance_preregistered": True,
        "8_owner_live_budget_approved": False,
    }

    if corpus_path is None or not corpus_path.is_file():
        return {
            "schema": INTEGRITY_SCHEMA,
            "status": "AWAITING_INDEPENDENT_CORPUS",
            "h1_authoring_independence": "NOT_ESTABLISHED",
            "h1_measurement": "NOT_MEASURED",
            "live_provider_calls": 0,
            "git_head_at_generation": head_sha,
            "corpus_present": False,
            "corpus_path": str(corpus_path.relative_to(repo_root).as_posix()) if corpus_path and corpus_path.is_relative_to(repo_root) else None,
            "corpus_sha256": None,
            "oracle_sha256": None,
            "author": None,
            "composition_required": {
                "total": 60,
                "SERVE": 45,
                "OUT_OF_DOMAIN": 5,
                "CONTRADICTORY_DATA": 5,
                "MISSING_DATA": 5,
            },
            "composition_observed": "NOT_MEASURED",
            "contamination_scan": "NOT_RUN_NO_CORPUS",
            "semantic_equivalence_policy": SEMANTIC_EQUIVALENCE_POLICY,
            "candidate_identity": cand,
            "runtime_identity": ident,
            "sealing_checklist": sealing_steps,
            "blocking_conditions": [
                "INDEPENDENT_AUTHOR_NOT_ASSIGNED_OR_CORPUS_NOT_DELIVERED",
                "PAIRED_LIVE_CAMPAIGN_BUDGET_NOT_APPROVED_BY_OWNER",
            ],
        }

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    P.validate_corpus(corpus)
    cases = corpus["cases"]
    serve_n = sum(c["expect"] == "SERVE" for c in cases)
    ref_counts = {k: sum(c.get("refusal_class") == k for c in cases) for k in P.REFUSAL_CLASSES}
    exact_comp = (
        len(cases) == 60
        and serve_n == 45
        and ref_counts == {"OUT_OF_DOMAIN": 5, "CONTRADICTORY_DATA": 5, "MISSING_DATA": 5}
    )
    if not exact_comp:
        raise P.LiveRefused(
            f"H-1 paired corpus must have exact 45 SERVE + 5/5/5 REFUSE composition; got SERVE={serve_n}, {ref_counts}"
        )

    hits = P.contamination_scan(corpus, repo_root, exclude=corpus_path)
    exact_hits = {cid: v["exact"] for cid, v in hits.items() if v.get("exact")}
    near_hits = {cid: v["near"] for cid, v in hits.items() if v.get("near")}
    if exact_hits:
        raise P.LiveRefused(f"H-1 corpus contains exact overlap with repository files: {exact_hits}")

    author = str(corpus.get("author") or "").strip()
    indep = (
        "ESTABLISHED"
        if author
        and author != "TO_BE_NAMED_BY_OWNER"
        and corpus.get("authoring_independence") == "ESTABLISHED"
        else "NOT_ESTABLISHED"
    )
    c_sha = P.sha256_file(corpus_path)
    o_sha = compute_oracle_sha256(cases)
    worst_req_usd = P.worst_case_request_usd(
        corpus,
        {
            "input_usd_per_million": 0.30,
            "output_usd_per_million": 2.50,
            "llm_only_output_reservation_tokens": P.MODEL_OUTPUT_LIMIT,
        },
    )

    sealing_steps.update({
        "1_format_validated": True,
        "2_duplication_and_contamination_checked": True,
        "3_count_and_stratification_45_5_5_5_verified": True,
        "4_independent_oracle_parsed_exact": True,
        "5_corpus_and_oracle_sha256_recorded": True,
        "6_evaluation_manifest_sealed": indep == "ESTABLISHED" and not near_hits,
    })

    return {
        "schema": INTEGRITY_SCHEMA,
        "status": "CORPUS_SEALED_AWAITING_BUDGET" if (indep == "ESTABLISHED" and not near_hits) else "CORPUS_NEEDS_REVIEW",
        "h1_authoring_independence": indep,
        "h1_measurement": "NOT_MEASURED",
        "live_provider_calls": 0,
        "git_head_at_generation": head_sha,
        "corpus_present": True,
        "corpus_path": str(corpus_path.relative_to(repo_root).as_posix()) if corpus_path.is_relative_to(repo_root) else corpus_path.name,
        "corpus_sha256": c_sha,
        "oracle_sha256": o_sha,
        "author": author or None,
        "composition_required": {
            "total": 60,
            "SERVE": 45,
            "OUT_OF_DOMAIN": 5,
            "CONTRADICTORY_DATA": 5,
            "MISSING_DATA": 5,
        },
        "composition_observed": {"total": len(cases), "SERVE": serve_n, **ref_counts},
        "contamination_scan": {"exact_overlap_cases": exact_hits, "near_overlap_cases": near_hits},
        "worst_case_request_usd_at_paid_flash_rates": round(worst_req_usd, 6),
        "semantic_equivalence_policy": SEMANTIC_EQUIVALENCE_POLICY,
        "candidate_identity": cand,
        "runtime_identity": ident,
        "sealing_checklist": sealing_steps,
        "blocking_conditions": (
            (["AUTHORING_INDEPENDENCE_NOT_ESTABLISHED"] if indep != "ESTABLISHED" else [])
            + (["NEAR_OVERLAP_REQUIRES_MANUAL_REVIEW"] if near_hits else [])
            + ["PAIRED_LIVE_CAMPAIGN_BUDGET_NOT_APPROVED_BY_OWNER"]
        ),
    }


def _load_jsonl_rows(paths: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("type") == "row":
                out.append(obj)
    return out


def main(argv: list[str] | None = None) -> int:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_seal = sub.add_parser("integrity", help="Verify/seal H-1 corpus or write pre-corpus integrity JSON")
    p_seal.add_argument("--corpus", type=Path, default=None)
    p_seal.add_argument("--out", type=Path, default=None)

    p_score = sub.add_parser("score-rows", help="Score study JSONL rows across Mathematical, Semantic, and Strict tiers")
    p_score.add_argument("jsonl", type=Path, nargs="+")
    p_score.add_argument("--out", type=Path, default=None)

    args = ap.parse_args(argv)
    if args.cmd == "integrity":
        res = build_h1_corpus_integrity_receipt(args.corpus)
    else:
        res = score_three_tier_rows(_load_jsonl_rows(args.jsonl))
    rendered = json.dumps(res, ensure_ascii=False, indent=2) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
