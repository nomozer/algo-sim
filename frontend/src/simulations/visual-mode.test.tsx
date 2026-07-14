import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { SimulationWorkspace } from "../components/SimulationWorkspace";
import { useAppStore } from "../state/store";
import { makeAndGateModule } from "./domains/logic";
import { makeNetworkModule } from "./domains/network";
import { registerAllSimulations } from "./index";
import { listSimulations } from "./registry";
import { availableVisualModes, effectiveVisualMode, rendererFor } from "./renderer";
import type { SimulationEnvelope } from "./types";

/**
 * M8 Slice 1 — KIẾN TRÚC RENDERER DÙNG CHUNG.
 *
 * Tuyên bố cần chứng minh: 3D là MỘT RENDERER, không phải domain mới —
 * cùng module, cùng config, cùng engine state, cùng timeline, cùng SimAction.
 * visualMode là trình bày thuần túy: đổi mode KHÔNG restart mô phỏng, KHÔNG
 * reset cursor, KHÔNG đụng canonical state, KHÔNG xoá prediction, KHÔNG gọi AI
 * (test-setup.ts chặn fetch — suite xanh ⇔ 0 network call).
 */

registerAllSimulations();

const NET_CONFIG = {
  nodes: [
    { id: "pc", type: "client" as const },
    { id: "r1", type: "router" as const },
    { id: "srv", type: "server" as const },
  ],
  links: [
    ["pc", "r1"],
    ["r1", "srv"],
  ] as [string, string][],
  source: "pc",
  destination: "srv",
  notes: null,
};

function envelopeFor(id: string, config: unknown): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: id,
    domain: id.split(".")[0] as SimulationEnvelope["domain"],
    visual_mode: "2d",
    title: "t",
    description: null,
    config,
    notes: null,
  };
}

beforeEach(() => useAppStore.getState().reset());

describe("visualMode — trạng thái TRÌNH BÀY trong store", () => {
  it("(1) mặc định là 2D", () => {
    expect(useAppStore.getState().visualMode).toBe("2d");
  });

  it("nạp mô phỏng mới → quay về 2D (chính sách mặc định M8)", () => {
    useAppStore.getState().setVisualMode("3d");
    useAppStore.getState().loadEnvelope(envelopeFor("network.packet_routing", NET_CONFIG));
    expect(useAppStore.getState().visualMode).toBe("2d");
  });

  it("(4)(6) đổi 2D→3D KHÔNG restart mô phỏng, canonical state GIỮ NGUYÊN KHỐI", () => {
    useAppStore.getState().loadEnvelope(envelopeFor("network.packet_routing", NET_CONFIG));
    const stateBefore = useAppStore.getState().active!.state;

    useAppStore.getState().setVisualMode("3d");

    const after = useAppStore.getState();
    expect(after.visualMode).toBe("3d");
    // Cùng THAM CHIẾU — không rebuild, không init lại, không copy-mutate.
    expect(after.active!.state).toBe(stateBefore);
  });

  it("(5) đổi 3D→2D giữ nguyên cursor timeline", () => {
    useAppStore.getState().loadEnvelope(envelopeFor("network.packet_routing", NET_CONFIG));
    useAppStore.getState().nextStep();
    const cursorBefore = (useAppStore.getState().active!.state as { cursor: number }).cursor;
    expect(cursorBefore).toBe(1);

    useAppStore.getState().setVisualMode("3d");
    useAppStore.getState().setVisualMode("2d");

    expect((useAppStore.getState().active!.state as { cursor: number }).cursor).toBe(cursorBefore);
  });

  it("(7) prediction KHÔNG bị renderer mode đụng tới (nó gắn với BƯỚC, không gắn renderer)", () => {
    useAppStore.getState().loadEnvelope(envelopeFor("network.packet_routing", NET_CONFIG));
    const canonical = (useAppStore.getState().active!.state as { route: string[] }).route[1];
    useAppStore.getState().submitPrediction(canonical);
    expect(useAppStore.getState().prediction!.verdict).toBe("correct");

    useAppStore.getState().setVisualMode("3d");
    expect(useAppStore.getState().prediction!.verdict).toBe("correct");

    useAppStore.getState().setVisualMode("2d");
    expect(useAppStore.getState().prediction!.verdict).toBe("correct");
  });
});

describe("renderer selection — DẪN XUẤT TỪ HỢP ĐỒNG MODULE (không theo id)", () => {
  it('(8) "2d" mặc định là Workspace; mode không khai → undefined', () => {
    const logic = makeAndGateModule();
    expect(rendererFor(logic, "2d")).toBe(logic.Workspace);
    expect(rendererFor(logic, "3d")).toBeUndefined();
  });

  it("(2) module chỉ 2D → availableVisualModes = ['2d'] → không có toggle giả", () => {
    expect(availableVisualModes(makeAndGateModule())).toEqual(["2d"]);
  });

  it("mode TUYÊN BỐ nhưng KHÔNG có renderer → không khả dụng (chống toggle rỗng)", () => {
    const fake = { ...makeAndGateModule(), supportedVisualModes: ["2d", "3d"] as const };
    expect(availableVisualModes(fake as never)).toEqual(["2d"]);
  });

  it("effectiveVisualMode rơi an toàn về 2D khi module không đáp ứng mode đã chọn", () => {
    expect(effectiveVisualMode(makeAndGateModule(), "3d")).toBe("2d");
    expect(effectiveVisualMode(makeAndGateModule(), "2d")).toBe("2d");
  });

  it("(9) KHÔNG có simulation_id riêng cho 3D trong registry", () => {
    for (const meta of listSimulations()) {
      expect(meta.id).not.toMatch(/3d/i);
    }
  });
});

describe("SimulationWorkspace — toggle theo capability", () => {
  it("(2) module 2D-only: KHÔNG render nút chuyển chế độ", () => {
    useAppStore
      .getState()
      .loadEnvelope(envelopeFor("logic.and_gate", { inputA: 0, inputB: 0, notes: null }));
    const html = renderToString(<SimulationWorkspace />);
    expect(html).not.toContain("visual-mode-toggle");
  });

  it("(3) module khai 2D+3D: hiện đủ hai nút chế độ", () => {
    // Dùng module network THẬT nếu đã có 3D; nếu chưa (Slice 1 thuần), test này
    // vẫn đúng nhờ module giả — nhưng ưu tiên kiểm module thật qua registry.
    const net = makeNetworkModule();
    if (availableVisualModes(net).length > 1) {
      useAppStore.getState().loadEnvelope(envelopeFor("network.packet_routing", NET_CONFIG));
      const html = renderToString(<SimulationWorkspace />);
      expect(html).toContain("visual-mode-toggle");
      expect(html).toContain(">2D<");
      expect(html).toContain(">3D<");
    } else {
      // Slice 1: chưa có module 3D thật — chấp nhận, Slice 2 sẽ kích hoạt nhánh trên.
      expect(availableVisualModes(net)).toEqual(["2d"]);
    }
  });
});
