"""Pre-merge diff audit facts for main...HEAD (read-only git calls)."""
import json, re, subprocess, sys
from collections import Counter

repo = sys.argv[1]
g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True).stdout.decode("utf-8", "replace")
ns = [l.split("\t") for l in g("diff", "--name-status", "-z", "main...HEAD").replace("\0", "\t").strip("\t").split("\t")]
flat = g("diff", "--name-status", "-z", "main...HEAD").split("\0")
items, i = [], 0
while i < len(flat) - 1:
    st = flat[i]
    if not st:
        i += 1
        continue
    items.append((st[0], flat[i + 1]))
    i += 2
sizes = {}
for rec in g("ls-tree", "-r", "-l", "-z", "HEAD").split("\0"):
    if rec:
        meta, path = rec.split("\t", 1)
        parts = meta.split()
        sizes[path] = int(parts[3]) if parts[3] != "-" else 0
added = [(sizes.get(p, 0), p) for s, p in items if s in "AM"]
added.sort(reverse=True)
sens = [p for s, p in items if re.search(r"(?i)(\.env($|\.)|\.db$|\.sqlite|credential|secret|\.pem$|\.key$|\.gguf$|\.safetensors$|\.bin$|\.zip$)", p)]
binary_ext = Counter(p.rsplit(".", 1)[-1].lower() for s, p in items if s in "AM" and re.search(r"\.(png|jpg|jpeg|webp|gif|pdf|docx)$", p, re.I))
deleted = [p for s, p in items if s == "D"]
out = {
    "files": len(items), "status_counts": Counter(s for s, _ in items),
    "tip_bytes_added_or_modified": sum(x for x, _ in added),
    "largest": [{"bytes": x, "path": p} for x, p in added[:10]],
    "files_over_1MiB": sum(1 for x, _ in added if x > 1 << 20),
    "sensitive_names": sens, "binary_media_by_ext": binary_ext,
    "deleted_by_dir": Counter(p.rsplit("/", 1)[0] for p in deleted),
}
print(json.dumps(out, indent=1, default=dict))
