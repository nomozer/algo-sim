# -*- coding: utf-8 -*-
"""W19 — kiểm link markdown, anchor và đường dẫn `docs/…` trong tài liệu (chỉ đọc).

Chạy từ gốc kho:
    backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w19-docs-organization/diagnostics/check_doc_links.py \
        --inventory docs/evaluation/geometry/runs/w19-docs-organization/inventory/INVENTORY.json --out <file.json>

Ba lớp file (luật R1/R4 của W19):
- FROZEN   : docs/evaluation/** (trừ run w19) + báo cáo/snapshot giữ chỗ theo R1 (inventory: KEEP, kiểu evidence/protocol/decision)
- ARCHIVED : docs/legacy/** do W19 chuyển vào nguyên byte
- LIVING   : mọi tài liệu còn lại — W19 phải giữ 0 link hỏng MỚI ở lớp này.
Link hỏng ở FROZEN/ARCHIVED không sửa (sửa là đổi evidence); đường cũ tra qua inventory/MIGRATION_MAP.json.
Kiểm: [x](đích) và ![x](đích) tương đối (tồn tại; #anchor theo slug kiểu GitHub), `docs/…` trong dấu backtick.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[6]
RUN = "docs/evaluation/geometry/runs/w19-docs-organization/"
LINK = re.compile(r"!?\[(?:[^\]\[]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
TICK = re.compile(r"`(docs/[^`\s*<>{}|]+?)`")
FENCE = re.compile(r"^\s*(```|~~~)")


def git(*a: str) -> str:
    return subprocess.run(["git", "-c", "core.quotePath=false", *a], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def slug(h: str) -> str:
    h = re.sub(r"`|\*\*|__|\[|\]\([^)]*\)", "", h.strip().lower())
    h = "".join(c for c in h if c in " -_" or unicodedata.category(c)[0] in "LN")
    return h.replace(" ", "-")


def anchors(p: Path, cache: dict[Path, set[str]]) -> set[str]:
    if p not in cache:
        seen: dict[str, int] = {}
        out: set[str] = set()
        in_fence = False
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if FENCE.match(line):
                in_fence = not in_fence
            if in_fence or not line.startswith("#"):
                continue
            s = slug(line.lstrip("#"))
            n = seen.get(s, 0)
            out.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
        out.update(re.findall(r'<a\s+(?:name|id)="([^"]+)"', p.read_text(encoding="utf-8", errors="ignore")))
        cache[p] = out
    return cache[p]


def lop(p: str, frozen: set[str], merge: set[str]) -> str:
    if p.startswith(RUN) or p in ("docs/evaluation/README.md", "docs/evaluation/HISTORICAL_REPORTS.md"):
        return "LIVING"  # do W19 viết, không phải artifact đóng băng
    if p.startswith("docs/evaluation/") or p in frozen:
        return "FROZEN"
    if (p.startswith("docs/legacy/") and p != "docs/legacy/RULES_v0.3.md") or p in merge:
        return "ARCHIVED"
    return "LIVING"


def ban_do(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """old -> new và new -> old cho các file đã di chuyển (MIGRATION_MAP.json); rỗng nếu chưa có."""
    if not path.is_file():
        return {}, {}
    m = json.loads(path.read_text(encoding="utf-8"))
    xuoi = {e["old"]: e["new"] for e in m["entries"] if e.get("blob_before")}
    nguoc = {v: k for k, v in xuoi.items()}
    nguoc["docs/legacy/CURRENT_STATE_HISTORY.md"] = "docs/CURRENT_STATE.md"
    return xuoi, nguoc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    inv = json.loads((ROOT / a.inventory).read_text(encoding="utf-8"))
    frozen = {r["path"] for r in inv["docs"] if r["decision"] == "KEEP"
              and r["type"] in ("EXECUTION_EVIDENCE", "EXPERIMENT_PROTOCOL", "ARCHIVED_DECISION")}
    merge = {r["path"] for r in inv["docs"] if r["decision"] == "MERGE"}
    xuoi, nguoc = ban_do(ROOT / Path(a.inventory).parent / "MIGRATION_MAP.json")
    files = [p for p in git("ls-files", "*.md").splitlines() if p and not p.startswith("backend/app/ai/skills/")]
    files += [p for p in git("ls-files", "--others", "--exclude-standard", "*.md").splitlines() if p.startswith(RUN)]
    cache: dict[Path, set[str]] = {}
    hong = []
    dem = {"LIVING": 0, "FROZEN": 0, "ARCHIVED": 0}
    qua_ban_do = 0
    for p in sorted(set(files)):
        f = ROOT / p
        if not f.is_file():
            continue
        cl = lop(p, frozen, merge)
        dem[cl] += 1
        # FROZEN/ARCHIVED không sửa: link của chúng viết cho vị trí GỐC; đích đã đi thì tra bảng di chuyển
        goc_dir = (ROOT / nguoc.get(p, p)).parent if cl != "LIVING" else f.parent
        in_fence = False
        for no, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in LINK.finditer(line):
                t = m.group(1)
                if re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I):
                    continue
                duong, _, neo = unquote(t).partition("#")
                dich = (goc_dir / duong).resolve() if duong else f
                if duong and not dich.exists() and cl != "LIVING":
                    rel = dich.relative_to(ROOT).as_posix() if dich.is_relative_to(ROOT) else ""
                    if rel in xuoi and (ROOT / xuoi[rel]).exists():
                        dich = ROOT / xuoi[rel]
                        qua_ban_do += 1
                if duong and not dich.exists():
                    hong.append({"class": cl, "file": p, "line": no, "kind": "MISSING_TARGET", "target": t})
                elif neo and dich.is_file() and dich.suffix == ".md" and neo.lower() not in anchors(dich, cache):
                    hong.append({"class": cl, "file": p, "line": no, "kind": "MISSING_ANCHOR", "target": t})
            if cl == "LIVING":
                for m in TICK.finditer(line):
                    t = m.group(1).rstrip(".,;:)").split("#")[0].split("§")[0].strip()
                    if t and not (ROOT / t).exists():
                        hong.append({"class": cl, "file": p, "line": no, "kind": "MISSING_BACKTICK_PATH", "target": t})
    tom = {}
    for h in hong:
        k = f"{h['class']}:{h['kind']}"
        tom[k] = tom.get(k, 0) + 1
    kq = {"schema_version": "w19-doc-links/1", "head": git("rev-parse", "HEAD").strip(),
          "files_checked": dem, "frozen_or_archived_links_resolved_via_migration_map": qua_ban_do,
          "broken_total": len(hong), "broken_by_class_kind": dict(sorted(tom.items())), "broken": hong}
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: kq[k] for k in ("head", "files_checked", "frozen_or_archived_links_resolved_via_migration_map",
                                         "broken_total", "broken_by_class_kind")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
