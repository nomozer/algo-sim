/**
 * catalog-preview.ts — Bộ phân giải thumbnail 2D siêu nhẹ dành riêng cho thẻ bài mẫu
 * trên Thư viện (`/library`), đọc từ `sample-catalog-meta.ts` mà KHÔNG kéo
 * `advanced-geometry-samples.json`, `geometry-samples.json` hay `three`.
 */
import { geometryShapeLabel, sampleMetaById } from "../../data/sample-catalog-meta";
import { normalizeGeometryFamily, type GeometryFamilyId } from "./family-icons";
import { GEOMETRY_TEMPLATES, type GeometryTemplateId, type VerifiedTemplateLabels } from "./templates";

export interface CatalogIllustrationResolution {
  mode: "verified" | "generic" | "family-icon" | "fallback-neutral";
  family: GeometryFamilyId;
  templateId: GeometryTemplateId | null;
  fallback: boolean;
  canonicalSampleId: string | null;
  labels?: VerifiedTemplateLabels;
  reason: string;
}

export function resolveCatalogSampleIllustration(input: {
  sampleId?: string | null;
  category?: string | null;
  templateId?: GeometryTemplateId | null;
  forceGeneric?: boolean;
}): CatalogIllustrationResolution {
  const meta = sampleMetaById(input.sampleId ?? undefined);
  const canonicalId = meta?.id ?? null;

  if (input.templateId && input.templateId in GEOMETRY_TEMPLATES) {
    const spec = GEOMETRY_TEMPLATES[input.templateId];
    const hasMetaLabels = meta && meta.illustration.templateId === input.templateId && meta.illustration.labels;
    if (hasMetaLabels && !input.forceGeneric) {
      return {
        mode: "verified",
        family: spec.family,
        templateId: input.templateId,
        fallback: false,
        canonicalSampleId: canonicalId,
        labels: meta.illustration.labels ?? undefined,
        reason: "explicit_template_meta_verified",
      };
    }
    return {
      mode: "generic",
      family: spec.family,
      templateId: input.templateId,
      fallback: false,
      canonicalSampleId: canonicalId,
      reason: "explicit_template_generic",
    };
  }

  if (meta) {
    const ill = meta.illustration;
    if (ill.mode === "verified" && ill.templateId && ill.labels && !input.forceGeneric) {
      return {
        mode: "verified",
        family: ill.family,
        templateId: ill.templateId,
        fallback: ill.fallback,
        canonicalSampleId: meta.id,
        labels: ill.labels,
        reason: "sample_meta_verified",
      };
    }
    if (ill.templateId) {
      return {
        mode: "generic",
        family: ill.family,
        templateId: ill.templateId,
        fallback: false,
        canonicalSampleId: meta.id,
        reason: "sample_meta_generic",
      };
    }
  }

  const label = input.category ?? (canonicalId ? geometryShapeLabel(canonicalId) : null);
  const normalized = normalizeGeometryFamily(label);
  if (normalized !== "neutral") {
    return {
      mode: "family-icon",
      family: normalized,
      templateId: null,
      fallback: true,
      canonicalSampleId: canonicalId,
      reason: "category_family_icon",
    };
  }

  return {
    mode: "fallback-neutral",
    family: "neutral",
    templateId: null,
    fallback: true,
    canonicalSampleId: canonicalId,
    reason: "neutral_fallback",
  };
}
