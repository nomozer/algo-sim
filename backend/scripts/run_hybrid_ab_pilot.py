# -*- coding: utf-8 -*-
"""Offline-first identity, schedule and reservation contract for Hybrid A/B P-AB1.

This module deliberately has no network transport.  A later injected-provider layer may use these locked inputs only after
the identity and pre-request budget checks succeed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import random
import statistics
import math
import httpx
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-ab-pilot-readiness" / "inputs"
MAX_OUTPUT_TOKENS = 3072
PROMPT_FRAMING_RESERVE = 4096
INPUT_USD_PER_MILLION = 0.30
OUTPUT_USD_PER_MILLION = 2.50
MODEL = "gemini-2.5-flash"
LOCKED_CASES_SHA = "8f41f5374cef8e9c07020b92377cd723431b550c650fe0acb0f2acea47b30285"
LOCKED_ORACLE_SHA = "6e1a2437c5cc6879580591d066f9101eb91d88a2223f83868938482d9836ac0e"
LOCKED_QUESTIONS_SHA = "8599c6c97acca8df7d58c9b40d31e4922972826d5904a22b5859ede67feccb1f"
SCHEDULE_SEEDS = {"SMOKE_AB": 2026101012, "FULL_AB": 2026101048}


class PilotStopped(RuntimeError):
    """A durable fail-closed measurement stop; never implies zero cost."""

SMOKE_IDS = (
    "g05/X1", "g05/P09", "g05/NT2", "g05/N02", "paraphrase/P01", "paraphrase/P08",
    "expansion/X02", "expansion/X06", "hybrid/H01", "hybrid/H05", "hybrid/H07", "hybrid/H13",
)


class PilotMode(str, Enum):
    SMOKE_AB = "SMOKE_AB"
    FULL_AB = "FULL_AB"


@dataclass(frozen=True)
class PilotCaps:
    logical_calls: int
    http_attempts: int
    accounted_tokens: int
    usd: float
    samples: int


CAPS = {
    PilotMode.SMOKE_AB: PilotCaps(24, 36, 500_000, 0.60, 1),
    PilotMode.FULL_AB: PilotCaps(300, 450, 6_000_000, 7.00, 3),
}


@dataclass(frozen=True)
class PilotRow:
    case_id: str
    source: str
    text: str


@dataclass(frozen=True)
class PilotIdentity:
    mode: PilotMode
    corpus_sha256: str
    oracle_sha256: str
    question_obligations_sha256: str
    parameters_sha256: str


@dataclass(frozen=True)
class LockedInputs:
    mode: PilotMode
    rows: tuple[PilotRow, ...]
    identity: PilotIdentity


@dataclass(frozen=True)
class ScheduledCall:
    case_id: str
    sample: int
    arm: str


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _read_json(name: str) -> dict[str, Any]:
    data = json.loads((INPUTS / name).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{name}: JSON root must be an object")
    return data


def load_locked_inputs(mode: PilotMode) -> LockedInputs:
    """Load additive materialized text/oracle; never reads historical run outputs at execution time."""
    cases, oracle = _read_json("pilot_cases.json"), _read_json("oracle.json")
    questions = _read_json("question_obligations.json")
    if _sha(cases) != LOCKED_CASES_SHA or _sha(oracle) != LOCKED_ORACLE_SHA or _sha(questions) != LOCKED_QUESTIONS_SHA:
        raise PilotStopped("INPUT_IDENTITY_MISMATCH")
    raw_rows = cases.get("rows")
    if cases.get("schema") != "hybrid_ab_pilot_cases/1" or not isinstance(raw_rows, list):
        raise ValueError("pilot_cases schema mismatch")
    rows = tuple(PilotRow(str(x["id"]), str(x["source"]), str(x["text"])) for x in raw_rows)
    if len(rows) != 48 or len({x.case_id for x in rows}) != 48 or any(not x.text for x in rows):
        raise ValueError("locked corpus must contain 48 unique non-empty texts")
    if {str(x.get("id")) for x in oracle.get("rows", [])} != {x.case_id for x in rows}:
        raise ValueError("oracle does not cover exactly the locked corpus")
    selected = tuple(x for case_id in SMOKE_IDS for x in rows if x.case_id == case_id)
    if len(selected) != len(SMOKE_IDS):
        raise ValueError("smoke selection is incomplete")
    mode_rows = selected if mode is PilotMode.SMOKE_AB else rows
    parameters = {"model": "gemini-2.5-flash", "temperature": 0.0, "max_output_tokens": MAX_OUTPUT_TOKENS,
                  "framing_reserve": PROMPT_FRAMING_RESERVE, "mode": mode.value, "samples": CAPS[mode].samples,
                  "schedule_seed": SCHEDULE_SEEDS[mode.value]}
    return LockedInputs(mode, mode_rows, PilotIdentity(mode, _sha([x.__dict__ for x in mode_rows]),
                                                       _sha([x for x in oracle["rows"] if x["id"] in {r.case_id for r in mode_rows}]),
                                                       _sha(questions),
                                                       _sha(parameters)))


def schedule(locked: LockedInputs) -> tuple[ScheduledCall, ...]:
    """Deterministic pair order; each case/sample executes A and B exactly once."""
    rows: list[ScheduledCall] = []
    for row in locked.rows:
        for sample in range(1, CAPS[locked.mode].samples + 1):
            order = ("A", "B") if int(_sha([SCHEDULE_SEEDS[locked.mode.value], locked.mode.value, row.case_id, sample])[:2], 16) % 2 == 0 else ("B", "A")
            rows.extend(ScheduledCall(row.case_id, sample, arm) for arm in order)
    if len(rows) != len(locked.rows) * CAPS[locked.mode].samples * 2:
        raise AssertionError("schedule cardinality invariant")
    return tuple(rows)


def reserve_payload(payload: dict[str, Any], output_cap: int = MAX_OUTPUT_TOKENS) -> dict[str, float | int]:
    """Conservative local prompt estimator plus combined output/thinking cap; not a provider-proven bound."""
    prompt = len(canonical_json(payload)) + PROMPT_FRAMING_RESERVE
    total = prompt + output_cap
    usd = prompt * INPUT_USD_PER_MILLION / 1_000_000 + output_cap * OUTPUT_USD_PER_MILLION / 1_000_000
    return {"prompt_tokens": prompt, "output_tokens": output_cap, "tokens": total, "usd": usd}


def audit_reservations() -> dict[int, dict[str, dict[str, float | int]]]:
    """All-corpus deterministic audit. It sends no token-count or generation request."""
    from app.ai import fact_extraction as facts
    from app.ai import function_calling as functions

    full = load_locked_inputs(PilotMode.FULL_AB)
    smoke_ids = set(SMOKE_IDS)
    results: dict[int, dict[str, dict[str, float | int]]] = {}
    for cap in (2048, 3072, 8192):
        per_case = []
        for row in full.rows:
            a, b = functions.build_request(row.text), facts.build_request(row.text)
            a["generationConfig"]["maxOutputTokens"] = cap
            b["generationConfig"]["maxOutputTokens"] = cap
            per_case.append((row.case_id, reserve_payload(a, cap), reserve_payload(b, cap)))
        def total(items: list[tuple[str, dict[str, float | int], dict[str, float | int]]], repeats: int) -> dict[str, float | int]:
            return {"tokens": repeats * sum(int(a["tokens"]) + int(b["tokens"]) for _, a, b in items),
                    "usd": repeats * sum(float(a["usd"]) + float(b["usd"]) for _, a, b in items)}
        results[cap] = {"smoke": total([x for x in per_case if x[0] in smoke_ids], 1), "full": total(per_case, 3)}
    return results


def effective_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply the pilot's shared cap to the real adapter request, without altering product defaults."""
    value = json.loads(canonical_json(payload))
    value["generationConfig"]["maxOutputTokens"] = MAX_OUTPUT_TOKENS
    return value


def measurement_identity(locked: LockedInputs, caps: PilotCaps) -> dict[str, Any]:
    from app.ai import fact_extraction as facts, function_calling as functions
    surfaces = {}
    for arm, adapter in (("A", functions), ("B", facts)):
        payload = effective_payload(adapter.build_request(""))
        payload.pop("contents")
        surfaces[arm] = _sha(payload)
    # Reuse the candidate authority, including its frontend/schema coverage and CRLF normalization.
    from scripts.freeze_evaluation_candidate import measured_system_hash
    product, _ = measured_system_hash()
    cache = re.search(r'^CACHE_VERSION = "([^"]+)"', (ROOT / "backend/app/main.py").read_text(encoding="utf8"), re.M)
    if cache is None:
        raise PilotStopped("CACHE_IDENTITY_UNKNOWN")
    return {**asdict(locked.identity), "caps": asdict(caps), "surfaces": surfaces,
            "schedule_sha256": _sha([asdict(x) for x in schedule(locked)]),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "product_sha256": product, "model": MODEL, "cache_version": cache[1],
            "schedule_seed": SCHEDULE_SEEDS[locked.mode.value],
            "price_usd_per_million": {"input": INPUT_USD_PER_MILLION, "output_and_thoughts": OUTPUT_USD_PER_MILLION}}


@dataclass
class PilotBudget:
    logical_calls: int = 0
    http_attempts: int = 0
    tokens: int = 0
    usd: float = 0.0

    def reserve(self, reservation: dict[str, Any], caps: PilotCaps) -> None:
        for exhausted, code in (
            (self.logical_calls + 1 > caps.logical_calls, "LOGICAL_CAP"),
            (self.http_attempts + 1 > caps.http_attempts, "HTTP_CAP"),
            (self.tokens + reservation["tokens"] > caps.accounted_tokens, "TOKEN_CAP"),
            (self.usd + reservation["usd"] > caps.usd + 1e-12, "USD_CAP"),
            (reservation["prompt_tokens"] > 1_048_576, "CONTEXT_CAP"),
        ):
            if exhausted:
                raise PilotStopped(code)
        # Retain the entire conservative reservation even after known usage, avoiding optimistic reuse.
        self.logical_calls += 1
        self.http_attempts += 1
        self.tokens += reservation["tokens"]
        self.usd += reservation["usd"]


def redact(value: Any, secrets: tuple[str, ...]) -> tuple[Any, bool]:
    """Scrub credentials recursively, preserving promptTokenCount and other usage keys."""
    found = False
    def scrub(item: Any) -> Any:
        nonlocal found
        if isinstance(item, dict):
            output = {}
            for key, val in item.items():
                key = scrub(str(key))
                if re.search(r"api.?key|authorization|secret|password|access.?token|refresh.?token", key, re.I):
                    found = found or val != "[REDACTED]"
                    output[key] = "[REDACTED]"
                else:
                    output[key] = scrub(val)
            return output
        if isinstance(item, list):
            return [scrub(x) for x in item]
        if isinstance(item, str):
            for secret in secrets:
                if secret and secret in item:
                    found = True
                    item = item.replace(secret, "[REDACTED]")
            return item
        return item
    return scrub(value), found


def _persist(path: Path, state: dict[str, Any], secrets: tuple[str, ...]) -> None:
    clean, found = redact(state, secrets)
    if found:
        raise PilotStopped("SECRET_DETECTED")
    data = canonical_json(clean)
    temporary = path.with_suffix(".pending")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Windows: another process (indexer, antivirus) can hold a just-written file for a moment, and `os.replace`
        # raises PermissionError [WinError 5]. Retry briefly; a lock that lasts ~1.6 s still stops the pilot.
        for attempt in range(8):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(0.025 * 2 ** attempt)
        if path.read_bytes() != data:
            raise OSError("readback mismatch")
    except OSError:
        raise PilotStopped("PERSISTENCE_FAILED") from None
    # Fail on leaked exact credentials anywhere in this dedicated output directory.
    for artifact in path.parent.rglob("*"):
        if artifact.is_file() and any(secret.encode() in artifact.read_bytes() for secret in secrets if secret):
            raise PilotStopped("SECRET_DETECTED")


def _usage(body: Any, reservation: dict[str, Any], *, enforce_reservation: bool = True) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise PilotStopped("PROVIDER_RESPONSE_INVALID")
    usage = body.get("usageMetadata")
    required = ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in required):
        raise PilotStopped("USAGE_UNKNOWN")
    # Omitted thoughts means zero per the API's optional non-thinking counter, not a missing total.
    thoughts = usage.get("thoughtsTokenCount", 0)
    if type(thoughts) is not int or thoughts < 0 or usage.get("toolUsePromptTokenCount", 0):
        raise PilotStopped("USAGE_UNKNOWN")
    prompt, candidates, total = (usage[k] for k in required)
    if total != prompt + candidates + thoughts:
        raise PilotStopped("USAGE_UNKNOWN")
    if enforce_reservation and (prompt > reservation["prompt_tokens"] or candidates + thoughts > reservation["output_tokens"]):
        raise PilotStopped("RESERVATION_BREACH")
    return {"input_tokens": prompt, "output_tokens": candidates, "thinking_tokens": thoughts,
            "total_tokens": total, "usd": prompt * 0.30 / 1e6 + (candidates + thoughts) * 2.50 / 1e6}


def failure_source(code: str | None, arm: str) -> str | None:
    if code is None:
        return None
    if code.startswith(("PROVIDER", "HTTP", "MODEL_", "USAGE_", "RESPONSE_TRUNCATED")):
        return "infrastructure"
    if arm == "A" and code in {"SCHEMA_INVALID", "DANGLING_DEPENDENCY", "DEPENDENCY_CYCLE"}:
        return "ai_extraction"
    if code in {"JSON_INVALID", "NO_CANDIDATE", "NO_FUNCTION_CALL", "MALFORMED_FUNCTION_CALL",
                "MALFORMED_RESPONSE_PART", "CALL_ID_MISSING", "DUPLICATE_CALL_ID", "OBJECT_NOT_IN_QUOTE",
                "QUOTE_NOT_IN_SOURCE", "PREDICATE_NOT_IN_QUOTE", "GOAL_CLAUSE_NOT_PREMISE", "NEGATED_CLAUSE",
                "CONDITIONAL_CLAUSE", "UNGROUNDED_VALUE", "ROLE_NOT_IN_QUOTE", "PLANE_NOT_IN_QUOTE",
                "UNKNOWN_LABEL", "AMBIGUOUS_VALUE_QUOTE"}:
        return "ai_extraction"
    if arm == "B" and code in {"SCHEMA_INVALID", "FACT_INCOMPLETE", "AMBIGUOUS_REFERENCE", "AMBIGUOUS_FACT",
                               "PLAN_TOO_LARGE", "UNSUPPORTED_CAPABILITY", "UNKNOWN_SOLID"}:
        return "compiler"
    return "geometry"


def _totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {a: {k: 0 for k in ("input_tokens", "output_tokens", "thinking_tokens", "total_tokens", "usd")}
              for a in ("A", "B")}
    for row in rows:
        if row["usage"] is not None:
            for key, value in row["usage"].items():
                totals[row["arm"]][key] += value
    totals["unknown_usage_rows"] = sum(r["usage"] is None for r in rows)
    totals["actual_usd"] = None if totals["unknown_usage_rows"] else totals["A"]["usd"] + totals["B"]["usd"]
    return totals


def run_pilot(mode: PilotMode, provider: Any, out_dir: Path, *, resume: bool = False,
              caps: PilotCaps | None = None, secrets: tuple[str, ...] = ()) -> dict[str, Any]:
    """Execute the existing adapters once per schedule row through an injected, single-attempt transport."""
    from app.ai import fact_extraction as facts, function_calling as functions
    mode = PilotMode(mode)
    out_dir = Path(out_dir).resolve()
    docs = (ROOT / "docs").resolve()
    allowed = (INPUTS.parent / "fake-provider").resolve()
    if getattr(provider, "is_live", False) and out_dir.is_relative_to(docs):
        raise PilotStopped("LIVE_EVIDENCE_FORBIDDEN")
    if out_dir.is_relative_to(docs) and not out_dir.is_relative_to(allowed):
        raise PilotStopped("EVIDENCE_PATH_FORBIDDEN")
    locked = load_locked_inputs(mode)
    limits = caps or CAPS[mode]
    if any(getattr(limits, k) > getattr(CAPS[mode], k) for k in ("logical_calls", "http_attempts", "accounted_tokens", "usd")):
        raise PilotStopped("CAP_INCREASE_FORBIDDEN")
    identity = measurement_identity(locked, limits)
    planned = schedule(locked)
    path = out_dir / "manifest.json"
    if out_dir.exists() and not path.exists() and any(out_dir.iterdir()):
        raise PilotStopped("PARTIAL_ARTIFACT")
    out_dir.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if not resume:
            raise PilotStopped("OUTPUT_EXISTS")
        try:
            state = json.loads(path.read_bytes())
        except (ValueError, OSError):
            raise PilotStopped("PARTIAL_ARTIFACT") from None
        if state.get("identity") != identity:
            raise PilotStopped("IDENTITY_MISMATCH")
        execution_class = "LIVE" if getattr(provider, "is_live", False) else "FAKE"
        if state.get("execution_class") != execution_class:
            raise PilotStopped("EXECUTION_CLASS_MISMATCH")
        if state.get("pending") is not None or path.with_suffix(".pending").exists():
            raise PilotStopped("REQUEST_STATE_UNKNOWN")
        rows = state.get("rows")
        if not isinstance(rows, list) or state.get("rows_sha256") != _sha(rows) or len(rows) > len(planned):
            raise PilotStopped("PARTIAL_ARTIFACT")
        if type(state.get("live_model_calls")) is not int or state["live_model_calls"] != (
                len(rows) if execution_class == "LIVE" else 0):
            raise PilotStopped("LIVE_COUNT_MISMATCH")
        for index, row in enumerate(rows):
            if row["position"] != index or any(row[k] != getattr(planned[index], k) for k in ("case_id", "sample", "arm")):
                raise PilotStopped("SCHEDULE_MISMATCH")
        recalculated = PilotBudget()
        for row in rows:
            recalculated.reserve(row["reservation"], limits)
        if asdict(recalculated) != state.get("budget") or state.get("totals") != _totals(rows):
            raise PilotStopped("PARTIAL_ARTIFACT")
        if state["stop_reason"] is not None or len(rows) == len(planned):
            return state
    else:
        state = {"schema": "hybrid_ab_pilot/2", "identity": identity, "rows": [], "rows_sha256": _sha([]),
                 "pending": None, "stop_reason": None, "budget": asdict(PilotBudget()), "totals": _totals([]),
                 "live_model_calls": 0, "execution_class": "LIVE" if getattr(provider, "is_live", False) else "FAKE"}
        _persist(path, state, secrets)
    budget = PilotBudget(**state["budget"])
    texts = {r.case_id: r.text for r in locked.rows}
    for position in range(len(state["rows"]), len(planned)):
        call = planned[position]
        record = {**asdict(call), "position": position, "usage": None, "raw_response": None,
                  "model_version": None, "finish_reason": None, "latency_seconds": 0.0}
        stop: str | None = None
        request_started = False
        def transport(base_payload: dict[str, Any]) -> Any:
            nonlocal stop, request_started
            payload = effective_payload(base_payload)
            reservation = reserve_payload(payload)
            record.update(payload_sha256=_sha(payload), reservation=reservation,
                          surface_sha256=identity["surfaces"][call.arm])
            try:
                budget.reserve(reservation, limits)
            except PilotStopped as error:
                stop = str(error)
                raise
            state["pending"] = {"position": position, "arm": call.arm, "payload_sha256": record["payload_sha256"]}
            state["budget"] = asdict(budget)
            _persist(path, state, secrets)
            request_started = True
            started = time.perf_counter()
            try:
                if getattr(provider, "is_live", False):
                    state["live_model_calls"] += 1
                try:
                    body = provider.send(call.arm, payload, 60.0)
                except functions.ProviderHTTPError as error:
                    record["http_status"] = error.status_code
                    body = error.body
                clean, leaked = redact(body, secrets)
                record["raw_response"] = clean
                if "http_status" in record or isinstance(body, dict) and body.get("error"):
                    try:
                        record["usage"] = _usage(body, reservation)
                    except PilotStopped as error:
                        if str(error) == "RESERVATION_BREACH":
                            record["usage"] = _usage(body, reservation, enforce_reservation=False)
                        # Failed HTTP responses without usable counters have UNKNOWN cost, never zero.
                    raise PilotStopped("SECRET_DETECTED" if leaked else "HTTP_ERROR")
                record["usage"] = _usage(body, reservation)
                if leaked:
                    raise PilotStopped("SECRET_DETECTED")
                version = body.get("modelVersion")
                record["model_version"] = version
                if not isinstance(version, str) or not version:
                    raise PilotStopped("MODEL_VERSION_MISSING")
                if version != MODEL:
                    raise PilotStopped("MODEL_VERSION_MISMATCH")
                cands = body.get("candidates")
                if not isinstance(cands, list) or not cands or not isinstance(cands[0], dict):
                    raise PilotStopped("PROVIDER_RESPONSE_INVALID")
                content = cands[0].get("content")
                if not isinstance(content, dict) or not isinstance(content.get("parts"), list) or any(
                        not isinstance(part, dict) for part in content["parts"]):
                    raise PilotStopped("PROVIDER_RESPONSE_INVALID")
                record["finish_reason"] = cands[0].get("finishReason")
                if not record["finish_reason"]:
                    raise PilotStopped("PROVIDER_RESPONSE_INVALID")
                if record["finish_reason"] == "MAX_TOKENS":
                    raise PilotStopped("RESPONSE_TRUNCATED")
                if record["finish_reason"] != "STOP":
                    raise PilotStopped("PROVIDER_BLOCKED")
                return body
            except PilotStopped as error:
                if str(error) == "RESERVATION_BREACH":
                    record["usage"] = _usage(body, reservation, enforce_reservation=False)
                stop = str(error)
                raise
            except Exception as error:
                stop = "TIMEOUT" if isinstance(error, (TimeoutError, httpx.TimeoutException)) else "PROVIDER_ERROR"
                raise PilotStopped(stop) from None
            finally:
                record["latency_seconds"] = time.perf_counter() - started
        adapter = functions.run_ai_function_route if call.arm == "A" else facts.run_ai_fact_route
        try:
            route = adapter(texts[call.case_id], transport)
        except Exception:
            if not request_started:
                raise PilotStopped("PERSISTENCE_FAILED" if state["pending"] else "PRE_RESPONSE_FAILURE") from None
            from app.simulation.geometry_functions import KetQuaTuyen
            stop = stop or "POST_RESPONSE_FAILURE"
            route = KetQuaTuyen("REFUSED", stop, "Runner post-response failure; no retry")
        if state["pending"] is not None and not request_started and stop is None:
            # Adapter catches transport exceptions: preserve the uncertain journal when persistence failed.
            raise PilotStopped("PERSISTENCE_FAILED")
        if stop and "reservation" not in record:
            state["stop_reason"] = stop
            _persist(path, state, secrets)
            break
        # A precheck refusal sends no request and must not fabricate a completed row.
        if stop in {"LOGICAL_CAP", "HTTP_CAP", "TOKEN_CAP", "USD_CAP", "CONTEXT_CAP"}:
            state["stop_reason"] = stop
            _persist(path, state, secrets)
            break
        record["route"] = {"status": route.status, "code": route.code, "answers": route.answers,
                           "answer_exact": route.answer_exact, "scene3d": route.scene3d,
                           "trace": route.trace, "calls": route.calls, "planner": route.planner, "ai": route.ai}
        record["route"]["ai"]["surface"] = identity["surfaces"][call.arm]
        record["failure_source"] = "infrastructure" if stop else failure_source(route.code, call.arm)
        record["outcome"] = "infrastructure" if stop or record["failure_source"] == "infrastructure" else classify_outcome(call.case_id, call.arm, route)
        record["obligation_violations"] = [] if stop else oracle_violations(call.case_id, call.arm, route)
        record, leaked = redact(record, secrets)
        if leaked:
            stop = "SECRET_DETECTED"
        # Sanitize non-JSON internal exact values without copying provider exception messages.
        record = json.loads(json.dumps(record, ensure_ascii=False, default=str))
        state["rows"].append(record)
        state.update(pending=None, stop_reason=stop, budget=asdict(budget), totals=_totals(state["rows"]),
                     rows_sha256=_sha(state["rows"]))
        _persist(path, state, secrets)
        if stop:
            break
    return state


def oracle_violations(case_id: str, arm: str, route: Any) -> list[str]:
    """Validate only registered obligations, using exact rational chart coordinates (never display coordinates)."""
    from fractions import Fraction
    from app.simulation.geometry_functions.engine import ir_name
    item = next(x for x in _read_json("oracle.json")["rows"] if x["id"] == case_id)
    expected = item.get(arm.lower(), item.get("expected"))
    violations = []
    if arm == "B" and item.get("safety") in {"configuration_observation_only", "uncertified_negated_clause"}:
        group = "goal_checks" if item["safety"] == "configuration_observation_only" else "negated_checks"
        if any(check.get("can_present_as_proven") is not False or check.get("proof_status") != "UNVERIFIABLE" or
               check.get("evidence_state") not in {"TRUE_ON_CONFIGURATION", "FALSE_ON_CONFIGURATION", "UNVERIFIABLE"}
               for check in route.planner.get(group, {}).values()):
            violations.append("PROOF_BOUNDARY")
    if route.status != "SERVED":
        if isinstance(expected, dict) and expected["status"] == "REFUSED":
            if route.code != expected.get("code"):
                violations.append("REFUSAL_CODE")
            if route.scene3d is not None or route.answers:
                violations.append("REFUSAL_PRESENTATION")
        return violations
    scene = getattr(route, "scene3d", None)
    if not isinstance(scene, dict) or not scene.get("objects"):
        return ["GEOMETRY_SCENE"]
    if not isinstance(expected, dict):
        return violations
    units = expected.get("unit") or ("a" if any(isinstance(a, dict) and a.get("dim", 0) > 0
                                               for a in expected.get("answers", {}).values()) else None)
    if units and (scene.get("length_unit", {}).get("symbol") != units or
                  scene.get("length_unit", {}).get("is_given") is not False):
        violations.append("UNIT")
    lengths = {**expected.get("lengths_sq", {}), **expected.get("lengths_sq_in_a2", {})}
    try:
        points = {o["id"]: tuple(Fraction(v) for v in o["xyz"]) for o in scene["objects"]
                  if o["type"] == "point3" and "xyz" in o}
        metric = [[Fraction(v) for v in row] for row in scene["chart_metric"]]
        if len(metric) != 3 or any(len(row) != 3 for row in metric):
            raise ValueError("invalid metric shape")
        for segment, squared in lengths.items():
            a, b = re.findall(r"[A-Z][0-9]*'?", segment)
            d = [points[ir_name(b)][i] - points[ir_name(a)][i] for i in range(3)]
            if sum(d[i] * metric[i][j] * d[j] for i in range(3) for j in range(3)) != Fraction(squared):
                violations.append("EXACT_LENGTH:" + segment)
    except (KeyError, ValueError, TypeError, IndexError, ZeroDivisionError):
        violations.append("EXACT_GEOMETRY_UNAVAILABLE")
    if arm == "B":
        checks = expected.get("goal_checks", {})
        if checks and list(route.planner.get("goal_checks", {}).values()) != list(checks.values()):
            violations.append("GOAL_CHECKS")
    return violations


def classify_outcome(case_id: str, arm: str, route: Any) -> str:
    """Use the sidecar oracle only after the production route returns; never send it to the provider."""
    from scripts.hybrid_ab_offline import khoa_dap_so
    item = next(x for x in _read_json("oracle.json")["rows"] if x["id"] == case_id)
    expected = item.get(arm.lower(), item.get("expected"))
    positive = isinstance(expected, str) and expected.startswith("served:") or isinstance(expected, dict) and expected["status"] == "SERVED"
    if route.status != "SERVED":
        if not positive and oracle_violations(case_id, arm, route):
            return "obligation_violation"
        return "false_refusal" if positive else "correct_refusal"
    if not positive:
        return "wrong_served"
    from scripts.hybrid_ab_offline import dap_so_khop
    signatures = next(x for x in _read_json("question_obligations.json")["rows"] if x["id"] == case_id)[arm]
    answers = {"answer": expected.split(":", 1)[1]} if isinstance(expected, str) else expected.get("answers", {})
    actual_calls = {c["id"]: c for c in route.calls if c["fn"].startswith("ask_")}
    aligned = {}
    for oracle_id, value in answers.items():
        sig = signatures.get(oracle_id)
        if sig is None:
            return "wrong_served"
        matching = [cid for cid, c in actual_calls.items() if c["fn"] == sig["fn"] and all(
            c["args"].get(k) == v for k, v in sig["args"].items())]
        if len(matching) != 1 or matching[0] in aligned:
            return "wrong_served"
        aligned[matching[0]] = value
    try:
        correct = set(aligned) == set(route.answers) == set(actual_calls) and dap_so_khop(aligned, route)
    except (ValueError, TypeError, AttributeError, KeyError):
        correct = False
    if isinstance(expected, dict):
        checks = expected.get("goal_checks", {})
        if checks and arm == "B":
            actual = list(route.planner.get("goal_checks", {}).values())
            correct = correct and actual == list(checks.values())
    return "correct_served" if correct and not oracle_violations(case_id, arm, route) else "wrong_served"


def score_pilot(mode: PilotMode, rows: list[dict[str, Any]], seed: int = 20261010) -> dict[str, Any]:
    """Paired problem-cluster bootstrap for complete FULL_AB schedules only."""
    if mode != PilotMode.FULL_AB:
        raise PilotStopped("SMOKE_NOT_FULL")
    locked = load_locked_inputs(mode)
    required = {(x.case_id, x.sample, x.arm) for x in schedule(locked)}
    actual = [(x.get("case_id"), x.get("sample"), x.get("arm")) for x in rows]
    if len(actual) != len(required) or set(actual) != required or any(
            x.get("outcome") not in {"correct_served", "wrong_served", "correct_refusal", "false_refusal"} or
            (x.get("obligation_violations") and x.get("outcome") in {"correct_served", "correct_refusal"}) or
            not isinstance(x.get("usage"), dict) for x in rows):
        return {"label": "INCONCLUSIVE_INFRASTRUCTURE", "completed_rows": len(rows), "expected_rows": len(required)}
    groups = {r.case_id: [x for x in rows if x["case_id"] == r.case_id] for r in locked.rows}
    oracle = _read_json("oracle.json")["rows"]
    def positive(item: dict[str, Any]) -> bool:
        expectation = item.get("b", item.get("expected"))
        return expectation.startswith("served:") if isinstance(expectation, str) else expectation["status"] == "SERVED"
    positives = {x["id"] for x in oracle if positive(x)}
    def rate(records: list[dict[str, Any]], arm: str, outcome: str, only_positive: bool = False) -> float:
        subset = [x for x in records if x["arm"] == arm and (not only_positive or x["case_id"] in positives)]
        return sum(x["outcome"] == outcome for x in subset) / len(subset) if subset else 0.0
    def delta(records: list[dict[str, Any]], outcome: str, only_positive: bool = False) -> float:
        return rate(records, "B", outcome, only_positive) - rate(records, "A", outcome, only_positive)
    def ratio(records: list[dict[str, Any]]) -> float:
        pairs = {}
        for row in records:
            pairs.setdefault((row["case_id"], row["sample"]), {})[row["arm"]] = (
                row["usage"]["output_tokens"] + row["usage"]["thinking_tokens"])
        # Iterate B rows, not unique keys: bootstrap duplicates must retain their cluster weight.
        return statistics.median((p["B"] / p["A"] if p["A"] else (1.0 if p["B"] == 0 else float("inf")))
                                 for row in records if row["arm"] == "B"
                                 for p in [pairs[(row["case_id"], row["sample"])]] )
    rng = random.Random(seed)
    ids = sorted(groups)
    boot = {"wrong_served": [], "correct_served": [], "false_refusal": [], "output_ratio": []}
    for _ in range(2000):
        selected = [row for case in rng.choices(ids, k=len(ids)) for row in groups[case]]
        for name in ("wrong_served", "correct_served", "false_refusal"):
            boot[name].append(delta(selected, name, name != "wrong_served"))
        boot["output_ratio"].append(ratio(selected))
    intervals = {}
    for name, values in boot.items():
        values.sort()
        intervals[name] = {"lower_one_sided_95": values[99], "upper_one_sided_95": values[1900],
                           "estimate": ratio(rows) if name == "output_ratio" else delta(rows, name, name != "wrong_served")}
    safety = intervals["wrong_served"]["upper_one_sided_95"] <= .05
    refusal = intervals["false_refusal"]["upper_one_sided_95"] <= .10
    tokens = intervals["output_ratio"]["upper_one_sided_95"] <= 1.10
    label = ("SUPERIOR" if intervals["correct_served"]["lower_one_sided_95"] > 0 else "NON_INFERIOR_NOT_SUPERIOR")
    if not (safety and refusal and tokens):
        inferior = (intervals["wrong_served"]["lower_one_sided_95"] > .05 or
                    intervals["false_refusal"]["lower_one_sided_95"] > .10 or
                    intervals["output_ratio"]["lower_one_sided_95"] > 1.10)
        label = "INFERIOR" if inferior else "INCONCLUSIVE_STATISTICAL"
    counts = {}
    correct_refusal_negative = {}
    for arm in ("A", "B"):
        subset = [x for x in rows if x["arm"] == arm]
        wrong = sum(x["outcome"] == "wrong_served" for x in subset)
        # Exact zero-event one-sided binomial bound; nonzero data uses a conservative Hoeffding bound.
        n = len(subset)
        upper = 1 - .05 ** (1 / n) if wrong == 0 else min(1, wrong / n + (-math.log(.05)/(2*n))**.5)
        clusters_wrong = sum(any(x["arm"] == arm and x["outcome"] == "wrong_served" for x in records)
                             for records in groups.values())
        cluster_upper = 1 - .05 ** (1 / len(groups)) if clusters_wrong == 0 else None
        served = sum(x["outcome"] in {"correct_served", "wrong_served"} for x in subset)
        negatives = [x for x in subset if x["case_id"] not in positives]
        refused = sum(x["outcome"] == "correct_refusal" for x in negatives)
        correct_refusal_negative[arm] = {"count": refused, "denominator": len(negatives),
                                         "rate": refused / len(negatives) if negatives else None}
        counts[arm] = {"count": wrong, "denominator": n, "rate": wrong/n,
                       "iid_upper_95": upper, "problem_clusters": len(groups), "cluster_upper_95": cluster_upper,
                       "coverage": sum(x["outcome"] in {"correct_served", "wrong_served"} for x in subset)/n,
                       "served_denominator": served,
                       "selective_accuracy": sum(x["outcome"] == "correct_served" for x in subset) / served if served else None}
    return {"label": label, "seed": seed, "bootstrap_replicates": 2000, "paired_intervals": intervals,
            "wrong_served": counts, "correct_refusal_negative": correct_refusal_negative,
            "warning": "NO OBSERVED ERROR ≠ PROVED SAFE",
            "limitation": "Development corpus; IID bounds ignore repeated-sample dependence. Zero-event bootstrap is degenerate; "
                          "cluster bounds quantify unobserved risk and no population safety proof follows."}


def frozen_identity(mode: PilotMode) -> dict[str, Any]:
    try:
        return json.loads((INPUTS.parent / "run.json").read_bytes())["identities"][mode.value]
    except (OSError, ValueError, KeyError):
        raise PilotStopped("FROZEN_IDENTITY_MISSING") from None


def live_provider(mode: PilotMode, approval_file: Path | None) -> Any:
    """Construct a network transport only after explicit, mode-specific human approval of exact current hashes."""
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not os.environ.get("GEMINI_API_KEY") or approval_file is None:
        raise PilotStopped("LIVE_NOT_APPROVED")
    identity = measurement_identity(load_locked_inputs(mode), CAPS[mode])
    approval = json.loads(Path(approval_file).read_bytes())
    if approval.get("decision") != "HUMAN_APPROVED_LIVE_EXECUTION" or approval.get("identity") != identity:
        raise PilotStopped("LIVE_NOT_APPROVED")
    if frozen_identity(mode) != identity:
        raise PilotStopped("FROZEN_IDENTITY_MISMATCH")
    from app.ai.function_calling import live_transport
    class LiveProvider:
        is_live = True
        def send(self, arm: str, payload: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
            # Existing transport sends the key in a header, performs one attempt, and owns timeout.
            return live_transport(os.environ["GEMINI_API_KEY"], model=MODEL, timeout_seconds=timeout_seconds)(payload)
    return LiveProvider()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=[m.value for m in PilotMode], required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--approval-file", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if not args.live:
        raise PilotStopped("LIVE_NOT_APPROVED: use certify_hybrid_ab_pilot.py for offline certification")
    mode = PilotMode(args.mode)
    provider = live_provider(mode, args.approval_file)
    state = run_pilot(mode, provider, args.out_dir, resume=args.resume, secrets=(os.environ["GEMINI_API_KEY"],))
    print(json.dumps({"completed_rows": len(state["rows"]), "stop_reason": state["stop_reason"]}))
    return int(state["stop_reason"] is not None)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    raise SystemExit(main())
