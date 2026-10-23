"""Cổng xuất bản `scripts/check_publication_safety.py` trên repo Git tạm (0 lượt gọi model, không đụng repo thật trừ
kiểm toàn vẹn file miễn trừ).

Vector bị cấm được GHÉP lúc chạy, nên chính file này không mang dòng khớp luật nào. Allowlist "đã duyệt" chỉ được ghi
vào ``tmp_path`` bằng hằng ``gate.OWNER_APPROVED``: đó là fixture của cơ chế, không phải phê duyệt một artifact thật.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_publication_safety.py"
_spec = importlib.util.spec_from_file_location("check_publication_safety", SCRIPT)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

TB_HEADER = "Trace" + "back (most recent call last):"
TB = (f"pytest output\n  {TB_HEADER}\n    " + 'File "C:\\x\\threading.py"' + ", line 1075, in run\n"
      "UnicodeDecodeError: boom\n")
FAKE_KEY = "AI" + "za" + "Sy" + "Q" * 33


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    for k, v in (("user.name", "t"), ("user.email", "t@example.invalid"), ("core.autocrlf", "false"),
                 ("commit.gpgsign", "false")):
        _git(r, "config", k, v)
    _commit(r, {"README.md": "clean\n"}, "base")
    _git(r, "tag", "base")
    return r


def _commit(repo: Path, files: dict[str, str | None], msg: str) -> None:
    for name, text in files.items():
        p = repo / name
        if text is None:
            _git(repo, "rm", "-q", name)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
        _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", msg)


def _exceptions(tmp: Path, repo: Path, path: str, rev: str, decision: str, rules=("PY_TRACEBACK",)) -> Path:
    blob = _git(repo, "rev-parse", f"{rev}:{path}")
    content = subprocess.run(["git", "cat-file", "blob", blob], cwd=repo, capture_output=True, check=True).stdout
    f = tmp / "exceptions.json"
    f.write_text(json.dumps({"schema": "publication-exceptions/1", "entries": [{
        "path": path, "blob": blob, "sha256": hashlib.sha256(content).hexdigest(), "rules": list(rules),
        "owner_decision": decision}]}), encoding="utf-8")
    return f


def _run(repo: Path, exc: Path, *argv: str, capsys) -> tuple[int, str]:
    code = gate.main([*argv, "--exceptions", str(exc)], cwd=repo)
    return code, capsys.readouterr().out


def test_new_traceback_in_range_is_blocked_and_output_has_no_raw_text(repo, tmp_path, capsys):
    _commit(repo, {"logs/run.log": TB}, "add log")
    code, out = _run(repo, tmp_path / "none.json", "--range", "base..HEAD", capsys=capsys)
    assert code == 1 and "rule=PY_TRACEBACK path=logs/run.log" in out and "verdict=BLOCKED" in out
    assert "most recent call" not in out and "threading.py" not in out and "boom" not in out


def test_approved_exact_historical_blob_is_not_a_false_positive(repo, tmp_path, capsys):
    _commit(repo, {"logs/run.log": TB}, "add log")
    exc = _exceptions(tmp_path, repo, "logs/run.log", "HEAD", gate.OWNER_APPROVED)
    assert _run(repo, exc, "--range", "base..HEAD", capsys=capsys)[0] == 0
    assert _run(repo, exc, "--head", capsys=capsys)[0] == 0


def test_pending_exception_still_blocks(repo, tmp_path, capsys):
    _commit(repo, {"logs/run.log": TB}, "add log")
    exc = _exceptions(tmp_path, repo, "logs/run.log", "HEAD", gate.PENDING)
    code, out = _run(repo, exc, "--range", "base..HEAD", capsys=capsys)
    assert code == 1 and f"exception={gate.PENDING}" in out and "pending_exception=" in out


def test_changed_content_of_exempt_blob_is_not_exempt(repo, tmp_path, capsys):
    _commit(repo, {"logs/run.log": TB}, "add log")
    exc = _exceptions(tmp_path, repo, "logs/run.log", "HEAD", gate.OWNER_APPROVED)
    _commit(repo, {"logs/run.log": TB + "one more line\n"}, "edit log")
    code, out = _run(repo, exc, "--range", "base..HEAD", capsys=capsys)
    assert code == 1 and out.count("path=logs/run.log") >= 1
    assert _run(repo, exc, "--head", capsys=capsys)[0] == 1


def test_same_bytes_under_another_name_are_not_exempt(repo, tmp_path, capsys):
    _commit(repo, {"logs/run.log": TB}, "add log")
    exc = _exceptions(tmp_path, repo, "logs/run.log", "HEAD", gate.OWNER_APPROVED)
    _commit(repo, {"logs/copy.log": TB}, "copy log")
    code, out = _run(repo, exc, "--head", capsys=capsys)
    assert code == 1 and "path=logs/copy.log" in out and "path=logs/run.log" not in out


def test_exception_does_not_cover_a_different_rule(repo, tmp_path, capsys):
    _commit(repo, {"logs/run.log": TB + f"key={FAKE_KEY}\n"}, "add log")
    exc = _exceptions(tmp_path, repo, "logs/run.log", "HEAD", gate.OWNER_APPROVED)
    code, out = _run(repo, exc, "--head", capsys=capsys)
    assert code == 1 and "rule=GOOGLE_API_KEY" in out and "rule=PY_TRACEBACK" not in out and FAKE_KEY not in out


def test_removed_from_tip_passes_head_but_history_still_blocks_range(repo, tmp_path, capsys):
    _commit(repo, {"logs/run.log": TB}, "add log")
    _commit(repo, {"logs/run.log": None}, "remove log from tip")
    none = tmp_path / "none.json"
    assert _run(repo, none, "--head", capsys=capsys)[0] == 0
    code, out = _run(repo, none, "--range", "base..HEAD", capsys=capsys)
    assert code == 1 and "path=logs/run.log" in out


def test_commit_message_is_scanned(repo, tmp_path, capsys):
    _commit(repo, {"a.txt": "x\n"}, f"fix\n\n{TB}")
    code, out = _run(repo, tmp_path / "none.json", "--range", "base..HEAD", capsys=capsys)
    assert code == 1 and "path=commit-message:" in out and "most recent call" not in out


def test_detector_literal_in_code_and_binary_are_not_flagged(repo, tmp_path, capsys):
    code_line = "if rc or b'" + TB_HEADER + "' in data:\n    keep_local()\n"
    _commit(repo, {"tool.py": code_line, "shot.png": "\x89PNG\x00" + TB}, "tooling")
    assert _run(repo, tmp_path / "none.json", "--range", "base..HEAD", capsys=capsys)[0] == 0


@pytest.mark.parametrize("bad", [
    {"schema": "other", "entries": []},
    {"schema": "publication-exceptions/1", "entries": [{"path": "a", "blob": "x", "sha256": "y", "rules": [],
                                                         "owner_decision": "APPROVED"}]},
])
def test_malformed_exceptions_file_is_an_error_not_a_pass(repo, tmp_path, capsys, bad):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps(bad), encoding="utf-8")
    assert _run(repo, f, "--head", capsys=capsys)[0] == 2


def test_repository_exceptions_match_real_objects_and_are_never_agent_approved():
    """Toàn vẹn file miễn trừ thật: mọi entry trỏ đúng blob có thật, SHA-256 khớp, luật thật sự khớp blob đó."""
    entries = gate.load_exceptions(gate.EXCEPTIONS)
    assert entries, "publication_exceptions.json missing or empty"
    for (path, blob), e in entries.items():
        content = subprocess.run(["git", "cat-file", "blob", blob], cwd=gate.ROOT, capture_output=True,
                                 check=True).stdout
        assert hashlib.sha256(content).hexdigest() == e["sha256"], path
        assert set(e["rules"]) == {r for r, _ in gate.findings_in(content)}, path
        assert e["owner_decision"] in (gate.PENDING, gate.OWNER_APPROVED)
