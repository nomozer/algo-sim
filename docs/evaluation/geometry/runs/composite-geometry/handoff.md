# Handoff — `composite-geometry` (Hybrid Wave 2C)

- **Status:** `WAVE2C_READY_FOR_GO_MAIN_REVIEW` — stop at the GO MAIN gate; no merge or push without separate owner authorization.
- **Branch:** `research/hybrid-wave2c-composite-geometry`; base `main` = `78bd68764a69c513086b844ab3ed5e29ae18ce04`
- **Product commit:** `050bb35377b40146d4862afe050a40228821a758`
- **Candidate freeze:** `962b97237246b65bb2d4abc6ebed9bc5b971f5fd` — `3e6c403cff0e2c4ae96c4a541f97ecbe92f1efd821e08d5fdb1572d4ee823ab9` (112 files)
- **Authoritative Full T3:** `FULL_PRODUCT_GATE_PASS` at `0acfa9e96fc41d8ca6ba79983f49391553349a3a` (attempt 2; attempt 1 harness failure kept) — [`verification/authoritative-t3.json`](verification/authoritative-t3.json)
- **Independent review:** `INDEPENDENT_REVIEW_PASS` (round 2) — [`verification/independent-review.md`](verification/independent-review.md)
- **Report:** [`report.md`](report.md) · **Machine summary:** [`run.json`](run.json)

Key numbers: development 16/16 exact (main 0/16), 14/14 refusals, 0 false serves; SGH known regression 10/10, 16/16
goals, 5/5 negative; SG-1..SG-6 30/30 unchanged; BH2A unchanged; NLU GOLD 0 changed; backend 11,391 / frontend 1,146.

Invariants: `LLM_ONLY`, `flat`, `CACHE_VERSION = 127`, Hybrid NO-GO, Adapter `/2`, `ALLOW_LIVE_AI = 0`, 0 live calls.
