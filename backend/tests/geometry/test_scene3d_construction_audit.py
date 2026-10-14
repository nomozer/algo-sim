"""The construction audit (`scripts/audit_scene3d_construction.py`) must go red on injected scene faults."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from tests.geometry.test_two_line_plane_section import CASES

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('audit', ROOT/'scripts/audit_scene3d_construction.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
ROWS = json.loads((ROOT.parent/'docs/evaluation/geometry/runs/two-line-plane-section/visual/scenes.json')
                  .read_text(encoding='utf-8'))


def obj(scene, i):
    return next(o for o in scene['objects'] if o['id'] == i)


def fails(scene, case):
    a = audit.audit_scene(scene, case)
    return a['fails'] + audit.audit_steps(scene, a['section_segments'])[1]


def shift_h(s): obj(s, 'H')['xyz'][1] = '3/4'
def euclid_metric(s): s['chart_metric'] = [['1', '0', '0'], ['0', '1', '0'], ['0', '0', '1']]
def euclid_normal(s): obj(s, 'mp_td_q')['normal'] = ['1', '0', '1']
def section_vertex_off_edge(s): obj(s, 'td_q')['polygon'][2] = ['1/2', '1/4', '1/2']
def wrong_face_narration(s):
    e = next(e for e in s['events'] if e['action'] == 'EXTEND')
    e['learner_text'] = e['learner_text'].replace('mặt ', 'mặt X', 1)
def plane_before_h1(s):
    k = next(st['step_index'] for st in s['formation']['steps'] if 'H1' in st['visible_ids'])
    s['formation']['steps'][k - 1]['visible_ids'].append('mp_td_q')
def section_early(s):
    for st in s['formation']['steps'][:3]:
        st['visible_ids'].append('td_q')
def point_disappears(s): s['formation']['steps'][-1]['visible_ids'].remove('M')


@pytest.mark.parametrize('fault', [shift_h, euclid_metric, euclid_normal, section_vertex_off_edge, wrong_face_narration,
                                   plane_before_h1, section_early, point_disappears])
@pytest.mark.parametrize('row', [r for r in ROWS if r['served']], ids=lambda r: r['id'])
def test_audit_is_red_on_injected_fault(row, fault):
    case = CASES[row['corpus_index']]
    assert fails(row['scene'], case) == []
    bad = copy.deepcopy(row['scene'])
    fault(bad)
    assert fails(bad, case)
