# SLM_RUNTIME_IMPLEMENTATION.md — Local CPU Inference Runtime & Lifecycle (AXO HYBRID /5)

**Module:** [`backend/app/ai/local_slm_runtime.py`](../../../../../backend/app/ai/local_slm_runtime.py) (`LOCAL_SLM_RUNTIME_VERSION = "local-slm-runtime/1"`)  
**Provisioning CLI:** [`backend/scripts/provision_local_slm.py`](../../../../../backend/scripts/provision_local_slm.py)

---

## 1. Runtime Selection Rationale & Binary Pinning

On Windows 11 x64 (`Python 3.12.10`) without a local MSVC/CMake/Ninja C++ toolchain, PyPI lacked `cp312-win_amd64` CPU wheels supporting Qwen3 GGUF metadata, and requiring an external user daemon (`Ollama` or `LM Studio`) breaks self-contained product packaging. Therefore, Axo Hybrid `/5` provisions and manages the official MIT-licensed **`ggml-org/llama.cpp` release `b12470`** binary (`llama-server.exe`) internally as a single-instance background loopback subprocess:

| Artifact | Origin / Revision | Size (Bytes) | SHA-256 Digest | License |
|---|---|---|---|---|
| `llama-b12470-bin-win-cpu-x64.zip` | `ggml-org/llama.cpp` tag `b12470` | `25,272,394` | `fc83371644b501647c253ca1e42277795eca7ed15851a218b20294275b45d67f` | `MIT` |
| `Qwen3-0.6B-Q4_K_M.gguf` *(Primary)* | `unsloth/Qwen3-0.6B-GGUF` (`50968a4468ef4233ed78cd7c3de230dd1d61a56b`) | `396,705,472` | `ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a` | `Apache-2.0` |
| `qwen2.5-0.5b-instruct-q4_k_m.gguf` *(Comparator)* | `Qwen/Qwen2.5-0.5B-Instruct-GGUF` (`9217f5db79a29953eb74d5343926648285ec7e67`) | `491,400,032` | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` | `Apache-2.0` |

Artifacts reside outside the Git tree under `%LOCALAPPDATA%\axo-slm` (overridable via `LOCAL_SLM_CACHE_DIR`). Downloads use atomic `.part.<pid>` staging + streaming SHA-256 & byte-length checks + safe zip extraction against path traversal (`_safe_extract_zip`). When `allow_download=False` (online API default), missing artifacts fail closed with `503 MODEL_RUNTIME_UNAVAILABLE`, and corrupted digests fail closed with `503 MODEL_CHECKSUM_MISMATCH`.

---

## 2. Engineering Discoveries & Fixes During Runtime Verification

1. **Qwen3 `<think>` vs JSON-Schema Grammar Conflict in `llama.cpp b12470`:**  
   Passing `--reasoning-budget 0 --reasoning-format none` caused `llama-server.exe` to fail sampler initialization with HTTP `400`: `Unexpected empty grammar stack after accepting piece: <think> (151667)` because Unsloth's Qwen3 chat template emitted `<think>\n\n</think>\n\n` ahead of assistant JSON. Inspecting `llama-server.exe --help` showed `-rea, --reasoning [on|off|auto]`; switching Qwen3 server flags to `--reasoning off` cleanly aligns the grammar sampler with `response_format={"type": "json_schema", "strict": true}` while also prepending `/no_think` and `chat_template_kwargs={"enable_thinking": false}` plus defensive `_strip_thinking_prefix`.
2. **Offline `pytest` Socket Guard vs Loopback IPC:**  
   `backend/conftest.py` blocks all `httpx.HTTPTransport` calls during offline tests while `backend/tests/offline_child/offline_socket_guard.py` explicitly permits `127.0.0.1` loopback connections. Using stdlib `http.client.HTTPConnection("127.0.0.1", port, ...)` inside `LocalSlmRuntime` respects both layers without altering any test security boundary (keeping `httpx` exclusively for explicit `allow_download=True` provisioning, which stays blocked in offline tests).
3. **Windows Excluded Dynamic Port Range (`WinError 10013`):**  
   Repeated ephemeral `bind(("127.0.0.1", 0))` calls can hit Hyper-V / WSL reserved ranges (`PermissionError: [WinError 10013]`). `_pick_ephemeral_port()` now falls back cleanly across `[31000..47999]`.
4. **64-Bit Win32 Process RSS Measurement:**  
   `get_process_memory_info()` explicitly configures `HANDLE` `argtypes`/`restype` on `kernel32.GetCurrentProcess`, `OpenProcess`, `CloseHandle`, and `psapi.GetProcessMemoryInfo` (`WorkingSetSize`, `PeakWorkingSetSize`, `PrivateUsage`), preventing 32-bit handle truncation on 64-bit Windows.

---

## 3. Measured Resource Footprint, Thread Scaling & Fault Recovery

Measured offline on host hardware (`Windows 11 10.0.26100 AMD64`, `Intel Core i5-11400H` 6 cores / 12 threads, `15.78 GiB` host RAM — see [`SLM_RESOURCE_BENCHMARK.json`](SLM_RESOURCE_BENCHMARK.json)):

| Model / Threads | Server Load (ms) | Cold Infer (ms) | Warm p50 (ms) | Warm p95 (ms) | Warm Mean (ms) | Throughput (tok/s) | Peak Server RSS (MiB) | Peak Combined RSS (MiB) | Warm Truncation Failures |
|---|---|---|---|---|---|---|---|---|---|
| `qwen3-0.6b-q4_k_m` (`threads=4`) | `870.33` | `9559.61` | `8065.27` | `8480.07` | `8351.61` | `32.18` | `923.42` | `1039.62` | `0 / 5` |
| `qwen3-0.6b-q4_k_m` (`threads=6`) | `834.98` | `8913.13` | `6683.53` | `8025.00` | `7161.13` | `38.08` | `924.43` | `1040.57` | `0 / 5` |
| `qwen2.5-0.5b-instruct-q4_k_m` (`threads=4`) | `731.51` | `7926.47` | `5440.94` | `5730.06` | `5286.24` | `44.06` | `558.77` | `674.81` | `1 / 5` *(cal_p05 JSON cut at 512 tokens -> `LOCAL_SLM_RESPONSE_INVALID`)* |

- **4–6 GiB RAM Viability:** Combined Python + `llama-server.exe` peak RSS is `1040.57 MiB` (~`1.02 GiB`) for `Qwen3-0.6B` and `674.81 MiB` (~`0.66 GiB`) for `Qwen2.5-0.5B`, both well under the `2048 MiB` preregistered budget (`-np 1`, `ctx_size = 2048`, `max_tokens = 512`). Because this host has `15.78 GiB` physical RAM, **`PHYSICAL_LOW_END = NOT_MEASURED`** on a real physical 4 GiB / 6 GiB laptop.

### Fault-Injection & Recovery Verification (`5/5 PASS`)
- `missing_model_fail_closed`: empty cache + `allow_download=False` -> `503 MODEL_RUNTIME_UNAVAILABLE` (`PASS`).
- `crash_auto_recovery`: `force_kill_server()` killed `llama-server.exe` PID `5700`; next inference transparently respawned (`751.66 ms` load) and succeeded (`PASS`).
- `timeout_kill_and_recovery`: `timeout_s=0.05` triggered `504 LOCAL_SLM_TIMEOUT`, terminated server slot cleanly, and recovered cleanly on the following call (`PASS`).
- `bounded_queue_busy`: `max_queue=1` serialized concurrent requests with `Semaphore(1)` and rejected excess load with `503 LOCAL_SLM_BUSY` (`PASS`).
- `prompt_injection_rejected`: adversarial jailbreak blocked pre-inference (`PROMPT_INJECTION_REJECTED`, `PASS`).
