import type { ReactNode } from "react";
import type { GeometryFamilyId } from "./family-icons";
import {
  GEO2D_TOKENS,
  Geo2DEdge,
  Geo2DEllipseRim,
  Geo2DPlaneBadge,
  Geo2DPoint,
  Geo2DPolygon,
  Geo2DRightAngle,
  type Point2D,
} from "./primitives";

export type GeometryTemplateId =
  | "pyramid.section"
  | "pyramid.diagonal-section"
  | "pyramid.perpendicular"
  | "pyramid.altitude-distance"
  | "pyramid.volume-height"
  | "sphere.plane-section"
  | "sphere.basic-radius"
  | "cylinder.perpendicular-section"
  | "cylinder.oblique-axis"
  | "cylinder.right-basic"
  | "cone.axial-section"
  | "cone.slant-generator";

export interface VerifiedTemplateLabels {
  apex?: string;
  base?: readonly string[];
  section?: readonly string[];
  center?: string;
  topCenter?: string;
  foot?: string;
  rimPoint?: string;
  secondRimPoint?: string;
  plane?: string;
}

export interface TemplateRenderOptions {
  /**
   * `"verified"`: Chỉ hiển thị các nhãn điểm / mặt phẳng đã được xác minh từ dữ liệu hình học thật (`Scene3D`).
   * `"generic"`: Minh họa khái quát cho dạng bài — tuyệt đối không gán nhãn điểm/mặt phẳng tùy tiện (§6).
   */
  mode: "verified" | "generic";
  labels?: VerifiedTemplateLabels;
}

export interface GeometryTemplateDefinition {
  id: GeometryTemplateId;
  family: Exclude<GeometryFamilyId, "neutral">;
  titleVi: string;
  invariants: readonly string[];
  render: (options: TemplateRenderOptions) => ReactNode;
}

/**
 * Hệ tọa độ trục đo (cabinet/axonometric) chuẩn SGK cho hình chóp tứ giác S.ABCD có SA ⊥ (ABCD):
 * - A = (66, 66) (đỉnh đáy phía trong bên trái, chân đường cao SA)
 * - B = (36, 88) (đỉnh đáy phía trước bên trái, AB = (-30, 22))
 * - D = (136, 72) (đỉnh đáy phía trong bên phải, AD = (70, 6))
 * - C = B + AD = (106, 94) (đỉnh đáy phía trước bên phải)
 * - S = (66, 14) (đỉnh chóp thẳng đứng phía trên A, SA = 52px)
 *
 * Bảo toàn chính xác phép chiếu song song (affine):
 * - ABCD là hình bình hành mở rộng (rộng 100px, sâu 28px), 4 cạnh bên SB, SA, SC, SD tách góc rõ ràng.
 */
const PYRAMID_FRAME = {
  S: [66, 14] as Point2D,
  A: [66, 66] as Point2D,
  B: [36, 88] as Point2D,
  C: [106, 94] as Point2D,
  D: [136, 72] as Point2D,
} as const;

function renderPyramidShell({
  emphasizeBase = false,
  altitudeRole = "altitude-hidden",
  rightAngleAtA = true,
}: {
  emphasizeBase?: boolean;
  altitudeRole?: "hidden" | "altitude-hidden" | "section-hidden";
  rightAngleAtA?: boolean;
} = {}) {
  const { S, A, B, C, D } = PYRAMID_FRAME;
  return (
    <>
      {/* Tô nền mặt đáy và mặt bên */}
      <Geo2DPolygon
        points={[A, B, C, D]}
        fill={emphasizeBase ? GEO2D_TOKENS.baseFill : GEO2D_TOKENS.shellFill}
      />
      <Geo2DPolygon points={[S, B, C]} fill={GEO2D_TOKENS.shellFill} />
      <Geo2DPolygon points={[S, C, D]} fill={GEO2D_TOKENS.shellFill} />

      {/* Các cạnh khuất: AB, AD và đường cao SA */}
      <Geo2DEdge from={A} to={B} role="hidden" />
      <Geo2DEdge from={A} to={D} role="hidden" />
      <Geo2DEdge from={S} to={A} role={altitudeRole} />

      {/* Ký hiệu góc vuông tại chân đường cao A */}
      {rightAngleAtA ? (
        <>
          <Geo2DRightAngle at={A} alongA={S} alongB={B} size={5.8} />
          <Geo2DRightAngle at={A} alongA={S} alongB={D} size={5.8} />
        </>
      ) : null}

      {/* Các cạnh nhìn thấy: BC, CD, SB, SC, SD */}
      <Geo2DEdge from={B} to={C} role="solid" />
      <Geo2DEdge from={C} to={D} role="solid" />
      <Geo2DEdge from={S} to={B} role="solid" />
      <Geo2DEdge from={S} to={C} role="solid" />
      <Geo2DEdge from={S} to={D} role="solid" />
    </>
  );
}

function renderPyramidBaseAndApexPoints(options: TemplateRenderOptions) {
  const show = options.mode === "verified";
  const { S, A, B, C, D } = PYRAMID_FRAME;
  const base = options.labels?.base ?? [];
  const apex = options.labels?.apex;
  return (
    <>
      <Geo2DPoint at={S} label={apex} dx={0} dy={-8} showLabel={show && Boolean(apex)} />
      <Geo2DPoint at={A} label={base[0]} dx={-9} dy={-5} showLabel={show && Boolean(base[0])} />
      <Geo2DPoint at={B} label={base[1]} dx={-9} dy={4} showLabel={show && Boolean(base[1])} />
      <Geo2DPoint at={C} label={base[2]} dx={3} dy={9} showLabel={show && Boolean(base[2])} />
      <Geo2DPoint at={D} label={base[3]} dx={10} dy={2} showLabel={show && Boolean(base[3])} />
    </>
  );
}

export const GEOMETRY_TEMPLATES: Readonly<Record<GeometryTemplateId, GeometryTemplateDefinition>> =
  Object.freeze({
    "pyramid.section": {
      id: "pyramid.section",
      family: "pyramid",
      titleVi: "Thiết diện của hình chóp cắt bởi mặt phẳng",
      invariants: [
        "M, N, P, Q là trung điểm chính xác của SA, SB, SC, SD trong phép chiếu affine (MN ∥ PQ ∥ AB, MQ ∥ NP ∥ AD)",
        "Hai cạnh thiết diện phía sau MN, MQ nét đứt; hai cạnh thiết diện phía trước NP, PQ nét liền",
        "Nhãn mặt phẳng nằm ở diềm ngoài, không che lấp miền thiết diện MNPQ",
      ],
      render: (options) => {
        const { S, A, B, C, D } = PYRAMID_FRAME;
        // Trung điểm chính xác trên 4 cạnh bên SA, SB, SC, SD
        const M: Point2D = [(S[0] + A[0]) * 0.5, (S[1] + A[1]) * 0.5]; // (66, 40)
        const N: Point2D = [(S[0] + B[0]) * 0.5, (S[1] + B[1]) * 0.5]; // (51, 51)
        const P: Point2D = [(S[0] + C[0]) * 0.5, (S[1] + C[1]) * 0.5]; // (86, 54)
        const Q: Point2D = [(S[0] + D[0]) * 0.5, (S[1] + D[1]) * 0.5]; // (101, 43)
        // Diềm mặt phẳng cắt mở rộng nhẹ quanh thiết diện MNPQ
        const planeSheet: readonly Point2D[] = [
          [63, 35],
          [38, 53],
          [94, 59],
          [119, 41],
        ];
        const show = options.mode === "verified";
        const sec = options.labels?.section ?? [];
        return (
          <>
            <Geo2DPolygon
              points={planeSheet}
              fill={GEO2D_TOKENS.planeFill}
              stroke={GEO2D_TOKENS.planeStroke}
              strokeWidth={0.95}
            />
            {renderPyramidShell({ rightAngleAtA: true })}
            {/* Miền thiết diện MNPQ nổi bật */}
            <Geo2DPolygon points={[M, N, P, Q]} fill={GEO2D_TOKENS.sectionFill} />
            <Geo2DEdge from={M} to={N} role="section-hidden" />
            <Geo2DEdge from={M} to={Q} role="section-hidden" />
            <Geo2DEdge from={N} to={P} role="section" />
            <Geo2DEdge from={P} to={Q} role="section" />

            {renderPyramidBaseAndApexPoints(options)}
            <Geo2DPoint
              at={M}
              label={sec[0]}
              dx={8}
              dy={-6}
              variant="derived"
              showLabel={show && Boolean(sec[0])}
            />
            <Geo2DPoint
              at={N}
              label={sec[1]}
              dx={-11}
              dy={0}
              variant="derived"
              showLabel={show && Boolean(sec[1])}
            />
            <Geo2DPoint
              at={P}
              label={sec[2]}
              dx={-4}
              dy={9}
              variant="derived"
              showLabel={show && Boolean(sec[2])}
            />
            <Geo2DPoint
              at={Q}
              label={sec[3]}
              dx={10}
              dy={-6}
              variant="derived"
              showLabel={show && Boolean(sec[3])}
            />
            <Geo2DPlaneBadge
              at={[140, 44]}
              label={options.labels?.plane}
              showLabel={show && Boolean(options.labels?.plane)}
            />
          </>
        );
      },
    },

    "pyramid.diagonal-section": {
      id: "pyramid.diagonal-section",
      family: "pyramid",
      titleVi: "Thiết diện của hình chóp theo mặt phẳng chéo",
      invariants: [
        "Mặt phẳng chéo đi qua đỉnh S và đường chéo đáy AC",
        "Đường chéo đáy AC và đường cao SA nét đứt; cạnh bên SC nét liền; tam giác SAC vuông tại A",
      ],
      render: (options) => {
        const { S, A, C } = PYRAMID_FRAME;
        const planeSheet: readonly Point2D[] = [
          [62, 10],
          [62, 69],
          [114, 99],
          [114, 42],
        ];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DPolygon
              points={planeSheet}
              fill={GEO2D_TOKENS.planeFill}
              stroke={GEO2D_TOKENS.planeStroke}
              strokeWidth={0.95}
            />
            {renderPyramidShell({ altitudeRole: "section-hidden", rightAngleAtA: false })}
            <Geo2DPolygon points={[S, A, C]} fill={GEO2D_TOKENS.sectionFill} />
            <Geo2DEdge from={A} to={C} role="section-hidden" />
            <Geo2DEdge from={S} to={A} role="section-hidden" />
            <Geo2DEdge from={S} to={C} role="section" />
            <Geo2DRightAngle at={A} alongA={S} alongB={C} size={6.2} />
            {renderPyramidBaseAndApexPoints(options)}
            <Geo2DPlaneBadge
              at={[130, 38]}
              label={options.labels?.plane}
              showLabel={show && Boolean(options.labels?.plane)}
            />
          </>
        );
      },
    },

    "pyramid.perpendicular": {
      id: "pyramid.perpendicular",
      family: "pyramid",
      titleVi: "Đường thẳng vuông góc với mặt phẳng trong hình chóp",
      invariants: [
        "SA ⊥ (ABCD) tại A và AB ⊥ BC tại B ⇒ BC ⊥ (SAB) tại B",
        "Mặt bên (SAB) được đánh dấu làm mặt phẳng mục tiêu, cạnh BC nổi bật kèm ký hiệu góc vuông tại A và B",
      ],
      render: (options) => {
        const { S, A, B, C } = PYRAMID_FRAME;
        const sabPlaneSheet: readonly Point2D[] = [
          [70, 9],
          [26, 91],
          [70, 70],
        ];
        const bcStart: Point2D = [26, 87.1];
        const bcEnd: Point2D = [118, 95.0];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DPolygon
              points={sabPlaneSheet}
              fill={GEO2D_TOKENS.planeFill}
              stroke={GEO2D_TOKENS.planeStroke}
              strokeWidth={1.05}
            />
            <Geo2DPolygon points={[S, A, B]} fill="rgba(109, 40, 217, 0.14)" />
            {renderPyramidShell({ rightAngleAtA: true })}
            {/* Đường thẳng mục tiêu BC vuông góc với (SAB) tại B */}
            <Geo2DEdge from={bcStart} to={bcEnd} role="target" />
            <Geo2DRightAngle
              at={B}
              alongA={A}
              alongB={C}
              size={6.4}
              color={GEO2D_TOKENS.targetStroke}
            />
            {renderPyramidBaseAndApexPoints(options)}
            <Geo2DPlaneBadge
              at={[30, 42]}
              label={options.labels?.plane}
              showLabel={show && Boolean(options.labels?.plane)}
            />
          </>
        );
      },
    },

    "pyramid.altitude-distance": {
      id: "pyramid.altitude-distance",
      family: "pyramid",
      titleVi: "Mặt phẳng qua một điểm và vuông góc với đường thẳng",
      invariants: [
        "Điểm H nằm chính xác trên cạnh bên SC (t = 0.575 trên đoạn SC)",
        "Đoạn BH ⊥ SC tại H kèm ký hiệu góc vuông và tấm mặt phẳng (α) đi qua B, H vuông góc với SC",
      ],
      render: (options) => {
        const { S, B, C } = PYRAMID_FRAME;
        // H nằm chính xác trên đoạn SC: H = (1 - t)*S + t*C với t = 0.575 => (89, 60)
        const H: Point2D = [89, 60];
        const alphaPlaneSheet: readonly Point2D[] = [
          [32, 90],
          [74, 46],
          [112, 62],
          [70, 96],
        ];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DPolygon
              points={alphaPlaneSheet}
              fill={GEO2D_TOKENS.planeFill}
              stroke={GEO2D_TOKENS.planeStroke}
              strokeWidth={1.0}
            />
            {renderPyramidShell({ rightAngleAtA: true })}
            <Geo2DEdge from={S} to={C} role="target" />
            <Geo2DEdge from={B} to={H} role="altitude" />
            <Geo2DRightAngle at={H} alongA={B} alongB={S} size={6.2} />
            {renderPyramidBaseAndApexPoints(options)}
            <Geo2DPoint
              at={H}
              label={options.labels?.foot}
              dx={10}
              dy={-4}
              variant="derived"
              showLabel={show && Boolean(options.labels?.foot)}
            />
            <Geo2DPlaneBadge
              at={[28, 52]}
              label={options.labels?.plane}
              showLabel={show && Boolean(options.labels?.plane)}
            />
          </>
        );
      },
    },

    "pyramid.volume-height": {
      id: "pyramid.volume-height",
      family: "pyramid",
      titleVi: "Thể tích khối chóp và khoảng cách từ đỉnh đến đáy",
      invariants: [
        "Đường cao SA ⊥ (ABCD) tại A với ký hiệu góc vuông chuẩn xác tại A",
        "Mặt đáy ABCD được tô nhấn làm miền đáy tính diện tích, không sinh điểm H trùng A",
      ],
      render: (options) => {
        return (
          <>
            {renderPyramidShell({ emphasizeBase: true, rightAngleAtA: true })}
            {renderPyramidBaseAndApexPoints(options)}
          </>
        );
      },
    },

    "sphere.plane-section": {
      id: "sphere.plane-section",
      family: "sphere",
      titleVi: "Đường tròn giao của mặt phẳng và mặt cầu",
      invariants: [
        "Mặt cầu tâm I(96, 58) bán kính R = 38; mặt phẳng (P) cắt mặt cầu theo đường tròn tâm H(96, 35)",
        "Tam giác IHM vuông tại H với IH ⊥ HM và M(65.8, 35) nằm đồng thời trên vành cầu và đường tròn giao tuyến",
      ],
      render: (options) => {
        const I: Point2D = [96, 58];
        const H: Point2D = [96, 35];
        // r_sec = sqrt(38^2 - 23^2) = sqrt(915) ≈ 30.2 => M = (96 - 30.2, 35) = (65.8, 35)
        const M: Point2D = [65.8, 35];
        const planeSheet: readonly Point2D[] = [
          [34, 43],
          [148, 43],
          [162, 27],
          [48, 27],
        ];
        const show = options.mode === "verified";
        return (
          <>
            {/* Tấm mặt phẳng cắt (P) */}
            <Geo2DPolygon
              points={planeSheet}
              fill={GEO2D_TOKENS.planeFill}
              stroke={GEO2D_TOKENS.planeStroke}
              strokeWidth={0.95}
            />
            {/* Khối cầu tâm I */}
            <circle
              cx={I[0]}
              cy={I[1]}
              r={38}
              fill={GEO2D_TOKENS.shellFill}
              stroke={GEO2D_TOKENS.ink}
              strokeWidth={1.6}
            />
            {/* Đường tròn lớn xích đạo tham chiếu */}
            <Geo2DEllipseRim
              center={I}
              rx={38}
              ry={10.5}
              frontRole="hidden"
              backRole="hidden"
            />
            {/* Đường tròn giao tuyến tâm H, bán kính r = HM */}
            <Geo2DEllipseRim
              center={H}
              rx={30.2}
              ry={8.2}
              fill={GEO2D_TOKENS.sectionFill}
              frontRole="section"
              backRole="section-hidden"
            />
            {/* Tam giác vuông IHM: IH ⊥ HM tại H */}
            <Geo2DEdge from={I} to={H} role="altitude-hidden" />
            <Geo2DEdge from={H} to={M} role="section-hidden" />
            <Geo2DEdge from={I} to={M} role="section-hidden" />
            <Geo2DRightAngle at={H} alongA={I} alongB={M} size={5.8} />

            <Geo2DPoint
              at={I}
              label={options.labels?.center}
              dx={8}
              dy={6}
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPoint
              at={H}
              label={options.labels?.foot}
              dx={8}
              dy={-7}
              variant="derived"
              showLabel={show && Boolean(options.labels?.foot)}
            />
            <Geo2DPoint
              at={M}
              label={options.labels?.rimPoint}
              dx={-10}
              dy={-6}
              variant="derived"
              showLabel={show && Boolean(options.labels?.rimPoint)}
            />
            <Geo2DPlaneBadge
              at={[24, 35]}
              label={options.labels?.plane}
              showLabel={show && Boolean(options.labels?.plane)}
            />
          </>
        );
      },
    },

    "sphere.basic-radius": {
      id: "sphere.basic-radius",
      family: "sphere",
      titleVi: "Bán kính, diện tích và thể tích khối cầu",
      invariants: [
        "Mặt cầu tâm I(90, 55), bán kính IA nối từ tâm I đến điểm A(128, 55) nằm trên đường tròn lớn",
      ],
      render: (options) => {
        const I: Point2D = [90, 55];
        const A: Point2D = [128, 55];
        const show = options.mode === "verified";
        return (
          <>
            <circle
              cx={I[0]}
              cy={I[1]}
              r={38}
              fill={GEO2D_TOKENS.shellFill}
              stroke={GEO2D_TOKENS.ink}
              strokeWidth={1.6}
            />
            <Geo2DEllipseRim
              center={I}
              rx={38}
              ry={11.5}
              fill="rgba(148, 163, 184, 0.08)"
              frontRole="solid"
              backRole="hidden"
            />
            <Geo2DEdge from={I} to={A} role="section-hidden" />
            <Geo2DPoint
              at={I}
              label={options.labels?.center}
              dx={-8}
              dy={-7}
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPoint
              at={A}
              label={options.labels?.rimPoint}
              dx={10}
              dy={0}
              variant="derived"
              showLabel={show && Boolean(options.labels?.rimPoint)}
            />
          </>
        );
      },
    },

    "cylinder.perpendicular-section": {
      id: "cylinder.perpendicular-section",
      family: "cylinder",
      titleVi: "Thiết diện vuông góc với trục của hình trụ",
      invariants: [
        "Hình trụ đứng có trục OO′, M là trung điểm OO′",
        "Mặt phẳng (α) qua M vuông góc OO′ cắt hình trụ theo đường tròn (M, R) bằng hai đáy",
      ],
      render: (options) => {
        const OPrime: Point2D = [96, 22];
        const M: Point2D = [96, 55];
        const O: Point2D = [96, 88];
        const rx = 33;
        const ry = 9;
        const planeSheet: readonly Point2D[] = [
          [36, 65],
          [148, 65],
          [160, 45],
          [48, 45],
        ];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DPolygon
              points={planeSheet}
              fill={GEO2D_TOKENS.planeFill}
              stroke={GEO2D_TOKENS.planeStroke}
              strokeWidth={0.95}
            />
            <Geo2DPolygon
              points={[
                [OPrime[0] - rx, OPrime[1]],
                [O[0] - rx, O[1]],
                [O[0] + rx, O[1]],
                [OPrime[0] + rx, OPrime[1]],
              ]}
              fill={GEO2D_TOKENS.shellFill}
            />
            {/* Đáy dưới (O) */}
            <Geo2DEllipseRim
              center={O}
              rx={rx}
              ry={ry}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="hidden"
            />
            {/* Thiết diện tròn tại M */}
            <Geo2DEllipseRim
              center={M}
              rx={rx}
              ry={ry}
              fill={GEO2D_TOKENS.sectionFill}
              frontRole="section"
              backRole="section-hidden"
            />
            {/* Đáy trên (O') */}
            <Geo2DEllipseRim
              center={OPrime}
              rx={rx}
              ry={ry}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="solid"
              fullVisible
            />
            {/* Hai đường sinh biên & trục OO' */}
            <Geo2DEdge from={[OPrime[0] - rx, OPrime[1]]} to={[O[0] - rx, O[1]]} role="solid" />
            <Geo2DEdge from={[OPrime[0] + rx, OPrime[1]]} to={[O[0] + rx, O[1]]} role="solid" />
            <Geo2DEdge from={OPrime} to={O} role="altitude-hidden" />
            <Geo2DRightAngle at={M} alongA={OPrime} alongB={[M[0] + rx, M[1]]} size={5.8} />

            <Geo2DPoint
              at={OPrime}
              label={options.labels?.topCenter}
              dx={11}
              dy={-1}
              showLabel={show && Boolean(options.labels?.topCenter)}
            />
            <Geo2DPoint
              at={M}
              label={options.labels?.foot}
              dx={-9}
              dy={-4}
              variant="derived"
              showLabel={show && Boolean(options.labels?.foot)}
            />
            <Geo2DPoint
              at={O}
              label={options.labels?.center}
              dx={10}
              dy={-1}
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPlaneBadge
              at={[24, 55]}
              label={options.labels?.plane}
              showLabel={show && Boolean(options.labels?.plane)}
            />
          </>
        );
      },
    },

    "cylinder.oblique-axis": {
      id: "cylinder.oblique-axis",
      family: "cylinder",
      titleVi: "Hình trụ tròn xoay có trục đặt nghiêng",
      invariants: [
        "Trục OO′ nghiêng theo phương u = (0.6, -0.8); hai mặt đáy vuông góc chính xác với OO′ (phương bán kính n = (0.8, 0.6), góc xoay 36.87°)",
        "Bán kính đáy OA ⊥ OO′ tại O được bảo toàn góc vuông chính xác (OA · OO′ = 0)",
      ],
      render: (options) => {
        const O: Point2D = [72, 75];
        const OPrime: Point2D = [108, 27];
        // Phương vuông góc với OO' = (36, -48) là n = (0.8, 0.6), bán kính r = 26 => offset = (20.8, 15.6)
        const A: Point2D = [92.8, 90.6];
        const BBot: Point2D = [51.2, 59.4];
        const ATop: Point2D = [128.8, 42.6];
        const BTop: Point2D = [87.2, 11.4];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DPolygon points={[BBot, A, ATop, BTop]} fill={GEO2D_TOKENS.shellFill} />
            <Geo2DEllipseRim
              center={O}
              rx={26}
              ry={9.2}
              rotationDeg={36.87}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="hidden"
            />
            <Geo2DEllipseRim
              center={OPrime}
              rx={26}
              ry={9.2}
              rotationDeg={36.87}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="solid"
              fullVisible
            />
            {/* Hai đường sinh biên song song với OO' */}
            <Geo2DEdge from={BBot} to={BTop} role="solid" />
            <Geo2DEdge from={A} to={ATop} role="solid" />
            {/* Trục OO' và bán kính đáy OA ⊥ OO' */}
            <Geo2DEdge from={O} to={OPrime} role="altitude-hidden" />
            <Geo2DEdge from={O} to={A} role="section-hidden" />
            <Geo2DRightAngle at={O} alongA={OPrime} alongB={A} size={5.8} />

            <Geo2DPoint
              at={O}
              label={options.labels?.center}
              dx={-9}
              dy={3}
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPoint
              at={OPrime}
              label={options.labels?.topCenter}
              dx={9}
              dy={-6}
              showLabel={show && Boolean(options.labels?.topCenter)}
            />
            <Geo2DPoint
              at={A}
              label={options.labels?.rimPoint}
              dx={8}
              dy={6}
              variant="derived"
              showLabel={show && Boolean(options.labels?.rimPoint)}
            />
          </>
        );
      },
    },

    "cylinder.right-basic": {
      id: "cylinder.right-basic",
      family: "cylinder",
      titleVi: "Hình trụ đứng cơ bản",
      invariants: [
        "Hình trụ đứng tâm O, O′, trục OO′ ⊥ OA tại O",
      ],
      render: (options) => {
        const OPrime: Point2D = [90, 22];
        const O: Point2D = [90, 86];
        const rx = 33;
        const ry = 9.5;
        const A: Point2D = [O[0] + rx, O[1]];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DPolygon
              points={[
                [OPrime[0] - rx, OPrime[1]],
                [O[0] - rx, O[1]],
                [O[0] + rx, O[1]],
                [OPrime[0] + rx, OPrime[1]],
              ]}
              fill={GEO2D_TOKENS.shellFill}
            />
            <Geo2DEllipseRim
              center={O}
              rx={rx}
              ry={ry}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="hidden"
            />
            <Geo2DEllipseRim
              center={OPrime}
              rx={rx}
              ry={ry}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="solid"
              fullVisible
            />
            <Geo2DEdge from={[OPrime[0] - rx, OPrime[1]]} to={[O[0] - rx, O[1]]} role="solid" />
            <Geo2DEdge from={[OPrime[0] + rx, OPrime[1]]} to={[O[0] + rx, O[1]]} role="solid" />
            <Geo2DEdge from={OPrime} to={O} role="altitude-hidden" />
            <Geo2DEdge from={O} to={A} role="section-hidden" />
            <Geo2DRightAngle at={O} alongA={OPrime} alongB={A} size={5.8} />

            <Geo2DPoint
              at={OPrime}
              label={options.labels?.topCenter}
              dx={0}
              dy={-8}
              showLabel={show && Boolean(options.labels?.topCenter)}
            />
            <Geo2DPoint
              at={O}
              label={options.labels?.center}
              dx={-8}
              dy={6}
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPoint
              at={A}
              label={options.labels?.rimPoint}
              dx={9}
              dy={2}
              variant="derived"
              showLabel={show && Boolean(options.labels?.rimPoint)}
            />
          </>
        );
      },
    },

    "cone.axial-section": {
      id: "cone.axial-section",
      family: "cone",
      titleVi: "Thiết diện qua trục của hình nón",
      invariants: [
        "Hình nón đỉnh S(90, 15), tâm đáy O(90, 85), đường kính đáy AB đi qua O",
        "Thiết diện qua trục là tam giác cân SAB với SO ⊥ AB tại O",
      ],
      render: (options) => {
        const S: Point2D = [90, 15];
        const O: Point2D = [90, 85];
        const rx = 42;
        const ry = 11.5;
        const A: Point2D = [O[0] - rx, O[1]];
        const B: Point2D = [O[0] + rx, O[1]];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DEllipseRim
              center={O}
              rx={rx}
              ry={ry}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="hidden"
            />
            {/* Tam giác thiết diện qua trục SAB */}
            <Geo2DPolygon points={[S, A, B]} fill={GEO2D_TOKENS.sectionFill} />
            <Geo2DEdge from={A} to={B} role="section-hidden" />
            <Geo2DEdge from={S} to={O} role="altitude-hidden" />
            <Geo2DEdge from={S} to={A} role="section" />
            <Geo2DEdge from={S} to={B} role="section" />
            <Geo2DRightAngle at={O} alongA={S} alongB={A} size={5.8} />

            <Geo2DPoint
              at={S}
              label={options.labels?.apex}
              dx={0}
              dy={-8}
              showLabel={show && Boolean(options.labels?.apex)}
            />
            <Geo2DPoint
              at={O}
              label={options.labels?.center}
              dx={7}
              dy={6}
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPoint
              at={A}
              label={options.labels?.rimPoint}
              dx={-10}
              dy={2}
              variant="derived"
              showLabel={show && Boolean(options.labels?.rimPoint)}
            />
            <Geo2DPoint
              at={B}
              label={options.labels?.secondRimPoint}
              dx={10}
              dy={2}
              variant="derived"
              showLabel={show && Boolean(options.labels?.secondRimPoint)}
            />
          </>
        );
      },
    },

    "cone.slant-generator": {
      id: "cone.slant-generator",
      family: "cone",
      titleVi: "Đường sinh, chiều cao và bán kính đáy hình nón",
      invariants: [
        "Hình nón đỉnh S(90, 15), tâm đáy O(90, 85), điểm A trên đường tròn đáy",
        "Tam giác vuông SOA vuông tại O (SO ⊥ OA), cạnh huyền là đường sinh SA",
      ],
      render: (options) => {
        const S: Point2D = [90, 15];
        const O: Point2D = [90, 85];
        const rx = 42;
        const ry = 11.5;
        const A: Point2D = [O[0] - rx, O[1]];
        const B: Point2D = [O[0] + rx, O[1]];
        const show = options.mode === "verified";
        return (
          <>
            <Geo2DPolygon points={[S, A, B]} fill={GEO2D_TOKENS.shellFill} />
            <Geo2DEllipseRim
              center={O}
              rx={rx}
              ry={ry}
              fill={GEO2D_TOKENS.baseFill}
              frontRole="solid"
              backRole="hidden"
            />
            {/* Tam giác vuông đặc trưng SOA */}
            <Geo2DPolygon points={[S, O, A]} fill={GEO2D_TOKENS.altitudeFill} />
            <Geo2DEdge from={S} to={B} role="solid" />
            <Geo2DEdge from={S} to={O} role="altitude-hidden" />
            <Geo2DEdge from={O} to={A} role="section-hidden" />
            <Geo2DEdge from={S} to={A} role="section" />
            <Geo2DRightAngle at={O} alongA={S} alongB={A} size={5.8} />

            <Geo2DPoint
              at={S}
              label={options.labels?.apex}
              dx={0}
              dy={-8}
              showLabel={show && Boolean(options.labels?.apex)}
            />
            <Geo2DPoint
              at={O}
              label={options.labels?.center}
              dx={6}
              dy={8}
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPoint
              at={A}
              label={options.labels?.rimPoint}
              dx={-10}
              dy={2}
              variant="derived"
              showLabel={show && Boolean(options.labels?.rimPoint)}
            />
          </>
        );
      },
    },
  });

export function getGeometryTemplate(id: GeometryTemplateId): GeometryTemplateDefinition | undefined {
  return GEOMETRY_TEMPLATES[id];
}

export function listGeometryTemplates(): GeometryTemplateDefinition[] {
  return Object.values(GEOMETRY_TEMPLATES);
}
