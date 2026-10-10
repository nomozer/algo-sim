# -*- coding: utf-8 -*-
"""Execute both complete pilot schedules through the production adapters with fixture responses and network disabled."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from scripts import run_hybrid_ab_pilot as P
from scripts.hybrid_ab_offline import facts_from_calls


class FixtureProvider:
    """Handwritten historical parser fixtures, never live outputs. G05 gets an explicit unsupported fixture."""
    is_live = False

    def __init__(self):
        fixture_dir = ROOT / "backend/tests/geometry/fixtures"
        self.fixtures = {}
        for source, filename in (("paraphrase", "paraphrase_cases.json"),
                                 ("expansion", "geometry_expansion_cases.json"),
                                 ("hybrid", "hybrid_holdout_cases.json")):
            for row in json.loads((fixture_dir / filename).read_text(encoding="utf8"))["cases"]:
                if source == "paraphrase" and not row["id"].startswith("P"):
                    continue
                self.fixtures[row["text"]] = {
                    "A": row.get("a_calls", row.get("calls")),
                    "B": row.get("b_facts", facts_from_calls(row.get("calls", []))),
                }
        self.calls = 0
        self.response_bytes = {}

    def send(self, arm, payload, timeout_seconds):
        if ("tools" in payload) != (arm == "A"):
            raise AssertionError("ARM_SURFACE_MISMATCH")
        if payload["generationConfig"]["maxOutputTokens"] != P.MAX_OUTPUT_TOKENS:
            raise AssertionError("OUTPUT_CAP_MISMATCH")
        text = payload["contents"][0]["parts"][0]["text"].split('"""\n', 1)[1].rsplit('\n"""', 1)[0]
        fixture = self.fixtures.get(text)
        if arm == "A":
            calls = fixture["A"] if fixture else [{
                "id": "c1", "fn": "unsupported", "args": {"reason": "G05 apparatus-only fixture"},
                "source": {"quotes": [text]}}]
            parts = [{"functionCall": {"name": c["fn"], "args": {
                **c["args"], "call_id": c["id"], "quotes": c["source"]["quotes"],
                "depends_on": c.get("depends_on", [])}}} for c in calls]
        else:
            facts = fixture["B"] if fixture else [{
                "id": "f1", "kind": "unsupported", "role": "premise", "negated": False,
                "ambiguous": False, "quotes": [text], "reason": "G05 apparatus-only fixture"}]
            parts = [{"text": P.canonical_json({"facts": facts}).decode("utf8")}]
        size = len(P.canonical_json(parts))
        self.response_bytes[(text, arm)] = size
        if size > P.MAX_OUTPUT_TOKENS:
            raise AssertionError("fixture byte-bound exceeds selected output ceiling")
        self.calls += 1
        # Deliberately large fake input usage exercises the byte-bound accounting, not Gemini tokenizer accuracy.
        prompt = len(P.canonical_json(payload))
        return {"modelVersion": P.MODEL, "usageMetadata": {
            "promptTokenCount": prompt, "candidatesTokenCount": size, "thoughtsTokenCount": 0,
            "totalTokenCount": prompt + size},
            "candidates": [{"finishReason": "STOP", "content": {"parts": parts}}]}


def certify(out_dir: Path) -> dict:
    import httpx
    if out_dir.exists() and any(out_dir.iterdir()):
        raise P.PilotStopped("CERTIFICATION_OUTPUT_EXISTS")
    provider = FixtureProvider()
    # Hard-block sockets and both HTTP client paths: a wiring regression cannot silently make a model call.
    with patch.object(socket.socket, "connect", side_effect=AssertionError("NETWORK_FORBIDDEN")) as network, \
         patch.object(httpx.Client, "send", side_effect=AssertionError("NETWORK_FORBIDDEN")), \
         patch.object(httpx.AsyncClient, "send", side_effect=AssertionError("NETWORK_FORBIDDEN")):
        results = {}
        for mode in P.PilotMode:
            state = P.run_pilot(mode, provider, out_dir / mode.value)
            expected = 24 if mode == P.PilotMode.SMOKE_AB else 288
            assert state["stop_reason"] is None and len(state["rows"]) == expected
            assert state["live_model_calls"] == 0
            assert sum(r["arm"] == "A" for r in state["rows"]) == expected // 2
            assert any(r["route"]["scene3d"] for r in state["rows"])
            results[mode.value] = {"completed_rows": len(state["rows"]), "identity": state["identity"],
                                  "budget": state["budget"], "totals": state["totals"],
                                  "served_geometry_rows": sum(r["route"]["status"] == "SERVED" for r in state["rows"]),
                                  "stop_reason": state["stop_reason"]}
        assert network.call_count == 0
    summary = {"schema": "hybrid_ab_fake_certification/2", "verdict": "OFFLINE_SCHEDULES_CERTIFIED",
               "live_model_calls": 0, "network_calls": 0, "fake_provider_calls": provider.calls,
               "results": results, "max_fixture_response_bytes": max(provider.response_bytes.values()),
               "budget_comparison": P.audit_reservations(),
               "limitation": "Fake fixtures certify wiring and guards. G05 responses are unsupported apparatus fixtures; "
                             "no Gemini extraction, thinking allocation or live truncation performance was measured."}
    P._persist(out_dir / "CERTIFICATION.json", summary, ())
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    result = certify(args.out_dir)
    print(json.dumps({"verdict": result["verdict"], "fake_calls": result["fake_provider_calls"],
                      "live_model_calls": result["live_model_calls"]}))
