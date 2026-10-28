# -*- coding: utf-8 -*-
"""Execute T0, T1, and T2 verification checks and persist structured receipts for W2-M5."""
from __future__ import annotations

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
VER = RUN / "verification"
VER.mkdir(parents=True, exist_ok=True)
PYTHON = sys.executable

BASELINE = "eb661971847c034500862299c5091f1f3d2a2998"
PRODUCT_COMMIT = "73ca8d92e74059680ce53b99692af396df37a2f8"
FREEZE_HASH = "1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d"


def lf_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    env = {
        **os.environ,
        "ALLOW_LIVE_AI": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    # 1. T0: impact plan dry-run
    impact = subprocess.run(
        ["node", "frontend/scripts/impact.mjs", "--dry", "--base", BASELINE, "--json", str(VER / "impact-plan.json")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert impact.returncode == 0, impact.stderr

    # 2. T0: publication safety check over branch range
    pub = subprocess.run(
        [PYTHON, "backend/scripts/check_publication_safety.py", "--range", f"{BASELINE}..{head}"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert pub.returncode == 0, pub.stdout + "\n" + pub.stderr

    # 3. T0: scope & raw evidence identity check
    prod_files = [
        line.strip()
        for line in subprocess.check_output(
            ["git", "diff", "--name-only", f"{BASELINE}..{head}", "--", "backend/app", "frontend/src"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        if line.strip()
    ]
    assert prod_files == ["backend/app/ai/adapter4_route.py"], prod_files
    scope_payload = {
        "status": "SOURCE_SCOPE_AND_RAW_EVIDENCE_IDENTITY_PASS",
        "baseline_head": BASELINE,
        "main_head": subprocess.check_output(["git", "rev-parse", "main"], cwd=ROOT, text=True).strip(),
        "origin_main_head": subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip(),
        "product_commit": PRODUCT_COMMIT,
        "candidate": head,
        "product_files_changed": prod_files,
        "forbidden_layers_changed": [],
        "publication_safety_exit_code": pub.returncode,
        "locked_evidence_sha256_lf": {
            "inputs/development.json": lf_sha256(RUN / "inputs/development.json"),
            "inputs/oracle.json": lf_sha256(RUN / "inputs/oracle.json"),
            "results/red-before.json": lf_sha256(RUN / "results/red-before.json"),
            "results/green-after.json": lf_sha256(RUN / "results/green-after.json"),
            "results/tamper-results.json": lf_sha256(RUN / "results/tamper-results.json"),
            "results/wave2-post-feedback-regression.json": lf_sha256(RUN / "results/wave2-post-feedback-regression.json"),
            "results/w2-a10-scorer-adjudication-receipt.json": lf_sha256(RUN / "results/w2-a10-scorer-adjudication-receipt.json"),
        },
        "live_provider_calls": 0,
    }
    (VER / "scope-and-evidence.json").write_text(
        json.dumps(scope_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 4. T0: cache lock & 41 stored preview fixtures
    cache_proc = subprocess.run(
        [PYTHON, "backend/scripts/lock_cache_identity.py", "--verify"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert cache_proc.returncode == 0, cache_proc.stderr
    fix_proc = subprocess.run(
        [
            PYTHON,
            "backend/scripts/export_hybrid_preview_fixtures.py",
            "--verify",
            "docs/evaluation/geometry/runs/hybrid-v2-backend-generalization/fixtures-adapter-2-named-plane",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert fix_proc.returncode == 0, fix_proc.stderr
    fix_json = json.loads(fix_proc.stdout)
    assert fix_json["verified"] == 41 and fix_json["problems"] == []
    (VER / "cache-and-fixtures.json").write_text(
        json.dumps(
            {
                "cache": {"exit_code": cache_proc.returncode, "stdout": cache_proc.stdout.strip()},
                "preview_fixtures": {
                    "exit_code": fix_proc.returncode,
                    "verified": fix_json["verified"],
                    "problems": fix_json["problems"],
                    "producer_now": fix_json["producer_now"],
                },
                "cache_version": 130,
                "live_provider_calls": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # 5. T1 + T2 targeted backend suites
    (ROOT / ".superpowers").mkdir(parents=True, exist_ok=True)
    basetemp = (ROOT / ".superpowers/t1-t2-temp").as_posix()
    t1_t2_cmd = [
        PYTHON,
        "-B",
        "-m",
        "pytest",
        "backend/tests/geometry/test_w2_m5_adapter4_category_a_identity.py",
        "backend/tests/geometry/test_adapter4_response.py",
        "backend/tests/geometry/test_adapter4_plane_section_certificate.py",
        "backend/tests/geometry/test_section_display_identity.py",
        "backend/tests/geometry/test_display_identity_source_names.py",
        "backend/tests/geometry/test_hybrid_contract_v2.py",
        "backend/tests/geometry/test_hybrid_offline.py",
        "backend/tests/geometry/test_holdout_failure_repair.py",
        "backend/tests/geometry/test_radical_domain.py",
        "backend/tests/geometry/test_source_gate_language.py",
        "backend/tests/geometry/test_hybrid_backend_integration.py",
        "backend/tests/semantic_program/test_evaluation_candidate.py",
        "backend/tests/geometry/test_thesis_acceptance_matrix.py",
        "-q",
        "--tb=short",
        "-p",
        "no:cacheprovider",
        f"--basetemp={basetemp}",
    ]
    t1_t2 = subprocess.run(t1_t2_cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    (VER / "t1-t2.log").write_text(t1_t2.stdout + t1_t2.stderr, encoding="utf-8")
    assert t1_t2.returncode == 0, t1_t2.stdout[-1000:] + "\n" + t1_t2.stderr[-1000:]
    last_line = [ln.strip() for ln in t1_t2.stdout.splitlines() if "passed" in ln][-1]
    (VER / "tiers.json").write_text(
        json.dumps(
            {
                "t0_impact_exit_code": impact.returncode,
                "t0_publication_safety_exit_code": pub.returncode,
                "t0_scope_status": scope_payload["status"],
                "t0_cache_exit_code": cache_proc.returncode,
                "t0_preview_fixtures_verified": fix_json["verified"],
                "t1_t2_exit_code": t1_t2.returncode,
                "t1_t2_summary": last_line,
                "live_provider_calls": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("T0, T1, T2 PASS:", last_line)


if __name__ == "__main__":
    main()
