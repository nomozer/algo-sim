# R-1 · SL-3 · bridge regex — Continuation 13 audit

> **Evidence class:** `IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC` + `OFFLINE_DETERMINISTIC_FIXTURE_TEST`. 0 provider calls.
> **Product commit:** `9503482a7480c2e8501efa8bcef0ce2c37776287` (`measured_system_hash = 773e440de0385d577040a9eca107706bfb2d3e4aec1d827b52c99c89d42ac7c3`, `118` files; Registry `/29`, Planner `/23`, Engine `/20`).
> **Receipts:** `r1-described-point-probe.json` (at `e4240c99`) & `r1-described-point-probe-r2.json` (clean at `9503482a`, `product_uncommitted: false`), `s2-pilot-gold-replay-r3.jsonl`, `inventory-phase-p2.json`, `continuation13-adversarial-review.md` (`READY`, Round 2), `backend/tests/geometry/test_route_d4_described_points.py` (`55/55`). This layer corrects the `/4` part of
> `planner-recomposition-route-d4-correction.md` (that report is unchanged).

## 1. Root cause (R-1)

The goal path on `/4` lost an unnamed described point **before the planner**, at the contract:
- `MathGoalSpec.target` operands and a section's `through_point` accept only labels. A described point has no label, so the
  bridge refused it with `INVALID_MATH_GOAL` / `INVALID_QUALIFIED_REF` (C12 probe).
- The rest of the chain already handled such points on route B:
  - the planner's `_EffectResolver` resolves `("desc", kind, inputs)` needs over the Registry descriptor contracts;
  - the Source Gate certifies an `effect-chain` whose goal measures from one described point;
  - the engine checks the description on the built figure.

Nothing below the bridge needed to change for one described point per goal.

## 2. The representation (`typed-fact-next/2`, additive)

`described_points: [{described_id, kind, <operands>, quote}]`:
- **kinds:** the six Registry descriptor contracts — midpoint, centroid, orthogonal_projection,
  orthogonal_projection_line, intersect_line_line, intersect_line_plane;
- **operands:** exactly those of the kind;
- **quote:** the verbatim describing phrase.

The point is used by writing `@id` where its label would stand:
- in a measurement goal's point operands (`point`, `segment`, `line`, `line1`, `line2`, `polygon`);
- in a section's `through_point`;
- in another described point's point operand.

| Concern | Rule (where) |
|---|---|
| A described point is never a fact or a label | An `@id` in a premise, a plane, a relation or a simulation goal → `INVALID_DESCRIBED_POINT` (`_check_described_refs`, a count of every `@` string). |
| Declared, used, unique | Undeclared → `UNKNOWN_DERIVED_REFERENCE`; declared but unused → `DANGLING_DEPENDENCY`; duplicate id → `INVALID_DESCRIBED_POINT`. |
| Explicit dependencies, cycles, depth | `@` inside a described point = an edge; a cycle → `DEPENDENCY_CYCLE`; nesting > 2 → `PLAN_TOO_LARGE`. |
| Operand shape | Exactly the kind's fields; distinct operands (both lexical and canonical via `canonical_vertex_ref`); no self reference; planes and polygons are labels only. |
| Scope / ownership | `scope_records` checks the labels of a described point in every non-`None` consumer solid scope (`_described_consumer_scopes`, propagating nested `@id` dependencies upward so a shared `@id` cannot launder cross-solid vertices past `S5`/`S7`/`S8`). |
| Provenance | The describing quote must lie inside the quote of every goal or section that uses it (`_mo_ta_cua`, `SOURCE_OBJECT_MISMATCH`). The extractor's verbatim check already covers every `quote`. |
| `/1` | Unchanged: any `@` stays `INVALID_MATH_GOAL`. |
| Identity aliasing | Two ids with the same description become one point: the planner builds it once (test-locked). |

**Model surface (Hybrid arm only):**
- the provider response schema gains `described_points`;
- the `/2` extraction instruction gains one sentence.

The flat, v3 and Route A schemas, the `TypedFact` JSON schema, function declarations, the LLM_ONLY arm and `CACHE_VERSION` 131 are unchanged.

## 3. What changed below the contract

- **Bridge** (`typed_fact_next_bridge.py`):
  - `_mo_ta_phang` turns each described point into route B's flat description (`point_kind` + `points`, in the
    contract's input order);
  - `_cau_hoi_mo_ta` maps a goal with ONE described operand to route B's described question (`distance(point, plane)`, `distance(point, line)` on `point`, `distance(segment)`, `angle(line, plane)` on `line`, `angle(line1, line2)` on either line, and 3-vertex `area(polygon)`); any uncontracted `@id` shape (such as `distance(line, plane)`, ≥4-vertex `area(polygon)`, curved goals/sections with `@id`, or `D2` two-`@id` goals) refuses cleanly at the bridge with `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` (`CAPABILITY`);
  - `_mat_fact` maps a described through-point to a section's `point_kind` + `points`.
  - So the **same** planner, Source Gate and engine run. There is no flat-route call, no adapter of its own, no
    construction list and no case rule.
- **Planner, engine, Registry functions and contracts:** unchanged.
- **Refusal classes:** `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` is CAPABILITY; `INVALID_DESCRIBED_POINT` is EXTRACTION_FAILED.

## 4. Results on `/4` (`run_hybrid_offline`, the production opt-in path)

| Case | Answer | Hand oracle | Telemetry |
|---|---|---|---|
| C1a | 3√34/5 | 3√34/5 | DISCOVERED_FUNCTION_COMPOSITION |
| C1b | √3 | √3 | DISCOVERED_FUNCTION_COMPOSITION |
| C2 | √2/2 | √2/2 | DISCOVERED_FUNCTION_COMPOSITION |
| C3 | 5/6 (cos²) | 5/6 | DISCOVERED_FUNCTION_COMPOSITION |
| C4 | 3√34/5, 36/25 | same | DISCOVERED_FUNCTION_COMPOSITION, one foot built for both goals |
| C5 | 1107/250 | 1107/250 | DISCOVERED_FUNCTION_COMPOSITION |
| C6a | √3/6 | √3/6 | DISCOVERED_FUNCTION_COMPOSITION |
| C6b | 20√6/27 | 20√6/27 | DISCOVERED_FUNCTION_COMPOSITION |
| C7 (prism) | 4√34/5 | 4√34/5 | DISCOVERED_FUNCTION_COMPOSITION |
| N1 (named control) | 2√6/3 | 2√6/3 | REGISTERED_DECOMPOSITION |

The hand derivations are in the probe's docstring; each also agrees with the route B value of the C11 matrix.

**Adversarial extractions, 6/6 refused, none served:**
- operands swapped under the same quote;
- the wrong descriptor kind;
- a describing quote that is not in the goal;
- a swapped target plane;
- a described point the text does not describe;
- a section through-point with a different description.

**Also locked by tests:**
- metamorphic: ids renamed and premises reordered, same answer;
- a degenerate description (AB ∥ CD) is refused;
- every malformed contract shape is refused with its own code.

**C11's development cases (`DISCOVERED_FUNCTION_COMPOSITION`) now 9/9 on `/4`.**

Limit: on `/4`, a *named* triangle's area is still `BRIDGE_UNSUPPORTED_MEASUREMENT`, as the locked
target-grammar controls pin it. Only the described form (C1b) maps to `ask_area`. Opening the named form is a separate
capability change with its own registered transition.

## 5. D1 / D2

| | D1 (nested) | D2 (two described operands) |
|---|---|---|
| Representable in `/2` | **Yes** (validated: depth 2, acyclic) | **Yes** |
| Registry producers / plan | Yes / oracle 3 steps, √2 | Yes / oracle 3 steps, √6 |
| Planner resolver | Recursive on `("desc", …)` needs by construction | Two Point needs |
| Source Gate | **No certificate:** an `effect-chain` names ONE described operand, its target points must be source labels, and the descriptor grammar has no nested phrase | **No certificate**, same reason |
| `/4` outcome | `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` (CAPABILITY), fail-closed | same |

Status: **representable; Source Gate certification not implemented.** This is neither
`REPRESENTATION_BLOCKED` (the contract carries them) nor a search miss. Unlocking them means generalizing
`registry._kiem_result_binding.chain`:
- several `operand` records;
- produced (not source) target points;
- recursive descriptor phrases with renamed groups.

That is a change to the Source Gate's most safety-critical check. It is left for its own reviewed step, not bundled here.

## 6. SL-3 — student shorthand

**Root cause:** the Source Gate's ask grammar read the words "khoảng cách" and "đường thẳng" literally.
- **Fix** (Registry `/29`):
  - `k/c` (case-insensitive, including sentence-initial `"K/c"` and `"K/C"`) is accepted as a whole token wherever the ask grammar reads "khoảng cách" (`_KC`, `_KHOANG_CACH_DIEM_DUONG`, `_DICH_KHOANG_CACH`, plus `re:(?i)...` keywords on `ask_distance_*`);
  - `đt` is accepted as a line's noun before its two labels across `_doan_cum`, `_KHOANG_CACH_DIEM_DUONG`, `_DICH_KHOANG_CACH`, descriptor phrases (`orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`), and `ask_angle_line_plane` / `ask_angle_lines`;
  - `mp` was already read before a plane's labels.
- **Not done:** abbreviations are not expanded in `chuan_hoa`, which would rewrite source text for every route.
- **Minimality:** two other candidate additions (neutral object nouns, goal-body words) were tried and removed; no case
  needed them.

| | Before (r2, `800ab355`) | After |
|---|---|---|
| S-2 gold end-to-end | 33/36 | **35/36** |
| False refusal (expected-serve) | 3/18 | **1/18** (S07) |
| Wrong-served | 0 | 0 |
| Source Gate attribution | 3 | 1 |
| C10 probe gold / adversarial | 52 served-correct, 3 false refusal / 20/20 safe | **identical, 0 transitions** |

**Contrastive tests, all refused:**
- the wrong plane;
- "kk/c" (not a token);
- "k/c … đến mp." (no operand);
- "Biết k/c … bằng 3" (a given, not asked);
- "đt S" (one label).

**Not unlocked: S07 "hình chop".** A missing tone mark on the solid word is diacritic restoration, which is Owner policy
S-1. It is not guessed here.

## 7. The literal BACKSPACE regex (`_v2_plane_def_quotes`)

- **Bytes:** the file held `dựng` + `0x08` where `\b` was meant (since `c15eebe4`). The rule "skip an imperative
  (Hãy) dựng … sentence when looking for the plane's declarative definition" therefore never fired.
- **RED reproduction, function level:**

  | Text | Defect returned | Intended skip-only fix would return |
  |---|---|---|
  | declarative + restating imperative | `[]` | `[declarative]` |
  | imperative only | `[imperative]` | `[]` |

- **End to end:** none of the three texts changes outcome. The declarative + imperative text is refused by a separate
  Source Gate rule (`mat_song_song_dung_nguon`: two definitions of (P)). The imperative-only text is served correctly
  (3√2/2, hand-checked) before and after. No fail-open was found.
- **Fix:**
  - one candidate → use it;
  - an imperative that restates the one declarative definition word for word → the declarative;
  - any other set → none.

  A pure skip was rejected: it would have turned the correct imperative-only serve into a refusal.
- **Edit method:** made by a byte-exact script, not a shell-quoted edit.
- **Scan:** a byte scan of all 766 tracked backend files finds no other control byte.
- **Tests:** a test locks the absence of control bytes and the four cases.
