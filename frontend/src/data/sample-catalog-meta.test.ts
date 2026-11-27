import { describe, expect, it } from "vitest";
import { GEOMETRY_SAMPLES } from "./geometry-samples";
import { offlineCatalog, publicCatalog } from "./offline-catalog";
import {
  ALL_SAMPLE_META,
  canonicalSlugForSampleId,
  configHashOf,
  discoverableCatalogMeta,
  problemTextForSample,
  publicCatalogMeta,
  resolveGeometrySampleIdMeta,
  resolveSampleMetaByRouteToken,
  sampleMetaById,
  starterMetaEntries,
  stepCountOfEnvelopeLite,
} from "./sample-catalog-meta";
import { loadSampleById } from "./sample-loader";
import { stepCountOfEnvelope } from "../components/SessionCard";
import { resolveGeometrySolidFamily } from "../components/family-icons";
import { resolveGeometryIllustration } from "../components/geometry2d/resolver";
import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";

describe("sample-catalog-meta & on-demand sample-loader parity", () => {
  it("preserves all 22 geometry samples, 11 public entries, and 4 starter entries with exact metadata", () => {
    const fullOffline = offlineCatalog();
    const fullPublic = publicCatalog();
    expect(ALL_SAMPLE_META).toHaveLength(fullOffline.length);
    expect(publicCatalogMeta()).toHaveLength(fullPublic.length);
    expect(discoverableCatalogMeta().length).toBe(11);
    expect(starterMetaEntries()).toHaveLength(4);

    for (const fullEntry of fullOffline) {
      const meta = sampleMetaById(fullEntry.id);
      expect(meta, `missing meta for ${fullEntry.id}`).toBeDefined();
      expect(meta!.slug).toBe(fullEntry.slug);
      expect(canonicalSlugForSampleId(fullEntry.id)).toBe(fullEntry.slug);
      expect(resolveSampleMetaByRouteToken(fullEntry.slug)?.id).toBe(fullEntry.id);
      expect(resolveSampleMetaByRouteToken(fullEntry.id)?.id).toBe(fullEntry.id);
      expect(meta!.title).toBe(fullEntry.title);
      expect(meta!.visibility).toBe(fullEntry.visibility);
      expect(meta!.configHash).toBe(configHashOf(fullEntry.envelope));
      expect(resolveGeometrySampleIdMeta({ envelope: fullEntry.envelope })).toBe(fullEntry.id);

      const raw = GEOMETRY_SAMPLES.find((s) => s.id === fullEntry.id)!;
      expect(problemTextForSample(fullEntry.id)).toBe(raw.problemText);
      expect(meta!.stepCount).toBe(stepCountOfEnvelope(fullEntry.envelope));
      expect(stepCountOfEnvelopeLite(fullEntry.envelope)).toBe(meta!.stepCount);
      expect(meta!.solidFamily).toBe(
        resolveGeometrySolidFamily({
          envelope: fullEntry.envelope,
          sampleId: fullEntry.id,
          problemStatement: raw.problemText,
          title: fullEntry.title,
        }),
      );

      const sc = (fullEntry.envelope as unknown as { scene3d?: Scene3D }).scene3d ?? null;
      const expectedIll = resolveGeometryIllustration({
        sampleId: fullEntry.id,
        category: fullEntry.slug,
        scene3d: sc,
      });
      expect(meta!.illustration.templateId).toBe(expectedIll.templateId);
      expect(meta!.illustration.family).toBe(expectedIll.family);
      expect(meta!.illustration.mode).toBe(expectedIll.mode);
    }
  });

  it("loads public and legacy sample payloads on demand via sample-loader", async () => {
    const pub = await loadSampleById("pyramid-circumscribed-sphere");
    expect(pub?.id).toBe("chop-mat-cau-ngoai-tiep");
    expect((pub?.envelope as { scene3d?: unknown })?.scene3d).toBeDefined();

    const leg = await loadSampleById("cau-cat-mat-phang");
    expect(leg?.id).toBe("cau-cat-mat-phang");
    expect((leg?.envelope as { scene3d?: unknown })?.scene3d).toBeDefined();
  });
});
