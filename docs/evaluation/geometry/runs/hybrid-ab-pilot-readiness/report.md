# Hybrid A/B readiness — LOCAL correction and offline certification

Status: `HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW`. No live approval, merge, push, or default change.
Product code: `cfe2ada5`; candidate: `12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52` (110 files).
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
  not “correct”; obligation/infra rows make a full comparison inconclusive.
- A typed failure from the *existing* HTTP transport preserves status and recoverable JSON body, redacted at the runner boundary;
  non-JSON error bodies and unavailable usage remain UNKNOWN. Tests mock HTTP responses; no real HTTP request was sent.

Review: one fresh whole-task review of `5c33406a..a2db9272`, no Critical / six Important / one Minor. The bounded pass reproduced
24 failing cases (plus one already-passing proof case) before fixes. HTTP secret detection intentionally takes priority over
HTTP_ERROR; its test now verifies both leak and non-leak responses. A further accounting RED→GREEN retains known breach usage.
All Important findings and the Minor undefined selective-accuracy / negative-refusal metrics are addressed with tests.
No second reviewer or claimed independent post-fix review. Details: `diagnostics/review_resolution.json`.

## Identity and evidence boundaries

Exact per-mode corpus/oracle/question/parameter/schedule/seed/runner/product hashes and caps are in `run.json`. SMOKE selection
is locked before execution and cannot be scored as FULL. Current surfaces at output3072:

- A: `f329e89155b162ad1e0cd03b6c437542b0be8175907c09153e4b508a2f75f8ee`
- B: `aa198078c47ffdf0e05e31b1726c62c1c218a87dc02e7d5698f144c11d27e2ce`

The post-review runner hash is `6426e497cd535ad58fdc7d7c2b94506b6c079d8694a570956ba62124a719ab9f`. The earlier frozen
`fake-provider/` manifests and 314-pass `diagnostics/focused.xml` describe pre-review identities and remain unchanged.
Current certification is additive under `fake-provider/review-fix/`; no old/new outputs are pooled. The current candidate was
refrozen from clean source `cfe2ada5`; current divergence authority moved to this run, leaving the old declaration untouched.
No historical thesis/hybrid result is rescored or rewritten. Cache 125 remains appropriate: experimental modules are outside
the product default route, and the existing cache/route dependency tests guard that boundary.

## Verification

| Gate | Current evidence | Result |
|---|---|---|
| Focused safety, adapters, A/B, independent geometry, runner | `diagnostics/focused-review-fix.xml` | 341 pass, 0 fail/skip/deselected; 49.29s |
| In-memory guard-removal mutation | Included in focused XML | 9/9 mutants killed; not an exhaustive mutation campaign |
| Fake schedules through real adapters | `fake-provider/review-fix/CERTIFICATION.json` | 24 + 288 = 312; network/live 0; no stop |
| Renderer metric | `diagnostics/renderer-metric.log` | 14 scenes, 194 pairs; max relative error 7.02e-10 (<1e-9); not visual acceptance |
| Candidate / cache identity | Clean detached candidate source; final verify journal pending | Current candidate frozen; final guards PENDING |
| Full backend, clean detached checkout | Final diagnostics pending | PENDING; not yet a readiness GO |
| Documentation gates | Final diagnostics pending | PENDING |

Fake FULL records contain 138 correct served / 90 correct refusal / 60 false refusal and no obligation violations. These are
fixture apparatus outcomes, **not Gemini quality**. G05 receives explicit unsupported fake fixtures, accounting for its positive
false refusals. Fake token counters/costs are simulated bytes; `actual_usd` in those manifests is not real expenditure.
The numeric renderer input scenes are compared byte-for-byte with current fake outputs before reuse; no browser/human visual
acceptance occurred. Hidden edges, labels, faces and interaction quality remain unaccepted.

The exploratory full diagnostic returned 8036 pass / 2 fail / 1 skip / 2 deselected, 332.11s: an uncommitted candidate manifest
made its checkout dirty; the old divergence-authority pointer failed after product changes. Its failed journal is retained in
ignored local scratch, not counted as a green gate. The corrected test checks the new additive declaration with the same invariant.
One earlier fake run stopped at row266 on local atomic I/O failure; cause UNKNOWN, pending journal retained without resume.
A separate 312-row fake run failed summary serialization (integer JSON keys); RED→GREEN fixed it. Failed scratch is not research
evidence, contains no real model calls, and is retained recoverably. No reliability claim from one successful rerun.

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
| Offline runner readiness | PENDING clean full regression/docs guards | All verification gates must pass |
| SMOKE live execution | NO-GO | Human review of exact identities + verified prompt-count/billing basis + explicit smoke approval |
| FULL live execution | NO-GO | Smoke completion/review plus separate exact-identity full approval; no smoke superiority claim |

Skills used: using-superpowers; brainstorming/writing-plans; executing-plans; TDD and writing-good-tests; systematic-debugging;
verification-before-completion; requesting/receiving-code-review; using-git-worktrees; graphify; karpathy-guidelines; ponytail.
Their effect: reused existing authorities, literal RED tests and a single bounded fresh review; additive evidence and clean-source
verification instead of architecture expansion. Finishing branch policy keeps the research branch local; no integration authorized.

Next action: human review of [`protocol.md`](protocol.md), [`run.json`](run.json) and [`handoff.md`](handoff.md). No approval
artifact is manufactured, and no script writes APPROVED_BY_USER. Main remains the preflight local ref `28ac1d61`.
