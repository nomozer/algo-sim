# Codex → Claude takeover — W3-F2 Adapter /3 safety recovery

Date 2026-10-29 (Asia/Bangkok). Owner GO `HYBRID_V2_W3_F2_ADAPTER3_SEMANTIC_FALLBACK_SAFETY_HARDENING` (continuation,
Claude takeover). Written read-only, before any product edit.

## 1. Exact state at takeover

- Branch `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`, HEAD
  `6516d5d46379a4d4f251c4fa29e6a16191a79ca6` (Codex added six commits after checkpoint `a318a598`:
  `42fab670` RED prereg, `e067f07b` RED controls, `f7dd5580` terminal refusal + scoped identities, `11816921`
  qualified-containment Bridge repair, `add9c04e` gates/replay evidence, `6516d5d4` new candidate freeze).
  Main `996f114b` unchanged. No merge/push.
- Dirty state: staged diff empty, unstaged diff empty. One untracked file:
  `verification/full-t3/full-t3.log` (0 bytes).
- Detached T3 worktree `.superpowers/worktrees/w3-f2-adapter3-t3` at `6516d5d4`, clean tracked tree; ignored
  `.superpowers/t3-*` temp dirs carry Codex sandbox ACLs (unreadable, left in place). No python/pytest/full-gate
  process is running (process table checked).
- Backup (ignored, outside history): `D:/Documents/projects/algo-sim/.superpowers/backups/w3-f2-codex-takeover-20261029/`
  — git status/HEAD, empty staged/unstaged diffs, the untracked log, Codex `.superpowers/f2` scratch, both Codex
  session transcripts and their decoded reviewer excerpt, with `SHA256SUMS`.

## 2. What actually stopped Codex (from the Codex session transcript, not from inference)

The stop was **not** a Full T3 test failure. T3 started at 11:16:22Z on `6516d5d4`. At 11:16:55Z the separate-context
final reviewer (`/root/adapter3_final_review`) reported a MAJOR; Codex invoked the Owner STOP contract. Its first
abort command threw (two runner processes matched, nothing stopped); the second was rejected by automatic approval
review because the Codex usage limit was hit. The session then ended. The T3 log is empty because the runner writes
through a buffered file handle and was never flushed: **no T3 result of any kind exists; no receipt.json was written.**
`final-safety-gates.json` (A–D PASS) and `verification/pre-freeze-tiers.json` were recorded before the review and are
invalidated for Gate A by the finding below; they stay immutable and are corrected by this layer.

## 3. Latest safety failure — reproduced on HEAD by Claude (0 provider calls)

Probe: Bridge, Adapter /3, Adapter /4 on the supplementary control and on corpus case A3-DEV-02 (genuine
`BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` legacy positive).

| id | input mutation | Bridge | Adapter /3 | Adapter /4 |
|---|---|---|---|---|
| H1 | A3-DEV-02 + `height` premise `solid_id=pyr1`, `args.solid=pyr2` | capability refusal | **SERVED** | n/a (/1 identity) |
| H2a | control volume goal `solid_id=s2`, `target.solid=s1` | OK | **SERVED** | **SERVED** |
| H2b | control volume goal `solid_id=foreign` | OK | **SERVED** | **SERVED** |
| H2c | A3-DEV-02 volume goal `solid_id=pyr2` or `foreign`, `target.solid=pyr1` | capability refusal | **SERVED** | n/a |
| H3 | control volume goal `solid_id=s1`, `target.solid=T.ABCD` (notation of s2) | capability refusal | **SERVED** | REFUSED (capability code) |

Answers are numerically unchanged in these cases, so this is *scope contradiction served*, i.e. fail-open on
provenance (explicit declared solid ignored), not a wrong number. It violates "verified semantic rejection must be
terminal" and Gate A ("foreign-solid premise refused", "semantic refusal never served via fallback").

## 4. Root cause

Proven:
- Adapter /3 reads every solid-valued operand as `inner or scope`: `altitude`/`height` use
  `a.get("solid") or sid`; measurement volume uses `t.get("solid") or sid`. A declared scope is never checked
  against the inner operand, and an unknown declared goal scope is never checked at all. These are the only
  solid-valued operands (`_ARGS_LOI` shape `id`: `height.solid`, `altitude.solid`; goal `target.solid`).
- Bridge: its premise validator `_kiem_pham_vi_tien_de` already refuses H1-type premises, but `_bridge` raises the
  capability refusal `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` (solid loop) before calling it, so on legacy inputs the
  semantic check never runs and Adapter /3's own compile is the only guard. Bridge's volume goal uses
  `target.solid or solid_id` with neither existence nor consistency check (H2a/H2b for Adapter /4 as well).

Not proven / not claimed: the Adapter /3 area-by-section goal ignores a declared goal `solid_id` versus the
section's solid (the Bridge checks it); the RED test below decides whether it is reachable.

## 5. Gate status at takeover

A: **FAIL** (H1–H3). B: PASS as independently adjudicated on `f7dd5580` (not affected: no incidence code involved).
C, D: recorded PASS on `11816921`; must be re-run after any product change. Full T3: **NOT RUN** (aborted, no result).
Candidate freeze `6516d5d4` will be stale after the fix and must be re-frozen.

## 6. Minimal RED → GREEN plan

Files: `backend/app/ai/adapter3_simulation.py`, `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`,
`backend/tests/geometry/test_adapter3_fallback_safety.py` (new tests only; no expected value changed).

1. RED: add H1/H2/H3 tests (Adapter /3 real legacy path, Adapter /3 forced-capability path, Bridge, Adapter /4) and
   consistent-scope positives (same solid by id or notation, absent scope) that must keep the exact answer.
2. GREEN: one Bridge helper for "declared scope vs named solid" (the logic already in `_kiem_pham_vi_tien_de`
   lines 117–125, extracted, reused for the volume goal); one Adapter /3 helper with the same rule used at the three
   solid-operand sites (and the section-area goal if RED shows it reachable). Unknown declared scope →
   `UNKNOWN_SOLID_ID`; conflict → `SOURCE_OBJECT_MISMATCH`. No reordering of Bridge capability checks (would make the
   Bridge scope validator judge legacy qualified identities it was not designed for).
3. Mutants: removing either new guard must be caught.
4. Then Gate A–D re-run, full 144-case `POST_FEEDBACK_DEVELOPMENT_REGRESSION` replay, T0–T2, new freeze (separate
   commit), clean detached Full T3 in a new worktree and new output directory, post-freeze verify, independent review.

## 7. Authority and stop conditions

In scope: Adapter /3, Bridge, tests, evidence. Not in scope: kernel/radical, Registry/planner capability, Adapter /4
code, W3-F3/F4/F5, UI/Scene3D, default routing (`LLM_ONLY`), live calls (`ALLOW_LIVE_AI=0`). No merge, push or
cleanup; historical evidence and Wave 3 holdout immutable; new replays labelled
`POST_FEEDBACK_DEVELOPMENT_REGRESSION`. STOP at `NOT_READY` if any gate fails after the fix, if the fix needs a change
outside this scope or a locked expected-outcome change, or if a reviewer finds a new BLOCKER/MAJOR.
