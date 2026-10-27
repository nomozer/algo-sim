# -*- coding: utf-8 -*-
"""Re-score the registered development corpus of `hybrid-v2-planner-generalization` on the CURRENT checkout, writing into
THIS run (the predecessor run's files are never written). Offline, 0 provider calls. AUTHORED_DEVELOPMENT_NOT_HOLDOUT.

Run from `backend/`:  python <this file> <out.json>
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.function_route import run_fact_route  # noqa: E402
from app.simulation.geometry_functions import planner, registry  # noqa: E402

PRED = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-planner-generalization"
ROWS = json.loads((PRED / "inputs/development.json").read_text(encoding="utf-8"))["cases"]
ORACLE = json.loads((PRED / "inputs/oracle.json").read_text(encoding="utf-8"))


def main(out: Path) -> None:
    rows = []
    for r in ROWS:
        res = run_fact_route(r["text"], deepcopy(r["payload"]))
        row = {"id": r["id"], "expected": r["expected_status"], "status": res.status, "code": res.code}
        if res.status == "SERVED":
            v = res.exec_result.final_memory["kq_q"]
            sq = F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2
            row["area_squared"] = str(sq)
            row["oracle_area_squared"] = ORACLE.get(r["id"], {}).get("area_squared")
            row["oracle_agree"] = row["oracle_area_squared"] is not None and F(row["oracle_area_squared"]) == sq
        else:
            row["reason_ok"] = res.code in r.get("expected_codes", [])
        rows.append(row)
    pos = [x for x in rows if x["expected"] == "SERVED"]
    neg = [x for x in rows if x["expected"] == "REFUSED"]
    agg = {"registry": registry.REGISTRY_VERSION, "planner": planner.PLANNER_VERSION,
           "positives_served": f"{sum(x['status'] == 'SERVED' for x in pos)}/{len(pos)}",
           "oracle_agreement": f"{sum(bool(x.get('oracle_agree')) for x in pos)}/{len(pos)}",
           "negatives_refused_with_registered_code": f"{sum(x['status'] == 'REFUSED' and x['reason_ok'] for x in neg)}/{len(neg)}",
           "wrong_served": sum(x["status"] == "SERVED" and (x["expected"] == "REFUSED" or not x.get("oracle_agree")) for x in rows)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"classification": "AUTHORED_DEVELOPMENT_NOT_HOLDOUT", "provider_calls": 0, "aggregate": agg,
                               "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
