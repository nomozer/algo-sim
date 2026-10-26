# Hybrid V2 backend generalization — named planes and point–line distance

Run `hybrid-v2-backend-generalization`, 2026-10-26, Claude. Owner authorization for this task only: push the verified
local `main`; finish, verify, merge and push this backend branch if every integration gate passes; safe cleanup. No
force-push, no history rewrite, no live provider, Hybrid stays opt-in, `LLM_ONLY` stays the default.

Evidence class throughout: **authored development cases** (offline, 0 provider calls). Not a holdout, not an extraction
measurement. `INDEPENDENT_HOLDOUT_NOT_EXECUTED`, `INDEPENDENT_REVIEW_NOT_EXECUTED`.

## 1. Remote main sync (P1)

| | SHA |
|---|---|
| local `main` before | `a9889031a1ff1bedcf56b4d6843b000088fb4660` |
| `origin/main` before | `43247c9e9375a3dbf2b5223324a58e6f932ca596` (ancestor of local, 0 commits only on remote) |
| push | `43247c9e..a9889031  main -> main`, 226 commits, no force |
| after fetch: local = `origin/main` = `ls-remote` | `a9889031…` — **`REMOTE_MAIN_SYNC_VERIFIED`** |

Pre-push scan of the 226 commits: no key/token pattern (one regex false positive, `task-profile…`), largest blob
12.5 MB, two committed evidence zips opened and checked (logs only). Product trees equal the Full T3 PASS candidate
`3d6351d8`, so the Scene3D T3 was not repeated.

## 2. Gap audit (P2, code read at `a9889031`)

| Capability on the canonical `/2 → /4` path | Before | Evidence class |
|---|---|---|
| distance point–plane, segment, skew lines (B3) | served, 3-label planes only | backend + earlier browser rows |
| angle line–plane / line–line / dihedral | served, 3-label planes only | backend + earlier browser rows |
| plane named by ≥ 4 labels, (ABCD), (BCC′B′) | **refused** `INVALID_MATH_GOAL` (route B served it) | — |
| distance point–line | **refused** `INVALID_MATH_GOAL` (route B served it) | — |
| volume, section area, volume ratio | served | backend |
| curved solids, Oxyz | refused `BRIDGE_UNSUPPORTED_CURVED` / no contract | correct refusal |
| live NL extraction | not run | UNKNOWN |

Rendering a solid is not support: the curved families stay RENDER_ONLY.

## 3. Capability 1 — named planes (P3)

Commits `1cff5458` (first version), `b11349ae` (witness + identity fix asked by the Owner), `302f5139` + `e7284ce3`
(preview fixtures), `ac644c9c` (browser evidence).

- Bridge `/2`: a plane operand is ≥ 3 distinct labels; lines/segments exactly 2; repeated labels `INVALID_MATH_GOAL`.
- Planner /14: a > 3-label point–plane distance plane keeps the registry's three-label call (function-calling surface
  `7ea511a6…` unchanged) and is handed in full to the engine (`KeHoach.named_planes`, keyed by call id).
- Engine /13: `chon_ba_mat` measures every question plane through the **first non-collinear triple of the whole group**
  — (BMCC′) with M on BC is served, not refused (the first version refused it; corrected); `kiem_mat_viet` checks every
  label coplanar (`SOURCE_OBJECT_MISMATCH`, also when all points are collinear or a label coincides); the IR plane carries
  the written name, so the learner sees **(BCC′B′)** / **(ABCD)**, never the witness triple.
- Side effect on route B (intended): preview fixture H03 now reads "góc giữa SA và (ABCD)" instead of "(ABC)"; answer
  and geometry unchanged; every other fixture differs only in producer commit / version identity. New bundle
  `fixtures-adapter-2-named-plane/`; older bundles kept.

Tests: `test_typed_fact_next_v2_named_plane.py` (closed-form oracles, families #3, #4, #11, #12, #13; 3/4/5-label
planes; label orders incl. crossed; collinear leading labels; coincident label H = A; all-collinear; non-coplanar 4th
label incl. one absent from the quote (review I-1); unknown label; quote naming another face; display identity; scale;
fractional and irrational values). Fault injection `fault-injection.json`: **16/16 detected**, every file restored
byte-identical.

## 4. Capability 2 — point–line distance (P6)

Commit `eca4b44b`. `/2` `{point, line}` → the planner's existing decomposition: the foot is built on a fresh auxiliary
label by `orthogonal_projection_line` (a text that already uses H gets another label); the engine checks foot ∈ line and
segment ⊥ line, then measures. Point named only by the question ⇒ `UNDERDETERMINED_POINT`; quote naming another line ⇒
`SOURCE_OBJECT_MISMATCH`; point on the line ⇒ served 0 (true value); malformed operands `INVALID_MATH_GOAL`.

Oracles: right prism d²(A, BC), d²(A′, BC) (three perpendiculars); SA ⊥ base pyramid d²(A, SB), d²(S, BD), d²(A, SC);
regular pyramid d²(A, SC) = 2s² − s⁴/l²; cuboid d²(A′, BD). Fault injection `fault-injection-point-line.json`: bridge
mapping removed (17 red), 3-label line (1), list point (1), degenerate decomposition (16), wrong foot computed (14) — all
detected; removing the independent ⊥ check alone (correct foot) stays green — defence in depth; two verifiers not on
this path (`_kc2_do_dai`, `_kc2_khoang_cach` line branch) were probed and are **not** exercised here
(`fault-injection-point-line-verifier-probe.json`).

Known presentation gap (not incorrect): the answer is labelled `d(S, H)` with the construction step "Dựng H: hình chiếu
của S lên BD", not `d(S, BD)` as asked — the existing route B convention. Recorded under D-10.

## 5. Version, cache, compatibility (P4)

| Identity | Before → after | Why |
|---|---|---|
| `REGISTRY_VERSION` | `geometry-functions/13` (unchanged) | no function or schema changed; surface fingerprints unchanged |
| `PLANNER_VERSION` | `/13 → /14` | plan output gains `named_planes` |
| `ENGINE_VERSION` | `/12 → /13` | witness choice, named-plane check, IR plane label (served output changes for > 3-label planes) |
| `typed-fact-next-bridge/2` | unchanged | the string names the schema generation; B3 and the angle slice also changed it without a bump; identity carried by planner/engine |
| `CACHE_VERSION` | `130` (unchanged) | default `/api/analyze` never imports `geometry_functions`; the Hybrid V2 local route answers `no-store`; route D preview refuses the product cache (`main._policy_identity`) ⇒ no stored refusal can be replayed |

`IDENTITY_DELTAS` declares the planner/engine pair for preview-fixture verification. Version pins updated in 4 test
files; architecture docs updated.

## 6. Browser E2E (P5) — `OFFLINE_BROWSER_E2E_VERIFIED`, not `LIVE_NL_E2E_VERIFIED`

Harness `frontend/scripts/b3-distance-browser-e2e.mjs --analyze`: real input box → HTTP `/api/analyze` on this branch
(`HYBRID_V2_LOCAL=offline-replay`, authored replay corpus, loopback, no API key) → `/4` consumer → Scene3D, Chrome
headless, 1440 and 390 px. Checks per served row: HTTP contract + `no-store`, expected disposition, consumer accepts,
Mode A hides the answer, Mode B shows it exactly once, displayed value² equals the closed-form oracle (not engine
output), engine binding, certified witness drawn when provided, no new number in the inspector, no internal name, no
horizontal overflow. Refused rows: no scene, learner reason shown, code hidden, no answer.

| Run | Families | Rows | Result |
|---|---|---|---|
| `browser-named-plane/` | #3, #4, #11, #12, #13 | 28 (10 served + 4 refused × 2 widths) | **28/28 PASS**, 0 JS errors, 0 external requests |
| `browser-point-line/` | #3, #4, #11, #12 | 16 (6 served + 2 refused × 2 widths) | **16/16 PASS** |

Not covered: orbit sweeps of these scenes (renderer unchanged), selection/deselection beyond the selected answer.

## 7. Generalization checks (P7)

Covered by authored tests: label renaming (≥ 5 label sets), plane label order and crossed order, 3/4/5-label names of
one face, fact order (premise inserted before the question), scale ×2, fractional and irrational answers (24√29/29,
12√82/41), non-axis-aligned solids (oblique prism, regular pyramid with irrational height), missing data, contradictory
operands, degenerate groups. Not observable through this interface: translation/rotation of a coordinate input (the
engine chooses the layout; oracles use no coordinates). Planner budget: unchanged (existing `PLAN_TOO_LARGE` tests).
Independent holdout and independent review: **not executed**.

## 8. 18-family matrix

No class changes: **0 FULL_E2E_VERIFIED / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED**. Delta: on `/4`, named-plane
distance/angle goals are OFFLINE_BROWSER_E2E_VERIFIED for #3, #4, #11, #12, #13 and point–line distance for #3, #4, #11,
#12. FULL still needs independent expectations, NL extraction evidence and the remaining family scope (sections,
circumscribed spheres, etc.).

## 9. Full T3 on the backend candidate (P8)

| Item | Value |
|---|---|
| product commit | `eca4b44be1fc1b4de45a87eb9931995ea37cb8aa` |
| freeze | `cec477a5` — 118 measured files, `ecae59e688d2ae1e3262d0f44da2acf5bbe1677c28c7a141165fcfb11257016b` |
| candidate (clean detached checkout) | `7210a016183e72b8f94dd32a6ca7dc2090483ab5`, tree `c676d3ee…`, source clean before and after |
| verdict | **`FULL_PRODUCT_GATE_PASS`**, exit 0, 2026-10-26 16:12–16:24 UTC |
| backend pytest | 12086 passed, 1 skipped, 15 xfailed, 0 failed |
| frontend vitest | 1417 / 1417 (83 files); build, demo replay, crash surface PASS |
| post-run freeze verify | MATCH; freeze file SHA-256 identical before/after |
| streams | `full-t3/stdout.log` `9586d24a…`, `full-t3/stderr.log` `aa9b7207…`; receipt `full-t3/receipt.json` |
| provider calls | 0 (`ALLOW_LIVE_AI=0`, `HYBRID_V2_LOCAL` unset) |

Everything committed after `7210a016` on this branch is documentation (this report, handoff, indexes); the measured
product files are unchanged, so the receipt still describes the merged code.

## 10. Merge gates (P9)

| Gate | State |
|---|---|
| Full T3 PASS + freeze MATCH | PASS (`7210a016`) |
| browser E2E within the claimed scope | PASS (44/44 rows) |
| oracles + negative tests + fault injection | PASS (16/16 + 5/5 effective) |
| known incorrect-served case | none known |
| Source Gate / provenance fail-closed | unchanged; quote-mismatch refusals tested |
| default `LLM_ONLY`, `CACHE_VERSION=130` | unchanged (T3 tests) |
| live provider | 0 calls |
| Official F2 | no new regression possible: no renderer or `frontend/src` product file changed (one test file only); locked suite not re-run |
| independent review | `DEFERRED_FOR_LOCAL_DISABLED_BACKEND_INTEGRATION` — not a PASS |
| Hybrid production | not enabled |
