import type { ReactNode } from "react";
import type { GeometryFamilyId } from "./family-icons";
import {
  Cone2D,
  Cube2D,
  Cylinder2D,
  DEFAULT_CUBE_FRAME,
  DEFAULT_PRISM_FRAME,
  DEFAULT_PYRAMID_FRAME,
  GEO2D_TOKENS,
  Geo2DEllipseRim,
  Geo2DPoint,
  Geo2DPolygon,
  PerpendicularMarker2D,
  Plane2D,
  Prism2D,
  Pyramid2D,
  Section2D,
  Segment2D,
  Sphere2D,
  type Point2D,
} from "./primitives";

export type GeometryTemplateId =
  | "pyramid.section"
  | "pyramid.diagonal-section"
  | "pyramid.perpendicular"
  | "pyramid.altitude-distance"
  | "pyramid.volume-height"
  | "pyramid.circumscribed-sphere"
  | "sphere.plane-section"
  | "sphere.basic-radius"
  | "cylinder.perpendicular-section"
  | "cylinder.oblique-axis"
  | "cylinder.right-basic"
  | "cone.axial-section"
  | "cone.slant-generator"
  | "cone.inscribed-cylinder"
  | "cube.plane-section"
  | "prism.plane-section"
  | "pyramid.point-to-plane-distance"
  | "pyramid.dihedral-angle"
  | "pyramid.skew-lines-distance"
  | "oxyz.line-plane-intersection"
  | "sphere.tangent-plane"
  | "cone.parallel-section";

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
   * `"generic"`: Minh họa khái quát cho dạng bài — tuyệt đối không gán nhãn điểm/mặt phẳng tùy tiện (§4.A1, §4.A4).
   */
  mode: "verified" | "generic";
  labels?: VerifiedTemplateLabels;
}

export interface GeometryTemplateDefinition {
  id: GeometryTemplateId;
  family: Exclude<GeometryFamilyId, "neutral">;
  secondaryFamilies?: readonly Exclude<GeometryFamilyId, "neutral">[];
  titleVi: string;
  invariants: readonly string[];
  render: (options: TemplateRenderOptions) => ReactNode;
}

const PYRAMID_FRAME = DEFAULT_PYRAMID_FRAME;

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
        "Tổ hợp từ Plane2D + Pyramid2D + Section2D",
      ],
      render: (options) => {
        const { S, A, B, C, D } = PYRAMID_FRAME;
        const M: Point2D = [(S[0] + A[0]) * 0.5, (S[1] + A[1]) * 0.5]; // (66, 40)
        const N: Point2D = [(S[0] + B[0]) * 0.5, (S[1] + B[1]) * 0.5]; // (51, 51)
        const P: Point2D = [(S[0] + C[0]) * 0.5, (S[1] + C[1]) * 0.5]; // (86, 54)
        const Q: Point2D = [(S[0] + D[0]) * 0.5, (S[1] + D[1]) * 0.5]; // (101, 43)
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
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[140, 44]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Pyramid2D rightAngleAtA />
            <Section2D
              kind="polygon"
              points={[M, N, P, Q]}
              hiddenEdges={[true, false, false, true]}
            />
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
        "Tổ hợp từ Plane2D + Pyramid2D + Section2D + PerpendicularMarker2D",
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
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[130, 38]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Pyramid2D altitudeRole="section-hidden" rightAngleAtA={false} />
            <Section2D
              kind="polygon"
              points={[S, A, C]}
              hiddenEdges={[true, true, false]}
            />
            <PerpendicularMarker2D at={A} alongA={S} alongB={C} size={6.2} />
            {renderPyramidBaseAndApexPoints(options)}
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
        "Tổ hợp từ Plane2D + Pyramid2D + Segment2D + PerpendicularMarker2D",
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
            <Plane2D
              points={sabPlaneSheet}
              strokeWidth={1.05}
              label={options.labels?.plane}
              labelAt={[30, 42]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Geo2DPolygon points={[S, A, B]} fill="rgba(109, 40, 217, 0.14)" />
            <Pyramid2D rightAngleAtA />
            <Segment2D from={bcStart} to={bcEnd} role="target" />
            <PerpendicularMarker2D
              at={B}
              alongA={A}
              alongB={C}
              size={6.4}
              color={GEO2D_TOKENS.targetStroke}
            />
            {renderPyramidBaseAndApexPoints(options)}
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
        "Tổ hợp từ Plane2D + Pyramid2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const { S, B, C } = PYRAMID_FRAME;
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
            <Plane2D
              points={alphaPlaneSheet}
              strokeWidth={1.0}
              label={options.labels?.plane}
              labelAt={[28, 52]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Pyramid2D rightAngleAtA />
            <Segment2D from={S} to={C} role="target" />
            <Segment2D from={B} to={H} role="altitude" />
            <PerpendicularMarker2D at={H} alongA={B} alongB={S} size={6.2} />
            {renderPyramidBaseAndApexPoints(options)}
            <Geo2DPoint
              at={H}
              label={options.labels?.foot}
              dx={10}
              dy={-4}
              variant="derived"
              showLabel={show && Boolean(options.labels?.foot)}
            />
          </>
        );
      },
    },

    "pyramid.volume-height": {
      id: "pyramid.volume-height",
      family: "pyramid",
      titleVi: "Hình chóp đơn & chiều cao khối chóp",
      invariants: [
        "Đường cao SA ⊥ (ABCD) tại A với ký hiệu góc vuông chuẩn xác tại A",
        "Mặt đáy ABCD được tô nhấn làm miền đáy tính diện tích, không sinh điểm H trùng A",
        "Tổ hợp trực tiếp từ Pyramid2D",
      ],
      render: (options) => {
        return (
          <>
            <Pyramid2D emphasizeBase rightAngleAtA />
            {renderPyramidBaseAndApexPoints(options)}
          </>
        );
      },
    },

    "pyramid.circumscribed-sphere": {
      id: "pyramid.circumscribed-sphere",
      family: "pyramid",
      secondaryFamilies: ["sphere"],
      titleVi: "Hình chóp nội tiếp mặt cầu",
      invariants: [
        "Mặt cầu tâm I(90, 56) bán kính R = 40 ngoại tiếp hình chóp S.ABCD",
        "Đỉnh S(90, 16) nằm chính xác trên cực bắc mặt cầu; 4 đỉnh đáy A, B, C, D nằm chính xác trên đường tròn giao tuyến đáy tâm O(90, 72) bán kính r = 36.6",
        "Đường cao SO đi qua tâm cầu I và vuông góc với đáy tại O",
        "Tổ hợp từ Sphere2D + Pyramid2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const I: Point2D = [90, 56];
        const O: Point2D = [90, 72];
        const S: Point2D = [90, 16];
        // r_base = sqrt(40^2 - 16^2) = 36.66; 4 đỉnh trên elip đáy (O, rx=36.6, ry=9.5) tại ±35°, ±145°
        const A: Point2D = [60.0, 66.6];
        const B: Point2D = [60.0, 77.4];
        const C: Point2D = [120.0, 77.4];
        const D: Point2D = [120.0, 66.6];
        const show = options.mode === "verified";
        const base = options.labels?.base ?? [];
        return (
          <>
            {/* Mặt cầu ngoại tiếp */}
            <Sphere2D
              center={I}
              radius={40}
              equatorRy={10.2}
              equatorMode="all-hidden"
              fill={GEO2D_TOKENS.secondaryShellFill}
              stroke={GEO2D_TOKENS.secondaryStroke}
              strokeWidth={1.4}
            />
            {/* Đường tròn ngoại tiếp đa giác đáy ABCD trên mặt cầu */}
            <Geo2DEllipseRim
              center={O}
              rx={36.6}
              ry={9.5}
              fill="none"
              frontRole="secondary-hidden"
              backRole="secondary-hidden"
            />
            {/* Hình chóp S.ABCD nội tiếp */}
            <Pyramid2D
              apex={S}
              base={[A, B, C, D]}
              emphasizeBase
              altitudeFoot={O}
              altitudeRole="altitude-hidden"
              rightAngleAtA={false}
            />
            {/* Đường chéo đáy AC qua O và bán kính cầu IS, IC */}
            <Segment2D from={A} to={C} role="hidden" />
            <Segment2D from={I} to={C} role="section-hidden" />
            <PerpendicularMarker2D at={O} alongA={S} alongB={C} size={5.4} />

            <Geo2DPoint
              at={S}
              label={options.labels?.apex}
              dx={0}
              dy={-7}
              showLabel={show && Boolean(options.labels?.apex)}
            />
            <Geo2DPoint
              at={I}
              label={options.labels?.center}
              dx={-9}
              dy={-2}
              variant="derived"
              showLabel={show && Boolean(options.labels?.center)}
            />
            <Geo2DPoint
              at={O}
              label={options.labels?.foot}
              dx={-8}
              dy={7}
              variant="altitude"
              showLabel={show && Boolean(options.labels?.foot)}
            />
            <Geo2DPoint at={A} label={base[0]} dx={-9} dy={-4} showLabel={show && Boolean(base[0])} />
            <Geo2DPoint at={B} label={base[1]} dx={-9} dy={5} showLabel={show && Boolean(base[1])} />
            <Geo2DPoint at={C} label={base[2]} dx={9} dy={5} showLabel={show && Boolean(base[2])} />
            <Geo2DPoint at={D} label={base[3]} dx={9} dy={-4} showLabel={show && Boolean(base[3])} />
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
        "Tổ hợp từ Plane2D + Sphere2D + Section2D(ellipse) + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const I: Point2D = [96, 58];
        const H: Point2D = [96, 35];
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
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[24, 35]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Sphere2D center={I} radius={38} equatorRy={10.5} equatorMode="all-hidden" />
            <Section2D kind="ellipse" center={H} rx={30.2} ry={8.2} />
            <Segment2D from={I} to={H} role="altitude-hidden" />
            <Segment2D from={H} to={M} role="section-hidden" />
            <Segment2D from={I} to={M} role="section-hidden" />
            <PerpendicularMarker2D at={H} alongA={I} alongB={M} size={5.8} />

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
          </>
        );
      },
    },

    "sphere.basic-radius": {
      id: "sphere.basic-radius",
      family: "sphere",
      titleVi: "Hình cầu đơn — tâm và bán kính",
      invariants: [
        "Mặt cầu tâm I(90, 55), bán kính IA nối từ tâm I đến điểm A(128, 55) nằm trên đường tròn lớn",
        "Tổ hợp từ Sphere2D + Segment2D",
      ],
      render: (options) => {
        const I: Point2D = [90, 55];
        const A: Point2D = [128, 55];
        const show = options.mode === "verified";
        return (
          <>
            <Sphere2D center={I} radius={38} equatorRy={11.5} equatorMode="front-solid" />
            <Segment2D from={I} to={A} role="section-hidden" />
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
        "Tổ hợp từ Plane2D + Cylinder2D + Section2D(ellipse) + PerpendicularMarker2D",
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
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[24, 55]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Cylinder2D topCenter={OPrime} bottomCenter={O} rx={rx} ry={ry} showAxis />
            <Section2D kind="ellipse" center={M} rx={rx} ry={ry} />
            <PerpendicularMarker2D at={M} alongA={OPrime} alongB={[M[0] + rx, M[1]]} size={5.8} />

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
            <Segment2D from={BBot} to={BTop} role="solid" />
            <Segment2D from={A} to={ATop} role="solid" />
            <Segment2D from={O} to={OPrime} role="altitude-hidden" />
            <Segment2D from={O} to={A} role="section-hidden" />
            <PerpendicularMarker2D at={O} alongA={OPrime} alongB={A} size={5.8} />

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
      titleVi: "Hình trụ đơn — trục và bán kính đáy",
      invariants: [
        "Hình trụ đứng tâm O, O′, trục OO′ ⊥ OA tại O",
        "Tổ hợp từ Cylinder2D + Segment2D + PerpendicularMarker2D",
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
            <Cylinder2D topCenter={OPrime} bottomCenter={O} rx={rx} ry={ry} showAxis />
            <Segment2D from={O} to={A} role="section-hidden" />
            <PerpendicularMarker2D at={O} alongA={OPrime} alongB={A} size={5.8} />

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
        "Tổ hợp từ Cone2D + Section2D(polygon) + PerpendicularMarker2D",
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
            <Cone2D apex={S} baseCenter={O} rx={rx} ry={ry} showAxis />
            <Section2D
              kind="polygon"
              points={[S, A, B]}
              hiddenEdges={[false, true, false]}
            />
            <Segment2D from={S} to={O} role="altitude-hidden" />
            <PerpendicularMarker2D at={O} alongA={S} alongB={A} size={5.8} />

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
      titleVi: "Hình nón đơn — đường sinh, chiều cao và bán kính đáy",
      invariants: [
        "Hình nón đỉnh S(90, 15), tâm đáy O(90, 85), điểm A trên đường tròn đáy",
        "Tam giác vuông SOA vuông tại O (SO ⊥ OA), cạnh huyền là đường sinh SA",
        "Tổ hợp từ Cone2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const S: Point2D = [90, 15];
        const O: Point2D = [90, 85];
        const rx = 42;
        const ry = 11.5;
        const A: Point2D = [O[0] - rx, O[1]];
        const show = options.mode === "verified";
        return (
          <>
            <Cone2D apex={S} baseCenter={O} rx={rx} ry={ry} showAxis />
            <Geo2DPolygon points={[S, O, A]} fill={GEO2D_TOKENS.altitudeFill} />
            <Segment2D from={S} to={O} role="altitude-hidden" />
            <Segment2D from={O} to={A} role="section-hidden" />
            <Segment2D from={S} to={A} role="section" />
            <PerpendicularMarker2D at={O} alongA={S} alongB={A} size={5.8} />

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

    "cone.inscribed-cylinder": {
      id: "cone.inscribed-cylinder",
      family: "cone",
      secondaryFamilies: ["cylinder"],
      titleVi: "Hình nón nội tiếp hình trụ",
      invariants: [
        "Hình trụ đứng tâm hai đáy O(90, 86), O′(90, 22) bán kính R = 34",
        "Hình nón có đỉnh S trùng tâm đáy trên O′(90, 22) và chung đường tròn đáy dưới (O, R) với hình trụ",
        "Trục SO ⊥ OA tại O; hai đường sinh SA, SB nối từ tâm đáy trên xuống vành đáy dưới",
        "Tổ hợp từ Cylinder2D + Cone2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const S: Point2D = [90, 22];
        const O: Point2D = [90, 86];
        const rx = 34;
        const ry = 9.5;
        const A: Point2D = [O[0] - rx, O[1]];
        const B: Point2D = [O[0] + rx, O[1]];
        const show = options.mode === "verified";
        return (
          <>
            {/* Hình trụ ngoại tiếp */}
            <Cylinder2D
              topCenter={S}
              bottomCenter={O}
              rx={rx}
              ry={ry}
              showAxis={false}
              emphasizeBases={false}
              variant="secondary"
            />
            {/* Hình nón nội tiếp chung đáy dưới và có đỉnh tại tâm đáy trên */}
            <Cone2D
              apex={S}
              baseCenter={O}
              rx={rx}
              ry={ry}
              showAxis
              emphasizeBase
            />
            <Geo2DPolygon points={[S, A, B]} fill={GEO2D_TOKENS.sectionFill} />
            <Segment2D from={S} to={A} role="section" />
            <Segment2D from={S} to={B} role="section" />
            <Segment2D from={O} to={B} role="section-hidden" />
            <PerpendicularMarker2D at={O} alongA={S} alongB={B} size={5.8} />

            <Geo2DPoint
              at={S}
              label={options.labels?.apex ?? options.labels?.topCenter}
              dx={0}
              dy={-8}
              showLabel={show && Boolean(options.labels?.apex ?? options.labels?.topCenter)}
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

    "cube.plane-section": {
      id: "cube.plane-section",
      family: "pyramid",
      titleVi: "Thiết diện lục giác đều của hình lập phương cắt bởi mặt phẳng",
      invariants: [
        "Hình lập phương ABCD.A'B'C'D' với 3 cạnh khuất AB, AD, AA' xuất phát từ đỉnh khuất A",
        "6 đỉnh thiết diện M, N, E, P, F, Q lần lượt là trung điểm chính xác của AD, CD, CC', B'C', A'B', AA' (MN ∥ FP, NE ∥ QF, EP ∥ MQ)",
        "Tổ hợp từ Plane2D + Cube2D + Section2D",
      ],
      render: (options) => {
        const { A, B, C, D, A_prime: Ap, B_prime: Bp, C_prime: Cp } = DEFAULT_CUBE_FRAME;
        const M: Point2D = [(A[0] + D[0]) * 0.5, (A[1] + D[1]) * 0.5];
        const N: Point2D = [(C[0] + D[0]) * 0.5, (C[1] + D[1]) * 0.5];
        const E: Point2D = [(C[0] + Cp[0]) * 0.5, (C[1] + Cp[1]) * 0.5];
        const P: Point2D = [(Bp[0] + Cp[0]) * 0.5, (Bp[1] + Cp[1]) * 0.5];
        const F: Point2D = [(Ap[0] + Bp[0]) * 0.5, (Ap[1] + Bp[1]) * 0.5];
        const Q: Point2D = [(A[0] + Ap[0]) * 0.5, (A[1] + Ap[1]) * 0.5];
        const planeSheet: readonly Point2D[] = [
          [32, 24],
          [116, 16],
          [142, 86],
          [56, 94],
        ];
        const show = options.mode === "verified";
        const base = options.labels?.base ?? [];
        const sec = options.labels?.section ?? [];
        return (
          <>
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[148, 34]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Cube2D />
            <Section2D
              kind="polygon"
              points={[M, N, E, P, F, Q]}
              hiddenEdges={[true, false, false, false, false, true]}
            />
            <Geo2DPoint at={A} label={base[0]} dx={-8} dy={-4} showLabel={show && Boolean(base[0])} />
            <Geo2DPoint at={B} label={base[1]} dx={-9} dy={5} showLabel={show && Boolean(base[1])} />
            <Geo2DPoint at={C} label={base[2]} dx={4} dy={9} showLabel={show && Boolean(base[2])} />
            <Geo2DPoint at={D} label={base[3]} dx={10} dy={2} showLabel={show && Boolean(base[3])} />
            <Geo2DPoint at={M} label={sec[0]} dx={7} dy={-6} variant="derived" showLabel={show && Boolean(sec[0])} />
            <Geo2DPoint at={N} label={sec[1]} dx={9} dy={6} variant="derived" showLabel={show && Boolean(sec[1])} />
            <Geo2DPoint at={E} label={sec[2]} dx={9} dy={0} variant="derived" showLabel={show && Boolean(sec[2])} />
            <Geo2DPoint at={P} label={sec[3]} dx={0} dy={-8} variant="derived" showLabel={show && Boolean(sec[3])} />
            <Geo2DPoint at={F} label={sec[4]} dx={-9} dy={-5} variant="derived" showLabel={show && Boolean(sec[4])} />
            <Geo2DPoint at={Q} label={sec[5]} dx={-9} dy={2} variant="derived" showLabel={show && Boolean(sec[5])} />
          </>
        );
      },
    },

    "prism.plane-section": {
      id: "prism.plane-section",
      family: "pyramid",
      titleVi: "Thiết diện của lăng trụ đứng tam giác cắt bởi mặt phẳng",
      invariants: [
        "Lăng trụ đứng tam giác ABC.A'B'C' với AA' ⊥ (ABC)",
        "Thiết diện ngũ giác MNPQE cắt cả 5 mặt của lăng trụ với M ∈ AB (t=0.75), N trung điểm BC, P trung điểm CC', Q trung điểm A'C', E ∈ A'B' (t=0.25)",
        "Tổ hợp từ Plane2D + Prism2D + Section2D",
      ],
      render: (options) => {
        const { A, B, C, A_prime: Ap, B_prime: Bp, C_prime: Cp } = DEFAULT_PRISM_FRAME;
        const M: Point2D = [A[0] + (B[0] - A[0]) * 0.75, A[1] + (B[1] - A[1]) * 0.75];
        const N: Point2D = [(B[0] + C[0]) * 0.5, (B[1] + C[1]) * 0.5];
        const P: Point2D = [(C[0] + Cp[0]) * 0.5, (C[1] + Cp[1]) * 0.5];
        const Q: Point2D = [(Ap[0] + Cp[0]) * 0.5, (Ap[1] + Cp[1]) * 0.5];
        const E: Point2D = [Ap[0] + (Bp[0] - Ap[0]) * 0.25, Ap[1] + (Bp[1] - Ap[1]) * 0.25];
        const planeSheet: readonly Point2D[] = [
          [32, 22],
          [134, 24],
          [138, 90],
          [28, 92],
        ];
        const show = options.mode === "verified";
        const base = options.labels?.base ?? [];
        const sec = options.labels?.section ?? [];
        return (
          <>
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[148, 36]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Prism2D rightAngleAtA />
            <Section2D
              kind="polygon"
              points={[M, N, P, Q, E]}
              hiddenEdges={[true, false, true, false, true]}
            />
            <Geo2DPoint at={A} label={base[0]} dx={-9} dy={-4} showLabel={show && Boolean(base[0])} />
            <Geo2DPoint at={B} label={base[1]} dx={-9} dy={6} showLabel={show && Boolean(base[1])} />
            <Geo2DPoint at={C} label={base[2]} dx={9} dy={5} showLabel={show && Boolean(base[2])} />
            <Geo2DPoint at={M} label={sec[0]} dx={-10} dy={-2} variant="derived" showLabel={show && Boolean(sec[0])} />
            <Geo2DPoint at={N} label={sec[1]} dx={0} dy={9} variant="derived" showLabel={show && Boolean(sec[1])} />
            <Geo2DPoint at={P} label={sec[2]} dx={10} dy={0} variant="derived" showLabel={show && Boolean(sec[2])} />
            <Geo2DPoint at={Q} label={sec[3]} dx={6} dy={-7} variant="derived" showLabel={show && Boolean(sec[3])} />
            <Geo2DPoint at={E} label={sec[4]} dx={-9} dy={-5} variant="derived" showLabel={show && Boolean(sec[4])} />
          </>
        );
      },
    },

    "pyramid.point-to-plane-distance": {
      id: "pyramid.point-to-plane-distance",
      family: "pyramid",
      titleVi: "Khoảng cách từ điểm A đến mặt phẳng nghiêng (SBC)",
      invariants: [
        "Hình chóp S.ABC có SA ⊥ (ABC) tại A, đáy ABC vuông tại B",
        "Hình chiếu vuông góc H của A trên mặt phẳng nghiêng (SBC) nằm trên cạnh SB, đoạn AH ⊥ (SBC) có ký hiệu góc vuông tại H",
        "Tổ hợp từ Plane2D + Pyramid2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const S: Point2D = [56, 14];
        const A: Point2D = [56, 70];
        const B: Point2D = [92, 92];
        const C: Point2D = [142, 68];
        const H: Point2D = [S[0] + (B[0] - S[0]) * 0.62, S[1] + (B[1] - S[1]) * 0.62];
        const sbcSheet: readonly Point2D[] = [S, B, C];
        const show = options.mode === "verified";
        const base = options.labels?.base ?? [];
        return (
          <>
            <Plane2D
              points={sbcSheet}
              label={options.labels?.plane}
              labelAt={[132, 34]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Geo2DPolygon points={[A, B, C]} fill={GEO2D_TOKENS.shellFill} />
            <Geo2DPolygon points={[S, B, C]} fill="rgba(109, 40, 217, 0.14)" />
            <Segment2D from={A} to={C} role="hidden" />
            <Segment2D from={S} to={A} role="altitude-hidden" />
            <Segment2D from={A} to={B} role="solid" />
            <Segment2D from={B} to={C} role="solid" />
            <Segment2D from={S} to={B} role="solid" />
            <Segment2D from={S} to={C} role="solid" />
            <Segment2D from={A} to={H} role="altitude" />
            <Segment2D from={H} to={C} role="section-hidden" />
            <PerpendicularMarker2D at={A} alongA={S} alongB={B} size={5.8} />
            <PerpendicularMarker2D at={B} alongA={A} alongB={C} size={5.8} />
            <PerpendicularMarker2D at={H} alongA={A} alongB={S} size={6.0} />
            <Geo2DPoint at={S} label={options.labels?.apex} dx={0} dy={-8} showLabel={show && Boolean(options.labels?.apex)} />
            <Geo2DPoint at={A} label={base[0]} dx={-9} dy={2} showLabel={show && Boolean(base[0])} />
            <Geo2DPoint at={B} label={base[1]} dx={-4} dy={9} showLabel={show && Boolean(base[1])} />
            <Geo2DPoint at={C} label={base[2]} dx={9} dy={3} showLabel={show && Boolean(base[2])} />
            <Geo2DPoint at={H} label={options.labels?.foot} dx={10} dy={-4} variant="derived" showLabel={show && Boolean(options.labels?.foot)} />
          </>
        );
      },
    },

    "pyramid.dihedral-angle": {
      id: "pyramid.dihedral-angle",
      family: "pyramid",
      titleVi: "Góc nhị diện giữa hai mặt phẳng (SBC) và (ABC)",
      invariants: [
        "Giao tuyến Δ = BC được đánh dấu nổi bật; điểm H trên BC với AH ⊥ BC trong (ABC) và SH ⊥ BC trong (SBC)",
        "Mặt phẳng phẳng nhị diện (SAH) vuông góc với giao tuyến BC tại H, tạo góc phẳng nhị diện SHA",
        "Tổ hợp từ Plane2D + Section2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const S: Point2D = [54, 14];
        const A: Point2D = [54, 72];
        const B: Point2D = [92, 94];
        const C: Point2D = [140, 62];
        const H: Point2D = [(B[0] + C[0]) * 0.5, (B[1] + C[1]) * 0.5];
        const show = options.mode === "verified";
        const base = options.labels?.base ?? [];
        return (
          <>
            <Geo2DPolygon points={[A, B, C]} fill={GEO2D_TOKENS.baseFill} />
            <Geo2DPolygon points={[S, B, C]} fill={GEO2D_TOKENS.shellFill} />
            <Section2D kind="polygon" points={[S, A, H]} hiddenEdges={[true, true, false]} />
            <Segment2D from={A} to={C} role="hidden" />
            <Segment2D from={S} to={A} role="altitude-hidden" />
            <Segment2D from={A} to={B} role="solid" />
            <Segment2D from={S} to={B} role="solid" />
            <Segment2D from={S} to={C} role="solid" />
            <Segment2D from={B} to={C} role="target" />
            <Segment2D from={A} to={H} role="altitude-hidden" />
            <Segment2D from={S} to={H} role="section" />
            <PerpendicularMarker2D at={A} alongA={S} alongB={H} size={5.8} />
            <PerpendicularMarker2D at={H} alongA={A} alongB={B} size={5.8} />
            <PerpendicularMarker2D at={H} alongA={S} alongB={C} size={5.8} />
            <Geo2DPoint at={S} label={options.labels?.apex} dx={0} dy={-8} showLabel={show && Boolean(options.labels?.apex)} />
            <Geo2DPoint at={A} label={base[0]} dx={-9} dy={2} showLabel={show && Boolean(base[0])} />
            <Geo2DPoint at={B} label={base[1]} dx={-4} dy={9} showLabel={show && Boolean(base[1])} />
            <Geo2DPoint at={C} label={base[2]} dx={9} dy={2} showLabel={show && Boolean(base[2])} />
            <Geo2DPoint at={H} label={options.labels?.foot} dx={10} dy={5} variant="derived" showLabel={show && Boolean(options.labels?.foot)} />
          </>
        );
      },
    },

    "pyramid.skew-lines-distance": {
      id: "pyramid.skew-lines-distance",
      family: "pyramid",
      titleVi: "Đoạn vuông góc chung của hai đường thẳng chéo nhau",
      invariants: [
        "Hai đường thẳng chéo nhau SC và BD được tô nổi bật trong hình chóp S.ABCD",
        "Đoạn vuông góc chung PQ nối P ∈ SC và Q ∈ BD kèm ký hiệu góc vuông tại cả hai chân P và Q",
        "Tổ hợp từ Pyramid2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const { S, A, B, C, D } = PYRAMID_FRAME;
        const Q: Point2D = [(B[0] + D[0]) * 0.5, (B[1] + D[1]) * 0.5];
        const P: Point2D = [S[0] + (C[0] - S[0]) * (2 / 3), S[1] + (C[1] - S[1]) * (2 / 3)];
        const show = options.mode === "verified";
        return (
          <>
            <Pyramid2D rightAngleAtA />
            <Segment2D from={A} to={C} role="hidden" />
            <Segment2D from={B} to={D} role="target" />
            <Segment2D from={S} to={C} role="target" />
            <Segment2D from={P} to={Q} role="altitude" />
            <PerpendicularMarker2D at={P} alongA={Q} alongB={S} size={5.8} />
            <PerpendicularMarker2D at={Q} alongA={P} alongB={B} size={5.8} />
            {renderPyramidBaseAndApexPoints(options)}
            <Geo2DPoint
              at={P}
              label={options.labels?.foot}
              dx={10}
              dy={-4}
              variant="derived"
              showLabel={show && Boolean(options.labels?.foot)}
            />
            <Geo2DPoint
              at={Q}
              label={options.labels?.center}
              dx={-8}
              dy={8}
              variant="altitude"
              showLabel={show && Boolean(options.labels?.center)}
            />
          </>
        );
      },
    },

    "oxyz.line-plane-intersection": {
      id: "oxyz.line-plane-intersection",
      family: "pyramid",
      titleVi: "Giao điểm của đường thẳng và mặt phẳng trong không gian Oxyz",
      invariants: [
        "Hệ trục Oxyz và mặt phẳng chắn trục (P) qua A, B, C",
        "Đường thẳng d = DE cắt mặt phẳng (P) tại giao điểm duy nhất M; hình chiếu vuông góc H của E lên (P) thỏa EH ⊥ HM",
        "Tổ hợp từ Plane2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const O: Point2D = [56, 72];
        const A: Point2D = [32, 92];
        const B: Point2D = [136, 84];
        const C: Point2D = [56, 16];
        const D: Point2D = [44, 86];
        const E: Point2D = [126, 22];
        const M: Point2D = [D[0] + (E[0] - D[0]) * 0.48, D[1] + (E[1] - D[1]) * 0.48];
        const H: Point2D = [104, 56];
        const show = options.mode === "verified";
        const base = options.labels?.base ?? [];
        return (
          <>
            <Plane2D
              points={[C, A, B]}
              label={options.labels?.plane}
              labelAt={[142, 48]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Segment2D from={O} to={A} role="hidden" />
            <Segment2D from={O} to={B} role="hidden" />
            <Segment2D from={O} to={C} role="hidden" />
            <Segment2D from={A} to={B} role="solid" />
            <Segment2D from={B} to={C} role="solid" />
            <Segment2D from={C} to={A} role="solid" />
            <Segment2D from={D} to={M} role="section-hidden" />
            <Segment2D from={M} to={E} role="target" />
            <Segment2D from={E} to={H} role="altitude-hidden" />
            <Segment2D from={H} to={M} role="section" />
            <PerpendicularMarker2D at={H} alongA={E} alongB={M} size={5.8} />
            <Geo2DPoint at={O} label={options.labels?.center} dx={-8} dy={-4} showLabel={show && Boolean(options.labels?.center)} />
            <Geo2DPoint at={A} label={base[0]} dx={-9} dy={4} showLabel={show && Boolean(base[0])} />
            <Geo2DPoint at={B} label={base[1]} dx={9} dy={4} showLabel={show && Boolean(base[1])} />
            <Geo2DPoint at={C} label={base[2]} dx={0} dy={-8} showLabel={show && Boolean(base[2])} />
            <Geo2DPoint at={M} label={options.labels?.foot} dx={-9} dy={-6} variant="derived" showLabel={show && Boolean(options.labels?.foot)} />
            <Geo2DPoint at={H} label={options.labels?.rimPoint} dx={10} dy={4} variant="altitude" showLabel={show && Boolean(options.labels?.rimPoint)} />
          </>
        );
      },
    },

    "sphere.tangent-plane": {
      id: "sphere.tangent-plane",
      family: "sphere",
      titleVi: "Mặt phẳng tiếp diện tiếp xúc với mặt cầu tại tiếp điểm A",
      invariants: [
        "Mặt cầu (S) tâm I(86, 62) bán kính R = 34; tiếp điểm A(86, 28) nằm trên mặt cầu",
        "Mặt phẳng tiếp diện (P) đi qua A và vuông góc với bán kính IA tại duy nhất tiếp điểm A (IA ⊥ AB, IA ⊥ AC, không sinh đường tròn giao tuyến)",
        "Tổ hợp từ Plane2D + Sphere2D + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const I: Point2D = [86, 64];
        const A: Point2D = [86, 30];
        const B: Point2D = [126, 30];
        const C: Point2D = [64, 18];
        const planeSheet: readonly Point2D[] = [
          [34, 38],
          [144, 38],
          [158, 18],
          [48, 18],
        ];
        const show = options.mode === "verified";
        return (
          <>
            <Sphere2D center={I} radius={34} equatorRy={9.5} equatorMode="front-solid" />
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[154, 44]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Segment2D from={I} to={A} role="altitude" />
            <Segment2D from={A} to={B} role="section" />
            <Segment2D from={A} to={C} role="section-hidden" />
            <Segment2D from={I} to={B} role="hidden" />
            <PerpendicularMarker2D at={A} alongA={I} alongB={B} size={5.8} />
            <Geo2DPoint at={I} label={options.labels?.center} dx={-9} dy={5} showLabel={show && Boolean(options.labels?.center)} />
            <Geo2DPoint at={A} label={options.labels?.rimPoint} dx={-9} dy={-7} variant="derived" showLabel={show && Boolean(options.labels?.rimPoint)} />
            <Geo2DPoint at={B} label={options.labels?.secondRimPoint} dx={9} dy={-5} variant="derived" showLabel={show && Boolean(options.labels?.secondRimPoint)} />
          </>
        );
      },
    },

    "cone.parallel-section": {
      id: "cone.parallel-section",
      family: "cone",
      titleVi: "Hình nón cắt bởi mặt phẳng song song với đáy",
      invariants: [
        "Hình nón đỉnh S(90, 14), tâm đáy O(90, 88), bán kính đáy OA = 40",
        "Mặt phẳng (P) qua trung điểm I(90, 51) của trục SO song song với đáy, cắt hình nón theo đường tròn thiết diện (C) tâm I bán kính r' = IM = 20 = 1/2 R",
        "Tổ hợp từ Plane2D + Cone2D + Section2D(ellipse) + Segment2D + PerpendicularMarker2D",
      ],
      render: (options) => {
        const S: Point2D = [90, 14];
        const O: Point2D = [90, 88];
        const I: Point2D = [90, 51];
        const rxBase = 40;
        const ryBase = 10.5;
        const rxSec = 20;
        const rySec = 5.5;
        const A: Point2D = [O[0] + rxBase, O[1]];
        const M: Point2D = [I[0] + rxSec, I[1]];
        const planeSheet: readonly Point2D[] = [
          [38, 59],
          [144, 59],
          [156, 43],
          [50, 43],
        ];
        const show = options.mode === "verified";
        return (
          <>
            <Plane2D
              points={planeSheet}
              label={options.labels?.plane}
              labelAt={[28, 51]}
              showLabel={show && Boolean(options.labels?.plane)}
            />
            <Cone2D apex={S} baseCenter={O} rx={rxBase} ry={ryBase} showAxis />
            <Section2D kind="ellipse" center={I} rx={rxSec} ry={rySec} />
            <Segment2D from={O} to={A} role="section-hidden" />
            <Segment2D from={I} to={M} role="section" />
            <PerpendicularMarker2D at={I} alongA={S} alongB={M} size={5.4} />
            <PerpendicularMarker2D at={O} alongA={S} alongB={A} size={5.6} />
            <Geo2DPoint at={S} label={options.labels?.apex} dx={0} dy={-7} showLabel={show && Boolean(options.labels?.apex)} />
            <Geo2DPoint at={O} label={options.labels?.center} dx={-8} dy={6} showLabel={show && Boolean(options.labels?.center)} />
            <Geo2DPoint at={I} label={options.labels?.foot} dx={-8} dy={-5} variant="derived" showLabel={show && Boolean(options.labels?.foot)} />
            <Geo2DPoint at={M} label={options.labels?.rimPoint} dx={9} dy={-5} variant="derived" showLabel={show && Boolean(options.labels?.rimPoint)} />
            <Geo2DPoint at={A} label={options.labels?.secondRimPoint} dx={9} dy={2} showLabel={show && Boolean(options.labels?.secondRimPoint)} />
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
