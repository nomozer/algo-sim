"""Phân tích TRÁCH NHIỆM (quyết định A giao cho AI mà B chuyển sang planner) + BỀ MẶT schema/prompt của hai nhánh. 0 API call.
Chạy từ backend/. Đọc trace planner trên 14 ca holdout. Bề mặt đo bằng KÝ TỰ và số mục — KHÔNG suy ra token."""
import json, sys
from pathlib import Path

sys.path.insert(0, ".")
from app.ai import fact_extraction as FE, function_calling as FC
from app.ai.function_route import run_fact_route

LOAI = {"definitional_expansion": lambda r: "⇒" in r or "định nghĩa" in r,
        "role_resolution": lambda r: any(k in r for k in ("lateral_edge", "base_edge", "(edge)", "(height)")),
        "relation_type_to_function": lambda r: r.startswith("perpendicular(") or r.startswith("question("),
        "solid_to_construction": lambda r: r.startswith("solid")}

cases = json.loads(Path("tests/geometry/fixtures/hybrid_holdout_cases.json").read_text(encoding="utf-8"))["cases"]
tong = {k: 0 for k in LOAI}
print(f"{'case':<42} " + " ".join(f"{k[:22]:>22}" for k in LOAI))
for c in cases:
    r = run_fact_route(c["text"], {"facts": c["b_facts"]})
    rules = [t["rule"] for t in (r.planner.get("trace") or [])]
    dem = {k: sum(f(x) for x in rules) for k, f in LOAI.items()}
    for k in tong:
        tong[k] += dem[k]
    print(f"{c['id']:<42} " + " ".join(f"{dem[k]:>22}" for k in LOAI))
print("TOTAL", tong)

pa, pb = FC.build_request("x"), FE.build_request("x")
sa = json.dumps(pa["tools"], ensure_ascii=False)
sb = json.dumps(pb["generationConfig"]["responseSchema"], ensure_ascii=False)
print(json.dumps({
    "A_function_declarations": len(pa["tools"][0]["functionDeclarations"]), "A_schema_chars": len(sa),
    "A_prompt_chars": len(FC.SYSTEM_PROMPT), "A_surface_sha256": FC.surface_fingerprint(),
    "B_fact_kinds": len(json.loads(sb)["properties"]["facts"]["items"]["properties"]["kind"]["enum"]),
    "B_fact_fields": len(json.loads(sb)["properties"]["facts"]["items"]["properties"]), "B_schema_chars": len(sb),
    "B_prompt_chars": len(FE.SYSTEM_PROMPT), "B_surface_sha256": FE.surface_fingerprint(),
    "REAL_MODEL_TOKEN_USAGE": "NOT_MEASURED"}, ensure_ascii=False, indent=1))
