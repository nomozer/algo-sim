# Generic formation and assumption foundation (w14)

Status: **`FORMATION_FOUNDATION_INCOMPLETE`** — the first matching row of the plan's
outcome table. One program of the enforced formation set stays `AMBIGUOUS_TOPOLOGY`:
the thesis-gold negative `n2_khoi_ghep_bu_can_boolean`, a composite problem that is
refused at `structural_coverage` before and after this wave, so no learner sees its
formation (details and the open decision below). Track B also stopped
(`ASSUMPTION_POLICY_INCOMPLETE`). Automation only; nothing here is `MERGE_READY`.

## Identity

- Branch `fix/cuboid-visual-semantic-closure`, start **`ce9c672d`**; `origin/main`
  `a9492ee9` (fetched at the start: unchanged, ancestor of HEAD, ahead 115 / behind 0).
- Red tests first: `0daa6354` (portability, formation, assumption, trust, source length),
  `1a8ea7b8` (characterization of the five configurations that must not change).
- Product commits: `44f2dd32` (formation pass; frontend stage label) · `d537cf74`
  (trust policy) · `2f2c97b2` (length connector vocabulary) · `69d3c985` (sample text,
  frontend/src outside the measured paths) · `733435ac` (`CACHE_VERSION`) · `a2af56e4`
  (ponytail cleanup) — last product commit **`a2af56e4`**.
- Candidate `548f5b3b…` → **`40263983…`** (105 files), frozen **once** at `a2af56e4` in
  a clean detached worktree: **`380db58c`** = measurement commit. Declared in
  `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` and the living
  `product-response-contract-alignment/CANDIDATE_DIVERGENCE.json`.
- Evidence commit **`54af39a4`**; T3 from a path with a space at `380db58c`.
- `CACHE_VERSION` 105 → **106**, once (`733435ac`), decided by real rows
  (`diagnostics/PROOF_CACHE_ROW_W14.json`): under 105 the cache would replay a served
  envelope W14 refuses (*"AB dài 5 cm"* with `AC = 5` declared GIVEN) and a served LLM
  gold envelope with the old formation timeline (p1). Provider fingerprint
  `b1714b566e25c912` unchanged. `DEFAULT_MODE = LLM_ONLY`; 0 live Gemini requests;
  0 application LLM calls.

## What the reviewer rejected, and what changed

| Finding | Repair | Result |
|---|---|---|
| W12-H1/H2 — triangular pyramid and prism show only points → base → solid | Track A (`44f2dd32`): one shape-class completion pass `semantic_program/formation.py::hoan_thien_dung_hinh`, run by `route.verify_and_compile` and `pipeline._dung_scene3d` on compiler **and** LLM programs (S4, Q1 approved). For each `construct_solid` whose face table classifies as `PYRAMID_LIKE`/`PRISM_LIKE` it inserts the missing base/top faces, the height (only from a typed `perpendicular_line_plane` relation or a `project_onto` foot) and the lateral edges as real statements before the solid. Topology authority: contract topology → typed relation → unambiguous face table (leaf `solid_faces.py`); otherwise the solid is left alone with a status. Malformed face tables are refused at stage `formation` (`SOLID_TOPOLOGY_MALFORMED`). The compiler no longer hand-writes height/lateral/top statements. Roles are assigned at the producer (`simulation_state` → `gan_vai_tro_dung`); `scene3d` only carries `formation_roles`, `shape_class`, `formation_requirements` | Triangular pyramid: points · base ABC · SA (height and lateral, one object, one visual owner) · SB, SC · closed solid. Triangular prism: points · base ABC · top DEF · AD, BE, CF · closed solid. Six families × desktop/mobile role coverage PASS against an independent expectation; served gold p1/p2 completed with answers unchanged; cross-section sub-steps unchanged |
| W12-H3 — no family hardcode | The planner reads only typed data; an AST guard forbids family IDs, titles, problem text, label keys and `_length` names in `formation.py`/`solid_faces.py` | `test_planner_khong_re_nhanh_theo_ho` green |
| W12-H4 — the assumption channel is open | Track B: three-valued gate designed (C0/C1 certificates, validated counterexample, `UNDETERMINED` refuses), measured on a hand-labelled corpus committed **before** any mechanism ran | **STOP — `ASSUMPTION_POLICY_INCOMPLETE`**: 0 `PROVEN_SAFE` on DEPENDS rows and every AC1/adversarial/certificate-limit row refused, but **0/18** AC2 gold rows certified (C1 blocked: the six families' relations cite facts not confirmed as InputFacts; LLM gold/demo programs are not compiler-recognized). No gate shipped; the 16 gate tests are strict xfail citing `diagnostics/ASSUMPTION_MECHANISM_DECISION.json` |
| W13 NA-57 — *"AB dài 5 cm"* binds no segment | Track C (`2f2c97b2`): one closed connector vocabulary `segment_relation._NOI_DO_DAI` (`=`, `bằng`, `dài`, `có độ dài`) for the length reader and the GIVEN-evidence labeler (`nhan_doan_truoc`); public entity-bound `grounding_gate.bang_chung_doan` | Probe diff **exactly as registered**: `dai_cm` now reads AB = 5; `standalone_wrong_segment` refused `SOURCE_EVIDENCE_CONFLICT`; the other 23 rows identical (`diagnostics/SOURCE_GROUNDING_PHRASING_PROBE_W14.json`) |
| Plan R2 — an empty `problem_text` meant "unchecked" | `d537cf74`: `NguonDe.CAN_DE` by default; empty text ⇒ `SOURCE_TEXT_MISSING` at `grounding`, never sent to repair; only an explicit `NguonDe.FIXTURE_TIN_CAY` argument skips source checks and records `source_check = UNCHECKED_TRUSTED_FIXTURE`; not reachable from HTTP payloads, headers or model output | 20 test callers and 44 scripts classified one by one (`diagnostics/TRUST_POLICY_CALLERS.json`); 0 production references to `FIXTURE_TIN_CAY` |
| W13 NA-05 — a default test read `D:/tmp/...` | `0daa6354`: opt-in marker `external_evidence` + `ALGOSIM_LIVE_RETRY_EVIDENCE_DIR`; AST guard on absolute paths | default suite reads no path outside the repository |
| Q3 — the oblique-cylinder sample's answers used a radius its text did not state | `69d3c985`: the text states `OA = √5`; answers unchanged | sample test green |

## Formation status per program (at the measured product)

`diagnostics/S4_INVENTORY_AT_380db58c.json` (identical to the Task 4 inventory):

| Program | Status |
|---|---|
| six compiler families | `COMPLETED` |
| thesis gold p1 (cross-section), p2 (non-convex base) | `COMPLETED`, answers unchanged, p1 section progress unchanged |
| thesis gold **n2** (`n2_khoi_ghep_bu_can_boolean`) | **`AMBIGUOUS_TOPOLOGY`** — the box has no contract topology and no typed base relation, so three base choices remain and the pass does not guess (by design); refused at `structural_coverage` before and after |
| demo v2_04 `AMNP` | `AMBIGUOUS_TOPOLOGY` — demo replay without a contract, never routed in production (outside the enforced set) |
| offline samples with a pyramid | `COMPLETED` when replayed; the shipped sample JSON is static and not routed |
| curved and remaining programs | no polyhedral solid — untouched |

## Measurement

`diagnostics/MEASUREMENT_ATTEMPTS.json` lists every run; nothing was superseded.

1. **FREEZE-1** (`a2af56e4`): the single freeze, clean tree.
2. **BROWSER-1** (`380db58c`, detached clean worktree, `npm ci --offline`): PASS.
3. **OCCLUSION-1**: product = oracle on 24/24 states; the frozen human expectations
   transfer for cuboid and cube and **stop at `SCENE_GEOMETRY_CHANGED`** for the
   triangular pyramid, triangular prism, rectangular pyramid and cross-section — S4 adds
   drawn objects to the scenes a person reviewed (and Q1 renames the rectangular
   pyramid's lateral IDs). The gate result is kept as measured (`pass = false`);
   the registry is untouched.
4. **OCCLUSION-DIAG-1**: for those four records the independent oracle reproduces the
   reviewed visible/hidden sets 4/4 at the registered and at the new camera; the
   drawn-geometry difference is exactly the S4 insertions. Known answer: one reviewed edge
   moved ⇒ `REVIEWED_SETS_DIFFER` 4/4. No visibility regression measured; the four scenes
   need human re-review.
5. **SECTION-DIAG-1**: cross-section sub-steps equal w12's in every field S4 does not
   change by construction (5/5; five injected faults caught).
6. **PLAYBACK-1**, **BUILDER-1**, **T3-1**, **GATES-1**, **S4-INVENTORY-2**: below.

## Final verification

| Gate | Result |
|---|---|
| T3 `full-gate.mjs` from a path WITH a space (`380db58c`) | `FULL_PRODUCT_GATE_PASS` — pytest **6564 passed / 0 failed** (1 skipped, 2 deselected opt-in, 16 xfailed = the recorded Track B strict xfails) · vitest 1010/1010 (67 files) · typecheck + build · thesis demo · demo crash surface |
| Browser suite, 6 families × desktop 1440×900 + mobile 390×844 | 12/12 positive, 12/12 ungrounded negative (refused, no canvas, no answer); `FORMATION_ROLE_COVERAGE` 12/12 for the enforced classes (PYRAMID_LIKE; PRISM_LIKE; cross-section SECTION + PYRAMID_LIKE); no structured reference left unrendered; 0 raw tokens, 0 serious console errors, 0 uncaught exceptions, 0 failed API calls, no document overflow on any of the 24 runs |
| Occlusion | product = oracle 24/24; frozen expectations 2/6 transfer, 4/6 `SCENE_GEOMETRY_CHANGED` (gate red by design — see above) |
| Learner playback | 12/12 runs × 19/19 checks (every geometry step changes the figure, final result shown once, forward/backward), orbit 5 laps per run |
| Crops · sheets · filmstrips | 64 crops, endpoints inside, 0 oracle disagreements, 0 duplicate owners; `SHEET.png` and role-captioned `FILMSTRIP.png` per family |
| Candidate · cache · schema · mode | `--verify` PASS (`40263983…`, product commit `a2af56e4`) · `CACHE_VERSION 106`, fingerprint `b1714b56…` · schema exported twice, both mirrors `d852b47c…`, no diff · `LLM_ONLY`, compiler not wired, `FIXTURE_TIN_CAY` absent from production paths |
| `git diff --check ce9c672d..380db58c` · node harness | clean (verbatim logs excluded) · 42 pass + 2 skipped by design in a worktree without a local venv (44/44 in the main tree) |
| Ponytail review | 3 SIMPLIFY_NOW + 1 SAFE_TO_DELETE applied (net −10 lines), 2 REQUIRED_KEEP, 1 OUT_OF_SCOPE (`diagnostics/PONYTAIL_REVIEW.json`) |

## Limitations (not hidden)

- **No human has looked at the new formation.** The filmstrips and sheets are for that
  review; the four scenes whose hidden-line expectation could not be transferred need
  it in particular.
- **n2 decides the headline.** If a refused program, whose formation no learner sees,
  is outside the enforced set — the pre-product S4 test enforced only the served gold
  programs p1 and p2 — the outcome table's first match becomes
  `ASSUMPTION_POLICY_INCOMPLETE`. The written rule is applied here; the choice is the
  user's (`HANDOFF.md`).
- **Track B is not shipped.** `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION` stays
  OPEN: a layout or `model_assumption` coordinate can still fix a dimension the text does
  not state. The census is a corpus result inside the certificate scope (C0 ∪ C1 over
  `PHEP_DO_C1`), not a general soundness proof; the counterexample search also produced
  11 false counterexamples on invariant rows.
- **Height needs a typed foot.** A height whose foot is a derived point not yet built
  (centre of the base, foot not declared) gets no height step (declared limitation,
  tested).
- Curved-solid formation, regular solids, frustum, multi-solid and OCR are out of
  scope; `ISSUE-OPS-OFFLINE-SAMPLES-STALE` and `ISSUE-OPS-DIST-ACL-OWNERSHIP` remain
  open (the main-tree `npm run build` still fails with `EPERM`; every build here ran in
  a fresh worktree).
- Deviations from the plan, each ruled in the execution ledger: the frozen human
  expectations could not be transferred (plan assumed they would); "section sub-steps
  byte-equal" checked field by field; the suite built `dist` itself; the n2 reading of
  the enforced set.
