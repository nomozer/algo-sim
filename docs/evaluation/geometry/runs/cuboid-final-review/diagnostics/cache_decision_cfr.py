"""cuboid-final-review — CACHE_VERSION decision (task 6). 0 model calls.

Inputs: the 27 rows of the W20 corpus run through `run_pipeline` with the code at 4048ff83 (end of W20, "before")
and at 284a9bfa (this run's product commit, "after"), by the unchanged W20 tool
`runs/w20-cleanup-premerge/diagnostics/proof_cache_row_w20.py envelopes`; its `prove` output says whether a row
served before is refused after (the stale-cache risk).

This script adds the check this change needs: `main.py` caches only `status == "ok"`, so the decision is safe iff
every served envelope is byte-identical before and after (a cache HIT then returns exactly what the new code serves)
and refusals differ only in fields the API rebuilds or never caches.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/cuboid-final-review/\
diagnostics/cache_decision_cfr.py --before <envelopes before> --after <envelopes after> --proof <PROOF json> --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(env: dict) -> str:
    return hashlib.sha256(json.dumps(env, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    for k in ("before", "after", "proof", "out"):
        ap.add_argument(f"--{k}", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    truoc = json.loads(a.before.read_text(encoding="utf-8"))
    sau = json.loads(a.after.read_text(encoding="utf-8"))
    proof = json.loads(a.proof.read_text(encoding="utf-8"))
    rows = {}
    for ca in truoc:
        e0, e1 = truoc[ca]["envelope"], sau[ca]["envelope"]
        keys = sorted(k for k in set(e0) | set(e1) if e0.get(k) != e1.get(k))
        rows[ca] = {"status_before": e0.get("status"), "status_after": e1.get("status"),
                    "reason_code_after": e1.get("reason_code"), "identical": sha(e0) == sha(e1),
                    "differing_keys": keys,
                    **({"reason_subjects_before": e0.get("reason_subjects"),
                        "reason_subjects_after": e1.get("reason_subjects")} if keys else {})}
    served_changed = [c for c, r in rows.items() if "ok" in (r["status_before"], r["status_after"]) and not r["identical"]]
    status_changed = [c for c, r in rows.items() if r["status_before"] != r["status_after"]]
    refused_other_keys = [c for c, r in rows.items() if r["status_after"] != "ok"
                          and set(r["differing_keys"]) - {"reason_subjects"}]
    safe = not (served_changed or status_changed or refused_other_keys or proof["stale_rows_replayed_under_current_version"])
    out = {
        "decision": "CACHE_DECISION_CFR",
        "model_calls": 0,
        "before": "4048ff83 (end of W20; detached worktree D:/tmp/cfr-before)",
        "after": "284a9bfa (product commit of cuboid-final-review)",
        "cache_version_current": proof["cache_version_current"],
        "w20_prove_stale_rows": proof["stale_rows_replayed_under_current_version"],
        "served_envelopes_changed": served_changed,
        "status_changed": status_changed,
        "refused_rows_differing_beyond_reason_subjects": refused_other_keys,
        "rows": rows,
        "CACHE_DECISION": ("NO_BUMP — every served envelope is byte-identical before and after, no status changes, and "
                           "refusals (never cached: main.py writes only status == \"ok\", pinned by "
                           "test_api.py::test_khong_cache_ket_qua_unsupported) differ only in reason_subjects; the "
                           "learner message and the card label are rebuilt on every response")
                          if safe else "BUMP — see the lists above",
    }
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("served_envelopes_changed", "status_changed",
                                          "refused_rows_differing_beyond_reason_subjects", "CACHE_DECISION")},
                     ensure_ascii=False, indent=1))
    return 0 if safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
