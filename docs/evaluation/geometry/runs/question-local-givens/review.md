# Independent LOCAL review

Reviewed range: `232c1225..06cd8cdf`. One reviewer completed the review with a fresh context (gpt-6.1-sol); the first requested reviewer failed on a usage limit before reviewing. No Claude Cloud or model/provider geometry requests.

Reviewer independently ran existing focused suites: 224 passed, 4 xfailed (provider pins included); benchmark 19/9/0/2. Its adversarial probes: 19 failed, 4 passed. Verdict at `06cd8cdf`: NO-GO.

| Finding | Reproducer / effect | Resolution |
|---|---|---|
| C1: uncovered context | `Tính SC. Tính SC khi SA = 5.`, `Tính SC. SA = 5.`, later parallel assertion, auxiliary short quote → old answer and scene | Require coverage of following context and reject scoped contexts independently of an earlier clean ask |
| C2: omitted original shapes | Original SA perpendicular to base or square side 2 omitted from payload; typed local SB perpendicular / side 4 → replacement figure served | Validate original source shape constraints against the same canonical calls whenever local context is checked; no omission authorizes replacement |
| C3: construction bypass | `Vẽ thiết diện … cắt bởi (MAB), biết SA = 5.` → old scene | Construction call context is checked independently of recognizing the verb `dựng` |
| I1: canonical side false refusal | `Tính SC, biết AB = 2.` refused although a validated square side 2 supplies AB | Include direct segment values and canonical polygon sides, reusing engine length authorities |

All four findings were reproduced by the executor with the committed regression file `backend/tests/geometry/test_question_context_review.py`: **19 failed / 4 passed RED**, then **23 passed GREEN** as part of the **861 passed / 4 xfailed** cluster. Critical/Important fix pass: one. No second independent review is claimed; closure is by RED→GREEN and the subsequent clean-worktree product gate.

No Minor findings. Declined judgments and executor rulings:

- Real-provider extraction/live budgets: prohibited; no real-model accuracy or live GO claimed.
- General scoped replacement/theorem proving: excluded; scope changes remain refused.
- Arbitrary language and unit conversion: no general parser/converter added; source coverage outside the closed vocabulary remains unsupported.
- B27/B28 and multi-step planning: excluded; proposed next slice only.
- Renderer appearance/orbit P1: unchanged; Phase 1 evidence retained, P1 not fixed.
- T3/candidate/divergence/integration: executor obligations, recorded in this run after this review. Phase 2 merge/push not authorized.
- Concurrency/throughput: no mutable state added; no production-load claim.

These decisions preserve the authorized bounded repair. Their cost is safe refusal of unsupported requests and no claim about unmeasured provider/renderer/load behavior.
