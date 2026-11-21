"""Local parser latency, before vs after, same machine, same inputs, interleaved.

BEFORE = backend/app exported with `git archive` at the previous run's HEAD into a scratch directory (no worktree);
AFTER = this checkout. Each side runs in its own child process (`measure` mode) so the two code bases never share
an import. Inputs: the 23 controlled-vision polyhedron transcriptions + the 2 fresh items. `use_cache=False`, the
parser's own Stage 8 (bridge, planner, Source Gate) included.  Run from backend/:
    python <tools>/parser_latency.py <before_backend_dir>
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
BEFORE_REF = "c5bb73f51"
ROUNDS, REPEAT = 5, 10


def statements() -> list[str]:
    prior = json.loads((RUN.parent / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    fresh = json.loads((RUN / "fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
    scope = {c["case_id"] for c in json.loads((RUN / "text_to_geometry_before_after.json").read_text(encoding="utf-8"))["cases"]
             if "OUT_OF_SCOPE" not in (c["before"]["outcome"], c["after"]["outcome"])}
    return [i["statement"] for i in prior if i["case_id"] in scope] + [i["statement"] for i in fresh]


def measure() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.local_geometry_parser import parse_geometry_problem_locally as parse
    texts = json.loads(sys.stdin.read())
    for t in texts:  # warm imports and regex compilation
        parse(t, use_cache=False)
    out = []
    for t in texts:
        samples = []
        for _ in range(REPEAT):
            t0 = time.perf_counter()
            parse(t, use_cache=False)
            samples.append((time.perf_counter() - t0) * 1000)
        out.append(samples)
    print(json.dumps(out))


def side(backend: Path, texts: list[str]) -> list[list[float]]:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--measure"], input=json.dumps(texts), capture_output=True, text=True,
                         cwd=backend, env=env, encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def main() -> int:
    before_dir, texts = Path(sys.argv[1]), statements()
    acc = {"before": [[] for _ in texts], "after": [[] for _ in texts]}
    for _ in range(ROUNDS):  # interleaved so drift in machine load hits both sides
        for name, backend in (("before", before_dir), ("after", ROOT / "backend")):
            for i, samples in enumerate(side(backend, texts)):
                acc[name][i].extend(samples)
    med = {k: [statistics.median(s) for s in v] for k, v in acc.items()}
    allv = {k: sorted(x for s in v for x in s) for k, v in acc.items()}
    p95 = {k: v[int(0.95 * (len(v) - 1))] for k, v in allv.items()}
    ratio = [a / b for a, b in zip(med["after"], med["before"]) if b > 0]
    (RUN / "parser_latency_before_after.json").write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "before_ref": BEFORE_REF,
        "method": f"{ROUNDS} interleaved rounds x {REPEAT} calls per statement per side, separate child processes, use_cache=False, warm imports",
        "statements": len(texts), "samples_per_side": len(allv["before"]),
        "median_of_statement_medians_ms": {k: statistics.median(v) for k, v in med.items()},
        "p95_all_calls_ms": p95, "max_all_calls_ms": {k: v[-1] for k, v in allv.items()},
        "after_over_before_median_ratio": {"median": statistics.median(ratio), "max": max(ratio), "min": min(ratio)},
        "per_statement_median_ms": [{"before": b, "after": a} for b, a in zip(med["before"], med["after"])],
        "limits": ["single Windows desktop, background load not controlled", "parser only; OCR time is unchanged code"]},
        indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: statistics.median(v) for k, v in med.items()}), "ratio", round(statistics.median(ratio), 3), "p95", p95)
    return 0


if __name__ == "__main__":
    if "--measure" in sys.argv:
        measure()
    else:
        raise SystemExit(main())
