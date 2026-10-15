"""Offline real-route scenes/receipts for the locked result-binding development corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.ai.function_route import run_fact_route


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        parser.error('refusing to overwrite measured output')
    root=Path(__file__).resolve().parents[2]
    source=root/'docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/next-slice-corpus.json'
    corpus=json.loads(source.read_text(encoding='utf-8'))
    receipts,scenes=[],[]
    for group in ('positive','negative'):
        for case in corpus[group]:
            result=run_fact_route(case['text'],case['payload'])
            receipts.append({'id':case['id'],'status':result.status,'code':result.code,
                             'answers':result.answers,'kernel_check':result.kernel_check,
                             'functions':[c['fn'] for c in result.calls], 'planner':result.planner,
                             'engine_trace':result.trace})
            if case['id'] in ('derived-line-pyramid','derived-line-cuboid','derived-line-prism','parallel-planes'):
                scenes.append({'id':case['id'],'served':result.status=='SERVED','code':result.code,
                               'reason':result.reason,'kind':'line','target':'gt_g','foot':'H',
                               'scene':result.scene3d,'answers':result.answers,'text':case['text']})
    args.out.mkdir(parents=True)
    for name,data in (('scenes.json',scenes),('corpus-results.json',receipts)):
        (args.out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.out/'manifest.json').write_text(json.dumps({'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                  'measurement':'OFFLINE_REAL_FACT_ROUTE; development, NOT_HELD_OUT; no direct-IR shortcut',
                  'live_calls':0,'positive':6,'negative':12,'exported_scenes':len(scenes)},indent=2)+'\n',encoding='utf-8')
    print(f'Exported {len(receipts)} real-route outcomes and {len(scenes)} browser fixtures; live calls 0.')


if __name__=='__main__':
    main()
