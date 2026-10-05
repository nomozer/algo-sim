# -*- coding: utf-8 -*-
"""regular-square-pyramid-w01 — does the browser evidence measured at ed37f9fa (candidate 4629c3e8) transfer to the
candidate after the self-review fix (5234c37e)? Read-only, 0 model calls. Pattern of
`cuboid-merge/diagnostics/fixture_transfer_cmerge.py`.

Inputs: the run's committed `inputs/` (fixtures generated at ed37f9fa in a clean worktree, the ones the images were taken
from) and a fresh `generate_generic_tier_a_fixtures.py --out <dir>` at the commit under review (clean worktree).
1. Reproduction: sha256 of the committed FIXTURE_MANIFEST.json must equal `fixture_manifest_sha256` recorded in
   results/BROWSER_EVIDENCE.json — in its raw, LF-blob or CRLF form (the generator writes CRLF on Windows, git stores
   LF; the first version of this script compared only the LF form and wrongly failed, FIXTURE_TRANSFER_b5cf4503.json).
2. Comparison per fixture (LF-normalised bytes; if different, every differing JSON path with old/new values).
3. Verdict TRANSFERS only if every difference lies in the identity fields `product_commit_sha` / `product_tree_sha` of
   the wrapper (and FIXTURE_MANIFEST's own identity fields and the per-fixture hashes that follow from them), i.e. every
   `envelope` — the renderer's only input — is byte-identical.
Usage: <python> fixture_transfer_w01.py <old inputs dir> <new dir> <BROWSER_EVIDENCE.json> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

old, new, evidence, out = (Path(a) for a in sys.argv[1:5])
IDENTITY = {"product_commit_sha", "product_tree_sha"}


def lf(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n")


def diff(a, b, path="$"):
    if type(a) is not type(b):
        yield path, a, b
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                yield f"{path}.{k}", a.get(k, "<absent>"), b.get(k, "<absent>")
            else:
                yield from diff(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield f"{path}[len]", len(a), len(b)
        for i, (x, y) in enumerate(zip(a, b)):
            yield from diff(x, y, f"{path}[{i}]")
    elif a != b:
        yield path, a, b


def short(v):
    return v if isinstance(v, (int, float, bool)) or v is None or (isinstance(v, str) and len(v) <= 160) \
        else f"<{type(v).__name__}, {len(json.dumps(v, ensure_ascii=False))} chars>"


recorded = json.loads(evidence.read_text(encoding="utf-8"))["fixture_manifest_sha256"]
# The suite hashes the RAW bytes the generator wrote (CRLF on Windows: text-mode write_text); git stores the LF blob.
# Accept the raw file, its LF blob or the blob's CRLF form — one of them must be the recorded hash.
_m = lf(old / "FIXTURE_MANIFEST.json")
forms = {"raw": hashlib.sha256((old / "FIXTURE_MANIFEST.json").read_bytes()).hexdigest(),
         "lf_blob": hashlib.sha256(_m).hexdigest(),
         "crlf": hashlib.sha256(_m.replace(b"\n", b"\r\n")).hexdigest()}
report = {"schema_version": "fixture-transfer/1", "old_dir": str(old), "new_dir": str(new),
          "reproduction": {"recorded_fixture_manifest_sha256": recorded, "committed_fixture_manifest_sha256": forms,
                           "matching_form": next((k for k, v in forms.items() if v == recorded), None),
                           "byte_exact": recorded in forms.values()},
          "fixtures": {}}
names = sorted(p.name for p in (old / "fixtures").glob("*.json"))
assert names == sorted(p.name for p in (new / "fixtures").glob("*.json")), "fixture sets differ"
for n in names:
    a_raw, b_raw = lf(old / "fixtures" / n), lf(new / "fixtures" / n)
    a, b = json.loads(a_raw), json.loads(b_raw)
    entry = {"byte_equal": a_raw == b_raw,
             "envelope_byte_equal": json.dumps(a["envelope"], sort_keys=True, ensure_ascii=False)
             == json.dumps(b["envelope"], sort_keys=True, ensure_ascii=False)}
    if not entry["byte_equal"]:
        d = list(diff(a, b))
        entry["differing_paths"] = [{"path": p, "old": short(x), "new": short(y)} for p, x, y in d]
        entry["identity_only"] = all(p.split(".")[1] in IDENTITY for p, _, _ in d if p.count(".") == 1) \
            and all(p.count(".") == 1 for p, _, _ in d)
    report["fixtures"][n] = entry
m_old, m_new = json.loads(lf(old / "FIXTURE_MANIFEST.json")), json.loads(lf(new / "FIXTURE_MANIFEST.json"))
manifest_paths = [p for p, _, _ in diff(m_old, m_new)]
report["fixture_manifest_differing_paths"] = manifest_paths
envelopes_equal = all(e["envelope_byte_equal"] for e in report["fixtures"].values())
identity_only = all(e["byte_equal"] or e.get("identity_only") for e in report["fixtures"].values())
manifest_ok = all(p.split(".")[1] in IDENTITY or p.startswith("$.fixtures.") for p in manifest_paths)
report["summary"] = {"fixtures": len(names),
                     "byte_equal": sum(e["byte_equal"] for e in report["fixtures"].values()),
                     "envelopes_byte_equal": sum(e["envelope_byte_equal"] for e in report["fixtures"].values()),
                     "differences_only_in_identity_fields": identity_only and manifest_ok}
report["verdict"] = ("TRANSFERS — every envelope the renderer reads is byte-identical; only the product identity "
                     "fields differ" if report["reproduction"]["byte_exact"] and envelopes_equal and identity_only
                     and manifest_ok else "DOES_NOT_TRANSFER — re-measure")
if out.exists():
    raise SystemExit(f"refusing to overwrite {out}")
out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(report["reproduction"]), json.dumps(report["summary"], ensure_ascii=False), report["verdict"])
