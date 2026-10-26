# Root consolidation execution plan

Goal: audit and preserve root work, make the root checkout clean on synchronized main, and record intentional research
and worktree dispositions without changing product behavior. Architecture: Git blob identity, exact per-path snapshots,
ordinary non-forced Git operations, local-only recovery data and a documentation-only integration. Spec: Owner's pasted
FINAL ROOT CONSOLIDATION & CLEAN MAIN RESET directive (2026-10-27), AGENTS.md and docs/RULES.md.

- [x] P0: verify current branch, HEAD, status, remote, processes and previous cleanup inventory.
- [x] P1: snapshot all 79 files, binary patches and index; classify each against current/historical main.
- [x] P2/P3: no unique product delta to port; verify baseline main equality, no empty product commit.
- [x] P4: clear each verified path, release old main worktree, switch root non-forcibly to main, delete merged root ref.
- [x] P5: audit all five divergent research refs; preserve intentional valuable work and verify recovery bundle.
- [x] P6: preserve other dirty/hidden data, stop owned servers, perform eligible ordinary removals; quarantine blockers.
- [ ] P7: commit only these provenance documents after review, verify detached candidate and final docs checks, fast-forward
  and normally push main, then record exact post-push identity locally and remove the temporary integration worktree.
- [x] P8: ordered backend handoff only; D-10 first, independent holdout/extraction next; no backend implementation.

Constraints: no force push, rewrite, blanket restore/clean, ACL change, raw evidence mutation, product rollback, live
provider request, new Full T3, Scene3D/sphere redo, approval forgery or production Hybrid enablement. UNKNOWN data stays.
No new product modules, dependencies or test harnesses. Reuse existing docs gate; final test and source identity evidence
must precede success claims. Do not commit backups. User authorization covers this documentation integration and push.
