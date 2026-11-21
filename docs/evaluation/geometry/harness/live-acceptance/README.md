# Live-acceptance harness (`axo-live-acceptance-harness/1`)

Shared tooling for live acceptance of the local-only Hybrid route on the real app (backend + frontend + GGUF +
llama.cpp + browser). Before this harness existed, each run copied these scripts into its own `tools/` folder. Their default
output was the run folder itself, so re-running an old copy overwrote frozen evidence. Here **no tool has a
default output**. Every tool refuses to write into an existing file or a non-empty directory. Inputs are read-only paths.

| tool | inputs | output |
|---|---|---|
| `live_browser_acceptance.mjs` | `--manifest`, `--base` (default `http://127.0.0.1:4173`), `--filter all\|valid\|negative`, `--batch-size`, `--label` | `--out-dir`: `responses.jsonl`, `browser_checks.json`, `screenshots/` |
| `ui_scenarios.mjs` | `--manifest`, `--browser-checks`, `--base` | `--out-dir`: `ui_scenarios.json`, `screenshots/` |
| `scene_oracle.py` | `<manifest> <responses.jsonl>` (independent exact validator; `--selfcheck`) | `<out.json>` (new file) |
| `aggregate.py` | `--run-dir` + `--layout v12\|generic` (input file names) | `--out-dir`: `LIVE_ACCEPTANCE_RESULTS`, `SLM_LIVE_CONTRIBUTION_AUDIT`, `VISUAL_AND_INTERACTION_ACCEPTANCE`, `NETWORK_ISOLATION_PROOF` |
| `perf_bench.py` | `--base-url --manifest --browser-checks --freeze --stack-csv` | `--out` (new file) |
| `egress_blackhole_proxy.py`, `tcp_egress_sampler.ps1`, `stack_memory_sampler.ps1` | — | path arguments, as in the /12 run |

Browser scripts run from `frontend/` so that Playwright resolves (`node ../docs/evaluation/geometry/harness/live-acceptance/<tool>.mjs …`).

Equivalence with the /12 run (`runs/axo-hybrid-compositional-geometry-language-grounded-simulation/`) is locked by
`backend/tests/geometry/test_shared_live_harness.py`:

- the oracle replay on /12 responses reproduces `SCENE_ORACLE_VERIFICATION.json` (139 results);
- the aggregate replay (`--layout v12`) reproduces the four /12 deliverables, and only the `schema` and `harness_version` keys differ;
- the proxy and both samplers are byte copies of the /12 tools.

The validation record is `runs/axo-hybrid-local-model1-finalization-test-consolidation/SHARED_LIVE_HARNESS_VALIDATION.json`.
