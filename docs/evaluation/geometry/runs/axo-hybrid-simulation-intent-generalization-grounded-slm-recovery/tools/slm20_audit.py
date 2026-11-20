"""SLM20 causal audit + multi-arm gold intervention for the 20 SLM-route refusals of /10 pass 2 (+ the 4 non-SLM refusals).

Real AxoV9 GGUF via the product LocalSlmRuntime; every arm goes through the REAL Source Gate / planner / engine / adapter
(`run_hybrid_offline`). No arm is production-served: this is a diagnostic harness.
  A  product route (`route_text_input_local_slm`, v9, no cache)
  B  the SLM's own lowered payload through the downstream route (= A's downstream, isolated)
  D  same SLM facts, simulation goal representation replaced by gold intent (SIMULATE_ONLY ⇒ math_goals = [])
  C  deterministic-parser payload of the ORIGINAL text + gold intent (only when the parser built a payload)
  E  downstream capability: full deterministic route on a minimal canonical rephrase of the same geometry, oracle-checked
usage (from backend/): python <this> <out.json> [--ids V08,V05]
"""

import copy
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
RUN = Path(__file__).resolve().parents[1]
R10 = RUN.parent / "axo-hybrid-local-only-3d-simulation-live-acceptance-cutover"
sys.path.insert(0, str(RUN / "tools"))
import scene_oracle as so  # noqa: E402

from app.ai.adaptive_input_router import route_text_input_local_slm  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import run_local_slm_extraction, V9_CLOSURE_MODE  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402

CANON = {  # Arm E: minimal canonical rephrase (same geometry, command/question in parser-known form)
    "V02": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với đáy và SA = 3a. Hãy mô phỏng hình chóp.",
    "V05": "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng a. Hãy mô phỏng hình chóp.",
    "V06": "Cho tứ diện đều ABCD cạnh a. Hãy mô phỏng hình.",
    "V08": "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Hãy mô phỏng hình.",
    "V09": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3, AA' = 4. Hãy mô phỏng hình.",
    "V10": "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác ABC vuông cân tại A, AB = AC = a, cạnh bên AA' = 2a. Hãy mô phỏng hình lăng trụ.",
    "V11": "Cho lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng a và cạnh bên bằng a. Hãy mô phỏng hình lăng trụ.",
    "V14": "Cho hình chóp S.ABC có đáy là tam giác ABC cân tại A, AB = AC = a, góc BAC = 120°, SA vuông góc với đáy, SA = 2a. Hãy mô phỏng hình chóp.",
    "V16": "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = a, BC = 2a. Cạnh bên SA vuông góc với mặt phẳng đáy và SA = 2a. Gọi M là trung điểm của cạnh SD và N là trung điểm của cạnh SC. Hãy mô phỏng hình chóp.",
    "V19": "Cho tứ diện ABCD có AB, AC, AD đôi một vuông góc, AB = AC = AD = a. Hãy mô phỏng hình.",
    "V26": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = a, AD = 2a, AA' = 3a. Hãy mô phỏng hình.",
    "V28": "Cho hình chóp đều S.ABC có cạnh đáy bằng a, cạnh bên bằng a√2. Hãy mô phỏng hình chóp.",
    "Q03": "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Tính khoảng cách giữa hai đường thẳng AA' và BD.",
    "Q04": "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = a, AD = a√3, SA ⊥ (ABCD), SA = a. Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
    "Q05": "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2a, SA vuông góc với đáy, SA = 2a. Tính khoảng cách từ S đến mặt phẳng (ABCD).",
    "Q08": "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 1, AD = 2, AA' = 2. Tính độ dài đoạn thẳng AC'.",
    "Q10": "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = a, AC = 2a, SA vuông góc với (ABC), SA = 2a. Tính thể tích khối chóp S.ABC.",
    "C03": "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng a. Tính thể tích khối chóp S.ABCD.",
    "C25": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với đáy, SA = 3. Tính thể tích khối chóp S.ABCD.",
    "C26": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD) và SA = a√2. Tính thể tích khối chóp S.ABCD. Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
    "V13": "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành, AB = 2a, AD = a, góc BAD = 60°, SA ⊥ (ABCD) và SA = a. Hãy mô phỏng hình chóp.",
    "V18": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD), SA = a. Hãy mô phỏng hình chóp.",
    "C24": "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC), SA = a. Tính thể tích khối chóp S.ABC.",
    "C20": "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Tính góc giữa hai đường thẳng AB' và BC'.",
}
POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def downstream(text, payload):
    r = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY, timeout_seconds=30)
    rd = r.response.get("route_d") or {}
    env = r.response.get("envelope") or {}
    return {"status": rd.get("status"), "code": (rd.get("refusal") or {}).get("code") or env.get("reason_code"),
            "answers": rd.get("answers"), "failure_stage": r.receipt.get("failure_stage"),
            "source_gate": r.receipt.get("source_gate", {}).get("status"), "response": r.response}


def summarize_route(resp):
    rd = resp.get("route_d") or {}
    return {"status": rd.get("status"), "extraction_mode": rd.get("extraction_mode"),
            "code": (rd.get("refusal") or {}).get("code") or (resp.get("envelope") or {}).get("reason_code") or resp.get("reason_code"),
            "slm_ops": [o.get("kind") for o in (rd.get("slm_grounding_envelope") or {}).get("accepted_ops", [])]}


def oracle(case, resp):
    if (resp.get("route_d") or {}).get("status") != "SERVED":
        return None
    v = so.validate(case, resp)
    return {"scene_validation": v.get("scene_validation"), "issues": v.get("issues"), "numeric": (v.get("numeric") or {}).get("status")}


def main():
    out_path = sys.argv[1]
    ids = sys.argv[sys.argv.index("--ids") + 1].split(",") if "--ids" in sys.argv else list(CANON)
    man = {c["case_id"]: c for c in json.loads((R10 / "LIVE_SIMULATION_ACCEPTANCE_MANIFEST.json").read_text(encoding="utf-8"))["valid_cases"]}
    rows = []
    for cid in ids:
        case = man[cid]; text = case["original_input"]; t0 = time.perf_counter()
        row = {"case_id": cid, "intent": case["simulation_intent"], "input": text}
        lp = parse_geometry_problem_locally(text, use_cache=False)
        cov = lp.source_coverage
        row["parser"] = {"status": lp.status, "reason_code": lp.reason_code, "has_payload": lp.payload is not None,
                         "unparsed_goal": list(getattr(cov, "unparsed_goal_candidates", []) or []),
                         "unparsed_fact": list(getattr(cov, "unparsed_fact_candidates", []) or [])}
        slm = run_local_slm_extraction(text, model_key="v9", closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", use_cache=False)
        env = slm.grounding_envelope or {}
        row["slm"] = {"ok": slm.ok, "reason_code": slm.reason_code, "reason_detail": (slm.reason_detail or "")[:300],
                      "failure_taxonomy": slm.failure_taxonomy, "raw_model_output": slm.inference.raw_content if slm.inference else None,
                      "wire_payload": slm.wire_payload, "grounding_status": env.get("grounding_status"),
                      "accepted_ops": env.get("accepted_ops"), "rejected_ops": env.get("rejected_ops"),
                      "normalization": slm.normalization_provenance, "lowered_payload": slm.canonical_payload}
        a = route_text_input_local_slm(text, model_key="v9", closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", use_cache=False, policy=POLICY)
        row["arm_A_product"] = {**summarize_route(a.response), "oracle": oracle(case, a.response)}
        if slm.canonical_payload:
            b = downstream(slm.norm_text, slm.canonical_payload)
            row["arm_B_slm_payload"] = {k: b[k] for k in ("status", "code", "answers", "failure_stage", "source_gate")} | {"oracle": oracle(case, b["response"])}
            gold = copy.deepcopy(slm.canonical_payload)
            if case["simulation_intent"] == "SIMULATE_ONLY":
                gold["math_goals"] = []
            d = downstream(slm.norm_text, gold)
            row["arm_D_gold_intent"] = {k: d[k] for k in ("status", "code", "answers", "failure_stage", "source_gate")} | {
                "math_goals_removed": len(slm.canonical_payload.get("math_goals") or []) if case["simulation_intent"] == "SIMULATE_ONLY" else 0,
                "oracle": oracle(case, d["response"])}
        else:
            row["arm_B_slm_payload"] = row["arm_D_gold_intent"] = {"status": "NOT_RUN", "why": "SLM output not lowered (no payload)"}
        if lp.payload:
            g = copy.deepcopy(lp.payload)
            if case["simulation_intent"] == "SIMULATE_ONLY":
                g["math_goals"] = []
                g["simulation_goals"] = g.get("simulation_goals") or [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": g["solids"][0]["solid_id"], "quote": g["solids"][0].get("quote", "")}]
            c = downstream(text, g)
            row["arm_C_parser_facts_gold_intent"] = {k: c[k] for k in ("status", "code", "answers", "failure_stage")} | {"oracle": oracle(case, c["response"])}
        else:
            row["arm_C_parser_facts_gold_intent"] = {"status": "NOT_CONSTRUCTED", "why": f"parser built no payload ({lp.status})"}
        if cid in CANON:
            e = route_text_input_local_slm(CANON[cid], model_key="v9", closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", use_cache=False, policy=POLICY)
            row["arm_E_downstream_canonical"] = {"text": CANON[cid], **summarize_route(e.response), "oracle": oracle(case, e.response)}
        row["seconds"] = round(time.perf_counter() - t0, 1)
        rows.append(row)
        print(cid, row["parser"]["status"], "| A", row["arm_A_product"]["status"], row["arm_A_product"]["code"], "| B", row["arm_B_slm_payload"].get("status"),
              row["arm_B_slm_payload"].get("code"), "| D", row["arm_D_gold_intent"].get("status"), row["arm_D_gold_intent"].get("code"),
              "| C", row["arm_C_parser_facts_gold_intent"].get("status"), "| E", row.get("arm_E_downstream_canonical", {}).get("status"),
              row.get("arm_E_downstream_canonical", {}).get("extraction_mode"), (row.get("arm_E_downstream_canonical", {}).get("oracle") or {}).get("scene_validation"), flush=True)
    Path(out_path).write_text(json.dumps({"schema": "axo-slm20-audit/1", "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
