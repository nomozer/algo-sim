import hashlib, subprocess, sys
repo, rev = sys.argv[1], sys.argv[2]
paths = ["backend/app", "frontend/src/simulations/domains/semantic", "frontend/src/simulations/domains/semantic/semantic_program.schema.json"]
def git(*a): return subprocess.run(["git","-C",repo,*a],capture_output=True,check=True).stdout
files = []
for p in paths:
    out = git("ls-tree","-r","-z","--name-only",rev,"--",p).split(b"\0")
    files += [f.decode() for f in out if f]
files = sorted(f for f in files if not any(b in f for b in ("__pycache__",".pyc",".pyo")))  # dup entries kept like original (file listed twice)
h = hashlib.sha256()
for f in files:
    data = git("cat-file","blob",f"{rev}:{f}").replace(b"\r\n",b"\n")
    h.update(f.encode()); h.update(b"\0"); h.update(hashlib.sha256(data).digest())
print(rev, len(files), h.hexdigest())
