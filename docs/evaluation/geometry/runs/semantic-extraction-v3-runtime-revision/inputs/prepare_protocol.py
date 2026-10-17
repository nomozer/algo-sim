"""One-time runtime revision lock; reuse parent data/oracle and existing review/identity helpers without rewriting them."""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = HERE.parents[5]
PARENT = RUN.parent / "semantic-extraction-schema-contract"
sys.path.insert(0, str(ROOT / "backend"))
from scripts import run_schema_contract_evaluation as R
from scripts.freeze_evaluation_candidate import measured_system_hash, _measured_system_files

spec = importlib.util.spec_from_file_location("parent_protocol_helpers", PARENT / "inputs/prepare_protocol.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
REQUIRED = {"backend/app/simulation/geometry_functions/registry.py", "backend/scripts/run_schema_contract_evaluation.py",
            "backend/scripts/run_schema_contract_offline.py", (HERE / "prepare_protocol.py").relative_to(ROOT).as_posix()}


def prepare(lock=False):
    previous = P.read(HERE / "protocol.json") if (HERE / "protocol.json").exists() else {}
    P.require_unlocked(previous)
    parent = P.read(PARENT / "inputs/protocol.json")
    parent_hash = R.V1._sha(parent)
    if parent["lock_status"] != "LOCKED" or previous and previous["parent_protocol_sha256"] != parent_hash:
        raise SystemExit("PARENT_PROTOCOL_CHANGED")
    # Validate preserved parent data/reports and source hashes, not its old product against the corrected product.
    for path, want in parent["file_sha256"].items():
        f = (PARENT / "inputs" / path).resolve()
        if f.is_relative_to(PARENT.resolve()) and P.lf_sha(f) != want:
            raise SystemExit("PARENT_EVIDENCE_MUTATED")
    if P.source_hashes() != parent["source_sha256"]:
        raise SystemExit("PARENT_SOURCE_MUTATED")
    for name in ("corpus.json", "gold_facts.json"):
        source, target = PARENT / "inputs" / name, HERE / name
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise SystemExit("REVISION_DATA_MUTATED")
        if not target.exists():
            target.write_bytes(source.read_bytes())
    # These frozen scorer/executor/helper files have no changes in this revision.
    for name in ("run_semantic_extraction_evaluation.py", "run_nlu_extraction_evaluation.py", "run_hybrid_ab_pilot.py"):
        f = ROOT / "backend/scripts" / name
        key = os.path.relpath(f, PARENT / "inputs").replace("\\", "/")
        if P.lf_sha(f) != parent["file_sha256"][key]:
            raise SystemExit("SCORER_OR_EXECUTOR_CHANGED")
    from app.ai import fact_extraction as fx
    old_ids = P.read(PARENT / "approval-identities.json")["identities"]
    if any(fx.surface_fingerprint(arm) != old_ids[arm + "-PILOT"]["surface_sha256"] for arm in R.ARMS):
        raise SystemExit("PROMPT_OR_SCHEMA_CHANGED")
    product, count = measured_system_hash()
    gate = P.check_gate(RUN / "review-gates/revision.json", REQUIRED)
    candidate_path = ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"
    candidate = P.read(candidate_path)
    matched = candidate["measured_system"]["tree_hash"] == product and candidate["measured_system"]["so_file"] == count
    reviewed = gate["status"] == "PASS" and gate.get("product_sha256") == product
    if lock and not (matched and reviewed):
        raise SystemExit("LOCK_PREREQUISITES_NOT_PASS")
    protocol = {**parent, "schema": "semantic-extraction-protocol/3-runtime-revision/1",
                "lock_status": "LOCKED" if lock else "NOT_LOCKED", "live_authorizable": bool(lock),
                "parent_protocol_sha256": parent_hash, "revision": "runtime-and-split-isolation/1",
                "parent_review_gates": parent["review_gates"], "review_gates": {"revision": gate},
                "frozen_candidate": {"status": "MATCH" if matched else "NOT_MATCHED", "product_sha256": product, "files": count},
                "heldout_status": "REUSED_DIAGNOSTIC_NOT_FRESH_BLIND", "offline_watchdog_seconds": 120}
    files = [f for f in (PARENT / "inputs").rglob("*") if f.is_file() and "__pycache__" not in f.parts]
    files += [ROOT / f for f in parent["source_sha256"]]
    files += [f for f in HERE.iterdir() if f.is_file() and f.name != "protocol.json"]
    files += [PARENT / "preregistration.md", RUN / "preregistration.md"]
    files += [ROOT / g["path"] for g in parent["review_gates"].values()]
    files += [ROOT / "backend/scripts" / n for n in ("run_schema_contract_evaluation.py", "run_schema_contract_offline.py",
               "run_semantic_extraction_evaluation.py", "run_nlu_extraction_evaluation.py", "run_hybrid_ab_pilot.py",
               "freeze_evaluation_candidate.py")]
    if lock:
        files += _measured_system_files() + [candidate_path, RUN / "review-gates/revision.json"]
        files += [ROOT / f for f in P.read(RUN / "review-gates/revision.json")["reviewed_sha256"]]
    protocol["file_sha256"] = {os.path.relpath(f, HERE).replace("\\", "/"): P.lf_sha(f) for f in sorted(set(files))}
    if "ABSENT" in protocol["file_sha256"].values():
        raise SystemExit("BOUND_FILE_ABSENT")
    subprocess.run([sys.executable, "-B", str(HERE / "oracle.py")], check=True, capture_output=True)
    P.write(HERE / "protocol.json", protocol)
    R.E.load_inputs(HERE)
    print({"lock_status": protocol["lock_status"], "product_sha256": product, "protocol_sha256": R.V1._sha(protocol),
           "review": gate["status"], "parent_protocol_sha256": parent_hash})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    prepare(lock=args.lock)
