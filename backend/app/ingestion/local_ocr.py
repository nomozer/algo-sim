# -*- coding: utf-8 -*-
"""Local OCR client: chạy `local_ocr_worker.py` như sidecar trong interpreter OCR riêng.

Bật bằng cấu hình (mặc định TẮT — tuyến văn bản và bộ nhớ backend không đổi):
- `LOCAL_OCR_PYTHON`: interpreter có `tesserocr` + `rapidocr` (vd. venv OCR riêng).
- `LOCAL_OCR_TESSDATA`: thư mục `vie.traineddata` (mặc định `tessdata_fast`).
- `LOCAL_OCR_TIMEOUT_S`: trần thời gian mỗi lượt nhận dạng (mặc định 90 s, gồm nạp mô hình lần đầu).

Worker sống lâu để không nạp lại mô hình mỗi request; chết/treo ⇒ dựng lại ở lượt sau.
Cache trong bộ nhớ theo SHA-256 ảnh (giới hạn `_CACHE_MAX` mục, chỉ giữ kết quả OCR — KHÔNG
giữ byte ảnh), nên học sinh sửa văn bản không làm OCR chạy lại.
"""
from __future__ import annotations

import base64
import atexit
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

LOCAL_OCR_RAW_SCHEMA = "local-ocr-raw/1"
LOCAL_OCR_WORKER_VERSION = "local-ocr-worker/5"
_WORKER_PATH = Path(__file__).with_name("local_ocr_worker.py")
_CACHE_MAX = 16
_RAW_OCR_CACHE_MAX = 32
_REREAD_CACHE_MAX = 512
_RAW_OCR_CACHE: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_REREAD_CACHE: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_CACHE = _RAW_OCR_CACHE
_LOCK = threading.Lock()


def local_ocr_config() -> dict[str, Any] | None:
    py = (os.getenv("LOCAL_OCR_PYTHON") or "").strip()
    if not py:
        return None
    tessdata = (os.getenv("LOCAL_OCR_TESSDATA") or "").strip()
    if not py or not Path(py).exists() or not tessdata or not Path(tessdata).is_dir():
        return {"available": False, "python": py, "tessdata": tessdata, "reason": "LOCAL_OCR_MISCONFIGURED"}
    try:
        timeout = float(os.getenv("LOCAL_OCR_TIMEOUT_S") or "90")
    except ValueError:
        timeout = 90.0
    return {"available": True, "python": py, "tessdata": tessdata, "timeout_s": timeout}


def local_ocr_available() -> bool:
    cfg = local_ocr_config()
    return bool(cfg and cfg.get("available"))


class _Worker:
    def __init__(self, python: str) -> None:
        self.python = python
        self.proc: subprocess.Popen[str] | None = None
        self.out: "queue.Queue[str | None]" = queue.Queue()
        self.started_at: float | None = None

    def _reader(self, stream, output) -> None:  # pragma: no cover - thread
        try:
            for line in stream:
                output.put(line)
        finally:
            output.put(None)

    def ensure(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            return
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        self.proc = subprocess.Popen(
            [self.python, "-u", str(_WORKER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            env=env,
            creationflags=flags,
        )
        self.out = queue.Queue()
        threading.Thread(target=self._reader, args=(self.proc.stdout, self.out), daemon=True).start()
        self.started_at = time.perf_counter()

    def request(self, payload: dict[str, Any], timeout_s: float) -> dict[str, Any]:
        self.ensure()
        assert self.proc is not None and self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        try:
            line = self.out.get(timeout=timeout_s)
        except queue.Empty:
            self.kill()
            raise TimeoutError("LOCAL_OCR_TIMEOUT") from None
        if line is None:
            self.kill()
            raise OSError("LOCAL_OCR_WORKER_EXITED")
        response = json.loads(line)
        if not isinstance(response, dict):
            raise ValueError("LOCAL_OCR_RESPONSE_INVALID")
        return response

    def kill(self) -> None:
        if self.proc is not None:
            try:
                self.proc.kill()
                self.proc.wait(timeout=5)
            except OSError:
                pass
            finally:
                for stream in (self.proc.stdin, self.proc.stdout):
                    if stream is not None:
                        stream.close()
        self.proc = None

    def pid(self) -> int | None:
        return self.proc.pid if self.proc is not None and self.proc.poll() is None else None


_WORKER: _Worker | None = None


def shutdown_local_ocr() -> None:
    global _WORKER
    with _LOCK:
        if _WORKER is not None:
            _WORKER.kill()
        _WORKER = None


atexit.register(shutdown_local_ocr)


def clear_local_ocr_cache() -> None:
    with _LOCK:
        _RAW_OCR_CACHE.clear()
        _REREAD_CACHE.clear()


def local_ocr_worker_pid() -> int | None:
    return _WORKER.pid() if _WORKER is not None else None


def reread_local_ocr_regions(image_bytes: bytes, boxes: list[list[int]]) -> dict[str, Any]:
    """Đọc lại các vùng tranh chấp bằng bộ nhận dạng thứ 3/4, gom trùng và cache theo từng hộp bao. Không ném lỗi."""
    global _WORKER
    cfg = local_ocr_config()
    if not cfg or not cfg.get("available") or not boxes:
        return {"ok": False, "readings": [], "reason": "LOCAL_OCR_DISABLED" if not boxes else None}
    sha = hashlib.sha256(image_bytes).hexdigest()
    norm_boxes = [[int(v) for v in b] for b in boxes]
    box_keys = [f"reread:{LOCAL_OCR_WORKER_VERSION}:{sha}:{json.dumps(b)}:{cfg['tessdata']}" for b in norm_boxes]

    readings_out: list[dict[str, Any] | None] = [None] * len(norm_boxes)
    miss_unique: dict[str, list[int]] = {}
    miss_indices: dict[str, list[int]] = {}
    cache_hits = 0

    with _LOCK:
        for idx, (b, bkey) in enumerate(zip(norm_boxes, box_keys)):
            hit = _REREAD_CACHE.get(bkey)
            if hit is not None:
                _REREAD_CACHE.move_to_end(bkey)
                readings_out[idx] = hit
                cache_hits += 1
            else:
                if bkey not in miss_unique:
                    miss_unique[bkey] = b
                    miss_indices[bkey] = []
                miss_indices[bkey].append(idx)

        if not miss_unique:
            return {
                "ok": True,
                "worker_version": LOCAL_OCR_WORKER_VERSION,
                "readings": [r or {} for r in readings_out],
                "worker_ms": 0.0,
                "total_ms": 0.0,
                "cached": True,
                "cache_hits": cache_hits,
                "unique_requested": 0,
            }

        if _WORKER is None or _WORKER.python != cfg["python"]:
            if _WORKER is not None:
                _WORKER.kill()
            _WORKER = _Worker(cfg["python"])
        req_keys = list(miss_unique.keys())
        req_boxes = [miss_unique[k] for k in req_keys]
        t0 = time.perf_counter()
        try:
            resp = _WORKER.request(
                {"op": "reread", "id": sha[:12], "image_b64": base64.b64encode(image_bytes).decode("ascii"),
                 "boxes": req_boxes, "tessdata": cfg["tessdata"]},
                timeout_s=float(cfg["timeout_s"]),
            )
        except (TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            if _WORKER is not None:
                _WORKER.kill()
            return {"ok": False, "readings": [], "reason": f"LOCAL_OCR_WORKER_FAILED:{type(exc).__name__}"}

        fetched = resp.get("readings") or []
        ok = bool(resp.get("ok"))
        for bkey, rd in zip(req_keys, fetched):
            entry = rd if isinstance(rd, dict) else {}
            if ok:
                _REREAD_CACHE[bkey] = entry
                while len(_REREAD_CACHE) > _REREAD_CACHE_MAX:
                    _REREAD_CACHE.popitem(last=False)
            for idx in miss_indices[bkey]:
                readings_out[idx] = entry
        return {
            "ok": ok,
            "worker_version": resp.get("worker_version") or LOCAL_OCR_WORKER_VERSION,
            "readings": [r or {} for r in readings_out],
            "worker_ms": resp.get("ms"),
            "decode_ms": resp.get("decode_ms"),
            "timings": resp.get("timings"),
            "total_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            "cached": False,
            "cache_hits": cache_hits,
            "unique_requested": len(req_boxes),
        }


def run_local_ocr(image_bytes: bytes, *, engines: tuple[str, ...] = ("tesseract", "rapidocr")) -> dict[str, Any]:
    """Nhận dạng ảnh bằng các engine local. Không bao giờ ném lỗi: thất bại ⇒ `ok=False` + `reason`."""
    global _WORKER
    cfg = local_ocr_config()
    if not cfg or not cfg.get("available"):
        return {"schema": LOCAL_OCR_RAW_SCHEMA, "ok": False, "reason": (cfg or {}).get("reason", "LOCAL_OCR_DISABLED")}
    sha = hashlib.sha256(image_bytes).hexdigest()
    key = f"{LOCAL_OCR_WORKER_VERSION}:{sha}:{','.join(engines)}:{cfg['tessdata']}"
    with _LOCK:
        hit = _RAW_OCR_CACHE.get(key)
        if hit is not None:
            _RAW_OCR_CACHE.move_to_end(key)
            return {**hit, "cached": True, "total_ms": 0.0}
        t0 = time.perf_counter()
        cold = _WORKER is None or _WORKER.pid() is None
        if _WORKER is None or _WORKER.python != cfg["python"]:
            if _WORKER is not None:
                _WORKER.kill()
            _WORKER = _Worker(cfg["python"])
        try:
            resp = _WORKER.request(
                {
                    "id": sha[:12],
                    "image_b64": base64.b64encode(image_bytes).decode("ascii"),
                    "engines": list(engines),
                    "tessdata": cfg["tessdata"],
                    "tess_lang": "vie",
                },
                timeout_s=float(cfg["timeout_s"]),
            )
        except (TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            if _WORKER is not None:
                _WORKER.kill()
            return {"schema": LOCAL_OCR_RAW_SCHEMA, "ok": False, "reason": f"LOCAL_OCR_WORKER_FAILED:{type(exc).__name__}"}
        out = {
            "schema": LOCAL_OCR_RAW_SCHEMA,
            "worker_version": resp.get("worker_version") or LOCAL_OCR_WORKER_VERSION,
            "ok": bool(resp.get("ok")),
            "reason": None if resp.get("ok") else "LOCAL_OCR_ENGINE_FAILED",
            "image_sha256": sha,
            "width": resp.get("width"),
            "height": resp.get("height"),
            "decode_ms": resp.get("decode_ms"),
            "engines": resp.get("engines") or {},
            "cold_worker": cold,
            "cached": False,
            "total_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        }
        if out["ok"]:
            _RAW_OCR_CACHE[key] = out
            while len(_RAW_OCR_CACHE) > _RAW_OCR_CACHE_MAX:
                _RAW_OCR_CACHE.popitem(last=False)
        return out
