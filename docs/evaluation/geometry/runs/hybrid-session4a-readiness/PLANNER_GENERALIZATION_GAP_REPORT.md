# Planner generalization gap

Status: **PARTIAL — bounded reusable composition, section-specific orchestration, no general-planner claim**. Scope: product `69bd2fe4…`, verified at candidate `84c729e0…`. Root workspace's later waves are not substituted for this source.

## Four distinct responsibilities

| Layer | Actual implementation | What it establishes |
|---|---|---|
| A. Goal-directed function composition | `planner._EffectResolver._resolve/_emit/goal`, Registry `PlanningContract`, typed goal slots/effects, cost-based reuse, bounded recursion and memoization | Described midpoint/triangle centroid → area/length/distance/angles; declared intersection-line and projection chains. Function contracts can be recombined for supported typed needs; this is genuine bounded composition. |
| B. Section-specific planning | `_dinh_cat_canh`, `_khoi_tren_thiet_dien`, section grammar/rules and lateral-edge enumeration | Handwritten orchestration knows pyramid/prism lateral edges, through point, requested boundary and derived-pyramid closure; chooses reuse/named/fresh/derived vertices and emits a section certificate. |
| C. Deterministic preprocessing | `parse_typed_fact_next_v2`, `convert_v1_to_v2(route=…)`, `bridge_v2`, source clause parsing, dependency sorting and IR deduplication | Schema/identity normalization and closed semantic translation, not open-ended geometric planning. `/1` conversion preserves the declared route convention rather than discovering missing premises. |
| D. Exact kernel verification | engine `kiem_dinh_cat`, `chung_chi_khep_kin`, exact line-plane intersections, metric/containment/volume checks, interpreter, Scene3D structural validation | Checks what was planned against exact geometry, source and topology. It can refuse a candidate; verification alone is not plan discovery or browser validation. |

`intersect_line_plane` has a Registry `Meet` contract, but Session 3 selects this contract inside `_dinh_cat_canh` for section vertices. Direct source-declared point construction is another dispatch path. The generic resolver searches typed `Answer`/Point/Line/Plane needs; it does not thereby become a general search for arbitrary `Meet` consequences. **Do not claim general geometric planning from this one contract registration.**

Cost 0 reuses the section through point or an available intersection; cost 1 handles a source-named/unnamed stated cut; cost 2 synthesizes an unstated cut only where a derived solid or declared boundary requires closure. These choices operate inside handwritten section logic, then the exact engine independently verifies incidence, segment bounds and cyclic closure. A three-function trace is not proof of open-world composition.

## New development diagnostics

`planner_diagnostics.py prepare` wrote `results/diagnostic-inputs.json`, a separate oracle file and a SHA-256 lock before `evaluate` ran. Twelve newly authored problems use new dimensions (5/7/11/12), cut ratios 2/5 and 3/7, or changed centroid support/target combinations. Their source texts and fact payloads are new to these runs, while the generator and function signatures are inherited. The oracle uses existing independent Fraction coordinate/similarity helpers, not engine answers. No product changes followed evaluation.

| Track | Cases | Result | Interpretation |
|---|---:|---|---|
| Canonical `/2` section → derived pyramid → ratio + residual | 6 | 6 exact matches; 6 structurally valid scenes | Numeric/operand transfer within section-specific planning. No generic effect-chain certificate in these six. |
| Flat TypedFacts to common Planner, changed centroid goals | 6 | 6 exact matches; 6 structurally valid scenes; six effect-chain certificates | Reuse of six known signatures: centroid→area, length, plane distance, projection→length, line-plane angle, line-line angle. This is not proof that every chain is expressible through the canonical `/2` bridge. |

The measurement is **IMPLEMENTER_AUTHORED_DEVELOPMENT_NOT_BLIND**. All twelve pass, zero new producer/consumer signatures are established, and there is no independent generalization estimate. Parameter transfer is weaker than new structural capability. Original S1–S3 corpora and the new diagnostic lock remain unedited. Source text was authored as a new diagnostic, never changed to rescue a failed source problem.

## Capability matrix

“Common planner” means internal TypedFacts support; “canonical V2” means reachable through `bridge_v2`/Adapter `/4`. Schema admission alone does not imply either capability.

| Geometry / request | Canonical V2/common planner | Legacy `/1` Adapter `/3` or default route | Limit |
|---|---|---|---|
| Pyramids, supported polygon bases | V2 pyramid/prism identities, determined base/height constraints and exact measurements; supported cases measured | Also supported by specialized Adapter `/3` and selected default semantic-program routes | Not arbitrary polyhedron layout or arbitrary premise vocabulary |
| General polyhedra | Exact kernel has polyhedral verification; V2 solid bridge still only accepts pyramid/prism | Legacy semantic IR can describe selected topology | Kernel expressibility does not establish NL-to-topology or V2 planner coverage |
| Right/oblique prisms | Supported closed facts and supported section forms; named base/top, determinate geometry | Legacy prism path exists | Qualified multi-frame identity and arbitrary composite layouts are not generalized |
| Composite solids | Some shared-root, source-declared pyramid combinations/common solid operands can be represented | Adapter `/3` has explicit solid-qualified identity and composite handling | Nontrivial `vertex_bindings` or non-root coordinate frame are refused by V2 (`BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY`); no generic solid Boolean solver |
| Sections | Through point ∥ plane, ⟂ line, and supported direct section forms; G1–G7 source grammar; D6 lateral vertex completion | Legacy also supports broader specialized construction/plane forms | `/2` bridge refuses unsupported plane kinds; clipping is verified rather than searched generically |
| Derived solids | Derived pyramid whose apex/parent/boundary bind to a verified section | Specialized derived-solid paths, including selected curved cuts | V2 rejects a non-pyramid section-derived solid (`BRIDGE_UNSUPPORTED_DERIVED_SOLID`) |
| Volume ratio / remaining volume | V2 explicit numerator/denominator/parent/cut operands; exact ratio and containment/disjointness certificates | Legacy selected ratio/residual constructions | No anonymous operand guessing; positive residual and containment must be certified; residual result does not imply a new residual mesh |
| Sphere / cylinder / cone / frustum | Canonical V2 refuses curved solids (`BRIDGE_UNSUPPORTED_CURVED`) before planning | Explicit curved code in Adapter `/3` and selected semantic-program/default families | No claim of curved generalization in V2; schema support is not route support |
| Arbitrary line-plane intersections | Direct declared point or bounded section `Meet` | Specialized construction paths | No general backwards search for arbitrary unstated intersections |

## Budgets and topology

Pinned planner caps: 64 calls; four derived planes; effect depth 3; 32 typed needs; eight candidates in generic search; four result lines; eight fresh result feet. Section search also applies an eight×32 candidate guard and shares needs/fresh-point counters. These distinct limits must not be collapsed into “32 IR nodes”. Semantic IR caps: 32 memory declarations, 50 statements, nesting depth eight.

The S3 F receipt reports six 3/4-sided section probes at 24–30 declarations and two hexagonal probes at 33/36, refused with `IR_MEMORY_BUDGET_EXCEEDED`. Composition inspections span 18–30 declarations. These are case measurements, not universal limits on polygon size. Zero duplicate planner calls coexist with 38 pre-dedup IR duplicate constructs across 38 plans; the final emission deduplicates operands. Do not relabel this as zero duplicates at every layer.

Closure compares exact section cycles up to rotation/reversal, checks cuts lie on the stated lateral segments, and refuses open/degenerate/out-of-edge boundaries. Shared namespaces and restricted base forms further limit topology even below the memory cap.

Next justified work is a source/contract gap chosen from independently reproduced failures, followed by a new independent evaluation. No geometry feature was added in 4A to improve these known corpora.
