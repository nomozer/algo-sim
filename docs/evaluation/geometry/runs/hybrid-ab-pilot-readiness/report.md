# Hybrid A/B readiness — LOCAL correction and offline certification

Status: `HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW`. No live approval, merge, push, or default change.
Product code: `cfe2ada5`; candidate: `12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52` (110 files).
Verified runner code: `2f1b457c` (evaluation-only taxonomy / oracle / scoring follow-ups; product remains `cfe2ada5`).
Branch: `feat/text-to-geometry-functions`; cache 125; live Gemini calls **0**. Documentation commit role: SELF.

## Budget resolution

The old shared output ceiling 8192 plus payload-specific reservations exceeds both registered USD ceilings and the old FULL
5.2M accounted-token ceiling. A fixed 18k reservation also understates large function-declaration payloads. The replacement
counts the *actual canonical UTF-8 request payload*, including system instruction, function/schema surface and problem text:

`reserved_prompt = payload_bytes + 4096`; `reserved_total = reserved_prompt + maxOutputTokens`;
`reserved_USD = reserved_prompt × 0.30 / 1e6 + maxOutputTokens × 2.50 / 1e6`.

Output/thinking is reserved once. Gemini documents that the output ceiling includes thinking and visible output; lowering it
can truncate a response, including a billed response with little visible content. This is not evidence that 3072 is sufficient
for real model reasoning. [Thinking limits](https://ai.google.dev/gemini-api/docs/thinking#token-limits-and-max_output_tokens),
[pricing](https://ai.google.dev/gemini-api/docs/pricing).

| Shared output cap | Smoke accounted tokens | Smoke reserved USD | Full accounted tokens | Full reserved USD |
|---|---:|---:|---:|---:|
| 2048 | 470,640 | 0.2493264 | 5,645,322 | 2.9912094 |
| **3072 selected** | **495,216** | **0.3107664** | **5,940,234** | **3.7284894** |
| 8192 | 618,096 | 0.6179664 | 7,414,794 | 7.4148894 |

All 96 distinct payloads (48 × A/B), and repetition/selection totals, are in `diagnostics/budget_audit.json`. Final ceilings:
SMOKE 24 logical / 36 HTTP / 500,000 accounted / USD 0.60; FULL 300 logical / 450 HTTP / 6,000,000 accounted / USD 7.00
(scheduled exactly 288). Only the FULL *accounting* cap increases; USD caps do not. Output 3072 is shared by both arms,
temperature 0, model `gemini-2.5-flash`. Largest fake content-parts response is 1644 bytes, with fake thinking=0.

Bytes are **not billed tokens**, and +4096 is **not a provider-proven overhead bound**. Input context limit is 1,048,576;
the runner's local estimator prechecks it but cannot prove real context/billing containment. Full request token counting includes
system instructions and function declarations; no countTokens request was made. [Token API](https://ai.google.dev/api/tokens),
[model limits](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash).

Reservations are held conservatively and checked before every request; actual input/output/thinking usage is recorded separately.
Unknown cost is null, never zero. Reservation breach, timeout, HTTP error, truncated/blocked output, missing usage/model,
identity or secret failure stops without retry. A breach with valid counters retains its known usage/cost. This detects overrun
*after* a response; it cannot retroactively prevent provider billing. Therefore strict live billed-cap containment remains NO-GO.

## Implementation and review correction

The runner reuses `run_ai_function_route` / `run_ai_fact_route`, shared registry/engine/kernel/Scene3D, existing Gemini transport
and candidate-hash authority. No new solver, planner, renderer, geometry function, fallback, or default route is added.

- `registry.py`: cube/cuboid predicates bind exact polygon groups, not substrings, mixed faces, another object or a later clause.
  The fresh review exposed unrelated “đều” / “hình vuông” bypassing the cube gate; each regularity witness now binds its object.
  Existing named regular polygons, regular-tetrahedron faces and unique named-base shorthand remain covered by regression.
- `function_route.py`: `TRUE_ON_CONFIGURATION` / `FALSE_ON_CONFIGURATION` remain observations, `UNVERIFIABLE`, never proof;
  proof-only requests refuse `PROOF_UNVERIFIABLE`; uncertified negation refuses `NEGATED_CLAUSE`, not global inconsistency.
- The experimental adapters explicitly refuse malformed nested content. An unexpected post-response exception has a durable
  `POST_RESPONSE_FAILURE` row preserving known response/usage; exception messages are not persisted. Persistence uncertainty
  retains a pending journal and is not resumed automatically.
- Resume checks execution class and live-call count as well as mode, payload/runner/product identities, schedule, row hashes,
  reservations and totals, including terminal manifests; fake/live results cannot mix silently.
- Taxonomy now matches actual grounding codes. The scorer enforces question-object signatures, exact answer/dimension,
  scene/chart-metric lengths, units, refusal codes and checker/proof obligations. Unsafe refusal becomes `obligation_violation`,
  not “correct”; uncertifiable refusal/infra rows make a full comparison inconclusive. A served result violating geometry/proof
  obligations remains `wrong_served` and is counted in safety statistics, not erased as infrastructure. Refusal metadata is
  checked for illicit proof claims even when its refusal code itself is correct.
- A typed failure from the *existing* HTTP transport preserves status and recoverable JSON body, redacted at the runner boundary;
  non-JSON error bodies and unavailable usage remain UNKNOWN. Tests mock HTTP responses; no real HTTP request was sent.

Review: one fresh whole-task review of `5c33406a..a2db9272`, no Critical / six Important / one Minor. The bounded pass reproduced
24 failing cases (plus one already-passing proof case) before fixes. HTTP secret detection intentionally takes priority over
HTTP_ERROR; its test now verifies both leak and non-leak responses. A further accounting RED→GREEN retains known breach usage; a real invalid-call-schema RED→GREEN makes A `SCHEMA_INVALID`
(and invalid model-call dependencies) extraction errors, not geometry. B schema errors remain compiler errors.
The reviewer-labelled Minor undefined selective-accuracy / negative-refusal metrics were regraded Important because the human
spec requires honest missing/undefined statistics. All seven Important findings after regrading are addressed with tests.
Two additional scorer RED→GREEN cases close refusal proof-metadata and counted served-geometry obligations. No second
reviewer or claimed independent post-fix review. Details: `diagnostics/review_resolution-final.json`; the earlier review-resolution snapshot remains unchanged.

## Identity and evidence boundaries

Exact per-mode corpus/oracle/question/parameter/schedule/seed/runner/product hashes and caps are in `run.json`. SMOKE selection
is locked before execution and cannot be scored as FULL. Current surfaces at output3072:

- A: `f329e89155b162ad1e0cd03b6c437542b0be8175907c09153e4b508a2f75f8ee`
- B: `aa198078c47ffdf0e05e31b1726c62c1c218a87dc02e7d5698f144c11d27e2ce`

The post-review runner hash is `f456cf95e6e87672183f4f955f4ff309a25ea39dd1c1bdc83ee8055bfe8f8899`. The earlier frozen
`fake-provider/` manifests and 314-pass `diagnostics/focused.xml` describe pre-review identities and remain unchanged.
Current certification is additive under `fake-provider/verified/`; earlier `fake-provider/review-fix/`, `final/` and
`safety-certified/` snapshots also remain unchanged. No old/new outputs are pooled. The current candidate was
refrozen from clean source `cfe2ada5`; current divergence authority moved to this run, leaving the old declaration untouched.
No historical thesis/hybrid result is rescored or rewritten. Cache 125 remains appropriate: experimental modules are outside
the product default route, and the existing cache/route dependency tests guard that boundary.

## Verification

| Gate | Current evidence | Result |
|---|---|---|
| Focused safety, adapters, A/B, independent geometry, runner | `diagnostics/focused-verified.xml` | 344 pass, 0 fail/skip/deselected; 50.12s |
| In-memory guard-removal mutation | Included in focused XML | 9/9 mutants killed; not an exhaustive mutation campaign |
| Fake schedules through real adapters | `fake-provider/verified/CERTIFICATION.json` | 24 + 288 = 312; network/live 0; no stop |
| Renderer metric | `diagnostics/renderer-metric.log` | 14 scenes, 194 pairs; max relative error 7.02e-10 (<1e-9); not visual acceptance |
| Candidate / cache identity | `diagnostics/verification.json` | Candidate12da4768 / cache125 match; frozen per-mode identities match current code |
| Full backend, clean detached checkout | `diagnostics/full-backend-authoritative.xml`, clean `2f1b457c` | 8068 pass, 0 fail, 1 skip, 2 deselected; 359.12s; clean before/after |
| Documentation gates | `diagnostics/docs-audit-final.json`, `diagnostics/docs-final.xml`, clean `475defaa` | Audit PASS;153 tests PASS/0 fail/skip,38.27s;48 artifact hashes verified; clean before/after |
| Additional frontend regression/build | Native Vitest + tsc/Vite | 1040 tests/67 files PASS,7.05s; fresh-output build PASS |

Frontend build to the existing `dist` failed on EPERM while emptying its assets directory. Building the same source with a
new validated output under ignored workspace scratch passed (94 transformed modules,2.29s); no manual deletion of existing output was performed; the failed build's partial-cleanup state was not inventoried.
Original dist permissions remain unresolved. Existing SSR useLayoutEffect and large-bundle warnings were observed, not repaired.

Fake FULL records contain 138 correct served / 90 correct refusal / 60 false refusal and no obligation violations. These are
fixture apparatus outcomes, **not Gemini quality**. G05 receives explicit unsupported fake fixtures, accounting for its positive
false refusals. Fake token counters/costs are simulated bytes; `actual_usd` in those manifests is not real expenditure.
The 14 numeric renderer input scenes structurally match current B sample1 fake outputs before reuse; no browser/human visual
acceptance occurred. Hidden edges, labels, faces and interaction quality remain unaccepted.

The exploratory full diagnostic returned 8036 pass / 2 fail / 1 skip / 2 deselected, 332.11s: an uncommitted candidate manifest
made its checkout dirty; the old divergence-authority pointer failed after product changes. Its failed journal is retained in
ignored local scratch, not counted as a green gate. The corrected test checks the new additive declaration with the same invariant.
The clean pre-final-taxonomy suite at `0b144c81` then passed8065 / skipped1 / deselected2 in371.27s; its XML is retained
as `diagnostics/full-backend.xml`, not relabelled as testing the final runner. A further clean suite at `8aad0673` passed8066 / skipped1 / deselected2 in372.93s (`full-backend-final.xml`).
The authoritative suite at `2f1b457c` is separate: 8068 PASS,1 skip,2 deselected,0 failures/errors; selected8069/collected8071.
The one skip is an existing scalar-obligation case: missing `term` defaults to identity and has a separate test. Deselections are
opt-in Postgres/external-evidence markers, not live calls. The existing Starlette TestClient deprecation warning remains.
One earlier fake run stopped at row266 on local atomic I/O failure; cause UNKNOWN, pending journal retained without resume.
A separate 312-row fake run failed summary serialization (integer JSON keys); RED→GREEN fixed it. Failed scratch is not research
evidence, contains no real model calls, and is retained recoverably. A later safety-oracle certification also stopped on persistence: SMOKE24 complete, FULL109 durable rows, with a completed
row110 in `manifest.pending`. Its journal was moved recoverably into ignored scratch, never resumed/retried; cause/errno/winerror
are UNKNOWN. A new instrumented attempt and the current verified attempt each completed312. No reliability claim from reruns;
`ISSUE-OPS-HYBRID-PERSISTENCE-FAILURE-UNRECOVERED` remains OPEN and must be accepted/resolved before live execution.

## Statistical interpretation and decisions

FULL uses paired problem-cluster bootstrap (2000, seed20261010) with repeated-cluster multiplicity preserved; output ratios
include thinking. It reports SUPERIOR, NON_INFERIOR_NOT_SUPERIOR, INFERIOR, INCONCLUSIVE_STATISTICAL or
INCONCLUSIVE_INFRASTRUCTURE. Failure to establish noninferiority is not proof of inferiority. Negative correct-refusal rates
have separate denominators; selective accuracy is null if no problem was served.

Zero wrong_served in both arms does **not** prove safety or true error rate0. For144 per-arm rows the zero-event one-sided95%
IID bound is about2.06%; repeated samples are dependent. A zero-error bound over48 problem clusters is about6.05%, under its
own independence/sampling assumptions. This development corpus is not a random population sample; neither is a population
guarantee. The degenerate zero-event bootstrap is reported with those limitations, not marketed as a safety proof.

| Decision | Status | Requirement before change |
|---|---|---|
| Offline runner readiness | GO — bounded offline wiring/guards certification | Clean backend/docs PASS; identity journals sealed; not a reliability or real-model claim |
| SMOKE live execution | NO-GO | Human review of exact identities + verified prompt-count/billing basis + storage-risk acceptance/resolution + explicit smoke approval |
| FULL live execution | NO-GO | Smoke completion/review plus separate exact-identity full approval; no smoke superiority claim |

Skills used: using-superpowers; brainstorming/writing-plans; executing-plans; TDD and writing-good-tests; systematic-debugging;
verification-before-completion; requesting/receiving-code-review; using-git-worktrees; graphify; karpathy-guidelines; ponytail.
Their effect: reused existing authorities, literal RED tests and a single bounded fresh review; additive evidence and clean-source
verification instead of architecture expansion. Finishing branch policy keeps the research branch local; no integration authorized.

Next action: human review of [`protocol.md`](protocol.md), [`run.json`](run.json) and [`handoff.md`](handoff.md). No approval
artifact is manufactured, and no script writes APPROVED_BY_USER. Main remains the preflight local ref `28ac1d61`.

## Rulings made during inline execution (in order)

1. Task1 ends at RED and commits tests before implementation; its standalone green gate is deferred to Tasks2/3. Cost if wrong:
   no green Task1 commit; the exact oracle tests must subsequently pass (now covered by focused suite).
2. Reserve combined output/thinking once, use3072 and FULL6M accounted while preserving USD7. Cost if wrong: model thinking
   or input overhead can defeat the estimate; live remains NO-GO, not retrospectively asserted safe.
3. Bytes+4096 is only a local estimator, not a provider bound. Cost if wrong: strict billed-cap containment remains unavailable.
4. Stop on the first provider/truncation failure instead of old tolerance thresholds. Cost if wrong: incomplete pilots are
   more frequent, but uncertain-cost retries are not silently enabled.
5. Add INCONCLUSIVE_STATISTICAL. Cost if wrong: comparison may remain undecided; failure of noninferiority is not inferiority.
6. Match questions by function/arguments, not insertion order/IDs. Cost if wrong: alternate equivalent notation needs adjudication;
   a correct number on a wrong object cannot receive an automatic correct-service label.
7. Tasks4–6 were vertical slices of one module committed together, not retroactively split. Cost if wrong: coarser commit granularity;
   earlier safety history remains intact and per-slice RED→GREEN evidence was observed.
8. Reviewer set aside strict billed-budget proof: retain live NO-GO, do not call APIs to fill it. Cost if wrong: live overspend risk
   remains open, not a hidden GO assumption.
9. Reviewer set aside live thinking/truncation: require an approved smoke review later. Cost if wrong: real model may truncate.
10. Reviewer set aside human visual acceptance: only14-scene metric is claimed. Cost if wrong: display quality remains unaccepted.
11. Reviewer set aside general proof completeness: stay within observation/UNVERIFIABLE boundary. Cost if wrong: general proof
    requests safely refuse; no new proof engine delivered.
12. Reviewer set aside equivalent notation: conservative signature matching stands. Cost if wrong: valid equivalents may count
    wrong until independent adjudication; quality claims must disclose this bias.
13. Reviewer did not judge unfinished handoff/full suite: final clean gates are implementer-owned, no second reviewer. Cost if
    wrong: final docs and post-fix judgments have no independent re-review.
14. Use a new build output after dist EPERM instead of removing old output. Cost if wrong: original dist permissions unresolved.
15. Retain ignored failed journals/ledger instead of skill scratch deletion, honoring preservation and recoverability. Cost if wrong:
    retained local scratch consumes disk; no old evidence or uncertain request journal is lost. No deferred Minor finding remains.
16. Existing live transport is exercised only through mocked HTTP, never an unmocked live request. This clarifies the plan's
    transport prohibition without changing the human zero-call rule. Cost if wrong: a missing mock would risk a real call;
    certification hard-blocks sockets/HTTP and these unit cases replace httpx.post explicitly.
