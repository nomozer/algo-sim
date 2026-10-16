# Generalized Goal Entry Implementation Plan

> Native execution by main agent; independent read-only reviewers. User request supplies the specification and authorizes implementation without a separate plan approval.

**Goal:** Resolve a non-distance semantic length goal through Registry effects, including an unnamed described operand.
**Architecture:** Reuse bounded `_EffectResolver`, call templates and effect-chain certificates. Multiple mathematical meanings of `ask_length` require an additional internal contract, without changing its provider declaration. The engine independently checks the descriptor and squared point–point distance.
**Tech Stack:** Python 3.12/Pydantic/Fraction, existing exact geometry IR, Scene3D, Playwright.

## Preflight

- Active branch: `research/generalized-goal-entry`; start HEAD `96569792d32ee0ceef007b8396264fd1a661858d`.
- Working tree at entry: only untracked `frontend/public/`; protected, no contents read or changed.
- Milestone: Function Discovery research, product `cfa27baa`, candidate `093359c2…`, inherited detached T3 `e6c5b0f1`.
- Classification: CORE; thesis relevance: verified composition beyond distance goals.
- Dependencies: main `2a3c0787` → Result Binding `f83b4ed1` → Scene3D `8c24cb52` → Function Discovery `96569792`.
- Source of truth: actual code/tests; historical runs remain byte-preserved.
- Reuse: `PlanningContract`, `PlanningTerm`, `render_call`, `same_call`, `_EffectResolver`, `_kiem_result_binding`, `_MO_TA`, `_Dung.kc2_dich`, `ask_length`, existing benchmark/browser tooling.
- Expected changes: geometry_functions/{registry,planner,engine}.py; new focused test and measurement script; living navigation docs; this run. Provider, TypedFact declarations, Kernel and renderer excluded.
- Contract/cache/history impact: internal planning metadata/admissibility only; schema and provider fingerprints unchanged; cache125; no merge/push/history rewrite.
- Duplicate check: searched symbols, same responsibilities, callers and CODE_INDEX; extend existing modules, no parallel engine/state.
- Dependency-cycle risk: bounded resolver retains cycle refusal; no import direction added.
- Scope-creep risk: source grammar and old Scene3D debt; fix only direct certificate blocker, classify inherited issues.
- Smallest implementation: length described point → named point, generic answer-effect dispatch; existing distance path retained.
- Stops: required provider/TypedFact schema change, new mathematical system, correctness blocker outside bounded scope.

## Global constraints

`DEFAULT_MODE = LLM_ONLY`; Hybrid enablement `NO-GO`; Gemini0; provider/schema untouched; cache125 unless evidence requires otherwise. One run package. No frozen output edits. Missing measurement = NOT_MEASURED. No automated human approval.

## Tasks and verification

- [ ] Register corpus, independent Fraction oracle, success criteria and baseline before product edits. Development only; no new held-out claim.
- [ ] RED tests for non-distance goals, repeated/mixed goals, contract discovery, source/certificate forgery including label metadata, budgets, metamorphic transformations and schema fingerprints.
- [ ] Extend internal contracts and resolver; source certification and direct engine checks. GREEN focused tests and previous corpora; registry ablations separate algorithm from catalog.
- [ ] Export scenes; test Product renderer via offline envelope injection and existing shared Scene3D harness where available. Record environment failures and human review pending.
- [ ] Independent final review, T1/T2; commit product; clean refreeze, append candidate divergence correction; one final T3 in clean detached worktree. Publish report/handoff answering A–J and integration conditions.

## Review focus

Repeated answers must retain distinct ask IDs; unknown/extra target labels must refuse; unread asks cannot disappear; contracts cannot forge mathematical or presentation provenance; all answer effects must avoid memoization of answer calls.
