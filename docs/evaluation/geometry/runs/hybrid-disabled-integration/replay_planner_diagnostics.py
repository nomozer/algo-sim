"""Re-run the Session 4A locked planner diagnostics on the integrated candidate. No product changes.

Session 4A's `planner_diagnostics.verify_source` pins HEAD to the Session 3 candidate. Here the identity
check is replaced by a stricter product check: every product/test subtree of the integrated HEAD must be
the same Git tree as at 84c729e0. The locked inputs/oracles/lock are copied byte-for-byte and verified by
4A's own `evaluate`, so nothing is re-authored.

    python replay_planner_diagnostics.py <integrated-root> <NEW-output-dir>
"""
from pathlib import Path
import shutil
import subprocess
import sys

S3_CANDIDATE = '84c729e0b0df7868dfcc0a6e48cac457d7959e92'
SUBTREES = ('backend/app', 'backend/tests', 'backend/scripts', 'frontend/src')
S4A = Path(__file__).resolve().parent.parent / 'hybrid-session4a-readiness'
LOCKED = ('diagnostic-inputs.json', 'diagnostic-oracles.json', 'diagnostic-lock.json')


def tree(root, rev, path):
    return subprocess.run(['git', '-C', str(root), 'rev-parse', f'{rev}:{path}'],
                          capture_output=True, text=True, check=True).stdout.strip()


def main(root, out):
    status = subprocess.run(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=no'],
                            capture_output=True, text=True, check=True).stdout
    assert not status, 'INTEGRATED_TRACKED_CHANGES'
    for p in SUBTREES:
        assert tree(root, 'HEAD', p) == tree(root, S3_CANDIDATE, p), f'PRODUCT_TREE_DIFFERS:{p}'
    out.mkdir(parents=True, exist_ok=False)
    for name in LOCKED:
        shutil.copyfile(S4A / 'results' / name, out / name)
    sys.path.insert(0, str(root / 'backend'))
    sys.path.insert(0, str(S4A))
    import planner_diagnostics as pd
    pd.verify_source = lambda _root: S3_CANDIDATE  # subtree identity proven above
    pd.evaluate(root, out)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
