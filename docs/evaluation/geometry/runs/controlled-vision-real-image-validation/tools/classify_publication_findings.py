"""Classify every whole-HEAD publication finding without ever printing a matched line or value.

Reuses the gate itself (backend/scripts/check_publication_safety.py) for scanning, so the count here
is the gate's count. Adds, per finding, only derived metadata: value SHAPE (length, entropy bucket,
placeholder markers), file role, registry entry, and whether the same blob is already at baseline /
on origin/main. Decides nothing: owner_decision is read, never written.

Run from backend/:  python ../docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/classify_publication_findings.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
BASELINE = "44807b13bffe608153bc58e453a3bc9c37703485"
sys.path.insert(0, str(ROOT / "backend/scripts"))
import check_publication_safety as gate  # noqa: E402

MARKERS = re.compile(rb"(?i)fake|test|example|dummy|placeholder|sample|your|xxxx|abcd|1234|gia|secret|token|key|dan[-_ ]?key|changeme|password")
HOME = re.compile(rb"(?i)[A-Z]:\\+Users\\+[^\\\r\n\"']+|/home/[^/\s\"']+|/Users/[^/\s\"']+")
EXC_NAME = re.compile(rb"(?m)^([A-Za-z_][\w.]*(?:Error|Exception|Warning|Interrupt|Exit))\b")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8", "replace")


def tree(ref: str) -> set[tuple[str, str]]:
    out = set()
    for rec in subprocess.check_output(["git", "ls-tree", "-r", "-z", ref], cwd=ROOT).split(b"\0"):
        if rec:
            meta, path = rec.split(b"\t", 1)
            out.add((path.decode("utf-8"), meta.split()[2].decode()))
    return out


def secret_value(rule: str, text: bytes) -> bytes:
    """The value part only: the variable name or the word Bearer must not count as a placeholder marker."""
    if rule == "HARDCODED_PASSWORD":
        return re.search(rb"['\"]([^'\"]+)['\"]", text).group(1)
    if rule in ("SECRET_ASSIGNMENT", "BEARER_TOKEN"):
        return re.search(rb"[A-Za-z0-9_.\-]+$", text).group(0)
    return text


def shape(value: bytes) -> dict:
    """Describe a secret-shaped match without revealing it."""
    counts = Counter(value)
    entropy = -sum(c / len(value) * math.log2(c / len(value)) for c in counts.values())
    period = next((p for p in range(1, 9) if len(value) > 2 * p and all(value[i] == value[i - p] for i in range(p, len(value)))), None)
    return {"length": len(value), "distinct_characters": len(counts), "shannon_bits_per_char": round(entropy, 2),
            "repeating_period": period, "contains_placeholder_marker": bool(MARKERS.search(value)),
            "looks_random": entropy >= 4.0 and period is None and not MARKERS.search(value)}


def role(path: str) -> str:
    if path.startswith("backend/tests/") or "/tests/" in path or path.endswith((".test.ts", ".test.tsx")):
        return "TEST_SOURCE"
    if path.endswith(".example"):
        return "CONFIG_TEMPLATE"
    if path.startswith("docs/evaluation/"):
        return "EVALUATION_EVIDENCE"
    if path.startswith(("backend/app/", "frontend/src/")):
        return "PRODUCT_SOURCE"
    return "OTHER"


def main() -> int:
    exceptions = gate.load_exceptions(gate.EXCEPTIONS)
    items = gate.head_items(ROOT)
    found = gate.scan(ROOT, items, [], exceptions)
    blobs = gate._blobs(ROOT, sorted({f["blob"] for f in found}))
    baseline_tree = tree(BASELINE)
    try:
        remote_tree, remote = tree("origin/main"), git("rev-parse", "origin/main").strip()
    except subprocess.CalledProcessError:
        remote_tree, remote = None, None
    rows = []
    for f in found:
        content = blobs[f["blob"]]
        lines = content.split(b"\n")
        entry = exceptions.get((f["path"], f["blob"]))
        row = {"rule": f["rule"], "path": f["path"], "blob": f["blob"], "line": f["line"],
               "content_sha256": hashlib.sha256(content).hexdigest(), "file_role": role(f["path"]),
               "gate_exception_state": f["exception"], "registry_category": (entry or {}).get("category"),
               "registry_scope": (entry or {}).get("scope"), "first_commit": (entry or {}).get("first_commit"),
               "first_commit_date": (entry or {}).get("first_commit_date"),
               "same_blob_at_report_head_44807b13b": (f["path"], f["blob"]) in baseline_tree,
               "same_blob_on_origin_main": None if remote_tree is None else (f["path"], f["blob"]) in remote_tree}
        if f["rule"] == "PY_TRACEBACK":
            row["match_kind"] = "HEADER" if b"most recent call last" in lines[f["line"] - 1] else "FRAME"
        else:
            match = next(m for m in gate.RULES[f["rule"]].finditer(content) if content.count(b"\n", 0, m.start()) + 1 == f["line"])
            row["value_shape"] = shape(secret_value(f["rule"], match.group(0)))
        rows.append(row)

    per_blob = {}
    for (path, blob), group in sorted({(r["path"], r["blob"]): [x for x in rows if (x["path"], x["blob"]) == (r["path"], r["blob"])] for r in rows}.items()):
        content = blobs[blob]
        other_rules = sorted({rule for rule, _ in gate.findings_in(content)})
        secret_rows = [r for r in group if "value_shape" in r]
        if secret_rows:
            random_like = [r for r in secret_rows if r["value_shape"]["looks_random"]]
            classification = ("SECRET_SHAPED_VALUE_NOT_PROVEN_SYNTHETIC" if random_like else
                              "CONFIG_TEMPLATE_PLACEHOLDER" if group[0]["file_role"] == "CONFIG_TEMPLATE" else
                              "SYNTHETIC_TEST_VECTOR" if group[0]["file_role"] == "TEST_SOURCE" else
                              "SYNTHETIC_VALUE_IN_EVIDENCE")
            risk = "HIGH_UNTIL_OWNER_CONFIRMS_NOT_A_LIVE_CREDENTIAL" if random_like else "LOW_FALSE_POSITIVE_BY_SHAPE"
        else:
            classification = "RAW_TRACEBACK_IN_HISTORICAL_LOG"
            risk = "LOW_PRIVACY_LOCAL_ACCOUNT_AND_PATHS" if HOME.search(content) else "LOW_NO_HOME_PATH_FOUND"
        per_blob[f"{path}@{blob[:12]}"] = {
            "path": path, "blob": blob, "findings": len(group), "rules": dict(Counter(r["rule"] for r in group)),
            "all_rules_matching_this_blob": other_rules, "file_role": group[0]["file_role"], "bytes": len(content),
            "classification": classification, "risk": risk,
            "discloses_home_directory_path": bool(HOME.search(content)),
            "exception_type_names_in_file": sorted({m.decode() for m in EXC_NAME.findall(content)})[:12],
            "registry_category": group[0]["registry_category"], "registry_scope": group[0]["registry_scope"],
            "gate_exception_state": group[0]["gate_exception_state"], "first_commit": group[0]["first_commit"],
            "first_commit_date": group[0]["first_commit_date"],
            "introduced_after_report_head": not group[0]["same_blob_at_report_head_44807b13b"],
            "same_blob_on_origin_main": group[0]["same_blob_on_origin_main"],
            "referenced_by_tracked_files": None,
            "agent_can_close_without_owner": False,
            "why_not": ("exempting a blob requires owner_decision=APPROVED_BY_USER, which only the Owner writes; "
                        "editing or removing the file changes frozen evidence or a test of the scanners themselves")}
    # Which pending evidence logs are still linked from other tracked files (removal would break frozen reports)?
    names = {Path(v["path"]).name: key for key, v in per_blob.items() if v["file_role"] == "EVALUATION_EVIDENCE"}
    if names:
        grep = subprocess.run(["git", "grep", "-l", "-F", *sum((["-e", n] for n in names), []), "HEAD", "--", "docs", "backend", "frontend"],
                              cwd=ROOT, capture_output=True).stdout.decode("utf-8", "replace").splitlines()
        referencing = [g.split(":", 1)[1] for g in grep]
        for name, key in names.items():
            own = per_blob[key]["path"]
            hits = subprocess.run(["git", "grep", "-l", "-F", name, "HEAD", "--", *referencing], cwd=ROOT, capture_output=True).stdout.decode("utf-8", "replace").splitlines()
            per_blob[key]["referenced_by_tracked_files"] = sorted({h.split(":", 1)[1] for h in hits} - {own})[:8]

    registry_pending = [e for e in exceptions.values() if e["owner_decision"] == gate.PENDING]
    summary = {
        "findings": len(rows), "distinct_blobs": len(per_blob),
        "findings_by_rule": dict(Counter(r["rule"] for r in rows)),
        "blobs_by_classification": dict(Counter(v["classification"] for v in per_blob.values())),
        "findings_by_classification": dict(Counter(per_blob[f"{r['path']}@{r['blob'][:12]}"]["classification"] for r in rows)),
        "blobs_by_risk": dict(Counter(v["risk"] for v in per_blob.values())),
        "blobs_by_file_role": dict(Counter(v["file_role"] for v in per_blob.values())),
        "findings_without_registry_entry": sum(r["gate_exception_state"] is None for r in rows),
        "blobs_introduced_after_report_head": sum(v["introduced_after_report_head"] for v in per_blob.values()),
        "blobs_already_on_origin_main": None if remote is None else sum(bool(v["same_blob_on_origin_main"]) for v in per_blob.values()),
        "blobs_with_random_looking_secret_shape": sum(v["classification"] == "SECRET_SHAPED_VALUE_NOT_PROVEN_SYNTHETIC" for v in per_blob.values()),
        "registry_entries_pending": len(registry_pending),
        "registry_entries_pending_not_in_head_tree": sorted(e["path"] for e in registry_pending if (e["path"], e["blob"]) not in set(items)),
        "registry_entries_owner_approved": sum(e["owner_decision"] == gate.OWNER_APPROVED for e in exceptions.values()),
        "resolved_by_this_run": 0, "require_owner_review": len(rows)}
    out = {"schema": "algosim-publication-pending-classification/1", "run_id": RUN.name,
           "generated_at_utc": datetime.now(timezone.utc).isoformat(), "head": git("rev-parse", "HEAD").strip(),
           "origin_main": remote, "scanned_tracked_files": len(items),
           "gate": "backend/scripts/check_publication_safety.py --head (imported, same rules and registry)",
           "registry": gate.EXCEPTIONS.relative_to(ROOT).as_posix(),
           "privacy": "No matched line or value is stored. Secret-shaped matches are described by length, entropy and placeholder markers only.",
           "limits": ["The gate's regexes are a lower bound, not proof that nothing else is sensitive.",
                      "looks_random=false is a shape judgement; it cannot prove a string was never a live credential.",
                      "This tool reads owner_decision; it never writes it."],
           "PUBLICATION_HEAD": "BLOCKED_PENDING_OWNER_REVIEW" if rows else "PASS",
           "summary": summary, "blobs": per_blob, "findings": rows}
    (RUN / "publication_pending_classification.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
