"""Build PENDING publication-exception proposals for branch-introduced hits (never writes APPROVED_BY_USER, never prints values)."""
import hashlib, json, re, subprocess, sys
from pathlib import Path

repo, report, out = Path(sys.argv[1]), Path(sys.argv[2]).read_text(encoding="utf-8"), Path(sys.argv[3])
classes = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))["rows"]
head_paths = set(subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.splitlines())
head_blobs = {}
for rec in subprocess.run(["git", "ls-tree", "-r", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.splitlines():
    meta, path = rec.split("\t", 1)
    head_blobs[path] = meta.split()[2]
pairs = {}
for m in re.finditer(r"rule=(\S+) path=(\S+) blob=([0-9a-f]{40}) line=(\d+)", report):
    pairs.setdefault((m.group(2), m.group(3)), {"rules": set(), "lines": []})
    pairs[(m.group(2), m.group(3))]["rules"].add(m.group(1))
    pairs[(m.group(2), m.group(3))]["lines"].append(int(m.group(4)))
entries = []
for (path, blob), v in sorted(pairs.items()):
    data = subprocess.run(["git", "cat-file", "-p", blob], cwd=repo, capture_output=True, check=True).stdout
    first = subprocess.run(["git", "log", "--reverse", "--format=%H %cI", f"--find-object={blob}", "bc6ff5e33..HEAD", "--", path],
                           cwd=repo, capture_output=True, text=True, check=True).stdout.split("\n")[0].split()
    c = [r for r in classes if r["path"] == path and r["blob"] == blob]
    entries.append({
        "path": path, "blob": blob, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
        "rules": sorted(v["rules"]), "lines": sorted(v["lines"]),
        "category": "SYNTHETIC_TEST_VECTOR_OR_PLACEHOLDER",
        "scope": "HISTORY_AND_TIP" if head_blobs.get(path) == blob else "HISTORY_ONLY",
        "first_commit": first[0] if first else None, "first_commit_date": first[1] if len(first) > 1 else None,
        "already_public_on_origin_main": False,
        "evidence": {
            "value_sha256_prefixes": sorted({r["value_sha256_prefix"] for r in c}),
            "register_call_on_loopback_test_server": all(r["in_register_call"] or r["loopback_base_in_file"] for r in c),
            "frozen_run_tool": "/runs/" in path and "/tools/" in path,
        },
        "owner_decision": "PENDING_OWNER_DECISION",
    })
out.write_text(json.dumps({"schema": "publication-exception-proposal/1", "target_register":
    "docs/evaluation/geometry/runs/publication-safety-remediation/publication_exceptions.json",
    "note": "Proposal only. Agents never write APPROVED_BY_USER; the register is not modified by this run.",
    "entries": entries}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(len(entries), sum(e["scope"] == "HISTORY_AND_TIP" for e in entries))
