# Consolidated Owner GO request — live paired measurement for Hybrid production cutover

**What it unblocks:** this is the only decision blocking D-04, D-11, D-13 and GATE-16.

**Defaults without a GO:** `MAX_AUTHORIZED_LIVE_REQUESTS = 0` and `MAX_AUTHORIZED_LIVE_SPEND_USD = 0`. No live call has been made.

**Scope:** approving this does not switch production. Cutover is decided by the pre-registered criteria in item 10, applied to the results.

**Provider facts** below were checked against official Google documentation on 2026-10-31 (`provider-facts.md`).

**Update, fifth continuation (2026-10-31). It supersedes the fourth-continuation measured system and curved finding below.**
- **Measured system:** candidate `98df8189` (118 files, `2f8c9945…`). `--manifest` prints the hash to bind.
- **Curved solids on Hybrid /4:** cylinder, cone and sphere volume, lateral area, sphere surface and radius are now served exactly, with π kept; the independent review is READY.
- **Still refused on Hybrid, but served by LLM_ONLY:**
  - curved **sections** (parallel or axial);
  - the cone ratio / remaining volume;
  - curved composites (inscribed / circumscribed);
  - diameter phrasings.

  A corpus with several such problems would still cost Hybrid served-correct under criterion 2.
- **The corpus must not be shaped around this.**

**Update, fourth continuation (2026-10-31):**
- **Measured system:** it is now candidate `5caa6e94` (118 files, `f0ebd8df…`), which includes the M-3 fix and registry /22. `--manifest` prints the exact `measured_system` and `harness_sha256` to bind.
- **Acceptance contract:** reviewed `ACCEPTANCE_CONTRACT_REVIEW_READY` (protocol revisions A–D).
- **Decision-relevant finding:** Hybrid /4 refuses every curved solid. The corpus admits curved solids as expected-serve, and criterion 2 tolerates a net loss of only 2 of 45. **If the author includes 3 or more curved serve problems, the run will almost certainly end `HYBRID_CUTOVER_NO_GO`.** You can choose to:
  - (a) run now, as a measurement of the current product; or
  - (b) first let the agent build curved solids on /4 offline, then run.

  Either way, the corpus must not be shaped around this: the author writes it independently.

| # | item | proposal |
|---|---|---|
| 1 | Provider | Google Gemini API `v1beta generateContent`, on the Owner's **paid (billed) Cloud project**. The free tier is excluded because its content may be used for product improvement and human review. |
| 2 | Exact model | `gemini-2.5-flash`, the production default, for both arms. **Check first:** Google now limits 2.5 access to accounts that used it before. If the Owner's key cannot use it, the production model itself is unavailable, which needs a product decision; there is no silent model switch. |
| 3 | Maximum live requests | **400 HTTP requests** in total, both arms, retries included. Expected 180–300 (60 problems × Hybrid 1 + LLM_ONLY 2–4, plus retries). |
| 4 | Maximum cost | **USD 70 hard cap**, enforced client-side before every request on the exact payload: input ≤ UTF-8 bytes; output ≤ the request cap, else 65 536 including thinking. A request that could break the cap is never sent. A provider prepay balance or project spend cap is recommended as a second line. |
| 5 | Expected cost | About **USD 2–8**: Hybrid ≤ USD 0.024 per request ceiling, LLM_ONLY ≤ about USD 0.17 per request ceiling (uncapped output), at USD 0.30 / 2.50 per million input/output tokens (official, 2026-10-28). Actual spend comes from `usageMetadata`; until measured it is UNKNOWN. |
| 6 | Data sent | Only the authored problem texts plus each arm's system prompt and schema. No learner, account, image or repository data. |
| 7 | Privacy | On the paid tier, Google logs prompts and responses for a limited time only for abuse and legal purposes, and does not use them for product improvement. Locally, only decoded structured outputs and hashes are kept; keys and headers are never written. |
| 8 | Measurement class | `PREREGISTERED_LIVE_PAIRED_EVALUATION`; held-out claim `NEW_UNOPENED_SET`, with the corpus hash recorded at freeze |
| 9 | Dataset author and independence | **Not yet established.** The Owner must name an author who is not the implementer (the Owner or a nominated teacher). The author writes 45 serve and 15 refuse problems with hand-computed exact oracles before any run (`heldout-authoring/`). The serve problems include curved solids with π answers: LLM_ONLY serves them today, so a Hybrid refusal there is counted as a capability loss. Without a named author the run is only `IMPLEMENTER_AUTHORED_DIAGNOSTIC` and **cannot** satisfy D-13. **No author name is invented here.** |
| 10 | GO/NO-GO for cutover | Protocol §7 (revision A), which is not re-tuned after results. It is computed by the harness's `acceptance()`:<br>• a complete paired run with the pre-registered composition<br>• Hybrid wrong-served 0 observed, and no excess over LLM_ONLY. The Wilson 95% bound is reported, not compared.<br>• served-correct not worse: McNemar does not favour LLM_ONLY, and the difference is ≥ −5 pp<br>• 100% of expected-refuse cases refused, with reason accuracy ≥ LLM_ONLY<br>• median latency ≤ LLM_ONLY, and p90 ≤ 1.5× LLM_ONLY<br>• USD per served-correct ≤ LLM_ONLY<br>• infrastructure failures ≤ 5%<br>• independence established |
| 11 | Early stop | Protocol §5 and the harness: served expected-refusal, 80% of the cap, the request cap, the cost ceiling, 3 consecutive infrastructure failures, any identity change |
| 12 | Independent reviews | Architecture review: see `architecture-review.md`. Evaluation-readiness review: see `evaluation-readiness-review.md`. |
| 13 | What Claude does after a valid GO | Freeze the corpus hash into a protocol amendment; run `--live` under the approved terms without asking per request; record rows, the summary and the stop reason; get an independent review of the results; apply item 10. Only if every criterion passes: run the cutover checks, then retire legacy by parity and last consumer. Otherwise report `HYBRID_CUTOVER_NO_GO` and keep LLM_ONLY. |

**What the Owner provides:**
1. An approval JSON written by the Owner. Required fields:
   - `owner_decision`;
   - `corpus_sha256`;
   - `measured_system` and `harness_sha256`, which bind exactly what is measured. They are printed by `--manifest`.
   - `max_requests`, `max_usd`;
   - `model`;
   - the two prices;
   - `llm_only_output_reservation_tokens` ≥ 65 536;
   - `corpus_author`, `authoring_independence` and `evaluator_independence` (`ESTABLISHED` or not). Criterion 7 reads these; without them the verdict is NO-GO.
2. The author's name.
3. `ALLOW_LIVE_AI=1` and the key, for the run only.

The agent never writes the approval value.
