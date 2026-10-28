# Independent Review — `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION`

- **Reviewer:** Independent W2-M4 Exact Radical Reviewer Subagent (`conversation://1cedffc6-e203-4b8a-bbf9-6b8323a99199`)
- **Reviewed Branch:** `research/hybrid-v2-w2-m4-exact-radical-normalization`
- **Parent Baseline HEAD:** `d99f6149ff1997258970bf888db5484665b106b8` (`research/hybrid-v2-wave2-source-gate-language-generalization`)
- **Product Commit:** `051224ee2740cbf5d55dd94633503db1f0050ada`
- **Frozen Full T3 Candidate:** `1e0c8db668bbe110f343a8a67cdeca465008c188`
- **Frozen Product Tree Hash (`118` files):** `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`
- **Review Verdict:** `APPROVED_NO_FINDINGS` (`0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `0 NIT`)

---

## 1. Finding Counts

| Severity | Count | Summary |
|---|---:|---|
| **BLOCKER** | `0` | None. |
| **MAJOR** | `0` | None. (`ACCEPTANCE-1` on `DEV-1-3` and `N04_regular_hexagon` regression both resolved; Full T3 passes `12,552 / 12,552` backend tests and `1,417 / 1,417` frontend tests.) |
| **MINOR** | `0` | None. |
| **NIT** | `0` | None. |

---

## 2. Audit of All 8 Mandatory Review Criteria

1. **Mathematical Correctness of Exact Radical Normalization (`PASS`):**
   - `sqrt_rational(x)` delegates directly to `radical(Fraction(1, q), p * q)` where `p, q = x.numerator, x.denominator` are coprime, preserving `radical()` + `_tach_binh_phuong()` as the single canonical normalization authority.
   - `multiply(a, b)` extracts $g = \gcd(c_a, c_b)$ into `ha * hb * g` before passing `(ca // g) * (cb // g)` to `radical()`.
   - For $1 \le n \le \text{MAX\_RADICAND} = 10^{12}$, `_tach_binh_phuong(n)` strips prime factors $d \le 10^4$ ($d^3 \le \text{MAX\_RADICAND}$) and applies `math.isqrt(m)` at the start and after each factor extraction; since any prime $p > 10^4$ with $p^2 \mid n$ has cofactor $n / p^2 < 10^{12} / 10^8 = 10^4$, stripping primes $\le 10^4$ leaves $m = p^2$, guaranteeing exact squarefree decomposition across $[1, 10^{12}]$.
   - For $\text{MAX\_RADICAND} < n \le \text{MAX\_RADICAND}^2$ ($10^{12} < n \le 10^{24}$), square-factor extraction is bounded to the schoolbook prime factor base $d^3 \le \text{MAX\_RADICAND}$ ($d \le 10^4$, with `isqrt(m)` folding $r$ if and only if $r^3 \le \text{MAX\_RADICAND}$). Both mandatory cases reduce in $\le 7$ steps:
     - `DEV-1-3`: $p \cdot q = 2,233,081,922,500 = 2^2 \cdot 5^4 \cdot 11^4 \cdot 13^2 \cdot 19^2 \implies (1494350, 1) \implies \text{Fraction}(6175, 242)$.
     - `W2-A04`: $p \cdot q = 122,970,403,125,000 = 2^3 \cdot 3^4 \cdot 5^8 \cdot 17^2 \cdot 41^2 \implies (7841250, 2) \implies \text{Radical}(\text{Fraction}(11250, 697), 2, 0)$ (`11250√2/697`).
   - Conversely, decimal approximations such as `"1.7321"` $= 17321/10000$ in `test_general_polygon_base.py::N04_regular_hexagon` (locked as `N-11`) introduce a 5-digit prime $17321 > 10^4$ ($17321^3 > \text{MAX\_RADICAND}$) whose square inflates $p \cdot q = 90,005,112,300,000,000 > \text{MAX\_RADICAND}$ and is deterministically rejected with `RadicalDomainError`.

2. **Strict Absence of Floating-Point Approximation (`PASS`):**
   - Zero use of `float`, `math.sqrt`, `** 0.5`, `round`, or epsilon comparisons; only `int`, `Fraction`, `math.isqrt`, and `math.gcd` are used.

3. **Absence of Case-Specific Hardcoding (`PASS`):**
   - Zero case IDs, vertex names, or problem-specific constants appear in `backend/app/simulation/geometry/radical.py`.

4. **Complexity & DoS Safety (`PASS`):**
   - The trial-division loop condition `while d * d * d <= m and d * d * d <= MAX_RADICAND:` bounds $d \le 10^4$ ($< 5,000$ odd steps, $< 0.5\text{ ms}$) across the entire domain, and $n > \text{MAX\_RADICAND}^2 = 10^{24}$ fails closed in $O(1)$ time.

5. **Canonical Representation Invariants (`PASS`):**
   - Verified across all 16 kernel cases and 6 metamorphic groups (`results/green-after.json`): rational results return `Fraction`, zero returns `Fraction(0)`, and irrational results return `Radical(he, can, mu)` with $1 \le \text{can} \le \text{MAX\_RADICAND}$ squarefree.

6. **Scope Compliance (`PASS`):**
   - `git diff --name-only d99f6149ff1997258970bf888db5484665b106b8..1e0c8db668bbe110f343a8a67cdeca465008c188 -- backend/app frontend/src` shows only `backend/app/simulation/geometry/radical.py` (`1` file). `Registry /19`, `Planner /17`, `Engine /14`, `Adapter /4`, `Certificate /1`, `CACHE_VERSION = 130`, and `DEFAULT_MODE = LLM_ONLY` are untouched.

7. **Integrity of Evidence & SHA-256 Locks (`PASS`):**
   - All LF-normalized SHA-256 hashes in `verification/scope-and-evidence.json` match the committed files (`inputs/development.json`, `results/red-before.json`, `results/green-after.json`, `results/source-gate-regression.json`, `results/wave2-post-feedback-regression.json`), and all historical artifacts in `hybrid-v2-wave2-source-gate-language-generalization` and `hybrid-v2-independent-vietnamese-section-holdout-wave2` are byte-identical.

8. **Honesty of Tests & Full T3 Receipt (`PASS`):**
   - `verification/full-t3/receipt.json` confirms `FULL_PRODUCT_GATE_PASS` (`exit_code: 0`) on clean detached candidate `1e0c8db668bbe110f343a8a67cdeca465008c188` (`product_commit: 051224ee2740cbf5d55dd94633503db1f0050ada`): `12552 passed, 0 failed` backend tests, `83 passed / 1417 passed` frontend tests, production build `PASS`, demo replay `5/5 PASS`, crash surface `6/6 PASS`, and `post_freeze: MATCH` (`8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`).
