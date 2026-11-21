"""Offline authorization preflight for a future paired Vision comparison.

No provider transport is connected while owner authorization is absent. The existing
paired-route SafeCampaignBudget provides request/USD caps for a future authorized executor.
This script never enables ALLOW_LIVE_AI and never writes human approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ["ALLOW_LIVE_AI"] = "0"


def validate(authorization: dict, corpus_bytes: bytes) -> list[str]:
    errors = []
    if authorization.get("owner_decision") != "AUTHORIZE_VISION_COMPARISON":
        errors.append("explicit owner decision absent")
    if not authorization.get("user_instruction_reference"):
        errors.append("user instruction reference absent")
    for field in ("provider", "model"):
        if not isinstance(authorization.get(field), str) or not authorization[field].strip():
            errors.append(f"{field} absent")
    if authorization.get("corpus_sha256") != hashlib.sha256(corpus_bytes).hexdigest():
        errors.append("corpus hash mismatch")
    data_hashes = authorization.get("data_sha256")
    if not isinstance(data_hashes, list) or not data_hashes or any(
        not isinstance(h, str) or len(h) != 64 or any(c not in "0123456789abcdef" for c in h)
        for h in data_hashes
    ):
        errors.append("explicit image data hashes absent or malformed")
    budget = authorization.get("max_provider_requests")
    if type(budget) is not int or budget <= 0:
        errors.append("positive request budget absent")
    cost = authorization.get("max_cost_usd")
    if type(cost) not in (int, float) or cost <= 0 or not cost < float("inf"):
        errors.append("finite positive cost budget absent")
    stops = authorization.get("stop_conditions")
    if not isinstance(stops, list) or not stops or any(not isinstance(s, str) or not s.strip() for s in stops):
        errors.append("stop conditions absent")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        assert len(validate({}, b"{}")) == 9
        assert "positive request budget absent" in validate({"max_provider_requests": True}, b"{}")
        assert "finite positive cost budget absent" in validate({"max_cost_usd": float("nan")}, b"{}")
        print("3 authorization-rejection self-checks passed; provider_calls=0")
        return 0
    if not args.authorization or not args.corpus:
        print(json.dumps({"status": "NOT_AUTHORIZED", "provider_calls": 0,
                          "reason": "Explicit owner authorization and hash-bound corpus are required."}))
        return 2
    try:
        authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
        errors = validate(authorization, args.corpus.read_bytes()) if isinstance(authorization, dict) else ["authorization must be an object"]
    except (OSError, ValueError):
        errors = ["authorization or corpus unreadable"]
    if errors:
        print(json.dumps({"status": "NOT_AUTHORIZED", "provider_calls": 0, "errors": errors}))
        return 2
    print(json.dumps({"status": "BOUNDED_EXECUTOR_REQUIRED", "provider_calls": 0,
                      "reason": "Preflight fields present; dollar reservation, observed usage accounting, and stop enforcement must be connected before live execution."}))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
