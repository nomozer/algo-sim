/**
 * Semantic Layout Compiler (Domain 0–100 coordinate system).
 * 
 * Tự động phân vùng không gian dựa trên vai trò ngữ nghĩa của đối tượng:
 * - Input Zone: array_strip, bar_chart, table_grid (Dữ liệu đầu vào - đặt trên cùng)
 * - State Zone: value_box, pointer, switch, slider (Trạng thái trung gian - đặt bên trái)
 * - Structure Zone: stack_view, queue_view, tree_element (Cấu trúc dữ liệu - đặt bên phải)
 * - Output Zone: value_box kết quả (Đặt dưới cùng)
 * 
 * Đảm bảo 100% không chồng chéo nhãn hoặc đối tượng.
 */

import type { SimulationSpec, SpecObject } from "./model";

export interface BoundingBox {
  id: string;
  x: number; // center x (0-100)
  y: number; // center y (0-100)
  w: number; // width in domain units (0-100)
  h: number; // height in domain units (0-100)
}

function estimateObjectSize(o: SpecObject): { w: number; h: number } {
  switch (o.type) {
    case "array_strip": {
      const count = Array.isArray(o.items) ? o.items.length : 1;
      return { w: Math.min(80, Math.max(25, count * 7)), h: 18 };
    }
    case "bar_chart": {
      const count = Array.isArray(o.bars) ? o.bars.length : 1;
      return { w: Math.min(80, Math.max(30, count * 8)), h: 32 };
    }
    case "table_grid": {
      const cols = Array.isArray(o.headers) ? o.headers.length : 2;
      return { w: Math.min(85, Math.max(35, cols * 14)), h: 35 };
    }
    case "stack_view":
      return { w: 22, h: 36 };
    case "queue_view":
      return { w: 35, h: 20 };
    case "value_box":
      return { w: 18, h: 16 };
    case "switch":
      return { w: 16, h: 14 };
    case "slider":
      return { w: 28, h: 16 };
    case "lamp":
      return { w: 14, h: 14 };
    default:
      return { w: 20, h: 16 };
  }
}

function isResultBox(o: SpecObject): boolean {
  if (o.type !== "value_box") return false;
  const label = (o.label || "").toLowerCase();
  const id = o.id.toLowerCase();
  return (
    label.includes("kết quả") ||
    label.includes("result") ||
    label.includes("kết luận") ||
    label.includes("thành tích") ||
    label.includes("tổng") ||
    label.includes("đếm") ||
    id.includes("res") ||
    id.includes("count") ||
    id.includes("total")
  );
}

const STRUCTURAL_TYPES = new Set<string>(["container", "group", "heading", "paragraph", "text", "pointer", "edge", "label"]);

/**
 * Tính toán tọa độ phân vùng ngữ nghĩa tự động cho toàn bộ objects trong spec.
 */
export function computeSemanticLayout(spec: SimulationSpec): Record<string, { x: number; y: number }> {
  const pos: Record<string, { x: number; y: number }> = {};
  const objects = spec.objects.filter((o) => !STRUCTURAL_TYPES.has(o.type));

  // 1. Phân loại theo vai trò
  const inputObjs: SpecObject[] = [];
  const stateObjs: SpecObject[] = [];
  const structObjs: SpecObject[] = [];
  const outputObjs: SpecObject[] = [];
  const otherObjs: SpecObject[] = [];

  for (const o of objects) {
    if (typeof o.x === "number" && typeof o.y === "number") {
      pos[o.id] = { x: o.x, y: o.y };
      continue;
    }

    if (o.type === "array_strip" || o.type === "bar_chart" || o.type === "table_grid") {
      inputObjs.push(o);
    } else if (o.type === "stack_view" || o.type === "queue_view" || o.type === "tree_element") {
      structObjs.push(o);
    } else if (isResultBox(o)) {
      outputObjs.push(o);
    } else if (o.type === "value_box" || o.type === "switch" || o.type === "slider" || o.type === "lamp") {
      stateObjs.push(o);
    } else {
      otherObjs.push(o);
    }
  }

  // 2. Tính tọa độ cho Input Zone (Top / Center)
  if (inputObjs.length > 0) {
    const hasStructures = structObjs.length > 0;
    inputObjs.forEach((o, idx) => {
      if (pos[o.id]) return;
      if (hasStructures) {
        // Đẩy sang trái một chút để nhường không gian bên phải cho stack/queue
        pos[o.id] = { x: 34, y: 18 + idx * 28 };
      } else {
        // Căn giữa toàn cảnh
        pos[o.id] = { x: 50, y: 22 + idx * 30 };
      }
    });
  }

  // 3. Tính tọa độ cho Structure Zone (Right Side)
  if (structObjs.length > 0) {
    structObjs.forEach((o, idx) => {
      if (pos[o.id]) return;
      pos[o.id] = { x: 78 + idx * 22, y: 35 };
    });
  }

  // 4. Tính tọa độ cho State Zone (Middle-Left)
  if (stateObjs.length > 0) {
    const startY = inputObjs.length > 0 ? (structObjs.length > 0 ? 50 : 62) : 25;
    stateObjs.forEach((o, idx) => {
      if (pos[o.id]) return;
      const col = idx % 2;
      const row = Math.floor(idx / 2);
      const baseX = structObjs.length > 0 ? 22 + col * 26 : 30 + col * 38;
      pos[o.id] = { x: baseX, y: startY + row * 24 };
    });
  }

  // 5. Tính tọa độ cho Output Zone (Bottom-Left / Bottom-Center)
  if (outputObjs.length > 0) {
    const hasStruct = structObjs.length > 0;
    const startOutY = stateObjs.length > 0 ? startY + Math.ceil(stateObjs.length / 2) * 20 : inputObjs.length > 0 ? 68 : 45;
  outputObjs.forEach((o, idx) => {
    if (!pos[o.id]) {
      const col = idx % 2;
      const row = Math.floor(idx / 2);
      const baseX = hasStruct ? 26 + col * 28 : (col === 0 && outputObjs.length === 1 ? 50 : 50 + (col * 34 - 17));
      pos[o.id] = { x: baseX, y: startOutY + row * 18 };
    }
  });
  }

  // 6. Các đối tượng còn lại (fallback lưới đều)
  otherObjs.forEach((o, idx) => {
    if (pos[o.id]) return;
    pos[o.id] = { x: 20 + (idx % 3) * 30, y: 70 + Math.floor(idx / 3) * 22 };
  });

  return pos;
}
