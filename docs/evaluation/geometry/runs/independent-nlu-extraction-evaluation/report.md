# Independent NLU extraction evaluation — baseline report

2026-10-17 · branch `research/independent-nlu-extraction-evaluation` from `main` `76dca142` · no product change ·
candidate `57c7f5db…` MATCH · `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid NO-GO. Protocol locked at `6255a743`
([`preregistration.md`](preregistration.md)); live pilot (`a9724519`) and live locked run under two separate owner GOs
(`approval-receipt.json`). Locked analysis: [`results/live-locked/analysis.md`](results/live-locked/analysis.md);
pilot: [`results/live-pilot/analysis.md`](results/live-pilot/analysis.md); review: [`review.md`](review.md).

**Baseline result (locked, 44 items):** preregistered answer **UNSAFE** (frozen scorer: 1 `WRONG_SERVED`); that row is
a verified scorer artifact (L01 served the oracle value), and the correction beside it gives **P1 PASS, P2 NO**.
Goal+entity agreement on expressible requests 24/45 (CI95 0.38–0.68) frozen, 27/45 (0.44–0.74) corrected — below the
preregistered 0.85 either way. 2 of 44 rows served correctly (gold facts: 8). Cost: 76 live requests, est. USD 0.299.

## A. Provider, model, prompt, schema

Route D branch B: `app/ai/fact_extraction.py` builds one Gemini `generateContent` request (REST v1beta, key in header via
`function_calling.live_transport`, one attempt), structured JSON with `responseSchema` = `TypedFact[]`, temperature 0,
`maxOutputTokens` 8192 shared with default thinking. Model id `gemini-2.5-flash` (API id; every response reported it).
Surface fingerprint `485d3834…` unchanged. Branch B had never run live before this run.

## B. Corpus

60 Vietnamese cases by a subagent with no repository access (`inputs/corpus-authoring/AUTHORING_BRIEF.md`, verbatim):
dev 16 (14 structures), locked 44 (40 structures; groups A 8 · B 9 · C 5 · D 8 · E 6 · F 8; 12 multi-request by
annotation, 11 with ≥ 2 gold requests). Minimal pairs L09/L10, L11/L12, L13/L14, L15/L16. Wordings not shown in the
prompt; overlap with repository fixtures published in the preregistration.

## C. Oracle and annotation independence

Blind author's `fractions` oracle (56 values) re-checked independently on 44 values: 0 mismatches. Labels
**INDEPENDENT_AGENT_AUTHORED_NOT_HUMAN_VALIDATED**; gold Typed Facts (319) **IMPLEMENTER_AUTHORED**, amendments before the
lock logged. No human validation.

## D. Harness gates

Runner `backend/scripts/run_nlu_extraction_evaluation.py` (reuses the A/B pilot's budget/redaction/persistence helpers),
21 tests, 7 injected faults (6 killed, 1 equivalent), two pre-lock audits (`audit/`), GOLD + REPLAY receipts at 0 calls.
Both live runs completed without a stop rule; the frozen score re-scores byte-identically.

## E. Live execution

| | pilot (dev 16 × 2) | locked (44 × 1) |
|---|---|---|
| requests / retries / stops | 32 / 0 / none | 44 / 0 / none |
| input / output / thinking tokens | 25,106 / 22,074 / 29,762 | 34,466 / 25,468 / 35,166 |
| median latency | 7.0 s | 5.55 s |
| est. USD (list price; billing UNKNOWN) | 0.137 | 0.162 |
| truncated | 1 (D05 s2) | 1 (L12) |

## F. Accuracy per layer (locked; frozen → correction)

Intent 42/57 · goal+entity 24/57 → 27/57 (expressible 24/45 → 27/45) · premise recall 139/165, precision 142/182 ·
multi-goal 4/11 · unsupported flagged 0/12 (1/12 in substance) with 6 approximated · invented labels 3 rows · case
extraction correct 7/43 → 9/43. End to end: correct served 1 → 2, wrong served 1 → 0, safe refusals 13 (= always-refuse
baseline), capability/grounding/schema refusals 22, extraction-caused refusals 6, no-parse 1. Gold facts on the same
texts: 8 served, 0 unsafe.

## G. Where failures come from (locked, `results/live-locked/layer_rows.json`)

- **Semantic extraction:** 34 incorrect extractions — 30 stopped at planner input (`SCHEMA_INVALID`, `UNKNOWN_SOLID`,
  `FACT_INCOMPLETE`, `AMBIGUOUS_FACT`, and L19's request without operands), 3 at Source Grounding, 1 flagged unsupported;
  1 unparsed. Main error types: request operands omitted (14 rows), measure without its solid (14), out-of-schema requests
  approximated (6), invented labels (3). 6 of the 8 gold-servable cases lost here.
- **Source Grounding:** 5 correct extractions refused as the gold facts are (L02 "dài bao nhiêu", L03 "… thì … bằng mấy",
  L13 "Tính cos²", L23, L27 "Tính BD'"); 1 hallucinated label stopped (L22). Gold arm: 18 grounding refusals, including the
  unlabelled base "đáy là hình vuông" (9 cases across splits).
- **Planner / Engine:** 0 live stops; gold-arm capability gaps L17 (no dimensions), L19 (centroid), L29 (line–line angle);
  L40/L44 engine stops are correct refusals.
- **Schema:** 12 locked requests without a schema form; refusing them is correct.
- **Prompt/gate conflict:** prompt rule 7 (three labels per plane) vs the gate refusing a three-label `(ABCD)` (L39).
- **Scene3D:** reached only by served rows; no rendering claim.

## H. Valid wordings still refused

By Source Grounding: unlabelled base ("đáy là hình vuông/chữ nhật"), "dài bao nhiêu", "… thì … bằng mấy", "tính cos²",
bare "Tính BD'", "dựng hình chiếu …, gọi điểm đó là H", unnamed foot of a perpendicular, "suy ra", and two
`QUESTION_LOCAL_GIVEN_UNVERIFIED` cases. Not fixed here (product change, own wave, fresh held-out data).

## I. New false serves in live

Frozen scorer: 1 (L01); verified as a scorer artifact — the served value equals the oracle for the asked object. Real
wrong serves: 0 in pilot (0/32) and locked (0/44). Not a bound beyond these items.

## J. Prompt / schema / product changes

None. Product, prompt, schema, Registry, Planner, Engine untouched; only the evaluation runner, its test, run documents,
a correction script and one allow-listed next-action name in the docs audit.

## K. Review, gates, candidate, Git

Pre-lock audits (Agent 2 architecture; Agent 3 evaluation, NOT_READY → fixed). Post-run review (Agent 4):
`BASELINE_EVIDENCE_NEEDS_FIXES`, all text/receipt fixes applied (`review.md`). Tests: harness 21 + docs gate; candidate
`--verify` MATCH; T3 not required (no product or frontend change). Git: research branch, not merged or pushed.

## L. Before Hybrid could become a product candidate

P1 PASS and P2 YES on a fresh locked set with a scorer that judges served values independently of pairing; human
validation of labels; the extraction failures of G reduced (operands, solids, `unsupported`); the grounding false
refusals of H fixed in a separate wave; the capability gaps decided against the capability matrix; Scene3D acceptance for
served route-D cases; an explicit enablement decision. None is met.

## M. Next research step (from these numbers)

1. **Semantic Extraction first.** It loses 30/44 rows before grounding and 6/8 of the servable ones; the specific
   failures (operands omitted, measure without solid, no `unsupported`, invented names) are prompt/schema-level and
   measurable on a fresh corpus. Needs its own approval (prompt/schema surface change ⇒ cache decision, re-measure).
2. **Source Grounding wording coverage second** (H): it blocks correct extractions and the gold facts alike.
3. **Goal schema / G16 later:** the 12 out-of-schema requests and 3 capability gaps matter only once extraction and
   grounding let servable rows through.
Re-using these 44 items after tuning is not held-out evidence; the next evaluation needs new items.

## Environment residuals

`.superpowers/worktrees/goal-bounded`, `goal-fixed`, `semantic-grounding-base-20261017` (deregistered; every non-cache
file equals a git blob) and `backend/.tmp/pytest-05045731…` are owned by `CodexSandboxOffline`; `BUILTIN\Users` lacks
Delete; no ACL change attempted. Owner action (elevated PowerShell): `Remove-Item -LiteralPath <path> -Recurse -Force`.
The worktree `scene3d-educational-finalization`, created outside this session, is untouched.
