"""Classify HARDCODED_PASSWORD hits without printing any secret value (only sha256 prefixes and context facts)."""
import hashlib, json, re, subprocess, sys
from pathlib import Path

repo = Path(sys.argv[1])
report = Path(sys.argv[2]).read_text(encoding="utf-8")
env_files = [Path(p) for p in sys.argv[3:]]
pat = re.compile(rb"(?i)password\s*[:=]\s*['\"]([^'\"\r\n]{6,})['\"]")
env_blob = b"".join(p.read_bytes() for p in env_files if p.exists())
seen = {}
rows = []
for m in re.finditer(r"rule=HARDCODED_PASSWORD path=(\S+) blob=([0-9a-f]{40}) line=(\d+)", report):
    path, blob, line = m.group(1), m.group(2), int(m.group(3))
    data = subprocess.run(["git", "cat-file", "-p", blob], cwd=repo, capture_output=True, check=True).stdout
    lines = data.split(b"\n")
    ln = lines[line - 1]
    vals = pat.findall(ln)
    ctx = b"\n".join(lines[max(0, line - 4):line + 2])
    for v in vals:
        h = hashlib.sha256(v).hexdigest()[:16]
        rows.append({
            "path": path, "blob": blob, "line": line, "value_sha256_prefix": h, "value_length": len(v),
            "in_register_call": b"/api/auth/register" in ctx,
            "synthetic_email_domain": bool(re.search(rb"@(example\.com|algosim\.test)", ctx)),
            "loopback_base_in_file": bool(re.search(rb"127\.0\.0\.1|localhost", data)),
            "value_in_env_files": v in env_blob,
        })
print(json.dumps({"hits": len(rows), "distinct_values": sorted({r["value_sha256_prefix"] for r in rows}), "rows": rows}, indent=1))
