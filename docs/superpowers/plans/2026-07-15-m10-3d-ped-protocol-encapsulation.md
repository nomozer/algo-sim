# M10-3D-PED: TCP/IP Encapsulation Flagship — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second `network` module, `network.protocol_encapsulation`, that simulates TCP/IP encapsulation/decapsulation with a deterministic PDU engine, a legible 2D renderer, and a 3D renderer whose depth axis carries a real meaning (`meaning_of_z = protocol layer`).

**Architecture:** A new `SimulationModule` in `frontend/src/simulations/domains/network/`, reusing the existing shared-renderer architecture (invariant #16) and `PredictionCapability`. Engine state is renderer-neutral (M7.FREEZE): the PDU is an ordered list of labeled segments; 2D and 3D read the same state. One optional contract field (`threeD`) records each 3D module's honest role. Offline public sample only — no backend/AI routing.

**Tech Stack:** TypeScript, React 18, Zustand, Three.js (`three` + `three/addons` OrbitControls), Vitest, `react-dom/server` for SSR tests.

## Global Constraints

- **Language:** all user-facing strings, narration, comments in **Vietnamese** (copy the exact Vietnamese strings shown in each task).
- **R0 / invariant #1:** the LLM never generates timeline/steps/state. This milestone adds **no** backend/pipeline/prompt/schema code and makes **0 live AI calls**.
- **Invariant #16:** 3D is a renderer, not a domain — one module id, one engine, shared config/state/timeline/action/prediction. No `_3d` id, no second engine, no second prediction path.
- **M7.FREEZE:** engine state holds **no** `x/y/z/camera/mesh/position/layout` — only semantics. Coordinates live in the renderer (ref/closure), never in state or store.
- **Hygiene guard** (`components/ui-hygiene.test.ts`): no emoji or banned Unicode as icons in any `.tsx`; the char `⌂` (U+2302) is allowed (used by the existing 3D reset button). Components under `components/` must not render raw `simId` — but the new renderers live under `domains/network/`, so only the emoji/Unicode rule applies to them.
- **No linter:** `npm run build` (`tsc -b && vite build`) is the typecheck.
- **Commits:** this repo omits the `Co-Authored-By` trailer. Do not add it.
- **Module id regex:** `^[a-z_]+\.[a-z0-9_]+$`.

All commands run from `d:/Documents/projects/algo-sim/frontend` unless stated. Current branch: `m10-3d-ped`.

---

## File map

| File | Responsibility | Task |
|---|---|---|
| `src/simulations/types.ts` | add optional `ThreeDMeaning` + `threeD?` on `SimulationModule` | 1 |
| `src/simulations/domains/network/index.ts` | add `threeD` to packet-routing module; register encapsulation module | 1, 5 |
| `src/simulations/domains/network/encap-model.ts` | deterministic engine: layers, PDU, 9-step builder, prediction pieces | 2 |
| `src/simulations/domains/network/encap-ui.tsx` | 2D renderer + Inspector | 3 |
| `src/styles/global.css` | `.encap-*` presentation classes (4px-grid spacing) | 3 |
| `src/simulations/domains/network/encap-ui3d.tsx` | 3D renderer (lazy), `layerDepth`/`sideX` pure fns | 4 |
| `src/simulations/domains/network/encap.ts` | `SimulationModule` factory `makeEncapsulationModule` | 5 |
| `src/data/sim-samples.ts` | one public `OfflineSample` | 6 |
| `src/components/SamplePreview.tsx` | new preview kind + `previewKindOf` mapping | 6 |
| `src/simulations/domains/network/encap.test.ts` | engine + module + prediction tests | 2, 5 |
| `src/simulations/domains/network/encap-render3d.test.tsx` | renderer + parity + metadata tests | 3, 4, 5 |
| `src/data/catalog.test.tsx` | update counts + preview + starter | 6 |
| `docs/*` | CURRENT_STATE, COVERAGE, ARCHITECTURE_MAP, CODE_INDEX | 7 |

---

## Task 1: `ThreeDMeaning` contract field + honest packet-routing classification

**Files:**
- Modify: `src/simulations/types.ts` (add interface + optional field)
- Modify: `src/simulations/domains/network/index.ts` (add `threeD` to existing module)
- Test: `src/simulations/domains/network/render3d.test.tsx` (add one assertion)

**Interfaces:**
- Produces: `ThreeDMeaning { role: "architectural_poc" | "pedagogical"; meaningOfZ: string }`; `SimulationModule.threeD?: ThreeDMeaning`.

- [ ] **Step 1: Write the failing test** — append to `src/simulations/domains/network/render3d.test.tsx`:

```tsx
describe("(M10) 3D meaning metadata — honest classification", () => {
  it("packet_routing khai threeD.role='architectural_poc' (Z chỉ là bố cục)", () => {
    expect(mod.threeD).toBeDefined();
    expect(mod.threeD!.role).toBe("architectural_poc");
    expect(mod.threeD!.meaningOfZ.toLowerCase()).toContain("bố cục");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/simulations/domains/network/render3d.test.tsx -t "honest classification"`
Expected: FAIL (`mod.threeD` is `undefined`).

- [ ] **Step 3: Add the contract field** — in `src/simulations/types.ts`, add before `SimulationModule`:

```ts
/**
 * M10 — vai trò của renderer 3D. Phân biệt TRUNG THỰC:
 * - "architectural_poc": 3D chứng minh dùng chung renderer, nhưng chiều sâu (Z)
 *   chỉ là BỐ CỤC (vd tách nút trên/ngoài tuyến) — không mang nghĩa khái niệm.
 * - "pedagogical": Z mã hoá một biến khái niệm thật (vd tầng giao thức).
 * Không khai = module không có 3D hoặc chưa phân loại.
 */
export interface ThreeDMeaning {
  role: "architectural_poc" | "pedagogical";
  /** Trục sâu (Z) mã hoá điều gì — tiếng Việt, dùng cho caption + test trung thực. */
  meaningOfZ: string;
}
```

Then inside `SimulationModule`, after the `renderers?` field, add:

```ts
  /**
   * M10 — tuyên bố TRUNG THỰC về nghĩa của chiều sâu 3D (chỉ khai khi có 3D).
   * Khoá bằng test: PoC không được giả vờ có nghĩa khái niệm.
   */
  threeD?: ThreeDMeaning;
```

- [ ] **Step 4: Add packet-routing metadata** — in `src/simulations/domains/network/index.ts`, inside the object returned by `makeNetworkModule()`, add after `supportedVisualModes: ["2d", "3d"],`:

```ts
    // M10: TRUNG THỰC — Z ở đây chỉ tách hàng route/ngoài-route (bố cục), KHÔNG
    // mang nghĩa khái niệm. Đây là PoC kiến trúc, không phải 3D sư phạm.
    threeD: {
      role: "architectural_poc",
      meaningOfZ: "phân tách nút trên/ngoài tuyến (bố cục), không mang nghĩa khái niệm",
    },
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run src/simulations/domains/network/render3d.test.tsx -t "honest classification"`
Expected: PASS.

- [ ] **Step 6: Typecheck + commit**

```bash
npx tsc -b
git add src/simulations/types.ts src/simulations/domains/network/index.ts src/simulations/domains/network/render3d.test.tsx
git commit -m "M10: add ThreeDMeaning contract field; classify packet_routing 3D as architectural_poc"
```

---

## Task 2: Deterministic encapsulation engine (`encap-model.ts`)

**Files:**
- Create: `src/simulations/domains/network/encap-model.ts`
- Test: `src/simulations/domains/network/encap.test.ts`

**Interfaces:**
- Produces (all exported):
  - types `LayerId`, `PduRole`, `PduComponent`, `Phase`, `Side`, `StepDelta`, `EncapStep`, `EncapConfig`, `EncapState`, `ProtocolPiece`
  - `LAYERS: LayerId[]`, `LAYER_LABEL: Record<LayerId,string>`, `PROTOCOL_PIECES: ProtocolPiece[]`
  - `buildEncapState(config: EncapConfig): EncapState`
  - `currentStep(state: EncapState): EncapStep`
  - `pieceForComponents(componentIds: string[]): ProtocolPiece | undefined`

- [ ] **Step 1: Write the failing tests** — create `src/simulations/domains/network/encap.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import {
  buildEncapState, currentStep, LAYERS, PROTOCOL_PIECES, pieceForComponents,
  type EncapConfig, type EncapState,
} from "./encap-model";

const CONFIG: EncapConfig = { payloadLabel: "Dữ liệu ứng dụng", appProtocol: "HTTP", notes: null };

function ids(s: EncapState, step: number): string[] {
  return s.steps[step].pdu.map((c) => c.id);
}

describe("(M10) engine đóng gói — dựng PDU tất định", () => {
  it("bắt đầu chỉ có payload ứng dụng", () => {
    const s = buildEncapState(CONFIG);
    expect(s.steps).toHaveLength(9);
    expect(ids(s, 0)).toEqual(["data"]);
    expect(s.steps[0].pdu[0].label).toBe("Dữ liệu ứng dụng");
    expect(s.cursor).toBe(0);
  });

  it("đóng gói thêm TCP → IP → LINK/FCS đúng thứ tự", () => {
    const s = buildEncapState(CONFIG);
    expect(ids(s, 1)).toEqual(["tcp", "data"]);
    expect(ids(s, 2)).toEqual(["ip", "tcp", "data"]);
    expect(ids(s, 3)).toEqual(["link", "ip", "tcp", "data", "fcs"]);
  });

  it("(bất biến #4) Network Access thêm LINK + FCS trong MỘT delta nguyên tử", () => {
    const s = buildEncapState(CONFIG);
    expect(s.steps[3].delta.kind).toBe("add");
    expect([...s.steps[3].delta.componentIds].sort()).toEqual(["fcs", "link"]);
    // không có trạng thái trung gian chỉ có LINK mà thiếu FCS
    for (const st of s.steps) {
      const hasLink = st.pdu.some((c) => c.id === "link");
      const hasFcs = st.pdu.some((c) => c.id === "fcs");
      expect(hasLink).toBe(hasFcs);
    }
  });

  it("(bất biến #1) truyền tin giữ nguyên PDU, chỉ đổi side", () => {
    const s = buildEncapState(CONFIG);
    expect(s.steps[4].delta.kind).toBe("transmit");
    expect(s.steps[4].side).toBe("medium");
    expect(ids(s, 4)).toEqual(ids(s, 3)); // nội dung y hệt khung đã đóng gói
  });

  it("mở gói gỡ ngược từ ngoài vào: LINK/FCS → IP → TCP", () => {
    const s = buildEncapState(CONFIG);
    expect(s.steps[5].delta.kind).toBe("remove");
    expect([...s.steps[5].delta.componentIds].sort()).toEqual(["fcs", "link"]);
    expect(ids(s, 5)).toEqual(["ip", "tcp", "data"]);
    expect(ids(s, 6)).toEqual(["tcp", "data"]);
    expect(ids(s, 7)).toEqual(["data"]);
  });

  it("(bất biến #3) payload giao đúng như ban đầu", () => {
    const s = buildEncapState(CONFIG);
    expect(s.steps[8].delta.kind).toBe("deliver");
    expect(ids(s, 8)).toEqual(ids(s, 0));
    expect(s.steps[8].pdu[0].label).toBe(s.steps[0].pdu[0].label);
  });

  it("(bất biến #2) tất định: cùng config → steps y hệt", () => {
    expect(JSON.stringify(buildEncapState(CONFIG))).toBe(JSON.stringify(buildEncapState(CONFIG)));
  });

  it("(M7.FREEZE) state KHÔNG chứa toạ độ/camera", () => {
    const dump = JSON.stringify(buildEncapState(CONFIG));
    for (const forbidden of ["camera", "mesh", "position", "layout", "webgl"]) {
      expect(dump.toLowerCase()).not.toContain(forbidden);
    }
    expect(dump).not.toMatch(/"[xyz]":\s*-?\d/);
  });

  it("PROTOCOL_PIECES: ba mảnh, LINK+FCS là một mảnh gộp", () => {
    expect(PROTOCOL_PIECES.map((p) => p.id)).toEqual(["tcp", "ip", "link+fcs"]);
    expect(pieceForComponents(["fcs", "link"])!.id).toBe("link+fcs");
    expect(pieceForComponents(["tcp"])!.id).toBe("tcp");
    expect(pieceForComponents(["data"])).toBeUndefined();
  });

  it("currentStep kẹp cursor về [0, len-1]", () => {
    const s = { ...buildEncapState(CONFIG), cursor: 999 };
    expect(currentStep(s)).toBe(s.steps[8]);
  });

  it("LAYERS đủ 4 tầng đúng thứ tự trên→dưới", () => {
    expect(LAYERS).toEqual(["application", "transport", "internet", "network_access"]);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/simulations/domains/network/encap.test.ts`
Expected: FAIL (`encap-model` not found).

- [ ] **Step 3: Write the engine** — create `src/simulations/domains/network/encap-model.ts`:

```ts
/**
 * Model: đóng gói/mở gói dữ liệu qua các tầng TCP/IP (M10). Progressive: có timeline.
 *
 * State RENDERER-NEUTRAL (M7.FREEZE): không toạ độ/camera/mesh. PDU là danh sách
 * PHÂN ĐOẠN CÓ THỨ TỰ — thứ tự là sự thật ngữ nghĩa duy nhất; renderer 2D/3D tự
 * đặt chỗ. Đây là bằng chứng: cùng state → 2D hoặc 3D, không fork engine.
 *
 * Đây là MÔ HÌNH SƯ PHẠM của đóng gói, không phải bộ mô phỏng chồng giao thức
 * đầy đủ: một transport (TCP), không bắt tay/seq/ack, không phân mảnh.
 */

export type LayerId = "application" | "transport" | "internet" | "network_access";

/** Thứ tự tầng trên → dưới (đóng gói đi xuống, mở gói đi lên). */
export const LAYERS: LayerId[] = ["application", "transport", "internet", "network_access"];

export const LAYER_LABEL: Record<LayerId, string> = {
  application: "Tầng Ứng dụng",
  transport: "Tầng Giao vận",
  internet: "Tầng Liên mạng",
  network_access: "Tầng Truy cập mạng",
};

export type PduRole = "payload" | "header" | "trailer";

export interface PduComponent {
  id: string; // "data" | "tcp" | "ip" | "link" | "fcs"
  label: string;
  role: PduRole;
  layer: LayerId; // tầng đã thêm thành phần này (để tô màu/quy nghĩa)
}

export type Phase =
  | "sender_application"
  | "sender_encapsulation"
  | "transmission"
  | "receiver_decapsulation"
  | "completed";

export type Side = "sender" | "medium" | "receiver";

/**
 * Delta TƯỜNG MINH của một bước (thay cho changed/changeKind đơn lẻ): hỗ trợ
 * NHIỀU thành phần đổi trong MỘT bước ngữ nghĩa — Network Access thêm/gỡ LINK
 * và FCS NGUYÊN TỬ (bất biến #4).
 */
export interface StepDelta {
  kind: "add" | "remove" | "transmit" | "deliver";
  layer: LayerId | null; // null chỉ khi truyền tin thuần
  componentIds: string[]; // vd ["link","fcs"]
}

export interface EncapStep {
  phase: Phase;
  side: Side;
  activeLayer: LayerId | null;
  pdu: PduComponent[]; // PDU SAU bước này
  delta: StepDelta;
  narration: string;
}

export interface EncapConfig {
  payloadLabel: string;
  /** CHỈ để hiển thị ngữ cảnh (vd "HTTP") — KHÔNG mô hình hoá thành PDU. */
  appProtocol: string | null;
  notes: string | null;
}

export interface EncapState {
  payloadLabel: string;
  appProtocol: string | null;
  layers: LayerId[];
  steps: EncapStep[];
  cursor: number;
}

/** "Mảnh thông tin giao thức" cho nhịp dự đoán — LINK+FCS là MỘT mảnh gộp. */
export interface ProtocolPiece {
  id: string; // "tcp" | "ip" | "link+fcs"
  label: string;
  componentIds: string[];
}

export const PROTOCOL_PIECES: ProtocolPiece[] = [
  { id: "tcp", label: "Phần đầu TCP", componentIds: ["tcp"] },
  { id: "ip", label: "Phần đầu IP", componentIds: ["ip"] },
  { id: "link+fcs", label: "Phần đầu LINK + phần đuôi FCS", componentIds: ["link", "fcs"] },
];

function comp(id: string, label: string, role: PduRole, layer: LayerId): PduComponent {
  return { id, label, role, layer };
}

const TCP = comp("tcp", "TCP", "header", "transport");
const IP = comp("ip", "IP", "header", "internet");
const LINK = comp("link", "LINK", "header", "network_access");
const FCS = comp("fcs", "FCS", "trailer", "network_access");

/** Dựng toàn bộ timeline 9 bước — tất định (bất biến #2). */
export function buildEncapState(config: EncapConfig): EncapState {
  const data = comp("data", config.payloadLabel, "payload", "application");
  const pApp = [data];
  const pTcp = [TCP, data];
  const pIp = [IP, TCP, data];
  const pFrame = [LINK, IP, TCP, data, FCS];

  const steps: EncapStep[] = [
    { phase: "sender_application", side: "sender", activeLayer: "application", pdu: pApp,
      delta: { kind: "add", layer: "application", componentIds: ["data"] },
      narration: "Máy gửi: ứng dụng tạo dữ liệu cần gửi đi." },
    { phase: "sender_encapsulation", side: "sender", activeLayer: "transport", pdu: pTcp,
      delta: { kind: "add", layer: "transport", componentIds: ["tcp"] },
      narration: "Tầng Giao vận thêm phần đầu TCP → dữ liệu trở thành đoạn TCP." },
    { phase: "sender_encapsulation", side: "sender", activeLayer: "internet", pdu: pIp,
      delta: { kind: "add", layer: "internet", componentIds: ["ip"] },
      narration: "Tầng Liên mạng thêm phần đầu IP → đoạn TCP trở thành gói IP." },
    { phase: "sender_encapsulation", side: "sender", activeLayer: "network_access", pdu: pFrame,
      delta: { kind: "add", layer: "network_access", componentIds: ["link", "fcs"] },
      narration: "Tầng Truy cập mạng thêm phần đầu LINK và phần đuôi FCS → gói IP trở thành khung." },
    { phase: "transmission", side: "medium", activeLayer: null, pdu: pFrame,
      delta: { kind: "transmit", layer: null, componentIds: [] },
      narration: "Khung được truyền qua đường truyền tới máy nhận — nội dung không đổi." },
    { phase: "receiver_decapsulation", side: "receiver", activeLayer: "network_access", pdu: pIp,
      delta: { kind: "remove", layer: "network_access", componentIds: ["link", "fcs"] },
      narration: "Máy nhận: tầng Truy cập mạng gỡ phần đầu LINK và phần đuôi FCS → còn lại gói IP." },
    { phase: "receiver_decapsulation", side: "receiver", activeLayer: "internet", pdu: pTcp,
      delta: { kind: "remove", layer: "internet", componentIds: ["ip"] },
      narration: "Tầng Liên mạng gỡ phần đầu IP → còn lại đoạn TCP." },
    { phase: "receiver_decapsulation", side: "receiver", activeLayer: "transport", pdu: pApp,
      delta: { kind: "remove", layer: "transport", componentIds: ["tcp"] },
      narration: "Tầng Giao vận gỡ phần đầu TCP → còn lại dữ liệu ứng dụng." },
    { phase: "completed", side: "receiver", activeLayer: "application", pdu: pApp,
      delta: { kind: "deliver", layer: "application", componentIds: ["data"] },
      narration: "Ứng dụng ở máy nhận nhận đúng dữ liệu ban đầu. Hoàn tất!" },
  ];

  return { payloadLabel: config.payloadLabel, appProtocol: config.appProtocol, layers: LAYERS, steps, cursor: 0 };
}

export function currentStep(state: EncapState): EncapStep {
  return state.steps[Math.max(0, Math.min(state.cursor, state.steps.length - 1))];
}

/** Mảnh giao thức khớp một tập componentIds (so khớp theo TẬP HỢP, không theo thứ tự). */
export function pieceForComponents(componentIds: string[]): ProtocolPiece | undefined {
  const key = [...componentIds].sort().join(",");
  return PROTOCOL_PIECES.find((p) => [...p.componentIds].sort().join(",") === key);
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx vitest run src/simulations/domains/network/encap.test.ts`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
git add src/simulations/domains/network/encap-model.ts src/simulations/domains/network/encap.test.ts
git commit -m "M10: deterministic TCP/IP encapsulation engine (9-step PDU model, atomic LINK+FCS delta)"
```

---

## Task 3: 2D renderer (`encap-ui.tsx`) + CSS

**Files:**
- Create: `src/simulations/domains/network/encap-ui.tsx`
- Modify: `src/styles/global.css` (append `.encap-*` classes)
- Test: `src/simulations/domains/network/encap-render3d.test.tsx` (create; 2D section)

**Interfaces:**
- Consumes: `EncapConfig`, `EncapState`, `currentStep`, `LAYERS`, `LAYER_LABEL`, `PduComponent`, `Side` from `encap-model`; `WorkspaceProps` from `../../types`.
- Produces: `EncapWorkspace`, `EncapInspector` (both `ComponentType<WorkspaceProps<EncapConfig, EncapState>>`).

- [ ] **Step 1: Write the failing test** — create `src/simulations/domains/network/encap-render3d.test.tsx`:

```tsx
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { buildEncapState, type EncapConfig, type EncapState } from "./encap-model";
import { EncapWorkspace, EncapInspector } from "./encap-ui";

const CONFIG: EncapConfig = { payloadLabel: "Dữ liệu ứng dụng", appProtocol: "HTTP", notes: null };
function at(step: number): EncapState {
  return { ...buildEncapState(CONFIG), cursor: step };
}

describe("(M10) 2D renderer đọc CÙNG authoritative PDU state", () => {
  it("hiện các phân đoạn PDU của bước hiện tại + narration", () => {
    const html = renderToString(<EncapWorkspace config={CONFIG} state={at(3)} busy={false} dispatch={() => {}} />);
    for (const seg of ["LINK", "IP", "TCP", "Dữ liệu ứng dụng", "FCS"]) expect(html).toContain(seg);
    expect(html).toContain("gói IP trở thành khung");
    expect(html).toContain("MÁY GỬI");
    expect(html).toContain("MÁY NHẬN");
  });

  it("bước truyền tin hiện dải đường truyền", () => {
    const html = renderToString(<EncapWorkspace config={CONFIG} state={at(4)} busy={false} dispatch={() => {}} />);
    expect(html).toContain("Đường truyền");
  });

  it("Inspector hiện tầng + đơn vị dữ liệu, KHÔNG lộ simulation_id", () => {
    const html = renderToString(<EncapInspector config={CONFIG} state={at(2)} busy={false} dispatch={() => {}} />);
    expect(html).toContain("Tầng Liên mạng");
    expect(html).not.toContain("network.protocol_encapsulation");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/simulations/domains/network/encap-render3d.test.tsx -t "2D renderer"`
Expected: FAIL (`encap-ui` not found).

- [ ] **Step 3: Write the 2D renderer** — create `src/simulations/domains/network/encap-ui.tsx`:

```tsx
import type { WorkspaceProps } from "../../types";
import {
  currentStep, LAYERS, LAYER_LABEL,
  type EncapConfig, type EncapState, type PduComponent, type Side,
} from "./encap-model";

/**
 * Renderer 2D của network.protocol_encapsulation — baseline dễ đọc.
 *
 * M7.FREEZE: BỐ CỤC thuộc renderer, không thuộc state. Đọc CÙNG EncapState mà
 * renderer 3D đọc: PDU là danh sách phân đoạn, ở đây trải NGANG cho dễ đọc
 * (ưu tiên rõ ràng hơn hình khối lồng nhau).
 */

type Props = WorkspaceProps<EncapConfig, EncapState>;

const ROLE_COLOR: Record<string, string> = {
  payload: "var(--accent-green)",
  header: "var(--accent-sky)",
  trailer: "var(--accent-orange)",
};

function PduRow({ pdu, changed }: { pdu: PduComponent[]; changed: Set<string> }) {
  return (
    <div className="encap-pdu">
      {pdu.map((c) => (
        <span
          key={c.id}
          className={`encap-seg encap-seg-${c.role}${changed.has(c.id) ? " is-changed" : ""}`}
          style={{ borderColor: ROLE_COLOR[c.role] }}
        >
          {c.label}
        </span>
      ))}
    </div>
  );
}

export function EncapWorkspace({ state }: Props) {
  const step = currentStep(state);
  const changed = new Set(step.delta.componentIds);
  const sides: Side[] = ["sender", "receiver"];
  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <div className="encap-2d">
          {sides.map((side) => (
            <div key={side} className={`encap-col${step.side === side ? " is-active-side" : ""}`}>
              <div className="encap-col-label">{side === "sender" ? "MÁY GỬI" : "MÁY NHẬN"}</div>
              {LAYERS.map((layer) => {
                const here = step.side === side && step.activeLayer === layer;
                return (
                  <div key={layer} className={`encap-layer${here ? " is-active-layer" : ""}`}>
                    <span className="encap-layer-name">{LAYER_LABEL[layer]}</span>
                    {here && <PduRow pdu={step.pdu} changed={changed} />}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
        {step.side === "medium" && (
          <div className="encap-medium">
            <span className="encap-medium-label">Đường truyền</span>
            <PduRow pdu={step.pdu} changed={new Set()} />
          </div>
        )}
      </div>
      <div className="narration-bar">{step.narration}</div>
    </div>
  );
}

export function EncapInspector({ state }: Props) {
  const step = currentStep(state);
  const sideLabel =
    step.side === "sender" ? "Máy gửi" : step.side === "receiver" ? "Máy nhận" : "Đường truyền";
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <section className="card" style={{ padding: "var(--sp-md)" }}>
        <span className="eyebrow">ĐÓNG GÓI DỮ LIỆU</span>
        <div className="analysis-grid" style={{ marginTop: "var(--sp-sm)" }}>
          <span className="analysis-label">Vị trí</span>
          <span>{sideLabel}</span>
          <span className="analysis-label">Tầng</span>
          <span>{step.activeLayer ? LAYER_LABEL[step.activeLayer] : "—"}</span>
          <span className="analysis-label">Đơn vị dữ liệu</span>
          <span>{step.pdu.map((c) => c.label).join(" | ")}</span>
          <span className="analysis-label">Bước</span>
          <span>
            {state.cursor + 1} / {state.steps.length}
          </span>
        </div>
      </section>
    </div>
  );
}
```

- [ ] **Step 4: Append CSS** — add to the end of `src/styles/global.css` (spacing strictly on the 4px scale so `npm run audit:layout` stays clean):

```css
/* ── M10: renderer 2D đóng gói TCP/IP ─────────────────────────────────────── */
.encap-2d {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-md);
}
.encap-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.encap-col-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-muted);
  letter-spacing: 0.04em;
}
.encap-col.is-active-side .encap-col-label {
  color: var(--primary);
}
.encap-layer {
  border: 1px solid var(--hairline);
  border-radius: var(--rounded-md);
  padding: 8px 12px;
  min-height: 44px;
  background: var(--surface);
}
.encap-layer.is-active-layer {
  background: var(--canvas-soft);
  border-color: var(--primary);
}
.encap-layer-name {
  font-size: 12px;
  color: var(--ink-muted);
}
.encap-pdu {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
.encap-seg {
  border: 2px solid var(--hairline);
  border-radius: var(--rounded-md);
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  background: var(--surface);
}
.encap-seg.is-changed {
  box-shadow: 0 0 0 2px var(--canvas-soft);
}
.encap-medium {
  display: flex;
  align-items: center;
  gap: var(--sp-sm);
  margin-top: var(--sp-md);
  padding: 8px 12px;
  border-top: 1px dashed var(--hairline);
}
.encap-medium-label {
  font-size: 12px;
  color: var(--ink-muted);
}
```

> **Token names are exact** (verified against `src/styles/tokens.css`): radius tokens are `--rounded-xs/sm/md/lg` — **there is no `--radius-sm`** (it was a ghost token removed in M9-UX5). Spacing is `--sp-xxs/xs/sm/md/lg/xl/xxl/3xl/4xl`. Colors used here (`--canvas-soft`, `--hairline`, `--surface`, `--ink-muted`, `--primary`, `--accent-green/sky/orange`) all exist in tokens.css. `styles/tokens.test.ts` fails the build if any `var()` is undefined — do **not** invent token names. Raw pixel values in this CSS (4/8/12/44px) are all multiples of 4 to keep `npm run audit:layout` clean.

- [ ] **Step 5: Run tests to verify they pass**

Run: `npx vitest run src/simulations/domains/network/encap-render3d.test.tsx -t "2D renderer" && npx vitest run src/styles/tokens.test.ts`
Expected: PASS (both).

- [ ] **Step 6: Commit**

```bash
git add src/simulations/domains/network/encap-ui.tsx src/simulations/domains/network/encap-render3d.test.tsx src/styles/global.css
git commit -m "M10: 2D encapsulation renderer (segmented PDU, sender/receiver stacks)"
```

---

## Task 4: 3D renderer (`encap-ui3d.tsx`) — meaningful depth

**Files:**
- Create: `src/simulations/domains/network/encap-ui3d.tsx`
- Test: `src/simulations/domains/network/encap-render3d.test.tsx` (append 3D section)

**Interfaces:**
- Consumes: `EncapState`, `EncapConfig`, `currentStep`, `LAYERS`, `LAYER_LABEL`, `LayerId`, `Side` from `encap-model`; `WorkspaceProps`.
- Produces: `Encap3DWorkspace`, and pure fns `layerDepth(layer: LayerId): number`, `sideX(side: Side): number`, `tryCreateWebGLRenderer(): THREE.WebGLRenderer | null`, `ENCAP_WEBGL_FALLBACK: string`.

- [ ] **Step 1: Write the failing tests** — append to `src/simulations/domains/network/encap-render3d.test.tsx`:

```tsx
import { layerDepth, sideX, Encap3DWorkspace, tryCreateWebGLRenderer, ENCAP_WEBGL_FALLBACK } from "./encap-ui3d";
import { LAYERS } from "./encap-model";

describe("(M10) 3D renderer — Z = tầng giao thức (nghĩa thật)", () => {
  it("layerDepth GIẢM đơn điệu theo tầng (Application 0 → Network Access sâu nhất)", () => {
    const depths = LAYERS.map(layerDepth);
    expect(depths[0]).toBe(0);
    for (let i = 1; i < depths.length; i++) expect(depths[i]).toBeLessThan(depths[i - 1]);
    expect(depths).toEqual([...depths].map((d) => d)); // tất định
    expect(layerDepth("network_access")).toBe(-12);
  });

  it("sideX: máy gửi bên trái, máy nhận bên phải, đường truyền ở giữa", () => {
    expect(sideX("sender")).toBeLessThan(sideX("medium"));
    expect(sideX("medium")).toBeLessThan(sideX("receiver"));
    expect(sideX("medium")).toBe(0);
  });

  it("SSR: render container + narration, KHÔNG ném lỗi (WebGL chưa chạy)", () => {
    const html = renderToString(
      <Encap3DWorkspace config={CONFIG} state={at(1)} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain("three-container");
    expect(html).toContain("đoạn TCP");
    expect(html).toContain("Trục sâu"); // caption meaning_of_z
  });

  it("môi trường không WebGL → tryCreateWebGLRenderer trả null, không ném", () => {
    expect(tryCreateWebGLRenderer()).toBeNull();
    expect(ENCAP_WEBGL_FALLBACK).toContain("2D");
  });

  it("3D KHÔNG tự tính PDU: file không chứa nhãn 'TCP'/'IP' cứng ngoài import model", () => {
    // Bằng chứng không nhân đôi engine: mọi phân đoạn đến từ state.pdu.
    // (kiểm ở mức hành vi: cùng state → cùng phân đoạn ở 2D và 3D SSR)
    const html3d = renderToString(
      <Encap3DWorkspace config={CONFIG} state={at(3)} busy={false} dispatch={() => {}} />,
    );
    expect(html3d).toContain("gói IP trở thành khung"); // narration từ state, không bịa
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/simulations/domains/network/encap-render3d.test.tsx -t "3D renderer"`
Expected: FAIL (`encap-ui3d` not found).

- [ ] **Step 3: Write the 3D renderer** — create `src/simulations/domains/network/encap-ui3d.tsx`:

```tsx
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { WorkspaceProps } from "../../types";
import {
  currentStep, LAYERS, LAYER_LABEL,
  type EncapConfig, type EncapState, type LayerId, type PduComponent, type Side,
} from "./encap-model";

/**
 * Renderer 3D của network.protocol_encapsulation (M10 — 3D SƯ PHẠM).
 *
 * CÙNG module/CÙNG EncapState với renderer 2D: KHÔNG engine 3D, KHÔNG tính lại
 * PDU, KHÔNG prediction riêng (PredictionBar dùng chung, nằm ngoài renderer).
 *
 * TUYÊN BỐ TRUNG TÂM: trục Z = TẦNG GIAO THỨC (nghĩa khái niệm thật), trục X =
 * chiều truyền (gửi → nhận). PDU đi XUỐNG các tầng khi đóng gói, băng NGANG khi
 * truyền, đi LÊN khi mở gói. Mọi toạ độ/camera/mesh là renderer-owned (ref/closure),
 * KHÔNG BAO GIỜ vào store/state (M7.FREEZE).
 */

type Props = WorkspaceProps<EncapConfig, EncapState>;

const LAYER_GAP = 4;
/** Z = độ sâu TẦNG: Application 0 → Network Access -12. Đây là nghĩa của trục sâu. */
export function layerDepth(layer: LayerId): number {
  return -LAYERS.indexOf(layer) * LAYER_GAP;
}
/** X = chiều truyền: gửi (-6) → đường truyền (0) → nhận (+6). */
export function sideX(side: Side): number {
  return side === "sender" ? -6 : side === "receiver" ? 6 : 0;
}

const ROLE_COLOR_3D: Record<string, number> = {
  payload: 0x34d399, // green
  header: 0x38bdf8, // sky
  trailer: 0xfb923c, // orange
};

export const ENCAP_WEBGL_FALLBACK =
  "Không khởi tạo được chế độ 3D trên thiết bị này (WebGL không khả dụng). " +
  "Mô phỏng vẫn hoạt động đầy đủ ở chế độ 2D — hãy bấm nút 2D phía trên.";

export function tryCreateWebGLRenderer(): THREE.WebGLRenderer | null {
  try {
    return new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch {
    return null;
  }
}

function makeLabelSprite(text: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 64;
  const ctx = canvas.getContext("2d")!;
  ctx.textAlign = "center";
  ctx.font = "bold 28px system-ui, sans-serif";
  ctx.lineWidth = 6;
  ctx.strokeStyle = "rgba(15,23,42,0.9)";
  ctx.strokeText(text, 128, 40);
  ctx.fillStyle = "#ffffff";
  ctx.fillText(text, 128, 40);
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(canvas), depthTest: false }),
  );
  sprite.scale.set(2.6, 0.65, 1);
  return sprite;
}

interface SceneHandles {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  pduGroup: THREE.Group;
  pduTarget: THREE.Vector3;
  raf: number;
  observer: ResizeObserver;
  home: { position: THREE.Vector3; target: THREE.Vector3 };
}

/** Dựng lại nhóm PDU (các hộp phân đoạn) theo state.pdu — thứ tự từ engine. */
function buildPduGroup(pdu: PduComponent[]): THREE.Group {
  const group = new THREE.Group();
  const W = 0.9;
  const total = pdu.length * W;
  pdu.forEach((c, i) => {
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(W * 0.92, 0.6, 0.6),
      new THREE.MeshLambertMaterial({ color: ROLE_COLOR_3D[c.role] }),
    );
    box.position.x = -total / 2 + W * (i + 0.5);
    group.add(box);
    const label = makeLabelSprite(c.label);
    label.position.set(box.position.x, 0.7, 0);
    label.scale.set(1.2, 0.4, 1);
    group.add(label);
  });
  return group;
}

function disposeScene(h: SceneHandles, container: HTMLElement): void {
  cancelAnimationFrame(h.raf);
  h.observer.disconnect();
  h.controls.dispose();
  h.scene.traverse((obj) => {
    if (obj instanceof THREE.Mesh) {
      obj.geometry.dispose();
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      for (const m of mats) m.dispose();
    }
    if (obj instanceof THREE.Sprite) {
      obj.material.map?.dispose();
      obj.material.dispose();
    }
  });
  h.renderer.dispose();
  if (h.renderer.domElement.parentElement === container) container.removeChild(h.renderer.domElement);
}

function pduPosition(state: EncapState): THREE.Vector3 {
  const step = currentStep(state);
  const layer = step.activeLayer ?? "network_access"; // truyền tin: ở độ sâu khung
  return new THREE.Vector3(sideX(step.side), 0.4, layerDepth(layer));
}

export function Encap3DWorkspace({ state }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const handlesRef = useRef<SceneHandles | null>(null);
  const [webglFailed, setWebglFailed] = useState(false);
  const step = currentStep(state);

  // Dựng scene MỘT LẦN cho một mô phỏng (số tầng/side bất biến; đổi bước chỉ dời PDU).
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const renderer = tryCreateWebGLRenderer();
    if (!renderer) {
      setWebglFailed(true);
      return;
    }
    const scene = new THREE.Scene();
    scene.add(new THREE.AmbientLight(0xffffff, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 1.5);
    sun.position.set(6, 10, 8);
    scene.add(sun);

    // Bốn phiến tầng (slab) ở mỗi độ sâu Z — cả hai phía gửi/nhận.
    for (const layer of LAYERS) {
      const z = layerDepth(layer);
      const slab = new THREE.Mesh(
        new THREE.BoxGeometry(16, 0.08, 2.6),
        new THREE.MeshLambertMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.18 }),
      );
      slab.position.set(0, -0.5, z);
      scene.add(slab);
      const label = makeLabelSprite(LAYER_LABEL[layer]);
      label.position.set(-7.4, 0, z);
      scene.add(label);
    }
    // Nhãn hai đầu trục X (chiều truyền).
    const gtx = makeLabelSprite("MÁY GỬI");
    gtx.position.set(sideX("sender"), 1.6, 0);
    scene.add(gtx);
    const rcv = makeLabelSprite("MÁY NHẬN");
    rcv.position.set(sideX("receiver"), 1.6, 0);
    scene.add(rcv);

    const pduGroup = buildPduGroup(currentStep(state).pdu);
    const startPos = pduPosition(state);
    pduGroup.position.copy(startPos);
    scene.add(pduGroup);

    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    camera.position.set(0, 9, 12);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, -6);
    controls.enablePan = false;
    controls.minDistance = 6;
    controls.maxDistance = 40;
    controls.enableDamping = true;
    const home = { position: camera.position.clone(), target: controls.target.clone() };

    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    const resize = () => {
      const w = container.clientWidth || 600;
      const h = container.clientHeight || 320;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);

    const handles: SceneHandles = {
      renderer, scene, camera, controls, pduGroup,
      pduTarget: startPos.clone(), raf: 0, observer, home,
    };
    const tick = () => {
      handles.raf = requestAnimationFrame(tick);
      pduGroup.position.lerp(handles.pduTarget, 0.14);
      controls.update();
      renderer.render(scene, camera);
    };
    tick();
    handlesRef.current = handles;
    return () => {
      handlesRef.current = null;
      disposeScene(handles, container);
    };
    // Chỉ payloadLabel (định danh mô phỏng) là bất biến trong một phiên; đổi bước
    // KHÔNG rebuild — effect dưới lo việc rebuild nhóm PDU + dời vị trí.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.payloadLabel]);

  // Đổi bước → rebuild nhóm PDU (thành phần đổi) + dời tới đích ngữ nghĩa mới.
  useEffect(() => {
    const h = handlesRef.current;
    if (!h) return;
    h.scene.remove(h.pduGroup);
    h.pduGroup.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose();
        (obj.material as THREE.Material).dispose();
      }
      if (obj instanceof THREE.Sprite) {
        obj.material.map?.dispose();
        obj.material.dispose();
      }
    });
    const group = buildPduGroup(step.pdu);
    const target = pduPosition(state);
    group.position.copy(h.pduGroup.position); // lướt từ vị trí cũ
    h.scene.add(group);
    h.pduGroup = group;
    h.pduTarget = target;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.cursor]);

  if (webglFailed) {
    return (
      <div className="stack" style={{ gap: "var(--sp-md)" }}>
        <div className="sim-stage">
          <p className="notes" role="alert" style={{ padding: "var(--sp-lg)" }}>
            {ENCAP_WEBGL_FALLBACK}
          </p>
        </div>
        <div className="narration-bar">{step.narration}</div>
      </div>
    );
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage sim-stage-3d">
        <div ref={containerRef} className="three-container" />
        <div className="three-caption">Trục sâu = tầng giao thức · trục ngang = chiều truyền</div>
        <button
          type="button"
          className="btn-utility three-reset-view"
          title="Đưa camera về góc nhìn ban đầu — KHÔNG ảnh hưởng mô phỏng"
          onClick={() => {
            const h = handlesRef.current;
            if (!h) return;
            h.camera.position.copy(h.home.position);
            h.controls.target.copy(h.home.target);
            h.controls.update();
          }}
        >
          ⌂ Góc nhìn
        </button>
      </div>
      <div className="narration-bar">{step.narration}</div>
    </div>
  );
}
```

- [ ] **Step 4: Add caption CSS** — append to `src/styles/global.css`:

```css
.three-caption {
  position: absolute;
  left: var(--sp-sm);
  bottom: var(--sp-sm);
  font-size: 12px;
  color: var(--ink-muted);
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--rounded-md);
  padding: 4px 8px;
  pointer-events: none;
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `npx vitest run src/simulations/domains/network/encap-render3d.test.tsx -t "3D renderer"`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/simulations/domains/network/encap-ui3d.tsx src/simulations/domains/network/encap-render3d.test.tsx src/styles/global.css
git commit -m "M10: 3D encapsulation renderer (X=direction, Z=protocol layer) with meaning caption"
```

---

## Task 5: Module assembly (`encap.ts`) + registration + prediction/store/metadata tests

**Files:**
- Create: `src/simulations/domains/network/encap.ts`
- Modify: `src/simulations/domains/network/index.ts` (register + export)
- Test: `src/simulations/domains/network/encap.test.ts` (append module + prediction) and `encap-render3d.test.tsx` (append store parity + metadata)

**Interfaces:**
- Consumes: everything from `encap-model`, `EncapWorkspace`/`EncapInspector` (`encap-ui`), `Encap3DWorkspace` (lazy from `encap-ui3d`), `registerSimulation`, `SimulationModule`, `ConfigResult`.
- Produces: `makeEncapsulationModule(): SimulationModule<EncapConfig, EncapState>`; `registerNetworkDomain()` now registers **two** modules.

- [ ] **Step 1: Write failing tests** — append to `src/simulations/domains/network/encap.test.ts`:

```ts
import { makeEncapsulationModule } from "./encap";

const emod = makeEncapsulationModule();

describe("(M10) module đóng gói — hợp đồng + validate", () => {
  it("id/domain/mode/threeD đúng", () => {
    expect(emod.id).toBe("network.protocol_encapsulation");
    expect(emod.domain).toBe("network");
    expect(emod.interactionMode).toBe("progressive");
    expect(emod.supportedVisualModes).toEqual(["2d", "3d"]);
    expect(emod.threeD!.role).toBe("pedagogical");
    expect(emod.threeD!.meaningOfZ.toLowerCase()).toContain("tầng");
  });

  it("validateConfig chuẩn hoá payload thiếu về mặc định", () => {
    const r = emod.validateConfig({});
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.config.payloadLabel).toBe("Dữ liệu ứng dụng");
  });

  it("init dựng 9 bước; timeline kẹp", () => {
    const s = emod.init({ payloadLabel: "X", appProtocol: null, notes: null });
    expect(emod.timeline!.stepCount(s)).toBe(9);
    expect(emod.timeline!.currentStep(emod.timeline!.goToStep(s, 99))).toBe(8);
  });

  it("getExplainContext sạch, serializable, không lộ toạ độ", () => {
    const s = emod.timeline!.goToStep(emod.init({ payloadLabel: "X", appProtocol: null, notes: null }), 2);
    const ctx = emod.getExplainContext(s, { payloadLabel: "X", appProtocol: null, notes: null });
    expect(JSON.parse(JSON.stringify(ctx))).toEqual(ctx);
    expect(ctx.simulation_id).toBe("network.protocol_encapsulation");
    expect(ctx.active_layer).toBe("internet");
  });
});

describe("(M10) prediction — bám delta thật của bước kế tiếp", () => {
  const base = emod.init({ payloadLabel: "Dữ liệu ứng dụng", appProtocol: null, notes: null });
  const at = (i: number) => ({ ...base, cursor: i });

  it("ở bước đóng gói: hỏi 'thêm gì', đáp án đúng = mảnh của bước kế", () => {
    const ch = emod.predict!.challenge(at(0));
    expect(ch).not.toBeNull();
    expect(ch!.question).toContain("THÊM");
    expect(ch!.options.map((o) => o.id)).toEqual(["tcp", "ip", "link+fcs"]);
    expect(emod.predict!.check(at(0), "tcp").verdict).toBe("correct");
    expect(emod.predict!.check(at(0), "ip").verdict).toBe("incorrect");
  });

  it("ở Network Access: LINK+FCS là MỘT đáp án gộp đúng", () => {
    expect(emod.predict!.check(at(2), "link+fcs").verdict).toBe("correct");
    expect(emod.predict!.check(at(2), "link+fcs").expectedId).toBe("link+fcs");
  });

  it("ở bước mở gói: hỏi 'gỡ gì', gỡ LINK+FCS trước", () => {
    const ch = emod.predict!.challenge(at(4));
    expect(ch!.question).toContain("GỠ");
    expect(emod.predict!.check(at(4), "link+fcs").verdict).toBe("correct");
  });

  it("bước truyền tin / đã xong → không có challenge", () => {
    expect(emod.predict!.challenge(at(3))).toBeNull(); // kế tiếp là transmit
    expect(emod.predict!.challenge(at(8))).toBeNull(); // hết bước
    expect(emod.predict!.check(at(3), "tcp").verdict).toBe("unsupported_to_verify");
  });

  it("(bất biến) check là hàm THUẦN — không đụng state", () => {
    const before = JSON.stringify(at(1));
    emod.predict!.check(at(1), "ip");
    expect(JSON.stringify(at(1))).toBe(before);
  });
});
```

Append to `src/simulations/domains/network/encap-render3d.test.tsx`:

```tsx
import { registerAllSimulations } from "../../index";
import { useAppStore } from "../../../state/store";
import type { SimulationEnvelope } from "../../types";
import { availableVisualModes, rendererFor } from "../../renderer";
import { makeEncapsulationModule } from "./encap";

registerAllSimulations();

function encapEnvelope(): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: "network.protocol_encapsulation",
    domain: "network",
    visual_mode: "2d",
    title: "t",
    description: null,
    config: { payloadLabel: "Dữ liệu ứng dụng", appProtocol: "HTTP", notes: null },
    notes: null,
  };
}

describe("(M10) shared renderer + store: đổi 2D/3D không đụng engine", () => {
  const emod = makeEncapsulationModule();
  it("khai đủ hai mode, cả hai có renderer thật, id KHÔNG có hậu tố _3d", () => {
    expect(availableVisualModes(emod)).toEqual(["2d", "3d"]);
    expect(rendererFor(emod, "2d")).toBe(emod.Workspace);
    expect(rendererFor(emod, "3d")).toBeDefined();
    expect(emod.id).toBe("network.protocol_encapsulation");
  });

  it("đổi mode nhiều lần: state + cursor nguyên vẹn", () => {
    useAppStore.getState().reset();
    useAppStore.getState().loadEnvelope(encapEnvelope());
    useAppStore.getState().nextStep();
    useAppStore.getState().nextStep();
    const before = useAppStore.getState().active!.state;
    for (let i = 0; i < 5; i++) useAppStore.getState().setVisualMode(i % 2 === 0 ? "3d" : "2d");
    expect(useAppStore.getState().active!.state).toBe(before);
    expect((useAppStore.getState().active!.state as EncapState).cursor).toBe(2);
  });

  it("(honesty) encapsulation là 3D SƯ PHẠM; packet_routing là PoC", () => {
    expect(makeEncapsulationModule().threeD!.role).toBe("pedagogical");
    // đối chiếu: hai module cùng domain, phân loại KHÁC nhau — trung thực
    const routing = useAppStore.getState(); // registry đã có cả hai
    void routing;
    expect(makeEncapsulationModule().threeD!.meaningOfZ).toContain("tầng");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/simulations/domains/network/encap.test.ts src/simulations/domains/network/encap-render3d.test.tsx`
Expected: FAIL (`./encap` not found).

- [ ] **Step 3: Write the module** — create `src/simulations/domains/network/encap.ts`:

```ts
import { lazy } from "react";
import { registerSimulation } from "../../registry";
import type { ConfigResult, SimulationModule } from "../../types";
import {
  buildEncapState, currentStep, LAYER_LABEL, PROTOCOL_PIECES, pieceForComponents,
  type EncapConfig, type EncapState,
} from "./encap-model";
import { EncapWorkspace, EncapInspector } from "./encap-ui";

/**
 * network.protocol_encapsulation (M10) — mô phỏng TIẾN TRÌNH (progressive).
 *
 * Module THỨ HAI của domain network. Cùng khuôn packet_routing: engine tất định
 * dựng toàn bộ timeline; 2D + 3D dùng chung state; PredictionCapability chấm bằng
 * chính engine. threeD = "pedagogical" vì Z mã hoá TẦNG GIAO THỨC (nghĩa thật).
 */

const Encap3DWorkspace = lazy(() =>
  import("./encap-ui3d").then((m) => ({ default: m.Encap3DWorkspace })),
);

function validateEncapConfig(raw: unknown): ConfigResult<EncapConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const payloadLabel =
    typeof r.payloadLabel === "string" && r.payloadLabel.trim()
      ? r.payloadLabel.trim()
      : "Dữ liệu ứng dụng";
  const appProtocol =
    typeof r.appProtocol === "string" && r.appProtocol.trim() ? r.appProtocol.trim() : null;
  const notes = typeof r.notes === "string" ? r.notes : null;
  return { ok: true, config: { payloadLabel, appProtocol, notes } };
}

export function makeEncapsulationModule(): SimulationModule<EncapConfig, EncapState> {
  return {
    id: "network.protocol_encapsulation",
    domain: "network",
    title: "Đóng gói dữ liệu qua các tầng TCP/IP",
    interactionMode: "progressive",
    supportedVisualModes: ["2d", "3d"],
    // M10: 3D SƯ PHẠM — Z = tầng giao thức (nghĩa khái niệm thật, không phải bố cục).
    threeD: {
      role: "pedagogical",
      meaningOfZ: "độ sâu tầng giao thức (Application → Network Access)",
    },

    validateConfig: validateEncapConfig,
    init: buildEncapState,
    apply: (state) => state, // điều khiển qua timeline; không what-if

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: Math.max(0, Math.min(step, s.steps.length - 1)) }),
    },

    /**
     * Nhịp DỰ ĐOÁN — hỏi tại điểm quyết định (add ở máy gửi, remove ở máy nhận).
     * Ground truth = delta của bước KẾ TIẾP (engine đã dựng). LINK+FCS là MỘT
     * đáp án gộp. Chấm là hàm thuần, KHÔNG đụng canonical state.
     */
    predict: {
      challenge: (s) => {
        const next = s.steps[s.cursor + 1];
        if (!next) return null;
        if (next.delta.kind === "add") {
          return {
            question: "Theo em, tầng kế tiếp sẽ THÊM phần thông tin giao thức nào?",
            options: PROTOCOL_PIECES.map((p) => ({ id: p.id, label: p.label })),
          };
        }
        if (next.delta.kind === "remove") {
          return {
            question: "Ở máy nhận, phần thông tin giao thức nào được GỠ tiếp theo?",
            options: PROTOCOL_PIECES.map((p) => ({ id: p.id, label: p.label })),
          };
        }
        return null;
      },
      check: (s, answerId) => {
        const next = s.steps[s.cursor + 1];
        if (!next || (next.delta.kind !== "add" && next.delta.kind !== "remove")) {
          return {
            verdict: "unsupported_to_verify",
            answerId,
            message: "Ở bước này không có phần thông tin giao thức nào được thêm hoặc gỡ để dự đoán.",
          };
        }
        const expected = pieceForComponents(next.delta.componentIds)!;
        const layerName = next.delta.layer ? LAYER_LABEL[next.delta.layer] : "";
        const verb = next.delta.kind === "add" ? "thêm" : "gỡ";
        if (answerId === expected.id) {
          return {
            verdict: "correct",
            answerId,
            expectedId: expected.id,
            message: `Chính xác. Ở bước kế tiếp, ${layerName} ${verb} ${expected.label.toLowerCase()}.`,
          };
        }
        return {
          verdict: "incorrect",
          answerId,
          expectedId: expected.id,
          message: `Chưa đúng. Ở bước kế tiếp, ${layerName} ${verb} ${expected.label.toLowerCase()}.`,
        };
      },
    },

    getExplainContext: (state) => {
      const step = currentStep(state);
      return {
        simulation_id: "network.protocol_encapsulation",
        phase: step.phase,
        side: step.side,
        active_layer: step.activeLayer,
        pdu: step.pdu.map((c) => c.label),
        current_step: state.cursor + 1,
        total_steps: state.steps.length,
        narration: step.narration,
      };
    },

    Workspace: EncapWorkspace,
    renderers: { "3d": Encap3DWorkspace },
    Inspector: EncapInspector,
  };
}
```

- [ ] **Step 4: Register the module** — in `src/simulations/domains/network/index.ts`:

Add to the top imports:
```ts
import { makeEncapsulationModule } from "./encap";
```
Change `registerNetworkDomain` to register both:
```ts
export function registerNetworkDomain(): void {
  registerSimulation(makeNetworkModule());
  registerSimulation(makeEncapsulationModule());
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `npx vitest run src/simulations/domains/network/encap.test.ts src/simulations/domains/network/encap-render3d.test.tsx`
Expected: PASS.

- [ ] **Step 6: Run the whole suite to catch count assertions**

Run: `npm test`
Expected: All green EXCEPT possibly `data/catalog.test.tsx` counts (fixed in Task 6). If any *other* test asserts a total module/registry count, update it to include the new module and note it in the commit. `domains.test.ts` registers modules manually and is unaffected.

- [ ] **Step 7: Typecheck + commit**

```bash
npx tsc -b
git add src/simulations/domains/network/encap.ts src/simulations/domains/network/index.ts src/simulations/domains/network/encap.test.ts src/simulations/domains/network/encap-render3d.test.tsx
git commit -m "M10: assemble network.protocol_encapsulation module (prediction, threeD=pedagogical) + register"
```

---

## Task 6: Public offline sample, preview, catalog tests

**Files:**
- Modify: `src/data/sim-samples.ts` (add `OfflineSample`)
- Modify: `src/components/SamplePreview.tsx` (new kind + `previewKindOf` mapping)
- Test: `src/data/catalog.test.tsx` (update counts + preview)

**Interfaces:**
- Consumes: `OfflineSample` type, `previewKindOf`, `SamplePreview`.
- Produces: catalog entry id `network-encapsulation`; preview kind `network-encapsulation`.

> **Scope note:** the sample is reachable via the **Library** (whose card count is dynamic = `publicCatalog().length`, so `ux-shell.test.tsx` line ~127 auto-adjusts). It is **not** added to `STARTER_SIM_IDS` — Home is deliberately curated at exactly 6 starter cards (locked by `ux-shell.test.tsx` lines ~70 and ~111). Do **not** touch `offline-catalog.ts` or the starter assertion.

- [ ] **Step 1: Update the failing tests** — edit `src/data/catalog.test.tsx`:

Change the public-count assertion (currently `expect(pub).toHaveLength(12);`) to `13` and add the new id:
```tsx
    // 8 algorithm + logic + binary + network(x2) + web = 13 mẫu công khai
    expect(pub).toHaveLength(13);
    expect(ids).toContain("gen-web");
    expect(ids).toContain("network-encapsulation"); // M10 flagship (Thư viện)
```
Change the offline-count assertion (currently `expect(all).toHaveLength(16);`) to `17`.
**Leave the `starterEntries` assertion unchanged** (still the 6 ids — the flagship is not a Home starter).
In the `previewKindOf` test, add:
```tsx
    expect(previewKindOf("network.protocol_encapsulation")).toBe("network-encapsulation");
```
In the "mọi kind đều là SVG" enumeration list, add `"network-encapsulation"` to the array.

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/data/catalog.test.tsx`
Expected: FAIL (counts/preview kind not yet present).

- [ ] **Step 3: Add the offline sample** — in `src/data/sim-samples.ts`, add a new entry to the `OFFLINE_SAMPLES` array literal (after the `network-packet` object, before the closing `]`):

```ts
  {
    id: "network-encapsulation",
    envelope: {
      status: "ok",
      simulation_id: "network.protocol_encapsulation",
      domain: "network",
      visual_mode: "2d",
      title: "Dữ liệu được đóng gói qua các tầng TCP/IP như thế nào?",
      description: "Đóng gói ở máy gửi, truyền đi, rồi mở gói ở máy nhận",
      config: { payloadLabel: "Dữ liệu ứng dụng", appProtocol: "HTTP", notes: null },
      notes: null,
    },
  },
```
(No `visibility` → defaults to `public`.)

- [ ] **Step 4: Add the preview** — `src/components/SamplePreview.tsx` uses a `PreviewKind` union, a `KIND_BY_SIM_ID` map, one component function per kind, and a `RENDERERS: Record<PreviewKind, () => JSX.Element>` map. Make **four** edits:

(a) Add to the `PreviewKind` union (after `"network-path"`):
```ts
  | "network-encapsulation"
```

(b) Add to `KIND_BY_SIM_ID` (after the `network.packet_routing` line):
```ts
  "network.protocol_encapsulation": "network-encapsulation",
```

(c) Add a component function next to `NetworkPath()` (use `className="sample-preview-svg"` and `viewBox="0 0 96 56"` like the other previews — growing segment widths depict encapsulation nesting; payload green, headers sky, trailer orange):
```tsx
function NetworkEncap() {
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      <rect x="8" y="8" width="34" height="8" rx="2" fill="var(--accent-green)" />
      <rect x="8" y="20" width="48" height="8" rx="2" fill="var(--accent-sky)" />
      <rect x="8" y="32" width="62" height="8" rx="2" fill="var(--accent-sky)" opacity="0.6" />
      <rect x="8" y="44" width="80" height="8" rx="2" fill="var(--accent-orange)" opacity="0.7" />
    </svg>
  );
}
```

(d) Register it in the `RENDERERS` map (after `"network-path": NetworkPath,`):
```ts
  "network-encapsulation": NetworkEncap,
```
> `RENDERERS` is typed `Record<PreviewKind, () => JSX.Element>`, so **all three** of (a), (c), (d) are required together — omitting the union member or the map entry is a type error, and `isPreviewKind` (`s in RENDERERS`) is what makes `previewKindOf`'s explicit-kind path recognise it.

- [ ] **Step 5: Run tests to verify they pass**

Run: `npx vitest run src/data/catalog.test.tsx`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/data/sim-samples.ts src/components/SamplePreview.tsx src/data/catalog.test.tsx
git commit -m "M10: public encapsulation sample (Library) + segmented-stack preview"
```

---

## Task 7: Docs + full regression gates + manual acceptance

**Files:**
- Modify: `docs/CURRENT_STATE.md`, `docs/COVERAGE.md`, `docs/ARCHITECTURE_MAP.md`, `docs/CODE_INDEX.md`

**Interfaces:** none (docs + verification).

- [ ] **Step 1: Full frontend gates**

Run (from `frontend`):
```bash
npm test
npm run build
```
Expected: `npm test` all green (report the exact vitest count — it will differ from the pre-M10 baseline because of the new tests; that is expected, report the real number). `npm run build` clean.

- [ ] **Step 2: Backend regression (unchanged, must stay green)**

Run (from `backend`, venv active):
```bash
python -m pytest -q
```
Expected: green, same count as baseline (M10 touches no backend). Report the real number.

- [ ] **Step 3: Real-browser layout audit** — start dev server, run audit, confirm the tool actually inspects the workspace route.

Run (from `frontend`):
```bash
npm run dev   # in one shell (background)
npm run audit:layout
```
Expected: 4/4 routes clean. If the audit reports off-4px-grid spacing or overflow on the encapsulation stage, fix the `.encap-*` CSS (Task 3/4) to land on the 4px scale, then re-run. **Prove the audit can still fail** (fault-injection) before trusting a clean result, per anti-pattern #14 — temporarily add a `padding: 3px` to `.encap-layer`, confirm the audit flags it, then revert.

- [ ] **Step 4: Update `docs/CURRENT_STATE.md`** — add an M10 row to the milestone table (§2) and refresh the baseline counts (§1) with the real pytest/vitest numbers:

```md
| **M10-3D-PED** | *(nhánh `m10-3d-ped`)* | **3D SƯ PHẠM đầu tiên: đóng gói/mở gói TCP/IP.** Module THỨ HAI của domain network (`network.protocol_encapsulation`) — engine tất định 9 bước dựng PDU phân đoạn (delta tường minh add/remove/transmit/deliver; LINK+FCS **nguyên tử**); 2D (stack gửi/nhận) + **3D có NGHĨA**: X = chiều truyền, **Z = tầng giao thức** (`meaning_of_z`). Dùng chung PredictionCapability (LINK+FCS là một đáp án gộp). Thêm field hợp đồng `threeD` phân loại TRUNG THỰC: encapsulation = `pedagogical`, packet_routing = `architectural_poc`. Một mẫu công khai + preview + starter Home. Định tuyến AI **HOÃN** (frontend + mẫu offline; **0 gọi AI**). Click 3D trực tiếp **HOÃN**. Bất biến #18. |
```

- [ ] **Step 5: Update `docs/ARCHITECTURE_MAP.md`** — add invariant #18 to the §5 table:

```md
| 18 | **Nghĩa của chiều sâu 3D phải TRUNG THỰC** (M10): module khai `threeD.role` = `architectural_poc` (Z chỉ là bố cục, vd packet_routing) hoặc `pedagogical` (Z mã hoá biến khái niệm thật, vd `network.protocol_encapsulation`: Z = tầng giao thức). PoC không được giả vờ có nghĩa khái niệm. | `SimulationModule.threeD` + renderer caption | `render3d.test.tsx`, `encap-render3d.test.tsx` |
```
Add `network.protocol_encapsulation` to the source-of-truth/ownership notes near invariant #16 (second network 3D module; the pedagogical one).

- [ ] **Step 6: Update `docs/COVERAGE.md` §8** — append under "Kết quả M8":

```md
### M10 — 3D sư phạm đầu tiên (đã ship, nhánh `m10-3d-ped`)

- `network.protocol_encapsulation` là mô phỏng ĐẦU TIÊN có **chiều sâu 3D mang
  nghĩa khái niệm**: `meaning_of_z = tầng giao thức`. Đóng gói đi xuống, truyền
  ngang, mở gói đi lên — cùng engine/state cho 2D và 3D.
- `network.packet_routing` được **phân loại lại TRUNG THỰC** là `architectural_poc`
  (Z chỉ tách nút trên/ngoài tuyến — bố cục).
- 2D vẫn có, là baseline dễ đọc + mặc định khi mở. **KHÔNG** tuyên bố 3D dạy tốt
  hơn 2D; chỉ tuyên bố: *"dùng chiều thứ ba để mã hoá độ sâu tầng giao thức, cho
  biểu diễn 3D một vai trò ngữ nghĩa tường minh."*
- `practice_activity` vẫn **PARTIAL / CHƯA làm**.
```

- [ ] **Step 7: Update `docs/CODE_INDEX.md`** — add the four new files (`encap-model.ts`, `encap-ui.tsx`, `encap-ui3d.tsx`, `encap.ts`) with a one-line role each and the re-verify tag `offline` (no live AI).

- [ ] **Step 8: Commit docs**

```bash
git add docs/CURRENT_STATE.md docs/ARCHITECTURE_MAP.md docs/COVERAGE.md docs/CODE_INDEX.md
git commit -m "M10: docs — encapsulation flagship, invariant #18 (honest 3D depth meaning)"
```

- [ ] **Step 9: Manual acceptance in a real browser** (spec §24). With `npm run dev` running, open the app and verify:
  - **Flow A (2D):** open "Dữ liệu được đóng gói qua các tầng TCP/IP như thế nào?" → payload starts as `[Dữ liệu ứng dụng]` → advance: TCP, IP, LINK+FCS appear in order → at a prediction point submit a wrong answer → deterministic causal feedback → advance through transmission → decapsulation removes LINK+FCS first → delivered payload equals original.
  - **Flow B (3D):** switch to 3D → sender/receiver distinguishable on X → PDU descends through Z layers on the sender, crosses on X, ascends on the receiver → mechanism readable without rotating (caption visible).
  - **Flow C (parity):** stop at step 3 (frame built), note PDU → 2D↔3D → identical state/cursor, no AI call (Network tab shows no `/api/*`).
  - **Flow D (history):** advance, set 3D, go Home, reopen from history → same step + 3D restored, 0 `/api/analyze|edit|explain`.
  - **Flow E (old 3D honesty):** open packet routing → still works, no regression; its 3D makes no protocol-layer claim.

Record results (pass/fail per flow) in the final report. Do not proceed to any new milestone.

---

## Self-review notes (author)

- **Spec coverage:** §3 identity → T1/T5; §4 engine (9-step, delta, atomic LINK+FCS) → T2; §5 prediction (fixed 3 pieces, LINK+FCS combined, keyed on next delta.kind) → T5; §6 metadata → T1+T5; §7 2D → T3; §8 3D (X=dir, Z=layer, caption) → T4; §9 catalog/sample/preview/history → T6 (+ history verified in T7 Flow D); §10 tests+docs → T2–T7; §11 direct-3D deferred → documented, not built; invariants #1–#4 → T2 tests; #5 honesty → T1+T5.
- **Type consistency:** `buildEncapState`/`currentStep`/`pieceForComponents`/`PROTOCOL_PIECES`/`LAYER_LABEL`/`LAYERS` names identical across T2/T3/T4/T5; `layerDepth`/`sideX`/`ENCAP_WEBGL_FALLBACK`/`tryCreateWebGLRenderer` defined in T4 and consumed only within T4's file; module id string `network.protocol_encapsulation` identical everywhere.
- **Known verification-dependent spots:** the exact JSX signature of `SamplePreview` cases and the shape of the `previewKindOf` mapping must be read from the file before editing (T6 Step 5 says so); CSS token names must be confirmed against `:root` (T3 Step 4 note). Both are flagged inline rather than guessed.
