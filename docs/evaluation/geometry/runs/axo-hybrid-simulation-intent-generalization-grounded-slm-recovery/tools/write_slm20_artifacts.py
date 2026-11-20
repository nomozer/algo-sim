"""Writes SLM20_ROOT_CAUSE_AUDIT.json, SLM20_GOLD_INTERVENTION_RESULTS.json and V10_CASE_LEVEL_FAILURE_RECONCILIATION.json from the
baseline audit evidence (evidence/slm20/slm20_audit_baseline.json) and a per-case classification made by reading the raw model
output, the lowered payload and every intervention arm. usage: python write_slm20_artifacts.py   (from the run directory)
"""

import json
from pathlib import Path

A = {r["case_id"]: r for r in json.loads(Path("evidence/slm20/slm20_audit_baseline.json").read_text(encoding="utf-8"))["rows"]}
G = "TYPED_FACT_CONTRACT_MISMATCH"   # compact-clause GBNF: a clause with a simulate verb but no ask becomes a goal clause whose
                                     # only legal goals are metric, and `root` demands >= 1 goal or >= 1 unresolved item
SG = "SOURCE_GATE_GRAMMAR_GAP"
CLS = {  # case: (primary, [secondary], model_extraction_semantically_correct, first_failing_layer, minimal fix, evidence)
    "V02": (G, ["DETERMINISTIC_INTENT_COVERAGE_GAP"], "NOT_EXPRESSIBLE", "SLM_GRAMMAR",
            "goal-free grammar branch when the source asks nothing; parser 7b noun coverage", "raw u:[ambig] — the only legal non-metric output"),
    "V05": (SG, [G, "SLM_LOWERING_INCOMPLETE"], True, "SLM_LOWERING+SOURCE_GATE",
            "lower len-on-regular-solid to every edge class; Source Gate reads 'tất cả các cạnh (đều) bằng' (handoff unless owner widens)",
            "raw r:len(S.ABCD)=a (all edges); lowered only SA=a; UNGROUNDED_VALUE in B and D"),
    "V06": (G, [SG, "SLM_LOWERING_QUOTE"], True, "SLM_GRAMMAR", "goal-free grammar + construct_object quote on the command; Source Gate noun 'tứ diện'",
            "B: SOURCE_OBJECT_MISMATCH (forced goal:vol); D (goal removed): SOURCE_PREMISE_UNREAD (command unread)"),
    "V08": (G, [SG, "SLM_LOWERING_QUOTE"], True, "SLM_GRAMMAR", "same; noun 'lập phương'", "B forced goal:vol; D command unread; direct probe: Source Gate reads only 'mô phỏng hình (chóp|lăng trụ)'"),
    "V09": (G, ["DETERMINISTIC_INTENT_COVERAGE_GAP"], True, "SLM_GRAMMAR", "goal-free grammar; noun 'hình hộp'", "forced goal lratio rejected UNGROUNDED_GOAL_CLAUSE_TOKENS"),
    "V10": (G, ["DETERMINISTIC_INTENT_COVERAGE_GAP"], True, "SLM_GRAMMAR", "goal-free grammar; 'lăng trụ' followed by nothing → parser", "forced goal lratio rejected"),
    "V11": (G, [SG], True, "SLM_GRAMMAR", "goal-free grammar; noun 'lăng trụ' (+ đều) in Source Gate", "B forced goal:vol; D command unread"),
    "V14": (G, ["DETERMINISTIC_INTENT_COVERAGE_GAP"], True, "SLM_GRAMMAR", "goal-free grammar; verb 'dựng' in parser 7b", "B forced goal dist_line_line ×2; D command unread"),
    "V16": (G, [SG], True, "SLM_GRAMMAR", "goal-free grammar; 'hình chóp và các điểm M, N' (Source Gate already lists points)", "B forced goal:vol; D command unread (normalized text)"),
    "V19": (G, ["DETERMINISTIC_INTENT_COVERAGE_GAP"], "NOT_EXPRESSIBLE", "SLM_GRAMMAR", "goal-free grammar; noun 'tứ diện ABCD'", "raw u:[ambig]"),
    "V26": (G, [SG], True, "SLM_GRAMMAR", "goal-free grammar; 'hình hộp chữ nhật đó'", "B forced goal:vol; D command unread"),
    "V28": (G, [SG], True, "SLM_GRAMMAR", "goal-free grammar; 'hình chóp đều đó' (Source Gate forbids 'đều' after chóp)", "B forced goal:vol; D command unread"),
    "Q03": (SG, ["DETERMINISTIC_INTENT_COVERAGE_GAP"], True, "SOURCE_GATE",
            "Source Gate reads 'mô phỏng hình lập phương và tính …' once the noun is in its request grammar", "goal dist_line_line correct; QUESTION_CONTEXT_UNSUPPORTED in A,B,D"),
    "Q04": (SG, ["SOURCE_QUOTE_ALIGNMENT_FAILURE"], True, "SOURCE_GATE",
            "'biểu diễn <quantity>' is not an ask in the Source Gate question grammar — owner contract decision (handoff)", "NOT_ASKED_IN_SOURCE in A,B,D"),
    "Q05": (SG, ["SOURCE_QUOTE_ALIGNMENT_FAILURE"], True, "SLM_LOWERING_QUOTE+SOURCE_GATE",
            "goal quote picked from a fact clause; 'biểu diễn khoảng cách' not an ask (handoff)", "AMBIGUOUS_VALUE_QUOTE; goal quote = 'SA vuông góc với (ABCD)'"),
    "Q08": (SG, ["DETERMINISTIC_INTENT_COVERAGE_GAP"], True, "SOURCE_GATE", "noun 'hình hộp' in the Source Gate request grammar", "goal len correct; QUESTION_CONTEXT_UNSUPPORTED"),
    "Q10": ("SOURCE_QUOTE_ALIGNMENT_FAILURE", [], True, "SLM_LOWERING_QUOTE", "right_tri quote must be the clause stating 'vuông tại A'",
            "right_angle premise quoted 'SA vuông góc với (ABC)' → SOURCE_OBJECT_MISMATCH"),
    "C03": (SG, ["SLM_LOWERING_INCOMPLETE"], True, "SLM_LOWERING+SOURCE_GATE", "as V05", "raw len on solid; lowered SA only"),
    "C25": ("MODEL_RELATION_EXTRACTION_ERROR", ["NORMALIZER_PROVENANCE_ERROR"], False, "MODEL",
            "telegraphic clause: grammar allowed facts + vol goal, model chose ambig after 4 VN06/VN07 rewrites; candidate for training data only if a re-run confirms",
            "raw u:[ambig]; Arm E canonical served"),
    "C26": (SG, [], True, "SOURCE_GATE", "exam header 'Câu 2 (2 điểm).' unread by Source Gate (handoff; parser treats it benign)", "SOURCE_PREMISE_UNREAD in A,B,D"),
}
NON_SLM = {
    "V13": ("DETERMINISTIC_INTENT_COVERAGE_GAP", "parser AMBIGUOUS on the parallelogram clause; router does not fall back to SLM on AMBIGUOUS; Arm D (SLM facts, goal removed) SERVED"),
    "V18": ("DOMAIN_ROUTING_ERROR", "domain gate detect_domain refuses diacritic-less geometry before the router (handoff)"),
    "C24": ("DOMAIN_ROUTING_ERROR", "same"),
    "C20": ("UNDERDETERMINED_SIMULATION", "cube without an edge: angle fixed up to similarity; kernel refuses MISSING_DIMENSION; illustrative scale is kernel-owned (handoff)"),
}
arms = ("arm_A_product", "arm_B_slm_payload", "arm_D_gold_intent", "arm_C_parser_facts_gold_intent", "arm_E_downstream_canonical")
rows = []
for cid, (prim, sec, ok, layer, fix, ev) in CLS.items():
    r = A[cid]
    rows.append({"case_id": cid, "intent": r["intent"], "input": r["input"], "parser": r["parser"],
                 "slm_raw_model_output": r["slm"]["raw_model_output"], "slm_grounding_status": r["slm"]["grounding_status"],
                 "slm_accepted_ops": r["slm"]["accepted_ops"], "slm_rejected_ops": r["slm"]["rejected_ops"],
                 "normalizer_rules": (r["slm"]["normalization"] or {}).get("applied_rule_ids"),
                 "lowered_payload_problem_text_equals_input": (r["slm"]["lowered_payload"] or {}).get("problem_text") == r["input"],
                 "arms": {a: {k: v for k, v in (r.get(a) or {}).items() if k in ("status", "code", "extraction_mode", "oracle", "math_goals_removed", "why")} for a in arms},
                 "model_semantically_correct": ok, "first_failing_layer": layer, "primary_root_cause": prim, "secondary": sec,
                 "minimal_fix": fix, "evidence": ev,
                 "model_capability_failure": prim.startswith("MODEL_")})
Path("SLM20_ROOT_CAUSE_AUDIT.json").write_text(json.dumps({
    "schema": "axo-slm20-root-cause/1", "source": "evidence/slm20/slm20_audit_baseline.json (real AxoV9 GGUF, product runtime, /10 code at 2f12b96b0)",
    "counts": {"cases": len(rows),
               "primary": {p: sum(x["primary_root_cause"] == p for x in rows) for p in sorted({x["primary_root_cause"] for x in rows})},
               "model_semantically_correct": sum(x["model_semantically_correct"] is True for x in rows),
               "not_expressible_under_grammar": sum(x["model_semantically_correct"] == "NOT_EXPRESSIBLE" for x in rows),
               "model_capability_failure": sum(x["model_capability_failure"] for x in rows),
               "fabricated_metric_goal_forced_by_grammar": sum("goal:" in json.dumps(x["slm_accepted_ops"]) and x["intent"] == "SIMULATE_ONLY" for x in rows)},
    "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
Path("SLM20_GOLD_INTERVENTION_RESULTS.json").write_text(json.dumps({
    "schema": "axo-slm20-gold-intervention/1",
    "arms": {"A": "product route", "B": "SLM lowered payload → downstream", "D": "SLM facts + gold simulation intent", "C": "parser payload of original + gold intent",
             "E": "deterministic route on a minimal canonical rephrase (oracle-checked); C20's rephrase ADDS an edge length — not equivalent"},
    "served": {a: sum((A[c].get(a) or {}).get("status") == "SERVED" for c in A) for a in arms},
    "valid_by_oracle": {a: sum(((A[c].get(a) or {}).get("oracle") or {}).get("scene_validation") == "MATHEMATICALLY_VALID" for c in A) for a in arms},
    "rows": [{"case_id": c, **{a: {k: v for k, v in (A[c].get(a) or {}).items() if k in ("status", "code", "oracle", "why")} for a in arms}} for c in A],
    "note": "Arm D isolates the forced goal: for the 7 SIMULATE_ONLY cases it moves the first failure from SOURCE_OBJECT_MISMATCH to SOURCE_PREMISE_UNREAD (the Source Gate does not read the command); V13 is SERVED by Arm D."},
    ensure_ascii=False, indent=1), encoding="utf-8")
recon = [{"case_id": c, "slm_route": True, "primary_root_cause": CLS[c][0]} for c in CLS] + \
        [{"case_id": c, "slm_route": False, "primary_root_cause": v[0], "note": v[1]} for c, v in NON_SLM.items()]
Path("V10_CASE_LEVEL_FAILURE_RECONCILIATION.json").write_text(json.dumps({
    "schema": "axo-v10-failure-reconciliation/1", "refused_valid_cases": len(recon),
    "by_primary": {p: sum(x["primary_root_cause"] == p for x in recon) for p in sorted({x["primary_root_cause"] for x in recon})},
    "no_route_cases": {"V18": "DOMAIN_ROUTING_ERROR", "C24": "DOMAIN_ROUTING_ERROR"},
    "truly_out_of_product_scope": 0, "rows": recon}, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.load(open("SLM20_ROOT_CAUSE_AUDIT.json", encoding="utf-8"))["counts"])
