"""Independent W4 development corpus for premise-sentence generalization (not derived from Wave 3 text).

Each geometry is stated once in a CANONICAL phrasing (a form the product served before W4) and in several VARIANT
phrasings that use connectors / lexical forms common in Vietnamese textbooks. The payload (facts) is identical across
phrasings; only quotes follow the text. Oracle (metamorphic): a variant must give exactly the canonical answer, and the
canonical answer must be produced by the pre-W4 product. Negatives tamper one thing and must never be served.
Writes cases.json once (x mode)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'dev-corpus'
SEP = ', '


def tri_pyramid(L, v, h, k, r, rel):
    """S.L0L1L2, right angle at L0, S L0 ⊥ base; point k on S L1 (Sk = r S L1)."""
    s, (a, b, c), (x, y) = 'S', L, v
    solid = f'{s}.{a}{b}{c}'
    prem = [
        ('right_angle', {'vertices': [a, b, c], 'right_at': a},
         {'canon': f'có đáy {a}{b}{c} là tam giác vuông tại {a}', 'thoa_man': f'thỏa mãn đáy {a}{b}{c} là tam giác vuông tại {a}',
          'voi_so_do': f'với mặt đáy {a}{b}{c} là tam giác vuông ở {a}', 'tg_day': f'biết tam giác đáy {a}{b}{c} vuông tại {a}'}),
        ('perpendicular_line_plane', {'line': [s, a], 'plane': [a, b, c]},
         {'canon': f'cạnh bên {s}{a} vuông góc với mặt phẳng ({a}{b}{c})', 'thoa_man': f'thỏa mãn {s}{a} ⊥ ({a}{b}{c})',
          'voi_so_do': f'đường thẳng {s}{a} vuông góc với mặt phẳng ({a}{b}{c})', 'tg_day': f'cạnh bên {s}{a} vuông góc với mặt phẳng ({a}{b}{c})'}),
        ('segment_length', {'segment': [a, b], 'value': x},
         {'canon': f'biết {a}{b} = {x}', 'thoa_man': f'thỏa mãn {a}{b} = {x}', 'voi_so_do': f'có số đo {a}{b} = {x}', 'tg_day': f'với độ dài {a}{b} = {x}'}),
        ('segment_length', {'segment': [a, c], 'value': y},
         {'canon': f'{a}{c} = {y}', 'thoa_man': f'biết {a}{c} = {y}', 'voi_so_do': f'đoạn {a}{c} = {y}', 'tg_day': f'cạnh {a}{c} = {y}'}),
        ('segment_length', {'segment': [s, a], 'value': h},
         {'canon': f'và {s}{a} = {h}', 'thoa_man': f'và cạnh {s}{a} = {h}', 'voi_so_do': f'độ dài {s}{a} = {h}', 'tg_day': f'chiều cao {s}{a} = {h}'}),
    ]
    lead = {'canon': f'Xét hình chóp {solid}', 'thoa_man': f'Xét hình chóp tam giác {solid}', 'voi_so_do': f'Cho hình chóp {solid}',
            'tg_day': f'Trong không gian, cho hình chóp tam giác {solid}'}
    point = ('divide_segment', {'point': k, 'segment': [s, b], 'ratio': r}, f'Lấy điểm {k} trên cạnh {s}{b} sao cho {s}{k} = {r} {s}{b}')
    return solid, 'pyramid', lead, prem, point, rel


def rect_pyramid(L, v, h, k, r, rel):
    s, (a, b, c, d), (x, y) = 'S', L, v
    solid = f'{s}.{a}{b}{c}{d}'
    prem = [
        ('rectangle', {'vertices': [a, b, c, d]},
         {'canon': f'có đáy {a}{b}{c}{d} là hình chữ nhật', 'thoa_man': f'thỏa mãn đáy {a}{b}{c}{d} là hình chữ nhật',
          'voi_so_do': f'với tứ giác đáy {a}{b}{c}{d} là hình chữ nhật'}),
        ('perpendicular_line_plane', {'line': [s, a], 'plane': [a, b, c, d]},
         {'canon': f'cạnh bên {s}{a} vuông góc với mặt phẳng ({a}{b}{c}{d})', 'thoa_man': f'thỏa mãn {s}{a} ⊥ ({a}{b}{c}{d})',
          'voi_so_do': f'đường thẳng {s}{a} vuông góc với mặt phẳng ({a}{b}{c}{d})'}),
        ('segment_length', {'segment': [a, b], 'value': x},
         {'canon': f'biết {a}{b} = {x}', 'thoa_man': f'thỏa mãn {a}{b} = {x}', 'voi_so_do': f'có số đo {a}{b} = {x}'}),
        ('segment_length', {'segment': [a, d], 'value': y},
         {'canon': f'{a}{d} = {y}', 'thoa_man': f'biết {a}{d} = {y}', 'voi_so_do': f'đoạn {a}{d} = {y}'}),
        ('segment_length', {'segment': [s, a], 'value': h},
         {'canon': f'và {s}{a} = {h}', 'thoa_man': f'và cạnh {s}{a} = {h}', 'voi_so_do': f'độ dài {s}{a} = {h}'}),
    ]
    lead = {'canon': f'Xét hình chóp {solid}', 'thoa_man': f'Cho hình chóp tứ giác {solid}', 'voi_so_do': f'Trong không gian, cho hình chóp tứ giác {solid}'}
    point = ('divide_segment', {'point': k, 'segment': [a, b], 'ratio': r}, f'Lấy điểm {k} trên cạnh {a}{b} sao cho {a}{k} = {r} {a}{b}')
    return solid, 'pyramid', lead, prem, point, rel


def right_prism(L, v, h, k, r, rel):
    (a, b, c), (x, y) = L, v
    top = [f"{p}'" for p in (a, b, c)]
    solid = f"{a}{b}{c}.{''.join(top)}"
    prem = [
        ('right_angle', {'vertices': [a, b, c], 'right_at': a},
         {'canon': f'có đáy {a}{b}{c} là tam giác vuông tại {a}', 'tg_day': f'biết tam giác đáy {a}{b}{c} vuông tại {a}',
          'voi_so_do': f'với mặt đáy {a}{b}{c} là tam giác vuông ở {a}'}),
        ('segment_length', {'segment': [a, b], 'value': x},
         {'canon': f'biết {a}{b} = {x}', 'tg_day': f'với độ dài {a}{b} = {x}', 'voi_so_do': f'có số đo {a}{b} = {x}'}),
        ('segment_length', {'segment': [a, c], 'value': y},
         {'canon': f'{a}{c} = {y}', 'tg_day': f'cạnh {a}{c} = {y}', 'voi_so_do': f'đoạn {a}{c} = {y}'}),
        ('segment_length', {'segment': [a, f"{a}'"], 'value': h},
         {'canon': f"và {a}{a}' = {h}", 'tg_day': f"chiều cao {a}{a}' = {h}", 'voi_so_do': f"độ dài {a}{a}' = {h}"}),
    ]
    lead = {'canon': f'Xét khối lăng trụ đứng {solid}', 'tg_day': f'Cho hình lăng trụ đứng {solid}', 'voi_so_do': f'Xét hình lăng trụ đứng {solid}'}
    base = ('right_prism', {'base': [a, b, c], 'top': top})
    point = ('divide_segment', {'point': k, 'segment': [a, b], 'ratio': r}, f'Lấy điểm {k} trên cạnh {a}{b} sao cho {a}{k} = {r} {a}{b}')
    return solid, 'prism', lead, prem, point, rel, base


def cuboid(L, v, h, k, r, rel):
    (a, b, c, d), (x, y) = L, v
    top = [f"{p}'" for p in (a, b, c, d)]
    solid = f"{a}{b}{c}{d}.{''.join(top)}"
    prem = [
        ('rectangle', {'vertices': [a, b, c, d]},
         {'canon': f'có đáy {a}{b}{c}{d} là hình chữ nhật', 'voi_so_do': f'với tứ giác đáy {a}{b}{c}{d} là hình chữ nhật',
          'thoa_man': f'thỏa mãn đáy {a}{b}{c}{d} là hình chữ nhật'}),
        ('segment_length', {'segment': [a, b], 'value': x},
         {'canon': f'biết {a}{b} = {x}', 'voi_so_do': f'có số đo {a}{b} = {x}', 'thoa_man': f'thỏa mãn {a}{b} = {x}'}),
        ('segment_length', {'segment': [a, d], 'value': y},
         {'canon': f'{a}{d} = {y}', 'voi_so_do': f'đoạn {a}{d} = {y}', 'thoa_man': f'biết {a}{d} = {y}'}),
        ('segment_length', {'segment': [a, f"{a}'"], 'value': h},
         {'canon': f"và {a}{a}' = {h}", 'voi_so_do': f"độ dài {a}{a}' = {h}", 'thoa_man': f"và cạnh {a}{a}' = {h}"}),
    ]
    lead = {'canon': f'Xét hình hộp chữ nhật {solid}', 'voi_so_do': f'Trong không gian, cho hình hộp chữ nhật {solid}',
            'thoa_man': f'Cho khối hộp chữ nhật {solid}'}
    base = ('right_prism', {'base': [a, b, c, d], 'top': top})
    point = ('divide_segment', {'point': k, 'segment': [a, b], 'ratio': r}, f'Lấy điểm {k} trên cạnh {a}{b} sao cho {a}{k} = {r} {a}{b}')
    return solid, 'prism', lead, prem, point, rel, base


def cube(L, v, h, k, r, rel):
    (a, b, c, d), (x, _y) = L, v
    top = [f"{p}'" for p in (a, b, c, d)]
    solid = f"{a}{b}{c}{d}.{''.join(top)}"
    prem = [
        ('base_is_square', {'vertices': [a, b, c, d], 'side': x},
         {'canon': f'có đáy {a}{b}{c}{d} là hình vuông cạnh {x}', 'biet_mat_day': f'biết mặt đáy {a}{b}{c}{d} là hình vuông có cạnh bằng {x}',
          'voi_day': f'với đáy {a}{b}{c}{d} là hình vuông cạnh bằng {x}'}),
        ('segment_length', {'segment': [a, f"{a}'"], 'value': x},
         {'canon': f"cạnh bên {a}{a}' = {x}", 'biet_mat_day': f"cạnh bên {a}{a}' = {x}", 'voi_day': f"cạnh bên {a}{a}' = {x}"}),
    ]
    lead = {'canon': f'Cho hình lập phương {solid}', 'biet_mat_day': f'Xét hình lập phương {solid}', 'voi_day': f'Cho khối lập phương {solid}'}
    base = ('right_prism', {'base': [a, b, c, d], 'top': top})
    point = ('divide_segment', {'point': k, 'segment': [a, b], 'ratio': r}, f'Lấy điểm {k} trên cạnh {a}{b} sao cho {a}{k} = {r} {a}{b}')
    return solid, 'prism', lead, prem, point, rel, base


def make(cid, spec, style, plane, question, tamper=None):
    solid, stype, lead, prem, point, rel, *rest = spec
    base = rest[0] if rest else None
    clauses = [(kind, args, quotes[style]) for kind, args, quotes in prem]
    text_clauses = [q for _k, _a, q in clauses]
    payload_prem = ([{'kind': base[0], 'args': base[1], 'quote': lead[style], 'solid_id': 's1'}] if base else [])
    payload_prem += [{'kind': k, 'args': a, 'quote': q, 'solid_id': 's1'} for k, a, q in clauses]
    first = lead[style] + ' ' + SEP.join(text_clauses) + '.'
    pk, pargs, ptext = point
    payload_prem.append({'kind': pk, 'args': pargs, 'quote': ptext, 'solid_id': 's1'})
    name = plane['name']
    if rel == 'two':
        la, lb = plane['lines']
        ptxt = f"Gọi ({name}) là mặt phẳng qua {pargs['point']}, song song với hai đường thẳng {''.join(la)} và {''.join(lb)}"
        sec = {'plane_kind': 'through_point_parallel_two_lines', 'parallel_line_a': la, 'parallel_line_b': lb}
    else:
        ln = plane['line']
        ptxt = f"Xét mặt phẳng ({name}) đi qua điểm {pargs['point']} và vuông góc với đường thẳng {''.join(ln)}"
        sec = {'plane_kind': 'through_point_perpendicular_line', 'perpendicular_line': ln}
    if question == 'area':
        qtxt = f'Hãy tính diện tích thiết diện tạo bởi mặt phẳng ({name}) với hình {"chóp" if stype == "pyramid" else "khối"} {solid}'
        qtxt = f'Hãy tính diện tích thiết diện tạo bởi mặt phẳng ({name}) với {"hình chóp" if stype == "pyramid" else "hình lăng trụ"} {solid}'
        math = [{'goal_id': 'mg1', 'kind': 'measurement', 'goal_type': 'area', 'solid_id': 's1', 'target': {'section_id': 'sec'}, 'quote': qtxt}]
        sim = []
    else:
        qtxt = f'Xác định thiết diện của {"hình chóp" if stype == "pyramid" else "hình lăng trụ"} {solid} cắt bởi mặt phẳng ({name})'
        math = []
        sim = [{'goal_id': 'sg2', 'kind': 'construct_plane_section', 'target_section_id': 'sec', 'quote': qtxt}]
    text = f'{first} {ptext}. {ptxt}. {qtxt}.'
    if tamper:
        text, payload_prem = tamper(text, payload_prem)
    payload = {
        'schema_version': 'typed-fact-next/2', 'problem_text': text,
        'length_unit': 'a' if any('a' in str(a.get('value', '')) or 'a' in str(a.get('side', '')) for _k, a, _q in clauses) else '1',
        'solids': [{'solid_id': 's1', 'solid_type': stype, 'notation': solid, 'quote': lead[style]}],
        'premises': payload_prem,
        'derived_sections': [{'section_id': 'sec', 'plane_name': name, 'target_solid_id': 's1', 'through_point': pargs['point'],
                              **sec, 'quote': ptxt, 'stated_intersections': []}],
        'relations': [],
        'simulation_goals': [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1', 'quote': lead[style]}, *sim],
        'math_goals': math,
    }
    return {'id': cid, 'style': style, 'question': question, 'payload': payload}


def styles(spec):
    return [s for s in spec[2] if s != 'canon']


def main():
    geoms = {
        'TP1': (tri_pyramid(('D', 'E', 'F'), ('6', '8'), '12', 'K', '2/5', 'two'), {'name': 'α', 'lines': [['D', 'E'], ['D', 'F']]}),
        'TP2': (tri_pyramid(('P', 'Q', 'R'), ('5a', '9a'), '14a', 'N', '3/7', 'two'), {'name': 'β', 'lines': [['S', 'P'], ['P', 'R']]}),
        'TP3': (tri_pyramid(('D', 'E', 'F'), ('6', '8'), '12', 'K', '2/5', 'perp'), {'name': 'P', 'line': ['S', 'E']}),
        'QP1': (rect_pyramid(('D', 'E', 'F', 'G'), ('7', '10'), '15', 'K', '3/8', 'two'), {'name': 'α', 'lines': [['S', 'D'], ['D', 'G']]}),
        'RP1': (right_prism(('D', 'E', 'F'), ('5', '12'), '9', 'K', '1/3', 'two'), {'name': 'γ', 'lines': [["D", "D'"], ['D', 'F']]}),
        'RP2': (right_prism(('P', 'Q', 'R'), ('4a', '7a'), '11a', 'N', '2/9', 'two'), {'name': 'Q', 'lines': [["P", "P'"], ['P', 'R']]}),
        'HB1': (cuboid(('D', 'E', 'F', 'G'), ('6', '9'), '15', 'K', '4/9', 'two'), {'name': 'β', 'lines': [["D", "D'"], ['D', 'G']]}),
        'CB1': (cube(('D', 'E', 'F', 'G'), ('8', None), None, 'K', '3/8', 'two'), {'name': 'α', 'lines': [["D", "D'"], ['D', 'G']]}),
        'CB2': (cube(('P', 'Q', 'R', 'T'), ('10a', None), None, 'N', '2/5', 'perp'), {'name': 'R', 'line': ['P', 'Q']}),
    }
    cases = {}
    for gid, (spec, plane) in geoms.items():
        for q in ('area', 'section'):
            cases[f'{gid}.canon.{q}'] = {**make(f'{gid}.canon.{q}', spec, 'canon', plane, q), 'class': 'CANON', 'geometry': gid}
            for st in styles(spec):
                cases[f'{gid}.{st}.{q}'] = {**make(f'{gid}.{st}.{q}', spec, st, plane, q), 'class': 'VARIANT', 'geometry': gid,
                                            'oracle': f'{gid}.canon.{q}'}
    # negatives: one tamper each, built on a variant phrasing; must never be served
    def value_tamper(t, p):
        p = json.loads(json.dumps(p)); seg = next(x for x in p if x['kind'] == 'segment_length'); seg['args']['value'] = '7' if seg['args']['value'] != '7' else '9'
        return t, p
    def qualifier(t, p):
        return t.replace('hình chóp tam giác', 'hình chóp tứ giác'), [{**x, 'quote': x['quote'].replace('hình chóp tam giác', 'hình chóp tứ giác')} for x in p]
    def conditional(t, p):
        return t.replace('thỏa mãn SD ⊥', 'giả sử SD ⊥'), [{**x, 'quote': x['quote'].replace('thỏa mãn SD ⊥', 'giả sử SD ⊥')} for x in p]
    def disjunction(t, p):
        return t.replace('và cạnh SD = 12.', 'và cạnh SD = 12 hoặc SD = 13.'), p
    def wrong_height(t, p):
        return t.replace("chiều cao DD' = 9", "chiều cao EE' = 9"), [{**x, 'quote': x['quote'].replace("chiều cao DD' = 9", "chiều cao EE' = 9")} for x in p]
    def cube_side(t, p):
        p = json.loads(json.dumps(p)); sq = next(x for x in p if x['kind'] == 'base_is_square'); sq['args']['side'] = '9'
        return t, p
    def wrong_right_vertex(t, p):
        return t.replace('vuông ở D', 'vuông ở E'), [{**x, 'quote': x['quote'].replace('vuông ở D', 'vuông ở E')} for x in p]
    negs = [('N.value', 'TP1', 'thoa_man', value_tamper), ('N.qualifier', 'TP1', 'thoa_man', qualifier),
            ('N.conditional', 'TP1', 'thoa_man', conditional), ('N.disjunction', 'TP1', 'thoa_man', disjunction),
            ('N.wrong_height', 'RP1', 'tg_day', wrong_height), ('N.cube_side', 'CB1', 'biet_mat_day', cube_side),
            ('N.cube_side_voi', 'CB1', 'voi_day', cube_side), ('N.wrong_right_vertex', 'TP1', 'voi_so_do', wrong_right_vertex),
            ('N.value_prism', 'RP1', 'voi_so_do', value_tamper), ('N.value_cuboid', 'HB1', 'thoa_man', value_tamper)]
    for nid, gid, st, fn in negs:
        spec, plane = geoms[gid]
        cases[nid] = {**make(nid, spec, st, plane, 'area', tamper=fn), 'class': 'NEGATIVE', 'geometry': gid}
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'cases.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(cases, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
    print(len(cases), {c: sum(v['class'] == c for v in cases.values()) for c in ('CANON', 'VARIANT', 'NEGATIVE')})


if __name__ == '__main__':
    main()
