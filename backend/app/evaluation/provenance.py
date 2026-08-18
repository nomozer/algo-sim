"""Provenance Logging & Reproducibility Infrastructure.

Ghi nhận toàn bộ vết thực thi, metadata băm (Git SHA, Prompt Hash, Model ID),
và raw telemetry của từng bài toán trong benchmark để đảm bảo tính minh bạch và
khả năng tái lập 100% trong báo cáo khoa học.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any


def get_git_commit_hash() -> str:
    """Lấy Git commit SHA của commit hiện tại."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def is_git_clean() -> bool:
    """Kiểm tra xem working tree có clean (không có uncommitted changes) không."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return len(res.stdout.strip()) == 0
    except Exception:
        return False


def compute_sha256(data: str | bytes | dict | list) -> str:
    """Tính toán mã băm SHA-256 của dữ liệu."""
    if isinstance(data, (dict, list)):
        raw_bytes = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    elif isinstance(data, str):
        raw_bytes = data.encode("utf-8")
    else:
        raw_bytes = data
    return hashlib.sha256(raw_bytes).hexdigest()


class ProvenanceLogger:
    """Logger ghi nhận phiên chạy benchmark vào thư mục recorded/."""

    def __init__(self, run_id: str, base_dir: Path | None = None):
        self.run_id = run_id
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.git_commit = get_git_commit_hash()
        self.is_clean = is_git_clean()
        
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "recorded"
        self.output_dir = base_dir / run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.records: list[dict[str, Any]] = []

    def log_task(
        self,
        task_id: str,
        problem_text: str,
        model_id: str,
        temperature: float,
        classification: dict[str, Any] | None,
        attempts: list[dict[str, Any]],
        final_envelope: dict[str, Any] | None,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        duration_sec: float = 0.0,
    ) -> dict[str, Any]:
        prompt_hash = compute_sha256(problem_text)
        record = {
            "task_id": task_id,
            "problem_text": problem_text,
            "prompt_hash": prompt_hash,
            "git_commit": self.git_commit,
            "model_id": model_id,
            "temperature": temperature,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "duration_sec": duration_sec,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "llm_calls": len(attempts),
            "first_pass_ok": len(attempts) > 0 and attempts[0].get("ok", False),
            "repaired_by_cegis": len(attempts) > 1 and attempts[-1].get("ok", False),
            "classification": classification,
            "attempts": attempts,
            "final_envelope": final_envelope,
        }
        
        # Lưu file record riêng từng task
        task_file = self.output_dir / f"{task_id}.json"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
            
        self.records.append(record)
        return record

    def save_summary_manifest(self, extra_meta: dict[str, Any] | None = None) -> Path:
        manifest = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "git_commit": self.git_commit,
            "git_clean": self.is_clean,
            "total_tasks": len(self.records),
            "extra_metadata": extra_meta or {},
            "tasks_summary": [
                {
                    "task_id": r["task_id"],
                    "status": (r["final_envelope"] or {}).get("status", "unknown"),
                    "llm_calls": r["llm_calls"],
                    "first_pass_ok": r["first_pass_ok"],
                }
                for r in self.records
            ],
        }
        manifest_file = self.output_dir / "run_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        return manifest_file
