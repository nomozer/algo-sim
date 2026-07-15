import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeNetworkModule } from "./index";
import type { NetworkState } from "./model";
import { NetworkWorkspace } from "./ui";
import {
  layout3d,
  Network3DWorkspace,
  tryCreateWebGLRenderer,
  WEBGL_FALLBACK_MESSAGE,
} from "./ui3d";
import { availableVisualModes, rendererFor } from "../../renderer";
import { registerAllSimulations } from "../../index";
import { useAppStore } from "../../../state/store";
import type { SimulationEnvelope } from "../../types";

/**
 * M8 Slice 2 — NETWORK 3D PoC: chứng minh "3D là renderer, không phải domain".
 *
 * KHÔNG có engine 3D / BFS thứ hai / prediction riêng: renderer 3D đọc ĐÚNG
 * NetworkState mà renderer 2D đọc; mọi toạ độ/camera/mesh là renderer-owned.
 * 0 network call (test-setup.ts chặn fetch), 0 WebGL thật (SSR — effect không chạy).
 */

registerAllSimulations();

const mod = makeNetworkModule();

// client → router → isp → server, cộng một switch NGOÀI route (kiểm hàng chiều sâu)
const CONFIG = {
  nodes: [
    { id: "client", type: "client" as const },
    { id: "router", type: "router" as const },
    { id: "isp", type: "isp" as const },
    { id: "server", type: "server" as const },
    { id: "sw", type: "switch" as const },
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

function initState(): NetworkState {
  const r = mod.validateConfig(CONFIG);
  if (!r.ok) throw new Error(r.error);
  return mod.init(r.config);
}

function envelope(): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: "network.packet_routing",
    domain: "network",
    visual_mode: "2d",
    title: "t",
    description: null,
    config: CONFIG,
    notes: null,
  };
}

describe("(10) hợp đồng module: 2D + 3D trên CÙNG một module", () => {
  it("network khai đủ hai mode, cả hai đều có renderer thật", () => {
    expect(mod.supportedVisualModes).toEqual(["2d", "3d"]);
    expect(availableVisualModes(mod)).toEqual(["2d", "3d"]);
    expect(rendererFor(mod, "2d")).toBe(mod.Workspace);
    expect(rendererFor(mod, "3d")).toBeDefined();
    expect(rendererFor(mod, "3d")).not.toBe(mod.Workspace);
  });

  it("(9)(no-fork) id giữ nguyên — không có network.packet_routing_3d", () => {
    expect(mod.id).toBe("network.packet_routing");
  });
});

describe("(11)(12) hai renderer đọc CÙNG authoritative state", () => {
  it("cùng một state → cả 2D lẫn 3D kể CÙNG narration của CÙNG bước", () => {
    const s0 = initState();
    const s2 = mod.timeline!.goToStep(s0, 2) as NetworkState;
    const narration2 = s2.steps[s2.cursor].narration;

    const html2d = renderToString(
      <NetworkWorkspace config={CONFIG} state={s2} busy={false} dispatch={() => {}} />,
    );
    const html3d = renderToString(
      <Network3DWorkspace config={CONFIG} state={s2} busy={false} dispatch={() => {}} />,
    );
    expect(html2d).toContain(narration2);
    expect(html3d).toContain(narration2);
  });

  it("packetAt (id nút ngữ nghĩa) là thứ DUY NHẤT định vị gói tin — layout3d chỉ tra cứu", () => {
    const s = initState();
    const pos = layout3d(s.nodes, s.route);
    for (let i = 0; i < mod.timeline!.stepCount(s); i++) {
      const at = (mod.timeline!.goToStep(s, i) as NetworkState).steps[i].packetAt;
      expect(pos[at]).toBeDefined(); // mọi packetAt đều có chỗ đứng trong bố cục renderer
    }
  });
});

describe("layout3d — bố cục RENDERER-OWNED, tất định", () => {
  it("route nằm hàng trước (z=0) theo thứ tự; nút ngoài route lùi vào chiều sâu", () => {
    const s = initState();
    const pos = layout3d(s.nodes, s.route);
    expect(Object.keys(pos).sort()).toEqual(s.nodes.map((n) => n.id).sort());
    // hàng route: z = 0, x tăng dần theo thứ tự route
    const xs = s.route.map((id) => pos[id].x);
    for (const id of s.route) expect(pos[id].z).toBe(0);
    expect([...xs].sort((a, b) => a - b)).toEqual(xs);
    // nút ngoài route: lùi về sau (z âm) — chiều sâu là giá trị 3D thêm vào
    expect(pos.sw.z).toBeLessThan(0);
    // tất định: gọi lại cho kết quả y hệt
    expect(layout3d(s.nodes, s.route)).toEqual(pos);
  });
});

describe("(13)(16) store: đổi renderer không đụng engine", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("(13) route BFS y hệt trước/sau khi đổi mode", () => {
    useAppStore.getState().loadEnvelope(envelope());
    const routeBefore = (useAppStore.getState().active!.state as NetworkState).route;
    useAppStore.getState().setVisualMode("3d");
    const routeAfter = (useAppStore.getState().active!.state as NetworkState).route;
    expect(routeAfter).toBe(routeBefore); // cùng THAM CHIẾU — không tính lại
    expect(routeAfter).toEqual(["client", "router", "isp", "server"]);
  });

  it("(16) đổi mode liên tục nhiều lần: state + cursor nguyên vẹn", () => {
    useAppStore.getState().loadEnvelope(envelope());
    useAppStore.getState().nextStep();
    useAppStore.getState().nextStep();
    const stateBefore = useAppStore.getState().active!.state;
    for (let i = 0; i < 6; i++) {
      useAppStore.getState().setVisualMode(i % 2 === 0 ? "3d" : "2d");
    }
    expect(useAppStore.getState().active!.state).toBe(stateBefore);
    expect((useAppStore.getState().active!.state as NetworkState).cursor).toBe(2);
  });
});

describe("(14)(15) prediction — MỘT capability cho cả hai renderer", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("(14) đang ở 3D: dự đoán vẫn chấm bằng BFS engine, kết quả là dữ liệu", () => {
    useAppStore.getState().loadEnvelope(envelope());
    useAppStore.getState().setVisualMode("3d");

    const s = useAppStore.getState().active!.state as NetworkState;
    useAppStore.getState().submitPrediction(s.route[1]);

    const after = useAppStore.getState();
    expect(after.visualMode).toBe("3d");
    expect(after.prediction!.verdict).toBe("correct");
    // KHÔNG có PredictionBar 3D riêng: capability là của MODULE, không của renderer
    expect(mod.predict).toBeDefined();
  });

  it("(15) dự đoán SAI không làm sai lệch route canonical — ở cả hai mode", () => {
    useAppStore.getState().loadEnvelope(envelope());
    const before = JSON.stringify(useAppStore.getState().active!.state);

    useAppStore.getState().setVisualMode("3d");
    useAppStore.getState().submitPrediction("sw"); // kề router? không — kề client? không → sai
    expect(useAppStore.getState().prediction!.verdict).toBe("incorrect");
    expect(JSON.stringify(useAppStore.getState().active!.state)).toBe(before);

    useAppStore.getState().clearPrediction();
    useAppStore.getState().setVisualMode("2d");
    expect(JSON.stringify(useAppStore.getState().active!.state)).toBe(before);
  });
});

describe("(17)(18) authoritative state SẠCH dữ liệu trình bày 3D", () => {
  it("không camera/mesh/toạ độ nào lọt vào NetworkState — trước và sau khi có 3D", () => {
    const s = initState();
    // Khoá đúng bộ khoá M7.FREEZE — thêm 3D KHÔNG thêm trường nào vào state.
    expect(Object.keys(s).sort()).toEqual(
      ["cursor", "destination", "links", "nodes", "route", "source", "steps"].sort(),
    );
    const dump = JSON.stringify(s);
    for (const forbidden of ["camera", "position", "mesh", "vector", "layout", "webgl"]) {
      expect(dump.toLowerCase()).not.toContain(forbidden);
    }
    expect(dump).not.toMatch(/"x":\s*-?\d/);
    expect(dump).not.toMatch(/"y":\s*-?\d/);
    expect(dump).not.toMatch(/"z":\s*-?\d/);
  });

  it("store cũng không giữ dữ liệu 3D: visualMode là chuỗi trình bày duy nhất", () => {
    useAppStore.getState().reset();
    useAppStore.getState().loadEnvelope(envelope());
    useAppStore.getState().setVisualMode("3d");
    const snapshot = useAppStore.getState();
    expect(snapshot.visualMode).toBe("3d");
    const engineDump = JSON.stringify(snapshot.active!.state);
    expect(engineDump).not.toMatch(/"z":\s*-?\d/);
    expect(engineDump.toLowerCase()).not.toContain("camera");
  });
});

describe("(19) WebGL fallback tử tế", () => {
  it("môi trường không có WebGL: trả null, KHÔNG ném lỗi", () => {
    expect(tryCreateWebGLRenderer()).toBeNull();
  });

  it("thông điệp fallback hướng người dùng quay về 2D (tiếng Việt, user-facing)", () => {
    expect(WEBGL_FALLBACK_MESSAGE).toContain("WebGL");
    expect(WEBGL_FALLBACK_MESSAGE).toContain("2D");
  });

  it("SSR (chưa chạy effect): component 3D vẫn render container + narration, không văng lỗi", () => {
    const s = initState();
    const html = renderToString(
      <Network3DWorkspace config={CONFIG} state={s} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain("three-container");
    expect(html).toContain(s.steps[0].narration);
    expect(html).toContain("Góc nhìn"); // nút reset CAMERA — không phải reset mô phỏng
  });
});

describe("(M10) 3D meaning metadata — honest classification", () => {
  it("packet_routing khai threeD.role='architectural_poc' (Z chỉ là bố cục)", () => {
    expect(mod.threeD).toBeDefined();
    expect(mod.threeD!.role).toBe("architectural_poc");
    expect(mod.threeD!.meaningOfZ.toLowerCase()).toContain("bố cục");
  });
});
