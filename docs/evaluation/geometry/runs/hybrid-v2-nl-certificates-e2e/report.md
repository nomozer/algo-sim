# Hybrid V2 — certificate presentation, NL audit, evaluation harness, line–plane distance

Run `hybrid-v2-nl-certificates-e2e`, 2026-10-27, Claude (Sonnet 5.5). Branch `research/hybrid-v2-nl-certificates-e2e` from
`main` `dd557f8f` (`main` = `origin/main` = `ls-remote`, root clean). No owner authorization beyond the campaign prompt:
**no merge, no push** (`MERGE_READY_PENDING_OWNER_GO`), no live provider, Hybrid stays opt-in, `LLM_ONLY` stays the default.

Evidence class throughout: **authored development cases by the implementing agent** (offline, 0 provider calls). Not a
holdout, not an extraction measurement. `INDEPENDENT_HOLDOUT_NOT_EXECUTED`, `INDEPENDENT_REVIEW_NOT_EXECUTED`.

## 1. Baseline (P0)

`main` `dd557f8f`; engine `/13`, planner `/14`, registry `/13`, `CACHE_VERSION` 130, `DEFAULT_MODE` `LLM_ONLY`, Hybrid
opt-in, previous product `eca4b44b`, previous authoritative T3 candidate `7210a016` (not a certificate of this code). Work in
worktree `.superpowers/worktrees/hybrid-v2-nl-cert`; old dirty/ACL worktrees and backups untouched; no old research branch
merged or pushed.

## 2. D-10 — point–line distance named by the asked line (P1)

Commit `4eae907d`. Owner of the semantic goal = the planner's certificate (`rule: distance(point,line)`, `ask`, `point`,
named `line`); presentation owner = `function_route._dich_khoang_cach_diem_duong` (the module that already presents
certificates: `_gan_nhan_chung_*`). Nothing in the frontend; no label is special-cased.

| Before | After |
|---|---|
| `Tính khoảng cách giữa S và H: d(S, H) = √11.` | `Tính khoảng cách giữa S và BD: d(S, BD) = √11.` |
| `Dựng H: hình chiếu của S lên BD.` | `Dựng H: hình chiếu của S lên BD, nên d(S, BD) = SH.` |

Result object: label, notation, reference, formula text, final event and formation step all name the asked line, in the
order the quote wrote it (`BD` vs `DB`). The value, the foot, the witness and the drawn segment S–H are unchanged. The
renaming happens **only** when the foot object carries a verified `perpendicular_witness` from that very point and the
answer's subjects are `[point, foot]`; otherwise the old wording stays (nothing is inferred). Construction steps never carry
the number, so Mode A shows none and Mode B shows exactly one. Refusals carry no scene.

Checks: renamed labels (`TMNPQ`, `d(T, NQ)`), another point already called H (foot H1, goal still `d(S, BD)`), two goals
on one figure (`d(C, SB)`, `d(S, BD)`), point on the line (served 0), tampered/absent witness keeps the old wording,
6 tests (`test_point_line_distance_presentation.py`), fault injection (presenter removed ⇒ 3 tests red). Oracle: independent closed form of `hybrid_compiler_benchmark`.
Browser (`browser-point-line-asked-line/`): 16/16 rows at 1440 and 390 on the final product code, new check
`goal_named_as_asked` 12/12 (answer row and scene notation both equal the question's `d(P, line)`).

**Does D-10 fix the semantic goal?** Yes for named lines; a point–line distance whose line is a derived `line_ref`
result keeps its previous wording (not in this slice, recorded).

## 3. NL → TypedFacts V2 audit (P2) — `audit/NL_GAP_MATRIX.md`

What runs: extraction is **LLM only** (`TransportExtractor`; no deterministic NL parser exists); offline it is a recorded
replay. Deterministic and therefore measurable: schema/source identity/verbatim quotes/roles (extraction validator) →
Source Gate → planner → engine → envelope. Findings (DEV_AUTHORED probes, 51-item dataset + `audit/provenance_probe.py`):

* No incorrect-served case found: 51 gold items (38 served correctly, 9 refused correctly, **4 valid wordings refused**),
  7 unfaithful payloads refused (wrong target / value / plane, non-premise clauses made premises), 6 stated-vs-derived
  provenance probes refused with a code.
* **NL-1 fixed** (`30530cf8`): `Đáy ABCD là hình vuông, cạnh 4` / `… với cạnh 4` / `… và có cạnh 4` / `… có độ dài cạnh bằng 4`
  were refused `UNGROUNDED_VALUE`; the clause grammar `_C_DAY` takes the connectors of `_CANH_SAU_DAY`. 8 wordings × 3 sizes
  served with the formula value, 11 negative-metamorphic cases keep refusing.
* **Open, pinned, deliberately not loosened:** NL-2 side in parentheses; NL-3 `mặt phẳng đáy (ABCD)`; NL-4 `d(S, BD)`
  notation; NL-5 `mặt phẳng chứa mặt bên (…)`. By design, not a gap: `số đo góc` (the product answers cos², never degrees).
* Wordings that already worked: tính/tìm, đến/tới, 6 `SA ⊥ đáy` formulations, plane names `(BCC'B')` in 6 spellings incl. `′`.

## 4. Independent evaluation readiness (P3) — `protocol/`

Built and tested (47 tests in `test_nl_eval_scoring.py`): `backend/scripts/nl_eval_scoring.py`, `run_nl_eval_offline.py`, dataset protocol
(`NL_EVAL_PROTOCOL.md`), request for an independent author (`HOLDOUT_AUTHORING_BRIEF.md`). Layers are scored separately
(entity · facts · provenance · goal · outcome · contradiction · e2e ratios) and never summed; outcomes are
`CORRECT/INCORRECT_SERVED`, `CORRECT/INCORRECT_REFUSED`, `EXTRACTION_FAILURE` (never a correct refusal). `validate_dataset` /
`claim_ceiling` / `dataset_sha256` enforce provenance, exposure, split, registration; a HOLDOUT cannot be `SAME_AGENT` or
exposed, and one edited character voids its registration.

| Dataset | Items | Author | Label |
|---|---|---|---|
| `inputs/nl_dev_authored.json` | 51 (+ 7 stress payloads) | implementing agent | `DEV_AUTHORED_NOT_INDEPENDENT` |
| 60 cases of `independent-nlu-extraction-evaluation` | not imported | blind agent (gold: implementer) | `EXPOSED_PRIOR` — the locked 44 were scored once live; no longer held out |
| independent holdout | **none** | — | `INDEPENDENT_HOLDOUT_NOT_EXECUTED` |

Result (GOLD arm, 0 calls): `CORRECT_SERVED 38 · INCORRECT_SERVED 0 · CORRECT_REFUSED 9 · INCORRECT_REFUSED 4 ·
EXTRACTION_FAILURE 0`; STRESS arm `CORRECT_REFUSED 7`; contradictions 2/2 refused by the gate. G05 (`471a2c79`, read only): the
exact-value key, the "provider failure is never a correct refusal" rule, the outcome taxonomy and the stop policy were
rewritten for V2; its LLM_ONLY scene replay / live runner / certifier were not reused; no raw responses copied. **Live calls: 0.**
A live pilot needs its own protocol and `LIVE_PROVIDER_GO_REQUIRED` (approval packet in the protocol §7); not run.

## 5. Second vertical slice — line–plane and plane–plane distance (P4)

Commit `059daadc`. The kernel and the IR already measured `distance(line, plane)` and `distance(plane, plane)` exactly (0
when the objects meet); the registry, planner, bridge and engine did not expose them. Added: `ask_distance_line_plane`,
`ask_distance_planes` (`provider_offered=False`: route A surface unchanged), planner dispatch, `/2` bridge keys `{line, plane}` /
`{plane1, plane2}`, ask grammar (`khoảng cách giữa/từ … và/đến …`, both operand orders), engine emission and an **independent
Gram-determinant cross-check** (`_kc2_duong_mat`, `_kc2_mat_mat`) that refuses `ENGINE_SELF_CHECK_FAILED` when the kernel and the
check disagree. The generic layer already names the answer `d(AB, (SCD))`, `d((ABC), (A′B′C′))`.

Oracles (closed form from the stated facts): pyramid `S.ABCD`, `SA ⊥ base` — d²(AB,(SCD)) = h²s²/(h²+s²), d(BC,(SAD)) = d(CD,(SAB)) = s,
d(AD,(SBC)) = d(A,SB); right prism — d((ABC),(A′B′C′)) = h, d²(AA′,(BCC′B′)) = x²y²/(x²+y²), d(BB′,(ACC′A′)) = x; cuboid — five
face/edge/base distances; regular pyramid d²(AB,(SCD)) = s²H²/m². One hand-written oracle was **wrong** (CD,(SAB) by false
symmetry) and the engine disagreed: corrected from first principles (AD ⊥ (SAB) ⇒ s).

Tests (`test_typed_fact_next_v2_line_plane_distance.py`, 48): oracles × sizes × renamed labels × 7 wordings, intersecting/
contained ⇒ 0, refusals with exact codes (other line/plane, arity, repeated label, unknown label, assertion/proof/conditional/negated/
"bình phương"/"rồi nhân đôi"/second object), off-plane fourth label, route A declarations unchanged, three fault injections (kernel
value off by one for each ask; the independent check itself corrupted) ⇒ `ENGINE_SELF_CHECK_FAILED`.
Browser (`browser-line-plane-distance/`, final code): 7 served + 2 refused rows × 1440/390 = **18/18**, `goal_named_as_asked` 14/14, value² equals
the closed-form oracle, Mode A hides, Mode B shows once, 0 JS errors, 0 external requests.
**Limitations:** the answer has no drawn foot segment (the perpendicular-witness annotation exists for point–plane, not yet for
line–plane); a line that meets the plane is served as 0 (true value), as the kernel defines it.
This is `OFFLINE_BROWSER_E2E_VERIFIED` for #3, #4, #11, #12 — **not** a family FULL.

## 6. Versions, cache, identity (P5)

| Identity | Before → after | Why |
|---|---|---|
| `REGISTRY_VERSION` | `geometry-functions/13 → /14` | two new asks + a source-gate clause (precedent: `source-gate-hardening` bumped the registry) |
| `PLANNER_VERSION` | `/14 → /15` | new distance dispatch |
| `ENGINE_VERSION` | `/13 → /14` | emission + independent checks |
| `typed-fact-next-bridge/2` | unchanged | names the schema generation |
| `CACHE_VERSION` | `130` (unchanged) | default `/api/analyze` never imports `geometry_functions` / `function_route`; Hybrid local route answers `no-store`; preview refuses the product cache |
| route A surface | `7ea511a6…`, `485d3834…` unchanged | pinned by `test_version_constants_surface_fingerprints…` |

`IDENTITY_DELTAS` declares the triple for preview-fixture verification; pins updated in 6 tests (4 version pins, 2 route-B-only
declaration sets). Locked oracles untouched.

## 7. Full T3 (P5/P6)

| Item | Value |
|---|---|
| product commit | `059daadc418268d0707d6ff58e8650e5137e235d` |
| freeze | `28a6a348` — 118 measured files, `fef0b050e42f6ee8629e76ddb44f6b3dc0191cf89f5df922d8a62be54ef71657`; divergence declared `34ecce49` |
| candidate (clean detached checkout) | `34ecce4961c2e6369dcf9e03ce9919540c96420d`, tree `e6351742…`, source clean before and after |
| verdict | **`FULL_PRODUCT_GATE_PASS`**, exit 0, 2026-10-26 19:19–19:30 UTC |
| backend pytest | 12228 passed, 1 skipped, 15 xfailed, 0 failed |
| frontend vitest | 1417 / 1417 (83 files); typecheck + build, demo replay, crash surface PASS |
| post-run freeze verify | MATCH; freeze file SHA-256 identical before/after (`becc55ad…`) |
| streams | `full-t3/stdout.log` `faa011c1…`, `full-t3/stderr.log` `aa9b7207…`; receipt `full-t3/receipt.json` |
| provider calls | 0 (`ALLOW_LIVE_AI=0`, `HYBRID_V2_LOCAL` unset) |

Everything committed after `34ecce49` on this branch is documentation or run evidence (this report, handoff, `run.json`, indexes,
the provenance probe and the T3 receipt); no measured product file changed, so the receipt still describes the code. Earlier local
full runs in this worktree, made before the freeze was committed, showed 12 red tests (candidate-freeze / identity / pre-check tests that read the frozen
candidate); they are green in the detached T3. The two route-B-only declaration tests that the new asks turned red were updated in `059daadc`.

### Merge gates (P6) — `MERGE_READY_PENDING_OWNER_GO`

| Gate | State |
|---|---|
| Full T3 PASS + freeze MATCH | PASS (`34ecce49`) |
| browser E2E within the claimed scope (1440/390, offline replay) | PASS (16 + 18 rows) |
| oracles + negative tests + fault injection | PASS (§2, §5) |
| known incorrectly served case | none known — DEV data only, not a proof |
| default `LLM_ONLY`, `CACHE_VERSION = 130`, route A surface | unchanged (pinned by T3 tests) |
| live provider | 0 calls |
| independent holdout / independent review | **not executed** — no migration-readiness claim; opt-in code integration is a separate decision from enabling Hybrid |
| Owner GO to merge and push **for this task** | **absent** — nothing merged or pushed; `main` = `origin/main` = `dd557f8f` |

## 8. Answers to the 18 report questions

1. Baseline `main` `dd557f8f`. 2. Product commits `4eae907d` (D-10), `30530cf8` (NL-1), `059daadc` (line–plane / plane–plane distance); freeze `28a6a348`, divergence `34ecce49`.
3. D-10 corrects the semantic goal for named lines (§2). 4. **No** known incorrectly served problem; not a proof (DEV data).
5. §3. 6. D-10, NL-1, the evaluation harness, line–plane/plane–plane distance. 7. **No** independent dataset. 8. `nl_dev_authored.json`
(51, + stress) and every test fixture of this run are DEV_AUTHORED by the implementer. 9. §4. 10. **No** live calls.
11. Yes (§5). 12. 1440 and 390: 16 + 18 rows PASS (§2, §5), offline replay, not live NL. 13. §7. 14. registry `/14`, planner `/15`,
engine `/14`, bridge `/2`, cache 130. 15. 18-family matrix: **0 FULL / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED**, no class change;
OFFLINE_BROWSER_E2E_VERIFIED gains line–plane/plane–plane distance for #3 #4 #11 #12 and the asked-line name for #3 #4 #11 #12.
16. `INDEPENDENT_HOLDOUT_NOT_EXECUTED`, `INDEPENDENT_REVIEW_NOT_EXECUTED`. 17. Not merged, not pushed: `MERGE_READY_PENDING_OWNER_GO`
(§7). 18. `NEXT_AGENT_HANDOFF.md`.
