# Provisional image-input architecture decision

Status: **DECISION_PENDING_LIVE_EVIDENCE**

Retain local OCR followed by source checks and targeted user confirmation as the provisional image-input route. Keep the existing Geometry Planner, Registry, Exact Kernel and Scene3D adapter responsible for mathematical execution. OCR agreement and user confirmation alone do not certify geometric facts or answers.

The prior receipts show one automatic local image solve among 11 supported printed problem instances; ten further solves used simulated ground-truth-assisted confirmation. The corrected full-text CER median on five new polyhedral images is 0.1135. These are exposed development measurements with unverified agent transcriptions, not independent H1 or a student usability study. See `prior_metric_reconciliation.json`.

Live Vision is **NOT_AUTHORIZED** and **LIVE_VISION_NOT_MEASURED**. A paired comparison cannot rank local-first against Vision without real provider measurements on the same hash-bound images, a frozen candidate, and separately graded recognition, source fidelity, parsing, solving and scene results. Historical synthetic responses and telemetry do not supply that comparison.

Before reconsidering the route, obtain explicit owner authorization naming provider/model, data hashes, request and USD budgets and mandatory stop conditions. Reuse the existing paired-route `SafeCampaignBudget` for request reservation and USD accounting before any live transport. The offline `tools/vision_comparison.py` checks authorization prerequisites and deliberately has no live executor while authorization is absent.

Human confirmation usability remains **NOT_MEASURED**. Automated browser checks demonstrate software interactions only; parent-owned current-run receipts require review before claiming their individual outcomes. Keep handwriting and diagram-dependent facts fail-closed, and expose uncertainty for review.

The current product fixes concern OCR worker lifecycle and confirmation state. They do not expand geometric capability. Final candidate freeze and regression evidence are separate parent-owned gates. This provisional record changes no product routing, contracts, live policy or historical evidence.

## Decision matrix (measured facts separated from inference)

| Criterion | Local-first + confirmation | Vision-first | Adaptive local + Vision |
|---|---|---|---|
| Critical-input accuracy | New6 evaluation references: token/fact proxies only, no independently adjudicated semantic accuracy. All require review;0 new served. | NOT_MEASURED | NOT_MEASURED; authored conflict fixtures exercise routing only |
| Correction burden | Per-case scripted span edits recorded; real student effort NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |
| Latency | Precursor prepare-only p50: cold model4596ms, warm miss2532ms, cache161ms; n10 each, shared host | NOT_MEASURED | NOT_MEASURED |
| RAM / CPU | Complete FastAPI+OCR descendant working-set peak: warm p50~746MiB,p95~882MiB;12-thread shared workstation, not physical low-end | NOT_MEASURED | NOT_MEASURED |
| Provider cost |0 provider requests in these offline runs; CPU/server operating cost not measured | Unknown; authorization absent | Unknown; no calibrated fallback rate/cost |
| Privacy | Inference: image is sent to the user's backend; OCR arm sends no image to an AI provider | Inference: selected image must be disclosed to the authorized provider | Inference: only escalated images disclosed, if implemented/authorized |
| Offline operation | Inference: can execute without external AI when backend, engines and application are locally available | Requires provider connectivity | Local arm works under the same conditions; fallback requires connectivity |
| Operational complexity | Existing sidecar lifecycle plus confirmation, with measured bounded cleanup | Provider credentials, budgets, source fidelity and failure handling remain necessary | Adds fallback policy and cross-checking; benefit unproved |

The evidence supports retaining the existing local path while designing the authorized paired experiment. It does not establish that local-first is more accurate or cheaper end to end than Vision-first. Do not select a final winner until equivalent image hashes, references, criteria and timing boundaries have been measured live under an approved budget.
