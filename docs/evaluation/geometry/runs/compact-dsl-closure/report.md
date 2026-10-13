# Compact DSL — research closure (NO-GO_ARCHIVED)

- LOCAL, 2026-10-13. User decision: **NO-GO** for the Compact Geometry DSL (C) and for compact structured JSON (B) as the
  AI → Hybrid wire format. The current Typed Facts structured JSON (A) stays. State: **`COMPACT_DSL = NO-GO_ARCHIVED`**.
- Documentation and receipts only on `main`. No DSL parser, codec, harness or production code is brought to `main`.
  LIVE GEMINI CALLS = 0 in the research and in this closure; `LLM_ONLY`, `CACHE_VERSION` 125, Hybrid off.
- The research itself lives on the archived branch `research/compact-geometry-dsl` @ `3db08a1e` and in a verified local
  bundle (§4). Its reports there are unchanged; this page summarises them and does not replace them.

## 1. What was evaluated

Three formats decoding to the same production `TypedFact` and run through the same `run_fact_route` (grounding, planner,
engine): A = current JSON with the production `responseSchema`; B = short keys + label strings, schema derived from A's;
C = line DSL, parsed. 59 cases: 35 dev (the cases DSL v0 was designed on) + 24 held-out written before any format change.
Tokens are proxies (gemma3 SentencePiece = the `google-genai` local tokenizer of `gemini-2.5-flash`; tiktoken), not billing.

## 2. Results (from [`evaluation/run.json`](evaluation/run.json), [`evaluation/metrics.json`](evaluation/metrics.json), [`evaluation/cost_model.json`](evaluation/cost_model.json))

| Item | Result |
|---|---|
| Dataset | 59 cases = 35 dev + 24 held-out |
| Semantic round trip after the fixes | 59/59, A ≡ B ≡ C on normalized facts, planner calls and route outcome; 11 injected semantic faults reach the same decision in all three |
| Held-out before the fixes | **21/24** with the DSL (H09–H11 `plane_relation` unrepresentable) — the honest held-out figure |
| Output tokens (proxy, median per case vs A) | C 0.46 · B 0.885 |
| Full request tokens (proxy) | C ≈ −15 % (median 0.846) · B **+1.6 %** |
| Gemini actual usage / cost | **NOT_MEASURED** |
| Gemini malformed output, repairs, retries, latency | **NOT_MEASURED** |
| Cost model, central assumption (compact A, median thinking 418, $0.30 / $2.50 per 1M) | C saves ≈ **$0.00037 per request** (−18 %); break-even at 21 % of requests needing one repair; ≤ $0.0014 in the most DSL-favourable model |
| Schema drift | real: `TypedFact.plane_relation` (goal-directed section slice) was unrepresentable and the serializer raised `TypeError`, while the prototype's 95 tests stayed green |
| Fail-closed defects found and fixed in the prototype | stray `"…"` string and `#` line silently dropped; 37/176 line-boundary truncations served → mandatory `END n` |
| Production consumer | none: Hybrid is not enabled in `/api/analyze` |
| Independent review | local subagent, no Critical; 2 Important fixed (B null labels, held-out independence wording) |

The cost figures are a model built on proxy tokens, measured historical thinking and the published price. They are not
live measurements and must not be quoted as Gemini usage.

## 3. Verdict and reasons

The DSL has a real representation advantage: about half the output tokens of A on the proxy tokenizers. That does not
show a lower total Gemini cost: thinking (billed as output, format-independent by assumption) and the shared prompt
dominate, and repair cost after losing constrained decoding is unmeasured. Decision criteria G0–G8 are in the evaluation
report (§2 recovery); GO needed all of them.

- **G0 not met — no product consumer.** No live result could make an integration trial useful while Hybrid is off.
- **G8 not met — a hand-written grammar has to follow `TypedFact`.** A's `responseSchema` is generated from the model;
  the DSL grammar, parser, serializer and prompt are a second copy. It drifted within one day and the tests did not see it.
- Supporting: the realistic saving (≈ $0.00037/request) is below the practical threshold set before any live run
  (≥ 25 % **and** ≥ $0.001 per served request, or ≥ 1 s p50).
- B is dominated by A on total tokens.

NO-GO is a decision for the current architecture and project stage. It does **not** say a DSL is always worse than JSON.

## 4. Preservation and recovery (local only — not an off-machine backup)

| Object | Identity |
|---|---|
| Archived branch | `research/compact-geometry-dsl` → `3db08a1e3c8a47a7284b7dbdfaac112640106593`, tree `01b0430ba090f8a77f9d706ff373b5635e2f8a7b`; prototype ancestor `a9498fdf`; not on any remote |
| New bundle | `.superpowers/preserved/compact-geometry-dsl-3db08a1e.bundle`, 96 460 bytes, SHA-256 `01e918b87ce1cdbc16ba6940e70273151d523b6b86ce7cff27d3187610943aae`; 8 commits (`45551c0f` … `3db08a1e`, incl. merge `dee744e6`) |
| Prerequisites | `9cfd0fca` and `c63efdb5`, both ancestors of `origin/main` ⇒ the bundle is **incremental**: recovery needs `origin/main` (≥ `c63efdb5`) + this file |
| Older bundle (kept) | `.superpowers/preserved/compact-geometry-dsl-a9498fdf.bundle`, SHA-256 `cb97d132…8309a1` (unchanged); a subset of the new one |

Verification on 2026-10-13: `git bundle verify` okay; in an isolated clone holding only `main` (`3db08a1e` and `a9498fdf`
absent before), `git fetch <bundle> refs/heads/research/compact-geometry-dsl:refs/heads/restored` gave `3db08a1e`,
`a9498fdf` an ancestor, the same tree id as the original, and the same SHA-256 for the files below. The isolated clone
was deleted afterwards.

```bash
git fetch .superpowers/preserved/compact-geometry-dsl-3db08a1e.bundle refs/heads/research/compact-geometry-dsl:refs/heads/research/compact-geometry-dsl
```

| File on the branch | SHA-256 |
|---|---|
| `docs/evaluation/geometry/runs/compact-dsl-format-evaluation/report.md` | `c251c46c2d69d235c81cd10c3c150733069d22a7c589b4e6a713cc490b45d57b` |
| `docs/evaluation/geometry/runs/compact-dsl-format-evaluation/run.json` (= `evaluation/run.json` here) | `88027fe6f6fa1769e73c24f8064b0bbc07338d11f1e335bd0f13bfbac42e817d` |
| `…/measurement/metrics.json` (= `evaluation/metrics.json`) | `fdfe4da10e4e7bc3c8a0b45e09a9a4421ad739b20ac949b74ce437cea479078c` |
| `…/measurement/cost_model.json` (= `evaluation/cost_model.json`) | `c6c94a7a0a876376efe65a85c8a5399dfec21e72a0ace805e77dccd57763c33d` |
| `…/measurement/payloads.json` (regenerable from the harness) | `a0ff7677c21c3d819f63ca0e890e9fa564a784edeb88ec622cec10d4603497ba` |
| `docs/evaluation/geometry/runs/compact-geometry-dsl-spike/report.md` (HOLD report, corrected by the evaluation) | `0a8b11bd52f985f359092a73fdaeb6a515dbed00d01af4785afd09ccf4ee1941` |
| `backend/scripts/compact_geometry_dsl.py` | `4263c97bd64bd1f6af67ff248ec4f6f54cbd5a1aa76df09eb0311a15f5d3b5b1` |
| `backend/scripts/fact_format_eval.py` | `0165025ae5b1eede8700d4c5cc70ab84b53fb7ea48e0162e978e41147b81150b` |
| `backend/scripts/count_payload_tokens.py` | `b7b158acf771c9f15a1231c9a2cb8bfab53de916896b20c023c6bca40136f3f9` |
| `backend/tests/geometry/fact_format_corpus.py` | `cedbfd21a16a7a6f0c8cf8a507fc8a4a4a1fe215246bed706dcfe7497c0c8474` |
| `backend/tests/geometry/test_fact_format_equivalence.py` | `53cfd5398b120cb93b657650c53cf10586bb39815eb7e8937c9006235dc40e61` |
| `backend/tests/geometry/test_compact_geometry_dsl.py` | `c44c6b1db9a8be306a08b35a0532289a702683bccabe19783a17b848eca99580` |

The three JSON receipts in [`evaluation/`](evaluation/run.json) are byte copies (same Git blob ids) so the numbers survive
on `origin/main` even if the local branch and bundle are lost. Code, corpus, tests, payloads and full reports do **not**
survive such a loss: there is no remote or off-machine copy of the branch.

Reproduce (after recovery, 0 model calls): from `backend/`, `pytest tests/geometry/test_fact_format_equivalence.py
tests/geometry/test_compact_geometry_dsl.py` (320 passed at `3db08a1e`), and `python scripts/fact_format_eval.py --out
<new dir> --tokenizer-python <python with tiktoken + google-genai[local-tokenizer]>` (byte-identical `metrics.json`).

**Branch state: `ARCHIVED_NO_ACTIVE_WORKTREE`.** `git branch -d` refused (not merged), as intended; no `-D`. The branch may
be deleted with `-D` only after the user approves it **and** an off-machine copy of the bundle (or a remote ref) exists and
has been verified the same way as above, because the local bundle is then the only copy.

## 5. Reopen trigger

Reopen only when both hold: (1) Hybrid fact extraction is approved for a real product path; (2) real `usageMetadata` of A on
that path shows non-thinking output ≥ 30 % of billed cost, or output generation ≥ 1 s p50. Then the prepared A/C live
experiment may be proposed (frozen held-out H01–H24, `gemini-2.5-flash`, ≤ 144 requests, expected ≈ US$0.30, worst case
≤ US$3.10, separate approval). Before that, fix the two review leftovers: pin DSL kind coverage beyond field names, and
decide `\r` / U+2028 inside quotes.

## 6. Cleanup

| Item | Result |
|---|---|
| Worktree `.superpowers/worktrees/dsl-spike` | clean (0 tracked changes, 0 untracked; ignored = `__pycache__` + an empty-schema test `backend/algosim.db`, all tables 0 rows, SHA-256 `f0096c4c…`, not the protected root DB); no junction; no process. Removed with `git worktree remove` (no force): deregistered **and** physical directory gone |
| Content removed | worktree 1 691 857 441 bytes (13 292 files; D: free space +1 726 337 024 bytes observed) · this research's session scratch 2 306 422 562 bytes (recovery clone, its tokenizer venv, review snapshot, re-measurement, probe scripts) · its tokenizer model cache `%LOCALAPPDATA%\Temp\vertexai_tokenizer_model` 4 689 074 bytes (created 2026-10-13 17:41 by the measurement) · empty `%TEMP%\claude\dslprobe`. Total 4 002 969 077 bytes; C: free-space delta UNKNOWN (no snapshot before) |
| Kept as protected | the older session's `tokvenv` and `tiktoken-cache`, old `.superpowers/scratch/`, root `backend/algosim.db`, `frontend/public/`, `.superpowers/preserved/` (both DSL bundles + the real-model bundle), branches `docs/real-model-e2e-readiness` and `feat/real-model-pilot-tooling`, pilot commit `471a2c79`, historical A/B evidence, candidates and correction layers |
| Remaining worktrees | `main` only |
