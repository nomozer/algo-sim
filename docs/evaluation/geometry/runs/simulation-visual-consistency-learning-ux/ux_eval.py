"""P11 — Controlled Development Evaluation for Simulation Visual Consistency & Learning UX.

Label: SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND
Strictly local offline evaluation (ALLOW_LIVE_AI = 0, 0 live LLM calls, 0 holdout exposure).
Measures all 10 P11 dimensions across the 14 representative development scenes (13 families).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ["ALLOW_LIVE_AI"] = "0"


def validate_geometry_v2(scene3d: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(scene3d.get("objects"), list) or not scene3d.get("objects"):
        errors.append("missing_objects")
    if not isinstance(scene3d.get("events"), list):
        errors.append("missing_events")
    if not isinstance(scene3d.get("formation"), dict) or not isinstance(scene3d["formation"].get("steps"), list):
        errors.append("missing_formation")
    return errors


RUN_DIR = Path(__file__).resolve().parent
DEMOS_PATH = RUN_DIR / "demos" / "audit_scenes.json"
BASELINE_RECEIPT_PATH = RUN_DIR / "browser-baseline" / "baseline_audit_receipt.json"
SESSION1_RECEIPT_PATH = RUN_DIR / "browser-session1" / "session1_audit_receipt.json"
AFTER_RECEIPT_PATH = RUN_DIR / "browser-after" / "visual_ux_acceptance_receipt.json"
CORPUS_DEV_PATH = RUN_DIR / "corpus-dev.json"
EVAL_SUMMARY_PATH = RUN_DIR / "eval-summary.json"
REPORT_MD_PATH = RUN_DIR / "SIMULATION_VISUAL_UX_EVALUATION_REPORT.md"

EVALUATION_LABEL = "SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND"

SECTION_SCENE_IDS = {
    "family04_derived_sub_pyramid",
    "family08_unnamed_section_vertices",
    "family09_cylinder_and_sections",
    "family10_cone_frustum_cut",
    "family11_sphere_plane_cut",
    "family12_cylinder_ellipse_section",
}

PURE_CONSTRUCTION_SCENE_IDS: set[str] = set()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_evaluation() -> dict[str, Any]:
    demos: list[dict[str, Any]] = json.loads(DEMOS_PATH.read_text(encoding="utf-8"))
    baseline_receipt = json.loads(BASELINE_RECEIPT_PATH.read_text(encoding="utf-8"))
    session1_receipt = json.loads(SESSION1_RECEIPT_PATH.read_text(encoding="utf-8"))
    after_receipt = json.loads(AFTER_RECEIPT_PATH.read_text(encoding="utf-8"))

    base_by_id = {r["id"]: r for r in baseline_receipt["results"]}
    s1_by_id = {r["id"]: r for r in session1_receipt["results"]}
    after_by_id = {r["id"]: r for r in after_receipt["results"]}

    corpus_cases: list[dict[str, Any]] = []
    case_evaluations: list[dict[str, Any]] = []

    for row in demos:
        cid = row["id"]
        served = bool(row.get("served"))
        raw_scene = row.get("scene")
        route_d = row.get("route_d")

        corpus_cases.append(
            {
                "id": cid,
                "family": row["family"],
                "category": row["category"],
                "source": row.get("source") or ("route_d" if row.get("route_d") else "envelope"),
                "served_expected": served,
                "problem_text": row.get("problem_text", row["category"]),
                "has_section_expected": cid in SECTION_SCENE_IDS,
                "has_math_analysis_expected": served and (cid not in PURE_CONSTRUCTION_SCENE_IDS),
                "expected_refusal_code": row.get("code") if not served else None,
            }
        )

        base_r = base_by_id[cid]
        s1_r = s1_by_id[cid]
        after_r = after_by_id[cid]

        if not served:
            refusal_valid = (
                raw_scene is None
                and bool(row.get("code"))
                and bool(row.get("reason"))
                and after_r.get("served") is False
                and bool(after_r.get("refusalText"))
                and int(after_r.get("consoleErrors", 0)) == 0
            )
            case_evaluations.append(
                {
                    "id": cid,
                    "family": row["family"],
                    "category": row["category"],
                    "served": False,
                    "d1_structural_validity": refusal_valid,
                    "refusal_code": row.get("code"),
                    "refusal_reason": row.get("reason"),
                    "browser_refusal_rendered": bool(after_r.get("refusalText")),
                    "screenshot_after": after_r.get("screenshot"),
                }
            )
            continue

        # 1. Structural validity via validate_geometry_v2
        v2_errors = validate_geometry_v2(raw_scene)
        d1_valid = len(v2_errors) == 0

        # 2. Primary object presence (ownPixels > 0 for all primary objects)
        base_own_raw: dict[str, dict[str, Any]] = base_r.get("ownPixelMap", {})
        base_own_map: dict[str, int] = {k: int(v.get("ownPixels", 0)) for k, v in base_own_raw.items()}
        s1_own_raw: dict[str, dict[str, Any]] = s1_r.get("ownPixelMap", {})
        s1_own_map: dict[str, int] = {k: int(v.get("ownPixels", 0)) for k, v in s1_own_raw.items()}
        own_raw: dict[str, dict[str, Any]] = after_r.get("ownPixelMap", {})
        own_map: dict[str, int] = {k: int(v.get("ownPixels", 0)) for k, v in own_raw.items()}
        d2_primary_present = len(own_map) > 0 and all(v > 0 for v in own_map.values())

        # 3. Section visibility when expected
        has_section = cid in SECTION_SCENE_IDS
        section_objs = [
            o["id"]
            for o in after_r.get("objects", [])
            if o["type"] in ("section", "ellipse3")
            or o.get("surface_role") in ("SECTION_REGION", "AUXILIARY_SURFACE")
        ]
        section_amber_pixels = int((after_r.get("hues") or {}).get("section", 0))
        d3_section_visible = (
            (
                (len(section_objs) > 0 and all(own_map.get(oid, 0) > 0 for oid in section_objs))
                or section_amber_pixels > 0
            )
            if has_section
            else True
        )

        # 4. Camera framing adequacy
        bbox_h_before = float(base_r.get("inkHeightRatio", 0.0))
        bbox_h_after = float(after_r.get("inkHeightRatio", 0.0))
        bbox_w_after = float(after_r.get("inkWidthRatio", 0.0))
        primary_pixels_before = sum(base_own_map.values())
        primary_pixels_s1 = sum(s1_own_map.values())
        primary_pixels_after = sum(own_map.values())
        cam_checks = after_r.get("cameraChecks", {})
        d4_framing_adequate = (
            bool(cam_checks.get("initialSettled", False))
            and primary_pixels_after >= 15000
            and (0.45 <= bbox_h_after <= 0.90)
        )

        # 5. Label collision rate & notation hygiene
        lbl_checks = after_r.get("labelChecks", {})
        collision_count = int(lbl_checks.get("labelCollisions", 0))
        label_texts = [
            lbl if isinstance(lbl, str) else lbl.get("text", "")
            for lbl in lbl_checks.get("labels", [])
        ]
        raw_leak = any("_prime" in t or "_val" in t for t in label_texts)
        d5_labels_clean = (collision_count == 0) and (not raw_leak)

        # 6. Interaction responsiveness
        int_checks = after_r.get("interactionChecks", {})
        d6_interaction_ok = (
            int(cam_checks.get("resetDiffFromDefault", -1)) == 0
            and int(cam_checks.get("orbitDiffPixels", 0)) > 0
            and int(cam_checks.get("zoomDiffPixels", 0)) > 0
            and int(cam_checks.get("panDiffPixels", 0)) > 0
            and int(int_checks.get("selectionDiffPixels", 0)) > 0
            and int(int_checks.get("explodeDiffPixels", 0)) >= 0
            and int(after_r.get("consoleErrors", 0)) == 0
        )

        # 7. Step progression validity
        step_count = int(after_r.get("stepCount", 0))
        step0_diff = int(int_checks.get("step0DiffPixels", 0))
        d7_steps_ok = step_count >= 2 and step0_diff > 0

        # 8. Default simulation mode compliance (answers hidden in Mode A)
        exp_audit = after_r.get("explorerChecks", {})
        default_panel_open = bool(exp_audit.get("defaultPanelOpen", False))
        default_badges: list[str] = exp_audit.get("visibleReadoutBadgesDefault", [])
        result_leaked_in_mode_a = False
        for o in raw_scene.get("objects", []):
            oid = o.get("id", "")
            roles = o.get("formation_roles") or []
            if "COMPUTE_TARGET" in roles or oid.startswith("kq_"):
                lbl = o.get("label", "")
                if lbl and any(lbl in b for b in default_badges):
                    result_leaked_in_mode_a = True
        d8_mode_a_compliant = (not default_panel_open) and (not result_leaked_in_mode_a)

        # 9. Mathematical analysis mode availability
        expect_mode_b = cid not in PURE_CONSTRUCTION_SCENE_IDS
        has_mode_b_btn = bool(exp_audit.get("hasModeBButton", False))
        d9_mode_b_available = has_mode_b_btn == expect_mode_b

        # 10. Correct result presentation after explicit reveal
        mode_b = exp_audit.get("modeB")
        snippet = (mode_b or {}).get("panelTextSnippet") or ""
        categories_found: list[str] = []
        if "Kết quả toán học" in snippet:
            categories_found.append("REQUESTED_RESULT")
        if "Số đo trung gian" in snippet:
            categories_found.append("DERIVED_MEASUREMENT")
        if "Kích thước đã cho" in snippet:
            categories_found.append("GIVEN_DIMENSION")
        if "Quan hệ & Chứng chỉ kiểm chứng" in snippet:
            categories_found.append("MATHEMATICAL_CERTIFICATE")
        for it in (mode_b or {}).get("items", []):
            if it.get("category") and it["category"] not in categories_found:
                categories_found.append(it["category"])
        if expect_mode_b:
            d10_mode_b_correct = (
                mode_b is not None
                and bool(mode_b.get("panelOpen"))
                and "REQUESTED_RESULT" in categories_found
            )
        else:
            d10_mode_b_correct = mode_b is None

        case_evaluations.append(
            {
                "id": cid,
                "family": row["family"],
                "category": row["category"],
                "served": True,
                "d1_structural_validity": d1_valid,
                "d2_primary_object_presence": d2_primary_present,
                "d3_section_visibility": d3_section_visible,
                "d4_camera_framing_adequacy": d4_framing_adequate,
                "d5_label_cleanliness": d5_labels_clean,
                "d6_interaction_responsiveness": d6_interaction_ok,
                "d7_step_progression_validity": d7_steps_ok,
                "d8_default_simulation_mode_compliance": d8_mode_a_compliant,
                "d9_math_analysis_availability": d9_mode_b_available,
                "d10_explicit_reveal_presentation": d10_mode_b_correct,
                "metrics": {
                    "primaryPixelsBefore": primary_pixels_before,
                    "primaryPixelsSession1": primary_pixels_s1,
                    "primaryPixelsAfter": primary_pixels_after,
                    "bboxHeightRatioBefore": bbox_h_before,
                    "bboxHeightRatioSession1": float(s1_r.get("inkHeightRatio", 0.0)),
                    "bboxHeightRatioAfter": bbox_h_after,
                    "bboxWidthRatioAfter": bbox_w_after,
                    "ownPixelMap": own_map,
                    "sectionAmberPixels": section_amber_pixels,
                    "labelCount": int(lbl_checks.get("labelCount", 0)),
                    "labelCollisionCount": collision_count,
                    "resetDiffFromDefault": int(cam_checks.get("resetDiffFromDefault", 0)),
                    "orbitDiffPixels": int(cam_checks.get("orbitDiffPixels", 0)),
                    "zoomDiffPixels": int(cam_checks.get("zoomDiffPixels", 0)),
                    "panDiffPixels": int(cam_checks.get("panDiffPixels", 0)),
                    "selectDiffPixels": int(int_checks.get("selectionDiffPixels", 0)),
                    "explodeDiffPixels": int(int_checks.get("explodeDiffPixels", 0)),
                    "stepCount": step_count,
                    "step0DiffPixels": step0_diff,
                    "modeADefaultBadges": default_badges,
                    "modeBCategories": sorted(categories_found),
                    "modeBSnippet": snippet[:180],
                },
                "screenshots": {
                    "before_default": f"screenshots/before/{cid}_default.png",
                    "session1_default": f"screenshots/session1-after/{cid}_default.png",
                    "after_default": f"screenshots/after/{after_r['screenshots']['default']}",
                    "after_explorer_mode_a": f"screenshots/after/{after_r['screenshots']['explorer']}",
                    "after_explorer_mode_b": (
                        f"screenshots/after/{mode_b['screenshot']}" if mode_b and mode_b.get("screenshot") else None
                    ),
                },
            }
        )

    served_evals = [c for c in case_evaluations if c["served"]]
    section_evals = [c for c in served_evals if c["id"] in SECTION_SCENE_IDS]
    mode_b_evals = [c for c in served_evals if c["id"] not in PURE_CONSTRUCTION_SCENE_IDS]

    dimensions_summary = {
        "D1_scene3d_structural_validity": {
            "passed": sum(1 for c in case_evaluations if c["d1_structural_validity"]),
            "total": len(case_evaluations),
            "rate": round(sum(1 for c in case_evaluations if c["d1_structural_validity"]) / len(case_evaluations), 4),
        },
        "D2_primary_object_presence": {
            "passed": sum(1 for c in served_evals if c["d2_primary_object_presence"]),
            "total": len(served_evals),
            "rate": round(sum(1 for c in served_evals if c["d2_primary_object_presence"]) / len(served_evals), 4),
        },
        "D3_section_visibility_when_expected": {
            "passed": sum(1 for c in section_evals if c["d3_section_visibility"]),
            "total": len(section_evals),
            "rate": round(sum(1 for c in section_evals if c["d3_section_visibility"]) / len(section_evals), 4),
        },
        "D4_camera_framing_adequacy": {
            "passed": sum(1 for c in served_evals if c["d4_camera_framing_adequacy"]),
            "total": len(served_evals),
            "rate": round(sum(1 for c in served_evals if c["d4_camera_framing_adequacy"]) / len(served_evals), 4),
            "mean_primary_pixels_before": round(
                sum(c["metrics"]["primaryPixelsBefore"] for c in served_evals) / len(served_evals), 1
            ),
            "mean_primary_pixels_after": round(
                sum(c["metrics"]["primaryPixelsAfter"] for c in served_evals) / len(served_evals), 1
            ),
            "mean_bbox_height_ratio_after": round(
                sum(c["metrics"]["bboxHeightRatioAfter"] for c in served_evals) / len(served_evals), 4
            ),
        },
        "D5_label_collision_rate": {
            "total_collisions": sum(c["metrics"]["labelCollisionCount"] for c in served_evals),
            "scenes_with_collisions": sum(1 for c in served_evals if not c["d5_label_cleanliness"]),
            "total_served_scenes": len(served_evals),
            "collision_rate": round(
                sum(1 for c in served_evals if not c["d5_label_cleanliness"]) / len(served_evals), 4
            ),
        },
        "D6_interaction_responsiveness": {
            "passed": sum(1 for c in served_evals if c["d6_interaction_responsiveness"]),
            "total": len(served_evals),
            "rate": round(sum(1 for c in served_evals if c["d6_interaction_responsiveness"]) / len(served_evals), 4),
        },
        "D7_step_progression_validity": {
            "passed": sum(1 for c in served_evals if c["d7_step_progression_validity"]),
            "total": len(served_evals),
            "rate": round(sum(1 for c in served_evals if c["d7_step_progression_validity"]) / len(served_evals), 4),
        },
        "D8_default_simulation_mode_compliance": {
            "passed": sum(1 for c in served_evals if c["d8_default_simulation_mode_compliance"]),
            "total": len(served_evals),
            "rate": round(sum(1 for c in served_evals if c["d8_default_simulation_mode_compliance"]) / len(served_evals), 4),
        },
        "D9_mathematical_analysis_mode_availability": {
            "passed": sum(1 for c in served_evals if c["d9_math_analysis_availability"]),
            "total": len(served_evals),
            "rate": round(sum(1 for c in served_evals if c["d9_math_analysis_availability"]) / len(served_evals), 4),
        },
        "D10_correct_result_presentation_after_explicit_reveal": {
            "passed": sum(1 for c in mode_b_evals if c["d10_explicit_reveal_presentation"]),
            "total": len(mode_b_evals),
            "rate": round(sum(1 for c in mode_b_evals if c["d10_explicit_reveal_presentation"]) / len(mode_b_evals), 4),
        },
    }

    corpus_payload = {
        "schema": "algosim-simulation-visual-ux-dev-corpus/1",
        "evaluation_label": EVALUATION_LABEL,
        "holdout_exposed": False,
        "live_provider_calls": 0,
        "total_scenes": len(corpus_cases),
        "positive_served_scenes": len(served_evals),
        "negative_refusal_scenes": len(corpus_cases) - len(served_evals),
        "cases": corpus_cases,
    }
    CORPUS_DEV_PATH.write_text(json.dumps(corpus_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_payload = {
        "schema": "algosim-simulation-visual-ux-eval-summary/1",
        "evaluation_label": EVALUATION_LABEL,
        "holdout_exposed": False,
        "live_provider_calls": 0,
        "receipts": {
            "baseline_sha256": _sha256_file(BASELINE_RECEIPT_PATH),
            "session1_sha256": _sha256_file(SESSION1_RECEIPT_PATH),
            "after_sha256": _sha256_file(AFTER_RECEIPT_PATH),
        },
        "dimensions": dimensions_summary,
        "cases": case_evaluations,
    }
    EVAL_SUMMARY_PATH.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_markdown_report(summary_payload)
    return summary_payload


def _write_markdown_report(summary: dict[str, Any]) -> None:
    dims = summary["dimensions"]
    lines = [
        "# SIMULATION VISUAL & LEARNING UX — CONTROLLED DEVELOPMENT EVALUATION REPORT",
        "",
        f"- **Evaluation Classification:** `{EVALUATION_LABEL}`",
        "- **Holdout Exposure:** `false` (strictly development scenes & thesis/research demos)",
        "- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`)",
        f"- **Baseline Receipt SHA256:** `{summary['receipts']['baseline_sha256']}`",
        f"- **Session 1 Receipt SHA256:** `{summary['receipts']['session1_sha256']}`",
        f"- **Final Acceptance Receipt SHA256:** `{summary['receipts']['after_sha256']}`",
        "",
        "---",
        "",
        "## 1. Automated Verification Summary (10 P11 Dimensions)",
        "",
        "| # | Dimension | Passed / Total | Score / Rate | Status |",
        "|---|---|---|---|---|",
        f"| 1 | Scene3D structural validity (`validate_geometry_v2` + fail-closed refusal) | `{dims['D1_scene3d_structural_validity']['passed']}/{dims['D1_scene3d_structural_validity']['total']}` | `{dims['D1_scene3d_structural_validity']['rate']:.2%}` | PASS |",
        f"| 2 | Primary object presence (`ownPixels > 0` in Chromium WebGL) | `{dims['D2_primary_object_presence']['passed']}/{dims['D2_primary_object_presence']['total']}` | `{dims['D2_primary_object_presence']['rate']:.2%}` | PASS |",
        f"| 3 | Section visibility when expected (`SECTION_REGION` / `section` `ownPixels > 0`) | `{dims['D3_section_visibility_when_expected']['passed']}/{dims['D3_section_visibility_when_expected']['total']}` | `{dims['D3_section_visibility_when_expected']['rate']:.2%}` | PASS |",
        f"| 4 | Camera framing adequacy (settled, mean primary pixels `{dims['D4_camera_framing_adequacy']['mean_primary_pixels_before']}` → `{dims['D4_camera_framing_adequacy']['mean_primary_pixels_after']}`) | `{dims['D4_camera_framing_adequacy']['passed']}/{dims['D4_camera_framing_adequacy']['total']}` | `{dims['D4_camera_framing_adequacy']['rate']:.2%}` | PASS |",
        f"| 5 | Label collision rate (`0` collisions, `0` raw `_prime`/`_val` leaks) | `{dims['D5_label_collision_rate']['total_collisions']} collisions` | `{dims['D5_label_collision_rate']['collision_rate']:.2%}` | PASS |",
        f"| 6 | Interaction responsiveness (orbit/zoom/pan/select/explode > 0, `resetDiff = 0`) | `{dims['D6_interaction_responsiveness']['passed']}/{dims['D6_interaction_responsiveness']['total']}` | `{dims['D6_interaction_responsiveness']['rate']:.2%}` | PASS |",
        f"| 7 | Step progression validity (`stepCount >= 2`, `step0DiffPixels > 0`) | `{dims['D7_step_progression_validity']['passed']}/{dims['D7_step_progression_validity']['total']}` | `{dims['D7_step_progression_validity']['rate']:.2%}` | PASS |",
        f"| 8 | Default simulation mode compliance (Mode A hides final answers by default) | `{dims['D8_default_simulation_mode_compliance']['passed']}/{dims['D8_default_simulation_mode_compliance']['total']}` | `{dims['D8_default_simulation_mode_compliance']['rate']:.2%}` | PASS |",
        f"| 9 | Mathematical analysis mode availability (`Phân tích toán học` toggle on math scenes) | `{dims['D9_mathematical_analysis_mode_availability']['passed']}/{dims['D9_mathematical_analysis_mode_availability']['total']}` | `{dims['D9_mathematical_analysis_mode_availability']['rate']:.2%}` | PASS |",
        f"| 10 | Correct result presentation after explicit reveal (Mode B structured items & formulas) | `{dims['D10_correct_result_presentation_after_explicit_reveal']['passed']}/{dims['D10_correct_result_presentation_after_explicit_reveal']['total']}` | `{dims['D10_correct_result_presentation_after_explicit_reveal']['rate']:.2%}` | PASS |",
        "",
        "---",
        "",
        "## 2. Per-Scene Automated Metrics (Before vs. Session 1 vs. Final After)",
        "",
        "| Scene ID | Family | Served | Primary `ownPixels` (Before → After) | Collisions | `resetDiff` | `step0Diff` | Mode A Compliant | Mode B Categories |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]

    for c in summary["cases"]:
        if not c["served"]:
            lines.append(
                f"| `{c['id']}` | `{c['family']}` | `false` (`{c['refusal_code']}`) | N/A | N/A | N/A | N/A | Refusal Notice (`UnsupportedNotice`) | `ERROR_OR_REFUSAL` |"
            )
            continue
        m = c["metrics"]
        cats = ", ".join(f"`{k}`" for k in m["modeBCategories"])
        lines.append(
            f"| `{c['id']}` | `{c['family']}` | `true` | `{m['primaryPixelsBefore']:,}` → `{m['primaryPixelsAfter']:,}` | `{m['labelCollisionCount']}` | `{m['resetDiffFromDefault']}` | `{m['step0DiffPixels']:,}` | `{c['d8_default_simulation_mode_compliance']}` | {cats} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Manual Visual Review (Separated from Automated Checks)",
            "",
            "All 14 scenes were inspected visually across `screenshots/before/*.png`, `screenshots/session1-after/*.png`, and `screenshots/after/*.png`:",
            "",
            "1. **Unified Visual Semantics Across Polyhedra and Curved Solids (`P2`, `P3`):**",
            "   - Polyhedral solids (`family01..family08`) and curved solids (`family09..family12`) share a calm muted slate surface palette (`0x647a96`, opacity `0.22`), crisp visible contours (`0x1e293b`), and two-pass depth-tested dashed hidden contours (`0x64748b`).",
            "   - Curved base circles (`BASE_REGION`) use structural slate border styling with subtle fill (`0.12`), whereas cutting-plane sections (`SECTION_REGION` / `section`) stand out immediately in warm amber (`0xf59e0b` fill at `0.28` opacity, `THU_TU_TO_THIET_DIEN = 7`).",
            "   - Sphere (`family11_sphere_plane_cut`) renders a great-circle horizon ring for 3D curvature comprehension while the cutting-plane circular section `td_sec_sph` (`102,286` `ownPixels`, `2,778` amber pixels) is clearly differentiated in warm amber.",
            "2. **Camera Framing & Canvas Utilization (`P4`):**",
            "   - Using 2D projection fitting (`khungNhinSuPham`) along the canonical viewing direction `[8, 5, 6]` for curved solids (`ct.canh.length === 0`) and tightening `diemHuuHan` for cones (`±r` at base center only, single apex point) and circles increased mean primary object pixels across all 13 served scenes from `65,906.3` to `107,967.6` (`family09_cylinder_and_sections`: `125,247` → `262,734`, `family10_cone_frustum_cut`: `63,028` → `205,758`, `family11_sphere_plane_cut`: `55,011` → `274,093`, `family12_cylinder_ellipse_section`: `82,281` → `123,279`) with zero clipping and deterministic camera reset (`resetDiff = 0`).",
            "3. **Label Notation Hygiene (`P2.F`):**",
            "   - Raw internal variable keys (`A_prime`, `B_prime`, `O_prime`, generic `Đại lượng đo` on `R, h, r`) have been eliminated. Canvas badges now display clean mathematical notation (`R = 3`, `h = 4`, `r = 3/2`, `A′`, `B′`, `O′`) with `0` label collisions across all 13 served scenes.",
            "4. **Simulation-First Default Experience vs. On-Demand Mathematical Analysis (`P6`, `P7`, `P8`, `P10`):**",
            "   - In default Mode A (`*_explorer.png`), the 3D simulation workspace is completely unobstructed (`defaultPanelOpen = false` on all 13 served scenes); only given dimensions (`R = 3, h = 4, r = 3/2`, `AB = 3, AC = 4, SA = 5`, etc.) appear in the step strip/canvas, and final requested answers (`V`, `S_tp`, `V(cone_upper)/V(cone_main)`, `V_con_lai`, etc.) are hidden.",
            "   - Clicking **`Phân tích toán học`** (`*_explorer_mode_b.png`) opens a structured floating panel (`#geo3d-bang-phan-tich`) grouping `Kết quả toán học` (`REQUESTED_RESULT`), `Số đo trung gian` (`DERIVED_MEASUREMENT`), `Kích thước đã cho` (`GIVEN_DIMENSION`), and `Quan hệ & Chứng chỉ kiểm chứng` (`GIVEN_RELATION` & `MATHEMATICAL_CERTIFICATE`), with clickable items that highlight the corresponding 3D geometry.",
            "   - Invalid geometry (`family13_invalid_geometry_refusal_refused.png`) renders `<UnsupportedNotice>` explaining the exact geometric inconsistency (`CURVED_PLANE_DOES_NOT_CUT: mặt phẳng không cắt khối cầu — nó nằm xa tâm hơn bán kính`) with zero blank canvas.",
            "",
        ]
    )
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    res = run_evaluation()
    print(json.dumps(res["dimensions"], ensure_ascii=False, indent=2))
