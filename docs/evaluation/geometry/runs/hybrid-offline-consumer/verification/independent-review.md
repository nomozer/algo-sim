# Independent review — `hybrid-offline-consumer` (Session 5)

Reviewer: fresh-context Claude subagent, read-only (no repo/git writes, no network, no model calls; probes in a
temp directory outside the repo). Implementers: Codex (`56507602`) and Claude (takeover fixes). The reviewer is not a
holdout curator. Final verdict: **`PASS` (round 3, `e090af1c`)**.

## Round 1 — `3f6d7375..2f4be5a7` — `PASS_WITH_FINDINGS`

| id | severity | finding | disposition |
|---|---|---|---|
| R1-M1 | MAJOR | Provenance checked one way only: derived `I` relabelled `SOURCE_NAMED`/`stated=true` accepted (adapter + store), confirmed by execution | fixed `12a56461`: per-provenance rule `LUAT_NGUON` from planner `_dinh_cat_canh` |
| R1-M2 | MAJOR | Dropping `boundary`/`closure_certificate` entered the plane-only path beside a derived solid (vertex_ids deleted/renamed/solid removed) while serving residual answers | fixed `12a56461`: certificate-less only when no solid besides the cut one; dangling `depends` refuse |
| R1-M3 | MAJOR | Docs IA `test_inv_20` red: candidate not re-frozen after `frontend/src` change | fixed `9f06ed2b` (freeze, `--verify` MATCH) |
| R1-m1 | MINOR | Boundary threw `TypeError` on malformed scene shapes | fixed `12a56461` (refuse, never throw) |
| R1-m2 | MINOR | Harness "early" check reused `entitiesPresentAt`, blind to section sub-entities drawn ahead of construction | fixed `12a56461`/`e090af1c`: open-section `::face` forbidden, `::vertex:k` index ≤ visible edges |
| R1-m3 | MINOR | Circular readout checks; per-frame answers not asserted; refusal rows skipped leak check | partly fixed: `quantityEarly` asserted (independent path via `formation.visible_ids`), refusal leak check added; readout remains operator-only (disclosed) |
| R1-m4 | MINOR | Receipt not bound to a clean tree | fixed: `tree_clean` recorded; authoritative receipt `browser-final-9f06ed2b` has `tree_clean: true` |
| R1-m5 | MINOR | Vitest did not run this run's 25 refusal fixtures | fixed: all 25 run in `adapter4-consumer.test.tsx` |
| R1-m6 | MINOR | `/4` wrapper has no backend producer; refusal envelopes synthesised via `classify_refusal` | disclosed in report §6 (out of scope: no endpoint by design) |
| R1-m7 | MINOR | Duplicated literals (`Điểm dựng phụ`, `typed-fact-next/2`) | constants `VAI_DIEM_PHU`, `HYBRID_SIMULATION_CONTRACT`; backend literal still mirrored |
| R1-m8 | MINOR | `extraction-replay.json` has no execution receipt | disclosed (Codex artifact; counts reconciled by reviewer) |
| R1-m9 | MINOR | Takeover checkpoint misdescribed attempt 4 | corrected in `report.md` §2 (checkpoint file left unedited) |
| notes | NOTE | empty closure rule accepted; `″` not normalised; `declared_boundary` copied unchecked | first two fixed; third left (view field, unread) |

Reviewer's suggested fix for R1-M1 ("non-`DERIVED_FRESH` must not be a derived auxiliary") was **not** adopted:
12 real `STATED_UNNAMED` vertices are unnamed auxiliaries with role `Điểm dựng phụ` and would be falsely refused.

## Round 2 — `2f4be5a7..12a56461` — `PASS_WITH_FINDINGS`

All round-1 probes re-run and closed; 0 false refusals on 22 served + 25 refusal fixtures and the /2 tests.
New: **MAJOR** — `THROUGH_POINT_REUSE` unconstrained, so derived `I` relabelled through-point was accepted (confirmed).
Fixed `e090af1c`: named point that the section plane depends on (true of all 22 real through-point vertices).
MINOR — coordinated multi-field scene fabrication (remove derived solid and scrub every `depends`; retype it to
`polygon3`) still passes; accepted as the ceiling of a consumer that does not recompute geometry. `events[].object` is
not checked because 11/22 real scenes have event objects that are not scene objects (would falsely refuse).

## Round 3 — `12a56461..e090af1c` — `PASS`

Round-2 bypass and named-intersection→through-point relabel rejected; dangling `visible_ids` rejected; 0 false
refusals; harness per-index bound shown non-vacuous (index equals the bound in 2 of 116 open-section frames).
MINOR (evidence): no browser receipt at `e090af1c` yet → resolved by `results/browser-final-9f06ed2b` (candidate
commit, clean tree, PASS). NOTEs accepted: `THROUGH_POINT_REUSE`→`SOURCE_NAMED` relabel promotes nothing;
`qua` accepts any non-solid in `section.depends` (fixtures only have `plane3`); `REUSED_INTERSECTION` unconstrained.

Disclosed residual ceiling: the scene cannot distinguish `STATED_UNNAMED` from `DERIVED_FRESH`; that flag is
backend authority.
