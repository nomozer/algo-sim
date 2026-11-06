"""Classify scanner metadata without copying flagged contents. Existing exceptions stay untouched."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
import check_publication_safety as gate

exceptions = gate.load_exceptions(gate.EXCEPTIONS)
scans = {}
for name, mode in [("head", None), ("integration", "bb61a804..HEAD"), ("task", "1be6a7ae..HEAD")]:
    items, messages = (gate.head_items(ROOT), []) if mode is None else gate.range_items(ROOT, mode)
    found = gate.scan(ROOT, items, messages, exceptions)
    blobs = gate._blobs(ROOT, sorted({f["blob"] for f in found if f["blob"]}))
    for f in found:
        body = blobs.get(f["blob"], b"")
        f["content_sha256"] = hashlib.sha256(body).hexdigest() if body else None
        f["has_personal_windows_path"] = bool(re.search(rb"[A-Za-z]:[\\/]Users[\\/][^\\/\r\n]+", body))
        if f["rule"] == "PY_TRACEBACK":
            f["classification"] = "HISTORICAL_DIAGNOSTIC_TRACEBACK"
            f["risk"] = "personal path disclosure" if f["has_personal_windows_path"] else "diagnostic implementation details"
            f["least_risk_action"] = "owner decides archive access or exact-blob exception; retain evidence bytes; HEAD edits do not erase history"
        elif f["rule"] == "HARDCODED_PASSWORD" and f["path"].startswith("backend/tests/"):
            f["classification"] = "TEST_FIXTURE"
            f["risk"] = "throw-away test account constant; history remains publishable content"
            f["least_risk_action"] = "owner decides exact-blob exception; no real credential rotation indicated by this fixture"
        elif f["rule"] == "BEARER_TOKEN" and ("test_dev_backend_launcher" in f["path"] or "docker-backend-dev-auto-refresh/SECRET_SCAN.json" in f["path"]):
            f["classification"] = "REDACTION_TEST_PLACEHOLDER"
            f["risk"] = "test placeholder copied into scanner evidence, not a service credential"
            f["least_risk_action"] = "owner decides exact-blob false-positive exception"
        else:
            f["classification"] = "NEEDS_MANUAL_SECRET_REVIEW"
            f["risk"] = "UNKNOWN"
            f["least_risk_action"] = "do not publish before owner classification"
        f["decision"] = "OWNER_DECISION_REQUIRED"
    scans[name] = {"range": mode or "HEAD", "scanned": len(items), "messages": len(messages),
                   "violations": len(found), "counts": dict(Counter(f["rule"] for f in found)),
                   "status": "BLOCKED" if found else "PASS", "findings": found}

result = {"schema": "axo-publication-review/1", "head": gate._git("rev-parse", "HEAD", cwd=ROOT).decode().strip(),
          "owner_exceptions_modified": False, "history_rewritten": False, "scans": scans}
target = OUT / (Path(sys.argv[1]).name if len(sys.argv) > 1 else "publication-audit.json")
assert not target.exists(), "fresh output required"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: {"status": v["status"], "violations": v["violations"], "counts": v["counts"]} for k, v in scans.items()}))
