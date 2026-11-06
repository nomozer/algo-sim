# Handoff

Status: **READY_TO_MERGE (squash)** / BLOCKED (merge with history, pending three blob exceptions: 23109136, 28be1ef6,
f4b76988). Not merged, not pushed.
Read `report.md` first.

## Merge, when the Owner authorises it
1. Re-check: `git fetch origin && git rev-parse origin/main` must still be `bb61a804` (else re-run the simulation and T3 on the new base).
2. Squash (recommended): from the main checkout, `git merge --squash integration/axo-hybrid4-reliability`, review `git diff --cached --stat`,
   commit (conventional message, no `Co-Authored-By`), confirm `git rev-parse HEAD^{tree}` equals the integration HEAD tree, run
   `check_publication_safety.py --range bb61a804..HEAD` (expected PASS), then `git push origin main`; verify with `git ls-remote origin main`.
3. Keep `integration/axo-hybrid4-reliability` LOCAL as the evidence archive (its hashes are cited in `docs/EVIDENCE_INDEX.md`); do not
   push it (that would publish blob `23109136`).
4. Deploy: `alembic upgrade head` (revision `e437149641fa`); PostgreSQL run pending.

## Branches / worktrees (inventory 2026-11-07, nothing removed)
Worktrees under `.superpowers/worktrees/`: `axo-hybrid4-integration` (this branch), `axo-pedagogical-integration`
(`integration/axo-pedagogical-construction-hardening`, local `67f780ca` vs remote `a4c60e62`), `axo-performance-baseline`,
`axo-performance-verifier`, `w3-f2-*` (detached), `axo-v27-frontend-integration`, `independent-section-holdout`, and four marked
`prunable` (`s3d-hybrid-v2`, `s3d-hybrid-v2-codex`, `scene3d-visual-correction`, `visual-hybrid-integration`). Many hold untracked
evidence; inventory each (`git status`, untracked files) before removing anything, and never remove old run evidence.

## Next task: streamline Axo toward construction (separate task)
Keep Typed Facts, planner/compiler, exact kernel, verifier, Scene3D contract and the step sequence (the certificates stay the
correctness backbone even when no answer is shown). Candidates to examine there, not here: answer-reveal surfaces already hidden by
the presentation policy, goal summary wording, refusal copy, and docs that still describe answer display.
