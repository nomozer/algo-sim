# -*- coding: utf-8 -*-
"""Run every W20 fault injection (`fault_injection_w20.INJECTIONS`) — baseline first (must be all green), one
pytest process per injection, baseline again. Writes `results/logs/FAULT_INJECTION_W20<suffix>.log` (`suffix` =
first argument); refuses to overwrite. 0 model calls. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/run_fault_injections_w20.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[5] / "backend"
OUT = HERE.parent / "results" / "logs" / f"FAULT_INJECTION_W20{sys.argv[1] if len(sys.argv) > 1 else ''}.log"
TESTS = ["tests/geometry/test_construction_binding_literal.py", "tests/geometry/test_construction_binding.py",
         "tests/test_learner_messages.py", "tests/geometry/test_second_family_live_measurement_reconciliation.py"]

sys.path.insert(0, str(HERE))
from fault_injection_w20 import INJECTIONS  # noqa: E402


def chay(fi: str | None) -> tuple[str, list[str], dict]:
    with tempfile.TemporaryDirectory() as td:
        st = Path(td) / "stages.json"
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(HERE), "PYTHONDONTWRITEBYTECODE": "1",
               "W20_STAGES": str(st)}
        env.pop("W20_FI", None)
        if fi:
            env["W20_FI"] = fi
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p",
                            "fault_injection_w20", "--tb=no", "-rf", *TESTS],
                           cwd=BACKEND, env=env, capture_output=True, text=True, encoding="utf-8")
        stages = json.loads(st.read_text(encoding="utf-8")) if st.exists() else {}
    dong = r.stdout.strip().splitlines()
    tom = next((x for x in reversed(dong) if re.search(r"\d+ (passed|failed)", x)), dong[-1] if dong else "")
    if "FAULT INJECTION STALE" in r.stdout + r.stderr:
        tom = "STALE INJECTION — " + (r.stdout + r.stderr).split("FAULT INJECTION STALE", 1)[1][:120]
    hong = [x.split(" ", 1)[1].split(" - ")[0].rsplit("/", 1)[-1] for x in dong if x.startswith("FAILED ")]
    return tom, hong, stages


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    head = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=BACKEND, capture_output=True,
                          text=True).stdout.strip()
    ra = [f"W20 — §17 fault injections (HEAD {head} + working tree, 0 model calls)",
          "method: one exact in-memory source substitution per run (fault_injection_w20.py, W15 _tiem); "
          "files on disk are never edited, so 'revert' = the next run without W20_FI",
          f"tests: {' '.join(TESTS)}", ""]
    tom, hong, goc = chay(None)
    ra += [f"baseline (no injection): {tom}", *(f"  FAILED {h}" for h in hong), ""]
    for fi, (mod, _cu, _moi, mo_ta, du_doan) in INJECTIONS.items():
        tom, hong, stages = chay(fi)
        ra += [f"{fi} [{mod.rsplit('.', 1)[-1]}] {mo_ta}", f"  predicted: {du_doan}",
               f"  observed : {tom} -> {'CAUGHT' if hong else 'NOT CAUGHT'}",
               *(f"    FAILED {h}" for h in hong[:14]),
               *([f"    … and {len(hong) - 14} more"] if len(hong) > 14 else [])]
        doi = {ca: (goc.get(ca), v) for ca, v in stages.items() if goc.get(ca) != v}
        ra += [f"  route outcome changed vs baseline ({len(doi)} rows):",
               *(f"    {ca}: {b} -> {a}" for ca, (b, a) in sorted(doi.items())), ""]
    tom, hong, _ = chay(None)
    ra += [f"after all injections (no injection again): {tom}", *(f"  FAILED {h}" for h in hong)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(ra) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(ra))


if __name__ == "__main__":
    main()
