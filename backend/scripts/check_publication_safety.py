"""Cổng xuất bản: chặn traceback thô và credential trong nội dung Git trước khi push (AGENTS.md §4). 0 lượt gọi model.

Hai chế độ, đều đọc ĐỐI TƯỢNG GIT chứ không đọc cây làm việc:

- ``--head``: mọi file tracked trong cây của HEAD (``git ls-tree -r``).
- ``--range BASE..TIP``: mọi blob MỚI trong khoảng (``git rev-list --objects``, tức là chưa có ở BASE) tại mọi đường dẫn
  nó xuất hiện, cộng message của từng commit trong khoảng.

Miễn trừ chỉ đến từ ``publication_exceptions.json`` và chỉ cho đúng bộ (đường dẫn, blob SHA-1, SHA-256 nội dung, luật).
Entry chỉ có hiệu lực khi ``owner_decision == "APPROVED_BY_USER"``, giá trị đó do Owner ghi, không script hay agent nào ghi.
Entry ``PENDING_OWNER_DECISION`` vẫn chặn. Đổi một byte (blob khác) hay chép sang đường dẫn khác thì không còn được miễn.

Output chỉ có metadata (luật, đường dẫn, blob, số dòng), không bao giờ in dòng bị bắt. Exit 0 sạch, 1 có vi phạm, 2 lỗi.
Không quét: file nhị phân (có NUL trong 8000 byte đầu), output mô hình thô, đường dẫn local. Regex là giới hạn dưới,
không phải bằng chứng là không có dữ liệu nhạy cảm.

Chạy từ ``backend/``::

    python scripts/check_publication_safety.py --head
    python scripts/check_publication_safety.py --range origin/main..HEAD
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCEPTIONS = ROOT / "docs/evaluation/geometry/runs/publication-safety-remediation/publication_exceptions.json"
OWNER_APPROVED = "APPROVED_BY_USER"
PENDING = "PENDING_OWNER_DECISION"

# Ghép chuỗi để chính file này không mang một dòng khớp luật.
_TB = "Trace" + "back"
RULES: dict[str, re.Pattern[bytes]] = {
    # Khung traceback Python thô: dòng mở đầu, hoặc một dòng khung `File "...", line N`, đứng đầu dòng.
    # Một chuỗi literal nằm giữa dòng mã (`b'Trace…' in data`) không khớp.
    "PY_TRACEBACK": re.compile(rb"(?m)^[ \t]*(?:" + _TB.encode() + rb" \(most recent call last\):"
                               rb"|File \"[^\"\r\n]+\", line \d+)"),
    "GOOGLE_API_KEY": re.compile(rb"AIza[0-9A-Za-z_\-]{35}"),
    "OPENAI_KEY": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}"),
    "ANTHROPIC_KEY": re.compile(rb"\bsk-ant-[A-Za-z0-9_\-]{20,}"),
    "GITHUB_TOKEN": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}"),
    "AWS_ACCESS_KEY": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "SLACK_TOKEN": re.compile(rb"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    "PRIVATE_KEY": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    # Cùng hai mẫu của `audit_secret_scan` (docs IA inv_22), nhưng ở đây áp cho mọi đối tượng Git.
    "BEARER_TOKEN": re.compile(rb"Bearer\s+[a-zA-Z0-9\-_]{20,}"),
    "HARDCODED_PASSWORD": re.compile(rb"(?i)password\s*[:=]\s*['\"][^'\"\r\n]{6,}['\"]"),
    "SECRET_ASSIGNMENT": re.compile(
        rb"(?i)\b(?:GEMINI_API_KEY|GOOGLE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|HYBRID_ROUTE_D_PREVIEW_TOKEN)"
        rb"[ \t]*[:=][ \t]*[\"']?[A-Za-z0-9_\-]{20,}"),
}


def _git(*args: str, cwd: Path, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True, check=True).stdout


def findings_in(content: bytes) -> list[tuple[str, int]]:
    """(luật, số dòng 1-based) cho mỗi lần khớp. Nhị phân ⇒ rỗng."""
    if b"\0" in content[:8000]:
        return []
    out = []
    for rule, pattern in RULES.items():
        for m in pattern.finditer(content):
            out.append((rule, content.count(b"\n", 0, m.start()) + 1))
    return out


def load_exceptions(path: Path) -> dict[tuple[str, str], dict]:
    """(đường dẫn, blob) → entry. Sai dạng ⇒ ValueError (exit 2), không bao giờ âm thầm bỏ qua."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "publication-exceptions/1" or not isinstance(data.get("entries"), list):
        raise ValueError("publication_exceptions: schema")
    out = {}
    for e in data["entries"]:
        if not (isinstance(e, dict) and re.fullmatch(r"[0-9a-f]{40}", str(e.get("blob")))
                and re.fullmatch(r"[0-9a-f]{64}", str(e.get("sha256"))) and isinstance(e.get("path"), str)
                and isinstance(e.get("rules"), list) and set(e["rules"]) <= set(RULES)
                and e.get("owner_decision") in (PENDING, OWNER_APPROVED)):
            raise ValueError("publication_exceptions: entry")
        key = (e["path"], e["blob"])
        if key in out:
            raise ValueError("publication_exceptions: duplicate")
        out[key] = e
    return out


def _blobs(cwd: Path, shas: list[str]) -> dict[str, bytes]:
    raw = _git("cat-file", "--batch", cwd=cwd, data="".join(s + "\n" for s in shas).encode())
    out, i = {}, 0
    for sha in shas:
        nl = raw.index(b"\n", i)
        size = int(raw[i:nl].split()[2])
        out[sha] = raw[nl + 1:nl + 1 + size]
        i = nl + 1 + size + 1
    return out


def head_items(cwd: Path) -> list[tuple[str, str]]:
    """(đường dẫn, blob) của mọi file tracked trong cây HEAD."""
    items = []
    for rec in _git("ls-tree", "-r", "-z", "HEAD", cwd=cwd).split(b"\0"):
        if rec:
            meta, path = rec.split(b"\t", 1)
            _, kind, sha = meta.split()
            if kind == b"blob":
                items.append((path.decode("utf-8"), sha.decode()))
    return items


def range_items(cwd: Path, rng: str) -> tuple[list[tuple[str, str]], list[tuple[str, bytes]]]:
    """Blob mới của khoảng tại mọi đường dẫn nó xuất hiện, và (commit, message) của khoảng."""
    new = {line.split(b" ")[0].decode() for line in _git("rev-list", "--objects", rng, cwd=cwd).splitlines()}
    items: set[tuple[str, str]] = set()
    raw = _git("log", "--raw", "--no-abbrev", "--no-renames", "--diff-merges=first-parent", "-z", "--format=", rng, cwd=cwd)
    fields = raw.split(b"\0")
    i = 0
    while i < len(fields):
        f = fields[i].lstrip(b"\n")
        if f.startswith(b":"):
            parts = f.split()
            sha, status, path = parts[3].decode(), parts[4][:1], fields[i + 1].decode("utf-8")
            if status != b"D" and sha in new:
                items.add((path, sha))
            i += 2
        else:
            i += 1
    msgs = []
    for rec in _git("log", "-z", "--format=%H%x01%B", rng, cwd=cwd).split(b"\0"):
        if rec.strip():
            h, body = rec.lstrip(b"\n").split(b"\x01", 1)
            msgs.append((h.decode(), body))
    return sorted(items), msgs


def scan(cwd: Path, items: list[tuple[str, str]], messages: list[tuple[str, bytes]],
         exceptions: dict[tuple[str, str], dict]) -> list[dict]:
    """Mọi vi phạm còn chặn. Miễn trừ đã duyệt bị bỏ; miễn trừ PENDING vẫn báo, kèm cờ."""
    contents = _blobs(cwd, sorted({b for _, b in items}))
    out = []
    for path, blob in items:
        content = contents[blob]
        hits = findings_in(content)
        if not hits:
            continue
        e = exceptions.get((path, blob))
        sha256 = hashlib.sha256(content).hexdigest()
        for rule, line in hits:
            covered = e is not None and e["sha256"] == sha256 and rule in e["rules"]
            if covered and e["owner_decision"] == OWNER_APPROVED:
                continue
            out.append({"rule": rule, "path": path, "blob": blob, "line": line,
                        "exception": e["owner_decision"] if covered else None})
    for commit, body in messages:
        for rule, line in findings_in(body):
            out.append({"rule": rule, "path": f"commit-message:{commit}", "blob": None, "line": line, "exception": None})
    return out


def main(argv: list[str] | None = None, cwd: Path = ROOT, exceptions_path: Path = EXCEPTIONS) -> int:
    ap = argparse.ArgumentParser(description="Publication safety gate (traceback / credential), 0 model calls.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--head", action="store_true")
    mode.add_argument("--range")
    ap.add_argument("--exceptions", type=Path, default=None)
    a = ap.parse_args(argv)
    try:
        exc = load_exceptions(a.exceptions or exceptions_path)
        items, msgs = (head_items(cwd), []) if a.head else range_items(cwd, a.range)
        found = scan(cwd, items, msgs, exc)
    except (ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"ERROR {type(e).__name__}: {str(e)[:120]}")
        return 2
    for f in found:
        tag = f" exception={f['exception']}" if f["exception"] else ""
        print(f"VIOLATION rule={f['rule']} path={f['path']} blob={f['blob']} line={f['line']}{tag}")
    pending = sum(1 for f in found if f["exception"])
    print(f"SUMMARY scanned={len(items)} messages={len(msgs)} violations={len(found)} pending_exception={pending} "
          f"verdict={'BLOCKED' if found else 'PASS'}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
