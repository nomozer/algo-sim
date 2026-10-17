"""Lossless offline assembly and one-time review-gated lock. Never writes approval or author files.

--prepare may refresh a draft after source review; original data hashes cannot change.
--lock additionally requires current independent reviews and a matching frozen candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
RUN = HERE.parent
OLD = RUN.parent / "hybrid-semantic-extraction-v2/inputs"
sys.path.insert(0, str(ROOT / "backend"))
from scripts import run_semantic_extraction_evaluation as E

SOURCE_PATHS = [OLD / n for n in ("corpus.json", "gold_facts.json", "oracle.py", "authoring.md", "prelock_corrections.json")]
SOURCE_PATHS += [HERE / "heldout" / n for n in ("corpus.json", "gold_facts.json", "oracle.py", "authoring.md", "gold_encoding.md")]
GATE_REQUIRED = {
    "gold-oracle": {str((HERE / "heldout" / n).relative_to(ROOT).as_posix()) for n in ("corpus.json", "gold_facts.json", "oracle.py")},
    "scorer": {"backend/scripts/run_semantic_extraction_evaluation.py", "backend/scripts/run_schema_contract_evaluation.py"},
    "candidate": {"backend/app/ai/fact_extraction.py", "backend/app/simulation/geometry_functions/registry.py"},
}
CANDIDATE = ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lf_sha(path):
    return E.V1._lf_sha(path)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def source_hashes():
    return {p.relative_to(ROOT).as_posix(): lf_sha(p) for p in SOURCE_PATHS}


def assemble():
    old, fresh = read(OLD / "corpus.json"), read(HERE / "heldout/corpus.json")
    dev = [c for c in old["cases"] if c["split"] == "dev"]
    held = fresh["cases"]
    assert len(dev) == 12 and len(held) == 24
    assert all(c["split"] == "heldout" for c in held)
    cases = dev + held
    assert len({c["id"] for c in cases}) == 36
    families = {}
    for c in cases:
        assert families.setdefault(c["structure_id"], c["split"]) == c["split"], "SPLIT_FAMILY_LEAK"
    old_gold = read(OLD / "gold_facts.json")["cases"]
    gold = {**{c["id"]: old_gold[c["id"]] for c in dev}, **read(HERE / "heldout/gold_facts.json")["cases"]}
    return {"schema": "semantic-extraction-corpus/2", "independence": "MIXED_EXPOSED_DEVELOPMENT_AND_FRESH_AI_AUTHORED_HELDOUT_NOT_HUMAN_VALIDATED", "cases": cases}, {"cases": gold}


def require_unlocked(protocol):
    if protocol.get("lock_status") == "LOCKED":
        raise SystemExit("ALREADY_LOCKED")


def check_gate(path, required, root=ROOT):
    if not path.exists():
        return {"status": "MISSING"}
    gate = read(path)
    hashes = gate.get("reviewed_sha256", {})
    if gate.get("status") != "PASS" or not gate.get("reviewer"):
        return {"status": "NOT_PASS"}
    if not required <= set(hashes):
        return {"status": "INCOMPLETE_COVERAGE"}
    if any(not (root / p).resolve().is_relative_to(root.resolve()) or lf_sha(root / p) != h or h == "ABSENT" for p, h in hashes.items()):
        return {"status": "STALE_REVIEW"}
    return {"status": "PASS", "path": os.path.relpath(path, root).replace("\\", "/"), "sha256": lf_sha(path),
            "reviewer": gate["reviewer"], **({"product_sha256": gate["product_sha256"]} if "product_sha256" in gate else {})}


def prepare(lock=False):
    previous = read(HERE / "protocol.json") if (HERE / "protocol.json").exists() else {}
    require_unlocked(previous)
    original = source_hashes()
    if previous and previous.get("source_sha256") != original:
        raise SystemExit("SOURCE_MUTATION_REQUIRES_NEW_RUN")
    corpus, gold = assemble()
    for name, value in (("corpus", corpus), ("gold_facts", gold)):
        path = HERE / (name + ".json")
        if path.exists() and read(path) != value:
            raise SystemExit("ASSEMBLED_DATA_MUTATION")
    # Only the development portion of the historical author oracle is copied. It has no author entry point.
    original_oracle = (OLD / "oracle.py").read_text(encoding="utf-8")
    dev_oracle = original_oracle[:original_oracle.index("# Heldout family H1:")].rstrip("\n") + "\n"
    (HERE / "exposed_dev_oracle.py").write_text(dev_oracle, encoding="utf-8", newline="\n")
    write(HERE / "corpus.json", corpus)
    write(HERE / "gold_facts.json", gold)
    from scripts.freeze_evaluation_candidate import measured_system_hash
    product, count = measured_system_hash()
    gates = {name: check_gate(RUN / "review-gates" / (name + ".json"), required) for name, required in GATE_REQUIRED.items()}
    candidate = read(CANDIDATE) if CANDIDATE.exists() else {}
    candidate_ok = (candidate.get("measured_system", {}).get("tree_hash") == product
                    and candidate.get("measured_system", {}).get("so_file") == count
                    and gates["candidate"].get("product_sha256") == product)
    if lock and (any(g["status"] != "PASS" for g in gates.values()) or not candidate_ok):
        raise SystemExit("LOCK_PREREQUISITES_NOT_PASS")
    write(HERE / "provenance.json", {
        "development": {"status": "EXPOSED_DEVELOPMENT_REUSED_NOT_FRESH_EVALUATION", "cases": 12,
                        "source_run": "hybrid-semantic-extraction-v2", "semantic_changes": 0,
                        "oracle_derivation": "Exact source prefix before # Heldout family H1:; no author or historical heldout code copied."},
        "heldout": {"status": "FRESH_INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED", "cases": 24,
                    "source_directory": "heldout", "semantic_changes": 0,
                    "limitations": "See preserved authoring.md and gold_encoding.md; gold encoder received oracle and limited planner code, and disclosed prior structural communications."},
        "assembly": "Concatenation of original dev case objects plus original heldout case objects; matching gold objects copied without semantic edits.",
        "source_sha256": original})
    protocol = {
        "schema": "semantic-extraction-protocol/3", "model": "gemini-2.5-flash", "scorer": E.SCORER_VERSION,
        "lock_status": "LOCKED" if lock else "NOT_LOCKED", "live_authorizable": bool(lock),
        "locked_sha256": {"corpus": E.V1._sha(corpus), "gold_facts": E.V1._sha(gold)},
        "source_sha256": original, "review_gates": gates,
        "frozen_candidate": {"status": "MATCH" if candidate_ok else "NOT_MATCHED", "product_sha256": product, "files": count},
        "caps": {"PILOT": {"logical_calls": 12, "http_attempts": 12, "accounted_tokens": 400000, "usd": .50, "samples": 1},
                 "LOCKED": {"logical_calls": 24, "http_attempts": 24, "accounted_tokens": 800000, "usd": 1.00, "samples": 1}},
        "arms": ["flat", "v3"], "retries": 0, "timeout_seconds": 90,
        "pilot_total_calls": 24, "pilot_total_usd_cap": 1.0, "locked_total_calls": 48, "locked_total_usd_cap": 2.0,
        "thresholds": {"unsafe_serves_max": 0, "unscorable_serves_max": 0, "goal_entity_recall_min": .85,
                       "operand_correct_min": .85, "solid_ownership_min": .85, "hallucinated_entity_rows_max": 0},
        "descriptive_only": ["multi_goal", "unsupported", "correlated_structure_families"],
        "human_validation": "NOT_HUMAN_VALIDATED", "live_decision": "PENDING_EXACT_IDENTITY_OWNER_GO" if lock else "NOT_AUTHORIZABLE_DRAFT",
        "integration_decision": "PENDING_SEPARATE_OWNER_GO",
    }
    files = [p for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "protocol.json"]
    files += SOURCE_PATHS + [RUN / "preregistration.md"]
    files += [ROOT / "backend/scripts" / n for n in ("run_schema_contract_evaluation.py", "run_semantic_extraction_evaluation.py", "run_nlu_extraction_evaluation.py", "run_hybrid_ab_pilot.py", "freeze_evaluation_candidate.py")]
    if lock:
        files += [CANDIDATE] + [RUN / "review-gates" / (n + ".json") for n in GATE_REQUIRED]
        from scripts.freeze_evaluation_candidate import _measured_system_files
        files += _measured_system_files()
    protocol["file_sha256"] = {os.path.relpath(p, HERE).replace("\\", "/"): lf_sha(p) for p in sorted(set(files))}
    assert original == source_hashes(), "SOURCE_CHANGED_DURING_PREPARE"
    write(HERE / "protocol.json", protocol)
    E.load_inputs(HERE)
    subprocess.run([sys.executable, "-B", str(HERE / "oracle.py")], check=True, capture_output=True)
    print(json.dumps({"lock_status": protocol["lock_status"], "cases": 36, "source_requests": sum(c["n_source_requests"] for c in corpus["cases"]),
                      "gates": {n: g["status"] for n, g in gates.items()}, "candidate": protocol["frozen_candidate"]["status"],
                      "locked_sha256": protocol["locked_sha256"], "protocol_sha256": E.V1._sha(protocol)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--prepare", action="store_true")
    choice.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    prepare(lock=args.lock)
