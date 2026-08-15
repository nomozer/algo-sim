/**
 * Khai báo kiểu cho `evidence.mjs`.
 *
 * Vì sao có file này thay vì đổi `evidence.mjs` thành TypeScript: các script
 * trong `frontend/scripts/` chạy THẲNG bằng `node` (harness đo, runner trình
 * duyệt), không đi qua bundler. Đổi sang `.ts` sẽ buộc mọi lượt chạy phải biên
 * dịch trước — thêm một bước có thể quên, ở đúng chỗ mà "quên" nghĩa là đo sai.
 *
 * Nên file nguồn ở lại JS thuần, và đây là bản chiếu kiểu cho phía test.
 */

export declare const PROVENANCE_VERSION: number;
export declare const SOURCE_PATHS: string[];

export declare function gitHead(): string;
export declare function sourceFingerprint(): string;
export declare function dirtyRelevantSources(): string[];

export interface Provenance {
  provenanceVersion: number;
  sourceFingerprint: string;
  dirtyRelevantSources: string[];
  head: string;
  dirty: boolean;
  generatedAt: string;
  tool: string;
  toolVersion: string;
  environment: Record<string, unknown>;
}

export declare function provenance(tool: string, env?: Record<string, unknown>): Provenance;

export type ProvenanceState =
  | "FRESH"
  | "STALE_SOURCE"
  | "DIRTY_SOURCE"
  | "INCOMPATIBLE_TOOL"
  | "UNKNOWN_PROVENANCE";

export declare function provenanceVerdict(data: unknown): {
  state: ProvenanceState;
  reason: string | null;
};

export declare function assertFresh(path: string): {
  ok: boolean;
  state: ProvenanceState;
  reason: string | null;
  data: unknown;
};

/* ─── LƯỢT CHỨNG NHẬN — nguồn phải đứng yên từ đầu tới cuối lượt ─────────── */

export declare const SWEEP_VALID: "CERTIFICATION_SWEEP_VALID";
export declare const SWEEP_INVALID: "CERTIFICATION_SWEEP_INVALID";
export declare const SWEEP_FAULTS: {
  DIRTY_AT_START: "SOURCE_DIRTY_AT_SWEEP_START";
  DIRTY_AT_END: "SOURCE_DIRTY_AT_SWEEP_END";
  HEAD_MOVED: "HEAD_MOVED_DURING_SWEEP";
  FINGERPRINT_CHANGED: "SOURCE_FINGERPRINT_CHANGED_DURING_SWEEP";
};

export interface SweepBegin {
  tool: string;
  startedAt: string;
  headBefore: string;
  sourceFingerprintBefore: string;
  dirtyBefore: string[];
}

export interface SweepRecord extends SweepBegin {
  endedAt: string;
  headAfter: string;
  sourceFingerprintAfter: string;
  dirtyAfter: string[];
}

export declare function sweepBegin(tool: string): SweepBegin;
export declare function sweepEnd(begin: SweepBegin): SweepRecord;
export declare function sweepVerdict(sweep: unknown): {
  state: typeof SWEEP_VALID | typeof SWEEP_INVALID;
  faults: string[];
};

export declare function crossCheckFreshness(paths: string[]): {
  rows: { path: string; state: ProvenanceState; sourceFingerprint: string | null }[];
  counts: Record<string, number>;
  uniqueFingerprints: number;
  fingerprints: string[];
  ok: boolean;
};
