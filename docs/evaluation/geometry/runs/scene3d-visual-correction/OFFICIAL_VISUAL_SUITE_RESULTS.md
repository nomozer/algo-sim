# Official Visual suite results

**Final: 7/8 at candidate freeze `c84e8620` (product `b8b3311b`). `F2_POLICY_DECISION_REQUIRED` stands. Not 8/8.**

## 1. How it was run

| Item | Value |
|---|---|
| Runner | `frontend/scripts/compiler-scene-replay.mjs --suite`, Playwright transport (`visual-closure-hybrid-readiness/browser-environment.mjs`) |
| Viewports | desktop 1440 + mobile 390, one uninterrupted run per candidate |
| Model calls | 0 |
| What was measured | `dist/` built at the candidate commit, in the clean detached worktree `.superpowers/worktrees/svc-cand` (owner Bunny) |
| Inputs | the locked `visual-closure-hybrid-readiness/visual/final-inputs`, rebound to the candidate by `prepare_official_inputs.py` (a copy of the integration run's script, unchanged) |
| Rebinding | changes only `product_commit_sha`, `product_tree_sha`, `task_id`; it asserts that envelopes, scenarios and oracle expectations are unchanged (49 inputs, `geometry_envelopes_changed: 0`, `oracle_expectations_changed: 0`; see `official-inputs-*-rebinding.json`) |
| Locked oracle | **not edited**. The role-aware check (§3) is separate and is not part of this suite |

## 2. Results

| Candidate | Result | Failing assertions | Evidence |
|---|---|---|---|
| `ddb1a4be` / `88a1b43e` (before this campaign, from the integration run) | 7/8 | `cross_section`: `canvas_role_hues.cam` → `causal_closure`, `evidence_gates` | `../visual-b3-sphere-integration/` |
| `3c6d1e65` (Codex + Claude, after both review rounds) | **0/8** | every family: `mode_b_reveal`, `selection_per_quantity` (`ANNOTATION_MISSING:<result>`), `evidence_gates`; `cross_section` also `causal_closure` | `visual/official-run-3c6d1e65-mode-b-regression/` |
| **`c84e8620`** (Mode B reveal restored, `b8b3311b`) | **7/8** | `cross_section` only: `canvas_role_hues.cam` → `causal_closure`, `evidence_gates`, desktop and mobile | `visual/official-run-c84e8620/` |

### The 0/8 regression, and why it was not caught earlier

Codex's answer-presentation change hid final results in **both** modes: the value in the «Kết quả» row (`giaTri`) and
the result's canvas annotation (`hiddenIds`). The locked contract (Owner policy `aa458cc3`, encoded in
`compiler-scene-suite.mjs` `mode_b_reveal`) hides them in Mode A only. In Mode B:
- each final answer is in exactly one «Kết quả» row, carrying the expected value;
- the analysis panel states it;
- selecting the result shows its annotation on the canvas.

Codex's own vitest asserted the stricter reading, and so did the takeover's browser-matrix check. Both were written to
the same misreading, so neither could catch it. Only the locked suite did. Fix `b8b3311b` reverts exactly those two uses
(`tapKetQua` → `dapAnAn`). It keeps Codex's inspector change (link to the analysis panel instead of repeating the
value), and it corrects the test and the check. Lesson for the next run: run the locked suite before trusting a
re-interpretation of a locked policy.

## 3. The one remaining failure (F2)

`cross_section` fails `canvas_role_hues.cam`. The locked hue gate counts every orange-band pixel of a selected-state
frame as a violation. Owner policy F2 keeps the section's terracotta fill and turns only its boundary cobalt, so the gate
fails exactly the policy. This is unchanged since the integration run. It needs an Owner decision: amend the locked gate
or adopt a role-aware check. It is not a renderer bug, and the locked oracle was not edited to hide it.

The supplemental role-aware check (proposal, not official), on `b8b3311b` (`verification/role-aware-b8b3311b/`). The
verdicts are identical to `78aaef2f`:

| Rows | Unfaulted views | Certified views | Faults detected | Retries / error rows |
|---|---|---|---|---|
| 180 | 19 PASS · 0 FAIL · 11 UNCERTIFIABLE | polygon 10, circle 5, ellipse 4 | 95/95 on certified views (55/55 also FAIL on uncertifiable views) | 0 / 0 |

Faults injected: boundary→terracotta, boundary→magenta, fill→grey, fill hidden, wrong object.

Known limits are listed in `REVIEW_REPORT.md`:
- it shares the renderer's curve discretisation;
- a hidden arc may lose up to about 40 % of its ink and still pass;
- views where labels cover the boundary are UNCERTIFIABLE, not certified.
