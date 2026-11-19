import type { ReactNode } from "react";
import { GEO2D_TOKENS } from "./primitives";

export type GeometryFamilyId = "pyramid" | "sphere" | "cylinder" | "cone" | "neutral";

export interface FamilyIconDefinition {
  id: GeometryFamilyId;
  labelVi: string;
  renderGlyph: () => ReactNode;
}

/**
 * Tầng A (§5): Bộ 4 icon Họ Hình Học (Hình chóp, Mặt cầu, Hình trụ, Hình nón) + 1 icon trung tính.
 * Thiết kế trong hệ khung chuẩn `24×24`:
 * - Đường nét rõ, cân đối, nhận diện ngay ở kích thước nhỏ (14px–24px) lẫn thumbnail fallback.
 * - Không chữ, không ký hiệu điểm, không biến icon thành ảnh chụp Scene3D thu nhỏ.
 */
export const GEOMETRY_FAMILY_ICONS: Readonly<Record<GeometryFamilyId, FamilyIconDefinition>> =
  Object.freeze({
    pyramid: {
      id: "pyramid",
      labelVi: "Hình chóp",
      renderGlyph: () => (
        <>
          <polygon
            points="12,3 4,17.2 13.2,20.5 20,15.2"
            fill={GEO2D_TOKENS.shellFill}
          />
          <polygon
            points="12,3 13.2,20.5 20,15.2"
            fill={GEO2D_TOKENS.baseFill}
          />
          {/* Cạnh đáy khuất phía sau */}
          <polyline
            points="4,17.2 10.6,13.6 20,15.2"
            fill="none"
            stroke={GEO2D_TOKENS.hiddenEdge}
            strokeWidth="1.25"
            strokeDasharray="2.2,1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <line
            x1="12"
            y1="3"
            x2="10.6"
            y2="13.6"
            stroke={GEO2D_TOKENS.hiddenEdge}
            strokeWidth="1.25"
            strokeDasharray="2.2,1.8"
            strokeLinecap="round"
          />
          {/* Các cạnh nhìn thấy */}
          <polygon
            points="12,3 4,17.2 13.2,20.5 20,15.2"
            fill="none"
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.65"
            strokeLinejoin="round"
          />
          <line
            x1="12"
            y1="3"
            x2="13.2"
            y2="20.5"
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.55"
            strokeLinecap="round"
          />
        </>
      ),
    },
    sphere: {
      id: "sphere",
      labelVi: "Mặt cầu",
      renderGlyph: () => (
        <>
          <circle
            cx="12"
            cy="12"
            r="8.5"
            fill={GEO2D_TOKENS.shellFill}
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.65"
          />
          {/* Nửa cung xích đạo phía sau (nét đứt) */}
          <path
            d="M 3.5 12 A 8.5 3.1 0 0 1 20.5 12"
            fill="none"
            stroke={GEO2D_TOKENS.hiddenEdge}
            strokeWidth="1.2"
            strokeDasharray="2.2,1.8"
            strokeLinecap="round"
          />
          {/* Nửa cung xích đạo phía trước (nét liền) */}
          <path
            d="M 3.5 12 A 8.5 3.1 0 0 0 20.5 12"
            fill="none"
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </>
      ),
    },
    cylinder: {
      id: "cylinder",
      labelVi: "Hình trụ",
      renderGlyph: () => (
        <>
          <path
            d="M 5.2 6.5 L 5.2 17.5 A 6.8 2.6 0 0 0 18.8 17.5 L 18.8 6.5 Z"
            fill={GEO2D_TOKENS.shellFill}
          />
          <ellipse
            cx="12"
            cy="6.5"
            rx="6.8"
            ry="2.6"
            fill={GEO2D_TOKENS.baseFill}
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.6"
          />
          {/* Cung đáy dưới phía sau (nét đứt) */}
          <path
            d="M 5.2 17.5 A 6.8 2.6 0 0 1 18.8 17.5"
            fill="none"
            stroke={GEO2D_TOKENS.hiddenEdge}
            strokeWidth="1.2"
            strokeDasharray="2.2,1.8"
            strokeLinecap="round"
          />
          {/* Cung đáy dưới phía trước + hai đường sinh biên */}
          <path
            d="M 5.2 6.5 L 5.2 17.5 A 6.8 2.6 0 0 0 18.8 17.5 L 18.8 6.5"
            fill="none"
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.65"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </>
      ),
    },
    cone: {
      id: "cone",
      labelVi: "Hình nón",
      renderGlyph: () => (
        <>
          <path
            d="M 12 3.2 L 4.6 17.6 A 7.4 2.7 0 0 0 19.4 17.6 Z"
            fill={GEO2D_TOKENS.shellFill}
          />
          {/* Cung đáy phía sau (nét đứt) */}
          <path
            d="M 4.6 17.6 A 7.4 2.7 0 0 1 19.4 17.6"
            fill="none"
            stroke={GEO2D_TOKENS.hiddenEdge}
            strokeWidth="1.2"
            strokeDasharray="2.2,1.8"
            strokeLinecap="round"
          />
          {/* Trục cao gợi ý nhẹ */}
          <line
            x1="12"
            y1="3.2"
            x2="12"
            y2="17.6"
            stroke={GEO2D_TOKENS.hiddenEdge}
            strokeWidth="1.15"
            strokeDasharray="2.1,1.8"
            strokeLinecap="round"
          />
          {/* Hai đường sinh biên + cung đáy trước */}
          <path
            d="M 12 3.2 L 4.6 17.6 A 7.4 2.7 0 0 0 19.4 17.6 Z"
            fill="none"
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.65"
            strokeLinejoin="round"
          />
        </>
      ),
    },
    neutral: {
      id: "neutral",
      labelVi: "Hình học không gian",
      renderGlyph: () => (
        <>
          <polygon
            points="12,3.2 4.5,7.5 4.5,16.5 12,20.8 19.5,16.5 19.5,7.5"
            fill={GEO2D_TOKENS.shellFill}
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <polyline
            points="4.5,7.5 12,12 19.5,7.5"
            fill="none"
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.45"
            strokeLinejoin="round"
          />
          <line
            x1="12"
            y1="12"
            x2="12"
            y2="20.8"
            stroke={GEO2D_TOKENS.ink}
            strokeWidth="1.45"
            strokeLinecap="round"
          />
        </>
      ),
    },
  });

export function familyIdFromCategoryLabel(category?: string | null): GeometryFamilyId {
  if (!category) return "neutral";
  const norm = category.trim().toLowerCase();
  if (norm === "hình chóp" || norm === "pyramid" || norm === "prism" || norm === "hình lăng trụ") {
    return "pyramid";
  }
  if (norm === "mặt cầu" || norm === "khối cầu" || norm === "sphere") {
    return "sphere";
  }
  if (norm === "hình trụ" || norm === "khối trụ" || norm === "cylinder") {
    return "cylinder";
  }
  if (norm === "hình nón" || norm === "khối nón" || norm === "cone") {
    return "cone";
  }
  return "neutral";
}

export type GeometryFamilyIconSpec = FamilyIconDefinition;

export function normalizeGeometryFamily(category?: string | null): GeometryFamilyId {
  return familyIdFromCategoryLabel(category);
}

export function getFamilyIconDefinition(family: GeometryFamilyId): FamilyIconDefinition {
  return GEOMETRY_FAMILY_ICONS[family] ?? GEOMETRY_FAMILY_ICONS.neutral;
}

/**
 * Component hiển thị icon họ hình độc lập (24×24) dùng cho nhãn danh mục / bộ lọc hoặc danh sách.
 */
export function GeometryFamilyIcon({
  family,
  size = 16,
  className,
}: {
  family: GeometryFamilyId;
  size?: number;
  className?: string;
}) {
  const def = getFamilyIconDefinition(family);
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      data-family-icon={def.id}
      aria-hidden="true"
    >
      {def.renderGlyph()}
    </svg>
  );
}

/**
 * Render icon họ hình cân đối bên trong khung thumbnail `180×110` khi chỉ biết họ hình
 * hoặc dùng làm fallback an toàn (không có chữ hay ký hiệu điểm chưa xác minh).
 */
export function renderFamilyThumbnailContent(family: GeometryFamilyId): ReactNode {
  const def = getFamilyIconDefinition(family);
  return (
    <g transform="translate(54, 19) scale(3.0)" data-family-glyph={def.id}>
      {def.renderGlyph()}
    </g>
  );
}
