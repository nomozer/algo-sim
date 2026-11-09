export {
  GEO2D_TOKENS,
  Geo2DEdge,
  Geo2DEllipseRim,
  Geo2DPlaneBadge,
  Geo2DPoint,
  Geo2DPolygon,
  Geo2DRightAngle,
  Geometry2DFrame,
  type EdgeVisualRole,
  type Point2D,
} from "./primitives";

export {
  GEOMETRY_FAMILY_ICONS,
  GeometryFamilyIcon,
  normalizeGeometryFamily,
  renderFamilyThumbnailContent,
  type GeometryFamilyIconSpec,
  type GeometryFamilyId,
} from "./family-icons";

export {
  GEOMETRY_TEMPLATES,
  type GeometryTemplateDefinition,
  type GeometryTemplateId,
  type TemplateRenderOptions,
  type VerifiedTemplateLabels,
} from "./templates";

export {
  SAMPLE_ILLUSTRATION_MAPPING,
  detectFamilyFromScene3D,
  extractVerifiedLabelsFromScene3D,
  resolveGeometryIllustration,
  resolveTemplateIdFromScene3D,
  verifyCatalogIllustrationConsistency,
  type GeometryIllustrationInput,
  type GeometryIllustrationMode,
  type ResolvedGeometryIllustration,
} from "./resolver";
