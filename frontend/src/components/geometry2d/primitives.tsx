import type { ReactNode } from "react";

/**
 * Bảng token thị giác 2D thống nhất cho hệ thống hình minh họa Hình học không gian Axo.
 * Bám sát `DESIGN.md` và `tokens.css` (nền giấy ấm `--canvas-soft`, mực đậm `--ink`,
 * cam đất thiết diện `--geo3d-vai-tro-du-kien-so`, xanh lam mục tiêu `--primary`, xanh cổ vịt đường cao `--accent-teal`).
 */
export const GEO2D_TOKENS = {
  ink: "#1E293B",
  hiddenEdge: "#64748B",
  shellFill: "rgba(148, 163, 184, 0.10)",
  baseFill: "rgba(148, 163, 184, 0.16)",
  sectionStroke: "#C85A32",
  sectionFill: "rgba(200, 90, 50, 0.24)",
  planeStroke: "rgba(109, 40, 217, 0.44)",
  planeFill: "rgba(109, 40, 217, 0.09)",
  planeLabel: "#6D28D9",
  altitudeStroke: "#0F766E",
  altitudeFill: "rgba(15, 118, 110, 0.14)",
  targetStroke: "#0075DE",
  haloStroke: "#F6F5F4",
  fontFamily: "var(--font-family, 'Inter', system-ui, sans-serif)",
} as const;

export type Point2D = readonly [number, number];

export type EdgeVisualRole =
  | "solid"
  | "hidden"
  | "section"
  | "section-hidden"
  | "altitude"
  | "altitude-hidden"
  | "target"
  | "plane-border";

const EDGE_ROLE_STYLE: Record<
  EdgeVisualRole,
  { stroke: string; strokeWidth: number; strokeDasharray?: string }
> = {
  solid: { stroke: GEO2D_TOKENS.ink, strokeWidth: 1.55 },
  hidden: { stroke: GEO2D_TOKENS.hiddenEdge, strokeWidth: 1.15, strokeDasharray: "3.6,2.5" },
  section: { stroke: GEO2D_TOKENS.sectionStroke, strokeWidth: 1.9 },
  "section-hidden": {
    stroke: GEO2D_TOKENS.sectionStroke,
    strokeWidth: 1.35,
    strokeDasharray: "3.6,2.5",
  },
  altitude: { stroke: GEO2D_TOKENS.altitudeStroke, strokeWidth: 1.6 },
  "altitude-hidden": {
    stroke: GEO2D_TOKENS.altitudeStroke,
    strokeWidth: 1.45,
    strokeDasharray: "3.6,2.5",
  },
  target: { stroke: GEO2D_TOKENS.targetStroke, strokeWidth: 2.0 },
  "plane-border": { stroke: GEO2D_TOKENS.planeStroke, strokeWidth: 1.0 },
};

export function Geo2DPolygon({
  points,
  fill = GEO2D_TOKENS.shellFill,
  stroke,
  strokeWidth = 1,
  strokeDasharray,
}: {
  points: readonly Point2D[];
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
}) {
  const ptsAttr = points.map(([x, y]) => `${Number(x.toFixed(1))},${Number(y.toFixed(1))}`).join(" ");
  return (
    <polygon
      points={ptsAttr}
      fill={fill}
      stroke={stroke}
      strokeWidth={stroke ? strokeWidth : undefined}
      strokeDasharray={strokeDasharray}
      strokeLinejoin="round"
    />
  );
}

export function Geo2DEdge({
  from,
  to,
  role = "solid",
}: {
  from: Point2D;
  to: Point2D;
  role?: EdgeVisualRole;
}) {
  const style = EDGE_ROLE_STYLE[role];
  return (
    <line
      x1={Number(from[0].toFixed(1))}
      y1={Number(from[1].toFixed(1))}
      x2={Number(to[0].toFixed(1))}
      y2={Number(to[1].toFixed(1))}
      stroke={style.stroke}
      strokeWidth={style.strokeWidth}
      strokeDasharray={style.strokeDasharray}
      strokeLinecap="round"
    />
  );
}

export function Geo2DRightAngle({
  at,
  alongA,
  alongB,
  size = 6.2,
  color = GEO2D_TOKENS.altitudeStroke,
}: {
  at: Point2D;
  alongA: Point2D;
  alongB: Point2D;
  size?: number;
  color?: string;
}) {
  const ux = alongA[0] - at[0];
  const uy = alongA[1] - at[1];
  const vx = alongB[0] - at[0];
  const vy = alongB[1] - at[1];
  const uLen = Math.hypot(ux, uy) || 1;
  const vLen = Math.hypot(vx, vy) || 1;
  const u1x = (ux / uLen) * size;
  const u1y = (uy / uLen) * size;
  const v1x = (vx / vLen) * size;
  const v1y = (vy / vLen) * size;
  const p1 = `${(at[0] + u1x).toFixed(1)},${(at[1] + u1y).toFixed(1)}`;
  const p2 = `${(at[0] + u1x + v1x).toFixed(1)},${(at[1] + u1y + v1y).toFixed(1)}`;
  const p3 = `${(at[0] + v1x).toFixed(1)},${(at[1] + v1y).toFixed(1)}`;
  return (
    <polyline
      points={`${p1} ${p2} ${p3}`}
      fill="none"
      stroke={color}
      strokeWidth="1.25"
      strokeLinejoin="round"
    />
  );
}

/**
 * Vẽ hình elip biểu diễn đường tròn trong không gian (đáy trụ, đáy nón, xích đạo cầu, thiết diện tròn).
 * Tự động phân tách nửa cung phía sau (nét đứt) và nửa cung phía trước (nét liền), hoặc vẽ liền toàn bộ.
 */
export function Geo2DEllipseRim({
  center,
  rx,
  ry,
  rotationDeg = 0,
  fill = "none",
  frontRole = "solid",
  backRole = "hidden",
  fullVisible = false,
}: {
  center: Point2D;
  rx: number;
  ry: number;
  rotationDeg?: number;
  fill?: string;
  frontRole?: EdgeVisualRole;
  backRole?: EdgeVisualRole;
  fullVisible?: boolean;
}) {
  const [cx, cy] = center;
  const frontStyle = EDGE_ROLE_STYLE[frontRole];
  const backStyle = EDGE_ROLE_STYLE[backRole];
  const transform =
    Math.abs(rotationDeg) > 1e-3 ? `rotate(${rotationDeg} ${cx} ${cy})` : undefined;

  if (fullVisible) {
    return (
      <ellipse
        cx={cx}
        cy={cy}
        rx={rx}
        ry={ry}
        transform={transform}
        fill={fill}
        stroke={frontStyle.stroke}
        strokeWidth={frontStyle.strokeWidth}
      />
    );
  }

  return (
    <g transform={transform}>
      {fill !== "none" ? <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill={fill} /> : null}
      {/* Nửa cung phía sau (y <= cy): nét đứt */}
      <path
        d={`M ${(cx - rx).toFixed(1)} ${cy.toFixed(1)} A ${rx.toFixed(1)} ${ry.toFixed(1)} 0 0 1 ${(cx + rx).toFixed(1)} ${cy.toFixed(1)}`}
        fill="none"
        stroke={backStyle.stroke}
        strokeWidth={backStyle.strokeWidth}
        strokeDasharray={backStyle.strokeDasharray}
        strokeLinecap="round"
      />
      {/* Nửa cung phía trước (y >= cy): nét liền */}
      <path
        d={`M ${(cx - rx).toFixed(1)} ${cy.toFixed(1)} A ${rx.toFixed(1)} ${ry.toFixed(1)} 0 0 0 ${(cx + rx).toFixed(1)} ${cy.toFixed(1)}`}
        fill="none"
        stroke={frontStyle.stroke}
        strokeWidth={frontStyle.strokeWidth}
        strokeLinecap="round"
      />
    </g>
  );
}

export function Geo2DPoint({
  at,
  label,
  dx = 0,
  dy = -8,
  variant = "primary",
  showLabel = true,
}: {
  at: Point2D;
  label?: string;
  dx?: number;
  dy?: number;
  variant?: "primary" | "derived" | "altitude";
  showLabel?: boolean;
}) {
  const color =
    variant === "derived"
      ? GEO2D_TOKENS.sectionStroke
      : variant === "altitude"
        ? GEO2D_TOKENS.altitudeStroke
        : GEO2D_TOKENS.ink;
  const r = variant === "derived" ? 2.4 : 2.25;
  const tx = Number((at[0] + dx).toFixed(1));
  const ty = Number((at[1] + dy).toFixed(1));

  return (
    <>
      <circle cx={Number(at[0].toFixed(1))} cy={Number(at[1].toFixed(1))} r={r} fill={color} />
      {showLabel && label ? (
        <text
          x={tx}
          y={ty}
          fontFamily={GEO2D_TOKENS.fontFamily}
          fontSize="10"
          fontWeight="700"
          fill={color}
          paintOrder="stroke"
          stroke={GEO2D_TOKENS.haloStroke}
          strokeWidth="2.5"
          strokeLinejoin="round"
          textAnchor="middle"
          dominantBaseline="central"
        >
          {label}
        </text>
      ) : null}
    </>
  );
}

export function Geo2DPlaneBadge({
  at,
  label,
  showLabel = true,
}: {
  at: Point2D;
  label?: string;
  showLabel?: boolean;
}) {
  if (!showLabel || !label) return null;
  return (
    <text
      x={Number(at[0].toFixed(1))}
      y={Number(at[1].toFixed(1))}
      fontFamily={GEO2D_TOKENS.fontFamily}
      fontStyle="italic"
      fontSize="9.8"
      fontWeight="700"
      fill={GEO2D_TOKENS.planeLabel}
      paintOrder="stroke"
      stroke={GEO2D_TOKENS.haloStroke}
      strokeWidth="2.4"
      strokeLinejoin="round"
      textAnchor="middle"
      dominantBaseline="central"
    >
      {label}
    </text>
  );
}

export interface Geometry2DFrameProps {
  thumbId: string;
  templateId: string;
  family: string;
  mode: "verified" | "generic" | "family-icon" | "fallback-neutral";
  fallback?: boolean;
  children: ReactNode;
}

export function Geometry2DFrame({
  thumbId,
  templateId,
  family,
  mode,
  fallback = false,
  children,
}: Geometry2DFrameProps) {
  return (
    <svg
      viewBox="0 0 180 110"
      data-thumb-id={thumbId}
      data-thumb-template={templateId}
      data-thumb-family={family}
      data-thumb-mode={mode}
      data-thumb-fallback={fallback ? "true" : "false"}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}
