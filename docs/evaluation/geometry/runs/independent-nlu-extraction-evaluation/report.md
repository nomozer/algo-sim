# Independent NLU extraction evaluation — pre-live checkpoint

2026-10-17 · branch `research/independent-nlu-extraction-evaluation` from `main` `76dca142` · no product change ·
candidate `57c7f5db…` MATCH · `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid NO-GO · **LIVE_NOT_AUTHORIZED, 0 model calls**.
Protocol: [`preregistration.md`](preregistration.md). Approval request: [`approval-request.md`](approval-request.md).

## A. Provider, model, prompt, schema

Route D branch B: `app/ai/fact_extraction.py` builds one Gemini `generateContent` request (REST v1beta, key in header via
`function_calling.live_transport`, one attempt), structured JSON output with `responseSchema` = `TypedFact[]`,
temperature 0, `maxOutputTokens` 8192 shared with default thinking (no `thinkingConfig`). Model id `gemini-2.5-flash`
(API id; not deprecated on 2026-10-17). Surface fingerprint `485d3834…` unchanged. Branch B had **never** been run live
before this run (`audit/extraction-architecture.md` §8).

## B. Corpus

60 Vietnamese cases written by a subagent with no repository access (`inputs/corpus-authoring/AUTHORING_BRIEF.md`,
verbatim): dev 16 (14 structures), locked 44 (40 structures). Groups locked A 8 · B 9 · C 5 · D 8 · E 6 · F 8;
multi-request 12 by annotation (10 by gold request facts). Minimal pairs L09/L10, L11/L12, L13/L14, L15/L16 are pairs, not
independent items. Overlap with existing repository texts is published in the preregistration (max D10 0.988, L40 0.943);
the LLM prompt carries no examples, so the wordings are unseen by the LLM.

## C. Oracle and annotation independence

Blind author's own `fractions` oracle: 56 values in 43 cases + 12 structural checks; a second read-only agent recomputed
44 values with its own coordinates: 0 mismatches. Labels: **INDEPENDENT_AGENT_AUTHORED_NOT_HUMAN_VALIDATED**. Gold Typed
Facts (319): **IMPLEMENTER_AUTHORED**, faithful to the product prompt rules; authoring and audit amendments before the lock
are logged in `inputs/gold_authoring_log.md`. No human validation exists.

## D. Harness gates (0 calls)

`backend/scripts/run_nlu_extraction_evaluation.py`, reusing the A/B pilot's budget/redaction/persistence helpers.
`tests/geometry/test_nlu_extraction_evaluation.py`: 21 tests — no network in REPLAY, single failure recorded and run
continues, 3 consecutive failures stop, 400/401/403/429 stop, caps refuse before sending, secret never reaches disk,
model-version pin, resume never re-sends, pending request blocks resume, persistence failure stops, approval identity
required, changed inputs refused, scorer catches unsafe/over/partial/wrong-object serving, NO_PARSE, malformed facts,
equivalent encodings, pilot gate, decision rule, locked hashes and gold outcomes. Fault injection: 7 mutants, 6 killed; the
surviving one (removing the first redaction) is equivalent — the second redaction and the byte scan still stop the run.
Receipts: `results/gold/`, `results/replay-pilot/` (gate `CONTINUE_TO_LOCKED`), `results/replay-locked/`
(`NOT_A_MEASUREMENT_FAKE_PROVIDER`).

## E. Live

Not approved, not run: 0 requests, 0 tokens, USD 0. Requested: ≤ 76 requests, 0 retries, ≤ 1.493M accounted tokens,
≤ USD 1.83 (expected ≈ 0.85–1.20).

## F. Accuracy per layer

Live intent/entity/goal/premise accuracy: **NOT_MEASURED**. Deterministic ceiling with gold facts (locked): 7
`CORRECT_COMPLETE` + 1 `CORRECT_PART_FLAGGED`, 23 `FALSE_REFUSAL_CAPABILITY_GAP`, 13 `SAFE_REFUSAL`, 0 unsafe.

## G. Where failures come from (gold arm, offline)

- **Source Grounding false refusals of faithful extractions:** unlabelled base "đáy là hình vuông/chữ nhật" (9 cases,
  `OBJECT_NOT_IN_QUOTE`; no quote variant helps); "dài bao nhiêu" (`PREDICATE_NOT_IN_QUOTE`); "… thì đoạn AC' bằng mấy"
  (`CONDITIONAL_CLAUSE`); "tính cos²", bare "Tính BD'" (`NOT_ASKED_IN_SOURCE`); "dựng hình chiếu …, gọi điểm đó là H"
  and an unnamed foot (`SOURCE_OBJECT_MISMATCH`); "suy ra"; `QUESTION_LOCAL_GIVEN_UNVERIFIED` (L20/L28, cause not
  diagnosed).
- **Planner/Registry capability:** centroid, line–line angle, trirectangular tetrahedron, intersection line without
  dimensions, right-trapezoid/parallelogram bases.
- **Schema gaps (correctly `unsupported`):** distance to a segment, squared length, face centre, construct/explain,
  interaction, optimisation, context references.
- **Prompt/gate conflict:** prompt rule 7 (three labels per plane) vs the gate's refusal of a three-label `(ABCD)` (L39).
- Scene3D: not reached by this measurement beyond served cases; no rendering claim.

## H. Valid wordings still refused

All of G's grounding list; these are reported as findings, not fixed here (fixing them is a product change and would
need its own wave and a fresh held-out set).

## I. New false serves in live

Not measured. Offline gold arm: 0 unsafe rows.

## J. Prompt / schema / product changes

None. Product, prompt, schema, Registry, Planner, Engine untouched; only the evaluation runner, its test, run documents
and one allow-listed next-action name in the docs audit.

## K. Review, gates, candidate, Git

Audits: extraction architecture (Agent 2) and evaluation (Agent 3, NOT_READY → every BLOCKER/IMPORTANT finding fixed or
dispositioned, `audit/evaluation-audit.md`). Tests: new 21 + A/B runner 80 + docs gate, candidate `--verify` MATCH. T3 not
required (no product or frontend change). Git: checkpoint commit on the research branch; no merge or push before the
live decision and a final integration decision.

## L. Before Hybrid could become a product candidate

Live extraction measured with P1 PASS and P2 YES on a locked set; human validation of labels; the grounding false
refusals of G fixed in a separate wave and re-measured on fresh data; capability gaps decided against the capability
matrix; browser/Scene3D acceptance for served route-D cases; an explicit enablement decision. None is met yet.

## M. Next research step

The owner's live GO for this locked protocol. Independently of it, the offline data already shows that the largest
blocker for these wordings is Source Grounding wording coverage (unlabelled base, interrogative forms), ahead of new
goal schema or G16; that ranking is provisional until extraction accuracy is measured.

## Environment residuals

`.superpowers/worktrees/goal-bounded`, `goal-fixed`, `semantic-grounding-base-20261017` (deregistered; every non-cache
file equals a git blob and the main checkout) and `backend/.tmp/pytest-05045731…` are owned by `CodexSandboxOffline`;
`BUILTIN\Users` lacks Delete, normal-user removal failed with `UnauthorizedAccessException`; no ACL change attempted.
Owner action in an elevated PowerShell: `Remove-Item -LiteralPath <path> -Recurse -Force` for each path. A worktree
`scene3d-educational-finalization` created outside this session is untouched.
