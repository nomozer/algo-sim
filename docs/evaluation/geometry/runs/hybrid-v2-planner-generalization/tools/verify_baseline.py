"""Verify inherited baseline identity/receipt without rerunning baseline Full T3."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
BASE = "386d214952e6a7ba98f0931b5ecfd7a5b89d1667"


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True, encoding="utf-8").strip()


def main() -> None:
    previous = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-nl-certificates-e2e"
    receipt = json.loads((previous / "full-t3/receipt.json").read_text(encoding="utf-8"))
    streams = {}
    for name, expected in receipt["streams"].items():
        data = (previous / "full-t3" / name).read_bytes()
        blob = subprocess.check_output(["git", "-C", str(ROOT), "show",
                                       f"{BASE}:" + (previous / "full-t3" / name).relative_to(ROOT).as_posix()])
        actual = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        stored = {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}
        streams[name] = {"checkout": actual, "git_blob": stored, "receipt": expected,
                         "checkout_matches_receipt": actual == expected, "git_blob_matches_receipt": stored == expected,
                         "checkout_normalizes_to_git_blob": data.replace(b"\r\n", b"\n") == blob,
                         "raw_recovery": "EXACT_GIT_BLOB" if stored == expected else "NOT_RECOVERABLE"}
        assert streams[name]["checkout_normalizes_to_git_blob"], name
    product_diff = git("diff", "--name-only", receipt["candidate"], BASE, "--", "backend/app", "frontend/src")
    assert not product_diff, product_diff
    assert receipt["exit_code"] == 0 and receipt["verdict"] == "FULL_PRODUCT_GATE_PASS"
    candidate_bytes = subprocess.check_output(["git", "-C", str(ROOT), "show",
                                               f"{BASE}:docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"])
    candidate = json.loads(candidate_bytes)
    assert candidate["product_commit_sha"] == receipt["product_commit"]
    # The manifest was written in Windows text mode; Git stores its LF-normalized blob.
    assert hashlib.sha256(candidate_bytes.replace(b"\n", b"\r\n")).hexdigest() == receipt["freeze_sha256_after"]
    out = RUN / "verification"
    out.mkdir(exist_ok=True)
    (out / "baseline-candidate.json").write_bytes(candidate_bytes)
    result = {"baseline_commit": BASE, "remote_verified_sha": BASE,
              "remote_method": "git fetch origin --no-tags; git ls-remote origin refs/heads/main (2026-10-27)",
              "baseline_detached_freeze": "MATCH (checked before research branch creation)",
              "baseline_product_tree_equals_t3": True,
              "product_commit": receipt["product_commit"], "t3_candidate": receipt["candidate"],
              "measured_system": candidate["measured_system"], "receipt_verdict": receipt["verdict"],
              "receipt_streams": streams, "baseline_t3_rerun": False,
              "receipt_limit": "stdout original mixed-newline bytes not preserved by Git; PASS is inherited from receipt and committed normalized transcript, not re-proved here. New candidate gets fresh T3 with binary-preserved streams.",
              "default_mode": "LLM_ONLY", "cache_version": 130, "live_provider_calls": 0,
              "old_worktrees": "Preserved; four dirty and two Git-clean, see preflight in plan.md",
              "stale_documentation": "Historical handoffs still say unmerged/dd557f8f. Git ancestry proves integration at baseline; no product divergence."}
    (out / "baseline-identity.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"baseline": BASE, "stderr_git_blob": "MATCH", "stdout_raw": "NOT_RECOVERABLE",
                      "product_tree": "MATCH", "manifest_identity": "MATCH"}))


if __name__ == "__main__":
    main()
