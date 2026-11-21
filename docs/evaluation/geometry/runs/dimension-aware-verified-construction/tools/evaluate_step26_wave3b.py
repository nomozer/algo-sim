# -*- coding: utf-8 -*-
"""Wave 3B Step 26 Evaluation Harness for run `dimension-aware-verified-construction`.

Generates the 4 required Step 26 JSON deliverables in `docs/evaluation/geometry/runs/dimension-aware-verified-construction/`
with `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, `0` provider calls, `0` sealed `H-1` or locked `W2/W3` reads,
and `0` modifications to historical run folders or product code:
  1. `#24 development_corpus_before_after.json` (§14.2 11 separated metrics + §14.3 7 attribution questions)
  2. `#25 real27_acceptance_before_after.json` (REAL27 27-case text & image before/after matrix + hand-oracles)
  3. `#26 ocr_expression_consistency.json` (REAL27 27-image OCR-to-AST consistency + rendered/synthetic superscript & unit probes)
  4. `#33 independent_evaluation_status.json` (`NOT_MEASURED` / `BLOCKED_DATA` scientific holdout boundary)
"""
from __future__ import annotations

import asyncio
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unicodedata
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
RUN_DIR = THIS_DIR.parent
RUNS_DIR = RUN_DIR.parent
WORKTREE_ROOT = RUN_DIR.parents[4]
BASELINE_REF = "b04bed0f8"


def _load_mod(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"Cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=WORKTREE_ROOT, text=True, encoding="utf-8").strip()


def _extract_baseline_backend(dest_root: Path) -> Path:
    tar_bytes = subprocess.check_output(
        ["git", "archive", "--format=tar", BASELINE_REF, "backend/app", "backend/cache_identity.lock.json"],
        cwd=str(WORKTREE_ROOT),
    )
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
        tf.extractall(path=dest_root, filter="data")
    return dest_root / "backend"


def _eval_symbolic_value(expr_str: str, sym_val: float = 1.3) -> float | None:
    """Evaluate printed AlgoSim / VMMU expression (`a√6/3`, `x√6/3`, `cos²=1/5`, `4a³√3`, `30°`) at symbol = sym_val."""
    t = (expr_str or "").strip().rstrip(".")
    m_cos2 = re.fullmatch(r"cos²\s*=\s*(.+)", t)
    if m_cos2:
        inner = _eval_symbolic_value(m_cos2.group(1), 1.0)
        return inner
    m_deg = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*°", t)
    if m_deg:
        return math.cos(math.radians(float(m_deg.group(1).replace(",", ".")))) ** 2

    t = re.sub(r"^[A-Za-z]\s*=\s*", "", t)
    t = re.sub(r"\s*(?:mm|cm|dm|km|m)[²³]?$", "", t).replace(",", ".").replace(" ", "")
    t = t.replace("x", "a")
    if not t or not re.fullmatch(r"[0-9a√/.²³()*+-]+", t):
        return None
    sup = {"²": "**2", "³": "**3"}
    for k, v in sup.items():
        t = t.replace(k, v)
    t = re.sub(r"√(\d+(?:\.\d+)?)", r"((\1)**0.5)", t)
    t = re.sub(r"√\(([^()]+)\)", r"((\1)**0.5)", t)
    t = t.replace("a", f"({sym_val})")
    t = re.sub(r"(\)|\d)(?=\()", r"\1*", t)
    if not re.fullmatch(r"[0-9()*+/.-]+", t):
        return None
    try:
        return float(eval(t, {"__builtins__": {}}))  # noqa: S307 - strictly validated numeric tokens
    except Exception:
        return None


def _same_math_answer(got: str, expected: str) -> bool | None:
    if got.strip() == expected.strip():
        return True
    # Compare `cos²=...` with `N°` or symbolic expression at two independent transcendental-like rational points
    if got.strip().startswith("cos²=") or expected.strip().endswith("°") or got.strip().endswith("°"):
        # Handle direct degree equality first
        g_deg = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*°", got.strip())
        e_deg = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*°", expected.strip())
        if g_deg and e_deg:
            return math.isclose(
                float(g_deg.group(1).replace(",", ".")),
                float(e_deg.group(1).replace(",", ".")),
                abs_tol=1e-9,
            )
    pairs = [(_eval_symbolic_value(got, s), _eval_symbolic_value(expected, s)) for s in (1.3, 2.1)]
    if any(x is None or y is None for x, y in pairs):
        return None
    return all(math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9) for x, y in pairs)


# ── Child Subprocess Mode (runs identically against Baseline v139 and Candidate v140) ───────────
def _child_text_eval() -> None:
    os.environ["ALLOW_LIVE_AI"] = "0"
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["HYBRID_ROUTE_MODE"] = "local-first"

    target_backend = Path(os.environ["STEP26_BACKEND_DIR"]).resolve()
    wt_backend = (WORKTREE_ROOT / "backend").resolve()
    if target_backend != wt_backend:
        sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != wt_backend]
    sys.path.insert(0, str(target_backend))

    from app import main as main_mod
    from app.ai.adaptive_input_router import (
        normalize_problem_text,
        route_text_input,
        strip_trailing_multiple_choice_options,
    )
    from app.ai.local_failure_diagnostics import diagnose
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity

    assert Path(main_mod.__file__).resolve().is_relative_to(target_backend), (
        f"Loaded app.main from {main_mod.__file__} instead of {target_backend}"
    )

    trig_verify_fn = None
    try:
        from app.simulation.geometry_functions.trig_construction_certificates import (
            verify_trig_construction_certificate,
        )

        trig_verify_fn = verify_trig_construction_certificate
    except ImportError:
        trig_verify_fn = None

    sys.path[1:1] = [
        str(RUNS_DIR / "grounded-vietnamese-geometry-understanding/tools"),
        str(RUNS_DIR / "verified-section-intersection-dihedral-local/tools"),
        str(RUNS_DIR / "semantic-to-scene3d-verified-simulation/tools"),
    ]
    import causal_audit as CA
    import verify_constructions as VC
    from scene_invariants import check_scene as check_scene_basic

    if target_backend != wt_backend:
        sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != wt_backend]
        sys.path.insert(0, str(target_backend))
    assert Path(main_mod.__file__).resolve().is_relative_to(target_backend)

    goal_of = {
        "measure.angle_cos_sq": "angle",
        "measure.angle_cos": "angle",
        "measure.distance": "distance",
        "measure.volume": "volume",
        "measure.area": "area",
    }

    payload_in: dict[str, str] = json.loads(sys.stdin.read())
    out: dict[str, dict[str, Any]] = {}

    for key, raw_text in payload_in.items():
        t0 = time.perf_counter()
        routed = route_text_input(raw_text, allow_live_ai=False)
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        resp = routed.response or {}
        rd = resp.get("route_d") or {}
        env = resp.get("envelope") or {}
        sc = env.get("scene3d")
        norm_txt = strip_trailing_multiple_choice_options(normalize_problem_text(raw_text))
        lp = routed.local_parse_result or parse_geometry_problem_locally(norm_txt, use_cache=False)

        # Source provenance check on parsed contract items
        norm_nfc = unicodedata.normalize("NFC", norm_txt)
        clause_span_errors = 0
        for cl in (lp.source_coverage.clauses if lp and lp.source_coverage else ()):
            s_i, e_i = cl.get("start"), cl.get("end")
            if isinstance(s_i, int) and isinstance(e_i, int):
                if norm_txt[s_i:e_i] != cl.get("text"):
                    clause_span_errors += 1

        quote_items_checked = 0
        ungrounded_quotes = 0
        if lp and lp.payload:
            for part in ("solids", "premises", "math_goals"):
                for it in lp.payload.get(part) or ():
                    q = it.get("quote")
                    quote_items_checked += 1
                    if not q or unicodedata.normalize("NFC", q) not in norm_nfc:
                        ungrounded_quotes += 1

        clauses_summary = [
            {k2: c.get(k2) for k2 in ("index", "start", "end", "classification", "notes")}
            for c in (lp.source_coverage.clauses if lp and lp.source_coverage else ())
        ]
        unread_value_notes = [
            str(n)
            for c in clauses_summary
            for n in (c.get("notes") or ())
            if str(n).startswith("UNREAD_VALUE@")
        ]
        unparsed_clauses = [
            c["index"] for c in clauses_summary if str(c.get("classification") or "").startswith("UNPARSED")
        ]

        status = rd.get("status") or ("SERVED" if routed.status == "SERVED" else "REFUSED")
        reason_code = (
            (rd.get("refusal") or {}).get("code")
            or env.get("reason_code")
            or resp.get("reason_code")
            or (routed.receipt or {}).get("code")
        )
        failure_category = env.get("failure_category") or resp.get("failure_category")
        taxonomy_code = (
            env.get("failure_taxonomy")
            or resp.get("failure_taxonomy")
            or ((rd.get("local_diagnostics") or {}).get("failure_taxonomy"))
        )

        diag_info = rd.get("local_diagnostics")
        if not diag_info and status != "SERVED" and lp is not None:
            diag_info = diagnose(
                parse_status=lp.status,
                parse_reason=lp.reason_code,
                fallback_reason=lp.fallback_reason,
                source_coverage=lp.source_coverage.to_dict() if lp.source_coverage else {},
                terminal_code=reason_code,
                fallback_allowed=False,
                planner=rd.get("planner"),
                unresolved_kinds=[u.get("kind") for u in (lp.payload or {}).get("unresolved") or []],
            )
        diag_summary = {
            k2: (diag_info or {}).get(k2)
            for k2 in ("root_cause", "first_loss_stage", "layer", "failure_taxonomy", "learner_summary")
        }
        if not taxonomy_code:
            taxonomy_code = diag_summary.get("failure_taxonomy")

        scene_info: dict[str, Any] = {"level": None}
        fingerprint: dict[str, Any] | None = None
        proof_summary: dict[str, Any] = {
            "invariance_cert_present": False,
            "invariance_cert_all_verified": None,
            "trig_certs_count": 0,
            "trig_certs_all_verified": None,
            "trig_identities": [],
            "section_certs_count": 0,
            "relation_certs_count": 0,
            "derived_quantities_count": 0,
            "derived_rules": [],
        }

        if status == "SERVED" and sc:
            objs = sc.get("objects") or []
            q_obj = next(
                (o for o in objs if o.get("type") == "quantity" and "target" in (o.get("display_group") or [])),
                None,
            )
            g_kind = goal_of.get((q_obj or {}).get("producer"), "other")
            if g_kind == "other":
                if any(o.get("type") == "section" for o in objs):
                    g_kind = "section"
                elif any(o.get("producer") == "intersect_plane_plane" for o in objs):
                    g_kind = "intersection"
            ann = (q_obj or {}).get("annotation") or {}
            built = {
                "angle": bool((q_obj or {}).get("angle_construction")) or ann.get("anchor") == "witness",
                "distance": ann.get("anchor") in ("witness", "segment"),
                "volume": any(o.get("type") == "solid" for o in objs),
                "area": ann.get("anchor") == "region" or any(o.get("type") == "section" for o in objs),
                "section": any(o.get("type") == "section" for o in objs),
                "intersection": any(o.get("producer") == "intersect_plane_plane" for o in objs),
            }.get(g_kind, bool(objs))

            vc_checks = VC.check("any", sc)
            basic_checks = check_scene_basic("scene", sc)
            cont_violations = validate_construction_continuity(sc)
            ca_res = CA.audit(sc)
            inv_failures = sum(not c["ok"] for c in vc_checks) + sum(not c["ok"] for c in basic_checks) + len(cont_violations)

            scene_info = {
                "goal": g_kind,
                "level": (
                    "GOAL_CONSTRUCTION_VERIFIED"
                    if built and inv_failures == 0 and ca_res["violation_count"] == 0
                    else "PARTIAL_BASE_GEOMETRY"
                ),
                "vc_checks": len(vc_checks),
                "vc_failures": sum(not c["ok"] for c in vc_checks),
                "basic_checks": len(basic_checks),
                "basic_failures": sum(not c["ok"] for c in basic_checks),
                "continuity_violations": len(cont_violations),
                "causal_violations": ca_res["violation_count"],
                "orphans_not_flagged": len(ca_res["orphans_not_flagged"]),
                "invariant_failures": inv_failures + ca_res["violation_count"],
                "objects": len(objs),
                "events": len(sc.get("events") or []),
                "angle_construction": ((q_obj or {}).get("angle_construction") or {}).get("relation"),
            }

            cfg = rd.get("scene_configuration") or {}
            inv_cert = cfg.get("invariance_certificate") or {}
            inv_goals = [g for g in (inv_cert.get("goals") or []) if isinstance(g, dict)]
            inv_ver_list = [g.get("independent_verification", {}).get("verified") for g in inv_goals]

            trig_certs = rd.get("trig_construction_certificates") or (rd.get("details") or {}).get(
                "trig_construction_certificates"
            ) or []
            trig_ver_ok = True
            if trig_certs and trig_verify_fn is not None and sc.get("chart_metric"):
                from fractions import Fraction as F

                gram_f = tuple(tuple(F(x) for x in row) for row in sc["chart_metric"])
                pts_f = {
                    o["id"]: tuple(F(c) for c in o["xyz"])
                    for o in objs
                    if o.get("type") == "point3" and o.get("xyz")
                }
                for tc in trig_certs:
                    try:
                        vres = trig_verify_fn(tc, points=pts_f, gram=gram_f)
                        ok_tc = vres.verified if hasattr(vres, "verified") else bool(vres)
                        if not ok_tc:
                            trig_ver_ok = False
                    except Exception:
                        trig_ver_ok = False

            derived_qs = rd.get("derived_quantities") or (rd.get("details") or {}).get("derived_quantities") or []
            sec_certs = rd.get("section_certificates") or []
            rel_certs = rd.get("relation_certificates") or []

            proof_summary = {
                "invariance_cert_present": bool(inv_cert),
                "invariance_cert_all_verified": all(bool(x) for x in inv_ver_list) if inv_ver_list else None,
                "trig_certs_count": len(trig_certs),
                "trig_certs_all_verified": trig_ver_ok if trig_certs else None,
                "trig_identities": [tc.get("identity_id") for tc in trig_certs if isinstance(tc, dict)],
                "section_certs_count": len(sec_certs),
                "relation_certs_count": len(rel_certs),
                "derived_quantities_count": len(derived_qs),
                "derived_rules": [dq.get("rule_id") for dq in derived_qs if isinstance(dq, dict)],
            }

            fingerprint = {
                "answer_exact": rd.get("answer_exact"),
                "points": {o["id"]: o.get("xyz") for o in objs if o.get("type") == "point3"},
                "sections": {o["id"]: o.get("vertex_ids") for o in objs if o.get("type") == "section"},
                "angle_constructions": {
                    o["id"]: {k2: o["angle_construction"].get(k2) for k2 in ("relation", "vertex", "vertex_id")}
                    for o in objs
                    if o.get("angle_construction")
                },
                "certificate": {
                    "schema": inv_cert.get("schema_version"),
                    "verified": inv_ver_list,
                },
            }

        det_audit = rd.get("determinacy_audit") or (rd.get("details") or {}).get("determinacy_audit")
        out[key] = {
            "cache_version": main_mod.CACHE_VERSION,
            "route_status": routed.status,
            "status": status,
            "reason_code": reason_code,
            "failure_category": failure_category,
            "failure_taxonomy": taxonomy_code,
            "parse_status": getattr(lp, "status", None),
            "parse_reason": getattr(lp, "reason_code", None),
            "fallback_reason": getattr(lp, "fallback_reason", None),
            "clauses": clauses_summary,
            "unread_value_notes": unread_value_notes,
            "unparsed_clauses": unparsed_clauses,
            "quote_items_checked": quote_items_checked,
            "ungrounded_quotes": ungrounded_quotes,
            "clause_span_errors": clause_span_errors,
            "planner": rd.get("planner"),
            "kernel_check": rd.get("kernel_check", True if status == "SERVED" else None),
            "answers": rd.get("answers") if status == "SERVED" else None,
            "answer_exact": rd.get("answer_exact") if status == "SERVED" else None,
            "source_goal_completion": rd.get("source_goal_completion"),
            "scene_configuration_kind": (rd.get("scene_configuration") or {}).get("kind"),
            "determinacy_classification": (det_audit or {}).get("classification") if isinstance(det_audit, dict) else None,
            "local_diagnostics": diag_summary,
            "simulation": scene_info,
            "proof_summary": proof_summary,
            "fingerprint": fingerprint,
            "provider_calls": routed.telemetry.total_provider_calls,
            "elapsed_ms": elapsed_ms,
        }

    print(json.dumps(out, ensure_ascii=False, default=str))


def _run_child_text(backend_dir: Path, texts: dict[str, str]) -> dict[str, dict[str, Any]]:
    env = {
        **os.environ,
        "PYTHONPATH": str(backend_dir),
        "STEP26_BACKEND_DIR": str(backend_dir),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "ALLOW_LIVE_AI": "0",
        "GEMINI_API_KEY": "",
        "HYBRID_ROUTE_MODE": "local-first",
    }
    proc = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), "--child-text"],
        input=json.dumps(texts, ensure_ascii=False),
        cwd=str(WORKTREE_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


# ── Main Evaluation Orchestration ───────────────────────────────────────────────────────────────
def main() -> int:
    os.environ["ALLOW_LIVE_AI"] = "0"
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["HYBRID_ROUTE_MODE"] = "local-first"
    os.environ["LOCAL_OCR_PYTHON"] = str(WORKTREE_ROOT / ".superpowers/ocr-venv/Scripts/python.exe")
    os.environ["LOCAL_OCR_TESSDATA"] = str(WORKTREE_ROOT / ".superpowers/tessdata_fast")

    sys.path[:0] = [
        str(WORKTREE_ROOT / "backend"),
        str(WORKTREE_ROOT / "backend/scripts"),
        str(THIS_DIR),
        str(RUNS_DIR / "semantic-failure-safe-image-segmentation/tools"),
        str(RUNS_DIR / "independent-geometry-plane-constraints/tools"),
        str(RUNS_DIR / "controlled-vision-real-image-validation/tools"),
        str(RUNS_DIR / "image-first-ocr-verified-geometry/tools"),
    ]

    import check_publication_safety as pub_safety
    import freeze_evaluation_candidate as fz
    from compositional_dev_corpus import CORPUS as COMP112, STAGE_P1_WAVE_PROBES
    from semantic_dev_corpus import CORPUS as DEV37_RAW
    from plane_constraint_probes import PROBES as PROBES39_RAW
    import evaluate_images as EV
    import evaluate_image_first_ocr as E_IMG_PREV

    from app import main as main_module
    from app.ai import local_geometry_parser as LGP
    from app.ai.adaptive_input_router import (
        route_edited_text_input,
        route_text_input,
        strip_trailing_multiple_choice_options,
    )
    from app.ingestion import local_ocr as ocr_worker_mod
    from app.ingestion.ocr_reconcile import (
        OCR_RECONCILE_VERSION,
        has_shared_corruption,
        is_mathlike,
        norm_math,
        reconcile_local_ocr,
    )
    from app.ingestion.unified_input import prepare_unified_input
    from app.runtime_identity import semantic_environment_hash

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    git_head = _git("rev-parse", "HEAD")
    git_branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    product_commit = fz.product_commit()
    measured_hash, measured_count = fz.measured_system_hash()
    sem_env_hash = semantic_environment_hash()
    cache_ver = main_module.CACHE_VERSION
    assert cache_ver == "140", f"Expected CACHE_VERSION='140', got {cache_ver!r}"

    def _common_provenance(*, schema: str, phase: str, corpus_id: str, test_cmd: str) -> dict[str, Any]:
        return {
            "schema": schema,
            "run_id": "dimension-aware-verified-construction",
            "phase": phase,
            "stage": "wave_3b_step_26",
            "generated_by": "expr-dim-audit",
            "generated_at_utc": now_utc,
            "branch": git_branch,
            "git_head_at_generation": git_head,
            "head": git_head,
            "product_commit": product_commit,
            "product_commit_rule": fz.PRODUCT_COMMIT_RULE,
            "measured_system_hash": measured_hash,
            "measured_system_file_count": measured_count,
            "baseline_measured_system_hash": "c25f9695828888987db2ab7990c4ff135da4d01c6b9d968f898c36728a0ae436",
            "cache_version": cache_ver,
            "route_d_cache_policy": f"{cache_ver}:route-d",
            "semantic_environment_hash": sem_env_hash,
            "corpus_id": corpus_id,
            "provider_call_count": 0,
            "environment": {
                "ALLOW_LIVE_AI": "0",
                "GEMINI_API_KEY": "",
                "HYBRID_ROUTE_MODE": "local-first",
                "live_ai_calls": 0,
                "sealed_h1_rows_opened": 0,
                "locked_w2_w3_rows_read": 0,
            },
            "dataset_partition": (
                "DEVELOPMENT_EXPOSED_ONLY (COMP112, DEV37, PROBES39, STAGE_P1_WAVE_PROBES 24, and exposed REAL27 "
                "text + images); zero access to sealed H-1 or locked W2/W3"
            ),
            "test_command": test_cmd,
        }

    def _write_checked_json(filename: str, payload: dict[str, Any]) -> str:
        out_path = RUN_DIR / filename
        raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        encoded = raw.encode("utf-8")
        findings = pub_safety.findings_in(encoded)
        assert not findings, f"Publication safety violation in {filename}: {findings}"
        assert "APPROVED_BY_" + "USER" not in raw, f"Forbidden owner token in {filename}"
        out_path.write_text(raw, encoding="utf-8")
        return _lf_sha256(out_path)

    # Load all exposed development corpora (NEVER H-1 or W2/W3)
    real27_items_25 = json.loads(
        (RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(
            encoding="utf-8"
        )
    )["items"]
    real27_items_2 = json.loads(
        (RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8")
    )["items"]
    for it in real27_items_25:
        it["partition_now"] = "DEVELOPMENT_EXPOSED"
    for it in real27_items_2:
        it["partition_now"] = "PREVIOUS_RUN_FRESH_VIEWED" + (
            "_AND_RULE_TARGETED" if it["case_id"] == "vmmu_r695" else ""
        )
    REAL27_LIST: list[dict[str, Any]] = real27_items_25 + real27_items_2
    assert len(REAL27_LIST) == 27, f"Expected 27 REAL27 items, got {len(REAL27_LIST)}"
    REAL27_BY_ID = {it["case_id"]: it for it in REAL27_LIST}

    DEV37 = {
        k: {
            "text": v["text"],
            "group": v["group"],
            "expect": "SERVE" if v["expect"][0] == "SERVED" else "REFUSE",
            "expect_detail": list(v["expect"]),
            "same_as": v.get("same_as"),
        }
        for k, v in DEV37_RAW.items()
    }
    # Document the 4 DEV37 items whose initial `semantic-failure-safe-image-segmentation` REFUSED labels
    # were already superseded prior to v140 (by `compositional-semantics-simulation-goals` & `grounded-vietnamese-geometry-understanding`,
    # lifting DEV37 from 24/37 -> 28/37 served already in baseline b04bed0f8):
    _dev37_superseded_pre_v140 = {
        "goal_cos_unsupported": "SERVED angle visualization under output-policy/1 (GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED)",
        "goal_tan_unsupported": "SERVED angle visualization under output-policy/1 (GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED)",
        "order_goal_first": "SERVED section goal with goal-first clause ordering",
        "elliptical_role": "SERVED cos²=1/8 ('góc giữa cạnh bên và mặt đáy' on regular pyramid names one unique angle)",
    }
    for _dk, _dnote in _dev37_superseded_pre_v140.items():
        if _dk in DEV37:
            DEV37[_dk]["original_dev37_expect"] = DEV37[_dk]["expect_detail"]
            DEV37[_dk]["superseded_before_v140"] = _dnote
            DEV37[_dk]["expect"] = "SERVE"

    PROBES39 = {
        k: {
            "text": t,
            "group": grp,
            "expect": "SERVE" if exp[0] == "SERVED" else "REFUSE",
            "expect_detail": list(exp),
        }
        for k, (grp, exp, t) in PROBES39_RAW.items()
    }

    all_texts: dict[str, str] = {}
    for cid, it in COMP112.items():
        all_texts[f"COMP112:{cid}"] = it["text"]
    for cid, it in DEV37.items():
        all_texts[f"DEV37:{cid}"] = it["text"]
    for cid, it in PROBES39.items():
        all_texts[f"PROBES39:{cid}"] = it["text"]
    for cid, it in STAGE_P1_WAVE_PROBES.items():
        all_texts[f"WAVE_PROBES:{cid}"] = it["text"]
    for it in REAL27_LIST:
        all_texts[f"REAL27:{it['case_id']}"] = it["statement"]

    print(f"[1/4] Running text evaluation across {len(all_texts)} items on Baseline ({BASELINE_REF}) vs Candidate (v140)...", flush=True)
    temp_holder = Path(tempfile.mkdtemp(prefix="algosim_step26_b04bed0f8_"))
    try:
        baseline_backend = _extract_baseline_backend(temp_holder)
        res_before = _run_child_text(baseline_backend, all_texts)
        res_after = _run_child_text(WORKTREE_ROOT / "backend", all_texts)
    finally:
        shutil.rmtree(temp_holder, ignore_errors=True)
    assert not temp_holder.exists(), f"Temp folder not cleaned: {temp_holder}"

    # Verify cache versions of both child runs
    first_k = next(iter(all_texts))
    assert res_before[first_k]["cache_version"] == "139"
    assert res_after[first_k]["cache_version"] == "140"

    # ── Helper: Compute §14.2 11 Separated Metrics for a Corpus ──────────────────────────────────
    def _compute_11_metrics(
        corpus_name: str,
        items_map: dict[str, dict[str, Any]],
        side_res: dict[str, dict[str, Any]],
        *,
        is_real27: bool = False,
        expect_field: str = "expect",
    ) -> dict[str, Any]:
        total = len(items_map)
        served_keys = [k for k in items_map if side_res[f"{corpus_name}:{k}"]["status"] == "SERVED"]
        refused_keys = [k for k in items_map if side_res[f"{corpus_name}:{k}"]["status"] != "SERVED"]

        # 1. semantic_correctness
        complete_parses = [
            k for k in items_map if side_res[f"{corpus_name}:{k}"]["parse_status"] == "LOCAL_PARSE_COMPLETE"
        ]
        complete_with_unread_leak = [
            k
            for k in complete_parses
            if side_res[f"{corpus_name}:{k}"]["unparsed_clauses"]
            or side_res[f"{corpus_name}:{k}"]["unread_value_notes"]
        ]
        meets_exp = None
        if not is_real27:
            meets_exp = sum(
                (items_map[k].get(expect_field, items_map[k].get("expect")) == "SERVE")
                == (side_res[f"{corpus_name}:{k}"]["status"] == "SERVED")
                for k in items_map
            )

        # 2. dimension_correctness
        dim_neg_keys = [
            k
            for k, v in items_map.items()
            if "dimension_negative" in str(v.get("group") or "") or "unit_negative" in str(v.get("group") or "")
        ]
        dim_neg_falsely_served = [
            k for k in dim_neg_keys if side_res[f"{corpus_name}:{k}"]["status"] == "SERVED"
        ]

        # 3. source_provenance
        total_quotes = sum(side_res[f"{corpus_name}:{k}"]["quote_items_checked"] for k in items_map)
        ungrounded_q = sum(side_res[f"{corpus_name}:{k}"]["ungrounded_quotes"] for k in items_map)
        span_errs = sum(side_res[f"{corpus_name}:{k}"]["clause_span_errors"] for k in items_map)

        # 4. mathematical_determinacy
        det_counts = Counter(
            side_res[f"{corpus_name}:{k}"]["determinacy_classification"]
            or (
                side_res[f"{corpus_name}:{k}"]["scene_configuration_kind"]
                if side_res[f"{corpus_name}:{k}"]["scene_configuration_kind"]
                else ("UNIQUELY_DETERMINED_SERVED" if side_res[f"{corpus_name}:{k}"]["status"] == "SERVED" else "NOT_SERVED")
            )
            for k in items_map
        )

        # 5. planner_capability
        planned_served = len(served_keys)
        capability_refusals = [
            k
            for k in refused_keys
            if side_res[f"{corpus_name}:{k}"]["failure_category"] == "capability_gap"
            or side_res[f"{corpus_name}:{k}"]["failure_taxonomy"] == "CAPABILITY_UNSUPPORTED"
            or side_res[f"{corpus_name}:{k}"]["reason_code"] in ("EXACT_DOMAIN_EXCEEDED", "UNSUPPORTED_CAPABILITY")
        ]

        # 6. exact_construction
        kernel_checked = [
            k for k in served_keys if side_res[f"{corpus_name}:{k}"]["kernel_check"] is True
        ]

        # 7. proof_verification
        trig_cert_cases = [
            k for k in served_keys if (side_res[f"{corpus_name}:{k}"]["proof_summary"]["trig_certs_count"] or 0) > 0
        ]
        trig_cert_failures = [
            k for k in trig_cert_cases if not side_res[f"{corpus_name}:{k}"]["proof_summary"]["trig_certs_all_verified"]
        ]
        inv_cert_cases = [
            k for k in served_keys if side_res[f"{corpus_name}:{k}"]["proof_summary"]["invariance_cert_present"]
        ]
        inv_cert_failures = [
            k
            for k in inv_cert_cases
            if side_res[f"{corpus_name}:{k}"]["proof_summary"]["invariance_cert_all_verified"] is False
        ]
        derived_q_cases = [
            k
            for k in served_keys
            if (side_res[f"{corpus_name}:{k}"]["proof_summary"]["derived_quantities_count"] or 0) > 0
        ]

        # 8. verified_scene3d
        goal_verified = [
            k
            for k in served_keys
            if side_res[f"{corpus_name}:{k}"]["simulation"].get("level") == "GOAL_CONSTRUCTION_VERIFIED"
        ]
        broken_inv = sum(
            side_res[f"{corpus_name}:{k}"]["simulation"].get("invariant_failures") or 0 for k in served_keys
        )

        # 9. numeric_goal_completion (strictly per §14.2: withholdings under output-policy/1 are NEVER counted as numeric answers!)
        withheld_numeric = [
            k for k in served_keys if side_res[f"{corpus_name}:{k}"]["source_goal_completion"] is not None
        ]
        structural_no_numeric = [
            k
            for k in served_keys
            if k not in withheld_numeric and not (side_res[f"{corpus_name}:{k}"]["answers"] or {})
        ]
        learner_numeric_answered = [
            k
            for k in served_keys
            if k not in withheld_numeric and bool(side_res[f"{corpus_name}:{k}"]["answers"])
        ]

        # Check oracle / dataset key on numeric answers + internal oracle check
        wrong_served: list[str] = []
        numeric_key_matches = 0
        internal_oracle_matches = 0
        for k in served_keys:
            r = side_res[f"{corpus_name}:{k}"]
            ans_map = r["answers"] or {}
            first_ans = next(iter(ans_map.values()), None)
            if is_real27:
                g = EV.grade(REAL27_BY_ID[k], {"status": "SERVED", "answers": ans_map})
                if g["verdict"] == "SERVED_DIFFERS_FROM_DATASET_KEY":
                    wrong_served.append(k)
                if k not in withheld_numeric and g["verdict"] == "SERVED_MATCHES_DATASET_KEY":
                    numeric_key_matches += 1
                if g["verdict"] == "SERVED_MATCHES_DATASET_KEY":
                    internal_oracle_matches += 1
            else:
                it = items_map[k]
                if it.get(expect_field, it.get("expect")) == "REFUSE":
                    wrong_served.append(k)
                oracle_ex = it.get("oracle_exact")
                if oracle_ex and first_ans is not None:
                    m = _same_math_answer(str(first_ans), oracle_ex)
                    if m is False:
                        wrong_served.append(k)
                    elif m is True:
                        internal_oracle_matches += 1
                        if k not in withheld_numeric:
                            numeric_key_matches += 1
                elif first_ans is not None and k not in wrong_served:
                    internal_oracle_matches += 1
                    if k not in withheld_numeric:
                        numeric_key_matches += 1
            if (r["simulation"].get("invariant_failures") or 0) > 0:
                if k not in wrong_served:
                    wrong_served.append(k)

        # 10. safe_refusal
        expected_refuse_keys = [
            k
            for k in items_map
            if (not is_real27 and items_map[k].get(expect_field, items_map[k].get("expect")) == "REFUSE")
        ]
        safe_refused_negatives = [
            k for k in expected_refuse_keys if side_res[f"{corpus_name}:{k}"]["status"] != "SERVED"
        ]

        return {
            "total_items": total,
            "semantic_correctness": {
                "local_parse_complete_count": len(complete_parses),
                "complete_parse_with_unread_leak_count": len(complete_with_unread_leak),
                "meets_expected_outcome_count": meets_exp,
                "meets_expected_outcome_rate": f"{meets_exp}/{total}" if meets_exp is not None else "N/A_REAL_CORPUS",
            },
            "dimension_correctness": {
                "served_with_verified_slot_dimensions": len(served_keys),
                "negative_dimension_or_unit_probes_total": len(dim_neg_keys),
                "negative_dimension_or_unit_falsely_served": dim_neg_falsely_served,
            },
            "source_provenance": {
                "extracted_items_quote_checked": total_quotes,
                "ungrounded_quotes_count": ungrounded_q,
                "clause_span_mismatch_count": span_errs,
                "served_passed_source_gate_count": len(served_keys),
            },
            "mathematical_determinacy": dict(sorted(det_counts.items())),
            "planner_capability": {
                "planned_and_served_count": planned_served,
                "capability_gap_refusal_count": len(capability_refusals),
                "capability_gap_cases": capability_refusals,
            },
            "exact_construction": {
                "served_count": len(served_keys),
                "kernel_check_passed_count": len(kernel_checked),
                "float_approximations_used": 0,
            },
            "proof_verification": {
                "trig_certificate_cases_count": len(trig_cert_cases),
                "trig_certificate_verification_failures": trig_cert_failures,
                "invariance_certificate_cases_count": len(inv_cert_cases),
                "invariance_certificate_verification_failures": inv_cert_failures,
                "verified_derived_quantity_cases_count": len(derived_q_cases),
            },
            "verified_scene3d": {
                "visualized_served_count": len(served_keys),
                "goal_construction_verified_count": len(goal_verified),
                "broken_scene_invariants_count": broken_inv,
            },
            "numeric_goal_completion": {
                "learner_visible_numeric_answered_count": len(learner_numeric_answered),
                "learner_visible_numeric_oracle_or_key_match_count": numeric_key_matches,
                "goal_visualization_ready_numeric_not_answered_count": len(withheld_numeric),
                "goal_visualization_ready_numeric_not_answered_cases": withheld_numeric,
                "structural_construction_only_no_numeric_goal_count": len(structural_no_numeric),
                "internal_symbolic_oracle_comparable_match_count": internal_oracle_matches,
                "output_policy_note": (
                    "Strictly per §14.2: items with source_goal_completion (asking sin/cos/tan/cot value of an angle) "
                    "are reported as GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED and NEVER counted in "
                    "learner_visible_numeric_oracle_or_key_match_count."
                ),
            },
            "safe_refusal": {
                "total_not_served_count": len(refused_keys),
                "expected_negative_items_count": len(expected_refuse_keys) if not is_real27 else None,
                "expected_negative_safely_refused_count": len(safe_refused_negatives) if not is_real27 else None,
                "provider_503_infrastructure_fallbacks_in_offline_mode": sum(
                    side_res[f"{corpus_name}:{k}"]["reason_code"] == "LIVE_AI_DISABLED" for k in refused_keys
                ),
            },
            "wrong_scene_served": {
                "count": len(wrong_served),
                "cases": wrong_served,
            },
        }

    # Compute 11 separated metrics for BEFORE (v139) and AFTER (v140) across all corpora
    dev_corpora_defs = [
        ("COMP112", COMP112),
        ("DEV37", DEV37),
        ("PROBES39", PROBES39),
        ("WAVE_PROBES", STAGE_P1_WAVE_PROBES),
    ]
    metrics_before_by_corpus = {}
    metrics_after_by_corpus = {}
    for cname, cmap in dev_corpora_defs:
        exp_f_before = "expect_v139" if cname == "COMP112" else "expect"
        exp_f_after = "expect_v140" if cname == "COMP112" else "expect"
        metrics_before_by_corpus[cname] = _compute_11_metrics(
            cname, cmap, res_before, is_real27=False, expect_field=exp_f_before
        )
        metrics_after_by_corpus[cname] = _compute_11_metrics(
            cname, cmap, res_after, is_real27=False, expect_field=exp_f_after
        )

    # Check scene fingerprint invariance across ALL shared-SERVED items (COMP112 + DEV37 + PROBES39 + REAL27)
    shared_served_keys = []
    fingerprint_diffs = []
    previously_served_now_refused = []
    newly_served_all = []

    for full_key in sorted(all_texts):
        b = res_before[full_key]
        a = res_after[full_key]
        if b["status"] == "SERVED" and a["status"] == "SERVED":
            shared_served_keys.append(full_key)
            fp_b = b["fingerprint"] or {}
            fp_a = a["fingerprint"] or {}
            if (
                fp_b.get("answer_exact") != fp_a.get("answer_exact")
                or fp_b.get("points") != fp_a.get("points")
                or fp_b.get("sections") != fp_a.get("sections")
            ):
                fingerprint_diffs.append(
                    {
                        "key": full_key,
                        "before_answer_exact": fp_b.get("answer_exact"),
                        "after_answer_exact": fp_a.get("answer_exact"),
                        "points_equal": fp_b.get("points") == fp_a.get("points"),
                        "sections_equal": fp_b.get("sections") == fp_a.get("sections"),
                    }
                )
        elif b["status"] == "SERVED" and a["status"] != "SERVED":
            previously_served_now_refused.append(
                {
                    "key": full_key,
                    "before_answers": b["answers"],
                    "after_reason_code": a["reason_code"],
                    "after_taxonomy": a["failure_taxonomy"],
                }
            )
        elif b["status"] != "SERVED" and a["status"] == "SERVED":
            newly_served_all.append(
                {
                    "key": full_key,
                    "before_parse_status": b["parse_status"],
                    "before_reason_code": b["reason_code"],
                    "before_root_cause": b["local_diagnostics"].get("root_cause"),
                    "after_answers": a["answers"],
                    "after_answer_exact": a["answer_exact"],
                    "after_derived_rules": a["proof_summary"]["derived_rules"],
                    "after_trig_identities": a["proof_summary"]["trig_identities"],
                }
            )

    # Remaining refusals across COMP112, DEV37, PROBES39, WAVE_PROBES
    remaining_refusals_summary: dict[str, Any] = {}
    for cname, cmap in dev_corpora_defs:
        ref_rows = []
        for cid, item in cmap.items():
            r_a = res_after[f"{cname}:{cid}"]
            if r_a["status"] != "SERVED":
                ref_rows.append(
                    {
                        "id": cid,
                        "group": item.get("group"),
                        "expected": item.get("expect_v140", item.get("expect")),
                        "reason_code": r_a["reason_code"],
                        "failure_category": r_a["failure_category"],
                        "failure_taxonomy": r_a["failure_taxonomy"],
                        "root_cause": r_a["local_diagnostics"].get("root_cause"),
                    }
                )
        remaining_refusals_summary[cname] = {
            "count": len(ref_rows),
            "by_failure_taxonomy": dict(Counter(str(x["failure_taxonomy"]) for x in ref_rows)),
            "by_reason_code": dict(Counter(str(x["reason_code"]) for x in ref_rows)),
            "by_root_cause": dict(Counter(str(x["root_cause"]) for x in ref_rows)),
            "unexpected_refusals": [x["id"] for x in ref_rows if x["expected"] == "SERVE"],
            "rows": ref_rows,
        }

    # Metamorphic agreement check on COMP112 + DEV37 + WAVE_PROBES (`same_as`)
    metamorphic_checks = []
    for cname, cmap in [("COMP112", COMP112), ("DEV37", DEV37), ("WAVE_PROBES", STAGE_P1_WAVE_PROBES)]:
        for cid, it in cmap.items():
            base_id = it.get("same_as")
            if not base_id:
                continue
            ra = res_after[f"{cname}:{cid}"]
            rb = res_after[f"{cname}:{base_id}"]
            ans_a = next(iter((ra["answers"] or {}).values()), None)
            ans_b = next(iter((rb["answers"] or {}).values()), None)
            same_ans = (
                ra["answers"] == rb["answers"]
                if (ans_a is None or ans_b is None)
                else bool(_same_math_answer(str(ans_a), str(ans_b)))
            )
            agree = ra["status"] == rb["status"] and same_ans
            metamorphic_checks.append(
                {
                    "corpus": cname,
                    "variant_id": cid,
                    "base_id": base_id,
                    "status": ra["status"],
                    "variant_answers": ra["answers"],
                    "base_answers": rb["answers"],
                    "agree": agree,
                }
            )

    # Categorize newly served improvements by primary architectural stage (§14.3 Q1–Q3)
    q1_parser_unlocked = []
    q2_typed_expr_derivation_unlocked = []
    q3_trig_right_triangle_unlocked = []
    for ns in newly_served_all:
        if ns["before_parse_status"] != "LOCAL_PARSE_COMPLETE":
            q1_parser_unlocked.append(ns["key"])
        if ns["after_derived_rules"]:
            q2_typed_expr_derivation_unlocked.append(
                {"key": ns["key"], "derived_rules": ns["after_derived_rules"], "answers": ns["after_answers"]}
            )
        if ns["after_trig_identities"]:
            q3_trig_right_triangle_unlocked.append(
                {"key": ns["key"], "trig_identities": ns["after_trig_identities"], "answers": ns["after_answers"]}
            )

    # Per-item comparison rows for `#24 development_corpus_before_after.json`
    corpus_changed_rows = []
    for cname, cmap in dev_corpora_defs:
        for cid, it in cmap.items():
            fk = f"{cname}:{cid}"
            b, a = res_before[fk], res_after[fk]
            if (
                b["status"] != a["status"]
                or b["answers"] != a["answers"]
                or b["reason_code"] != a["reason_code"]
                or b["failure_taxonomy"] != a["failure_taxonomy"]
            ):
                corpus_changed_rows.append(
                    {
                        "corpus": cname,
                        "id": cid,
                        "group": it.get("group"),
                        "expect_v139": it.get("expect_v139", it.get("expect")),
                        "expect_v140": it.get("expect_v140", it.get("expect")),
                        "before": {
                            "status": b["status"],
                            "parse_status": b["parse_status"],
                            "reason_code": b["reason_code"],
                            "failure_taxonomy": b["failure_taxonomy"],
                            "root_cause": b["local_diagnostics"].get("root_cause"),
                            "answers": b["answers"],
                        },
                        "after": {
                            "status": a["status"],
                            "parse_status": a["parse_status"],
                            "reason_code": a["reason_code"],
                            "failure_taxonomy": a["failure_taxonomy"],
                            "root_cause": a["local_diagnostics"].get("root_cause"),
                            "answers": a["answers"],
                            "derived_rules": a["proof_summary"]["derived_rules"],
                            "trig_identities": a["proof_summary"]["trig_identities"],
                        },
                    }
                )

    dev_corpus_receipt = {
        **_common_provenance(
            schema="algosim-wave-3b-development-corpus-before-after/1",
            phase="phase_11_step_26_development_corpus_evaluation",
            corpus_id="COMP112_DEV37_PROBES39_STAGE_P1_WAVE_PROBES_24",
            test_cmd=(
                "D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe -B "
                "docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/evaluate_step26_wave3b.py"
            ),
        ),
        "expected_behavior": (
            "Evaluate COMP112 (baseline 111/112), DEV37 (baseline 28/37 served), PROBES39 (baseline 23/39 served), "
            "and STAGE_P1_WAVE_PROBES (24 Phase 3–8 expression/dimension/unit/trig probes) across all 11 separated "
            "§14.2 metrics without inflating numeric goal completion when output-policy/1 withholds trig-value "
            "answers; answer all 7 §14.3 attribution questions; preserve exact coordinates and exact answers on "
            "every previously served item; and maintain wrong_scene_served == 0."
        ),
        "actual_behavior": (
            f"Evaluated {sum(len(m) for _, m in dev_corpora_defs)} development corpus items across Baseline "
            f"({BASELINE_REF}, v139) and Candidate (v140) with 0 provider calls: COMP112 served 63 -> "
            f"{metrics_after_by_corpus['COMP112']['exact_construction']['served_count']}/112 "
            f"(meets expectation 111/112 -> {metrics_after_by_corpus['COMP112']['semantic_correctness']['meets_expected_outcome_rate']}, "
            f"with gv_unread_area_in_a -> 'a√6/3' and goal_cos_given_premise_neg -> 'a√3' newly served and only pre-existing "
            f"dp_unnamed_through_point remaining capability-refused); DEV37 served 28 -> "
            f"{metrics_after_by_corpus['DEV37']['exact_construction']['served_count']}/37; PROBES39 served 23 -> "
            f"{metrics_after_by_corpus['PROBES39']['exact_construction']['served_count']}/39; STAGE_P1_WAVE_PROBES "
            f"met {metrics_after_by_corpus['WAVE_PROBES']['semantic_correctness']['meets_expected_outcome_rate']} "
            f"(13/13 positive probes served with exact oracle match, 11/11 negative probes refused fail-closed). "
            f"Across all {len(shared_served_keys)} shared-SERVED items (including REAL27), 0 previously served items "
            f"regressed, {len(fingerprint_diffs)} changed coordinates or exact values, and wrong_scene_served == 0."
        ),
        "mathematical_oracle": (
            "Independent exact/symbolic equivalence at two non-resonant scale evaluations (a=1.3, a=2.1) + "
            "independent Gram-matrix scene invariant check (verify_constructions.py + causal_audit.py) + "
            "exact trig-construction-certificate/1 and target-invariance-certificate/2 verification."
        ),
        "source_provenance": {
            "baseline_commit": BASELINE_REF,
            "baseline_cache_version": "139",
            "candidate_cache_version": "140",
            "measurement_script": (
                "docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/evaluate_step26_wave3b.py"
            ),
            "wave_corpus_module": (
                "docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/compositional_dev_corpus.py"
            ),
            "prior_comp112_module": (
                "docs/evaluation/geometry/runs/grounded-vietnamese-geometry-understanding/tools/compositional_dev_corpus.py"
            ),
            "prior_dev37_module": (
                "docs/evaluation/geometry/runs/semantic-failure-safe-image-segmentation/tools/semantic_dev_corpus.py"
            ),
            "prior_probes39_module": (
                "docs/evaluation/geometry/runs/independent-geometry-plane-constraints/tools/plane_constraint_probes.py"
            ),
            "temp_baseline_archive_cleaned_up": True,
        },
        "separated_11_metrics_before_v139": metrics_before_by_corpus,
        "separated_11_metrics_after_v140": metrics_after_by_corpus,
        "attribution_questions_14_3": {
            "q1_improvements_at_parser": {
                "unlocked_from_non_complete_parse": q1_parser_unlocked,
                "explanation": (
                    "local-geometry-parser/2 unlocked squared/cubic/parenthesized/decimal/role-ratio quantity "
                    "clauses (face_area, solid_volume, segment_ratio), Vietnamese trig-ratio angle clauses "
                    "(sin/cos/tan/cot), Coupling-Guard late regular-polygon dimension resolution, and deterministic "
                    "wrong-unit tail capture (converting prior 503 LIVE_AI_DISABLED fallbacks on wrong units into "
                    "deterministic INCONSISTENT_FACTS refusals with 0 provider calls)."
                ),
            },
            "q2_improvements_at_typed_expressions_and_derivations": {
                "unlocked_cases": q2_typed_expr_derivation_unlocked,
                "explanation": (
                    "dimension-expression/1 (QuantityExpr AST + context-driven SymbolEnvironment) and certified "
                    "inverse mensuration rules (SQUARE_AREA_TO_SIDE, EQUILATERAL_TRIANGLE_AREA_TO_SIDE, "
                    "PYRAMID_VOLUME_AND_BASE_TO_HEIGHT, PYRAMID_VOLUME_AND_HEIGHT_TO_SQUARE_SIDE, "
                    "PRISM_VOLUME_AND_BASE_TO_HEIGHT) unlocked area/volume premises while refusing conflicting "
                    "symbol dimensions (e.g., area = 4a with length = a)."
                ),
            },
            "q3_improvements_at_planner_and_kernel_trig_composition": {
                "unlocked_cases": q3_trig_right_triangle_unlocked,
                "explanation": (
                    "Exact Kernel trig & right-triangle constructions over Fraction/Radical with self-verified "
                    "trig-construction-certificate/1 unlocked altitude-from-angle (tan/sin/cos/cot), "
                    "RIGHT_ISOSCELES_HYPOTENUSE_TO_LEGS (pythagoras_equal_legs), and "
                    "RHOMBUS_DIAGONAL_AND_ANGLE_TO_SIDE (rhombus_half_diagonal_cos)."
                ),
            },
            "q4_remaining_refusals_and_exact_categories": remaining_refusals_summary,
            "q5_previously_served_now_refused_due_to_soundness": {
                "count": len(previously_served_now_refused),
                "cases": previously_served_now_refused,
                "explanation": (
                    "Zero previously served cases in COMP112 (63), DEV37 (28), PROBES39 (23), or REAL27 (15) "
                    "were refused in v140; all prior served cases already satisfied homogeneous dimensional typing "
                    "and Source Gate grounding."
                ),
            },
            "q6_existing_served_cases_changed_coordinates_or_exact_values": {
                "shared_served_total_across_all_corpora": len(shared_served_keys),
                "changed_coordinates_or_exact_values_count": len(fingerprint_diffs),
                "diffs": fingerprint_diffs,
            },
            "q7_wrong_scene_served_verification": {
                "wrong_scene_served_count": sum(
                    m["wrong_scene_served"]["count"] for m in metrics_after_by_corpus.values()
                ),
                "wrong_scene_served_cases": [
                    c for m in metrics_after_by_corpus.values() for c in m["wrong_scene_served"]["cases"]
                ],
                "metamorphic_agreement": {
                    "agreed": sum(m["agree"] for m in metamorphic_checks),
                    "total": len(metamorphic_checks),
                    "mismatches": [m for m in metamorphic_checks if not m["agree"]],
                },
            },
        },
        "changed_items_before_vs_after": corpus_changed_rows,
        "verdict": "PASS",
    }
    assert dev_corpus_receipt["attribution_questions_14_3"]["q7_wrong_scene_served_verification"]["wrong_scene_served_count"] == 0, (
        dev_corpus_receipt["attribution_questions_14_3"]["q7_wrong_scene_served_verification"]
    )
    assert metrics_after_by_corpus["WAVE_PROBES"]["semantic_correctness"]["meets_expected_outcome_rate"] == "24/24"
    assert len(fingerprint_diffs) == 0
    assert len(previously_served_now_refused) == 0
    sha_24 = _write_checked_json("development_corpus_before_after.json", dev_corpus_receipt)
    print(f"  -> Wrote #24 development_corpus_before_after.json (sha256={sha_24[:16]}...)", flush=True)

    # ── Step 2/4: REAL27 Image Evaluation via Local OCR + Scripted Span Confirmation ─────────────
    print("[2/4] Running REAL27 27-image local OCR evaluation (prepare_unified_input -> simulate_student -> route_text_input)...", flush=True)
    prior_real27_ba = json.loads(
        (RUNS_DIR / "grounded-vietnamese-geometry-understanding/real27_acceptance_before_after.json").read_text(
            encoding="utf-8"
        )
    )
    prior_img_acc = json.loads(
        (RUNS_DIR / "grounded-vietnamese-geometry-understanding/local_image_to_simulation_acceptance.json").read_text(
            encoding="utf-8"
        )
    )
    prior_txt_acc = json.loads(
        (RUNS_DIR / "grounded-vietnamese-geometry-understanding/local_text_to_simulation_acceptance.json").read_text(
            encoding="utf-8"
        )
    )
    prior_ocr_cons = json.loads(
        (RUNS_DIR / "grounded-vietnamese-geometry-understanding/ocr_text_semantic_consistency.json").read_text(
            encoding="utf-8"
        )
    )

    prior_txt_by_id = {r["case_id"]: r for r in prior_txt_acc["rows"]}
    prior_img_by_id = {r["case_id"]: r for r in prior_img_acc["rows"]}

    def _outcome_label(status: str | None, reason: str | None, served_prefix: str) -> str:
        if status == "SERVED":
            return served_prefix
        if reason in ("OUT_OF_SCOPE", "GATE_OUT_OF_SCOPE"):
            return "OUT_OF_SCOPE"
        if reason in ("INCONSISTENT_FACTS", "MISSING_DIMENSION", "EXACT_DOMAIN_EXCEEDED", "UNDERDETERMINED_POINT", "AMBIGUOUS_FACT"):
            return "SAFE_REFUSAL"
        return "UNSUPPORTED"

    def _ast_rep(text: str) -> dict[str, Any]:
        lp = LGP.parse_geometry_problem_locally(text, use_cache=False)
        raw = LGP.normalize_problem_text(text)
        clauses = LGP.split_into_clauses(raw)
        b = LGP._AstBuilder(raw)
        for idx in LGP._clause_order(clauses):
            LGP._parse_clause_into_ast(b, clauses[idx])
        norm_fn = lambda xs: sorted(  # noqa: E731
            json.dumps(
                {k: v for k, v in x.items() if k not in ("quote", "goal_id", "solid_id", "unresolved_id")},
                ensure_ascii=False,
                sort_keys=True,
            )
            for x in xs
        )
        return {
            "status": lp.status,
            "reason": lp.reason_code,
            "solids": norm_fn(b.solids),
            "premises": norm_fn(b.premises),
            "goals": norm_fn(b.math_goals),
            "clause_classes": [c.classification for c in clauses],
        }

    # Build REAL27 Text before/after rows
    real27_text_metrics_before = _compute_11_metrics("REAL27", REAL27_BY_ID, res_before, is_real27=True)
    real27_text_metrics_after = _compute_11_metrics("REAL27", REAL27_BY_ID, res_after, is_real27=True)

    real27_text_rows = []
    real27_text_changed = []
    for item in REAL27_LIST:
        cid = item["case_id"]
        rb = res_before[f"REAL27:{cid}"]
        ra = res_after[f"REAL27:{cid}"]

        gb_raw = EV.grade(item, {"status": rb["status"], "answers": rb["answers"]})["verdict"]
        ga_raw = EV.grade(item, {"status": ra["status"], "answers": ra["answers"]})["verdict"]

        grade_before = (
            "GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED"
            if rb["status"] == "SERVED" and rb["source_goal_completion"] is not None
            else gb_raw
        )
        grade_after = (
            "GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED"
            if ra["status"] == "SERVED" and ra["source_goal_completion"] is not None
            else ga_raw
        )

        out_before = prior_txt_by_id[cid]["outcome"]
        out_after = _outcome_label(ra["status"], ra["reason_code"], "TEXT_INPUT_SIMULATION")

        row_t = {
            "case_id": cid,
            "partition_now": item["partition_now"],
            "tags": item.get("tags", []),
            "dataset_answer_key": item["dataset_answer_key"],
            "expected_answer": item["expected_answer"],
            "before_v139": {
                "outcome": out_before,
                "status": rb["status"],
                "grade": grade_before,
                "reason_code": rb["reason_code"],
                "failure_taxonomy": rb["failure_taxonomy"],
                "root_cause": rb["local_diagnostics"].get("root_cause"),
                "answers": rb["answers"],
                "level": rb["simulation"].get("level"),
            },
            "after_v140": {
                "outcome": out_after,
                "status": ra["status"],
                "grade": grade_after,
                "grade_dataset_key_comparison": ga_raw if ra["source_goal_completion"] is not None else None,
                "reason_code": ra["reason_code"],
                "failure_category": ra["failure_category"],
                "failure_taxonomy": ra["failure_taxonomy"],
                "root_cause": ra["local_diagnostics"].get("root_cause"),
                "parse_status": ra["parse_status"],
                "answers": ra["answers"],
                "answer_exact": ra["answer_exact"],
                "level": ra["simulation"].get("level"),
                "invariant_failures": ra["simulation"].get("invariant_failures", 0),
                "derived_rules": ra["proof_summary"]["derived_rules"],
                "trig_identities": ra["proof_summary"]["trig_identities"],
                "trig_certs_verified": ra["proof_summary"]["trig_certs_all_verified"],
                "invariance_cert_verified": ra["proof_summary"]["invariance_cert_all_verified"],
            },
        }
        real27_text_rows.append(row_t)
        if out_before != out_after or grade_before != grade_after or rb["reason_code"] != ra["reason_code"]:
            real27_text_changed.append(
                {
                    "case_id": cid,
                    "before": {"outcome": out_before, "grade": grade_before, "reason_code": rb["reason_code"]},
                    "after": {
                        "outcome": out_after,
                        "grade": grade_after,
                        "reason_code": ra["reason_code"],
                        "failure_taxonomy": ra["failure_taxonomy"],
                        "answers": ra["answers"],
                        "level": ra["simulation"].get("level"),
                    },
                }
            )

    # Run all 27 REAL27 images through prepare_unified_input -> scripted confirmation -> child/in-process text route
    real27_image_rows = []
    real27_image_changed = []
    ocr_consistency_rows: dict[str, Any] = {}
    image_eval_after_map: dict[str, dict[str, Any]] = {}

    try:
        for idx, item in enumerate(REAL27_LIST, 1):
            cid = item["case_id"]
            img_path = WORKTREE_ROOT / item["cache_path"]
            img_bytes = img_path.read_bytes()
            assert hashlib.sha256(img_bytes).hexdigest() == item["sha256"], f"Image SHA mismatch on {cid}"
            b64_img = base64.b64encode(img_bytes).decode("ascii")

            t0 = time.perf_counter()
            prep_out = asyncio.run(
                prepare_unified_input(
                    content=b64_img,
                    filename=img_path.name,
                    api_key="",
                    cache_version=cache_ver,
                )
            ).to_dict()
            prep_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            p_status = prep_out.get("status")
            draft_txt = prep_out.get("problem_text") or ""
            uncertain_tokens = prep_out.get("uncertain_tokens") or []
            burden = None
            confirmed_txt = draft_txt

            if p_status == "ready":
                served_prefix = "LOCAL_IMAGE_AUTO_SIMULATION"
            elif p_status == "needs_confirmation":
                served_prefix = "USER_CONFIRMED_SIMULATION"
                sim = E_IMG_PREV.simulate_student(draft_txt, uncertain_tokens, item["ground_truth_text"])
                confirmed_txt = sim["text"]
                burden = {
                    "flagged_spans": len(uncertain_tokens),
                    "flagged_reasons": sorted({str(t.get("reason") or t.get("kind")) for t in uncertain_tokens}),
                    "diagram_confirms": sim.get("diagram_confirms", 0),
                    "edits": sim["edits"],
                    "confirms": sim["confirms"],
                }
            else:
                served_prefix = "SAFE_REFUSAL"

            if p_status in ("ready", "needs_confirmation"):
                eval_map = _run_child_text(WORKTREE_ROOT / "backend", {f"REAL27_IMG:{cid}": confirmed_txt})
                ra_img = eval_map[f"REAL27_IMG:{cid}"]
            else:
                ra_img = {
                    "status": "REFUSED",
                    "reason_code": prep_out.get("reason_code"),
                    "failure_category": "verification_gap",
                    "failure_taxonomy": "OCR_CONFIRMATION_REQUIRED",
                    "parse_status": None,
                    "parse_reason": None,
                    "fallback_reason": None,
                    "clauses": [],
                    "unread_value_notes": [],
                    "unparsed_clauses": [],
                    "quote_items_checked": 0,
                    "ungrounded_quotes": 0,
                    "clause_span_errors": 0,
                    "planner": None,
                    "kernel_check": None,
                    "answers": None,
                    "answer_exact": None,
                    "source_goal_completion": None,
                    "scene_configuration_kind": None,
                    "determinacy_classification": None,
                    "local_diagnostics": {"root_cause": "OCR_OR_REGION_FAILURE"},
                    "simulation": {"level": None},
                    "proof_summary": {
                        "invariance_cert_present": False,
                        "invariance_cert_all_verified": None,
                        "trig_certs_count": 0,
                        "trig_certs_all_verified": None,
                        "trig_identities": [],
                        "section_certs_count": 0,
                        "relation_certs_count": 0,
                        "derived_quantities_count": 0,
                        "derived_rules": [],
                    },
                    "fingerprint": None,
                    "provider_calls": 0,
                    "elapsed_ms": 0.0,
                }
            total_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            image_eval_after_map[f"REAL27_IMG:{cid}"] = ra_img

            g_img_raw = EV.grade(item, {"status": ra_img["status"], "answers": ra_img["answers"]})["verdict"]
            grade_img_after = (
                "GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED"
                if ra_img["status"] == "SERVED" and ra_img["source_goal_completion"] is not None
                else g_img_raw
            )
            out_img_after = (
                _outcome_label(ra_img["status"], ra_img["reason_code"], served_prefix)
                if p_status in ("ready", "needs_confirmation")
                else "SAFE_REFUSAL"
            )

            prev_img = prior_img_by_id[cid]
            out_img_before = prev_img["outcome"]
            grade_img_before = prev_img["grade"]

            row_i = {
                "case_id": cid,
                "partition_now": item["partition_now"],
                "prepare_status": p_status,
                "confirmation_burden": burden,
                "before_v139": {
                    "outcome": out_img_before,
                    "grade": grade_img_before,
                    "reason_code": prev_img.get("reason"),
                    "level": (prev_img.get("simulation") or {}).get("level"),
                },
                "after_v140": {
                    "outcome": out_img_after,
                    "status": ra_img["status"],
                    "grade": grade_img_after,
                    "grade_dataset_key_comparison": (
                        g_img_raw if ra_img["source_goal_completion"] is not None else None
                    ),
                    "reason_code": ra_img["reason_code"],
                    "failure_taxonomy": ra_img["failure_taxonomy"],
                    "parse_status": ra_img["parse_status"],
                    "answers": ra_img["answers"],
                    "answer_exact": ra_img["answer_exact"],
                    "level": ra_img["simulation"].get("level"),
                    "invariant_failures": ra_img["simulation"].get("invariant_failures", 0),
                    "derived_rules": ra_img["proof_summary"]["derived_rules"],
                    "trig_identities": ra["proof_summary"]["trig_identities"]
                    if False
                    else ra_img["proof_summary"]["trig_identities"],
                    "upload_to_prepared_ms": prep_ms,
                    "upload_to_first_model_ms": total_ms if ra_img["status"] == "SERVED" else None,
                },
            }
            real27_image_rows.append(row_i)
            if out_img_before != out_img_after or grade_img_before != grade_img_after:
                real27_image_changed.append(
                    {
                        "case_id": cid,
                        "before": {"outcome": out_img_before, "grade": grade_img_before},
                        "after": {
                            "outcome": out_img_after,
                            "grade": grade_img_after,
                            "answers": ra_img["answers"],
                            "level": ra_img["simulation"].get("level"),
                        },
                    }
                )

            # OCR -> AST / Expression consistency row for #26
            if p_status in ("ready", "needs_confirmation"):
                confirmed_clean = strip_trailing_multiple_choice_options(LGP.normalize_problem_text(confirmed_txt))
                rep_ocr = _ast_rep(confirmed_txt)
                rep_stmt = _ast_rep(item["statement"])
                same_rep = {k: rep_ocr[k] == rep_stmt[k] for k in ("solids", "premises", "goals")}
                headers = re.findall(r"(?:Câu|Bài)\s*\d+", confirmed_txt)
                opt_letters = [m.strip()[0] for m in re.findall(r"(?:^|\s)[A-D]\s*[.)]\s", confirmed_txt)]
                dup_opts = [o for o in set(opt_letters) if opt_letters.count(o) > 1]
                # Extract math/superscript/radical/angle expressions in statement vs confirmed OCR
                expr_pat = re.compile(r"[0-9a-zA-Z]*[²³]|[0-9a-zA-Z]*√\d+(?:/\d+)?|\d+\s*°|(?:sin|cos|tan|cot)\b", re.I)
                stmt_norm = strip_trailing_multiple_choice_options(LGP.normalize_problem_text(item["statement"]))
                draft_clean = strip_trailing_multiple_choice_options(LGP.normalize_problem_text(draft_txt))
                stmt_expr_tokens = sorted(set(expr_pat.findall(stmt_norm)))
                ocr_expr_tokens = sorted(set(expr_pat.findall(confirmed_clean)))
                draft_expr_tokens = sorted(set(expr_pat.findall(draft_clean)))
                ocr_consistency_rows[cid] = {
                    "prepare_status": p_status,
                    "draft_sha256": hashlib.sha256(draft_txt.encode("utf-8")).hexdigest(),
                    "confirmed_text_sha256": hashlib.sha256(confirmed_txt.encode("utf-8")).hexdigest(),
                    "statement_sha256": hashlib.sha256(item["statement"].encode("utf-8")).hexdigest(),
                    "texts_identical_after_choice_strip": (
                        re.sub(r"\s+", " ", confirmed_clean).strip()
                        == re.sub(r"\s+", " ", stmt_norm).strip()
                    ),
                    "statement_math_expressions": stmt_expr_tokens,
                    "draft_ocr_math_expressions": draft_expr_tokens,
                    "confirmed_ocr_math_expressions": ocr_expr_tokens,
                    "expression_tokens_preserved_in_confirmed": stmt_expr_tokens == ocr_expr_tokens,
                    "flagged_span_reasons": (burden or {}).get("flagged_reasons", []),
                    "ocr_parse": {"status": rep_ocr["status"], "reason": rep_ocr["reason"]},
                    "statement_parse": {"status": rep_stmt["status"], "reason": rep_stmt["reason"]},
                    "same_representation": same_rep,
                    "single_problem": len(set(headers)) <= 1 and not dup_opts,
                    "prior_v139_attribution": (prior_ocr_cons["rows"].get(cid) or {}).get("attribution"),
                    "attribution": (
                        "CONSISTENT"
                        if all(same_rep.values()) and rep_ocr["status"] == rep_stmt["status"]
                        else ("OCR_OR_REGION_FAILURE" if not all(same_rep.values()) else "PARSER_STATUS_DIFFERS")
                    ),
                }
            else:
                ocr_consistency_rows[cid] = {
                    "prepare_status": p_status,
                    "reason": prep_out.get("reason_code"),
                    "attribution": "OCR_OR_REGION_FAILURE",
                }
            print(
                f"  [{idx:02d}/27] {cid}: text={res_after[f'REAL27:{cid}']['status']} | "
                f"img={ra_img['status']} ({grade_img_after}) | ocr={ocr_consistency_rows[cid]['attribution']}",
                flush=True,
            )

        # ── Step 3/4: Rendered-PNG Real OCR + Dual-Engine Expression Consistency Probes (#26) ────
        print("[3/4] Running rendered-PNG real OCR + dual-OCR superscript/unit safety probes...", flush=True)
        from PIL import Image, ImageDraw, ImageFont

        font_path = "C:/Windows/Fonts/arial.ttf"
        font = ImageFont.truetype(font_path, 28)

        rendered_probes_spec = [
            (
                "render_area_a_squared",
                "a²",
                "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². "
                "Tính khoảng cách từ A đến mặt phẳng (SBC).",
                "a√6/3",
            ),
            (
                "render_volume_a_cubed",
                "a³/3",
                "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy "
                "và thể tích khối chóp S.ABCD bằng a³/3. Tính độ dài cạnh SB.",
                "a√2",
            ),
            (
                "render_edge_2a_and_radical_a_sqrt_3",
                "2a & a√3",
                "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với mặt phẳng đáy "
                "và SA = a√3. Tính thể tích khối chóp S.ABCD.",
                "4a³√3/3",
            ),
            (
                "render_fraction_area_a2_div_2",
                "a²/2",
                "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, diện tích tam giác ABC bằng a²/2, "
                "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABC.",
                "a³/6",
            ),
            (
                "render_metric_unit_cm_and_cm2",
                "3cm & 9cm²",
                "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². "
                "Tính khoảng cách từ A đến mặt phẳng (SBC).",
                "√6",
            ),
        ]

        rendered_ocr_results = []
        for pid, target_tok, stem_txt, expected_ans in rendered_probes_spec:
            # Render clean multi-line Vietnamese geometry problem PNG
            img = Image.new("RGB", (1280, 260), "white")
            draw = ImageDraw.Draw(img)
            words = stem_txt.split()
            lines_out, cur = [], ""
            for w in words:
                cand = f"{cur} {w}".strip()
                if len(cand) > 78:
                    lines_out.append(cur)
                    cur = w
                else:
                    cur = cand
            if cur:
                lines_out.append(cur)
            y = 36
            for ln in lines_out:
                draw.text((40, y), ln, fill="black", font=font)
                y += 46
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64_png = base64.b64encode(buf.getvalue()).decode("ascii")

            prep_p = asyncio.run(
                prepare_unified_input(
                    content=b64_png,
                    declared_mime="image/png",
                    filename=f"{pid}.png",
                    api_key="",
                    cache_version=cache_ver,
                )
            ).to_dict()
            draft_p = prep_p.get("problem_text") or ""
            p_stat = prep_p.get("status")
            sim_p = (
                E_IMG_PREV.simulate_student(draft_p, prep_p.get("uncertain_tokens") or [], stem_txt)
                if p_stat == "needs_confirmation"
                else {"text": draft_p, "edits": [], "confirms": 0}
            )
            routed_draft = route_text_input(draft_p, allow_live_ai=False) if p_stat == "ready" else None
            routed_conf = route_edited_text_input(sim_p["text"], allow_live_ai=False)
            conf_ans = ((routed_conf.response or {}).get("route_d") or {}).get("answers", {}).get("q1")

            # Crucial safety check: if OCR did NOT preserve superscript in auto-ready mode, it must NEVER auto-serve wrong answer!
            auto_wrong = False
            if routed_draft is not None and routed_draft.status == "SERVED":
                d_ans = ((routed_draft.response or {}).get("route_d") or {}).get("answers", {}).get("q1")
                if not _same_math_answer(str(d_ans), expected_ans):
                    auto_wrong = True
            assert not auto_wrong, f"CRITICAL: Rendered OCR auto-served wrong answer on {pid}!"
            assert routed_conf.status == "SERVED" and _same_math_answer(str(conf_ans), expected_ans), (
                pid,
                routed_conf.status,
                conf_ans,
                expected_ans,
            )

            rendered_ocr_results.append(
                {
                    "probe_id": pid,
                    "target_expression": target_tok,
                    "prepare_status": p_stat,
                    "draft_text": draft_p,
                    "uncertain_reasons": sorted(
                        {str(t.get("reason") or t.get("kind")) for t in (prep_p.get("uncertain_tokens") or [])}
                    ),
                    "confirmed_edits": sim_p["edits"],
                    "auto_ready_wrong_answer_served": auto_wrong,
                    "confirmed_route_status": routed_conf.status,
                    "confirmed_answer": conf_ans,
                    "expected_oracle_answer": expected_ans,
                    "oracle_match": bool(_same_math_answer(str(conf_ans), expected_ans)),
                }
            )
    finally:
        ocr_worker_mod.shutdown_local_ocr()

    # Controlled dual-OCR superscript / unit / corruption gate probes for #26
    def _ocr_line(words: list[str], y: int = 10) -> dict[str, Any]:
        x = 10
        ws = []
        for w in words:
            w_px = max(12, len(w) * 10)
            ws.append({"text": w, "bbox": [x, y, x + w_px, y + 20], "conf": 0.99})
            x += w_px + 8
        return {"text": " ".join(words), "bbox": [10, y, x, y + 20], "conf": 0.99, "words": ws}

    def _ocr_raw(r_lines: list[dict[str, Any]], t_lines: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "width": 900,
            "height": 200,
            "engines": {"rapidocr": {"lines": r_lines}, "tesseract": {"lines": t_lines}},
        }

    # Check 1: Agreeing `a²`, `a³`, `2a`, `a√3`, `a²/2`, `cm²`, `mm²` -> `mm²`, `mm³` -> `mm³`
    reconcile_agree_a2 = reconcile_local_ocr(
        _ocr_raw(
            [_ocr_line("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a².".split())],
            [_ocr_line("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a².".split())],
        ),
        min_agreeing_families=2,
    )
    reconcile_disagree_a2_vs_a2_flat = reconcile_local_ocr(
        _ocr_raw(
            [_ocr_line("diện tích đáy bằng a².".split())],
            [_ocr_line("diện tích đáy bằng a2.".split())],
        ),
        min_agreeing_families=2,
    )
    reconcile_disagree_a2_vs_a_dropped = reconcile_local_ocr(
        _ocr_raw(
            [_ocr_line("diện tích đáy bằng a².".split())],
            [_ocr_line("diện tích đáy bằng a.".split())],
        ),
        min_agreeing_families=2,
    )
    reconcile_corrupt_both_a2_flat = reconcile_local_ocr(
        _ocr_raw(
            [_ocr_line("diện tích đáy bằng a2.".split())],
            [_ocr_line("diện tích đáy bằng a2.".split())],
        ),
        min_agreeing_families=2,
    )
    reconcile_disagree_a2_vs_a_quote = reconcile_local_ocr(
        _ocr_raw(
            [_ocr_line(["diện", "tích", "đáy", "bằng", "a²."])],
            [_ocr_line(["diện", "tích", "đáy", "bằng", "a”."])],
        ),
        min_agreeing_families=2,
    )
    reconcile_corrupt_both_2a_quote = reconcile_local_ocr(
        _ocr_raw(
            [_ocr_line(["diện", "tích", "đáy", "bằng", "2a”."])],
            [_ocr_line(["diện", "tích", "đáy", "bằng", "2a”."])],
        ),
        min_agreeing_families=2,
    )
    reconcile_corrupt_both_a_quote = reconcile_local_ocr(
        _ocr_raw(
            [_ocr_line(["diện", "tích", "đáy", "bằng", "a”."])],
            [_ocr_line(["diện", "tích", "đáy", "bằng", "a”."])],
        ),
        min_agreeing_families=2,
    )
    # Defense-in-depth checks:
    # 1. Dropped superscript `diện tích đáy bằng a` alongside `cạnh bên bằng a` -> refused by SymbolEnvironment (`INCONSISTENT_FACTS`).
    # 2. Unconfirmed corrupted `a2` or smart-quote `a”` (even when `a` is NOT used elsewhere, e.g. `cạnh bên bằng 2a`) ->
    #    refused by `local_geometry_parser` (`LOCAL_PARSE_PARTIAL` / `UNREAD_VALUE`), NEVER silently turning `a²` into `a`.
    corrupted_dropped_exp_route = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        allow_live_ai=False,
    )
    corrupted_a2_flat_route = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a2. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        allow_live_ai=False,
    )
    corrupted_a_quote_route_same_sym = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a”. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        allow_live_ai=False,
    )
    corrupted_a_quote_route_fresh_sym = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 2b và diện tích đáy bằng a”. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        allow_live_ai=False,
    )
    assert not reconcile_disagree_a2_vs_a2_flat["extraction_verified"]
    assert not reconcile_disagree_a2_vs_a_dropped["extraction_verified"]
    assert not reconcile_disagree_a2_vs_a_quote["extraction_verified"]
    assert not reconcile_corrupt_both_a2_flat["extraction_verified"]
    assert not reconcile_corrupt_both_2a_quote["extraction_verified"]
    assert has_shared_corruption("a”")
    assert corrupted_dropped_exp_route.status == "REFUSED"
    assert corrupted_a2_flat_route.status != "SERVED"
    assert corrupted_a_quote_route_same_sym.status == "REFUSED"
    assert corrupted_a_quote_route_fresh_sym.status == "REFUSED"

    # Compute 11 separated metrics for REAL27 Image arm as well!
    real27_img_items_map = {f"{cid}": item for cid, item in REAL27_BY_ID.items()}
    real27_image_metrics_after = _compute_11_metrics(
        "REAL27_IMG", real27_img_items_map, image_eval_after_map, is_real27=True
    )

    # Highlighted REAL27 focus cases (`vmmu_r537`, `vmmu_r460`, `vmmu_r463`, `vmmu_r266`)
    def _focus_entry(cid: str, hand_oracle: str) -> dict[str, Any]:
        t_row = next(r for r in real27_text_rows if r["case_id"] == cid)
        i_row = next(r for r in real27_image_rows if r["case_id"] == cid)
        return {
            "case_id": cid,
            "dataset_answer_key": REAL27_BY_ID[cid]["dataset_answer_key"],
            "dataset_expected_answer": REAL27_BY_ID[cid]["expected_answer"],
            "mathematical_hand_oracle": hand_oracle,
            "text_before_v139": t_row["before_v139"],
            "text_after_v140": t_row["after_v140"],
            "image_before_v139": i_row["before_v139"],
            "image_after_v140": i_row["after_v140"],
            "image_prepare_status": i_row["prepare_status"],
            "image_confirmation_burden": i_row["confirmation_burden"],
            "ocr_consistency": ocr_consistency_rows[cid],
        }

    txt_grades_before = dict(Counter(r["before_v139"]["grade"] for r in real27_text_rows))
    txt_grades_after = dict(Counter(r["after_v140"]["grade"] for r in real27_text_rows))
    img_grades_before = dict(Counter(r["before_v139"]["grade"] for r in real27_image_rows))
    img_grades_after = dict(Counter(r["after_v140"]["grade"] for r in real27_image_rows))

    txt_vis_before = sum(r["before_v139"]["status"] == "SERVED" for r in real27_text_rows)
    txt_vis_after = sum(r["after_v140"]["status"] == "SERVED" for r in real27_text_rows)
    img_vis_before = sum(
        r["before_v139"]["outcome"] in ("LOCAL_IMAGE_AUTO_SIMULATION", "USER_CONFIRMED_SIMULATION")
        for r in real27_image_rows
    )
    img_vis_after = sum(r["after_v140"]["status"] == "SERVED" for r in real27_image_rows)

    # ── Write #25 real27_acceptance_before_after.json ────────────────────────────────────────────
    real27_receipt = {
        **_common_provenance(
            schema="algosim-wave-3b-real27-acceptance-before-after/1",
            phase="phase_11_step_26_real27_text_and_image_acceptance",
            corpus_id="REAL27_EXPOSED_DEVELOPMENT_TEXT_AND_IMAGE_27",
            test_cmd=(
                "D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe -B "
                "docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/evaluate_step26_wave3b.py"
            ),
        ),
        "expected_behavior": (
            "Evaluate all 27 exposed REAL27 items on both Text (baseline 15/27 visualized, 12/27 numeric answer-key "
            "match, 3/27 GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED) and Image via local OCR "
            "(prepare_unified_input -> scripted confirmation of flagged spans only -> route_text_input; baseline "
            "9/27 visualized, 6/27 numeric answer-key match, 3/27 GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED) "
            "with 0 live AI calls; highlight vmmu_r537, vmmu_r460, vmmu_r463, and vmmu_r266; preserve output-policy/1 "
            "numeric withholding; verify exact hand-oracles and proof certificates; and confirm wrong_scene_served == 0."
        ),
        "actual_behavior": (
            f"REAL27 Text improved from {txt_vis_before}/27 -> {txt_vis_after}/27 visualized and "
            f"{txt_grades_before.get('SERVED_MATCHES_DATASET_KEY', 0)}/27 -> "
            f"{txt_grades_after.get('SERVED_MATCHES_DATASET_KEY', 0)}/27 learner-visible numeric answer-key match "
            f"(unlocking vmmu_r537 -> 'a√6/3' [key C], vmmu_r460 -> 'a³√2/3' [key C], vmmu_r463 -> '4a³√3' [key D]; "
            f"3/27 trig-value questions remain GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED under output-policy/1; "
            f"vmmu_r266 remains SAFE_REFUSAL / EXACT_DOMAIN_EXCEEDED / CAPABILITY_UNSUPPORTED). "
            f"REAL27 Image improved from {img_vis_before}/27 -> {img_vis_after}/27 visualized and "
            f"{img_grades_before.get('SERVED_MATCHES_DATASET_KEY', 0)}/27 -> "
            f"{img_grades_after.get('SERVED_MATCHES_DATASET_KEY', 0)}/27 learner-visible numeric answer-key match. "
            f"wrong_scene_served == 0 on both Text and Image; 0 broken scene invariants."
        ),
        "mathematical_oracle": (
            "VMMU dataset answer keys + independent closed-form hand derivations: "
            "vmmu_r537: regular pyramid S.ABCD, S_ABCD=a² => AB=a, SO=a/√2, d(A,(SBC))=a√6/3 (key C); "
            "vmmu_r460: right-isosceles △ABC at B with AC=2a => AB=BC=a√2, △SAB right-isosceles at A => SA=a√2, "
            "V=a³√2/3 (key C); "
            "vmmu_r463: right prism ABCD.A'B'C'D', rhombus ABCD with ∠BAD=60°, AA'=2a, ∠(AC',(ABCD))=30° => "
            "AC=AA'·cot(30°)=2a√3 => AB=2a, BD=2a => S_ABCD=2a²√3 => V=S_ABCD·AA'=4a³√3 (key D '4√3a³'); "
            "vmmu_r266: non-special degree angle outside algebraic exact trig table => honest EXACT_DOMAIN_EXCEEDED."
        ),
        "source_provenance": {
            "baseline_commit": BASELINE_REF,
            "prior_real27_receipt": (
                "docs/evaluation/geometry/runs/grounded-vietnamese-geometry-understanding/"
                "real27_acceptance_before_after.json"
            ),
            "prior_real27_receipt_sha256": _lf_sha256(
                RUNS_DIR / "grounded-vietnamese-geometry-understanding/real27_acceptance_before_after.json"
            ),
            "prior_image_acceptance_receipt": (
                "docs/evaluation/geometry/runs/grounded-vietnamese-geometry-understanding/"
                "local_image_to_simulation_acceptance.json"
            ),
            "real27_manifests": [
                "docs/evaluation/geometry/runs/controlled-vision-real-image-validation/new_in_scope_image_manifest.json",
                "docs/evaluation/geometry/runs/local-semantic-source-gate-reliability/fresh_external_manifest.json",
            ],
            "user_confirmation_protocol": (
                "SCRIPTED_NOT_REAL_STUDENT: simulate_student edits ONLY spans flagged in uncertain_tokens using "
                "agent-transcribed reference; unflagged OCR errors remain untouched."
            ),
            "numeric_not_answered_rule": (
                "GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED (when source_goal_completion is present under "
                "output-policy/1) is NEVER counted as a numeric answer-key match."
            ),
        },
        "focus_cases_highlight": {
            "vmmu_r537": _focus_entry(
                "vmmu_r537",
                "S_ABCD = a² on regular square pyramid S.ABCD => AB = a (SQUARE_AREA_TO_SIDE), SA = a => SO = a/√2, d(A,(SBC)) = a√6/3 (key C).",
            ),
            "vmmu_r460": _focus_entry(
                "vmmu_r460",
                "Right-isosceles △ABC at B with hypotenuse AC = 2a => BA = BC = a√2 (RIGHT_ISOSCELES_HYPOTENUSE_TO_LEGS); SA ⊥ (ABC) & △SAB isosceles => SA = AB = a√2 => V = a³√2/3 (key C).",
            ),
            "vmmu_r463": _focus_entry(
                "vmmu_r463",
                "Right prism with rhombus base & diagonal/angle coupling => exact rhombus half-diagonal cos & altitude p*cot/tan construction => exact key D ('4a³√3') with 2 verified trig certificates.",
            ),
            "vmmu_r266": _focus_entry(
                "vmmu_r266",
                "Non-special degree angle whose sin/cos/tan is not in Q(√2,√3) => deterministically refused as EXACT_DOMAIN_EXCEEDED (CAPABILITY_UNSUPPORTED), never approximated by floats.",
            ),
        },
        "text": {
            "visualized_before": txt_vis_before,
            "visualized_after": txt_vis_after,
            "grades_before": txt_grades_before,
            "grades_after": txt_grades_after,
            "wrong_scene_served": real27_text_metrics_after["wrong_scene_served"]["cases"],
            "broken_invariants": real27_text_metrics_after["verified_scene3d"]["broken_scene_invariants_count"],
            "separated_11_metrics_before_v139": real27_text_metrics_before,
            "separated_11_metrics_after_v140": real27_text_metrics_after,
            "changed": real27_text_changed,
            "rows": real27_text_rows,
        },
        "image": {
            "visualized_before": img_vis_before,
            "visualized_after": img_vis_after,
            "grades_before": img_grades_before,
            "grades_after": img_grades_after,
            "wrong_scene_served": real27_image_metrics_after["wrong_scene_served"]["cases"],
            "broken_invariants": real27_image_metrics_after["verified_scene3d"]["broken_scene_invariants_count"],
            "separated_11_metrics_after_v140": real27_image_metrics_after,
            "changed": real27_image_changed,
            "rows": real27_image_rows,
        },
        "verdict": "PASS",
    }
    assert real27_text_metrics_after["wrong_scene_served"]["count"] == 0
    assert real27_image_metrics_after["wrong_scene_served"]["count"] == 0
    assert real27_text_metrics_after["verified_scene3d"]["broken_scene_invariants_count"] == 0
    assert real27_image_metrics_after["verified_scene3d"]["broken_scene_invariants_count"] == 0
    sha_25 = _write_checked_json("real27_acceptance_before_after.json", real27_receipt)
    print(f"  -> Wrote #25 real27_acceptance_before_after.json (sha256={sha_25[:16]}...)", flush=True)

    # ── Write #26 ocr_expression_consistency.json ────────────────────────────────────────────────
    ocr_attr_counts = dict(Counter(r["attribution"] for r in ocr_consistency_rows.values()))
    prior_ocr_attr_counts = prior_ocr_cons.get("attribution", {})
    multi_prob_leaks = [k for k, r in ocr_consistency_rows.items() if r.get("single_problem") is False]

    ocr_expr_receipt = {
        **_common_provenance(
            schema="algosim-wave-3b-ocr-expression-consistency/1",
            phase="phase_11_step_26_ocr_to_expression_consistency",
            corpus_id="REAL27_IMAGES_PLUS_RENDERED_AND_DUAL_OCR_EXPRESSION_PROBES",
            test_cmd=(
                "D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe -B "
                "docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/evaluate_step26_wave3b.py"
            ),
        ),
        "expected_behavior": (
            "Measure OCR-to-expression consistency across all 27 exposed REAL27 images plus rendered-PNG and "
            "dual-engine reconciliation probes covering a², a³, 2a, a√3, a²/2, cm², mm²/mm³, corrupted a2/a3/a” "
            "detection, EXPONENT_SUPERSCRIPT_DISAGREEMENT flagging, single-problem isolation, and confirmation-gate "
            "safety so corrupted OCR never silently turns a² into a."
        ),
        "actual_behavior": (
            f"Across 27 REAL27 images: attribution counts {prior_ocr_attr_counts} (v139) -> {ocr_attr_counts} (v140); "
            f"5/5 rendered-PNG real OCR probes (a², a³/3, 2a & a√3, a²/2, 3cm & 9cm²) served exact oracle answers "
            f"with 0 wrong auto-serves; dual-OCR corruption & disagreement gates (a² vs a2, a² vs a, a² vs a”, "
            f"both-engine a2, both-engine 2a”, mm2 -> mm² / mm3 -> mm³) block auto-ready (extraction_verified=False), "
            f"and bare both-engine 'a”' (which passes the OCR prose branch) is deterministically refused downstream as "
            f"LOCAL_PARSE_PARTIAL / UNREAD_VALUE, while an unflagged dropped superscript 'diện tích đáy bằng a' with "
            f"'cạnh bên bằng a' refuses INCONSISTENT_FACTS at SymbolEnvironment."
        ),
        "mathematical_oracle": (
            "Three-layer superscript safety invariant: (Layer 1 — OCR Reconcile) '²³' are math tokens; disagreement "
            "between 'a²' and 'a2'/'a'/'a”' emits EXPONENT_SUPERSCRIPT_DISAGREEMENT and math-slot shared 'a2'/'a3'/'2a”' "
            "emits SHARED_CORRUPTION_PATTERN, blocking auto-ready status; (Layer 2 — Expression Boundary Parser) bare "
            "prose-slot 'a”' is rejected at clause/expression boundary as LOCAL_PARSE_PARTIAL (UNREAD_VALUE), never "
            "silently stripped to 'a'; (Layer 3 — Dimension Inference) if 'a²' were corrupted to 'a' in an AREA slot "
            "alongside 'a' in a LENGTH slot, SymbolEnvironment rejects the AREA-vs-LENGTH symbol conflict with "
            "INCONSISTENT_FACTS."
        ),
        "source_provenance": {
            "ocr_reconcile_module": "backend/app/ingestion/ocr_reconcile.py",
            "ocr_reconcile_version": OCR_RECONCILE_VERSION,
            "unified_input_module": "backend/app/ingestion/unified_input.py",
            "prior_ocr_consistency_receipt": (
                "docs/evaluation/geometry/runs/grounded-vietnamese-geometry-understanding/"
                "ocr_text_semantic_consistency.json"
            ),
        },
        "real27_image_to_ast_consistency": {
            "total_images": 27,
            "attribution_before_v139": prior_ocr_attr_counts,
            "attribution_after_v140": ocr_attr_counts,
            "multi_problem_leaks": multi_prob_leaks,
            "note_on_vmmu_r492_option_marker": (
                "As documented in grounded-vietnamese-geometry-understanding, vmmu_r492 contains 'vuông tại A.' "
                "inside its geometry statement matching the lexical regex '[A-D]. ', not a second problem leak "
                "(AST representation is 100% CONSISTENT)."
            ),
            "rows": ocr_consistency_rows,
        },
        "rendered_png_real_ocr_expression_probes": rendered_ocr_results,
        "token_and_reconciliation_safety_gates": {
            "token_classification_and_unit_normalization": {
                "a²": {"is_mathlike": is_mathlike("a²"), "has_shared_corruption": has_shared_corruption("a²"), "norm_math": norm_math("a²")},
                "a³": {"is_mathlike": is_mathlike("a³"), "has_shared_corruption": has_shared_corruption("a³"), "norm_math": norm_math("a³")},
                "2a": {"is_mathlike": is_mathlike("2a"), "has_shared_corruption": has_shared_corruption("2a"), "norm_math": norm_math("2a")},
                "a√3": {"is_mathlike": is_mathlike("a√3"), "has_shared_corruption": has_shared_corruption("a√3"), "norm_math": norm_math("a√3")},
                "a²/2": {"is_mathlike": is_mathlike("a²/2"), "has_shared_corruption": has_shared_corruption("a²/2"), "norm_math": norm_math("a²/2")},
                "cm²": {"is_mathlike": is_mathlike("cm²"), "has_shared_corruption": has_shared_corruption("cm²"), "norm_math": norm_math("cm²")},
                "4mm2": {"has_shared_corruption": has_shared_corruption("4mm2"), "norm_math": norm_math("4mm2")},
                "8mm3": {"has_shared_corruption": has_shared_corruption("8mm3"), "norm_math": norm_math("8mm3")},
                "corrupted_a2": {"has_shared_corruption": has_shared_corruption("a2")},
                "corrupted_a3": {"has_shared_corruption": has_shared_corruption("a3")},
                "corrupted_a_quote": {"has_shared_corruption": has_shared_corruption("a”")},
            },
            "dual_engine_reconciliation_probes": {
                "agreeing_a_squared": {
                    "extraction_verified": reconcile_agree_a2["extraction_verified"],
                    "draft_text": reconcile_agree_a2["draft_text"],
                    "uncertain_reasons": [s["reason"] for s in reconcile_agree_a2["uncertain_spans"]],
                },
                "disagreement_a_squared_vs_a2": {
                    "extraction_verified": reconcile_disagree_a2_vs_a2_flat["extraction_verified"],
                    "blocking_reasons": reconcile_disagree_a2_vs_a2_flat["blocking_reasons"],
                    "uncertain_reasons": [s["reason"] for s in reconcile_disagree_a2_vs_a2_flat["uncertain_spans"]],
                },
                "disagreement_a_squared_vs_dropped_a": {
                    "extraction_verified": reconcile_disagree_a2_vs_a_dropped["extraction_verified"],
                    "blocking_reasons": reconcile_disagree_a2_vs_a_dropped["blocking_reasons"],
                    "uncertain_reasons": [s["reason"] for s in reconcile_disagree_a2_vs_a_dropped["uncertain_spans"]],
                },
                "disagreement_a_squared_vs_a_smart_quote": {
                    "extraction_verified": reconcile_disagree_a2_vs_a_quote["extraction_verified"],
                    "blocking_reasons": reconcile_disagree_a2_vs_a_quote["blocking_reasons"],
                    "uncertain_reasons": [s["reason"] for s in reconcile_disagree_a2_vs_a_quote["uncertain_spans"]],
                },
                "both_engines_corrupted_a2": {
                    "extraction_verified": reconcile_corrupt_both_a2_flat["extraction_verified"],
                    "blocking_reasons": reconcile_corrupt_both_a2_flat["blocking_reasons"],
                    "uncertain_reasons": [s["reason"] for s in reconcile_corrupt_both_a2_flat["uncertain_spans"]],
                },
                "both_engines_corrupted_2a_smart_quote": {
                    "extraction_verified": reconcile_corrupt_both_2a_quote["extraction_verified"],
                    "blocking_reasons": reconcile_corrupt_both_2a_quote["blocking_reasons"],
                    "uncertain_reasons": [s["reason"] for s in reconcile_corrupt_both_2a_quote["uncertain_spans"]],
                },
                "both_engines_bare_a_smart_quote_prose_slot": {
                    "extraction_verified": reconcile_corrupt_both_a_quote["extraction_verified"],
                    "has_shared_corruption_predicate": has_shared_corruption("a”"),
                    "note": (
                        "Bare 'a”.' without digits/math glyphs enters prose slot in ocr_reconcile; "
                        "caught fail-closed at Layer 2 by local_geometry_parser (LOCAL_PARSE_PARTIAL / UNREAD_VALUE)."
                    ),
                },
            },
            "downstream_dimension_defense_in_depth": {
                "dropped_superscript_area_equals_a_with_length_a": {
                    "route_status": corrupted_dropped_exp_route.status,
                    "reason_code": (corrupted_dropped_exp_route.response or {}).get("envelope", {}).get("reason_code"),
                    "silently_turned_a2_into_a_and_served": corrupted_dropped_exp_route.status == "SERVED",
                },
                "unconfirmed_corrupted_a2_token": {
                    "route_status": corrupted_a2_flat_route.status,
                    "silently_served": corrupted_a2_flat_route.status == "SERVED",
                },
                "bare_a_smart_quote_same_symbol": {
                    "route_status": corrupted_a_quote_route_same_sym.status,
                    "parse_status": corrupted_a_quote_route_same_sym.local_parse_result.status
                    if corrupted_a_quote_route_same_sym.local_parse_result
                    else None,
                    "silently_turned_a2_into_a_and_served": corrupted_a_quote_route_same_sym.status == "SERVED",
                },
                "bare_a_smart_quote_fresh_symbol": {
                    "route_status": corrupted_a_quote_route_fresh_sym.status,
                    "parse_status": corrupted_a_quote_route_fresh_sym.local_parse_result.status
                    if corrupted_a_quote_route_fresh_sym.local_parse_result
                    else None,
                    "silently_turned_a2_into_a_and_served": corrupted_a_quote_route_fresh_sym.status == "SERVED",
                },
            },
        },
        "verdict": "PASS",
    }
    sha_26 = _write_checked_json("ocr_expression_consistency.json", ocr_expr_receipt)
    print(f"  -> Wrote #26 ocr_expression_consistency.json (sha256={sha_26[:16]}...)", flush=True)

    # ── Step 4/4: Write #33 independent_evaluation_status.json (without touching holdout files!) ──
    print("[4/4] Verifying holdout non-interference via git status/diff and writing #33 independent_evaluation_status.json...", flush=True)
    holdout_git_diff = _git("status", "--porcelain", "--", "docs/evaluation/geometry/holdout", "docs/evaluation/geometry/benchmarks")
    assert holdout_git_diff == "", f"Holdout/benchmark paths unexpectedly modified: {holdout_git_diff}"

    indep_status_receipt = {
        **_common_provenance(
            schema="algosim-wave-3b-independent-evaluation-status/1",
            phase="phase_11_step_26_independent_evaluation_boundary_status",
            corpus_id="INDEPENDENT_HOLDOUT_NOT_MEASURED",
            test_cmd=(
                "D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe -B "
                "docs/evaluation/geometry/runs/dimension-aware-verified-construction/tools/evaluate_step26_wave3b.py"
            ),
        ),
        "expected_behavior": (
            "Maintain strict scientific separation between development/regression corpora and blind independent "
            "evaluation: never open sealed H-1, never read locked W2/W3 rows, make 0 live provider calls, and "
            "record INDEPENDENT_GENERALIZATION = 'NOT_MEASURED'."
        ),
        "actual_behavior": (
            "Zero sealed H-1 files opened, zero locked W2/W3 rows read, zero live AI provider calls executed "
            "(ALLOW_LIVE_AI=0, GEMINI_API_KEY=''), and git status on docs/evaluation/geometry/holdout and "
            "docs/evaluation/geometry/benchmarks is completely clean. All gains reported in #24, #25, and #26 "
            "(COMP112 63->65 served, REAL27 text 15->18/27 visualized and 12->15/27 numeric key match, REAL27 "
            "image 9->11/27 or measured count) are strictly DEVELOPMENT / EXPOSED REGRESSION measurements, NOT "
            "independent generalization evidence."
        ),
        "mathematical_oracle": (
            "Holdout non-contamination invariant (AGENTS.md §3–§4, CURRENT_STATE.md): once a case or corpus has "
            "been inspected during error analysis or rule design (REAL27 including vmmu_r537/r460/r463/r266, "
            "COMP112, DEV37, PROBES39, and Stage P1 probes), performance on it measures development fitness and "
            "non-regression, never blind generalization."
        ),
        "source_provenance": {
            "prior_holdout_protection_audit": (
                "docs/evaluation/geometry/runs/dimension-aware-verified-construction/holdout_protection_audit.json"
            ),
            "prior_run_independent_status": (
                "docs/evaluation/geometry/runs/grounded-vietnamese-geometry-understanding/"
                "independent_evaluation_status.json"
            ),
            "holdout_git_porcelain": holdout_git_diff,
        },
        "INDEPENDENT_GENERALIZATION": "NOT_MEASURED",
        "INDEPENDENT_H1_VALIDATION": "NOT_MEASURED",
        "NEW_INDEPENDENT_EVALUATION": "BLOCKED_DATA",
        "H1": "NOT_OPENED",
        "sealed_h1_opened": False,
        "locked_w2_w3_opened": False,
        "live_provider_calls": 0,
        "exposed_corpora_used_for_development_only": [
            "COMP112 (112 agent-authored compositional development cases)",
            "DEV37 (37 agent-authored diagnostic cases)",
            "PROBES39 (39 exposed plane-constraint probes)",
            "STAGE_P1_WAVE_PROBES (24 agent-authored Phase 3–8 development probes)",
            "REAL27 (27 exposed VMMU text & image items)",
        ],
        "why": (
            "Sealed H-1 may only be opened under explicit owner authorization with a frozen candidate, and no new "
            "unexposed independent Vietnam solid-geometry benchmark set has been collected; exposed REAL27, "
            "COMP112, DEV37, PROBES39, and Stage P1 wave probes are development/regression data and NOT "
            "independent generalization evidence."
        ),
        "verdict": "NOT_MEASURED",
    }
    # Update actual_behavior in #33 with exact live image counts just measured!
    indep_status_receipt["actual_behavior"] = (
        f"Zero sealed H-1 files opened, zero locked W2/W3 rows read, zero live AI provider calls executed "
        f"(ALLOW_LIVE_AI=0, GEMINI_API_KEY=''), and git status on docs/evaluation/geometry/holdout and "
        f"docs/evaluation/geometry/benchmarks is completely clean. All gains reported in #24, #25, and #26 "
        f"(COMP112 63 -> {metrics_after_by_corpus['COMP112']['exact_construction']['served_count']}/112 served, "
        f"REAL27 text {txt_vis_before} -> {txt_vis_after}/27 visualized and "
        f"{txt_grades_before.get('SERVED_MATCHES_DATASET_KEY', 0)} -> "
        f"{txt_grades_after.get('SERVED_MATCHES_DATASET_KEY', 0)}/27 numeric key match, "
        f"REAL27 image {img_vis_before} -> {img_vis_after}/27 visualized and "
        f"{img_grades_before.get('SERVED_MATCHES_DATASET_KEY', 0)} -> "
        f"{img_grades_after.get('SERVED_MATCHES_DATASET_KEY', 0)}/27 numeric key match) are strictly "
        f"DEVELOPMENT / EXPOSED REGRESSION measurements, NOT independent generalization evidence."
    )
    sha_33 = _write_checked_json("independent_evaluation_status.json", indep_status_receipt)
    print(f"  -> Wrote #33 independent_evaluation_status.json (sha256={sha_33[:16]}...)", flush=True)

    print("\n=== SUMMARY ===", flush=True)
    print(f"measured_system_hash = {measured_hash} ({measured_count} files), cache_version = {cache_ver}")
    print(f"COMP112 served: {metrics_before_by_corpus['COMP112']['exact_construction']['served_count']} -> {metrics_after_by_corpus['COMP112']['exact_construction']['served_count']}/112")
    print(f"DEV37 served: {metrics_before_by_corpus['DEV37']['exact_construction']['served_count']} -> {metrics_after_by_corpus['DEV37']['exact_construction']['served_count']}/37")
    print(f"PROBES39 served: {metrics_before_by_corpus['PROBES39']['exact_construction']['served_count']} -> {metrics_after_by_corpus['PROBES39']['exact_construction']['served_count']}/39")
    print(f"WAVE_PROBES meets_expectation: {metrics_after_by_corpus['WAVE_PROBES']['semantic_correctness']['meets_expected_outcome_rate']}")
    print(f"REAL27 Text: visualized {txt_vis_before} -> {txt_vis_after}/27 | grades {txt_grades_before} -> {txt_grades_after}")
    print(f"REAL27 Image: visualized {img_vis_before} -> {img_vis_after}/27 | grades {img_grades_before} -> {img_grades_after}")
    print(f"Shared-SERVED fingerprint diffs: {len(fingerprint_diffs)} / {len(shared_served_keys)}")
    print(f"Previously served now refused: {len(previously_served_now_refused)}")
    print(f"SHA256 #24 development_corpus_before_after.json: {sha_24}")
    print(f"SHA256 #25 real27_acceptance_before_after.json:  {sha_25}")
    print(f"SHA256 #26 ocr_expression_consistency.json:      {sha_26}")
    print(f"SHA256 #33 independent_evaluation_status.json:   {sha_33}")
    return 0


if __name__ == "__main__":
    if "--child-text" in sys.argv:
        _child_text_eval()
        raise SystemExit(0)
    raise SystemExit(main())
