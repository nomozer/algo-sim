import type { AlgorithmId } from "./types";

/**
 * Mã giả từng thuật toán (giọng liệt kê bước kiểu SGK, chỉ số 1-based).
 * Engine gắn Step.line trỏ vào dòng đang thực hiện — renderer highlight.
 * R1.2: khi đối chiếu SGK, chỉnh câu chữ tại đây cho khớp sách.
 */
export const PSEUDOCODE: Record<AlgorithmId, string[]> = {
  find_max: [
    "max ← a[1]; vt ← 1",
    "với mỗi i từ 2 đến n:",
    "   nếu a[i] > max thì",
    "      max ← a[i]; vt ← i",
    "trả về max và vị trí vt",
  ],
  find_min: [
    "min ← a[1]; vt ← 1",
    "với mỗi i từ 2 đến n:",
    "   nếu a[i] < min thì",
    "      min ← a[i]; vt ← i",
    "trả về min và vị trí vt",
  ],
  sum_if: [
    "tong ← 0",
    "với mỗi i từ 1 đến n:",
    "   nếu a[i] thỏa điều kiện thì",
    "      tong ← tong + a[i]",
    "trả về tong",
  ],
  count_if: [
    "dem ← 0",
    "với mỗi i từ 1 đến n:",
    "   nếu a[i] thỏa điều kiện thì",
    "      dem ← dem + 1",
    "trả về dem",
  ],
  linear_search: [
    "với mỗi i từ 1 đến n:",
    "   nếu a[i] = x thì",
    "      trả về vị trí i",
    "trả về “không tìm thấy”",
  ],
  binary_search: [
    "trái ← 1; phải ← n",
    "lặp khi trái ≤ phải:",
    "   giữa ← (trái + phải) div 2",
    "   nếu a[giữa] = x: trả về giữa",
    "   nếu a[giữa] < x: trái ← giữa + 1",
    "   ngược lại: phải ← giữa − 1",
    "trả về “không tìm thấy”",
  ],
  bubble_sort: [
    "với mỗi lượt từ 1 đến n − 1:",
    "   với mỗi cặp kề (j, j+1) trong vùng chưa sắp:",
    "      nếu a[j] và a[j+1] sai thứ tự thì",
    "         đổi chỗ a[j] và a[j+1]",
    "   phần tử cuối vùng chưa sắp đã đúng chỗ",
    "trả về dãy đã sắp xếp",
  ],
  insertion_sort: [
    "coi a[1] là phần đã sắp",
    "với mỗi i từ 2 đến n:",
    "   k ← a[i]; j ← i − 1",
    "   lặp khi j ≥ 1 và a[j] > k:",
    "      dời a[j] sang phải; j ← j − 1",
    "   chèn k vào vị trí j + 1",
    "trả về dãy đã sắp xếp",
  ],
};
