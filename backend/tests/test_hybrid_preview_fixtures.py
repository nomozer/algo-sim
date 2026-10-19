"""Lock on the committed Hybrid preview envelope fixtures (run `hybrid-preview-contract-hardening`): the exporter reproduces
them from the real endpoint, they cover the frontend contract, and they hold no secret."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
#: Adapter /2 bundle. The first bundle (`fixtures/`, exported at 2a832ae2) is superseded: it predates the review fixes and
#: is labelled adapter /1, the label of the pre-classification adapter (report §6).
FIXTURES = ROOT / 'docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2'
SCRIPT = ROOT / 'backend/scripts/export_hybrid_preview_fixtures.py'
MANIFEST = json.loads((FIXTURES / 'manifest.json').read_text(encoding='utf-8'))


def _run(*args):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('HYBRID_ROUTE_D_PREVIEW', 'GEMINI'))}
    env.update(ALLOW_LIVE_AI='0', PYTHONIOENCODING='utf-8')
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT / 'backend', env=env, capture_output=True,
                          text=True, encoding='utf-8', timeout=600)


def test_committed_fixtures_regenerate_identically_from_the_endpoint():
    r = _run('--verify', str(FIXTURES))
    assert r.returncode == 0, (r.stdout[-3000:], r.stderr[-3000:])
    assert json.loads(r.stdout)['problems'] == []


def test_exporter_refuses_to_overwrite_existing_fixtures():
    before = {p.name: p.read_bytes() for p in FIXTURES.iterdir()}
    r = _run('--out', str(FIXTURES))
    assert r.returncode == 2 and 'refusing to overwrite' in r.stdout
    assert {p.name: p.read_bytes() for p in FIXTURES.iterdir()} == before


def test_fixture_inventory_covers_the_frontend_contract():
    rows = MANIFEST['fixtures']
    kinds = [r['kind'] for r in rows]
    assert (kinds.count('served'), kinds.count('refusal'), kinds.count('gate')) == (12, 25, 4)
    covers = {tag for r in rows for tag in r['covers']}
    assert {'multi_goal', 'symbolic_length_unit', 'goal_observation', 'object:section', 'injected_fault'} <= covers
    refusals = [r['expected'] for r in rows if r['kind'] == 'refusal']
    assert {e['failure_category'] for e in refusals} == {'capability_gap', 'insufficient_specification',
                                                         'geometry_generation_failed', 'verification_gap'}
    assert {e['refusal_cause'] for e in refusals} == {'SOURCE', 'UNKNOWN'}
    producer = MANIFEST['producer']
    assert producer['backend_app_dirty'] is False and producer['inputs_dirty'] is False and len(producer['commit']) == 40
    assert producer['adapter_version'] == 'hybrid-preview-adapter/2'
    assert producer['envelope_version'] == 'hybrid-route-d-preview/1'


def test_fixture_files_match_the_manifest_and_hold_no_secret():
    for row in MANIFEST['fixtures']:
        raw = (FIXTURES / row['file']).read_bytes().replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == row['sha256'], row['id']
        text = raw.decode('utf-8')
        for secret in ('X-AlgoSim-Preview-Token', 'GEMINI_API_KEY', 'HYBRID_ROUTE_D_PREVIEW_TOKEN', 'Authorization',
                       'api_key'):
            assert secret not in text, (row['id'], secret)
        fixture = json.loads(text)
        assert fixture['producer'] == MANIFEST['producer'] and fixture['expected'] == row['expected']


def test_served_fixtures_never_present_an_observation_as_a_proof():
    for row in MANIFEST['fixtures']:
        if row['kind'] != 'served':
            continue
        response = json.loads((FIXTURES / row['file']).read_text(encoding='utf-8'))['response']
        for group in ('goal_checks', 'negated_checks'):
            for observation in response['route_d']['planner'].get(group, {}).values():
                assert observation['proof_status'] == 'UNVERIFIABLE' and observation['can_present_as_proven'] is False
        assert 'đã chứng minh' not in json.dumps(response['envelope'], ensure_ascii=False).lower()


def _exporter():
    import importlib.util
    spec = importlib.util.spec_from_file_location('export_hybrid_preview_fixtures', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_identity_restore_maps_only_declared_version_pairs():
    """Run `goal-directed-function-composition`: the bundle predates the route D version bump. `--verify` may map a
    fresh identity back ONLY through the declared old → new pairs; anything else stays different or is refused."""
    import copy
    X = _exporter()
    stored = json.loads((FIXTURES / 'served-H01_CUBE.json').read_text(encoding='utf-8'))['response']
    fresh = copy.deepcopy(stored)
    ident = fresh['route_d']['runtime_identity']
    for key in X.IDENTITY_DELTAS[0]['versions']:                       # the whole declared chain, oldest -> newest
        assert ident[key] == X.IDENTITY_DELTAS[0]['versions'][key][0]
        ident[key] = X.IDENTITY_DELTAS[-1]['versions'][key][1]
    fresh['route_d']['planner']['version'] = X.IDENTITY_DELTAS[-1]['versions']['planner_version'][1]
    ident['fingerprint'] = X._preview_fingerprint(ident)
    assert X._restore_declared_identity(fresh, stored) == stored                     # declared pairs only: restored
    undeclared = copy.deepcopy(fresh)
    undeclared['route_d']['runtime_identity']['registry_version'] = 'geometry-functions/99'
    undeclared['route_d']['runtime_identity']['fingerprint'] = X._preview_fingerprint(undeclared['route_d']['runtime_identity'])
    assert X._restore_declared_identity(undeclared, stored) != stored                # undeclared: still differs
    forged = copy.deepcopy(fresh)
    forged['route_d']['runtime_identity']['fingerprint'] = '0' * 64
    assert X._restore_declared_identity(forged, stored) is None                      # fingerprint not of its identity
    other = copy.deepcopy(fresh)
    other['envelope']['status'] = 'unsupported'
    assert X._restore_declared_identity(other, stored) != stored                     # identity restore never hides content
