/** Model domain logic — cổng AND (M5). Exploratory: không timeline. */

export type Bit = 0 | 1;

export interface LogicConfig {
  inputA: Bit;
  inputB: Bit;
  notes: string | null;
}

/** State = hai đầu vào; output là hàm dẫn xuất (engine tính, không lưu thừa). */
export interface LogicState {
  inputA: Bit;
  inputB: Bit;
}

/** Quy tắc tất định: AND chỉ cho 1 khi cả hai đầu vào đều 1. */
export function andOutput(state: LogicState): Bit {
  return state.inputA === 1 && state.inputB === 1 ? 1 : 0;
}

export const AND_RULE = "AND chỉ cho đầu ra 1 khi cả hai đầu vào đều là 1.";
