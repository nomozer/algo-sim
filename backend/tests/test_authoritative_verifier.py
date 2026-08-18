"""Test Suite kiểm định toàn bộ 12 Certification Cases (0 Token LLM).

Bao gồm:
1. 6 Certified Cases (Đối chiếu Ground Truth với Independent Result Oracle)
2. 4 Faults Cases (Bắt chính xác Counterexample & Runtime Invariant Violations)
3. 2 Refusals Cases (Kiểm tra năng lực từ chối trung thực)
"""

import json
from pathlib import Path
import pytest

from app.simulation.dsl.validator import validate_generic_config
from app.simulation.dsl.executor import execute_simulation
import tests.oracles as oracles

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(category: str, filename: str) -> dict:
    path = FIXTURES_DIR / category / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 1. Certified Positive Cases (with Result Oracle Verification) ───────────

@pytest.mark.parametrize(
    "fixture_file",
    [
        "c01_temperature_scan.json",
        "c02_bracket_stack.json",
        "c03_order_count_range.json",
        "c04_athlete_sorting.json",
        "c05_last_occurrence.json",
        "c06_table_filter.json",
    ],
)
def test_certified_goldens_pass_all_gates_and_match_oracle(fixture_file: str):
    data = load_fixture("certified", fixture_file)
    spec = data["spec"]
    
    # Gate 1 & 2: Schema & Type validation
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi Validate Gate 1/2 tại {fixture_file}: {err}"
    assert validated is not None

    # Gate 5 Oracle Ground Truth Computation
    oracle_cfg = data["expected_oracle"]
    oracle_func = getattr(oracles, oracle_cfg["oracle_func"])
    oracle_result = oracle_func(*oracle_cfg["inputs"])
    
    # Gate 3, 4, 5, 6: Authoritative AST & Invariant Execution + Oracle Check
    report = execute_simulation(validated, oracle_result=oracle_result)
    assert report.ok is True, f"Lỗi Execution/Invariant/Oracle tại {fixture_file}: {report.error} (Code: {report.error_code})"
    assert len(report.snapshots) > 0


# ── 2. Engineered Fault Cases (Counterexample Verification) ─────────────────

def test_f01_pointer_oob_detected():
    data = load_fixture("faults", "f01_pointer_oob.json")
    spec = data["spec"]
    validated, _ = validate_generic_config(spec)
    assert validated is not None
    
    report = execute_simulation(validated)
    assert report.ok is False
    assert report.counterexample is not None
    assert report.counterexample.violation_code == "INDEX_OUT_OF_BOUNDS"
    assert report.counterexample.step_index == 2
    assert "vượt quá độ dài" in report.counterexample.message


def test_f02_stack_underflow_detected():
    data = load_fixture("faults", "f02_stack_underflow.json")
    spec = data["spec"]
    validated, _ = validate_generic_config(spec)
    assert validated is not None
    
    report = execute_simulation(validated)
    assert report.ok is False
    assert report.counterexample is not None
    assert report.counterexample.violation_code == "STACK_UNDERFLOW"
    assert report.counterexample.step_index == 1
    assert "ngăn xếp rỗng" in report.counterexample.message


def test_f03_dangling_binding_detected():
    data = load_fixture("faults", "f03_dangling_binding.json")
    spec = data["spec"]
    # Validator checks target validity and rejects dangling target
    validated, err = validate_generic_config(spec)
    assert validated is None
    assert "không tồn tại" in err


def test_f04_type_incoherent_detected():
    data = load_fixture("faults", "f04_type_incoherent.json")
    spec = data["spec"]
    validated, err = validate_generic_config(spec)
    assert validated is None, "Validator phải từ chối rule boolean ghi vào bar_chart target"
    assert "không nhận được vai trò" in err or "Rule" in err


# ── 3. Refusals & Sufficiency Verification ─────────────────────────────────

def test_r01_insufficient_input_refusal():
    from app.simulation.catalog import CATALOG
    from app.simulation.sufficiency_gate import check_input_sufficiency
    
    # Mock analysis of pre-order tree without tree structure
    analysis = {
        "objects": ["cây nhị phân"],
        "data": [],
        "relations": [],
        "processes": ["duyệt tiền thứ tự"],
        "constraints": [],
        "goal": "duyệt cây",
        "input_description": "Không có cây",
        "output_description": "Thứ tự duyệt",
        "domain_scope": "computer_science",
        "simulatability": "algorithmic",
        "result_ownership": "algorithmic",
        "prescribed_procedure": "preorder_traversal",
    }
    verdict = check_input_sufficiency(analysis, "tree.traversal")
    assert verdict is not None, "Cổng đủ dữ kiện phải bắt được lỗi thiếu cây"
    assert "cây" in verdict[1].lower() or "dữ kiện" in verdict[1].lower()


def test_r02_continuous_physics_refusal():
    from app.simulation.scope_gate import check_scope_and_simulatability
    
    # Analysis of physics differential equation
    analysis = {
        "objects": ["con lắc đơn"],
        "data": [],
        "relations": [],
        "processes": ["dao động"],
        "constraints": ["phương trình vi phân"],
        "goal": "giải dao động",
        "input_description": "phương trình vi phân",
        "output_description": "quỹ đạo",
        "domain_scope": "physics",
        "simulatability": "continuous_physical_system",
        "result_ownership": "rule_derivable",
    }
    verdict = check_scope_and_simulatability(analysis)
    assert verdict is not None, "Cổng phạm vi phải từ chối bài toán vật lý liên tục ngoài Tin học"
