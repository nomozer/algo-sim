import { GEOMETRY_SAMPLES } from "./geometry-samples";
import { normalizeCylinderEnvelopeTitle } from "../simulations/domains/geometry/scene3d-semantic-policy";
import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";
import type { Domain, SimulationEnvelope } from "../simulations/types";

/**
 * Danh mục bài mẫu OFFLINE hợp nhất (M9-UX1) — một nguồn cho cả HomeView
 * (gợi ý khám phá) lẫn InputPanel (drawer trong workspace). Mỗi entry mang
 * sẵn envelope đã chuẩn — click = loadEnvelope, không cần AI.
 *
 * M9-UX2 — LUẬT PHẠM VI: kiến trúc được phép tổng quát, nhưng danh mục CÔNG
 * KHAI khoanh trong phạm vi sản phẩm — nay là bài mẫu hình học không gian
 * (`geometry-samples`). `visibility` là metadata TƯỜNG MINH khai tại
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

export const DOMAIN_COLOR: Record<Domain, string> = {
  algorithm: "var(--accent-green)",
  logic: "var(--accent-purple-deep)",
  binary: "var(--primary)",
  network: "var(--accent-pink)",
  tree: "var(--accent-green)",
  database: "var(--accent-teal)",
  web: "var(--accent-orange)",
  color: "var(--accent-sky)",
  geometry: "var(--secondary)",
  generic: "var(--accent-orange-deep)",
};

export const DOMAIN_LABEL: Record<Domain, string> = {
  algorithm: "Thuật toán",
  logic: "Lôgic",
  binary: "Nhị phân",
  network: "Mạng",
  tree: "Cây",
  database: "CSDL",
  web: "Web",
  color: "Màu sắc",
  geometry: "Hình học",
  generic: "Tổng quát",
};

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

/** TOÀN BỘ mẫu (kể cả fixture nội bộ) — cho test/dev/regression. */
export function offlineCatalog(): CatalogEntry[] {
  if (_offlineCatalogMemo) return [..._offlineCatalogMemo];
  // HÌNH HỌC — envelope SINH RA từ kernel, không viết tay (xem
  // `geometry-samples.ts`). `domain` đọc từ envelope chứ không gán cứng
  // "geometry" ở đây: gán cứng là dựng nguồn sự thật thứ hai, và nó sẽ lệch
  // đúng lúc backend đổi nhãn miền.
  //
  // ⚠️ Hai nguồn cũ (`SAMPLES` — bài mẫu Tin học soạn sẵn; `OFFLINE_SAMPLES`
  // — mẫu viết tay cho dev) đã gỡ cùng chín domain Tin học. Đây nay là nguồn
  // DUY NHẤT của danh mục offline, và nó là nguồn SINH RA chứ không viết tay
  // — tức bài mẫu không thể mang một toạ độ do người gõ vào.
  const built: CatalogEntry[] = [
    ...GEOMETRY_SAMPLES.map(
      (s): CatalogEntry => {
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
          visibility: "public",
          preview: s.group,
        };
      },
    ),
  ];
  _offlineCatalogMemo = built;
  return [...built];
}

/**
 * PHẠM VI SẢN PHẨM — miền nào được BÀY RA cho người dùng.
 *
 * Đề tài đổi 2026-08-24 (`STATUS_LEDGER §0-2026-08-24`): sản phẩm là hệ mô phỏng
 * **hình học không gian 3D**. Trước bản này `publicCatalog()` lọc theo
 * `FOCUS_SIM_IDS` — 13 target Tin học — nên Thư viện và Trang chủ bày ra một
 * danh mục thuật toán/mạng/cây, còn ba bài hình học thì KHÔNG lối nào tới được
 * (chúng mang `simulation_id` là `generic.semantic_program`, không nằm trong
 * danh sách ấy). Tức bề mặt công khai vẫn đang quảng bá đề tài cũ.
 *
 * ⚠️ Đây là hằng số của **BỀ MẶT**, không phải của **NĂNG LỰC**. Mười miền Tin
 * học vẫn đăng ký đầy đủ, vẫn chạy, vẫn mở lại được từ Lịch sử và từ bài giáo
 * viên đã giao, vẫn nguyên trong test/benchmark. Chúng chỉ thôi được BÀY. Xoá
 * chúng là chuyện khác hẳn và phải quyết riêng — de-expose trước, delete sau.
 */
export const PRODUCT_DOMAINS: readonly Domain[] = ["geometry"];

/**
 * W5P — TIÊU ĐIỂM KHOÁ LUẬN (ĐỀ CŨ): 13 target thuộc BA ĐIỂM NGHẼN nhận thức.
 *
 * ⚠️ KHÔNG còn lái bề mặt công khai — `publicCatalog()` nay hỏi `PRODUCT_DOMAINS`.
 * Giữ lại vì nó vẫn là mirror của `FOCUS_SIMULATION_IDS` bên backend và vẫn có
 * nghĩa cho lát đánh giá của đề cũ; đọc nó như **lịch sử khoa học**, không như
 * trạng thái sản phẩm.
 *
 * Mirror của `FOCUS_SIMULATION_IDS` bên `backend/app/simulation/catalog.py`
 * (cùng khuôn hai tầng như mọi hợp đồng khác trong repo).
 *
 * Nó khai TIÊU ĐIỂM, không khai NĂNG LỰC: 11 target ngoài danh sách vẫn đăng ký
 * đầy đủ, vẫn AI tới được, vẫn chạy trong test/regression — chỉ thôi được QUẢNG
 * BÁ ở Thư viện. Nguồn phán quyết: `docs/STATUS_LEDGER.md §0`.
 */
export const FOCUS_SIM_IDS: readonly string[] = [
  "algorithm.find_max",
  "algorithm.find_min",
  "algorithm.sum_if",
  "algorithm.count_if",
  "algorithm.linear_search",
  "algorithm.scan",
  "algorithm.bounded_control_flow",
  "algorithm.binary_search",
  "algorithm.bubble_sort",
  "algorithm.insertion_sort",
  "algorithm.selection_sort",
  "tree.traversal",
  "network.graph_traversal",
];

/**
 * Bài Thư viện bày cho học sinh = mẫu công khai VÀ thuộc tiêu điểm.
 *
 * Hai điều kiện là hai câu hỏi khác nhau, cố ý giữ tách: `visibility` nói "mẫu
 * này có phải fixture nội bộ không", `FOCUS_SIM_IDS` nói "target này có thuộc
 * tiêu điểm khoá luận không". Gộp lại thì đổi phạm vi đề tài sẽ phải đi sửa
 * metadata của từng mẫu.
 */
/**
 * Danh mục NGƯỜI DÙNG THẤY: mẫu công khai VÀ thuộc phạm vi sản phẩm.
 *
 * Hai điều kiện là hai câu hỏi khác nhau, cố ý giữ tách: `visibility` nói "mẫu
 * này có phải fixture nội bộ không", `PRODUCT_DOMAINS` nói "miền này có thuộc
 * sản phẩm hiện tại không". Gộp lại thì mỗi lần đổi phạm vi sẽ phải đi sửa
 * metadata của từng mẫu.
 */
export function publicCatalog(): CatalogEntry[] {
  if (!_publicCatalogMemo) {
    _publicCatalogMemo = discoverableCatalog().filter((e) => PRODUCT_DOMAINS.includes(e.domain));
  }
  return [..._publicCatalogMemo];
}

/** Phân giải bài mẫu công khai theo `slug` tiếng Anh chuẩn HOẶC `id` tiếng Việt cũ (tương thích ngược §8). */
export function resolveSampleByRouteToken(token: string | null | undefined): CatalogEntry | undefined {
  if (!token) return undefined;
  const trimmed = token.trim();
  if (!trimmed) return undefined;
  const lower = trimmed.toLowerCase();
  const pub = publicCatalog();
  return pub.find((e) => e.slug === lower || e.id === trimmed || e.id.toLowerCase() === lower);
}

/**
 * Mẫu KHÔNG PHẢI fixture nội bộ — bất kể miền.
 *
 * ─── VÌ SAO TÁCH KHỎI `publicCatalog()` ──────────────────────────────────
 *
 * Hai câu hỏi khác nhau đã có lúc trùng đáp án nên bị dùng lẫn:
 *
 *   "mẫu này có phải fixture nội bộ không"   → `discoverableCatalog()`
 *   "miền này có thuộc sản phẩm hiện tại không" → `publicCatalog()`
 *
 * Lúc sản phẩm còn là Tin học thì hai tập trùng nhau, nên các cross-lock
 * (`capability-descriptors`, `generation-parity`, `target-certification`,
 * `experience-manifest`) đều hỏi `publicCatalog()` — trong khi thứ chúng thật
 * sự canh là **target có bịa ra một mẫu không có thật hay không**, chuyện của
 * runtime chứ không phải chuyện của bề mặt quảng bá.
 *
 * Thu hẹp bề mặt xuống hình học làm hai tập tách ra, và các guard ấy đỏ vì
 * **hỏi nhầm câu**, không vì hệ hỏng. Nên tách tên chứ không nới ngưỡng: nới
 * ngưỡng là bỏ luôn thứ guard đang canh.
 */
export function discoverableCatalog(): CatalogEntry[] {
  if (!_discoverableCatalogMemo) {
    _discoverableCatalogMemo = offlineCatalog().filter((e) => e.visibility === "public");
  }
  return [..._discoverableCatalogMemo];
}

/**
 * Gợi ý trên Trang chủ — bộ NHỎ chọn lọc, không đổ cả danh mục dài.
 *
 * Chọn theo **id mẫu**, không theo `simId` như bản cũ: mọi bài hình học dùng
 * chung `generic.semantic_program`, nên lọc theo `simId` sẽ hoặc lấy hết hoặc
 * không lấy gì — không phân biệt được bài nào với bài nào.
 */
const STARTER_SAMPLE_IDS = [
  "thiet-dien-chop",
  "cau-cat-mat-phang",
  "tru-thiet-dien-tron",
  "non-thiet-dien-truc",
];

/** Nhãn phân loại khối hình học hiển thị trên thẻ gợi ý khám phá (Axo V2.7 P6). */
export function geometryShapeLabel(sampleId: string): string {
  const canonicalId = _slugRegistry.bySlug.get(sampleId.toLowerCase()) ?? sampleId;
  if (canonicalId.startsWith("cau-")) return "Mặt cầu";
  if (canonicalId.startsWith("tru-")) return "Hình trụ";
  if (canonicalId.startsWith("non-")) return "Hình nón";
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
  "Mặt cầu",
  "Hình trụ",
  "Hình nón",
] as const;

export type LibraryCategory = (typeof LIBRARY_CATEGORY_ORDER)[number];

/** Đề bài đầy đủ của mẫu hình học (hiển thị ở mô tả thẻ Thư viện Axo V2.7). */
export function problemTextForSample(sampleId: string): string {
  const canonicalId = _slugRegistry.bySlug.get(sampleId.toLowerCase()) ?? sampleId;
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === canonicalId);
  return sample?.problemText ?? "";
}

/**
 * Khớp mẫu hình học từ `id`/`slug` hoặc `simulation_id + config` (tất định). KHÔNG khớp theo tiêu đề:
 * hai đề khác nhau có thể trùng tiêu đề, nên tiêu đề không phải bằng chứng là cùng một bài.
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
 * khớp chính xác bài mẫu công khai theo `simulation_id` + `config` (cùng chương trình đã biên dịch).
 * Không khớp theo tiêu đề; bản ghi không khớp được trả nguyên trạng (không có `scene3d`) để
 * xưởng báo thiếu dữ liệu thay vì gán cảnh của một bài mẫu trông giống.
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

/** Nhãn loại hình học (`Hình chóp`, `Mặt cầu`, `Hình trụ`, `Hình nón`) cho mục lịch sử hoặc mẫu. */
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
  if (text.includes("hình trụ") || text.includes("khối trụ")) return "Hình trụ";
  if (text.includes("hình nón") || text.includes("khối nón")) return "Hình nón";
  return "Hình chóp";
}
