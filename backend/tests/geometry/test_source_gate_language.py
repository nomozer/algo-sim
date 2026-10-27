"""Actual route + Adapter4 regressions with preregistered mathematical outcomes."""
import importlib.util
import json
from pathlib import Path
import pytest

RUN = Path(__file__).resolve().parents[3]/"docs/evaluation/geometry/runs/hybrid-v2-wave2-source-gate-language-generalization"
spec = importlib.util.spec_from_file_location("source_language_evaluation",RUN/"tools/evaluate_development.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
CASES = json.loads((RUN/"inputs/development.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case",CASES,ids=[c["id"] for c in CASES])
def test_source_language_product_outcome(case):
    row = evaluation.evaluate_case(case)
    assert row["matches_expected"], (row["outcome"],row.get("code"),row.get("reason"),row.get("oracle_mismatches"))
