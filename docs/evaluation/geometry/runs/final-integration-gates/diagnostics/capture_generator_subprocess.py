"""Diagnostic pytest plugin (load with -p capture_generator_subprocess). Changes no test and no assertion.

For test_cross_section_fixture_preserves_verifiable_measurement_provenance only: wraps subprocess.run, records
exit code, stdout, stderr, the environment the child inherits, and the environment keys that drifted from the
session start, then re-raises exactly what the original call raised. One JSON line per invocation.
"""
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

OUT = Path(os.environ["DIAG_GENERATOR_OUT"])
_SESSION_ENV = dict(os.environ)
_TARGET = "test_cross_section_fixture_preserves_verifiable_measurement_provenance"


@pytest.fixture(autouse=True)
def _capture_generator(request, monkeypatch):
    if request.node.name != _TARGET:
        yield
        return
    original = subprocess.run

    def traced(*args, **kwargs):
        rec = {"t": time.time(), "args": [str(a) for a in (args[0] if args else kwargs.get("args"))],
               "cwd": str(kwargs.get("cwd")),
               "env_drift": {k: [_SESSION_ENV.get(k), os.environ.get(k)]
                             for k in sorted(set(_SESSION_ENV) | set(os.environ))
                             if _SESSION_ENV.get(k) != os.environ.get(k)},
               "env_selected": {k: os.environ.get(k) for k in (
                   "DATABASE_URL", "GEOMETRY_COMPILER_MODE", "ALLOW_LIVE_AI", "PYTHONIOENCODING", "PYTHONUTF8",
                   "SEMANTIC_ROUTE_MODE", "GEMINI_API_KEY")}}
        rec["env_selected"]["GEMINI_API_KEY"] = "SET" if rec["env_selected"]["GEMINI_API_KEY"] else None
        try:
            res = original(*args, **kwargs)
            rec.update(exit=res.returncode, stdout=(res.stdout or "")[-4000:], stderr=(res.stderr or "")[-8000:])
            return res
        except subprocess.CalledProcessError as e:
            rec.update(exit=e.returncode, stdout=(e.stdout or "")[-4000:], stderr=(e.stderr or "")[-8000:],
                       raised="CalledProcessError")
            raise
        except Exception as e:  # noqa: BLE001
            rec.update(raised=f"{type(e).__name__}: {e}")
            raise
        finally:
            out_dir = next((Path(a) for a in rec["args"][rec["args"].index("--out") + 1:][:1]), None) \
                if "--out" in rec["args"] else None
            rec["out_files"] = sorted(p.name for p in out_dir.rglob("*")) if out_dir and out_dir.exists() else None
            with OUT.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    monkeypatch.setattr(subprocess, "run", traced)
    yield
