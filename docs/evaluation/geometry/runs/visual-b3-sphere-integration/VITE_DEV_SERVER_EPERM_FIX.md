# `npm run dev` — Vite EPERM fix

Owner requirement "FIX `npm run dev` / VITE EPERM", 2026-10-25. Candidate branch `integration/visual-b3-sphere-candidate`,
fix commit `88a1b43e`.

## Symptom

`EPERM: operation not permitted, unlink frontend/node_modules/.vite/deps/chunk-HJPS0Q44.js` (as reported; the file
on disk is `chunk-HUPSOQ44.js`).

## Diagnosis (evidence, not assumption)

| Check | Observation |
|---|---|
| Owner of `frontend/node_modules/.vite/deps` and its chunks (root checkout) | `DESKTOP-SCQFJL8\CodexSandboxOffline`, created 2026-10-24 12:22 |
| ACL for the interactive user | `Bunny` gets only `BUILTIN\Users: Write, ReadAndExecute` — **no Delete** |
| Processes holding the folder | none: no `vite`/`node`/`esbuild` process alive besides unrelated MCP tools |
| Why the root cache is shared | the worktrees' `frontend/node_modules` are junctions, and the Codex clones' are symlinks, to the root install; Vite's default `cacheDir` is `<root>/node_modules/.vite`, so every checkout writes the same folder |
| Reproduction (RED) | `npm run dev` in the candidate worktree (junction to the same folder): "Re-optimizing dependencies because vite config has changed" → `Error: EPERM … unlink …\node_modules\.vite\deps\chunk-5WRI5ZAA.js`, **exit 1** |

Root cause: an **ACL conflict, not a lock**. One shared mutable cache inside a shared `node_modules` was populated by
another Windows account (the Codex sandbox). The interactive user can create files there but not delete the sandbox's
files. Vite needs to delete them whenever it re-optimises dependencies.

## Fix

`frontend/vite.config.ts`: `cacheDir: ".vite-cache"` (resolved against `frontend/`), with the reason in a comment.
`.gitignore`: `.vite-cache/`. Each checkout (root, every worktree, every clone) has its own `frontend/`, so each gets
its own cache owned by whoever runs it. `node_modules` stays shared and read-mostly. Vitest's result cache moves to
the same per-checkout folder.

Not done, on purpose:
- the Codex-owned `node_modules/.vite` was not deleted or re-permissioned (no `takeown`/`icacls`, no forced delete);
- `node_modules` was not removed;
- no process of another agent was killed;
- no backend `CACHE_VERSION` change.

## Acceptance (`verification/vite-dev-server/`)

Harness `dev-server-acceptance.mjs`. Each round spawns `npm run dev` and waits for "ready". It loads the app in
Chrome, which triggers dependency optimisation. It appends a comment to `src/styles/global.css` and waits for the
browser console "[vite] hot updated", then restores the file byte-for-byte. Finally it stops only its own process
tree (`taskkill /T` on the PID it spawned).

**Result at `88a1b43e` (clean tree): PASS** — `verification/vite-dev-server/acceptance-88a1b43e.json`, CSS restored byte-identical: True.

| Round | Ready after spawn | App rendered | Hot reload | EPERM | Exit |
|---|---|---|---|---|---|
| start-1 | 877 ms | yes | `[vite] hot updated: /src/styles/global.css` | NONE | 1 (our taskkill) |
| start-2 | 878 ms | yes | `[vite] hot updated: /src/styles/global.css` | NONE | 1 (our taskkill) |
| force-reoptimise | 880 ms | yes | `[vite] hot updated: /src/styles/global.css` | NONE | 1 (our taskkill) |

`force-reoptimise` logs "Forced re-optimization of dependencies": Vite deleted and rebuilt its cache without EPERM. The exit code 1 of every round is `taskkill /F` stopping the server we spawned; Vite did not exit on its own.

The same three rounds also passed while a second Vite server (private config, port 3142, its own cache) was running; that server kept answering 200 and logged no EPERM (`acceptance-with-second-vite-server.json`). Port 3000 keeps `strictPort`: a busy 3000 still fails loudly by design.

RED before the fix: `verification/vite-dev-server/red-npm-run-dev.log` (exit 1, EPERM unlink).

## Effect on the candidate

`frontend/vite.config.ts` and `.gitignore` are outside `PRODUCT_PATHS` (`backend/app`, `frontend/src`) and outside
the browser-evidence `SOURCE_PATHS`. Product commit `9ced3d27`, measured hash `ee474c81…` and the freeze `ddb1a4be`
are unchanged (`--verify` matches). Browser evidence is not stale. Vitest and the build read this config, so Full T3
was re-run.

**Full T3 PASS at `88a1b43e`**: pytest 11923 passed, vitest 80 files / 1359, typecheck + build, demo, crash surface; tree clean before and after; freeze `--verify` matches (`verification/full-t3/integration-88a1b43e/receipt.json`).

## Still ACL-locked (left untouched)

- root `frontend/node_modules/.vite/` (deps and vitest, owner `CodexSandboxOffline`). Harmless once every checkout
  uses `.vite-cache`. **The root checkout itself is on `research/hybrid-wave3a-volume-reasoning` with the old
  `vite.config.ts`, so `npm run dev` in the root keeps failing until this commit reaches that branch** (merge of the
  candidate, or cherry-pick of `88a1b43e`). Until then, run the dev server from the candidate worktree.
- Codex clone `.superpowers/workspaces/visual-closure-hybrid-readiness/frontend/dist/`.
- root `.superpowers/t3-closure-final/`, `.superpowers/t3-closure-temp/`.
