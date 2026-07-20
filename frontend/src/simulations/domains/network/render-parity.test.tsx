import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { buildEncapState, currentStep as encapStep, LAYERS, type EncapConfig } from "./encap-model";
import { EncapWorkspace, ROLE_COLOR } from "./encap-ui";
import { layerDepth, pduLayout3d, ROLE_COLOR_3D, sideX } from "./encap-ui3d";

import { makeNetworkModule } from "./index";
import type { NetworkState } from "./model";
import { layout2d, NetworkWorkspace } from "./ui";
import { layout3d } from "./ui3d";

/**
 * TẦNG ĐỐI CHIẾU RENDERER (2D ↔ 3D) — bằng chứng khoá được cho luận điểm
 * "một authoritative state → hai renderer, không fork engine, không renderer nào
 * tính lại hay bịa" (bất biến #16/#18).
 *
 * Khác với các test render sẵn có (mỗi renderer kiểm riêng lẻ), tầng này khẳng
 * định TAM GIÁC: sự thật renderer-2D == sự thật renderer-3D == authoritative
 * state, ở MỌI bước. Test thuần (SSR + hàm bố cục PURE) — 0 WebGL, 0 network.
 */

// ── Trích nhãn phân đoạn PDU mà renderer 2D thực sự xuất ra (SSR HTML).
function seg2dLabels(html: string): string[] {
  const re = /class="encap-seg[^"]*"[^>]*>([^<]*)</g;
  const out: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) !== null) out.push(m[1]);
  return out;
}

const ENCAP_CONFIG: EncapConfig = {
  payloadLabel: "Dữ liệu ứng dụng",
  appProtocol: "HTTP",
  notes: null,
};

function encapAt(cursor: number) {
  return { ...buildEncapState(ENCAP_CONFIG), cursor };
}

describe("PARITY encapsulation — PDU 2D == PDU 3D == state.pdu ở MỌI bước", () => {
  const total = buildEncapState(ENCAP_CONFIG).steps.length;

  it(`cả ${total} bước: nhãn phân đoạn 2D khớp ĐÚNG THỨ TỰ với state.pdu`, () => {
    for (let k = 0; k < total; k++) {
      const state = encapAt(k);
      const truth = encapStep(state).pdu.map((c) => c.label);
      const html = renderToString(
        <EncapWorkspace config={ENCAP_CONFIG} state={state} busy={false} dispatch={() => {}} />,
      );
      expect(seg2dLabels(html)).toEqual(truth); // đủ, đúng thứ tự, KHÔNG thừa/thiếu
    }
  });

  it("mọi bước: bố cục 3D (pduLayout3d) khớp state.pdu về id/role/thứ tự", () => {
    for (let k = 0; k < total; k++) {
      const pdu = encapStep(encapAt(k)).pdu;
      const segs = pduLayout3d(pdu);
      expect(segs.map((s) => s.id)).toEqual(pdu.map((c) => c.id));
      expect(segs.map((s) => s.role)).toEqual(pdu.map((c) => c.role));
      expect(segs).toHaveLength(pdu.length); // không mồ côi, không bịa thêm hộp
    }
  });

  it("ĐỐI CHIẾU TRỰC TIẾP 2D↔3D: nhãn hàng 2D == nhãn hộp 3D, mọi bước", () => {
    for (let k = 0; k < total; k++) {
      const state = encapAt(k);
      const html = renderToString(
        <EncapWorkspace config={ENCAP_CONFIG} state={state} busy={false} dispatch={() => {}} />,
      );
      const labels3d = pduLayout3d(encapStep(state).pdu).map((s) => s.label);
      expect(seg2dLabels(html)).toEqual(labels3d);
    }
  });

  it("x của hộp 3D tăng đơn điệu theo thứ tự PDU + đối xứng quanh 0", () => {
    const pdu = encapStep(encapAt(3)).pdu; // khung đầy đủ 5 phân đoạn
    const xs = pduLayout3d(pdu).map((s) => s.x);
    for (let i = 1; i < xs.length; i++) expect(xs[i]).toBeGreaterThan(xs[i - 1]);
    const sum = xs.reduce((a, b) => a + b, 0);
    expect(Math.abs(sum)).toBeLessThan(1e-9); // tâm ở gốc
    expect(pduLayout3d(pdu)).toEqual(pduLayout3d(pdu)); // tất định
  });
});

describe("FAITHFULNESS encapsulation — bảng màu 2D và 3D phủ CÙNG tập vai trò", () => {
  it("key ROLE_COLOR (2D) == key ROLE_COLOR_3D (3D)", () => {
    expect(Object.keys(ROLE_COLOR_3D).sort()).toEqual(Object.keys(ROLE_COLOR).sort());
  });

  it("mọi vai trò XUẤT HIỆN trong bất kỳ bước nào đều có màu ở CẢ HAI renderer", () => {
    const state = buildEncapState(ENCAP_CONFIG);
    const roles = new Set(state.steps.flatMap((s) => s.pdu.map((c) => c.role)));
    for (const role of roles) {
      expect(ROLE_COLOR[role]).toBeDefined();
      expect(ROLE_COLOR_3D[role]).toBeDefined();
    }
  });

  it("mọi TẦNG có activeLayer trong timeline đều có độ sâu Z xác định (không NaN)", () => {
    const state = buildEncapState(ENCAP_CONFIG);
    const layers = new Set(
      state.steps.map((s) => s.activeLayer).filter((l): l is (typeof LAYERS)[number] => l !== null),
    );
    for (const layer of layers) expect(Number.isFinite(layerDepth(layer))).toBe(true);
    // hai đầu trục X (gửi/nhận) cũng phải xác định
    expect(Number.isFinite(sideX("sender"))).toBe(true);
    expect(Number.isFinite(sideX("receiver"))).toBe(true);
  });
});

// ── packet_routing ─────────────────────────────────────────────────────────
const mod = makeNetworkModule();
const NET_CONFIG = {
  nodes: [
    { id: "client", type: "client" as const },
    { id: "router", type: "router" as const },
    { id: "isp", type: "isp" as const },
    { id: "server", type: "server" as const },
    { id: "sw", type: "switch" as const }, // NGOÀI route — kiểm phủ toàn bộ nút
  ],
  links: [
    ["client", "router"],
    ["router", "isp"],
    ["isp", "server"],
    ["router", "sw"],
  ] as [string, string][],
  source: "client",
  destination: "server",
  notes: null,
};

function netState(): NetworkState {
  const r = mod.validateConfig(NET_CONFIG);
  if (!r.ok) throw new Error(r.error);
  return mod.init(r.config);
}

describe("PARITY packet_routing — bố cục 2D và 3D phủ CÙNG tập nút", () => {
  it("layout2d và layout3d cùng định vị ĐÚNG toàn bộ nút (không thừa/thiếu)", () => {
    const s = netState();
    const allIds = s.nodes.map((n) => n.id).sort();
    const keys2d = Object.keys(layout2d(s.nodes, s.route).positions).sort();
    const keys3d = Object.keys(layout3d(s.nodes, s.route)).sort();
    expect(keys2d).toEqual(allIds);
    expect(keys3d).toEqual(allIds);
    expect(keys2d).toEqual(keys3d); // đối chiếu trực tiếp 2D↔3D
  });

  it("mọi bước: cả hai renderer định vị được gói tin ở CÙNG nút (packetAt)", () => {
    const s = netState();
    const pos2d = layout2d(s.nodes, s.route).positions;
    const pos3d = layout3d(s.nodes, s.route);
    for (let i = 0; i < mod.timeline!.stepCount(s); i++) {
      const at = (mod.timeline!.goToStep(s, i) as NetworkState).steps[i].packetAt;
      expect(pos2d[at]).toBeDefined(); // gói tin không mồ côi ở 2D
      expect(pos3d[at]).toBeDefined(); // ...cũng không ở 3D
    }
  });

  it("renderer 2D xuất mọi id nút (SSR) — không bỏ sót nút nào", () => {
    const s = netState();
    const html = renderToString(
      <NetworkWorkspace config={NET_CONFIG} state={s} busy={false} dispatch={() => {}} />,
    );
    for (const n of s.nodes) expect(html).toContain(n.id);
  });
});

describe("FAITHFULNESS packet_routing — bố cục KHÔNG bịa nút ngoài topology", () => {
  it("không key bố cục nào nằm ngoài tập nút của state (cả 2D lẫn 3D)", () => {
    const s = netState();
    const known = new Set(s.nodes.map((n) => n.id));
    for (const id of Object.keys(layout2d(s.nodes, s.route).positions)) expect(known.has(id)).toBe(true);
    for (const id of Object.keys(layout3d(s.nodes, s.route))) expect(known.has(id)).toBe(true);
  });
});
