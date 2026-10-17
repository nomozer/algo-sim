"""Execute the P1-P6 Independent Mathematical Construction Audit for Scene3D.

Strictly zero live AI calls (`ALLOW_LIVE_AI=0`).
Generates machine-verifiable receipts in `docs/evaluation/geometry/runs/step-math-validation/`:
  - `catalog-audit.json`
  - `counterexamples.json`
  - `run.json`
  - `report.md`
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"

WORKTREE_ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = WORKTREE_ROOT / "docs" / "evaluation" / "geometry" / "runs" / "step-math-validation"
sys.path.insert(0, str(RUN_DIR))

import oracle  # noqa: E402


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_and_audit_all_scenes() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Audit all Frontend sample/fixture scenes and all Backend Hybrid Route D scenes."""
    frontend_reports: list[dict[str, Any]] = []
    backend_reports: list[dict[str, Any]] = []
    refusal_rows: list[dict[str, Any]] = []

    # 1. Frontend Sample Scenes (11 scenes in frontend/src/data/geometry-samples.json)
    samples_path = WORKTREE_ROOT / "frontend" / "src" / "data" / "geometry-samples.json"
    samples_data = json.loads(samples_path.read_text(encoding="utf-8"))
    for s in samples_data.get("samples", []):
        sc = s["envelope"]["scene3d"]
        rep = oracle.verify_scene_mathematics(
            sc,
            scene_id=s["id"],
            data_source="frontend/src/data/geometry-samples.json",
            source_kind="frontend_sample_or_fixture",
            problem_text=s.get("problemText", ""),
        )
        frontend_reports.append(_serialize_report(rep))

    # 2. Frontend Standalone Fixtures (2 scenes)
    for rel_fp, prob_desc in [
        (
            "frontend/src/simulations/domains/geometry/scene3d-section-fixture.json",
            "Hình chóp tứ giác đều S.ABCD cắt bởi mặt phẳng (P1P2P3) đi qua trung điểm SA, SB, SC; tính thể tích V.",
        ),
        (
            "frontend/src/simulations/domains/geometry/scene3d-circumsphere-fixture.json",
            "Tứ diện vuông OABC có OA, OB, OC đôi một vuông góc (OA=OB=OC=2); dựng tâm M và bán kính R mặt cầu ngoại tiếp.",
        ),
    ]:
        fp = WORKTREE_ROOT / rel_fp
        sc = json.loads(fp.read_text(encoding="utf-8"))
        rep = oracle.verify_scene_mathematics(
            sc,
            scene_id=fp.stem,
            data_source=rel_fp,
            source_kind="frontend_sample_or_fixture",
            problem_text=prob_desc,
        )
        frontend_reports.append(_serialize_report(rep))

    # 3. Backend Visual / Offline Certification Scene Catalogs on `main` (4abc4afb)
    backend_json_files = [
        "docs/evaluation/geometry/runs/scene3d-visual-correctness/visual/scenes.json",
        "docs/evaluation/geometry/runs/scene3d-annotation-correctness/visual/scenes.json",
        "docs/evaluation/geometry/runs/scene3d-educational-finalization/visual/scenes.json",
        "docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json",
        "docs/evaluation/geometry/runs/pedagogical-construction-sequencing/visual/scenes.json",
        "docs/evaluation/geometry/runs/generalized-goal-entry/visual/scenes.json",
        "docs/evaluation/geometry/runs/source-bound-result-planning/visual/scenes.json",
        "docs/evaluation/geometry/runs/goal-directed-function-discovery/visual/scenes.json",
        "docs/evaluation/geometry/runs/two-line-plane-section/visual/scenes.json",
        "docs/evaluation/geometry/runs/hybrid-semantic-hardening/visual/scenes.json",
        "docs/evaluation/geometry/runs/hybrid-slice-review/visual/scenes.json",
        "docs/evaluation/geometry/runs/geometry-library-expansion/offline-certification/scenes.json",
    ]
    for rel_p in backend_json_files:
        p = WORKTREE_ROOT / rel_p
        if not p.exists():
            continue
        raw = json.loads(p.read_text(encoding="utf-8"))
        rows = raw["scenes"] if isinstance(raw, dict) and "scenes" in raw else (raw if isinstance(raw, list) else [])
        run_slug = Path(rel_p).parts[4]
        for r in rows:
            sc = r.get("scene") or r.get("scene3d")
            if not sc:
                refusal_rows.append(
                    {
                        "scene_id": f"{run_slug}::{r.get('id', 'unknown')}",
                        "data_source": rel_p,
                        "served": bool(r.get("served", False)),
                        "code": r.get("code"),
                        "reason": r.get("reason"),
                        "problem_text": r.get("text", ""),
                        "verdict": "VERIFIED_FAIL_CLOSED_REFUSAL" if not r.get("served") else "UNVERIFIABLE",
                    }
                )
                continue
            rep = oracle.verify_scene_mathematics(
                sc,
                scene_id=f"{run_slug}::{r.get('id', 'unknown')}",
                data_source=rel_p,
                source_kind="backend_hybrid_route_d",
                problem_text=r.get("text", ""),
                expected_answers=r.get("answers"),
            )
            backend_reports.append(_serialize_report(rep))

    # 4. Backend Individual Offline Scene Directories on `main` (4abc4afb)
    backend_scene_dirs = [
        "docs/evaluation/geometry/runs/ai-function-route/offline/geometry_expansion_cases/scenes",
        "docs/evaluation/geometry/runs/ai-function-route/offline/paraphrase_cases/scenes",
        "docs/evaluation/geometry/runs/ai-function-route/offline/text_to_functions_cases/scenes",
        "docs/evaluation/geometry/runs/hybrid-compiler-selection/offline/scenes",
        "docs/evaluation/geometry/runs/text-to-geometry-functions/offline/scenes",
    ]
    for rel_d in backend_scene_dirs:
        d_path = WORKTREE_ROOT / rel_d
        if not d_path.exists():
            continue
        dir_tag = "/".join(Path(rel_d).parts[4:-1])
        for f in sorted(d_path.glob("*.json")):
            sc = json.loads(f.read_text(encoding="utf-8"))
            rep = oracle.verify_scene_mathematics(
                sc,
                scene_id=f"{dir_tag}::{f.stem}",
                data_source=f"{rel_d}/{f.name}",
                source_kind="backend_hybrid_route_d",
                problem_text="",
            )
            backend_reports.append(_serialize_report(rep))

    # 5. Frozen `research/contract-driven-goal-composition` (a629ebee) — 23 served scenes
    cdgc_wt = WORKTREE_ROOT.parent / "contract-driven-goal-composition"
    cdgc_corpus_path = cdgc_wt / "docs" / "evaluation" / "geometry" / "runs" / "contract-driven-goal-composition" / "corpus.json"
    if cdgc_corpus_path.exists():
        sys.path.insert(0, str(cdgc_wt / "backend"))
        import app.simulation.geometry_functions.registry as cdgc_registry  # noqa: E402
        from app.ai.fact_extraction import run_fact_route  # noqa: E402
        from tests.geometry.test_contract_driven_goal_composition import (  # noqa: E402
            experimental_centroid_contract,
        )

        corpus = json.loads(cdgc_corpus_path.read_text(encoding="utf-8"))
        for group_name in ("positive", "held_out", "angle_line_plane_slice_b"):
            for case in corpus.get(group_name, []):
                res = run_fact_route(case["text"], case["payload"])
                if res.status == "SERVED" and res.scene3d:
                    rep = oracle.verify_scene_mathematics(
                        res.scene3d,
                        scene_id=f"contract-driven-goal-composition::{group_name}::{case['id']}",
                        data_source="research/contract-driven-goal-composition@a629ebee:corpus.json",
                        source_kind="backend_hybrid_route_d",
                        problem_text=case["text"],
                        expected_answers=res.answers,
                    )
                    backend_reports.append(_serialize_report(rep))

        orig_centroid = cdgc_registry.REGISTRY["centroid"]
        cdgc_registry.REGISTRY["centroid"] = experimental_centroid_contract(cdgc_registry)
        try:
            for case in corpus.get("discovery", []):
                res = run_fact_route(case["text"], case["payload"])
                if res.status == "SERVED" and res.scene3d:
                    rep = oracle.verify_scene_mathematics(
                        res.scene3d,
                        scene_id=f"contract-driven-goal-composition::discovery::{case['id']}",
                        data_source="research/contract-driven-goal-composition@a629ebee:corpus.json (with experimental_centroid_contract)",
                        source_kind="backend_hybrid_route_d",
                        problem_text=case["text"],
                        expected_answers=res.answers,
                    )
                    backend_reports.append(_serialize_report(rep))
        finally:
            cdgc_registry.REGISTRY["centroid"] = orig_centroid

    # Aggregate category check counts across all 148 scenes
    cat_totals: dict[str, dict[str, int]] = {}
    for rep_d in frontend_reports + backend_reports:
        for ck, cv in rep_d["category_results"].items():
            entry = cat_totals.setdefault(ck, {"checked_count": 0, "passed_scenes": 0, "failed_scenes": 0})
            entry["checked_count"] += int(cv["checked_count"])
            if cv["passed"]:
                entry["passed_scenes"] += 1
            else:
                entry["failed_scenes"] += 1

    summary = {
        "frontend_scenes_total": len(frontend_reports),
        "frontend_scenes_verified": sum(1 for r in frontend_reports if r["verdict"] == "VERIFIED"),
        "frontend_scenes_invalid": sum(1 for r in frontend_reports if r["verdict"] == "INVALID"),
        "backend_scenes_total": len(backend_reports),
        "backend_scenes_verified": sum(1 for r in backend_reports if r["verdict"] == "VERIFIED"),
        "backend_scenes_invalid": sum(1 for r in backend_reports if r["verdict"] == "INVALID"),
        "refusal_rows_total": len(refusal_rows),
        "total_served_scenes_audited": len(frontend_reports) + len(backend_reports),
        "total_served_scenes_verified": sum(
            1 for r in (frontend_reports + backend_reports) if r["verdict"] == "VERIFIED"
        ),
        "category_totals": cat_totals,
    }
    return frontend_reports, backend_reports, {"summary": summary, "refusal_rows": refusal_rows}


def _serialize_report(rep: oracle.SceneAuditReport) -> dict[str, Any]:
    d = asdict(rep)
    return d


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    frontend_reports, backend_reports, meta = collect_and_audit_all_scenes()
    counterexamples = oracle.run_counterexample_suite()

    catalog_payload = {
        "run": "step-math-validation",
        "baseline_main_commit": "4abc4afbb976babc4740bf22e42dc368a24c1b13",
        "frozen_backend_commit": "a629ebee346bf0083cf90294ad352640bcc936ce",
        "frontend_final_snapshot_status": "WAITING_FOR_FRONTEND_FINAL_SNAPSHOT",
        "summary": meta["summary"],
        "frontend_sample_and_fixture_scenes": frontend_reports,
        "backend_hybrid_route_d_scenes": backend_reports,
        "refusal_rows": meta["refusal_rows"],
    }
    catalog_path = RUN_DIR / "catalog-audit.json"
    catalog_path.write_text(json.dumps(catalog_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ce_payload = {
        "run": "step-math-validation",
        "total_counterexamples": len(counterexamples),
        "all_detected_by_oracle": all(c["oracle_detected"] for c in counterexamples),
        "counterexamples": counterexamples,
    }
    ce_path = RUN_DIR / "counterexamples.json"
    ce_path.write_text(json.dumps(ce_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    hashes = {
        "oracle.py": _sha256_file(RUN_DIR / "oracle.py"),
        "catalog-audit.json": _sha256_file(catalog_path),
        "counterexamples.json": _sha256_file(ce_path),
    }
    report_path = RUN_DIR / "report.md"
    if report_path.exists():
        hashes["report.md"] = _sha256_file(report_path)

    run_payload = {
        "run": "step-math-validation",
        "branch": "research/step-math-validation",
        "base_commit": "4abc4afbb976babc4740bf22e42dc368a24c1b13",
        "frozen_backend_branch": "research/contract-driven-goal-composition",
        "frozen_backend_commit": "a629ebee346bf0083cf90294ad352640bcc936ce",
        "live_ai_calls": 0,
        "allow_live_ai_env": "0",
        "frontend_reverification_status": "WAITING_FOR_FRONTEND_FINAL_SNAPSHOT",
        "summary": meta["summary"],
        "counterexamples_detected": f"{sum(1 for c in counterexamples if c['oracle_detected'])}/{len(counterexamples)}",
        "hashes": hashes,
    }
    run_path = RUN_DIR / "run.json"
    run_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"Audit complete: frontend={meta['summary']['frontend_scenes_verified']}/{meta['summary']['frontend_scenes_total']} VERIFIED, "
        f"backend={meta['summary']['backend_scenes_verified']}/{meta['summary']['backend_scenes_total']} VERIFIED, "
        f"counterexamples={run_payload['counterexamples_detected']}"
    )


if __name__ == "__main__":
    main()
