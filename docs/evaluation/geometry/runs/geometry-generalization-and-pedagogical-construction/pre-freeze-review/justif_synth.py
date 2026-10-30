"""Synthetic: _ly_do_canh_thiet_dien does not check the step edge lies in the named face (relies on upstream face_index)."""
import sys; sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
from app.simulation.semantic_program import scene3d as S3
V = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]]
solid = {'id': 's', 'type': 'solid', 'vertices': V, 'faces': [[0,1,2,3],[0,3,7,4]], 'vertex_ids': list('ABCDEFGH')}
plane = {'id': 'p', 'type': 'plane3', 'point': [0,0,'1/2'], 'normal': [0,0,1], 'notation': '(α)'}
for fi in (1, 0):  # 1 = true face x=0 ; 0 = WRONG face (base, parallel to the cutting plane)
    sec = {'id': 'sec', 'type': 'section', 'depends': ['s', 'p'], 'steps': [{'a': [0,0,'1/2'], 'b': [0,1,'1/2'], 'face_index': fi}]}
    by_id = {'s': solid, 'p': plane, 'sec': sec, **{c: {'id': c, 'label': c} for c in 'ABCDEFGH'}}
    try:
        print(fi, S3._ly_do_canh_thiet_dien({'details': {'canh': 0}}, sec, by_id))
    except Exception as e:
        print(fi, 'EXC', type(e).__name__, e)
