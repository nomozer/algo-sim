"""Independent Fraction/Gram oracle. Reuse previous independent figure definitions; no app imports.
Writes corpus once; never overwrites registered inputs or labels.
"""
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

RUN = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('previous_oracle', RUN.parent / 'goal-directed-function-discovery/oracle.py')
O = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O)


def make():
    positive, discovery = [], []
    for family, defs, facts, pts, gram, desc in (
        ('pyramid', O.PYR_TEXT, O.PYR_FACTS, O.PYR, O.I3, ['S', 'C']),
        ('cube', O.CUBE_TEXT, O.CUBE_FACTS, O.CUBE, O.I3, ["C'", "D'"]),
        ('cuboid', O.CUBOID_TEXT, O.CUBOID_FACTS, O.CUBOID, O.I3, ["A'", "C'"]),
        ('prism', O.PRISM_TEXT, O.PRISM_FACTS, O.PRISM, O.PRISM_G, ["B'", "C'"]),
    ):
        for target in ['A', 'B']:
            quote = f"Tính độ dài đoạn nối trung điểm của {''.join(desc)} với {target}."
            x = O.mid(*(pts[p] for p in desc))
            w = O.sub(x, pts[target])
            positive.append(dict(id=f'{family}-midpoint-{target}', text=' '.join([*defs, quote]),
                payload={'facts': deepcopy(facts) + [O.f('q', 'question', quote, role='question', quantity='length',
                    point_kind='midpoint', points=desc, points_b=[target])]}, expected_squared={'q':str(O.g(w,w,gram))}))
    for target in ['A', 'D']:
        quote = f'Tính độ dài đoạn nối trọng tâm của tam giác SBC với {target}.'
        x = O.centroid(*(O.PYR[p] for p in 'SBC'))
        w = O.sub(x, O.PYR[target])
        discovery.append(dict(id=f'centroid-{target}', text=' '.join([*O.PYR_TEXT,quote]),
            payload={'facts':deepcopy(O.PYR_FACTS) + [O.f('q','question',quote,role='question',quantity='length',
                point_kind='centroid',points=list('SBC'),points_b=[target])]},expected_squared={'q':str(O.g(w,w,O.I3))}))
    negative=[]
    def neg(name, codes, edit):
        c=deepcopy(positive[0]); c['id']=name; c.pop('expected_squared'); c['expected_codes']=codes
        edit(c,c['payload']['facts'][-1]); negative.append(c)
    neg('ambiguous',['AMBIGUOUS_FACT'],lambda c,f:f.update(ambiguous=True))
    neg('conditional',['CONDITIONAL_CLAUSE'],lambda c,f:f.update(role='condition'))
    neg('prove',['GOAL_CLAUSE_NOT_PREMISE'],lambda c,f:f.update(role='prove'))
    neg('negated',['NEGATED_CLAUSE'],lambda c,f:f.update(negated=True))
    neg('missing-target',['FACT_INCOMPLETE'],lambda c,f:f.update(points_b=[]))
    neg('extra-target',['FACT_INCOMPLETE'],lambda c,f:f.update(points_b=['A','B']))
    neg('duplicate-descriptor',['FACT_INCOMPLETE'],lambda c,f:f.update(points=['S','S']))
    neg('wrong-source-target',['SOURCE_OBJECT_MISMATCH'],lambda c,f:f.update(points_b=['D']))
    def change(c,f,old,new):
        c['text']=c['text'].replace(old,new); f['quotes']=[q.replace(old,new) for q in f['quotes']]
    neg('squared-request',['NOT_ASKED_IN_SOURCE','SOURCE_OBJECT_MISMATCH'],lambda c,f:change(c,f,'độ dài đoạn','bình phương độ dài đoạn'))
    neg('unread-second-ask',['QUESTION_CONTEXT_UNSUPPORTED','NOT_ASKED_IN_SOURCE'],lambda c,f:change(c,f,'với A.', 'với A. Tính độ dài đoạn nối trung điểm của SC với B.'))
    neg('contradictory-length',['INCONSISTENT_CONSTRAINTS'],lambda c,f:(c.update(text=c['text']+' SA = 4.'),c['payload']['facts'].insert(4,O.f('conflict','length','SA = 4.',points=['S','A'],measure='segment',value='4'))))
    return dict(run='generalized-goal-entry', status='DEVELOPMENT_NOT_HELD_OUT',positive=positive,negative=negative,discovery=discovery)


if __name__=='__main__':
    out=RUN/'corpus.json'
    if out.exists(): raise SystemExit('refusing to overwrite registered corpus')
    out.write_text(json.dumps(make(),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print({k:len(v) for k,v in make().items() if isinstance(v,list)})
