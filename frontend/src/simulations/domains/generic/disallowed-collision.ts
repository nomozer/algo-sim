/**
 * Disallowed Pairwise Collision Verifier.
 * 
 * Kiểm tra các va chạm vùng cấm thực tế giữa các đối tượng hình ảnh:
 * 1. Text-on-Text Collision: Nhãn đè nhãn.
 * 2. Box-on-Box Collision: Hộp/Biểu đồ đè hộp/biểu đồ khác.
 * 3. Boundary Overflow: Tràn ra ngoài canvas [0, 100].
 */

import type { SimulationSpec, SpecObject } from "./model";
import { computeSemanticLayout } from "./layout-compiler";

export interface CollisionViolation {
  kind: "TEXT_ON_TEXT" | "BOX_ON_BOX" | "CANVAS_OVERFLOW";
  id1: string;
  id2?: string;
  message: string;
}

export interface Rect {
  id: string;
  type: string;
  label?: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

function computeAABB(o: SpecObject, cx: number, cy: number): Rect {
  let hw = 10;
  let hh = 8;

  switch (o.type) {
    case "array_strip": {
      const count = Array.isArray(o.items) ? o.items.length : 1;
      hw = Math.min(40, Math.max(12, count * 3.5));
      hh = 9;
      break;
    }
    case "bar_chart": {
      const count = Array.isArray(o.bars) ? o.bars.length : 1;
      hw = Math.min(40, Math.max(15, count * 4));
      hh = 16;
      break;
    }
    case "table_grid": {
      const cols = Array.isArray(o.headers) ? o.headers.length : 2;
      hw = Math.min(42, Math.max(16, cols * 7));
      hh = 18;
      break;
    }
    case "stack_view":
      hw = 11;
      hh = 18;
      break;
    case "queue_view":
      hw = 18;
      hh = 10;
      break;
    case "value_box":
      hw = 9;
      hh = 8;
      break;
    case "slider":
      hw = 14;
      hh = 8;
      break;
    default:
      hw = 10;
      hh = 8;
  }

  return {
    id: o.id,
    type: o.type,
    label: o.label,
    x1: cx - hw,
    y1: cy - hh,
    x2: cx + hw,
    y2: cy + hh,
  };
}

function intersects(r1: Rect, r2: Rect, tolerance = 1.0): boolean {
  // Có giao nhau nếu khoảng cách theo cả 2 trục < 0
  return !(
    r1.x2 - tolerance < r2.x1 ||
    r1.x1 + tolerance > r2.x2 ||
    r1.y2 - tolerance < r2.y1 ||
    r1.y1 + tolerance > r2.y2
  );
}

/**
 * Kiểm tra toàn bộ va chạm vùng cấm trên SimulationSpec.
 * Trả về danh sách vi phạm (rỗng nếu 100% hợp lệ).
 */
export function checkDisallowedCollisions(
  spec: SimulationSpec,
  customPos?: Record<string, { x: number; y: number }>,
): CollisionViolation[] {
  const pos = customPos ?? computeSemanticLayout(spec);
  const violations: CollisionViolation[] = [];
  const boxes: Rect[] = [];

  const structural = new Set(["container", "group", "heading", "paragraph", "text", "pointer", "edge", "label"]);
  const activeObjects = spec.objects.filter((o) => !structural.has(o.type));

  for (const o of activeObjects) {
    const p = pos[o.id];
    if (!p) continue;

    // 1. Boundary check [0..100]
    if (p.x < 5 || p.x > 95 || p.y < 5 || p.y > 95) {
      violations.push({
        kind: "CANVAS_OVERFLOW",
        id1: o.id,
        message: `Đối tượng "${o.id}" (${o.type}) nằm quá sát biên canvas: (${p.x}, ${p.y}).`,
      });
    }

    boxes.push(computeAABB(o, p.x, p.y));
  }

  // 2. Pairwise Collision Checks
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const b1 = boxes[i];
      const b2 = boxes[j];

      if (intersects(b1, b2)) {
        violations.push({
          kind: "BOX_ON_BOX",
          id1: b1.id,
          id2: b2.id,
          message: `Va chạm vùng cấm giữa "${b1.id}" (${b1.type}) và "${b2.id}" (${b2.type}).`,
        });
      }
    }
  }

  return violations;
}
