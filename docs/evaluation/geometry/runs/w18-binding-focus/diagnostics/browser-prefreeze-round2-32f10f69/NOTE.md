# Pre-freeze browser round 2 — 32f10f69 (diagnostic, not acceptance evidence)

The confirm round after the harness fix 32f10f69. Same scratch worktree `D:/tmp/w18-pre`, moved
to 32f10f69, same fixtures as round 1 (`D:/tmp/w18-pre-fixtures`), same stale identity labels (see
round 1). Command, from `D:/tmp/w18-pre/frontend`:

    timeout --signal=KILL 3000 node scripts/compiler-scene-replay.mjs --suite scripts/generic-tier-a-scenarios.json --fixture-root D:/tmp/w18-pre-fixtures --ra D:/tmp/w18-pre-browser-r2

Result: six families PASS, suite exit 0. It showed that the harness was ready before the freeze.
It is not acceptance evidence: the product changed afterwards (7a06ee47, behaviour-preserving
cuts) and the candidate was frozen at 7a06ee47. The acceptance run is in `../../results/`.

- `BROWSER_EVIDENCE.json` and `SUITE.log` are copied unchanged from the scratch output.
- The screenshots stayed in the scratch folder; they are listed in `../TEMP_FILE_INVENTORY.json`.
