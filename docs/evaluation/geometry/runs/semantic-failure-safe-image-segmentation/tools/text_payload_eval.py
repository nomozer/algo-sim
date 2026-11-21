"""Text-negative vs payload-negative safety, each through ITS OWN boundary (run `semantic-failure-safe-image-segmentation`).

TRACK A — the input is problem TEXT with a real fault in the text (route_text_input, local-first, ALLOW_LIVE_AI=0).
TRACK B — the input is an extraction PAYLOAD with a fault (a corrupted typed-fact-next/2 payload of a valid text), sent
through the boundary the Source Gate guards (`run_typed_fact_next_v2_route`: schema → bridge → Source Gate → planner).
Payloads are derived from the local parser's own payload of a served development text, then corrupted one way each.
The historical W2/W3 receipts are untouched; this replaces nothing there.  Run from the worktree root.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""

from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from app.ai.local_geometry_parser import parse_geometry_problem_locally  # noqa: E402

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
TEXT_NEGATIVES = {
    "contradiction": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, AB = 2a, SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABCD.",
    "missing_data": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.",
    "invalid_point_definition": P + "Gọi M là trung điểm của SZ. Tính khoảng cách từ M đến mặt phẳng (SBC).",
    "unsatisfiable_relation": P + "SB vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.",
    "plane_not_unique": P + "Mặt phẳng (P) chứa AB và song song với CD. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).",
    "nonexistent_object": P + "Tính khoảng cách từ A đến mặt phẳng (XYZ).",
    "unsupported_goal": P + "Tính côsin của góc giữa đường thẳng SC và mặt phẳng (ABCD).",
    "goal_stated_as_premise": P + "Thể tích khối chóp S.ABCD bằng a³/3. Tính độ dài SC.",
}
BASE = P + "Gọi M là trung điểm của SC. Tính khoảng cách từ M đến mặt phẳng (SAB)."
OTHER = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2a."


def _first(p, kind):
    return next(x for x in p["premises"] if x["kind"] == kind)


def corruptions(p: dict) -> dict:
    out = {}
    q = copy.deepcopy(p); _first(q, "segment_length")["quote"] = "SA = 7a"; out["quote_not_in_source"] = q
    q = copy.deepcopy(p); q["premises"] = [x for x in q["premises"] if x["kind"] not in ("perpendicular_line_plane", "line_perp_plane")]; out["clause_dropped"] = q
    q = copy.deepcopy(p); _first(q, "segment_length")["args"]["value"] = "2a"; out["value_substituted"] = q
    q = copy.deepcopy(p); m = _first(q, "midpoint"); m["args"]["segment"] = ["S", "B"]; out["symbol_differs_from_text"] = q
    q = copy.deepcopy(p); q["verified"] = True; out["forged_verified_flag"] = q
    q = copy.deepcopy(p); q["premises"].append({"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2a"}, "quote": OTHER, "solid_id": q["solids"][0]["solid_id"]}); out["fact_from_another_problem"] = q
    q = copy.deepcopy(p); g = q["math_goals"][0]; g["target"] = {"point": "M", "plane": ["X", "Y", "Z"]}; out["nonexistent_entity"] = q
    q = copy.deepcopy(p); q["problem_text"] = q["problem_text"].split(" Gọi M")[0]; out["source_truncated"] = q
    return out


def main() -> int:
    a_rows = {}
    for k, t in TEXT_NEGATIVES.items():
        r = route_text_input(t, allow_live_ai=False).response
        rd = r["route_d"]
        a_rows[k] = {"status": rd["status"], "terminal": (rd.get("refusal") or {}).get("code"),
                     "root_cause": (rd.get("local_diagnostics") or {}).get("root_cause"), "safe": rd["status"] != "SERVED"}
    base = parse_geometry_problem_locally(BASE, use_cache=False)
    assert base.payload is not None
    control = run_typed_fact_next_v2_route(copy.deepcopy(base.payload))
    b_rows = {}
    for k, q in corruptions(base.payload).items():
        try:
            res = run_typed_fact_next_v2_route(q)
            b_rows[k] = {"status": res.status, "code": res.code, "safe": res.status != "SERVED"}
        except Exception as e:                                       # noqa: BLE001 — a raise at the boundary is a refusal
            b_rows[k] = {"status": "RAISED", "code": type(e).__name__, "safe": True}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "head": head,
            "environment": {"ALLOW_LIVE_AI": "0"}, "command": "python docs/evaluation/geometry/runs/semantic-failure-safe-image-segmentation/tools/text_payload_eval.py",
            "dataset_partition": "DEVELOPMENT (agent-written texts and payloads derived from them)",
            "oracle_status": "AGENT_DIAGNOSTIC: each negative is a fault by construction",
            "track_a_text": {"boundary": "route_text_input (text → local parser → Source Gate → planner → kernel)", "rows": a_rows,
                             "served": sum(not r["safe"] for r in a_rows.values()), "items": len(a_rows)},
            "track_b_payload": {"boundary": "run_typed_fact_next_v2_route (payload → schema → bridge → Source Gate → planner → kernel)",
                                "valid_text_control": {"text_sha": __import__("hashlib").sha256(BASE.encode()).hexdigest()[:16], "status": control.status},
                                "rows": b_rows, "served": sum(not r["safe"] for r in b_rows.values()), "items": len(b_rows)},
            "historical_w2_w3": "unchanged: W2 2/48, W3 0/72 positives served correctly and 2 WRONG_SERVED under the registered rule (independent-geometry-plane-constraints/unseen_evaluation_results.json); its post-hoc note explains that both were payload-origin negatives sent as text. The split above is the corrected method for new measurements only."}
    (RUN / "text_vs_payload_negative_evaluation.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("A", {k: (v["status"], v["terminal"], v["root_cause"]) for k, v in a_rows.items()})
    print("control", control.status, "B", {k: (v["status"], v["code"]) for k, v in b_rows.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
