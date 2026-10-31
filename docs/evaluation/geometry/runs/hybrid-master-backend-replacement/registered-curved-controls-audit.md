# REGISTERED_CURVED_CONTROLS_AUDIT

Seventh continuation of `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`, 2026-10-31. Offline, 0 provider calls.

Scope:

- the 32 Owner-registered curved control cells on `/4` (`a4`). These are 26 `target-grammar-identity-recovery` cells and
  6 `measurement-dispatch-and-identity-order` cells.
- the 12 curved probes among the 203 probes whose `/4` outcome moved from the F7 snapshot.

## Rule applied

**What may change.**

- A cell may only move from one REFUSED code to another REFUSED code.
- A REFUSED → SERVED move is never recorded in a transition layer. It would be an `OWNER_CONTRACT_CONFLICT`, which means
  withhold the change and propose it to the Owner.

**What stays fixed.**

- The registered oracle files are not edited.
- Layer 1 (`registered-curved-control-transitions.json`, sixth continuation) is not edited.
- Layer 2 (`registered-curved-control-transitions-2.json`) corrects layer 1:
  - each `before` in layer 2 equals the matching `after` in layer 1;
  - the tests compose the two layers in one place (`test_target_grammar_identity_recovery.load_transitions`);
  - the tests assert both the chain and the REFUSED → REFUSED rule.

A transition does not pass just because the outcome is still REFUSED. Each code was checked against what the input actually
says.

## Findings

| # | Finding | Class | Action |
|---|---|---|---|
| R1 | 5dc812ed..c3bc1f67: an unread curved clause was refused as `SOURCE_OBJECT_MISMATCH`, which moved the group from CAPABILITY to SOURCE_UNVERIFIED. The input did not name a wrong object; the grammar could not read it. | REFUSAL_REASON_REGRESSION | **Fixed.** A parse failure now refuses with `CURVED_WORDING_UNSUPPORTED` (CAPABILITY) in `_khoi_cong_dung_nguon`, `_CHIA_NON` and `_doc_mat_cat`. The adversarial suites pin the exact code per case. |
| R2 | Two curved sections in one run, and the question "diện tích thiết diện qua trục" names `sec_axial`. The bounded binder `_mat_cat_khop` reads a section question only when the run has one section, so it returned "câu hỏi về đối tượng khác" (`SOURCE_OBJECT_MISMATCH`). That statement is false for the cone cell. | REFUSAL_REASON_REGRESSION | **Fixed RED→GREEN.** The binder now raises `CURVED_MULTI_SECTION_UNSUPPORTED` (CAPABILITY) when the run has more than one section. It is locked by the 4 `K.*.area.section*` control cells: reverting the fix makes the layer-2 assertion red. |
| R3 | Base-centre grammar (registry /25) | — | The figure sentences of the controls now parse. Every refusal comes from the question binder, so layer 1's stated cause ("wording outside the grammar") is out of date for all 32 cells. Layer 2 records the current cause, including the 22 cells whose code did not change. |

## The 32 cells

`before` is the registered value: REFUSED `BRIDGE_UNSUPPORTED_CURVED`, group CAPABILITY. `after` is the composed layer-2 value.

| Cells | Count | After | Group | Class | Why the code is true of the input |
|---|---|---|---|---|---|
| `K.{cone,cyl}.volume.{solid,solid_id,notation}` + `CTRL.K.*.volume.solid` | 8 | `SOURCE_OBJECT_MISMATCH` | SOURCE_UNVERIFIED | JUSTIFIED_REFUSAL_REFINEMENT | The goal quote "Tính thể tích" names no solid. The cone run declares three solids (cone, small cone, frustum). |
| `K.{cone,cyl}.radius.{solid,notation}` + `CTRL.K.*.radius.solid` | 6 | `SOURCE_OBJECT_MISMATCH` | SOURCE_UNVERIFIED | JUSTIFIED_REFUSAL_REFINEMENT | "Tính bán kính." names no object, and both a base radius and a section radius exist. |
| `K.{cone,cyl}.radius.section*` | 4 | `SOURCE_OBJECT_MISMATCH` | SOURCE_UNVERIFIED | JUSTIFIED_REFUSAL_REFINEMENT | Same quote, and no section is named. Adapter /3 also refuses (`GEOMETRY_OPERAND_TYPE`). |
| `K.{cone,cyl}.area.{solid,notation}` | 4 | `SOURCE_OBJECT_MISMATCH` | SOURCE_UNVERIFIED | JUSTIFIED_REFUSAL_REFINEMENT | The target is the solid but the quote asks a section's area: a true mismatch. Adapter /3 also refuses (`GEOMETRY_OPERAND_TYPE`). |
| `K.{cone,cyl}.area.section*` | 4 | `CURVED_MULTI_SECTION_UNSUPPORTED` | CAPABILITY | JUSTIFIED_REFUSAL_REFINEMENT (after the R2 fix) | Two sections are present, and the bounded binder covers one. The group is the same as the registered one. |
| `K.{cone,cyl}.lateral_area.{solid,notation}` + `CTRL.K.*.lateral_area.solid` | 6 | `NOT_ASKED_IN_SOURCE` | SOURCE_UNVERIFIED | JUSTIFIED_REFUSAL_REFINEMENT | The shared question-context gate (S1 closed tail) cannot verify the tail ", diện tích thiết diện qua trục, tỉ số thể tích …". Polyhedra get the same rule. |

Totals:

- 32 / 32 REFUSED;
- 0 SOURCE_GROUNDING_REGRESSION;
- 0 open REFUSAL_REASON_REGRESSION (R1 and R2 are fixed);
- 0 UNRESOLVED;
- 0 OWNER_CONTRACT_CONFLICT present.

Two latent conflicts are proposed below and not implemented.

**Adapter /3 evidence (not acted on, since LLM_ONLY and Adapter /3 are out of scope):**

- `K.cyl.area.section*`: Adapter /3 SERVED the axial-section area for the quote "diện tích thiết diện tròn", which names the
  *parallel* circle. This is a possible Adapter /3 wrong binding.
- `K.{cone,cyl}.radius.{solid,notation}`: Adapter /3 served a bare "Tính bán kính." even though more than one circle exists.

Both are recorded for the Owner.

## The 12 moved probes (203-probe set, `/4` only)

| Probe | Before | After | Class |
|---|---|---|---|
| `C.cone_base`, `C.cone_volume_target_notation_alias`, `C.cone_highlight_control`, `C.cone_single_hyphen_id`, `C.cone_single_multi_hyphen_id`, `F5.curved_target_notation_alias` | `BRIDGE_UNSUPPORTED_CURVED` | `CURVED_MULTI_SECTION_UNSUPPORTED` | JUSTIFIED_REFUSAL_REFINEMENT (CAPABILITY → CAPABILITY): an axial plus a ratio section in one run |
| `C.two_cones_control`, `C.two_cyl_hyphen_control`, `C.two_cyl_underscore_control`, `C.two_cyl_hyphen` | `BRIDGE_UNSUPPORTED_CURVED` | `BRIDGE_UNSUPPORTED_CURVED_COMPOSITE` | JUSTIFIED_REFUSAL_REFINEMENT (CAPABILITY → CAPABILITY): two solids of revolution |
| `C.cyl_base`, `C.cyl_volume_target_notation_with_prime` | `BRIDGE_UNSUPPORTED_CURVED` | `SOURCE_OBJECT_MISMATCH` | JUSTIFIED_REFUSAL_REFINEMENT: the goal quote "thiết diện qua trục" (inside "diện tích thiết diện tròn và thiết diện qua trục") carries no measure word |

There are 0 REFUSED → SERVED moves and 0 wrong serves.

The 8 Adapter /3 fixtures that /4 refused still refuse. The base-centre grammar was necessary but not sufficient. The next
blockers, in order, are:

1. coordinated question lists (P-1);
2. multi-section binding (P-2);
3. the unordered "tỉ số thể tích" in the cone fixtures, which has no order to bind and so stays a refusal.

## Owner proposals (withheld; the locked policy stays until approval)

- **P-1 Coordinated question lists.**
  - The wording: "Tính thể tích, diện tích xung quanh hình nón, … và …" distributes one object over several measures.
  - What would change: binding it would SERVE `K.*.volume*` / `K.*.lateral_area*`, which are registered as REFUSED.
  - What it needs: an Owner repin of those cells (registered → SERVED with the Adapter /3 answer as the oracle), plus a
    change to the shared question gate that also reaches polyhedra.
- **P-2 Multi-section binding by kind.**
  - The wording: "thiết diện qua trục" binds the axial section, and the plane name "(α)" or "thiết diện tròn" binds the
    parallel one.
  - What would change: it would SERVE `K.cone.area.section*`, which is registered as REFUSED.
  - What it needs: an Owner repin.
