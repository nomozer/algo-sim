"""Actual route + Adapter4 regressions with preregistered mathematical outcomes."""
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import pytest

RUN = Path(__file__).resolve().parents[3]/"docs/evaluation/geometry/runs/hybrid-v2-wave2-source-gate-language-generalization"
spec = importlib.util.spec_from_file_location("source_language_evaluation",RUN/"tools/evaluate_development.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
CASES = json.loads((RUN/"inputs/development.json").read_text(encoding="utf-8"))["cases"]
SUPPLEMENTAL = json.loads((RUN/"inputs/supplemental.json").read_text(encoding="utf-8"))["cases"]
ADJUDICATION = json.loads((RUN/"results/development-adjudication.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case",CASES,ids=[c["id"] for c in CASES])
def test_source_language_product_outcome(case):
    if case["id"] in ADJUDICATION:
        # Preserve the locked false-negative label; independently reviewed math governs this execution assertion.
        correction = ADJUDICATION[case["id"]]
        assert case["expected_status"] == correction["raw_expected_status"]
        case = dict(deepcopy(case),expected_status=correction["adjudicated_expected_status"],
                    oracle=correction["expected_oracle"])
    row = evaluation.evaluate_case(case)
    assert row["matches_expected"], (row["outcome"],row.get("code"),row.get("reason"),row.get("oracle_mismatches"))


@pytest.mark.parametrize("case",SUPPLEMENTAL,ids=[c["id"] for c in SUPPLEMENTAL])
def test_source_language_supplemental_controls(case):
    row = evaluation.evaluate_case(case)
    assert row["matches_expected"], (row["outcome"],row.get("code"),row.get("reason"),row.get("oracle_mismatches"))


@pytest.mark.parametrize("segment,ratio,expected", [
    (["S","A"],"2/7",True), (["A","S"],"5/7",True),
    (["A","S"],"2/7",False), (["S","A"],"5/7",False), (["S","B"],"2/7",False)])
def test_inverted_ratio_binds_endpoint_direction_and_value(segment,ratio,expected):
    from types import SimpleNamespace
    from app.simulation.geometry_functions import registry as R
    call=SimpleNamespace(args=SimpleNamespace(point="M",segment=segment,ratio=ratio))
    assert R._ty_so_tron_cau(call,"Trên cạnh SA lấy điểm M sao cho SM = 2/7 SA.") is expected


@pytest.mark.parametrize("text",[
    "Trên cạnh SA lấy điểm M sao cho SM = 2/7 SA, SB = SC.",
    "Trên cạnh SB lấy điểm M sao cho SM = 2/7 SA.",
    "Trên cạnh SA lấy điểm N sao cho SM = 2/7 SA.",
    "Trên cạnh SA lấy điểm M sao cho SM = 1/0 SA.",
    "Trên cạnh SA lấy điểm M sao cho SM = 2/7 SX.",
    "Trên cạnh SA lấy điểm M sao cho SM = 2/7 SA'.",
])
def test_ratio_premise_reader_rejects_mutated_operands_and_unread_tails(text):
    from types import SimpleNamespace
    from app.simulation.geometry_functions import registry as R
    call=SimpleNamespace(args=SimpleNamespace(point="M",segment=["S","A"],ratio="2/7"))
    assert not R._ty_so_tron_cau(call,text)
