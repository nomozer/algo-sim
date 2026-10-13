# Source grounding completeness — LOCAL Windows, 2026-10-13

Branch `research/source-grounding-completeness` from `main` = `origin/main` = `7767c7e1`. No merge, no push.
Hybrid stays a research route: `LLM_ONLY` default, `CACHE_VERSION` 125, IR schema, provider surfaces and renderer
unchanged; 0 live calls.

## 1. Root cause

`registry._kiem_du_kien_cau_hoi` (the one coverage authority shared by routes A and B) read the problem only from the
first request on. A premise sentence before it was never read unless some call quoted it, so

- "Cho hình chóp S.ABCD … SA = 3. **Đổi SA thành 5.** Tính SC." served SC = √17 from the old figure;
- likewise "Đổi đáy thành hình vuông cạnh 4.", "SB vuông góc với (ABCD).", "Giả sử SA = 5.", "Nhân đôi mọi kích thước.";
- on both routes, for asks, construction-only requests, auxiliary decompositions and derived-plane sections.

A long quote could also carry a change ("SA = 3 và SB = 7" quoted by the SA call), and a route-B goal fact could make a
hypothesis in its sentence look read.

## 2. Bounded obligation (one authority, no parser, no second state)

`_kiem_vung_tien_de`, called inside `_kiem_du_kien_cau_hoi` on the text before the first request, one obligation per
sentence / ";" clause. Outside sentence-local quotes of validated calls, only these may remain:

| Allowed residue | Closed by |
|---|---|
| connectors and lead-ins ("cho", "có", "và", "biết", units) | `_NOI_TIEN_DE` |
| exam scaffolding ("Bài 3.", "Câu a:", "a)", "1)", "(1 điểm)") | `_GIAN_DAN` |
| a note made only of note words; a number only as "N chữ số" | `_GHI_CHU` |
| names of objects the calls use; a role noun only when a call gives that role (line ⊥ base, altitude, apex projection, lateral edge of a right prism, apex → centre of a regular pyramid, base / lateral face / edge of the solid) | `_TEN_DOI_TUONG`, `_vai_tro_doi_tuong_khop`, `_tam_day` |
| a goal clause and goals chained to it ("rồi suy ra", ", từ đó suy ra", "Hãy chứng minh"), up to the gate's own given / condition / next-task / causal / contrast markers; a length it states must match a validated value | `_mo_muc_tieu`, `_ket_muc_tieu`, `_KET_MUC_TIEU`, `_NOI_MUC_TIEU` |

Every number must sit inside the quote of a call carrying that value, and each value backs one occurrence. A quote
spanning sentences covers only what its call's binding grammar reads there. Route B passes goal / negated quotes as
`read_quotes`. They count only where the gate itself reads a goal or a negation, from the goal opener on, so a "prove"
label on a premise reads nothing. Anything else ⇒ `SOURCE_PREMISE_UNREAD` (class `grounding`); a goal length
contradicting a validated value ⇒ `INCONSISTENT_FACTS`.

## 3. Evidence

`backend/tests/geometry/test_premise_source_coverage.py`, real routes A and B, no provider: **209 passed, 1 xfailed**.

| Check | Result |
|---|---|
| RED at `7767c7e1` | final file: **130 failed / 79 passed / 1 xfailed** (the 79 are positive controls); first version 30 failed / 12 passed |
| RED → GREEN per review round | 34 (`c56ccc67`), 34 (`90ce6497`), 25 (`f8ac9f4b`), 13 (`b264828f`) |
| changed hypotheses refused | asks, construction-only, auxiliary, derived-plane; premise / note / goal / long-quote variants |
| positive controls served | canonical problems; notes and rounding; exam layouts; verified role nouns; chained proofs; heights of right prisms and regular pyramids |
| metamorphic | relabelling (S.ABCD → T.EFGK) keeps both verdicts; the same expected verdict on routes A and B for every case run on both |
| fault injection | each rule is pinned by a test with a distinct reason (e.g. the oblique-prism height must fail at the premise gate, not at the engine) |

Adapted tests keep their intent; no historical label was edited:
- fixture premises that were intentionally left unextracted are now refused;
- the planner's label choice is asserted on the planner;
- unread second clauses moved into explicit refusal tests;
- `NEG2` is refused one layer earlier, as a documented override.

Benchmark (30 cases, method and labels unchanged): `metrics.json` sha256 `febb5b60…`, byte-identical, 19/9/0/2 on both
arms. Provider surfaces pinned: A `912b22ef`, declarations `f2ec9698`, B `4a20601f` (`test_provider_surfaces_are_pinned`).

## 4. Reviews

Four fresh-context LOCAL reviews (details in [`review.md`](review.md)):
- interrupted (partial probes acted on);
- BLOCKING (I1–I5);
- BLOCKING (verification);
- NON-BLOCKING. Its two Important false refusals and the cheap Minors were fixed RED → GREEN.

## 5. Declared limits (bounded, not a claim of full Vietnamese coverage)

Measured on a closed grammar only. The gate fails closed outside it; it does not understand arbitrary Vietnamese.

- Not detected: a shape / scale claim with no number hidden inside a long quote of another call; a hypothesis joined to a
  goal by bare "và" (xfail) or by "song"; a goal asserting a length of an object with no validated value ("Suy ra SB = 7.").
- Conservative refusals: open wording; "bằng cách …" after a goal; "Cạnh bên SA là đường cao."; "(a) …" / "a. …" layouts;
  "Câu 2 (1 điểm)."; a leading rhetorical "?" sentence opens the request region; true-but-unread second clauses.
- "đỉnh A" accepts any vertex of the solid (no figure change: the solid name fixes the apex).

## 6. Identity and verification

| Item | Value |
|---|---|
| Product commits | `ea18d62f`, `996f9bc8`, `c56ccc67`, `90ce6497`, `f8ac9f4b`, `b264828f` |
| Candidate | `46ca75a2…` (110 files), frozen in a clean detached worktree at `b264828f`, commit `046ab48a`; `d84cd373…` (`63ec673f`) superseded before any measurement. Divergence layer [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json) corrects the `goal-directed-section-planning-main-integration` layer |
| T3 | `FULL_PRODUCT_GATE_PASS` in a clean detached worktree at `046ab48a`: backend 9143 passed, 1 skipped, 6 xfailed; frontend 1053 (68 files); build PASS; demo 5/5; crash surface 6/6. Receipt [`verification/t3.log`](verification/t3.log), SHA256 `e4813748ed1b5c99223685a9e3f4aa92ac13ba77ccae3a6e79a2ba5841efafe4`. A first T3 at `63ec673f` was stopped and discarded when `b264828f` was added |
| Docs audit | `test_docs_information_architecture.py` + identity tests green after the docs commit |
| Default / cache / live | `LLM_ONLY`, 125, 0 Gemini calls; Hybrid not wired into `/api/analyze` |

Scene3D browser harness not rerun: gate-only change, served scenes are unchanged (benchmark byte-identical).
