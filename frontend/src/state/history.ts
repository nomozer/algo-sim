import type { SimulationEnvelope, VisualMode } from "../simulations/types";

/**
 * LỊCH SỬ HỌC CỤC BỘ (M9-UX1) — dữ liệu BỀN, tách hẳn khỏi runtime store.
 *
 * Mục đích: học sinh phân tích một đề trên lớp, đóng trình duyệt, về nhà mở
 * lại ĐÚNG mô phỏng đó mà KHÔNG tốn thêm lượt gọi AI. Vì vậy thứ được lưu là
 * `SimulationEnvelope` ĐÃ QUA server-side validation — mở lại = loadEnvelope
 * (module.validateConfig + module.init đều tất định), không đi qua pipeline.
 *
 * CHÍNH SÁCH LƯU:
 * - localStorage (không tài khoản/không sync); node/SSR → shim in-memory.
 * - Schema CÓ VERSION; entry hỏng / version lạ bị bỏ qua êm (không ném).
 * - Tối đa HISTORY_MAX_ITEMS = 30 (≈ nhiều tuần học; mỗi envelope vài KB nên
 *   xa giới hạn ~5MB của localStorage) — evict item xem lâu nhất.
 * - CHỈ lưu trường whitelist. KHÔNG BAO GIỜ lưu: key/secret, blob/tệp gốc,
 *   prediction tạm, nhánh what-if, camera/WebGL, hội thoại AI.
 * - Tiến độ TRÌNH BÀY an toàn được phép: lastCursor (timeline là tất định nên
 *   goToStep khôi phục đúng), visualMode.
 */

export const HISTORY_SCHEMA_VERSION = 1;
export const HISTORY_MAX_ITEMS = 30;
const KEY = "algosim.history.v1";

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
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
export function historyIdOf(env: SimulationEnvelope): string {
  const s = `${env.simulation_id}|${JSON.stringify(env.config)}`;
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  return `h${(h >>> 0).toString(36)}`;
}

/** Chỉ giữ đúng các trường của hợp đồng envelope — lọc mọi thứ thừa/rò rỉ. */
function sanitizeEnvelope(env: SimulationEnvelope): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: env.simulation_id,
    domain: env.domain,
    visual_mode: env.visual_mode,
    title: env.title,
    description: env.description ?? null,
    config: env.config,
    notes: env.notes ?? null,
  };
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
  record(env: SimulationEnvelope, originalInput: string | null): HistoryItem;
  touch(id: string, patch: { lastCursor?: number; visualMode?: VisualMode }): void;
  remove(id: string): void;
  clear(): void;
}

export function createHistoryStore(storage: StorageLike | null): HistoryStore {
  function read(): HistoryItem[] {
    if (!storage) return [];
    try {
      const raw = storage.getItem(KEY);
      if (!raw) return [];
      const parsed: unknown = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.filter(isValidItem);
    } catch {
      return []; // JSON rác → coi như chưa có lịch sử, không ném
    }
  }

  function write(items: HistoryItem[]): void {
    if (!storage) return;
    try {
      storage.setItem(KEY, JSON.stringify(items));
    } catch {
      /* storage đầy/bị chặn → lịch sử là tiện ích, không được phá app */
    }
  }

  return {
    list() {
      return read().sort((a, b) => b.lastViewedAt - a.lastViewedAt);
    },

    record(env, originalInput) {
      const id = historyIdOf(env);
      const items = read();
      const t = now();
      const existing = items.find((x) => x.id === id);
      if (existing) {
        existing.lastViewedAt = t;
        existing.updatedAt = t;
        if (existing.originalInput === null && originalInput) {
          existing.originalInput = originalInput;
        }
        write(items);
        return existing;
      }
      const item: HistoryItem = {
        id,
        schemaVersion: HISTORY_SCHEMA_VERSION,
        title: env.title,
        simulationId: env.simulation_id,
        domain: env.domain,
        envelope: sanitizeEnvelope(env),
        originalInput: originalInput ?? null,
        createdAt: t,
        updatedAt: t,
        lastViewedAt: t,
        lastCursor: null,
        visualMode: null,
      };
      items.push(item);
      // Hạn mức: evict item XEM lâu nhất cho tới khi vừa.
      while (items.length > HISTORY_MAX_ITEMS) {
        let oldest = 0;
        for (let i = 1; i < items.length; i++) {
          if (items[i].lastViewedAt < items[oldest].lastViewedAt) oldest = i;
        }
        items.splice(oldest, 1);
      }
      write(items);
      return item;
    },

    touch(id, patch) {
      const items = read();
      const item = items.find((x) => x.id === id);
      if (!item) return;
      if (patch.lastCursor !== undefined) item.lastCursor = patch.lastCursor;
      if (patch.visualMode !== undefined) item.visualMode = patch.visualMode;
      const t = now();
      item.lastViewedAt = t;
      item.updatedAt = t;
      write(items);
    },

    remove(id) {
      write(read().filter((x) => x.id !== id));
    },

    clear() {
      if (!storage) return;
      try {
        storage.removeItem(KEY);
      } catch {
        /* như trên */
      }
    },
  };
}

/* ── singleton mặc định cho app ──────────────────────────────────────────── */

function defaultStorage(): StorageLike | null {
  try {
    const ls = (globalThis as { localStorage?: StorageLike }).localStorage;
    if (!ls) return inMemory();
    // Safari private mode: tồn tại nhưng ném khi ghi — thử một lần.
    ls.setItem("algosim.history.probe", "1");
    ls.removeItem("algosim.history.probe");
    return ls;
  } catch {
    return inMemory();
  }
}

function inMemory(): StorageLike {
  const m = new Map<string, string>();
  return {
    getItem: (k) => m.get(k) ?? null,
    setItem: (k, v) => void m.set(k, v),
    removeItem: (k) => void m.delete(k),
  };
}

export const historyStore: HistoryStore = createHistoryStore(defaultStorage());

/** Chỉ dùng trong test — dọn lịch sử của singleton giữa các test case. */
export function __resetHistoryForTest(): void {
  historyStore.clear();
}
