# -*- coding: utf-8 -*-
"""Post-merge case identity and evidence adjudication verifier for HYBRID_V2_W2_M5_POSTMERGE_CASE_IDENTITY_ADJUDICATION."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ["ALLOW_LIVE_AI"] = "0"
sys.dont_write_bytecode = True

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))

PREMERGE_MAIN_SHA = "eb661971847c034500862299c5091f1f3d2a2998"
PRODUCT_SHA = "73ca8d92e74059680ce53b99692af396df37a2f8"
ARTIFACTS_SHA = "7aa538aecf2d31c40887b7c6ee52f7e8219ea0eb"
T3_CANDIDATE_SHA = "b61f16995dfbe0110a639a2127d0fb5a9c3afde0"
POSTMERGE_MAIN_SHA = "2c42f6cf23ddde89cc752e0ee6dfec6e4e230d3b"
HIST_W2_SHA = "ecdc26b012c8ce80d53524a98dc75cdcb020079d"
FREEZE_TREE_HASH = "1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d"

HIST_W2_DIR = "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2"
W2_M5_DIR = "docs/evaluation/geometry/runs/hybrid-v2-w2-m5-adapter4-category-a-identity-repair"


def git_out(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha256_raw(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_lf(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def canonical_descriptor(v_src: dict, pt_xyz: list[str], solid_verts: list[str], solid_pts_norm: dict[str, tuple[Fraction, Fraction, Fraction]]):
    xyz = tuple(Fraction(x) for x in pt_xyz)
    if v_src["kind"] == "SOLID_VERTEX":
        v_label = solid_verts[v_src["solid_vertex_index"]]
        assert solid_pts_norm[v_label] == xyz
        return ("VERTEX", v_label)
    assert v_src["kind"] == "SOLID_EDGE_INTERSECTION"
    i0, i1 = v_src["solid_edge_vertex_indices"]
    u_label, v_label = solid_verts[i0], solid_verts[i1]
    p0, p1 = solid_pts_norm[u_label], solid_pts_norm[v_label]
    t_vals = []
    for k in range(3):
        if p1[k] != p0[k]:
            t_vals.append((xyz[k] - p0[k]) / (p1[k] - p0[k]))
        else:
            assert xyz[k] == p0[k]
    assert len(set(t_vals)) == 1
    t = t_vals[0]
    assert Fraction(0) < t < Fraction(1)
    return ("EDGE", u_label, v_label, str(t))


def oracle_descriptor(item: dict):
    if "vertex" in item:
        return ("VERTEX", item["vertex"])
    u, v = item["edge"]
    return ("EDGE", u, v, str(Fraction(item["t"])))


def check_cyclic_equivalence(cycle_a: list, cycle_b: list) -> dict:
    assert len(cycle_a) == len(cycle_b)
    n = len(cycle_a)
    for shift in range(n):
        rotated = cycle_a[shift:] + cycle_a[:shift]
        if rotated == cycle_b:
            return {"cyclic_equivalent": True, "orientation": "same", "shift": shift}
    rev = list(reversed(cycle_a))
    for shift in range(n):
        rotated = rev[shift:] + rev[:shift]
        if rotated == cycle_b:
            return {"cyclic_equivalent": True, "orientation": "reversed", "shift": shift}
    return {"cyclic_equivalent": False, "orientation": None, "shift": None}


def verify_section_1_preflight() -> dict:
    main_actual = git_out("rev-parse", "main")
    origin_main_actual = git_out("rev-parse", "origin/main")
    remote_ls = git_out("ls-remote", "origin", "refs/heads/main").split()[0]
    w2_actual = git_out("rev-parse", "research/hybrid-v2-independent-vietnamese-section-holdout-wave2")

    assert main_actual == POSTMERGE_MAIN_SHA, f"main mismatch: {main_actual}"
    assert origin_main_actual == POSTMERGE_MAIN_SHA, f"origin/main mismatch: {origin_main_actual}"
    assert remote_ls == POSTMERGE_MAIN_SHA, f"remote mismatch: {remote_ls}"
    assert w2_actual == HIST_W2_SHA, f"holdout-wave2 mismatch: {w2_actual}"

    # Verify ancestry chain
    for anc, desc in [
        (PREMERGE_MAIN_SHA, PRODUCT_SHA),
        (PRODUCT_SHA, ARTIFACTS_SHA),
        (ARTIFACTS_SHA, T3_CANDIDATE_SHA),
        (T3_CANDIDATE_SHA, POSTMERGE_MAIN_SHA),
        (POSTMERGE_MAIN_SHA, "HEAD"),
    ]:
        subprocess.check_call(["git", "merge-base", "--is-ancestor", anc, desc], cwd=ROOT)

    # Verify zero product diff between T3 candidate and main / HEAD
    diff_t3_to_main = git_out("diff", "--name-only", f"{T3_CANDIDATE_SHA}..{POSTMERGE_MAIN_SHA}", "--", "backend/app", "frontend/src")
    diff_t3_to_head = git_out("diff", "--name-only", f"{T3_CANDIDATE_SHA}..HEAD", "--", "backend/app", "frontend/src")
    diff_pre_to_main = git_out("diff", "--name-only", f"{PREMERGE_MAIN_SHA}..{POSTMERGE_MAIN_SHA}", "--", "backend/app", "frontend/src").splitlines()
    assert diff_t3_to_main == ""
    assert diff_t3_to_head == ""
    assert diff_pre_to_main == ["backend/app/ai/adapter4_route.py"]

    # Verify historical holdout Wave 2 untouched
    diff_hist_w2 = git_out("diff", "--name-only", f"{HIST_W2_SHA}..HEAD", "--", HIST_W2_DIR)
    assert diff_hist_w2 == ""

    # Verify original W2-M5 committed files untouched on HEAD
    preserved_w2_m5_files = [
        f"{W2_M5_DIR}/report.md",
        f"{W2_M5_DIR}/handoff.md",
        f"{W2_M5_DIR}/review.md",
        f"{W2_M5_DIR}/run.json",
        f"{W2_M5_DIR}/baseline-audit.md",
        f"{W2_M5_DIR}/architecture-decision.md",
        f"{W2_M5_DIR}/plan.md",
        f"{W2_M5_DIR}/inputs/development.json",
        f"{W2_M5_DIR}/inputs/oracle.json",
        f"{W2_M5_DIR}/results/red-before.json",
        f"{W2_M5_DIR}/results/green-after.json",
        f"{W2_M5_DIR}/results/tamper-results.json",
        f"{W2_M5_DIR}/results/wave2-post-feedback-regression.json",
        f"{W2_M5_DIR}/results/w2-a10-scorer-adjudication-receipt.json",
        f"{W2_M5_DIR}/verification/scope-and-evidence.json",
        f"{W2_M5_DIR}/verification/full-t3/receipt.json",
        f"{W2_M5_DIR}/verification/full-t3/full-t3.log",
    ]
    diff_preserved = git_out("diff", "--name-only", f"{POSTMERGE_MAIN_SHA}..HEAD", "--", *preserved_w2_m5_files)
    assert diff_preserved == "", f"Original W2-M5 files modified: {diff_preserved}"

    # Verify candidate freeze
    freeze_cmd = [
        sys.executable,
        str(ROOT / "backend/scripts/freeze_evaluation_candidate.py"),
        "--manifest",
        str(ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "--verify",
    ]
    freeze_proc = subprocess.run(freeze_cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    cand_manifest = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    assert cand_manifest["measured_system"]["tree_hash"] == FREEZE_TREE_HASH
    assert cand_manifest["measured_system"]["so_file"] == 118
    assert cand_manifest["product_commit_sha"] == PRODUCT_SHA

    from app.simulation.geometry_functions.registry import REGISTRY_VERSION
    from app.simulation.geometry_functions.planner import PLANNER_VERSION
    from app.simulation.geometry_functions.engine import ENGINE_VERSION, PLANE_SECTION_CERTIFICATE_VERSION
    from app.ai.adapter4_route import ADAPTER_V4_VERSION
    from app.main import CACHE_VERSION
    from app.ai.pipeline import route_policy_snapshot

    pol = route_policy_snapshot()
    versions = {
        "registry": REGISTRY_VERSION,
        "planner": PLANNER_VERSION,
        "engine": ENGINE_VERSION,
        "adapter": ADAPTER_V4_VERSION,
        "certificate": PLANE_SECTION_CERTIFICATE_VERSION,
        "cache_version": int(CACHE_VERSION),
        "default_mode": str(pol.geometry_compiler_mode),
        "hybrid_preview_enabled": bool(pol.hybrid_preview_enabled),
    }
    assert versions == {
        "registry": "geometry-functions/19",
        "planner": "geometry-fact-planner/17",
        "engine": "geometry-function-engine/14",
        "adapter": "hybrid-simulation-adapter/4",
        "certificate": "plane-section-certificate/1",
        "cache_version": 130,
        "default_mode": "LLM_ONLY",
        "hybrid_preview_enabled": False,
    }

    return {
        "main_sha": main_actual,
        "origin_main_sha": origin_main_actual,
        "remote_main_sha": remote_ls,
        "historical_holdout_wave2_sha": w2_actual,
        "premerge_main_sha": PREMERGE_MAIN_SHA,
        "product_commit_sha": PRODUCT_SHA,
        "artifacts_commit_sha": ARTIFACTS_SHA,
        "frozen_t3_candidate_sha": T3_CANDIDATE_SHA,
        "product_diff_t3_to_main": [],
        "product_diff_t3_to_head": [],
        "product_files_modified_in_wave": diff_pre_to_main,
        "historical_holdout_wave2_diff": [],
        "original_w2_m5_files_diff": [],
        "measured_system_files": 118,
        "measured_system_tree_hash": FREEZE_TREE_HASH,
        "freeze_verify_stdout": freeze_proc.stdout.strip(),
        "versions": versions,
        "live_provider_calls": 0,
    }


def verify_sections_2_and_3_cases() -> dict:
    from app.simulation.geometry import radical as R
    from app.simulation.geometry_functions.engine import _binh_phuong
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

    w2_inputs_bytes = git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/inputs/holdout-wave2.json")
    w2_expected_bytes = git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/oracle/expected.json")
    w2_geometry_bytes = git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/oracle/geometry.json")
    dev_inputs_bytes = git_bytes("show", f"{POSTMERGE_MAIN_SHA}:{W2_M5_DIR}/inputs/development.json")
    dev_oracle_bytes = git_bytes("show", f"{POSTMERGE_MAIN_SHA}:{W2_M5_DIR}/inputs/oracle.json")

    w2_inputs = json.loads(w2_inputs_bytes.decode("utf-8"))
    w2_expected_raw = json.loads(w2_expected_bytes.decode("utf-8"))
    w2_expected = w2_expected_raw.get("cases", w2_expected_raw.get("oracles", w2_expected_raw))
    w2_geometry_raw = json.loads(w2_geometry_bytes.decode("utf-8"))
    w2_geometry = w2_geometry_raw.get("cases", w2_geometry_raw.get("oracles", w2_geometry_raw))
    dev_inputs = json.loads(dev_inputs_bytes.decode("utf-8"))
    dev_oracles = json.loads(dev_oracle_bytes.decode("utf-8"))["oracles"]

    w2_cases = {c["id"]: c for c in w2_inputs["cases"]}
    dev_cases = {c["id"]: c for c in dev_inputs["positive_cases"]}

    # Verify W2-A07 and W2-A10 in development.json are byte-for-byte identical in payload to frozen holdout-wave2.json
    for cid in ["W2-A07", "W2-A10"]:
        assert w2_cases[cid]["problem_text"] == dev_cases[cid]["problem_text"]
        assert w2_cases[cid]["payload"] == dev_cases[cid]["payload"]
        assert w2_expected[cid]["boundary"] == dev_oracles[cid]["boundary"]
        assert w2_expected[cid]["area_squared"] == dev_oracles[cid]["area_squared"]
        assert w2_expected[cid]["expected_certificate_category"] == dev_oracles[cid]["expected_certificate_category"]

    def sub(u, v): return tuple(u[i] - v[i] for i in range(3))
    def add(u, v): return tuple(u[i] + v[i] for i in range(3))
    def scale(c, u): return tuple(c * u[i] for i in range(3))
    def dot(u, v): return sum(u[i] * v[i] for i in range(3))
    def cross(u, v):
        return (
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        )

    # --- W2-A07 verification ---
    c07 = w2_cases["W2-A07"]
    e07 = w2_expected["W2-A07"]
    g07 = w2_geometry["W2-A07"]
    res07 = run_typed_fact_next_v2_route(deepcopy(c07["payload"]))
    env07 = build_adapter4_response(deepcopy(res07), c07["problem_text"])
    objs07 = {o["id"]: o for o in res07.scene3d["objects"]}
    td07 = objs07["td_sec"]
    sec07 = env07["route_d"]["sections"][0]

    solid07_verts = ["A", "B", "C", "A'", "B'", "C'"]
    solid07_norm = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(0), Fraction(1), Fraction(0)),
        "A'": (Fraction(0), Fraction(0), Fraction(1)),
        "B'": (Fraction(1), Fraction(0), Fraction(1)),
        "C'": (Fraction(0), Fraction(1), Fraction(1)),
    }
    prod_desc_07 = [
        canonical_descriptor(vs, pt, solid07_verts, solid07_norm)
        for vs, pt in zip(td07["vertex_sources"], td07["polygon"])
    ]
    oracle_desc_07 = [oracle_descriptor(b) for b in e07["boundary"]]
    cyc07 = check_cyclic_equivalence(prod_desc_07, oracle_desc_07)
    assert cyc07["cyclic_equivalent"] is True

    # Independent Euclidean computation for W2-A07 (AB=5, BC=5, right at B, AA'=10)
    A07 = (Fraction(0), Fraction(0), Fraction(0))
    B07 = (Fraction(5), Fraction(0), Fraction(0))
    C07 = (Fraction(5), Fraction(5), Fraction(0))
    Ap07 = (Fraction(0), Fraction(0), Fraction(10))
    Bp07 = (Fraction(5), Fraction(0), Fraction(10))
    Cp07 = (Fraction(5), Fraction(5), Fraction(10))
    n07 = sub(Cp07, A07)  # (5, 5, 10)
    t_BBp_07 = -dot(n07, sub(B07, Ap07)) / dot(n07, sub(Bp07, B07))
    t_CCp_07 = -dot(n07, sub(C07, Ap07)) / dot(n07, sub(Cp07, C07))
    M07 = add(B07, scale(t_BBp_07, sub(Bp07, B07)))
    N07 = add(C07, scale(t_CCp_07, sub(Cp07, C07)))
    cr07 = cross(sub(M07, Ap07), sub(N07, Ap07))
    area_sq_07 = Fraction(1, 4) * dot(cr07, cr07)
    assert t_BBp_07 == Fraction(3, 4)
    assert t_CCp_07 == Fraction(1, 2)
    assert area_sq_07 == Fraction(1875, 8)
    assert _binh_phuong(res07.exec_result.final_memory["kq_mg1"]) == Fraction(1875, 8)
    assert R.display(R.sqrt_rational(area_sq_07)) == "25√6/4"
    assert env07["route_d"]["answers"]["mg1"] == "25√6/4"

    # --- W2-A10 verification ---
    c10 = w2_cases["W2-A10"]
    e10 = w2_expected["W2-A10"]
    g10 = w2_geometry["W2-A10"]
    res10 = run_typed_fact_next_v2_route(deepcopy(c10["payload"]))
    env10 = build_adapter4_response(deepcopy(res10), c10["problem_text"])
    objs10 = {o["id"]: o for o in res10.scene3d["objects"]}
    td10 = objs10["td_sec"]
    sec10 = env10["route_d"]["sections"][0]

    solid10_verts = ["A", "B", "C", "D", "A'", "B'", "C'", "D'"]
    solid10_norm = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(1), Fraction(1), Fraction(0)),
        "D": (Fraction(0), Fraction(1), Fraction(0)),
        "A'": (Fraction(0), Fraction(0), Fraction(1)),
        "B'": (Fraction(1), Fraction(0), Fraction(1)),
        "C'": (Fraction(1), Fraction(1), Fraction(1)),
        "D'": (Fraction(0), Fraction(1), Fraction(1)),
    }
    prod_desc_10 = [
        canonical_descriptor(vs, pt, solid10_verts, solid10_norm)
        for vs, pt in zip(td10["vertex_sources"], td10["polygon"])
    ]
    oracle_desc_10 = [oracle_descriptor(b) for b in e10["boundary"]]
    cyc10 = check_cyclic_equivalence(prod_desc_10, oracle_desc_10)
    assert cyc10["cyclic_equivalent"] is True
    assert cyc10["orientation"] == "reversed"
    assert cyc10["shift"] == 2

    # Independent Euclidean computation for W2-A10 (cuboid AB=3, AD=6, AA'=9)
    A10 = (Fraction(0), Fraction(0), Fraction(0))
    B10 = (Fraction(3), Fraction(0), Fraction(0))
    C10 = (Fraction(3), Fraction(6), Fraction(0))
    D10 = (Fraction(0), Fraction(6), Fraction(0))
    Ap10 = (Fraction(0), Fraction(0), Fraction(9))
    Bp10 = (Fraction(3), Fraction(0), Fraction(9))
    Cp10 = (Fraction(3), Fraction(6), Fraction(9))
    Dp10 = (Fraction(0), Fraction(6), Fraction(9))
    n10 = sub(Cp10, A10)  # (3, 6, 9)
    t_BBp_10 = -dot(n10, sub(B10, Ap10)) / dot(n10, sub(Bp10, B10))
    t_CCp_10 = -dot(n10, sub(C10, Ap10)) / dot(n10, sub(Cp10, C10))
    t_DDp_10 = -dot(n10, sub(D10, Ap10)) / dot(n10, sub(Dp10, D10))
    I10 = add(B10, scale(t_BBp_10, sub(Bp10, B10)))
    I1_10 = add(C10, scale(t_CCp_10, sub(Cp10, C10)))
    I2_10 = add(D10, scale(t_DDp_10, sub(Dp10, D10)))
    # Polygon order [I, A', I2, I1]
    cr10_1 = cross(sub(Ap10, I10), sub(I2_10, I10))
    cr10_2 = cross(sub(I2_10, I10), sub(I1_10, I10))
    cr10_tot = add(cr10_1, cr10_2)
    area_sq_10 = Fraction(1, 4) * dot(cr10_tot, cr10_tot)
    assert t_BBp_10 == Fraction(8, 9)
    assert t_CCp_10 == Fraction(4, 9)
    assert t_DDp_10 == Fraction(5, 9)
    assert area_sq_10 == Fraction(504)
    assert str(area_sq_10) == e10["area_squared"]

    # Check repository at 2c42f6cf for conversational hallucination tokens
    hallucinated_tokens = [
        "section_37467f986437",
        "37467f986437",
        "section_fa8b24d27d9e",
        "fa8b24d27d9e",
        "(A, B, C, A′)",
        "(A, B, C, A')",
        "(A, M, P, N)",
        "holdout_wave2_w2_a07_scorer_adjudication",
        "holdout_wave2_after_w2_m5_raw",
    ]
    repo_hits = []
    for tok in hallucinated_tokens:
        proc = subprocess.run(
            ["git", "grep", "-F", tok, POSTMERGE_MAIN_SHA],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            repo_hits.append({"token": tok, "matches": proc.stdout.strip()})
    assert repo_hits == [], f"Unexpected repo hits: {repo_hits}"

    return {
        "holdout_wave2_inputs_sha256_lf": sha256_lf(w2_inputs_bytes),
        "holdout_wave2_expected_sha256_lf": sha256_lf(w2_expected_bytes),
        "holdout_wave2_geometry_sha256_lf": sha256_lf(w2_geometry_bytes),
        "W2-A07": {
            "frozen_case_sha256": sha256_raw(json.dumps(c07, ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "input_payload_sha256": sha256_raw(json.dumps(c07["payload"], ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "problem_text": c07["problem_text"],
            "expected_solid": {
                "solid_id": "s1",
                "solid_type": "prism",
                "family": "right_triangular_prism",
                "notation": "ABC.A'B'C'",
                "dimensions": {"AB": "5", "BC": "5", "right_at": "B", "AA'": "10"},
                "plane_spec": {"plane_name": "α", "kind": "through_point_perpendicular_line", "through_point": "A'", "perpendicular_line": ["A", "C'"]},
            },
            "expected_polygon_oracle": oracle_desc_07,
            "actual_polygon_descriptors": prod_desc_07,
            "actual_scene3d_section": {
                "id": td07["id"],
                "label": td07["label"],
                "notation": td07["notation"],
                "polygon_normalized_prism_coords": td07["polygon"],
                "polygon_vertex_order": ["M", "A'", "N"],
                "euclidean_coords": {
                    "M": [str(x) for x in M07],
                    "A'": [str(x) for x in Ap07],
                    "N": [str(x) for x in N07],
                },
            },
            "cyclic_equivalence": cyc07,
            "category_a_certificate": sec07,
            "exact_oracle": {
                "expected_certificate_category": e07["expected_certificate_category"],
                "vertex_count": 3,
                "area_squared": e07["area_squared"],
                "expected_answer": "25√6/4",
            },
            "product_response": {
                "route_status": res07.status,
                "adapter4_status": env07["route_d"]["status"],
                "envelope_status": env07["envelope"]["status"],
                "answer_mg1": env07["route_d"]["answers"]["mg1"],
                "area_squared": str(_binh_phuong(res07.exec_result.final_memory["kq_mg1"])),
                "notation_A_prime": objs07["A_prime"]["notation"],
            },
            "scorer_outcome": {
                "raw_historical_scorer": "SERVED_CORRECT",
                "adjudicated_scorer": "SERVED_CORRECT",
            },
            "discrepancy_classification": {
                "conversational_postmerge_report_string": "section_37467f986437 (A, B, C, A′)",
                "exists_in_product_or_fixtures_or_git": False,
                "classification": "REPORT_RECORDING_ERROR_CONVERSATIONAL_ONLY",
                "committed_report_prose_note": "report.md:32 wrote illustrative coordinates A'=[0,0,5], M=[6,0,15/4], N=[0,6,5/2] and polygon_A_prime_M_N; actual scene3d object is td_sec (notation MA′N) with normalized coords M=[1,0,3/4], A'=[0,0,1], N=[0,1,1/2] and Euclidean coords A'=[0,0,10], M=[5,0,15/2], N=[5,5,5] giving area_squared = 1875/8.",
            },
        },
        "W2-A10": {
            "frozen_case_sha256": sha256_raw(json.dumps(c10, ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "input_payload_sha256": sha256_raw(json.dumps(c10["payload"], ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "problem_text": c10["problem_text"],
            "expected_solid": {
                "solid_id": "s1",
                "solid_type": "prism",
                "family": "cuboid",
                "notation": "ABCD.A'B'C'D'",
                "dimensions": {"AB": "3a", "AD": "6a", "AA'": "9a", "base_shape": "rectangle"},
                "plane_spec": {"plane_name": "Q", "kind": "through_point_perpendicular_line", "through_point": "A'", "perpendicular_line": ["A", "C'"]},
            },
            "expected_polygon_oracle": oracle_desc_10,
            "actual_polygon_descriptors": prod_desc_10,
            "actual_scene3d_section": {
                "id": td10["id"],
                "label": td10["label"],
                "notation": td10["notation"],
                "polygon_normalized_prism_coords": td10["polygon"],
                "polygon_vertex_order": ["I", "A'", "I2", "I1"],
                "euclidean_coords": {
                    "I": [str(x) for x in I10],
                    "A'": [str(x) for x in Ap10],
                    "I2": [str(x) for x in I2_10],
                    "I1": [str(x) for x in I1_10],
                },
            },
            "cyclic_equivalence": cyc10,
            "category_a_certificate": sec10,
            "exact_oracle": {
                "expected_certificate_category": e10["expected_certificate_category"],
                "vertex_count": 4,
                "area_squared": e10["area_squared"],
                "question_type": "section_only",
            },
            "product_response": {
                "route_status": res10.status,
                "adapter4_status": env10["route_d"]["status"],
                "envelope_status": env10["envelope"]["status"],
                "answers": env10["route_d"]["answers"],
                "polygon_area_squared": str(area_sq_10),
                "notation_A_prime": objs10["A_prime"]["notation"],
            },
            "scorer_outcome": {
                "raw_historical_scorer": "WRONG_SERVED (scorer primed-label lookup bug at evaluate_holdout_wave2.py:184)",
                "adjudicated_scorer": "SERVED_CORRECT",
            },
            "discrepancy_classification": {
                "conversational_postmerge_report_string": "section_fa8b24d27d9e (A, M, P, N)",
                "exists_in_product_or_fixtures_or_git": False,
                "classification": "REPORT_RECORDING_ERROR_CONVERSATIONAL_ONLY",
                "committed_report_prose_note": "report.md:33 and handoff.md:25 summarized W2-A10 in prose as 'cube ABCD.A'B'C'D', edge a = 6, section (A'MN)' and 'polygon_I_A_prime_I2_I1'; actual frozen W2-A10 is a rectangular cuboid (AB=3a, AD=6a, AA'=9a, cutting plane (Q), section object td_sec 'Thiết diện bởi (Q)') with cycle [I, A', I2, I1] and exact area_squared = 504.",
            },
        },
        "repository_scan_for_conversational_hallucinations": {
            "tokens_scanned": hallucinated_tokens,
            "hits_in_committed_repo": repo_hits,
        },
    }


def verify_section_4_scorer_adjudication() -> dict:
    reg_bytes = git_bytes("show", f"{POSTMERGE_MAIN_SHA}:{W2_M5_DIR}/results/wave2-post-feedback-regression.json")
    adj_bytes = git_bytes("show", f"{POSTMERGE_MAIN_SHA}:{W2_M5_DIR}/results/w2-a10-scorer-adjudication-receipt.json")
    reg = json.loads(reg_bytes.decode("utf-8"))
    adj = json.loads(adj_bytes.decode("utf-8"))

    assert reg["target_cases"]["W2-A07"]["outcome"] == "SERVED_CORRECT"
    assert reg["target_cases"]["W2-A07"]["oracle_mismatches"] == []
    assert reg["target_cases"]["W2-A10_raw"]["outcome"] == "WRONG_SERVED"
    assert reg["target_cases"]["W2-A10_adjudicated"]["outcome"] == "SERVED_CORRECT"
    assert adj["case_id"] == "W2-A10"
    assert adj["raw_scorer_verdict"] == "WRONG_SERVED"
    assert adj["adjudicated_scorer_verdict"] == "SERVED_CORRECT"

    return {
        "affected_case_id": "W2-A10",
        "unaffected_case_id": "W2-A07",
        "why_w2_a07_passes_raw_scorer": "W2-A07 is a 3-vertex triangle {A', M, N}; every permutation of 3 elements is either a cyclic rotation or reversal of the 3-cycle, so even when A' falls back to poly_idx=0, [A', M, N] remains cyclically equivalent to [M, A', N].",
        "why_w2_a10_fails_raw_scorer": "W2-A10 is a 4-vertex quadrilateral [I, A', I2, I1]; at evaluate_holdout_wave2.py:184, `v['label'] in objects_by_id` is False for \"A'\" (keyed by \"A_prime\"), so \"A'\" falls back to poly_idx=0 and collides with \"I\" (poly_idx=0), sorting into the bow-tie order [A', I, I2, I1] instead of [I, A', I2, I1].",
        "committed_receipt_path": f"{W2_M5_DIR}/results/w2-a10-scorer-adjudication-receipt.json",
        "committed_receipt_sha256_lf": sha256_lf(adj_bytes),
        "committed_regression_path": f"{W2_M5_DIR}/results/wave2-post-feedback-regression.json",
        "committed_regression_sha256_lf": sha256_lf(reg_bytes),
        "historical_scorer_modified": False,
    }


def verify_section_5_corpus_denominators() -> dict:
    w2_inputs = json.loads(git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/inputs/holdout-wave2.json").decode("utf-8"))
    w2_strata = {}
    payload_hashes = set()
    for c in w2_inputs["cases"]:
        s = c["stratum"]
        w2_strata[s] = w2_strata.get(s, 0) + 1
        ph = sha256_raw(json.dumps(c["payload"], ensure_ascii=False, sort_keys=True).encode("utf-8"))
        assert ph not in payload_hashes, f"Duplicate payload in holdout-wave2.json: {c['id']}"
        payload_hashes.add(ph)

    assert len(w2_inputs["cases"]) == 96
    assert w2_strata == {"P-B": 36, "P-A": 12, "N": 48}

    dev_inputs = json.loads(git_bytes("show", f"{POSTMERGE_MAIN_SHA}:{W2_M5_DIR}/inputs/development.json").decode("utf-8"))
    tamper_res = json.loads(git_bytes("show", f"{POSTMERGE_MAIN_SHA}:{W2_M5_DIR}/results/tamper-results.json").decode("utf-8"))
    assert len(dev_inputs["positive_cases"]) == 14
    assert tamper_res["tamper_total"] == 12

    w1_recheck = json.loads(git_bytes("show", f"{POSTMERGE_MAIN_SHA}:docs/evaluation/geometry/runs/hybrid-v2-holdout-failure-repair/results/post-feedback-84-comparison.json").decode("utf-8"))

    return {
        "independent_holdout_wave2": {
            "path": f"{HIST_W2_DIR}/inputs/holdout-wave2.json",
            "commit": HIST_W2_SHA,
            "total_cases": 96,
            "category_b_positives_P_B": 36,
            "category_a_positives_P_A": 12,
            "positive_total": 48,
            "negatives_N": 48,
        },
        "w2_m5_development_and_tamper_corpus": {
            "path": f"{W2_M5_DIR}/inputs/development.json",
            "commit": POSTMERGE_MAIN_SHA,
            "total_cases": 26,
            "positive_category_a_primed_cases": 14,
            "mandatory_tamper_cases": 12,
        },
        "holdout_wave1": {
            "path": "docs/evaluation/geometry/runs/hybrid-v2-holdout-failure-repair/results/post-feedback-84-comparison.json",
            "total_cases": 84,
            "positive_total": 42,
            "negative_total": 42,
        },
        "erroneous_22_14_12_origin": {
            "exists_in_any_repository_file": False,
            "explanation": "In step 9929 (context compaction checkpoint), the summarizer conflated Wave 2's 48 positive cases with W2-M5's 14 positive development cases and 12 tamper cases (48 - 14 - 12 = 22) and fabricated a 48-case breakdown '22 Category A, 14 Category B, 12 Category C'. Category C does not exist in AlgoSim's section certificate taxonomy (only Category A DINH_CAT_CANH and Category B ENGINE_DERIVED_SECTION exist).",
        },
    }


def main() -> int:
    s1 = verify_section_1_preflight()
    s23 = verify_sections_2_and_3_cases()
    s4 = verify_section_4_scorer_adjudication()
    s5 = verify_section_5_corpus_denominators()

    scope_ev = json.loads(git_bytes("show", f"{POSTMERGE_MAIN_SHA}:{W2_M5_DIR}/verification/scope-and-evidence.json").decode("utf-8"))
    locked_hashes = {}
    for rel_path, expected_lf in scope_ev["locked_evidence_sha256_lf"].items():
        raw_b = (RUN / rel_path).read_bytes()
        actual_lf = sha256_lf(raw_b)
        assert actual_lf == expected_lf, f"Hash mismatch on {rel_path}: {actual_lf} != {expected_lf}"
        locked_hashes[rel_path] = {
            "bytes": len(raw_b),
            "sha256_raw": sha256_raw(raw_b),
            "sha256_lf": actual_lf,
            "status": "MATCH",
        }

    out = {
        "task_id": "HYBRID_V2_W2_M5_POSTMERGE_CASE_IDENTITY_ADJUDICATION",
        "final_status": "EVIDENCE_CORRECTION_REQUIRED",
        "product_regression_found": False,
        "section_1_preflight": s1,
        "sections_2_and_3_case_identities": s23,
        "section_4_scorer_adjudication": s4,
        "section_5_corpus_denominators": s5,
        "locked_w2_m5_evidence_inventory": locked_hashes,
    }

    out_path = RUN / "results/postmerge-case-identity-adjudication.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": out["final_status"], "receipt": str(out_path.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
