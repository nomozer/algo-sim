# Hybrid V2 vertical slice

Status: NOT_STARTED_AWAITING_P7. No new Hybrid slice or backend capability was implemented during watchdog recovery. After verified local main integration and safe cleanup, choose one reusable slice based on the fresh gap audit and implement its source-bound facts, witness/engine, bounded planning, trace/envelope and offline E2E/refusal checks together.

## Implemented slice — named planes on canonical V2 distance / angle goals (Claude, 2026-10-26)

Status: **`OFFLINE_ADAPTER4_E2E_VERIFIED`** for authored payloads (families #3 and #12). Not a holdout, not an extraction
measurement, no provider call, no browser row.

Branch `research/hybrid-v2-backend-generalization` from `main` `a9889031`:

| Commit | What |
|---|---|
| `1cff5458` | product + tests: `feat(geometry): serve V2 distance and angle goals on planes named by all their vertices` |
| `0201c274` | `chore(eval)`: re-freeze candidate on the clean tree — 118 files, `c10917978af38f2c…` (was `3850e787…`) |
| `19a763c1` | `eval(geometry)`: candidate divergence layer `inputs/candidate_divergence.json` (corrects the `claude-to-codex-takeover` layer) |

### What changed (one authority per step)

`TypedFactNext /2 → Source Gate → Planner/Registry → Engine → verified output → Adapter /4 / Scene3D`:

1. **Bridge** (`typed_fact_next_bridge._operand`): a plane operand of a `/2` `distance` or `angle` goal is three or more
   DISTINCT labels; a line / segment stays exactly two. Repeated labels and wrong shapes stay `INVALID_MATH_GOAL`.
2. **Source Gate**: unchanged. The question quote must still name the plane (`_cung_mat`).
3. **Planner**: `ask_distance_point_plane` keeps the registry's three-label slot (that schema is part of the
   function-calling surface `7ea511a6…`, left unchanged). When the asked plane has more labels, the full group goes to
   `KeHoach.named_planes` (also for a described point). Angle calls already carried the whole plane.
4. **Route** (`function_route.run_fact_route`): passes `named_planes` beside `calls`; branch A (function calling) never
   sets it, and the field can only add checks.
5. **Engine** (`_Dung.kiem_mat_viet`): exact coplanarity and non-degeneracy now also cover `named_planes`; a > 3-label
   question plane whose first three labels are collinear is refused `COLLINEAR_POINTS` (`ponytail` ceiling: refused, not
   reordered).

**Correction to the message of `1cff5458`:** it says the collinear check replaces "a Gram division by zero". Measured
afterwards with the check disabled (file restored byte-identical): the distance case was still refused, as
`SOURCE_OBJECT_MISMATCH` "(BMC) không phải một mặt phẳng" (the truncated call group), and the angle case already got the
kernel's `COLLINEAR_POINTS`. No division by zero occurred. The check only gives the distance case the correct reason and
the same code as the angle case. The commit is not rewritten; the test was renamed accordingly in the docs commit.

Unchanged: registry / planner / engine version strings, prompts, schemas, grammar card, capability table,
`CACHE_VERSION = "130"`, `LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `/api/analyze` (does not import `geometry_functions`),
frontend, Scene3D renderer, IR emitted for every plan accepted before. Scene contract unchanged ⇒ no browser smoke run.

### Oracles (closed form from the stated facts; no engine coordinates)

| Case | Oracle | Result |
|---|---|---|
| right prism, d²(A, (BCC'B')), labels ABC / DEF / KLM, sizes (6,8,12) (3,4,5) (12,16,7) | x²y²/(x²+y²) | PASS |
| d²(B, (ACC'A')) | x² | PASS |
| same face in 4 label orders, incl. crossed (B C' C B') | same value | PASS |
| (BCC'B') named by 4 labels vs 3 labels | equal | PASS |
| cos²(A'B, (ACC'A')), 2 sizes | h²/(x²+h²) | PASS |
| cos²((BCC'B'), (ACC'A')), 2 sizes | y²/(x²+y²) | PASS |
| uniform scale × 2 | d² × 4 | PASS |
| pyramid S.ABCD, square side s, SA ⊥ (ABCD), SA = h: cos²(SC, (ABCD)), (s,h) = (4,3) (2,5) (6,1), labels SABCD / PKLMN | 2s²/(2s²+h²) | PASS |
| cos²((SCD), (ABCD)) | s²/(s²+h²) | PASS |
| d²(S, (ABCD)) | h² | PASS |
| Adapter /4 envelope, angle | SERVED; provenance `ask_angle_line_plane` with `plane [A,B,C,D]` | PASS |
| Adapter /4 envelope, distance | SERVED; call `plane [B,C,C']` (registry contract), quote names `(BCC'B')` | PASS |

Invariance covered: label renaming (5 label sets), plane label order, 3- vs 4-label naming, uniform scale. Translation and
rotation are not observable through this interface (the engine chooses the layout; the oracle uses no coordinates).

### Refusals (fail closed, typed)

| Case | Code |
|---|---|
| fourth label off the plane — distance [B,C,C',A'], angle [A,B,C,B'], dihedral [B,C,C',A] | `SOURCE_OBJECT_MISMATCH` |
| quote names (BCC'), target adds A' (review I-1: only the engine's every-label check can catch it) | `SOURCE_OBJECT_MISMATCH` |
| pyramid base with the apex as fourth label [A,B,C,S] | `SOURCE_OBJECT_MISMATCH` |
| quote names (ACC'A'), target (BCC'B') | `SOURCE_OBJECT_MISMATCH` |
| collinear leading labels [B,M,C,C'], M midpoint of BC — distance and angle (without the new check: distance `SOURCE_OBJECT_MISMATCH`, angle `COLLINEAR_POINTS`) | `COLLINEAR_POINTS` |
| repeated label, two-label plane, string plane, non-string label | `INVALID_MATH_GOAL` / `INVALID_TYPED_FACT_NEXT` |

Changed expectations in earlier tests (no negative case removed): `test_four_label_plane_target_is_refused_not_truncated`
→ `…_is_served_with_every_label_checked` (the coplanar face is now the capability); the non-coplanar `[A,B,C,A']`
(distance) and `[A,B,C,B']` (angle) moved from `INVALID_MATH_GOAL` to dedicated tests expecting the engine's
`SOURCE_OBJECT_MISMATCH`. `COLLINEAR_POINTS` added to the benchmark refusal taxonomy as `unsupported` (taxonomy only).

### Fault injection (each reverted; file SHA-256 identical afterwards)

`fault-injection.json`: 10 faults, **10 detected**.

| Fault | Failing tests |
|---|---|
| F1 planner forgets the full distance plane | 3 |
| F2 route drops `named_planes` | 3 |
| F3 engine ignores `named_planes` | 3 |
| F4 engine skips the collinear-leading check | 1 |
| F5 bridge back to exactly three plane labels | 32 |
| F6 bridge accepts repeated labels | 9 |
| F7a bridge truncates the distance plane | 3 |
| F7b bridge truncates the angle plane | 1 |
| F8 coplanarity loop skips `named_planes` | 2 |
| F9 bridge accepts lines longer than two labels | 1 |

### Effect on the 18-family matrix

No overall classification changes: still **0 FULL_E2E_VERIFIED / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED**. Delta: the
`/4` column for distance/angle goals that name a plane by all its vertices becomes OFFLINE_GEOMETRY_VERIFIED for #3
(S.ABCD, SA ⊥ base) and #12 (right triangular prism). #4, #11, #13 are expected to benefit through the same code but were
**not** tested. FULL_E2E for any family still needs a `/4` browser row (desktop + mobile), independent expectations and
NL extraction evidence.

### What this does not establish

- NL extraction: payloads are authored; whether an extractor emits four-label planes is UNKNOWN. Live calls: 0.
- Independent review / holdout: not run. The tests above are authored development tests.
- Browser: not run (scene contract unchanged).
- Version strings were not bumped (`ENGINE /12`, `PLANNER /13`): every plan accepted before emits the same calls and IR,
  and a bump would regenerate frontend preview fixtures. **Owner decision** whether this engine refusal deserves a bump.
