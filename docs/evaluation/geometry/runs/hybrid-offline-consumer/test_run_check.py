import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]


def test_timeout_still_has_a_receipt_and_preserves_partial_output_locally(tmp_path):
    spec = importlib.util.spec_from_file_location('run_check', Path(__file__).with_name('run_check.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    output = tmp_path/'timeout'
    code = m.main(output, ROOT, [sys.executable, '-c', 'import time; print("started", flush=True); time.sleep(5)'], timeout=0.5)
    receipt = json.loads((output/'execution.json').read_text(encoding='utf-8'))
    assert code == 124 and receipt['timed_out'] is True
    assert receipt['streams']['stdout']['bytes'] > 0
    assert receipt['streams']['stdout']['sha256'] != receipt['streams']['stdout']['stored_sha256']
