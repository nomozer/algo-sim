"""Gate 0 baseline integrity (from Git objects) and the candidate-freeze record (identity, tools, models, inputs).
Reads only; writes baseline_integrity.json and candidate_freeze.json.  Run from backend/.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
START = "44807b13bffe608153bc58e453a3bc9c37703485"
SEALED = "70b22cc7167d8e2372d606547c3e398b199fb101"
CANDIDATE = "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8", "replace").strip()


def ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT).returncode == 0


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    at_start = json.loads(git("show", f"{START}:{CANDIDATE}"))
    current = json.loads((ROOT / CANDIDATE).read_text(encoding="utf-8"))
    product_paths = ["backend/app", "frontend/src"]
    (RUN / "baseline_integrity.json").write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": now, "start_head": START,
        "start_head_is_ancestor_of_head": ancestor(START, "HEAD"), "sealed_candidate_is_ancestor_of_start": ancestor(SEALED, START),
        "candidate_at_start": {"commit": at_start["commit"], "product_commit": at_start["product_commit_sha"],
                               "measured_system": at_start["measured_system"]["tree_hash"], "files": at_start["measured_system"]["so_file"],
                               "cache_version": at_start["cache_version"]},
        "handoff_values_match": {"product_commit": at_start["product_commit_sha"] == "7b170021451a86c56a2eebadcdd0f0f088fcc229",
                                 "measured_system": at_start["measured_system"]["tree_hash"] == "a068b6f6586c1b120bd8350dbe706f5681ab71fd7da57502c34f940140268921",
                                 "files": at_start["measured_system"]["so_file"] == 115, "cache_version": at_start["cache_version"] == "132"},
        "start_verification_observed": "At session start (2026-11-12 19:05 local) `freeze_evaluation_candidate.py --verify` printed a match for 115 files a068b6f6586c1b12; the tree had no tracked changes (root-repo untracked ocr_reconcile.py is outside this worktree).",
        "product_changes_since_start": git("diff", "--stat", START, "HEAD", "--", *product_paths).splitlines()[-1:] or ["none"],
        "commits_since_start": git("log", "--format=%h %s", f"{START}..HEAD").splitlines(),
        "prior_regression_at_start": {"backend": "14259 passed, 7 skipped, 3 deselected, 15 xfailed", "frontend": "2018 passed",
                                      "publication_head": "97 pending, BLOCKED", "overall": "BLOCKED_GATES_REMAIN",
                                      "source": "real-image-ocr-vision-comparative-acceptance/full_regression_summary.json (not re-used as this run's result)"}},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ocr_python = ROOT / ".superpowers/ocr-venv/Scripts/python.exe"
    probe = subprocess.run([str(ocr_python), "-c", "import json, rapidocr, tesserocr, onnxruntime, PIL; print(json.dumps({'rapidocr': getattr(rapidocr, '__version__', 'UNKNOWN'), 'tesseract': tesserocr.tesseract_version().splitlines()[0], 'tesserocr': tesserocr.__version__, 'onnxruntime': onnxruntime.__version__, 'pillow': PIL.__version__}))"],
                           capture_output=True, text=True)
    tessdata = ROOT / ".superpowers/tessdata_fast/vie.traineddata"
    manifest = RUN / "new_in_scope_image_manifest.json"
    (RUN / "candidate_freeze.json").write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": now, "head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "candidate_file": CANDIDATE, "freeze_commit": current["commit"], "product_commit": current["product_commit_sha"],
        "measured_system": current["measured_system"], "cache_version": current["cache_version"],
        "contracts_unchanged": ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2", "output-policy/1"],
        "frozen_working_tree_clean": current["cay_lam_viec_sach"],
        "verify_command": "cd backend && python scripts/freeze_evaluation_candidate.py --verify",
        "test_commands": ["python -m pytest -c backend/pytest.ini backend/tests -q", "npm run test:wave (vitest run && tsc -b && vite build)",
                          "backend/scripts/replay_demo_cases.py --json", "backend/scripts/audit_demo_crash_surface.py --json",
                          "backend/scripts/audit_docs_information_architecture.py --json", "backend/scripts/check_publication_safety.py --head | --range",
                          "backend/scripts/freeze_evaluation_candidate.py --verify"],
        "tool_versions": {"python_backend": sys.version.split()[0], "node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
                          "ocr_interpreter": json.loads(probe.stdout) if probe.returncode == 0 else f"UNKNOWN ({probe.returncode})"},
        "ocr_models": {"tesseract_lang": "vie (tessdata_fast)", "vie_traineddata_sha256": hashlib.sha256(tessdata.read_bytes()).hexdigest() if tessdata.exists() else "UNKNOWN",
                       "rapidocr_models": "PP-OCRv6 det/rec small (package default); reread: PP-OCRv5 Latin mobile rec + Tesseract eng single line"},
        "evaluation_inputs": {"manifest": manifest.relative_to(ROOT).as_posix(), "manifest_sha256_lf": hashlib.sha256(manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                              "images": 25, "ground_truth": "AGENT_TRANSCRIBED_UNVERIFIED", "images_in_git": False},
        "known_limitations": ["one dataset of rendered crops; no photos, handwriting or multi-problem pages", "agent references; no H-1",
                              "no live Vision", "no real students", "SQLite only; 8 simultaneous new-session uploads produced SQLITE_BUSY failures",
                              "publication HEAD blocked pending Owner decision"],
        "merge_push_deploy": "NOT_PERFORMED"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("baseline match:", all(json.loads((RUN / "baseline_integrity.json").read_text(encoding="utf-8"))["handoff_values_match"].values()), "| probe:", probe.stdout.strip()[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
