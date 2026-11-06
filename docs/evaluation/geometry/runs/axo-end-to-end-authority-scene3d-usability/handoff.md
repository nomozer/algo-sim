# Handoff

Status: **READY_FOR_OWNER_REVIEW**. Read `report.md` (11 sections) first.

- Branch `integration/axo-hybrid4-reliability`, worktree `.superpowers/worktrees/axo-hybrid4-integration`. Start `667fff7a`;
  commits `751d9eff` (backend certificate authority) → `e1309a79` (near-zoom + label wheel) → `b1282aee` (candidate refreeze)
  → docs-only evidence commit(s). `main` untouched. Not merged, not pushed. 0 provider calls.
- Tested tree for T3: `b1282aee`, clean detached worktree. Run 1 FAIL (1 telemetry concurrency test, outside the change, passes
  alone 3/3); run 2 PASS on the same tree. Node harness 0 fail.
- Re-run the authority audit: `tools/collect_served_corpus.py <fresh.json>` (from `backend/`), then the harness in
  `tools/authority_audit.vitest.ts.txt` (copy into `frontend/src`, run, remove). Expected 434/434 reached on this HEAD.
- Camera observability: `node scripts/axo-camera-views-browser-check.mjs --dist dist --fixtures
  ../docs/evaluation/geometry/runs/axo-hybrid4-capability-scene3d-reliability/fixtures --out <fresh> --viewport WxH`.
- Live prism probe (needs Owner GO + budget, 1 call): `ALLOW_LIVE_AI=1 python tools/prism_layer_probe.py --live --max-calls 1 <fresh.json>`.
- Untracked artifacts of earlier runs and perf traces/screenshots of this run stay untracked (repo practice: receipts only).
- Owner decisions: publication exceptions (98 pending + `28be1ef6`, risk table §11), merge/push, live prism run, telemetry
  write-loss follow-up task.
