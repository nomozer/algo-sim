# Integration preflight — Session 4A

Date: 2026-10-23 (Asia/Bangkok). Status: **PARTIAL — mechanically compatible, combined acceptance pending**.

## Verified local identities

Authoritative snapshot: `results/receipt-audit-attempt2.json`. Git trees below are SHA-1 object IDs; the measured-system fingerprint is a separate SHA-256 algorithm.

| Ref / role | Commit |
|---|---|
| local main | `f10e6283dd3fd2cfdef189e1bef0ffdecf2be942` |
| local origin/main tracking ref | `43247c9e9375a3dbf2b5223324a58e6f932ca596` |
| original workspace HEAD | `fe9f555437498432427ae6bbd54402cdd59c7eb7` |
| Session 1 final documentation HEAD | `82d3d25540ea643a68bd7877eb1b67a78dfc7134` |
| Session 2 final documentation HEAD | `227d447f5c1ca55a2c4bd68f3c8c583228902cfc` |
| Session 3 final documentation HEAD | `0f7b3a69d0f920a6cc115a7d9e1a89f693137208` |
| Session 3 product | `69bd2fe48be1fd3afa6ce4112ccddda92a07d850` |
| Session 3 successful T3 candidate | `84c729e0b0df7868dfcc0a6e48cac457d7959e92` |

`origin/main` is an ancestor of local main; main is one documentation-only commit ahead. The remote server was not fetched: **remote freshness UNKNOWN**. S1 → S2 → S3 ancestry succeeds. S3 and local main are divergent descendants of `43247c9e…`; neither contains the other. Session 3 is not integrated on main.

Original root has pre-existing untracked run directories, a source-gate failure log and `frontend/public/`; all remain untouched. The snapshot inventories every registered worktree with HEAD, branch/detached state, status and product subtree IDs. Several unrelated worktrees are dirty; none is used as an integration source. Session 1/2 expose untracked verification logs to the collector; Session 3 reports no tracked/untracked changes. Git warns that some pytest-cache directories and the user's global ignore file are unreadable, so the inventory records the visible state rather than claiming a complete scan of inaccessible caches.

Session 4A worktree: `.superpowers/worktrees/hybrid-session4a-readiness`, branch `research/hybrid-session4a-readiness`, created from local main. Verification worktree: `.superpowers/worktrees/hybrid-session4a-s3-verify`, clean detached at `84c729e0…`. No integration merge was performed.

## Product and frontend comparison

| Tree | main | Session 3 candidate |
|---|---|---|
| `backend/app` | `63ce7dfc3032fe9215fec0db5e5e2c006ae5a1c9` | `357afcfae2289cfed286cb47f709c708a6c661cc` |
| `frontend/src` | `0d4b20883c4b5741653579bc9b418ccd3d4db7b8` | `0d4b20883c4b5741653579bc9b418ccd3d4db7b8` |

The newest reachable frontend source commit is `34a57d35` (2026-10-22, section depth/x-ray ordering), preceded by `24e1a9db`, `36dfccef`, `ca84337e`. Main and S3 already contain the same frontend source tree. This says nothing about dirty/untracked UI artifacts, visual acceptance, or compatibility with the new `/4` envelope. No frontend files were copied or merged.

Read-only `git merge-tree BASE main 0f7b3a69` returned exit 0 and no conflict markers. This old three-tree analysis does not construct or test a merged candidate. Its decoded-output digest is recorded in the snapshot. Shared documentation must still be reconciled deliberately; source compatibility is not release authorization.

## Safe integration scope and coordinated tests

The S3-vs-main product diff is ten backend files: `adapter3_simulation.py`, new `adapter4_route.py`, `fact_extraction.py`, `function_route.py`, `hybrid_preview.py`, and geometry-functions `engine.py`, `planner.py`, `registry.py`, `typed_fact_next.py`, new `typed_fact_next_bridge.py`. Import them as a coherent contract/registry/planner/engine stack with their tests, rather than selecting individual files. There are no frontend changes in this diff.

Offline research integration is technically plausible after an owner-selected integration candidate is tested. Required combined checks: default-route import isolation and byte fingerprints; `/1` compatibility and explicitly route-labelled conversion; `/2` schema/gate/closure; preview envelope/taxonomy identity; `/4` to frontend consumer compatibility; cache policy snapshots; regenerate candidate identity for the actual integrated tree and run its required gate. The original workspace's later composite/volume work is a separate source and must not be silently substituted for S3.

Fresh targeted verification at the clean S3 candidate: freeze check MATCH; 154 passed / 1 xfailed across contract V2, contract unification and goal composition. These results cover the pinned S3 source, **not a merged main candidate**. S3's existing full T3 receipt is reused with its original identity; no heavy gate was rerun.

Integration decision: **PARTIAL**. No content conflicts were detected; production isolation, canonical extraction, combined release checks and owner integration authorization remain separate obligations. No merge, push, branch deletion or worktree deletion occurred.

## Inventory collection limitations

`results/receipt-audit.json` is a failed first collection: Python-spawned Git rejected repository ownership and returned 128. Do not use its empty refs/diff or zero conflict count. The successful `receipt-audit-attempt2.json` uses per-command `safe.directory` for this explicit workspace, without global configuration changes. A decoding failure before attempt 2 produced no receipt; decoded merge output uses replacement for non-UTF-8 historical bytes. No identity is inferred from failed collection.
