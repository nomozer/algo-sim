# Continuation 14 — live readiness, S-2 coverage of R-1, and the Owner gate

**Status: `OFFLINE_READY_AWAITING_OWNER_GO`.** 0 provider calls, USD 0. No Owner approval file exists for S-2 or for the
paired run, so no live step of the directive ran. The directive itself is not a spending approval.

## 1. Checkpoint restored (verified, not re-run)

| item | evidence |
|---|---|
| branch / HEAD at start | `research/hybrid-master-backend-replacement` at `48c7e4c0`, tree clean |
| candidate | `0fe38a29`, product `9503482a`, 118 files `773e440de0385d577040a9eca107706bfb2d3e4aec1d827b52c99c89d42ac7c3`; `freeze_evaluation_candidate.py --verify` matches |
| product drift since freeze | `git diff 0fe38a29 HEAD -- backend/app frontend/src`: empty |
| production defaults | `routing.py::CHE_DO_MAC_DINH = "LLM_ONLY"`, `main.py::CACHE_VERSION = "131"`, D-01 import-closure lock `test_structured_geometry_relations.py::test_Y_*` present |
| approval files | none in the run folder (only `s2-owner-approval.template.json`, `PENDING_OWNER_DECISION`) |

C13 audits (R-1, SL-3, bridge regex, Full T3 at `0fe38a29`) were not repeated: the product has not changed since.

## 2. Live readiness of the two runners (code read, offline tests)

| check | finding |
|---|---|
| identity binding | the approval binds `corpus_sha256`, `measured_system`, `runner_sha256`, `paired_harness_sha256`, `model`; `runtime_identity` is re-read before every case (`IDENTITY_CHANGED` stop) |
| model | `gemini-2.5-flash`, bound; a different model refuses before any request. **Availability is not checkable offline**: Google limits 2.5 access to earlier users (`provider-facts.md`). No silent model switch exists |
| transport, retry, timeout | `hybrid_transport` = `function_calling.live_transport` with `call_gemini`'s retry and 120 s timeout; route deadline `HYBRID_LIVE_DEADLINE_S = 480 s` |
| budget | every HTTP send, retries included, first reserves the exact payload's ceiling in `CostCappedBudget` (request cap + USD cap). Output ceiling `MAX_OUTPUT_TOKENS = 8192` on `/4` |
| stops | S-2: request cap, USD cap, provider block, 3 consecutive infrastructure failures, identity change, interruption (= protocol §5.6). Paired: the same plus 80 % of the USD cap and the Hybrid-only expected-refusal stop (protocol §5) |
| parsing, refusals | decoded by `TransportExtractor`; infrastructure codes become `NOT_RECOVERABLE`, never a model result; refusals classified by `classify_refusal` and the server-built `route-d-clarification/1` |
| usage, cost | `usageMetadata` per row; a row without usage is `UNKNOWN`, never 0 |
| secrets | the key is never written (test-locked) |
| receipt integrity | the output is opened with `"x"` (never overwritten) and flushed per row; a stop writes `INCOMPLETE` |
| **resume / re-run** | **defect found and fixed** (§3) |

## 3. Defect fixed: an approval could fund more than one run

Both runners count `max_requests` and `max_usd` inside one process. Nothing stopped a second `--live` under the same
approval file, so an interrupted run could be "resumed" by sending again requests the Owner's cap had already counted.

Fix (`fe8d0aa6`, scripts and tests only): `run_paired_route_evaluation.claim_approval`, called by both `main`s after
`authorize_live` and before `evaluate`.
- `--out` is created and removed first, so a taken, misspelt or unwritable path does not burn the approval (the
  existence-only check of `fe8d0aa6` missed a missing directory: review round 1, `db601ac8`).
- It then creates `<approval>.consumed` exclusively; a later `--live` under that file is refused before any request.
- There is no resume. A stopped run stays `INCOMPLETE`; a re-run needs a new Owner approval file.
- It guards an accidental re-run, not a copied approval file; the agent never writes approval files (AGENTS.md).

Also from review round 1 (`db601ac8`):
- The paired harness refuses `NaN` / non-positive USD terms and a non-integer `max_requests`. `NaN` compared false
  everywhere and switched the USD cap off; the S-2 runner already had this check.
- The S-2 approval binds `scorer_sha256`, because the scorer writes the summary's 8 metrics.

RED, then GREEN, each time. Harness tests: 95 → 105. Measurement semantics are unchanged. New identity from
`--manifest`:
- runner `2c463ac3…`;
- paired harness `2ac9577f…`;
- scorer `8c330bd4…`.

`measured_system` and the corpus are unchanged. The S-2 template is re-issued as blob `8b2ab292…`; its command was
dry-run with a non-approval value and passed `check_approval_terms` (per-request estimate USD 0.0244).

Kept, recorded:
- **NIT:** S-2 gold replay and attribution run outside the per-case `try`. An exception there after a paid request
  would drop that row as `INTERRUPTED`. This is unlikely: the dry run exercises the same code.
- **NIT:** `hybrid_transport` under-counts `retry_requests`. The cap is unaffected, because every send is counted.
- **NIT:** `arm_upper` can be off by about USD 0.0004.
- **Owner note:** an S-2 run needs 35 requests under the cap of 36, retries included.
- **Owner note:** LLM_ONLY `call_gemini` puts the key in the URL. httpx INFO logging must stay off during the paired run.

## 4. What S-2 can and cannot measure (directive §5.2, §7)

`tools/s2_r1_coverage_scan.py` → `s2-r1-coverage.json` (0 requests):
- 0 of 36 gold extractions declare `described_points`;
- 0 of 36 problem texts phrase a goal through an unnamed described point (the C12 usage regex; that scan never covered
  this corpus, because it is not under `inputs/`). The 5 texts with a derived point all name it ("Gọi M là trung điểm …");
- the 17 gold-served cases all have planner search classification `SOURCE_EXPLICIT_SEQUENCE`; none is
  `DISCOVERED_FUNCTION_COMPOSITION`.

So a live S-2 run measures how the model reads student wording on named constructions. It cannot show whether Gemini
produces correct `DescribedPointSpec`s, nor whether the planner recomposes functions on live extractions:
**`R1_LIVE_GENERALIZATION_NOT_ESTABLISHED`**, whatever S-2 returns. The locked corpus is not changed to fix this.

**Proposal (not run, needs its own approval): an R-1 live probe.**
- Texts: 12–18 problems that ask through an unnamed point ("khoảng cách từ trung điểm của SC đến (ABCD)"), half single
  descriptor, plus D1/D2 forms and ambiguous ones that should end `unresolved`.
- Author: preferably the independent paired author. Texts written by the implementer, or the 10 texts of
  `tools/r1_described_point_probe.py`, would be a `LIVE_DEVELOPMENT_PILOT` only: their gold already sits in the repo.
- Attribution: the six R-1 classes of directive §7, by gold reproduction as in the S-2 runner.
- Runner: the S-2 runner hard-codes its strata and pilot name, so it needs a small generalization first (scripts only,
  with review), then a new template.
- Cost: at most 18 requests at about USD 0.0244 each, about USD 0.44; proposed cap USD 1.0.

## 5. Migration and production gates (directive §11)

The ledger states are unchanged, and the code still matches them:
- PROVED: D-01, D-03, D-05, D-06, D-09; D-02 and D-12 offline.
- PROVED for preview only: D-07, D-08.
- OPEN: D-10, frontend-owned. Presentation and manual QA belong to a separate frontend session.
- BLOCKED: D-04, D-11, D-13, which need a new held-out set and the live paired run.
- GATE-13, 15, 16 and 20 are `NOT_STARTED`: canary, held-out, tokens and latency, and a user study, all live or human.

No status moves without live evidence. `LLM_ONLY` stays the default, nothing is retired, and `CACHE_VERSION` is not
bumped (no prompt or routing change).

| label | state | evidence |
|---|---|---|
| `OFFLINE_BACKEND_READY` | yes, for candidate `0fe38a29` | Full T3 `full-t3-0fe38a29.json`; `--verify` match |
| `LIVE_EVALUATION_PASS` | not measured | no approval |
| `INTEGRATION_READY` | no | D-10 frontend, GATE-13/15/20, Owner merge GO |
| `PRODUCTION_READY` | no | D-04, D-11, D-13, GATE-16 need live data |

## 6. Owner gate after this continuation

See the fourteenth-continuation addendum in `owner-go-request.md`: the re-issued S-2 template blob and command, the
paired GO (independent author, `heldout-authoring/`), the optional R-1 probe, S-1, D1/D2, P-1..P-3 and integration.

## 7. Independent review

Fresh-context reviewer. Scope: live-run harness readiness and the S-2 R-1 coverage claim. It does not cover product or
production readiness.

**Round 1 (`fe8d0aa6`): `NOT_READY`.** 0 BLOCKER, 1 MAJOR, 4 MINOR, 3 NIT.
- The MAJOR was the stale template and addendum. They were re-issued after the last byte change (§3).
- The two code MINORs were fixed with RED/GREEN tests (§3).
- The retry-headroom MINOR is told to the Owner.
- On item 3 the reviewer **agreed**. It read all 36 texts, found no unnamed described-point phrasing, and reproduced
  the scan. It noted regex gaps for future corpora ("Cho …, tính khoảng cách từ trung điểm …", "tâm", "chân đường …"),
  none of which occur in this corpus.

ROUND_2_PENDING
