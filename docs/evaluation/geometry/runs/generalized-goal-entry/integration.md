# Stacked integration into `main` — 2026-10-16

**Decision:** the user chose "GO: ff + push + dọn" in this session (agent question, one time). This file records the agent's
actions; it is not a user-written approval token.

| item | value |
|---|---|
| `main` / `origin/main` before | `2a3c0787` |
| integrated tip | `bd4d3f59` (fast-forward only, 58 commits, no merge commit, no history rewrite) |
| stack | result binding (`55c657b8` product, `f83b4ed1`) → Scene3D W1–W3 (`8c24cb52`) → Function Discovery (`cfa27baa` product, `96569792`) → Generalized Goal Entry (`193e634a` + `289007a4` product, `bd4d3f59`) |
| candidate | `eaddb56c2d7b8a0a5bfc095c2cd06adef9e5780c3e049d9e48f7ceb825b7a08f` (110 files), `--verify` MATCH on integrated `main` |
| authoritative T3 | clean detached worktree at `5964f875` (`bd4d3f59` adds docs only): `FULL_PRODUCT_GATE_PASS`, `verification/t3-pass.json` |
| gates on integrated `main` | candidate verify MATCH; docs IA/telemetry/identity, goal entry, function discovery, result binding, goal decomposition (mutants), thesis acceptance matrix: 404 passed, 2 xfailed |
| product default | `LLM_ONLY`, `CACHE_VERSION = 125`; route D is not on `/api/analyze` ⇒ Hybrid product enablement stays NO-GO |
| human review | Scene3D W1–W3 reviewed by agents (PASS_WITH_FINDINGS, findings fixed); human visual acceptance NOT_APPROVED |

**Environment incident during the switch to `main`:** 54 files created or rewritten inside the Codex Windows sandbox carry an
ACL granting the user account read + write but not delete (`BUILTIN\Users:(RX,W)`, `CodexSandbox*` groups). `git switch`
could not unlink them; they stayed untracked and blocked the fast-forward. Each was verified identical to its blob in
`bd4d3f59`, staged by explicit path (blob ids equal the target) and the fast-forward then completed without rewriting them.
No ACL was changed by the agent. The same ACL causes the recurring `backend/.tmp/pytest-…: Permission denied` warning.
Fixing it needs an administrator (`icacls … /reset /T` or a take-ownership) — a decision for the machine owner.

**Branches:** local branches wholly contained in `main` and without remote copies are deleted with `git branch -d` after the
push (`research/source-bound-result-planning`, `research/goal-directed-planner-generalization-audit`,
`research/scene3d-visual-parity-audit`, `research/goal-directed-function-discovery`, `research/generalized-goal-entry`;
`research/goal-directed-two-line-plane-section` was already in `main` and deleted earlier). Kept:
`research/scene3d-visual-correctness` (another session's active work, branched from `140ae4ed`), `research/compact-geometry-dsl`
(NO-GO archive), `docs/real-model-e2e-readiness`, `feat/real-model-pilot-tooling` (remote branches with their own evidence).
