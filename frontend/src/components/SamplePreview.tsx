import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";
import {
  GEOMETRY_TEMPLATES,
  Geometry2DFrame,
  renderFamilyThumbnailContent,
  resolveGeometryIllustration,
  type GeometryTemplateId,
  type IllustrationSpec,
} from "./geometry2d";

/**
 * Hệ thống hình minh họa 2D sư phạm theo Họ hình học (Tier A) + Dạng bài toán (Tier B).
 * Dùng chung cho Trang chủ (`HomeView`), Thư viện (`LibraryView`) và Lịch sử (`SessionCard`).
 */

export type PreviewKind = "geometry";

export function previewKindOf(_simId: string): PreviewKind {
  return "geometry";
}

export interface SamplePreviewProps {
  kind?: PreviewKind;
  sampleId?: string | null;
  category?: string;
  scene3d?: Scene3D | null;
  templateId?: GeometryTemplateId | null;
  spec?: IllustrationSpec | null;
  forceGeneric?: boolean;
}

export function SamplePreview({
  sampleId,
  category,
  scene3d,
  templateId,
  spec,
  forceGeneric,
}: SamplePreviewProps) {
  const resolved = resolveGeometryIllustration({
    sampleId,
    category,
    scene3d,
    templateId,
    spec,
    forceGeneric,
  });

  const template = resolved.templateId
    ? GEOMETRY_TEMPLATES[resolved.templateId]
    : null;

  const content =
    template && (resolved.mode === "verified" || resolved.mode === "generic")
      ? template.render({
          mode: resolved.mode,
          labels: resolved.mode === "verified" ? resolved.labels : undefined,
        })
      : renderFamilyThumbnailContent(resolved.family);

  const thumbId =
    resolved.canonicalSampleId ??
    resolved.templateId ??
    (resolved.mode === "family-icon"
      ? `family:${resolved.family}`
      : "fallback:neutral");

  return (
    <Geometry2DFrame
      thumbId={thumbId}
      templateId={resolved.templateId ?? `family.${resolved.family}`}
      family={resolved.family}
      mode={resolved.mode}
      fallback={resolved.fallback}
    >
      {content}
    </Geometry2DFrame>
  );
}
