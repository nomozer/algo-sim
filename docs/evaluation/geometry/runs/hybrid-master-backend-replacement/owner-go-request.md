# Consolidated Owner GO request — live paired measurement for Hybrid production cutover

**What it unblocks:** this is the only decision blocking D-04, D-11, D-13 and GATE-16.

**Defaults without a GO:** `MAX_AUTHORIZED_LIVE_REQUESTS = 0` and `MAX_AUTHORIZED_LIVE_SPEND_USD = 0`. No live call has been made.

**Scope:** approving this does not switch production. Cutover is decided by the pre-registered criteria in item 10, applied to the results.

**Provider facts** below were checked against official Google documentation on 2026-10-31 (`provider-facts.md`).

**Update, ninth continuation (2026-11-01). It supersedes the eighth-continuation measured system below.**
- **Measured system:** candidate `17e4a326` (product `fa1ed277`; 118 files, `9583018d…`). `--manifest` prints the exact `measured_system` and `harness_sha256` to bind.
- **Model surface:** the `/4` arm's provider response schema widened with additive `typed-fact-next/2` fields (`SolidSpec.inscribed_in` and `GeometricRelationSpecV2` kinds `circumscribes`, `inscribed_in`, `tangent_to` + optional `contact_ref`). `typed-fact-next/1`, the `LLM_ONLY` arm, and `CACHE_VERSION` 131 are unchanged.
- **Newly served and certified on Hybrid `/4`** (independent review `READY` after 3 rounds; Registry `/26`, Planner `/22`, Engine `/18`, `geometric-relation-certificate/1`):
  - certified spheres inscribed in convex polyhedra across **all** boundary faces (`NO_INSCRIBED_SPHERE`, strict inward half-spaces, strict `relint` face polygon contacts, and independent $9V^2 = r^2 (\sum_k S_k)^2$ cross-check);
  - certified sphere–plane tangency (`tangent_to`, $d^2 = R^2$ vs. `PLANE_INTERSECTS_SPHERE_NOT_TANGENT` / `PLANE_DOES_NOT_TOUCH_SPHERE`, non-collinear witness triple, optional named contact point usable in downstream metric goals);
  - composite topologies: multi-polyhedron `shared_faces` + sphere, dual circumscribed + inscribed spheres (named `(S1)`/`(S2)` or unnamed `"()"`), polyhedron plane section + sphere coexistence, axial cylinder/cone hosts (`O.O'`, `(T)`, `S.O`, `(N)`) + circumscribed/inscribed/dual spheres (`NO_INSCRIBED_SPHERE` when cylinder $h \ne 2R$), explicit planner dependency DAG + `composition_classification`, and 4-layer `relation_certificates`.
- **Still refused on Hybrid `/4`:**
  - non-cospheric polyhedra (`NO_CIRCUMSCRIBED_SPHERE`), non-tangential polyhedra or cylinders (`NO_INSCRIBED_SPHERE`), and irrational Cholesky charts (`METRIC_REQUIRES_EUCLIDEAN_CHART`);
  - polyhedron–cylinder/cone inscription, sphere–line / sphere–sphere tangency, standalone frustum, Oxyz coordinate/equation input, ellipse sections, coordinated question lists (`P-1`), several sections in one run (`P-2`), and unordered ratio questions.
- **Same three optional grammar rulings (`P-1`, `P-2`, `P-3`)** as in the seventh continuation below remain open.

**Update, eighth continuation (2026-10-31). It supersedes the seventh-continuation measured system below.**
- **Measured system:** candidate `db1ac63a` (product `44a0b79e`; 118 files, `ccfce08c…`). `--manifest` prints the exact `measured_system` and `harness_sha256` to bind.
- **Model surface:** the `/4` arm's provider response schema widened with the additive `typed-fact-next/2` field `SolidSpec.circumscribes` (a sphere circumscribing a declared polyhedron). The `LLM_ONLY` arm is unchanged, and so is `CACHE_VERSION` 131.
- **Newly served and hardened on Hybrid `/4`** (independent review `READY` after 2 rounds; Registry `/25`, Planner `/21`, Engine `/17`):
  - polyhedral role-phrase parity without `"của"` (`"chiều cao hình chóp"`, `"cạnh bên hình lăng trụ"`, etc.) with full prism-subclass invariant verification;
  - machine-verified `preconditions` and `postconditions` exported on `KetQuaTuyen.trace` and `route_d.construction_trace` (stripped of post-execution kernel claims on all `REFUSED` paths, axisless standalone sphere pose);
  - certified circumscribed spheres of polyhedra (`"mặt cầu / khối cầu ngoại tiếp"`), solved via exact `Fraction` $3 \times 3$ Gram circumcenter + all-vertex cosphericity certificate (`NO_CIRCUMSCRIBED_SPHERE`) + exact `Fraction` Cholesky Euclidean chart normalization (`chuan_hoa_euclid`) + G4 IR perpendicular-bisector construction + independent closed-form cross-check, plus composite polyhedron/sphere `ask_volume` disambiguation.
- **Still refused on Hybrid `/4`:**
  - inscribed spheres, tangent spheres, and circumcircles;
  - non-cospheric polyhedra (`NO_CIRCUMSCRIBED_SPHERE`) and irrational Cholesky charts (`METRIC_REQUIRES_EUCLIDEAN_CHART`);
  - coordinated question lists (P-1), several sections in one run (P-2), a ratio question without its order, a plane given by an equation, and ellipse sections.
- **Same three optional grammar rulings (`P-1`, `P-2`, `P-3`)** as in the seventh continuation below remain open.

**Update, seventh continuation (2026-10-31). It supersedes the sixth-continuation measured system below.**
- **Measured system:** candidate `cb06635e` (product `d9d11b60`; 118 files, `4c269bab…`). `--manifest` prints the exact `measured_system` and `harness_sha256` to bind.
- **Model surface:** the /4 arm's provider response schema widened. It gains the additive `typed-fact-next/2` plane kinds `at_distance_from_center` / `through_center` and the field `distance_from_center`. The LLM_ONLY arm is unchanged, and so is `CACHE_VERSION` 131.
- **Newly served on Hybrid** (independent review READY after 3 rounds):
  - the base-centre wordings;
  - the general apex ratio k;
  - sphere sections at a distance from the centre or through it.
- **Still refused on Hybrid:**
  - coordinated question lists;
  - several sections in one run;
  - a ratio question without its order;
  - a plane given by an equation;
  - ellipse sections.
- **Three grammar rulings are needed** (each is optional; until it is given, the locked policy stays):
  - **P-1:** should "Tính thể tích, diện tích xung quanh hình nón, …" bind one object across several measures? This would SERVE registered REFUSED controls, which needs your repin.
  - **P-2:** with several sections in one run, may a section question bind by kind ("qua trục" ⇒ axial, plane name ⇒ parallel)? This also needs a repin.
  - **P-3:** is "cắt trục SO theo tỉ lệ k tính từ đỉnh S" the whole-axis ratio SM/SO in the target curriculum? "theo tỉ số k" is refused as ambiguous.
- **Adapter /3 finding** (evidence only; Adapter /3 is not changed): it served the axial-section area for the quote "diện tích thiết diện tròn", and it answered a bare "Tính bán kính." when several circles exist (`registered-curved-controls-audit.md`).

**Update, sixth continuation (2026-10-31). It supersedes the fifth-continuation measured system below.**
- **Measured system:** candidate `7a870059` (118 files, `277338ce…`).
- **Newly served on Hybrid:** curved sections parallel to the base, axial sections, the cone volume ratio and the remaining volume. Each passed an independent review (READY after 3 rounds).
- **Still refused on Hybrid:**
  - sphere sections;
  - a ratio from the apex other than the midpoint;
  - a ratio question that does not state its order. Adapter /3 guesses that order; /4 refuses it.
  - the wordings "tâm đáy O" and "tâm đáy dưới/trên".

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

## Addendum — tenth continuation (student language), 2026-11-01

Nothing above is changed: the locked protocol, scorer, thresholds and 60-case corpus stay as registered. The measured
system changes (registry /27, engine /19, `/4` extraction surface gains the `unresolved` exit), so `--manifest` prints a
new `measured_system`; an approval written for an earlier candidate does not bind this one. Evidence:
`student-language-audit.md`.

Three decisions only the Owner can take, in one place:

| # | decision | why it is not taken here | options |
|---|---|---|---|
| S-1 | **Diacritic-free input.** `detect_domain` refuses "cho hinh chop S.ABCD …" as out of scope on every route, including the `LLM_ONLY` default. | Changing it changes default-route behaviour (more text reaches a paid model) and the domain policy; a Hybrid-only fix would be dead code behind that gate. | (a) keep, and tell learners to type with diacritics; (b) authorize one slice: a length-preserving restoration copy for the domain gate and the Source Gate, raw quotes kept, ambiguous folds refused or clarified, with its own independent review |
| S-2 | **A live student-wording study**, separate from the locked paired protocol: does a live model use the honest exit correctly, and how often does it over-use it? | Needs provider budget and authored student-style texts; gold replay cannot answer it. | GO with a budget and an author, or defer |
| S-3 | **The corpus author** of the locked 60-case set should know that diacritic-free and simulation-only wording now behave differently on the two arms (Hybrid reads simulation requests; both arms refuse no-diacritic text). | Authoring choices are the author's. | inform the author; no protocol change |

## Addendum — eleventh continuation (semantic correctness, generalized planner recomposition & S-1/S-2 readiness), 2026-11-01

The locked 60-case live paired protocol (`live-evaluation-protocol.md`), thresholds, and `ALLOW_LIVE_AI=0` default stay unchanged (`0` live calls, `USD 0` spend). Product commit is now `9e059eb7` (Registry `/28`, Planner `/23`, Engine `/20`; independent adversarial review `READY` in Round 4, `0 BLOCKER, 0 MAJOR, 0 MINOR`; `continuation11-adversarial-review.md`):

- **PE-2 closed (`ISSUE-ARCH-ROUTE-D-SOLID-CLASS-WORD-UNCERTIFIED`):** premise-level solid-class and 2D polygon assertions (`cube`, `cuboid`, `right_parallelepiped`, `parallelepiped`, `regular_prism`, `right_prism`, `oblique_prism`, `regular_pyramid`, `regular_tetrahedron`, `square`, `rhombus`, `rectangle`, `parallelogram`, `trapezoid`, `isosceles_trapezoid`, `right_trapezoid`, `regular_hexagon`, triangle classes) are certified in exact `Fraction` Gram arithmetic (`INCONSISTENT_FACTS` / `AMBIGUOUS_REFERENCE`), and operand-less imperative requests (`"Vẽ hình rồi tính."`, `"Tìm."`, `"Xác định."`) refuse fail-closed (`SOURCE_GOAL_UNANSWERED`).
- **Generalized planner recomposition (`planner-recomposition-audit.md`, `planner-recomposition-matrix.json`):** `Point` descriptor `PlanningContract`s cover all 6 general point constructors (`midpoint`, `centroid`, `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`) with zero change to locked `TypedFact` / `flat` / `v3` / Route A schema SHAs, connected to auxiliary planes (`MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`), 2D `carrier_planes` perpendicular anchors (`_chon_moc_vuong_duong`), Gram postcondition self-checks (`_MO_TA`), and `search_telemetry` (`9` newly unlocked `DISCOVERED_FUNCTION_COMPOSITION` chains, `24/24` agreement with standalone `backend/scripts/planning_oracle.py`, `0` wrong-served).
- **Offline readiness for `S-1` and `S-2`:**
  - `S-1` (`s1-diacritic-free-offline-audit.md`): isolated prototype `backend/scripts/s1_diacritic_offline.py` (`0` imports in `backend/app/`, `detect_domain` untouched) preserves 1-to-1 `norm_char_to_raw_span`, mixed-IME `_ascii_fold`, `verify_no_forged_quotes`, and `NEEDS_CLARIFICATION` polysemy flags (`16/16` dev corpus). Production policy remains Owner decision `S-1` above.
  - `S-2` (`s2-student-language-pilot-protocol.md`): offline deterministic 8-metric scorer `backend/scripts/score_s2_student_language_pilot.py` (`ALLOW_LIVE_AI=0`, `NOT_MEASURED`/`NOT_RECOVERABLE` preserved) is ready if the Owner authorizes the 6 live parameters (`Execution Authorization`, `Model ID`, `Project/Key`, `Hard Request Cap <= 36`, `Hard USD Cap`, `Data Scope`).
