/**
 * Snapshot trạng thái học tập tạm thời trong phiên (`sessionStorage`) phục vụ khôi phục có điều kiện (§5.3, §8.7).
 *
 * Bảo toàn:
 * - Bài toán đang mở (`problemKey`) + bảng trạng thái gần nhất theo từng bài (`entries`) để điều hướng
 *   `Back`/`Forward` giữa nhiều bài toán không làm mất hoặc trộn trạng thái giữa các bài.
 * - Bước dựng hiện tại (`stepIndex`) và đối tượng đang chọn (`selectedId`)
 * - Tùy chọn hiển thị (`display`)
 * - Góc camera hợp lệ, hữu hạn, không suy biến (`camera`)
 * - Trạng thái mở/đóng Study Dock (`dockCollapsed`) và chế độ xem trên mobile (`mobileViewMode`)
 *
 * Ràng buộc an toàn:
 * - Kiểm tra `schemaVersion` nghiêm ngặt: khác phiên bản ⇒ bỏ qua an toàn.
 * - Giới hạn thời gian sống (`ttlMs`, mặc định 30 phút), số bài tối đa (`<= 12`) và kích thước (`<= 12 KB`).
 * - KHÔNG lưu API key, thông tin cá nhân hay toàn bộ payload `Scene3D`.
 */

export const LEARNER_RECOVERY_STORAGE_KEY = "axo:learner-recovery:v1";
export const LEARNER_RECOVERY_SCHEMA_VERSION = 1 as const;
const DEFAULT_TTL_MS = 30 * 60 * 1000;
const MAX_SNAPSHOT_CHARS = 12288;
const MAX_STORED_PROBLEMS = 12;

export type MobileViewMode = "dock_open" | "stage_expanded";

export interface LearnerDisplaySnapshot {
  showShell: boolean;
  showVertexLabels: boolean;
  showPlane: boolean;
  showSection: boolean;
  showAxes: boolean;
  showDimensionLabels: boolean;
  showRightAngles: boolean;
  showDashedHidden: boolean;
  auxiliaryShown: boolean;
  gridShown: boolean;
  xray: boolean;
  shellOpacityPct: number;
  planeOpacityPct: number;
}

export interface LearnerCameraSnapshot {
  position: [number, number, number];
  target: [number, number, number];
}

export interface LearnerRecoverySnapshotInput {
  problemKey: string;
  stepIndex: number;
  selectedId: string | null;
  dockCollapsed: boolean;
  mobileViewMode: MobileViewMode;
  display: LearnerDisplaySnapshot;
  camera: LearnerCameraSnapshot | null;
}

export interface LearnerRecoverySnapshot extends LearnerRecoverySnapshotInput {
  schemaVersion: typeof LEARNER_RECOVERY_SCHEMA_VERSION;
  savedAtMs: number;
}

interface StoredRecoveryEnvelope extends LearnerRecoverySnapshot {
  entries?: Record<string, LearnerRecoverySnapshot>;
}

export interface SnapshotStorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export interface SnapshotOptions {
  storage?: SnapshotStorageLike | null;
  nowMs?: number;
  ttlMs?: number;
}

function defaultSessionStorage(): SnapshotStorageLike | null {
  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      return window.sessionStorage;
    }
  } catch {
    /* sessionStorage có thể bị chặn trong iframe sandbox hoặc chế độ riêng tư nghiêm ngặt */
  }
  return null;
}

function isFiniteCoordTuple(v: unknown): v is [number, number, number] {
  return (
    Array.isArray(v)
    && v.length === 3
    && v.every((n) => typeof n === "number" && Number.isFinite(n) && Math.abs(n) <= 1e4)
  );
}

export function sanitizeCameraSnapshot(raw: unknown): LearnerCameraSnapshot | null {
  if (!raw || typeof raw !== "object") return null;
  const cand = raw as { position?: unknown; target?: unknown };
  if (!isFiniteCoordTuple(cand.position) || !isFiniteCoordTuple(cand.target)) {
    return null;
  }
  const dx = cand.position[0] - cand.target[0];
  const dy = cand.position[1] - cand.target[1];
  const dz = cand.position[2] - cand.target[2];
  const dist = Math.hypot(dx, dy, dz);
  if (!Number.isFinite(dist) || dist <= 1e-3 || dist > 500) {
    return null;
  }
  return {
    position: [cand.position[0], cand.position[1], cand.position[2]],
    target: [cand.target[0], cand.target[1], cand.target[2]],
  };
}

function clampPct(v: unknown, fallback: number): number {
  if (typeof v !== "number" || !Number.isFinite(v)) return fallback;
  return Math.max(0, Math.min(100, Math.round(v)));
}

function sanitizeDisplaySnapshot(raw: unknown): LearnerDisplaySnapshot | null {
  if (!raw || typeof raw !== "object") return null;
  const d = raw as Record<string, unknown>;
  const boolKeys = [
    "showShell",
    "showVertexLabels",
    "showPlane",
    "showSection",
    "showAxes",
    "showDimensionLabels",
    "showRightAngles",
    "showDashedHidden",
    "auxiliaryShown",
    "gridShown",
    "xray",
  ] as const;
  for (const k of boolKeys) {
    if (typeof d[k] !== "boolean") return null;
  }
  return {
    showShell: d.showShell as boolean,
    showVertexLabels: d.showVertexLabels as boolean,
    showPlane: d.showPlane as boolean,
    showSection: d.showSection as boolean,
    showAxes: d.showAxes as boolean,
    showDimensionLabels: d.showDimensionLabels as boolean,
    showRightAngles: d.showRightAngles as boolean,
    showDashedHidden: d.showDashedHidden as boolean,
    auxiliaryShown: d.auxiliaryShown as boolean,
    gridShown: d.gridShown as boolean,
    xray: d.xray as boolean,
    shellOpacityPct: clampPct(d.shellOpacityPct, 12),
    planeOpacityPct: clampPct(d.planeOpacityPct, 8),
  };
}

function parseSingleSnapshotEntry(
  raw: unknown,
  nowMs: number,
  ttlMs: number,
): LearnerRecoverySnapshot | null {
  if (!raw || typeof raw !== "object") return null;
  const rec = raw as Record<string, unknown>;
  if (rec.schemaVersion !== LEARNER_RECOVERY_SCHEMA_VERSION) return null;
  if (
    typeof rec.savedAtMs !== "number" ||
    !Number.isFinite(rec.savedAtMs) ||
    nowMs - rec.savedAtMs > ttlMs ||
    rec.savedAtMs > nowMs + 60_000
  ) {
    return null;
  }
  if (typeof rec.problemKey !== "string" || !rec.problemKey.trim()) return null;
  if (typeof rec.stepIndex !== "number" || !Number.isInteger(rec.stepIndex) || rec.stepIndex < 0) {
    return null;
  }
  const display = sanitizeDisplaySnapshot(rec.display);
  if (!display) return null;
  return {
    schemaVersion: LEARNER_RECOVERY_SCHEMA_VERSION,
    savedAtMs: rec.savedAtMs,
    problemKey: rec.problemKey.trim().slice(0, 200),
    stepIndex: rec.stepIndex,
    selectedId: typeof rec.selectedId === "string" && rec.selectedId.trim() ? rec.selectedId : null,
    dockCollapsed: Boolean(rec.dockCollapsed),
    mobileViewMode: rec.mobileViewMode === "stage_expanded" ? "stage_expanded" : "dock_open",
    display,
    camera: sanitizeCameraSnapshot(rec.camera),
  };
}

function readValidStoredEntries(
  store: SnapshotStorageLike,
  nowMs: number,
  ttlMs: number,
): Map<string, LearnerRecoverySnapshot> {
  const out = new Map<string, LearnerRecoverySnapshot>();
  let rawText: string | null = null;
  try {
    rawText = store.getItem(LEARNER_RECOVERY_STORAGE_KEY);
  } catch {
    return out;
  }
  if (!rawText || rawText.length > MAX_SNAPSHOT_CHARS) return out;
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawText);
  } catch {
    return out;
  }
  if (!parsed || typeof parsed !== "object") return out;
  const rec = parsed as Record<string, unknown>;
  if (rec.schemaVersion !== LEARNER_RECOVERY_SCHEMA_VERSION) return out;
  const top = parseSingleSnapshotEntry(rec, nowMs, ttlMs);
  if (top) {
    out.set(top.problemKey, top);
  }
  if (rec.entries && typeof rec.entries === "object") {
    for (const [k, val] of Object.entries(rec.entries as Record<string, unknown>)) {
      const entry = parseSingleSnapshotEntry(val, nowMs, ttlMs);
      if (entry && entry.problemKey === k) {
        out.set(entry.problemKey, entry);
      }
    }
  }
  return out;
}

export function saveLearnerRecoverySnapshot(
  input: LearnerRecoverySnapshotInput,
  opts?: SnapshotOptions,
): boolean {
  const store = opts?.storage !== undefined ? opts.storage : defaultSessionStorage();
  if (!store) return false;
  if (typeof input.problemKey !== "string" || !input.problemKey.trim()) return false;
  if (typeof input.stepIndex !== "number" || !Number.isFinite(input.stepIndex) || input.stepIndex < 0) {
    return false;
  }
  const display = sanitizeDisplaySnapshot(input.display);
  if (!display) return false;
  const nowMs = opts?.nowMs ?? Date.now();
  const ttlMs = opts?.ttlMs ?? DEFAULT_TTL_MS;
  const normalizedKey = input.problemKey.trim().slice(0, 200);
  const currentEntry: LearnerRecoverySnapshot = {
    schemaVersion: LEARNER_RECOVERY_SCHEMA_VERSION,
    savedAtMs: nowMs,
    problemKey: normalizedKey,
    stepIndex: Math.trunc(input.stepIndex),
    selectedId:
      typeof input.selectedId === "string" && input.selectedId.trim().length > 0
        ? input.selectedId.trim().slice(0, 120)
        : null,
    dockCollapsed: Boolean(input.dockCollapsed),
    mobileViewMode: input.mobileViewMode === "stage_expanded" ? "stage_expanded" : "dock_open",
    display,
    camera: sanitizeCameraSnapshot(input.camera),
  };

  const map = readValidStoredEntries(store, nowMs, ttlMs);
  map.set(normalizedKey, currentEntry);
  const sortedEntries = [...map.values()]
    .sort((a, b) => b.savedAtMs - a.savedAtMs)
    .slice(0, MAX_STORED_PROBLEMS);
  const entriesRecord: Record<string, LearnerRecoverySnapshot> = {};
  for (const entry of sortedEntries) {
    entriesRecord[entry.problemKey] = entry;
  }

  const payload: StoredRecoveryEnvelope = {
    ...currentEntry,
    entries: entriesRecord,
  };

  try {
    let serialized = JSON.stringify(payload);
    if (serialized.length > MAX_SNAPSHOT_CHARS) {
      serialized = JSON.stringify(currentEntry);
      if (serialized.length > MAX_SNAPSHOT_CHARS) return false;
    }
    store.setItem(LEARNER_RECOVERY_STORAGE_KEY, serialized);
    return true;
  } catch {
    return false;
  }
}

export function loadLearnerRecoverySnapshot(
  expectedProblemKey: string,
  opts?: SnapshotOptions,
): LearnerRecoverySnapshot | null {
  const store = opts?.storage !== undefined ? opts.storage : defaultSessionStorage();
  const targetKey = expectedProblemKey.trim();
  if (!store || !targetKey) return null;
  let rawText: string | null = null;
  try {
    rawText = store.getItem(LEARNER_RECOVERY_STORAGE_KEY);
  } catch {
    return null;
  }
  if (!rawText || rawText.length > MAX_SNAPSHOT_CHARS) return null;

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawText);
  } catch {
    clearLearnerRecoverySnapshot(opts);
    return null;
  }
  if (!parsed || typeof parsed !== "object") {
    clearLearnerRecoverySnapshot(opts);
    return null;
  }
  const rec = parsed as Record<string, unknown>;
  if (rec.schemaVersion !== LEARNER_RECOVERY_SCHEMA_VERSION) {
    clearLearnerRecoverySnapshot(opts);
    return null;
  }
  const nowMs = opts?.nowMs ?? Date.now();
  const ttlMs = opts?.ttlMs ?? DEFAULT_TTL_MS;

  // Kiểm tra schema của bản ghi gốc trên cùng để phát hiện dữ liệu hỏng ngay lập tức
  const topSnapshot = parseSingleSnapshotEntry(rec, nowMs, ttlMs);
  if (!topSnapshot) {
    // Nếu không có bản ghi hợp lệ nào trong entries thì xóa storage để dọn sạch snapshot hết hạn/hỏng
    const validMap = readValidStoredEntries(store, nowMs, ttlMs);
    if (validMap.size === 0) {
      clearLearnerRecoverySnapshot(opts);
      return null;
    }
    return validMap.get(targetKey) ?? null;
  }

  if (topSnapshot.problemKey === targetKey) {
    return topSnapshot;
  }

  if (rec.entries && typeof rec.entries === "object") {
    const candidate = (rec.entries as Record<string, unknown>)[targetKey];
    const parsedCandidate = parseSingleSnapshotEntry(candidate, nowMs, ttlMs);
    if (parsedCandidate && parsedCandidate.problemKey === targetKey) {
      return parsedCandidate;
    }
  }

  return null;
}

export function clearLearnerRecoverySnapshot(opts?: SnapshotOptions): void {
  const store = opts?.storage !== undefined ? opts.storage : defaultSessionStorage();
  if (!store) return;
  try {
    store.removeItem(LEARNER_RECOVERY_STORAGE_KEY);
  } catch {
    /* bỏ qua lỗi quyền truy cập storage */
  }
}
