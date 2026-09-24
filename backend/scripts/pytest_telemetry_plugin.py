# -*- coding: utf-8 -*-
"""Pytest Telemetry Plugin.

Thu thập dữ liệu kiểm thử trực tiếp từ pytest hooks theo chuẩn 2 tầng máy:
1. Tầng Thu thập (Collection Level):
   INITIAL_COLLECTED = SELECTED + DESELECTED
2. Tầng Thực thi (Execution Level):
   SELECTED = PASSED + FAILED + ERRORS + SKIPPED + XFAILED + XPASSED + NOT_RUN

Ghi tệp nguyên tử (tempfile -> flush -> fsync -> os.replace -> read-back validation).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest


class TelemetryCollector:
    def __init__(self, target_file: Path | None = None) -> None:
        self.target_file = target_file
        self.start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.start_perf = time.perf_counter()
        self.initial_collected: int = 0
        self.selected: int = 0
        self.deselected: int = 0
        self.item_statuses: dict[str, str] = {}  # nodeid -> final status
        self.invocation_id = f"inv_{int(time.time())}_{os.getpid()}"

    def record_deselected(self, items: list[Any]) -> None:
        self.deselected += len(items)

    def record_report(self, report: pytest.TestReport) -> None:
        nodeid = report.nodeid
        # Teardown failure overrides to error
        if report.when == "teardown":
            if report.failed:
                self.item_statuses[nodeid] = "errors"
            return

        if report.when == "setup":
            if report.failed:
                self.item_statuses[nodeid] = "errors"
            elif report.skipped:
                self.item_statuses[nodeid] = "skipped"
            return

        if report.when == "call":
            if report.passed:
                if hasattr(report, "wasxfail"):
                    self.item_statuses[nodeid] = "xpassed"
                else:
                    self.item_statuses[nodeid] = "passed"
            elif report.skipped:
                self.item_statuses[nodeid] = "skipped"
            elif report.failed:
                if hasattr(report, "wasxfail"):
                    self.item_statuses[nodeid] = "xfailed"
                else:
                    self.item_statuses[nodeid] = "failed"

    def finalize(self, exitstatus: int) -> dict[str, Any]:
        end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        duration_s = round(time.perf_counter() - self.start_perf, 3)

        passed = sum(1 for s in self.item_statuses.values() if s == "passed")
        failed = sum(1 for s in self.item_statuses.values() if s == "failed")
        errors = sum(1 for s in self.item_statuses.values() if s == "errors")
        skipped = sum(1 for s in self.item_statuses.values() if s == "skipped")
        xfailed = sum(1 for s in self.item_statuses.values() if s == "xfailed")
        xpassed = sum(1 for s in self.item_statuses.values() if s == "xpassed")

        outcomes_sum = passed + failed + errors + skipped + xfailed + xpassed
        not_run = max(0, self.selected - outcomes_sum)

        collection_balanced = (self.initial_collected == self.selected + self.deselected)
        execution_balanced = (self.selected == outcomes_sum + not_run)

        telemetry: dict[str, Any] = {
            "schema_version": "2.0.0",
            "invocation_id": self.invocation_id,
            "start_time": self.start_time,
            "end_time": end_time,
            "duration_seconds": duration_s,
            "exit_code": exitstatus,
            "initial_collected": self.initial_collected,
            "selected": self.selected,
            "deselected": self.deselected,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "xfailed": xfailed,
            "xpassed": xpassed,
            "not_run": not_run,
            "collection_balanced": collection_balanced,
            "execution_balanced": execution_balanced,
            "all_tests_completed": (not_run == 0),
            "command": " ".join(sys.argv),
        }

        if self.target_file:
            self.write_atomic(telemetry)

        return telemetry

    def write_atomic(self, data: dict[str, Any]) -> str:
        assert self.target_file is not None
        target = self.target_file.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_file = target.parent / f".tmp_{target.name}_{os.getpid()}"
        raw = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        raw_bytes = raw.encode("utf-8")

        with open(temp_file, "wb") as f:
            f.write(raw_bytes)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_file, target)

        # Read back verification
        read_back = target.read_bytes()
        assert read_back == raw_bytes, f"Read-back byte mismatch for {target}"
        return hashlib.sha256(raw_bytes).hexdigest()


_collector: TelemetryCollector | None = None


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("telemetry", "Pytest Telemetry Recording")
    group.addoption(
        "--telemetry-json",
        action="store",
        default=None,
        help="Path to output atomic pytest telemetry JSON",
    )
    group.addoption(
        "--invocation-id",
        action="store",
        default=None,
        help="Explicit invocation ID to bind with telemetry",
    )


def pytest_configure(config: pytest.Config) -> None:
    global _collector
    target_path = config.getoption("--telemetry-json")
    inv_id = config.getoption("--invocation-id")
    target_file = Path(target_path) if target_path else None
    _collector = TelemetryCollector(target_file=target_file)
    if inv_id:
        _collector.invocation_id = inv_id


@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]):
    global _collector
    if _collector is not None:
        _collector.initial_collected = len(items)
    outcome = yield
    if _collector is not None:
        _collector.selected = len(items)
        _collector.deselected = _collector.initial_collected - _collector.selected
        # Pre-populate selected items
        for it in items:
            _collector.item_statuses[it.nodeid] = "not_run"


def pytest_deselected(items: list[pytest.Item]) -> None:
    global _collector
    if _collector is not None:
        _collector.record_deselected(items)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    global _collector
    if _collector is not None:
        _collector.record_report(report)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    global _collector
    if _collector is not None:
        _collector.finalize(exitstatus)
