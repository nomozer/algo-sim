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
