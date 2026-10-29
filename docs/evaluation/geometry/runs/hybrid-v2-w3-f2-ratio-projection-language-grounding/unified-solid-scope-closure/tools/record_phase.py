"""Append-only RED/GREEN receipt for the closure suite. Usage (worktree root):
python record_phase.py red|green <candidate log> [<baseline label>=<log> ...]"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

U = Path(__file__).resolve().parents[1]; ROOT = U.parents[5]
phase, log, *baselines = sys.argv[1:]
def digest(p): return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def git(*a): return subprocess.check_output(['git', *a], cwd=ROOT, text=True).strip()
def failed(text): return sorted(set(re.findall(r'^FAILED \S+::(\S+)', text, re.M)))
def summary(text): return re.findall(r'^(\d+ (?:failed|passed).*)$', text, re.M)[-1]
RUNS = ROOT / 'docs/evaluation/geometry/runs'
inputs = [RUNS / 'hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json',
          RUNS / 'typedfact-next-adapter3-simulation/corpus-dev.json',
          RUNS / 'simulation-coverage-visual-validation/corpus-dev.json', U / 'schema-field-inventory.json']
text = Path(log).read_text(encoding='utf-8-sig'); cand = failed(text)
out = U / f'{phase}.log'
with out.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
base = {}
for item in baselines:
    label, path = item.split('=', 1); t = Path(path).read_text(encoding='utf-8-sig')
    with (U / f'{phase}-{label}.log').open('x', encoding='utf-8', newline='\n') as f: f.write(t)
    base[label] = {'summary': summary(t), 'failed': failed(t), 'log': f'{phase}-{label}.log'}
receipt = {
    'phase': phase, 'head': git('rev-parse', 'HEAD'), 'product_dirty': git('status', '--porcelain=v1', '--', 'backend/app') != '',
    'classification': 'development security tests / POST_FEEDBACK_DEVELOPMENT_REGRESSION', 'live_provider_calls': 0,
    'summary': summary(text), 'failed': cand, 'baselines': base,
    'regressions': {label: sorted(set(cand) - set(b['failed'])) for label, b in base.items()},
    'test_file_sha256_lf': digest(ROOT / 'backend/tests/geometry/test_scope_census_closure.py'),
    'census_sha256_lf': digest(ROOT / 'backend/tests/geometry/scope_field_census.py'),
    'inputs_sha256_lf': {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs},
    'product_sha256_lf': {p: digest(ROOT / p) for p in ('backend/app/simulation/geometry_functions/typed_fact_next.py',
        'backend/app/simulation/geometry_functions/typed_fact_next_bridge.py', 'backend/app/ai/adapter3_simulation.py')},
    'log': out.name}
with (U / f'{phase}.json').open('x', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('phase', 'head', 'summary', 'regressions')}, ensure_ascii=False))
