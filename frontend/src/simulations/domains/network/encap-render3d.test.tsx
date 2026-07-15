import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { buildEncapState, LAYERS, type EncapConfig, type EncapState } from "./encap-model";
import { EncapWorkspace, EncapInspector } from "./encap-ui";
import {
  layerDepth, sideX, Encap3DWorkspace, tryCreateWebGLRenderer, ENCAP_WEBGL_FALLBACK,
} from "./encap-ui3d";

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
