"""Export / verify the offline envelope fixtures of the Hybrid Route D preview — the data contract handed to Scene3D
(`docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md`). 0 model calls.

    python scripts/export_hybrid_preview_fixtures.py --out <NEW directory>
    python scripts/export_hybrid_preview_fixtures.py --verify <directory>

Every fixture is the real response of `POST /api/preview/hybrid`, served in-process to a loopback peer:
- the operator token is ephemeral and never written;
- the network is blocked, `ALLOW_LIVE_AI=0`, and no API key is set;
- inputs come only from committed corpora, the holdout cases and the declared faults of
  `tests/test_hybrid_preview_contract.py` (no hand-written envelope).

`--out` refuses an existing directory and an uncommitted `backend/app` or input (`INPUT_PATHS`), so the producer commit
names everything that ran.
`--verify` regenerates every fixture and exits 1 on any difference in source, expected outcome or response. The producer
identity is reported, not compared: a later commit may serve the same contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

SCHEMA = "hybrid-preview-envelope-fixture/1"
MANIFEST_SCHEMA = "hybrid-preview-envelope-fixtures/1"
URL = "/api/preview/hybrid"
#: Committed inputs used for the served fixtures (id → origin). Refusals come from `CASES` of the contract test.
SERVED = (
    ("pyramid-midpoint-area-AB", "corpus:positive"),
    ("pyramid-shared-midpoint-area-and-distance", "corpus:positive"),
    ("pyramid-projection-and-unnamed-midpoint-area", "corpus:positive"),
    ("H01_CUBE", "holdout"), ("H02_CUBOID_DISTANCE", "holdout"), ("H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS", "holdout"),
    ("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED", "holdout"), ("H11_SKEW_DISTANCE_COMPOSITION", "holdout"),
    ("H12_PROJECTION_MIDPOINT_ANGLE", "holdout"), ("H14_REGULAR_TETRAHEDRON", "holdout"),
    ("section-MAB-trapezoid", "benchmark"), ("intersection-SAB-SCD", "benchmark"),
)
CORPUS_FILE = "docs/evaluation/geometry/runs/contract-driven-goal-composition/corpus.json"
HOLDOUT_FILE = "backend/tests/geometry/fixtures/hybrid_holdout_cases.json"
#: Everything the fixtures are built from besides `backend/app`: inputs, case/fault definitions and this exporter.
INPUT_PATHS = ("backend/tests", "backend/scripts/export_hybrid_preview_fixtures.py",
               "docs/evaluation/geometry/runs/contract-driven-goal-composition")


def _canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _benchmark(case_id: str) -> dict:
    """The same problems as `scripts/export_hybrid_section_scenes.py` (built from `hybrid_compiler_benchmark`)."""
    from tests.geometry import hybrid_compiler_benchmark as HB

    sq = HB._square()
    if case_id == "section-MAB-trapezoid":
        quote = "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB)."
        sentences, facts = HB._with(sq, HB._mid("f5", "M", "S", "C"),
                                    HB._f("f6", "section", quote, role="question", solid="S.ABCD", points=list("MAB")))
    else:
        sentences, facts = HB._with(sq, HB._f("f5", "intersection_line", "Tìm giao tuyến của (SAB) và (SCD).",
                                              role="question", points_a=list("SAB"), points_b=list("SCD")))
    return {"text": " ".join(sentences), "payload": {"facts": facts}}


def _rows():
    """(id, kind, origin, case, fault, expected) for every fixture, in a fixed order."""
    from tests import test_hybrid_preview_contract as C

    for case_id, origin in SERVED:
        if origin == "corpus:positive":
            case, src = C.corpus(case_id, "positive"), f"{CORPUS_FILE}#positive/{case_id}"
        elif origin == "holdout":
            case, src = C.hold(case_id), f"{HOLDOUT_FILE}#{case_id}/b_facts"
        else:
            case, src = _benchmark(case_id), f"backend/tests/geometry/hybrid_compiler_benchmark.py ({case_id})"
        yield f"served-{case_id}", "served", src, case, None, {"http_status": 200, "envelope_status": "ok"}
    for cid, build, fault, code, category, cause in C.CASES:
        expected = {"http_status": 200, "envelope_status": "unsupported", "reason_code": code,
                    "failure_category": category, "refusal_cause": cause}
        yield f"refusal-{cid}", "refusal", f"tests/test_hybrid_preview_contract.py::CASES[{cid}]", build(), fault, expected
    text = C.CORPUS["positive"][0]["text"]
    for gate, status, code in (("disabled", 404, "PREVIEW_DISABLED"), ("forbidden", 403, "PREVIEW_FORBIDDEN"),
                               ("body-invalid", 422, "PREVIEW_BODY_INVALID"),
                               ("fixture-missing", 503, "OFFLINE_FIXTURE_REQUIRED")):
        yield f"gate-{gate}", "gate", "backend/app/main.py::hybrid_preview", {"text": text, "gate": gate}, None, \
            {"http_status": status, "reason_code": code}


def _covers(kind: str, fault, response: dict) -> list[str]:
    """Tags read from the response itself (never asserted from the case list)."""
    tags = [kind]
    route_d = response.get("route_d") or {}
    env = response.get("envelope") or {}
    if fault is not None:
        tags.append("injected_fault")
    if kind == "served":
        scene = env.get("scene3d") or {}
        if len(route_d.get("answer_exact") or {}) > 1:
            tags.append("multi_goal")
        if route_d.get("length_unit"):
            tags.append("symbolic_length_unit")
        if (route_d.get("planner") or {}).get("goal_checks"):
            tags.append("goal_observation")
        if route_d.get("planner", {}).get("auxiliary"):
            tags.append("auxiliary_points")
        tags += sorted({f"object:{o['type']}" for o in scene.get("objects", ())
                        if o.get("type") in ("section", "line3", "plane")})
    return tags


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def _producer() -> dict:
    from freeze_evaluation_candidate import measured_system_hash, product_commit

    from app.ai.hybrid_preview import ADAPTER_VERSION, ENVELOPE_VERSION

    tree, files = measured_system_hash()
    return {"commit": _git("rev-parse", "HEAD"), "product_commit": product_commit(),
            "source_fingerprint": {"measured_system_hash": tree, "files": files,
                                   "rule": "scripts/freeze_evaluation_candidate.py::measured_system_hash"},
            "adapter_version": ADAPTER_VERSION, "envelope_version": ENVELOPE_VERSION,
            "backend_app_dirty": bool(_git("status", "--porcelain", "--", "backend/app")),
            "inputs_dirty": bool(_git("status", "--porcelain", "--", *INPUT_PATHS))}


def generate() -> tuple[list[dict], str]:
    """Run every row through the endpoint. Returns the fixtures and the ephemeral token (for the leak check only)."""
    import pytest
    from fastapi.testclient import TestClient

    token = secrets.token_urlsafe(32)
    os.environ.update(ALLOW_LIVE_AI="0", HYBRID_ROUTE_D_PREVIEW="1", HYBRID_ROUTE_D_PREVIEW_TOKEN=token,
                      GEMINI_API_KEY="")
    os.environ.pop("GEOMETRY_COMPILER_MODE", None)

    def no_network(*a, **k):
        raise RuntimeError("network access is forbidden while exporting preview fixtures")
    socket.getaddrinfo = socket.create_connection = no_network

    import app.main as main
    from tests.test_hybrid_preview_api import provider_body

    client = TestClient(main.app, client=("127.0.0.1", 43210))
    producer = _producer()
    fixtures = []
    for fid, kind, origin, case, fault, expected in _rows():
        body = case.get("body") or (provider_body(case["payload"]) if "payload" in case else None)
        headers = {"X-AlgoSim-Preview-Token": token}
        with pytest.MonkeyPatch.context() as mp:
            if fault:
                fault(mp)
            gate = case.get("gate")
            if gate == "disabled":
                mp.setenv("HYBRID_ROUTE_D_PREVIEW", "0")
            if gate == "forbidden":
                headers = {}
            main.app.state.hybrid_preview_fixtures = {} if gate == "fixture-missing" else {case["text"]: body}
            r = (client.post(URL, content="not-json", headers={**headers, "content-type": "application/json"})
                 if gate == "body-invalid" else client.post(URL, json={"problem_text": case["text"]}, headers=headers))
        response = r.json()
        env = response.get("envelope") or response
        observed = {"http_status": r.status_code,
                    **({"envelope_status": env["status"]} if "status" in env else {}),
                    **{k: env[k] for k in ("reason_code", "failure_category", "refusal_cause") if k in env}}
        if any(observed.get(k) != v for k, v in expected.items()):
            raise SystemExit(f"{fid}: expected {expected}, observed {observed}")
        source = {"origin": origin, "problem_text": case["text"], "provider_body": body}
        fixtures.append({
            "schema": SCHEMA, "id": fid, "kind": kind, "covers": _covers(kind, fault, response),
            "source": {**source, "input_sha256": _sha(_canonical({"problem_text": case["text"], "provider_body": body}))},
            "injection": None if fault is None else {"name": fault.__name__,
                                                     "defined_in": "backend/tests/test_hybrid_preview_contract.py"},
            "producer": producer, "expected": observed, "response": response,
            "response_sha256": _sha(_canonical(response)),
        })
    return fixtures, token


def _text(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


_FORBIDDEN = ("X-AlgoSim-Preview-Token", "GEMINI_API_KEY", "HYBRID_ROUTE_D_PREVIEW_TOKEN", "Authorization", "api_key")


def _leaks(text: str, token: str) -> list[str]:
    return [s for s in (token, *_FORBIDDEN) if s in text]


def export(out: Path) -> int:
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    fixtures, token = generate()
    producer = fixtures[0]["producer"]
    if producer["backend_app_dirty"] or producer["inputs_dirty"]:
        print("refusing to export from uncommitted backend/app or inputs: the producer commit would not name what ran")
        return 2
    texts = {f["id"]: _text(f) for f in fixtures}
    leaked = {fid: _leaks(t, token) for fid, t in texts.items() if _leaks(t, token)}
    if leaked:
        print(f"refusing to write: secret material in {leaked}")
        return 2
    out.mkdir(parents=True)
    rows = []
    for f in fixtures:
        name = f"{f['id']}.json"
        with open(out / name, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texts[f["id"]])
        rows.append({"id": f["id"], "kind": f["kind"], "file": name, "sha256": _sha(texts[f["id"]]),
                     "response_sha256": f["response_sha256"], "expected": f["expected"], "covers": f["covers"]})
    manifest = {"schema": MANIFEST_SCHEMA, "generated_by": "backend/scripts/export_hybrid_preview_fixtures.py",
                "producer": fixtures[0]["producer"], "count": len(rows), "fixtures": rows}
    with open(out / "manifest.json", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(_text(manifest))
    print(json.dumps({"written": len(rows), "out": str(out)}, ensure_ascii=False))
    return 0


def _strip_verified_wave1_segment_certificates(response: dict, stored_response: dict) -> dict | None:
    """When verifying against an Adapter /2 bundle recorded before Wave 1 segment3 certificates,
    validate every additive `segment3.perpendicular_witness` with `verify_perpendicular_witness` and
    return a copy with only those additive fields removed so the historical `response_sha256` can be checked."""
    from copy import deepcopy
    from app.simulation.geometry_functions.certificates import CERTIFICATE_SCHEMA, verify_perpendicular_witness

    f_scene = (response.get("envelope") or {}).get("scene3d") or {}
    s_scene = (stored_response.get("envelope") or {}).get("scene3d") or {}
    f_objs = f_scene.get("objects") or []
    s_objs = {o["id"]: o for o in (s_scene.get("objects") or []) if isinstance(o, dict) and "id" in o}
    if not f_objs or not s_objs:
        return None
    copy_resp = deepcopy(response)
    copy_objs = copy_resp["envelope"]["scene3d"]["objects"]
    stripped_any = False
    for obj in copy_objs:
        if not isinstance(obj, dict) or obj.get("type") != "segment3":
            continue
        w = obj.get("perpendicular_witness")
        s_obj = s_objs.get(obj.get("id"))
        if (
            isinstance(w, dict)
            and w.get("certificate") == CERTIFICATE_SCHEMA
            and isinstance(s_obj, dict)
            and "perpendicular_witness" not in s_obj
        ):
            ok, _ = verify_perpendicular_witness(w, f_scene, f_scene.get("chart_metric"), segment_obj=obj)
            if not ok:
                return None
            obj.pop("perpendicular_witness", None)
            stripped_any = True
    return copy_resp if stripped_any else None


#: Declared runtime-identity deltas, in order: a later product revision that bumps a route D version names the exact
#: old → new pair here. `--verify` maps a fresh response back ONLY through these pairs (and the preview fingerprint they
#: determine, recomputed on both sides); every other byte must still equal the stored fixture.
IDENTITY_DELTAS = (
    {"run": "goal-directed-function-composition",
     "versions": {"registry_version": ("geometry-functions/6", "geometry-functions/7"),
                  "planner_version": ("geometry-fact-planner/7", "geometry-fact-planner/8"),
                  "engine_version": ("geometry-function-engine/5", "geometry-function-engine/6")}},
    {"run": "geometry-capability-expansion",
     "versions": {"registry_version": ("geometry-functions/7", "geometry-functions/8"),
                  "planner_version": ("geometry-fact-planner/8", "geometry-fact-planner/9"),
                  "engine_version": ("geometry-function-engine/6", "geometry-function-engine/7")}},
    {"run": "source-gate-hardening",                       # engine unchanged (/7)
     "versions": {"registry_version": ("geometry-functions/8", "geometry-functions/9"),
                  "planner_version": ("geometry-fact-planner/9", "geometry-fact-planner/10")}},
    {"run": "composite-geometry",
     "versions": {"registry_version": ("geometry-functions/9", "geometry-functions/10"),
                  "engine_version": ("geometry-function-engine/7", "geometry-function-engine/8")}},
    {"run": "volume-reasoning",
     "versions": {"registry_version": ("geometry-functions/10", "geometry-functions/11"),
                  "planner_version": ("geometry-fact-planner/10", "geometry-fact-planner/11"),
                  "engine_version": ("geometry-function-engine/8", "geometry-function-engine/9")}},
)


def _preview_fingerprint(identity: dict) -> str:
    from app.ai.hybrid_preview import preview_identity

    source = {"route": "HYBRID_ROUTE_D_PREVIEW", **{k: identity.get(k) for k in preview_identity()}}
    return hashlib.sha256(json.dumps(source, sort_keys=True).encode("utf-8")).hexdigest()


def _restore_declared_identity(response: dict, stored_response: dict) -> dict | None:
    """A copy of `response` whose route D identity is mapped back through `IDENTITY_DELTAS` to the stored one, or None
    when an identity field differs other than by a declared pair, or a fingerprint is not the hash of its own identity."""
    from copy import deepcopy

    fresh, stored = deepcopy(response), stored_response
    rd, srd = fresh.get("route_d") or {}, stored.get("route_d") or {}
    ident, sident = rd.get("runtime_identity"), srd.get("runtime_identity")
    pairs = {}
    for delta in IDENTITY_DELTAS:
        for key, (old, new) in delta["versions"].items():
            pairs.setdefault(key, {})[new] = old
    if isinstance(ident, dict) and isinstance(sident, dict):
        if ident.get("fingerprint") != _preview_fingerprint(ident) or sident.get("fingerprint") != _preview_fingerprint(sident):
            return None
        for key, back in pairs.items():
            while ident.get(key) in back and ident.get(key) != sident.get(key):
                ident[key] = back[ident[key]]
        ident["fingerprint"] = _preview_fingerprint(ident)
    planner = rd.get("planner")
    if isinstance(planner, dict) and "version" in planner:
        back = pairs["planner_version"]
        while planner["version"] in back and planner["version"] != (srd.get("planner") or {}).get("version"):
            planner["version"] = back[planner["version"]]
    return fresh


def verify(directory: Path) -> int:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    problems = []
    stored = {}
    for row in manifest["fixtures"]:
        raw = (directory / row["file"]).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        if _sha(raw) != row["sha256"]:
            problems.append(f"{row['id']}: file hash differs from manifest")
        stored[row["id"]] = json.loads(raw)
    fixtures, token = generate()
    fresh = {f["id"]: f for f in fixtures}
    if set(fresh) != set(stored):
        problems.append(f"fixture set differs: missing {sorted(set(stored) - set(fresh))}, "
                        f"new {sorted(set(fresh) - set(stored))}")
    for fid in sorted(set(fresh) & set(stored)):
        for key in ("source", "expected", "covers", "injection"):
            if fresh[fid][key] != stored[fid][key]:
                problems.append(f"{fid}: {key} differs")
        restored = _restore_declared_identity(fresh[fid]["response"], stored[fid]["response"])
        if restored is None:
            problems.append(f"{fid}: runtime identity differs other than by a declared pair")
            continue
        fresh[fid] = {**fresh[fid], "response": restored, "response_sha256": _sha(_canonical(restored))}
        if fresh[fid]["response"] != stored[fid]["response"] or fresh[fid]["response_sha256"] != stored[fid]["response_sha256"]:
            stripped = _strip_verified_wave1_segment_certificates(fresh[fid]["response"], stored[fid]["response"])
            if stripped is None or stripped != stored[fid]["response"] or _sha(_canonical(stripped)) != stored[fid]["response_sha256"]:
                if fresh[fid]["response"] != stored[fid]["response"]:
                    problems.append(f"{fid}: response differs")
                if fresh[fid]["response_sha256"] != stored[fid]["response_sha256"]:
                    problems.append(f"{fid}: response_sha256 differs")
        if _leaks(_text(stored[fid]), token):
            problems.append(f"{fid}: secret material")
    producer = fixtures[0]["producer"]
    same = producer["source_fingerprint"] == manifest["producer"]["source_fingerprint"]
    print(json.dumps({"verified": len(stored), "problems": problems, "producer_now": producer,
                      "same_source_fingerprint": same}, ensure_ascii=False, indent=1))
    return 1 if problems else 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out")
    mode.add_argument("--verify")
    args = ap.parse_args()
    return export(Path(args.out)) if args.out else verify(Path(args.verify))


if __name__ == "__main__":
    raise SystemExit(main())
