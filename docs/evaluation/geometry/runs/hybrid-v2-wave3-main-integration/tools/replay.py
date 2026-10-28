"""Replay merged-main Wave 3 using the locked scorer; require a fresh output path."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

os.environ['ALLOW_LIVE_AI']='0'
sys.dont_write_bytecode=True
ap=argparse.ArgumentParser()
ap.add_argument('--root',default=str(Path(__file__).resolve().parents[6]))
ap.add_argument('--wave3-root')
ap.add_argument('--out',required=True)
args=ap.parse_args()
root=Path(args.root).resolve()
wave3=Path(args.wave3_root).resolve() if args.wave3_root else root/'docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3'
out=Path(args.out).resolve()
bp='docs/evaluation/geometry/runs/hybrid-v2-w3-f1-cross-sentence-plane-grounding'
if out.exists():
    raise SystemExit('Output exists; choose a new output path')
if out.is_relative_to(wave3) or out.is_relative_to(root/bp):
    raise SystemExit('Output must be outside the locked source evidence runs')
sys.path.insert(0,str(root/'backend'))
def offline(*a,**kw):
    raise RuntimeError('OFFLINE_ONLY: outbound socket blocked')
socket.socket.connect=offline
socket.create_connection=offline
spec=importlib.util.spec_from_file_location('integration_replay',root/bp/'tools/build_and_evaluate_w3_f1.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.WAVE3_WORKTREE=wave3
result=mod.evaluate_wave3_post_feedback_regression()
frozen=json.loads((root/bp/'results/wave3-post-feedback-regression.json').read_text(encoding='utf-8'))
assert result['cases']==frozen['cases'], 'per-case replay divergence'
assert result['post_feedback_regression_summary']==frozen['post_feedback_regression_summary']
assert result['transitions_from_historical_wave3']==frozen['transitions_from_historical_wave3']
summary=result['post_feedback_regression_summary']
assert (summary['positive_served_correct'],summary['negative_refused'],summary['negative_correct_reason'],summary['overall_wrong_served'])==(29,72,62,0)
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'classification':result['evidence_classification'],'cases_identical':True,'summary':summary,'replay_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},ensure_ascii=True))
