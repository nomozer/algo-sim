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

### 3.1 Separate Coprime Numerator/Denominator Normalization in `sqrt_rational(x)`

For $x = \text{Fraction}(x) > 0$, Python's `Fraction` guarantees $x = p / q$ with $p, q \in \mathbb{Z}_{\ge 1}$ and $\gcd(p, q) = 1$.
Decompose $p = k_p^2 m_p$ and $q = k_q^2 m_q$ via `_tach_binh_phuong(p)` and `_tach_binh_phuong(q)`, where $m_p, m_q \ge 1$ are squarefree and $\le \text{MAX\_RADICAND}$.
Then:

$$\sqrt{\frac{p}{q}} = \frac{k_p \sqrt{m_p}}{k_q \sqrt{m_q}} = \frac{k_p}{k_q m_q}\sqrt{m_p m_q}$$

Because $\gcd(p, q) = 1$, $\gcd(m_p, m_q) = 1$; since $m_p$ and $m_q$ are squarefree and coprime, $m_p m_q$ is already squarefree. Passing `radical(Fraction(kp, kq * mq), mp * mq)` enforces `mp * mq <= MAX_RADICAND` and returns `Fraction(kp, kq)` when $m_p m_q = 1$ or `Radical(Fraction(kp, kq * mq), mp * mq, 0)` when $1 < m_p m_q \le \text{MAX\_RADICAND}$.

### 3.2 GCD Cancellation in `multiply(a, b)`

For canonical operands with squarefree radicands $c_a, c_b \ge 1$, let $g = \gcd(c_a, c_b)$. Since $c_a, c_b$ are squarefree, $u_a = c_a // g$ and $u_b = c_b // g$ are squarefree and coprime, so:

$$(h_a \pi^{m_a} \sqrt{c_a}) \cdot (h_b \pi^{m_b} \sqrt{c_b}) = (h_a h_b g)\pi^{m_a + m_b}\sqrt{u_a u_b}$$

Calling `radical(ha * hb * g, (ca // g) * (cb // g), ma + mb)` avoids multiplying $g^2$ into the intermediate radicand.

### 3.3 Bounded Cube-Root + `isqrt` Squarefree Reduction in `_tach_binh_phuong(n)`

Given $n \in \mathbb{Z}$:
1. If $n \le 0$, raise `RadicalDomainError`.
2. If $n > \text{MAX\_RADICAND}^2 = 10^{24}$, raise `RadicalDomainError` in $O(1)$ time.
3. Check $r = \text{isqrt}(n)$; if $r^2 == n$, return $(r, 1)$ in $O(1)$ time.
4. Maintain invariant $n = k^2 \cdot \text{sf} \cdot m$, where $\text{sf} \ge 1$ is squarefree with all prime factors $< d$, and $m \ge 1$ has no prime factors $< d$:
   - Strip all factors of $2$ from $m$: $k \gets k \cdot 2^{\lfloor e_2 / 2 \rfloor}$, $\text{sf} \gets 2^{e_2 \bmod 2}$; check $r = \text{isqrt}(m)$ and if $r^2 == m$, return $(k \cdot r, \text{sf})$.
   - Loop odd $d = 3, 5, 7, \dots$ while $d^3 \le m$ and $d^2 \le \text{MAX\_RADICAND}$:
     - Since $m$ is not a perfect square at the top of the loop and has no prime factors $< d$, its squarefree part $\text{sf}(m)$ satisfies $\text{sf}(m) \ge d$. Therefore, if $\text{sf} \cdot d > \text{MAX\_RADICAND}$, the canonical squarefree core $\text{sf} \cdot \text{sf}(m)$ is provably $> \text{MAX\_RADICAND}$; raise `RadicalDomainError` immediately.
     - If $d \mid m$, strip all factors of $d$ (`while m % d == 0: m //= d; e += 1`), update $k \gets k \cdot d^{\lfloor e/2 \rfloor}$ and (if $e$ is odd) $\text{sf} \gets \text{sf} \cdot d$ (raising `RadicalDomainError` if $\text{sf} > \text{MAX\_RADICAND}$). Check $r = \text{isqrt}(m)$; if $r^2 == m$, return $(k \cdot r, \text{sf})$.
5. After the loop:
   - **Theorem:** If $d^3 > m$ for a non-square integer $m > 1$ with no prime divisors $< d$, then $m$ has at most two prime factors counted with multiplicity (since $p_1 p_2 p_3 \ge d^3 > m$); because $m \ne p^2$ (already checked by `isqrt(m)`), $m$ is either prime or a product of two distinct primes $\ge d$, hence **provably squarefree** and coprime to $\text{sf}$.
   - Therefore, if $d^3 \le m$ (the loop hit $d^2 > \text{MAX\_RADICAND}$ on a large unfactored $m > 10^{18}$) or $m > \text{MAX\_RADICAND}$ or $\text{sf} \cdot m > \text{MAX\_RADICAND}$, raise `RadicalDomainError`.
   - Otherwise return $(k, \text{sf} \cdot m)$.

---

## 4. Invariant Preservation & Zero Downstream Contract Drift

- **Canonical Representation:** Every returned value is either `Fraction` (when rational, i.e. $m = 1 \land \mu = 0$ or $h = 0$) or `Radical(he, can, mu)` with $h \ne 0$, $\mu \in \{0, 1\}$, and $1 \le \text{can} \le \text{MAX\_RADICAND}$ squarefree.
- **No Floating Point:** Uses only `Fraction`, `int`, `math.isqrt`, and `math.gcd`.
- **Equality, Hashing & Serialization:** Unchanged (`Radical` remains `@dataclass(frozen=True)`).
- **Engine / Planner / Registry / Adapter / Cache Compatibility:** Zero changes outside `radical.py`; `CACHE_VERSION = 130` and all component version strings remain intact.
