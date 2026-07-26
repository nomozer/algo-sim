/**
 * Cơ chế ĐỔI CƠ SỐ — phần THUẦN TẤT ĐỊNH, không React, không renderer.
 *
 * Trích ra từ `convert-module.tsx` (M17 P1a) để `binary.character_encoding`
 * dùng lại được **chính cơ chế**, chứ không chỉ dùng lại hàm `toBase()`.
 *
 * Vì sao phải trích: audit authenticity phát hiện W3 gọi thẳng `toBase()` và
 * **bỏ qua `divideSteps()`** đang nằm trong đúng file nó import — nên dãy bit
 * được **thông báo** thay vì được **dẫn ra**. `divideSteps` khi đó là private
 * của một file `.tsx`, không reuse sạch được.
 *
 * Ràng buộc của module này:
 * - KHÔNG import React / renderer / store / registry / fixture / target id;
 * - cùng input → cùng output; không timestamp, không random, không LLM;
 * - đây là NGUỒN DUY NHẤT của phép đổi cơ số trong toàn frontend.
 *
 * `convert-module.tsx` re-export lại các ký hiệu này nên mọi import cũ giữ nguyên.
 */

export const CONV_BASES = [2, 8, 10, 16] as const;
export type ConvBase = (typeof CONV_BASES)[number];
export type ConvStrategy = "quotient_remainder" | "positional_weights" | "two_stage";

export interface BaseConvConfig {
  sourceBase: ConvBase;
  targetBase: ConvBase;
  /** Chuỗi chữ số CANONICAL theo source base (hoa, không số 0 thừa đầu). */
  inputValue: string;
  strategy: ConvStrategy;
  notes: string | null;
}

export type ConvStep =
  | { kind: "intro"; narration: string }
  | {
      kind: "weight";
      digit: string;
      digitValue: number;
      position: number; // số mũ của trọng số
      weight: number;
      product: number;
      runningSum: number;
      narration: string;
    }
  | {
      kind: "divide";
      value: number;
      base: number;
      quotient: number;
      remainder: number;
      digit: string;
      narration: string;
    }
  | { kind: "stage"; stage: 1 | 2; narration: string }
  | { kind: "result"; output: string; narration: string };

/** Bước chia lấy dư — hẹp lại từ `ConvStep` để nơi dùng khỏi phải narrow lặp. */
export type DivideStep = Extract<ConvStep, { kind: "divide" }>;

const DIGITS = "0123456789ABCDEF";
export const CONV_MAX_VALUE = 65535; // bound 16 bit — bounded capability

export function digitsValid(value: string, base: ConvBase): boolean {
  if (value.length === 0 || value.length > 16) return false;
  const allowed = DIGITS.slice(0, base);
  return [...value.toUpperCase()].every((ch) => allowed.includes(ch));
}

/** Chuẩn hóa canonical: chữ HOA, bỏ số 0 thừa đầu (giữ "0" đơn). */
export function canonicalDigits(value: string): string {
  const up = value.toUpperCase().replace(/^0+(?=.)/, "");
  return up;
}

export function parseInBase(value: string, base: ConvBase): number {
  return [...value].reduce((acc, ch) => acc * base + DIGITS.indexOf(ch), 0);
}

export function toBase(value: number, base: ConvBase): string {
  if (value === 0) return "0";
  let v = value;
  let out = "";
  while (v > 0) {
    out = DIGITS[v % base] + out;
    v = Math.floor(v / base);
  }
  return out;
}

export function strategyOf(source: ConvBase, target: ConvBase): ConvStrategy {
  if (source === 10) return "quotient_remainder";
  if (target === 10) return "positional_weights";
  return "two_stage";
}

export const BASE_NAME: Record<ConvBase, string> = {
  2: "nhị phân",
  8: "bát phân",
  10: "thập phân",
  16: "thập lục phân",
};

/* ── engine tất định ─────────────────────────────────────────── */

export function weightSteps(digits: string, base: ConvBase, steps: ConvStep[]): number {
  let sum = 0;
  const n = digits.length;
  for (let i = 0; i < n; i++) {
    const digit = digits[i];
    const digitValue = DIGITS.indexOf(digit);
    const position = n - 1 - i;
    const weight = base ** position;
    const product = digitValue * weight;
    sum += product;
    steps.push({
      kind: "weight",
      digit,
      digitValue,
      position,
      weight,
      product,
      runningSum: sum,
      narration:
        `Chữ số ${digit} (giá trị ${digitValue}) ở vị trí trọng số ${base}^${position} = ${weight}: ` +
        `cộng ${digitValue} × ${weight} = ${product}. Tổng dồn: ${sum}.`,
    });
  }
  return sum;
}

/**
 * Chia lấy dư liên tiếp — đẩy từng phép chia vào `steps` và trả kết quả DẪN RA
 * TỪ CHUỖI SỐ DƯ (đọc ngược). Không gọi `toBase`: kết quả ở đây và `toBase`
 * phải trùng nhau vì cùng một phép toán, không phải vì chép của nhau.
 */
export function divideSteps(value: number, base: ConvBase, steps: ConvStep[]): string {
  if (value === 0) {
    steps.push({
      kind: "divide",
      value: 0,
      base,
      quotient: 0,
      remainder: 0,
      digit: "0",
      narration: `0 chia ${base} được 0 dư 0 — chữ số duy nhất là 0.`,
    });
    return "0";
  }
  let v = value;
  let out = "";
  while (v > 0) {
    const quotient = Math.floor(v / base);
    const remainder = v % base;
    const digit = DIGITS[remainder];
    out = digit + out;
    steps.push({
      kind: "divide",
      value: v,
      base,
      quotient,
      remainder,
      digit,
      narration:
        `${v} : ${base} = ${quotient} dư ${remainder} → chữ số ${digit}. ` +
        `Các số dư đọc NGƯỢC từ dưới lên sẽ thành kết quả.`,
    });
    v = quotient;
  }
  return out;
}

export function buildConvSteps(config: BaseConvConfig): {
  decimalValue: number;
  steps: ConvStep[];
  result: string;
} {
  const { sourceBase, targetBase, inputValue } = config;
  const steps: ConvStep[] = [];
  steps.push({
    kind: "intro",
    narration:
      `Đổi ${inputValue} từ hệ ${BASE_NAME[sourceBase]} (cơ số ${sourceBase}) ` +
      `sang hệ ${BASE_NAME[targetBase]} (cơ số ${targetBase}).`,
  });

  let decimalValue: number;
  let result: string;

  if (sourceBase === 10) {
    decimalValue = parseInBase(inputValue, 10);
    result = divideSteps(decimalValue, targetBase, steps);
  } else if (targetBase === 10) {
    steps.push({
      kind: "stage",
      stage: 1,
      narration: `Tính giá trị theo TRỌNG SỐ VỊ TRÍ của hệ cơ số ${sourceBase}.`,
    });
    decimalValue = weightSteps(inputValue, sourceBase, steps);
    result = String(decimalValue);
  } else {
    steps.push({
      kind: "stage",
      stage: 1,
      narration:
        `Giai đoạn 1: đổi ${inputValue} (cơ số ${sourceBase}) về thập phân bằng trọng số vị trí.`,
    });
    decimalValue = weightSteps(inputValue, sourceBase, steps);
    steps.push({
      kind: "stage",
      stage: 2,
      narration:
        `Giai đoạn 2: đổi ${decimalValue} (thập phân) sang cơ số ${targetBase} bằng chia lấy dư.`,
    });
    result = divideSteps(decimalValue, targetBase, steps);
  }

  steps.push({
    kind: "result",
    output: result,
    narration: `Kết quả: ${inputValue} (cơ số ${sourceBase}) = ${result} (cơ số ${targetBase}).`,
  });
  return { decimalValue, steps, result };
}
