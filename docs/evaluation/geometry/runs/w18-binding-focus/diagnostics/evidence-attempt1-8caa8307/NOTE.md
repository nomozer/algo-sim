# Acceptance attempt 1 — measurement commit 8caa8307 (superseded, kept apart)

The first complete acceptance measurement on the final candidate `d3b4cab9` (product commit `7a06ee47`), in clean
detached worktrees at `8caa8307`, 0 model calls. Every gate passed:

- browser suite: 12/12 positives, 46/46 negatives, 6/6 served;
- occlusion: pass, `HUMAN_REVIEW_PENDING` (the four W14-changed scenes);
- playback: 12/12;
- sheet builder: 64 crops, 0 disagreements;
- T3 `FULL_PRODUCT_GATE_PASS`: pytest 7001 / 0, vitest 1058 / 1058;
- identity gates: all PASS;
- backend fault injections run 3: 12/12.

It is superseded because the frontend fault injections run 1 (`../logs/FAULT_INJECTION_W18_FRONTEND.log`) found
three blind spots of the browser HARNESS. The product was right, and its unit tests caught all three faults:

| Injection | What the harness missed | Root cause |
|---|---|---|
| FW1, a highlighted hidden edge drawn solid | `dash_signature_preserved` stayed true | the dash check ran only in the causal state, where no edge owner is highlighted |
| FW2, the chip rewinds to step 0 | the suite threw `CAUSAL_TARGET_NOT_CLICKABLE` and wrote no evidence | the isolation reference was the state after the first toggle, and a throwing run killed the suite |
| FW4, two regions carry a formula | `DETAIL_REGIONS_2` never computed | no result with a referenced formula was selected while the solution was open |

The harness was fixed red-first (`../logs/RED_W18_HARNESS_FIX.log`; amendment §16.8 dated correction, registered
before re-measuring). Every acceptance run was then repeated at the new measurement commit on the unchanged candidate.

What is kept here, copied unchanged from the measurement worktree `D:/tmp/w18-m`:

- `results/`: `BROWSER_EVIDENCE.json`, `OCCLUSION_MEASUREMENT.json`, `PLAYBACK_EVIDENCE.json`,
  `HIDDEN_EDGE_CROPS.json`. They record the sha256 of every screenshot.
- `logs/`: the command logs of that attempt.

The 466 images of this attempt were never committed. They are reproducible from `8caa8307` and are listed in
`../TEMP_FILE_INVENTORY.json`. The backend fault-injection run 3 (`../logs/FAULT_INJECTION_W18_R3.log`) tested the same
product code and stays valid.
