"""Fault injection for test_hybrid_preview_contract.py: MUTATION=<name> patches app.ai.hybrid_preview at session start."""
import os


def pytest_sessionstart(session):
    from app.ai import hybrid_preview as HP
    m = os.environ.get('MUTATION')
    orig_classify, orig_refusal = HP.classify_refusal, HP._refusal
    if m == 'no_minus_fold':
        HP._GACH_TRU = frozenset()
    elif m == 'integrity_as_capability':
        HP._NHOM = tuple((n, 'capability_gap' if n == 'INTEGRITY' else c, codes, msg) for n, c, codes, msg in HP._NHOM)
    elif m == 'drop_adapter_origin':
        HP._refusal = lambda code, policy, planner=None, *, adapter=False: orig_refusal(code, policy, planner)
    elif m == 'ignore_negated_observation':
        HP.classify_refusal = lambda code, planner=None, *, adapter=False: orig_classify(code, None, adapter=adapter)
    elif m == 'all_capability_gap':   # the original defect
        HP._NHOM = tuple((n, 'capability_gap', codes, msg) for n, c, codes, msg in HP._NHOM)
    elif m == 'drop_new_code':
        HP._NHOM = tuple((n, c, codes - {'LINE_CONTAINED_IN_PLANE'}, msg) for n, c, codes, msg in HP._NHOM)
    elif m:
        raise SystemExit('unknown mutation ' + m)
