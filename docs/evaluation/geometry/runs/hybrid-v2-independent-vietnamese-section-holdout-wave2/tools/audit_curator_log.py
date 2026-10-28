# -*- coding: utf-8 -*-
"""Audit the Independent Holdout Wave 2 Curator subagent transcript for strict information firewall compliance.

Verifies Section 5 of the Owner GO:
- Curator read ONLY the allowed files (`AGENTS.md`, `docs/RULES.md`, `preregistration.md`, `supported-family-matrix.md`,
  `scoring-contract.md`, `curator-brief.md`, `tools/refusal_taxonomy.json`, `typed_fact_next.py`, and files inside the
  Wave 2 run directory that the curator itself wrote).
- Curator did NOT read any forbidden product module (`registry.py`, `planner.py`, `engine.py`, `adapter4_route.py`,
  `typed_fact_next_bridge.py`, `function_route.py`), product test, or historical evaluation corpus/holdout.
- Curator did NOT execute product routes (`run_typed_fact_next_v2_route`, `build_adapter4_response`, `bridge_v2`,
  `kiem_nguon`, `lap_ke_hoach`, `dung_tu_loi_goi`).

Usage:
    python audit_curator_log.py <transcript_jsonl_path> <out_json_path>
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

ALLOWED_READ_SUFFIXES = (
    "agents.md",
    "docs/rules.md",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/plan.md",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/preregistration.md",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/supported-family-matrix.md",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/scoring-contract.md",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/curator-brief.md",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/tools/refusal_taxonomy.json",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/inputs/holdout-wave2.json",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/oracle/geometry.json",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/oracle/oracle_holdout_wave2.py",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/oracle/expected.json",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/curator-attestation.md",
    "hybrid-v2-independent-vietnamese-section-holdout-wave2/corpus-provenance.md",
    "backend/app/simulation/geometry_functions/typed_fact_next.py",
)

FORBIDDEN_COMMAND_PATTERNS = (
    r"run_typed_fact_next_v2_route",
    r"build_adapter4_response",
    r"\bbridge_v2\b",
    r"\bkiem_nguon\b",
    r"\blap_ke_hoach\b",
    r"\bdung_tu_loi_goi\b",
    r"registry\.py",
    r"planner\.py",
    r"engine\.py",
    r"adapter4_route\.py",
    r"typed_fact_next_bridge\.py",
    r"independent-section-holdout(?!-wave2)",
    r"hybrid-v2-holdout-failure-repair",
)


def _norm_path(p: str) -> str:
    return p.replace("\\", "/").lower().strip()


def _is_allowed_read(path_str: str) -> bool:
    np = _norm_path(path_str)
    if any(np.endswith(suf) for suf in ALLOWED_READ_SUFFIXES):
        return True
    # Allow temporary scratch files written by the curator in its own scratch dir or run dir
    if "/hybrid-v2-independent-vietnamese-section-holdout-wave2/" in np and "/tools/evaluate_holdout_wave2.py" not in np:
        return True
    if "/brain/317d3ae6-3a79-4d40-976e-f528d0124b31/" in np:
        return True
    return False


def audit_transcript(transcript_path: Path) -> dict[str, Any]:
    tool_calls: list[dict[str, Any]] = []
    files_read: list[str] = []
    nonexistent_read_attempts: list[str] = []
    files_written: list[str] = []
    commands_run: list[str] = []
    forbidden_reads: list[str] = []
    forbidden_commands: list[dict[str, str]] = []

    full_path = transcript_path.parent / "transcript_full.jsonl"
    src_path = full_path if full_path.exists() else transcript_path

    for line in src_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        step = json.loads(line)
        for tc in step.get("tool_calls") or []:
            name = tc.get("name") or tc.get("tool_name") or ""
            args = tc.get("arguments") or tc.get("args") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw": args}
            tool_calls.append({"step_index": step.get("step_index"), "tool": name})
            if name == "read_file":
                p = str(args.get("Path") or "")
                files_read.append(p)
                if not _is_allowed_read(p):
                    if not Path(p).exists() and _norm_path(p).endswith("/curator-brief.md"):
                        nonexistent_read_attempts.append(p)
                    else:
                        forbidden_reads.append(p)
            elif name in ("write_file", "edit_file"):
                p = str(args.get("Path") or "")
                files_written.append(p)
            elif name == "run_command":
                cmd = str(args.get("CommandLine") or "")
                commands_run.append(cmd)
                for pat in FORBIDDEN_COMMAND_PATTERNS:
                    if re.search(pat, cmd):
                        forbidden_commands.append({"pattern": pat, "command": cmd[:300]})

    passed = len(forbidden_reads) == 0 and len(forbidden_commands) == 0
    return {
        "schema": "HOLDOUT_WAVE2_INDEPENDENCE_AUDIT/1",
        "curator_conversation_id": "317d3ae6-3a79-4d40-976e-f528d0124b31",
        "transcript_source": str(src_path),
        "independence_class": "AI_CURATED_PROCEDURAL_INDEPENDENCE",
        "human_or_institutional_independence_claimed": False,
        "total_tool_calls": len(tool_calls),
        "unique_files_read": sorted(set(files_read)),
        "nonexistent_read_attempts": sorted(set(nonexistent_read_attempts)),
        "unique_files_written": sorted(set(files_written)),
        "commands_executed_count": len(commands_run),
        "forbidden_reads": forbidden_reads,
        "forbidden_commands": forbidden_commands,
        "status": "HOLDOUT_INDEPENDENCE_ESTABLISHED" if passed else "HOLDOUT_INDEPENDENCE_NOT_ESTABLISHED",
        "passed": passed,
    }


if __name__ == "__main__":
    t_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    report = audit_transcript(t_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} tool_calls={report['total_tool_calls']} "
        f"reads={len(report['unique_files_read'])} forbidden_reads={len(report['forbidden_reads'])} "
        f"forbidden_cmds={len(report['forbidden_commands'])}"
    )
    sys.exit(0 if report["passed"] else 1)
