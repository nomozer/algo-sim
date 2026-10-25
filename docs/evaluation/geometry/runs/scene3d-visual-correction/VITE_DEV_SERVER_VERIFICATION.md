# `npm run dev` verification

Verdict: **PASS** on the candidate checkout. **No EPERM.** The root checkout is still on the old config; see §4.

## 1. The fix is present (not redone)

`88a1b43e` — `frontend/vite.config.ts` `cacheDir: ".vite-cache"`, `.gitignore` `.vite-cache/` — is an ancestor of this
branch. Branch `research/scene3d-visual-correction` was created from `main` `9978e512` and fast-forwarded to
`fe5f40b7`, which contains `88a1b43e`. Nothing was re-applied. The old Codex-owned root `frontend/node_modules/.vite`
was not deleted, no ACL was changed, `node_modules` was not removed, and no process of another agent was stopped.

## 2. Acceptance (`verification/vite-dev-server/`)

Where it ran:

| Item | Value |
|---|---|
| Checkout | `.superpowers/worktrees/svc-cand` at freeze `c84e8620`; clean, detached |
| Owner of the checkout and its `frontend/.vite-cache` | `Bunny` (the cache was created by this checkout's own T3) |
| Harness | `dev-server-acceptance.mjs`, the integration run's harness with one change: the port is a parameter |
| Port | 3171, because port 3000 is held by another agent's Vite (PID 19484, not ours) |
| Port mechanism | `npm run dev -- --port 3171`: same `vite.config.ts`, `cacheDir` and `strictPort`; only the port differs |

Each round:
1. spawns `npm run dev`;
2. loads the app in Chrome;
3. appends a comment to `src/styles/global.css` and waits for the browser's `[vite] hot updated`;
4. restores the file byte for byte;
5. kills only the process tree it spawned.

| Round | Args | Ready | App rendered | HMR | EPERM |
|---|---|---|---|---|---|
| start-1 | — | 747 ms | yes | `[vite] hot updated: /src/styles/global.css` | no |
| start-2 (restart) | — | 733 ms | yes | same | no |
| force-reoptimise | `--force` | 1100 ms | yes | same | no |

- **Outcome:** `pass: true`. CSS restored byte-identical, worktree clean afterwards, port released.
- **Exit codes:** each round exits 1 because of the harness's own `taskkill /F`; this is expected.
- **Plain `npm run dev` on the busy port 3000** (`plain-npm-run-dev-port-3000.log`): Vite exits with
  `Error: Port 3000 is already in use`. That is the intended `strictPort` behaviour (W4B-2D: fail loudly rather than
  silently serving on another port), and it printed 0 EPERM lines.
- **Typecheck and build:** `npm run build` (`tsc -b` + `vite build`) passes inside Full T3 at `c84e8620`, and as a
  standalone build before the official suite. A no-emit `tsc` on both tsconfigs gives 0 errors on the working tree.

## 3. A new trap found (not a regression of the fix)

In Codex's worktree (`.superpowers/worktrees/scene3d-visual-correction`), both `frontend/.vite-cache` and
`frontend/dist` are owned by `CodexSandboxOffline`. A per-checkout `cacheDir` fixes sharing *between* checkouts. It
cannot help when two Windows accounts use the *same* checkout. That is why build, dev-server acceptance and T3 ran in
the Bunny-owned candidate worktree. The Codex-owned folders were left untouched.

## 4. Still open

The root checkout (`research/hybrid-wave3a-volume-reasoning`, which holds uncommitted user work) still has the old
`vite.config.ts`. `npm run dev` there keeps failing until `88a1b43e` reaches that branch. The root checkout was not
touched.
