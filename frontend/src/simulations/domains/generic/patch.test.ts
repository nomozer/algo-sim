import { describe, expect, it } from "vitest";
import {
  applyEditedSpec,
  findFreePosition,
  visibleContentBounds,
  type GenericState,
  type SimulationSpec,
} from "./model";
import { makeGenericModule } from "./index";
import { validateAndApplyPatch } from "./patch";

/**
 * Test SimulationPatch v1 phía frontend (M7.14) — song song test_patch.py:
 * cùng fixture tam giác, cùng luật cascade/reject, spec gốc nguyên vẹn.
 * Kèm helpers edit: findFreePosition / applyEditedSpec / visibleContentBounds.
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
    { id: "AC", type: "edge", from: "A", to: "C" },
    { id: "BC", type: "edge", from: "B", to: "C" },
  ],
  rules: [],
  interactions: [{ type: "drag", target: "C" }],
  processes: [
    {
      type: "reveal_sequence",
      steps: [{ objects: ["A", "B"] }, { objects: ["AB"] }, { objects: ["C"] }, { objects: ["AC", "BC"] }],
    },
  ],
});

describe("patch v1 — validate + apply (song song backend)", () => {
  it("thêm D và nối trong MỘT patch; spec gốc nguyên vẹn", () => {
    const before = JSON.stringify(TRIANGLE);
    const res = validateAndApplyPatch(TRIANGLE, {
      operations: [
        { op: "add_object", object: { id: "D", type: "node", label: "D", x: 50, y: 92 } },
        { op: "connect", from: "A", to: "D", edge_id: "AD" },
      ],
    });
    expect(res.status).toBe("valid");
    if (res.status === "valid") {
      const ids = new Set(res.config.objects.map((o) => o.id));
      expect(ids.has("D") && ids.has("AD")).toBe(true);
    }
    expect(JSON.stringify(TRIANGLE)).toBe(before);
  });

  it("id trùng / endpoint thiếu / type lạ / quá 10 ops → structurally_invalid", () => {
    const cases = [
      [{ op: "add_object", object: { id: "A", type: "node" } }],
      [{ op: "connect", from: "A", to: "Zzz", edge_id: "AZ" }],
      [{ op: "add_object", object: { id: "X", type: "hexagon" } }],
      Array.from({ length: 11 }, (_, i) => ({ op: "add_object", object: { id: `N${i}`, type: "node" } })),
    ];
    for (const operations of cases) {
      const res = validateAndApplyPatch(TRIANGLE, { operations: operations as never });
      expect(res.status, JSON.stringify(operations[0])).toBe("structurally_invalid");
    }
  });

  it("remove node cascade edges + interactions + reveal mentions", () => {
    const res = validateAndApplyPatch(TRIANGLE, { operations: [{ op: "remove_object", id: "C" }] });
    expect(res.status).toBe("valid");
    if (res.status === "valid") {
      const ids = new Set(res.config.objects.map((o) => o.id));
      expect(ids.has("C") || ids.has("AC") || ids.has("BC")).toBe(false);
      expect(res.config.interactions).toHaveLength(0); // drag C bị gỡ
      for (const p of res.config.processes) {
        for (const st of (p as { steps: { objects: string[] }[] }).steps) {
          expect(st.objects).not.toContain("C");
          expect(st.objects.length).toBeGreaterThan(0);
        }
      }
    }
  });

  it("remove object có semantic dependents (rule/process) → reject", () => {
    const gate = spec({
      dsl_version: "1.0",
      title: "AND",
      objects: [
        { id: "a", type: "switch", value: 0 },
        { id: "b", type: "switch", value: 0 },
        { id: "y", type: "lamp" },
      ],
      rules: [{ type: "boolean", op: "and", inputs: ["a", "b"], target: "y" }],
      interactions: [],
      processes: [],
    });
    // M7.14D: cảnh switch/lamp là VALUE_ONLY → EditPolicy chặn TRƯỚC (policy.*)
    const res = validateAndApplyPatch(gate, { operations: [{ op: "remove_object", id: "a" }] });
    expect(res.status).toBe("structurally_invalid");
    if (res.status === "structurally_invalid") expect(res.reasonCode).toBe("policy.operation_not_allowed");

    // Luật dependents ngữ nghĩa vẫn là chốt chặn ĐỘC LẬP — kiểm khi bỏ qua policy
    const raw = validateAndApplyPatch(gate, { operations: [{ op: "remove_object", id: "a" }] }, false);
    expect(raw.status).toBe("structurally_invalid");
    if (raw.status === "structurally_invalid") expect(raw.error).toContain("rule");
  });

  it("xóa tới mức mất hết tiến trình → guard bảo toàn diễn biến chặn", () => {
    const mini = spec({
      dsl_version: "1.0",
      title: "Hai điểm",
      objects: [
        { id: "A", type: "node" },
        { id: "B", type: "node" },
        { id: "bg", type: "label", label: "nền" },
      ],
      rules: [],
      interactions: [],
      processes: [{ type: "reveal_sequence", steps: [{ objects: ["A"] }, { objects: ["B"] }] }],
    });
    const res = validateAndApplyPatch(mini, {
      operations: [
        { op: "remove_object", id: "A" },
        { op: "remove_object", id: "B" },
      ],
    });
    expect(res.status).toBe("structurally_invalid");
    if (res.status === "structurally_invalid") expect(res.error).toContain("tiến trình");
  });

  it("update chỉ fields nội dung/vị trí; disconnect đúng edge", () => {
    const up = validateAndApplyPatch(TRIANGLE, {
      operations: [{ op: "update_object", id: "A", fields: { x: 30, label: "A'" } }],
    });
    expect(up.status).toBe("valid");
    const bad = validateAndApplyPatch(TRIANGLE, {
      operations: [{ op: "update_object", id: "AB", fields: { from: "C" } }],
    });
    expect(bad.status).toBe("structurally_invalid");
    const dis = validateAndApplyPatch(TRIANGLE, { operations: [{ op: "disconnect", edge_id: "BC" }] });
    expect(dis.status).toBe("valid");
    const disNode = validateAndApplyPatch(TRIANGLE, { operations: [{ op: "disconnect", edge_id: "A" }] });
    expect(disNode.status).toBe("structurally_invalid");
  });
});

describe("edit helpers — findFreePosition / applyEditedSpec / bounds", () => {
  it("findFreePosition không đè object cũ, tất định, tôn trọng hint khi trống", () => {
    const taken = [
      { x: 20, y: 70 },
      { x: 80, y: 70 },
      { x: 50, y: 20 },
    ];
    const p = findFreePosition(taken);
    expect(taken.every((t) => Math.hypot(t.x - p.x, t.y - p.y) >= 12)).toBe(true);
    expect(findFreePosition(taken)).toEqual(p); // tất định
    expect(findFreePosition(taken, { x: 50, y: 90 })).toEqual({ x: 50, y: 90 }); // hint trống → dùng
    const nudged = findFreePosition(taken, { x: 21, y: 71 }); // hint đè A → tránh
    expect(taken.every((t) => Math.hypot(t.x - nudged.x, t.y - nudged.y) >= 12)).toBe(true);
  });

  it("applyEditedSpec GIỮ pos đã kéo + base của id sống; object mới không đè", () => {
    let s = mod.init(TRIANGLE) as GenericState;
    s = { ...s, cursor: s.timeline.length - 1 };
    s = mod.apply(s, { type: "move", target: "C", x: 44, y: 33 }) as GenericState;
    expect(s.pos.C).toEqual({ x: 44, y: 33 });

    const res = validateAndApplyPatch(s.spec, {
      operations: [
        { op: "add_object", object: { id: "D", type: "node", label: "D" } }, // KHÔNG tọa độ
        { op: "connect", from: "A", to: "D", edge_id: "AD" },
      ],
    });
    expect(res.status).toBe("valid");
    if (res.status !== "valid") return;
    const next = applyEditedSpec(s, res.config);
    expect(next.spec).toBe(res.config);
    expect(next.pos.C).toEqual({ x: 44, y: 33 }); // vị trí đã kéo KHÔNG mất
    const d = next.pos.D;
    for (const id of ["A", "B", "C"]) {
      expect(Math.hypot(next.pos[id].x - d.x, next.pos[id].y - d.y)).toBeGreaterThanOrEqual(12);
    }
    expect(next.cursor).toBe(s.cursor); // cursor giữ (timeline cùng độ dài)
    expect(next.timeline.at(-1)?.visibleIds).toContain("D"); // object mới là nền — hiện ngay
  });

  it("visibleContentBounds: chỉ object visible; null cho cảnh structural", () => {
    const s0 = mod.init(TRIANGLE) as GenericState; // cursor 0: A, B
    const b0 = visibleContentBounds(s0);
    expect(b0).toEqual({ minX: 20, minY: 70, maxX: 80, maxY: 70 });
    const sEnd = { ...s0, cursor: s0.timeline.length - 1 };
    expect(visibleContentBounds(sEnd)).toEqual({ minX: 20, minY: 20, maxX: 80, maxY: 70 });

    const web = mod.init(
      spec({
        dsl_version: "1.0",
        title: "Trang",
        objects: [
          { id: "page", type: "container", text: "Trang" },
          { id: "h", type: "heading", text: "Tiêu đề", parent: "page" },
        ],
        rules: [],
        interactions: [],
        processes: [],
      }),
    ) as GenericState;
    expect(visibleContentBounds(web)).toBeNull();
  });

  it("drag chạm bounds → InteractionFeedback từ rule, không suy diễn ngữ nghĩa", () => {
    const bounded = spec({
      dsl_version: "1.0",
      title: "Điểm bị giới hạn",
      objects: [{ id: "M", type: "node", x: 50, y: 50 }],
      rules: [],
      interactions: [
        { type: "drag", target: "M", constraints: { bounds: { min_x: 30, max_x: 70 } } },
      ],
      processes: [],
    });
    let s = mod.init(bounded) as GenericState;
    s = mod.apply(s, { type: "move", target: "M", x: 95, y: 50 }) as GenericState;
    expect(s.pos.M.x).toBe(70); // clamp
    expect(s.feedback?.rule).toBe("drag_bounds");
    expect(s.feedback?.message).toContain("vùng tương tác");
    expect(s.feedback?.message).not.toContain("BC"); // KHÔNG suy diễn hình học
    // kéo về vị trí hợp lệ → feedback tự xóa
    s = mod.apply(s, { type: "move", target: "M", x: 50, y: 50 }) as GenericState;
    expect(s.feedback ?? null).toBeNull();
  });
});
