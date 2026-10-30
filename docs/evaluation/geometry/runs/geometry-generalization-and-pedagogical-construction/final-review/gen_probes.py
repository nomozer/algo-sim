"""Generate NEW adversarial payloads (not from the dev corpus text) for W4 SG-3 grammar + role check."""
import json, copy, sys
CASES = json.load(open(sys.argv[1], encoding='utf-8'))
OUT = sys.argv[2]
probes, labels = {}, {}

def mk(pid, base, text, prem=None, label='NEG', note=''):
    """prem: full list of (kind, args, quote) or None to keep base premises (quotes must still be substrings)."""
    p = copy.deepcopy(CASES[base]['payload'])
    p['problem_text'] = text
    if prem is not None:
        p['premises'] = [{'kind': k, 'args': a, 'quote': q, 'solid_id': 's1'} for k, a, q in prem]
    import re as _re
    for so in p['solids']:
        i = text.find(so['notation']); st = max((m.start() for m in _re.finditer(r'(?:Cho|Xét|cho|xét)\s', text[:i])), default=0)
        q = text[st:i + len(so['notation'])]; so['quote'] = q
        for g in p['simulation_goals']:
            if g.get('target_solid_id') == so['solid_id']: g['quote'] = q
    probes[pid] = p; labels[pid] = {'label': label, 'base': base, 'note': note}

TAIL_TP1 = " Lấy điểm K trên cạnh SE sao cho SK = 2/5 SE. Gọi (α) là mặt phẳng qua K, song song với hai đường thẳng DE và DF. Hãy tính diện tích thiết diện tạo bởi mặt phẳng (α) với hình chóp S.DEF."
DIV_TP1 = ('divide_segment', {'point': 'K', 'ratio': '2/5', 'segment': ['S', 'E']}, 'Lấy điểm K trên cạnh SE sao cho SK = 2/5 SE')
def tp1(pid, head, q, label='NEG', note='', vals=('6', '8', '12'), right='D', seg3=('S', 'D')):
    """q = quotes for (right, perp, DE, DF, SD)."""
    prem = [('right_angle', {'right_at': right, 'vertices': ['D', 'E', 'F']}, q[0]),
            ('perpendicular_line_plane', {'line': ['S', 'D'], 'plane': ['D', 'E', 'F']}, q[1]),
            ('segment_length', {'segment': ['D', 'E'], 'value': vals[0]}, q[2]),
            ('segment_length', {'segment': ['D', 'F'], 'value': vals[1]}, q[3]),
            ('segment_length', {'segment': list(seg3), 'value': vals[2]}, q[4]), DIV_TP1]
    mk(pid, 'TP1.canon.area', head + TAIL_TP1, prem, label, note)

# --- A: connectors that might swallow conditions / negations / disjunctions
tp1('A1.khi', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8 thỏa mãn SD = 12 khi K là trung điểm SE.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'thỏa mãn SD = 12'], note='trailing conditional after thỏa mãn')
tp1('A2.neu', "Trong không gian, nếu hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'và SD = 12'], note='Trong không gian, nếu ...')
tp1('A3.khong_thoa', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), không thỏa mãn DE = 6, DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'thỏa mãn DE = 6', 'DF = 8', 'và SD = 12'], note='negated thỏa mãn')
tp1('A4.chua_biet', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), chưa biết DE = 6, DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'và SD = 12'], note='chưa biết')
tp1('A5.khong_biet', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), DF = 8, SD = 12 và không biết DE = 6.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'SD = 12'], note='không biết')
tp1('A6.gia_su_thoa', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), giả sử thỏa mãn DE = 6, DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'thỏa mãn DE = 6', 'DF = 8', 'và SD = 12'], note='giả sử thỏa mãn')
tp1('A7.biet_neu', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết rằng nếu DE = 6 thì DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'DE = 6', 'DF = 8', 'và SD = 12'], note='biết rằng nếu ... thì')
tp1('A8.thoa_hoac', "Xét hình chóp S.DEF thỏa mãn đáy DEF là tam giác vuông tại D, thỏa mãn SD ⊥ (DEF), thỏa mãn DE = 6 hoặc DE = 7, biết DF = 8, và SD = 12.",
    ['thỏa mãn đáy DEF là tam giác vuông tại D', 'thỏa mãn SD ⊥ (DEF)', 'thỏa mãn DE = 6', 'biết DF = 8', 'và SD = 12'], note='disjunction on DE')
tp1('A9.thoa_xap_xi', "Xét hình chóp S.DEF thỏa mãn đáy DEF là tam giác vuông tại D, thỏa mãn SD ⊥ (DEF), thỏa mãn DE xấp xỉ 6, biết DF = 8, và SD = 12.",
    ['thỏa mãn đáy DEF là tam giác vuông tại D', 'thỏa mãn SD ⊥ (DEF)', 'DE xấp xỉ 6', 'biết DF = 8', 'và SD = 12'], note='approximate')
tp1('A10.voi_day_khac', "Cho hình chóp S.DEF với đáy DEF là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12 với đáy của hình chóp khác.",
    ['với đáy DEF là tam giác vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='trailing reattribution')
tp1('A11.trong_kg_mid', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, trong không gian, DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'và SD = 12'], label='POS', note='harmless mid-sentence prefix')
tp1('A12.thoa_man_sau_so', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), DE = 6 thỏa mãn DF = 8 và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'DE = 6', 'DF = 8', 'SD = 12'], label='POS', note='odd but numerically consistent')
tp1('A13.biet_gap', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), DF = 8, SD = 12 biết DE = 6 lần DK.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'DE = 6', 'DF = 8', 'SD = 12'], note='DE = 6 lần DK')
tp1('A14.thoa_man_value_wrong', "Xét hình chóp S.DEF thỏa mãn đáy DEF là tam giác vuông tại D, thỏa mãn SD ⊥ (DEF), thỏa mãn DE = 6, biết DF = 8, và SD = 12.",
    ['thỏa mãn đáy DEF là tam giác vuông tại D', 'thỏa mãn SD ⊥ (DEF)', 'thỏa mãn DE = 6', 'biết DF = 8', 'và SD = 12'], vals=('6', '8', '13'), note='payload SD=13, text 12')
tp1('A15.biet_sau', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D biết cạnh bên SD vuông góc với mặt phẳng (DEF) biết DE = 6 biết DF = 8 biết SD = 12 sau khi kéo dài.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'biết DF = 8', 'biết SD = 12'], note='trailing modifier')
tp1('A16.thoa_man_doi', "Xét hình chóp S.DEF thỏa mãn đáy DEF là tam giác vuông tại D, thỏa mãn SD ⊥ (DEF), thỏa mãn DE = 6, biết DF = 8, và SD = 12 thỏa mãn đổi vai trò E và F.",
    ['thỏa mãn đáy DEF là tam giác vuông tại D', 'thỏa mãn SD ⊥ (DEF)', 'thỏa mãn DE = 6', 'biết DF = 8', 'và SD = 12'], note='trailing number-free opaque after thỏa mãn')

# --- B: role prefix claims
tp1('B1.chieu_cao_DE', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết chiều cao DE = 6, DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'chiều cao DE = 6', 'DF = 8', 'và SD = 12'], note='height role on base edge')
tp1('B2.canh_ben_DF', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, cạnh bên DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'cạnh bên DF = 8', 'và SD = 12'], note='lateral role on base edge')
tp1('B3.chieu_cao_SE', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và chiều cao SE = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'chiều cao SE = 12'], seg3=('S', 'E'), note='height role on slanted lateral edge')
tp1('B4.CHIEU_CAO_upper', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và Chiều  Cao SE = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'Chiều  Cao SE = 12'], seg3=('S', 'E'), note='case/space variant height on SE')
tp1('B5.duong_cao_SE', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và đường cao SE = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'đường cao SE = 12'], seg3=('S', 'E'), note='đường cao role (not in _C_DOAN sv)')
tp1('B6.chieu_cao_ES', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và chiều cao DS = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'chiều cao DS = 12'], seg3=('D', 'S'), label='POS', note='height reversed label, true')
tp1('B7.chieu_cao_chain', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và chiều cao SD = SE = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'chiều cao SD = SE = 12'], note='chain equality SD=SE=12 (false geometry)')
tp1('B8.do_dai_chieu_cao', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và độ dài chiều cao SE = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'độ dài chiều cao SE = 12'], seg3=('S', 'E'), note='độ dài + chiều cao on SE')
tp1('B9.chieu_cao_hinh_chop', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và chiều cao của hình chóp SE = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'chiều cao của hình chóp SE = 12'], seg3=('S', 'E'), note='chiều cao của hình chóp SE')
tp1('B10.canh_day_SD', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và cạnh đáy SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'cạnh đáy SD = 12'], note='base-edge role on lateral edge')

# --- C: day / right-angle vertex / qualifier
tp1('C1.tg_day_vuong_o_E', "Cho hình chóp S.DEF biết tam giác đáy DEF vuông ở E, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['biết tam giác đáy DEF vuông ở E', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='vuông ở E vs payload D')
tp1('C2.tu_giac_day', "Cho hình chóp S.DEF với tứ giác đáy DEF là tam giác vuông tại D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với tứ giác đáy DEF là tam giác vuông tại D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='tứ giác đáy on triangle')
tp1('C3.vuong_can_o', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông cân ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông cân ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='vuông cân but DE != DF')
tp1('C4.can_o_vuong_tai', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác cân ở E vuông tại D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác cân ở E vuông tại D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='cân ở E + vuông tại D (false claim)')
tp1('C5.day_khong_vuong', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác không vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác không vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='negated right angle')
tp1('C6.voi_day_unlabelled', "Cho hình chóp S.DEF với đáy là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với đáy là tam giác vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], label='POS', note='unlabelled base')
tp1('C7.vuong_o_label_of_other', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở S, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông ở S', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='vertex not in base')
tp1('C8.tg_vuong_o_tai', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở trung điểm của EF, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông ở trung điểm của EF', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='ở + phrase')

# --- D: số đo / units / angles
tp1('D1.so_do_goc', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo góc DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo góc DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='số đo góc')
tp1('D2.so_do_do', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6 độ, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='degrees unit')
tp1('D3.so_do_ratio', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6 DF, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], note='DE = 6 DF')
tp1('D4.so_do_frac', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6/1, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6/1', 'đoạn DF = 8', 'độ dài SD = 12'], label='POS', note='6/1')

# --- E: prism: role check, cube, oblique wording
TAIL_RP1 = " Lấy điểm K trên cạnh DE sao cho DK = 1/3 DE. Gọi (γ) là mặt phẳng qua K, song song với hai đường thẳng DD' và DF. Hãy tính diện tích thiết diện tạo bởi mặt phẳng (γ) với hình lăng trụ DEF.D'E'F'."
DIV_RP1 = ('divide_segment', {'point': 'K', 'ratio': '1/3', 'segment': ['D', 'E']}, 'Lấy điểm K trên cạnh DE sao cho DK = 1/3 DE')
def rp1(pid, head, q, label='NEG', note='', seg3=('D', "D'"), vals=('5', '12', '9'), solidq=None):
    prem = [('right_prism', {'base': ['D', 'E', 'F'], 'top': ["D'", "E'", "F'"]}, q[0]),
            ('right_angle', {'right_at': 'D', 'vertices': ['D', 'E', 'F']}, q[1]),
            ('segment_length', {'segment': ['D', 'E'], 'value': vals[0]}, q[2]),
            ('segment_length', {'segment': ['D', 'F'], 'value': vals[1]}, q[3]),
            ('segment_length', {'segment': list(seg3), 'value': vals[2]}, q[4]), DIV_RP1]
    mk(pid, 'RP1.canon.area', head + TAIL_RP1, prem, label, note)

rp1('E1.cheo_chieu_cao', "Cho hình lăng trụ DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, chiều cao DD' = 9.",
    ["Cho hình lăng trụ DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "chiều cao DD' = 9"], note='prism not stated right; payload right')
rp1('E2.chieu_cao_DE_prime', "Cho hình lăng trụ đứng DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, chiều cao DE' = 9.",
    ["Cho hình lăng trụ đứng DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "chiều cao DE' = 9"], seg3=('D', "E'"), note="height on diagonal DE'")
rp1('E3.canh_ben_DE_prime', "Cho hình lăng trụ đứng DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, cạnh bên DE' = 9.",
    ["Cho hình lăng trụ đứng DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "cạnh bên DE' = 9"], seg3=('D', "E'"), note="lateral on face diagonal")
rp1('E4.canh_ben_FF', "Cho hình lăng trụ đứng DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, cạnh bên F'F = 9.",
    ["Cho hình lăng trụ đứng DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "cạnh bên F'F = 9"], seg3=("F'", 'F'), label='POS', note="true lateral FF'")
rp1('E5.chieu_cao_DpEp', "Cho hình lăng trụ đứng DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, chiều cao D'E' = 9.",
    ["Cho hình lăng trụ đứng DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "chiều cao D'E' = 9"], seg3=("D'", "E'"), note="height on top edge")
rp1('E6.tg_day_tu_giac', "Cho hình lăng trụ đứng DEF.D'E'F' biết tứ giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, chiều cao DD' = 9.",
    ["Cho hình lăng trụ đứng DEF.D'E'F'", 'biết tứ giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "chiều cao DD' = 9"], note="tứ giác đáy on triangle")
rp1('E7.lap_phuong_tam_giac', "Cho hình lăng trụ tứ giác đứng DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, chiều cao DD' = 9.",
    ["Cho hình lăng trụ tứ giác đứng DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "chiều cao DD' = 9"], note="qualifier tứ giác")
rp1('E8.chieu_cao_value_wrong', "Cho hình lăng trụ đứng DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, chiều cao DD' = 9.",
    ["Cho hình lăng trụ đứng DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "chiều cao DD' = 9"], vals=('5', '12', '10'), note="payload 10 text 9")

# --- F: cube with new forms
TAIL_CB1 = " Lấy điểm K trên cạnh DE sao cho DK = 3/8 DE. Gọi (α) là mặt phẳng qua K, song song với hai đường thẳng DD' và DG. Hãy tính diện tích thiết diện tạo bởi mặt phẳng (α) với hình lăng trụ DEFG.D'E'F'G'."
DIV_CB1 = ('divide_segment', {'point': 'K', 'ratio': '3/8', 'segment': ['D', 'E']}, 'Lấy điểm K trên cạnh DE sao cho DK = 3/8 DE')
def cb1(pid, head, q, label='NEG', note='', side='8', lat='8'):
    prem = [('right_prism', {'base': ['D', 'E', 'F', 'G'], 'top': ["D'", "E'", "F'", "G'"]}, q[0]),
            ('base_is_square', {'side': side, 'vertices': ['D', 'E', 'F', 'G']}, q[1]),
            ('segment_length', {'segment': ['D', "D'"], 'value': lat}, q[2]), DIV_CB1]
    mk(pid, 'CB1.canon.area', head + TAIL_CB1, prem, label, note)
cb1('F1.lp_tg_day', "Trong không gian, cho hình lập phương DEFG.D'E'F'G' với tam giác đáy DEFG là hình vuông cạnh 8, cạnh bên DD' = 8.",
    ["cho hình lập phương DEFG.D'E'F'G'", 'với tam giác đáy DEFG là hình vuông cạnh 8', "cạnh bên DD' = 8"], note='tam giác đáy DEFG (count mismatch)')
cb1('F2.lp_side_wrong', "Trong không gian, cho hình lập phương DEFG.D'E'F'G' thỏa mãn mặt đáy DEFG là hình vuông cạnh 8, cạnh bên DD' = 8.",
    ["cho hình lập phương DEFG.D'E'F'G'", 'thỏa mãn mặt đáy DEFG là hình vuông cạnh 8', "cạnh bên DD' = 8"], side='9', lat='9', note='payload 9 text 8')
cb1('F3.lp_side_ok', "Trong không gian, cho hình lập phương DEFG.D'E'F'G' thỏa mãn mặt đáy DEFG là hình vuông cạnh 8, cạnh bên DD' = 8.",
    ["cho hình lập phương DEFG.D'E'F'G'", 'thỏa mãn mặt đáy DEFG là hình vuông cạnh 8', "cạnh bên DD' = 8"], label='POS', note='consistent')
cb1('F4.lp_canh_ben_DE', "Cho hình lập phương DEFG.D'E'F'G' biết mặt đáy DEFG là hình vuông cạnh 8, cạnh bên DE = 8.",
    ["Cho hình lập phương DEFG.D'E'F'G'", 'biết mặt đáy DEFG là hình vuông cạnh 8', "cạnh bên DE = 8"], note='cạnh bên on base edge')
cb1('F5.lp_day_other', "Cho hình lập phương DEFG.D'E'F'G' biết mặt đáy D'E'F'G' là hình vuông cạnh 8, cạnh bên DD' = 8.",
    ["Cho hình lập phương DEFG.D'E'F'G'", "biết mặt đáy D'E'F'G' là hình vuông cạnh 8", "cạnh bên DD' = 8"], label='POS?', note='top face called đáy; values consistent')

json.dump(probes, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(labels, open(OUT.replace('.json', '-labels.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(probes))
json.dump(probes, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(labels, open(OUT.replace('.json', '-labels.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
probes.clear(); labels.clear()
tp1('K1.canon', "Xét hình chóp S.DEF có đáy DEF là tam giác vuông tại D, cạnh bên SD vuông góc với mặt phẳng (DEF), biết DE = 6, DF = 8, và SD = 12.",
    ['có đáy DEF là tam giác vuông tại D', 'cạnh bên SD vuông góc với mặt phẳng (DEF)', 'biết DE = 6', 'DF = 8', 'và SD = 12'], label='POS')
tp1('K2.voi_so_do', "Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.",
    ['với mặt đáy DEF là tam giác vuông ở D', 'đường thẳng SD vuông góc với mặt phẳng (DEF)', 'có số đo DE = 6', 'đoạn DF = 8', 'độ dài SD = 12'], label='POS')
rp1('K3.rp1_tg_day', "Cho hình lăng trụ đứng DEF.D'E'F' biết tam giác đáy DEF vuông tại D, với độ dài DE = 5, cạnh DF = 12, chiều cao DD' = 9.",
    ["Cho hình lăng trụ đứng DEF.D'E'F'", 'biết tam giác đáy DEF vuông tại D', 'với độ dài DE = 5', 'cạnh DF = 12', "chiều cao DD' = 9"], label='POS')
cb1('K4.cb1_voi', "Cho khối lập phương DEFG.D'E'F'G' với đáy DEFG là hình vuông cạnh bằng 8, cạnh bên DD' = 8.",
    ["Cho khối lập phương DEFG.D'E'F'G'", 'với đáy DEFG là hình vuông cạnh bằng 8', "cạnh bên DD' = 8"], label='POS')
json.dump(probes, open(OUT.replace('.json', '-ctl.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
