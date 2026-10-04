# -*- coding: utf-8 -*-
"""Run every W18 backend fault injection (`fault_injection_w18.INJECTIONS`) — baseline first (must be
all green), one pytest process per injection, baseline again. Writes `logs/FAULT_INJECTION_W18<suffix>.log`
(`suffix` = first argument); refuses to overwrite. 0 model calls. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/run_fault_injections_w18.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[5] / "backend"
OUT = HERE / "logs" / f"FAULT_INJECTION_W18{sys.argv[1] if len(sys.argv) > 1 else ''}.log"
TESTS = ["tests/geometry/test_construction_binding.py", "tests/geometry/test_scene3d_annotations.py",
         "tests/test_learner_messages.py"]

sys.path.insert(0, str(HERE))
from fault_injection_w18 import INJECTIONS  # noqa: E402


def chay(fi: str | None) -> tuple[str, list[str]]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(HERE), "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("W18_FI", None)
    if fi:
        env["W18_FI"] = fi
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p",
                        "fault_injection_w18", "--tb=no", "-rf", *TESTS],
                       cwd=BACKEND, env=env, capture_output=True, text=True, encoding="utf-8")
    dong = r.stdout.strip().splitlines()
    tom = next((x for x in reversed(dong) if re.search(r"\d+ (passed|failed)", x)), dong[-1] if dong else "")
    if "FAULT INJECTION STALE" in r.stdout + r.stderr:
        tom = "STALE INJECTION — " + (r.stdout + r.stderr).split("FAULT INJECTION STALE", 1)[1][:120]
    hong = [x.split(" ", 1)[1].split(" - ")[0].rsplit("/", 1)[-1] for x in dong if x.startswith("FAILED ")]
    return tom, hong


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    head = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=BACKEND, capture_output=True,
                          text=True).stdout.strip()
    ra = [f"W18 — backend fault injections (HEAD {head} + working tree, 0 model calls)",
          "method: one exact in-memory source substitution per run (fault_injection_w18.py, W15 _tiem); "
          "files on disk are never edited, so 'revert' = the next run without W18_FI",
          f"tests: {' '.join(TESTS)}", ""]
    tom, hong = chay(None)
    ra += [f"baseline (no injection): {tom}", *(f"  FAILED {h}" for h in hong), ""]
    for fi, (mod, _cu, _moi, mo_ta, du_doan) in INJECTIONS.items():
        tom, hong = chay(fi)
        ra += [f"{fi} [{mod.rsplit('.', 1)[-1]}] {mo_ta}", f"  predicted: {du_doan}",
               f"  observed : {tom} -> {'CAUGHT' if hong else 'NOT CAUGHT'}",
               *(f"    FAILED {h}" for h in hong[:12]),
               *([f"    … and {len(hong) - 12} more"] if len(hong) > 12 else []), ""]
    tom, hong = chay(None)
    ra += [f"after all injections (no injection again): {tom}", *(f"  FAILED {h}" for h in hong)]
    OUT.write_text("\n".join(ra) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(ra))


if __name__ == "__main__":
    main()
