# Source grounding integration and research closure — LOCAL, 2026-10-13

User-authorized final independent review, ff-only main integration and push, physical cleanup and read-only research audit.
No new feature, live provider request, Hybrid enablement, cache change or history rewrite.

Final review found one previously undeclared Important safety gap, present at main `7767c7e1`, prior review `90ce6497`
and product `b264828f`: overlapping quotes of one length call could spend that value twice. Source `SA = 3 và SB = 3.`
or `SA = 3, đổi AB thành 3.` served SC = √17 when its SA call listed a short quote before the whole sentence.
This corrects the numeric one-use claim of `source-grounding-completeness` §2; that historical report remains untouched.
Product fix `c30049fd` gives each validated call field one numeric budget across all its quotes, in the same authority.
RED 4 failed / 14 passed; GREEN 227 passed / 1 xfailed. Independent follow-up NON-BLOCKING: 415 passed / 1 xfailed,
12 extra route probes, including equal values on distinct validated fields. See [review.md](review.md).

Declared residuals remain open: goal joined to hypothesis by bare và/song; numberless relation inside another call's
long quote; a goal value without a validated value. All reproduce at the baseline; no full Vietnamese coverage claim.
## Integration

Preflight: main = origin/main = ls-remote `7767c7e1`; research tip `0bb3f3ed`, product `b264828f`.
User's only visible dirty state was untracked `frontend/public/`; it is preserved (favicon SHA256 `5cd57f27…`).
Final targeted independent review covered the last two product fixes and all seven requested grounding concerns.
Single authority, proof/negation isolation, causal connectors, valid chained proofs and solid-height controls pass.
The residual table in [review.md](review.md) separates declared safety gaps, conservative refusals and closed grammar limits.

Product fix `c30049fd`; clean refreeze and correction-layer commit `27b81c51`.
Candidate `736613f67d6e3a1a7459b8af4562c5000768989ddb8ef09a1d5b9a14a12706e2`, 110 files, clean source `c30049fd`.
Main ff-only `7767c7e1` → `27b81c51`, no merge commit/rewrite. Candidate verify PASS on integrated clean detached `27b81c51`.
Connected grounding/Hybrid/Geometry Functions/provider/docs/identity gate: 1224 passed / 5 xfailed.
Benchmark 30 cases: both evaluations 19/9/0/2; metrics SHA256 `febb5b602fcb194c502e07ea47fe4200ed4083f0b09bac12784b2536940ab12e`,
byte-identical to the preceding run. Provider A `912b22ef`, B `4a20601f`, declarations `f2ec9698`; no surface change.
LLM_ONLY, cache125, Hybrid not connected to `/api/analyze`, 0 live calls. Hybrid product enablement: **NO-GO**.
No new Playwright run: source-gate changes only, no renderer/scene-building logic or served geometry payload change.

T3 must be measured anew after this product fix; the old 9143-pass receipt is not reused.
Initial attempts were stopped and receive no PASS credit: one started before the verifier checkout completed;
others replaced the session Git configuration with a longpaths-only configuration, causing dubious-ownership failures.
Exact reproduction: `test_analyze_failure_cluster_diagnosis::test_tien_kiem_kho` 1 failed / 98 passed.
Appending longpaths to the existing session configuration closes that environment failure (same test 1 passed).
The authoritative final attempt runs the full gate serially in clean detached `27b81c51`, preserves session Git settings,
uses an isolated task TEMP and disables live AI. Final completed receipt/status is in `run.json`.
**FULL_PRODUCT_GATE_PASS**, exit 0: backend 9161 passed / 1 skipped / 2 deselected / 6 xfailed; frontend 1053 (68 files),
typecheck/build PASS, demo 5/5, crash boundary 6/6. Receipt `verification/t3.log`, SHA256
`76a0e91659c7cd5237d2d743523ac6344d84868129dae3ff65d4f17c1cd9f17a`.
Living docs/identity/correction gates after documentation updates: 97 passed (`verification/docs-final.log`).

Push `7767c7e1..6e053b41` succeeded after a fresh fetch and fast-forward ancestry check. Main, origin/main and
ls-remote all matched `6e053b41962444f0dbbe2f6ef73e775ef63d3442`: **REMOTE_SYNC_PASS**. Only afterwards was
`research/source-grounding-completeness` deleted with `git branch -d` (tip `27b81c51`, contained in remote main,
no executable consumer). The documentation-only commit closing this record follows that verified push; its identity
is **SELF**, and its final remote SHA is checked from Git after commit/push, without a self-referential commit hash.

## Physical cleanup

Before: two registered worktrees (root, DSL); three physical directories (DSL, question-local-givens, geometry-library-expansion).
Both old leftovers had no `.git`, registration, branch or active code/tool consumer. Process inventory found no process
using them (the read-only inventory command itself was excluded); no old service/browser was stopped.

| Target | Before | Result / preservation |
|---|---:|---|
| question-local-givens | 13234 files, 1687454380 bytes | Removed with native `Remove-Item -LiteralPath ... -Recurse`, no force. 13126 source/evidence files matched main or recoverable `5fe14001`; remaining generated caches and SQLite test DB (all ten tables empty) had no unique user/research data |
| geometry-library-expansion | 26 files, 426067 bytes | Removed with the same legal operation. All 21 research files exactly matched main; remaining five pytest cache files were scratch. No unfinished source change |
| `.superpowers/worktrees/hybrid-ab-handoff-final.xml` | absent | User-supplied location corrected by physical inventory |
| `.superpowers/hybrid-ab-handoff-final.xml` | 20425 bytes | Deleted: JUnit of 2026-10-10, 153 tests, 0 failures/errors/skips; no active consumer or unique research finding. Not a handoff. Summary preserved here; exact untracked XML byte recovery NOT_RECOVERABLE |
| dsl-spike | registered, clean, 1683016400 bytes | Kept: active HOLD research, committed prototype/tests/evidence |

Old contents removed: **1687900872 bytes** including XML (1687880447 bytes for the two directories).
This is the sum of measured file contents that no longer exist, excluding junction targets. Physical allocation/free-volume
delta is **UNKNOWN**: a volume-free snapshot immediately before deletion was not recorded, and tests allocate concurrently.
Full inventory and per-file preservation receipts: [inventory.json](inventory.json), [preservation.json](preservation.json).
No permission blocker remained on either authorised old worktree target. Owner names were not used as proof of permission;
the legal deletion operations succeeded. No force, ACL/owner modification, `git clean`, or policy bypass.

Kept as requested: old `.superpowers/scratch/`, builds/agent drafts, root `backend/algosim.db`, untracked `frontend/public/`,
all historical candidates/correction layers and locked A/B evidence. Ten old scratch directories remain access-denied;
their full sizes/contents are UNKNOWN (readable subtotal 2912680 bytes, not a total). No deletion/ACL retry on them.
The preexisting `backend/.tmp/pytest-05045731f8a046b9ba317bc970ecca11` remains (readable empty subdirectories); the
root `backend/.pytest_cache/` still warns permission denied. These preexisting warnings are separate from this task's temps.
Current-task verifier, node_modules junction and scratch are removed after receipts are preserved; final counts in `run.json`.
The main `frontend/node_modules` junction target is preserved.
Final physical worktree list: **dsl-spike only**; registrations return to **two** (main + DSL). The verifier's Git removal
deregistered it but left files (`Invalid argument`); native legal deletion completed the physical cleanup.
Current-task contents removed: **1770132178 bytes** (junction target excluded); observed D: free-volume increase during
that cleanup was **1826193408 bytes**, an observation rather than exclusively attributable allocation accounting.
Task test Git objects had ReadOnly flags and their `.git` directories Hidden flags; only these generated file attributes
were cleared (226 blobs / 10 hidden directories). ACLs/owners unchanged; no forced deletion.
No task Python/node/browser process remained at final process inventory.

## Research closure

**Compact DSL: HOLD_WITH_NEXT_EXPERIMENT.** `research/compact-geometry-dsl` @ `a9498fdf`, two unique commits;
worktree clean. Prototype semantically round-trips 205 facts / 35 cases and preserves plan/route outcomes; malformed
inputs fail closed. Fresh read-only verification 95 passed. Ratios 0.44 / 0.50 are tiktoken proxy measurements only.
No Gemini tokenizer, extraction accuracy, malformed/repair rate, total billing or constrained-output loss is measured.
Planner needs existing Typed Facts, not DSL. Minimum decision-changing experiment, only with separate user budget approval:
paired JSON/DSL extraction on a frozen representative corpus, fixed model/settings and one-repair maximum, predeclared
stop rules; compare exact outcomes, errors and total Gemini `usageMetadata` cost including repairs. Until those thresholds
are met, keep HOLD; do not merge/remove the branch or make DSL a Hybrid dependency. No experiment was started here.

**Real-model readiness / pilot:** `4cfa547f` readiness is contained in pilot `471a2c79`; neither is in main.
Readiness is on its remote; pilot remote is `24a9a557`, exactly one commit behind local. `471a2c79` is on no remote ref.
That commit adds 44 unique files containing live evidence and review diagnostics, and current-main has none of the pilot package/tooling.
Consumers are the research report/handoff, live manifest, replay/certification/scorer and tests on the pilot branch;
no production consumer. The one 16-case development pilot completed, **not** a successful product E2E: 0/10 positive
served correctly, 1/6 negative refused correctly, no case served, 9 analyze schema exceptions; timeout cost UNKNOWN.
P1–P3/F1–F6 remain research findings, not presumed fixed by Source Grounding. No rerun/rescoring/merge/push here.
Readiness may retire only after pilot evidence is durably preserved and its report references remain recoverable.
Pilot may retire only after separate review disposition and durable backup/remote preservation under separate authorisation.

Both DSL and pilot now have small verified incremental **local** bundles in `.superpowers/preserved/` (kept; not scratch):
- `compact-geometry-dsl-a9498fdf.bundle`, 31472 bytes, SHA256 `cb97d1320fe6279844d03b6ede01320e13dd81ab965d2b87484d1474de8309a1`, prerequisite `9cfd0fca` on origin/main.
- `real-model-pilot-471a2c79.bundle`, 43140 bytes, SHA256 `11eb7ba52fc846e20bb086e5fa6676dc50f58cb3c3ccafa6f1831aa117f95812`, prerequisite `24a9a557` on the pilot remote.
`git bundle verify` PASS. These add local recovery, not independent/off-machine or remote preservation.
Recover after prerequisites exist with `git fetch <bundle-path> <refs/heads/branch-name>`; no need to run live tools.

| Công việc | Trạng thái | Việc còn thiếu | Quyết định |
|---|---|---|---|
| Source Grounding | Product repair complete; main integrated/pushed, fresh T3 PASS; branch retired | Declared safety residuals still OPEN | Keep Hybrid off; historical correction preserved |
| Question-Local Givens | Product/Git integration complete; physical cleanup complete | Broader grounding limits tracked separately | Old worktree retired; evidence retained on main/remote |
| Geometry Library Expansion | Approved code already integrated (ancestor of main); physical cleanup complete | Human visual / live quality limits remain separate | Retire leftover directory, no new integration |
| Compact DSL | HOLD_WITH_NEXT_EXPERIMENT | Real model comparison could change HOLD | Keep research branch/worktree + local bundle |
| Real-model readiness | Survey complete, contained in pilot, remote preserved | Pilot disposition/preservation prerequisite | Keep branch; no main merge |
| Real-model pilot tooling | Tooling + one live measurement complete, quality unsuccessful | Unpushed 471a2c79, findings review, durable off-machine preservation | Keep branch + verified local bundle; separate decision |

## Next action

Only proposal: user approval of a bounded next goal-directed Planner slice on the existing architecture, as ROADMAP §0
prioritises. It has not been started; DSL, live pilot, Hybrid enablement and a new vertical slice remain outside this task.
