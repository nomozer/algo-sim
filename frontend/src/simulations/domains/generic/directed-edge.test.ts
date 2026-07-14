import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { makeGenericModule } from "./index";
import { GenericWorkspace } from "./ui";
import { validateGenericConfig } from "./validate";
import type { SimulationSpec } from "./model";

/**
 * M8-PRE (S2): mirror TS của `directed` trên edge.
 *
 * Config được validate ở CẢ HAI phía (hai tầng). Nếu mirror này lệch với
 * backend, spec hợp lệ ở server sẽ bị frontend từ chối (hoặc ngược lại) —
 * đúng loại drift mà kiến trúc hai tầng phải chống.
 */

function spec(objects: unknown[]): Record<string, unknown> {
  return {
    dsl_version: "1.0",
    title: "Hệ thống quản lí điểm",
    objects,
    rules: [],
    interactions: [],
    processes: [],
  };
}

const SYS_OBJECTS = [
  { id: "gv", type: "node", node_type: "actor", label: "Giáo viên", x: 15, y: 30 },
  { id: "nhap", type: "node", node_type: "process", label: "Nhập điểm", x: 50, y: 30 },
  { id: "kho", type: "node", node_type: "data_store", label: "CSDL điểm", x: 85, y: 30 },
  { id: "f1", type: "edge", from: "gv", to: "nhap", directed: true },
  { id: "f2", type: "edge", from: "nhap", to: "kho", directed: true },
];

describe("directed edge — mirror validator TS", () => {
  it("giữ directed=true trên edge (sơ đồ luồng dữ liệu)", () => {
    const res = validateGenericConfig(spec(SYS_OBJECTS));
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    const edges = s.objects.filter((o) => o.type === "edge");
    expect(edges.map((e) => e.directed)).toEqual([true, true]);
  });

  it("edge KHÔNG khai directed thì giữ nguyên như cũ (thuần bổ sung)", () => {
    const res = validateGenericConfig(
      spec([
        { id: "a", type: "node", x: 10, y: 10 },
        { id: "b", type: "node", x: 40, y: 40 },
        { id: "e", type: "edge", from: "a", to: "b" },
      ]),
    );
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    const edge = s.objects.find((o) => o.type === "edge")!;
    expect(edge.directed).toBeUndefined(); // không tự bịa mặc định
  });

  it("directed không phải bool THẬT → bỏ qua (khớp backend)", () => {
    for (const bad of [1, 0, "true", "yes", null]) {
      const res = validateGenericConfig(
        spec([
          { id: "a", type: "node", x: 10, y: 10 },
          { id: "b", type: "node", x: 40, y: 40 },
          { id: "e", type: "edge", from: "a", to: "b", directed: bad },
        ]),
      );
      expect(res.ok).toBe(true);
      const s = (res as { ok: true; config: SimulationSpec }).config;
      expect(s.objects.find((o) => o.type === "edge")!.directed).toBeUndefined();
    }
  });

  it("SUY directed cho luồng hệ thống khi LLM không khai (mirror backend)", () => {
    const objs = SYS_OBJECTS.map((o) => {
      const { directed: _drop, ...rest } = o as Record<string, unknown>;
      return rest;
    });
    const res = validateGenericConfig(spec(objs));
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    const edges = s.objects.filter((o) => o.type === "edge");
    expect(edges.every((e) => e.directed === true)).toBe(true);
  });

  it("KHÔNG suy directed cho topology mạng (liên kết hai chiều)", () => {
    const res = validateGenericConfig(
      spec([
        { id: "pc", type: "node", node_type: "client", x: 10, y: 50 },
        { id: "r", type: "node", node_type: "router", x: 50, y: 50 },
        { id: "e1", type: "edge", from: "pc", to: "r" },
      ]),
    );
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    expect(s.objects.find((o) => o.type === "edge")!.directed).toBeUndefined();
  });

  it("directed trên object không phải edge → bỏ qua", () => {
    const res = validateGenericConfig(spec([{ id: "n", type: "node", x: 10, y: 10, directed: true }]));
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    expect(s.objects[0].directed).toBeUndefined();
  });

  it("node_type tự do — nhận vai trò hệ thống ngoài từ vựng gợi ý", () => {
    const res = validateGenericConfig(
      spec([{ id: "n", type: "node", node_type: "bo_phan_kho", x: 10, y: 10 }]),
    );
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    expect(s.objects[0].node_type).toBe("bo_phan_kho");
  });
});

/**
 * M8-PRE plan C: nén dư thừa an toàn (mirror backend `compact_redundant_labels`).
 * Hai tầng validator phải cho ra CÙNG một spec, nếu không spec sửa cục bộ sẽ lệch server.
 */
describe("nén dư thừa an toàn — mirror backend", () => {
  const NODES = [
    { id: "gv", type: "node", node_type: "actor", label: "Giáo viên", x: 10, y: 30 },
    { id: "nhap", type: "node", node_type: "process", label: "Nhập điểm", x: 30, y: 30 },
    { id: "kho", type: "node", node_type: "data_store", label: "CSDL điểm", x: 50, y: 30 },
    { id: "bc", type: "node", node_type: "output", label: "Bảng điểm", x: 70, y: 30 },
    { id: "hs", type: "node", node_type: "actor", label: "Học sinh", x: 90, y: 30 },
  ];
  const EDGES = [
    ["gv", "nhap", "nhập điểm"],
    ["nhap", "kho", "ghi dữ liệu"],
    ["kho", "bc", "kết xuất"],
    ["bc", "hs", "xem điểm"],
    ["hs", "gv", "phản hồi"],
    ["nhap", "bc", "in nhanh"],
  ].map(([from, to, label], i) => ({ id: `e${i}`, type: "edge", from, to, label }));
  const DUP = [...NODES, ...EDGES].map((o) => ({
    id: `lb_${o.id}`,
    type: "label",
    label: o.label,
    x: 10,
    y: 40,
  }));

  it("vượt hạn mức vì label TRÙNG → nén lại và hợp lệ, không mất nội dung", () => {
    const res = validateGenericConfig(spec([...NODES, ...EDGES, ...DUP])); // 22 object
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    expect(s.objects).toHaveLength(11);
    expect(s.objects.some((o) => o.type === "label")).toBe(false);
    for (const o of [...NODES, ...EDGES]) {
      expect(s.objects.some((x) => x.label === o.label)).toBe(true);
    }
  });

  it("label CÓ NGHĨA (không trùng) → KHÔNG gỡ; vượt hạn mức thì vẫn từ chối", () => {
    const unique = Array.from({ length: 11 }, (_, i) => ({
      id: `note${i}`,
      type: "label",
      label: `Ghi chú số ${i}`,
      x: 5,
      y: 5,
    }));
    const res = validateGenericConfig(spec([...NODES, ...EDGES, ...unique]));
    expect(res.ok).toBe(false);
    expect((res as { ok: false; error: string }).error).toContain("1–20");
  });

  it("cảnh TRONG hạn mức không bị đụng tới (0 regression)", () => {
    const res = validateGenericConfig(
      spec([...NODES.slice(0, 2), { id: "lb_gv", type: "label", label: "Giáo viên", x: 5, y: 5 }]),
    );
    expect(res.ok).toBe(true);
    const s = (res as { ok: true; config: SimulationSpec }).config;
    expect(s.objects.map((o) => o.id)).toEqual(["gv", "nhap", "lb_gv"]);
  });
});

/**
 * Mũi tên phải THẤY ĐƯỢC: luồng dữ liệu mà không nhìn ra chiều thì sơ đồ vô
 * nghĩa về mặt sư phạm (đây chính là lỗ hổng PRE-M8 audit tìm ra).
 */
describe("renderer — mũi tên cho edge có chiều", () => {
  const mod = makeGenericModule();

  function renderSpec(objects: unknown[]): string {
    const res = validateGenericConfig(spec(objects));
    expect(res.ok).toBe(true);
    const config = (res as { ok: true; config: SimulationSpec }).config;
    return renderToString(
      createElement(GenericWorkspace, {
        config,
        state: mod.init(config),
        busy: false,
        dispatch: () => {},
      }),
    );
  }

  it("edge directed → vẽ marker mũi tên", () => {
    const html = renderSpec(SYS_OBJECTS);
    expect(html).toContain('id="gen-arrow"'); // marker được định nghĩa
    expect(html).toContain("url(#gen-arrow)"); // và ĐƯỢC DÙNG trên line
  });

  it("edge KHÔNG directed → KHÔNG mũi tên (cảnh cũ không đổi)", () => {
    const html = renderSpec([
      { id: "a", type: "node", x: 20, y: 20 },
      { id: "b", type: "node", x: 60, y: 60 },
      { id: "e", type: "edge", from: "a", to: "b" },
    ]);
    expect(html).not.toContain("url(#gen-arrow)");
  });
});
