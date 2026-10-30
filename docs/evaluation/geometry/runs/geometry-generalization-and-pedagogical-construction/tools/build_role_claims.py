"""Amendment layer (pre-freeze review B1): role-claim negatives whose PAYLOAD agrees with the wrong reading, plus a
genuine-height positive. Derived from the frozen dev corpus by one text+fact edit each. Writes role-claims.json once."""
import json
from copy import deepcopy
from pathlib import Path

W = Path(__file__).resolve().parents[1]
CASES = json.loads((W / 'dev-corpus/cases.json').read_text(encoding='utf-8'))


def edit(cid, old_quote, new_quote, new_seg=None, new_value=None):
    p = deepcopy(CASES[cid]['payload'])
    assert p['problem_text'].count(old_quote) == 1
    p['problem_text'] = p['problem_text'].replace(old_quote, new_quote)
    x = next(x for x in p['premises'] if x['quote'] == old_quote)
    x['quote'] = new_quote
    if new_seg:
        x['args']['segment'] = new_seg
    if new_value:
        x['args']['value'] = new_value
    return p


out = {
    # SP ⊥ (PQR) is stated; "chiều cao SQ" names a segment that is not the height (payload: |SQ| = 15a, a consistent figure)
    'RC.height_not_perpendicular_pyr3': {'class': 'NEGATIVE', 'payload': edit('TP2.tg_day.area', 'chiều cao SP = 14a', 'chiều cao SQ = 15a', ['S', 'Q'], '15a')},
    # SD ⊥ (DEFG) is stated; "chiều cao SE" claims the lateral edge SE is the height
    'RC.height_not_perpendicular_pyr4': {'class': 'NEGATIVE', 'payload': edit('QP1.thoa_man.area', 'và cạnh SD = 15', 'và chiều cao SE = 17', ['S', 'E'], '17')},
    # "cạnh bên DG": DG is a base side, not a lateral edge (pre-existing gap N1 closed by the same check)
    'RC.lateral_edge_is_base_side': {'class': 'NEGATIVE', 'payload': edit('QP1.thoa_man.area', 'biết DG = 10', 'biết cạnh bên DG = 10')},
    # genuine height: SD ⊥ (DEFG) is stated, so "chiều cao SD" is proved — must give the canonical answer
    'RC.height_proved': {'class': 'VARIANT', 'oracle': 'QP1.canon.area', 'payload': edit('QP1.thoa_man.area', 'và cạnh SD = 15', 'và chiều cao SD = 15')},
}
with (W / 'dev-corpus/role-claims.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
print(len(out))
