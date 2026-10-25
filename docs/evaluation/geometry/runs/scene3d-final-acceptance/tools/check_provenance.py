"""Read-only product/evidence verification; output is a new run artifact, never a frozen receipt."""
import ast
import hashlib
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
RUN = Path(__file__).resolve().parents[1]
FROZEN = ROOT / ".superpowers/worktrees/svc-cand"  # overridden below: linked worktree shares the root repository
COMMON = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True).strip()).resolve()
REPOSITORY = COMMON.parent
FROZEN = REPOSITORY / ".superpowers/worktrees/svc-cand"
sha = lambda b: hashlib.sha256(b).hexdigest()
git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

result = {"schema": "scene3d-acceptance-provenance/1", "source_head": git("rev-parse", "HEAD"),
          "main": git("rev-parse", "main"), "candidate": git("rev-parse", "c84e8620"),
          "product": git("rev-parse", "b8b3311b"), "provider_calls": 0, "errors": []}
result["product_diff_from_freeze"] = git("diff", "c84e8620", "--name-only", "--", "frontend/src", "backend/app", "frontend/vite.config.ts")
result["product_trees"] = {p: {"candidate": git("rev-parse", f"c84e8620:{p}"), "head": git("rev-parse", f"HEAD:{p}")}
                           for p in ["frontend/src", "backend/app"]}
result["locked_gate_diff"] = git("diff", "c84e8620", "--name-only", "--", "frontend/scripts/compiler-scene-suite.mjs", "frontend/scripts/compiler-scene-replay-lib.mjs")
oldrun = ROOT / "docs/evaluation/geometry/runs/scene3d-visual-correction"
receipt = json.loads((oldrun / "verification/full-t3/t3-c84e8620/receipt.json").read_text(encoding="utf-8"))
result["prior_t3_receipt"] = {"sha256": sha((oldrun / "verification/full-t3/t3-c84e8620/receipt.json").read_bytes()),
                            "verdict": receipt["verdict"], "target": receipt["target"], "summaries": receipt["summaries"]}
result["t3_streams"] = {}
for name, expected in receipt["streams"].items():
    file = FROZEN / ".superpowers/closure/t3-c84e8620" / name
    if file.exists():
        actual = sha(file.read_bytes())
        result["t3_streams"][name] = {"sha256": actual, "matches": actual == expected["sha256"]}
    else:
        result["t3_streams"][name] = {"status": "NOT_RECOVERABLE"}
envpython = REPOSITORY / "backend/.venv/Scripts/python.exe"
taskenv = dict(os.environ)
entry = int(taskenv.get('GIT_CONFIG_COUNT', '0'))
taskenv.update({'GIT_CONFIG_COUNT':str(entry+1), f'GIT_CONFIG_KEY_{entry}':'safe.directory', f'GIT_CONFIG_VALUE_{entry}':str(FROZEN)})
verify = subprocess.run([str(envpython), "backend/scripts/freeze_evaluation_candidate.py", "--verify"],
                        cwd=FROZEN, env=taskenv, capture_output=True, text=True, encoding="utf-8")
result["freeze_verify"] = {"exit_code": verify.returncode, "stdout": verify.stdout.strip()}
result["detached_status"] = subprocess.check_output(["git", "status", "--porcelain"], cwd=FROZEN, env=taskenv, text=True).strip()
result["detached_head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=FROZEN, env=taskenv, text=True).strip()
result["official_receipt"] = {"path": str((oldrun / "visual/official-run-c84e8620/BROWSER_EVIDENCE.json").relative_to(ROOT)),
                            "sha256": sha((oldrun / "visual/official-run-c84e8620/BROWSER_EVIDENCE.json").read_bytes()),
                            "unchanged_since_handoff": not git("diff", "16b46d38", "--name-only", "--", str(oldrun.relative_to(ROOT)))}
result["server_sources"] = []
for name in ["scene3d-view.tsx", "scene3d-edge-visibility.ts", "Scene3DExplorer.tsx"]:
    relative = "src/simulations/domains/geometry/" + name
    try:
        text = urllib.request.urlopen("http://127.0.0.1:3156/" + relative + "?raw", timeout=5).read().decode("utf-8")
        literal = re.search(r'''export default ('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")''', text).group(1)
        content = ast.literal_eval(literal)
        local = (ROOT / "frontend" / relative).read_text(encoding="utf-8")
        result["server_sources"].append({"file": relative, "sha256_lf": sha(local.encode()),
                                         "server_sha256_lf": sha(content.replace("\r\n", "\n").encode()),
                                         "matches": content.replace("\r\n", "\n") == local})
    except Exception as exc:
        result["errors"].append({"source": relative, "kind": type(exc).__name__})
result["pass"] = (not result["product_diff_from_freeze"] and not result["locked_gate_diff"]
                  and verify.returncode == 0 and not result["detached_status"]
                  and all(x.get("matches") is True for x in result["t3_streams"].values())
                  and all(x["matches"] for x in result["server_sources"]) and not result["errors"])
output = RUN / "provenance-verified.json"
if output.exists():
    raise SystemExit("Fresh output required")
output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"pass": result["pass"], "streams": result["t3_streams"], "sources": result["server_sources"]}, indent=2))
raise SystemExit(0 if result["pass"] else 1)
