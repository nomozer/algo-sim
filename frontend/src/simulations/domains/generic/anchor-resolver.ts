/**
 * Semantic Anchor System (G5 / Shared Architecture).
 *
 * Tự động tính toán vị trí hiển thị (X, Y) của Pointer và Annotations
 * neo vào các thành phần ngữ nghĩa (array_strip, stack_view, queue_view,
 * table_grid, bar_chart, tree_element, node).
 *
 * Nguyên tắc: Renderer tự resolve vị trí theo kiểu đối tượng và chỉ số target_index,
 * loại bỏ hoàn toàn hardcode tọa độ hoặc can thiệp cục bộ cho từng bài toán.
 */

export type AnchorPoint = "top-center" | "bottom-center" | "left-center" | "right-center";

export interface ResolvedAnchor {
  x: number;
  y: number;
  direction: "down" | "up" | "left" | "right";
}

export function resolveSemanticAnchor(
  targetObj: any,
  targetPos: { x: number; y: number },
  targetIndex?: number,
  preferredAnchor: AnchorPoint = "top-center",
): ResolvedAnchor {
  if (!targetObj) {
    return { x: targetPos.x, y: targetPos.y, direction: "down" };
  }

  const otype = targetObj.type;
  const idx = typeof targetIndex === "number" ? Math.max(0, targetIndex) : 0;

  switch (otype) {
    case "array_strip": {
      const items = Array.isArray(targetObj.items)
        ? targetObj.items
        : typeof targetObj.text === "string"
        ? Array.from(targetObj.text)
        : [0];
      const count = Math.max(1, items.length);
      const safeIdx = Math.min(idx, count - 1);
      const cellW = 34;
      const cellH = 34;
      const totalW = count * cellW;
      const startX = targetPos.x - totalW / 2;
      const cellCenterX = startX + safeIdx * cellW + cellW / 2;

      if (preferredAnchor === "bottom-center") {
        return {
          x: cellCenterX,
          y: targetPos.y + cellH / 2 + 8,
          direction: "up",
        };
      }
      // Mặc định top-center: mũi tên trỏ xuống mép trên của ô
      return {
        x: cellCenterX,
        y: targetPos.y - cellH / 2 - 4,
        direction: "down",
      };
    }

    case "stack_view": {
      const items = Array.isArray(targetObj.items) ? targetObj.items : [];
      const itemH = 22;
      const boxW = 80;
      const capacity = targetObj.capacity ?? Math.max(4, items.length);
      const boxH = Math.max(80, capacity * itemH + 20);
      const safeIdx = Math.min(idx, Math.max(0, items.length - 1));
      const iy = targetPos.y + boxH / 2 - (safeIdx + 1) * itemH - 4 + itemH / 2;

      return {
        x: targetPos.x + boxW / 2 + 14,
        y: iy,
        direction: "left",
      };
    }

    case "queue_view": {
      const items = Array.isArray(targetObj.items) ? targetObj.items : [];
      const itemW = 34;
      const boxH = 36;
      const capacity = targetObj.capacity ?? Math.max(4, items.length);
      const boxW = Math.max(120, capacity * itemW + 20);
      const safeIdx = Math.min(idx, Math.max(0, items.length - 1));
      const ix = targetPos.x - boxW / 2 + 10 + safeIdx * itemW + itemW / 2;

      return {
        x: ix,
        y: targetPos.y - boxH / 2 - 4,
        direction: "down",
      };
    }

    case "bar_chart": {
      const bars = Array.isArray(targetObj.bars) && targetObj.bars.length > 0 ? targetObj.bars : [{ value: 50 }];
      const safeIdx = Math.min(idx, bars.length - 1);
      const chartW = Math.min(320, bars.length * 44 + 40);
      const chartH = 120;
      const barW = Math.max(16, Math.floor((chartW - 40) / bars.length) - 8);
      const bx = targetPos.x - chartW / 2 + 20 + safeIdx * (barW + 8) + barW / 2;
      const maxVal = targetObj.max_val ?? Math.max(10, ...bars.map((b: any) => Number(b.value) || 0));
      const bVal = Number(bars[safeIdx]?.value) || 0;
      const bH = Math.max(4, (bVal / maxVal) * (chartH - 40));
      const by = targetPos.y + chartH / 2 - 20 - bH;

      return {
        x: bx,
        y: by - 4,
        direction: "down",
      };
    }

    case "node":
    case "tree_element": {
      return {
        x: targetPos.x,
        y: targetPos.y - 20,
        direction: "down",
      };
    }

    default:
      return {
        x: targetPos.x,
        y: targetPos.y - 16,
        direction: "down",
      };
  }
}
