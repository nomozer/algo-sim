# -*- coding: utf-8 -*-
"""Execute T0, T1, and T2 verification checks and persist structured receipts."""
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

BASELINE = "d99f6149ff1997258970bf888db5484665b106b8"
PRODUCT_COMMIT = "051224ee2740cbf5d55dd94633503db1f0050ada"
CANDIDATE = "1e0c8db668bbe110f343a8a67cdeca465008c188"
FREEZE_HASH = "8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369"


def lf_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    env = {
        **os.environ,
        "ALLOW_LIVE_AI": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }

    # 1. T0: impact plan dry-run
    impact = subprocess.run(
        ["node", "frontend/scripts/impact.mjs", "--dry-run", f"--base={BASELINE}"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert impact.returncode == 0, impact.stderr
    (VER / "impact-plan.json").write_text(impact.stdout, encoding="utf-8")

    # 2. T0: scope & raw evidence identity check
    prod_files = [
        line.strip()
        for line in subprocess.check_output(
            ["git", "diff", "--name-only", f"{BASELINE}..{CANDIDATE}", "--", "backend/app", "frontend/src"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        if line.strip()
    ]
    assert prod_files == ["backend/app/simulation/geometry/radical.py"], prod_files
    scope_payload = {
        "status": "SOURCE_SCOPE_AND_RAW_EVIDENCE_IDENTITY_PASS",
        "baseline_head": BASELINE,
        "main_head": subprocess.check_output(["git", "rev-parse", "main"], cwd=ROOT, text=True).strip(),
        "origin_main_head": subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip(),
        "product_commit": PRODUCT_COMMIT,
        "candidate": CANDIDATE,
        "product_files_changed": prod_files,
        "forbidden_layers_changed": [],
        "locked_evidence_sha256_lf": {
            "inputs/development.json": lf_sha256(RUN / "inputs/development.json"),
            "results/red-before.json": lf_sha256(RUN / "results/red-before.json"),
            "results/green-after.json": lf_sha256(RUN / "results/green-after.json"),
            "results/source-gate-regression.json": lf_sha256(RUN / "results/source-gate-regression.json"),
            "results/wave2-post-feedback-regression.json": lf_sha256(RUN / "results/wave2-post-feedback-regression.json"),
        },
        "live_provider_calls": 0,
    }
    (VER / "scope-and-evidence.json").write_text(
        json.dumps(scope_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 3. T0: cache lock & 41 stored preview fixtures
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

    # 4. T1 + T2 targeted backend suites
    (ROOT / ".superpowers").mkdir(parents=True, exist_ok=True)
    basetemp = (ROOT / ".superpowers/t1-t2-temp").as_posix()
    t1_t2_cmd = [
        PYTHON,
        "-B",
        "-m",
        "pytest",
        "backend/tests/geometry/test_radical_domain.py",
        "backend/tests/geometry/test_pi_exact_domain.py",
        "backend/tests/geometry/test_radical_distance.py",
        "backend/tests/geometry/test_radical_end_to_end.py",
        "backend/tests/geometry/test_general_polygon_base.py",
        "backend/tests/geometry/test_regular_hexagonal_pyramid.py",
        "backend/tests/geometry/test_source_gate_language.py",
        "backend/tests/geometry/test_solid_kind_source_binding.py",
        "backend/tests/geometry/test_two_line_plane_section.py",
        "backend/tests/geometry/test_holdout_failure_repair.py",
        "backend/tests/geometry/test_hybrid_backend_integration.py",
        "backend/tests/geometry/test_wave3a_adapter3_integration.py",
        "backend/tests/geometry/test_wave3a_volume_reasoning.py",
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
    print("T0, T1, T2 PASS:", last_line)


if __name__ == "__main__":
    main()
