# Migration readiness and release decision

Date: 2026-10-23. Assessed product: Session 3 `69bd2fe4…`; candidate `84c729e0…`; documentation `0f7b3a69…`. Session 4A changes only offline tooling/reports/index pointers on a branch from main. No product activation is implied.

## Four separate decisions

| Level | Decision | Basis / remaining work |
|---|---|---|
| 1. Offline research engine | **READY, bounded scope** | Existing exact deterministic route and pinned T3 receipt, fresh targeted verification, 22/22 positive canonical seam cases and 12/12 new development diagnostics. Valid for research on declared supported facts, not a general geometry or NL E2E claim. |
| 2. Integrate code into main, production disabled | **PARTIAL** | Read-only merge analysis has no content conflicts; main/S3 frontend trees agree. Actual combined candidate, complete integration gate, shared docs/candidate reconciliation and owner integration disposition remain pending. Nothing was merged. |
| 3. Bounded live experiment | **BLOCKED** | Need owner GO, independent curator/pilot, provider/model/prompt/schema/price lock and enforced caps. Existing flat output cannot measure V2 extraction. Concrete proposal is in OWNER_LIVE_EVALUATION_DECISION.md; this is readiness preparation, not authorization. |
| 4. Replace legacy backend in production | **BLOCKED / NO-GO** | D-04/10/11/12 and compiler-first gates remain incomplete; no independent full E2E, live paired benchmark, product rollout/rollback acceptance or learner evaluation. |

## Route-D blockers re-evaluated

| Gate | Session 4A assessment | Required acceptance evidence |
|---|---|---|
| D-04 extraction contract | **PARTIAL offline; BLOCKED NL V2 validation** | Strict `/2`, route-labelled `/1` conversion and one source authority exist. Production remains flat. Forty-four archived provider rows give no V2 provider sample. Need separately locked extraction/full-E2E tracks on fresh source texts; no guessed flat→V2 mapping. |
| D-10 certificate-backed Scene3D | **PARTIAL backend; combined frontend acceptance OPEN** | Engine emits certificates; latest frontend tree is shared with main and has substantial rendering work. This does not prove that Adapter `/4`'s sections/closure/ratio/residual data reach a product caller and are interpreted correctly. Need `/4` consumer fixtures, certificate tampering/refusal checks, selected camera/step browser evidence and owner visual acceptance on that exact combined build. Canonical stream validity alone is insufficient. |
| D-11 paired live benchmark | **BLOCKED / NOT_STARTED in 4A** | No provider call made. Curator/owner lock and budget gate before any paired attempts. Fake-provider benchmark H is not live evidence. |
| D-12 rollback and route-aware cache | **PARTIAL** | Existing route-aware policy and snapshot logic preserve default identity; preview has no cache. Real V2 provider/cached serving is not implemented/tested here. Need enable→populate→disable and reverse-transition tests on the actual proposed route, including in-flight snapshot behavior and incompatible-envelope rejection. |
| D-13 activation | **NO-GO** | Owner release decision after required gates; never inferred from offline tests. |

D-01/03/05/06/07/08/09 retain their previously documented **scoped** research/preview evidence. Session 4A does not upgrade them to unrestricted production guarantees. Default isolation and route-cache tests are included in targeted verification; evidence quality and denominator corrections are in SESSION3_EVIDENCE_RECONCILIATION.md.

## All twenty compiler-first gates

These gates govern the compiler-first migration, distinct from opt-in Route-D research. The canonical checklist contains historical descriptions already identified as stale (especially hidden-line/routing/fallback implementation). This table separates that existing status from what 4A actually establishes. No canonical status is silently promoted.

| Gate | Canonical status retained | 4A reassessment / next evidence |
|---|---|---|
| 01 Structured Analyze | PROVED_ON_PILOT | No independent new NL→V2 samples; measure extraction fidelity across fresh families. |
| 02 Contract Validation | PROVED_ON_PILOT | V2 schema validated offline; not universal RequestContract/compiler topology coverage. |
| 03 FactGraph Safety | PROVED_ON_PILOT | Deterministic source/geometry refusals are scoped; no expanded transitive-inference proof. |
| 04 Primitive Coverage | PARTIAL | Canonical V2 bridge excludes curved solids, non-root qualified identity and unsupported forms; publish scope instead of generic coverage. |
| 05 Compiler Correctness | PROVED_ON_PILOT | Exact offline checks support known paths; not an independent NL/full-product result. |
| 06 Topology Verification | PROVED_ON_PILOT | Exact section closure strengthened; arbitrary polyhedron planning/topology remains limited. |
| 07 Final-Memory & Answer | PROVED_ON_PILOT | 12 new diagnostics exact, original corpus counts scoped; independent holdout pending. |
| 08 Visual Quality/Fidelity | PROVED_ON_PILOT | Same latest frontend source tree; no new `/4` visual acceptance or browser run. |
| 09 Layout/Camera | PARTIAL | Adaptive framing exists in latest frontend history; no new locked acceptance across families in 4A. |
| 10 Hidden Lines | NOT_STARTED (stale implementation description) | Renderer has later occlusion/section work; assess actual acceptance separately instead of assuming no code or claiming production closure. |
| 11 Compiler-First Routing | NOT_STARTED (historical status) | Opt-in routing exists; default remains LLM_ONLY. No default-switch/live routing acceptance. |
| 12 Fallback | NOT_STARTED (historical status) | Recoverable/fatal decisions exist; actual V2 provider failure/fallback semantics need a locked end-to-end acceptance test. |
| 13 Canary | NOT_STARTED | No rollout requested or built. |
| 14 Rollback | NOT_STARTED | Route-D D-12 is partial; full compiler/product rollback acceptance remains open. |
| 15 Holdout | NOT_STARTED | Protocol prepared; evaluator, sealed sources/oracles/seed and execution pending. |
| 16 Tokens/Latency | PARTIAL | Offline timings only; new provider tokens/latency/cost UNKNOWN, not zero. |
| 17 Unsafe Acceptance | PROVED_ON_PILOT | No wrong serve observed in the checked canonical/diagnostic arms; no pooled “0/562” claim or population guarantee. |
| 18 Observability | PARTIAL | Existing runtime identity diagnostics; new offline stage records do not establish production telemetry. |
| 19 Cache/Version | PRODUCTION_READY for LLM_ONLY only | CACHE_VERSION 127 unchanged; route-aware snapshot regression checked. V2 cached serving remains D-02/D-12 work. |
| 20 User/Pedagogy | NOT_STARTED | No learner study or full-product pedagogical acceptance in 4A. |

**Release recommendation:** retain research use; review a coherent disabled integration candidate next. Complete independent extraction/E2E and combined certificate-rendering evidence before considering activation. Do not change `DEFAULT_MODE=LLM_ONLY`, `RESPONSE_CONTRACT=flat`, `HYBRID_PRODUCT_ENABLEMENT=NO-GO`, `ALLOW_LIVE_AI=0`, `CACHE_VERSION=127`, or `MAX_MEMORY_DECLARATIONS=32`.
