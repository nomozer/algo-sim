# Handoff — Backend Hybrid Session 2 (`backend-hybrid-contract-unification`)

**Final state: `SESSION2_CONTRACT_DECISION_REQUIRED`.** Backward-compatible implementation complete, frozen, independently
reviewed and gated by an Authoritative Full T3 (below). Further unification needs Owner decisions D1–D6
(`CONTRACT_DECISION_PROPOSAL.md`). Results and the ten answers: `report.md`.

## Git

| item | value |
|---|---|
| branch / worktree | `research/hybrid-backend-session2-contract` · `.superpowers/worktrees/hybrid-backend-s2` |
| base | Session 1 HEAD `82d3d25540ea643a68bd7877eb1b67a78dfc7134` (Session 1 branch, worktrees and untracked logs untouched) |
| `origin/main` / local `main` | `43247c9e` / `f10e6283` (local main 1 docs-only commit ahead, unpushed; not in this branch) — fetched, unchanged |
| product | `3553e4d45991954dd0fb8c0ac30bf5fb79a3ff51` |
| candidate freeze | `5beb0e86` — clean detached freeze at `3553e4d4`, 115 files, `96962736b4aed18ec13afd73d06fab822fe398d7bf5939babc9a3733e45c1af4` |
| test-only fix after review | `a6aee400` (strict xfails; measured system unchanged) |
| evidence + docs | `f1ae2238` |
| T3 target | `f1ae22384e3e01255879f52aa4104eb33ca46a3f` |

Commits have no `Co-Authored-By` trailer. Nothing merged or pushed; no branch or worktree deleted.

Worktrees created this session (kept, for evidence): `hybrid-backend-s2` (campaign), `s2-freeze` (detached `3553e4d4`,
clean freeze), `t3-s2` (detached T3 target; `frontend/node_modules` is a junction — `rmdir` it before any
`git worktree remove`). Raw pytest / T3 logs are local and untracked (AGENTS §4: no raw traceback in git); committed
receipts carry their SHA-256.

## Verification

- Targeted suites (single worker): new `test_hybrid_contract_unification.py` 20 passed + 1 xfail; Adapter /3, bridge,
  curved, Wave 3A, preview suites green; composition suites 334 passed; docs gates green.
- Independent review round 1: `INDEPENDENT_REVIEW_PASS` (0 BLOCKER, 2 IMPORTANT handled, 3 MINOR recorded) —
  `independent-review.md`.
- Authoritative Full T3: see `verification/full-t3/execution.json` — result recorded below.

**Authoritative Full T3 — `FULL_PRODUCT_GATE_PASS`** (single attempt, no retry): `node frontend/scripts/full-gate.mjs` in
the clean detached worktree `t3-s2` at `f1ae22384e3e01255879f52aa4104eb33ca46a3f` (measured system = candidate
`96962736…`), exit 0, 582.35 s, dirty before/after: none. pytest **11525 passed**, 1 skipped, 2 deselected, 15 xfailed,
0 failed (553.0 s); vitest **72/72 files, 1156 passed**; typecheck + build PASS; demo 5/5; crash surface 6/6. Post-T3
`freeze_evaluation_candidate.py --verify`: MATCH (exit 0). Receipts: `verification/full-t3/execution.json`
(stdout SHA-256 `561e4586…`, stderr `aa9b7207…`), `invocation.json`, `post-t3-freeze-verify.json`; raw stream logs kept
local, untracked. T3 is the only gate run — no browser gate (scene3d-orbit, photo, spot-check) was run.

## Governance (unchanged)

`DEFAULT_MODE = LLM_ONLY` · `RESPONSE_CONTRACT = flat` · `HYBRID_PRODUCT_ENABLEMENT = NO-GO` · `ALLOW_LIVE_AI = 0` (0
provider calls) · `CACHE_VERSION = 127` (NO_BUMP) · contract versions `typed-fact-next/1`, bridge `/1`, Adapter `/3`,
route-D `/3`, Registry `/12`, Planner `/12`, Engine `/10` unchanged.

## Open for the owner

D1 `typed-fact-next/2` section contract · D2 Source Gate strictness (strict costs Adapter /3's corpus unless D3 + D6) ·
D3 gate grammar coverage (4/5 paraphrases and 5 corpus encodings false-refused) · D4 IR budget policy for engine programs
(hexagon 33/36) · D5 version labels · D6 planner-derived unstated cuts. Follow-ups without a decision: narrow the
`except` around the bridge in `_shared_source_gate`; enforce the dedup name invariant; Adapter /3 non-`TuChoi` crash
surface on malformed premise args (pre-existing).
