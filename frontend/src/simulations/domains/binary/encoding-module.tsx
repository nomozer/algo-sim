import { TraceBuilder } from "../../../core/trace-builder";
import type { Step, Trace, TraceEvent } from "../../../core/types";
import { IconCheck } from "../../../components/icons";
import type { ConfigResult, SimulationModule, WorkspaceProps } from "../../types";
import { CONV_MAX_VALUE, toBase } from "./convert-module";

/**
 * M17 W3 — MÃ HOÁ KÝ TỰ: ký tự → mã → nhị phân. Engine tất định, engine-owned.
 *
 * RANH GIỚI KIẾN TRÚC (quyết định W3): backend CHỈ kiểm định hợp đồng; toàn bộ
 * việc chạy nằm ở đây. Và ở đây **KHÔNG có bộ chuyển đổi thứ hai** — mã số được
 * đổi sang nhị phân bằng CHÍNH `toBase()` của `base_conversion`
 * (`convert-module.tsx`), nên quy ước hiển thị (không đệm số 0) là MỘT nguồn.
 *
 * Vì sao không dùng `decimal_to_binary`: nó chặn cứng ở 0–255 / 8 bit, trong khi
 * BMP cần tới 65535 — đúng bằng `CONV_MAX_VALUE` của base_conversion.
 *
 * UNICODE THEO CODE POINT, KHÔNG THEO UTF-16 UNIT: `Array.from()` + `codePointAt`.
 * Dùng `text.length`/`charCodeAt` sẽ khiến 😀 thành HAI ký tự BMP "hợp lệ" trong
 * khi backend (Python đếm theo code point) từ chối — sai câm giữa hai tầng, và
 * đường mở-lại-từ-lịch-sử (bất biến #17) đi THẲNG vào engine này.
 */

export const CHAR_ENC_VERSION = "charenc-1.0";
export const MAX_TEXT_CODE_POINTS = 12;
export const ASCII_MAX = 0x7f;
export const BMP_MAX = 0xffff;          // == CONV_MAX_VALUE của base_conversion
const SURROGATE_MIN = 0xd800;
const SURROGATE_MAX = 0xdfff;

export type CharEncoding = "ascii" | "unicode_codepoint";
export const CHAR_ENCODINGS: readonly CharEncoding[] = ["ascii", "unicode_codepoint"];

export interface CharEncodingSpec {
  spec_version: string;
  text: string;
  encoding: CharEncoding;
  notes?: string | null;
}

/** Một hàng kết quả — do ENGINE tính, renderer chỉ đọc. */
export interface EncodedRow {
  index: number;
  char: string;
  /** Nhãn học sinh đọc được cho ký tự khó nhìn (dấu cách…). */
  label: string;
  codePoint: number;
  decimal: number;
  binary: string;
}

export type EncodingPhase = "select_character" | "map_to_code" | "convert_to_binary" | "commit_row";

export interface CharEncodingState {
  spec: CharEncodingSpec;
  trace: Trace;
  cursor: number;
  /** Bảng ĐẦY ĐỦ — renderer chỉ được hiện phần đã commit tới cursor. */
  rows: EncodedRow[];
}

export type CharEncodingValidation =
  | { ok: true; spec: CharEncodingSpec }
  | { ok: false; error: string };

/** Nhãn learner-facing cho ký tự không nhìn thấy được. */
function visibleLabel(ch: string, cp: number): string {
  if (ch === " ") return "dấu cách";
  if (ch === "\t") return "dấu tab";
  if (ch === "\n") return "xuống dòng";
  if (cp < 0x20 || cp === 0x7f) return `ký tự điều khiển (mã ${cp})`;
  return ch;
}

function fail(error: string): CharEncodingValidation {
  return { ok: false, error };
}

/** Duyệt theo CODE POINT — không bao giờ theo UTF-16 unit. */
export function codePointsOf(text: string): number[] {
  return Array.from(text).map((ch) => ch.codePointAt(0) as number);
}

/* ── validator (mirror backend, cùng luật) ──────────────────── */

export function validateCharEncodingSpec(raw: unknown): CharEncodingValidation {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return fail("Config phải là một đối tượng.");
  }
  const r = raw as Record<string, unknown>;
  for (const key of ["code_points", "decimal_values", "binary_values", "rows", "result", "trace"]) {
    if (key in r) return fail(`Config KHÔNG được chứa kết quả đã tính sẵn: ${key}.`);
  }
  const version = (r.spec_version as string) || CHAR_ENC_VERSION;
  if (version !== CHAR_ENC_VERSION) return fail(`spec_version phải là '${CHAR_ENC_VERSION}'.`);

  const encoding = r.encoding as CharEncoding;
  if (!CHAR_ENCODINGS.includes(encoding)) {
    return fail("Trường 'encoding' phải là 'ascii' hoặc 'unicode_codepoint'.");
  }
  const text = r.text;
  if (typeof text !== "string") {
    return fail("Trường 'text' phải là chuỗi ký tự cần mã hoá.");
  }
  if (text === "") return fail("Chưa có ký tự nào để mã hoá.");

  const chars = Array.from(text);        // CODE POINT, không phải UTF-16 unit
  if (chars.length > MAX_TEXT_CODE_POINTS) {
    return fail(`Mô phỏng chỉ chạy tối đa ${MAX_TEXT_CODE_POINTS} ký tự một lần.`);
  }
  for (const ch of chars) {
    const cp = ch.codePointAt(0) as number;
    if (cp >= SURROGATE_MIN && cp <= SURROGATE_MAX) {
      return fail("Chuỗi chứa một nửa cặp ký tự đặc biệt (surrogate) nên không phải một ký tự hoàn chỉnh.");
    }
    if (encoding === "ascii" && cp > ASCII_MAX) {
      return fail(`Ký tự '${ch}' không mã hoá được. Chế độ ASCII chỉ hỗ trợ các ký tự có mã từ 0 đến ${ASCII_MAX}.`);
    }
    if (cp > BMP_MAX) {
      return fail(`Ký tự '${ch}' không mã hoá được. Mô phỏng hiện chỉ hỗ trợ ký tự Unicode trong vùng cơ bản (mã tối đa ${BMP_MAX}), chưa hỗ trợ emoji.`);
    }
  }
  return {
    ok: true,
    spec: {
      spec_version: CHAR_ENC_VERSION,
      text,
      encoding,
      ...(typeof r.notes === "string" ? { notes: r.notes } : {}),
    },
  };
}

/* ── interpreter tất định ───────────────────────────────────── */

export interface CharEncodingRun {
  trace: Trace;
  rows: EncodedRow[];
}

export function runCharacterEncoding(spec: CharEncodingSpec): CharEncodingRun {
  const chars = Array.from(spec.text);
  const b = new TraceBuilder([]);
  const rows: EncodedRow[] = [];

  const step = (events: TraceEvent[], narration: string, line?: number) =>
    b.step(events, narration, false, line);

  chars.forEach((ch, i) => {
    const cp = ch.codePointAt(0) as number;
    const label = visibleLabel(ch, cp);
    const pos = i + 1;

    // 1) chọn ký tự — CHƯA có mã, CHƯA có nhị phân
    step([], `Xét ký tự thứ ${pos}: ${label}.`, pos);

    // 2) tra mã — có mã, VẪN chưa có nhị phân
    b.setVar(`mã ${label}`, cp);
    step([{ type: "assign_var", name: `mã ${label}`, value: cp }],
         `Tra bảng mã: ${label} có mã ${cp}.`, pos);

    // 3) đổi sang nhị phân — DÙNG LẠI toBase() của base_conversion
    const binary = toBase(cp, 2);
    step([{ type: "assign_var", name: `nhị phân ${label}`, value: binary }],
         `Đổi mã ${cp} sang nhị phân: ${binary}.`, pos);

    // 4) chốt hàng
    rows.push({ index: i, char: ch, label, codePoint: cp, decimal: cp, binary });
    step([], `Hoàn thành ký tự ${label}.`, pos);
  });

  const summary = `Đã mã hoá ${chars.length} ký tự theo bảng mã ` +
    `${spec.encoding === "ascii" ? "ASCII" : "Unicode code point"}.`;
  b.step([{ type: "done", result: summary }], summary, false);

  return { trace: b.build(), rows };
}

/** Số hàng ĐÃ CHỐT tính tới bước hiện tại — nguồn của progressive reveal. */
export function committedRowCount(state: CharEncodingState): number {
  const perChar = 4;                       // 4 phase mỗi ký tự
  return Math.min(state.rows.length, Math.floor((state.cursor + 1) / perChar));
}

/** Hàng đang xử lý dở (đã tra mã / đã đổi nhị phân nhưng chưa chốt). */
export function partialRow(state: CharEncodingState): Partial<EncodedRow> | null {
  const perChar = 4;
  const done = committedRowCount(state);
  if (done >= state.rows.length) return null;
  const phase = (state.cursor + 1) % perChar;      // 1=select, 2=map, 3=convert
  if (phase === 0) return null;
  const row = state.rows[done];
  if (phase === 1) return { index: row.index, char: row.char, label: row.label };
  if (phase === 2) return { index: row.index, char: row.char, label: row.label,
                            codePoint: row.codePoint, decimal: row.decimal };
  return { ...row };
}

/* ── module ─────────────────────────────────────────────────── */

function clampCursor(state: CharEncodingState, step: number): number {
  return Math.max(0, Math.min(step, state.trace.steps.length - 1));
}

type Props = WorkspaceProps<CharEncodingSpec, CharEncodingState>;

const ENCODING_LABEL: Record<CharEncoding, string> = {
  ascii: "ASCII",
  unicode_codepoint: "Unicode code point",
};

function stepOf(state: CharEncodingState): Step {
  return state.trace.steps[clampCursor(state, state.cursor)];
}

export function CharEncodingWorkspace({ state }: Props) {
  const cursor = clampCursor(state, state.cursor);
  const step = stepOf(state);
  const shown = committedRowCount({ ...state, cursor });
  const partial = partialRow({ ...state, cursor });
  const last = cursor >= state.trace.steps.length - 1;
  const done = step.events.find((e) => e.type === "done");

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div>
        {`Chuỗi cần mã hoá: “${state.spec.text}” · Bảng mã: ${ENCODING_LABEL[state.spec.encoding]}`}
      </div>

      <div className="sim-stage">
        <table className="truth-table">
          <thead>
            <tr>
              <th>Vị trí</th><th>Ký tự</th><th>Mã (code point)</th>
              <th>Thập phân</th><th>Nhị phân</th>
            </tr>
          </thead>
          <tbody>
            {state.rows.slice(0, shown).map((row) => (
              <tr key={row.index}>
                <td>{row.index + 1}</td>
                <td>{row.label}</td>
                <td>{`U+${row.codePoint.toString(16).toUpperCase().padStart(4, "0")}`}</td>
                <td>{row.decimal}</td>
                <td>{row.binary}</td>
              </tr>
            ))}
            {partial && (
              <tr className="is-current">
                <td>{(partial.index ?? 0) + 1}</td>
                <td>{partial.label}</td>
                <td>
                  {partial.codePoint === undefined
                    ? "…"
                    : `U+${partial.codePoint.toString(16).toUpperCase().padStart(4, "0")}`}
                </td>
                <td>{partial.decimal ?? "…"}</td>
                <td>{partial.binary ?? "…"}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="narration-bar">{step.narration}</div>

      {last && done && done.type === "done" && (
        <div className="result-banner">
          <IconCheck size={15} /> {done.result}
        </div>
      )}
    </div>
  );
}

export function CharEncodingInspector({ state }: Props) {
  const cursor = clampCursor(state, state.cursor);
  const partial = partialRow({ ...state, cursor });
  const shown = committedRowCount({ ...state, cursor });
  const current = partial ?? state.rows[Math.max(0, shown - 1)];
  if (!current) return null;
  return (
    <div className="stack" style={{ gap: "var(--sp-xs)" }}>
      <div>{`Ký tự đang xét: ${current.label}`}</div>
      {current.decimal !== undefined && <div>{`Mã thập phân: ${current.decimal}`}</div>}
      {current.binary !== undefined && <div>{`Dãy bit: ${current.binary}`}</div>}
    </div>
  );
}

export function makeCharEncodingModule(): SimulationModule<CharEncodingSpec, CharEncodingState> {
  return {
    id: "binary.character_encoding",
    domain: "binary",
    title: "Mã hoá ký tự",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],

    validateConfig: (raw): ConfigResult<CharEncodingSpec> => {
      const v = validateCharEncodingSpec(raw);
      return v.ok ? { ok: true, config: v.spec } : { ok: false, error: v.error };
    },

    init: (spec) => {
      const run = runCharacterEncoding(spec);
      return { spec, trace: run.trace, cursor: 0, rows: run.rows };
    },

    apply: (state) => state,

    timeline: {
      stepCount: (s) => s.trace.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    getExplainContext: (state) => {
      const cursor = clampCursor(state, state.cursor);
      return {
        simulation_id: "binary.character_encoding",
        text: state.spec.text,
        encoding: state.spec.encoding,
        current_step: cursor + 1,
        total_steps: state.trace.steps.length,
        narration: state.trace.steps[cursor].narration,
        completed_rows: state.rows.slice(0, committedRowCount({ ...state, cursor })),
        max_code_point: CONV_MAX_VALUE,
      };
    },

    Workspace: CharEncodingWorkspace,
    Inspector: CharEncodingInspector,
  };
}
