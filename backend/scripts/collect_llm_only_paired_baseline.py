# -*- coding: utf-8 -*-
"""Apparatus thu thập baseline LLM_ONLY ghép cặp ngoại tuyến (Phase 5).

Nguyên tắc bất biến:
- PRIMARY_ARCHITECTURE_ISOLATED_EVALUATION: Cả hai nhánh dùng cùng RequestContract (COMMON_INPUT).
- SHARED_ANALYZE_REQUESTS = 0 (không gọi lại tầng Analyze).
- PLANNED_OBSERVATIONS_PER_CASE = 3, RETRIES_PER_OBSERVATION = 0.
- ABSOLUTE_REQUEST_CAP = 54 (18 cases x 3 observations).
- Tuyệt đối không gọi Analyze, Vision hoặc Repair.
- Giao thức ghi bền vững: temp file -> flush -> fsync -> atomic replace -> read-back verify.
- Raw responses được ghi ra ngoài repository; không commit raw response.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REGISTRY_PATH = REPO_ROOT / "docs" / "research" / "llm_only_paired_baseline_registry.json"

MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.1
TIMEOUT_SECONDS = 120.0
MAX_OBSERVATIONS_PER_CASE = 3
TOTAL_EXPECTED_CASES = 18
ABSOLUTE_REQUEST_CAP = 54


class BaselineCollectorError(Exception):
    """Lỗi chung của collector apparatus."""


class BudgetExceededError(BaselineCollectorError):
    """Vượt quá ngân sách request cho phép."""


class SecurityViolationError(BaselineCollectorError):
    """Vi phạm quy tắc bảo mật hoặc an toàn repository."""


class DurableWriteError(BaselineCollectorError):
    """Lỗi trong giao thức ghi tệp bền vững."""


class DuplicateExecutionError(BaselineCollectorError):
    """Yêu cầu thực thi trùng lặp case và observation."""


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize đối tượng sang bytes JSON chuẩn tắc (deterministic)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(obj: Any) -> str:
    """Tính SHA-256 của biểu diễn JSON chuẩn tắc."""
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def durable_atomic_write(target_path: Path, data: bytes) -> tuple[int, str]:
    """Ghi tệp bền vững theo giao thức:

    temp file -> flush -> fsync -> os.replace -> read-back byte count & SHA-256 verify.
    """
    target_path = Path(target_path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = target_path.with_name(f"{target_path.name}.tmp.{uuid.uuid4().hex}")
    expected_bytes = len(data)
    expected_hash = hashlib.sha256(data).hexdigest()

    try:
        with open(temp_path, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, target_path)

        # Read-back verification
        with open(target_path, "rb") as f:
            read_data = f.read()

        actual_bytes = len(read_data)
        actual_hash = hashlib.sha256(read_data).hexdigest()

        if actual_bytes != expected_bytes:
            raise DurableWriteError(
                f"Byte count mismatch: expected {expected_bytes}, got {actual_bytes} at {target_path}"
            )
        if actual_hash != expected_hash:
            raise DurableWriteError(
                f"SHA-256 mismatch: expected {expected_hash}, got {actual_hash} at {target_path}"
            )

        return actual_bytes, actual_hash

    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def validate_registry_content(registry_data: dict[str, Any]) -> dict[str, Any]:
    """Kiểm tra tính hợp lệ và bất biến của registry dữ liệu."""
    invariants = registry_data.get("invariants", {})
    cases = registry_data.get("cases", [])

    if len(cases) != TOTAL_EXPECTED_CASES:
        raise BaselineCollectorError(
            f"Expected exactly {TOTAL_EXPECTED_CASES} cases, got {len(cases)}"
        )

    case_ids = [c["case_id"] for c in cases]
    if len(set(case_ids)) != len(case_ids):
        raise BaselineCollectorError("Duplicate case IDs found in registry")

    # Budget arithmetic
    planned_obs = invariants.get("planned_observations_per_case", 3)
    planned_requests = invariants.get("planned_live_synthesis_requests", 0)
    cap = invariants.get("absolute_request_cap", 0)

    if planned_obs != MAX_OBSERVATIONS_PER_CASE:
        raise BaselineCollectorError(f"planned_observations_per_case must be {MAX_OBSERVATIONS_PER_CASE}")
    if planned_requests != TOTAL_EXPECTED_CASES * MAX_OBSERVATIONS_PER_CASE:
        raise BaselineCollectorError(f"planned_live_synthesis_requests must be {TOTAL_EXPECTED_CASES * MAX_OBSERVATIONS_PER_CASE}")
    if cap != ABSOLUTE_REQUEST_CAP:
        raise BaselineCollectorError(f"absolute_request_cap must be {ABSOLUTE_REQUEST_CAP}")
    if invariants.get("shared_analyze_requests") != 0:
        raise BaselineCollectorError("shared_analyze_requests must be 0")
    if invariants.get("retries_per_observation") != 0:
        raise BaselineCollectorError("retries_per_observation must be 0")

    # Audit each case
    for case in cases:
        if not case.get("parse_valid"):
            raise BaselineCollectorError(f"Case {case['case_id']} parse_valid is not True")
        if case.get("leakage_check") != "PASS":
            raise BaselineCollectorError(f"Case {case['case_id']} leakage_check is not PASS")
        if case.get("expected_execution_path") != "REACHES_LLM_SYNTHESIS":
            raise BaselineCollectorError(f"Case {case['case_id']} expected_execution_path must be REACHES_LLM_SYNTHESIS")

        # Verify canonical contract SHA-256
        contract_obj = case.get("canonical_request_contract")
        if contract_obj is None:
            raise BaselineCollectorError(f"Case {case['case_id']} missing canonical_request_contract")
        computed_contract_hash = canonical_sha256(contract_obj)
        if computed_contract_hash != case.get("canonical_request_contract_sha256"):
            raise BaselineCollectorError(f"Contract hash mismatch for {case['case_id']}")

    return {
        "status": "VALID",
        "case_count": len(cases),
        "total_requests_budgeted": planned_requests,
        "cap": cap,
    }


@dataclass
class CollectorSession:
    """Theo dõi phiên thu thập để đảm bảo ngân sách và ngăn chặn duplicate."""

    request_count: int = 0
    executed_pairs: set[tuple[str, int]] = field(default_factory=set)
    recorded_observations: list[dict[str, Any]] = field(default_factory=list)

    def register_request(self, case_id: str, obs_index: int, stage: str = "semantic_program") -> None:
        if stage != "semantic_program":
            raise SecurityViolationError(f"Forbidden stage requested: {stage}. Only 'semantic_program' permitted.")

        pair = (case_id, obs_index)
        if pair in self.executed_pairs:
            raise DuplicateExecutionError(f"Duplicate execution attempted for {pair}")

        if self.request_count >= ABSOLUTE_REQUEST_CAP:
            raise BudgetExceededError(
                f"Absolute request cap ({ABSOLUTE_REQUEST_CAP}) reached. Cannot execute {pair}."
            )

        self.executed_pairs.add(pair)
        self.request_count += 1


async def execute_single_observation(
    client: httpx.AsyncClient,
    session: CollectorSession,
    case: dict[str, Any],
    obs_index: int,
    output_dir: Path,
    api_key: str,
    stage: str = "semantic_program",
) -> dict[str, Any]:
    """Thực thi một quan sát đơn lẻ với chính sách NO-RETRY và ghi bền vững."""
    case_id = case["case_id"]
    binding = case["request_binding"]

    session.register_request(case_id, obs_index, stage=stage)

    # Build URL without exposing API key in logs
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

    # Reconstruct request body from binding parameters
    from app.ai.gemini import load_skill, _sanitize_gemini_schema
    from app.simulation.semantic_program.contract import generate_json_schema
    from app.simulation.semantic_program.grammar_card import grammar_card
    from app.ai.pipeline import _facts_for_prompt, _obligations_for_prompt
    from app.simulation.semantic_program.request_contract import RequestContract

    contract = RequestContract.model_validate(case["canonical_request_contract"])
    text = case["input_text"]
    skill_content = load_skill("geometry_program_generator")
    schema = _sanitize_gemini_schema(generate_json_schema())
    card = grammar_card("hinh_hoc")

    base = f'Đề bài:\n"""\n{text}\n"""'
    base = f"{base}\n\n{_facts_for_prompt(contract)}"
    base = f"{base}\n\n{_obligations_for_prompt(contract)}"
    base = f"{base}\n\n{card}"

    request_body = {
        "contents": [{"parts": [{"text": base}], "role": "user"}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": TEMPERATURE,
        },
        "systemInstruction": {"parts": [{"text": skill_content}]},
    }

    # Verify deterministic body hash matches pre-registered binding
    body_bytes = canonical_json_bytes(request_body)
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    if body_hash != binding["canonical_request_body_sha256"]:
        raise BaselineCollectorError(
            f"Request body hash mismatch for {case_id}: computed {body_hash} vs preregistered {binding['canonical_request_body_sha256']}"
        )

    # Perform exactly 1 request (NO RETRY)
    res = await client.post(url, json=request_body)

    # Handle status
    status_code = res.status_code
    response_content = res.content

    # Durable write raw response to external dir
    obs_file = output_dir / f"{case_id}_obs_{obs_index}_raw.json"
    written_bytes, written_hash = durable_atomic_write(obs_file, response_content)

    obs_record: dict[str, Any] = {
        "case_id": case_id,
        "observation_index": obs_index,
        "http_status": status_code,
        "raw_response_bytes": written_bytes,
        "raw_response_sha256": written_hash,
        "raw_artifact_file": str(obs_file.resolve()),
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "request_body_sha256": body_hash,
    }

    if status_code != 200:
        obs_record["error"] = f"HTTP_{status_code}"
        obs_record["error_detail"] = res.text[:300]
        return obs_record

    # Parse and validate response JSON
    try:
        data = res.json()
        obs_record["json_parse_status"] = "PASS"
        # Extract candidate text
        candidates = data.get("candidates", [])
        if not candidates:
            obs_record["schema_parse_status"] = "EMPTY_CANDIDATES"
        else:
            first = candidates[0]
            parts = first.get("content", {}).get("parts", [])
            if parts and "text" in parts[0]:
                raw_text = parts[0]["text"]
                obs_record["candidate_text_sha256"] = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
                try:
                    payload = json.loads(raw_text)
                    from app.simulation.semantic_program.validator import validate_semantic_program
                    val = validate_semantic_program(payload)
                    obs_record["schema_parse_status"] = "PASS" if val.ok else "VALIDATION_FAIL"
                    obs_record["validator_error"] = val.error
                except Exception as ex:
                    obs_record["schema_parse_status"] = "JSON_PARSE_FAIL"
                    obs_record["validator_error"] = str(ex)
            else:
                obs_record["schema_parse_status"] = "NO_TEXT_PART"
    except Exception as ex:
        obs_record["json_parse_status"] = "FAIL"
        obs_record["error"] = str(ex)

    return obs_record


def run_dry_run(registry_path: Path) -> dict[str, Any]:
    """Chế độ --dry-run: Không tải API key, không gọi mạng, kiểm tra toàn bộ registry & budget."""
    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    audit = validate_registry_content(registry_data)
    cases = registry_data["cases"]

    print("=== DRY RUN AUDIT PASSED ===")
    print(f"Registry: {registry_path}")
    print(f"Total Cases: {audit['case_count']}")
    print(f"Planned Live Synthesis Requests: {audit['total_requests_budgeted']}")
    print(f"Absolute Request Cap: {audit['cap']}")
    print("Invariants Verified:")
    print("  - NETWORK_REQUESTS = 0")
    print("  - GEMINI_REQUESTS = 0")
    print("  - API_KEY_LOADED = NO")
    print("  - SHARED_ANALYZE_REQUESTS = 0")
    print("  - NO_RETRY_RULE = ENFORCED")
    print(f"  - FORBIDDEN_STAGES = {registry_data['invariants']['forbidden_stages']}")
    print("============================")

    return {
        "status": "DRY_RUN_SUCCESS",
        "case_count": audit["case_count"],
        "planned_requests": audit["total_requests_budgeted"],
        "cap": audit["cap"],
    }


async def run_live_collection(
    registry_path: Path,
    output_dir: Path,
    api_key: str,
    confirmation: bool,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    """Chế độ --execute-live (chỉ dùng khi có cờ xác nhận, ghi ngoài repo)."""
    if not confirmation:
        raise SecurityViolationError(
            "Live execution rejected: missing explicit confirmation flag (--confirm-live-execution)"
        )

    output_dir = Path(output_dir).resolve()
    # Check that output_dir is outside repo root (safety invariant)
    try:
        if output_dir.is_relative_to(REPO_ROOT):
            raise SecurityViolationError(
                f"Output directory {output_dir} must be OUTSIDE repository root {REPO_ROOT}"
            )
    except AttributeError:
        # Python < 3.9 fallback
        if str(output_dir).startswith(str(REPO_ROOT)):
            raise SecurityViolationError(
                f"Output directory {output_dir} must be OUTSIDE repository root {REPO_ROOT}"
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    validate_registry_content(registry_data)
    cases = registry_data["cases"]

    session = CollectorSession()
    client_kwargs: dict[str, Any] = {"timeout": TIMEOUT_SECONDS}
    if transport is not None:
        client_kwargs["transport"] = transport

    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(**client_kwargs) as client:
        for case in cases:
            for obs_idx in [1, 2, 3]:
                obs_res = await execute_single_observation(
                    client=client,
                    session=session,
                    case=case,
                    obs_index=obs_idx,
                    output_dir=output_dir,
                    api_key=api_key,
                )
                results.append(obs_res)

    summary = {
        "status": "LIVE_COLLECTION_COMPLETED",
        "total_executed_requests": session.request_count,
        "observations_collected": len(results),
        "output_directory": str(output_dir),
    }

    # Write summary manifest durably inside output_dir
    summary_bytes = canonical_json_bytes({"summary": summary, "results": results})
    durable_atomic_write(output_dir / "collection_summary.json", summary_bytes)

    return summary


def main():
    parser = argparse.ArgumentParser(description="LLM_ONLY Paired Baseline Collector")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH, help="Path to baseline registry JSON")
    parser.add_argument("--dry-run", action="store_true", help="Perform offline audit without network or API key")
    parser.add_argument("--execute-live", action="store_true", help="Execute live collection (requires confirmation)")
    parser.add_argument("--confirm-live-execution", action="store_true", help="Explicit confirmation for live execution")
    parser.add_argument("--output-dir", type=Path, help="External directory to save raw responses")
    parser.add_argument("--api-key", type=str, default=None, help="Gemini API key for live execution")

    args = parser.parse_args()

    if args.dry_run:
        res = run_dry_run(args.registry)
        sys.exit(0)
    elif args.execute_live:
        api_key = args.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: API key required for live execution", file=sys.stderr)
            sys.exit(1)
        if not args.output_dir:
            print("ERROR: --output-dir required for live execution", file=sys.stderr)
            sys.exit(1)
        try:
            res = asyncio.run(
                run_live_collection(
                    registry_path=args.registry,
                    output_dir=args.output_dir,
                    api_key=api_key,
                    confirmation=args.confirm_live_execution,
                )
            )
            print("Live collection completed:", res)
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
