# Pre-Merge Evidence Reconciliation & Correction Addendum — `HYBRID_V2_W2_M4_PREMERGE_EVIDENCE_RECONCILIATION`

- **Addendum Wave ID:** `HYBRID_V2_W2_M4_PREMERGE_EVIDENCE_RECONCILIATION`
- **Corrects Wave ID:** `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION`
- **Branch:** `research/hybrid-v2-w2-m4-exact-radical-normalization`
- **Pre-Reconciliation Documentation HEAD:** `e78ecfe7a28cbe9de2754b08283b56d3829d1c1a`
- **Frozen Full T3 Candidate:** `1e0c8db668bbe110f343a8a67cdeca465008c188`
- **Product Commit:** `051224ee2740cbf5d55dd94633503db1f0050ada`
- **Measured Product Tree (`118` files):** `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369` (`MATCH`)
- **Authoritative `main = origin/main`:** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Historical Holdout Wave 2 Commit:** `ecdc26b012c8ce80d53524a98dc75cdcb020079d`
- **Parent Source Gate `/19` HEAD:** `d99f6149ff1997258970bf888db5484665b106b8`
- **Machine Verification Receipt:** [`results/premerge-evidence-reconciliation.json`](results/premerge-evidence-reconciliation.json)
- **Independent Review Receipt:** [`review-reconciliation.md`](review-reconciliation.md)
- **Reconciliation Status:** `PREMERGE_EVIDENCE_RECONCILED_READY_FOR_OWNER_GO`

---

## 1. Scope & Non-Destructive Preservation Rule

This additive correction layer resolves all pre-merge evidence and narrative discrepancies identified during the Owner GO audit (`HYBRID_V2_W2_M4_PREMERGE_EVIDENCE_RECONCILIATION`) without modifying any product file, oracle, test, or locked machine result:

1. **Zero Product Diff:** `git diff --name-only 1e0c8db668bbe110f343a8a67cdeca465008c188..HEAD -- backend/app frontend/src` is empty (`0` files). `freeze_evaluation_candidate.py --verify` returns `MATCH` (`118` files, `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`).
2. **Historical Artifacts Preserved Byte-for-Byte:** [`report.md`](report.md), [`architecture-decision.md`](architecture-decision.md), [`baseline-audit.md`](baseline-audit.md), [`plan.md`](plan.md), [`review.md`](review.md), [`inputs/development.json`](inputs/development.json), [`results/red-before.json`](results/red-before.json), [`results/green-after.json`](results/green-after.json), [`results/source-gate-regression.json`](results/source-gate-regression.json), [`results/wave2-post-feedback-regression.json`](results/wave2-post-feedback-regression.json), [`verification/full-t3/receipt.json`](verification/full-t3/receipt.json), and [`verification/full-t3/full-t3.log`](verification/full-t3/full-t3.log) remain 100% byte-identical to commit `e78ecfe7a28cbe9de2754b08283b56d3829d1c1a`.

---

## 2. Finding A — `W2-A04` Mathematical Consistency Adjudication

### 2.1 Discrepancy Under Audit

- **Committed Evidence (`report.md`, `review.md`, `handoff.md`, `run.json`, `inputs/development.json`, `results/green-after.json`, `results/wave2-post-feedback-regression.json`):** `area_squared = 253125000/485809`, exact area `11250√2/697`.
- **Previous Conversational Chat Summary (Prose Reply Only):** `area_squared = 150062500/819529`, exact area `8750√1006/901`.

### 2.2 Independent First-Principles Verification (`Fraction`)

1. **Frozen Holdout Wave 2 Problem & Oracle (`ecdc26b012c8ce80d53524a98dc75cdcb020079d`):**
   - **Source text (`inputs/holdout-wave2.json`):** *"Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 6, AD = 8, cạnh bên SA vuông góc với mặt phẳng (ABCD) và SA = 10. Mặt phẳng (Q) đi qua điểm A và vuông góc với đường thẳng SC, cắt các cạnh bên SB, SC, SD lần lượt tại M, N, P. Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (Q). Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (Q)."*
   - **Frozen independent oracle (`oracle/expected.json` & `oracle/geometry.json`):**
     - `solid`: `"S.ABCD"`, `section_id`: `"sec"`, `expected_certificate_category`: `"DINH_CAT_CANH"`, `vertex_count`: `4`.
     - `boundary`: `[{"vertex": "A"}, {"edge": ["S", "D"], "t": "25/41"}, {"edge": ["S", "C"], "t": "1/2"}, {"edge": ["S", "B"], "t": "25/34"}]`.
     - `area_squared`: `"253125000/485809"`.
2. **Independent Exact Euclidean Recomputation (`Fraction`):**
   - Place $A = (0, 0, 0)$, $B = (6, 0, 0)$, $C = (6, 8, 0)$, $D = (0, 8, 0)$, $S = (0, 0, 10)$.
   - Plane $(Q)$ passes through $A(0, 0, 0)$ with normal $\vec{n} = \vec{SC} = (6, 8, -10)$, giving plane equation $3x + 4y - 5z = 0$.
   - Intersecting the lateral edges $S \to B$, $S \to C$, $S \to D$ with $3x + 4y - 5z = 0$:
     - On $SB$: $P(t) = (6t, 0, 10(1 - t)) \implies 18t - 50(1 - t) = 0 \implies t_{SB} = \frac{25}{34}$, $M = \left(\frac{75}{17}, 0, \frac{45}{17}\right)$.
     - On $SC$: $P(t) = (6t, 8t, 10(1 - t)) \implies (18 + 32)t - 50(1 - t) = 0 \implies t_{SC} = \frac{1}{2}$, $N = (3, 4, 5)$.
     - On $SD$: $P(t) = (0, 8t, 10(1 - t)) \implies 32t - 50(1 - t) = 0 \implies t_{SD} = \frac{25}{41}$, $P = \left(0, \frac{200}{41}, \frac{160}{41}\right)$.
   - Decomposing convex quadrilateral $AMNP$ into $\triangle AMN$ and $\triangle ANP$:
     $$\vec{AM} \times \vec{AN} = \left(-\frac{180}{17}, -\frac{240}{17}, \frac{300}{17}\right), \qquad \vec{AN} \times \vec{AP} = \left(-\frac{360}{41}, -\frac{480}{41}, \frac{600}{41}\right)$$
     $$\vec{\Sigma} = \vec{AM} \times \vec{AN} + \vec{AN} \times \vec{AP} = \left(-\frac{13500}{697}, -\frac{18000}{697}, \frac{22500}{697}\right) = \frac{4500}{697}(-3, -4, 5)$$
   - Since $\|(-3, -4, 5)\|^2 = 9 + 16 + 25 = 50 = 2 \cdot 5^2$:
     $$\text{area}^2 = \frac{1}{4}\|\vec{\Sigma}\|^2 = \frac{1}{4} \cdot \frac{4500^2 \cdot 50}{697^2} = \frac{2250^2 \cdot 50}{697^2} = \frac{11250^2 \cdot 2}{697^2} = \frac{253,125,000}{485,809}$$
   - Prime factorizations:
     - Numerator: $p = 253,125,000 = 2^3 \cdot 3^4 \cdot 5^8 = (2 \cdot 3^2 \cdot 5^4)^2 \cdot 2 = 11,250^2 \cdot 2$.
     - Denominator: $q = 485,809 = 17^2 \cdot 41^2 = 697^2$.
     - Unreduced intermediate radicand in `sqrt_rational(Fraction(p, q))`:
       $$p \cdot q = 253,125,000 \times 485,809 = 122,970,403,125,000 = (11,250 \times 697)^2 \cdot 2 = 7,841,250^2 \cdot 2$$
   - Canonical reduced `Radical` and square identity check:
     $$\sqrt{\frac{253,125,000}{485,809}} = \frac{11,250\sqrt{2}}{697} = \text{Radical}\!\left(\text{he}=\text{Fraction}(11250, 697),\ \text{can}=2,\ \text{mu}=0\right)$$
     $$\text{square}(\text{rad}) = \left(\frac{11,250}{697}\right)^2 \times 2 = \frac{126,562,500 \times 2}{485,809} = \frac{253,125,000}{485,809}$$
3. **Actual Product Output Verification (`051224ee2740cbf5d55dd94633503db1f0050ada`):**
   - `route_res.status == "SERVED"`, `a4_res["route_d"]["status"] == "SERVED"`, `a4_res["envelope"]["status"] == "ok"`.
   - `route_res.exec_result.final_memory["kq_mg1"] == Radical(he=Fraction(11250, 697), can=2, mu=0)`.
   - `route_res.answers["mg1"] == "11250√2/697"`.
   - `a4_res["envelope"]["scene3d"]["objects"]` quantity `kq_mg1`: `value = "11250√2/697"`, `exact = {"kind": "radical", "coefficient": "11250/697", "radicand": 2}`.
   - `a4_res["route_d"]["sections"][0]`: Category A (`DINH_CAT_CANH`) 4-vertex certificate (`A` on `[S, A]` with `THROUGH_POINT_REUSE`, `M` on `[S, B]`, `N` on `[S, C]`, `P` on `[S, D]` with `SOURCE_NAMED`).
   - `route_res.section_certificates[0]["closure_certificate"]["area_squared"] == "253125000/485809"`.
4. **Origin of the Discrepancy & Repository Scan:**
   - The values `area_squared = 253125000/485809` and `area = 11250√2/697` are the **unique mathematically correct values**.
   - Full-repository scan (`tools/reconcile_premerge_evidence.py`) confirms **zero (`0`) occurrences** of `150062500`, `819529`, `8750`, or `1006` in any committed file in the Git tree. Those numbers were a post-compaction conversational hallucination in the final Vietnamese chat reply at the end of the previous session and never entered any committed artifact.
   - **Minor Intermediate Exponent Typo in `baseline-audit.md:53` (`W2-M4-DOC-5`):** Line 53 of [`baseline-audit.md`](baseline-audit.md#L53) writes `253,125,000 = 2^3 \cdot 3^4 \cdot 5^7 = (2 \cdot 3^2 \cdot 5^3)^2 \cdot 10 = 11250^2 \cdot 2`. While the left-hand side (`253,125,000`) and right-hand side (`11250^2 \cdot 2`) are exact, the intermediate exponent of $5$ should read `2^3 \cdot 3^4 \cdot 5^8 = (2 \cdot 3^2 \cdot 5^4)^2 \cdot 2 = 11250^2 \cdot 2` (as correctly stated in [`report.md:39`](report.md#L39) and [`review.md:32`](review.md#L32)).

---

## 3. Finding B — Holdout Wave 2 Historical & Post-Feedback Per-Case Counts

### 3.1 Authoritative Machine Comparison Table (`96` Cases: `48` Positive + `48` Negative)

All counts below are computed directly from the per-case `cases` arrays of the four machine JSON artifacts by [`tools/reconcile_premerge_evidence.py`](tools/reconcile_premerge_evidence.py) and locked in [`results/premerge-evidence-reconciliation.json`](results/premerge-evidence-reconciliation.json):

| Metric | Historical Wave 2 Raw (`scored-run-1` at `d7a94d3c` / `ecdc26b0`) | Historical Wave 2 Adjudicated (`scored-run-2` at `d7a94d3c` / `ecdc26b0`) | Source Gate `/19` Replay (`d99f6149` / `c6f6b64b`) | W2-M4 Replay (`051224ee` / `1e0c8db6`) |
|---|---:|---:|---:|---:|
| **Evidence Classification** | `INDEPENDENT_BLIND_HOLDOUT_WAVE2_RAW` | `INDEPENDENT_BLIND_HOLDOUT_WAVE2_ADJUDICATED` | `POST_FEEDBACK_DEVELOPMENT_REGRESSION` | `POST_FEEDBACK_DEVELOPMENT_REGRESSION` |
| **Positives `SERVED_CORRECT` (`/48`)** | **`3/48`** (`6.25%`) | **`5/48`** (`10.42%`) | **`45/48`** (`93.75%`) | **`46/48`** (`95.83%`) |
| **Category B (`ENGINE_DERIVED_SECTION`, `/36`)** | **`3/36`** (`W2-B08`, `W2-B12`, `W2-B14`) | **`3/36`** (`W2-B08`, `W2-B12`, `W2-B14`) | **`36/36`** (`100.0%`) | **`36/36`** (`100.0%`) |
| **Category A (`DINH_CAT_CANH`, `/12`)** | **`0/12`** | **`2/12`** (`W2-A01`, `W2-A03`) | **`9/12`** (`75.0%`) | **`10/12`** (`83.33%`, `W2-A04` repaired) |
| **Positives `FALSE_REFUSAL` (`/48`)** | **`43/48`** | **`43/48`** | **`3/48`** (`W2-A04`, `W2-A07`, `W2-A10`) | **`2/48`** (`W2-A07`, `W2-A10`) |
| **Positives `WRONG_SERVED` (`/48`)** | **`2/48`** (harness bug on `W2-A01`, `W2-A03`) | **`0/48`** | **`0/48`** | **`0/48`** |
| **Negatives Refused (`/48`)** | **`48/48`** (`100.0%`) | **`48/48`** (`100.0%`) | **`48/48`** (`100.0%`) | **`48/48`** (`100.0%`) |
| **Negative Refusal Category Match (`/48`)** | **`33/48`** (`68.75%`) | **`33/48`** (`68.75%`) | **`36/48`** (`75.0%`) | **`36/48`** (`75.0%`) |
| **Genuine `WRONG_SERVED` (`/96`)** | **`0/96`** (`2` raw harness false alarms) | **`0/96`** | **`0/96`** | **`0/96`** |
| **Exact Oracle Agreement on Served Cases** | **`3/3`** (`5/5` after harness fix) | **`5/5`** (`100.0%`) | **`45/45`** (`100.0%`) | **`46/46`** (`100.0%`) |

### 3.2 Narrative Corrections to `report.md` §2.3

1. **`W2-M4-DOC-1` ([`report.md:77`](report.md#L77)):**
   - **Erroneous text:** `historical Holdout Wave 2 raw score at d7a94d3c remains 37/48 positive SERVED_CORRECT, preserved unchanged`
   - **Verified correction:** At baseline `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c` (commit `ecdc26b012c8ce80d53524a98dc75cdcb020079d`), the historical Holdout Wave 2 raw score (`results/scored-run-1/track-a.json`) is **`3/48`** positive `SERVED_CORRECT` (`3/36` Category B, `0/12` Category A, plus `2/48` harness-induced false `WRONG_SERVED` on `W2-A01`, `W2-A03`), and the harness-corrected adjudicated score (`results/scored-run-2-harness-corrected/track-a.json`) is **`5/48`** positive `SERVED_CORRECT` (`3/36` Category B: `W2-B08`, `W2-B12`, `W2-B14`; `2/12` Category A: `W2-A01`, `W2-A03`; `0/96` `WRONG_SERVED`).
2. **`W2-M4-DOC-2` ([`report.md:79–80`](report.md#L79-L80)):**
   - **Erroneous text:** `Category B (ENGINE_DERIVED_SECTION): 36/36 SERVED_CORRECT (100.0%, up from 35/36). Category A (DINH_CAT_CANH): 10/12 SERVED_CORRECT (83.33%).`
   - **Verified correction:** Because `W2-A04` belongs to Category A (`DINH_CAT_CANH`, `stratum = P-A`), Category B (`ENGINE_DERIVED_SECTION`) was already **`36/36` (`100.0%`)** at the parent Source Gate `/19` baseline `d99f6149` (up from `3/36` at historical Wave 2 `d7a94d3c`) and remains **`36/36` (`100.0%`, unchanged from `d99f6149`)** at W2-M4 `051224ee`. Category A (`DINH_CAT_CANH`) is the stratum that rose from **`9/12` (`75.0%`) at `d99f6149`** (and `0/12` raw / `2/12` adjudicated at `d7a94d3c`) to **`10/12` (`83.33%`) at `051224ee`** when `W2-A04` transitioned from `FALSE_REFUSAL` to `SERVED_CORRECT`.

---

## 4. Additional Integrity, Complexity-Bound & Provenance Reconciliations

### 4.1 Radical Algorithm Complexity Bounds (`W2-M4-DOC-3`)

During the wave, `backend/app/simulation/geometry/radical.py` underwent two commits:
- `8ecad7bd5ff114c4be58e52ff44985a89811bf1f` (initial implementation): factored $p$ and $q$ separately in `sqrt_rational` and ran odd trial division in `_tach_binh_phuong(n)` with loop condition `d * d * d <= m and d * d <= MAX_RADICAND` ($d \le 10^6$, worst-case $\le 500,000$ odd steps for $n \le 10^{24}$).
- `051224ee2740cbf5d55dd94633503db1f0050ada` (final product commit frozen in `1e0c8db6`): restored `sqrt_rational(x)` to delegate directly to the single normalization authority `radical(Fraction(1, q), p * q)` and bounded above-ceiling square-factor extraction in `_tach_binh_phuong(n)` to the schoolbook prime factor base $B = \lfloor \text{MAX\_RADICAND}^{1/3} \rfloor = 10^4$ (`while d * d * d <= m and d * d * d <= MAX_RADICAND:`, with `isqrt(m)` folding $r$ only when $n \le \text{MAX\_RADICAND}$ or $r^3 \le \text{MAX\_RADICAND}$).

Consequently, in the final product (`051224ee` / `1e0c8db6`), the trial-division loop executes **at most $5,000$ odd steps across the entire accepted input domain $1 \le n \le 10^{24}$** (not $500,000$ steps). Specifically:
- [`architecture-decision.md:30`](architecture-decision.md#L30) retained the leftover phrase `and <= 500,000 odd steps for n <= 10^24` from `8ecad7bd`, whereas Section 3.1 and Section 3.3 ([`architecture-decision.md:36–70`](architecture-decision.md#L36-L70)), [`report.md:43–52`](report.md#L43-L52), and [`review.md:26–43`](review.md#L26-L43) state the exact `051224ee` bound ($d^3 \le \text{MAX\_RADICAND} \implies d \le 10^4$, at most $5,000$ odd steps).
- Pre-code documents [`baseline-audit.md:80–103`](baseline-audit.md#L80-L103) and [`plan.md:46–48`](plan.md#L46-L48) (authored at preregistration commit `574ad40c`) reflect the initial pre-`051224ee` design and are superseded by [`architecture-decision.md` §3.1/§3.3](architecture-decision.md#L36-L70) and [`report.md` §1.2](report.md#L41-L52).

### 4.2 Provenance of `"head"` and `"product_diff_sha256"` in `results/*.json` (`W2-M4-DOC-4`)

`results/green-after.json`, `results/source-gate-regression.json`, and `results/wave2-post-feedback-regression.json` were generated and committed in product commit `051224ee2740cbf5d55dd94633503db1f0050ada` (whose parent commit is `14bc010e4b4af2bb324c63e309d41c5c5847a904`). Because the evaluation scripts invoked `git rev-parse HEAD` and `git diff -- backend/app` on the working tree immediately *before* `git commit` created `051224ee`, their top-level metadata records the parent commit SHA `"head": "14bc010e4b4af2bb324c63e309d41c5c5847a904"` and the working-tree diff hash `"product_diff_sha256": "c730cb94bbd50e557b8d8283c8f73c741d90f32b84576fb954538de07696e147"` of `051224ee`'s `radical.py`.

### 4.3 Authoritative Artifact SHA-256 Inventory

| Artifact Path (relative to run directory) | Bytes | Raw SHA-256 (Checkout) | LF-Normalized SHA-256 (Git Blob) |
|---|---:|---|---|
| `inputs/development.json` | `21,241` | `2d189f0b8697b6244a5b46c95ce9226d69fbcf1fd84c060f3543c2fd9637de81` | `0c37d00b06e5fe93f728906e9c86e7db679846dd1558494a0372ef7886277ea8` |
| `results/red-before.json` | `11,293` | `4742f903d302fb04c6cc8083ebd220597ff5a6df49c3f199ab565599a08a9370` | `33ac13b66f3bcbb5a8cd684b17177b1040c4f00d6659611afd2f47428beb12d6` |
| `results/green-after.json` | `13,793` | `488af40da444569c62a0357a28ac4cee515bf52743584617c626ebeb8e8a7408` | `424ac18a9d8de07d9e785632761299be5c50f85e7de57ba4b797b5a17f4e161a` |
| `results/source-gate-regression.json` | `147,478` | `7d3371f64f95c7c77eee01bf1cd934f98941931ba2a1ccfce39fc30d430b0c7f` | `12aeefc9ce7eb0b9c521293c8d98160bce42d605c6270888c86433b68ca498d8` |
| `results/wave2-post-feedback-regression.json` | `145,649` | `baf469d34e8555240e8bbfdf80b2893af2081d1a5ad43b9fd75d939c62d12001` | `e9d04f93dac49f569d832358282a206e85a559c0e5e8929cb69c067e14bf5c72` |
| `candidate_divergence.json` | `1,374` | `721af146936929fe3340816579d5b3def63c3405bbecafab7c4892ae2d92984e` | `bd266fe1d70adfe480342126988ef0192ab20936a7ffa179922d61636c5e1781` |
| `verification/scope-and-evidence.json` | `1,103` | `779fa5f2a032cf42072ed91eab3b9452ee4e12e6d785fa926ea18397364846a4` | `1f7bf8bfaca0a6872b64a0ac71b2c08a0cf90bb5502291360de9d775e15f512c` |
| `verification/cache-and-fixtures.json` | `861` | `a9098b360f8eb8d28d637c145aab0c6fa097e71b0e5162ee34ee1e1347f57f2b` | `ddc9d7ab76ec819a221db96617ea98e090aa6ab53258145ff454f8abd099ed72` |
| `verification/impact-plan.json` | `1,489` | `c36e5c8f7088b6a47a8d03a6de89f06670c26cfd24c89ba0393b9bbe8e8ac63c` | `4b5bf752ce63e92abc8e4ec50f9ff9cabcaac9dccb5a15339976fb02c30b04f6` |
| `verification/tiers.json` | `2,865` | `28e8e45a5b0028ff7bcd001e28aaba6dd2d3e88f944910d8bc5ea9ec553883ec` | `28e8e45a5b0028ff7bcd001e28aaba6dd2d3e88f944910d8bc5ea9ec553883ec` |
| `verification/full-t3/receipt.json` | `1,998` | `1a7484bbee1bc130e176d6d8ee03865a771d7aa28f94a1a19ec7e36043bfadd3` | `640b012fd5034ff0c29c16930575347ba7084cc92c77fc71b18fcad79054aa1f` |
| `verification/full-t3/full-t3.log` | `167,683` | `57af94912561e1b06e3e9a4e363d80128814b755bf09232d367db048de4fcbc7` | `7370633cf1e864b023074fc4232c2125c0e1b3e764d727b13c95a0804d0c8880` |

*(Note: In the previous conversational chat summary, the SHA-256 digests quoted for `red-before.json`, `green-after.json`, `source-gate-regression.json`, and `wave2-post-feedback-regression.json` were those of the earlier `8ecad7bd` run rather than the final `051224ee` commit; the table above and `verification/scope-and-evidence.json` record the authoritative `051224ee` / `1e0c8db6` digests.)*

---

## 5. Archival Analysis & Recommended Integration Sequence for `main`

### 5.1 Current Branch & Commit Topology

Both the evaluation-only Holdout Wave 2 branch (`research/hybrid-v2-independent-vietnamese-section-holdout-wave2` at `ecdc26b012c8ce80d53524a98dc75cdcb020079d`) and the product repair lineage (`research/hybrid-v2-wave2-source-gate-language-generalization` $\to$ `research/hybrid-v2-w2-m4-exact-radical-normalization`) branch directly from `main` (`d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`):

- `d7a94d3c..ecdc26b0` (`3` commits: `5e329d75`, `7e5c3ddd`, `ecdc26b0`) adds **only** the `34` files inside `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/`.
- `d7a94d3c..HEAD` on `research/hybrid-v2-w2-m4-exact-radical-normalization` touches `0` files inside `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/`.
- Path overlap between the two branches is **strictly empty (`0` files)** (`verify_artifact_hashes_and_archival()` in `tools/reconcile_premerge_evidence.py`).

### 5.2 Why Order Matters

- If `main` (`d7a94d3c`) were fast-forwarded to `ecdc26b0` **first**, `research/hybrid-v2-w2-m4-exact-radical-normalization` would no longer be a fast-forward descendant of `main`, and rebasing the product branch onto `ecdc26b0` would violate `AGENTS.md §2` (no history rewrite) and invalidate every locked commit SHA (`c6f6b64b`, `b9e3d096`, `d99f6149`, `574ad40c`, `051224ee`, `1e0c8db6`).
- Conversely, if `research/hybrid-v2-w2-m4-exact-radical-normalization` is fast-forwarded into `main` without preserving `ecdc26b0` in `main`'s reachable DAG (or on `origin`), a single-branch clone of `main` would not contain commit object `ecdc26b012c8ce80d53524a98dc75cdcb020079d` required by `git show ecdc26b012c8ce80d53524a98dc75cdcb020079d:...` in the run-local replay tools.

### 5.3 Recommended Safe Integration Sequence (Upon Future Owner Merge GO)

1. **Step 1 — Fast-Forward `main` to `research/hybrid-v2-w2-m4-exact-radical-normalization` (`git merge --ff-only`):**
   - Advances `main` linearly from `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c` to the reconciled `research/hybrid-v2-w2-m4-exact-radical-normalization` HEAD with **zero history rewrite**.
   - Preserves the exact SHAs of product commit `051224ee2740cbf5d55dd94633503db1f0050ada` and frozen Full T3 candidate `1e0c8db668bbe110f343a8a67cdeca465008c188` on `main`'s first-parent spine.
2. **Step 2 — Integrate Holdout Wave 2 (`ecdc26b012c8ce80d53524a98dc75cdcb020079d`) via Disjoint Documentation-Only `--no-ff` Merge (plus Remote Branch/Tag Ref):**
   - Merge `ecdc26b012c8ce80d53524a98dc75cdcb020079d` into `main` (`git merge --no-ff ecdc26b012c8ce80d53524a98dc75cdcb020079d -m "docs(eval): integrate frozen Holdout Wave 2 evidence package (ecdc26b0) into main"`).
   - Because `d7a94d3c..ecdc26b0` adds only the 34 path-disjoint files under `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/`:
     - There are **zero merge conflicts** and **zero product-tree changes** (`freeze_evaluation_candidate.py --verify` remains `MATCH` on `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`).
     - Commit `ecdc26b012c8ce80d53524a98dc75cdcb020079d` (along with `7e5c3ddd` and `5e329d75`) becomes a **first-class reachable ancestor of `main`**, so every single-branch clone of `main` both checks out the 34 Holdout Wave 2 files on disk and resolves `git show ecdc26b012c8ce80d53524a98dc75cdcb020079d:...` offline.
3. **Step 3 — Post-Merge Verification Before Push:**
   - Run `freeze_evaluation_candidate.py --verify` (`MATCH`), `audit_docs_information_architecture.py` (`PASS`), and `check_publication_safety.py` (`PASS`) on `main` before pushing `main` to `origin`.
