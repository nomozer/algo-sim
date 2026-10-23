"""Integration invariants + default-route isolation receipt. 0 provider calls, no product changes.

Run from `backend/` of the integrated checkout:
    python ../docs/evaluation/geometry/runs/hybrid-disabled-integration/verify_integration_invariants.py <NEW-output.json>

Default-route isolation is measured, not assumed: a fresh interpreter imports the production entry points
(`app.main`, `app.ai.pipeline`) and records which product modules are loaded; each loaded module is compared
byte-for-byte (Git blob) with `main`. A loaded module whose blob differs from `main` is a finding.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = 'main'
ROOT = Path.cwd().parent

PROBE = r'''
import json, sys
import app.main, app.ai.pipeline
from app.ai.pipeline import route_policy_snapshot
mods = sorted({m.__file__ for n, m in list(sys.modules.items())
               if n.startswith("app.") and getattr(m, "__file__", None)})
default = route_policy_snapshot({})
analyze_with_preview_env = route_policy_snapshot({"HYBRID_ROUTE_D_PREVIEW": "1"})
print(json.dumps({"modules": mods,
                  "default_policy": [default.geometry_compiler_mode, default.hybrid_preview_enabled,
                                     default.response_contract, default.fingerprint()],
                  "analyze_policy_with_preview_env": [analyze_with_preview_env.hybrid_preview_enabled,
                                                      analyze_with_preview_env.fingerprint()]}))
'''


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


def blob(rev, rel):
    r = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', f'{rev}:{rel}'], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def main(out):
    # Recorded from the inherited environment BEFORE the probe forces it; asserting the forced value would be circular.
    inherited_live = os.environ.get('ALLOW_LIVE_AI', 'UNSET')
    env = {k: v for k, v in os.environ.items() if k not in ('HYBRID_ROUTE_D_PREVIEW', 'GEOMETRY_COMPILER_MODE')}
    env['ALLOW_LIVE_AI'] = '0'
    probe = json.loads(subprocess.run([sys.executable, '-c', PROBE], capture_output=True, text=True,
                                      check=True, env=env, cwd=Path.cwd()).stdout.splitlines()[-1])
    loaded = [Path(f).resolve().relative_to(ROOT).as_posix() for f in probe['modules']]
    differs = [rel for rel in loaded if blob('HEAD', rel) != blob(BASE, rel)]
    changed = git('diff', '--name-only', BASE, 'HEAD', '--', 'backend/app').splitlines()

    sys.path.insert(0, str(Path.cwd()))
    from app.main import CACHE_VERSION
    from app.ai.fact_extraction import RESPONSE_CONTRACT
    from app.simulation.semantic_program.validator import MAX_MEMORY_DECLARATIONS
    from app.simulation.geometry_compiler.routing import che_do
    from app.simulation.geometry_functions import registry, planner, engine
    from app.ai.adapter4_route import ADAPTER_V4_VERSION
    from app.ai.hybrid_preview import ADAPTER_VERSION, ENVELOPE_VERSION

    invariants = {'CACHE_VERSION': CACHE_VERSION, 'DEFAULT_MODE': che_do({}), 'RESPONSE_CONTRACT': RESPONSE_CONTRACT,
                  'MAX_MEMORY_DECLARATIONS': MAX_MEMORY_DECLARATIONS, 'ALLOW_LIVE_AI': inherited_live}
    expected = {'CACHE_VERSION': '127', 'DEFAULT_MODE': 'LLM_ONLY', 'RESPONSE_CONTRACT': 'flat',
                'MAX_MEMORY_DECLARATIONS': 32, 'ALLOW_LIVE_AI': '0'}
    receipt = {
        'schema': 'hybrid_disabled_integration_invariants/1', 'provider_calls': 0,
        'head': git('rev-parse', 'HEAD'), 'base': git('rev-parse', BASE),
        'invariants': invariants, 'invariants_hold': invariants == expected,
        'contract_versions': {'registry': registry.REGISTRY_VERSION, 'planner': planner.PLANNER_VERSION,
                              'engine': engine.ENGINE_VERSION, 'adapter4': ADAPTER_V4_VERSION,
                              'preview_adapter': ADAPTER_VERSION, 'preview_envelope': ENVELOPE_VERSION,
                              'registry_functions': len(registry.REGISTRY)},
        'default_policy': probe['default_policy'],
        'analyze_policy_with_preview_env': probe['analyze_policy_with_preview_env'],
        'product_files_changed_vs_base': changed,
        'modules_loaded_by_production_entry': len(loaded),
        'loaded_modules_differing_from_base': differs,
        'changed_files_not_loaded_at_startup': sorted(set(changed) - set(loaded)),
    }
    out = Path(out)
    with out.open('x', encoding='utf-8') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({k: receipt[k] for k in ('invariants_hold', 'default_policy', 'analyze_policy_with_preview_env',
                                              'loaded_modules_differing_from_base')}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
