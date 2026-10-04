# -*- coding: utf-8 -*-
"""W19 — danh tính bằng chứng lịch sử TRƯỚC / SAU (chỉ đọc).

Chạy từ gốc kho:
    backend/.venv/Scripts/python.exe <run>/diagnostics/verify_frozen_identity.py --base 6d0e6321 \
        --inventory <run>/inventory/INVENTORY.json --map <run>/inventory/MIGRATION_MAP.json --out <file.json>

So blob git (băm nội dung) giữa commit `--base` và INDEX hiện tại (= cây sẽ được commit):
  F1  mọi file dưới docs/evaluation/ tại base — cùng đường dẫn, cùng blob;
  F2  báo cáo/snapshot giữ chỗ theo R1 (inventory: KEEP + kiểu evidence/protocol/decision) — cùng đường, cùng blob;
  F3  file đã di chuyển — blob ở đường mới bằng blob cũ, hoặc nằm trong danh sách đổi nội dung có nhật ký;
  F4  FROZEN_HISTORICAL_HASHES (36 file, sha256) của collect_docs_provenance_evidence — khớp.
Digest = sha256 của danh sách "đường blob" đã sắp, cho F1+F2, tính ở base và ở index: phải bằng nhau.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
RUN = "docs/evaluation/geometry/runs/w19-docs-organization/"


def git(*a: str) -> str:
    return subprocess.run(["git", "-c", "core.quotePath=false", *a], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    base = git("rev-parse", a.base).strip()
    truoc = {}
    for line in git("ls-tree", "-r", base).splitlines():
        meta, path = line.split("\t", 1)
        truoc[path] = meta.split()[2]
    sau = {}
    for line in git("ls-files", "-s").splitlines():
        meta, path = line.split("\t", 1)
        sau[path] = meta.split()[1]
    inv = json.loads((ROOT / a.inventory).read_text(encoding="utf-8"))
    mp = json.loads((ROOT / a.map).read_text(encoding="utf-8"))

    f1 = sorted(p for p in truoc if p.startswith("docs/evaluation/"))
    f2 = sorted(r["path"] for r in inv["docs"] if r["decision"] == "KEEP"
                and r["type"] in ("EXECUTION_EVIDENCE", "EXPERIMENT_PROTOCOL", "ARCHIVED_DECISION"))
    lech = [{"set": "F1", "path": p, "base": truoc[p], "now": sau.get(p)} for p in f1 if sau.get(p) != truoc[p]]
    lech += [{"set": "F2", "path": p, "base": truoc.get(p), "now": sau.get(p)} for p in f2 if sau.get(p) != truoc.get(p)]

    f3_dong_nhat, f3_doi, f3_loi = 0, [], []
    for e in mp["entries"]:
        if not e.get("blob_before"):
            continue
        now = sau.get(e["new"])
        if e["old"] in sau:
            f3_loi.append({"path": e["old"], "problem": "old path still tracked"})
        if now == e["blob_before"]:
            f3_dong_nhat += 1
        elif now and e.get("content_changed") and e.get("changed_by"):
            f3_doi.append({"new": e["new"], "changed_by": e["changed_by"]})
        else:
            f3_loi.append({"path": e["new"], "problem": "blob differs without a recorded content change", "now": now})

    sys.path.insert(0, str(ROOT / "backend" / "scripts"))
    import collect_docs_provenance_evidence as C  # noqa: E402
    f4 = C.collect_historical_byte_integrity()

    def digest(bang_: dict[str, str], paths: list[str]) -> str:
        return hashlib.sha256("".join(f"{p} {bang_.get(p)}\n" for p in paths).encode()).hexdigest()

    kq = {"schema_version": "w19-frozen-identity/1", "base_commit": base, "compared_against": "git index (tree to commit)",
          "F1_docs_evaluation_files": len(f1), "F2_frozen_docs_kept_in_place": len(f2),
          "F1_F2_digest_base": digest(truoc, f1 + f2), "F1_F2_digest_now": digest(sau, f1 + f2),
          "F1_F2_mismatches": lech,
          "F3_moved_identical": f3_dong_nhat, "F3_moved_with_recorded_link_changes": f3_doi, "F3_problems": f3_loi,
          "F4_frozen_historical_hashes": {"checked": f4["total_files_checked"], "verdict": f4["verdict"]},
          "new_files_under_docs_evaluation": sorted(p for p in sau if p.startswith("docs/evaluation/")
                                                    and p not in truoc and not p.startswith(RUN))}
    ok = not lech and not f3_loi and f4["verdict"] == "PASS" and kq["F1_F2_digest_base"] == kq["F1_F2_digest_now"]
    kq["verdict"] = "PASS" if ok else "FAIL"
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in kq.items() if k not in ("F3_moved_with_recorded_link_changes",)},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
