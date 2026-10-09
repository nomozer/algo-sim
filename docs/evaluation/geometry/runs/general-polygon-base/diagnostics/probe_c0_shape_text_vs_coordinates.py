"""Cache-impact probe: a coordinate (C0) right-trapezoid pyramid whose text ALSO contains the newly read phrase.
Run from a backend/ directory (current tree or a d5287ff7 worktree); prints the route outcome to compare."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

TEN = ["A", "B", "C", "D", "S"]
TOA = {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 4, 0], "S": [0, 0, 3]}
MAT = [["D", "C", "B", "A"]] + [[TEN[i], TEN[(i + 1) % 4], "S"] for i in range(4)]
TEXTS = {
    "with_phrase": "Cho khối chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B với A(0;0;0), B(2;0;0), "
                   "C(2;2;0), D(0;4;0) và đỉnh S(0;0;3). Tính thể tích khối chóp.",
    "phrase_contradicts_coords": "Cho khối chóp S.ABCD có đáy ABCD là hình thang vuông tại C và D với A(0;0;0), "
                                 "B(2;0;0), C(2;2;0), D(0;4;0) và đỉnh S(0;0;3). Tính thể tích khối chóp.",
}
spec = SemanticProgramSpec.model_validate({
    "title": "Thể tích khối chóp",
    "memory_declarations": [{"name": t, "type": "point3", "initial_value": TOA[t], "source_fact_id": f"d_{t}"}
                            for t in TEN] + [{"name": "chop", "type": "solid"}, {"name": "V", "type": "float"}],
    "statements": [
        {"kind": "construct_solid", "target_var": "chop", "vertices": TEN, "faces": MAT, "label": "S.ABCD"},
        {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}}]})
for name, text in TEXTS.items():
    ct = RequestContract(problem_text=text,
                         input_facts=[{"fact_id": f"d_{t}", "label": f"điểm {t}", "values": [t],
                                       "provenance": "confirmed"} for t in TEN],
                         obligations=(Obligation(kind="volume", container="chop", params={"witness": "V"}),))
    oc = verify_and_compile(ct, spec)
    d = oc.model_dump() if hasattr(oc, "model_dump") else vars(oc)
    keep = {k: d.get(k) for k in ("servable", "stage_reached", "reason_code", "error_code")}
    keep["V"] = str(oc.final_memory.get("V")) if oc.final_memory else None
    keep["assumption"] = {k: v for k, v in (d.get("da_chay") or d.get("executed") or {}).items()
                          if k.startswith("assumption")} or [x for x in (oc.details or []) if "C0" in str(x) or "T10" in str(x)]
    print(name, json.dumps(keep, ensure_ascii=False, default=str))
import hashlib, re
for name, text in TEXTS.items():
    ct = RequestContract(problem_text=text,
                         input_facts=[{"fact_id": f"d_{t}", "label": f"điểm {t}", "values": [t],
                                       "provenance": "confirmed"} for t in TEN],
                         obligations=(Obligation(kind="volume", container="chop", params={"witness": "V"}),))
    oc = verify_and_compile(ct, spec)
    d = oc.model_dump() if hasattr(oc, "model_dump") else dict(vars(oc))
    s = json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)
    s = re.sub(r'"[a-z_]*(?:ms|elapsed|time)[a-z_]*": [0-9.e-]+', '"t": 0', s)
    s = re.sub(r" at 0x[0-9A-Fa-f]+", "", s)
    print("FULL", name, hashlib.sha256(s.encode()).hexdigest()[:16], len(s))
    print("ASSUMPTION", name, json.dumps({k: v for k, v in d.items() if "assum" in k or "gia_dinh" in k}, ensure_ascii=False, default=str)[:300])
