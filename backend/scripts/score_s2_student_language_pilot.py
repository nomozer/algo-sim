# -*- coding: utf-8 -*-
"""Continuation 11 (§5.2) — Offline S-2 Student Language Pilot Scorer & Harness.

STRICT OFFLINE & ISOLATION CONTRACT:
- Zero provider imports, zero live network calls (`ALLOW_LIVE_AI=0`).
- Strictly separate from the preregistered 60-problem live paired evaluation.
- Scores recorded/simulated pilot records on all 8 mandatory §5.2 metrics:
  1. `extraction_accuracy`
  2. `goal_completeness`
  3. `operand_preservation`
  4. `ambiguity_detection`
  5. `clarification_correctness`
  6. `false_clarification`
  7. `unsupported_classification`
  8. `wrong_served_end_to_end`
- Obeys `AGENTS.md` §4: missing or unmeasured fields are reported as `"UNKNOWN"` / `"NOT_RECOVERABLE"`,
  NEVER silently coerced to `0`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _rate_or_unknown(num: int, den: int) -> dict[str, Any]:
    if den == 0:
        return {"numerator": 0, "denominator": 0, "rate": "UNKNOWN"}
    return {"numerator": num, "denominator": den, "rate": round(num / den, 6)}


def score_s2_pilot_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministically score S-2 student-language pilot records across all 8 §5.2 metrics."""
    if os.environ.get("ALLOW_LIVE_AI", "0") not in ("0", "", "false", "False"):
        raise RuntimeError("score_s2_student_language_pilot.py is an offline scorer; run with ALLOW_LIVE_AI=0.")

    if not records:
        unknown = {"numerator": "UNKNOWN", "denominator": 0, "rate": "NOT_MEASURED"}
        return {
            "schema": "s2-student-language-pilot-score/1",
            "live_provider_calls": 0,
            "measurement_status": "NOT_MEASURED",
            "total_records": 0,
            "metrics": {
                "extraction_accuracy": unknown,
                "goal_completeness": unknown,
                "operand_preservation": unknown,
                "ambiguity_detection": unknown,
                "clarification_correctness": unknown,
                "false_clarification": unknown,
                "unsupported_classification": unknown,
                "wrong_served_end_to_end": unknown,
            },
            "per_case": [],
        }

    ext_num = ext_den = 0
    goal_num = goal_den = 0
    op_num = op_den = 0
    amb_num = amb_den = 0
    clar_num = clar_den = 0
    fclar_num = fclar_den = 0
    unsup_num = unsup_den = 0
    ws_num = ws_den = 0
    unrecoverable_count = 0

    per_case: list[dict[str, Any]] = []

    for rec in records:
        cid = rec.get("case_id", "UNKNOWN_ID")
        expected = rec.get("expected") or {}
        observed = rec.get("observed")

        if not isinstance(observed, dict) or observed.get("status") in (None, "UNKNOWN", "NOT_RECOVERABLE"):
            unrecoverable_count += 1
            per_case.append({
                "case_id": cid,
                "measurement": "NOT_RECOVERABLE",
                "wrong_served": "UNKNOWN",
            })
            continue

        ws_den += 1
        exp_outcome = expected.get("outcome")  # "SERVED" | "CLARIFY" | "REFUSED_UNSUPPORTED" | "REFUSED_INCONSISTENT"
        obs_outcome = observed.get("status")   # "SERVED" | "CLARIFY" | "REFUSED"

        # 1. Extraction accuracy (exact semantic fact-set / solid+premise match on evaluable cases)
        if "expected_facts_signature" in expected:
            ext_den += 1
            ext_ok = observed.get("facts_signature") == expected["expected_facts_signature"]
            if ext_ok:
                ext_num += 1
        else:
            ext_ok = "UNKNOWN"

        # 2. Goal completeness (all expected goals extracted & none dropped)
        if "expected_goals" in expected:
            goal_den += 1
            goal_ok = sorted(observed.get("extracted_goals") or []) == sorted(expected["expected_goals"])
            if goal_ok:
                goal_num += 1
        else:
            goal_ok = "UNKNOWN"

        # 3. Operand preservation (labels, numbers, and verbatim quotes preserved without mutation)
        if "expected_operands" in expected:
            op_den += 1
            quotes_verbatim = bool(observed.get("quotes_verbatim_in_raw", False))
            op_ok = quotes_verbatim and (observed.get("operands") == expected["expected_operands"])
            if op_ok:
                op_num += 1
        else:
            op_ok = "UNKNOWN"

        # 4. Ambiguity detection (among genuinely ambiguous inputs, did the pipeline detect ambiguity?)
        is_ambiguous = bool(expected.get("is_ambiguous", False))
        if is_ambiguous:
            amb_den += 1
            detected_amb = obs_outcome == "CLARIFY" or bool(observed.get("unresolved_flagged", False))
            if detected_amb:
                amb_num += 1
        else:
            detected_amb = None

        # 5. Clarification correctness (among emitted CLARIFY responses, is clarification justified + reason code valid?)
        if obs_outcome == "CLARIFY":
            clar_den += 1
            valid_reason = observed.get("clarification_code") in set(expected.get("allowed_clarification_codes") or [])
            clar_ok = exp_outcome == "CLARIFY" and valid_reason
            if clar_ok:
                clar_num += 1
        else:
            clar_ok = None

        # 6. False clarification (among unambiguous inputs, did the pipeline falsely emit CLARIFY?)
        if not is_ambiguous:
            fclar_den += 1
            false_clar = obs_outcome == "CLARIFY"
            if false_clar:
                fclar_num += 1
        else:
            false_clar = None

        # 7. Unsupported classification (among genuinely out-of-scope / unsupported inputs, refused with unsupported code)
        if exp_outcome == "REFUSED_UNSUPPORTED":
            unsup_den += 1
            unsup_ok = obs_outcome == "REFUSED" and bool(observed.get("is_unsupported_code", False))
            if unsup_ok:
                unsup_num += 1
        else:
            unsup_ok = None

        # 8. Wrong-served end-to-end (SERVED when expected non-SERVED, or SERVED with wrong answer / dropped goal / bad cert)
        wrong_served = False
        if obs_outcome == "SERVED":
            if exp_outcome != "SERVED":
                wrong_served = True
            elif observed.get("answers") != expected.get("expected_answers"):
                wrong_served = True
            elif not bool(observed.get("certificate_verified", False)):
                wrong_served = True
            elif goal_ok is False or op_ok is False:
                wrong_served = True
        if wrong_served:
            ws_num += 1

        per_case.append({
            "case_id": cid,
            "expected_outcome": exp_outcome,
            "observed_outcome": obs_outcome,
            "extraction_ok": ext_ok,
            "goal_complete": goal_ok,
            "operand_preserved": op_ok,
            "ambiguity_detected": detected_amb,
            "clarification_correct": clar_ok,
            "false_clarification": false_clar,
            "unsupported_classified": unsup_ok,
            "wrong_served": wrong_served,
        })

    return {
        "schema": "s2-student-language-pilot-score/1",
        "live_provider_calls": 0,
        "measurement_status": "SCORED_OFFLINE",
        "total_records": len(records),
        "evaluable_records": ws_den,
        "not_recoverable_records": unrecoverable_count,
        "metrics": {
            "extraction_accuracy": _rate_or_unknown(ext_num, ext_den),
            "goal_completeness": _rate_or_unknown(goal_num, goal_den),
            "operand_preservation": _rate_or_unknown(op_num, op_den),
            "ambiguity_detection": _rate_or_unknown(amb_num, amb_den),
            "clarification_correctness": _rate_or_unknown(clar_num, clar_den),
            "false_clarification": _rate_or_unknown(fclar_num, fclar_den),
            "unsupported_classification": _rate_or_unknown(unsup_num, unsup_den),
            "wrong_served_end_to_end": _rate_or_unknown(ws_num, ws_den),
        },
        "per_case": per_case,
    }


def main() -> None:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    records: list[dict[str, Any]] = []
    if len(sys.argv) > 1:
        inp = Path(sys.argv[1])
        data = json.loads(inp.read_text(encoding="utf-8"))
        records = data["records"] if isinstance(data, dict) and "records" in data else data
    out = score_s2_pilot_records(records)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
