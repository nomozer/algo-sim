# Evaluation & Verification Report — Hybrid V2 W2-M4 Exact Radical Normalization (`hybrid-v2-w2-m4-exact-radical-normalization`)

- **Task:** `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION`
- **Branch:** `research/hybrid-v2-w2-m4-exact-radical-normalization`
- **Worktree:** `.superpowers/worktrees/w2-m4-exact-radical-normalization`
- **Authoritative `main = origin/main`:** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Parent Baseline (`research/hybrid-v2-wave2-source-gate-language-generalization`):**
  - Final HEAD: `d99f6149ff1997258970bf888db5484665b106b8`
  - Product commit: `c6f6b64bda6473c175a32a7875a9dd9831ae7c6d`
  - Frozen T3 candidate: `b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9` (`8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25`, `118` files)
  - Historical verdict (preserved untouched): `NOT_READY_ACCEPTANCE_GATE_FAILED` (`ACCEPTANCE-1` open MAJOR on `DEV-1-3`)
- **Preregistered RED Commit:** `574ad40ca446232bf54e8e26cda196eee943fcb3`
- **Product Repair Commit:** `051224ee2740cbf5d55dd94633503db1f0050ada`
- **Frozen Full T3 Candidate:** `1e0c8db668bbe110f343a8a67cdeca465008c188`
- **Measured Product System:** `118` files, tree SHA-256 `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`
- **Product Files Modified (`d99f6149..1e0c8db6`):** `backend/app/simulation/geometry/radical.py` (`1` file only)
- **Component Versions & Cache Identity:**
  - `REGISTRY_VERSION`: `geometry-functions/19` (unchanged from `d99f6149`)
  - `PLANNER_VERSION`: `geometry-fact-planner/17` (unchanged)
  - `ENGINE_VERSION`: `geometry-function-engine/14` (unchanged)
  - `ADAPTER_V4_VERSION`: `hybrid-simulation-adapter/4` (unchanged)
  - `PLANE_SECTION_CERTIFICATE_VERSION`: `plane-section-certificate/1` (unchanged)
  - `CACHE_VERSION`: `130` (`NO_BUMP`)
  - `DEFAULT_MODE`: `LLM_ONLY` (Hybrid opt-in only)
  - `live_provider_calls`: `0` (`ALLOW_LIVE_AI=0`)
- **Final Wave Verdict:** `READY_FOR_OWNER_REVIEW`

---

## 1. Root-Cause Diagnosis & Exact Mathematical Normalization

### 1.1 Why `DEV-1-3` and `W2-A04` Failed at Baseline (`d99f6149`)

In `backend/app/simulation/geometry/radical.py`, `sqrt_rational(x)` computes $\sqrt{p/q} = \frac{1}{q}\sqrt{p \cdot q}$ by calling `radical(Fraction(1, q), p * q)`. In the baseline implementation, `radical()` enforced `if can > MAX_RADICAND:` ($10^{12}$) on the **unreduced** integer `can = p * q` before `_tach_binh_phuong(can)` extracted square factors:

| Mandatory Case | Solid & Inputs | Exact `area_squared` ($p / q$) | Unreduced $p \cdot q$ | Prime Factorization of $p \cdot q$ | Canonical Squarefree Core $m$ | Canonical Exact Area |
|---|---|---|---|---|---|---|
| `DEV-1-3` | Triangular pyramid `T.EFG` ($EF=13$, $EG=19$, $TE=11$, $TJ/TE=5/11$) | $\frac{38130625}{58564} = \frac{6175^2}{242^2}$ | $2,233,081,922,500 > 10^{12}$ | $(2 \cdot 5^2 \cdot 11^2 \cdot 13 \cdot 19)^2 \cdot 1$ | $1$ | `Fraction(6175, 242)` (`6175/242`) |
| `W2-A04` | Quadrilateral pyramid `S.ABCD` ($AB=6$, $AD=8$, $SA=10$, plane through $A \perp SC$) | $\frac{253125000}{485809} = \frac{2 \cdot 11250^2}{697^2}$ | $122,970,403,125,000 > 10^{12}$ | $(2 \cdot 3^2 \cdot 5^4 \cdot 17 \cdot 41)^2 \cdot 2$ | $2$ | `Radical(Fraction(11250, 697), 2, 0)` (`11250√2/697`) |

### 1.2 Exact Normalization Design (`051224ee`)

1. **Single Normalization Authority in `radical()` & `_tach_binh_phuong(n)`:**
   - `sqrt_rational(x)` continues to delegate directly to `radical(Fraction(1, q), p * q)`.
   - `radical(he, can, mu)` calls `k, m = _tach_binh_phuong(can)` **before** checking `he == 0` or `m == 1`, enforcing `m <= MAX_RADICAND` on the canonical squarefree core $m$.
2. **Bounded Cube-Root + `isqrt` Squarefree Reduction with Schoolbook Factor Base $B = \lfloor \text{MAX\_RADICAND}^{1/3} \rfloor = 10^4$:**
   - Hard input guard: $n \le 0$ or $n > \text{MAX\_RADICAND}^2 = 10^{24}$ fails closed in $O(1)$ time.
   - For $1 \le n \le \text{MAX\_RADICAND} = 10^{12}$: any prime $p > 10^4$ with $p^2 \mid n$ has cofactor $n / p^2 < 10^{12} / 10^8 = 10^4$, so stripping prime factors $d \le 10^4$ leaves $m = p^2$, which is caught in $O(1)$ time by `math.isqrt(m)`. Thus **every** integer $1 \le n \le 10^{12}$ is reduced completely in at most $5,000$ odd steps.
   - For $10^{12} < n \le 10^{24}$: square-factor extraction is bounded to the schoolbook prime factor base $d^3 \le \text{MAX\_RADICAND}$ ($d \le 10^4$, with `isqrt(m)` folding $r$ only when $r^3 \le \text{MAX\_RADICAND}$). Across all 163 cases in Source Gate `/19` and Holdout Wave 2, the largest prime factor of $k$ is $41 \ll 10^4$, so `DEV-1-3` and `W2-A04` reduce in $\le 7$ steps. Conversely, decimal approximations such as `"1.7321"` ($= 17321/10000$ in `test_general_polygon_base.py::N04_regular_hexagon`, locked as `N-11`) introduce a 5-digit prime $17321 > 10^4$ ($17321^3 > \text{MAX\_RADICAND}$) whose square inflates $p \cdot q = 90,005,112,300,000,000 > \text{MAX\_RADICAND}$ and is deterministically rejected with `RadicalDomainError`.
3. **GCD Cancellation in `multiply(a, b)`:**
   - Extracts $g = \gcd(c_a, c_b)$ into the rational coefficient `ha * hb * g` and passes `(ca // g) * (cb // g)` to `radical()`.

---

## 2. RED / GREEN & Regression Results

### 2.1 Locked W2-M4 Verification Corpus (`inputs/development.json`)

| Stratum | Count | RED Before (`results/red-before.json`) | GREEN After (`results/green-after.json`) | Details |
|---|---:|---:|---:|---|
| End-to-end product cases (`DEV-1-3`, `W2-A04`) | 2 | `0/2` | `2/2` | Both transition from `FALSE_REFUSAL (ENGINE_EXECUTION_FAILED / RADICAL_DOMAIN_OVERFLOW)` to `SERVED_CORRECT` with exact oracle match |
| Exact kernel & boundary cases (`K-01`..`K-16`) | 16 | `7/16` | `16/16` | All 9 previously overflowing reducible rational/radical cases now pass |
| Metamorphic equivalence groups (`M-01`..`M-06`) | 6 | `1/6` | `6/6` | Identical canonical type, equality, `hash`, `to_json`, `display`, and `square` across all algebraic paths |
| Negative fail-closed controls (`N-01`..`N-11`) | 11 | `11/11` | `11/11` | All 11 invalid/overflowing cases fail closed with `RadicalDomainError` (including `N-11` decimal approximation $17321^2$) |

### 2.2 Full Source Gate `/19` Regression (`results/source-gate-regression.json`)

- **Original Locked Positives:** `24/24` `SERVED_CORRECT` (`100.0%`, up from `23/24` in the parent wave; `DEV-1-3` is now `SERVED_CORRECT` with exact area `6175/242`, closing `ACCEPTANCE-1`).
- **Genuine Negatives:** `36/36` refused (`36/36` exact refusal-category agreement).
- **Adjudicated Valid Mislabeled Negative (`DEV-4-4`):** `1/1` `SERVED_CORRECT`.
- **Genuine Wrong-Served:** `0/61`.
- **Served Exact Oracle Agreement:** `25/25` (`100.0%`).
- **Supplemental Controls (`SUP-1`..`SUP-7`):** `7/7` passed (`5/5` served-correct, `2/2` refused-correct-reason).

### 2.3 Full 96-Case Holdout Wave 2 Post-Feedback Regression (`results/wave2-post-feedback-regression.json`)

- **Evidence Classification:** `POST_FEEDBACK_DEVELOPMENT_REGRESSION` (historical Holdout Wave 2 raw score at `d7a94d3c` remains `37/48` positive `SERVED_CORRECT`, preserved unchanged).
- **Positive Cases (`48`):** `46/48` `SERVED_CORRECT` (`95.83%`, Wilson 95% CI `[0.8602, 0.9885]`, up from `45/48` at `d99f6149`; `W2-A04` transitions from `FALSE_REFUSAL` to `SERVED_CORRECT` with exact area `11250√2/697`).
  - Category B (`ENGINE_DERIVED_SECTION`): `36/36` `SERVED_CORRECT` (`100.0%`, up from `35/36`).
  - Category A (`DINH_CAT_CANH`): `10/12` `SERVED_CORRECT` (`83.33%`).
- **Remaining False Refusals (`2/48`):** `W2-A07` and `W2-A10` (`PREVIEW_VALIDATION_FAILED / CANNOT_BUILD_SOLIDS`, out-of-scope `W2-M5` at `Adapter /4`, untouched per scope guard).
- **Negative Cases (`48`):** `48/48` refused (`100.0%`; `36/48` exact refusal-category agreement, `12/48` benign refusal-code granularity differences).
- **Wrong-Served:** `0/96` (`0.00%`).
- **Exact Oracle Agreement on Served Cases:** `46/46` (`100.0%`).

---

## 3. Tiered Verification (`T0`–`T3`) & Independent Review

- **T0 (`verification/impact-plan.json`, `verification/scope-and-evidence.json`, `verification/cache-and-fixtures.json`, `verification/publication-candidate.log`):**
  - Product diff is strictly `1` file (`backend/app/simulation/geometry/radical.py`).
  - Cache identity lock `MATCH` (`CACHE_VERSION = 130`), `41/41` stored preview fixtures verified (`0` problems).
  - Publication safety scan `PASS` (`scanned=26 messages=6 violations=0 pending_exception=0`).
- **T1 & T2 (`verification/t1-t2.log`):** `735 passed in 63.11s` (`0` failures), including `test_source_language_product_outcome[DEV-1-3]`, `test_llm_only_theo_nhan[N04_regular_hexagon]`, `test_radical_domain.py`, and `test_C2b_candidate_hien_tai_duoc_KHAI`.
- **Full T3 on Clean Detached Checkout (`verification/full-t3/receipt.json`, `verification/full-t3/full-t3.log`):**
  - Candidate SHA: `1e0c8db668bbe110f343a8a67cdeca465008c188` (detached worktree `.superpowers/worktrees/w2-m4-t3-detached`, clean before and after).
  - Verdict: `FULL_PRODUCT_GATE_PASS` (`exit_code = 0`).
  - Backend pytest: `12552 passed, 1 skipped, 2 deselected, 15 xfailed, 1 warning in 493.26s` (`0` failures).
  - Frontend vitest: `83 passed (83)` files, `1417 passed (1417)` tests.
  - Typecheck + production build: `PASS` (`5.5s`).
  - Thesis demo replay: `5/5 PASS` + `1/1 expected REFUSAL`.
  - Demo crash surface: `6/6 PASS`.
  - Post-T3 `freeze_evaluation_candidate.py --verify`: `MATCH` (`118` files, tree hash `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`).
  - Log SHA-256: `57af94912561e1b06e3e9a4e363d80128814b755bf09232d367db048de4fcbc7` (`167683` bytes).
- **Independent Review (`review.md`):** Audited by independent reviewer subagent (`1cedffc6-e203-4b8a-bbf9-6b8323a99199`); `0 BLOCKER, 0 MAJOR, 0 MINOR, 0 NIT`.
