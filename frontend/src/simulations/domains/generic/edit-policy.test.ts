import { describe, expect, it } from "vitest";
import { makeAlgorithmModule } from "../algorithm";
import { makeAndGateModule } from "../logic";
import { makeBinaryModule } from "../binary";
import { makeNetworkModule } from "../network";
import { makeGenericModule } from "./index";
import { checkOpsAgainstPolicy, editPolicyOf, hasMeaningfulEditAffordance } from "./edit-policy";
import type { SimulationSpec } from "./model";
import { validateAndApplyPatch } from "./patch";

/**
 * EditPolicy v1 (M7.14D) — affordance suy TỪ NĂNG LỰC cảnh, mirror
 * backend `app/simulation/edit_policy.py`. Cảnh generic KHÔNG còn nhận chung
 * một bộ công cụ.
 */

const mod = makeGenericModule();

function spec(raw: object): SimulationSpec {
  const r = mod.validateConfig(raw);
  if (!r.ok) throw new Error(r.error);
  return r.config;
}

const TRIANGLE = spec({
  dsl_version: "1.0",
  title: "Tam giác ABC",
  objects: [
    { id: "A", type: "node", x: 20, y: 70 },
    { id: "B", type: "node", x: 80, y: 70 },
    { id: "C", type: "node", x: 50, y: 20 },
    { id: "AB", type: "edge", from: "A", to: "B" },
  ],
  rules: [],
  interactions: [{ type: "drag", target: "C" }],
  processes: [{ type: "reveal_sequence", steps: [{ objects: ["A", "B"] }, { objects: ["AB"] }] }],
});

const WEB = spec({
  dsl_version: "1.0",
  title: "Trang giới thiệu",
  objects: [
    { id: "page", type: "container", text: "Trang" },
    { id: "h", type: "heading", text: "Xin chào", parent: "page" },
    { id: "p", type: "paragraph", text: "Đoạn văn.", parent: "page" },
  ],
  rules: [],
  interactions: [],
  processes: [],
});

const GENERIC_LOGIC = spec({
  dsl_version: "1.0",
  title: "Cổng AND",
  objects: [
    { id: "a", type: "switch", value: 0 },
    { id: "b", type: "switch", value: 0 },
    { id: "y", type: "lamp" },
  ],
  rules: [{ type: "boolean", op: "and", inputs: ["a", "b"], target: "y" }],
  interactions: [{ type: "toggle", target: "a" }],
  processes: [],
});

const GENERIC_BINARY = spec({
  dsl_version: "1.0",
  title: "Đổi nhị phân",
  objects: [
    { id: "b0", type: "switch", value: 1, weight: 8 },
    { id: "b1", type: "switch", value: 0, weight: 4 },
    { id: "out", type: "value_box" },
  ],
  rules: [{ type: "weighted_sum", inputs: ["b0", "b1"], weights: [8, 4], target: "out" }],
  interactions: [{ type: "toggle", target: "b0" }],
  processes: [],
});

const PACKET = spec({
  dsl_version: "1.0",
  title: "Gói tin",
  objects: [
    { id: "c", type: "node", node_type: "client" },
    { id: "s", type: "node", node_type: "server" },
    { id: "e1", type: "edge", from: "c", to: "s" },
    { id: "pkt", type: "moving_entity" },
  ],
  rules: [],
  interactions: [],
  processes: [{ type: "move_along_path", entity: "pkt", path: ["c", "s"] }],
});

describe("EditPolicy — affordance theo năng lực cảnh", () => {
  it("family suy từ cấu trúc spec (không tên bài/môn)", () => {
    expect(editPolicyOf(TRIANGLE).family).toBe("spatial");
    expect(editPolicyOf(WEB).family).toBe("structural");
    expect(editPolicyOf(GENERIC_LOGIC).family).toBe("value_only");
    expect(editPolicyOf(GENERIC_BINARY).family).toBe("value_only");
    expect(editPolicyOf(PACKET).family).toBe("observation");
  });

  it("cảnh structural: KHÔNG Thêm điểm/Nối, CÓ Thêm nội dung", () => {
    const p = editPolicyOf(WEB);
    expect(p.uiActions).toContain("add_content");
    expect(p.uiActions).toContain("delete");
    expect(p.uiActions).not.toContain("add_node");
    expect(p.uiActions).not.toContain("connect");
    expect(p.addableTypes).toEqual(expect.arrayContaining(["heading", "paragraph", "text"]));
    expect(p.addableTypes).not.toContain("node");
  });

  it("cảnh generic binary/logic: KHÔNG có công cụ sửa cấu trúc", () => {
    for (const scene of [GENERIC_LOGIC, GENERIC_BINARY]) {
      const p = editPolicyOf(scene);
      expect(p.uiActions).not.toContain("add_node");
      expect(p.uiActions).not.toContain("connect");
      expect(p.uiActions).not.toContain("delete");
      expect(p.addableTypes).toHaveLength(0);
    }
  });

  it("cảnh move_along_path: topology bị khóa", () => {
    const p = editPolicyOf(PACKET);
    expect(p.family).toBe("observation");
    expect(p.uiActions).not.toContain("add_node");
    expect(p.allowedOps).toEqual(["update_object"]);
  });

  it("cảnh spatial: giữ nguyên Thêm điểm/Nối/Xóa (không regression M7.14)", () => {
    const p = editPolicyOf(TRIANGLE);
    expect(p.uiActions).toEqual(expect.arrayContaining(["add_node", "connect", "delete"]));
  });

  it("cảnh LAI dùng precedence bảo thủ (limitation có chủ đích)", () => {
    const mixed = spec({
      dsl_version: "1.0",
      title: "Lai",
      objects: [
        { id: "page", type: "container", text: "Trang" },
        { id: "h", type: "heading", text: "Tiêu đề", parent: "page" },
        { id: "A", type: "node", x: 10, y: 10 },
      ],
      rules: [],
      interactions: [],
      processes: [],
    });
    expect(editPolicyOf(mixed).family).toBe("structural"); // structural > spatial
    expect(editPolicyOf(mixed).allowedOps).not.toContain("connect");
  });
});

describe("M7.14D.1 — không quảng bá chế độ Chỉnh sửa RỖNG", () => {
  it("value_only & observation: KHÔNG có affordance đáng kể → ẩn nút Chỉnh sửa", () => {
    for (const scene of [GENERIC_LOGIC, GENERIC_BINARY, PACKET]) {
      const p = editPolicyOf(scene);
      expect(p.uiActions.filter((a) => a !== "edit_text")).toHaveLength(0);
      expect(hasMeaningfulEditAffordance(p)).toBe(false);
    }
  });

  it("spatial & structural: CÓ affordance đáng kể → vẫn hiện Chỉnh sửa", () => {
    expect(hasMeaningfulEditAffordance(editPolicyOf(TRIANGLE))).toBe(true);
    expect(hasMeaningfulEditAffordance(editPolicyOf(WEB))).toBe(true);
  });

  it("suy từ POLICY, không hard-code theo loại object/tên cảnh", () => {
    // Cảnh value_only nhưng đổi tiêu đề/nhãn → vẫn ẩn (quyết định theo uiActions)
    const renamed = spec({
      ...GENERIC_LOGIC,
      title: "Tam giác giả danh",
    } as object);
    expect(hasMeaningfulEditAffordance(editPolicyOf(renamed))).toBe(false);

    // Backend policy KHÔNG bị xóa: update_object vẫn hợp lệ nếu gọi thẳng patch
    const res = validateAndApplyPatch(GENERIC_LOGIC, {
      operations: [{ op: "update_object", id: "a", fields: { label: "Công tắc A" } }],
    });
    expect(res.status).toBe("valid");
  });
});

describe("EditPolicy — enforce ở tầng patch (ẩn UI là KHÔNG đủ)", () => {
  it("structural + add node → policy.object_type_not_allowed", () => {
    const res = validateAndApplyPatch(WEB, {
      operations: [{ op: "add_object", object: { id: "P1", type: "node", x: 50, y: 50 } }],
    });
    expect(res.status).toBe("structurally_invalid");
    if (res.status === "structurally_invalid") {
      expect(res.reasonCode).toBe("policy.object_type_not_allowed");
    }
  });

  it("structural + add paragraph → chấp nhận", () => {
    const res = validateAndApplyPatch(WEB, {
      operations: [{ op: "add_object", object: { id: "p2", type: "paragraph", text: "Đoạn mới.", parent: "page" } }],
    });
    expect(res.status).toBe("valid");
    if (res.status === "valid") {
      expect(res.config.objects.some((o) => o.id === "p2")).toBe(true);
    }
  });

  it("structural + connect → policy.operation_not_allowed", () => {
    const res = validateAndApplyPatch(WEB, {
      operations: [{ op: "connect", from: "h", to: "p", edge_id: "e" }],
    });
    if (res.status === "structurally_invalid") {
      expect(res.reasonCode).toBe("policy.operation_not_allowed");
    } else {
      throw new Error("phải bị từ chối");
    }
  });

  it("move_along_path + add node → policy.path_topology_locked", () => {
    const res = validateAndApplyPatch(PACKET, {
      operations: [{ op: "add_object", object: { id: "r", type: "node" } }],
    });
    if (res.status === "structurally_invalid") {
      expect(res.reasonCode).toBe("policy.path_topology_locked");
    } else {
      throw new Error("phải bị từ chối");
    }
  });

  it("spatial + thêm D nối A vẫn chạy (không regression)", () => {
    const res = validateAndApplyPatch(TRIANGLE, {
      operations: [
        { op: "add_object", object: { id: "D", type: "node", label: "D", x: 50, y: 92 } },
        { op: "connect", from: "A", to: "D", edge_id: "AD" },
      ],
    });
    expect(res.status).toBe("valid");
  });

  it("lỗi cấu trúc giữ namespace structure.* (không lẫn với policy.*)", () => {
    const res = validateAndApplyPatch(TRIANGLE, {
      operations: [{ op: "add_object", object: { id: "A", type: "node" } }], // id trùng
    });
    if (res.status === "structurally_invalid") {
      expect(res.reasonCode).toBe("structure.invalid");
    } else {
      throw new Error("phải bị từ chối");
    }
    expect(checkOpsAgainstPolicy(TRIANGLE, [{ op: "add_object", object: { type: "node" } }])).toBeNull();
  });
});

describe("Capability edit trên SimulationModule", () => {
  it("generic KHAI capability; 4 module chuyên biệt KHÔNG khai (mặc định an toàn)", () => {
    expect(mod.edit).toBeDefined();
    expect(mod.edit!.policyOf(TRIANGLE, mod.init(TRIANGLE)).uiActions).toContain("add_node");

    // Algorithm/Logic/Binary/Network: KHÔNG có edit → UI không bao giờ hiện
    // "Thêm điểm" cho các mô phỏng này.
    expect(makeAlgorithmModule("find_max").edit).toBeUndefined();
    expect(makeAndGateModule().edit).toBeUndefined();
    expect(makeBinaryModule().edit).toBeUndefined();
    expect(makeNetworkModule().edit).toBeUndefined();
  });

  it("policyOf suy theo CONFIG hiện tại, không phải hằng số của module", () => {
    expect(mod.edit!.policyOf(WEB, mod.init(WEB)).uiActions).not.toContain("add_node");
    expect(mod.edit!.policyOf(GENERIC_LOGIC, mod.init(GENERIC_LOGIC)).uiActions).not.toContain("add_node");
  });
});
