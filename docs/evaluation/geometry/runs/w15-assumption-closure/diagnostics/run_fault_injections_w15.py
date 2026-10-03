# -*- coding: utf-8 -*-
"""Run every W15 fault injection (`fault_injection_w15.INJECTIONS`) against the W15 gate tests.

Baseline first (no injection: must be all green), then one pytest process per injection.
Writes `logs/FAULT_INJECTION_ASSUMPTION_GATE.log`; refuses to overwrite it. 0 model calls.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[5] / "backend"
OUT = HERE / "logs" / "FAULT_INJECTION_ASSUMPTION_GATE.log"
TESTS = ["tests/geometry/test_assumption_gate.py", "tests/geometry/test_assumption_certificate.py",
         "tests/geometry/test_shape_constraint.py", "tests/geometry/test_shape_class_formation.py"]

sys.path.insert(0, str(HERE))
from fault_injection_w15 import INJECTIONS  # noqa: E402


def chay(fi: str | None) -> tuple[str, list[str]]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(HERE), "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("W15_FI", None)
    if fi:
        env["W15_FI"] = fi
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p",
                        "fault_injection_w15", "--tb=no", "-rf", *TESTS],
                       cwd=BACKEND, env=env, capture_output=True, text=True, encoding="utf-8")
    dong = r.stdout.strip().splitlines()
    tom = next((x for x in reversed(dong) if re.search(r"\d+ (passed|failed)", x)), dong[-1] if dong else "")
    if "FAULT INJECTION STALE" in r.stdout + r.stderr:
        tom = "STALE INJECTION — " + (r.stdout + r.stderr).split("FAULT INJECTION STALE", 1)[1][:120]
    hong = []
    for x in dong:
        if x.startswith("FAILED "):
            tep, _, ten = x.split(" ", 1)[1].split(" - ")[0].partition("::")
            hong.append(f"{tep.rsplit('/', 1)[-1]}::{ten}")
    return tom, hong


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=BACKEND, capture_output=True,
                          text=True).stdout.strip()
    ra = [f"W15 Task 6 — fault injections on the assumption gate (HEAD {head} + working tree, "
          "0 model calls)",
          "method: one exact in-memory source substitution per run (fault_injection_w15.py); the files on "
          "disk are never edited, so 'revert' = the next run without W15_FI",
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
