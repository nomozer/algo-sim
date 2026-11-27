import { resolveCatalogSampleIllustration } from "./geometry2d/catalog-preview";
import { renderFamilyThumbnailContent } from "./geometry2d/family-icons";
import { Geometry2DFrame } from "./geometry2d/primitives";
import { GEOMETRY_TEMPLATES, type GeometryTemplateId } from "./geometry2d/templates";

/**
 * Thumbnail 2D siêu nhẹ cho thẻ bài mẫu trên Thư viện (`/library`),
 * chỉ đọc metadata đã xác minh từ `sample-catalog-meta.ts`.
 */
export function CatalogSamplePreview({
  sampleId,
  category,
  templateId,
  forceGeneric,
}: {
  sampleId?: string | null;
  category?: string;
  templateId?: GeometryTemplateId | null;
  forceGeneric?: boolean;
}) {
  const resolved = resolveCatalogSampleIllustration({
    sampleId,
    category,
    templateId,
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
