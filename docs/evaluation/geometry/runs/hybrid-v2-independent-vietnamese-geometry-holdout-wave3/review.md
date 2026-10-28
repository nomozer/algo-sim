# Independent Evaluation Review — `hybrid-v2-independent-vietnamese-geometry-holdout-wave3`

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Reviewer Role:** Independent Holdout Wave 3 Evaluation Reviewer (Section 11 of Owner GO)
- **Run Directory:** `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3`
- **Branch:** `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3`
- **Authoritative Baseline (`main = origin/main`):** `e137623c4f674135a8d7884b78614c132eb78085`
- **Product Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`
- **Product Freeze Tree Hash (`118` files):** `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`MATCH`)
- **Findings (`CRITICAL` / `HIGH` / `MEDIUM` / `LOW`):** `NONE` (`0` open findings; 2 clerical table transcription cells in untracked `report.md` reconciled during review to match `statistical-summary.json` and `diagnostics.json`)
- **Final Review Verdict:** `APPROVED_NO_FINDINGS` / `INDEPENDENT_HOLDOUT_WAVE3_REVIEW_PASS`

---

## 1. Product Freeze & Scope Integrity Audit

| Check | Command / Evidence | Observed Result | Verdict |
|---|---|---|---|
| Frozen evaluation candidate verification | `python backend/scripts/freeze_evaluation_candidate.py --verify` | `Candidate khớp bản đã đóng băng (mã sản phẩm: 118 file, 1170ca163529dd4058826db92a6433359546aa2ad718712f38a538c10d)` | `PASS` |
| Product code diff against `e137623c4f674135a8d7884b78614c132eb78085` | `git diff e137623c4f674135a8d7884b78614c132eb78085 -- backend/app frontend/src` | Empty (`0` changed files, `0` changed lines) | `PASS` |
| `backend/app` Git tree hash | `git rev-parse HEAD:backend/app` | `29eb33d0e767069ce9d6557e7da8532644ceee7c` | `PASS` |
| Offline execution discipline | `results/scored-run-1/summary.json` & `holdout-manifest.json` | `ALLOW_LIVE_AI = "0"`, `live_provider_calls = 0` | `PASS` |
| Branch & integration safety | `git status` / `git branch` | On isolated worktree branch `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3`; no merge into `main`, no remote push | `PASS` |

---

## 2. Chronological Phase Gates & Pre-Execution Freeze Audit

Git commit history on `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3` strictly enforces the preregistered phase order prior to product execution:

| Phase Gate | Commit SHA | Verified Contents | Post-Gate Immutability Check | Verdict |
|---|---|---|---|---|
| **Baseline (`main`)** | `e137623c4f674135a8d7884b78614c132eb78085` | W2-M5 post-merge baseline (`73ca8d92e74059680ce53b99692af396df37a2f8` product code) | Unchanged | `PASS` |
| **Gate 1 — Preregistration & Scorer Infrastructure** | `f438a62a3485ce9b8d687cb91102c366e6848960` | `plan.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `refusal-taxonomy.json`, `curator-brief.md`, `tools/evaluate_holdout_wave3.py`, `tools/test_evaluate_holdout_wave3.py`, `tools/dedup_check_wave3.py`, `tools/audit_curator_log.py` committed **before** any corpus case existed | Verified via `git diff-tree` | `PASS` |
| **Gate 2 — Scorer Qualification Receipt** | `53cba0c8a63ae3cf7c1b058b8b09f07046449f06` | `verification/scorer-qualification-receipt.json` (`24/24` suites PASS, `10/10` mutations killed) committed **before** any corpus case existed | Verified via `git diff-tree` | `PASS` |
| **Gate 3 & Gate 4 — Blinded Corpus, Independent Oracle Review & Pre-Execution Freeze** | `2332f7ad3d1a73733bbc720bcf36705c67bc2d6b` | `inputs/holdout-wave3.json`, `oracle/geometry.json`, `oracle/oracle_holdout_wave3.py`, `oracle/expected.json`, `curator-attestation.md`, `corpus-provenance.md`, `verification/independence-audit.json`, `verification/deduplication-audit.json`, `verification/independent-oracle-review.json`, `verification/independent-oracle-review.md`, and `holdout-manifest.json` committed **before** product execution | Verified `0` bytes changed across all `18` manifest files (`git diff 2332f7ad3d1a73733bbc720bcf36705c67bc2d6b` empty and SHA-256 / SHA-256-LF exact match) | `PASS` |

---

## 3. Scorer Qualification & Independent Oracle Verification

1. **Scorer Qualification (`tools/test_evaluate_holdout_wave3.py`):**
   - Re-executed `pytest docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/tools/test_evaluate_holdout_wave3.py -v`: **`24 passed in 0.17s`**.
   - Verified all 22 mandatory positive/negative/tamper controls, the explicit W2-A10 non-zero fallback guard (`test_23_unfound_vertex_never_defaults_to_polygon_index_zero`), and the 10-mutation systematic kill suite (`test_24_systematic_mutation_kill_suite`, `10/10` killed, `0%` survival).
2. **Standalone Rational Oracle (`oracle/oracle_holdout_wave3.py`):**
   - Re-executed `python docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/oracle/oracle_holdout_wave3.py --check`: **`OK: verified 72 positive cases`**.
   - Confirmed zero imports from `backend.app.*`; all 3D plane equations, edge intersections, cyclic polygon orderings, and `area_squared` values are computed in exact `fractions.Fraction` arithmetic.
3. **Pre-Execution Independent Oracle Review (`verification/independent-oracle-review.json` & `.md`):**
   - Verified that subagent `9fdf8f17-aeaf-4fd3-8530-34c02d1363c2` independently synthesized 3D coordinates from problem premises, verified Euclidean isometry across all $\binom{V}{2}$ pairwise squared distances, recomputed all `72` positive sections and `area_squared` values, and audited all `72` negative cases before product execution (`status: "ORACLE_VERIFIED_BEFORE_EXECUTION"`, `discrepancies: []`).

---

## 4. Procedural Independence & 9-Dimensional Deduplication Audit

1. **Curator Firewall Audit (`verification/independence-audit.json`):**
   - Subagent Curator (`206cf35f-d6b5-4ac4-a16a-38ae2ced52d1`) executed `68` tool calls and read only the `8` allowed specification/contract files (`AGENTS.md`, `docs/RULES.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `curator-brief.md`, `refusal-taxonomy.json`, `typed_fact_next.py`) plus its own newly written Wave 3 files.
   - `forbidden_reads = []`, `forbidden_commands = []`, `human_or_institutional_independence_claimed = false`, `independence_class = "AI_CURATED_PROCEDURAL_INDEPENDENCE"`, `status = "HOLDOUT_INDEPENDENCE_ESTABLISHED"`.
2. **9-Dimensional Semantic Deduplication (`verification/deduplication-audit.json`):**
   - Audited all `144` Wave 3 cases against `940` historical items across Wave 1, Wave 2, W2-M1..M5, backend test fixtures, and internal pairwise comparisons across all 9 required dimensions (normalized text, character 5-gram Jaccard, solid topology, cutting-plane relation & roles, dihedral vertex-relabelling invariance, projective scale invariance, cut-ratio profile, question objective, and oracle solution invariance).
   - Verified pre-freeze replacement transparency in `corpus-provenance.md §2.2`: initial candidate `W3-B01` triggered `external_scale_invariant_flags` before freeze and was replaced prior to Gate 4 under the same procedural firewall (`S.EFG` with lengths `(13, 19, 23)` and ratio `3/11`).
   - Final frozen corpus deduplication metrics: `passed = true`, `max_external_5gram_jaccard = 0.6713 < 0.75`, `max_internal_5gram_jaccard = 0.7153 < 0.80`, `max_internal_positive_5gram_jaccard = 0.7153 < 0.75`, and `0` flags across all 5 flag arrays.

---

## 5. Cross-Artifact Quantitative & Failure-Analysis Audit

All counts, percentages, and 95% Wilson confidence intervals were independently recomputed and cross-checked across `results/scored-run-1/summary.json`, `results/scored-run-1/track-a.json`, `results/scored-run-1/track-b.json`, `results/statistical-summary.json`, `results/diagnostics.json`, `report.md`, and `handoff.md`:

| Metric | Verified Count | Rate (%) | Verified 95% Wilson CI | Cross-Artifact Consistency |
|---|---:|---:|---|---|
| **Overall Positive Serve Accuracy (`SERVE`)** | `20 / 72` | `27.78%` | `[18.76%, 39.05%]` | Exact match across all artifacts |
| **Stratum `P-B` (Category B) Serve Accuracy** | `12 / 54` | `22.22%` | `[13.20%, 34.94%]` | Exact match across all artifacts |
| **Stratum `P-A` (Category A) Serve Accuracy** | `8 / 18` | `44.44%` | `[24.56%, 66.28%]` | Exact match across all artifacts |
| **Single-Question Positive Accuracy (`section_only` + `area_only`)** | `20 / 48` | `41.67%` | `section_only`: `10/24` (`[24.47%, 61.17%]`), `area_only`: `10/24` (`[24.47%, 61.17%]`) | Exact match across all artifacts |
| **Compound-Question Positive Accuracy (`section_and_area`)** | `0 / 24` | `0.00%` | `[0.00%, 13.80%]` | Exact match across all artifacts |
| **Exact Oracle Agreement Given Served (`SERVED_CORRECT / SERVED`)** | `20 / 20` | `100.00%` | `[83.89%, 100.00%]` | Exact match across all artifacts |
| **Downstream `Planner /17 -> Engine /14 -> Adapter /4` Success Given Source Gate Pass on Positive** | `20 / 20` | `100.00%` | `[83.89%, 100.00%]` | Exact match (`0` `RADICAL_DOMAIN_OVERFLOW`, `0` Category A `PREVIEW_RESULT_INVALID`) |
| **False Refusal Rate on Positive (`FALSE_REFUSAL`)** | `52 / 72` | `72.22%` | `[60.95%, 81.24%]` | Exact partition into `W3-F1` (`24`), `W3-F2` (`14`), `W3-F3` (`10`), `W3-F4` (`3`), `W3-F5` (`1`) |
| **Negative Fail-Closed Refusal Rate (`REFUSE`)** | `72 / 72` | `100.00%` | `[94.93%, 100.00%]` | Exact match across all artifacts |
| **Negative Refusal Reason Agreement (`REFUSED_CORRECT_REASON`)** | `60 / 72` | `83.33%` | `[73.09%, 90.20%]` | Exact match (`12` `REFUSED_REASON_DISAGREEMENT` documented in `diagnostics.json`) |
| **Wrong-Served Rate Overall (`WRONG_SERVED`)** | `0 / 144` | `0.00%` | `[0.00%, 2.60%]` | Exact match (`0/72` positive, `0/72` negative) |
| **Track B Contract Representability** | `72 / 64 / 8` | `50.0% / 44.4% / 5.6%` | N/A | Exact match (`72` without loss, `64` with explicit gap, `8` outside capability) |
| **Track C Scene3D Semantics Clean Rate** | `20 / 20` | `100.00%` | `[83.89%, 100.00%]` | `0` `_prime` leaks, `0` source identity leaks, `20/20` auxiliary points visibly distinguished |
| **Uncaught Product Exceptions / Harness Errors** | `0 / 144` | `0.00%` | `[0.00%, 2.60%]` | Exact match across all artifacts |

### Verification of Post-Wave-2 Repairs & Root-Cause Honesty
- **W2-M4 (Exact Radical Normalization):** Verified `0 / 72` `RADICAL_DOMAIN_OVERFLOW` failures despite prime-heavy dimensions and large rational `area_squared` denominators.
- **W2-M5 (Adapter `/4` Category A Identity & Primed-Vertex Repair):** Verified `8 / 8` (`100%`) Category A positive cases passing `Source Gate` (including primed top vertices `A'`, `B'`) were served with exact oracle agreement and `0` `PREVIEW_RESULT_INVALID` false refusals, while `2` adversarial non-closed Category A negative cases (`W3-N54`, `W3-N55`) were rightly caught by Adapter `/4` with `PREVIEW_RESULT_INVALID`.
- **Source Gate (`kiem_nguon`) Bottleneck Diagnosis:** All `52` positive false refusals occur in `SOURCE_GROUNDING` (`W3-F1`: `24` `SOURCE_OBJECT_MISMATCH` on two-sentence `section_and_area` prompts; `W3-F2`: `14` `PREDICATE_NOT_IN_QUOTE` on `'thỏa mãn'`/`'với'` and `'chân đường cao'`; `W3-F3`: `10` `SOURCE_PREMISE_UNREAD` on `parallel_two_lines` slice grammar; `W3-F4`: `3` `UNGROUNDED_VALUE` on cube base-square edge phrasing; `W3-F5`: `1` `CONDITIONAL_CLAUSE` on `'Giả sử'`). During review, 2 minor cell transcription typos in untracked `report.md` (Section 4.2 `P-B`/`P-A` subcounts for `perpendicular_line` `5/18, 6/11` and `parallel_plane` `5/18, 2/5`, and Section 6 `W3-F3` case list `W3-B08` vs `W3-B25`) were reconciled directly against `statistical-summary.json` and `diagnostics.json`.

---

## 6. Final Verdict

- **Findings:** `NONE`
- **Review Status:** `APPROVED_NO_FINDINGS` / `INDEPENDENT_HOLDOUT_WAVE3_REVIEW_PASS`
