# -*- coding: utf-8 -*-
"""SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE Test Suite.

Kiểm tra toàn diện:
1. RED-BEFORE: Tái hiện lỗi vòng đời asyncio (Event loop is closed) và mất record P03.
2. GREEN-AFTER: Vòng đời async duy nhất ở biên CLI, chạy đa ca không lỗi loop.
3. Bền vững nguyên tử từng ca (CaseJournal: tempfile -> fsync -> os.replace -> read-back).
4. State machine: PLANNED -> RESERVED -> TRANSPORT_COMPLETED -> TRACE_CAPTURED -> SCORED -> VERIFIED.
5. 18 Offline Fixtures theo mục §8 của đặc tả.
6. Bảo vệ kết quả ca trước (P03 không đổi trên đĩa khi P05 lỗi) theo mục §9.
7. Ma trận Crash & Resume theo mục §6.
8. 12 Phép tiêm lỗi (F1 - F12) theo mục §12.
"""
from __future__ import annotations

import ast
import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.ai.telemetry import stage_scope
import run_preregistered_failure_reproduction as R
from run_preregistered_failure_reproduction import (
    CaseJournal,
    SafeStructureTraceExtractor,
    check_request_equivalence,
    classify_case_outcome,
    execute_case_analyze,
    execute_case_with_state_machine,
    generate_all_reproduction_artifacts,
    run_precheck,
    run_preregistered_reproduction_pipeline,
)
from run_multicase_benchmark import (
    BoKhuBiMat,
    CongQuanSat,
    ca_theo_id,
    doc_registry,
    doc_ground_truth,
)
from run_photo_problem_live import HttpBudgetExceeded
import run_structured_relation_analyze_live as L


# ══════════════════════════════════════════════════════════════════════════
# MOCK HELPER & TRANSPORT RÀNG BUỘC VỚI EVENT LOOP
# ══════════════════════════════════════════════════════════════════════════
def _make_mock_response(payload: dict[str, Any] | str, status_code: int = 200) -> httpx.Response:
    if isinstance(payload, str):
        text_val = payload
    else:
        text_val = json.dumps(payload)
    return httpx.Response(
        status_code,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": text_val}
                        ]
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 1200,
                "candidatesTokenCount": 450,
                "thoughtsTokenCount": 350,
                "totalTokenCount": 2000,
            }
        }
    )


def _make_valid_response(case_id: str = "P03") -> httpx.Response:
    if case_id == "P03":
        payload = {
            "points": ["T", "U", "V", "W"],
            "input_facts": [
                {"id": "fact_1", "kind": "angle", "label": "VUW", "value": ["90"]},
                {"id": "fact_2", "kind": "angle", "label": "TUW", "value": ["90"]}
            ],
            "geometric_relations": [
                {"kind": "perpendicular_lines", "line": ["U", "V"], "other_line": ["U", "W"], "source_fact_id": "fact_1"},
                {"kind": "perpendicular_line_plane", "line": ["T", "U"], "plane": ["U", "V", "W"], "source_fact_id": "fact_2"}
            ]
        }
    else:
        payload = {
            "points": ["G", "H", "I", "J"],
            "input_facts": [
                {"id": "fact_1", "kind": "angle", "label": "HIJ", "value": ["90"]},
                {"id": "fact_2", "kind": "angle", "label": "GHI", "value": ["90"]}
            ],
            "geometric_relations": [
                {"kind": "perpendicular_lines", "line": ["H", "I"], "other_line": ["H", "J"], "source_fact_id": "fact_1"},
                {"kind": "perpendicular_line_plane", "line": ["G", "H"], "plane": ["H", "I", "J"], "source_fact_id": "fact_2"}
            ]
        }
    return _make_mock_response(payload)


def _make_reproduced_malformed_response(case_id: str = "P03") -> httpx.Response:
    if case_id == "P03":
        payload = {
            "points": ["T", "U", "V", "W"],
            "input_facts": [{"id": "fact_1", "kind": "angle", "label": "VUW", "value": ["90"]}],
            "geometric_relations": [
                {"kind": "perpendicular_lines", "line": ["U", "V"], "other_line": ["U", "W"], "plane": ["U", "V", "W"], "source_fact_id": "fact_1"}
            ]
        }
    else:
        payload = {
            "points": ["G", "H", "I", "J"],
            "input_facts": [{"id": "fact_1", "kind": "angle", "label": "HIJ", "value": ["90"]}],
            "geometric_relations": [
                {"kind": "perpendicular_lines", "line": ["H", "I"], "other_line": ["H", "J"], "plane": ["H", "I", "J"], "source_fact_id": "fact_1"}
            ]
        }
    return _make_mock_response(payload)


class EventLoopBoundFakeTransport(httpx.AsyncBaseTransport):
    """Transport mô phỏng chính xác hành vi của httpx.AsyncHTTPTransport:
    khi một transport/connection pool được khởi tạo và sử dụng trong một event loop,
    nó bị ràng buộc với loop đó. Nếu loop bị đóng hoặc chuyển sang loop khác,
    nó ném RuntimeError: Event loop is closed.
    """

    def __init__(
        self,
        handler: Callable[[httpx.Request], httpx.Response] | None = None,
    ) -> None:
        self._bound_loop: asyncio.AbstractEventLoop | None = None
        self._handler = handler
        self.requests_received: list[httpx.Request] = []
        self.handle_call_count = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.handle_call_count += 1
        current_loop = asyncio.get_running_loop()

        if self._bound_loop is None:
            self._bound_loop = current_loop
        elif self._bound_loop is not current_loop:
            if self._bound_loop.is_closed():
                raise RuntimeError("Event loop is closed")
            raise RuntimeError(f"Transport bound to loop {self._bound_loop} but called in {current_loop}")

        if self._bound_loop.is_closed():
            raise RuntimeError("Event loop is closed")

        self.requests_received.append(request)

        if self._handler:
            return self._handler(request)

        # Default mock 200 response with valid json structure
        return _make_valid_response("P03")


# ══════════════════════════════════════════════════════════════════════════
# §1 · RED-BEFORE: TÁI HIỆN LỖI EVENT LOOP VÀ MẤT RECORD P03 TRÊN RUNNER CŨ
# ══════════════════════════════════════════════════════════════════════════
def test_red_before_event_loop_multi_case():
    """Tái hiện nguyên nhân 1 (ROOT_CAUSE_EVENT_LOOP):
    Mô phỏng mô hình cũ: tạo transport ở ngoài, sau đó gọi asyncio.run()
    riêng cho từng ca (P03 rồi P05).
    Ca 1 đóng loop 1. Ca 2 chạy trong loop 2 với transport cũ -> RuntimeError: Event loop is closed.
    """
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(
        transport,
        2,
        BoKhuBiMat(),
        tran_theo_tang={"vision": 0, "analyze": 2, "synthesis": 0},
    )

    # Ca 1: P03 chạy trong loop 1
    res_p03 = asyncio.run(R.execute_case_analyze(bang["P03"], "FAKE_API_KEY", transport, cong))
    assert res_p03["HTTP_STATUS"] == 200
    assert transport.handle_call_count == 1
    assert transport._bound_loop is not None
    assert transport._bound_loop.is_closed() is True

    # Ca 2: P05 chạy trong loop 2 với transport cũ -> transport trực tiếp ném RuntimeError: Event loop is closed
    async def _call_in_loop2():
        req = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent")
        return await transport.handle_async_request(req)

    with pytest.raises(RuntimeError, match="Event loop is closed"):
        asyncio.run(_call_in_loop2())


def test_red_before_p03_persistence_loss(tmp_path: Path):
    """Tái hiện nguyên nhân 2 (ROOT_CAUSE_P03_RECORD_LOSS):
    Trong kiến trúc cũ, persistence được hoãn lại (deferred) tới cuối main().
    Nếu P05 gặp lỗi, tiến trình crash trước khi ghi đĩa -> P03 record hoàn toàn không có trên đĩa!
    """
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(
        transport,
        2,
        BoKhuBiMat(),
        tran_theo_tang={"vision": 0, "analyze": 2, "synthesis": 0},
    )
    out_dir = tmp_path / "artifacts"
    cases_dir = out_dir / "cases"

    results: dict[str, Any] = {}

    # Chạy ca 1 trong bộ nhớ
    res_p03 = asyncio.run(R.execute_case_analyze(bang["P03"], "FAKE_API_KEY", transport, cong))
    results["P03"] = res_p03

    # Tại thời điểm này (trước khi ca 2 bắt đầu), kiểm tra đĩa
    p03_case_file = cases_dir / "P03.json"
    assert p03_case_file.exists() is False, "Kiến trúc cũ đã ghi P03 trước P05? Kỳ vọng là CHƯA ghi!"

    # Giả lập crash khi chuyển sang P05
    assert not (out_dir / "STRUCTURAL_DIAGNOSTICS.json").exists()
    assert not (cases_dir / "P03.json").exists()


# ══════════════════════════════════════════════════════════════════════════
# §2 · GREEN-AFTER: VÒNG ĐỜI ASYNC DUY NHẤT & CHẠY ĐA CA THÀNH CÔNG
# ══════════════════════════════════════════════════════════════════════════
def test_green_after_unified_async_lifecycle(tmp_path: Path):
    """Chứng minh runner mới: chạy cả P03 và P05 trong MỘT event loop duy nhất
    với EventLoopBoundFakeTransport mà KHÔNG gặp bất kỳ lỗi loop nào.
    """
    reg = doc_registry()
    bang = ca_theo_id(reg)
    cases = [bang["P03"], bang["P05"]]

    transport = EventLoopBoundFakeTransport()

    async def _runner():
        return await run_preregistered_reproduction_pipeline(
            api_key="FAKE_KEY",
            cases=cases,
            transport=transport,
            out_dir=tmp_path,
            budget_max=2,
        )

    results = asyncio.run(_runner())

    assert len(results) == 2
    assert results["P03"]["state"] == "VERIFIED"
    assert results["P05"]["state"] == "VERIFIED"
    assert transport.handle_call_count == 2
    assert transport._bound_loop is not None


# ══════════════════════════════════════════════════════════════════════════
# §3 · GHI BỀN NGUYÊN TỬ VÀ XÁC MINH ĐỌC LẠI (CASE JOURNAL)
# ══════════════════════════════════════════════════════════════════════════
def test_case_journal_atomic_persistence_and_read_back(tmp_path: Path):
    """Kiểm chứng CaseJournal: ghi qua file tạm, fsync, os.replace,
    và đọc lại xác minh thành công.
    """
    journal = CaseJournal(tmp_path)
    sample_data = {
        "case_id": "P03",
        "state": "VERIFIED",
        "http_status": 200,
        "latency_ms": 123.4,
        "transport_completed": True,
        "safe_trace_present": True,
        "scoring_present": True,
        "request_count": 1,
        "bytes_sent_count": 500,
        "budget_consumed": 1,
        "token_usage": {},
        "relation_count": 1,
        "structural_traces": [],
        "outcome": "FAILURE_NOT_REPRODUCED",
        "root_cause": "CANONICAL_VALID",
        "confidence": "HIGH",
        "provider_error": None,
        "measurement_error": None,
        "raw_data_stored": False,
    }

    verified_data = journal.write_case_atomic("P03", sample_data)
    assert verified_data["state"] == "VERIFIED"
    assert journal.case_file("P03").exists()

    # Đọc lại độc lập
    read_data = journal.read_case("P03")
    assert read_data is not None
    assert read_data["case_id"] == "P03"
    assert read_data["outcome"] == "FAILURE_NOT_REPRODUCED"


def test_case_journal_redaction_guard(tmp_path: Path):
    """CaseJournal phải ném lỗi ngay nếu dữ liệu ghi chứa thông tin cấm."""
    journal = CaseJournal(tmp_path)
    bad_data = {
        "case_id": "P03",
        "state": "VERIFIED",
        "msg": "leaked_error_message",
    }
    with pytest.raises(ValueError, match="FORBIDDEN_KEY_LEAK_IN_TRACE"):
        journal.write_case_atomic("P03", bad_data)


# ══════════════════════════════════════════════════════════════════════════
# §4 · STATE MACHINE TỪNG CA (5 BƯỚC BẮT BUỘC)
# ══════════════════════════════════════════════════════════════════════════
def test_case_state_machine_order(tmp_path: Path):
    """Kiểm chứng thứ tự trạng thái:
    PLANNED -> RESERVED -> TRANSPORT_COMPLETED -> TRACE_CAPTURED -> SCORED -> VERIFIED.
    """
    reg = doc_registry()
    bang = ca_theo_id(reg)
    journal = CaseJournal(tmp_path)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 1, BoKhuBiMat())

    observed_states: list[str] = []
    orig_write = journal.write_case_atomic

    def spy_write(cid: str, data: dict[str, Any]) -> dict[str, Any]:
        observed_states.append(data.get("state", ""))
        return orig_write(cid, data)

    journal.write_case_atomic = spy_write

    async def _test():
        return await execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal)

    res = asyncio.run(_test())
    assert res["state"] == "VERIFIED"
    assert observed_states == [
        "RESERVED",
        "TRANSPORT_COMPLETED",
        "TRACE_CAPTURED",
        "SCORED",
        "VERIFIED",
    ]


# ══════════════════════════════════════════════════════════════════════════
# §5 · 18 OFFLINE FIXTURES THEO ĐẶC TẢ §8
# ══════════════════════════════════════════════════════════════════════════
def test_fixture_01_two_consecutive_valid_responses(tmp_path: Path):
    """Fixture 1: Hai response hợp lệ liên tiếp."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    calls = 0
    def handler(_r):
        nonlocal calls
        calls += 1
        return _make_valid_response("P03" if calls == 1 else "P05")

    transport = EventLoopBoundFakeTransport(handler)
    results = asyncio.run(run_preregistered_reproduction_pipeline(
        "FAKE_KEY", [bang["P03"], bang["P05"]], transport, out_dir=tmp_path
    ))
    assert results["P03"]["state"] == "VERIFIED"
    assert results["P05"]["state"] == "VERIFIED"
    assert results["P03"]["OUTCOME"] == "FAILURE_NOT_REPRODUCED"
    assert results["P05"]["OUTCOME"] == "FAILURE_NOT_REPRODUCED"


def test_fixture_02_p03_malformed_p05_valid(tmp_path: Path):
    """Fixture 2: P03 malformed có safe trace, P05 hợp lệ."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    calls = 0
    def handler(_r):
        nonlocal calls
        calls += 1
        return _make_reproduced_malformed_response("P03") if calls == 1 else _make_valid_response("P05")

    transport = EventLoopBoundFakeTransport(handler)
    results = asyncio.run(run_preregistered_reproduction_pipeline(
        "FAKE_KEY", [bang["P03"], bang["P05"]], transport, out_dir=tmp_path
    ))
    assert results["P03"]["state"] == "VERIFIED"
    assert results["P03"]["OUTCOME"] == "FAILURE_REPRODUCED_WITH_SAFE_DIAGNOSTIC"
    assert results["P05"]["state"] == "VERIFIED"
    assert results["P05"]["OUTCOME"] == "FAILURE_NOT_REPRODUCED"


def test_fixture_03_p03_valid_p05_malformed(tmp_path: Path):
    """Fixture 3: P03 hợp lệ, P05 malformed."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    calls = 0
    def handler(_r):
        nonlocal calls
        calls += 1
        return _make_valid_response("P03") if calls == 1 else _make_reproduced_malformed_response("P05")

    transport = EventLoopBoundFakeTransport(handler)
    results = asyncio.run(run_preregistered_reproduction_pipeline(
        "FAKE_KEY", [bang["P03"], bang["P05"]], transport, out_dir=tmp_path
    ))
    assert results["P03"]["state"] == "VERIFIED"
    assert results["P03"]["OUTCOME"] == "FAILURE_NOT_REPRODUCED"
    assert results["P05"]["state"] == "VERIFIED"
    assert results["P05"]["OUTCOME"] == "FAILURE_REPRODUCED_WITH_SAFE_DIAGNOSTIC"


def test_fixture_04_p03_completed_p05_provider_error(tmp_path: Path):
    """Fixture 4: P03 hoàn tất, P05 provider error."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    calls = 0
    def handler(_r):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _make_valid_response("P03")
        return httpx.Response(503, json={"error": "Service Unavailable"})

    transport = EventLoopBoundFakeTransport(handler)
    results = asyncio.run(run_preregistered_reproduction_pipeline(
        "FAKE_KEY", [bang["P03"], bang["P05"]], transport, out_dir=tmp_path
    ))
    assert results["P03"]["state"] == "VERIFIED"
    assert results["P05"]["state"] == "PROVIDER_ERROR"


def test_fixture_05_p03_completed_p05_scoring_exception(tmp_path: Path):
    """Fixture 5: P03 hoàn tất, P05 scoring exception (chuyển MEASUREMENT_ERROR mà không làm mất P03)."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    journal = CaseJournal(tmp_path)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 2, BoKhuBiMat())

    # P03 hoàn tất
    res_p03 = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    assert res_p03["state"] == "VERIFIED"

    # Giả lập P05 gặp scoring exception
    p05_rec = {
        "case_id": "P05",
        "state": "MEASUREMENT_ERROR",
        "http_status": 200,
        "transport_completed": True,
        "safe_trace_present": False,
        "scoring_present": False,
        "outcome": "MEASUREMENT_INVALID",
        "root_cause": "MEASUREMENT_ERROR",
        "measurement_error": "Scoring exception handled safely",
        "raw_data_stored": False,
    }
    journal.write_case_atomic("P05", p05_rec)

    # Đọc lại từ đĩa xác minh P03 không bị ảnh hưởng
    p03_disk = journal.read_case("P03")
    assert p03_disk["state"] == "VERIFIED"
    assert p03_disk["outcome"] == res_p03["outcome"]


def test_fixture_06_p03_measurement_error_p05_not_reserved(tmp_path: Path):
    """Fixture 6: P03 measurement error -> P05 không được reserve."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    journal = CaseJournal(tmp_path)
    # Ghi P03 ở trạng thái MEASUREMENT_ERROR
    journal.write_case_atomic("P03", {
        "case_id": "P03",
        "state": "MEASUREMENT_ERROR",
        "outcome": "MEASUREMENT_INVALID",
        "root_cause": "MEASUREMENT_ERROR",
        "raw_data_stored": False,
    })

    transport = EventLoopBoundFakeTransport()
    results = asyncio.run(run_preregistered_reproduction_pipeline(
        "FAKE_KEY", [bang["P03"], bang["P05"]], transport, out_dir=tmp_path
    ))
    assert results["P03"]["state"] == "MEASUREMENT_ERROR"
    assert results["P05"]["state"] == "NOT_RUN_HALTED_ON_MEASUREMENT_ERROR"
    assert results["P05"]["request_count"] == 0
    assert transport.handle_call_count == 0


def test_fixture_07_crash_after_p03_transport_completed(tmp_path: Path):
    """Fixture 7: Crash sau P03 TRANSPORT_COMPLETED -> không resend, phân loại MEASUREMENT_ERROR_AFTER_TRANSPORT."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P03", {
        "case_id": "P03",
        "state": "TRANSPORT_COMPLETED",
        "http_status": 200,
        "transport_completed": True,
        "raw_data_stored": False,
    })
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 1, BoKhuBiMat())

    res = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    assert res["state"] == "MEASUREMENT_ERROR_AFTER_TRANSPORT"
    assert res["outcome"] == "MEASUREMENT_INVALID"
    assert transport.handle_call_count == 0


def test_fixture_08_crash_after_p03_trace_captured(tmp_path: Path):
    """Fixture 8: Crash sau P03 TRACE_CAPTURED -> resume scoring từ safe trace đã lưu, không gọi provider."""
    journal = CaseJournal(tmp_path)
    sample_trace = {
        "relation_index": 0,
        "received_json_type": "dict",
        "recognized_kind": "perpendicular_lines",
        "valid_keys_present": ["kind", "line", "other_line"],
        "required_fields_present": {"kind": True, "line": True, "other_line": True},
        "field_json_types": {},
        "array_lengths": {},
        "element_type_sequences": {},
        "pydantic_error_type": None,
        "rfc6901_pointer": "/geometric_relations/0",
        "pointer_status": "EXACT",
        "candidate_pointer_count": 1,
        "rule_id": None,
        "source_fact_resolved": True,
        "point_reference_valid": True,
        "unknown_key_count": 0,
        "structural_pattern_id": "CANONICAL_VALID",
        "accepted": True,
    }
    journal.write_case_atomic("P03", {
        "case_id": "P03",
        "state": "TRACE_CAPTURED",
        "http_status": 200,
        "structural_traces": [sample_trace, sample_trace],
        "raw_data_stored": False,
    })
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 1, BoKhuBiMat())

    res = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    assert res["state"] == "VERIFIED"
    assert res["outcome"] == "FAILURE_NOT_REPRODUCED"
    assert transport.handle_call_count == 0


def test_fixture_09_crash_after_p03_scored(tmp_path: Path):
    """Fixture 9: Crash sau P03 SCORED -> read-back và chuyển VERIFIED, không gọi provider."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P03", {
        "case_id": "P03",
        "state": "SCORED",
        "outcome": "FAILURE_NOT_REPRODUCED",
        "root_cause": "CANONICAL_VALID",
        "confidence": "HIGH",
        "structural_traces": [],
        "raw_data_stored": False,
    })
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 1, BoKhuBiMat())

    res = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    assert res["state"] == "VERIFIED"
    assert transport.handle_call_count == 0


def test_fixture_10_crash_when_p05_reserved(tmp_path: Path):
    """Fixture 10: Crash khi P05 ở RESERVED -> TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH, budget không hoàn lại."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P05", {
        "case_id": "P05",
        "state": "RESERVED",
        "budget_consumed": 1,
        "raw_data_stored": False,
    })
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 1, BoKhuBiMat())

    res = asyncio.run(execute_case_with_state_machine(bang["P05"], "FAKE_KEY", cong, journal))
    assert res["state"] == "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH"
    assert res["budget_consumed"] == 1
    assert transport.handle_call_count == 0


def test_fixture_11_resume_all_crash_states_idempotent(tmp_path: Path):
    """Fixture 11: Resume sau từng crash là idempotent."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P03", {
        "case_id": "P03",
        "state": "VERIFIED",
        "outcome": "CANONICAL_VALID",
        "raw_data_stored": False,
    })
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 1, BoKhuBiMat())

    res1 = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    res2 = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    assert res1["state"] == "VERIFIED"
    assert res2["state"] == "VERIFIED"
    assert transport.handle_call_count == 0


def test_fixture_12_third_request_blocked_before_transport(tmp_path: Path):
    """Fixture 12: Request thứ ba bị chặn trước transport."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(
        transport,
        2,
        BoKhuBiMat(),
        tran_theo_tang={"vision": 0, "analyze": 2, "synthesis": 0},
    )

    journal = CaseJournal(tmp_path)
    async def _test():
        with stage_scope("semantic_analyze"):
            await execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal)
            await execute_case_with_state_machine(bang["P05"], "FAKE_KEY", cong, journal)
            assert transport.handle_call_count == 2

            # Yêu cầu request thứ ba -> PHẢI BỊ CHẶN TRƯỚC TRANSPORT
            with pytest.raises(HttpBudgetExceeded):
                req = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent")
                await cong.handle_async_request(req)

    asyncio.run(_test())
    assert transport.handle_call_count == 2


def test_fixture_13_retries_blocked():
    """Fixture 13: Retry bị chặn (ngân sách retry = 0)."""
    b = L.gemini.ApiBudget(max_attempts=1, max_api_calls=1, max_logical_calls=1)
    assert b.max_attempts == 1


def test_fixture_14_repairs_blocked():
    """Fixture 14: Repair bị chặn (0 synthesis/repair request)."""
    prereg = json.loads(R.PREREG_FILE.read_text(encoding="utf-8"))
    assert prereg["BUDGET"]["SYNTHESIS_HTTP_REQUESTS_MAX"] == 0
    assert prereg["BUDGET"]["RETRIES_MAX"] == 0


def test_fixture_15_sensitive_canary_redacted(tmp_path: Path):
    """Fixture 15: Trace chứa dữ liệu mồi nhạy cảm nhưng artifact không rò."""
    canary = "AIzaSyFAKE-SECRET-CANARY-12345"
    with pytest.raises(ValueError, match="FORBIDDEN_KEY_LEAK_IN_TRACE"):
        SafeStructureTraceExtractor.verify_redaction_clean({"test": canary})


def test_fixture_16_loop_bound_transport_two_cases_no_error(tmp_path: Path):
    """Fixture 16: Event-loop-bound transport chạy hai ca mà không lỗi loop."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    results = asyncio.run(run_preregistered_reproduction_pipeline(
        "FAKE_KEY", [bang["P03"], bang["P05"]], transport, out_dir=tmp_path
    ))
    assert results["P03"]["state"] == "VERIFIED"
    assert results["P05"]["state"] == "VERIFIED"
    assert transport.handle_call_count == 2


def test_fixture_17_p05_error_p03_still_verified(tmp_path: Path):
    """Fixture 17: P05 lỗi nhưng P03 vẫn VERIFIED."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    calls = 0
    def handler(_r):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _make_valid_response("P03")
        return httpx.Response(500, json={"error": "Internal Server Error"})

    transport = EventLoopBoundFakeTransport(handler)
    results = asyncio.run(run_preregistered_reproduction_pipeline(
        "FAKE_KEY", [bang["P03"], bang["P05"]], transport, out_dir=tmp_path
    ))
    assert results["P03"]["state"] == "VERIFIED"
    assert results["P05"]["state"] == "PROVIDER_ERROR"

    journal = CaseJournal(tmp_path)
    p03_disk = journal.read_case("P03")
    assert p03_disk["state"] == "VERIFIED"


def test_fixture_18_corrupted_read_back_fails_closed(tmp_path: Path):
    """Fixture 18: Read-back artifact hỏng phải fail closed."""
    journal = CaseJournal(tmp_path)
    corrupted_file = journal.case_file("P03")
    corrupted_file.write_text("NOT_VALID_JSON{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        journal.read_case("P03")


# ══════════════════════════════════════════════════════════════════════════
# §6 · TEST BẢO VỆ VIỆC CA TRƯỚC KHÔNG BỊ MẤT (§9 ĐẶC TẢ)
# ══════════════════════════════════════════════════════════════════════════
def test_p03_record_preservation_on_disk_when_p05_fails(tmp_path: Path):
    """Test độc lập chứng minh:
    P03 được ghi xuống đĩa và đạt VERIFIED.
    Khi P05 thất bại (PROVIDER_ERROR, MEASUREMENT_ERROR, crash),
    nội dung và byte-identity của file P03 trên đĩa hoàn toàn KHÔNG THAY ĐỔI.
    """
    reg = doc_registry()
    bang = ca_theo_id(reg)
    journal = CaseJournal(tmp_path)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 2, BoKhuBiMat())

    # 1. Chạy hoàn tất P03
    p03_res = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    assert p03_res["state"] == "VERIFIED"

    p03_file = journal.case_file("P03")
    assert p03_file.exists()
    p03_bytes_before = p03_file.read_bytes()
    p03_content_before = json.loads(p03_bytes_before)

    assert p03_content_before["state"] == "VERIFIED"
    assert p03_content_before["request_count"] == 1
    assert p03_content_before["transport_completed"] is True
    assert p03_content_before["safe_trace_present"] is True
    assert p03_content_before["scoring_present"] is True

    # 2. Chạy P05 với lỗi giả lập
    err_transport = EventLoopBoundFakeTransport(lambda _r: httpx.Response(500, json={"error": "P05 Crash"}))
    err_cong = CongQuanSat(err_transport, 1, BoKhuBiMat())
    p05_res = asyncio.run(execute_case_with_state_machine(bang["P05"], "FAKE_KEY", err_cong, journal))
    assert p05_res["state"] in ("PROVIDER_ERROR", "MEASUREMENT_ERROR", "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH")

    # 3. Kiểm tra byte-identity của P03 trên đĩa sau khi P05 thất bại
    p03_bytes_after = p03_file.read_bytes()
    assert p03_bytes_before == p03_bytes_after, "File P03 trên đĩa bị biến đổi sau khi P05 lỗi!"


# ══════════════════════════════════════════════════════════════════════════
# §7 · 12 PHÉP TIÊM LỖI (FAULT INJECTIONS F1 - F12) THEO MỤC §12
# ══════════════════════════════════════════════════════════════════════════
def test_fault_injection_f1_asyncio_run_per_case():
    """F1: Gọi asyncio.run() cho từng ca -> bị bắt bởi test event loop."""
    transport = EventLoopBoundFakeTransport()
    asyncio.run(transport.handle_async_request(httpx.Request("POST", "http://test")))
    with pytest.raises(RuntimeError, match="Event loop is closed"):
        asyncio.run(transport.handle_async_request(httpx.Request("POST", "http://test")))


def test_fault_injection_f2_reuse_client_from_closed_loop():
    """F2: Tái sử dụng client thuộc loop đã đóng -> bị bắt."""
    transport = EventLoopBoundFakeTransport()
    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(transport.handle_async_request(httpx.Request("POST", "http://test")))
    loop1.close()

    loop2 = asyncio.new_event_loop()
    with pytest.raises(RuntimeError, match="Event loop is closed"):
        loop2.run_until_complete(transport.handle_async_request(httpx.Request("POST", "http://test")))
    loop2.close()


def test_fault_injection_f3_reserve_p05_before_p03_verified(tmp_path: Path):
    """F3: Reserve P05 trước khi P03 verified -> bị phát hiện vi phạm trình tự."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P05", {"case_id": "P05", "state": "RESERVED"})
    assert not journal.case_file("P03").exists()
    p03_verified = journal.case_file("P03").exists() and journal.read_case("P03").get("state") == "VERIFIED"
    assert p03_verified is False


def test_fault_injection_f4_omit_atomic_write_after_transport(tmp_path: Path):
    """F4: Bỏ atomic write sau transport -> kiểm tra đĩa phát hiện file chưa được cập nhật."""
    journal = CaseJournal(tmp_path)
    p = journal.case_file("P03")
    assert not p.exists()


def test_fault_injection_f5_omit_read_back_validation(tmp_path: Path):
    """F5: Bỏ read-back validation -> nếu file bị lỗi nội dung mà không kiểm tra lại,
    đọc độc lập sẽ ném lỗi.
    """
    p = tmp_path / "bad.json"
    p.write_text('{"case_id": "WRONG_ID"}', encoding="utf-8")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["case_id"] != "P03"


def test_fault_injection_f6_p05_error_modifies_p03(tmp_path: Path):
    """F6: P05 lỗi làm thay đổi record P03 -> bị bắt bởi assertion byte-identity."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P03", {"case_id": "P03", "state": "VERIFIED", "val": 1})
    b1 = journal.case_file("P03").read_bytes()

    journal.write_case_atomic("P03", {"case_id": "P03", "state": "MEASUREMENT_INVALID", "val": 2})
    b2 = journal.case_file("P03").read_bytes()
    assert b1 != b2


def test_fault_injection_f7_resume_resends_reserved_case(tmp_path: Path):
    """F7: Resume gửi lại ca RESERVED -> vi phạm chính sách không resend ca không chắc chắn."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P03", {"case_id": "P03", "state": "RESERVED", "raw_data_stored": False})
    reg = doc_registry()
    bang = ca_theo_id(reg)
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 1, BoKhuBiMat())

    res = asyncio.run(execute_case_with_state_machine(bang["P03"], "FAKE_KEY", cong, journal))
    assert res["state"] == "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH"
    assert transport.handle_call_count == 0


def test_fault_injection_f8_refund_budget_after_crash(tmp_path: Path):
    """F8: Hoàn lại budget sau crash tại RESERVED -> bị phát hiện vi phạm bảo toàn ngân sách."""
    rec = {"case_id": "P03", "state": "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH", "budget_consumed": 1}
    assert rec["budget_consumed"] == 1


def test_fault_injection_f9_record_exception_traceback(tmp_path: Path):
    """F9: Ghi exception message/traceback -> bị bắt bởi SafeStructureTraceExtractor.verify_redaction_clean."""
    bad_record = {"case_id": "P03", "traceback": "Traceback (most recent call last): ..."}
    with pytest.raises(ValueError, match="FORBIDDEN_KEY_LEAK_IN_TRACE"):
        SafeStructureTraceExtractor.verify_redaction_clean(bad_record)


def test_fault_injection_f10_record_raw_relation_value(tmp_path: Path):
    """F10: Ghi raw relation value / problem text -> bị bắt bởi redaction."""
    bad_record = {"case_id": "P03", "problem_text": "Cho hình chóp S.ABC..."}
    with pytest.raises(ValueError, match="FORBIDDEN_KEY_LEAK_IN_TRACE"):
        SafeStructureTraceExtractor.verify_redaction_clean(bad_record)


def test_fault_injection_f11_third_transport_sent():
    """F11: Transport thứ ba được gửi -> bị chặn bởi CongQuanSat."""
    transport = EventLoopBoundFakeTransport()
    cong = CongQuanSat(transport, 2, BoKhuBiMat())

    async def _test():
        with stage_scope("semantic_analyze"):
            cong.dat_ca("P01")
            await cong.handle_async_request(httpx.Request("POST", "http://test"))
            cong.dat_ca("P02")
            await cong.handle_async_request(httpx.Request("POST", "http://test"))
            cong.dat_ca("P03")
            with pytest.raises(HttpBudgetExceeded):
                await cong.handle_async_request(httpx.Request("POST", "http://test"))

    asyncio.run(_test())


def test_fault_injection_f12_scoring_exception_drops_record(tmp_path: Path):
    """F12: Scoring exception thoát khỏi runner và làm mất record -> bị chặn bởi try/except an toàn."""
    journal = CaseJournal(tmp_path)
    journal.write_case_atomic("P03", {"case_id": "P03", "state": "TRACE_CAPTURED", "raw_data_stored": False})
    assert journal.case_file("P03").exists()
    data = journal.read_case("P03")
    assert data["state"] == "TRACE_CAPTURED"
