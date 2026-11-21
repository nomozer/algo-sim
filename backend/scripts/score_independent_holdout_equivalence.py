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
REGISTERED_FAMILIES = ("pyramid", "prism", "cuboid", "cube", "sphere", "cylinder", "cone")
REGISTERED_QUESTIONS = ("section_measure", "distance", "angle", "volume", "area")
MIN_CASES_PER_STRATUM = 3
ALLOWED_EXPLICIT_GOALS = frozenset(P.KINDS.values()) | {"angle", "construct_plane_section"}

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
    """Evaluate Semantic Goal Correctness under finalized P1 (`h1-section-determination-equivalence/1`):

    - Returns `"UNKNOWN"` when `expected_goals` is `None` (e.g., `CLARIFY` cases where `unresolved` exits honestly).
    - Case A: `problem_text` explicitly requests section determination (`xác định/tìm/dựng/vẽ thiết diện`) for a
      declared section `S` measured by `area` or `radius` -> canonical P1 goal set REQUIRES BOTH
      `construct_plane_section(target_section_id=S)` AND the explicit measurement goal(s). Omitting either fails.
    - Case B: `problem_text` asks only `"Tính diện tích thiết diện..."` without an explicit section-determination
      clause -> canonical P1 goal set contains ONLY the measurement goal (`construct_plane_section` is rejected).
    - Case C: Any unasked simulation or math goal (e.g., adding `volume` or `distance` when only `area` was asked)
      or any dropped expected goal fails (`False`).
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
    allowed_sections = _measured_sections([x for x in exp_parsed if x is not None])
    if has_explicit_section_determination_request(problem_text) and allowed_sections:
        p1_expected_set = exp_set | {
            json.dumps(("sim", {"kind": "construct_plane_section", "target_section_id": sec_id}),
                       ensure_ascii=False, sort_keys=True)
            for sec_id in allowed_sections
        }
    else:
        p1_expected_set = exp_set
    return obs_set == p1_expected_set


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
    return P.compute_oracle_sha256(cases)


_PROBLEM_TEXT_JSON_RE = re.compile(r'"(?:problem_text|text)"\s*:\s*"((?:\\.|[^"\\])*)"')
_SOLID_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9']*\.[A-Z][A-Z0-9']*$")
_POLY_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9']+$")
_PT_TOKEN_RE = re.compile(r"^[A-Z]'?$")
_NUM_TOKEN_RE = re.compile(r"^(?:\d+(?:/\d+)?|[0-9/\u221a\u03c0\u00b0^+-]*\d[0-9/\u221a\u03c0\u00b0^+-]*|\u221a\d+|\u03c0)$")
_VERTEX_ATOM_RE = re.compile(r"[A-Z][0-9']*|\.")
_CLAUSE_HEADER_RE = re.compile(
    r"^(cho\s+(?:h\u00ecnh|kh\u1ed1i)\s+(?:ch\u00f3p(?:\s+c\u1ee5t)?|l\u0103ng\s+tr\u1ee5|h\u1ed9p|l\u1eadp\s+ph\u01b0\u01a1ng|t\u1ee9\s+di\u1ec7n|\u0111a\s+di\u1ec7n)(?:\s+\u0111\u1ec1u|\s+\u0111\u1ee9ng|\s+vu\u00f4ng)?\s+(?:<SOLID>|<PT>\s+<POLY>|<POLY>\s+<POLY>|<POLY>))\s+c\u00f3\s+",
    flags=re.IGNORECASE,
)


def _layer1_exact_verbatim(text: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFC", text).strip()


def _layer2_normalized_text(text: str) -> str:
    import unicodedata
    cleaned = unicodedata.normalize("NFC", text).lower()
    cleaned = re.sub(r"[.,;:!?()\[\]\"\u201c\u201d]", " ", cleaned)
    return " ".join(cleaned.split())


def _layer3_number_stripped_template(text: str) -> str:
    import unicodedata
    cleaned = unicodedata.normalize("NFC", text)
    cleaned = re.sub(r"[.,;:!?()\[\]\"\u201c\u201d]", " ", cleaned)
    tokens: list[str] = []
    for tok in cleaned.split():
        if _NUM_TOKEN_RE.fullmatch(tok):
            tokens.append("<NUM>")
        elif _SOLID_TOKEN_RE.fullmatch(tok) or _POLY_TOKEN_RE.fullmatch(tok) or _PT_TOKEN_RE.fullmatch(tok):
            tokens.append(tok)
        else:
            tokens.append(tok.lower())
    return " ".join(tokens)


def _canonicalize_vertices_tokens(text: str, *, scale_numbers: bool = False) -> list[str]:
    from fractions import Fraction
    import unicodedata
    from app.simulation.geometry.radical import display, divided_by_rational, parse_exact, sign

    cleaned = unicodedata.normalize("NFC", text)
    cleaned = re.sub(r"[.,;:!?()\[\]\"\u201c\u201d]", " ", cleaned)
    raw_tokens = cleaned.split()
    vmap: dict[str, str] = {}
    base_he: Fraction | None = None
    if scale_numbers:
        for tok in raw_tokens:
            if _NUM_TOKEN_RE.fullmatch(tok) and not tok.endswith("\u00b0"):
                val = parse_exact(tok)
                if val is not None and sign(val) > 0:
                    base_he = val if isinstance(val, Fraction) else val.he
                    break

    out: list[str] = []
    for tok in raw_tokens:
        if _SOLID_TOKEN_RE.fullmatch(tok) or _POLY_TOKEN_RE.fullmatch(tok) or _PT_TOKEN_RE.fullmatch(tok):
            atoms = _VERTEX_ATOM_RE.findall(tok)
            mapped = []
            for a in atoms:
                if a == ".":
                    mapped.append(".")
                else:
                    if a not in vmap:
                        vmap[a] = f"V{len(vmap)}"
                    mapped.append(vmap[a])
            out.append("".join(mapped))
        elif _NUM_TOKEN_RE.fullmatch(tok):
            if scale_numbers and not tok.endswith("\u00b0") and base_he is not None:
                val = parse_exact(tok)
                if val is not None and sign(val) > 0:
                    ratio = divided_by_rational(val, base_he)
                    out.append(f"<SCALE:{display(ratio)}>")
                    continue
            out.append(tok)
        else:
            out.append(tok.lower())
    return out


def _layer4_isomorphic_vertex_renaming(text: str) -> str:
    return " ".join(_canonicalize_vertices_tokens(text, scale_numbers=False))


def _layer5_scale_factor_transform(text: str) -> str:
    return " ".join(_canonicalize_vertices_tokens(text, scale_numbers=True))


def _layer6_construction_relation_graph(text: str) -> str:
    import unicodedata
    cleaned = unicodedata.normalize("NFC", text)
    raw_clauses = re.split(
        r"\.(?![A-Z0-9'])|[,;:]|\b(?:v\u00e0|bi\u1ebft|trong \u0111\u00f3)\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    norm_clauses: list[str] = []
    for cl in raw_clauses:
        skel = _structural_skeleton(cl)
        if not skel:
            continue
        m = _CLAUSE_HEADER_RE.match(skel)
        if m:
            norm_clauses.append(m.group(1))
            rest = skel[m.end():].strip()
            if rest:
                norm_clauses.append(rest)
        else:
            norm_clauses.append(skel)
    return " || ".join(sorted(norm_clauses))


def scan_six_layer_contamination(
    cases: list[dict[str, Any]],
    repo_root: Path,
    *,
    exclude: Path | None = None,
) -> dict[str, dict[str, list[str]]]:
    """Run 6-layer anti-contamination checking against all problem texts in the repository
    (including the 72 Dev Matrix cases, 46 Held-Out cases, K-1/S-2/R-1, and historical runs)."""
    layer_fns = {
        "exact_verbatim": _layer1_exact_verbatim,
        "normalized_text": _layer2_normalized_text,
        "number_stripped_template": _layer3_number_stripped_template,
        "isomorphic_vertex_renaming": _layer4_isomorphic_vertex_renaming,
        "scale_factor_transform": _layer5_scale_factor_transform,
        "construction_relation_graph": _layer6_construction_relation_graph,
    }
    case_sigs = {
        layer: {c["id"]: fn(c["problem_text"]) for c in cases}
        for layer, fn in layer_fns.items()
    }
    results: dict[str, dict[str, list[str]]] = {layer: {} for layer in layer_fns}
    for path in repo_root.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in P._TEXT_SUFFIXES
            or P._SKIP_DIRS & set(path.relative_to(repo_root).parts)
            or (exclude is not None and path.resolve() == exclude.resolve())
        ):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(repo_root).as_posix()
        for m in _PROBLEM_TEXT_JSON_RE.finditer(raw):
            try:
                ref_text = json.loads(f'"{m.group(1)}"')
            except ValueError:
                continue
            if not isinstance(ref_text, str) or len(ref_text.strip()) < 25:
                continue
            for layer, fn in layer_fns.items():
                ref_sig = fn(ref_text)
                for cid, c_sig in case_sigs[layer].items():
                    if c_sig == ref_sig and rel not in results[layer].get(cid, ()):
                        results[layer].setdefault(cid, []).append(rel)
    return results


def _layer7_intermediate_construction_sequence(text: str) -> str:
    """Layer 7: Canonical intermediate construction sequence (`solids -> premises -> described_points -> derived_sections -> goals`
    with vertex-canonicalized kind sequence), detecting problems that share an identical intermediate construction chain
    even when surface wording and clause order are rewritten."""
    try:
        from app.ai.local_geometry_parser import parse_geometry_problem_locally

        res = parse_geometry_problem_locally(text)
        if res.payload is not None:
            p = res.payload
            steps: list[str] = []
            for s in p.get("solids") or ():
                steps.append(f"solid:{s.get('solid_type')}")
            for pr in p.get("premises") or ():
                steps.append(f"prem:{pr.get('kind')}")
            for dp in p.get("described_points") or ():
                steps.append(f"desc:{dp.get('kind')}")
            for ds in p.get("derived_sections") or ():
                steps.append(f"sec:{len(ds.get('plane_points') or ())}")
            for mg in p.get("math_goals") or ():
                steps.append(f"goal:{mg.get('goal_type')}")
            if steps:
                return " -> ".join(steps)
    except Exception:
        pass
    return f"SKEL_SEQ:{_layer6_construction_relation_graph(text)}"


_SOLUTION_LEAK_RE = re.compile(
    r"(?:\bđáp\s+số\b|\blời\s+giải\b|\bta\s+có\s+V\s*=|\bsuy\s+ra\s+V\s*=|\bkết\s+quả\s+là\b)",
    flags=re.IGNORECASE | re.UNICODE,
)


def _layer8_solution_or_expected_answer_leakage(text: str, oracle: Any = None) -> str:
    """Layer 8: Detect leaked solution steps or expected answers embedded inside `problem_text` or matching a known
    `(structural_skeleton, oracle)` pair."""
    has_leak = bool(_SOLUTION_LEAK_RE.search(text or ""))
    oracle_str = json.dumps(oracle, sort_keys=True, ensure_ascii=False) if oracle else ""
    return f"LEAK={has_leak}|SKEL={_structural_skeleton(text)}|ORACLE={oracle_str}"


H1_REQUIRED_13_FIELDS = (
    "case_id",
    "problem_text",
    "source_type",
    "author_or_source",
    "author_date",
    "solid_family",
    "question_types",
    "auxiliary_chain_depth",
    "expected_behavior",
    "independent_oracle",
    "independent_derivation",
    "contamination_check",
    "freeze_sha256",
)


def validate_h1_case_13_fields(case: dict[str, Any]) -> dict[str, Any]:
    """Validate that an H-1 case record satisfies all 13 mandatory provenance & oracle fields (Section IV.1.2)."""
    missing = [f for f in H1_REQUIRED_13_FIELDS if f not in case or case.get(f) in (None, "", [], {})]
    source_type = str(case.get("source_type") or "")
    author = str(case.get("author_or_source") or "")
    ai_authored = bool(
        re.search(r"\b(?:agent|antigravity|claude|gemini|gpt|copilot|llm|synthetic)\b", author, re.IGNORECASE)
        or source_type not in ("HUMAN_AUTHORED", "CURATED_EXAM")
    )
    has_inline_leak = bool(_SOLUTION_LEAK_RE.search(str(case.get("problem_text") or "")))
    valid = (not missing) and (not ai_authored) and (not has_inline_leak)
    return {
        "case_id": case.get("case_id") or case.get("id"),
        "valid_h1_case": valid,
        "missing_fields": missing,
        "ai_or_synthetic_rejected": ai_authored,
        "inline_solution_leak_detected": has_inline_leak,
    }


def scan_eight_layer_contamination(
    cases: list[dict[str, Any]],
    repo_root: Path,
    *,
    exclude: Path | None = None,
) -> dict[str, dict[str, list[str]]]:
    """Run 8-layer anti-contamination checking (Section IV.1.3) against all problem texts in the repository."""
    six = scan_six_layer_contamination(
        [{"id": c.get("case_id") or c["id"], "problem_text": c["problem_text"]} for c in cases],
        repo_root,
        exclude=exclude,
    )
    results: dict[str, dict[str, list[str]]] = {
        **six,
        "intermediate_construction_sequence": {},
        "solution_or_expected_answer_leakage": {},
    }
    l7_sigs = {(c.get("case_id") or c["id"]): _layer7_intermediate_construction_sequence(c["problem_text"]) for c in cases}
    l8_sigs = {(c.get("case_id") or c["id"]): _layer8_solution_or_expected_answer_leakage(c["problem_text"]) for c in cases}
    for c in cases:
        cid = c.get("case_id") or c["id"]
        if _SOLUTION_LEAK_RE.search(c.get("problem_text") or ""):
            results["solution_or_expected_answer_leakage"].setdefault(cid, []).append("SELF_INLINE_SOLUTION_LEAK")

    for path in repo_root.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in P._TEXT_SUFFIXES
            or P._SKIP_DIRS & set(path.relative_to(repo_root).parts)
            or (exclude is not None and path.resolve() == exclude.resolve())
        ):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(repo_root).as_posix()
        for m in _PROBLEM_TEXT_JSON_RE.finditer(raw):
            try:
                ref_text = json.loads(f'"{m.group(1)}"')
            except ValueError:
                continue
            if not isinstance(ref_text, str) or len(ref_text.strip()) < 25:
                continue
            ref_l7 = _layer7_intermediate_construction_sequence(ref_text)
            ref_l8 = _layer8_solution_or_expected_answer_leakage(ref_text)
            for cid, sig7 in l7_sigs.items():
                if sig7 == ref_l7 and rel not in results["intermediate_construction_sequence"].get(cid, ()):
                    results["intermediate_construction_sequence"].setdefault(cid, []).append(rel)
            for cid, sig8 in l8_sigs.items():
                if sig8 == ref_l8 and rel not in results["solution_or_expected_answer_leakage"].get(cid, ()):
                    results["solution_or_expected_answer_leakage"].setdefault(cid, []).append(rel)
    return results


def _structural_skeleton(text: str) -> str:
    """Mask vertex/solid/plane ASCII labels and numeric/radical literals so renaming `S.ABCD -> P.MNPQ` and `4 -> 6`
    produces the exact same structural template skeleton."""
    import unicodedata

    cleaned = unicodedata.normalize("NFC", text)
    cleaned = re.sub(r"[.,;:!?()\[\]\"“”]", " ", cleaned)
    tokens: list[str] = []
    for tok in cleaned.split():
        if _SOLID_TOKEN_RE.fullmatch(tok):
            tokens.append("<SOLID>")
        elif _POLY_TOKEN_RE.fullmatch(tok):
            tokens.append("<POLY>")
        elif _PT_TOKEN_RE.fullmatch(tok):
            tokens.append("<PT>")
        elif _NUM_TOKEN_RE.fullmatch(tok):
            tokens.append("<NUM>")
        else:
            tokens.append(tok.lower())
    return " ".join(tokens)


def _scan_structural_template_clones(
    cases: list[dict[str, Any]],
    repo_root: Path,
    *,
    exclude: Path | None = None,
) -> dict[str, list[str]]:
    """Detect H-1 cases whose structural skeleton matches an existing problem text in repository docs/tests/corpora
    (including `H1_AUTHORING_HANDOFF.md`'s illustrative examples) even after vertex renaming and number scaling."""
    case_skeletons = {c["id"]: _structural_skeleton(c["problem_text"]) for c in cases}
    clones: dict[str, list[str]] = {}
    for path in repo_root.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in P._TEXT_SUFFIXES
            or P._SKIP_DIRS & set(path.relative_to(repo_root).parts)
            or (exclude is not None and path.resolve() == exclude.resolve())
        ):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(repo_root).as_posix()
        for m in _PROBLEM_TEXT_JSON_RE.finditer(raw):
            try:
                ref_text = json.loads(f'"{m.group(1)}"')
            except ValueError:
                continue
            if not isinstance(ref_text, str) or len(ref_text.strip()) < 25:
                continue
            ref_skel = _structural_skeleton(ref_text)
            for cid, c_skel in case_skeletons.items():
                if c_skel == ref_skel and rel not in clones.get(cid, ()):
                    clones.setdefault(cid, []).append(rel)
    return clones


def _is_non_placeholder_text(val: Any, *, min_len: int = 3) -> bool:
    if not isinstance(val, str):
        return False
    s = val.strip()
    if len(s) < min_len or ("<" in s and ">" in s):
        return False
    upper = s.upper()
    if upper in ("TO_BE_NAMED_BY_OWNER", "TBD", "TODO", "UNKNOWN", "PENDING"):
        return False
    return True


def _verify_authoring_independence(corpus: dict[str, Any]) -> tuple[str, list[str]]:
    """Refuse to rubber-stamp `authoring_independence = ESTABLISHED` unless author identity, affiliation, pre-run
    attestation, independence evidence, per-case provenance, and independent oracle derivations are all present."""
    missing: list[str] = []
    if corpus.get("authoring_independence") != "ESTABLISHED":
        missing.append("authoring_independence!=ESTABLISHED")
    author = corpus.get("author")
    if not _is_non_placeholder_text(author, min_len=3):
        missing.append("author")
    elif re.search(r"\b(?:agent|antigravity|claude|gemini|gpt|copilot|llm)\b", str(author), flags=re.IGNORECASE):
        missing.append("author_cannot_be_ai_agent")
    if not _is_non_placeholder_text(corpus.get("author_affiliation"), min_len=2):
        missing.append("author_affiliation")
    if corpus.get("written_before_any_system_run") is not True:
        missing.append("written_before_any_system_run")
    if not _is_non_placeholder_text(corpus.get("independence_evidence"), min_len=20):
        missing.append("independence_evidence")
    for c in corpus.get("cases") or ():
        cid = c.get("id", "?")
        if not _is_non_placeholder_text(c.get("provenance"), min_len=8):
            missing.append(f"{cid}.provenance")
        if c.get("expect") == "SERVE":
            if not _is_non_placeholder_text(c.get("oracle_derivation"), min_len=10):
                missing.append(f"{cid}.oracle_derivation")
            sem = c.get("semantic_annotations")
            goals = sem.get("explicit_goals") if isinstance(sem, dict) else None
            if not isinstance(goals, list) or not goals or not all(isinstance(g, str) and g for g in goals):
                missing.append(f"{cid}.semantic_annotations.explicit_goals")
    return ("ESTABLISHED" if not missing else "NOT_ESTABLISHED"), missing


def _verify_stratum_coverage(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify C28 §IV.4: every registered solid family (7) and question type (5) has >= 3 SERVE cases."""
    fam_counts = {f: 0 for f in REGISTERED_FAMILIES}
    q_counts = {q: 0 for q in REGISTERED_QUESTIONS}
    deficits: list[str] = []
    for c in cases:
        if c.get("expect") != "SERVE":
            continue
        st = c.get("stratum")
        fam = st.get("family") if isinstance(st, dict) else None
        q = st.get("question") if isinstance(st, dict) else None
        if fam in fam_counts:
            fam_counts[fam] += 1
        else:
            deficits.append(f"{c.get('id')}:unknown_or_missing_family:{fam!r}")
        if q in q_counts:
            q_counts[q] += 1
        else:
            deficits.append(f"{c.get('id')}:unknown_or_missing_question:{q!r}")
    for fam, n in fam_counts.items():
        if n < MIN_CASES_PER_STRATUM:
            deficits.append(f"family:{fam}:{n}<{MIN_CASES_PER_STRATUM}")
    for q, n in q_counts.items():
        if n < MIN_CASES_PER_STRATUM:
            deficits.append(f"question:{q}:{n}<{MIN_CASES_PER_STRATUM}")
    return {"valid": not deficits, "families": fam_counts, "questions": q_counts, "deficits": deficits}


def _verify_semantic_annotations(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify C28 §IV.7 & §V (P1): `semantic_annotations.explicit_goals` uses closed goal kinds, covers every oracle key,
    and includes `construct_plane_section` iff `problem_text` contains an explicit section-determination clause."""
    issues: list[str] = []
    for c in cases:
        if c.get("expect") != "SERVE":
            continue
        cid = c.get("id", "?")
        sem = c.get("semantic_annotations")
        goals = sem.get("explicit_goals") if isinstance(sem, dict) else None
        if not isinstance(goals, list) or not goals or not all(isinstance(g, str) and g in ALLOWED_EXPLICIT_GOALS for g in goals):
            issues.append(f"{cid}:invalid_or_unknown_explicit_goals")
            continue
        goal_set = set(goals)
        for ok_key in (c.get("oracle") or {}):
            accepted = {ok_key, "angle"} if ok_key in ("angle_cos_sq", "angle_cos") else {ok_key}
            if not (goal_set & accepted):
                issues.append(f"{cid}:oracle_kind_missing_from_explicit_goals:{ok_key}")
        wants_sec = has_explicit_section_determination_request(c.get("problem_text", ""))
        has_sec = "construct_plane_section" in goal_set
        if wants_sec != has_sec:
            issues.append(f"{cid}:p1_section_goal_mismatch(text_explicit={wants_sec},annotated={has_sec})")
    return {"valid": not issues, "issues": issues}


def _assess_oracle_verification(corpus: dict[str, Any]) -> dict[str, Any]:
    """Verify C28 §IV.5–6: exact syntax is machine-verified; independent mathematical truth requires explicit human/expert
    review status rather than assuming prose derivations are error-free."""
    weak_derivations: list[str] = []
    for c in corpus.get("cases") or ():
        if c.get("expect") != "SERVE":
            continue
        deriv = str(c.get("oracle_derivation") or "")
        if not re.search(r"[0-9=+\-*/√π^]", deriv):
            weak_derivations.append(str(c.get("id", "?")))
    expert_verified = (
        corpus.get("expert_oracle_review") == "VERIFIED_BY_HUMAN_EXPERT"
        and _is_non_placeholder_text(corpus.get("expert_reviewer"), min_len=3)
    )
    return {
        "exact_syntax_verified": True,
        "derivations_have_symbolic_steps": not weak_derivations,
        "weak_derivation_cases": weak_derivations,
        "expert_mathematical_review_status": (
            "VERIFIED_BY_HUMAN_EXPERT" if expert_verified else "PENDING_HUMAN_EXPERT_VERIFICATION"
        ),
    }


def render_paired_comparison_table(corpus: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    """Render the C28 §VIII per-case paired comparison table (`| Case | H-1 Oracle | LLM_ONLY | HYBRID | Comparison |`)."""
    by = {(r["case_id"], r["arm"]): r for r in rows if r.get("type") == "row"}
    lines = [
        "| Case | H-1 Oracle | LLM_ONLY | HYBRID | Comparison |",
        "|---|---|---|---|---|",
    ]
    for c in corpus.get("cases") or ():
        cid = c["id"]
        oracle_desc = (
            ", ".join(f"{k}={v}" for k, v in sorted((c.get("oracle") or {}).items()))
            if c.get("expect") == "SERVE"
            else f"REFUSE:{c.get('refusal_class')}"
        )
        l_row, h_row = by.get((cid, "LLM_ONLY")), by.get((cid, "HYBRID"))

        def _fmt(r: dict[str, Any] | None) -> str:
            if r is None:
                return "UNMEASURED"
            if r.get("technical_failure"):
                return "TECH_FAILURE"
            if r.get("served"):
                tag = "SERVED_OK" if r.get("served_correct") else "WRONG_SERVED"
                return f"{tag} ({r.get('served_quantities')})"
            return f"REFUSED:{r.get('refusal_class') or 'UNSPECIFIC'}"

        if l_row is None or h_row is None:
            comp = "INCOMPLETE_PAIR"
        elif c.get("expect") == "SERVE":
            lc, hc = bool(l_row.get("served_correct")), bool(h_row.get("served_correct"))
            comp = (
                "BOTH_CORRECT" if (lc and hc)
                else "HYBRID_ONLY_CORRECT" if hc
                else "LLM_ONLY_CORRECT" if lc
                else "BOTH_INCORRECT"
            )
        else:
            ls, hs = bool(l_row.get("served")), bool(h_row.get("served"))
            comp = (
                "BOTH_REFUSED" if (not ls and not hs)
                else "HYBRID_WRONG_SERVED_NEGATIVE" if (hs and not ls)
                else "LLM_ONLY_WRONG_SERVED_NEGATIVE" if (ls and not hs)
                else "BOTH_WRONG_SERVED_NEGATIVE"
            )
        lines.append(f"| `{cid}` | `{oracle_desc}` | {_fmt(l_row)} | {_fmt(h_row)} | `{comp}` |")
    return "\n".join(lines) + "\n"


def _candidate_summary(repo_root: Path) -> dict[str, Any]:
    cand_path = repo_root / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
    cand = json.loads(cand_path.read_text(encoding="utf-8"))
    from app.ai.adapter4_route import ADAPTER_V4_VERSION
    from app.ai.route_policy import route_policy_snapshot
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
        "default_mode": route_policy_snapshot({}).default_route_mode,
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

    template_clones = _scan_structural_template_clones(cases, repo_root, exclude=corpus_path)
    six_layer_hits = scan_six_layer_contamination(cases, repo_root, exclude=corpus_path)
    indep, missing_indep = _verify_authoring_independence(corpus)
    stratum_cov = _verify_stratum_coverage(cases)
    sem_check = _verify_semantic_annotations(cases)
    oracle_ver = _assess_oracle_verification(corpus)
    author = str(corpus.get("author") or "").strip()
    c_sha = P.sha256_file(corpus_path)
    o_sha = compute_oracle_sha256(cases)
    worst_req_usd = P.worst_case_request_usd(
        corpus,
        {
            "model": "gemini-2.5-flash",
            "input_usd_per_million": 0.30,
            "output_usd_per_million": 2.50,
            "llm_only_output_reservation_tokens": P.MODEL_OUTPUT_LIMIT,
        },
    )
    clean_seal = (
        indep == "ESTABLISHED"
        and stratum_cov["valid"]
        and sem_check["valid"]
        and oracle_ver["derivations_have_symbolic_steps"]
        and not near_hits
        and not template_clones
    )

    sealing_steps.update({
        "1_format_validated": True,
        "2_duplication_and_contamination_checked": True,
        "3_count_and_stratification_45_5_5_5_verified": exact_comp and stratum_cov["valid"],
        "4_independent_oracle_parsed_exact": oracle_ver["exact_syntax_verified"] and oracle_ver["derivations_have_symbolic_steps"],
        "5_corpus_and_oracle_sha256_recorded": True,
        "6_evaluation_manifest_sealed": clean_seal,
    })

    return {
        "schema": INTEGRITY_SCHEMA,
        "status": "CORPUS_SEALED_AWAITING_BUDGET" if clean_seal else "CORPUS_NEEDS_REVIEW",
        "h1_authoring_independence": indep,
        "missing_independence_fields": missing_indep,
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
        "stratum_coverage": stratum_cov,
        "semantic_annotations_validation": sem_check,
        "oracle_verification": oracle_ver,
        "contamination_scan": {
            "exact_overlap_cases": exact_hits,
            "near_overlap_cases": near_hits,
            "structural_template_clones": template_clones,
            "six_layer_contamination": six_layer_hits,
        },
        "worst_case_request_usd_at_paid_flash_rates": round(worst_req_usd, 6),
        "proposed_campaign_limits": {
            "campaign_max_requests": 300,
            "campaign_max_usd": 5.0,
            "model": "gemini-2.5-flash",
            "approval_status": "PENDING_OWNER_DECISION",
        },
        "semantic_equivalence_policy": SEMANTIC_EQUIVALENCE_POLICY,
        "candidate_identity": cand,
        "runtime_identity": ident,
        "sealing_checklist": sealing_steps,
        "blocking_conditions": (
            (["AUTHORING_INDEPENDENCE_NOT_ESTABLISHED"] if indep != "ESTABLISHED" else [])
            + (["INSUFFICIENT_STRATUM_COVERAGE"] if not stratum_cov["valid"] else [])
            + (["INVALID_SEMANTIC_ANNOTATIONS"] if not sem_check["valid"] else [])
            + (["WEAK_ORACLE_DERIVATION_REQUIRES_AUTHOR_REVISION"] if not oracle_ver["derivations_have_symbolic_steps"] else [])
            + (["NEAR_OVERLAP_REQUIRES_MANUAL_REVIEW"] if near_hits else [])
            + (["STRUCTURAL_TEMPLATE_CLONE_REQUIRES_REWRITE"] if template_clones else [])
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

    p_table = sub.add_parser("paired-table", help="Render C28 60-case paired comparison Markdown table")
    p_table.add_argument("--corpus", type=Path, required=True)
    p_table.add_argument("--rows", type=Path, required=True)
    p_table.add_argument("--out", type=Path, default=None)

    args = ap.parse_args(argv)
    if args.cmd == "paired-table":
        corpus_doc = json.loads(args.corpus.read_text(encoding="utf-8"))
        md = render_paired_comparison_table(corpus_doc, _load_jsonl_rows([args.rows]))
        if args.out is not None:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(md, encoding="utf-8", newline="\n")
        else:
            print(md, end="")
        return 0
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
