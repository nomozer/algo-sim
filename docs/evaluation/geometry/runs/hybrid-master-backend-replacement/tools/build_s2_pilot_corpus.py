"""Twelfth continuation: build the S-2 live student-language pilot corpus (protocol §3: 6 strata × 6 = 36 cases).

IMPLEMENTER-AUTHORED DEVELOPMENT TEXTS — never held-out, never the locked 60-case paired corpus. 21 cases reuse the
tenth-continuation probe (`student_language_probe.py`): its raw text, its `gold` extraction and its hand-written
expectation, unchanged. 15 cases are written here for the strata the probe lacks (out-of-scope school topics,
shorthand wording, elliptical goals, shape contradictions). Oracles are exact strings in the `radical.parse_exact`
grammar written by hand; for reused cases each is checked against the probe's own independent squared / cos² oracle.

Offline, 0 provider calls. Usage: build_s2_pilot_corpus.py <out.json>   (refuses to overwrite)
"""
import json, sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
_src = (HERE / 'student_language_probe.py').read_text(encoding='utf-8')
_MARK = '# ---- scoring'
assert _src.count(_MARK) == 1, 'probe layout changed: re-check what is reused'
NS = {'__file__': str(HERE / 'student_language_probe.py'), '__name__': 'student_language_probe_defs'}
exec(compile(_src[:_src.index(_MARK)], 'student_language_probe.py', 'exec'), NS)   # definitions only, no scoring run
PROBE = {c['id']: c for c in NS['CASES']}
X, P, M, U, c1, STD, C1 = (NS[k] for k in ('X', 'P', 'M', 'U', 'c1', 'STD', 'C1'))


def squared(s):
    """Square of a hand oracle string `p√r/q` (same reader as the probe's `squared`, which sits past the marker)."""
    m = __import__('re').fullmatch(r'(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?', s)
    assert m and (m['p'] or m['r']), s
    p, r, q = F(m['p'] or 1), F(m['r'] or 1), F(m['q'] or 1)
    return p * p * r / (q * q)


def reused(stratum, cid, outcome, oracle=None, codes=()):
    c = PROBE[cid]
    exp = c['expect']
    if outcome == 'SERVED':
        assert exp['action'] == 'SERVED', cid
        want = sorted(v for _, (k, v) in sorted(exp['oracle'].items()))
        got = sorted(F(s) if k == 'angle_cos_sq' else squared(s) for k, vs in (oracle or {}).items() for s in vs)
        assert got == want, f'{cid}: hand oracle {oracle} disagrees with the probe oracle {exp["oracle"]}'
    return {'id': f'{stratum}-{cid}', 'stratum': stratum, 'source': f'student_language_probe.py::{cid}',
            'problem_text': c['text'], 'gold_extraction': c['extractions'].get('gold'),
            'expected': expected(outcome, oracle, codes)}


def new(stratum, cid, text, gold, outcome, oracle=None, codes=()):
    assert gold is None or gold['problem_text'] == text, cid
    return {'id': f'{stratum}-{cid}', 'stratum': stratum, 'source': 'build_s2_pilot_corpus.py (new, implementer)',
            'problem_text': text, 'gold_extraction': gold, 'expected': expected(outcome, oracle, codes)}


def expected(outcome, oracle, codes):
    e = {'outcome': outcome, 'is_ambiguous': outcome == 'CLARIFY'}
    if outcome == 'SERVED':
        e['oracle'] = oracle or {}
    if codes:
        e['allowed_clarification_codes'] = list(codes)
    return e


def only_unsupported(text, quote):
    return X(text, None, [], unresolved=[U('u1', 'unsupported', quote)])


VOL = {'volume': ['8/3']}
VOL_GOAL = M('mg1', 'volume', {'solid_id': 's1'}, 'Tính thể tích khối chóp S.ABCD')
CUBE_RECT = "Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, AA' = 4. Tính thể tích khối lập phương ABCD.A'B'C'D'."
CUBE_TALL = "Cho hình lập phương MNPQ.M'N'P'Q' có MM' = 5, đáy MNPQ là hình vuông cạnh 2. Tính thể tích khối lập phương MNPQ.M'N'P'Q'."
AB_PERP = ('Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2 và '
           'AB vuông góc với mặt phẳng (ABCD). Tính thể tích khối chóp S.ABCD.')
AC_3 = ('Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2 và AC = 3. '
        'Tính thể tích khối chóp S.ABCD.')
NO_SIDE = 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng (ABCD). Tính thể tích khối chóp S.ABCD.'
KC = 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. Tính k/c từ A đến mp(SBC).'
DT = 'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với đáy, SA = 2. Tính góc giữa đt SC và mp (ABCD).'


def cube(text, notation, solid_quote, premises, goal_quote):
    b, t = notation.split('.')
    split = lambda s: [x for x in __import__('re').findall(r"[A-Z]'?", s)]
    return X(text, solid_quote, [P('right_prism', solid_quote, base=split(b), top=split(t)), *premises],
             [M('mg1', 'volume', {'solid_id': 's1'}, goal_quote)], notation=notation, solid_type='prism')


CORPUS = [
    # S2-A — simulation only: served, no invented number
    *[reused('S2-A', cid, 'SERVED', {}) for cid in
      ('I02_ve', 'I04_mo_phong', 'I05_cho_minh_xem', 'I08_trailing_ve', 'I09_trailing_mo_phong_hinh', 'I12_trailing_point')],
    # S2-B — simulation + computation, several goals
    reused('S2-B', 'I07_ve_va_tinh', 'SERVED', VOL),
    reused('S2-B', 'I10_ve_roi_tinh', 'SERVED', VOL),
    reused('S2-B', 'I11_mo_phong_va_tinh_SC', 'SERVED', {'distance': ['2√3']}),
    reused('S2-B', 'P07_shared_intermediate_two_goals', 'SERVED', {'distance': ['√3', '1']}),
    reused('S2-B', 'P09_student_chain', 'SERVED', {'distance': ['√3']}),
    reused('S2-B', 'A03_control_with_dimensions', 'SERVED', {'volume': ['√3']}),
    # S2-C — elliptical goal or missing operand: the honest exit, then a clarification
    reused('S2-C', 'A01_goc_chieu', 'CLARIFY', codes=('AMBIGUOUS', 'MISSING_DATA')),
    reused('S2-C', 'D05_projection_missing_target', 'CLARIFY', codes=('MISSING_DATA', 'AMBIGUOUS')),
    reused('S2-C', 'D06_unnamed_prism', 'CLARIFY', codes=('MISSING_DATA',)),
    new('S2-C', 'C04_angle_plane_missing', f'{STD} Tính góc giữa SB và mặt phẳng.',
        c1(f'{STD} Tính góc giữa SB và mặt phẳng.', 'Cho hình chóp S.ABCD',
           unresolved=[U('u1', 'missing_operand', 'Tính góc giữa SB và mặt phẳng', ['target_line_or_plane'], ['angle'])]),
        'CLARIFY', codes=('MISSING_DATA', 'AMBIGUOUS')),
    new('S2-C', 'C05_draw_then_compute', f'{STD} Vẽ hình rồi tính.',
        c1(f'{STD} Vẽ hình rồi tính.', 'Cho hình chóp S.ABCD', sim='Vẽ hình',
           unresolved=[U('u1', 'missing_operand', 'rồi tính', ['goal_object'])]),
        'CLARIFY', codes=('MISSING_DATA',)),
    new('S2-C', 'C06_square_without_side', NO_SIDE,
        X(NO_SIDE, 'Cho hình chóp S.ABCD',
          [P('regular_polygon', 'đáy ABCD là hình vuông', vertices=list('ABCD')),
           P('perpendicular_line_plane', 'SA vuông góc với mặt phẳng (ABCD)', line=['S', 'A'], plane=list('ABCD'))],
          [VOL_GOAL], unresolved=[U('u1', 'missing_operand', 'đáy ABCD là hình vuông', ['dimension'])]),
        'CLARIFY', codes=('MISSING_DATA',)),
    # S2-D — contradictory givens or a wrong solid-class word: refused, never repaired
    reused('S2-D', 'D03_contradictory_length', 'REFUSED_INCONSISTENT'),
    reused('S2-D', 'D04_two_values_same_segment', 'REFUSED_INCONSISTENT'),
    new('S2-D', 'D07_cube_rectangle_base', CUBE_RECT,
        cube(CUBE_RECT, "ABCD.A'B'C'D'", "Cho hình lập phương ABCD.A'B'C'D'",
             [P('rectangle', 'đáy ABCD là hình chữ nhật', vertices=list('ABCD')),
              P('segment_length', 'AB = 2', segment=['A', 'B'], value='2'),
              P('segment_length', 'AD = 3', segment=['A', 'D'], value='3'),
              P('segment_length', "AA' = 4", segment=['A', "A'"], value='4')],
             "Tính thể tích khối lập phương ABCD.A'B'C'D'"), 'REFUSED_INCONSISTENT'),
    new('S2-D', 'D08_cube_tall', CUBE_TALL,
        cube(CUBE_TALL, "MNPQ.M'N'P'Q'", "Cho hình lập phương MNPQ.M'N'P'Q'",
             [P('segment_length', "MM' = 5", segment=['M', "M'"], value='5'),
              P('regular_polygon', 'đáy MNPQ là hình vuông cạnh 2', vertices=list('MNPQ'), side='2')],
             "Tính thể tích khối lập phương MNPQ.M'N'P'Q'"), 'REFUSED_INCONSISTENT'),
    new('S2-D', 'D09_base_edge_perp_base', AB_PERP,
        c1(AB_PERP, 'Cho hình chóp S.ABCD', [VOL_GOAL],
           extra=[P('perpendicular_line_plane', 'AB vuông góc với mặt phẳng (ABCD)', line=['A', 'B'], plane=list('ABCD'))]),
        'REFUSED_INCONSISTENT'),
    new('S2-D', 'D10_square_diagonal_3', AC_3,
        c1(AC_3, 'Cho hình chóp S.ABCD', [VOL_GOAL],
           extra=[P('segment_length', 'AC = 3', segment=['A', 'C'], value='3')]),
        'REFUSED_INCONSISTENT'),
    # S2-E — school topics outside the supported library: refused as unsupported
    *[new('S2-E', cid, text, only_unsupported(text, quote) if quote else gold, 'REFUSED_UNSUPPORTED')
      for cid, text, quote, gold in (
          ('E01_oxyz', 'Trong không gian Oxyz, cho điểm A(1; 2; 3) và mặt phẳng (P): 2x - y + 2z - 3 = 0. '
                       'Tính khoảng cách từ A đến mặt phẳng (P).', 'Trong không gian Oxyz', None),
          ('E02_truncated_pyramid', "Cho hình chóp cụt đều ABC.A'B'C' có cạnh đáy lớn bằng 4, cạnh đáy nhỏ bằng 2 và "
                                    "chiều cao bằng 3. Tính thể tích khối chóp cụt.", "hình chóp cụt đều ABC.A'B'C'", None),
          ('E03_volume_maximum', 'Cho hình hộp chữ nhật có tổng ba kích thước bằng 6. Tìm giá trị lớn nhất của thể tích '
                                 'khối hộp.', 'Tìm giá trị lớn nhất của thể tích khối hộp', None),
          ('E06_word_problem_rate', 'Một bể nước dạng hình hộp chữ nhật dài 2 m, rộng 1 m và cao 1 m. Vòi nước chảy vào '
                                    'bể 50 lít mỗi phút. Hỏi sau bao nhiêu phút thì bể đầy?',
           'Hỏi sau bao nhiêu phút thì bể đầy', None))],
    new('S2-E', 'E04_locus', f'{STD} Tìm tập hợp các điểm M trong không gian sao cho MA = MC.',
        c1(f'{STD} Tìm tập hợp các điểm M trong không gian sao cho MA = MC.', 'Cho hình chóp S.ABCD',
           unresolved=[U('u1', 'unsupported', 'Tìm tập hợp các điểm M trong không gian sao cho MA = MC')]),
        'REFUSED_UNSUPPORTED'),
    new('S2-E', 'E05_translation', f'{STD} Dựng ảnh của hình chóp S.ABCD qua phép tịnh tiến theo vectơ AB.',
        c1(f'{STD} Dựng ảnh của hình chóp S.ABCD qua phép tịnh tiến theo vectơ AB.', 'Cho hình chóp S.ABCD',
           unresolved=[U('u1', 'unsupported', 'Dựng ảnh của hình chóp S.ABCD qua phép tịnh tiến theo vectơ AB')]),
        'REFUSED_UNSUPPORTED'),
    # S2-F — colloquial / shorthand wording with diacritics: served (or a safe clarification), never wrong
    reused('S2-F', 'S02_vuong_goc_day', 'SERVED', VOL),
    reused('S2-F', 'S03_symbol_perp', 'SERVED', VOL),
    reused('S2-F', 'S07_typo_tone', 'SERVED', VOL),
    reused('S2-F', 'S08_altitude_wording', 'SERVED', VOL),
    # C1 chart: (SBC): x + z = 2 ⇒ d(A, (SBC)) = √2; cos²(SC, (ABCD)) = AC²/SC² = 8/12 = 2/3 (hand, see probe C1 note)
    new('S2-F', 'F05_kc_mp_shorthand', KC,
        c1(KC, 'Cho hình chóp S.ABCD', [M('mg1', 'distance', {'point': 'A', 'plane': ['S', 'B', 'C']},
                                          'Tính k/c từ A đến mp(SBC)')], perp='SA ⊥ (ABCD)'),
        'SERVED', {'distance': ['√2']}),
    new('S2-F', 'F06_dt_mp_shorthand', DT,
        c1(DT, 'Cho hình chóp S.ABCD', [M('mg1', 'angle', {'line': ['S', 'C'], 'plane': list('ABCD')},
                                          'Tính góc giữa đt SC và mp (ABCD)')], perp='SA vuông góc với đáy'),
        'SERVED', {'angle_cos_sq': ['2/3']}),
]

assert len(CORPUS) == 36 and all(sum(c['stratum'] == s for c in CORPUS) == 6 for s in
                                 ('S2-A', 'S2-B', 'S2-C', 'S2-D', 'S2-E', 'S2-F')), 'protocol §3 composition'
assert sum(c['source'].startswith('student_language_probe') for c in CORPUS) == 21

if __name__ == '__main__':
    doc = {'schema': 's2-student-language-pilot-corpus/1', 'measurement_class_if_run_live': 'LIVE_DEVELOPMENT_PILOT',
           'author': 'IMPLEMENTER (agent) — development texts, NOT independent, NOT held-out',
           'protocol': 's2-student-language-pilot-protocol.md §3',
           'excluded_by_design': 'the locked 60-case paired corpus (not written yet) and every independent holdout',
           'cases': CORPUS}
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'wrote {len(CORPUS)} cases to {sys.argv[1]}')
