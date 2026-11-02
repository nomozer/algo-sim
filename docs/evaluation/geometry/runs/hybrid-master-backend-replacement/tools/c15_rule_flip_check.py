"""Continuation 18 (review R2-2): does declaring `DINH_NGHIA_DIEM` in `AUXILIARY_RULES` change the S-2/R-1 runner's C15
`composition_label` of any stored gold row? The label function is unchanged; it reads the union of the rule table's
function lists, so the entry is a GLOBAL change of that rule (it can only move a row from DISCOVERED to REGISTERED).
Recomputes every stored row with and without the entry. Usage: c15_rule_flip_check.py [out.json]   (offline, 0 calls)
"""
import importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
from app.simulation.geometry_functions import registry  # noqa: E402

spec = importlib.util.spec_from_file_location('s2_runner', ROOT / 'backend/scripts/run_s2_student_language_pilot.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
FILES = ('s2-pilot-gold-replay-c18.jsonl', 'r1-live-pilot-gold-replay-c18.jsonl')


def labels():
    out = {}
    for f in FILES:
        for line in (RUN / f).read_text(encoding='utf-8').splitlines():
            row = json.loads(line) if line.strip() else {}
            if row.get('type') == 'row':
                out[f"{f}|{row['case_id']}"] = runner.composition_label(row)
    return out


if __name__ == '__main__':
    with_rule = labels()
    entry = registry.AUXILIARY_RULES.pop(registry.DINH_NGHIA_DIEM)
    try:
        without = labels()
    finally:
        registry.AUXILIARY_RULES[registry.DINH_NGHIA_DIEM] = entry
    flips = {k: [without[k], with_rule[k]] for k in with_rule if with_rule[k] != without[k]}
    res = {'rows': len(with_rule), 'flips': flips, 'labels_with_rule': with_rule,
           'note': 'global effect: any planner step using midpoint / intersect_line_line beyond the description now counts as '
                   'a registered-rule function (undercounts discovery, never overcounts)'}
    print(json.dumps({'rows': res['rows'], 'flips': flips}, ensure_ascii=False))
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
            f.write('\n')
