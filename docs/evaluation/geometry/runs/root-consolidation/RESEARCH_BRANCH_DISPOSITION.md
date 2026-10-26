# Research branch disposition

All five refs are intentionally retained. No old divergent branch is merged or pushed. The incremental recovery bundle
`.superpowers/backups/root-consolidation-20261027/retained-research.bundle` passed `git bundle verify`; its prerequisites are ancestors available on main.
`git bundle list-heads` confirms the five exact tips, including full `471a2c79`. To recover, use a clone with the main
history and fetch the selected branch from the bundle. It is not a standalone replacement for the whole repository.

Changed files were distinguished from the fork-point product, and their live-pilot/credential risk was examined before
the no-push decision. A bounded scan of branch-delta files found zero Google/GitHub/private-key credential patterns;
that does not certify arbitrary secrets absent. Existing raw live response artifacts on the pilot ref are a separate
reason to avoid publication. No raw model content or secret is copied into this new report. Detailed fork diffs and
main-reference inventories remain local in `research-audit.json`.

## `research/hybrid-semantic-extraction-v2`

HEAD `dc27009fe9530ced01c3e6d52898d789a62cb36f`; 14 unique commits; fork `8427c87989487fdbcbb547ec16039d439528eb51`; 0 paths absent from main; 97 main documentation references.

**Decision:** Keep local research ref and bundle. Do not integrate prompt v2.

Owner disposition explicitly says NO-GO for prompt v2 and the 48 held-out requests. Safe source-grounding/scorer work already reached main as e4fff851, aa0da02b and 0507cb01 (main extraction-v2-integration-record/report.md). The 14 divergent commits still preserve the original pilot, scorer/grounding variants and sealed protocol. Its files exist on main, but some bytes and prompt differ. A future extraction study must start from current main and current typed-fact-next/2; the old paired pilot served 0/12 in both arms and is not evidence for replacing the extractor.

Unique commits:

- `dc27009fe9530ced01c3e6d52898d789a62cb36f fix(docs): restore 43 EVIDENCE_INDEX entries an unscoped substitution overwrote`
- `d0cf43f253cde52586515bea56c9a85809928efb docs(extraction-v2): record the owner disposition and seal the unrun held-out`
- `0303c3ebf9c2a47b76106dad01e635a83d3fcad3 eval(extraction-v2): record the owner-approved paired dev pilot`
- `7ee8cc1476f663996580f77811df954861528cab eval(extraction-v2): record T3 on the branch merged with main`
- `b7b7e89e68a470da150257f7911b06ebc6ac8bc4 eval(extraction-v2): refreeze the candidate on the merged branch`
- `1893d7d134587cee92a2ad0c81b71e827228d78f merge: bring main 8427c879 (Scene3D educational finalization) into the extraction-v2 branch`
- `f12a33ccb96b1becdce70b2baa155e48c23d5bf0 eval(extraction-v2): record the final authoritative T3 on a clean detached worktree`
- `fa6d792ef177ca0f0e266c72ab2d2d2d2145a01e docs(extraction-v2): report the offline evidence, live approval request and handoff`
- `c640cd14be4533c3d8970266dacab491ea4e601b eval(extraction-v2): load backend/.env on the live path like the frozen evaluator`
- `108fc0868cedfe624981b6dcde7014a0b2de5f47 eval(extraction-v2): refreeze the candidate at the reviewed product commit`
- `69fa9be808c2ef6ee8eb9742f441435ac38e695f fix(extraction): apply the whole-change review and close an oblique-box serve`
- `920527b150c33ae682c015fb8dcd4626a9e291c4 eval(extraction-v2): refreeze the candidate after the extraction contract change`
- `fb3f4ee503514af1327dd358243461112f95a864 feat(extraction): clarify the typed-fact contract and recognise two source wordings`
- `6ceb25080cb87613640a7e0dab9becc5f4961447 eval(extraction-v2): lock corpus, oracle, scorer and preregistration before prompt changes`

## `feat/real-model-pilot-tooling`

HEAD `471a2c796b44bf9bf8fc14ca02a5a365b440c2a7`; 4 unique commits; fork `28ac1d61cbaa6b33085bb12392e5f0f5815eb787`; 69 paths absent from main; 47 main documentation references.

**Decision:** Keep local research ref, especially 471a2c79; do not push it.

Four scripts and the exact scorer, ten outcome classes, fake-provider certification, offline replay and 55 historical tests are potentially reusable. The runner pins cache 125 and candidate 93077b51, uses old product mot_luot/run_pipeline contracts, and a token reserve that was not a hard output cap. Current cache130/V2 contracts require selective adaptation, a new protocol and offline recertification. Commit 471a2c79 contains the completed historical live run, including raw model artifacts: 0/10 correct served, 1/6 correct refusals, 0 wrong served, 33 logical/47 HTTP attempts, 224023 recorded tokens, USD 0.364 plus UNKNOWN for 16 timeout attempts. Those historical figures are not current extraction quality. No pilot was rerun.

Unique commits:

- `471a2c796b44bf9bf8fc14ca02a5a365b440c2a7 eval(g05-real-model-pilot): record PHASE B independent verification and the single live gemini-2.5-flash run`
- `24a9a5577a604df6568d18e348d62feea27a7ed9 docs(g05-real-model-pilot): record the full backend suite on a clean tree and identity verification for PHASE A`
- `f694d086349bc70847cf71ee615dc6c4131ccbb5 feat(eval): G05 real-model pilot tooling â€” exact scorer, run_pipeline runner, refusal classes, offline Scene3D replay, key safety (0 model calls)`
- `4cfa547f0989e53b917cc020adf59e250acbf68d docs(real-model-e2e-readiness): survey existing live harnesses, tooling gaps and a 16-problem G05 pilot proposal (0 model calls)`

## `research/nl-to-scene3d-e2e-readiness`

HEAD `25f57e31604c5a12ca30667276b17596dcceb71b`; 1 unique commits; fork `43247c9e9375a3dbf2b5223324a58e6f932ca596`; 92 paths absent from main; 24 main documentation references.

**Decision:** Keep local evidence ref and bundle; no merge.

Unique authored corpora, symbolic/coordinate oracle, browser receipts and readiness research remain referenced by main. Product has moved from its earlier typed-fact-next/1 baseline to /2. Authored gold/replay ceilings and exposure-labelled holdout work cannot serve as fresh independent live extraction evidence. Future work may adapt harness ideas, with a newly registered independent corpus.

Unique commits:

- `25f57e31604c5a12ca30667276b17596dcceb71b eval(geometry): complete NL-to-Scene3D E2E research readiness campaign (nl-to-scene3d-e2e-readiness)`

## `research/hybrid-next-architecture-gap-audit`

HEAD `4f1d1a4886ae47c452fb533f21faa883918d175d`; 1 unique commits; fork `f8423d4b87f942d3d850970c741bcf4ee6d2c634`; 8 paths absent from main; 7 main documentation references.

**Decision:** Keep local research evidence ref and bundle; no merge.

One docs/research commit contains four offline POCs and gap matrices on cache126, planner/7 and engine/5. Current main has Adapter /3 and /4, exact certificates, dependency planning and V2 contracts, so the old POCs must not replace product modules. The evidence and original diagnosis remain referenced and useful for research provenance.

Unique commits:

- `4f1d1a4886ae47c452fb533f21faa883918d175d docs(research): add hybrid next-generation architecture gap audit and offline POCs`

## `research/compact-geometry-dsl`

HEAD `3db08a1e3c8a47a7284b7dbdfaac112640106593`; 8 unique commits; fork `c63efdb5515d89867d2cb7bf3136f97caf53fbac`; 16 paths absent from main; 57 main documentation references.

**Decision:** Keep local NO-GO evidence ref and bundle; do not ship DSL.

Eight divergent commits contain seven unique prototype/harness/test files and format-evaluation evidence. The final verdict is NO-GO for compact DSL and compact JSON as the AI wire format. Token proxies were not provider billing or extraction-quality evidence; held-out-driven fixes are disclosed. The historical fail-closed/truncation lessons remain useful, but the prototype is not compatible evidence for replacing current V2 typed extraction.

Unique commits:

- `3db08a1e3c8a47a7284b7dbdfaac112640106593 docs(eval): record the compact DSL format evaluation (NO-GO, 0 model calls)`
- `6c07dd3a4fb0ffa531bc89d477336cdeae8860fd fix(dsl): close independent review findings on the format harness`
- `152c91a3babddee591db666c00d76194206059d9 eval(dsl): measure the three formats offline and model the request cost`
- `0e614452bca585cac995250ec8a8ecaae48c3456 fix(dsl): carry plane_relation and fail closed on cut or dropped text (GREEN)`
- `72f21a243fa80d5737e39e1f738c61fd6d96be61 test(dsl): freeze a held-out corpus and a three-format harness (RED)`
- `dee744e6a6b6c61fb99a7a6d21cb6e65b91fdc71 merge: bring main c63efdb5 into the compact DSL research branch`
- `a9498fdfa55386b447e11c41ab2a584ed4179125 docs(dsl): record the compact geometry DSL spike (verdict HOLD, proxy tokens only, 0 model calls)`
- `45551c0f63136f715753039f641763df6977f1e6 feat(dsl): add a research prototype of a compact text form of the Hybrid Typed Facts`
