# Run `hybrid-live-gemini-execution`

Candidate-divergence layer for the real Gemini 2.5 Flash live execution and post-Run-3 AI wire-normalizer phase of
`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (backend only; `frontend/**` untouched). It corrects
`../hybrid-live-validation/candidate_divergence.json`.

- **Canonical live evaluation report & receipts:** [`../hybrid-live-validation/LIVE_GEMINI_EVALUATION_REPORT.md`](../hybrid-live-validation/LIVE_GEMINI_EVALUATION_REPORT.md) and `../hybrid-live-validation/live-pilots-{79bbc053,48372208,8853c4b0}/` (`70 / 70` HTTP requests total; Run 3 measured `64 / 64` HTTP 200 `STOP` on candidate `44568bc9` / product `8853c4b0`, `5c0175289995b921…`).
- **Post-Run-3 candidate (`frozen-evaluation-candidate.json`):** candidate commit `428515dc`, product `f60ae29e` (`118` files, `e758e25af26707c2…`), normalizing observed wire `construct_object + target_section_id` simulation goals, omitted single-solid `MathGoalSpec.solid_id`, and out-of-vocab wire `UnresolvedSpec` hints in `backend/app/ai/typed_fact_next_extraction.py`.
- **Verdict:** `LIVE_GEMINI_MEASURED = YES` (`VERIFIED_LIVE`), `LIVE_GEMINI_QUALITY_VALIDATED = NO`, `HYBRID_CUTOVER_BLOCKED` (`DEFAULT_MODE = LLM_ONLY`, `HYBRID_ROUTE_MODE = off`, `CACHE_VERSION = 131`).
