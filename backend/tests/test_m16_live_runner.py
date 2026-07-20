# -*- coding: utf-8 -*-
"""M16 Task 7 (W7) — live runner extension: parse args (--label/--out/
--resume-from), trace JSON đúng schema, resume bỏ case OK-khớp-expectation
giữ case fail, label ghi vào meta, KHÔNG opt-in vẫn abort (giữ nguyên hành vi
cũ). Nguồn yêu cầu: .superpowers/sdd/m16-task-7-brief.md (Phụ lục).

KHÔNG mạng: `evaluate_item` (điểm nối duy nhất còn lại trước khi chạm
`pipeline.run_pipeline`) bị monkeypatch thẳng — cách "ít xâm lấn" brief cho
phép (mock run_eval hoặc evaluate_item) — nên không cần dựng lại
analyze/classify/simulate scripted như test_m16_offline_eval.py.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import gemini, pipeline
from app.evaluation import live
from app.evaluation.harness import EvalReport, ItemResult
from app.evaluation.m16_record import M16CaseRecord

# 2 case đầu suite "smoke" (dataset "regression" mặc định) — cả hai
# "specialized", đủ đơn giản để dựng M16CaseRecord tay không cần script pipeline.
SMOKE_2 = ["a-and", "a-packet"]


@pytest.fixture(autouse=True)
def _clear_budget():
    gemini.set_budget(None)
    yield
    gemini.set_budget(None)


def _rec(
    case_id: str,
    *,
    group: str = "specialized",
    envelope_status: str | None = "ok",
    final_route: str | None,
    expected_final_route: str | None,
) -> M16CaseRecord:
    """Dựng `M16CaseRecord` TAY tối thiểu — đủ field để `_status_final` và
    `m16_artifacts._outcome_matches_expectation` (Task 7 tái dùng) chạy đúng."""
    return M16CaseRecord(
        case_id=case_id,
        group=group,
        archetype=None,
        expected_family=None,
        expected_initial_route=None,
        expected_final_route=expected_final_route,
        raw_prescribed=None,
        canonical_prescribed=None,
        result_ownership=None,
        initial_route=final_route,
        initial_family=None,
        reclassify_attempted=False,
        reclassify_result_route=None,
        final_route=final_route,
        final_family=None,
        selector_token_used=False,
        variant=None,
        gates=[],
        simulate_attempts=[{"n": 1, "ok": True, "error_code": None}],
        first_attempt_ok=True,
        semantic_ok=True,
        envelope_status=envelope_status,
        envelope_error_code=None,
        envelope_failure_category=None,
        source="composed",
        budget_delta={"logical_calls": 1, "http_requests": 1, "retry_requests": 0, "transient_hits": 0},
        via_production_pipeline=True,
        infra_error=None,
        detail="",
    )


def _fake_evaluate_item(records_by_case: dict[str, M16CaseRecord], calls: list[str]):
    """Thay `pipeline.run_pipeline` bằng bảng kịch bản record CÓ SẴN — mock
    Ở ĐÚNG điểm brief cho phép (evaluate_item), không chạm mạng."""

    async def fake(item, api_key, budget=None, record_sink=None):
        calls.append(item.id)
        record = records_by_case[item.id]
        if record_sink is not None:
            record_sink.append(record)
        return ItemResult(item.id, item.group, record.final_route, True)

    return fake


# ── parse args ──────────────────────────────────────────────────

def test_parse_args_mac_dinh_khong_kich_hoat_co_moi():
    args = live._parse_args(["--suite", "smoke"])
    assert args.label == "baseline"
    assert args.out is None
    assert args.resume_from is None


def test_parse_args_co_moi_duoc_doc_dung():
    args = live._parse_args([
        "--suite", "smoke", "--label", "postfix",
        "--out", "trace.json", "--resume-from", "old.json",
    ])
    assert args.label == "postfix"
    assert args.out == "trace.json"
    assert args.resume_from == "old.json"


def test_parse_args_label_sai_gia_tri_bi_tu_choi():
    with pytest.raises(SystemExit):
        live._parse_args(["--label", "khong-hop-le"])


# ── trace JSON đúng schema (mock 2 case) ──────────────────────────

def test_trace_ghi_dung_schema_mock_run_2_case(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-test")
    records = {
        "a-and": _rec("a-and", final_route="logic.and_gate", expected_final_route="logic.and_gate"),
        "a-packet": _rec(
            "a-packet", final_route="network.packet_routing", expected_final_route="network.packet_routing"
        ),
    }
    calls: list[str] = []
    monkeypatch.setattr(live, "evaluate_item", _fake_evaluate_item(records, calls))

    out_path = tmp_path / "trace.json"
    args = live._parse_args([
        "--suite", "smoke", "--max-cases", "2", "--out", str(out_path), "--label", "postfix",
    ])
    code = asyncio.run(live._main(args))

    assert code == 0
    assert calls == SMOKE_2  # đúng 2 case, đúng thứ tự

    trace = json.loads(out_path.read_text(encoding="utf-8"))
    assert trace["schema_version"] == "1"
    assert trace["dataset_version"] == live.M16_DATASET_VERSION
    assert trace["run_label"] == "postfix"
    assert set(trace["run_meta"]) == {"started_at", "suite", "dataset", "model"}
    assert trace["run_meta"]["suite"] == "smoke"
    assert trace["run_meta"]["dataset"] == "regression"
    assert trace["run_meta"]["model"] == gemini.MODEL
    assert set(trace["budget"]) == {"logical_calls", "http_requests", "retry_requests", "transient_hits"}
    assert [c["case_id"] for c in trace["cases"]] == SMOKE_2
    for c in trace["cases"]:
        assert c["status_final"] == "ok"
        assert c["record"]["case_id"] == c["case_id"]
    assert "budget_cumulative" not in trace  # không resume → không có field này


# ── resume: bỏ case OK-khớp-expectation, giữ/chạy-lại case fail ────

def test_resume_bo_case_ok_giu_case_fail(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-test")

    # Vòng 1: a-and OK + khớp expectation; a-packet bị từ chối (envelope
    # "unsupported") trong khi group="specialized" → KHÔNG khớp expectation.
    round1 = {
        "a-and": _rec("a-and", final_route="logic.and_gate", expected_final_route="logic.and_gate"),
        "a-packet": _rec(
            "a-packet", envelope_status="unsupported", final_route=None,
            expected_final_route="network.packet_routing",
        ),
    }
    calls1: list[str] = []
    monkeypatch.setattr(live, "evaluate_item", _fake_evaluate_item(round1, calls1))
    old_path = tmp_path / "old.json"
    args1 = live._parse_args(["--suite", "smoke", "--max-cases", "2", "--out", str(old_path)])
    code1 = asyncio.run(live._main(args1))
    assert code1 == 0
    assert calls1 == SMOKE_2

    # Vòng 2: --resume-from old.json. a-and PHẢI bị bỏ qua (không gọi lại);
    # a-packet chạy lại, lần này thành công.
    round2 = {
        "a-packet": _rec(
            "a-packet", final_route="network.packet_routing", expected_final_route="network.packet_routing"
        ),
    }
    calls2: list[str] = []
    monkeypatch.setattr(live, "evaluate_item", _fake_evaluate_item(round2, calls2))
    new_path = tmp_path / "new.json"
    args2 = live._parse_args([
        "--suite", "smoke", "--max-cases", "2",
        "--resume-from", str(old_path), "--out", str(new_path),
    ])
    code2 = asyncio.run(live._main(args2))

    assert code2 == 0
    assert calls2 == ["a-packet"]  # a-and KHÔNG chạy lại — "a-and" not in round2 nếu lỡ gọi sẽ KeyError

    trace = json.loads(new_path.read_text(encoding="utf-8"))
    assert [c["case_id"] for c in trace["cases"]] == SMOKE_2
    a_and = next(c for c in trace["cases"] if c["case_id"] == "a-and")
    a_packet = next(c for c in trace["cases"] if c["case_id"] == "a-packet")
    assert a_and["status_final"] == "ok"
    assert a_and["record"]["final_route"] == "logic.and_gate"  # y nguyên bản ghi cũ (không đè bằng dữ liệu vòng 2)
    assert a_packet["status_final"] == "ok"  # đã được sửa ở vòng 2
    assert "budget_cumulative" in trace
    assert set(trace["budget_cumulative"]) == {"logical_calls", "http_requests", "retry_requests", "transient_hits"}


def test_resume_bo_ca_case_unsupported_bi_tu_choi_dung(monkeypatch, tmp_path):
    """Review Task 7 (Important): case group="unsupported" bị TỪ CHỐI ĐÚNG
    (status_final=="refused", khớp expectation) cũng PHẢI được skip khi
    --resume-from — gate literal status_final=="ok" cũ khiến 9/50 case
    unsupported của pool m16 luôn chạy lại, đốt budget live vô ích."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-test")

    # Vòng 1: a-and OK-khớp; a-packet đóng vai case unsupported bị từ chối ĐÚNG.
    round1 = {
        "a-and": _rec("a-and", final_route="logic.and_gate", expected_final_route="logic.and_gate"),
        "a-packet": _rec(
            "a-packet", group="unsupported", envelope_status="unsupported",
            final_route=None, expected_final_route=None,
        ),
    }
    calls1: list[str] = []
    monkeypatch.setattr(live, "evaluate_item", _fake_evaluate_item(round1, calls1))
    old_path = tmp_path / "old.json"
    args1 = live._parse_args(["--suite", "smoke", "--max-cases", "2", "--out", str(old_path)])
    assert asyncio.run(live._main(args1)) == 0
    assert calls1 == SMOKE_2
    old_trace = json.loads(old_path.read_text(encoding="utf-8"))
    a_packet_old = next(c for c in old_trace["cases"] if c["case_id"] == "a-packet")
    assert a_packet_old["status_final"] == "refused"  # tiền đề của test

    # Vòng 2: resume — CẢ HAI đều khớp expectation → không case nào chạy lại
    # (bảng round2 rỗng: lỡ gọi case nào sẽ KeyError ngay).
    calls2: list[str] = []
    monkeypatch.setattr(live, "evaluate_item", _fake_evaluate_item({}, calls2))
    new_path = tmp_path / "new.json"
    args2 = live._parse_args([
        "--suite", "smoke", "--max-cases", "2",
        "--resume-from", str(old_path), "--out", str(new_path),
    ])
    assert asyncio.run(live._main(args2)) == 0
    assert calls2 == []

    trace = json.loads(new_path.read_text(encoding="utf-8"))
    kept = {c["case_id"]: c["status_final"] for c in trace["cases"]}
    assert kept == {"a-and": "ok", "a-packet": "refused"}  # giữ nguyên bản ghi cũ


def test_resume_khong_co_trace_cu_thi_chay_lai_ca_hai(monkeypatch, tmp_path):
    """Case KHÔNG có trong trace cũ (id lạ/trace rỗng) → coi như chưa chạy,
    PHẢI chạy lại — không tự ý bỏ qua."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-test")
    empty_trace = tmp_path / "empty.json"
    empty_trace.write_text(
        json.dumps({"schema_version": "1", "dataset_version": live.M16_DATASET_VERSION,
                    "run_label": "baseline", "run_meta": {}, "budget": {}, "cases": []}),
        encoding="utf-8",
    )
    records = {
        "a-and": _rec("a-and", final_route="logic.and_gate", expected_final_route="logic.and_gate"),
        "a-packet": _rec(
            "a-packet", final_route="network.packet_routing", expected_final_route="network.packet_routing"
        ),
    }
    calls: list[str] = []
    monkeypatch.setattr(live, "evaluate_item", _fake_evaluate_item(records, calls))
    args = live._parse_args([
        "--suite", "smoke", "--max-cases", "2", "--resume-from", str(empty_trace),
    ])
    code = asyncio.run(live._main(args))
    assert code == 0
    assert calls == SMOKE_2


# ── label ghi vào meta ──────────────────────────────────────────

def test_label_mac_dinh_baseline_khi_khong_truyen(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-test")
    records = {"a-and": _rec("a-and", final_route="logic.and_gate", expected_final_route="logic.and_gate")}
    monkeypatch.setattr(live, "evaluate_item", _fake_evaluate_item(records, []))
    out_path = tmp_path / "trace.json"
    args = live._parse_args(["--suite", "smoke", "--max-cases", "1", "--out", str(out_path)])
    asyncio.run(live._main(args))
    trace = json.loads(out_path.read_text(encoding="utf-8"))
    assert trace["run_label"] == "baseline"


# ── không opt-in vẫn abort (test cũ test_live_budget.py giữ nguyên; đây là
#    bằng chứng THÊM rằng 3 cờ mới KHÔNG mở lối tắt qua cổng opt-in) ────────

def test_khong_opt_in_van_abort_du_co_co_moi(monkeypatch, capsys):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)

    async def boom(*a, **k):
        raise AssertionError("live.py KHÔNG được gọi API khi thiếu ALLOW_LIVE_AI=1")

    monkeypatch.setattr(pipeline, "call_gemini", boom)
    code = live.main(["--suite", "smoke", "--out", "trace.json", "--label", "postfix"])

    assert code == 1
    out = capsys.readouterr().out
    assert "TỪ CHỐI" in out and "ALLOW_LIVE_AI=1" in out


# ── không cờ mới → đường CŨ (run_eval gốc), không đi qua vòng lặp mới ──────

def test_khong_co_co_moi_dung_duong_run_eval_goc(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-test")
    calls = {"run_eval": 0}

    async def fake_run_eval(items, api_key, budget=None):
        calls["run_eval"] += 1
        report = EvalReport(planned=len(items))
        report.budget = budget
        return report

    async def boom(*a, **k):
        raise AssertionError(
            "KHÔNG được đi qua _run_eval_with_records khi thiếu cả --out lẫn --resume-from "
            "(phải dùng run_eval gốc — hành vi cờ-cũ giữ nguyên tuyệt đối)"
        )

    monkeypatch.setattr(live, "run_eval", fake_run_eval)
    monkeypatch.setattr(live, "_run_eval_with_records", boom)

    code = asyncio.run(live._main(live._parse_args(["--suite", "smoke", "--max-cases", "1"])))

    assert code == 0
    assert calls["run_eval"] == 1
