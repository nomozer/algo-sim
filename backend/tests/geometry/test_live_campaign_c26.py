"""C26 — a NEW Owner-authorized live campaign (80 requests / USD 1.00) beside the spent C21 one (70 / 4.00), with a
canary whose rows the full suite counts instead of re-sending (0 real provider calls: httpx is mocked)."""
import json

import httpx
import pytest

from scripts import run_s2_student_language_pilot as R
from tests.geometry.test_s2_student_language_pilot_runner import (
    _FAKE_AQ_KEY, _case, _delegated_terms, _k1, _mini_suite_spec, _r1_case, _write_study,
)
from tests.test_paired_route_evaluation import Provider, _body


def test_campaign_caps_are_per_campaign_and_c21_is_not_widened(tmp_path):
    assert R.DELEGATED_CAMPAIGNS == {"C21": (70, 4.0), "C26": (80, 1.0)}
    R.GlobalBudgetLedger(tmp_path / "a", max_requests=80, max_usd=1.0, campaign_id="C26")
    for kw in ({"max_requests": 81, "max_usd": 1.0}, {"max_requests": 80, "max_usd": 1.01}):
        with pytest.raises(R.LiveRefused):
            R.GlobalBudgetLedger(tmp_path / "b", campaign_id="C26", **kw)
    with pytest.raises(R.LiveRefused):
        R.GlobalBudgetLedger(tmp_path / "c", max_requests=80, max_usd=1.0)            # C21 stays <= 70
    with pytest.raises(R.LiveRefused):
        R.GlobalBudgetLedger(tmp_path / "d", max_requests=10, max_usd=1.0, campaign_id="C99")


def test_delegated_terms_bind_the_campaign(tmp_path):
    (tmp_path / "k1").mkdir()
    k1 = _write_study(tmp_path / "k1", "K-1", [_k1("K-A01")])
    c26 = {"campaign_id": "C26", "global_max_requests": 80, "global_max_usd": 1.0}
    assert R.check_approval_terms(k1.read_bytes(), _delegated_terms(k1, delegation=c26))["pilot"] == "K-1"
    with pytest.raises(R.LiveRefused, match="global_max_requests"):
        R.check_approval_terms(k1.read_bytes(), _delegated_terms(k1, delegation={"global_max_requests": 80}))
    with pytest.raises(R.LiveRefused, match="global_max_usd"):
        R.check_approval_terms(k1.read_bytes(), _delegated_terms(k1, delegation={**c26, "global_max_usd": 1.5}))
    with pytest.raises(R.LiveRefused, match="campaign_id"):
        R.check_approval_terms(k1.read_bytes(), _delegated_terms(k1, delegation={**c26, "campaign_id": "C27"}))


def test_canary_then_full_suite_reuses_canary_rows_under_one_carried_ledger(tmp_path, monkeypatch):
    repo, pilots = _mini_suite_spec(tmp_path)
    dotenv = tmp_path / "root.env"
    dotenv.write_text(f"GEMINI_API_KEY={_FAKE_AQ_KEY}\n", encoding="utf-8")
    att = tmp_path / "paid.json"
    att.write_text(json.dumps({"schema": "owner-paid-project-attestation/1",
                               "authorization_source": "EXPLICIT_OWNER_SEPARATE_STATEMENT",
                               "statement_ref": "OWNER_PAID_CONFIRMATION_TEST",
                               "statement_quote": "Confirmed paid Cloud Billing enabled.",
                               "paid_project_confirmed": True}), encoding="utf-8")
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    golds = {"K-1": _k1("K-A01")["gold_extraction"], "S-2": _case("S2-B-I11_mo_phong_va_tinh_SC")["gold_extraction"],
             "R-1": _r1_case()["gold_extraction"]}
    calls = []

    def post(url, **kw):
        text = kw["json"]["contents"][0]["parts"][0]["text"]
        study = next(s for s, g in golds.items() if g["problem_text"] in text)
        calls.append(study)
        return Provider(_body(golds[study]))(url, **kw)

    monkeypatch.setattr(httpx, "post", post)
    common = dict(dotenv_path=dotenv, paid_attestation_path=att, pilot_specs=pilots, git_cwd=repo,
                  sleep=lambda s: None, campaign_id="C26", global_max_requests=80, global_max_usd=1.0)
    canary = R.run_delegated_c21_suite(out_dir=tmp_path / "canary", ledger_dir=tmp_path / "canary",
                                       only_case_ids={"K-1": {"K-A01"}}, **common)
    assert calls == ["K-1"] and canary["total_http_requests"] == 1 and canary["campaign_id"] == "C26"
    ledger = tmp_path / "canary" / "c26-global-budget-ledger.json"
    assert json.loads(ledger.read_text(encoding="utf-8"))["campaign_id"] == "C26"

    full = R.run_delegated_c21_suite(out_dir=tmp_path / "full", ledger_dir=tmp_path / "full", carry_ledger=ledger,
                                     reuse_rows_from={"K-1": tmp_path / "canary" / "k1-live.jsonl"}, **common)
    assert calls == ["K-1", "S-2", "R-1"]                         # the canary case is counted, never re-sent
    assert full["status"] == "COMPLETE" and full["total_http_requests"] == 3
    assert full["carried_ledger"]["requests_used"] == 1
    k1 = full["pilots"][0]
    assert k1["reused_rows"] == 1 and k1["http_requests"] == 0 and k1["completed"]
    rows = [json.loads(x) for x in (tmp_path / "full" / "k1-live.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[1]["reused_from"] == "canary/k1-live.jsonl"

    # a different runtime identity (candidate change) can never be pooled into a full retest
    forged = tmp_path / "forged.jsonl"
    lines = (tmp_path / "canary" / "k1-live.jsonl").read_text(encoding="utf-8").splitlines()
    head = json.loads(lines[0])
    head["runtime_identity"] = {**head["runtime_identity"], "measured_system": "0" * 64}
    forged.write_text("\n".join([json.dumps(head)] + lines[1:]) + "\n", encoding="utf-8")
    with pytest.raises(R.LiveRefused, match="another runtime identity"):
        R.load_reusable_rows(forged, pilots["K-1"]["corpus_path"], R.runtime_identity())
