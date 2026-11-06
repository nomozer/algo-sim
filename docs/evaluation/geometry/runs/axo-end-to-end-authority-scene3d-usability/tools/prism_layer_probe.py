"""Layer-by-layer probe of the right-prism volume problem (oracle V = (3*4/2)*5 = 30, fixed before running).

Offline (default, 0 model calls):  python <this> --offline <fresh out.json>
  Runs hand-written TypedFactNext /2 payloads — the reference reading plus plausible alternative extractions of the same
  text — through the product route (`run_hybrid_offline` + ReplayExtractor, same code as /api/analyze after extraction)
  and records each layer: text, typed facts, bridged facts, planner program, kernel/answer, certificate trace, Scene3D
  quantity, Adapter /4 status.

Live (NOT run by this task; needs owner GO and budget):  ALLOW_LIVE_AI=1 python <this> --live --max-calls 1 <fresh out.json>
  Exactly one provider extraction of the same text, then the identical offline layers on the extracted payload, plus a
  structural diff against the reference payload. Never prints or stores the API key, request headers or raw provider
  body; stores only the normalized payload and layer outputs. The first differing layer is reported.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402

TEXT = ("Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. Cạnh bên AD = 5. "
        "Tính thể tích khối lăng trụ ABC.DEF.")
ORACLE = "30"


def reference() -> dict:
    solid, shape, question = "Cho hình lăng trụ đứng ABC.DEF", "đáy ABC là tam giác vuông tại A", "Tính thể tích khối lăng trụ ABC.DEF."
    return {"schema_version": "typed-fact-next/2", "problem_text": TEXT, "length_unit": "1",
            "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": "ABC.DEF", "quote": solid}],
            "premises": [{"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": shape},
                         {"kind": "right_prism", "args": {"base": list("ABC"), "top": list("DEF")}, "quote": solid},
                         {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3"},
                         {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "quote": "AC = 4"},
                         {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "5"}, "quote": "AD = 5"}],
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "pr", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "pr"},
                            "quote": question}]}


def variants() -> dict[str, dict]:
    """Plausible alternative extractions of TEXT (what a model may emit), each a valid /2 payload."""
    out = {"reference": reference()}
    v = reference(); v["premises"][0] = {"kind": "base_is_right_triangle",
                                         "args": {"vertices": list("ABC"), "right_at": "A"},
                                         "quote": "đáy ABC là tam giác vuông tại A"}
    out["right-triangle-as-base-shape"] = v
    v = reference(); v["premises"][4] = {"kind": "height", "args": {"value": "5", "solid": "pr"}, "quote": "Cạnh bên AD = 5"}
    out["lateral-edge-as-height"] = v
    v = reference(); v["premises"] = [p for p in v["premises"] if p["kind"] != "right_prism"]
    out["right-prism-dropped"] = v            # mis-extraction: "đứng" lost ⇒ must refuse, never serve 30
    v = reference(); v["premises"][4]["quote"] = "Cạnh bên AD = 5"
    out["wider-quote"] = v
    v = reference(); v["premises"].append({"kind": "perpendicular_line_plane", "args": {"line": ["A", "D"], "plane": list("ABC")},
                                          "quote": "Cho hình lăng trụ đứng ABC.DEF"})
    out["redundant-lateral-perpendicular"] = v
    return out


def layers(payload: dict) -> dict:
    policy = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    product = run_hybrid_offline(payload["problem_text"], ReplayExtractor({payload["problem_text"]: copy.deepcopy(payload)}),
                                 policy=policy).response
    r = run_typed_fact_next_v2_route(copy.deepcopy(payload))
    scene = (product.get("envelope") or {}).get("scene3d") or {}
    quantity = next((o for o in scene.get("objects", []) if o.get("id") == "kq_q"), None)
    return {
        "1_text": payload["problem_text"],
        "2_typed_facts": payload,
        "3_planner_program": (r.planner or {}).get("calls"),
        "4_kernel": {"status": r.status, "code": r.code, "kernel_check": r.kernel_check, "answer_exact": r.answer_exact},
        "5_certificates": [t for t in (r.trace or []) if t.get("step") in ("verify_shape_assertion", "measure")],
        "6_scene_quantity": quantity and {k: quantity.get(k) for k in ("id", "value", "exact", "producer", "source")},
        "7_adapter4": {"status": product["route_d"]["status"], "reason_code": product["envelope"].get("reason_code"),
                       "failure_category": product["envelope"].get("failure_category"),
                       "answers": product["route_d"].get("answers")},
        "response": product,
        "oracle_match": r.status == "SERVED" and (r.answer_exact.get("q") or {}).get("coef") == ORACLE,
    }


def main() -> None:
    mode, out = sys.argv[1], Path(sys.argv[-1])
    if mode == "--offline":
        rows = {name: layers(p) for name, p in variants().items()}
    elif mode == "--live":
        if os.environ.get("ALLOW_LIVE_AI") != "1" or "--max-calls" not in sys.argv or sys.argv[sys.argv.index("--max-calls") + 1] != "1":
            raise SystemExit("LIVE_NOT_AUTHORIZED: needs ALLOW_LIVE_AI=1 and --max-calls 1 (owner GO + budget)")
        from app.ai.hybrid_offline import _live_provider_transport, prepare_live_hybrid
        from app.ai.typed_fact_next_extraction import TransportExtractor
        job = prepare_live_hybrid(TEXT)
        key = os.environ["GEMINI_API_KEY"]
        extracted = TransportExtractor(_live_provider_transport(key, model=job.model, timeout_seconds=60.0,
                                                                deadline_seconds=180.0)).extract(TEXT)
        rows = {"live": {"model": job.model, **layers(extracted)}, "reference": layers(reference())}
        ref, live = rows["reference"], rows["live"]
        rows["first_divergent_layer"] = next((k for k in ("2_typed_facts", "3_planner_program", "4_kernel",
                                                          "6_scene_quantity", "7_adapter4") if ref[k] != live[k]), None)
    else:
        raise SystemExit("usage: --offline <out> | --live --max-calls 1 <out>")
    with out.open("x", encoding="utf-8") as s:
        json.dump({"oracle": ORACLE, "derivation": "(3*4/2)*5", "rows": rows}, s, ensure_ascii=False, indent=1)
    print(json.dumps({k: (v["7_adapter4"]["status"], v["4_kernel"]["code"], v["oracle_match"]) for k, v in rows.items()
                      if isinstance(v, dict)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
