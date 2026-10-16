"""Generalized goal entry replay. Reuses prior arm/classification tooling; no live calls or overwrite."""
import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import measure_function_discovery as previous

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'docs/evaluation/geometry/runs/generalized-goal-entry'
original_variant = previous.apply_variant


def variant(name):
    if name != 'no-length':
        return original_variant(name)
    from dataclasses import replace
    from app.simulation.geometry_functions.registry import REGISTRY
    REGISTRY['ask_length'] = replace(REGISTRY['ask_length'], planning_extra=())


def bundle(out):
    with TemporaryDirectory() as td:
        p=Path(td)/'old.json'; previous.bundle(p)
        data=json.loads(p.read_text(encoding='utf-8'))
    corpus=json.loads((RUN/'corpus.json').read_text(encoding='utf-8'))
    for split in ('positive','negative','discovery'):
        for c in corpus[split]:
            data['rows'].append(dict(corpus='goal/'+split,id=c['id'],text=c['text'],facts=c['payload']['facts'],
                expect={k:c[k] for k in ('expected_squared','expected_codes') if k in c}))
    previous._write(out,data)


def scenes(out):
    sys.path.insert(0,str(ROOT/'backend'))
    from app.ai.function_route import run_fact_route
    rows=[]
    corpus=json.loads((RUN/'corpus.json').read_text(encoding='utf-8'))
    for c in (corpus['positive'][0],corpus['positive'][6],corpus['negative'][7]):
        r=run_fact_route(c['text'],c['payload'])
        solid=next((o['id'] for o in (r.scene3d or {}).get('objects',[]) if o['type']=='solid'),None)
        envelope=None
        if r.status=='SERVED':
            # envelope field, as pipeline_adapter writes it — not the prompt-domain keyword the domain-string guard watches
            envelope=dict(status='ok',simulation_id='generic.semantic_program',**{'domain':'generic'},visual_mode='2d',
                title=c['text'],description=None,notes=None,scene3d=r.scene3d,
                config=dict(spec_version='1',title=c['text'],frames=[dict(step_index=0,narration=c['text'],objects=[])],
                    view_steps=[dict(view_index=0,frame_lo=0,frame_hi=0,narration=c['text'])],grouping_level='step',
                    presentation_overflow=False,execution_truncated=False))
        rows.append(dict(id=c['id'],served=r.status=='SERVED',code=r.code,reason=r.reason,kind='descriptor',
            target=solid,foot='M',scene=r.scene3d,answers=r.answers,text=c['text'],envelope=envelope))
    previous._write(out/'scenes.json',rows)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('cmd',choices=['bundle','arm','compare','scenes'])
    ap.add_argument('--out',type=Path,required=True); ap.add_argument('--bundle',type=Path)
    ap.add_argument('--code-root',type=Path,default=ROOT); ap.add_argument('--label',default='NEW')
    ap.add_argument('--registry',default='production'); ap.add_argument('--arms',type=Path,nargs='+')
    a=ap.parse_args(); previous.apply_variant=variant
    if a.cmd=='bundle': bundle(a.out.resolve())
    elif a.cmd=='arm': previous.arm(a.code_root.resolve(),a.bundle.resolve(),a.label,a.out.resolve(),a.registry)
    elif a.cmd=='compare': previous.compare(a.bundle.resolve(),[p.resolve() for p in a.arms],a.out.resolve())
    else: scenes(a.out.resolve())
