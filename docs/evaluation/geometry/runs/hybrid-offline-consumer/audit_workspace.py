"""Read-only P0 audit. Findings contain paths/line numbers, never matched secret values or traceback text."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
BASE = '3f6d737529af6fc79494fc3baeb340a7ca663b10'


def git(*args, root=ROOT):
    return subprocess.check_output(['git', '-c', 'safe.directory=' + str(root).replace('\\', '/'), '-C', str(root), *args])


def main(out):
    assert git('rev-parse', 'main').decode().strip() == BASE
    paths = git('diff-tree', '--no-commit-id', '--name-only', '-r', '77f7aaf7').decode().splitlines()
    patterns = {
        'credential': r'(?i)(?:sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN [^-]*PRIVATE KEY-----|(?:api[_-]?key|access[_-]?token|authorization)\s*[:=]\s*[\x22\x27]?(?!redacted|none|null|fake|test|dummy|0\b)[A-Za-z0-9_/-]{24,})',
        'raw_traceback': r'Traceback \(most recent call last\):',
        'raw_model_field': r'(?i)(?:raw_response|raw_model_output)\s*[:=]',
        'sensitive_field': r'(?i)(?:password|bearer)\s*[:=]\s*[^\s]{12,}',
    }
    rows = []
    for path in paths:
        if not path.endswith('.log'): continue
        data = git('show', BASE + ':' + path); text = data.decode('utf-8', errors='replace')
        hits = {name: [text[:m.start()].count('\n')+1 for m in re.finditer(pattern, text)]
                for name, pattern in patterns.items()}
        rows.append({'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                     'findings': {k: v for k, v in hits.items() if v}})
    assert len(rows) == 22
    main_root = Path(git('rev-parse', '--git-common-dir').decode().strip()).resolve().parent
    dirty = git('status', '--porcelain', root=main_root).decode().splitlines()
    changed_files = []
    for line in dirty:
        path = main_root / line[3:]
        if path.is_file():
            changed_files.append({'path': line[3:], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    result = {'base_main': BASE, 'preservation_commit': '77f7aaf7', 'logs': rows,
              'remote_push_status': 'REMOTE_PUSH_SECURITY_BLOCKED' if any(r['findings'] for r in rows) else 'NO_PATTERN_FINDINGS',
              'scope': 'All 22 blobs decoded and scanned. Test failures are diagnostics, not provider outputs. Raw traceback manually confirmed at the reported location. Pattern scan is not a universal secret guarantee.',
              'root_status': dirty, 'root_file_hashes': changed_files, 'disk_free_bytes': shutil.disk_usage(ROOT).free,
              'worktrees': git('worktree', 'list', '--porcelain').decode().splitlines(),
              'deletions': [], 'reclaimed_bytes': 0}
    with out.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print(result['remote_push_status'], len(rows))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
