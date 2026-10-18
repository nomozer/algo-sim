# Handoff — `hybrid-offline-readiness-finalization`

## 1. Executive Summary & Verdict

- **Verdict:** **`HYBRID_OFFLINE_READINESS_PARTIAL`**
- **Why `PARTIAL` (not full `HYBRID_OFFLINE_READINESS_VERIFIED`):**
  1. All scoped implementation and offline readiness items in this wave are verified and green:
     - Backend source-length / vector-zero fix (`ISSUE-ARCH-SOURCE-LENGTH-READER-VECTOR-ZERO`, `CACHE_VERSION = 126`),
     - Frontend `HFOI-F3`, `HFOI-F5`, `HFOI-F6`, single wrapper validation boundary (`docPhanHoiHybrid` / `kiemHybridView`), and final-step observation anchor enforcement,
     - Minimal pedagogical answer disclosure (`Xem đáp án` / `Ẩn đáp án`) preserving exact data and certified distance witnesses while hiding answer cards/labels by default,
     - Offline E2E browser harness (`48/48` checks PASS), targeted disclosure browser checks (`4/4` suites PASS across cube, regular square pyramid, cuboid distance, and replacement/refusal/legacy), `41/41` regenerated fixture response parity, `12/12` independent hand-coordinate oracle checks,
     - Authoritative T3 (`FULL_PRODUCT_GATE_PASS` at refrozen candidate `f8423d4b87f942d3d850970c741bcf4ee6d2c634`) and independent read-only reviews (`PASS`, 0 blocking/important findings).
  2. However, **two explicit architectural boundaries remain open by design**:
     - **`HFOI-F4` exact relation operands (`PARTIAL`):** Adapter `/2` (`hybrid-route-d-preview/1`) carries `planner.trace.goal_checks` relation types and check IDs, but does **not** carry the exact geometric operand pairs (e.g., naming `BC` and `(SAB)`). Identifying exact operands requires an Adapter `/3` contract and regenerated fixtures.
     - **Production Hybrid transport:** No production frontend caller invokes `/api/preview/hybrid` (`DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`). Browser verification uses the offline injected fixture harness (`__HFOI__.nap`), so **no Product End-to-End PASS** is claimed.

---

## 2. Recovery & Multi-Agent Lineage (`Claude Opus 5.5 → Codex → Gemini`)

- **Base (`main` = `origin/main`):** `f2b00ed3ec1e333e3b5c18c046ac5beec1f7b6fb`
- **Branch / Worktree:** `research/hybrid-offline-readiness-finalization` at `.superpowers/worktrees/hybrid-offline-readiness-finalization`
- **Preserved commits (`f2b00ed3..f8423d4b`):**
  1. `c55374cc` — `fix(grounding): stop reading segment lengths out of vector, sum, product and conditional expressions`
  2. `9088fedb` — `eval(hybrid-offline-readiness): record the source-length fix evidence, reader parity and the cache bump decision`
  3. `479e04d5` — `feat(frontend): validate the Hybrid preview wrapper once and stop presenting a = 1 values as general answers`
  4. `c6693e1e` — `eval(hybrid-offline-readiness): record the offline E2E harness, the independent oracle and the browser receipts`
  5. `9d17557e` — `fix(grounding): close the review findings on the source-length predicate and finish the cache bump`
  6. `cc07f512` — `fix(frontend): close the review findings on the Hybrid preview adapter`
  7. `b59d14bc` — `eval(hybrid-offline-readiness): refresh the evidence after the review fixes`
  8. `8bcb9d8e` — `fix(grounding): finish preserved second-review source length corrections`
  9. `531b7143` — `feat(scene3d): reveal validated Hybrid answers only on learner request`
  10. `794563cb` — `fix(grounding): keep radical vectors and conditional magnitudes out of source premises`
  11. `8ee9e3eb` — `fix(frontend): reject premature observation anchors and malformed preview entries`
  12. `2af99e0e` — `fix(scene3d): retain distance witnesses when answer labels are hidden` (**final product commit `2af99e0eddb67da253adcf6dc0aa7ac4fd08b05d`**)
  13. `00b7bba4` — `test(eval): align offline gates with explicit answer disclosure and record recovery`
  14. `96e2fe1e` — `chore(eval): freeze offline readiness candidate with learner answer disclosure` (superseded candidate; T3 recorded in `verification/t3-96e2fe1e-superseded.json`)
  15. `efbdc5a7` — `test(eval): align thesis runner divergence reader with active cache 126 head and record offline verification receipts`
  16. `f8423d4b` — `chore(eval): refreeze offline readiness candidate after test alignment` (**authoritative T3 candidate `f8423d4b87f942d3d850970c741bcf4ee6d2c634`**)

---

## 3. Verified Summary Table

| Gate / Scope | Status | Key Metrics & Receipt |
|---|---|---|
| **Product Identity & Freeze** | `MATCH` | Product `2af99e0eddb67da253adcf6dc0aa7ac4fd08b05d`, Candidate `f8423d4b87f942d3d850970c741bcf4ee6d2c634`, `111` files, `cb11bc7757466bd6c52cd063e975c4540514bac6c49acc70c4d4dfca7fff660c` |
| **P1 Backend Source-Length / Vector-Zero** | `PASS` | `loai_nhan_doan` shared authority; `185` targeted tests PASS; `1896`-text reader parity (`22` intended fixes, `0` regressions) (`verification/reader-parity-final-diff.json`) |
| **Cache Version & Policy** | `PASS` | `CACHE_VERSION = "126"`, `cache_identity.lock.json` relocked, `7/7` confirmation probes (`verification/cache-final.json`) |
| **P2 Frontend `HFOI-F3, F5, F6`** | `PASS` | Symbolic answers vs `a = 1` construction qualifier (`ghiChuGiaTriDung`), neutral `verification_gap` wording, `SOURCE` vs `UNKNOWN` attribution |
| **P2 Frontend `HFOI-F4`** | `PARTIAL` | Single wrapper boundary (`docPhanHoiHybrid` / `kiemHybridView`), final-step observation anchor enforced; exact relation operands unavailable in Adapter `/2` |
| **P2B Pedagogical Answer Disclosure** | `PASS` | Default hidden, explicit `Xem đáp án` / `Ẩn đáp án`, keyboard-accessible, reset on analysis replacement, distance witnesses & exact payloads preserved (`p2b-disclosure/final-browser.json`) |
| **P3 Offline E2E & Oracle** | `PASS` | `41/41` fixture responses byte-identical (`verification/offline-summary.json`), `12/12` independent oracle + `4/4` mutated-witness catches (`verification/oracle-final.json`), `48/48` browser E2E checks PASS with `0` provider/forbidden calls (`verification/offline-browser-final.json`) |
| **P4 Authoritative T3 (Clean Detached)** | `FULL_PRODUCT_GATE_PASS` | Detached `.superpowers/worktrees/t3-hybrid-offline-readiness-final` at `f8423d4b`: Backend `10950 passed, 0 failed`, Frontend `70 files / 1143 passed`, Build `PASS`, Demo `5/5`, Crash `6/6` (`verification/authoritative-t3.json`) |
| **Independent Read-Only Review** | `PASS` | Codex continuation review + Gemini subagent review (`8156e1fc`) at `f8423d4b`: `0` critical, `0` important, `0` minor findings (`review.md`) |
