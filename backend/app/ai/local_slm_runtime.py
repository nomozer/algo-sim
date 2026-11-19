"""Local CPU Small Language Model (SLM) runtime manager for Axo Hybrid /5.

Manages pinned, checksum-verified provisioning and lazy single-instance local
``llama-server.exe`` execution over loopback HTTP (``127.0.0.1``) with strict
concurrency bounds, timeout/crash recovery, and Win32 RSS measurement.
"""

from __future__ import annotations

import atexit
from collections import OrderedDict
from dataclasses import asdict, dataclass
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from typing import Any
import zipfile

import httpx

if os.name == "nt":
    import ctypes
    from ctypes import wintypes


LOCAL_SLM_RUNTIME_VERSION = "local-slm-runtime/3"
LOCAL_SLM_RUNTIME_V9_VERSION = "local-slm-runtime/4"
LOCAL_SLM_CACHE_NAMESPACE = "HYBRID_V7_LOCAL_SLM"
LOCAL_SLM_CACHE_V9_NAMESPACE = "HYBRID_V9_LOCAL_SLM"
DEFAULT_LOCAL_SLM_MODEL_KEY = "qwen3-0.6b-q4_k_m"
FINETUNED_LOCAL_SLM_MODEL_KEY = "qwen3-0.6b-axo-v7-q4_k_m"
V9_LOCAL_SLM_MODEL_KEY = "qwen3-0.6b-axo-v9-q4_k_m"
COMPARATOR_LOCAL_SLM_MODEL_KEY = "qwen2.5-0.5b-instruct-q4_k_m"
DEFAULT_LOCAL_SLM_CTX_SIZE = 2048
DEFAULT_LOCAL_SLM_MAX_TOKENS = 512
DEFAULT_LOCAL_SLM_THREADS = 6
DEFAULT_LOCAL_SLM_REQUEST_TIMEOUT_S = 45.0
DEFAULT_LOCAL_SLM_STARTUP_TIMEOUT_S = 45.0
DEFAULT_LOCAL_SLM_MAX_QUEUE = 4

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
_SHA256_STAT_CACHE: dict[str, tuple[int, int, str]] = {}
_SHA256_CACHE_LOCK = threading.Lock()


@dataclass(frozen=True)
class LlamaCppRuntimeSpec:
    release_tag: str
    asset_name: str
    url: str
    size_bytes: int
    sha256: str
    license: str
    server_binary_name: str = "llama-server.exe"


@dataclass(frozen=True)
class LocalSlmModelSpec:
    model_key: str
    role: str
    repo_id: str
    revision: str
    filename: str
    url: str
    size_bytes: int
    sha256: str
    license: str
    family: str
    param_count_b: float
    quantization: str
    supports_thinking: bool


LLAMA_CPP_RUNTIME_SPEC = LlamaCppRuntimeSpec(
    release_tag="b12470",
    asset_name="llama-b12470-bin-win-cpu-x64.zip",
    url="https://github.com/ggml-org/llama.cpp/releases/download/b12470/llama-b12470-bin-win-cpu-x64.zip",
    size_bytes=25272394,
    sha256="fc83371644b501647c253ca1e42277795eca7ed15851a218b20294275b45d67f",
    license="MIT",
)

LOCAL_SLM_MODELS: dict[str, LocalSlmModelSpec] = {
    "qwen3-0.6b-q4_k_m": LocalSlmModelSpec(
        model_key="qwen3-0.6b-q4_k_m",
        role="primary",
        repo_id="unsloth/Qwen3-0.6B-GGUF",
        revision="50968a4468ef4233ed78cd7c3de230dd1d61a56b",
        filename="Qwen3-0.6B-Q4_K_M.gguf",
        url=(
            "https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/"
            "50968a4468ef4233ed78cd7c3de230dd1d61a56b/Qwen3-0.6B-Q4_K_M.gguf"
        ),
        size_bytes=396705472,
        sha256="ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a",
        license="Apache-2.0",
        family="qwen3",
        param_count_b=0.6,
        quantization="Q4_K_M",
        supports_thinking=True,
    ),
    "qwen3-0.6b-axo-v7-q4_k_m": LocalSlmModelSpec(
        model_key="qwen3-0.6b-axo-v7-q4_k_m",
        role="finetuned",
        repo_id="local/Qwen3-0.6B-AxoV7-LoRA-Merged",
        revision="c1899de289a04d12100db370d81485cdf75e47ca+axo-v7-lora",
        filename="Qwen3-0.6B-AxoV7-Q4_K_M.gguf",
        url="",
        size_bytes=396704736,
        sha256="36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148",
        license="Apache-2.0",
        family="qwen3",
        param_count_b=0.6,
        quantization="Q4_K_M",
        supports_thinking=True,
    ),
    "qwen3-0.6b-axo-v9-q4_k_m": LocalSlmModelSpec(
        model_key="qwen3-0.6b-axo-v9-q4_k_m",
        role="finetuned",
        repo_id="local/Qwen3-0.6B-AxoV9-LoRA-Merged",
        revision="c1899de289a04d12100db370d81485cdf75e47ca+axo-v9-lora",
        filename="Qwen3-0.6B-AxoV9-Q4_K_M.gguf",
        url="",
        size_bytes=396704736,
        sha256="73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35",
        license="Apache-2.0",
        family="qwen3",
        param_count_b=0.6,
        quantization="Q4_K_M",
        supports_thinking=True,
    ),
    "qwen2.5-0.5b-instruct-q4_k_m": LocalSlmModelSpec(
        model_key="qwen2.5-0.5b-instruct-q4_k_m",
        role="comparator",
        repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        revision="9217f5db79a29953eb74d5343926648285ec7e67",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        url=(
            "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/"
            "9217f5db79a29953eb74d5343926648285ec7e67/qwen2.5-0.5b-instruct-q4_k_m.gguf"
        ),
        size_bytes=491400032,
        sha256="74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db",
        license="Apache-2.0",
        family="qwen2.5",
        param_count_b=0.5,
        quantization="Q4_K_M",
        supports_thinking=False,
    ),
}


class LocalSlmRuntimeError(RuntimeError):
    """Typed infrastructure error for local SLM provisioning or inference."""

    def __init__(self, reason_code: str, detail: str, *, status_code: int = 503) -> None:
        super().__init__(detail)
        self.reason_code = str(reason_code)
        self.detail = str(detail)
        self.status_code = int(status_code)


ACTIVE_MODEL_STATE_FILENAME = "active_model.json"


def read_active_local_slm_model_key(cache_dir: str | Path | None = None) -> str | None:
    path = resolve_local_slm_cache_dir(cache_dir) / ACTIVE_MODEL_STATE_FILENAME
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    candidate = str(payload.get("model_key") or "").strip().lower() if isinstance(payload, dict) else ""
    if candidate in LOCAL_SLM_MODELS:
        return candidate
    return None


def write_active_local_slm_model_key(
    model_key: str,
    *,
    reason: str = "",
    cache_dir: str | Path | None = None,
) -> Path:
    spec = resolve_local_slm_model_spec(model_key)
    root = resolve_local_slm_cache_dir(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    target = root / ACTIVE_MODEL_STATE_FILENAME
    tmp = root / f".{ACTIVE_MODEL_STATE_FILENAME}.{os.getpid()}.tmp"
    payload = {
        "schema": "axo-local-slm-active-model/1",
        "model_key": spec.model_key,
        "sha256": spec.sha256,
        "reason": str(reason or "").strip(),
        "updated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return target


def resolve_local_slm_model_spec(model_key: str | None = None) -> LocalSlmModelSpec:
    raw = str(model_key or os.getenv("LOCAL_SLM_MODEL") or "").strip().lower()
    if raw in {"", "default", "primary"}:
        raw = DEFAULT_LOCAL_SLM_MODEL_KEY
    elif raw in {"finetuned", "v7", "axo-v7"}:
        raw = FINETUNED_LOCAL_SLM_MODEL_KEY
    elif raw in {"v9", "axo-v9", "v9-default"}:
        raw = V9_LOCAL_SLM_MODEL_KEY
    elif raw in {"active", "v9-active"}:
        raw = read_active_local_slm_model_key() or V9_LOCAL_SLM_MODEL_KEY
    elif raw == "comparator":
        raw = COMPARATOR_LOCAL_SLM_MODEL_KEY
    spec = LOCAL_SLM_MODELS.get(raw)
    if spec is None:
        raise LocalSlmRuntimeError(
            "INVALID_LOCAL_SLM_MODEL",
            f"Unsupported local SLM model '{model_key}'. Expected one of {sorted(LOCAL_SLM_MODELS)}.",
            status_code=503,
        )
    return spec


def resolve_local_slm_cache_dir(cache_dir: str | Path | None = None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir).expanduser().resolve()
    env_dir = str(os.getenv("LOCAL_SLM_CACHE_DIR") or "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    local_app_data = str(os.getenv("LOCALAPPDATA") or "").strip()
    if local_app_data:
        return (Path(local_app_data) / "axo-slm").resolve()
    return (Path.home() / ".cache" / "axo-slm").resolve()


def resolve_default_threads(threads: int | None = None) -> int:
    if threads is not None and threads > 0:
        return int(threads)
    env_val = str(os.getenv("LOCAL_SLM_THREADS") or "").strip()
    if env_val.isdigit() and int(env_val) > 0:
        return int(env_val)
    return DEFAULT_LOCAL_SLM_THREADS


def _compute_sha256(path: Path, *, force_rehash: bool = False) -> str:
    stat = path.stat()
    key = str(path.resolve())
    if not force_rehash:
        with _SHA256_CACHE_LOCK:
            cached = _SHA256_STAT_CACHE.get(key)
            if cached and cached[0] == stat.st_size and cached[1] == stat.st_mtime_ns:
                return cached[2]
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(4 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    sha_hex = digest.hexdigest().lower()
    with _SHA256_CACHE_LOCK:
        _SHA256_STAT_CACHE[key] = (stat.st_size, stat.st_mtime_ns, sha_hex)
    return sha_hex


def _download_verified_file(
    *,
    url: str,
    dest_path: Path,
    expected_size: int,
    expected_sha256: str,
    timeout_s: float = 600.0,
) -> dict[str, Any]:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    part_path = dest_path.with_name(f"{dest_path.name}.part.{os.getpid()}")
    hasher = hashlib.sha256()
    total_bytes = 0
    started = time.perf_counter()
    try:
        with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(timeout_s, connect=20.0)) as client:
            with client.stream("GET", url) as resp:
                if resp.status_code >= 400:
                    raise LocalSlmRuntimeError(
                        "MODEL_RUNTIME_UNAVAILABLE",
                        f"Download failed HTTP {resp.status_code} for {url}",
                    )
                with part_path.open("wb") as out_fh:
                    for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        out_fh.write(chunk)
                        hasher.update(chunk)
                        total_bytes += len(chunk)
        actual_sha = hasher.hexdigest().lower()
        if total_bytes != expected_size:
            raise LocalSlmRuntimeError(
                "MODEL_CHECKSUM_MISMATCH",
                f"Downloaded size mismatch for {dest_path.name}: got {total_bytes}, expected {expected_size}.",
            )
        if actual_sha != expected_sha256.lower():
            raise LocalSlmRuntimeError(
                "MODEL_CHECKSUM_MISMATCH",
                f"Downloaded SHA-256 mismatch for {dest_path.name}: got {actual_sha}, expected {expected_sha256}.",
            )
        os.replace(part_path, dest_path)
    except Exception:
        try:
            if part_path.exists():
                part_path.unlink()
        except OSError:
            pass
        raise
    stat = dest_path.stat()
    with _SHA256_CACHE_LOCK:
        _SHA256_STAT_CACHE[str(dest_path.resolve())] = (stat.st_size, stat.st_mtime_ns, expected_sha256.lower())
    return {
        "downloaded": True,
        "elapsed_s": round(time.perf_counter() - started, 3),
        "size_bytes": total_bytes,
        "sha256": expected_sha256.lower(),
    }


def _find_server_executable(root_dir: Path, binary_name: str) -> Path | None:
    direct = root_dir / binary_name
    if direct.is_file():
        return direct
    for candidate in root_dir.rglob(binary_name):
        if candidate.is_file():
            return candidate
    return None


def _safe_extract_zip(zip_path: Path, runtime_dir: Path, runtime_spec: LlamaCppRuntimeSpec) -> Path:
    tmp_dir = runtime_dir.with_name(f"{runtime_dir.name}.extract.{os.getpid()}")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_resolved = tmp_dir.resolve()
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                member_path = (tmp_dir / member.filename).resolve()
                if tmp_resolved not in member_path.parents and member_path != tmp_resolved:
                    raise LocalSlmRuntimeError(
                        "MODEL_RUNTIME_UNAVAILABLE",
                        f"Unsafe zip member path in {zip_path.name}: {member.filename}",
                    )
            zf.extractall(tmp_dir)
        server_exe = _find_server_executable(tmp_dir, runtime_spec.server_binary_name)
        if server_exe is None:
            raise LocalSlmRuntimeError(
                "MODEL_RUNTIME_UNAVAILABLE",
                f"{runtime_spec.server_binary_name} not found inside {zip_path.name}.",
            )
        manifest = {
            "release_tag": runtime_spec.release_tag,
            "asset_name": runtime_spec.asset_name,
            "size_bytes": runtime_spec.size_bytes,
            "sha256": runtime_spec.sha256,
            "license": runtime_spec.license,
            "server_rel_path": str(server_exe.relative_to(tmp_dir)),
        }
        (tmp_dir / ".provision_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if runtime_dir.exists():
            shutil.rmtree(runtime_dir)
        os.replace(tmp_dir, runtime_dir)
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    final_exe = _find_server_executable(runtime_dir, runtime_spec.server_binary_name)
    if final_exe is None:
        raise LocalSlmRuntimeError(
            "MODEL_RUNTIME_UNAVAILABLE",
            f"Server binary disappeared after extracting into {runtime_dir}.",
        )
    return final_exe


def _verify_runtime_dir(runtime_dir: Path, runtime_spec: LlamaCppRuntimeSpec) -> Path | None:
    manifest_path = runtime_dir / ".provision_manifest.json"
    if not runtime_dir.is_dir() or not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if (
        manifest.get("release_tag") != runtime_spec.release_tag
        or manifest.get("sha256") != runtime_spec.sha256
        or manifest.get("size_bytes") != runtime_spec.size_bytes
    ):
        return None
    rel = str(manifest.get("server_rel_path") or runtime_spec.server_binary_name)
    server_exe = (runtime_dir / rel).resolve()
    if not server_exe.is_file():
        return None
    return server_exe


@dataclass(frozen=True)
class ProvisionedLocalSlm:
    cache_dir: Path
    runtime_dir: Path
    server_executable: Path
    model_path: Path
    model_spec: LocalSlmModelSpec
    runtime_spec: LlamaCppRuntimeSpec
    downloaded_runtime: bool
    downloaded_model: bool

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
            "cache_dir": str(self.cache_dir),
            "runtime_dir": str(self.runtime_dir),
            "server_executable": str(self.server_executable),
            "model_path": str(self.model_path),
            "downloaded_runtime": self.downloaded_runtime,
            "downloaded_model": self.downloaded_model,
            "runtime_spec": asdict(self.runtime_spec),
            "model_spec": asdict(self.model_spec),
        }


def ensure_local_slm_provisioned(
    *,
    model_key: str | None = None,
    cache_dir: str | Path | None = None,
    allow_download: bool = False,
    force_rehash: bool = False,
) -> ProvisionedLocalSlm:
    """Verify or download the pinned llama.cpp runtime binary and GGUF model."""
    model_spec = resolve_local_slm_model_spec(model_key)
    root_dir = resolve_local_slm_cache_dir(cache_dir)
    runtime_dir = root_dir / "runtime" / f"llama.cpp-{LLAMA_CPP_RUNTIME_SPEC.release_tag}-win-cpu-x64"
    zip_path = root_dir / "archives" / LLAMA_CPP_RUNTIME_SPEC.asset_name
    model_path = root_dir / "models" / model_spec.model_key / model_spec.filename

    downloaded_runtime = False
    server_exe = _verify_runtime_dir(runtime_dir, LLAMA_CPP_RUNTIME_SPEC)
    if server_exe is None:
        if zip_path.is_file():
            zip_stat = zip_path.stat()
            if zip_stat.st_size == LLAMA_CPP_RUNTIME_SPEC.size_bytes and (
                _compute_sha256(zip_path, force_rehash=force_rehash) == LLAMA_CPP_RUNTIME_SPEC.sha256
            ):
                server_exe = _safe_extract_zip(zip_path, runtime_dir, LLAMA_CPP_RUNTIME_SPEC)
        if server_exe is None:
            if not allow_download:
                raise LocalSlmRuntimeError(
                    "MODEL_RUNTIME_UNAVAILABLE",
                    f"Local SLM runtime {LLAMA_CPP_RUNTIME_SPEC.release_tag} is not provisioned in {runtime_dir}.",
                )
            _download_verified_file(
                url=LLAMA_CPP_RUNTIME_SPEC.url,
                dest_path=zip_path,
                expected_size=LLAMA_CPP_RUNTIME_SPEC.size_bytes,
                expected_sha256=LLAMA_CPP_RUNTIME_SPEC.sha256,
            )
            server_exe = _safe_extract_zip(zip_path, runtime_dir, LLAMA_CPP_RUNTIME_SPEC)
            downloaded_runtime = True

    downloaded_model = False
    if model_path.is_file():
        model_stat = model_path.stat()
        if model_stat.st_size != model_spec.size_bytes:
            if not allow_download:
                raise LocalSlmRuntimeError(
                    "MODEL_CHECKSUM_MISMATCH",
                    f"Model file {model_path} size mismatch ({model_stat.st_size} != {model_spec.size_bytes}).",
                )
            model_path.unlink()
        else:
            actual_sha = _compute_sha256(model_path, force_rehash=force_rehash)
            if actual_sha != model_spec.sha256:
                if not allow_download:
                    raise LocalSlmRuntimeError(
                        "MODEL_CHECKSUM_MISMATCH",
                        f"Model file {model_path} SHA-256 mismatch ({actual_sha} != {model_spec.sha256}).",
                    )
                model_path.unlink()

    if not model_path.is_file():
        if not allow_download or not model_spec.url:
            raise LocalSlmRuntimeError(
                "MODEL_RUNTIME_UNAVAILABLE",
                f"Local SLM model {model_spec.model_key} is not provisioned at {model_path}.",
            )
        _download_verified_file(
            url=model_spec.url,
            dest_path=model_path,
            expected_size=model_spec.size_bytes,
            expected_sha256=model_spec.sha256,
        )
        downloaded_model = True

    return ProvisionedLocalSlm(
        cache_dir=root_dir,
        runtime_dir=runtime_dir,
        server_executable=server_exe,
        model_path=model_path,
        model_spec=model_spec,
        runtime_spec=LLAMA_CPP_RUNTIME_SPEC,
        downloaded_runtime=downloaded_runtime,
        downloaded_model=downloaded_model,
    )


if os.name == "nt":
    class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
            ("PrivateUsage", ctypes.c_size_t),
        ]


    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _KERNEL32.GetCurrentProcess.argtypes = []
    _KERNEL32.GetCurrentProcess.restype = wintypes.HANDLE
    _KERNEL32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _KERNEL32.OpenProcess.restype = wintypes.HANDLE
    _KERNEL32.CloseHandle.argtypes = [wintypes.HANDLE]
    _KERNEL32.CloseHandle.restype = wintypes.BOOL

    _PSAPI = ctypes.WinDLL("psapi", use_last_error=True)
    _PSAPI.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_PROCESS_MEMORY_COUNTERS_EX),
        wintypes.DWORD,
    ]
    _PSAPI.GetProcessMemoryInfo.restype = wintypes.BOOL
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _PROCESS_VM_READ = 0x0010


def get_process_memory_info(pid: int | None = None) -> dict[str, float | int] | None:
    """Measure RSS (WorkingSetSize) and PrivateUsage via Win32 GetProcessMemoryInfo."""
    if os.name != "nt":
        return None
    handle = None
    close_handle = False
    try:
        if pid is None or pid == os.getpid():
            handle = _KERNEL32.GetCurrentProcess()
        else:
            handle = _KERNEL32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION | _PROCESS_VM_READ, False, int(pid))
            if not handle:
                return None
            close_handle = True
        counters = _PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(counters)
        ok = _PSAPI.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if not ok:
            return None
        ws = int(counters.WorkingSetSize)
        peak_ws = int(counters.PeakWorkingSetSize)
        priv = int(counters.PrivateUsage)
        return {
            "pid": int(pid or os.getpid()),
            "working_set_bytes": ws,
            "peak_working_set_bytes": peak_ws,
            "private_bytes": priv,
            "working_set_mib": round(ws / (1024 * 1024), 2),
            "peak_working_set_mib": round(peak_ws / (1024 * 1024), 2),
            "private_mib": round(priv / (1024 * 1024), 2),
        }
    except Exception:
        return None
    finally:
        if close_handle and handle:
            _KERNEL32.CloseHandle(handle)


def _pick_ephemeral_port() -> int:
    """Pick a bindable loopback port, skipping Windows excluded/Hyper-V dynamic ranges (WinError 10013)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    except OSError:
        pass
    base = 31000 + (os.getpid() % 10000)
    for offset in range(16000):
        candidate = 31000 + ((base - 31000 + offset) % 17000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", candidate))
                return int(candidate)
            except OSError:
                continue
    raise LocalSlmRuntimeError("MODEL_RUNTIME_UNAVAILABLE", "No bindable loopback port available on 127.0.0.1.")


def _strip_thinking_prefix(text: str) -> tuple[str, bool]:
    if "<think>" not in text:
        return text, False
    cleaned = _THINK_BLOCK_RE.sub("", text).strip()
    if "<think>" in cleaned and "</think>" not in cleaned:
        cleaned = ""
    return cleaned, True


@dataclass(frozen=True)
class LocalSlmInferenceResult:
    raw_content: str
    parsed_json: dict[str, Any]
    model_key: str
    model_sha256: str
    runtime_version: str
    server_load_time_ms: float
    inference_time_ms: float
    prompt_tokens: int | None
    completion_tokens: int | None
    thinking_stripped: bool
    server_restarted: bool
    python_rss_mib: float | None
    server_rss_mib: float | None
    combined_rss_mib: float | None
    server_peak_rss_mib: float | None
    threads: int
    ctx_size: int
    queue_wait_ms: float = 0.0
    prompt_eval_ms: float | None = None
    token_gen_ms: float | None = None
    tokens_per_sec: float | None = None
    cached_prompt_tokens: int | None = None
    json_decode_ms: float = 0.0
    cache_prompt_enabled: bool = True


class LocalSlmRuntime:
    """Lazy single-instance local llama-server runtime manager."""

    def __init__(
        self,
        *,
        cache_dir: str | Path | None = None,
        allow_download: bool | None = None,
        ctx_size: int = DEFAULT_LOCAL_SLM_CTX_SIZE,
        max_tokens: int = DEFAULT_LOCAL_SLM_MAX_TOKENS,
        threads: int | None = None,
        request_timeout_s: float = DEFAULT_LOCAL_SLM_REQUEST_TIMEOUT_S,
        startup_timeout_s: float = DEFAULT_LOCAL_SLM_STARTUP_TIMEOUT_S,
        max_queue: int = DEFAULT_LOCAL_SLM_MAX_QUEUE,
    ) -> None:
        self.cache_dir = resolve_local_slm_cache_dir(cache_dir)
        if allow_download is None:
            allow_download = os.getenv("LOCAL_SLM_AUTO_DOWNLOAD") == "1"
        self.allow_download = bool(allow_download)
        self.ctx_size = int(ctx_size)
        self.max_tokens = int(max_tokens)
        self.threads = resolve_default_threads(threads)
        self.request_timeout_s = float(request_timeout_s)
        self.startup_timeout_s = float(startup_timeout_s)
        self.max_queue = max(1, int(max_queue))

        self._queue_lock = threading.Lock()
        self._pending_count = 0
        self._infer_semaphore = threading.Semaphore(1)
        self._proc_lock = threading.Lock()
        self._proc: subprocess.Popen[bytes] | None = None
        self._http_conn: http.client.HTTPConnection | None = None
        self._http_port: int | None = None
        self._log_file: Any = None
        self._port: int | None = None
        self._active_model_key: str | None = None
        self._active_ctx_size: int | None = None
        self._active_threads: int | None = None
        self._provisioned: ProvisionedLocalSlm | None = None
        self._last_load_ms: float = 0.0
        self._crash_recovery_count: int = 0
        self._timeout_recovery_count: int = 0

    def status(self) -> dict[str, Any]:
        with self._proc_lock:
            alive = self._proc is not None and self._proc.poll() is None
            pid = self._proc.pid if alive and self._proc is not None else None
            server_mem = get_process_memory_info(pid) if pid else None
            py_mem = get_process_memory_info(None)
            return {
                "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
                "cache_dir": str(self.cache_dir),
                "server_alive": alive,
                "server_pid": pid,
                "port": self._port if alive else None,
                "active_model_key": self._active_model_key if alive else None,
                "active_ctx_size": self._active_ctx_size if alive else None,
                "active_threads": self._active_threads if alive else None,
                "last_load_ms": self._last_load_ms,
                "crash_recovery_count": self._crash_recovery_count,
                "timeout_recovery_count": self._timeout_recovery_count,
                "python_memory": py_mem,
                "server_memory": server_mem,
            }

    def _close_log_file_locked(self) -> None:
        if self._log_file is not None:
            try:
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None

    def _close_http_conn(self) -> None:
        conn = self._http_conn
        self._http_conn = None
        self._http_port = None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    def _stop_server_locked(self) -> None:
        self._close_http_conn()
        proc = self._proc
        self._proc = None
        self._port = None
        self._active_model_key = None
        self._active_ctx_size = None
        self._active_threads = None
        if proc is not None:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3.0)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=2.0)
            except Exception:
                pass
        self._close_log_file_locked()

    def shutdown(self) -> None:
        with self._proc_lock:
            self._stop_server_locked()

    def force_kill_server(self) -> int | None:
        """Kill active llama-server.exe immediately (for fault-recovery testing)."""
        with self._proc_lock:
            self._close_http_conn()
            proc = self._proc
            if proc is None:
                return None
            pid = proc.pid
            try:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=3.0)
            finally:
                self._proc = None
                self._port = None
                self._close_log_file_locked()
            return pid

    def _ensure_server_running_locked(
        self,
        *,
        model_key: str | None,
        ctx_size: int,
        threads: int,
        allow_download: bool,
    ) -> tuple[ProvisionedLocalSlm, int, float, bool]:
        spec = resolve_local_slm_model_spec(model_key)
        provisioned = ensure_local_slm_provisioned(
            model_key=spec.model_key,
            cache_dir=self.cache_dir,
            allow_download=allow_download,
        )
        restarted = False
        if self._proc is not None and self._proc.poll() is not None:
            self._crash_recovery_count += 1
            self._stop_server_locked()
            restarted = True

        if (
            self._proc is not None
            and self._proc.poll() is None
            and self._port is not None
            and self._active_model_key == spec.model_key
            and self._active_ctx_size == ctx_size
            and self._active_threads == threads
        ):
            self._provisioned = provisioned
            return provisioned, self._port, 0.0, restarted

        if self._proc is not None:
            self._stop_server_locked()
            restarted = True

        port = _pick_ephemeral_port()
        log_dir = self.cache_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"llama-server-{spec.model_key}.log"
        log_fh = log_path.open("wb")
        cmd = [
            str(provisioned.server_executable),
            "-m",
            str(provisioned.model_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "-c",
            str(ctx_size),
            "-t",
            str(threads),
            "-b",
            "512",
            "-ub",
            "512",
            "-np",
            "1",
            "--jinja",
            "--no-webui",
        ]
        if spec.supports_thinking:
            cmd.extend(["--reasoning", "off"])

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        started = time.perf_counter()
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(provisioned.server_executable.parent),
                stdin=subprocess.DEVNULL,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )
        except Exception as exc:
            log_fh.close()
            raise LocalSlmRuntimeError(
                "MODEL_RUNTIME_UNAVAILABLE",
                f"Failed to spawn llama-server.exe: {exc}",
            ) from exc

        self._proc = proc
        self._log_file = log_fh
        self._port = port
        self._active_model_key = spec.model_key
        self._active_ctx_size = ctx_size
        self._active_threads = threads
        self._provisioned = provisioned

        deadline = started + self.startup_timeout_s
        last_err = ""
        while time.perf_counter() < deadline:
            if proc.poll() is not None:
                rc = proc.returncode
                self._stop_server_locked()
                tail = ""
                try:
                    tail = log_path.read_text(encoding="utf-8", errors="replace")[-600:]
                except Exception:
                    pass
                raise LocalSlmRuntimeError(
                    "LOCAL_SLM_PROCESS_CRASHED",
                    f"llama-server exited during startup (code {rc}): {tail.strip()}",
                )
            conn: http.client.HTTPConnection | None = None
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
                conn.request("GET", "/health")
                resp = conn.getresponse()
                resp.read()
                if resp.status == 200:
                    load_ms = round((time.perf_counter() - started) * 1000.0, 2)
                    self._last_load_ms = load_ms
                    return provisioned, port, load_ms, True
                last_err = f"HTTP {resp.status}"
            except Exception as exc:
                last_err = str(exc)
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass
            time.sleep(0.1)

        self._stop_server_locked()
        raise LocalSlmRuntimeError(
            "LOCAL_SLM_TIMEOUT",
            f"llama-server failed health check within {self.startup_timeout_s}s ({last_err}).",
            status_code=504,
        )

    def chat_completion_json(
        self,
        *,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
        schema_name: str = "slm_response",
        grammar: str | None = None,
        cache_prompt: bool = True,
        model_key: str | None = None,
        ctx_size: int | None = None,
        max_tokens: int | None = None,
        threads: int | None = None,
        timeout_s: float | None = None,
        temperature: float = 0.0,
        seed: int = 42,
        repeat_penalty: float | None = None,
        allow_download: bool | None = None,
    ) -> LocalSlmInferenceResult:
        eff_ctx = int(ctx_size or self.ctx_size)
        eff_max_tokens = int(max_tokens or self.max_tokens)
        eff_threads = int(threads or self.threads)
        eff_timeout = float(timeout_s or self.request_timeout_s)
        eff_allow_dl = self.allow_download if allow_download is None else bool(allow_download)

        with self._queue_lock:
            if self._pending_count >= self.max_queue:
                raise LocalSlmRuntimeError(
                    "LOCAL_SLM_BUSY",
                    f"Local SLM queue limit reached (max_queue={self.max_queue}).",
                    status_code=503,
                )
            self._pending_count += 1

        wait_t0 = time.perf_counter()
        try:
            with self._infer_semaphore:
                queue_wait_ms = round((time.perf_counter() - wait_t0) * 1000.0, 3)
                return self._run_single_inference(
                    messages=messages,
                    json_schema=json_schema,
                    schema_name=schema_name,
                    grammar=grammar,
                    cache_prompt=bool(cache_prompt),
                    model_key=model_key,
                    ctx_size=eff_ctx,
                    max_tokens=eff_max_tokens,
                    threads=eff_threads,
                    timeout_s=eff_timeout,
                    temperature=temperature,
                    seed=seed,
                    repeat_penalty=repeat_penalty,
                    allow_download=eff_allow_dl,
                    queue_wait_ms=queue_wait_ms,
                )
        finally:
            with self._queue_lock:
                self._pending_count = max(0, self._pending_count - 1)

    def _post_completion_keepalive(self, port: int, raw_payload: bytes, timeout_s: float) -> tuple[int, bytes]:
        """POST to llama-server reusing a keep-alive loopback socket; reconnect once on stale socket."""
        headers = {"Content-Type": "application/json", "Connection": "keep-alive"}
        for attempt in range(2):
            conn = self._http_conn if (self._http_conn is not None and self._http_port == port) else None
            reused = conn is not None
            if conn is None:
                self._close_http_conn()
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout_s)
                self._http_conn = conn
                self._http_port = port
            else:
                conn.timeout = timeout_s
                if conn.sock is not None:
                    conn.sock.settimeout(timeout_s)
            try:
                conn.request("POST", "/v1/chat/completions", body=raw_payload, headers=headers)
                resp = conn.getresponse()
                resp_status = int(resp.status)
                resp_bytes = resp.read()
                if resp.will_close:
                    self._close_http_conn()
                return resp_status, resp_bytes
            except (TimeoutError, socket.timeout):
                self._close_http_conn()
                raise
            except (http.client.HTTPException, OSError) as exc:
                self._close_http_conn()
                # If the server process actually exited, fail immediately. A REUSED socket the idle server already closed
                # (Windows: 10053 aborted / 10054 reset / broken pipe / remote disconnect) is stale, not a crash; the
                # transient 10013 also gets one retry. Live acceptance: idle > server keep-alive (~5 s) hit 10053 every time.
                proc_dead = self._proc is not None and self._proc.poll() is not None
                if attempt == 0 and not proc_dead and (reused or "10013" in str(exc)):
                    time.sleep(0.05)
                    continue
                raise

    def _run_single_inference(
        self,
        *,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None,
        schema_name: str,
        grammar: str | None,
        cache_prompt: bool,
        model_key: str | None,
        ctx_size: int,
        max_tokens: int,
        threads: int,
        timeout_s: float,
        temperature: float,
        seed: int,
        repeat_penalty: float | None = None,
        allow_download: bool = False,
        queue_wait_ms: float = 0.0,
    ) -> LocalSlmInferenceResult:
        with self._proc_lock:
            provisioned, port, load_ms, restarted = self._ensure_server_running_locked(
                model_key=model_key,
                ctx_size=ctx_size,
                threads=threads,
                allow_download=allow_download,
            )
            server_pid = self._proc.pid if self._proc is not None else None

        payload: dict[str, Any] = {
            "model": provisioned.model_spec.model_key,
            "messages": messages,
            "temperature": float(temperature),
            "top_p": 1.0,
            "seed": int(seed),
            "max_tokens": int(max_tokens),
            "cache_prompt": bool(cache_prompt),
            "stream": False,
        }
        if repeat_penalty is not None:
            payload["repeat_penalty"] = float(repeat_penalty)
        if provisioned.model_spec.supports_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        if grammar is not None:
            payload["grammar"] = grammar
        elif json_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": json_schema,
                },
            }
        else:
            payload["response_format"] = {"type": "json_object"}

        raw_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        infer_start = time.perf_counter()
        try:
            resp_status, resp_bytes = self._post_completion_keepalive(port, raw_payload, timeout_s)
        except (TimeoutError, socket.timeout) as exc:
            with self._proc_lock:
                self._timeout_recovery_count += 1
                self._stop_server_locked()
            raise LocalSlmRuntimeError(
                "LOCAL_SLM_TIMEOUT",
                f"Local SLM request timed out after {timeout_s:.1f}s: {exc}",
                status_code=504,
            ) from exc
        except (http.client.HTTPException, OSError) as exc:
            with self._proc_lock:
                if self._proc is not None and self._proc.poll() is not None:
                    self._crash_recovery_count += 1
                self._stop_server_locked()
            raise LocalSlmRuntimeError(
                "LOCAL_SLM_PROCESS_CRASHED",
                f"Local SLM loopback HTTP communication failed: {exc}",
                status_code=503,
            ) from exc

        infer_ms = round((time.perf_counter() - infer_start) * 1000.0, 2)
        resp_text = resp_bytes.decode("utf-8", errors="replace")
        if resp_status >= 400:
            raise LocalSlmRuntimeError(
                "LOCAL_SLM_RESPONSE_INVALID",
                f"llama-server returned HTTP {resp_status}: {resp_text[:300]}",
                status_code=502,
            )

        dec_t0 = time.perf_counter()
        try:
            body = json.loads(resp_text)
            choices = body.get("choices") or []
            message = (choices[0] or {}).get("message") or {}
            raw_content = str(message.get("content") or "").strip()
        except Exception as exc:
            raise LocalSlmRuntimeError(
                "LOCAL_SLM_RESPONSE_INVALID",
                f"Malformed JSON envelope from llama-server: {exc}",
                status_code=502,
            ) from exc

        cleaned, thinking_stripped = _strip_thinking_prefix(raw_content)
        if not cleaned:
            raise LocalSlmRuntimeError(
                "LOCAL_SLM_RESPONSE_INVALID",
                "Local SLM returned empty JSON content (or truncated thinking block).",
                status_code=502,
            )
        try:
            parsed_json = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LocalSlmRuntimeError(
                "LOCAL_SLM_RESPONSE_INVALID",
                f"Local SLM content is not valid JSON: {exc}; content={cleaned[:200]}",
                status_code=502,
            ) from exc
        json_decode_ms = round((time.perf_counter() - dec_t0) * 1000.0, 3)
        if not isinstance(parsed_json, dict):
            raise LocalSlmRuntimeError(
                "LOCAL_SLM_RESPONSE_INVALID",
                "Local SLM JSON root must be an object.",
                status_code=502,
            )

        usage = body.get("usage") or {}
        timings = body.get("timings") or {}
        py_mem = get_process_memory_info(None)
        srv_mem = get_process_memory_info(server_pid)
        py_rss = py_mem["working_set_mib"] if py_mem else None
        srv_rss = srv_mem["working_set_mib"] if srv_mem else None
        srv_peak = srv_mem["peak_working_set_mib"] if srv_mem else None
        combined = (
            round(float(py_rss) + float(srv_rss), 2)
            if py_rss is not None and srv_rss is not None
            else None
        )

        return LocalSlmInferenceResult(
            raw_content=cleaned,
            parsed_json=parsed_json,
            model_key=provisioned.model_spec.model_key,
            model_sha256=provisioned.model_spec.sha256,
            runtime_version=LOCAL_SLM_RUNTIME_VERSION,
            server_load_time_ms=load_ms,
            inference_time_ms=infer_ms,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            thinking_stripped=thinking_stripped,
            server_restarted=restarted,
            python_rss_mib=py_rss,
            server_rss_mib=srv_rss,
            combined_rss_mib=combined,
            server_peak_rss_mib=srv_peak,
            threads=threads,
            ctx_size=ctx_size,
            queue_wait_ms=queue_wait_ms,
            prompt_eval_ms=round(float(timings["prompt_ms"]), 3) if timings.get("prompt_ms") is not None else None,
            token_gen_ms=round(float(timings["predicted_ms"]), 3) if timings.get("predicted_ms") is not None else None,
            tokens_per_sec=round(float(timings["predicted_per_second"]), 2) if timings.get("predicted_per_second") is not None else None,
            cached_prompt_tokens=int(timings["cache_n"]) if timings.get("cache_n") is not None else None,
            json_decode_ms=json_decode_ms,
            cache_prompt_enabled=bool(cache_prompt),
        )


def build_local_slm_cache_identity(
    *,
    exact_input_text: str,
    model_key: str,
    model_sha256: str,
    runtime_version: str = LOCAL_SLM_RUNTIME_VERSION,
    strategy: str,
    schema_version: str,
    schema_sha256: str,
    grounding_policy_version: str,
    parser_version: str,
    capability_identity: dict[str, Any] | str,
    namespace: str = LOCAL_SLM_CACHE_NAMESPACE,
) -> tuple[str, dict[str, Any]]:
    """Compute a deterministic cache identity binding all 9 required SLM/grounding fields."""
    input_sha256 = hashlib.sha256(exact_input_text.encode("utf-8")).hexdigest()
    metadata: dict[str, Any] = {
        "namespace": str(namespace),
        "exact_input_sha256": input_sha256,
        "model_key": str(model_key),
        "model_sha256": str(model_sha256),
        "runtime_version": str(runtime_version),
        "strategy": str(strategy),
        "schema_version": str(schema_version),
        "schema_sha256": str(schema_sha256),
        "grounding_policy_version": str(grounding_policy_version),
        "parser_version": str(parser_version),
        "capability_identity": capability_identity,
    }
    digest = hashlib.sha256(json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return digest, metadata


class LocalSlmExtractionCache:
    """Thread-safe bounded LRU cache for verified local SLM extraction results."""

    def __init__(self, max_entries: int = 256) -> None:
        self.max_entries = max(1, int(max_entries))
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, Any] = OrderedDict()

    def get(self, cache_key: str) -> Any | None:
        with self._lock:
            val = self._entries.get(cache_key)
            if val is not None:
                self._entries.move_to_end(cache_key)
            return val

    def put(self, cache_key: str, value: Any) -> None:
        with self._lock:
            self._entries[cache_key] = value
            self._entries.move_to_end(cache_key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


_GLOBAL_RUNTIMES_LOCK = threading.Lock()
_GLOBAL_RUNTIME: LocalSlmRuntime | None = None
_GLOBAL_EXTRACTION_CACHE = LocalSlmExtractionCache(max_entries=256)


def get_shared_local_slm_runtime() -> LocalSlmRuntime:
    global _GLOBAL_RUNTIME
    with _GLOBAL_RUNTIMES_LOCK:
        if _GLOBAL_RUNTIME is None:
            _GLOBAL_RUNTIME = LocalSlmRuntime()
        return _GLOBAL_RUNTIME


def get_shared_local_slm_extraction_cache() -> LocalSlmExtractionCache:
    return _GLOBAL_EXTRACTION_CACHE


def shutdown_global_local_slm_runtimes() -> None:
    global _GLOBAL_RUNTIME
    with _GLOBAL_RUNTIMES_LOCK:
        runtime = _GLOBAL_RUNTIME
        _GLOBAL_RUNTIME = None
    if runtime is not None:
        runtime.shutdown()


atexit.register(shutdown_global_local_slm_runtimes)


__all__ = [
    "ACTIVE_MODEL_STATE_FILENAME",
    "COMPARATOR_LOCAL_SLM_MODEL_KEY",
    "DEFAULT_LOCAL_SLM_CTX_SIZE",
    "DEFAULT_LOCAL_SLM_MAX_QUEUE",
    "DEFAULT_LOCAL_SLM_MAX_TOKENS",
    "DEFAULT_LOCAL_SLM_MODEL_KEY",
    "DEFAULT_LOCAL_SLM_REQUEST_TIMEOUT_S",
    "DEFAULT_LOCAL_SLM_STARTUP_TIMEOUT_S",
    "DEFAULT_LOCAL_SLM_THREADS",
    "FINETUNED_LOCAL_SLM_MODEL_KEY",
    "LLAMA_CPP_RUNTIME_SPEC",
    "LOCAL_SLM_CACHE_NAMESPACE",
    "LOCAL_SLM_CACHE_V9_NAMESPACE",
    "LOCAL_SLM_MODELS",
    "LOCAL_SLM_RUNTIME_VERSION",
    "LOCAL_SLM_RUNTIME_V9_VERSION",
    "LlamaCppRuntimeSpec",
    "LocalSlmExtractionCache",
    "LocalSlmInferenceResult",
    "LocalSlmModelSpec",
    "LocalSlmRuntime",
    "LocalSlmRuntimeError",
    "ProvisionedLocalSlm",
    "V9_LOCAL_SLM_MODEL_KEY",
    "build_local_slm_cache_identity",
    "ensure_local_slm_provisioned",
    "get_process_memory_info",
    "get_shared_local_slm_extraction_cache",
    "get_shared_local_slm_runtime",
    "read_active_local_slm_model_key",
    "resolve_default_threads",
    "resolve_local_slm_cache_dir",
    "resolve_local_slm_model_spec",
    "shutdown_global_local_slm_runtimes",
    "write_active_local_slm_model_key",
]
