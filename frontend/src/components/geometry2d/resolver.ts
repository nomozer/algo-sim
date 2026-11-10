import { GEOMETRY_SAMPLES } from "../../data/geometry-samples";
import {
  geometryShapeLabel,
  publicCatalog,
  resolveGeometrySampleId,
} from "../../data/offline-catalog";
import {
  geometryStepCount,
  anchorOfGeometryStep,
  objectsAt,
  toVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "../../simulations/domains/geometry/scene3d-model";
import { kyHieu, veTrenKhung } from "../../simulations/domains/geometry/scene3d-presentation";
import {
  buildPedagogicalConstructionPlan,
  ungroundedFreePointIdsAt,
} from "../../simulations/domains/geometry/scene3d-semantic-policy";
import {
  isSubEntity,
  laDiemPhuDungMatPhang,
  withSubEntities,
} from "../../simulations/domains/geometry/scene3d-subentities";
import {
  normalizeGeometryFamily,
  type GeometryFamilyId,
} from "./family-icons";
import {
  GEOMETRY_TEMPLATES,
  type GeometryTemplateId,
  type VerifiedTemplateLabels,
} from "./templates";

export type GeometryIllustrationMode =
  | "verified"
  | "generic"
  | "family-icon"
  | "fallback-neutral";

export type ShapeKind =
  | "pyramid"
  | "prism"
  | "sphere"
  | "cylinder"
  | "cone";

export type GeometryRelation =
  | "none"
  | "plane_section"
  | "inscribed"
  | "circumscribed"
  | "perpendicular_line_plane"
  | "point_to_plane_distance"
  | "dihedral_angle"
  | "skew_lines_distance"
  | "line_plane_intersection"
  | "tangent_plane"
  | "altitude_to_base"
  | "axial_section"
  | (string & {});

export type IllustrationEmphasis =
  | "section"
  | "volume"
  | "altitude"
  | "radius"
  | "slant_height"
  | "perpendicular"
  | "composite";

export interface IllustrationSpec {
  primaryShape: ShapeKind;
  secondaryShapes?: ShapeKind[];
  relation?: GeometryRelation;
  emphasis?: IllustrationEmphasis;
  variant?: string;
}

export interface GeometryIllustrationInput {
  sampleId?: string | null;
  category?: string | null;
  scene3d?: Scene3D | null;
  templateId?: GeometryTemplateId | null;
  spec?: IllustrationSpec | null;
  /**
   * Cho phép buộc chế độ `"generic"` (không hiển thị nhãn điểm/mặt phẳng cụ thể)
   * ngay cả khi có `sampleId` hoặc `templateId`.
   */
  forceGeneric?: boolean;
}

export interface ResolvedGeometryIllustration {
  mode: GeometryIllustrationMode;
  family: GeometryFamilyId;
  templateId: GeometryTemplateId | null;
  spec?: IllustrationSpec | null;
  fallback: boolean;
  canonicalSampleId: string | null;
  labels?: VerifiedTemplateLabels;
  reason: string;
}

/**
 * Bảng ánh xạ tường minh & kiểm chứng được của 11 bài toán công khai trong Thư viện
 * (cùng 11 fixture hồi quy cũ) sang Họ hình học (Tier A) + Template dạng bài (Tier B).
 */
export const SAMPLE_ILLUSTRATION_MAPPING: Readonly<
  Record<
    string,
    {
      family: Exclude<GeometryFamilyId, "neutral">;
      templateId: GeometryTemplateId;
      categoryVi: string;
    }
  >
> = Object.freeze({
  // 11 bài toán hình học THPT nâng cao công khai
  "chop-thiet-dien-ba-diem": {
    family: "pyramid",
    templateId: "pyramid.section",
    categoryVi: "Hình chóp",
  },
  "lap-phuong-thiet-dien-bat-ky": {
    family: "pyramid",
    templateId: "cube.plane-section",
    categoryVi: "Hình lăng trụ",
  },
  "khoang-cach-diem-mat-phang-nghieng": {
    family: "pyramid",
    templateId: "pyramid.point-to-plane-distance",
    categoryVi: "Hình chóp",
  },
  "goc-nhi-dien-hai-mat-phang": {
    family: "pyramid",
    templateId: "pyramid.dihedral-angle",
    categoryVi: "Hình chóp",
  },
  "khoang-cach-hai-duong-cheo-nhau": {
    family: "pyramid",
    templateId: "pyramid.skew-lines-distance",
    categoryVi: "Hình chóp",
  },
  "lang-tru-tam-giac-thiet-dien": {
    family: "pyramid",
    templateId: "prism.plane-section",
    categoryVi: "Hình lăng trụ",
  },
  "mat-cau-cat-mat-phang": {
    family: "sphere",
    templateId: "sphere.plane-section",
    categoryVi: "Mặt cầu",
  },
  "oxyz-giao-diem-duong-mat": {
    family: "pyramid",
    templateId: "oxyz.line-plane-intersection",
    categoryVi: "Tọa độ Oxyz",
  },
  "mat-phang-tiep-xuc-mat-cau": {
    family: "sphere",
    templateId: "sphere.tangent-plane",
    categoryVi: "Mặt cầu",
  },
  "hinh-non-cat-song-song-day": {
    family: "cone",
    templateId: "cone.parallel-section",
    categoryVi: "Hình nón",
  },
  "chop-mat-cau-ngoai-tiep": {
    family: "pyramid",
    templateId: "pyramid.circumscribed-sphere",
    categoryVi: "Hình chóp",
  },
  // 11 fixture hình học cũ bảo toàn cho kiểm thử hồi quy
  "thiet-dien-chop": {
    family: "pyramid",
    templateId: "pyramid.section",
    categoryVi: "Hình chóp",
  },
  "mat-cheo-sac": {
    family: "pyramid",
    templateId: "pyramid.diagonal-section",
    categoryVi: "Hình chóp",
  },
  "vuong-goc-chop": {
    family: "pyramid",
    templateId: "pyramid.perpendicular",
    categoryVi: "Hình chóp",
  },
  "mp-vuong-goc-duong": {
    family: "pyramid",
    templateId: "pyramid.altitude-distance",
    categoryVi: "Hình chóp",
  },
  "the-tich-chop": {
    family: "pyramid",
    templateId: "pyramid.volume-height",
    categoryVi: "Hình chóp",
  },
  "cau-cat-mat-phang": {
    family: "sphere",
    templateId: "sphere.plane-section",
    categoryVi: "Mặt cầu",
  },
  "cau-the-tich": {
    family: "sphere",
    templateId: "sphere.basic-radius",
    categoryVi: "Mặt cầu",
  },
  "tru-thiet-dien-tron": {
    family: "cylinder",
    templateId: "cylinder.perpendicular-section",
    categoryVi: "Hình trụ",
  },
  "tru-truc-xien": {
    family: "cylinder",
    templateId: "cylinder.oblique-axis",
    categoryVi: "Hình trụ",
  },
  "non-thiet-dien-truc": {
    family: "cone",
    templateId: "cone.axial-section",
    categoryVi: "Hình nón",
  },
  "non-duong-sinh": {
    family: "cone",
    templateId: "cone.slant-generator",
    categoryVi: "Hình nón",
  },
});

function dist3(a: Vec3, b: Vec3): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}

function isRedundantPolyhedronBasePlane(
  plane: SceneObject,
  presentObjects: readonly SceneObject[],
): boolean {
  if (plane.type !== "plane3" || !plane.point || !plane.normal) return false;
  const p0 = toVec3(plane.point);
  const nRaw = toVec3(plane.normal);
  const nLen = Math.hypot(...nRaw);
  if (nLen <= 1e-9) return false;
  const nx = nRaw[0] / nLen;
  const ny = nRaw[1] / nLen;
  const nz = nRaw[2] / nLen;

  const basePolys = presentObjects.filter(
    (o) =>
      !isSubEntity(o.id) &&
      o.type === "polygon3" &&
      (o.surface_role === "BASE_REGION" || o.id.startsWith("day_")) &&
      (o.polygon ?? o.vertices ?? []).length >= 3,
  );
  for (const bp of basePolys) {
    const verts = (bp.polygon ?? bp.vertices ?? []).map(toVec3);
    const allCoplanar = verts.every(
      (v) =>
        Math.abs((v[0] - p0[0]) * nx + (v[1] - p0[1]) * ny + (v[2] - p0[2]) * nz) <= 1e-4,
    );
    if (allCoplanar) return true;
  }
  return false;
}

const _presentObjectsCache = new WeakMap<Scene3D, SceneObject[]>();

function presentSceneObjects(rawScene: Scene3D): SceneObject[] {
  const cached = _presentObjectsCache.get(rawScene);
  if (cached) return cached;
  try {
    const normalized: Scene3D = {
      ...rawScene,
      free_objects: Array.isArray(rawScene.free_objects) ? rawScene.free_objects : [],
      events: Array.isArray(rawScene.events) ? rawScene.events : [],
    };
    const pedPlan = buildPedagogicalConstructionPlan(withSubEntities(normalized));
    const expanded = pedPlan.scene;
    const lastStep = pedPlan.steps[pedPlan.steps.length - 1];
    const stepCount = geometryStepCount(expanded);
    const finalAnchor =
      lastStep?.anchor ?? anchorOfGeometryStep(expanded, Math.max(0, stepCount - 1));
    const ungrounded = ungroundedFreePointIdsAt(expanded, finalAnchor);
    const byObjId = new Map(expanded.objects.map((o) => [o.id, o]));
    const result = objectsAt(expanded, finalAnchor).filter(
      (o) =>
        !isSubEntity(o.id) &&
        veTrenKhung(o) &&
        !ungrounded.has(o.id) &&
        ((o.display_group ?? []).includes("sphere_plane_aux") ||
          !laDiemPhuDungMatPhang(expanded, o, byObjId)),
    );
    const effective =
      result.length > 0
        ? result
        : (rawScene.objects ?? []).filter((o) => !isSubEntity(o.id));
    _presentObjectsCache.set(rawScene, effective);
    return effective;
  } catch {
    const fallbackResult = (rawScene.objects ?? []).filter((o) => !isSubEntity(o.id));
    _presentObjectsCache.set(rawScene, fallbackResult);
    return fallbackResult;
  }
}

function shapeKindToFamily(kind: ShapeKind | string | undefined): GeometryFamilyId {
  switch (kind) {
    case "pyramid":
    case "prism":
      return "pyramid";
    case "sphere":
      return "sphere";
    case "cylinder":
      return "cylinder";
    case "cone":
      return "cone";
    default:
      return "neutral";
  }
}

/**
 * Xác định Họ hình học (Tier A) từ cấu trúc đối tượng `Scene3D`.
 */
export function detectFamilyFromScene3D(rawScene: Scene3D): GeometryFamilyId {
  const objs = presentSceneObjects(rawScene);
  const hasPolyhedron = objs.some(
    (o) =>
      o.type === "solid" ||
      (o.type === "polygon3" && (o.surface_role === "BASE_REGION" || o.id.startsWith("day_"))),
  );
  const hasBall = objs.some(
    (o) => o.type === "curved_solid" && o.curved_kind === "ball",
  );
  const hasCone = objs.some(
    (o) => o.type === "curved_solid" && o.curved_kind === "cone",
  );
  const hasCylinder = objs.some(
    (o) => o.type === "curved_solid" && o.curved_kind === "cylinder",
  );

  if (hasPolyhedron && hasBall) return "pyramid";
  if (hasCone && hasCylinder) return "cone";

  if (hasBall) return "sphere";
  if (hasCylinder) return "cylinder";
  if (hasCone) return "cone";
  if (hasPolyhedron) return "pyramid";

  const hasPlane = objs.some((o) => o.type === "plane3");
  const hasLine = objs.some((o) => o.type === "line3");
  const hasPolygon = objs.some((o) => o.type === "polygon3");
  if (hasPlane && hasLine && hasPolygon) return "pyramid";

  return "neutral";
}

/**
 * Suy dẫn `IllustrationSpec` có cấu trúc từ `Scene3D` (hỗ trợ cả hình đơn và hình tổ hợp),
 * hoàn toàn không phụ thuộc vào thứ tự bài mẫu hay phỏng đoán từ khóa tiêu đề.
 */
export function deriveIllustrationSpecFromScene3D(
  rawScene: Scene3D,
): IllustrationSpec | null {
  const objs = presentSceneObjects(rawScene);
  const rawObjs = (rawScene.objects ?? []).filter((o) => !isSubEntity(o.id));
  const byId = new Map(objs.map((o) => [o.id, o]));
  const rawById = new Map(rawObjs.map((o) => [o.id, o]));
  const family = detectFamilyFromScene3D(rawScene);

  if (family === "neutral") {
    return null;
  }

  const hasPolyhedron = objs.some(
    (o) =>
      o.type === "solid" ||
      (o.type === "polygon3" && (o.surface_role === "BASE_REGION" || o.id.startsWith("day_"))),
  );
  const hasBall = objs.some(
    (o) => o.type === "curved_solid" && o.curved_kind === "ball",
  );
  const hasCone = objs.some(
    (o) => o.type === "curved_solid" && o.curved_kind === "cone",
  );
  const hasCylinder = objs.some(
    (o) => o.type === "curved_solid" && o.curved_kind === "cylinder",
  );

  // Tổ hợp đa khối: Hình chóp nội tiếp mặt cầu
  if (hasPolyhedron && hasBall) {
    return {
      primaryShape: "pyramid",
      secondaryShapes: ["sphere"],
      relation: "circumscribed",
      emphasis: "composite",
    };
  }

  // Tổ hợp đa khối: Hình nón nội tiếp hình trụ
  if (hasCone && hasCylinder) {
    return {
      primaryShape: "cone",
      secondaryShapes: ["cylinder"],
      relation: "inscribed",
      emphasis: "composite",
    };
  }

  const activePlanes = objs.filter(
    (o) => o.type === "plane3" && !isRedundantPolyhedronBasePlane(o, objs),
  );

  if (family === "pyramid") {
    // 1. Bài toán giao điểm đường thẳng và mặt phẳng trong Oxyz
    if (!hasPolyhedron) {
      return {
        primaryShape: "pyramid",
        relation: "line_plane_intersection",
        emphasis: "perpendicular",
        variant: "oxyz",
      };
    }

    const solid = objs.find((o) => o.type === "solid");
    const basePolys = objs.filter(
      (o) =>
        o.type === "polygon3" &&
        (o.surface_role === "BASE_REGION" || o.id.startsWith("day_")),
    );
    const isPrismOrCube =
      basePolys.length >= 2 ||
      objs.some((o) => (o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")) ||
      (solid?.vertices?.length ?? 0) >= 6;

    const sectionPolys = objs.filter(
      (o) =>
        o.type === "section" ||
        (o.type === "polygon3" &&
          o.surface_role !== "BASE_REGION" &&
          !o.id.startsWith("day_") &&
          !(o.display_group ?? []).includes("face")),
    );

    // 2. Khối lăng trụ đứng hoặc hình lập phương cắt bởi mặt phẳng
    if (isPrismOrCube && sectionPolys.length > 0) {
      const sec = sectionPolys[0]!;
      const isCube =
        (solid?.vertices?.length ?? 0) === 8 ||
        (basePolys[0]?.polygon ?? basePolys[0]?.vertices ?? []).length === 4;
      return {
        primaryShape: "prism",
        relation: "plane_section",
        emphasis: "section",
        variant: isCube ? `cube:${sec.id}` : `prism:${sec.id}`,
      };
    }

    const quadSection = sectionPolys.find(
      (s) => (s.polygon ?? s.vertices ?? []).length >= 4,
    );
    if (quadSection) {
      return {
        primaryShape: "pyramid",
        relation: "plane_section",
        emphasis: "section",
        variant: `parallel:${quadSection.id}`,
      };
    }

    const triSection = sectionPolys.find(
      (s) => (s.polygon ?? s.vertices ?? []).length === 3,
    );
    if (triSection) {
      return {
        primaryShape: "pyramid",
        relation: "plane_section",
        emphasis: "section",
        variant: `diagonal:${triSection.id}`,
      };
    }

    // 3. Khoảng cách giữa hai đường thẳng chéo nhau (có >= 2 điểm dẫn xuất P, Q và phép đo khoảng cách giữa 2 đường thẳng)
    const solidVertSet = new Set(
      (solid?.vertices ?? []).map((v) => toVec3(v).join(",")),
    );
    const derivedPoints = rawObjs.filter(
      (o) =>
        o.type === "point3" &&
        o.xyz &&
        !solidVertSet.has(toVec3(o.xyz).join(",")),
    );
    const hasSkewLinesPerp =
      derivedPoints.length >= 2 &&
      rawObjs.filter((o) => o.type === "line3").length >= 3 &&
      rawObjs.some(
        (o) =>
          o.type === "quantity" &&
          (o.producer ?? "").includes("distance") &&
          (o.depends ?? []).length === 2 &&
          (o.depends ?? []).every((depId) => rawById.get(depId)?.type === "line3"),
      );
    if (hasSkewLinesPerp) {
      return {
        primaryShape: "pyramid",
        relation: "skew_lines_distance",
        emphasis: "perpendicular",
      };
    }

    // 4. Góc nhị diện giữa hai mặt phẳng (có >= 2 mặt phẳng active cùng giao tuyến)
    if (activePlanes.length >= 2) {
      return {
        primaryShape: "pyramid",
        relation: "dihedral_angle",
        emphasis: "perpendicular",
      };
    }

    // 5. Mặt phẳng đi qua điểm và vuông góc với đường thẳng (mp-vuong-goc-duong)
    const planePerpToLine = activePlanes.find((pl) =>
      (pl.depends ?? []).some((depId) => byId.get(depId)?.type === "line3"),
    );
    if (planePerpToLine) {
      return {
        primaryShape: "pyramid",
        relation: "perpendicular_line_plane",
        emphasis: "altitude",
        variant: `plane-perp-line:${planePerpToLine.id}`,
      };
    }

    // 6. Khoảng cách từ chân đường cao A đến mặt phẳng nghiêng (SBC) (có điểm H = project_onto trên mặt phẳng nghiêng)
    const projectedFoot = rawObjs.find(
      (o) =>
        o.type === "point3" &&
        ((o.producer ?? "").includes("project") ||
          (o.depends ?? []).some((depId) => rawById.get(depId)?.type === "plane3")),
    );
    if (projectedFoot && activePlanes.length > 0) {
      return {
        primaryShape: "pyramid",
        relation: "point_to_plane_distance",
        emphasis: "altitude",
        variant: `point-to-plane:${activePlanes[0]!.id}`,
      };
    }

    if (activePlanes.length > 0) {
      return {
        primaryShape: "pyramid",
        relation: "perpendicular_line_plane",
        emphasis: "perpendicular",
        variant: `line-perp-plane:${activePlanes[0].id}`,
      };
    }

    const hasHeightOrBase = objs.some(
      (o) =>
        (o.type === "segment3" &&
          (Boolean(o.perpendicular_witness || o.annotation?.witness) ||
            (o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT"))) ||
        (o.type === "polygon3" && o.surface_role === "BASE_REGION") ||
        o.type === "quantity",
    );
    if (hasHeightOrBase) {
      return {
        primaryShape: "pyramid",
        relation: "altitude_to_base",
        emphasis: "volume",
      };
    }

    return {
      primaryShape: "pyramid",
      relation: "unverified_archetype",
    };
  }

  if (family === "sphere") {
    const hasSectionCircle = objs.some(
      (o) =>
        o.type === "circle3" &&
        o.surface_role !== "BASE_REGION" &&
        !o.id.includes("equator") &&
        (activePlanes.length > 0 || (o.depends ?? []).some((d) => byId.get(d)?.type === "plane3")),
    );
    if (hasSectionCircle) {
      return {
        primaryShape: "sphere",
        relation: "plane_section",
        emphasis: "section",
      };
    }
    if (activePlanes.length > 0) {
      return {
        primaryShape: "sphere",
        relation: "tangent_plane",
        emphasis: "perpendicular",
      };
    }
    return {
      primaryShape: "sphere",
      relation: "none",
      emphasis: "radius",
    };
  }

  if (family === "cylinder") {
    const hasSectionCircle = objs.some(
      (o) => o.type === "circle3" && o.surface_role !== "BASE_REGION",
    );
    if (activePlanes.length > 0 || hasSectionCircle) {
      return {
        primaryShape: "cylinder",
        relation: "plane_section",
        emphasis: "section",
      };
    }
    const cyl = objs.find(
      (o) => o.type === "curved_solid" && o.curved_kind === "cylinder" && o.anchor,
    );
    if (cyl?.anchor && cyl.apex_or_top) {
      const a = toVec3(cyl.anchor);
      const t = toVec3(cyl.apex_or_top);
      const horizontalOffset = Math.hypot(t[0] - a[0], t[1] - a[1]);
      if (horizontalOffset > 1e-4) {
        return {
          primaryShape: "cylinder",
          relation: "none",
          emphasis: "altitude",
          variant: "oblique",
        };
      }
    }
    return {
      primaryShape: "cylinder",
      relation: "none",
      emphasis: "radius",
      variant: "right",
    };
  }

  // family === "cone"
  const hasConeSectionCircle = objs.some(
    (o) =>
      o.type === "circle3" &&
      o.surface_role !== "BASE_REGION" &&
      (activePlanes.length > 0 || (o.depends ?? []).some((d) => byId.get(d)?.type === "plane3")),
  );
  if (hasConeSectionCircle) {
    return {
      primaryShape: "cone",
      relation: "plane_section",
      emphasis: "section",
      variant: "parallel",
    };
  }

  const hasAxialTriangle = objs.some(
    (o) =>
      (o.type === "polygon3" || o.type === "section") &&
      o.surface_role !== "BASE_REGION" &&
      (o.polygon ?? o.vertices ?? []).length === 3,
  );
  if (hasAxialTriangle || activePlanes.length > 0) {
    return {
      primaryShape: "cone",
      relation: "axial_section",
      emphasis: "section",
    };
  }
  return {
    primaryShape: "cone",
    relation: "none",
    emphasis: "slant_height",
  };
}

/**
 * Chọn `GeometryTemplateId` từ `IllustrationSpec` (§4.4).
 */
export function resolveTemplateFromIllustrationSpec(spec: IllustrationSpec): {
  family: GeometryFamilyId;
  templateId: GeometryTemplateId | null;
  fallback: boolean;
  reason: string;
} {
  const family = shapeKindToFamily(spec.primaryShape);
  if (family === "neutral") {
    return {
      family: "neutral",
      templateId: null,
      fallback: true,
      reason: "spec_unknown_primary_shape",
    };
  }

  const secondaries = (spec.secondaryShapes ?? []).filter(Boolean);
  const rel = spec.relation ?? "none";
  const variant = spec.variant ?? "";

  if (secondaries.length > 0) {
    if (
      secondaries.length === 1 &&
      (spec.primaryShape === "pyramid" || spec.primaryShape === "prism") &&
      secondaries[0] === "sphere" &&
      (rel === "circumscribed" || rel === "inscribed" || rel === "none")
    ) {
      return {
        family: "pyramid",
        templateId: "pyramid.circumscribed-sphere",
        fallback: false,
        reason: "spec_composite:pyramid_circumscribed_sphere",
      };
    }

    if (
      secondaries.length === 1 &&
      ((spec.primaryShape === "cone" && secondaries[0] === "cylinder") ||
        (spec.primaryShape === "cylinder" && secondaries[0] === "cone")) &&
      (rel === "inscribed" || rel === "circumscribed" || rel === "none")
    ) {
      return {
        family: "cone",
        templateId: "cone.inscribed-cylinder",
        fallback: false,
        reason: "spec_composite:cone_inscribed_cylinder",
      };
    }

    return {
      family,
      templateId: null,
      fallback: true,
      reason: `spec_unverified_composite_fallback:${family}`,
    };
  }

  if (family === "pyramid") {
    if (spec.primaryShape === "prism" && rel === "plane_section") {
      const isCube = variant.startsWith("cube");
      return {
        family: "pyramid",
        templateId: isCube ? "cube.plane-section" : "prism.plane-section",
        fallback: false,
        reason: isCube ? "scene3d_cube_plane_section" : "scene3d_prism_plane_section",
      };
    }
    if (rel === "circumscribed") {
      return {
        family: "pyramid",
        templateId: "pyramid.circumscribed-sphere",
        fallback: false,
        reason: "spec_pyramid_circumscribed_sphere",
      };
    }
    if (rel === "line_plane_intersection") {
      return {
        family: "pyramid",
        templateId: "oxyz.line-plane-intersection",
        fallback: false,
        reason: "scene3d_oxyz_line_plane_intersection",
      };
    }
    if (rel === "skew_lines_distance") {
      return {
        family: "pyramid",
        templateId: "pyramid.skew-lines-distance",
        fallback: false,
        reason: "scene3d_pyramid_skew_lines_distance",
      };
    }
    if (rel === "dihedral_angle") {
      return {
        family: "pyramid",
        templateId: "pyramid.dihedral-angle",
        fallback: false,
        reason: "scene3d_pyramid_dihedral_angle",
      };
    }
    if (rel === "point_to_plane_distance") {
      return {
        family: "pyramid",
        templateId: "pyramid.point-to-plane-distance",
        fallback: false,
        reason: "scene3d_pyramid_point_to_plane_distance",
      };
    }
    if (rel === "plane_section") {
      const isDiag = variant.startsWith("diagonal");
      const suffix = variant.includes(":") ? `:${variant.split(":")[1]}` : "";
      return {
        family: "pyramid",
        templateId: isDiag ? "pyramid.diagonal-section" : "pyramid.section",
        fallback: false,
        reason: isDiag
          ? `scene3d_diagonal_triangle_section${suffix}`
          : `scene3d_polygon_section${suffix}`,
      };
    }
    if (rel === "perpendicular_line_plane") {
      const isPlanePerpLine =
        variant.startsWith("plane-perp-line") || spec.emphasis === "altitude";
      const suffix = variant.includes(":") ? `:${variant.split(":")[1]}` : "";
      return {
        family: "pyramid",
        templateId: isPlanePerpLine ? "pyramid.altitude-distance" : "pyramid.perpendicular",
        fallback: false,
        reason: isPlanePerpLine
          ? `scene3d_plane_perp_to_line${suffix}`
          : `scene3d_line_perp_to_lateral_plane${suffix}`,
      };
    }
    if (rel === "altitude_to_base" || rel === "none") {
      return {
        family: "pyramid",
        templateId: "pyramid.volume-height",
        fallback: false,
        reason: "scene3d_pyramid_volume_or_altitude",
      };
    }
    return {
      family: "pyramid",
      templateId: null,
      fallback: true,
      reason: "pyramid_without_recognized_problem_archetype",
    };
  }

  if (family === "sphere") {
    if (rel === "plane_section") {
      return {
        family: "sphere",
        templateId: "sphere.plane-section",
        fallback: false,
        reason: "scene3d_sphere_plane_intersection",
      };
    }
    if (rel === "tangent_plane") {
      return {
        family: "sphere",
        templateId: "sphere.tangent-plane",
        fallback: false,
        reason: "scene3d_sphere_tangent_plane",
      };
    }
    if (rel === "none" || rel === "altitude_to_base") {
      return {
        family: "sphere",
        templateId: "sphere.basic-radius",
        fallback: false,
        reason: "scene3d_sphere_radius_and_volume",
      };
    }
    return {
      family: "sphere",
      templateId: null,
      fallback: true,
      reason: "sphere_unverified_relation_fallback",
    };
  }

  if (family === "cylinder") {
    if (rel === "plane_section") {
      return {
        family: "cylinder",
        templateId: "cylinder.perpendicular-section",
        fallback: false,
        reason: "scene3d_cylinder_perpendicular_section",
      };
    }
    if (rel === "inscribed") {
      return {
        family: "cone",
        templateId: "cone.inscribed-cylinder",
        fallback: false,
        reason: "spec_composite:cone_inscribed_cylinder",
      };
    }
    if (rel === "none" || rel === "altitude_to_base") {
      const isOblique = variant === "oblique" || spec.emphasis === "altitude";
      return {
        family: "cylinder",
        templateId: isOblique ? "cylinder.oblique-axis" : "cylinder.right-basic",
        fallback: false,
        reason: isOblique
          ? "scene3d_cylinder_oblique_axis"
          : "scene3d_cylinder_right_basic",
      };
    }
    return {
      family: "cylinder",
      templateId: null,
      fallback: true,
      reason: "cylinder_unverified_relation_fallback",
    };
  }

  // family === "cone"
  if (rel === "inscribed") {
    return {
      family: "cone",
      templateId: "cone.inscribed-cylinder",
      fallback: false,
      reason: "spec_composite:cone_inscribed_cylinder",
    };
  }
  if (rel === "plane_section" && variant === "parallel") {
    return {
      family: "cone",
      templateId: "cone.parallel-section",
      fallback: false,
      reason: "scene3d_cone_parallel_section",
    };
  }
  if (rel === "axial_section" || rel === "plane_section") {
    return {
      family: "cone",
      templateId: "cone.axial-section",
      fallback: false,
      reason: "scene3d_cone_axial_section",
    };
  }
  if (rel === "none" || rel === "altitude_to_base") {
    return {
      family: "cone",
      templateId: "cone.slant-generator",
      fallback: false,
      reason: "scene3d_cone_slant_generator",
    };
  }
  return {
    family: "cone",
    templateId: null,
    fallback: true,
    reason: "cone_unverified_relation_fallback",
  };
}

/**
 * Phân tích cấu trúc `Scene3D` để chọn `GeometryTemplateId` phù hợp mà không phụ thuộc từ khóa.
 */
export function resolveTemplateIdFromScene3D(rawScene: Scene3D): {
  family: GeometryFamilyId;
  templateId: GeometryTemplateId | null;
  spec: IllustrationSpec | null;
  reason: string;
} {
  const spec = deriveIllustrationSpecFromScene3D(rawScene);
  if (!spec) {
    return {
      family: "neutral",
      templateId: null,
      spec: null,
      reason: "no_recognized_solid_in_scene3d",
    };
  }
  const resolved = resolveTemplateFromIllustrationSpec(spec);
  return {
    family: resolved.family,
    templateId: resolved.templateId,
    spec,
    reason: resolved.reason,
  };
}

function pointLabel(o: SceneObject | undefined): string | undefined {
  if (!o) return undefined;
  const sym = (kyHieu(o) ?? o.notation ?? o.label ?? "").trim();
  return sym.length > 0 && sym.length <= 6 ? sym : undefined;
}

function findPointNear3D(
  pointObjs: readonly SceneObject[],
  target: Vec3,
  tol = 1e-3,
): SceneObject | undefined {
  return pointObjs.find((p) => p.xyz && dist3(toVec3(p.xyz), target) <= tol);
}

function findPointOnSegment3D(
  pointObjs: readonly SceneObject[],
  a: Vec3,
  b: Vec3,
  excludeIds: ReadonlySet<string>,
): SceneObject | undefined {
  const len = dist3(a, b);
  if (len <= 1e-6) return undefined;
  let best: SceneObject | undefined;
  let bestErr = Infinity;
  for (const p of pointObjs) {
    if (!p.xyz || excludeIds.has(p.id)) continue;
    const v = toVec3(p.xyz);
    const err = Math.abs(dist3(a, v) + dist3(v, b) - len);
    if (err <= 1e-3 && err < bestErr) {
      bestErr = err;
      best = p;
    }
  }
  return best;
}

/**
 * Trích xuất các nhãn điểm/mặt phẳng đã xác minh trực tiếp từ `Scene3D`.
 * Không bao giờ tự suy đoán nhãn nếu đối tượng không tồn tại trong `Scene3D`.
 */
export function extractVerifiedLabelsFromScene3D(
  rawScene: Scene3D,
  templateId: GeometryTemplateId,
): VerifiedTemplateLabels {
  const objs = presentSceneObjects(rawScene);
  const rawObjs = (rawScene.objects ?? []).filter((o) => !isSubEntity(o.id));
  const pointObjs = objs.filter((o) => o.type === "point3" && o.xyz);
  const rawPointObjs = rawObjs.filter((o) => o.type === "point3" && o.xyz);
  const allPointObjs = pointObjs.length >= rawPointObjs.length ? pointObjs : rawPointObjs;

  const activePlanes = objs.filter(
    (o) => o.type === "plane3" && !isRedundantPolyhedronBasePlane(o, objs),
  );
  const activePlaneLabel = activePlanes
    .map((p) => kyHieu(p))
    .find((lbl): lbl is string => Boolean(lbl && lbl.startsWith("(")));

  const spec = GEOMETRY_TEMPLATES[templateId];

  if (templateId === "oxyz.line-plane-intersection") {
    const originPt = findPointNear3D(allPointObjs, [0, 0, 0]);
    const triPoly = objs.find(
      (o) => o.type === "polygon3" && (o.polygon ?? o.vertices ?? []).length === 3,
    );
    const baseLabels: string[] = [];
    for (const v of (triPoly?.polygon ?? triPoly?.vertices ?? []).map(toVec3)) {
      const lbl = pointLabel(findPointNear3D(allPointObjs, v));
      if (lbl) baseLabels.push(lbl);
    }
    const interPt = allPointObjs.find((p) =>
      (p.producer ?? "").includes("intersect_line_plane"),
    );
    const projPt = allPointObjs.find((p) => (p.producer ?? "").includes("project"));
    return {
      center: pointLabel(originPt),
      base: baseLabels.length > 0 ? baseLabels : undefined,
      foot: pointLabel(interPt),
      rimPoint: pointLabel(projPt),
      plane: activePlaneLabel,
    };
  }

  if (templateId === "cube.plane-section") {
    const solid = objs.find((o) => o.type === "solid" && (o.vertices?.length ?? 0) === 8);
    const baseLabels: string[] = [];
    const sectionLabels: string[] = [];
    if (solid?.vertices) {
      const verts = solid.vertices.map(toVec3);
      const solidIds = new Set<string>();
      for (const v of verts) {
        const pt = findPointNear3D(allPointObjs, v);
        if (pt) solidIds.add(pt.id);
      }
      for (let i = 0; i < 4; i += 1) {
        const lbl = pointLabel(findPointNear3D(allPointObjs, verts[i]!));
        if (lbl) baseLabels.push(lbl);
      }
      const edgePairs: readonly [number, number][] = [
        [0, 3], // AD -> M
        [2, 3], // CD -> N
        [2, 6], // CC' -> E
        [5, 6], // B'C' -> P
        [4, 5], // A'B' -> F
        [0, 4], // AA' -> Q
      ];
      for (const [ia, ib] of edgePairs) {
        const pt = findPointOnSegment3D(allPointObjs, verts[ia]!, verts[ib]!, solidIds);
        const lbl = pointLabel(pt);
        if (lbl) sectionLabels.push(lbl);
      }
    }
    return {
      base: baseLabels.length > 0 ? baseLabels : undefined,
      section: sectionLabels.length > 0 ? sectionLabels : undefined,
      plane: activePlaneLabel,
    };
  }

  if (templateId === "prism.plane-section") {
    const solid = objs.find((o) => o.type === "solid" && (o.vertices?.length ?? 0) === 6);
    const baseLabels: string[] = [];
    const sectionLabels: string[] = [];
    if (solid?.vertices) {
      const verts = solid.vertices.map(toVec3);
      const solidIds = new Set<string>();
      for (const v of verts) {
        const pt = findPointNear3D(allPointObjs, v);
        if (pt) solidIds.add(pt.id);
      }
      for (let i = 0; i < 3; i += 1) {
        const lbl = pointLabel(findPointNear3D(allPointObjs, verts[i]!));
        if (lbl) baseLabels.push(lbl);
      }
      const edgePairs: readonly [number, number][] = [
        [0, 1], // AB -> M
        [1, 2], // BC -> N
        [2, 5], // CC' -> P
        [3, 5], // A'C' -> Q
        [3, 4], // A'B' -> E
      ];
      for (const [ia, ib] of edgePairs) {
        const pt = findPointOnSegment3D(allPointObjs, verts[ia]!, verts[ib]!, solidIds);
        const lbl = pointLabel(pt);
        if (lbl) sectionLabels.push(lbl);
      }
    }
    return {
      base: baseLabels.length > 0 ? baseLabels : undefined,
      section: sectionLabels.length > 0 ? sectionLabels : undefined,
      plane: activePlaneLabel,
    };
  }

  if (spec.family === "pyramid") {
    const solid = objs.find((o) => o.type === "solid" && o.vertices && o.vertices.length >= 4);
    let apexLabel: string | undefined;
    const baseLabels: string[] = [];

    if (solid?.vertices) {
      const verts = solid.vertices.map(toVec3);
      let apexIdx = 0;
      for (let i = 1; i < verts.length; i += 1) {
        if (verts[i][2] > verts[apexIdx][2]) {
          apexIdx = i;
        }
      }
      apexLabel = pointLabel(findPointNear3D(allPointObjs, verts[apexIdx]));
      for (let i = 0; i < verts.length; i += 1) {
        if (i === apexIdx) continue;
        const lbl = pointLabel(findPointNear3D(allPointObjs, verts[i]));
        if (lbl) baseLabels.push(lbl);
      }
    }

    const sectionLabels: string[] = [];
    if (templateId === "pyramid.section") {
      const secObj = objs.find(
        (o) =>
          o.type === "section" ||
          (o.type === "polygon3" &&
            o.surface_role !== "BASE_REGION" &&
            !o.id.startsWith("day_") &&
            (o.polygon ?? o.vertices ?? []).length >= 4),
      );
      const secVerts = (secObj?.polygon ?? secObj?.vertices ?? []).map(toVec3);
      const usedSecLabels = new Set<string>();
      if (solid?.vertices && secVerts.length >= 4) {
        const verts = solid.vertices.map(toVec3);
        let apexIdx = 0;
        for (let i = 1; i < verts.length; i += 1) {
          if (verts[i][2] > verts[apexIdx][2]) apexIdx = i;
        }
        const apex3 = verts[apexIdx];
        const base3 = verts.filter((_, idx) => idx !== apexIdx);
        for (const b3 of base3) {
          let bestSec: Vec3 | undefined;
          let bestErr = Infinity;
          const edgeLen = dist3(apex3, b3) || 1;
          for (const sv of secVerts) {
            const err = Math.abs(dist3(apex3, sv) + dist3(sv, b3) - edgeLen);
            if (err <= 1e-3 && err < bestErr) {
              bestErr = err;
              bestSec = sv;
            }
          }
          const lbl = bestSec ? pointLabel(findPointNear3D(allPointObjs, bestSec)) : undefined;
          if (lbl && !usedSecLabels.has(lbl)) {
            usedSecLabels.add(lbl);
            sectionLabels.push(lbl);
          }
        }
        for (const sv of secVerts) {
          if (sectionLabels.length >= 4) break;
          const lbl = pointLabel(findPointNear3D(allPointObjs, sv));
          if (lbl && !usedSecLabels.has(lbl)) {
            usedSecLabels.add(lbl);
            sectionLabels.push(lbl);
          }
        }
      } else {
        for (const v of secVerts) {
          const lbl = pointLabel(findPointNear3D(allPointObjs, v));
          if (lbl && !usedSecLabels.has(lbl)) {
            usedSecLabels.add(lbl);
            sectionLabels.push(lbl);
          }
        }
      }
    }

    let footLabel: string | undefined;
    if (
      templateId === "pyramid.altitude-distance" ||
      templateId === "pyramid.point-to-plane-distance" ||
      templateId === "pyramid.dihedral-angle"
    ) {
      const givenSet = new Set([apexLabel, ...baseLabels].filter(Boolean));
      const derivedPt = allPointObjs.find((p) => {
        const lbl = pointLabel(p);
        return Boolean(lbl && !givenSet.has(lbl));
      });
      footLabel = pointLabel(derivedPt);
    }

    let centerLabel: string | undefined;
    if (templateId === "pyramid.skew-lines-distance") {
      const givenSet = new Set([apexLabel, ...baseLabels].filter(Boolean));
      const derivedPts = allPointObjs.filter((p) => {
        const lbl = pointLabel(p);
        return Boolean(lbl && !givenSet.has(lbl));
      });
      const highPt = derivedPts.find((p) => p.xyz && toVec3(p.xyz)[2] > 1e-4) ?? derivedPts[0];
      const lowPt = derivedPts.find((p) => p.id !== highPt?.id) ?? derivedPts[1];
      footLabel = pointLabel(highPt);
      centerLabel = pointLabel(lowPt);
    }

    if (templateId === "pyramid.circumscribed-sphere") {
      const ball = objs.find(
        (o) => o.type === "curved_solid" && o.curved_kind === "ball" && o.anchor,
      );
      const centerPt = ball?.anchor
        ? findPointNear3D(allPointObjs, toVec3(ball.anchor))
        : undefined;
      centerLabel = pointLabel(centerPt);
    }

    return {
      apex: apexLabel,
      base: baseLabels.length > 0 ? baseLabels : undefined,
      section: sectionLabels.length > 0 ? sectionLabels : undefined,
      foot: footLabel,
      center: centerLabel,
      plane: activePlaneLabel,
    };
  }

  if (spec.family === "sphere") {
    const ball = objs.find(
      (o) => o.type === "curved_solid" && o.curved_kind === "ball" && o.anchor,
    );
    const centerPt = ball?.anchor
      ? findPointNear3D(allPointObjs, toVec3(ball.anchor))
      : allPointObjs[0];
    const centerLabel = pointLabel(centerPt);

    if (templateId === "sphere.plane-section") {
      const secCircle = objs.find(
        (o) => o.type === "circle3" && o.surface_role !== "BASE_REGION" && o.center,
      );
      const footPt = secCircle?.center
        ? findPointNear3D(allPointObjs, toVec3(secCircle.center))
        : undefined;
      const footLabel = pointLabel(footPt);
      const secCenter3 = secCircle?.center ? toVec3(secCircle.center) : undefined;
      const rimPt =
        (secCenter3
          ? allPointObjs.find(
              (p) =>
                p.id !== centerPt?.id &&
                p.id !== footPt?.id &&
                p.xyz &&
                Math.abs(toVec3(p.xyz)[2] - secCenter3[2]) <= 1e-3,
            )
          : undefined) ??
        allPointObjs.find((p) => p.id !== centerPt?.id && p.id !== footPt?.id);
      return {
        center: centerLabel,
        foot: footLabel,
        rimPoint: pointLabel(rimPt),
        plane: activePlaneLabel,
      };
    }

    if (templateId === "sphere.tangent-plane") {
      const otherPts = allPointObjs.filter((p) => p.id !== centerPt?.id);
      return {
        center: centerLabel,
        rimPoint: pointLabel(otherPts[0]),
        secondRimPoint: pointLabel(otherPts[1]),
        plane: activePlaneLabel,
      };
    }

    const rimPt = allPointObjs.find((p) => p.id !== centerPt?.id);
    return {
      center: centerLabel,
      rimPoint: pointLabel(rimPt),
    };
  }

  if (spec.family === "cylinder") {
    const cyl = objs.find(
      (o) => o.type === "curved_solid" && o.curved_kind === "cylinder" && o.anchor,
    );
    const bottomPt = cyl?.anchor
      ? findPointNear3D(allPointObjs, toVec3(cyl.anchor))
      : undefined;
    const topPt = cyl?.apex_or_top
      ? findPointNear3D(allPointObjs, toVec3(cyl.apex_or_top))
      : undefined;
    const centerLabel = pointLabel(bottomPt);
    const topCenterLabel = pointLabel(topPt);

    if (templateId === "cylinder.perpendicular-section") {
      const secCircle = objs.find(
        (o) => o.type === "circle3" && o.surface_role !== "BASE_REGION" && o.center,
      );
      const midPt = secCircle?.center
        ? findPointNear3D(allPointObjs, toVec3(secCircle.center))
        : allPointObjs.find((p) => p.id !== bottomPt?.id && p.id !== topPt?.id);
      return {
        center: centerLabel,
        topCenter: topCenterLabel,
        foot: pointLabel(midPt),
        plane: activePlaneLabel,
      };
    }

    const rimPt = allPointObjs.find((p) => p.id !== bottomPt?.id && p.id !== topPt?.id);
    return {
      center: centerLabel,
      topCenter: topCenterLabel,
      rimPoint: pointLabel(rimPt),
    };
  }

  // spec.family === "cone"
  const cone = objs.find(
    (o) => o.type === "curved_solid" && o.curved_kind === "cone" && o.anchor,
  );
  const centerPt = cone?.anchor
    ? findPointNear3D(allPointObjs, toVec3(cone.anchor))
    : undefined;
  const apexPt = cone?.apex_or_top
    ? findPointNear3D(allPointObjs, toVec3(cone.apex_or_top))
    : undefined;

  if (templateId === "cone.parallel-section") {
    const secCircle = objs.find(
      (o) => o.type === "circle3" && o.surface_role !== "BASE_REGION" && o.center,
    );
    const secCenter3 = secCircle?.center ? toVec3(secCircle.center) : undefined;
    const footPt = secCenter3 ? findPointNear3D(allPointObjs, secCenter3) : undefined;
    const baseZ = cone?.anchor ? toVec3(cone.anchor)[2] : 0;
    const secRimPt = secCenter3
      ? allPointObjs.find(
          (p) =>
            p.id !== footPt?.id &&
            p.xyz &&
            Math.abs(toVec3(p.xyz)[2] - secCenter3[2]) <= 1e-3,
        )
      : undefined;
    const baseRimPt = allPointObjs.find(
      (p) =>
        p.id !== centerPt?.id &&
        p.xyz &&
        Math.abs(toVec3(p.xyz)[2] - baseZ) <= 1e-3,
    );
    return {
      apex: pointLabel(apexPt),
      center: pointLabel(centerPt),
      foot: pointLabel(footPt),
      rimPoint: pointLabel(secRimPt),
      secondRimPoint: pointLabel(baseRimPt),
      plane: activePlaneLabel,
    };
  }

  const rimPts = allPointObjs.filter((p) => p.id !== centerPt?.id && p.id !== apexPt?.id);

  return {
    apex: pointLabel(apexPt),
    center: pointLabel(centerPt),
    rimPoint: pointLabel(rimPts[0]),
    secondRimPoint: pointLabel(rimPts[1]),
    plane: activePlaneLabel,
  };
}

/**
 * Bộ phân giải hình minh họa 2D trung tâm của Axo (§6 & §7).
 */
export function resolveGeometryIllustration(
  input: GeometryIllustrationInput,
): ResolvedGeometryIllustration {
  const canonicalId = resolveGeometrySampleId({ id: input.sampleId ?? undefined });
  const catalogSample = canonicalId
    ? GEOMETRY_SAMPLES.find((s) => s.id === canonicalId)
    : undefined;
  const catalogScene = (catalogSample?.envelope as { scene3d?: Scene3D } | undefined)?.scene3d;
  const effectiveScene = input.scene3d ?? catalogScene ?? null;
  const catalogCategory = canonicalId ? geometryShapeLabel(canonicalId) : undefined;

  if (input.spec) {
    const fromSpec = resolveTemplateFromIllustrationSpec(input.spec);
    if (fromSpec.templateId) {
      if (effectiveScene && !input.forceGeneric) {
        return {
          mode: "verified",
          family: fromSpec.family,
          templateId: fromSpec.templateId,
          spec: input.spec,
          fallback: false,
          canonicalSampleId: canonicalId,
          labels: extractVerifiedLabelsFromScene3D(effectiveScene, fromSpec.templateId),
          reason: `spec_verified:${fromSpec.reason}`,
        };
      }
      return {
        mode: "generic",
        family: fromSpec.family,
        templateId: fromSpec.templateId,
        spec: input.spec,
        fallback: false,
        canonicalSampleId: canonicalId,
        labels: undefined,
        reason: `spec_generic:${fromSpec.reason}`,
      };
    }
    if (fromSpec.family !== "neutral") {
      return {
        mode: "family-icon",
        family: fromSpec.family,
        templateId: null,
        spec: input.spec,
        fallback: true,
        canonicalSampleId: canonicalId,
        labels: undefined,
        reason: fromSpec.reason,
      };
    }
    return {
      mode: "fallback-neutral",
      family: "neutral",
      templateId: null,
      spec: input.spec,
      fallback: true,
      canonicalSampleId: null,
      labels: undefined,
      reason: fromSpec.reason,
    };
  }

  if (input.templateId && input.templateId in GEOMETRY_TEMPLATES) {
    const spec = GEOMETRY_TEMPLATES[input.templateId];
    if (effectiveScene && !input.forceGeneric) {
      return {
        mode: "verified",
        family: spec.family,
        templateId: input.templateId,
        fallback: false,
        canonicalSampleId: canonicalId,
        labels: extractVerifiedLabelsFromScene3D(effectiveScene, input.templateId),
        reason: `explicit_template_verified:${input.templateId}`,
      };
    }
    return {
      mode: "generic",
      family: spec.family,
      templateId: input.templateId,
      fallback: false,
      canonicalSampleId: canonicalId,
      labels: undefined,
      reason: `explicit_template_generic:${input.templateId}`,
    };
  }

  if (effectiveScene) {
    const resolved = resolveTemplateIdFromScene3D(effectiveScene);
    if (resolved.templateId) {
      if (input.forceGeneric) {
        return {
          mode: "generic",
          family: resolved.family,
          templateId: resolved.templateId,
          spec: resolved.spec,
          fallback: false,
          canonicalSampleId: canonicalId,
          labels: undefined,
          reason: `scene3d_generic:${resolved.reason}`,
        };
      }
      return {
        mode: "verified",
        family: resolved.family,
        templateId: resolved.templateId,
        spec: resolved.spec,
        fallback: false,
        canonicalSampleId: canonicalId,
        labels: extractVerifiedLabelsFromScene3D(effectiveScene, resolved.templateId),
        reason: resolved.reason,
      };
    }

    const fallbackFamily =
      resolved.family !== "neutral"
        ? resolved.family
        : normalizeGeometryFamily(input.category ?? catalogCategory);

    if (fallbackFamily !== "neutral") {
      return {
        mode: "family-icon",
        family: fallbackFamily,
        templateId: null,
        spec: resolved.spec,
        fallback: true,
        canonicalSampleId: canonicalId,
        labels: undefined,
        reason: `scene3d_family_fallback:${fallbackFamily}`,
      };
    }
  }

  const familyFromCategory = normalizeGeometryFamily(
    input.category ?? catalogCategory,
  );
  if (familyFromCategory !== "neutral") {
    return {
      mode: "family-icon",
      family: familyFromCategory,
      templateId: null,
      fallback: true,
      canonicalSampleId: null,
      labels: undefined,
      reason: `category_family_fallback:${familyFromCategory}`,
    };
  }

  return {
    mode: "fallback-neutral",
    family: "neutral",
    templateId: null,
    fallback: true,
    canonicalSampleId: null,
    labels: undefined,
    reason: "neutral_fallback",
  };
}

/**
 * Kiểm chứng toàn bộ 11 bài trong `publicCatalog()` đều được resolver
 * chọn đúng Họ hình học + Template dạng bài thông qua phân tích `Scene3D`.
 */
export function verifyCatalogIllustrationConsistency(): {
  sampleId: string;
  expectedFamily: GeometryFamilyId;
  actualFamily: GeometryFamilyId;
  expectedTemplateId: GeometryTemplateId;
  actualTemplateId: GeometryTemplateId | null;
  mode: GeometryIllustrationMode;
  matches: boolean;
}[] {
  return publicCatalog().map((sim) => {
    const expected = SAMPLE_ILLUSTRATION_MAPPING[sim.id];
    const resolved = resolveGeometryIllustration({
      sampleId: sim.id,
      category: geometryShapeLabel(sim.id),
    });
    return {
      sampleId: sim.id,
      expectedFamily: expected?.family ?? "neutral",
      actualFamily: resolved.family,
      expectedTemplateId: expected?.templateId ?? "pyramid.section",
      actualTemplateId: resolved.templateId,
      mode: resolved.mode,
      matches:
        Boolean(expected) &&
        resolved.mode === "verified" &&
        !resolved.fallback &&
        resolved.family === expected.family &&
        resolved.templateId === expected.templateId,
    };
  });
}
