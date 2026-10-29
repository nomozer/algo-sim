"""Append-only RED/GREEN receipt for the unified solid-scope tests: input/test hashes, pytest summary, failing ids.
Usage (from the worktree root): python record_phase.py red|green <pytest log>"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

U = Path(__file__).resolve().parents[1]; ROOT = U.parents[5]
phase, log = sys.argv[1], Path(sys.argv[2])
def digest(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def git(*a): return subprocess.check_output(['git', *a], cwd=ROOT, text=True).strip()
RUNS = ROOT / 'docs/evaluation/geometry/runs'
inputs = [RUNS / 'hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json',
          RUNS / 'hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/development.json',
          RUNS / 'typedfact-next-adapter3-simulation/corpus-dev.json',
          RUNS / 'simulation-coverage-visual-validation/corpus-dev.json']
text = log.read_text(encoding='utf-8-sig')
assert 'Traceback' not in text.split('short test summary')[0] or phase == 'red'
summary = re.findall(r'^(\d+ (?:failed|passed).*)$', text, re.M)[-1]
out = U / f'{phase}.log'
with out.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
receipt = {
    'phase': phase, 'head': git('rev-parse', 'HEAD'), 'dirty': git('status', '--porcelain=v1', '--', 'backend/app') != '',
    'classification': 'POST_FEEDBACK_DEVELOPMENT_REGRESSION (development security tests)', 'live_provider_calls': 0,
    'summary': summary, 'failed': sorted(re.findall(r'^FAILED \S+::(\S+)', text, re.M)),
    'test_file_sha256_lf': digest(ROOT / 'backend/tests/geometry/test_unified_solid_scope.py'),
    'product_sha256_lf': {p: digest(ROOT / p) for p in (
        'backend/app/simulation/geometry_functions/typed_fact_next.py',
        'backend/app/simulation/geometry_functions/typed_fact_next_bridge.py', 'backend/app/ai/adapter3_simulation.py')},
    'inputs_sha256_lf': {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs},
    'log': out.name, 'log_sha256_lf': digest(out)}
with (U / f'{phase}.json').open('x', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('phase', 'head', 'summary')}, ensure_ascii=False), len(receipt['failed']))
