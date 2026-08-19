/**
 * Real Browser Disallowed Collision Classifier (G6).
 *
 * Phân loại các trường hợp giao thoa bounding box trong trình duyệt thực:
 * - ALLOWED_CONTAINMENT: Phần tử con nằm trọn trong khung chứa cha (chữ trong value_box, item trong stack).
 * - ALLOWED_ANCHOR: Pointer neo vào đỉnh/cạnh ô mục tiêu.
 * - DISALLOWED_COLLISION: Chữ đè chữ, box độc lập đè nhau, tiêu đề đè mô hình.
 */

export interface BoundingBox {
  id: string;
  type: string;
  left: number;
  top: number;
  right: number;
  bottom: number;
  width: number;
  height: number;
}

export type OverlapClassification = "ALLOWED_CONTAINMENT" | "ALLOWED_ANCHOR" | "DISALLOWED_COLLISION" | "NO_OVERLAP";

export function computeIntersectionArea(a: BoundingBox, b: BoundingBox): number {
  const xOverlap = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
  const yOverlap = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
  return xOverlap * yOverlap;
}

export function isContainedWithin(inner: BoundingBox, outer: BoundingBox, tolerance = 4): boolean {
  return (
    inner.left >= outer.left - tolerance &&
    inner.right <= outer.right + tolerance &&
    inner.top >= outer.top - tolerance &&
    inner.bottom <= outer.bottom + tolerance
  );
}

export function classifyBoundingOverlap(
  a: BoundingBox,
  b: BoundingBox,
): OverlapClassification {
  const area = computeIntersectionArea(a, b);
  if (area <= 1) {
    return "NO_OVERLAP";
  }

  // 1. Pointer neo vào ô đích
  if (a.type === "pointer" || b.type === "pointer") {
    return "ALLOWED_ANCHOR";
  }

  // 2. Chữ / phần tử nằm trong khung chứa
  if (isContainedWithin(a, b) || isContainedWithin(b, a)) {
    return "ALLOWED_CONTAINMENT";
  }

  // 3. Item trong Stack hoặc Queue
  if (
    (a.type.startsWith("stack") && b.type.startsWith("stack")) ||
    (a.type.startsWith("queue") && b.type.startsWith("queue"))
  ) {
    return "ALLOWED_CONTAINMENT";
  }

  // 4. Mọi trường hợp giao thoa độc lập còn lại là vi phạm vùng cấm
  return "DISALLOWED_COLLISION";
}
