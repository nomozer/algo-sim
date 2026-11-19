# AXO HYBRID /9 — Local Model Provisioning & Rollback Report

> **Tooling:** [`provision_local_slm.py`](../../../../../backend/scripts/provision_local_slm.py) + [`local_slm_runtime.py`](../../../../../backend/app/ai/local_slm_runtime.py)  
> **Cache Root:** `C:\Users\Bunny\AppData\Local\axo-slm` (`external_ai_calls = 0`)

---

## 1. Registered Local Model Catalog & Preserved Checksums

| Model Key | Alias(es) | Artifact Filename | Size (Bytes) | Verified SHA-256 | Role |
| --- | --- | --- | --- | --- | --- |
| `qwen3-0.6b-q4_k_m` | `default`, `primary` | `Qwen3-0.6B-Q4_K_M.gguf` | `396704736` | `ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a` | Frozen `/6` base Q4_K_M (unchanged) |
| `qwen3-0.6b-axo-v7-q4_k_m` | `finetuned`, `v7`, `axo-v7` | `Qwen3-0.6B-AxoV7-Q4_K_M.gguf` | `396704736` | `36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148` | Frozen `/7` LoRA Q4_K_M (unchanged, rollback target) |
| **`qwen3-0.6b-axo-v9-q4_k_m`** | `v9`, `axo-v9`, `v9-default` | `Qwen3-0.6B-AxoV9-Q4_K_M.gguf` | `396704736` | **`73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35`** | **Promoted `/9` Q4_K_M model** |

Runtime server executable verified: `C:\Users\Bunny\AppData\Local\axo-slm\runtime\llama.cpp-b12470-win-cpu-x64\llama-server.exe` (`-b 512 -ub 512 --reasoning off`).

---

## 2. Atomic Activation & Rollback Mechanism (`active_model.json`)

- **`read_active_local_slm_model_key` / `write_active_local_slm_model_key`:** Writes `C:\Users\Bunny\AppData\Local\axo-slm\active_model.json` atomically via temp file + `os.replace(...)` after verifying file existence and strict SHA-256 match (`force_rehash=True`, `allow_download=False`).
- Local-only `/9` routing (`prepare_local_slm_v9_hybrid` / `local_slm_ready_status`) resolves `os.getenv("LOCAL_SLM_MODEL") or "v9-active"`, allowing operators to roll back instantly without modifying application code or restarting a build, while `/5`–`/7` callers continue resolving `FINETUNED_LOCAL_SLM_MODEL_KEY` (`AxoV7`) or `DEFAULT_LOCAL_SLM_MODEL_KEY`.

---

## 3. Verified CLI Operations

All commands executed against the local cache (`allow_download=False`, exit code `0`):

1. `provision_local_slm.py --status --json` -> `"ok": true`, all 3 models `provisioned: true`, `active_model_key: "qwen3-0.6b-axo-v9-q4_k_m"`.
2. `provision_local_slm.py --verify --json` -> `"ok": true`, full SHA-256 rehash matched across `qwen3-0.6b-q4_k_m`, `qwen3-0.6b-axo-v7-q4_k_m`, and `qwen3-0.6b-axo-v9-q4_k_m`.
3. `provision_local_slm.py --rollback v7 --json` -> `"ok": true, "action": "rollback", "active_model_key": "qwen3-0.6b-axo-v7-q4_k_m"`, wrote `active_model.json`.
4. `provision_local_slm.py --activate v9 --json` -> `"ok": true, "action": "activate", "active_model_key": "qwen3-0.6b-axo-v9-q4_k_m"`, restored `AxoV9` active in `active_model.json`.
