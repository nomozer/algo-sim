# Geometry capability and non-absolute architecture preregistration (w13)

Status: `ARCHITECTURE_PREREGISTRATION_READY` — documentation and evidence only. No
product code, no refreeze, no cache bump, no model call, no browser run, no push, no
merge.

## Identity

- Branch `fix/cuboid-visual-semantic-closure`, start `bf5a7907`. `origin/main`
  re-fetched: `a9492ee9`, unchanged, ancestor of HEAD.
- Commits: `7202befe` (architecture audit, matrix v2, inventory, probe, Phase 0 log) and
  the documentation commit that contains this file.
- Candidate `548f5b3b…` (product commit `4014f311`) unchanged; `CACHE_VERSION` 105
  unchanged; schema mirrors `d852b47c…` byte-identical after two exports;
  `DEFAULT_MODE = LLM_ONLY`. The identity values in the task statement were re-read from
  the repository and matched.

## The w12 review and what w13 did with it

| Finding | What w13 established | What happens next |
|---|---|---|
| W12-H1 — triangular pyramid shows only givens/points → base → solid | `compiler.py::bien_dich` emits no height segment and no lateral-edge group; its narration names a height that the scene does not contain | generic `PYRAMID_LIKE` formation (preregistration §2, §6 Track A) |
| W12-H2 — triangular prism shows only givens/points → base → solid | `_bien_dich_prism` emits no top face and no lateral edges; the cuboid path already does | generic `PRISM_LIKE` formation |
| W12-H3 — no family-specific patch before the missing shapes are assessed | the 17-group matrix and the audit are that assessment | the fix is one shape-class plan for every family, guarded by an AST check |
| W12-H4 — assumption channel still open | unchanged; policy and acceptance criteria written | Track B |
| Four families `PROVISIONAL_PASS`; amber section = design question (W12-D1) | recorded as such; not a failed gate | D1, no change in W14 |

The review is recorded additively in `inputs/W12_HUMAN_VISUAL_REVIEW.json`; the w12 run
is byte-identical.

## Absolute assumptions

67 items, each with `file:line` sources: A 4 · B 1 · C 9 · D 13 · E 3 · F 6 · G 8 · H 4 ·
I 9 · **J 10** (`results/ABSOLUTE_ASSUMPTION_INVENTORY.json`). HIGH severity:

- NA-05 — a default backend test requires `D:/tmp/live_retry_evidence/…`; T3 is green only
  on the machine that holds it.
- NA-18 — the per-family compiler statement sequences (root cause of W12-H1/H2).
- NA-37 — the assumption channel (W12-H4).
- NA-54 — coordinates only in Q³: figures without a rational placement (regular
  triangles and tetrahedra, regular pyramids given by base and lateral edge) cannot be
  built exactly, and there is no stable refusal code.
- NA-57 — measured by the probe: *"AB dài 5 cm"* binds no segment, so a program can
  declare `AC = 5` as GIVEN and pass.

Two findings worth reading even though they are not HIGH: the production synthesis prompt
still tells the model that oblique cylinder/cone sections cannot be expressed (NA-52), and
`geometry/exact.py::hf` rationalises floats with `limit_denominator(10**9)` while its
docstring says the conversion is exact (NA-42).

The five examples the task asked for are answered in the audit document §2.2: no GPU model
is recorded anywhere (a GPU is a baseline, never a contract); Chrome 154 is the recorded
environment of w12; `3·3·5·5·5·10` is a historical measurement; cache and candidate are
read from the repository; the colour role is the contract and the hex value is a token.

## Capability inventory

17 groups × 17 layers (the task says 16 layers and names 17; all 17 are kept) = 289
cells: `SUPPORTED` 82 · `PARTIAL` 111 · `MISSING` 87 · `NOT_APPLICABLE` 9. By taxonomy:
polyhedral `PARTIAL`, curved solid `PARTIAL`, auxiliary geometry `PARTIAL`, section
`PARTIAL`, composite scene `MISSING`. The frustum group is `OUT_OF_SCOPE_PENDING_DECISION`.
Educational evaluation is `MISSING` for every group. The matrix links to — and does not
override — `product_capability.py` and the 12-family `CAPABILITY_MATRIX.json`; it also
records three places where it reads the 2026-09-25 v1 matrix differently.

## Preregistration

`docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`: six shared
abstractions, a generic formation model (open set of semantic operations with their IR
status, valid-step criteria V1–V9, minimum semantic coverage per shape class without
counts), the assumption/default policy (P1–P6, AC1–AC7), the source-grounding table, the
capability-based environment policy, and the next wave
`W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION` with success criteria S1–S8, seven fault
injections and stop rules. W14 starts after the user answers D2 (refuse + label, or also a
confirmation UI) and D3 (whether cone/sphere formation joins W14; proposed: no).

## Living documents

CURRENT_STATE (base state, a w13 table, correction banners on the stale §3/§4 capability
lists), ROADMAP §0 and P2, AI_CONTEXT_BUNDLE, OPEN_ISSUES (six new issues; the two prism
issues marked RESOLVED from code; the compiler-coverage and OCR issues annotated as stale;
the assumption issue pointed at W14), STATUS_LEDGER, EVIDENCE_INDEX (chain, w12 entry,
w13 entry), THESIS_READINESS (scope of the w12 GIVEN closure), ARCHITECTURE_MAP, docs
README, CODE_INDEX (the probe), and the docs-audit allow-list (W13 and W14 action names).

## Verification

| Check | Result | Evidence |
|---|---|---|
| JSON files parse | PASS — `json.loads` over every JSON of this run plus the v2 matrix: 7 files, 0 invalid (before `MANIFEST.json` existed; the manifest is written by a script) | session check |
| Docs information-architecture audit | PASS — 0 broken links in canonical docs, next action canonical | both logs |
| Relative links in every touched markdown file, every `docs/architecture/*.md` and the run documents | 58 checked, 0 broken | session check |
| Docs-touching backend tests, clean detached worktree at `7202befe` | 507 passed | `diagnostics/logs/CLEAN_WORKTREE_DOCS_TESTS_7202befe.log` |
| Same tests, main tree | 506 passed, 1 failed — `test_holdout_readiness_7b::test_bao_cao_da_sinh_va_KHONG_TROI` requires a clean tree; the main tree carries the user's favicon deletion and the uncommitted w13 documents | `diagnostics/logs/VERIFICATION_MAIN_TREE.log` |
| Docs-touching frontend tests (6 files) | 47 passed | main-tree log |
| Candidate verify · cache verify | exit 0 · exit 0 | main-tree log |
| Schema export ×2 | both mirrors `d852b47c…` both times; no file changed | main-tree log |
| `DEFAULT_MODE` | `LLM_ONLY` (`routing.py:30`) | main-tree log |
| `git diff --check` · product diff (`backend/app`, `frontend/src`) | clean · 0 lines | main-tree log |
| Full product suite | `NOT_RUN_NOT_REQUIRED_FOR_DOCS_ONLY_AUDIT` | — |

## Limitations

- Each matrix cell is read from code; none was exercised by running that shape in w13,
  except the source-grounding probe. Cells that are guesses say `HYPOTHESIS`.
- The number-theory statements about rational placements are hypotheses that a
  deterministic feasibility check must confirm before they become rules.
- The Tin học-era parts of `STATUS_LEDGER` (rows 191–456, 600–902) and the long
  development log of `CURRENT_STATE` were keyword-scanned, not read line by line.
- The temporary worktree `D:/tmp/w13-verify-c1` is unregistered but still on disk
  (`diagnostics/WORKTREE_CLEANUP.json`); it holds no unique artifact.
- The audit document committed in `7202befe` links to two files added by the next commit.
- Correction inside this run: `7202befe` wrote into
  `results/REMAINING_GEOMETRY_CAPABILITY_MATRIX.json` the sha256 of the v2 matrix's CRLF
  working-copy bytes (`00561661…`), which no LF checkout reproduces. The documentation
  commit replaces it with the hash of the LF-normalised content (= git blob content,
  `6bac0245…`) and states the basis; the cells are unchanged.
