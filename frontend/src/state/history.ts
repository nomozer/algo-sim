import type { SimulationEnvelope, VisualMode } from "../simulations/types";
import { hopLeScene3D } from "../simulations/domains/geometry/scene3d-model";
import { normalizeCylinderEnvelopeTitle } from "../simulations/domains/geometry/scene3d-semantic-policy";
import { hybridViewCua, kiemHybridView, KHOA_HYBRID_VIEW } from "../simulations/domains/geometry/hybrid-preview-adapter";

/**
 * LỊCH SỬ HỌC CỤC BỘ (M9-UX1) — dữ liệu BỀN, tách hẳn khỏi runtime store.
 *
 * Mục đích: học sinh phân tích một đề trên lớp, đóng trình duyệt, về nhà mở
 * lại ĐÚNG mô phỏng đó mà KHÔNG tốn thêm lượt gọi AI. Vì vậy thứ được lưu là
 * `SimulationEnvelope` ĐÃ QUA server-side validation — mở lại = loadEnvelope
 * (module.validateConfig + module.init đều tất định), không đi qua pipeline.
 *
 * CHÍNH SÁCH LƯU:
 * - localStorage (cho phiên khách / bộ đệm cục bộ); đồng bộ `/api/history` khi
 *   đã đăng nhập; node/SSR → shim in-memory.
 * - Schema CÓ VERSION; entry hỏng / version lạ bị bỏ qua êm (không ném).
 * - Tối đa HISTORY_MAX_ITEMS = 30 (≈ nhiều tuần học; mỗi envelope vài KB nên
 *   xa giới hạn ~5MB của localStorage) — evict item xem lâu nhất.
 * - MỖI BẢN GHI MỘT KHOÁ (`algosim.history.v1:<id>`, từ 2026-11-06): hai tab cùng origin thấy localStorage của nhau
 *   TRỄ (mỗi renderer Chromium giữ bản sao, đồng bộ bất đồng bộ), nên đọc-sửa-ghi cả danh sách trong MỘT khoá làm
 *   mất bản ghi của tab kia (đo thật: run axo-hybrid4-final-premerge-hardening, two-tab). Khoá riêng ⇒ hai tab không
 *   bao giờ ghi đè bản ghi của nhau; cùng một bản ghi thì bên ghi sau thắng (cùng một lần học). Khoá cũ một-mảng
 *   (`algosim.history.v1`) được chuyển sang khi đọc rồi xoá.
 * - CHỈ lưu trường whitelist. KHÔNG BAO GIỜ lưu: key/secret, blob/tệp gốc,
 *   prediction tạm, nhánh what-if, camera/WebGL, hội thoại AI.
 * - Tiến độ TRÌNH BÀY an toàn được phép: lastCursor (timeline là tất định nên
 *   goToStep khôi phục đúng), visualMode.
 */

/**
 * v2 (M17-RC1 §C1): envelope lưu TRƯỚC khi có cổng semantic-completeness có
 * thể là mô phỏng TRẢ LỜI NỬA VỜI — vd đề hỏi cả bốn cách duyệt cây nhưng
 * envelope chỉ dựng một, hoặc đề hỏi cả max lẫn min mà chỉ có max. Mở lại
 * những entry đó là tái hiện đúng lỗi vừa đóng, dù bản thân đường mở lại là
 * zero-AI và tất định (bất biến #17 không đổi).
 *
 * Vì vậy bump version = BỎ entry cũ, có chủ đích. Đánh đổi: học sinh mất lịch
 * sử cục bộ đã lưu; đổi lại không có mô phỏng thiếu sót nào sống sót qua bản
 * vá. Lịch sử là tiện ích cục bộ, không phải sổ gốc — chấp nhận được.
 */
export const HISTORY_SCHEMA_VERSION = 2;
export const HISTORY_MAX_ITEMS = 30;
/** Khoá cũ: cả danh sách trong một mảng JSON — chỉ còn để chuyển sang khoá từng bản ghi. */
const LEGACY_KEY = "algosim.history.v1";
/** Khoá của MỘT bản ghi: tiền tố + `id`. */
export const HISTORY_ITEM_KEY_PREFIX = "algosim.history.v1:";

/** Tập con của Web Storage mà lịch sử cần (liệt kê khoá để đọc các bản ghi). */
export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
  key(index: number): string | null;
  readonly length: number;
}

export interface HistoryItem {
  id: string;
  schemaVersion: typeof HISTORY_SCHEMA_VERSION;
  title: string;
  simulationId: string;
  domain: string;
  /** Envelope ĐÃ VALIDATE — đủ để mở lại zero-AI qua loadEnvelope. */
  envelope: SimulationEnvelope;
  /** Đề gốc học sinh nhập (nếu có) — chỉ text đã chuẩn hoá, không tệp gốc. */
  originalInput: string | null;
  createdAt: number;
  updatedAt: number;
  lastViewedAt: number;
  /** Tiến độ trình bày an toàn (null = chưa ghi). */
  lastCursor: number | null;
  visualMode: VisualMode | null;
}

/** Đồng hồ đơn điệu tăng — tránh hoà lastViewedAt khi ghi liên tiếp trong 1ms. */
let lastTick = 0;
function now(): number {
  const t = Date.now();
  lastTick = t > lastTick ? t : lastTick + 1;
  return lastTick;
}

/** Hash tất định (djb2) — id lịch sử = simulation_id + config đã validate. */
/**
 * ĐỊNH DANH CHƯƠNG TRÌNH BIÊN DỊCH (compiled geometry identity): `simulation_id + config`. Dùng để nhận ra bài
 * mẫu và làm khoá cho lần mở KHÔNG kèm đề (bài mẫu, route). Không phải định danh lần gửi: hai đề khác nhau có
 * thể biên dịch ra cùng chương trình.
 */
export function historyIdOf(env: SimulationEnvelope): string {
  const s = `${env.simulation_id}|${JSON.stringify(env.config)}`;
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  return `h${(h >>> 0).toString(36)}`;
}

/** cyrb53 — băm 53 bit tất định, đồng bộ (đủ cho ≤ 30 bản ghi mỗi người; không dùng cho bảo mật). */
function cyrb53(s: string): string {
  let h1 = 0xdeadbeef;
  let h2 = 0x41c6ce57;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 2654435761);
    h2 = Math.imul(h2 ^ c, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
}

/** Đề đã chuẩn hoá (NFC, gộp khoảng trắng) hoặc `null` khi rỗng. */
export function normalizeStatement(text: string | null | undefined): string | null {
  const t = (text ?? "").normalize("NFC").replace(/\s+/gu, " ").trim();
  return t || null;
}

/**
 * ĐỊNH DANH SCENE3D của một kết quả đã chấp nhận (băm nội dung `scene3d`, `null` khi không có). Bỏ qua khoá bắt đầu
 * bằng `_`: đó là cờ chạy-thời-gian của trình xem (vd `_auxiliaryShown`) mà bản trước 2026-11-05 ghi thẳng vào đối
 * tượng cảnh và có thể đã bị lưu kèm bản ghi; chúng không phải nội dung hình học.
 */
export function sceneDigestOf(env: SimulationEnvelope): string {
  return cyrb53(JSON.stringify((env as { scene3d?: unknown }).scene3d ?? null, (k, v) => (k.startsWith("_") ? undefined : v)));
}

/**
 * ĐỊNH DANH LẦN GỬI (submission/attempt identity): chương trình biên dịch + đề đã chuẩn hoá + Scene3D. Cùng đề,
 * cùng kết quả ⇒ cùng một lần học; khác đề HOẶC khác cảnh ⇒ bản ghi riêng, không ghi đè lần gửi trước.
 * Khoá `s…` là chuỗi mờ ≤ 80 ký tự như `history_key` phía máy chủ yêu cầu; không đổi khoá của bản ghi cũ.
 */
/**
 * ĐỊNH DANH LẦN GỬI (attempt identity): tạo MỘT lần khi học sinh bấm gửi, không suy từ nội dung, tiêu đề hay chương
 * trình biên dịch. Thử lại do lỗi mạng nằm trong cùng lời gọi `analyzeViaServer` nên dùng chung ID này; bấm gửi lần
 * nữa là lần học mới. `getRandomValues` (có cả ngoài secure context, khác `randomUUID`), 128 bit, 33 ký tự ≤ 80
 * (`history_key` máy chủ).
 */
export function newAttemptId(): string {
  const b = new Uint8Array(16);
  globalThis.crypto.getRandomValues(b);
  return `a${Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("")}`;
}

export function submissionIdOf(env: SimulationEnvelope, statement: string): string {
  return `s${cyrb53(`${historyIdOf(env)}|${statement}|${sceneDigestOf(env)}`)}`;
}

/** Chỉ giữ đúng các trường của hợp đồng envelope — lọc mọi thứ thừa/rò rỉ. */
function sanitizeEnvelope(env: SimulationEnvelope): SimulationEnvelope {
  const raw = env as SimulationEnvelope & { scene3d?: unknown };
  const safeScene = hopLeScene3D(raw.scene3d) ? raw.scene3d : null;
  const safeTitle = normalizeCylinderEnvelopeTitle(env.title, safeScene);
  const base: SimulationEnvelope & { scene3d?: unknown } = {
    status: "ok",
    simulation_id: env.simulation_id,
    domain: env.domain,
    visual_mode: env.visual_mode,
    title: safeTitle,
    description: env.description ?? null,
    config: env.config,
    notes: env.notes ?? null,
  };
  // Đề người học đóng dấu trên envelope (main 928fb880) đi theo bản ghi; không thuộc khoá định danh nào.
  if (typeof env.problem_statement === "string" && env.problem_statement.trim()) {
    base.problem_statement = env.problem_statement;
  }
  if (raw.scene3d !== undefined && raw.scene3d !== null) {
    base.scene3d = raw.scene3d;
  }
  // Source evidence belongs to this scene and attempt; losing it changes goal classification after reopening.
  const hybrid = hybridViewCua(env);
  if (hybrid && safeScene && kiemHybridView(hybrid, safeScene) === null) {
    Object.assign(base, { [KHOA_HYBRID_VIEW]: hybrid });
  }
  return base;
}

function isValidItem(x: unknown): x is HistoryItem {
  if (typeof x !== "object" || x === null) return false;
  const r = x as Record<string, unknown>;
  return (
    r.schemaVersion === HISTORY_SCHEMA_VERSION &&
    typeof r.id === "string" &&
    typeof r.title === "string" &&
    typeof r.simulationId === "string" &&
    typeof r.envelope === "object" &&
    r.envelope !== null &&
    typeof (r.envelope as Record<string, unknown>).simulation_id === "string"
  );
}

export interface HistoryStore {
  list(): HistoryItem[];
  /**
   * `recordId`: định danh LẦN HỌC đã biết — ID lần gửi (`newAttemptId`, tạo khi học sinh bấm gửi) hoặc ID của bản ghi
   * đang mở lại. Có `recordId` ⇒ bản ghi được khoá đúng theo nó (thử lại / mở lại không nhân bản, hai lần gửi độc lập
   * không gộp). Không có ⇒ khoá theo nội dung như cũ (bài mẫu, bài giao, bản ghi cũ).
   */
  record(env: SimulationEnvelope, originalInput: string | null, recordId?: string): HistoryItem;
  touch(id: string, patch: { lastCursor?: number; visualMode?: VisualMode }): void;
  remove(id: string): void;
  clear(): void;
  replaceAll?(items: HistoryItem[]): void;
}

export function createHistoryStore(storage: StorageLike | null): HistoryStore {
  /** khoá → (chuỗi đã đọc, bản ghi đã kiểm) — chỉ parse lại khoá có chuỗi đổi. */
  const cache = new Map<string, { raw: string; item: HistoryItem | null }>();

  function parseItem(raw: string): HistoryItem | null {
    try {
      const it: unknown = JSON.parse(raw);
      if (!isValidItem(it)) return null;
      const rawScene = (it.envelope as SimulationEnvelope & { scene3d?: unknown }).scene3d;
      const safeScene = hopLeScene3D(rawScene) ? rawScene : null;
      const normTitle = normalizeCylinderEnvelopeTitle(it.title, safeScene);
      const normEnvTitle = normalizeCylinderEnvelopeTitle(it.envelope.title, safeScene);
      return normTitle !== it.title || normEnvTitle !== it.envelope.title
        ? { ...it, title: normTitle, envelope: { ...it.envelope, title: normEnvTitle } }
        : it;
    } catch {
      return null; // JSON rác → bỏ qua êm
    }
  }

  function itemKeys(s: StorageLike): string[] {
    const out: string[] = [];
    for (let i = 0; i < s.length; i++) {
      const k = s.key(i);
      if (k !== null && k.startsWith(HISTORY_ITEM_KEY_PREFIX)) out.push(k);
    }
    return out;
  }

  /** Khoá một-mảng cũ → khoá từng bản ghi (không ghi đè bản ghi đã có), rồi xoá khoá cũ. Lặp lại vô hại. */
  function migrateLegacy(s: StorageLike): void {
    const raw = s.getItem(LEGACY_KEY);
    if (raw === null) return;
    try {
      const arr: unknown = JSON.parse(raw);
      if (Array.isArray(arr)) {
        for (const it of arr) {
          if (isValidItem(it) && s.getItem(HISTORY_ITEM_KEY_PREFIX + it.id) === null) {
            s.setItem(HISTORY_ITEM_KEY_PREFIX + it.id, JSON.stringify(it));
          }
        }
      }
    } catch {
      /* khoá cũ hỏng: không có gì để chuyển */
    }
    s.removeItem(LEGACY_KEY);
  }

  function read(): HistoryItem[] {
    if (!storage) return [];
    try {
      migrateLegacy(storage);
      const items: HistoryItem[] = [];
      const seen = new Set<string>();
      for (const k of itemKeys(storage)) {
        const raw = storage.getItem(k);
        if (raw === null) continue;
        seen.add(k);
        let c = cache.get(k);
        if (!c || c.raw !== raw) {
          c = { raw, item: parseItem(raw) };
          cache.set(k, c);
        }
        if (c.item) items.push({ ...c.item });
      }
      for (const k of [...cache.keys()]) if (!seen.has(k)) cache.delete(k);
      return items;
    } catch {
      return [];
    }
  }

  function readOne(id: string): HistoryItem | null {
    if (!storage) return null;
    try {
      const raw = storage.getItem(HISTORY_ITEM_KEY_PREFIX + id);
      const item = raw === null ? null : parseItem(raw);
      return item ? { ...item } : null;
    } catch {
      return null;
    }
  }

  function put(item: HistoryItem): void {
    if (!storage) return;
    try {
      storage.setItem(HISTORY_ITEM_KEY_PREFIX + item.id, JSON.stringify(item));
    } catch {
      /* storage đầy/bị chặn → lịch sử là tiện ích, không được phá app */
    }
  }

  function drop(id: string): void {
    if (!storage) return;
    try {
      storage.removeItem(HISTORY_ITEM_KEY_PREFIX + id);
    } catch {
      /* như trên */
    }
  }

  return {
    list() {
      return read().sort((a, b) => b.lastViewedAt - a.lastViewedAt);
    },

    record(env, originalInput, recordId) {
      const input = normalizeStatement(originalInput);
      const cleanEnv = sanitizeEnvelope(env);
      const id = recordId ?? (input ? submissionIdOf(cleanEnv, input) : historyIdOf(env));
      const items = read();
      const t = now();
      const existing =
        items.find((x) => x.id === id) ??
        // Bản ghi cũ (khoá `historyIdOf`) của CHÍNH lần gửi này — cùng chương trình, cùng đề, cùng cảnh — được
        // dùng lại nguyên ID, không nhân bản và không đổi khoá (snapshot `history:<id>`, máy chủ giữ nguyên).
        // Chỉ khi KHÔNG có `recordId`: một lần gửi mới có ID riêng, không bao giờ nhập vào bản ghi cũ trùng nội dung.
        (input && !recordId
          ? items.find((x) =>
              x.id === historyIdOf(env)
              && normalizeStatement(x.originalInput) === input
              && sceneDigestOf(x.envelope) === sceneDigestOf(cleanEnv))
          : undefined);
      if (existing) {
        existing.lastViewedAt = t;
        existing.updatedAt = t;
        // Mở không kèm đề (bài mẫu, route) mà trúng một bản ghi LẦN GỬI cũ (cùng khoá biên dịch): chỉ đánh dấu đã
        // xem, không ghi đè envelope hay đề của lần gửi đó.
        if (input || existing.originalInput === null) {
          existing.title = cleanEnv.title;
          existing.envelope = cleanEnv;
        }
        put(existing);
        return existing;
      }
      const item: HistoryItem = {
        id,
        schemaVersion: HISTORY_SCHEMA_VERSION,
        title: cleanEnv.title,
        simulationId: env.simulation_id,
        domain: env.domain,
        envelope: cleanEnv,
        originalInput: input,
        createdAt: t,
        updatedAt: t,
        lastViewedAt: t,
        lastCursor: null,
        visualMode: null,
      };
      put(item);
      items.push(item);
      // Hạn mức: evict item XEM lâu nhất cho tới khi vừa.
      while (items.length > HISTORY_MAX_ITEMS) {
        let oldest = 0;
        for (let i = 1; i < items.length; i++) {
          if (items[i].lastViewedAt < items[oldest].lastViewedAt) oldest = i;
        }
        drop(items[oldest].id);
        items.splice(oldest, 1);
      }
      return item;
    },

    touch(id, patch) {
      const item = readOne(id);
      if (!item) return;
      if (patch.lastCursor !== undefined) item.lastCursor = patch.lastCursor;
      if (patch.visualMode !== undefined) item.visualMode = patch.visualMode;
      const t = now();
      item.lastViewedAt = t;
      item.updatedAt = t;
      put(item);
    },

    remove(id) {
      drop(id);
    },

    clear() {
      if (!storage) return;
      try {
        for (const k of itemKeys(storage)) storage.removeItem(k);
        storage.removeItem(LEGACY_KEY);
      } catch {
        /* như trên */
      }
      cache.clear();
    },

    replaceAll(items) {
      const keep = items.slice(0, HISTORY_MAX_ITEMS);
      const ids = new Set(keep.map((x) => x.id));
      for (const it of keep) put(it);
      for (const old of read()) if (!ids.has(old.id)) drop(old.id);
    },
  };
}

/* ── singleton mặc định cho app ──────────────────────────────────────────── */

function defaultStorage(): StorageLike | null {
  try {
    const ls = (globalThis as { localStorage?: StorageLike }).localStorage;
    if (!ls) return memoryStorage();
    // Safari private mode: tồn tại nhưng ném khi ghi — thử một lần.
    ls.setItem("algosim.history.probe", "1");
    ls.removeItem("algosim.history.probe");
    return ls;
  } catch {
    return memoryStorage();
  }
}

/** Web Storage trong bộ nhớ (node/SSR, Safari private mode, test). */
export function memoryStorage(): StorageLike & { raw: Map<string, string> } {
  const raw = new Map<string, string>();
  return {
    raw,
    getItem: (k) => raw.get(k) ?? null,
    setItem: (k, v) => void raw.set(k, v),
    removeItem: (k) => void raw.delete(k),
    key: (i) => [...raw.keys()][i] ?? null,
    get length() {
      return raw.size;
    },
  };
}

export const historyStore: HistoryStore = createHistoryStore(defaultStorage());

/** Chỉ dùng trong test — dọn lịch sử của singleton giữa các test case. */
export function __resetHistoryForTest(): void {
  historyStore.clear();
}

/* ── ĐỒNG BỘ LỊCH SỬ VỚI BACKEND KHI ĐÃ ĐĂNG NHẬP (`/api/history`) ───────── */

interface ServerHistoryDto {
  id: string;
  sampleId?: string | null;
  title: string;
  simulationId: string;
  domain: string;
  envelope: SimulationEnvelope;
  originalInput?: string | null;
  lastCursor?: number | null;
  stepCount?: number | null;
  visualMode?: VisualMode | null;
  createdAt?: string;
  updatedAt?: string;
  lastViewedAt?: string;
}

function parseServerTimestamp(iso?: string): number {
  if (!iso) return now();
  const parsed = Date.parse(iso);
  return Number.isFinite(parsed) ? parsed : now();
}

export function fromServerHistoryDto(dto: ServerHistoryDto): HistoryItem | null {
  if (!dto || typeof dto.id !== "string" || !dto.envelope || typeof dto.envelope !== "object") {
    return null;
  }
  return {
    id: dto.id,
    schemaVersion: HISTORY_SCHEMA_VERSION,
    title: dto.title || dto.envelope.title || "Mô phỏng hình học",
    simulationId: dto.simulationId || dto.envelope.simulation_id || "generic.semantic_program",
    domain: dto.domain || dto.envelope.domain || "geometry",
    envelope: sanitizeEnvelope(dto.envelope),
    originalInput: dto.originalInput ?? null,
    createdAt: parseServerTimestamp(dto.createdAt),
    updatedAt: parseServerTimestamp(dto.updatedAt),
    lastViewedAt: parseServerTimestamp(dto.lastViewedAt),
    lastCursor: typeof dto.lastCursor === "number" ? dto.lastCursor : null,
    visualMode: dto.visualMode === "3d" || dto.visualMode === "2d" ? dto.visualMode : null,
  };
}

export async function fetchServerHistory(): Promise<HistoryItem[] | null> {
  try {
    const r = await fetch("/api/history", { credentials: "include" });
    if (!r.ok) return null;
    const body = (await r.json()) as { items?: ServerHistoryDto[] };
    if (!Array.isArray(body.items)) return [];
    return body.items
      .map(fromServerHistoryDto)
      .filter((x): x is HistoryItem => x !== null);
  } catch {
    return null;
  }
}

export async function upsertServerHistory(
  item: HistoryItem,
  opts?: { sampleId?: string | null; stepCount?: number },
): Promise<void> {
  try {
    await fetch("/api/history", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: item.id,
        sampleId: opts?.sampleId ?? null,
        title: item.title,
        simulationId: item.simulationId,
        domain: item.domain,
        envelope: item.envelope,
        originalInput: item.originalInput,
        lastCursor: item.lastCursor ?? 0,
        stepCount: opts?.stepCount ?? 0,
        visualMode: item.visualMode ?? "3d",
      }),
    });
  } catch {
    /* mạng lỗi → giữ bản cục bộ */
  }
}

export async function touchServerHistory(
  id: string,
  patch: { lastCursor?: number; stepCount?: number; visualMode?: VisualMode },
): Promise<void> {
  try {
    await fetch(`/api/history/${encodeURIComponent(id)}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
  } catch {
    /* mạng lỗi → giữ bản cục bộ */
  }
}

export async function deleteServerHistoryItem(id: string): Promise<boolean> {
  try {
    const r = await fetch(`/api/history/${encodeURIComponent(id)}`, {
      method: "DELETE",
      credentials: "include",
    });
    return r.ok || r.status === 404;
  } catch {
    /* mạng lỗi → báo thất bại để UI giữ nguyên mục */
    return false;
  }
}

export async function clearServerHistory(): Promise<void> {
  try {
    await fetch("/api/history", {
      method: "DELETE",
      credentials: "include",
    });
  } catch {
    /* mạng lỗi → giữ bản cục bộ */
  }
}
