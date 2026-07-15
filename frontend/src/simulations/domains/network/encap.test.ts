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
