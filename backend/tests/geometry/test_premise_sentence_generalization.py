"""W4: textbook premise-sentence forms read by the closed SG-3 clause grammar (preregistered metamorphic corpus).

A variant phrasing must give exactly the answer of its canonical twin; tamper negatives are never served; each grammar
extension is guarded by a behavioural mutant (the extension removed ⇒ its variants are refused again)."""
from copy import deepcopy
import hashlib
import inspect
import json
import re
import textwrap
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import registry as R

RUN = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/geometry-generalization-and-pedagogical-construction'
CASES = json.loads((RUN / 'dev-corpus/cases.json').read_text(encoding='utf-8'))
INPUT_SHA256 = '17b66cae38b99d3faee2da5fbb34d538d2b47d9e42ec6fd983726c2c90449992'  # preregistration.md (0bcfed14)


def run(cid):
    r = run_typed_fact_next_v2_route(deepcopy(CASES[cid]['payload']))
    return r.status, r.code, (r.answer_exact if r.status == 'SERVED' else None)


def names(cls):
    return sorted(k for k, c in CASES.items() if c['class'] == cls)


def test_frozen_corpus():
    assert hashlib.sha256((RUN / 'dev-corpus/cases.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest() == INPUT_SHA256


@pytest.mark.parametrize('cid', names('VARIANT'))
def test_variant_phrasing_gives_the_canonical_answer(cid):
    canon = run(CASES[cid]['oracle'])
    assert canon[0] == 'SERVED', canon
    assert run(cid) == canon


@pytest.mark.parametrize('cid', names('NEGATIVE'))
def test_tampered_premise_is_never_served(cid):
    status, code, answer = run(cid)
    assert status == 'REFUSED' and answer is None, (status, code)


@pytest.mark.parametrize('sentence,kinds', [
    ("Trong không gian, cho hình chóp tam giác S.DEF biết tam giác đáy DEF vuông tại D, cạnh bên SD vuông góc với "
     "mặt phẳng (DEF), với độ dài DE = 6, cạnh DF = 8, chiều cao SD = 12.", ['khoi', 'day', 'vuong', 'doan', 'doan', 'doan']),
    ("Xét hình chóp tam giác S.DEF thỏa mãn đáy DEF là tam giác vuông tại D, thỏa mãn SD ⊥ (DEF), thỏa mãn DE = 6, "
     "biết DF = 8, và cạnh SD = 12.", ['khoi', 'day', 'vuong', 'doan', 'doan', 'doan']),
    ("Cho hình chóp S.DEF với mặt đáy DEF là tam giác vuông ở D, đường thẳng SD vuông góc với mặt phẳng (DEF), "
     "có số đo DE = 6, đoạn DF = 8, độ dài SD = 12.", ['khoi', 'day', 'vuong', 'doan', 'doan', 'doan']),
    ("Xét hình lập phương DEFG.D'E'F'G' biết mặt đáy DEFG là hình vuông có cạnh bằng 8, cạnh bên DD' = 8.", ['khoi', 'day', 'doan']),
    ("Trong không gian, cho hình hộp chữ nhật DEFG.D'E'F'G' với tứ giác đáy DEFG là hình chữ nhật, có số đo DE = 6.",
     ['khoi', 'day', 'doan']),
])
def test_textbook_premise_sentence_parses_completely(sentence, kinds):
    assert [k for k, _m in R._phan_tich_cau(sentence)] == kinds


@pytest.mark.parametrize('sentence', [
    "Xét hình chóp S.DEF thỏa mãn DE = 6 hoặc DE = 7.",            # a number in an unread clause stays unbound
    "Xét hình chóp S.DEF giả sử DE = 6.",
    "Xét hình chóp S.DEF với chiều cao bằng 12 của mặt bên SDE.",
])
def test_number_carrying_unread_clauses_still_leave_the_sentence_unparsed(sentence):
    assert R._phan_tich_cau(sentence) is None


# Behavioural mutants: each removes ONE grammar extension; the variants that need it must be refused again.
MUTANTS = {
    'no_space_openers': ('_C_NOI', r'''\s+(?=biết\s|th[ỏo]a\s+mãn\s|với\s+(?:(?:mặt|tứ\s+giác|tam\s+giác)\s+)?đáy(?!\w)|có\s|''', r'''\s+(?=có\s|''',
                         'TP1.thoa_man.area'),
    'no_space_lead': ('_C_DAU', r'''(?:trong\s+không\s+gian\s*,\s*)?''', '', 'TP1.tg_day.area'),
    'no_thoa_man': ('_C_DAU', r'''(?:(?:biết(?:\s+rằng)?|th[ỏo]a\s+mãn)\s+)?''', r'''(?:biết\s+(?:rằng\s+)?)?''', 'QP1.thoa_man.area'),
    'no_so_do': ('_C_DOAN', r'''|số\s+đo)''', ')', 'TP1.voi_so_do.area'),
    'no_o_synonym': ('_C_DAY', r'''(?:tại|ở)''', 'tại', 'RP1.voi_so_do.area'),
    'no_base_prefix': ('_C_DAY', r'''(?:(?:có|với)\s+)?(?:(?:mặt|tứ\s+giác|tam\s+giác)\s+)?đáy''', r'''(?:có\s+)?(?:mặt\s+)?đáy''',
                       'RP1.tg_day.area'),
}


@pytest.mark.parametrize('mutant', sorted(MUTANTS))
def test_each_grammar_extension_is_load_bearing(monkeypatch, mutant):
    attr, old, new, cid = MUTANTS[mutant]
    assert run(cid)[0] == 'SERVED'
    rx = getattr(R, attr)
    assert rx.pattern.count(old) >= 1, (mutant, 'anchor missing')
    monkeypatch.setattr(R, attr, re.compile(rx.pattern.replace(old, new), rx.flags))
    assert run(cid)[0] == 'REFUSED', mutant


# Amendment (pre-freeze review B1): a role prefix is a claim. Negatives whose payload AGREES with the wrong reading.
ROLE = json.loads((RUN / 'dev-corpus/role-claims.json').read_text(encoding='utf-8'))
ROLE_SHA256 = '24a10004fca5d42134471157ba2726222842c58dfabb51db2e35fd83d5776527'


def run_role(cid):
    r = run_typed_fact_next_v2_route(deepcopy(ROLE[cid]['payload']))
    return r.status, r.code, (r.answer_exact if r.status == 'SERVED' else None)


def test_role_claim_corpus_frozen():
    assert hashlib.sha256((RUN / 'dev-corpus/role-claims.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest() == ROLE_SHA256


@pytest.mark.parametrize('cid', sorted(k for k, c in ROLE.items() if c['class'] == 'NEGATIVE'))
def test_unproved_role_claim_is_never_served(cid):
    status, code, answer = run_role(cid)
    assert status == 'REFUSED' and answer is None, (status, code)


def test_proved_height_gives_the_canonical_answer():
    assert run_role('RC.height_proved') == run(ROLE['RC.height_proved']['oracle'])


def test_role_check_is_load_bearing(monkeypatch):
    monkeypatch.setattr(R, '_vai_doan_ok', lambda m, khoi, calls: True)
    assert run_role('RC.height_not_perpendicular_pyr3')[0] == 'SERVED'      # the B1 defect returns without the check


def test_right_angle_vertex_reads_o_as_tai(monkeypatch):
    # The base clause binds its right-angle vertex from "tại|ở"; without "ở" a parsed "vuông ở D" binds no vertex.
    cid = 'RP1.voi_so_do.area'
    assert run(cid)[0] == 'SERVED'
    src = textwrap.dedent(inspect.getsource(R._cau_tien_de_dong_hop_le))
    old = 'rf"(?:tại|ở)\\s+(?P<v>{_L1})'
    assert src.count(old) == 1
    ns = dict(vars(R))
    exec(compile(src.replace(old, 'rf"tại\\s+(?P<v>{_L1})'), '<mutant>', 'exec'), ns)
    monkeypatch.setattr(R, '_cau_tien_de_dong_hop_le', ns['_cau_tien_de_dong_hop_le'])
    assert run(cid)[0] == 'REFUSED'
