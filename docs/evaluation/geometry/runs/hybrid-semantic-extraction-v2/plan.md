# Semantic Extraction v2 Implementation Plan

> Execution: main agent implements inline with executing-plans; independent agents audit and review. User supplied the execution scope and method in the attached specification.

**Goal:** Preserve grounded operands, solid ownership and every source request without adding a solver or inventing facts.
**Architecture:** Keep TypedFact and the deterministic route. Clarify the existing model contract. Score actual served objects independently of extraction pairing.
**Tech stack:** Existing Python/Pydantic/Fraction, pytest, Node product gates; no dependency additions.
**Spec:** User attachment, “HYBRID SEMANTIC EXTRACTION V2 & GROUNDED GOAL COMPLETENESS”, 2026-10-17; contract: `docs/architecture/GROUNDED_GOAL_COMPLETENESS_CONTRACT.md`.

## Preflight

- Active branch: research/hybrid-semantic-extraction-v2; baseline HEAD/main/origin/main/remote bc0445ae4a4376c97af6ef9e1a21fa8fb0f5a3f8 (remote checked).
- Isolated worktree: `.superpowers/worktrees/hybrid-semantic-extraction-v2`; clean at creation. Main checkout untracked `frontend/public/` preserved; Gemini Scene3D worktree excluded.
- Milestone: independent NLU baseline integrated; default LLM_ONLY, cache125, Hybrid NO-GO.
- Classification: CORE extraction; SUPPORTING evaluation, directly serving the geometry thesis.
- Reuse: TypedFact, build_request/facts_response_schema/parse_response, run_fact_route, registry source checks, old harness execution/budget/redaction helpers, candidate freezer and full-gate.
- Source of truth: code/tests, docs/RULES.md, architecture decisions, immutable baseline run and corrections beside it.
- Expected files: fact_extraction.py; bounded registry predicate change if regression establishes it; focused tests; new scorer/evaluation script; run package and canonical indexes.
- Contract/cache/history: no TypedFact migration; B surface changes and new live identity required. Check default cache consumers before deciding version. Historical scorer and evidence bytes preserved.
- Duplicate check: old evaluator combines execution with fact-pairing scoring; reuse execution helpers, add versioned semantic scorer because old published scoring must remain reproducible. No duplicate planner/parser/kernel.
- Dependency cycles: evaluation imports product and existing scripts; product never imports evaluation.
- Scope risk: grammar expansion and capability work; bounded to one already accepted length phrase if safe.
- Smallest sufficient implementation: prompt clarification + independently bound scorer + new frozen corpus/oracle + one keyword compatibility fix.
- Excluded: planner, schema, geometry functions/capability expansion, frontend, default/cache consumers, live requests without GO, integration without GO.
- Stop: genuinely new architecture/schema decision, unsafe acceptance, scope expansion, or exact-identity live/integration approval gates.

## Review focus

Wrong object with equal value; omitted nonnumeric request; unsupported approximation; invented source identity; truncated provider output.

## Tasks

- [x] Audit extraction/provider/schema, baseline evidence/corrections and grounding independently; report A1–A7.
- [ ] Lock new independent-AI corpus, source obligations, gold facts, Fraction oracle, split and preregistration before prompt changes. Run author oracle and audit coverage. Keep heldout out of tuning.
- [ ] RED: scorer tests for correct object with irrelevant slots, wrong equal-valued object, wrong value, missing/extra request, missing bindings and construction evidence. Implement versioned semantic scoring with executed calls; GREEN/adversarial checks. Preserve old evaluator bytes.
- [ ] RED: provider contract and valid “dài bao nhiêu” real-route regression; minimal prompt/keyword changes; GREEN plus hostile modifiers and historical regression.
- [ ] Offline GOLD/REPLAY and extraction mutations; separate prompt-only effects (NOT_MEASURED live) from gate effects. Freeze candidate and new approval identities.
- [ ] Independent whole-change review; fix substantive findings with RED/GREEN. Backend regression, documentation gate, final refreeze, authoritative detached T3 on committed candidate.
- [ ] Publish report A–O, capability/composition handoff and a single next action: separate exact-identity pilot GO. Keep clean committed research branch; no live/merge/push/cleanup of unintegrated branch.

## Takeover (Claude, 2026-10-17)

Codex stopped at 08:05:42Z on `usage_limit_exceeded` (its session log), immediately after its scorer fixes went 22/22
green; nothing had been committed. Worktree and branch reused unchanged (HEAD `bc0445ae` = main = origin/main); all
fourteen untracked files were archived with SHA-256 before any edit; nothing was deleted or reverted. The ACL-locked
`backend/.tmp/*` folders of Codex's sandbox are left in place (ignored, unreadable).

| file (last Codex turn: six files, +736 lines) | state at takeover | continued by Claude |
|---|---|---|
| `backend/scripts/run_semantic_extraction_evaluation.py` (406) | review findings 1–3, SCORE isolation, schedule check patched; unreviewed | polygon cycle, section plane, `capability_gap` fulfilment, rightness derivation, false-refusal split, published-score sanitising + secret scan, LIVE path check first |
| `backend/tests/geometry/test_semantic_extraction_evaluation.py` (169) | 22 green | RED→GREEN for each change above + recorded-L01 receipt |
| `docs/architecture/GROUNDED_GOAL_COMPLETENESS_CONTRACT.md` (15) | complete | kept |
| `plan.md` (43), `preregistration.md` (45) | lock text, not committed | amendments recorded before the lock |
| `inputs/prepare_protocol.py` (58) | already executed (`ALREADY_LOCKED` guard) | kept |

Earlier Codex output kept byte-identical: `corpus.json`, `gold_facts.json`, `oracle.py`, `authoring.md`,
`baseline_prompt.txt`, `baseline_schema.json`, `prelock_corrections.json`, `protocol.json`.

## Decision record

2026-10-17: explicit current request authorizes this research implementation. Canonical architecture policy requires remeasurement of model-facing changes, not a universal extra approval for a prompt-only change. No schema or planner design change is proposed. Live and integration remain separately gated by user instructions.
