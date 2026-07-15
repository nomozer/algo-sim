# M10-3D-PED — Semantically Meaningful 3D Flagship: TCP/IP Encapsulation / Decapsulation

**Date:** 2026-07-15
**Branch:** `m10-3d-ped`
**Status:** Design approved (with the delta-model adjustment below). Ready for implementation plan.

## 0. One-paragraph verdict

AlgoSim already proved *renderer sharing* (same config/state/timeline → 2D **or** 3D) with `network.packet_routing`. That PoC's Z axis only separates on-route from off-route nodes — layout, not concept. M10 adds a **second `network` module**, `network.protocol_encapsulation`, whose 3D depth axis carries a genuine meaning: **`meaning_of_z = protocol layer`**. Data descends the sender's TCP/IP stack (encapsulation), crosses the wire (transmission), and ascends the receiver's stack (decapsulation). The engine owns the PDU as renderer-neutral semantic truth; both a legible 2D renderer and a meaningful 3D renderer read the *same* state. Scope stays inside the thesis: one reusable deterministic capability, one offline public sample, mechanism-aligned prediction, deterministic feedback — **0 live AI calls**, no backend routing, no full network stack.

## 1. Why this topic justifies 3D

Encapsulation is intrinsically two-dimensional in *meaning*: information moves **along** a path (device → device) **and** through a **stack of layers** (down then up). A flat 2D diagram must overload one axis or use arrows to fake the second. Mapping the two meanings to two orthogonal spatial axes (X = direction, Z = layer depth) is the rare case where the third dimension encodes a real conceptual variable rather than decoration. This is the only curriculum-grounded 3D candidate (COVERAGE §8; SGK T12 B4 / 12CS B22–24: "đóng gói qua các tầng").

Allowed claim (COVERAGE §8): *"This simulation uses the third spatial dimension to encode protocol-layer depth, giving the 3D representation an explicit semantic role."* Banned claim: *"3D improves learning outcomes."*

## 2. Invariants this milestone must uphold

Carried forward (must not regress): R0 (LLM never owns runtime truth); #16 (3D is a renderer, not a domain — shared module/config/state/timeline/action/prediction; `visualMode` is presentation-only); #17 (history reopen is zero-AI); M7.FREEZE (engine state holds **no** pixel/coordinate/camera/layout data); PredictionCapability contract (pure, engine-graded, canonical never mutated).

New invariants introduced by M10 (each locked by a test):

1. **Transmission preserves PDU content.** A `transmit` step changes `side`/location but the PDU component list is byte-for-byte identical before and after.
2. **Encapsulation/decapsulation order is deterministic** for a given config (same steps every `init`).
3. **Delivered payload equals the original payload.** Final state's PDU equals the initial application PDU (`[DỮ LIỆU]`), same component id/label.
4. **LINK + FCS are added and removed atomically.** The Network Access transition's delta lists **both** `componentIds` in one step; there is no intermediate state with LINK but not FCS (or vice versa).
5. **Declared 3D meaning is truthful** (see §6): `network.packet_routing.threeD.role = "architectural_poc"`; `network.protocol_encapsulation.threeD.role = "pedagogical"` with `meaningOfZ` naming the protocol layer.

## 3. Identity & placement (no core edits)

- Module id: **`network.protocol_encapsulation`** (matches `^[a-z_]+\.[a-z0-9_]+$`), domain `network`, learner title **"Đóng gói dữ liệu qua các tầng TCP/IP"**.
- `interactionMode: "progressive"`, `supportedVisualModes: ["2d","3d"]`.
- New files (all under `frontend/src/simulations/domains/network/`):
  - `encap-model.ts` — engine (layers, PDU, step builder, prediction helpers).
  - `encap.ts` — `SimulationModule` (validateConfig, init, timeline, predict, threeD).
  - `encap-ui.tsx` — 2D renderer + Inspector.
  - `encap-ui3d.tsx` — 3D renderer (`React.lazy`, code-split like `ui3d.tsx`).
- `domains/network/index.ts` — export `makeEncapsulationModule()`; add one `registerSimulation(makeEncapsulationModule())` to `registerNetworkDomain()`; add `threeD` metadata to the existing packet-routing module.
- **No edits to** `pipeline.py`, `store.ts` internals, `registry.ts`, or `catalog.py` (backend). Store is untouched: the 2D-default load policy already does what we want.

## 4. Deterministic engine (`encap-model.ts`)

### 4.1 Fixed constants (engine, not config)

```
LayerId = "application" | "transport" | "internet" | "network_access"
LAYERS = ["application","transport","internet","network_access"]   // top → down
```

Layer display (Vietnamese): Application = "Tầng Ứng dụng", Transport = "Tầng Giao vận", Internet = "Tầng Liên mạng", Network Access = "Tầng Truy cập mạng".

Protocol info contributed per layer (fixed): Transport → TCP header; Internet → IP header; Network Access → LINK header **and** FCS trailer. Application produces the payload.

### 4.2 PDU — renderer-neutral semantic truth

```ts
type PduRole = "payload" | "header" | "trailer";
interface PduComponent {
  id: string;      // "data" | "tcp" | "ip" | "link" | "fcs"
  label: string;   // "DỮ LIỆU" | "TCP" | "IP" | "LINK" | "FCS"
  role: PduRole;
  layer: LayerId;  // layer that contributed it (attribution / colour)
}
```

PDU is an **ordered `PduComponent[]`** (a legible left-to-right segmented list, *not* nested shells):

```
Application:      [DỮ LIỆU]
Transport:        [TCP | DỮ LIỆU]                        → "đoạn TCP"
Internet:         [IP | TCP | DỮ LIỆU]                   → "gói IP"
Network Access:   [LINK | IP | TCP | DỮ LIỆU | FCS]      → "khung"   (LINK front, FCS back)
```

No coordinates, no camera — ordering is the only spatial fact, and it is semantic.

### 4.3 Step model (9 steps, precomputed in `init`)

```ts
type Phase =
  | "sender_application"
  | "sender_encapsulation"
  | "transmission"
  | "receiver_decapsulation"
  | "completed";

type Side = "sender" | "medium" | "receiver";

// Explicit engine event/delta (replaces singular changed/changeKind).
// Supports multiple components changing in ONE semantic step (LINK + FCS).
interface StepDelta {
  kind: "add" | "remove" | "transmit" | "deliver";
  layer: LayerId | null;      // null only for pure transmission
  componentIds: string[];     // e.g. ["link","fcs"] atomically
}

interface EncapStep {
  phase: Phase;
  side: Side;
  activeLayer: LayerId | null;
  pdu: PduComponent[];        // PDU AFTER this step
  delta: StepDelta;           // what changed to reach this step
  narration: string;          // Vietnamese, learner-facing
}
```

The canonical sequence:

| # | phase | side | activeLayer | delta.kind | componentIds | PDU after |
|---|-------|------|-------------|-----------|--------------|-----------|
| 0 | sender_application | sender | application | add | ["data"] | [DỮ LIỆU] |
| 1 | sender_encapsulation | sender | transport | add | ["tcp"] | [TCP,DỮ LIỆU] |
| 2 | sender_encapsulation | sender | internet | add | ["ip"] | [IP,TCP,DỮ LIỆU] |
| 3 | sender_encapsulation | sender | network_access | add | ["link","fcs"] | [LINK,IP,TCP,DỮ LIỆU,FCS] |
| 4 | transmission | medium | null | transmit | [] | [LINK,IP,TCP,DỮ LIỆU,FCS] *(unchanged)* |
| 5 | receiver_decapsulation | receiver | network_access | remove | ["link","fcs"] | [IP,TCP,DỮ LIỆU] |
| 6 | receiver_decapsulation | receiver | internet | remove | ["ip"] | [TCP,DỮ LIỆU] |
| 7 | receiver_decapsulation | receiver | transport | remove | ["tcp"] | [DỮ LIỆU] |
| 8 | completed | receiver | application | deliver | ["data"] | [DỮ LIỆU] |

`timeline`: `stepCount = steps.length`, `currentStep = cursor`, `goToStep` clamps `[0, len-1]` (pure, like network).

### 4.4 Config & validateConfig

```ts
interface EncapConfig {
  payloadLabel: string;       // display for the "DỮ LIỆU" segment; default "Dữ liệu ứng dụng"
  appProtocol: string | null; // CONTEXTUAL ONLY (e.g. "HTTP") — NOT modeled as PDU semantics
  notes: string | null;
}
```

`validateConfig`: object check; `payloadLabel` non-empty string (fallback to default); `appProtocol` string|null; `notes` string|null. There is nothing structurally variable — the honesty guarantee is that the engine, not the LLM/config, owns the layer/header model.

### 4.5 State

```ts
interface EncapState {
  payloadLabel: string;
  appProtocol: string | null;
  layers: LayerId[];
  steps: EncapStep[];
  cursor: number;
}
```

Renderer-neutral (locked by the coordinate-scan test: no `x/y/z/camera/mesh/position` keys).

`getExplainContext`: `{ simulation_id, phase, side, active_layer, pdu: [labels], current_step, total_steps, narration }` — serializable, no engine objects.

## 5. Prediction (reuses `PredictionCapability`)

The challenge is keyed **only** on `steps[cursor+1].delta.kind` (there is no next step at the last cursor → `null`):
- `kind === "add"` (next is a sender encapsulation step): ask **"Tầng kế tiếp sẽ THÊM phần thông tin nào?"**
- `kind === "remove"` (next is a receiver decapsulation step): ask **"Phần thông tin nào được GỠ tiếp theo?"**
- `kind === "transmit"` or `"deliver"`, or no next step → `null` (not a protocol-info decision point).

**Options are a FIXED set of three combined protocol pieces** — `{tcp}`, `{ip}`, `{link+fcs}` (the Network Access piece is one option covering both LINK and FCS) — presented in every add/remove question, so the choice is never trivially single-option. Answer ids encode the delta set (e.g. `"link+fcs"`, `"ip"`, `"tcp"`). Expected = `steps[cursor+1].delta.componentIds` as a set. `check(state, answerId)` compares the picked set against that expected set — pure, canonical never mutated. No next decision → `unsupported_to_verify`.

Deterministic feedback templates (real state values, no LLM):
- add correct: *"Chính xác. Tầng Giao vận thêm phần đầu TCP, nên dữ liệu ứng dụng trở thành đoạn TCP."*
- add incorrect: *"Chưa đúng. Phần đầu IP được thêm ở tầng Liên mạng, SAU khi tầng Giao vận đã tạo đoạn TCP."*
- remove (LINK+FCS): *"Ở máy nhận, tầng Truy cập mạng gỡ ĐỒNG THỜI phần đầu khung (LINK) và phần đuôi (FCS), để lộ gói IP bên trong."*

## 6. Honest 3D metadata (smallest contract addition)

Add an optional field to `SimulationModule` (`types.ts`):

```ts
interface ThreeDMeaning {
  role: "architectural_poc" | "pedagogical";
  meaningOfZ: string;   // what the depth axis encodes, in Vietnamese
}
// SimulationModule.threeD?: ThreeDMeaning
```

- `network.packet_routing` → `{ role: "architectural_poc", meaningOfZ: "phân tách nút trên/ngoài tuyến (bố cục), không mang nghĩa khái niệm" }`.
- `network.protocol_encapsulation` → `{ role: "pedagogical", meaningOfZ: "độ sâu tầng giao thức (Application → Network Access)" }`.

The 3D renderer surfaces `meaningOfZ` as a small on-stage caption so the semantic role is legible without rotating the camera. Locked by tests (invariant #5). Modules without 3D omit the field (safe default).

## 7. 2D renderer (`encap-ui.tsx`) — baseline / accessibility

- Two labeled stacks side by side: **MÁY GỬI** (sender) | **MÁY NHẬN** (receiver), each four layer rows, Application at top → Network Access at bottom.
- The current PDU is a **row of labeled segments** (payload / header / trailer visually distinct by role colour), drawn at the active layer on the active side; during `transmission` it rides a "đường truyền" band between the two stacks.
- Segments changed by the current step's delta are highlighted; narration bar below. Layout is renderer-owned SVG; reads `state` only. Prefer legibility (clear segment labels) over spectacle.
- `Inspector`: current phase, side, active layer, PDU composition (labels), step N/total.

## 8. 3D renderer (`encap-ui3d.tsx`) — meaningful depth

- **X = communication direction**: sender at −X, medium at X≈0, receiver at +X.
- **Z = protocol layer**: Application z=0, Transport z=−4, Internet z=−8, Network Access z=−12. This is the claim.
- Four labeled semantic layer slabs (translucent planes) at each Z. The PDU is a group of **segmented boxes** (order & identity from `state.pdu`; colour by role) — descends in Z through sender layers, crosses in X on the wire at the Network-Access depth, ascends in Z through receiver layers.
- Restrained lerp animation; auto camera framing that shows both axes at rest (mechanism readable without orbiting); OrbitControls rotate+zoom, pan locked; reset-view button (camera only, never the sim); WebGL fallback message pointing to 2D. Small caption from `threeD.meaningOfZ`.
- Pure exported `layerDepth(layer)→z` and `sideX(side)→x` (deterministic; tested). **No PDU/step logic duplicated** — the renderer imports engine truth; renderer owns only coordinates/camera/mesh (ref/closure, never store/state).

## 9. Catalog, sample, preview, history

- One **public** `OfflineSample` in `data/sim-samples.ts`:
  ```
  id: "network-encapsulation"
  envelope: { simulation_id: "network.protocol_encapsulation", domain: "network",
              visual_mode: "2d", title: "Dữ liệu được đóng gói qua các tầng TCP/IP như thế nào?",
              config: { payloadLabel: "Dữ liệu ứng dụng", appProtocol: "HTTP", notes: null } }
  // visibility omitted → public
  ```
- Featured on Home starters (add `"network.protocol_encapsulation"` to `STARTER_SIM_IDS`) + appears in Library.
- `SamplePreview`: new `kind: "network-encapsulation"` (static segmented-stack SVG) + `previewKindOf("network.protocol_encapsulation") → "network-encapsulation"`.
- History reopen (cursor + visualMode, zero-AI) works via the existing envelope path — no new code; add a targeted acceptance test only.

## 10. Test plan (offline, 0 AI) & docs

**Engine/prediction** (`encap.test.ts`): initial PDU = `[DỮ LIỆU]`; each add step composes the expected PDU; step 3 delta = `["link","fcs"]` atomically; transmission preserves PDU identity (invariant #1); decapsulation removes outermost-first, LINK+FCS atomically (invariant #4); delivered payload equals original (invariant #3); determinism (invariant #2); no coordinate keys in state; prediction challenge only at decision points; expected derived from next `delta`; correct/incorrect pure; canonical never mutated.

**Renderer/metadata** (`encap-render3d.test.tsx`): 2D reads `state.pdu`; 3D reads the *same* `state.pdu`; `layerDepth` monotonic (Application 0 → Network Access most negative) and deterministic; `sideX` sender<medium<receiver; no PDU recomputation in 3D; store mode-switch preserves state+cursor; WebGL fallback; `threeD` metadata truthful for both network modules (invariant #5); no banned Unicode/emoji icons (hygiene guard).

**Catalog/history**: update `catalog.test.tsx` counts (public 12→13, offline 16→17), `previewKindOf` + SVG enumeration, starter list; new public sample present; zero-AI reopen restores cursor + visualMode.

**Regression + gates**: full `pytest` (expect 289), full `vitest` (new count reported honestly), `tsc -b` clean, `vite build` clean, `npm run audit:layout` 4/4 (fault-injection-checked). M8 / M9-S1 / M9-UX1 / M9-UX2 suites green.

**Docs**: `CURRENT_STATE.md` (M10 entry, honest counts), `COVERAGE.md §8` (first pedagogical semantic-depth 3D; packet_routing reclassified PoC), `ARCHITECTURE_MAP.md` (invariant #18 = declared-3D-meaning honesty; add module to the ownership table + #16 note), `CODE_INDEX.md` (new files).

## 11. Direct 3D interaction — DEFERRED (honest)

Clicking a 3D layer slab to answer the prediction would require threading a prediction callback into `WorkspaceProps` (contract change) or the renderer reaching into the store (breaks "renderer reads props only"). Per spec §14 this is explicitly deferrable and not a blocker. The shared `PredictionBar` (outside the renderer, already renderer-independent) remains the only answer path. Reported as deferred, not implemented.

## 12. Scope intentionally NOT added

No backend AI routing (classify/simulate/prompt/schema untouched); no direct 3D click; no TCP handshake / seq / ack / retransmission / congestion control; no UDP branching; no IP fragmentation; no DNS/HTTP internals; no router forwarding, packet capture, live network, Packet Tracer / Wireshark features; no scoring; no teacher mode; no new 3D domains; no AI-generated module code. `practice_activity` remains **PARTIAL / NOT IMPLEMENTED**. The model is a *pedagogical model of encapsulation*, not a complete stack emulator.

## 13. Honest limitations

- Reachable from the offline catalog only (no typed-prompt routing in v1).
- Single canonical transport (TCP); no protocol branching.
- One payload; the model shows structure, not real byte contents.
- 3D "recommended" status is deferred to manual acceptance — 2D remains the load default; 3D is opt-in via the toggle. No claim that 3D teaches better than 2D.
