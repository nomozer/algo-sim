# Codex → Claude takeover checkpoint

Authorization `GO_CLAUDE_CONTINUE_CODEX_VISUAL_HYBRID_B3_LOCAL_ONLY`, 2026-10-25. Codex stopped on a usage limit
while Full T3 of the visual closure candidate was being diagnosed. This file records what was found and what
was preserved **before** any new change was made.

## Where Codex was working

Codex did not work in a linked worktree. Its checkout is a separate clone owned by the Windows user
`CodexSandboxOffline` (Git reports "dubious ownership" to user `Bunny`):

| Item | Value |
|---|---|
| Codex clone | `.superpowers/workspaces/visual-closure-hybrid-readiness` (git dir inside; `objects/info/alternates` → root object store) |
| Branch | `research/visual-closure-hybrid-readiness` |
| HEAD | `c84392c15dbd08e4a59a6083ace17b577b8b2cb7` (detached at the time of the stop) |
| Commits on top of `1a4a0b93` | `956b77f8` fix(scene3d) F1/F2 · `9dd47b5d` docs RED/GREEN · `95303040` freeze closure candidate · `53fe3d25` fix(scene3d) formula regions, hover, clean spheres (**product**) · `c84392c1` eval freeze final product |
| Tracked changes (staged / unstaged / untracked) | **0 / 0 / 0** — `git status --porcelain=v1 -uall` empty |
| Clean measurement clone Codex created at 08:35 | `.superpowers/verify-visual-closure` (owner Bunny, alternates → Codex clone objects, `frontend/node_modules` symlink → root install, no `dist`) |

Read with a per-command `safe.directory` (`git -c safe.directory=<clone>` or `GIT_CONFIG_COUNT` env). No global Git
trust and no ACL was changed.

The "19 files, +678/−15" shown in the Codex UI does not correspond to any tracked diff: there were no uncommitted
tracked edits. The files Codex was editing in its last hour are **ignored scratch** under the clone's
`.superpowers/` (29 `.mjs/.py/.md` files modified after 07:30, among them the named
`official-playwright.mjs`, `run-t3.py`, `section-role-probe.mjs`, eight draft reports, `prepare_package.py`,
`finalize_package.py`, `SESSION_PROGRESS.md`).

## Preservation performed

1. **Commits:** `git fetch <codex clone> research/visual-closure-hybrid-readiness:refs/heads/research/visual-closure-hybrid-readiness`
   in the root repository. The five Codex commits now exist in the root object store under that branch name
   (`c84392c1`). The root working tree was not touched (status before/after: the same 19 modified + 8 untracked
   paths that belong to the root owner).
2. **Ignored evidence:** all 1161 ignored files of the Codex clone, excluding Chrome profiles, Vite/Playwright caches,
   `node_modules`, `__pycache__`, `.pytest_cache`, were hashed with SHA-256; 0 read errors. Inventory:
   `takeover/codex-ignored-sha256.txt` (`sha256sum -c` format, run from the Codex clone root; file sha256
`573b136be22b0f455a347b25a1bf933ce6837aab99165acfeb6c863e6d69f4e4`).
   Nothing was moved, rewritten or deleted.
3. **Key artifacts** (sha256, paths relative to the Codex clone):

| File | sha256 |
|---|---|
| `.superpowers/run-t3.py` | `7a07f0db9e8be1481f182d15f4a95cef27c46169cba11d11eefce30844da8c4a` |
| `.superpowers/official-playwright.mjs` | `2e8486c72d9b456f38de1967af185e7adc5c9dd4ad8c7a2bb283c6bebe00fa31` |
| `.superpowers/section-role-probe.mjs` | `7e5f4f49e03e3ad2724ed6ec358c167c05f6ba9b4f9cb313e289b42a326dd442` |
| `.superpowers/closure/SESSION_PROGRESS.md` | `f85eef175ecb788188f89b490d760619b15f972174450b0d380c060c131eae93` |
| `.superpowers/closure/t3-owner-diagnostic/receipt.json` (failed T3) | `b6763ca81a64d7aa6d8ff6e0dc76daaf26ac95cbf40992b1e972d6f6ab82be94` |
| `.superpowers/closure/t3-owner-diagnostic/stdout.log` | `451d04360d2b0214fe1b198b576017d2044898f6f9c4180532bf4b720b20e7f7` |
| `.superpowers/closure/t3-owner-diagnostic/stderr.log` | `d6bf0c25f9e05bd31e3b9a9f0c91ecb3153c6247b8dd41406200a931e0e38f57` |
| `.superpowers/closure/package/visual/official/AGGREGATE_SUITE_RECEIPT.json` | `eeaa090d2218d24f9679dbd5a95bd6e4198e40c902f34f4269cc8dd551640e28` |
| `.superpowers/closure/adapter4-final/receipt.json` | `a106f3d4761f7d9d16e387ca52a2018c08442a29fafd15e0af499437c885ec5f` |
| `.superpowers/closure/refusal-final/refusal-surface.json` | `c60566806d72bc4235b290eaf1c0efc137264799468fc232ec75aeb3f18fca1b` |
| `.superpowers/closure/orbit-final/ORBIT_GATE.json` | `410c6c2e05b3b5ba391f9e9a1d0fd6e13d3ee3be47ea8089f8f54e4d300fc571` |
| `.superpowers/closure/section-role-v2/receipt.json` | `31f9b8927569c71a2912b17dbcaa0ad55f1c4a92fee6c3d9b8549d937793f443` |
| `.superpowers/closure/capability-probe-final.json` | `4157f497a8e22d693160ebaf0b2fae7a18e7b07c6c6a7ee6173c97e7a35ee255` |
| `.superpowers/closure/catalog-audit.json` | `7f4bdfb06c4b5615a2497f0eb3e0d86043e711b8bf5f5508cb7a5cd161690c82` |

## Objects Claude cannot read or delete (left as is)

| Object | Owner / state | Content |
|---|---|---|
| root `.superpowers/t3-closure-final/`, `.superpowers/t3-closure-temp/` | sandbox ACL, `Permission denied` on list | pytest `--basetemp` of earlier Codex T3 attempts |
| Codex clone `frontend/dist/assets/` | sandbox ACL; files readable, directory not removable by Bunny | stale production build — the cause of failure B |
| `hybrid-visual-candidate/backend/.pytest_cache/`, root `backend/.tmp/pytest-0504…/` | unreadable | test caches |

No `takeown`, `icacls`, forced delete, `git clean`, reset, restore or forced checkout was run.

## Processes found

| PID | Owner | Process | Action |
|---|---|---|---|
| 11120 / 2796 | CodexSandboxOffline | Vite dev `:3129` + esbuild (Codex private config) | left running — not Claude's, ownership not transferable |
| 10496 / 10308 | CodexSandboxOffline | `vite preview :4179` + esbuild | left running |
| 4900, 13520, Chrome tree | Bunny | Playwright MCP / user Chrome | not related, untouched |

No T3 or browser suite of Codex was still running; no process used `verify-visual-closure`.

## Other checkouts inspected, not modified

Root `D:/Documents/projects/algo-sim` (`research/hybrid-wave3a-volume-reasoning` @ `fe9f5554`, owner's dirty tree);
`.superpowers/worktrees/hybrid-visual-candidate` (`integration/hybrid-visual-candidate` @ `1a4a0b93`, clean);
`.superpowers/worktrees/visual-hybrid-integration` (detached `13d28b84`, dirty with an older session's untracked
evidence and one modified script). `main` = `9978e512`.

## Continuation point

Codex's last instruction to itself (`SESSION_PROGRESS.md`): wait for T3 `t3-owner-diagnostic`, fill the handoff
placeholders, package the run, update the indexes, commit an allowlist. That T3 finished at 01:32 UTC with
`FULL_PRODUCT_GATE_FAIL` (see `T3_FAILURE_ROOT_CAUSE_AND_RECOVERY.md`). Claude continued from exactly there.
