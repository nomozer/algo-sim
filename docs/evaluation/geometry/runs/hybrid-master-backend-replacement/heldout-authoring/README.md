# Held-out authoring package (for an independent author)

**Status:**
- `AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`.
- No author has been named, and the implementer has written **no** case.
- This folder holds instructions and a template only. It must stay free of real cases until the author delivers them.

## Who may author

A person who did not build or tune the system: the Owner, or a teacher the Owner nominates.
- **Must not:** be the implementer or an AI agent of this repository.
- **Must not:** look at system outputs for any draft case before the corpus is frozen.
- **Must:** be named in the Owner GO.

## What to write: 60 problems

**45 expected-serve:**
- Natural Vietnamese grade 11–12 solid-geometry problems.
- Each asks for exact quantities of kind `distance` (lengths count as distances), `angle_cos_sq` (the cosine squared of an angle), `volume`, `area`, `lateral_area` or `radius`.
- Spread over pyramids, prisms, cuboids and cubes, and over section, distance, angle and volume questions. Give at least 3 per stratum, or the stratum is reported as `INSUFFICIENT_N`.

**15 expected-refuse:**
- 3 out of domain (not solid geometry);
- 3 curved solids;
- 3 with contradictory data;
- 3 with missing data;
- 3 "chứng minh" (prove) requests.

**Exclude:**
- Any text copied or adapted from `docs/evaluation/**`, `backend/tests/**` or the frontend samples; the freeze script scans for this.
- Images.
- Answers needing nested radicals.

## Oracle rules

- Compute every answer **by hand or with a CAS independent of this repository, before any system run.**
- Write the **square** of each exact value, as a rational string (for example `"8/3"` for 2√6/3). For `angle_cos_sq`, write cos² itself.
- If a problem asks for two quantities of the same kind, list both values.
- For expected-refuse cases, list `acceptable_refusal_codes`. The implementer supplies the code vocabulary from `hybrid_preview.classify_refusal` and the LLM_ONLY `error_code` taxonomy. This is a classification aid only and gives no hint of answers.
- Note the premise sentences that must be read (source-grounded premise classification), so failures can be attributed.

## Format

Use `corpus-template.json`, one object per case. Do not include a `dry_run` field: live runs read text only.

## Freeze (before any run)

1. Run `backend/scripts/run_paired_route_evaluation.py --corpus corpus.json --manifest`. It validates the corpus (unique ids and texts, oracle present, kinds known, refusal codes present) and prints `corpus_sha256` with the runtime identity.
2. Put `corpus_sha256` and the author's name in the Owner approval file and in an amendment to `../live-evaluation-protocol.md`.
3. After the first live request, the corpus is immutable. Errata go to an amendment and are reported, never silently fixed.
4. Every case observed in a run becomes development data afterwards. A later blind run needs a new corpus.
