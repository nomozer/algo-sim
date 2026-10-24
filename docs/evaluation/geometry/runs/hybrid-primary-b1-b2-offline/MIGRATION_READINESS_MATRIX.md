# Migration readiness matrix

This is a scoped B1/B2 assessment, not an edit or automatic approval of `docs/MIGRATION_CHECKLIST.md`. Its 20 GATE items concern compiler Route C; canonical V2 Hybrid Route D also has 13 separate D gates. Historical pilot evidence and offline subsets do not establish production readiness.

| Gate | Current evidence | Status in B1/B2 scope | Blocker | Required action | Owner approval |
|---|---|---|---|---|---|
| 01 Structured analyze | Historical pilot; new V2 fake/replay interface | PILOT_ONLY | No eligible live V2 outputs | Lock provider/prompt/schema, bounded paired measurement | Live GO |
| 02 Contract validation | Canonical V2, verbatim source/quote and role tests | OFFLINE_VERIFIED | Full semantic fidelity not independently measured | New independent extraction evaluation | Live/holdout GO |
| 03 Fact safety | Existing strict Registry source gate | OFFLINE_PARTIAL | Closed source grammar, incomplete general premise coverage | Independent adversarial scope audit | Scope decision |
| 04 Coverage | 22 positive development scenes; supported pyramids/prisms/sections | OFFLINE_PARTIAL | Unsupported families/operands/wordings remain | Prioritize a demonstrated capability gap | Expansion GO |
| 05 Exact engine correctness | Existing exact engine and unchanged independent squared-answer oracle | OFFLINE_VERIFIED | Finite corpus only | Broader independently curated evidence | Holdout GO |
| 06 Topology verification | Existing exact section closure plus producer/consumer checks | OFFLINE_VERIFIED | Arbitrary polyhedra/frames not generalized | Separate topology scope/evaluation | Expansion GO |
| 07 Memory/answer correctness | Exact-memory binding of point/quantity/answer/dimension/text | OFFLINE_VERIFIED | No live full-source success estimate | Paired live/holdout evaluation | Live GO |
| 08 Visual fidelity | Existing consumer plus current offline browser acceptance | OFFLINE_PARTIAL | Human visual/pedagogical approval pending | Review actual desktop/mobile evidence | Human approval |
| 09 Layout/camera | Existing renderer orbit and responsive paths | OFFLINE_PARTIAL | No general optimal-layout claim | Scoped visual acceptance | Human approval |
| 10 Hidden lines | Existing renderer implementation and geometry regressions | OFFLINE_PARTIAL | Canonical NOT_STARTED text is historical; no broad visual proof | Review code/test/browser evidence by scope | Human approval |
| 11 Routing | Internal service, explicit opt-in, default lock and cache exclusion | OFFLINE_VERIFIED | No authorized production/public V2 endpoint | Approve a deployment/activation contract | Endpoint/deployment GO |
| 12 Fallback | Intentional fail-closed with no automatic LLM fallback | OWNER_REQUIRED | Compiler-C historical fallback policy is not Hybrid-D policy | Approve explicit refusal/fallback contract if deployment needs one | Policy decision |
| 13 Canary | No shadow/canary executed | NOT_MEASURED | No bounded live route/traffic policy | Preregister shadow/canary limits | Deployment/live GO |
| 14 Rollback | Explicit off/default bypass and no shared cache | OFFLINE_VERIFIED | No deployed/in-flight provider rollback experiment | Test deployment rollback and transport cancellation | Deployment GO |
| 15 Holdout | Existing corpus is disclosed development data | NOT_MEASURED | No independent curator/locked new packet | Independent curator, lock and contamination audit | Appoint curator |
| 16 Cost/tokens/latency | Combined offline stage timing only | NOT_MEASURED | Provider counters/pricing/latency unknown | Lock usage accounting, model/pricing, budget/stop rules | Live GO |
| 17 Unsafe acceptance | Zero wrong-served in locked development replay; adversarial boundary tests | OFFLINE_VERIFIED | Finite sample and historical grammar gaps | Independent wrong-served/false-refused audit | Holdout GO |
| 18 Diagnostics | Linked sanitized request/stage receipts | OFFLINE_PARTIAL | No deployed operational monitoring | Specify shadow monitoring/stop thresholds | Deployment GO |
| 19 Cache policy | Existing cache127/default compatibility; new route excluded | OFFLINE_VERIFIED | No Hybrid cached endpoint or migration | Define separate identity/version/migration before caching | Cache/deployment GO |
| 20 Pedagogy | No learner/user study executed | NOT_MEASURED | Human study/protocol absent | Independent educational evaluation | Study GO |

Counts of these scoped categories: **8 OFFLINE_VERIFIED, 6 OFFLINE_PARTIAL, 4 NOT_MEASURED, 1 PILOT_ONLY, 1 OWNER_REQUIRED = 20**. No production gate is promoted by this table. Existing LLM_ONLY cache readiness is retained; it does not make Hybrid production-ready.

| Hybrid D gate | Current scope and remaining requirement |
|---|---|
| D-01 default isolation | Existing static/runtime/default-route probes preserved; two lazy internal validator edges explicitly declared |
| D-02 cache identity | Offline route has no cache; preview policy cannot enter product cache; future cached Hybrid identity needs design |
| D-03 request snapshot | Existing immutable RoutePolicy reused; service records actual internal identities and checks for changes |
| D-04 extraction contract | V2 source/schema interface verified offline; live compatibility, quality and independent fidelity unknown |
| D-05 exact math | Existing exact engine/oracle retained; finite development results only |
| D-06 fail-closed | Schema/source/engine refusals preserved; technical failure is not scored as correct geometry refusal |
| D-07 envelope | Product /4 wrapper and current frontend consumer integrated offline; one historical refusal-category mismatch retained |
| D-08 API gate | Existing operator-only preview unchanged; new service internal only, no authorized public /4 endpoint |
| D-09 observability | Existing diagnostics plus linked local receipts; no deployed telemetry claim |
| D-10 presentation | Existing proof/provenance consumer and current browser run; human review remains pending |
| D-11 paired live | NOT_AUTHORIZED / NOT_MEASURED |
| D-12 rollback | Off/default/cache exclusion proven in offline tests; deployed cancellation/in-flight rollback not measured |
| D-13 enablement | NO-GO until remaining D requirements and explicit owner decision |

## Route to a bounded pilot

Research progression is LLM_ONLY -> offline Hybrid -> approved opt-in -> shadow/canary -> separately approved default. These are readiness stages, not new runtime enum values.

Before a pilot: appoint independent curator/adjudicator; seal new source/gold/oracle packets without implementer contamination; lock candidate, provider/model/version, prompt, schema lowering and harness; measure provider schema compatibility; define attempted-call/token/cost budgets and mandatory stop rules; enforce transport timeout/cancellation, no silent retry/fallback, rate/technical failure taxonomy, paired baseline and all-attempt accounting. Record unknown counters as UNKNOWN. Shadow monitoring must distinguish wrong-served from false-refused and technical failures. Validate rollback and preserve main cache identity before any deployment.

No live pilot, production opt-in, shadow/canary or default switch is authorized by this run.
