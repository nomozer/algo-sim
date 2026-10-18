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
        HP._refusal = lambda code, policy, planner=None, *, adapter=False, **kw: orig_refusal(code, policy, planner, **kw)
    elif m == 'ignore_negated_observation':
        HP.classify_refusal = lambda code, planner=None, **kw: orig_classify(code, None, **kw)
    elif m == 'npl_always_source':   # the review's finding 2: SOURCE without the server reading the text
        HP._de_ghi_do_dai_khong_duong = lambda text: True
    elif m == 'escape_as_out_of_scope':   # the review's finding 1
        HP._NHOM = tuple((n, c, codes - {'OUT_OF_SCOPE'}, msg) for n, c, codes, msg in HP._NHOM) + (
            ('OUT_OF_SCOPE', 'out_of_scope', frozenset({'OUT_OF_SCOPE'}), 'Bài này thuộc môn học khác.'),)
    elif m == 'all_capability_gap':   # the original defect
        HP._NHOM = tuple((n, 'capability_gap', codes, msg) for n, c, codes, msg in HP._NHOM)
    elif m == 'drop_new_code':
        HP._NHOM = tuple((n, c, codes - {'LINE_CONTAINED_IN_PLANE'}, msg) for n, c, codes, msg in HP._NHOM)
    elif m:
        raise SystemExit('unknown mutation ' + m)
