# AXO HYBRID /8 — REAL STUDENT PILOT & INDEPENDENT H-1 GOVERNANCE PROTOCOL (Phase P7 / Gate D7)

- **Status:**
  - `REAL_STUDENT_USABILITY = NOT_MEASURED` (`Gate D7 = NOT_MEASURED`)
  - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`
  - `sealed_H1` (`hybrid-independent-h1`): **UNOPENED** (`0` items read or evaluated; `H1_CORPUS_INTEGRITY.json` = `AWAITING_INDEPENDENT_CORPUS`)
  - `locked_W2_W3` (`hybrid-v2-independent-vietnamese-section-holdout-wave2` & `wave3`): **UNTOUCHED**
  - Prior approval templates (`k1`, `r1`, `s2`): all remain at **`PENDING_OWNER_DECISION`**
- **Anti-Fabrication Rule (`/8 §14`):** No synthetic agent prompts or simulated personas may be reported as real student feedback or classroom evaluation.

---

## 1. Prerequisites for Launching a Real User Pilot (`BLOCKED` Until Met)

1. Written approval from project owner and participating school/educator coordinator.
2. Ethical & data protection review covering minor participants (parental/guardian consent for students under 18, student assent, explicit opt-out without academic penalty).
3. Hardware target alignment (separating `>= 8 GiB` Windows laptops vs `4–6 GiB` target devices once physical low-end validation in `Gate D4` completes).
4. Frozen candidate release boundary (`local-slm` mode explicitly marked scoped/experimental or constrained-primary; zero silent fallback to cloud AI without user disclosure).

---

## 2. Participant Selection & Cohort Design

| Cohort | Minimum Target N | Eligibility Criteria | Stratification |
|---|---|---|---|
| **Students (Grades 11–12)** | `30–45` participants across `>= 2` schools / study groups | Studying Vietnamese THPT solid geometry (`Hình học không gian`), self-typing or pasting homework problems directly without researcher rewriting | Mix of textbook standard phrasing, casual chat phrasing, incomplete drafts, and out-of-scope questions |
| **Mathematics Teachers / Tutors** | `6–10` teachers | Teaching Vietnamese high-school geometry; reviewing both served 3D scenes/steps and refusal clarity | Independent from AlgoSim engineering & authoring team |

---

## 3. Consent, Privacy & Data Governance

- **No unnecessary PII:** Never store full student names, phone numbers, school IDs, IP addresses, or account credentials alongside submitted problems.
- **Pseudonymized session IDs:** Assign random per-session UUIDs (`stu_001`..`stu_N`); strip incidental greetings containing real names before archiving in any evaluation corpus.
- **No model training on held-out pilot data:** Collected user inputs are quarantined strictly for holdout evaluation & usability auditing unless separately consented and versioned into a future training corpus (with disjoint split).

---

## 4. Study Protocol, Collection Workflow & Metrics

Each participant completes **8 tasks** (6 natural-wording homework prompts typed/pasted in their own words + 2 intentionally underspecified/out-of-scope traps) under blinded presentation or alternating sessions (`live` vs scoped `local-slm` when hardware permits):

1. **Mathematical & Scope Correctness (Independent Teacher Adjudication):**
   - Exact answer verification against independent closed-form derivation / coordinate kernel (`axo-math-evaluator/2`).
   - Safe refusal audit: verify `0` fabricated premises or silent hallucinations when a student omits a height, introduces a contradiction, or asks a curved/unsupported topic.
2. **Refusal Comprehension Rate (Critical Safety Metric):**
   - Prompt the student after any `REFUSED` or `CLARIFICATION` / `OUT_OF_SCOPE` card: *"Hệ thống đang yêu cầu bạn bổ sung hoặc sửa thông tin nào?"*
   - Target: **`>= 85%`** of refusals accurately understood by students on first reading (measured specifically because technical internal codes or cryptic `SOURCE_PREMISE_UNREAD` messages can confuse novices unless mapped to plain Vietnamese student guidance).
3. **Perceived Latency & Interactive Tolerance:**
   - Record both wall-clock backend latency (`ms`) and student 5-point Likert rating (`1 = Quá chậm, bỏ dở` to `5 = Phản hồi nhanh, chấp nhận được`), measuring abandonment rate per latency bucket (`<= 3s`, `3–5s`, `5–8s`, `> 8s`).
   - Rationale from `Gate D4`: while local CPU `p95` sits above `5.0 s`, interactive usability tolerance without streaming/progress UI cannot be assumed `PASS` from backend RSS alone.
4. **Task Completion & Pedagogical Construction-Step Usefulness:**
   - End-to-end task completion rate (student successfully revises an incomplete prompt after clarification until `SERVED` when mathematically solvable).
   - Teacher + student rating of `Scene3D` + cumulative `construction_steps` helpfulness (`1–5` scale).

---

## 5. Independent Evaluation & Sealed H-1 Handoff Rules

1. External teacher adjudicators (who did not author AlgoSim rules or SLM training sets) score mathematical correctness and step pedagogical clarity independently on anonymized logs.
2. **Sealed `H-1` & `locked W2/W3`:** Opening [`hybrid-independent-h1`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/hybrid-independent-h1/H1_CORPUS_INTEGRITY.json) requires an independent external image/text corpus populated by a separate curator plus explicit owner approval via the `C21`/owner-approval workflow — it remains completely untouched (`0` rows accessed) throughout `/8`.
