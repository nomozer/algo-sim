# Approval Request — Semantic Extraction v3 Runtime Revision (`GO_LIVE_PILOT_REQUIRED`)

Status: **`GO_LIVE_PILOT_REQUIRED`** (`authorization: "NONE"`).

All prerequisites under owner approval `GO_RUNTIME_RECOVERY_AND_OFFLINE_REVISION` are complete and verified:

1. Original stalled task tree `bufr6nkj1` was verified by PID/creation-time/command-line chain and terminated with `0`
   surviving processes (`recovery/termination.json`), while preserving all parent artifacts in
   `docs/evaluation/geometry/runs/semantic-extraction-schema-contract/` byte-for-byte (`verification/parent-preservation.json`).
2. Catastrophic regex backtracking in `_SAU_HOP_LE` (`backend/app/simulation/geometry_functions/registry.py`) and pre-route
   `PILOT`/`LOCKED` split isolation (`backend/scripts/run_schema_contract_evaluation.py`) were fixed and verified by
   independent read-only review (`review-gates/revision.json`, `PASS`).
3. Revision protocol (`protocol_sha256 = 4e0ec65e3f93f00c5dc41ebd0df20644661c25e56a50bbd87eb848d813c05a5b`) and frozen
   candidate (`product_sha256 = 6ba9033bfca06d671cd27891e2dad06c7d44f365fed45527123c907d664b65ed`, product commit
   `283813b23afd5a3235cd5d944ef30ebbe9d0691a`) were locked at commit `2b955ead0b0a1d2190395fe50627b0fc3f75f6da`.
4. All 8 sequential offline invocations (`PILOT`/`LOCKED` × `flat`/`v3` × `gold`/`replay`) completed in `13.014s` total
   with `exit_code = 0`, `status = COMPLETE`, `0` unsafe serves, and `0` live model calls (`results/offline/invocations.json`).
5. Authoritative T3 passed on clean detached checkout `04b0db373380d980c82e7b7e58cb3fc51b71812f` (`10,508` backend passed,
   `1,079` frontend passed across `68` files, production build `PASS`, demo replay `5/5`, crash audit `6/6`).

## Exact Live PILOT Envelope Request (`flat-PILOT` and `v3-PILOT` Only)

Full identity dictionaries are recorded in [`approval-identities.json`](approval-identities.json).

| Parameter | Value |
|---|---|
| Target arms / mode | `flat-PILOT` and `v3-PILOT` (`PILOT` 12 development cases only; `LOCKED` live is NOT requested before `PILOT` review) |
| Identity commit | `2b955ead0b0a1d2190395fe50627b0fc3f75f6da` (offline receipts committed at `04b0db373380d980c82e7b7e58cb3fc51b71812f`) |
| `flat-PILOT` canonical identity SHA-256 | `f9cbf39966c9b71280d388890944c678d47e1a6194d3efd515977ee5ce05070b` |
| `v3-PILOT` canonical identity SHA-256 | `6f97a22be91daea8b376dd9302025870be40a6bb83f47d04a81259664147ebe0` |
| (`flat-LOCKED` / `v3-LOCKED` inventory SHA-256) | `3377169ea0e58e4c8048581e894f8d7c8a52477cf3dd1d035e2c9809ec01aeb5` / `266c6ffa90adef2e18d9f299eaa61aea60f7027cc5ba33d6a42b105d84600d4f` (inventory only; not requested now) |
| Model | `gemini-2.5-flash` |
| `protocol_sha256` | `4e0ec65e3f93f00c5dc41ebd0df20644661c25e56a50bbd87eb848d813c05a5b` |
| `product_sha256` | `6ba9033bfca06d671cd27891e2dad06c7d44f365fed45527123c907d664b65ed` |
| `contract_runner_sha256` | `a91f3256ed473656f573ac198b55ad50f65f6f08bfc9c48c56d6e75b5fb6ee80` |
| `flat` / `v3` `surface_sha256` | `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a` / `90bf8f039df830062e068adcf1d243643c8ebebfde5b4a5cf9ec340078ea7aab` |
| `PILOT` cap per arm | `12` logical calls, `12` HTTP attempts, `800,000` accounted tokens, `USD 0.50`, `1` sample |
| `PILOT` paired total (`flat` + `v3`) | `24` logical calls, `24` HTTP attempts, `1,600,000` accounted tokens, `USD 1.00` |
| Retries / HTTP timeout | `0` retries / `90` seconds |
| Mandatory stop rules | HTTP `400`/`401`/`403`/`429`, logical/HTTP/token/USD/context caps, persistence/secret failure, model version drift, disabled live AI, post-response adapter failure, unknown/inconsistent usage, or 3 consecutive infrastructure errors |
| Held-out blindness disclosure | Held-out case `h07` was inspected during runtime stall diagnosis; the 24-case `LOCKED` split is `REUSED_DIAGNOSTIC_NOT_FRESH_BLIND` |
| Product defaults | `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `CACHE_VERSION = 125`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO` |
