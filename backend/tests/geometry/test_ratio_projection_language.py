"""F2 source relations, exact independent geometry, and mandatory semantic mutations."""
import importlib.util
import json
from pathlib import Path

import pytest

RUN = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding'
spec = importlib.util.spec_from_file_location('ratio_projection_evaluation', RUN / 'tools/evaluate_development.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
CASES = json.loads((RUN / 'inputs/development.json').read_text(encoding='utf-8'))['cases']
ORACLE = json.loads((RUN / 'inputs/oracle.json').read_text(encoding='utf-8'))['cases']


@pytest.mark.parametrize('case', CASES, ids=[c['id'] for c in CASES])
def test_ratio_projection_language(case):
    row = evaluation.evaluate_case(case, ORACLE.get(case['id']))
    assert row['matches_expected'], (row['outcome'], row['code'], row.get('source_relation_provenance'), row.get('oracle_mismatches'))
    assert row['outcome'] != 'WRONG_SERVED'
    if case['expected_disposition'] == 'REFUSE':
        assert not row['served'] and row['code'] in case['expected_codes']


def test_all_owner_tamper_classes_are_distinct_mutations_of_positive_witnesses():
    by_id = {case['id']:case for case in CASES}
    negatives = [case for case in CASES if case['slice'] == 'mandatory_negative_tamper']
    assert {case['negative_class'] for case in negatives} == {str(i) for i in range(1,25)}
    for case in negatives:
        original = by_id['DEV-RATIO-03' if int(case['negative_class']) <= 13 else 'DEV-PROJECTION-10']
        assert case['payload'] != original['payload'], case['id']
        assert original['expected_disposition'] == 'SERVE'
