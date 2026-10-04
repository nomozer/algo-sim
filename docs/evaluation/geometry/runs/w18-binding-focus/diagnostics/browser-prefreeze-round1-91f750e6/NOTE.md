# Pre-freeze browser round 1 — 91f750e6 (diagnostic, not acceptance evidence)

The first real-browser round of W18, before the freeze. It ran on the detached scratch worktree
`D:/tmp/w18-pre` at 91f750e6 (W18 product code; the registry and `EVALUATION_CANDIDATE.json` there
still named the W17 candidate d63d6fd4, so `product_commit_sha` in the evidence reads d3817d5f).
Command, from `D:/tmp/w18-pre/frontend`:

    timeout --signal=KILL 3000 node scripts/compiler-scene-replay.mjs --suite scripts/generic-tier-a-scenarios.json --fixture-root D:/tmp/w18-pre-fixtures --ra D:/tmp/w18-pre-browser

Fixtures were generated in that worktree (0 model calls). Result: five families PASS, cuboid FAIL.

| Code (cuboid) | Count | Cause | Kind | Fixed in |
|---|---|---|---|---|
| `SOLUTION_LAYER_OUT_OF_SYNC`, `STRUCTURED_REFERENCE_NOT_RENDERED` | 4 + 4 | The harness oracle `expectedSolutionRows` did not know rule §16.6 (`same_as`). The product merges the measured duplicate of a given (cuboid: d(A, A′) and AA′ = 5) into the given's row; the oracle still expected a separate row and a reference to it. | measurement | 32f10f69 (the oracle drops a `same_as` row whose owner is present; `solutionRowOf` resolves references through it). Product unchanged. |

- `BROWSER_EVIDENCE.json` and `SUITE.log` are copied unchanged from the scratch output.
- The screenshots stayed in the scratch folder; they are listed in `../TEMP_FILE_INVENTORY.json`.
