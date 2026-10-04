# -*- coding: utf-8 -*-
"""W19 — ai còn nhắc ĐƯỜNG CŨ của file đã di chuyển (chỉ đọc).

Chạy từ gốc kho:
    backend/.venv/Scripts/python.exe <run>/diagnostics/check_old_path_consumers.py --map <run>/inventory/MIGRATION_MAP.json \
        --inventory <run>/inventory/INVENTORY.json --out <file.json>

Quét mọi file văn bản được theo dõi (+ file chưa theo dõi của run W19) tìm đúng chuỗi đường dẫn cũ `docs/…`
và đường cũ của thư mục đã biến mất. Phân lớp nơi nhắc:
  LIVING_DOC / CODE_OR_TEST / TOOL_SCRIPT  — phải bằng 0 (đã cập nhật hoặc có ngoại lệ ghi rõ);
  FROZEN_EVIDENCE / ARCHIVED / W19_RECORD   — được phép (bằng chứng đóng băng giữ nguyên; bảng di chuyển giải).
Tên file trần (không `docs/…`) không tính: tên giữ nguyên sau di chuyển.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
RUN = "docs/evaluation/geometry/runs/w19-docs-organization/"
TEXT = {".md", ".json", ".py", ".mjs", ".js", ".ts", ".tsx", ".txt", ".yml", ".yaml", ".toml", ".csv", ".html", ".css",
        ".sh", ".cfg", ".ini"}


def git(*a: str) -> str:
    return subprocess.run(["git", "-c", "core.quotePath=false", *a], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = json.loads((ROOT / a.map).read_text(encoding="utf-8"))
    inv = json.loads((ROOT / a.inventory).read_text(encoding="utf-8"))
    frozen = {r["path"] for r in inv["docs"] if r["decision"] == "KEEP"
              and r["type"] in ("EXECUTION_EVIDENCE", "EXPERIMENT_PROTOCOL", "ARCHIVED_DECISION")}
    merge = {r["path"] for r in inv["docs"] if r["decision"] == "MERGE"}  # lưu trữ nguyên byte, không sửa
    cu = sorted({e["old"] for e in m["entries"] if e.get("blob_before") and (ROOT / e["new"]).exists()
                 and not (ROOT / e["old"]).exists()}, key=len, reverse=True)
    thu_muc = sorted({str(Path(o).parent).replace("\\", "/") + "/" for o in cu
                      if not (ROOT / Path(o).parent).exists()}, key=len, reverse=True)
    pat = re.compile(r"(?<![A-Za-z0-9_/.-])(" + "|".join(re.escape(x) for x in cu + thu_muc) + r")")
    files = [p for p in git("ls-files").splitlines() if p and Path(p).suffix.lower() in TEXT]
    files += [p for p in git("ls-files", "--others", "--exclude-standard").splitlines() if p.startswith(RUN)]
    hits = []
    for p in sorted(set(files)):
        if p == "CLAUDE.md":
            continue
        try:
            s = (ROOT / p).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for no, line in enumerate(s.splitlines(), 1):
            for mm in pat.finditer(line):
                if p.startswith(RUN):
                    cls = "W19_RECORD"
                elif p.startswith("docs/evaluation/") or p in frozen:
                    cls = "FROZEN_EVIDENCE"
                elif p.startswith("docs/legacy/") or p in merge:
                    cls = "ARCHIVED"
                elif p.startswith(("backend/scripts/", "frontend/scripts/", "scripts/", ".claude/")):
                    cls = "TOOL_SCRIPT"
                elif p.startswith(("backend/", "frontend/")):
                    cls = "CODE_OR_TEST"
                else:
                    cls = "LIVING_DOC"
                hits.append({"class": cls, "file": p, "line": no, "old_path": mm.group(1)})
    tom: dict[str, int] = {}
    for h in hits:
        tom[h["class"]] = tom.get(h["class"], 0) + 1
    must_zero = {k: v for k, v in tom.items() if k in ("LIVING_DOC", "CODE_OR_TEST", "TOOL_SCRIPT")}
    kq = {"schema_version": "w19-old-path-consumers/1", "head": git("rev-parse", "HEAD").strip(),
          "old_paths_checked": len(cu), "vanished_directories_checked": thu_muc, "hits_by_class": tom,
          "must_be_zero": must_zero, "verdict": "PASS" if not must_zero else "FAIL",
          "hits_requiring_action": [h for h in hits if h["class"] in must_zero],
          "allowed_hits_sample": [h for h in hits if h["class"] not in must_zero][:40]}
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: kq[k] for k in ("old_paths_checked", "vanished_directories_checked", "hits_by_class",
                                         "verdict")}, ensure_ascii=False, indent=1))
    for h in kq["hits_requiring_action"][:30]:
        print(" ", h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
