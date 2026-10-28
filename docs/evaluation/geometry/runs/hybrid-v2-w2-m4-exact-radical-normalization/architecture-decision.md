# Architecture Decision — Exact Radical Normalization Before Complexity Ceiling (`hybrid-v2-w2-m4-exact-radical-normalization`)

- **Task:** `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION`
- **Decision Status:** `APPROVED_WITHIN_AUTHORIZED_KERNEL_SCOPE`
- **Target Module:** `backend/app/simulation/geometry/radical.py`
- **Unchanged Contracts:** `MAX_RADICAND = 10**12`, `PI_EXPONENT_DOMAIN = (0, 1)`, `REGISTRY_VERSION = geometry-functions/19`, `PLANNER_VERSION = geometry-fact-planner/17`, `ENGINE_VERSION = geometry-function-engine/14`, `ADAPTER_V4_VERSION = hybrid-simulation-adapter/4`, `PLANE_SECTION_CERTIFICATE_VERSION = plane-section-certificate/1`, `CACHE_VERSION = 130`, `DEFAULT_MODE = LLM_ONLY`.

---

## 1. Problem Statement

`backend/app/simulation/geometry/radical.py` represents exact values in the domain:

$$x \in \mathbb{Q} \cup \left\{\, h \cdot \pi^{\mu} \cdot \sqrt{c} \;\middle|\; h \in \mathbb{Q} \setminus \{0\},\ \mu \in \{0, 1\},\ c \in \mathbb{Z}_{\ge 1} \text{ squarefree},\ (c > 1 \lor \mu = 1),\ c \le \text{MAX\_RADICAND} \,\right\}$$

In the baseline implementation:
1. `sqrt_rational(p / q)` forms the unreduced integer product `p * q` before extracting squares from the coprime numerator $p$ and denominator $q$.
2. `multiply(a, b)` forms `ca * cb` before cancelling $g = \gcd(c_a, c_b)$.
3. `radical(he, can, mu)` enforces `if can > MAX_RADICAND:` on the **unnormalized** input `can` before `_tach_binh_phuong(can)` extracts square factors.

Consequently, valid schoolbook geometry problems with small integer edges (`DEV-1-3` with $13, 19, 11$ where $S = \frac{6175}{242}$ has canonical radicand $1$, and `W2-A04` with $6, 8, 10$ where $S = \frac{11250\sqrt{2}}{697}$ has canonical radicand $2$) fail with `RADICAL_DOMAIN_OVERFLOW` solely because their unreduced product $p \cdot q$ exceeds $10^{12}$.

---

## 2. Alternatives Considered

1. **Alternative A (Rejected): Increase `MAX_RADICAND` from $10^{12}$ to $10^{15}$ or $10^{16}$ without changing normalization order.**
   - *Why rejected:* Under naive $\sqrt{n}$ trial division (`while d * d <= m:`), raising `MAX_RADICAND` to $10^{16}$ increases worst-case loop iterations from $10^6$ to $10^8$ (~15 seconds per call), creating a denial-of-service / hang risk while still failing whenever a slightly larger rational denominator $q = k_q^2$ makes $p \cdot q > 10^{16}$.
2. **Alternative B (Selected): Exact Mathematical Normalization Before Enforcing `MAX_RADICAND = 10**12`, Paired with Bounded Cube-Root + `isqrt` Squarefree Reduction.**
   - *Why selected:* Preserves `MAX_RADICAND = 10**12` as the exact ceiling on canonical squarefree radicands and keeps worst-case trial-division work strictly bounded ($\le 5,000$ odd steps for $n \le 10^{12}$ and $\le 500,000$ odd steps for $n \le 10^{24}$), while eliminating false overflows caused by unreduced square factors in `sqrt_rational`, `multiply`, and `radical`.

---

## 3. Exact Mathematical Design & Proofs

### 3.1 Single Normalization Authority via `radical(Fraction(1, q), p * q)` in `sqrt_rational(x)`

For $x = \text{Fraction}(x) > 0$, Python's `Fraction` guarantees $x = p / q$ with $p, q \in \mathbb{Z}_{\ge 1}$ and $\gcd(p, q) = 1$:

$$\sqrt{\frac{p}{q}} = \frac{1}{q}\sqrt{p \cdot q}$$

Delegating `sqrt_rational(x)` directly to `radical(Fraction(1, q), p * q)` preserves a **single normalization authority** (`_tach_binh_phuong` inside `radical()`) with zero code duplication between `sqrt_rational` and `radical`. Because $\gcd(p, q) = 1$, the prime factorization of $p \cdot q$ is the disjoint union of the prime factorizations of $p$ and $q$, so `sqrt_rational(Fraction(p, q))` and `radical(Fraction(1, q), p * q)` have the exact same domain and produce the exact same canonical result on every input.

### 3.2 GCD Cancellation in `multiply(a, b)`

For canonical operands with squarefree radicands $c_a, c_b \ge 1$, let $g = \gcd(c_a, c_b)$. Since $c_a, c_b$ are squarefree, $u_a = c_a // g$ and $u_b = c_b // g$ are squarefree and coprime, so:

$$(h_a \pi^{m_a} \sqrt{c_a}) \cdot (h_b \pi^{m_b} \sqrt{c_b}) = (h_a h_b g)\pi^{m_a + m_b}\sqrt{u_a u_b}$$

Calling `radical(ha * hb * g, (ca // g) * (cb // g), ma + mb)` avoids multiplying $g^2$ into the intermediate radicand.

### 3.3 Bounded Cube-Root + `isqrt` Squarefree Reduction in `_tach_binh_phuong(n)`

Given $n \in \mathbb{Z}$:
1. If $n \le 0$, raise `RadicalDomainError`.
2. If $n > \text{MAX\_RADICAND}^2 = 10^{24}$, raise `RadicalDomainError` in $O(1)$ time.
3. Define the **schoolbook prime factor base** $B = \lfloor \text{MAX\_RADICAND}^{1/3} \rfloor = 10^4$ ($d^3 \le \text{MAX\_RADICAND}$):
   - For $n \le \text{MAX\_RADICAND} = B^3 = 10^{12}$, any prime $p > B$ with $p^2 \mid n$ has cofactor $n / p^2 < B^3 / B^2 = B$, so stripping prime factors $\le B$ leaves $m = p^2$, which is caught in $O(1)$ time by `math.isqrt(m)`. Thus **every** integer $1 \le n \le \text{MAX\_RADICAND}$ is reduced completely in at most $5,000$ odd trial-division steps.
   - For $\text{MAX\_RADICAND} < n \le \text{MAX\_RADICAND}^2$ ($10^{12} < n \le 10^{24}$), $n$ is accepted if and only if its square part $k$ is $B$-smooth (all prime factors of $k$ satisfy $p^3 \le \text{MAX\_RADICAND}$, i.e., $p \le 10^4$) and its squarefree core satisfies $m_0 \le \text{MAX\_RADICAND}$. In exact schoolbook 3D geometry over $\mathbb{Q}$, rational denominators arise from small integer dimensions (across all 163 cases in Source Gate `/19` and Holdout Wave 2, the largest prime factor in $k$ is $41 \ll 10^4$, so `DEV-1-3` with prime factors $\{2, 5, 11, 13, 19\}$ and `W2-A04` with prime factors $\{2, 3, 5, 17, 41\}$ are reduced in $\le 7$ steps). Conversely, a floating-point decimal approximation such as `"1.7321"` ($= 17321 / 10000$ in `test_general_polygon_base.py::N04_regular_hexagon`) introduces a 5-digit prime $17321 > 10^4$ ($17321^3 > \text{MAX\_RADICAND}$) whose square inflates $p \cdot q = 90,005,112,300,000,000 > \text{MAX\_RADICAND}$ and is deterministically rejected with `RadicalDomainError`.
4. Maintain invariant $n = k^2 \cdot \text{sf} \cdot m$, where $\text{sf} \ge 1$ is squarefree with all prime factors $< d$, and $m \ge 1$ has no prime factors $< d$:
   - Check $r = \text{isqrt}(n)$; if $r^2 == n$ and ($n \le \text{MAX\_RADICAND}$ or $r^3 \le \text{MAX\_RADICAND}$), return $(r, 1)$ in $O(1)$ time.
   - Strip all factors of $2$ from $m$: $k \gets k \cdot 2^{\lfloor e_2 / 2 \rfloor}$, $\text{sf} \gets 2^{e_2 \bmod 2}$; check $r = \text{isqrt}(m)$ and if $r^2 == m$ and ($n \le \text{MAX\_RADICAND}$ or $r^3 \le \text{MAX\_RADICAND}$), return $(k \cdot r, \text{sf})$.
   - Loop odd $d = 3, 5, 7, \dots$ while $d^3 \le m$ and $d^3 \le \text{MAX\_RADICAND}$ ($d \le 10^4$, at most $5,000$ odd steps):
     - If $\text{sf} \cdot d > \text{MAX\_RADICAND}$, raise `RadicalDomainError` immediately.
     - If $d \mid m$, strip all factors of $d$ (`while m % d == 0: m //= d; e += 1`), update $k \gets k \cdot d^{\lfloor e/2 \rfloor}$ and (if $e$ is odd) $\text{sf} \gets \text{sf} \cdot d$ (raising `RadicalDomainError` if $\text{sf} > \text{MAX\_RADICAND}$). Check $r = \text{isqrt}(m)$; if $r^2 == m$ and ($n \le \text{MAX\_RADICAND}$ or $r^3 \le \text{MAX\_RADICAND}$), return $(k \cdot r, \text{sf})$.
5. After the loop:
   - Check $r = \text{isqrt}(m)$: if $r^2 == m$, return $(k \cdot r, \text{sf})$ when $n \le \text{MAX\_RADICAND}$ or $r^3 \le \text{MAX\_RADICAND}$, and otherwise raise `RadicalDomainError` (large prime square $r^2$ with $r > 10^4$ in an overflowing radicand $n > \text{MAX\_RADICAND}$).
   - **Theorem:** If $d^3 > m$ for a non-square integer $m > 1$ with no prime divisors $< d$, then $m$ has at most two prime factors counted with multiplicity (since $p_1 p_2 p_3 \ge d^3 > m$); because $m \ne p^2$ (checked by `isqrt(m)`), $m$ is either prime or a product of two distinct primes $\ge d$, hence **provably squarefree** and coprime to $\text{sf}$.
   - Therefore, if $d^3 \le m$ or $m > \text{MAX\_RADICAND}$ or $\text{sf} \cdot m > \text{MAX\_RADICAND}$, raise `RadicalDomainError`.
   - Otherwise return $(k, \text{sf} \cdot m)$.

---

## 4. Invariant Preservation & Zero Downstream Contract Drift

- **Canonical Representation:** Every returned value is either `Fraction` (when rational, i.e. $m = 1 \land \mu = 0$ or $h = 0$) or `Radical(he, can, mu)` with $h \ne 0$, $\mu \in \{0, 1\}$, and $1 \le \text{can} \le \text{MAX\_RADICAND}$ squarefree.
- **No Floating Point:** Uses only `Fraction`, `int`, `math.isqrt`, and `math.gcd`.
- **Equality, Hashing & Serialization:** Unchanged (`Radical` remains `@dataclass(frozen=True)`).
- **Engine / Planner / Registry / Adapter / Cache Compatibility:** Zero changes outside `radical.py`; `CACHE_VERSION = 130` and all component version strings remain intact.
