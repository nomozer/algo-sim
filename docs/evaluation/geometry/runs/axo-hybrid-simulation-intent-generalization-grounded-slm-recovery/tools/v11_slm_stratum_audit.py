"""POST-HOC diagnostic of the /11 blind SLM_REQUIRED stratum (run AFTER the blind run; nothing here changes its result).

Per case: the product route verdict from the blind run, a fresh direct SLM extraction (real AxoV9 via the product runtime,
no cache: raw model output, grounding status, rejected ops), the SLM payload through the real downstream (Arm B), and
Arm SPLIT: a MECHANICAL rephrase that moves an embedded declaration out of the request
("Vẽ hình chóp S.ABCD có … và tính X" -> "Cho hình chóp S.ABCD có …. Hãy mô phỏng hình và tính X.") run on the full
deterministic route. SPLIT tests one hypothesis (declaration-inside-request is the blocker); it is not a gold rephrase.
usage (from backend/): python <this> <out.json>
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "tools"))
import scene_oracle as so  # noqa: E402

from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_slm_extractor import V9_CLOSURE_MODE, run_local_slm_extraction  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402

OUT = Path(sys.argv[1])
if OUT.exists():
    raise SystemExit(f"refusing to overwrite {OUT}")
OUT.parent.mkdir(parents=True, exist_ok=True)
POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
man = {c["case_id"]: c for c in json.loads((RUN / "V11_LIVE_ACCEPTANCE_MANIFEST.json").read_text(encoding="utf-8"))["valid_cases"]}
frz = json.loads((RUN / "V11_LIVE_ACCEPTANCE_FREEZE.json").read_text(encoding="utf-8"))["rows"]
blind = {json.loads(l)["case_id"]: json.loads(l) for l in (RUN / "evidence/browser/browser_records_v11.jsonl").read_text(encoding="utf-8").splitlines()}

VERB = r"(?:(?:em\s+)?hãy\s+)?(?:vẽ(?:\s+giúp\s+em)?|dựng|mô\s+phỏng|biểu\s+diễn)"
SPLIT = re.compile(rf"^\s*{VERB}\s+(?P<decl>(?:hình|khối)?\s*(?:chóp|lăng\s+trụ|hộp|lập\s+phương|tứ\s+diện).+?)"
                   rf"(?:\s*(?:,\s*)?(?:và|rồi|sau\s+đó|;)\s*(?P<ask>(?:tính|tìm|xác\s+định)\s+.+?))?\s*\.?\s*$", re.I)


def split(text: str):
    m = SPLIT.match(text)
    if not m:
        return None
    decl = re.sub(r"^(?:hình|khối)?\s*", "hình ", m["decl"].strip().rstrip("."), flags=re.I)
    return f"Cho {decl}. Hãy mô phỏng hình" + (f" và {m['ask'].rstrip('.')}." if m["ask"] else ".")


rows = []
for r in frz:
    if r["stratum"] != "SLM_REQUIRED":
        continue
    c, b = man[r["case_id"]], blind[r["case_id"]]
    row = {"case_id": c["case_id"], "input": c["original_input"], "blind": {k: b.get(k) for k in ("route_status", "extraction_mode", "refusal_code")}}
    if b.get("route_status") == "SERVED":
        row["first_failing_layer"] = "NONE (served in blind run)"
        rows.append(row); print(c["case_id"], "served"); continue
    x = run_local_slm_extraction(c["original_input"], model_key="v9", closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", use_cache=False)
    ge = x.grounding_envelope or {}
    row["slm"] = {"ok": x.ok, "raw": x.inference.raw_content if x.inference else None, "grounding": ge.get("grounding_status"),
                  "rejected_ops": ge.get("rejected_ops"), "error": getattr(x, "error_code", None)}
    if x.canonical_payload:
        h = run_hybrid_offline(x.norm_text, ReplayExtractor({x.norm_text: x.canonical_payload}), policy=POLICY, timeout_seconds=30)
        rd = h.response.get("route_d") or {}
        row["arm_B"] = {"status": rd.get("status"), "code": (rd.get("refusal") or {}).get("code")}
    s = split(c["original_input"])
    if s:
        d = route_text_input(s, allow_live_ai=False, model="local-slm:diag", policy=POLICY, timeout_seconds=30)
        rd = (d.response or {}).get("route_d") or {}
        row["arm_SPLIT"] = {"text": s, "status": rd.get("status"), "code": (rd.get("refusal") or {}).get("code"), "mode": rd.get("extraction_mode")}
        if rd.get("status") == "SERVED":
            v = so.validate(c, d.response)
            row["arm_SPLIT"]["oracle"] = v.get("scene_validation"); row["arm_SPLIT"]["numeric"] = (v.get("numeric") or {}).get("status")
    blk = row["blind"]
    row["first_failing_layer"] = (
        "DOMAIN_GATE" if blk["route_status"] is None else
        "PARSER_REFUSED_BEFORE_SLM" if blk["extraction_mode"] == "LOCAL_DETERMINISTIC_PARSER" else
        "SLM_REPORTED_UNRESOLVED" if row["slm"]["grounding"] == "SLM_REPORTED_UNRESOLVED" else
        "SLM_GROUNDING_REJECTED" if not x.canonical_payload else "DOWNSTREAM_SOURCE_GATE")
    rows.append(row)
    print(c["case_id"], row["first_failing_layer"], row["slm"]["grounding"], row.get("arm_B"), (row.get("arm_SPLIT") or {}).get("status"), flush=True)

cnt = {}
for r in rows:
    cnt[r["first_failing_layer"]] = cnt.get(r["first_failing_layer"], 0) + 1
split_ok = [r["case_id"] for r in rows if (r.get("arm_SPLIT") or {}).get("oracle") == "MATHEMATICALLY_VALID"]
OUT.write_text(json.dumps({"schema": "axo-v11-slm-stratum-audit/1", "post_hoc": True, "first_failing_layer": cnt,
                           "split_served_valid": split_ok, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(cnt), "SPLIT valid:", split_ok)
