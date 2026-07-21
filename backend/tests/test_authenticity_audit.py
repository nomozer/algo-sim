# -*- coding: utf-8 -*-
"""M17-Lite W0 — chạy TOÀN BỘ audit matrix qua production run_pipeline (offline).

0 network: conftest guard patch httpx + xoá GEMINI_API_KEY — provider scripted
per-case. Suite này là HARD CORRECTNESS của Wave 0:
- mọi ok-archetype (direct/paraphrase/changed_input/boundary) đạt route đúng;
- 4/4 near-miss (intentional gap) bị chặn trung thực đúng error code;
- leak control (Dijkstra + duyệt cây HONEST) fail-closed qua computation gate;
- đối chứng representation KHÔNG bị chặn oan;
- PIN hành vi probe adversarial duyệt cây (CONDITIONAL_LEAK_CONFIRMED) — đây
  là phát hiện Wave 0 được GHI NHẬN CÓ CHỦ ĐÍCH: gate hiện tại tin
  analysis.result_ownership; khi analyze khai man "provided", generic dựng
  cảnh Điểm/Đoạn nối/Vật di chuyển cho duyệt cây. Sửa gate = production
  change cần user duyệt (scope M17-Lite mục 3); fix dài hạn = family
  tree_traversal (Wave 2). Nếu tương lai siết gate làm probe bị chặn → pin
  này ĐỎ để buộc cập nhật ledger + docs một cách có ý thức.
"""

from __future__ import annotations

from app.ai import pipeline
from app.evaluation.authenticity_audit import (
    audit_metrics,
    build_leak_ledger,
    classify_targets,
    leak_verdict,
    run_audit,
)
from app.evaluation.authenticity_matrix import ai_reachable_ids, build_audit_cases
from app.simulation.authenticity import AUTHENTICITY_CONTRACTS


def _run(monkeypatch):
    return run_audit(lambda fake: monkeypatch.setattr(pipeline, "call_gemini", fake))


# ── matrix sinh từ registry: phủ đủ, id duy nhất ──
def test_matrix_phu_du_target_va_archetype():
    cases = build_audit_cases()
    ids = [c.case_id for c in cases]
    assert len(ids) == len(set(ids))
    # mỗi AI-reachable target ≥ 3 ok-archetype
    for sid in ai_reachable_ids():
        ok_cases = [c for c in cases if c.sim_id == sid]
        assert len(ok_cases) >= 3, f"{sid}: thiếu ok-archetype ({len(ok_cases)})"
    # mỗi cơ chế near-miss khai trong contract có ĐÚNG MỘT case
    mechs = {nm for c in AUTHENTICITY_CONTRACTS.values() for nm in c.near_miss_mechanisms}
    nm_cases = [c for c in cases if c.archetype == "near_miss"]
    assert {c.mechanism for c in nm_cases} == mechs
    assert len(nm_cases) == len(mechs)


# ── hard correctness toàn matrix ──
def test_audit_hard_correctness(monkeypatch):
    records = _run(monkeypatch)
    assert len(records) == len(build_audit_cases())

    # (a) không case non-probe nào sai kỳ vọng, không pipeline error
    for r in records:
        if r.archetype == "leak_probe":
            continue
        assert r.matched is True, (
            f"{r.case_id}: matched={r.matched} status={r.actual_status} "
            f"route={r.final_route} err={r.pipeline_error}"
        )

    # (b) near-miss: đúng MỘT case cho mỗi cơ chế near-miss khai trong contract
    # (dẫn xuất — không pin số cứng, tránh churn khi wave flip gap→owned)
    expected_nm = {nm_ for c in AUTHENTICITY_CONTRACTS.values() for nm_ in c.near_miss_mechanisms}
    nm = [r for r in records if r.archetype == "near_miss"]
    assert len(nm) == len(expected_nm) > 0
    for r in nm:
        assert r.envelope_error_code == "gate_mechanism_ownership", r.case_id
        assert r.failure_category == "capability_gap", r.case_id

    # (c) leak control fail-closed: dijkstra + duyệt cây honest → computation gate
    for cid in ("aud-leak-dijkstra", "aud-regression-tree-honest"):
        r = next(x for x in records if x.case_id == cid)
        assert r.actual_status == "unsupported", cid
        assert r.failure_category == "capability_gap", cid
        comp = [g for g in r.gates if g.get("gate") == "computation" and g.get("fired")]
        assert comp, f"{cid}: computation gate không bắn"
        assert r.simulate_attempts == 0, f"{cid}: simulate chạy dù gate chặn"

    # (d) đối chứng chống chặn oan: representation khai báo → generic ok
    ctrl = next(x for x in records if x.case_id == "aud-control-representation-ok")
    assert ctrl.actual_status == "ok" and ctrl.final_route == "generic.rule_scene"

    # (e) refusal control: TCP advanced từ chối ở classify (không phải gap)
    tcp = next(x for x in records if x.case_id == "aud-refusal-tcp-handshake")
    assert tcp.actual_status == "unsupported" and tcp.failure_category is None


# ── PIN probe adversarial (phát hiện Wave 0 — xem docstring) ──
def test_pin_adversarial_tree_probe_conditional_leak(monkeypatch):
    records = _run(monkeypatch)
    probe = next(r for r in records if r.case_id == "aud-regression-tree-adversarial")
    assert probe.matched is None  # probe không chấm đúng/sai
    # HÀNH VI HIỆN TẠI (pin có chủ đích): analyze khai man ownership=provided
    # → computation gate không có tín hiệu cấu trúc để chặn → generic ok.
    assert leak_verdict(probe) == "CONDITIONAL_LEAK_CONFIRMED"
    # gate computation ĐÃ chạy và KHÔNG bắn (đúng thiết kế fail-closed theo
    # tín hiệu cấu trúc — không phải bug gate, mà là giới hạn phụ thuộc
    # analyze trung thực; ghi ledger + docs, fix dài hạn = tree_traversal W2)
    comp = [g for g in probe.gates if g.get("gate") == "computation"]
    assert comp and not comp[0].get("fired")


# ── phân loại + metrics ──
def test_classification_va_metrics(monkeypatch):
    records = _run(monkeypatch)
    cls = classify_targets(records)
    n_targets = len(ai_reachable_ids())
    assert len(cls) == n_targets
    assert cls["generic.rule_scene"] == "PARTIAL"  # dual authority (boolean DAG + representation)
    assert all(v == "REAL" for sid, v in cls.items() if sid != "generic.rule_scene")

    m = audit_metrics(records, cls)
    n_nm = len({nm for c in AUTHENTICITY_CONTRACTS.values() for nm in c.near_miss_mechanisms})
    assert m["near_miss_gap_recall"] == {"numerator": n_nm, "denominator": n_nm}
    assert m["false_refusal_on_ok_archetypes"] == 0
    integ = m["concrete_envelope_integrity"]
    assert integ["numerator"] == integ["denominator"] > 0
    parity = m["production_parity"]
    assert parity["numerator"] == parity["denominator"] == len(records)
    assert m["generic_leak"]["unconditional_leaks"] == 0
    assert m["generic_leak"]["conditional_leaks_confirmed"] == 1  # probe pin ở trên
    assert m["classification_histogram"] == {"REAL": n_targets - 1, "PARTIAL": 1}

    ledger = build_leak_ledger(records)
    verdicts = {e["case_id"]: e["verdict"] for e in ledger}
    assert verdicts == {
        "aud-leak-dijkstra": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-honest": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-adversarial": "CONDITIONAL_LEAK_CONFIRMED",
    }


# ── tái lập: chạy 2 lần cùng kết quả (tất định) ──
def test_audit_tai_lap(monkeypatch):
    r1 = _run(monkeypatch)
    r2 = _run(monkeypatch)
    key = lambda rs: [(r.case_id, r.actual_status, r.final_route, r.matched) for r in rs]  # noqa: E731
    assert key(r1) == key(r2)
