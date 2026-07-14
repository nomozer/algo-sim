import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { VisualModeToggle } from "../components/SimulationWorkspace";
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

describe("VisualModeToggle — affordance theo capability (component thuần, SSR được)", () => {
  // Lưu ý hạ tầng test: zustand v5 trả INITIAL state trong renderToString, nên
  // không SSR SimulationWorkspace-qua-store được — toggle được tách thành
  // component thuần theo props và test TRỰC TIẾP; phần dẫn xuất modes từ module
  // đã được khoá ở describe "renderer selection" phía trên.
  it("(2) module 2D-only → modes có 1 phần tử → KHÔNG render gì (không toggle giả)", () => {
    const modes = availableVisualModes(makeAndGateModule());
    expect(modes).toEqual(["2d"]);
    const html = renderToString(<VisualModeToggle modes={modes} mode="2d" onSelect={() => {}} />);
    expect(html).toBe("");
  });

  it("(3) module khai 2D+3D → hiện đủ hai nút, nút mode hiện tại được đánh dấu", () => {
    const modes = availableVisualModes(makeNetworkModule());
    expect(modes).toEqual(["2d", "3d"]);
    const html = renderToString(<VisualModeToggle modes={modes} mode="3d" onSelect={() => {}} />);
    expect(html).toContain("visual-mode-toggle");
    expect(html).toContain(">2D<");
    expect(html).toContain(">3D<");
    // nút 3D đang chọn có is-active
    expect(html).toMatch(/is-active[^>]*>3D</);
  });
});
