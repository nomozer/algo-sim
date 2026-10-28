# Implementation & Verification Plan — Hybrid V2 W2-M4 Exact Radical Normalization (`hybrid-v2-w2-m4-exact-radical-normalization`)

- **Task:** `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION`
- **Branch:** `research/hybrid-v2-w2-m4-exact-radical-normalization`
- **Worktree:** `.superpowers/worktrees/w2-m4-exact-radical-normalization`
- **Parent / Baseline HEAD (`research/hybrid-v2-wave2-source-gate-language-generalization`):** `d99f6149ff1997258970bf888db5484665b106b8`
- **Parent Product Commit:** `c6f6b64bda6473c175a32a7875a9dd9831ae7c6d` (Frozen Candidate `b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9`, 118 files, tree hash `8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25`)
- **Authoritative `main = origin/main`:** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Parent Wave Historical Verdict (Preserved Unchanged):** `NOT_READY_ACCEPTANCE_GATE_FAILED` (`ACCEPTANCE-1` open MAJOR on `DEV-1-3`)

---

## 1. Mission & Scope Boundaries

1. **Mission:** Resolve `W2-M4: RADICAL_DOMAIN_OVERFLOW` by implementing exact mathematical normalization before enforcing the canonical radicand complexity ceiling (`MAX_RADICAND = 10**12`) in `backend/app/simulation/geometry/radical.py`, thereby repairing both mandatory failing cases (`DEV-1-3` and `W2-A04`) with exact mathematical verification and closing `ACCEPTANCE-1` that caused Full T3 to fail in the Source Gate `/19` wave.
2. **Strict Scope Boundaries:**
   - **Allowed product modifications:** `backend/app/simulation/geometry/radical.py` only, plus directly related unit/regression tests and evaluation candidate freeze metadata (`EVALUATION_CANDIDATE.json`).
   - **Forbidden modifications:**
     - Do **not** modify `Registry /19` (`backend/app/simulation/geometry_functions/registry.py`) or Source Gate logic.
     - Do **not** modify `Planner /17` (`planner.py`), `Engine /14` (`engine.py`), or `Adapter /4` (`adapter4_route.py`, including out-of-scope `W2-M5` on `W2-A07`/`W2-A10`).
     - Do **not** modify OCR, LLM schema/prompt, source/derived provenance, Scene3D visual semantics, or default production routing (`DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 130`, `ALLOW_LIVE_AI = 0`).
     - Do **not** increase `MAX_RADICAND` arbitrarily or disable resource/complexity guards.
     - Do **not** use floating-point operations (`float`, `math.sqrt`, `** 0.5`, `round`) anywhere in the exact radical domain.
     - Do **not** alter historical receipts, verdicts, or locked evaluation corpora.
     - Do **not** merge to `main`, push, or delete worktrees.

---

## 2. Execution Phases

1. **Phase 1 — Preflight, Kernel Diagnosis & Architectural Decision (Pre-Code):**
   - Verify Git ancestry (`d7a94d3c -> c6f6b64b -> b9e3d096 -> d99f6149`) and product freeze (`8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25`, `118` files).
   - Trace the exact call stack and mathematical factorization of `DEV-1-3` (`area_squared = 38130625/58564`) and `W2-A04` (`area_squared = 253125000/485809`).
   - Author `baseline-audit.md` answering all 5 diagnostic questions in Section 3 with exact mathematical proof.
   - Author `architecture-decision.md` specifying the exact normalization invariants, complexity bounds, and fail-closed boundary conditions.
2. **Phase 2 — Preregistered RED Baseline & Verification Corpus (Pre-Code):**
   - Author `inputs/development.json` with independent exact-arithmetic oracles covering:
     - Mandatory end-to-end cases `DEV-1-3` and `W2-A04` (expected `SERVED` with exact section boundary, certificate category, area squared, and canonical radical display/structure).
     - Exact kernel cases: integers, reduced fractions, perfect-square rationals with $p \cdot q > 10^{12}$, non-square rationals with $p, q \le 10^{12}$ and $p \cdot q > 10^{12}$, zero, negative signs, and $\pi$ exponents.
     - Boundary cases around `MAX_RADICAND = 10**12` (canonical squarefree radicand $= 10^{12} - 1$, reducible radicands $> 10^{12}$ with squarefree core $\le 10^{12}$, and irreducible/squarefree radicands $> 10^{12}$).
     - Metamorphic equivalence pairs verifying that distinct intermediate radical paths (`sqrt_rational(p/q)`, `radical(Fraction(1, q), p*q)`, `multiply(sqrt_rational(p), divided_by_rational(F(1), sqrt_rational(q)))`, `multiply` with shared large prime factors) produce identical canonical `ExactNumber` objects (`==`, `hash`, `to_json`, `square`, `display`).
     - Negative fail-closed cases (`can <= 0`, `x < 0`, squarefree radicand $> 10^{12}$ such as `MAX_RADICAND + 1` and prime $10^{12} + 39$, unreduced input $> \text{MAX\_RADICAND}^2 = 10^{24}$, $\sqrt{2} + \sqrt{3}$, $\pi^2$, division by zero).
   - Execute and freeze `results/red-before.json` before modifying `backend/app/simulation/geometry/radical.py`.
3. **Phase 3 — Minimal Exact Radical Normalization Implementation:**
   - Update `backend/app/simulation/geometry/radical.py`:
     - `_tach_binh_phuong(n)`: exact integer square-root check (`math.isqrt`), factor-2 extraction, and odd trial division bounded by `d * d * d <= m and d * d <= MAX_RADICAND` with squarefree accumulator `sf`, early `isqrt` termination after each factor extraction, early overflow abort when `sf * d > MAX_RADICAND`, and post-loop canonical ceiling enforcement (`m <= MAX_RADICAND` and `sf * m <= MAX_RADICAND`).
     - `radical(he, can, mu)`: normalize `can` via `_tach_binh_phuong(can)` before returning `Fraction(0)` (when `he == 0`), `he * k` (when `m == 1 and mu == 0`), or `Radical(he * k, m, mu)`.
     - `sqrt_rational(x)`: extract square factors from reduced numerator $p$ and denominator $q$ separately (`kp, mp = _tach_binh_phuong(p)` and `kq, mq = _tach_binh_phuong(q)`) before forming `radical(Fraction(kp, kq * mq), mp * mq)`.
     - `multiply(a, b)`: extract $g = \gcd(c_a, c_b)$ into the rational coefficient `ha * hb * g` before passing `(ca // g) * (cb // g)` to `radical`.
   - Add unit tests in `backend/tests/geometry/test_radical_domain.py` covering `DEV-1-3`, `W2-A04`, boundary cases, metamorphic equivalences, and fail-closed overflow cases.
4. **Phase 4 — GREEN Verification & Full Regressions:**
   - Record `results/green-after.json` (confirming `100%` pass across all end-to-end, kernel, boundary, metamorphic, and negative cases).
   - Execute the full locked Source Gate `/19` development corpus and record `results/source-gate-regression.json` (`24/24` original positives served-correct, `36/36` genuine negatives refused, `0` genuine wrong-served).
   - Execute the full 96-case Holdout Wave 2 corpus (`POST_FEEDBACK_DEVELOPMENT_REGRESSION`) and record `results/wave2-post-feedback-regression.json` (`46/48` positive `SERVED_CORRECT` including `W2-A04`, `2/48` remaining false refusals on out-of-scope `W2-M5` cases `W2-A07`/`W2-A10`, `48/48` negatives refused, `0/96` wrong-served).
5. **Phase 5 — T0/T1/T2, Candidate Freeze, Clean Detached Full T3 & Independent Review:**
   - Run T0, T1, T2 and record `verification/tiers.json`.
   - Commit product + test changes, run `freeze_evaluation_candidate.py --write`, create a clean detached worktree at the candidate commit, and run Full T3 (`verification/full-t3/receipt.json` and `verification/full-t3/full-t3.log`), verifying `FULL_PRODUCT_GATE_PASS` (`0` failed backend tests, including `test_source_language_product_outcome[DEV-1-3]` passing) and post-T3 `freeze_evaluation_candidate.py --verify` (`MATCH`).
   - Run publication safety checks.
   - Invoke an independent review subagent to audit the repair against all 8 Section 8 criteria and write `review.md`.
   - Write `report.md`, `handoff.md`, and `run.json`, commit all evidence on `research/hybrid-v2-w2-m4-exact-radical-normalization`, and report `READY_FOR_OWNER_REVIEW`.
