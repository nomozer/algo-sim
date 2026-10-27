"""Offline evaluator for Adapter /4 plane-only section certificates (RED / GREEN receipts).

Zero live provider calls (`ALLOW_LIVE_AI = 0`).
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route


def _square_exact(result, goal_id: str = "q") -> F:
    v = result.exec_result.final_memory[f"kq_{goal_id}"]
    return F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2


def _sync_tampered_certs(result, mutator) -> None:
    """Apply `mutator` to both `result.route_d['sections'][0]` and `result.section_certificates` so tampering tests
    reach `_validate_sections` rather than stopping only at the shallow `_phong_bi` equality check."""
    if getattr(result, "section_certificates", None):
        certs = deepcopy(list(result.section_certificates))
        mutator(certs[0])
        result.section_certificates = tuple(certs)
    if result.route_d.get("sections"):
        mutator(result.route_d["sections"][0])


def _apply_tamper(case: dict, result) -> None:
    kind = case["tamper_kind"]
    if not result.route_d.get("sections"):
        # On baseline before implementation, `sections` is already empty, so `build_adapter4_response` refuses.
        return
    if kind == "tamper-forged-certificate":
        _sync_tampered_certs(result, lambda s: s["closure_certificate"].update(verified=False, producer="forged.producer"))
    elif kind == "tamper-mismatched-edge-and-vertex":
        _sync_tampered_certs(result, lambda s: s["vertices"][0].update(edge=["A", "C"]))
    elif kind == "tamper-wrong-intersection-ordering":
        def _swap(s):
            s["vertices"][1], s["vertices"][2] = s["vertices"][2], s["vertices"][1]
            s["boundary"] = [v["entity_id"] for v in s["vertices"]]
            s["closure_certificate"]["boundary"] = list(s["boundary"])
            s["closure_certificate"]["polygon"] = [v["xyz"] for v in s["vertices"]]
        _sync_tampered_certs(result, _swap)
        sec_obj = next(o for o in result.scene3d["objects"] if o["type"] == "section")
        sec_obj["polygon"][1], sec_obj["polygon"][2] = sec_obj["polygon"][2], sec_obj["polygon"][1]
    elif kind == "tamper-duplicated-or-missing-vertex":
        _sync_tampered_certs(result, lambda s: s["vertices"].pop())
    elif kind == "tamper-degenerate-collinear-polygon":
        def _degen(s):
            s["closure_certificate"]["area_squared"] = "0"
        _sync_tampered_certs(result, _degen)
    elif kind == "tamper-exact-area":
        _sync_tampered_certs(result, lambda s: s["closure_certificate"].update(area_squared="999999"))
    elif kind == "tamper-unknown-certificate-version":
        _sync_tampered_certs(result, lambda s: s.update(certificate_version="plane-section-certificate/999"))
    elif kind == "tamper-unsupported-topology-diagonal-edge":
        _sync_tampered_certs(result, lambda s: s["vertices"][0].update(edge=["A", "C'"], solid_edge_vertex_indices=[0, 5]))
    elif kind == "tamper-inconsistent-provenance":
        _sync_tampered_certs(result, lambda s: s["vertices"][0].update(stated=True, provenance="SOURCE_NAMED"))
    elif kind == "tamper-certificate-reuse-across-plane-or-solid":
        other = run_typed_fact_next_v2_route(deepcopy(case["secondary_payload"]))
        if getattr(other, "section_certificates", None):
            result.section_certificates = deepcopy(other.section_certificates)
            result.route_d["sections"] = deepcopy(other.route_d["sections"])
    elif kind == "tamper-wrong-solid-identity":
        _sync_tampered_certs(result, lambda s: s.update(solid="S.ABC", solid_object_id="khoi_pyr"))


def evaluate(output_path: Path) -> dict:
    run = Path(__file__).resolve().parents[1]
    data = json.loads((run / "inputs/development.json").read_text(encoding="utf-8"))
    results = []
    passed = 0
    for case in data["cases"]:
        payload = deepcopy(case["payload"])
        r = run_typed_fact_next_v2_route(payload)
        if case["group"] == "negative_tamper" and r.status == "SERVED":
            _apply_tamper(case, r)
        resp = build_adapter4_response(r, payload["problem_text"])
        rd = resp["route_d"]
        adapter_status = rd["status"]
        refusal_code = (rd.get("refusal") or {}).get("code")

        ok = (
            r.status == case["expected_route_status"]
            and adapter_status == case["expected_adapter4_status"]
        )
        if case["expected_adapter4_status"] == "SERVED":
            ok = ok and resp["envelope"]["status"] == "ok" and len(rd.get("sections") or []) == 1
            if ok and case.get("expected_area_squared") is not None and "q" in r.answer_exact:
                ok = ok and _square_exact(r, "q") == F(case["expected_area_squared"])
            if ok and case.get("expected_vertex_count") is not None:
                ok = ok and len(rd["sections"][0]["vertices"]) == case["expected_vertex_count"]
        else:
            ok = ok and resp["envelope"]["status"] == "unsupported" and refusal_code in case["expected_codes"]

        if ok:
            passed += 1
        results.append({
            "id": case["id"],
            "group": case["group"],
            "route_status": r.status,
            "route_code": r.code,
            "adapter4_status": adapter_status,
            "adapter4_refusal_code": refusal_code,
            "sections_count": len(rd.get("sections") or []),
            "passed": ok,
        })

    summary = {
        "live_calls": 0,
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "positive_passed": sum(1 for x in results if x["group"].startswith("positive") and x["passed"]),
        "positive_total": sum(1 for x in results if x["group"].startswith("positive")),
        "negative_passed": sum(1 for x in results if x["group"].startswith("negative") and x["passed"]),
        "negative_total": sum(1 for x in results if x["group"].startswith("negative")),
        "cases": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    out = Path(sys.argv[1])
    s = evaluate(out)
    print(f"Evaluated {s['total']} cases: {s['passed']} passed, {s['failed']} failed "
          f"(positive {s['positive_passed']}/{s['positive_total']}, negative {s['negative_passed']}/{s['negative_total']})")
