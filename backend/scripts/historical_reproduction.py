# -*- coding: utf-8 -*-
"""M17-RC1 §E chế độ 1 — HISTORICAL REPRODUCTION.

Dựng lại bằng chứng ĐÃ CÔNG BỐ bằng **worktree + generator + fixture LỊCH SỬ**
(checkout đúng commit của wave), rồi so TỪNG BYTE với file đã commit.

Khác hẳn chế độ 2 (`current_policy_replay`, xem `app/evaluation/wave_replay.py`):
ở đây pipeline/cổng cũng là bản LỊCH SỬ, nên byte-identical là kỳ vọng ĐÚNG.
"Cổng hiện tại từ chối fixture cũ" KHÔNG liên quan tới chế độ này.

    python scripts/historical_reproduction.py --out ../docs/evaluation/m17/rc1

Cần `git` và cây làm việc sạch. Worktree tạo trong thư mục tạm và dọn sau.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.wave_snapshots import FROZEN_WAVES, snapshot_for  # noqa: E402

_REPO = Path(__file__).resolve().parents[2]

# Lý do HỢP LỆ khi không tái lập được (không được bịa lý do ngoài danh sách).
BLOCKER_KINDS = (
    "dependency_nondeterminism",
    "missing_immutable_input",
    "missing_historical_generator",
    "unavailable_model_output",
)


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd or _REPO),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _reproduce(wave_id: str) -> dict:
    snap = snapshot_for(wave_id)
    if snap is None:
        return {"wave_id": wave_id, "status": "NO_SNAPSHOT",
                "blocker_kind": "missing_immutable_input"}

    wt = Path(tempfile.mkdtemp(prefix=f"histrepro_{wave_id}_"))
    out = Path(tempfile.mkdtemp(prefix=f"histout_{wave_id}_"))
    try:
        r = _git("worktree", "add", "-f", "--detach", str(wt), snap.git_commit)
        if r.returncode:
            return {"wave_id": wave_id, "status": "BLOCKED",
                    "blocker_kind": "missing_immutable_input",
                    "detail": f"không tạo được worktree tại {snap.git_commit[:12]}: {r.stderr[-200:]}"}

        gen = wt / "backend" / "scripts" / "generate_m17_wave0_artifacts.py"
        if not gen.exists():
            return {"wave_id": wave_id, "status": "BLOCKED",
                    "blocker_kind": "missing_historical_generator",
                    "detail": "generator không tồn tại tại commit của wave"}

        # Generator lịch sử ghi THẲNG vào docs/ của worktree (chưa có --out).
        # Worktree là bản sao riêng nên không đụng cây làm việc thật.
        run = subprocess.run(
            [sys.executable, "scripts/generate_m17_wave0_artifacts.py", "--wave", wave_id],
            cwd=str(wt / "backend"), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )
        produced_dir = wt / "docs" / "evaluation" / "m17" / wave_id
        if run.returncode or not produced_dir.exists():
            return {"wave_id": wave_id, "status": "BLOCKED",
                    "blocker_kind": "missing_historical_generator",
                    "detail": (run.stderr or run.stdout)[-300:]}

        published_dir = _REPO / "docs" / "evaluation" / "m17" / wave_id
        files, mismatched = {}, []
        for name in sorted(snap.artifact_sha256):
            made = produced_dir / name
            if not made.exists():
                mismatched.append(name)
                files[name] = {"reproduced": False, "reason": "generator không sinh file"}
                continue
            sha = hashlib.sha256(made.read_bytes()).hexdigest()
            pub_sha = hashlib.sha256((published_dir / name).read_bytes()).hexdigest()
            ok = sha == pub_sha == snap.artifact_sha256[name]
            entry = {"reproduced": ok, "regenerated_sha256": sha,
                     "published_sha256": pub_sha}
            if not ok and name.endswith(".json"):
                # Tách PROVENANCE khỏi DỮ LIỆU: generator lịch sử ghi
                # `run_meta.generated_at` bằng đồng hồ lúc chạy, nên byte-identical
                # là BẤT KHẢ THI theo cấu trúc — đó là `dependency_nondeterminism`,
                # không phải bằng chứng bị trôi. Cái phải khớp là phần `data`.
                a = json.loads(made.read_text(encoding="utf-8"))
                b = json.loads((published_dir / name).read_text(encoding="utf-8"))
                data_same = (json.dumps(a.get("data"), ensure_ascii=False, sort_keys=True)
                             == json.dumps(b.get("data"), ensure_ascii=False, sort_keys=True))
                differing = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                entry.update({
                    "data_identical": data_same,
                    "differing_top_level_keys": differing,
                    "blocker_kind": ("dependency_nondeterminism"
                                     if data_same and differing == ["run_meta"] else None),
                })
                if data_same and differing == ["run_meta"]:
                    entry["reproduced"] = "DATA_IDENTICAL_RUN_META_NONDETERMINISTIC"
                    files[name] = entry
                    continue
            files[name] = entry
            if not ok:
                mismatched.append(name)
        nondet = [n for n, f in files.items()
                  if f.get("blocker_kind") == "dependency_nondeterminism"]
        if mismatched:
            status = "MISMATCH"
        elif nondet:
            status = "DATA_IDENTICAL_RUN_META_NONDETERMINISTIC"
        else:
            status = "BYTE_IDENTICAL"
        return {
            "wave_id": wave_id,
            "git_commit": snap.git_commit,
            "input_snapshot_id": snap.input_snapshot_id,
            "status": status,
            "blocker_kind": "dependency_nondeterminism" if nondet else None,
            "nondeterministic_files": nondet,
            "artifact_count": len(files),
            "mismatched": mismatched,
            "files": files,
        }
    finally:
        _git("worktree", "remove", "--force", str(wt))
        _git("worktree", "prune")
        shutil.rmtree(out, ignore_errors=True)
        shutil.rmtree(wt, ignore_errors=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../docs/evaluation/m17/rc1")
    args = p.parse_args()

    waves = [_reproduce(w) for w in FROZEN_WAVES]
    ok = all(w["status"] in ("BYTE_IDENTICAL",
                             "DATA_IDENTICAL_RUN_META_NONDETERMINISTIC")
             for w in waves)
    payload = {
        "schema_version": "1",
        "mode": "historical_reproduction",
        "note": (
            "Dựng lại bằng worktree + generator + fixture LỊCH SỬ. Byte-identical "
            "là kỳ vọng ĐÚNG ở chế độ này. Việc cổng HIỆN TẠI từ chối fixture cũ "
            "thuộc chế độ current_policy_replay, KHÔNG tính là lỗi ở đây."
        ),
        "blocker_kinds_allowed": list(BLOCKER_KINDS),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "waves": waves,
        "all_reproduced": ok,
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "historical_reproduction_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for w in waves:
        print(f"{w['wave_id']}: {w['status']}"
              + (f" · lệch {w['mismatched']}" if w.get("mismatched") else "")
              + (f" · {w.get('blocker_kind')}" if w.get("blocker_kind") else ""))
    print(f"Artifact → {out / 'historical_reproduction_report.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
