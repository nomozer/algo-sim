# Report — Hybrid Semantic Extraction v2 & grounded goal completeness

2026-10-17 · branch `research/hybrid-semantic-extraction-v2` from `main` `bc0445ae` · **LIVE_NOT_AUTHORIZED** (0 model
calls) · default `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid NO-GO. Contract:
[`GROUNDED_GOAL_COMPLETENESS_CONTRACT.md`](../../../../architecture/GROUNDED_GOAL_COMPLETENESS_CONTRACT.md). Protocol:
[`preregistration.md`](preregistration.md) (lock `6ceb2508`, amendments 1–2). Reviews: [`review.md`](review.md).

## 1. Provenance

Codex started the wave (audits, independent corpus, gold, protocol, first scorer) and stopped on its usage limit while
fixing scorer review findings; nothing was committed. Claude continued in the same worktree without discarding any file
(`plan.md` § Takeover: inventory, SHA-256 archive, the six files of Codex's last turn).

| commit | content |
|---|---|
| `6ceb2508` | protocol lock: corpus, gold, oracle, protocol, preregistration, scorer `grounded-source-obligations/2` + tests |
| `fb3f4ee5` | product: prompt v2 draft + `hộp chữ nhật` / `dài bao nhiêu` grounding vocabulary |
| `920527b1` | refreeze (superseded before any measurement) |
| `69fa9be8` | product: whole-change review fixes, article rule (dev01), bare `hình hộp` no longer right |
| `108fc086` | refreeze — candidate `b5406c91…`, 110 files, `--verify` MATCH |
| `c640cd14` | live path loads `backend/.env` like the frozen evaluator; identities and offline receipts produced here |

## 2. Scorer correctness (before any product change)

The frozen scorer judged a served answer through extraction fact pairing; on the locked baseline a harmless slot made
the correct L01 answer `WRONG_SERVED`. Scorer /2 matches each independently annotated source request one-to-one with the
**actually executed call operands**, then the exact Fraction oracle. Every source request counts (constructions,
unsupported, proof, multi-goal). Operand equivalence is decided per role, never by sorting everything: segment
endpoints unordered; a plane is a label set (containment, the engine checks coplanarity of every written label); a
polygon is its vertex cycle (`ACBD` ≠ `ABCD`); a solid is its vertex structure (`OPQR` = the planner's `R.OPQ`);
distance and unsigned angle between two objects are symmetric; projection point/image positional. Refusals split into
`_CAPABILITY_GAP` vs `_EXTRACTION` by the GOLD route on the same product.

Real-receipt regression: the recorded L01 live facts replayed through today's route score `CORRECT_COMPLETE`, a wrong
target with the same receipt `WRONG_SERVED`; the frozen `score.json` still says `WRONG_SERVED` (history untouched).

Raw-output isolation: LIVE output is refused outside git-ignored `.superpowers/` before a provider is built; published
`score.json` carries derived metrics, execution class, identity, usage/latency and the source manifest's row hash, never
model fact/answer ids, non-label strings or the key (secret scan on write). The historical run's committed manifests are
left as they are.

Tests: 61 RED→GREEN/adversarial cases (`test_semantic_extraction_evaluation.py`). Independent review: NOT_READY (2
blockers, 4 important) → LOCK_READY; remaining minors accepted in `review.md`.

## 3. Semantic extraction changes (product)

Root causes from the locked baseline (44 items): requests without operands 14, measures without their solid 14,
out-of-schema requests approximated 6/12, invented labels 3, three-point right angles 4. The audit found the TypedFact
schema already expresses these; the prompt never taught them. **Schema, parser, planner and function declarations are
unchanged** (surface A `7ea511a6…` and declarations `5ceb0f99…` identical; B `485d3834…` → `c4e4392c…`,
[`provider-surfaces.json`](provider-surfaces.json)).

Prompt v2 (rules 1, 5, 7 revised; 11–13 new; 2,518 → 4,080 characters): one fact per source request; question operand
matrix; `solid` for every non-segment measure and volume (ambiguous ownership ⇒ `ambiguous`); two-ray right angles;
written label groups for section/intersection planes, every label for operand planes, three only for `line_ref`
producers (else `unsupported`); unnamed point = `point_kind` + `points`, target in `points_b`; no invented labels or
properties; unsupported requests (finite-segment distance, squared quantities, optimisation, motion, explanation, curved
solids) as `kind = unsupported` with their role, **never approximated**. No corpus sentence is in the prompt (test).

Source Grounding, bounded, each with adversarial negatives: `hộp chữ nhật` names a cuboid (reuses the existing pattern;
bare `hộp` / a rectangle face do not); `dài bao nhiêu` asks a length (`dài 3`, comparisons, other objects refused); a
sentence-initial `Một` before a solid is an article (`một cạnh`, `một nửa`, a new unread premise still refused); a bare
`hình hộp` no longer certifies a right prism — it previously **served AC′ from a possibly oblique box** on `main`.
Remaining wording gaps stay open (`… thì … bằng mấy`, `Tính cos²`, repeated `tính`, `rồi suy ra`, projection wording,
`ba kích thước`).

Architecture boundary unchanged: the LLM extracts typed facts only; the planner chooses registry functions by bounded
search; the exact engine verifies; no template compiler, no coordinates from the model.

## 4. Offline evidence (0 model calls)

Corpus: 36 cases (12 dev / 24 heldout), 20 structure families, 51 source requests, 34 Fraction oracles recomputed
independently (0 mismatches). Labels INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED; 33 pre-lock gold encoding corrections.

| GOLD route (authored facts) | dev before `6ceb2508` | dev after `c640cd14` | heldout before | heldout after |
|---|---:|---:|---:|---:|
| served correct (`CORRECT_COMPLETE`) | 1 | **2** (dev01) | 2 | 2 |
| safe refusal | 5 | 5 | 4 | 4 |
| refused: capability / grounding gap | 6 | 5 | 18 | 18 |
| unsafe (wrong / partial / over / form) · unscorable | 0 · 0 | 0 · 0 | 0 · 0 | 0 · 0 |

Receipts: [`results/offline/`](results/offline/). REPLAY (gold facts as a provider body) equals GOLD for both arms on
both splits — harness wiring only, **not** prompt effectiveness. Agreement metrics are complete on gold (goal 51/51,
operands 25/25, solid 34/34, premises 205/205, multi-goal 14/14), which validates the scorer, not the model.

**Ceiling.** Even with perfect extraction the route serves 4/36 cases. Heldout refusals: `NOT_ASKED_IN_SOURCE` 5,
`OUT_OF_SCOPE` 4, `OBJECT_NOT_IN_QUOTE` 3, `PREDICATE_NOT_IN_QUOTE` 3, `MISSING_DIMENSION` 3, `SOURCE_OBJECT_MISMATCH` 2,
conditional 1, ambiguous 1. Served-answer gains from prompt v2 are bounded by this ceiling; the prompt's measurable
outcome is extraction agreement (operands, solid ownership, unsupported detection, invented labels, multi-goal).

Ablation (offline). *Deterministic validation:* injecting each baseline failure class into the authored facts of all 36
cases (drop operands, drop solid, invented label, three-point right angle, approximated unsupported, dropped later goal;
99 applicable mutations) yields 0 unsafe serves; on the 3 gold-served cases all 8 applicable mutations are refused —
safety comes from the gates, a tiny denominator. *Source Grounding:* the GOLD before/after table above (+1 dev case).
*Schema:* unchanged, no effect claimed. *Prompt:* NOT_MEASURED — needs the paired live arms below. Lower unsafe counts
from refusing everything are not counted as understanding: always-refuse would score 9/36 safe refusals.

Historical: the old 60-case NLU GOLD arm moves one row (L02 refused → refused at a later gate; served 10 → 10),
recorded in [`results/historical-gold-delta.json`](results/historical-gold-delta.json); the old 44 locked items are
diagnostic only, never held-out evidence.

## 5. Live measurement — paired dev pilot (owner GO pilot only)

24 requests (12 dev × baseline/v2), 0 retries, no stop, est. USD 0.123; LOCKED **not run**. Analysis:
[`results/live-pilot-analysis.md`](results/live-pilot-analysis.md). Both arms served 0/12 (GOLD ceiling 2/12), 0 unsafe.
v2 vs baseline: intent proxy 10→13/16, invented-label rows 1→0, parsed 11→12, multi-goal 0→1/4, cost −34 %, max latency
32→13 s; **unchanged** operand correctness 2/8, solid association 3/6, expressible goal/entity 5/11, unsupported 0/1.
The dominant failure persists: question operands land in `value` or are omitted, right angles keep three points. The
flat response schema makes every operand slot optional; a prompt rule alone did not move it. Recommendation: no
held-out run for this prompt; next, a separately approved provider-contract (schema) wave tuned on dev.

## 6. Verification

Backend full suite at the product commit before refreeze: 10,330 passed, only candidate-freeze guards red (expected,
cleared by the refreeze); after the review fixes the geometry suite 8,051 passed with the same guards; targeted grounding
suites 965 passed, 3 xfailed. Docs gate green. **Final Authoritative T3** on a clean detached worktree at `fa6d792e`:
`FULL_PRODUCT_GATE_PASS` — pytest 10,356 passed / 0 failed, vitest 1,072/1,072, typecheck+build PASS, demo 5/5,
crash surface 6/6, candidate `b5406c91…` MATCH after the gate ([`verification/t3.json`](verification/t3.json)).

## 7. Limits

AI-authored labels, not human-validated; heldout is structurally implementer-exposed (aggregate outcomes and one row's
structure seen while fixing the scorer; no text; no product change from heldout). No population or Gemini claim. Prompt
effect unknown until live. Hybrid product enablement, default mode and integration remain separate owner decisions.
