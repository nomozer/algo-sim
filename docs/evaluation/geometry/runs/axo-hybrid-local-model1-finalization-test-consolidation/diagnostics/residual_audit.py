"""Diagnostic harness for the 17 incomplete /12 in-scope cases (the /12 set is EXPOSED: regression only, never blind).

For each case:
  1. frozen /12 telemetry (route, parser status, fallback reason, SLM grounding, refusal code);
  2. the CURRENT code's real local path (`prepare_local_slm_v9_hybrid(...).run()`: deterministic parser, then the real
     GGUF through llama.cpp, Source Gate, planner, kernel) — no cache, 0 external AI;
  3. a GOLD INTERVENTION, diagnostic only: the same gold geometry written in a canonical phrasing, through the same path.
     If (3) is served and oracle-valid while (2) is not, the downstream layers are sound and the first failing layer is
     language understanding of the original phrasing. Nothing from (3) ever enters the product.
Each served scene is checked by the independent exact oracle against the /12 gold case.

usage (from backend/): python <this> --out <new file>   (env: LOCAL_SLM_CACHE_DIR, LOCAL_SLM_MODEL, ALLOW_LIVE_AI=0)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
R12 = ROOT / "docs/evaluation/geometry/runs/axo-hybrid-compositional-geometry-language-grounded-simulation"
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "docs/evaluation/geometry/harness/live-acceptance"))
import scene_oracle  # noqa: E402

#: case -> (canonical phrasing of the SAME gold geometry, note). Written from the /12 gold relations, not from outputs.
CANONICAL = {
    "V006": ("Vẽ hình chóp K.EFGH có đáy EFGH là hình vuông cạnh 4, KF vuông góc với đáy và KF = 2.", "meta prefix removed"),
    "V008": ("Vẽ hình lăng trụ đứng MNP.M'N'P' có đáy MNP là tam giác vuông tại M, MN = 3, MP = 4 và MM' = 6.", "'với' removed"),
    "V027": ("Cho tứ diện OMNP có OM, ON, OP đôi một vuông góc, OM = 2, ON = 3, OP = 6. Vẽ hình.", "O.MNP -> OMNP"),
    "V029": ("Vẽ hình chóp S.MNPQ có đáy MNPQ là hình thoi cạnh 2a, góc NMQ = 60°, SM vuông góc với (MNPQ) và SM = 2a.",
             "gold encodes angle NMQ = 60°; the /12 text says NMP"),
    "V030": ("Vẽ hình chóp K.EFG có đáy EFG là tam giác đều cạnh a, KE vuông góc với đáy và KE = 2a.", "two faces ⊥ base -> edge ⊥ base"),
    "V031": ("Vẽ hình chóp P.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, PB vuông góc với (ABC) và PB = 5.", "meta clause removed"),
    "V032": ("Vẽ hình lập phương KLMN.K'L'M'N' cạnh 4. Gọi I là trung điểm của LL'. Vẽ hình và điểm I.", "purpose tail removed"),
    "V033": ("Dựng lăng trụ đứng KLM.K'L'M' có đáy KLM là tam giác vuông cân tại K, KL = KM = 2 và KK' = 4.", "reordered"),
    "V040": ("Vẽ hình chóp H.MNPQ có đáy MNPQ là hình vuông cạnh 2, HM vuông góc với đáy và HM = 4.", "diacritics + faces ⊥ base"),
    "V047": ("Cho tứ diện KEFG có KE, KF, KG đôi một vuông góc, KE = 2, KF = 2, KG = 1. Vẽ hình và tính thể tích khối tứ diện KEFG.", "K.EFG -> KEFG"),
    "V062": ("Vẽ hình chóp K.EFGH có đáy EFGH là hình thoi cạnh 2, góc FEH = 60°, KE vuông góc với đáy và KE = 2. Tính thể tích khối chóp K.EFGH.", "'Biểu diễn ... biết' -> 'Vẽ ... có'"),
    "V067": ("Vẽ hình chóp K.EFGH có đáy EFGH là hình vuông cạnh 2, KE vuông góc với đáy và KE = 4. Tính thể tích khối chóp K.EFGH.", "'đường cao KE' -> 'KE ⊥ đáy'"),
    "V070": ("Vẽ hình chóp tứ giác đều H.MNPQ có cạnh đáy bằng 4 và chiều cao bằng 4. Tính độ dài cạnh bên HM và thể tích khối chóp H.MNPQ.", "reworded"),
    "V072": ("Vẽ lăng trụ đứng MNP.M'N'P' có đáy là tam giác đều cạnh 2 và MM' = 2√3. Tính diện tích tam giác MNP và thể tích khối lăng trụ.", "reworded; area of a base face still asked"),
    "V088": ("Cho hình chóp H.MNPQ có đáy MNPQ là hình vuông cạnh 3, HM vuông góc với đáy và HM = 3. Tính góc giữa mặt phẳng (HPQ) và mặt phẳng đáy.", "faces ⊥ base -> edge ⊥ base"),
    "V098": ("Cho tứ diện EKFG có EK, EF, EG đôi một vuông góc, EK = 3, EF = 4, EG = 5. Tính thể tích khối tứ diện EKFG.", "vertex E named first"),
    "V104": ("Cho tứ diện OMNP có OM, ON, OP đôi một vuông góc, OM = 3, ON = 4, OP = 6. Tính thể tích khối tứ diện OMNP.", "diacritics, O.MNP -> OMNP"),
}

_SOURCE_GATE = {"UNGROUNDED_VALUE", "SOURCE_PREMISE_UNREAD", "CONDITIONAL_CLAUSE", "QUESTION_CONTEXT_UNSUPPORTED",
                "SOURCE_GATE_MISMATCH"}


def _layer(rd: dict) -> str:
    """First failing layer from the route's own telemetry (no guessing past what the response says)."""
    at = rd.get("adaptive_telemetry") or {}
    se = rd.get("slm_grounding_envelope") or {}
    code = (rd.get("refusal") or {}).get("code") or rd.get("reason_code")
    if rd.get("status") == "SERVED":
        return "NONE"
    if se.get("grounding_status") == "SLM_REPORTED_UNRESOLVED" or "EMPTY_SOLIDS" in str(at.get("fallback_reason")):
        return "EXTRACTION(parser+SLM): solid/relations not extracted"
    if code in _SOURCE_GATE:
        return f"SOURCE_GATE:{code}"
    if code == "BRIDGE_UNSUPPORTED_MEASUREMENT":
        return "BRIDGE:" + code
    if code == "REPLAY_SOURCE_IDENTITY_MISMATCH":
        return "SLM_QUOTE_MAPPING:" + code
    if code == "MISSING_DIMENSION":
        return "EXTRACTION(dimension lost) or PLANNER:" + code
    return f"OTHER:{code}"


def _summ(rd: dict) -> dict:
    at = rd.get("adaptive_telemetry") or {}
    se = rd.get("slm_grounding_envelope") or {}
    return {"status": rd.get("status"), "code": (rd.get("refusal") or {}).get("code") or rd.get("reason_code"),
            "extraction_mode": rd.get("extraction_mode"), "parse": at.get("local_parse_status"), "route": at.get("chosen_route"),
            "fallback_reason": (at.get("fallback_reason") or "")[:300] or None, "slm_grounding": se.get("grounding_status"),
            "slm_accepted_ops": [o.get("kind") for o in se.get("accepted_ops", [])], "first_failing_layer": _layer(rd)}


def _run(text: str) -> dict:
    from app.ai.hybrid_offline import prepare_local_slm_v9_hybrid
    t0 = time.perf_counter()
    res = prepare_local_slm_v9_hybrid(text, mode_tag="local-only-scoped").run(timeout_seconds=60.0)
    body = res.response if isinstance(res.response, dict) else json.loads(json.dumps(res.response, default=str))
    return {"ms": round((time.perf_counter() - t0) * 1000), "body": body}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    assert os.getenv("ALLOW_LIVE_AI") == "0" and not os.getenv("GEMINI_API_KEY"), "local only: ALLOW_LIVE_AI=0, no GEMINI_API_KEY"
    man = {c["case_id"]: c for c in json.loads((R12 / "V12_ACCEPTANCE_MANIFEST.json").read_text(encoding="utf-8"))["valid_cases"]}
    frozen = {json.loads(l)["case_id"]: json.loads(l) for l in (R12 / "evidence/v12_responses.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    rows = []
    for cid, (canon, note) in CANONICAL.items():
        case = man[cid]
        row = {"case_id": cid, "text": case["original_input"], "v12": _summ(frozen[cid]["body"].get("route_d") or {})}
        cur = _run(case["original_input"])
        row["current"] = {**_summ(cur["body"].get("route_d") or {}), "ms": cur["ms"],
                          "oracle": scene_oracle.validate(case, cur["body"]).get("scene_validation")}
        gi = _run(canon)
        row["gold_intervention"] = {"text": canon, "note": note, **_summ(gi["body"].get("route_d") or {}), "ms": gi["ms"],
                                    "oracle": scene_oracle.validate(case, gi["body"]).get("scene_validation"),
                                    "numeric": (scene_oracle.validate(case, gi["body"]).get("numeric") or {}).get("status")}
        rows.append(row)
        print(cid, row["v12"]["first_failing_layer"], "| now:", row["current"]["status"], row["current"]["code"],
              "| gold:", row["gold_intervention"]["status"], row["gold_intervention"]["oracle"], flush=True)
    a.out.write_text(json.dumps({"schema": "axo-model1-residual-diagnostics/1", "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
