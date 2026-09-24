# -*- coding: utf-8 -*-
"""Kiểm thử apparatus thu thập baseline LLM_ONLY bằng Fake Transport (Phase 5).

Bao phủ các kịch bản:
- --dry-run an toàn ngoại tuyến (0 network, 0 Gemini, 0 API key)
- HTTP 200 hợp lệ
- schema parse failure
- HTTP 400
- HTTP 429
- HTTP 500
- timeout
- partial write
- hash mismatch
- request-budget overflow (trần 54)
- accidental Analyze/Vision/Repair request
- duplicate case/observation execution
- output dir an toàn ngoài repository
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from scripts.collect_llm_only_paired_baseline import (
    ABSOLUTE_REQUEST_CAP,
    DEFAULT_REGISTRY_PATH,
    BaselineCollectorError,
    BudgetExceededError,
    CollectorSession,
    DuplicateExecutionError,
    DurableWriteError,
    SecurityViolationError,
    durable_atomic_write,
    execute_single_observation,
    run_dry_run,
    run_live_collection,
    validate_registry_content,
)


@pytest.fixture
def sample_registry_data():
    with open(DEFAULT_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_output_dir(tmp_path_factory):
    # Tạo thư mục ngoài REPO_ROOT (dùng thư mục tạm của hệ thống)
    return tmp_path_factory.mktemp("external_baseline_raw")


def test_dry_run_offline_safe():
    """Kiểm tra --dry-run chạy thành công hoàn toàn ngoại tuyến không tải API key."""
    res = run_dry_run(DEFAULT_REGISTRY_PATH)
    assert res["status"] == "DRY_RUN_SUCCESS"
    assert res["case_count"] == 18
    assert res["planned_requests"] == 54
    assert res["cap"] == 54


def test_durable_atomic_write_success(tmp_path):
    """Ghi bền vững thành công và khớp byte count + SHA-256."""
    target = tmp_path / "subdir" / "test_file.json"
    content = b'{"hello": "world"}'
    written_bytes, sha = durable_atomic_write(target, content)

    assert target.exists()
    assert written_bytes == len(content)
    assert target.read_bytes() == content


def test_durable_atomic_write_partial_write_failure(tmp_path):
    """Phát hiện lỗi cắt cụt khi số byte đọc lại không khớp."""
    target = tmp_path / "partial.json"
    content = b"very_long_content_to_be_truncated"

    # Giả lập ghi thiếu byte
    original_replace = collect_replace = __import__("os").replace

    def corrupt_replace(src, dst):
        # Ghi đè file src với nội dung bị cắt
        with open(src, "wb") as f:
            f.write(content[:5])
        original_replace(src, dst)

    with patch("os.replace", side_effect=corrupt_replace):
        with pytest.raises(DurableWriteError, match="Byte count mismatch"):
            durable_atomic_write(target, content)


def test_durable_atomic_write_hash_mismatch_failure(tmp_path):
    """Phát hiện lỗi sai băm SHA-256 khi đọc lại."""
    target = tmp_path / "corrupt_hash.json"
    content = b"original_correct_content"

    original_replace = __import__("os").replace

    def corrupt_replace(src, dst):
        with open(src, "wb") as f:
            f.write(b"modified_tampered_content")
        original_replace(src, dst)

    with patch("os.replace", side_effect=corrupt_replace):
        with pytest.raises(DurableWriteError, match="(Byte count mismatch|SHA-256 mismatch)"):
            durable_atomic_write(target, content)


def test_fake_transport_http_200_valid(sample_registry_data, mock_output_dir):
    """Giả lập HTTP 200 trả về SemanticProgram hợp lệ."""
    valid_program = {
        "title": "Chương trình tính thể tích",
        "memory_declarations": [
            {"name": "v", "type": "float", "initial_value": 40.0, "source_fact_id": "day_vuong"}
        ],
        "statements": [],
    }
    payload_response = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(valid_program)}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 50, "totalTokenCount": 150},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload_response)

    transport = httpx.MockTransport(handler)
    session = CollectorSession()
    case = sample_registry_data["cases"][0]

    async def _run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await execute_single_observation(
                client=client,
                session=session,
                case=case,
                obs_index=1,
                output_dir=mock_output_dir,
                api_key="fake-test-key",
            )

    record = asyncio.run(_run())

    assert record["http_status"] == 200
    assert record["json_parse_status"] == "PASS"
    assert record["schema_parse_status"] == "PASS"
    assert Path(record["raw_artifact_file"]).exists()
    assert session.request_count == 1


def test_fake_transport_schema_parse_failure(sample_registry_data, mock_output_dir):
    """Giả lập HTTP 200 nhưng model trả về JSON cụt/hỏng (schema failure)."""
    payload_response = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": '{"broken_json": '}],
                    "role": "model",
                }
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload_response)

    transport = httpx.MockTransport(handler)
    session = CollectorSession()
    case = sample_registry_data["cases"][0]

    async def _run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await execute_single_observation(
                client=client,
                session=session,
                case=case,
                obs_index=1,
                output_dir=mock_output_dir,
                api_key="fake-test-key",
            )

    record = asyncio.run(_run())

    assert record["http_status"] == 200
    assert record["schema_parse_status"] == "JSON_PARSE_FAIL"
    assert session.request_count == 1  # No retry


def test_fake_transport_http_400(sample_registry_data, mock_output_dir):
    """Giả lập HTTP 400 (Bad Request)."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="Invalid argument: bad request")

    transport = httpx.MockTransport(handler)
    session = CollectorSession()
    case = sample_registry_data["cases"][0]

    async def _run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await execute_single_observation(
                client=client,
                session=session,
                case=case,
                obs_index=1,
                output_dir=mock_output_dir,
                api_key="fake-test-key",
            )

    record = asyncio.run(_run())

    assert record["http_status"] == 400
    assert record["error"] == "HTTP_400"
    assert session.request_count == 1  # No retry


def test_fake_transport_http_429(sample_registry_data, mock_output_dir):
    """Giả lập HTTP 429 (Rate Limit): Không retry trong baseline collection wave."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Resource exhausted")

    transport = httpx.MockTransport(handler)
    session = CollectorSession()
    case = sample_registry_data["cases"][0]

    async def _run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await execute_single_observation(
                client=client,
                session=session,
                case=case,
                obs_index=1,
                output_dir=mock_output_dir,
                api_key="fake-test-key",
            )

    record = asyncio.run(_run())

    assert record["http_status"] == 429
    assert record["error"] == "HTTP_429"
    assert session.request_count == 1


def test_fake_transport_http_500(sample_registry_data, mock_output_dir):
    """Giả lập HTTP 500 (Internal Server Error): Ghi nhận lỗi và không retry."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal server error")

    transport = httpx.MockTransport(handler)
    session = CollectorSession()
    case = sample_registry_data["cases"][0]

    async def _run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await execute_single_observation(
                client=client,
                session=session,
                case=case,
                obs_index=1,
                output_dir=mock_output_dir,
                api_key="fake-test-key",
            )

    record = asyncio.run(_run())

    assert record["http_status"] == 500
    assert record["error"] == "HTTP_500"
    assert session.request_count == 1


def test_fake_transport_timeout(sample_registry_data, mock_output_dir):
    """Giả lập TimeoutException: Không retry."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout reading from socket")

    transport = httpx.MockTransport(handler)
    session = CollectorSession()
    case = sample_registry_data["cases"][0]

    async def _run():
        async with httpx.AsyncClient(transport=transport) as client:
            await execute_single_observation(
                client=client,
                session=session,
                case=case,
                obs_index=1,
                output_dir=mock_output_dir,
                api_key="fake-test-key",
            )

    with pytest.raises(httpx.ReadTimeout):
        asyncio.run(_run())

    assert session.request_count == 1


def test_budget_overflow_prevention():
    """Chặn vượt trần ngân sách ABSOLUTE_REQUEST_CAP (54)."""
    session = CollectorSession()
    session.request_count = ABSOLUTE_REQUEST_CAP

    with pytest.raises(BudgetExceededError, match="Absolute request cap"):
        session.register_request("P01", 1)


def test_accidental_forbidden_stages_rejected():
    """Từ chối ngay lập tức bất kỳ lệnh gọi Analyze, Vision hoặc Repair."""
    session = CollectorSession()

    with pytest.raises(SecurityViolationError, match="Forbidden stage"):
        session.register_request("P01", 1, stage="semantic_analyze")

    with pytest.raises(SecurityViolationError, match="Forbidden stage"):
        session.register_request("P01", 1, stage="image_extraction")

    with pytest.raises(SecurityViolationError, match="Forbidden stage"):
        session.register_request("P01", 1, stage="repair")


def test_duplicate_case_observation_rejected():
    """Từ chối thực thi lặp lại cùng một ca và chỉ số quan sát."""
    session = CollectorSession()
    session.register_request("P01", 1)

    with pytest.raises(DuplicateExecutionError, match="Duplicate execution attempted"):
        session.register_request("P01", 1)


def test_unconfirmed_live_execution_rejected(mock_output_dir):
    """Từ chối live execution nếu thiếu cờ xác nhận rõ ràng."""
    with pytest.raises(SecurityViolationError, match="missing explicit confirmation"):
        asyncio.run(
            run_live_collection(
                registry_path=DEFAULT_REGISTRY_PATH,
                output_dir=mock_output_dir,
                api_key="test-key",
                confirmation=False,
            )
        )


def test_output_dir_inside_repo_rejected(tmp_path):
    """Từ chối ghi raw responses vào trong cây thư mục repository."""
    inside_dir = Path(__file__).resolve().parent / "forbidden_raw_output"

    with pytest.raises(SecurityViolationError, match="must be OUTSIDE repository"):
        asyncio.run(
            run_live_collection(
                registry_path=DEFAULT_REGISTRY_PATH,
                output_dir=inside_dir,
                api_key="test-key",
                confirmation=True,
            )
        )
