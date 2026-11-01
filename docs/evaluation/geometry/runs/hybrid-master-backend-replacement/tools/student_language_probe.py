"""Tenth continuation: DEVELOPMENT diagnostic of student-style Vietnamese wording on the production Hybrid boundary.

Each case is raw learner text plus authored extractions: `gold` (what a faithful extractor must emit under the
`typed-fact-next/2` contract) and `adv:*` (a plausible extractor error). Every row runs the real path: the product domain
gate (`detect_domain`, the first gate of /api/analyze) → `run_hybrid_offline` (verbatim-quote validation → bridge →
Source Gate → planner → exact engine → Adapter /4). Expected behaviour and oracles are written by hand before any run and
are never read from extractor output; served values are compared with the executed bindings (`answer_exact`).

This measures the deterministic backend on authored extractions only. It says nothing about how well a live model reads
the same text (that needs approved provider calls); it is authored by the implementer, so it is not held-out.
Offline, 0 provider calls. Usage: student_language_probe.py [out.json]
"""
import json, os, re, socket, sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.hybrid_preview import classify_refusal  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, detect_domain  # noqa: E402

POLICY = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})

#: Refusal group (`classify_refusal`, the product taxonomy) → the Owner's NLU class. Mapping only; no new code.
NLU_OF_GROUP = {'CAPABILITY': 'VALID_BUT_UNSUPPORTED', 'MISSING_DATA': 'MISSING_DATA', 'INVALID_DATA': 'CONTRADICTORY_DATA',
                'SOURCE_UNVERIFIED': 'UNRECOGNIZED_WORDING', 'INCONCLUSIVE': 'VALID_BUT_UNSUPPORTED',
                'RESULT_UNVERIFIED': 'TECHNICAL_FAILURE', 'EXTRACTION_FAILED': 'TECHNICAL_FAILURE',
                'INTEGRITY': 'TECHNICAL_FAILURE', 'FALLBACK': 'TECHNICAL_FAILURE'}
NLU_OF_CODE = {'AMBIGUOUS_FACT': 'AMBIGUOUS', 'AMBIGUOUS_REFERENCE': 'AMBIGUOUS'}
NLU_OF_CLARIFICATION = {'ambiguous': 'AMBIGUOUS', 'missing_operand': 'MISSING_DATA',
                        'unrecognized_term': 'UNRECOGNIZED_WORDING', 'unsupported': 'VALID_BUT_UNSUPPORTED'}


# ---- payload authoring helpers ------------------------------------------------------------------------------------------
def P(kind, quote, **args):
    return {'kind': kind, 'args': args, 'quote': quote, 'solid_id': 's1'}


def M(gid, goal_type, target, quote):
    return {'goal_id': gid, 'kind': 'measurement', 'goal_type': goal_type, 'target': target, 'quote': quote,
            'solid_id': 's1'}


def X(text, solid_quote, premises, goals=(), sim=None, notation='S.ABCD', solid_type='pyramid', highlight=None,
      unresolved=None, length_unit='1'):
    """One `typed-fact-next/2` payload. `sim` = the simulation-request quote (defaults to the solid quote)."""
    sims = [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1', 'quote': sim or solid_quote}]
    if highlight:
        sims.append({'goal_id': 'sg2', 'kind': 'highlight_geometry', 'target_refs': highlight[1], 'quote': highlight[0]})
    out = {'schema_version': 'typed-fact-next/2', 'problem_text': text, 'length_unit': length_unit,
           'solids': [{'solid_id': 's1', 'solid_type': solid_type, 'notation': notation, 'quote': solid_quote}]
           if solid_quote else [],
           'premises': list(premises), 'derived_sections': [], 'relations': [],
           'simulation_goals': sims if solid_quote else [], 'math_goals': list(goals)}
    if unresolved is not None:
        out['unresolved'] = unresolved
    return out


def U(uid, kind, quote, missing=(), candidates=(), subject=None):
    u = {'unresolved_id': uid, 'kind': kind, 'quote': quote, 'missing_roles': list(missing),
         'candidate_relations': list(candidates)}
    if subject:
        u['subject_ref'] = subject
    return u


# C1: S.ABCD, square ABCD side 2, SA ⊥ (ABCD), SA = 2. Chart A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2).
# Hand oracles (squared for lengths / volumes, cos² for angles): V = 8/3; SC² = 12; (SBC): x + z = 2 ⇒ d(A)² = 2;
# cos²(SC,(ABCD)) = AC²/SC² = 2/3; M = mid SC = (1,1,1); H = proj A on SB = (1,0,1); K = proj A on SD = (0,1,1);
# O = AC ∩ BD = (1,1,0); foot of B on SD = (0,1,1) ⇒ d(B,SD)² = 6.
C1 = 'có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2'


def c1(text, solid_quote='hình chóp S.ABCD', goals=(), sim=None, extra=(), base='đáy ABCD là hình vuông cạnh 2',
       perp='SA vuông góc với mặt phẳng (ABCD)', length='SA = 2', **kw):
    prem = [P('regular_polygon', base, vertices=list('ABCD'), side='2'),
            P('perpendicular_line_plane', perp, line=['S', 'A'], plane=list('ABCD')),
            P('segment_length', length, segment=['S', 'A'], value='2'), *extra]
    return X(text, solid_quote, prem, goals, sim, **kw)


VOL = 'Tính thể tích khối chóp S.ABCD'
STD = f'Cho hình chóp S.ABCD {C1}.'


def case(cid, axes, text, extractions, expect):
    return {'id': cid, 'axes': axes, 'text': text, 'extractions': extractions, 'expect': expect}


def served(oracle=None, show=()):
    return {'action': 'SERVED', 'oracle': oracle or {}, 'show': list(show)}


def refused(nlu, codes=None):
    return {'action': 'REFUSED', 'nlu_class': nlu, 'codes': codes}


def clarify(nlu, kind, missing=()):
    return {'action': 'NEEDS_CLARIFICATION', 'nlu_class': nlu, 'kind': kind, 'missing': list(missing)}


V_C1 = {'mg1': ('sq', F(64, 9))}
CASES = [
    # --- intent wording: same givens, different simulation / request phrasing --------------------------------------
    case('I01_cho_tinh', {'family': 'pyramid', 'intent': 'measure', 'wording': 'standard'}, f'{STD} {VOL}.',
         {'gold': c1(f'{STD} {VOL}.', 'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         served(V_C1)),
    *[case(f'I0{i}_{tag}', {'family': 'pyramid', 'intent': 'simulate_only', 'wording': tag},
           f'{verb} hình chóp S.ABCD {C1}.',
           {'gold': c1(f'{verb} hình chóp S.ABCD {C1}.', 'hình chóp S.ABCD', sim=f'{verb} hình chóp S.ABCD'),
            'adv:invented_volume_goal': c1(f'{verb} hình chóp S.ABCD {C1}.', 'hình chóp S.ABCD',
                                           [M('mg1', 'volume', {'solid_id': 's1'}, f'{verb} hình chóp S.ABCD')],
                                           sim=f'{verb} hình chóp S.ABCD')},
           served(show=['S', 'A', 'B', 'C', 'D']))
      for i, (tag, verb) in enumerate([('ve', 'Vẽ'), ('dung', 'Dựng'), ('mo_phong', 'Mô phỏng'),
                                       ('cho_minh_xem', 'Cho mình xem'), ('hay_ve', 'Hãy vẽ')], start=2)],
    case('I07_ve_va_tinh', {'family': 'pyramid', 'intent': 'simulate_and_measure', 'wording': 've_opener'},
         f'Vẽ hình chóp S.ABCD {C1}. {VOL}.',
         {'gold': c1(f'Vẽ hình chóp S.ABCD {C1}. {VOL}.', 'hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)],
                     sim='Vẽ hình chóp S.ABCD')},
         served(V_C1)),
    case('I08_trailing_ve', {'family': 'pyramid', 'intent': 'simulate_only', 'wording': 'trailing_request'},
         f'{STD} Vẽ hình chóp S.ABCD.',
         {'gold': c1(f'{STD} Vẽ hình chóp S.ABCD.', 'Cho hình chóp S.ABCD', sim='Vẽ hình chóp S.ABCD')},
         served(show=['S'])),
    case('I09_trailing_mo_phong_hinh', {'family': 'pyramid', 'intent': 'simulate_only', 'wording': 'trailing_request'},
         f'{STD} Hãy mô phỏng hình.',
         {'gold': c1(f'{STD} Hãy mô phỏng hình.', 'Cho hình chóp S.ABCD', sim='Hãy mô phỏng hình')},
         served(show=['S'])),
    case('I10_ve_roi_tinh', {'family': 'pyramid', 'intent': 'simulate_and_measure', 'wording': 'mixed_sentence'},
         f'{STD} Vẽ hình rồi tính thể tích khối chóp S.ABCD.',
         {'gold': c1(f'{STD} Vẽ hình rồi tính thể tích khối chóp S.ABCD.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'volume', {'solid_id': 's1'}, 'tính thể tích khối chóp S.ABCD')], sim='Vẽ hình')},
         served(V_C1)),
    case('I11_mo_phong_va_tinh_SC', {'family': 'pyramid', 'intent': 'simulate_and_measure', 'wording': 'mixed_sentence'},
         f'{STD} Mô phỏng hình chóp và tính độ dài SC.',
         {'gold': c1(f'{STD} Mô phỏng hình chóp và tính độ dài SC.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'segment': ['S', 'C']}, 'tính độ dài SC')], sim='Mô phỏng hình chóp')},
         served({'mg1': ('sq', F(12))})),
    case('I12_trailing_point', {'family': 'pyramid', 'intent': 'simulate_point', 'wording': 'trailing_request',
                                'chain': 1},
         f'{STD} Gọi M là trung điểm của SC. Hãy mô phỏng hình và điểm M.',
         {'gold': c1(f'{STD} Gọi M là trung điểm của SC. Hãy mô phỏng hình và điểm M.', 'Cho hình chóp S.ABCD',
                     sim='Hãy mô phỏng hình và điểm M',
                     extra=[P('midpoint', 'Gọi M là trung điểm của SC', point='M', segment=['S', 'C'])])},
         served(show=['M'])),
    case('I13_chi_ra_duong_cao', {'family': 'pyramid', 'intent': 'highlight_role', 'wording': 'informal'},
         f'{STD} Vẽ hình rồi chỉ ra đường cao của hình chóp.',
         {'gold': c1(f'{STD} Vẽ hình rồi chỉ ra đường cao của hình chóp.', 'Cho hình chóp S.ABCD', sim='Vẽ hình',
                     highlight=('chỉ ra đường cao của hình chóp', ['S', 'A']))},
         served(show=['S', 'A'])),
    case('I14_hoi_bao_nhieu', {'family': 'pyramid', 'intent': 'measure', 'wording': 'question_form'},
         f'{STD} Thể tích khối chóp S.ABCD bằng bao nhiêu?',
         {'gold': c1(f'{STD} Thể tích khối chóp S.ABCD bằng bao nhiêu?', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'volume', {'solid_id': 's1'}, 'Thể tích khối chóp S.ABCD')])},
         served(V_C1)),

    # --- surface wording of the givens ---------------------------------------------------------------------------------
    case('S01_lowercase_cho', {'family': 'pyramid', 'wording': 'lowercase_sentence'}, f'cho hình chóp S.ABCD {C1}. tính thể tích khối chóp',
         {'gold': c1(f'cho hình chóp S.ABCD {C1}. tính thể tích khối chóp', 'cho hình chóp S.ABCD',
                     [M('mg1', 'volume', {'solid_id': 's1'}, 'tính thể tích khối chóp')])},
         served(V_C1)),
    case('S02_vuong_goc_day', {'family': 'pyramid', 'wording': 'dropped_preposition'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc đáy và SA = 2. {VOL}.',
         {'gold': c1(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc đáy và SA = 2. {VOL}.',
                     'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)], perp='SA vuông góc đáy')},
         served(V_C1)),
    case('S03_symbol_perp', {'family': 'pyramid', 'wording': 'math_symbol'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. {VOL}.',
         {'gold': c1(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. {VOL}.',
                     'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)], perp='SA ⊥ (ABCD)')},
         served(V_C1)),
    case('S04_no_spaces', {'family': 'pyramid', 'wording': 'spacing'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA=2. {VOL}.',
         {'gold': c1(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA=2. {VOL}.',
                     'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)], length='SA=2')},
         served(V_C1)),
    case('S05_no_diacritics', {'family': 'pyramid', 'wording': 'no_diacritics'},
         'Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc voi mat phang (ABCD) va SA = 2. '
         'Tinh the tich khoi chop S.ABCD.',
         {'gold': c1('Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc voi mat phang (ABCD) va SA = 2. '
                     'Tinh the tich khoi chop S.ABCD.', 'Cho hinh chop S.ABCD',
                     [M('mg1', 'volume', {'solid_id': 's1'}, 'Tinh the tich khoi chop S.ABCD')],
                     base='day ABCD la hinh vuong canh 2', perp='SA vuong goc voi mat phang (ABCD)')},
         served(V_C1)),
    case('S06_lowercase_labels', {'family': 'pyramid', 'wording': 'lowercase_labels'},
         'Cho hình chóp s.abcd có đáy abcd là hình vuông cạnh 2, sa vuông góc với mặt phẳng (abcd) và sa = 2. '
         'Tính thể tích khối chóp s.abcd.',
         {'gold': c1('Cho hình chóp s.abcd có đáy abcd là hình vuông cạnh 2, sa vuông góc với mặt phẳng (abcd) và sa = 2. '
                     'Tính thể tích khối chóp s.abcd.', 'Cho hình chóp s.abcd',
                     [M('mg1', 'volume', {'solid_id': 's1'}, 'Tính thể tích khối chóp s.abcd')],
                     base='đáy abcd là hình vuông cạnh 2', perp='sa vuông góc với mặt phẳng (abcd)', length='sa = 2')},
         served(V_C1)),
    case('S07_typo_tone', {'family': 'pyramid', 'wording': 'typo'},
         f'Cho hình chop S.ABCD {C1}. {VOL}.',
         {'gold': c1(f'Cho hình chop S.ABCD {C1}. {VOL}.', 'Cho hình chop S.ABCD',
                     [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         served(V_C1)),
    case('S08_altitude_wording', {'family': 'pyramid', 'wording': 'equivalent_relation'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, đường cao SA = 2. {VOL}.',
         {'gold': X(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, đường cao SA = 2. {VOL}.', 'Cho hình chóp S.ABCD',
                    [P('regular_polygon', 'đáy ABCD là hình vuông cạnh 2', vertices=list('ABCD'), side='2'),
                     P('altitude', 'đường cao SA', apex='S', foot='A'),
                     P('segment_length', 'SA = 2', segment=['S', 'A'], value='2')],
                    [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         served(V_C1)),

    # --- metamorphic: rename, permute independent clauses, scale ------------------------------------------------------
    case('R01_permuted_clauses', {'family': 'pyramid', 'metamorphic': 'permute'},
         f'Cho hình chóp S.ABCD có SA = 2, SA vuông góc với mặt phẳng (ABCD) và đáy ABCD là hình vuông cạnh 2. {VOL}.',
         {'gold': c1(f'Cho hình chóp S.ABCD có SA = 2, SA vuông góc với mặt phẳng (ABCD) và đáy ABCD là hình vuông cạnh 2. {VOL}.',
                     'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         served(V_C1)),
    case('R02_renamed', {'family': 'pyramid', 'metamorphic': 'rename'},
         'Cho hình chóp S.MNPQ có đáy MNPQ là hình vuông cạnh 2, SM vuông góc với mặt phẳng (MNPQ) và SM = 2. '
         'Tính thể tích khối chóp S.MNPQ.',
         {'gold': X('Cho hình chóp S.MNPQ có đáy MNPQ là hình vuông cạnh 2, SM vuông góc với mặt phẳng (MNPQ) và SM = 2. '
                    'Tính thể tích khối chóp S.MNPQ.', 'Cho hình chóp S.MNPQ',
                    [P('regular_polygon', 'đáy MNPQ là hình vuông cạnh 2', vertices=list('MNPQ'), side='2'),
                     P('perpendicular_line_plane', 'SM vuông góc với mặt phẳng (MNPQ)', line=['S', 'M'], plane=list('MNPQ')),
                     P('segment_length', 'SM = 2', segment=['S', 'M'], value='2')],
                    [M('mg1', 'volume', {'solid_id': 's1'}, 'Tính thể tích khối chóp S.MNPQ')], notation='S.MNPQ')},
         served(V_C1)),
    case('R03_scaled_x2', {'family': 'pyramid', 'metamorphic': 'scale'},
         'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 4. '
         f'{VOL}.',
         {'gold': X(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 4. {VOL}.',
                    'Cho hình chóp S.ABCD',
                    [P('regular_polygon', 'đáy ABCD là hình vuông cạnh 4', vertices=list('ABCD'), side='4'),
                     P('perpendicular_line_plane', 'SA vuông góc với mặt phẳng (ABCD)', line=['S', 'A'], plane=list('ABCD')),
                     P('segment_length', 'SA = 4', segment=['S', 'A'], value='4')],
                    [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         served({'mg1': ('sq', F(64 * 64, 9))})),
    case('R04_symbolic_a', {'family': 'pyramid', 'metamorphic': 'symbolic_unit'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD) và SA = a. {VOL} theo a.',
         {'gold': X(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD) và SA = a. {VOL} theo a.',
                    'Cho hình chóp S.ABCD',
                    [P('regular_polygon', 'đáy ABCD là hình vuông cạnh a', vertices=list('ABCD'), side='a'),
                     P('perpendicular_line_plane', 'SA vuông góc với mặt phẳng (ABCD)', line=['S', 'A'], plane=list('ABCD')),
                     P('segment_length', 'SA = a', segment=['S', 'A'], value='a')],
                    [M('mg1', 'volume', {'solid_id': 's1'}, f'{VOL} theo a')], length_unit='a')},
         served({'mg1': ('sq', F(1, 9))})),

    # --- composition: the planner recombines registry functions over constructed points ---------------------------
    case('P01_mid_then_distance', {'family': 'pyramid', 'chain': 2, 'goals': 1},
         f'{STD} Gọi M là trung điểm của SC. Tính khoảng cách từ M đến mặt phẳng (ABCD).',
         {'gold': c1(f'{STD} Gọi M là trung điểm của SC. Tính khoảng cách từ M đến mặt phẳng (ABCD).', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'point': 'M', 'plane': list('ABCD')}, 'Tính khoảng cách từ M đến mặt phẳng (ABCD)')],
                     extra=[P('midpoint', 'Gọi M là trung điểm của SC', point='M', segment=['S', 'C'])])},
         served({'mg1': ('sq', F(1))})),
    case('P02_proj_then_length', {'family': 'pyramid', 'chain': 2},
         f'{STD} Gọi H là hình chiếu vuông góc của A trên SB. Tính độ dài AH.',
         {'gold': c1(f'{STD} Gọi H là hình chiếu vuông góc của A trên SB. Tính độ dài AH.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'segment': ['A', 'H']}, 'Tính độ dài AH')],
                     extra=[P('orthogonal_projection_line', 'Gọi H là hình chiếu vuông góc của A trên SB', point='A',
                              image='H', line=['S', 'B'])]),
          'adv:role_swap': c1(f'{STD} Gọi H là hình chiếu vuông góc của A trên SB. Tính độ dài AH.', 'Cho hình chóp S.ABCD',
                              [M('mg1', 'distance', {'segment': ['A', 'H']}, 'Tính độ dài AH')],
                              extra=[P('orthogonal_projection_line', 'Gọi H là hình chiếu vuông góc của A trên SB',
                                       point='H', image='A', line=['S', 'B'])])},
         served({'mg1': ('sq', F(2))})),
    case('P03_two_proj_then_length', {'family': 'pyramid', 'chain': 3},
         f'{STD} Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SD. Tính độ dài HK.',
         {'gold': c1(f'{STD} Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SD. Tính độ dài HK.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'segment': ['H', 'K']}, 'Tính độ dài HK')],
                     extra=[P('orthogonal_projection_line', 'Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SD',
                              point='A', image='H', line=['S', 'B']),
                            P('orthogonal_projection_line', 'Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SD',
                              point='A', image='K', line=['S', 'D'])])},
         served({'mg1': ('sq', F(2))})),
    case('P04_intersection_then_length', {'family': 'pyramid', 'chain': 2},
         f'{STD} Gọi O là giao điểm của AC và BD. Tính độ dài SO.',
         {'gold': c1(f'{STD} Gọi O là giao điểm của AC và BD. Tính độ dài SO.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'segment': ['S', 'O']}, 'Tính độ dài SO')],
                     extra=[P('intersect_line_line', 'Gọi O là giao điểm của AC và BD', point='O', line1=['A', 'C'],
                              line2=['B', 'D'])])},
         served({'mg1': ('sq', F(6))})),
    case('P05_point_line_decomposition', {'family': 'pyramid', 'chain': 2, 'auxiliary': 'planner'},
         f'{STD} Tính khoảng cách từ B đến đường thẳng SD.',
         {'gold': c1(f'{STD} Tính khoảng cách từ B đến đường thẳng SD.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'point': 'B', 'line': ['S', 'D']}, 'Tính khoảng cách từ B đến đường thẳng SD')])},
         served({'mg1': ('sq', F(6))})),
    case('P06_two_mid_then_angle', {'family': 'pyramid', 'chain': 3},
         f'{STD} Gọi M, N lần lượt là trung điểm của SC, AB. Tính góc giữa đường thẳng MN và mặt phẳng (ABCD).',
         {'gold': c1(f'{STD} Gọi M, N lần lượt là trung điểm của SC, AB. Tính góc giữa đường thẳng MN và mặt phẳng (ABCD).',
                     'Cho hình chóp S.ABCD',
                     [M('mg1', 'angle', {'line': ['M', 'N'], 'plane': list('ABCD')},
                        'Tính góc giữa đường thẳng MN và mặt phẳng (ABCD)')],
                     extra=[P('midpoint', 'Gọi M, N lần lượt là trung điểm của SC, AB', point='M', segment=['S', 'C']),
                            P('midpoint', 'Gọi M, N lần lượt là trung điểm của SC, AB', point='N', segment=['A', 'B'])])},
         served({'mg1': ('cos2', F(1, 2))})),
    case('P07_shared_intermediate_two_goals', {'family': 'pyramid', 'chain': 2, 'goals': 2},
         f'{STD} Gọi M là trung điểm của SC. Tính độ dài AM và khoảng cách từ M đến mặt phẳng (ABCD).',
         {'gold': c1(f'{STD} Gọi M là trung điểm của SC. Tính độ dài AM và khoảng cách từ M đến mặt phẳng (ABCD).',
                     'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'segment': ['A', 'M']}, 'Tính độ dài AM'),
                      M('mg2', 'distance', {'point': 'M', 'plane': list('ABCD')}, 'khoảng cách từ M đến mặt phẳng (ABCD)')],
                     extra=[P('midpoint', 'Gọi M là trung điểm của SC', point='M', segment=['S', 'C'])])},
         served({'mg1': ('sq', F(3)), 'mg2': ('sq', F(1))})),
    case('P08_proj_foot_reused', {'family': 'pyramid', 'chain': 2},
         f'{STD} Gọi H là hình chiếu vuông góc của A trên SB. Tính khoảng cách từ H đến mặt phẳng (ABCD).',
         {'gold': c1(f'{STD} Gọi H là hình chiếu vuông góc của A trên SB. Tính khoảng cách từ H đến mặt phẳng (ABCD).',
                     'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'point': 'H', 'plane': list('ABCD')}, 'Tính khoảng cách từ H đến mặt phẳng (ABCD)')],
                     extra=[P('orthogonal_projection_line', 'Gọi H là hình chiếu vuông góc của A trên SB', point='A',
                              image='H', line=['S', 'B'])])},
         served({'mg1': ('sq', F(1))})),
    case('P09_student_chain', {'family': 'pyramid', 'chain': 2, 'intent': 'simulate_and_measure', 'wording': 've_opener'},
         f'Vẽ hình chóp S.ABCD {C1}. Gọi M là trung điểm SC. Mô phỏng hình và tính độ dài AM.',
         {'gold': c1(f'Vẽ hình chóp S.ABCD {C1}. Gọi M là trung điểm SC. Mô phỏng hình và tính độ dài AM.',
                     'hình chóp S.ABCD', [M('mg1', 'distance', {'segment': ['A', 'M']}, 'tính độ dài AM')],
                     sim='Vẽ hình chóp S.ABCD',
                     extra=[P('midpoint', 'Gọi M là trung điểm SC', point='M', segment=['S', 'C'])])},
         served({'mg1': ('sq', F(3))})),
    case('P10_proj_point_on_face', {'family': 'pyramid', 'chain': 2, 'intent': 'simulate_point'},
         f'{STD} Gọi H là hình chiếu vuông góc của A lên mặt phẳng (SBC). Tính độ dài AH.',
         {'gold': c1(f'{STD} Gọi H là hình chiếu vuông góc của A lên mặt phẳng (SBC). Tính độ dài AH.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'segment': ['A', 'H']}, 'Tính độ dài AH')],
                     extra=[P('orthogonal_projection', 'Gọi H là hình chiếu vuông góc của A lên mặt phẳng (SBC)',
                              point='A', image='H', plane=['S', 'B', 'C'])])},
         served({'mg1': ('sq', F(2))})),

    # --- the Owner's mandatory example and its positive control ------------------------------------------------------
    case('A01_goc_chieu', {'family': 'prism', 'ambiguity': 'undefined_term', 'wording': 'nonstandard_term'},
         'Mô phỏng điểm S là góc chiếu của hình lăng trụ xiên.',
         {'gold': X('Mô phỏng điểm S là góc chiếu của hình lăng trụ xiên.', None, [],
                    unresolved=[U('u1', 'ambiguous', 'S là góc chiếu của hình lăng trụ xiên',
                                  ['source_point', 'target_line_or_plane'], ['orthogonal_projection'], 'S')]),
          'adv:assume_projection_of_A_prime': X(
              'Mô phỏng điểm S là góc chiếu của hình lăng trụ xiên.', 'hình lăng trụ xiên',
              [P('orthogonal_projection', 'S là góc chiếu', point="A'", image='S', plane=['A', 'B', 'C'])],
              sim='Mô phỏng điểm S', notation="ABC.A'B'C'", solid_type='prism'),
          'adv:assume_S_apex': X('Mô phỏng điểm S là góc chiếu của hình lăng trụ xiên.', 'hình lăng trụ xiên', [],
                                 sim='Mô phỏng điểm S', notation='S.ABC')},
         clarify('AMBIGUOUS', 'ambiguous', ['source_point', 'target_line_or_plane'])),
    case('A02_control_dimensionless', {'family': 'prism', 'completeness': 'missing_dimensions', 'intent': 'simulate_point'},
         "Cho lăng trụ xiên ABC.A'B'C'. Gọi S là hình chiếu vuông góc của A' lên mặt phẳng (ABC). Hãy mô phỏng hình và điểm S.",
         {'gold': X("Cho lăng trụ xiên ABC.A'B'C'. Gọi S là hình chiếu vuông góc của A' lên mặt phẳng (ABC). Hãy mô phỏng hình và điểm S.",
                    "Cho lăng trụ xiên ABC.A'B'C'",
                    [P('orthogonal_projection', "Gọi S là hình chiếu vuông góc của A' lên mặt phẳng (ABC)", point="A'",
                       image='S', plane=['A', 'B', 'C'])],
                    sim='Hãy mô phỏng hình và điểm S', notation="ABC.A'B'C'", solid_type='prism')},
         refused('MISSING_DATA')),
    case('A03_control_with_dimensions', {'family': 'prism', 'intent': 'simulate_and_measure', 'chain': 2},
         "Cho lăng trụ xiên ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2. Gọi H là trung điểm của BC, hình chiếu vuông góc "
         "của A' lên mặt phẳng (ABC) là H và AA' = 2. Hãy mô phỏng hình và điểm H, rồi tính thể tích khối lăng trụ.",
         {'gold': X("Cho lăng trụ xiên ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2. Gọi H là trung điểm của BC, hình chiếu "
                    "vuông góc của A' lên mặt phẳng (ABC) là H và AA' = 2. Hãy mô phỏng hình và điểm H, rồi tính thể tích khối lăng trụ.",
                    "Cho lăng trụ xiên ABC.A'B'C'",
                    [P('regular_polygon', 'đáy ABC là tam giác đều cạnh 2', vertices=list('ABC'), side='2'),
                     P('midpoint', 'Gọi H là trung điểm của BC', point='H', segment=['B', 'C']),
                     P('orthogonal_projection', "hình chiếu vuông góc của A' lên mặt phẳng (ABC) là H", point="A'",
                       image='H', plane=['A', 'B', 'C']),
                     P('segment_length', "AA' = 2", segment=['A', "A'"], value='2')],
                    # A'H² = AA'² − AH² = 4 − 3 = 1; V = (√3)·1 ⇒ V² = 3
                    [M('mg1', 'volume', {'solid_id': 's1'}, 'tính thể tích khối lăng trụ')],
                    sim='Hãy mô phỏng hình và điểm H', notation="ABC.A'B'C'", solid_type='prism')},
         served({'mg1': ('sq', F(3))}, show=['H'])),

    # --- missing / contradictory / ambiguous ---------------------------------------------------------------------------
    case('D01_no_side', {'family': 'pyramid', 'completeness': 'missing_dimension'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông. {VOL}.',
         {'gold': X(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông. {VOL}.', 'Cho hình chóp S.ABCD',
                    [P('regular_polygon', 'đáy ABCD là hình vuông', vertices=list('ABCD'))],
                    [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         refused('MISSING_DATA')),
    case('D02_bare_solid', {'family': 'pyramid', 'completeness': 'missing_shape', 'intent': 'simulate_only'},
         'Vẽ hình chóp S.ABCD.',
         {'gold': X('Vẽ hình chóp S.ABCD.', 'hình chóp S.ABCD', [], sim='Vẽ hình chóp S.ABCD')},
         refused('MISSING_DATA')),
    case('D03_contradictory_length', {'family': 'pyramid', 'completeness': 'contradictory'},
         'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2 và SC = 5. '
         f'{VOL}.',
         {'gold': c1('Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2 và SC = 5. '
                     f'{VOL}.', 'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)],
                     extra=[P('segment_length', 'SC = 5', segment=['S', 'C'], value='5')])},
         refused('CONTRADICTORY_DATA')),
    case('D04_two_values_same_segment', {'family': 'pyramid', 'completeness': 'contradictory'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2 và SA = 3. {VOL}.',
         {'gold': c1(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2 và SA = 3. {VOL}.',
                     'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)],
                     extra=[P('segment_length', 'SA = 3', segment=['S', 'A'], value='3')])},
         refused('CONTRADICTORY_DATA')),
    case('D05_projection_missing_target', {'family': 'pyramid', 'completeness': 'missing_operand'},
         f'{STD} Gọi H là hình chiếu của S. Mô phỏng hình và điểm H.',
         {'gold': X(f'{STD} Gọi H là hình chiếu của S. Mô phỏng hình và điểm H.', None, [],
                    unresolved=[U('u1', 'missing_operand', 'Gọi H là hình chiếu của S', ['target_line_or_plane'],
                                  ['orthogonal_projection'], 'H')]),
          'adv:assume_onto_base': c1(f'{STD} Gọi H là hình chiếu của S. Mô phỏng hình và điểm H.', 'Cho hình chóp S.ABCD',
                                     sim='Mô phỏng hình và điểm H',
                                     extra=[P('orthogonal_projection', 'Gọi H là hình chiếu của S', point='S', image='H',
                                              plane=list('ABCD'))])},
         clarify('MISSING_DATA', 'missing_operand', ['target_line_or_plane'])),
    case('D06_unnamed_prism', {'family': 'prism', 'completeness': 'missing_notation', 'intent': 'simulate_only'},
         'Mô phỏng hình lăng trụ.',
         {'gold': X('Mô phỏng hình lăng trụ.', None, [],
                    unresolved=[U('u1', 'missing_operand', 'Mô phỏng hình lăng trụ', ['solid_notation', 'dimension'])])},
         clarify('MISSING_DATA', 'missing_operand', ['solid_notation', 'dimension'])),
    case('D07_unsupported_unnamed_projection', {'family': 'pyramid', 'intent': 'find_point', 'support': 'unsupported'},
         f'{STD} Tìm hình chiếu của A lên mặt phẳng (SBC).',
         {'gold': X(f'{STD} Tìm hình chiếu của A lên mặt phẳng (SBC).', None, [],
                    unresolved=[U('u1', 'unsupported', 'Tìm hình chiếu của A lên mặt phẳng (SBC)')])},
         clarify('VALID_BUT_UNSUPPORTED', 'unsupported')),

    # --- out of scope (the product domain gate) ------------------------------------------------------------------------
    case('O01_calculus', {'scope': 'other_subject'}, 'Tính đạo hàm của hàm số f(x) = x^2 + 3x.', {'gold': None},
         refused('OUT_OF_SCOPE')),
    case('O02_plane_geometry', {'scope': 'plane_geometry'}, 'Cho tam giác ABC vuông tại A có AB = 3, AC = 4. Tính BC.',
         {'gold': None}, refused('OUT_OF_SCOPE')),

    # --- adversarial extractor errors on a valid text: each must be refused, never served --------------------------
    case('X01_point_plane_vs_point_line', {'family': 'pyramid', 'contrastive': 'goal_operand'},
         f'{STD} Tính khoảng cách từ A đến mặt phẳng (SBC).',
         {'gold': c1(f'{STD} Tính khoảng cách từ A đến mặt phẳng (SBC).', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'point': 'A', 'plane': ['S', 'B', 'C']}, 'Tính khoảng cách từ A đến mặt phẳng (SBC)')]),
          'adv:point_line': c1(f'{STD} Tính khoảng cách từ A đến mặt phẳng (SBC).', 'Cho hình chóp S.ABCD',
                               [M('mg1', 'distance', {'point': 'A', 'line': ['S', 'B']}, 'Tính khoảng cách từ A đến mặt phẳng (SBC)')])},
         served({'mg1': ('sq', F(2))})),
    case('X02_dropped_goal', {'family': 'pyramid', 'completeness': 'dropped_request'}, f'{STD} {VOL}.',
         {'adv:dropped_volume': c1(f'{STD} {VOL}.', 'Cho hình chóp S.ABCD')}, served(V_C1)),
    case('X03_negated', {'family': 'pyramid', 'adversarial': 'negation'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA không vuông góc với mặt phẳng (ABCD) và SA = 2. {VOL}.',
         {'adv:negation_as_premise': c1(
             f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA không vuông góc với mặt phẳng (ABCD) và SA = 2. {VOL}.',
             'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)], perp='vuông góc với mặt phẳng (ABCD)')},
         refused('MISSING_DATA')),
    case('X04_conditional', {'family': 'pyramid', 'adversarial': 'conditional'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và SA = 2. Nếu SA vuông góc với mặt phẳng (ABCD) thì {VOL[0].lower()}{VOL[1:]} bằng bao nhiêu?',
         {'adv:condition_as_premise': c1(
             f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và SA = 2. Nếu SA vuông góc với mặt phẳng (ABCD) thì {VOL[0].lower()}{VOL[1:]} bằng bao nhiêu?',
             'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, 'thể tích khối chóp S.ABCD')])},
         refused('VALID_BUT_UNSUPPORTED')),
    case('X05_value_mismatch', {'family': 'pyramid', 'adversarial': 'value'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 3. {VOL}.',
         {'adv:wrong_value': X(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 3. {VOL}.',
                               'Cho hình chóp S.ABCD',
                               [P('regular_polygon', 'đáy ABCD là hình vuông cạnh 2', vertices=list('ABCD'), side='2'),
                                P('perpendicular_line_plane', 'SA vuông góc với mặt phẳng (ABCD)', line=['S', 'A'], plane=list('ABCD')),
                                P('segment_length', 'SA = 3', segment=['S', 'A'], value='2')],
                               [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         served({'mg1': ('sq', F(16))})),
    case('X06_invented_given', {'family': 'pyramid', 'adversarial': 'invented_fact'},
         f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và SA vuông góc với mặt phẳng (ABCD). {VOL}.',
         {'adv:invented_height': c1(f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và SA vuông góc với mặt phẳng (ABCD). {VOL}.',
                                    'Cho hình chóp S.ABCD', [M('mg1', 'volume', {'solid_id': 's1'}, VOL)])},
         refused('MISSING_DATA')),
    case('X07_lines_vs_segment', {'family': 'pyramid', 'contrastive': 'quantity_kind'},
         f'{STD} Tính khoảng cách giữa hai đường thẳng SA và BC.',
         {'gold': c1(f'{STD} Tính khoảng cách giữa hai đường thẳng SA và BC.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'distance', {'line1': ['S', 'A'], 'line2': ['B', 'C']}, 'Tính khoảng cách giữa hai đường thẳng SA và BC')]),
          'adv:segment_length': c1(f'{STD} Tính khoảng cách giữa hai đường thẳng SA và BC.', 'Cho hình chóp S.ABCD',
                                   [M('mg1', 'distance', {'segment': ['S', 'A']}, 'Tính khoảng cách giữa hai đường thẳng SA và BC')])},
         served({'mg1': ('sq', F(4))})),
    case('X08_simulation_goal_swapped', {'family': 'pyramid', 'contrastive': 'intent_vs_measure'},
         f'{STD} Mô phỏng hình chóp.',
         {'gold': c1(f'{STD} Mô phỏng hình chóp.', 'Cho hình chóp S.ABCD', sim='Mô phỏng hình chóp'),
          'adv:sim_as_volume': c1(f'{STD} Mô phỏng hình chóp.', 'Cho hình chóp S.ABCD',
                                  [M('mg1', 'volume', {'solid_id': 's1'}, 'Mô phỏng hình chóp')], sim='Mô phỏng hình chóp')},
         served(show=['S'])),
    # smuggled givens and new objects inside a simulation request must stay unread
    case('X09_smuggled_value_in_request', {'family': 'pyramid', 'adversarial': 'smuggled_given'},
         f'{STD} Vẽ hình chóp với SC = 5.',
         {'adv:ignore_smuggled': c1(f'{STD} Vẽ hình chóp với SC = 5.', 'Cho hình chóp S.ABCD', sim='Vẽ hình chóp')},
         refused('UNRECOGNIZED_WORDING')),
    case('X10_new_object_in_request', {'family': 'pyramid', 'adversarial': 'unbuilt_object'},
         f'{STD} Vẽ hình và điểm M.',
         {'adv:show_unbuilt_point': c1(f'{STD} Vẽ hình và điểm M.', 'Cho hình chóp S.ABCD', sim='Vẽ hình và điểm M')},
         refused('UNRECOGNIZED_WORDING')),
    case('X11_negated_request', {'family': 'pyramid', 'adversarial': 'negated_request'},
         f'{STD} Không cần vẽ hình, {VOL[0].lower()}{VOL[1:]}.',
         {'gold': c1(f'{STD} Không cần vẽ hình, {VOL[0].lower()}{VOL[1:]}.', 'Cho hình chóp S.ABCD',
                     [M('mg1', 'volume', {'solid_id': 's1'}, 'tính thể tích khối chóp S.ABCD')])},
         served(V_C1)),
]


# ---- scoring -----------------------------------------------------------------------------------------------------------
def squared(coef):
    m = re.fullmatch(r'(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?', coef or '')
    if not m or not (m['p'] or m['r']):
        return None
    p, r, q = F(m['p'] or 1), F(m['r'] or 1), F(m['q'] or 1)
    return p * p * r / (q * q)


def observe(text, payload):
    if detect_domain(text) != DOMAIN_HINH_HOC:
        return {'status': 'REFUSED', 'code': 'GATE_OUT_OF_SCOPE', 'nlu_class': 'OUT_OF_SCOPE', 'stage': 'domain'}
    out = run_hybrid_offline(text, ReplayExtractor({text: payload} if payload is not None else {}), policy=POLICY)
    route, env = out.response['route_d'], out.response['envelope']
    o = {'status': route['status'], 'code': env.get('reason_code'), 'stage': out.receipt.get('failure_stage')}
    if route['status'] == 'SERVED':
        o['answer_exact'] = route.get('answer_exact') or {}
        o['scene_labels'] = sorted({str(x.get('label') or x.get('id')) for x in env['scene3d']['objects']})
        return o
    clar = (route.get('refusal') or {}).get('clarification')
    o['clarification'] = clar
    o['nlu_class'] = (NLU_OF_CLARIFICATION.get(clar.get('kind')) if clar else
                      NLU_OF_CODE.get(o['code']) or NLU_OF_GROUP[classify_refusal(o['code'] or '').group])
    return o


def score(expect, o, adversarial):
    if adversarial:
        return 'SAFE_REFUSAL' if o['status'] != 'SERVED' else 'WRONG_SERVED'
    if expect['action'] == 'SERVED':
        if o['status'] != 'SERVED':
            return 'FALSE_REFUSAL'
        for gid, (kind, want) in expect['oracle'].items():
            got = (o['answer_exact'].get(gid) or {}).get('coef')
            value = F(got) if kind == 'cos2' and got and '√' not in got else squared(got)
            if value != want:
                return 'WRONG_SERVED'
        if set(o['answer_exact']) != set(expect['oracle']):
            return 'WRONG_SERVED'
        missing = [s for s in expect['show'] if not any(s == lab or lab.startswith(s) for lab in o['scene_labels'])]
        return 'SERVED_INCOMPLETE_SCENE' if missing else 'SERVED_CORRECT'
    if o['status'] == 'SERVED':
        return 'WRONG_SERVED'
    if expect['action'] == 'NEEDS_CLARIFICATION':
        c = o.get('clarification')
        if not c:
            return 'REFUSED_NO_CLARIFICATION'
        ok = c.get('kind') == expect['kind'] and sorted(c.get('missing_roles') or []) == sorted(expect['missing'])
        return 'NEEDS_CLARIFICATION_CORRECT' if ok else 'CLARIFICATION_WRONG'
    return 'CORRECT_REFUSAL' if o['nlu_class'] == expect['nlu_class'] else 'REFUSAL_WRONG_CLASS'


rows = []
for c in CASES:
    for label, payload in c['extractions'].items():
        o = observe(c['text'], payload)
        adversarial = label.startswith('adv:')
        rows.append({'id': c['id'], 'extraction': label, 'axes': c['axes'], 'expect': None if adversarial else c['expect'],
                     'observed': o, 'outcome': score(c['expect'], o, adversarial)})
        print(f"{c['id']:36s} {label:34s} {o['status']:8s} {str(o['code']):34s} {rows[-1]['outcome']}")

summary = {}
for r in rows:
    key = 'adversarial' if r['extraction'].startswith('adv:') else 'gold'
    summary.setdefault(key, {}).setdefault(r['outcome'], 0)
    summary[key][r['outcome']] += 1
print(json.dumps(summary, ensure_ascii=False))
if len(sys.argv) > 1:
    import subprocess
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend/app'], cwd=ROOT, text=True).strip())
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'DEVELOPMENT_DIAGNOSTIC_NOT_HELDOUT_NOT_LIVE', 'provider_calls': 0,
                   'identity': {'head': head, 'product_uncommitted': dirty}, 'summary': summary, 'rows': rows},
                  f, ensure_ascii=False, indent=1, default=str)
        f.write('\n')
