# -*- coding: utf-8 -*-
"""W19 — viết lại đường dẫn tới tài liệu đã di chuyển, CHỈ trong tài liệu sống; sinh MIGRATION_MAP.json.

Chạy từ gốc kho, SAU `git mv` (cây làm việc đã ở vị trí mới):
    backend/.venv/Scripts/python.exe <run>/diagnostics/rewrite_doc_paths.py --inventory <run>/inventory/INVENTORY.json \
        --log <run>/inventory/REWRITE_LOG.json [--map <run>/inventory/MIGRATION_MAP.json] [--dry-run]

Cặp di chuyển = các dòng inventory có quyết định MOVE/ARCHIVE (MERGE xử lý ở bước sau, cùng bản đồ tuyên bố).
Không đụng: docs/evaluation/** (đóng băng), file giữ chỗ theo R1 (KEEP + kiểu evidence/protocol/decision),
file đã vào docs/legacy/ (lưu trữ nguyên byte), file MERGE (sắp lưu trữ nguyên byte), run folder W19.
Hai phép viết lại, đều tất định:
  (a) link markdown tương đối: giải theo vị trí CŨ của file chứa link, ánh xạ đích qua bảng di chuyển, rồi tính
      lại đường tương đối từ vị trí MỚI (giữ #anchor);
  (b) chuỗi `docs/…`: đường cũ đúng một file ⇒ đường mới; tiền tố của đúng một file đã di chuyển ⇒ thay phần thư mục.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[6]
RUN = "docs/evaluation/geometry/runs/w19-docs-organization/"
LINK = re.compile(r"(!?\[(?:[^\]\[]|\[[^\]]*\])*\]\(\s*<?)([^)\s>]+)(>?(?:\s+\"[^\"]*\")?\s*\))")
DOCS_TOKEN = re.compile(r"(?<![A-Za-z0-9_/.-])docs/[A-Za-z0-9_./-]*[A-Za-z0-9_/]")
FENCE = re.compile(r"^\s*(```|~~~)")


def git(*a: str) -> str:
    return subprocess.run(["git", "-c", "core.quotePath=false", *a], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--map")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    inv = json.loads((ROOT / a.inventory).read_text(encoding="utf-8"))
    moves = {r["path"]: r["destination"] for r in inv["docs"] if r["decision"] in ("MOVE", "ARCHIVE")}
    inverse = {v: k for k, v in moves.items()}
    khong_sua = {r["path"] for r in inv["docs"] if r["decision"] == "MERGE" or (
        r["decision"] == "KEEP" and r["type"] in ("EXECUTION_EVIDENCE", "EXPERIMENT_PROTOCOL", "ARCHIVED_DECISION"))}

    def song(p: str) -> bool:
        return not (p.startswith(("docs/evaluation/", "docs/legacy/")) or p in khong_sua)

    files = [p for p in git("ls-files", "*.md").splitlines()
             if p and song(p) and not p.startswith("backend/app/ai/skills/")]
    log = []
    for p_new in files:
        p_old = inverse.get(p_new, p_new)
        d_old, d_new = posixpath.dirname(p_old), posixpath.dirname(p_new)
        f = ROOT / p_new
        lines = f.read_text(encoding="utf-8").split("\n")
        in_fence = False
        doi = False
        for i, line in enumerate(lines):
            goc = line
            if FENCE.match(line):
                in_fence = not in_fence
            if not in_fence:
                def thay_link(m: re.Match) -> str:
                    t = m.group(2)
                    if re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I) or t.startswith("#"):
                        return m.group(0)
                    duong, sep, neo = t.partition("#")
                    abs_old = posixpath.normpath(posixpath.join(d_old, unquote(duong))) if duong else p_old
                    dich = moves.get(abs_old, abs_old)
                    if not (ROOT / dich).exists():
                        return m.group(0)
                    moi = posixpath.relpath(dich, d_new) if dich != p_new else posixpath.basename(dich)
                    if duong.endswith("/") and not moi.endswith("/"):
                        moi += "/"
                    if posixpath.normpath(moi) == posixpath.normpath(unquote(duong)):
                        return m.group(0)
                    return m.group(1) + moi + (sep + neo if sep else "") + m.group(3)
                line = LINK.sub(thay_link, line)

            def thay_token(m: re.Match) -> str:
                t = m.group(0)
                if t in moves:
                    return moves[t]
                ung = [o for o in moves if o.startswith(t) and len(o) > len(t)]
                if len(ung) == 1 and not (ROOT / t).exists():
                    o = ung[0]
                    return moves[o][: len(moves[o]) - (len(o) - len(t))]
                return t
            line = DOCS_TOKEN.sub(thay_token, line)
            if line != goc:
                lines[i] = line
                doi = True
                log.append({"file": p_new, "line": i + 1, "before": goc, "after": line})
        if doi and not a.dry_run:
            f.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    out = ROOT / a.log
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"schema_version": "w19-rewrite-log/1", "dry_run": a.dry_run,
                               "files_scanned": len(files), "lines_changed": len(log),
                               "files_changed": sorted({x["file"] for x in log}), "changes": log},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"files_scanned": len(files), "lines_changed": len(log),
                      "files_changed": len({x["file"] for x in log})}, ensure_ascii=False))

    if a.map:
        base = inv["base_commit"]
        rows = []
        for r in inv["docs"]:
            if r["decision"] not in ("MOVE", "ARCHIVE", "MERGE"):
                continue
            moi = r["destination"]
            after = git("hash-object", "--", moi).strip() if (ROOT / moi).exists() else None
            rows.append({"old": r["path"], "new": moi, "decision": r["decision"], "type": r["type"],
                         "reason": r["reason"], "blob_before": r["blob_at_base"], "blob_after": after,
                         "content_changed": (after is not None and after != r["blob_at_base"]),
                         "content_change_reason": ("relative links/paths rewritten for the new location "
                                                   "(see REWRITE_LOG.json)") if (after and after != r["blob_at_base"])
                         else None})
        rows.append({"old": "docs/CURRENT_STATE.md (lines 88-5475 at " + base[:8] + ")",
                     "new": "docs/legacy/CURRENT_STATE_HISTORY.md (body below the 15-line provenance header)",
                     "decision": "ARCHIVE", "type": "EXECUTION_EVIDENCE",
                     "reason": "R7: CURRENT_STATE keeps state + pointers; development log moved verbatim",
                     "verify": "diff <(tail -n +16 docs/legacy/CURRENT_STATE_HISTORY.md) "
                               "<(git show " + base[:8] + ":docs/CURRENT_STATE.md | sed -n 88,5475p)"})
        m = ROOT / a.map
        m.write_text(json.dumps({"schema_version": "w19-migration-map/1", "base_commit": base,
                                 "rule": "Old paths named by frozen artifacts or archived documents resolve here. "
                                         "Moved files keep their basename. blob = git blob id (LF).",
                                 "entries": rows}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8", newline="\n")
        print(f"map: {len(rows)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
