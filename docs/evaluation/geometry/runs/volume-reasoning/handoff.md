# Handoff — `volume-reasoning` (Hybrid Wave 3A)

- **Status:** `WAVE3A_READY_FOR_GO_MAIN_REVIEW` — stop at the GO MAIN gate; no merge or push without separate owner authorization.
- **Branch:** `research/hybrid-wave3a-volume-reasoning`; base `main` = `1613e0d3ebe16f0f2fe4be755052491ff581e51b`
- **Product commit:** `4c282ecd9f15b14ddbbe6e0be0b247e455d8edca` (initial product `2e277e6ec6b87a1e64bfc8c1c9127f591fedf24f`)
- **Candidate freeze:** `0a4b6d7027624849b53b5d79a78dd6f2116cffcd` — `df262376b3f2de7bcb0c295932c7c867a7ee2bf268ed9408071e5953ee9fc821` (112 files)
- **Authoritative Full T3:** `FULL_PRODUCT_GATE_PASS` at `373116d212758458c923252ef5fb72d63d0e07fb` (`11401 passed, 1 skipped, 2 deselected, 9 xfailed` backend; `70/70` files `1146` tests frontend) — [`verification/authoritative-t3.json`](verification/authoritative-t3.json)
- **Independent review:** `INDEPENDENT_REVIEW_PASS` (round 2, `0 BLOCKER`, `0 IMPORTANT`, `0 MINOR`) — [`verification/independent-review.md`](verification/independent-review.md)
- **Report:** [`report.md`](report.md) · **Machine summary:** [`run.json`](run.json) · **Contract:** [`WAVE3A_CONTRACT_DECISION.md`](WAVE3A_CONTRACT_DECISION.md)

Key numbers: Wave 3A development corpus (`DEVELOPMENT_EVALUATION_NOT_BLIND`) 18/18 positive exact (`12/12` `volume_ratio`, `6/6` `residual_volume`, `20/20` goals), 14/14 negative refusals, 0 wrong serves; BH2C external holdout (`D:\Documents\AlgoSim-Research\BH2C` untouched) 11/11 positive on both routes, 13/13 negative refusals, 0 diffs; Wave 2C dev 16/16, SGH 10/10, SG-1..SG-6 30/30, BH2A 11/12 + sentinel + variant, NLU GOLD 60 rows all 0 diffs.

Invariants: `LLM_ONLY`, `flat`, `CACHE_VERSION = 127` (`NO_BUMP`), Hybrid NO-GO, Adapter `/2`, all 5 provider surface fingerprints unchanged, `ALLOW_LIVE_AI = 0`, 0 live calls.
