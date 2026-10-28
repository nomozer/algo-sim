# Execution Plan — `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`

- **Task ID:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Wave Type:** Preregistered Blinded Offline Evaluation Wave (`evaluation-only`)
- **Authoritative Baseline (`main = origin/main = remote`):** `e137623c4f674135a8d7884b78614c132eb78085`
- **Product Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`
- **Frozen Full T3 Candidate:** `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`
- **Measured Product System (`118` files):** `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`MATCH`)
- **Isolated Research Branch:** `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3`
- **Isolated Worktree:** `.superpowers/worktrees/independent-section-holdout-wave3`
- **Run Directory:** `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/`
- **Architecture Versions:**
  - Registry: `geometry-functions/19`
  - Planner: `geometry-fact-planner/17`
  - Engine: `geometry-function-engine/14`
  - Adapter: `hybrid-simulation-adapter/4`
  - Certificate: `plane-section-certificate/1`
  - `CACHE_VERSION = 130`
  - `DEFAULT_MODE = LLM_ONLY`
  - `ALLOW_LIVE_AI = 0` (`0` live provider calls)

---

## Phase Gates & Execution Order

### Gate 1 — Preflight & Historical Corpus Quarantine (Completed)
1. Verified `main == origin/main == remote == e137623c4f674135a8d7884b78614c132eb78085`.
2. Verified `freeze_evaluation_candidate.py --verify` returns `MATCH` (`118` files, `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`).
3. Created isolated worktree `.superpowers/worktrees/independent-section-holdout-wave3` on branch `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3`.
4. Quarantined all previously opened corpora (`POST_FEEDBACK_DEVELOPMENT_REGRESSION`):
   - Independent Holdout Wave 1 (`H001..H084`, `84` cases)
   - Independent Holdout Wave 2 (`W2-B01..B36, W2-A01..A12, W2-N01..N48`, `96` cases)
   - W2-M1/M2/M3 holdout failure repair development corpus (`D001..D016, N001..N016`, `32` cases)
   - Source Gate `/19` development corpus (`34` cases)
   - W2-M4 Exact Radical Normalization development corpus (`10` cases)
   - W2-M5 Adapter `/4` Category A Identity Repair development & tamper corpus (`26` cases)
   - All existing backend test fixtures (`backend/tests/**`) and committed evaluation runs (`docs/evaluation/geometry/runs/**`).

### Gate 2 — Preregistration & Scorer Qualification Commit (Before Any Corpus Authoring)
1. Author and commit:
   - `plan.md`
   - `preregistration.md`
   - `supported-family-matrix.md`
   - `scoring-contract.md`
   - `refusal-taxonomy.json`
   - `curator-brief.md`
   - `tools/evaluate_holdout_wave3.py` (Wave 3 evaluator with upgraded polygon-index bijection resolution, primed-label normalization, 5+ vertex polygon support, and zero-fallback prohibition)
   - `tools/test_evaluate_holdout_wave3.py` (all 22 mandatory synthetic control categories + systematic mutation controls)
   - `tools/dedup_check_wave3.py` (9-dimensional + symmetry/scale/relabelling deduplication auditor)
   - `tools/audit_curator_log.py` (Curator subagent transcript firewall auditor)
   - `verification/scorer-qualification-receipt.json`
2. Run `pytest` on `tools/test_evaluate_holdout_wave3.py` and verify 100% pass rate before spawning the Curator.
3. Commit Gate 2 and lock the preregistration + scorer commit SHA.

### Gate 3 — Blinded Corpus Authoring & Exact Independent Oracle (`144` Cases)
1. Spawn an isolated Curator subagent under the strict file-access firewall defined in `curator-brief.md` to author:
   - `inputs/holdout-wave3.json` (`144` cases = `54` Category B `W3-B01..W3-B54` + `18` Category A `W3-A01..W3-A18` + `72` Negative `W3-N01..W3-N72`)
   - `oracle/geometry.json` (`72` positive cases in exact rational 3D coordinates)
   - `oracle/oracle_holdout_wave3.py` (pure `fractions.Fraction` exact 3D geometry oracle with `0` imports from `app.*`)
   - `oracle/expected.json`
   - `curator-attestation.md`
   - `corpus-provenance.md`
2. Audit the Curator's tool-access transcript via `tools/audit_curator_log.py` -> `verification/independence-audit.json`.
3. Run `tools/dedup_check_wave3.py` -> `verification/deduplication-audit.json`.
4. Spawn an Independent Oracle Reviewer subagent to recompute all `72` positive oracle cases from scratch in exact rational arithmetic -> `verification/independent-oracle-review.md` and `verification/independent-oracle-review.json`.

### Gate 4 — Pre-Execution Freeze Commit
1. Generate `holdout-manifest.json` locking SHA-256 digests of the frozen product (`1170ca16...`), preregistration, scoring contract, refusal taxonomy, scorer, 144-case corpus, exact oracle, deduplication audit, independence audit, and independent oracle review.
2. Commit the pre-execution freeze on `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3` and verify all SHA-256 digests before executing the product.

### Gate 5 — One-Shot Scored Execution, Independent Evaluation Review & Final Report
1. Execute `tools/evaluate_holdout_wave3.py` exactly once (`results/scored-run-1/`).
2. Generate diagnostics and statistical summary with 95% Wilson confidence intervals.
3. Spawn an Independent Evaluation Reviewer subagent to verify all artifacts, hashes, firewall logs, and statistical tables (`review.md`).
4. Write `report.md`, `handoff.md`, `run.json`, update `docs/EVIDENCE_INDEX.md`, `docs/CURRENT_STATE.md`, `docs/CODE_INDEX.md` in the isolated worktree, verify `audit_docs_information_architecture.py` and `check_publication_safety.py`, and commit on `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3`.
