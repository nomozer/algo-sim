# -*- coding: utf-8 -*-
"""Pre-merge evidence reconciliation verifier for HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION."""
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

MAIN_SHA = "d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c"
HIST_W2_SHA = "ecdc26b012c8ce80d53524a98dc75cdcb020079d"
SG_HEAD_SHA = "d99f6149ff1997258970bf888db5484665b106b8"
SG_PRODUCT_SHA = "c6f6b64bda6473c175a32a7875a9dd9831ae7c6d"
SG_CANDIDATE_SHA = "b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9"
PREREG_RED_SHA = "574ad40ca446232bf54e8e26cda196eee943fcb3"
FIRST_ATTEMPT_PRODUCT_SHA = "8ecad7bd5ff114c4be58e52ff44985a89811bf1f"
FIRST_ATTEMPT_CANDIDATE_SHA = "14bc010e4b4af2bb324c63e309d41c5c5847a904"
PRODUCT_SHA = "051224ee2740cbf5d55dd94633503db1f0050ada"
T3_CANDIDATE_SHA = "1e0c8db668bbe110f343a8a67cdeca465008c188"
PRE_RECON_HEAD_SHA = "e78ecfe7a28cbe9de2754b08283b56d3829d1c1a"
FREEZE_TREE_HASH = "8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369"

HIST_W2_DIR = "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2"
SG_DIR = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-wave2-source-gate-language-generalization"


def git_out(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha256_raw(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_lf(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def verify_git_and_freeze() -> dict:
    main_actual = git_out("rev-parse", "main")
    origin_main_actual = git_out("rev-parse", "origin/main")
    w2_actual = git_out("rev-parse", "research/hybrid-v2-independent-vietnamese-section-holdout-wave2")
    sg_actual = git_out("rev-parse", "research/hybrid-v2-wave2-source-gate-language-generalization")

    assert main_actual == MAIN_SHA, f"main mismatch: {main_actual}"
    assert origin_main_actual == MAIN_SHA, f"origin/main mismatch: {origin_main_actual}"
    assert w2_actual == HIST_W2_SHA, f"holdout-wave2 mismatch: {w2_actual}"
    assert sg_actual == SG_HEAD_SHA, f"source-gate mismatch: {sg_actual}"

    # Verify ancestry
    subprocess.check_call(["git", "merge-base", "--is-ancestor", MAIN_SHA, SG_HEAD_SHA], cwd=ROOT)
    subprocess.check_call(["git", "merge-base", "--is-ancestor", SG_HEAD_SHA, PRODUCT_SHA], cwd=ROOT)
    subprocess.check_call(["git", "merge-base", "--is-ancestor", PRODUCT_SHA, T3_CANDIDATE_SHA], cwd=ROOT)
    subprocess.check_call(["git", "merge-base", "--is-ancestor", T3_CANDIDATE_SHA, PRE_RECON_HEAD_SHA], cwd=ROOT)
    subprocess.check_call(["git", "merge-base", "--is-ancestor", T3_CANDIDATE_SHA, "HEAD"], cwd=ROOT)

    # Verify zero product diff between T3_CANDIDATE_SHA and PRE_RECON_HEAD_SHA / HEAD
    diff_t3_to_prerecon = git_out("diff", "--name-only", f"{T3_CANDIDATE_SHA}..{PRE_RECON_HEAD_SHA}", "--", "backend/app", "frontend/src")
    diff_t3_to_head = git_out("diff", "--name-only", f"{T3_CANDIDATE_SHA}..HEAD", "--", "backend/app", "frontend/src")
    diff_sg_to_t3 = git_out("diff", "--name-only", f"{SG_HEAD_SHA}..{T3_CANDIDATE_SHA}", "--", "backend/app", "frontend/src").splitlines()
    assert diff_t3_to_prerecon == "", f"Product diff 1e0c8db6..e78ecfe7 not empty: {diff_t3_to_prerecon}"
    assert diff_t3_to_head == "", f"Product diff 1e0c8db6..HEAD not empty: {diff_t3_to_head}"
    assert diff_sg_to_t3 == ["backend/app/simulation/geometry/radical.py"], f"Unexpected product diff: {diff_sg_to_t3}"

    # Verify candidate freeze via freeze_evaluation_candidate.py --verify
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

    # Verify component versions & cache version
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
    }
    assert versions == {
        "registry": "geometry-functions/19",
        "planner": "geometry-fact-planner/17",
        "engine": "geometry-function-engine/14",
        "adapter": "hybrid-simulation-adapter/4",
        "certificate": "plane-section-certificate/1",
        "cache_version": 130,
        "default_mode": "LLM_ONLY",
    }, f"Version mismatch: {versions}"

    return {
        "main_sha": main_actual,
        "origin_main_sha": origin_main_actual,
        "historical_holdout_wave2_sha": w2_actual,
        "parent_source_gate_head_sha": sg_actual,
        "parent_source_gate_product_sha": SG_PRODUCT_SHA,
        "parent_source_gate_t3_candidate_sha": SG_CANDIDATE_SHA,
        "preregistered_red_sha": PREREG_RED_SHA,
        "first_attempt_product_sha": FIRST_ATTEMPT_PRODUCT_SHA,
        "first_attempt_candidate_sha": FIRST_ATTEMPT_CANDIDATE_SHA,
        "product_commit_sha": PRODUCT_SHA,
        "frozen_t3_candidate_sha": T3_CANDIDATE_SHA,
        "pre_reconciliation_head_sha": PRE_RECON_HEAD_SHA,
        "product_diff_t3_to_pre_reconciliation": [],
        "product_diff_t3_to_head": [],
        "product_files_modified_in_wave": diff_sg_to_t3,
        "measured_system_files": 118,
        "measured_system_tree_hash": FREEZE_TREE_HASH,
        "freeze_verify_stdout": freeze_proc.stdout.strip(),
        "versions": versions,
    }


def verify_finding_a_w2_a04() -> dict:
    from app.simulation.geometry import radical as R
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

    corpus_bytes = git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/inputs/holdout-wave2.json")
    expected_bytes = git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/oracle/expected.json")
    geometry_bytes = git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/oracle/geometry.json")

    corpus = json.loads(corpus_bytes.decode("utf-8"))
    expected = json.loads(expected_bytes.decode("utf-8"))
    geometry = json.loads(geometry_bytes.decode("utf-8"))

    c_a04 = next(c for c in corpus["cases"] if c["id"] == "W2-A04")
    e_a04 = expected["W2-A04"]
    g_a04 = next(g for g in geometry["cases"] if g["id"] == "W2-A04") if isinstance(geometry["cases"], list) else geometry["cases"]["W2-A04"]

    # Product execution
    route_res = run_typed_fact_next_v2_route(deepcopy(c_a04["payload"]))
    a4_res = build_adapter4_response(route_res, c_a04["problem_text"])
    kq_mg1 = route_res.exec_result.final_memory["kq_mg1"]
    qty_obj = next(o for o in a4_res["envelope"]["scene3d"]["objects"] if o.get("id") == "kq_mg1")

    # Independent Euclidean Fraction recomputation
    A = (Fraction(0), Fraction(0), Fraction(0))
    B = (Fraction(6), Fraction(0), Fraction(0))
    C = (Fraction(6), Fraction(8), Fraction(0))
    D = (Fraction(0), Fraction(8), Fraction(0))
    S = (Fraction(0), Fraction(0), Fraction(10))

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

    n_vec = sub(C, S)  # (6, 8, -10)
    def intersect_edge(P0, P1):
        t = -dot(n_vec, sub(P0, A)) / dot(n_vec, sub(P1, P0))
        pt = add(P0, scale(t, sub(P1, P0)))
        return t, pt

    t_SB, M = intersect_edge(S, B)
    t_SC, N = intersect_edge(S, C)
    t_SD, P = intersect_edge(S, D)

    c1 = cross(sub(M, A), sub(N, A))
    c2 = cross(sub(N, A), sub(P, A))
    c_total = add(c1, c2)
    area_sq = Fraction(1, 4) * dot(c_total, c_total)
    p, q = area_sq.numerator, area_sq.denominator
    pq = p * q
    rad_val = R.sqrt_rational(area_sq)
    sq_back = R.square(rad_val)

    assert str(area_sq) == "253125000/485809"
    assert e_a04["area_squared"] == "253125000/485809"
    assert pq == 122970403125000
    assert pq == (7841250 ** 2) * 2
    assert p == (2 ** 3) * (3 ** 4) * (5 ** 8) == (11250 ** 2) * 2
    assert q == (17 ** 2) * (41 ** 2) == 697 ** 2
    assert rad_val == R.Radical(Fraction(11250, 697), 2, 0)
    assert kq_mg1 == rad_val
    assert R.display(rad_val) == "11250√2/697"
    assert route_res.answers["mg1"] == "11250√2/697"
    assert qty_obj["value"] == "11250√2/697"
    assert qty_obj["exact"] == {"kind": "radical", "coefficient": "11250/697", "radicand": 2}
    assert sq_back == area_sq == Fraction(253125000, 485809)

    # Scan repository for any occurrence of the conversational error tokens
    bad_tokens = ["150062500", "819529", "8750*sqrt(1006)", "8750√1006"]
    bad_hits = []
    reconciliation_meta_files = {
        "reconcile_premerge_evidence.py",
        "premerge-evidence-reconciliation.json",
        "correction-addendum.md",
        "review-reconciliation.md",
        "handoff.md",
    }
    for path in list(RUN.rglob("*")) + [ROOT / "docs/CURRENT_STATE.md", ROOT / "docs/EVIDENCE_INDEX.md", ROOT / "docs/CODE_INDEX.md"]:
        if path.is_file() and path.suffix in {".md", ".json", ".py", ".log"}:
            if path.name in reconciliation_meta_files:
                continue
            txt = path.read_text(encoding="utf-8", errors="ignore")
            for tok in bad_tokens:
                if tok in txt:
                    bad_hits.append({"file": str(path.relative_to(ROOT)), "token": tok})
    for tok in bad_tokens:
        proc = subprocess.run(
            ["git", "grep", "-F", tok, PRE_RECON_HEAD_SHA],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            bad_hits.append({"file": f"{PRE_RECON_HEAD_SHA}:git-grep", "token": tok, "matches": proc.stdout.strip()})
    assert bad_hits == [], f"Unexpected hits of conversational error tokens in committed files: {bad_hits}"

    return {
        "case_id": "W2-A04",
        "oracle_expected_area_squared": e_a04["area_squared"],
        "independent_recomputed_area_squared": str(area_sq),
        "numerator_factorization": "253125000 = 2^3 * 3^4 * 5^8 = (2 * 3^2 * 5^4)^2 * 2 = 11250^2 * 2",
        "denominator_factorization": "485809 = 17^2 * 41^2 = 697^2",
        "unreduced_pq": pq,
        "unreduced_pq_factorization": "122970403125000 = (11250 * 697)^2 * 2 = 7841250^2 * 2",
        "canonical_radical": R.to_json(rad_val),
        "canonical_display": R.display(rad_val),
        "square_identity_verified": sq_back == area_sq,
        "edge_parameters": {
            "SB": str(t_SB),
            "SC": str(t_SC),
            "SD": str(t_SD),
        },
        "euclidean_intersection_points": {
            "M": [str(c) for c in M],
            "N": [str(c) for c in N],
            "P": [str(c) for c in P],
        },
        "product_route_status": route_res.status,
        "product_adapter4_status": a4_res["route_d"]["status"],
        "product_envelope_status": a4_res["envelope"]["status"],
        "product_final_memory_kq_mg1": R.to_json(kq_mg1),
        "product_answer_mg1": route_res.answers["mg1"],
        "product_scene3d_quantity_exact": qty_obj["exact"],
        "product_route_d_certificate_category": "DINH_CAT_CANH",
        "product_engine_section_certificate_area_squared": route_res.section_certificates[0]["closure_certificate"]["area_squared"],
        "erroneous_chat_summary_values_in_committed_repo_files": bad_hits,
        "finding_a_conclusion": (
            "ORACLE_PRODUCT_AND_RECOMPUTATION_AGREE_EXACTLY: area_squared = 253125000/485809 and "
            "area = 11250√2/697 across frozen Holdout Wave 2 oracle, product output, independent Fraction "
            "recomputation, and all committed W2-M4 JSON/Markdown files. The values 150062500/819529 and "
            "8750√1006/901 appeared exclusively in the post-compaction conversational chat summary and never "
            "entered any committed file. A minor intermediate prime-exponent typo in baseline-audit.md line 53 "
            "('2^3 * 3^4 * 5^7 = (2 * 3^2 * 5^3)^2 * 10 = 11250^2 * 2' instead of '2^3 * 3^4 * 5^8 = "
            "(2 * 3^2 * 5^4)^2 * 2 = 11250^2 * 2') is also documented in correction-addendum.md."
        ),
    }


def verify_finding_b_wave2_counts() -> dict:
    expected = json.loads(git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/oracle/expected.json").decode("utf-8"))
    sr1_ta = json.loads(git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/results/scored-run-1/track-a.json").decode("utf-8"))
    sr2_ta = json.loads(git_bytes("show", f"{HIST_W2_SHA}:{HIST_W2_DIR}/results/scored-run-2-harness-corrected/track-a.json").decode("utf-8"))
    sg_w2 = json.loads((SG_DIR / "results/wave2-post-feedback-regression.json").read_text(encoding="utf-8"))
    m4_w2 = json.loads((RUN / "results/wave2-post-feedback-regression.json").read_text(encoding="utf-8"))

    def summarize(cases: list[dict]) -> dict:
        pos = [c for c in cases if c["expected"] == "SERVE"]
        neg = [c for c in cases if c["expected"] != "SERVE"]
        pos_sc = [c["id"] for c in pos if c["outcome"] == "SERVED_CORRECT"]
        pos_ws = [c["id"] for c in pos if c["outcome"] == "WRONG_SERVED"]
        pos_fr = [c["id"] for c in pos if c["outcome"] == "FALSE_REFUSAL"]
        cat_b_pos = [c for c in pos if expected[c["id"]]["expected_certificate_category"] == "ENGINE_DERIVED_SECTION"]
        cat_a_pos = [c for c in pos if expected[c["id"]]["expected_certificate_category"] == "DINH_CAT_CANH"]
        cat_b_sc = [c["id"] for c in cat_b_pos if c["outcome"] == "SERVED_CORRECT"]
        cat_a_sc = [c["id"] for c in cat_a_pos if c["outcome"] == "SERVED_CORRECT"]
        neg_ref = [c["id"] for c in neg if not c["served"]]
        neg_rcr = [c["id"] for c in neg if c["outcome"] == "REFUSED_CORRECT_REASON"]
        neg_rrd = [c["id"] for c in neg if c["outcome"] == "REFUSED_REASON_DISAGREEMENT"]
        neg_ws = [c["id"] for c in neg if c["outcome"] == "WRONG_SERVED"]
        return {
            "total_cases": len(cases),
            "positive_total": len(pos),
            "positive_served_correct": f"{len(pos_sc)}/{len(pos)}",
            "positive_served_correct_ids": pos_sc,
            "positive_wrong_served": f"{len(pos_ws)}/{len(pos)}",
            "positive_wrong_served_ids": pos_ws,
            "positive_false_refusal": f"{len(pos_fr)}/{len(pos)}",
            "positive_false_refusal_ids": pos_fr,
            "category_b_served_correct": f"{len(cat_b_sc)}/{len(cat_b_pos)}",
            "category_b_served_correct_ids": cat_b_sc,
            "category_a_served_correct": f"{len(cat_a_sc)}/{len(cat_a_pos)}",
            "category_a_served_correct_ids": cat_a_sc,
            "negative_total": len(neg),
            "negative_refused": f"{len(neg_ref)}/{len(neg)}",
            "negative_refused_correct_reason": f"{len(neg_rcr)}/{len(neg)}",
            "negative_refused_reason_disagreement": f"{len(neg_rrd)}/{len(neg)}",
            "negative_wrong_served": f"{len(neg_ws)}/{len(neg)}",
        }

    s_sr1 = summarize(sr1_ta["cases"])
    s_sr2 = summarize(sr2_ta["cases"])
    s_sg = summarize(sg_w2["cases"])
    s_m4 = summarize(m4_w2["cases"])

    assert s_sr1["positive_served_correct"] == "3/48"
    assert s_sr1["category_b_served_correct"] == "3/36"
    assert s_sr1["category_a_served_correct"] == "0/12"
    assert s_sr1["positive_wrong_served"] == "2/48"

    assert s_sr2["positive_served_correct"] == "5/48"
    assert s_sr2["category_b_served_correct"] == "3/36"
    assert s_sr2["category_a_served_correct"] == "2/12"
    assert s_sr2["positive_wrong_served"] == "0/48"

    assert s_sg["positive_served_correct"] == "45/48"
    assert s_sg["category_b_served_correct"] == "36/36"
    assert s_sg["category_a_served_correct"] == "9/12"
    assert s_sg["positive_false_refusal_ids"] == ["W2-A04", "W2-A07", "W2-A10"]

    assert s_m4["positive_served_correct"] == "46/48"
    assert s_m4["category_b_served_correct"] == "36/36"
    assert s_m4["category_a_served_correct"] == "10/12"
    assert s_m4["positive_false_refusal_ids"] == ["W2-A07", "W2-A10"]

    return {
        "historical_scored_run_1_raw": s_sr1,
        "historical_scored_run_2_harness_corrected": s_sr2,
        "source_gate_19_post_feedback_regression": s_sg,
        "w2_m4_post_feedback_regression": s_m4,
        "reconciled_narrative_discrepancies": [
            {
                "id": "W2-M4-DOC-1",
                "location": "docs/evaluation/geometry/runs/hybrid-v2-w2-m4-exact-radical-normalization/report.md:77",
                "erroneous_statement": "historical Holdout Wave 2 raw score at d7a94d3c remains 37/48 positive SERVED_CORRECT, preserved unchanged",
                "verified_truth": (
                    "At historical Holdout Wave 2 baseline d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c "
                    "(commit ecdc26b012c8ce80d53524a98dc75cdcb020079d), raw scored-run-1 is 3/48 positive "
                    "SERVED_CORRECT (Category B 3/36: W2-B08, W2-B12, W2-B14; Category A 0/12; 2 harness-induced "
                    "false WRONG_SERVED on W2-A01, W2-A03; 43/48 FALSE_REFUSAL; 48/48 negatives refused; 33/48 "
                    "reason agreement), and harness-corrected adjudicated scored-run-2 is 5/48 positive "
                    "SERVED_CORRECT (Category B 3/36: W2-B08, W2-B12, W2-B14; Category A 2/12: W2-A01, W2-A03; "
                    "0/96 WRONG_SERVED; 43/48 FALSE_REFUSAL; 48/48 negatives refused; 33/48 reason agreement)."
                ),
            },
            {
                "id": "W2-M4-DOC-2",
                "location": "docs/evaluation/geometry/runs/hybrid-v2-w2-m4-exact-radical-normalization/report.md:79-80",
                "erroneous_statement": "Category B (ENGINE_DERIVED_SECTION): 36/36 SERVED_CORRECT (100.0%, up from 35/36). Category A (DINH_CAT_CANH): 10/12 SERVED_CORRECT (83.33%).",
                "verified_truth": (
                    "Because W2-A04 is a Category A (DINH_CAT_CANH, stratum P-A) case, Category B was already "
                    "36/36 (100.0%) at the Source Gate /19 baseline d99f6149 (up from 3/36 at historical Wave 2 "
                    "d7a94d3c) and remains 36/36 (100.0%) at W2-M4 051224ee. Category A (DINH_CAT_CANH) is the "
                    "stratum that increased from 9/12 (75.0%) at d99f6149 (and 0/12 raw / 2/12 adjudicated at "
                    "d7a94d3c) to 10/12 (83.33%) at W2-M4 051224ee when W2-A04 transitioned from FALSE_REFUSAL "
                    "to SERVED_CORRECT."
                ),
            },
        ],
    }


def verify_artifact_hashes_and_archival() -> dict:
    # Verify hashes of all W2-M4 artifacts
    scope_ev = json.loads((RUN / "verification/scope-and-evidence.json").read_text(encoding="utf-8"))
    t3_rec = json.loads((RUN / "verification/full-t3/receipt.json").read_text(encoding="utf-8"))

    artifact_hashes = {}
    for rel in [
        "inputs/development.json",
        "results/red-before.json",
        "results/green-after.json",
        "results/source-gate-regression.json",
        "results/wave2-post-feedback-regression.json",
        "candidate_divergence.json",
        "verification/scope-and-evidence.json",
        "verification/cache-and-fixtures.json",
        "verification/impact-plan.json",
        "verification/tiers.json",
        "verification/full-t3/receipt.json",
        "verification/full-t3/full-t3.log",
    ]:
        p = RUN / rel
        b = p.read_bytes()
        artifact_hashes[rel] = {
            "bytes": len(b),
            "sha256_raw": sha256_raw(b),
            "sha256_lf": sha256_lf(b),
        }

    for rel, expected_lf in scope_ev["locked_evidence_sha256_lf"].items():
        assert artifact_hashes[rel]["sha256_lf"] == expected_lf, f"LF hash mismatch on {rel}"

    assert artifact_hashes["verification/full-t3/full-t3.log"]["sha256_raw"] == t3_rec["log"]["sha256"]
    assert artifact_hashes["verification/full-t3/full-t3.log"]["bytes"] == t3_rec["log"]["bytes"]

    # Verify that results/*.json were committed in 051224ee (whose parent is 14bc010e)
    parent_of_0512 = git_out("rev-parse", f"{PRODUCT_SHA}^")
    assert parent_of_0512 == FIRST_ATTEMPT_CANDIDATE_SHA
    green_json = json.loads((RUN / "results/green-after.json").read_text(encoding="utf-8"))
    assert green_json["head"] == FIRST_ATTEMPT_CANDIDATE_SHA
    recorded_diff_sha256 = green_json["product_diff_sha256"]

    # Verify Holdout Wave 2 branch path disjointness for safe integration
    w2_changed_files = git_out("diff", "--name-only", f"{MAIN_SHA}..{HIST_W2_SHA}").splitlines()
    m4_changed_files = git_out("diff", "--name-only", f"{MAIN_SHA}..{PRE_RECON_HEAD_SHA}").splitlines()
    overlap = sorted(set(w2_changed_files) & set(m4_changed_files))
    assert overlap == [], f"Unexpected file overlap between Holdout Wave 2 and W2-M4 branches: {overlap}"
    assert len(w2_changed_files) == 34
    assert all(f.startswith(f"{HIST_W2_DIR}/") for f in w2_changed_files)

    return {
        "w2_m4_artifact_hashes": artifact_hashes,
        "scope_and_evidence_lf_locks_verified": True,
        "t3_log_hash_and_size_verified": True,
        "result_json_recording_provenance": {
            "committed_in_product_commit": PRODUCT_SHA,
            "parent_commit_at_generation_time": FIRST_ATTEMPT_CANDIDATE_SHA,
            "recorded_head_in_results_json": FIRST_ATTEMPT_CANDIDATE_SHA,
            "recorded_working_tree_product_diff_sha256": recorded_diff_sha256,
            "explanation": (
                "results/green-after.json, results/source-gate-regression.json, and "
                "results/wave2-post-feedback-regression.json were generated on the working tree of product "
                "commit 051224ee2740cbf5d55dd94633503db1f0050ada immediately before committing 051224ee on "
                "top of parent commit 14bc010e4b4af2bb324c63e309d41c5c5847a904; `git rev-parse HEAD` inside "
                "the evaluation scripts therefore recorded the parent SHA 14bc010e4b4af2bb324c63e309d41c5c5847a904 "
                "and the working-tree `git diff -- backend/app` SHA-256 "
                "c730cb94bbd50e557b8d8283c8f73c741d90f32b84576fb954538de07696e147."
            ),
        },
        "holdout_wave2_archival_audit": {
            "holdout_wave2_branch": "research/hybrid-v2-independent-vietnamese-section-holdout-wave2",
            "holdout_wave2_head": HIST_W2_SHA,
            "holdout_wave2_commits_from_main": [
                "5e329d75 (docs(evaluation): preregister Hybrid V2 Holdout Wave 2 and verified scorer before corpus curation)",
                "7e5c3ddd (docs(evaluation): freeze Wave 2 independent holdout corpus, oracle, audits, and manifest before execution)",
                "ecdc26b0 (docs(eval): complete Wave 2 independent section holdout scored run, harness adjudication, diagnostics, and review)",
            ],
            "holdout_wave2_file_count": len(w2_changed_files),
            "overlap_with_product_repair_branch": overlap,
            "path_disjoint_verified": len(overlap) == 0,
        },
    }


def main() -> None:
    report = {
        "schema": "w2-m4-premerge-evidence-reconciliation/1",
        "task": "HYBRID_V2_W2_M4_PREMERGE_EVIDENCE_RECONCILIATION",
        "status": "PREMERGE_EVIDENCE_RECONCILED_READY_FOR_OWNER_GO",
        "live_provider_calls": 0,
        "git_and_freeze_verification": verify_git_and_freeze(),
        "finding_a_w2_a04_adjudication": verify_finding_a_w2_a04(),
        "finding_b_wave2_historical_counts": verify_finding_b_wave2_counts(),
        "integrity_and_archival_checks": verify_artifact_hashes_and_archival(),
    }
    out_path = RUN / "results/premerge-evidence-reconciliation.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {out_path.relative_to(ROOT)} SUCCESSFULLY")


if __name__ == "__main__":
    main()
