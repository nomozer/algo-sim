import {
  GEOMETRY_SAMPLES,
  LEGACY_GEOMETRY_SAMPLES,
  PUBLIC_GEOMETRY_SAMPLES,
} from "./geometry-samples";
import { cacheSamplePayloads } from "./sample-catalog-meta";
import { normalizeCylinderEnvelopeTitle } from "../simulations/domains/geometry/scene3d-metadata";
import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";
import type { Domain, SimulationEnvelope } from "../simulations/types";

/**
 * Danh mục bài mẫu OFFLINE hợp nhất (M9-UX1) — một nguồn cho cả HomeView
 * (gợi ý khám phá) lẫn InputPanel (drawer trong workspace). Mỗi entry mang
 * sẵn envelope đã chuẩn — click = loadEnvelope, không cần AI.
 *
 * M9-UX2 — LUẬT PHẠM VI: kiến trúc được phép tổng quát, nhưng danh mục CÔNG
 * KHAI khoanh trong phạm vi sản phẩm — nay là bài mẫu hình học không gian
 * (`PUBLIC_GEOMETRY_SAMPLES`). `visibility` là metadata TƯỜNG MINH khai tại
 * định nghĩa mẫu (CẤM lọc theo chuỗi tiêu đề). Gỡ một mẫu khỏi danh mục công
 * khai KHÔNG gỡ năng lực đã nuôi nó — fixture nội bộ vẫn sống cho test/dev,
 * và lịch sử học mở lại bằng envelope nên không phụ thuộc danh mục.
 */

export interface CatalogEntry {
  id: string;
  /** Định danh URL tiếng Anh chữ thường phân tách bằng dấu gạch nối (§8). */
  slug: string;
  title: string;
  simId: string;
  domain: Domain;
  envelope: SimulationEnvelope;
  visibility: "public" | "internal_fixture";
  /** Gợi ý preview tường minh (vd generic không tự nói lên từ simId). */
  preview?: string;
}

export const CANONICAL_SAMPLE_SLUGS: Readonly<Record<string, string>> = Object.freeze({
  // 11 bài toán hình học THPT nâng cao công khai
  "chop-thiet-dien-ba-diem": "pyramid-three-point-section",
  "lap-phuong-thiet-dien-bat-ky": "cube-hexagonal-plane-section",
  "khoang-cach-diem-mat-phang-nghieng": "point-to-inclined-plane-distance",
  "goc-nhi-dien-hai-mat-phang": "dihedral-angle-between-planes",
  "khoang-cach-hai-duong-cheo-nhau": "skew-lines-common-perpendicular",
  "lang-tru-tam-giac-thiet-dien": "triangular-prism-plane-section",
  "mat-cau-cat-mat-phang": "sphere-secant-plane-intersection",
  "oxyz-giao-diem-duong-mat": "oxyz-line-plane-intersection",
  "mat-phang-tiep-xuc-mat-cau": "sphere-tangent-plane-contact",
  "hinh-non-cat-song-song-day": "cone-parallel-base-section",
  "chop-mat-cau-ngoai-tiep": "pyramid-circumscribed-sphere",
  // 11 fixture hình học cũ bảo toàn cho kiểm thử & tương thích ngược
  "thiet-dien-chop": "pyramid-cross-section",
  "mat-cheo-sac": "pyramid-diagonal-section",
  "vuong-goc-chop": "pyramid-line-plane-angle",
  "mp-vuong-goc-duong": "pyramid-perpendicular-plane-distance",
  "the-tich-chop": "pyramid-volume-and-altitude",
  "cau-cat-mat-phang": "sphere-plane-intersection",
  "cau-the-tich": "sphere-radius-and-volume",
  "tru-thiet-dien-tron": "cylinder-perpendicular-section",
  "tru-truc-xien": "tilted-right-cylinder-metrics",
  "non-thiet-dien-truc": "cone-axial-section",
  "non-duong-sinh": "cone-slant-height-and-surface",
});

function toAsciiHyphenSlug(raw: string): string {
  const cleaned = raw
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[đĐ]/g, "d")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return cleaned || "geometry-problem";
}

function buildCanonicalSlugRegistry(): {
  byId: ReadonlyMap<string, string>;
  bySlug: ReadonlyMap<string, string>;
} {
  const byId = new Map<string, string>();
  const bySlug = new Map<string, string>();
  for (const s of GEOMETRY_SAMPLES) {
    const base = CANONICAL_SAMPLE_SLUGS[s.id] ?? toAsciiHyphenSlug(s.id);
    let candidate = base;
    let suffix = 2;
    while (bySlug.has(candidate) && bySlug.get(candidate) !== s.id) {
      candidate = `${base}-${suffix}`;
      suffix += 1;
    }
    byId.set(s.id, candidate);
    bySlug.set(candidate, s.id);
  }
  return { byId, bySlug };
}

const _slugRegistry = buildCanonicalSlugRegistry();

/** Trả về slug tiếng Anh chuẩn cho `sampleId` (hoặc giữ nguyên mã định danh lịch sử `h...`). */
export function canonicalSlugForSampleId(sampleIdOrToken: string): string {
  const trimmed = sampleIdOrToken.trim();
  if (!trimmed) return "";
  const direct = _slugRegistry.byId.get(trimmed);
  if (direct) return direct;
  const fromAlias = _slugRegistry.bySlug.get(trimmed.toLowerCase());
  if (fromAlias) return _slugRegistry.byId.get(fromAlias) ?? trimmed.toLowerCase();
  return trimmed;
}

let _offlineCatalogMemo: CatalogEntry[] | null = null;
let _discoverableCatalogMemo: CatalogEntry[] | null = null;
let _publicCatalogMemo: CatalogEntry[] | null = null;
let _sampleIdByConfigKeyMemo: Map<string, string> | null = null;

function sampleIdByConfigKey(): ReadonlyMap<string, string> {
  if (_sampleIdByConfigKeyMemo) return _sampleIdByConfigKeyMemo;
  const m = new Map<string, string>();
  for (const s of GEOMETRY_SAMPLES) {
    m.set(`${s.envelope.simulation_id}|${JSON.stringify(s.envelope.config)}`, s.id);
  }
  _sampleIdByConfigKeyMemo = m;
  return m;
}

function toCatalogEntry(
  s: (typeof GEOMETRY_SAMPLES)[number],
  visibility: "public" | "internal_fixture",
): CatalogEntry {
  const sc = (s.envelope as unknown as { scene3d?: Scene3D }).scene3d;
  const normalizedTitle = normalizeCylinderEnvelopeTitle(s.envelope.title, sc);
  const normalizedEnvelope =
    normalizedTitle !== s.envelope.title
      ? { ...s.envelope, title: normalizedTitle }
      : s.envelope;
  return {
    id: s.id,
    slug: canonicalSlugForSampleId(s.id),
    title: normalizedTitle,
    simId: s.envelope.simulation_id,
    domain: s.envelope.domain,
    envelope: normalizedEnvelope,
    visibility,
    preview: s.group,
  };
}

/** TOÀN BỘ mẫu (kể cả fixture nội bộ) — cho test/dev/regression. */
export function offlineCatalog(): CatalogEntry[] {
  if (_offlineCatalogMemo) return [..._offlineCatalogMemo];
  const built: CatalogEntry[] = [
    ...PUBLIC_GEOMETRY_SAMPLES.map((s) => toCatalogEntry(s, "public")),
    ...LEGACY_GEOMETRY_SAMPLES.map((s) => toCatalogEntry(s, "internal_fixture")),
  ];
  _offlineCatalogMemo = built;
  const byId = new Map(GEOMETRY_SAMPLES.map((s) => [s.id, s]));
  cacheSamplePayloads(
    built.map((e) => ({
      ...e,
      group: e.preview ?? byId.get(e.id)?.group ?? "",
      problemText: byId.get(e.id)?.problemText ?? "",
    })),
  );
  return [...built];
}

export const PRODUCT_DOMAINS: readonly Domain[] = ["geometry"];

/**
 * Danh mục NGƯỜI DÙNG THẤY: mẫu công khai VÀ thuộc phạm vi sản phẩm.
 */
export function publicCatalog(): CatalogEntry[] {
  if (!_publicCatalogMemo) {
    _publicCatalogMemo = discoverableCatalog().filter((e) => PRODUCT_DOMAINS.includes(e.domain));
  }
  return [..._publicCatalogMemo];
}

/**
 * Phân giải bài mẫu theo `slug` tiếng Anh chuẩn HOẶC `id` tiếng Việt
 * (ưu tiên `publicCatalog()`, fallback sang `offlineCatalog()` để giữ tương thích URL/phiên cũ §8).
 */
export function resolveSampleByRouteToken(token: string | null | undefined): CatalogEntry | undefined {
  if (!token) return undefined;
  const trimmed = token.trim();
  if (!trimmed) return undefined;
  const lower = trimmed.toLowerCase();
  const pub = publicCatalog();
  const matchedPub = pub.find(
    (e) => e.slug === lower || e.id === trimmed || e.id.toLowerCase() === lower,
  );
  if (matchedPub) return matchedPub;
  return offlineCatalog().find(
    (e) => e.slug === lower || e.id === trimmed || e.id.toLowerCase() === lower,
  );
}

/**
 * Mẫu KHÔNG PHẢI fixture nội bộ — bất kể miền.
 */
export function discoverableCatalog(): CatalogEntry[] {
  if (!_discoverableCatalogMemo) {
    _discoverableCatalogMemo = offlineCatalog().filter((e) => e.visibility === "public");
  }
  return [..._discoverableCatalogMemo];
}

/**
 * Gợi ý trên Trang chủ — 4 bài tiêu biểu đại diện cho 4 họ hình trong bộ 11 bài THPT nâng cao.
 */
const STARTER_SAMPLE_IDS = [
  "chop-thiet-dien-ba-diem",
  "mat-cau-cat-mat-phang",
  "lap-phuong-thiet-dien-bat-ky",
  "hinh-non-cat-song-song-day",
];

/** Nhãn phân loại khối hình học hiển thị trên thẻ gợi ý khám phá và Thư viện. */
export function geometryShapeLabel(sampleId: string): string {
  const canonicalId = _slugRegistry.bySlug.get(sampleId.toLowerCase()) ?? sampleId;
  if (canonicalId.startsWith("oxyz-")) {
    return "Tọa độ Oxyz";
  }
  if (
    canonicalId.startsWith("cau-") ||
    canonicalId.startsWith("mat-cau-") ||
    canonicalId === "mat-phang-tiep-xuc-mat-cau"
  ) {
    return "Mặt cầu";
  }
  if (
    canonicalId.startsWith("lap-phuong-") ||
    canonicalId.startsWith("lang-tru-")
  ) {
    return "Hình lăng trụ";
  }
  if (canonicalId.startsWith("tru-")) return "Hình trụ";
  if (
    canonicalId.startsWith("non-") ||
    canonicalId.startsWith("hinh-non-")
  ) {
    return "Hình nón";
  }
  return "Hình chóp";
}

export function starterEntries(): CatalogEntry[] {
  const pub = publicCatalog();
  const out: CatalogEntry[] = [];
  for (const id of STARTER_SAMPLE_IDS) {
    const entry = pub.find((e) => e.id === id);
    if (entry) out.push(entry);
  }
  return out;
}

export const LIBRARY_CATEGORY_ORDER = [
  "all",
  "Hình chóp",
  "Hình lăng trụ",
  "Mặt cầu",
  "Hình trụ",
  "Hình nón",
  "Tọa độ Oxyz",
] as const;

export type LibraryCategory = (typeof LIBRARY_CATEGORY_ORDER)[number];

/** Đề bài đầy đủ của mẫu hình học (hiển thị ở mô tả thẻ Thư viện Axo V2.7). */
export function problemTextForSample(sampleId: string): string {
  const canonicalId = _slugRegistry.bySlug.get(sampleId.toLowerCase()) ?? sampleId;
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === canonicalId);
  return sample?.problemText ?? "";
}

/**
 * Khớp mẫu hình học từ `id`/`slug` hoặc `simulation_id + config` (tất định). KHÔNG khớp theo tiêu đề.
 */
export function resolveGeometrySampleId(
  target:
    | { id?: string | null; title?: string | null; envelope?: SimulationEnvelope | null }
    | null
    | undefined,
): string | null {
  if (!target) return null;
  if (target.id) {
    const byRouteToken = resolveSampleByRouteToken(target.id);
    if (byRouteToken) return byRouteToken.id;
    const byDirectId = GEOMETRY_SAMPLES.find((s) => s.id === target.id);
    if (byDirectId) return byDirectId.id;
  }
  if (target.envelope) {
    const byConfig = sampleIdByConfigKey().get(
      `${target.envelope.simulation_id}|${JSON.stringify(target.envelope.config)}`,
    );
    if (byConfig) return byConfig;
  }
  return null;
}

/**
 * Khôi phục `scene3d` tất định từ `GEOMETRY_SAMPLES` cho các bản ghi lịch sử
 * được lưu trước khi `sanitizeEnvelope` giữ lại `scene3d`, miễn là bản ghi đó
 * khớp chính xác bài mẫu theo `simulation_id` + `config`.
 */
export function recoverCatalogScene3D(env: SimulationEnvelope): SimulationEnvelope {
  const raw = env as SimulationEnvelope & { scene3d?: unknown };
  if (raw.scene3d !== undefined && raw.scene3d !== null) {
    return env;
  }
  const matchedId = sampleIdByConfigKey().get(`${env.simulation_id}|${JSON.stringify(env.config)}`);
  if (matchedId) {
    const byConfig = GEOMETRY_SAMPLES.find((s) => s.id === matchedId);
    if (byConfig) {
      const sampleScene = (byConfig.envelope as SimulationEnvelope & { scene3d?: unknown }).scene3d;
      return { ...env, scene3d: sampleScene } as SimulationEnvelope;
    }
  }
  return env;
}

/** Nhãn loại hình học cho mục lịch sử hoặc mẫu. */
export function geometryCategoryForItem(
  target:
    | { id?: string | null; title?: string | null; envelope?: SimulationEnvelope | null }
    | null
    | undefined,
): Exclude<LibraryCategory, "all"> {
  const sampleId = resolveGeometrySampleId(target);
  if (sampleId) {
    return geometryShapeLabel(sampleId) as Exclude<LibraryCategory, "all">;
  }
  const text = `${target?.title ?? ""} ${target?.envelope?.title ?? ""}`.toLowerCase();
  if (text.includes("mặt cầu") || text.includes("khối cầu")) return "Mặt cầu";
  if (text.includes("lăng trụ") || text.includes("lập phương") || text.includes("hình hộp")) {
    return "Hình lăng trụ";
  }
  if (text.includes("hình trụ") || text.includes("khối trụ")) return "Hình trụ";
  if (text.includes("hình nón") || text.includes("khối nón")) return "Hình nón";
  if (text.includes("oxyz") && !text.includes("hình chóp") && !text.includes("tứ diện")) {
    return "Tọa độ Oxyz";
  }
  return "Hình chóp";
}
