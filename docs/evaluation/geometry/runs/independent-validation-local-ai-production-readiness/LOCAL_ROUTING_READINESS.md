# AXO HYBRID /8 — Scoped Local Routing Readiness (`LOCAL_ROUTING_READINESS.md`)

> **Policy Simulator Version:** `scoped-local-routing-sim/1` ([`simulate_scoped_local_routing.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/simulate_scoped_local_routing.py))  
> **Unit & Policy Verification:** [`test_scoped_local_routing_policy.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_scoped_local_routing_policy.py) — **`4 passed in 1.87s`**  
> **Production Default Preserved:** `HYBRID_ROUTE_MODE = "live"` (Gemini 2.5 Flash untouched; `RoutePolicy` unchanged under `backend/app/ai/route_policy.py`)  
> **Silent Cloud Fallback:** **Forbidden (`cloud_fallback_allowed = False`)** · **Machine Artifact:** [`SCOPED_LOCAL_ROUTING_SIMULATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/SCOPED_LOCAL_ROUTING_SIMULATION.json)

---

## 1. Six Mandatory Fail-Closed Routing Rules Evaluated (`/8 §15`, `VERIFIED`)

The standalone scoped router enforces six deterministic pre- and post-extraction gates without mutating `backend/app/**`:

1. **Deterministic Fast Path Bypasses SLM (`DETERMINISTIC_FAST_PATH`):** When `parse_geometry_problem_locally(txt)` returns `LOCAL_PARSE_COMPLETE`, execution bypasses the SLM cleanly (`slm_allowed = False`, median `51.50 ms`), reserving `llama-server` CPU for non-parser inputs.
2. **Parser Ambiguity Stays Fail-Closed (`CLARIFICATION_OR_REFUSAL` / `SAFE_REFUSAL`):** Prompt injections (`PROMPT_INJECTION_REJECTED`), UI viewer commands (`Quay hình...`, `Ẩn tên...`), context-dependent ellipses (`đoạn vừa dựng`, `điểm đó`), empty strings, and `LOCAL_PARSE_AMBIGUOUS` inputs never enter SLM guessing.
3. **Runtime Availability & Cryptographic Integrity (`INFRASTRUCTURE_FAILURE`):** Before SLM invocation, `verify_model_integrity` verifies `llama-server` health, file existence, and SHA-256 checksum (`qwen3-0.6b-axo-v7-q4_k_m = 36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148`, `OK`; rollback `qwen3-0.6b-q4_k_m = ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a`, `OK`). Missing binary or SHA-256 mismatch fails closed with `MODEL_FILE_MISSING` / `MODEL_CHECKSUM_MISMATCH` and **`cloud_fallback_allowed = False`**.
4. **Explicit Capability-Matrix Scoping (`UNSUPPORTED` / `OUT_OF_SCOPED_PRIMARY_ENVELOPE`):** Curved solids (`mặt cầu`, `hình nón`, `hình trụ`), dynamic extrema (`di động`, `giá trị lớn/nhỏ nhất`), derived sections/intersections (`thiết diện`, `giao tuyến`), unrecognized solid families, `EXPERIMENTAL` reordered rectangular premises without `"đáy"` (`Biết <base> là hình chữ nhật`), and `NOT_MEASURED` plane-plane angle goals are explicitly excluded from the primary local envelope (`0` silent promotion).
5. **Post-Extraction Zero-Trust Serving (`evaluate_post_extraction_serving`):** Only results achieving `status == "SERVED"` after passing `slm-grounding-validator/3` (`GROUNDED_AND_LOWERED` or deterministic `None`), `Source Gate`, `Planner /26`, and `Exact Kernel /24` may serve (`SERVED_VERIFIED`); any unresolved/rejected extraction returns `DO_NOT_SERVE`.
6. **Zero Silent Cloud Escalation & Instant Model Rollback:** Switching between `qwen3-0.6b-axo-v7-q4_k_m` and rollback `qwen3-0.6b-q4_k_m` works cleanly via verified config/env (`AXO_LOCAL_SLM_MODEL`), and no `local-slm` failure ever escalates silently to Gemini.

---

## 2. Offline Simulation Outcomes on `/7` & `/8` Corpora (`VERIFIED`)

| Split | Total | Fast Path | Eligible Local Primary | Gated Out (`UNSUPPORTED` / `OUT_OF_SCOPE` / `CLARIFY` / `SAFE_REFUSAL`) | `SERVED_VERIFIED` | `DO_NOT_SERVE` | Wrong-Served Inside Envelope (`axo-math-evaluator/2`) | Raw Frozen `/7` EVI Artifact |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`SLM_V7_HOLDOUT_112`** | `112` | `43` | `57` | `12` (`5` OOS-Exp + `6` Unsup + `1` Inj) | **`74`** | `26` | **`0`** | `5` (`v7h_p7_06..10` `cos²=`) |
| **`PERMISSIBLE_UNSEEN_77`** (`C60 + Ext17`) | `77` | `31` | `28` | `18` (`8` Clarify + `9` Unsup + `1` OOS-Exp) | **`25`** | `34` | **`0`** | `0` |

### Key Finding
- **Within the strictly scoped local envelope, wrong-served = `0` across all `189` evaluated cases.**
- **Coverage tradeoff remains clear:** Out of `59` fast-path + eligible items in `PERMISSIBLE_UNSEEN_77`, `34` still stop at `DO_NOT_SERVE` (predominantly `C60_BLIND_NLU` conversational paraphrases caught by `Source Gate` / `Exact Kernel`), demonstrating why local SLM remains **opt-in `local-slm`** rather than default replacement.
