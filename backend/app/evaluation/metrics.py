"""Quantitative Metrics Engine for Generative Simulation Certification.

Tính toán 9 nhóm chỉ số đo lường độc lập theo đúng định nghĩa phương pháp luận.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class MetricReport:
    total_tasks: int
    supported_tasks: int
    unsupported_tasks: int
    released_tasks: int
    correct_verdicts: int
    false_releases: int
    oracle_matches: int
    geom_matches: int
    first_pass_successes: int
    attempt0_failures: int
    repaired_by_cegis: int
    total_llm_calls: int
    total_prompt_tokens: int
    total_comp_tokens: int

    # 9 Measurement Families
    r_verdict: float
    r_release: float
    r_false_release: float
    r_oracle: float
    r_geom: float
    r_first: float
    r_cegis: float | None  # None = N/A when attempt0_failures == 0
    avg_llm_calls: float
    avg_prompt_tokens: float
    avg_comp_tokens: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": {
                "total_tasks": self.total_tasks,
                "supported_tasks": self.supported_tasks,
                "unsupported_tasks": self.unsupported_tasks,
                "released_tasks": self.released_tasks,
                "correct_verdicts": self.correct_verdicts,
                "false_releases": self.false_releases,
                "oracle_matches": self.oracle_matches,
                "geom_matches": self.geom_matches,
                "first_pass_successes": self.first_pass_successes,
                "attempt0_failures": self.attempt0_failures,
                "repaired_by_cegis": self.repaired_by_cegis,
                "total_llm_calls": self.total_llm_calls,
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_comp_tokens": self.total_comp_tokens,
            },
            "metrics": {
                "r_verdict_pct": round(self.r_verdict * 100, 2),
                "r_release_pct": round(self.r_release * 100, 2),
                "r_false_release_pct": round(self.r_false_release * 100, 2),
                "r_oracle_pct": round(self.r_oracle * 100, 2),
                "r_geom_pct": round(self.r_geom * 100, 2),
                "r_first_pct": round(self.r_first * 100, 2),
                "r_cegis_pct": round(self.r_cegis * 100, 2) if self.r_cegis is not None else "N/A",
                "avg_llm_calls_per_task": round(self.avg_llm_calls, 2),
                "avg_prompt_tokens_per_task": round(self.avg_prompt_tokens, 1),
                "avg_comp_tokens_per_task": round(self.avg_comp_tokens, 1),
            },
        }


def compute_metrics(
    eval_results: list[dict[str, Any]],
) -> MetricReport:
    """Tính toán 9 nhóm chỉ số từ danh sách kết quả thực nghiệm của từng task.
    
    Mỗi phần tử trong eval_results cần có cấu trúc:
    {
        "task_id": str,
        "is_supported_expected": bool,
        "actual_status": "ok" | "unsupported",
        "oracle_matched": bool | None,
        "geom_valid": bool | None,
        "first_pass_ok": bool,
        "repaired_by_cegis": bool,
        "llm_calls": int,
        "tokens_prompt": int,
        "tokens_comp": int,
    }
    """
    total = len(eval_results)
    if total == 0:
        return MetricReport(
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, 0.0, 0.0, 0.0,
        )

    supported_tasks = sum(1 for r in eval_results if r.get("is_supported_expected", True))
    unsupported_tasks = total - supported_tasks
    
    released_tasks = sum(1 for r in eval_results if r.get("actual_status") == "ok")
    
    # 1. Correct verdicts:
    # Supported -> ok, Unsupported -> unsupported
    correct_verdicts = sum(
        1 for r in eval_results
        if (r.get("is_supported_expected", True) and r.get("actual_status") == "ok")
        or (not r.get("is_supported_expected", True) and r.get("actual_status") == "unsupported")
    )
    
    # 2. False releases: released but failed oracle OR failed geom
    false_releases = sum(
        1 for r in eval_results
        if r.get("actual_status") == "ok"
        and (r.get("oracle_matched") is False or r.get("geom_valid") is False)
    )
    
    # 3. Oracle matches & Geom matches (out of released)
    oracle_matches = sum(1 for r in eval_results if r.get("actual_status") == "ok" and r.get("oracle_matched") is True)
    geom_matches = sum(1 for r in eval_results if r.get("actual_status") == "ok" and r.get("geom_valid") is True)
    
    # 4. First pass & CEGIS dynamics
    first_pass_ok = sum(1 for r in eval_results if r.get("is_supported_expected", True) and r.get("first_pass_ok", False))
    # attempt0_failures: các task thực sự sinh candidate 0 bị fail và phải kích hoạt CEGIS sửa
    attempt0_failures = sum(
        1 for r in eval_results 
        if r.get("is_supported_expected", True) and (r.get("cegis_triggered", False) or r.get("repaired_by_cegis", False))
    )
    repaired_by_cegis = sum(1 for r in eval_results if r.get("is_supported_expected", True) and r.get("repaired_by_cegis", False))
    
    # 5. Calls and Tokens
    total_calls = sum(r.get("llm_calls", 1) for r in eval_results)
    total_prompt_tok = sum(r.get("tokens_prompt", 0) for r in eval_results)
    total_comp_tok = sum(r.get("tokens_comp", 0) for r in eval_results)

    # Ratios
    r_verdict = correct_verdicts / total if total > 0 else 0.0
    r_release = released_tasks / supported_tasks if supported_tasks > 0 else 0.0
    r_false_release = false_releases / total if total > 0 else 0.0
    r_oracle = oracle_matches / released_tasks if released_tasks > 0 else 1.0
    r_geom = geom_matches / released_tasks if released_tasks > 0 else 1.0
    r_first = first_pass_ok / supported_tasks if supported_tasks > 0 else 0.0
    
    # CEGIS: if attempt0_failures == 0 -> None (N/A)
    r_cegis = (repaired_by_cegis / attempt0_failures) if attempt0_failures > 0 else None
    
    avg_llm_calls = total_calls / total if total > 0 else 0.0
    avg_prompt_tokens = total_prompt_tok / total if total > 0 else 0.0
    avg_comp_tokens = total_comp_tok / total if total > 0 else 0.0

    return MetricReport(
        total_tasks=total,
        supported_tasks=supported_tasks,
        unsupported_tasks=unsupported_tasks,
        released_tasks=released_tasks,
        correct_verdicts=correct_verdicts,
        false_releases=false_releases,
        oracle_matches=oracle_matches,
        geom_matches=geom_matches,
        first_pass_successes=first_pass_ok,
        attempt0_failures=attempt0_failures,
        repaired_by_cegis=repaired_by_cegis,
        total_llm_calls=total_calls,
        total_prompt_tokens=total_prompt_tok,
        total_comp_tokens=total_comp_tok,
        r_verdict=r_verdict,
        r_release=r_release,
        r_false_release=r_false_release,
        r_oracle=r_oracle,
        r_geom=r_geom,
        r_first=r_first,
        r_cegis=r_cegis,
        avg_llm_calls=avg_llm_calls,
        avg_prompt_tokens=avg_prompt_tokens,
        avg_comp_tokens=avg_comp_tokens,
    )
