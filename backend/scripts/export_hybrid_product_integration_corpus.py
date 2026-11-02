# -*- coding: utf-8 -*-
"""Build the staging replay corpus and run real `/api/analyze` verification across all 16 scope/refusal classes.

All inputs are existing authored development/pilot corpora (`hybrid-contract-v2`, `k1`, `r1`, `s2`, `curved_probe`,
`curved_section_probe`, `composite_relations_probe`). Every record is explicitly marked as authored/simulated replay
(`AUTHORED_DEVELOPMENT_REPLAY_NOT_PROVIDER_NOT_HOLDOUT`); 0 live provider calls are made.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import sys
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = ROOT / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement"
TOOLS_DIR = RUN_DIR / "tools"
sys.path.insert(0, str(ROOT / "backend"))

MACHINE_ID_RE = re.compile(r"\b(?:kq_|td_|mp_td_)[A-Za-z0-9_]+|section:td_")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _canon_answer(sym: str) -> str:
    s = str(sym).strip()
    if "=" in s:
        s = s.rsplit("=", 1)[-1].strip()
    return s.replace(" ", "")


def collect_sources() -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], dict[str, dict[str, Any]]]:
    """Return `(text_to_payload, conflicting_texts_by_sha, case_by_id)`."""
    from scripts.export_hybrid_v2_local_corpus import build as build_local_v2

    by_text: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    case_by_id: dict[str, dict[str, Any]] = {}

    def register(cid: str, text: str, payload: dict[str, Any], meta: dict[str, Any]) -> None:
        by_text.setdefault(text, []).append((cid, payload))
        case_by_id[cid] = {"id": cid, "problem_text": text, "payload": payload, **meta}

    # 1. Stage 2 `hybrid-contract-v2` authored lock
    ev = runpy.run_path(str(ROOT / "docs/evaluation/geometry/runs/hybrid-contract-v2/evaluate_grammar_set.py"))
    base_non_conflicting = build_local_v2()["outputs"]
    for c in ev["load_lock"]():
        text = c["payload"]["problem_text"]
        if text in base_non_conflicting:
            register(c["id"], text, c["payload"], {"source": "hybrid-contract-v2", "expected_raw": c.get("expected")})

    # 2. K-1, R-1, S-2 authored pilot corpora
    for fname in ("k1-live-pilot-corpus.json", "r1-live-pilot-corpus.json", "s2-student-language-pilot-corpus.json"):
        data = json.loads((RUN_DIR / fname).read_text(encoding="utf-8"))
        for c in data["cases"]:
            register(c["id"], c["problem_text"], c["gold_extraction"], {"source": fname, "expected": c["expected"]})

    # 3. Curved solids & curved sections (`curved_probe.py`, `curved_section_probe.py`)
    cp = _load_module("curved_probe", TOOLS_DIR / "curved_probe.py")
    for cid, fig, goal_type, question, expected in cp.CASES:
        pl = cp.payload(fig, goal_type, question)
        register(cid, pl["problem_text"], pl, {"source": "tools/curved_probe.py", "oracle": expected})
    for cid, fig, goal_type, question, mut in cp.NEGATIVES:
        if cid in ("n.bad_slant", "n.missing_height"):
            pl = cp.payload(fig, goal_type, question, mut)
            register(cid, pl["problem_text"], pl, {"source": "tools/curved_probe.py", "oracle": "REFUSE"})

    csp = _load_module("curved_section_probe", TOOLS_DIR / "curved_section_probe.py")
    for cid, pl, expected in csp.CASES:
        register(cid, pl["problem_text"], pl, {"source": "tools/curved_section_probe.py", "oracle": expected})

    # 4. Multi-object & composite sphere/polyhedron/curved relations (`composite_relations_probe.py`)
    crp = _load_module("composite_relations_probe", TOOLS_DIR / "composite_relations_probe.py")
    for row in crp.POSITIVE_CASES:
        cid, pl, expected = row[0], row[1], row[2]
        register(cid, pl["problem_text"], pl, {"source": "tools/composite_relations_probe.py", "oracle_map": expected})
    for row in crp.NEGATIVE_CASES:
        cid, pl = row[0], row[1]
        if cid.startswith("cr.neg."):
            register(cid, pl["problem_text"], pl, {"source": "tools/composite_relations_probe.py", "oracle": "REFUSE"})

    outputs: dict[str, dict[str, Any]] = {}
    conflicts: dict[str, list[str]] = {}
    for text, entries in by_text.items():
        distinct = {json.dumps(pl, sort_keys=True, ensure_ascii=False) for _, pl in entries}
        if len(distinct) == 1:
            outputs[text] = entries[0][1]
        else:
            conflicts[hashlib.sha256(text.encode("utf-8")).hexdigest()] = sorted({cid for cid, _ in entries})
    return outputs, conflicts, case_by_id


# All 16 required scope and refusal classes (§VI) mapped to non-conflicting cases in the staging corpus.
SIXTEEN_CLASSES: list[tuple[str, str, str, list[tuple[str, dict[str, Any]]]]] = [
    ("01_polyhedra", "Polyhedra (cube, asymmetric tetrahedron)", "SERVED", [
        ("cr.cube_2.dual_spheres.multi_goal", {"oracles": ["12π", "4π", "8"]}),
        ("cr.tetra_asym_132.inscribed.named_center", {"oracles": ["1/3", "√3/3"]}),
    ]),
    ("02_pyramids", "Pyramids", "SERVED", [
        ("S2-B-I07_ve_va_tinh", {"oracles": ["8/3"]}),
        ("S2-F-S02_vuong_goc_day", {"oracles": ["8/3"]}),
    ]),
    ("03_prisms", "Prisms", "SERVED", [
        ("S2-B-A03_control_with_dimensions", {"oracles": ["√3"]}),
        ("cr.prism_345_h2.inscribed.area", {"oracles": ["4π"]}),
    ]),
    ("04_distance_and_angle", "Distance and angle", "SERVED", [
        ("S2-F-F05_kc_mp_shorthand", {"oracles": ["√2"]}),
        ("S2-F-F06_dt_mp_shorthand", {"oracles": ["2/3"]}),
        ("R1-D01", {"oracles": ["√41/2"]}),
    ]),
    ("05_area_and_volume", "Area and volume", "SERVED", [
        ("R1-A05", {"oracles": ["√6"]}),
        ("CORPUS-DEV10-prism-area", {"exact_oracles": ["√3/4"], "symbolic_oracles": ["a²√3/4"]}),
    ]),
    ("06_plane_sections", "Plane sections (Category A declared/edge-cut & Category B engine-derived)", "SERVED", [
        ("PARTIAL-1of2-construct", {"oracles": [], "section_category": "CATEGORY_A"}),
        ("R1-C02", {"oracles": ["3/2"], "section_category": "ENGINE_DERIVED_SECTION"}),
    ]),
    ("07_curved_solids", "Curved solids (sphere, cylinder, cone, curved plane section)", "SERVED", [
        ("sph.V", {"oracles": ["36π"]}),
        ("cyl.Stp", {"oracles": ["48π"]}),
        ("coneR.Sxq", {"oracles": ["4π√2"]}),
        ("cone.par.S", {"oracles": ["81π/16"]}),
    ]),
    ("08_multi_object_geometry", "Multi-object geometry (shared faces, dual spheres, frustum residual volume)", "SERVED", [
        ("cr.shared_base_pyramids_plus_inscribed_sphere", {"oracles": ["72", "9π"]}),
        ("cr.cube_section_plus_inscribed_sphere", {"oracles": ["4", "4π/3"]}),
        ("cone.residual", {"oracles": ["21π/2"]}),
    ]),
    ("09_described_points", "Described points (@id midpoint, ratio, projection, centroid)", "SERVED", [
        ("R1-A01", {"oracles": ["√2"]}),
        ("R1-A02", {"oracles": ["2√6/3"]}),
    ]),
    ("10_constrained_planes", "Constrained planes (MAT_RANG_BUOC)", "SERVED", [
        ("K-A01", {"oracles": ["3√2/2"], "section_category": "ENGINE_DERIVED_SECTION"}),
        ("K-A03", {"oracles": ["√61"], "section_category": "ENGINE_DERIVED_SECTION"}),
    ]),
    ("11_orthocenter_and_circumcenter", "Orthocenter and circumcenter", "SERVED", [
        ("R1-B01", {"oracles": ["2304/625"], "section_category": "ENGINE_DERIVED_SECTION"}),
        ("K-C01", {"oracles": ["1"]}),
        ("K-C02", {"oracles": ["1/4"]}),
    ]),
    ("12_registered_multi_function_composition", "Registered multi-function composition", "SERVED", [
        ("S2-B-P07_shared_intermediate_two_goals", {"oracles": ["√3", "1"]}),
        ("S2-B-P09_student_chain", {"oracles": ["√3"]}),
        ("K-C03", {"oracles": ["√66/4"]}),
    ]),
    ("13_contradictory_data", "Contradictory geometric data (fail-closed refusal)", "REFUSED", [
        ("S2-D-D03_contradictory_length", {"failure_category": "geometry_generation_failed"}),
        ("K-D01", {"failure_category": "geometry_generation_failed"}),
        ("n.bad_slant", {"failure_category": "geometry_generation_failed"}),
    ]),
    ("14_missing_data", "Missing geometric data (fail-closed refusal)", "REFUSED", [
        ("K-B01", {"failure_category": "insufficient_specification"}),
        ("n.missing_height", {"failure_category": "insufficient_specification"}),
    ]),
    ("15_ambiguous_expressions", "Ambiguous expressions (route-d-clarification/1 user-facing question)", "CLARIFY", [
        ("S2-C-A01_goc_chieu", {"clarification_question_required": True}),
        ("K-E01", {"clarification_question_required": True}),
        ("R1-E01", {"clarification_question_required": True}),
    ]),
    ("16_unsupported_goals", "Unsupported goals and outside-exact-domain requests (fail-closed refusal)", "REFUSED", [
        ("S2-E-E02_truncated_pyramid", {"failure_category": "capability_gap"}),
        ("R1-F01", {"failure_category": "capability_gap"}),
        ("cylR.Stp", {"failure_category": "capability_gap"}),
    ]),
]


def build_corpus_json() -> dict[str, Any]:
    from app.ai.hybrid_offline import LOCAL_REPLAY_SCHEMA

    outputs, conflicts, _ = collect_sources()
    return {
        "schema": LOCAL_REPLAY_SCHEMA,
        "classification": "AUTHORED_DEVELOPMENT_REPLAY_NOT_PROVIDER_NOT_HOLDOUT",
        "simulated": True,
        "live_provider_calls": 0,
        "sources": [
            "docs/evaluation/geometry/runs/hybrid-contract-v2 (load_lock)",
            "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/k1-live-pilot-corpus.json",
            "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/r1-live-pilot-corpus.json",
            "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/s2-student-language-pilot-corpus.json",
            "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/curved_probe.py",
            "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/curved_section_probe.py",
            "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/composite_relations_probe.py",
        ],
        "excluded_texts_with_several_payloads": conflicts,
        "outputs": outputs,
    }


def verify_16_classes(corpus_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run all 16 scope/refusal classes through real FastAPI `POST /api/analyze` (`HYBRID_ROUTE_MODE=staging-replay`)."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.simulation.geometry.radical import parse_exact

    _, _, case_by_id = collect_sources()
    env = {
        "HYBRID_ROUTE_MODE": "staging-replay",
        "HYBRID_REPLAY_CORPUS": str(corpus_path),
        "ALLOW_LIVE_AI": "0",
    }
    category_summaries: list[dict[str, Any]] = []
    frontend_fixtures: list[dict[str, Any]] = []
    seen_fixture_ids: set[str] = set()

    with patch.dict(os.environ, env, clear=False):
        client = TestClient(app)
        for cat_id, cat_label, expected_mode, specs in SIXTEEN_CLASSES:
            rows: list[dict[str, Any]] = []
            for cid, rules in specs:
                assert cid in case_by_id, f"Missing case {cid}"
                text = case_by_id[cid]["problem_text"]
                res = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
                assert res.status_code == 200, f"{cid}: HTTP {res.status_code} {res.text}"
                body = res.json()
                assert body["schema_version"] == "hybrid-route-d-simulation/4", cid
                envelope = body["envelope"]
                route_d = body["route_d"]
                raw_sha = hashlib.sha256(
                    json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()

                if expected_mode == "SERVED":
                    assert envelope["status"] == "ok", f"{cid}: {envelope}"
                    assert route_d["status"] == "SERVED", f"{cid}: {route_d}"
                    assert route_d["source_verification"] == {"authority": "registry.kiem_nguon"}, cid
                    scene = envelope["scene3d"]
                    obj_ids = {o["id"] for o in scene["objects"]}
                    deps_closed = all(
                        all(d in obj_ids for d in (o.get("depends") or ())) for o in scene["objects"]
                    ) and all(
                        all(d in obj_ids for d in (st.get("visible_ids") or ()))
                        for st in (scene.get("formation") or {}).get("steps") or ()
                    )
                    assert deps_closed, f"{cid}: dangling scene3d dependency"

                    learner_texts = [
                        str(envelope.get("title") or ""),
                        str(envelope.get("description") or ""),
                        *(str(e.get("learner_text") or "") for e in scene["events"]),
                        *(str(s.get("learner_text") or "") for s in (scene.get("formation") or {}).get("steps") or ()),
                    ]
                    leaked = [t for t in learner_texts if MACHINE_ID_RE.search(t)]
                    assert not leaked, f"{cid}: leaked machine ID in {leaked}"

                    answers = route_d.get("answers") or {}
                    exact_map = route_d.get("answer_exact") or {}
                    assert set(answers) == set(exact_map), cid
                    got_vals = [_canon_answer(v) for v in answers.values()]
                    want_vals = rules.get("oracles")
                    if want_vals is not None:
                        got_parsed = sorted((str(parse_exact(x)) for x in got_vals))
                        want_parsed = sorted((str(parse_exact(x)) for x in want_vals))
                        assert got_parsed == want_parsed, f"{cid}: got {got_vals} ({got_parsed}) != want {want_vals} ({want_parsed})"
                        recorded_oracles: Any = want_vals
                    else:
                        exact_want = rules["exact_oracles"]
                        sym_want = rules["symbolic_oracles"]
                        got_exact = sorted((str(parse_exact(v["coef"])) for v in exact_map.values()))
                        want_exact = sorted((str(parse_exact(x)) for x in exact_want))
                        assert got_exact == want_exact, f"{cid}: exact {got_exact} != {want_exact}"
                        assert sorted(got_vals) == sorted(sym_want), f"{cid}: symbolic {got_vals} != {sym_want}"
                        recorded_oracles = {"symbolic": sym_want, "exact_coef": exact_want}

                    sec_cat = rules.get("section_category")
                    if sec_cat == "ENGINE_DERIVED_SECTION":
                        assert any(
                            s.get("certificate_category") == "ENGINE_DERIVED_SECTION"
                            and s.get("closure_certificate", {}).get("verified") is True
                            for s in (route_d.get("sections") or ())
                        ), f"{cid}: missing verified ENGINE_DERIVED_SECTION certificate"
                    elif sec_cat == "CATEGORY_A":
                        assert any(
                            "certificate_category" not in s
                            and s.get("closure_certificate", {}).get("verified") is True
                            for s in (route_d.get("sections") or ())
                        ), f"{cid}: missing verified Category A section certificate"

                    for rcert in route_d.get("relation_certificates") or ():
                        for layer in (
                            "SOURCE_GROUNDING_PROOF",
                            "GEOMETRIC_RELATION_PROOF",
                            "KERNEL_EXECUTION_PROOF",
                            "RESULT_CERTIFICATE",
                        ):
                            assert rcert[layer]["verified"] is True, f"{cid}: unverified {layer}"

                    rows.append({
                        "case_id": cid,
                        "problem_text": text,
                        "http_status": 200,
                        "route_d_status": "SERVED",
                        "envelope_status": "ok",
                        "answers": answers,
                        "oracles": recorded_oracles,
                        "oracle_verified": True,
                        "source_gate_authority": route_d["source_verification"]["authority"],
                        "section_certificates": len(route_d.get("sections") or ()),
                        "relation_certificates": len(route_d.get("relation_certificates") or ()),
                        "scene3d_objects": len(scene["objects"]),
                        "scene3d_events": len(scene["events"]),
                        "dependencies_closed": deps_closed,
                        "zero_machine_id_leak": True,
                        "response_sha256": raw_sha,
                    })
                else:
                    assert envelope["status"] == "unsupported", f"{cid}: expected refusal, got {envelope}"
                    assert route_d["status"] == "REFUSED", f"{cid}: {route_d}"
                    assert "scene3d" not in envelope, f"{cid}: refusal must not carry scene3d"
                    assert not (route_d.get("answers") or {}), f"{cid}: refusal must not carry answers"
                    clar = (route_d.get("refusal") or {}).get("clarification")
                    if expected_mode == "CLARIFY":
                        assert isinstance(clar, dict), f"{cid}: missing clarification record"
                        assert clar.get("schema_version") == "route-d-clarification/1", cid
                        assert isinstance(clar.get("question"), str) and clar["question"].strip(), cid
                        assert clar.get("quote") in text, cid
                    if "failure_category" in rules:
                        assert envelope.get("failure_category") == rules["failure_category"], (
                            f"{cid}: got {envelope.get('failure_category')} != {rules['failure_category']}"
                        )
                    rows.append({
                        "case_id": cid,
                        "problem_text": text,
                        "http_status": 200,
                        "route_d_status": "REFUSED",
                        "envelope_status": "unsupported",
                        "reason_code": envelope.get("reason_code"),
                        "failure_category": envelope.get("failure_category"),
                        "clarification_question": clar.get("question") if isinstance(clar, dict) else None,
                        "zero_scene_on_refusal": True,
                        "response_sha256": raw_sha,
                    })

                # Keep first case of each category (plus all Category B & clarification fixtures) for Vitest consumer checks.
                if cid not in seen_fixture_ids and (
                    cid == specs[0][0] or cid in {"K-A01", "R1-B01", "S2-C-A01_goc_chieu", "S2-C-D06_unnamed_prism", "S2-E-E02_truncated_pyramid"}
                ):
                    seen_fixture_ids.add(cid)
                    frontend_fixtures.append({
                        "id": cid,
                        "category": cat_id,
                        "source_corpus": case_by_id[cid]["source"],
                        "problem_text": text,
                        "response": body,
                    })

            category_summaries.append({
                "category_id": cat_id,
                "label": cat_label,
                "expected_disposition": expected_mode,
                "cases_verified": len(rows),
                "all_passed": True,
                "cases": rows,
            })

    # Include `S2-C-D06_unnamed_prism` so existing Vitest named test cases stay present in the same single fixture bundle.
    if "S2-C-D06_unnamed_prism" not in seen_fixture_ids:
        with patch.dict(os.environ, env, clear=False):
            client = TestClient(app)
            c = case_by_id["S2-C-D06_unnamed_prism"]
            res = client.post("/api/analyze", json={"input": {"type": "text", "content": c["problem_text"]}})
            assert res.status_code == 200
            frontend_fixtures.append({
                "id": "S2-C-D06_unnamed_prism",
                "category": "15_ambiguous_expressions",
                "source_corpus": c["source"],
                "problem_text": c["problem_text"],
                "response": res.json(),
            })

    receipt = {
        "schema": "hybrid-product-integration-16-classes-verification/1",
        "classification": "PRODUCT_RUNTIME_REPLAY_VERIFICATION_NOT_LIVE_PROVIDER",
        "route_mode": "staging-replay",
        "live_provider_calls": 0,
        "categories_total": len(category_summaries),
        "categories_passed": sum(1 for c in category_summaries if c["all_passed"]),
        "cases_total": sum(c["cases_verified"] for c in category_summaries),
        "categories": category_summaries,
    }
    return receipt, frontend_fixtures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--corpus-out",
        default=str(RUN_DIR / "product-integration-staging-corpus.json"),
    )
    ap.add_argument(
        "--verification-out",
        default=str(RUN_DIR / "product-integration-16-classes-verification.json"),
    )
    ap.add_argument(
        "--frontend-fixtures-out",
        default=str(RUN_DIR / "product-integration-frontend-fixtures.json"),
    )
    args = ap.parse_args()

    corpus = build_corpus_json()
    corpus_path = Path(args.corpus_out)
    corpus_text = json.dumps(corpus, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    corpus_path.write_text(corpus_text, encoding="utf-8")

    receipt, fe_fixtures = verify_16_classes(corpus_path)
    receipt["corpus_sha256"] = hashlib.sha256(corpus_text.encode("utf-8")).hexdigest()
    receipt["corpus_texts"] = len(corpus["outputs"])

    ver_path = Path(args.verification_out)
    ver_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fe_path = Path(args.frontend_fixtures_out)
    fe_path.write_text(
        json.dumps(
            {
                "schema": "hybrid-product-integration-frontend-fixtures/1",
                "classification": "AUTHORED_REPLAY_ENGINE_OUTPUT_NOT_LIVE_PROVIDER",
                "fixtures": fe_fixtures,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "corpus_texts": len(corpus["outputs"]),
                "categories_passed": f"{receipt['categories_passed']}/{receipt['categories_total']}",
                "cases_verified": receipt["cases_total"],
                "frontend_fixtures": len(fe_fixtures),
                "corpus_sha256": receipt["corpus_sha256"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
