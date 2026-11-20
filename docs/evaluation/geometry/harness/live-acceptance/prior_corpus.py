"""Exposure corpus for a new holdout (axo-live-acceptance-harness/1).

Collects every geometry-looking string the system or its authors have already seen:
- string values in every TRACKED .json/.jsonl of the repository (all run manifests, responses, fixtures);
- Python string constants in tracked backend/tests, backend/scripts and docs/**/tools sources;
- the local SLM training/validation sets (`--training-dir`, outside the repository).

A new case is EXPOSED when its normalised text is contained in any collected string (containment, not equality, so a
problem wrapped inside a training prompt or a longer exam text still counts).

usage: python prior_corpus.py --training-dir <dir> --out <new file>
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
_GEOM = re.compile(r"hình|hinh|tứ diện|tu dien|lăng trụ|lang tru|lập phương|lap phuong|chóp|chop|hộp|hop|mặt phẳng|mat phang|khoảng cách|khoang cach|góc|goc|cạnh|canh|thể tích|the tich", re.I)


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").lower()
    return re.sub(r"\s+", " ", s).strip()


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(k)
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _keep(s: str) -> bool:
    return 15 <= len(s) <= 20000 and bool(_GEOM.search(s))


def collect(training_dir: Path | None) -> dict[str, str]:
    out: dict[str, str] = {}
    files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8").split("\0")
    for rel in filter(None, files):
        p = ROOT / rel
        try:
            if rel.endswith(".json"):
                values = _strings(json.loads(p.read_text(encoding="utf-8")))
            elif rel.endswith(".jsonl"):
                values = (s for line in p.read_text(encoding="utf-8").splitlines() if line.strip()
                          for s in _strings(json.loads(line)))
            elif rel.endswith(".py") and (rel.startswith(("backend/tests/", "backend/scripts/")) or "/tools/" in rel):
                values = (n.value for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
                          if isinstance(n, ast.Constant) and isinstance(n.value, str))
            else:
                continue
            for s in values:
                if _keep(s):
                    out.setdefault(norm_text(s), rel)
        except (ValueError, SyntaxError, OSError, UnicodeDecodeError):
            continue
    if training_dir:
        for p in sorted(training_dir.rglob("*.jsonl")):
            if ".venv" in p.parts:
                continue
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    for s in _strings(json.loads(line)):
                        if _keep(s):
                            out.setdefault(norm_text(s), f"training:{p.relative_to(training_dir).as_posix()}")
    return out


def exposed(texts: list[str], corpus: dict[str, str]) -> dict[str, str]:
    """{text: first corpus source containing it}."""
    hay = "\n\x00".join(corpus)
    sources = list(corpus.values())
    starts, pos = [], 0
    for k in corpus:
        starts.append(pos)
        pos += len(k) + 2
    import bisect
    hits = {}
    for t in texts:
        i = hay.find(norm_text(t))
        if i >= 0:
            hits[t] = sources[bisect.bisect_right(starts, i) - 1]
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--training-dir", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    corpus = collect(a.training_dir)
    raw = json.dumps(corpus, ensure_ascii=False, sort_keys=True).encode("utf-8")
    a.out.write_bytes(raw)
    print(json.dumps({"normalized_texts": len(corpus), "sha256": hashlib.sha256(raw).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
