"""Diagnostics, NOT acceptance: the four v1 fresh-source controls in PENDING_SOURCE_GRAMMAR_SUPPORT.

Not collected by default (name outside `test_*.py`); run by explicit path. Inputs and the expected SERVED/12 are the v1
ones, unchanged (closed-input-contract/source-grammar-adjudication/amendment-1.md). A failure here is the recorded
Source Gate grammar limitation, never a pass of the product.
"""
import json

import pytest

import test_scope_census_closure as F

PENDING = json.loads((F.RUN / 'closed-input-contract/source-grammar-adjudication/pending-source-grammar-controls.json')
                     .read_text(encoding='utf-8'))


@pytest.mark.parametrize('scope', list(PENDING['cases']))
def test_pending_source_grammar_control(scope):
    p = PENDING['cases'][scope]
    for name, route in F.ROUTES.items():
        r = route(p); assert r.status == 'SERVED', (name, r.code, r.reason)
        assert [x['coef'] for x in r.answer_exact.values()] == ['12']
