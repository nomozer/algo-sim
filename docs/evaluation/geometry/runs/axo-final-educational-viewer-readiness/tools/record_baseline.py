"""Read-only Git/resource inventory; never serializes file contents or environment secrets."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parents[1]


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir")).parent
worktrees = []
for block in git("worktree", "list", "--porcelain").split("\n\n"):
    lines = block.splitlines()
    path = Path(lines[0].removeprefix("worktree "))
    row = {"path": str(path).replace(str(common), "<repo>"), "metadata": lines[1:]}
    if path.exists():
        try:
            row["status"] = git("status", "--porcelain", cwd=path).splitlines()
        except subprocess.CalledProcessError as exc:
            row["status"] = f"GIT_STATUS_UNAVAILABLE_EXIT_{exc.returncode}"
    else:
        row["status"] = "NOT_PRESENT"
    worktrees.append(row)

resources = json.loads(subprocess.run(["node", "-e", "const o=require('os');console.log(JSON.stringify({freeGiB:o.freemem()/2**30,totalGiB:o.totalmem()/2**30,logicalCPUs:o.availableParallelism()}))"], capture_output=True, text=True, check=True).stdout)
result = {"head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
          "main": git("rev-parse", "main"), "merge_base": git("merge-base", "main", "HEAD"),
          "worktrees": worktrees, "resources": resources, "provider_calls": 0}
target = OUT / (Path(sys.argv[1]).name if len(sys.argv) > 1 else "baseline.json")
if target.exists():
    raise SystemExit("Refusing to overwrite baseline inventory")
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"head": result["head"], "worktrees": len(worktrees), "resources": resources}))
