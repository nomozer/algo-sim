import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { buildEncapState, LAYERS, type EncapConfig, type EncapState } from "./encap-model";
import { EncapWorkspace, EncapInspector } from "./encap-ui";
import {
  layerDepth, sideX, Encap3DWorkspace, tryCreateWebGLRenderer, ENCAP_WEBGL_FALLBACK,
} from "./encap-ui3d";
import { makeEncapsulationModule } from "./encap";
import { registerAllSimulations } from "../../index";
import { availableVisualModes, rendererFor } from "../../renderer";
import { useAppStore } from "../../../state/store";
import type { SimulationEnvelope } from "../../types";

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

describe("(M10) 3D renderer — Z = tầng giao thức (nghĩa thật)", () => {
  it("layerDepth GIẢM đơn điệu theo tầng (Application 0 → Network Access sâu nhất)", () => {
    const depths = LAYERS.map(layerDepth);
    expect(depths[0]).toBe(0);
    for (let i = 1; i < depths.length; i++) expect(depths[i]).toBeLessThan(depths[i - 1]);
    expect(layerDepth("network_access")).toBe(-12);
    // tất định
    expect(LAYERS.map(layerDepth)).toEqual(depths);
  });

  it("sideX: máy gửi bên trái, máy nhận bên phải, đường truyền ở giữa", () => {
    expect(sideX("sender")).toBeLessThan(sideX("medium"));
    expect(sideX("medium")).toBeLessThan(sideX("receiver"));
    expect(sideX("medium")).toBe(0);
  });

  it("SSR: render container + narration + caption meaning_of_z, KHÔNG ném lỗi", () => {
    const html = renderToString(
      <Encap3DWorkspace config={CONFIG} state={at(1)} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain("three-container");
    expect(html).toContain("đoạn TCP");
    expect(html).toContain("Trục sâu"); // caption Z = tầng giao thức
  });

  it("môi trường không WebGL → tryCreateWebGLRenderer trả null; fallback trỏ về 2D", () => {
    expect(tryCreateWebGLRenderer()).toBeNull();
    expect(ENCAP_WEBGL_FALLBACK).toContain("2D");
  });

  it("3D KHÔNG tự tính PDU: narration đến từ state (không bịa)", () => {
    const html3d = renderToString(
      <Encap3DWorkspace config={CONFIG} state={at(3)} busy={false} dispatch={() => {}} />,
    );
    expect(html3d).toContain("gói IP trở thành khung");
  });
});

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

  it("(honesty) encapsulation là 3D SƯ PHẠM; meaningOfZ nói về tầng", () => {
    expect(emod.threeD!.role).toBe("pedagogical");
    expect(emod.threeD!.meaningOfZ).toContain("tầng");
  });
});
