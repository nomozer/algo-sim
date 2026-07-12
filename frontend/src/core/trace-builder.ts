import type { Mark, Step, Trace, TraceEvent, TraceSource } from "./types";

/**
 * Can thiệp what-if (R3.3): sau khi thuật toán phát xong bước thứ `afterStep`,
 * đổi chỗ phần tử i và j rồi để thuật toán chạy tiếp trên dãy đã bị sửa.
 * Vì thuật toán tất định, đoạn trước bước k của nhánh giống hệt dòng chính.
 */
export interface WhatIfSwap {
  afterStep: number;
  i: number;
  j: number;
}

/**
 * Bộ dựng trace: engine thao tác trên mảng nội bộ, mỗi lần gọi step()
 * chụp lại snapshot đầy đủ (R3.1a) kèm sự kiện + thuyết minh.
 */
export class TraceBuilder {
  private steps: Step[] = [];
  private vars: Record<string, number | string | boolean | null> = {};
  private marks: Record<number, Mark> = {};
  private array: number[];
  /** Định danh bền của phần tử tại từng vị trí — nuôi hoạt cảnh trượt cột. */
  private ids: number[];
  private whatIf: WhatIfSwap | undefined;

  constructor(array: number[], private source: TraceSource = "engine", whatIf?: WhatIfSwap) {
    this.array = [...array];
    this.ids = array.map((_, i) => i);
    this.whatIf = whatIf;
  }

  get length(): number {
    return this.array.length;
  }

  at(i: number): number {
    return this.array[i];
  }

  setVar(name: string, value: number | string | boolean | null): void {
    this.vars[name] = value;
  }

  swap(i: number, j: number): void {
    [this.array[i], this.array[j]] = [this.array[j], this.array[i]];
    [this.ids[i], this.ids[j]] = [this.ids[j], this.ids[i]];
  }

  set(i: number, value: number): void {
    this.array[i] = value;
  }

  idAt(i: number): number {
    return this.ids[i];
  }

  /** Dời định danh khi dời giá trị (sắp xếp chèn: a[to] ← a[from]). */
  moveId(from: number, to: number): void {
    this.ids[to] = this.ids[from];
  }

  setIdAt(i: number, id: number): void {
    this.ids[i] = id;
  }

  mark(index: number, status: Mark): void {
    this.marks[index] = status;
  }

  unmark(index: number): void {
    delete this.marks[index];
  }

  clearMarks(only?: Mark): void {
    for (const key of Object.keys(this.marks)) {
      const idx = Number(key);
      if (!only || this.marks[idx] === only) delete this.marks[idx];
    }
  }

  step(events: TraceEvent[], narration: string, checkpoint = false, line?: number): void {
    this.steps.push({
      index: this.steps.length,
      snapshot: {
        array: [...this.array],
        ids: [...this.ids],
        vars: { ...this.vars },
        marks: { ...this.marks },
      },
      events,
      narration,
      ...(checkpoint ? { checkpoint: true } : {}),
      ...(line !== undefined ? { line } : {}),
    });

    // R3.3c — tiêm can thiệp của học sinh đúng một lần, ngay sau bước k
    if (this.whatIf && this.steps.length - 1 === this.whatIf.afterStep) {
      const { i, j } = this.whatIf;
      this.whatIf = undefined;
      const vi = this.array[i];
      const vj = this.array[j];
      this.swap(i, j);
      this.steps.push({
        index: this.steps.length,
        snapshot: {
          array: [...this.array],
          ids: [...this.ids],
          vars: { ...this.vars },
          marks: { ...this.marks },
        },
        events: [{ type: "swap", i, j }],
        narration: `Em đã tự đổi chỗ ${fmt(vi)} (vị trí thứ ${i + 1}) với ${fmt(vj)} (vị trí thứ ${j + 1}). Thuật toán không hề biết điều này — quan sát xem nó chạy tiếp ra sao.`,
        userAction: true,
      });
    }
  }

  build(): Trace {
    return { source: this.source, steps: this.steps };
  }
}

/** Định dạng số cho thuyết minh: 7 → "7", 7.5 → "7,5" (kiểu Việt Nam). */
export function fmt(n: number): string {
  return Number.isInteger(n) ? String(n) : String(n).replace(".", ",");
}
