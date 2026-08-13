import { TraceBuilder } from "../../../core/trace-builder";
import type { Step, Trace, TraceEvent } from "../../../core/types";
import { IconCheck } from "../../../components/icons";
import type { ConfigResult, SimulationModule, WorkspaceProps } from "../../types";
import { CONV_MAX_VALUE, divideSteps } from "./base-conversion";
import type { ConvStep, DivideStep } from "./base-conversion";

/**
 * M17 W3 — MÃ HOÁ KÝ TỰ: ký tự → mã → nhị phân. Engine tất định, engine-owned.
 *
 * RANH GIỚI KIẾN TRÚC (quyết định W3): backend CHỈ kiểm định hợp đồng; toàn bộ
 * việc chạy nằm ở đây. Và ở đây **KHÔNG có bộ chuyển đổi thứ hai** — mã số được
 * đổi sang nhị phân bằng CHÍNH cơ chế CHIA LẤY DƯ của `base_conversion`
 * (`divideSteps()` ở `./base-conversion`), nên quy ước hiển thị (không đệm số 0)
 * là MỘT nguồn.
 *
 * M17 P1a — trước đây chỗ này gọi thẳng `toBase()`, tức là chỉ mượn KẾT QUẢ:
 * học sinh thấy `65 → 1000001` như một tuyên bố, không thấy vì sao. Nay engine
 * chạy từng phép chia thật và dãy bit được DẪN RA từ chuỗi số dư. `toBase()`
 * chỉ còn dùng trong test hồi quy để xác nhận hai đường cho cùng kết quả.
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

export type EncodingPhase =
  | "select_character"
  | "map_to_code"
  | "begin_conversion"
  | "divide_step"
  | "read_remainders"
  | "convert_compact"
  | "commit_row"
  | "complete";

/** Trạng thái MỘT phép chia — engine sinh, renderer chỉ đọc. */
export interface DivisionState {
  /** Số bị chia của bước này (65, rồi 32, rồi 16…). */
  value: number;
  base: number;
  quotient: number;
  remainder: number;
  digit: string;
  /** Thứ tự phép chia trong chuỗi, 0-based. */
  stepIndex: number;
  /** Các số dư đã thu được, THEO THỨ TỰ SINH (chưa đảo). */
  collected: string[];
}

/**
 * Metadata mỗi bước — song ánh 1:1 với `trace.steps`. Renderer tra theo cursor
 * thay vì làm SỐ HỌC trên cursor. Bản cũ dùng `floor((cursor+1)/4)` vì mỗi ký tự
 * cố định 4 phase; nay số bước chia thay đổi theo giá trị mã nên số học đó sai.
 */
export interface EncStepMeta {
  /** -1 ở bước tổng kết. */
  charIndex: number;
  phase: EncodingPhase;
  /** Ký tự này có bung chi tiết phép chia không (§10: ký tự đầu tiên). */
  detailed: boolean;
  division?: DivisionState;
  /** Số hàng ĐÃ CHỐT tính đến hết bước này. */
  committed: number;
}

export interface CharEncodingState {
  spec: CharEncodingSpec;
  trace: Trace;
  cursor: number;
  /** Bảng ĐẦY ĐỦ — renderer chỉ được hiện phần đã commit tới cursor. */
  rows: EncodedRow[];
  /** Song ánh với `trace.steps` — nguồn của progressive reveal. */
  meta: EncStepMeta[];
}

export type CharEncodingValidation =
  | { ok: true; spec: CharEncodingSpec }
  | { ok: false; error: string };

/**
 * W3-VR2 — hiển thị ô "Ký tự" sao cho KHÔNG lẫn với con số.
 * Ký tự `'7'` in trần cạnh cột "Thập phân 55" đọc rất dễ thành *số* 7 — đúng
 * điểm nhầm mà bài học này tồn tại để sửa. Ký tự in được thì bọc nháy; ký tự đã
 * có nhãn mô tả (dấu cách…) giữ nguyên nhãn. Đây là TRÌNH BÀY thuần: cả `char`
 * lẫn `label` đều lấy từ trace, renderer không suy diễn gì thêm.
 */
export function displayChar(row: { char: string; label: string }): string {
  return row.label === row.char ? `'${row.char}'` : row.label;
}

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
  meta: EncStepMeta[];
}

/**
 * Chính sách BUNG CHI TIẾT (M17 P1a §10) — ký tự ĐẦU TIÊN mở đầy đủ chuỗi chia
 * lấy dư; các ký tự sau trình bày rút gọn. Đây là quyết định TRÌNH BÀY: mọi ký
 * tự đều đi qua **cùng một** `divideSteps()`, nên không có đường engine thứ hai
 * và không thể lệch kết quả giữa hai chế độ. Lý do rút gọn: 12 code point × ~13
 * phép chia sẽ cho timeline vài trăm bước, học sinh không đọc nổi.
 */
function isDetailed(charIndex: number): boolean {
  return charIndex === 0;
}

export function runCharacterEncoding(spec: CharEncodingSpec): CharEncodingRun {
  const chars = Array.from(spec.text);
  const b = new TraceBuilder([]);
  const rows: EncodedRow[] = [];
  const meta: EncStepMeta[] = [];
  let committed = 0;

  const emit = (
    events: TraceEvent[],
    narration: string,
    charIndex: number,
    phase: EncodingPhase,
    extra: { division?: DivisionState; detailed?: boolean } = {},
  ) => {
    b.step(events, narration, false, charIndex >= 0 ? charIndex + 1 : undefined);
    meta.push({
      charIndex,
      phase,
      detailed: extra.detailed ?? (charIndex >= 0 && isDetailed(charIndex)),
      ...(extra.division ? { division: extra.division } : {}),
      committed,
    });
  };

  chars.forEach((ch, i) => {
    const cp = ch.codePointAt(0) as number;
    const label = visibleLabel(ch, cp);
    const pos = i + 1;
    const detailed = isDetailed(i);

    // 1) chọn ký tự — CHƯA có mã, CHƯA có nhị phân
    emit([], `Xét ký tự thứ ${pos}: ${label}.`, i, "select_character");

    // 2) tra mã — có mã, VẪN chưa có nhị phân
    b.setVar(`mã ${label}`, cp);
    emit([{ type: "assign_var", name: `mã ${label}`, value: cp }],
         `Tra bảng mã: ${label} có mã ${cp}.`, i, "map_to_code");

    // 3) ĐỔI CƠ SỐ — dùng lại CHÍNH cơ chế chia lấy dư của base_conversion.
    //    `divideSteps` đẩy từng phép chia vào `convSteps` và trả kết quả DẪN RA
    //    TỪ CHUỖI SỐ DƯ. Không gọi `toBase()` ở runtime: một nguồn duy nhất.
    const convSteps: ConvStep[] = [];
    const binary = divideSteps(cp, 2, convSteps);
    const divides = convSteps.filter((s): s is DivideStep => s.kind === "divide");

    if (detailed) {
      emit([], `Đổi mã ${cp} sang nhị phân: CHIA LIÊN TIẾP cho 2 và ghi lại số dư.`,
           i, "begin_conversion");

      const collected: string[] = [];
      divides.forEach((d, k) => {
        collected.push(d.digit);
        emit([{ type: "assign_var", name: "số dư thu được", value: collected.join(" ") }],
             d.narration, i, "divide_step",
             { division: { value: d.value, base: d.base, quotient: d.quotient,
                           remainder: d.remainder, digit: d.digit,
                           stepIndex: k, collected: [...collected] } });
      });

      const doc = [...collected].reverse().join("");
      b.setVar(`nhị phân ${label}`, binary);
      emit([{ type: "assign_var", name: `nhị phân ${label}`, value: binary }],
           `Đọc các số dư NGƯỢC từ dưới lên: ${doc} → mã ${cp} trong nhị phân là ${binary}.`,
           i, "read_remainders");
    } else {
      b.setVar(`nhị phân ${label}`, binary);
      emit([{ type: "assign_var", name: `nhị phân ${label}`, value: binary }],
           `Mã ${cp}: áp dụng CÙNG quy tắc chia lấy dư cho 2 qua ${divides.length} ` +
           `phép chia → ${binary}.`,
           i, "convert_compact");
    }

    // 4) chốt hàng
    rows.push({ index: i, char: ch, label, codePoint: cp, decimal: cp, binary });
    committed = rows.length;
    emit([], `Hoàn thành ký tự ${label}.`, i, "commit_row");
  });

  const summary = `Đã mã hoá ${chars.length} ký tự theo bảng mã ` +
    `${spec.encoding === "ascii" ? "ASCII" : "Unicode code point"}.`;
  emit([{ type: "done", result: summary }], summary, -1, "complete", { detailed: false });

  return { trace: b.build(), rows, meta };
}

/** Metadata của bước hiện tại — renderer KHÔNG tự suy từ cursor. */
export function metaAt(state: CharEncodingState): EncStepMeta {
  const i = Math.max(0, Math.min(state.cursor, state.meta.length - 1));
  return state.meta[i];
}

/** Số hàng ĐÃ CHỐT tính tới bước hiện tại — engine ghi sẵn, không tính lại. */
export function committedRowCount(state: CharEncodingState): number {
  return Math.min(state.rows.length, metaAt(state).committed);
}

/** Hàng đang xử lý dở — hé lộ đúng theo phase, không sớm hơn. */
export function partialRow(state: CharEncodingState): Partial<EncodedRow> | null {
  const m = metaAt(state);
  if (m.charIndex < 0 || m.phase === "commit_row") return null;
  const row = state.rows[m.charIndex];
  if (!row) return null;
  const base = { index: row.index, char: row.char, label: row.label };
  if (m.phase === "select_character") return base;
  // mã đã tra xong; dãy bit chỉ lộ SAU khi cơ chế chạy hết
  const withCode = { ...base, codePoint: row.codePoint, decimal: row.decimal };
  if (m.phase === "read_remainders" || m.phase === "convert_compact") return { ...row };
  return withCode;
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

/**
 * Các phép chia ĐÃ DIỄN RA của ký tự đang xét, tính tới cursor — đọc thẳng từ
 * `state.meta` do engine sinh. Renderer KHÔNG chia, KHÔNG lấy dư, KHÔNG gọi
 * `divideSteps`/`toBase`/`toString(2)`: nếu trace nói `65 : 2 = 30 dư 5` thì
 * màn hình phải hiện đúng như vậy (có test trace bịa khoá điều này).
 */
export function divisionsSoFar(state: CharEncodingState, upTo: number): DivisionState[] {
  const m = state.meta[Math.max(0, Math.min(upTo, state.meta.length - 1))];
  if (!m || m.charIndex < 0) return [];
  return state.meta
    .slice(0, upTo + 1)
    .filter((x) => x.charIndex === m.charIndex && x.division)
    .map((x) => x.division as DivisionState);
}

/** Bảng chia lấy dư — chỉ hiện khi cơ chế đang chạy cho ký tự chi tiết. */
function DivisionPanel({ state, cursor }: { state: CharEncodingState; cursor: number }) {
  const m = state.meta[cursor];
  const active = m.phase === "begin_conversion" || m.phase === "divide_step" ||
                 m.phase === "read_remainders";
  if (!active) return null;
  const rows = divisionsSoFar(state, cursor);
  const row = state.rows[m.charIndex];
  const collected = rows.length ? rows[rows.length - 1].collected : [];
  const finished = m.phase === "read_remainders";

  return (
    <div className="sim-stage">
      <div>
        {`Đổi mã của ${displayChar(row)} sang nhị phân — chia liên tiếp cho 2, giữ lại số dư:`}
      </div>
      <table className="truth-table">
        <thead>
          <tr><th>Số bị chia</th><th>: 2</th><th>Thương</th><th>Số dư</th></tr>
        </thead>
        <tbody>
          {rows.map((d) => (
            <tr key={d.stepIndex} className={d.stepIndex === rows.length - 1 ? "is-current" : undefined}>
              <td>{d.value}</td><td>{d.base}</td><td>{d.quotient}</td><td>{d.digit}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr className="is-current"><td>{row.decimal}</td><td>2</td><td>…</td><td>…</td></tr>
          )}
        </tbody>
      </table>
      <div>
        {`Số dư đã thu (từ trên xuống): ${collected.length ? collected.join(" ") : "…"}`}
      </div>
      {/* W3-SIM-VR1 — chỉ ĐỐI CHIẾU hai chiều đọc. Bản đầu viết
          "…→ nhị phân là 1000001." trong khi băng thuyết minh nói y hệt câu đó:
          cùng lớp lỗi lặp đã gặp ở W3-VR1/W2C-VR3. Kết luận để một chỗ. */}
      <div>
        {finished
          ? `Đọc ngược lại, từ DƯỚI LÊN: ${[...collected].reverse().join(" ")}`
          : "Đọc NGƯỢC các số dư từ dưới lên sẽ ra dãy nhị phân."}
      </div>
    </div>
  );
}

/** W4B-4C — đổi ký tự hoặc bảng mã, xem điểm mã và nhị phân đổi theo. */
function EncodingParamBar({ state, busy, dispatch }: Props) {
  return (
    <div className="param-bar" role="group" aria-label="Chọn ký tự và bảng mã">
      <label>
        Ký tự
        <input value={state.spec.text} disabled={busy} aria-label="Ký tự cần mã hoá"
          onChange={(e) => dispatch({ type: "set_param", name: "text", value: e.target.value })} />
      </label>
      <label>
        Bảng mã
        <select value={state.spec.encoding} disabled={busy}
          onChange={(e) => dispatch({ type: "set_param", name: "encoding", value: e.target.value })}>
          <option value="ascii">ASCII</option>
          <option value="unicode_codepoint">Unicode (điểm mã)</option>
        </select>
      </label>
    </div>
  );
}

export function CharEncodingWorkspace({ state, config, busy, dispatch }: Props) {
  const cursor = clampCursor(state, state.cursor);
  const step = stepOf(state);
  const partial = partialRow({ ...state, cursor });
  const last = cursor >= state.trace.steps.length - 1;
  const done = step.events.find((e) => e.type === "done");

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <EncodingParamBar state={state} config={config} busy={busy} dispatch={dispatch} />
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
          {/* W5 §4A — BẢNG LÀ TRẠNG THÁI HIỆN TẠI CỦA ĐẦU VÀO, KHÔNG PHẢI BĂNG
              HOẠT HÌNH.

              Bản trước cắt `state.rows` theo `committedRowCount`, nên mở bài
              lên chỉ thấy hàng đầu và phải bấm Tiến mới có hàng sau. Đo ở 1920:
              dãy bit của 'T', 'i', 'n' KHÔNG có mặt trong DOM ở cursor 0.

              Hệ quả sư phạm không chỉ là bất tiện: học sinh đổi "Tin" thành
              "Bin" rồi nhìn một bảng chỉ có một hàng thì không so sánh được
              đúng thứ vừa đổi. Bảng đầy đủ mới là thứ trả lời "chuỗi này mã hoá
              ra gì".

              Diễn giải KHÔNG mất đi: hàng nào trace đang xét thì được đánh dấu
              `is-current`, và `DivisionPanel` bên dưới vẫn kể từng phép chia. */}
          <tbody>
            {state.rows.map((row) => (
              <tr key={row.index}
                className={partial?.index === row.index ? "is-current" : undefined}>
                <td>{row.index + 1}</td>
                <td>{displayChar(row)}</td>
                <td>{`U+${row.codePoint.toString(16).toUpperCase().padStart(4, "0")}`}</td>
                <td>{row.decimal}</td>
                <td>{row.binary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <DivisionPanel state={{ ...state, cursor }} cursor={cursor} />

      {/* (SHELL-N) Thuyết minh đã về khe của shell — luật ẩn ở bước cuối
          (W3-VR1, cùng lớp lỗi W2C-VR3) nay sống trong `narrate` bên dưới. */}

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
      <div>{`Ký tự đang xét: ${displayChar({ char: current.char ?? "", label: current.label ?? "" })}`}</div>
      {current.decimal !== undefined && <div>{`Mã thập phân: ${current.decimal}`}</div>}
      {current.binary !== undefined && <div>{`Dãy bit: ${current.binary}`}</div>}
    </div>
  );
}

/**
 * W4B-4C — ĐỔI KÝ TỰ / BẢNG MÃ, XEM MÃ ĐỔI THEO.
 *
 * Cơ chế của bài là ánh xạ KÝ TỰ → ĐIỂM MÃ → NHỊ PHÂN. Bấm Tiến qua một chuỗi
 * cố định chỉ cho thấy MỘT ánh xạ; gõ ký tự khác rồi thấy điểm mã đổi mới là
 * thứ dạy được quy tắc.
 *
 * Miền ĐÓNG: `text` (đúng ràng buộc validator hiện hành) và `encoding` trong
 * {ascii, unicode_codepoint}. Không mở thành phòng thí nghiệm mã hoá.
 */
export function withEncodingParam(
  spec: CharEncodingSpec,
  name: string,
  value: number | string | boolean,
): CharEncodingSpec | null {
  if (typeof value !== "string") return null;
  if (name === "encoding") {
    if (value !== "ascii" && value !== "unicode_codepoint") return null;
    if (value === spec.encoding) return null;
    const next = { ...spec, encoding: value as CharEncoding };
    // Đi qua ĐÚNG cổng validator — ASCII không nhận mọi ký tự Unicode.
    return validateCharEncodingSpec(next).ok ? next : null;
  }
  if (name === "text") {
    if (value === spec.text) return null;
    const next = { ...spec, text: value };
    return validateCharEncodingSpec(next).ok ? next : null;
  }
  return null;
}

export function makeCharEncodingModule(): SimulationModule<CharEncodingSpec, CharEncodingState> {
  return {
    id: "binary.character_encoding",
    domain: "binary",
    title: "Mã hoá ký tự",
    /* W4B-4C — `progressive` → `hybrid`: nay có CẢ dòng thời gian giải thích
       LẪN tham số học sinh đổi được bất cứ lúc nào trên sân khấu. */
    interactionMode: "hybrid",
    supportedVisualModes: ["2d"],

    validateConfig: (raw): ConfigResult<CharEncodingSpec> => {
      const v = validateCharEncodingSpec(raw);
      return v.ok ? { ok: true, config: v.spec } : { ok: false, error: v.error };
    },

    init: (spec) => {
      const run = runCharacterEncoding(spec);
      return { spec, trace: run.trace, cursor: 0, rows: run.rows, meta: run.meta };
    },

    /* W4B-4C — đổi ký tự/bảng mã ⇒ chạy lại `runCharacterEncoding`. */
    apply: (state, action) => {
      if (action.type !== "set_param") return state;
      const next = withEncodingParam(state.spec, action.name, action.value);
      if (!next) return state;
      const run = runCharacterEncoding(next);
      return { spec: next, trace: run.trace, cursor: 0, rows: run.rows, meta: run.meta };
    },

    timeline: {
      stepCount: (s) => s.trace.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    // (SHELL-N) W3-VR1: bước cuối, thuyết minh TRÙNG y hệt băng kết quả —
    // trả `null` để không nói hai lần cùng một câu.
    narrate: (state) => {
      const cursor = clampCursor(state, state.cursor);
      const step = state.trace.steps[cursor];
      const last = cursor >= state.trace.steps.length - 1;
      const done = step.events.find((e) => e.type === "done");
      if (last && done && done.type === "done" && step.narration === done.result) return null;
      return { text: step.narration };
    },

    /* W4B-4D — mô hình chạy config NÀO ngay lúc này; shell so với bản đã
       validate để nói ra khi học sinh đã kéo mô hình rời khỏi đề bài. */
    /* State ở đây gọi nó là `spec`, không phải `config` — cùng vai trò, khác
       tên, nên khai tay chứ đừng suy từ miền khác. */
    currentConfig: (state) => state.spec,

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
