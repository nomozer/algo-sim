# Schema-Contract v3 continuation plan

Continuation of Claude's interrupted implementation, 2026-10-17. User takeover specification is the execution authority; no new workstream or branch. Default flat extraction, LLM_ONLY and Hybrid NO-GO remain.

## Preflight

- Worktree `.superpowers/worktrees/semantic-extraction-v3`, branch `research/semantic-extraction-v3`, takeover HEAD `cf6a2d234f6483d68c5163658196b4508637d831`.
- No staged/tracked modifications; three untracked held-out author files preserved and hashed in `takeover-inventory.md`.
- Main/origin-main local references `4abc4afbb976babc4740bf22e42dc368a24c1b13`; frontend annotation changes since branch base must be incorporated before final verification. Remote freshness checked separately before readiness.
- CORE: typed extraction contract; SUPPORTING: independent gold/review, evaluation and verification. No planner/function expansion, frontend edits, live calls, merge/push to main or unrelated cleanup.
- Reuse `TypedFact`, `facts_response_schema`, `parse_response`, `run_fact_route`, scorer /2, frozen evaluator executor, candidate freezer and full-gate. Extend their existing code; no parallel parser/solver.
- Source of truth: user requirements, AGENTS/RULES, actual code/tests, frozen earlier evidence. Model-facing research identity changes; production cache consumers/default surface remain unchanged.
- Risks: mathematical operand completeness, unsupported exits, provider-schema subset, scorer binding, held-out exposure, stale candidate. Dependencies remain evaluation → product, never reverse.
- Stop gates: exact-identity GO LIVE and GO INTEGRATION required; no automatic approval creation.

## Tasks

1. Recover original reviewer/encoder state and preserve initial files (inventory).
2. Complete independent candidate review and missing goal-contract regressions; retain grounding safety fixes; incorporate current main into this research branch only.
3. Complete gold encoding in an isolated agent; independent read-only oracle/gold audit. Do not use held-out content to tune prompt/schema.
4. Reuse old development cases as explicitly exposed diagnostics; fresh 24 held-out cases stay separately labeled. Prepare source requests, oracle, gold, protocol/scorer hashes and preregistration. Lock only after all prerequisites pass.
5. Offline GOLD/replay/schema ablation with no extraction-accuracy claim from fake provider. Preserve historical scorer/evidence bytes.
6. Refreeze candidate, final review on exact diff, clean detached authoritative T3 with backend/frontend/build/demo/crash/docs checks.
7. Publish final report and separate fresh pilot/held-out identities and caps. Keep clean committed checkpoint awaiting human GO; no live/integration.

## Review focus

Incomplete and wrong-target requests; finite segments vs infinite lines; all multi-goal source requests; malformed/provider-truncated output; unsupported required slots; numeric answer for a different object; raw-manifest privacy; stale candidate and approval identity.

## Progress

- Takeover preflight and byte-preserving local backup completed. Old reviewer and gold encoder both ended on session-limit messages, no final verdict/gold output. Independent review and gold completion resumed in clean agent contexts.
