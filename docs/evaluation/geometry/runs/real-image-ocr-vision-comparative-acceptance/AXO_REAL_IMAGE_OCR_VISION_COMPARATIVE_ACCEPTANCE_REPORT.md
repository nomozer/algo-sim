# AXO — Real-image OCR/Vision comparative acceptance

Status: **OFFLINE_EVALUATION_WITH_LIMITS; REGRESSION=BLOCKED_GATES_REMAIN; LIVE/HUMAN/H1 NOT_MEASURED; ARCHITECTURE DECISION_PENDING_LIVE_EVIDENCE**. No merge, push or deploy.

Product checkpoints:2969e9e76 and7b1700214; baseline6bb22fa3b. Planner/26, Registry/33, Engine/24, height-invariance-certificate/2, output-policy/1 and cache132 unchanged. Candidate measured hash recorded in run.json; full working-source fingerprint in regression receipts additionally covers UI files outside the115-file freeze surface.

Actual offline API measurements use HYBRID_ROUTE_MODE=local-first, HYBRID_LOCAL_FIRST=1, ALLOW_LIVE_AI=0 and an empty provider key. The official live Hybrid default and deployment configuration are unchanged. A503 LIVE_AI_DISABLED is an infrastructure refusal, not evidence of mathematical out-of-scope classification.

This run corrects [the original report](../image-first-ocr-verified-geometry/ALGOSIM_IMAGE_FIRST_OCR_VERIFIED_GEOMETRY_REPORT.md), preserving historical bytes. See [metric reconciliation](prior_metric_reconciliation.json), [baseline audit](baseline_integrity.json) and [review](review.md).

## Owner questions

|#|Question|Classification|Finding|
|---:|---|---|---|
|1|Baseline OCR|VERIFIED FACT|Actual rerun16 images/17 variants:1/11 local auto in supported printed instances;10/10 further simulated corrections served correctly;6 other variants unserved. Keep the arms separate.|
|2|CER discrepancy|VERIFIED FACT|Five polyhedral cases median0.1135; all12 median0.1040. All source per-case scores reproduce receipts; report0.0110 is an unreproducible reporting error, not a new normalization result.|
|3|Full regression|VERIFIED FACT|Product tests=PASS; backend 14259 passed, 7 skipped, 3 deselected, 15 xfailed, 1 warning in 554.92s (0:09:14). Overall gates=BLOCKED_GATES_REMAIN; whole-HEAD publication remains blocked by97 unchanged baseline pending entries. Exact commands/exclusions below.|
|4|New images found|VERIFIED FACT|31 fresh downloads;5 relevant selected. Three older acquired-but-unevaluated geometry images added with exposure disclosed.26 irrelevant algebra images excluded; source stopped at429.|
|5|Eligible new corpus|VERIFIED FACT|8 relevant technical images:2 development/6 frozen external evaluation. This falls short of20–30; only1 evaluation item is a named-polyhedron distance problem in solver scope.|
|6|Verified ground truth|NOT_MEASURED|0 HUMAN_VERIFIED;8 AGENT_TRANSCRIBED_UNVERIFIED references. No independent scorer or sealed H-1.|
|7|Printed/handwritten accuracy|VERIFIED FACT|Printed evaluation draft median CER=0.1165; handwriting NOT_MEASURED (no new handwritten sample). Prose+choices references exclude diagram labels/footer: insertions reflect both segmentation and recognition.|
|8|Critical math tokens|VERIFIED FACT|Evaluation token micro precision=0.7944, recall=0.6911; exact-substring fact proxy=19/27. These are not semantic fact precision/recall; answer-choice strings in the manifest must be excluded from premise claims.|
|9|Fully exact images|VERIFIED FACT|0/6 exact full statements;1/6 exact math-token sequences, against agent references.|
|10|New local automatic solves|VERIFIED FACT|0/8;0/6 evaluation. All eight API preparations require confirmation; no oracle text enters the automatic arm.|
|11|Need corrections|VERIFIED FACT|8/8 require review/confirmation, which does not mean all can be solved after correction. Simulated span corrections did not serve a new result.|
|12|Need Vision|NOT_MEASURED|No calibrated count of images uniquely requiring Vision. Handwriting/diagram coverage remains a hypothesis for Vision, not measured success.|
|13|False acceptance|VERIFIED FACT|0 observed automatic acceptances on8 images; no automatic accepted item to grade. Do not claim a population false-acceptance probability or zero silent corruption.|
|14|False refusal|NOT_MEASURED|No independently adjudicated eligible-support oracle set. Known r446 has correct answer√3/3 but existing kernel deduction gap; token-exact r310 still has diagram and prose ambiguity.|
|15|Live Gemini Vision|BLOCKED|NOT_AUTHORIZED / LIVE_VISION_NOT_MEASURED;0 actual calls. No real recorded Vision replay exists for this corpus.|
|16|Live cost/latency|NOT_MEASURED|Unknown, not0. Authorization preflight exists; actual live executor/cost accounting remains deliberately unconnected pending authorization.|
|17|Adaptive benefit|INFERENCE|Mock transcript cross-check improves six authored conflict/control fixtures; it establishes routing safety only. Recognition/latency/cost superiority over local-only remains unmeasured.|
|18|Replace OCR model|INFERENCE|No evidence justifies a model replacement yet; no new model or training. New corpus too small and mostly outside solver scope.|
|19|Handwriting improvement|NOT_MEASURED|No new handwritten evaluation or recognition algorithm improvement claimed; prior handwriting case remains unserved.|
|20|Real student usability|NOT_MEASURED|No real participant; automated browser scripts are not students.|
|21|Correction actions|VERIFIED FACT|Per-case scripted edits/confirmation actions in user_correction_e2e.json; no human time-to-correct/keystroke benefit claim.|
|22|Stale cache|VERIFIED FACT|Browser text-edit scenario changes answers and Scene3D without re-preparing image; further span/free edits clear old confirmation. Other cache states are covered only as explicitly tested.|
|23|Correct image-to-result|VERIFIED FACT|Prior development11 outcomes:1 LOCAL_AUTO,10 USER_CORRECTED_SIMULATED. New corpus0 served. Never combine local, simulated, live or real-user categories into one accuracy.|
|24|Scene3D|VERIFIED FACT|Actual browser6/6 existing scenarios and4/4 confirmation checks; supported prior scenes render and continuity checked. No new corpus scene served; no blanket geometric fidelity claim.|
|25|Combined RSS|VERIFIED FACT|Measured precursor4ab43853 warm miss combined sampled-peak p50=746.1MiB,p95=882.0MiB,n=10. Includes Windows venv launcher, actual interpreter and descendants, not just4MiB launcher. Shared working sets may double count pages. Sealed candidate 70b22cc71 re-measured: combined p50=751.1MiB,p95=875.3MiB; OCR process tree alone p50=618.5MiB,p95=742.8MiB (n=10).|
|26|Cold/warm latency|VERIFIED FACT|Precursor HTTP prepare-only p50/p95: cold-model4596/7916ms(n10);warm miss2532/3012ms(n10);cache161/321ms(n10). Sealed candidate 70b22cc71 re-measured (n10 each): cold-model7151/16707ms;warm miss3711/5687ms;cache240/398ms. Fresh FastAPI process (n5): start-to-health3034/6153ms, first image6440/9019ms, next image3572/18858ms, repeat371/777ms. The two runs differ in host load (whole-machine CPU busy80% vs89%, OCR itself included), so the difference is NOT a measured regression or improvement. Do not add stages or call prepare latency upload-to-Scene3D.|
|27|Physical low-end|NOT_MEASURED|12 logical CPU/16GB shared host; PHYSICAL_LOW_END_NOT_MEASURED. Host CPU busy80% (precursor) and89% (sealed candidate) during the benchmarks, the OCR engines' own threads included; available RAM1916MiB at start. Not an isolated hardware claim.|
|28|Independent H-1|NOT_MEASURED|H1_NOT_MEASURED. Frozen external split is developer-collected and agent-transcribed; old12 VMMU images are exposed development/regression material.|
|29|Architecture choice|INFERENCE|Provisional local-first+targeted confirmation; DECISION_PENDING_LIVE_EVIDENCE. No empirical basis to rank Vision-first or adaptive live quality/cost.|
|30|Rust/training|INFERENCE|No new evidence requiring Rust, GPU or training. Engine inference dominates CPU; retain existing stack pending representative licensed data and approved comparison.|
|31|Pilot readiness|BLOCKED|Not ready for unrestricted student pilot: new corpus has0 solves, no human usability/live comparison/H1, and concurrency is checked only for two simultaneous uploads on SQLite (20/20 on the sealed candidate). Supervised technical evaluation with declared limits is feasible.|
|32|Remaining limits|VERIFIED FACT|Small nonrepresentative corpus, unverified transcriptions, recognition/segmentation errors, unresolved geometry capability gaps, no live Vision/human/H1/physical-low-end evidence, and limited concurrent-load follow-up.|

## Regression and acceptance boundaries

- `backend_pytest`: **PASS**; 14259 passed, 7 skipped, 3 deselected, 15 xfailed, 1 warning in 554.92s (0:09:14)
- `frontend_test_wave`: **PASS**; ['Test Files  139 passed (139)', 'Tests  2018 passed (2018)', 'Duration  48.13s (transform 4.56s, setup 1.35s, import 25.14s, tests 45.38s, environment 12ms)', '✓ built in 3.91s']
- `demo_replay`: **PASS**;
- `crash_audit`: **PASS**;
- `publication_head`: **FAIL**; ['SUMMARY scanned=30789 messages=0 violations=97 pending_exception=97 verdict=BLOCKED']
- `docs_ia`: **PASS**;
- `publication_range`: **PASS**; ['SUMMARY scanned=83 messages=4 violations=0 pending_exception=0 verdict=PASS']
- `freeze_verify`: **PASS**; ['Candidate khớp bản đã đóng băng (mã sản phẩm: 115 file, a068b6f6586c1b12…).']

Postgres and external-evidence markers remain explicitly opt-in/excluded by canonical pytest.ini. Earlier interrupted runs and the pre-existing UI glyph failure are retained in regression history; none supply final PASS counts. Canonical full-gate.mjs alone owns FULL_PRODUCT_GATE_PASS; this report does not invent that label.

Publication range passes with no new finding. Whole-HEAD publication reports97 pending exceptions; every reported path/blob matches the baseline. No exception or human approval was changed. See publication_safety_baseline_comparison.json. Product test success must not be read as permission to publish the repository.

## Resource and failure correction

Original precursor measured5/20 concurrent HTTP500. The claim that their precise cause was SQLite lacked exception evidence. A controlled real-SQLite regression demonstrates an event-loop/session-lock mechanism and now passes after offloading the guard; fresh actual HTTP follow-ups before and after each returned10/10. This does **not** prove elimination of the original stochastic failure or production-load reliability. [Correction receipt](resource_measurement_correction.json).

Sealed candidate 70b22cc71: the same benchmark workload returned 20/20 HTTP200 with 0 captured server exceptions ([profile](ocr_worker_resource_profile_final.json)). The precursor run had no exception capture, so this is an observation on the candidate, not a controlled before/after experiment.

Precursor resource/latency files identify4ab43853 explicitly; final patches affect confirmation, comparison and session waiting rather than OCR inference. They are not relabelled as a final-candidate performance run; the sealed candidate has its own `*_final.json` latency, resource and cold-process receipts, and its API acceptance re-run reproduces the prepare and solve statuses of all eight new-corpus images. Original long-form stage timings and cold-process measurements remain separate. A historical idle-RSS delta0MiB is not active OCR memory.

The shared OCR result cache has operation-dependent bounds: normal OCR inserts trim to16 entries, while reread inserts trim to64. The previous statement of a fixed32-entry cache does not match current code. Cache occupancy and descendant RSS are recorded separately.

## Corpus, provenance and contamination

[Manifest](new_image_corpus_manifest.json), [references](ground_truth_provenance.json), [split audit](dataset_split_and_contamination_audit.json). Source: [VMMU dataset](https://huggingface.co/datasets/anvo25/vmmu) declares MIT; upstream exam redistribution rights are not independently established, so image binaries and browser screenshots containing crops remain ignored locally. Reference text is agent transcribed, not OCR output; exact image hashes and retrieval records are in the manifest. No evaluation image drove a recognition heuristic or geometry expansion. Existing12 VMMU cases cannot be independent H1 after parser tuning in the old run.

## Post-flight

Reused modules: existing OCR worker/client, lexer, reconciler, fidelity gate, region detector, parser, Hybrid adapter, continuity checker, browser harness and canonical audits. Created product modules:none. Added focused regression tests and run-scoped measurement tools only. Duplicate check: CODE_INDEX and callers inspected; no parallel solver/OCR implementation. No changed expected answers or deleted tests.
