/**
 * sample-loader.ts — Nạp payload JSON bài mẫu (`advanced-geometry-samples.json` /
 * `geometry-samples.json`) THEO NHU CẦU bằng dynamic `import()`.
 *
 * Chỉ tải khi người dùng mở một bài mẫu hoặc khôi phục `scene3d` thiếu từ lịch sử.
 * Tuyệt đối không nằm trong dependency graph khởi động của Landing hay App Shell.
 */
import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";
import {
  attachProblemContextToScene,
  normalizeCylinderEnvelopeTitle,
} from "../simulations/domains/geometry/scene3d-metadata";
import type { SimulationEnvelope } from "../simulations/types";
import { shouldPrefetchOnIntent } from "../utils/lazy-with-retry";
import {
  cacheSamplePayloads,
  canonicalSlugForSampleId,
  configHashOf,
  getCachedSampleEntry,
  recoverCachedCatalogScene3D,
  resolveGeometrySampleIdMeta,
  resolveSampleMetaByRouteToken,
  type CachedSampleRecord,
} from "./sample-catalog-meta";

interface RawGeometrySample {
  id: string;
  group: string;
  problemText: string;
  envelope: SimulationEnvelope;
}

interface RawSampleFile {
  khai: string;
  samples: RawGeometrySample[];
}

function hydrateRawSamples(
  samples: readonly RawGeometrySample[],
  visibility: "public" | "internal_fixture",
): Map<string, CachedSampleRecord> {
  const out = new Map<string, CachedSampleRecord>();
  const records: CachedSampleRecord[] = [];
  for (const s of samples) {
    const sc = (s.envelope as unknown as { scene3d?: Scene3D }).scene3d;
    if (sc && typeof sc === "object") {
      attachProblemContextToScene(sc, {
        title: s.envelope.title,
        statement: s.problemText || s.envelope.description,
      });
    }
    const normalizedTitle = normalizeCylinderEnvelopeTitle(s.envelope.title, sc);
    const normalizedEnvelope =
      normalizedTitle !== s.envelope.title
        ? { ...s.envelope, title: normalizedTitle }
        : s.envelope;
    const rec: CachedSampleRecord = {
      id: s.id,
      slug: canonicalSlugForSampleId(s.id),
      title: normalizedTitle,
      group: s.group,
      simId: s.envelope.simulation_id,
      domain: s.envelope.domain,
      visibility,
      problemText: s.problemText,
      envelope: normalizedEnvelope,
    };
    out.set(s.id, rec);
    records.push(rec);
  }
  cacheSamplePayloads(records);
  return out;
}

let _publicPromise: Promise<ReadonlyMap<string, CachedSampleRecord>> | null = null;
let _legacyPromise: Promise<ReadonlyMap<string, CachedSampleRecord>> | null = null;

export function loadPublicSamplePayloads(): Promise<ReadonlyMap<string, CachedSampleRecord>> {
  if (!_publicPromise) {
    _publicPromise = import("./advanced-geometry-samples.json")
      .then((mod) => {
        const raw = (mod.default ?? mod) as unknown as RawSampleFile;
        return hydrateRawSamples(raw.samples, "public");
      })
      .catch((err) => {
        // Cho phép thử lại nếu tải chunk thất bại do mạng chập chờn.
        _publicPromise = null;
        throw err;
      });
  }
  return _publicPromise;
}

export function loadLegacySamplePayloads(): Promise<ReadonlyMap<string, CachedSampleRecord>> {
  if (!_legacyPromise) {
    _legacyPromise = import("./geometry-samples.json")
      .then((mod) => {
        const raw = (mod.default ?? mod) as unknown as RawSampleFile;
        return hydrateRawSamples(raw.samples, "internal_fixture");
      })
      .catch((err) => {
        _legacyPromise = null;
        throw err;
      });
  }
  return _legacyPromise;
}

export async function loadSampleById(
  idOrToken: string | null | undefined,
): Promise<CachedSampleRecord | null> {
  if (!idOrToken) return null;
  const cached = getCachedSampleEntry(idOrToken);
  if (cached) return cached;

  const meta = resolveSampleMetaByRouteToken(idOrToken);
  if (!meta) return null;

  if (meta.visibility === "internal_fixture") {
    const legacy = await loadLegacySamplePayloads();
    return legacy.get(meta.id) ?? null;
  }
  const pub = await loadPublicSamplePayloads();
  return pub.get(meta.id) ?? null;
}

export async function recoverCatalogScene3DAsync(
  env: SimulationEnvelope,
): Promise<SimulationEnvelope> {
  const raw = env as SimulationEnvelope & { scene3d?: unknown };
  if (raw.scene3d !== undefined && raw.scene3d !== null) {
    return env;
  }
  const cached = recoverCachedCatalogScene3D(env);
  if ((cached as { scene3d?: unknown }).scene3d != null) {
    return cached;
  }
  const matchedId = resolveGeometrySampleIdMeta({ envelope: env });
  if (!matchedId) return env;
  const loaded = await loadSampleById(matchedId);
  if (loaded && configHashOf(loaded.envelope) === configHashOf(env)) {
    const sampleScene = (loaded.envelope as SimulationEnvelope & { scene3d?: unknown }).scene3d;
    if (sampleScene !== undefined && sampleScene !== null) {
      return { ...env, scene3d: sampleScene } as SimulationEnvelope;
    }
  }
  return env;
}

/** Prefetch đúng nhóm chunk JSON (public hoặc legacy) và chunk Workspace khi hover/focus card. */
export function preloadSampleGroup(sampleId: string): void {
  if (!shouldPrefetchOnIntent()) return;
  const meta = resolveSampleMetaByRouteToken(sampleId);
  if (!meta) return;
  if (meta.visibility === "internal_fixture") {
    void loadLegacySamplePayloads().catch(() => {});
  } else {
    void loadPublicSamplePayloads().catch(() => {});
  }
  void import("../components/SimulationWorkspace").catch(() => {});
}
