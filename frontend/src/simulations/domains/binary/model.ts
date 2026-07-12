/** Model domain binary — đổi thập phân sang nhị phân (M5). Exploratory. */

export type Bit = 0 | 1;

export interface BinaryConfig {
  decimalValue: number;
  bitWidth: number;
  notes: string | null;
}

/** State = các bit (MSB trước); giá trị thập phân là hàm dẫn xuất. */
export interface BinaryState {
  bits: Bit[];
  bitWidth: number;
}

/** Trọng số từng vị trí: [2^(w-1), ..., 4, 2, 1]. */
export function placeValues(bitWidth: number): number[] {
  return Array.from({ length: bitWidth }, (_, i) => 2 ** (bitWidth - 1 - i));
}

/** Giá trị thập phân tính từ các bit — engine tất định, không lưu thừa. */
export function decimalOf(state: BinaryState): number {
  const pv = placeValues(state.bitWidth);
  return state.bits.reduce<number>((sum, bit, i) => sum + bit * pv[i], 0);
}

/** Dãy bit MSB-first của một số trong bitWidth cho trước. */
export function bitsOf(value: number, bitWidth: number): Bit[] {
  return placeValues(bitWidth).map((pv) => ((value & pv) !== 0 ? 1 : 0));
}

export function binaryString(state: BinaryState): string {
  return state.bits.join("");
}
