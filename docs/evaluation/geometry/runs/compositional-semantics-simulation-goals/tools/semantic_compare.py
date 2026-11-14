"""Before/after on the DEVELOPMENT corpora of run `compositional-semantics-simulation-goals` (never a locked W2/W3 row,
never H-1). Each side runs in its own child process with its own backend on PYTHONPATH (same instrument, both sides).

  python semantic_compare.py <before_backend_dir> <out.json>      # from the worktree root, backend interpreter
  python semantic_compare.py --child                               # internal
Corpora: COMP (tools/compositional_dev_corpus.py, this run), DEV37 (previous run's agent corpus), REAL27 (exposed),
PROBES (exposed plane-constraint probes).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
RUNS = RUN.parent
sys.path[:0] = [str(Path(__file__).resolve().parent), str(RUNS / "semantic-failure-safe-image-segmentation/tools"),
                str(RUNS / "independent-geometry-plane-constraints/tools")]


def child() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.adaptive_input_router import route_text_input
    out = {}
    for k, t in json.loads(sys.stdin.read()).items():
        o = route_text_input(t, allow_live_ai=False)
        r = o.response or {}
        rd = r.get("route_d") or {}
        lp = o.local_parse_result
        sc = (r.get("envelope") or {}).get("scene3d") or {}
        objs = sc.get("objects") or []
        kinds = sorted({o2.get("producer", "") for o2 in objs if o2.get("type") == "quantity" and "target" in (o2.get("display_group") or [])})
        out[k] = {"status": rd.get("status") or o.status, "code": (rd.get("refusal") or {}).get("code") or (r.get("envelope") or {}).get("reason_code"),
                  "parse_status": getattr(lp, "status", None), "parse_reason": getattr(lp, "reason_code", None),
                  "fallback_reason": getattr(lp, "fallback_reason", None),
                  "clauses": [{k2: c.get(k2) for k2 in ("index", "start", "end", "classification", "notes")}
                              for c in (lp.source_coverage.clauses if lp else ())],
                  "answers": rd.get("answers") if rd.get("status") == "SERVED" else None,
                  "target_producers": kinds, "sections": sum(o2["type"] == "section" for o2 in objs),
                  "source_goal_completion": rd.get("source_goal_completion"),
                  "local_diagnostics": {k2: (rd.get("local_diagnostics") or {}).get(k2) for k2 in ("root_cause", "first_loss_stage", "layer")}}
    print(json.dumps(out, ensure_ascii=False, default=str))


def run(backend: Path, texts: dict) -> dict:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--child"], input=json.dumps(texts, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8")
    if res.returncode:
        raise SystemExit(res.stderr[-3000:])
    return json.loads(res.stdout.strip().splitlines()[-1])


def corpora() -> dict[str, dict[str, dict]]:
    from compositional_dev_corpus import CORPUS as COMP
    from semantic_eval import corpora as prev
    c = prev()
    return {"COMP": COMP, "DEV37": c["DEV"], "REAL27": c["REAL27"], "PROBES": c["PROBES"]}


def main(before: Path, out: Path) -> int:
    cs = corpora()
    texts = {f"{n}:{k}": v["text"] for n, items in cs.items() for k, v in items.items()}
    res = {"before": run(before, texts), "after": run(ROOT / "backend", texts)}
    rows = {}
    for key, t in texts.items():
        n, k = key.split(":", 1)
        rows[key] = {"corpus": n, "id": k, "group": cs[n][k].get("group"), "expect": cs[n][k].get("expect"),
                     "goal": cs[n][k].get("goal"), "numeric": cs[n][k].get("numeric"), "same_as": cs[n][k].get("same_as"),
                     "pair": cs[n][k].get("pair"), "text_sha256": hashlib.sha256(t.encode("utf-8")).hexdigest(),
                     "before": res["before"][key], "after": res["after"][key]}
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for n in cs:
        sb = sum(r["before"]["status"] == "SERVED" for r in rows.values() if r["corpus"] == n)
        sa = sum(r["after"]["status"] == "SERVED" for r in rows.values() if r["corpus"] == n)
        print(n, len(cs[n]), "served", sb, "->", sa)
    for key, r in rows.items():
        if r["before"]["status"] != r["after"]["status"] or r["before"]["answers"] != r["after"]["answers"]:
            print("  CHANGED", key, r["before"]["status"], r["before"]["code"], "->", r["after"]["status"], r["after"]["code"],
                  "| expect", r["expect"])
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        child()
        raise SystemExit(0)
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
