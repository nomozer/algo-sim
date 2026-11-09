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
  secondaryShellFill: "rgba(98, 174, 240, 0.08)",
  secondaryStroke: "#334155",
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
  | "secondary-solid"
  | "secondary-hidden"
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
  "secondary-solid": { stroke: GEO2D_TOKENS.secondaryStroke, strokeWidth: 1.35 },
  "secondary-hidden": {
    stroke: GEO2D_TOKENS.hiddenEdge,
    strokeWidth: 1.05,
    strokeDasharray: "3.2,2.4",
  },
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

/* ============================================================================
 * CÁC THÀNH PHẦN SVG 2D TÁI SỬ DỤNG & TỔ HỢP (§4.A2):
 * - Segment2D
 * - PerpendicularMarker2D
 * - Plane2D
 * - Section2D
 * - Pyramid2D
 * - Sphere2D
 * - Cylinder2D
 * - Cone2D
 * ============================================================================ */

/**
 * Đoạn thẳng 2D tái sử dụng (nét liền, nét đứt, đường cao, cạnh thiết diện, đường mục tiêu).
 */
export function Segment2D({
  from,
  to,
  role = "solid",
}: {
  from: Point2D;
  to: Point2D;
  role?: EdgeVisualRole;
}) {
  return <Geo2DEdge from={from} to={to} role={role} />;
}

/**
 * Ký hiệu góc vuông 2D theo hai hướng tia trong phép chiếu song song.
 */
export function PerpendicularMarker2D({
  at,
  alongA,
  alongB,
  size = 6.0,
  color = GEO2D_TOKENS.altitudeStroke,
}: {
  at: Point2D;
  alongA: Point2D;
  alongB: Point2D;
  size?: number;
  color?: string;
}) {
  return (
    <Geo2DRightAngle
      at={at}
      alongA={alongA}
      alongB={alongB}
      size={size}
      color={color}
    />
  );
}

/**
 * Mặt phẳng 2D (tấm hình bình hành/đa giác bán trong suốt kèm nhãn mặt phẳng tùy chọn).
 */
export function Plane2D({
  points,
  fill = GEO2D_TOKENS.planeFill,
  stroke = GEO2D_TOKENS.planeStroke,
  strokeWidth = 0.95,
  label,
  labelAt,
  showLabel = false,
}: {
  points: readonly Point2D[];
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  label?: string;
  labelAt?: Point2D;
  showLabel?: boolean;
}) {
  return (
    <g data-geo2d-comp="plane">
      <Geo2DPolygon
        points={points}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
      />
      {labelAt ? (
        <Geo2DPlaneBadge at={labelAt} label={label} showLabel={showLabel} />
      ) : null}
    </g>
  );
}

export type Section2DProps =
  | {
      kind?: "polygon";
      points: readonly Point2D[];
      /**
       * Mảng boolean tương ứng với từng cạnh `points[i] -> points[(i+1)%n]`:
       * `true` = cạnh khuất (`section-hidden`), `false` = cạnh nhìn thấy (`section`).
       */
      hiddenEdges?: readonly boolean[];
      fill?: string;
    }
  | {
      kind: "ellipse";
      center: Point2D;
      rx: number;
      ry: number;
      rotationDeg?: number;
      fill?: string;
      fullVisible?: boolean;
    };

/**
 * Thiết diện 2D (đa giác thiết diện hoặc đường tròn/elip giao tuyến).
 */
export function Section2D(props: Section2DProps) {
  if (props.kind === "ellipse") {
    return (
      <g data-geo2d-comp="section-ellipse">
        <Geo2DEllipseRim
          center={props.center}
          rx={props.rx}
          ry={props.ry}
          rotationDeg={props.rotationDeg}
          fill={props.fill ?? GEO2D_TOKENS.sectionFill}
          frontRole="section"
          backRole="section-hidden"
          fullVisible={props.fullVisible}
        />
      </g>
    );
  }

  const { points, hiddenEdges, fill = GEO2D_TOKENS.sectionFill } = props;
  return (
    <g data-geo2d-comp="section-polygon">
      <Geo2DPolygon points={points} fill={fill} />
      {points.map((pt, idx) => {
        const next = points[(idx + 1) % points.length]!;
        const isHidden = hiddenEdges?.[idx] ?? false;
        return (
          <Segment2D
            key={idx}
            from={pt}
            to={next}
            role={isHidden ? "section-hidden" : "section"}
          />
        );
      })}
    </g>
  );
}

export const DEFAULT_PYRAMID_FRAME = {
  S: [66, 14] as Point2D,
  A: [66, 66] as Point2D,
  B: [36, 88] as Point2D,
  C: [106, 94] as Point2D,
  D: [136, 72] as Point2D,
} as const;

/**
 * Thành phần Hình chóp 2D (`Pyramid2D`) có thể tái sử dụng độc lập hoặc kết hợp với
 * mặt phẳng cắt (`Plane2D`), thiết diện (`Section2D`), đường vuông góc (`Segment2D`) hoặc mặt cầu (`Sphere2D`).
 */
export function Pyramid2D({
  apex = DEFAULT_PYRAMID_FRAME.S,
  base = [
    DEFAULT_PYRAMID_FRAME.A,
    DEFAULT_PYRAMID_FRAME.B,
    DEFAULT_PYRAMID_FRAME.C,
    DEFAULT_PYRAMID_FRAME.D,
  ],
  emphasizeBase = false,
  altitudeRole = "altitude-hidden",
  rightAngleAtA = true,
  altitudeFoot,
}: {
  apex?: Point2D;
  base?: readonly [Point2D, Point2D, Point2D, Point2D];
  emphasizeBase?: boolean;
  altitudeRole?: EdgeVisualRole | "none";
  rightAngleAtA?: boolean;
  /**
   * Nếu truyền `altitudeFoot` (ví dụ tâm đáy O của chóp đều/chóp nội tiếp mặt cầu),
   * cạnh `SA` sẽ được vẽ như cạnh bên khuất thông thường và đường cao hạ từ `apex` xuống `altitudeFoot`.
   */
  altitudeFoot?: Point2D;
}) {
  const [A, B, C, D] = base;
  const S = apex;
  const hasSeparateAltitudeFoot = Boolean(altitudeFoot);
  const saRole: EdgeVisualRole = hasSeparateAltitudeFoot
    ? "hidden"
    : altitudeRole === "none"
      ? "hidden"
      : altitudeRole;

  return (
    <g data-geo2d-comp="pyramid">
      <Geo2DPolygon
        points={[A, B, C, D]}
        fill={emphasizeBase ? GEO2D_TOKENS.baseFill : GEO2D_TOKENS.shellFill}
      />
      <Geo2DPolygon points={[S, B, C]} fill={GEO2D_TOKENS.shellFill} />
      <Geo2DPolygon points={[S, C, D]} fill={GEO2D_TOKENS.shellFill} />

      {/* Cạnh đáy khuất phía sau: AB, AD */}
      <Segment2D from={A} to={B} role="hidden" />
      <Segment2D from={A} to={D} role="hidden" />
      <Segment2D from={S} to={A} role={saRole} />

      {/* Nếu có tâm đáy riêng (altitudeFoot), vẽ đường cao từ S xuống altitudeFoot */}
      {altitudeFoot && altitudeRole !== "none" ? (
        <Segment2D from={S} to={altitudeFoot} role={altitudeRole} />
      ) : null}

      {/* Ký hiệu góc vuông tại chân đường cao A */}
      {rightAngleAtA && !hasSeparateAltitudeFoot ? (
        <>
          <PerpendicularMarker2D at={A} alongA={S} alongB={B} size={5.8} />
          <PerpendicularMarker2D at={A} alongA={S} alongB={D} size={5.8} />
        </>
      ) : null}

      {/* Các cạnh nhìn thấy phía trước: BC, CD, SB, SC, SD */}
      <Segment2D from={B} to={C} role="solid" />
      <Segment2D from={C} to={D} role="solid" />
      <Segment2D from={S} to={B} role="solid" />
      <Segment2D from={S} to={C} role="solid" />
      <Segment2D from={S} to={D} role="solid" />
    </g>
  );
}

export const DEFAULT_CUBE_FRAME = {
  A: [58, 66] as Point2D,
  B: [34, 86] as Point2D,
  C: [106, 92] as Point2D,
  D: [130, 72] as Point2D,
  A_prime: [58, 18] as Point2D,
  B_prime: [34, 38] as Point2D,
  C_prime: [106, 44] as Point2D,
  D_prime: [130, 24] as Point2D,
} as const;

/**
 * Thành phần Hình lập phương / Hình hộp 2D (`Cube2D`) có thể tái sử dụng độc lập hoặc kết hợp
 * với mặt phẳng cắt (`Plane2D`), thiết diện đa giác (`Section2D`) và đoạn vuông góc (`Segment2D`).
 */
export function Cube2D({
  base = [
    DEFAULT_CUBE_FRAME.A,
    DEFAULT_CUBE_FRAME.B,
    DEFAULT_CUBE_FRAME.C,
    DEFAULT_CUBE_FRAME.D,
  ],
  top = [
    DEFAULT_CUBE_FRAME.A_prime,
    DEFAULT_CUBE_FRAME.B_prime,
    DEFAULT_CUBE_FRAME.C_prime,
    DEFAULT_CUBE_FRAME.D_prime,
  ],
  emphasizeBase = false,
}: {
  base?: readonly [Point2D, Point2D, Point2D, Point2D];
  top?: readonly [Point2D, Point2D, Point2D, Point2D];
  emphasizeBase?: boolean;
}) {
  const [A, B, C, D] = base;
  const [Ap, Bp, Cp, Dp] = top;
  return (
    <g data-geo2d-comp="cube">
      <Geo2DPolygon
        points={[A, B, C, D]}
        fill={emphasizeBase ? GEO2D_TOKENS.baseFill : GEO2D_TOKENS.shellFill}
      />
      <Geo2DPolygon points={[Ap, Bp, Cp, Dp]} fill={GEO2D_TOKENS.shellFill} />
      <Geo2DPolygon points={[B, C, Cp, Bp]} fill={GEO2D_TOKENS.shellFill} />
      <Geo2DPolygon points={[C, D, Dp, Cp]} fill={GEO2D_TOKENS.shellFill} />

      {/* 3 cạnh khuất xuất phát từ đỉnh khuất A phía sau: AB, AD, AA' */}
      <Segment2D from={A} to={B} role="hidden" />
      <Segment2D from={A} to={D} role="hidden" />
      <Segment2D from={A} to={Ap} role="hidden" />

      {/* 9 cạnh nhìn thấy */}
      <Segment2D from={B} to={C} role="solid" />
      <Segment2D from={C} to={D} role="solid" />
      <Segment2D from={Ap} to={Bp} role="solid" />
      <Segment2D from={Bp} to={Cp} role="solid" />
      <Segment2D from={Cp} to={Dp} role="solid" />
      <Segment2D from={Dp} to={Ap} role="solid" />
      <Segment2D from={B} to={Bp} role="solid" />
      <Segment2D from={C} to={Cp} role="solid" />
      <Segment2D from={D} to={Dp} role="solid" />
    </g>
  );
}

export const DEFAULT_PRISM_FRAME = {
  A: [58, 66] as Point2D,
  B: [38, 88] as Point2D,
  C: [124, 84] as Point2D,
  A_prime: [58, 18] as Point2D,
  B_prime: [38, 40] as Point2D,
  C_prime: [124, 36] as Point2D,
} as const;

/**
 * Thành phần Hình lăng trụ tam giác 2D (`Prism2D`) hỗ trợ lăng trụ đứng/xiên và thiết diện phẳng.
 */
export function Prism2D({
  base = [
    DEFAULT_PRISM_FRAME.A,
    DEFAULT_PRISM_FRAME.B,
    DEFAULT_PRISM_FRAME.C,
  ],
  top = [
    DEFAULT_PRISM_FRAME.A_prime,
    DEFAULT_PRISM_FRAME.B_prime,
    DEFAULT_PRISM_FRAME.C_prime,
  ],
  emphasizeBase = false,
  rightAngleAtA = true,
}: {
  base?: readonly [Point2D, Point2D, Point2D];
  top?: readonly [Point2D, Point2D, Point2D];
  emphasizeBase?: boolean;
  rightAngleAtA?: boolean;
}) {
  const [A, B, C] = base;
  const [Ap, Bp, Cp] = top;
  return (
    <g data-geo2d-comp="prism">
      <Geo2DPolygon
        points={[A, B, C]}
        fill={emphasizeBase ? GEO2D_TOKENS.baseFill : GEO2D_TOKENS.shellFill}
      />
      <Geo2DPolygon points={[Ap, Bp, Cp]} fill={GEO2D_TOKENS.shellFill} />
      <Geo2DPolygon points={[B, C, Cp, Bp]} fill={GEO2D_TOKENS.shellFill} />

      {/* 3 cạnh khuất xuất phát từ đỉnh khuất A phía sau: AB, AC, AA' */}
      <Segment2D from={A} to={B} role="hidden" />
      <Segment2D from={A} to={C} role="hidden" />
      <Segment2D from={A} to={Ap} role="altitude-hidden" />

      {rightAngleAtA ? (
        <PerpendicularMarker2D at={A} alongA={Ap} alongB={C} size={5.5} />
      ) : null}

      {/* 6 cạnh nhìn thấy */}
      <Segment2D from={B} to={C} role="solid" />
      <Segment2D from={Ap} to={Bp} role="solid" />
      <Segment2D from={Bp} to={Cp} role="solid" />
      <Segment2D from={Cp} to={Ap} role="solid" />
      <Segment2D from={B} to={Bp} role="solid" />
      <Segment2D from={C} to={Cp} role="solid" />
    </g>
  );
}

/**
 * Thành phần Mặt cầu 2D (`Sphere2D`) có thể dùng đơn lẻ hoặc kết hợp với mặt phẳng cắt / hình chóp nội tiếp.
 */
export function Sphere2D({
  center = [90, 55],
  radius = 38,
  equatorRy = 11.2,
  equatorMode = "front-solid",
  fill = GEO2D_TOKENS.shellFill,
  stroke = GEO2D_TOKENS.ink,
  strokeWidth = 1.6,
}: {
  center?: Point2D;
  radius?: number;
  equatorRy?: number;
  equatorMode?: "front-solid" | "all-hidden" | "none";
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
}) {
  return (
    <g data-geo2d-comp="sphere">
      <circle
        cx={center[0]}
        cy={center[1]}
        r={radius}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
      />
      {equatorMode !== "none" ? (
        <Geo2DEllipseRim
          center={center}
          rx={radius}
          ry={equatorRy}
          fill={equatorMode === "front-solid" ? "rgba(148, 163, 184, 0.07)" : "none"}
          frontRole={equatorMode === "front-solid" ? "solid" : "hidden"}
          backRole="hidden"
        />
      ) : null}
    </g>
  );
}

/**
 * Thành phần Hình trụ 2D (`Cylinder2D`) hỗ trợ trụ đứng, trụ xiên, trụ cắt bởi mặt phẳng,
 * hoặc làm khối ngoại tiếp cho hình nón (`Cone2D`).
 */
export function Cylinder2D({
  topCenter = [92, 22],
  bottomCenter = [92, 86],
  rx = 33,
  ry = 9.2,
  showAxis = true,
  axisRole = "altitude-hidden",
  emphasizeBases = true,
  variant = "primary",
}: {
  topCenter?: Point2D;
  bottomCenter?: Point2D;
  rx?: number;
  ry?: number;
  showAxis?: boolean;
  axisRole?: EdgeVisualRole;
  emphasizeBases?: boolean;
  variant?: "primary" | "secondary";
}) {
  const frontEdgeRole: EdgeVisualRole =
    variant === "secondary" ? "secondary-solid" : "solid";
  const backEdgeRole: EdgeVisualRole =
    variant === "secondary" ? "secondary-hidden" : "hidden";
  const bodyFill =
    variant === "secondary" ? GEO2D_TOKENS.secondaryShellFill : GEO2D_TOKENS.shellFill;
  const baseFill = emphasizeBases
    ? variant === "secondary"
      ? "rgba(98, 174, 240, 0.11)"
      : GEO2D_TOKENS.baseFill
    : "none";

  return (
    <g data-geo2d-comp="cylinder">
      <Geo2DPolygon
        points={[
          [topCenter[0] - rx, topCenter[1]],
          [bottomCenter[0] - rx, bottomCenter[1]],
          [bottomCenter[0] + rx, bottomCenter[1]],
          [topCenter[0] + rx, topCenter[1]],
        ]}
        fill={bodyFill}
      />
      {/* Đáy dưới */}
      <Geo2DEllipseRim
        center={bottomCenter}
        rx={rx}
        ry={ry}
        fill={baseFill}
        frontRole={frontEdgeRole}
        backRole={backEdgeRole}
      />
      {/* Đáy trên */}
      <Geo2DEllipseRim
        center={topCenter}
        rx={rx}
        ry={ry}
        fill={baseFill}
        frontRole={frontEdgeRole}
        backRole={frontEdgeRole}
        fullVisible
      />
      {/* Hai đường sinh biên */}
      <Segment2D
        from={[topCenter[0] - rx, topCenter[1]]}
        to={[bottomCenter[0] - rx, bottomCenter[1]]}
        role={frontEdgeRole}
      />
      <Segment2D
        from={[topCenter[0] + rx, topCenter[1]]}
        to={[bottomCenter[0] + rx, bottomCenter[1]]}
        role={frontEdgeRole}
      />
      {/* Trục OO' */}
      {showAxis ? (
        <Segment2D from={topCenter} to={bottomCenter} role={axisRole} />
      ) : null}
    </g>
  );
}

/**
 * Thành phần Hình nón 2D (`Cone2D`) có thể dùng đơn lẻ, kết hợp mặt phẳng cắt qua trục,
 * hoặc đặt nội tiếp bên trong `Cylinder2D`.
 */
export function Cone2D({
  apex = [90, 16],
  baseCenter = [90, 86],
  rx = 38,
  ry = 9.5,
  showAxis = true,
  axisRole = "altitude-hidden",
  emphasizeBase = true,
  showBaseRim = true,
}: {
  apex?: Point2D;
  baseCenter?: Point2D;
  rx?: number;
  ry?: number;
  showAxis?: boolean;
  axisRole?: EdgeVisualRole;
  emphasizeBase?: boolean;
  showBaseRim?: boolean;
}) {
  const leftRim: Point2D = [baseCenter[0] - rx, baseCenter[1]];
  const rightRim: Point2D = [baseCenter[0] + rx, baseCenter[1]];
  return (
    <g data-geo2d-comp="cone">
      <Geo2DPolygon points={[apex, leftRim, rightRim]} fill={GEO2D_TOKENS.shellFill} />
      {showBaseRim ? (
        <Geo2DEllipseRim
          center={baseCenter}
          rx={rx}
          ry={ry}
          fill={emphasizeBase ? GEO2D_TOKENS.baseFill : "none"}
          frontRole="solid"
          backRole="hidden"
        />
      ) : null}
      {showAxis ? <Segment2D from={apex} to={baseCenter} role={axisRole} /> : null}
      <Segment2D from={apex} to={leftRim} role="solid" />
      <Segment2D from={apex} to={rightRim} role="solid" />
    </g>
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
