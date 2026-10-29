"""Reviewer-3 spot mutations on a scratch copy (never the worktree). python mutate.py <scratch_mut_dir>"""
import shutil, subprocess, sys, os
from pathlib import Path

MUT = Path(sys.argv[1]); BE = MUT / 'backend'; ORIG = MUT / 'backend_orig'
TFN = 'app/simulation/geometry_functions/typed_fact_next.py'
BR = 'app/simulation/geometry_functions/typed_fact_next_bridge.py'
MUTANTS = {
    'remove_S7_unqualified_foreign_label': (TFN,
        "            if ns is None and base in solids and label in owners_of and base not in owners_of[label] \\\n                    and label not in built:",
        "            if False:"),
    'remove_S7_and_bridge_S8': (None, None, None),     # composite, below
    'remove_S4_DA_parent_on_other_kinds': (TFN,
        "        if g.kind != \"construct_derived_solid\" and g.parent_solid_id is not None:",
        "        if False:"),
    'remove_F7_residual_ancestry': (TFN,
        "            if mg.kind == \"residual_volume\" and mg.cut_solid_id in parents:",
        "            if False:"),
    'remove_S11_operand_type': (TFN,
        "            if v is not None and not (isinstance(v, str) or",
        "            if False and not (isinstance(v, str) or"),
    'remove_S10_unknown_token': (TFN,
        "            if not _QUALIFIED_REF_RE.match(token) or parse_qualified_ref(token)[1] not in {*owners_of, *built}:",
        "            if False:"),
}
COMPOSITE = {'remove_S7_and_bridge_S8': [
    MUTANTS['remove_S7_unqualified_foreign_label'],
    (BR, "            if ns is None and owners.get(label) and base not in owners[label]:", "            if False:")]}
TESTS = ['tests/geometry/test_scope_census_closure.py', 'tests/geometry/test_unified_solid_scope.py']


def apply(edits):
    for f, old, new in edits:
        p = BE / f; s = p.read_text(encoding='utf-8')
        assert s.count(old) == 1, (f, old[:60], s.count(old))
        p.write_text(s.replace(old, new), encoding='utf-8')


def restore():
    for f in (TFN, BR):
        shutil.copyfile(ORIG / f, BE / f)


env = {**os.environ, 'ALLOW_LIVE_AI': '0', 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}
for name, m in MUTANTS.items():
    restore()
    apply(COMPOSITE.get(name) or [m])
    r = subprocess.run([sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', f'--basetemp={MUT.parent}/pt',
                        *TESTS], cwd=BE, env=env, capture_output=True, text=True, encoding='utf-8')
    tail = [l for l in r.stdout.splitlines() if 'passed' in l or 'failed' in l][-1:]
    failed = [l.split(' ')[1] for l in r.stdout.splitlines() if l.startswith('FAILED')][:6]
    print(f'{name:<40} {"KILLED" if r.returncode else "SURVIVED"} {tail} {failed}', flush=True)
restore()
