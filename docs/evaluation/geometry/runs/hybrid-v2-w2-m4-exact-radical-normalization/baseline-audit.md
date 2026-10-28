# Baseline Audit — W2-M4 Exact Radical Normalization (`hybrid-v2-w2-m4-exact-radical-normalization`)

- **Task:** `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION`
- **Baseline HEAD (`research/hybrid-v2-wave2-source-gate-language-generalization`):** `d99f6149ff1997258970bf888db5484665b106b8`
- **Baseline Product Commit:** `c6f6b64bda6473c175a32a7875a9dd9831ae7c6d` (Frozen Candidate `b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9`, 118 files, tree hash `8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25`)
- **Inspected Module:** `backend/app/simulation/geometry/radical.py` (`MAX_RADICAND = 10**12`)

---

## 1. Complete Trace of the Two Mandatory Failing Cases

Both `DEV-1-3` and `W2-A04` succeed completely in:
1. Source Gate `/19` (`registry.py`),
2. Planner `/17` (`planner.py`), and
3. Engine `/14` (`engine.py`, where `_dt2_da_giac` computes the exact rational squared area $S^2 \in \mathbb{Q}$ without taking any square root).

Both fail during semantic program execution (`interpreter.py:219` $\to$ `geometry_exec.py:425 area_of` $\to$ `measure.py:327 area_section` $\to$ `measure.py:313 area_polygon`), where `measure.area_polygon` computes:

```python
return sqrt_rational(Fraction(_m.area_sq_from_cross_sum(tong), 4))
```

### 1.1 Case A — `DEV-1-3` (Triangular Pyramid `T.EFG`)

- **Given:** Right triangular pyramid $T.EFG$ with $\triangle EFG$ right at $E$, $EF = 13$, $EG = 19$, $TE \perp (EFG)$, $TE = 11$, point $J \in ET$ with $JT = \frac{5}{11}ET$, and plane $(\alpha)$ through $J$ parallel to $(EFG)$.
- **Exact Geometry:**
  - Base area: $S_{\triangle EFG} = \frac{1}{2} \cdot 13 \cdot 19 = \frac{247}{2}$.
  - Homothety ratio from apex $T$: $t = \frac{5}{11}$.
  - Exact section area (rational):
    $$S = \left(\frac{5}{11}\right)^2 \cdot \frac{247}{2} = \frac{25 \cdot 247}{2 \cdot 121} = \frac{6175}{242}$$
  - Exact squared area passed to `sqrt_rational(x)`:
    $$x = S^2 = \frac{38,130,625}{58,564}$$
    where:
    - Numerator $p = 38,130,625 = 5^4 \cdot 13^2 \cdot 19^2 = 6175^2 < 3.82 \times 10^7 \ll 10^{12}$ (an exact perfect square, $m_p = 1$).
    - Denominator $q = 58,564 = 2^2 \cdot 11^4 = 242^2 < 5.86 \times 10^4 \ll 10^{12}$ (an exact perfect square, $m_q = 1$).
- **Why `radical.py` Refused:**
  - `sqrt_rational(Fraction(38130625, 58564))` at `radical.py:248` executes `return radical(Fraction(1, q), p * q)`.
  - Multiplying $p \cdot q = 38,130,625 \times 58,564 = 2,233,081,922,500 = 1,494,350^2$ produces an unreduced perfect square $> 10^{12}$.
  - `radical()` at `radical.py:214` checks `if can > MAX_RADICAND:` **before** calling `_tach_binh_phuong(can)` (where `math.isqrt(can)` at line 175 would have reduced $1,494,350^2$ to $(1494350, 1)$ in $O(1)$ time), raising:
    `RadicalDomainError: căn thức 2233081922500 vượt trần 1000000000000 — từ chối thay vì treo`.

### 1.2 Case B — `W2-A04` (Quadrilateral Pyramid `S.ABCD`)

- **Given:** Rectangular pyramid $S.ABCD$ with $AB = 6$, $AD = 8$, $SA \perp (ABCD)$, $SA = 10$, cut by plane $(Q)$ through $A$ perpendicular to $SC$, intersecting $SB, SC, SD$ at $M, N, P$.
- **Exact Geometry:**
  - Coordinates: $A(0,0,0), B(6,0,0), C(6,8,0), D(0,8,0), S(0,0,10)$.
  - Plane $(Q)$: $3x + 4y - 5z = 0$.
  - Edge parameters from $S$: $t_M = \frac{25}{34}$ on $SB$, $t_N = \frac{1}{2}$ on $SC$, $t_P = \frac{25}{41}$ on $SD$.
  - Cross-product sum $\Sigma = A \times M + M \times N + N \times P + P \times A = \frac{-2250}{697}(4, 3, 5)$, where $697 = 17 \times 41$ and $|(4,3,5)|^2 = 50 = 25 \times 2$.
  - Exact squared area passed to `sqrt_rational(x)`:
    $$x = S^2 = \frac{1}{4}|\Sigma|^2 = \frac{253,125,000}{485,809}$$
    where:
    - Numerator $p = 253,125,000 = 2^3 \cdot 3^4 \cdot 5^7 = (2 \cdot 3^2 \cdot 5^3)^2 \cdot 10 = 11250^2 \cdot 2 < 2.54 \times 10^8 \ll 10^{12}$ (square part $k_p = 11250$, squarefree core $m_p = 2$).
    - Denominator $q = 485,809 = 17^2 \cdot 41^2 = 697^2 < 4.86 \times 10^5 \ll 10^{12}$ (an exact perfect square, $k_q = 697$, squarefree core $m_q = 1$).
  - Exact section area:
    $$S = \frac{11250\sqrt{2}}{697} = \text{Radical}\!\left(\text{Fraction}(11250, 697),\ 2,\ 0\right)$$
    whose canonical squarefree radicand is **`can = 2`**.
- **Why `radical.py` Refused:**
  - `sqrt_rational(Fraction(253125000, 485809))` at `radical.py:248` multiplies $p \cdot q = 253,125,000 \times 485,809 = 122,970,403,125,000 = 7,841,250^2 \times 2 > 10^{12}$ before extracting the square parts $11250^2$ from $p$ and $697^2$ from $q$, raising:
    `RadicalDomainError: căn thức 122970403125000 vượt trần 1000000000000 — từ chối thay vì treo`.

---

## 2. Evidence-Based Answers to the 5 Diagnostic Questions (Section 3)

### Q1. Why does a problem with relatively small integer data produce an intermediate radicand exceeding the ceiling?

In 3D coordinate geometry over $\mathbb{Q}^3$, section vertices on skew/oblique edges have rational coordinates whose denominators are dot products $|\vec{u}|^2$ (e.g. $11$ in `DEV-1-3`; $34 = 2 \cdot 17$ and $41$ in `W2-A04`). When `area_polygon` computes the polygon cross-product vector $\Sigma = \sum P_i \times P_{i+1}$, the common denominator of $\Sigma$ is the product of edge denominators ($D = 17 \cdot 41 = 697$ in `W2-A04`, or $D = 11^2 = 121$ in `DEV-1-3`). Taking the squared norm $S^2 = \frac{1}{4}|\Sigma|^2 = \frac{p}{q}$ **squares both the numerator scale and the denominator $D$**, so $p = k_p^2 m_p$ and $q = k_q^2 m_q$ already carry large square factors ($k_p^2$ and $k_q^2$). When `sqrt_rational(p / q)` then computes `p * q` to rationalize the denominator *before* extracting $k_p^2$ and $k_q^2$, it multiplies two fourth-degree / squared quantities together ($p \cdot q = k_p^2 k_q^2 m_p m_q$), inflating small inputs ($13, 19, 11$ or $6, 8, 10$) into $10^{12}\text{–}10^{14}$ even when the canonical squarefree radicand $m_p m_q$ is $1$ or $2$.

### Q2. Is the ceiling checked before or after canonical normalization?

In the baseline code (`radical.py:214–222`), `if can > MAX_RADICAND:` is checked **strictly before** canonical normalization:
1. In `sqrt_rational(x)` (`radical.py:247–248`), `p * q` is formed before `_tach_binh_phuong` is called on $p$ and $q$.
2. In `multiply(a, b)` (`radical.py:331`), `ca * cb` is formed before dividing out $g = \gcd(c_a, c_b)$.
3. In `radical(he, can, mu)` (`radical.py:214–222`), `if can > MAX_RADICAND:` runs at line 214 before `_tach_binh_phuong(can)` at line 222 (and even before `math.isqrt(can)` at line 175).

### Q3. Can we perform exact reduction/normalization before checking the limit while strictly bounding computational cost?

**Yes, provably.**
1. **Separate Coprime Numerator/Denominator Reduction in `sqrt_rational(p / q)`:**
   Because `x = Fraction(x)` is reduced ($\gcd(p, q) = 1$), $p$ and $q$ are coprime. Factoring $p = k_p^2 m_p$ and $q = k_q^2 m_q$ separately yields:
   $$\sqrt{\frac{p}{q}} = \frac{k_p}{k_q m_q}\sqrt{m_p m_q}$$
   where $\gcd(m_p, m_q) = 1$ and both $m_p, m_q$ are squarefree, so $m_p m_q$ is already canonical and squarefree without ever forming the unreduced product $p \cdot q$.
2. **GCD Cancellation in `multiply(a, b)`:**
   For canonical squarefree radicands $c_a, c_b$, let $g = \gcd(c_a, c_b)$. Then $\sqrt{c_a c_b} = g \sqrt{(c_a // g)(c_b // g)}$, where $(c_a // g)(c_b // g)$ is already squarefree and avoids multiplying $g^2$ into the radicand.
3. **Bounded Cube-Root + `isqrt` Squarefree Reduction in `_tach_binh_phuong(n)`:**
   By stripping each prime divisor $d$ completely from $m$ (accumulating square pairs into $k$ and odd-exponent primes into squarefree `sf` so $n = k^2 \cdot \text{sf} \cdot m$) and checking `r = math.isqrt(m); if r * r == m: return k * r, sf` before the loop and after every prime extraction:
   - Any remaining non-square $m > 1$ with no prime factors $< d$ that satisfies $m < d^3$ has at most two prime factors (counted with multiplicity); since $m$ is not a square ($r^2 \ne m$), $m$ is **provably squarefree** once $d^3 > m$.
   - Furthermore, since $m$ is not a square, its squarefree core is $\ge d$, so if $\text{sf} \cdot d > \text{MAX\_RADICAND}$ at any step, the canonical squarefree radicand of $n$ is provably $> \text{MAX\_RADICAND}$ and the loop aborts immediately.
   - Capping the input at $n \le \text{MAX\_RADICAND}^2 = 10^{24}$ and the loop at `d * d * d <= m and d * d <= MAX_RADICAND` bounds worst-case iterations to $\le 5,000$ odd steps ($< 0.8\text{ ms}$) for $n \le 10^{12}$ and $\le 500,000$ odd steps ($\le 66\text{ ms}$) for $n \le 10^{24}$, while enforcing `sf * m <= MAX_RADICAND` on the canonical output.

### Q4. What invariants protect the kernel from overly large or degenerate inputs?

1. **Positivity & Non-Degeneracy:** `can <= 0` in `radical()` / `_tach_binh_phuong()` and `x < 0` in `sqrt_rational()` raise `RadicalDomainError`; `he == 0` or `x == 0` canonicalizes to `Fraction(0)` (never `0 * √b`); `m == 1 and mu == 0` canonicalizes to `Fraction(he * k)` (never `a * √1`).
2. **Hard Input Ceiling (`n <= MAX_RADICAND ** 2 = 10**24`):** Rejects astronomical integers in $O(1)$ before `isqrt` or division.
3. **Bounded Trial Division (`d^3 <= m and d^2 <= MAX_RADICAND`):** Guarantees at most $500,000$ odd trial-division steps in the absolute worst case (and $\le 5,000$ steps for $m \le 10^{12}$).
4. **Canonical Output Ceiling & Squarefreeness (`1 <= can <= MAX_RADICAND`, `can` squarefree):** Every constructed `Radical(he, can, mu)` has `can` provably squarefree and $1 \le \text{can} \le 10^{12}$, preserving `frozen=True` structural equality and hashing.

### Q5. Are there cases that genuinely exceed representability even after exact normalization?

**Yes, and they must remain fail-closed (`RadicalDomainError`):**
1. **Irreducible/Squarefree Radicands $> \text{MAX\_RADICAND}$:** Any number whose canonical squarefree radicand $s = m_p m_q > 10^{12}$ (for example, `radical(1, MAX_RADICAND + 1)` where $10^{12} + 1 = 73 \cdot 137 \cdot 99990001$ is squarefree, or `sqrt_rational(Fraction(10**12 + 39, 1))`, or `sqrt_rational(Fraction(999983, 999979))` where $m_p m_q = 999983 \times 999979 = 999,962,000,357 \le 10^{12}$ succeeds but `sqrt_rational(Fraction(1000003, 1000033))` where $m_p m_q > 10^{12}$ fails).
2. **Unfactored Composites Requiring Trial Division Beyond $\sqrt{\text{MAX\_RADICAND}} = 10^6$:** A single integer $n > 10^{18}$ passed directly to `radical(1, n)` whose prime factors all exceed $10^6$ and is not a perfect square ($d^3 \le m$ still holds when $d$ reaches $10^6$).
3. **Out-of-Domain Algebraic Forms:** Sums of incommensurable radicals ($\sqrt{2} + \sqrt{3}$, $1 + \sqrt{2}$), $\pi$ exponents outside $\{0, 1\}$ ($\pi^2$), negative inputs to `sqrt_rational`, and division by zero.
